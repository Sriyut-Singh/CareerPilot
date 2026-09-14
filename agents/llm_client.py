"""
Isolated Gemini LLM integration.

All calls to Google's Gemini API go through this module so the rest of the
codebase never touches the SDK directly.

Key/config resolution order (secure by design for Streamlit Community Cloud):
    1. st.secrets["GEMINI_API_KEY"] / st.secrets["GEMINI_MODEL"]  (deployed)
    2. Environment variables via python-dotenv / os.environ       (local dev fallback)

No key is ever logged, printed, or surfaced in the UI. If no key is found in
either location, the LLM is simply treated as unavailable and every caller
in this app falls back to deterministic local logic instead of crashing.
"""
import json
import re
from typing import Any

from config import get_secret

GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
GEMINI_MODEL = get_secret("GEMINI_MODEL", "gemini-2.5-flash")

_client = None
_configured = False
_last_error = ""


def _safe_error(exc: Exception) -> str:
    """Return a diagnostic that never exposes the configured API key."""
    text = str(exc) or exc.__class__.__name__
    if GEMINI_API_KEY:
        text = text.replace(GEMINI_API_KEY, "[REDACTED]")
    # Also avoid accidentally exposing a long credential-like token.
    text = re.sub(r"AIza[0-9A-Za-z_-]+", "[REDACTED]", text)
    text = re.sub(r"AQ\.[0-9A-Za-z_-]+", "[REDACTED]", text)
    return text[:600]


def get_llm_diagnostic() -> str:
    """Return the latest safe Gemini diagnostic for the UI."""
    return _last_error


def _configure() -> bool:
    """Lazily configure the current Google GenAI SDK."""
    global _client, _configured, _last_error
    if _configured:
        return _client is not None
    _configured = True
    if not GEMINI_API_KEY:
        _last_error = "GEMINI_API_KEY was not found in Streamlit secrets or environment variables."
        return False
    try:
        from google import genai
        _client = genai.Client(api_key=GEMINI_API_KEY)
        return True
    except Exception as e:
        _client = None
        _last_error = f"Gemini client setup failed: {_safe_error(e)}"
        return False


def is_llm_available() -> bool:
    """Public check so the UI/agent can decide whether to use fallback logic."""
    return _configure()


def call_gemini(
    prompt: str,
    temperature: float = 0.4,
    response_mime_type: str | None = None,
) -> str:
    """Call Gemini with a text prompt and return the raw text response."""
    global _last_error
    if not _configure():
        raise RuntimeError(
            "Gemini is not configured. Set GEMINI_API_KEY in Streamlit secrets "
            "(or a local .env file for development)."
        )
    try:
        from google.genai import types
        config_kwargs: dict[str, Any] = {"temperature": temperature}
        if response_mime_type:
            config_kwargs["response_mime_type"] = response_mime_type
        response = _client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(**config_kwargs),
        )
        text = response.text or ""
        if not text.strip():
            raise RuntimeError("Gemini returned an empty response")
        _last_error = ""
        return text
    except Exception as e:
        _last_error = f"Gemini API call failed: {_safe_error(e)}"
        raise RuntimeError(_last_error) from e


def call_gemini_json(prompt: str, temperature: float = 0.3) -> Any:
    """Call Gemini expecting JSON and parse the response."""
    raw = call_gemini(
        prompt,
        temperature=temperature,
        response_mime_type="application/json",
    )
    cleaned = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"(\[.*\]|\{.*\})", cleaned, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Could not parse Gemini JSON response: {e}") from e
        raise RuntimeError("Could not parse Gemini JSON response")
