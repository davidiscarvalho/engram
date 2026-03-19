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
import subprocess as _sp
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

        def _session_is_alive(session_data: dict) -> bool:
            pid = session_data.get("pid")
            if not pid:
                return False  # old format without PID → treat as stale
            try:
                os.kill(int(pid), 0)
                return True   # process alive
            except ProcessLookupError:
                return False  # process dead → stale
            except PermissionError:
                return True   # process alive, different owner (safe default)

        def _new_session():
            SESSION_PATH.write_text(json.dumps({
                "started_at": datetime.datetime.now().isoformat(),
                "project": cwd_project,
                "cwd": os.getcwd(),
                "pid": os.getpid()
            }, indent=2))

        if not SESSION_PATH.exists():
            _new_session()
        else:
            existing = json.loads(SESSION_PATH.read_text())
            if not _session_is_alive(existing):
                # Stale session (crash/kill) → end it, then start fresh
                engram_cli = Path.home() / ".claude" / "engram" / "engram"
                if engram_cli.exists():
                    _sp.run(["python3", str(engram_cli), "session", "end"],
                            capture_output=True)
                _new_session()
            # else: same process, session continues — do nothing

    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
