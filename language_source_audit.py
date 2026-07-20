#!/usr/bin/env python3
"""Audit language coverage of active and approved sources."""

from __future__ import annotations

import ast
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REGISTRY = ROOT / "multilingual-source-registry.json"
AGGREGATE = ROOT / "aggregate.py"
OUTPUT = ROOT / "language-source-audit.json"


def read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def aggregate_rows() -> list[dict[str, Any]]:
    if not AGGREGATE.exists():
        return []

    tree = ast.parse(AGGREGATE.read_text(encoding="utf-8"))
    result = []

    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue

        value_node = node.value

        try:
            value = ast.literal_eval(value_node)
        except Exception:
            continue

        if not isinstance(value, dict):
            continue

        for category, rows in value.items():
            if not isinstance(rows, list):
                continue

            for item in rows:
                if not isinstance(item, dict):
                    continue

                result.append({
                    "name": item.get("name", "Unbekannt"),
                    "language": (
                        item.get("language")
                        or item.get("lang")
                        or item.get("sprache")
                        or "und"
                    ),
                    "category": str(category),
                    "url": (
                        item.get("url")
                        or item.get("feedUrl")
                        or item.get("feed")
                        or ""
                    )
                })

        if result:
            break

    return result


def main() -> int:
    active = aggregate_rows()
    registry = read_json(REGISTRY, {})
    approved = registry.get("sources", [])

    active_counts = Counter(
        str(item.get("language", "und")).split("-")[0].lower()
        for item in active
    )

    approved_counts = Counter()

    for item in approved:
        for language in item.get("languages", ["und"]):
            approved_counts[str(language).split("-")[0].lower()] += 1

    payload = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "activeSourceRows": len(active),
        "activeLanguages": dict(sorted(active_counts.items())),
        "approvedLanguages": dict(sorted(approved_counts.items())),
        "approvedSources": approved,
        "note": (
            "Mehrfachkategorien zählen als mehrere Quellenzeilen; "
            "sie werden beim Abruf über die Feed-URL dedupliziert."
        )
    }

    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
