#!/usr/bin/env python3
"""Löst kuratierte Radiosender auf und prüft deren HTTPS-Streams."""
from __future__ import annotations

import json
import re
import socket
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import quote, urlparse

import requests

ROOT = Path(__file__).resolve().parent
SOURCES_FILE = ROOT / "radio-sources.json"
OUTPUT_FILE = ROOT / "radio-stations.json"
HEALTH_FILE = ROOT / "radio-health.json"
USER_AGENT = "WorldRevolutionNews-RadioHealth/1.7.1 (+https://blackfront161.github.io/Revolution-News-Data/)"

session = requests.Session()
session.headers.update({
    "User-Agent": USER_AGENT,
    "Accept": "application/json, audio/*, */*;q=0.4",
    "Icy-MetaData": "1",
})

FALLBACK_API_SERVERS = [
    "https://de1.api.radio-browser.info",
    "https://de2.api.radio-browser.info",
    "https://nl1.api.radio-browser.info",
]


def unique(values):
    return list(dict.fromkeys(value for value in values if value))


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_name(a), normalize_name(b)).ratio()


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
    candidates = []

    for server in radio_browser_servers():
        for name in names:
            try:
                url = f"{server}/json/stations/byname/{quote(name)}?hidebroken=true&limit=15&order=clickcount&reverse=true"
                response = session.get(url, timeout=15)
                response.raise_for_status()
                rows = response.json()
            except Exception:
                continue

            ranked = []
            for row in rows if isinstance(rows, list) else []:
                row_name = str(row.get("name") or "")
                score = similarity(name, row_name)
                homepage_host = (urlparse(str(row.get("homepage") or "")).hostname or "").replace("www.", "")
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
                    ranked.append((score, int(row.get("clickcount") or 0), stream))

            ranked.sort(reverse=True)
            candidates.extend(stream for _, _, stream in ranked[:4])

        if candidates:
            break

    return unique(candidates)


def check_stream(url: str) -> tuple[bool, str]:
    if not str(url).startswith("https://"):
        return False, "Kein HTTPS-Stream"

    try:
        response = session.get(
            url,
            stream=True,
            timeout=(8, 14),
            allow_redirects=True,
            headers={"Range": "bytes=0-2047", "Icy-MetaData": "1"},
        )
        status = response.status_code
        content_type = str(response.headers.get("content-type") or "").lower()
        final_url = response.url

        if status not in {200, 206}:
            response.close()
            return False, f"HTTP {status}"

        if "text/html" in content_type or "application/json" in content_type:
            response.close()
            return False, f"Kein Audiostream ({content_type or 'unbekannter Typ'})"

        chunk = next(response.iter_content(1024), b"")
        response.close()
        if not chunk:
            return False, "Stream liefert keine Daten"

        return True, final_url
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def main() -> int:
    sources = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    stations = []
    health = {}

    for source in sources:
        source_id = source.get("id", source.get("name", "unknown"))
        print(f"[RADIO] {source.get('name')}")
        manual = list(source.get("streamCandidates") or [])
        discovered = lookup_radio_browser(
            list(source.get("radioBrowserNames") or [source.get("name", "")]),
            source.get("website", "")
        )
        candidates = unique(manual + discovered)
        working = ""
        errors = []

        for candidate in candidates[:10]:
            ok, result = check_stream(candidate)
            if ok:
                working = result
                break
            errors.append(f"{candidate}: {result}")

        status = "healthy" if working else ("unknown" if not candidates else "error")
        ordered_candidates = unique(([working] if working else []) + candidates)

        station = {
            key: value for key, value in source.items()
            if key != "radioBrowserNames"
        }
        station["streamCandidates"] = ordered_candidates
        station["healthStatus"] = status
        station["workingStream"] = working
        station["lastChecked"] = datetime.now(timezone.utc).isoformat()
        stations.append(station)

        health[source_id] = {
            "name": source.get("name"),
            "status": status,
            "ok": status == "healthy",
            "workingStream": working,
            "candidateCount": len(candidates),
            "checkedAt": station["lastChecked"],
            "message": "Stream erreichbar" if working else ("; ".join(errors[-4:]) or "Kein Streamkandidat gefunden"),
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
