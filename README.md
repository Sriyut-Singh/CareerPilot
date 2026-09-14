# 🧭 CareerPilot — Agentic AI Career Execution System

**CareerPilot is an agentic career-planning system that gathers profile evidence, makes prioritization decisions, executes a plan, evaluates readiness, and adapts when something goes wrong.**

## 🚀 Live Demo

**Try the deployed app:** https://careerpilot-sriyut.streamlit.app/

**Source code:** https://github.com/Sriyut-Singh/CareerPilot

## 🎯 Problem

Students often receive generic career roadmaps that do not use their actual resume/project evidence and do not react when information is missing or a tool fails.

CareerPilot treats career planning as an **execution problem**, not a one-shot chatbot prompt.

## 💡 Solution

CareerPilot runs a complete:

**Goal → Observe → Decide → Act → Evaluate → Adapt** loop.

- **Goal:** understand the student's target role and timeframe.
- **Observe:** collect evidence from the resume, GitHub, and job-requirement research.
- **Decide:** rank skill gaps using `priority_score = importance × gap × relevance`.
- **Act:** generate a sequenced career action plan.
- **Evaluate:** score readiness across profile, skills, projects, resume, and goal alignment.
- **Adapt:** if a tool fails or readiness issues are detected, select a fallback strategy, recalculate gaps, and generate an adapted plan.

## 🤖 Why this is Agentic AI

CareerPilot is designed as an **agentic controller**, not merely a chatbot:

1. It uses multiple tools and combines their outputs as evidence.
2. It makes explicit prioritization decisions.
3. It evaluates the result after execution.
4. It detects failures and changes strategy.
5. It produces a distinct adapted plan after replanning.
6. It exposes the execution history through the Agent Activity panel.
7. Gemini provides LLM reasoning where available, while deterministic local fallbacks keep the system operational if an LLM call fails.

### Failure-recovery demo

The app includes a **Demo Failure Mode** that intentionally simulates a GitHub tool failure. This makes the adaptation loop easy to demonstrate without depending on a real outage.

Expected flow:

```text
❌ GitHub tool failed
        ↓
⚠️ Issue detected
        ↓
↻ Evaluate failure
        ↓
↻ Select fallback strategy
        ↓
✅ Use available resume/profile evidence
        ↓
✅ Recalculate skill gaps
        ↓
✅ Update career plan (adapted)
```

## 🏗️ Architecture

```text
User
  ↓
Streamlit UI (app.py)
  ↓
CareerPilot Agent / Controller
  ↓
┌─────────────────────────────────────────┐
│ Observe                                 │
│  ├─ Resume Parser                       │
│  ├─ GitHub Analyzer                     │
│  └─ Job Requirements Researcher         │
└─────────────────────────────────────────┘
  ↓
Skill Gap Analyzer
  ↓
Decision / Priority Scoring
  ↓
Planner
  ↓
Evaluator
  ↓
Needs adaptation?
  ├─ NO  → Final Career Plan
  └─ YES → Replanner → Adapted Career Plan
  ↓
Agent Activity + SQLite Run History
```

Gemini integration is isolated in `agents/llm_client.py`. No API key is stored in source code.

## ✨ Features

- 🤖 Gemini-powered reasoning for goal understanding and priority decisions
- 📄 Local PDF resume parsing with PyMuPDF
- 🐙 Real GitHub REST API project/profile analysis
- 🔎 Job-requirements research with a clearly labeled fallback dataset
- 🧠 Evidence-based skill-gap analysis
- 📊 Quantitative priority scoring
- 🗺️ Personalized, sequenced action plan
- 📈 Career readiness evaluation
- 🔄 Automatic fallback + replanning after failures
- ⚠️ Demo Failure Mode for reliable hackathon demonstration
- 🗃️ SQLite run history
- 🛡️ Deterministic local fallback when Gemini is unavailable
- 🌐 Deployed with Streamlit Community Cloud

## 🛠️ Tech Stack

- **Python 3.10+**
- **Streamlit** — web UI
- **Google Gemini API / `google-genai`** — LLM reasoning
- **PyMuPDF** — PDF resume extraction
- **GitHub REST API** — project evidence
- **SQLite** — run history
- **python-dotenv** — local configuration

## 📁 Project Structure

```text
CareerPilot/
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
├── agents/
│   ├── career_agent.py
│   ├── evaluator.py
│   ├── llm_client.py
│   ├── planner.py
│   └── replanner.py
├── tools/
│   ├── github_tool.py
│   ├── job_search.py
│   ├── resume_parser.py
│   └── skill_analyzer.py
├── database/
│   └── database.py
├── prompts/
│   └── prompts.py
└── demo/
    └── sample_profile.json
```

## 🔐 Secrets & Security

**Never commit API keys.** CareerPilot reads secrets from Streamlit Community Cloud Secrets in deployment and environment variables for local development.

Required for Gemini reasoning:

```text
GEMINI_API_KEY = "your_key_here"
GEMINI_MODEL = "gemini-3.6-flash"
```

Optional:

```text
GITHUB_TOKEN = "optional_token"
SEARCH_API_KEY = "optional_live_search_key"
```

Real `.env` and `.streamlit/secrets.toml` files are intentionally excluded from Git.

## ▶️ Local Setup

```bash
git clone https://github.com/Sriyut-Singh/CareerPilot.git
cd CareerPilot
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
streamlit run app.py
```

## ☁️ Deployment

The application is deployed on **Streamlit Community Cloud**.

Set the required values under the app's **Secrets** settings. Do not put real credentials in GitHub or the README.

The application remains functional with deterministic local fallbacks if Gemini or optional external services are unavailable.

## 🎬 Hackathon Demo

### Normal run

1. Enter a career goal and target role.
2. Upload a resume PDF.
3. Enter a GitHub username.
4. Enter current skills.
5. Run CareerPilot.
6. Show the Agent Activity sequence and Career Readiness results.
7. Highlight the Gemini reasoning events.

### Failure-recovery run

1. Enable **⚠️ Demo Failure Mode**.
2. Run CareerPilot again.
3. Show the simulated GitHub failure.
4. Point out the evaluator detecting the issue.
5. Show fallback selection and recalculated skill gaps.
6. Show the **Adapted Plan**.

### One-line judge explanation

> **“CareerPilot is an agentic career execution system: it observes real profile evidence, decides what matters, acts by generating a plan, evaluates the outcome, and replans when its tools or assumptions fail.”**

## 📌 Current Scope / Honest Limitations

- Job requirements use a **labeled fallback demo dataset** when no live search provider is configured.
- GitHub analysis uses a username and the GitHub REST API; authentication is optional.
- SQLite run history is best-effort on Streamlit Cloud because the cloud filesystem is ephemeral.
- The Demo Failure Mode is intentionally simulated for reliable evaluation of the adaptation path.

## 🔮 Future Improvements

- Live job-market search provider integration
- Persistent multi-session skill-progress memory
- Resume rewriting tied to identified skill gaps
- OAuth-based GitHub connection
- Roadmap export to PDF/Notion
