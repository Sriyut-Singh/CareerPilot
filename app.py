"""
CareerPilot — Agentic AI Career Execution System
Streamlit front-end. Run with: streamlit run app.py
"""
import streamlit as st
import pandas as pd

from agents.career_agent import CareerPilotAgent
from agents.llm_client import is_llm_available
from database.database import save_run, get_recent_runs

st.set_page_config(page_title="CareerPilot", page_icon="🧭", layout="wide")

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🧭 CareerPilot")
st.markdown("#### Agentic AI Career Execution System")
st.caption("Goal → Observe → Decide → Act → Evaluate → Adapt")

if not is_llm_available():
    st.warning(
        "GEMINI_API_KEY is not configured. CareerPilot will still run using "
        "deterministic local fallbacks for every reasoning step, but LLM-powered "
        "reasoning will be disabled. Set GEMINI_API_KEY in your .env to enable it.",
        icon="⚠️",
    )

# ---------------------------------------------------------------------------
# Sidebar: inputs
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Student Inputs")
    goal = st.text_area(
        "Career Goal",
        placeholder="I want to become an AI/ML engineer and get an internship within 6 months.",
        height=80,
    )
    target_role = st.text_input("Target Role (optional)", placeholder="AI/ML Engineer")
    resume_file = st.file_uploader("Resume (PDF)", type=["pdf"])
    github_username = st.text_input("GitHub Username", placeholder="octocat")
    current_skills = st.text_area(
        "Current Skills / Profile",
        placeholder="Python, pandas, basic ML coursework, SQL",
        height=80,
    )

    st.divider()
    demo_failure_mode = st.checkbox(
        "⚠️ Demo Failure Mode (simulate GitHub tool failure)",
        help="Forces the GitHub Tool to fail so you can demonstrate the agent's "
             "adaptation / replanning behavior.",
    )
    run_clicked = st.button("🚀 Run CareerPilot", type="primary", use_container_width=True)

    st.divider()
    with st.expander("Recent Runs (SQLite)"):
        recent = get_recent_runs(5)
        if recent:
            st.dataframe(pd.DataFrame(recent), hide_index=True, use_container_width=True)
        else:
            st.caption("No runs yet.")

# ---------------------------------------------------------------------------
# Run the agent
# ---------------------------------------------------------------------------
if run_clicked:
    if not goal.strip():
        st.error("Please enter a career goal before running CareerPilot.")
        st.stop()

    agent = CareerPilotAgent()
    with st.spinner("CareerPilot agent is working through its Goal→Observe→Decide→Act→Evaluate→Adapt loop..."):
        result = agent.run(
            goal=goal,
            resume_file=resume_file,
            github_username=github_username,
            current_skills=current_skills,
            target_role=target_role,
            force_github_failure=demo_failure_mode,
        )
    st.session_state["last_result"] = result

# ---------------------------------------------------------------------------
# Render results
# ---------------------------------------------------------------------------
result = st.session_state.get("last_result")

if result:
    # ---------------- Agent Activity Panel ----------------
    st.subheader("🔄 Agent Activity")
    icon_map = {"success": "✅", "warning": "⚠️", "error": "❌", "info": "↻"}
    activity_cols = st.columns(1)
    for event in result.activity_log:
        icon = icon_map.get(event.status, "•")
        if event.status == "error":
            st.error(f"{icon} {event.message}")
        elif event.status == "warning":
            st.warning(f"{icon} {event.message}")
        elif event.status == "info":
            st.info(f"{icon} {event.message}")
        else:
            st.success(f"{icon} {event.message}")

    st.divider()

    # ---------------- Career Readiness ----------------
    ev = result.evaluation
    st.subheader("📊 Career Readiness")
    score = ev.overall_score if ev else 0
    st.metric("Overall Readiness Score", f"{score}%")
    st.progress(min(max(score, 0), 100) / 100)

    cols = st.columns(5)
    if ev:
        cols[0].metric("Profile", f"{ev.profile_completeness}%")
        cols[1].metric("Skills", f"{ev.skill_readiness}%")
        cols[2].metric("Projects", f"{ev.project_readiness}%")
        cols[3].metric("Resume", f"{ev.resume_readiness}%")
        cols[4].metric("Goal Alignment", f"{ev.goal_alignment}%")

        if ev.recommendations:
            st.markdown("**Evaluator Recommendations:**")
            for r in ev.recommendations:
                st.markdown(f"- {r}")

    st.divider()

    # ---------------- Skill Gap Analysis ----------------
    st.subheader("🧩 Skill Gap Analysis")
    if result.ranked_gaps:
        df = pd.DataFrame(result.ranked_gaps)
        df = df.rename(columns={
            "skill": "Skill", "current_level": "Current", "required_level": "Required",
            "gap": "Gap", "importance": "Importance", "priority_score": "Priority Score",
        })
        st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.caption("No skill gap data available.")

    st.divider()

    # ---------------- Agent Decision ----------------
    st.subheader("🧠 Agent Decision")
    st.write(result.decision_explanation)
    if result.job_research and result.job_research.source == "fallback_demo_dataset":
        st.caption("ℹ️ Job requirements used a labeled fallback demo dataset (no live search API configured).")

    st.divider()

    # ---------------- Personalized Action Plan ----------------
    st.subheader("🗺️ Personalized Action Plan")
    if result.plan and result.plan.steps:
        plan_rows = [{
            "Priority": s.priority,
            "Action": s.action,
            "Reason": s.reason,
            "Expected Outcome": s.expected_outcome,
            "Timeframe": s.timeframe,
        } for s in result.plan.steps]
        st.dataframe(pd.DataFrame(plan_rows), hide_index=True, use_container_width=True)
    else:
        st.caption("No plan generated.")

    # ---------------- Adapted Plan (only if adaptation occurred) ----------------
    if result.adapted and result.adapted_plan and result.adapted_plan.steps:
        st.divider()
        st.subheader("🔁 Adapted Plan")
        st.info(f"Adaptation triggered by: {result.adapted_plan.trigger_reason}")
        adapted_rows = [{
            "Priority": s.priority,
            "Action": s.action,
            "Reason": s.reason,
            "Expected Outcome": s.expected_outcome,
            "Timeframe": s.timeframe,
        } for s in result.adapted_plan.steps]
        st.dataframe(pd.DataFrame(adapted_rows), hide_index=True, use_container_width=True)

    # ---------------- Persist run ----------------
    save_run(
        goal=goal,
        target_role=target_role or (result.goal_info.get("target_role", "")),
        github_username=github_username,
        overall_score=score,
        adapted=result.adapted,
        adaptation_reason=(result.adapted_plan.trigger_reason if result.adapted_plan else ""),
        plan=[s.__dict__ for s in (result.plan.steps if result.plan else [])],
    )
else:
    st.info("Fill in the inputs on the left and click **🚀 Run CareerPilot** to start the agent.")
