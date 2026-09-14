"""
Job Research Tool
------------------
Fetches typical skill requirements for a target role. The provider is
modular/configurable via SEARCH_API_KEY — if no live search key is
configured (or the request fails), this tool clearly falls back to a
curated demo dataset and LABELS the result as fallback data. It never
fabricates results and claims they were live.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

import requests

from config import get_secret

SEARCH_API_KEY = get_secret("SEARCH_API_KEY")

# Curated fallback requirement sets, keyed by normalized role name.
# Used only when no live search API is configured or the call fails.
FALLBACK_ROLE_REQUIREMENTS = {
    "ai/ml engineer": [
        "Python", "Machine Learning", "Deep Learning", "PyTorch", "TensorFlow",
        "Data Structures", "Statistics", "SQL", "Model Deployment", "NLP",
    ],
    "machine learning engineer": [
        "Python", "Machine Learning", "Deep Learning", "PyTorch", "TensorFlow",
        "Data Structures", "Statistics", "SQL", "Model Deployment", "MLOps",
    ],
    "data scientist": [
        "Python", "Statistics", "Machine Learning", "SQL", "Pandas",
        "Data Visualization", "A/B Testing", "Communication",
    ],
    "backend engineer": [
        "Python", "REST API", "SQL", "System Design", "Docker",
        "Git", "Data Structures", "Algorithms", "Cloud (AWS/GCP/Azure)",
    ],
    "frontend engineer": [
        "JavaScript", "TypeScript", "React", "HTML/CSS", "REST API",
        "Git", "Testing", "Web Performance",
    ],
    "full stack engineer": [
        "JavaScript", "React", "Node.js", "SQL", "REST API",
        "Git", "System Design", "Cloud (AWS/GCP/Azure)",
    ],
    "default": [
        "Python", "Problem Solving", "Git", "Data Structures", "Algorithms",
        "SQL", "Communication", "System Design",
    ],
}


@dataclass
class JobResearchResult:
    success: bool
    target_role: str = ""
    required_skills: list = field(default_factory=list)
    source: str = ""  # "live" or "fallback_demo_dataset"
    error: str = ""


def research_job_requirements(target_role: str, timeout: int = 8) -> JobResearchResult:
    """
    Attempt a live search for role requirements; fall back to a labeled
    demo dataset if no API key is configured or the live call fails.
    """
    role_key = (target_role or "").strip().lower()
    if not role_key:
        role_key = "ai/ml engineer"

    if SEARCH_API_KEY:
        try:
            skills = _live_search(target_role, timeout=timeout)
            if skills:
                return JobResearchResult(
                    success=True,
                    target_role=target_role,
                    required_skills=skills,
                    source="live",
                )
        except Exception:
            pass  # fall through to fallback dataset below

    # --- Fallback path (clearly labeled, not pretending to be live) ---
    matched_key = None
    for key in FALLBACK_ROLE_REQUIREMENTS:
        if key != "default" and (key in role_key or role_key in key):
            matched_key = key
            break
    if not matched_key:
        matched_key = "default"

    return JobResearchResult(
        success=True,
        target_role=target_role or matched_key,
        required_skills=FALLBACK_ROLE_REQUIREMENTS[matched_key],
        source="fallback_demo_dataset",
    )


def _live_search(target_role: str, timeout: int = 8) -> Optional[list]:
    """
    Placeholder for a real search-API integration (e.g. Serper, Tavily, Bing).
    Kept isolated so the provider can be swapped without touching callers.
    Returns None if it cannot produce a confident skill list.
    """
    # Example shape only — real implementation would call the configured
    # SEARCH_API_KEY provider here and parse results into a skill list.
    # Intentionally not implemented with a real provider for this MVP so we
    # never claim "live" results without a genuine successful call.
    return None
