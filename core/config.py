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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
GEMINI_FALLBACK_MODELS = [
    model.strip()
    for model in os.getenv(
        "GEMINI_FALLBACK_MODELS",
        "gemini-2.5-flash,gemini-2.0-flash-lite"
    ).split(",")
    if model.strip()
]
GEMINI_MAX_RETRIES = int(os.getenv("GEMINI_MAX_RETRIES", "2"))
GEMINI_TIMEOUT_SECONDS = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "45"))

if not GEMINI_API_KEY:
    try:
        import streamlit as st

        GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
        GEMINI_MODEL = st.secrets.get("GEMINI_MODEL", GEMINI_MODEL)
        secret_fallbacks = st.secrets.get("GEMINI_FALLBACK_MODELS", None)
        if secret_fallbacks:
            GEMINI_FALLBACK_MODELS = [
                model.strip()
                for model in str(secret_fallbacks).split(",")
                if model.strip()
            ]
    except Exception:
        # If streamlit isn't available or secrets not set, keep None
        GEMINI_API_KEY = GEMINI_API_KEY

APP_NAME = "AI Data Analyst Agent"
