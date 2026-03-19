#!/usr/bin/env bash
# install.sh — engram installer for macOS
# Run from the directory containing this script:  bash install.sh
set -e

ENGRAM_DIR="$HOME/.claude/engram"
CLAUDE_DIR="$HOME/.claude"
HOOKS_DIR="$CLAUDE_DIR/hooks"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "── engram installer ─────────────────────────────────────────"
echo ""

echo "→ Creating directories..."
mkdir -p "$ENGRAM_DIR"
mkdir -p "$HOOKS_DIR"

echo "→ Installing engram CLI..."
cp "$SCRIPT_DIR/engram" "$ENGRAM_DIR/engram"
chmod +x "$ENGRAM_DIR/engram"

if ! command -v python3 &>/dev/null; then
    echo "✗ Python 3 not found. Install via: brew install python3"
    exit 1
fi
echo "  python3: $(python3 --version)"

echo "→ Initialising database..."
python3 "$ENGRAM_DIR/engram" stats 2>/dev/null || true

echo "→ Installing Claude Code hooks..."
cp "$SCRIPT_DIR/hooks/session_start.py" "$HOOKS_DIR/engram_session_start.py"
cp "$SCRIPT_DIR/hooks/session_end.py"   "$HOOKS_DIR/engram_session_end.py"
cp "$SCRIPT_DIR/hooks/pre_compact.py"   "$HOOKS_DIR/engram_pre_compact.py"
cp "$SCRIPT_DIR/hooks/post_compact.py"  "$HOOKS_DIR/engram_post_compact.py"
chmod +x "$HOOKS_DIR/engram_session_start.py"
chmod +x "$HOOKS_DIR/engram_session_end.py"
chmod +x "$HOOKS_DIR/engram_pre_compact.py"
chmod +x "$HOOKS_DIR/engram_post_compact.py"

SETTINGS_FILE="$CLAUDE_DIR/settings.json"
if [ ! -f "$SETTINGS_FILE" ]; then
    echo '{}' > "$SETTINGS_FILE"
fi

cp "$SETTINGS_FILE" "$SETTINGS_FILE.bak"
echo "  Settings backed up → $SETTINGS_FILE.bak"

python3 << 'PYEOF'
import json
from pathlib import Path

settings_path = Path.home() / ".claude" / "settings.json"
hooks_dir     = Path.home() / ".claude" / "hooks"

with open(settings_path) as f:
    settings = json.load(f)

hooks = settings.setdefault("hooks", {})

hooks.setdefault("UserPromptSubmit", [])
start_hook = {
    "hooks": [{
        "type": "command",
        "command": f"python3 {hooks_dir}/engram_session_start.py"
    }]
}
existing = [h.get("hooks", [{}])[0].get("command", "") for h in hooks["UserPromptSubmit"]]
if not any("engram_session_start" in c for c in existing):
    hooks["UserPromptSubmit"].append(start_hook)

hooks.setdefault("PreCompact", [])
compact_hook = {
    "hooks": [{
        "type": "command",
        "command": f"python3 {hooks_dir}/engram_pre_compact.py"
    }]
}
existing_compact = [h.get("hooks", [{}])[0].get("command", "") for h in hooks["PreCompact"]]
if not any("engram_pre_compact" in c for c in existing_compact):
    hooks["PreCompact"].append(compact_hook)

hooks.setdefault("SessionEnd", [])
end_hook = {"hooks": [{"type": "command",
                        "command": f"python3 {hooks_dir}/engram_session_end.py"}]}
existing_end = [h.get("hooks", [{}])[0].get("command", "") for h in hooks["SessionEnd"]]
if not any("engram_session_end" in c for c in existing_end):
    hooks["SessionEnd"].append(end_hook)

hooks.setdefault("PostCompact", [])
post_compact_hook = {
    "hooks": [{
        "type": "command",
        "command": f"python3 {hooks_dir}/engram_post_compact.py"
    }]
}
existing_post_compact = [h.get("hooks", [{}])[0].get("command", "") for h in hooks["PostCompact"]]
if not any("engram_post_compact" in c for c in existing_post_compact):
    hooks["PostCompact"].append(post_compact_hook)

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)

print("  Hooks registered in settings.json")
PYEOF

ZSHRC="$HOME/.zshrc"
if ! grep -qF "/.claude/engram" "$ZSHRC" 2>/dev/null; then
    echo "" >> "$ZSHRC"
    echo "# engram — persistent memory for Claude Code" >> "$ZSHRC"
    echo 'export PATH="$HOME/.claude/engram:$PATH"' >> "$ZSHRC"
    echo "→ Added engram to PATH in ~/.zshrc"
else
    echo "→ PATH already configured in ~/.zshrc"
fi

CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"
if [ ! -f "$CLAUDE_MD" ]; then
    touch "$CLAUDE_MD"
fi

if ! grep -q "engram" "$CLAUDE_MD" 2>/dev/null; then
    echo "" >> "$CLAUDE_MD"
    cat "$SCRIPT_DIR/CLAUDE_MD_SNIPPET.md" >> "$CLAUDE_MD"
    echo "→ engram protocol appended to CLAUDE.md"
else
    echo "→ CLAUDE.md already contains engram section (skipped)"
fi

echo ""
echo "── Verification ─────────────────────────────────────────────"
echo ""

if python3 "$ENGRAM_DIR/engram" stats 2>&1 | grep -q "DB path"; then
    echo "  ✓ engram CLI working"
else
    echo "  ✗ engram CLI failed — check $ENGRAM_DIR/engram"
fi

python3 -c "
import json; from pathlib import Path
s = json.load(open(Path.home() / '.claude' / 'settings.json'))
h = s.get('hooks', {})
assert any('engram_session_start' in str(x) for x in h.get('UserPromptSubmit', []))
assert any('engram_pre_compact'   in str(x) for x in h.get('PreCompact', []))
assert any('engram_session_end'   in str(x) for x in h.get('SessionEnd', []))
assert any('engram_post_compact'  in str(x) for x in h.get('PostCompact', []))
print('  ✓ Hooks registered in settings.json')
" 2>/dev/null || echo "  ✗ Hook registration failed"

echo ""
echo "── Done ─────────────────────────────────────────────────────"
echo ""
echo "  Reload your shell:      source ~/.zshrc"
echo "  Test it:                engram stats"
echo "  Add your first note:    engram add \"Hello\" \"test\" \"My first engram note\""
echo "  Start a session:        engram session start"
echo ""
