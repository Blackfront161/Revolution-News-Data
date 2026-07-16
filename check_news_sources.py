#!/usr/bin/env python3
"""Prüft die in aggregate.py eingetragenen Nachrichtenquellen parallel.

Die Datei source-health.json enthält nur technische Erreichbarkeitsdaten.
Ein grüner Status ist keine redaktionelle Empfehlung und garantiert nicht,
dass sämtliche Beiträge einer Quelle erfolgreich verarbeitet wurden.
"""
from __future__ import annotations

import ast
import concurrent.futures
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import feedparser
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parent
AGGREGATE_PATH = ROOT / "aggregate.py"
OUTPUT_PATH = ROOT / "source-health.json"

MAX_WORKERS = 12
CONNECT_TIMEOUT = 7
READ_TIMEOUT = 14
MAX_DOWNLOAD_BYTES = 2_500_000

USER_AGENT = (
    "WorldRevolutionNews-SourceHealth/1.0 "
    "(technical feed availability check; contact: worldrevnews@brief.li)"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value or "source"


def load_sources() -> list[dict[str, Any]]:
    """Liest das Literal `quellen = {...}` aus aggregate.py, ohne das Skript auszuführen."""
    tree = ast.parse(AGGREGATE_PATH.read_text(encoding="utf-8"), filename=str(AGGREGATE_PATH))
    source_map: dict[str, Any] | None = None

    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        names: list[str] = []
        value_node = None
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            value_node = node.value
        elif isinstance(node.target, ast.Name):
            names = [node.target.id]
            value_node = node.value

        if "quellen" in names and value_node is not None:
            source_map = ast.literal_eval(value_node)
            break

    if not isinstance(source_map, dict):
        raise RuntimeError("In aggregate.py wurde kein auswertbares `quellen`-Wörterbuch gefunden.")

    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for category, entries in source_map.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            name = str(entry.get("name") or "").strip()
            url = str(entry.get("url") or "").strip()
            if not name or not url:
                continue
            key = (name, url)
            item = merged.setdefault(key, {"name": name, "url": url, "categories": []})
            category_name = str(category).strip()
            if category_name and category_name not in item["categories"]:
                item["categories"].append(category_name)

    return sorted(merged.values(), key=lambda item: (item["name"].casefold(), item["url"]))


def make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=1,
        connect=1,
        read=1,
        status=1,
        backoff_factor=0.35,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=MAX_WORKERS, pool_maxsize=MAX_WORKERS)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*;q=0.2",
    })
    return session


def check_source(source: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    checked_at = utc_now()
    result: dict[str, Any] = {
        "name": source["name"],
        "url": source["url"],
        "categories": source["categories"],
        "host": urlparse(source["url"]).hostname or "",
        "status": "error",
        "ok": False,
        "httpStatus": None,
        "entries": 0,
        "responseMs": 0,
        "lastChecked": checked_at,
        "error": "",
    }

    try:
        with make_session() as session:
            response = session.get(
                source["url"],
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                allow_redirects=True,
                stream=True,
            )
            result["httpStatus"] = response.status_code
            result["finalUrl"] = response.url

            chunks: list[bytes] = []
            size = 0
            for chunk in response.iter_content(chunk_size=65536):
                if not chunk:
                    continue
                remaining = MAX_DOWNLOAD_BYTES - size
                if remaining <= 0:
                    break
                chunks.append(chunk[:remaining])
                size += min(len(chunk), remaining)

            payload = b"".join(chunks)
            parsed = feedparser.parse(payload)
            entry_count = len(parsed.entries or [])
            result["entries"] = entry_count

            content_type = str(response.headers.get("content-type") or "")
            feed_like = bool(entry_count) or bool(getattr(parsed, "feed", None))
            http_ok = 200 <= response.status_code < 400

            if http_ok and feed_like:
                result["ok"] = True
                result["status"] = "ok"
            elif http_ok:
                result["status"] = "warning"
                result["error"] = (
                    "Antwort erreichbar, aber kein verwertbarer RSS-/Atom-Feed erkannt"
                    + (f" ({content_type})" if content_type else "")
                )
            else:
                result["error"] = f"HTTP {response.status_code}"

            bozo_error = getattr(parsed, "bozo_exception", None)
            if bozo_error and not result["error"] and entry_count == 0:
                result["error"] = str(bozo_error)[:240]

    except requests.Timeout:
        result["error"] = "Zeitüberschreitung"
    except requests.RequestException as exc:
        result["error"] = str(exc)[:240]
    except Exception as exc:  # Die übrigen Quellen sollen trotzdem geprüft werden.
        result["error"] = f"{type(exc).__name__}: {exc}"[:240]

    result["responseMs"] = int((time.perf_counter() - started) * 1000)
    return result


def main() -> int:
    sources = load_sources()
    checked: list[dict[str, Any]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_source, source): source for source in sources}
        for future in concurrent.futures.as_completed(futures):
            checked.append(future.result())

    checked.sort(key=lambda item: (item["name"].casefold(), item["url"]))
    output: dict[str, dict[str, Any]] = {}
    used_keys: set[str] = set()

    for item in checked:
        base_key = slugify(item["name"])
        key = base_key
        suffix = 2
        while key in used_keys:
            key = f"{base_key}-{suffix}"
            suffix += 1
        used_keys.add(key)
        output[key] = item

    OUTPUT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    ok_count = sum(1 for item in checked if item["ok"])
    warning_count = sum(1 for item in checked if item["status"] == "warning")
    error_count = len(checked) - ok_count - warning_count
    print(
        f"Quellenprüfung abgeschlossen: {ok_count} OK, "
        f"{warning_count} Warnungen, {error_count} Fehler, {len(checked)} insgesamt."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
