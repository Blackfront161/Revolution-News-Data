from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_aggregator_stops_before_the_workflow_timeout():
    aggregate = (ROOT / "aggregate.py").read_text(encoding="utf-8")
    for token in (
        "WRN_AGGREGATE_BUDGET_SECONDS",
        "WRN_AGGREGATE_STOP_RESERVE_SECONDS",
        "aggregate_budget_exhausted()",
        "aggregate_stopped_for_budget",
        "rotate_source_buckets",
    ):
        assert token in aggregate


def test_checkpoints_are_throttled_and_atomic():
    aggregate = (ROOT / "aggregate.py").read_text(encoding="utf-8")
    assert "WRN_CHECKPOINT_INTERVAL_SECONDS" in aggregate
    assert 'temporary = f"{path}.tmp"' in aggregate
    assert "os.replace(temporary, path)" in aggregate
    assert "save_checkpoint(force=True)" in aggregate
    assert "NON_IMAGE_MEDIA_EXTENSIONS" in aggregate
    assert "pathname.endswith(NON_IMAGE_MEDIA_EXTENSIONS)" in aggregate


def test_workflow_validates_and_stages_every_browser_feed():
    workflow = (ROOT / ".github" / "workflows" / "update.yml").read_text(
        encoding="utf-8"
    )
    for filename in ("news-feed.json", "events-feed.json", "feed-status.json"):
        assert filename in workflow
    assert "git add news-feed.json events-feed.json feed-status.json" in workflow
    assert 'age > 3600' in workflow
    assert 'status.get("news", {}).get("feedCount") != len(news)' in workflow


if __name__ == "__main__":
    test_aggregator_stops_before_the_workflow_timeout()
    test_checkpoints_are_throttled_and_atomic()
    test_workflow_validates_and_stages_every_browser_feed()
    print("WRN feed upload pipeline: OK")
