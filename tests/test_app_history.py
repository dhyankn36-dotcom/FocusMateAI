import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


class AppHistorySmokeTests(unittest.TestCase):
    def test_history_editors_render_in_both_apps(self):
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
                            "Smoke test task",
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
                            "Smoke test response",
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


if __name__ == "__main__":
    unittest.main()
