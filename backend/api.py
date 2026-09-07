from __future__ import annotations

import hmac
import os
import threading
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.channels import (
    bundled_root,
    categories_for_channels,
    channel_to_dict,
    countries_for_channels,
    default_channels_file,
    filter_channels,
    load_channels,
)
from backend.updater import DEFAULT_LIMIT, refresh_channels

API_VERSION = "2.2.0"
_TRUTHY_ENV = {"1", "true", "yes", "on"}
_DEPLOY_ENV_VARS = ("FLY_APP_NAME", "FLY_MACHINE_ID", "VERCEL")


def _web_dir() -> Path:
    # Uses bundled_root() (sys._MEIPASS when frozen) rather than a
    # __file__-relative path, since PyInstaller's handling of __file__ for
    # bytecode-archived modules isn't something to lean on directly - this
    # matches the pattern backend.channels already uses for the same reason.
    return bundled_root() / "web"


def _static_dir() -> Path:
    return _web_dir() / "static"


def _branding_dir() -> Path:
    return bundled_root() / "assets" / "branding"


def _utc_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_refresh_state() -> dict[str, object]:
    return {
        "status": "idle",
        "message": "Ready to refresh the shared channel catalog.",
        "started_at": None,
        "finished_at": None,
        "last_result": None,
        "last_error": None,
    }


def _truthy_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in _TRUTHY_ENV


def admin_token_is_required(configured_token: str = "") -> bool:
    """True when refresh must not run without a configured admin token.

    Local desktop/`--serve-api` stays open if no token is set. Fly, Vercel,
    Docker (`ADAMSY_REQUIRE_ADMIN_TOKEN=1`), or an explicit token all require
    one so public deploys cannot rebuild the catalog anonymously.
    """
    if configured_token.strip():
        return True
    if _truthy_env("ADAMSY_REQUIRE_ADMIN_TOKEN"):
        return True
    return any(os.getenv(name, "").strip() for name in _DEPLOY_ENV_VARS)


def _admin_tokens_match(provided: str, configured: str) -> bool:
    if not provided or not configured or len(provided) != len(configured):
        return False
    return hmac.compare_digest(provided, configured)


def cors_allow_origins() -> list[str]:
    """Browser origins allowed to call the public JSON API.

    Default is `*` because the catalog is public, cookies are not used
    (`allow_credentials=False`), and the web UI / desktop webview / third-party
    IPTV clients all need to reach the API from varying hosts. Set
    `ADAMSY_CORS_ORIGINS` to a comma-separated list to tighten a deploy.
    """
    raw = os.getenv("ADAMSY_CORS_ORIGINS", "*").strip()
    if not raw or raw == "*":
        return ["*"]
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return origins or ["*"]


