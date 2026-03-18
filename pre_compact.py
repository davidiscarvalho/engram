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

Context window is filling up. Before compaction erases early context:

1. Save any key decisions made so far:
   engram add -p . "Decision: <topic>" "decision,<tags>" "<what was decided and why>"

2. Save any important discoveries:
   engram add -p . "Insight: <topic>" "insight,<tags>" "<what you learned>"

3. Log session progress if needed:
   engram session end   (then: engram session start for a fresh session)

──────────────────────────────────────────────────────────────────────────
"""

    reminder_file = Path.home() / ".claude" / "engram" / ".compaction_reminder.txt"
    reminder_file.write_text(reminder)
    sys.exit(0)


if __name__ == "__main__":
    main()
