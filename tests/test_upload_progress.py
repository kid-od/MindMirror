import unittest


class UploadProgressEventTest(unittest.TestCase):
    def test_marks_previous_steps_done_and_current_step_active(self):
        from backend.upload_progress import build_upload_progress_event

        event = build_upload_progress_event("parsing", detail="正在提取文档文本")

        self.assertEqual(event["stage"], "parsing")
        self.assertEqual(event["state"], "running")
        self.assertEqual(event["step_index"], 2)
        self.assertEqual(event["total_steps"], 5)
        self.assertEqual(event["stages"][0]["status"], "done")
        self.assertEqual(event["stages"][1]["status"], "active")
        self.assertEqual(event["stages"][2]["status"], "pending")

    def test_marks_final_step_completed_as_full_progress(self):
        from backend.upload_progress import build_upload_progress_event

        event = build_upload_progress_event("indexing", state="completed", detail="写入完成")

        self.assertEqual(event["progress_percent"], 100)
        self.assertTrue(all(stage["status"] == "done" for stage in event["stages"]))


if __name__ == "__main__":
    unittest.main()
