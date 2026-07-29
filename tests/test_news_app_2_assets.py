from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_parallel_preview_assets_exist():
    for name in (
        "next.html", "news-app-2.css", "news-app-2.js", "news-app-2-core.js",
        "news-app-2-config.js", "news-app-2-specialty.js", "news-app-2-media.js",
        "news-app-2-release.js", "news-app-2-release.css",
        "news-app-2-release-checklist.html", "news-app-2-release-checklist.css",
        "news-app-2-sw.js", "wrn-logo-preview-transparent.png"
    ):
        path = ROOT / name
        assert path.exists(), f"{name} is missing"
        assert path.stat().st_size > 300, f"{name} looks empty"


def test_preview_server_can_be_exposed_to_private_lan():
    server = (ROOT / "scripts" / "serve_news_app_2.js").read_text(encoding="utf-8")
    assert "argumentValue('--host')" in server
    assert "'0.0.0.0'" in server
    assert "Smartphone im gleichen WLAN" in server
    assert "data=live" in server


def test_release_entry_point_is_news_app_2_and_classic_is_preserved():
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    classic = (ROOT / "classic.html").read_text(encoding="utf-8")
    redirect = (ROOT / "next.html").read_text(encoding="utf-8")
    service_worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
    assert "news-app-2.js?release=1" in index
    assert "news-app-2.css?release=1" in index
    assert "app.js" in classic
    assert "classic.html" in index
    assert "index.html" in redirect
    assert "news-app-2.js?release=1" in service_worker
    assert "classic.html" in service_worker


def test_release_keeps_card_translation_and_safe_metadata():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    script = (ROOT / "news-app-2.js").read_text(encoding="utf-8")
    assert "shared-translation-client.js" in html
    assert '<script src="config.js"></script>' not in html
    assert "news-app-2-config.js" in html
    assert 'data-action="translate"' in script
    assert "title_and_text" in script
    assert 'meta name="robots" content="index,follow"' in html
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
    assert "isProduction ? './service-worker.js' : './news-app-2-sw.js'" in script
    assert "isProduction ? './' : './next.html'" in script


def test_release_uses_same_origin_feeds_and_preview_can_read_live_feeds():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    config = (ROOT / "news-app-2-config.js").read_text(encoding="utf-8")
    assert "https://blackfront161.github.io" in html
    assert "WRN_PREVIEW_LIVE_DATA" in config
    assert "'same-origin-production'" in config
    assert "'live-readonly'" in config
    assert "wrnPreviewDataUrl('news-feed.json')" in config
    assert "wrnPreviewDataUrl('events-feed.json')" in config


def test_preview_and_production_offline_caches_are_distinct():
    preview_worker = (ROOT / "news-app-2-sw.js").read_text(encoding="utf-8")
    live_worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
    assert "wrn-news-app-2-" in preview_worker
    assert "./next.html" in preview_worker
    assert "./index.html" not in preview_worker
    assert "wrn-app-v2.0.0-action-radar" in live_worker


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
    assert "allDiscoverResults().slice(0, state.discover.limit)" in script
    assert "last7Days" in script
    assert "last30Days" in script
    assert 'data-action="discover-more"' in script


def test_media_sections_are_native_and_privacy_conscious():
    script = (ROOT / "news-app-2.js").read_text(encoding="utf-8")
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "renderPodcastSection" in script
    assert "renderRadioSection" in script
    assert "renderVideoSection" in script
    assert 'id="global-media-player" preload="none"' in html
    assert "media-player.js" in html
    assert "audio-tools.js" in html
    assert "appendSimpleMediaControls" in script
    assert "podcasts.json" in script
    assert "radio-stations.json" in script
    assert "news-app-2-media.js" in html


def test_menu_briefing_and_responsive_images_are_present():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
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
    assert ".dialog-actions #next-dialog-translate {" in style
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


def test_article_tools_and_professional_discovery_are_present():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    script = (ROOT / "news-app-2.js").read_text(encoding="utf-8")
    style = (ROOT / "news-app-2.css").read_text(encoding="utf-8")
    worker = (ROOT / "news-app-2-sw.js").read_text(encoding="utf-8")
    for action in ("article-summary", "article-translate", "article-podcast", "article-zine", "article-read", "article-share"):
        assert f'data-action="{action}"' in html
    assert "article-summary-core.js" in html
    assert "article-summary-core.js" in worker
    assert "renderTranslationComparison" in script
    assert "shareOpenArticle" in script
    assert "toggleRead" in script
    assert "TOPIC_GROUPS" in script
    assert "filter-chips--regions" in style
    assert ".archive-periods" in style
    assert "aspect-ratio: auto;" in style


