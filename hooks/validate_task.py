#!/usr/bin/env python3
"""PostToolUse hook: validates task file YAML frontmatter.

Called by Claude Code after Write/Edit operations on task files.
Reads tool input from stdin, validates frontmatter, outputs JSON on stdout.
"""

from __future__ import annotations

import json
import sys


VALID_STATES = {"backlog", "todo", "active", "waiting", "done", "cancelled", "someday"}


def _scalar(value: str) -> str:
    """A frontmatter scalar without a trailing `# comment` or YAML quotes."""
    value = value.split(" #", 1)[0].strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        value = value[1:-1]
    return value


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
            state_value = _scalar(stripped.split(":", 1)[1])
        if stripped.startswith("created:"):
            has_created = True

    if state_value is None:
        return "Task file missing required 'state' field in frontmatter"

    if not has_created:
        return "Task file missing required 'created' field in frontmatter"

    if state_value not in VALID_STATES:
        return (
            f"Invalid task state '{state_value}'. "
            f"Valid states: {', '.join(sorted(VALID_STATES))}"
        )

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
        elif tool_name == "Edit":
            # PostToolUse runs after the edit, so the file on disk is the result.
            with open(file_path, encoding="utf-8") as f:
                error = validate_task_frontmatter(f.read())
        else:
            print(json.dumps({}))
            sys.exit(0)

        if error:
            message = f"Task validation warning: {error}"
            # systemMessage is shown to the user; additionalContext reaches the
            # model, which is the one that can fix the file.
            result = {
                "systemMessage": message,
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": message,
                },
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
