#!/usr/bin/env python3
"""
hooks/pre_compact.py
Claude Code PreCompact hook — fires when /compact is called.
Injects a reminder into Claude's context to save decisions to engram
before compaction erases early session knowledge.
"""

import sys
import json
from pathlib import Path


def main():
    try:
        json.loads(sys.stdin.read())
    except Exception:
        pass

    reminder = (
        "── engram: Save before compaction ──────────────────────────────────────\n"
        "Context is about to compact. Save any knowledge not yet in engram:\n\n"
        "  engram add -p . \"Decision: <topic>\" \"decision,<tag>\" \"<what and why>\"\n"
        "  engram add -p . \"Impl: <feature>\" \"impl,<tag>\" \"<what was built>\"\n"
        "  engram add -p . \"Fix: <bug>\" \"bug,fix\" \"<root cause and solution>\"\n\n"
        "Fill in the current session log if it has empty sections:\n"
        "  engram session recent   → get the session note ID\n"
        "  engram update <id> \"<full content>\"\n"
        "─────────────────────────────────────────────────────────────────────────"
    )

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreCompact",
            "additionalContext": reminder
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
