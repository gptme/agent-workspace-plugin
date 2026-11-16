"""Tests for hooks/validate_task.py state validation."""

import importlib.util
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "validate_task.py"
spec = importlib.util.spec_from_file_location("validate_task", HOOK)
assert spec and spec.loader
validate_task = importlib.util.module_from_spec(spec)
sys.modules["validate_task"] = validate_task
spec.loader.exec_module(validate_task)


def task(state: str) -> str:
    return f"---\nstate: {state}\ncreated: 2026-11-16T00:00:00+00:00\n---\n\n# T\n"


CANONICAL = [
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
]


@pytest.mark.parametrize("state", CANONICAL)
def test_canonical_state_accepted(state):
    assert validate_task.validate_task_frontmatter(task(state)) is None
    assert validate_task.state_deprecation_warning(task(state)) is None


@pytest.mark.parametrize("alias,canonical", [("new", "backlog"), ("paused", "backlog")])
def test_deprecated_alias_warns_but_is_not_an_error(alias, canonical):
    assert validate_task.validate_task_frontmatter(task(alias)) is None
    warning = validate_task.state_deprecation_warning(task(alias))
    assert warning and alias in warning and canonical in warning


def test_invalid_state_is_an_error():
    error = validate_task.validate_task_frontmatter(task("finished"))
    assert error and "Invalid task state 'finished'" in error


def test_matches_gptodo_canonical_states():
    """Drift guard: the vendored list must equal gptodo's (skipped without gptodo)."""
    utils = pytest.importorskip("gptodo.utils")
    assert set(utils.get_canonical_states()) == validate_task.VALID_STATES
