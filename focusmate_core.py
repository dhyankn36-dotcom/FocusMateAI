import json
import re
import sqlite3
from contextlib import contextmanager


def json_dump(value):
    return json.dumps(value, ensure_ascii=False)


def json_load(value, fallback=None):
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return fallback if fallback is not None else []


@contextmanager
def open_database(path):
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def delete_task_record(connection, task_id):
    return connection.execute(
        "DELETE FROM tasks WHERE id = ?", (task_id,)
    ).rowcount


def delete_response_record(connection, response_id):
    return connection.execute(
        "DELETE FROM responses WHERE id = ?", (response_id,)
    ).rowcount


def build_history_export(tasks, responses):
    task_records = [
        {
            "id": task["id"],
            "title": task["title"],
            "actions": json_load(task["actions"]),
            "completed": json_load(task["completed"]),
            "finished": bool(task["finished"]),
            "created_at": task["created_at"],
        }
        for task in tasks
    ]
    response_records = [
        {
            "id": response["id"],
            "title": response["title"],
            "content": response["content"],
            "created_at": response["created_at"],
        }
        for response in responses
    ]
    return json.dumps(
        {
            "format_version": 1,
            "tasks": task_records,
            "responses": response_records,
        },
        ensure_ascii=False,
        indent=2,
    )


def filter_history(records, query, fields):
    normalized_query = query.strip().casefold()
    if not normalized_query:
        return list(records)

    return [
        record
        for record in records
        if any(
            normalized_query in str(record[field]).casefold()
            for field in fields
            if record[field] is not None
        )
    ]


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
