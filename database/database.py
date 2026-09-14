"""
Lightweight, deployment-safe SQLite persistence for CareerPilot.

Streamlit Community Cloud's filesystem is ephemeral and, depending on the
deployment, may be read-only or reset between reboots/redeploys. This module
therefore treats persistence as a "best effort" convenience feature, never a
requirement:

- The DB file is written under the OS temp directory, not the repo directory,
  so it never conflicts with a read-only source checkout.
- Every public function catches all exceptions and degrades gracefully
  (returns -1 / [] instead of raising) so a storage failure never crashes
  the Streamlit app.
- Most in-session state still lives in st.session_state (see app.py); this
  module only adds a "recent runs" convenience view when storage is available.
"""
from __future__ import annotations
import sqlite3
import json
import os
import tempfile
from datetime import datetime, timezone

# Use the system temp dir so this works even if the app's source directory
# is mounted read-only (common on hosted platforms).
DB_PATH = os.path.join(tempfile.gettempdir(), "careerpilot_runs.db")


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


def is_storage_available() -> bool:
    """Best-effort check the UI can use to show a note when history is off."""
    try:
        conn = _get_conn()
        conn.close()
        return True
    except Exception:
        return False


def save_run(
    goal: str,
    target_role: str,
    github_username: str,
    overall_score: int,
    adapted: bool,
    adaptation_reason: str,
    plan: list,
) -> int:
    """
    Persist a run record. Returns the new row id, or -1 if storage is
    unavailable/failed for any reason. Never raises — this must not be able
    to crash the app on a read-only or ephemeral deployment filesystem.
    """
    try:
        conn = _get_conn()
        cur = conn.execute(
            """INSERT INTO runs
               (created_at, goal, target_role, github_username, overall_score,
                adapted, adaptation_reason, plan_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(),
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
    """Return recent run summaries, most recent first. Never raises — returns [] on any failure."""
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
