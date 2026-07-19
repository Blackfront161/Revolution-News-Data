#!/usr/bin/env python3
"""Resolve curated radio stations and validate browser-playable HTTPS streams.

1.7.5 improvements:
- preserves the last known working stream during short outages
- verifies response type and audio magic bytes
- records latency, redirects, candidate results and last success
- distinguishes healthy, degraded, error and unknown
"""
from __future__ import annotations

import json
import re
import socket
import time
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import quote, urlparse

import requests

ROOT = Path(__file__).resolve().parent
SOURCES_FILE = ROOT / "radio-sources.json"
OUTPUT_FILE = ROOT / "radio-stations.json"
HEALTH_FILE = ROOT / "radio-health.json"
USER_AGENT = "WorldRevolutionNews-RadioHealth/1.7.5 (+https://blackfront161.github.io/Revolution-News-Data/)"

session = requests.Session()
session.headers.update({
    "User-Agent": USER_AGENT,
    "Accept": "audio/*, application/ogg, application/octet-stream, */*;q=0.3",
    "Icy-MetaData": "1",
})

FALLBACK_API_SERVERS = [
    "https://de1.api.radio-browser.info",
    "https://de2.api.radio-browser.info",
    "https://nl1.api.radio-browser.info",
]

AUDIO_TYPES = (
    "audio/",
    "application/ogg",
    "application/x-ogg",
    "application/octet-stream",
    "binary/octet-stream",
)
STALE_GRACE = timedelta(days=7)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat()


def unique(values):
    return list(dict.fromkeys(str(value).strip() for value in values if str(value).strip()))


def load_json(path: Path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_name(a), normalize_name(b)).ratio()


