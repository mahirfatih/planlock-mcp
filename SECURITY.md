# Security

This document describes how security reports are handled for `planlock-mcp` and
the scope of what the maintainers consider a vulnerability.

## Reporting a vulnerability

Report through the private security channel:

- **GitHub Security tab**: submit a private security advisory at
  [github.com/mahirfatih/planlock-mcp/security](https://github.com/mahirfatih/planlock-mcp/security)

Please do not open a public GitHub issue about a suspected vulnerability. The
private channel lets us assess the report, develop a fix, and coordinate
disclosure with the reporter.

## Handling reports

- **Acknowledgment:** we aim to acknowledge a new report within 5 business days.
- **Triage:** a first assessment is done within 10 business days; we may ask for
  details or reproduction steps.
- **Fix window:** critical and high findings should have a fix or mitigation
  within 30 days of triage; low and informational findings are addressed in
  normal maintenance cycles.
- **Disclosure:** we prefer to disclose through the same channel as the report.
  Public disclosure happens only after the fix is available unless a reporter
  asks for an earlier date. Reporters are credited in the advisory when they
  wish.

## Scope

In scope — please report these if found:

- The `planlock.py` server and its runtime behaviour: the `.opencode/plan.md`
  and `.opencode/plan.md.bak` files it reads and writes, the atomic write path
  (`tempfile.mkstemp` + `os.replace`), `_STATE_LOCK` serialization, and the
  stdio transport between the client and the server.
- Packaging and build configuration (`pyproject.toml`, `hatch` settings,
  `requirements*.txt`).

Out of scope:

- Bugs in the coding agents or LLMs the plan lock is used with (OpenCode,
  Claude Code, ...). Those belong to their respective maintainers.
- Anything about the plan lock itself beyond the code and file formats above:
  it enforces step ordering, not an authorization boundary. It is a
  discipline layer, not a security control, and is not intended as one.
- Issues with local machine state outside the working directory the server
  runs in; the server reads and writes only within its working directory.
- Self-declared "vulnerabilities" in the plan format or the lock messages.

## Coordinated disclosure

When we fix a reported issue we may release a new version, e.g. `1.0.1` or
`1.1.0`. Fixes are described in `CHANGELOG.md` without revealing private
details.
