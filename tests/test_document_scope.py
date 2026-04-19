import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


def _fake_text_splitter_module():
    module = types.ModuleType("langchain_text_splitters")

    class RecursiveCharacterTextSplitter:
        def __init__(self, *args, **kwargs):
            pass

        def create_documents(self, texts, metadatas):
            docs = []
            for text, metadata in zip(texts, metadatas):
                docs.append(types.SimpleNamespace(page_content=text, metadata=metadata))
            return docs

    module.RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter
    return module


def _fake_document_loaders_module():
    loaders_module = types.ModuleType("langchain_community.document_loaders")

    class _UnusedLoader:
        def __init__(self, *args, **kwargs):
            pass

        def load(self):
            return []

    loaders_module.PyPDFLoader = _UnusedLoader
    loaders_module.Docx2txtLoader = _UnusedLoader
    loaders_module.UnstructuredExcelLoader = _UnusedLoader
    return loaders_module


def _load_document_loader_module():
    with patch.dict(
        sys.modules,
        {
            "langchain_text_splitters": _fake_text_splitter_module(),
            "langchain_community.document_loaders": _fake_document_loaders_module(),
        },
    ):
        import backend.document_loader as document_loader_module

        return importlib.reload(document_loader_module)


def _load_milvus_writer_module():
    embedding_module = types.ModuleType("embedding")

    class EmbeddingService:
        pass

    embedding_module.EmbeddingService = EmbeddingService
    embedding_module.embedding_service = object()

    milvus_client_module = types.ModuleType("milvus_client")

    class MilvusManager:
        pass

    milvus_client_module.MilvusManager = MilvusManager

    with patch.dict(
        sys.modules,
        {
            "embedding": embedding_module,
            "milvus_client": milvus_client_module,
            "upload_progress": importlib.import_module("backend.upload_progress"),
        },
    ):
        import backend.milvus_writer as milvus_writer_module

        return importlib.reload(milvus_writer_module)


class DocumentScopeMetadataTest(unittest.TestCase):
    def test_markdown_chunks_include_public_scope_metadata(self):
        DocumentLoader = _load_document_loader_module().DocumentLoader

        path = Path("/tmp/public_scope_notes.md")
        path.write_text("第一段关于自我觉察。\n\n第二段关于存在主义。", encoding="utf-8")

        loader = DocumentLoader(chunk_size=120, chunk_overlap=10)
        docs = loader.load_document(
            str(path),
            "public_scope_notes.md",
            metadata={
                "visibility": "public",
                "owner_id": "",
                "document_domain": "knowledge_base",
            },
        )

        self.assertGreater(len(docs), 0)
        self.assertTrue(all(doc["visibility"] == "public" for doc in docs))
        self.assertTrue(all(doc["owner_id"] == "" for doc in docs))
        self.assertTrue(all(doc["document_domain"] == "knowledge_base" for doc in docs))

    def test_markdown_chunks_include_private_scope_metadata(self):
        DocumentLoader = _load_document_loader_module().DocumentLoader

        path = Path("/tmp/private_scope_essay.md")
        path.write_text("今天我注意到自己在会议前很紧张。", encoding="utf-8")

        loader = DocumentLoader(chunk_size=120, chunk_overlap=10)
        docs = loader.load_document(
            str(path),
            "private_scope_essay.md",
            metadata={
                "visibility": "private",
                "owner_id": "alice",
                "document_domain": "essay",
            },
        )

        self.assertGreater(len(docs), 0)
        self.assertTrue(all(doc["visibility"] == "private" for doc in docs))
        self.assertTrue(all(doc["owner_id"] == "alice" for doc in docs))
        self.assertTrue(all(doc["document_domain"] == "essay" for doc in docs))

    def test_private_chunk_ids_are_scoped_by_owner_to_avoid_collisions(self):
        DocumentLoader = _load_document_loader_module().DocumentLoader

        path = Path("/tmp/shared_private_scope.md")
        path.write_text("同名随笔也应该拥有不同的分块标识。", encoding="utf-8")

        loader = DocumentLoader(chunk_size=120, chunk_overlap=10)
        alice_docs = loader.load_document(
            str(path),
            "shared_private_scope.md",
            metadata={
                "visibility": "private",
                "owner_id": "alice",
                "document_domain": "essay",
            },
        )
        bob_docs = loader.load_document(
            str(path),
            "shared_private_scope.md",
            metadata={
                "visibility": "private",
                "owner_id": "bob",
                "document_domain": "essay",
            },
        )

        self.assertTrue({doc["chunk_id"] for doc in alice_docs}.isdisjoint({doc["chunk_id"] for doc in bob_docs}))
        self.assertTrue({doc["root_chunk_id"] for doc in alice_docs}.isdisjoint({doc["root_chunk_id"] for doc in bob_docs}))

    def test_milvus_writer_includes_scope_fields(self):
        MilvusWriter = _load_milvus_writer_module().MilvusWriter

        class FakeEmbeddingService:
            def increment_add_documents(self, texts):
                self.texts = texts

            def get_all_embeddings(self, texts):
                return [[0.1, 0.2] for _ in texts], [{1: 0.5} for _ in texts]

        class FakeMilvusManager:
            def init_collection(self):
                self.initialized = True

            def insert(self, data):
                self.inserted = data

        manager = FakeMilvusManager()
        writer = MilvusWriter(embedding_service=FakeEmbeddingService(), milvus_manager=manager)
        writer.write_documents(
            [
                {
                    "text": "private journal",
                    "filename": "journal.md",
                    "file_type": "Markdown",
                    "file_path": "/tmp/journal.md",
                    "page_number": 0,
                    "chunk_idx": 0,
                    "chunk_id": "journal.md::p0::l3::0",
                    "parent_chunk_id": "journal.md::p0::l2::0",
                    "root_chunk_id": "journal.md::p0::l1::0",
                    "chunk_level": 3,
                    "visibility": "private",
                    "owner_id": "alice",
                    "document_domain": "essay",
                }
            ],
            batch_size=10,
        )

        row = manager.inserted[0]
        self.assertEqual(row["visibility"], "private")
        self.assertEqual(row["owner_id"], "alice")
        self.assertEqual(row["document_domain"], "essay")

    def test_long_essay_chunks_stay_within_milvus_varchar_limit(self):
        DocumentLoader = _load_document_loader_module().DocumentLoader

        path = Path("/tmp/long_single_paragraph_essay.md")
        path.write_text("我在想" * 1200, encoding="utf-8")

        loader = DocumentLoader(chunk_size=120, chunk_overlap=10)
        payload = loader.load_essay_document(
            str(path),
            "long_single_paragraph_essay.md",
            metadata={
                "visibility": "private",
                "owner_id": "alice",
                "document_domain": "essay",
            },
        )

        chunks = payload["chunks"]
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk["text"].encode("utf-8")) <= 2000 for chunk in chunks))


