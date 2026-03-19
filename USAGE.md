# Using engram

Mental model, daily workflow, and complete command reference.

---

## The mental model

engram is the persistent memory that Claude Code reads **before** it does anything else.

When you work on a project, you accumulate knowledge that doesn't exist anywhere else: why you made a certain decision, the exact fix for a confusing bug, the pattern you've settled on. This knowledge lives in your head — and disappears from Claude Code when the session ends.

engram captures it in a SQLite database. Because it uses full-text search, retrieving it costs ~50 tokens whether you have 10 notes or 10,000. It syncs across machines via a private git repo, so the same memory is available wherever you work.

Three types of things live in memory:

| Type | What it is | Created by |
|------|-----------|-----------|
| **Note** | Atomic knowledge: a decision, a fix, a pattern, a gotcha | `engram add` |
| **Session log** | Archive of a work session: what was built, decided, and what's next | `engram session end` |
| **Topic hub** | Hub page for a concept that appears across many notes | Claude suggests at 3+ occurrences |

---

## The memory-first protocol

After installing, `~/.claude/CLAUDE.md` contains a protocol telling Claude Code to follow this search order:

1. `engram topics` — check hub notes for recurring concepts
2. `engram list -p .` — check what's known about this project
3. `engram search "query"` — keyword search across all notes
4. `engram session recent` — what was decided recently
5. **Then** go to docs, web search, or training knowledge

Never skip straight to step 5.

---

## The daily workflow

### Sessions are automatic

Sessions start and end via hooks — no manual calls needed:

- **Session start** — fires on your first prompt; loads recent context and starts a session log with PID tracking
- **Session end** — fires on exit or `/clear`; archives the session log automatically

If you want to view what sessions are running or check context: `engram session recent`

### During the session — save as you go

**This is the most important habit.** Don't wait until the end — save notes when decisions happen:

```bash
# Bug fix
engram add -p . "Fix: Clerk redirect silent 400" "clerk,auth,bug" \
  "afterSignInUrl must be allowlisted in Clerk dashboard. Silent 400, no error in logs."

# Architecture decision
engram add -p . "Decision: Redis for rate limiting" "decision,redis,architecture" \
  "Chose Redis over in-memory because sessions span multiple FastAPI workers. TTL=60s. Key: ratelimit:{user_id}."

# Cross-project insight (no -p flag = global)
engram add "Docker: healthcheck with depends_on" "docker,devops,gotcha" \
  "Use 'condition: service_healthy' not just depends_on. Without it, containers start before DB is ready."
```

Session logs have `[Claude: fill in...]` placeholders. If Claude didn't fill them in during the session, use `update`:

```bash
engram session recent            # find the session note ID
engram update <id> "<content>"   # replace the placeholder content
```

### End of day

```bash
engram sync
```

`sync` pushes everything to your other machines. The next session — wherever you open Claude Code — will have the full picture.

### When you use /compact

Two hooks fire automatically:

**Before compaction** (`PreCompact`) — Claude sees a reminder injected into its context:
```
── engram: Save before compaction ──────────────────────────────────────
Context is about to compact. Save any knowledge not yet in engram: ...
```

**After compaction** (`PostCompact`) — the compaction summary is **automatically saved to engram** as a session note. No action needed. Find it with `engram session recent`.

---

## All commands

### Searching

```bash
engram search "query"           # all active notes
engram search -p . "query"      # current project + global
```

Notes from other machines show an `@machine` badge so you know where they came from. Supports multiple terms (`engram search "auth redirect"`), prefix matching (`engram search "dock"`), and column targeting (`engram search "title:clerk"`).

### Reading

```bash
engram get <id>                 # full note
engram list                     # recent notes
engram list -p .                # project notes
engram list --limit 30          # more results
engram tags                     # all tags with counts
engram topics                   # topic hub notes
engram stats                    # db info, sync remote, machine name
```

### Adding notes

```bash
engram add "Title" "tag1,tag2" "content"          # global
engram add -p . "Title" "tag1,tag2" "content"     # project-scoped
```

**Title conventions:**
- `Fix: <description>` — bug fixes
- `Decision: <topic>` — architecture choices
- `Gotcha: <context>` — non-obvious traps
- `Insight: <topic>` — things you learned
- `Pattern: <context>` — recurring approaches
- `Topic: <Name>` — topic hub notes

**What makes a good note:** actionable, contextual, non-obvious, concise. One insight per note.

**What doesn't belong:** things easily found in official docs, one-off facts, copy-pasted documentation.

### Updating notes

```bash
engram update <id> "<new content>"   # replace a note's content
```

Useful for filling in session logs after the fact:
```bash
engram session recent
engram update 14 "## Session: ...\n\n### What Was Done\n..."
```

### Session management

```bash
engram session recent            # last 10 sessions (all machines)
engram session recent --limit 5

# Manual control (usually not needed — hooks handle this automatically)
engram session start -p .       # start session manually
engram session end               # end session manually
engram session end --summary "..." --decisions "..." --files "..." --next-steps "..." --context "..."
```

### Sync

```bash
engram push                     # export → commit → push to GitHub
engram pull                     # pull from GitHub → merge new notes
engram sync                     # pull then push (full bidirectional)
engram remote add <url>         # set the git remote
engram remote show              # show remote and machine name
```

**Recommended flow:**
```bash
# Start of day (on any machine)
engram pull

# End of day
engram sync
```

Session start/end are handled automatically by hooks.

### Maintenance

```bash
engram archive <id>             # soft-delete (excluded from search, never deleted)
engram export > backup.json     # full JSON export
engram import backup.json       # restore from export
engram ingest <file>            # curation protocol for a document
```

---

## Topic notes

When a concept appears across three or more notes, create a topic hub:

```bash
engram add "Topic: Clerk Authentication" "topic-note,clerk,auth" \
  "Hub for everything Clerk-related.

Key gotchas:
- Redirect URLs must be allowlisted (note 0003)
- Token refresh is silent after 7d inactivity (note 0007)

Search: engram search -p . clerk"
```

View all hubs: `engram topics`

---

## Document ingestion

```bash
engram ingest /path/to/doc.md
```

Prints a curation protocol — Claude Code reads the document and adds 5–15 distilled notes. Best for design docs, long READMEs, architecture documents.

---

## Complete command reference

```bash
engram search "query"
engram search -p . "query"
engram get <id>
engram add "Title" "tags" "content"
engram add -p . "Title" "tags" "content"
engram update <id> "<new content>"
engram list
engram list -p .
engram list --limit <n>
engram tags
engram topics
engram stats
engram archive <id>
engram export > backup.json
engram import backup.json
engram ingest <file>

engram session start
engram session start -p .
engram session end
engram session end --summary "..." --decisions "..." --files "..." --next-steps "..." --context "..."
engram session recent
engram session recent --limit <n>

engram remote add <url>
engram remote show
engram push
engram pull
engram sync
```
