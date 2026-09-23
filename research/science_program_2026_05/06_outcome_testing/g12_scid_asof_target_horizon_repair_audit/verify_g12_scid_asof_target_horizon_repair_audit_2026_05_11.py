#!/usr/bin/env python3
"""Verify the G12 SCID target/horizon repair audit artifacts."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-11"
ROUTE_ID = "G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT"
EVIDENCE_CLASS = "G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_ONLY"
RESULT_PATH = ROUTE_DIR / f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_VERIFICATION_RESULT_{DATE_TAG}.json"
FORBIDDEN_EXTENSIONS = {".scid", ".parquet", ".csv", ".dly", ".bin"}

REQUIRED_FILES = [
    f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_CONTEXT_ANCHOR_{DATE_TAG}.json",
    f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_CONTEXT_ANCHOR_{DATE_TAG}.md",
    f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_PREDECESSOR_BLOCKER_REVIEW_{DATE_TAG}.json",
    f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_COUNT_RECONCILIATION_{DATE_TAG}.json",
    f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_RULEBOOK_REVIEW_{DATE_TAG}.json",
    f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_FAMILY_MATRIX_REVIEW_{DATE_TAG}.json",
    f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_SOURCE_FIELD_CONTRACT_REVIEW_{DATE_TAG}.json",
    f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_NOLEAK_FORBIDDEN_REVIEW_{DATE_TAG}.json",
    f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_RAW_BLOB_DIRTY_STATE_{DATE_TAG}.json",
    f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_SATURATION_REDTEAM_{DATE_TAG}.json",
    f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_DECISION_LEDGER_{DATE_TAG}.json",
    f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_DECISION_LEDGER_{DATE_TAG}.md",
    f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_COMPLETION_AUDIT_{DATE_TAG}.json",
    f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_COMPLETION_AUDIT_{DATE_TAG}.md",
    f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_OUTPUT_MANIFEST_{DATE_TAG}.json",
    "build_g12_scid_asof_target_horizon_repair_audit_2026_05_11.py",
    "verify_g12_scid_asof_target_horizon_repair_audit_2026_05_11.py",
    "test_g12_scid_asof_target_horizon_repair_audit_2026_05_11.py",
]


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def load(name: str) -> dict[str, Any]:
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def git_status_short() -> list[str]:
    proc = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True, check=False)
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if proc.stderr:
        lines.extend([f"stderr: {line}" for line in proc.stderr.splitlines() if line.strip()])
    return lines


def safe_flags_closed(payload: dict[str, Any]) -> bool:
    false_keys = [
        "validation_safe",
        "outcome_review_opened",
        "live_effect",
        "changes_live_trading_behavior",
        "credentials_touched",
        "opens_ai_api",
        "opens_broker_account_order_history_deal_position_evidence",
        "opens_live_trading_behavior",
        "opens_paid_or_vendor_access",
        "opens_prompt_config_risk_safety_execution_canary_selector_edit",
        "opens_raw_market_data_blob_commit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
    ]
    return (
        payload.get("route_id") == ROUTE_ID
        and payload.get("evidence_class") == EVIDENCE_CLASS
        and payload.get("promotion_verdict") == "NO_PROMOTION_VERDICT"
        and all(payload.get(key) is False for key in false_keys)
    )


def main() -> None:
    issues: list[str] = []
    checks: dict[str, bool] = {}

    required_paths = [ROUTE_DIR / name for name in REQUIRED_FILES]
    checks["required_files_exist"] = all(path.exists() for path in required_paths)
    if not checks["required_files_exist"]:
        issues.append(f"missing required files: {[rel(path) for path in required_paths if not path.exists()]}")

    parsed: dict[str, dict[str, Any]] = {}
    for path in required_paths:
        if path.suffix == ".json" and path.exists():
            try:
                parsed[path.name] = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                issues.append(f"json parse failed for {rel(path)}: {exc}")
    checks["json_parse_ok"] = not any(issue.startswith("json parse failed") for issue in issues)

    json_payloads = list(parsed.values())
    checks["safe_flags_closed"] = bool(json_payloads) and all(safe_flags_closed(payload) for payload in json_payloads)

    predecessor = parsed.get(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_PREDECESSOR_BLOCKER_REVIEW_{DATE_TAG}.json", {})
    counts = parsed.get(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_COUNT_RECONCILIATION_{DATE_TAG}.json", {})
    rulebook = parsed.get(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_RULEBOOK_REVIEW_{DATE_TAG}.json", {})
    family = parsed.get(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_FAMILY_MATRIX_REVIEW_{DATE_TAG}.json", {})
    source = parsed.get(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_SOURCE_FIELD_CONTRACT_REVIEW_{DATE_TAG}.json", {})
    noleak = parsed.get(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_NOLEAK_FORBIDDEN_REVIEW_{DATE_TAG}.json", {})
    raw_dirty = parsed.get(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_RAW_BLOB_DIRTY_STATE_{DATE_TAG}.json", {})
    saturation = parsed.get(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_SATURATION_REDTEAM_{DATE_TAG}.json", {})
    decision = parsed.get(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_DECISION_LEDGER_{DATE_TAG}.json", {})
    completion = parsed.get(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_COMPLETION_AUDIT_{DATE_TAG}.json", {})
    manifest = parsed.get(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_OUTPUT_MANIFEST_{DATE_TAG}.json", {})

    checks["reviews_pass"] = all(
        review.get("pass") is True for review in [predecessor, counts, rulebook, family, source, noleak, raw_dirty, saturation]
    )
    checks["decision_accepts_source_control_only"] = (
        decision.get("terminal_decision") == "ACCEPT_AS_G12_SOURCE_SAFE_NEUTRAL_TARGET_RULEBOOK_CONTROL_EVIDENCE_ONLY"
        and decision.get("accepted_source_safe_neutral_target_rulebook_only") is True
        and decision.get("accepted_strategy_family_execution") is False
        and decision.get("accepted_validation_execution") is False
        and decision.get("accepted_result_scoring") is False
        and decision.get("accepted_promotion") is False
    )
    checks["completion_can_mark_complete"] = completion.get("can_mark_goal_complete") is True
    checks["exact_counts_verified"] = counts.get("actual_counts", {}) == counts.get("expected_counts", {})
    checks["family_statuses_safe"] = family.get("status_counts", {}) == {
        "CONTROL_ONLY": 4,
        "SOURCE_SAFE_NEUTRAL_TARGET_ONLY": 7,
    }
    checks["rulebook_neutral_horizons"] = rulebook.get("horizon_set_m15_bars") == [1, 4, 16, 32]
    checks["source_contract_strategy_blockers_exact"] = source.get("checks", {}).get(
        "strategy_expansion_requirements_exact"
    ) is True
    checks["noleak_no_results"] = noleak.get("checks", {}).get("noleak_flags_no_result_or_performance") is True
    checks["raw_dirty_pass"] = raw_dirty.get("raw_blob_audit_pass") is True and raw_dirty.get("scoped_dirty_state_pass") is True
    checks["manifest_has_artifacts"] = manifest.get("artifact_count", 0) >= 17
    route_files = [path for path in ROUTE_DIR.rglob("*") if path.is_file()]
    checks["audit_route_has_no_raw_blobs"] = not any(path.suffix.lower() in FORBIDDEN_EXTENSIONS for path in route_files)

    for key, value in checks.items():
        if not value:
            issues.append(f"check failed: {key}")

    output = {
        "route_id": ROUTE_ID,
        "schema_version": "g12_scid_asof_target_horizon_repair_audit_v1",
        "artifact_family": "verification_result",
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "changes_live_trading_behavior": False,
        "credentials_touched": False,
        "opens_ai_api": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
        "opens_live_trading_behavior": False,
        "opens_paid_or_vendor_access": False,
        "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
        "opens_raw_market_data_blob_commit": False,
        "opens_remote_push": False,
        "opens_result_scoring": False,
        "opens_validation": False,
        "ok": not issues,
        "checks": checks,
        "issues": issues,
        "git_status_short_informational": git_status_short(),
        "can_mark_goal_complete_after_commit_and_closeout": not issues,
    }
    RESULT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": output["ok"], "issues": issues}, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
