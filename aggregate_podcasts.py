#!/usr/bin/env python3
"""Aggregates original podcast feeds without copying audio files.

The generated podcasts.json only stores metadata and original audio URLs.
"""
from __future__ import annotations
import hashlib, json, os, re, sys, time
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
MAX_PER_SOURCE = 30
MAX_TOTAL = 500
MAX_AGE_DAYS = 730
USER_AGENT = "WorldRevolutionNews-PodcastAggregator/1.0 (+https://blackfront161.github.io/Revolution-News-Data/)"
AUDIO_EXTENSIONS = (".mp3", ".m4a", ".ogg", ".oga", ".opus", ".wav", ".aac")

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, text/html;q=0.8, */*;q=0.5"})


def clean_text(value: object) -> str:
    if not value: return ""
    soup = BeautifulSoup(str(value), "html.parser")
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()


HTTPS_UPGRADE_HOSTS = {"www.freie-radios.net", "freie-radios.net"}

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
        if value:
            try:
                dt = parsedate_to_datetime(value)
                if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc).isoformat()
            except Exception: pass
    return ""


def audio_from_entry(entry) -> str:
    candidates = []
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
        if entry.get(key): html_parts.append(str(entry.get(key)))
    for part in entry.get("content", []) or []:
        if part.get("value"): html_parts.append(str(part.get("value")))
    for html in html_parts:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all(["audio", "source", "a"]):
            href = tag.get("src") or tag.get("href")
            if href and str(href).lower().split("?")[0].endswith(AUDIO_EXTENSIONS): candidates.append(href)
    for candidate in candidates:
        url = safe_url(candidate, entry.get("link") or "")
        if url: return url
    return ""


def discover_feeds(homepage: str) -> list[str]:
    if not homepage: return []
    try:
        response = session.get(homepage, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        found = []
        for link in soup.find_all("link", rel=lambda x: x and "alternate" in x):
            typ = str(link.get("type") or "").lower()
            href = link.get("href")
            if href and ("rss" in typ or "atom" in typ or "xml" in typ): found.append(urljoin(response.url, href))
        return list(dict.fromkeys(found))
    except Exception:
        return []


def find_audio_on_page(url: str) -> str:
    if not url: return ""
    try:
        response = session.get(url, timeout=25)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup.find_all(["audio", "source", "a"]):
            href = tag.get("src") or tag.get("href")
            if not href: continue
            absolute = safe_url(href, response.url)
            path = urlparse(absolute).path.lower()
            typ = str(tag.get("type") or "").lower()
            if absolute and (path.endswith(AUDIO_EXTENSIONS) or typ.startswith("audio/")):
                return absolute
    except Exception:
        return ""
    return ""


def source_entries(source: dict) -> tuple[list[dict], str]:
    candidates = list(source.get("feedUrls") or [])
    candidates += discover_feeds(source.get("homepage", ""))
    errors = []
    for feed_url in dict.fromkeys(candidates):
        try:
            response = session.get(feed_url, timeout=30)
            response.raise_for_status()
            parsed = feedparser.parse(response.content)
            if not parsed.entries:
                errors.append(f"{feed_url}: no entries")
                continue
            result = []
            for entry in parsed.entries[:MAX_PER_SOURCE * 2]:
                audio = audio_from_entry(entry)
                episode_url = safe_url(entry.get("link") or entry.get("id") or "", feed_url)
                if not audio and source.get("pageAudioFallback") and episode_url:
                    audio = find_audio_on_page(episode_url)
                    time.sleep(0.15)
                if not audio: continue
                title = clean_text(entry.get("title")) or source.get("name", "Podcast")
                description = clean_text(entry.get("summary") or entry.get("description") or (entry.get("content") or [{}])[0].get("value"))
                published = parse_date(entry)
                duration = clean_text(entry.get("itunes_duration") or entry.get("duration"))
                image = ""
                for img in entry.get("media_thumbnail", []) or []:
                    image = safe_url(img.get("url"));
                    if image: break
                guid_seed = str(entry.get("id") or entry.get("guid") or audio)
                result.append({
                    "id": hashlib.sha256(f"{source.get('id')}|{guid_seed}".encode()).hexdigest()[:24],
                    "type": "original-podcast",
                    "sourceId": source.get("id", ""), "sourceName": source.get("name", ""),
                    "title": title, "description": description[:4000], "published": published,
                    "duration": duration, "language": source.get("language", ""),
                    "audioUrl": audio, "episodeUrl": episode_url or source.get("homepage", ""),
                    "feedUrl": feed_url, "artwork": image, "categories": source.get("categories", []),
                    "license": source.get("license", "Originalquelle")
                })
                if len(result) >= MAX_PER_SOURCE: break
            if result: return result, feed_url
            errors.append(f"{feed_url}: entries without playable audio")
        except Exception as exc:
            errors.append(f"{feed_url}: {type(exc).__name__}: {exc}")
    return [], "; ".join(errors[-4:])


def main() -> int:
    sources = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    all_items, health = [], {}
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    for source in sources:
        if source.get("enabled", True) is False: continue
        print(f"[PODCAST] {source.get('name')}")
        items, used = source_entries(source)
        fresh = []
        for item in items:
            if item.get("published"):
                try:
                    if datetime.fromisoformat(item["published"].replace("Z", "+00:00")) < cutoff: continue
                except Exception: pass
            fresh.append(item)
        all_items.extend(fresh)
        health[source.get("id", source.get("name", "unknown"))] = {
            "name": source.get("name"), "ok": bool(fresh), "episodes": len(fresh),
            "feedOrError": used, "checkedAt": datetime.now(timezone.utc).isoformat()
        }
    unique = {}
    for item in all_items:
        unique[item["audioUrl"]] = item
    items = list(unique.values())
    items.sort(key=lambda x: x.get("published") or "", reverse=True)

    previous_items = []
    if OUTPUT_FILE.exists():
        try:
            loaded = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                previous_items = [item for item in loaded if isinstance(item, dict) and item.get("audioUrl")]
        except Exception as exc:
            print(f"[PODCAST] previous output could not be read: {exc}")

    if items:
        output_items = items[:MAX_TOTAL]
        OUTPUT_FILE.write_text(json.dumps(output_items, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[PODCAST] saved {len(output_items)} episodes")
    elif previous_items:
        # A temporary outage of all feeds must not erase a previously working library.
        print(f"[PODCAST] no fresh episodes; preserving {len(previous_items)} existing episodes")
    else:
        OUTPUT_FILE.write_text("[]\n", encoding="utf-8")
        print("[PODCAST] no playable episodes and no previous library")

    HEALTH_FILE.write_text(json.dumps(health, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
