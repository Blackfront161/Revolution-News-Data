"""Verify coupled source-archive outputs before the media workflow commits them."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from build_source_archive import detail_matches
from update_calendar import verify_calendar_generation

PROTECTED = (
    "news.json", "events.json", "events-feed.json", "events-v2.json",
    "events-v2-feed.json", "calendar-source-cache.json",
    "calendar-status.json", "calendar-generation.json",
)


def baseline(root: Path, name: str):
    return json.loads(subprocess.check_output(
        ["git", "show", f"HEAD:{name}"], cwd=root))


def validate(root: Path) -> dict:
    def read(name):
        return json.loads((root / name).read_bytes())

    previous_feed = baseline(root, "news-feed.json")
    feed = read("news-feed.json")
    if not isinstance(feed, list) or not isinstance(previous_feed, list):
        raise ValueError("News feed must remain a flat array")
    def without_routes(rows):
        return [{k: v for k, v in row.items() if k not in ("detailPath", "detailUrl")}
                for row in rows]
    if without_routes(feed) != without_routes(previous_feed):
        raise ValueError("Media archive rebuild changed news content, identity or order")

    previous_status = baseline(root, "feed-status.json")
    status = read("feed-status.json")
    expected_status = copy.deepcopy(previous_status)
    expected_status["news"]["bytes"] = (root / "news-feed.json").stat().st_size
    if status != expected_status:
        raise ValueError("Media archive rebuild changed status beyond news.bytes")
    if status["news"]["feedCount"] != len(feed):
        raise ValueError("News feed/status count mismatch")

    packages = {}
    for row in feed:
        route = row.get("detailPath")
        if not route:
            if row.get("detailUrl"):
                raise ValueError("Unbound detail URL after archive rebuild")
            continue
        path = Path(str(route))
        if (path.parent != Path("news-archive") or path.suffix != ".json"
                or "\\" in str(route) or path.name in (".json", "..json")):
            raise ValueError("Unsafe source detail path")
        if route not in packages:
            packages[route] = read(route)
        rows = packages[route]
        if not isinstance(rows, list) or sum(detail_matches(row, full) for full in rows) != 1:
            raise ValueError("Detail route does not bind one admitted complete body")
        if row.get("detailUrl"):
            raise ValueError("Unexpected remote detail URL after archive rebuild")

    changed = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", *PROTECTED],
                             cwd=root, capture_output=True)
    if changed.returncode:
        raise ValueError("Media rebuild modified protected news/calendar inputs")
    if (root / "events-v2.json").exists() and not (root / "calendar-generation.json").exists():
        raise ValueError("V2 calendar missing generation certificate")
    verify_calendar_generation(root)
    return {"newsFeedCount": len(feed), "boundSourcePackages": len(packages),
            "protectedInputsUnchanged": True, "statusOnlyNewsBytesChanged": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(validate(args.root), sort_keys=True))


if __name__ == "__main__":
    main()
