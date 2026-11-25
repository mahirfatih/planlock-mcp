# Test

Local test runner for Plan Lock MCP. Everything is one command; there is no device
matrix and nothing to install beyond the dev dependencies.

The full strategy — the suite map and the flags — lives in
[`docs/testing/TESTING.md`](../docs/testing/TESTING.md). Commit conventions are
in [`CONTRIBUTING.md`](../CONTRIBUTING.md); the working tour is in the
[README](../README.md#-testing).

## Contents

| Path | Purpose |
| :--- | :--- |
| [`test.sh`](./test.sh) | Test runner: supports `--unit`, `--integration`, `--e2e`, `--smoke`, `--regression`, `--lint`. |
| [`py/test_planlock.py`](./py/test_planlock.py) | 18 core unit tests: format, empty/blank steps, activation, lock, done/fail, gitignore entries, plan header, root vs. `.opencode/` location. |
| [`py/planlock-tests.py`](./py/planlock-tests.py) | 23 unit tests: format, activation, lock, lifecycle, gitignore, backup, injection safety, concurrency, atomic-write mode. |
| [`py/integration-tests.py`](./py/integration-tests.py) | 4 integration tests: full lifecycle disk audit, crash-recovery, multi-generation backup rotation, atomic write cleanup. |
| [`py/smoke-sanity-tests.py`](./py/smoke-sanity-tests.py) | 5 smoke & sanity tests: tool registration, golden path flow, missing plan handling, invalid ID safety, `--version`. |
| [`py/regression-tests.py`](./py/regression-tests.py) | 11 regression tests: CRLF/tab injection, UTF-8/emojis, heavy concurrency locks, foreign plan lines, empty inputs, project-name injection, non-list steps, duplicate ids, fsync ordering, root plan ignored via `.gitignore`, preserved `.gitignore` content. |
| [`py/planlock-mcp-tests.py`](./py/planlock-mcp-tests.py) | 1 E2E test: spawns the server and drives JSON-RPC handshake, `tools/list` and two `tools/call` over STDIO wire. |

## Quick start

```bash
./test/test.sh                                   # deps + ruff + all 62 tests
./test/test.sh --unit                            # unit tests only
./test/test.sh --integration                     # integration tests
./test/test.sh --e2e                             # stdio transport E2E
./test/test.sh --smoke                           # smoke and sanity tests
./test/test.sh --regression                      # regression tests
./test/test.sh --lint                            # ruff only
./test/test.sh --no-install                      # skip the install step
./test/test.sh --only test/py/planlock-tests.py::test_plan_next_lock_active
./test/test.sh --help                            # full flag list
```

A bare `./test/test.sh` is what you run while working and before a commit. The
runner prefers `uv run` when available; otherwise it uses the project `.venv`
or `python3` (override with `PYTHON`). Tests are fully offline and use a fresh
temporary working directory per case, so they never touch a real plan.

## File names

Scripts and data files are kebab-case, and Python test files carry a `-tests`
suffix (for example `planlock-tests.py`). A name fixed by a tool — `pytest.ini`
— keeps its name; it pins `python_files = *-tests.py` so pytest picks up that
suffix instead of the default `test_*.py`.

## Outputs

pytest writes its cache to `.pytest_cache/` (gitignored). Ruff writes to
`.ruff_cache/` (gitignored). The only test-side effect is a temporary
plan file (and its ignore file) under pytest's `tmp_path`, removed with the
temp dir.

## Further reading

- [`docs/testing/TESTING.md`](../docs/testing/TESTING.md) — suite map and flags
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — setup, tests and commit conventions
- [`README.md`](../README.md) — install, tools and the plan format
