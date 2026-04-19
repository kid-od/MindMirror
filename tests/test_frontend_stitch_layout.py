import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FrontendStitchLayoutTest(unittest.TestCase):
    def test_template_contains_stitch_indigo_shell_regions(self):
        html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")

        for token in [
            "stitch-auth-shell",
            "stitch-auth-panel",
            "stitch-shell",
            "stitch-sidebar",
            "stitch-topbar",
            "stitch-chat-layout",
            "stitch-dashboard-grid",
            "stitch-knowledge-stage",
            "stitch-essays-grid",
            "stitch-settings-grid",
            "auth-preferences",
            "topbar-preferences",
            "session-delete",
        ]:
            self.assertIn(token, html)


if __name__ == "__main__":
    unittest.main()
