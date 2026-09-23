from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
AUDIT_JSON = ROUTE_DIR / "G12_FPB_RESULT_AUDIT_2026-05-11.json"
VERIFICATION_JSON = ROUTE_DIR / "G12_FPB_AUDIT_VERIFICATION_2026-05-11.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify() -> dict[str, Any]:
    failures: list[str] = []
    if not AUDIT_JSON.exists():
        failures.append(f"missing audit json: {AUDIT_JSON.as_posix()}")
        payload: dict[str, Any] = {}
    else:
        payload = load_json(AUDIT_JSON)

    expected_decision = "ACCEPT_AS_QUARANTINED_DISCOVERY_PATH_BEHAVIOR_LEDGER"
    if payload.get("audit_decision") != expected_decision:
        failures.append(f"audit_decision is not {expected_decision}")
    if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
        failures.append("promotion_verdict is not NO_PROMOTION_VERDICT")
    for flag in ["validation_safe", "outcome_review_opened", "live_effect"]:
        if payload.get(flag) is not False:
            failures.append(f"{flag} is not false")
    for flag in [
        "opens_validation",
        "opens_promotion",
        "opens_result_scoring",
        "opens_paid_api_or_databento_route",
        "opens_mt5_order_account_history_behavior",
        "opens_live_trading_behavior",
        "opens_live_restart",
        "opens_registry_edit",
        "opens_remote_push",
        "credentials_touched",
        "changes_live_trading_behavior",
    ]:
        if payload.get(flag) is not False:
            failures.append(f"{flag} is not false")

    checklist = payload.get("prompt_to_artifact_checklist") or []
    if len(checklist) != 10:
        failures.append(f"expected 10 checklist rows, got {len(checklist)}")
    bad_rows = [row for row in checklist if row.get("status") != "PASS"]
    if bad_rows:
        failures.append(f"non-PASS checklist rows: {bad_rows}")

    count_audit = payload.get("count_audit") or {}
    expected_counts = {
        "raw_candidate_attempts": 13_540_033,
        "duplicate_candidate_keys": 687_275,
        "unique_nonduplicate_candidate_path_label_denominator": 12_852_758,
        "path_label_row_count": 12_852_758,
    }
    if count_audit.get("expected_counts") != expected_counts:
        failures.append("expected count constants mismatch")
    if count_audit.get("passes") is not True:
        failures.append("count audit did not pass")
    if count_audit.get("opened_family_count") != 11:
        failures.append("opened family count is not 11")
    if count_audit.get("baseline_control_family_count") != 4:
        failures.append("baseline control count is not 4")
    if payload.get("label_vocabulary") != [
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH",
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH",
        "MIDPOINT_RETRACE_BEFORE_EXTENSION",
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE",
        "SAME_BAR_CONTEXT_AMBIGUOUS",
        "UNRESOLVED_BY_WINDOW",
        "UNRESOLVED_AT_SOURCE_END",
    ]:
        failures.append("label vocabulary mismatch")

    if payload.get("lfs_materialization_audit", {}).get("passes") is not True:
        failures.append("LFS materialization audit failed")
    if payload.get("blob_size_audit", {}).get("passes") is not True:
        failures.append("blob-size audit failed")
    if payload.get("predecessor_context_anchor_audit", {}).get("all_context_anchor_inputs_exist") is not True:
        failures.append("context-anchor predecessor audit failed")
    noleak = payload.get("no_leak_dirty_state_audit") or {}
    if noleak.get("safe_flag_failures"):
        failures.append("safe flag failures present")
    if noleak.get("forbidden_result_key_hits"):
        failures.append("forbidden result key hits present")
    if noleak.get("surface_diff", {}).get("passes") is not True:
        failures.append("surface diff audit failed")

    if payload.get("completion_standard_satisfied") is not True:
        failures.append("completion standard is not satisfied")
    if payload.get("can_mark_goal_complete") is not True:
        failures.append("can_mark_goal_complete is not true")
    if payload.get("missing_incomplete_or_weak_requirements"):
        failures.append("missing/incomplete/weak requirements are present")

    result = {
        "ok": not failures,
        "can_mark_goal_complete": not failures,
        "failures": failures,
        "audit_decision": payload.get("audit_decision"),
        "promotion_verdict": payload.get("promotion_verdict"),
        "validation_safe": payload.get("validation_safe"),
        "outcome_review_opened": payload.get("outcome_review_opened"),
        "live_effect": payload.get("live_effect"),
    }
    VERIFICATION_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
