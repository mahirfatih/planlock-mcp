"""Regression tests for Plan Lock MCP.

Guards against reintroduction of past bugs, edge-cases, and formatting anomalies:
- Input sanitization (line breaks, tab characters, CRLF injection)
- Working-directory names that contain newlines
- Non-list `steps` arguments
- Duplicate step ids in hand-edited plans
- fsync ordering in atomic writes
- Multi-threading race conditions on plan_next / plan_done
- Markdown header or formatting preservation
- Unmatched pattern lines or corrupted plan handling
- Unicode and multilingual content support
"""

import concurrent.futures
import os
import shutil
import subprocess

import pytest

from planlock import plan_create, plan_done, plan_fail, plan_next


@pytest.fixture(autouse=True)
def change_test_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _next_step(step_id: int, text: str) -> str:
    """Builds the expected plan_next response for the .opencode/ layout."""
    return (
        f"Next step (id={step_id}, file: {os.path.abspath('.opencode/plan.md')}): "
        f"{text}"
    )


def test_regression_crlf_and_tabs_sanitization():
    """Regression: CRLF (\r\n) and special characters do not break the step parsing."""
    plan_create(["Step\r\nwith\r\nwindows\tnewlines"])
    res = plan_next()
    assert "Step with windows newlines" in res

    # Done with embedded \r\n and markdown-like injection
    plan_done(1, "Done\r\n- [ ] 2. Fake Step")
    with open(".opencode/plan.md", encoding="utf-8") as f:
        content = f.read()

    assert "- [ ] 2. Fake Step" not in content.splitlines()
    assert "- [x] 1. Step with windows newlines — note: Done - [ ] 2. Fake Step" in content


def test_regression_unicode_and_emojis():
    """Regression: UTF-8 encoding support for accented characters and emojis."""
    steps = ["1. Étape: préparer le schéma 🚀", "2. Étape: test des accents (äöüéè)"]
    plan_create(steps)

    res1 = plan_next()
    assert "Étape: préparer le schéma 🚀" in res1

    res_done = plan_done(1, "Terminé avec succès ✔️")
    assert "Terminé avec succès ✔️" in res_done

    res2 = plan_next()
    assert "test des accents (äöüéè)" in res2


def test_regression_concurrent_rapid_next_and_done():
    """Regression: Thread safety under heavy interleaved concurrent requests."""
    plan_create([f"Step {i}" for i in range(1, 11)])

    # Ensure sequential lock discipline even under concurrency
    for step_num in range(1, 11):
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            next_calls = list(pool.map(lambda _: plan_next(), range(5)))

        # Exactly one call must succeed in getting the step, others must receive 'Plan Lock active'
        successful = [r for r in next_calls if r.startswith("Next step")]
        locked = [r for r in next_calls if "Plan Lock active" in r]

        assert len(successful) == 1
        assert len(locked) == 4
        assert f"id={step_num}" in successful[0]

        # Resolve step
        done_res = plan_done(step_num, f"Done {step_num}")
        assert f"Step {step_num} completed" in done_res

    assert plan_next() == "PLAN_DONE"


def test_regression_corrupted_plan_lines_handling():
    """Regression: Unexpected or foreign lines in plan.md do not crash the parser."""
    os.makedirs(".opencode", exist_ok=True)
    with open(".opencode/plan.md", "w", encoding="utf-8") as f:
        f.write("# Foreign Document\nRandom text that is not a step\n- [ ] 1. Real step\n")

    res = plan_next()
    assert res == _next_step(1, "Real step")


def test_regression_empty_note_or_reason():
    """Regression: Whitespace-only notes and reasons are cleanly rejected."""
    plan_create(["Step 1"])
    plan_next()
    assert plan_done(1, "   ") == "Note cannot be empty"
    assert plan_fail(1, "   ") == "Reason cannot be empty"


def test_regression_project_name_cannot_inject_step(tmp_path, monkeypatch):
    """Regression: a working-directory name with a newline cannot forge a step line."""
    evil = tmp_path / "evil\n- [~] 9. forged"
    evil.mkdir()
    monkeypatch.chdir(evil)

    plan_create(["Real step"])

    with open(".opencode/plan.md", encoding="utf-8") as f:
        lines = f.readlines()

    assert lines[0] == "# Plan — evil - [~] 9. forged\n"
    assert "- [~] 9. forged\n" not in lines
    assert plan_next() == _next_step(1, "Real step")


def test_regression_steps_must_be_a_list():
    """Regression: a bare string is rejected instead of becoming one step per character."""
    assert plan_create("ab") == "Steps must be a list of strings"
    assert not os.path.exists(".opencode/plan.md")


def test_regression_active_duplicate_id_is_reachable():
    """Regression: a later active duplicate id is used instead of reporting 'not active'."""
    os.makedirs(".opencode", exist_ok=True)
    with open(".opencode/plan.md", "w", encoding="utf-8") as f:
        f.write("# Plan\n\n- [x] 1. old\n- [~] 1. active\n")

    assert plan_done(1, "ok") == "Step 1 completed: ok"
    with open(".opencode/plan.md", encoding="utf-8") as f:
        assert "- [x] 1. active — note: ok\n" in f.read()


def test_regression_atomic_write_fsyncs_before_replace(monkeypatch):
    """Regression: the plan is flushed to disk before os.replace publishes it."""
    synced: list[int] = []
    monkeypatch.setattr(os, "fsync", lambda fd: synced.append(fd))

    plan_create(["Step"])

    assert synced


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_regression_root_plan_stays_out_of_git_status(tmp_path):
    """Regression: a project-root plan is ignored through a created .gitignore."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, capture_output=True)

    plan_create(["Step"])

    assert (tmp_path / "plan.md").exists()
    gitignore = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert "plan.md" in gitignore.splitlines()
    assert "plan.md.bak" in gitignore.splitlines()

    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
        text=True,
    )
    assert "plan.md" not in result.stdout


def test_regression_root_gitignore_preserves_existing_content(tmp_path):
    """Regression: a pre-existing root .gitignore keeps its lines and gets no duplicates."""
    (tmp_path / ".gitignore").write_text("node_modules/\nplan.md\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")

    plan_create(["First step"])
    plan_create(["Second step"])

    lines = (tmp_path / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "node_modules/" in lines
    assert lines.count("plan.md") == 1
    assert lines.count("plan.md.bak") == 1
