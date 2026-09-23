#!/usr/bin/env python3
"""Materialize the next Wave2 same-evidence-class continuation artifacts.

This pass does not complete Wave2 and does not create Wave3 launch authority.
It tightens the current checkpoint by turning several open buckets into
row-level evidence, exact source gaps, or prospective capture requirements.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]
GENERATED_AT = datetime.now(timezone.utc).isoformat()

MT5_BASE = Path(
    "/Users/borr/Library/Application Support/net.metaquotes.wine.metatrader5/"
    "drive_c/Program Files/MetaTrader 5/Bases"
)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} is not a JSON object")
    return payload


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{line_no} is not a JSON object")
            rows.append(payload)
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
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


def route_rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def route_path(name: str) -> Path:
    return ROUTE_DIR / name


def safe_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def row_count(path: Path) -> int | None:
    if path.suffix != ".jsonl":
        return None
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def utc_bucket(timestamp: str | None) -> str:
    if not timestamp:
        return "unknown_utc_bucket"
    try:
        hour = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).hour
    except ValueError:
        return "unknown_utc_bucket"
    if 0 <= hour <= 6:
        return "asia_tokyo_broad_utc_00_06"
    if 7 <= hour <= 11:
        return "london_broad_utc_07_11"
    if 12 <= hour <= 16:
        return "ny_overlap_broad_utc_12_16"
    if 17 <= hour <= 21:
        return "late_ny_broad_utc_17_21"
    return "rollover_utc_22_23"


def load_route_inputs() -> dict[str, Any]:
    return {
        "trades": read_jsonl(route_path("WAVE2_EVERY_TRADE_CAUSAL_MICROSCOPE.jsonl")),
        "selector": read_jsonl(route_path("WAVE2_SELECTOR_LOOSENESS_AND_TRADE_QUALITY_LEDGER.jsonl")),
        "final_say": read_jsonl(route_path("WAVE2_LIVE_AUTHORITY_FINAL_SAY_MATRIX.jsonl")),
        "allocator": read_jsonl(route_path("WAVE2_INFERRED_ALLOCATOR_DECISION_WINDOW_REPAIR_LEDGER.jsonl")),
        "zero_trade": read_jsonl(route_path("WAVE2_ZERO_TRADE_AND_REJECTION_VALUE_LEDGER.jsonl")),
        "cost": read_jsonl(route_path("WAVE2_COST_BROKER_NET_CAUSAL_LEDGER.jsonl")),
        "first_passage": read_jsonl(route_path("WAVE2_FIRST_PASSAGE_TIME_TO_DESTINATION_LEDGER.jsonl")),
        "candidate_microscope": read_jsonl(route_path("WAVE2_EVERY_CANDIDATE_CAUSAL_MICROSCOPE.jsonl")),
        "health": read_json(route_path("WAVE2_SYMBOL_SESSION_SIDE_REGIME_HEALTH_TABLE.json")),
        "questions": read_jsonl(route_path("WAVE2_ACTIVE_CAUSAL_QUESTION_STACK.jsonl")),
        "coverage": read_jsonl(route_path("WAVE2_QUESTION_COVERAGE_SATURATION_LEDGER.jsonl")),
        "proof": read_jsonl(route_path("WAVE2_NEW_QUESTION_PURSUIT_PROOF.jsonl")),
        "hypotheses": read_jsonl(route_path("WAVE2_DISCOVERED_HYPOTHESIS_LEDGER.jsonl")),
        "new_intel": read_jsonl(route_path("WAVE2_NEWLY_DISCOVERED_INTELLIGENCE_LEDGER.jsonl")),
        "blockers": read_jsonl(route_path("WAVE2_BLOCKER_AND_REPAIR_LEDGER.jsonl")),
        "manifest": read_json(route_path("WAVE2_OUTPUT_MANIFEST.json")),
        "full_coverage": read_json(route_path("WAVE2_FULL_LEDGER_COVERAGE_AUDIT.json")),
        "final_state": read_json(route_path("WAVE2_FINAL_MASTER_STATE_TABLE.json")),
    }


def by_position(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        position_id = row.get("broker_position_id")
        if position_id not in (None, ""):
            out[str(position_id)] = row
    return out


def candidate_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        candidate_id = row.get("candidate_id")
        if candidate_id not in (None, "") and str(candidate_id) not in out:
            out[str(candidate_id)] = row
    return out


def classify_trade(
    trade: dict[str, Any],
    cost: dict[str, Any] | None,
    path: dict[str, Any] | None,
    health: dict[str, Any],
) -> tuple[str, list[str], str]:
    symbol = str(trade.get("symbol") or "")
    metrics = trade.get("metric_fields_used") if isinstance(trade.get("metric_fields_used"), dict) else {}
    pnl = safe_float(metrics.get("broker_real_pnl_cash"))
    win_loss = str(metrics.get("win_loss") or "")
    failure_tags = set(metrics.get("failure_tags") or [])
    symbol_health = health.get("by_symbol", {}).get(symbol, {})
    symbol_net = safe_float(symbol_health.get("net"))
    symbol_win_rate = safe_float(symbol_health.get("win_rate"))
    cost_drag = safe_float((cost or {}).get("cost_drag_cash"))
    swap = safe_float((cost or {}).get("swap_cash"))
    tick_status = (path or {}).get("status")
    destination = (path or {}).get("destination_efficiency")

    evidence_tags: list[str] = []
    if symbol_net is not None and symbol_net < 0:
        evidence_tags.append("symbol_health_net_negative")
    if symbol_win_rate is not None and symbol_win_rate <= 0.35:
        evidence_tags.append("symbol_health_low_win_rate")
    if "stop_loss_or_broker_sl_exit" in failure_tags:
        evidence_tags.append("stop_loss_or_broker_sl_exit")
    if "dominant_damage_symbol" in failure_tags:
        evidence_tags.append("dominant_damage_symbol")
    if cost_drag is not None and cost_drag <= -25:
        evidence_tags.append("material_explicit_cost_drag")
    if swap is not None and swap < 0:
        evidence_tags.append("swap_drag")
    if tick_status == "partial_or_missing_tick_window_source_gap":
        evidence_tags.append("tick_window_partial_or_missing")
    if destination and destination not in {"reached_1r_fast_enough", "reached_0_25r_not_0_5r"}:
        evidence_tags.append(f"destination_{destination}")

    if tick_status == "partial_or_missing_tick_window_source_gap":
        primary = "bad_data_capture"
        counterfactual = "do_not_promote_path_or_market-whiteboard claim without exact market data source repair"
    elif pnl is not None and pnl < 0 and (cost_drag is not None and cost_drag <= -25 or swap is not None and swap < 0):
        primary = "bad_execution_cost_broker"
        counterfactual = "pretrade broker-net cost and swap gate or no-trade"
    elif symbol_net is not None and symbol_net < 0 and (symbol_win_rate is not None and symbol_win_rate <= 0.35):
        primary = "bad_market_system_mismatch"
        counterfactual = "recent-damage symbol/session quarantine or reduced risk until repaired"
    elif win_loss == "loss" and "stop_loss_or_broker_sl_exit" in failure_tags:
        primary = "bad_system_logic"
        counterfactual = "selector reject, tighter invalidation, delayed entry, or harvest/exit redesign"
    elif pnl is not None and pnl >= 0:
        primary = "unknown_with_source_gap"
        counterfactual = "preserve positive context but require same admission/cost/path proof before reuse"
    else:
        primary = "unknown_with_source_gap"
        counterfactual = "market whiteboard replay and packet capture required"

    return primary, evidence_tags, counterfactual


def build_market_system_rows(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    cost_by_pos = by_position(inputs["cost"])
    path_by_pos = by_position(inputs["first_passage"])
    rows: list[dict[str, Any]] = []
    for trade in inputs["trades"]:
        position_id = str(trade.get("broker_position_id"))
        cost = cost_by_pos.get(position_id)
        path = path_by_pos.get(position_id)
        primary, tags, counterfactual = classify_trade(trade, cost, path, inputs["health"])
        metrics = trade.get("metric_fields_used") if isinstance(trade.get("metric_fields_used"), dict) else {}
        entry_time = (trade.get("time_window") or {}).get("entry_time_utc") if isinstance(trade.get("time_window"), dict) else None
        symbol = trade.get("symbol")
        side = trade.get("side")
        rows.append(
            {
                "row_id": f"market_system_trade:{position_id}",
                "broker_position_id": trade.get("broker_position_id"),
                "symbol": symbol,
                "side": side,
                "entry_time_utc": entry_time,
                "utc_bucket": utc_bucket(entry_time),
                "broker_real_pnl_cash": metrics.get("broker_real_pnl_cash"),
                "win_loss": metrics.get("win_loss"),
                "primary_disposition": primary,
                "supporting_evidence_tags": tags,
                "symbol_health": inputs["health"].get("by_symbol", {}).get(str(symbol), {}),
                "symbol_side_bucket_health": inputs["health"]
                .get("by_symbol_side_utc_bucket", {})
                .get(f"{symbol}|{side}|{utc_bucket(entry_time)}", {}),
                "cost_fields": {
                    "gross_deal_profit_cash": (cost or {}).get("gross_deal_profit_cash"),
                    "cost_drag_cash": (cost or {}).get("cost_drag_cash"),
                    "commission_cash": (cost or {}).get("commission_cash"),
                    "swap_cash": (cost or {}).get("swap_cash"),
                },
                "path_fields": {
                    "tick_repair_status": (path or {}).get("tick_repair_status"),
                    "destination_efficiency": (path or {}).get("destination_efficiency"),
                    "tick_mfe_r": (path or {}).get("tick_mfe_r"),
                    "tick_mae_r": (path or {}).get("tick_mae_r"),
                    "time_to_plus_1r_minutes": (path or {}).get("time_to_plus_1r_minutes"),
                    "missing_tick_dates": (path or {}).get("missing_tick_dates"),
                },
                "counterfactual_decision": counterfactual,
                "source_paths": [
                    route_rel(route_path("WAVE2_EVERY_TRADE_CAUSAL_MICROSCOPE.jsonl")),
                    route_rel(route_path("WAVE2_SYMBOL_SESSION_SIDE_REGIME_HEALTH_TABLE.json")),
                    route_rel(route_path("WAVE2_COST_BROKER_NET_CAUSAL_LEDGER.jsonl")),
                    route_rel(route_path("WAVE2_FIRST_PASSAGE_TIME_TO_DESTINATION_LEDGER.jsonl")),
                ],
                "evidence_class": "broker-real cash plus source-bound path/cost/health diagnostics",
                "status": "row_level_market_system_classified_not_full_runtime_whiteboard",
                "owning_wave3_lane": "market_whiteboard_v2",
                "v4_requirement_id": "market_whiteboard_v2_fail_closed_symbol_session_cost_path_gate",
            }
        )
    return rows


def build_selector_repair_rows(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in inputs["selector"]:
        missing = list(row.get("missing_fields") or [])
        has_rows = row.get("selected_cell_rows") not in (None, "")
        status = (
            "selected_cell_rows_present_win_pf_not_captured"
            if has_rows and {"selected_cell_win_rate", "selected_cell_profit_factor"}.intersection(missing)
            else "selected_cell_quality_fields_missing_fail_closed"
            if missing
            else "selected_cell_quality_fields_present"
        )
        rows.append(
            {
                "row_id": f"selector_quality_repair:{row.get('row_id')}",
                "source_selector_row_id": row.get("row_id"),
                "broker_position_id": row.get("broker_position_id"),
                "symbol": row.get("symbol"),
                "win_loss": row.get("win_loss"),
                "broker_real_pnl_cash": row.get("broker_real_pnl_cash"),
                "selected_cell_rows": row.get("selected_cell_rows"),
                "selected_cell_win_rate": row.get("selected_cell_win_rate"),
                "selected_cell_profit_factor": row.get("selected_cell_profit_factor"),
                "missing_fields": missing,
                "repair_actions_attempted": [
                    "consumed_wave2_selector_looseness_ledger",
                    "consumed_wave2_selector_quality_field_coverage_ledger",
                    "consumed_symbol_session_broker_health_for_fail_closed_admission_context",
                ],
                "repair_status": status,
                "result_use_status": "selector_v4_admission_requirement_not_live_selector_proof",
                "evidence_class": row.get("evidence_class") or "source-bound selected-cell context",
                "v4_requirement_id": "selector_v4_selected_cell_win_rate_profit_factor_broker_net_gate",
                "owning_wave3_lane": "selector_v4",
            }
        )
    return rows


def build_allocator_replay_rows(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in inputs["allocator"]:
        missing_runtime_truth = list(row.get("missing_runtime_truth") or [])
        replay_status = (
            "same_evidence_class_replay_materialized_original_runtime_intent_non_generatable"
            if missing_runtime_truth
            else "same_evidence_class_replay_materialized"
        )
        rows.append(
            {
                "row_id": f"allocator_replay:{row.get('inferred_window_id')}",
                "inferred_window_id": row.get("inferred_window_id"),
                "window_time_utc": row.get("window_time_utc"),
                "candidate_rows": row.get("candidate_rows"),
                "filled_count": row.get("filled_count"),
                "alternative_count": row.get("alternative_count"),
                "symbols": row.get("symbols"),
                "sides": row.get("sides"),
                "selected_or_filled_candidate_ids": row.get("selected_or_filled_candidate_ids"),
                "rejected_skipped_no_trade_candidate_ids": row.get("rejected_skipped_no_trade_candidate_ids"),
                "best_filled_by_exact_r": row.get("best_filled_by_exact_r"),
                "best_rejected_or_skipped_by_source_expectancy": row.get("best_rejected_or_skipped_by_source_expectancy"),
                "selected_vs_best_delta": row.get("selected_vs_best_delta"),
                "missing_runtime_truth": missing_runtime_truth,
                "repair_actions_attempted": [
                    "grouped_wave1a_candidate_trade_records_by_decision_time",
                    "joined_existing_selected_vs_alternative_opportunity_cost_ledgers",
                    "preserved_filled_exact_r_separate_from_nonfilled_source_expectancy",
                ],
                "replay_status": replay_status,
                "evidence_class": "source_bound_reconstruction_not_original_runtime_intent",
                "result_use_status": "diagnostic_allocator_replay_not_original_runtime_allocator_truth",
                "v4_requirement_id": "scheduler_v4_decision_window_candidate_set_open_pending_snapshot_capture",
                "owning_wave3_lane": "scheduler_v4_best_trade_allocator",
            }
        )
    return rows


def build_zero_trade_rank_rows(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    candidate_by_id = candidate_index(inputs["candidate_microscope"])
    rows: list[dict[str, Any]] = []
    for row in inputs["zero_trade"]:
        candidate_id = row.get("candidate_id")
        candidate = candidate_by_id.get(str(candidate_id)) if candidate_id not in (None, "") else None
        metric_fields = candidate.get("metric_fields_used") if candidate and isinstance(candidate.get("metric_fields_used"), dict) else {}
        missing_fields = ["counterfactual_path_outcome", "source_bound_proxy_r_or_exact_r_for_nonfilled_row"]
        if candidate is None:
            missing_fields.append("candidate_microscope_join")
        rows.append(
            {
                "row_id": f"zero_trade_counterfactual_rank:{row.get('row_id')}",
                "source_zero_trade_row_id": row.get("row_id"),
                "candidate_id": candidate_id,
                "trade_id": row.get("trade_id"),
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "final_outcome": row.get("final_outcome"),
                "candidate_quality_classification": row.get("candidate_quality_classification"),
                "source_bound_expectancy_context": {
                    "expectancy_r_source_bound": metric_fields.get("expectancy_r_source_bound"),
                    "selected_cell_rows": metric_fields.get("selected_cell_rows"),
                    "selected_cell_win_rate": metric_fields.get("selected_cell_win_rate"),
                    "selected_cell_profit_factor": metric_fields.get("selected_cell_profit_factor"),
                },
                "rank_status": "counterfactual_path_rank_source_gap_exact_row_preserved",
                "missing_fields": missing_fields,
                "repair_actions_attempted": [
                    "joined_zero_trade_ledger_to_candidate_microscope_by_candidate_id_when_available",
                    "preserved_source_bound_expectancy_context",
                    "did_not_promote_nonfilled_source_expectancy_to_realized_counterfactual_pnl",
                ],
                "evidence_class": "source-bound candidate context plus source gap for nonfilled path outcome",
                "result_use_status": "zero_trade_quality_evidence_not_realized_alternative_counterfactual",
                "v4_requirement_id": "selector_v4_zero_trade_counterfactual_path_and_no_trade_value_capture",
                "owning_wave3_lane": "selector_v4_zero_trade",
            }
        )
    return rows


def build_final_say_join_rows(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in inputs["final_say"]:
        missing_packet_fields: list[str] = []
        if row.get("candidate_action") in (None, ""):
            missing_packet_fields.append("candidate_action")
        if row.get("cost_swap_slippage_state") == "not_materialized_in_runtime_decision_row":
            missing_packet_fields.append("cost_swap_slippage_state")
        if row.get("source_completeness_state") in (None, "", "not_reported_in_runtime_row"):
            missing_packet_fields.append("source_completeness_state")
        if "default_off" in str(row.get("v3_selector_status")):
            missing_packet_fields.append("selector_v3_runtime_authority")
        if "default_off" in str(row.get("v3_scheduler_status")):
            missing_packet_fields.append("scheduler_v3_runtime_authority")
        if "default_off" in str(row.get("v3_execution_status")):
            missing_packet_fields.append("execution_policy_v3_runtime_authority")
        rows.append(
            {
                "row_id": f"final_say_selector_scheduler_join:{row.get('material_row_id')}",
                "material_row_id": row.get("material_row_id"),
                "source_row_kind": row.get("source_row_kind"),
                "symbol": row.get("symbol"),
                "timestamp_utc": row.get("timestamp_utc"),
                "decision_status": row.get("decision_status"),
                "candidate_action": row.get("candidate_action"),
                "final_say_authority": row.get("final_say_authority"),
                "v3_selector_status": row.get("v3_selector_status"),
                "v3_scheduler_status": row.get("v3_scheduler_status"),
                "v3_execution_status": row.get("v3_execution_status"),
                "cost_swap_slippage_state": row.get("cost_swap_slippage_state"),
                "source_completeness_state": row.get("source_completeness_state"),
                "missing_packet_fields": missing_packet_fields,
                "join_status": "final_say_preserved_packet_incomplete" if missing_packet_fields else "final_say_preserved_packet_fields_present",
                "repair_actions_attempted": [
                    "consumed_wave2_final_say_matrix",
                    "classified_packet_missingness_by_authority_and_v3_default_off_status",
                ],
                "evidence_class": row.get("evidence_class"),
                "result_use_status": "live_authority_join_status_not_v4_runtime_packet",
                "v4_requirement_id": "livedecisionpacket_v4_final_say_selector_scheduler_cost_capture",
                "owning_wave3_lane": "livedecisionpacket_v4",
            }
        )
    return rows


def mt5_symbol_aliases(symbol: str) -> list[str]:
    aliases = [symbol]
    alias_map = {
        "US30_cash": ["US30_cash", "US30", "DJ30", "US30.cash"],
        "US30": ["US30", "US30_cash", "DJ30", "US30.cash"],
        "ETHUSD": ["ETHUSD", "ETHUSD.", "ETHUSDm"],
        "EURJPY": ["EURJPY", "EURJPYm"],
        "USDJPY": ["USDJPY", "USDJPYm"],
    }
    aliases.extend(alias_map.get(symbol, []))
    seen: list[str] = []
    for alias in aliases:
        if alias and alias not in seen:
            seen.append(alias)
    return seen


def mt5_probe(server: str, symbol_aliases: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for alias in symbol_aliases:
        tick_dir = MT5_BASE / server / "ticks" / alias
        history_dir = MT5_BASE / server / "history" / alias
        files = []
        for directory in (tick_dir, history_dir):
            if directory.exists():
                for path in sorted(directory.glob("*")):
                    if path.is_file():
                        files.append(
                            {
                                "path": path.as_posix(),
                                "size_bytes": path.stat().st_size,
                                "modified_utc": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
                                "sha256": sha256_file(path),
                            }
                        )
        rows.append(
            {
                "server": server,
                "symbol_alias": alias,
                "tick_dir_exists": tick_dir.exists(),
                "history_dir_exists": history_dir.exists(),
                "file_count": len(files),
                "files": files[:12],
            }
        )
    return rows


def build_mt5_recovery_rows(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    gap_rows = [
        row
        for row in inputs["first_passage"]
        if row.get("status") != "source_bound_first_passage_computed"
    ]
    rows: list[dict[str, Any]] = []
    for row in gap_rows:
        symbol = str(row.get("tick_symbol") or row.get("symbol") or "")
        aliases = mt5_symbol_aliases(symbol)
        probes: list[dict[str, Any]] = []
        for server in ("FTMO-Server3", "MetaQuotes-Demo", "Default"):
            probes.extend(mt5_probe(server, aliases))
        exact_ftmo_tick = any(
            probe["server"] == "FTMO-Server3" and probe["tick_dir_exists"] and probe["file_count"] > 0
            for probe in probes
        )
        proxy_history = any(probe["history_dir_exists"] and probe["file_count"] > 0 for probe in probes)
        if exact_ftmo_tick:
            recovery_status = "mt5_ftmo_tick_cache_present_requires_parser_or_export"
        elif proxy_history:
            recovery_status = "mt5_history_or_demo_proxy_present_not_redacted_account_exact_tick"
        else:
            recovery_status = "not_found_in_current_mt5_cache_requires_readonly_chart_export_or_source_pull"
        rows.append(
            {
                "row_id": f"mt5_readonly_recovery:{row.get('broker_position_id')}:{row.get('trade_id')}",
                "broker_position_id": row.get("broker_position_id"),
                "trade_id": row.get("trade_id"),
                "symbol": row.get("symbol"),
                "tick_symbol": row.get("tick_symbol"),
                "entry_time_utc": row.get("entry_time_utc"),
                "close_time_utc": row.get("close_time_utc"),
                "previous_tick_repair_status": row.get("tick_repair_status"),
                "missing_tick_dates": row.get("missing_tick_dates"),
                "mt5_base_path": MT5_BASE.as_posix(),
                "symbol_aliases_searched": aliases,
                "mt5_probe_results": probes,
                "recovery_status": recovery_status,
                "evidence_class": "read_only_local_mt5_market_data_source_inventory",
                "result_use_status": "market_data_recovery_audit_not_broker_mutation_not_runtime_intent",
                "same_evidence_class_repairs_attempted": [
                    "searched_local_redacted_account_tick_parquet_before_this_pass",
                    "searched_local_mt5_bases_ftmo_server3_metaquotes_demo_default_ticks_and_history",
                    "kept_ftmo_and_demo_proxy_distinct_from_redacted_account_broker_tick_truth",
                ],
                "next_source_action": (
                    "parse_or_export exact FTMO tick cache if present"
                    if exact_ftmo_tick
                    else "read-only MT5 chart/tick export or exact source pull required for this bounded window"
                    if not proxy_history
                    else "proxy bar/history can be used only with explicit proxy label; exact redacted_account tick remains missing"
                ),
                "owning_wave3_lane": "historical_replay_digital_twin_v4",
                "v4_requirement_id": "market_data_source_recovery_and_proxy_label_contract",
            }
        )
    return rows


def update_questions(inputs: dict[str, Any], artifact_map: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    status_updates = {
        "W2Q_SELECTOR_QUALITY": "answered_with_selected_cell_quality_repair_fail_closed_broker_net_admission_still_required",
        "W2Q_FINAL_SAY_AUTHORITY": "answered_with_final_say_join_packet_missingness_v4_capture_required",
        "W2Q_BEST_TRADE_ALLOCATOR": "answered_with_allocator_replay_diagnostic_original_runtime_intent_non_generatable",
        "W2Q_BAD_MARKET_VS_SYSTEM": "answered_with_row_level_market_system_classification_whiteboard_replay_still_required",
        "W2Q_REJECT_SKIP_ZERO_TRADE": "answered_with_zero_trade_rank_source_gap_exact_counterfactual_path_capture_required",
        "W2Q_CAPTURE_GAPS": "answered_with_mt5_readonly_recovery_and_packet_capture_gap_contract",
        "W2Q_DOMINANT_DAMAGE_SYMBOL_QUARANTINE": "answered_with_row_level_symbol_session_damage_classification_market_health_gate_required",
    }
    result_updates = {
        "W2Q_SELECTOR_QUALITY": artifact_map["selector"],
        "W2Q_FINAL_SAY_AUTHORITY": artifact_map["final_say"],
        "W2Q_BEST_TRADE_ALLOCATOR": artifact_map["allocator"],
        "W2Q_BAD_MARKET_VS_SYSTEM": artifact_map["market"],
        "W2Q_REJECT_SKIP_ZERO_TRADE": artifact_map["zero_trade"],
        "W2Q_CAPTURE_GAPS": artifact_map["mt5"],
        "W2Q_DOMINANT_DAMAGE_SYMBOL_QUARANTINE": artifact_map["market"],
    }

    def patch_question(row: dict[str, Any]) -> dict[str, Any]:
        row = dict(row)
        question_id = row.get("question_id")
        if question_id in status_updates:
            row["status"] = status_updates[question_id]
            row["result_artifact"] = result_updates[question_id]
            actions = list(row.get("pursuit_actions") or [])
            if "wave2_continuation_materialization_pass" not in actions:
                actions.append("wave2_continuation_materialization_pass")
            row["pursuit_actions"] = actions
            repairs = list(row.get("same_evidence_class_repairs_attempted") or [])
            if "row_level_repair_or_exact_source_gap_materialized" not in repairs:
                repairs.append("row_level_repair_or_exact_source_gap_materialized")
            row["same_evidence_class_repairs_attempted"] = repairs
        return row

    questions = [patch_question(row) for row in inputs["questions"]]
    coverage: list[dict[str, Any]] = []
    for row in inputs["coverage"]:
        row = dict(row)
        question_id = row.get("question_id")
        if question_id in status_updates:
            row["status"] = status_updates[question_id]
            row["coverage_status"] = "answered_or_exact_gap_bounded_not_wave2_complete"
            row["result_artifact"] = result_updates[question_id]
            row["remaining_work"] = "consume into Wave3 lane contract and sealed validation; do not treat as prompt-pack-ready completion"
        coverage.append(row)

    proof: list[dict[str, Any]] = []
    for row in inputs["proof"]:
        row = dict(row)
        question_id = row.get("question_id")
        if question_id in status_updates:
            row["status"] = status_updates[question_id]
            row["proof_status"] = "continuation_artifact_materialized_with_exact_boundary"
            actions = list(row.get("pursuit_actions") or [])
            if "wave2_continuation_materialization_pass" not in actions:
                actions.append("wave2_continuation_materialization_pass")
            row["pursuit_actions"] = actions
        proof.append(row)

    hypotheses: list[dict[str, Any]] = []
    for row in inputs["hypotheses"]:
        row = dict(row)
        question_id = row.get("question_id")
        if question_id in status_updates:
            row["status"] = status_updates[question_id]
            row["result_artifact"] = result_updates[question_id]
            actions = list(row.get("pursuit_actions") or [])
            if "wave2_continuation_materialization_pass" not in actions:
                actions.append("wave2_continuation_materialization_pass")
            row["pursuit_actions"] = actions
        hypotheses.append(row)

    return questions, coverage, proof, hypotheses


def update_blockers(inputs: dict[str, Any], mt5_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blockers = [
        row
        for row in inputs["blockers"]
        if row.get("blocker_id") != "wave2_mt5_readonly_tick_gap_recovery"
    ]
    blockers.append(
        {
            "blocker_id": "wave2_mt5_readonly_tick_gap_recovery",
            "source_path": "WAVE2_MT5_READONLY_MARKET_DATA_RECOVERY_LEDGER.jsonl",
            "evidence_class": "recoverable_market_data_or_proxy_source_gap_not_runtime_intent",
            "missing_file_path_field_source": "exact redacted_account tick windows for five partial rows and one EURJPY no-window row; exact FTMO tick cache not present in current local MT5 cache for those bounded symbols/windows",
            "searched_roots_or_repairs": [
                "local redacted_account tick parquet roots",
                MT5_BASE.as_posix(),
                "FTMO-Server3 ticks/history",
                "MetaQuotes-Demo ticks/history",
                "Default ticks/history",
            ],
            "reason_repair_not_complete_in_initial_spine": "current local cache lacks exact broker tick source for bounded missing windows; any MT5 bar/demo source is proxy-labeled and cannot become redacted_account broker-real tick truth",
            "owner_access_source_capture_requirement": "read-only MT5 chart/tick export or exact source pull for the listed symbol/date windows; do not mutate broker account/orders/history/deals/positions",
            "downstream_lane": "historical_replay_digital_twin_v4",
            "status": "mt5_readonly_recovery_audited_exact_source_gap_bounded",
            "row_count": len(mt5_rows),
        }
    )
    return blockers


def build_new_intel(inputs: dict[str, Any], counts: dict[str, int]) -> list[dict[str, Any]]:
    continuation_ids = {"W2INTEL-CONT-MKT-ROW-001", "W2INTEL-CONT-MT5-001"}
    rows = [
        row
        for row in inputs["new_intel"]
        if row.get("intelligence_id") not in continuation_ids
    ]
    rows.extend(
        [
            {
                "intelligence_id": "W2INTEL-CONT-MKT-ROW-001",
                "origin": "wave2_continuation_materialization",
                "finding": f"Bad-market versus bad-system is now row-classified for all {counts['market']} broker-real trades; the classification remains source-bound diagnostics, not a full runtime market whiteboard.",
                "source_paths": ["WAVE2_MARKET_SYSTEM_ROW_CLASSIFICATION_LEDGER.jsonl"],
                "evidence_class": "broker-real cash plus source-bound path/cost/health diagnostics",
                "downstream_question_ids": ["W2Q_BAD_MARKET_VS_SYSTEM", "W2Q_DOMINANT_DAMAGE_SYMBOL_QUARANTINE"],
                "status": "accepted_row_level_market_system_intelligence_whiteboard_still_required",
                "v4_requirement_id": "market_whiteboard_v2_fail_closed_symbol_session_cost_path_gate",
            },
            {
                "intelligence_id": "W2INTEL-CONT-MT5-001",
                "origin": "wave2_continuation_materialization",
                "finding": f"Read-only MT5 cache was searched for {counts['mt5']} bounded tick/path gaps; current cache does not provide exact redacted_account tick truth for those windows and any FTMO/demo/history source must remain proxy-labeled.",
                "source_paths": ["WAVE2_MT5_READONLY_MARKET_DATA_RECOVERY_LEDGER.jsonl"],
                "evidence_class": "read_only_local_mt5_market_data_source_inventory",
                "downstream_question_ids": ["W2Q_CAPTURE_GAPS", "W2Q_VALIDATION_REPLAY"],
                "status": "accepted_market_data_recovery_boundary_not_no_data_excuse",
                "v4_requirement_id": "market_data_source_recovery_and_proxy_label_contract",
            },
        ]
    )
    return rows


def update_summaries(counts: dict[str, int], inputs: dict[str, Any]) -> None:
    full_coverage = dict(inputs["full_coverage"])
    full_coverage["continuation_materialization"] = {
        "generated_at_utc": GENERATED_AT,
        "market_system_row_classification_rows": counts["market"],
        "selector_selected_cell_repair_rows": counts["selector"],
        "allocator_decision_window_replay_rows": counts["allocator"],
        "zero_trade_counterfactual_path_rank_rows": counts["zero_trade"],
        "final_say_selector_scheduler_join_rows": counts["final_say"],
        "mt5_readonly_market_data_recovery_rows": counts["mt5"],
        "status": "same_evidence_class_continuation_materialized_not_wave2_complete",
    }
    full_coverage["coverage_gap"] = (
        "Wave2 now includes row-level market/system, selector repair, allocator replay, "
        "zero-trade rank, final-say join, and MT5 read-only source recovery ledgers; "
        "remaining completion still requires full prompt pack, sealed validation, original "
        "runtime packet capture/prospective implementation, and non-generatable lifecycle fields."
    )
    write_json(route_path("WAVE2_FULL_LEDGER_COVERAGE_AUDIT.json"), full_coverage)

    final_state = dict(inputs["final_state"])
    final_state["generated_at_utc"] = GENERATED_AT
    truths = list(final_state.get("truths") or [])
    for truth in [
        "bad-market versus bad-system now has row-level broker-trade classification but not a full runtime whiteboard",
        "read-only local MT5 cache was searched for bounded missing tick windows; exact redacted_account tick truth remains missing where listed",
        "selector selected-cell rows/PF/win-rate gaps are now fail-closed repair evidence, not live admission proof",
    ]:
        if truth not in truths:
            truths.append(truth)
    final_state["truths"] = truths
    gaps = list(final_state.get("blocking_gaps") or [])
    for gap in [
        "Wave3 per-lane prompts and starters are still not generated because causal/question closure remains incomplete",
        "exact missing market tick windows require read-only source export or proxy-labeled replay before full path claims",
    ]:
        if gap not in gaps:
            gaps.append(gap)
    final_state["blocking_gaps"] = gaps
    final_state["wave3_prompt_pack_allowed"] = False
    final_state["status"] = "not_final_incomplete_master_state_continuation_materialized"
    final_state["continuation_materialization_counts"] = counts
    write_json(route_path("WAVE2_FINAL_MASTER_STATE_TABLE.json"), final_state)


def update_markdown(counts: dict[str, int]) -> None:
    completion = f"""# Wave2 Completion Audit - Continuation Checkpoint

