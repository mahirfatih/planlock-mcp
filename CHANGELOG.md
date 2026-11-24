# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-11-24

### Added

- `plan_create`, `plan_next`, `plan_done`, and `plan_fail` tools that enforce a
  strict one-step-at-a-time lock over `.opencode/plan.md`.
- Automatic backup of an existing plan to `.opencode/plan.md.bak` on recreate.
- Automatic creation/update of `.opencode/.gitignore` covering both `plan.md`
  and `plan.md.bak`.
- Atomic writes via `tempfile.mkstemp` + `os.replace`, with no in-memory plan
  state between tool calls.
- A plan header recording the project name (working-directory basename) and a
  unix creation timestamp.
- Input sanitization: step text, completion notes, and failure reasons are
  collapsed to a single line so they cannot inject plan lines.
- `_STATE_LOCK` serialization of read-modify-write cycles, so concurrent tool
  calls cannot both activate the same step.
- A root `.gitignore` for caches, virtual environments, secrets, and SAGE
  runtime state.
- Installable package (`pyproject.toml`) with a `planlock` console script.
- `README.tr.md`, `CONTRIBUTING.md`, this changelog, and a `docs/` tree.
- `test/test.sh` runner, Ruff configuration, pre-commit hooks, and a manually
  dispatched CI workflow.
- 47 deterministic pytest cases covering formatting, lock enforcement,
  gitignore handling, lifecycle states, input injection, concurrency, the real
  MCP stdio transport, crash recovery, atomic writes, and regression cases. The
  14 core cases are in `test/py/test_planlock.py`.
- A `test/` folder with a single runner, `test/test.sh`, and six suites under
  `test/py/`: `test_planlock.py` (14 core), `planlock-tests.py` (19 unit),
  `integration-tests.py` (4), `regression-tests.py` (5),
  `smoke-sanity-tests.py` (4), and `planlock-mcp-tests.py` (1 stdio e2e).

### Changed

- All Python comments, docstrings, and user-facing tool messages are written in
  English; the test suite asserts those messages.
- The test suite follows the `test/py/*-tests.py` convention used by the
  companion Context Shrink project, with `pytest.ini` pinning the suffix.
