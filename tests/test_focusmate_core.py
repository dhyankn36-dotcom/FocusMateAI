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
    find_resumable_task,
    json_dump,
    json_load,
    open_database,
    import_history_json,
    task_stats,
    undo_last_completed_action,
    valid_completed_actions,
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

    def test_task_stats_counts_totals_and_active_tasks(self):
        tasks = [
            {
                "actions": '["Plan", "Build", "Review"]',
                "completed": "[0, 0, 99, -1, true, \"1\"]",
                "finished": 0,
            },
            {
                "actions": '["Write", "Share"]',
                "completed": "[0, 1]",
                "finished": 1,
            },
            {
                "actions": "invalid",
                "completed": "[]",
                "finished": 0,
            },
        ]

        self.assertEqual(task_stats(tasks), (3, 1, 1, 5, 3))

    def test_task_stats_handles_empty_history(self):
        self.assertEqual(task_stats([]), (0, 0, 0, 0, 0))

    def test_find_resumable_task_skips_finished_and_completed_tasks(self):
        tasks = [
            {
                "id": 3,
                "title": "Finished",
                "actions": '["Only action"]',
                "completed": "[0]",
                "finished": 1,
            },
            {
                "id": 2,
                "title": "Already complete",
                "actions": '["Only action"]',
                "completed": "[0]",
                "finished": 0,
            },
            {
                "id": 1,
                "title": "Continue this",
                "actions": '["First", "Second"]',
                "completed": "[0]",
                "finished": 0,
            },
        ]

        self.assertEqual(find_resumable_task(tasks)["id"], 1)

    def test_find_resumable_task_ignores_invalid_progress_and_empty_plans(self):
        tasks = [
            {
                "id": 2,
                "title": "Empty",
                "actions": "[]",
                "completed": "[]",
                "finished": 0,
            },
            {
                "id": 1,
                "title": "Resume",
                "actions": '["First", "Second"]',
                "completed": "[99, -1, true]",
                "finished": 0,
            },
        ]

        self.assertEqual(find_resumable_task(tasks)["id"], 1)
        self.assertIsNone(find_resumable_task(tasks[:1]))

    def test_valid_completed_actions_filters_invalid_indexes_and_duplicates(self):
        self.assertEqual(
            valid_completed_actions(["First", "Second"], [1, 0, 1, -1, 9, True]),
            [0, 1],
        )

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


class HistoryImportTests(unittest.TestCase):
    def create_database(self, database_path):
        with open_database(database_path) as db:
            db.execute("""
                CREATE TABLE tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    actions TEXT NOT NULL,
                    completed TEXT NOT NULL,
                    finished INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            db.execute("""
                CREATE TABLE responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

    def test_imports_exported_records_without_reusing_record_ids(self):
        export = build_history_export(
            [
                {
                    "id": 40,
                    "title": "Plan",
                    "actions": '["Research", "Write"]',
                    "completed": "[0]",
                    "finished": False,
                    "created_at": "2026-11-09T10:00:00",
                }
            ],
            [
                {
                    "id": 50,
                    "title": "Notes",
                    "content": "Saved response",
                    "created_at": "2026-11-09T10:05:00",
                }
            ],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "focusmate.db"
            self.create_database(database_path)
            with open_database(database_path) as db:
                self.assertEqual(import_history_json(db, export), (1, 1))
                self.assertEqual(import_history_json(db, export), (0, 0))
                tasks = db.execute(
                    "SELECT id, title, actions, completed FROM tasks ORDER BY id"
                ).fetchall()
                responses = db.execute(
                    "SELECT id, title, content FROM responses ORDER BY id"
                ).fetchall()

            self.assertEqual([task["id"] for task in tasks], [1])
            self.assertEqual(tasks[0]["completed"], "[0]")
            self.assertEqual([response["id"] for response in responses], [1])

    def test_rejects_malformed_history_before_inserting_any_records(self):
        payload = {
            "format_version": 1,
            "tasks": [
                {
                    "title": "Valid task",
                    "actions": ["Action"],
                    "completed": [0],
                    "finished": False,
                    "created_at": "2026-11-09T10:00:00",
                }
            ],
            "responses": [{"title": "Invalid response"}],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "focusmate.db"
            self.create_database(database_path)
            with self.assertRaisesRegex(ValueError, "invalid response"):
                with open_database(database_path) as db:
                    import_history_json(db, json_dump(payload))

            with open_database(database_path) as db:
                self.assertEqual(
                    db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],
                    0,
                )

    def test_rejects_unsupported_versions_and_invalid_step_indexes(self):
        payload = {
            "format_version": 1,
            "tasks": [
                {
                    "title": "Plan",
                    "actions": ["Action"],
                    "completed": [1],
                    "finished": False,
                    "created_at": "2026-11-09T10:00:00",
                }
            ],
            "responses": [],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "focusmate.db"
            self.create_database(database_path)
            with open_database(database_path) as db:
                with self.assertRaisesRegex(ValueError, "invalid task"):
                    import_history_json(db, json_dump(payload))
                payload["format_version"] = True
                with self.assertRaisesRegex(ValueError, "Unsupported"):
                    import_history_json(db, json_dump(payload))

    def test_rejects_oversized_and_non_utf8_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "focusmate.db"
            self.create_database(database_path)
            with open_database(database_path) as db:
                with self.assertRaisesRegex(ValueError, "5 MB"):
                    import_history_json(db, b" " * (5_000_001))
                with self.assertRaisesRegex(ValueError, "UTF-8"):
                    import_history_json(db, b"\xff")


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
