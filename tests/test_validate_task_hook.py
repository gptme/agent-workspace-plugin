"""Run hooks/validate_task.py the way Claude Code does: hook JSON on stdin."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "hooks" / "validate_task.py"

VALID = "---\nstate: active\ncreated: 2026-11-24T00:00:00Z\n---\n# Task\n"


def run_hook(payload: dict) -> dict:
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def write(path: Path, content: str) -> dict:
    return run_hook(
        {
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": str(path), "content": content},
        }
    )


def model_context(result: dict) -> str:
    return result.get("hookSpecificOutput", {}).get("additionalContext", "")


def test_valid_task_is_silent(tmp_path):
    assert write(tmp_path / "tasks" / "t.md", VALID) == {}


def test_warning_reaches_the_model(tmp_path):
    # systemMessage is shown to the user only; the model needs additionalContext.
    result = write(tmp_path / "tasks" / "t.md", VALID.replace("active", "finished"))
    assert "Invalid task state 'finished'" in model_context(result)
    assert result["hookSpecificOutput"]["hookEventName"] == "PostToolUse"


def test_inline_comment_and_quotes_are_not_part_of_the_state(tmp_path):
    # The task-management skill's own template annotates the field this way.
    commented = VALID.replace("state: active", "state: active   # Required: backlog")
    assert write(tmp_path / "tasks" / "t.md", commented) == {}
    quoted = VALID.replace("state: active", 'state: "active"')
    assert write(tmp_path / "tasks" / "t.md", quoted) == {}


def test_edit_validates_the_file_on_disk(tmp_path):
    task = tmp_path / "tasks" / "t.md"
    task.parent.mkdir()
    task.write_text(VALID.replace("active", "finished"))  # PostToolUse: already edited
    result = run_hook(
        {
            "hook_event_name": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(task),
                "old_string": "state: active",
                "new_string": "state: finished",
            },
        }
    )
    assert "Invalid task state 'finished'" in model_context(result)


def test_edit_of_valid_file_is_silent(tmp_path):
    task = tmp_path / "tasks" / "t.md"
    task.parent.mkdir()
    task.write_text(VALID)
    result = run_hook(
        {"tool_name": "Edit", "tool_input": {"file_path": str(task)}}
    )
    assert result == {}


def test_hook_command_quotes_plugin_root():
    # An unquoted ${CLAUDE_PLUGIN_ROOT} breaks on paths with spaces, and the
    # resulting python exit code 2 is Claude Code's blocking code.
    config = json.loads((ROOT / "hooks" / "hooks.json").read_text())
    command = config["hooks"]["PostToolUse"][0]["hooks"][0]["command"]
    assert '"${CLAUDE_PLUGIN_ROOT}/hooks/validate_task.py"' in command
