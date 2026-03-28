#!/usr/bin/env bash
# Hook: PreToolUse (Bash tool) — Safety guard + audit logging
set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

COMMAND="${CLAUDE_TOOL_INPUT_COMMAND:-}"
[ -z "$COMMAND" ] && exit 0

# Audit log
AUDIT_LOG=".claude/audit.log"
mkdir -p "$(dirname "$AUDIT_LOG")"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] BASH: $COMMAND" >> "$AUDIT_LOG"

# Block dangerous patterns
BLOCKED_PATTERNS=(
  "rm -rf /"
  "rm -rf ~"
  "rm --no-preserve-root"
  ":(){:|:&};:"
  "dd if=/dev/zero of=/dev/"
  "mkfs\."
  "> /dev/sd"
  "DROP TABLE"
  "DROP DATABASE"
  "TRUNCATE TABLE"
  "git push --force.*main"
  "git push --force.*master"
  "git push -f.*main"
  "git push -f.*master"
)

for pattern in "${BLOCKED_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qiE "$pattern"; then
    echo -e "${RED}[BLOCKED]${NC} Dangerous command pattern: '$pattern'"
    echo -e "${RED}Command:${NC} $COMMAND"
    exit 1
  fi
done

# Warn on installs
WARN_PATTERNS=(
  "pip install"
  "pip3 install"
  "npm install"
  "curl.*|.*sh"
)

for pattern in "${WARN_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qiE "$pattern"; then
    echo -e "${YELLOW}[WARN]${NC} Package installation detected."
    echo -e "Command: $COMMAND"
    break
  fi
done

# Secret leak check
if echo "$COMMAND" | grep -qiE "echo.*(GITHUB_TOKEN|SENTRY_TOKEN|API_KEY|SECRET|PASSWORD)"; then
  echo -e "${YELLOW}[WARN]${NC} Command may expose a secret value."
fi

exit 0
