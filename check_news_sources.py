#!/usr/bin/env python3
"""World Revolution News 1.7.16 – Quellenprüfung mit Feed-Erkennung."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import socket
import ssl
from typing import Any
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
import warnings

import requests
from requests.adapters import HTTPAdapter
from urllib3.exceptions import InsecureRequestWarning
from urllib3.util.retry import Retry


ROOT = Path(__file__).resolve().parent
CATALOG_PATH = ROOT / "source-catalog.json"
OUTPUT_PATH = ROOT / "source-health.json"
DISCOVERED_PATH = ROOT / "discovered-feeds.json"

USER_AGENT = (
    "Mozilla/5.0 (compatible; WorldRevolutionNews/1.7.16; "
    "+https://blackfront161.github.io/Revolution-News-Data/)"
)

CONNECT_TIMEOUT = 8
READ_TIMEOUT = 15
MAX_BYTES = 196608
MAX_WORKERS = 8

warnings.simplefilter("ignore", InsecureRequestWarning)


class FeedLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag.lower() != "link":
            return

        data = {
            str(key).lower(): str(value or "")
            for key, value in attrs
        }

        rel = data.get("rel", "").lower()
        content_type = data.get("type", "").lower()
        href = data.get("href", "").strip()

        if not href or "alternate" not in rel:
            return

        if any(token in content_type for token in (
            "rss",
            "atom",
            "feed+json",
            "application/xml",
            "text/xml",
        )):
            self.links.append(href)


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

        return [
            {"name": key, **value}
            for key, value in data.items()
            if isinstance(value, dict)
        ]

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


def explicit_feed_url(item: dict[str, Any]) -> str:
    return str(
        item.get("feedUrl")
        or item.get("feed")
        or item.get("rss")
        or item.get("atom")
        or ""
    ).strip()


def source_page_url(item: dict[str, Any]) -> str:
    return str(
        item.get("homepage")
        or item.get("website")
        or item.get("siteUrl")
        or item.get("sourceUrl")
        or item.get("url")
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
        name = source_name(item)
        feed_url = explicit_feed_url(item)
        page_url = source_page_url(item)

        key = (
            canonical_url(feed_url)
            or canonical_url(page_url)
            or re.sub(r"[^a-z0-9]+", "", name.lower())
        )

        if not key:
            continue

        candidate = {
            "name": name,
            "feedUrl": feed_url,
            "pageUrl": page_url,
            "categories": source_categories(item),
        }

        if key not in merged:
            merged[key] = candidate
            continue

        existing = merged[key]

        for category in candidate["categories"]:
            if category not in existing["categories"]:
                existing["categories"].append(category)

        if not existing["feedUrl"] and candidate["feedUrl"]:
            existing["feedUrl"] = candidate["feedUrl"]

        if not existing["pageUrl"] and candidate["pageUrl"]:
            existing["pageUrl"] = candidate["pageUrl"]

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
            "application/json, text/html;q=0.9, */*;q=0.5"
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

    return False, "unexpected_content"


def result_base(
    source: dict[str, Any]
) -> dict[str, Any]:
    return {
        "name": source["name"],
        "url": source.get("feedUrl", ""),
        "pageUrl": source.get("pageUrl", ""),
        "categories": source.get("categories", []),
        "checkedAt": datetime.now(timezone.utc).isoformat(),
        "ok": False,
        "status": "unknown",
        "httpStatus": 0,
        "finalUrl": "",
        "contentType": "",
        "feedType": "",
        "discovered": False,
        "warning": "",
        "error": "",
    }


def request_once(
    session: requests.Session,
    url: str,
    *,
    verify: bool = True
) -> tuple[requests.Response, bytes]:
    response = session.get(
        url,
        timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
        allow_redirects=True,
        stream=True,
        verify=verify,
    )

    return response, read_limited(response)


def discover_feed(
    session: requests.Session,
    page_url: str
) -> str:
    if not page_url:
        return ""

    try:
        response, payload = request_once(
            session,
            page_url,
            verify=True
        )
    except requests.exceptions.SSLError:
        try:
            response, payload = request_once(
                session,
                page_url,
                verify=False
            )
        except requests.RequestException:
            return ""
    except requests.RequestException:
        return ""

    content_type = response.headers.get(
        "Content-Type",
        ""
    ).lower()

    is_feed, _ = looks_like_feed(payload, content_type)

    if is_feed:
        return response.url

    if "html" not in content_type and b"<html" not in payload.lower():
        return ""

    parser = FeedLinkParser()

    try:
        parser.feed(
            payload.decode(
                response.encoding or "utf-8",
                errors="replace"
            )
        )
    except Exception:
        return ""

    for href in parser.links:
        candidate = urljoin(response.url, href)

        if candidate:
            return candidate

    return ""


def classify_response(
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
            "Quelle blockiert automatisierte Prüfungen "
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
                "Feed erreichbar, TLS-Zertifikat konnte "
                "aber nicht regulär bestätigt werden."
            )

        return result

    result["status"] = "warning"
    result["warning"] = (
        "Adresse erreichbar, aber nicht eindeutig als Feed erkannt."
    )
    return result


def check_feed_url(
    session: requests.Session,
    result: dict[str, Any],
    feed_url: str,
) -> dict[str, Any]:
    result["url"] = feed_url

    try:
        response, payload = request_once(
            session,
            feed_url,
            verify=True
        )
        return classify_response(result, response, payload)

    except requests.exceptions.SSLError:
        try:
            response, payload = request_once(
                session,
                feed_url,
                verify=False
            )
            return classify_response(
                result,
                response,
                payload,
                insecure_tls=True,
            )
        except requests.RequestException as error:
            result["status"] = "warning"
            result["warning"] = (
                "TLS-Problem und Diagnoseabruf fehlgeschlagen: "
                f"{error}"
            )
            return result

    except requests.exceptions.Timeout as error:
        result["status"] = "warning"
        result["warning"] = f"Zeitüberschreitung: {error}"
        return result

    except requests.exceptions.ConnectionError as error:
        message = str(error)

        if any(token in message for token in (
            "NameResolutionError",
            "getaddrinfo failed",
            "Name or service not known",
        )):
            result["status"] = "error"
            result["error"] = f"DNS-/Domainfehler: {message}"
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


def check_source(
    source: dict[str, Any]
) -> dict[str, Any]:
    result = result_base(source)
    session = make_session()

    try:
        feed_url = source.get("feedUrl", "").strip()

        if not feed_url:
            feed_url = discover_feed(
                session,
                source.get("pageUrl", "").strip()
            )

            if feed_url:
                result["discovered"] = True
                result["warning"] = (
                    "Feed-Adresse automatisch auf der Quellenseite erkannt."
                )

        if not feed_url:
            result["status"] = "unknown"
            result["warning"] = (
                "Keine technische Feed-Adresse vorhanden; "
                "Quelle wurde nicht als defekt gewertet."
            )
            return result

        checked = check_feed_url(
            session,
            result,
            feed_url
        )

        if result["discovered"] and checked["status"] == "ok":
            checked["warning"] = (
                "Feed-Adresse automatisch erkannt."
            )

        return checked

    finally:
        session.close()


def main() -> int:
    if not CATALOG_PATH.exists():
        raise SystemExit("source-catalog.json fehlt.")

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

    summary = {
        "total": len(results),
        "ok": sum(item["status"] == "ok" for item in results),
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
        "discovered": sum(
            bool(item.get("discovered"))
            for item in results
        ),
    }

    payload = {
        "schemaVersion": 3,
        "generatedAt": datetime.now(
            timezone.utc
        ).isoformat(),
        "summary": summary,
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

    discovered = {
        item["name"]: item["url"]
        for item in results
        if item.get("discovered") and item.get("url")
    }

    DISCOVERED_PATH.write_text(
        json.dumps(
            discovered,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
