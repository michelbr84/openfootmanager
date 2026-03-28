#!/usr/bin/env bash
# Hook: Stop — Persist session state for next session
set -euo pipefail

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

ESTADO_FILE=".estado.md"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo ""
echo "[stop hook] Saving session state to $ESTADO_FILE..."

SUMMARY="${CLAUDE_STOP_HOOK_SUMMARY:-Session ended at $TIMESTAMP. No summary provided.}"

ENTRY="## Session: $TIMESTAMP

$SUMMARY

---
"

if [ -f "$ESTADO_FILE" ]; then
  EXISTING=$(cat "$ESTADO_FILE")
  printf '%s\n%s' "$ENTRY" "$EXISTING" > "$ESTADO_FILE"
else
  printf '# Session State Log\n\n%s' "$ENTRY" > "$ESTADO_FILE"
fi

echo -e "${GREEN}Session state saved to $ESTADO_FILE${NC}"

if git rev-parse --is-inside-work-tree &>/dev/null 2>&1; then
  git add "$ESTADO_FILE" 2>/dev/null || true
  echo -e "${YELLOW}Staged $ESTADO_FILE${NC}"
fi

echo ""
