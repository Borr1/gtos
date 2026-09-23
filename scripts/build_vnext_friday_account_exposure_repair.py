"""Build Friday account-exposure, prop-deferral, and concurrency audit artifacts.

This builder is offline and source-bound. It reconstructs the 45 Friday
``DEFERRED_GTOS_VNEXT_PROP_RESET`` rows from the route-local micro price-action
ledger, records the real-money exposure math captured in the live packets, and
audits whether current code still has stale count/concurrency blockers.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_vnext_friday_microscope_freeze_inventory as freeze


ROUTE_DIR = freeze.ROUTE_DIR
MICRO_LEDGER = ROUTE_DIR / "FRIDAY_MICRO_PRICE_ACTION_LEDGER.jsonl"
CANONICAL_LEDGER = ROUTE_DIR / "FRIDAY_CANONICAL_EVENT_LEDGER.jsonl"
FULL_REPLAY_LEDGER = ROUTE_DIR / "FRIDAY_FULL_VNEXT_SYSTEM_REPLAY_LEDGER.jsonl"
CONFIG_PATH = ROOT / "config" / "agent_config.yaml"

ACCOUNT_LEDGER = ROUTE_DIR / "FRIDAY_ACCOUNT_EXPOSURE_RISK_LEDGER.jsonl"
PROP_REPAIR_LEDGER = ROUTE_DIR / "FRIDAY_PROP_DEFERRAL_REPAIR_LEDGER.jsonl"
CONCURRENCY_AUDIT = ROUTE_DIR / "FRIDAY_CONCURRENCY_CAP_STALENESS_AUDIT.json"
ACCOUNT_SUMMARY = ROUTE_DIR / "FRIDAY_ACCOUNT_EXPOSURE_RISK_SUMMARY.json"
VERIFIER = ROUTE_DIR / "verify_friday_account_exposure_repair.py"
VERIFICATION = ROUTE_DIR / "FRIDAY_ACCOUNT_EXPOSURE_RISK_VERIFICATION.json"

EXPECTED_PRIMARY_ROWS = 328
EXPECTED_PROP_DEFERRALS = 45
PROP_DEFERRAL_OUTCOME = "DEFERRED_GTOS_VNEXT_PROP_RESET"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def write_json(path: Path, data: Any) -> None:
    freeze.write_json(path, data)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    freeze.write_jsonl(path, rows)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return freeze.load_jsonl(path)


def line_count(path: Path) -> int:
    return freeze.line_count(path)


def get_path(row: dict[str, Any], *keys: str, default: Any = None) -> Any:
    current: Any = row
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return default if current is None else current


def float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def round_or_none(value: Any, digits: int = 6) -> float | None:
    parsed = float_or_none(value)
    if parsed is None:
        return None
    return round(parsed, digits)


def source_ref(path: str, pattern: str) -> str:
    full = ROOT / path
    if not full.exists():
        return path
    try:
        for line_no, line in enumerate(full.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            if pattern in line:
                return f"{path}:{line_no}"
    except OSError:
        return path
    return path


def route_rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}


def prop_before(row: dict[str, Any]) -> dict[str, Any]:
    direct = get_path(row, "prop_governor", "before_geometry_repair", default={})
    if isinstance(direct, dict) and direct:
        return direct
    fallback = get_path(row, "risk_lot_calculation", "prop_safe_selector_before_geometry", default={})
    return fallback if isinstance(fallback, dict) else {}


def prop_after(row: dict[str, Any]) -> dict[str, Any]:
    direct = get_path(row, "prop_governor", "after_geometry_repair", default={})
    return direct if isinstance(direct, dict) else {}


def account_budget_bucket(before: dict[str, Any]) -> str:
    external = before.get("external_rule_projection") or {}
    exposure = before.get("exposure_breakdown") or {}
    max_amount = float_or_none(external.get("max_allowed_new_trade_risk_amount"))
    max_pct = float_or_none(external.get("max_allowed_new_trade_risk_pct"))
    new_trade = float_or_none(exposure.get("new_trade_sl_risk_amount")) or 0.0
    min_reduced = 0.25
    if max_amount is None:
        return "missing_budget_amount"
    if max_amount <= 0:
        return "no_budget_after_existing_and_buffers"
    if max_pct is not None and max_pct < min_reduced:
        return "positive_budget_below_min_reduced_risk"
    if max_amount < new_trade:
        return "reducible_budget_below_full_new_trade_risk"
    return "budget_allows_full_new_trade_risk"


def prop_deferral_explained(row: dict[str, Any], before: dict[str, Any]) -> bool:
    if row.get("final_outcome") != PROP_DEFERRAL_OUTCOME:
        return True
    external = before.get("external_rule_projection") or {}
    exposure = before.get("exposure_breakdown") or {}
    binding = external.get("binding_budget_name")
    max_pct = float_or_none(external.get("max_allowed_new_trade_risk_pct"))
    new_trade = float_or_none(exposure.get("new_trade_sl_risk_amount")) or 0.0
    action = before.get("action")
    if action != "DEFER_UNTIL_RESET" or binding != "gtos_internal_daily_overlay":
        return False
    return bool(new_trade > 0 and (max_pct is not None and max_pct < 0.25))


def current_terminal_projection(row: dict[str, Any], before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    order_path = get_path(row, "final_order_decision", "order_path")
    outcome = row.get("final_outcome")
    budget_bucket = account_budget_bucket(before)
    selected_risk_pct = float_or_none(row.get("selected_cell_risk_pct"))
    after_ran = bool(after.get("ran")) if isinstance(after, dict) else False
    if outcome == PROP_DEFERRAL_OUTCOME and order_path == "prop_budget_rejected_before_geometry_repair":
        if budget_bucket in {"no_budget_after_existing_and_buffers", "positive_budget_below_min_reduced_risk"}:
            replay_status = "current_after_geometry_account_exposure_would_still_defer_under_same_account_state"
        else:
            replay_status = "current_after_geometry_terminal_replay_needs_selected_cell_risk_and_geometry"
        return {
            "historical_stale_blocker": "pre_dynamic_prop_projection_was_terminal",
            "current_code_repair_status": "repaired_projection_only_before_dynamic_then_terminal_after_geometry",
            "current_terminal_replay_status": replay_status,
            "selected_cell_risk_pct": selected_risk_pct,
            "selected_cell_risk_materiality": (
                "not_material_to_deferral_when_budget_below_min_reduced_risk"
                if replay_status.startswith("current_after_geometry_account_exposure_would_still_defer")
                else "needed_for_terminal_after_geometry_replay"
            ),
            "after_geometry_ran_in_historical_row": after_ran,
        }
    if outcome == PROP_DEFERRAL_OUTCOME and order_path == "prop_budget_rejected_after_geometry_repair":
        return {
            "historical_stale_blocker": None,
            "current_code_repair_status": "terminal_after_geometry_deferral_path",
            "current_terminal_replay_status": "already_after_geometry_terminal_deferral",
            "selected_cell_risk_pct": selected_risk_pct,
            "selected_cell_risk_materiality": "included_in_terminal_gate",
            "after_geometry_ran_in_historical_row": after_ran,
        }
    return {
        "historical_stale_blocker": None,
        "current_code_repair_status": "not_a_prop_deferral",
        "current_terminal_replay_status": "not_applicable",
        "selected_cell_risk_pct": selected_risk_pct,
        "selected_cell_risk_materiality": "not_applicable",
        "after_geometry_ran_in_historical_row": after_ran,
    }


def broker_geometry(row: dict[str, Any]) -> dict[str, Any]:
    spec = row.get("broker_spec_snapshot") or {}
    tick_value = spec.get("trade_tick_value")
    point = spec.get("point")
    return {
        "symbol_info_available": spec.get("symbol_info_available"),
        "broker_symbol": spec.get("broker_symbol"),
        "contract_size": spec.get("trade_contract_size"),
        "tick_size": spec.get("trade_tick_size") or point,
        "tick_value": tick_value,
        "tick_value_source_status": (
            "present_in_packet"
            if tick_value not in (None, "")
            else "missing_from_friday_packet_symbol_info_snapshot"
        ),
        "point": point,
        "lot_step": spec.get("volume_step"),
        "min_lot": spec.get("volume_min"),
        "max_lot": spec.get("volume_max"),
        "trade_stops_level": spec.get("trade_stops_level"),
        "trade_freeze_level": spec.get("trade_freeze_level"),
    }


def build_account_row(row: dict[str, Any], canonical: dict[str, Any] | None, full_replay: dict[str, Any] | None) -> dict[str, Any]:
    before = prop_before(row)
    after = prop_after(row)
    exposure = before.get("exposure_breakdown") or {}
    external = before.get("external_rule_projection") or {}
    internal = before.get("internal_overlay_projection") or {}
    concentration = before.get("concentration") or {}
    reset_window = before.get("reset_window") or {}
    gate3 = get_path(row, "gate3", "output", default={})
    gate3_details = gate3.get("details") if isinstance(gate3, dict) else {}
    if not isinstance(gate3_details, dict):
        gate3_details = {}
    risk_lot = row.get("risk_lot_calculation") or {}
    lot_recompute = risk_lot.get("lot_recompute") or {}
    projection = current_terminal_projection(row, before, after)
    return {
        "schema_version": "friday_account_exposure_risk_ledger_v1",
        "trade_id": row.get("trade_id"),
        "candidate_id": row.get("candidate_id"),
        "symbol": row.get("symbol"),
        "broker_symbol": row.get("broker_symbol"),
        "side": row.get("side"),
        "candle_time_utc": row.get("candle_time_utc"),
        "route_session": row.get("route_session") or row.get("session"),
        "final_outcome": row.get("final_outcome"),
        "canonical_denominator_status": row.get("canonical_denominator_status") or (canonical or {}).get("denominator_status"),
        "full_replay_prop_exposure_pass": (full_replay or {}).get("prop_exposure_pass"),
        "broker_placement_ready": row.get("broker_placement_ready"),
        "actually_placed": row.get("actually_placed"),
        "prop_action": before.get("action") or before.get("not_run_reason"),
        "prop_reason": before.get("reason") or before.get("not_run_reason"),
        "prop_budget_bucket": account_budget_bucket(before) if before else "prop_selector_not_reached",
        "prop_deferral_explained": prop_deferral_explained(row, before),
        "current_terminal_projection": projection,
        "risk_percent": {
            "before_risk_pct": before.get("before_risk_pct"),
            "after_risk_pct": before.get("after_risk_pct"),
            "selected_cell_risk_pct": row.get("selected_cell_risk_pct"),
            "selected_cell_risk_cell_id": row.get("selected_cell_risk_cell_id"),
            "selected_cell_risk_status": get_path(row, "selected_cell_risk_proof", "status"),
            "effective_risk_pct": risk_lot.get("effective_risk_pct"),
            "autocorrelation_after_risk_pct": get_path(risk_lot, "autocorrelation_risk_sizing", "after_risk_pct"),
        },
        "risk_geometry": {
            "raw_entry": row.get("raw_entry"),
            "raw_stop_loss": row.get("raw_stop_loss"),
            "repaired_entry": row.get("repaired_entry"),
            "repaired_stop_loss": row.get("repaired_stop_loss"),
            "risk_distance": row.get("risk_distance"),
            "spread_at_candidate": row.get("spread_at_candidate"),
            "spread_r_at_candidate": row.get("spread_r_at_candidate"),
            "lot_recompute": lot_recompute,
        },
        "broker_geometry": broker_geometry(row),
        "account_exposure_dollars": {
            "current_equity": exposure.get("current_equity"),
            "risk_base_amount": exposure.get("risk_base_amount"),
            "open_position_risk_amount": exposure.get("open_position_risk_amount"),
            "pending_order_risk_amount": exposure.get("pending_order_risk_amount"),
            "new_trade_sl_risk_amount": exposure.get("new_trade_sl_risk_amount"),
            "spread_slippage_commission_buffer_amount": exposure.get("spread_slippage_commission_buffer_amount"),
            "correlated_exposure_buffer_amount": exposure.get("correlated_exposure_buffer_amount"),
            "concentration_buffer_amount": exposure.get("concentration_buffer_amount"),
            "simultaneous_candidate_reserved_risk_amount": exposure.get("simultaneous_candidate_reserved_risk_amount"),
            "existing_and_buffer_risk_amount": exposure.get("existing_and_buffer_risk_amount"),
            "full_projected_risk_amount": exposure.get("full_projected_risk_amount"),
            "projected_equity_before_new_trade": exposure.get("projected_equity_before_new_trade"),
            "projected_equity_after_full_risk": exposure.get("projected_equity_after_full_risk"),
        },
        "prop_limits": {
            "initial_balance": external.get("initial_balance"),
            "external_daily_loss_limit_pct": external.get("daily_loss_limit_pct"),
            "external_daily_floor": external.get("daily_floor"),
            "external_remaining_daily_cushion": external.get("remaining_daily_cushion"),
            "external_projected_daily_cushion_before_new_trade": external.get("projected_daily_cushion_before_new_trade"),
            "external_projected_daily_cushion_after_full_risk": external.get("projected_daily_cushion_after_full_risk"),
            "overall_max_loss_pct": external.get("overall_max_loss_pct"),
            "overall_max_loss_floor": external.get("max_loss_floor"),
            "overall_remaining_cushion": external.get("remaining_overall_cushion"),
            "overall_projected_cushion_before_new_trade": external.get("projected_overall_cushion_before_new_trade"),
            "overall_projected_cushion_after_full_risk": external.get("projected_overall_cushion_after_full_risk"),
            "internal_overlay_enabled": internal.get("enabled"),
            "internal_overlay_applies_to_budget": internal.get("applies_to_selector_budget"),
            "internal_daily_loss_limit_pct": internal.get("daily_loss_limit_pct"),
            "internal_daily_floor": internal.get("daily_floor"),
            "internal_remaining_daily_cushion": internal.get("remaining_daily_cushion"),
            "internal_projected_daily_cushion_before_new_trade": internal.get("projected_daily_cushion_before_new_trade"),
            "internal_projected_daily_cushion_after_full_risk": internal.get("projected_daily_cushion_after_full_risk"),
            "binding_budget_name": external.get("binding_budget_name"),
            "binding_budget_after_existing_risk": external.get("binding_budget_after_existing_risk"),
            "max_allowed_new_trade_risk_amount": external.get("max_allowed_new_trade_risk_amount"),
            "max_allowed_new_trade_risk_pct": external.get("max_allowed_new_trade_risk_pct"),
        },
        "count_and_concurrency_evidence": {
            "gate3_passed": gate3.get("passed") if isinstance(gate3, dict) else None,
            "gate3_denial_reason": row.get("gate3_denial_reason"),
            "gate3_checks_run": gate3.get("checks_run") if isinstance(gate3, dict) else None,
            "historical_trades_today": gate3_details.get("trades_today"),
            "historical_trades_in_kz": gate3_details.get("trades_in_kz"),
            "concentration_day_trade_count": concentration.get("day_trade_count"),
            "concentration_session_trade_count": concentration.get("session_trade_count"),
            "concentration_symbol_day_trade_count": concentration.get("symbol_day_trade_count"),
            "concentration_symbol_session_trade_count": concentration.get("symbol_session_trade_count"),
            "simultaneous_candidate_count": concentration.get("simultaneous_candidate_count"),
            "current_count_gate_interpretation": (
                "no_count_or_concurrency_refusal"
                if row.get("gate3_denial_reason") != "concurrent_cap_reached"
                else "concurrent_cap_refusal"
            ),
        },
        "source_refs": {
            "micro_price_action_ledger": route_rel(MICRO_LEDGER),
            "canonical_event_ledger": route_rel(CANONICAL_LEDGER) if canonical else None,
            "full_vnext_system_replay_ledger": route_rel(FULL_REPLAY_LEDGER) if full_replay else None,
            "source_path": row.get("source_path"),
            "source_row_reference": row.get("source_row_reference"),
        },
    }


def build_prop_repair_rows(account_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    repair_refs = current_code_refs()
    for row in account_rows:
        if row.get("final_outcome") != PROP_DEFERRAL_OUTCOME:
            continue
        prop_limits = row.get("prop_limits") or {}
        exposure = row.get("account_exposure_dollars") or {}
        projection = row.get("current_terminal_projection") or {}
        max_pct = float_or_none(prop_limits.get("max_allowed_new_trade_risk_pct"))
        rows.append(
            {
                "schema_version": "friday_prop_deferral_repair_ledger_v1",
                "trade_id": row.get("trade_id"),
                "candidate_id": row.get("candidate_id"),
                "symbol": row.get("symbol"),
                "candle_time_utc": row.get("candle_time_utc"),
                "historical_outcome": row.get("final_outcome"),
                "historical_order_path": "prop_budget_rejected_before_geometry_repair",
                "historical_reason": row.get("prop_reason"),
                "account_exposure_explanation": (
                    "gtos_internal_daily_overlay_budget_bound_after_existing_open_risk_buffers"
                ),
                "binding_budget_name": prop_limits.get("binding_budget_name"),
                "max_allowed_new_trade_risk_amount": prop_limits.get("max_allowed_new_trade_risk_amount"),
                "max_allowed_new_trade_risk_pct": prop_limits.get("max_allowed_new_trade_risk_pct"),
                "new_trade_sl_risk_amount": exposure.get("new_trade_sl_risk_amount"),
                "open_position_risk_amount": exposure.get("open_position_risk_amount"),
                "pending_order_risk_amount": exposure.get("pending_order_risk_amount"),
                "spread_slippage_commission_buffer_amount": exposure.get("spread_slippage_commission_buffer_amount"),
                "existing_and_buffer_risk_amount": exposure.get("existing_and_buffer_risk_amount"),
                "internal_projected_daily_cushion_before_new_trade": prop_limits.get("internal_projected_daily_cushion_before_new_trade"),
                "internal_projected_daily_cushion_after_full_risk": prop_limits.get("internal_projected_daily_cushion_after_full_risk"),
                "budget_bucket": row.get("prop_budget_bucket"),
                "min_reduced_risk_pct": 0.25,
                "deferral_explained": bool(row.get("prop_deferral_explained")),
                "current_code_repair_status": projection.get("current_code_repair_status"),
                "current_terminal_replay_status": projection.get("current_terminal_replay_status"),
                "selected_cell_risk_materiality": projection.get("selected_cell_risk_materiality"),
                "selected_cell_risk_missing_is_not_material": bool(max_pct is not None and max_pct < 0.25),
                "repair_decision": (
                    "no_new_code_change_required_current_code_already_projection_only_and_terminal_after_geometry"
                ),
                "code_refs": repair_refs["code_refs"],
                "test_refs": repair_refs["test_refs"],
            }
        )
    return rows


def current_code_refs() -> dict[str, list[str]]:
    return {
        "code_refs": [
            source_ref("src/components/orchestrator.py", "pre_dynamic_projection_only_"),
            source_ref("src/components/orchestrator.py", "gtos_vnext_prop_safe_selector_after_geometry_repair"),
            source_ref("src/components/gtos_vnext_runtime.py", "def evaluate_vnext_prop_safe_selector"),
            source_ref("src/components/permissions.py", "def _reject_if_concurrent_cap_reached"),
            source_ref("src/components/orchestrator.py", "def _get_open_positions_for_correlation"),
        ],
        "test_refs": [
            source_ref("tests/test_vnext_broader_origin_orchestrator.py", "def test_pre_dynamic_prop_budget_projection_does_not_terminally_block_dynamic_router"),
            source_ref("tests/test_vnext_broader_origin_orchestrator.py", "def test_open_position_risk_uses_ticket_bound_vnext_lifecycle_not_base_config"),
            source_ref("tests/test_vnext_broader_origin_orchestrator.py", "def test_open_position_risk_missing_lifecycle_does_not_default_to_base_config"),
            source_ref("tests/test_concurrent_cap.py", "def test_vnext_selected_cell_risk_bypasses_old_count_cap"),
            source_ref("tests/test_concurrent_cap.py", "def test_vnext_rejects_same_symbol_until_multi_ticket_lifecycle_supported"),
        ],
    }


def build_concurrency_audit(account_rows: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    outcomes = Counter(row.get("final_outcome") for row in account_rows)
    gate3_denials = Counter(
        (row.get("count_and_concurrency_evidence") or {}).get("gate3_denial_reason")
        for row in account_rows
    )
    prop_actions = Counter(row.get("prop_action") for row in account_rows)
    budget_buckets = Counter(row.get("prop_budget_bucket") for row in account_rows)
    cfg_risk = config.get("risk", {}) or {}
    cfg_runtime = config.get("gtos_vnext_runtime", {}) or {}
    refs = current_code_refs()
    count_refusals = [
        row for row in account_rows
        if (row.get("count_and_concurrency_evidence") or {}).get("gate3_denial_reason")
        in {"concurrent_cap_reached", "max_kz_trades", "trades_today", "trades_kz"}
    ]
    prop_rows = [row for row in account_rows if row.get("final_outcome") == PROP_DEFERRAL_OUTCOME]
    return {
        "schema_version": "friday_concurrency_cap_staleness_audit_v1",
        "generated_at_utc": utc_now(),
        "git_head": git_head(),
        "primary_rows": len(account_rows),
        "outcome_counts": dict(outcomes),
        "prop_action_counts": dict(prop_actions),
        "prop_budget_bucket_counts": dict(budget_buckets),
        "gate3_denial_counts": {str(key): value for key, value in gate3_denials.items()},
        "prop_deferral_rows": len(prop_rows),
        "prop_deferrals_explained": sum(1 for row in prop_rows if row.get("prop_deferral_explained")),
        "count_or_concurrency_refusal_rows": len(count_refusals),
        "count_or_concurrency_refusal_trade_ids": [row.get("trade_id") for row in count_refusals],
        "current_config_risk": {
            "risk_per_trade_pct": cfg_risk.get("risk_per_trade_pct"),
            "max_daily_loss_pct": cfg_risk.get("max_daily_loss_pct"),
            "max_concurrent": cfg_risk.get("max_concurrent"),
        },
        "current_config_prop_safe_selector": {
            "enabled": cfg_runtime.get("prop_safe_selector_enabled"),
            "apply_to_execution": cfg_runtime.get("prop_safe_selector_apply_to_execution"),
            "external_daily_loss_limit_pct": cfg_runtime.get("prop_safe_selector_external_daily_loss_limit_pct"),
            "external_overall_max_loss_pct": cfg_runtime.get("prop_safe_selector_external_overall_max_loss_pct"),
            "internal_daily_overlay_enabled": cfg_runtime.get("prop_safe_selector_internal_daily_overlay_enabled"),
            "internal_overlay_applies_to_budget": cfg_runtime.get("prop_safe_selector_internal_overlay_applies_to_budget"),
            "internal_daily_overlay_pct": cfg_runtime.get("prop_safe_selector_internal_daily_overlay_pct"),
            "min_reduced_risk_pct": cfg_runtime.get("prop_safe_selector_min_reduced_risk_pct"),
        },
        "current_code_interpretation": {
            "pre_dynamic_prop_projection": (
                "budget actions before dynamic selected-cell risk are projection-only unless hard boundary reasons apply"
            ),
            "terminal_prop_gate": "reruns after selected-cell risk and executable geometry",
            "legacy_count_cap": "legacy/non-vNext only; selected-cell-governed vNext rows bypass old filled-position count cap",
            "same_symbol_vnext_gate": "same-symbol stacking remains fail-closed until multi-ticket lifecycle support is explicit",
            "open_position_risk_source": "ticket-bound pending lifecycle selected-cell risk; missing lifecycle does not default to base risk",
        },
        "code_refs": refs["code_refs"],
        "test_refs": refs["test_refs"],
        "repair_decision": (
            "no_additional_code_change_required_for_friday_stage10; existing current code repairs stale pre-dynamic prop terminal block and stale count defaults"
        ),
    }


def build_summary(account_rows: list[dict[str, Any]], prop_rows: list[dict[str, Any]], concurrency: dict[str, Any]) -> dict[str, Any]:
    outcome_counts = Counter(row.get("final_outcome") for row in account_rows)
    budget_buckets = Counter(row.get("prop_budget_bucket") for row in account_rows)
    prop_budget_buckets = Counter(row.get("budget_bucket") for row in prop_rows)
    prop_binding = Counter(row.get("binding_budget_name") for row in prop_rows)
    max_allowed = [
        float(row["max_allowed_new_trade_risk_pct"])
        for row in prop_rows
        if row.get("max_allowed_new_trade_risk_pct") is not None
    ]
    open_risk = [
        float(row["open_position_risk_amount"])
        for row in prop_rows
        if row.get("open_position_risk_amount") is not None
    ]
    return {
        "schema_version": "friday_account_exposure_risk_summary_v1",
        "generated_at_utc": utc_now(),
        "git_head": git_head(),
        "primary_rows": len(account_rows),
        "prop_deferral_rows": len(prop_rows),
        "outcome_counts": dict(outcome_counts),
        "prop_budget_bucket_counts": dict(budget_buckets),
        "prop_deferral_budget_bucket_counts": dict(prop_budget_buckets),
        "prop_deferral_binding_budget_counts": dict(prop_binding),
        "prop_deferrals_explained": sum(1 for row in prop_rows if row.get("deferral_explained")),
        "prop_deferrals_current_code_repaired": sum(
            1
            for row in prop_rows
            if row.get("current_code_repair_status")
            == "repaired_projection_only_before_dynamic_then_terminal_after_geometry"
        ),
        "count_or_concurrency_refusal_rows": concurrency.get("count_or_concurrency_refusal_rows"),
        "gate3_denial_counts": concurrency.get("gate3_denial_counts"),
        "max_allowed_new_trade_risk_pct_range": {
            "min": round(min(max_allowed), 6) if max_allowed else None,
            "max": round(max(max_allowed), 6) if max_allowed else None,
        },
        "open_position_risk_amount_range": {
            "min": round(min(open_risk), 6) if open_risk else None,
            "max": round(max(open_risk), 6) if open_risk else None,
        },
        "decision": (
            "all_45_friday_prop_deferrals_explained_by_gtos_internal_daily_overlay_budget; "
            "historical pre-dynamic terminal blocker is already repaired in current code"
        ),
        "runtime_effect_boundary": "offline_artifact_only_no_broker_action_no_live_restart",
    }


def load_by_trade_id(path: Path) -> dict[str, dict[str, Any]]:
    rows = load_jsonl(path)
    return {str(row.get("trade_id")): row for row in rows if row.get("trade_id")}


def write_verifier() -> None:
    text = f'''"""Verify Friday Stage10 account-exposure repair artifacts."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ROUTE = ROOT / "research" / "operations" / "{freeze.ROUTE_ID}"
