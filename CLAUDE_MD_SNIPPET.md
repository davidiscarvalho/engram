# ─── engram: Persistent Memory ───────────────────────────────────────────────
#
# Add this block to your ~/.claude/CLAUDE.md
# ─────────────────────────────────────────────────────────────────────────────

## Persistent Memory (engram)

I maintain a personal knowledge base at `~/.claude/engram/` using the `engram` CLI.
It stores curated notes, past decisions, project context, and session logs.
**Always search engram BEFORE going to external docs, web search, or training knowledge.**

### Memory-First Search Protocol

When starting work on anything, follow this 5-step order:

1. **Topics** → `engram topics` (check hub notes for recurring concepts)
2. **Project notes** → `engram list -p .` (what's known about this project)
3. **Keyword search** → `engram search "relevant terms"` (cross-project knowledge)
4. **Session history** → `engram session recent` (what was decided recently)
5. **THEN** go to docs / web / training knowledge

Never skip straight to step 5.

### Search Commands (cheap — ~50 tokens each)

```bash
engram search "query"           # search all active notes
engram search -p . "query"      # search current project + global notes
engram list -p .                # list all notes for current project
engram topics                   # view topic hub notes
engram session recent           # see last 10 sessions
engram get <id>                 # fetch full note (only when needed)
```

### When to Search

| Situation | Action |
|-----------|--------|
| "Why did we do X?" | `engram search "X"` first |
| "What's our pattern for X?" | `engram search "X"` first |
| Starting work on a project | `engram list -p .` |
| Auth / infra / deployment questions | `engram search "auth"` etc. |
| Any unfamiliar error or bug | `engram search "error message keywords"` |

### Adding Knowledge

```bash
# Global note (reusable across projects)
engram add "Insight: <topic>" "tag1,tag2" "<atomic content>"

# Project-scoped note
engram add -p . "Fix: <bug description>" "bug,fix" "<what the problem was and solution>"

# Decision note
engram add -p . "Decision: <topic>" "decision,architecture" "<what was decided and why>"
```

### Session Logging

At the start of each work session:
```bash
engram session start -p .
```

At the end (or before context compacts):
```bash
engram session end
```

Then fill in the session log: `engram get <new_id>`

### Topic Notes

If a concept appears in 3+ notes, suggest a topic hub:
```bash
engram add "Topic: <ConceptName>" "topic-note,<tag>" "Hub for <ConceptName>.\n\nRelated: [engram search <concept>]"
```

View all topics: `engram topics`

### Ingest a Document

```bash
engram ingest /path/to/doc.md
```

Follow the printed protocol to distil a document into 5–15 atomic notes.

### Database Info

- Location: `~/.claude/engram/memory.db`
- Archived notes excluded from search (still stored, never deleted)
- Export: `engram export > backup.json`
- Stats: `engram stats`
