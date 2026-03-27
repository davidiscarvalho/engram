#!/usr/bin/env python3
"""
hooks/session_start.py
Claude Code UserPromptSubmit hook — fires on every user prompt.
Injects engram context: recent sessions + project notes.
Uses session_id from payload to detect real Claude session boundaries.
"""

import sys
import os
import json
import sqlite3
import datetime
import subprocess as _sp
from pathlib import Path

DB_PATH      = Path.home() / ".claude" / "engram" / "memory.db"
LOG_PATH     = Path.home() / ".claude" / "engram" / "hook.log"
SESSION_PATH = Path.home() / ".claude" / "engram" / ".current_session.json"


def log(msg: str):
    try:
        with open(LOG_PATH, "a") as f:
            f.write(f"[{datetime.datetime.now().isoformat()}] [session_start] {msg}\n")
    except Exception:
        pass


def main():
    payload = {}
    try:
        payload = json.loads(sys.stdin.read())
    except Exception:
        log("Failed to parse stdin payload")

    if not DB_PATH.exists():
        sys.exit(0)

    current_session_id = payload.get("session_id", "")

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row

        try:
            result = _sp.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True, text=True, cwd=os.getcwd()
            )
            cwd_project = Path(result.stdout.strip()).name if result.returncode == 0 else Path(os.getcwd()).name
        except Exception:
            cwd_project = Path(os.getcwd()).name

        # ── Session identity: use session_id, not PID ─────────────────────
        def _end_previous_session():
            engram_cli = Path.home() / ".claude" / "engram" / "engram"
            if engram_cli.exists():
                _sp.run(["python3", str(engram_cli), "session", "end"],
                        capture_output=True)

        def _new_session(sid: str):
            SESSION_PATH.write_text(json.dumps({
                "started_at": datetime.datetime.now().isoformat(),
                "project": cwd_project,
                "cwd": os.getcwd(),
                "session_id": sid,
            }, indent=2))

        if not SESSION_PATH.exists():
            _new_session(current_session_id)
            log(f"New session started: project={cwd_project}")
        else:
            existing = json.loads(SESSION_PATH.read_text())
            stored_sid = existing.get("session_id", "")
            if stored_sid and stored_sid == current_session_id:
                pass  # same Claude session — just output context below
            else:
                log(f"Session boundary detected (id changed), ending previous session")
                _end_previous_session()
                _new_session(current_session_id)

        # ── Build context ─────────────────────────────────────────────────
        lines = ["── engram: Memory Context ───────────────────────────────"]

        recent = conn.execute(
            "SELECT id, project, title, summary FROM notes "
            "WHERE (type IN ('session', 'compact') "
            "       OR (type='note' AND tags LIKE '%session%')) "
            "AND archived_at IS NULL "
            "ORDER BY id DESC LIMIT 3"
        ).fetchall()

        if recent:
            lines.append("Recent sessions:")
            for r in recent:
                proj = f"[{r['project']}] " if r['project'] else ""
                lines.append(f"  [{r['id']:04d}] {proj}{r['title']}")
                if r['summary']:
                    lines.append(f"         {r['summary'][:100]}")

        proj_notes = conn.execute(
            "SELECT id, title, tags FROM notes "
            "WHERE project=? AND type='note' AND archived_at IS NULL "
            "AND tags NOT LIKE '%auto%' "
            "ORDER BY updated_at DESC LIMIT 5",
            [cwd_project]
        ).fetchall()

        if proj_notes:
            lines.append(f"\nProject notes [{cwd_project}]:")
            for r in proj_notes:
                lines.append(f"  [{r['id']:04d}] {r['title']}  #{r['tags']}")

        lines.append("\nReminder: search engram FIRST → engram search \"query\" before going external.")
        lines.append("─────────────────────────────────────────────────────")

        context = "\n".join(lines)

        # ── Output context to Claude ──────────────────────────────────────
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": context
            }
        }))
        log(f"Context injected: project={cwd_project}, {len(recent)} sessions, {len(proj_notes)} notes")

    except Exception as e:
        log(f"Error: {e}")

    sys.exit(0)


if __name__ == "__main__":
    main()
