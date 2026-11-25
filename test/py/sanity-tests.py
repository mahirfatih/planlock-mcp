"""Sanity tests for Plan Lock MCP.

Minimum acceptance criteria at the contract level: exact tool response strings,
the plan header format, and the two supported plan locations.
"""

import os
import re
import time
from pathlib import Path

import pytest

from planlock import plan_create, plan_done, plan_fail, plan_next


@pytest.fixture(autouse=True)
def change_test_dir(tmp_path, monkeypatch):
    """Isolate every case in a fresh temporary working directory."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _next_step(step_id: int, text: str) -> str:
    """Build the expected plan_next response for the .opencode/ layout."""
    return f"Next step (id={step_id}, file: {os.path.abspath('.opencode/plan.md')}): {text}"


def test_sanity_empty_system_calls():
    """Sanity: calls before plan_create report the documented missing-plan error."""
    assert plan_next() == "plan.md not found; call plan_create first"
    assert plan_done(1, "note") == "plan.md not found; call plan_create first"
    assert plan_fail(1, "reason") == "plan.md not found; call plan_create first"


def test_sanity_id_type_safety_and_mismatch():
    """Sanity: unknown ids and inactive ids are rejected with distinct messages."""
    plan_create(["Step 1"])
    plan_next()

    assert plan_done(999, "unknown") == "id=999 not found"
    assert plan_fail(999, "unknown") == "id=999 not found"


def test_sanity_tool_response_contract():
    """Sanity: every user-facing tool message matches the documented contract."""
    plan_path = os.path.abspath(".opencode/plan.md")

    assert plan_create([]) == "Step list cannot be empty"
    assert plan_create("ab") == "Steps must be a list of strings"
    assert plan_create(["   "]) == "Step text cannot be empty"
    assert plan_create(["Alpha", "Beta"]) == (
        f"Plan Lock created: 2 steps -> {plan_path}"
    )
    assert plan_next() == _next_step(1, "Alpha")
    assert plan_next() == (
        "Plan Lock active: step 1 is still [~]. Call plan_done or plan_fail first."
    )
    assert plan_done(1, "   ") == "Note cannot be empty"
    assert plan_fail(1, "   ") == "Reason cannot be empty"
    assert plan_done(9, "note") == "id=9 not found"
    assert plan_done(2, "note") == "id=2 is not the active step"
    assert plan_done(1, "ok") == "Step 1 completed: ok"
    assert plan_next() == _next_step(2, "Beta")
    assert plan_fail(2, "boom") == "Step 2 failed: boom"
    assert plan_next() == "PLAN_DONE"


def test_sanity_plan_header_contract():
    """Sanity: the header records the project name and a current unix timestamp."""
    before = int(time.time())
    plan_create(["Header check"])
    after = int(time.time())

    lines = Path(".opencode/plan.md").read_text(encoding="utf-8").splitlines(keepends=True)
    assert lines[0] == f"# Plan — {os.path.basename(os.getcwd())}\n"
    assert re.fullmatch(r"- created: \d+\n", lines[1])
    assert before <= int(lines[1].removeprefix("- created: ").strip()) <= after
    assert lines[2] == "\n"


def test_sanity_plan_location_contract(tmp_path, monkeypatch):
    """Sanity: project markers select the root plan, other folders use .opencode/."""
    root = tmp_path / "root"
    root.mkdir()
    (root / ".git").mkdir()
    monkeypatch.chdir(root)

    assert plan_create(["Root step"]) == (
        f"Plan Lock created: 1 step -> {root / 'plan.md'}"
    )
    assert (root / "plan.md").exists()
    assert "plan.md" in (root / ".gitignore").read_text(encoding="utf-8").splitlines()

    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.chdir(scratch)

    assert plan_create(["Scratch step"]) == (
        f"Plan Lock created: 1 step -> {scratch / '.opencode' / 'plan.md'}"
    )
    assert not (scratch / "plan.md").exists()
    assert (scratch / ".opencode" / "plan.md").exists()
    ignore_lines = (scratch / ".opencode" / ".gitignore").read_text(
        encoding="utf-8"
    ).splitlines()
    assert "plan.md" in ignore_lines
    assert ".gitignore" in ignore_lines
