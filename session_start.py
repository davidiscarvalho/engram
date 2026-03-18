#!/usr/bin/env python3
"""
hooks/session_start.py
Claude Code UserPromptSubmit hook — fires at the start of every session.
Injects engram context: recent sessions + project notes.
"""

import sys
import os
import json
import sqlite3
import datetime
from pathlib import Path

DB_PATH      = Path.home() / ".claude" / "engram" / "memory.db"
SESSION_PATH = Path.home() / ".claude" / "engram" / ".current_session.json"

def main():
    try:
        json.loads(sys.stdin.read())
    except Exception:
        sys.exit(0)

    if not DB_PATH.exists():
        sys.exit(0)

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cwd_project = Path(os.getcwd()).name

        lines = ["── engram: Memory Context ───────────────────────────────"]

        recent = conn.execute(
            "SELECT id, project, title, summary FROM notes WHERE type='session' AND archived_at IS NULL ORDER BY id DESC LIMIT 3"
        ).fetchall()

        if recent:
            lines.append("Recent sessions:")
            for r in recent:
                proj = f"[{r['project']}] " if r['project'] else ""
                lines.append(f"  [{r['id']:04d}] {proj}{r['title']}")
                if r['summary']:
                    lines.append(f"         {r['summary'][:100]}")

        proj_notes = conn.execute(
            "SELECT id, title, tags FROM notes WHERE project=? AND type='note' AND archived_at IS NULL ORDER BY updated_at DESC LIMIT 5",
            [cwd_project]
        ).fetchall()

        if proj_notes:
            lines.append(f"\nProject notes [{cwd_project}]:")
            for r in proj_notes:
                lines.append(f"  [{r['id']:04d}] {r['title']}  #{r['tags']}")

        lines.append("\nReminder: search engram FIRST → engram search \"query\" before going external.")
        lines.append("─────────────────────────────────────────────────────")

        context_file = Path.home() / ".claude" / "engram" / ".session_context.txt"
        context_file.write_text("\n".join(lines))

        if not SESSION_PATH.exists():
            session = {
                "started_at": datetime.datetime.now().isoformat(),
                "project": cwd_project,
                "cwd": os.getcwd()
            }
            SESSION_PATH.write_text(json.dumps(session, indent=2))

    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
