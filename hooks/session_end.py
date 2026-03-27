#!/usr/bin/env python3
"""
hooks/session_end.py
Claude Code SessionEnd hook — fires on exit, /clear, logout.
Auto-archives the active engram session.
"""
import sys
import json
import datetime
import subprocess
from pathlib import Path

LOG_PATH     = Path.home() / ".claude" / "engram" / "hook.log"
ENGRAM_CLI   = Path.home() / ".claude" / "engram" / "engram"
SESSION_FILE = Path.home() / ".claude" / "engram" / ".current_session.json"


def log(msg: str):
    try:
        with open(LOG_PATH, "a") as f:
            f.write(f"[{datetime.datetime.now().isoformat()}] [session_end] {msg}\n")
    except Exception:
        pass


def main():
    try:
        json.loads(sys.stdin.read())
    except Exception:
        pass

    if SESSION_FILE.exists() and ENGRAM_CLI.exists():
        try:
            subprocess.run(["python3", str(ENGRAM_CLI), "session", "end"],
                           capture_output=True)
            log("Session end triggered successfully")
        except Exception as e:
            log(f"Error ending session: {e}")

    if ENGRAM_CLI.exists():
        try:
            subprocess.run(["python3", str(ENGRAM_CLI), "sync"],
                           capture_output=True, timeout=15)
            log("Sync triggered on session end")
        except Exception as e:
            log(f"Sync error: {e}")
    sys.exit(0)


if __name__ == "__main__":
    main()
