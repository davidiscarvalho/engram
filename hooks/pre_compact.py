#!/usr/bin/env python3
"""
hooks/pre_compact.py
Claude Code PreCompact hook — fires when context window is nearly full.
Reminds Claude to save important decisions to engram before context compresses.
"""

import sys
import json
from pathlib import Path

def main():
    try:
        json.loads(sys.stdin.read())
    except Exception:
        pass

    reminder = """
── engram: Context Compaction Warning ────────────────────────────────────

Context window is filling up. Save knowledge NOW — before compaction:

1. Key decisions (most important):
   engram add -p . "Decision: <topic>" "decision,<tags>" "<what was decided and why>"

2. Important discoveries:
   engram add -p . "Insight: <topic>" "insight,<tags>" "<what you learned>"

3. Completed work summary:
   engram add -p . "Impl: <feature>" "impl,<tags>" "<what was built, key choices>"

4. Fill in the current session log if it has empty sections:
   engram session recent   → get the session note ID
   engram update <id> "<full content replacing the [Claude: fill in...] placeholders>"

──────────────────────────────────────────────────────────────────────────
"""

    reminder_file = Path.home() / ".claude" / "engram" / ".compaction_reminder.txt"
    reminder_file.write_text(reminder)
    sys.exit(0)


if __name__ == "__main__":
    main()
