import json
import re


def json_dump(value):
    return json.dumps(value, ensure_ascii=False)


def json_load(value, fallback=None):
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return fallback if fallback is not None else []


def extract_ollama_content(payload):
    if not isinstance(payload, dict):
        return ""

    message = payload.get("message")
    if not isinstance(message, dict):
        return ""

    content = message.get("content")
    return content.strip() if isinstance(content, str) else ""


def extract_gemini_content(payload):
    if not isinstance(payload, dict):
        return ""

    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        return ""

    candidate = candidates[0]
    if not isinstance(candidate, dict):
        return ""

    content = candidate.get("content")
    if not isinstance(content, dict):
        return ""

    parts = content.get("parts")
    if not isinstance(parts, list):
        return ""

    answer = "".join(
        part["text"]
        for part in parts
        if isinstance(part, dict) and isinstance(part.get("text"), str)
    )
    return answer.strip()


def extract_gemini_error(payload):
    if not isinstance(payload, dict):
        return ""

    error = payload.get("error")
    if not isinstance(error, dict):
        return ""

    message = error.get("message")
    return message.strip() if isinstance(message, str) else ""


def extract_action_steps(text):
    actions = []
    seen = set()
    ignored = (
        "here is your plan", "here's your plan",
        "here is your first action", "here's your first action",
        "action plan", "here are the steps",
    )

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        line = re.sub(
            r"^(?:step\s*)?\d+\s*[\.\):\-]\s*",
            "", line, flags=re.IGNORECASE,
        )
        line = re.sub(r"^[-*•]\s*", "", line)
        line = re.sub(
            r"^step\s+\d+\s*[:\-]\s*",
            "", line, flags=re.IGNORECASE,
        )
        line = line.strip().strip("* ").strip()

        if len(line) < 5:
            continue

        lower = line.lower().strip("*# :")
        if any(lower.startswith(item) for item in ignored):
            continue
        if lower in {"steps", "plan", "your plan", "action plan"}:
            continue
        normalized = line.casefold()
        if normalized not in seen:
            actions.append(line)
            seen.add(normalized)

    return actions[:12]
