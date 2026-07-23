#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "release_audit_183.py"

spec = importlib.util.spec_from_file_location("release_audit_183", AUDIT_PATH)
assert spec and spec.loader
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

report = audit.run_audit(root=ROOT, write_report=False)
summary = report["summary"]

assert report["version"] == "1.8.4"
assert report["readOnlyAudit"] is True
assert summary["fail"] == 0, [
    item for item in report["checks"] if item["status"] == "fail"
]
assert summary["total"] >= 35

source_recovery = (ROOT / "source_recovery.py").read_text(encoding="utf-8")
assert "PERMANENT_FAILURE_THRESHOLD = 4" in source_recovery
assert "PERMANENT_FAILURE_MIN_AGE = timedelta(hours=12)" in source_recovery
assert '"automaticDeletion": False' in source_recovery
assert "unlink(" not in source_recovery
assert "rmtree(" not in source_recovery

worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
assert "isIndexNavigation ? './index.html' : request" in worker
assert "cache.match(request, { ignoreSearch: true })" in worker

quality = (
    ROOT / ".github" / "workflows" / "quality-gate.yml"
).read_text(encoding="utf-8")
for command in (
    "python release_audit_183.py",
    "node tests/test_runtime_selftest_183.js",
    "python tests/test_release_candidate_183.py",
):
    assert command in quality
assert "release-readiness-183.json" in quality
assert audit.REPORT_PATH.name == "release-readiness-183.json"

print(
    "WRN 1.8.4 prerelease: "
    f"{summary['pass']} passed, "
    f"{summary['warning']} warnings, "
    f"{summary['total']} total"
)
