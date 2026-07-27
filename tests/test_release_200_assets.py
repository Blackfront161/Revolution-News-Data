from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

config = (ROOT / "config.js").read_text(encoding="utf-8")
worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
radar = (ROOT / "action-radar.js").read_text(encoding="utf-8")
editorial = (ROOT / "editorial-review-ui.js").read_text(encoding="utf-8")
freshness = (ROOT / "source-health-freshness.js").read_text(encoding="utf-8")
checker = (ROOT / "check_news_sources.py").read_text(encoding="utf-8")
roadmap = json.loads((ROOT / "ROADMAP.json").read_text(encoding="utf-8"))

assert "version: '2.0.0'" in config
assert "wrn-app-v2.0.0-" in worker
assert "action-radar.js" in config and "action-radar.js" in worker
assert "editorial-review-ui.js" in config and "editorial-review-ui.js" in worker
assert "source-health-freshness.js" in config and "source-health-freshness.js" in worker

for language in ("de", "en", "es", "fr", "it", "pt", "ru", "el", "tr"):
    assert f"{language}:" in radar
    assert f"{language}:" in editorial
    assert f"{language}:" in freshness

for token in (
    "navigator.geolocation",
    "wrn_event_reminders_v2",
    "Notification.requestPermission",
    "distanceKm",
    "openstreetmap.org",
):
    assert token in radar

for token in (
    "wrn_editorial_review_decisions_v2",
    "editorial-review.json",
    "exportDecisions",
    "wrn-more-admin-tools-184",
):
    assert token in editorial

assert "timedelta(hours=12)" in checker
assert '"freshUntil"' in checker
assert '"workflowIntervalHours": 4' in checker
assert '"expiredResultsAreNotPresentedAsCurrent": True' in checker

assert roadmap["current"]["version"] == "2.0.0"
assert roadmap["deferred"][0]["name"] == "Kuratiertes alternatives Social-Media-Fenster"
assert "zurückgestellt" in roadmap["deferred"][0]["status"]

loader_block = config[config.index("const loadCore"):config.index("openLandingTab();", config.index("const loadCore"))]
assert "alternative-social-media.js" not in loader_block

print("WRN 2.0 release assets: OK")
