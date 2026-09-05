from unittest import mock

import pytest
from fastapi.testclient import TestClient

from backend import updater
from backend.api import create_app


def test_health():
    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "adamsy-free-tv-api"


def test_channels_list():
    app = create_app()
    client = TestClient(app)
    response = client.get("/channels")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0


def test_web_app_assets_are_served():
    # Regression test: VirtualTV.spec's PyInstaller `datas` list once only
    # bundled tv_channels.json and a single icon, so the frozen desktop app
    # (which now serves this same web UI via pywebview) had no web/index.html
    # or assets/branding/*.png to find - FileResponse raised, and pywebview
    # showed an "internal server error" on first load. This exercises every
    # route that reads from _web_dir()/_static_dir()/_branding_dir().
    app = create_app()
    client = TestClient(app)

    index = client.get("/")
    assert index.status_code == 200
    assert "<title>" in index.text

    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/manifest.webmanifest").status_code == 200
    assert client.get("/service-worker.js").status_code == 200
    assert client.get("/brand/adamsy-free-tv-icon-192.png").status_code == 200


def test_admin_refresh_requires_token_when_configured(monkeypatch):
    monkeypatch.setenv("ADAMSY_ADMIN_TOKEN", "super-secret-token")
    app = create_app()
    client = TestClient(app)

    response = client.post("/admin/refresh")
    assert response.status_code == 401

    response = client.post("/admin/refresh", headers={"x-admin-token": "wrong-token"})
    assert response.status_code == 401


def test_admin_refresh_open_when_no_token_configured(monkeypatch, tmp_path):
    monkeypatch.delenv("ADAMSY_ADMIN_TOKEN", raising=False)
    app = create_app(channels_file=tmp_path / "tv_channels.json")
    client = TestClient(app)

    fake_m3u = (
        '#EXTM3U\n#EXTINF:-1 tvg-country="NG" group-title="News",Sample\n'
        "https://example.com/sample.m3u8\n"
    )
    with mock.patch("backend.updater._fetch", return_value=fake_m3u):
        response = client.post("/admin/refresh")
    assert response.status_code == 202


@pytest.mark.parametrize("limit", [0, -1])
def test_refresh_channels_unlimited_keeps_every_channel(tmp_path, limit):
    fake_m3u = "#EXTM3U\n"
    for i in range(1200):
        fake_m3u += f'#EXTINF:-1 tvg-country="NG" group-title="News",Channel {i}\n'
        fake_m3u += f"https://example.com/{i}.m3u8\n"

    output_path = tmp_path / "tv_channels.json"
    with mock.patch.object(updater, "_fetch", return_value=fake_m3u):
        result = updater.refresh_channels(limit=limit, output_path=output_path)

    assert result["selected"] == 1200
    assert result["requested_limit"] == "unlimited"


def test_refresh_channels_rejects_non_http_sources(tmp_path):
    with pytest.raises(ValueError):
        updater._fetch("file:///etc/passwd")


def test_probe_stream_rejects_non_http_urls():
    assert updater._probe_stream("file:///etc/passwd", timeout=1) is False
