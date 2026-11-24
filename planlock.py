"""Plan Lock MCP — one-at-a-time plan execution enforcer for local LLMs."""

import functools
import os
import re
import tempfile
import threading
import time

try:
    from mcp.server.fastmcp import FastMCP
except (ImportError, ModuleNotFoundError):
    from mcp.server.mcpserver import MCPServer as FastMCP

mcp = FastMCP("planlock")

OPENCODE_DIR = ".opencode"
PLAN_FILE = os.path.join(OPENCODE_DIR, "plan.md")
BACKUP_FILE = os.path.join(OPENCODE_DIR, "plan.md.bak")
GITIGNORE_FILE = os.path.join(OPENCODE_DIR, ".gitignore")
GITIGNORE_ENTRIES = ("plan.md", "plan.md.bak")

# Pattern matches lines like: "- [ ] 1. <step>" or "- [x] 2. <step> — note: note"
STEP_PATTERN = re.compile(r"^-\s*\[([ x~!])\]\s*(\d+)\.\s*(.*?)$")

# Serializes read-modify-write cycles so two concurrent tool calls cannot both
# observe an unlocked plan and activate the same step.
_STATE_LOCK = threading.RLock()


def _single_line(text: str) -> str:
    """Collapses whitespace so user input can never inject a new plan line."""
    return " ".join(str(text).split())


def _locked(func):
    """Runs a tool body while holding the plan state lock."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with _STATE_LOCK:
            return func(*args, **kwargs)
    return wrapper


def _atomic_write(filepath: str, content: str) -> None:
    """Atomically writes content to a file using a temporary file and os.replace."""
    dir_name = os.path.dirname(filepath) or "."
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, prefix=".tmp_plan_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, filepath)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _read_plan_lines() -> list[str]:
    """Reads the raw lines of plan.md."""
    if not os.path.exists(PLAN_FILE):
        return []
    with open(PLAN_FILE, encoding="utf-8") as f:
        return f.readlines()


def _ensure_gitignore() -> None:
    """Ensures .opencode/.gitignore ignores both plan.md and its backup."""
    if os.path.exists(GITIGNORE_FILE):
        with open(GITIGNORE_FILE, encoding="utf-8") as f:
            content = f.read()
        existing = {line.strip() for line in content.splitlines()}
        missing = [entry for entry in GITIGNORE_ENTRIES if entry not in existing]
        if not missing:
            return
    else:
        content = ""
        missing = list(GITIGNORE_ENTRIES)

    if content and not content.endswith("\n"):
        content += "\n"
    content += "".join(entry + "\n" for entry in missing)
    _atomic_write(GITIGNORE_FILE, content)


@mcp.tool()
@_locked
def plan_create(steps: list[str]) -> str:
    """Create a new plan and write it to .opencode/plan.md.

    Args:
        steps: List of step descriptions to add to the plan.

    Returns:
        A message reporting the number of created steps on success,
        or an error message on failure.
    """
    clean_steps = [_single_line(step) for step in steps]
    if not clean_steps:
        return "Step list cannot be empty"
    if any(not step for step in clean_steps):
        return "Step text cannot be empty"

    os.makedirs(OPENCODE_DIR, exist_ok=True)
    _ensure_gitignore()

    if os.path.exists(PLAN_FILE):
        with open(PLAN_FILE, encoding="utf-8") as f_src:
            content_src = f_src.read()
        _atomic_write(BACKUP_FILE, content_src)

    project = os.path.basename(os.getcwd()) or "unknown"
    ts = int(time.time())
    lines = [f"# Plan — {project}\n", f"- created: {ts}\n", "\n"]
    for idx, step in enumerate(clean_steps, start=1):
        lines.append(f"- [ ] {idx}. {step}\n")

    _atomic_write(PLAN_FILE, "".join(lines))
    label = "step" if len(clean_steps) == 1 else "steps"
    return f"Plan Lock created: {len(clean_steps)} {label}"


@mcp.tool()
@_locked
def plan_next() -> str:
    """Activate the next pending plan step ([~]) and return it.

    Returns:
        The ID and text of the next step; an error message if a lock is already
        active or the plan file is missing; 'PLAN_DONE' when all steps are done.
    """
    if not os.path.exists(PLAN_FILE):
        return "plan.md not found; call plan_create first"

    lines = _read_plan_lines()

    active_id = None
    next_step_index = None
    next_step_id = None
    next_step_text = ""

    for i, line in enumerate(lines):
        match = STEP_PATTERN.match(line.strip())
        if match:
            status, step_id, rest = match.groups()
            if status == "~":
                active_id = step_id
                break
            elif status == " " and next_step_index is None:
                next_step_index = i
                next_step_id = step_id
                next_step_text = rest.strip()

    if active_id is not None:
        return f"Plan Lock active: step {active_id} is still [~]. Call plan_done or plan_fail first."

    if next_step_index is None:
        return "PLAN_DONE"

    lines[next_step_index] = f"- [~] {next_step_id}. {next_step_text}\n"
    _atomic_write(PLAN_FILE, "".join(lines))

    return f"Next step (id={next_step_id}): {next_step_text}"


@mcp.tool()
@_locked
def plan_done(id: int, note: str) -> str:
    """Mark the active [~] step as completed [x] and append a note.

    Args:
        id: ID of the completed step.
        note: Short completion note to append to the step.

    Returns:
        A success or error message.
    """
    if not os.path.exists(PLAN_FILE):
        return "plan.md not found; call plan_create first"

    note_text = _single_line(note)
    if not note_text:
        return "Note cannot be empty"

    lines = _read_plan_lines()
    target_index = None
    step_text = ""

    for i, line in enumerate(lines):
        match = STEP_PATTERN.match(line.strip())
        if match:
            status, step_id, rest = match.groups()
            if int(step_id) == id:
                if status == "~":
                    target_index = i
                    step_text = rest.strip()
                    break
                else:
                    return f"id={id} is not the active step"

    if target_index is None:
        return f"id={id} not found"

    lines[target_index] = f"- [x] {id}. {step_text} — note: {note_text}\n"
    _atomic_write(PLAN_FILE, "".join(lines))

    return f"Step {id} completed: {note_text}"


@mcp.tool()
@_locked
def plan_fail(id: int, reason: str) -> str:
    """Mark the active [~] step as failed [!] and append a reason.

    Args:
        id: ID of the failed step.
        reason: Reason for the failure.

    Returns:
        A success or error message.
    """
    if not os.path.exists(PLAN_FILE):
        return "plan.md not found; call plan_create first"

    reason_text = _single_line(reason)
    if not reason_text:
        return "Reason cannot be empty"

    lines = _read_plan_lines()
    target_index = None
    step_text = ""

    for i, line in enumerate(lines):
        match = STEP_PATTERN.match(line.strip())
        if match:
            status, step_id, rest = match.groups()
            if int(step_id) == id:
                if status == "~":
                    target_index = i
                    step_text = rest.strip()
                    break
                else:
                    return f"id={id} is not the active step"

    if target_index is None:
        return f"id={id} not found"

    lines[target_index] = f"- [!] {id}. {step_text} — error: {reason_text}\n"
    _atomic_write(PLAN_FILE, "".join(lines))

    return f"Step {id} failed: {reason_text}"


def main() -> None:
    """Run the MCP server over stdio (entry point for ``planlock``)."""
    mcp.run()


if __name__ == "__main__":
    main()
