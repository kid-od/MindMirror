import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InsightsTimelineApiContractTest(unittest.TestCase):
    def test_api_defines_authenticated_insights_and_timeline_routes(self):
        source = (ROOT / "backend" / "api.py").read_text(encoding="utf-8")

        self.assertIn('@router.get("/insights", response_model=InsightsResponse)', source)
        self.assertIn('@router.get("/timeline", response_model=TimelineResponse)', source)
        self.assertIn('@router.get("/document-cover")', source)
        self.assertIn("async def get_insights(current_user: User = Depends(get_current_user))", source)
        self.assertIn("async def get_timeline(current_user: User = Depends(get_current_user))", source)

    def test_schemas_define_insights_and_timeline_response_models(self):
        source = (ROOT / "backend" / "schemas.py").read_text(encoding="utf-8")

        for token in [
            "class InsightTotals",
            "class InsightTheme",
            "class ActivityPoint",
            "class InsightsResponse",
            "class TimelineEvent",
            "class TimelineGroup",
            "class TimelineResponse",
        ]:
            self.assertIn(token, source)

    def test_document_schema_exposes_cover_url(self):
        source = (ROOT / "backend" / "schemas.py").read_text(encoding="utf-8")

        self.assertIn("cover_url: Optional[str] = None", source)


if __name__ == "__main__":
    unittest.main()
