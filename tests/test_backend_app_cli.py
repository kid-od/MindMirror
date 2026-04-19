import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BackendAppCliTest(unittest.TestCase):
    def test_backend_app_honors_reload_flag(self):
        source = (ROOT / "backend" / "app.py").read_text(encoding="utf-8")

        self.assertIn('"--reload" in sys.argv', source)
        self.assertIn('uvicorn.run("app:app"', source)
        self.assertIn("reload=True", source)
        self.assertIn('app_dir=str(BASE_DIR / "backend")', source)


if __name__ == "__main__":
    unittest.main()
