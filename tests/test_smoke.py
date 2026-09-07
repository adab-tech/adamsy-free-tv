from pathlib import Path
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from backend import updater
from backend.api import create_app

_FAKE_M3U = (
    '#EXTM3U\n#EXTINF:-1 tvg-country="NG" group-title="News",Sample\n'
    "https://example.com/sample.m3u8\n"
)
_DEPLOY_ENV = (
    "ADAMSY_ADMIN_TOKEN",
    "ADAMSY_REQUIRE_ADMIN_TOKEN",
    "ADAMSY_CORS_ORIGINS",
    "FLY_APP_NAME",
    "FLY_MACHINE_ID",
    "VERCEL",
)


def _clear_deploy_env(monkeypatch) -> None:
    for name in _DEPLOY_ENV:
        monkeypatch.delenv(name, raising=False)


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
    _clear_deploy_env(monkeypatch)
    monkeypatch.setenv("ADAMSY_ADMIN_TOKEN", "super-secret-token")
    app = create_app()
    client = TestClient(app)

    response = client.post("/admin/refresh")
    assert response.status_code == 401

    response = client.post("/admin/refresh", headers={"x-admin-token": "wrong-token"})
    assert response.status_code == 401

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["admin_token_required"] is True


def test_admin_refresh_open_when_no_token_configured(monkeypatch, tmp_path):
    _clear_deploy_env(monkeypatch)
    app = create_app(channels_file=tmp_path / "tv_channels.json")
    client = TestClient(app)

    with mock.patch("backend.updater._fetch", return_value=_FAKE_M3U):
        response = client.post("/admin/refresh")
    assert response.status_code == 202
    assert client.get("/health").json()["admin_token_required"] is False


def test_admin_refresh_succeeds_with_matching_token(monkeypatch, tmp_path):
    _clear_deploy_env(monkeypatch)
    monkeypatch.setenv("ADAMSY_ADMIN_TOKEN", "super-secret-token")
    app = create_app(channels_file=tmp_path / "tv_channels.json")
    client = TestClient(app)

    with mock.patch("backend.updater._fetch", return_value=_FAKE_M3U):
        response = client.post(
            "/admin/refresh",
            headers={"x-admin-token": "super-secret-token"},
        )
    assert response.status_code == 202


@pytest.mark.parametrize(
    "env_name,env_value",
    [
        ("FLY_APP_NAME", "adamsy-free-tv"),
        ("VERCEL", "1"),
        ("ADAMSY_REQUIRE_ADMIN_TOKEN", "1"),
    ],
)
def test_admin_refresh_refuses_open_access_when_deployed(monkeypatch, tmp_path, env_name, env_value):
    _clear_deploy_env(monkeypatch)
    monkeypatch.setenv(env_name, env_value)
    app = create_app(channels_file=tmp_path / "tv_channels.json")
    client = TestClient(app)

    response = client.post("/admin/refresh")
    assert response.status_code == 503
    assert "ADAMSY_ADMIN_TOKEN" in response.json()["detail"]
    assert client.get("/health").json()["admin_token_required"] is True
    # Status polling used by the web UI stays public so page load does not fail.
    assert client.get("/admin/refresh").status_code == 200


def test_cors_default_allows_any_origin(monkeypatch):
    _clear_deploy_env(monkeypatch)
    app = create_app()
    client = TestClient(app)
    response = client.get("/health", headers={"Origin": "https://example.com"})
    assert response.headers.get("access-control-allow-origin") == "*"


def test_cors_origins_can_be_restricted(monkeypatch):
    _clear_deploy_env(monkeypatch)
    monkeypatch.setenv("ADAMSY_CORS_ORIGINS", "https://tv.example.com")
    app = create_app()
    client = TestClient(app)

    allowed = client.get("/health", headers={"Origin": "https://tv.example.com"})
    assert allowed.headers.get("access-control-allow-origin") == "https://tv.example.com"

    denied = client.get("/health", headers={"Origin": "https://evil.example"})
    assert denied.headers.get("access-control-allow-origin") != "https://evil.example"


def test_docker_and_fly_listen_on_the_same_port():
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    fly = Path("fly.toml").read_text(encoding="utf-8")
    assert "internal_port = 8080" in fly
    assert 'PORT = \'8080\'' in fly or 'PORT = "8080"' in fly
    assert "memory = '256mb'" in fly or 'memory = "256mb"' in fly
    assert "memory_mb" not in fly
    assert "--port\", \"8080\"" in dockerfile
    assert "uvicorn" in dockerfile
    assert "fastapi\", \"run\"" not in dockerfile
    assert "ADAMSY_REQUIRE_ADMIN_TOKEN=1" in dockerfile


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
