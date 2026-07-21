#!/usr/bin/env python3
"""Update visible WRN release markers without replacing configuration files."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "release-version-report.json"


def patch_config() -> dict:
    path = ROOT / "config.js"

    if not path.is_file():
        return {
            "path": "config.js",
            "changed": False,
            "status": "missing",
        }

    text = path.read_text(encoding="utf-8")
    original = text

    text, version_count = re.subn(
        r"(version\s*:\s*['\"])[^'\"]+(['\"])",
        r"\g<1>1.7.23\g<2>",
        text,
        count=1,
    )

    text, build_count = re.subn(
        r"(build\s*:\s*['\"])[^'\"]+(['\"])",
        r"\g<1>2026.07.21-aggregator-hardening\g<2>",
        text,
        count=1,
    )

    text, stage_count = re.subn(
        r"(recoveryStage\s*:\s*)\d+",
        r"\g<1>12",
        text,
        count=1,
    )

    if text != original:
        path.write_text(text, encoding="utf-8")

    return {
        "path": "config.js",
        "changed": text != original,
        "versionUpdated": bool(version_count),
        "buildUpdated": bool(build_count),
        "recoveryStageUpdated": bool(stage_count),
    }


def patch_service_worker() -> dict:
    path = ROOT / "service-worker.js"

    if not path.is_file():
        return {
            "path": "service-worker.js",
            "changed": False,
            "status": "missing",
        }

    text = path.read_text(encoding="utf-8")
    original = text

    text = re.sub(
        r"wrn-app-v\d+\.\d+\.\d+",
        "wrn-app-v1.7.23",
        text,
    )
    text = re.sub(
        r"wrn-data-v\d+\.\d+\.\d+",
        "wrn-data-v1.7.23",
        text,
    )

    asset = "'./generated-podcasts.json'"

    if asset not in text:
        anchors = (
            "'./podcasts.json',",
            "'./radio-stations.json',",
            "'./generated-podcasts-report.json',",
        )

        inserted = False

        for anchor in anchors:
            if anchor in text:
                text = text.replace(
                    anchor,
                    anchor + "\n  " + asset + ",",
                    1,
                )
                inserted = True
                break

        if not inserted:
            # Do not guess a new asset array in an unknown worker.
            pass

    if text != original:
        path.write_text(text, encoding="utf-8")

    return {
        "path": "service-worker.js",
        "changed": text != original,
        "generatedPodcastsCached": asset in text,
        "appCacheVersion": (
            "wrn-app-v1.7.23" in text
        ),
        "dataCacheVersion": (
            "wrn-data-v1.7.23" in text
        ),
    }


def main() -> int:
    results = [
        patch_config(),
        patch_service_worker(),
    ]

    payload = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(
            timezone.utc
        ).isoformat(),
        "version": "1.7.23",
        "files": results,
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
