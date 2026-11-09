import sqlite3
import tempfile
import unittest
from pathlib import Path

from focusmate_core import (
    build_history_export,
    delete_response_record,
    delete_task_record,
    extract_action_steps,
    filter_history,
    json_dump,
    json_load,
    open_database,
    undo_last_completed_action,
)


class JsonHelpersTests(unittest.TestCase):
    def test_json_dump_preserves_non_ascii_text(self):
        self.assertEqual(json_dump(["完成"]), '["完成"]')

    def test_json_load_reads_valid_json(self):
        self.assertEqual(json_load('["one", "two"]'), ["one", "two"])

    def test_json_load_uses_default_fallback_for_invalid_json(self):
        self.assertEqual(json_load("{"), [])

    def test_json_load_uses_supplied_fallback_for_invalid_json(self):
        fallback = {"status": "unknown"}
        self.assertIs(json_load(None, fallback), fallback)

    def test_build_history_export_preserves_records_and_unicode(self):
        payload = json_load(
            build_history_export(
                [
                    {
                        "id": 3,
                        "title": "完成 project",
                        "actions": '["Plan", "Review"]',
                        "completed": "[0]",
                        "finished": 0,
                        "created_at": "2026-11-09T10:00:00",
                    }
                ],
                [
                    {
                        "id": 8,
                        "title": "Draft",
                        "content": "Hello 🌱",
                        "created_at": "2026-11-09T10:05:00",
                    }
                ],
            )
        )

        self.assertEqual(payload["format_version"], 1)
        self.assertEqual(payload["tasks"][0]["actions"], ["Plan", "Review"])
        self.assertEqual(payload["tasks"][0]["completed"], [0])
        self.assertFalse(payload["tasks"][0]["finished"])
        self.assertEqual(payload["responses"][0]["content"], "Hello 🌱")

    def test_build_history_export_handles_empty_history(self):
        self.assertEqual(
            json_load(build_history_export([], [])),
            {"format_version": 1, "tasks": [], "responses": []},
        )

    def test_filter_history_is_case_insensitive_and_searches_multiple_fields(self):
        records = [
            {"title": "Plan a Project", "content": "Outline milestones"},
            {"title": "Meeting notes", "content": "Discuss the PROJECT launch"},
            {"title": "Personal reminder", "content": "Buy groceries"},
        ]

        matches = filter_history(records, " project ", ("title", "content"))

        self.assertEqual(matches, records[:2])

    def test_filter_history_returns_all_records_for_blank_query(self):
        records = [{"title": "First"}, {"title": "Second"}]
        self.assertEqual(filter_history(records, "  ", ("title",)), records)

    def test_filter_history_returns_no_records_when_query_does_not_match(self):
        records = [{"title": "First"}, {"title": "Second"}]
        self.assertEqual(filter_history(records, "missing", ("title",)), [])

    def test_undo_last_completed_action_removes_highest_step_index(self):
        self.assertEqual(undo_last_completed_action([0, 1, 2]), [0, 1])

    def test_undo_last_completed_action_handles_unsorted_indexes(self):
        self.assertEqual(undo_last_completed_action([3, 0, 2]), [0, 2])

    def test_undo_last_completed_action_handles_no_completed_steps(self):
        self.assertEqual(undo_last_completed_action([]), [])

    def test_open_database_commits_and_closes_connection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "focusmate.db"
            with open_database(database_path) as db:
                db.execute("CREATE TABLE entries (value TEXT NOT NULL)")
                db.execute("INSERT INTO entries VALUES (?)", ("saved",))

            with self.assertRaises(sqlite3.ProgrammingError):
                db.execute("SELECT * FROM entries")

            with open_database(database_path) as db:
                self.assertEqual(
                    db.execute("SELECT value FROM entries").fetchone()["value"],
                    "saved",
                )

    def test_open_database_rolls_back_failed_transactions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "focusmate.db"
            with open_database(database_path) as db:
                db.execute("CREATE TABLE entries (value TEXT NOT NULL)")

            with self.assertRaisesRegex(RuntimeError, "abort transaction"):
                with open_database(database_path) as db:
                    db.execute("INSERT INTO entries VALUES (?)", ("discarded",))
                    raise RuntimeError("abort transaction")

            with open_database(database_path) as db:
                self.assertEqual(
                    db.execute("SELECT COUNT(*) FROM entries").fetchone()[0],
                    0,
                )

    def test_delete_history_records_removes_only_the_selected_rows(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "focusmate.db"
            with open_database(database_path) as db:
                db.execute("CREATE TABLE tasks (id INTEGER PRIMARY KEY, title TEXT)")
                db.execute(
                    "CREATE TABLE responses (id INTEGER PRIMARY KEY, title TEXT)"
                )
                db.execute("INSERT INTO tasks VALUES (1, 'Keep'), (2, 'Delete')")
                db.execute(
                    "INSERT INTO responses VALUES (1, 'Keep'), (2, 'Delete')"
                )

            with open_database(database_path) as db:
                self.assertEqual(delete_task_record(db, 2), 1)
                self.assertEqual(delete_response_record(db, 2), 1)
                self.assertEqual(delete_task_record(db, 99), 0)
                self.assertEqual(delete_response_record(db, 99), 0)

            with open_database(database_path) as db:
                self.assertEqual(
                    db.execute("SELECT title FROM tasks").fetchall()[0]["title"],
                    "Keep",
                )
                self.assertEqual(
                    db.execute("SELECT title FROM responses").fetchall()[0]["title"],
                    "Keep",
                )


class ActionStepTests(unittest.TestCase):
    def test_extracts_steps_from_numbered_and_bulleted_text(self):
        text = (
            "Here is your plan:\n"
            "1. Gather the project requirements\n"
            "- Draft a short implementation plan\n"
            "Step 3: Review the results with the team"
        )
        self.assertEqual(
            extract_action_steps(text),
            [
                "Gather the project requirements",
                "Draft a short implementation plan",
                "Review the results with the team",
            ],
        )

    def test_skips_headings_short_lines_and_duplicate_steps(self):
        text = (
            "# Plan\n"
            "Steps\n"
            "1. No\n"
            "1. Prepare a list of project requirements\n"
            "Prepare a list of project requirements"
        )
        self.assertEqual(
            extract_action_steps(text),
            ["Prepare a list of project requirements"],
        )

    def test_limits_action_list_to_twelve_steps(self):
        text = "\n".join(
            f"{index}. Complete the project task number {index}"
            for index in range(1, 15)
        )
        self.assertEqual(len(extract_action_steps(text)), 12)


if __name__ == "__main__":
    unittest.main()