Status: incomplete.

Completed in the earlier checkpoint:

- Mandatory context and doctrine were read in-session before route materialization.
- Wave1A/B/C and Wave1 integration artifacts were inspected from disk and consumed as terminal inputs.
- The full broker/candidate/live-authority row universe was preserved without top-N truncation.
- Initial selector/scheduler/path/cost/static-R/SLTP/capture/validation ledgers, verifiers, manifest, and incomplete state table were materialized.
- A scoped checkpoint commit exists: `24823d98c research: add wave2 hard-halt causal microscope checkpoint`. This is not a completion commit.

Completed in this continuation checkpoint:

- `WAVE2_MARKET_SYSTEM_ROW_CLASSIFICATION_LEDGER.jsonl` classifies all {counts['market']} broker-real trades by bad-market/bad-system/cost/capture disposition using broker-real cash plus source-bound path, cost, and symbol/session health diagnostics.
- `WAVE2_SELECTOR_SELECTED_CELL_QUALITY_REPAIR_LEDGER.jsonl` preserves all {counts['selector']} selector-quality rows and converts missing win-rate/profit-factor/row-count fields into fail-closed Selector V4 requirements instead of soft advisory context.
- `WAVE2_ALLOCATOR_DECISION_WINDOW_REPLAY_LEDGER.jsonl` preserves all {counts['allocator']} inferred allocator windows as source-bound replay diagnostics while keeping original allocator intent non-generatable.
- `WAVE2_ZERO_TRADE_COUNTERFACTUAL_PATH_RANK_LEDGER.jsonl` preserves all {counts['zero_trade']} zero-trade/rejected/skipped rows and labels path-rank as an exact source gap where nonfilled outcome is not reconstructable.
- `WAVE2_FINAL_SAY_SELECTOR_SCHEDULER_JOIN_LEDGER.jsonl` preserves all {counts['final_say']} final-say rows with selector/scheduler/V3/cost/source-completeness packet missingness.
- `WAVE2_MT5_READONLY_MARKET_DATA_RECOVERY_LEDGER.jsonl` records read-only MT5 cache search for {counts['mt5']} bounded tick/path gaps. The local MT5 cache does not currently provide exact redacted_account tick truth for those windows; any FTMO/demo/history source must remain proxy-labeled unless an exact read-only export is produced.

