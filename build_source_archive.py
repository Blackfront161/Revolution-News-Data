#!/usr/bin/env python3
"""Build small, lazily loadable 30-day news archives per source."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from source_import_policy import article_is_withdrawn, restrict_existing_article
from urllib.parse import urlsplit
from build_web_feeds import clean_text, newest_article_at


ROOT = Path(__file__).resolve().parent
DEFAULT_DAYS = 30
DEFAULT_EXCERPT_LIMIT = 1400
MAX_SOURCE_PACKAGE_BYTES = 4 * 1024 * 1024
PUBLIC_ARCHIVE_BASE = "https://blackfront161.github.io/Revolution-News-Data/"
DETAIL_PATH = re.compile(r"news-archive/details/([0-9a-f]{64})\.json\Z")
CARD_FIELDS = (
    "kontinent", "categories", "primaryRegion", "primaryTopic",
    "secondaryTopics", "classificationConfidence", "classificationMethod",
    "editorialReview", "editorialReviewReasons", "quelleName", "author",
    "title", "link", "pubDate", "content", "contentComplete", "image",
    "images", "language", "languages", "originCountry", "originCountryCode",
    "originRegion", "sourceHomepage", "sourceTags", "type", "sourceType", "importMode", "rightsReview",
)


def read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return fallback


def parse_date(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(text.replace(" UTC", " +0000"))
        except (TypeError, ValueError, OverflowError):
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso(value: datetime | None) -> str:
    return value.isoformat().replace("+00:00", "Z") if value else ""


def source_name(article: dict[str, Any]) -> str:
    return str(article.get("quelleName") or "Unknown source").strip()


def stable_article_key(article: dict[str, Any]) -> str:
    return str(article.get("link") or article.get("id") or article.get("title") or "").strip()


def source_id(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.casefold()).strip("-")[:54]
    digest = hashlib.sha256(name.casefold().encode("utf-8")).hexdigest()[:8]
    return f"{slug or 'source'}-{digest}"


def detail_matches(quick: dict[str, Any], full: dict[str, Any]) -> bool:
    """Bind only an existing complete App body, never infer publisher rights."""
    if any(row.get("importMode") == "metadata-only" for row in (quick, full)):
        return False
    if full.get("contentComplete") is not True or quick.get("webFeedTruncated") is not True:
        return False
    if any(not quick.get(key) or quick.get(key) != full.get(key)
           for key in ("link", "title", "quelleName")):
        return False
    try:
        url = urlsplit(quick["link"])
        if url.scheme != "https" or not url.hostname or url.username or url.password:
            return False
    except ValueError:
        return False
    body, excerpt = clean_text(full.get("content")), clean_text(quick.get("content"))
    prefix = excerpt[:-2] if excerpt.endswith(" …") else excerpt
    return bool(prefix and len(body) > len(excerpt)
                and quick.get("webFeedOriginalLength") == len(body)
                and body.startswith(prefix))


def projected_article(article: dict[str, Any], excerpt_limit: int, *, retain_body: bool = False) -> dict[str, Any]:
    projected = {key: article[key] for key in CARD_FIELDS if key in article}
    content = str(projected.get("content") or "").strip()
    projected["content"] = content if retain_body else content[:excerpt_limit]
    if not retain_body and len(content) > excerpt_limit:
        projected["webFeedTruncated"] = True
        projected["webFeedOriginalLength"] = len(content)
        projected["contentComplete"] = False
    images = projected.get("images")
    if isinstance(images, list):
        projected["images"] = images[:1]
    return projected


def retained_detail_matches(previous: dict[str, Any], current: dict[str, Any]) -> bool:
    """Keep an already delivered full body only against the same current body."""
    if any(row.get("importMode") == "metadata-only"
           or row.get("contentComplete") is not True
           or row.get("webFeedTruncated") is True for row in (previous, current)):
        return False
    if any(not current.get(key) or current.get(key) != previous.get(key)
           for key in ("link", "title", "quelleName")):
        return False
    try:
        url = urlsplit(current["link"])
        if url.scheme != "https" or not url.hostname or url.username or url.password:
            return False
    except ValueError:
        return False
    body = str(current.get("content") or "").strip()
    return bool(body and body == str(previous.get("content") or "").strip())


def build_source_archives(
    news: list[dict[str, Any]],
    quick_feed: list[dict[str, Any]],
    *,
    previous_articles: list[dict[str, Any]] | None = None,
    source_policies: list[dict[str, Any]] | None = None,
    previous_tracking: dict[str, str] | None = None,
    withdrawn_keys: set[str] | None = None,
    days: int = DEFAULT_DAYS,
    excerpt_limit: int = DEFAULT_EXCERPT_LIMIT,
    generated_at: datetime | None = None,
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    withdrawn_keys = (withdrawn_keys or set()) | explicit_withdrawal_keys(news, quick_feed, previous_articles or [])
    merged: dict[str, dict[str, Any]] = {}
    previous_rows: dict[str, list[dict[str, Any]]] = {}
    for article in previous_articles or []:
        if isinstance(article, dict) and stable_article_key(article):
            merged[stable_article_key(article)] = article
            previous_rows.setdefault(stable_article_key(article), []).append(article)
    # Current archive rows win over an older projected copy of the same item.
    for article in news:
        if isinstance(article, dict) and stable_article_key(article):
            merged[stable_article_key(article)] = article
    restricted = {}
    for key, article in merged.items():
        if key in withdrawn_keys:
            continue
        admitted = restrict_existing_article(article, source_policies)
        if admitted is not None:
            restricted[key] = admitted
    merged = restricted

    dated = [
        (parse_date(article.get("pubDate")), article)
        for article in merged.values()
        if isinstance(article, dict) and source_name(article)
    ]
    dated = [(stamp, article) for stamp, article in dated if stamp]
    created = (generated_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    # A source may publish an event with a future pubDate. Archive coverage is
    # measured against the build time, never against that future article.
    reference = created
    cutoff = reference - timedelta(days=max(1, days))
    quick_keys = {
        stable_article_key(article)
        for article in quick_feed
        if isinstance(article, dict)
    }
    quick_rows = {stable_article_key(row): row for row in quick_feed if isinstance(row, dict)}
    current_keys = {stable_article_key(row) for row in news if isinstance(row, dict)}
    grouped: dict[str, list[tuple[datetime, dict[str, Any]]]] = {}
    for stamp, article in dated:
        if stamp < cutoff or stamp > reference + timedelta(days=1):
            continue
        grouped.setdefault(source_name(article), []).append((stamp, article))

    chunks: dict[str, list[dict[str, Any]]] = {}
    sources = []
    for name in sorted(grouped, key=str.casefold):
        rows = sorted(grouped[name], key=lambda item: item[0], reverse=True)
        identifier = source_id(name)
        projected = [projected_article(
            article, excerpt_limit,
            retain_body=((stable_article_key(article) in current_keys
                          and detail_matches(quick_rows.get(stable_article_key(article), {}), article))
                         or any(retained_detail_matches(previous, article)
                                for previous in previous_rows.get(stable_article_key(article), []))),
        ) for _, article in rows]
        # Keep v1 packages unchanged when small. For large sources, separate
        # admitted full texts from their index instead of raising a source cap.
        if len(payload_bytes(projected)) > MAX_SOURCE_PACKAGE_BYTES:
            projected, details = split_source_details(projected, excerpt_limit)
            chunks.update(details)
        assert_package_size(identifier, projected)
        chunks[identifier] = projected
        oldest = rows[-1][0]
        newest = rows[0][0]
        tracking_started = parse_date((previous_tracking or {}).get(name)) or created
        coverage_complete = (
            oldest <= cutoff + timedelta(hours=24)
            and tracking_started <= cutoff + timedelta(hours=24)
        )
        sources.append({
            "id": identifier,
            "name": name,
            "path": f"news-archive/{identifier}.json",
            "itemCount": len(rows),
            "quickIndexCount": sum(stable_article_key(article) in quick_keys for _, article in rows),
            "newestAt": iso(newest),
            "oldestAt": iso(oldest),
            "coverage": "complete" if coverage_complete else "partial",
            "coverageDays": round(min(days, max(0.0, (reference - oldest).total_seconds() / 86400)), 2),
            "trackingStartedAt": iso(tracking_started),
        })

    manifest = {
        "schemaVersion": 1,
        "generatedAt": iso(created),
        "windowDays": days,
        "referenceAt": iso(reference),
        "cutoffAt": iso(cutoff),
        "sourceCount": len(sources),
        "itemCount": sum(source["itemCount"] for source in sources),
        "quickIndexCount": sum(source["quickIndexCount"] for source in sources),
        "sources": sources,
    }
    return manifest, chunks


def explicit_withdrawal_keys(*datasets) -> set[str]:
    return {stable_article_key(row) for rows in datasets for row in rows
            if isinstance(row, dict) and article_is_withdrawn(row) and stable_article_key(row)}


def payload_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def assert_package_size(identifier: str, rows: list) -> None:
    size = len(payload_bytes(rows))
    if size > MAX_SOURCE_PACKAGE_BYTES:
        raise ValueError(f"Source package {identifier} is {size} bytes and exceeds {MAX_SOURCE_PACKAGE_BYTES} bytes; refusing silent body truncation")


def split_source_details(rows: list[dict[str, Any]], excerpt_limit: int):
    """Separate complete bodies, never infer completeness or discard content.

    Each detail is content-addressed and immutable. The index stays a v1 JSON
    list with all rows, including excerpts that were never full-text admitted.
    An oversized single article or card index still fails closed.
    """
    cards, details = [], {}
    for row in rows:
        if row.get("contentComplete") is not True or row.get("webFeedTruncated") is True or row.get("importMode") == "metadata-only":
            cards.append(row)
            continue
        body = str(row.get("content") or "")
        if len(body) <= excerpt_limit:
            cards.append(row)
            continue
        full = dict(row)
        for field in ("detailPath", "detailUrl", "detailRevision"):
            full.pop(field, None)
        assert_package_size("individual article", [full])
        revision = hashlib.sha256(payload_bytes([full])).hexdigest()
        identifier = f"details/{revision}"
        path = f"news-archive/{identifier}.json"
        card = dict(full, content=body[:excerpt_limit], contentComplete=False,
                    webFeedTruncated=True, webFeedOriginalLength=len(clean_text(body)),
                    detailPath=path, detailUrl=PUBLIC_ARCHIVE_BASE + path,
                    detailRevision=revision)
        if not detail_matches(card, full):
            raise ValueError("Cannot safely bind archived full text; refusing silent body truncation")
        details[identifier] = [full]
        cards.append(card)
    return cards, details


def bind_quick_details(quick_feed: list[dict[str, Any]], chunks: dict[str, list[dict[str, Any]]],
                       *, source_policies=None, withdrawn_keys=None) -> list[dict[str, Any]]:
    """Only point at the exact complete row actually written to a package."""
    output = []
    for quick in quick_feed:
        if stable_article_key(quick) in (withdrawn_keys or set()):
            continue
        admitted = restrict_existing_article(quick, source_policies)
        if admitted is None:
            continue
        item = dict(admitted)
        for field in ("detailPath", "detailUrl", "detailRevision"):
            item.pop(field, None)
        identifier = source_id(source_name(item))
        matches = []
        for row in chunks.get(identifier, []):
            path = row.get("detailPath", "")
            if DETAIL_PATH.fullmatch(path):
                candidates = chunks.get(path.removeprefix("news-archive/").removesuffix(".json"), [])
                matches.extend((full, path, row.get("detailRevision")) for full in candidates if detail_matches(item, full))
            elif detail_matches(item, row):
                matches.append((row, f"news-archive/{identifier}.json", None))
        if len(matches) == 1:
            _, path, revision = matches[0]
            item["detailPath"] = path
            if revision:
                item["detailRevision"] = revision
                item["detailUrl"] = PUBLIC_ARCHIVE_BASE + path
        output.append(item)
    return output


def read_article_list(path: Path, label: str) -> list[dict[str, Any]]:
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"Cannot read {label}; refusing archive changes") from error
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"Invalid {label}; refusing archive changes")
    return rows


def read_previous_archives(output: Path) -> list[dict[str, Any]]:
    previous = []
    for archive_path in sorted(output.glob("*.json")) if output.is_dir() else []:
        for row in read_article_list(archive_path, f"previous archive {archive_path.name}"):
            if (not stable_article_key(row) or not isinstance(row.get("quelleName"), str)
                    or not row["quelleName"].strip() or parse_date(row.get("pubDate")) is None):
                raise ValueError(f"Invalid previous archive {archive_path.name}; refusing archive changes")
            # A restriction on the index is authoritative and must not be
            # overwritten by an older, still-complete detail revision.
            if article_is_withdrawn(row) or row.get("importMode") == "metadata-only":
                previous.append(row)
                continue
            if any(field in row for field in ("detailPath", "detailUrl", "detailRevision")):
                match = DETAIL_PATH.fullmatch(str(row.get("detailPath", "")))
                if not match or match[1] != row.get("detailRevision"):
                    raise ValueError("Invalid previous detail reference; refusing archive changes")
                target = output / "details" / f"{match[1]}.json"
                try:
                    raw = target.read_bytes()
                    full_rows = json.loads(raw)
                except (OSError, ValueError) as error:
                    raise ValueError("Missing or invalid previous detail; refusing archive changes") from error
                if (hashlib.sha256(raw).hexdigest() != match[1] or not isinstance(full_rows, list)
                        or len(full_rows) != 1 or not isinstance(full_rows[0], dict)
                        or parse_date(full_rows[0].get("pubDate")) is None
                        or full_rows[0].get("pubDate") != row.get("pubDate")
                        or not detail_matches(row, full_rows[0])):
                    raise ValueError("Previous detail identity or revision mismatch; refusing archive changes")
                row = full_rows[0]
            previous.append(row)
    return previous


def write_payload(path: Path, payload: Any, *, pretty: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    separators = None if pretty else (",", ":")
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2 if pretty else None, separators=separators) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--news", type=Path, default=ROOT / "news.json")
    parser.add_argument("--quick-feed", type=Path, default=ROOT / "news-feed.json")
    parser.add_argument("--output", type=Path, default=ROOT / "news-archive")
    parser.add_argument("--manifest", type=Path, default=ROOT / "news-archive-manifest.json")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS)
    parser.add_argument("--excerpt-limit", type=int, default=DEFAULT_EXCERPT_LIMIT)
    args = parser.parse_args()

    news = read_article_list(args.news, "news.json")
    quick_feed = read_article_list(args.quick_feed, "quick feed")

    previous_manifest = read_json(args.manifest, {})
    previous_tracking = {
        str(source.get("name") or ""): str(source.get("trackingStartedAt") or "")
        for source in previous_manifest.get("sources", [])
        if isinstance(source, dict) and source.get("name")
    } if isinstance(previous_manifest, dict) else {}
    previous_articles = read_previous_archives(args.output)
    registry = json.loads((ROOT / "multilingual-source-registry.json").read_text(encoding="utf-8"))
    source_policies = registry.get("sources") if isinstance(registry, dict) else None
    if not isinstance(source_policies, list) or any(not isinstance(row, dict) for row in source_policies):
        raise ValueError("Invalid source policies; refusing archive changes")
    withdrawn_keys = explicit_withdrawal_keys(news, previous_articles, quick_feed)
    quick_feed = bind_quick_details(quick_feed, {}, source_policies=source_policies,
                                   withdrawn_keys=withdrawn_keys)
    manifest, chunks = build_source_archives(
        news,
        quick_feed,
        previous_articles=previous_articles,
        source_policies=source_policies,
        withdrawn_keys=withdrawn_keys,
        previous_tracking=previous_tracking,
        days=max(1, args.days),
        excerpt_limit=max(240, args.excerpt_limit),
    )
    args.output.mkdir(parents=True, exist_ok=True)
    expected = {f"{identifier}.json" for identifier in chunks}
    # Details first, then indexes. Prevalidation completed before any output
    # change; the existing workflow commits the complete generation together.
    for identifier, items in sorted(chunks.items(), key=lambda item: not item[0].startswith("details/")):
        write_payload(args.output / f"{identifier}.json", items)
    for stale in args.output.glob("*.json"):
        if stale.name not in expected:
            stale.unlink()
    write_payload(args.manifest, manifest, pretty=True)
    write_payload(args.quick_feed, bind_quick_details(quick_feed, chunks, source_policies=source_policies,
                                                   withdrawn_keys=withdrawn_keys))
    # The detail routes change feed bytes after build_web_feeds.py wrote status.
    if args.quick_feed.resolve() == (ROOT / "news-feed.json").resolve():
        status_path = ROOT / "feed-status.json"
        status = read_json(status_path, {})
        if isinstance(status, dict) and isinstance(status.get("news"), dict):
            status["news"]["bytes"] = args.quick_feed.stat().st_size
            status["news"]["feedCount"] = len(quick_feed)
            status["news"]["newestArticleAt"] = newest_article_at(quick_feed)
            write_payload(status_path, status)
    # Remove details no longer admitted or retained, including withdrawals and
    # expired articles. A stale CDN index must fail visibly, never revive them.
    detail_dir = args.output / "details"
    for stale in detail_dir.glob("*.json") if detail_dir.is_dir() else []:
        if f"details/{stale.name}" not in expected:
            stale.unlink()
    print(
        f"[SOURCE-ARCHIVE] {manifest['itemCount']} articles, "
        f"{manifest['sourceCount']} sources, {manifest['windowDays']} days."
    )


if __name__ == "__main__":
    main()
