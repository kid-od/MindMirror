import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FrontendChatUiLayoutTest(unittest.TestCase):
    def test_chat_shell_uses_viewport_height_and_internal_scrolling(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertRegex(css, r"\.psyche-shell\s*\{[^}]*height:\s*100vh;[^}]*height:\s*100dvh", re.S)
        self.assertRegex(css, r"\.psyche-main\s*\{[^}]*height:\s*100vh;[^}]*height:\s*100dvh", re.S)
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

        self.assertRegex(
            css,
            r"\.psyche-chat-layout,\s*\.stitch-chat-layout\s*\{[^}]*grid-template-columns:\s*minmax\(220px,\s*280px\)\s*minmax\(0,\s*1fr\)[^}]*align-items:\s*stretch[^}]*max-width:\s*var\(--chat-layout-max-width\)[^}]*margin-inline:\s*auto",
            re.S,
        )
        self.assertRegex(css, r"\.user-bubble\s*\{[^}]*max-width:\s*min\(42rem,\s*78%\)", re.S)
        self.assertRegex(css, r"\.curator-card\s*\{[^}]*max-width:\s*min\(56rem,\s*100%\)", re.S)

    def test_chat_view_has_refined_message_and_composer_layers(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertRegex(css, r"\.deep-chat\s*\{[^}]*background:\s*linear-gradient", re.S)
        self.assertRegex(css, r"\.deep-chat-messages\s*\{[^}]*scrollbar-gutter:\s*stable", re.S)
        self.assertRegex(css, r"\.deep-input-area\s*\{[^}]*background:\s*linear-gradient", re.S)
        self.assertRegex(css, r"\.user-bubble\s*\{[^}]*background:\s*linear-gradient", re.S)
        self.assertRegex(css, r"\.curator-card\s*\{[^}]*border:\s*1px\s+solid", re.S)

    def test_chat_layout_stretches_rows_and_keeps_composer_out_of_overlap(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertRegex(css, r"\.psyche-chat-layout,\s*\.stitch-chat-layout\s*\{[^}]*align-items:\s*stretch", re.S)
        self.assertRegex(css, r"\.deep-input-area\s*\{[^}]*flex:\s*0\s+0\s+auto", re.S)

    def test_chat_states_share_one_stable_message_window_size(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertIn("--chat-message-window-width: 56rem;", css)
        self.assertRegex(css, r"--chat-message-window-min-height:\s*clamp\(11rem,\s*24vh,\s*16rem\);", re.S)
        self.assertRegex(css, r"\.deep-chat\s*\{[^}]*grid-template-rows:\s*auto\s+minmax\(0,\s*1fr\)\s+auto", re.S)
        self.assertRegex(css, r"\.deep-chat-messages\s*\{[^}]*flex:\s*1\s+1\s+0[^}]*min-height:\s*0", re.S)
        self.assertRegex(css, r"\.curator-welcome,\s*\.curator-card\s*\{[^}]*width:\s*min\(100%,\s*var\(--chat-message-window-width\)\)[^}]*min-height:\s*var\(--chat-message-window-min-height\)", re.S)
        self.assertRegex(css, r"\.thinking-text,\s*\.markdown-body\s*\{[^}]*min-height:\s*var\(--chat-message-body-min-height\)", re.S)

    def test_secondary_controls_share_one_hover_language(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertRegex(
            css,
            r"\.ghost-auth,\s*"
            r"\.psyche-logout,\s*"
            r"\.ghost-action,\s*"
            r"\.activity-head button,\s*"
            r"\.essay-card-footer button,\s*"
            r"\.reflection-chip,\s*"
            r"\.reflection-session,\s*"
            r"\.psyche-nav-item,\s*"
            r"\.analysis-chip-row button\s*\{[^}]*"
            r"transition:\s*[^}]*transform var\(--calm-motion\)[^}]*"
            r"border-color var\(--calm-motion\)",
            re.S,
        )
        self.assertRegex(
            css,
            r"\.ghost-auth:hover,\s*"
            r"\.psyche-logout:hover,\s*"
            r"\.ghost-action:hover,\s*"
            r"\.activity-head button:hover,\s*"
            r"\.essay-card-footer button:hover,\s*"
            r"\.reflection-chip:hover,\s*"
            r"\.analysis-chip-row button:hover,\s*"
            r"\.psyche-nav-item:not\(\.active\):hover,\s*"
            r"\.reflection-session:not\(\.active\):hover\s*\{[^}]*"
            r"transform:\s*translateY\(-1px\);[^}]*"
            r"background:\s*var\(--primary\);[^}]*"
            r"color:\s*var\(--surface-container-lowest\);[^}]*"
            r"border-color:\s*var\(--primary\)",
            re.S,
        )

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
