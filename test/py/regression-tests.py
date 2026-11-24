"""Regression tests for Plan Lock MCP.

Guards against reintroduction of past bugs, edge-cases, and formatting anomalies:
- Input sanitization (line breaks, tab characters, CRLF injection)
- Multi-threading race conditions on plan_next / plan_done
- Markdown header or formatting preservation
- Unmatched pattern lines or corrupted plan handling
- Unicode and multilingual content support
"""

import concurrent.futures
import os

import pytest

from planlock import plan_create, plan_done, plan_fail, plan_next


@pytest.fixture(autouse=True)
def change_test_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


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
    assert res == "Next step (id=1): Real step"


def test_regression_empty_note_or_reason():
    """Regression: Whitespace-only notes and reasons are cleanly rejected."""
    plan_create(["Step 1"])
    plan_next()
    assert plan_done(1, "   ") == "Note cannot be empty"
    assert plan_fail(1, "   ") == "Reason cannot be empty"
