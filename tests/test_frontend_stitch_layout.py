import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FrontendStitchLayoutTest(unittest.TestCase):
    def test_template_contains_landing_and_app_shell_regions(self):
        html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")

        for token in [
            "stitch-landing-shell",
            "stitch-landing-hero",
            "stitch-auth-card",
            "stitch-shell",
            "stitch-sidebar",
            "stitch-topbar",
            "stitch-main-stage",
            "auth-preferences",
            "topbar-preferences",
            "session-delete",
        ]:
            self.assertIn(token, html)

        self.assertIn("toggleLocale", html)
        self.assertNotIn("toggleTheme", html)

    def test_template_contains_stitch_core_view_regions(self):
        html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")

        for token in [
            "stitch-dashboard-overview",
            "knowledge-library-grid",
            "knowledge-stage-shell",
            "reflection-archive-grid",
            "settings-sanctuary-grid",
            "insight-signal-grid",
            "timeline-entry-button",
            "app-icon-timeline",
        ]:
            self.assertIn(token, html)


if __name__ == "__main__":
    unittest.main()
