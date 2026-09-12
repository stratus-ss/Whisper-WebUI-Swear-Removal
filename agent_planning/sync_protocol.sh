#!/usr/bin/env bash
set -euo pipefail

# Sync canonical agent_planning protocol files from scratch_pad to all
# downstream repos that have an agent_planning/ directory.
#
# Usage:
#   ./sync_protocol.sh              # sync all known repos
#   ./sync_protocol.sh --dry-run    # show what would be copied
#   ./sync_protocol.sh --discover   # find repos with agent_planning/ under ~/git_projects

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL="$SCRIPT_DIR"
GIT_PROJECTS="${GIT_PROJECTS_ROOT:-$HOME/git_projects}"

CANONICAL_FILES=(
  "PLAN_CORE.md"
  "EXECUTION_PROTOCOL.md"
  "deepseek/PLAN_INSTRUCTIONS.md"
  "deepseek/MODEL_ADDENDUM.md"
  "minimax/PLAN_INSTRUCTIONS.md"
  "minimax/MODEL_ADDENDUM.md"
  "prompts/README.md"
)

CANONICAL_DIRS=(
  "addenda"
)

KNOWN_REPOS=(
  "OpenAudible-To-AudioBookShelf"
  "infra-playbooks"
  "silverblue-desktop"
  "openshift-sv-tools-dev"
  "D&D_Workflow"
)

DRY_RUN=false
DISCOVER=false

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --discover) DISCOVER=true ;;
  esac
done

if $DISCOVER; then
  echo "Repos with agent_planning/ under $GIT_PROJECTS:"
  find "$GIT_PROJECTS" -maxdepth 2 -type d -name "agent_planning" \
    ! -path "*/scratch_pad/*" -printf "  %h\n" 2>/dev/null | sort
  exit 0
fi

sync_file() {
  local src="$1" dst="$2"
  if $DRY_RUN; then
    if [ -f "$dst" ] && diff -q "$src" "$dst" >/dev/null 2>&1; then
      echo "  [skip]  $dst (identical)"
    else
      echo "  [copy]  $src -> $dst"
    fi
  else
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
  fi
}

errors=0
for repo in "${KNOWN_REPOS[@]}"; do
  target="$GIT_PROJECTS/$repo/agent_planning"
  if [ ! -d "$target" ]; then
    echo "WARNING: $target does not exist — skipping"
    continue
  fi

  echo "=== $repo ==="

  for f in "${CANONICAL_FILES[@]}"; do
    if [ ! -f "$CANONICAL/$f" ]; then
      echo "  ERROR: canonical file $f missing from $CANONICAL"
      ((errors++))
      continue
    fi
    sync_file "$CANONICAL/$f" "$target/$f"
  done

  for d in "${CANONICAL_DIRS[@]}"; do
    if [ ! -d "$CANONICAL/$d" ]; then
      echo "  ERROR: canonical dir $d missing from $CANONICAL"
      ((errors++))
      continue
    fi
    for f in "$CANONICAL/$d"/*.md; do
      [ -f "$f" ] || continue
      rel="${f#"$CANONICAL"/}"
      sync_file "$f" "$target/$rel"
    done
  done
done

if ! $DRY_RUN; then
  echo ""
  echo "=== Verification ==="
  for repo in "${KNOWN_REPOS[@]}"; do
    target="$GIT_PROJECTS/$repo/agent_planning"
    [ -d "$target" ] || continue
    mismatches=0
    for f in "${CANONICAL_FILES[@]}"; do
      [ -f "$CANONICAL/$f" ] || continue
      if ! diff -q "$CANONICAL/$f" "$target/$f" >/dev/null 2>&1; then
        echo "  MISMATCH: $repo/$f"
        ((mismatches++))
      fi
    done
    if [ "$mismatches" -eq 0 ]; then
      echo "  $repo: all files in sync"
    fi
  done
fi

if [ "$errors" -gt 0 ]; then
  echo "Completed with $errors error(s)"
  exit 1
fi
