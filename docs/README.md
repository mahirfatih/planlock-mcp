# Documentation

A map of the documents in this repository. The top-level
[`README.md`](../README.md) is the quick tour; start here when you want the
detail behind a tool, a test run, or a release. Each folder answers one
question — read the one that matches what you are doing.

Everything in `docs/` is written in **English**. The Turkish quick tour is
[`README.tr.md`](../README.tr.md) at the repository root.

## How the folders are organised

| Folder | The question it answers | Written or generated |
| :--- | :--- | :--- |
| [`guides/`](./guides) | How do I cut a release | written |
| [`testing/`](./testing) | How do I verify the server | written |

## Start here

- [`../README.md`](../README.md) — install, the four tools and the plan format.
- [`../README.tr.md`](../README.tr.md) — the same tour in Turkish.
- [`../examples/plan.md`](../examples/plan.md) — a real completed plan in the
  exact format the server writes.

## Guides — how do I work on it

- [`guides/RELEASING.md`](./guides/RELEASING.md) — version bump, `uv build`, the
  TestPyPI/PyPI publish and the from-GitHub alternative.

## Testing — how do I verify it

- [`testing/TESTING.md`](./testing/TESTING.md) — the seven test categories (Smoke,
  Sanity, Unit, Regression, Integration, E2E, UI), the runner flags, and how to
  add a new case.

## Also at the repository root

- [`../CONTRIBUTING.md`](../CONTRIBUTING.md) — development setup, coding rules
  and commit conventions.
- [`../CHANGELOG.md`](../CHANGELOG.md) — release notes.
- [`../SECURITY.md`](../SECURITY.md) — vulnerability reporting policy.
- [`../LICENSE`](../LICENSE) — MIT license.
