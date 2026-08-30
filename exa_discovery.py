#!/usr/bin/env python3
"""WRN Exa discovery prototype.

Uses Exa as a low-volume supplementary discovery layer. It never mutates
news.json or the source registry. Results are written to exa-discovery.json
for review or later ingestion.

Environment:
    EXA_API_KEY  Required for live searches.

The defaults are intentionally conservative so the Exa free tier is enough
for regular experiments.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests

EXA_SEARCH_URL = "https://api.exa.ai/search"
DEFAULT_QUERY_FILE = Path("exa-queries.json")
DEFAULT_OUTPUT_FILE = Path("exa-discovery.json")
DEFAULT_NEWS_FILE = Path("news.json")
REQUEST_TIMEOUT_SECONDS = 25
DEFAULT_MAX_RESULTS = 8
DEFAULT_LOOKBACK_HOURS = 72

TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "source",
    "utm_campaign",
    "utm_content",
    "utm_medium",
    "utm_source",
    "utm_term",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path, fallback: Any) -> Any:
    if not path.is_file():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def canonical_url(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        parsed = urlsplit(raw)
    except ValueError:
        return raw.lower().rstrip("/")

    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]

    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")

    clean_query = [
        (key, val)
        for key, val in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in TRACKING_QUERY_KEYS
    ]

    return urlunsplit(
        (
            (parsed.scheme or "https").lower(),
            host,
            path,
            urlencode(clean_query, doseq=True),
            "",
        )
    )


def existing_article_urls(news_path: Path) -> set[str]:
    payload = read_json(news_path, [])
    if isinstance(payload, dict):
        for key in ("articles", "items", "news"):
            if isinstance(payload.get(key), list):
                payload = payload[key]
                break
    if not isinstance(payload, list):
        return set()

    urls: set[str] = set()
    for item in payload:
        if not isinstance(item, dict):
            continue
        for key in ("url", "link", "sourceUrl", "originalUrl"):
            value = canonical_url(item.get(key))
            if value:
                urls.add(value)
    return urls


def load_queries(path: Path) -> list[dict[str, Any]]:
    payload = read_json(path, [])
    if isinstance(payload, dict):
        payload = payload.get("queries", [])
    if not isinstance(payload, list):
        raise SystemExit(f"Ungültige Query-Datei: {path}")

    queries: list[dict[str, Any]] = []
    for index, item in enumerate(payload, start=1):
        if isinstance(item, str):
            item = {"id": f"query-{index}", "query": item}
        if not isinstance(item, dict):
            continue
        query = str(item.get("query") or "").strip()
        if not query:
            continue
        queries.append(
            {
                "id": str(item.get("id") or f"query-{index}").strip(),
                "query": query,
                "category": str(item.get("category") or "news").strip() or "news",
                "enabled": item.get("enabled", True) is not False,
            }
        )
    return [item for item in queries if item["enabled"]]


def request_exa(
    session: requests.Session,
    api_key: str,
    query: dict[str, Any],
    *,
    max_results: int,
    lookback_hours: int,
    now: datetime,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "query": query["query"],
        "type": "auto",
        "numResults": max(1, min(int(max_results), 10)),
        "contents": {"highlights": {"maxCharacters": 1200}},
    }

    category = str(query.get("category") or "").strip()
    if category:
        body["category"] = category

    if category == "news" and lookback_hours > 0:
        body["startPublishedDate"] = iso(now - timedelta(hours=lookback_hours))

    response = session.post(
        EXA_SEARCH_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("Exa lieferte keine JSON-Antwort.")
    return payload


def normalized_results(
    payload: dict[str, Any],
    query_id: str,
    existing_urls: set[str],
) -> tuple[list[dict[str, Any]], int]:
    accepted: list[dict[str, Any]] = []
    skipped_existing = 0

    for rank, raw in enumerate(payload.get("results") or [], start=1):
        if not isinstance(raw, dict):
            continue
        url = str(raw.get("url") or "").strip()
        canonical = canonical_url(url)
        if not canonical:
            continue
        if canonical in existing_urls:
            skipped_existing += 1
            continue

        highlights = raw.get("highlights") or []
        if isinstance(highlights, str):
            highlights = [highlights]
        if not isinstance(highlights, list):
            highlights = []

        accepted.append(
            {
                "queryId": query_id,
                "rank": rank,
                "title": str(raw.get("title") or "").strip(),
                "url": url,
                "canonicalUrl": canonical,
                "publishedAt": str(raw.get("publishedDate") or "").strip(),
                "author": str(raw.get("author") or "").strip(),
                "image": str(raw.get("image") or "").strip(),
                "highlights": [
                    str(item).strip()
                    for item in highlights[:3]
                    if str(item).strip()
                ],
                "discoveredBy": "exa",
                "exaId": str(raw.get("id") or "").strip(),
            }
        )
    return accepted, skipped_existing


def dedupe_candidates(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in items:
        key = str(item.get("canonicalUrl") or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="WRN Exa discovery prototype")
    parser.add_argument("--queries", type=Path, default=DEFAULT_QUERY_FILE)
    parser.add_argument("--news", type=Path, default=DEFAULT_NEWS_FILE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_FILE)
    parser.add_argument("--max-results", type=int, default=DEFAULT_MAX_RESULTS)
    parser.add_argument("--lookback-hours", type=int, default=DEFAULT_LOOKBACK_HOURS)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration without calling Exa.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    queries = load_queries(args.queries)
    now = utc_now()

    if not queries:
        raise SystemExit("Keine aktiven Exa-Queries konfiguriert.")

    if args.dry_run:
        print(
            f"Exa-Konfiguration OK: {len(queries)} Queries, "
            f"max. {max(1, min(args.max_results, 10))} Resultate je Query."
        )
        return 0

    api_key = os.environ.get("EXA_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("EXA_API_KEY fehlt.")

    existing_urls = existing_article_urls(args.news)
    all_candidates: list[dict[str, Any]] = []
    query_reports: list[dict[str, Any]] = []
    skipped_existing = 0
    total_cost = 0.0

    with requests.Session() as session:
        for query in queries:
            try:
                payload = request_exa(
                    session,
                    api_key,
                    query,
                    max_results=args.max_results,
                    lookback_hours=args.lookback_hours,
                    now=now,
                )
                candidates, skipped = normalized_results(
                    payload,
                    query["id"],
                    existing_urls,
                )
                all_candidates.extend(candidates)
                skipped_existing += skipped

                cost = payload.get("costDollars") or {}
                if isinstance(cost, dict):
                    try:
                        total_cost += float(cost.get("total") or 0.0)
                    except (TypeError, ValueError):
                        pass

                query_reports.append(
                    {
                        "id": query["id"],
                        "query": query["query"],
                        "status": "ok",
                        "resultsReturned": len(payload.get("results") or []),
                        "newCandidates": len(candidates),
                        "requestId": str(payload.get("requestId") or ""),
                    }
                )
            except Exception as exc:
                query_reports.append(
                    {
                        "id": query["id"],
                        "query": query["query"],
                        "status": "error",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )

    candidates = dedupe_candidates(all_candidates)
    output = {
        "schemaVersion": 1,
        "generatedAt": iso(now),
        "discoveredBy": "exa",
        "mode": "review-only",
        "queryCount": len(queries),
        "candidateCount": len(candidates),
        "skippedExisting": skipped_existing,
        "reportedCostUsd": round(total_cost, 6),
        "queries": query_reports,
        "candidates": candidates,
    }
    write_json(args.output, output)

    errors = sum(1 for item in query_reports if item.get("status") != "ok")
    print(
        f"Exa: {len(candidates)} neue Kandidaten, "
        f"{skipped_existing} bereits vorhanden, "
        f"{errors} Query-Fehler, "
        f"gemeldete Kosten ${total_cost:.4f}."
    )
    return 1 if errors == len(queries) else 0


if __name__ == "__main__":
    raise SystemExit(main())
