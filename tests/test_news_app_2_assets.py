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


def test_preview_server_can_be_exposed_to_private_lan():
    server = (ROOT / "scripts" / "serve_news_app_2.js").read_text(encoding="utf-8")
    assert "argumentValue('--host')" in server
    assert "'0.0.0.0'" in server
    assert "Smartphone im gleichen WLAN" in server


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
    assert "zine-designer.js" in html
    assert "zine-designer.css" in html
    assert "renderZineSection" in script
    assert "wrn_zine_articles" in script
    assert "next-dialog-zine" in html
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


def test_menu_briefing_and_responsive_images_are_present():
    html = (ROOT / "next.html").read_text(encoding="utf-8")
    script = (ROOT / "news-app-2.js").read_text(encoding="utf-8")
    style = (ROOT / "news-app-2.css").read_text(encoding="utf-8")
    assert 'id="next-menu-toggle"' in html
    assert 'id="next-menu-dialog"' in html
    assert 'id="next-briefing-dialog"' in html
    assert "openBriefing" in script
    assert "speakBriefing" in script
    assert "speechSynthesis" in script
    assert ".menu-dialog" in style
    assert ".briefing-dialog" in style
    assert "max-width: 100%" in style
    assert "-1px -1px 0 var(--red)" in style
    menu = html.split('id="next-menu-dialog"', 1)[1].split('</dialog>', 1)[0]
    assert 'data-view-target="home"' not in menu
    assert 'data-view-target=' not in menu
    assert 'id="next-menu-theme"' in menu
    assert 'id="next-menu-font-size"' in menu
    assert 'id="next-menu-density"' in menu
    assert "ensureBriefingTranslations" in script
    assert "data-briefing-id" in script
    assert "targetLanguage: language" in script
    assert "<h2>${escapeHtml(t('latest'))}</h2>" in script
    assert "UI_SETTINGS_KEY" in script
    assert "article-classification" in script
    assert ':root[data-theme="light"]' in style
    assert ':root[data-font-size="xlarge"]' in style
    assert ".news-card__image img" in style
    assert "object-fit: contain" in style
    assert "-webkit-line-clamp" not in style
    assert "display: block;\n  overflow: visible;" in style
    assert "linear-gradient(90deg, #050508 0 48%, #ff3158 52% 100%)" in style
    assert "-webkit-text-stroke: .6px #ff3158" in style
    assert ".dialog-actions a {\n  border-color: var(--red);" in style
    assert 'id="next-source-choices"' in html
    assert 'id="next-prisoner-choices"' in html
    assert 'id="next-development-choices"' in html
    assert 'id="next-preference-language"' in html
    assert "data-source-preference" in script
    assert "prisonerIds" in script
    assert "preferredLanguage" in script
    assert "briefingAmount" in script
    assert "preferenceReasons" in script
    assert ".filter-chips--topics" in style
    assert ".media-section-tabs button.active {\n  border-color: var(--red);\n  background: var(--red);\n  color: #07080a;" in style
    assert ".media-section-tabs button.active span {\n  color: #07080a;" in style


if __name__ == "__main__":
    test_parallel_preview_assets_exist()
    test_preview_server_can_be_exposed_to_private_lan()
    test_live_entry_point_is_not_rewired()
    test_preview_keeps_card_translation_and_safe_metadata()
    test_preview_offline_cache_is_isolated_from_live_app()
    test_specialty_views_are_native_preview_routes()
    test_default_lists_stay_short_and_source_balanced()
    test_media_sections_are_native_and_privacy_conscious()
    test_menu_briefing_and_responsive_images_are_present()
    print("News App 2 parallel preview assets: OK")
