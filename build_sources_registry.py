#!/usr/bin/env python3
"""Build one declarative registry from static and dynamically merged sources."""

from __future__ import annotations

import ast
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "sources-registry.json"

JSON_INPUTS = (
    "multilingual-source-registry.json",
    "source-catalog.json",
    "podcast-sources.json",
    "radio-sources.json",
)

NAME_FIELDS = (
    "name",
    "sourceName",
    "title",
    "station",
    "label",
    "podcast",
)

URL_FIELDS = (
    "feedUrl",
    "url",
    "feed",
    "rss",
    "streamUrl",
    "stream_url",
    "homepage",
    "website",
    "pageUrl",
)

LANGUAGE_FIELDS = (
    "languages",
    "language",
    "lang",
    "sprache",
    "locale",
)


def read_json(path: Path, fallback: Any) -> Any:
    if not path.is_file():
        return fallback

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


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

    path = re.sub(r"/+", "/", parsed.path or "/")

    if path != "/":
        path = path.rstrip("/")

    return urlunsplit(
        (
            parsed.scheme.lower(),
            host,
            path,
            parsed.query,
            "",
        )
    )


def as_languages(value: Any) -> list[str]:
    if isinstance(value, str):
        values = re.split(r"[,;\s]+", value)
    elif isinstance(value, list):
        values = value
    else:
        values = []

    result: list[str] = []

    aliases = {
        "english": "en",
        "deutsch": "de",
        "german": "de",
        "español": "es",
        "spanish": "es",
        "français": "fr",
        "french": "fr",
        "italiano": "it",
        "italian": "it",
        "português": "pt",
        "portuguese": "pt",
        "русский": "ru",
        "russian": "ru",
        "ελληνικά": "el",
        "greek": "el",
        "türkçe": "tr",
        "turkish": "tr",
    }

    for item in values:
        raw = str(item or "").strip().lower()

        if not raw:
            continue

        language = aliases.get(
            raw,
            raw,
        )

        language = re.split(r"[-_]", language)[0]

        if re.fullmatch(r"[a-z]{2,3}", language):
            if language not in result:
                result.append(language)

    return result


def infer_languages(name: str, url: str) -> list[str]:
    haystack = f"{name} {url}".lower()

    rules = (
        ("de", (
            ".de/", ".de ", "deutsch", "germany",
            "deutschland", "graswurzel", "fau-",
        )),
        ("es", (
            ".es/", ".org.ar", "argentina", "méxico",
            "mexico", "españ", "spanish", "chile",
            "colombia", "subversiones", "anred",
        )),
        ("fr", (
            ".fr/", "france", "français", "paris",
            "marseille", "rebellyon", "lundi",
        )),
        ("it", (
            ".it/", "italia", "italiano",
        )),
        ("pt", (
            ".pt/", ".br/", "brasil", "brazil",
            "agência", "agencia publica", "pública",
        )),
        ("ru", (
            ".ru/", "russia", "russian", "avtonom",
        )),
        ("el", (
            ".gr/", "greece", "greek", "omniatv",
            "alerta gr",
        )),
        ("tr", (
            ".tr/", "turkey", "turkish",
        )),
        ("pl", (
            ".pl/", "poland", "polska", "federacja",
        )),
        ("id", (
            ".id/", "indonesia", "palang hitam",
        )),
        ("zh", (
            ".cn/", "china", "chinese", "chuang",
        )),
        ("ca", (
            ".cat/", "catalunya", "catalan",
        )),
    )

    result = [
        language
        for language, markers in rules
        if any(marker in haystack for marker in markers)
    ]

    return result


def first_value(
    item: dict[str, Any],
    fields: tuple[str, ...],
) -> str:
    for field in fields:
        value = item.get(field)

        if value not in (None, "", [], {}):
            return str(value).strip()

    return ""


def extract_languages(
    item: dict[str, Any],
    *,
    name: str,
    url: str,
) -> tuple[list[str], str]:
    for field in LANGUAGE_FIELDS:
        if field not in item:
            continue

        languages = as_languages(item.get(field))

        if languages:
            return languages, "explicit"

    inferred = infer_languages(name, url)

    if inferred:
        return inferred, "inferred"

    return ["und"], "unknown"


def extract_categories(
    item: dict[str, Any],
    inherited: str = "",
) -> list[str]:
    value = item.get(
        "categories",
        item.get("category", []),
    )

    if isinstance(value, str):
        values = [value]
    elif isinstance(value, list):
        values = value
    else:
        values = []

    if inherited:
        values.append(inherited)

    result: list[str] = []

    for category in values:
        clean = str(category or "").strip()

        if clean and clean not in result:
            result.append(clean)

    return result


def is_source_like(item: dict[str, Any]) -> bool:
    return bool(
        first_value(item, NAME_FIELDS)
        and first_value(item, URL_FIELDS)
    )


