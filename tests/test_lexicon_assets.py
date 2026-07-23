from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_lexicon_assets_are_loaded_and_cached():
    config = read("config.js")
    worker = read("service-worker.js")

    assert "['lexicon-tab.css', 'lexicon-tab-recovery-184']" in config
    assert "['lexicon-tab.js', 'lexicon-tab-recovery-184']" in config
    assert "'./lexicon-tab.css'" in worker
    assert "'./lexicon-tab.js'" in worker


def test_lexicon_has_sections_sources_and_downloads():
    script = read("lexicon-tab.js")

    for section in ("basics", "organisation", "justice", "struggles", "all", "sources"):
        assert f"{section}:" in script or f"'{section}'" in script

    assert "TransformHarm" in script
    assert "Creative Interventions Toolkit" in script
    assert "An Anarchist FAQ" in script
    assert "Libcom · Anarchism reading guide" in script
    assert "wrn-begriffslexikon.json" in script
    assert "noopener noreferrer" in script


def test_lexicon_is_in_navigation_and_about_is_menu_only():
    navigation = read("release-1.5-nav.js")

    assert "key: 'lexicon'" in navigation
    assert "window.WRNLexicon184?.show?.(target)" in navigation
    assert "menuOnly: true" in navigation
    assert "activateTab('about')" in navigation
