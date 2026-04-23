import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FrontendPsycheArchiveWorkspaceTest(unittest.TestCase):
    def test_script_defines_stitch_navigation_copy(self):
        script = (ROOT / "frontend" / "script.js").read_text(encoding="utf-8")

        for token in [
            "Dashboard",
            "Knowledge Base",
            "Reflections",
            "AI Explorer",
            "Insights",
            "Timeline",
            "Settings",
        ]:
            self.assertIn(token, script)

    def test_template_contains_self_analysis_surfaces_and_i18n_hooks(self):
        html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")

        for token in [
            "t('essays.title')",
            "t('chat.title')",
            "t('chat.recents')",
            "t('chat.knowledgeActive')",
            "t('chat.inputPlaceholder')",
            "t('chat.disclaimer')",
        ]:
            self.assertIn(token, html)

    def test_script_routes_home_to_dashboard_and_essay_actions_to_ai_explorer(self):
        script = (ROOT / "frontend" / "script.js").read_text(encoding="utf-8")

        self.assertRegex(script, r"currentView:\s*'dashboard'")
        self.assertIn("this.currentView = 'dashboard';", script)
        self.assertIn("this.currentView = 'ai_explorer';", script)
        self.assertIn("/essays", script)
        self.assertIn("/essays/upload/stream", script)


if __name__ == "__main__":
    unittest.main()
