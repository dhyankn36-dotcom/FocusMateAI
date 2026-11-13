# FocusMate AI

![Tests](https://github.com/dhyankn36-dotcom/FocusMateAI/actions/workflows/tests.yml/badge.svg)

<div align="center">

### Your AI-powered workspace for planning, focus, and communication

Turn complex tasks into manageable actions, simplify difficult text, and draft clear messages with an interactive Streamlit application.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Ollama](https://img.shields.io/badge/Local_AI-Ollama-111111?logoColor=white)](https://ollama.com/)
[![SQLite](https://img.shields.io/badge/Storage-SQLite-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)

</div>

---

## Overview

FocusMate AI is a Python productivity application that helps users organize work and move from a broad request to a clear next action. It provides task planning, one-step guidance, text simplification, message drafting, progress tracking, and searchable local history.

The repository contains two application variants:

| Entry point | AI provider | Intended use |
|---|---|---|
| `app.py` | Local Ollama model (Llama 3.2 by default) | Run AI requests locally on your machine |
| `app_cloud.py` | Google Gemini API | Run with a configured hosted AI API key |

## Features

### AI productivity tools
- **Task planner:** Convert assignments, projects, and goals into actionable steps.
- **One-step mode:** Work through a plan one action at a time.
- **Text simplifier:** Rewrite difficult information in easier-to-understand language.
- **Message writer:** Draft clear messages that can be reviewed and edited.

### Planning and progress
- Track completed actions and remaining steps.
- View active and completed tasks in a progress overview.
- Resume the latest unfinished task.
- Undo the most recent completed step in one-step mode.
- Restart completed plans after confirming a progress reset.
- Duplicate saved plans without changing the original.

### History and data management
- Persist tasks and responses in SQLite.
- Search saved content by title, step, or response text.
- Filter task history by status and date range.
- Sort task and response history by title or creation time.
- Paginate task and response history.
- Rename saved tasks and edit saved response titles and content.
- Duplicate saved responses before editing.
- Export an individual task as a Markdown checklist.
- Download generated responses as text files with descriptive filenames.
- Back up and restore task and response history using JSON.
- Export all matching filtered history, not only the visible page.

### Personalization and usability
- Adjust response length and language style.
- Apply input limits to keep requests manageable.
- Clear history filters in one action.
- Delete individual saved tasks and responses.

## Technology Stack

| Technology | Role |
|---|---|
| Python | Application logic |
| Streamlit | Interactive user interface |
| Ollama | Local model runtime |
| Llama 3.2 | Default local language model |
| Google Gemini API | Hosted model provider for `app_cloud.py` |
| SQLite | Local task and response persistence |
| unittest | Automated test framework |

## Application Flow

```text
       USER INPUT
           |
           v
    SELECT A PRODUCTIVITY TOOL
      /        |        \
     v         v         v
  PLANNER  SIMPLIFIER  WRITER
      \        |        /
       v       v       v
       CONFIGURED AI PROVIDER
          /           \
         v             v
      OLLAMA         GEMINI API
         \             /
          v           v
         GENERATED RESPONSE
                 |
        +--------+---------+
        |                  |
        v                  v
   REVIEW / EDIT       SAVE TO SQLITE
        |                  |
        v                  v
  TAKE NEXT ACTION     HISTORY / EXPORT
```

## Run Locally

### Prerequisites

- Python 3.10 or newer
- [Ollama](https://ollama.com/) installed and running
- Llama 3.2 downloaded in Ollama
- Git (to clone the repository)

### 1. Clone the repository

```powershell
git clone https://github.com/dhyankn36-dotcom/FocusMateAI.git
cd FocusMateAI
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Download the local model

```powershell
ollama pull llama3.2
```

The local app uses the Ollama chat endpoint `http://localhost:11434/api/chat` and model `llama3.2` by default. Optional environment variables allow you to change these values:

```powershell
$env:FOCUSMATE_OLLAMA_URL = "http://localhost:11434/api/chat"
$env:FOCUSMATE_OLLAMA_MODEL = "llama3.2"
```

### 5. Start the application

```powershell
python -m streamlit run app.py
```

Open the local address shown by Streamlit, usually [http://localhost:8501](http://localhost:8501).

## Run the Hosted Gemini Variant

The alternate entry point is `app_cloud.py`. Configure `GEMINI_API_KEY` in your Streamlit deployment's **Settings → Secrets**:

```toml
GEMINI_API_KEY = "your-gemini-api-key"
```

Then launch `app_cloud.py` in the deployment configuration.

**Keep API keys in environment variables or deployment secrets. Never commit real credentials.** The hosted variant sends prompts to Google's Gemini API. Its SQLite data is stored on the deployment filesystem, which may be ephemeral; configure persistent storage before relying on history across restarts.

## Tests

Run the test suite from the repository root with the project dependencies installed:

```powershell
python -m unittest discover -s tests -v
```

The suite covers shared task/history behavior and saved-history editing across both application variants. GitHub Actions is configured to run tests on Python 3.10 and 3.12.

## Privacy and Responsible Use

- The local variant sends prompts to the Ollama service configured on your machine.
- The hosted variant sends prompts to Google's Gemini API.
- Task history is stored in SQLite; protect the database and your device.
- Local model execution does not by itself guarantee complete privacy or security.
- AI-generated output can be incorrect or incomplete. Review responses before using them for important work.

## Potential Improvements

- Persistent database storage for hosted deployments.
- More AI provider options and configurable model settings.
- Expanded accessibility and personalization controls.

## License

No open-source license has been selected in this repository. Until a license is added, permissions to reuse or redistribute this project should not be assumed.

---

<div align="center">

Built with Python, Streamlit, and AI.

**[GitHub Profile](https://github.com/dhyankn36-dotcom)**

</div>
