#!/usr/bin/env python3
"""Verifier for the G12 HAZ-001 density/waiting-time audit artifacts."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any


DATE_ID = "2026-05-15"
ROUTE_ID = "G12_HAZ001_DENSITY_WAITING_TIME_MECHANISM_EXPANSION_AUDIT"
EVIDENCE_CLASS = "G12_HAZ001_MECHANISM_EXPANSION_AUDIT_ONLY"
ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = Path(__file__).resolve().parent

SAFE_FALSE_KEYS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "changes_trading_risk_safety_prompt_decision_behavior",
    "credentials_touched",
    "opens_ai_api",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_live_restart",
    "opens_live_trading_behavior",
    "opens_paid_or_vendor_access",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "opens_raw_market_data_blob_commit",
    "opens_registry_edit",
    "opens_remote_push",
    "opens_strategy_edge_claims",
]

ARTIFACTS = {
    "recomputation": OUT_DIR / f"G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_RECOMPUTATION_LEDGER_{DATE_ID}.json",
    "discrepancy_repair": OUT_DIR / f"G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_DISCREPANCY_REPAIR_LEDGER_{DATE_ID}.json",
    "decision": OUT_DIR / f"G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_DECISION_LEDGER_{DATE_ID}.json",
    "saturation": OUT_DIR / f"G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_SATURATION_SELF_RED_TEAM_LEDGER_{DATE_ID}.json",
    "completion": OUT_DIR / f"G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_COMPLETION_AUDIT_{DATE_ID}.json",
    "manifest": OUT_DIR / f"G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_OUTPUT_MANIFEST_{DATE_ID}.json",
    "focused": OUT_DIR / f"G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_FOCUSED_TEST_RESULT_{DATE_ID}.json",
}
RESULT_PATH = OUT_DIR / f"G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_VERIFICATION_RESULT_{DATE_ID}.json"


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_flags_closed(obj: dict[str, Any]) -> bool:
    return obj.get("promotion_verdict") == "NO_PROMOTION_VERDICT" and all(obj.get(key) is False for key in SAFE_FALSE_KEYS)


def main() -> int:
    issues: list[str] = []
    checks: dict[str, bool] = {}

    for name, path in ARTIFACTS.items():
        checks[f"{name}_exists"] = path.exists()
        if not path.exists():
            issues.append(f"missing artifact: {rel(path)}")

    if issues:
        result = {
            "schema_version": "g12_haz001_density_waiting_time_audit_verifier_v1",
            "route_id": ROUTE_ID,
            "evidence_class": EVIDENCE_CLASS,
            "generated_at_utc": utc_now(),
            "ok": False,
            "issues": issues,
            "checks": checks,
        }
        RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"ok": False, "issues": issues}, sort_keys=True))
        return 1

    recomputation = load_json(ARTIFACTS["recomputation"])
    discrepancy = load_json(ARTIFACTS["discrepancy_repair"])
    decision = load_json(ARTIFACTS["decision"])
    saturation = load_json(ARTIFACTS["saturation"])
    completion = load_json(ARTIFACTS["completion"])
    manifest = load_json(ARTIFACTS["manifest"])
    focused = load_json(ARTIFACTS["focused"])

    for name, obj in [
        ("recomputation", recomputation),
        ("discrepancy", discrepancy),
        ("decision", decision),
        ("saturation", saturation),
        ("completion", completion),
        ("manifest", manifest),
        ("focused", focused),
    ]:
        checks[f"{name}_safe_flags_closed"] = safe_flags_closed(obj)

    checks["decision_accepted"] = decision.get("accepted") is True
    checks["terminal_decision_no_promotion"] = decision.get("terminal_decision") == "ACCEPT_AS_G12_HAZ001_MECHANISM_EXPANSION_AUDIT_NO_PROMOTION"
    checks["same_g12_zero"] = discrepancy.get("same_g12_repairable_items_remaining") == 0 and completion.get("same_g12_repairable_items_remaining") == 0
    checks["input_counts_exact"] = recomputation["input_recomputation"].get("haz001_target_rows") == 24112 and recomputation["input_recomputation"].get("haz001_rowset_rows") == 3014
    checks["pass_control_recomputed_zero_mismatch"] = recomputation["pass_control_descriptor_recomputation"].get("field_mismatch_count") == 0 and recomputation["pass_control_descriptor_recomputation"].get("recomputed_rows") == recomputation["pass_control_descriptor_recomputation"].get("builder_ledger_rows")
    checks["deconcentration_labels_ok"] = recomputation["deconcentration_label_recomputation"].get("label_mismatch_count") == 0
    checks["fail_closed_labels_ok"] = recomputation["fail_closed_sensitivity_recomputation"].get("label_mismatch_count") == 0
    checks["retest_packet_no_leak"] = not recomputation["retest_packet_audit"].get("forbidden_target_or_outcome_field_counts") and recomputation["retest_packet_audit"].get("rows") == 3014
    checks["source_roots_audited"] = recomputation["source_search_audit"].get("has_sierra_root") is True and recomputation["source_search_audit"].get("has_absolute_local_heavy_root") is True
    checks["manifest_hash_repair_recorded"] = recomputation["manifest_hash_repair"].get("manifest_entries_refreshed_count", 0) > 0
    checks["completion_checklist_all_true"] = all(item.get("satisfied") is True for item in completion.get("prompt_to_artifact_checklist", []))
    checks["saturation_complete"] = saturation["saturation_checks"].get("same_g12_repairable_items_remaining_zero") is True
    checks["focused_tests_passed"] = focused.get("exit_code") == 0 and focused.get("outcome") == "PASSED"

    for key, ok in checks.items():
        if not ok:
            issues.append(f"check failed: {key}")

    result = {
        "schema_version": "g12_haz001_density_waiting_time_audit_verifier_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": utc_now(),
        "ok": not issues,
        "can_mark_goal_complete": not issues,
        "issues": issues,
        "checks": checks,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "changes_trading_risk_safety_prompt_decision_behavior": False,
        "credentials_touched": False,
        "opens_ai_api": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
        "opens_live_restart": False,
        "opens_live_trading_behavior": False,
        "opens_paid_or_vendor_access": False,
        "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
        "opens_raw_market_data_blob_commit": False,
        "opens_registry_edit": False,
        "opens_remote_push": False,
        "opens_strategy_edge_claims": False,
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["ok"], "issues": issues}, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