class ScopePersistenceTest(unittest.TestCase):
    def test_scoped_retrieval_filter_for_user(self):
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

            rag_utils_module = importlib.reload(rag_utils_module)

        self.assertEqual(
            rag_utils_module.build_scope_filter("alice"),
            '(visibility == "public" and document_domain == "knowledge_base") or '
            '(visibility == "private" and owner_id == "alice" and document_domain == "essay")',
        )

    def test_parent_chunk_store_payload_keeps_scope_fields(self):
        cache_module = types.ModuleType("cache")
        cache_module.cache = types.SimpleNamespace(
            set_json=lambda *args, **kwargs: None,
            get_json=lambda *args, **kwargs: None,
            delete=lambda *args, **kwargs: None,
        )

        database_module = types.ModuleType("database")
        database_module.SessionLocal = lambda: None

        models_module = types.ModuleType("models")

        class ParentChunk:
            pass

        models_module.ParentChunk = ParentChunk

        with patch.dict(
            sys.modules,
            {
                "cache": cache_module,
                "database": database_module,
                "models": models_module,
            },
        ):
            import backend.parent_chunk_store as parent_chunk_store_module

            parent_chunk_store_module = importlib.reload(parent_chunk_store_module)

        class Row:
            text = "parent text"
            filename = "journal.md"
            file_type = "Markdown"
            file_path = "/tmp/journal.md"
            page_number = 0
            chunk_id = "journal.md::p0::l2::0"
            parent_chunk_id = "journal.md::p0::l1::0"
            root_chunk_id = "journal.md::p0::l1::0"
            chunk_level = 2
            chunk_idx = 3
            visibility = "private"
            owner_id = "alice"
            document_domain = "essay"

        payload = parent_chunk_store_module.ParentChunkStore._to_dict(Row())

        self.assertEqual(payload["visibility"], "private")
        self.assertEqual(payload["owner_id"], "alice")
        self.assertEqual(payload["document_domain"], "essay")


class ScopedRetrievalExecutionTest(unittest.TestCase):
    def test_retrieve_documents_combines_chunk_level_and_scope_filter(self):
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
                self.last_filter = None

            def hybrid_retrieve(self, dense_embedding, sparse_embedding, top_k, filter_expr=""):
                self.last_filter = filter_expr
                return []

            def dense_retrieve(self, dense_embedding, top_k, filter_expr=""):
                self.last_filter = filter_expr
                return []

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

            rag_utils_module = importlib.reload(rag_utils_module)

        manager = rag_utils_module._milvus_manager
        rag_utils_module.retrieve_documents("焦虑来自哪里", top_k=5, user_id="alice")

        self.assertEqual(
            manager.last_filter,
            'chunk_level == 3 and ((visibility == "public" and document_domain == "knowledge_base") or '
            '(visibility == "private" and owner_id == "alice" and document_domain == "essay"))',
        )

    def test_auto_merge_skips_parent_docs_from_other_scope(self):
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

            def get_documents_by_ids(self, chunk_ids):
                return [
                    {
                        "chunk_id": "shared_private_scope.md::p0::l2::0",
                        "filename": "shared_private_scope.md",
                        "text": "bob parent",
                        "page_number": 0,
                        "chunk_level": 2,
                        "chunk_idx": 1,
                        "visibility": "private",
                        "owner_id": "bob",
                        "document_domain": "essay",
                    }
                ]

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

            rag_utils_module = importlib.reload(rag_utils_module)

        docs, merged_count = rag_utils_module._merge_to_parent_level(
            [
                {
                    "chunk_id": "shared_private_scope.md::p0::l3::0",
                    "parent_chunk_id": "shared_private_scope.md::p0::l2::0",
                    "root_chunk_id": "shared_private_scope.md::p0::l1::0",
                    "filename": "shared_private_scope.md",
                    "text": "alice leaf",
                    "page_number": 0,
                    "chunk_level": 3,
                    "chunk_idx": 2,
                    "visibility": "private",
                    "owner_id": "alice",
                    "document_domain": "essay",
                    "score": 0.9,
                }
            ],
            threshold=1,
        )

        self.assertEqual(merged_count, 0)
        self.assertEqual(docs[0]["owner_id"], "alice")
        self.assertEqual(docs[0]["chunk_level"], 3)


if __name__ == "__main__":
    unittest.main()
