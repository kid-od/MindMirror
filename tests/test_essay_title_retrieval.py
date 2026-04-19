import importlib
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
        def __init__(self):
            self.query_filters = []

        def hybrid_retrieve(self, dense_embedding, sparse_embedding, top_k, filter_expr=""):
            self.query_filters.append(filter_expr)
            return [
                {
                    "filename": "加缪.md",
                    "text": "荒诞与反抗。",
                    "file_type": "Markdown",
                    "page_number": 0,
                    "chunk_id": "public::0",
                    "parent_chunk_id": "",
                    "root_chunk_id": "",
                    "chunk_level": 3,
                    "chunk_idx": 0,
                    "visibility": "public",
                    "owner_id": "",
                    "document_domain": "knowledge_base",
                    "score": 0.4,
                }
            ]

        def dense_retrieve(self, dense_embedding, top_k, filter_expr=""):
            self.query_filters.append(filter_expr)
            return []

        def query_all(self, filter_expr="", output_fields=None):
            self.query_filters.append(filter_expr)
            if 'filename == "随笔1.md"' in filter_expr:
                return [
                    {
                        "filename": "随笔1.md",
                        "text": "今天我写下了会议前的紧张和想逃开的冲动。",
                        "file_type": "Markdown",
                        "page_number": 0,
                        "chunk_id": "essay::0",
                        "parent_chunk_id": "",
                        "root_chunk_id": "",
                        "chunk_level": 3,
                        "chunk_idx": 0,
                        "visibility": "private",
                        "owner_id": "alice",
                        "document_domain": "essay",
                        "score": 1.0,
                    }
                ]
            return [{"filename": "随笔1.md"}]

    milvus_client_module.MilvusManager = MilvusManager

    parent_chunk_store_module = types.ModuleType("parent_chunk_store")

    class ParentChunkStore:
        def __init__(self):
            pass

    parent_chunk_store_module.ParentChunkStore = ParentChunkStore

    langchain_chat_models = types.ModuleType("langchain.chat_models")
    langchain_chat_models.init_chat_model = lambda *args, **kwargs: None

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


class ExactEssayTitleRetrievalTest(unittest.TestCase):
    def test_retrieve_documents_pulls_private_essay_when_query_mentions_essay_title(self):
        rag_utils_module = _load_rag_utils_module()

        result = rag_utils_module.retrieve_documents(
            "请帮我一步步分析这篇反思《随笔1》。",
            top_k=5,
            user_id="alice",
        )

        self.assertGreater(len(result["docs"]), 0)
        self.assertEqual(result["docs"][0]["filename"], "随笔1.md")
        self.assertEqual(result["docs"][0]["document_domain"], "essay")

    def test_retrieve_documents_can_use_original_question_as_title_hint(self):
        rag_utils_module = _load_rag_utils_module()

        result = rag_utils_module.retrieve_documents(
            "这是一段没有直接标题信息的假设文档。",
            top_k=5,
            user_id="alice",
            title_hint_query="请帮我一步步分析这篇反思《随笔1》。",
        )

        self.assertGreater(len(result["docs"]), 0)
        self.assertEqual(result["docs"][0]["filename"], "随笔1.md")
        self.assertEqual(result["docs"][0]["document_domain"], "essay")


if __name__ == "__main__":
    unittest.main()
