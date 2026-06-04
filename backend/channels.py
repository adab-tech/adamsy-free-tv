from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_CHANNELS: list[dict[str, str]] = [
    {
        "name": "Al Jazeera English",
        "url": "https://live-hls-web-aje.getaj.net/AJE/index.m3u8",
        "country": "International",
        "category": "News",
    },
    {
        "name": "DW English",
        "url": "https://dwamdstream102.akamaized.net/hls/live/2015525/dwstream102/index.m3u8",
        "country": "Germany",
        "category": "News",
    },
    {
        "name": "France 24 English",
        "url": "https://stream.france24.com/hls/live/2037163/F24_EN_HI_HLS/master.m3u8",
        "country": "France",
        "category": "News",
    },
    {
        "name": "NASA TV Public",
        "url": "https://ntv1.akamaized.net/hls/live/2014075/NASA-NTV1-HLS/master.m3u8",
        "country": "USA",
        "category": "Education",
    },
]


@dataclass(slots=True)
class Channel:
    name: str
    url: str
    country: str = ""
    category: str = ""


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def bundled_root() -> Path:
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        return Path(bundle_root)
    return Path(__file__).resolve().parent.parent


def default_channels_file() -> Path:
    return project_root() / "tv_channels.json"


def bundled_channels_file() -> Path:
    return bundled_root() / "tv_channels.json"


def channel_to_dict(channel: Channel) -> dict[str, str]:
    return {
        "name": channel.name,
        "url": channel.url,
        "country": channel.country,
        "category": channel.category,
    }


def _coerce_channel(item: dict[str, str]) -> Channel:
    return Channel(
        name=item["name"].strip(),
        url=item["url"].strip(),
        country=item.get("country", "").strip(),
        category=item.get("category", "").strip(),
    )


def load_channels(
    channels_file: Path | None = None,
    fallback_file: Path | None = None,
) -> list[Channel]:
    primary_file = channels_file or default_channels_file()
    bundled_file = fallback_file or bundled_channels_file()
    source_file = primary_file if primary_file.exists() else bundled_file

    if not source_file.exists():
        return [_coerce_channel(item) for item in DEFAULT_CHANNELS]

    try:
        raw_data = json.loads(source_file.read_text(encoding="utf-8"))
        loaded = [_coerce_channel(item) for item in raw_data]
        valid = [channel for channel in loaded if channel.name and channel.url]
        return valid if valid else [_coerce_channel(item) for item in DEFAULT_CHANNELS]
    except (json.JSONDecodeError, KeyError, TypeError):
        return [_coerce_channel(item) for item in DEFAULT_CHANNELS]


def save_channels(channels_file: Path, channels: Sequence[Channel]) -> None:
    payload = [channel_to_dict(channel) for channel in channels]
    channels_file.parent.mkdir(parents=True, exist_ok=True)
    channels_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _channel_matches(
    channel: Channel,
    query: str = "",
    category: str | None = None,
    country: str | None = None,
) -> bool:
    query_text = query.lower().strip()
    category_filter = (category or "").strip().lower()
    country_filter = (country or "").strip().lower()

    if query_text and not (
        query_text in channel.name.lower()
        or query_text in channel.country.lower()
        or query_text in channel.category.lower()
        or query_text in channel.url.lower()
    ):
        return False

    if category_filter and category_filter != "all" and channel.category.lower() != category_filter:
        return False

    if country_filter and country_filter != "all" and channel.country.lower() != country_filter:
        return False

    return True


def filter_channel_indexes(
    channels: Sequence[Channel],
    query: str = "",
    category: str | None = None,
    country: str | None = None,
) -> list[int]:
    return [
        index
        for index, channel in enumerate(channels)
        if _channel_matches(channel, query=query, category=category, country=country)
    ]


def filter_channels(
    channels: Sequence[Channel],
    query: str = "",
    category: str | None = None,
    country: str | None = None,
) -> list[Channel]:
    indexes = filter_channel_indexes(channels, query=query, category=category, country=country)
    return [channels[index] for index in indexes]


def categories_for_channels(channels: Iterable[Channel]) -> list[str]:
    return sorted({channel.category for channel in channels if channel.category})


def countries_for_channels(channels: Iterable[Channel]) -> list[str]:
    return sorted({channel.country for channel in channels if channel.country})
