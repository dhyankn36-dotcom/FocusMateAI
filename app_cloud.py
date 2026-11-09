
import html
from datetime import datetime
from pathlib import Path

import requests
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
from focusmate_core import (
    MAX_MESSAGE_PURPOSE_CHARS,
    MAX_RECIPIENT_CHARS,
    MAX_SIMPLIFY_INPUT_CHARS,
    MAX_TASK_INPUT_CHARS,
    build_history_export,
    delete_response_record,
    delete_task_record,
    extract_action_steps,
    extract_gemini_content,
    extract_gemini_error,
    filter_history,
    json_dump,
    json_load,
    open_database,
    task_stats,
    undo_last_completed_action,
)


# ============================================================
# FOCUSPATE AI — PRODUCTIVITY WORKSPACE
# ============================================================

st.set_page_config(
    page_title="FocusMate AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

GEMINI_MODEL = "gemini-3.8-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
DB_PATH = Path(__file__).resolve().parent / "focusmate.db"


# ============================================================
# DATABASE
# ============================================================

def get_db():
    return open_database(DB_PATH)


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                actions TEXT NOT NULL,
                completed TEXT NOT NULL DEFAULT '[]',
                finished INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


def save_task():
    task_id = st.session_state.get("task_db_id")
    title = st.session_state.get("task_title", "")
    actions = st.session_state.get("task_actions", [])
    completed = st.session_state.get("completed_actions", [])
    finished = st.session_state.get("task_finished", False)

    if not title or not actions:
        return

    with get_db() as db:
        if task_id:
            db.execute(
                """UPDATE tasks SET title=?, actions=?, completed=?,
                   finished=? WHERE id=?""",
                (
                    title,
                    json_dump(actions),
                    json_dump(completed),
                    int(finished),
                    task_id,
                ),
            )
        else:
            cursor = db.execute(
                """INSERT INTO tasks
                   (title, actions, completed, finished, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    title,
                    json_dump(actions),
                    json_dump(completed),
                    int(finished),
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            st.session_state.task_db_id = cursor.lastrowid


def save_response(title, content):
    st.session_state.last_response_title = title
    st.session_state.last_response = content

    with get_db() as db:
        db.execute(
            "INSERT INTO responses (title, content, created_at) VALUES (?, ?, ?)",
            (
                title,
                content,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )


def load_tasks():
    with get_db() as db:
        return db.execute(
            "SELECT * FROM tasks ORDER BY id DESC"
        ).fetchall()


def load_responses():
    with get_db() as db:
        return db.execute(
            "SELECT * FROM responses ORDER BY id DESC LIMIT 50"
        ).fetchall()

def load_all_responses():
    with get_db() as db:
        return db.execute(
            "SELECT * FROM responses ORDER BY id DESC"
        ).fetchall()


init_db()


# ============================================================
# THEME
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');

:root {
    color-scheme: light;
    --ink: #202844;
    --muted: #596783;
    --primary: #4f6bed;
    --border: #e0e5f0;
    --background: #f7f8fc;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: var(--background) !important;
    color: var(--ink) !important;
}

.stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stApp p, .stApp label, .stApp li,
.stApp [data-testid="stCaptionContainer"],
.stApp [data-testid="stWidgetLabel"],
.stApp [data-testid="stMarkdownContainer"] {
    color: var(--ink) !important;
}

[data-testid="stHeader"] {
    background: rgba(247,248,252,.96) !important;
}

[data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {
    background: white !important;
}

[data-testid="stSidebar"] {
    border-right: 1px solid var(--border);
}

.block-container {
    max-width: 1240px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

.fm-brand {
    font-size: 1.5rem;
    font-weight: 800;
    letter-spacing: -.8px;
    color: var(--ink) !important;
}

.fm-brand span, .fm-eyebrow {
    color: var(--primary) !important;
}

.fm-caption {
    color: var(--muted) !important;
    line-height: 1.6;
}

.fm-hero {
    background: linear-gradient(115deg,#fff 0%,#f0f3ff 62%,#f3efff 100%);
    border: 1px solid #e4e8fb;
    border-radius: 22px;
    padding: 2rem;
    margin-bottom: 1.4rem;
}

.fm-eyebrow {
    text-transform: uppercase;
    letter-spacing: 1.4px;
    font-size: .75rem;
    font-weight: 800;
    margin-bottom: .5rem;
}

.fm-title {
    font-size: clamp(1.8rem,3vw,2.6rem);
    font-weight: 800;
    line-height: 1.2;
    color: var(--ink) !important;
    margin-bottom: .6rem;
}

.fm-card {
    background: white;
    border: 1px solid var(--border);
    border-radius: 17px;
    padding: 1.25rem;
    min-height: 155px;
}

.fm-card-icon {
    font-size: 1.7rem;
    margin-bottom: .6rem;
}

.fm-card-title {
    font-size: 1.05rem;
    font-weight: 800;
    color: var(--ink) !important;
    margin-bottom: .4rem;
}

.fm-card-text {
    color: var(--muted) !important;
    line-height: 1.6;
    font-size: .9rem;
}

.fm-step {
    background: white;
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1rem;
    margin-bottom: .65rem;
}

.fm-current {
    background: #f1f3ff;
    border-color: #9ba9ff;
}

.stButton > button, .stDownloadButton > button,
[data-testid="stFormSubmitButton"] > button {
    border-radius: 11px;
    min-height: 2.65rem;
    font-weight: 700;
}

.stButton > button[kind="primary"],
[data-testid="stFormSubmitButton"] > button[kind="primary"] {
    background: var(--primary) !important;
    color: white !important;
    border-color: var(--primary) !important;
}

.stButton > button[kind="primary"] *,
[data-testid="stFormSubmitButton"] > button[kind="primary"] * {
    color: white !important;
}

.stTextArea textarea, .stTextInput input {
    background: white !important;
    color: var(--ink) !important;
    -webkit-text-fill-color: var(--ink) !important;
    border-radius: 10px !important;
}

.stTextArea textarea::placeholder, .stTextInput input::placeholder {
    color: #697691 !important;
    -webkit-text-fill-color: #697691 !important;
    opacity: 1 !important;
}

[data-baseweb="select"] > div {
    background: white !important;
}

.stTabs [data-baseweb="tab"],
.stTabs [data-baseweb="tab"] * {
    color: #394563 !important;
    font-weight: 700;
}

.stTabs [data-baseweb="tab"][aria-selected="true"],
.stTabs [data-baseweb="tab"][aria-selected="true"] * {
    color: #3048b5 !important;
}

[data-testid="stMetric"] {
    background: white;
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1rem;
}

[data-testid="stMetric"] label,
[data-testid="stMetricValue"] {
    color: var(--ink) !important;
}

[data-testid="stExpander"] {
    background: white;
    border: 1px solid var(--border);
    border-radius: 12px;
}

[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg,#4f6bed,#8067e8) !important;
}

@media(max-width:700px) {
    .block-container {padding-top:1rem;}
    .fm-hero {padding:1.25rem;}
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================

DEFAULTS = {
    "page": "Dashboard",
    "last_response": "",
    "last_response_title": "",
    "task_actions": [],
    "completed_actions": [],
    "current_action": 0,
    "task_title": "",
    "task_active": False,
    "task_finished": False,
    "task_generation": 0,
    "task_db_id": None,
    "response_length": "Balanced",
    "language_style": "Simple",
    "one_step_mode": True,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# AI HELPERS
# ============================================================

def build_preferences():
    lengths = {
        "Short": "Be concise and focus on essentials.",
        "Balanced": "Give a useful, organized explanation.",
        "Detailed": "Explain thoroughly with examples and clear steps.",
    }
    styles = {
        "Simple": "Use beginner-friendly language and explain jargon.",
        "Standard": "Use clear professional language.",
    }
    return (
        lengths[st.session_state.response_length] + " "
        + styles[st.session_state.language_style]
        + " Do not invent facts."
    )


def ask_ollama(prompt, system_prompt=None):
    """Generate a response with Gemini for the hosted Streamlit app."""
    system_prompt = system_prompt or (
        "You are FocusMate AI, a practical and supportive productivity "
        "assistant. Be accurate, organized, and actionable."
    )

    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
    except StreamlitSecretNotFoundError:
        api_key = ""

    if not api_key:
        return None, (
            "Gemini API key is missing. Add GEMINI_API_KEY in your "
            "Streamlit app Settings → Secrets, then reboot the app."
        )

    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4},
    }

    try:
        response = requests.post(
            GEMINI_URL,
            headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
            json=payload,
            timeout=(10, 120),
        )
        if response.status_code != 200:
            try:
                details = extract_gemini_error(response.json())
            except ValueError:
                details = ""
            return None, (
                f"Gemini API returned HTTP {response.status_code}. "
                + (details or "Check your API key, model access, and quota.")
            )

        answer = extract_gemini_content(response.json())
        if not answer:
            return None, "Gemini returned an empty response. Please try again."
        return answer, None
    except requests.exceptions.Timeout:
        return None, "Gemini took too long to respond. Please try again."
    except requests.exceptions.RequestException:
        return None, "Could not reach Gemini. Check the app's internet connection and try again."
    except (ValueError, KeyError, IndexError) as exc:
        return None, f"Could not read Gemini's response: {exc}"


# ============================================================
# TASK HELPERS
# ============================================================

def start_task(title, actions):
    st.session_state.task_title = title.strip()
    st.session_state.task_actions = actions
    st.session_state.completed_actions = []
    st.session_state.current_action = 0
    st.session_state.task_active = True
    st.session_state.task_finished = False
    st.session_state.task_db_id = None
    st.session_state.task_generation += 1
    save_task()


def save_task_progress():
    if st.session_state.task_actions:
        save_task()


def finish_task():
    st.session_state.completed_actions = list(
        range(len(st.session_state.task_actions))
    )
    st.session_state.task_finished = True
    st.session_state.task_active = False
    save_task_progress()


def undo_task_progress():
    st.session_state.completed_actions = undo_last_completed_action(
        st.session_state.completed_actions
    )
    st.session_state.task_finished = False
    st.session_state.task_active = True
    save_task_progress()


def navigate(page):
    st.session_state.page = page


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

with st.sidebar:
    st.markdown(
        '<div class="fm-brand">FocusMate<span> AI</span> 🎯</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="fm-caption">Your personal cognitive co-pilot.</p>',
        unsafe_allow_html=True,
    )
    st.divider()

    pages = [
        "Dashboard",
        "Task Planner",
        "Text Simplifier",
        "Message Writer",
        "History",
    ]

    selected_page = st.radio(
        "NAVIGATION",
        pages,
        index=pages.index(st.session_state.page),
        label_visibility="collapsed",
    )

    if selected_page != st.session_state.page:
        navigate(selected_page)
        st.rerun()

    st.divider()
    st.markdown("#### ⚙️ Personalization")

    st.selectbox(
        "Response length",
        ["Short", "Balanced", "Detailed"],
        key="response_length",
    )
    st.selectbox(
        "Language style",
        ["Simple", "Standard"],
        key="language_style",
    )
    st.toggle("One step at a time", key="one_step_mode")

    st.divider()
    st.markdown("#### ☁️ Hosted AI")

    st.caption(f"Model: `{GEMINI_MODEL}`")
    if st.button("Check Gemini connection", use_container_width=True):
        with st.spinner("Checking Gemini API..."):
            _, error = ask_ollama(
                "Reply with the single word Connected.",
                "Reply with one short word only.",
            )
        if error:
            st.error(error)
        else:
            st.success("Gemini is responding.")

    st.caption("Your prompts are sent to the Google Gemini API.")


# ============================================================
# LOAD SAVED DATA
# ============================================================

tasks = load_tasks()
responses = load_responses()


# ============================================================
# DASHBOARD
# ============================================================

if st.session_state.page == "Dashboard":
    st.markdown("""
    <div class="fm-hero">
        <div class="fm-eyebrow">YOUR PERSONAL AI WORKSPACE</div>
        <div class="fm-title">Make progress, one step at a time.</div>
        <p class="fm-caption">
            Plan your work, simplify difficult information, and write
            with confidence — all in one place.
        </p>
    </div>
    """, unsafe_allow_html=True)

    (
        total_tasks,
        finished_tasks,
        active_tasks,
        total_actions,
        completed_actions,
    ) = (
        task_stats(tasks)
    )
    remaining = max(0, total_actions - completed_actions)
    completion_rate = (
        round(completed_actions / total_actions * 100)
        if total_actions else 0
    )

    st.markdown("### 📊 Your overview")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total tasks", total_tasks)
    m2.metric("Tasks finished", finished_tasks)
    m3.metric("Tasks in progress", active_tasks)
    m4.metric("Actions completed", completed_actions)
    m5.metric("Actions remaining", remaining)

    st.markdown("### Overall progress")
    st.progress(
        completion_rate / 100,
        text=f"{completion_rate}% of saved task actions completed",
    )

    st.markdown("### 🚀 Your workspace")
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("""
        <div class="fm-card">
            <div class="fm-card-icon">🧩</div>
            <div class="fm-card-title">Task Planner</div>
            <div class="fm-card-text">
                Break goals into manageable steps and track progress.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Task Planner", use_container_width=True):
            navigate("Task Planner")
            st.rerun()

    with c2:
        st.markdown("""
        <div class="fm-card">
            <div class="fm-card-icon">📘</div>
            <div class="fm-card-title">Text Simplifier</div>
            <div class="fm-card-text">
                Make complex concepts easier to understand.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Text Simplifier", use_container_width=True):
            navigate("Text Simplifier")
            st.rerun()

    with c3:
        st.markdown("""
        <div class="fm-card">
            <div class="fm-card-icon">✍️</div>
            <div class="fm-card-title">Message Writer</div>
            <div class="fm-card-text">
                Draft clear and appropriate messages in seconds.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Message Writer", use_container_width=True):
            navigate("Message Writer")
            st.rerun()

    st.markdown("### 🗂️ Recent tasks")
    if tasks:
        for task in tasks[:5]:
            action_list = json_load(task["actions"])
            done_list = json_load(task["completed"])
            count = len(action_list)
            percent = round(len(done_list) / count * 100) if count else 0

            with st.container(border=True):
                st.markdown(f"**{task['title']}**")
                st.caption(
                    f"{len(done_list)} of {count} actions complete · "
                    f"{'Finished' if task['finished'] else 'In progress'}"
                )
                st.progress(percent / 100)
    else:
        st.info("No saved tasks yet. Open Task Planner to create your first plan.")

    if st.button("View full history →"):
        navigate("History")
        st.rerun()


# ============================================================
# TASK PLANNER
# ============================================================

elif st.session_state.page == "Task Planner":
    st.markdown("## 🧩 Task Planner")
    st.caption("Turn a goal into a practical, step-by-step action plan.")

    with st.form("task_form"):
        task_input = st.text_area(
            "What do you need to do?",
            placeholder=(
                "Example: Prepare for my DAA exam, build a Python project, "
                "or plan my weekly study schedule..."
            ),
            height=120,
            max_chars=MAX_TASK_INPUT_CHARS,
        )
        submitted = st.form_submit_button(
            "✨ Generate action plan",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not task_input.strip():
            st.warning("Enter a task or goal first.")
        else:
            prompt = f"""
Create a practical action plan for this goal:

{task_input.strip()}

Requirements:
- Provide 5 to 8 concrete, actionable steps.
- Put each step on its own line.
- Number the steps from 1.
- Start with action verbs where possible.
- Order the steps logically.
- Keep each step specific and manageable.
- Return the numbered list only.
"""
            with st.spinner("Building your action plan..."):
                answer, error = ask_ollama(
                    prompt,
                    "You are an expert task planner. Return a numbered "
                    "list of realistic and actionable steps. "
                    + build_preferences(),
                )

            if error:
                st.error(error)
            else:
                actions = extract_action_steps(answer)
                if len(actions) < 2:
                    st.warning("The AI returned too few steps. Please try again.")
                else:
                    start_task(task_input, actions)
                    save_response("Task action plan", answer)
                    st.success("Your plan has been saved.")
                    st.rerun()

    # Display the active task in this session.
    if st.session_state.task_actions:
        actions = st.session_state.task_actions
        completed = st.session_state.completed_actions
        total = len(actions)
        done = len(completed)

        st.divider()
        st.markdown("### 📍 Task progress")
        st.markdown(f"**{st.session_state.task_title}**")

        a, b, c = st.columns(3)
        a.metric("Total actions", total)
        b.metric("Completed", done)
        c.metric("Remaining", total - done)

        st.progress(done / total if total else 0)

        if done == total:
            st.success("🎉 All actions are complete!")
            st.session_state.task_finished = True
            st.session_state.task_active = False
            save_task_progress()
            if st.session_state.one_step_mode and completed:
                if st.button(
                    "↩ Undo last completed step",
                    use_container_width=True,
                ):
                    undo_task_progress()
                    st.rerun()
        else:
            incomplete = [i for i in range(total) if i not in completed]
            current = incomplete[0]

            if st.session_state.one_step_mode:
                st.markdown(
                    '<div class="fm-step fm-current">'
                    '<div class="fm-eyebrow">YOUR NEXT ACTION</div>'
                    f'<strong>STEP {current + 1} OF {total}</strong><br><br>'
                    f'{html.escape(actions[current])}'
                    '</div>',
                    unsafe_allow_html=True,
                )

                if st.button(
                    "✓ Mark current action complete",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state.completed_actions = sorted(
                        set(completed) | {current}
                    )
                    save_task_progress()
                    st.rerun()
            else:
                st.markdown("#### Action checklist")
                for i, action in enumerate(actions):
                    checked = st.checkbox(
                        f"Step {i + 1}: {action}",
                        value=(i in completed),
                        key=f"check_{st.session_state.task_generation}_{i}",
                    )
                    if checked and i not in completed:
                        st.session_state.completed_actions = sorted(
                            set(completed) | {i}
                        )
                        save_task_progress()
                        st.rerun()
                    elif not checked and i in completed:
                        st.session_state.completed_actions = [
                            n for n in completed if n != i
                        ]
                        save_task_progress()
                        st.rerun()

            if st.session_state.one_step_mode and completed:
                if st.button("↩ Undo last completed step", use_container_width=True):
                    undo_task_progress()
                    st.rerun()

            with st.expander("📋 View full action plan"):
                for i, action in enumerate(actions):
                    if i in st.session_state.completed_actions:
                        st.markdown(f"- ~~{action}~~ ✅")
                    else:
                        st.markdown(f"- {action}")

            if st.button("Finish task", use_container_width=True):
                finish_task()
                st.rerun()

        if st.button("＋ Start a new task", use_container_width=True):
            st.session_state.task_title = ""
            st.session_state.task_actions = []
            st.session_state.completed_actions = []
            st.session_state.current_action = 0
            st.session_state.task_active = False
            st.session_state.task_finished = False
            st.session_state.task_db_id = None
            st.session_state.task_generation += 1
            st.rerun()

    st.markdown("### Previously saved tasks")
    if tasks:
        for task in tasks[:10]:
            with st.expander(task["title"]):
                saved_actions = json_load(task["actions"])
                saved_done = json_load(task["completed"])
                st.caption(
                    f"{len(saved_done)} / {len(saved_actions)} actions complete"
                )
                for i, action in enumerate(saved_actions):
                    mark = "✅" if i in saved_done else "▫️"
                    st.markdown(f"{mark} {action}")

                if st.button(
                    "Resume this task",
                    key=f"resume_{task['id']}",
                ):
                    st.session_state.task_db_id = task["id"]
                    st.session_state.task_title = task["title"]
                    st.session_state.task_actions = saved_actions
                    st.session_state.completed_actions = saved_done
                    st.session_state.task_finished = bool(task["finished"])
                    st.session_state.task_active = not bool(task["finished"])
                    st.session_state.task_generation += 1
                    st.rerun()


# ============================================================
# TEXT SIMPLIFIER
# ============================================================

elif st.session_state.page == "Text Simplifier":
    st.markdown("## 📘 Text Simplifier")
    st.caption("Make difficult concepts and long passages easier to understand.")

    with st.form("simplify_form"):
        text_input = st.text_area(
            "Text you want to simplify",
            placeholder="Paste your study notes or text here...",
            height=240,
            max_chars=MAX_SIMPLIFY_INPUT_CHARS,
        )
        submitted = st.form_submit_button(
            "Simplify this text",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not text_input.strip():
            st.warning("Paste some text first.")
        else:
            prompt = f"""
Simplify the following text for a learner.

- Preserve the original meaning and important facts.
- Use clear, easy language.
- Explain technical terms.
- Use short paragraphs and bullets when helpful.
- Include a simple example if useful.
- Do not introduce unsupported claims.

TEXT:
{text_input.strip()}
"""
            with st.spinner("Simplifying your text..."):
                answer, error = ask_ollama(
                    prompt,
                    "You are a patient educational assistant. "
                    + build_preferences(),
                )

            if error:
                st.error(error)
            else:
                save_response("Simplified text", answer)
                st.rerun()


# ============================================================
# MESSAGE WRITER
# ============================================================

elif st.session_state.page == "Message Writer":
    st.markdown("## ✍️ Message Writer")
    st.caption("Write a clear message for the situation and tone you choose.")

    with st.form("draft_form"):
        recipient = st.text_input(
            "Who is the message for?",
            placeholder="My professor, manager, teammate...",
            max_chars=MAX_RECIPIENT_CHARS,
        )
        purpose = st.text_area(
            "What do you want to communicate?",
            placeholder="Explain what you want your message to say...",
            height=150,
            max_chars=MAX_MESSAGE_PURPOSE_CHARS,
        )
        tone = st.selectbox(
            "Choose a tone",
            ["Professional", "Friendly", "Polite", "Formal", "Casual"],
        )
        submitted = st.form_submit_button(
            "Draft my message",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not recipient.strip() or not purpose.strip():
            st.warning("Enter both the recipient and message purpose.")
        else:
            prompt = f"""
Draft a complete message.

Recipient: {recipient.strip()}
Purpose: {purpose.strip()}
Tone: {tone}

Requirements:
- Make the message natural, respectful, and clear.
- Include an appropriate greeting and closing.
- Do not invent names, dates, events, or promises.
- Return the message only.
"""
            with st.spinner("Drafting your message..."):
                answer, error = ask_ollama(
                    prompt,
                    "You are a professional writing assistant. "
                    + build_preferences(),
                )

            if error:
                st.error(error)
            else:
                save_response("Drafted message", answer)
                st.rerun()


# ============================================================
# HISTORY
# ============================================================

elif st.session_state.page == "History":
    st.markdown("## 🕘 History")
    st.caption("Review tasks and AI responses saved on this computer.")

    history_query = st.text_input(
        "Search saved tasks and AI responses",
        placeholder="Search titles, content, or task steps...",
        key="history_search",
    )
    matching_tasks = filter_history(tasks, history_query, ("title", "actions"))
    matching_responses = filter_history(
        responses, history_query, ("title", "content")
    )

    if tasks or responses:
        st.download_button(
            "⬇️ Download all history (.json)",
            data=build_history_export(tasks, load_all_responses()),
            file_name="focusmate_history.json",
            mime="application/json",
            use_container_width=True,
        )

    st.markdown("### Saved tasks")
    if not tasks:
        st.info("No tasks saved yet.")
    elif not matching_tasks:
        st.info("No saved tasks match your search.")
    else:
        for task in matching_tasks:
            actions = json_load(task["actions"])
            completed = json_load(task["completed"])
            total = len(actions)
            percent = round(len(completed) / total * 100) if total else 0

            with st.expander(task["title"]):
                st.caption(
                    f"Created: {task['created_at']} · "
                    f"{len(completed)}/{total} actions complete"
                )
                st.progress(percent / 100)

                for i, action in enumerate(actions):
                    prefix = "✅" if i in completed else "▫️"
                    st.markdown(f"{prefix} {action}")

                if st.button(
                    "Delete saved task",
                    key=f"delete_task_{task['id']}",
                ):
                    st.session_state.confirm_delete_task_id = task["id"]
                    st.rerun()

                if st.session_state.get("confirm_delete_task_id") == task["id"]:
                    st.warning("Delete this saved task permanently?")
                    confirm_col, cancel_col = st.columns(2)
                    with confirm_col:
                        if st.button(
                            "Confirm delete",
                            key=f"confirm_delete_task_{task['id']}",
                        ):
                            with get_db() as db:
                                delete_task_record(db, task["id"])

                            if st.session_state.task_db_id == task["id"]:
                                st.session_state.task_db_id = None
                                st.session_state.task_title = ""
                                st.session_state.task_actions = []
                                st.session_state.completed_actions = []
                                st.session_state.current_action = 0
                                st.session_state.task_active = False
                                st.session_state.task_finished = False
                                st.session_state.task_generation += 1

                            st.session_state.confirm_delete_task_id = None
                            st.rerun()
                    with cancel_col:
                        if st.button(
                            "Cancel",
                            key=f"cancel_delete_task_{task['id']}",
                        ):
                            st.session_state.confirm_delete_task_id = None
                            st.rerun()

    st.divider()
    st.markdown("### AI response history")

    if not responses:
        st.info("No AI responses saved yet.")
    elif not matching_responses:
        st.info("No AI responses match your search.")
    else:
        for response in matching_responses:
            with st.expander(
                f"{response['title']} · {response['created_at']}"
            ):
                st.markdown(response["content"])
                st.download_button(
                    "Download this response",
                    data=response["content"],
                    file_name="focusmate_response.md",
                    mime="text/markdown",
                    key=f"download_response_{response['id']}",
                    use_container_width=True,
                )

                if st.button(
                    "Delete saved response",
                    key=f"delete_response_{response['id']}",
                ):
                    st.session_state.confirm_delete_response_id = response["id"]
                    st.rerun()

                if (
                    st.session_state.get("confirm_delete_response_id")
                    == response["id"]
                ):
                    st.warning("Delete this saved response permanently?")
                    confirm_col, cancel_col = st.columns(2)
                    with confirm_col:
                        if st.button(
                            "Confirm delete",
                            key=f"confirm_delete_response_{response['id']}",
                        ):
                            with get_db() as db:
                                delete_response_record(db, response["id"])
                            st.session_state.confirm_delete_response_id = None
                            st.rerun()
                    with cancel_col:
                        if st.button(
                            "Cancel",
                            key=f"cancel_delete_response_{response['id']}",
                        ):
                            st.session_state.confirm_delete_response_id = None
                            st.rerun()


# ============================================================
# SHARED LAST RESPONSE
# ============================================================

if (
    st.session_state.page in {"Task Planner", "Text Simplifier", "Message Writer"}
    and st.session_state.last_response
):
    st.divider()
    st.markdown("### ✨ Your latest result")
    st.markdown(st.session_state.last_response)

    st.download_button(
        "⬇️ Download response (.md)",
        data=st.session_state.last_response,
        file_name="focusmate_response.md",
        mime="text/markdown",
        key="download_latest_response",
        use_container_width=True,
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()
st.caption(
    "FocusMate AI · AI productivity workspace · "
    "Review important AI-generated information before relying on it."
)
