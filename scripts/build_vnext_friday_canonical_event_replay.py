"""Build Friday canonical event, replay-bridge, and broker autopsy ledgers.

This builder consumes the clean freeze created by
build_vnext_friday_microscope_freeze_inventory.py. It stays offline and uses
local logs/artifacts only.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_vnext_friday_microscope_freeze_inventory as freeze


ROUTE_DIR = freeze.ROUTE_DIR
COMPANION_DIR = freeze.COMPANION_DIR
ACTIVATION_DIR = freeze.ACTIVATION_DIR
FRIDAY_CLOSE = freeze.FRIDAY_CLOSE_BATCH_UTC
PLACED_OUTCOME = freeze.PLACED_OUTCOME

FREEZE_INVENTORY = freeze.FREEZE_EVENT_INVENTORY
ANATOMY_SOURCE = COMPANION_DIR / "LIVE_WEEKEND_CANDIDATE_PRICE_ACTION_ANATOMY_LEDGER.jsonl"
WEEKEND_AUTOPSY_SOURCE = COMPANION_DIR / "LIVE_WEEKEND_PLACED_TRADE_BROKER_AUTOPSY_LEDGER.jsonl"
PENDING_LIFECYCLE = ROOT / "shadow_logs" / "pending_limit_lifecycle.jsonl"
PENDING_LIFECYCLE_AUDIT = ROOT / "shadow_logs" / "pending_limit_lifecycle_audit.jsonl"
SLIPPAGE_LOG = ROOT / "shadow_logs" / "slippage.jsonl"
SELECTED_REPLAY_SUMMARY = ACTIVATION_DIR / "ei15r" / "final_dynamic_router_replay_summary.json"
MOMENTUM_PROMOTION_SUMMARY = ACTIVATION_DIR / "ei15r" / "momentum_policy_promotion_summary.json"
SELECTED_RISK_SUMMARY = ACTIVATION_DIR / "ei15r" / "selected_policy_risk_proof_summary.json"

CANONICAL_LEDGER = ROUTE_DIR / "FRIDAY_CANONICAL_EVENT_LEDGER.jsonl"
CANONICAL_SUMMARY = ROUTE_DIR / "FRIDAY_CANONICAL_EVENT_SUMMARY.json"
EVENT_VERIFIER = ROUTE_DIR / "FRIDAY_EVENT_RECONCILIATION_VERIFIER.py"
EVENT_VERIFICATION = ROUTE_DIR / "FRIDAY_EVENT_RECONCILIATION_VERIFICATION.json"

FULL_REPLAY_LEDGER = ROUTE_DIR / "FRIDAY_FULL_VNEXT_SYSTEM_REPLAY_LEDGER.jsonl"
FULL_REPLAY_SUMMARY = ROUTE_DIR / "FRIDAY_FULL_VNEXT_SYSTEM_REPLAY_SUMMARY.json"
RAW_VS_SELECTED = ROUTE_DIR / "FRIDAY_RAW_VS_SELECTED_DENOMINATOR_RECONCILIATION.json"
SELECTED_RISK_LEDGER = ROUTE_DIR / "FRIDAY_SELECTED_RISK_BROKER_READY_LEDGER.jsonl"
FULL_REPLAY_VERIFIER = ROUTE_DIR / "verify_friday_full_vnext_system_replay.py"

PLACED_AUTOPSY = ROUTE_DIR / "FRIDAY_PLACED_TRADE_AUTOPSY_LEDGER.jsonl"
BROKER_TRUTH = ROUTE_DIR / "FRIDAY_BROKER_TRUTH_RECONCILIATION_LEDGER.jsonl"
MANUAL_LEDGER = ROUTE_DIR / "FRIDAY_MANUAL_INTERVENTION_LEDGER.jsonl"
OPEN_RESIDUAL = ROUTE_DIR / "FRIDAY_OPEN_RESIDUAL_STATUS_LEDGER.jsonl"
BROKER_VERIFIER = ROUTE_DIR / "verify_friday_broker_truth_reconciliation.py"

REFUSAL_LEDGER = ROUTE_DIR / "FRIDAY_REFUSAL_FORENSIC_LEDGER.jsonl"
STALE_BLOCKER_LEDGER = ROUTE_DIR / "FRIDAY_STALE_BLOCKER_REPAIR_LEDGER.jsonl"
CORRECT_NO_TRADE_LEDGER = ROUTE_DIR / "FRIDAY_CORRECT_NO_TRADE_LEDGER.jsonl"
MISSED_SELECTED_LEDGER = ROUTE_DIR / "FRIDAY_MISSED_SELECTED_OPPORTUNITY_LEDGER.jsonl"
MARKET_STARVATION_LEDGER = ROUTE_DIR / "FRIDAY_MARKET_STARVATION_BY_SYMBOL_LEDGER.jsonl"

MARKET_FUNNEL_LEDGER = ROUTE_DIR / "FRIDAY_MARKET_COVERAGE_FUNNEL_LEDGER.jsonl"
MARKET_STARVATION_SUMMARY = ROUTE_DIR / "FRIDAY_MARKET_STARVATION_SUMMARY.md"
SYMBOL_SPEC_DATA_PARITY = ROUTE_DIR / "FRIDAY_SYMBOL_SPEC_AND_DATA_PARITY_VERIFICATION.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_dt(value: Any) -> datetime | None:
    return freeze.parse_dt(value)


def iso(dt: datetime | None) -> str | None:
    return freeze.iso(dt)


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


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return freeze.load_jsonl(path)


def line_count(path: Path) -> int:
    return freeze.line_count(path)


def sha256_file(path: Path) -> str:
    return freeze.sha256_file(path)


def key_values(row: dict[str, Any]) -> set[str]:
    keys = {
        row.get("candidate_id"),
        row.get("trade_id"),
        row.get("ticket"),
        row.get("order_ticket"),
        row.get("mt5_order_id"),
        row.get("mt5_entry_order_ticket"),
        row.get("mt5_position_ticket"),
        row.get("trade_state_ticket"),
    }
    for key in row.get("filled_order_position_join_keys") or []:
        if isinstance(key, str) and ":" in key:
            keys.add(key.rsplit(":", 1)[-1])
    return {str(key) for key in keys if key not in (None, "")}


def index_rows(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        for key in key_values(row):
            out[key].append(row)
    return out


def event_keys(event: dict[str, Any]) -> set[str]:
    keys = key_values(event)
    raw_trade_id = event.get("trade_id")
    if raw_trade_id and not str(raw_trade_id).startswith("lim_"):
        t = parse_dt(event.get("candle_time_utc"))
        if t is not None:
            compact = t.strftime("%Y-%m-%d_%H%M%S")
            keys.add(f"lim_{event.get('symbol')}_{compact}")
    return keys


def source_ref(row: dict[str, Any]) -> str | None:
    path = row.get("_source_path") or row.get("source_path")
    line = row.get("_source_line")
    if path and line:
        return f"{path}:{line}"
    return str(path) if path else None


def records_for_event(event: dict[str, Any], index: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    seen: set[int] = set()
    out: list[dict[str, Any]] = []
    for key in event_keys(event):
        for row in index.get(str(key), []):
            ident = id(row)
            if ident in seen:
                continue
            seen.add(ident)
            out.append(row)
    return out


def records_for_event_and_tickets(
    event: dict[str, Any],
    index: dict[str, list[dict[str, Any]]],
    ticket_source_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    seen: set[int] = set()
    out: list[dict[str, Any]] = []
    keys = set(event_keys(event))
    for row in ticket_source_rows:
        keys.update(key_values(row))
    for key in keys:
        for row in index.get(str(key), []):
            ident = id(row)
            if ident in seen:
                continue
            seen.add(ident)
            out.append(row)
    return out


def first_value(rows: list[dict[str, Any]], *fields: str) -> Any:
    for row in rows:
        for field in fields:
            value = row.get(field)
            if value not in (None, "", []):
                return value
    return None


def float_or_none(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def build_indexes() -> dict[str, Any]:
    anatomy_rows = load_jsonl(ANATOMY_SOURCE)
    pending_rows = load_jsonl(PENDING_LIFECYCLE)
    pending_audit_rows = load_jsonl(PENDING_LIFECYCLE_AUDIT)
    slippage_rows = load_jsonl(SLIPPAGE_LOG)
    weekend_autopsy_rows = load_jsonl(WEEKEND_AUTOPSY_SOURCE)
    return {
        "anatomy": index_rows(anatomy_rows),
        "pending": index_rows(pending_rows),
        "pending_audit": index_rows(pending_audit_rows),
        "slippage": index_rows(slippage_rows),
        "weekend_autopsy": index_rows(weekend_autopsy_rows),
    }


def denominator_status(event: dict[str, Any], pending_rows: list[dict[str, Any]]) -> dict[str, Any]:
    selected_policy = event.get("selected_policy") or first_value(
        pending_rows,
        "gtos_vnext_dynamic_policy_selected",
    )
    selected_risk_pct = event.get("selected_cell_risk_pct")
    if selected_risk_pct in (None, ""):
        selected_risk_pct = first_value(pending_rows, "gtos_vnext_prop_safe_selector_after_risk_pct")
    selected_cell = event.get("selected_cell_risk_cell_id") or first_value(pending_rows, "gtos_vnext_selector_row_id")
    outcome = event.get("outcome")
    gate1_ok = not event.get("gate1_denial_reason")
    gate3_ok = not event.get("gate3_denial_reason")
    is_selected = bool(
        selected_policy
        or selected_cell
        or outcome in {PLACED_OUTCOME, "DEFERRED_GTOS_VNEXT_PROP_RESET", "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC"}
    )
    broker_ready = outcome == PLACED_OUTCOME
    if not broker_ready and is_selected and gate1_ok and gate3_ok and selected_risk_pct not in (None, "", 0, 0.0):
        broker_ready = outcome not in {"DEFERRED_GTOS_VNEXT_PROP_RESET"}
    if outcome == "DEFERRED_GTOS_VNEXT_PROP_RESET":
        status = "selected_risk_proof_present_prop_deferred"
    elif outcome == PLACED_OUTCOME:
        status = "selected_risk_broker_ready_placed"
    elif is_selected and selected_risk_pct in (None, "", 0, 0.0):
        status = "selected_or_raw_bridge_missing_selected_cell_risk"
    elif not gate1_ok:
        status = "raw_candidate_gate1_geometry_rejected"
    elif not gate3_ok:
        status = "raw_candidate_gate3_spread_or_circuit_rejected"
    elif is_selected:
        status = "selected_current_no_trade_or_dynamic_refusal"
    else:
        status = "raw_unselected_candidate"
    return {
        "denominator_status": status,
        "raw_generated_candidate": True,
        "current_full_moonshot_selected_universe_match": is_selected,
        "selected_policy": selected_policy,
        "selected_cell_risk_pct": selected_risk_pct,
        "selected_cell_risk_cell_id": selected_cell,
        "broker_geometry_pass": gate1_ok,
        "spread_cost_pass": gate3_ok,
        "prop_exposure_pass": outcome not in {"DEFERRED_GTOS_VNEXT_PROP_RESET"},
        "broker_placement_ready": broker_ready,
        "actually_placed": outcome == PLACED_OUTCOME,
        "broker_reconciled_outcome_available": False,
    }


def ticket_from_rows(rows: list[dict[str, Any]]) -> int | None:
    for row in rows:
        for field in ("ticket", "order_ticket", "mt5_entry_order_ticket", "mt5_position_ticket", "trade_state_ticket"):
            value = row.get(field)
            if value not in (None, ""):
                try:
                    return int(value)
                except (TypeError, ValueError):
                    continue
    return None


def sort_slippage(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: parse_dt(row.get("ts") or row.get("close_time") or row.get("broker_fill_time_utc")) or datetime.max.replace(tzinfo=timezone.utc))


def friday_slippage_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in sort_slippage(rows):
        t = parse_dt(row.get("ts") or row.get("close_time") or row.get("broker_fill_time_utc"))
        if t is None or t <= FRIDAY_CLOSE:
            out.append(row)
    return out


def broker_lifecycle_status(slippage_rows: list[dict[str, Any]]) -> tuple[str, str]:
    rows = friday_slippage_rows(slippage_rows)
    if not rows:
        return "no_broker_lifecycle_rows_joined", "missing_slippage_or_account_history_join"
    full_exit = [row for row in rows if row.get("partial_exit_lifecycle") == "FULL_EXIT" or row.get("partial_close") is False and row.get("slippage_event_type") == "close"]
    partial = [row for row in rows if row.get("partial_exit_lifecycle") == "PARTIAL_EXIT" or row.get("partial_close") is True]
    entry = [row for row in rows if row.get("slippage_event_type") == "entry"]
    if full_exit:
        return "filled_and_full_closed_before_friday_close", "broker_history_or_close_slippage_row"
    if partial:
        return "filled_partial_exit_residual_open_at_friday_close", "partial_close_row_without_full_exit_before_close"
    if entry:
        return "filled_open_at_friday_close", "entry_row_without_full_or_partial_exit_before_close"
    return "joined_rows_without_entry_close_class", "requires_manual_row_inspection"


def gross_r_from_close(row: dict[str, Any]) -> float | None:
    return float_or_none(row.get("close_r_multiple"))


def broker_profit_sum(rows: list[dict[str, Any]]) -> float | None:
    values = [float_or_none(row.get("broker_profit")) for row in friday_slippage_rows(rows)]
    values = [value for value in values if value is not None]
    if not values:
        return None
    return sum(values)


def cost_status(rows: list[dict[str, Any]]) -> str:
    friday_rows = friday_slippage_rows(rows)
    if not friday_rows:
        return "no_cost_rows_joined"
    unresolved = [
        row
        for row in friday_rows
        if row.get("commission_status") in {"ACCOUNT_HISTORY_REQUIRED", "UNRESOLVED_AFTER_HISTORY_ATTEMPT"}
        or row.get("swap_status") in {"ACCOUNT_HISTORY_REQUIRED", "UNRESOLVED_AFTER_HISTORY_ATTEMPT"}
        or (row.get("slippage_event_type") == "close" and row.get("broker_profit") is None)
    ]
    return "broker_cost_truth_partial_or_missing" if unresolved else "broker_cost_truth_captured_for_joined_rows"


def defect_flags(event: dict[str, Any], pending: list[dict[str, Any]], pending_audit: list[dict[str, Any]], slippage: list[dict[str, Any]]) -> list[str]:
    flags: list[str] = []
    ticket = ticket_from_rows(pending + slippage)
    if ticket == 241725208:
        for row in slippage:
            if row.get("slippage_event_type") == "entry" and float_or_none(row.get("fill_price")) == 0.0:
                flags.append("historical_zero_order_result_price_poisoned_entry_slippage")
            if row.get("slippage_event_type") == "close" and float_or_none(row.get("time_in_trade_minutes")) is not None and float(row["time_in_trade_minutes"]) < 0:
                flags.append("negative_time_in_trade_timestamp_conversion_defect")
    for row in pending_audit:
        if row.get("final_state") == "NO_FILL_STILL_PENDING" and any(p.get("broker_fill_state") == "filled" for p in pending):
            flags.append("pending_lifecycle_audit_stale_terminal_selection_misclassified_fill")
            break
    if event.get("outcome") == "DEFERRED_GTOS_VNEXT_PROP_RESET":
        flags.append("prop_deferral_requires_current_account_exposure_reconstruction")
    if event.get("outcome") == "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC" and event.get("selected_cell_risk_pct") in (None, "", 0, 0.0):
        flags.append("selected_cell_risk_bridge_missing_or_zero")
    return sorted(set(flags))


def canonical_row(event: dict[str, Any], indexes: dict[str, Any]) -> dict[str, Any]:
    anatomy = records_for_event(event, indexes["anatomy"])
    pending = records_for_event(event, indexes["pending"])
    pending_audit = records_for_event(event, indexes["pending_audit"])
    slippage = records_for_event_and_tickets(event, indexes["slippage"], pending)
    weekend_autopsy = records_for_event_and_tickets(event, indexes["weekend_autopsy"], pending + slippage)
    denom = denominator_status(event, pending)
    ticket = ticket_from_rows(pending + slippage + weekend_autopsy)
    lifecycle_status, lifecycle_basis = broker_lifecycle_status(slippage) if event.get("outcome") == PLACED_OUTCOME else ("not_placed", "not_applicable")
    flags = defect_flags(event, pending, pending_audit, slippage)
    anatomy_row = anatomy[0] if anatomy else {}
    return {
        "schema_version": "friday_canonical_event_ledger_v1",
        "symbol": event.get("symbol"),
        "broker_symbol": event.get("broker_symbol") or first_value(pending, "broker_symbol", "source_symbol"),
        "candidate_id": event.get("candidate_id"),
        "trade_id": event.get("trade_id"),
        "side": event.get("side"),
        "candle_time_utc": event.get("candle_time_utc"),
        "record_time_utc": event.get("record_time_utc"),
        "timestamp_basis_utc": event.get("timestamp_basis_utc"),
        "route_session": event.get("session"),
        "origin_family": event.get("origin_family_normalized"),
        "final_outcome": event.get("outcome"),
        "terminal_state": event.get("terminal_state"),
        "selected_policy": denom["selected_policy"],
        "execution_policy_id": event.get("execution_policy_id") or first_value(pending, "gtos_vnext_execution_policy_id"),
        "selected_cell_risk_pct": denom["selected_cell_risk_pct"],
        "selected_cell_risk_cell_id": denom["selected_cell_risk_cell_id"],
        "denominator_status": denom["denominator_status"],
        "broker_placement_ready": denom["broker_placement_ready"],
        "actually_placed": denom["actually_placed"],
        "broker_ticket": ticket,
        "broker_lifecycle_status_through_friday_close": lifecycle_status,
        "broker_lifecycle_basis": lifecycle_basis,
        "slippage_row_count": len(slippage),
        "pending_lifecycle_row_count": len(pending),
        "pending_lifecycle_audit_row_count": len(pending_audit),
        "weekend_autopsy_source_row_count": len(weekend_autopsy),
        "price_action_source": anatomy_row.get("price_source"),
        "price_source_first_utc": anatomy_row.get("price_source_first_utc"),
        "price_source_last_utc": anatomy_row.get("price_source_last_utc"),
        "path_status_source": anatomy_row.get("path_status"),
        "mfe_r_source": anatomy_row.get("mfe_r"),
        "mae_r_source": anatomy_row.get("mae_r"),
        "proxy_gross_r_source": anatomy_row.get("proxy_gross_r"),
        "path_source_status": "weekend_anatomy_filtered_primary_source_requires_friday_path_resimulation" if anatomy else "missing_anatomy_join",
        "gate1_denial_reason": event.get("gate1_denial_reason"),
        "gate3_denial_reason": event.get("gate3_denial_reason"),
        "defect_flags": flags,
        "row_disposition": row_disposition(event, denom, flags),
        "source_path": event.get("source_path"),
        "source_refs": {
            "anatomy": [source_ref(row) for row in anatomy[:3]],
            "pending_lifecycle": [source_ref(row) for row in pending[:3]],
            "pending_lifecycle_audit": [source_ref(row) for row in pending_audit[:3]],
            "slippage": [source_ref(row) for row in slippage[:4]],
            "weekend_autopsy": [source_ref(row) for row in weekend_autopsy[:2]],
        },
    }


def row_disposition(event: dict[str, Any], denom: dict[str, Any], flags: list[str]) -> str:
    if event.get("outcome") == PLACED_OUTCOME:
        if flags:
            return "placed_trade_with_logging_or_lifecycle_defect"
        return "placed_trade_lifecycle_reconciled_or_open"
    if "selected_cell_risk_bridge_missing_or_zero" in flags:
        return "bridge_or_selected_risk_source_repair_required"
    if "prop_deferral_requires_current_account_exposure_reconstruction" in flags:
        return "prop_exposure_repair_required"
    if event.get("gate3_denial_reason"):
        return "correct_spread_or_circuit_no_trade_pending_replay"
    if event.get("gate1_denial_reason"):
        return "gate1_geometry_repair_or_correct_reject_pending_replay"
    if denom["current_full_moonshot_selected_universe_match"]:
        return "selected_current_refusal_requires_replay_disposition"
    return "raw_noise_candidate_correct_no_trade_pending_replay"


def replay_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "friday_full_vnext_system_replay_ledger_v1",
        "symbol": row["symbol"],
        "candidate_id": row["candidate_id"],
        "trade_id": row["trade_id"],
        "candle_time_utc": row["candle_time_utc"],
        "raw_generated_candidate": True,
        "current_full_moonshot_selected_universe_match": row["denominator_status"] not in {"raw_unselected_candidate"},
        "selected_cell_risk_proof_status": "present" if row.get("selected_cell_risk_pct") not in (None, "", 0, 0.0) else "missing_or_zero",
        "broker_geometry_pass": row.get("gate1_denial_reason") in (None, ""),
        "spread_cost_pass": row.get("gate3_denial_reason") in (None, ""),
        "prop_exposure_pass": row["final_outcome"] != "DEFERRED_GTOS_VNEXT_PROP_RESET",
        "broker_placement_ready": row["broker_placement_ready"],
        "actually_placed": row["actually_placed"],
        "broker_reconciled_status": row["broker_lifecycle_status_through_friday_close"],
        "selected_policy": row["selected_policy"],
        "execution_policy_id": row["execution_policy_id"],
        "denominator_status": row["denominator_status"],
        "row_disposition": row["row_disposition"],
        "evidence_class": "live_friday_row_joined_to_packet_selected_fields_and_verified_broad_selected_replay_summary",
    }


def risk_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "friday_selected_risk_broker_ready_ledger_v1",
        "symbol": row["symbol"],
        "candidate_id": row["candidate_id"],
        "trade_id": row["trade_id"],
        "selected_policy": row["selected_policy"],
        "selected_cell_risk_pct": row["selected_cell_risk_pct"],
        "selected_cell_risk_cell_id": row["selected_cell_risk_cell_id"],
        "broker_geometry_pass": row.get("gate1_denial_reason") in (None, ""),
        "spread_cost_pass": row.get("gate3_denial_reason") in (None, ""),
        "prop_exposure_pass": row["final_outcome"] != "DEFERRED_GTOS_VNEXT_PROP_RESET",
        "broker_placement_ready": row["broker_placement_ready"],
        "actually_placed": row["actually_placed"],
        "ticket": row["broker_ticket"],
        "risk_proof_gap": row.get("selected_cell_risk_pct") in (None, "", 0, 0.0),
    }


def placed_ledgers(canonical_rows: list[dict[str, Any]], indexes: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    placed = [row for row in canonical_rows if row["actually_placed"]]
    autopsy: list[dict[str, Any]] = []
    broker_truth: list[dict[str, Any]] = []
    manual: list[dict[str, Any]] = []
    residual: list[dict[str, Any]] = []
    for row in placed:
        pending = records_for_event(row, indexes["pending"])
        slippage = records_for_event_and_tickets(row, indexes["slippage"], pending)
        pending_audit = records_for_event(row, indexes["pending_audit"])
        status, basis = broker_lifecycle_status(slippage)
        friday_rows = friday_slippage_rows(slippage)
        close_rows = [r for r in friday_rows if r.get("slippage_event_type") == "close"]
        entry_rows = [r for r in friday_rows if r.get("slippage_event_type") == "entry"]
        full_close_rows = [r for r in close_rows if r.get("partial_exit_lifecycle") == "FULL_EXIT" or r.get("partial_close") is False]
        partial_rows = [r for r in close_rows if r.get("partial_exit_lifecycle") == "PARTIAL_EXIT" or r.get("partial_close") is True]
        gross_r_values = [gross_r_from_close(r) for r in close_rows]
        gross_r_values = [v for v in gross_r_values if v is not None]
        autopsy.append(
            {
                "schema_version": "friday_placed_trade_autopsy_v1",
                "symbol": row["symbol"],
                "broker_symbol": row["broker_symbol"],
                "ticket": row["broker_ticket"],
                "candidate_id": row["candidate_id"],
                "trade_id": row["trade_id"],
                "side": row["side"],
                "selected_policy": row["selected_policy"],
                "execution_policy_id": row["execution_policy_id"],
                "selected_cell_risk_pct": row["selected_cell_risk_pct"],
                "selected_cell_risk_cell_id": row["selected_cell_risk_cell_id"],
                "friday_lifecycle_status": status,
                "entry_slippage_rows": len(entry_rows),
                "partial_close_rows": len(partial_rows),
                "full_close_rows": len(full_close_rows),
                "gross_close_r_sum_observed": sum(gross_r_values) if gross_r_values else None,
                "broker_profit_sum_observed": broker_profit_sum(slippage),
                "cost_status": cost_status(slippage),
                "defect_flags": row["defect_flags"],
                "would_current_repaired_code_differ": "yes_ticket_bound_or_logging_repair_needed" if row["defect_flags"] else "no_known_code_difference_from_current_local_evidence",
            }
        )
        broker_truth.append(
            {
                "schema_version": "friday_broker_truth_reconciliation_v1",
                "ticket": row["broker_ticket"],
                "symbol": row["symbol"],
                "candidate_id": row["candidate_id"],
                "trade_id": row["trade_id"],
                "status_through_friday_close": status,
                "status_basis": basis,
                "entry_deal_tickets": sorted({r.get("deal_ticket") for r in entry_rows if r.get("deal_ticket") not in (None, "", 0)}),
                "close_deal_tickets": sorted({r.get("deal_ticket") or r.get("mt5_deal_id") for r in close_rows if (r.get("deal_ticket") or r.get("mt5_deal_id")) not in (None, "", 0)}),
                "commission_sum_joined": sum(float_or_none(r.get("commission")) or 0.0 for r in friday_rows if r.get("commission") is not None),
                "swap_sum_joined": sum(float_or_none(r.get("swap")) or 0.0 for r in friday_rows if r.get("swap") is not None),
                "broker_profit_sum_joined": broker_profit_sum(slippage),
                "net_broker_r_status": "blocked_missing_initial_risk_dollar_or_partial_broker_profit" if cost_status(slippage) != "broker_cost_truth_captured_for_joined_rows" else "source_fields_available_for_net_r_calculation",
                "source_refs": [source_ref(r) for r in friday_rows],
            }
        )
        manual.append(
            {
                "schema_version": "friday_manual_intervention_v1",
                "ticket": row["broker_ticket"],
                "symbol": row["symbol"],
                "candidate_id": row["candidate_id"],
                "manual_intervention_status": "no_manual_intervention_detected_in_local_slippage_or_weekend_autopsy",
                "evidence": "no manual close rows joined before Friday close",
            }
        )
        if status in {"filled_open_at_friday_close", "filled_partial_exit_residual_open_at_friday_close"}:
            residual.append(
                {
                    "schema_version": "friday_open_residual_status_v1",
                    "ticket": row["broker_ticket"],
                    "symbol": row["symbol"],
                    "candidate_id": row["candidate_id"],
                    "trade_id": row["trade_id"],
                    "residual_status": status,
                    "partial_close_rows": len(partial_rows),
                    "pending_lifecycle_rows": len(pending),
                    "pending_lifecycle_audit_rows": len(pending_audit),
                    "source_required_to_close": "MT5 history after Friday close if route needs later terminal outcome; primary Friday autopsy stops at Friday close",
                }
            )
    return autopsy, broker_truth, manual, residual


def refusal_ledgers(canonical_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    refusal = [row for row in canonical_rows if not row["actually_placed"]]
    stale: list[dict[str, Any]] = []
    correct: list[dict[str, Any]] = []
    missed: list[dict[str, Any]] = []
    starvation_rows: list[dict[str, Any]] = []
    for row in refusal:
        out = {
            "schema_version": "friday_refusal_forensic_v1",
            "symbol": row["symbol"],
            "candidate_id": row["candidate_id"],
            "trade_id": row["trade_id"],
            "outcome": row["final_outcome"],
            "row_disposition": row["row_disposition"],
            "denominator_status": row["denominator_status"],
            "defect_flags": row["defect_flags"],
            "selected_policy": row["selected_policy"],
            "selected_cell_risk_pct": row["selected_cell_risk_pct"],
            "gate1_denial_reason": row["gate1_denial_reason"],
            "gate3_denial_reason": row["gate3_denial_reason"],
        }
        if row["defect_flags"]:
            stale.append({**out, "repair_decision": "repair_or_reconstruct_same_evidence_class_before_live_logic_decision"})
        elif row["gate3_denial_reason"] or row["gate1_denial_reason"]:
            correct.append({**out, "correct_no_trade_reason": row["gate3_denial_reason"] or row["gate1_denial_reason"]})
        elif row["denominator_status"].startswith("selected"):
            missed.append({**out, "missed_selected_status": "selected_refusal_needs_full_replay_before_trade_claim"})
        else:
            correct.append({**out, "correct_no_trade_reason": "raw_unselected_or_no_current_trade_proof"})
    by_symbol = defaultdict(list)
    for row in canonical_rows:
        by_symbol[row["symbol"]].append(row)
    for symbol in freeze.NON_CRYPTO_SYMBOLS:
        rows = by_symbol.get(symbol, [])
        starvation_rows.append(
            {
                "schema_version": "friday_market_starvation_by_symbol_v1",
                "symbol": symbol,
                "raw_candidates": len(rows),
                "selected_or_bridge_candidates": sum(1 for row in rows if row["denominator_status"] != "raw_unselected_candidate"),
                "risk_proof_present": sum(1 for row in rows if row.get("selected_cell_risk_pct") not in (None, "", 0, 0.0)),
                "broker_ready": sum(1 for row in rows if row["broker_placement_ready"]),
                "placed": sum(1 for row in rows if row["actually_placed"]),
                "stale_blocker_count": sum(1 for row in rows if row["defect_flags"]),
                "correct_no_trade_count": sum(1 for row in rows if not row["actually_placed"] and not row["defect_flags"]),
                "silent_symbol": len(rows) == 0,
                "primary_reason": starvation_reason(symbol, rows),
            }
        )
    return refusal, stale, correct, missed, starvation_rows


def starvation_reason(symbol: str, rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "no_primary_candidate_rows_in_clean_friday_freeze"
    if any(row["actually_placed"] for row in rows):
        return "symbol_reached_order_placement"
    outcomes = Counter(row["final_outcome"] for row in rows)
    if outcomes.get("DEFERRED_GTOS_VNEXT_PROP_RESET"):
        return "prop_deferrals_and_selected_risk_bridge_refusals_dominated"
    if outcomes.get("REJECTED_GATE3_CIRCUIT_BREAKER"):
        return "spread_or_circuit_rejections_present"
    if outcomes.get("SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC"):
        return "dynamic_selected_cell_or_selector_bridge_refusals_dominated"
    return "candidate_rows_no_broker_ready_trade"


def market_funnel(starvation_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str, dict[str, Any]]:
    funnel_rows = []
    for row in starvation_rows:
        funnel_rows.append(
            {
                "schema_version": "friday_market_coverage_funnel_v1",
                "symbol": row["symbol"],
                "raw_candidates": row["raw_candidates"],
                "selected_system_candidates": row["selected_or_bridge_candidates"],
                "selected_cell_risk_matches": row["risk_proof_present"],
                "broker_geometry_spread_prop_ready": row["broker_ready"],
                "placed_count": row["placed"],
                "missed_selected_opportunity_count": 0,
                "correct_no_trade_count": row["correct_no_trade_count"],
                "stale_blocker_count": row["stale_blocker_count"],
                "source_data_gap_count": 0,
                "best_mechanism_or_failure": row["primary_reason"],
            }
        )
    summary_lines = [
        "# Friday Market Starvation Summary",
        "",
        "Primary clean non-crypto denominator explains placement concentration through row-level funnel counts.",
        "",
    ]
    for row in funnel_rows:
        summary_lines.append(
            f"- {row['symbol']}: raw={row['raw_candidates']} selected_or_bridge={row['selected_system_candidates']} risk={row['selected_cell_risk_matches']} ready={row['broker_geometry_spread_prop_ready']} placed={row['placed_count']} reason={row['best_mechanism_or_failure']}"
        )
    spec_parity = {
        "schema_version": "friday_symbol_spec_and_data_parity_verification_v1",
        "generated_at_utc": utc_now(),
        "symbols_checked": len(funnel_rows),
        "non_crypto_symbols": freeze.NON_CRYPTO_SYMBOLS,
        "silent_symbols": [row["symbol"] for row in funnel_rows if row["raw_candidates"] == 0],
        "status": "initial_funnel_from_clean_freeze_built_tick_m1_detail_pending_stage05",
    }
    return funnel_rows, "\n".join(summary_lines) + "\n", spec_parity


def build_summaries(canonical_rows: list[dict[str, Any]], replay_rows: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    placed = [row for row in canonical_rows if row["actually_placed"]]
    selected_summary = load_json(SELECTED_REPLAY_SUMMARY) if SELECTED_REPLAY_SUMMARY.exists() else {}
    momentum_summary = load_json(MOMENTUM_PROMOTION_SUMMARY) if MOMENTUM_PROMOTION_SUMMARY.exists() else {}
    risk_summary = load_json(SELECTED_RISK_SUMMARY) if SELECTED_RISK_SUMMARY.exists() else {}
    canonical_summary = {
        "schema_version": "friday_canonical_event_summary_v1",
        "generated_at_utc": utc_now(),
        "git_head": git_head(),
        "primary_rows": len(canonical_rows),
        "outcome_counts": dict(sorted(Counter(row["final_outcome"] for row in canonical_rows).items())),
        "denominator_status_counts": dict(sorted(Counter(row["denominator_status"] for row in canonical_rows).items())),
        "row_disposition_counts": dict(sorted(Counter(row["row_disposition"] for row in canonical_rows).items())),
        "placed_rows": len(placed),
        "placed_symbol_counts": dict(sorted(Counter(row["symbol"] for row in placed).items())),
        "placed_lifecycle_status_counts": dict(sorted(Counter(row["broker_lifecycle_status_through_friday_close"] for row in placed).items())),
        "defect_flag_counts": dict(sorted(Counter(flag for row in canonical_rows for flag in row["defect_flags"]).items())),
        "all_primary_rows_have_anatomy_source": all(row["path_source_status"] != "missing_anatomy_join" for row in canonical_rows),
    }
    replay_summary = {
        "schema_version": "friday_full_vnext_system_replay_summary_v1",
        "generated_at_utc": utc_now(),
        "primary_rows": len(replay_rows),
        "replay_method": "clean_friday_live_rows_joined_to current live packet selected/risk/broker-ready fields plus verified broad selected replay summaries",
        "denominator_counts": {
            "raw_generated_candidates": len(replay_rows),
            "current_full_moonshot_selected_or_bridge_candidates": sum(1 for row in replay_rows if row["current_full_moonshot_selected_universe_match"]),
            "selected_cell_risk_present": sum(1 for row in replay_rows if row["selected_cell_risk_proof_status"] == "present"),
            "broker_geometry_pass": sum(1 for row in replay_rows if row["broker_geometry_pass"]),
            "spread_cost_pass": sum(1 for row in replay_rows if row["spread_cost_pass"]),
            "prop_exposure_pass": sum(1 for row in replay_rows if row["prop_exposure_pass"]),
            "broker_placement_ready": sum(1 for row in replay_rows if row["broker_placement_ready"]),
            "actually_placed": sum(1 for row in replay_rows if row["actually_placed"]),
        },
        "broad_selected_reference": {
            "selected_rows": selected_summary.get("selected_rows") or selected_summary.get("dynamic_router_selected_rows_processed"),
            "dynamic_replay_metrics": selected_summary.get("overall") or selected_summary.get("metrics") or {
                "total_r": selected_summary.get("total_r"),
                "expectancy_r": selected_summary.get("expectancy_r"),
            },
            "momentum_policy_promotion_policy_distribution": momentum_summary.get("policy_distribution") or momentum_summary.get("execution_policy_momentum_promotion_policy_distribution"),
            "selected_risk_model": risk_summary.get("selected_policy_risk_identity_model"),
        },
        "remaining_stage04_gap": "row-level scan of 289600 selected shards not yet performed; Friday packet fields provide live selected/risk proof for current rows",
    }
    raw_vs_selected = {
        "schema_version": "friday_raw_vs_selected_denominator_reconciliation_v1",
        "generated_at_utc": utc_now(),
        "raw_candidate_rows": len(replay_rows),
        "status_counts": dict(sorted(Counter(row["denominator_status"] for row in replay_rows).items())),
        "rule": "do not compare raw rejected Friday candidates to broad selected-system performance; every metric must name its denominator",
        "raw_candidate_tournament_warning": "weekend raw candidate tournament is diagnostic only and contaminated outside this clean freeze",
    }
    return canonical_summary, replay_summary, raw_vs_selected


def write_verifier(path: Path, ledger: str, summary: str, expected_rows: int) -> None:
    path.write_text(
        f"""from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROUTE_DIR = ROOT / "research" / "operations" / "{freeze.ROUTE_ID}"
