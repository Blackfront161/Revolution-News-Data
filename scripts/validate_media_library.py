"""Stop publication when derived media, library or archive data is inconsistent."""

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def main():
    status = read("feed-status.json")
    video = read("video-feed.json")
    health = read("video-health.json")
    libraries = read("library-feed.json")
    library_health = read("library-health.json")
    archive = read("news-archive-manifest.json")
    now = datetime.now(timezone.utc)
    fetched = datetime.fromisoformat(str(status["lastSuccessfulFetchAt"]).replace("Z", "+00:00"))
    if not status.get("ok") or not 0 <= (now - fetched).total_seconds() <= 86400:
        raise SystemExit("News-Eingabe fehlt oder ist mehr als 24 Stunden alt")
    videos = video.get("items")
    if not isinstance(videos, list) or not videos:
        raise SystemExit("Video-Feed ist leer")
    ids = [item.get("canonicalId") for item in videos]
    if any(not key for key in ids) or len(ids) != len(set(ids)):
        raise SystemExit("Video-IDs fehlen oder sind doppelt")
    if health.get("totals", {}).get("acceptedCount") != len(videos):
        raise SystemExit("Video-Health und Feed widersprechen sich")
    checks = health.get("networkChecks", {})
    if checks.get("checked", 0) < len(videos) or checks.get("reachable", 0) < len(videos) // 2:
        raise SystemExit("Zu wenige Video-Links waren bei der Prüfung erreichbar")
    for result in checks.get("items", {}).get("results", []):
        if result.get("original", {}).get("unsafe") or (result.get("embed") or {}).get("unsafe"):
            raise SystemExit("Video-Feed enthält ein nichtöffentliches Ziel")
    if not isinstance(libraries, list) or len(libraries) < 20:
        raise SystemExit("Bibliotheksindex ist leer oder unvollständig")
    if library_health.get("itemCount") != len(libraries):
        raise SystemExit("Bibliotheks-Health und Index widersprechen sich")
    for item in libraries:
        links = [item.get("readUrl"), *(item.get("downloads") or {}).values()]
        if not item.get("id") or not item.get("title") or not any(
            urlparse(str(link)).scheme in {"http", "https"} and urlparse(str(link)).netloc
            for link in links if link
        ):
            raise SystemExit("Bibliothekseintrag ohne Titel oder sicheren Leselink")
    sources = archive.get("sources", [])
    if not sources or archive.get("sourceCount") != len(sources):
        raise SystemExit("Quellenarchiv-Manifest ist leer oder inkonsistent")
    count = 0
    for source in sources:
        path = Path(str(source.get("path", "")))
        if path.parent != Path("news-archive") or not (ROOT / path).is_file():
            raise SystemExit("Quellenarchiv-Datei fehlt oder ist außerhalb des Archivs")
        rows = read(path)
        if len(rows) != source.get("itemCount") or any(
            row.get("quelleName") != source.get("name") for row in rows
        ):
            raise SystemExit(f"Quellenarchiv inkonsistent: {path}")
        count += len(rows)
    if count != archive.get("itemCount"):
        raise SystemExit("Quellenarchiv-Gesamtzahl stimmt nicht")
    print(f"Geprüft: {len(videos)} Videos, {len(libraries)} Bibliothekstitel, {count} Archivartikel")


if __name__ == "__main__":
    main()
