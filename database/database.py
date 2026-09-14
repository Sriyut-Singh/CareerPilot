"""
Lightweight SQLite persistence for CareerPilot.

Stores a compact record of each agent run (goal, scores, adaptation events)
so a student could look back at previous sessions. Intentionally minimal —
most in-session state lives in Streamlit's session_state.
"""
from __future__ import annotations
import sqlite3
import json
import os
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "careerpilot.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            goal TEXT,
            target_role TEXT,
            github_username TEXT,
            overall_score INTEGER,
            adapted INTEGER,
            adaptation_reason TEXT,
            plan_json TEXT
        )
    """)
    return conn


def save_run(
    goal: str,
    target_role: str,
    github_username: str,
    overall_score: int,
    adapted: bool,
    adaptation_reason: str,
    plan: list,
) -> int:
    """Persist a run record. Returns the new row id. Never raises."""
    try:
        conn = _get_conn()
        cur = conn.execute(
            """INSERT INTO runs
               (created_at, goal, target_role, github_username, overall_score,
                adapted, adaptation_reason, plan_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.utcnow().isoformat(),
                goal,
                target_role,
                github_username,
                overall_score,
                1 if adapted else 0,
                adaptation_reason,
                json.dumps(plan, default=str),
            ),
        )
        conn.commit()
        row_id = cur.lastrowid
        conn.close()
        return row_id
    except Exception:
        return -1


def get_recent_runs(limit: int = 10) -> list:
    """Return recent run summaries, most recent first. Never raises."""
    try:
        conn = _get_conn()
        cur = conn.execute(
            """SELECT id, created_at, goal, target_role, github_username,
                      overall_score, adapted, adaptation_reason
               FROM runs ORDER BY id DESC LIMIT ?""",
            (limit,),
        )
        rows = cur.fetchall()
        conn.close()
        cols = ["id", "created_at", "goal", "target_role", "github_username",
                "overall_score", "adapted", "adaptation_reason"]
        return [dict(zip(cols, r)) for r in rows]
    except Exception:
        return []
