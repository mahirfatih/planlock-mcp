# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- CI now runs on every push to `main` and on pull requests, not only manual dispatch.
- Root `.gitignore` ignores `.opencode/.tmp_plan_*` so files left by an interrupted
  atomic write are never committed.
- New unit tests: `plan_next` on an empty plan file returns `PLAN_DONE`,
  `plan_done`/`plan_fail` reject terminal steps, `plan_create` creates a missing
  `.opencode/` directory, and atomic writes publish `plan.md` with mode `0o644`.
- Added `SECURITY.md` with the vulnerability reporting policy: private channel
  via the GitHub Security tab, response timelines, and in-scope/out-of-scope items.
- Added badge lines (Python, MCP-stdio, License) at the top of `README.md` and
  `README.tr.md`, adapted from `omlx-prompt-shrink/README.md` (no PyPI badge:
  `planlock-mcp` is not published there).
- Added `[project.urls]` metadata to `pyproject.toml` (Homepage, Repository,
  Issues, Changelog) and a `__version__` constant plus a `--version` flag to
  `planlock.py`, so `planlock --version` verifies an install.

### Changed

- `_atomic_write` now sets mode `0o644` on the published file; previously the
  restrictive `mkstemp` default (`0o600`) was inherited.
- `actions/checkout` bumped to `v7.0.1` and `actions/setup-python` to `v7.1.0`
  (latest as of 2026-11-24).

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
