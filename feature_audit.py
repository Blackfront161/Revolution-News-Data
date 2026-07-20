#!/usr/bin/env python3
"""Inventory World Revolution News features after the emergency recovery.

The audit never deletes files and does not restore unknown old copies.
It records whether expected feature files exist and whether they are cached
or loaded by the current recovery configuration.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "feature-audit.json"

GROUPS: dict[str, dict[str, list[str]]] = {
    "core": {
        "critical": [
            "index.html",
            "styles.css",
            "app.js",
            "config.js",
            "service-worker.js",
            "manifest.json",
        ],
        "optional": [
            "icon.svg",
            "app-background.webp",
            "wrn-logo.webp",
            "wrn-future-header.webp",
        ],
    },
    "intro_and_navigation": {
        "critical": [
            "intro-screen.js",
            "intro-screen.css",
            "release-1.5-nav.js",
            "release-1.5-nav.css",
        ],
        "optional": [
            "release-1.4.js",
            "release-1.4.css",
            "interface-qol.css",
            "wrn-header.js",
            "wrn-header.css",
        ],
    },
    "reading_and_accessibility": {
        "critical": [],
        "optional": [
            "reading-state.js",
            "accessibility.js",
            "source-profiles.js",
            "translation-tools.js",
            "typography.js",
            "typography.css",
            "wrn-i18n.js",
            "language-qol.js",
            "language-status.js",
        ],
    },
    "privacy_and_storage": {
        "critical": [],
        "optional": [
            "offline-db.js",
            "data-control.js",
            "status-center.js",
        ],
    },
    "briefing_and_summaries": {
        "critical": [],
        "optional": [
            "briefing.js",
            "briefing.css",
            "briefing-loader.js",
            "briefing-loader.css",
            "article-summary-core.js",
            "article-summary.js",
            "article-summary.css",
        ],
    },
    "audio": {
        "critical": [],
        "optional": [
            "media-player.js",
            "audio-tools.js",
            "audio-hub.js",
            "audio-player-fixes.js",
            "audio-catalog.js",
            "audio-catalog.css",
            "audio-tab.js",
            "audio-tab.css",
            "audio-reliability.js",
            "audio-reliability.css",
        ],
    },
    "translation": {
        "critical": [],
        "optional": [
            "shared-translation-client.js",
            "shared-translation-status.js",
            "shared-translation-status.css",
            "translation-dialog-l10n.js",
        ],
    },
    "diagnostics_and_recovery": {
        "critical": [
            "app-safety.js",
            "normalize_source_health.py",
            "check_news_sources.py",
        ],
        "optional": [
            "app-diagnostics.js",
            "app-diagnostics.css",
            "source-verification.js",
            "source-verification.css",
            "runtime-selftest.js",
            "runtime-selftest.css",
            "recovery-audit.js",
            "recovery-audit.css",
            "language-source-status.js",
            "language-source-status.css",
            "zine-designer.js",
            "zine-designer.css",
        ],
    },
}

LAZY_ALLOWED = {
    "briefing.js",
    "briefing.css",
    "article-summary-core.js",
    "article-summary.js",
    "article-summary.css",
    "media-player.js",
    "audio-tools.js",
    "audio-hub.js",
    "audio-player-fixes.js",
    "audio-catalog.js",
    "audio-catalog.css",
    "app-diagnostics.js",
    "app-diagnostics.css",
}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def audit_file(
    filename: str,
    *,
    critical: bool,
    config_text: str,
    worker_text: str,
) -> dict[str, Any]:
    path = ROOT / filename
    present = path.is_file()
    cached = filename in worker_text
    loaded = filename in config_text

    if not present:
        status = "missing"
    elif loaded:
        status = "active_or_loader"
    elif filename in LAZY_ALLOWED:
        status = "present_lazy"
    elif cached:
        status = "present_cached"
    else:
        status = "present_unreferenced"

    return {
        "file": filename,
        "critical": critical,
        "present": present,
        "cached": cached,
        "loadedByConfig": loaded,
        "status": status,
        "sizeBytes": path.stat().st_size if present else 0,
    }


def main() -> int:
    config_text = read_text(ROOT / "config.js")
    worker_text = read_text(ROOT / "service-worker.js")

    groups: dict[str, Any] = {}
    critical_missing: list[str] = []
    optional_missing: list[str] = []

    for group_name, definitions in GROUPS.items():
        rows: list[dict[str, Any]] = []

        for critical, files in (
            (True, definitions.get("critical", [])),
            (False, definitions.get("optional", [])),
        ):
            for filename in files:
                row = audit_file(
                    filename,
                    critical=critical,
                    config_text=config_text,
                    worker_text=worker_text,
                )
                rows.append(row)

                if not row["present"]:
                    (
                        critical_missing
                        if critical
                        else optional_missing
                    ).append(filename)

        groups[group_name] = {
            "total": len(rows),
            "present": sum(row["present"] for row in rows),
            "missing": sum(not row["present"] for row in rows),
            "files": rows,
        }

    payload = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "version": "1.7.19",
        "summary": {
            "groups": len(groups),
            "criticalMissing": len(critical_missing),
            "optionalMissing": len(optional_missing),
            "criticalMissingFiles": critical_missing,
            "optionalMissingFiles": optional_missing,
        },
        "groups": groups,
        "interpretation": {
            "active_or_loader":
                "Datei vorhanden und in config.js direkt oder als Loader referenziert.",
            "present_lazy":
                "Datei vorhanden; absichtlich erst bei Bedarf zu laden.",
            "present_cached":
                "Datei vorhanden und im Offline-Cache, aber nicht beim Start aktiv.",
            "present_unreferenced":
                "Datei vorhanden, derzeit jedoch nicht referenziert.",
            "missing":
                "Datei fehlt im Repository.",
        },
    }

    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))

    if critical_missing:
        print("KRITISCHE DATEIEN FEHLEN:")
        for filename in critical_missing:
            print(f"- {filename}")
        return 1

    print("Kritische App-Dateien vollständig.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
