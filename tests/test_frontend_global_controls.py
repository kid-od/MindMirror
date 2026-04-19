import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FrontendGlobalControlsTest(unittest.TestCase):
    def test_html_contains_locale_and_theme_controls(self):
        html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")

        self.assertIn("toggleLocale", html)
        self.assertIn("toggleTheme", html)
        self.assertIn("session-delete", html)
        self.assertIn("auth-preferences", html)
        self.assertIn("topbar-preferences", html)

    def test_script_tracks_daily_quote_locale_theme_and_session_delete(self):
        script = (ROOT / "frontend" / "script.js").read_text(encoding="utf-8")

        self.assertIn("dailyQuote", script)
        self.assertIn("/daily-quote", script)
        self.assertIn("locale:", script)
        self.assertIn("theme:", script)
        self.assertIn("localStorage.getItem('locale')", script)
        self.assertIn("localStorage.getItem('theme')", script)
        self.assertIn("localStorage.getItem('theme') === 'light' ? 'light' : 'dark'", script)
        self.assertIn("toggleLocale()", script)
        self.assertIn("toggleTheme()", script)
        self.assertIn("deleteSession(", script)

    def test_css_separates_auth_and_app_preference_layouts(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertIn(".auth-preferences", css)
        self.assertIn(".topbar-preferences", css)


if __name__ == "__main__":
    unittest.main()
