import unittest

from focusmate_core import (
    build_history_export,
    extract_action_steps,
    json_dump,
    json_load,
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
