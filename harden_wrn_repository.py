#!/usr/bin/env python3
"""WRN 1.7.21c: protect runtime data without modifying workflow files.

GitHub's built-in Actions token may write ordinary repository content, but
must not be used to create or update files in .github/workflows without a
separate token carrying workflow permissions.

This script therefore:
- patches only runtime pages and JavaScript files;
- audits workflows without changing them;
- writes origin-safety-report.json;
- never writes beneath .github/workflows.
"""

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
    '<script src="./wrn-origin-safety.js?v=1721c"></script>'
)

EXPECTED_SOURCE_OUTPUTS = (
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

    if "</head>" in text:
        text = text.replace(
            "</head>",
            f"  {SAFETY_SCRIPT}\n</head>",
            1,
        )
    elif "<body" in text:
        body_start = text.find("<body")
        insertion = text.find(">", body_start) + 1
        text = (
            text[:insertion]
            + "\n  "
            + SAFETY_SCRIPT
            + text[insertion:]
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
            (
                "window.WRNOriginSafety"
                ".clearOwnedStorage(window.localStorage)"
            ),
            "localStorage.clear",
        ),
        (
            r"\b(?:window\.)?sessionStorage\.clear\(\s*\)",
            (
                "window.WRNOriginSafety"
                ".clearOwnedStorage(window.sessionStorage)"
            ),
            "sessionStorage.clear",
        ),
        (
            r"\b(?:window\.)?caches\.keys\(\s*\)",
            (
                "window.WRNOriginSafety"
                ".getOwnedCacheNames()"
            ),
            "caches.keys",
        ),
        (
            (
                r"\bnavigator\.serviceWorker"
                r"\.getRegistrations\(\s*\)"
            ),
            (
                "window.WRNOriginSafety"
                ".getOwnedServiceWorkerRegistrations()"
            ),
            "serviceWorker.getRegistrations",
        ),
        (
            r"\b(?:window\.)?indexedDB\.databases\(\s*\)",
            (
                "window.WRNOriginSafety"
                ".getOwnedDatabases()"
            ),
            "indexedDB.databases",
        ),
    )

    for pattern, replacement, label in replacements:
        text, count = re.subn(pattern, replacement, text)

        if count:
            changes.append(f"{label}:{count}")

    if text != original:
        marker = (
            "/* WRN 1.7.21c: browser deletion is "
            "repository-scoped. */\n"
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


def audit_workflow(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    writer = workflow_is_writer(text)

    checks: dict[str, Any] = {
        "writer": writer,
        "commonConcurrency": (
            "group: wrn-main-write" in text
            if writer
            else None
        ),
        "safePush": (
            (
                "wrn-safe-push.sh" in text
                or "Push-Versuch" in text
            )
            if writer
            else None
        ),
        "runsNewsSourceCheck": (
            "check_news_sources.py" in text
        ),
    }

    if checks["runsNewsSourceCheck"]:
        checks["stagesSourceHealth"] = (
            "source-health.json" in text
        )
        checks["stagesSourceHealthReport"] = (
            "source-health-report.json" in text
        )
        checks["stagesDiscoveredFeeds"] = (
            "discovered-feeds.json" in text
        )

    warnings: list[str] = []

    if writer and not checks["commonConcurrency"]:
        warnings.append("missing_wrn_main_write")

    if writer and not checks["safePush"]:
        warnings.append("missing_safe_push")

    if checks["runsNewsSourceCheck"]:
        if not checks.get("stagesSourceHealthReport"):
            warnings.append(
                "missing_source_health_report_staging"
            )

        if not checks.get("stagesDiscoveredFeeds"):
            warnings.append(
                "missing_discovered_feeds_staging"
            )

    return {
        "path": str(path.relative_to(ROOT)),
        "checks": checks,
        "warnings": warnings,
        "modified": False,
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

    workflow_reports: list[dict[str, Any]] = []

    if WORKFLOWS.is_dir():
        paths = sorted(
            list(WORKFLOWS.glob("*.yml"))
            + list(WORKFLOWS.glob("*.yaml"))
        )

        workflow_reports = [
            audit_workflow(path)
            for path in paths
        ]

    warning_count = sum(
        len(item["warnings"])
        for item in workflow_reports
    )

    report = {
        "schemaVersion": 2,
        "generatedAt": datetime.now(
            timezone.utc
        ).isoformat(),
        "version": "1.7.21c",
        "mode": "runtime_only",
        "workflowModificationEnabled": False,
        "scope": "/Revolution-News-Data/",
        "cachePrefix": "wrn-",
        "changedRuntimeFiles": sorted(
            set(changed_files)
        ),
        "operationChanges": operation_changes,
        "workflowAudit": workflow_reports,
        "workflowWarningCount": warning_count,
        "expectedSourceOutputs": list(
            EXPECTED_SOURCE_OUTPUTS
        ),
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
    print(
        "Workflow-Dateien wurden nur geprüft, "
        "nicht verändert."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
