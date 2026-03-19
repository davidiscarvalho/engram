#!/usr/bin/env python3
"""
hooks/post_compact.py
Claude Code PostCompact hook — fires after /compact completes.
Automatically saves the compaction summary to engram so knowledge
from the compacted context is preserved across session boundaries.
"""

import sys
import json
import os
import sqlite3
import datetime
import uuid as _uuid
from pathlib import Path

ENGRAM_DIR   = Path.home() / ".claude" / "engram"
DB_PATH      = ENGRAM_DIR / "memory.db"
LOG_PATH     = ENGRAM_DIR / "hook.log"
SESSION_PATH = ENGRAM_DIR / ".current_session.json"


def log(msg: str):
    try:
        with open(LOG_PATH, "a") as f:
            f.write(f"[{datetime.datetime.now().isoformat()}] [post_compact] {msg}\n")
    except Exception:
        pass


def machine_name() -> str:
    try:
        cfg_path = ENGRAM_DIR / "config.json"
        if cfg_path.exists():
            return json.loads(cfg_path.read_text()).get("machine", os.uname().nodename)
    except Exception:
        pass
    return os.uname().nodename


def make_uuid() -> str:
    return _uuid.uuid4().hex[:16]


def make_summary(content: str, length: int = 180) -> str:
    text = " ".join(content.split())
    return text[:length] + ("…" if len(text) > length else "")


def get_project() -> str:
    if SESSION_PATH.exists():
        try:
            return json.loads(SESSION_PATH.read_text()).get("project") or Path(os.getcwd()).name
        except Exception:
            pass
    return Path(os.getcwd()).name


def main():
    payload = {}
    try:
        payload = json.loads(sys.stdin.read())
    except Exception:
        log("Failed to parse stdin payload")

    summary = payload.get("summary", "")
    if not summary or not DB_PATH.exists():
        sys.exit(0)

    try:
        project = get_project()
        now     = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        title   = f"Compact summary: {project} ({now[:10]})"
        content = f"## Context compaction — {now}\nProject: {project}\nMachine: {machine_name()}\n\n{summary}"
        tags    = f"compact,session,{project}"

        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            "INSERT INTO notes (uuid, type, project, title, tags, content, summary, machine) VALUES (?,?,?,?,?,?,?,?)",
            [make_uuid(), "compact", project, title, tags, content, make_summary(summary), machine_name()]
        )
        conn.commit()
        conn.close()
        log(f"Saved compact note for project '{project}'")
    except Exception as e:
        log(f"Error saving compact note: {e}")

    sys.exit(0)


if __name__ == "__main__":
    main()
