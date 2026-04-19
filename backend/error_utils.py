import re


def extract_model_error_code(message: str) -> int | None:
    match = re.search(r"Error code:\s*(\d{3})", message or "")
    if not match:
        return None
    return int(match.group(1))


def _region_hint(base_url: str | None) -> str:
    url = (base_url or "").strip().lower()
    if "dashscope-us.aliyuncs.com" in url:
        return (
            "\n当前 BASE_URL 指向美国地域。阿里云官方文档说明 API Key 按地域区分；"
            "如果你的 key 是北京地域创建的，请改用 "
            "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
    if "dashscope-intl.aliyuncs.com" in url:
        return (
            "\n当前 BASE_URL 指向新加坡地域。阿里云官方文档说明 API Key 按地域区分；"
            "请确认 key 与地域一致。"
        )
    return ""


def format_model_error_message(error: Exception | str, base_url: str | None = None) -> str:
    message = str(error)
    code = extract_model_error_code(message)

    if "_init_chat_model_helper() missing 1 required positional argument: 'model'" in message:
        return (
            "模型配置缺失：当前没有可用的 MODEL 配置，聊天模型无法初始化。"
            "请在项目根目录的 .env 中补齐 ARK_API_KEY、MODEL 和 BASE_URL 后重试。"
        )

    if code == 429:
        return (
            "上游模型服务触发限流或额度限制（429）。请检查账号额度、模型状态，或稍后重试。\n"
            f"原始错误：{message}"
        )

    if code in (401, 403):
        return (
            f"上游模型服务认证失败（{code}）。请检查 ARK_API_KEY、BASE_URL 和 MODEL 配置是否正确。\n"
            f"原始错误：{message}"
            f"{_region_hint(base_url)}"
        )

    return message
