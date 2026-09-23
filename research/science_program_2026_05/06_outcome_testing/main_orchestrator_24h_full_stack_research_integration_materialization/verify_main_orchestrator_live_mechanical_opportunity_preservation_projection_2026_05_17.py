"""Verify live-mechanical opportunity-preservation projection."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
ROWS = ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_OPPORTUNITY_PRESERVATION_PROJECTION_ROWS_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_OPPORTUNITY_PRESERVATION_PROJECTION_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_OPPORTUNITY_PRESERVATION_PROJECTION_MANIFEST_{DATE}.json"
VERIFY_OUT = ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECH_OPP_PRES_PROJECTION_VERIFY_RESULT_{DATE}.json"

PREFILL_PROXY_COUNTING = "PROXY_R_OWNED_BY_ENTRY_OFFSET_050R_NOT_DUPLICATED"
FULL_FIELDS = (
    "opportunity_preservation_status",
    "opportunity_owner_row_id",
    "opportunity_owner_source_artifact",
    "opportunity_proxy_reference_status",
    "opportunity_not_independently_countable_reason",
    "opportunity_useful_mechanism",
    "opportunity_downstream_paths",
)
AUDIT_FIELDS = (
    "kill_scope",
    "current_claim",
    "unsupported_reason",
    "what_was_tried",
    "what_could_make_it_work",
    "preserve_as",
    "next_route",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def requires_preservation(row: dict[str, Any]) -> bool:
    branch = str(row.get("branch_decision") or "").upper()
    return (
        isinstance(row.get("missed_opportunity_audit"), dict)
        or row.get("underlying_intelligence_preserved") is True
        or row.get("prefill_proxy_counting_decision") == PREFILL_PROXY_COUNTING
        or branch.startswith(("KILL", "REDESIGN", "SOURCE", "PRESERVE"))
    )


def has_full_preservation(row: dict[str, Any]) -> bool:
    audit = row.get("missed_opportunity_audit")
    return (
        all(row.get(field) not in (None, "", []) for field in FULL_FIELDS)
        and isinstance(row.get("opportunity_downstream_paths"), list)
        and isinstance(audit, dict)
        and all(audit.get(field) not in (None, "", []) for field in AUDIT_FIELDS)
        and row.get("underlying_intelligence_preserved") is True
    )


def main() -> None:
    issues: list[str] = []
    for path in (ROWS, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing:{path.name}")

    rows = read_jsonl(ROWS) if ROWS.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}
    required_rows = [row for row in rows if requires_preservation(row)]
    missing = [row for row in required_rows if not has_full_preservation(row)]
    proxy_values = [value for row in rows if (value := safe_float(row.get("strategy_proxy_r"))) is not None]
    prefill_owner_rows = [
        row for row in rows if row.get("prefill_proxy_counting_decision") == PREFILL_PROXY_COUNTING
    ]
    prefill_refs = [
        value
        for row in prefill_owner_rows
        if (value := safe_float(row.get("opportunity_proxy_r_reference"))) is not None
    ]
    gbpjpy_adverse_rows = [
        row for row in rows if row.get("gbpjpy_long_adverse_avoid_materialization_status")
    ]
    gbpjpy_adverse_saved_refs = [
        value
        for row in gbpjpy_adverse_rows
        if row.get("gbpjpy_long_adverse_avoid_saved_proxy_counted") is True
        and (value := safe_float(row.get("gbpjpy_long_adverse_avoid_saved_proxy_r"))) is not None
    ]
    gbpjpy_adverse_source_required_rows = [
        row
        for row in gbpjpy_adverse_rows
        if row.get("gbpjpy_long_adverse_avoid_materialization_status")
        == "SOURCE_REQUIRED_BEFORE_AVOID_SAVED_R_COUNT"
    ]
    gbpjpy_adverse_interval_rows = [
        row
        for row in gbpjpy_adverse_rows
        if row.get("gbpjpy_long_adverse_avoid_materialization_status")
        == "BOUNDED_AVOID_FILTER_SAVED_R_INTERVAL_NOT_COUNTED"
    ]
    gbpjpy_adverse_interval_low = [
        value
        for row in gbpjpy_adverse_interval_rows
        if (
            value := safe_float(row.get("gbpjpy_long_adverse_avoid_saved_proxy_r_interval_low"))
        )
        is not None
    ]
    gbpjpy_adverse_interval_high = [
        value
        for row in gbpjpy_adverse_interval_rows
        if (
            value := safe_float(row.get("gbpjpy_long_adverse_avoid_saved_proxy_r_interval_high"))
        )
        is not None
    ]
    gbpjpy_adverse_interval_mid = [
        round((low + high) / 2, 8)
        for low, high in zip(gbpjpy_adverse_interval_low, gbpjpy_adverse_interval_high)
    ]
    gbpjpy_adverse_false_positive_rows = [
        row
        for row in gbpjpy_adverse_rows
        if row.get("gbpjpy_long_adverse_avoid_materialization_status")
        == "REDESIGN_AVOID_FILTER_FALSE_POSITIVE_PROXY_REFERENCE"
    ]
    gbpjpy_adverse_unresolved_horizon_rows = [
        row
        for row in gbpjpy_adverse_rows
        if row.get("gbpjpy_long_adverse_avoid_materialization_status")
        == "UNRESOLVED_HORIZON_AVOID_FILTER_REFERENCE_NOT_COUNTED"
    ]
    gbpjpy_adverse_non_saved_refs = [
        value
        for row in gbpjpy_adverse_false_positive_rows
        if (
            value := safe_float(row.get("gbpjpy_long_adverse_avoid_non_saved_proxy_r_reference"))
        )
        is not None
    ]
    gbpjpy_adverse_unresolved_mfe_refs = [
        value
        for row in gbpjpy_adverse_unresolved_horizon_rows
        if (
            value := safe_float(row.get("gbpjpy_long_adverse_unresolved_horizon_mfe_r_reference"))
        )
        is not None
    ]
    gbpjpy_adverse_unresolved_mae_refs = [
        value
        for row in gbpjpy_adverse_unresolved_horizon_rows
        if (
            value := safe_float(row.get("gbpjpy_long_adverse_unresolved_horizon_mae_r_reference"))
        )
        is not None
    ]
    entry_offset_guard_rows = [
        row for row in rows if row.get("entry_offset_concentration_guard_status")
    ]
    entry_offset_no_fill_rows = [
        row
        for row in rows
        if row.get("entry_offset_no_fill_control_status")
        == "CURRENT_050R_FILL_CLAIM_UNSUPPORTED_REDESIGN_PATH_PRESERVED"
    ]
    standalone_fvg_repair_rows = [
        row
        for row in rows
        if row.get("standalone_fvg_current_claim_repair_status")
        == "CONSUMED_REPAIRED_ACTION_DECISION_REFERENCE_ONLY"
    ]
    standalone_fvg_repair_refs = [
        value
        for row in standalone_fvg_repair_rows
        if (value := safe_float(row.get("standalone_fvg_current_claim_proxy_r_reference")))
        is not None
    ]
    standalone_fvg_source_required = [
        row
        for row in rows
        if row.get("branch_decision") == "SOURCE_CAPTURE_REQUIRED_FOR_FVG_SCORER"
    ]
    swing_protected_repair_rows = [
        row for row in rows if row.get("swing_protected_current_claim_repair_status")
    ]
    swing_protected_counted_proxy = [
        value
        for row in swing_protected_repair_rows
        if row.get("swing_protected_current_claim_repair_status")
        == "CONSUMED_REPAIRED_ACTION_DECISION_COUNTED_DEFAULT_OFF_PROXY"
        and (value := safe_float(row.get("strategy_proxy_r"))) is not None
    ]
    swing_protected_reference_proxy = [
        value
        for row in swing_protected_repair_rows
        if row.get("swing_protected_current_claim_repair_status")
        == "CONSUMED_REPAIRED_ACTION_DECISION_REFERENCE_ONLY"
        and (value := safe_float(row.get("swing_protected_current_claim_proxy_r_reference")))
        is not None
    ]
    structural_lock_source_required = [
        row
        for row in rows
        if row.get("branch_decision") == "SOURCE_CAPTURE_REQUIRED_FOR_STRUCTURAL_LOCK_SCORER"
    ]
    swing_cost_rows = [
        row
        for row in rows
        if row.get("swing_protected_current_claim_repair_status")
        == "CONSUMED_REPAIRED_ACTION_DECISION_COUNTED_DEFAULT_OFF_PROXY"
        and row.get("strategy_proxy_r_cost_adjusted_decision_spread") is not None
    ]
    swing_spread_rows = [
        row
        for row in rows
        if row.get("swing_protected_cost_source_status")
        == "TICK_ASK_BID_DECISION_SPREAD_CAPTURED"
    ]
    swing_cost_adjusted = [
        value
        for row in swing_cost_rows
        if (value := safe_float(row.get("strategy_proxy_r_cost_adjusted_decision_spread")))
        is not None
    ]
    swing_spread_2x = [
        value
        for row in swing_cost_rows
        if (value := safe_float(row.get("strategy_proxy_r_spread_2x_stress"))) is not None
    ]
    nas100_depth_rows = [
        row for row in rows if row.get("strategy_id") == "NAS100_NQ_DEPTH_THINNESS_DIAGNOSTIC"
    ]
    nas100_depth_source_repair_rows = [
        row for row in nas100_depth_rows if row.get("depth_thinness_source_repair_status")
    ]
    nas100_depth_source_complete_rows = [
        row
        for row in nas100_depth_source_repair_rows
        if row.get("depth_thinness_source_repair_status")
        == "SIERRA_DEPTH_FEATURES_EXTRACTED_SOURCE_COMPLETE"
    ]
    nas100_depth_no_sample_rows = [
        row
        for row in nas100_depth_source_repair_rows
        if row.get("depth_thinness_source_repair_status")
        == "SIERRA_DEPTH_ATTEMPTED_NO_SAMPLES_SOURCE_COMPLETE_NO_CONTEXT"
    ]
    nas100_depth_heavy_scan_rows = [
        row
        for row in nas100_depth_source_repair_rows
        if row.get("depth_thinness_source_repair_status") == "SIERRA_DEPTH_HEAVY_SCAN_REQUIRED"
    ]
    nas100_depth_waiting_rows = [
        row for row in nas100_depth_rows if row.get("strategy_status") == "WAITING_FOR_DEPTH_FEATURES"
    ]
    fvg_ob_trade_record_bounds_repair_rows = [
        row for row in rows if row.get("fvg_ob_trade_record_bounds_repair_status")
    ]
    fvg_ob_trade_record_bounds_reference_proxy = [
        value
        for row in fvg_ob_trade_record_bounds_repair_rows
        if (value := safe_float(row.get("fvg_ob_current_claim_proxy_r_reference"))) is not None
    ]
    fvg_ob_exact_bounds_required_rows = [
        row
        for row in rows
        if row.get("branch_decision") == "PRESERVE_FVG_OB_BUCKET_BOTH_FIRE_EXACT_BOUNDS_REQUIRED"
    ]
    structural_duplicate_merge_rows = [
        row for row in rows if row.get("structural_duplicate_merge_status")
    ]
    structural_duplicate_proxy_refs = [
        value
        for row in structural_duplicate_merge_rows
        if (value := safe_float(row.get("structural_duplicate_proxy_reference_r"))) is not None
    ]
    structural_duplicate_old_redesign_rows = [
        row
        for row in rows
        if row.get("branch_decision")
        == "REDESIGN_DUPLICATE_STRUCTURAL_LOCK_SHARED_PATH_PROXY_NOT_DISTINCT_IMPLEMENTATION"
    ]
    pending_hypothetical_merge_rows = [
        row for row in rows if row.get("pending_hypothetical_merge_status")
    ]
    pending_hypothetical_proxy_refs = [
        value
        for row in pending_hypothetical_merge_rows
        if (value := safe_float(row.get("pending_hypothetical_proxy_reference_r"))) is not None
    ]
    pending_hypothetical_old_redesign_rows = [
        row
        for row in rows
        if row.get("branch_decision")
        == "REDESIGN_PENDING_LIFECYCLE_HYPOTHETICAL_PATH_PROXY_NOT_DISTINCT"
    ]
    pending_source_partial_rows = [
        row
        for row in rows
        if row.get("branch_decision") == "REDESIGN_PENDING_LIFECYCLE_SOURCE_PARTIAL_REPAIR_REQUIRED"
    ]
    pending_no_entry_no_cost_complete_rows = [
        row
        for row in rows
        if isinstance(row.get("pending_lifecycle_source_capture_statuses"), dict)
        and row["pending_lifecycle_source_capture_statuses"].get("decision_spread_value_source_safe")
        == "NOT_APPLICABLE_NO_ENTRY_TOUCH_NO_SPREAD_COST"
    ]

    if not rows:
        issues.append("projection_rows_empty")
    if summary.get("dry_run_only_no_shadow_append") is not True:
        issues.append("not_marked_dry_run_only")
    if summary.get("rows") != len(rows):
        issues.append("summary_rows_mismatch")
    if summary.get("missing_opportunity_preservation_rows") != 0 or missing:
        issues.append(f"missing_opportunity_preservation:{len(missing)}")
    if summary.get("required_opportunity_preservation_rows") != len(required_rows):
        issues.append("required_row_count_mismatch")
    if summary.get("prefill_owner_reference_rows") != len(prefill_owner_rows):
        issues.append("prefill_owner_rows_mismatch")
    if summary.get("prefill_owner_reference_proxy_rows") != len(prefill_refs):
        issues.append("prefill_proxy_reference_count_mismatch")
    if summary.get("strategy_proxy_rows") != len(proxy_values):
        issues.append("strategy_proxy_count_mismatch")
    if round(sum(proxy_values), 8) != summary.get("strategy_proxy_sum"):
        issues.append("strategy_proxy_sum_mismatch")
    if summary.get("gbpjpy_long_adverse_avoid_rows") != len(gbpjpy_adverse_rows):
        issues.append("gbpjpy_adverse_avoid_rows_mismatch")
    if summary.get("gbpjpy_long_adverse_avoid_saved_proxy_rows") != len(gbpjpy_adverse_saved_refs):
        issues.append("gbpjpy_adverse_saved_proxy_rows_mismatch")
    if summary.get("gbpjpy_long_adverse_avoid_saved_proxy_sum") != round(sum(gbpjpy_adverse_saved_refs), 8):
        issues.append("gbpjpy_adverse_saved_proxy_sum_mismatch")
    if summary.get("gbpjpy_long_adverse_avoid_source_required_rows") != len(
        gbpjpy_adverse_source_required_rows
    ):
        issues.append("gbpjpy_adverse_source_required_rows_mismatch")
    if summary.get("gbpjpy_long_adverse_avoid_interval_rows") != len(
        gbpjpy_adverse_interval_rows
    ):
        issues.append("gbpjpy_adverse_interval_rows_mismatch")
    if summary.get("gbpjpy_long_adverse_avoid_false_positive_rows") != len(
        gbpjpy_adverse_false_positive_rows
    ):
        issues.append("gbpjpy_adverse_false_positive_rows_mismatch")
    if summary.get("gbpjpy_long_adverse_avoid_unresolved_horizon_rows") != len(
        gbpjpy_adverse_unresolved_horizon_rows
    ):
        issues.append("gbpjpy_adverse_unresolved_horizon_rows_mismatch")
    if summary.get("gbpjpy_long_adverse_avoid_interval_low_sum") != round(
        sum(gbpjpy_adverse_interval_low), 8
    ):
        issues.append("gbpjpy_adverse_interval_low_sum_mismatch")
    if summary.get("gbpjpy_long_adverse_avoid_interval_high_sum") != round(
        sum(gbpjpy_adverse_interval_high), 8
    ):
        issues.append("gbpjpy_adverse_interval_high_sum_mismatch")
    if summary.get("gbpjpy_long_adverse_avoid_interval_mid_sum") != round(
        sum(gbpjpy_adverse_interval_mid), 8
    ):
        issues.append("gbpjpy_adverse_interval_mid_sum_mismatch")
    if summary.get("gbpjpy_long_adverse_avoid_non_saved_proxy_reference_sum") != round(
        sum(gbpjpy_adverse_non_saved_refs), 8
    ):
        issues.append("gbpjpy_adverse_non_saved_reference_sum_mismatch")
    if summary.get("gbpjpy_long_adverse_avoid_unresolved_horizon_mfe_reference_sum") != round(
        sum(gbpjpy_adverse_unresolved_mfe_refs), 8
    ):
        issues.append("gbpjpy_adverse_unresolved_mfe_sum_mismatch")
    if summary.get("gbpjpy_long_adverse_avoid_unresolved_horizon_mae_reference_sum") != round(
        sum(gbpjpy_adverse_unresolved_mae_refs), 8
    ):
        issues.append("gbpjpy_adverse_unresolved_mae_sum_mismatch")
    if len(gbpjpy_adverse_source_required_rows) != 0:
        issues.append("gbpjpy_adverse_source_required_rows_expected_0_after_repair")
    if len(gbpjpy_adverse_interval_rows) != 10:
        issues.append("gbpjpy_adverse_interval_rows_expected_10_after_repair")
    if len(gbpjpy_adverse_false_positive_rows) != 1:
        issues.append("gbpjpy_adverse_false_positive_rows_expected_1_after_repair")
    if len(gbpjpy_adverse_unresolved_horizon_rows) != 1:
        issues.append("gbpjpy_adverse_unresolved_horizon_rows_expected_1_after_repair")
    if round(sum(gbpjpy_adverse_interval_low), 8) != -13.5:
        issues.append("gbpjpy_adverse_interval_low_sum_expected_-13_5")
    if round(sum(gbpjpy_adverse_interval_high), 8) != 8.0:
        issues.append("gbpjpy_adverse_interval_high_sum_expected_8_0")
    if round(sum(gbpjpy_adverse_interval_mid), 8) != -2.75:
        issues.append("gbpjpy_adverse_interval_mid_sum_expected_-2_75")
    if round(sum(gbpjpy_adverse_non_saved_refs), 8) != -1.5:
        issues.append("gbpjpy_adverse_false_positive_non_saved_reference_expected_-1_5")
    if round(sum(gbpjpy_adverse_unresolved_mfe_refs), 8) != 1.34482759:
        issues.append("gbpjpy_adverse_unresolved_mfe_reference_expected_1_34482759")
    if round(sum(gbpjpy_adverse_unresolved_mae_refs), 8) != -0.16976127:
        issues.append("gbpjpy_adverse_unresolved_mae_reference_expected_-0_16976127")
    if summary.get("before_gbpjpy_long_adverse_interval_repair_projection_reference", {}).get(
        "source_required_rows"
    ) != 12:
        issues.append("before_gbpjpy_adverse_source_required_reference_mismatch")
    if summary.get("gbpjpy_long_adverse_interval_repair_projection_delta", {}).get(
        "source_required_rows_delta"
    ) != -12:
        issues.append("gbpjpy_adverse_source_required_delta_mismatch")
    if summary.get("gbpjpy_long_adverse_interval_repair_projection_delta", {}).get(
        "bounded_interval_rows_delta"
    ) != 10:
        issues.append("gbpjpy_adverse_interval_delta_mismatch")
    if summary.get("gbpjpy_long_adverse_interval_repair_projection_delta", {}).get(
        "false_positive_rows_delta"
    ) != 1:
        issues.append("gbpjpy_adverse_false_positive_delta_mismatch")
    if summary.get("gbpjpy_long_adverse_interval_repair_projection_delta", {}).get(
        "unresolved_horizon_rows_delta"
    ) != 1:
        issues.append("gbpjpy_adverse_unresolved_horizon_delta_mismatch")
    if summary.get("gbpjpy_long_adverse_interval_repair_projection_delta", {}).get(
        "saved_proxy_rows_delta"
    ) != 0:
        issues.append("gbpjpy_adverse_saved_proxy_rows_delta_mismatch")
    if summary.get("gbpjpy_long_adverse_interval_repair_projection_delta", {}).get(
        "saved_proxy_sum_delta"
    ) != 0.0:
        issues.append("gbpjpy_adverse_saved_proxy_sum_delta_mismatch")
    if summary.get("entry_offset_concentration_guard_rows") != len(entry_offset_guard_rows):
        issues.append("entry_offset_guard_rows_mismatch")
    if summary.get("entry_offset_concentration_guard_owner_rows") != sum(
        1
        for row in entry_offset_guard_rows
        if row.get("entry_offset_concentration_guard_status") == "ENTRY_OFFSET_OWNER_CLUSTER_GUARDED"
    ):
        issues.append("entry_offset_guard_owner_rows_mismatch")
    if summary.get("entry_offset_concentration_guard_prefill_reference_rows") != sum(
        1
        for row in entry_offset_guard_rows
        if row.get("entry_offset_concentration_guard_status") == "PREFILL_REFERENCE_CLUSTER_GUARDED"
    ):
        issues.append("entry_offset_guard_prefill_rows_mismatch")
    if summary.get("entry_offset_no_fill_control_rows") != len(entry_offset_no_fill_rows):
        issues.append("entry_offset_no_fill_control_rows_mismatch")
    if summary.get("entry_offset_no_fill_repair_branch_rows") != len(entry_offset_no_fill_rows):
        issues.append("entry_offset_no_fill_repair_branch_rows_mismatch")
    if entry_offset_no_fill_rows and not all(
        row.get("entry_offset_no_fill_repair_branch_candidate")
        == "REDESIGN_ENTRY_OFFSET_NO_FILL_RETEST_SOURCE_COST_FILL_REPAIR_REQUIRED"
        for row in entry_offset_no_fill_rows
    ):
        issues.append("entry_offset_no_fill_repair_branch_missing")
    if summary.get("standalone_fvg_current_claim_repair_rows") != len(standalone_fvg_repair_rows):
        issues.append("standalone_fvg_repair_rows_mismatch")
    if summary.get("standalone_fvg_current_claim_proxy_reference_rows") != len(standalone_fvg_repair_refs):
        issues.append("standalone_fvg_proxy_reference_rows_mismatch")
    if summary.get("standalone_fvg_current_claim_proxy_reference_sum") != round(
        sum(standalone_fvg_repair_refs), 8
    ):
        issues.append("standalone_fvg_proxy_reference_sum_mismatch")
    if summary.get("standalone_fvg_source_capture_required_rows") != len(standalone_fvg_source_required):
        issues.append("standalone_fvg_source_required_rows_mismatch")
    if standalone_fvg_source_required:
        issues.append(f"standalone_fvg_source_required_unrepaired:{len(standalone_fvg_source_required)}")
    if any(row.get("strategy_proxy_r") is not None for row in standalone_fvg_repair_rows):
        issues.append("standalone_fvg_repair_rows_duplicate_strategy_proxy")
    if standalone_fvg_repair_rows and not all(
        row.get("opportunity_proxy_reference_status")
        == "REFERENCE_ONLY_CURRENT_STANDALONE_FVG_CLAIM_NOT_COUNTED"
        for row in standalone_fvg_repair_rows
    ):
        issues.append("standalone_fvg_reference_status_mismatch")
    if any(row.get("strategy_proxy_r") is not None for row in prefill_owner_rows):
        issues.append("prefill_owner_rows_duplicate_strategy_proxy")
    if prefill_owner_rows and not all(
        row.get("opportunity_proxy_reference_status") == "REFERENCE_ONLY_NOT_COUNTED_DUPLICATE_ENTRY_OFFSET_OWNER"
        for row in prefill_owner_rows
    ):
        issues.append("prefill_owner_reference_status_mismatch")
    if summary.get("swing_protected_current_claim_repair_rows") != len(swing_protected_repair_rows):
        issues.append("swing_protected_repair_rows_mismatch")
    if len(swing_protected_repair_rows) != 274:
        issues.append(f"expected_274_swing_repair_rows_found_{len(swing_protected_repair_rows)}")
    if summary.get("swing_protected_current_claim_counted_proxy_rows") != len(swing_protected_counted_proxy):
        issues.append("swing_protected_counted_proxy_rows_mismatch")
    if summary.get("swing_protected_current_claim_counted_proxy_sum") != round(
        sum(swing_protected_counted_proxy), 8
    ):
        issues.append("swing_protected_counted_proxy_sum_mismatch")
    if summary.get("swing_protected_current_claim_reference_proxy_rows") != len(
        swing_protected_reference_proxy
    ):
        issues.append("swing_protected_reference_proxy_rows_mismatch")
    if summary.get("swing_protected_current_claim_reference_proxy_sum") != round(
        sum(swing_protected_reference_proxy), 8
    ):
        issues.append("swing_protected_reference_proxy_sum_mismatch")
    if summary.get("structural_lock_source_capture_required_rows") != len(structural_lock_source_required):
        issues.append("structural_lock_source_required_rows_mismatch")
    if structural_lock_source_required:
        issues.append(f"structural_lock_source_required_unrepaired:{len(structural_lock_source_required)}")
    if any(
        row.get("swing_protected_current_claim_repair_status")
        == "CONSUMED_REPAIRED_ACTION_DECISION_REFERENCE_ONLY"
        and row.get("strategy_proxy_r") is not None
        for row in swing_protected_repair_rows
    ):
        issues.append("swing_protected_reference_rows_duplicate_strategy_proxy")
    if summary.get("swing_protected_cost_adjusted_rows") != len(swing_cost_rows):
        issues.append("swing_protected_cost_adjusted_rows_mismatch")
    if len(swing_cost_rows) != len(swing_protected_counted_proxy):
        issues.append("swing_protected_counted_rows_missing_cost_adjusted_proxy")
    if summary.get("swing_protected_spread_source_rows") != len(swing_spread_rows):
        issues.append("swing_protected_spread_source_rows_mismatch")
    if summary.get("swing_protected_cost_adjusted_proxy_r_sum") != round(
        sum(swing_cost_adjusted), 8
    ):
        issues.append("swing_protected_cost_adjusted_sum_mismatch")
    if summary.get("swing_protected_spread_2x_stress_proxy_r_sum") != round(
        sum(swing_spread_2x), 8
    ):
        issues.append("swing_protected_spread_2x_stress_sum_mismatch")
    if summary.get("before_swing_repair_projection_reference", {}).get(
        "structural_lock_source_capture_required_rows"
    ) != 190:
        issues.append("before_swing_reference_structural_source_rows_mismatch")
    if summary.get("swing_repair_projection_delta", {}).get(
        "structural_lock_source_capture_required_rows_delta"
    ) != -190:
        issues.append("swing_structural_source_delta_mismatch")
    if summary.get("nas100_depth_thinness_rows") != len(nas100_depth_rows):
        issues.append("nas100_depth_rows_mismatch")
    if summary.get("nas100_depth_source_repair_rows") != len(nas100_depth_source_repair_rows):
        issues.append("nas100_depth_source_repair_rows_mismatch")
    if len(nas100_depth_source_repair_rows) != 72:
        issues.append(f"expected_72_nas100_depth_source_repair_rows_found_{len(nas100_depth_source_repair_rows)}")
    if nas100_depth_waiting_rows:
        issues.append(f"nas100_depth_waiting_rows_not_converted:{len(nas100_depth_waiting_rows)}")
    nas100_depth_path_proxy_rows = [
        row
        for row in nas100_depth_source_repair_rows
        if row.get("strategy_status") == "SCORED_DEPTH_THINNESS_WINDOW_PATH_PROXY"
    ]
    nas100_depth_path_proxy_values = [
        safe_float(row.get("strategy_proxy_r"))
        for row in nas100_depth_path_proxy_rows
        if safe_float(row.get("strategy_proxy_r")) is not None
    ]
    if len(nas100_depth_path_proxy_values) != 65:
        issues.append(f"nas100_depth_path_proxy_rows_expected_65_found_{len(nas100_depth_path_proxy_values)}")
    if round(sum(nas100_depth_path_proxy_values), 8) != 0.0:
        issues.append("nas100_depth_path_proxy_sum_expected_0")
    if summary.get("nas100_depth_proxy_r_rows_counted") != len(nas100_depth_path_proxy_values):
        issues.append("nas100_depth_summary_proxy_r_count_mismatch")
    if summary.get("nas100_depth_repair_projection_delta", {}).get("waiting_for_depth_feature_rows_delta") != -72:
        issues.append("nas100_depth_waiting_delta_mismatch")
    if summary.get("fvg_ob_trade_record_bounds_repair_rows") != len(
        fvg_ob_trade_record_bounds_repair_rows
    ):
        issues.append("fvg_ob_trade_record_bounds_repair_rows_mismatch")
    if len(fvg_ob_trade_record_bounds_repair_rows) != 1:
        issues.append(
            f"expected_1_fvg_ob_trade_record_bounds_repair_row_found_{len(fvg_ob_trade_record_bounds_repair_rows)}"
        )
    if summary.get("fvg_ob_trade_record_bounds_proxy_reference_rows") != len(
        fvg_ob_trade_record_bounds_reference_proxy
    ):
        issues.append("fvg_ob_trade_record_bounds_proxy_reference_rows_mismatch")
    if summary.get("fvg_ob_trade_record_bounds_proxy_reference_sum") != round(
        sum(fvg_ob_trade_record_bounds_reference_proxy), 8
    ):
        issues.append("fvg_ob_trade_record_bounds_proxy_reference_sum_mismatch")
    if any(row.get("strategy_proxy_r") is not None for row in fvg_ob_trade_record_bounds_repair_rows):
        issues.append("fvg_ob_trade_record_bounds_repair_rows_duplicate_strategy_proxy")
    if len(fvg_ob_exact_bounds_required_rows) != 0:
        issues.append(
            f"fvg_ob_exact_bounds_requirement_rows_not_repaired:{len(fvg_ob_exact_bounds_required_rows)}"
        )
    if summary.get("fvg_ob_exact_bounds_requirement_rows_after_repair") != len(
        fvg_ob_exact_bounds_required_rows
    ):
        issues.append("fvg_ob_exact_bounds_requirement_summary_mismatch")
    if summary.get("fvg_ob_trade_record_bounds_repair_projection_delta", {}).get(
        "fvg_ob_exact_bounds_requirement_rows_delta"
    ) != -1:
        issues.append("fvg_ob_trade_record_bounds_requirement_delta_mismatch")
    if fvg_ob_trade_record_bounds_repair_rows and not all(
        row.get("opportunity_proxy_reference_status")
        == "REFERENCE_ONLY_SHARED_PATH_PROXY_NOT_FVG_OB_IMPLEMENTATION"
        for row in fvg_ob_trade_record_bounds_repair_rows
    ):
        issues.append("fvg_ob_trade_record_bounds_reference_status_mismatch")
    if summary.get("structural_duplicate_merge_rows") != len(structural_duplicate_merge_rows):
        issues.append("structural_duplicate_merge_rows_mismatch")
    if len(structural_duplicate_merge_rows) != 822:
        issues.append(
            f"expected_822_structural_duplicate_merge_rows_found_{len(structural_duplicate_merge_rows)}"
        )
    if summary.get("structural_duplicate_proxy_reference_rows") != len(
        structural_duplicate_proxy_refs
    ):
        issues.append("structural_duplicate_proxy_reference_rows_mismatch")
    if summary.get("structural_duplicate_proxy_reference_sum") != round(
        sum(structural_duplicate_proxy_refs), 8
    ):
        issues.append("structural_duplicate_proxy_reference_sum_mismatch")
    if structural_duplicate_old_redesign_rows:
        issues.append(
            f"structural_duplicate_old_redesign_rows_not_merged:{len(structural_duplicate_old_redesign_rows)}"
        )
    if any(row.get("strategy_proxy_r") is not None for row in structural_duplicate_merge_rows):
        issues.append("structural_duplicate_merge_rows_duplicate_strategy_proxy")
    if structural_duplicate_merge_rows and not all(
        row.get("opportunity_proxy_reference_status")
        == "REFERENCE_ONLY_DUPLICATE_STRUCTURAL_LOCK_SHARED_PATH_NOT_COUNTED"
        for row in structural_duplicate_merge_rows
    ):
        issues.append("structural_duplicate_reference_status_mismatch")
    if summary.get("structural_duplicate_merge_projection_delta", {}).get(
        "strategy_proxy_rows_delta"
    ) != -786:
        issues.append("structural_duplicate_strategy_proxy_rows_delta_mismatch")
    if summary.get("structural_duplicate_merge_projection_delta", {}).get(
        "strategy_proxy_sum_delta"
    ) != 15.0:
        issues.append("structural_duplicate_strategy_proxy_sum_delta_mismatch")
    if summary.get("pending_hypothetical_merge_rows") != len(pending_hypothetical_merge_rows):
        issues.append("pending_hypothetical_merge_rows_mismatch")
    if len(pending_hypothetical_merge_rows) != 235:
        issues.append(
            f"expected_235_pending_hypothetical_merge_rows_found_{len(pending_hypothetical_merge_rows)}"
        )
    if summary.get("pending_hypothetical_proxy_reference_rows") != len(
        pending_hypothetical_proxy_refs
    ):
        issues.append("pending_hypothetical_proxy_reference_rows_mismatch")
    if summary.get("pending_hypothetical_proxy_reference_sum") != round(
        sum(pending_hypothetical_proxy_refs), 8
    ):
        issues.append("pending_hypothetical_proxy_reference_sum_mismatch")
    if pending_hypothetical_old_redesign_rows:
        issues.append(
            f"pending_hypothetical_old_redesign_rows_not_merged:{len(pending_hypothetical_old_redesign_rows)}"
        )
    if any(row.get("strategy_proxy_r") is not None for row in pending_hypothetical_merge_rows):
        issues.append("pending_hypothetical_merge_rows_duplicate_strategy_proxy")
    if pending_hypothetical_merge_rows and not all(
        row.get("opportunity_proxy_reference_status")
        == "REFERENCE_ONLY_NO_LIVE_PENDING_LIMIT_INTENT_NOT_COUNTED"
        for row in pending_hypothetical_merge_rows
    ):
        issues.append("pending_hypothetical_reference_status_mismatch")
    if summary.get("pending_hypothetical_merge_projection_delta", {}).get(
        "strategy_proxy_rows_delta"
    ) != -224:
        issues.append("pending_hypothetical_strategy_proxy_rows_delta_mismatch")
    if summary.get("pending_hypothetical_merge_projection_delta", {}).get(
        "strategy_proxy_sum_delta"
    ) != 9.0:
        issues.append("pending_hypothetical_strategy_proxy_sum_delta_mismatch")
    if summary.get("pending_lifecycle_source_partial_rows_after_no_cost_repair") != len(
        pending_source_partial_rows
    ):
        issues.append("pending_lifecycle_source_partial_rows_summary_mismatch")
    if pending_source_partial_rows:
        issues.append(
            f"pending_lifecycle_source_partial_rows_not_repaired:{len(pending_source_partial_rows)}"
        )
    if len(pending_no_entry_no_cost_complete_rows) != 1:
        issues.append(
            "expected_1_pending_no_entry_no_spread_cost_complete_row_found_"
            f"{len(pending_no_entry_no_cost_complete_rows)}"
        )
    if summary.get("pending_lifecycle_no_entry_no_spread_cost_complete_rows") != len(
        pending_no_entry_no_cost_complete_rows
    ):
        issues.append("pending_lifecycle_no_entry_no_spread_cost_complete_rows_summary_mismatch")
    if summary.get("before_pending_no_entry_no_cost_repair_projection_reference", {}).get(
        "pending_lifecycle_source_partial_rows"
    ) != 1:
        issues.append("before_pending_no_entry_no_cost_source_partial_reference_mismatch")
    if summary.get("before_pending_no_entry_no_cost_repair_projection_reference", {}).get(
        "pending_lifecycle_reconstructed_source_scorer_rows"
    ) != 36:
        issues.append("before_pending_no_entry_no_cost_reconstructed_reference_mismatch")
    if summary.get("pending_no_entry_no_cost_repair_projection_delta", {}).get(
        "pending_lifecycle_source_partial_rows_delta"
    ) != -1:
        issues.append("pending_no_entry_no_cost_source_partial_delta_mismatch")
    if summary.get("pending_no_entry_no_cost_repair_projection_delta", {}).get(
        "pending_lifecycle_no_entry_no_spread_cost_complete_rows_delta"
    ) != 1:
        issues.append("pending_no_entry_no_cost_complete_rows_delta_mismatch")
    if manifest.get("output_files", {}).get("rows", {}).get("sha256") != sha256_file(ROWS):
        issues.append("rows_hash_mismatch")
    if manifest.get("output_files", {}).get("summary", {}).get("sha256") != sha256_file(SUMMARY):
        issues.append("summary_hash_mismatch")

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(rows),
        "required_opportunity_preservation_rows": len(required_rows),
        "missing_opportunity_preservation_rows": len(missing),
        "prefill_owner_reference_rows": len(prefill_owner_rows),
        "prefill_owner_reference_proxy_rows": len(prefill_refs),
        "prefill_owner_reference_proxy_sum": round(sum(prefill_refs), 8),
        "strategy_proxy_rows": len(proxy_values),
        "strategy_proxy_sum": round(sum(proxy_values), 8),
        "gbpjpy_long_adverse_avoid_rows": len(gbpjpy_adverse_rows),
        "gbpjpy_long_adverse_avoid_saved_proxy_rows": len(gbpjpy_adverse_saved_refs),
        "gbpjpy_long_adverse_avoid_saved_proxy_sum": round(sum(gbpjpy_adverse_saved_refs), 8),
        "gbpjpy_long_adverse_avoid_source_required_rows": len(
            gbpjpy_adverse_source_required_rows
        ),
        "gbpjpy_long_adverse_avoid_interval_rows": len(gbpjpy_adverse_interval_rows),
        "gbpjpy_long_adverse_avoid_interval_low_sum": round(
            sum(gbpjpy_adverse_interval_low), 8
        ),
        "gbpjpy_long_adverse_avoid_interval_high_sum": round(
            sum(gbpjpy_adverse_interval_high), 8
        ),
        "gbpjpy_long_adverse_avoid_interval_mid_sum": round(
            sum(gbpjpy_adverse_interval_mid), 8
        ),
        "gbpjpy_long_adverse_avoid_false_positive_rows": len(
            gbpjpy_adverse_false_positive_rows
        ),
        "gbpjpy_long_adverse_avoid_non_saved_proxy_reference_sum": round(
            sum(gbpjpy_adverse_non_saved_refs), 8
        ),
        "gbpjpy_long_adverse_avoid_unresolved_horizon_rows": len(
            gbpjpy_adverse_unresolved_horizon_rows
        ),
        "gbpjpy_long_adverse_avoid_unresolved_horizon_mfe_reference_sum": round(
            sum(gbpjpy_adverse_unresolved_mfe_refs), 8
        ),
        "gbpjpy_long_adverse_avoid_unresolved_horizon_mae_reference_sum": round(
            sum(gbpjpy_adverse_unresolved_mae_refs), 8
        ),
        "entry_offset_concentration_guard_rows": len(entry_offset_guard_rows),
        "entry_offset_no_fill_control_rows": len(entry_offset_no_fill_rows),
        "standalone_fvg_current_claim_repair_rows": len(standalone_fvg_repair_rows),
        "standalone_fvg_current_claim_proxy_reference_rows": len(standalone_fvg_repair_refs),
        "standalone_fvg_current_claim_proxy_reference_sum": round(sum(standalone_fvg_repair_refs), 8),
        "standalone_fvg_source_capture_required_rows": len(standalone_fvg_source_required),
        "swing_protected_current_claim_repair_rows": len(swing_protected_repair_rows),
        "swing_protected_current_claim_counted_proxy_rows": len(swing_protected_counted_proxy),
        "swing_protected_current_claim_counted_proxy_sum": round(
            sum(swing_protected_counted_proxy), 8
        ),
        "swing_protected_current_claim_reference_proxy_rows": len(swing_protected_reference_proxy),
        "swing_protected_current_claim_reference_proxy_sum": round(
            sum(swing_protected_reference_proxy), 8
        ),
        "structural_lock_source_capture_required_rows": len(structural_lock_source_required),
        "swing_protected_cost_adjusted_rows": len(swing_cost_rows),
        "swing_protected_spread_source_rows": len(swing_spread_rows),
        "swing_protected_cost_adjusted_proxy_r_sum": round(sum(swing_cost_adjusted), 8),
        "swing_protected_spread_2x_stress_proxy_r_sum": round(sum(swing_spread_2x), 8),
        "nas100_depth_source_repair_rows": len(nas100_depth_source_repair_rows),
        "nas100_depth_source_complete_context_rows": len(nas100_depth_source_complete_rows),
        "nas100_depth_no_sample_redesign_rows": len(nas100_depth_no_sample_rows),
        "nas100_depth_heavy_scan_source_required_rows": len(nas100_depth_heavy_scan_rows),
        "nas100_depth_waiting_rows_after_repair": len(nas100_depth_waiting_rows),
        "nas100_depth_path_proxy_rows": len(nas100_depth_path_proxy_values),
        "nas100_depth_path_proxy_sum": round(sum(nas100_depth_path_proxy_values), 8),
        "fvg_ob_trade_record_bounds_repair_rows": len(fvg_ob_trade_record_bounds_repair_rows),
        "fvg_ob_trade_record_bounds_proxy_reference_rows": len(
            fvg_ob_trade_record_bounds_reference_proxy
        ),
        "fvg_ob_trade_record_bounds_proxy_reference_sum": round(
            sum(fvg_ob_trade_record_bounds_reference_proxy), 8
        ),
        "fvg_ob_exact_bounds_requirement_rows_after_repair": len(
            fvg_ob_exact_bounds_required_rows
        ),
        "structural_duplicate_merge_rows": len(structural_duplicate_merge_rows),
        "structural_duplicate_proxy_reference_rows": len(structural_duplicate_proxy_refs),
        "structural_duplicate_proxy_reference_sum": round(
            sum(structural_duplicate_proxy_refs), 8
        ),
        "structural_duplicate_old_redesign_rows_after_merge": len(
            structural_duplicate_old_redesign_rows
        ),
        "pending_hypothetical_merge_rows": len(pending_hypothetical_merge_rows),
        "pending_hypothetical_proxy_reference_rows": len(pending_hypothetical_proxy_refs),
        "pending_hypothetical_proxy_reference_sum": round(
            sum(pending_hypothetical_proxy_refs), 8
        ),
        "pending_hypothetical_old_redesign_rows_after_merge": len(
            pending_hypothetical_old_redesign_rows
        ),
        "pending_lifecycle_source_partial_rows_after_no_cost_repair": len(
            pending_source_partial_rows
        ),
        "pending_lifecycle_no_entry_no_spread_cost_complete_rows": len(
            pending_no_entry_no_cost_complete_rows
        ),
        "dry_run_only_no_shadow_append": summary.get("dry_run_only_no_shadow_append"),
    }
    VERIFY_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
