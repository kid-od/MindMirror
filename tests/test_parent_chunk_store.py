import importlib
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


def _load_parent_chunk_store_module():
    cache_module = types.ModuleType("cache")
    cache_module.cache = types.SimpleNamespace(
        set_json=lambda *args, **kwargs: None,
        get_json=lambda *args, **kwargs: None,
        delete=lambda *args, **kwargs: None,
    )

    database_module = types.ModuleType("database")
    database_module.SessionLocal = lambda: None
    database_module.ensure_parent_chunk_schema = lambda *args, **kwargs: None

    class ParentChunk:
        chunk_id = "chunk_id"

        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    models_module = types.ModuleType("models")
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

        return importlib.reload(parent_chunk_store_module)


class ParentChunkStoreSchemaGuardTest(unittest.TestCase):
    def test_upsert_documents_ensures_parent_chunk_schema_before_querying(self):
        parent_chunk_store_module = _load_parent_chunk_store_module()
        ParentChunkStore = parent_chunk_store_module.ParentChunkStore

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        docs = [
            {
                "chunk_id": "essay::p0::l1::0",
                "text": "反思内容",
                "filename": "随笔1.md",
                "file_type": "Markdown",
                "file_path": "/tmp/随笔1.md",
                "page_number": 0,
                "parent_chunk_id": "",
                "root_chunk_id": "essay::p0::l1::0",
                "chunk_level": 1,
                "chunk_idx": 0,
                "visibility": "private",
                "owner_id": "alice",
                "document_domain": "essay",
            }
        ]

        with patch.object(parent_chunk_store_module, "SessionLocal", return_value=db), \
             patch.object(parent_chunk_store_module, "ensure_parent_chunk_schema") as ensure_parent_chunk_schema, \
             patch.object(parent_chunk_store_module.cache, "set_json"):
            ParentChunkStore().upsert_documents(docs)

        ensure_parent_chunk_schema.assert_called_once()


if __name__ == "__main__":
    unittest.main()
