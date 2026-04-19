import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FrontendUiRegressionTests(unittest.TestCase):
    def test_chat_panel_keeps_a_stable_empty_state_footprint(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertRegex(css, r"--chat-shell-stable-height:\s*clamp\(40rem,\s*76vh,\s*58rem\);", re.S)
        self.assertRegex(css, r"\.deep-chat\s*\{[^}]*min-height:\s*var\(--chat-shell-stable-height\)", re.S)
        self.assertRegex(css, r"\.curator-welcome\s*\{[^}]*min-height:\s*100%", re.S)

    def test_session_delete_uses_a_dedicated_column_without_overlap(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertRegex(css, r"\.reflection-session-row\s*\{[^}]*grid-template-columns:\s*minmax\(0,\s*1fr\)\s*auto", re.S)
        self.assertRegex(css, r"\.reflection-session-row\s*\{[^}]*align-items:\s*center", re.S)
        self.assertRegex(css, r"\.session-delete\s*\{[^}]*position:\s*static", re.S)
        self.assertRegex(css, r"\.session-delete\s*\{[^}]*align-self:\s*center", re.S)
        self.assertRegex(css, r"\.session-delete\s*\{[^}]*border-radius:\s*14px", re.S)

    def test_essays_area_is_forced_into_black_white_high_contrast(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertRegex(css, r"\.essays-view\s+\.stitch-upload-status,\s*\.essays-view\s+\.empty-garden,\s*\.essay-card,\s*\.essay-card\.featured\s*\{[^}]*background:\s*#ffffff", re.S)
        self.assertRegex(css, r"\.essay-card h3,\s*\.essay-card p,\s*\.essay-meta,\s*\.essay-card-footer\s*\{[^}]*color:\s*var\(--essay-ink\)", re.S)
        self.assertRegex(css, r"\.essay-card-actions\s+\.ghost-action\s*\{[^}]*background:\s*transparent", re.S)


if __name__ == "__main__":
    unittest.main()
