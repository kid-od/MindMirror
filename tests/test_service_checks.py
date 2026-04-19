import unittest
from unittest.mock import patch


class EnsureTcpServiceTest(unittest.TestCase):
    def test_raises_clear_error_when_service_is_unreachable(self):
        from backend.service_checks import ensure_tcp_service

        with patch("backend.service_checks.socket.create_connection", side_effect=OSError("refused")):
            with self.assertRaises(RuntimeError) as ctx:
                ensure_tcp_service("127.0.0.1", 19530, "Milvus", timeout=0.1)

        self.assertIn("Milvus 服务不可达", str(ctx.exception))
        self.assertIn("127.0.0.1:19530", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
