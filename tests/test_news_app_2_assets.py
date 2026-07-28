from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_parallel_preview_assets_exist():
    for name in (
        "next.html", "news-app-2.css", "news-app-2.js", "news-app-2-core.js",
        "news-app-2-config.js", "news-app-2-specialty.js", "news-app-2-media.js",
        "news-app-2-sw.js"
    ):
        path = ROOT / name
        assert path.exists(), f"{name} is missing"
        assert path.stat().st_size > 300, f"{name} looks empty"


def test_live_entry_point_is_not_rewired():
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    service_worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
    assert "news-app-2.js" not in index
    assert "news-app-2.css" not in index
    assert "next.html" not in service_worker


def test_preview_keeps_card_translation_and_safe_metadata():
    html = (ROOT / "next.html").read_text(encoding="utf-8")
    script = (ROOT / "news-app-2.js").read_text(encoding="utf-8")
    assert "shared-translation-client.js" in html
    assert '<script src="config.js"></script>' not in html
    assert "news-app-2-config.js" in html
    assert 'data-action="translate"' in script
    assert "title_and_text" in script
    assert 'meta name="robots" content="noindex,nofollow"' in html
    assert "news-app-2-specialty.js" in html
    assert "news-app-2-media.js" in html
    assert "stories-core.js" in html
    assert "lexicon-tab.js" in html
    assert "prisoner-solidarity.js" in html
    assert "serviceWorker.register('./news-app-2-sw.js'" in script
    assert "scope: './next.html'" in script


def test_preview_offline_cache_is_isolated_from_live_app():
    preview_worker = (ROOT / "news-app-2-sw.js").read_text(encoding="utf-8")
    live_worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
    assert "wrn-news-app-2-" in preview_worker
    assert "./next.html" in preview_worker
    assert "./index.html" not in preview_worker
    assert "wrn-news-app-2-" not in live_worker


def test_specialty_views_are_native_preview_routes():
    script = (ROOT / "news-app-2.js").read_text(encoding="utf-8")
    for view in ("events", "lexicon", "prisoners", "developments"):
        assert f"render{view.capitalize()}" in script
        assert f"'{view}'" in script
    assert "WRNPrisonerSolidarity190.openWorkshop" in script
    assert "threshold: 0.5" in script


def test_default_lists_stay_short_and_source_balanced():
    script = (ROOT / "news-app-2.js").read_text(encoding="utf-8")
    assert "core.balanceBySource(chosen, HOME_COUNT, 2)" in script
    assert "hasActiveFilters ? 40 : HOME_COUNT" in script


def test_media_sections_are_native_and_privacy_conscious():
    script = (ROOT / "news-app-2.js").read_text(encoding="utf-8")
    html = (ROOT / "next.html").read_text(encoding="utf-8")
    assert "renderPodcastSection" in script
    assert "renderRadioSection" in script
    assert "renderVideoSection" in script
    assert 'preload="none"' in script
    assert "podcasts.json" in script
    assert "radio-stations.json" in script
    assert "news-app-2-media.js" in html


if __name__ == "__main__":
    test_parallel_preview_assets_exist()
    test_live_entry_point_is_not_rewired()
    test_preview_keeps_card_translation_and_safe_metadata()
    test_preview_offline_cache_is_isolated_from_live_app()
    test_specialty_views_are_native_preview_routes()
    test_default_lists_stay_short_and_source_balanced()
    test_media_sections_are_native_and_privacy_conscious()
    print("News App 2 parallel preview assets: OK")
