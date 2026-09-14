"""
GitHub Tool
-----------
Uses GitHub's public REST API to analyze a student's repositories:
languages used, project count/diversity, stars, and recent activity.

Supports an explicit `force_failure` flag used by the app's
"Demo Failure Mode" checkbox to reliably demonstrate the agent's
failure-handling / adaptation loop. When force_failure is True, this tool
does NOT call the real API and does NOT pretend to succeed — it returns a
clearly labeled simulated failure.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

import requests

from config import get_secret

GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = get_secret("GITHUB_TOKEN")


@dataclass
class GitHubResult:
    success: bool
    username: str = ""
    public_repo_count: int = 0
    languages: list = field(default_factory=list)
    top_repos: list = field(default_factory=list)  # list of dicts
    total_stars: int = 0
    project_diversity_score: int = 0  # 0-100
    recent_activity: bool = False
    error: str = ""
    simulated_failure: bool = False


def analyze_github(username: str, force_failure: bool = False, timeout: int = 8) -> GitHubResult:
    """
    Analyze a GitHub user's public profile. Never raises — all failure modes
    are captured in the returned GitHubResult so the agent can adapt.
    """
    username = (username or "").strip()

    if force_failure:
        return GitHubResult(
            success=False,
            username=username,
            simulated_failure=True,
            error=(
                "GitHub analysis intentionally failed (Demo Failure Mode is ON). "
                "This is a simulated failure for demonstrating agent adaptation — "
                "no real API call was made."
            ),
        )

    if not username:
        return GitHubResult(success=False, error="No GitHub username provided.")

    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    try:
        user_resp = requests.get(f"{GITHUB_API_BASE}/users/{username}", headers=headers, timeout=timeout)
        if user_resp.status_code == 404:
            return GitHubResult(success=False, username=username, error=f"GitHub user '{username}' not found.")
        if user_resp.status_code == 403:
            return GitHubResult(success=False, username=username, error="GitHub API rate limit exceeded.")
        user_resp.raise_for_status()
        user_data = user_resp.json()
        public_repo_count = user_data.get("public_repos", 0)

        repos_resp = requests.get(
            f"{GITHUB_API_BASE}/users/{username}/repos",
            headers=headers,
            params={"per_page": 100, "sort": "updated"},
            timeout=timeout,
        )
        repos_resp.raise_for_status()
        repos = repos_resp.json()
        if not isinstance(repos, list):
            repos = []

        languages = {}
        total_stars = 0
        top_repos = []
        for repo in repos:
            lang = repo.get("language")
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
            total_stars += repo.get("stargazers_count", 0) or 0

        sorted_repos = sorted(repos, key=lambda r: r.get("stargazers_count", 0) or 0, reverse=True)
        for r in sorted_repos[:5]:
            top_repos.append({
                "name": r.get("name", ""),
                "description": r.get("description") or "No description",
                "language": r.get("language") or "Unknown",
                "stars": r.get("stargazers_count", 0) or 0,
                "updated_at": r.get("updated_at", ""),
            })

        language_list = sorted(languages.keys(), key=lambda k: languages[k], reverse=True)
        diversity_score = min(100, len(language_list) * 15 + min(len(repos), 10) * 3)
        recent_activity = any(r.get("pushed_at") for r in repos[:5])

        return GitHubResult(
            success=True,
            username=username,
            public_repo_count=public_repo_count,
            languages=language_list,
            top_repos=top_repos,
            total_stars=total_stars,
            project_diversity_score=diversity_score,
            recent_activity=recent_activity,
        )
    except requests.exceptions.RequestException as e:
        return GitHubResult(success=False, username=username, error=f"GitHub API request failed: {e}")
    except Exception as e:
        return GitHubResult(success=False, username=username, error=f"Unexpected error analyzing GitHub: {e}")
