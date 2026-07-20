#!/usr/bin/env python3
"""Apply WRN 1.7.21 origin and workflow safety to the current repository."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parent
WORKFLOWS = ROOT / ".github" / "workflows"
REPORT = ROOT / "origin-safety-report.json"

HTML_FILES = (
    "recovery.html",
    "mobile-repair.html",
)

JS_FILES = (
    "app.js",
    "data-control.js",
)

SAFETY_SCRIPT = (
    '<script src="./wrn-origin-safety.js?v=1721"></script>'
)

OUTPUT_FILES = (
    "source-health.json",
    "source-health-report.json",
    "discovered-feeds.json",
)


def inject_safety_script(path: Path) -> bool:
    if not path.is_file():
        return False

    text = path.read_text(encoding="utf-8")

    if "wrn-origin-safety.js" in text:
        return False

    if "<head" in text and "</head>" in text:
        text = text.replace(
            "</head>",
            f"  {SAFETY_SCRIPT}\n</head>",
            1,
        )
    elif "<body" in text:
        index = text.find(">", text.find("<body")) + 1
        text = (
            text[:index]
            + "\n  "
            + SAFETY_SCRIPT
            + text[index:]
        )
    else:
        text = SAFETY_SCRIPT + "\n" + text

    path.write_text(text, encoding="utf-8")
    return True


def replace_destructive_patterns(path: Path) -> list[str]:
    if not path.is_file():
        return []

    text = path.read_text(encoding="utf-8")
    original = text
    changes: list[str] = []

    replacements = (
        (
            r"\b(?:window\.)?localStorage\.clear\(\s*\)",
            "window.WRNOriginSafety.clearOwnedStorage(window.localStorage)",
            "localStorage.clear",
        ),
        (
            r"\b(?:window\.)?sessionStorage\.clear\(\s*\)",
            "window.WRNOriginSafety.clearOwnedStorage(window.sessionStorage)",
            "sessionStorage.clear",
        ),
        (
            r"\b(?:window\.)?caches\.keys\(\s*\)",
            "window.WRNOriginSafety.getOwnedCacheNames()",
            "caches.keys",
        ),
        (
            r"\bnavigator\.serviceWorker\.getRegistrations\(\s*\)",
            "window.WRNOriginSafety.getOwnedServiceWorkerRegistrations()",
            "getRegistrations",
        ),
        (
            r"\b(?:window\.)?indexedDB\.databases\(\s*\)",
            "window.WRNOriginSafety.getOwnedDatabases()",
            "indexedDB.databases",
        ),
    )

    for pattern, replacement, label in replacements:
        text, count = re.subn(pattern, replacement, text)
        if count:
            changes.append(f"{label}:{count}")

    if text != original:
        marker = (
            "/* WRN 1.7.21: destructive browser operations "
            "are repository-scoped. */\n"
        )

        if marker not in text:
            text = marker + text

        path.write_text(text, encoding="utf-8")

    return changes


def workflow_is_writer(text: str) -> bool:
    return (
        "contents: write" in text
        or "git push" in text
        or "wrn-safe-push.sh" in text
    )


def set_common_concurrency(text: str) -> tuple[str, bool]:
    if re.search(
        r"(?m)^\s*group:\s*wrn-main-write\s*$",
        text,
    ):
        return text, False

    concurrency_pattern = re.compile(
        r"(?ms)^concurrency:\s*\n"
        r"(?:^[ \t]+.*\n?)+?(?=^[^\s]|\Z)"
    )

    replacement = (
        "concurrency:\n"
        "  group: wrn-main-write\n"
        "  cancel-in-progress: false\n\n"
    )

    if concurrency_pattern.search(text):
        return concurrency_pattern.sub(
            replacement,
            text,
            count=1,
        ), True

    jobs_match = re.search(r"(?m)^jobs:\s*$", text)

    if not jobs_match:
        return text, False

    index = jobs_match.start()

    return (
        text[:index]
        + replacement
        + text[index:],
        True,
    )


def find_commit_step_position(text: str) -> int | None:
    step_starts = [
        match.start()
        for match in re.finditer(
            r"(?m)^[ ]{6}- name:.*$",
            text,
        )
    ]

    for index, start in enumerate(step_starts):
        end = (
            step_starts[index + 1]
            if index + 1 < len(step_starts)
            else len(text)
        )
        block = text[start:end]

        if (
            "git commit" in block
            or "git config user.name" in block
            or "Änderungen speichern" in block
            or "Commit changes" in block
        ):
            return start

    return None


def add_update_news_staging(text: str) -> tuple[str, bool]:
    if "check_news_sources.py" not in text:
        return text, False

    if "WRN source status outputs" in text:
        return text, False

    position = find_commit_step_position(text)

    if position is None:
        return text, False

    step = """      - name: WRN source status outputs erfassen
        shell: bash
        run: |
          set -euo pipefail
          for file in \
            source-health.json \
            source-health-report.json \
            discovered-feeds.json
          do
            if [ -e "$file" ]; then
              git add "$file"
            fi
          done