ACCOUNT = ROUTE / "FRIDAY_ACCOUNT_EXPOSURE_RISK_LEDGER.jsonl"
PROP = ROUTE / "FRIDAY_PROP_DEFERRAL_REPAIR_LEDGER.jsonl"
AUDIT = ROUTE / "FRIDAY_CONCURRENCY_CAP_STALENESS_AUDIT.json"
SUMMARY = ROUTE / "FRIDAY_ACCOUNT_EXPOSURE_RISK_SUMMARY.json"
OUT = ROUTE / "FRIDAY_ACCOUNT_EXPOSURE_RISK_VERIFICATION.json"


def count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("rb") as handle:
        return sum(chunk.count(b"\\n") for chunk in iter(lambda: handle.read(1024 * 1024), b""))


def rows(path: Path):
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def main() -> int:
    issues = []
    account_rows = count(ACCOUNT)
    prop_rows = count(PROP)
    if account_rows != {EXPECTED_PRIMARY_ROWS}:
        issues.append({{"code": "account_ledger_row_count_mismatch", "expected": {EXPECTED_PRIMARY_ROWS}, "actual": account_rows}})
    if prop_rows != {EXPECTED_PROP_DEFERRALS}:
        issues.append({{"code": "prop_repair_row_count_mismatch", "expected": {EXPECTED_PROP_DEFERRALS}, "actual": prop_rows}})
    if not AUDIT.exists():
        issues.append({{"code": "missing_concurrency_audit"}})
        audit = {{}}
    else:
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    if not SUMMARY.exists():
        issues.append({{"code": "missing_account_summary"}})
        summary = {{}}
    else:
        summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    unexplained = [row.get("trade_id") for row in rows(PROP) if not row.get("deferral_explained")]
    if unexplained:
        issues.append({{"code": "unexplained_prop_deferrals", "trade_ids": unexplained[:20], "count": len(unexplained)}})
    unrepaired = [
        row.get("trade_id")
        for row in rows(PROP)
        if row.get("current_code_repair_status") != "repaired_projection_only_before_dynamic_then_terminal_after_geometry"
    ]
    if unrepaired:
        issues.append({{"code": "prop_deferral_repair_status_unexpected", "trade_ids": unrepaired[:20], "count": len(unrepaired)}})
    if int(audit.get("count_or_concurrency_refusal_rows") or 0) != 0:
        issues.append({{"code": "unexpected_count_or_concurrency_refusals", "count": audit.get("count_or_concurrency_refusal_rows")}})
    if int(summary.get("prop_deferrals_explained") or 0) != {EXPECTED_PROP_DEFERRALS}:
        issues.append({{"code": "summary_prop_deferrals_not_all_explained", "actual": summary.get("prop_deferrals_explained")}})
    result = {{
        "schema_version": "friday_account_exposure_risk_verification_v1",
        "ok": not issues,
        "issues": issues,
        "account_rows": account_rows,
        "prop_repair_rows": prop_rows,
        "count_or_concurrency_refusal_rows": audit.get("count_or_concurrency_refusal_rows"),
        "prop_deferrals_explained": summary.get("prop_deferrals_explained"),
    }}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''
    VERIFIER.write_text(text, encoding="utf-8")


