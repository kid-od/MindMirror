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

        self.assertRegex(css, r"\.stitch-chat-layout\s*\{[^}]*grid-template-columns:\s*minmax\(220px,\s*280px\)\s*minmax\(0,\s*1fr\)", re.S)
        self.assertRegex(css, r"\.stitch-chat-layout\s*\{[^}]*align-items:\s*stretch", re.S)
        self.assertRegex(css, r"\.user-bubble\s*\{[^}]*max-width:\s*min\(760px,\s*78%\)", re.S)
        self.assertRegex(css, r"\.curator-card\s*\{[^}]*max-width:\s*min\(1180px,\s*100%\)", re.S)

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

    def test_theme_palette_matches_clinical_void_neutrals(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertIn("--primary: #000000;", css)
        self.assertIn("--primary-dim: #1b1b1b;", css)
        self.assertIn("--primary-container: #3b3b3b;", css)
        self.assertIn("--surface: #f9f9f9;", css)
        self.assertIn("--surface-container-low: #f3f3f3;", css)
        self.assertIn("--surface-container-high: #e8e8e8;", css)
        self.assertIn("--on-surface: #1b1b1b;", css)
        self.assertIn("--outline-variant: #c6c6c6;", css)

    def test_essay_cards_do_not_keep_old_blue_featured_gradient(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertRegex(css, r"\.essay-card\.featured\s*\{[^}]*background:\s*var\(--surface-container-lowest\)", re.S)


if __name__ == "__main__":
    unittest.main()
