import json
import tempfile
import unittest
from pathlib import Path

from focusmate_core import import_history_json, open_database


class HistoryImportValidationTests(unittest.TestCase):
    def create_database(self, path):
        with open_database(path) as db:
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

    def test_import_validates_all_records_before_inserting_any(self):
        payload = {
            "format_version": 1,
            "tasks": [
                {
                    "title": "Valid task",
                    "actions": ["Plan the work"],
                    "completed": [],
                    "finished": False,
                    "created_at": "2026-11-13T10:00:00",
                }
            ],
            "responses": [
                {
                    "title": "Invalid response",
                    "content": None,
                    "created_at": "2026-11-13T10:05:00",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "focusmate.db"
            self.create_database(database_path)

            with self.assertRaisesRegex(ValueError, "invalid response"):
                with open_database(database_path) as db:
                    import_history_json(db, json.dumps(payload))

            with open_database(database_path) as db:
                self.assertEqual(
                    db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],
                    0,
                )
                self.assertEqual(
                    db.execute("SELECT COUNT(*) FROM responses").fetchone()[0],
                    0,
                )

    def test_reimporting_same_history_does_not_create_duplicates(self):
        payload = {
            "format_version": 1,
            "tasks": [
                {
                    "title": "Prepare report",
                    "actions": ["Collect data"],
                    "completed": [0],
                    "finished": True,
                    "created_at": "2026-11-13T10:00:00",
                }
            ],
            "responses": [
                {
                    "title": "Report notes",
                    "content": "Summary of the report.",
                    "created_at": "2026-11-13T10:05:00",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "focusmate.db"
            self.create_database(database_path)

            with open_database(database_path) as db:
                self.assertEqual(
                    import_history_json(db, json.dumps(payload)),
                    (1, 1),
                )
            with open_database(database_path) as db:
                self.assertEqual(
                    import_history_json(db, json.dumps(payload)),
                    (0, 0),
                )
                self.assertEqual(
                    db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],
                    1,
                )
                self.assertEqual(
                    db.execute("SELECT COUNT(*) FROM responses").fetchone()[0],
                    1,
                )


    def test_import_rejects_invalid_task_timestamp_before_writing(self):
        payload = {
            "format_version": 1,
            "tasks": [
                {
                    "title": "Task with invalid date",
                    "actions": ["Review"],
                    "completed": [],
                    "finished": False,
                    "created_at": "not-a-timestamp",
                }
            ],
            "responses": [],
        }

        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "focusmate.db"
            self.create_database(database_path)

            with self.assertRaisesRegex(ValueError, "invalid task"):
                with open_database(database_path) as db:
                    import_history_json(db, json.dumps(payload))

            with open_database(database_path) as db:
                self.assertEqual(
                    db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],
                    0,
                )

    def test_import_rejects_invalid_response_timestamp(self):
        payload = {
            "format_version": 1,
            "tasks": [],
            "responses": [
                {
                    "title": "Response with invalid date",
                    "content": "Notes",
                    "created_at": "yesterday",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "focusmate.db"
            self.create_database(database_path)

            with self.assertRaisesRegex(ValueError, "invalid response"):
                with open_database(database_path) as db:
                    import_history_json(db, json.dumps(payload))


if __name__ == "__main__":
    unittest.main()
