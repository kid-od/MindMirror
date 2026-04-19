import re


def default_session_title(locale: str = "zh") -> str:
    return "新对话" if locale == "zh" else "New Chat"


def derive_session_title(messages: list[dict] | None, locale: str = "zh", max_length: int = 72) -> str:
    messages = messages or []
    for message in messages:
        if message.get("type") != "human":
            continue

        content = re.sub(r"\s+", " ", (message.get("content") or "").strip())
        if not content:
            continue

        if len(content) <= max_length:
            return content

        clipped = content[: max(0, max_length - 3)].rstrip()
        return f"{clipped}..."

    return default_session_title(locale)