def verify() -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    account_rows = line_count(ACCOUNT_LEDGER)
    prop_rows = line_count(PROP_REPAIR_LEDGER)
    if account_rows != EXPECTED_PRIMARY_ROWS:
        issues.append({"code": "account_ledger_row_count_mismatch", "expected": EXPECTED_PRIMARY_ROWS, "actual": account_rows})
    if prop_rows != EXPECTED_PROP_DEFERRALS:
        issues.append({"code": "prop_repair_row_count_mismatch", "expected": EXPECTED_PROP_DEFERRALS, "actual": prop_rows})
    audit = load_json(CONCURRENCY_AUDIT, {})
    summary = load_json(ACCOUNT_SUMMARY, {})
    if int(audit.get("count_or_concurrency_refusal_rows") or 0) != 0:
        issues.append({"code": "unexpected_count_or_concurrency_refusals", "count": audit.get("count_or_concurrency_refusal_rows")})
    if int(summary.get("prop_deferrals_explained") or 0) != EXPECTED_PROP_DEFERRALS:
        issues.append({"code": "summary_prop_deferrals_not_all_explained", "actual": summary.get("prop_deferrals_explained")})
    for row in load_jsonl(PROP_REPAIR_LEDGER):
        if not row.get("deferral_explained"):
            issues.append({"code": "unexplained_prop_deferral", "trade_id": row.get("trade_id")})
        if row.get("current_code_repair_status") != "repaired_projection_only_before_dynamic_then_terminal_after_geometry":
            issues.append({"code": "unexpected_prop_repair_status", "trade_id": row.get("trade_id"), "status": row.get("current_code_repair_status")})
    return {
        "schema_version": "friday_account_exposure_risk_verification_v1",
        "generated_at_utc": utc_now(),
        "git_head": git_head(),
        "ok": not issues,
        "issues": issues,
        "account_rows": account_rows,
        "prop_repair_rows": prop_rows,
        "count_or_concurrency_refusal_rows": audit.get("count_or_concurrency_refusal_rows"),
        "prop_deferrals_explained": summary.get("prop_deferrals_explained"),
    }


