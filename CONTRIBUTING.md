# Contributing to FlowDL

Thanks for contributing.

## Development Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run Tests

```bash
python3 -m unittest discover -s tests -v
```

## Code Guidelines

- Keep CLI user-facing behavior preset-driven.
- Avoid exposing raw `yt-dlp` options in command arguments.
- Prefer focused, testable modules in `flowdl/core` and `flowdl/integrations`.
- Add or update unit tests with every behavior change.

## Pull Request Process

1. Open an issue first for major changes.
2. Keep PR scope focused and include tests.
3. Update `README.md` and `CHANGELOG.md` if behavior changes.
4. Ensure CI passes before requesting review.

