
import requests
import streamlit as st

# ==========================================
# FOCUSMATE AI - ACCESSIBLE COGNITIVE CO-PILOT
# ==========================================

st.set_page_config(
    page_title="FocusMate AI",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="expanded"
)

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.2"


# ==========================================
# AI FUNCTION
# ==========================================

def get_ai_response(
    feature,
    user_text,
    response_length,
    language_style,
    one_step_mode,
    completed_steps=None
):
    if completed_steps is None:
        completed_steps = []

    instructions = {
        "Break down a task": (
            "Help the user make progress on their task "
            "with clear and practical actions."
        ),
        "Simplify text": (
            "Rewrite the supplied text in easier language. "
            "Preserve important facts and the original meaning."
        ),
        "Draft a message": (
            "Write a clear, respectful message based on the "
            "user's input. Do not invent facts or commitments."
        )
    }

    length_instructions = {
        "Short": "Be concise and use only essential information.",
        "Balanced": "Give useful detail without unnecessary explanation.",
        "Detailed": "Explain clearly with helpful details and examples."
    }

    if language_style == "Simple language":
        language_instruction = (
            "Use everyday words and short sentences. "
            "Explain difficult terms simply."
        )
    else:
        language_instruction = (
            "Use natural, clear language suitable for the topic."
        )

    if one_step_mode and feature == "Break down a task":
        completed_text = (
            "\n".join(
                f"- {step}" for step in completed_steps
            )
            if completed_steps
            else "No steps completed yet."
        )

        pacing_instruction = f"""
STRICT ONE-STEP MODE:

You must return EXACTLY ONE next actionable step.

Original task:
{user_text}

Steps already completed or previously shown:
{completed_text}

Rules:
1. Return only ONE action the user should take next.
2. Do not provide a full plan.
3. Do not provide a numbered list or multiple actions.
4. Do not repeat any completed or previously shown step.
5. Keep the response to 1-3 short sentences.
6. Start directly with the action.
7. Choose a realistic next action that moves the task forward.
8. Do not add an introduction, conclusion, or extra suggestions.

Return only the next step.
"""
    elif one_step_mode:
        pacing_instruction = (
            "Keep the response compact and focused on one main idea. "
            "Avoid multiple sections or unnecessary detail."
        )
    else:
        pacing_instruction = (
            "Provide a complete answer or full sequence of steps "
            "when appropriate. Organize it clearly."
        )

    prompt = f"""
Feature: {feature}

Task instructions:
{instructions[feature]}

Response length:
{length_instructions[response_length]}

Language preference:
{language_instruction}

Pacing:
{pacing_instruction}

User input:
{user_text}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are FocusMate AI, a supportive cognitive "
                        "co-pilot. Help users organize tasks, understand "
                        "information, and communicate clearly. "
                        "Respect individual preferences. Never diagnose "
                        "users or assume their abilities or needs. "
                        "Be patient, practical, respectful, and "
                        "non-judgmental. Keep the user in control. "
                        "Follow the user's requested output format exactly."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False,
            "options": {
                "temperature": 0.2
            }
        },
        timeout=180
    )

    response.raise_for_status()
    return response.json()["message"]["content"].strip()


# ==========================================
# SESSION STATE
# ==========================================

defaults = {
    "last_response": None,
    "last_input": None,
    "last_feature": None,
    "last_settings": None,
    "completed_steps": [],
    "task_finished": False,
    "last_error": None
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==========================================
# HEADER
# ==========================================

st.title("🧠 FocusMate AI")
st.subheader("Your Personal Cognitive Co-Pilot")

st.write(
    "Make tasks, information, and communication easier "
    "to manage — in the way that works for you."
)

st.info(
    "You choose how FocusMate AI responds. These settings are "
    "preferences, not assessments or diagnoses."
)


# ==========================================
# PERSONALIZATION SETTINGS
# ==========================================

with st.expander("⚙️ Personalize your experience", expanded=True):

    response_length = st.selectbox(
        "How much detail would you like?",
        ["Short", "Balanced", "Detailed"],
        index=1
    )

    language_style = st.radio(
        "Which language style do you prefer?",
        ["Simple language", "Standard language"],
        index=0
    )

    one_step_mode = st.checkbox(
        "One step at a time",
        value=False,
        help=(
            "For task breakdown, receive one next action at a time "
            "and continue when you're ready."
        )
    )


# ==========================================
# FEATURE SELECTION
# ==========================================

feature = st.selectbox(
    "What would you like help with?",
    [
        "Break down a task",
        "Simplify text",
        "Draft a message"
    ]
)

descriptions = {
    "Break down a task":
        "Turn a large task into smaller, manageable actions.",
    "Simplify text":
        "Make difficult information easier to understand.",
    "Draft a message":
        "Create a message that you can review and edit."
}

st.caption(descriptions[feature])


# ==========================================
# USER INPUT
# ==========================================

user_text = st.text_area(
    "Enter your task, text, or message",
    placeholder=(
        "Example: I need to prepare a database assignment "
        "by tomorrow..."
    ),
    height=180
)


# ==========================================
# GENERATE RESPONSE
# ==========================================

if st.button("✨ Help me get started", type="primary"):

    if not user_text.strip():
        st.warning("Please enter some text first.")

    else:
        try:
            with st.spinner("FocusMate AI is preparing your response..."):

                result = get_ai_response(
                    feature=feature,
                    user_text=user_text.strip(),
                    response_length=response_length,
                    language_style=language_style,
                    one_step_mode=one_step_mode,
                    completed_steps=[]
                )

            st.session_state.last_response = result
            st.session_state.last_input = user_text.strip()
            st.session_state.last_feature = feature

            st.session_state.last_settings = {
                "response_length": response_length,
                "language_style": language_style,
                "one_step_mode": one_step_mode
            }

            st.session_state.completed_steps = []
            st.session_state.task_finished = False
            st.session_state.last_error = None

            # Remember the first displayed action in one-step mode.
            if one_step_mode and feature == "Break down a task":
                st.session_state.completed_steps = [result]

        except requests.exceptions.ConnectionError:
            st.error(
                "Cannot connect to Ollama. Make sure Ollama is "
                "running on your computer."
            )

        except requests.exceptions.Timeout:
            st.error(
                "The AI took too long to respond. Please try again."
            )

        except requests.exceptions.RequestException as error:
            st.error(f"Could not generate a response: {error}")

        except (KeyError, ValueError):
            st.error(
                "The AI returned an unexpected response. "
                "Please try again."
            )


# ==========================================
# DISPLAY RESPONSE
# ==========================================

if st.session_state.last_response:

    st.divider()
    st.subheader("Your personalized assistance")

    if (
        st.session_state.last_settings
        and st.session_state.last_settings["one_step_mode"]
        and st.session_state.last_feature == "Break down a task"
    ):
        step_number = len(st.session_state.completed_steps)

        st.caption(f"Step {step_number}")

        st.markdown(st.session_state.last_response)

        st.caption(
            "Move at your own pace. You can continue when you're ready."
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "➡️ Next step",
                type="primary",
                disabled=st.session_state.task_finished
            ):
                try:
                    settings = st.session_state.last_settings

                    with st.spinner("Preparing your next step..."):
                        next_response = get_ai_response(
                            feature=st.session_state.last_feature,
                            user_text=st.session_state.last_input,
                            response_length=settings["response_length"],
                            language_style=settings["language_style"],
                            one_step_mode=True,
                            completed_steps=st.session_state.completed_steps
                        )

                    st.session_state.last_response = next_response
                    st.session_state.completed_steps.append(next_response)
                    st.session_state.last_error = None
                    st.rerun()

                except requests.exceptions.RequestException:
                    st.error(
                        "Could not generate the next step. "
                        "Check that Ollama is running and try again."
                    )

            if st.button("✅ I'm finished"):
                st.session_state.task_finished = True
                st.rerun()

        with col2:
            if st.button("🔄 Start task again"):
                st.session_state.last_response = None
                st.session_state.last_input = None
                st.session_state.last_feature = None
                st.session_state.last_settings = None
                st.session_state.completed_steps = []
                st.session_state.task_finished = False
                st.rerun()

        if st.session_state.task_finished:
            st.success("Well done! You've marked this task as finished.")

    else:
        st.markdown(st.session_state.last_response)

        st.caption(
            "Review the response and adjust it to suit your needs."
        )

    st.download_button(
        label="⬇️ Download response as text",
        data=st.session_state.last_response,
        file_name="focusmate_response.txt",
        mime="text/plain"
    )


# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "FocusMate AI | Version 0.4 | Local AI with user-controlled settings"
)

st.caption(
    "An assistive tool for learning, task management, "
    "and communication. Not a diagnostic tool."
)
