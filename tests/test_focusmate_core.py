import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path

from focusmate_core import (
    build_history_export,
    build_task_markdown,
    delete_response_record,
    delete_task_record,
    extract_action_steps,
    filter_history,
    filter_records_by_date,
    filter_tasks_by_status,
    find_resumable_task,
    get_ollama_config,
    json_dump,
    json_load,
    open_database,
    import_history_json,
    count_response_records,
    load_response_page,
    paginate_records,
    response_filename,
    sort_response_records,
    sort_task_records,
    task_stats,
    task_is_completed,
    undo_last_completed_action,
    valid_completed_actions,
)


class JsonHelpersTests(unittest.TestCase):
    def test_response_filename_uses_safe_title_slug(self):
        self.assertEqual(
            response_filename("../../Project Plan: Week 1"),
            "project-plan-week-1.md",
        )

    def test_response_filename_falls_back_when_title_has_no_ascii_slug(self):
        self.assertEqual(response_filename("完成"), "focusmate-response.md")

    def test_response_filename_limits_slug_length(self):
        filename = response_filename("a" * 100)
        self.assertEqual(filename, f"{'a' * 80}.md")

    def test_ollama_config_uses_defaults(self):
        self.assertEqual(
            get_ollama_config({}),
            ("http://localhost:11434/api/chat", "llama3.2"),
        )

    def test_ollama_config_accepts_custom_server_and_model(self):
        self.assertEqual(
            get_ollama_config(
                {
                    "FOCUSMATE_OLLAMA_URL": "https://ai.example.test/api/chat",
                    "FOCUSMATE_OLLAMA_MODEL": "custom-model",
                }
            ),
            ("https://ai.example.test/api/chat", "custom-model"),
        )

    def test_ollama_config_rejects_invalid_server_urls(self):
        for url in ("", "localhost:11434", "ftp://example.test/api"):
            with self.subTest(url=url):
                with self.assertRaisesRegex(ValueError, "HTTP or HTTPS"):
                    get_ollama_config({"FOCUSMATE_OLLAMA_URL": url})

    def test_ollama_config_rejects_empty_model(self):
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            get_ollama_config({"FOCUSMATE_OLLAMA_MODEL": "  "})

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

    def test_build_history_export_corrects_completed_progress_status(self):
        payload = json_load(
            build_history_export(
                [
                    {
                        "id": 1,
                        "title": "Finished by progress",
                        "actions": '["One"]',
                        "completed": "[0]",
                        "finished": 0,
                        "created_at": "2026-11-09T10:00:00",
                    }
                ],
                [],
            )
        )

        self.assertTrue(payload["tasks"][0]["finished"])

    def test_filtered_history_export_contains_all_matching_records(self):
        tasks = [
            {
                "id": 1,
                "title": "Project plan",
                "actions": '["Write project brief"]',
                "completed": "[]",
                "finished": 0,
                "created_at": "2026-11-09T10:00:00",
            },
            {
                "id": 2,
                "title": "Finished project",
                "actions": '["Review project"]',
                "completed": "[0]",
                "finished": 1,
                "created_at": "2026-11-09T10:05:00",
            },
            {
                "id": 3,
                "title": "Personal plan",
                "actions": '["Buy groceries"]',
                "completed": "[]",
                "finished": 0,
                "created_at": "2026-11-09T10:10:00",
            },
        ]
        responses = [
            {
                "id": 4,
                "title": "Project notes",
                "content": "Project notes",
                "created_at": "2026-11-09T10:15:00",
            },
            {
                "id": 5,
                "title": "Shopping list",
                "content": "Groceries",
                "created_at": "2026-11-09T10:20:00",
            },
        ]
        matching_tasks = filter_tasks_by_status(
            filter_history(tasks, "project", ("title", "actions")),
            "In progress",
        )
        matching_responses = filter_history(
            responses, "project", ("title", "content")
        )

        payload = json_load(
            build_history_export(matching_tasks, matching_responses)
        )

        self.assertEqual(
            [task["title"] for task in payload["tasks"]],
            ["Project plan"],
        )
        self.assertEqual(
            [response["title"] for response in payload["responses"]],
            ["Project notes"],
        )

    def test_build_task_markdown_includes_progress_and_checklist(self):
        task = {
            "title": "Plan the release",
            "actions": '["Write release notes", "Review deployment"]',
            "completed": "[0, 99, -1, true]",
            "finished": 0,
            "created_at": "2026-11-09T10:00:00",
        }

        self.assertEqual(
            build_task_markdown(task),
            "# Plan the release\n\n"
            "Created: 2026-11-09T10:00:00\n"
            "Status: In progress\n"
            "Progress: 1/2 actions complete\n\n"
            "- [x] Write release notes\n"
            "- [ ] Review deployment",
        )

    def test_build_task_markdown_marks_finished_tasks_completed(self):
        task = {
            "title": "Finished task",
            "actions": '["One action"]',
            "completed": "[0]",
            "finished": 1,
            "created_at": "2026-11-09T10:00:00",
        }

        self.assertIn("Status: Completed", build_task_markdown(task))

    def test_completed_progress_overrides_stale_finished_flag(self):
        task = {
            "id": 1,
            "title": "Imported complete plan",
            "actions": '["First", "Second"]',
            "completed": "[0, 1]",
            "finished": 0,
            "created_at": "2026-11-09T10:00:00",
        }

        self.assertTrue(task_is_completed(task))
        self.assertIn("Status: Completed", build_task_markdown(task))
        self.assertEqual(task_stats([task])[:3], (1, 1, 0))
        self.assertIsNone(find_resumable_task([task]))

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

    def test_filter_records_by_date_includes_both_boundary_days(self):
        records = [
            {"id": 1, "created_at": "2026-11-08T23:59:59"},
            {"id": 2, "created_at": "2026-11-09T12:00:00"},
            {"id": 3, "created_at": "2026-11-10T00:00:00"},
            {"id": 4, "created_at": "invalid"},
        ]

        self.assertEqual(
            [record["id"] for record in filter_records_by_date(
                records, date(2026, 11, 9), date(2026, 11, 9)
            )],
            [2],
        )
        self.assertEqual(
            [record["id"] for record in filter_records_by_date(
                records, end_date=date(2026, 11, 8)
            )],
            [1],
        )

    def test_filter_records_by_date_returns_all_without_bounds(self):
        records = [{"created_at": "not-a-date"}, {"title": "legacy"}]
        self.assertEqual(filter_records_by_date(records), records)

    def test_filter_records_by_date_rejects_reversed_range(self):
        with self.assertRaisesRegex(ValueError, "on or before"):
            filter_records_by_date(
                [], date(2026, 11, 10), date(2026, 11, 9)
            )

    def test_filter_tasks_by_status_returns_all_and_matching_tasks(self):
        tasks = [
            {
                "id": 1, "finished": 0, "actions": '["One"]', "completed": "[]"
            },
            {
                "id": 2, "finished": 1, "actions": '["One"]', "completed": "[0]"
            },
            {
                "id": 3, "finished": 0, "actions": '["One"]', "completed": "[]"
            },
            {
                "id": 4, "finished": 0, "actions": '["One"]', "completed": "[0]"
            },
        ]

        self.assertEqual(filter_tasks_by_status(tasks, "All tasks"), tasks)
        self.assertEqual(
            [task["id"] for task in filter_tasks_by_status(tasks, "In progress")],
            [1, 3],
        )
        self.assertEqual(
            [task["id"] for task in filter_tasks_by_status(tasks, "Completed")],
            [2, 4],
        )

    def test_filter_tasks_by_status_rejects_unknown_status(self):
        with self.assertRaisesRegex(ValueError, "Task status"):
            filter_tasks_by_status([], "Archived")

    def test_sort_task_records_uses_creation_time_and_case_insensitive_title(self):
        tasks = [
            {"id": 3, "title": "beta", "created_at": "2026-11-07"},
            {"id": 2, "title": "Alpha", "created_at": "2026-11-09"},
            {"id": 1, "title": "alpha", "created_at": "2026-11-08"},
        ]

        self.assertEqual(
            [task["id"] for task in sort_task_records(tasks, "Newest first")],
            [2, 1, 3],
        )
        self.assertEqual(
            [task["id"] for task in sort_task_records(tasks, "Oldest first")],
            [3, 1, 2],
        )
        self.assertEqual(
            [task["id"] for task in sort_task_records(tasks, "Title A-Z")],
            [2, 1, 3],
        )

    def test_sort_task_records_rejects_unknown_order(self):
        with self.assertRaisesRegex(ValueError, "Task order"):
            sort_task_records([], "Random")

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

    def test_response_pages_are_newest_first_and_count_all_records(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "focusmate.db"
            self.create_database(database_path)
            with open_database(database_path) as db:
                db.executemany(
                    "INSERT INTO responses (title, content, created_at) "
                    "VALUES (?, ?, ?)",
                    [
                        (f"Response {index}", "content", "2026-11-09")
                        for index in range(1, 61)
                    ],
                )
                self.assertEqual(count_response_records(db), 60)
                self.assertEqual(
                    [row["title"] for row in load_response_page(db, 50, 0)][:2],
                    ["Response 60", "Response 59"],
                )
                self.assertEqual(
                    [row["title"] for row in load_response_page(db, 50, 50)],
                    ["Response 10", "Response 9", "Response 8", "Response 7",
                     "Response 6", "Response 5", "Response 4", "Response 3",
                     "Response 2", "Response 1"],
                )

    def test_response_pages_support_oldest_first(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "focusmate.db"
            self.create_database(database_path)
            with open_database(database_path) as db:
                db.executemany(
                    "INSERT INTO responses (title, content, created_at) "
                    "VALUES (?, ?, ?)",
                    [
                        ("Earlier", "content", "2026-11-08"),
                        ("Later", "content", "2026-11-10"),
                        ("Middle", "content", "2026-11-09"),
                    ],
                )

                self.assertEqual(
                    [row["title"] for row in load_response_page(
                        db, 2, 0, "Oldest first"
                    )],
                    ["Earlier", "Middle"],
                )
                self.assertEqual(
                    [row["title"] for row in load_response_page(db, 2, 0)],
                    ["Later", "Middle"],
                )

    def test_response_pages_support_case_insensitive_title_order(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "focusmate.db"
            self.create_database(database_path)
            with open_database(database_path) as db:
                db.executemany(
                    "INSERT INTO responses (title, content, created_at) "
                    "VALUES (?, ?, ?)",
                    [
                        ("zebra", "content", "2026-11-09"),
                        ("Alpha", "content", "2026-11-09"),
                        ("alpha", "content", "2026-11-09"),
                    ],
                )

                self.assertEqual(
                    [row["title"] for row in load_response_page(
                        db, 3, 0, "Title A-Z"
                    )],
                    ["alpha", "Alpha", "zebra"],
                )

    def test_response_page_rejects_unknown_order(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "focusmate.db"
            self.create_database(database_path)
            with open_database(database_path) as db:
                with self.assertRaisesRegex(ValueError, "Response order"):
                    load_response_page(db, 10, 0, "Random")

    def test_sort_response_records_orders_search_matches(self):
        records = [
            {"id": 3, "title": "C", "created_at": "2026-11-07"},
            {"id": 1, "title": "A", "created_at": "2026-11-09"},
            {"id": 2, "title": "B", "created_at": "2026-11-08"},
        ]

        self.assertEqual(
            [record["id"] for record in sort_response_records(
                records, "Oldest first"
            )],
            [3, 2, 1],
        )
        self.assertEqual(
            [record["id"] for record in sort_response_records(
                records, "Newest first"
            )],
            [1, 2, 3],
        )
        title_records = [
            {"id": 3, "title": "beta"},
            {"id": 2, "title": "Alpha"},
            {"id": 1, "title": "alpha"},
        ]
        self.assertEqual(
            [record["id"] for record in sort_response_records(
                title_records, "Title A-Z"
            )],
            [2, 1, 3],
        )

    def test_response_page_rejects_invalid_limit_and_offset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "focusmate.db"
            self.create_database(database_path)
            with open_database(database_path) as db:
                for limit, offset in ((0, 0), (True, 0), (10, -1), (10, False)):
                    with self.subTest(limit=limit, offset=offset):
                        with self.assertRaises(ValueError):
                            load_response_page(db, limit, offset)

    def test_paginate_records_returns_requested_slice(self):
        self.assertEqual(paginate_records(list(range(10)), 3, 3), [3, 4, 5])
        self.assertEqual(paginate_records(list(range(5)), 10, 0), list(range(5)))

    def test_paginate_records_after_filtering_keeps_search_across_all_records(self):
        records = [
            {"title": f"Task {index}", "actions": "Prepare the report"}
            for index in range(45)
        ]
        matching_records = filter_history(records, "report", ("title", "actions"))

        self.assertEqual(len(matching_records), 45)
        self.assertEqual(
            paginate_records(matching_records, 20, 20),
            records[20:40],
        )

    def test_paginate_records_rejects_invalid_bounds(self):
        for limit, offset in ((0, 0), (2, -1), (True, 0), (2, False)):
            with self.subTest(limit=limit, offset=offset):
                with self.assertRaises(ValueError):
                    paginate_records([], limit, offset)

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
