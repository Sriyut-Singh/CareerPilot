# 🧭 CareerPilot — Agentic AI Career Execution System

**An autonomous agent that plans, executes, evaluates, and adapts a student's path to their career goal — not just a chatbot that prints a roadmap.**

## Problem

Students get generic "learn X, do Y" career advice from static tools or one-shot chatbot prompts. That advice doesn't adapt when a data source fails, when the student's actual profile contradicts their self-assessment, or when new information changes the picture. Nobody *acts* on the student's behalf to gather evidence, reason about priorities, and revise the plan.

## Solution

CareerPilot is an agentic controller that runs a full **Goal → Observe → Decide → Act → Evaluate → Adapt** loop:

1. **Goal** — understands the student's stated career goal and timeframe.
2. **Observe** — gathers evidence from three tools: a Resume parser, a GitHub analyzer, and a Job Requirements researcher.
3. **Decide** — computes `priority_score = importance × gap × relevance` to rank skill gaps and decide what matters most.
4. **Act** — calls the Planner to generate a concrete, sequenced action plan.
5. **Evaluate** — scores profile/skill/project/resume readiness and overall goal alignment.
6. **Adapt** — if a tool fails (e.g. GitHub is unreachable) or the Evaluator flags an issue, the Replanner generates a revised plan that explicitly accounts for what changed.

## Why Agentic AI (not a chatbot)

A chatbot answers a prompt once. CareerPilot:
- Calls **multiple real tools** in sequence and combines their outputs as evidence.
- Makes **quantitative prioritization decisions** (priority_score formula), not just prose.
- **Detects failure conditions** (missing data, tool errors, low readiness) and **visibly reacts** to them.
- **Regenerates its own plan** based on the new situation — the adaptation is a distinct, inspectable output, not a rephrased answer.
- Tracks every step in an **activity log** so the reasoning process is observable, not hidden inside one LLM call.

## Key Features

- Clean Streamlit dashboard with a live **Agent Activity** panel
- Real GitHub REST API analysis (languages, repos, stars, activity)
- Local PDF resume parsing (PyMuPDF) — never uploaded externally
- Modular job-requirements research with a clearly labeled fallback dataset
- Skill Gap Analyzer combining self-reported + resume + GitHub evidence
- Planner using `importance × gap × relevance` prioritization
- Evaluator producing a readiness score + recommendations
- Replanner that adapts the plan when tools fail or issues are found
- **Demo Failure Mode** checkbox to reliably showcase the adaptation loop
- SQLite run history
- Every reasoning step has a deterministic local fallback if Gemini is unavailable — the app never crashes due to a missing/failed LLM call

## Agent Workflow

```
GOAL
  → OBSERVE  (Resume Tool, GitHub Tool, Job Research Tool)
  → DECIDE   (priority_score = importance × gap × relevance)
  → ACT      (Planner generates sequenced steps)
  → EVALUATE (readiness scores, needs_replan flag)
  → ADAPT    (Replanner revises the plan if needed)
  → OUTPUT   (Roadmap + full reasoning/action history)
```

## Architecture

```
User
 ↓
Streamlit UI (app.py)
 ↓
CareerPilot Agent / Controller (agents/career_agent.py)
 ↓
Planner (agents/planner.py)
 ↓
Tool Selection
 ├── Resume Tool        (tools/resume_parser.py)
 ├── GitHub Tool         (tools/github_tool.py)
 └── Job Research Tool   (tools/job_search.py)
 ↓
Skill Gap Analyzer (tools/skill_analyzer.py)
 ↓
Evaluator (agents/evaluator.py)
 ↓
Success?
 ├── YES → Final Career Plan
 └── NO  → Replanner (agents/replanner.py) → back to Agent
 ↓
SQLite state (database/database.py) + Streamlit session_state
```

Gemini LLM calls are isolated in `agents/llm_client.py` — no other module talks to the SDK directly, and every LLM-backed function has a deterministic local fallback.

## Tech Stack

- Python 3.10+
- Streamlit — UI
- Google Gemini API (`google-generativeai`) — reasoning
- PyMuPDF — resume PDF extraction
- GitHub REST API — project evidence
- SQLite — lightweight run history
- python-dotenv — secret/config management

## Project Structure

