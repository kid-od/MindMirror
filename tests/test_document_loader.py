import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class DocumentLoaderSanitizationTest(unittest.TestCase):
    def test_split_chunks_do_not_contain_nul_characters(self):
        from backend.document_loader import DocumentLoader

        loader = DocumentLoader()
        chunks = loader._split_page_to_three_levels(
            "第一段\x00第二段",
            {
                "filename": "nul.pdf",
                "file_path": "/tmp/nul.pdf",
                "file_type": "PDF",
                "page_number": 0,
            },
            0,
        )

        self.assertTrue(chunks)
        self.assertTrue(all("\x00" not in chunk["text"] for chunk in chunks))


class DocumentLoaderMarkdownTest(unittest.TestCase):
    def test_load_markdown_document_reads_text_and_sets_file_type(self):
        from backend.document_loader import DocumentLoader

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "notes.md"
            path.write_text("# 标题\n\n这是一份 Markdown\x00 文档。", encoding="utf-8")

            chunks = DocumentLoader().load_document(str(path), "notes.md")

        self.assertTrue(chunks)
        self.assertTrue(any(chunk["file_type"] == "Markdown" for chunk in chunks))
        self.assertTrue(any("Markdown" in chunk["text"] for chunk in chunks))
        self.assertTrue(all("\x00" not in chunk["text"] for chunk in chunks))


if __name__ == "__main__":
    unittest.main()
