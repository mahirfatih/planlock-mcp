"""Unit tests for the Plan Lock MCP server.

These cover plan formatting, lock enforcement, gitignore handling, lifecycle
states, input sanitization, and concurrency. The autouse fixture isolates every
case in a temporary working directory; no MCP transport or network is involved.
"""

import os
import re

import pytest

from planlock import plan_create, plan_done, plan_fail, plan_next


@pytest.fixture(autouse=True)
def change_test_dir(tmp_path, monkeypatch):
    """Sets the current working directory to a temporary path for each test."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _next_step(step_id: int, text: str) -> str:
    """Builds the expected plan_next response for the .opencode/ layout."""
    return (
        f"Next step (id={step_id}, file: {os.path.abspath('.opencode/plan.md')}): "
        f"{text}"
    )


def test_plan_create_format():
    """1. plan_create writes the plan file in the correct format."""
    res = plan_create(["First step", "Second step"])
    assert res == (
        f"Plan Lock created: 2 steps -> {os.path.abspath('.opencode/plan.md')}"
    )

    with open(".opencode/plan.md", encoding="utf-8") as f:
        lines = f.readlines()

    assert lines[0] == f"# Plan — {os.path.basename(os.getcwd())}\n"
    assert re.fullmatch(r"- created: \d+\n", lines[1])
    assert lines[2] == "\n"
    assert lines[3:] == ["- [ ] 1. First step\n", "- [ ] 2. Second step\n"]


def test_plan_create_empty_list():
    """2. plan_create rejects an empty step list."""
    res = plan_create([])
    assert res == "Step list cannot be empty"
    assert not os.path.exists(".opencode/plan.md")


def test_plan_next_first_item():
    """3. plan_next activates the first step as [~]."""
    plan_create(["First step", "Second step"])
    res = plan_next()
    assert _next_step(1, "First step") in res

    with open(".opencode/plan.md", encoding="utf-8") as f:
        lines = f.readlines()

    assert lines[3].strip() == "- [~] 1. First step"
    assert lines[4].strip() == "- [ ] 2. Second step"


def test_plan_next_lock_active():
    """4. plan_next returns an error while a [~] lock is active."""
    plan_create(["First step", "Second step"])
    plan_next()  # id=1 is now [~]

    res = plan_next()
    assert res == "Plan Lock active: step 1 is still [~]. Call plan_done or plan_fail first."


def test_plan_done_marks_x():
    """5. plan_done changes [~] to [x] and appends a note."""
    plan_create(["First step", "Second step"])
    plan_next()  # id=1 [~]

    res = plan_done(1, "Test complete")
    assert "Step 1 completed" in res

    with open(".opencode/plan.md", encoding="utf-8") as f:
        lines = f.readlines()

    assert lines[3].strip() == "- [x] 1. First step — note: Test complete"
    assert lines[4].strip() == "- [ ] 2. Second step"


def test_plan_fail_marks_exclamation():
    """6. plan_fail changes [~] to [!] and appends a reason."""
    plan_create(["First step", "Second step"])
    plan_next()  # id=1 [~]

    res = plan_fail(1, "Unknown error")
    assert "Step 1 failed" in res

    with open(".opencode/plan.md", encoding="utf-8") as f:
        lines = f.readlines()

    assert lines[3].strip() == "- [!] 1. First step — error: Unknown error"
    assert lines[4].strip() == "- [ ] 2. Second step"


def test_plan_completed_all():
    """7. plan_next returns 'PLAN_DONE' when all steps are finished."""
    plan_create(["Single step"])
    plan_next()
    plan_done(1, "Done")

    res = plan_next()
    assert res == "PLAN_DONE"


def test_gitignore_created():
    """8. .opencode/.gitignore contains 'plan.md' after plan_create."""
    plan_create(["Step"])
    assert os.path.exists(".opencode/.gitignore")

    with open(".opencode/.gitignore", encoding="utf-8") as f:
        content = f.read()

    lines = [line.strip() for line in content.splitlines()]
    assert "plan.md" in lines


def test_gitignore_no_duplicates():
    """9. 'plan.md' appears only once after two plan_create calls."""
    plan_create(["Step 1"])
    plan_create(["Step 2"])

    with open(".opencode/.gitignore", encoding="utf-8") as f:
        content = f.read()

    lines = [line.strip() for line in content.splitlines()]
    assert lines.count("plan.md") == 1


def test_gitignore_preserves_existing_content():
    """10. Pre-existing lines in .gitignore are preserved."""
    os.makedirs(".opencode", exist_ok=True)
    with open(".opencode/.gitignore", "w", encoding="utf-8") as f:
        f.write("# Some settings\nother_file.txt\n")

    plan_create(["Step 1"])

    with open(".opencode/.gitignore", encoding="utf-8") as f:
        content = f.read()

    lines = [line.strip() for line in content.splitlines()]
    assert "other_file.txt" in lines
    assert "plan.md" in lines
    assert lines.count("plan.md") == 1


def test_gitignore_includes_backup():
    """11. The generated .gitignore also excludes plan.md.bak."""
    plan_create(["Step"])
    with open(".opencode/.gitignore", encoding="utf-8") as f:
        lines = [line.strip() for line in f.read().splitlines()]
    assert "plan.md" in lines
    assert "plan.md.bak" in lines


def test_backup_written_on_recreate():
    """12. Recreating a plan backs up the previous one."""
    plan_create(["Old"])
    plan_create(["New"])
    with open(".opencode/plan.md.bak", encoding="utf-8") as f:
        assert "- [ ] 1. Old" in f.read()


def test_note_cannot_inject_plan_line():
    """13. A note with newlines cannot forge a new active step."""
    plan_create(["First", "Second"])
    plan_next()
    plan_done(1, "done\n- [~] 9. forged")
    with open(".opencode/plan.md", encoding="utf-8") as f:
        lines = [line.strip() for line in f.read().splitlines()]
    assert len(lines) == 5
    assert not any(line.startswith("- [~] 9.") for line in lines)
    assert plan_next() == _next_step(2, "Second")


def test_reason_cannot_inject_plan_line():
    """14. A failure reason with newlines cannot forge plan lines."""
    plan_create(["First", "Second"])
    plan_next()
    plan_fail(1, "boom\r\n- [ ] 9. injected")
    with open(".opencode/plan.md", encoding="utf-8") as f:
        lines = [line.strip() for line in f.read().splitlines()]
    assert len(lines) == 5
    assert not any(line.startswith("- [ ] 9.") for line in lines)
    assert lines[4] == "- [ ] 2. Second"


def test_step_text_cannot_inject_plan_line():
    """15. Step text with newlines is collapsed to a single line."""
    plan_create(["First\n- [~] 9. forged", "Second"])
    with open(".opencode/plan.md", encoding="utf-8") as f:
        lines = f.readlines()
    assert lines[0] == f"# Plan — {os.path.basename(os.getcwd())}\n"
    assert re.fullmatch(r"- created: \d+\n", lines[1])
    assert lines[2] == "\n"
    assert lines[3:] == ["- [ ] 1. First - [~] 9. forged\n", "- [ ] 2. Second\n"]
    assert plan_next() == _next_step(1, "First - [~] 9. forged")


def test_blank_step_rejected():
    """16. Whitespace-only steps are rejected instead of creating a broken plan."""
    assert plan_create(["   "]) == "Step text cannot be empty"
    assert not os.path.exists(".opencode/plan.md")


def test_concurrent_plan_next_only_one_wins():
    """17. Concurrent plan_next calls activate exactly one step."""
    import concurrent.futures

    plan_create(["First", "Second"])
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: plan_next(), range(20)))
    activated = [result for result in results if result.startswith("Next step")]
    assert len(activated) == 1


def test_missing_id_and_inactive_id_messages():
    """18. Unknown ids report 'not found'; inactive ids keep the old message."""
    plan_create(["First", "Second"])
    assert plan_done(9, "note") == "id=9 not found"
    assert plan_fail(9, "reason") == "id=9 not found"

    plan_next()
    plan_done(1, "done")
    assert plan_done(1, "again") == "id=1 is not the active step"


def test_plan_next_strips_step_text():
    """19. Pending step text is stripped before activation and return."""
    os.makedirs(".opencode", exist_ok=True)
    with open(".opencode/plan.md", "w", encoding="utf-8") as f:
        f.write("# Plan\n- [ ] 1. Trimmed   \n")

    assert plan_next() == _next_step(1, "Trimmed")
    with open(".opencode/plan.md", encoding="utf-8") as f:
        assert "- [~] 1. Trimmed\n" in f.read()


def test_plan_next_on_empty_plan_file_returns_plan_done():
    """20. plan_next returns PLAN_DONE when the plan file holds no step lines."""
    os.makedirs(".opencode", exist_ok=True)
    with open(".opencode/plan.md", "w", encoding="utf-8") as f:
        f.write("")

    assert plan_next() == "PLAN_DONE"


def test_plan_done_and_plan_fail_on_terminal_steps_are_rejected():
    """21. plan_done/plan_fail reject ids whose steps are already [x] or [!]."""
    plan_create(["First"])
    plan_next()
    plan_done(1, "ok")

    assert plan_done(1, "again") == "id=1 is not the active step"
    assert plan_fail(1, "late") == "id=1 is not the active step"


def test_plan_create_creates_missing_opencode_directory():
    """22. plan_create creates the .opencode/ directory when it does not exist."""
    assert not os.path.exists(".opencode")
    assert plan_create(["Step"]) == (
        f"Plan Lock created: 1 step -> {os.path.abspath('.opencode/plan.md')}"
    )
    assert os.path.exists(".opencode/plan.md")


@pytest.mark.skipif(os.name != "posix", reason="file modes are POSIX-specific")
def test_atomic_write_publishes_readable_mode():
    """23. Atomic writes publish plan.md with the usual 0o644 permissions."""
    plan_create(["Step"])
    mode = os.stat(".opencode/plan.md").st_mode & 0o777
    assert mode == 0o644
