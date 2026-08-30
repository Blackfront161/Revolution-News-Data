import json
from pathlib import Path
import tempfile
import unittest

import exa_discovery


class ExaDiscoveryTests(unittest.TestCase):
    def test_canonical_url_removes_tracking(self):
        value = exa_discovery.canonical_url(
            "https://www.example.org/a/?utm_source=x&id=7#part"
        )
        self.assertEqual(value, "https://example.org/a?id=7")

    def test_load_queries_accepts_enabled_queries(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "queries.json"
            path.write_text(
                json.dumps(
                    {
                        "queries": [
                            {"id": "a", "query": "one", "enabled": True},
                            {"id": "b", "query": "two", "enabled": False},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            result = exa_discovery.load_queries(path)

        self.assertEqual([item["id"] for item in result], ["a"])

    def test_existing_results_are_not_reoffered(self):
        payload = {
            "results": [
                {
                    "title": "Already known",
                    "url": "https://example.org/story?utm_source=test",
                },
                {
                    "title": "New",
                    "url": "https://example.org/new",
                    "publishedDate": "2026-08-30T10:00:00Z",
                    "highlights": ["Example"],
                },
            ]
        }
        items, skipped = exa_discovery.normalized_results(
            payload,
            "test",
            {"https://example.org/story"},
        )
        self.assertEqual(skipped, 1)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "New")

    def test_dedupe_candidates(self):
        items = [
            {"canonicalUrl": "https://example.org/a", "queryId": "one"},
            {"canonicalUrl": "https://example.org/a", "queryId": "two"},
            {"canonicalUrl": "https://example.org/b", "queryId": "two"},
        ]
        result = exa_discovery.dedupe_candidates(items)
        self.assertEqual(len(result), 2)


if __name__ == "__main__":
    unittest.main()
