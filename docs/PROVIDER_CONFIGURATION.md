# AI Provider Configuration

FocusMateAI has two application entry points so the AI runtime can match the way you want to run the app.

## Local Ollama application

Use `app.py` when you want prompts to be processed by an Ollama model running on your own machine.

1. Install and start Ollama.
2. Download the configured model (Llama 3.2 by default).
3. Install the Python dependencies from `requirements.txt`.
4. Start the app with `python -m streamlit run app.py`.

The default chat endpoint is `http://localhost:11434/api/chat`. The endpoint and model can be overridden with `FOCUSMATE_OLLAMA_URL` and `FOCUSMATE_OLLAMA_MODEL`.

## Hosted Gemini application

Use `app_cloud.py` when you want requests to be handled by the Gemini API.

1. Create an API key with Google AI Studio.
2. Store it in the `GEMINI_API_KEY` environment variable or your deployment platform's secrets manager.
3. Start the Streamlit app using `app_cloud.py`.

Never put a real API key in source code, README examples, screenshots, or commits.

## Choosing a provider

| Consideration | Local Ollama | Gemini API |
|---|---|---|
| Runtime | Your machine | Hosted API |
| Network | Local service; internet may be needed to download models | Internet required |
| Credentials | No hosted API key required | API key required |
| Compute | Uses local system resources | Uses provider infrastructure |
| Data handling | Prompts go to the configured local Ollama service | Prompts are sent to Google's API |

## Troubleshooting

- **Ollama connection refused:** confirm the Ollama service is running and that the configured URL is correct.
- **Model not found:** run `ollama pull llama3.2` or set the model variable to an installed model.
- **Gemini authentication error:** check that `GEMINI_API_KEY` is set in the environment used to launch Streamlit.
- **Unexpected provider behavior:** verify which entry point you launched; `app.py` and `app_cloud.py` use different providers.

AI output may be inaccurate. Review generated plans and messages before relying on them.
