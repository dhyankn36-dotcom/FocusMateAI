# FocusMate AI Release Checklist

Use this checklist before publishing a release or deploying an updated build.

## Application behavior

- [ ] Launch the local Ollama entry point and verify the configured model is available.
- [ ] Launch the Gemini entry point with a deployment secret, not a committed key.
- [ ] Test task planning, one-step guidance, simplification, and message drafting.
- [ ] Verify task progress, completion, restart, and undo behavior.
- [ ] Check history search, filters, pagination, editing, duplication, and deletion.
- [ ] Export a task checklist, response text, and a JSON history backup; inspect the files.

## Data and privacy

- [ ] Confirm the original task and response history remains intact after an upgrade.
- [ ] Test backup and restore using a disposable test database.
- [ ] Document which AI provider receives prompts in the deployed variant.
- [ ] Confirm database files and exported user content are excluded from Git.

## Quality checks

- [ ] Run `python -m unittest discover -s tests -v`.
- [ ] Review the GitHub Actions result for the release commit.
- [ ] Check installation instructions against the current requirements.
- [ ] Review changed dependencies and remove unused packages.
- [ ] Update the README when user-visible behavior or setup changes.

## Publish

- [ ] Review the final diff and commit history.
- [ ] Add concise release notes describing user-visible changes.
- [ ] State known limitations and any required configuration changes.
