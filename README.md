# 🧭 CareerPilot — Agentic AI Career Execution System

> **An autonomous AI agent that plans, executes, evaluates, and adapts a student's path toward their career goal — not just a chatbot that prints a roadmap.**

---

## 🎯 Problem

Students often receive generic career advice such as *"learn X, build Y, and apply for Z."*

Traditional career tools and one-shot AI prompts usually provide static recommendations. They do not continuously analyze a student's actual evidence, prioritize what matters most, respond to failures, or revise the plan when circumstances change.

Career preparation is dynamic — students improve, requirements change, data sources fail, and new information becomes available.

**The problem:** students need a system that doesn't just tell them what to do, but continuously **analyzes, decides, evaluates, and adapts**.

---

## 💡 Solution

**CareerPilot** is an Agentic AI career-execution system that runs a complete:

> **GOAL → OBSERVE → DECIDE → ACT → EVALUATE → ADAPT**

loop.

### 1. 🎯 Goal

Understands the student's target career, role, and timeframe.

### 2. 👀 Observe

Collects evidence from:

* Resume
* GitHub profile
* Student-provided skills
* Job/role requirements

### 3. 🧠 Decide

Identifies and prioritizes skill gaps using:

```text
priority_score = importance × gap × relevance
```

This allows the system to determine which skills should be addressed first.

### 4. ⚙️ Act

Uses the Planner to generate a concrete, sequenced action plan based on the identified priorities.

### 5. 📊 Evaluate

Evaluates:

* Skill readiness
* Project readiness
* Resume readiness
* Profile completeness
* Alignment with the target career

### 6. 🔄 Adapt

When a tool fails, information is missing, or evaluation identifies an issue, CareerPilot reassesses the situation and generates an **adapted plan**.

---

# 🤖 Why Agentic AI?

CareerPilot is designed as an **agentic system**, rather than a conventional chatbot.

### Traditional chatbot

```text
User Question
      ↓
LLM
      ↓
Answer
      ↓
STOP
```

### CareerPilot

```text
GOAL
  ↓
OBSERVE
  ↓
DECIDE
  ↓
ACT
  ↓
EVALUATE
  ↓
Success?
 ├── YES → Final Outcome
 └── NO  → ADAPT → REPLAN
                    ↓
                  ACT
```

CareerPilot demonstrates agentic behavior through:

* **Multiple tool calls** performed in sequence
* **Evidence-based decision making**
* **Quantitative skill prioritization**
* **Failure detection**
* **Fallback strategy selection**
* **Dynamic replanning**
* **Observable agent activity**
* **State maintained across the execution**

The system does not simply regenerate the same answer. Its plan changes according to the information and tool outcomes available to it.

---

# ✨ Key Features

### 🧠 Agentic Career Controller

Coordinates the complete Goal → Observe → Decide → Act → Evaluate → Adapt workflow.

### 📄 Resume Analysis

Extracts information from PDF resumes locally using **PyMuPDF**.

### 🐙 GitHub Analysis

Analyzes publicly available GitHub information including:

* Repositories
* Programming languages
* Stars
* Project activity
* Project diversity
* Other available project signals

### 🔎 Job Requirements Research

Uses a modular job-research tool with support for external search and a clearly labeled fallback dataset when live search is unavailable.

### 📊 Skill Gap Analyzer

Combines:

* Self-reported skills
* Resume evidence
* GitHub evidence
* Target-role requirements

to identify and rank skill gaps.

### 📋 Intelligent Planner

Creates a prioritized and sequenced career action plan.

### 📈 Career Readiness Evaluator

Produces readiness scores and identifies areas requiring improvement.

### 🔄 Adaptive Replanner

When the system encounters a failure or identifies a major issue, it revises the career plan rather than simply stopping.

### ⚠️ Demo Failure Mode

A controlled failure mode allows the complete adaptation loop to be demonstrated reliably during a hackathon presentation.

### 💾 Run History

SQLite stores lightweight execution history.

### 🛡️ Graceful Fallbacks

