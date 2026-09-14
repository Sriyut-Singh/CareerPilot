"""
Planner Agent
-------------
Prioritizes skill gaps using: priority_score = importance * gap * relevance,
then asks Gemini to generate a concrete sequenced action plan. Falls back to
a deterministic template plan if the LLM is unavailable.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from agents.llm_client import call_gemini_json, is_llm_available
from prompts.prompts import PLANNER_PROMPT
from tools.skill_analyzer import SkillGap


@dataclass
class PlanStep:
    priority: str
    action: str
    reason: str
    expected_outcome: str
    timeframe: str


@dataclass
class PlanResult:
    success: bool
    steps: list = field(default_factory=list)  # list[PlanStep]
    ranked_gaps: list = field(default_factory=list)  # list of dicts with priority_score
    used_llm: bool = True
    error: str = ""


def rank_gaps(gaps: list, relevance: float = 1.0) -> list:
    """Return gaps ranked by priority_score = importance * gap * relevance, desc."""
    ranked = []
    for g in gaps:
        score = g.importance * g.gap * relevance
        ranked.append({
            "skill": g.skill,
            "current_level": g.current_level,
            "required_level": g.required_level,
            "gap": g.gap,
            "importance": g.importance,
            "priority_score": round(score, 1),
        })
    ranked.sort(key=lambda x: x["priority_score"], reverse=True)
    return ranked


def generate_plan(
    intent_summary: str,
    target_role: str,
    timeframe_months: int,
    gaps: list,
    evaluation_notes: str = "",
) -> PlanResult:
    ranked = rank_gaps(gaps)

    if is_llm_available():
        try:
            prompt = PLANNER_PROMPT.format(
                intent_summary=intent_summary,
                target_role=target_role,
                timeframe_months=timeframe_months,
                ranked_gaps=_format_ranked_gaps(ranked),
                evaluation_notes=evaluation_notes or "None yet.",
            )
            raw = call_gemini_json(prompt)
            steps = _parse_steps(raw)
            if steps:
                return PlanResult(success=True, steps=steps, ranked_gaps=ranked, used_llm=True)
        except Exception:
            pass

    steps = _local_fallback_plan(ranked, timeframe_months)
    return PlanResult(success=True, steps=steps, ranked_gaps=ranked, used_llm=False)


def _format_ranked_gaps(ranked: list) -> str:
    lines = []
    for r in ranked[:8]:
        lines.append(
            f"- {r['skill']}: importance={r['importance']}, gap={r['gap']}, "
            f"priority_score={r['priority_score']}"
        )
    return "\n".join(lines) if lines else "No significant gaps identified."


def _parse_steps(raw) -> list:
    steps = []
    if not isinstance(raw, list):
        return steps
    for item in raw:
        try:
            steps.append(PlanStep(
                priority=str(item.get("priority", "Medium")),
                action=str(item.get("action", "")).strip(),
                reason=str(item.get("reason", "")).strip(),
                expected_outcome=str(item.get("expected_outcome", "")).strip(),
                timeframe=str(item.get("timeframe", "")).strip(),
            ))
        except (ValueError, TypeError, AttributeError):
            continue
    return [s for s in steps if s.action]


def _local_fallback_plan(ranked: list, timeframe_months: int) -> list:
    steps = []
    top = ranked[:6] if ranked else []
    for i, r in enumerate(top):
        priority = "High" if i < 2 else ("Medium" if i < 4 else "Low")
        month = max(1, round((i + 1) * timeframe_months / max(1, len(top))))
        steps.append(PlanStep(
            priority=priority,
            action=f"Build a focused project or complete a course in {r['skill']}",
            reason=f"{r['skill']} has a high priority score ({r['priority_score']}) "
                   f"driven by importance {r['importance']} and current gap {r['gap']}.",
            expected_outcome=f"Demonstrable evidence of {r['skill']} on resume/GitHub",
            timeframe=f"Month {month}",
        ))
    if not steps:
        steps.append(PlanStep(
            priority="Medium",
            action="Build 1-2 portfolio projects aligned with the target role",
            reason="No specific high-priority gaps were identified from available evidence.",
            expected_outcome="Stronger project portfolio for applications",
            timeframe=f"Month 1-{timeframe_months}",
        ))
    return steps
