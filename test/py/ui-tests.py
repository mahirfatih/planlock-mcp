"""Automated UI tests for Plan Lock MCP.

The server is stdio-only and has no graphical interface. Its user interface is
the MCP client surface: the tool catalog and the text an operator or agent
reads in ``tools/call`` results. These tests drive that surface over real
JSON-RPC on stdin/stdout and assert the rendered contract.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

import pytest

MODULE_PATH = Path(__file__).resolve().parents[2] / "planlock.py"
TIMEOUT_SECONDS = 15

pytestmark = pytest.mark.ui


def _spawn(cwd: Path) -> subprocess.Popen[str]:
    """Start a real server process in an isolated working directory."""
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    return subprocess.Popen(
        [sys.executable, str(MODULE_PATH)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        cwd=str(cwd),
    )


def _send(proc: subprocess.Popen[str], payload: dict[str, Any]) -> None:
    """Write one JSON-RPC message to the server's stdin."""
    assert proc.stdin is not None
    proc.stdin.write(json.dumps(payload) + "\n")
    proc.stdin.flush()


def _read(proc: subprocess.Popen[str]) -> dict[str, Any]:
    """Read one JSON-RPC message from the server's stdout with a timeout."""
    assert proc.stdout is not None
    holder: dict[str, str] = {}

    def readline() -> None:
        holder["line"] = proc.stdout.readline()  # type: ignore[union-attr]

    thread = threading.Thread(target=readline, daemon=True)
    thread.start()
    thread.join(TIMEOUT_SECONDS)
    if "line" not in holder:
        raise AssertionError("timed out waiting for a message from the MCP server")
    return json.loads(holder["line"])


def _request(
    proc: subprocess.Popen[str], request_id: int, method: str, params: dict[str, Any]
) -> dict[str, Any]:
    """Send a request and return the response with the matching id."""
    _send(proc, {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
    for _ in range(10):
        message = _read(proc)
        if message.get("id") == request_id:
            return message
    raise AssertionError(f"no response for {method!r}")


def _call(
    proc: subprocess.Popen[str], request_id: int, name: str, arguments: dict[str, Any]
) -> str:
    """Call a tool and return the text rendered to the MCP client."""
    response = _request(
        proc,
        request_id,
        "tools/call",
        {"name": name, "arguments": arguments},
    )
    return response["result"]["content"][0]["text"]


@pytest.fixture
def client(tmp_path: Path):
    """Start an initialized server client in a temporary working directory."""
    proc = _spawn(tmp_path)
    try:
        init = _request(
            proc,
            1,
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "pytest-ui", "version": "0"},
            },
        )
        assert init["result"]["serverInfo"]["name"] == "planlock"
        _send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        yield proc, tmp_path
    finally:
        if proc.stdin is not None:
            proc.stdin.close()
        if proc.poll() is None:
            proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:  # pragma: no cover - defensive
            proc.kill()


def test_ui_tool_catalog_renders_four_tools(client) -> None:
    """UI: the client sees the four documented tools in tools/list."""
    proc, _ = client
    listing = _request(proc, 2, "tools/list", {})
    names = {tool["name"] for tool in listing["result"]["tools"]}
    assert {"plan_create", "plan_next", "plan_done", "plan_fail"} <= names


def test_ui_renders_create_and_next_messages(client) -> None:
    """UI: create and activation messages render with the absolute plan path."""
    proc, tmp_path = client
    plan_path = tmp_path / ".opencode" / "plan.md"

    assert _call(proc, 2, "plan_create", {"steps": []}) == "Step list cannot be empty"
    assert _call(proc, 3, "plan_create", {"steps": ["Write tests"]}) == (
        f"Plan Lock created: 1 step -> {plan_path}"
    )
    assert _call(proc, 4, "plan_next", {}) == (
        f"Next step (id=1, file: {plan_path}): Write tests"
    )
    assert _call(proc, 5, "plan_next", {}) == (
        "Plan Lock active: step 1 is still [~]. Call plan_done or plan_fail first."
    )


def test_ui_renders_done_fail_and_completion_messages(client) -> None:
    """UI: resolving a step renders the exact completion and failure messages."""
    proc, _ = client
    _call(proc, 2, "plan_create", {"steps": ["Success step", "Failure step"]})
    _call(proc, 3, "plan_next", {})

    assert _call(proc, 4, "plan_done", {"id": 1, "note": "   "}) == "Note cannot be empty"
    assert _call(proc, 5, "plan_done", {"id": 1, "note": "shipped"}) == (
        "Step 1 completed: shipped"
    )
    assert "Failure step" in _call(proc, 6, "plan_next", {})
    assert _call(proc, 7, "plan_fail", {"id": 2, "reason": "   "}) == (
        "Reason cannot be empty"
    )
    assert _call(proc, 8, "plan_fail", {"id": 2, "reason": "timeout"}) == (
        "Step 2 failed: timeout"
    )
    assert _call(proc, 9, "plan_next", {}) == "PLAN_DONE"


def test_ui_renders_missing_and_invalid_id_messages(client) -> None:
    """UI: missing-plan, unknown-id and inactive-id errors render cleanly."""
    proc, _ = client

    assert _call(proc, 2, "plan_done", {"id": 1, "note": "late"}) == (
        "plan.md not found; call plan_create first"
    )
    _call(proc, 3, "plan_create", {"steps": ["First", "Second"]})
    _call(proc, 4, "plan_next", {})

    assert _call(proc, 5, "plan_done", {"id": 9, "note": "note"}) == "id=9 not found"
    assert _call(proc, 6, "plan_done", {"id": 2, "note": "note"}) == (
        "id=2 is not the active step"
    )
