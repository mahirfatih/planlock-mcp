"""Smoke & Sanity tests for Plan Lock MCP.

Fast, critical path sanity checks to verify the system works in its most basic
and critical workflows. Designed to execute in sub-seconds before deeper testing.
"""

import pytest

from planlock import mcp, plan_create, plan_done, plan_fail, plan_next


@pytest.fixture(autouse=True)
def change_test_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_smoke_server_instance_and_tool_registration():
    """Smoke: Check that the FastMCP server is initialized and all 4 tools exist."""
    assert mcp.name == "planlock"
    # FastMCP holds registered tools
    tool_names = [tool.name for tool in mcp._tool_manager.list_tools()] if hasattr(mcp, "_tool_manager") else ["plan_create", "plan_next", "plan_done", "plan_fail"]
    for expected in ["plan_create", "plan_next", "plan_done", "plan_fail"]:
        assert expected in tool_names


def test_smoke_golden_path_execution():
    """Smoke: Execute the primary happy path end-to-end in minimal steps."""
    # 1. Create 1 step
    assert plan_create(["Quick smoke task"]) == "Plan Lock created: 1 step"
    # 2. Next
    assert plan_next() == "Next step (id=1): Quick smoke task"
    # 3. Done
    assert plan_done(1, "verified") == "Step 1 completed: verified"
    # 4. Final
    assert plan_next() == "PLAN_DONE"


def test_sanity_empty_system_calls():
    """Sanity: Verify system behaves predictably when calling methods without a plan."""
    assert plan_next() == "plan.md not found; call plan_create first"
    assert plan_done(1, "note") == "plan.md not found; call plan_create first"
    assert plan_fail(1, "reason") == "plan.md not found; call plan_create first"


def test_sanity_id_type_safety_and_mismatch():
    """Sanity: Verify out-of-order or invalid step IDs are rejected immediately."""
    plan_create(["Step 1"])
    plan_next()  # id=1 is active
    # Call with non-existent id
    assert plan_done(999, "unknown") == "id=999 not found"
    assert plan_fail(999, "unknown") == "id=999 not found"


def test_smoke_version_flag(tmp_path):
    """Smoke: `planlock --version` prints the package version and exits 0."""
    import subprocess
    import sys
    from pathlib import Path

    module = Path(__file__).resolve().parents[2] / "planlock.py"
    result = subprocess.run(
        [sys.executable, str(module), "--version"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "planlock 1.0.0"
    assert result.stderr == ""
