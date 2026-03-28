#!/usr/bin/env bash
# ClaudeMaxPower Setup for OpenFoot Manager
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; }

echo ""
echo "============================================"
echo "  ClaudeMaxPower — OpenFoot Manager Setup"
echo "============================================"
echo ""

# Check required tools
MISSING=0
check_tool() {
  if command -v "$1" &>/dev/null; then
    ok "$1 found"
  else
    err "$1 not found. $2"
    MISSING=$((MISSING + 1))
  fi
}

check_tool "claude"  "Install: npm install -g @anthropic-ai/claude-code"
check_tool "git"     "Install: https://git-scm.com"
check_tool "python3" "Install: https://python.org"
check_tool "poetry"  "Install: pip install poetry"

echo ""
[ "$MISSING" -gt 0 ] && { err "$MISSING tool(s) missing."; exit 1; }

# Make scripts executable
echo "Making scripts executable..."
chmod +x .claude/hooks/*.sh 2>/dev/null || true
chmod +x scripts/*.sh 2>/dev/null || true
ok "Scripts are executable."

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
poetry install
ok "Dependencies installed."

echo ""
echo "============================================"
echo "  Setup complete!"
echo "============================================"
echo ""
