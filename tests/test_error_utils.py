import unittest


class FormatModelErrorMessageTest(unittest.TestCase):
    def test_formats_authentication_errors(self):
        from backend.error_utils import format_model_error_message

        message = format_model_error_message(
            Exception("Error code: 401 - {'error': {'code': 'invalid_api_key'}}")
        )

        self.assertIn("认证失败（401）", message)
        self.assertIn("ARK_API_KEY", message)

    def test_adds_region_hint_for_us_endpoint(self):
        from backend.error_utils import format_model_error_message

        message = format_model_error_message(
            Exception("Error code: 401 - {'error': {'code': 'invalid_api_key'}}"),
            base_url="https://dashscope-us.aliyuncs.com/compatible-mode/v1",
        )

        self.assertIn("地域", message)
        self.assertIn("dashscope.aliyuncs.com/compatible-mode/v1", message)

    def test_returns_original_message_for_unknown_errors(self):
        from backend.error_utils import format_model_error_message

        self.assertEqual(
            format_model_error_message(Exception("Connection error.")),
            "Connection error.",
        )

    def test_formats_missing_model_configuration_errors(self):
        from backend.error_utils import format_model_error_message

        message = format_model_error_message(
            TypeError("_init_chat_model_helper() missing 1 required positional argument: 'model'")
        )

        self.assertIn("模型配置缺失", message)
        self.assertIn("ARK_API_KEY", message)
        self.assertIn("MODEL", message)
        self.assertIn(".env", message)


if __name__ == "__main__":
    unittest.main()
