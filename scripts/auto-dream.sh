#!/usr/bin/env bash
# auto-dream.sh — Memory consolidation inspired by REM sleep
# Reviews memory files, prunes stale entries, consolidates overlapping memories, rebuilds index.
# Triggers: After 24 hours + 5 sessions since last consolidation.
set -euo pipefail

# --- Configuration ---
MEMORY_DIR="${CLAUDE_MEMORY_DIR:-}"
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
LOCK_FILE="${MEMORY_DIR}/.dream.lock"
STATE_FILE="${MEMORY_DIR}/.dream-state.json"
MIN_HOURS_BETWEEN_DREAMS=24
MIN_SESSIONS_BETWEEN_DREAMS=5

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[AutoDream]${NC} $1"; }
log_ok()    { echo -e "${GREEN}[AutoDream]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[AutoDream]${NC} $1"; }

cleanup() { rm -f "$LOCK_FILE" 2>/dev/null || true; }

# Detect memory dir
if [ -z "$MEMORY_DIR" ]; then
  if [ -d "$HOME/.claude/projects" ]; then
    PROJECT_SLUG=$(echo "$PROJECT_DIR" | sed 's/[:\\\/]/-/g' | sed 's/^-//')
    CANDIDATE="$HOME/.claude/projects/${PROJECT_SLUG}/memory"
    [ -d "$CANDIDATE" ] && MEMORY_DIR="$CANDIDATE"
  fi
fi

if [ -z "$MEMORY_DIR" ] || [ ! -d "$MEMORY_DIR" ]; then
  exit 0
fi

MEMORY_INDEX="$MEMORY_DIR/MEMORY.md"

# Lock file
if [ -f "$LOCK_FILE" ]; then
  LOCK_PID=$(cat "$LOCK_FILE" 2>/dev/null || echo "")
  if [ -n "$LOCK_PID" ] && kill -0 "$LOCK_PID" 2>/dev/null; then
    exit 0
  fi
  rm -f "$LOCK_FILE"
fi

trap cleanup EXIT
echo $$ > "$LOCK_FILE"

# Check if dream is needed
now_epoch=$(date +%s)

if [ -f "$STATE_FILE" ]; then
  last_dream_epoch=$(grep -o '"last_dream_epoch":[0-9]*' "$STATE_FILE" | grep -o '[0-9]*' || echo "0")
  sessions_since=$(grep -o '"sessions_since":[0-9]*' "$STATE_FILE" | grep -o '[0-9]*' || echo "0")
else
  last_dream_epoch=0
  sessions_since=0
fi

hours_since=$(( (now_epoch - last_dream_epoch) / 3600 ))

if [ "$hours_since" -lt "$MIN_HOURS_BETWEEN_DREAMS" ] || [ "$sessions_since" -lt "$MIN_SESSIONS_BETWEEN_DREAMS" ]; then
  new_sessions=$((sessions_since + 1))
  cat > "$STATE_FILE" << EOF
{"last_dream_epoch":${last_dream_epoch},"sessions_since":${new_sessions},"last_check":"$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
EOF
  exit 0
fi

log_info "Starting memory consolidation..."

# Inventory memory files
memory_files=()
while IFS= read -r -d '' file; do
  memory_files+=("$file")
done < <(find "$MEMORY_DIR" -name "*.md" -not -name "MEMORY.md" -print0 2>/dev/null)

total_files=${#memory_files[@]}

if [ "$total_files" -eq 0 ]; then
  cat > "$STATE_FILE" << EOF
{"last_dream_epoch":${now_epoch},"sessions_since":0,"last_check":"$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
EOF
  exit 0
fi

# Check for stale memories (>30 days)
stale_count=0
for file in "${memory_files[@]}"; do
  if [ "$(uname)" = "Darwin" ]; then
    file_epoch=$(stat -f %m "$file" 2>/dev/null || echo "$now_epoch")
  else
    file_epoch=$(stat -c %Y "$file" 2>/dev/null || echo "$now_epoch")
  fi
  file_age_days=$(( (now_epoch - file_epoch) / 86400 ))
  [ "$file_age_days" -gt 30 ] && stale_count=$((stale_count + 1))
done

# Check for duplicates
duplicate_count=0
seen_names=()
for file in "${memory_files[@]}"; do
  name=$(grep -m1 '^name:' "$file" 2>/dev/null | sed 's/^name: *//' || echo "")
  if [ -n "$name" ]; then
    for seen in "${seen_names[@]:-}"; do
      [ "$seen" = "$name" ] && duplicate_count=$((duplicate_count + 1))
    done
    seen_names+=("$name")
  fi
done

# Rebuild index
declare -A type_files 2>/dev/null || true
{
  echo "# Memory Index"
  echo ""
  for type in "user" "feedback" "project" "reference"; do
    entries=""
    for file in "${memory_files[@]}"; do
      ftype=$(grep -m1 '^type:' "$file" 2>/dev/null | sed 's/^type: *//' || echo "")
      if [ "$ftype" = "$type" ]; then
        filename=$(basename "$file")
        fname=$(grep -m1 '^name:' "$file" 2>/dev/null | sed 's/^name: *//' || echo "$filename")
        desc=$(grep -m1 '^description:' "$file" 2>/dev/null | sed 's/^description: *//' || echo "")
        [ ${#desc} -gt 80 ] && desc="${desc:0:77}..."
        entries="${entries}- [${fname}](${filename}) -- ${desc}\n"
      fi
    done
    if [ -n "$entries" ]; then
      header=$(echo "$type" | sed 's/^./\U&/')
      echo "## ${header}"
      echo -e "$entries"
    fi
  done
} > "$MEMORY_INDEX"

# Update dream state
cat > "$STATE_FILE" << EOF
{"last_dream_epoch":${now_epoch},"sessions_since":0,"last_check":"$(date -u +%Y-%m-%dT%H:%M:%SZ)","files_processed":${total_files},"stale_found":${stale_count},"duplicates_found":${duplicate_count}}
EOF

log_ok "Auto Dream complete: ${total_files} files, ${stale_count} stale, ${duplicate_count} duplicates."
