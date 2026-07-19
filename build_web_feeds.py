#!/usr/bin/env python3
"""Build small browser feeds while retaining the complete news/event archives."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent

NEWS_SOURCE = ROOT / "news.json"
EVENTS_SOURCE = ROOT / "events.json"
NEWS_TARGET = ROOT / "news-feed.json"
EVENTS_TARGET = ROOT / "events-feed.json"
STATUS_TARGET = ROOT / "feed-status.json"
CONFIG_PATH = ROOT / "config.js"

NEWS_LIMIT = max(50, int(os.environ.get("WRN_NEWS_FEED_LIMIT", "500")))
EVENT_LIMIT = max(50, int(os.environ.get("WRN_EVENT_FEED_LIMIT", "500")))
NEWS_CONTENT_LIMIT = max(
    1000,
    int(os.environ.get("WRN_NEWS_CONTENT_LIMIT", "4500"))
)
EVENT_CONTENT_LIMIT = max(
    800,
    int(os.environ.get("WRN_EVENT_CONTENT_LIMIT", "2800"))
)


def load_list(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path.name} muss eine JSON-Liste enthalten.")
    return [item for item in data if isinstance(item, dict)]


def date_value(item: dict[str, Any]) -> float:
    candidates = (
        item.get("eventStart"),
        item.get("pubDate"),
        item.get("date"),
        item.get("published"),
    )

    for raw in candidates:
        value = str(raw or "").strip()
        if not value:
            continue

        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.timestamp()
        except Exception:
            pass

        try:
            parsed = parsedate_to_datetime(value)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.timestamp()
        except Exception:
            pass

    return 0.0


def clean_text(value: Any) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def shorten(value: Any, limit: int) -> tuple[str, bool]:
    text = clean_text(value)
    if len(text) <= limit:
        return text, False

    shortened = text[:limit]
    word_boundary = max(
        shortened.rfind(" "),
        shortened.rfind("\n"),
        shortened.rfind("."),
    )
    if word_boundary >= int(limit * 0.78):
        shortened = shortened[:word_boundary]

    return shortened.rstrip(" \n.,;:") + " …", True


def stable_key(item: dict[str, Any]) -> str:
    return str(
        item.get("link")
        or item.get("eventApiId")
        or item.get("id")
        or item.get("title")
        or ""
    ).strip().casefold()


def prepare(
    rows: list[dict[str, Any]],
    *,
    limit: int,
    content_limit: int,
) -> list[dict[str, Any]]:
    ordered = sorted(rows, key=date_value, reverse=True)
    output: list[dict[str, Any]] = []
    seen: set[str] = set()

    for source in ordered:
        key = stable_key(source)
        if key and key in seen:
            continue
        if key:
            seen.add(key)

        item = dict(source)
        content, truncated = shorten(item.get("content"), content_limit)
        item["content"] = content

        if truncated:
            item["contentComplete"] = False
            item["webFeedTruncated"] = True
            item["webFeedOriginalLength"] = len(
                clean_text(source.get("content"))
            )

        for field in ("title", "author", "quelleName", "eventVenue"):
            if field in item:
                item[field] = clean_text(item.get(field))

        output.append(item)
        if len(output) >= limit:
            break

    return output


def atomic_json(path: Path, data: Any) -> int:
    payload = json.dumps(
        data,
        ensure_ascii=False,
        separators=(",", ":"),
    ) + "\n"

    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(payload, encoding="utf-8")
    temporary.replace(path)
    return len(payload.encode("utf-8"))


def activate_config() -> bool:
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError("config.js wurde nicht gefunden.")

    text = CONFIG_PATH.read_text(encoding="utf-8")
    original = text

    text = re.sub(
        r"news:\s*'https://blackfront161\.github\.io/"
        r"Revolution-News-Data/(?:news|news-feed)\.json'",
        "news: 'https://blackfront161.github.io/"
        "Revolution-News-Data/news-feed.json'",
        text,
        count=1,
    )
    text = re.sub(
        r"events:\s*'https://blackfront161\.github\.io/"
        r"Revolution-News-Data/(?:events|events-feed)\.json'",
        "events: 'https://blackfront161.github.io/"
        "Revolution-News-Data/events-feed.json'",
        text,
        count=1,
    )

    if "version: '1.7.8'" not in text:
        text = re.sub(
            r"version:\s*'[^']+'",
            "version: '1.7.8'",
            text,
            count=1,
        )
        text = re.sub(
            r"build:\s*'[^']+'",
            "build: '2026.07.19-lightweight-web-feed'",
            text,
            count=1,
        )
        text = re.sub(
            r"releasedAt:\s*'[^']+'",
            f"releasedAt: '{datetime.now(timezone.utc).isoformat()}'",
            text,
            count=1,
        )

    if text == original:
        return False

    CONFIG_PATH.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    news = load_list(NEWS_SOURCE)
    events = load_list(EVENTS_SOURCE)

    news_feed = prepare(
        news,
        limit=NEWS_LIMIT,
        content_limit=NEWS_CONTENT_LIMIT,
    )
    event_feed = prepare(
        events,
        limit=EVENT_LIMIT,
        content_limit=EVENT_CONTENT_LIMIT,
    )

    if not news_feed:
        raise SystemExit(
            "Der schnelle News-Feed wäre leer. "
            "Die vorhandenen Dateien werden nicht überschrieben."
        )

    news_bytes = atomic_json(NEWS_TARGET, news_feed)
    event_bytes = atomic_json(EVENTS_TARGET, event_feed)
    config_changed = activate_config()

    status = {
        "ok": True,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "version": "1.7.8",
        "news": {
            "archiveCount": len(news),
            "feedCount": len(news_feed),
            "bytes": news_bytes,
            "contentLimit": NEWS_CONTENT_LIMIT,
        },
        "events": {
            "archiveCount": len(events),
            "feedCount": len(event_feed),
            "bytes": event_bytes,
            "contentLimit": EVENT_CONTENT_LIMIT,
        },
        "configActivated": config_changed,
    }
    atomic_json(STATUS_TARGET, status)

    print(
        f"[WEB-FEED] News: {len(news_feed)}/{len(news)} "
        f"({news_bytes / 1024 / 1024:.2f} MiB)"
    )
    print(
        f"[WEB-FEED] Termine: {len(event_feed)}/{len(events)} "
        f"({event_bytes / 1024 / 1024:.2f} MiB)"
    )
    print(
        "[WEB-FEED] config.js: "
        + ("aktiviert" if config_changed else "bereits aktiv")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
