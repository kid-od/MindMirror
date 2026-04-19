import unittest


class DailyQuoteServiceTest(unittest.TestCase):
    def test_normalizes_zenquotes_payload(self):
        from backend.daily_quote import normalize_quote_payload

        quote = normalize_quote_payload(
            [{"q": "Stay close to your inner life.", "a": "Rainer Maria Rilke"}],
            source="zenquotes",
        )

        self.assertEqual(quote["text"], "Stay close to your inner life.")
        self.assertEqual(quote["author"], "Rainer Maria Rilke")
        self.assertEqual(quote["source"], "zenquotes")
        self.assertFalse(quote["fallback"])

    def test_returns_localized_fallback_quote(self):
        from backend.daily_quote import pick_fallback_quote

        quote = pick_fallback_quote("zh")

        self.assertIn("text", quote)
        self.assertIn("author", quote)
        self.assertEqual(quote["language"], "zh")
        self.assertTrue(quote["fallback"])


if __name__ == "__main__":
    unittest.main()