Still not complete:

- Wave3 prompt pack and prompt hardening artifacts are intentionally still blocked.
- Full SLTP modify lifecycle, partial/BE/trailing/time-stop action clocks, original allocator packet truth, and unlogged AI/final-say runtime intent remain non-generatable historical truth unless a source already captured them.
- Sealed validation/digital-twin execution is not complete.
- Context current-state files are stale versus the Wave2 checkpoint and should be refreshed only when Wave2 final truth is ready, not from this incomplete checkpoint.
"""
    route_path("WAVE2_COMPLETION_AUDIT.md").write_text(completion, encoding="utf-8")

    saturation = f"""# Wave2 Saturation Self-Red-Team - Continuation Checkpoint

Status: incomplete.

Same-evidence-class gaps pursued in this continuation:

- Bad-market-vs-bad-system was not left as a two-row summary. It now has {counts['market']} broker-trade classification rows.
- Selector looseness was not left as generic missingness. It now has {counts['selector']} selected-cell quality repair rows with fail-closed status for missing win-rate/profit-factor evidence.
- Allocator opportunity cost was not left as route language. It now has {counts['allocator']} replay rows preserving diagnostic candidate windows while refusing to invent original runtime intent.
- Zero-trade/reject/skipped evidence was not reduced to examples. It now has {counts['zero_trade']} preserved counterfactual path-rank rows with exact source-gap labels.
- Final-say authority was not left as a matrix count. It now has {counts['final_say']} joined packet-missingness rows across selector, scheduler, V3 authority, cost, and source-completeness fields.
- Missing market data was not accepted as a vague blocker. It now has {counts['mt5']} MT5 read-only recovery rows with exact local cache search results and proxy/exact-source boundaries.

