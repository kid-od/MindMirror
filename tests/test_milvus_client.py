import unittest
from unittest.mock import patch

from pymilvus.exceptions import MilvusException


class _ClosedChannelClient:
    def has_collection(self, *args, **kwargs):
        raise MilvusException(code=1, message="Unexpected error, message=<Cannot invoke RPC on closed channel!>")

    def query(self, *args, **kwargs):
        raise MilvusException(code=1, message="Unexpected error, message=<Cannot invoke RPC on closed channel!>")


class _HealthyClient:
    def __init__(self, payload):
        self.payload = payload

    def has_collection(self, *args, **kwargs):
        return True

    def query(self, *args, **kwargs):
        return self.payload


class MilvusReconnectTest(unittest.TestCase):
    def test_recreates_client_during_init_collection_after_closed_channel_error(self):
        from backend.milvus_client import MilvusManager

        created = []

        def fake_constructor(uri):
            created.append(uri)
            if len(created) == 1:
                return _ClosedChannelClient()
            return _HealthyClient([])

        with patch("backend.milvus_client.MilvusClient", side_effect=fake_constructor):
            manager = MilvusManager()
            manager.init_collection()

        self.assertEqual(len(created), 2)

    def test_recreates_client_after_closed_channel_error(self):
        from backend.milvus_client import MilvusManager

        created = []

        def fake_constructor(uri):
            created.append(uri)
            if len(created) == 1:
                return _ClosedChannelClient()
            return _HealthyClient([{"filename": "demo.pdf"}])

        with patch("backend.milvus_client.MilvusClient", side_effect=fake_constructor):
            manager = MilvusManager()
            result = manager.query()

        self.assertEqual(result, [{"filename": "demo.pdf"}])
        self.assertEqual(len(created), 2)


if __name__ == "__main__":
    unittest.main()
