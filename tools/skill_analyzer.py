"""
Skill Analyzer
--------------
Combines evidence from self-reported skills, resume-detected skills, and
GitHub-detected languages/technologies against the target role's required
skills. Uses Gemini to produce a structured, reasoned skill-gap estimate;
falls back to a deterministic local heuristic if the LLM is unavailable.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from agents.llm_client import call_gemini_json, is_llm_available
from prompts.prompts import SKILL_GAP_PROMPT


@dataclass
class SkillGap:
    skill: str
    current_level: int
    required_level: int
    gap: int
    importance: int


@dataclass
class SkillAnalysisResult:
    success: bool
    gaps: list = field(default_factory=list)  # list[SkillGap]
    used_llm: bool = True
    error: str = ""


def analyze_skill_gaps(
    target_role: str,
    required_skills: list,
    current_skills: str,
    resume_skills: list,
    github_skills: list,
    github_available: bool,
) -> SkillAnalysisResult:
    if is_llm_available():
        try:
            prompt = SKILL_GAP_PROMPT.format(
                target_role=target_role,
                required_skills=", ".join(required_skills) if required_skills else "Not specified",
                current_skills=current_skills or "Not provided",
                resume_skills=", ".join(resume_skills) if resume_skills else "None detected",
                github_skills=", ".join(github_skills) if github_skills else "None detected",
                github_available=github_available,
            )
            raw = call_gemini_json(prompt)
            gaps = _parse_llm_gaps(raw)
            if gaps:
                return SkillAnalysisResult(success=True, gaps=gaps, used_llm=True)
        except Exception:
            pass  # fall through to local heuristic

    # --- Deterministic local fallback (no LLM required) ---
    gaps = _local_heuristic_gaps(required_skills, current_skills, resume_skills, github_skills)
    return SkillAnalysisResult(success=True, gaps=gaps, used_llm=False)


def _parse_llm_gaps(raw) -> list:
    gaps = []
    if not isinstance(raw, list):
        return gaps
    for item in raw:
        try:
            gaps.append(SkillGap(
                skill=str(item.get("skill", "")).strip(),
                current_level=int(item.get("current_level", 0)),
                required_level=int(item.get("required_level", 70)),
                gap=max(0, int(item.get("gap", 0))),
                importance=int(item.get("importance", 5)),
            ))
        except (ValueError, TypeError, AttributeError):
            continue
    return [g for g in gaps if g.skill]


def _local_heuristic_gaps(required_skills, current_skills, resume_skills, github_skills) -> list:
    evidence_pool = set()
    for s in (current_skills or "").split(","):
        s = s.strip().lower()
        if s:
            evidence_pool.add(s)
    for s in resume_skills:
        evidence_pool.add(s.strip().lower())
    for s in github_skills:
        evidence_pool.add(s.strip().lower())

    gaps = []
    for i, skill in enumerate(required_skills or []):
        skill_l = skill.strip().lower()
        has_evidence = any(skill_l in e or e in skill_l for e in evidence_pool)
        current_level = 65 if has_evidence else 15
        required_level = 80
        gap = max(0, required_level - current_level)
        # earlier items in the list treated as slightly more important
        importance = max(4, 10 - i)
        gaps.append(SkillGap(
            skill=skill,
            current_level=current_level,
            required_level=required_level,
            gap=gap,
            importance=importance,
        ))
    return gaps
