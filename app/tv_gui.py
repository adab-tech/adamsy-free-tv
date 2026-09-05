"""
Desktop shell for Adamsy Free TV.

Wraps the same web UI used in the browser (the FastAPI backend plus the
web/ frontend) in a native window via pywebview, instead of a separate
Tkinter/VLC interface. Playback happens through the OS's built-in
browser engine (WebView2 on Windows) using the same HTML5 video +
hls.js player as the web app, so no VLC install is required.
"""
from __future__ import annotations

import socket
import time
from pathlib import Path
from threading import Thread

import webview

from backend.api import create_app
from backend.channels import default_channels_file


def _find_free_port(preferred: int = 8000) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            probe.bind(("127.0.0.1", 0))
            return probe.getsockname()[1]


def _run_server(port: int, channels_file: Path) -> None:
    import uvicorn

    app = create_app(channels_file=channels_file)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def _wait_until_ready(port: int, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.25):
                return
        except OSError:
            time.sleep(0.1)


def launch_tv_gui(channels_file: Path | None = None) -> None:
    if channels_file is None:
        channels_file = default_channels_file()

    port = _find_free_port()
    Thread(target=_run_server, args=(port, channels_file), daemon=True).start()
    _wait_until_ready(port)

    webview.create_window(
        "Adamsy Free TV",
        f"http://127.0.0.1:{port}/",
        width=1360,
        height=860,
        min_size=(960, 640),
    )
    webview.start()
