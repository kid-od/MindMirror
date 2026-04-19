import unittest


class SanitizeTextTest(unittest.TestCase):
    def test_removes_nul_characters_from_text(self):
        from backend.text_utils import sanitize_text

        self.assertEqual(sanitize_text("abc\x00def"), "abcdef")

    def test_converts_none_to_empty_string(self):
        from backend.text_utils import sanitize_text

        self.assertEqual(sanitize_text(None), "")


if __name__ == "__main__":
    unittest.main()
