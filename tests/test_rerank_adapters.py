import importlib
import os
import sys
import types
import unittest
from unittest.mock import patch


def _load_rag_utils_module(env: dict[str, str]):
    embedding_module = types.ModuleType("embedding")

    class _EmbeddingService:
        def get_embeddings(self, texts):
            return [[0.1, 0.2] for _ in texts]

        def get_sparse_embedding(self, text):
            return {1: 0.5}

    embedding_module.embedding_service = _EmbeddingService()

    milvus_client_module = types.ModuleType("milvus_client")

    class MilvusManager:
        def __init__(self):
            pass

    milvus_client_module.MilvusManager = MilvusManager

    parent_chunk_store_module = types.ModuleType("parent_chunk_store")

    class ParentChunkStore:
        def __init__(self):
            pass

    parent_chunk_store_module.ParentChunkStore = ParentChunkStore

    langchain_chat_models = types.ModuleType("langchain.chat_models")
    langchain_chat_models.init_chat_model = lambda *args, **kwargs: None

    with patch.dict(os.environ, env, clear=False):
        with patch.dict(
            sys.modules,
            {
                "embedding": embedding_module,
                "milvus_client": milvus_client_module,
                "parent_chunk_store": parent_chunk_store_module,
                "langchain.chat_models": langchain_chat_models,
                "config": importlib.import_module("backend.config"),
            },
        ):
            import backend.rag_utils as rag_utils_module

            return importlib.reload(rag_utils_module)


class RerankAdapterTest(unittest.TestCase):
    def test_qwen_endpoint_uses_dashscope_compatible_reranks(self):
        rag_utils_module = _load_rag_utils_module(
            {
                "ARK_API_KEY": "ark-test-key",
                "RERANK_MODEL": "qwen3-rerank",
                "RERANK_BINDING_HOST": "https://dashscope.aliyuncs.com/compatible-api/v1",
                "RERANK_API_KEY": "",
            }
        )

        self.assertEqual(
            rag_utils_module._get_rerank_endpoint(),
            "https://dashscope.aliyuncs.com/compatible-api/v1/reranks",
        )

    def test_qwen_rerank_uses_ark_api_key_and_parses_output_results(self):
        rag_utils_module = _load_rag_utils_module(
            {
                "ARK_API_KEY": "ark-test-key",
                "RERANK_MODEL": "qwen3-rerank",
                "RERANK_BINDING_HOST": "https://dashscope.aliyuncs.com/compatible-api/v1",
                "RERANK_API_KEY": "",
            }
        )

        captured: dict[str, object] = {}

        class FakeResponse:
            status_code = 200
            text = ""

            @staticmethod
            def json():
                return {
                    "output": {
                        "results": [
                            {"index": 1, "relevance_score": 0.92},
                            {"index": 0, "relevance_score": 0.33},
                        ]
                    }
                }

        def fake_post(url, headers, json, timeout):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            captured["timeout"] = timeout
            return FakeResponse()

        docs, meta = [], {}
        with patch.object(rag_utils_module.requests, "post", side_effect=fake_post):
            docs, meta = rag_utils_module._rerank_documents(
                query="如何面对自我怀疑",
                docs=[
                    {"text": "第一段", "chunk_id": "c1"},
                    {"text": "第二段", "chunk_id": "c2"},
                ],
                top_k=1,
            )

        self.assertEqual(captured["url"], "https://dashscope.aliyuncs.com/compatible-api/v1/reranks")
        self.assertEqual(captured["headers"]["Authorization"], "Bearer ark-test-key")
        self.assertEqual(
            captured["json"],
            {
                "model": "qwen3-rerank",
                "query": "如何面对自我怀疑",
                "documents": ["第一段", "第二段"],
                "top_n": 1,
                "return_documents": False,
            },
        )
        self.assertEqual(docs[0]["chunk_id"], "c2")
        self.assertEqual(docs[0]["rerank_score"], 0.92)
        self.assertTrue(meta["rerank_enabled"])
        self.assertTrue(meta["rerank_applied"])

    def test_jina_rerank_endpoint_and_response_format_still_work(self):
        rag_utils_module = _load_rag_utils_module(
            {
                "RERANK_MODEL": "jina-reranker-v2-base-multilingual",
                "RERANK_BINDING_HOST": "https://api.jina.ai",
                "RERANK_API_KEY": "jina-test-key",
            }
        )

        captured: dict[str, object] = {}

        class FakeResponse:
            status_code = 200
            text = ""

            @staticmethod
            def json():
                return {"results": [{"index": 0, "relevance_score": 0.81}]}

        def fake_post(url, headers, json, timeout):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            captured["timeout"] = timeout
            return FakeResponse()

        with patch.object(rag_utils_module.requests, "post", side_effect=fake_post):
            docs, meta = rag_utils_module._rerank_documents(
                query="meaning",
                docs=[{"text": "doc-a", "chunk_id": "c1"}],
                top_k=1,
            )

        self.assertEqual(captured["url"], "https://api.jina.ai/v1/rerank")
        self.assertEqual(captured["headers"]["Authorization"], "Bearer jina-test-key")
        self.assertEqual(docs[0]["chunk_id"], "c1")
        self.assertEqual(docs[0]["rerank_score"], 0.81)
        self.assertEqual(meta["rerank_model"], "jina-reranker-v2-base-multilingual")


if __name__ == "__main__":
    unittest.main()
