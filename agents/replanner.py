"""
Replanner Agent
---------------
Triggered when a tool fails, information is missing, or the Evaluator flags
needs_replan=True. Produces a revised plan that explicitly accounts for the
new situation (e.g. missing GitHub data), so the demo can clearly show
adaptation rather than a static roadmap.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from agents.llm_client import call_gemini_json, is_llm_available
from agents.planner import PlanStep, _parse_steps, _local_fallback_plan, rank_gaps
from prompts.prompts import REPLAN_PROMPT


@dataclass
class ReplanResult:
    success: bool
    steps: list = field(default_factory=list)  # list[PlanStep]
    trigger_reason: str = ""
    used_llm: bool = True
    error: str = ""


def replan(
    original_steps: list,
    gaps: list,
    trigger_reason: str,
    new_context: str,
) -> ReplanResult:
    ranked = rank_gaps(gaps)
    original_plan_text = _format_steps(original_steps)

    if is_llm_available():
        try:
            prompt = REPLAN_PROMPT.format(
                original_plan=original_plan_text,
                trigger_reason=trigger_reason,
                new_context=new_context,
            )
            raw = call_gemini_json(prompt)
            steps = _parse_steps(raw)
            if steps:
                return ReplanResult(success=True, steps=steps, trigger_reason=trigger_reason, used_llm=True)
        except Exception:
            pass

    # Deterministic fallback: reuse planner's local logic but inject an
    # explicit adaptation note on the first step so it's visible in the UI.
    steps = _local_fallback_plan(ranked, timeframe_months=6)
    if steps:
        steps[0] = PlanStep(
            priority=steps[0].priority,
            action=steps[0].action,
            reason=(
                f"[Adapted] {trigger_reason}. The agent recalculated priorities using "
                f"available evidence ({new_context})."
            ),
            expected_outcome=steps[0].expected_outcome,
            timeframe=steps[0].timeframe,
        )
    return ReplanResult(success=True, steps=steps, trigger_reason=trigger_reason, used_llm=False)


def _format_steps(steps: list) -> str:
    if not steps:
        return "No prior plan available."
    lines = []
    for s in steps:
        lines.append(f"- [{s.priority}] {s.action} (reason: {s.reason})")
    return "\n".join(lines)
