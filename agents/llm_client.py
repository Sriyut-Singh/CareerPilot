"""
Isolated Gemini LLM integration.

All calls to Google's Gemini API go through this module so the rest of the
codebase never touches the SDK directly. Reads GEMINI_API_KEY and
GEMINI_MODEL from environment variables via python-dotenv.
"""
import os
import json
import re
from typing import Any, Optional

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()

_model = None
_configured = False


def _configure() -> bool:
    """Lazily configure the Gemini SDK. Returns True if a key is available."""
    global _model, _configured
    if _configured:
        return _model is not None
    _configured = True
    if not GEMINI_API_KEY:
        return False
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        _model = genai.GenerativeModel(GEMINI_MODEL)
        return True
    except Exception:
        _model = None
        return False


def is_llm_available() -> bool:
    """Public check so the UI/agent can decide whether to use fallback logic."""
    return _configure()


def call_gemini(prompt: str, temperature: float = 0.4) -> str:
    """
    Call Gemini with a plain text prompt and return the raw text response.
    Raises RuntimeError if the SDK/key is unavailable or the call fails,
    so callers can decide how to fall back (this module never silently
    fabricates a successful response).
    """
    if not _configure():
        raise RuntimeError("Gemini API key not configured (set GEMINI_API_KEY in .env)")
    try:
        response = _model.generate_content(
            prompt,
            generation_config={"temperature": temperature},
        )
        text = response.text or ""
        if not text.strip():
            raise RuntimeError("Gemini returned an empty response")
        return text
    except Exception as e:
        raise RuntimeError(f"Gemini API call failed: {e}") from e


def call_gemini_json(prompt: str, temperature: float = 0.3) -> Any:
    """
    Call Gemini expecting a JSON response and parse it, stripping any
    accidental markdown code fences. Raises RuntimeError on failure so the
    caller (agent) can trigger its own fallback / adaptation logic.
    """
    raw = call_gemini(prompt, temperature=temperature)
    cleaned = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # try to salvage the largest {...} or [...] block
        match = re.search(r"(\[.*\]|\{.*\})", cleaned, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Could not parse Gemini JSON response: {e}") from e
        raise RuntimeError("Could not parse Gemini JSON response")
