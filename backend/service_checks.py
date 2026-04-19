import socket


def ensure_tcp_service(host: str, port: int, service_name: str, timeout: float = 1.5) -> None:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return None
    except OSError as exc:
        raise RuntimeError(
            f"{service_name} 服务不可达，请先确认 {host}:{port} 已启动并可访问。"
        ) from exc
