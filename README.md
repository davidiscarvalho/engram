# engram

Persistent memory for Claude Code.

Claude Code forgets everything when a session ends. Every time you start fresh, you re-explain your project, your decisions, your gotchas — paying tokens to reconstruct context that already existed yesterday.

**engram** gives Claude Code a memory it can read from and write to across every session — and sync across multiple machines via a private git repo. Named after the physical trace a memory leaves in the brain.

---

## What it does

- **Remembers your decisions** — architecture choices, bug fixes, patterns you've settled on
- **Logs every session** — what you built, what you decided, what to pick up next time
- **Searches in ~50 tokens** — SQLite full-text search, flat cost at any scale
- **Hooks into Claude Code** — auto-loads context at the start of every session
- **Syncs across machines** — Mac, home server, wherever you work, via a private git repo
- **Stays isolated on prod** — your Hetzner server gets its own local memory, never connected to the shared repo

---

## Quick install

```bash
git clone https://github.com/davidiscarvalho/engram.git
cd engram
bash install.sh
source ~/.zshrc
engram stats
```

Full details → [INSTALL.md](./INSTALL.md)

---

## Sync setup (after installing on each machine)

```bash
# On every machine you want to sync
engram remote add git@github.com:davidiscarvalho/engram-memory.git

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

```bash
engram session start -p .       # orient Claude with recent context
engram add -p . "Decision: ..." "tags" "content"   # save as you go
engram session end               # archive the session
engram sync                      # push to other machines
```

---

## Requirements

- macOS (Apple Silicon or Intel) — Linux support coming
- Python 3 — pre-installed on macOS, or `brew install python3`
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) — `npm i -g @anthropic-ai/claude-code`
- Git — pre-installed on macOS

For sync: a GitHub account with SSH key configured.

---

## Documentation

- **[INSTALL.md](./INSTALL.md)** — install, SSH key setup, sync configuration, troubleshooting
- **[USAGE.md](./USAGE.md)** — mental model, all commands, daily workflows
