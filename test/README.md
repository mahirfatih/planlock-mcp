# Test

Local test runner for Plan Lock MCP. Everything is one command; there is no device
matrix and nothing to install beyond the dev dependencies.

The full strategy — the category map and the flags — lives in
[`docs/testing/TESTING.md`](../docs/testing/TESTING.md). Commit conventions are
in [`CONTRIBUTING.md`](../CONTRIBUTING.md); the working tour is in the
[README](../README.md).

## Contents

| Path | Purpose |
| :--- | :--- |
| [`test.sh`](./test.sh) | Runner: supports `--smoke`, `--sanity`, `--unit`, `--regression`, `--integration`, `--e2e`, `--ui`, `--lint`. |
| [`py/smoke-tests.py`](./py/smoke-tests.py) | 4 smoke tests: source compile, tool registration, golden path, `--version`. |
| [`py/sanity-tests.py`](./py/sanity-tests.py) | 5 sanity tests: missing plan, invalid IDs, exact response strings, header contract, both plan locations. |
| [`py/core-tests.py`](./py/core-tests.py) | 18 core unit tests: format, empty/blank steps, activation, lock, done/fail, gitignore entries, plan header, root vs. `.opencode/` location. |
| [`py/planlock-tests.py`](./py/planlock-tests.py) | 23 unit tests: format, activation, lock, lifecycle, gitignore, backup, injection safety, concurrency, atomic-write mode. |
| [`py/integration-tests.py`](./py/integration-tests.py) | 4 integration tests: full lifecycle disk audit, crash-recovery, multi-generation backup rotation, atomic write cleanup. |
| [`py/regression-tests.py`](./py/regression-tests.py) | 11 regression tests: CRLF/tab injection, UTF-8/emojis, heavy concurrency locks, foreign plan lines, empty inputs, project-name injection, non-list steps, duplicate ids, fsync ordering, root plan ignored via `.gitignore`, preserved `.gitignore` content. |
| [`py/planlock-mcp-tests.py`](./py/planlock-mcp-tests.py) | 1 E2E test: spawns the server and drives JSON-RPC handshake, `tools/list` and two `tools/call` over the STDIO wire. |
| [`py/ui-tests.py`](./py/ui-tests.py) | 4 automated UI tests: tool catalog and the exact tool messages rendered to an MCP client over STDIO. |

## Category map

| Category | Flag | File(s) | Scope |
| :--- | :--- | :--- | :--- |
| 💨 Smoke | `--smoke` | [`smoke-tests.py`](./py/smoke-tests.py) | Compile, import, register tools, golden path, `--version`. |
| ✅ Sanity | `--sanity` | [`sanity-tests.py`](./py/sanity-tests.py) | Minimum acceptance contract: messages, header, plan locations. |
| 🔬 Unit | `--unit` | [`core-tests.py`](./py/core-tests.py), [`planlock-tests.py`](./py/planlock-tests.py) | Function behaviour with a temporary working directory. |
| 🩹 Regression | `--regression` | [`regression-tests.py`](./py/regression-tests.py) | Fixed bugs and injection/race edge cases. |
| 🔗 Integration | `--integration` | [`integration-tests.py`](./py/integration-tests.py) | Multi-call flows verified on disk. |
| 🎯 E2E | `--e2e` | [`planlock-mcp-tests.py`](./py/planlock-mcp-tests.py) | Real STDIO transport: handshake, listing, tool calls. |
| 🖥️ UI | `--ui` | [`ui-tests.py`](./py/ui-tests.py) | User-facing MCP surface; no GUI exists for a stdio-only server. |

## Quick start

```bash
./test/test.sh                                   # deps + ruff + all 70 tests
./test/test.sh --smoke                           # smoke tests
./test/test.sh --sanity                          # sanity contract tests
./test/test.sh --unit                            # unit tests
./test/test.sh --regression                      # regression tests
./test/test.sh --integration                     # integration tests
./test/test.sh --e2e                             # stdio transport E2E
./test/test.sh --ui                              # automated UI contract
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

All shell and Python file names are kebab-case, including `test.sh` and
`core-tests.py`. Python test files carry a `-tests` suffix (for example
`sanity-tests.py`). A name fixed by a tool — `pytest.ini` — keeps its name; its
`python_files` pattern still accepts `test_*.py` for compatibility, while every
current suite uses `*-tests.py`.

## Outputs

pytest writes its cache to `.pytest_cache/` (gitignored). Ruff writes to
`.ruff_cache/` (gitignored). The only test-side effect is a temporary
plan file (and its ignore file) under pytest's `tmp_path`, removed with the
temp dir.

## Further reading

- [`docs/testing/TESTING.md`](../docs/testing/TESTING.md) — category map and flags
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — setup, tests and commit conventions
- [`README.md`](../README.md) — install, tools and the plan format
