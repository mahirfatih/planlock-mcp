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
- Added `examples/plan.md`: a real, completed plan from the `media-studio`
  3-column layout work, normalized to the exact format `plan_create` writes.
  Linked from `README.md`, `README.tr.md` and `docs/README.md`.
- Named the motivating failure mode in both READMEs: parallel tool calling,
  uncoordinated fan-out / tool call flooding, fan-out or scattergun editing,
  and the resulting context or state thrashing.
- Added badge lines (Python, MCP-stdio, License) at the top of `README.md` and
  `README.tr.md`, adapted from `omlx-prompt-shrink/README.md` (no PyPI badge:
  `planlock-mcp` is not published there).
- Added `[project.urls]` metadata to `pyproject.toml` (Homepage, Repository,
  Issues, Changelog) and a `__version__` constant plus a `--version` flag to
  `planlock.py`, so `planlock --version` verifies an install.
- Added an empty `py.typed` marker (PEP 561) so type checkers treat the
  package as typed; included in both the wheel and the sdist.
- Added a `--version` smoke test and documented the flag in `README.md` and
  `CONTRIBUTING.md`.
- Regression tests for a working-directory name containing a newline, a bare
  string `steps` argument, a duplicated step id, fsync ordering in atomic
  writes, and the generated `.opencode/` staying out of `git status`.

### Fixed

- `plan_create` sanitizes the project name taken from the working-directory
  basename with `_single_line`, so a directory name containing a newline can no
  longer inject a forged `- [~]` line and hijack the lock.
- `plan_create` rejects a bare `str`/`bytes` `steps` argument with
  `Steps must be a list of strings`; previously it silently created one step per
  character.
- `plan_done` and `plan_fail` share a `_locate_step` helper that prefers an
  active `[~]` line over an earlier terminal line with the same id, so a
  hand-edited duplicate id no longer blocks releasing the lock.
- `_atomic_write` flushes and fsyncs the temporary file and the target
  directory, so the documented crash safety also holds for power loss.
- `.opencode/.gitignore` now also ignores itself, so a freshly generated
  `.opencode/` directory no longer appears as untracked in `git status`.

### Changed

- The plan now lives at `<cwd>/plan.md` when the working directory contains a
  project marker (`.git`, `pyproject.toml`, `package.json`, `Cargo.toml`, or
  `go.mod`). Other directories keep using `<cwd>/.opencode/plan.md`.
- `plan_create` appends `plan.md` and `plan.md.bak` to the working directory
  `.gitignore`, creating the file when it is missing. The `.opencode/` layout
  keeps using `.opencode/.gitignore`.
- `plan_create` now returns the absolute path of the plan file, for example
  `Plan Lock created: 2 steps -> /home/user/project/plan.md`, so the model
  never has to search for the active file.
- `plan_next` also reports that path in its response:
  `Next step (id=1, file: /home/user/project/plan.md): <text>`.
- `_atomic_write` now sets mode `0o644` on the published file; previously the
  restrictive `mkstemp` default (`0o600`) was inherited.
- Replaced Turkish test fixtures in `regression-tests.py` with French/German
  accented + emoji data so Python files contain no Turkish text.
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
