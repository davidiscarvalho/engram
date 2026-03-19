# engram

Persistent memory for Claude Code.

Claude Code forgets everything when a session ends. Every time you start fresh, you re-explain your project, your decisions, your gotchas — paying tokens to reconstruct context that already existed yesterday.

**engram** gives Claude Code a memory it can read from and write to across every session — and sync across machines via a private git repo. Named after the physical trace a memory leaves in the brain.

---

## What it does

- **Remembers your decisions** — architecture choices, bug fixes, patterns you've settled on
- **Auto-loads context on every prompt** — memory context injected into Claude before each response
- **Logs every session** — what you built, decided, and what to pick up next time
- **Searches in ~50 tokens** — SQLite full-text search, flat cost at any scale
- **Auto-saves compaction summaries** — `/compact` knowledge preserved automatically
- **Syncs across machines** — Mac, Linux, home server, wherever you work, via a private git repo

---

## Quick install

```bash
git clone https://github.com/davidiscarvalho/engram.git
cd engram
bash install.sh
source ~/.zshrc    # or ~/.bash_profile / ~/.config/fish/config.fish
engram stats
```

The installer detects your shell (zsh, bash, fish) automatically.

Full details → [INSTALL.md](./INSTALL.md)

---

## Sync setup

```bash
# On every machine you want to sync (use your own private repo)
engram remote add git@github.com:you/engram-memory.git

# Push from the first machine
engram push

# Pull on any other machine
engram pull

# Full bidirectional sync
engram sync
```

Full details → [INSTALL.md#sync-setup](./INSTALL.md#sync-setup)

---

## The daily loop

Sessions start and end **automatically** via hooks — no manual calls needed.

```bash
engram add -p . "Decision: ..." "tags" "content"   # save decisions as you go
engram add -p . "Fix: ..." "bug,fix" "content"      # after fixing something tricky
engram sync                                          # push to other machines
```

When you use `/compact`, the compaction summary is **automatically saved** as a searchable note. No action needed.

---

## Requirements

- macOS or Linux
- Python 3
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) — `npm i -g @anthropic-ai/claude-code`
- Git

For sync: a GitHub account with SSH key configured.

---

## Documentation

- **[INSTALL.md](./INSTALL.md)** — install, SSH key setup, sync configuration, troubleshooting
- **[USAGE.md](./USAGE.md)** — mental model, all commands, daily workflows

---

## Future development

### MCP server

The current architecture uses a `UserPromptSubmit` hook to push memory context into Claude on every prompt, plus shell commands (`engram search "..."`) for interactive queries. This works well but has one limitation: Claude has to run a subprocess to query memory, and the CLAUDE.md protocol has to remind it to do so.

A native MCP server would expose engram as a set of Claude tools (`engram:search`, `engram:add`, `engram:get`, `engram:session_recent`). Claude would call them directly as tool use — no subprocess, no shell parsing, no reminder needed in CLAUDE.md.

**The right architecture is both, not either/or:**

- **Hook stays** for guaranteed upfront context injection — recent sessions and project notes appear before every response whether Claude thinks to ask or not.
- **MCP server adds** interactive pull querying — Claude can chain multiple searches, follow up with `get`, and call `add` mid-task without constructing shell commands.

**Implementation sketch:**

```python
# engram_mcp.py — ~100 lines using the mcp Python SDK
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("engram")

@mcp.tool()
def search(query: str, project: str = None) -> str:
    """Search engram memory. Returns matching notes with summaries."""
    ...

@mcp.tool()
def add(title: str, tags: str, body: str, project: str = None) -> str:
    """Save a note to engram memory."""
    ...

@mcp.tool()
def get(id: int) -> str:
    """Fetch full content of a note by ID."""
    ...

@mcp.tool()
def session_recent() -> str:
    """Show recent session logs and compact summaries."""
    ...
```

Registered in `~/.claude/settings.json`:
```json
{
  "mcpServers": {
    "engram": {
      "command": "python3",
      "args": ["~/.claude/engram/engram_mcp.py"]
    }
  }
}
```

**Key trade-off:** the MCP server and CLI would share the same SQLite logic. The clean implementation extracts core DB functions into a shared module (`engram_core.py`) imported by both — otherwise any new command needs to be added in two places.

**When this makes sense:** the current hook + CLI approach already works correctly. MCP becomes worthwhile if engram grows to support richer multi-step memory workflows, or if the CLI shelling friction becomes noticeable in practice.

### Project identity via git remote

Currently `-p .` resolves to the git repository root folder name (e.g. `engram`). This can collide when two unrelated repos share the same folder name (`~/client-a/api` and `~/client-b/api` both become `api`).

The correct fix is to use the normalized git remote URL as the project identifier (`owner/repo`), which is stable across machines and unique across repos. This requires a one-time data migration to rewrite existing `project` field values — deferred until a migration command is implemented.

### Schema versioning

The current `get_db()` uses ad-hoc `ALTER TABLE` checks for each column. A `meta(key, value)` table tracking `schema_version` would make future migrations explicit and sequential rather than scattered inline checks.