LLM and external-tool failures are handled gracefully where possible, allowing the application to continue using deterministic local fallbacks.

---

# 🔄 Agent Workflow

```text
                    ┌──────────────┐
                    │     GOAL     │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │   OBSERVE    │
                    └──────┬───────┘
                           ↓
              ┌────────────┼────────────┐
              ↓            ↓            ↓
        Resume Tool   GitHub Tool   Job Research
              └────────────┼────────────┘
                           ↓
                    ┌──────────────┐
                    │    DECIDE    │
                    │ Skill Gaps   │
                    │ Priorities   │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │     ACT      │
                    │    Planner   │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │   EVALUATE   │
                    └──────┬───────┘
                           ↓
                       Success?
                      /         \
                    YES          NO
                    ↓             ↓
              Final Plan      ADAPT
                                ↓
                             REPLAN
                                ↓
                              ACT
```

---

# 🏗️ Architecture

```text
┌──────────────────────┐
│        User          │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│    Streamlit UI      │
│       app.py         │
└──────────┬───────────┘
           ↓
┌──────────────────────────────┐
│ CareerPilot Agent Controller │
│    agents/career_agent.py    │
└──────────────┬───────────────┘
               ↓
       ┌───────────────┐
       │    Planner    │
       └───────┬───────┘
               ↓
        ┌──────┴──────┐
        ↓             ↓
   Tool Layer      Profile
        ↓
 ┌──────┼───────────────┐
 ↓      ↓               ↓
Resume GitHub       Job Research
Tool    Tool             Tool
 └──────┼───────────────┘
        ↓
┌───────────────────────┐
│  Skill Gap Analyzer   │
└───────────┬───────────┘
            ↓
┌───────────────────────┐
│      Evaluator        │
└───────────┬───────────┘
            ↓
         Success?
        /       \
      YES        NO
       ↓          ↓
 Final Plan    Replanner
                  ↓
                Adapt
                  ↓
               Re-evaluate

        ↓
┌───────────────────────┐
│ SQLite + Session State│
└───────────────────────┘
```

### LLM Layer

Gemini integration is isolated inside:

```text
agents/llm_client.py
```

This keeps the LLM provider separate from the rest of the application and allows model configuration through environment variables.

---

# 🛠️ Tech Stack

| Technology            | Purpose                         |
| --------------------- | ------------------------------- |
| **Python 3.10+**      | Core application                |
| **Streamlit**         | Interactive dashboard           |
| **Google Gemini API** | AI reasoning                    |
| **PyMuPDF**           | Local resume PDF extraction     |
| **GitHub REST API**   | GitHub profile/project analysis |
| **SQLite**            | Lightweight execution history   |
| **python-dotenv**     | Environment configuration       |

---

# 📁 Project Structure

```text
CareerPilot/
│
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── agents/
│   ├── __init__.py
│   ├── llm_client.py
│   ├── career_agent.py
│   ├── planner.py
│   ├── evaluator.py
│   └── replanner.py
│
├── tools/
│   ├── __init__.py
│   ├── resume_parser.py
│   ├── github_tool.py
│   ├── job_search.py
│   └── skill_analyzer.py
│
├── database/
│   ├── __init__.py
│   └── database.py
│
├── prompts/
│   ├── __init__.py
│   └── prompts.py
│
└── demo/
    └── sample_profile.json
```

---

# 🚀 Setup

## 1. Clone the repository

```bash
git clone https://github.com/Sriyut-Singh/CareerPilot.git
cd CareerPilot
```

## 2. Create a virtual environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure environment variables

Copy:

```text
.env.example
```

to:

```text
.env
```

Then add your credentials.

---

