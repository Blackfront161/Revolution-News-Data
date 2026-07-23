#!/usr/bin/env python3
"""Aggregiert kuratierte Original-Podcast-Feeds.

Es werden ausschließlich Metadaten und Original-URLs gespeichert.
Audiodateien werden weder kopiert noch neu veröffentlicht.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
SOURCES_FILE = ROOT / "podcast-sources.json"
OUTPUT_FILE = ROOT / "podcasts.json"
HEALTH_FILE = ROOT / "podcast-health.json"

MAX_PER_SOURCE = 35
MAX_TOTAL = 800
DEFAULT_MAX_AGE_DAYS = 730
USER_AGENT = "WorldRevolutionNews-AudioCatalog/1.7.5 (+https://blackfront161.github.io/Revolution-News-Data/)"
AUDIO_EXTENSIONS = (".mp3", ".m4a", ".ogg", ".oga", ".opus", ".wav", ".aac", ".flac")
HTTPS_UPGRADE_HOSTS = {"www.freie-radios.net", "freie-radios.net"}

session = requests.Session()
session.headers.update({
    "User-Agent": USER_AGENT,
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, text/html;q=0.8, */*;q=0.5",
})


def clean_text(value: object) -> str:
    if not value:
        return ""
    soup = BeautifulSoup(str(value), "html.parser")
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()


def safe_url(value: object, base: str = "") -> str:
    if not value:
        return ""
    url = urljoin(base, str(value).strip())
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return ""
    if parsed.scheme == "http" and (parsed.hostname or "").lower() in HTTPS_UPGRADE_HOSTS:
        url = "https://" + url.split("://", 1)[1]
    return url


def parse_date(entry) -> str:
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        value = entry.get(key)
        if value:
            return datetime(*value[:6], tzinfo=timezone.utc).isoformat()
    for key in ("published", "updated", "pubDate"):
        value = entry.get(key)
        if not value:
            continue
        try:
            dt = parsedate_to_datetime(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except Exception:
            continue
    return ""


def audio_from_entry(entry) -> str:
    candidates: list[str] = []
    for enc in entry.get("enclosures", []) or []:
        href = enc.get("href") or enc.get("url")
        typ = str(enc.get("type") or "").lower()
        if href and (typ.startswith("audio/") or str(href).lower().split("?")[0].endswith(AUDIO_EXTENSIONS)):
            candidates.append(href)

    for link in entry.get("links", []) or []:
        href = link.get("href")
        typ = str(link.get("type") or "").lower()
        rel = str(link.get("rel") or "").lower()
        if href and (rel == "enclosure" or typ.startswith("audio/")):
            candidates.append(href)

    for item in entry.get("media_content", []) or []:
        href = item.get("url")
        typ = str(item.get("type") or "").lower()
        if href and (typ.startswith("audio/") or str(href).lower().split("?")[0].endswith(AUDIO_EXTENSIONS)):
            candidates.append(href)

    html_parts = []
    for key in ("summary", "description"):
        if entry.get(key):
            html_parts.append(str(entry.get(key)))
    for part in entry.get("content", []) or []:
        if part.get("value"):
            html_parts.append(str(part.get("value")))

    for html in html_parts:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all(["audio", "source", "a"]):
            href = tag.get("src") or tag.get("href")
            if href and str(href).lower().split("?")[0].endswith(AUDIO_EXTENSIONS):
                candidates.append(href)

    for candidate in candidates:
        url = safe_url(candidate, entry.get("link") or "")
        if url:
            return url
    return ""


def discover_feeds(homepage: str) -> list[str]:
    if not homepage:
        return []
    try:
        response = session.get(homepage, timeout=22)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        found = []
        for link in soup.find_all("link", rel=lambda x: x and "alternate" in x):
            typ = str(link.get("type") or "").lower()
            href = link.get("href")
            if href and ("rss" in typ or "atom" in typ or "xml" in typ):
                found.append(urljoin(response.url, href))
        return list(dict.fromkeys(found))
    except Exception:
        return []


def find_audio_on_page(url: str) -> str:
    if not url:
        return ""
    try:
        response = session.get(url, timeout=25)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup.find_all(["audio", "source", "a"]):
            href = tag.get("src") or tag.get("href")
            if not href:
                continue
            absolute = safe_url(href, response.url)
            path = urlparse(absolute).path.lower()
            typ = str(tag.get("type") or "").lower()
            if absolute and (path.endswith(AUDIO_EXTENSIONS) or typ.startswith("audio/")):
                return absolute
    except Exception:
        return ""
    return ""


def source_entries(source: dict) -> tuple[list[dict], str, list[str]]:
    candidates = list(source.get("feedUrls") or [])
    candidates += discover_feeds(source.get("homepage", ""))
    errors: list[str] = []

    for feed_url in dict.fromkeys(candidates):
        try:
            response = session.get(feed_url, timeout=32)
            response.raise_for_status()
            parsed = feedparser.parse(response.content)

            if not parsed.entries:
                errors.append(f"{feed_url}: keine Einträge")
                continue

            result = []
            for entry in parsed.entries[:MAX_PER_SOURCE * 3]:
                audio = audio_from_entry(entry)
                episode_url = safe_url(entry.get("link") or entry.get("id") or "", feed_url)

                if not audio and source.get("pageAudioFallback") and episode_url:
                    audio = find_audio_on_page(episode_url)
                    time.sleep(0.12)

                if not audio:
                    continue

                title = clean_text(entry.get("title")) or source.get("name", "Podcast")
                description = clean_text(
                    entry.get("summary")
                    or entry.get("description")
                    or (entry.get("content") or [{}])[0].get("value")
                )
                published = parse_date(entry)
                duration = clean_text(entry.get("itunes_duration") or entry.get("duration"))
                image = ""

                for img in entry.get("media_thumbnail", []) or []:
                    image = safe_url(img.get("url"))
                    if image:
                        break

                if not image:
                    image = safe_url(
                        entry.get("image", {}).get("href")
                        if isinstance(entry.get("image"), dict)
                        else ""
                    )

                guid_seed = str(entry.get("id") or entry.get("guid") or audio)
                result.append({
                    "id": hashlib.sha256(f"{source.get('id')}|{guid_seed}".encode()).hexdigest()[:24],
                    "type": "original-podcast",
                    "sourceId": source.get("id", ""),
                    "sourceName": source.get("name", ""),
                    "sourceKind": source.get("sourceKind", "independent-podcast"),
                    "sourcePriority": int(source.get("priority", 50)),
                    "title": title,
                    "description": description[:4000],
                    "published": published,
                    "duration": duration,
                    "language": source.get("language", ""),
                    "country": source.get("country", ""),
                    "region": source.get("region", ""),
                    "audioUrl": audio,
                    "episodeUrl": episode_url or source.get("homepage", ""),
                    "feedUrl": feed_url,
                    "artwork": image,
                    "topics": source.get("topics", []),
                    "categories": source.get("categories", []),
                    "license": source.get("license", "Originalquelle"),
                })

                if len(result) >= MAX_PER_SOURCE:
                    break

            if result:
                return result, feed_url, errors

            errors.append(f"{feed_url}: Einträge ohne direkt abspielbare Audiodatei")
        except Exception as exc:
            errors.append(f"{feed_url}: {type(exc).__name__}: {exc}")

    return [], "", errors[-6:]


def parse_iso(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def main() -> int:
    sources = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    catalog_source_ids = {
        source.get("id")
        for source in sources
        if source.get("id")
    }
    requested_ids = {
        value.strip()
        for value in os.environ.get("WRN_PODCAST_SOURCE_IDS", "").split(",")
        if value.strip()
    }
    if requested_ids:
        sources = [
            source for source in sources
            if source.get("id") in requested_ids
        ]
        missing = requested_ids - {
            source.get("id") for source in sources
        }
        if missing:
            raise SystemExit(
                "Unbekannte Podcast-Quellen: "
                + ", ".join(sorted(missing))
            )
    all_items: list[dict] = []
    health: dict[str, dict] = {}
    if requested_ids and HEALTH_FILE.exists():
        try:
            existing_health = json.loads(
                HEALTH_FILE.read_text(encoding="utf-8")
            )
            if isinstance(existing_health, dict):
                health.update({
                    key: value
                    for key, value in existing_health.items()
                    if key in catalog_source_ids
                })
        except Exception:
            pass

    for source in sources:
        source_id = source.get("id", source.get("name", "unknown"))
        if source.get("enabled", True) is False:
            health[source_id] = {
                "name": source.get("name"),
                "status": "disabled",
                "ok": False,
                "episodes": 0,
                "feedOrError": source.get("disabledReason", "deaktiviert"),
                "checkedAt": datetime.now(timezone.utc).isoformat(),
            }
            continue

        print(f"[PODCAST] {source.get('name')}")
        items, used_feed, errors = source_entries(source)
        max_age = int(source.get("maxAgeDays", DEFAULT_MAX_AGE_DAYS))
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age)
        fresh: list[dict] = []
        stale: list[dict] = []

        for item in items:
            published = parse_iso(item.get("published", ""))
            if published and published < cutoff:
                stale.append(item)
            else:
                fresh.append(item)

        selected = fresh or stale[: min(10, MAX_PER_SOURCE)]
        all_items.extend(selected)

        latest = max(
            (item.get("published", "") for item in items if item.get("published")),
            default=""
        )

        if fresh:
            status = "healthy"
        elif stale:
            status = "stale"
        else:
            status = "error"

        health[source_id] = {
            "name": source.get("name"),
            "status": status,
            "ok": status in {"healthy", "stale"},
            "episodes": len(selected),
            "freshEpisodes": len(fresh),
            "latestPublished": latest,
            "feedOrError": used_feed or "; ".join(errors),
            "checkedAt": datetime.now(timezone.utc).isoformat(),
            "region": source.get("region", ""),
            "language": source.get("language", ""),
        }

    # Doppelte Audiodateien: die spezifischere Quelle gewinnt vor Aggregatoren.
    unique: dict[str, dict] = {}
    for item in all_items:
        key = item.get("audioUrl")
        if not key:
            continue
        existing = unique.get(key)
        if not existing or int(item.get("sourcePriority", 0)) > int(existing.get("sourcePriority", 0)):
            unique[key] = item

    items = list(unique.values())
    items.sort(key=lambda x: x.get("published") or "", reverse=True)

    previous_items = []
    if OUTPUT_FILE.exists():
        try:
            loaded = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                previous_items = [
                    item for item in loaded
                    if isinstance(item, dict) and item.get("audioUrl")
                ]
        except Exception as exc:
            print(f"[PODCAST] bisherige Datei konnte nicht gelesen werden: {exc}")

    if requested_ids and previous_items:
        retained = [
            item for item in previous_items
            if item.get("sourceId") not in requested_ids
        ]
        targeted = {
            item.get("audioUrl"): item
            for item in items
            if item.get("audioUrl")
        }
        for item in retained:
            targeted.setdefault(item.get("audioUrl"), item)
        items = sorted(
            targeted.values(),
            key=lambda item: item.get("published") or "",
            reverse=True,
        )

    if items:
        output_items = items[:MAX_TOTAL]
        OUTPUT_FILE.write_text(
            json.dumps(output_items, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8"
        )
        print(f"[PODCAST] {len(output_items)} Folgen gespeichert")
    elif previous_items:
        print(f"[PODCAST] keine neuen Folgen; {len(previous_items)} vorhandene Folgen bleiben erhalten")
    else:
        OUTPUT_FILE.write_text("[]\n", encoding="utf-8")
        print("[PODCAST] keine abspielbaren Folgen vorhanden")

    HEALTH_FILE.write_text(
        json.dumps(health, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