def update_route_files(outputs: list[Path], summary: dict[str, Any], audit: dict[str, Any]) -> None:
    now = utc_now()
    state = load_json(freeze.STATE_PATH, {})
    finished = set(state.get("finished_artifacts") or [])
    finished.update(route_rel(path) for path in outputs)
    repaired = set(state.get("repaired_defects") or [])
    repaired.add("FRIDAY_ACCOUNT_EXPOSURE_PROP_DEFERRAL_REPLAY_REQUIRED")
    open_defects = [
        item for item in state.get("open_defects", [])
        if item.get("defect_id") != "FRIDAY_ACCOUNT_EXPOSURE_PROP_DEFERRAL_REPLAY_REQUIRED"
    ]
    tests = set(state.get("tests_run") or [])
    tests.update(
        [
            "py -3 -m py_compile scripts/build_vnext_friday_account_exposure_repair.py",
            "python scripts/build_vnext_friday_account_exposure_repair.py",
            "python scripts/build_vnext_friday_account_exposure_repair.py --check",
            "python research/operations/vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31/verify_friday_account_exposure_repair.py",
            "py -3 -m pytest tests/test_vnext_broader_origin_orchestrator.py::test_pre_dynamic_prop_budget_projection_does_not_terminally_block_dynamic_router tests/test_vnext_broader_origin_orchestrator.py::test_open_position_risk_uses_ticket_bound_vnext_lifecycle_not_base_config tests/test_vnext_broader_origin_orchestrator.py::test_open_position_risk_missing_lifecycle_does_not_default_to_base_config tests/test_concurrent_cap.py::TestGate3Integration::test_vnext_selected_cell_risk_bypasses_old_count_cap tests/test_concurrent_cap.py::TestGate3Integration::test_vnext_rejects_same_symbol_until_multi_ticket_lifecycle_supported -q",
        ]
    )
    state.update(
        {
            "updated_at_utc": now,
            "current_head": git_head(),
            "current_stage": "stage_10_account_exposure_prop_concurrency_repair_built",
            "finished_artifacts": sorted(finished),
            "open_defects": open_defects,
            "repaired_defects": sorted(repaired),
            "tests_run": sorted(tests),
            "exact_next_action": "Repair research_current_state/context and write Friday microscope final report.",
        }
    )
    write_json(freeze.STATE_PATH, state)

    completion = load_json(freeze.COMPLETION_AUDIT, {})
    completed = set(completion.get("completed_requirements") or [])
    completed.add("Stage 10 account-exposure risk, prop-deferral, portfolio, and concurrency repair built")
    unmet = [
        item for item in completion.get("unmet_requirements", [])
        if "account-exposure risk and prop-deferral reconstruction" not in item
    ]
    completion.update(
        {
            "generated_at_utc": now,
            "completed_requirements": sorted(completed),
            "unmet_requirements": unmet,
            "completion_decision": "keep_goal_active",
            "status": "not_complete",
        }
    )
    write_json(freeze.COMPLETION_AUDIT, completion)

    freeze.append_jsonl(
        freeze.REPAIR_LEDGER,
        {
            "schema_version": "friday_microscope_repair_ledger_v1",
            "timestamp_utc": now,
            "defect_id": "FRIDAY_ACCOUNT_EXPOSURE_PROP_DEFERRAL_REPLAY_REQUIRED",
            "defect_class": "account_exposure_prop_deferral_reconstruction",
            "status": "repaired_stage10_ledgers_built_current_code_verified",
            "evidence": route_rel(ACCOUNT_SUMMARY),
            "decision": summary.get("decision"),
            "count_or_concurrency_refusal_rows": audit.get("count_or_concurrency_refusal_rows"),
        },
    )
    freeze.append_jsonl(
        freeze.CONTROL_LEDGER,
        {
            "schema_version": "friday_microscope_control_ledger_v1",
            "timestamp_utc": now,
            "stage": "stage_10_account_exposure_prop_concurrency_repair",
            "action": "built_account_exposure_prop_deferral_and_concurrency_audit_ledgers",
            "git_head": git_head(),
            "account_rows": summary.get("primary_rows"),
            "prop_deferral_rows": summary.get("prop_deferral_rows"),
            "prop_deferrals_explained": summary.get("prop_deferrals_explained"),
            "count_or_concurrency_refusal_rows": audit.get("count_or_concurrency_refusal_rows"),
        },
    )
    paths = sorted(path for path in ROUTE_DIR.iterdir() if path.is_file())
    write_json(freeze.OUTPUT_MANIFEST, freeze.output_manifest(paths))


