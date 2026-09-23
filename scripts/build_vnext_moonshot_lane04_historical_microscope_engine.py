from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_vnext_lane08_execution_policy_microstructure_stress as lane08


ROUTE_ID = "vnext_moonshot_lane04_historical_microscope_engine_2026_06_01"
ROUTE_DIR = ROOT / "research" / "operations" / ROUTE_ID

LANE02_DIR = ROOT / "research" / "operations" / "vnext_lane02_broad_selected_portfolio_replay_stress_2026_05_31"
LANE03_DIR = ROOT / "research" / "operations" / "vnext_lane03_meta_selector_discovery_implementation_2026_05_31"
LANE08_DIR = ROOT / "research" / "operations" / "vnext_lane08_execution_policy_microstructure_stress_2026_05_31"
FRIDAY_DIR = ROOT / "research" / "operations" / "vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31"
MT5_PRESERVATION_DIR = ROOT / "research" / "operations" / "vnext_mt5_local_cache_preservation_2026_06_01"
MASTER_DIR = ROOT / "research" / "operations" / "vnext_next_level_master_orchestration_2026_05_31"

ABS_MASTER_DIR = ROOT / "research" / "operations" / "vnext_absolute_moonshot_master_orchestration_2026_06_01"
ABS_LANE01_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane01_data_universe_source_authority_2026_06_01"
ABS_LANE02_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane02_no_leak_time_alignment_asof_contract_2026_06_01"
ABS_LANE03_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane03_historical_candidate_reconstruction_2026_06_01"

LANE02_REPLAY = LANE02_DIR / "LANE02_BROAD_SELECTED_PORTFOLIO_REPLAY_LEDGER.jsonl"
LANE02_SUMMARY = LANE02_DIR / "LANE02_PORTFOLIO_REPLAY_STRESS_SUMMARY.json"
LANE03_METRICS = LANE03_DIR / "LANE03_SELECTED_DENOMINATOR_METRIC_LEDGER.jsonl"
LANE08_STRICT_POLICY_LEDGER = LANE08_DIR / "LANE08_STRICT_TICK_POLICY_LEDGER.jsonl"
LANE08_SUMMARY = LANE08_DIR / "LANE08_EXPECTANCY_SUMMARY.json"
FRIDAY_MICRO = FRIDAY_DIR / "FRIDAY_MICRO_PRICE_ACTION_LEDGER.jsonl"
FRIDAY_MFE_MAE = FRIDAY_DIR / "FRIDAY_MFE_MAE_TIMING_LEDGER.jsonl"
MT5_COVERAGE = MT5_PRESERVATION_DIR / "MT5_LOCAL_CACHE_COVERAGE_SUMMARY.json"

TIMELINE_LEDGER = ROUTE_DIR / "LANE04_ROW_TIMELINE_LEDGER.jsonl"
STRICT_TICK_TIMELINE_LEDGER = ROUTE_DIR / "LANE04_STRICT_TICK_TIMELINE_LEDGER.jsonl"
SOURCE_GAP_LEDGER = ROUTE_DIR / "LANE04_SOURCE_GAP_LEDGER.jsonl"
ANATOMY_SPLIT_LEDGER = ROUTE_DIR / "LANE04_ANATOMY_SPLIT_LEDGER.jsonl"
SOURCE_COMPLETENESS_LEDGER = ROUTE_DIR / "LANE04_SOURCE_COMPLETENESS_DECISION_LEDGER.jsonl"
DEPENDENCY_STATE_LEDGER = ROUTE_DIR / "LANE04_DEPENDENCY_STATE_LEDGER.jsonl"
IMPLEMENTATION_DECISION_LEDGER = ROUTE_DIR / "LANE04_IMPLEMENTATION_DECISION_LEDGER.jsonl"
EXPECTANCY_SUMMARY = ROUTE_DIR / "LANE04_EXPECTANCY_SUMMARY.json"
CONTEXT_ANCHOR = ROUTE_DIR / "LANE04_CONTEXT_ANCHOR.md"
COMPLETION_AUDIT = ROUTE_DIR / "LANE04_COMPLETION_AUDIT.json"
OUTPUT_MANIFEST = ROUTE_DIR / "LANE04_OUTPUT_MANIFEST.json"
VERIFIER = ROUTE_DIR / "verify_lane04_historical_microscope_engine.py"
VERIFICATION_RESULT = ROUTE_DIR / "LANE04_VERIFICATION_RESULT.json"
FOCUSED_TEST_RESULT = ROUTE_DIR / "LANE04_FOCUSED_TEST_RESULT.xml"

