import importlib
import sys
import types
import unittest
from unittest.mock import patch


def _load_tools_module(fake_result):
    rag_pipeline_module = types.ModuleType("rag_pipeline")
    rag_pipeline_module.run_rag_graph = lambda query, user_id=None: fake_result

    with patch.dict(sys.modules, {"rag_pipeline": rag_pipeline_module}):
        import backend.tools as tools_module
        return importlib.reload(tools_module)


class SearchKnowledgeBaseToolOutputTest(unittest.TestCase):
    def test_exact_essay_match_output_explicitly_marks_the_essay_as_found(self):
        tools_module = _load_tools_module(
            {
                "docs": [
                    {
                        "filename": "随笔1.md",
                        "page_number": 0,
                        "text": "这是随笔正文。",
                        "document_domain": "essay",
                    }
                ],
                "rag_trace": {
                    "retrieval_mode": "exact_title_match",
                },
            }
        )

        tools_module.reset_tool_call_guards()
        tools_module.set_current_rag_user("entropy")
        fake_rag_pipeline = types.ModuleType("rag_pipeline")
        fake_rag_pipeline.run_rag_graph = lambda query, user_id=None: {
            "docs": [
                {
                    "filename": "随笔1.md",
                    "page_number": 0,
                    "text": "这是随笔正文。",
                    "document_domain": "essay",
                }
            ],
            "rag_trace": {
                "retrieval_mode": "exact_title_match",
            },
        }
        with patch.dict(sys.modules, {"rag_pipeline": fake_rag_pipeline}):
            output = tools_module.search_knowledge_base.invoke({"query": "请分析《随笔1》"})

        self.assertIn("EXACT_ESSAY_MATCH_FOUND", output)
        self.assertIn("Do not say the essay was not found", output)
        self.assertIn("随笔1.md", output)

    def test_output_separates_essay_context_from_knowledge_context(self):
        tools_module = _load_tools_module(
            {
                "docs": [
                    {
                        "filename": "随笔1.md",
                        "page_number": 0,
                        "text": "这是我的随笔原文。",
                        "document_domain": "essay",
                    },
                    {
                        "filename": "蛤蟆先生去看心理医生.pdf",
                        "page_number": 12,
                        "text": "这是辅助分析的知识库内容。",
                        "document_domain": "knowledge_base",
                    },
                ],
                "rag_trace": {
                    "retrieval_mode": "exact_title_match",
                    "essay_context": {"found": True, "title": "随笔1"},
                    "knowledge_context": {"found": True},
                },
            }
        )

        tools_module.reset_tool_call_guards()
        with patch.dict(
            sys.modules,
            {
                "rag_pipeline": types.SimpleNamespace(
                    run_rag_graph=lambda query, user_id=None, session_context=None: {
                        "docs": [
                            {
                                "filename": "随笔1.md",
                                "page_number": 0,
                                "text": "这是我的随笔原文。",
                                "document_domain": "essay",
                            },
                            {
                                "filename": "蛤蟆先生去看心理医生.pdf",
                                "page_number": 12,
                                "text": "这是辅助分析的知识库内容。",
                                "document_domain": "knowledge_base",
                            },
                        ],
                        "rag_trace": {
                            "retrieval_mode": "exact_title_match",
                            "essay_context": {"found": True, "title": "随笔1"},
                            "knowledge_context": {"found": True},
                        },
                    }
                )
            },
        ):
            output = tools_module.search_knowledge_base.invoke({"query": "请分析《随笔1》"})

        self.assertIn("Essay Context:", output)
        self.assertIn("Knowledge Context:", output)
        self.assertIn("这是我的随笔原文。", output)
        self.assertIn("这是辅助分析的知识库内容。", output)


if __name__ == "__main__":
    unittest.main()
