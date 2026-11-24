# Releasing

Plan Lock MCP is published as a Python package, `planlock-mcp`, with a `planlock`
console script. A release is a version bump plus a tag; nothing else changes
in the source tree.

## 1. Prepare

- Make sure `./test/test.sh --no-install` passes locally.
- Bump `version` in `pyproject.toml` using
  [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
- Add a dated section to [`CHANGELOG.md`](../../CHANGELOG.md) with `Added`,
  `Changed`, `Fixed`, or `Security` subsections as needed.
- Commit as `chore: release vX.Y.Z` and tag as `vX.Y.Z`.

## 2. Build and check locally

```bash
uv build                       # writes dist/planlock_mcp-*.whl and .tar.gz
uv run --with twine twine check dist/*
```

The wheel contains `planlock.py` only; `mcp` is declared as its sole runtime
dependency. The sdist also carries the READMEs, license, changelog, and
contributing guide.

## 3. Publish

```bash
uv publish --index testpypi     # optional dry run against TestPyPI
uv publish                      # PyPI; requires UV_PUBLISH_TOKEN
```

Install from TestPyPI to verify the console script before the real upload:

```bash
uvx --index-url https://test.pypi.org/simple/ --from planlock-mcp planlock
```

## 4. Alternative: release from GitHub

If you do not want to publish to PyPI, tag the commit and let users install
directly from the repository:

```bash
pip install git+https://github.com/<owner>/planlock-mcp.git@vX.Y.Z
```

Replace `<owner>` with the actual repository owner. Update the `[project.urls]`
table in `pyproject.toml` with the real repository URL before publishing.

## 5. After the release

- Confirm the tag points at the release commit.
- Confirm `planlock --help`-style startup does not pollute `stdout` (the server
  speaks MCP over stdio; diagnostics belong on `stderr`).
- Announce the change in the changelog only — do not retrofit old entries.
