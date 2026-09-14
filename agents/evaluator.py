"""
Evaluator Agent
---------------
Assesses profile/skill/project/resume readiness and goal alignment, produces
an overall readiness score, and decides whether the situation warrants
replanning (needs_replan). Falls back to a deterministic scoring heuristic
if the LLM is unavailable.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from agents.llm_client import call_gemini_json, is_llm_available
from prompts.prompts import EVALUATOR_PROMPT


@dataclass
class EvaluationResult:
    success: bool
    profile_completeness: int = 0
    skill_readiness: int = 0
    project_readiness: int = 0
    resume_readiness: int = 0
    goal_alignment: int = 0
    overall_score: int = 0
    recommendations: list = field(default_factory=list)
    needs_replan: bool = False
    used_llm: bool = True
    error: str = ""


def evaluate(
    target_role: str,
    resume_available: bool,
    github_available: bool,
    num_required_skills: int,
    avg_gap: float,
    num_projects: int,
) -> EvaluationResult:
    if is_llm_available():
        try:
            prompt = EVALUATOR_PROMPT.format(
                target_role=target_role,
                resume_available=resume_available,
                github_available=github_available,
                num_required_skills=num_required_skills,
                avg_gap=round(avg_gap, 1),
                num_projects=num_projects,
            )
            raw = call_gemini_json(prompt)
            result = _parse_evaluation(raw)
            if result:
                return result
        except Exception:
            pass

    return _local_heuristic_evaluation(
        resume_available, github_available, avg_gap, num_projects
    )


def _parse_evaluation(raw) -> EvaluationResult | None:
    if not isinstance(raw, dict):
        return None
    try:
        return EvaluationResult(
            success=True,
            profile_completeness=int(raw.get("profile_completeness", 0)),
            skill_readiness=int(raw.get("skill_readiness", 0)),
            project_readiness=int(raw.get("project_readiness", 0)),
            resume_readiness=int(raw.get("resume_readiness", 0)),
            goal_alignment=int(raw.get("goal_alignment", 0)),
            overall_score=int(raw.get("overall_score", 0)),
            recommendations=list(raw.get("recommendations", [])),
            needs_replan=bool(raw.get("needs_replan", False)),
            used_llm=True,
        )
    except (ValueError, TypeError):
        return None


def _local_heuristic_evaluation(resume_available, github_available, avg_gap, num_projects) -> EvaluationResult:
    resume_readiness = 70 if resume_available else 20
    project_readiness = min(100, num_projects * 15) if github_available else 10
    skill_readiness = max(0, 100 - int(avg_gap))
    profile_completeness = int((resume_readiness + (80 if github_available else 20)) / 2)
    goal_alignment = 60  # neutral default without deeper reasoning
    overall = int((resume_readiness + project_readiness + skill_readiness + profile_completeness + goal_alignment) / 5)

    recommendations = []
    if not resume_available:
        recommendations.append("Upload a resume so the agent can verify claimed skills.")
    if not github_available:
        recommendations.append("Connect or fix GitHub analysis to surface real project evidence.")
    if avg_gap > 40:
        recommendations.append("Focus on closing the largest skill gaps before applying.")
    if not recommendations:
        recommendations.append("Keep building projects that demonstrate top-priority skills.")

    needs_replan = (not github_available) or (overall < 40) or (resume_readiness < 30)

    return EvaluationResult(
        success=True,
        profile_completeness=profile_completeness,
        skill_readiness=skill_readiness,
        project_readiness=project_readiness,
        resume_readiness=resume_readiness,
        goal_alignment=goal_alignment,
        overall_score=overall,
        recommendations=recommendations,
        needs_replan=needs_replan,
        used_llm=False,
    )
