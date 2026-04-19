import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FrontendIconRenderingTest(unittest.TestCase):
    def test_icons_do_not_depend_on_external_material_symbol_font(self):
        html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")

        self.assertNotIn("Material+Symbols", html)
        self.assertNotIn("material-symbols-outlined", html)
        self.assertNotIn("fonts.googleapis.com/css2?family=Material", html)

    def test_used_icons_are_defined_as_local_app_icons(self):
        html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")
        required_icons = [
            "account-circle",
            "arrow-forward",
            "article",
            "auto-awesome",
            "cloud-upload",
            "dashboard",
            "database",
            "edit-document",
            "format-quote",
            "insights",
            "library-add",
            "menu-book",
            "notifications",
            "psychology",
            "psychology-alt",
            "schema",
            "search",
            "send",
            "settings",
            "stop",
        ]

        self.assertIn(".app-icon {", css)
        for icon in required_icons:
            self.assertIn(f"app-icon app-icon-{icon}", html)
            self.assertIn(f".app-icon-{icon}", css)


if __name__ == "__main__":
    unittest.main()
