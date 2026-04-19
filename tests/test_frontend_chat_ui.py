import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FrontendChatUiLayoutTest(unittest.TestCase):
    def test_chat_shell_uses_viewport_height_and_internal_scrolling(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertRegex(css, r"\.psyche-shell\s*\{[^}]*height:\s*100vh", re.S)
        self.assertRegex(css, r"\.psyche-main\s*\{[^}]*height:\s*100vh", re.S)
        self.assertRegex(css, r"\.psyche-main\s*\{[^}]*overflow:\s*hidden", re.S)
        self.assertRegex(css, r"\.deep-chat-messages\s*\{[^}]*overflow-y:\s*auto", re.S)

    def test_reflection_list_rows_do_not_stretch_into_large_blobs(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertRegex(css, r"\.reflection-session-list\s*\{[^}]*align-content:\s*start", re.S)
        self.assertRegex(css, r"\.reflection-session-list\s*\{[^}]*grid-auto-rows:\s*max-content", re.S)

    def test_session_delete_stays_accessible_on_touch_devices(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertRegex(css, r"@media\s*\(hover:\s*none\)\s*\{[^}]*\.session-delete\s*\{[^}]*opacity:\s*1", re.S)

    def test_chat_column_is_centered_and_readable(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertRegex(css, r"\.stitch-chat-layout\s*\{[^}]*grid-template-columns:\s*minmax\(260px,\s*320px\)\s*minmax\(0,\s*1fr\)", re.S)
        self.assertRegex(css, r"\.stitch-chat-layout\s*\{[^}]*align-items:\s*stretch", re.S)
        self.assertRegex(css, r"\.user-bubble\s*\{[^}]*max-width:\s*min\(620px,\s*72%\)", re.S)

    def test_chat_view_has_refined_message_and_composer_layers(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertRegex(css, r"\.deep-chat\s*\{[^}]*background:\s*linear-gradient", re.S)
        self.assertRegex(css, r"\.deep-chat-messages\s*\{[^}]*scrollbar-gutter:\s*stable", re.S)
        self.assertRegex(css, r"\.deep-input-area\s*\{[^}]*background:\s*linear-gradient", re.S)
        self.assertRegex(css, r"\.user-bubble\s*\{[^}]*background:\s*linear-gradient", re.S)
        self.assertRegex(css, r"\.curator-card\s*\{[^}]*border:\s*1px\s+solid", re.S)

    def test_chat_layout_stretches_rows_and_keeps_composer_out_of_overlap(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertRegex(css, r"\.stitch-chat-layout\s*\{[^}]*align-items:\s*stretch", re.S)
        self.assertRegex(css, r"\.deep-input-area\s*\{[^}]*flex:\s*0\s+0\s+auto", re.S)

    def test_theme_palette_matches_stitch_introspective_indigo(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertIn("--primary: #2e5bff;", css)
        self.assertIn("--primary-dim: #184cf2;", css)
        self.assertIn("--surface: #060e20;", css)
        self.assertIn("--surface-container-low: #06122c;", css)
        self.assertIn("--surface-container-highest: #11244c;", css)
        self.assertIn("--on-surface: #dee5ff;", css)
        self.assertIn("rgba(46, 91, 255", css)


if __name__ == "__main__":
    unittest.main()
