import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PrivateEssayApiStaticTest(unittest.TestCase):
    def test_api_defines_private_essay_routes(self):
        source = (ROOT / "backend" / "api.py").read_text(encoding="utf-8")

        self.assertIn('@router.get("/essays"', source)
        self.assertIn('@router.post("/essays/upload/stream"', source)
        self.assertIn('@router.delete("/essays/{filename}"', source)
        self.assertIn('"visibility": "private"', source)
        self.assertIn('"document_domain": "essay"', source)
        self.assertIn("current_user.username", source)

    def test_schemas_define_essay_response_models(self):
        source = (ROOT / "backend" / "schemas.py").read_text(encoding="utf-8")

        self.assertIn("class EssayInfo", source)
        self.assertIn("class EssayListResponse", source)
        self.assertIn("class EssayDeleteResponse", source)

    def test_api_and_schemas_define_daily_quote_and_session_title_support(self):
        api_source = (ROOT / "backend" / "api.py").read_text(encoding="utf-8")
        schema_source = (ROOT / "backend" / "schemas.py").read_text(encoding="utf-8")

        self.assertIn('@router.get("/daily-quote"', api_source)
        self.assertIn("class DailyQuoteResponse", schema_source)
        self.assertIn("title: str", schema_source)


if __name__ == "__main__":
    unittest.main()
