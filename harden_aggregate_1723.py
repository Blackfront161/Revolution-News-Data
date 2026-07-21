#!/usr/bin/env python3
"""Harden aggregate.py without replacing its source catalogue.

WRN 1.7.23 goals:
- normalize null and non-string feed values;
- skip malformed entries instead of aborting the whole aggregation;
- write a structured per-entry error report;
- preserve the complete existing source dictionary;
- fail safely when the expected aggregation structure is not recognized.
"""

from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import py_compile
import re
import shutil


ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "aggregate.py"
BACKUP = ROOT / "aggregate.py.pre-1723.bak"
REPORT = ROOT / "aggregate-hardening-report.json"
MARKER = "# WRN 1.7.23 ENTRY SAFETY"


HELPERS = r"""
# WRN 1.7.23 ENTRY SAFETY
AGGREGATE_ENTRY_ERRORS = []


def safe_text(value, fallback=""):
    # Return a stripped string for arbitrary feed values.
    if value is None:
        return fallback

    try:
        text = value if isinstance(value, str) else str(value)
    except Exception:
        return fallback

    text = text.strip()
    return text if text else fallback


def safe_lower(value, fallback=""):
    return safe_text(value, fallback).casefold()


def log_feed_entry_error(feed_name, entry, error):
    # Record one malformed feed entry without stopping other entries.
    try:
        title_value = (
            entry.get("title")
            if hasattr(entry, "get")
            else ""
        )
    except Exception:
        title_value = ""

    record = {
        "feed": safe_text(feed_name, "Unbekannte Quelle"),
        "title": safe_text(title_value, "Unbekannter Eintrag"),
        "errorType": type(error).__name__,
        "error": safe_text(error, "Unbekannter Fehler"),
        "recordedAt": datetime.now().isoformat(),
    }

    AGGREGATE_ENTRY_ERRORS.append(record)

    print(
        "  [EINTRAG ÜBERSPRUNGEN] "
        f"{record['feed']} – {record['title']}: "
        f"{record['errorType']}: {record['error']}"
    )


def save_aggregate_error_report():
    payload = {
        "schemaVersion": 1,
        "generatedAt": datetime.now().isoformat(),
        "errorCount": len(AGGREGATE_ENTRY_ERRORS),
        "errors": AGGREGATE_ENTRY_ERRORS[-500:],
    }

    with open(
        "aggregate-errors.json",
        "w",
        encoding="utf-8",
    ) as report_file:
        json.dump(
            payload,
            report_file,
            ensure_ascii=False,
            indent=2,
        )

"""


def replace_once(
    text: str,
    old: str,
    new: str,
    label: str,
    changes: list[str],
    *,
    required: bool = True,
) -> str:
    count = text.count(old)

    if count == 0:
        if required:
            raise RuntimeError(
                f"Erwartetes Muster nicht gefunden: {label}"
            )
        return text

    if count > 1 and required:
        raise RuntimeError(
            f"Muster ist nicht eindeutig ({count} Treffer): {label}"
        )

    changes.append(label)
    return text.replace(old, new, 1)


def wrap_entry_loop(
    text: str,
    changes: list[str],
) -> str:
    lines = text.splitlines(keepends=True)

    loop_index = None
    checkpoint_index = None

    for index, line in enumerate(lines):
        if re.match(
            r"^\s{8}for entry in parsed\.entries\[:limit\]:\s*$",
            line.rstrip("\r\n"),
        ):
            loop_index = index
            break

    if loop_index is None:
        raise RuntimeError(
            "Die Feed-Eintragsschleife wurde nicht erkannt."
        )

    for index in range(loop_index + 1, len(lines)):
        if re.match(
            r"^\s{8}save_checkpoint\(\)\s*$",
            lines[index].rstrip("\r\n"),
        ):
            checkpoint_index = index
            break

    if checkpoint_index is None:
        raise RuntimeError(
            "Das Checkpoint-Ende der Eintragsschleife "
            "wurde nicht erkannt."
        )

    body = lines[loop_index + 1 : checkpoint_index]

    if any(
        "except Exception as entry_error" in line
        for line in body
    ):
        return text

    indented_body = [
        "    " + line
        if line.strip()
        else line
        for line in body
    ]

    wrapped = [
        lines[loop_index],
        "            try:\n",
        *indented_body,
        "            except Exception as entry_error:\n",
        "                log_feed_entry_error(\n",
        "                    feed_name,\n",
        "                    entry,\n",
        "                    entry_error,\n",
        "                )\n",
        "                continue\n",
    ]

    lines[loop_index:checkpoint_index] = wrapped
    changes.append("per_entry_exception_boundary")

    return "".join(lines)


