#!/usr/bin/env python3
"""Read-only static release audit for the current World Revolution News release.

The audit only writes release-readiness-183.json when write_report is true.
It never edits application files, workflows, registries, or user data.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parent
REPORT_PATH = ROOT / "release-readiness-183.json"
EXPECTED_VERSION = "1.9.0"
EXPECTED_APP_CACHE = "wrn-app-v1.9.0-prisoner-solidarity"
EXPECTED_DATA_CACHE = "wrn-data-v1.9.0-prisoner-solidarity"

REQUIRED_FILES = (
    ".github/workflows/quality-gate.yml",
    ".github/workflows/update.yml",
    "app-check.html",
    "app-diagnostics.js",
    "config.js",
    "manifest.json",
    "service-worker.js",
    "runtime-selftest.js",
    "runtime-selftest.css",
    "video-hub.js",
    "video-hub.css",
    "lexicon-tab.js",
    "lexicon-tab.css",
    "audio-tab-183.js",
    "audio-tab-183.css",
    "interface-block3.js",
    "interface-block3.css",
    "light-theme.css",
    "source-recovery-ui-183.js",
    "source-recovery-ui-183.css",
    "source-verification.js",
    "source_recovery.py",
    "app-background.webp",
    "wrn-future-header-white.png",
    "tests/test_video_assets.py",
    "tests/test_audio_block2_assets.py",
    "tests/test_source_recovery_assets.py",
    "tests/test_runtime_selftest_183.js",
    "tests/test_release_candidate_183.py",
)

APP_SHELL_FILES = (
    "app-check.html",
    "runtime-selftest.js",
    "runtime-selftest.css",
    "video-hub.js",
    "video-hub.css",
    "lexicon-tab.js",
    "lexicon-tab.css",
    "audio-tab-183.js",
    "audio-tab-183.css",
    "interface-block3.js",
    "interface-block3.css",
    "light-theme.css",
    "source-recovery-ui-183.js",
    "source-recovery-ui-183.css",
    "app-background.webp",
    "wrn-future-header-white.png",
)

SELFTEST_LANGUAGES = ("en", "de", "es", "fr", "it", "pt", "ru", "el", "tr")
SELFTEST_MODULES = (
    "WRNVideoHub",
    "WRNAudioTab183",
    "WRNInterfaceBlock3",
    "WRNSourceRecoveryUI183",
    "WRNSourceVerification",
)


def read_text(root: Path, relative: str) -> str:
    path = root / relative
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


class ReleaseAudit:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.checks: list[dict[str, Any]] = []

    def add(
        self,
        check_id: str,
        category: str,
        condition: bool,
        message: str,
        *,
        warning: bool = False,
        detail: str = "",
    ) -> None:
        status = "pass" if condition else ("warning" if warning else "fail")
        self.checks.append(
            {
                "id": check_id,
                "category": category,
                "status": status,
                "message": message,
                "detail": detail,
            }
        )

    def run(self) -> dict[str, Any]:
        self.check_files()
        self.check_config()
        self.check_service_worker()
        self.check_manifest()
        self.check_security_policy()
        self.check_runtime_selftest()
        self.check_release_test_page()
        self.check_diagnostics()
        self.check_source_recovery()
        self.check_workflows()
        self.check_header()

        summary = {
            "pass": sum(item["status"] == "pass" for item in self.checks),
            "warning": sum(item["status"] == "warning" for item in self.checks),
            "fail": sum(item["status"] == "fail" for item in self.checks),
            "total": len(self.checks),
        }
        config = read_text(self.root, "config.js")
        build = re.search(r"\bbuild:\s*['\"]([^'\"]+)", config)
        return {
            "schemaVersion": 1,
            "app": "World Revolution News",
            "version": EXPECTED_VERSION,
            "build": build.group(1) if build else "",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "readOnlyAudit": True,
            "summary": summary,
            "checks": self.checks,
        }

    def check_files(self) -> None:
        for relative in REQUIRED_FILES:
            self.add(
                f"file:{relative}",
                "files",
                (self.root / relative).is_file(),
                f"Required file exists: {relative}",
            )

    def check_config(self) -> None:
        source = read_text(self.root, "config.js")
        self.add(
            "config-version",
            "release",
            f"version: '{EXPECTED_VERSION}'" in source,
            f"config.js declares version {EXPECTED_VERSION}",
        )
        build = re.search(r"\bbuild:\s*['\"]([^'\"]+)", source)
        build_value = build.group(1) if build else ""
        self.add(
            "config-build",
            "release",
            EXPECTED_VERSION in build_value and "release" in build_value,
            f"Build is marked as the {EXPECTED_VERSION} release",
            detail=build_value,
        )
        self.add(
            "config-recovery-stage",
            "release",
            re.search(r"\brecoveryStage:\s*15\b", source) is not None,
            "Recovery stage is 15",
        )
        self.add(
            "config-loader",
            "release",
            "const VERSION = '190-solidarity-1';" in source,
            "Dynamic loader uses 190-solidarity-1",
        )
        for token in ("dataUrls:", "proxyUrl:", "sharedTranslationUrl:"):
            self.add(
                f"config-preserves-{token.rstrip(':')}",
                "safety",
                token in source,
                f"Existing config contract remains present: {token}",
            )

    def check_service_worker(self) -> None:
        source = read_text(self.root, "service-worker.js")
        self.add(
            "worker-app-cache",
            "offline",
            EXPECTED_APP_CACHE in source,
            "Service worker uses the release app cache",
        )
        self.add(
            "worker-data-cache",
            "offline",
            EXPECTED_DATA_CACHE in source,
            "Service worker uses the release data cache",
        )
        for relative in APP_SHELL_FILES:
            self.add(
                f"app-shell:{relative}",
                "offline",
                f"'./{relative}'" in source,
                f"App shell contains {relative}",
            )
        for token in (
            "networkFirstNavigation",
            "networkFirstData",
            "networkFirstAsset",
            "JSON_FALLBACKS",
            "cache: 'no-store'",
            "isIndexNavigation ? './index.html' : request",
        ):
            self.add(
                f"worker-preserves:{token}",
                "offline",
                token in source,
                f"Offline/fallback contract remains present: {token}",
            )

    def check_manifest(self) -> None:
        path = self.root / "manifest.json"
        manifest: dict[str, Any] = {}
        valid_json = False
        try:
            parsed = json.loads(path.read_text(encoding="utf-8"))
            valid_json = isinstance(parsed, dict)
            manifest = parsed if isinstance(parsed, dict) else {}
        except (OSError, json.JSONDecodeError):
            pass
        self.add("manifest-json", "pwa", valid_json, "manifest.json is valid JSON")
        self.add(
            "manifest-name",
            "pwa",
            manifest.get("name") == "World Revolution News",
            "Manifest name is World Revolution News",
        )
        self.add(
            "manifest-start-url",
            "pwa",
            bool(manifest.get("start_url")),
            "Manifest provides start_url",
        )
        icons = manifest.get("icons", [])
        self.add(
            "manifest-icon",
            "pwa",
            isinstance(icons, list)
            and any(isinstance(icon, dict) and icon.get("src") == "icon.svg" for icon in icons),
            "Manifest contains icon.svg",
        )

    def check_security_policy(self) -> None:
        index = read_text(self.root, "index.html")
        match = re.search(
            r'http-equiv="Content-Security-Policy"\s+content="([^"]+)"',
            index,
            flags=re.IGNORECASE,
        )
        csp = match.group(1) if match else ""
        self.add("csp-present", "security", bool(csp), "Content Security Policy is present")
        for origin in (
            "https://www.youtube-nocookie.com",
            "https://player.vimeo.com",
            "https://kolektiva.media",
        ):
            self.add(
                f"csp-frame:{origin}",
                "security",
                origin in csp,
                f"Video CSP allows {origin}",
            )
        self.add(
            "csp-no-broad-frame-https",
            "security",
            re.search(r"frame-src[^;]*\shttps:\s", csp) is None,
            "frame-src does not allow every HTTPS origin",
        )
        self.add(
            "csp-object-none",
            "security",
            "object-src 'none'" in csp,
            "CSP contains object-src 'none'",
        )

    def check_runtime_selftest(self) -> None:
        source = read_text(self.root, "runtime-selftest.js")
        self.add(
            "selftest-version",
            "selftest",
            f"const EXPECTED_VERSION = '{EXPECTED_VERSION}';" in source,
            f"Runtime self-test expects {EXPECTED_VERSION}",
        )
        self.add(
            "selftest-no-old-version",
            "selftest",
            re.search(r"EXPECTED_VERSION\s*=\s*['\"]1\.7\.(?:5|17)", source) is None,
            "Runtime self-test has no obsolete expected version",
        )
        for language in SELFTEST_LANGUAGES:
            self.add(
                f"selftest-language:{language}",
                "selftest",
                re.search(
                    rf"\b{re.escape(language)}:\s*Object\.freeze\(\{{",
                    source,
                )
                is not None,
                f"Runtime self-test contains {language}",
            )
        for module_name in SELFTEST_MODULES:
            self.add(
                f"selftest-module:{module_name}",
                "selftest",
                f"'{module_name}'" in source,
                f"Runtime self-test checks {module_name}",
            )
        for check_id, token, message in (
            ("selftest-storage-cleanup", "localStorage.removeItem(TEMP_STORAGE_KEY)", "Temporary storage key is removed"),
            ("selftest-escape", "event.key === 'Escape'", "Escape closes the self-test"),
            ("selftest-no-store", "cache: 'no-store'", "Self-test fetches bypass caches"),
            ("selftest-sw-registration", "navigator.serviceWorker.getRegistration()", "Self-test checks service-worker registration"),
            ("selftest-sw-control", "navigator.serviceWorker?.controller", "Self-test checks service-worker control"),
            ("selftest-manifest", "'./manifest.json'", "Self-test checks manifest.json"),
            ("selftest-report-copy", "copyReport", "Self-test can copy its report"),
        ):
            self.add(check_id, "selftest", token in source, message)

    def check_release_test_page(self) -> None:
        source = read_text(self.root, "app-check.html")
        for check_id, token, message in (
            ("app-check-version", "WRN_CONFIG.version === EXPECTED_VERSION", "Release page checks WRN_CONFIG.version"),
            ("app-check-build", "EXPECTED_BUILD_MARKER", "Release page checks the release build"),
            ("app-check-manifest", "'./manifest.json'", "Release page checks manifest.json"),
            ("app-check-cache", EXPECTED_APP_CACHE, "Release page checks the release app cache"),
            ("app-check-runtime", "runtime-selftest.js", "Release page checks runtime self-test"),
            ("app-check-no-store", "cache:'no-store'", "Release page bypasses caches"),
            ("app-check-read-only", "keine App- oder Browserdaten verändert", "Release page states its read-only behavior"),
        ):
            self.add(check_id, "release-page", token in source, message)

    def check_diagnostics(self) -> None:
        source = read_text(self.root, "app-diagnostics.js")
        self.add(
            "diagnostics-version",
            "diagnostics",
            f"version === '{EXPECTED_VERSION}'" in source,
            f"App diagnostics expects {EXPECTED_VERSION}",
        )
        self.add(
            "diagnostics-no-175",
            "diagnostics",
            "version === '1.7.5'" not in source,
            "App diagnostics no longer expects 1.7.5",
        )

    def check_source_recovery(self) -> None:
        source = read_text(self.root, "source_recovery.py")
        self.add(
            "recovery-threshold",
            "source-recovery",
            "PERMANENT_FAILURE_THRESHOLD = 4" in source,
            "Permanent failure threshold remains 4",
        )
        self.add(
            "recovery-min-age",
            "source-recovery",
            "PERMANENT_FAILURE_MIN_AGE = timedelta(hours=12)" in source,
            "Permanent failure minimum age remains 12 hours",
        )
        self.add(
            "recovery-no-auto-delete",
            "source-recovery",
            '"automaticDeletion": False' in source,
            "Automatic source deletion remains disabled",
        )
        self.add(
            "recovery-registry-guard",
            "source-recovery",
            "never edits or deletes the canonical source registry" in source,
            "Canonical source registry guard remains documented",
        )
        self.add(
            "recovery-no-delete-api",
            "source-recovery",
            "unlink(" not in source and "rmtree(" not in source,
            "Source recovery contains no file deletion API",
        )

    def check_workflows(self) -> None:
        quality = read_text(self.root, ".github/workflows/quality-gate.yml")
        update = read_text(self.root, ".github/workflows/update.yml")
        quality_commands = (
            "python release_audit_183.py",
            "node tests/test_runtime_selftest_183.js",
            "python tests/test_release_candidate_183.py",
            "node tests/test_video_hub.js",
            "python tests/test_video_assets.py",
            "node tests/test_audio_tab_183.js",
            "python tests/test_audio_block2_assets.py",
            "node tests/test_block3_interface.js",
            "node tests/test_block3_runtime.js",
            "python tests/test_block3_assets.py",
            "python tests/test_source_recovery.py",
            "node tests/test_source_recovery_ui.js",
            "python tests/test_source_recovery_assets.py",
            "PYTHONPATH=. python tests/test_audio_source_schema.py",
            "python tests/test_release_182.py",
        )
        for command in quality_commands:
            self.add(
                f"quality-command:{command}",
                "quality-gate",
                command in quality,
                f"Quality gate runs: {command}",
            )
        for token in (
            "app-check.html",
            "runtime-selftest.js",
            "release-readiness-183.json",
        ):
            self.add(
                f"quality-artifact-or-smoke:{token}",
                "quality-gate",
                token in quality,
                f"Quality gate includes {token}",
            )
        for token in ("source-health-history.json", "source-recovery-report.json"):
            self.add(
                f"update-preserves:{token}",
                "update-workflow",
                token in update,
                f"Update workflow preserves {token}",
            )

    def check_header(self) -> None:
        script = read_text(self.root, "wrn-header.js")
        css = read_text(self.root, "wrn-header.css")
        worker = read_text(self.root, "service-worker.js")
        self.add(
            "header-asset-reference",
            "header",
            "wrn-future-header-white.png" in script,
            "Header script uses the white-title transparent banner",
        )
        self.add(
            "header-asset-offline",
            "header",
            "'./wrn-future-header-white.png'" in worker,
            "White-title transparent header banner is in the app shell",
        )
        self.add(
            "header-responsive-size",
            "header",
            "object-fit: contain" in css
            and "aspect-ratio:" in css
            and "max-height" in css,
            "Header banner has bounded responsive sizing",
        )
        self.add(
            "header-accessibility",
            "header",
            "image.alt = '';" in script and "image.setAttribute('aria-hidden', 'true')" in script,
            "Decorative banner does not duplicate the accessible heading",
        )


def run_audit(
    *,
    root: Path = ROOT,
    write_report: bool = True,
) -> dict[str, Any]:
    report = ReleaseAudit(root).run()
    if write_report:
        report_path = root / REPORT_PATH.name
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return report


def main() -> int:
    report = run_audit()
    summary = report["summary"]
    print(
        f"WRN {EXPECTED_VERSION} release audit: "
        f"{summary['pass']} passed, "
        f"{summary['warning']} warnings, "
        f"{summary['fail']} failed, "
        f"{summary['total']} total"
    )
    return 1 if summary["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
