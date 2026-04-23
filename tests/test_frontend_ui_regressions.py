import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FrontendUiRegressionTests(unittest.TestCase):
    def test_layout_css_uses_a_single_consolidated_shell_definition(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertEqual(len(re.findall(r"(?m)^:root\s*\{", css)), 1)
        self.assertEqual(len(re.findall(r"(?m)^\.psyche-shell\s*\{", css)), 1)
        self.assertEqual(len(re.findall(r"(?m)^\.psyche-main\s*\{", css)), 1)
        self.assertEqual(len(re.findall(r"(?m)^\.deep-chat\s*\{", css)), 1)

    def test_primary_views_share_a_centered_content_width(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertRegex(css, r"--layout-max-width:\s*80rem;", re.S)
        self.assertRegex(
            css,
            r"\.dashboard-view\s*>\s*\*,\s*"
            r"\.knowledge-view\s*>\s*\*,\s*"
            r"\.essays-view\s*>\s*\*,\s*"
            r"\.settings-view\s*>\s*\*\s*\{[^}]*"
            r"width:\s*min\(100%,\s*var\(--layout-max-width\)\);[^}]*"
            r"margin-inline:\s*auto",
            re.S,
        )

    def test_dashboard_and_library_grids_use_auto_fit_tracks(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertRegex(
            css,
            r"\.bento-grid\s*\{[^}]*grid-template-columns:\s*repeat\(auto-fit,\s*minmax\(min\(100%,\s*16rem\),\s*1fr\)\)",
            re.S,
        )
        self.assertRegex(
            css,
            r"\.essay-grid\s*\{[^}]*grid-template-columns:\s*repeat\(auto-fit,\s*minmax\(min\(100%,\s*18rem\),\s*1fr\)\)",
            re.S,
        )
        self.assertRegex(
            css,
            r"\.activity-grid,\s*\.settings-grid\s*\{[^}]*grid-template-columns:\s*repeat\(auto-fit,\s*minmax\(min\(100%,\s*18rem\),\s*1fr\)\)",
            re.S,
        )

    def test_core_views_share_editorial_grid_rules(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertRegex(css, r"\.stitch-dashboard-overview\s*\{[^}]*display:\s*grid", re.S)
        self.assertRegex(css, r"\.knowledge-library-grid\s*\{[^}]*grid-template-columns:\s*1\.2fr\s*0\.8fr", re.S)
        self.assertRegex(css, r"\.knowledge-stage-shell\s*\{[^}]*grid-template-columns:\s*minmax\(0,\s*1\.1fr\)\s*minmax\(20rem,\s*0\.9fr\)", re.S)
        self.assertRegex(css, r"\.document-stack\s*\{[^}]*grid-column:\s*1\s*/\s*-1", re.S)
        self.assertRegex(
            css,
            r"\.reflection-archive-grid\s+\.essay-grid\s*\{[^}]*grid-template-columns:\s*repeat\(auto-fit,\s*minmax\(min\(100%,\s*18rem\),\s*1fr\)\)",
            re.S,
        )
        self.assertRegex(
            css,
            r"\.settings-sanctuary-grid\s+\.settings-grid\s*\{[^}]*grid-template-columns:\s*repeat\(auto-fit,\s*minmax\(min\(100%,\s*18rem\),\s*1fr\)\)",
            re.S,
        )

    def test_dashboard_quote_card_uses_an_isolated_copy_layer(self):
        html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertIn('class="quote-card-copy"', html)
        self.assertRegex(css, r"\.quote-card\s*\{[^}]*isolation:\s*isolate", re.S)
        self.assertRegex(css, r"\.quote-card\s*\{[^}]*min-height:\s*clamp\(14rem,\s*24vw,\s*18rem\)", re.S)
        self.assertRegex(css, r"\.quote-card-copy\s*\{[^}]*display:\s*grid[^}]*max-width:\s*min\(100%,\s*52rem\)", re.S)
        self.assertRegex(css, r"\.quote-card h2\s*\{[^}]*color:\s*var\(--on-surface\)", re.S)

    def test_chat_panel_keeps_a_stable_empty_state_footprint(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertRegex(css, r"--chat-shell-stable-height:\s*clamp\(36rem,\s*calc\(100dvh - 12rem\),\s*54rem\);", re.S)
        self.assertRegex(css, r"\.deep-chat\s*\{[^}]*min-height:\s*var\(--chat-shell-stable-height\)", re.S)
        self.assertRegex(css, r"\.curator-welcome,\s*\.curator-card\s*\{[^}]*min-height:\s*var\(--chat-message-window-min-height\)", re.S)

    def test_chat_panel_keeps_a_fixed_desktop_shell(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertRegex(css, r"\.psyche-chat-layout,\s*\.stitch-chat-layout\s*\{[^}]*align-items:\s*stretch", re.S)
        self.assertRegex(css, r"\.deep-chat\s*\{[^}]*height:\s*var\(--chat-shell-stable-height\)", re.S)
        self.assertRegex(css, r"\.reflection-list\s*\{[^}]*max-height:\s*var\(--chat-shell-stable-height\)", re.S)
        self.assertRegex(css, r"@media\s*\(max-width:\s*980px\)\s*\{[\s\S]*?\.deep-chat\s*\{[^}]*height:\s*auto", re.S)

    def test_explorer_and_aggregation_views_have_stitch_layout_rules(self):
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertRegex(css, r"\.stitch-explorer-shell\s*\{[^}]*grid-template-columns:\s*22rem\s*minmax\(0,\s*1fr\)", re.S)
        self.assertRegex(css, r"\.stitch-insights-grid\s*\{[^}]*display:\s*grid", re.S)
        self.assertRegex(css, r"\.stitch-timeline-grid\s*\{[^}]*display:\s*grid", re.S)
        self.assertRegex(css, r"\.insight-signal-grid\s*\{[^}]*grid-template-columns:\s*repeat\(auto-fit,\s*minmax\(min\(100%,\s*18rem\),\s*1fr\)\)", re.S)
        self.assertRegex(css, r"\.timeline-entry-button\s*\{[^}]*width:\s*100%", re.S)
        self.assertRegex(css, r"\.activity-sparkline\s*\{[^}]*display:\s*grid", re.S)
        self.assertIn(".app-icon-timeline {", css)

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
