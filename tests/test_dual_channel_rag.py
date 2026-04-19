import importlib
import os
import sys
import types
import unittest
from unittest.mock import patch


def _load_rag_utils_module():
    embedding_module = types.ModuleType("embedding")

    class _EmbeddingService:
        def get_embeddings(self, texts):
            return [[0.1, 0.2] for _ in texts]

        def get_sparse_embedding(self, text):
            return {1: 0.5}

    embedding_module.embedding_service = _EmbeddingService()

    milvus_client_module = types.ModuleType("milvus_client")

    class MilvusManager:
        instances = []

        def __init__(self, collection_name=None):
            self.collection_name = collection_name or "knowledge_chunks"
            self.dense_calls = []
            self.hybrid_calls = []
            self.query_calls = []
            MilvusManager.instances.append(self)

        def hybrid_retrieve(self, dense_embedding, sparse_embedding, top_k, filter_expr=""):
            self.hybrid_calls.append((top_k, filter_expr))
            if self.collection_name == "knowledge_chunks":
                return [
                    {
                        "filename": "蛤蟆先生去看心理医生.pdf",
                        "text": "当一个人开始描述自己的自动反应时，反思才真正开始。",
                        "file_type": "PDF",
                        "page_number": 12,
                        "chunk_id": "kb::1",
                        "parent_chunk_id": "",
                        "root_chunk_id": "",
                        "chunk_level": 3,
                        "chunk_idx": 0,
                        "visibility": "public",
                        "owner_id": "",
                        "document_domain": "knowledge_base",
                        "score": 0.71,
                    }
                ]
            return []

        def dense_retrieve(self, dense_embedding, top_k, filter_expr=""):
            self.dense_calls.append((top_k, filter_expr))
            if self.collection_name == "essay_chunks":
                return [
                    {
                        "filename": "随笔1.md",
                        "text": "我总在会前想逃开，也会怪自己不够坚定。",
                        "file_type": "Markdown",
                        "page_number": 0,
                        "chunk_id": "essay::semantic::1",
                        "parent_chunk_id": "",
                        "root_chunk_id": "",
                        "chunk_level": 1,
                        "chunk_idx": 0,
                        "visibility": "private",
                        "owner_id": "alice",
                        "document_domain": "essay",
                        "score": 0.82,
                    }
                ]
            return []

        def query_all(self, filter_expr="", output_fields=None):
            self.query_calls.append((filter_expr, tuple(output_fields or [])))
            return []

    milvus_client_module.MilvusManager = MilvusManager

    parent_chunk_store_module = types.ModuleType("parent_chunk_store")

    class ParentChunkStore:
        def __init__(self):
            pass

    parent_chunk_store_module.ParentChunkStore = ParentChunkStore

    essay_store_module = types.ModuleType("essay_store")

    class EssayStore:
        def find_by_id(self, owner_id, essay_id):
            if owner_id == "alice" and essay_id == "essay-alice-1":
                return {
                    "essay_id": "essay-alice-1",
                    "owner_id": "alice",
                    "title": "随笔1",
                    "filename": "随笔1.md",
                    "file_type": "Markdown",
                    "language": "zh",
                    "content": "今天我写下会前的紧张、想逃开的冲动，以及对自己的责备。",
                    "chunk_count": 1,
                }
            return None

        def find_by_titles(self, owner_id, titles):
            if owner_id == "alice" and "今日所想" in titles:
                return {
                    "essay_id": "essay-alice-2",
                    "owner_id": "alice",
                    "title": "今日所想",
                    "filename": "今日所想.md",
                    "file_type": "Markdown",
                    "language": "zh",
                    "content": "今天我意识到自己把疲惫误认为懒惰。",
                    "chunk_count": 1,
                }
            return None

        def find_by_filename(self, owner_id, filename):
            return None

    essay_store_module.EssayStore = EssayStore

    langchain_chat_models = types.ModuleType("langchain.chat_models")
    langchain_chat_models.init_chat_model = lambda *args, **kwargs: None

    with patch.dict(
        sys.modules,
        {
            "embedding": embedding_module,
            "milvus_client": milvus_client_module,
            "parent_chunk_store": parent_chunk_store_module,
            "essay_store": essay_store_module,
            "langchain.chat_models": langchain_chat_models,
            "config": importlib.import_module("backend.config"),
        },
    ), patch.dict(
        os.environ,
        {
            "MILVUS_KNOWLEDGE_COLLECTION": "knowledge_chunks",
            "MILVUS_ESSAY_COLLECTION": "essay_chunks",
        },
        clear=False,
    ):
        import backend.rag_utils as rag_utils_module

        return importlib.reload(rag_utils_module)


class DualChannelRetrievalTest(unittest.TestCase):
    def test_session_bound_essay_is_used_before_vector_recall(self):
        rag_utils_module = _load_rag_utils_module()

        result = rag_utils_module.retrieve_documents(
            "继续帮我分析刚才那篇随笔。",
            top_k=5,
            user_id="alice",
            session_context={
                "analysis_mode": "essay",
                "active_essay_id": "essay-alice-1",
                "active_essay_title": "随笔1",
            },
        )

        self.assertTrue(result["meta"]["essay_context"]["found"])
        self.assertEqual(result["meta"]["essay_context"]["essay_id"], "essay-alice-1")
        self.assertEqual(result["meta"]["essay_context"]["retrieval_mode"], "session_bound")
        self.assertEqual(result["docs"][0]["document_domain"], "essay")
        self.assertEqual(result["docs"][0]["filename"], "随笔1.md")

    def test_exact_essay_match_combines_user_essay_with_public_knowledge(self):
        rag_utils_module = _load_rag_utils_module()

        result = rag_utils_module.retrieve_documents(
            "请帮我一步步分析这篇反思《今日所想》。",
            top_k=5,
            user_id="alice",
        )

        self.assertTrue(result["meta"]["essay_context"]["found"])
        self.assertEqual(result["meta"]["essay_context"]["title"], "今日所想")
        self.assertEqual(result["meta"]["essay_context"]["retrieval_mode"], "exact_title_match")
        self.assertTrue(result["meta"]["knowledge_context"]["found"])
        self.assertEqual(result["docs"][0]["document_domain"], "essay")
        self.assertTrue(any(doc["document_domain"] == "knowledge_base" for doc in result["docs"]))


if __name__ == "__main__":
    unittest.main()
