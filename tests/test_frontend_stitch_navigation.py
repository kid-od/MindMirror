import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FrontendStitchNavigationTest(unittest.TestCase):
    def test_html_uses_stitch_view_names(self):
        html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")

        for token in [
            "setCurrentView('dashboard')",
            "setCurrentView('knowledge_base')",
            "setCurrentView('reflections')",
            "setCurrentView('ai_explorer')",
            "setCurrentView('insights')",
            "setCurrentView('timeline')",
            "setCurrentView('settings')",
        ]:
            self.assertIn(token, html)

    def test_script_normalizes_legacy_view_aliases_and_preserves_core_loaders(self):
        script = (ROOT / "frontend" / "script.js").read_text(encoding="utf-8")

        self.assertIn("const VIEW_ALIASES = {", script)
        self.assertIn("knowledge: 'knowledge_base'", script)
        self.assertIn("essays: 'reflections'", script)
        self.assertIn("chat: 'ai_explorer'", script)
        self.assertIn("if (nextView === 'knowledge_base') this.loadDocuments({ silentForbidden: true });", script)
        self.assertIn("if (nextView === 'reflections') this.loadEssays({ silent: true });", script)
        self.assertIn("if (nextView === 'ai_explorer') this.loadSessions({ silent: true });", script)

    def test_script_defines_insights_and_timeline_loaders(self):
        script = (ROOT / "frontend" / "script.js").read_text(encoding="utf-8")

        self.assertIn("insights:", script)
        self.assertIn("timelineGroups:", script)
        self.assertIn("async loadInsights(", script)
        self.assertIn("async loadTimeline(", script)
        self.assertIn("await this.authFetch('/insights')", script)
        self.assertIn("await this.authFetch('/timeline')", script)
        self.assertIn("if (nextView === 'insights') this.loadInsights({ silent: true });", script)
        self.assertIn("if (nextView === 'timeline') this.loadTimeline({ silent: true });", script)

    def test_logout_clears_aggregation_state(self):
        script = (ROOT / "frontend" / "script.js").read_text(encoding="utf-8")

        self.assertIn("this.timelineGroups = [];", script)
        self.assertIn("this.insights = {", script)
        self.assertIn("recent_sessions: []", script)

    def test_timeline_entries_route_back_into_core_workflows(self):
        html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "frontend" / "script.js").read_text(encoding="utf-8")

        self.assertIn("@click=\"openTimelineItem(item)\"", html)
        self.assertIn("openTimelineItem(item)", script)
        self.assertIn("this.loadSession(item.reference);", script)

    def test_ai_explorer_keeps_prompt_suggestions_and_rag_references(self):
        html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")

        self.assertIn("chatSuggestions", html)
        self.assertIn("applyChatSuggestion", html)
        self.assertIn("msg.ragTrace", html)
        self.assertIn("chunk.filename", html)


if __name__ == "__main__":
    unittest.main()
