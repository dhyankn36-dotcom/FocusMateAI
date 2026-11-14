# Contributing to FocusMate AI

Thanks for considering a contribution. This guide keeps changes easy to review and helps protect users' saved data and configuration.

## Getting started

1. Fork the repository and clone your fork.
2. Create a focused branch from `main`, for example `feature/history-filter` or `fix/task-progress`.
3. Follow the local setup instructions in [README.md](README.md).
4. Make a small, clearly scoped change.

## Development guidelines

- Keep the local Ollama and hosted Gemini entry points working independently.
- Reuse shared task and history behavior where practical instead of duplicating logic.
- Preserve existing saved-history behavior unless a change explicitly addresses it.
- Validate user-provided input and handle unavailable AI providers with clear messages.
- Keep secrets, API keys, local databases, and personal data out of commits.
- Update documentation when setup steps, configuration, or user-facing behavior changes.

## Run the tests

From the repository root, install the project dependencies and run:

```bash
python -m unittest discover -s tests -v
```

Please include relevant test coverage for bug fixes and new behavior.

## Pull requests

- Explain the problem and the proposed solution.
- List the main files or behaviors changed.
- Include test results and any manual verification performed.
- Add screenshots for meaningful UI changes when useful.
- Keep pull requests focused; avoid unrelated formatting or generated files.

## Reporting issues

Include steps to reproduce, expected behavior, actual behavior, and relevant error output. Remove API keys, personal information, and private task content before sharing logs.
