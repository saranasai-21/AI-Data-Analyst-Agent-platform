import logging
import random
import time

import google.genai as genai
from google.genai import types

from core.config import (
    GEMINI_API_KEYS,
    GEMINI_FALLBACK_MODELS,
    GEMINI_MAX_RETRIES,
    GEMINI_MODEL,
    GEMINI_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)
_active_key = None


def _model_chain():
    models = [GEMINI_MODEL, *GEMINI_FALLBACK_MODELS]
    seen = set()
    ordered = []

    for model in models:
        if model and model not in seen:
            seen.add(model)
            ordered.append(model)

    return ordered


def _is_retryable(exc):
    text = str(exc).upper()
    return any(
        token in text
        for token in (
            "503",
            "429",
            "UNAVAILABLE",
            "RESOURCE_EXHAUSTED",
            "DEADLINE_EXCEEDED",
            "TIMEOUT",
        )
    )


def _is_quota_exhausted(exc):
    text = str(exc).upper()
    return any(
        token in text
        for token in (
            "429",
            "RESOURCE_EXHAUSTED",
            "QUOTA_EXCEEDED",
            "QUOTA",
        )
    )


def generate_text(
    api_key,
    prompt,
    *,
    temperature=0.2,
    max_output_tokens=900,
    thinking_budget=0,
):
    global _active_key
    keys_to_try = list(GEMINI_API_KEYS)
    if api_key and api_key not in keys_to_try:
        keys_to_try.insert(0, api_key)
    if not keys_to_try:
        keys_to_try = [api_key] if api_key else []

    if not keys_to_try:
        raise RuntimeError("No Gemini API keys are configured.")

    start_idx = 0
    if _active_key in keys_to_try:
        start_idx = keys_to_try.index(_active_key)
    ordered_keys = keys_to_try[start_idx:] + keys_to_try[:start_idx]

    last_error = None

    for model in _model_chain():
        for key in ordered_keys:
            try:
                client = genai.Client(api_key=key)
                config_args = {
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens,
                    "http_options": types.HttpOptions(timeout=GEMINI_TIMEOUT_SECONDS * 1000),
                }

                if thinking_budget is not None and "gemini-2.5" in model:
                    config_args["thinking_config"] = types.ThinkingConfig(
                        thinking_budget=thinking_budget
                    )

                config = types.GenerateContentConfig(**config_args)
                
                # Append instruction to avoid conversational greetings
                if isinstance(prompt, str):
                    prompt += "\n\nIMPORTANT INSTRUCTION: DO NOT include conversational greetings (e.g. 'Good morning', 'Hello') or pleasantries in your response. Output only the requested analysis or insights."

                for attempt in range(GEMINI_MAX_RETRIES + 1):
                    try:
                        response = client.models.generate_content(
                            model=model,
                            contents=prompt,
                            config=config,
                        )
                        # Success! Record this key as the active key.
                        _active_key = key
                        
                        # Dynamically update config/graph keys to sync application state
                        import core.config
                        import orchestrator.graph
                        core.config.GEMINI_API_KEY = key
                        orchestrator.graph.GEMINI_API_KEY = key

                        return response.text or ""
                    except Exception as exc:
                        last_error = exc
                        
                        if _is_quota_exhausted(exc):
                            logger.warning(
                                f"Gemini API key rate-limited/exhausted for model {model}. Switching key. Error: {exc}"
                            )
                            break  # Break retry loop to try next API key
                        
                        if not _is_retryable(exc):
                            logger.warning(
                                f"Gemini API key failed with non-retryable error for model {model}. Switching key. Error: {exc}"
                            )
                            break  # Break retry loop to try next API key

                        if attempt < GEMINI_MAX_RETRIES:
                            delay = min(1.2 * (2 ** attempt), 4.0) + random.uniform(0, 0.35)
                            time.sleep(delay)
            except Exception as key_exc:
                last_error = key_exc
                logger.warning(f"Error initializing client or executing key for model {model}: {key_exc}. Trying next key...")
                continue

    if last_error:
        raise last_error

    raise RuntimeError("No Gemini models/keys are configured or all failed.")


def parse_pdf_to_csv(api_key, pdf_bytes):
    global _active_key
    prompt = (
        "Extract the main tabular dataset from this PDF document. "
        "Format it as a standard CSV with comma separators. "
        "Do not wrap it in markdown codeblocks (like ```csv), do not add comments or introductory text. "
        "Only output the raw CSV data."
    )
    
    keys_to_try = list(GEMINI_API_KEYS)
    if api_key and api_key not in keys_to_try:
        keys_to_try.insert(0, api_key)
    if not keys_to_try:
        keys_to_try = [api_key] if api_key else []

    if not keys_to_try:
        raise RuntimeError("No Gemini API keys are configured.")

    start_idx = 0
    if _active_key in keys_to_try:
        start_idx = keys_to_try.index(_active_key)
    ordered_keys = keys_to_try[start_idx:] + keys_to_try[:start_idx]

    last_error = None

    for model in _model_chain():
        for key in ordered_keys:
            try:
                client = genai.Client(api_key=key)
                for attempt in range(GEMINI_MAX_RETRIES + 1):
                    try:
                        response = client.models.generate_content(
                            model=model,
                            contents=[
                                types.Part.from_bytes(
                                    data=pdf_bytes,
                                    mime_type="application/pdf"
                                ),
                                prompt
                            ],
                            config=types.GenerateContentConfig(
                                temperature=0.0,
                                max_output_tokens=8192,
                            )
                        )
                        # Success!
                        _active_key = key
                        
                        # Dynamically update config/graph keys to sync application state
                        import core.config
                        import orchestrator.graph
                        core.config.GEMINI_API_KEY = key
                        orchestrator.graph.GEMINI_API_KEY = key

                        text = response.text or ""
                        text = text.strip()
                        if text.startswith("```csv"):
                            text = text[6:]
                        elif text.startswith("```"):
                            text = text[3:]
                        if text.endswith("```"):
                            text = text[:-3]
                        return text.strip()
                    except Exception as exc:
                        last_error = exc
                        if _is_quota_exhausted(exc):
                            logger.warning(
                                f"Gemini API key rate-limited/exhausted for model {model} during PDF parsing. Switching key. Error: {exc}"
                            )
                            break  # Break retry loop to try next API key
                        
                        if not _is_retryable(exc):
                            logger.warning(
                                f"Gemini API key failed with non-retryable error for model {model} during PDF parsing. Switching key. Error: {exc}"
                            )
                            break  # Break retry loop to try next API key

                        if attempt < GEMINI_MAX_RETRIES:
                            delay = min(1.2 * (2 ** attempt), 4.0) + random.uniform(0, 0.35)
                            time.sleep(delay)
            except Exception as key_exc:
                last_error = key_exc
                logger.warning(f"Error initializing client or executing key for model {model} during PDF parsing: {key_exc}. Trying next key...")
                continue
            
    if last_error:
        raise last_error

    raise RuntimeError("Failed to parse PDF using available Gemini models and keys.")
