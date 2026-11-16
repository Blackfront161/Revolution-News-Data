#!/usr/bin/env python3
"""Build small, lazily loadable 30-day news archives per source."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import unicodedata
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from source_import_policy import article_is_withdrawn, restrict_existing_article
from urllib.parse import urlsplit
from reviewed_article_identity import canonicalize_reviewed_articles, canonicalize_reviewed_withdrawals
from build_web_feeds import clean_text, newest_article_at


ROOT = Path(__file__).resolve().parent
DEFAULT_DAYS = 30
DEFAULT_EXCERPT_LIMIT = 1400
MAX_SOURCE_PACKAGE_BYTES = 4 * 1024 * 1024
PUBLIC_ARCHIVE_BASE = "https://blackfront161.github.io/Revolution-News-Data/"
DETAIL_INDEX_SUFFIX = "-bridge-v1"
DETAIL_PREFIX = "bridge-detail-"
DETAIL_PATH = re.compile(r"news-archive/bridge-detail-([0-9a-f]{64})\.json\Z")
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


def detail_index_id(name: str) -> str:
    """A distinct identity also protects older IDB and URL-keyed caches."""
    return source_id(name) + DETAIL_INDEX_SUFFIX


def detail_matches(quick: dict[str, Any], full: dict[str, Any]) -> bool:
    """Bind only an existing complete App body, never infer publisher rights."""
    if any(row.get("importMode") == "metadata-only" for row in (quick, full)):
        return False
    if full.get("contentComplete") is not True or quick.get("webFeedTruncated") is not True:
        return False
    if any(not quick.get(key) or quick.get(key) != full.get(key)
           for key in ("link", "title", "quelleName", "pubDate")):
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
    if not retain_body:
        projected["contentComplete"] = False
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
           for key in ("link", "title", "quelleName", "pubDate")):
        return False
    try:
        url = urlsplit(current["link"])
        if url.scheme != "https" or not url.hostname or url.username or url.password:
            return False
    except ValueError:
        return False
    body = str(current.get("content") or "").strip()
    return bool(body and body == str(previous.get("content") or "").strip())


def can_retain_complete_body(article: dict[str, Any], source_policies=None) -> bool:
    """Retain an admitted canonical body, independently of the bounded quick feed.

    This never hydrates a current row from an older revision or infers a body
    from an excerpt. Restrictions still win; a technical fetch pause is not a
    withdrawal. The quick-feed detail-binding checks remain separate.
    """
    if (article.get("contentComplete") is not True
            or ("webFeedTruncated" in article and article["webFeedTruncated"] is not False)
            or article_is_withdrawn(article)
            or any(not isinstance(article.get(field), str) or not article[field].strip()
                   for field in ("link", "title", "quelleName", "content"))):
        return False
    name = article["quelleName"].strip().casefold()
    policies = [article] + [policy for policy in source_policies or []
                           if str(policy.get("name") or "").strip().casefold() == name]
    if any(policy.get("importMode") not in (None, "", "fulltext")
           or policy.get("contentPolicy") == "metadata_and_links_only"
           or policy.get("status") == "directory-only"
           or article_is_withdrawn(policy) for policy in policies):
        return False
    try:
        url = urlsplit(article["link"])
        # Accessing port validates malformed authorities without making requests.
        _ = url.port
        return bool(url.scheme == "https" and url.hostname
                    and not url.username and not url.password)
    except ValueError:
        return False


def build_source_archives(
    news: list[dict[str, Any]],
    quick_feed: list[dict[str, Any]],
    *,
    previous_articles: list[dict[str, Any]] | None = None,
    source_policies: list[dict[str, Any]] | None = None,
    previous_tracking: dict[str, str] | None = None,
    withdrawn_keys: set[str] | None = None,
    previous_bridged_sources: set[str] | None = None,
    protected_inline_keys: set[str] | None = None,
    days: int = DEFAULT_DAYS,
    excerpt_limit: int = DEFAULT_EXCERPT_LIMIT,
    generated_at: datetime | None = None,
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    news = canonicalize_reviewed_articles(news)
    quick_feed = canonicalize_reviewed_articles(quick_feed)
    previous_articles = canonicalize_reviewed_articles(previous_articles or [])
    def identity(row):
        return tuple(row.get(key) for key in ("link", "title", "quelleName")) + (parse_date(row.get("pubDate")),)
    prior_unique = {}
    for article in previous_articles:
        key = stable_article_key(article)
        if key in prior_unique and prior_unique[key] != article:
            raise ValueError("Conflicting previous archive identity/revision; refusing archive changes")
        prior_unique[key] = article
    for article in news:
        prior = prior_unique.get(stable_article_key(article))
        if prior is not None and identity(prior) != identity(article):
            raise ValueError("Current/previous article identity conflict; refusing archive changes")
    withdrawn_keys = canonicalize_reviewed_withdrawals(withdrawn_keys or set()) | explicit_withdrawal_keys(news, quick_feed, previous_articles or [])
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
    current_keys = {stable_article_key(row) for row in news if isinstance(row, dict)}
    grouped: dict[str, list[tuple[datetime, dict[str, Any]]]] = {}
    for stamp, article in dated:
        if stamp < cutoff or stamp > reference + timedelta(days=1):
            continue
        grouped.setdefault(source_name(article), []).append((stamp, article))

    chunks: dict[str, list[dict[str, Any]]] = {}
    sources = []
    claimed_source_ids = set()
    for name in sorted(grouped, key=str.casefold):
        rows = sorted(grouped[name], key=lambda item: item[0], reverse=True)
        identifier = source_id(name)
        if identifier in claimed_source_ids:
            raise ValueError("Conflicting source package identity; refusing archive changes")
        claimed_source_ids.add(identifier)
        projected = [projected_article(
            article, excerpt_limit,
            retain_body=(can_retain_complete_body(article, source_policies)
                         and (stable_article_key(article) in current_keys
                              or any(retained_detail_matches(previous, article)
                                     for previous in previous_rows.get(stable_article_key(article), [])))),
        ) for _, article in rows]
        # Keep v1 packages unchanged when small. For large sources, separate
        # admitted full texts from their index instead of raising a source cap.
        if (name in (previous_bridged_sources or set())
                or len(payload_bytes(projected)) > MAX_SOURCE_PACKAGE_BYTES):
            projected, details = split_source_details(projected, excerpt_limit,
                                                      protected_inline_keys=protected_inline_keys)
            chunks.update(details)
            # Legacy clients key their durable cache by manifest source.id.
            # A card-only index must not overwrite a cached v1 full-text list.
            identifier = detail_index_id(name)
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
            **({"legacyId": source_id(name)} if identifier != source_id(name) else {}),
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


def split_source_details(rows: list[dict[str, Any]], excerpt_limit: int,
                         *, protected_inline_keys: set[str] | None = None):
    """Separate complete bodies, never infer completeness or discard content.

    Each detail is content-addressed and immutable. The index stays a v1 JSON
    list with all rows, including excerpts that were never full-text admitted.
    An oversized single article or card index still fails closed.
    """
    cards, details = [], {}
    for row in rows:
        # Never turn an already published inline body into an online-only
        # dependency for a legacy source reader. If these protected bodies
        # plus new cards cannot fit, the unchanged index size guard stops us.
        if stable_article_key(row) in (protected_inline_keys or set()):
            cards.append(row)
            continue
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
        identifier = f"{DETAIL_PREFIX}{revision}"
        path = f"news-archive/{identifier}.json"
        card = dict(full, content=body[:excerpt_limit], contentComplete=False,
                    webFeedTruncated=True, webFeedOriginalLength=len(clean_text(body)),
                    detailPath=path, detailUrl=PUBLIC_ARCHIVE_BASE + path)
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
        if detail_index_id(source_name(item)) in chunks:
            identifier = detail_index_id(source_name(item))
        for row in chunks.get(identifier, []):
            path = row.get("detailPath", "")
            if DETAIL_PATH.fullmatch(path):
                candidates = chunks.get(path.removeprefix("news-archive/").removesuffix(".json"), [])
                matches.extend((full, path, True) for full in candidates if detail_matches(item, full))
            elif detail_matches(item, row):
                matches.append((row, f"news-archive/{identifier}.json", None))
        if len(matches) == 1:
            _, path, revision = matches[0]
            item["detailPath"] = path
            # Both published quick-feed readers resolve a relative path against
            # the actually successful feed mirror. The absolute URL is required
            # on source-index cards only; forcing it here breaks that fallback.
        output.append(item)
    return output


def read_article_list(path: Path, label: str) -> list[dict[str, Any]]:
    if path.is_symlink():
        raise ValueError(f"Symlink in {label}; refusing archive changes")
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"Cannot read {label}; refusing archive changes") from error
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"Invalid {label}; refusing archive changes")
    return rows


def read_manifest(path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(path.read_bytes())
    except (OSError, ValueError) as error:
        raise ValueError("Missing or invalid archive manifest") from error
    if (not isinstance(manifest, dict) or manifest.get("schemaVersion") != 1
            or manifest.get("windowDays") != DEFAULT_DAYS
            or not isinstance(manifest.get("sources"), list)
            or manifest.get("sourceCount") != len(manifest["sources"])
            or parse_date(manifest.get("referenceAt")) is None
            or parse_date(manifest.get("generatedAt")) is None
            or parse_date(manifest.get("cutoffAt")) != parse_date(manifest["referenceAt"]) - timedelta(days=DEFAULT_DAYS)):
        raise ValueError("Invalid archive manifest contract")
    names, identifiers = set(), set()
    for source in manifest["sources"]:
        if not isinstance(source, dict) or not isinstance(source.get("name"), str) or not source["name"].strip():
            raise ValueError("Invalid archive source")
        name, identifier = source["name"], source.get("id")
        if (name in names or identifier in identifiers
                or identifier not in {source_id(name), detail_index_id(name)}
                or source.get("path") != f"news-archive/{identifier}.json"
                or not isinstance(source.get("itemCount"), int) or source["itemCount"] < 0
                or parse_date(source.get("trackingStartedAt")) is None):
            raise ValueError("Invalid or ambiguous archive source identity")
        names.add(name)
        identifiers.add(identifier)
    if manifest.get("itemCount") != sum(source["itemCount"] for source in manifest["sources"]):
        raise ValueError("Archive manifest count mismatch")
    return manifest


def resolve_detail(row: dict[str, Any], output: Path) -> dict[str, Any]:
    match = DETAIL_PATH.fullmatch(str(row.get("detailPath", "")))
    if (not match or "detailRevision" in row
            or row.get("detailUrl") != PUBLIC_ARCHIVE_BASE + row["detailPath"]):
        raise ValueError("Invalid previous detail reference; refusing archive changes")
    target = output / f"{DETAIL_PREFIX}{match[1]}.json"
    if target.is_symlink():
        raise ValueError("Symlink in previous detail")
    try:
        raw = target.read_bytes()
        full_rows = json.loads(raw)
    except (OSError, ValueError) as error:
        raise ValueError("Missing or invalid previous detail; refusing archive changes") from error
    if (len(raw) > MAX_SOURCE_PACKAGE_BYTES or hashlib.sha256(raw).hexdigest() != match[1]
            or not isinstance(full_rows, list) or len(full_rows) != 1
            or not isinstance(full_rows[0], dict)
            or any(key in full_rows[0] for key in ("detailPath", "detailUrl", "detailRevision"))
            or not detail_matches(row, full_rows[0])):
        raise ValueError("Previous detail identity or revision mismatch; refusing archive changes")
    return full_rows[0]


def read_previous_archives(output: Path, manifest: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    previous = []
    if manifest is not None:
        paths = [(output / (source["id"] + ".json"), source) for source in manifest["sources"]]
    else:
        # Pure-function legacy fixtures only. Production always uses its manifest.
        paths = [(path, None) for path in sorted(output.glob("*.json"))
                 if not path.name.startswith(DETAIL_PREFIX)] if output.is_dir() else []
    for archive_path, source in paths:
        if source is not None and "legacyPackageSha256" in source:
            legacy = output / f"{source_id(source['name'])}.json"
            if (source.get("legacyPath") != f"news-archive/{legacy.name}" or legacy.is_symlink()
                    or not legacy.is_file()
                    or hashlib.sha256(legacy.read_bytes()).hexdigest() != source["legacyPackageSha256"]):
                raise ValueError("Legacy compatibility package changed unexpectedly")
        raw_rows = read_article_list(archive_path, f"previous archive {archive_path.name}")
        if archive_path.stat().st_size > MAX_SOURCE_PACKAGE_BYTES:
            raise ValueError("Previous package exceeds unchanged byte limit")
        if source is not None and (len(raw_rows) != source["itemCount"]
                or any(source_name(row) != source["name"] for row in raw_rows)):
            raise ValueError("Previous source count or identity mismatch")
        for row in raw_rows:
            if (not stable_article_key(row) or not isinstance(row.get("quelleName"), str)
                    or not row["quelleName"].strip() or parse_date(row.get("pubDate")) is None):
                raise ValueError(f"Invalid previous archive {archive_path.name}; refusing archive changes")
            # A restriction on the index is authoritative and must not be
            # overwritten by an older, still-complete detail revision.
            if article_is_withdrawn(row) or row.get("importMode") == "metadata-only":
                previous.append(row)
                continue
            if any(field in row for field in ("detailPath", "detailUrl", "detailRevision")):
                row = resolve_detail(row, output)
            previous.append(row)
    return previous


def capture_archive_input(bounded, capture, source_policies, created):
    """The bounded feed cannot silently become a second, divergent body authority."""
    from news_archive_capture import merge_capture_rows
    admitted_capture = merge_capture_rows(capture, [], source_policies, now=created)
    lookup = {stable_article_key(row): row for row in admitted_capture}
    for row in bounded:
        key = stable_article_key(row)
        captured = lookup.get(key)
        stamp = parse_date(row.get("pubDate"))
        if stamp is None:
            raise ValueError("Invalid bounded publication date")
        if stamp < created - timedelta(days=DEFAULT_DAYS) or stamp > created + timedelta(days=1):
            continue
        if captured is not None and article_is_withdrawn(captured):
            continue
        admitted = restrict_existing_article(row, source_policies)
        if admitted is None:
            continue
        if captured is None or any(admitted.get(key) != captured.get(key) for key in
                ("link", "title", "quelleName", "pubDate", "content", "contentComplete", "webFeedTruncated")):
            raise ValueError("Bounded news is not bound to the durable capture")
    return admitted_capture


def apply_prior_restrictions(rows, previous):
    """Previously published restrictions are not undone by a stale feed/capture."""
    restricted = {stable_article_key(row): row for row in previous
                  if article_is_withdrawn(row) or row.get("importMode") == "metadata-only"}
    result = []
    for row in rows:
        prior = restricted.get(stable_article_key(row))
        if prior is not None:
            if (any(row.get(key) != prior.get(key) for key in ("link", "title", "quelleName"))
                    or parse_date(row.get("pubDate")) != parse_date(prior.get("pubDate"))):
                raise ValueError("Restricted previous identity cannot be reassigned")
            row = dict(row)
            if article_is_withdrawn(prior):
                row.update(status="withdrawn", deleted=True)
            else:
                row["importMode"] = "metadata-only"
                for key in ("sourceHomepage", "rightsReview"):
                    if key in prior:
                        row[key] = prior[key]
        result.append(row)
    return result


def validate_capture_archive_coverage(captureRows, previousArticles, sourcePolicies, now):
    """Reject an incomplete bootstrap; never borrow an older archived body.

    The archive projection strips surrounding whitespace. Compare that exact
    projection while validating history hashes against their original bytes.
    This is a read-only preflight, also exported for workflow validation.
    """
    from news_archive_capture import merge_capture_rows, HISTORY
    now = now.astimezone(timezone.utc)
    capture = merge_capture_rows(captureRows, [], sourcePolicies, now=now)
    indexed = {}
    for row in capture:
        key = stable_article_key(row)
        if key in indexed and indexed[key] != row:
            raise ValueError("Ambiguous capture coverage identity")
        indexed[key] = row
    previous = {}
    for old in canonicalize_reviewed_articles(previousArticles):
        key = stable_article_key(old)
        if key in previous and previous[key] != old:
            raise ValueError("Ambiguous previous archive coverage identity")
        previous[key] = old
    def identity(row):
        return tuple(row.get(k) for k in ("link", "title", "quelleName")) + (parse_date(row.get("pubDate")),)
    for key, old in previous.items():
        stamp = parse_date(old.get("pubDate"))
        if stamp is None:
            raise ValueError("Invalid previous archive coverage date")
        if not now - timedelta(days=DEFAULT_DAYS) <= stamp <= now + timedelta(days=1):
            continue
        admitted = restrict_existing_article(old, sourcePolicies)
        if admitted is None or not can_retain_complete_body(admitted, sourcePolicies):
            continue
        current = indexed.get(key)
        if current is None or identity(current) != identity(old):
            raise ValueError("Capture missing or mismatched previous full-body identity")
        if article_is_withdrawn(current) or current.get("importMode") == "metadata-only":
            continue
        if not can_retain_complete_body(current, sourcePolicies):
            raise ValueError("Capture full-body coverage downgraded to partial")
        body = old["content"].strip()
        if current["content"].strip() == body:
            continue
        if not any(entry["body"].strip() == body
                   and identity(entry) == identity(old)
                   and entry["bodySha256"] == hashlib.sha256(entry["body"].encode("utf-8")).hexdigest()
                   and entry["provenance"] == "prior-validated-capture"
                   and parse_date(entry["capturedAt"]) <= now
                   for entry in current.get(HISTORY, [])):
            raise ValueError("Capture revision lacks verified previous full-body history")


def preserve_legacy_packages(output, previous_manifest, manifest, chunks):
    """Keep old URL/cache identities usable, subject to current policy and expiry.

    New indexes never overwrite a previously full-list cache ID. A compatible
    old endpoint retains only its already-known identities, using current
    admitted revisions. It must still fit the original per-file bound.
    """
    previous_ids = {source["id"] for source in previous_manifest["sources"]}
    for source in manifest["sources"]:
        name = source["name"]
        if source["id"] != detail_index_id(name):
            continue
        legacy_id = source_id(name)
        legacy_path = output / f"{legacy_id}.json"
        if not legacy_path.exists():
            continue
        prior_source = next((item for item in previous_manifest["sources"] if item["name"] == name), None)
        if legacy_id not in previous_ids and not (prior_source and prior_source.get("legacyPath") == f"news-archive/{legacy_id}.json"):
            raise ValueError("Unbound legacy compatibility file")
        current, cards = {}, {}
        for card in chunks[source["id"]]:
            if DETAIL_PATH.fullmatch(str(card.get("detailPath", ""))):
                full = chunks[card["detailPath"].removeprefix("news-archive/").removesuffix(".json")][0]
            else:
                full = card
            current[stable_article_key(full)] = full
            cards[stable_article_key(full)] = card
        previous = read_article_list(legacy_path, "legacy compatibility package")
        preserved = []
        for old in previous:
            if source_name(old) != name:
                raise ValueError("Legacy compatibility source mismatch")
            new = current.get(stable_article_key(old))
            if new is not None:
                # An old excerpt is not an already-delivered full-text cache.
                # Do not inflate it into the very oversized package we split.
                # Its current excerpt and absolute detail reference are v1-safe.
                preserved.append(new if old.get("contentComplete") is True and not old.get("webFeedTruncated")
                                 else cards[stable_article_key(old)])
        assert_package_size(legacy_id, preserved)
        chunks[legacy_id] = preserved
        source["legacyPath"] = f"news-archive/{legacy_id}.json"
        source["legacyPackageSha256"] = hashlib.sha256(payload_bytes(preserved)).hexdigest()


def verify_output_files(output, manifest, chunks, quick_path, quick, status_path, news_path, bounded_news):
    expected = {f"{identifier}.json" for identifier in chunks}
    actual = {path.name for path in output.glob("*.json")}
    if actual != expected or (output / "details").exists():
        raise ValueError("Unreferenced/missing or incompatible archive files")
    for identifier, rows in chunks.items():
        path = output / f"{identifier}.json"
        if path.is_symlink() or path.read_bytes() != payload_bytes(rows):
            raise ValueError("Archive byte/readback mismatch")
    if quick_path.read_bytes() != payload_bytes(quick):
        raise ValueError("Quick-feed binding/readback mismatch")
    bounded_bytes = (json.dumps(bounded_news, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if news_path.read_bytes() != bounded_bytes:
        raise ValueError("Bounded news policy/retention/readback mismatch")
    status = json.loads(status_path.read_bytes())
    if (not isinstance(status, dict) or not isinstance(status.get("news"), dict)
            or status["news"].get("bytes") != quick_path.stat().st_size
            or status["news"].get("feedCount") != len(quick)
            or status["news"].get("archiveCount") != len(bounded_news)
            or status["news"].get("newestArticleAt") != newest_article_at(quick)):
        raise ValueError("Feed status/readback mismatch")


def verify_publication_freshness(status_path, run_path, *, now=None):
    """Publication needs a real recent aggregation, not a rebuilt old snapshot."""
    status = json.loads(status_path.read_bytes())
    run = json.loads(run_path.read_bytes())
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    fetched = parse_date(status.get("lastSuccessfulFetchAt"))
    published = parse_date(status.get("lastPublishedAt"))
    generated = parse_date(status.get("generatedAt"))
    finished = parse_date(run.get("finishedAt")) if isinstance(run, dict) else None
    if (status.get("ok") is not True or status.get("publication", {}).get("pending") is not False
            or not all((fetched, published, generated, finished))
            or fetched != finished or not fetched <= published <= generated <= now
            or now - fetched > timedelta(hours=1)
            or run.get("mode") not in {"fast", "enrich"}):
        raise ValueError("Publication lacks a verified recent aggregation")


def write_payload(path: Path, payload: Any, *, pretty: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    separators = None if pretty else (",", ":")
    raw = (json.dumps(payload, ensure_ascii=False, indent=2 if pretty else None, separators=separators) + "\n").encode("utf-8")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".bridge-", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--news", type=Path, default=ROOT / "news.json")
    parser.add_argument("--quick-feed", type=Path, default=ROOT / "news-feed.json")
    parser.add_argument("--output", type=Path, default=ROOT / "news-archive")
    parser.add_argument("--manifest", type=Path, default=ROOT / "news-archive-manifest.json")
    parser.add_argument("--capture", type=Path, default=ROOT / "news-archive-capture.json")
    parser.add_argument("--status", type=Path, default=ROOT / "feed-status.json")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--require-fresh", action="store_true")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS)
    parser.add_argument("--excerpt-limit", type=int, default=DEFAULT_EXCERPT_LIMIT)
    args = parser.parse_args()
    if args.require_fresh and not args.verify_only:
        raise ValueError("Fresh publication gate requires read-only verification")

    from news_archive_capture import read_capture, merge_capture_rows, MAX_CAPTURE_BYTES
    bounded_news = canonicalize_reviewed_articles(read_article_list(args.news, "news.json"))
    if not bounded_news or len(bounded_news) > 2000:
        raise ValueError("news.json is empty; refusing archive changes")
    quick_feed = canonicalize_reviewed_articles(read_article_list(args.quick_feed, "quick feed"))
    if not quick_feed or len(quick_feed) > 500 or args.quick_feed.stat().st_size > MAX_SOURCE_PACKAGE_BYTES:
        raise ValueError("Quick feed exceeds its unchanged bounds")
    if args.days != DEFAULT_DAYS:
        raise ValueError("Bridge cannot change the 30-day retention window")

    previous_manifest = read_manifest(args.manifest)
    created = (parse_date(previous_manifest["referenceAt"]) if args.verify_only else datetime.now(timezone.utc))
    previous_tracking = {
        str(source.get("name") or ""): str(source.get("trackingStartedAt") or "")
        for source in previous_manifest.get("sources", [])
        if isinstance(source, dict) and source.get("name")
    } if isinstance(previous_manifest, dict) else {}
    previous_articles = read_previous_archives(args.output, previous_manifest)
    protected_inline_keys = {
        stable_article_key(row)
        for source in previous_manifest["sources"]
        for row in read_article_list(args.output / (source["id"] + ".json"), "prior inline contract")
        if row.get("contentComplete") is True and not row.get("webFeedTruncated")
        and not any(field in row for field in ("detailPath", "detailUrl", "detailRevision"))
    }
    previous_bridged_sources = {source["name"] for source in previous_manifest["sources"]
                                if source["id"] == detail_index_id(source["name"])}
    registry = json.loads((ROOT / "multilingual-source-registry.json").read_text(encoding="utf-8"))
    source_policies = registry.get("sources") if isinstance(registry, dict) else None
    if not isinstance(source_policies, list) or any(
            not isinstance(row, dict) or not isinstance(row.get("name"), str)
            or not row["name"].strip() for row in source_policies):
        raise ValueError("Invalid source policies; refusing archive changes")
    prior_restrictions = [row for row in previous_articles
                          if article_is_withdrawn(row) or row.get("importMode") == "metadata-only"]
    planned_capture = merge_capture_rows(read_capture(args.capture), prior_restrictions, source_policies, now=created)
    validate_capture_archive_coverage(planned_capture, previous_articles, source_policies, created)
    if len(payload_bytes(planned_capture)) > MAX_CAPTURE_BYTES:
        raise ValueError("Capture exceeds unchanged bound")
    bounded_news = apply_prior_restrictions(bounded_news, previous_articles)
    quick_feed = apply_prior_restrictions(quick_feed, previous_articles)
    news = capture_archive_input(bounded_news, planned_capture, source_policies, created)
    # A newly authoritative row-level restriction must reach the quick index
    # in this generation, not only after it becomes a previous archive row.
    quick_feed = apply_prior_restrictions(quick_feed, news)
    from news_archive_capture import public_capture_rows
    captured_lookup = {stable_article_key(row): row for row in public_capture_rows(news)
                       if not article_is_withdrawn(row)
                       and created - timedelta(days=DEFAULT_DAYS) <= parse_date(row["pubDate"]) <= created}
    bounded_news = [captured_lookup[stable_article_key(row)] for row in bounded_news
                    if stable_article_key(row) in captured_lookup]
    if not bounded_news:
        raise ValueError("Policy/retention would leave the bounded news archive empty")
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
        previous_bridged_sources=previous_bridged_sources,
        protected_inline_keys=protected_inline_keys,
        days=DEFAULT_DAYS,
        excerpt_limit=max(240, args.excerpt_limit),
        generated_at=created,
    )
    preserve_legacy_packages(args.output, previous_manifest, manifest, chunks)
    quick_feed = bind_quick_details(quick_feed, chunks, source_policies=source_policies,
                                   withdrawn_keys=withdrawn_keys)
    if not quick_feed or len(payload_bytes(quick_feed)) > MAX_SOURCE_PACKAGE_BYTES:
        raise ValueError("Bound quick feed is empty or exceeds byte limit")
    # Validate status before changing any output. Freshness is not fabricated here.
    status = json.loads(args.status.read_bytes())
    if not isinstance(status, dict) or not isinstance(status.get("news"), dict):
        raise ValueError("Invalid feed status")
    status["news"]["bytes"] = len(payload_bytes(quick_feed))
    status["news"]["feedCount"] = len(quick_feed)
    status["news"]["archiveCount"] = len(bounded_news)
    status["news"]["newestArticleAt"] = newest_article_at(quick_feed)
    expected_old = {source["id"] + ".json" for source in previous_manifest["sources"]}
    expected_old |= {Path(source["legacyPath"]).name for source in previous_manifest["sources"] if source.get("legacyPath")}
    for existing in args.output.glob("*.json"):
        if existing.is_symlink():
            raise ValueError("Symlink in archive output")
        if existing.name.startswith(DETAIL_PREFIX):
            raw = existing.read_bytes()
            if (existing.name != DETAIL_PREFIX + hashlib.sha256(raw).hexdigest() + ".json"
                    or len(raw) > MAX_SOURCE_PACKAGE_BYTES):
                raise ValueError("Immutable detail corruption; refusing output changes")
        elif existing.name not in expected_old:
            raise ValueError("Unknown archive file; refusing output changes")
    if (args.output / "details").exists():
        raise ValueError("Incompatible archive directory; bridge requires legacy v1 basis")
    if args.verify_only:
        if args.capture.read_bytes() != payload_bytes(planned_capture):
            raise ValueError("Capture does not reflect current policy/retention")
        if manifest != previous_manifest:
            raise ValueError("Archive manifest differs from verified capture reconstruction")
        verify_output_files(args.output, manifest, chunks, args.quick_feed, quick_feed, args.status, args.news, bounded_news)
        if args.require_fresh:
            verify_publication_freshness(args.status, ROOT / "aggregate-run-status.json")
        print("[SOURCE-ARCHIVE] Read-only v1 bridge/capture verification passed")
        return
    expected = {f"{identifier}.json" for identifier in chunks}
    write_payload(args.capture, planned_capture)
    # Details first, then indexes. Prevalidation completed before any output
    # change; the existing workflow commits the complete generation together.
    for identifier, items in sorted(chunks.items(), key=lambda item: not item[0].startswith(DETAIL_PREFIX)):
        write_payload(args.output / f"{identifier}.json", items)
    for stale in args.output.glob("*.json"):
        if stale.name not in expected:
            stale.unlink()
    write_payload(args.manifest, manifest, pretty=True)
    write_payload(args.news, bounded_news, pretty=True)
    write_payload(args.quick_feed, quick_feed)
    write_payload(args.status, status)
    verify_output_files(args.output, manifest, chunks, args.quick_feed, quick_feed, args.status, args.news, bounded_news)
    print(
        f"[SOURCE-ARCHIVE] {manifest['itemCount']} articles, "
        f"{manifest['sourceCount']} sources, {manifest['windowDays']} days."
    )


if __name__ == "__main__":
    main()
