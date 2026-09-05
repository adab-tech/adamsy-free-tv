import socket

import pytest

pytest.importorskip("webview")

from app import tv_gui


def test_find_free_port_returns_a_valid_port():
    port = tv_gui._find_free_port()
    assert 0 < port < 65536


def test_wait_until_ready_returns_once_port_is_listening():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]
        # Should return promptly rather than raise or block for the full timeout.
        tv_gui._wait_until_ready(port, timeout=1.0)
