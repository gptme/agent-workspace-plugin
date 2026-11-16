#!/usr/bin/env python3
"""PostToolUse hook: validates task file YAML frontmatter.

Called by Claude Code after Write/Edit operations on task files.
Reads tool input from stdin, validates frontmatter, outputs JSON on stdout.
"""

import json
import sys


# Vendored copy of gptodo's canonical states (gptodo.utils.get_canonical_states):
# the plugin must work without gptodo installed, so it cannot import it.
# tests/test_validate_task.py compares this set against gptodo when available.
VALID_STATES = {
    "backlog",
    "todo",
    "active",
    "ready_for_review",
    "waiting",
    "draft",
    "someday",
    "done",
    "cancelled",
    "expired",
}

# Deprecated aliases gptodo still reads (maps to the canonical state).
DEPRECATED_STATES = {"new": "backlog", "paused": "backlog"}


def validate_task_frontmatter(content: str) -> str | None:
    """Check that task content has valid frontmatter. Returns error message or None."""
    lines = content.split("\n")

    # Must start with frontmatter delimiter
    if not lines or lines[0].strip() != "---":
        return "Task file missing YAML frontmatter (must start with ---)"

    # Find closing delimiter
    end = -1
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end = i
            break

    if end == -1:
        return "Task file has unclosed YAML frontmatter (missing closing ---)"

    frontmatter = "\n".join(lines[1:end])

    # Check for required 'state' field
    state_value = None
    has_created = False
    for line in frontmatter.split("\n"):
        stripped = line.strip()
        if stripped.startswith("state:"):
            state_value = stripped.split(":", 1)[1].strip()
        if stripped.startswith("created:"):
            has_created = True

    if state_value is None:
        return "Task file missing required 'state' field in frontmatter"

    if not has_created:
        return "Task file missing required 'created' field in frontmatter"

    if state_value not in VALID_STATES and state_value not in DEPRECATED_STATES:
        return (
            f"Invalid task state '{state_value}'. "
            f"Valid states: {', '.join(sorted(VALID_STATES))}"
        )

    return None


def state_deprecation_warning(content: str) -> str | None:
    """Warning (not an error) when the task uses a deprecated state alias."""
    for line in content.split("\n")[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if stripped.startswith("state:"):
            state = stripped.split(":", 1)[1].strip()
            if state in DEPRECATED_STATES:
                return (
                    f"Task state '{state}' is deprecated; "
                    f"use '{DEPRECATED_STATES[state]}'"
                )
            break
    return None


def main():
    """Main entry point for PostToolUse hook."""
    try:
        input_data = json.load(sys.stdin)

        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        # Get file path from tool input
        file_path = tool_input.get("file_path", "")

        # Only validate task files (not README)
        if "/tasks/" not in file_path or file_path.endswith("README.md"):
            print(json.dumps({}))
            sys.exit(0)

        # Only validate .md files
        if not file_path.endswith(".md"):
            print(json.dumps({}))
            sys.exit(0)

        # For Write operations, validate the content directly
        if tool_name == "Write":
            content = tool_input.get("content", "")
            error = validate_task_frontmatter(content)
            if not error:
                error = state_deprecation_warning(content)
        elif tool_name == "Edit":
            # For Edit, we can't fully validate from the diff alone
            # Just output a reminder
            print(json.dumps({}))
            sys.exit(0)
        else:
            print(json.dumps({}))
            sys.exit(0)

        if error:
            result = {
                "systemMessage": f"Task validation warning: {error}"
            }
        else:
            result = {}

        print(json.dumps(result))

    except Exception as e:
        # Always output valid JSON, always exit 0
        print(json.dumps({"systemMessage": f"Task validation error: {e}"}))

    sys.exit(0)


if __name__ == "__main__":
    main()
