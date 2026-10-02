import json
from pathlib import Path
from source_import_policy import metadata_article


def test_registered_indigenous_feeds_preserve_original_host_and_exclude_publisher_body():
    registry = json.loads((Path(__file__).resolve().parents[1] / "multilingual-source-registry.json").read_text(encoding="utf-8"))
    urls = ("https://tejidocomunicacion.nasaacin.org/feed/", "https://debatesindigenas.org/feed/", "https://www.mapuexpress.org/feed/")
    for url in urls:
        matches = [s for s in registry["sources"] if s.get("feedUrl") == url]
        assert len(matches) == 1
        feed = matches[0]
        entry = {"title": "Public headline", "link": feed["homepage"] + "public-story/", "summary": "PROTECTED", "content": [{"value": "PROTECTED"}], "media_content": [{"url": feed["homepage"] + "protected.jpg"}]}
        result = metadata_article(feed, entry, "Latin America")
        assert result["language"] == "es"
        assert result["link"] == entry["link"]
        assert result["contentComplete"] is False
        assert result["image"] == "" and result["images"] == []
        assert "PROTECTED" not in str(result)
        assert metadata_article(feed, {**entry, "link": "https://foreign.example/story"}, "Latin America") is None
