#!/usr/bin/env python3
"""Conservative WRN repository cleanup.

Automatic removal is limited to:
- tracked Python bytecode and __pycache__ content;
- root workflow copies whose bytes are identical to the active file under
  .github/workflows;
- scripts/wrn-safe-push.sh when it is identical to root wrn-safe-push.sh.

Different files are only reported, never deleted automatically.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "repository-cleanup-report.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_lines(*arguments: str) -> list[str]:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT}", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    return [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    ]


def tracked_files() -> list[str]:
    try:
        return git_lines("ls-files")
    except Exception:
        return []


def remove_tracked(path: Path) -> None:
    subprocess.run(
        ["git", "-c", f"safe.directory={ROOT}", "rm", "-f", "--", str(path.relative_to(ROOT))],
        cwd=ROOT,
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply-safe",
        action="store_true",
    )
    args = parser.parse_args()

    tracked = tracked_files()
    safe_remove: list[dict[str, Any]] = []
    review: list[dict[str, Any]] = []
    removed: list[str] = []

    for filename in tracked:
        path = ROOT / filename
        parts = Path(filename).parts

        if (
            "__pycache__" in parts
            or filename.endswith((".pyc", ".pyo"))
        ):
            safe_remove.append({
                "path": filename,
                "reason": "tracked_python_bytecode",
            })

    workflows = ROOT / ".github" / "workflows"

    if workflows.is_dir():
        for root_file in sorted(
            list(ROOT.glob("*.yml"))
            + list(ROOT.glob("*.yaml"))
        ):
            active = workflows / root_file.name

            if not active.is_file():
                continue

            if sha256(root_file) == sha256(active):
                safe_remove.append({
                    "path": root_file.name,
                    "reason": "identical_root_workflow_copy",
                    "activePath": str(
                        active.relative_to(ROOT)
                    ),
                })
            else:
                review.append({
                    "path": root_file.name,
                    "reason": "different_root_workflow_copy",
                    "activePath": str(
                        active.relative_to(ROOT)
                    ),
                })

    legacy_push = ROOT / "scripts" / "wrn-safe-push.sh"
    root_push = ROOT / "wrn-safe-push.sh"

    if legacy_push.is_file() and root_push.is_file():
        if sha256(legacy_push) == sha256(root_push):
            safe_remove.append({
                "path": str(legacy_push.relative_to(ROOT)),
                "reason": "identical_legacy_push_helper",
                "activePath": root_push.name,
            })
        else:
            review.append({
                "path": str(legacy_push.relative_to(ROOT)),
                "reason": "different_legacy_push_helper",
                "activePath": root_push.name,
            })

    # Deduplicate by path.
    unique_safe = {
        item["path"]: item
        for item in safe_remove
    }
    safe_remove = [
        unique_safe[key]
        for key in sorted(unique_safe)
    ]

    if args.apply_safe:
        tracked_set = set(tracked)

        for item in safe_remove:
            relative = item["path"]
            path = ROOT / relative

            if relative in tracked_set:
                remove_tracked(path)
                removed.append(relative)
            elif path.is_file():
                path.unlink()
                removed.append(relative)

    payload = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(
            timezone.utc
        ).isoformat(),
        "status": "ok",
        "applySafe": args.apply_safe,
        "safeRemove": safe_remove,
        "removed": removed,
        "manualReview": review,
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
