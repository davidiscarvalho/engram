#!/usr/bin/env python3
"""
hooks/engram_auto_note.py
Claude Code PostToolUse hook — auto-captures engram notes from git commits.

Fires after every Bash tool call. When the command contains 'git commit',
extracts the commit subject + changed files and adds an atomic engram note.
This is the primary automatic knowledge capture mechanism.
"""

import sys
import json
import subprocess
import datetime
import re
from pathlib import Path

LOG_PATH   = Path.home() / ".claude" / "engram" / "hook.log"
ENGRAM_CLI = Path.home() / ".claude" / "engram" / "engram"


def log(msg: str):
    try:
        with open(LOG_PATH, "a") as f:
            f.write(f"[{datetime.datetime.now().isoformat()}] [auto_note] {msg}\n")
    except Exception:
        pass


def run(cmd: list[str], cwd: str | None = None) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=10)
        return result.stdout.strip()
    except Exception:
        return ""


def detect_project(cwd: str) -> str:
    """Map a working directory to an engram project slug."""
    path = Path(cwd)
    # Walk up to find a git root that has a recognisable name
    for parent in [path] + list(path.parents):
        if (parent / ".git").exists():
            return parent.name
    return path.name


def is_commit_command(command: str) -> bool:
    """Return True if the bash command contains an actual git commit (not --amend of other people's work, not --no-commit, etc.)."""
    # Must contain 'git commit' or 'git' followed later by 'commit'
    if "git commit" not in command:
        return False
    # Exclude dry-run, no-commit, verify-only patterns
    if "--dry-run" in command or "--no-commit" in command:
        return False
    return True


def get_commit_info(cwd: str) -> dict | None:
    """Get last commit subject and stat from the working directory."""
    subject = run(["git", "log", "-1", "--format=%s"], cwd=cwd)
    if not subject:
        return None

    commit_hash = run(["git", "log", "-1", "--format=%h"], cwd=cwd)
    stat = run(["git", "diff", "HEAD~1", "--stat", "--no-color"], cwd=cwd)

    # Trim stat to first 10 lines to avoid huge notes
    stat_lines = stat.splitlines()
    if len(stat_lines) > 10:
        stat_lines = stat_lines[:10] + [f"  ... ({len(stat_lines) - 10} more lines)"]
    stat_trimmed = "\n".join(stat_lines)

    return {
        "subject": subject,
        "hash": commit_hash,
        "stat": stat_trimmed,
    }


def note_exists_for_commit(project: str, commit_hash: str) -> bool:
    """Check if we already have a note for this commit hash to avoid duplicates."""
    result = run([str(ENGRAM_CLI), "search", "-p", project, commit_hash])
    return bool(result and commit_hash in result)


def add_note(project: str, info: dict):
    subject = info["subject"]
    commit_hash = info["hash"]

    # Skip merge commits and trivial housekeeping
    if subject.startswith("Merge "):
        log(f"Skipping merge commit: {subject}")
        return

    title = f"Impl: {subject} ({commit_hash})"
    tags = "impl,auto,commit"
    body = f"Commit: {commit_hash}\nSubject: {subject}\n\nChanged files:\n{info['stat']}"

    result = run([
        str(ENGRAM_CLI), "add", "-p", project,
        title, tags, body,
    ])
    log(f"Added note for [{project}] {commit_hash}: {subject} → {result}")


def main():
    payload = {}
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw)
    except Exception as e:
        log(f"Failed to parse payload: {e}")
        sys.exit(0)

    # Only act on Bash tool calls
    if payload.get("tool_name") != "Bash":
        sys.exit(0)

    tool_input = payload.get("tool_input", {})
    command = tool_input.get("command", "")

    if not is_commit_command(command):
        sys.exit(0)

    # Check if the commit actually succeeded (tool_response should contain branch info)
    tool_response = payload.get("tool_response", "")
    if isinstance(tool_response, dict):
        tool_response = json.dumps(tool_response)
    # A failed commit won't have typical success output
    if "nothing to commit" in tool_response or "error:" in tool_response.lower():
        log("Commit appears to have failed or was empty — skipping note")
        sys.exit(0)

    if not ENGRAM_CLI.exists():
        log("engram CLI not found — skipping")
        sys.exit(0)

    # Determine working directory from tool_input or fall back to cwd
    cwd = tool_input.get("cwd") or str(Path.cwd())

    # Extract project name
    project = detect_project(cwd)
    log(f"Detected project: {project} from cwd: {cwd}")

    # Get commit info
    info = get_commit_info(cwd)
    if not info:
        log("Could not extract commit info")
        sys.exit(0)

    # Avoid duplicate notes
    if note_exists_for_commit(project, info["hash"]):
        log(f"Note already exists for {info['hash']} — skipping")
        sys.exit(0)

    add_note(project, info)
    sys.exit(0)


if __name__ == "__main__":
    main()
