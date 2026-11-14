# Security Policy

## Supported versions

Security fixes are accepted for the latest version on the default branch.

## Reporting a vulnerability

Do not publish API keys, private task history, or exploit details in a public issue. Use the repository's private vulnerability reporting option in GitHub's Security tab. Include the affected component, impact, and safe reproduction steps. Allow reasonable time for investigation before public disclosure.

## Application-specific precautions

- Keep Gemini API keys in deployment secrets or local environment configuration.
- Treat SQLite task history, JSON backups, and downloaded responses as private user data.
- Remember that the hosted variant sends prompts to Gemini, while the local variant uses the configured Ollama service.
- Restrict access to the device, database, and backup locations.
- Review generated content before relying on it.

## Deployment checklist

Use HTTPS where applicable, protect deployment secrets, review provider data-handling terms, and configure persistent storage deliberately if hosted history must survive restarts.
