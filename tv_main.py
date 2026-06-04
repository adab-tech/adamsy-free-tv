"""
Adamsy Free TV entry point.

Usage:
    python tv_main.py
    python tv_main.py --refresh-channels --verify-live
"""
from __future__ import annotations

import argparse
from pathlib import Path

import tv_updater
from backend.channels import default_channels_file
from app.tv_gui import launch_tv_gui


def _default_channels_file() -> Path:
    return default_channels_file()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Launch Adamsy Free TV or refresh channels.")
    parser.add_argument(
        "--refresh-channels",
        action="store_true",
        help="Update tv_channels.json instead of opening the GUI.",
    )
    parser.add_argument(
        "--serve-api",
        action="store_true",
        help="Start the read-only backend API instead of opening the GUI.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="API host when using --serve-api.")
    parser.add_argument("--port", type=int, default=8000, help="API port when using --serve-api.")
    args, passthrough = parser.parse_known_args(argv)

    if args.refresh_channels:
        if "--output" not in passthrough and not any(arg.startswith("--output=") for arg in passthrough):
            passthrough.extend(["--output", str(_default_channels_file())])
        tv_updater.main(passthrough)
        return

    if args.serve_api:
        from backend.api import run_api

        run_api(host=args.host, port=args.port, channels_file=_default_channels_file())
        return

    launch_tv_gui()


if __name__ == "__main__":
    main()
