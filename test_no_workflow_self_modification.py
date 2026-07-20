#!/usr/bin/env python3
from pathlib import Path
import hashlib
import importlib.util
import json
import tempfile


MODULE = Path(__file__).with_name(
    "harden_wrn_repository.py"
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    workflows = root / ".github" / "workflows"
    workflows.mkdir(parents=True)

    workflow = workflows / "update.yml"
    workflow.write_text(
        "permissions:\n"
        "  contents: write\n"
        "jobs:\n"
        "  build:\n"
        "    steps:\n"
        "      - run: git push\n",
        encoding="utf-8",
    )

    (root / "app.js").write_text(
        "localStorage.clear();\n",
        encoding="utf-8",
    )
    (root / "data-control.js").write_text(
        "const names = await caches.keys();\n",
        encoding="utf-8",
    )
    (root / "recovery.html").write_text(
        "<html><head></head><body></body></html>",
        encoding="utf-8",
    )

    module_copy = root / "harden_wrn_repository.py"
    module_copy.write_bytes(MODULE.read_bytes())

    before = digest(workflow)

    spec = importlib.util.spec_from_file_location(
        "hardener",
        module_copy,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    module.main()

    after = digest(workflow)

    assert before == after
    assert "localStorage.clear()" not in (
        root / "app.js"
    ).read_text(encoding="utf-8")
    assert (
        "wrn-origin-safety.js"
        in (root / "recovery.html").read_text(
            encoding="utf-8"
        )
    )

    report = json.loads(
        (root / "origin-safety-report.json")
        .read_text(encoding="utf-8")
    )

    assert report["workflowModificationEnabled"] is False
    assert report["workflowAudit"]
    assert all(
        row["modified"] is False
        for row in report["workflowAudit"]
    )

print("No-workflow-self-modification test: OK")
