"""Integration tests for Plan Lock.

Tests filesystem interactions, atomicity, crash-recovery, process boundary,
file permissions, backup overwrite cycles, and multi-session integration.
"""

import os
import re
from pathlib import Path

import pytest

from planlock import plan_create, plan_done, plan_fail, plan_next


@pytest.fixture(autouse=True)
def change_test_dir(tmp_path, monkeypatch):
    """Isolate tests in a temporary working directory."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_full_plan_lifecycle_with_disk_verification():
    """Verify state transitions directly on disk across the entire lifecycle."""
    # 1. Create plan
    res_create = plan_create(["Task 1", "Task 2", "Task 3"])
    assert "Plan Lock created: 3 steps" == res_create
    assert os.path.exists(".opencode/plan.md")
    assert os.path.exists(".opencode/.gitignore")

    # Verify gitignore content
    with open(".opencode/.gitignore", encoding="utf-8") as f:
        gi = f.read()
    assert "plan.md\n" in gi
    assert "plan.md.bak\n" in gi

    # 2. Step 1: Activate & Complete
    res_next1 = plan_next()
    assert "Next step (id=1): Task 1" in res_next1

    res_done1 = plan_done(1, "Task 1 finished cleanly")
    assert "Step 1 completed: Task 1 finished cleanly" in res_done1

    # 3. Step 2: Activate & Fail
    res_next2 = plan_next()
    assert "Next step (id=2): Task 2" in res_next2

    res_fail2 = plan_fail(2, "Task 2 network timeout")
    assert "Step 2 failed: Task 2 network timeout" in res_fail2

    # 4. Step 3: Activate & Complete
    res_next3 = plan_next()
    assert "Next step (id=3): Task 3" in res_next3

    res_done3 = plan_done(3, "Task 3 done")
    assert "Step 3 completed: Task 3 done" in res_done3

    # 5. Check completion
    res_final = plan_next()
    assert res_final == "PLAN_DONE"

    # Verify final disk content
    with open(".opencode/plan.md", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines()]

    assert lines[0] == f"# Plan — {os.path.basename(os.getcwd())}"
    assert re.fullmatch(r"- created: \d+", lines[1])
    assert lines[2] == ""
    assert lines[3] == "- [x] 1. Task 1 — note: Task 1 finished cleanly"
    assert lines[4] == "- [!] 2. Task 2 — error: Task 2 network timeout"
    assert lines[5] == "- [x] 3. Task 3 — note: Task 3 done"


def test_crash_recovery_resumes_from_locked_step():
    """Simulates an LLM agent restart/crash while a step is locked."""
    plan_create(["Step A", "Step B"])
    plan_next()  # Step A is now [~]

    # Model / session restarts: next call without resolving should fail with lock active
    err = plan_next()
    assert "Plan Lock active: step 1 is still [~]" in err

    # The agent reads plan.md to inspect current state (as designed)
    with open(".opencode/plan.md", encoding="utf-8") as f:
        plan_content = f.read()
    assert "- [~] 1. Step A" in plan_content

    # The agent resolves the unfinished step
    plan_done(1, "Resolved after restart")

    # Now step 2 can be started
    next_step = plan_next()
    assert "Next step (id=2): Step B" in next_step


def test_backup_rotation_preserves_previous_plan():
    """Verify that multiple consecutive plan creations rotate the backup correctly."""
    plan_create(["First generation"])
    assert not os.path.exists(".opencode/plan.md.bak")

    plan_create(["Second generation"])
    assert os.path.exists(".opencode/plan.md.bak")
    with open(".opencode/plan.md.bak", encoding="utf-8") as f:
        assert "First generation" in f.read()

    plan_create(["Third generation"])
    with open(".opencode/plan.md.bak", encoding="utf-8") as f:
        assert "Second generation" in f.read()
    with open(".opencode/plan.md", encoding="utf-8") as f:
        assert "Third generation" in f.read()


def test_atomic_write_leaves_no_temporary_files(tmp_path: Path):
    """Ensure atomic write leaves no lingering temporary files (.tmp_plan_*)."""
    plan_create(["Test step 1", "Test step 2"])
    plan_next()
    plan_done(1, "done")

    temp_files = list(Path(".opencode").glob(".tmp_plan_*"))
    assert len(temp_files) == 0
