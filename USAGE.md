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
| **Session log** | Archive of a work session: what was built, decided, and what's next | auto (session end hook) |
| **Compact summary** | Knowledge preserved from a `/compact` operation | auto (PostCompact hook) |
| **Topic hub** | Hub page for a concept that appears across many notes | `engram add "Topic: ..."` |

---

## The memory-first protocol

After installing, `~/.claude/CLAUDE.md` contains a protocol telling Claude Code to search in this order:

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

- **Every prompt** — the `UserPromptSubmit` hook fires, injecting recent sessions and project notes into Claude's context. When the Claude session ID changes, the previous session is automatically archived and a new one starts.
- **Session end** — fires on exit or `/clear`; archives the session log automatically.

Session context appears as a system reminder in every conversation. Claude sees your recent sessions and project notes before each response.

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

### End of day

```bash
engram sync
```

`sync` pushes everything to your other machines. The next session — wherever you open Claude Code — will have the full picture.

### When you use /compact

Two hooks fire automatically:

**Before compaction** (`PreCompact`) — Claude sees a reminder injected into its context to save any pending notes before the context window shrinks.

**After compaction** (`PostCompact`) — the compaction summary is **automatically saved to engram** as a `compact` note. Find it with `engram session recent`.

---

## All commands

### Searching

```bash
engram search "query"           # all active notes
engram search -p . "query"      # current project + global
```

Notes from other machines show an `@machine` badge. If your query contains special characters (quotes, dashes), the search falls back to a simple LIKE match automatically.

Project scope (`-p .`) uses the git repository root name (not the subdirectory you're in). Running from `src/` inside `myproject/` still resolves to `myproject`.

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
engram session recent            # last 10 sessions + compact summaries
engram session recent --limit 5

# Manual control (usually not needed — hooks handle this automatically)
engram session start -p .
engram session end
engram session end --summary "..." --decisions "..." --files "..." --next-steps "..." --context "..."
```

### Sync

```bash
engram push                     # export → commit → push to GitHub
engram pull                     # pull from GitHub → merge/update notes
engram sync                     # pull then push (full bidirectional)
engram remote add <url>         # set the git remote
engram remote show              # show remote and machine name
```

`pull` uses upsert semantics: new notes are inserted, existing notes are updated if the remote version is newer (by `updated_at`).

**Recommended flow:**
```bash
# Start of day (on any machine)
engram pull

# End of day
engram sync
```

### Maintenance

```bash
engram archive <id>             # soft-delete (excluded from search)
engram unarchive <id>           # reverse a soft-delete
engram purge                    # hard-delete archived notes older than 90 days
engram purge --older-than 30    # hard-delete archived notes older than 30 days
engram export > backup.json     # full JSON export
engram import backup.json       # restore from export (duplicates skipped)
engram ingest <file>            # curation protocol for a document
engram rebuild-fts              # rebuild full-text search index (after corruption or migration)
engram doctor                   # health check: FTS consistency, UUIDs, sync status
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

## Debugging hooks

Hook activity is logged to `~/.claude/engram/hook.log`. If context isn't appearing or sessions aren't being saved:

```bash
tail -f ~/.claude/engram/hook.log
```

Each hook logs its activity with timestamps, so you can see exactly what's happening on each prompt.

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
engram unarchive <id>
engram purge [--older-than <days>]
engram export > backup.json
engram import backup.json
engram ingest <file>
engram rebuild-fts
engram doctor

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
