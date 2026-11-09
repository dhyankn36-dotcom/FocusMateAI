# FocusMate AI 🧠

**Your personal AI-powered cognitive co-pilot for planning, understanding, and communication.**

FocusMate AI is a Python-based productivity application designed to make everyday tasks easier to manage. It uses a locally running large language model to break complex tasks into actionable steps, simplify difficult text, and draft clear messages through an interactive Streamlit dashboard.

## ✨ Features

- **AI Task Planner:** Break large tasks into manageable, actionable steps.
- **Text Simplifier:** Make difficult information easier to understand.
- **Message Writer:** Generate clear, editable messages.
- **One-Step Mode:** Focus on one action at a time.
- **Personalization:** Adjust response length and language style.
- **Task Progress Tracking:** Track completed actions and monitor progress.
- **Task History and Persistence:** Save tasks and responses locally using SQLite.
- **Downloadable Responses:** Download AI-generated responses as text files.
- **Local AI:** Run language generation locally through Ollama and Llama 3.2.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Streamlit | Interactive web interface |
| Ollama | Local language model runtime |
| Llama 3.2 | AI-powered text generation |
| SQLite | Local task and response storage |

## 🏗️ How It Works

1. The user selects a tool and enters a task, text, or message request.
2. FocusMate AI prepares the input and sends it to the local Ollama service.
3. Llama 3.2 generates a response.
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

### 5. Run the application

```powershell
python -m streamlit run app.py
```

Open the local URL displayed in your terminal, usually `http://localhost:8501`.

## 🔧 Troubleshooting

**Ollama connection error**
- Check that Ollama is installed and running.
- Run `ollama list` to verify that Llama 3.2 is available.
- Check that the application can reach the configured Ollama endpoint.

**Python dependency errors**
- Activate the virtual environment.
- Run `python -m pip install -r requirements.txt`.

**Model not found**
- Run `ollama pull llama3.2` and retry.

## 🔒 Privacy and Limitations

FocusMate AI is a productivity aid, not a diagnostic or medical tool.

The application is designed to use a local language model. However, local processing alone does not guarantee complete privacy. Protect your device and stored data.

AI-generated responses may contain errors or omissions. Review the output before relying on it for important decisions.

## 🗺️ Future Improvements

Potential improvements include:
- Expanded automated testing and error handling
- Additional personalization options
- Deployment with a compatible AI backend
- Improved onboarding and documentation

## 📄 License

No open-source license has been selected yet. Until a license is added, reuse and redistribution permissions should not be assumed.

---

**Built with Python, Streamlit, Ollama, and Llama 3.2.**