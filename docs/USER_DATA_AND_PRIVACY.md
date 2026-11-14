# User Data and Privacy Notes

This document describes the data-handling choices users should understand before using FocusMate AI.

## AI requests

- `app.py` uses the Ollama service configured for the local application.
- `app_cloud.py` uses the configured Google Gemini API.
- Prompts and related context are sent to the selected provider to generate a response. Do not submit information you are not authorized to share with that provider.

## Local history

Task and response history is stored in SQLite. Treat the database as personal data: protect the device account, avoid placing the database in a public or shared folder, and make backups only in locations you trust.

JSON backups and downloaded responses can contain the original task descriptions and generated content. Check their contents before sending or uploading them.

## Before deployment

1. Configure provider credentials outside source control.
2. Use deployment secrets for hosted API keys.
3. Confirm the deployment has an appropriate persistent-storage plan if history must survive restarts.
4. Explain to users which AI provider is configured.
5. Provide a way to protect and remove stored history appropriate to the deployment.

## Output quality

AI output may be inaccurate, incomplete, or unsuitable for a particular task. Review and edit generated plans and messages before acting on them.
