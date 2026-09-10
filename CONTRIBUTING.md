# Contributing

Thanks for taking the time to improve Fapilot.

See the [expanded contributor guide](docs/contributing.md) for the repository map,
documentation checks, and release integration.

## Development setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

## Checks

Run these before opening a pull request:

```bash
ruff check .
pyright
pytest
python -m build
twine check dist/*
```

## Pull requests

- Keep changes focused.
- Add or update tests for behavior changes.
- Update `README.md` or `CHANGELOG.md` when user-facing behavior changes.
- Do not commit generated packaging artifacts such as `dist/`, `build/`, or
  `*.egg-info/`.
