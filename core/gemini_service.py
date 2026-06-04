import random
import time

import google.genai as genai
from google.genai import types

from core.config import (
    GEMINI_FALLBACK_MODELS,
    GEMINI_MAX_RETRIES,
    GEMINI_MODEL,
    GEMINI_TIMEOUT_SECONDS,
)


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


def generate_text(
    api_key,
    prompt,
    *,
    temperature=0.2,
    max_output_tokens=900,
    thinking_budget=0,
):
    client = genai.Client(api_key=api_key)

    last_error = None

    for model in _model_chain():
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

        for attempt in range(GEMINI_MAX_RETRIES + 1):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config,
                )
                return response.text or ""
            except Exception as exc:
                last_error = exc

                if not _is_retryable(exc):
                    raise

                if attempt < GEMINI_MAX_RETRIES:
                    delay = min(1.2 * (2 ** attempt), 4.0) + random.uniform(0, 0.35)
                    time.sleep(delay)

    if last_error:
        raise last_error

    raise RuntimeError("No Gemini models are configured.")


def parse_pdf_to_csv(api_key, pdf_bytes):
    client = genai.Client(api_key=api_key)
    
    prompt = (
        "Extract the main tabular dataset from this PDF document. "
        "Format it as a standard CSV with comma separators. "
        "Do not wrap it in markdown codeblocks (like ```csv), do not add comments or introductory text. "
        "Only output the raw CSV data."
    )
    
    for model in _model_chain():
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
            text = response.text or ""
            text = text.strip()
            if text.startswith("```csv"):
                text = text[6:]
            elif text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            return text.strip()
        except Exception:
            continue
            
    raise RuntimeError("Failed to parse PDF using available Gemini models.")
