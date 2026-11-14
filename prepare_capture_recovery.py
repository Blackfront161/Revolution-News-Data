#!/usr/bin/env python3
"""Prepare bounded, policy-validated recovery evidence, never publish or restore.

The output is outside the worktree and is suitable only for an isolated/manual
recovery review. An Actions artifact does not establish feed freshness, delivery
or permission to replay bodies under a future source policy.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile

from news_archive_capture import (
    MAX_CAPTURE_BYTES, HISTORY, WITHDRAWN_AT, read_capture, read_capture_policies,
)
from source_import_policy import article_is_withdrawn, restrict_existing_article

REPOSITORY = "Blackfront161/Revolution-News-Data"
MAX_RECOVERY_BYTES = MAX_CAPTURE_BYTES
MAX_POLICY_BYTES = 4 * 1024 * 1024
README = b"""RECOVERY ONLY - NOT A PUBLISHED FEED OR AUTOMATIC RESTORE INPUT

This bundle retains an exact bounded capture checkpoint, validated against the
included source policy at preparation. A failed aggregation may leave a partial
or old checkpoint. Timestamps here are evidence times, NOT feed freshness.

No workflow restores this artifact. Before any manual recovery: verify the
artifact digest and every receipt file digest, inspect the originating base/run/
attempt and aggregation outcome, compare current main and current source policy,
and revalidate identities, withdrawals, retention window, full-body provenance,
all derived outputs and current reader/release gates in an isolated copy.
Never copy this bundle over current production data or restamp it as a new fetch.
Successful runs retain capture in their normal data commit, not an artifact.
This failure-only copy is best effort: expiry, quota, cancellation and runner loss
can make it unavailable. It does not establish whether an uncertain push landed.
"""


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def regular_bytes(path: Path, limit: int) -> bytes:
    """Bound reads and refuse symlinks/non-files, including a symlink swap."""
    if path.is_symlink():
        raise ValueError("Recovery input cannot be a symlink")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError("Recovery input must be a regular file")
        with os.fdopen(fd, "rb", closefd=False) as source:
            raw = source.read(limit + 1)
    finally:
        os.close(fd)
    if len(raw) > limit:
        raise ValueError("Recovery input exceeds its byte limit")
    return raw


def assert_policy_conformity(rows: list[dict], policies: list[dict]) -> None:
    """Reject disallowed bodies rather than silently sanitizing a backup."""
    tombstone_fields = {
        "link", "title", "quelleName", "pubDate", "status", "deleted", "content",
        "contentComplete", WITHDRAWN_AT,
    }
    for row in rows:
        if article_is_withdrawn(row):
            if (set(row) - tombstone_fields or row.get("content") not in (None, "")
                    or row.get("contentComplete") is not False or HISTORY in row):
                raise ValueError("Recovery tombstone contains disallowed body/media/provenance")
            continue
        admitted = restrict_existing_article(row, policies)
        if admitted is None or admitted != row:
            raise ValueError("Capture does not conform to the current source policy; no recovery upload")


def prepare_recovery(repository: Path, output: Path, *, base_sha: str,
                     run_id: str, run_attempt: str, workflow_sha: str,
                     job: str, aggregation_outcome: str,
                     repository_name: str = REPOSITORY) -> dict:
    repository = repository.resolve(strict=True)
    if repository_name != REPOSITORY:
        raise ValueError("Unexpected recovery repository")
    if any(not re.fullmatch(r"[0-9a-f]{40}", value or "") for value in (base_sha, workflow_sha)):
        raise ValueError("Exact generation and workflow commit identities are required")
    if any(not re.fullmatch(r"[1-9][0-9]*", value or "") for value in (run_id, run_attempt)):
        raise ValueError("Exact positive run ID and attempt are required")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", job or ""):
        raise ValueError("Invalid recovery job identity")
    if aggregation_outcome not in {"success", "failure"}:
        raise ValueError("Aggregation must have actually succeeded or failed")
    head = subprocess.run(["git", "rev-parse", "--verify", "HEAD^{commit}"],
                          cwd=repository, text=True, capture_output=True, check=True).stdout.strip()
    if head != base_sha:
        checked = subprocess.run(
            ["bash", str(Path(__file__).with_name("wrn-bridge-safe-push.sh")),
             "--check-output-lineage", base_sha],
            cwd=repository, text=True, capture_output=True, check=True).stdout.strip()
        if checked != head:
            raise ValueError("Recovery HEAD is not the exact allowlisted data child of base")
    output = output.absolute()
    parent = output.parent.resolve(strict=True)
    if parent == repository or parent.is_relative_to(repository):
        raise ValueError("Recovery must be staged outside the publication worktree")
    output = parent / output.name
    if output.exists() or output.is_symlink():
        raise FileExistsError("Recovery output already exists; inspect instead of overwriting")

    raw = regular_bytes(repository / "news-archive-capture.json", MAX_CAPTURE_BYTES)
    policy_raw = regular_bytes(repository / "multilingual-source-registry.json", MAX_POLICY_BYTES)
    if head != base_sha:
        # Post-commit recovery must bind the retained bytes to that exact commit.
        for name, expected in (("news-archive-capture.json", raw),
                               ("multilingual-source-registry.json", policy_raw)):
            committed = subprocess.run(["git", "show", f"{head}:{name}"],
                                       cwd=repository, capture_output=True, check=True).stdout
            if committed != expected:
                raise ValueError("Recovery input differs from the exact output commit")
    with tempfile.TemporaryDirectory(prefix=".wrn-recovery-", dir=parent) as temporary:
        stage = Path(temporary)
        capture_path = stage / "news-archive-capture.json"
        policy_path = stage / "source-policy.json"
        capture_path.write_bytes(raw)
        policy_path.write_bytes(policy_raw)
        # The exact bytes being retained, not a second racing read, are validated.
        rows = read_capture(capture_path)
        policies = read_capture_policies(policy_path)
        assert_policy_conformity(rows, policies)
        receipt = {
            "schemaVersion": 1,
            "purpose": "capture-recovery-only",
            "publicationPerformed": False,
            "automaticRestorePermitted": False,
            "repository": repository_name,
            "generationBaseSha": base_sha,
            "checkpointHeadSha": head,
            "remotePublicationState": "not-established-by-recovery",
            "workflowSha": workflow_sha,
            "runId": run_id,
            "runAttempt": run_attempt,
            "job": job,
            "aggregationOutcome": aggregation_outcome,
            "preparedAt": datetime.now(timezone.utc).isoformat(),
            "freshnessClaim": "none",
            "rowCount": len(rows),
            "maximumBundleBytes": MAX_RECOVERY_BYTES,
            "sourcePolicyRevalidationRequiredBeforeRecovery": True,
            "files": {
                "news-archive-capture.json": {"bytes": len(raw), "sha256": digest(raw)},
                "source-policy.json": {"bytes": len(policy_raw), "sha256": digest(policy_raw)},
                "RECOVERY-ONLY.txt": {"bytes": len(README), "sha256": digest(README)},
            },
        }
        encoded = (json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
        if len(raw) + len(policy_raw) + len(README) + len(encoded) > MAX_RECOVERY_BYTES:
            raise ValueError("Recovery bundle exceeds the unchanged capture-sized limit")
        (stage / "RECOVERY-ONLY.txt").write_bytes(README)
        (stage / "recovery-receipt.json").write_bytes(encoded)
        # Refuse a concurrent replacement rather than binding mixed provenance.
        if raw != regular_bytes(repository / "news-archive-capture.json", MAX_CAPTURE_BYTES):
            raise ValueError("Capture changed during recovery preparation")
        if policy_raw != regular_bytes(repository / "multilingual-source-registry.json", MAX_POLICY_BYTES):
            raise ValueError("Source policy changed during recovery preparation")
        final_head = subprocess.run(["git", "rev-parse", "--verify", "HEAD^{commit}"],
                                    cwd=repository, text=True, capture_output=True, check=True).stdout.strip()
        if final_head != head:
            raise ValueError("Generation base changed during recovery preparation")
        # mkdir without exist_ok binds an empty destination; no existing evidence is overwritten.
        output.mkdir(mode=0o700)
        for name in receipt["files"]:
            (output / name).write_bytes((stage / name).read_bytes())
        (output / "recovery-receipt.json").write_bytes(encoded)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--aggregation-outcome", required=True, choices=("success", "failure"))
    args = parser.parse_args()
    receipt = prepare_recovery(
        Path.cwd(), args.output,
        base_sha=os.environ.get("WRN_BRIDGE_BASE_SHA", ""),
        run_id=os.environ.get("GITHUB_RUN_ID", ""),
        run_attempt=os.environ.get("GITHUB_RUN_ATTEMPT", ""),
        workflow_sha=os.environ.get("GITHUB_SHA", ""),
        job=os.environ.get("GITHUB_JOB", ""),
        repository_name=os.environ.get("GITHUB_REPOSITORY", ""),
        aggregation_outcome=args.aggregation_outcome,
    )
    print(json.dumps({
        "purpose": receipt["purpose"], "publicationPerformed": False,
        "rowCount": receipt["rowCount"],
        "captureSha256": receipt["files"]["news-archive-capture.json"]["sha256"],
        "aggregationOutcome": receipt["aggregationOutcome"],
    }))


if __name__ == "__main__":
    main()
