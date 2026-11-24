#!/usr/bin/env bash
#
# test/test.sh — Plan Lock test runner.
#
# Usage:
#   ./test/test.sh                 # run full test suite (lint + all tests)
#   ./test/test.sh --unit          # unit tests only
#   ./test/test.sh --integration   # integration tests only
#   ./test/test.sh --e2e           # end-to-end stdio transport tests only
#   ./test/test.sh --smoke         # smoke & sanity checks only
#   ./test/test.sh --regression    # regression tests only
#   ./test/test.sh --lint          # ruff only, no tests
#   ./test/test.sh --no-install    # skip dependency install step
#   ./test/test.sh --only <target> # run specific test file or test node
#   ./test/test.sh --help          # show help
#

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

RUN_LINT=1
RUN_TESTS=1
INSTALL=1
TARGETS=()

usage() {
    sed -n '3,17p' "$0" | sed 's/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --unit)
            TARGETS+=("test/py/planlock-tests.py" "test/py/test_planlock.py")
            ;;
        --integration)
            TARGETS+=("test/py/integration-tests.py")
            ;;
        --e2e)
            TARGETS+=("test/py/planlock-mcp-tests.py")
            ;;
        --smoke | --sanity)
            TARGETS+=("test/py/smoke-sanity-tests.py")
            ;;
        --regression)
            TARGETS+=("test/py/regression-tests.py")
            ;;
        --lint)
            RUN_TESTS=0
            ;;
        --no-install)
            INSTALL=0
            ;;
        --only)
            shift
            TARGETS+=("${1:-}")
            ;;
        -h | --help)
            usage
            exit 0
            ;;
        *)
            echo "unknown flag: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
    shift
done

if command -v uv >/dev/null 2>&1; then
    PY=(uv run --with pytest --with ruff python)
    INSTALL=0
elif [[ -x "$ROOT/.venv/bin/python" ]]; then
    PY=("$ROOT/.venv/bin/python")
else
    PY=("${PYTHON:-python3}")
fi

if [[ "$INSTALL" == 1 ]]; then
    echo "== install =="
    "${PY[@]}" -m pip install -q -r requirements-dev.txt
fi

if [[ "$RUN_LINT" == 1 ]]; then
    echo "== ruff =="
    "${PY[@]}" -m ruff check .
fi

if [[ "$RUN_TESTS" == 1 ]]; then
    echo "== pytest =="
    if [[ ${#TARGETS[@]} -gt 0 ]]; then
        "${PY[@]}" -m pytest -q "${TARGETS[@]}"
    else
        "${PY[@]}" -m pytest -q
    fi
fi
