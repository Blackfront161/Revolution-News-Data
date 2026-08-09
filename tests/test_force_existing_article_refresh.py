from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGGREGATE = (ROOT / "aggregate.py").read_text(encoding="utf-8")


assert '"WRN_FORCE_EXISTING_ARTICLE_REFRESH"' in AGGREGATE
assert '"WRN_NEWS_ARTICLE_LINKS"' in AGGREGATE
assert "not FORCE_EXISTING_ARTICLE_REFRESH" in AGGREGATE
assert "FORCE_EXISTING_ARTICLE_REFRESH\n                        or content_is_incomplete" in AGGREGATE
assert "if FORCE_EXISTING_ARTICLE_REFRESH:\n            MAX_NEUE_SCRAPES = limit" in AGGREGATE
assert "if TARGET_ARTICLE_LINKS and link not in TARGET_ARTICLE_LINKS" in AGGREGATE

print("Forced existing-article refresh hook: OK")
