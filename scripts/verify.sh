#!/usr/bin/env bash
# ClaudeMaxPower Verification for OpenFoot Manager
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

ok()      { echo -e "${GREEN}[PASS]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail()    { echo -e "${RED}[FAIL]${NC} $1"; FAILURES=$((FAILURES + 1)); }
section() { echo -e "\n${BLUE}--- $1 ---${NC}"; }

FAILURES=0

echo ""
echo "============================================"
echo "  ClaudeMaxPower — Verification"
echo "============================================"

section "Required Tools"
for tool in git python3 poetry; do
  if command -v "$tool" &>/dev/null; then
    ok "$tool: $(command -v "$tool")"
  else
    fail "$tool: not found"
  fi
done

section "Hooks"
for hook in session-start pre-tool-use post-tool-use stop; do
  f=".claude/hooks/${hook}.sh"
  if [ -f "$f" ]; then
    ok "$f: found"
  else
    fail "$f: not found"
  fi
done

section "Skills"
for skill in assemble-team fix-issue review-pr tdd-loop refactor-module; do
  f="skills/${skill}.md"
  if [ -f "$f" ]; then
    ok "$f: found"
  else
    fail "$f: not found"
  fi
done

section "Agents"
for agent in team-coordinator code-reviewer implementer tester security-auditor doc-writer; do
  f=".claude/agents/${agent}.md"
  if [ -f "$f" ]; then
    ok "$f: found"
  else
    fail "$f: not found"
  fi
done

section "Tests"
if poetry run pytest ofm/tests/ -q --tb=short 2>/dev/null; then
  ok "All tests passing"
else
  fail "Some tests failing"
fi

echo ""
echo "============================================"
if [ "$FAILURES" -eq 0 ]; then
  echo -e "${GREEN}All checks passed! ClaudeMaxPower is ready.${NC}"
else
  echo -e "${RED}$FAILURES check(s) failed.${NC}"
fi
echo "============================================"
echo ""
