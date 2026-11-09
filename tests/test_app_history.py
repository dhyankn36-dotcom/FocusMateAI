import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


class AppHistoryTests(unittest.TestCase):
    def test_history_editors_render_and_persist_changes_in_both_apps(self):
        repository_root = Path(__file__).resolve().parents[1]

        for app_name in ("app.py", "app_cloud.py"):
            with self.subTest(app=app_name), tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                shutil.copy2(repository_root / app_name, temp_path / app_name)
                shutil.copy2(
                    repository_root / "focusmate_core.py",
                    temp_path / "focusmate_core.py",
                )

                app = AppTest.from_file(str(temp_path / app_name)).run(timeout=30)
                if app.exception:
                    self.fail(f"{app_name} startup failed: {app.exception}")

                db = sqlite3.connect(temp_path / "focusmate.db")
                try:
                    db.execute(
                        """INSERT INTO tasks
                           (title, actions, completed, finished, created_at)
                           VALUES (?, ?, ?, ?, ?)""",
                        (
                            "History test task",
                            '["Review notes"]',
                            "[]",
                            0,
                            "2026-11-09T10:00:00",
                        ),
                    )
                    db.execute(
                        """INSERT INTO responses (title, content, created_at)
                           VALUES (?, ?, ?)""",
                        (
                            "History test response",
                            "Response content for the history editor.",
                            "2026-11-09T10:00:00",
                        ),
                    )
                    db.commit()
                finally:
                    db.close()

                app.session_state["page"] = "History"
                app.run(timeout=30)
                if app.exception:
                    self.fail(f"{app_name} history failed: {app.exception}")

                self.assertTrue(
                    any(
                        widget.key == "rename_task_title_1"
                        for widget in app.text_input
                    )
                )
                self.assertTrue(
                    any(
                        widget.key == "rename_response_title_1"
                        for widget in app.text_input
                    )
                )
                self.assertTrue(
                    any(
                        widget.key == "edit_response_content_1"
                        for widget in app.text_area
                    )
                )

                app.text_input(key="rename_task_title_1").set_value(
                    "Updated history test task"
                )
                app.button(
                    key="FormSubmitter:rename_task_form_1-Save title"
                ).click()
                app.run(timeout=30)
                if app.exception:
                    self.fail(f"{app_name} task rename failed: {app.exception}")

                app.text_input(key="rename_response_title_1").set_value(
                    "Updated history test response"
                )
                app.button(
                    key="FormSubmitter:rename_response_form_1-Save title"
                ).click()
                app.run(timeout=30)
                if app.exception:
                    self.fail(f"{app_name} response rename failed: {app.exception}")

                app.text_area(key="edit_response_content_1").set_value(
                    "Edited history test response content."
                )
                app.button(
                    key="FormSubmitter:edit_response_form_1-Save response"
                ).click()
                app.run(timeout=30)
                if app.exception:
                    self.fail(f"{app_name} response edit failed: {app.exception}")

                app.text_input(key="rename_task_title_1").set_value("  ")
                app.button(
                    key="FormSubmitter:rename_task_form_1-Save title"
                ).click()
                app.run(timeout=30)
                self.assertTrue(
                    any(
                        "Task title cannot be empty." in item.value
                        for item in app.error
                    )
                )

                app.text_input(key="rename_response_title_1").set_value("  ")
                app.button(
                    key="FormSubmitter:rename_response_form_1-Save title"
                ).click()
                app.run(timeout=30)
                self.assertTrue(
                    any(
                        "Response title cannot be empty." in item.value
                        for item in app.error
                    )
                )

                app.text_area(key="edit_response_content_1").set_value("  ")
                app.button(
                    key="FormSubmitter:edit_response_form_1-Save response"
                ).click()
                app.run(timeout=30)
                self.assertTrue(
                    any(
                        "Response content cannot be empty." in item.value
                        for item in app.error
                    )
                )

                app.button(key="duplicate_response_1").click()
                app.run(timeout=30)
                if app.exception:
                    self.fail(f"{app_name} response duplication failed: {app.exception}")
                self.assertTrue(
                    any(
                        "A copy of this response was saved." in item.value
                        for item in app.success
                    )
                )

                db = sqlite3.connect(temp_path / "focusmate.db")
                try:
                    task = db.execute(
                        "SELECT title FROM tasks WHERE id = 1"
                    ).fetchone()
                    responses = db.execute(
                        "SELECT title, content FROM responses WHERE id = 1"
                    ).fetchone(), db.execute(
                        "SELECT title, content FROM responses WHERE id = 2"
                    ).fetchone()
                finally:
                    db.close()

                self.assertEqual(task[0], "Updated history test task")
                self.assertEqual(
                    responses[0][0], "Updated history test response"
                )
                self.assertEqual(
                    responses[0][1], "Edited history test response content."
                )
                self.assertEqual(
                    responses[1][0], "Updated history test response (copy)"
                )
                self.assertEqual(
                    responses[1][1], "Edited history test response content."
                )


if __name__ == "__main__":
    unittest.main()
