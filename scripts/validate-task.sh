#!/bin/bash
# Validate task files on write/edit
# Called by PostToolUse hook for Write/Edit operations

FILE="$1"

# Only validate task files
case "$FILE" in
  */tasks/*.md) ;;
  *) exit 0 ;;
esac

# Skip README
[[ "$(basename "$FILE")" == "README.md" ]] && exit 0

# Check for required frontmatter fields
if ! head -20 "$FILE" | grep -q "^state:"; then
  echo "Warning: Task file missing 'state' field in frontmatter"
  echo "Required format:"
  echo "---"
  echo "state: todo"
  echo "created: $(date -Iseconds)"
  echo "---"
  exit 1
fi

if ! head -20 "$FILE" | grep -q "^created:"; then
  echo "Warning: Task file missing 'created' field in frontmatter"
  exit 1
fi

# Validate state value
STATE=$(head -20 "$FILE" | grep "^state:" | awk '{print $2}')
case "$STATE" in
  backlog|todo|active|waiting|done|cancelled|someday) ;;
  *)
    echo "Warning: Invalid task state '$STATE'"
    echo "Valid states: backlog, todo, active, waiting, done, cancelled, someday"
    exit 1
    ;;
esac

exit 0
