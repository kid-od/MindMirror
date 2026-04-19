import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FrontendUploadUiTest(unittest.TestCase):
    def test_file_pickers_accept_stitch_supported_documents(self):
        html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")

        self.assertIn("multiple", html)
        self.assertIn(".pdf,.doc,.docx,.xls,.xlsx,.md,.markdown", html)

    def test_script_has_public_and_private_upload_endpoints(self):
        script = (ROOT / "frontend" / "script.js").read_text(encoding="utf-8")

        self.assertIn("formData.append('files'", script)
        self.assertIn("uploadKnowledgeDocument", script)
        self.assertIn("uploadEssayDocument", script)
        self.assertIn("/documents/upload/stream", script)
        self.assertIn("/essays/upload/stream", script)

    def test_script_updates_local_essay_state_after_upload_and_delete(self):
        script = (ROOT / "frontend" / "script.js").read_text(encoding="utf-8")

        self.assertIn("applyEssayUploadResults", script)
        self.assertIn("removeLocalEssay", script)
        self.assertIn("this.applyEssayUploadResults(successPayload.files || []);", script)
        self.assertIn("this.removeLocalEssay(filename);", script)


if __name__ == "__main__":
    unittest.main()