def harden_source(source: str) -> tuple[str, list[str]]:
    if MARKER in source:
        return source, []

    changes: list[str] = []
    text = source

    helper_anchor = (
        "# =================================================================\n"
        "# 1. ARCHIV LADEN"
    )

    if helper_anchor not in text:
        raise RuntimeError(
            "Der Einfügepunkt vor ARCHIV LADEN wurde nicht gefunden."
        )

    text = text.replace(
        helper_anchor,
        HELPERS + "\n" + helper_anchor,
        1,
    )
    changes.append("safe_text_helpers")

    text = replace_once(
        text,
        """            for art in alter_stand:
                # Wir laden alle alten Artikel in den Arbeitsspeicher
                if "link" in art:
                    archiv_dict[art['link']] = art
                    titel_clean = art.get('title', '').lower().strip()
                    gesehene_titel.add(titel_clean)
""",
        """            for art in alter_stand:
                # Wir laden alle alten Artikel in den Arbeitsspeicher
                if not isinstance(art, dict):
                    continue

                link_value = safe_text(art.get("link"))

                if link_value:
                    archiv_dict[link_value] = art
                    titel_clean = safe_lower(
                        art.get("title"),
                    )

                    if titel_clean:
                        gesehene_titel.add(titel_clean)
""",
        "archive_value_normalization",
        changes,
    )

    text = replace_once(
        text,
        """    for feed in feeds:
        print(f"-> Portal: {feed['name']}...")
        parsed = None
""",
        """    for feed in feeds:
        if not isinstance(feed, dict):
            print("  [FEHLER] Ungültiger Quellen-Eintrag übersprungen.")
            continue

        feed_name = safe_text(
            feed.get("name"),
            "Unbekannte Quelle",
        )
        feed_url = safe_text(feed.get("url"))

        if not feed_url:
            print(
                f"  [FEHLER] {feed_name} besitzt keine gültige Feedadresse."
            )
            continue

        print(f"-> Portal: {feed_name}...")
        parsed = None
""",
        "feed_dictionary_normalization",
        changes,
    )

    text = text.replace("feed['url']", "feed_url")
    text = text.replace("feed['name']", "feed_name")
    changes.append("safe_feed_name_and_url")

    text = replace_once(
        text,
        """            link = entry.get('link', '')
            title = entry.get('title', 'Kein Titel')
            title_lower = title.lower().strip()
            author = entry.get('author', 'Unknown')
""",
        """            if not hasattr(entry, "get"):
                raise TypeError(
                    "Feed-Eintrag unterstützt keine get()-Abfragen."
                )

            link = safe_text(entry.get("link"))

            if not link:
                print(
                    f"  [EINTRAG ÜBERSPRUNGEN] "
                    f"{feed_name}: Link fehlt."
                )
                continue

            title = safe_text(
                entry.get("title"),
                "Kein Titel",
            )
            title_lower = safe_lower(title)
            author = safe_text(
                entry.get("author"),
                "Unknown",
            )
""",
        "entry_core_value_normalization",
        changes,
    )

    text = replace_once(
        text,
        """            pubDate = entry.get('published', entry.get('updated', datetime.now().isoformat()))
""",
        """            pubDate = safe_text(
                entry.get(
                    "published",
                    entry.get(
                        "updated",
                        datetime.now().isoformat(),
                    ),
                ),
                datetime.now().isoformat(),
            )
""",
        "publication_date_normalization",
        changes,
    )

    text = text.replace(
        "if enc.get('type', '').startswith('image/')",
        "if safe_text(enc.get('type')).startswith('image/')",
    )
    text = text.replace(
        "href = enc.get('href', '')",
        "href = safe_text(enc.get('href'))",
    )
    text = text.replace(
        "clean_text = full_text.strip()",
        "clean_text = safe_text(full_text)",
    )
    text = text.replace(
        'and title.lower() in clean_text.lower()',
        "and title_lower in clean_text.casefold()",
    )
    changes.append("secondary_value_normalization")

    text = wrap_entry_loop(text, changes)

    final_anchor = (
        'print(f"\\n>>> ERFOLG: Es wurden '
        '{radar_count} Radar-Termine gefunden! <<<")'
    )

    if final_anchor not in text:
        raise RuntimeError(
            "Der Abschluss der Aggregation wurde nicht erkannt."
        )

    text = text.replace(
        final_anchor,
        "save_aggregate_error_report()\n\n" + final_anchor,
        1,
    )
    changes.append("aggregate_error_report")

    ast.parse(text, filename="aggregate.py")
    return text, changes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the hardened aggregate.py.",
    )
    args = parser.parse_args()

    if not TARGET.is_file():
        print("FEHLER: aggregate.py fehlt.")
        return 1

    original = TARGET.read_text(encoding="utf-8")
    original_hash = hashlib.sha256(
        original.encode("utf-8")
    ).hexdigest()

    try:
        hardened, changes = harden_source(original)
    except Exception as error:
        payload = {
            "schemaVersion": 1,
            "generatedAt": datetime.now(
                timezone.utc
            ).isoformat(),
            "status": "failed",
            "applied": False,
            "error": str(error),
            "originalSha256": original_hash,
        }
        REPORT.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    changed = hardened != original

    if args.apply and changed:
        shutil.copy2(TARGET, BACKUP)
        TARGET.write_text(hardened, encoding="utf-8")

        try:
            py_compile.compile(
                str(TARGET),
                doraise=True,
            )
        except Exception:
            shutil.copy2(BACKUP, TARGET)
            raise

    payload = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(
            timezone.utc
        ).isoformat(),
        "status": "ok",
        "applied": bool(args.apply and changed),
        "alreadyHardened": not changed,
        "changes": changes,
        "originalSha256": original_hash,
        "resultSha256": hashlib.sha256(
            hardened.encode("utf-8")
        ).hexdigest(),
        "backup": (
            BACKUP.name
            if args.apply and changed
            else ""
        ),
    }

    REPORT.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
