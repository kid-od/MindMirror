import unittest


class ActivityViewsTest(unittest.TestCase):
    def test_build_insights_payload_counts_activity_and_themes(self):
        from backend.activity_views import build_insights_payload

        payload = build_insights_payload(
            essays=[
                {"title": "Morning Clarity", "filename": "morning-clarity.md", "uploaded_at": "2026-04-20T08:00:00"},
                {"title": "Evening Ritual", "filename": "evening-ritual.md", "uploaded_at": "2026-04-21T20:30:00"},
            ],
            sessions=[
                {"session_id": "s1", "title": "Clarity check-in", "updated_at": "2026-04-21T09:00:00", "message_count": 6},
                {"session_id": "s2", "title": "Ritual review", "updated_at": "2026-04-22T09:00:00", "message_count": 4},
            ],
            documents=[{"filename": "rituals.pdf", "updated_at": "2026-04-19T10:00:00"}],
        )

        self.assertEqual(payload["totals"]["essays"], 2)
        self.assertEqual(payload["totals"]["sessions"], 2)
        self.assertEqual(payload["totals"]["documents"], 1)
        self.assertEqual(payload["top_themes"][0]["label"], "clarity")
        self.assertEqual(payload["recent_sessions"][0]["session_id"], "s2")
        self.assertEqual(payload["activity"][-1]["sessions"], 1)

    def test_build_timeline_payload_groups_events_by_day_and_sort_order(self):
        from backend.activity_views import build_timeline_payload

        payload = build_timeline_payload(
            essays=[{"title": "Morning Clarity", "filename": "morning.md", "uploaded_at": "2026-04-21T08:00:00"}],
            sessions=[{"session_id": "s1", "title": "Night Review", "updated_at": "2026-04-22T21:00:00", "message_count": 5}],
            documents=[{"filename": "guide.pdf", "updated_at": "2026-04-22T07:00:00"}],
        )

        self.assertEqual(payload["groups"][0]["date"], "2026-04-22")
        self.assertEqual(payload["groups"][0]["items"][0]["kind"], "session")
        self.assertEqual(payload["groups"][0]["items"][1]["kind"], "document")
        self.assertEqual(payload["groups"][1]["items"][0]["kind"], "essay")


if __name__ == "__main__":
    unittest.main()