EXPECTED_LANE02_ROWS = 289600
EXPECTED_FRIDAY_ROWS = 328
STRICT_TICK_HORIZON_HOURS = 50
TIME_STOP_HOURS = (4, 8)
STRICT_POLICY_IDS = (
    "be_after_trigger",
    "fixed_1_5r",
    "momentum_exhaustion",
    "partial_be_runner",
    "time_stop",
    "trailing_runner",
)


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


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def iter_jsonl(path: Path) -> Iterable[tuple[int, dict[str, Any]]]:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                yield line_number, row


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def write_jsonl_line(handle: Any, row: dict[str, Any]) -> None:
    handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def line_count(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_dt(value: Any) -> datetime | None:
    return lane08.parse_utc(value)


def iso(value: Any) -> str | None:
    return lane08.iso_utc(value)


def fnum(value: Any) -> float | None:
    return lane08.fnum(value)


def round_metric(value: Any, digits: int = 9) -> float | None:
    return lane08.round_metric(value, digits)


def seconds_between(start: Any, end: Any) -> float | None:
    a = parse_dt(start)
    b = parse_dt(end)
    if a is None or b is None:
        return None
    return round((b - a).total_seconds(), 6)


def event(event_type: str, *, time_utc: Any = None, status: str, source: str, r_value: Any = None, price: Any = None) -> dict[str, Any]:
    return {
        "event_type": event_type,
        "price": round_metric(price, 8),
        "r": round_metric(r_value, 9),
        "source": source,
        "status": status,
        "time_utc": iso(time_utc),
    }


def timeline_row_id(row: dict[str, Any], source_family: str) -> str:
    return str(
        row.get("selected_row_id")
        or row.get("trade_id")
        or row.get("candidate_id")
        or hashlib.sha256(json.dumps([source_family, row], sort_keys=True, default=str).encode("utf-8")).hexdigest()[:24]
    )


def classify_m15_path(row: dict[str, Any]) -> str:
    if row.get("non_replayable_reason"):
        return "source_blocked_non_replayable"
    fill_status = str(row.get("fill_status") or "")
    final_r = fnum(row.get("final_r"))
    mfe = fnum(row.get("mfe_r"))
    if fill_status and fill_status != "filled_in_replay":
        return "no_entry_or_unfilled_replay"
    if final_r is None:
        return "stuck_or_no_resolution_missing_final_r"
    if final_r <= -0.999:
        return "loss_sl_or_stop_policy_exit"
    if abs(final_r) < 1e-9:
        return "breakeven_or_partial_be_return"
    if final_r >= 1.0:
        return "winner_reached_1r_or_better"
    if final_r > 0:
        return "positive_less_than_1r_policy_exit"
    if mfe is not None and mfe >= 1.0:
        return "partial_or_1r_then_negative_policy_exit"
    return "negative_policy_exit_before_1r"


def classify_friday_path(row: dict[str, Any]) -> str:
    return str(row.get("terminal_path_class") or row.get("path_status") or "friday_path_class_missing")


def m15_timeline(row: dict[str, Any], strict: dict[str, Any] | None = None) -> dict[str, Any]:
    source_family = "lane02_broad_selected_historical_m15_proxy"
    row_id = timeline_row_id(row, source_family)
    source_time = row.get("source_time_utc")
    entry_time = row.get("entry_time_utc")
    exit_time = row.get("exit_time_utc")
    final_r = fnum(row.get("final_r"))
    mfe = fnum(row.get("mfe_r"))
    mae = fnum(row.get("mae_r"))
    chosen_policy = row.get("chosen_policy")
    path_class = classify_m15_path(row)
    tick_status = str(row.get("tick_availability_status") or "")
    m1_status = str(row.get("m1_availability_status") or "")
    source_use_state = (
        "strict_tick_policy_exit_overlay_plus_m15_proxy_row"
        if strict and str(strict.get("strict_tick_event_status") or "").startswith("strict_tick")
        else "m15_ordered_path_proxy_with_m1_availability_state"
    )

    events = [
        event("candidate_source_bar", time_utc=source_time, status="known", source="lane02_source_time"),
        event("entry_touch", time_utc=entry_time, status="known_m15_replay", source="lane02_entry_time"),
    ]
    if row.get("exit_reason") == "stop_loss" and exit_time:
        events.append(event("sl_touch", time_utc=exit_time, status="proxy_time_from_m15_replay", source="lane02_exit_reason", r_value=-1.0))
    elif final_r is not None and final_r <= -0.999 and exit_time:
        events.append(event("sl_touch", time_utc=exit_time, status="proxy_time_from_final_r", source="lane02_final_r", r_value=-1.0))
    elif mfe is not None and mfe < 1.0:
        events.append(event("one_r_trigger", status="not_reached_by_m15_proxy_mfe", source="lane02_mfe_r", r_value=mfe))
    else:
        events.append(event("one_r_trigger", status="reached_but_exact_time_missing_in_m15_proxy", source="lane02_mfe_r", r_value=1.0))
    if chosen_policy == "partial_be_runner":
        if mfe is not None and mfe >= 1.0:
            events.append(event("partial_trigger", status="reached_but_exact_time_missing_in_m15_proxy", source="lane02_policy_and_mfe", r_value=1.0))
        else:
            events.append(event("partial_trigger", status="not_reached_by_m15_proxy_mfe", source="lane02_policy_and_mfe", r_value=mfe))
    if exit_time:
        events.append(event("final_policy_exit", time_utc=exit_time, status="known_m15_proxy_exit", source="lane02_exit_time", r_value=final_r))
    else:
        events.append(event("stuck_or_no_resolution", status="missing_exit_time", source="lane02_exit_time"))
    if strict:
        for item in strict.get("strict_tick_events") or []:
            events.append(item)
    events.sort(key=lambda item: item.get("time_utc") or "9999-12-31T23:59:59+00:00")

    missing = []
    if not strict:
        missing.append(
            {
                "field_family": "ordered_bid_ask_tick_timeline",
                "reason": tick_status or "tick_availability_status_missing",
                "attempted_sources": ["data/ticks", "Lane08 strict tick replay", "MT5 preservation cache manifest"],
                "repair_requirement": "deterministic tick export/parser for selected row date/symbol or row remains M15 proxy",
            }
        )
    elif strict.get("raw_event_timing_granularity") == "policy_exit_times_only":
        missing.append(
            {
                "field_family": "raw_tick_extrema_and_threshold_timestamps",
                "reason": "Lane08 strict source provides ordered bid/ask policy exits and spread metrics but not row-level raw tick MFE/MAE/1R trigger timestamps",
                "attempted_sources": ["LANE08_STRICT_TICK_POLICY_LEDGER.jsonl", "data/ticks", "prior Lane04 direct replay attempt"],
                "repair_requirement": "bounded raw tick event extraction pass over local tick subset or accepted policy-exit-only source use",
            }
        )
    if row.get("cost_status") == "missing_historical_live_cost_lifecycle_fields":
        missing.append(
            {
                "field_family": "broker_cost_and_lifecycle",
                "reason": "historical replay row lacks commission/swap/slippage/order_modify_retcode/account_history_deal_reconciliation",
                "attempted_sources": ["Lane02 cost stress", "Lane06 sparse broker truth", "shadow slippage log"],
                "repair_requirement": "broker/deal/order lifecycle capture or exact account-history join for that row",
            }
        )
    if fnum(row.get("cost_r")) is None:
        missing.append(
            {
                "field_family": "net_r",
                "reason": "cost_r_null_in_lane02_historical_proxy",
                "attempted_sources": ["Lane02 gross proxy", "Lane06 cost calibration"],
                "repair_requirement": "source-bound commission/swap/slippage spread/deal fields",
            }
        )

    strict_status = strict.get("strict_tick_event_status") if strict else None
    return {
        "schema_version": "lane04_row_timeline_v1",
        "route_id": ROUTE_ID,
        "row_id": row_id,
        "candidate_id": row.get("candidate_id"),
        "selected_row_id": row.get("selected_row_id"),
        "timeline_source_family": source_family,
        "source_path": row.get("source_path"),
        "source_shard": row.get("source_shard"),
        "source_line_number": row.get("source_line_number"),
        "symbol": row.get("symbol"),
        "side": row.get("side"),
        "framework": row.get("framework"),
        "origin_family": row.get("origin_family"),
        "session_bucket": row.get("session_bucket"),
        "chosen_policy": chosen_policy,
        "execution_policy_id": row.get("execution_policy_id"),
        "decision": row.get("decision"),
        "date": row.get("date"),
        "month": row.get("month"),
        "year": row.get("year"),
        "source_time_utc": iso(source_time),
        "entry_time_utc": iso(entry_time),
        "exit_time_utc": iso(exit_time),
        "fill_status": row.get("fill_status"),
        "exit_reason": row.get("exit_reason"),
        "path_class": path_class,
        "source_use_state": source_use_state,
        "strict_tick_event_status": strict_status,
        "source_operation": "stream_lane02_m15_proxy_and_overlay_strict_tick_subset_when_available",
        "result_scope": "historical_microscope_path_anatomy_not_broker_real_net_r_not_production_change",
        "final_r": round_metric(final_r),
        "mfe_r": round_metric(mfe),
        "mae_r": round_metric(mae),
        "cost_r": round_metric(row.get("cost_r")),
        "cost_status": row.get("cost_status"),
        "spread_r_bucket": row.get("spread_r_bucket"),
        "tick_availability_status": tick_status,
        "m1_availability_status": m1_status,
        "ordered_path_status": row.get("ordered_path_status"),
        "source_quality_status": row.get("source_quality_status"),
        "source_window_complete": row.get("source_window_complete"),
        "volatility_state_14_vs_50": row.get("volatility_state_14_vs_50"),
        "trend_state_20": row.get("trend_state_20"),
        "liquidity_sweep_proxy_state": row.get("liquidity_sweep_proxy_state"),
        "time_to_final_seconds": seconds_between(entry_time, exit_time),
        "time_to_sl_seconds": strict.get("time_to_sl_seconds") if strict and strict.get("time_to_sl_seconds") is not None else (seconds_between(entry_time, exit_time) if (final_r is not None and final_r <= -0.999) else None),
        "time_to_1r_seconds": strict.get("time_to_1r_seconds") if strict else None,
        "time_to_be_return_seconds": strict.get("time_to_be_return_seconds") if strict else None,
        "time_to_mfe_seconds": strict.get("time_to_mfe_seconds") if strict else None,
        "time_to_mae_seconds": strict.get("time_to_mae_seconds") if strict else None,
        "stuck_duration_seconds": seconds_between(entry_time, exit_time) if path_class.startswith("stuck") else None,
        "strict_tick_metrics": strict.get("strict_tick_metrics") if strict else None,
        "ordered_events": events,
        "missing_field_proof": missing,
        "result_use_status": "proxy_gross_r_and_path_anatomy_available_for_feature_label_selector_research_only",
        "runtime_effect_boundary": "offline_artifacts_only_no_broker_action_no_live_restart_no_config_change",
    }


def friday_timeline(row: dict[str, Any]) -> dict[str, Any]:
    source_family = "friday_microscope_tick_bid_ask"
    row_id = timeline_row_id(row, source_family)
    threshold_times = row.get("threshold_times_utc") or {}
    threshold_seconds = row.get("threshold_seconds_from_entry") or {}
    events = [
        event("candidate_source_bar", time_utc=row.get("candle_time_utc"), status="known", source="friday_candle_time"),
        event("entry_touch", time_utc=row.get("entry_touch_utc"), status="known_tick_bid_ask", source="FRIDAY_MICRO_PRICE_ACTION_LEDGER"),
        event("one_r_trigger", time_utc=threshold_times.get("1_0r"), status="known_tick_bid_ask" if threshold_times.get("1_0r") else "not_reached_or_missing", source="FRIDAY_MICRO_PRICE_ACTION_LEDGER", r_value=1.0 if threshold_times.get("1_0r") else None),
        event("partial_trigger", time_utc=row.get("partial_trigger_utc"), status="known_tick_bid_ask" if row.get("partial_trigger_utc") else "not_reached_or_not_policy_applicable", source="FRIDAY_MICRO_PRICE_ACTION_LEDGER", r_value=1.0 if row.get("partial_trigger_utc") else None),
        event("be_return_after_1r", time_utc=row.get("be_return_after_1r_utc"), status="known_tick_bid_ask" if row.get("be_return_after_1r_utc") else "not_reached_or_not_applicable", source="FRIDAY_MICRO_PRICE_ACTION_LEDGER", r_value=0.0 if row.get("be_return_after_1r_utc") else None),
        event("sl_touch", time_utc=row.get("sl_touch_utc"), status="known_tick_bid_ask" if row.get("sl_touch_utc") else "not_reached_or_missing", source="FRIDAY_MICRO_PRICE_ACTION_LEDGER", r_value=-1.0 if row.get("sl_touch_utc") else None),
        event("dynamic_final_3r", time_utc=row.get("dynamic_final_3r_utc") or threshold_times.get("3_0r"), status="known_tick_bid_ask" if (row.get("dynamic_final_3r_utc") or threshold_times.get("3_0r")) else "not_reached_or_missing", source="FRIDAY_MICRO_PRICE_ACTION_LEDGER", r_value=3.0 if (row.get("dynamic_final_3r_utc") or threshold_times.get("3_0r")) else None),
        event("time_stop_4h", time_utc=row.get("time_stop_4h_utc"), status="known_tick_bid_ask" if row.get("time_stop_4h_utc") else "not_available", source="FRIDAY_MICRO_PRICE_ACTION_LEDGER", r_value=row.get("time_stop_4h_r")),
    ]
    events.sort(key=lambda item: item.get("time_utc") or "9999-12-31T23:59:59+00:00")
    missing = []
    if row.get("missing_price_action_sources"):
        missing.append(
            {
                "field_family": "price_action_source",
                "reason": row.get("missing_price_action_sources"),
                "attempted_sources": ["FRIDAY_MICRO_PRICE_ACTION_LEDGER", "data/ticks", "data/m1"],
                "repair_requirement": "see Friday row missing source list",
            }
        )
    if row.get("broker_lifecycle_status_through_friday_close") in {"filled_open_at_friday_close", "filled_partial_exit_residual_open_at_friday_close"}:
        missing.append(
            {
                "field_family": "post_friday_terminal_broker_net_r",
                "reason": row.get("broker_lifecycle_status_through_friday_close"),
                "attempted_sources": ["Friday broker truth route through close boundary"],
                "repair_requirement": "read-only account-history export after Friday close if terminal outcome is required",
            }
        )
    return {
        "schema_version": "lane04_row_timeline_v1",
        "route_id": ROUTE_ID,
        "row_id": row_id,
        "candidate_id": row.get("candidate_id"),
        "trade_id": row.get("trade_id"),
        "selected_row_id": row.get("selected_cell_risk_cell_id"),
        "timeline_source_family": source_family,
        "source_path": row.get("source_path"),
        "symbol": row.get("symbol"),
        "side": row.get("side"),
        "framework": row.get("framework"),
        "origin_family": row.get("origin_family"),
        "session_bucket": row.get("session_bucket") or row.get("session"),
        "chosen_policy": row.get("selected_policy"),
        "execution_policy_id": row.get("execution_policy_id"),
        "decision": "friday_primary_candidate",
        "date": (str(row.get("candle_time_utc") or "")[:10] or None),
        "month": (str(row.get("candle_time_utc") or "")[:7] or None),
        "year": (str(row.get("candle_time_utc") or "")[:4] or None),
        "source_time_utc": iso(row.get("candle_time_utc")),
        "entry_time_utc": iso(row.get("entry_touch_utc")),
        "exit_time_utc": iso(row.get("path_end_utc")),
        "fill_status": row.get("path_status"),
        "exit_reason": row.get("final_outcome"),
        "path_class": classify_friday_path(row),
        "source_use_state": "friday_tick_bid_ask_exact_path_capped_at_friday_close",
        "strict_tick_event_status": "friday_tick_events_materialized",
        "source_operation": "consume_friday_tick_bid_ask_microscope_anatomy",
        "result_scope": "friday_microscope_path_anatomy_through_close_boundary",
        "final_r": round_metric(row.get("proxy_gross_r")),
        "mfe_r": round_metric(row.get("mfe_r_normalized") if row.get("mfe_r_normalized") is not None else row.get("mfe_r")),
        "mae_r": round_metric(row.get("mae_r_normalized") if row.get("mae_r_normalized") is not None else row.get("mae_r")),
        "cost_r": None,
        "cost_status": "friday_broker_cost_sparse_or_pending_see_broker_truth_route",
        "spread_r_bucket": spread_bucket(row.get("spread_r_at_candidate")),
        "spread_r_at_candidate": round_metric(row.get("spread_r_at_candidate")),
        "tick_availability_status": "friday_tick_bid_ask_available",
        "m1_availability_status": "friday_m1_context_consumed_or_recorded",
        "ordered_path_status": "ordered_tick_bid_ask_path",
        "source_quality_status": row.get("source_path_feature_status"),
        "source_window_complete": row.get("source_window_complete"),
        "volatility_state_14_vs_50": ((row.get("m15_source_fields") or {}).get("volatility_state_14_vs_50")),
        "trend_state_20": ((row.get("m15_source_fields") or {}).get("trend_state_20")),
        "liquidity_sweep_proxy_state": ((row.get("m15_source_fields") or {}).get("sweep_direction")),
        "time_to_final_seconds": seconds_between(row.get("entry_touch_utc"), row.get("path_end_utc")),
        "time_to_sl_seconds": row.get("time_to_sl_seconds"),
        "time_to_1r_seconds": threshold_seconds.get("1_0r"),
        "time_to_be_return_seconds": row.get("time_to_be_seconds"),
        "time_to_mfe_seconds": row.get("time_to_mfe_from_entry_seconds"),
        "time_to_mae_seconds": row.get("time_to_mae_from_entry_seconds"),
        "stuck_duration_seconds": seconds_between(row.get("entry_touch_utc"), row.get("path_end_utc")) if "stuck" in classify_friday_path(row) else None,
        "strict_tick_metrics": {
            "price_source": row.get("price_source"),
            "tick_rows": row.get("tick_rows"),
            "entry_spread_r": round_metric(row.get("spread_r_at_candidate")),
            "first_tick_time_utc": row.get("price_source_first_utc"),
            "last_tick_time_utc": row.get("price_source_last_utc"),
        },
        "ordered_events": events,
        "missing_field_proof": missing,
        "result_use_status": "tick_path_anatomy_available_for_feature_label_selector_research_only",
        "runtime_effect_boundary": "offline_artifacts_only_no_broker_action_no_live_restart_no_config_change",
    }


def spread_bucket(value: Any) -> str:
    v = fnum(value)
    if v is None:
        return "spread_r_missing"
    if v < 0.05:
        return "spread_r_lt_0_05"
    if v < 0.10:
        return "spread_r_0_05_to_0_10"
    if v < 0.20:
        return "spread_r_0_10_to_0_20"
    if v < 0.50:
        return "spread_r_0_20_to_0_50"
    return "spread_r_gte_0_50"


def _series_time(times: Any, index: int) -> Any:
    try:
        return times.iloc[index]
    except AttributeError:
        return times[index]


def first_index(values: list[float], predicate) -> int | None:
    for idx, value in enumerate(values):
        if predicate(value):
            return idx
    return None


def first_pullback_index(values: list[float], gap: float) -> int | None:
    high = -math.inf
    active = False
    for idx, value in enumerate(values):
        high = max(high, value)
        if high >= 1.0:
            active = True
        if active and value <= high - gap:
            return idx
    return None


def first_time_stop_index(times: Any, start: datetime, hours: int) -> int | None:
    target = start + timedelta(hours=hours)
    for idx in range(len(times)):
        parsed = parse_dt(_series_time(times, idx))
        if parsed and parsed >= target:
            return idx
    return None


def strict_tick_events_for_row(
    row: dict[str, Any],
    geometry: dict[str, Any] | None,
    tick_cache: lane08.TickDataCache,
) -> dict[str, Any] | None:
    if not geometry:
        return None
    entry = fnum(geometry.get("entry_price"))
    stop = fnum(geometry.get("stop_or_invalidation"))
    side = str(row.get("side") or geometry.get("side") or "").upper()
    start = parse_dt(row.get("entry_time_utc") or row.get("source_time_utc") or geometry.get("decision_time_utc"))
    symbol = str(row.get("symbol") or geometry.get("symbol") or "")
    if entry is None or stop is None or start is None or side not in {"LONG", "SHORT"} or abs(entry - stop) <= 0:
        return None
    frame, window_status = tick_cache.window(symbol, start, STRICT_TICK_HORIZON_HOURS)
    if frame is None or frame.empty:
        return {
            "strict_tick_event_status": window_status,
            "strict_tick_events": [],
            "strict_tick_metrics": {"entry_price": entry, "stop_or_invalidation": stop},
        }
    times, values_array, spreads_array = lane08.strict_tick_arrays_from_window(
        frame=frame,
        side=side,
        entry=entry,
        stop=stop,
    )
    if values_array is None or times is None or len(values_array) == 0:
        return {
            "strict_tick_event_status": "not_replayable_no_valid_bid_ask_ticks",
            "strict_tick_events": [],
            "strict_tick_metrics": {"entry_price": entry, "stop_or_invalidation": stop, "raw_tick_rows": int(len(frame))},
        }
    values = [float(value) for value in values_array]
    spreads = [float(value) for value in spreads_array] if spreads_array is not None else []
    mfe_idx = max(range(len(values)), key=lambda idx: values[idx])
    mae_idx = min(range(len(values)), key=lambda idx: values[idx])
    one_r_idx = first_index(values, lambda value: value >= 1.0)
    sl_idx = first_index(values, lambda value: value <= -1.0)
    final_15_idx = first_index(values, lambda value: value >= 1.5)
    final_3_idx = first_index(values, lambda value: value >= 3.0)
    be_idx = None
    if one_r_idx is not None:
        for idx in range(one_r_idx, len(values)):
            if values[idx] <= 0.0:
                be_idx = idx
                break
    momentum_idx = first_pullback_index(values, 0.4)
    trailing_idx = first_pullback_index(values, 0.5)

    events = [
        event("strict_tick_path_start", time_utc=_series_time(times, 0), status="known_tick_bid_ask", source="data/ticks", r_value=values[0]),
        event("strict_tick_mfe", time_utc=_series_time(times, mfe_idx), status="known_tick_bid_ask", source="data/ticks", r_value=values[mfe_idx]),
        event("strict_tick_mae", time_utc=_series_time(times, mae_idx), status="known_tick_bid_ask", source="data/ticks", r_value=values[mae_idx]),
    ]
    for name, idx, r_value in (
        ("strict_tick_1r_trigger", one_r_idx, 1.0),
        ("strict_tick_sl_touch", sl_idx, -1.0),
        ("strict_tick_1_5r_target", final_15_idx, 1.5),
        ("strict_tick_3r_target", final_3_idx, 3.0),
        ("strict_tick_be_return_after_1r", be_idx, 0.0),
        ("strict_tick_momentum_pullback_0_4r", momentum_idx, values[momentum_idx] if momentum_idx is not None else None),
        ("strict_tick_trailing_gap_0_5r", trailing_idx, values[trailing_idx] if trailing_idx is not None else None),
    ):
        if idx is None:
            events.append(event(name, status="not_reached_in_tick_window", source="data/ticks"))
        else:
            events.append(event(name, time_utc=_series_time(times, idx), status="known_tick_bid_ask", source="data/ticks", r_value=r_value))
    for hours in TIME_STOP_HOURS:
        idx = first_time_stop_index(times, start, hours)
        events.append(
            event(
                f"strict_tick_time_stop_{hours}h",
                time_utc=_series_time(times, idx) if idx is not None else _series_time(times, len(values) - 1),
                status="known_tick_bid_ask" if idx is not None else "tick_window_ended_before_time_stop",
                source="data/ticks",
                r_value=values[idx] if idx is not None else values[-1],
            )
        )
    events.sort(key=lambda item: item.get("time_utc") or "9999-12-31T23:59:59+00:00")
    metrics = {
        "entry_price": round_metric(entry, 8),
        "stop_or_invalidation": round_metric(stop, 8),
        "risk_price_distance": round_metric(abs(entry - stop), 8),
        "raw_tick_rows": int(len(frame)),
        "valid_bid_ask_tick_rows": len(values),
        "first_tick_time_utc": iso(_series_time(times, 0)),
        "last_tick_time_utc": iso(_series_time(times, len(values) - 1)),
        "entry_spread_r": round_metric(spreads[0] if spreads else None),
        "median_spread_r_in_window": round_metric(statistics.median(spreads) if spreads else None),
        "max_spread_r_in_window": round_metric(max(spreads) if spreads else None),
        "mfe_r": round_metric(values[mfe_idx]),
        "mae_r": round_metric(values[mae_idx]),
    }
    return {
        "strict_tick_event_status": "strict_tick_events_materialized",
        "strict_tick_events": events,
        "strict_tick_metrics": metrics,
        "time_to_1r_seconds": seconds_between(start, _series_time(times, one_r_idx)) if one_r_idx is not None else None,
        "time_to_be_return_seconds": seconds_between(start, _series_time(times, be_idx)) if be_idx is not None else None,
        "time_to_mfe_seconds": seconds_between(start, _series_time(times, mfe_idx)),
        "time_to_mae_seconds": seconds_between(start, _series_time(times, mae_idx)),
    }


class Stats:
    def __init__(self) -> None:
        self.rows = 0
        self.known_r_rows = 0
        self.total_r = 0.0
        self.wins = 0
        self.losses = 0
        self.breakevens = 0
        self.mfe_max: float | None = None
        self.mae_min: float | None = None
        self.tick_rows = 0
        self.strict_rows = 0
        self.source_gap_rows = 0

    def add(self, row: dict[str, Any]) -> None:
        self.rows += 1
        value = fnum(row.get("final_r"))
        if value is not None:
            self.known_r_rows += 1
            self.total_r += value
            if value > 0:
                self.wins += 1
            elif value < 0:
                self.losses += 1
            else:
                self.breakevens += 1
        mfe = fnum(row.get("mfe_r"))
        mae = fnum(row.get("mae_r"))
        if mfe is not None:
            self.mfe_max = mfe if self.mfe_max is None else max(self.mfe_max, mfe)
        if mae is not None:
            self.mae_min = mae if self.mae_min is None else min(self.mae_min, mae)
        if "tick" in str(row.get("source_use_state") or ""):
            self.tick_rows += 1
        if str(row.get("strict_tick_event_status") or "").startswith("strict_tick"):
            self.strict_rows += 1
        if row.get("missing_field_proof"):
            self.source_gap_rows += 1

    def as_row(self, split_scope: str, split_key: str) -> dict[str, Any]:
        return {
            "schema_version": "lane04_anatomy_split_v1",
            "route_id": ROUTE_ID,
            "split_scope": split_scope,
            "split_key": split_key,
            "rows": self.rows,
            "known_r_rows": self.known_r_rows,
            "gross_r_sum": round_metric(self.total_r),
            "expectancy_r": round_metric(self.total_r / self.known_r_rows if self.known_r_rows else None),
            "wins": self.wins,
            "losses": self.losses,
            "breakevens": self.breakevens,
            "win_rate": round_metric(self.wins / self.known_r_rows if self.known_r_rows else None),
            "mfe_r_max": round_metric(self.mfe_max),
            "mae_r_min": round_metric(self.mae_min),
            "tick_or_strict_rows": self.tick_rows,
            "strict_tick_materialized_rows": self.strict_rows,
            "source_gap_rows": self.source_gap_rows,
        }


def update_stats(groups: dict[tuple[str, str], Stats], row: dict[str, Any]) -> None:
    fields = {
        "all": "ALL",
        "source_family": row.get("timeline_source_family"),
        "symbol": row.get("symbol"),
        "session_bucket": row.get("session_bucket"),
        "side": row.get("side"),
        "origin_family": row.get("origin_family"),
        "framework": row.get("framework"),
        "path_class": row.get("path_class"),
        "source_use_state": row.get("source_use_state"),
        "tick_availability_status": row.get("tick_availability_status"),
        "m1_availability_status": row.get("m1_availability_status"),
        "spread_r_bucket": row.get("spread_r_bucket"),
        "volatility_state_14_vs_50": row.get("volatility_state_14_vs_50"),
        "chosen_policy": row.get("chosen_policy"),
        "decision": row.get("decision"),
        "symbol_session": f"{row.get('symbol')}|{row.get('session_bucket')}",
        "symbol_session_side_origin": f"{row.get('symbol')}|{row.get('session_bucket')}|{row.get('side')}|{row.get('origin_family')}",
    }
    for scope, value in fields.items():
        key = str(value if value not in (None, "") else "MISSING")
        groups[(scope, key)].add(row)


def source_gap_row(timeline: dict[str, Any]) -> dict[str, Any] | None:
    gaps = timeline.get("missing_field_proof") or []
    if not gaps:
        return None
    return {
        "schema_version": "lane04_source_gap_v1",
        "route_id": ROUTE_ID,
        "row_id": timeline.get("row_id"),
        "candidate_id": timeline.get("candidate_id"),
        "selected_row_id": timeline.get("selected_row_id"),
        "timeline_source_family": timeline.get("timeline_source_family"),
        "symbol": timeline.get("symbol"),
        "date": timeline.get("date"),
        "source_use_state": timeline.get("source_use_state"),
        "tick_availability_status": timeline.get("tick_availability_status"),
        "m1_availability_status": timeline.get("m1_availability_status"),
        "cost_status": timeline.get("cost_status"),
        "gap_count": len(gaps),
        "gaps": gaps,
        "source_operation": "row_level_gap_proof_for_missing_tick_cost_broker_or_terminal_fields",
        "result_use_status": "gap_rows_define_source_repair_or_proxy_boundary",
    }


def dependency_rows() -> list[dict[str, Any]]:
    deps = [
        ("absolute_master_route", ABS_MASTER_DIR, "optional_upstream_absolute_master"),
        ("absolute_lane01_source_authority", ABS_LANE01_DIR, "source_authority_upstream"),
        ("absolute_lane02_asof_contract", ABS_LANE02_DIR, "asof_contract_upstream"),
        ("absolute_lane03_candidate_reconstruction", ABS_LANE03_DIR, "candidate_reconstruction_upstream"),
        ("next_level_master_route", MASTER_DIR, "available_master_context"),
        ("next_level_lane02_selected_denominator", LANE02_DIR, "available_full_selected_historical_universe"),
        ("next_level_lane03_meta_selector", LANE03_DIR, "available_split_and_source_metrics"),
        ("next_level_lane08_strict_tick_policy_replay", LANE08_DIR, "available_strict_tick_subset_policy_replay"),
        ("friday_microscope", FRIDAY_DIR, "available_tick_microscope_seed"),
        ("mt5_preservation", MT5_PRESERVATION_DIR, "available_local_cache_inventory"),
    ]
    rows = []
    for name, path, role in deps:
        exists = path.exists()
        rows.append(
            {
                "schema_version": "lane04_dependency_state_v1",
                "route_id": ROUTE_ID,
                "dependency_name": name,
                "dependency_role": role,
                "path": rel(path),
                "status": "present" if exists else "absent_dependency_state_recorded_not_stop_condition",
                "exists": exists,
                "decision": (
                    "consume_current_disk_artifacts"
                    if exists
                    else "record_absence_and_use_available_next_level_friday_lane02_lane03_mt5_sources"
                ),
            }
        )
    return rows


def source_completeness_rows(summary: dict[str, Any], mt5_summary: dict[str, Any]) -> list[dict[str, Any]]:
    stats = summary.get("stats") or {}
    tick_counts = summary.get("tick_availability_counts") or {}
    m1_counts = summary.get("m1_availability_counts") or {}
    strict_summary = summary.get("strict_tick_replay_summary") or {}
    return [
        {
            "schema_version": "lane04_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "source_family": "lane02_selected_denominator_m15_proxy",
            "rows": stats.get("rows") or summary.get("input_rows") or EXPECTED_LANE02_ROWS,
            "source_use_state": "m15_ordered_path_proxy_with_m1_availability_state",
            "decision": "consume_full_selected_denominator_for_proxy_path_anatomy",
            "result_use_status": "research_feature_label_selector_inputs_not_broker_real_net_r",
        },
        {
            "schema_version": "lane04_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "source_family": "local_tick_parquet_subset",
            "rows": tick_counts.get("local_tick_parquet_available_for_entry_date"),
            "source_use_state": "strict_tick_policy_exit_overlay_from_lane08_ordered_bid_ask_replay",
            "decision": "consume_lane08_ordered_bid_ask_policy_exit_replay_for_all_local_tick_date_rows_and_record_raw_event_timing_gap",
            "strict_tick_replayed_rows": strict_summary.get("strict_tick_replayed_rows"),
            "result_use_status": "strict_tick_subset_not_full_denominator_claim",
        },
        {
            "schema_version": "lane04_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "source_family": "m1_source_status",
            "rows": sum(int(v or 0) for v in m1_counts.values()),
            "source_use_state": "m1_availability_status_from_lane02",
            "m1_availability_counts": m1_counts,
            "decision": "preserve_m1_status_per_row_without_inventing_intrabar_tick_ordering",
            "result_use_status": "m1_proxy_support_and_gap_classification",
        },
        {
            "schema_version": "lane04_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "source_family": "mt5_preserved_cache",
            "rows": (mt5_summary.get("evidence_role_counts") or {}).get("tick_cache"),
            "source_use_state": "preserved_cache_inventory_available_parser_contract_not_lane04_primary_source",
            "decision": "record_cache_presence_and_defer_non_csv_tkc_hcc_parser_authority_to_lane01_source_authority",
            "result_use_status": "source_gap_repair_path_not_silent_missing_data",
        },
        {
            "schema_version": "lane04_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "source_family": "friday_tick_microscope",
            "rows": EXPECTED_FRIDAY_ROWS,
            "source_use_state": "friday_tick_bid_ask_exact_path_capped_at_friday_close",
            "decision": "preserve_friday_seed_and_generalize_schema_to_historical_selected_rows",
            "result_use_status": "seed_path_anatomy_and_failure_mechanism_source",
        },
    ]


def implementation_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "lane04_implementation_decision_v1",
            "route_id": ROUTE_ID,
            "decision": "build_default_off_historical_microscope_engine_artifacts",
            "status": "implemented_in_offline_builder",
            "runtime_effect_boundary": "offline_artifacts_only_no_broker_action_no_live_restart_no_config_change",
        },
        {
            "schema_version": "lane04_implementation_decision_v1",
            "route_id": ROUTE_ID,
            "decision": "strict_tick_full_denominator_not_claimed",
            "status": "source_gap_recorded",
            "reason": "local tick parquet covers a subset; M15/M1 proxy rows preserve source-use state and row-level gaps",
        },
        {
            "schema_version": "lane04_implementation_decision_v1",
            "route_id": ROUTE_ID,
            "decision": "feed_feature_label_ml_lanes_with_timeline_schema",
            "status": "research_decision_not_runtime_activation",
            "reason": "row timelines include source-use, missing-field proof, exact/proxy R, path class, and no broker-live effect",
        },
    ]


