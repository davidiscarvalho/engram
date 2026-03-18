---
name: engram
description: >
  Persistent memory system for Claude Code. Use this skill whenever the user
  asks about their knowledge base, engram, saving decisions, session logging,
  or recalling past project context. Also triggers when the user says "remember
  this", "save this decision", "what do we know about X", "add to my memory",
  or starts a new work session. The engram CLI stores curated notes in SQLite
  with FTS5 for token-efficient retrieval (~50 tokens per search regardless of
  database size).
---

# engram — Persistent Memory for Claude Code

Personal knowledge base at `~/.claude/engram/` with token-efficient SQLite retrieval.

## Core Principle

**MEMORY FIRST, EVERYTHING ELSE SECOND.**

Before answering any question about project history, past decisions, known bugs,
or architecture patterns — search engram. It costs ~50 tokens and may save the
user from re-explaining everything.

## DB Schema (for reference)

```
notes(
  id, type,       -- 'note' | 'session' | 'topic'
  project,        -- NULL = global, else project name
  title, tags,    -- tags = comma-separated
  content,        -- full text
  summary,        -- first ~180 chars, auto-generated
  created_at, updated_at, archived_at  -- archived = soft-deleted
)
+ FTS5 virtual table for full-text search (flat cost, scales infinitely)
```

## Quick Reference

```bash
# Search (cheap — always try first)
engram search "query"              # all active notes
engram search -p . "query"         # current project + global
engram session recent              # last 10 session logs
engram topics                      # topic hub notes
engram list -p .                   # all notes for this project

# Fetch
engram get <id>                    # full note content

# Add
engram add "Title" "tag1,tag2" "content"         # global note
engram add -p . "Title" "tags" "content"         # project note

# Session tracking
engram session start               # begin logging (auto-shows recent sessions)
engram session end                 # archive structured session log

# Housekeeping
engram tags                        # all tags + counts
engram stats                       # db stats + path
engram archive <id>                # soft-delete (excluded from search)
engram export > backup.json        # full backup
engram ingest <file>               # curation protocol for a document
```

## Note Types

| Type | Purpose | Created by |
|------|---------|-----------|
| `note` | Atomic knowledge: bugs, decisions, patterns, gotchas | `engram add` |
| `session` | Session archive: what was done, decisions, next steps | `engram session end` |
| `topic` | Hub page for recurring concept (3+ references) | Suggested by Claude |

## Session Workflow

**Start of session:**
```bash
engram session start -p .     # starts tracking, shows recent sessions
```

**During session** (save decisions as they happen):
```bash
engram add -p . "Decision: Use Redis for rate limiting" "decision,redis,architecture" \
  "Chose Redis over in-memory because sessions span multiple workers. TTL=60s."
```

**End of session:**
```bash
engram session end
engram get <new_id>    # fill in the session log template
```

**When context window fills (PreCompact hook fires):**
- Save in-progress decisions immediately
- Then `engram session end` + `engram session start` for fresh context

## Topic Notes

When a concept appears in 3+ notes, suggest a topic hub:

```bash
engram add "Topic: Docker" "topic-note,docker,devops" \
  "Hub for Docker knowledge.\n\nKey patterns: [engram search docker]\nGotchas: [engram search docker,gotcha]"
```

## Ingest Workflow

```bash
engram ingest /path/to/doc.md
```

Follow the printed curation protocol:
1. Read the document
2. Extract 5–15 non-obvious, high-value insights
3. `engram add` each as an atomic note

**Quality bar:**
- ✓ Actionable — tells you WHAT TO DO
- ✓ Contextual — explains WHEN this applies
- ✓ Non-obvious — captures what docs don't make clear
- ✗ Skip anything easily found in official docs

## Token Cost

| Operation | Approx tokens |
|-----------|--------------|
| `engram search "query"` — 10 results | ~80 tokens |
| `engram list -p .` — 15 notes | ~120 tokens |
| `engram get <id>` — full note | varies |
| `engram session recent` — 10 sessions | ~200 tokens |

Search cost stays flat at any DB size because FTS5 returns only matches.
