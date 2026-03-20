#!/usr/bin/env python3
"""
hooks/engram_auto_note.py
Claude Code PostToolUse hook — automatic knowledge capture.

Triggers (in order of signal value):
  1. Bash: git commit      → note with subject + diff stat
  2. Bash: db migration    → note with migration file name
  3. Bash: deploy/stack    → note with command summary
  4. Write: new route/schema/config files → note with file path + purpose line
"""

import sys
import json
import subprocess
import datetime
import re
from pathlib import Path

LOG_PATH   = Path.home() / ".claude" / "engram" / "hook.log"
ENGRAM_CLI = Path.home() / ".claude" / "engram" / "engram"

# Write tool: only capture new files whose paths match these patterns
SIGNIFICANT_WRITE_PATTERNS = [
    r"/schema\.ts$",
    r"/route\.ts$",
    r"/middleware\.ts$",
    r"/features\.ts$",
    r"/helpers\.ts$",
    r"/migrations/.*\.sql$",
    r"/docker-compose.*\.yml$",
    r"/nginx/.*\.conf$",
]

# Bash: patterns that indicate a deploy/stack event worth logging
DEPLOY_PATTERNS = [
    r"cockpit\.sh\s+(up|rebuild|restart)",
    r"docker\s+compose\s+(up|restart)",
    r"pnpm\s+(build|start)",
    r"npm\s+run\s+(build|start)",
]


# ─── Utilities ────────────────────────────────────────────────────────────────

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


def add_note(project: str, title: str, tags: str, body: str):
    if not ENGRAM_CLI.exists():
        log("engram CLI not found")
        return
    result = run([str(ENGRAM_CLI), "add", "-p", project, title, tags, body])
    log(f"[{project}] {title} → {result}")


def note_exists(project: str, fingerprint: str) -> bool:
    """Search for an existing note containing a unique fingerprint string."""
    result = run([str(ENGRAM_CLI), "search", "-p", project, fingerprint])
    return bool(result and fingerprint in result)


def detect_project(cwd: str) -> str:
    path = Path(cwd)
    for parent in [path] + list(path.parents):
        if (parent / ".git").exists():
            return parent.name
    return path.name


def response_str(tool_response) -> str:
    if isinstance(tool_response, dict):
        return json.dumps(tool_response)
    return str(tool_response or "")


# ─── Handler 1: git commit ─────────────────────────────────────────────────────

def handle_git_commit(command: str, tool_response: str, cwd: str):
    if "git commit" not in command:
        return False
    if "--dry-run" in command or "--no-commit" in command:
        return False
    if "nothing to commit" in tool_response or "error:" in tool_response.lower():
        log("Commit failed or empty — skipping")
        return True  # matched but skip

    project = detect_project(cwd)

    subject = run(["git", "log", "-1", "--format=%s"], cwd=cwd)
    commit_hash = run(["git", "log", "-1", "--format=%h"], cwd=cwd)
    if not subject or not commit_hash:
        return True

    if subject.startswith("Merge "):
        log(f"Skipping merge commit: {subject}")
        return True

    if note_exists(project, commit_hash):
        log(f"Note already exists for {commit_hash} — skipping")
        return True

    stat = run(["git", "diff", "HEAD~1", "--stat", "--no-color"], cwd=cwd)
    stat_lines = stat.splitlines()
    if len(stat_lines) > 10:
        stat_lines = stat_lines[:10] + [f"  ... ({len(stat_lines) - 10} more lines)"]

    title = f"Impl: {subject} ({commit_hash})"
    body = f"Commit: {commit_hash}\nSubject: {subject}\n\nChanged files:\n" + "\n".join(stat_lines)
    add_note(project, title, "impl,auto,commit", body)
    return True


# ─── Handler 2: DB migration ───────────────────────────────────────────────────

