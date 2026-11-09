# FocusMate AI 🧠

**Your personal AI-powered cognitive co-pilot for planning, understanding, and communication.**

FocusMate AI is a Python-based productivity application designed to make everyday tasks easier to manage. It can use a locally running model or a hosted AI backend to break complex tasks into actionable steps, simplify difficult text, and draft clear messages through an interactive Streamlit dashboard.

Run [app.py](./app.py) with local Ollama, or use [app_cloud.py](./app_cloud.py) with the hosted Gemini API.

## ✨ Features

- **AI Task Planner:** Break large tasks into manageable, actionable steps.
- **Text Simplifier:** Make difficult information easier to understand.
- **Message Writer:** Generate clear, editable messages.
- **One-Step Mode:** Focus on one action at a time.
- **Personalization:** Adjust response length and language style.
- **Input Limits:** Keep AI requests responsive with clear per-tool text limits.
- **Task Progress Tracking:** Track completed actions and monitor progress.
- **Progress Overview:** See active tasks, finished tasks, and remaining actions at a glance.
- **Quick Resume:** Continue the latest unfinished task from the dashboard.
- **Flexible Progress:** Undo the last completed step while using one-step mode.
- **Task History and Persistence:** Save tasks and responses locally using SQLite.
- **Searchable History:** Find saved tasks and AI responses across all pages by title, step, or content.
- **Paged Task History:** Browse saved tasks in smaller pages, with search results paginated across the full history.
- **Task Status Filters:** Narrow saved tasks to in-progress or completed plans.
- **History Date Filters:** Narrow tasks and responses to a creation-date range; filters also apply to matching-history exports.
- **Task History Sorting:** Order saved tasks by creation time (newest or oldest) or title.
- **Task Checklist Downloads:** Export an individual saved task as a Markdown checklist with completion progress.
- **Paged Response History:** Browse saved AI responses beyond the latest 50.
- **Response History Sorting:** Browse saved responses by creation time (newest or oldest) or title, including search results.
- **Descriptive Downloads:** Save responses using safe filenames based on their titles.
- **History Backup:** Export saved tasks and AI responses to JSON and import backups up to 5 MB.
- **Filtered History Export:** Download all search and task-status matches as JSON without limiting the export to the visible page.
- **History Management:** Delete individual saved tasks and AI responses.
- **Downloadable Responses:** Download AI-generated responses as text files.
- **Local AI:** Run language generation locally through Ollama and Llama 3.2.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Streamlit | Interactive web interface |
| Ollama | Local language model runtime |
| Llama 3.2 | AI-powered text generation |
| Google Gemini API | Hosted AI backend used by `app_cloud.py` |
| SQLite | Local task and response storage |

## 🏗️ How It Works

1. The user selects a tool and enters a task, text, or message request.
2. FocusMate AI sends the input to the configured AI backend: local Ollama in `app.py` or Google Gemini in `app_cloud.py`.
3. The selected model generates a response.
4. The application displays the result and saves relevant information locally.
5. Users can revisit saved tasks, track progress, and download responses.

## 📋 Prerequisites

- Python 3.10 or newer
- [Ollama](https://ollama.com/) installed
- The Llama 3.2 model downloaded through Ollama
- Git, if cloning the repository

## 🚀 Installation and Setup

### 1. Clone the repository

```powershell
git clone https://github.com/dhyankn36-dotcom/FocusMateAI.git
cd FocusMateAI
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Download the AI model

Make sure Ollama is installed and running.

```powershell
ollama pull llama3.2
```

The local app defaults to `http://localhost:11434/api/chat` and the `llama3.2` model. To choose another Ollama-compatible server or installed model, set optional environment variables before starting Streamlit:

```powershell
$env:FOCUSMATE_OLLAMA_URL = "http://localhost:11434/api/chat"
$env:FOCUSMATE_OLLAMA_MODEL = "llama3.2"
python -m streamlit run app.py
```

### 5. Run the application

```powershell
python -m streamlit run app.py
```

Open the local URL displayed in your terminal, usually `http://localhost:8501`.

## Hosted Gemini variant

To run `app_cloud.py`, configure `GEMINI_API_KEY` in your Streamlit deployment's **Settings → Secrets**:

```toml
GEMINI_API_KEY = "your-gemini-api-key"
```

Keep the key in deployment secrets; do not commit it to the repository. This variant sends prompts to Google's Gemini API, unlike the local Ollama app. Its SQLite database is stored on the deployment filesystem, which may be ephemeral; use a persistent database before relying on hosted task history across restarts.

## 🔧 Troubleshooting

**Ollama connection error**
- Check that Ollama is installed and running.
- Run `ollama list` to verify that Llama 3.2 is available.
- Check that the application can reach the configured Ollama endpoint.

**Gemini API key is missing**
- Add `GEMINI_API_KEY` to the hosted app's Streamlit secrets and restart the app.

**Python dependency errors**
- Activate the virtual environment.
- Run `python -m pip install -r requirements.txt`.

**Model not found**
- Run `ollama pull llama3.2` and retry.

## 🔒 Privacy and Limitations

FocusMate AI is a productivity aid, not a diagnostic or medical tool.

The local app processes prompts through Ollama on your machine. The hosted Gemini variant sends prompts to Google's API. Protect your device, API credentials, and stored data; local processing alone does not guarantee complete privacy.

AI-generated responses may contain errors or omissions. Review the output before relying on it for important decisions.

## 🗺️ Future Improvements

Potential improvements include:
- Using a persistent database for hosted deployments
- Additional personalization and accessibility options

## 📄 License

No open-source license has been selected yet. Until a license is added, reuse and redistribution permissions should not be assumed.

---

**Built with Python and Streamlit; supports local Ollama and hosted Gemini.**