```
CareerPilot/
├── app.py                       # Streamlit entry point
├── config.py                    # single source of truth for secrets/config
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── .streamlit/
│   ├── config.toml               # Streamlit server/theme config
│   └── secrets.toml.example      # template only, never commit real secrets.toml
├── agents/
│   ├── __init__.py
│   ├── llm_client.py      # isolated Gemini integration
│   ├── career_agent.py    # the agentic controller/loop
│   ├── planner.py
│   ├── evaluator.py
│   └── replanner.py
├── tools/
│   ├── __init__.py
│   ├── resume_parser.py
│   ├── github_tool.py
│   ├── job_search.py
│   └── skill_analyzer.py
├── database/
│   ├── __init__.py
│   └── database.py         # writes to OS temp dir; best-effort, never blocks the app
├── prompts/
│   ├── __init__.py
│   └── prompts.py
└── demo/
    └── sample_profile.json
```

## Deploying to Streamlit Community Cloud

1. Push this repository to GitHub (make sure `.env`, `.streamlit/secrets.toml`, and any `*.db` files are **not** committed — `.gitignore` already excludes them).
2. Go to [share.streamlit.io](https://share.streamlit.io), click **New app**, and select this repo/branch.
3. Set **Main file path** to `app.py`.
4. Under **Advanced settings → Secrets**, paste:
   ```toml
   GEMINI_API_KEY = "your_gemini_api_key_here"
   GEMINI_MODEL = "gemini-2.0-flash"
   GITHUB_TOKEN = "optional_personal_access_token"
   SEARCH_API_KEY = "optional_live_job_search_key"
   ```
5. Click **Deploy**.

`GEMINI_API_KEY` is optional at deploy time — CareerPilot runs fully on deterministic local fallbacks without it and shows a friendly in-app notice instead of crashing. `GITHUB_TOKEN` and `SEARCH_API_KEY` are also optional (raises GitHub rate limits / enables live job search respectively).

Local run history is stored in the OS temp directory via SQLite as a best-effort convenience only — Streamlit Cloud's filesystem is ephemeral, so this is not guaranteed to persist across restarts, and the app is fully functional without it.

## Setup Instructions

```bash
cd CareerPilot
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Environment Variables / Secrets

Config values are resolved centrally in `config.py`, preferring **Streamlit secrets** and falling back to **environment variables** (`.env`) for local development only:

```
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash
GITHUB_TOKEN=optional_personal_access_token_for_higher_rate_limits
SEARCH_API_KEY=optional_live_job_search_provider_key
```

- `GEMINI_API_KEY` — enables LLM-powered reasoning. Without it, CareerPilot still runs fully using deterministic local fallbacks for every step, with a friendly in-app notice.
- `GEMINI_MODEL` — change to any current Gemini model name without touching code.
- `GITHUB_TOKEN` — optional; raises GitHub's unauthenticated rate limit.
- `SEARCH_API_KEY` — optional; if unset, Job Research Tool uses a clearly labeled fallback demo dataset.

For **local development**, copy `.env.example` to `.env` and fill in values (or copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`). For **Streamlit Community Cloud**, set the same keys under the app's Settings → Secrets — never commit a real `.env` or `secrets.toml`.

## How to Run

```bash
streamlit run app.py
```

Then open the local URL Streamlit prints (typically `http://localhost:8501`).

## Demo Failure Mode

Check **"⚠️ Demo Failure Mode"** in the sidebar before clicking **Run CareerPilot**. This forces the GitHub Tool to return a clearly labeled simulated failure (no real API call is made and pretended to succeed). The Agent Activity panel will show the tool failing, the agent evaluating the failure, selecting a fallback strategy, and producing an **Adapted Plan** that explicitly references the missing GitHub evidence.

## Example Workflow

1. Enter goal: *"I want to become an AI/ML engineer and get an internship within 6 months."*
2. Upload a resume PDF and enter a GitHub username.
3. Click **Run CareerPilot**.
4. Watch the Agent Activity panel execute Goal → Observe → Decide → Act → Evaluate.
5. Review Career Readiness score, Skill Gap table, Agent Decision explanation, and Action Plan.
6. Enable Demo Failure Mode and run again to see the Adapted Plan appear.

## Future Improvements

- Real live job-market search provider integration (the module is already isolated for this)
- Multi-session memory of skill progress over time
- Resume rewriting suggestions tied directly to identified gaps
- OAuth-based GitHub connection instead of username-only lookup
- Export the roadmap as PDF/Notion
