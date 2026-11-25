# Contributing

Thanks for your interest in **Plan Lock MCP**. This is a small, dependency-light MCP
server, so the contribution surface is intentionally narrow.

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt   # mcp + pytest + ruff
```

The runtime dependency (`mcp`) alone is enough to run the server; it is pinned
in `requirements.txt`. The project is also installable as a package:

```bash
uv sync                 # or: pip install -e .
planlock                # console script; equivalent to `python3 planlock.py`
```

Optional local git hooks (Ruff + basic hygiene) live in
`.pre-commit-config.yaml`: `pip install pre-commit && pre-commit install`.

## Running the checks

```bash
./test/test.sh                 # Ruff + pytest (installs dev deps first)
./test/test.sh --smoke         # smoke tests
./test/test.sh --sanity        # sanity contract tests
./test/test.sh --unit          # unit tests only
./test/test.sh --regression    # regression tests
./test/test.sh --integration   # integration tests
./test/test.sh --e2e           # stdio transport tests
./test/test.sh --ui            # automated UI contract tests
./test/test.sh --lint          # Ruff only
./test/test.sh --no-install    # skip the pip install step
./test/test.sh --only test/py/planlock-tests.py::test_plan_next_lock_active

Verify the console script after installing: `planlock --version` (prints
`planlock 1.0.0`).
```

The runner and both checks also run in CI (`.github/workflows/ci.yml`). CI is
**manual only** (`workflow_dispatch`) — start it from the Actions tab.

## The server

Everything ships in a single file, `planlock.py`. Keep it that way:

- Standard library only at runtime, apart from the required `mcp` SDK.
- New behaviour belongs in a pure helper (easy to unit-test) with the MCP tool
  acting as a thin wrapper.
- All comments, docstrings, and user-facing tool messages must be written in
  **English**. The messages are asserted by the test suite — do not change them
  casually.
- The plan lives at `.opencode/plan.md` relative to the current working
  directory. Never hardcode absolute paths or write to the home directory.
- Every tool that mutates the plan must hold `_STATE_LOCK` around its entire
  read-modify-write cycle and persist via `_atomic_write`.
- Pass every user-controlled value through `_single_line()` before writing it,
  so a newline cannot inject a forged plan line or bypass the lock.

## Tests

Add core cases to `test/py/core-tests.py`, extended unit cases to
`test/py/planlock-tests.py`, quick health checks to `test/py/smoke-tests.py`,
acceptance-contract checks to `test/py/sanity-tests.py`, bug fixes to
`test/py/regression-tests.py`, multi-call/disk checks to
`test/py/integration-tests.py`, transport cases to
`test/py/planlock-mcp-tests.py`, and user-facing MCP surface cases to
`test/py/ui-tests.py`. All test files live under `test/`. Every shell and
Python file name is kebab-case; test files carry a `-tests.py` suffix,
including the core `core-tests.py`. `pytest.ini` also accepts `test_*.py` for
compatibility. The autouse fixture changes the working directory
to a fresh `tmp_path` for each unit test, and the MCP suites spawn the server
with `cwd=tmp_path`, so no test touches the real `.opencode/` directory. Keep
tests deterministic: no network, no sleeps, and no dependency on wall-clock
time.

Run one test while iterating:

```bash
./test/test.sh --no-install --only test/py/planlock-tests.py::test_concurrent_plan_next_only_one_wins
```

The full test map is in [`docs/testing/TESTING.md`](./docs/testing/TESTING.md).

## Commit conventions

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <short imperative summary>
```

Common types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`. Keep
each commit to one logical change.

## Releasing

A release bumps `version` in `pyproject.toml`, builds with `uv build`, and
publishes with `uv publish`. The checklist is in
[`docs/guides/RELEASING.md`](./docs/guides/RELEASING.md).

## Syncing a local OpenCode install

If you run the server from OpenCode, keep the deployed copy in step with the
repository:

```bash
cp planlock.py ~/.config/opencode/mcp/planlock.py
```

OpenCode reloads MCP servers when configuration changes; run `/reload` in the
TUI if a code-only change does not take effect.
