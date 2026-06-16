import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ModuleNotFoundError:
    # Keep the app bootable even if python-dotenv has not been installed yet.
    pass

# Read GEMINI API key from environment first. Common usage is to set
# an env var named 'GEMINI_API_KEY'. If running in Streamlit with
# secrets configured, fall back to `st.secrets`.
GEMINI_API_KEYS = []

def _add_key(val):
    if val and isinstance(val, str):
        val = val.strip()
        if val and val not in GEMINI_API_KEYS:
            GEMINI_API_KEYS.append(val)

_add_key(os.getenv("GEMINI_API_KEY"))
for k in sorted(os.environ.keys()):
    if k.upper().startswith("GEMINI_API_KEY"):
        _add_key(os.getenv(k))

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_FALLBACK_MODELS = [
    model.strip()
    for model in os.getenv(
        "GEMINI_FALLBACK_MODELS",
        "gemini-2.5-pro,gemini-2.0-flash,gemini-1.5-pro-latest,gemini-1.5-flash-latest"
    ).split(",")
    if model.strip()
]
GEMINI_MAX_RETRIES = int(os.getenv("GEMINI_MAX_RETRIES", "2"))
GEMINI_TIMEOUT_SECONDS = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "30"))

try:
    import streamlit as st

    _add_key(st.secrets.get("GEMINI_API_KEY"))
    if hasattr(st, "secrets") and st.secrets is not None:
        for k in sorted(st.secrets.keys()):
            if k.upper().startswith("GEMINI_API_KEY"):
                _add_key(st.secrets.get(k))

    GEMINI_MODEL = st.secrets.get("GEMINI_MODEL", GEMINI_MODEL)
    secret_fallbacks = st.secrets.get("GEMINI_FALLBACK_MODELS", None)
    if secret_fallbacks:
        GEMINI_FALLBACK_MODELS = [
            model.strip()
            for model in str(secret_fallbacks).split(",")
            if model.strip()
        ]
except Exception:
    # If streamlit isn't available or secrets not set, keep existing keys
    pass

GEMINI_API_KEY = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else None

APP_NAME = "AI Data Analyst Agent"