# 🔐 Environment Variables

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_supported_gemini_model
GITHUB_TOKEN=optional_github_token
SEARCH_API_KEY=optional_search_provider_key
```

### Variables

**`GEMINI_API_KEY`**
Enables Gemini-powered reasoning. If unavailable, CareerPilot can use deterministic local fallbacks for supported operations.

**`GEMINI_MODEL`**
Specifies the Gemini model used by the application.

**`GITHUB_TOKEN`**
Optional token for increased GitHub API rate limits.

**`SEARCH_API_KEY`**
Optional key for live job/role research. When unavailable, the application uses a clearly labeled fallback dataset.

> ⚠️ **Never commit `.env` or API keys to GitHub.**

---

# ▶️ Run CareerPilot

```bash
streamlit run app.py
```

Streamlit will provide a local URL, typically:

```text
http://localhost:8501
```

---

# ⚠️ Demo Failure Mode

CareerPilot includes a controlled **Demo Failure Mode** designed to demonstrate robustness and adaptation.

Enable:

> **⚠️ Demo Failure Mode**

before clicking **Run CareerPilot**.

The GitHub tool then returns a clearly labeled simulated failure instead of making a real GitHub request.

The Agent Activity panel demonstrates:

```text
✓ Goal understood
✓ Resume analyzed
✓ Job requirements researched
⚠ GitHub analysis failed
↻ Evaluating failure
↻ Selecting fallback strategy
✓ Continuing with available evidence
✓ Recalculating skill gaps
✓ Updating career plan
```

The application then produces an **Adapted Plan** that explicitly accounts for the missing GitHub evidence.

This is a controlled robustness test and is **not presented as a real API failure**.

---

# 🎬 Demo Workflow

A recommended hackathon demonstration:

### 1. Define the goal

```text
I want to become an AI/ML engineer
and get an internship within 6 months.
```

### 2. Provide evidence

* Upload resume
* Enter GitHub username
* Enter current skills

### 3. Run CareerPilot

Show the Agent Activity panel.

### 4. Show the decision

Display:

* Career readiness
* Skill gaps
* Priority scores
* Agent's reasoning for prioritization

### 5. Show the action

Display the generated career plan.

### 6. Trigger failure

Enable:

```text
⚠️ Demo Failure Mode
```

### 7. Show adaptation

Demonstrate:

```text
Failure
   ↓
Evaluation
   ↓
Fallback
   ↓
Recalculation
   ↓
Replanning
   ↓
Adapted Outcome
```

### 8. Final outcome

Show the updated roadmap and explain:

> **"CareerPilot doesn't just answer the student. It observes, decides, acts, evaluates, and adapts."**

---

# 📌 Example

### User Goal

> I want to become an AI/ML engineer and get an internship within 6 months.

CareerPilot analyzes the available evidence and may identify:

```text
Python       → Strong
SQL          → Weak
Machine Learning → Moderate
DSA          → Weak
Projects     → Moderate
Resume       → Needs improvement
```

It then calculates priorities and creates a sequence such as:

```text
1. Strengthen SQL
2. Improve DSA fundamentals
3. Build a deployable ML project
4. Improve resume project descriptions
5. Apply to relevant internships
```

If GitHub evidence becomes unavailable, the system adapts the analysis instead of terminating the execution.

---

# 🔬 What Makes CareerPilot Agentic?

CareerPilot combines:

```text
Goal
 ↓
Evidence Collection
 ↓
Tool Usage
 ↓
Decision
 ↓
Action
 ↓
Evaluation
 ↓
Failure Detection
 ↓
Adaptation
 ↓
Replanning
```

The important distinction is that the system's next action depends on the results of previous actions.

It is therefore designed as an **execution loop**, rather than a single prompt-response interaction.

---

# 🔮 Future Improvements

* Live job-market intelligence across multiple sources
* Long-term tracking of skill progress
* Resume improvement suggestions tied to identified gaps
* OAuth-based GitHub integration
* Progress tracking across multiple career sessions
* Personalized project recommendations
* Internship/application tracking
* Roadmap export to PDF or productivity platforms

---

# 🏆 Hackathon Focus

CareerPilot is built around the principle:

> **Don't just tell the student what to do. Continuously figure out what should happen next.**

**Goal → Observe → Decide → Act → Evaluate → Adapt**

---

## 📄 License

This project currently does not specify an open-source license.
