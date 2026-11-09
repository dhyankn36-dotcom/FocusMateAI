import json
import re


def json_dump(value):
    return json.dumps(value, ensure_ascii=False)


def json_load(value, fallback=None):
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return fallback if fallback is not None else []


def extract_action_steps(text):
    actions = []
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
        if line not in actions:
            actions.append(line)

    return actions[:12]
