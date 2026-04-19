import unittest


class NormalizeBaseUrlTest(unittest.TestCase):
    def test_strips_accidental_env_key_prefix(self):
        from backend.config import normalize_base_url

        self.assertEqual(
            normalize_base_url("BASE_URL=https://dashscope-us.aliyuncs.com/compatible-mode/v1"),
            "https://dashscope-us.aliyuncs.com/compatible-mode/v1",
        )

    def test_keeps_valid_url_unchanged(self):
        from backend.config import normalize_base_url

        self.assertEqual(
            normalize_base_url("https://dashscope-us.aliyuncs.com/compatible-mode/v1"),
            "https://dashscope-us.aliyuncs.com/compatible-mode/v1",
        )

    def test_returns_none_for_blank_values(self):
        from backend.config import normalize_base_url

        self.assertIsNone(normalize_base_url("   "))


class ResolveGradeModelTest(unittest.TestCase):
    def test_uses_primary_model_when_grade_model_is_missing(self):
        from backend.config import resolve_grade_model

        self.assertEqual(resolve_grade_model("qwen3.6-plus", None), "qwen3.6-plus")

    def test_keeps_explicit_grade_model(self):
        from backend.config import resolve_grade_model

        self.assertEqual(resolve_grade_model("qwen-turbo", "qwen-plus"), "qwen-plus")

    def test_uses_safe_default_when_both_models_are_missing(self):
        from backend.config import resolve_grade_model

        self.assertEqual(resolve_grade_model(None, None), "qwen3.6-plus")


if __name__ == "__main__":
    unittest.main()