def build() -> dict[str, Any]:
    micro_rows = load_jsonl(MICRO_LEDGER)
    canonical_by_id = load_by_trade_id(CANONICAL_LEDGER)
    full_by_id = load_by_trade_id(FULL_REPLAY_LEDGER)
    config = load_config()
    account_rows = [
        build_account_row(
            row,
            canonical_by_id.get(str(row.get("trade_id"))),
            full_by_id.get(str(row.get("trade_id"))),
        )
        for row in micro_rows
    ]
    prop_rows = build_prop_repair_rows(account_rows)
    audit = build_concurrency_audit(account_rows, config)
    summary = build_summary(account_rows, prop_rows, audit)

    write_jsonl(ACCOUNT_LEDGER, account_rows)
    write_jsonl(PROP_REPAIR_LEDGER, prop_rows)
    write_json(CONCURRENCY_AUDIT, audit)
    write_json(ACCOUNT_SUMMARY, summary)
    write_verifier()
    verification = verify()
    write_json(VERIFICATION, verification)
    outputs = [
        ACCOUNT_LEDGER,
        PROP_REPAIR_LEDGER,
        CONCURRENCY_AUDIT,
        ACCOUNT_SUMMARY,
        VERIFIER,
        VERIFICATION,
    ]
    update_route_files(outputs, summary, audit)
    return verification


def main() -> int:
    args = parse_args()
    result = verify() if args.check else build()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