def handle_db_migration(command: str, tool_response: str, cwd: str):
    migration_cmds = ["db:migrate", "drizzle-kit migrate", "drizzle-kit push"]
    if not any(p in command for p in migration_cmds):
        return False

    # Only log successful runs
    if "error" in tool_response.lower() or "failed" in tool_response.lower():
        return True

    project = detect_project(cwd)

    # Extract migration filename from output if present
    migration_file = ""
    for line in tool_response.splitlines():
        if ".sql" in line:
            match = re.search(r"[\w\-]+\.sql", line)
            if match:
                migration_file = match.group(0)
                break

    fingerprint = migration_file or command[:60]
    if note_exists(project, fingerprint):
        log(f"Migration note already exists for {fingerprint} — skipping")
        return True

    label = f"Migration applied: {migration_file}" if migration_file else "DB migration applied"
    title = f"DB: {label}"
    body = f"Command: {command.strip()}\nMigration file: {migration_file or '(unknown)'}\nOutput:\n{tool_response[:400]}"
    add_note(project, title, "db,migration,auto", body)
    return True


# ─── Handler 3: deploy / stack events ─────────────────────────────────────────

def handle_deploy(command: str, tool_response: str, cwd: str):
    matched = None
    for pattern in DEPLOY_PATTERNS:
        m = re.search(pattern, command)
        if m:
            matched = m.group(0)
            break
    if not matched:
        return False

    # Skip if failed
    if "error" in tool_response.lower() and "0 error" not in tool_response.lower():
        return True

    project = detect_project(cwd)
    fingerprint = re.sub(r"\s+", " ", command.strip())[:80]

    if note_exists(project, fingerprint[:30]):
        log(f"Deploy note already exists — skipping")
        return True

    title = f"Deploy: {matched}"
    body = f"Command: {command.strip()[:200]}\nOutput:\n{tool_response[:300]}"
    add_note(project, title, "deploy,auto", body)
    return True


# ─── Handler 4: Write tool — new significant files ────────────────────────────

def handle_write(file_path: str, content: str, tool_response: str, cwd: str):
    # Only fire on new file creation
    if "created" not in tool_response.lower():
        return False

    # Filter to significant path patterns
    matched_pattern = None
    for pattern in SIGNIFICANT_WRITE_PATTERNS:
        if re.search(pattern, file_path):
            matched_pattern = pattern
            break
    if not matched_pattern:
        return False

    project = detect_project(cwd or file_path)

    # Avoid duplicate notes for the same file
    short_path = file_path.replace(str(Path.home()), "~")
    if note_exists(project, short_path):
        log(f"Write note already exists for {short_path} — skipping")
        return False

    # Extract first meaningful comment or export line as purpose hint
    purpose = ""
    for line in content.splitlines()[:15]:
        line = line.strip()
        if line.startswith("//") or line.startswith("#") or line.startswith("*"):
            text = re.sub(r"^[/#\*\s]+", "", line).strip()
            if len(text) > 10:
                purpose = text
                break
        if line.startswith("export") and len(line) > 15:
            purpose = line[:100]
            break

    # Categorise
    if "/migrations/" in file_path:
        tag_extra = "db,migration"
        category = "Migration"
    elif "/api/" in file_path:
        tag_extra = "api,route"
        category = "Route"
    elif "schema" in file_path:
        tag_extra = "db,schema"
        category = "Schema"
    elif "docker-compose" in file_path or ".conf" in file_path:
        tag_extra = "infra"
        category = "Config"
    else:
        tag_extra = "code"
        category = "File"

    title = f"New {category}: {short_path}"
    body = f"Path: {short_path}\nPurpose: {purpose or '(see file)'}\nPattern matched: {matched_pattern}"
    add_note(project, title, f"auto,write,{tag_extra}", body)
    return True


# ─── Dispatch ─────────────────────────────────────────────────────────────────

def main():
    payload = {}
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw)
    except Exception as e:
        log(f"Failed to parse payload: {e}")
        sys.exit(0)

    if not ENGRAM_CLI.exists():
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    tool_response = response_str(payload.get("tool_response", ""))

    if tool_name == "Bash":
        command = tool_input.get("command", "")
        cwd = tool_input.get("cwd") or str(Path.cwd())

        if handle_git_commit(command, tool_response, cwd):
            sys.exit(0)
        if handle_db_migration(command, tool_response, cwd):
            sys.exit(0)
        if handle_deploy(command, tool_response, cwd):
            sys.exit(0)

    elif tool_name == "Write":
        file_path = tool_input.get("file_path", "")
        content = tool_input.get("content", "")
        cwd = str(Path(file_path).parent) if file_path else str(Path.cwd())
        handle_write(file_path, content, tool_response, cwd)

    sys.exit(0)


if __name__ == "__main__":
    main()
