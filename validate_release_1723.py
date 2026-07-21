#!/usr/bin/env python3
"""Validate WRN 1.7.23 release contracts."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import py_compile
import re
import subprocess


ROOT = Path(__file__).resolve().parent


def load_json(filename: str):
    return json.loads(
        (ROOT / filename).read_text(encoding="utf-8")
    )


def valid_timestamp(value) -> bool:
    if not isinstance(value, str) or not value:
        return False

    try:
        datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
        return True
    except ValueError:
        return False


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    required_files = (
        ".gitignore",
        "requirements-wrn.lock.txt",
        "OPERATIONS.md",
        "generated-podcasts.json",
        "aggregate-hardening-report.json",
        "generated-podcasts-report.json",
        "repository-cleanup-report.json",
        "release-version-report.json",
    )

    for filename in required_files:
        if not (ROOT / filename).is_file():
            errors.append(f"{filename} fehlt.")

    aggregate = ROOT / "aggregate.py"

    if not aggregate.is_file():
        errors.append("aggregate.py fehlt.")
    else:
        text = aggregate.read_text(
            encoding="utf-8",
            errors="replace",
        )

        for marker in (
            "# WRN 1.7.23 ENTRY SAFETY",
            "def safe_text(",
            "except Exception as entry_error:",
            "save_aggregate_error_report()",
        ):
            if marker not in text:
                errors.append(
                    f"aggregate.py fehlt Marker: {marker}"
                )

        try:
            py_compile.compile(
                str(aggregate),
                doraise=True,
            )
        except Exception as error:
            errors.append(
                f"aggregate.py Syntaxfehler: {error}"
            )

    podcasts_path = ROOT / "generated-podcasts.json"

    if podcasts_path.is_file():
        try:
            podcasts = load_json(
                "generated-podcasts.json"
            )
        except Exception as error:
            errors.append(
                f"generated-podcasts.json ungültig: {error}"
            )
        else:
            if not isinstance(podcasts, list):
                errors.append(
                    "generated-podcasts.json ist keine Liste."
                )

    gitignore_text = (
        (ROOT / ".gitignore").read_text(
            encoding="utf-8",
        )
        if (ROOT / ".gitignore").is_file()
        else ""
    )

    for pattern in (
        "__pycache__/",
        "*.py[cod]",
        "*.tmp",
        "aggregate.py.pre-*.bak",
    ):
        if pattern not in gitignore_text:
            errors.append(
                f".gitignore fehlt Muster: {pattern}"
            )

    lock_text = (
        (ROOT / "requirements-wrn.lock.txt")
        .read_text(encoding="utf-8")
        if (ROOT / "requirements-wrn.lock.txt")
        .is_file()
        else ""
    )

    for package in (
        "beautifulsoup4",
        "cloudscraper",
        "feedparser",
        "lxml",
        "python-dateutil",
        "requests",
    ):
        if not re.search(
            rf"(?m)^{re.escape(package)}==[^\s]+$",
            lock_text,
        ):
            errors.append(
                f"requirements-wrn.lock.txt "
                f"pinnt {package} nicht."
            )

    for filename in (
        "aggregate-hardening-report.json",
        "generated-podcasts-report.json",
        "repository-cleanup-report.json",
        "release-version-report.json",
    ):
        path = ROOT / filename

        if not path.is_file():
            continue

        try:
            report = load_json(filename)
        except Exception as error:
            errors.append(
                f"{filename} ungültig: {error}"
            )
            continue

        if not valid_timestamp(
            report.get("generatedAt")
        ):
            errors.append(
                f"{filename}: generatedAt ungültig."
            )

        if report.get("status") == "failed":
            errors.append(
                f"{filename} meldet einen Fehler."
            )

    try:
        tracked = subprocess.run(
            ["git", "-c", f"safe.directory={ROOT}", "ls-files"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
    except Exception:
        tracked = []

    bytecode = [
        filename
        for filename in tracked
        if (
            "__pycache__" in Path(filename).parts
            or filename.endswith((".pyc", ".pyo"))
        )
    ]

    if bytecode:
        errors.append(
            "Versionierter Python-Bytecode verbleibt: "
            + ", ".join(bytecode)
        )

    if errors:
        for error in errors:
            print(f"FEHLER: {error}")

        print(
            f"WRN 1.7.23-Prüfung fehlgeschlagen: "
            f"{len(errors)} Fehler."
        )
        return 1

    for warning in warnings:
        print(f"WARNUNG: {warning}")

    print("WRN 1.7.23-Prüfung: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
