import unittest

from focusmate_core import extract_action_steps


class ActionStepParsingTests(unittest.TestCase):
    def test_removes_case_insensitive_duplicate_steps(self):
        text = (
            "1. Prepare a list of project requirements\n"
            "- prepare a list of project requirements"
        )
        self.assertEqual(
            extract_action_steps(text),
            ["Prepare a list of project requirements"],
        )

    def test_accepts_common_step_and_bullet_formats(self):
        text = (
            "Step 1: Gather the project requirements\n"
            "2) Draft a short implementation plan\n"
            "• Review the plan with the team"
        )
        self.assertEqual(
            extract_action_steps(text),
            [
                "Gather the project requirements",
                "Draft a short implementation plan",
                "Review the plan with the team",
            ],
        )


if __name__ == "__main__":
    unittest.main()
