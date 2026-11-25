# Testing

The suite has 70 deterministic cases and needs no network access. Every test
file lives under `test/py/`, and all shell and Python file names are
kebab-case.

## Running the suite

```bash
./test/test.sh                 # Ruff + pytest (all tests)
./test/test.sh --smoke         # Smoke
./test/test.sh --sanity        # Sanity
./test/test.sh --unit          # Unit
./test/test.sh --regression    # Regression
./test/test.sh --integration   # Integration
./test/test.sh --e2e           # End-to-end stdio transport
./test/test.sh --ui            # Automated UI contract
./test/test.sh --lint          # Ruff only
./test/test.sh --no-install    # skip pip install (uv or an existing .venv)
./test/test.sh --only test/py/core-tests.py::test_plan_create_empty_list
```

Without the runner:

```bash
uv run --with pytest --with ruff pytest -q
python3 -m pytest -q                      # when the .venv already has the deps
```

`pytest.ini` pins `testpaths = test`, `python_files = test_*.py *-tests.py` and
`pythonpath = .`, so every file under `test/` is collected and
`import planlock` resolves to the server at the repository root. The `ui`
marker is registered for the automated UI suite.

## Category map

The seven categories follow the same layered model as
`check-opencode-free-models`: fast safety net first, then contract checks,
logic, fixed bugs, component integration, the real transport, and finally the
user-facing surface.

| Category | Flag | File(s) | Scope |
| :--- | :--- | :--- | :--- |
| 💨 Smoke | `--smoke` | [`smoke-tests.py`](../../test/py/smoke-tests.py) | Compile, module load, tool registration, golden path, `--version`. |
| ✅ Sanity | `--sanity` | [`sanity-tests.py`](../../test/py/sanity-tests.py) | Exact response strings, header format, both plan locations. |
| 🔬 Unit | `--unit` | [`core-tests.py`](../../test/py/core-tests.py), [`planlock-tests.py`](../../test/py/planlock-tests.py) | Pure tool behaviour in a temporary working directory. |
| 🩹 Regression | `--regression` | [`regression-tests.py`](../../test/py/regression-tests.py) | Injection, concurrency, fsync and hand-edited-plan fixes. |
| 🔗 Integration | `--integration` | [`integration-tests.py`](../../test/py/integration-tests.py) | Multi-call flows with disk verification and crash recovery. |
| 🎯 E2E | `--e2e` | [`planlock-mcp-tests.py`](../../test/py/planlock-mcp-tests.py) | Real stdio transport: handshake, `tools/list`, `tools/call`. |
| 🖥️ UI | `--ui` | [`ui-tests.py`](../../test/py/ui-tests.py) | Tool catalog and rendered messages an MCP client sees. |

A stdio-only MCP server has no GUI. The UI category therefore covers its
actual user interface — the MCP client surface and the exact text returned by
tool calls — rather than pixels or window state.

## Layout

| Path | Purpose |
| :--- | :--- |
| [`test.sh`](../../test/test.sh) | Runner: install (or `uv`), Ruff, then pytest, with one flag per category. |
| [`py/smoke-tests.py`](../../test/py/smoke-tests.py) | 4 smoke tests: source compile, server instance and tool registration, golden path, `--version`. |
| [`py/sanity-tests.py`](../../test/py/sanity-tests.py) | 5 sanity tests: missing plan, invalid ids, full response-string contract, header contract, root vs. `.opencode/` location. |
| [`py/core-tests.py`](../../test/py/core-tests.py) | 18 core unit tests: format, empty/blank steps, activation, lock, done/fail, completion, gitignore entries, duplicates, plan header, and both plan locations. |
| [`py/planlock-tests.py`](../../test/py/planlock-tests.py) | 23 extended unit tests: backup, injection safety, concurrency, id messages, empty plan, terminal steps, atomic-write mode. |
| [`py/integration-tests.py`](../../test/py/integration-tests.py) | 4 integration tests: full lifecycle disk audit, crash recovery, backup rotation, atomic write cleanup. |
| [`py/regression-tests.py`](../../test/py/regression-tests.py) | 11 regression tests: CRLF/tab injection, UTF-8/emojis, heavy concurrency, foreign plan lines, empty inputs, project-name injection, non-list steps, duplicate ids, fsync ordering, root plan ignored via `.gitignore`, and preserved `.gitignore` content. |
| [`py/planlock-mcp-tests.py`](../../test/py/planlock-mcp-tests.py) | End-to-end test over the real stdio transport: handshake, `tools/list`, two `tools/call`. |
| [`py/ui-tests.py`](../../test/py/ui-tests.py) | 4 automated UI tests: tool catalog, create/next, done/fail/completion, and error messages rendered over real JSON-RPC. |

## Isolation

The unit, smoke, sanity, integration and regression files use an autouse fixture
with `monkeypatch.chdir(tmp_path)`, so each case gets a fresh working directory
that pytest restores on teardown. The E2E and UI suites spawn the server with
`cwd=tmp_path`. No case touches a real plan in the repository.

## What is covered

| Area | Cases |
| :--- | :--- |
| Plan creation | format, empty list, blank step rejection, non-list rejection, project/timestamp header, missing `.opencode/` directory, root vs. `.opencode/` location, absolute path in the response |
| Lock enforcement | first activation, active lock, concurrent activation |
| Lifecycle | `[~]` → `[x]` with note, `[~]` → `[!]` with reason, `PLAN_DONE`, terminal-step rejection, duplicate-id recovery |
| Gitignore | creation, no duplicates, preserved content, backup entry, self-ignore, root `.gitignore` created when missing |
| Backup | old plan written to `plan.md.bak` on recreate |
| Injection safety | newline in step text, note, failure reason, and working-directory name |
| Durability | fsync of the temp file before `os.replace`, `0o644` published mode, no leftover temp files |
| MCP transport | stdio handshake, tool listing, `plan_create` + `plan_next` calls |
| Integration | full lifecycle on disk, crash recovery, backup rotation, atomic write cleanup |
| Regression | CRLF/tab injection, UTF-8/emojis, heavy concurrency, malformed lines, empty inputs, root plan ignored via `.gitignore` |
| Smoke | source compile, module load, tool registration, golden path, `--version` |
| Sanity | exact tool messages, header contract, project-root and `.opencode/` plan locations |
| UI | tool catalog and the rendered create/next/done/fail/error messages over stdio |

## Adding a test

1. Add the case to the most specific category:
   `test/py/core-tests.py` for a core unit case,
   `test/py/planlock-tests.py` for an extended unit case,
   `test/py/smoke-tests.py` for a fast health check,
   `test/py/sanity-tests.py` for an acceptance-contract check,
   `test/py/regression-tests.py` for a fixed bug,
   `test/py/integration-tests.py` for multi-call/disk behaviour,
   `test/py/planlock-mcp-tests.py` for a transport case, or
   `test/py/ui-tests.py` for a user-facing MCP surface case.
2. Give it a one-line English docstring describing the assertion.
3. Rely on the temporary working directory — never hardcode a path.
4. Assert on both the tool's return message and the resulting file content.
5. Keep it deterministic: no network, no sleeps, no wall-clock dependence.

If you change a user-facing message, update the matching assertions in the
same commit — those strings are part of the tool's contract.
