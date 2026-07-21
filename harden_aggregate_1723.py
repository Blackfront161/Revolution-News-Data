#!/usr/bin/env python3
# WRN 1.7.23b – tolerant aggregator hardener.

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
BACKUP = ROOT / "aggregate.py.pre-1723b.bak"
REPORT = ROOT / "aggregate-hardening-report.json"
MARKER = "# WRN 1.7.23 ENTRY SAFETY"


HELPERS = r'''
# WRN 1.7.23 ENTRY SAFETY
AGGREGATE_ENTRY_ERRORS = []


def safe_text(value, fallback=""):
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

'''


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def leading_spaces(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def is_name(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


def find_feed_loop(tree: ast.AST) -> ast.For:
    matches = [
        node
        for node in ast.walk(tree)
        if (
            isinstance(node, ast.For)
            and is_name(node.target, "feed")
            and is_name(node.iter, "feeds")
        )
    ]

    if len(matches) != 1:
        raise RuntimeError(
            "Feed-Schleife nicht eindeutig erkannt: "
            f"{len(matches)} Treffer."
        )

    return matches[0]


def entry_iter_is_parsed_entries(node: ast.AST) -> bool:
    candidate = node.value if isinstance(node, ast.Subscript) else node

    return (
        isinstance(candidate, ast.Attribute)
        and candidate.attr == "entries"
        and is_name(candidate.value, "parsed")
    )


def find_entry_loop(tree: ast.AST) -> ast.For:
    matches = [
        node
        for node in ast.walk(tree)
        if (
            isinstance(node, ast.For)
            and is_name(node.target, "entry")
            and entry_iter_is_parsed_entries(node.iter)
        )
    ]

    if len(matches) != 1:
        raise RuntimeError(
            "Artikelschleife nicht eindeutig erkannt: "
            f"{len(matches)} Treffer."
        )

    return matches[0]


def insert_helpers(source: str) -> tuple[str, str]:
    tree = ast.parse(source, filename="aggregate.py")
    imports = [
        node
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]

    if not imports:
        raise RuntimeError(
            "Keine Importsektion in aggregate.py erkannt."
        )

    insert_after = max(
        int(node.end_lineno or node.lineno)
        for node in imports
    )

    lines = source.splitlines(keepends=True)
    lines.insert(insert_after, "\n" + HELPERS + "\n")

    return "".join(lines), "safe_text_helpers"


def insert_feed_guard(source: str) -> tuple[str, str]:
    tree = ast.parse(source, filename="aggregate.py")
    loop = find_feed_loop(tree)
    lines = source.splitlines(keepends=True)

    loop_index = loop.lineno - 1
    body_index = loop_index + 1
    body_indent = leading_spaces(lines[loop_index]) + 4
    indent = " " * body_indent

    window = "".join(
        lines[body_index:min(body_index + 20, len(lines))]
    )

    if "feed_name = safe_text(" in window:
        return source, "feed_guard_already_present"

    guard = [
        f"{indent}if not isinstance(feed, dict):\n",
        f"{indent}    print(\n",
        f"{indent}        \"  [FEHLER] Ungültiger Quellen-Eintrag \"\n",
        f"{indent}        \"übersprungen.\"\n",
        f"{indent}    )\n",
        f"{indent}    continue\n",
        "\n",
        f"{indent}feed_name = safe_text(\n",
        f"{indent}    feed.get(\"name\"),\n",
        f"{indent}    \"Unbekannte Quelle\",\n",
        f"{indent})\n",
        "\n",
    ]

    lines[body_index:body_index] = guard
    return "".join(lines), "feed_guard_inserted"


def tolerant_replacements(
    source: str,
) -> tuple[str, list[str], list[str]]:
    changes = []
    skipped = []
    text = source

    replacements = (
        (
            r"feed\[['\"]name['\"]\]",
            "feed_name",
            "feed_name_references",
        ),
        (
            r"entry\.get\(\s*['\"]link['\"]\s*,\s*['\"]['\"]\s*\)"
            r"\.strip\(\)",
            'safe_text(entry.get("link"))',
            "entry_link",
        ),
        (
            r"entry\.get\(\s*['\"]title['\"]\s*,\s*"
            r"['\"]Kein Titel['\"]\s*\)",
            'safe_text(entry.get("title"), "Kein Titel")',
            "entry_title",
        ),
        (
            r"entry\.get\(\s*['\"]author['\"]\s*,\s*"
            r"['\"]Unknown['\"]\s*\)",
            'safe_text(entry.get("author"), "Unknown")',
            "entry_author",
        ),
        (
            r"\bauthor\.lower\(\)",
            "safe_lower(author)",
            "author_lower",
        ),
        (
            r"href\s*=\s*enc\.get\(\s*['\"]href['\"]\s*,\s*"
            r"['\"]['\"]\s*\)",
            'href = safe_text(enc.get("href"))',
            "enclosure_href",
        ),
        (
            r"enc\.get\(\s*['\"]type['\"]\s*,\s*['\"]['\"]\s*\)"
            r"\.startswith\(",
            'safe_text(enc.get("type")).startswith(',
            "enclosure_type",
        ),
        (
            r"clean_text\s*=\s*full_text\.strip\(\)",
            "clean_text = safe_text(full_text)",
            "clean_text",
        ),
        (
            r"\bclean_text\.lower\(\)",
            "clean_text.casefold()",
            "clean_text_casefold",
        ),
        (
            r"\bfeed_name\.lower\(\)",
            "safe_lower(feed_name)",
            "feed_name_lower",
        ),
        (
            r"\btitle\.lower\(\)",
            "safe_lower(title)",
            "title_lower",
        ),
    )

    for pattern, replacement, label in replacements:
        text, count = re.subn(pattern, replacement, text)

        if count:
            changes.append(f"{label}:{count}")
        else:
            skipped.append(label)

    return text, changes, skipped


def wrap_entry_loop(source: str) -> tuple[str, str]:
    tree = ast.parse(source, filename="aggregate.py")
    loop = find_entry_loop(tree)

    if not loop.body:
        raise RuntimeError(
            "Artikelschleife besitzt keinen Inhalt."
        )

    lines = source.splitlines(keepends=True)
    loop_index = loop.lineno - 1
    body_start = loop_index + 1
    loop_end = int(loop.end_lineno or loop.lineno)
    body_lines = lines[body_start:loop_end]

    if any(
        "except Exception as entry_error" in line
        for line in body_lines
    ):
        return source, "entry_boundary_already_present"

    base_indent = leading_spaces(lines[loop_index])
    body_indent = base_indent + 4
    nested_indent = body_indent + 4
    indent = " " * body_indent
    nested = " " * nested_indent

    shifted_body = [
        "    " + line
        if line.strip()
        else line
        for line in body_lines
    ]

    replacement = [
        lines[loop_index],
        f"{indent}try:\n",
        f"{nested}if not hasattr(entry, \"get\"):\n",
        f"{nested}    raise TypeError(\n",
        f"{nested}        \"Feed-Eintrag unterstützt keine \"\n",
        f"{nested}        \"get()-Abfragen.\"\n",
        f"{nested}    )\n",
        *shifted_body,
        f"{indent}except Exception as entry_error:\n",
        f"{nested}log_feed_entry_error(\n",
        f"{nested}    feed_name,\n",
        f"{nested}    entry,\n",
        f"{nested}    entry_error,\n",
        f"{nested})\n",
        f"{nested}continue\n",
    ]

    lines[loop_index:loop_end] = replacement
    return "".join(lines), "per_entry_exception_boundary"


def insert_report_call(source: str) -> tuple[str, str]:
    if re.search(
        r"(?m)^\s*save_aggregate_error_report\(\)\s*$",
        source,
    ):
        return source, "error_report_call_already_present"

    lines = source.splitlines(keepends=True)

    for index in range(len(lines) - 1, -1, -1):
        line = lines[index]

        if "ERFOLG" in line and "radar_count" in line:
            indent = " " * leading_spaces(line)
            lines.insert(
                index,
                f"{indent}save_aggregate_error_report()\n\n",
            )
            return "".join(lines), "aggregate_error_report"

    tree = ast.parse(source, filename="aggregate.py")
    checkpoints = []

    for node in tree.body:
        if not isinstance(node, ast.Expr):
            continue

        call = node.value

        if (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id == "save_checkpoint"
        ):
            checkpoints.append(node)

    if checkpoints:
        node = checkpoints[-1]
        insertion = int(node.end_lineno or node.lineno)
        lines.insert(
            insertion,
            "\nsave_aggregate_error_report()\n",
        )
        return "".join(lines), "aggregate_error_report_fallback"

    raise RuntimeError(
        "Kein sicherer Einfügepunkt für den Fehlerbericht erkannt."
    )


def harden_source(
    source: str,
) -> tuple[str, list[str], list[str]]:
    if MARKER in source:
        ast.parse(source, filename="aggregate.py")
        return source, [], []

    changes = []
    skipped = []

    text, label = insert_helpers(source)
    changes.append(label)

    text, label = insert_feed_guard(text)
    changes.append(label)

    text, found, missing = tolerant_replacements(text)
    changes.extend(found)
    skipped.extend(missing)

    text, label = wrap_entry_loop(text)
    changes.append(label)

    text, label = insert_report_call(text)
    changes.append(label)

    ast.parse(text, filename="aggregate.py")
    return text, changes, skipped


def write_report(payload: dict) -> None:
    REPORT.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not TARGET.is_file():
        print("FEHLER: aggregate.py fehlt.")
        return 1

    original = TARGET.read_text(encoding="utf-8")
    original_hash = sha256_text(original)

    try:
        hardened, changes, skipped = harden_source(original)
    except Exception as error:
        payload = {
            "schemaVersion": 3,
            "generatedAt": datetime.now(
                timezone.utc
            ).isoformat(),
            "version": "1.7.23b",
            "status": "failed",
            "applied": False,
            "error": str(error),
            "originalSha256": original_hash,
        }
        write_report(payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    changed = hardened != original

    if args.apply and changed:
        shutil.copy2(TARGET, BACKUP)
        TARGET.write_text(hardened, encoding="utf-8")

        try:
            py_compile.compile(str(TARGET), doraise=True)
        except Exception:
            shutil.copy2(BACKUP, TARGET)
            raise

    payload = {
        "schemaVersion": 3,
        "generatedAt": datetime.now(
            timezone.utc
        ).isoformat(),
        "version": "1.7.23b",
        "status": "ok",
        "applied": bool(args.apply and changed),
        "alreadyHardened": not changed,
        "changes": changes,
        "optionalPatternsNotFound": skipped,
        "originalSha256": original_hash,
        "resultSha256": sha256_text(hardened),
        "backup": BACKUP.name if args.apply and changed else "",
        "feedUrlStructure": "not_required",
        "archiveLogic": "preserved",
        "sourceCatalogue": "preserved",
    }

    write_report(payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
