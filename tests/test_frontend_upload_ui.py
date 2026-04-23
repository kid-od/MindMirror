import unittest
import re
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

    def test_knowledge_cards_render_uploaded_cover_preview_when_available(self):
        html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")

        self.assertIn("knowledge-card-cover", html)
        self.assertIn("doc.preview_url", html)
        self.assertIn(".knowledge-card-cover {", css)
        self.assertIn(".knowledge-card-cover img {", css)
        self.assertRegex(css, r"\.document-stack\s*\{[^}]*grid-template-columns:\s*repeat\(auto-fit,\s*minmax\(min\(100%,\s*16\.5rem\),\s*1fr\)\)", re.S)
        self.assertRegex(css, r"\.knowledge-card\.has-cover\s*\{[^}]*grid-template-columns:\s*1fr", re.S)
        self.assertRegex(css, r"\.knowledge-card-cover\s*\{[^}]*aspect-ratio:\s*2\s*/\s*3", re.S)
        self.assertRegex(css, r"\.knowledge-card-body h3\s*\{[^}]*-webkit-line-clamp:\s*2", re.S)

    def test_script_fetches_document_covers_through_authenticated_blob_urls(self):
        script = (ROOT / "frontend" / "script.js").read_text(encoding="utf-8")

        self.assertIn("await this.authFetch(doc.cover_url)", script)
        self.assertIn("URL.createObjectURL", script)
        self.assertIn("URL.revokeObjectURL", script)
        self.assertIn("preview_url", script)


if __name__ == "__main__":
    unittest.main()
