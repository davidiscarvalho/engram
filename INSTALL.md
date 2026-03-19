# Installing engram

---

## Contents

- [Prerequisites](#prerequisites)
- [Install](#install)
- [What the installer does](#what-the-installer-does)
- [Sync setup](#sync-setup)
  - [Step 1 — Check your SSH key](#step-1--check-your-ssh-key)
  - [Step 2 — Create the private memory repo](#step-2--create-the-private-memory-repo)
  - [Step 3 — Configure the remote on each machine](#step-3--configure-the-remote-on-each-machine)
  - [Step 4 — First push](#step-4--first-push)
  - [Step 5 — Pull on your other machine](#step-5--pull-on-your-other-machine)
- [Multi-machine reference](#multi-machine-reference)
- [Troubleshooting](#troubleshooting)
- [Manual install](#manual-install)
- [Uninstalling](#uninstalling)

---

## Prerequisites

**1. macOS** — Apple Silicon or Intel. The installer uses macOS-specific paths and shell conventions.

**2. Python 3**
```bash
python3 --version
```
If not installed: `brew install python3`
Don't have Homebrew? Install it at [brew.sh](https://brew.sh).

**3. Claude Code**
```bash
npm i -g @anthropic-ai/claude-code
```
If you don't have Node: `brew install node`

**4. Git** — pre-installed on macOS. Verify with `git --version`.

---

## Install

```bash
git clone https://github.com/davidiscarvalho/engram.git
cd engram
bash install.sh
source ~/.zshrc
engram stats
```

You should see:

```
── engram stats ────────────────────
  Machine:          your-machine-name
  Notes (active):   0
  Session logs:     0
  ...
  Sync remote:      not configured
```

If you see that, the base install is working. Continue to [Sync setup](#sync-setup).

---

## What the installer does

`install.sh` is a short, readable script. Here's exactly what it does:

**1.** Creates `~/.claude/engram/` and `~/.claude/hooks/`

**2.** Copies the `engram` CLI to `~/.claude/engram/engram` and makes it executable

**3.** Initialises `memory.db` (the SQLite database)

**4.** Registers four Claude Code hooks in `~/.claude/settings.json` (backs it up first):
   - `UserPromptSubmit` — fires at session start; loads recent context, auto-starts a session with PID tracking
   - `PreCompact` — fires before `/compact`; injects a reminder into Claude's context to save decisions before compaction
   - `PostCompact` — fires after `/compact`; automatically saves the compaction summary to engram (no action needed)
   - `SessionEnd` — fires on exit or `/clear`; auto-closes the active session log

**5.** Adds `~/.claude/engram` to your PATH in `~/.zshrc`

**6.** Appends the memory-first protocol to `~/.claude/CLAUDE.md`

The installer is idempotent — running it twice won't break or duplicate anything.

---

## Sync setup

Sync lets your Mac and home server share the same memory via a private GitHub repo. Your Hetzner production server stays isolated — it never connects to this repo.

### Step 1 — Check your SSH key

SSH keys let your machine talk to GitHub without a password. Check if you already have one:

```bash
ssh -T git@github.com
```

**If you see:** `Hi davidiscarvalho! You've successfully authenticated` → you're good, skip to Step 2.

**If you see:** `Permission denied (publickey)` → you need to create and add a key:

```bash
# Generate a new SSH key (press Enter to accept all defaults)
ssh-keygen -t ed25519 -C "your@email.com"

# Copy the public key to your clipboard
cat ~/.ssh/id_ed25519.pub | pbcopy

# Now add it to GitHub:
# → github.com → Settings → SSH and GPG keys → New SSH key
# → Paste the key → Save
```

Then verify:
```bash
ssh -T git@github.com
# Should say: Hi davidiscarvalho! You've successfully authenticated
```

**On your home server (Linux):** Same steps, but use `xclip -sel clip < ~/.ssh/id_ed25519.pub` or just `cat ~/.ssh/id_ed25519.pub` and copy manually.

---

### Step 2 — Create the private memory repo

1. Go to [github.com/new](https://github.com/new)
2. Name it `engram-memory`
3. Set visibility to **Private**
4. Leave everything else unchecked (no README, no .gitignore)
5. Click **Create repository**

That's it. The repo should be empty.

---

### Step 3 — Configure the remote on each machine

Run this on **every machine** where you install engram (Mac, home server):

```bash
engram remote add git@github.com:davidiscarvalho/engram-memory.git
```

You'll see:
```
✓ Remote set: git@github.com:davidiscarvalho/engram-memory.git
  Machine name: your-machine-name

  Next: engram push
```

The machine name is auto-detected from your hostname. It's stamped on every note so you can see which machine created it. You can rename it in `~/.claude/engram/config.json` if you want something cleaner (e.g. `mac`, `homeserver`).

**Do not run this on Hetzner.** The production server stays isolated — no remote configured.

---

### Step 4 — First push

From your Mac (or whichever machine has notes):

```bash
engram push
```

On first push this clones the `engram-memory` repo locally, exports your notes to `memory.json`, commits, and pushes. Output:

```
── engram push ──────────────────────────────────────────
  Cloning git@github.com:davidiscarvalho/engram-memory.git...
  ✓ Cloned to /Users/david/.claude/engram/sync
  Pulling latest first...
  Exported 12 notes → memory.json
  ✓ Pushed: sync: mac @ 2026-03-18 14:30 (12 notes)
```

---

### Step 5 — Pull on your other machine

On your home server (after installing engram and configuring the remote):

```bash
engram pull
```

Output:
```
── engram pull ──────────────────────────────────────────
  Pulling from remote...
  ✓ Merged 12 new notes from remote.
```

Your home server now has a full copy of your memory. From here, both machines can push and pull independently.

---

## Multi-machine reference

| Command | What it does |
|---------|-------------|
| `engram push` | Export local DB → commit → push to GitHub |
| `engram pull` | Pull from GitHub → merge new notes into local DB |
| `engram sync` | Pull then push — full bidirectional sync |
| `engram remote show` | Show configured remote and machine name |

**Merge behaviour:** `pull` adds notes from the remote that don't exist locally, identified by UUID. It never deletes or overwrites existing notes. If the same note exists on both machines (same UUID), it's skipped. Last-write-wins doesn't apply — notes are append-only by design.

**When to sync:**
- After a long session: `engram sync` before closing
- Before starting on a different machine: `engram pull`
- As a habit: add `engram sync` to your end-of-session flow alongside `engram session end`

**Hetzner prod — no sync, ever.** The production server has its own isolated `memory.db`. Notes there are scoped to production projects only. If you ever want to bring a specific note across manually, use `engram export` + `engram import`.

---

## Troubleshooting

**`engram: command not found`**
```bash
source ~/.zshrc
```
If still missing, check `~/.zshrc` has: `export PATH="$HOME/.claude/engram:$PATH"`

**`python3: command not found`**
```bash
brew install python3
```

**`engram push` fails with "Permission denied (publickey)"**

Your SSH key isn't added to GitHub. Follow [Step 1](#step-1--check-your-ssh-key) above.

**`engram push` fails with "remote: Repository not found"**

The `engram-memory` repo doesn't exist or you're using the wrong URL. Check:
```bash
engram remote show
```
Then verify the repo exists at github.com/davidiscarvalho/engram-memory.

**`engram pull` says "No memory.json in remote yet"**

No machine has pushed yet. Run `engram push` from the machine with your notes first.

**Hooks don't seem to fire**

Check `~/.claude/settings.json` has the hook entries:
```bash
cat ~/.claude/settings.json
```
Re-run `bash install.sh` if the entries are missing.

**`settings.json` got corrupted**

```bash
cp ~/.claude/settings.json.bak ~/.claude/settings.json
bash install.sh
```

---

## Manual install

```bash
mkdir -p ~/.claude/engram ~/.claude/hooks
cp engram ~/.claude/engram/engram
chmod +x ~/.claude/engram/engram
cp hooks/session_start.py ~/.claude/hooks/engram_session_start.py
cp hooks/session_end.py   ~/.claude/hooks/engram_session_end.py
cp hooks/pre_compact.py   ~/.claude/hooks/engram_pre_compact.py
cp hooks/post_compact.py  ~/.claude/hooks/engram_post_compact.py
echo 'export PATH="$HOME/.claude/engram:$PATH"' >> ~/.zshrc
source ~/.zshrc
engram stats
```

Add hooks to `~/.claude/settings.json` (replace `/Users/YOU` with `echo $HOME`):
```json
{
  "hooks": {
    "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "python3 /Users/YOU/.claude/hooks/engram_session_start.py"}]}],
    "SessionEnd":       [{"hooks": [{"type": "command", "command": "python3 /Users/YOU/.claude/hooks/engram_session_end.py"}]}],
    "PreCompact":       [{"hooks": [{"type": "command", "command": "python3 /Users/YOU/.claude/hooks/engram_pre_compact.py"}]}],
    "PostCompact":      [{"hooks": [{"type": "command", "command": "python3 /Users/YOU/.claude/hooks/engram_post_compact.py"}]}]
  }
}
```

Copy `CLAUDE_MD_SNIPPET.md` contents into `~/.claude/CLAUDE.md`.

---

## Uninstalling

```bash
engram export > ~/engram_backup.json   # save your notes first
rm -rf ~/.claude/engram
rm ~/.claude/hooks/engram_session_start.py
rm ~/.claude/hooks/engram_session_end.py
rm ~/.claude/hooks/engram_pre_compact.py
rm ~/.claude/hooks/engram_post_compact.py
# Edit settings.json — remove the engram hook entries
# Edit ~/.zshrc — remove the engram PATH line
# Edit ~/.claude/CLAUDE.md — remove the engram section
```
