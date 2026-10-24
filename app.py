
import re
import requests
import streamlit as st

# =========================================================
# FOCUSMATE AI
# =========================================================

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2"

st.set_page_config(
    page_title="FocusMate AI",
    page_icon="🎯",
    layout="centered",
)

st.title("🎯 FocusMate AI")
st.caption("Your Personal Cognitive Co-Pilot")
st.write(
    "Turn overwhelming tasks into manageable actions, "
    "simplify difficult text, and draft clear messages."
)

# =========================================================
# SESSION STATE
# =========================================================

DEFAULTS = {
    "task_steps": [],
    "current_step": 0,
    "completed_steps": [],
    "active_task": "",
    "task_finished": False,
    "last_response": "",
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# PERSONALIZATION
# =========================================================

with st.sidebar:
    st.header("⚙️ Personalization")

    response_length = st.selectbox(
        "Response length",
        ["Short", "Balanced", "Detailed"],
        index=1,
    )

    language_style = st.selectbox(
        "Language style",
        ["Simple", "Standard"],
        index=0,
    )

    one_step_mode = st.toggle(
        "One step at a time",
        value=True,
    )

    st.divider()
    st.caption("AI runs locally through Ollama.")
    st.caption(f"Model: {MODEL}")


# =========================================================
# AI HELPER FUNCTIONS
# =========================================================

def build_system_prompt():
    length_instructions = {
        "Short": "Keep answers concise.",
        "Balanced": "Give clear, useful explanations.",
        "Detailed": "Explain thoroughly with practical examples.",
    }

    style_instructions = {
        "Simple": "Use beginner-friendly language and explain jargon.",
        "Standard": "Use clear, professional language.",
    }

    return (
        "You are FocusMate AI, a practical productivity assistant. "
        "Be clear, supportive, and accurate. Do not invent facts. "
        "Do not claim a task is complete unless the user confirms it. "
        f"{length_instructions[response_length]} "
        f"{style_instructions[language_style]}"
    )


def ask_ollama(prompt, system_prompt):
    payload = {
        "model": MODEL,
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=120,
    )

    response.raise_for_status()

    data = response.json()
    return data["message"]["content"].strip()


def extract_action_steps(result):
    """Extract actionable steps and ignore headings and introductions."""

    steps = []

    ignored_phrases = {
        "here's your first action",
        "here is your first action",
        "here are your steps",
        "here are the steps",
        "here is your action plan",
        "here's your action plan",
        "your action plan",
        "action plan",
        "steps",
    }

    for line in result.splitlines():
        cleaned = line.strip()

        if not cleaned:
            continue

        # Remove Markdown formatting and numbered-list prefixes.
        cleaned = re.sub(r"^\s*#{1,6}\s*", "", cleaned)
        cleaned = re.sub(
            r"^\s*(?:[-*•]\s*|\d+[\.\)]\s*)",
            "",
            cleaned,
        ).strip()

        if not cleaned:
            continue

        normalized = cleaned.lower().strip(" :.-")

        # Ignore known introductory headings.
        if normalized in ignored_phrases:
            continue

        # Ignore short heading-like introductions ending in a colon.
        if cleaned.endswith(":") and len(cleaned.split()) <= 10:
            continue

        # Ignore generic introductions that are not actions.
        if normalized.startswith(
            (
                "here's your first action",
                "here is your first action",
                "here are your steps",
                "here is your action plan",
                "let's break this down",
            )
        ):
            continue

        steps.append(cleaned)

    return steps


def reset_task():
    st.session_state.task_steps = []
    st.session_state.current_step = 0
    st.session_state.completed_steps = []
    st.session_state.active_task = ""
    st.session_state.task_finished = False


def handle_ollama_error(error):
    if isinstance(error, requests.exceptions.ConnectionError):
        st.error(
            "Cannot connect to Ollama. Make sure Ollama is running. "
            "You can start it with `ollama run llama3.2`."
        )
    elif isinstance(error, requests.exceptions.Timeout):
        st.error(
            "Ollama took too long to respond. Please try again."
        )
    elif isinstance(error, requests.exceptions.HTTPError):
        st.error(
            f"Ollama returned an HTTP error: {error}"
        )
    elif isinstance(error, (ValueError, KeyError, TypeError)):
        st.error(
            "The response from Ollama was unexpected. Please try again."
        )
    else:
        st.error(f"Something went wrong: {error}")


# =========================================================
# MAIN FEATURE SELECTOR
# =========================================================

feature = st.radio(
    "What would you like help with?",
    [
        "Break down a task",
        "Simplify text",
        "Draft a message",
    ],
    horizontal=False,
)


# =========================================================
# FEATURE 1: BREAK DOWN A TASK
# =========================================================

if feature == "Break down a task":
    st.subheader("🧩 Break down your task")

    task = st.text_area(
        "What do you need to accomplish?",
        placeholder="Example: Prepare for my DAA exam.",
        height=110,
        key="task_input",
    )

    if st.button(
        "Create my action plan",
        type="primary",
    ):
        if not task.strip():
            st.warning("Please enter a task first.")

        else:
            system_prompt = build_system_prompt() + (
                "\nYou are creating an actionable task plan. "
                "Return only a numbered list of 5 to 8 concrete steps. "
                "Each numbered line must contain one specific action. "
                "Do not include an introduction, heading, conclusion, "
                "or commentary. Start directly with step 1. "
                "Avoid vague actions. Make the steps achievable "
                "and relevant to the user's task."
            )

            prompt = (
                "Create a practical action plan for this task:\n"
                f"{task.strip()}\n\n"
                "Return 5 to 8 numbered actions. "
                "Each action should begin on a new line."
            )

            with st.spinner("Creating your action plan..."):
                try:
                    result = ask_ollama(
                        prompt,
                        system_prompt,
                    )

                    steps = extract_action_steps(result)

                    if not steps:
                        st.error(
                            "The AI didn't return clear action steps. "
                            "Please try again."
                        )

                    else:
                        st.session_state.task_steps = steps
                        st.session_state.current_step = 0
                        st.session_state.completed_steps = []
                        st.session_state.active_task = task.strip()
                        st.session_state.task_finished = False
                        st.session_state.last_response = result

                except (
                    requests.exceptions.RequestException,
                    ValueError,
                    KeyError,
                    TypeError,
                ) as error:
                    handle_ollama_error(error)

    # Display the generated action plan.
    if st.session_state.task_steps:
        st.divider()
        st.subheader("📍 Your action plan")

        st.write(
            f"**Task:** {st.session_state.active_task}"
        )

        steps = st.session_state.task_steps
        completed = st.session_state.completed_steps

        total = len(steps)
        done_count = len(completed)

        progress = done_count / total if total else 0

        st.progress(progress)
        st.caption(
            f"{done_count} of {total} actions marked complete"
        )

        if st.session_state.task_finished:
            st.success(
                "🎉 You've marked this task as finished!"
            )

        elif one_step_mode:
            current = st.session_state.current_step

            if current < total:
                st.markdown(
                    f"### Action {current + 1} of {total}"
                )

                st.info(steps[current])

                col1, col2 = st.columns(2)

                with col1:
                    if st.button(
                        "✅ Mark complete",
                        disabled=current in completed,
                        use_container_width=True,
                    ):
                        if current not in completed:
                            completed.append(current)

                        st.session_state.completed_steps = completed
                        st.rerun()

                with col2:
                    if st.button(
                        "➡️ Next action",
                        disabled=current >= total - 1,
                        use_container_width=True,
                    ):
                        st.session_state.current_step = current + 1
                        st.rerun()

                if current == total - 1:
                    if st.button(
                        "🏁 Finish task",
                        type="primary",
                        use_container_width=True,
                    ):
                        if current not in completed:
                            completed.append(current)

                        st.session_state.completed_steps = completed
                        st.session_state.task_finished = True
                        st.rerun()

            else:
                st.success("You've reached the end of the action plan.")

                if st.button(
                    "🏁 Finish task",
                    type="primary",
                ):
                    st.session_state.task_finished = True
                    st.rerun()

        else:
            # Use unique keys for checkboxes so Streamlit
            # can preserve their state across reruns.
            for index, step in enumerate(steps):
                is_done = index in completed

                checked = st.checkbox(
                    step,
                    value=is_done,
                    key=f"task_step_{index}",
                )

                if checked and not is_done:
                    completed.append(index)

                elif not checked and is_done:
                    completed.remove(index)

            st.session_state.completed_steps = completed

            if st.button(
                "🏁 Mark task finished",
                type="primary",
            ):
                if len(completed) == total:
                    st.session_state.task_finished = True
                    st.rerun()
                else:
                    st.warning(
                        "Complete all actions before marking "
                        "the task finished."
                    )

        with st.expander("View the full action plan"):
            for index, step in enumerate(steps):
                marker = (
                    "✅"
                    if index in completed
                    else "⬜"
                )

                st.write(
                    f"{marker} {index + 1}. {step}"
                )

        if st.button("🔄 Start a new task"):
            reset_task()
            st.rerun()


# =========================================================
# FEATURE 2: SIMPLIFY TEXT
# =========================================================

elif feature == "Simplify text":
    st.subheader("📖 Simplify difficult text")

    text_to_simplify = st.text_area(
        "Paste the text you want explained",
        placeholder="Paste a paragraph, concept, or notes here...",
        height=180,
    )

    if st.button(
        "Simplify text",
        type="primary",
    ):
        if not text_to_simplify.strip():
            st.warning("Please paste some text first.")

        else:
            prompt = (
                "Explain the following text in easier language. "
                "Preserve its important meaning, define difficult "
                "terms, and include an example where useful.\n\n"
                f"{text_to_simplify.strip()}"
            )

            with st.spinner("Simplifying the text..."):
                try:
                    result = ask_ollama(
                        prompt,
                        build_system_prompt(),
                    )

                    st.session_state.last_response = result

                    st.markdown("### Simplified explanation")
                    st.write(result)

                except (
                    requests.exceptions.RequestException,
                    ValueError,
                    KeyError,
                    TypeError,
                ) as error:
                    handle_ollama_error(error)


# =========================================================
# FEATURE 3: DRAFT A MESSAGE
# =========================================================

elif feature == "Draft a message":
    st.subheader("✍️ Draft a message")

    recipient = st.text_input(
        "Who is the message for?",
        placeholder="Example: My professor",
    )

    purpose = st.text_area(
        "What do you want to communicate?",
        placeholder="Explain your purpose and important details...",
        height=120,
    )

    tone = st.selectbox(
        "Tone",
        [
            "Friendly",
            "Professional",
            "Polite",
            "Casual",
        ],
    )

    if st.button(
        "Draft my message",
        type="primary",
    ):
        if not purpose.strip():
            st.warning(
                "Please describe what you want to communicate."
            )

        else:
            prompt = (
                f"Draft a {tone.lower()} message for "
                f"{recipient.strip() or 'the recipient'}. "
                "Use the user's intent and details without "
                "inventing facts. Return a complete draft that "
                "the user can review and edit.\n\n"
                f"Purpose and details: {purpose.strip()}"
            )

            with st.spinner("Drafting your message..."):
                try:
                    result = ask_ollama(
                        prompt,
                        build_system_prompt(),
                    )

                    st.session_state.last_response = result

                    st.markdown("### Your message draft")
                    st.write(result)

                except (
                    requests.exceptions.RequestException,
                    ValueError,
                    KeyError,
                    TypeError,
                ) as error:
                    handle_ollama_error(error)


# =========================================================
# DOWNLOAD LAST RESPONSE
# =========================================================

if st.session_state.last_response:
    st.divider()

    st.download_button(
        "⬇️ Download last response",
        data=st.session_state.last_response,
        file_name="focusmate_response.txt",
        mime="text/plain",
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "FocusMate AI uses your local Ollama server. "
    "AI-generated suggestions can be incorrect, so review "
    "them before relying on them."
)
