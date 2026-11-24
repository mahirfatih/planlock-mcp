# Testing

The suite has 47 deterministic cases and needs no network access. Every test
file lives under `test/py/`.

## Running the suite

```bash
./test/test.sh                 # Ruff + pytest (all tests)
./test/test.sh --unit          # Unit tests
./test/test.sh --integration   # Integration tests
./test/test.sh --e2e           # E2E stdio transport tests
./test/test.sh --smoke         # Smoke & Sanity tests
./test/test.sh --regression    # Regression tests
./test/test.sh --lint          # Ruff only
./test/test.sh --no-install    # skip pip install (uv or an existing .venv)
./test/test.sh --only test/py/test_planlock.py::test_plan_create_empty_list
```

Without the runner:

```bash
uv run --with pytest --with ruff pytest -q
python3 -m pytest -q                      # when the .venv already has the deps
```

`pytest.ini` pins `testpaths = test`, `python_files = test_*.py *-tests.py` and
`pythonpath = .`, so every file under `test/` is collected and
`import planlock` resolves to the server at the repository root.

## Layout

| Path | Purpose |
| :--- | :--- |
| [`test.sh`](../../test/test.sh) | Runner: install (or `uv`), Ruff, then pytest. |
| [`py/test_planlock.py`](../../test/py/test_planlock.py) | 14 core tests: format, empty/blank steps, activation, lock, done/fail, completion, gitignore entries, duplicates and plan header. |
| [`py/planlock-tests.py`](../../test/py/planlock-tests.py) | 19 extended unit tests: backup, injection safety, concurrency, id messages. |
| [`py/integration-tests.py`](../../test/py/integration-tests.py) | 4 integration tests: full lifecycle disk audit, crash recovery, backup rotation, atomic write cleanup. |
| [`py/regression-tests.py`](../../test/py/regression-tests.py) | 5 regression tests: CRLF/tab injection, UTF-8/emojis, heavy concurrency, foreign plan lines, empty inputs. |
| [`py/smoke-sanity-tests.py`](../../test/py/smoke-sanity-tests.py) | 4 smoke & sanity tests: tool registration, golden path, missing plan, invalid IDs. |
| [`py/planlock-mcp-tests.py`](../../test/py/planlock-mcp-tests.py) | End-to-end test over the real stdio transport: handshake, `tools/list`, two `tools/call`. |

## Isolation

Both unit files use an autouse fixture with `monkeypatch.chdir(tmp_path)`, so
each case gets a fresh working directory that pytest restores on teardown. The
MCP suite spawns the server with `cwd=tmp_path`. No case touches a real plan in
the repository.

## What is covered

| Area | Cases |
| :--- | :--- |
| Plan creation | format, empty list, blank step rejection, project/timestamp header |
| Lock enforcement | first activation, active lock, concurrent activation |
| Lifecycle | `[~]` → `[x]` with note, `[~]` → `[!]` with reason, `PLAN_DONE` |
| Gitignore | creation, no duplicates, preserved content, backup entry |
| Backup | old plan written to `plan.md.bak` on recreate |
| Injection safety | newline in step text, note, and failure reason |
| MCP transport | stdio handshake, tool listing, `plan_create` + `plan_next` calls |
| Integration | full lifecycle on disk, crash recovery, backup rotation, atomic write cleanup |
| Regression | CRLF/tab injection, UTF-8/emojis, heavy concurrency, malformed lines, empty inputs |
| Smoke & sanity | tool registration, golden path, missing plan, invalid IDs |

## Adding a test

1. Add `test_<behaviour>` to `test/py/test_planlock.py` for a core case,
   `test/py/planlock-tests.py` for an extended unit case,
   `test/py/integration-tests.py` for multi-call/disk behaviour,
   `test/py/regression-tests.py` for a fixed bug, `test/py/smoke-sanity-tests.py`
   for a quick health check, or `test/py/planlock-mcp-tests.py` if it crosses the
   stdio boundary.
2. Give it a one-line English docstring describing the assertion.
3. Rely on the temporary working directory — never hardcode a path.
4. Assert on both the tool's return message and the resulting file content.
5. Keep it deterministic: no network, no sleeps, no wall-clock dependence.

If you change a user-facing message, update the matching assertions in the
same commit — those strings are part of the tool's contract.