def test_release_header_cards_and_mobile_navigation_are_polished():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    script = (ROOT / "news-app-2.js").read_text(encoding="utf-8")
    style = (ROOT / "news-app-2.css").read_text(encoding="utf-8")
    worker = (ROOT / "news-app-2-sw.js").read_text(encoding="utf-8")
    assert 'src="wrn-logo-preview-transparent.png"' in html
    assert "./wrn-logo-preview-transparent.png" in worker
    assert 'class="small-action" type="button" data-action="open"' in script
    assert ".card-actions .translate-card,\n.card-actions .small-action {" in style
    assert "height: calc(68px + env(safe-area-inset-bottom));" in style
    assert "contain: layout paint;" in style
    assert "transform: translate3d(0, 0, 0);" in style
    assert ".news-card::before {\n    opacity: 1;" in style


def test_release_logo_is_transparent_and_donation_flow_matches_live_safety():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    script = (ROOT / "news-app-2.js").read_text(encoding="utf-8")
    style = (ROOT / "news-app-2.css").read_text(encoding="utf-8")
    logo = (ROOT / "wrn-logo-preview-transparent.png").read_bytes()
    assert logo.startswith(b"\x89PNG\r\n\x1a\n")
    assert logo[25] in (4, 6), "preview logo must contain an alpha channel"
    assert 'id="next-menu-donate"' in html
    assert 'id="next-donation-dialog"' in html
    assert "https://www.paypal.com/ncp/payment/6FSV9FEN4X7VS" in html
    assert 'rel="noopener noreferrer"' in html
    assert 'referrerpolicy="no-referrer"' in html
    assert "donationDialog.showModal()" in script
    assert "donateWarning" in script
    assert ".menu-shell > section > .menu-donate" in style


def test_release_candidate_restores_existing_live_capabilities():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    script = (ROOT / "news-app-2.js").read_text(encoding="utf-8")
    helper = (ROOT / "news-app-2-release.js").read_text(encoding="utf-8")
    worker = (ROOT / "news-app-2-sw.js").read_text(encoding="utf-8")
    for asset in (
        "source-profiles.js", "source-verification.js", "editorial-review-ui.js",
        "media-player.js", "audio-tools.js", "news-app-2-release.js"
    ):
        assert asset in html
        assert asset in worker
    for feature in (
        "splitTranslationChunks", "READING_POSITIONS_KEY", "discoverAdvancedFiltersMarkup",
        "eventIcs", "EVENT_REMINDERS_KEY", "renderDataControl", "renderSystemStatus",
        "generateCloudPodcast", "reportTranslationProblem"
    ):
        assert feature in script or feature in helper
    assert 'data-action="about"' in html
    assert 'data-action="system-status"' in html
    assert 'data-action="data-control"' in html
    assert 'value="200"' in html
    assert "unverÃ¤ndert', 'unverändert" in script


def test_release_checklist_is_readable_and_available():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    checklist = (ROOT / "news-app-2-release-checklist.html").read_text(encoding="utf-8")
    style = (ROOT / "news-app-2-release-checklist.css").read_text(encoding="utf-8")
    worker = (ROOT / "news-app-2-sw.js").read_text(encoding="utf-8")
    assert 'id="next-menu-release"' in html
    assert 'href="news-app-2-release-checklist.html"' in html
    assert "news-app-2-release-checklist.html" in worker
    assert "news-app-2-release-checklist.css" in worker
    assert 'class="release-checklist-page"' in checklist
    assert "Bestanden" in checklist
    assert "Integriert" in checklist
    assert "Noch gesperrt" in checklist
    assert "width: min(1040px, calc(100% - 32px));" in style
    assert "@media (max-width: 720px)" in style
    assert "<table" not in checklist


if __name__ == "__main__":
    test_parallel_preview_assets_exist()
    test_preview_server_can_be_exposed_to_private_lan()
    test_release_entry_point_is_news_app_2_and_classic_is_preserved()
    test_release_keeps_card_translation_and_safe_metadata()
    test_release_uses_same_origin_feeds_and_preview_can_read_live_feeds()
    test_preview_and_production_offline_caches_are_distinct()
    test_specialty_views_are_native_preview_routes()
    test_default_lists_stay_short_and_source_balanced()
    test_media_sections_are_native_and_privacy_conscious()
    test_menu_briefing_and_responsive_images_are_present()
    test_article_tools_and_professional_discovery_are_present()
    test_release_header_cards_and_mobile_navigation_are_polished()
    test_release_logo_is_transparent_and_donation_flow_matches_live_safety()
    test_release_candidate_restores_existing_live_capabilities()
    test_release_checklist_is_readable_and_available()
    print("News App 2 parallel preview assets: OK")
