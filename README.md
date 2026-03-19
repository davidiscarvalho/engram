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