"""

    return text[:position] + step + text[position:], True


def replace_simple_push(text: str) -> tuple[str, bool]:
    if "wrn-safe-push.sh" in text or "Push-Versuch" in text:
        return text, False

    if "git push" not in text:
        return text, False

    original = text

    text = re.sub(
        r"(?m)^(?P<indent>\s*)git pull --rebase.*$",
        r"\g<indent># Rebase wird von wrn-safe-push.sh ausgeführt.",
        text,
    )

    text = re.sub(
        r"(?m)^(?P<indent>\s*)git push(?:\s+.*)?$",
        r'\g<indent>bash wrn-safe-push.sh "${GITHUB_REF_NAME:-main}"',
        text,
    )

    return text, text != original


def harden_workflow(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")

    if not workflow_is_writer(text):
        return {
            "path": str(path.relative_to(ROOT)),
            "writer": False,
            "changed": False,
        }

    changed = False
    actions: list[str] = []

    text, did_change = set_common_concurrency(text)
    if did_change:
        changed = True
        actions.append("common_concurrency")

    text, did_change = add_update_news_staging(text)
    if did_change:
        changed = True
        actions.append("source_outputs_staging")

    text, did_change = replace_simple_push(text)
    if did_change:
        changed = True
        actions.append("safe_push_retry")

    if changed:
        path.write_text(text, encoding="utf-8")

    return {
        "path": str(path.relative_to(ROOT)),
        "writer": True,
        "changed": changed,
        "actions": actions,
    }


def main() -> int:
    changed_files: list[str] = []
    operation_changes: dict[str, list[str]] = {}

    for filename in HTML_FILES:
        path = ROOT / filename

        if inject_safety_script(path):
            changed_files.append(filename)

        replacements = replace_destructive_patterns(path)

        if replacements:
            operation_changes[filename] = replacements

    for filename in JS_FILES:
        path = ROOT / filename
        replacements = replace_destructive_patterns(path)

        if replacements:
            changed_files.append(filename)
            operation_changes[filename] = replacements

    workflow_results = []

    if WORKFLOWS.is_dir():
        for path in sorted(
            list(WORKFLOWS.glob("*.yml"))
            + list(WORKFLOWS.glob("*.yaml"))
        ):
            result = harden_workflow(path)
            workflow_results.append(result)

            if result.get("changed"):
                changed_files.append(
                    str(path.relative_to(ROOT))
                )

    report = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(
            timezone.utc
        ).isoformat(),
        "version": "1.7.21",
        "scope": "/Revolution-News-Data/",
        "cachePrefix": "wrn-",
        "storagePrefixes": [
            "wrn_",
            "wrn-",
            "wrn:",
            "wrnCamelCase",
        ],
        "changedFiles": sorted(set(changed_files)),
        "operationChanges": operation_changes,
        "workflows": workflow_results,
        "expectedSourceOutputs": list(OUTPUT_FILES),
    }

    REPORT.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
