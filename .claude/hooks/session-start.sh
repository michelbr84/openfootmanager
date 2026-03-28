#!/usr/bin/env bash
# Hook: SessionStart — ClaudeMaxPower for OpenFoot Manager
set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  ClaudeMaxPower — OpenFoot Manager${NC}"
echo -e "${BLUE}============================================${NC}"

echo ""
echo -e "Date: $(date '+%Y-%m-%d %H:%M:%S')"

# Git context
if git rev-parse --is-inside-work-tree &>/dev/null; then
  BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
  echo -e "Branch: ${GREEN}${BRANCH}${NC}"
  echo ""
  echo "Recent commits:"
  git log --oneline -5 2>/dev/null | sed 's/^/  /' || echo "  (no commits yet)"
else
  echo -e "${YELLOW}Not inside a git repository.${NC}"
fi

# Session state recovery
echo ""
if [ -f ".estado.md" ]; then
  echo -e "${GREEN}Previous session state found (.estado.md):${NC}"
  echo "---"
  head -20 .estado.md
  echo "---"
else
  echo "No previous session state. Starting fresh."
fi

# Available skills
echo ""
echo "Available skills:"
if [ -d "skills" ]; then
  for f in skills/*.md; do
    [ -f "$f" ] && echo "  /$(basename "$f" .md)"
  done
else
  echo "  (skills/ directory not found)"
fi

# Auto Dream — background memory consolidation
if [ -f "scripts/auto-dream.sh" ]; then
  bash scripts/auto-dream.sh &>/dev/null &
fi

echo ""
echo -e "${BLUE}============================================${NC}"
echo ""
