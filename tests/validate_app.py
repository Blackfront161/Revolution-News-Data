#!/usr/bin/env python3
"""Small dependency-free consistency checks for World Revolution News."""
from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []
WARNINGS: list[str] = []


class AppHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.scripts: list[str] = []
        self.handlers: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        element_id = attributes.get("id")
        if element_id:
            self.ids.append(element_id)
        if tag == "script" and attributes.get("src"):
            self.scripts.append(attributes["src"] or "")
        for name, value in attrs:
            if name.startswith("on") and value:
                self.handlers.append(value)


def error(message: str) -> None:
    ERRORS.append(message)


def warning(message: str) -> None:
    WARNINGS.append(message)


def check_required_files() -> None:
    required = [
        "index.html",
        "styles.css",
        "config.js",
        "status-center.js",
        "app.js",
        "offline-db.js",
        "service-worker.js",
        "manifest.json",
    ]
    for relative in required:
        if not (ROOT / relative).is_file():
            error(f"Pflichtdatei fehlt: {relative}")


def check_html() -> AppHtmlParser | None:
    path = ROOT / "index.html"
    if not path.is_file():
        return None
    parser = AppHtmlParser()
    parser.feed(path.read_text(encoding="utf-8"))

    seen: set[str] = set()
    duplicate_ids: set[str] = set()
    for value in parser.ids:
        if value in seen:
            duplicate_ids.add(value)
        seen.add(value)
    for value in sorted(duplicate_ids):
        error(f"Doppelte HTML-ID: {value}")

    for script in parser.scripts:
        if script.startswith(("http://", "https://", "//")):
            continue
        clean = script.split("?", 1)[0].lstrip("./")
        if not (ROOT / clean).is_file():
            error(f"In index.html referenzierte Scriptdatei fehlt: {clean}")

    required_ids = {
        "status-container",
        "feed-container",
        "event-filter-panel",
        "podcast-library-modal",
        "global-media-player",
        "system-status-modal",
        "system-status-version",
    }
    missing = sorted(required_ids.difference(parser.ids))
    for value in missing:
        error(f"Benötigte HTML-ID fehlt: {value}")

    return parser


def javascript_symbols() -> set[str]:
    symbols: set[str] = set()
    patterns = [
        re.compile(r"(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\("),
        re.compile(r"window\.([A-Za-z_$][\w$]*)\s*="),
    ]
    for path in ROOT.glob("*.js"):
        text = path.read_text(encoding="utf-8")
        for pattern in patterns:
            symbols.update(pattern.findall(text))
    return symbols


def check_inline_handlers(parser: AppHtmlParser | None) -> None:
    if parser is None:
        return
    known = javascript_symbols()
    calls: set[str] = set()
    for handler in parser.handlers:
        for name in re.findall(r"\b([A-Za-z_$][\w$]*)\s*\(", handler):
            if name not in {"if", "for", "while", "switch"}:
                calls.add(name)
    for name in sorted(calls.difference(known)):
        error(f"HTML ruft eine nicht gefundene JavaScript-Funktion auf: {name}()")


def check_json_files() -> None:
    expected_lists = {"news.json", "events.json", "podcasts.json", "radio-stations.json"}
    for path in ROOT.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            error(f"Ungültiges JSON in {path.name}: {exc}")
            continue
        if path.name in expected_lists and not isinstance(data, list):
            error(f"{path.name} muss eine JSON-Liste sein.")
        if path.name == "manifest.json" and not isinstance(data, dict):
            error("manifest.json muss ein JSON-Objekt sein.")


def check_service_worker() -> None:
    path = ROOT / "service-worker.js"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    for match in re.findall(r"['\"]\./([^'\"]+)['\"]", text):
        if match.endswith(".json"):
            continue
        if not (ROOT / match).is_file():
            error(f"Service Worker referenziert eine fehlende Datei: {match}")
    if "config.js" not in text or "status-center.js" not in text:
        error("Service Worker muss config.js und status-center.js im App-Shell führen.")


def check_config() -> None:
    path = ROOT / "config.js"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    for token in ["version:", "news:", "events:", "podcasts:", "radio:", "proxyUrl:"]:
        if token not in text:
            error(f"config.js enthält den Pflichtwert nicht: {token}")


def main() -> int:
    check_required_files()
    parser = check_html()
    check_inline_handlers(parser)
    check_json_files()
    check_service_worker()
    check_config()

    print("World Revolution News – App-Prüfung")
    for item in WARNINGS:
        print(f"WARNUNG: {item}")
    for item in ERRORS:
        print(f"FEHLER: {item}")
    if ERRORS:
        print(f"\nPrüfung fehlgeschlagen: {len(ERRORS)} Fehler.")
        return 1
    print("\nAlle Prüfungen erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
