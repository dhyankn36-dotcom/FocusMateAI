import json
import os
import re
import sqlite3
from contextlib import contextmanager
from urllib.parse import urlparse

MAX_TASK_INPUT_CHARS = 2_000
MAX_SIMPLIFY_INPUT_CHARS = 10_000
MAX_RECIPIENT_CHARS = 120
MAX_MESSAGE_PURPOSE_CHARS = 3_000
MAX_HISTORY_IMPORT_BYTES = 5_000_000


def get_ollama_config(environ=None):
    settings = os.environ if environ is None else environ
    url = settings.get(
        "FOCUSMATE_OLLAMA_URL", "http://localhost:11434/api/chat"
    ).strip()
    model = settings.get("FOCUSMATE_OLLAMA_MODEL", "llama3.2").strip()
    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError("FOCUSMATE_OLLAMA_URL must be an HTTP or HTTPS URL.")
    if not model:
        raise ValueError("FOCUSMATE_OLLAMA_MODEL must not be empty.")
    return url, model


def json_dump(value):
    return json.dumps(value, ensure_ascii=False)


def response_filename(title):
    slug = re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-")[:80].strip("-")
    return f"{slug or 'focusmate-response'}.md"


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


def load_response_page(connection, limit, offset):
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("Page size must be a positive integer.")
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError("Page offset must be a non-negative integer.")

    return connection.execute(
        "SELECT * FROM responses ORDER BY id DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()


def paginate_records(records, limit, offset):
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("Page size must be a positive integer.")
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError("Page offset must be a non-negative integer.")

    return list(records[offset:offset + limit])


def count_response_records(connection):
    return connection.execute("SELECT COUNT(*) FROM responses").fetchone()[0]


def delete_task_record(connection, task_id):
    return connection.execute(
        "DELETE FROM tasks WHERE id = ?", (task_id,)
    ).rowcount


def delete_response_record(connection, response_id):
    return connection.execute(
        "DELETE FROM responses WHERE id = ?", (response_id,)
    ).rowcount


def undo_last_completed_action(completed):
    if not completed:
        return []

    last_action = max(completed)
    return [action for action in completed if action != last_action]


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


def import_history_json(connection, content):
    if isinstance(content, bytes):
        if len(content) > MAX_HISTORY_IMPORT_BYTES:
            raise ValueError("The history file exceeds the 5 MB import limit.")
        try:
            content = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("The history file must be UTF-8 encoded JSON.") from exc
    elif isinstance(content, str):
        if len(content.encode("utf-8")) > MAX_HISTORY_IMPORT_BYTES:
            raise ValueError("The history file exceeds the 5 MB import limit.")
    else:
        raise ValueError("The history file must contain JSON text.")

    try:
        payload = json.loads(content)
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ValueError("The history file is not valid JSON.") from exc

    if (
        not isinstance(payload, dict)
        or type(payload.get("format_version")) is not int
        or payload["format_version"] != 1
    ):
        raise ValueError("Unsupported history file format.")

    tasks = payload.get("tasks")
    responses = payload.get("responses")
    if not isinstance(tasks, list) or not isinstance(responses, list):
        raise ValueError("History file must contain task and response lists.")

    valid_tasks = []
    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("History contains an invalid task record.")

        title = task.get("title")
        actions = task.get("actions")
        completed = task.get("completed")
        created_at = task.get("created_at")
        finished = task.get("finished")
        if (
            not isinstance(title, str)
            or not title.strip()
            or not isinstance(actions, list)
            or any(not isinstance(action, str) for action in actions)
            or not isinstance(completed, list)
            or any(
                not isinstance(index, int)
                or isinstance(index, bool)
                or index < 0
                or index >= len(actions)
                for index in completed
            )
            or not isinstance(finished, bool)
            or not isinstance(created_at, str)
        ):
            raise ValueError("History contains an invalid task record.")

        valid_tasks.append(
            (title, json_dump(actions), json_dump(sorted(set(completed))),
             int(finished), created_at)
        )

    valid_responses = []
    for response in responses:
        if not isinstance(response, dict):
            raise ValueError("History contains an invalid response record.")

        title = response.get("title")
        response_content = response.get("content")
        created_at = response.get("created_at")
        if (
            not isinstance(title, str)
            or not title.strip()
            or not isinstance(response_content, str)
            or not isinstance(created_at, str)
        ):
            raise ValueError("History contains an invalid response record.")

        valid_responses.append((title, response_content, created_at))

    imported_tasks = 0
    for task in valid_tasks:
        cursor = connection.execute(
            """INSERT INTO tasks (title, actions, completed, finished, created_at)
               SELECT ?, ?, ?, ?, ?
               WHERE NOT EXISTS (
                   SELECT 1 FROM tasks
                   WHERE title = ? AND actions = ? AND completed = ?
                     AND finished = ? AND created_at = ?
               )""",
            task + task,
        )
        imported_tasks += cursor.rowcount

    imported_responses = 0
    for response in valid_responses:
        cursor = connection.execute(
            """INSERT INTO responses (title, content, created_at)
               SELECT ?, ?, ?
               WHERE NOT EXISTS (
                   SELECT 1 FROM responses
                   WHERE title = ? AND content = ? AND created_at = ?
               )""",
            response + response,
        )
        imported_responses += cursor.rowcount

    return imported_tasks, imported_responses


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


def filter_tasks_by_status(tasks, status):
    if status == "All tasks":
        return list(tasks)
    if status not in {"In progress", "Completed"}:
        raise ValueError("Task status must be All tasks, In progress, or Completed.")

    finished = status == "Completed"
    return [task for task in tasks if bool(task["finished"]) is finished]


def valid_completed_actions(actions, completed):
    if not isinstance(actions, list) or not isinstance(completed, list):
        return []

    return sorted(
        {
            index
            for index in completed
            if isinstance(index, int)
            and not isinstance(index, bool)
            and 0 <= index < len(actions)
        }
    )


def task_stats(tasks):
    total_tasks = len(tasks)
    finished_tasks = 0
    active_tasks = 0
    total_actions = 0
    completed_actions = 0

    for task in tasks:
        actions = json_load(task["actions"])
        if not isinstance(actions, list):
            actions = []

        raw_completed = json_load(task["completed"])
        if not isinstance(raw_completed, list):
            raw_completed = []

        completed = valid_completed_actions(actions, raw_completed)

        is_finished = bool(task["finished"])
        finished_tasks += int(is_finished)
        active_tasks += int(not is_finished and bool(actions))
        total_actions += len(actions)
        completed_actions += len(completed)

    return (
        total_tasks,
        finished_tasks,
        active_tasks,
        total_actions,
        completed_actions,
    )


def find_resumable_task(tasks):
    for task in tasks:
        actions = json_load(task["actions"])
        if not isinstance(actions, list) or not actions:
            continue

        completed = json_load(task["completed"])
        if not isinstance(completed, list):
            completed = []

        valid_completed = valid_completed_actions(actions, completed)
        if not task["finished"] and len(valid_completed) < len(actions):
            return task

    return None


def extract_ollama_content(payload):
    if not isinstance(payload, dict):
        return ""

    message = payload.get("message")
    if not isinstance(message, dict):
        return ""

    content = message.get("content")
    return content.strip() if isinstance(content, str) else ""


def extract_ollama_error(payload):
    if not isinstance(payload, dict):
        return ""

    error = payload.get("error")
    return error.strip() if isinstance(error, str) else ""


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
