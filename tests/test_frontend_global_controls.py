import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FrontendGlobalControlsTest(unittest.TestCase):
    def test_html_contains_locale_control_without_theme_toggle(self):
        html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")

        self.assertIn("toggleLocale", html)
        self.assertNotIn("toggleTheme", html)
        self.assertIn("session-delete", html)
        self.assertIn("auth-preferences", html)
        self.assertIn("topbar-preferences", html)
        self.assertIn("displayDailyQuote.text", html)
        self.assertIn("displayDailyQuote.author", html)

    def test_script_tracks_daily_quote_locale_and_session_delete(self):
        script = (ROOT / "frontend" / "script.js").read_text(encoding="utf-8")

        self.assertIn("dailyQuote", script)
        self.assertIn("/daily-quote", script)
        self.assertIn("locale:", script)
        self.assertIn("localStorage.getItem('locale')", script)
        self.assertIn("toggleLocale()", script)
        self.assertNotIn("toggleTheme()", script)
        self.assertNotIn("applyTheme()", script)
        self.assertIn("deleteSession(", script)

    def test_script_normalizes_daily_quote_payload_before_rendering(self):
        script = (ROOT / "frontend" / "script.js").read_text(encoding="utf-8")

        self.assertIn("function normalizeDailyQuote(", script)
        self.assertIn("displayDailyQuote()", script)
        self.assertIn("return normalizeDailyQuote(this.dailyQuote, this.locale);", script)
        self.assertIn("dailyQuote: normalizeDailyQuote(null, localStorage.getItem('locale') || 'zh')", script)
        self.assertIn("this.dailyQuote = normalizeDailyQuote(await response.json(), this.locale);", script)
        self.assertIn("this.dailyQuote = normalizeDailyQuote(null, this.locale);", script)

    def test_css_separates_auth_and_app_preference_layouts(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertIn(".auth-preferences", css)
        self.assertIn(".topbar-preferences", css)

    def test_css_contains_stitch_theme_tokens(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        for token in [
            "--stitch-bg:",
            "--stitch-surface:",
            "--stitch-sage:",
            "--stitch-blue:",
            "--stitch-lavender:",
            "--stitch-radius-xl:",
            'font-family: "Manrope"',
            'font-family: "Noto Serif',
        ]:
            self.assertIn(token, css)


if __name__ == "__main__":
    unittest.main()
