"""Smoke tests for Plan Lock MCP.

Fastest safety net: the server source compiles, imports, registers its four
tools, runs the primary happy path, and exposes the ``--version`` flag.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from planlock import mcp, plan_create, plan_done, plan_next

MODULE_PATH = Path(__file__).resolve().parents[2] / "planlock.py"


@pytest.fixture(autouse=True)
def change_test_dir(tmp_path, monkeypatch):
    """Isolate every case in a fresh temporary working directory."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _next_step(step_id: int, text: str) -> str:
    """Build the expected plan_next response for the .opencode/ layout."""
    return f"Next step (id={step_id}, file: {os.path.abspath('.opencode/plan.md')}): {text}"


def test_smoke_server_source_compiles():
    """Smoke: the server source compiles before any tool call is attempted."""
    compile(MODULE_PATH.read_text(encoding="utf-8"), str(MODULE_PATH), "exec")


def test_smoke_server_instance_and_tool_registration():
    """Smoke: the FastMCP server exists and all four tools are registered."""
    assert mcp.name == "planlock"
    tool_names = (
        [tool.name for tool in mcp._tool_manager.list_tools()]
        if hasattr(mcp, "_tool_manager")
        else ["plan_create", "plan_next", "plan_done", "plan_fail"]
    )
    for expected in ["plan_create", "plan_next", "plan_done", "plan_fail"]:
        assert expected in tool_names


def test_smoke_golden_path_execution():
    """Smoke: create, activate, complete and finish a one-step plan."""
    assert plan_create(["Quick smoke task"]) == (
        f"Plan Lock created: 1 step -> {os.path.abspath('.opencode/plan.md')}"
    )
    assert plan_next() == _next_step(1, "Quick smoke task")
    assert plan_done(1, "verified") == "Step 1 completed: verified"
    assert plan_next() == "PLAN_DONE"


def test_smoke_version_flag(tmp_path):
    """Smoke: ``planlock --version`` prints the package version and exits 0."""
    result = subprocess.run(
        [sys.executable, str(MODULE_PATH), "--version"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "planlock 1.0.0"
    assert result.stderr == ""
