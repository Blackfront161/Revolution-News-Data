from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_parallel_preview_assets_exist():
    for name in ("next.html", "news-app-2.css", "news-app-2.js", "news-app-2-core.js", "news-app-2-config.js"):
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
    assert "serviceWorker.register" not in script


def test_default_lists_stay_short_and_source_balanced():
    script = (ROOT / "news-app-2.js").read_text(encoding="utf-8")
    assert "core.balanceBySource(chosen, HOME_COUNT, 2)" in script
    assert "hasActiveFilters ? 40 : HOME_COUNT" in script


if __name__ == "__main__":
    test_parallel_preview_assets_exist()
    test_live_entry_point_is_not_rewired()
    test_preview_keeps_card_translation_and_safe_metadata()
    test_default_lists_stay_short_and_source_balanced()
    print("News App 2 parallel preview assets: OK")
