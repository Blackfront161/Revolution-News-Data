#!/usr/bin/env python3
"""Ensure generated-podcasts.json exists without discarding existing data."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "generated-podcasts.json"
REPORT = ROOT / "generated-podcasts-report.json"

CANDIDATES = (
    "generated-podcasts.json",
    "generated_podcasts.json",
    "podcast-feed.json",
    "ai-podcasts.json",
    "podcasts-generated.json",
    "generated-audio.json",
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_items(data: Any) -> list[Any] | None:
    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        return None

    for key in (
        "items",
        "podcasts",
        "episodes",
        "generated",
        "data",
    ):
        value = data.get(key)

        if isinstance(value, list):
            return value

    return None


def main() -> int:
    source = ""
    items: list[Any] | None = None
    errors: list[str] = []

    for filename in CANDIDATES:
        path = ROOT / filename

        if not path.is_file():
            continue

        try:
            candidate = extract_items(read_json(path))
        except Exception as error:
            errors.append(f"{filename}: {error}")
            continue

        if candidate is None:
            errors.append(
                f"{filename}: kein unterstütztes Listenformat"
            )
            continue

        items = candidate
        source = filename
        break

    if items is None:
        items = []
        source = "empty_fallback"

    OUTPUT.write_text(
        json.dumps(
            items,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    payload = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(
            timezone.utc
        ).isoformat(),
        "status": "ok",
        "source": source,
        "itemCount": len(items),
        "errors": errors,
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
