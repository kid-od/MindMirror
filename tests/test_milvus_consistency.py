import importlib
import sys
import types
import unittest
from unittest.mock import patch


def _load_milvus_client_module():
    dotenv_module = types.ModuleType("dotenv")
    dotenv_module.load_dotenv = lambda *args, **kwargs: None

    pymilvus_module = types.ModuleType("pymilvus")

    class _DataType:
        INT64 = "INT64"
        FLOAT_VECTOR = "FLOAT_VECTOR"
        SPARSE_FLOAT_VECTOR = "SPARSE_FLOAT_VECTOR"
        VARCHAR = "VARCHAR"

    class _AnnSearchRequest:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class _RRFRanker:
        def __init__(self, k):
            self.k = k

    class _MilvusClient:
        def __init__(self, uri):
            self.uri = uri

    pymilvus_module.MilvusClient = _MilvusClient
    pymilvus_module.DataType = _DataType
    pymilvus_module.AnnSearchRequest = _AnnSearchRequest
    pymilvus_module.RRFRanker = _RRFRanker

    pymilvus_exceptions = types.ModuleType("pymilvus.exceptions")

    class _MilvusException(Exception):
        pass

    pymilvus_exceptions.MilvusException = _MilvusException

    with patch.dict(
        sys.modules,
        {
            "dotenv": dotenv_module,
            "pymilvus": pymilvus_module,
            "pymilvus.exceptions": pymilvus_exceptions,
        },
    ):
        import backend.milvus_client as milvus_client_module

        return importlib.reload(milvus_client_module)


class _RecordingClient:
    def __init__(self):
        self.insert_calls = []
        self.flush_calls = []
        self.delete_calls = []
        self.query_calls = []
        self.search_calls = []
        self.hybrid_search_calls = []

    def insert(self, collection_name, data):
        self.insert_calls.append({"collection_name": collection_name, "data": data})
        return {"insert_count": len(data)}

    def flush(self, collection_name):
        self.flush_calls.append({"collection_name": collection_name})
        return {"flushed": True}

    def delete(self, collection_name, filter):
        self.delete_calls.append({"collection_name": collection_name, "filter": filter})
        return {"delete_count": 1}

    def query(self, **kwargs):
        self.query_calls.append(kwargs)
        return []

    def search(self, **kwargs):
        self.search_calls.append(kwargs)
        return [[{"id": 1, "entity": {"text": "essay", "filename": "随笔1.md", "file_type": "Markdown", "page_number": 0, "chunk_id": "essay::0", "parent_chunk_id": "", "root_chunk_id": "", "chunk_level": 3, "chunk_idx": 0, "visibility": "private", "owner_id": "alice", "document_domain": "essay"}, "distance": 0.9}]]

    def hybrid_search(self, **kwargs):
        self.hybrid_search_calls.append(kwargs)
        return [[{"id": 1, "text": "essay", "filename": "随笔1.md", "file_type": "Markdown", "page_number": 0, "chunk_id": "essay::0", "parent_chunk_id": "", "root_chunk_id": "", "chunk_level": 3, "chunk_idx": 0, "visibility": "private", "owner_id": "alice", "document_domain": "essay", "distance": 0.9}]]


class MilvusConsistencyGuardTest(unittest.TestCase):
    def test_insert_flushes_collection_for_read_your_writes(self):
        milvus_client_module = _load_milvus_client_module()
        client = _RecordingClient()

        with patch.object(milvus_client_module, "MilvusClient", return_value=client):
            manager = milvus_client_module.MilvusManager()
            manager.insert([{"filename": "随笔1.md"}])

        self.assertEqual(len(client.insert_calls), 1)
        self.assertEqual(client.flush_calls, [{"collection_name": manager.collection_name}])

    def test_delete_flushes_collection_for_immediate_visibility(self):
        milvus_client_module = _load_milvus_client_module()
        client = _RecordingClient()

        with patch.object(milvus_client_module, "MilvusClient", return_value=client):
            manager = milvus_client_module.MilvusManager()
            manager.delete('filename == "随笔1.md"')

        self.assertEqual(len(client.delete_calls), 1)
        self.assertEqual(client.flush_calls, [{"collection_name": manager.collection_name}])

    def test_query_paths_use_strong_consistency(self):
        milvus_client_module = _load_milvus_client_module()
        client = _RecordingClient()

        with patch.object(milvus_client_module, "MilvusClient", return_value=client):
            manager = milvus_client_module.MilvusManager()
            manager.query(filter_expr='owner_id == "alice"')
            manager.query_all(filter_expr='owner_id == "alice"')
            manager.dense_retrieve([0.1, 0.2], top_k=1, filter_expr='owner_id == "alice"')
            manager.hybrid_retrieve([0.1, 0.2], {1: 0.5}, top_k=1, filter_expr='owner_id == "alice"')

        self.assertEqual(client.query_calls[0]["consistency_level"], "Strong")
        self.assertEqual(client.query_calls[1]["consistency_level"], "Strong")
        self.assertEqual(client.search_calls[0]["consistency_level"], "Strong")
        self.assertEqual(client.hybrid_search_calls[0]["consistency_level"], "Strong")


if __name__ == "__main__":
    unittest.main()
