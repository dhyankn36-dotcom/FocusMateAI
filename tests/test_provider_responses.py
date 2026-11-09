import unittest

from focusmate_core import (
    extract_gemini_content,
    extract_gemini_error,
    extract_ollama_content,
    extract_ollama_error,
)


class OllamaResponseTests(unittest.TestCase):
    def test_extracts_and_trims_message_content(self):
        payload = {"message": {"content": "  A useful answer\n"}}
        self.assertEqual(extract_ollama_content(payload), "A useful answer")

    def test_returns_empty_content_for_unexpected_payload_shapes(self):
        for payload in (
            None,
            [],
            {},
            {"message": None},
            {"message": []},
            {"message": {"content": 42}},
        ):
            with self.subTest(payload=payload):
                self.assertEqual(extract_ollama_content(payload), "")

    def test_extracts_provider_error_from_expected_shape(self):
        self.assertEqual(
            extract_ollama_error({"error": "  model not found  "}),
            "model not found",
        )

    def test_returns_empty_error_for_unexpected_shapes(self):
        for payload in (None, [], {}, {"error": {"message": "invalid"}}, {"error": 1}):
            with self.subTest(payload=payload):
                self.assertEqual(extract_ollama_error(payload), "")


class GeminiResponseTests(unittest.TestCase):
    def test_extracts_text_from_response_parts(self):
        payload = {
            "candidates": [
                {"content": {"parts": [{"text": " Hello"}, {"text": " world "}]}}
            ]
        }
        self.assertEqual(extract_gemini_content(payload), "Hello world")

    def test_returns_empty_content_for_unexpected_payload_shapes(self):
        for payload in (
            None,
            [],
            {},
            {"candidates": []},
            {"candidates": ["invalid"]},
            {"candidates": [{"content": None}]},
            {"candidates": [{"content": {"parts": "invalid"}}]},
        ):
            with self.subTest(payload=payload):
                self.assertEqual(extract_gemini_content(payload), "")

    def test_extracts_error_message_only_from_expected_shape(self):
        self.assertEqual(
            extract_gemini_error({"error": {"message": "  quota exceeded "}}),
            "quota exceeded",
        )
        self.assertEqual(extract_gemini_error({"error": "invalid"}), "")


if __name__ == "__main__":
    unittest.main()
