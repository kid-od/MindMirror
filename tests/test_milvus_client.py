import importlib
import sys
import types
import unittest
from unittest.mock import patch

try:
    from pymilvus.exceptions import MilvusException
except ModuleNotFoundError:  # pragma: no cover - local test fallback
    class MilvusException(Exception):
        def __init__(self, code=None, message=""):
            super().__init__(message)
            self.code = code


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
    pymilvus_exceptions.MilvusException = MilvusException

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


class _ClosedChannelClient:
    def has_collection(self, *args, **kwargs):
        raise MilvusException(code=1, message="Unexpected error, message=<Cannot invoke RPC on closed channel!>")

    def query(self, *args, **kwargs):
        raise MilvusException(code=1, message="Unexpected error, message=<Cannot invoke RPC on closed channel!>")


class _ClosedChannelValueErrorClient:
    def has_collection(self, *args, **kwargs):
        raise ValueError("Cannot invoke RPC on closed channel!")


class _ClosedChannelHybridClient:
    def hybrid_search(self, *args, **kwargs):
        raise MilvusException(code=1, message="Unexpected error, message=<Cannot invoke RPC on closed channel!>")


class _HealthyClient:
    def __init__(self, payload, hybrid_payload=None):
        self.payload = payload
        self.hybrid_payload = hybrid_payload or [[{
            "id": 1,
            "text": "demo",
            "filename": "demo.pdf",
            "file_type": "PDF",
            "page_number": 1,
            "chunk_id": "demo::0",
            "parent_chunk_id": "",
            "root_chunk_id": "demo",
            "chunk_level": 3,
            "chunk_idx": 0,
            "visibility": "public",
            "owner_id": "",
            "document_domain": "knowledge",
            "distance": 0.91,
        }]]
        self.closed = False

    def has_collection(self, *args, **kwargs):
        return True

    def query(self, *args, **kwargs):
        return self.payload

    def hybrid_search(self, *args, **kwargs):
        return self.hybrid_payload

    def close(self):
        self.closed = True


class MilvusReconnectTest(unittest.TestCase):
    def test_recreates_client_during_init_collection_after_closed_channel_error(self):
        milvus_client_module = _load_milvus_client_module()

        created = []

        def fake_constructor(uri):
            created.append(uri)
            if len(created) == 1:
                return _ClosedChannelClient()
            return _HealthyClient([])

        with patch.object(milvus_client_module, "MilvusClient", side_effect=fake_constructor):
            manager = milvus_client_module.MilvusManager()
            manager.init_collection()

        self.assertEqual(len(created), 2)

    def test_recreates_client_after_closed_channel_error(self):
        milvus_client_module = _load_milvus_client_module()

        created = []

        def fake_constructor(uri):
            created.append(uri)
            if len(created) == 1:
                return _ClosedChannelClient()
            return _HealthyClient([{"filename": "demo.pdf"}])

        with patch.object(milvus_client_module, "MilvusClient", side_effect=fake_constructor):
            manager = milvus_client_module.MilvusManager()
            result = manager.query()

        self.assertEqual(result, [{"filename": "demo.pdf"}])
        self.assertEqual(len(created), 2)

    def test_recreates_client_after_closed_channel_value_error(self):
        milvus_client_module = _load_milvus_client_module()

        created = []

        def fake_constructor(uri):
            created.append(uri)
            if len(created) == 1:
                return _ClosedChannelValueErrorClient()
            return _HealthyClient([])

        with patch.object(milvus_client_module, "MilvusClient", side_effect=fake_constructor):
            manager = milvus_client_module.MilvusManager()
            manager.init_collection()

        self.assertEqual(len(created), 2)

    def test_recreates_client_for_hybrid_search_after_closed_channel_error(self):
        milvus_client_module = _load_milvus_client_module()

        created = []

        def fake_constructor(uri):
            created.append(uri)
            if len(created) == 1:
                return _ClosedChannelHybridClient()
            return _HealthyClient([])

        with patch.object(milvus_client_module, "MilvusClient", side_effect=fake_constructor):
            manager = milvus_client_module.MilvusManager()
            result = manager.hybrid_retrieve([0.1, 0.2], {1: 0.5}, top_k=1)

        self.assertEqual(result[0]["filename"], "demo.pdf")
        self.assertEqual(len(created), 2)

    def test_refreshes_idle_client_before_next_request(self):
        milvus_client_module = _load_milvus_client_module()

        first_client = _HealthyClient([{"filename": "first.pdf"}])
        second_client = _HealthyClient([{"filename": "second.pdf"}])

        with patch.object(milvus_client_module, "MilvusClient", side_effect=[first_client, second_client]):
            manager = milvus_client_module.MilvusManager()
            manager.client_max_idle_seconds = 300

            with patch.object(milvus_client_module.time, "monotonic", side_effect=[0.0, 301.0, 301.0]):
                first_result = manager.query()
                second_result = manager.query()

        self.assertEqual(first_result, [{"filename": "first.pdf"}])
        self.assertEqual(second_result, [{"filename": "second.pdf"}])
        self.assertTrue(first_client.closed)


if __name__ == "__main__":
    unittest.main()