def flatten_json(
    data: Any,
    *,
    origin: str,
    inherited_category: str = "",
) -> list[tuple[dict[str, Any], str, str]]:
    rows: list[tuple[dict[str, Any], str, str]] = []

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                if is_source_like(item):
                    rows.append(
                        (item, origin, inherited_category)
                    )
                else:
                    rows.extend(
                        flatten_json(
                            item,
                            origin=origin,
                            inherited_category=(
                                inherited_category
                            ),
                        )
                    )

    elif isinstance(data, dict):
        if is_source_like(data):
            rows.append((data, origin, inherited_category))
        else:
            for key, value in data.items():
                category = inherited_category

                if isinstance(value, list):
                    category = str(key)

                rows.extend(
                    flatten_json(
                        value,
                        origin=origin,
                        inherited_category=category,
                    )
                )

    return rows


def extract_aggregate_rows() -> list[
    tuple[dict[str, Any], str, str]
]:
    path = ROOT / "aggregate.py"

    if not path.is_file():
        return []

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    rows: list[tuple[dict[str, Any], str, str]] = []

    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue

        value_node = node.value

        if value_node is None:
            continue

        try:
            value = ast.literal_eval(value_node)
        except Exception:
            continue

        rows.extend(
            flatten_json(
                value,
                origin="aggregate.py",
            )
        )

    return rows


def normalize_record(
    item: dict[str, Any],
    *,
    origin: str,
    inherited_category: str,
) -> dict[str, Any] | None:
    name = first_value(item, NAME_FIELDS)
    url = first_value(item, URL_FIELDS)

    if not name or not url:
        return None

    languages, language_source = extract_languages(
        item,
        name=name,
        url=url,
    )

    status = str(item.get("status", "active")).lower()

    active = status not in {
        "archived",
        "disabled",
        "inactive",
        "removed",
    }

    media_type = str(
        item.get(
            "kind",
            item.get(
                "mediaType",
                (
                    "radio"
                    if "stream" in " ".join(item.keys()).lower()
                    else (
                        "podcast"
                        if "podcast" in origin
                        else "news"
                    )
                ),
            ),
        )
    )

    return {
        "name": name,
        "url": url,
        "canonicalUrl": canonical_url(url),
        "homepage": str(
            item.get(
                "homepage",
                item.get("website", ""),
            )
            or ""
        ).strip(),
        "languages": languages,
        "languageSource": language_source,
        "categories": extract_categories(
            item,
            inherited_category,
        ),
        "mediaType": media_type,
        "status": status,
        "active": active,
        "origins": [origin],
    }


def merge_record(
    target: dict[str, Any],
    incoming: dict[str, Any],
) -> None:
    for language in incoming["languages"]:
        if language not in target["languages"]:
            target["languages"].append(language)

    if (
        target["languages"] == ["und"]
        and incoming["languages"] != ["und"]
    ):
        target["languages"] = list(incoming["languages"])
        target["languageSource"] = incoming[
            "languageSource"
        ]

    for category in incoming["categories"]:
        if category not in target["categories"]:
            target["categories"].append(category)

    for origin in incoming["origins"]:
        if origin not in target["origins"]:
            target["origins"].append(origin)

    if not target["homepage"] and incoming["homepage"]:
        target["homepage"] = incoming["homepage"]

    target["active"] = target["active"] or incoming["active"]


def build_registry() -> dict[str, Any]:
    rows = extract_aggregate_rows()

    for filename in JSON_INPUTS:
        path = ROOT / filename

        if not path.is_file():
            continue

        rows.extend(
            flatten_json(
                read_json(path, {}),
                origin=filename,
            )
        )

    merged: dict[str, dict[str, Any]] = {}

    for item, origin, category in rows:
        record = normalize_record(
            item,
            origin=origin,
            inherited_category=category,
        )

        if record is None:
            continue

        key = (
            record["canonicalUrl"]
            or re.sub(
                r"[^a-z0-9]+",
                "",
                record["name"].lower(),
            )
        )

        if key not in merged:
            merged[key] = record
        else:
            merge_record(merged[key], record)

    records = sorted(
        merged.values(),
        key=lambda item: item["name"].casefold(),
    )

    active = [
        item for item in records
        if item["active"]
    ]

    known_languages = sorted({
        language
        for item in active
        for language in item["languages"]
        if language != "und"
    })

    payload = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(
            timezone.utc
        ).isoformat(),
        "sourceCount": len(records),
        "activeSourceCount": len(active),
        "knownLanguages": known_languages,
        "sources": records,
    }

    OUTPUT.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    return payload


def main() -> int:
    payload = build_registry()
    print(
        json.dumps(
            {
                "sourceCount": payload["sourceCount"],
                "activeSourceCount":
                    payload["activeSourceCount"],
                "knownLanguages":
                    payload["knownLanguages"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    if payload["activeSourceCount"] == 0:
        print("FEHLER: Keine aktiven Quellen erkannt.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