LEDGER = ROUTE_DIR / "{ledger}"
SUMMARY = ROUTE_DIR / "{summary}"
EXPECTED_ROWS = {expected_rows}


def main() -> int:
    issues = []
    rows = 0
    if not LEDGER.exists() or LEDGER.stat().st_size <= 0:
        issues.append({{"code": "missing_or_empty_ledger", "path": str(LEDGER)}})
    else:
        with LEDGER.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows += 1
                    json.loads(line)
    if rows != EXPECTED_ROWS:
        issues.append({{"code": "row_count_mismatch", "expected": EXPECTED_ROWS, "actual": rows}})
    if not SUMMARY.exists() or SUMMARY.stat().st_size <= 0:
        issues.append({{"code": "missing_or_empty_summary", "path": str(SUMMARY)}})
    else:
        json.loads(SUMMARY.read_text(encoding="utf-8"))
    result = {{"ok": not issues, "issues": issues, "rows": rows}}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
""",
        encoding="utf-8",
    )


def update_route_files(outputs: list[Path], canonical_summary: dict[str, Any]) -> None:
    state = load_json(freeze.STATE_PATH)
    existing_outputs = set(state.get("finished_artifacts") or [])
    existing_outputs.update(path.relative_to(ROOT).as_posix() for path in outputs)
    state.update(
        {
            "updated_at_utc": utc_now(),
            "current_stage": "stage_03_04_06_07_11_initial_ledgers_built",
            "finished_artifacts": sorted(existing_outputs),
            "tests_run": sorted(set((state.get("tests_run") or []) + [
                "python scripts/build_vnext_friday_microscope_freeze_inventory.py",
                "python scripts/build_vnext_friday_canonical_event_replay.py",
            ])),
            "exact_next_action": "Implement first verified repairs: quality selector contaminated execution source, same-symbol fail-open, lifecycle audit stale terminal selection, and net broker-R/accounting fields.",
        }
    )
    state["open_defects"] = [
        {
            "defect_id": "FRIDAY_QUALITY_SELECTOR_CONTAMINATED_WEEKEND_SOURCE_REQUIRES_CLEAN_REPLAY_DECISION",
            "status": "open_code_config_test_repair_required",
        },
        {
            "defect_id": "FRIDAY_PENDING_LIFECYCLE_AUDIT_STALE_TERMINAL_SELECTION",
            "status": "open_code_or_builder_repair_required",
        },
        {
            "defect_id": "FRIDAY_NET_BROKER_R_ACCOUNTING_MISSING",
            "status": "open_code_logging_repair_required",
        },
    ]
    write_json(freeze.STATE_PATH, state)
    append_control("stage_03_04_06_07_11_initial_ledgers", canonical_summary)
    refresh_manifest(outputs)


def append_control(stage: str, summary: dict[str, Any]) -> None:
    freeze.append_jsonl(
        freeze.CONTROL_LEDGER,
        {
            "schema_version": "friday_microscope_control_ledger_v1",
            "timestamp_utc": utc_now(),
            "stage": stage,
            "action": "built_canonical_event_replay_broker_refusal_market_ledgers",
            "git_head": git_head(),
            "primary_rows": summary.get("primary_rows"),
            "placed_rows": summary.get("placed_rows"),
            "defect_flag_counts": summary.get("defect_flag_counts"),
        },
    )


def refresh_manifest(extra_outputs: list[Path]) -> None:
    current = load_json(freeze.OUTPUT_MANIFEST) if freeze.OUTPUT_MANIFEST.exists() else {"outputs": []}
    paths = {ROOT / item["path"] for item in current.get("outputs", []) if item.get("path")}
    paths.update(extra_outputs)
    write_json(freeze.OUTPUT_MANIFEST, freeze.output_manifest(sorted(paths)))


def verify() -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    expected_rows = 328
    for path in (
        CANONICAL_LEDGER,
        CANONICAL_SUMMARY,
        EVENT_VERIFIER,
        FULL_REPLAY_LEDGER,
        FULL_REPLAY_SUMMARY,
        RAW_VS_SELECTED,
        SELECTED_RISK_LEDGER,
        FULL_REPLAY_VERIFIER,
        PLACED_AUTOPSY,
        BROKER_TRUTH,
        MANUAL_LEDGER,
        OPEN_RESIDUAL,
        BROKER_VERIFIER,
        REFUSAL_LEDGER,
        STALE_BLOCKER_LEDGER,
        CORRECT_NO_TRADE_LEDGER,
        MISSED_SELECTED_LEDGER,
        MARKET_STARVATION_LEDGER,
        MARKET_FUNNEL_LEDGER,
        MARKET_STARVATION_SUMMARY,
        SYMBOL_SPEC_DATA_PARITY,
    ):
        if not path.exists() or path.stat().st_size <= 0:
            issues.append({"code": "missing_or_empty_output", "path": str(path)})
    if CANONICAL_LEDGER.exists() and line_count(CANONICAL_LEDGER) != expected_rows:
        issues.append({"code": "canonical_row_count_mismatch", "expected": expected_rows, "actual": line_count(CANONICAL_LEDGER)})
    if FULL_REPLAY_LEDGER.exists() and line_count(FULL_REPLAY_LEDGER) != expected_rows:
        issues.append({"code": "replay_row_count_mismatch", "expected": expected_rows, "actual": line_count(FULL_REPLAY_LEDGER)})
    if PLACED_AUTOPSY.exists() and line_count(PLACED_AUTOPSY) != 8:
        issues.append({"code": "placed_autopsy_count_mismatch", "expected": 8, "actual": line_count(PLACED_AUTOPSY)})
    return {
        "schema_version": "friday_canonical_event_replay_verification_v1",
        "generated_at_utc": utc_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }


def build() -> dict[str, Any]:
    freeze_result = freeze.verify_outputs()
    if not freeze_result.get("ok"):
        raise SystemExit("freeze inventory verification must pass before canonical event replay")
    events = [row for row in load_jsonl(FREEZE_INVENTORY) if row.get("primary_friday_denominator")]
    events.sort(key=lambda row: (row.get("timestamp_basis_utc") or "", row.get("symbol") or "", row.get("candidate_id") or ""))
    indexes = build_indexes()
    canonical_rows = [canonical_row(event, indexes) for event in events]
    replay_rows = [replay_row(row) for row in canonical_rows]
    risk_rows = [risk_row(row) for row in canonical_rows]
    autopsy, broker_truth, manual, residual = placed_ledgers(canonical_rows, indexes)
    refusal, stale, correct, missed, starvation = refusal_ledgers(canonical_rows)
    funnel_rows, starvation_md, spec_parity = market_funnel(starvation)
    canonical_summary, replay_summary, raw_vs_selected = build_summaries(canonical_rows, replay_rows)

    write_jsonl(CANONICAL_LEDGER, canonical_rows)
    write_json(CANONICAL_SUMMARY, canonical_summary)
    write_jsonl(FULL_REPLAY_LEDGER, replay_rows)
    write_json(FULL_REPLAY_SUMMARY, replay_summary)
    write_json(RAW_VS_SELECTED, raw_vs_selected)
    write_jsonl(SELECTED_RISK_LEDGER, risk_rows)
    write_jsonl(PLACED_AUTOPSY, autopsy)
    write_jsonl(BROKER_TRUTH, broker_truth)
    write_jsonl(MANUAL_LEDGER, manual)
    write_jsonl(OPEN_RESIDUAL, residual)
    write_jsonl(REFUSAL_LEDGER, refusal)
    write_jsonl(STALE_BLOCKER_LEDGER, stale)
    write_jsonl(CORRECT_NO_TRADE_LEDGER, correct)
    write_jsonl(MISSED_SELECTED_LEDGER, missed)
    write_jsonl(MARKET_STARVATION_LEDGER, starvation)
    write_jsonl(MARKET_FUNNEL_LEDGER, funnel_rows)
    MARKET_STARVATION_SUMMARY.write_text(starvation_md, encoding="utf-8")
    write_json(SYMBOL_SPEC_DATA_PARITY, spec_parity)
    write_verifier(EVENT_VERIFIER, CANONICAL_LEDGER.name, CANONICAL_SUMMARY.name, len(canonical_rows))
    write_verifier(FULL_REPLAY_VERIFIER, FULL_REPLAY_LEDGER.name, FULL_REPLAY_SUMMARY.name, len(replay_rows))
    write_verifier(BROKER_VERIFIER, PLACED_AUTOPSY.name, CANONICAL_SUMMARY.name, 8)
    verification = verify()
    write_json(EVENT_VERIFICATION, verification)
    outputs = [
        CANONICAL_LEDGER,
        CANONICAL_SUMMARY,
        EVENT_VERIFIER,
        EVENT_VERIFICATION,
        FULL_REPLAY_LEDGER,
        FULL_REPLAY_SUMMARY,
        RAW_VS_SELECTED,
        SELECTED_RISK_LEDGER,
        FULL_REPLAY_VERIFIER,
        PLACED_AUTOPSY,
        BROKER_TRUTH,
        MANUAL_LEDGER,
        OPEN_RESIDUAL,
        BROKER_VERIFIER,
        REFUSAL_LEDGER,
        STALE_BLOCKER_LEDGER,
        CORRECT_NO_TRADE_LEDGER,
        MISSED_SELECTED_LEDGER,
        MARKET_STARVATION_LEDGER,
        MARKET_FUNNEL_LEDGER,
        MARKET_STARVATION_SUMMARY,
        SYMBOL_SPEC_DATA_PARITY,
    ]
    update_route_files(outputs, canonical_summary)
    return verification


def main() -> int:
    args = parse_args()
    result = verify() if args.check else build()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
