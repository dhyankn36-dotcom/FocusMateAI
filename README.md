# FocusMate AI 🧠

FocusMate AI is a personal cognitive co-pilot that helps make everyday tasks, information, and communication easier to manage.

## Features

- **Task Breakdown:** Break large tasks into manageable actions.
- **Text Simplification:** Make difficult text easier to understand.
- **Message Drafting:** Generate clear, editable messages.
- **One-Step Mode:** Focus on one action at a time.
- **Personalization:** Choose response length and language style.
- **Download Responses:** Save AI-generated responses as text.
- **Local AI:** Uses Ollama to run the language model locally.

## Technology Stack

- Python
- Streamlit
- Ollama
- Llama 3.2

## Prerequisites

- Python 3.10 or newer
- Ollama installed
- The Llama 3.2 model

## Installation

Clone this repository and open the project folder.

Install the Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

Download the AI model:

```powershell
ollama pull llama3.2
```

Run the application:

```powershell
python -m streamlit run app.py
```

Open the local URL shown in the terminal.

## Privacy and Limitations

FocusMate AI is designed as an assistive tool, not a diagnostic tool. AI-generated responses may contain errors, so review them before relying on them.

## License

No license has been selected yet.
