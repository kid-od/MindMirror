import unittest


class SessionTitleDerivationTest(unittest.TestCase):
    def test_prefers_first_human_message_and_strips_newlines(self):
        from backend.session_titles import derive_session_title

        title = derive_session_title(
            [
                {"type": "system", "content": "ignore"},
                {"type": "human", "content": "  I keep avoiding difficult work.\nCan you help me unpack that?  "},
                {"type": "ai", "content": "Let's explore that gently."},
            ],
            locale="en",
        )

        self.assertEqual(title, "I keep avoiding difficult work. Can you help me unpack that?")

    def test_falls_back_to_localized_default_for_empty_session(self):
        from backend.session_titles import derive_session_title

        self.assertEqual(derive_session_title([], locale="zh"), "新对话")
        self.assertEqual(derive_session_title([], locale="en"), "New Chat")

    def test_truncates_overlong_session_titles(self):
        from backend.session_titles import derive_session_title

        long_message = "A" * 120
        title = derive_session_title([{"type": "human", "content": long_message}], locale="en", max_length=48)

        self.assertEqual(len(title), 48)
        self.assertTrue(title.endswith("..."))


if __name__ == "__main__":
    unittest.main()