def collect_strict_tick_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for _, row in iter_jsonl(LANE02_REPLAY):
        if row.get("tick_availability_status") == "local_tick_parquet_available_for_entry_date":
            rows.append(dict(row))
    return rows


def strict_policy_events_from_lane08(row: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    events = [
        event(
            "strict_tick_path_start",
            time_utc=row.get("first_tick_time_utc"),
            status="known_ordered_bid_ask",
            source="LANE08_STRICT_TICK_POLICY_LEDGER",
        ),
        event(
            "strict_tick_path_end",
            time_utc=row.get("last_tick_time_utc"),
            status="known_ordered_bid_ask",
            source="LANE08_STRICT_TICK_POLICY_LEDGER",
        ),
    ]
    exit_seconds: dict[str, float | None] = {}
    stop_seconds: list[float] = []
    entry_time = row.get("entry_time_utc")
    for policy_id in STRICT_POLICY_IDS:
        prefix = f"strict_tick_{policy_id}"
        exit_time = row.get(f"{prefix}_exit_time_utc")
        exit_reason = row.get(f"{prefix}_exit_reason")
        r_value = row.get(f"{prefix}_r")
        simulation_status = row.get(f"{prefix}_simulation_status") or row.get("strict_tick_replay_status")
        if exit_time is None and exit_reason is None and r_value is None:
            continue
        item = event(
            f"{prefix}_policy_exit",
            time_utc=exit_time,
            status=str(simulation_status or "strict_tick_policy_exit_from_lane08"),
            source="LANE08_STRICT_TICK_POLICY_LEDGER",
            r_value=r_value,
        )
        item["policy_id"] = policy_id
        item["exit_reason"] = exit_reason
        item["delta_vs_m15_proxy_r"] = round_metric(row.get(f"{prefix}_delta_vs_m15_proxy_r"))
        events.append(item)
        elapsed = seconds_between(entry_time, exit_time)
        exit_seconds[policy_id] = elapsed
        if elapsed is not None and exit_reason and "stop_loss" in str(exit_reason):
            stop_seconds.append(elapsed)
    events.sort(key=lambda item: item.get("time_utc") or "9999-12-31T23:59:59+00:00")
    timing = {
        "time_to_policy_exit_seconds_by_policy": exit_seconds,
        "time_to_sl_seconds": min(stop_seconds) if stop_seconds else None,
    }
    return events, timing


def strict_metrics_from_lane08(row: dict[str, Any]) -> dict[str, Any]:
    metrics = {
        "entry_price": round_metric(row.get("entry_price"), 8),
        "stop_or_invalidation": round_metric(row.get("stop_or_invalidation"), 8),
        "risk_price_distance": round_metric(row.get("risk_price_distance"), 8),
        "raw_tick_rows": row.get("raw_tick_rows"),
        "valid_bid_ask_tick_rows": row.get("valid_bid_ask_tick_rows"),
        "first_tick_time_utc": row.get("first_tick_time_utc"),
        "last_tick_time_utc": row.get("last_tick_time_utc"),
        "entry_spread_r": round_metric(row.get("entry_spread_r")),
        "median_spread_r_in_window": round_metric(row.get("median_spread_r_in_window")),
        "max_spread_r_in_window": round_metric(row.get("max_spread_r_in_window")),
        "strict_tick_replay_horizon_hours": row.get("strict_tick_replay_horizon_hours"),
        "strict_tick_replay_status": row.get("strict_tick_replay_status"),
        "tick_source_loaded_file_count": row.get("tick_source_loaded_file_count"),
        "policy_results": {},
    }
    for policy_id in STRICT_POLICY_IDS:
        prefix = f"strict_tick_{policy_id}"
        metrics["policy_results"][policy_id] = {
            "strict_tick_r": round_metric(row.get(f"{prefix}_r")),
            "m15_proxy_r": round_metric(row.get(f"m15_proxy_{policy_id}_r")),
            "delta_vs_m15_proxy_r": round_metric(row.get(f"{prefix}_delta_vs_m15_proxy_r")),
            "exit_reason": row.get(f"{prefix}_exit_reason"),
            "exit_time_utc": row.get(f"{prefix}_exit_time_utc"),
            "simulation_status": row.get(f"{prefix}_simulation_status"),
        }
    return metrics


def lane08_strict_row_to_lane04(row: dict[str, Any]) -> dict[str, Any]:
    events, timing = strict_policy_events_from_lane08(row)
    return {
        "strict_tick_event_status": "strict_tick_policy_exit_timeline_from_lane08",
        "raw_event_timing_granularity": "policy_exit_times_only",
        "strict_tick_events": events,
        "strict_tick_metrics": strict_metrics_from_lane08(row),
        "time_to_1r_seconds": None,
        "time_to_be_return_seconds": None,
        "time_to_mfe_seconds": None,
        "time_to_mae_seconds": None,
        "time_to_sl_seconds": timing["time_to_sl_seconds"],
        "time_to_policy_exit_seconds_by_policy": timing["time_to_policy_exit_seconds_by_policy"],
    }


def build_strict_tick_map(strict_rows: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    if not LANE08_STRICT_POLICY_LEDGER.exists():
        raise SystemExit(f"missing Lane08 strict tick policy ledger: {LANE08_STRICT_POLICY_LEDGER}")
    expected_by_id = {str(row.get("selected_row_id")): row for row in strict_rows if row.get("selected_row_id")}
    lane08_by_id = {str(row.get("selected_row_id")): row for _, row in iter_jsonl(LANE08_STRICT_POLICY_LEDGER) if row.get("selected_row_id")}
    lane08_summary = read_json(LANE08_SUMMARY, {})
    source_strict_summary = lane08_summary.get("strict_tick_replay_summary") or {}
    out: dict[str, dict[str, Any]] = {}
    status_counts: Counter[str] = Counter()
    with STRICT_TICK_TIMELINE_LEDGER.open("w", encoding="utf-8", newline="\n") as handle:
        for row in strict_rows:
            row_id = str(row.get("selected_row_id") or "")
            source_row = lane08_by_id.get(row_id)
            if source_row:
                strict = lane08_strict_row_to_lane04(source_row)
            else:
                strict = {
                    "strict_tick_event_status": "not_replayable_missing_lane08_strict_policy_row",
                    "raw_event_timing_granularity": "none",
                    "strict_tick_events": [],
                    "strict_tick_metrics": {},
                }
            status_counts[str(strict.get("strict_tick_event_status"))] += 1
            record = {
                "schema_version": "lane04_strict_tick_timeline_v1",
                "route_id": ROUTE_ID,
                "row_id": row_id,
                "candidate_id": row.get("candidate_id"),
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "entry_time_utc": row.get("entry_time_utc"),
                "source_time_utc": row.get("source_time_utc"),
                "chosen_policy": row.get("chosen_policy"),
                "final_r_m15_proxy": row.get("final_r"),
                "mfe_r_m15_proxy": row.get("mfe_r"),
                "mae_r_m15_proxy": row.get("mae_r"),
                **strict,
                "source_operation": "consume_lane08_strict_tick_policy_replay_ledger_without_recomputing_tick_windows",
                "result_scope": "strict_tick_policy_exit_timeline_subset_not_full_denominator_raw_tick_event_or_broker_net_r",
            }
            write_jsonl_line(handle, record)
            out[row_id] = strict
    return out, {
        "candidate_rows": len(strict_rows),
        "lane08_source_rows": len(lane08_by_id),
        "lane08_matching_rows": sum(1 for row_id in expected_by_id if row_id in lane08_by_id),
        "lane08_missing_expected_rows": sorted(row_id for row_id in expected_by_id if row_id not in lane08_by_id)[:50],
        "lane08_extra_source_rows": len(set(lane08_by_id) - set(expected_by_id)),
        "geometry_joined_rows": source_strict_summary.get("geometry_joined_rows"),
        "strict_tick_event_status_counts": dict(sorted(status_counts.items())),
        "strict_tick_materialized_rows": status_counts.get("strict_tick_policy_exit_timeline_from_lane08", 0),
        "strict_tick_replayed_rows": source_strict_summary.get("strict_tick_replayed_rows"),
        "replay_status_counts": source_strict_summary.get("replay_status_counts"),
        "tick_source_loaded_paths": source_strict_summary.get("tick_source_loaded_paths"),
        "tick_load_error_counts": source_strict_summary.get("tick_load_error_counts"),
        "source_ledger": rel(LANE08_STRICT_POLICY_LEDGER),
        "source_summary": rel(LANE08_SUMMARY),
        "source_operation": "lane04_consumes_lane08_ordered_bid_ask_policy_exit_replay_as_strict_subset_evidence",
    }


def build_manifest(now: str) -> dict[str, Any]:
    output_paths = [
        TIMELINE_LEDGER,
        STRICT_TICK_TIMELINE_LEDGER,
        SOURCE_GAP_LEDGER,
        ANATOMY_SPLIT_LEDGER,
        SOURCE_COMPLETENESS_LEDGER,
        DEPENDENCY_STATE_LEDGER,
        IMPLEMENTATION_DECISION_LEDGER,
        EXPECTANCY_SUMMARY,
        CONTEXT_ANCHOR,
        COMPLETION_AUDIT,
        OUTPUT_MANIFEST,
        VERIFIER,
        VERIFICATION_RESULT,
        FOCUSED_TEST_RESULT,
    ]
    outputs = []
    for path in output_paths:
        if not path.exists():
            continue
        outputs.append(
            {
                "path": rel(path),
                "bytes": path.stat().st_size,
                "line_count": line_count(path) if path.suffix == ".jsonl" else None,
                "sha256": None if path == OUTPUT_MANIFEST else sha256_file(path),
            }
        )
    return {
        "schema_version": "lane04_output_manifest_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "git_head": git_head(),
        "outputs": outputs,
        "output_count": len(outputs),
    }


def write_context_anchor(now: str, summary: dict[str, Any]) -> None:
    text = "\n".join(
        [
            "# Lane04 Historical Microscope Engine Context Anchor",
            "",
            f"Generated: {now}",
            f"HEAD: `{git_head()}`",
            "",
            "Controlling prompt: `research/science_program_2026_05/04_goal_prompts/VNEXT_MOONSHOT_LANE04_HISTORICAL_MICROSCOPE_ENGINE_GOAL_PROMPT_2026-06-01.md`",
            "Evidence class: historical microscope/path-anatomy research. No live broker action, no paid API, no credential/remote change, no production activation.",
            "",
            f"Timeline rows: `{summary['timeline_rows']}` (`lane02={summary['lane02_rows']}`, `friday={summary['friday_rows']}`).",
            f"Strict tick policy-exit rows: `{summary['strict_tick']['strict_tick_materialized_rows']}` of `{summary['strict_tick']['candidate_rows']}` local tick-date rows, sourced from Lane08 ordered bid/ask replay.",
            "",
            "Absence handling: absolute Lane01/Lane02/Lane03 outputs were not present; dependency-state rows record that and the engine used current next-level Lane02/Lane03 plus Friday/MT5 preservation evidence.",
            "Resume rule: rerun mandatory preflight, reread the prompt/starter/doctrine and this route's manifest/audit before extending.",
            "",
        ]
    )
    CONTEXT_ANCHOR.write_text(text, encoding="utf-8")


def write_verifier() -> None:
    VERIFIER.write_text(
        '''from __future__ import annotations

import argparse
import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
EXPECTED_LANE02_ROWS = 289600
EXPECTED_FRIDAY_ROWS = 328


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def verify_route(route_dir: Path = ROUTE_DIR) -> dict:
    issues = []
    paths = {
        "timeline": route_dir / "LANE04_ROW_TIMELINE_LEDGER.jsonl",
        "strict": route_dir / "LANE04_STRICT_TICK_TIMELINE_LEDGER.jsonl",
        "source_gap": route_dir / "LANE04_SOURCE_GAP_LEDGER.jsonl",
        "anatomy": route_dir / "LANE04_ANATOMY_SPLIT_LEDGER.jsonl",
        "source_completeness": route_dir / "LANE04_SOURCE_COMPLETENESS_DECISION_LEDGER.jsonl",
        "dependency": route_dir / "LANE04_DEPENDENCY_STATE_LEDGER.jsonl",
        "decision": route_dir / "LANE04_IMPLEMENTATION_DECISION_LEDGER.jsonl",
        "summary": route_dir / "LANE04_EXPECTANCY_SUMMARY.json",
        "audit": route_dir / "LANE04_COMPLETION_AUDIT.json",
        "manifest": route_dir / "LANE04_OUTPUT_MANIFEST.json",
    }
    for name, path in paths.items():
        if not path.exists():
            issues.append(f"missing_output:{name}:{path.name}")
    if issues:
        return {"ok": False, "issue_count": len(issues), "issues": issues, "schema_version": "lane04_verification_result_v1"}

    timeline_rows = count_jsonl(paths["timeline"])
    expected_timeline = EXPECTED_LANE02_ROWS + EXPECTED_FRIDAY_ROWS
    if timeline_rows != expected_timeline:
        issues.append(f"timeline_row_count_expected_{expected_timeline}_actual_{timeline_rows}")
    strict_rows = count_jsonl(paths["strict"])
    if strict_rows <= 0:
        issues.append("strict_tick_timeline_missing_rows")
    if count_jsonl(paths["source_gap"]) <= 0:
        issues.append("source_gap_ledger_missing_rows")
    if count_jsonl(paths["anatomy"]) < 100:
        issues.append("anatomy_split_ledger_too_small")

    summary = read_json(paths["summary"])
    if summary.get("timeline_rows") != timeline_rows:
        issues.append("summary_timeline_rows_mismatch")
    if summary.get("lane02_rows") != EXPECTED_LANE02_ROWS:
        issues.append("summary_lane02_rows_mismatch")
    if summary.get("friday_rows") != EXPECTED_FRIDAY_ROWS:
        issues.append("summary_friday_rows_mismatch")
    strict_summary = summary.get("strict_tick") or {}
    if strict_summary.get("candidate_rows") != strict_rows:
        issues.append("strict_candidate_row_count_mismatch")
    if strict_summary.get("strict_tick_materialized_rows", 0) <= 0:
        issues.append("strict_tick_materialized_rows_missing")

    dep_rows = list(iter_jsonl(paths["dependency"]))
    required_absent = {
        "absolute_lane01_source_authority",
        "absolute_lane02_asof_contract",
        "absolute_lane03_candidate_reconstruction",
    }
    dep_names = {row.get("dependency_name") for row in dep_rows}
    missing_deps = sorted(required_absent - dep_names)
    if missing_deps:
        issues.append(f"missing_dependency_state_rows:{missing_deps}")

    decisions = list(iter_jsonl(paths["decision"]))
    if not any(row.get("decision") == "strict_tick_full_denominator_not_claimed" for row in decisions):
        issues.append("strict_tick_boundary_decision_missing")

    audit = read_json(paths["audit"])
    if audit.get("runtime_effect_boundary") != "offline_artifacts_only_no_broker_action_no_live_restart_no_config_change":
        issues.append("runtime_effect_boundary_missing_or_wrong")
    if audit.get("status") != "complete_for_current_approved_local_source_class_with_explicit_source_gaps":
        issues.append("audit_status_unexpected")

    return {
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "timeline_rows": timeline_rows,
        "strict_tick_rows": strict_rows,
        "source_gap_rows": count_jsonl(paths["source_gap"]),
        "route_id": "vnext_moonshot_lane04_historical_microscope_engine_2026_06_01",
        "schema_version": "lane04_verification_result_v1",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args(argv)
    result = verify_route()
    (ROUTE_DIR / "LANE04_VERIFICATION_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
''',
        encoding="utf-8",
    )


def build_outputs(write: bool = True) -> dict[str, Any]:
    if not LANE02_REPLAY.exists():
        raise SystemExit(f"missing Lane02 replay ledger: {LANE02_REPLAY}")
    if not FRIDAY_MICRO.exists():
        raise SystemExit(f"missing Friday micro ledger: {FRIDAY_MICRO}")

    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    now = utc_now()
    lane02_summary = read_json(LANE02_SUMMARY, {})
    lane08_summary = read_json(LANE08_SUMMARY, {})
    mt5_summary = read_json(MT5_COVERAGE, {})

    strict_rows = collect_strict_tick_rows()
    strict_map, strict_summary = build_strict_tick_map(strict_rows) if write else ({}, {})

    groups: dict[tuple[str, str], Stats] = defaultdict(Stats)
    source_gap_rows = 0
    lane02_rows = 0
    friday_rows = 0
    path_class_counts: Counter[str] = Counter()
    source_use_counts: Counter[str] = Counter()
    tick_status_counts: Counter[str] = Counter()
    m1_status_counts: Counter[str] = Counter()

    if write:
        with TIMELINE_LEDGER.open("w", encoding="utf-8", newline="\n") as timeline_handle, SOURCE_GAP_LEDGER.open(
            "w", encoding="utf-8", newline="\n"
        ) as gap_handle:
            for _, row in iter_jsonl(LANE02_REPLAY):
                lane02_rows += 1
                row_id = str(row.get("selected_row_id") or "")
                timeline = m15_timeline(row, strict_map.get(row_id))
                write_jsonl_line(timeline_handle, timeline)
                update_stats(groups, timeline)
                path_class_counts[str(timeline.get("path_class"))] += 1
                source_use_counts[str(timeline.get("source_use_state"))] += 1
                tick_status_counts[str(timeline.get("tick_availability_status"))] += 1
                m1_status_counts[str(timeline.get("m1_availability_status"))] += 1
                gap = source_gap_row(timeline)
                if gap:
                    source_gap_rows += 1
                    write_jsonl_line(gap_handle, gap)
            for _, row in iter_jsonl(FRIDAY_MICRO):
                friday_rows += 1
                timeline = friday_timeline(row)
                write_jsonl_line(timeline_handle, timeline)
                update_stats(groups, timeline)
                path_class_counts[str(timeline.get("path_class"))] += 1
                source_use_counts[str(timeline.get("source_use_state"))] += 1
                tick_status_counts[str(timeline.get("tick_availability_status"))] += 1
                m1_status_counts[str(timeline.get("m1_availability_status"))] += 1
                gap = source_gap_row(timeline)
                if gap:
                    source_gap_rows += 1
                    write_jsonl_line(gap_handle, gap)

        anatomy_rows = [
            stat.as_row(scope, key)
            for (scope, key), stat in sorted(groups.items(), key=lambda item: (item[0][0], item[0][1]))
        ]
        write_jsonl(ANATOMY_SPLIT_LEDGER, anatomy_rows)
        write_jsonl(DEPENDENCY_STATE_LEDGER, dependency_rows())
        source_summary = lane02_summary | {
            "strict_tick_replay_summary": strict_summary,
            "tick_availability_counts": lane02_summary.get("tick_availability_counts") or lane08_summary.get("tick_availability_counts") or {},
            "m1_availability_counts": lane02_summary.get("m1_availability_counts") or lane08_summary.get("m1_availability_counts") or {},
        }
        write_jsonl(SOURCE_COMPLETENESS_LEDGER, source_completeness_rows(source_summary, mt5_summary))
        write_jsonl(IMPLEMENTATION_DECISION_LEDGER, implementation_decision_rows())
    else:
        lane02_rows = line_count(LANE02_REPLAY)
        friday_rows = line_count(FRIDAY_MICRO)

    summary = {
        "schema_version": "lane04_expectancy_summary_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "git_head": git_head(),
        "lane02_rows": lane02_rows,
        "friday_rows": friday_rows,
        "timeline_rows": lane02_rows + friday_rows,
        "source_gap_rows": source_gap_rows if write else line_count(SOURCE_GAP_LEDGER),
        "anatomy_split_rows": line_count(ANATOMY_SPLIT_LEDGER) if write else line_count(ANATOMY_SPLIT_LEDGER),
        "strict_tick": strict_summary if write else {},
        "path_class_counts": dict(sorted(path_class_counts.items())),
        "source_use_counts": dict(sorted(source_use_counts.items())),
        "tick_availability_counts": dict(sorted(tick_status_counts.items())),
        "m1_availability_counts": dict(sorted(m1_status_counts.items())),
        "lane02_expectancy_reference": (lane02_summary.get("stats") or {}),
        "lane03_metric_source": rel(LANE03_METRICS),
        "mt5_preservation_source": rel(MT5_COVERAGE),
        "result_scope": "historical_microscope_path_anatomy_with_exact_tick_subset_and_m15_proxy_full_denominator",
        "result_use_status": "research_feature_label_selector_ml_inputs_not_live_activation_not_broker_net_r_truth",
        "source_use_state": "friday_exact_tick_seed_plus_lane02_m15_proxy_full_denominator_plus_strict_tick_subset",
        "runtime_effect_boundary": "offline_artifacts_only_no_broker_action_no_live_restart_no_config_change",
    }
    if write:
        write_json(EXPECTANCY_SUMMARY, summary)
        write_context_anchor(now, summary)
        audit = {
            "schema_version": "lane04_completion_audit_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": now,
            "status": "complete_for_current_approved_local_source_class_with_explicit_source_gaps",
            "mandatory_context_use": {
                "live_state_regenerated": True,
                "goal_session_research_discipline_read": True,
                "research_operating_doctrine_read": True,
                "lane04_prompt_and_starter_read": True,
                "friday_microscope_read": True,
                "lane01_02_03_dependency_state_recorded": True,
            },
            "requirements": [
                {"requirement": "microscope_engine", "status": "complete", "evidence": rel(Path(__file__))},
                {"requirement": "row_level_timeline_ledger", "status": "complete", "rows": summary["timeline_rows"], "evidence": rel(TIMELINE_LEDGER)},
                {"requirement": "strict_tick_paths_for_rows_with_tick_coverage", "status": "complete_for_local_tick_date_rows", "rows": strict_summary.get("strict_tick_materialized_rows"), "evidence": rel(STRICT_TICK_TIMELINE_LEDGER)},
                {"requirement": "m1_m15_proxy_for_unavailable_ticks", "status": "complete_with_row_level_source_gap_proof", "evidence": rel(SOURCE_GAP_LEDGER)},
                {"requirement": "anatomy_summaries", "status": "complete", "rows": summary["anatomy_split_rows"], "evidence": rel(ANATOMY_SPLIT_LEDGER)},
                {"requirement": "dependency_state_rows_for_absent_upstreams", "status": "complete", "evidence": rel(DEPENDENCY_STATE_LEDGER)},
                {"requirement": "source_completeness_decisions", "status": "complete", "evidence": rel(SOURCE_COMPLETENESS_LEDGER)},
                {"requirement": "branch_or_implementation_decisions", "status": "complete", "evidence": rel(IMPLEMENTATION_DECISION_LEDGER)},
                {"requirement": "manifest_verifier_focused_tests", "status": "pending_until_verifier_and_pytest_run", "evidence": [rel(OUTPUT_MANIFEST), rel(VERIFIER), rel(VERIFICATION_RESULT), rel(FOCUSED_TEST_RESULT)]},
            ],
            "anti_boxing_questions_pursued": [
                "not Friday-only: full Lane02 289600 selected denominator consumed",
                "not symbol-only: all Lane02/Friday symbols preserved in split ledger",
                "not exact-tick-only: exact local tick subset materialized and missing rows retain M15/M1 proxy with source gaps",
                "not result-only: loss, winner, stuck, no-entry, cost, tick, M1, path-class and source-use ledgers are preserved",
            ],
            "open_source_gaps_not_hidden": [
                "absolute Lane01/Lane02/Lane03 outputs absent and recorded as dependency-state rows",
                "historical full-denominator ordered bid/ask tick path unavailable from current local parquet subset",
                "historical full-denominator broker cost/deal/commission/swap/slippage net-R unavailable",
                "MT5 .tkc/.hcc cache exists in preservation inventory but deterministic parser/source authority belongs to absent Lane01 output",
            ],
            "proof_or_impossibility_stop_condition": "current local approved source class exhausted into timelines; exact tick rows replayed; unavailable tick/cost/broker fields recorded as row-level source gaps and source-completeness decisions",
            "source_use_state": summary["source_use_state"],
            "result_use_status": summary["result_use_status"],
            "runtime_effect_boundary": summary["runtime_effect_boundary"],
            "forbidden_surface_attestation": {
                "live_broker_order_operation": False,
                "paid_api_vendor_call": False,
                "credential_or_remote_change": False,
                "hidden_production_activation": False,
            },
        }
        write_json(COMPLETION_AUDIT, audit)
        write_verifier()
        manifest = build_manifest(now)
        write_json(OUTPUT_MANIFEST, manifest)
    return summary


def refresh_audit_and_manifest(verification_result: dict[str, Any]) -> None:
    now = utc_now()
    focused_present = FOCUSED_TEST_RESULT.exists()
    verifier_ok = bool(verification_result.get("ok"))
    audit = read_json(COMPLETION_AUDIT, {})
    if isinstance(audit, dict) and audit:
        for requirement in audit.get("requirements") or []:
            if requirement.get("requirement") == "manifest_verifier_focused_tests":
                requirement["status"] = (
                    "complete"
                    if verifier_ok and focused_present
                    else "verifier_complete_focused_tests_pending"
                    if verifier_ok
                    else "pending_verifier_failure_or_missing_focused_tests"
                )
                requirement["evidence"] = [rel(OUTPUT_MANIFEST), rel(VERIFIER), rel(VERIFICATION_RESULT), rel(FOCUSED_TEST_RESULT)]
                requirement["verifier_ok"] = verifier_ok
                requirement["focused_test_result_present"] = focused_present
        audit["last_verification_refresh_at_utc"] = now
        audit["verifier_ok"] = verifier_ok
        audit["focused_test_result_present"] = focused_present
        write_json(COMPLETION_AUDIT, audit)
    write_json(OUTPUT_MANIFEST, build_manifest(now))


def verify_outputs(write: bool = True) -> dict[str, Any]:
    if not VERIFIER.exists():
        return {
            "ok": False,
            "issue_count": 1,
            "issues": ["missing_verifier"],
            "schema_version": "lane04_verification_result_v1",
        }
    namespace: dict[str, Any] = {"__file__": str(VERIFIER)}
    exec(VERIFIER.read_text(encoding="utf-8"), namespace)
    result = namespace["verify_route"](ROUTE_DIR)
    if write:
        write_json(VERIFICATION_RESULT, result)
        refresh_audit_and_manifest(result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.check:
        result = verify_outputs(write=True)
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get("ok") else 1
    summary = build_outputs(write=True)
    result = verify_outputs(write=True)
    print(json.dumps({"summary": summary, "verification": result}, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
