"""
Shared configuration/secret resolution helper.

Resolution order:
    1. st.secrets[key]   — Streamlit Community Cloud / local .streamlit/secrets.toml
    2. os.environ[key]   — local development via .env (python-dotenv) or shell env

This is the ONLY place secret-reading logic lives; every module that needs a
key/config value should import get_secret from here instead of re-reading
os.environ or st.secrets directly. Values are never logged or printed.
"""
import os
from dotenv import load_dotenv

# No-op if no .env file is present (e.g. on Streamlit Cloud) — local dev only.
load_dotenv()


def get_secret(key: str, default: str = "") -> str:
    """
    Return a config value, preferring Streamlit secrets over environment
    variables. Safe to call outside a Streamlit runtime (scripts, tests):
    st.secrets access is wrapped in try/except since it raises when no
    secrets.toml / Cloud secrets are configured.
    """
    try:
        import streamlit as st
        if key in st.secrets:
            value = st.secrets[key]
            if value:
                return str(value).strip()
    except Exception:
        pass
    return os.environ.get(key, default).strip()
