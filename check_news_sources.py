#!/usr/bin/env python3
"""World Revolution News 1.7.15 – robuste Quellenprüfung."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import socket
import ssl
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import warnings

import requests
from requests.adapters import HTTPAdapter
from urllib3.exceptions import InsecureRequestWarning
from urllib3.util.retry import Retry


ROOT = Path(__file__).resolve().parent
CATALOG_PATH = ROOT / "source-catalog.json"
OUTPUT_PATH = ROOT / "source-health.json"

USER_AGENT = (
    "Mozilla/5.0 (compatible; WorldRevolutionNews/1.7.15; "
    "+https://blackfront161.github.io/Revolution-News-Data/)"
)

CONNECT_TIMEOUT = 8
READ_TIMEOUT = 15
MAX_BYTES = 131072
MAX_WORKERS = 8

warnings.simplefilter("ignore", InsecureRequestWarning)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def as_sources(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]

    if isinstance(data, dict):
        for key in ("sources", "items", "entries", "results"):
            value = data.get(key)
            if isinstance(value, list):
                return [
                    item for item in value
                    if isinstance(item, dict)
                ]

        rows: list[dict[str, Any]] = []

        for key, value in data.items():
            if isinstance(value, dict):
                rows.append({"name": key, **value})

        return rows

    return []


def source_name(item: dict[str, Any]) -> str:
    return str(
        item.get("name")
        or item.get("sourceName")
        or item.get("source")
        or item.get("quelleName")
        or item.get("title")
        or "Unbekannte Quelle"
    ).strip()


def source_url(item: dict[str, Any]) -> str:
    return str(
        item.get("url")
        or item.get("feedUrl")
        or item.get("feed")
        or item.get("link")
        or ""
    ).strip()


def source_categories(item: dict[str, Any]) -> list[str]:
    raw = item.get("categories", item.get("category", []))

    if isinstance(raw, str):
        values = [raw]
    elif isinstance(raw, list):
        values = raw
    else:
        values = []

    result: list[str] = []

    for value in values:
        clean = str(value or "").strip()

        if clean and clean not in result:
            result.append(clean)

    return result


def canonical_url(value: str) -> str:
    raw = str(value or "").strip()

    if not raw:
        return ""

    try:
        split = urlsplit(raw)
    except ValueError:
        return raw.lower().rstrip("/")

    scheme = split.scheme.lower()
    hostname = (split.hostname or "").lower()

    if hostname.startswith("www."):
        hostname = hostname[4:]

    port = split.port
    netloc = hostname

    if port and not (
        (scheme == "http" and port == 80)
        or (scheme == "https" and port == 443)
    ):
        netloc = f"{hostname}:{port}"

    path = re.sub(r"/+", "/", split.path or "/")

    if path != "/":
        path = path.rstrip("/")

    query = urlencode(sorted(parse_qsl(
        split.query,
        keep_blank_values=True
    )))

    return urlunsplit((
        scheme,
        netloc,
        path,
        query,
        ""
    ))


def merge_catalog(
    rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}

    for item in rows:
        url = source_url(item)
        name = source_name(item)
        key = canonical_url(url) or re.sub(
            r"[^a-z0-9]+",
            "",
            name.lower()
        )

        if not key:
            continue

        if key not in merged:
            merged[key] = {
                "name": name,
                "url": url,
                "categories": source_categories(item)
            }
            continue

        existing = merged[key]

        for category in source_categories(item):
            if category not in existing["categories"]:
                existing["categories"].append(category)

        if len(name) > len(existing["name"]):
            existing["name"] = name

        if not existing["url"] and url:
            existing["url"] = url

    return sorted(
        merged.values(),
        key=lambda item: item["name"].lower()
    )


def make_session() -> requests.Session:
    retry = Retry(
        total=2,
        connect=2,
        read=1,
        backoff_factor=0.6,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=frozenset(["GET"]),
        respect_retry_after_header=True,
    )

    adapter = HTTPAdapter(
        max_retries=retry,
        pool_connections=MAX_WORKERS,
        pool_maxsize=MAX_WORKERS,
    )

    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": (
            "application/rss+xml, application/atom+xml, "
            "application/feed+json, application/xml, text/xml, "
            "application/json, text/html;q=0.8, */*;q=0.5"
        ),
    })
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def read_limited(response: requests.Response) -> bytes:
    chunks: list[bytes] = []
    size = 0

    for chunk in response.iter_content(chunk_size=16384):
        if not chunk:
            continue

        remaining = MAX_BYTES - size

        if remaining <= 0:
            break

        chunks.append(chunk[:remaining])
        size += min(len(chunk), remaining)

        if size >= MAX_BYTES:
            break

    return b"".join(chunks)


def looks_like_feed(
    payload: bytes,
    content_type: str
) -> tuple[bool, str]:
    sample = payload.lstrip()[:MAX_BYTES]
    lower = sample.lower()
    content_type = content_type.lower()

    if not sample:
        return False, "empty_response"

    if (
        b"<rss" in lower
        or b"<feed" in lower
        or b"<rdf:rdf" in lower
        or b"<channel" in lower
    ):
        return True, "xml_feed"

    if (
        "application/feed+json" in content_type
        or (
            "application/json" in content_type
            and (
                b'"items"' in lower
                or b'"version"' in lower
            )
        )
    ):
        return True, "json_feed"

    if "xml" in content_type and sample.startswith(b"<"):
        return True, "xml_document"

    return False, "unexpected_content"


def result_base(
    source: dict[str, Any]
) -> dict[str, Any]:
    return {
        "name": source["name"],
        "url": source["url"],
        "categories": source.get("categories", []),
        "checkedAt": datetime.now(timezone.utc).isoformat(),
        "ok": False,
        "status": "unknown",
        "httpStatus": 0,
        "finalUrl": "",
        "contentType": "",
        "feedType": "",
        "warning": "",
        "error": "",
    }


def request_once(
    session: requests.Session,
    url: str,
    verify: bool
) -> tuple[requests.Response, bytes]:
    response = session.get(
        url,
        timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
        allow_redirects=True,
        stream=True,
        verify=verify,
    )

    return response, read_limited(response)


def classify_http(
    result: dict[str, Any],
    response: requests.Response,
    payload: bytes,
    *,
    insecure_tls: bool = False,
) -> dict[str, Any]:
    result["httpStatus"] = response.status_code
    result["finalUrl"] = response.url
    result["contentType"] = response.headers.get(
        "Content-Type",
        ""
    )

    is_feed, feed_type = looks_like_feed(
        payload,
        result["contentType"]
    )
    result["feedType"] = feed_type

    status = response.status_code

    if status in (401, 403):
        result["status"] = "warning"
        result["warning"] = (
            "Die Quelle blockiert automatisierte Prüfungen "
            f"(HTTP {status})."
        )
        return result

    if status == 429:
        result["status"] = "warning"
        result["warning"] = "Rate-Limit der Quelle (HTTP 429)."
        return result

    if status in (404, 410):
        result["status"] = "error"
        result["error"] = (
            f"Feed dauerhaft nicht gefunden (HTTP {status})."
        )
        return result

    if status >= 500:
        result["status"] = "warning"
        result["warning"] = (
            f"Temporärer Serverfehler (HTTP {status})."
        )
        return result

    if status < 200 or status >= 400:
        result["status"] = "warning"
        result["warning"] = (
            f"Unerwarteter HTTP-Status {status}."
        )
        return result

    if is_feed:
        result["ok"] = not insecure_tls
        result["status"] = (
            "warning" if insecure_tls else "ok"
        )

        if insecure_tls:
            result["warning"] = (
                "Feed erreichbar, aber das TLS-Zertifikat "
                "konnte nicht regulär bestätigt werden."
            )

        return result

    result["status"] = "warning"
    result["warning"] = (
        "Adresse erreichbar, Antwort wurde aber nicht eindeutig "
        "als RSS-, Atom- oder JSON-Feed erkannt."
    )
    return result


def check_source(
    source: dict[str, Any]
) -> dict[str, Any]:
    result = result_base(source)
    url = source.get("url", "").strip()

    if not url:
        result["status"] = "error"
        result["error"] = "Keine Feed-Adresse vorhanden."
        return result

    session = make_session()

    try:
        response, payload = request_once(
            session,
            url,
            verify=True
        )
        return classify_http(result, response, payload)

    except requests.exceptions.SSLError as error:
        try:
            response, payload = request_once(
                session,
                url,
                verify=False
            )

            result = classify_http(
                result,
                response,
                payload,
                insecure_tls=True,
            )

            if result["status"] == "error":
                result["error"] = (
                    "TLS-Fehler und Ersatzabruf "
                    f"fehlgeschlagen: {error}"
                )

            return result

        except requests.RequestException as fallback_error:
            result["status"] = "warning"
            result["warning"] = (
                "TLS-Zertifikat nicht bestätigt; auch der "
                f"Diagnoseabruf scheiterte: {fallback_error}"
            )
            return result

    except requests.exceptions.Timeout as error:
        result["status"] = "warning"
        result["warning"] = f"Zeitüberschreitung: {error}"
        return result

    except requests.exceptions.ConnectionError as error:
        message = str(error)

        if (
            "NameResolutionError" in message
            or "getaddrinfo failed" in message
            or "Name or service not known" in message
        ):
            result["status"] = "error"
            result["error"] = (
                f"DNS-/Domainfehler: {message}"
            )
        else:
            result["status"] = "warning"
            result["warning"] = (
                f"Temporäres Verbindungsproblem: {message}"
            )

        return result

    except requests.RequestException as error:
        result["status"] = "warning"
        result["warning"] = f"Abruffehler: {error}"
        return result

    except (ValueError, ssl.SSLError, socket.error) as error:
        result["status"] = "error"
        result["error"] = f"Ungültige Quelle: {error}"
        return result

    finally:
        session.close()


def main() -> int:
    if not CATALOG_PATH.exists():
        raise SystemExit(
            "source-catalog.json fehlt. "
            "Zuerst build_source_catalog.py ausführen."
        )

    catalog = merge_catalog(
        as_sources(load_json(CATALOG_PATH))
    )

    if not catalog:
        raise SystemExit("Der Quellenkatalog ist leer.")

    results: list[dict[str, Any]] = []

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:
        futures = {
            executor.submit(check_source, source): source
            for source in catalog
        }

        for future in as_completed(futures):
            source = futures[future]

            try:
                result = future.result()
            except Exception as error:
                result = result_base(source)
                result["status"] = "warning"
                result["warning"] = (
                    f"Interner Prüffehler: {error}"
                )

            results.append(result)

            print(
                f"[{result['status'].upper():7}] "
                f"{result['name']}"
            )

    priority = {
        "error": 0,
        "warning": 1,
        "unknown": 2,
        "ok": 3,
    }

    results.sort(key=lambda item: (
        priority.get(item.get("status", "unknown"), 2),
        item.get("name", "").lower(),
    ))

    counts = {
        "total": len(results),
        "ok": sum(
            item["status"] == "ok"
            for item in results
        ),
        "warning": sum(
            item["status"] == "warning"
            for item in results
        ),
        "error": sum(
            item["status"] == "error"
            for item in results
        ),
        "unknown": sum(
            item["status"] == "unknown"
            for item in results
        ),
    }

    payload = {
        "schemaVersion": 2,
        "generatedAt": datetime.now(
            timezone.utc
        ).isoformat(),
        "summary": counts,
        "sources": results,
    }

    temporary = OUTPUT_PATH.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    temporary.replace(OUTPUT_PATH)

    print(json.dumps(counts, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
