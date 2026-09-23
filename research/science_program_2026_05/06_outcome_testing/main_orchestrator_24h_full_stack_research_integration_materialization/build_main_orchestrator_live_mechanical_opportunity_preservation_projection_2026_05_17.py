"""Materialize current live-mechanical opportunity-preservation projection."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.live_mechanical_shadow import (
    DEFAULT_CANDIDATES,
    DEFAULT_FVG_OB_CONFLUENCE,
    DEFAULT_FVG_OB_TRADE_RECORD_BOUNDS_REPAIRS,
    DEFAULT_LTF_PATH_ORDER,
    DEFAULT_MOONSHOT_SELECTED_ACTION_SOURCE_CAPTURE,
    DEFAULT_NAS100_DEPTH_THINNESS_SOURCE_REPAIRS,
    DEFAULT_NOFILL_FORWARD_SOURCE_CAPTURE,
    DEFAULT_PATHS,
    DEFAULT_PENDING_LIFECYCLE,
    DEFAULT_PENDING_TICK_SPREAD_RECONSTRUCTION,
    DEFAULT_STANDALONE_FVG_REPAIR_DECISIONS,
    DEFAULT_STRUCTURAL_METADATA,
    DEFAULT_SWING_PROTECTED_REPAIR_DECISIONS,
    run,
)


ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
TICK_ROOT = Path("data/ticks")

ROWS = ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_OPPORTUNITY_PRESERVATION_PROJECTION_ROWS_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_OPPORTUNITY_PRESERVATION_PROJECTION_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_OPPORTUNITY_PRESERVATION_PROJECTION_MANIFEST_{DATE}.json"

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


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def parse_utc(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def decision_time_from_row(row: dict[str, Any]) -> datetime | None:
    direct = parse_utc(row.get("decision_time_utc"))
    if direct is not None:
        return direct
    candidate_id = str(row.get("candidate_id") or "")
    symbol = str(row.get("symbol") or "")
    prefix = f"{symbol}_"
    if symbol and candidate_id.startswith(prefix):
        return parse_utc(candidate_id[len(prefix) :])
    return None


def attach_swing_spread_cost(rows: list[dict[str, Any]]) -> None:
    tick_cache: dict[tuple[str, str], pd.DataFrame | None] = {}

    def day_ticks(symbol: str, day: str) -> pd.DataFrame | None:
        key = (symbol, day)
        if key in tick_cache:
            return tick_cache[key]
        path = TICK_ROOT / symbol / f"{day}.parquet"
        if not path.exists():
            tick_cache[key] = None
            return None
        try:
            table = pq.read_table(path, columns=["ts_utc", "bid", "ask"])
            frame = table.to_pandas().dropna(subset=["ts_utc", "bid", "ask"])
        except Exception:
            tick_cache[key] = None
            return None
        frame = frame.sort_values("ts_utc")
        tick_cache[key] = frame
        return frame

    for row in rows:
        if row.get("swing_protected_current_claim_repair_status") != (
            "CONSUMED_REPAIRED_ACTION_DECISION_COUNTED_DEFAULT_OFF_PROXY"
        ):
            continue
        gross_proxy = safe_float(row.get("strategy_proxy_r"))
        path_metrics = row.get("path_metrics") if isinstance(row.get("path_metrics"), dict) else {}
        risk_price = safe_float(path_metrics.get("base_r_price"))
        decision_time = decision_time_from_row(row)
        symbol = str(row.get("symbol") or "")
        if gross_proxy is None or risk_price is None or risk_price <= 0:
            row["swing_protected_cost_source_status"] = "MISSING_GROSS_PROXY_OR_RISK_PRICE"
            continue
        outcome = str(row.get("outcome_status") or "")
        entry_touched = outcome.startswith("ENTRY_TOUCHED")
        if not entry_touched:
            row["swing_protected_cost_source_status"] = "NO_ENTRY_TOUCH_NO_SPREAD_COST_APPLIED"
            row["swing_protected_entry_touched_for_cost"] = False
            row["strategy_proxy_r_cost_adjusted_decision_spread"] = round(gross_proxy, 10)
            row["strategy_proxy_r_spread_2x_stress"] = round(gross_proxy, 10)
            continue
        if decision_time is None or not symbol:
            row["swing_protected_cost_source_status"] = "MISSING_DECISION_TIME_OR_SYMBOL"
            continue
        ticks = day_ticks(symbol, decision_time.date().isoformat())
        if ticks is None or ticks.empty:
            row["swing_protected_cost_source_status"] = "TICK_ASK_BID_SOURCE_NOT_AVAILABLE"
            continue
        eligible = ticks[ticks["ts_utc"] <= pd.Timestamp(decision_time)]
        if eligible.empty:
            row["swing_protected_cost_source_status"] = "NO_TICK_AT_OR_BEFORE_DECISION_TIME"
            continue
        tick = eligible.iloc[-1]
        bid = safe_float(tick.get("bid"))
        ask = safe_float(tick.get("ask"))
        if bid is None or ask is None or ask < bid:
            row["swing_protected_cost_source_status"] = "INVALID_TICK_BID_ASK"
            continue
        spread = ask - bid
        spread_r = spread / risk_price
        row["swing_protected_cost_source_status"] = "TICK_ASK_BID_DECISION_SPREAD_CAPTURED"
        row["swing_protected_cost_tick_ts_utc"] = pd.Timestamp(tick.get("ts_utc")).isoformat()
        row["swing_protected_cost_tick_source_path"] = str(
            TICK_ROOT / symbol / f"{decision_time.date().isoformat()}.parquet"
        )
        row["swing_protected_decision_spread"] = round(spread, 10)
        row["swing_protected_decision_spread_r"] = round(spread_r, 10)
        row["swing_protected_entry_touched_for_cost"] = True
        row["strategy_proxy_r_cost_adjusted_decision_spread"] = round(
            gross_proxy - spread_r, 10
        )
        row["strategy_proxy_r_spread_2x_stress"] = round(
            gross_proxy - (2.0 * spread_r), 10
        )


def mean(values: list[float]) -> float | None:
    return None if not values else round(sum(values) / len(values), 8)


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


def input_manifest() -> dict[str, Any]:
    files = {
        "candidates": DEFAULT_CANDIDATES,
        "paths": DEFAULT_PATHS,
        "pending_lifecycle": DEFAULT_PENDING_LIFECYCLE,
        "ltf_path_order": DEFAULT_LTF_PATH_ORDER,
        "fvg_ob_confluence": DEFAULT_FVG_OB_CONFLUENCE,
        "structural_metadata": DEFAULT_STRUCTURAL_METADATA,
        "nofill_forward_source_capture": DEFAULT_NOFILL_FORWARD_SOURCE_CAPTURE,
        "moonshot_selected_action_source_capture": DEFAULT_MOONSHOT_SELECTED_ACTION_SOURCE_CAPTURE,
        "pending_tick_spread_reconstruction": DEFAULT_PENDING_TICK_SPREAD_RECONSTRUCTION,
        "standalone_fvg_repair_decisions": DEFAULT_STANDALONE_FVG_REPAIR_DECISIONS,
        "swing_protected_repair_decisions": DEFAULT_SWING_PROTECTED_REPAIR_DECISIONS,
        "nas100_depth_thinness_source_repairs": DEFAULT_NAS100_DEPTH_THINNESS_SOURCE_REPAIRS,
        "fvg_ob_trade_record_bounds_repairs": DEFAULT_FVG_OB_TRADE_RECORD_BOUNDS_REPAIRS,
    }
    return {
        name: {
            "path": str(path),
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "sha256": sha256_file(path),
        }
        for name, path in files.items()
    }


def main() -> None:
    generated = utc_now()
    inputs = input_manifest()
    run_summary = run(
        dry_run=True,
        dry_run_output_path=ROWS,
        latest_paths_only=True,
    )
    rows = read_jsonl(ROWS)
    attach_swing_spread_cost(rows)
    with ROWS.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
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
    structural_lock_source_required_rows = [
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
    swing_spread_r = [
        value
        for row in swing_spread_rows
        if (value := safe_float(row.get("swing_protected_decision_spread_r"))) is not None
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
    swing_symbol_split: dict[str, dict[str, Any]] = {}
    for symbol in sorted({str(row.get("symbol") or "") for row in swing_cost_rows}):
        symbol_rows = [row for row in swing_cost_rows if str(row.get("symbol") or "") == symbol]
        gross = [safe_float(row.get("strategy_proxy_r")) for row in symbol_rows]
        cost = [
            safe_float(row.get("strategy_proxy_r_cost_adjusted_decision_spread"))
            for row in symbol_rows
        ]
        stress = [safe_float(row.get("strategy_proxy_r_spread_2x_stress")) for row in symbol_rows]
        gross_values = [value for value in gross if value is not None]
        cost_values = [value for value in cost if value is not None]
        stress_values = [value for value in stress if value is not None]
        swing_symbol_split[symbol] = {
            "rows": len(symbol_rows),
            "gross_proxy_r_sum": round(sum(gross_values), 8),
            "cost_adjusted_proxy_r_sum": round(sum(cost_values), 8),
            "spread_2x_stress_proxy_r_sum": round(sum(stress_values), 8),
        }
    summary = {
        "route_id": ROUTE_ID,
        "date": DATE,
        "generated_utc": generated,
        "rows": len(rows),
        "run_summary": run_summary,
        "latest_paths_only": True,
        "dry_run_only_no_shadow_append": True,
        "required_opportunity_preservation_rows": len(required_rows),
        "missing_opportunity_preservation_rows": len(missing),
        "rows_with_full_opportunity_preservation": len(required_rows) - len(missing),
        "prefill_owner_reference_rows": len(prefill_owner_rows),
        "prefill_owner_reference_proxy_rows": len(prefill_refs),
        "prefill_owner_reference_proxy_sum": round(sum(prefill_refs), 8),
        "gbpjpy_long_adverse_avoid_rows": len(gbpjpy_adverse_rows),
        "gbpjpy_long_adverse_avoid_status_counts": dict(
            sorted(
                Counter(
                    str(row.get("gbpjpy_long_adverse_avoid_materialization_status") or "")
                    for row in gbpjpy_adverse_rows
                ).items()
            )
        ),
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
        "before_gbpjpy_long_adverse_interval_repair_projection_reference": {
            "source_required_rows": 12,
            "bounded_interval_rows": 0,
            "false_positive_rows": 0,
            "unresolved_horizon_rows": 0,
            "saved_proxy_rows": 11,
            "saved_proxy_sum": 11.0,
        },
        "gbpjpy_long_adverse_interval_repair_projection_delta": {
            "source_required_rows_delta": len(gbpjpy_adverse_source_required_rows) - 12,
            "bounded_interval_rows_delta": len(gbpjpy_adverse_interval_rows),
            "false_positive_rows_delta": len(gbpjpy_adverse_false_positive_rows),
            "unresolved_horizon_rows_delta": len(gbpjpy_adverse_unresolved_horizon_rows),
            "saved_proxy_rows_delta": len(gbpjpy_adverse_saved_refs) - 11,
            "saved_proxy_sum_delta": round(sum(gbpjpy_adverse_saved_refs) - 11.0, 8),
        },
        "entry_offset_concentration_guard_rows": len(entry_offset_guard_rows),
        "entry_offset_concentration_guard_status_counts": dict(
            sorted(
                Counter(
                    str(row.get("entry_offset_concentration_guard_status") or "")
                    for row in entry_offset_guard_rows
                ).items()
            )
        ),
        "entry_offset_concentration_guard_owner_rows": sum(
            1
            for row in entry_offset_guard_rows
            if row.get("entry_offset_concentration_guard_status") == "ENTRY_OFFSET_OWNER_CLUSTER_GUARDED"
        ),
        "entry_offset_concentration_guard_prefill_reference_rows": sum(
            1
            for row in entry_offset_guard_rows
            if row.get("entry_offset_concentration_guard_status") == "PREFILL_REFERENCE_CLUSTER_GUARDED"
        ),
        "entry_offset_no_fill_control_rows": len(entry_offset_no_fill_rows),
        "entry_offset_no_fill_repair_branch_rows": sum(
            1
            for row in entry_offset_no_fill_rows
            if row.get("entry_offset_no_fill_repair_branch_candidate")
            == "REDESIGN_ENTRY_OFFSET_NO_FILL_RETEST_SOURCE_COST_FILL_REPAIR_REQUIRED"
        ),
        "standalone_fvg_current_claim_repair_rows": len(standalone_fvg_repair_rows),
        "standalone_fvg_current_claim_proxy_reference_rows": len(standalone_fvg_repair_refs),
        "standalone_fvg_current_claim_proxy_reference_sum": round(
            sum(standalone_fvg_repair_refs), 8
        ),
        "standalone_fvg_source_capture_required_rows": sum(
            1
            for row in rows
            if row.get("branch_decision") == "SOURCE_CAPTURE_REQUIRED_FOR_FVG_SCORER"
        ),
        "swing_protected_current_claim_repair_rows": len(swing_protected_repair_rows),
        "swing_protected_current_claim_counted_proxy_rows": len(swing_protected_counted_proxy),
        "swing_protected_current_claim_counted_proxy_sum": round(
            sum(swing_protected_counted_proxy), 8
        ),
        "swing_protected_current_claim_reference_proxy_rows": len(
            swing_protected_reference_proxy
        ),
        "swing_protected_current_claim_reference_proxy_sum": round(
            sum(swing_protected_reference_proxy), 8
        ),
        "structural_lock_source_capture_required_rows": len(structural_lock_source_required_rows),
        "before_swing_repair_projection_reference": {
            "strategy_proxy_rows": 2126,
            "strategy_proxy_sum": -10.5,
            "structural_lock_source_capture_required_rows": 190,
        },
        "swing_repair_projection_delta": {
            "strategy_proxy_rows_delta": len(proxy_values) - 2126,
            "strategy_proxy_sum_delta": round(sum(proxy_values) - (-10.5), 8),
            "structural_lock_source_capture_required_rows_delta": len(
                structural_lock_source_required_rows
            )
            - 190,
        },
        "swing_protected_cost_adjusted_rows": len(swing_cost_rows),
        "swing_protected_spread_source_rows": len(swing_spread_rows),
        "swing_protected_cost_source_status_counts": dict(
            sorted(
                Counter(
                    str(row.get("swing_protected_cost_source_status") or "")
                    for row in swing_protected_repair_rows
                    if row.get("swing_protected_current_claim_repair_status")
                    == "CONSUMED_REPAIRED_ACTION_DECISION_COUNTED_DEFAULT_OFF_PROXY"
                ).items()
            )
        ),
        "swing_protected_cost_adjusted_proxy_r_sum": round(sum(swing_cost_adjusted), 8),
        "swing_protected_cost_adjusted_proxy_r_mean": mean(swing_cost_adjusted),
        "swing_protected_spread_2x_stress_proxy_r_sum": round(sum(swing_spread_2x), 8),
        "swing_protected_spread_2x_stress_proxy_r_mean": mean(swing_spread_2x),
        "swing_protected_decision_spread_r_mean": mean(swing_spread_r),
        "swing_protected_cost_symbol_split": swing_symbol_split,
        "nas100_depth_thinness_rows": len(nas100_depth_rows),
        "nas100_depth_source_repair_rows": len(nas100_depth_source_repair_rows),
        "nas100_depth_source_complete_context_rows": len(nas100_depth_source_complete_rows),
        "nas100_depth_no_sample_redesign_rows": len(nas100_depth_no_sample_rows),
        "nas100_depth_heavy_scan_source_required_rows": len(nas100_depth_heavy_scan_rows),
        "nas100_depth_waiting_rows_after_repair": sum(
            1 for row in nas100_depth_rows if row.get("strategy_status") == "WAITING_FOR_DEPTH_FEATURES"
        ),
        "before_nas100_depth_repair_projection_reference": {
            "waiting_for_depth_feature_rows": 72,
            "scored_context_attached_rows": 2,
        },
        "nas100_depth_repair_projection_delta": {
            "waiting_for_depth_feature_rows_delta": sum(
                1
                for row in nas100_depth_rows
                if row.get("strategy_status") == "WAITING_FOR_DEPTH_FEATURES"
            )
            - 72,
            "source_complete_context_rows_delta": len(nas100_depth_source_complete_rows),
            "no_sample_redesign_rows_delta": len(nas100_depth_no_sample_rows),
            "heavy_scan_source_required_rows_delta": len(nas100_depth_heavy_scan_rows),
        },
        "nas100_depth_feature_status_counts": dict(
            sorted(
                Counter(
                    str(row.get("depth_thinness_feature_status") or "")
                    for row in nas100_depth_source_repair_rows
                ).items()
            )
        ),
        "nas100_depth_proxy_r_rows_counted": sum(
            1
            for row in nas100_depth_source_repair_rows
            if row.get("strategy_proxy_r") is not None
        ),
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
        "fvg_ob_trade_record_bounds_repair_status_counts": dict(
            sorted(
                Counter(
                    str(row.get("fvg_ob_trade_record_bounds_repair_status") or "")
                    for row in fvg_ob_trade_record_bounds_repair_rows
                ).items()
            )
        ),
        "before_fvg_ob_trade_record_bounds_repair_projection_reference": {
            "fvg_ob_exact_bounds_requirement_rows": 1,
            "fvg_ob_trade_record_bounds_repair_rows": 0,
        },
        "fvg_ob_trade_record_bounds_repair_projection_delta": {
            "fvg_ob_exact_bounds_requirement_rows_delta": len(
                fvg_ob_exact_bounds_required_rows
            )
            - 1,
            "fvg_ob_trade_record_bounds_repair_rows_delta": len(
                fvg_ob_trade_record_bounds_repair_rows
            ),
        },
        "structural_duplicate_merge_rows": len(structural_duplicate_merge_rows),
        "structural_duplicate_proxy_reference_rows": len(structural_duplicate_proxy_refs),
        "structural_duplicate_proxy_reference_sum": round(
            sum(structural_duplicate_proxy_refs), 8
        ),
        "structural_duplicate_old_redesign_rows_after_merge": len(
            structural_duplicate_old_redesign_rows
        ),
        "before_structural_duplicate_merge_projection_reference": {
            "duplicate_redesign_rows": 822,
            "duplicate_strategy_proxy_rows": 786,
            "duplicate_strategy_proxy_sum": -15.0,
            "strategy_proxy_rows": 2223,
            "strategy_proxy_sum": 13.5,
        },
        "structural_duplicate_merge_projection_delta": {
            "duplicate_redesign_rows_delta": len(structural_duplicate_old_redesign_rows)
            - 822,
            "duplicate_merge_rows_delta": len(structural_duplicate_merge_rows),
            "strategy_proxy_rows_delta": -len(structural_duplicate_proxy_refs),
            "strategy_proxy_sum_delta": round(-sum(structural_duplicate_proxy_refs), 8),
        },
        "pending_hypothetical_merge_rows": len(pending_hypothetical_merge_rows),
        "pending_hypothetical_proxy_reference_rows": len(pending_hypothetical_proxy_refs),
        "pending_hypothetical_proxy_reference_sum": round(
            sum(pending_hypothetical_proxy_refs), 8
        ),
        "pending_hypothetical_old_redesign_rows_after_merge": len(
            pending_hypothetical_old_redesign_rows
        ),
        "before_pending_hypothetical_merge_projection_reference": {
            "pending_hypothetical_redesign_rows": 235,
            "pending_hypothetical_strategy_proxy_rows": 224,
            "pending_hypothetical_strategy_proxy_sum": -9.0,
            "strategy_proxy_rows": 1437,
            "strategy_proxy_sum": 28.5,
        },
        "pending_hypothetical_merge_projection_delta": {
            "pending_hypothetical_redesign_rows_delta": len(
                pending_hypothetical_old_redesign_rows
            )
            - 235,
            "pending_hypothetical_merge_rows_delta": len(pending_hypothetical_merge_rows),
            "strategy_proxy_rows_delta": -len(pending_hypothetical_proxy_refs),
            "strategy_proxy_sum_delta": round(-sum(pending_hypothetical_proxy_refs), 8),
        },
        "pending_lifecycle_source_partial_rows_after_no_cost_repair": len(
            pending_source_partial_rows
        ),
        "pending_lifecycle_no_entry_no_spread_cost_complete_rows": len(
            pending_no_entry_no_cost_complete_rows
        ),
        "before_pending_no_entry_no_cost_repair_projection_reference": {
            "pending_lifecycle_source_partial_rows": 1,
            "pending_lifecycle_reconstructed_source_scorer_rows": 36,
        },
        "pending_no_entry_no_cost_repair_projection_delta": {
            "pending_lifecycle_source_partial_rows_delta": len(pending_source_partial_rows) - 1,
            "pending_lifecycle_no_entry_no_spread_cost_complete_rows_delta": len(
                pending_no_entry_no_cost_complete_rows
            ),
        },
        "strategy_proxy_rows": len(proxy_values),
        "strategy_proxy_sum": round(sum(proxy_values), 8),
        "branch_decision_counts": dict(sorted(Counter(str(row.get("branch_decision") or "") for row in rows).items())),
        "strategy_status_counts": dict(sorted(Counter(str(row.get("strategy_status") or "") for row in rows).items())),
        "materialization_mode": "dry_run_projection_rows_written_to_route_artifact",
    }
    write_json(SUMMARY, summary)
    manifest = {
        "route_id": ROUTE_ID,
        "date": DATE,
        "generated_utc": generated,
        "description": "Dry-run projection proving live-mechanical scorer emits full opportunity preservation fields.",
        "input_files": inputs,
        "output_files": {
            "rows": {"path": str(ROWS), "rows": len(rows), "size_bytes": ROWS.stat().st_size, "sha256": sha256_file(ROWS)},
            "summary": {"path": str(SUMMARY), "size_bytes": SUMMARY.stat().st_size, "sha256": sha256_file(SUMMARY)},
        },
    }
    write_json(MANIFEST, manifest)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