def parse_iso(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return None


def radio_browser_servers() -> list[str]:
    servers = []
    try:
        for info in socket.getaddrinfo("all.api.radio-browser.info", 443, type=socket.SOCK_STREAM):
            ip = info[4][0]
            try:
                hostname = socket.gethostbyaddr(ip)[0]
                if hostname:
                    servers.append(f"https://{hostname}")
            except Exception:
                continue
    except Exception:
        pass
    return unique(servers + FALLBACK_API_SERVERS)


def lookup_radio_browser(names: list[str], website: str = "") -> list[str]:
    website_host = (urlparse(website).hostname or "").replace("www.", "")
    candidates: list[str] = []

    for server in radio_browser_servers():
        for name in names:
            try:
                url = (
                    f"{server}/json/stations/byname/{quote(name)}"
                    "?hidebroken=true&limit=20&order=clickcount&reverse=true"
                )
                response = session.get(url, timeout=15)
                response.raise_for_status()
                rows = response.json()
            except Exception:
                continue

            ranked = []
            for row in rows if isinstance(rows, list) else []:
                row_name = str(row.get("name") or "")
                score = similarity(name, row_name)
                homepage_host = (
                    urlparse(str(row.get("homepage") or "")).hostname or ""
                ).replace("www.", "")
                if website_host and homepage_host and (
                    homepage_host == website_host
                    or homepage_host.endswith("." + website_host)
                    or website_host.endswith("." + homepage_host)
                ):
                    score += 0.45
                if score < 0.48:
                    continue

                stream = str(row.get("url_resolved") or row.get("url") or "").strip()
                if stream.startswith("https://"):
                    ranked.append((
                        score,
                        int(row.get("clickcount") or 0),
                        int(row.get("bitrate") or 0),
                        stream,
                    ))

            ranked.sort(reverse=True)
            candidates.extend(stream for _, _, _, stream in ranked[:5])

        if candidates:
            break

    return unique(candidates)


def looks_like_audio(chunk: bytes) -> bool:
    if not chunk:
        return False
    prefix = chunk[:16]
    if prefix.startswith((b"ID3", b"OggS", b"fLaC", b"RIFF")):
        return True
    if len(prefix) >= 2 and prefix[0] == 0xFF and (prefix[1] & 0xE0) == 0xE0:
        return True
    if b"ftypM4A" in chunk[:32] or b"ftypisom" in chunk[:32]:
        return True
    return False


def looks_like_markup(chunk: bytes) -> bool:
    sample = chunk[:256].lstrip().lower()
    return sample.startswith((
        b"<!doctype html",
        b"<html",
        b"<?xml",
        b"{",
        b"[",
    ))


def check_stream(url: str) -> dict:
    started = time.monotonic()
    result = {
        "url": url,
        "ok": False,
        "statusCode": 0,
        "contentType": "",
        "finalUrl": "",
        "latencyMs": 0,
        "message": "",
    }

    if not str(url).startswith("https://"):
        result["message"] = "Kein HTTPS-Stream"
        return result

    try:
        response = session.get(
            url,
            stream=True,
            timeout=(8, 16),
            allow_redirects=True,
            headers={"Range": "bytes=0-4095", "Icy-MetaData": "1"},
        )
        result["statusCode"] = response.status_code
        result["contentType"] = str(response.headers.get("content-type") or "").lower()
        result["finalUrl"] = str(response.url or url)
        result["latencyMs"] = round((time.monotonic() - started) * 1000)

        if not result["finalUrl"].startswith("https://"):
            response.close()
            result["message"] = "Weiterleitung auf unsicheres HTTP"
            return result

        if response.status_code not in {200, 206}:
            response.close()
            result["message"] = f"HTTP {response.status_code}"
            return result

        chunk = b""
        for part in response.iter_content(4096):
            if part:
                chunk += part
                if len(chunk) >= 4096:
                    break
        response.close()

        if not chunk:
            result["message"] = "Stream liefert keine Daten"
            return result

        content_type = result["contentType"]
        type_is_audio = content_type.startswith(AUDIO_TYPES)
        magic_is_audio = looks_like_audio(chunk)

        if "text/html" in content_type or "application/json" in content_type or looks_like_markup(chunk):
            result["message"] = f"Kein Audiostream ({content_type or 'Markup'})"
            return result

        if not type_is_audio and not magic_is_audio:
            result["message"] = f"Audioformat nicht sicher erkennbar ({content_type or 'ohne Typ'})"
            return result

        result["ok"] = True
        result["message"] = "Stream erreichbar"
        return result
    except Exception as exc:
        result["latencyMs"] = round((time.monotonic() - started) * 1000)
        result["message"] = f"{type(exc).__name__}: {exc}"
        return result


def main() -> int:
    sources = load_json(SOURCES_FILE, [])
    if not isinstance(sources, list):
        raise SystemExit("radio-sources.json muss eine Liste enthalten")

    previous_stations = {
        item.get("id"): item
        for item in load_json(OUTPUT_FILE, [])
        if isinstance(item, dict) and item.get("id")
    }
    previous_health = load_json(HEALTH_FILE, {})
    if not isinstance(previous_health, dict):
        previous_health = {}

    stations = []
    health = {}

    for source in sources:
        source_id = source.get("id", source.get("name", "unknown"))
        print(f"[RADIO] {source.get('name')}")

        previous_station = previous_stations.get(source_id, {})
        previous_row = previous_health.get(source_id, {})
        previous_working = (
            previous_row.get("workingStream")
            or previous_station.get("workingStream")
            or ""
        )

        manual = list(source.get("streamCandidates") or [])
        discovered = lookup_radio_browser(
            list(source.get("radioBrowserNames") or [source.get("name", "")]),
            source.get("website", "")
        )
        candidates = unique(([previous_working] if previous_working else []) + manual + discovered)

        working = ""
        checks = []
        for candidate in candidates[:12]:
            check = check_stream(candidate)
            checks.append(check)
            if check["ok"]:
                working = check["finalUrl"] or candidate
                break

        now = utc_now()
        previous_success = parse_iso(
            previous_row.get("lastSuccessAt")
            or previous_station.get("lastSuccess")
            or previous_row.get("checkedAt")
            or ""
        )
        recent_previous = bool(
            previous_working
            and previous_success
            and now - previous_success <= STALE_GRACE
        )

        if working:
            status = "healthy"
            usable_stream = working
            last_success = now.isoformat()
        elif recent_previous:
            status = "degraded"
            usable_stream = previous_working
            last_success = previous_success.isoformat()
        elif candidates:
            status = "error"
            usable_stream = ""
            last_success = previous_success.isoformat() if previous_success else ""
        else:
            status = "unknown"
            usable_stream = ""
            last_success = previous_success.isoformat() if previous_success else ""

        ordered_candidates = unique(([usable_stream] if usable_stream else []) + candidates)

        station = {
            key: value for key, value in source.items()
            if key != "radioBrowserNames"
        }
        station["streamCandidates"] = ordered_candidates
        station["healthStatus"] = status
        station["workingStream"] = usable_stream
        station["lastChecked"] = now.isoformat()
        station["lastSuccess"] = last_success
        stations.append(station)

        failures = [item for item in checks if not item.get("ok")]
        health[source_id] = {
            "name": source.get("name"),
            "status": status,
            "ok": status in {"healthy", "degraded"},
            "workingStream": usable_stream,
            "candidateCount": len(candidates),
            "testedCount": len(checks),
            "checkedAt": now.isoformat(),
            "lastSuccessAt": last_success,
            "latencyMs": next((item["latencyMs"] for item in checks if item.get("ok")), 0),
            "contentType": next((item["contentType"] for item in checks if item.get("ok")), ""),
            "finalUrl": next((item["finalUrl"] for item in checks if item.get("ok")), usable_stream),
            "message": (
                "Stream erreichbar"
                if status == "healthy"
                else "Letzten funktionierenden Stream vorübergehend beibehalten"
                if status == "degraded"
                else failures[-1]["message"]
                if failures
                else "Kein Streamkandidat gefunden"
            ),
            "candidateResults": checks[:8],
        }

    stations.sort(key=lambda item: (
        item.get("region", ""),
        item.get("country", ""),
        item.get("name", "")
    ))
    OUTPUT_FILE.write_text(
        json.dumps(stations, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    HEALTH_FILE.write_text(
        json.dumps(health, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )

    healthy = sum(1 for item in health.values() if item.get("status") == "healthy")
    degraded = sum(1 for item in health.values() if item.get("status") == "degraded")
    broken = sum(1 for item in health.values() if item.get("status") == "error")
    unknown = sum(1 for item in health.values() if item.get("status") == "unknown")
    print(f"[RADIO] healthy={healthy} degraded={degraded} error={broken} unknown={unknown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