def create_app(channels_file: Path | None = None) -> FastAPI:
    app = FastAPI(
        title="Adamsy Free TV API",
        version=API_VERSION,
        summary="API and web preview for Adamsy Free TV.",
    )
    app.state.channels_file = channels_file or default_channels_file()
    app.state.refresh_state = _default_refresh_state()
    app.state.refresh_lock = threading.Lock()
    app.state.admin_token = os.getenv("ADAMSY_ADMIN_TOKEN", "").strip()
    app.state.admin_token_required = admin_token_is_required(app.state.admin_token)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_allow_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    if _static_dir().exists():
        app.mount("/static", StaticFiles(directory=_static_dir()), name="static")
    if _branding_dir().exists():
        app.mount("/brand", StaticFiles(directory=_branding_dir()), name="brand")

    def _load_current_channels() -> list[dict[str, str]]:
        channels = load_channels(app.state.channels_file)
        return [channel_to_dict(channel) for channel in channels]

    def _read_refresh_state() -> dict[str, object]:
        with app.state.refresh_lock:
            refresh_state = dict(app.state.refresh_state)
        if isinstance(refresh_state.get("last_result"), dict):
            refresh_state["last_result"] = dict(refresh_state["last_result"])
        return refresh_state

    def _update_refresh_state(**updates: object) -> dict[str, object]:
        with app.state.refresh_lock:
            app.state.refresh_state.update(updates)
            refresh_state = dict(app.state.refresh_state)
        if isinstance(refresh_state.get("last_result"), dict):
            refresh_state["last_result"] = dict(refresh_state["last_result"])
        return refresh_state

    def _require_admin(x_admin_token: str | None) -> None:
        configured = app.state.admin_token
        provided = x_admin_token or ""
        if not app.state.admin_token_required:
            return
        if not configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Admin refresh is disabled until ADAMSY_ADMIN_TOKEN is set.",
            )
        if not _admin_tokens_match(provided, configured):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="A valid admin token is required to refresh channels.",
            )

    @app.get("/", include_in_schema=False)
    def web_index() -> FileResponse:
        return FileResponse(_web_dir() / "index.html")

    @app.get("/service-worker.js", include_in_schema=False)
    def service_worker() -> FileResponse:
        # Served from the root (not /static/) so its default scope covers
        # the whole app - a service worker's scope is limited to its own
        # directory and below unless served from a broader path.
        return FileResponse(
            _static_dir() / "service-worker.js",
            media_type="text/javascript",
        )

    @app.get("/health")
    def health() -> dict[str, object]:
        return {
            "status": "ok",
            "service": "adamsy-free-tv-api",
            "version": API_VERSION,
            "admin_token_required": app.state.admin_token_required,
            "refresh_status": _read_refresh_state()["status"],
        }

    @app.get("/channels")
    def list_channels(
        search: str = "",
        category: str = "All",
        country: str = "All",
        limit: int = Query(default=100, ge=1, le=5000),
        offset: int = Query(default=0, ge=0),
    ) -> dict[str, object]:
        channels = load_channels(app.state.channels_file)
        filtered = filter_channels(channels, query=search, category=category, country=country)
        items = [channel_to_dict(channel) for channel in filtered[offset : offset + limit]]
        return {
            "items": items,
            "total": len(filtered),
            "limit": limit,
            "offset": offset,
            "filters": {
                "search": search,
                "category": category,
                "country": country,
            },
        }

    @app.get("/channels/categories")
    def list_categories() -> dict[str, object]:
        channels = load_channels(app.state.channels_file)
        items = categories_for_channels(channels)
        return {
            "items": items,
            "total": len(items),
        }

    @app.get("/channels/countries")
    def list_countries() -> dict[str, object]:
        channels = load_channels(app.state.channels_file)
        items = countries_for_channels(channels)
        return {
            "items": items,
            "total": len(items),
        }

    @app.get("/channels/source")
    def channel_source() -> dict[str, object]:
        return {
            "channels_file": str(app.state.channels_file),
            "channel_count": len(_load_current_channels()),
        }

    @app.get("/admin/refresh")
    def refresh_status_view() -> dict[str, object]:
        refresh_state = _read_refresh_state()
        refresh_state["admin_token_required"] = app.state.admin_token_required
        return refresh_state

    @app.post("/admin/refresh", status_code=status.HTTP_202_ACCEPTED)
    def refresh_catalog(
        limit: int = Query(
            default=DEFAULT_LIMIT,
            ge=0,
            le=50000,
            description="Max channels to keep. 0 means no cap - keep every channel from the public source.",
        ),
        category: str | None = None,
        country: str | None = None,
        verify_live: bool = False,
        x_admin_token: str | None = Header(default=None),
    ) -> dict[str, object]:
        _require_admin(x_admin_token)

        refresh_state = _read_refresh_state()
        if refresh_state["status"] == "running":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A refresh is already running.",
            )

        _update_refresh_state(
            status="running",
            message="Fetching the latest public channel playlist.",
            started_at=_utc_timestamp(),
            finished_at=None,
            last_result=None,
            last_error=None,
        )

        try:
            result = refresh_channels(
                limit=limit,
                category=category,
                country=country,
                output_path=app.state.channels_file,
                verify_live=verify_live,
                progress=lambda message: _update_refresh_state(message=message),
            )
        except Exception as exc:
            return _update_refresh_state(
                status="error",
                message="Refresh failed.",
                finished_at=_utc_timestamp(),
                last_error=str(exc),
            )

        return _update_refresh_state(
            status="success",
            message="Refresh complete.",
            finished_at=_utc_timestamp(),
            last_error=None,
            last_result=result,
        )

    return app


app = create_app()


def run_api(
    host: str = "127.0.0.1",
    port: int = 8000,
    channels_file: Path | None = None,
) -> None:
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "uvicorn is required to serve the API. Install dependencies from requirements.txt first."
        ) from exc

    uvicorn.run(create_app(channels_file=channels_file), host=host, port=port, reload=False)
