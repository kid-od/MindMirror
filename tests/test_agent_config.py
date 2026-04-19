import importlib
import os
import sys
import types
import unittest
from unittest.mock import patch


def _load_agent_module():
    init_calls = []

    dotenv_module = types.ModuleType("dotenv")
    dotenv_module.load_dotenv = lambda *args, **kwargs: None

    langchain_chat_models = types.ModuleType("langchain.chat_models")

    def fake_init_chat_model(*args, **kwargs):
        init_calls.append((args, kwargs))
        return types.SimpleNamespace(invoke=lambda *_args, **_kwargs: types.SimpleNamespace(content="ok"))

    langchain_chat_models.init_chat_model = fake_init_chat_model

    langchain_agents = types.ModuleType("langchain.agents")
    langchain_agents.create_agent = lambda *args, **kwargs: types.SimpleNamespace(
        invoke=lambda *_args, **_kwargs: {"output": "ok"},
        astream=lambda *_args, **_kwargs: iter(()),
    )

    langchain_core_messages = types.ModuleType("langchain_core.messages")

    class _Message:
        message_type = "base"

        def __init__(self, content=""):
            self.content = content

        @property
        def type(self):
            return self.message_type

    class HumanMessage(_Message):
        message_type = "human"

    class AIMessage(_Message):
        message_type = "ai"

    class AIMessageChunk(AIMessage):
        pass

    class SystemMessage(_Message):
        message_type = "system"

    langchain_core_messages.HumanMessage = HumanMessage
    langchain_core_messages.AIMessage = AIMessage
    langchain_core_messages.AIMessageChunk = AIMessageChunk
    langchain_core_messages.SystemMessage = SystemMessage

    config_module = types.ModuleType("config")
    config_module.normalize_base_url = lambda value: value

    error_utils_module = types.ModuleType("error_utils")
    error_utils_module.format_model_error_message = lambda error, base_url=None: str(error)

    tools_module = types.ModuleType("tools")
    tools_module.get_current_weather = lambda *args, **kwargs: {}
    tools_module.search_knowledge_base = lambda *args, **kwargs: {}
    tools_module.get_last_rag_context = lambda clear=False: {}
    tools_module.reset_tool_call_guards = lambda: None
    tools_module.set_current_rag_user = lambda user_id: None
    tools_module.set_rag_step_queue = lambda queue: None

    cache_module = types.ModuleType("cache")
    cache_module.cache = types.SimpleNamespace(
        get_json=lambda *args, **kwargs: None,
        set_json=lambda *args, **kwargs: None,
        delete=lambda *args, **kwargs: None,
    )

    database_module = types.ModuleType("database")
    database_module.SessionLocal = lambda: types.SimpleNamespace(close=lambda: None)

    models_module = types.ModuleType("models")
    models_module.User = type("User", (), {})
    models_module.ChatSession = type("ChatSession", (), {})
    models_module.ChatMessage = type("ChatMessage", (), {})

    session_titles_module = types.ModuleType("session_titles")
    session_titles_module.derive_session_title = lambda *args, **kwargs: "新对话"

    with patch.dict(
        sys.modules,
        {
            "dotenv": dotenv_module,
            "langchain.chat_models": langchain_chat_models,
            "langchain.agents": langchain_agents,
            "langchain_core.messages": langchain_core_messages,
            "config": config_module,
            "error_utils": error_utils_module,
            "tools": tools_module,
            "cache": cache_module,
            "database": database_module,
            "models": models_module,
            "session_titles": session_titles_module,
        },
    ):
        import backend.agent as agent_module

        return importlib.reload(agent_module), init_calls


class AgentConfigurationGuardTest(unittest.TestCase):
    def test_missing_model_configuration_raises_clear_error_before_langchain_init(self):
        with patch.dict(os.environ, {"ARK_API_KEY": "", "MODEL": "", "BASE_URL": ""}, clear=False):
            agent_module, init_calls = _load_agent_module()

        with self.assertRaises(RuntimeError) as ctx:
            agent_module._ensure_agent_instance()

        self.assertIn("模型配置缺失", str(ctx.exception))
        self.assertIn("ARK_API_KEY", str(ctx.exception))
        self.assertIn("MODEL", str(ctx.exception))
        self.assertEqual(init_calls, [])


if __name__ == "__main__":
    unittest.main()
