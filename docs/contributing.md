# Contributor and release guide

[Documentation index](index.md)

The root [contribution policy](../CONTRIBUTING.md), [release process](../RELEASE.md),
and [security policy](../SECURITY.md) remain the authoritative project policies.

## Development setup

From the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

CI runs the test/lint/type checks on Python 3.12 and 3.13. The `dev` extra includes
pytest, HTTPX, Ruff, Pyright, build, and Twine. Avoid committing virtual environments,
local database files, build artifacts, or secrets.

## Repository map

| Path | Responsibility |
| --- | --- |
| `fapilot/cli.py` | CLI and scaffold templates |
| `fapilot/architectures.py` | Architecture slugs, folders, and guidance |
| `fapilot/core/application.py` | Factory, router discovery, middleware, lifespan |
| `fapilot/conf/` | Settings and cached/module loading |
| `fapilot/apps/` | App configuration and registry |
| `fapilot/db/` | ORM config/lifecycle and migration subprocess backend |
| `fapilot/auth/`, `permissions/` | Authentication helpers and permission predicates |
| `fapilot/events/`, `background/`, `realtime/` | Async features |
| `fapilot/testing/` | HTTPX testing wrapper |
| `tests/` | Framework regression tests |
| `docs/` | User guides and reference documentation |
| `.github/workflows/` | CI and package publishing workflows |

## Required checks

```bash
ruff check .
pyright
pytest
python -m build
twine check dist/*
```

Use the same virtual environment for imports and type checking. If Pyright resolves
the wrong interpreter, pass `--pythonpath .venv/bin/python` (adapt for your platform).
Add behavior tests for runtime changes, especially validation, migration targeting,
and actual database routing. Keep architectural scaffolds and docs aligned.

## Documentation maintenance

The documentation is repository-native Markdown and needs no documentation server.
Start at [docs/index.md](index.md); GitHub renders navigation and relative links.
When adding a public feature, update its guide, settings or CLI reference, API reference,
and troubleshooting notes as applicable. Change the README entry point if needed.

Before submitting documentation changes:

1. Check all relative links and referenced files.
2. Compile Python examples and run complete walkthroughs in a temporary project.
3. Verify CLI options against the parser and installed dependencies.
4. Test database examples on disposable files or databases.
5. Identify unsupported behavior rather than documenting it as implemented.

The documentation-only command `python docs/check_examples.py` checks links,
compiles Python snippets, runs the documented CRUD tests, and exercises the documented
migration workflow using a temporary project. It requires the `dev` extra and makes
changes only in its temporary directory. It also checks that settings fields, architecture
slugs, and public Python definitions remain represented in the documentation.

## Packaging and releases

Update the version in both `pyproject.toml` and `fapilot/__init__.py`, and add release
notes to [CHANGELOG.md](../CHANGELOG.md). Build artifacts and check metadata before
publishing. `MANIFEST.in` includes the Markdown docs in source distributions; the
runtime wheel contains the Python package rather than a rendered documentation site.

The repository's CI builds distributions and checks metadata. Its publishing workflow
uses the `pypi` environment and Trusted Publishing, triggers on published GitHub releases
or manual dispatch, and verifies release-tag/package-version agreement for release events.
Follow [RELEASE.md](../RELEASE.md) to configure the publisher and perform a release.
Publishing is a maintainer action; ordinary documentation updates do not publish anything.
