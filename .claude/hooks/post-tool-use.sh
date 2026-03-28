#!/usr/bin/env bash
# Hook: PostToolUse (Edit, Write) — Auto-run tests after code changes
set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

FILE_PATH="${CLAUDE_TOOL_OUTPUT_FILE_PATH:-}"
[ -z "$FILE_PATH" ] && exit 0

# Only act on Python source files
case "$FILE_PATH" in
  *.py) ;;
  *) exit 0 ;;
esac

echo ""
echo "[post-tool-use] File changed: $FILE_PATH"

# Find nearest tests/ directory (max 3 levels up)
DIR=$(dirname "$FILE_PATH")
TEST_DIR=""
for _ in 1 2 3; do
  if [ -d "$DIR/tests" ]; then
    TEST_DIR="$DIR/tests"
    break
  fi
  DIR=$(dirname "$DIR")
done

if [ -n "$TEST_DIR" ] && [ -d "$TEST_DIR" ]; then
  echo "Running tests: poetry run pytest $TEST_DIR -q --tb=short"
  if poetry run pytest "$TEST_DIR" -q --tb=short 2>&1; then
    echo -e "${GREEN}[PASS]${NC} All tests passed."
  else
    echo -e "${RED}[FAIL]${NC} Tests failed after editing $FILE_PATH"
    echo "Fix the failing tests before proceeding."
  fi
else
  echo -e "${YELLOW}[SKIP]${NC} No tests/ directory found near $FILE_PATH"
fi

echo ""
