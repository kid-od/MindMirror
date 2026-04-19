import importlib
import sys
import types
import unittest
import warnings
from unittest.mock import patch

from pydantic import BaseModel


def _load_rag_pipeline_module():
    dotenv_module = types.ModuleType("dotenv")
    dotenv_module.load_dotenv = lambda *args, **kwargs: None

    langchain_chat_models = types.ModuleType("langchain.chat_models")
    langchain_chat_models.init_chat_model = lambda *args, **kwargs: None

    langgraph_graph = types.ModuleType("langgraph.graph")

    class StateGraph:
        def __init__(self, state_type):
            self.state_type = state_type

        def add_node(self, *args, **kwargs):
            pass

        def set_entry_point(self, *args, **kwargs):
            pass

        def add_edge(self, *args, **kwargs):
            pass

        def add_conditional_edges(self, *args, **kwargs):
            pass

        def compile(self):
            return types.SimpleNamespace(invoke=lambda payload: payload)

    langgraph_graph.StateGraph = StateGraph
    langgraph_graph.END = "END"

    rag_utils_module = types.ModuleType("rag_utils")
    rag_utils_module.retrieve_documents = lambda *args, **kwargs: {"docs": [], "meta": {}}
    rag_utils_module.step_back_expand = lambda question: {
        "step_back_question": "",
        "step_back_answer": "",
        "expanded_query": question,
    }
    rag_utils_module.generate_hypothetical_document = lambda question: ""

    tools_module = types.ModuleType("tools")
    tools_module.emit_rag_step = lambda *args, **kwargs: None

    config_module = types.ModuleType("config")
    config_module.normalize_base_url = lambda value: value or ""
    config_module.resolve_grade_model = lambda model, grade_model: grade_model or model or ""

    with patch.dict(
        sys.modules,
        {
            "dotenv": dotenv_module,
            "langchain.chat_models": langchain_chat_models,
            "langgraph.graph": langgraph_graph,
            "rag_utils": rag_utils_module,
            "tools": tools_module,
            "config": config_module,
        },
    ):
        import backend.rag_pipeline as rag_pipeline_module

        return importlib.reload(rag_pipeline_module)


class RagPipelinePlainJsonModelParsingTest(unittest.TestCase):
    def test_grade_documents_node_accepts_plain_json_model_output(self):
        rag_pipeline_module = _load_rag_pipeline_module()

        class FakeGrader:
            def invoke(self, messages):
                return types.SimpleNamespace(content='{"binary_score": "yes"}')

        with patch.object(rag_pipeline_module, "_get_grader_model", return_value=FakeGrader()):
            result = rag_pipeline_module.grade_documents_node(
                {
                    "question": "请分析我的随笔",
                    "context": "这是关于焦虑与拖延的反思。",
                    "rag_trace": {},
                }
            )

        self.assertEqual(result["route"], "generate_answer")
        self.assertEqual(result["rag_trace"]["grade_score"], "yes")

    def test_rewrite_question_node_accepts_plain_json_model_output(self):
        rag_pipeline_module = _load_rag_pipeline_module()

        class FakeRouter:
            def invoke(self, messages):
                return types.SimpleNamespace(content='{"strategy": "hyde"}')

        with patch.object(rag_pipeline_module, "_get_router_model", return_value=FakeRouter()):
            result = rag_pipeline_module.rewrite_question_node(
                {
                    "question": "请分析《随笔1》背后的模式",
                    "rag_trace": {},
                }
            )

        self.assertEqual(result["expansion_type"], "hyde")
        self.assertEqual(result["rag_trace"]["rewrite_strategy"], "hyde")

    def test_sanitize_model_response_removes_parsed_pydantic_payloads(self):
        rag_pipeline_module = _load_rag_pipeline_module()

        class FakeResponse(BaseModel):
            content: str = '{"binary_score": "yes"}'
            parsed: None = None

        response = FakeResponse.model_construct(
            content='{"binary_score": "yes"}',
            parsed=rag_pipeline_module.GradeDocuments(binary_score="yes"),
        )

        with warnings.catch_warnings(record=True) as raw_warnings:
            warnings.simplefilter("always")
            response.model_dump(mode="python")

        self.assertTrue(raw_warnings)

        cleaned = rag_pipeline_module._sanitize_model_response(response)

        with warnings.catch_warnings(record=True) as cleaned_warnings:
            warnings.simplefilter("always")
            cleaned.model_dump(mode="python")

        self.assertFalse(cleaned_warnings)
        self.assertIsNone(cleaned.parsed)


if __name__ == "__main__":
    unittest.main()
