"""
CareerPilot Agent / Controller
-------------------------------
This is the orchestrator that implements the visible agentic loop:

    GOAL -> OBSERVE -> DECIDE -> ACT -> EVALUATE -> ADAPT

It calls tools, tracks an "activity log" of every step (for the UI),
and triggers the Replanner when a tool fails or the Evaluator flags
needs_replan. Nothing here silently swallows failures — every failure is
logged as a visible activity item.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, BinaryIO

from agents.llm_client import call_gemini_json, is_llm_available
from prompts.prompts import GOAL_UNDERSTANDING_PROMPT, DECISION_EXPLANATION_PROMPT

from tools.resume_parser import parse_resume, ResumeResult
from tools.github_tool import analyze_github, GitHubResult
from tools.job_search import research_job_requirements, JobResearchResult
from tools.skill_analyzer import analyze_skill_gaps, SkillAnalysisResult

from agents.planner import generate_plan, rank_gaps, PlanResult
from agents.evaluator import evaluate, EvaluationResult
from agents.replanner import replan, ReplanResult


@dataclass
class ActivityEvent:
    status: str   # "success" | "warning" | "info" | "error"
    message: str


@dataclass
class CareerPilotRunResult:
    activity_log: list = field(default_factory=list)  # list[ActivityEvent]
    goal_info: dict = field(default_factory=dict)
    resume: Optional[ResumeResult] = None
    github: Optional[GitHubResult] = None
    job_research: Optional[JobResearchResult] = None
    skill_analysis: Optional[SkillAnalysisResult] = None
    ranked_gaps: list = field(default_factory=list)
    plan: Optional[PlanResult] = None
    evaluation: Optional[EvaluationResult] = None
    adapted: bool = False
    adapted_plan: Optional[ReplanResult] = None
    decision_explanation: str = ""


class CareerPilotAgent:
    """Stateful controller for a single CareerPilot run."""

    def __init__(self):
        self.log: list = []

    def _emit(self, status: str, message: str):
        self.log.append(ActivityEvent(status=status, message=message))

    def run(
        self,
        goal: str,
        resume_file: Optional[BinaryIO],
        github_username: str,
        current_skills: str,
        target_role: str = "",
        force_github_failure: bool = False,
    ) -> CareerPilotRunResult:
        result = CareerPilotRunResult()

        # ---------------- GOAL ----------------
        goal_info = self._understand_goal(goal, target_role, current_skills)
        result.goal_info = goal_info
        self._emit("success", "Goal analyzed")

        effective_role = goal_info.get("target_role") or target_role or "AI/ML Engineer"
        timeframe = goal_info.get("timeframe_months", 6)

        # ---------------- OBSERVE: Resume ----------------
        resume_result = self._run_resume_tool(resume_file)
        result.resume = resume_result

        # ---------------- OBSERVE: GitHub ----------------
        github_result = self._run_github_tool(github_username, force_github_failure)
        result.github = github_result

        # ---------------- OBSERVE: Job requirements ----------------
        job_result = self._run_job_research(effective_role)
        result.job_research = job_result

        # ---------------- DECIDE + ACT: Skill gap analysis ----------------
        skill_result = self._run_skill_analysis(
            effective_role, job_result, current_skills, resume_result, github_result
        )
        result.skill_analysis = skill_result
        result.ranked_gaps = rank_gaps(skill_result.gaps) if skill_result.success else []

        avg_gap = (
            sum(g.gap for g in skill_result.gaps) / len(skill_result.gaps)
            if skill_result.gaps else 50.0
        )

        # ---------------- DECIDE: Explain prioritization ----------------
        result.decision_explanation = self._explain_decision(result.ranked_gaps)

        # ---------------- ACT: Generate plan ----------------
        plan_result = self._run_planner(goal_info, effective_role, timeframe, skill_result.gaps)
        result.plan = plan_result

        # ---------------- EVALUATE ----------------
        evaluation = self._run_evaluator(
            effective_role, resume_result, github_result, job_result, avg_gap
        )
        result.evaluation = evaluation

        # ---------------- ADAPT / REPLAN ----------------
        needs_replan = (not github_result.success) or evaluation.needs_replan
        if needs_replan:
            trigger_reason, new_context = self._build_replan_context(github_result, evaluation)
            self._emit("warning", f"Issue detected: {trigger_reason}")
            self._emit("info", "Agent evaluating failure / issue")
            self._emit("info", "Selecting fallback strategy")

            adapted_result = replan(
                original_steps=plan_result.steps,
                gaps=skill_result.gaps,
                trigger_reason=trigger_reason,
                new_context=new_context,
            )
            result.adapted = True
            result.adapted_plan = adapted_result
            self._emit("success", "Using available profile/resume information")
            self._emit("success", "Recalculating skill gaps")
            self._emit("success", "Updating career plan (adapted)")
        else:
            self._emit("success", "Progress evaluated")

        result.activity_log = self.log
        return result

    # ------------------------------------------------------------------
    # Individual step implementations
    # ------------------------------------------------------------------

    def _understand_goal(self, goal: str, target_role: str, current_skills: str) -> dict:
        if is_llm_available():
            try:
                prompt = GOAL_UNDERSTANDING_PROMPT.format(
                    goal=goal or "Not specified",
                    target_role=target_role or "Not specified",
                    current_skills=current_skills or "Not specified",
                )
                raw = call_gemini_json(prompt)
                if isinstance(raw, dict) and raw.get("target_role"):
                    raw.setdefault("timeframe_months", 6)
                    return raw
            except Exception:
                pass
        # local fallback
        return {
            "target_role": target_role or "AI/ML Engineer",
            "timeframe_months": 6,
            "focus_area": "AI/ML engineering",
            "intent_summary": goal or "Become job-ready for the target role.",
        }

    def _run_resume_tool(self, resume_file: Optional[BinaryIO]) -> ResumeResult:
        if resume_file is None:
            self._emit("warning", "No resume uploaded — skipping resume analysis")
            return ResumeResult(success=False, error="No resume uploaded")
        res = parse_resume(resume_file)
        if res.success:
            self._emit("success", "Resume parsed")
        else:
            self._emit("warning", f"Resume analysis issue: {res.error}")
        return res

    def _run_github_tool(self, username: str, force_failure: bool) -> GitHubResult:
        res = analyze_github(username, force_failure=force_failure)
        if res.success:
            self._emit("success", "GitHub analyzed")
        elif res.simulated_failure:
            self._emit("error", "GitHub tool failed (simulated demo failure)")
        else:
            self._emit("warning", f"GitHub analysis failed: {res.error}")
        return res

    def _run_job_research(self, target_role: str) -> JobResearchResult:
        res = research_job_requirements(target_role)
        if res.source == "live":
            self._emit("success", "Job requirements researched (live)")
        else:
            self._emit("success", "Job requirements researched (fallback demo dataset)")
        return res

    def _run_skill_analysis(self, target_role, job_result, current_skills, resume_result, github_result) -> SkillAnalysisResult:
        resume_skills = resume_result.detected_skills if resume_result.success else []
        github_skills = github_result.languages if github_result.success else []
        res = analyze_skill_gaps(
            target_role=target_role,
            required_skills=job_result.required_skills,
            current_skills=current_skills,
            resume_skills=resume_skills,
            github_skills=github_skills,
            github_available=github_result.success,
        )
        self._emit("success", "Skill gaps identified")
        self._emit("success", "Priority decided")
        return res

    def _explain_decision(self, ranked_gaps: list) -> str:
        if not ranked_gaps:
            return "No significant skill gaps were identified from the available evidence."
        if is_llm_available():
            try:
                text_gaps = "\n".join(
                    f"- {g['skill']}: importance={g['importance']}, gap={g['gap']}, "
                    f"priority_score={g['priority_score']}"
                    for g in ranked_gaps[:5]
                )
                prompt = DECISION_EXPLANATION_PROMPT.format(ranked_gaps=text_gaps)
                from agents.llm_client import call_gemini
                return call_gemini(prompt).strip()
            except Exception:
                pass
        top = ranked_gaps[:3]
        names = ", ".join(g["skill"] for g in top)
        return (
            f"The agent prioritized {names} because they combine high importance to the "
            f"target role with the largest current skill gaps (priority_score = "
            f"importance x gap x relevance)."
        )

    def _run_planner(self, goal_info: dict, target_role: str, timeframe: int, gaps: list) -> PlanResult:
        res = generate_plan(
            intent_summary=goal_info.get("intent_summary", ""),
            target_role=target_role,
            timeframe_months=timeframe,
            gaps=gaps,
        )
        self._emit("success", "Career plan generated")
        return res

    def _run_evaluator(self, target_role, resume_result, github_result, job_result, avg_gap) -> EvaluationResult:
        num_projects = len(github_result.top_repos) if github_result.success else 0
        res = evaluate(
            target_role=target_role,
            resume_available=resume_result.success,
            github_available=github_result.success,
            num_required_skills=len(job_result.required_skills),
            avg_gap=avg_gap,
            num_projects=num_projects,
        )
        return res

    def _build_replan_context(self, github_result: GitHubResult, evaluation: EvaluationResult) -> tuple:
        reasons = []
        if not github_result.success:
            if github_result.simulated_failure:
                reasons.append("GitHub analysis failed (simulated demo failure)")
            else:
                reasons.append(f"GitHub analysis failed ({github_result.error})")
        if evaluation.needs_replan:
            reasons.append("Evaluator flagged readiness/profile issues")

        trigger_reason = "; ".join(reasons) if reasons else "Evaluation identified issues"
        new_context = (
            "GitHub evidence unavailable — leaning on resume and self-reported skills"
            if not github_result.success
            else "Evaluator recommendations: " + "; ".join(evaluation.recommendations)
        )
        return trigger_reason, new_context
