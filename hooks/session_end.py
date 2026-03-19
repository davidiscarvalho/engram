#!/usr/bin/env python3
"""
hooks/session_end.py
Claude Code SessionEnd hook — fires on exit, /clear, logout.
Auto-archives the active engram session.
"""
import sys
import json
import subprocess
from pathlib import Path


def main():
    try:
        json.loads(sys.stdin.read())
    except Exception:
        pass

    engram_cli   = Path.home() / ".claude" / "engram" / "engram"
    session_file = Path.home() / ".claude" / "engram" / ".current_session.json"

    if session_file.exists() and engram_cli.exists():
        try:
            subprocess.run(["python3", str(engram_cli), "session", "end"],
                           capture_output=True)
        except Exception:
            pass
    sys.exit(0)


if __name__ == "__main__":
    main()
