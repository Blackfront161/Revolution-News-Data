#!/usr/bin/env python3
"""Semantically harden the current aggregate.py.

WRN 1.7.23a no longer requires an exact historic archive block. It locates
feed and entry loops through Python's AST and changes only required runtime
statements. The complete source catalogue and category logic remain intact.
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
BACKUP = ROOT / "aggregate.py.pre-1723a.bak"
REPORT = ROOT / "aggregate-hardening-report.json"
MARKER = "# WRN 1.7.23 ENTRY SAFETY"


HELPERS = r'''
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

'''


def source_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def insert_helpers_after_imports(source: str) -> tuple[str, str]:
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

    insertion_line = max(
        int(node.end_lineno or node.lineno)
        for node in imports
    )

    lines = source.splitlines(keepends=True)
    lines.insert(insertion_line, "\n" + HELPERS + "\n")

    return "".join(lines), "safe_text_helpers"


def is_name(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


def find_feed_loop(tree: ast.AST) -> ast.For:
    candidates: list[ast.For] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.For):
            continue

        if not is_name(node.target, "feed"):
            continue

        if is_name(node.iter, "feeds"):
            candidates.append(node)

    if len(candidates) != 1:
        raise RuntimeError(
            "Feed-Schleife nicht eindeutig erkannt: "
            f"{len(candidates)} Treffer."
        )

    return candidates[0]


def is_parsed_entries_slice(node: ast.AST) -> bool:
    if not isinstance(node, ast.Subscript):
        return False

    value = node.value

    return (
        isinstance(value, ast.Attribute)
        and value.attr == "entries"
        and is_name(value.value, "parsed")
    )


def find_entry_loop(tree: ast.AST) -> ast.For:
    candidates: list[ast.For] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.For):
            continue

        if not is_name(node.target, "entry"):
            continue

        if is_parsed_entries_slice(node.iter):
            candidates.append(node)

    if len(candidates) != 1:
        raise RuntimeError(
            "Artikelschleife nicht eindeutig erkannt: "
            f"{len(candidates)} Treffer."
        )

    return candidates[0]


def leading_spaces(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def patch_feed_loop(source: str) -> tuple[str, str]:
    tree = ast.parse(source, filename="aggregate.py")
    loop = find_feed_loop(tree)
    lines = source.splitlines(keepends=True)

    start = loop.lineno - 1
    body_start = start + 1
    body_indent = leading_spaces(lines[start]) + 4
    scan_end = min(len(lines), body_start + 20)
    replace_end = None

    for index in range(body_start, scan_end):
        stripped = lines[index].strip()

        if re.match(r"feed_url\s*=", stripped):
            replace_end = index + 1
            break

    if replace_end is None:
        raise RuntimeError(
            "feed_url-Zuweisung direkt nach der Feed-Schleife "
            "nicht erkannt."
        )

    indent = " " * body_indent

    replacement = [
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
        f"{indent}feed_url = safe_text(feed.get(\"url\"))\n",
        "\n",
        f"{indent}if not feed_url:\n",
        f"{indent}    print(\n",
        f"{indent}        f\"  [FEHLER] {{feed_name}} besitzt keine \"\n",
        f"{indent}        \"gültige Feedadresse.\"\n",
        f"{indent}    )\n",
        f"{indent}    continue\n",
        "\n",
        f"{indent}print(f\"-> Portal: {{feed_name}}...\")\n",
    ]

    lines[body_start:replace_end] = replacement
    return "".join(lines), "feed_value_normalization"


def replace_runtime_expressions(
    source: str,
) -> tuple[str, list[str]]:
    changes: list[str] = []
    text = source

    replacements = (
        (
            r"feed\[['\"]name['\"]\]",
            "feed_name",
            "safe_feed_name",
        ),
        (
            r"entry\.get\(\s*['\"]link['\"]\s*,\s*['\"]['\"]\s*\)"
            r"\.strip\(\)",
            'safe_text(entry.get("link"))',
            "safe_entry_link",
        ),
        (
            r"entry\.get\(\s*['\"]title['\"]\s*,\s*"
            r"['\"]Kein Titel['\"]\s*\)",
            'safe_text(entry.get("title"), "Kein Titel")',
            "safe_entry_title",
        ),
        (
            r"entry\.get\(\s*['\"]author['\"]\s*,\s*"
            r"['\"]Unknown['\"]\s*\)",
            'safe_text(entry.get("author"), "Unknown")',
            "safe_entry_author",
        ),
        (
            r"\bauthor\.lower\(\)",
            "safe_lower(author)",
            "safe_author_lower",
        ),
        (
            r"enc\.get\(\s*['\"]type['\"]\s*,\s*['\"]['\"]\s*\)"
            r"\.startswith\(",
            'safe_text(enc.get("type")).startswith(',
            "safe_enclosure_type",
        ),
        (
            r"href\s*=\s*enc\.get\(\s*['\"]href['\"]\s*,\s*"
            r"['\"]['\"]\s*\)",
            'href = safe_text(enc.get("href"))',
            "safe_enclosure_href",
        ),
        (
            r"clean_text\s*=\s*full_text\.strip\(\)",
            "clean_text = safe_text(full_text)",
            "safe_clean_text",
        ),
        (
            r"\bclean_text\.lower\(\)",
            "clean_text.casefold()",
            "safe_clean_text_casefold",
        ),
        (
            r"\btitle\.lower\(\)",
            "title_lower",
            "safe_title_comparison",
        ),
        (
            r"\bfeed_name\.lower\(\)",
            "safe_lower(feed_name)",
            "safe_feed_name_lower",
        ),
    )

    for pattern, replacement, label in replacements:
        text, count = re.subn(pattern, replacement, text)

        if count:
            changes.append(f"{label}:{count}")

    publication_pattern = re.compile(
        r"(?m)^(?P<indent>\s*)pubDate\s*=\s*"
        r"entry\.get\(\s*['\"]published['\"]\s*,\s*"
        r"entry\.get\(\s*['\"]updated['\"]\s*,\s*"
        r"datetime\.now\(\)\.isoformat\(\)\s*\)\s*\)\s*$"
    )

    def publication_replacement(match: re.Match[str]) -> str:
        indent = match.group("indent")
        return "\n".join(
            [
                f"{indent}pubDate = safe_text(",
                f"{indent}    entry.get(",
                f'{indent}        "published",',
                f"{indent}        entry.get(",
                f'{indent}            "updated",',
                f"{indent}            datetime.now().isoformat(),",
                f"{indent}        ),",
                f"{indent}    ),",
                f"{indent}    datetime.now().isoformat(),",
                f"{indent})",
            ]
        )

    text, count = publication_pattern.subn(
        publication_replacement,
        text,
    )

    if count:
        changes.append(f"safe_publication_date:{count}")

    return text, changes


def wrap_entry_loop(source: str) -> tuple[str, str]:
    tree = ast.parse(source, filename="aggregate.py")
    loop = find_entry_loop(tree)

    if not loop.body:
        raise RuntimeError(
            "Artikelschleife besitzt keinen Inhalt."
        )

    lines = source.splitlines(keepends=True)
    start = loop.lineno - 1
    end = int(loop.end_lineno or loop.lineno)
    body_start = start + 1
    body_lines = lines[body_start:end]

    if any(
        "except Exception as entry_error" in line
        for line in body_lines
    ):
        return source, "per_entry_boundary_already_present"

    base_indent = leading_spaces(lines[start])
    body_indent = base_indent + 4
    nested_indent = body_indent + 4
    indent = " " * body_indent
    nested = " " * nested_indent

    wrapped_body = [
        "    " + line
        if line.strip()
        else line
        for line in body_lines
    ]

    replacement = [
        lines[start],
        f"{indent}try:\n",
        f'{nested}if not hasattr(entry, "get"):\n',
        f"{nested}    raise TypeError(\n",
        f'{nested}        "Feed-Eintrag unterstützt keine "\n',
        f'{nested}        "get()-Abfragen."\n',
        f"{nested}    )\n",
        *wrapped_body,
        f"{indent}except Exception as entry_error:\n",
        f"{nested}log_feed_entry_error(\n",
        f"{nested}    feed_name,\n",
        f"{nested}    entry,\n",
        f"{nested}    entry_error,\n",
        f"{nested})\n",
        f"{nested}continue\n",
    ]

    lines[start:end] = replacement
    return "".join(lines), "per_entry_exception_boundary"


def insert_error_report_call(source: str) -> tuple[str, str]:
    if re.search(
        r"(?m)^\s*save_aggregate_error_report\(\)\s*$",
        source,
    ):
        return source, "error_report_call_already_present"

    lines = source.splitlines(keepends=True)

    for index, line in enumerate(lines):
        if (
            ">>> ERFOLG: Es wurden " in line
            and "radar_count" in line
        ):
            indent = " " * leading_spaces(line)
            lines.insert(
                index,
                f"{indent}save_aggregate_error_report()\n\n",
            )
            return "".join(lines), "aggregate_error_report"

    raise RuntimeError(
        "Abschlussmeldung der Aggregation nicht erkannt."
    )


def harden_source(source: str) -> tuple[str, list[str]]:
    if MARKER in source:
        ast.parse(source, filename="aggregate.py")
        return source, []

    changes: list[str] = []

    text, label = insert_helpers_after_imports(source)
    changes.append(label)

    text, label = patch_feed_loop(text)
    changes.append(label)

    text, expression_changes = replace_runtime_expressions(text)
    changes.extend(expression_changes)

    text, label = wrap_entry_loop(text)
    changes.append(label)

    text, label = insert_error_report_call(text)
    changes.append(label)

    ast.parse(text, filename="aggregate.py")
    return text, changes


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
    original_hash = source_hash(original)

    try:
        hardened, changes = harden_source(original)
    except Exception as error:
        payload = {
            "schemaVersion": 2,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "version": "1.7.23a",
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
        "schemaVersion": 2,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "version": "1.7.23a",
        "status": "ok",
        "applied": bool(args.apply and changed),
        "alreadyHardened": not changed,
        "changes": changes,
        "originalSha256": original_hash,
        "resultSha256": source_hash(hardened),
        "backup": BACKUP.name if args.apply and changed else "",
        "archiveLogic": "preserved",
        "sourceCatalogue": "preserved",
    }

    write_report(payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
