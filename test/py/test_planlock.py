"""Tests for planlock.py.

Every test runs in a fresh temporary working directory. ``monkeypatch.chdir``
restores the original cwd automatically during fixture teardown, so the cases
are independent of each other and of the repository.
"""

import os
import re

import pytest

from planlock import plan_create, plan_done, plan_fail, plan_next


@pytest.fixture(autouse=True)
def isolated_cwd(tmp_path, monkeypatch):
    """Switch to a clean temporary cwd before each test and restore it after."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_plan_create_writes_plan_file():
    """1. plan_create creates plan.md with numbered pending steps."""
    plan_create(["First step", "Second step"])

    assert os.path.exists(".opencode/plan.md")
    with open(".opencode/plan.md", encoding="utf-8") as f:
        content = f.read()
    assert "- [ ] 1. " in content
    assert "- [ ] 2. " in content


def test_plan_create_empty_list():
    """2. plan_create rejects an empty step list."""
    assert plan_create([]) == "Step list cannot be empty"
    assert not os.path.exists(".opencode/plan.md")


def test_plan_create_blank_step():
    """3. plan_create rejects a list containing a blank step."""
    assert plan_create(["Valid step", "   "]) == "Step text cannot be empty"
    assert not os.path.exists(".opencode/plan.md")


def test_plan_next_activates_first_step():
    """4. plan_next activates the first step and returns its id and text."""
    plan_create(["First step", "Second step"])

    result = plan_next()
    assert "id=1" in result
    assert "First step" in result

    with open(".opencode/plan.md", encoding="utf-8") as f:
        lines = f.readlines()
    assert lines[3].strip() == "- [~] 1. First step"
    assert lines[4].strip() == "- [ ] 2. Second step"


def test_plan_next_lock_active():
    """5. plan_next refuses to open another step while one is active."""
    plan_create(["First step", "Second step"])
    plan_next()

    assert "Plan Lock active" in plan_next()


def test_plan_done_marks_completed():
    """6. plan_done marks the active step [x] and appends a note."""
    plan_create(["First step"])
    plan_next()

    plan_done(1, "Test complete")
    with open(".opencode/plan.md", encoding="utf-8") as f:
        content = f.read()
    assert "- [x] 1. " in content
    assert " — note: " in content


def test_plan_done_wrong_id():
    """7. plan_done rejects an id that is not the active step."""
    plan_create(["First step", "Second step"])
    plan_next()

    assert plan_done(2, "not") == "id=2 is not the active step"


def test_plan_fail_marks_failed():
    """8. plan_fail marks the active step [!] and appends a reason."""
    plan_create(["First step"])
    plan_next()

    plan_fail(1, "Unknown error")
    with open(".opencode/plan.md", encoding="utf-8") as f:
        content = f.read()
    assert "- [!] 1. " in content
    assert " — error: " in content


def test_plan_completed_all():
    """9. plan_next returns PLAN_DONE once every step is finished."""
    plan_create(["Single step"])
    plan_next()
    plan_done(1, "Done")

    assert plan_next() == "PLAN_DONE"


def test_gitignore_created():
    """10. plan_create adds both plan.md and plan.md.bak to .opencode/.gitignore."""
    plan_create(["Step"])

    with open(".opencode/.gitignore", encoding="utf-8") as f:
        lines = [line.strip() for line in f.read().splitlines()]
    assert "plan.md" in lines
    assert "plan.md.bak" in lines


def test_gitignore_no_duplicates():
    """11. Recreating a plan does not duplicate gitignore entries."""
    plan_create(["Step 1"])
    plan_create(["Step 2"])

    with open(".opencode/.gitignore", encoding="utf-8") as f:
        lines = [line.strip() for line in f.read().splitlines()]
    assert lines.count("plan.md") == 1
    assert lines.count("plan.md.bak") == 1


def test_gitignore_preserves_existing_content():
    """12. Existing lines in .opencode/.gitignore are preserved."""
    os.makedirs(".opencode", exist_ok=True)
    with open(".opencode/.gitignore", "w", encoding="utf-8") as f:
        f.write("# Some settings\nother_file.txt\n")

    plan_create(["Step"])

    with open(".opencode/.gitignore", encoding="utf-8") as f:
        lines = [line.strip() for line in f.read().splitlines()]
    assert "other_file.txt" in lines
    assert lines.count("plan.md") == 1
    assert lines.count("plan.md.bak") == 1


def test_plan_header_records_project_and_timestamp():
    """13. The plan header stores the project name and a unix creation timestamp."""
    plan_create(["First step"])

    with open(".opencode/plan.md", encoding="utf-8") as f:
        lines = f.readlines()
    assert lines[0].startswith("# Plan — ")
    assert re.fullmatch(r"- created: \d+\n", lines[1])


def test_plan_header_uses_working_directory_basename():
    """14. The project name in the header equals the current directory basename."""
    plan_create(["First step"])

    with open(".opencode/plan.md", encoding="utf-8") as f:
        header = f.readline().strip()
    assert header == f"# Plan — {os.path.basename(os.getcwd())}"
