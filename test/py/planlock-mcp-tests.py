"""End-to-end test over the real MCP stdio transport.

The unit suite imports the server module directly. This file instead launches
``planlock.py`` as a subprocess and speaks JSON-RPC to it on stdin/stdout, so
the handshake, ``tools/list`` and two ``tools/call`` requests are exercised on
the actual wire path. The server runs with a temporary working directory, so
the repository's own plan files are never touched.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

MODULE_PATH = Path(__file__).resolve().parents[2] / "planlock.py"
_TIMEOUT_SECONDS = 15


def _spawn(cwd: Path) -> subprocess.Popen[str]:
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
    assert proc.stdin is not None
    proc.stdin.write(json.dumps(payload) + "\n")
    proc.stdin.flush()


def _read(proc: subprocess.Popen[str], *, timeout: int = _TIMEOUT_SECONDS) -> dict[str, Any]:
    assert proc.stdout is not None
    holder: dict[str, str] = {}

    def _readline() -> None:
        holder["line"] = proc.stdout.readline()  # type: ignore[union-attr]

    thread = threading.Thread(target=_readline, daemon=True)
    thread.start()
    thread.join(timeout)
    if "line" not in holder:
        raise AssertionError("timed out waiting for a message from the MCP server")
    return json.loads(holder["line"])


def _request(proc: subprocess.Popen[str], request_id: int, method: str, params: dict[str, Any]) -> dict[str, Any]:
    """Send a request and return the response with the matching id."""
    _send(proc, {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
    for _ in range(10):  # skip any interleaved notifications
        message = _read(proc)
        if message.get("id") == request_id:
            return message
    raise AssertionError(f"no response for {method!r}")


def _text(message: dict[str, Any]) -> str:
    """Return the text content of a tools/call response."""
    return message["result"]["content"][0]["text"]


def test_stdio_handshake_lists_tools_and_runs_a_plan(tmp_path: Path) -> None:
    proc = _spawn(tmp_path)
    try:
        init = _request(
            proc,
            1,
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "pytest", "version": "0"},
            },
        )
        assert init["result"]["serverInfo"]["name"] == "planlock"

        # The protocol expects an `initialized` notification before normal calls.
        _send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})

        listing = _request(proc, 2, "tools/list", {})
        names = {tool["name"] for tool in listing["result"]["tools"]}
        assert {"plan_create", "plan_next", "plan_done", "plan_fail"} <= names

        created = _request(
            proc,
            3,
            "tools/call",
            {"name": "plan_create", "arguments": {"steps": ["Alpha"]}},
        )
        assert _text(created) == "Plan Lock created: 1 step"

        activated = _request(proc, 4, "tools/call", {"name": "plan_next", "arguments": {}})
        assert "Alpha" in _text(activated)
        assert (tmp_path / ".opencode" / "plan.md").exists()
    finally:
        if proc.stdin is not None:
            proc.stdin.close()
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:  # pragma: no cover - defensive
            proc.kill()
