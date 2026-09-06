# Release Process

Fapilot can be released to PyPI from a clean git checkout.

## Before releasing

1. Confirm the distribution name in `pyproject.toml`.
2. Update `version` in `pyproject.toml`.
3. Update `CHANGELOG.md`.
4. Add `project.urls` in `pyproject.toml` after the GitHub repository URL is final.
5. Run the checks:

```bash
ruff check .
pyright
pytest
python -m build
twine check dist/*
```

## GitHub release

```bash
git tag v0.1.0
git push origin main --tags
```

## PyPI release

This repository includes a GitHub Actions workflow for Trusted Publishing. Add
the matching publisher on PyPI, then publish by creating a GitHub release.

For a manual upload:

```bash
python -m build
twine upload dist/*
```