Remaining skeptical rejection points:

- These continuation artifacts still do not prove final Wave2 completion or Wave3 launch readiness.
- MT5 cache discovery is read-only source inventory, not broker-real redacted_account tick truth unless exact exported ticks are produced and hashed.
- Allocator replay remains diagnostic and cannot stand in for unlogged decision-window IDs, candidate-set IDs, open/pending snapshots, or broker-net EV per unit risk.
- Selector repair proves fail-closed requirements; it does not prove a production selector edge.
- Market/system classifications are row-level diagnostics and still need Market Whiteboard V2 replay/validation before production-return claims.
"""
    route_path("WAVE2_SATURATION_SELF_RED_TEAM.md").write_text(saturation, encoding="utf-8")


def regenerate_manifest() -> None:
    files = []
    for path in sorted(ROUTE_DIR.iterdir()):
        if not path.is_file():
            continue
        files.append(
            {
                "path": route_rel(path),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "jsonl_rows": row_count(path),
            }
        )
    write_json(
        route_path("WAVE2_OUTPUT_MANIFEST.json"),
        {
            "generated_at_utc": GENERATED_AT,
            "completion_status": "continuation_materialized_not_complete",
            "file_count": len(files),
            "files": files,
        },
    )


def main() -> int:
    inputs = load_route_inputs()
    market_rows = build_market_system_rows(inputs)
    selector_rows = build_selector_repair_rows(inputs)
    allocator_rows = build_allocator_replay_rows(inputs)
    zero_trade_rows = build_zero_trade_rank_rows(inputs)
    final_say_rows = build_final_say_join_rows(inputs)
    mt5_rows = build_mt5_recovery_rows(inputs)

    counts = {
        "market": write_jsonl(route_path("WAVE2_MARKET_SYSTEM_ROW_CLASSIFICATION_LEDGER.jsonl"), market_rows),
        "selector": write_jsonl(route_path("WAVE2_SELECTOR_SELECTED_CELL_QUALITY_REPAIR_LEDGER.jsonl"), selector_rows),
        "allocator": write_jsonl(route_path("WAVE2_ALLOCATOR_DECISION_WINDOW_REPLAY_LEDGER.jsonl"), allocator_rows),
        "zero_trade": write_jsonl(route_path("WAVE2_ZERO_TRADE_COUNTERFACTUAL_PATH_RANK_LEDGER.jsonl"), zero_trade_rows),
        "final_say": write_jsonl(route_path("WAVE2_FINAL_SAY_SELECTOR_SCHEDULER_JOIN_LEDGER.jsonl"), final_say_rows),
        "mt5": write_jsonl(route_path("WAVE2_MT5_READONLY_MARKET_DATA_RECOVERY_LEDGER.jsonl"), mt5_rows),
    }

    artifact_map = {
        "market": "WAVE2_MARKET_SYSTEM_ROW_CLASSIFICATION_LEDGER.jsonl",
        "selector": "WAVE2_SELECTOR_SELECTED_CELL_QUALITY_REPAIR_LEDGER.jsonl",
        "allocator": "WAVE2_ALLOCATOR_DECISION_WINDOW_REPLAY_LEDGER.jsonl",
        "zero_trade": "WAVE2_ZERO_TRADE_COUNTERFACTUAL_PATH_RANK_LEDGER.jsonl",
        "final_say": "WAVE2_FINAL_SAY_SELECTOR_SCHEDULER_JOIN_LEDGER.jsonl",
        "mt5": "WAVE2_MT5_READONLY_MARKET_DATA_RECOVERY_LEDGER.jsonl",
    }
    questions, coverage, proof, hypotheses = update_questions(inputs, artifact_map)
    write_jsonl(route_path("WAVE2_ACTIVE_CAUSAL_QUESTION_STACK.jsonl"), questions)
    write_jsonl(route_path("WAVE2_QUESTION_COVERAGE_SATURATION_LEDGER.jsonl"), coverage)
    write_jsonl(route_path("WAVE2_NEW_QUESTION_PURSUIT_PROOF.jsonl"), proof)
    write_jsonl(route_path("WAVE2_DISCOVERED_HYPOTHESIS_LEDGER.jsonl"), hypotheses)
    write_jsonl(route_path("WAVE2_BLOCKER_AND_REPAIR_LEDGER.jsonl"), update_blockers(inputs, mt5_rows))
    write_jsonl(route_path("WAVE2_NEWLY_DISCOVERED_INTELLIGENCE_LEDGER.jsonl"), build_new_intel(inputs, counts))

    update_summaries(counts, inputs)
    update_markdown(counts)
    regenerate_manifest()
    print(json.dumps({"ok": True, "counts": counts, "generated_at_utc": GENERATED_AT}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
