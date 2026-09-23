"""Standalone verifier for the G12 READY8 target-result packet audit."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[4]
DATE_TAG = "2026-05-13"
PREFIX = "G12_SCID_NOAPI_READY8_TARGET_RESULT_AUDIT"
ACCEPT_DECISION = "ACCEPT_AS_G12_SCID_NOAPI_READY8_QUARANTINED_TARGET_RESULT_PACKET_CONTROL_EVIDENCE_ONLY"
EVIDENCE_CLASS = "G12_SCID_NOAPI_READY8_QUARANTINED_TARGET_RESULT_PACKET_AUDIT_ONLY"


def repo_path(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def verify() -> dict:
    paths = {
        "recompute": ROUTE_DIR / f"{PREFIX}_RECOMPUTE_AUDIT_{DATE_TAG}.json",
        "decision": ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_{DATE_TAG}.json",
        "verification": ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json",
        "completion": ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json",
        "saturation": ROUTE_DIR / f"{PREFIX}_SATURATION_SELF_RED_TEAM_{DATE_TAG}.md",
        "manifest": ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json",
        "focused": ROUTE_DIR / f"{PREFIX}_FOCUSED_TEST_RESULT_{DATE_TAG}.json",
    }
    missing = [name for name, path in paths.items() if not path.exists()]
    checks = {"required_artifacts_exist": not missing}
    if missing:
        return {"ok": False, "checks": checks, "missing": missing}

    recompute = load_json(paths["recompute"])
    decision = load_json(paths["decision"])
    verification = load_json(paths["verification"])
    completion = load_json(paths["completion"])
    manifest = load_json(paths["manifest"])
    focused = load_json(paths["focused"])

    checks.update(
        {
            "evidence_class_correct": all(
                item.get("evidence_class") == EVIDENCE_CLASS
                for item in [recompute, decision, verification, completion, manifest, focused]
            ),
            "decision_accepts_control_evidence_only": decision.get("terminal_decision") == ACCEPT_DECISION,
            "verification_ok": verification.get("ok") is True,
            "completion_audit_satisfied": completion.get("all_prompt_requirements_satisfied") is True,
            "recompute_ok": recompute.get("ok") is True,
            "focused_tests_passed": focused.get("status") == "passed",
            "safe_flags_closed": all(
                item.get("promotion_verdict") == "NO_PROMOTION_VERDICT"
                and item.get("validation_safe") is False
                and item.get("outcome_review_opened") is False
                and item.get("live_effect") is False
                for item in [recompute, decision, verification, completion, manifest, focused]
            ),
            "manifest_artifacts_exist": all(item.get("exists") and item.get("sha256") for item in manifest.get("artifacts", [])),
            "target_row_count_exact": recompute.get("target_audit", {}).get("target_result_row_count") == 192896,
            "no_recompute_issues": recompute.get("issues") == [],
        }
    )
    issues = [{"check": key, "passed": value} for key, value in checks.items() if not value]
    return {
        "ok": not issues,
        "checks": checks,
        "issues": issues,
        "artifacts": {name: repo_path(path) for name, path in paths.items()},
    }


def main() -> int:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
