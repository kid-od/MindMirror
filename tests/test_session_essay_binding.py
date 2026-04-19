import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SessionEssayBindingStaticTest(unittest.TestCase):
    def test_chat_request_and_session_models_expose_active_essay_binding(self):
        source = (ROOT / "backend" / "schemas.py").read_text(encoding="utf-8")

        self.assertIn("active_essay_id", source)
        self.assertIn("active_essay_title", source)
        self.assertIn("analysis_mode", source)

    def test_frontend_tracks_active_essay_and_sends_it_with_chat_requests(self):
        source = (ROOT / "frontend" / "script.js").read_text(encoding="utf-8")

        self.assertIn("activeEssayId", source)
        self.assertIn("activeEssayTitle", source)
        self.assertIn("analysisMode", source)
        self.assertIn("active_essay_id: this.activeEssayId", source)
        self.assertIn("active_essay_title: this.activeEssayTitle", source)
        self.assertIn("analysis_mode: this.analysisMode", source)


if __name__ == "__main__":
    unittest.main()
