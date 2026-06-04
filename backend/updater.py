from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

from backend.channels import default_channels_file

M3U_SOURCES: list[tuple[str, str]] = [
    ("All", "https://iptv-org.github.io/iptv/index.m3u"),
]

OUTPUT_FILE = default_channels_file()
DEFAULT_LIMIT = 700
DEFAULT_VERIFY_TIMEOUT = 4
DEFAULT_VERIFY_WORKERS = 24

_RE_NAME = re.compile(r",(.+)$")
_RE_COUNTRY = re.compile(r'tvg-country="([^"]*)"')
_RE_GROUP = re.compile(r'group-title="([^"]*)"')


def _emit(progress: Callable[[str], None] | None, message: str) -> None:
    if progress:
        progress(message)
    print(message, flush=True)


def _fetch(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "VirtualTV-Updater/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        return resp.read().decode("utf-8", errors="replace")


def _probe_stream(url: str, timeout: int) -> bool:
    headers = {
        "User-Agent": "VirtualTV-Updater/1.0",
        "Range": "bytes=0-2047",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            status = getattr(resp, "status", 200)
            if status >= 400:
                return False
            chunk = resp.read(2048)
            return len(chunk) > 0
    except urllib.error.HTTPError as exc:
        return exc.code in {401, 403, 405, 416}
    except Exception:
        return False


def _parse_m3u(content: str) -> list[dict[str, str]]:
    channels: list[dict[str, str]] = []
    lines = content.splitlines()
    n = len(lines)
    i = 0
    while i < n:
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            name_match = _RE_NAME.search(line)
            name = name_match.group(1).strip() if name_match else "Unknown"

            country_match = _RE_COUNTRY.search(line)
            country = country_match.group(1).strip() if country_match else ""

            category_match = _RE_GROUP.search(line)
            category = category_match.group(1).strip() if category_match else "General"

            i += 1
            while i < n and not lines[i].strip():
                i += 1
            if i < n:
                url = lines[i].strip()
                if url and not url.startswith("#"):
                    channels.append(
                        {
                            "name": name,
                            "url": url,
                            "country": country,
                            "category": category,
                        }
                    )
        i += 1
    return channels


def _filter(
    channels: list[dict[str, str]],
    category: str | None,
    country: str | None,
) -> list[dict[str, str]]:
    if category:
        query = category.lower()
        channels = [channel for channel in channels if query in channel["category"].lower()]
    if country:
        query = country.upper()
        channels = [channel for channel in channels if channel["country"].upper() == query]
    return channels


def _unique_channels(channels: list[dict[str, str]]) -> list[dict[str, str]]:
    seen_urls: set[str] = set()
    unique: list[dict[str, str]] = []
    for channel in channels:
        if channel["url"] not in seen_urls:
            seen_urls.add(channel["url"])
            unique.append(channel)
    return unique


def _select_verified_channels(
    channels: list[dict[str, str]],
    limit: int,
    max_checks: int,
    timeout: int,
    workers: int,
    progress: Callable[[str], None] | None = None,
) -> list[dict[str, str]]:
    candidates = channels[:max_checks]
    if not candidates:
        return []

    selected: list[dict[str, str]] = []
    tested = 0
    reachable = 0

    _emit(
        progress,
        f"Verifying up to {len(candidates):,} candidate streams (timeout={timeout}s, workers={workers})...",
    )

    batch_size = max(workers * 8, 200)
    start = 0
    while start < len(candidates) and len(selected) < limit:
        batch = candidates[start : start + batch_size]
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            future_map = {
                pool.submit(_probe_stream, channel["url"], timeout): channel
                for channel in batch
            }

            for future in concurrent.futures.as_completed(future_map):
                tested += 1
                channel = future_map[future]
                try:
                    ok = future.result()
                except Exception:
                    ok = False

                if ok:
                    reachable += 1
                    selected.append(channel)

                if tested % 100 == 0:
                    _emit(progress, f"Checked {tested:,}/{len(candidates):,} streams | reachable: {reachable:,}")

                if len(selected) >= limit:
                    break

        start += batch_size

    _emit(progress, f"Checked {tested:,}/{len(candidates):,} streams | reachable: {reachable:,}")
    if len(selected) > limit:
        selected = selected[:limit]

    _emit(progress, f"Verification complete: {len(selected):,} reachable channels selected.")
    return selected


def fetch_catalog() -> list[dict[str, str]]:
    all_channels: list[dict[str, str]] = []
    for label, url in M3U_SOURCES:
        print(f"Fetching {label} playlist... ({url})", flush=True)
        content = _fetch(url, timeout=45)
        parsed = _parse_m3u(content)
        print(f"  Parsed {len(parsed):,} entries from '{label}'.")
        all_channels.extend(parsed)
    return _unique_channels(all_channels)


def refresh_channels(
    *,
    limit: int = DEFAULT_LIMIT,
    category: str | None = None,
    country: str | None = None,
    output_path: str | Path | None = None,
    verify_live: bool = False,
    verify_count: int = 1800,
    verify_timeout: int = DEFAULT_VERIFY_TIMEOUT,
    verify_workers: int = DEFAULT_VERIFY_WORKERS,
    progress: Callable[[str], None] | None = None,
) -> dict[str, object]:
    out_path = Path(output_path) if output_path else OUTPUT_FILE
    out_path.parent.mkdir(parents=True, exist_ok=True)

    all_channels: list[dict[str, str]] = []
    for label, url in M3U_SOURCES:
        _emit(progress, f"Fetching {label} playlist...")
        try:
            content = _fetch(url, timeout=45)
        except Exception as exc:
            _emit(progress, f"Failed to fetch {url}: {exc}")
            continue
        parsed = _parse_m3u(content)
        _emit(progress, f"Parsed {len(parsed):,} entries from {label}.")
        all_channels.extend(parsed)

    if not all_channels:
        raise RuntimeError("No channels were retrieved from the configured sources.")

    unique = _unique_channels(all_channels)
    _emit(progress, f"Collected {len(unique):,} unique channels.")

    filtered = _filter(unique, category, country)
    if not filtered:
        raise ValueError("No channels matched the selected filters.")

    _emit(progress, f"{len(filtered):,} channels matched the current refresh filters.")

    if verify_live:
        selected = _select_verified_channels(
            channels=filtered,
            limit=limit,
            max_checks=max(limit, verify_count),
            timeout=max(1, verify_timeout),
            workers=max(1, verify_workers),
            progress=progress,
        )
    else:
        selected = filtered[:limit]

    if not selected:
        raise RuntimeError("No channels were selected for output.")

    out_path.write_text(json.dumps(selected, indent=2, ensure_ascii=False), encoding="utf-8")
    _emit(progress, f"Saved {len(selected):,} channels to {out_path}.")

    return {
        "output_path": str(out_path),
        "requested_limit": limit,
        "selected": len(selected),
        "unique_channels": len(unique),
        "filtered_channels": len(filtered),
        "verify_live": verify_live,
        "category": category or "All",
        "country": country or "All",
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Update tv_channels.json from iptv-org public playlists.")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Max channels to save (default 700).")
    parser.add_argument("--category", type=str, default=None, help="Filter by category, for example News.")
    parser.add_argument("--country", type=str, default=None, help="Filter by 2-letter country code, for example NG.")
    parser.add_argument("--list-countries", action="store_true", help="List all country codes in the feed and exit.")
    parser.add_argument("--output", type=str, default=str(OUTPUT_FILE), help="Output JSON file path.")
    parser.add_argument("--verify-live", action="store_true", help="Probe channel URLs and keep only reachable streams.")
    parser.add_argument("--verify-count", type=int, default=1800, help="How many candidates to probe when --verify-live is enabled.")
    parser.add_argument("--verify-timeout", type=int, default=DEFAULT_VERIFY_TIMEOUT, help="Per-stream probe timeout seconds.")
    parser.add_argument("--verify-workers", type=int, default=DEFAULT_VERIFY_WORKERS, help="Concurrent probe workers.")
    args = parser.parse_args(argv)

    out_path = Path(args.output)

    if args.list_countries:
        try:
            unique_channels = fetch_catalog()
        except Exception as exc:
            print(str(exc), file=sys.stderr)
            sys.exit(1)
        codes = sorted({channel["country"] for channel in unique_channels if channel["country"]})
        print("\nCountry codes found:")
        for code in codes:
            print(f"  {code}")
        return

    try:
        result = refresh_channels(
            limit=args.limit,
            category=args.category,
            country=args.country,
            output_path=out_path,
            verify_live=args.verify_live,
            verify_count=args.verify_count,
            verify_timeout=args.verify_timeout,
            verify_workers=args.verify_workers,
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    print(f"\nSaved {result['selected']:,} channels -> {result['output_path']}")
