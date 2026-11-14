"""Fail-closed producer capture before bounded feed retention.

This is an internal durable input, not a consumer feed or a freshness signal.
Bootstrap is explicit; published workflows must provide an existing valid file.
Ambiguous content revisions stop rather than silently replacing a verified body.
"""
from __future__ import annotations

import json
import hashlib
import os
import tempfile
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlsplit

from reviewed_article_identity import canonicalize_reviewed_articles, canonicalize_reviewed_withdrawals
from source_import_policy import article_is_withdrawn, restrict_existing_article

WITHDRAWN_AT = "captureWithdrawnAt"
WINDOW_DAYS = 30
MAX_CAPTURE_BYTES = 64 * 1024 * 1024
MAX_CAPTURE_ROWS = 30_000
HISTORY = "capturePreviousRevisions"
MAX_HISTORY_ROWS = 128
HISTORY_FIELDS = {"body", "bodySha256", "link", "title", "quelleName", "pubDate", "capturedAt", "provenance"}
IMPORT_MODES = (None, "", "fulltext", "metadata-only", "directory-only", "disabled")


def _json_read(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate capture JSON key")
            result[key] = value
        return result
    def constant(value):
        raise ValueError("Non-finite capture JSON number")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def _date(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Capture article has no publication date")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            result = parsedate_to_datetime(value.replace(" UTC", " +0000"))
        except (ValueError, TypeError, OverflowError) as error:
            raise ValueError("Invalid capture publication date") from error
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)


def read_capture_policies(path):
    try:
        registry = _json_read(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError("Cannot read capture source policies") from error
    policies = registry.get("sources") if isinstance(registry, dict) else None
    _validate_policies(policies)
    return policies


def _validate_policies(policies):
    if not isinstance(policies, list) or any(
        not isinstance(p, dict) or not isinstance(p.get("name"), str)
        or not p["name"].strip() for p in policies
    ):
        raise ValueError("Invalid capture source policies")
    if any(p.get("importMode") not in IMPORT_MODES for p in policies):
        raise ValueError("Unknown capture source import policy")


def _validate_row(row):
    if not isinstance(row, dict):
        raise ValueError("Capture must contain only article objects")
    if row.get("importMode") not in IMPORT_MODES:
        raise ValueError("Unknown capture article import policy")
    for key in ("link", "title", "quelleName"):
        if not isinstance(row.get(key), str) or not row[key].strip():
            raise ValueError("Capture article identity is incomplete")
    try:
        url = urlsplit(row["link"])
        _ = url.port
        if url.scheme not in ("https", "http") or not url.hostname or url.username or url.password:
            raise ValueError("Invalid capture original URL")
    except ValueError as error:
        raise ValueError("Invalid capture original URL") from error
    _date(row.get("pubDate"))
    if not article_is_withdrawn(row) and not isinstance(row.get("content"), str):
        raise ValueError("Capture article content is not a string")
    if WITHDRAWN_AT in row:
        if not article_is_withdrawn(row):
            raise ValueError("Withdrawal timestamp on an active capture article")
        _date(row[WITHDRAWN_AT])
    if HISTORY in row:
        history = row[HISTORY]
        if (not isinstance(history, list) or len(history) > MAX_HISTORY_ROWS
                or article_is_withdrawn(row) or row.get("importMode") == "metadata-only"):
            raise ValueError("Invalid capture revision history")
        seen = set()
        for entry in history:
            if (not isinstance(entry, dict) or set(entry) != HISTORY_FIELDS
                    or not isinstance(entry["body"], str) or not entry["body"]
                    or entry["provenance"] != "prior-validated-capture"
                    or entry["bodySha256"] != hashlib.sha256(entry["body"].encode("utf-8")).hexdigest()
                    or _identity(entry) != _identity(row)):
                raise ValueError("Capture revision history identity or hash mismatch")
            _date(entry["capturedAt"])
            if entry["bodySha256"] in seen:
                raise ValueError("Duplicate capture revision history")
            seen.add(entry["bodySha256"])


def _identity(row):
    return row["link"], row["quelleName"], row["title"], _date(row["pubDate"])


def _complete(row):
    return (row.get("contentComplete") is True and row.get("webFeedTruncated") is not True
            and row.get("importMode") != "metadata-only" and not article_is_withdrawn(row))


def _tombstone(row, now, previous=None):
    # No revoked body, images or old detail pointer survives in the producer file.
    stamp = (previous or {}).get(WITHDRAWN_AT) or row.get(WITHDRAWN_AT) or now.isoformat()
    if _date(stamp) > now:
        raise ValueError("Future capture withdrawal timestamp")
    return {key: row[key] for key in ("link", "title", "quelleName", "pubDate")} | {
        "status": "withdrawn", "deleted": True, "content": "", "contentComplete": False,
        WITHDRAWN_AT: stamp,
    }


def _indexed(rows, label, *, internal=True):
    if not isinstance(rows, list) or len(rows) > MAX_CAPTURE_ROWS:
        raise ValueError(f"Invalid {label}: expected article list")
    # Restrictive tombstones bind the exact original URL, including only the
    # seven already-evidenced aliases. They never admit a changed title/body.
    normalized = canonicalize_reviewed_articles([
        dict(row, link=next(iter(canonicalize_reviewed_withdrawals({row["link"]}))))
        if isinstance(row, dict) and article_is_withdrawn(row) and isinstance(row.get("link"), str)
        else row for row in rows
    ])
    result = {}
    for row in normalized:
        if not internal and isinstance(row, dict) and any(k in row for k in (HISTORY, WITHDRAWN_AT)):
            raise ValueError("Incoming article cannot supply internal capture provenance")
        _validate_row(row)
        key = row["link"]
        if key in result and result[key] != row:
            # A restrictive duplicate wins only with the same exact identity.
            if _identity(result[key]) != _identity(row):
                raise ValueError("Conflicting capture identity")
            if article_is_withdrawn(row):
                result[key] = row
            elif not article_is_withdrawn(result[key]):
                raise ValueError("Conflicting capture revisions")
        else:
            result[key] = dict(row)
    return result


def read_capture(path, *, allow_bootstrap=False):
    """Strict bounded input read; a missing file is never an implicit reset."""
    if Path(path).is_symlink():
        raise ValueError("Capture cannot be a symlink")
    try:
        with Path(path).open("rb") as source:
            raw = source.read(MAX_CAPTURE_BYTES + 1)
    except FileNotFoundError as error:
        if allow_bootstrap:
            return []
        raise ValueError("Capture is missing; explicit bootstrap required") from error
    except OSError as error:
        raise ValueError("Cannot read existing capture; refusing checkpoint") from error
    if len(raw) > MAX_CAPTURE_BYTES:
        raise ValueError("Capture exceeds byte limit; refusing checkpoint")
    try:
        rows = _json_read(raw)
    except (ValueError, UnicodeError) as error:
        raise ValueError("Invalid existing capture JSON; refusing checkpoint") from error
    return list(_indexed(rows, "previous capture").values())


def public_capture_rows(rows):
    """Never carry producer-only revision history into consumer feeds."""
    return [{key: value for key, value in row.items() if key not in {HISTORY, WITHDRAWN_AT}}
            for row in rows]


def load_capture_for_aggregation(path, bounded_rows, source_policies, *, now=None):
    """An older complete article remains known after leaving the 2,000-row list."""
    return public_capture_rows(merge_capture_rows(read_capture(path), bounded_rows,
                                                  source_policies, now=now))


def merge_capture_rows(previous, current, source_policies, *, now=None):
    """Merge an unbounded checkpoint without changing completeness or old text.

    Active identities and complete bodies are not guessed across revisions. A
    current explicit source/row restriction supersedes any earlier body. A new
    complete revision retains the prior verified body in bounded internal
    history; a changed partial revision stops instead of borrowing completeness.
    """
    _validate_policies(source_policies)
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    cutoff = now - timedelta(days=WINDOW_DAYS)
    old, incoming = _indexed(previous, "previous capture"), _indexed(current, "current capture", internal=False)
    result = []
    for key in sorted(old.keys() | incoming.keys()):
        previous_row, current_row = old.get(key), incoming.get(key)
        row = current_row or previous_row
        # Existing withdrawal cannot be undone by a feed replay for 30 days.
        withdrawn = article_is_withdrawn(row) or (previous_row is not None and article_is_withdrawn(previous_row))
        if withdrawn:
            row = _tombstone(previous_row or row, now, previous_row)
            if _date(row[WITHDRAWN_AT]) >= cutoff:
                result.append(row)
            continue
        if previous_row is not None and current_row is not None and _identity(previous_row) != _identity(current_row):
            raise ValueError("Capture identity changed; refusing unverified replacement")
        stamp = _date(row["pubDate"])
        if stamp < cutoff or stamp > now + timedelta(days=1):
            continue
        admitted = restrict_existing_article(row, source_policies)
        if admitted is None:
            result.append(_tombstone(row, now, previous_row))
            continue
        if (previous_row and previous_row.get("importMode") == "metadata-only"
                and admitted.get("importMode") != "metadata-only"):
            raise ValueError("Restricted capture cannot be reactivated by a feed replay")
        # Apply current policy to old content too before comparing revisions.
        old_admitted = restrict_existing_article(previous_row, source_policies) if previous_row else None
        history = list((previous_row or {}).get(HISTORY, []))
        if any(_date(entry["capturedAt"]) > now for entry in history):
            raise ValueError("Future capture revision timestamp")
        if admitted.get("importMode") == "metadata-only":
            history = []
        elif (old_admitted is not None and _complete(old_admitted)
                and admitted.get("content") != old_admitted.get("content")):
            if not _complete(admitted):
                raise ValueError("Complete capture body changed to partial; refusing unverified revision")
            body = old_admitted["content"]
            body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
            if body_hash not in {entry["bodySha256"] for entry in history}:
                history.append({key: old_admitted[key] for key in ("link", "title", "quelleName", "pubDate")} | {
                    "body": body, "bodySha256": body_hash, "capturedAt": now.isoformat(),
                    "provenance": "prior-validated-capture",
                })
        if len(history) > MAX_HISTORY_ROWS:
            raise ValueError("Capture revision history exceeds limit; refusing checkpoint")
        # A flag downgrade with identical bytes is safe: preserve bytes, not the old flag.
        admitted = dict(admitted)
        admitted.pop(HISTORY, None)
        if history:
            admitted[HISTORY] = history
        result.append(admitted)
    if len(result) > MAX_CAPTURE_ROWS:
        raise ValueError("Capture exceeds row limit; refusing checkpoint")
    return sorted(result, key=lambda row: (-_date(row["pubDate"]).timestamp(), row["link"]))


def capture_news_archive(rows, path, source_policies, *, now=None, allow_initialize=False):
    """Prevalidate, atomically persist, then return the complete retained list.

    No bounded news/event output may be written before this call succeeds.
    Missing state is an error unless an explicit, reviewed bootstrap permits it.
    """
    path = Path(path)
    previous = read_capture(path, allow_bootstrap=allow_initialize)
    captured = merge_capture_rows(previous, rows, source_policies, now=now)
    payload = (json.dumps(captured, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    if len(payload) > MAX_CAPTURE_BYTES:
        raise ValueError("Capture exceeds byte limit; refusing checkpoint")
    # The directory must already exist. A temp file is private to this call.
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        if os.name == "posix":
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return captured
