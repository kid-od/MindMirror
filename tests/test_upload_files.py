import unittest


class _FakeUploadFile:
    def __init__(self, filename):
        self.filename = filename


class UploadFilesTest(unittest.TestCase):
    def test_markdown_extensions_are_supported(self):
        from backend.upload_files import validate_upload_filename

        self.assertEqual(validate_upload_filename("notes.md"), "notes.md")
        self.assertEqual(validate_upload_filename("notes.markdown"), "notes.markdown")

    def test_rejects_unsupported_extensions(self):
        from backend.upload_files import validate_upload_filename

        with self.assertRaises(ValueError) as ctx:
            validate_upload_filename("notes.txt")

        self.assertIn("Markdown", str(ctx.exception))

    def test_collects_legacy_single_file_and_batch_files(self):
        from backend.upload_files import collect_upload_files

        legacy_file = _FakeUploadFile("legacy.md")
        batch_files = [_FakeUploadFile("first.pdf"), _FakeUploadFile("second.md")]

        collected = collect_upload_files(file=legacy_file, files=batch_files)

        self.assertEqual([item.filename for item in collected], ["first.pdf", "second.md", "legacy.md"])


if __name__ == "__main__":
    unittest.main()
