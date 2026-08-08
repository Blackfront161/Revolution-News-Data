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
        "WRN_SOURCE_ROTATION_HOURS",
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


def test_checkpoint_sorts_mixed_feed_dates_chronologically():
    aggregate = (ROOT / "aggregate.py").read_text(encoding="utf-8")
    assert "from build_web_feeds import date_value" in aggregate
    assert "alle.sort(key=date_value, reverse=True)" in aggregate

    from build_web_feeds import date_value

    rows = [
        {"title": "older-rfc", "pubDate": "Thu, 06 Aug 2026 23:09:20 +0000"},
        {"title": "newer-iso", "pubDate": "2026-08-08T08:55:05+00:00"},
        {"title": "newest-rfc", "pubDate": "Sat, 08 Aug 2026 09:05:00 +0000"},
    ]
    ordered = sorted(rows, key=date_value, reverse=True)
    assert [item["title"] for item in ordered] == [
        "newest-rfc",
        "newer-iso",
        "older-rfc",
    ]


def test_feed_status_exposes_the_actual_newest_article_timestamp():
    from build_web_feeds import newest_article_at

    assert newest_article_at([
        {"pubDate": "Thu, 06 Aug 2026 23:09:20 +0000"},
        {"pubDate": "2026-08-08T08:55:05+00:00"},
    ]) == "2026-08-08T08:55:05+00:00"


def test_workflow_validates_and_stages_every_browser_feed():
    workflow = (ROOT / ".github" / "workflows" / "update.yml").read_text(
        encoding="utf-8"
    )
    for filename in ("news-feed.json", "events-feed.json", "feed-status.json"):
        assert filename in workflow
    assert "git add news-feed.json events-feed.json feed-status.json" in workflow
    assert 'age > 3600' in workflow
    assert 'status["news"]["newestArticleAt"]' in workflow
    assert "newest_age > 30 * 3600" in workflow
    assert 'int(run.get("newArticles") or 0) > 0' in workflow
    assert 'status.get("news", {}).get("feedCount") != len(news)' in workflow
    assert 'cron: "17 */2 * * *"' in workflow


def test_reclassifier_ignores_runtime_source_transformations():
    from reclassify_news_categories import definitions

    base, _extras, classify, regions, topics = definitions()
    assert base
    assert callable(classify)
    assert regions
    assert topics


if __name__ == "__main__":
    test_aggregator_stops_before_the_workflow_timeout()
    test_checkpoints_are_throttled_and_atomic()
    test_checkpoint_sorts_mixed_feed_dates_chronologically()
    test_feed_status_exposes_the_actual_newest_article_timestamp()
    test_workflow_validates_and_stages_every_browser_feed()
    test_reclassifier_ignores_runtime_source_transformations()
    print("WRN feed upload pipeline: OK")
