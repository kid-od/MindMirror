import tempfile
import unittest
from pathlib import Path


class DocumentPreviewsTest(unittest.TestCase):
    def test_build_cover_url_encodes_filename_and_version(self):
        from backend.document_previews import build_cover_url

        url = build_cover_url("My Book.pdf", 123456)

        self.assertEqual(url, "/document-cover?filename=My%20Book.pdf&v=123456")

    def test_placeholder_cover_renderer_writes_png_file(self):
        from backend.document_previews import render_placeholder_cover

        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "cover.png"
            render_placeholder_cover("Morning Clarity.pdf", output_path, file_type="PDF")
            self.assertTrue(output_path.exists())
            self.assertGreater(output_path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
