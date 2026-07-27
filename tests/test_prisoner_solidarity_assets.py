from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

data = json.loads((ROOT / "prisoner-solidarity.json").read_text(encoding="utf-8"))
profiles = data["profiles"]
sources = {source["id"]: source for source in data["sources"]}

assert data["schemaVersion"] == 1
assert data["reviewWindowDays"] <= 45
assert len(profiles) >= 5
assert len({profile["id"] for profile in profiles}) == len(profiles)
assert {"nycabc-guide-19-5", "nycabc-write", "abcf-updates"} <= set(sources)

for profile in profiles:
    verification = profile["verification"]
    address = profile["mailingAddress"]
    assert verification["status"] == "verified"
    assert date.fromisoformat(verification["nextReviewAt"]) >= date.fromisoformat(
        verification["verifiedAt"]
    )
    assert date.fromisoformat(verification["nextReviewAt"]) >= date(2026, 7, 27)
    assert address["public"] is True
    assert len(address["lines"]) >= 4
    assert profile["prisonerId"] in "\n".join(address["lines"])
    assert verification["sourceIds"]
    assert all(source_id in sources for source_id in verification["sourceIds"])
    assert verification["profileUrl"].startswith("https://")
    assert profile["aliases"]
    assert profile["mailRules"]["imagesAllowed"] in (True, False, None)

config = (ROOT / "config.js").read_text(encoding="utf-8")
worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
navigation = (ROOT / "release-1.5-nav.js").read_text(encoding="utf-8")
index = (ROOT / "index.html").read_text(encoding="utf-8")
module = (ROOT / "prisoner-solidarity.js").read_text(encoding="utf-8")
styles = (ROOT / "prisoner-solidarity.css").read_text(encoding="utf-8")

for token in [
    "prisoner-solidarity.json",
    "prisoner-solidarity.js",
    "prisoner-solidarity.css",
]:
    assert token in worker or token in config

assert "key: 'solidarity'" in navigation
assert "WRNPrisonerSolidarity190" in navigation
assert "prisoner-solidarity.js?v=190-solidarity-1" in index
assert "prisoner-solidarity.css?v=190-solidarity-1" in index
assert "wrn_prisoner_letter_" in module
assert "window.confirm(t.translateConfirm)" in module
assert "title: '', text: body" in module
assert "profile.mailRules?.imagesAllowed !== true" in module
assert "if (!profile || !isCurrent(profile)) return" in module
assert "@media print" in styles
assert "@media (max-width: 760px)" in styles
assert "z-index: 1000000" in styles

print("WRN prisoner solidarity assets: OK")
