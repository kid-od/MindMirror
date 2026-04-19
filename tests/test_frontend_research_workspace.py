import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FrontendPsycheArchiveWorkspaceTest(unittest.TestCase):
    def test_script_defines_bilingual_branding_and_navigation_copy(self):
        script = (ROOT / "frontend" / "script.js").read_text(encoding="utf-8")

        for token in [
            "PsycheArchive",
            "心灵策展人",
            "Dashboard",
            "Knowledge Base",
            "My Essays",
            "AI Chat",
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

    def test_script_tracks_psychearchive_views_and_private_essays(self):
        script = (ROOT / "frontend" / "script.js").read_text(encoding="utf-8")

        self.assertRegex(script, r"currentView:\s*'chat'")
        self.assertIn("this.currentView = 'chat';", script)
        self.assertRegex(script, r"essays:\s*\[\]")
        self.assertRegex(script, r"selectedEssayFiles:\s*\[\]")
        self.assertIn("/essays", script)
        self.assertIn("/essays/upload/stream", script)


if __name__ == "__main__":
    unittest.main()
