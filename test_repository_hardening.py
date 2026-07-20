#!/usr/bin/env python3
"""Regression tests for the WRN workflow and page hardener."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parent
MODULE_PATH = ROOT / "harden_wrn_repository.py"

spec = importlib.util.spec_from_file_location(
    "wrn_hardener",
    MODULE_PATH,
)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def test_concurrency() -> None:
    workflow = """name: Writer
on:
  workflow_dispatch:
permissions:
  contents: write
jobs:
  write:
    runs-on: ubuntu-latest
    steps:
      - run: git push
"""

    updated, changed = module.set_common_concurrency(workflow)

    assert changed
    assert "group: wrn-main-write" in updated


def test_update_news_staging() -> None:
    workflow = """name: Update News
on:
  workflow_dispatch:
jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - name: Check sources
        run: python check_news_sources.py
      - name: Commit changes
        run: |
          git config user.name bot
          git add source-health.json
          git commit -m update
          git push
"""

    updated, changed = module.add_update_news_staging(workflow)

    assert changed
    assert "source-health-report.json" in updated
    assert "discovered-feeds.json" in updated
    assert updated.index("source-health-report.json") < updated.index(
        "git commit"
    )


def test_html_injection_and_replacements() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "recovery.html"
        path.write_text(
            """<html><head></head><body><script>
localStorage.clear();
const cachesToDelete = await caches.keys();
const registrations =
  await navigator.serviceWorker.getRegistrations();
</script></body></html>""",
            encoding="utf-8",
        )

        assert module.inject_safety_script(path)
        changes = module.replace_destructive_patterns(path)
        text = path.read_text(encoding="utf-8")

        assert "wrn-origin-safety.js" in text
        assert "localStorage.clear()" not in text
        assert "getOwnedCacheNames()" in text
        assert "getOwnedServiceWorkerRegistrations()" in text
        assert changes


def main() -> int:
    test_concurrency()
    test_update_news_staging()
    test_html_injection_and_replacements()
    print("WRN repository hardening tests: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
