from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import gzip
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage04_mixed_resolution_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage04", MODULE_PATH)
stage04 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage04)

stage02 = stage04.stage02
REPO_ROOT = stage04.REPO_ROOT
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.gtos_vnext_runtime import (  # noqa: E402
    GTOSVNextRuntimeDecision,
    evaluate_vnext_prop_safe_selector,
)


ROUTE_ID = stage04.ROUTE_ID
ROUTE_DIR = stage04.ROUTE_DIR
STATE_PATH = stage04.STATE_PATH
FULL_REPLAY_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "vnext_full_historical_candidate_generation_replay_2026_05_24"
)
PROP_METRICS_PATH = FULL_REPLAY_DIR / "VNEXT_FULL_REPLAY_PROP_FIRM_METRICS_2026-05-24.jsonl"
ROBUSTNESS_PROP_INDEX_PATH = (
    FULL_REPLAY_DIR / "VNEXT_FULL_REPLAY_ROBUSTNESS_PROP_METRICS_LEDGER_2026-05-24.jsonl"
)
MISSED_WINNER_INDEX_PATH = (
    FULL_REPLAY_DIR / "VNEXT_FULL_REPLAY_MISSED_WINNER_AVOIDED_LOSER_LEDGER_2026-05-24.jsonl"
)
PROP_SELECTOR_LEDGER_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_PROP_SAFE_SELECTOR_LEDGER_2026-05-25.jsonl"
)
STAGE05_SUMMARY_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_STAGE05_PROP_SAFE_SELECTOR_SUMMARY_2026-05-25.json"
)
STAGE05_DOSSIER_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_PROP_SAFE_SELECTOR_DOSSIER_2026-05-25.md"
)
STAGE05_VERIFICATION_RESULT_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_STAGE05_VERIFICATION_RESULT_2026-05-25.json"
)

REQUIRED_SCENARIOS = {
    "reset_before_0000_gmt3",
    "reset_after_0000_gmt3",
    "malaysia_0500_reset_conversion",
    "intraday_profit_plus_2pct_daily_cushion_7000",
    "losing_day_reduces_cushion",
    "overall_static_initial_balance_floor",
    "open_floating_loss_current_equity_included",
    "pending_order_risk_included",
    "multiple_simultaneous_candidates_reserved",
    "correlated_exposure_buffer_included",
    "reduced_risk_instead_of_block",
    "defer_until_reset",
    "hard_block_only_when_projected_breach_exists",
    "internal_4pct_overlay_reported_separately",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return stage02.rel(path)


def atomic_json_write(path: Path, payload: Any) -> None:
    stage02.atomic_json_write(path, payload)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    stage02.write_jsonl(path, rows)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def iter_gzip_index(index_path: Path) -> Iterable[dict[str, Any]]:
    for index_row in read_jsonl(index_path):
        chunk_path = REPO_ROOT / str(index_row["chunk_path"])
        with gzip.open(chunk_path, "rt", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def base_config(**overrides: Any) -> dict[str, Any]:
    runtime = {
        "prop_safe_selector_enabled": True,
        "prop_safe_selector_apply_to_execution": True,
        "prop_safe_selector_initial_balance": 100000.0,
        "prop_safe_selector_external_daily_loss_limit_pct": 5.0,
        "prop_safe_selector_external_overall_max_loss_pct": 10.0,
        "prop_safe_selector_phase1_target_pct": 8.0,
        "prop_safe_selector_phase2_target_pct": 5.0,
        "prop_safe_selector_daily_reset_timezone_offset_hours": 3.0,
        "prop_safe_selector_malaysia_timezone_offset_hours": 8.0,
        "prop_safe_selector_spread_slippage_commission_buffer_pct": 0.0,
        "prop_safe_selector_min_reduced_risk_pct": 0.25,
        "prop_safe_selector_reserve_simultaneous_candidates": True,
        "prop_safe_selector_internal_daily_overlay_enabled": False,
        "prop_safe_selector_internal_overlay_applies_to_budget": True,
    }
    runtime.update(overrides)
    return {"risk": {"max_daily_loss_pct": 4.0}, "gtos_vnext_runtime": runtime}


def base_account(
    *,
    current_equity: float = 100000.0,
    day_start: float = 100000.0,
    **overrides: Any,
) -> dict[str, Any]:
    state: dict[str, Any] = {
        "initial_balance": 100000.0,
        "current_balance": current_equity,
        "current_equity": current_equity,
        "risk_base_amount": 100000.0,
        "day_start_equity_or_balance_baseline": day_start,
        "open_position_risk_pct": 0.0,
        "pending_order_risk_pct": 0.0,
        "new_trade_sl_risk_pct": 1.0,
        "spread_slippage_commission_buffer_pct": 0.0,
        "correlated_exposure_buffer_pct": 0.0,
        "concentration_buffer_pct": 0.0,
        "day_trade_count": 0,
        "session_trade_count": 0,
        "symbol_day_trade_count": 0,
        "symbol_session_trade_count": 0,
        "simultaneous_candidate_count": 1,
        "symbol": "XAUUSD",
        "route_session": "ny_kz",
    }
    state.update(overrides)
    return state


def runtime_decision(*, apply_to_execution: bool = True) -> GTOSVNextRuntimeDecision:
    return GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "XAUUSD", "route_session": "ny_kz"},
        enabled=True,
        apply_to_execution=apply_to_execution,
        matched=True,
        reason="stage05_prop_safe_selector_scenario",
        evidence={
            "matched_rows": 3,
            "metrics": {
                "cost_adjusted_simulated_r": {"sum": 3.0, "mean": 1.0},
                "stress_simulated_r": {"sum": 1.5, "mean": 0.5},
                "effective_n": {"sum": 30},
            },
        },
    )


def selector_scenarios() -> list[dict[str, Any]]:
    return [
        {
            "scenario_id": "reset_before_0000_gmt3",
            "current_time_utc": "2026-05-25T20:59:00+00:00",
            "current_risk_pct": 1.0,
            "account_state": base_account(),
        },
        {
            "scenario_id": "reset_after_0000_gmt3",
            "current_time_utc": "2026-05-25T21:01:00+00:00",
            "current_risk_pct": 1.0,
            "account_state": base_account(),
        },
        {
            "scenario_id": "malaysia_0500_reset_conversion",
            "current_time_utc": "2026-05-25T20:59:00+00:00",
            "current_risk_pct": 1.0,
            "account_state": base_account(),
        },
        {
            "scenario_id": "intraday_profit_plus_2pct_daily_cushion_7000",
            "current_time_utc": "2026-05-25T12:00:00+00:00",
            "current_risk_pct": 1.0,
            "account_state": base_account(current_equity=102000.0),
        },
        {
            "scenario_id": "losing_day_reduces_cushion",
            "current_time_utc": "2026-05-25T12:00:00+00:00",
            "current_risk_pct": 1.0,
            "account_state": base_account(current_equity=97000.0),
        },
        {
            "scenario_id": "overall_static_initial_balance_floor",
            "current_time_utc": "2026-05-25T12:00:00+00:00",
            "current_risk_pct": 2.0,
            "account_state": base_account(
                current_equity=91000.0,
                day_start=91000.0,
                new_trade_sl_risk_pct=2.0,
            ),
        },
        {
            "scenario_id": "open_floating_loss_current_equity_included",
            "current_time_utc": "2026-05-25T12:00:00+00:00",
            "current_risk_pct": 1.0,
            "account_state": base_account(
                current_equity=96000.0,
                open_position_risk_pct=0.5,
                new_trade_sl_risk_pct=1.0,
            ),
        },
        {
            "scenario_id": "pending_order_risk_included",
            "current_time_utc": "2026-05-25T12:00:00+00:00",
            "current_risk_pct": 1.0,
            "account_state": base_account(pending_order_risk_pct=4.5),
        },
        {
            "scenario_id": "multiple_simultaneous_candidates_reserved",
            "current_time_utc": "2026-05-25T12:00:00+00:00",
            "current_risk_pct": 2.0,
            "account_state": base_account(
                new_trade_sl_risk_pct=2.0,
                simultaneous_candidate_count=3,
            ),
        },
        {
            "scenario_id": "correlated_exposure_buffer_included",
            "current_time_utc": "2026-05-25T12:00:00+00:00",
            "current_risk_pct": 1.0,
            "account_state": base_account(correlated_exposure_buffer_pct=4.5),
        },
        {
            "scenario_id": "reduced_risk_instead_of_block",
            "current_time_utc": "2026-05-25T12:00:00+00:00",
            "current_risk_pct": 2.0,
            "account_state": base_account(
                current_equity=96500.0,
                new_trade_sl_risk_pct=2.0,
            ),
        },
        {
            "scenario_id": "defer_until_reset",
            "current_time_utc": "2026-05-25T12:00:00+00:00",
            "current_risk_pct": 1.0,
            "account_state": base_account(
                current_equity=95200.0,
                new_trade_sl_risk_pct=1.0,
            ),
        },
        {
            "scenario_id": "hard_block_only_when_projected_breach_exists",
            "current_time_utc": "2026-05-25T12:00:00+00:00",
            "current_risk_pct": 1.0,
            "account_state": base_account(current_equity=89000.0, day_start=89000.0),
        },
        {
            "scenario_id": "internal_4pct_overlay_reported_separately",
            "current_time_utc": "2026-05-25T12:00:00+00:00",
            "current_risk_pct": 1.0,
            "config": base_config(
                prop_safe_selector_internal_daily_overlay_enabled=True,
                prop_safe_selector_internal_daily_overlay_pct=4.0,
            ),
            "account_state": base_account(
                current_equity=96500.0,
                new_trade_sl_risk_pct=1.0,
            ),
        },
    ]


def evaluate_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    config = scenario.get("config") or base_config()
    selector = evaluate_vnext_prop_safe_selector(
        decision=runtime_decision(),
        config=config,
        current_risk_pct=float(scenario["current_risk_pct"]),
        account_state=scenario["account_state"],
        current_time_utc=scenario["current_time_utc"],
        candidate_context={
            "symbol": scenario["account_state"].get("symbol", "XAUUSD"),
            "route_session": scenario["account_state"].get("route_session", "ny_kz"),
        },
    )
    record = selector.to_record()
    external = record["external_rule_projection"]
    internal = record["internal_overlay_projection"]
    exposure = record["exposure_breakdown"]
    return {
        "schema_version": "vnext_production_change_stage05_prop_safe_selector_row_v1",
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_05_PROP_SAFE_SELECTOR",
        "row_type": "prop_safe_selector_scenario",
        "scenario_id": scenario["scenario_id"],
        "current_time_utc": scenario["current_time_utc"],
        "selector_action": selector.action,
        "selector_would_action": selector.would_action,
        "selector_applied": selector.applied,
        "before_risk_pct": selector.before_risk_pct,
        "after_risk_pct": selector.after_risk_pct,
        "max_allowed_new_trade_risk_pct": selector.max_allowed_new_trade_risk_pct,
        "reason": selector.reason,
        "external_daily_loss_limit_pct": external.get("daily_loss_limit_pct"),
        "external_daily_loss_amount": external.get("daily_loss_amount"),
        "external_daily_floor": external.get("daily_floor"),
        "remaining_daily_cushion": external.get("remaining_daily_cushion"),
        "projected_daily_cushion_after_full_risk": external.get(
            "projected_daily_cushion_after_full_risk"
        ),
        "overall_max_loss_pct": external.get("overall_max_loss_pct"),
        "max_loss_floor": external.get("max_loss_floor"),
        "remaining_overall_cushion": external.get("remaining_overall_cushion"),
        "projected_overall_cushion_after_full_risk": external.get(
            "projected_overall_cushion_after_full_risk"
        ),
        "trailing_drawdown_modeled": external.get("trailing_drawdown_modeled"),
        "internal_overlay_enabled": internal.get("enabled", False),
        "internal_overlay_applies_to_budget": internal.get("applies_to_selector_budget", False),
        "internal_overlay_daily_loss_limit_pct": internal.get("daily_loss_limit_pct"),
        "internal_overlay_remaining_daily_cushion": internal.get("remaining_daily_cushion"),
        "internal_overlay_distinct_from_external": internal.get(
            "distinct_from_redacted_account_external_daily_limit", True
        ),
        "open_position_risk_amount": exposure.get("open_position_risk_amount"),
        "pending_order_risk_amount": exposure.get("pending_order_risk_amount"),
        "new_trade_sl_risk_amount": exposure.get("new_trade_sl_risk_amount"),
        "spread_slippage_commission_buffer_amount": exposure.get(
            "spread_slippage_commission_buffer_amount"
        ),
        "correlated_exposure_buffer_amount": exposure.get(
            "correlated_exposure_buffer_amount"
        ),
        "concentration_buffer_amount": exposure.get("concentration_buffer_amount"),
        "simultaneous_candidate_reserved_risk_amount": exposure.get(
            "simultaneous_candidate_reserved_risk_amount"
        ),
        "reset_window": record["reset_window"],
        "selector_record": record,
        "no_live_trading": True,
        "no_broker_mutation": True,
        "activation_gate": "gtos_vnext_runtime.prop_safe_selector_apply_to_execution",
    }


def prop_metrics_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scenarios = Counter(str(row.get("scenario") or "") for row in rows)
    phases = Counter(str(row.get("phase_target") or "") for row in rows)
    risks = sorted({float(row.get("risk_per_trade_pct") or 0.0) for row in rows})
    return {
        "source_path": rel(PROP_METRICS_PATH),
        "row_count": len(rows),
        "scenario_counts": dict(sorted(scenarios.items())),
        "phase_target_counts": dict(sorted(phases.items())),
        "risk_per_trade_pct_values": risks,
        "breach_rows": sum(
            1
            for row in rows
            if row.get("implementation_decision") == "prop_risk_breach_in_replay_proxy"
        ),
        "deterministic_pass_rows": sum(
            1 for row in rows if row.get("passed_deterministic_sequence") is True
        ),
        "trade_count_min": min(int(row.get("trade_count") or 0) for row in rows),
        "trade_count_max": max(int(row.get("trade_count") or 0) for row in rows),
        "max_trades_day": max(
            int(row.get("calendar_clustering_max_trades_day") or 0) for row in rows
        ),
        "max_loss_streak": max(int(row.get("max_loss_streak") or 0) for row in rows),
        "max_drawdown_pct": max(float(row.get("max_drawdown_pct") or 0.0) for row in rows),
        "pass_probability_proxy_min": min(
            float(row.get("monthly_bootstrap_pass_probability_proxy") or 0.0)
            for row in rows
        ),
        "pass_probability_proxy_max": max(
            float(row.get("monthly_bootstrap_pass_probability_proxy") or 0.0)
            for row in rows
        ),
    }


def robustness_summary() -> dict[str, Any]:
    index_rows = read_jsonl(ROBUSTNESS_PROP_INDEX_PATH)
    symbols: Counter[str] = Counter()
    sessions: Counter[str] = Counter()
    sides: Counter[str] = Counter()
    frameworks: Counter[str] = Counter()
    source_modes: Counter[str] = Counter()
    source_statuses: Counter[str] = Counter()
    performance_count = 0.0
    total_r = 0.0
    max_drawdown_r = 0.0
    max_loss_streak = 0
    profit_factor_values: list[float] = []
    expectancy_values: list[float] = []
    for row in iter_gzip_index(ROBUSTNESS_PROP_INDEX_PATH):
        if row.get("symbol"):
            symbols[str(row["symbol"])] += 1
        if row.get("session_bucket"):
            sessions[str(row["session_bucket"])] += 1
        if row.get("side"):
            sides[str(row["side"])] += 1
        if row.get("framework"):
            frameworks[str(row["framework"])] += 1
        for key, value in (row.get("source_mode_confidence_counts") or {}).items():
            source_modes[str(key)] += int(value or 0)
        for key, value in (row.get("source_status_counts") or {}).items():
            source_statuses[str(key)] += int(value or 0)
        perf = row.get("performance_metrics") or {}
        count = float(perf.get("performance_count") or 0.0)
        performance_count += count
        total_r += float(perf.get("total_r") or 0.0)
        max_drawdown_r = max(max_drawdown_r, float(perf.get("max_drawdown_r") or 0.0))
        max_loss_streak = max(max_loss_streak, int(perf.get("max_loss_streak") or 0))
        if perf.get("profit_factor") is not None:
            profit_factor_values.append(float(perf["profit_factor"]))
        if perf.get("expectancy_r") is not None:
            expectancy_values.append(float(perf["expectancy_r"]))
    return {
        "source_path": rel(ROBUSTNESS_PROP_INDEX_PATH),
        "chunk_count": len(index_rows),
        "logical_row_count": sum(int(row.get("row_count") or 0) for row in index_rows),
        "symbols": dict(sorted(symbols.items())),
        "sessions": dict(sorted(sessions.items())),
        "sides": dict(sorted(sides.items())),
        "frameworks": dict(sorted(frameworks.items())),
        "source_mode_counts": dict(sorted(source_modes.items())),
        "source_status_counts": dict(sorted(source_statuses.items())),
        "aggregate_performance_count_overlapping_groups": performance_count,
        "aggregate_total_r_overlapping_groups": total_r,
        "weighted_expectancy_r_overlapping_groups": (
            total_r / performance_count if performance_count else None
        ),
        "max_drawdown_r": max_drawdown_r,
        "max_loss_streak": max_loss_streak,
        "profit_factor_min": min(profit_factor_values) if profit_factor_values else None,
        "profit_factor_max": max(profit_factor_values) if profit_factor_values else None,
        "expectancy_r_min": min(expectancy_values) if expectancy_values else None,
        "expectancy_r_max": max(expectancy_values) if expectancy_values else None,
    }


def missed_winner_summary() -> dict[str, Any]:
    index_rows = read_jsonl(MISSED_WINNER_INDEX_PATH)
    classifications: Counter[str] = Counter()
    symbols: Counter[str] = Counter()
    sessions: Counter[str] = Counter()
    sides: Counter[str] = Counter()
    frameworks: Counter[str] = Counter()
    for row in iter_gzip_index(MISSED_WINNER_INDEX_PATH):
        classifications[str(row.get("classification") or "unknown")] += 1
        if row.get("symbol"):
            symbols[str(row["symbol"])] += 1
        if row.get("route_session"):
            sessions[str(row["route_session"])] += 1
        if row.get("side"):
            sides[str(row["side"])] += 1
        if row.get("framework"):
            frameworks[str(row["framework"])] += 1
    return {
        "source_path": rel(MISSED_WINNER_INDEX_PATH),
        "chunk_count": len(index_rows),
        "logical_row_count": sum(int(row.get("row_count") or 0) for row in index_rows),
        "classification_counts": dict(sorted(classifications.items())),
        "symbols": dict(sorted(symbols.items())),
        "sessions": dict(sorted(sessions.items())),
        "sides": dict(sorted(sides.items())),
        "frameworks": dict(sorted(frameworks.items())),
    }


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    prop_rows = read_jsonl(PROP_METRICS_PATH)
    action_counts = Counter(str(row["selector_action"]) for row in rows)
    would_counts = Counter(str(row["selector_would_action"]) for row in rows)
    return {
        "schema_version": "vnext_production_change_stage05_prop_safe_selector_summary_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": utc_now(),
        "prop_safe_selector_ledger_path": rel(PROP_SELECTOR_LEDGER_PATH),
        "prop_safe_selector_dossier_path": rel(STAGE05_DOSSIER_PATH),
        "scenario_row_count": len(rows),
        "required_scenario_count": len(REQUIRED_SCENARIOS),
        "missing_required_scenarios": sorted(
            REQUIRED_SCENARIOS - {str(row["scenario_id"]) for row in rows}
        ),
        "selector_action_counts": dict(sorted(action_counts.items())),
        "selector_would_action_counts": dict(sorted(would_counts.items())),
        "non_trivial_no_trade_check": {
            "has_allow": action_counts.get("ALLOW", 0) > 0,
            "has_reduce_risk": action_counts.get("REDUCE_RISK", 0) > 0,
            "has_defer_until_reset": action_counts.get("DEFER_UNTIL_RESET", 0) > 0,
            "has_block": action_counts.get("BLOCK", 0) > 0,
            "budget_allows_some_trades": action_counts.get("ALLOW", 0) > 0,
        },
        "prop_replay_metrics": prop_metrics_summary(prop_rows),
        "robustness_metrics": robustness_summary(),
        "missed_winner_avoided_loser_metrics": missed_winner_summary(),
        "external_budget_math": {
            "account_model": "redacted_account_100k_challenge",
            "phase1_target_pct": 8.0,
            "phase2_target_pct": 5.0,
            "daily_loss_limit_pct": 5.0,
            "daily_reset_timezone": "00:00 GMT+3",
            "daily_reset_malaysia_time": "05:00 Malaysia",
            "overall_max_loss_pct": 10.0,
            "overall_floor_mode": "static_initial_balance_floor",
            "trailing_drawdown_modeled": False,
        },
    }


def write_dossier(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    prop = summary["prop_replay_metrics"]
    robust = summary["robustness_metrics"]
    missed = summary["missed_winner_avoided_loser_metrics"]
    action_counts = summary["selector_action_counts"]
    reset_before = next(row for row in rows if row["scenario_id"] == "reset_before_0000_gmt3")
    profit_row = next(
        row for row in rows if row["scenario_id"] == "intraday_profit_plus_2pct_daily_cushion_7000"
    )
    lines = [
        "# vNext Production Change Stage05 Prop-Safe Selector Dossier",
        "",
        f"Created: {summary['created_at_utc']}",
        "",
        "## Selector Contract",
        "",
        "- Account model: redacted_account-style 100k challenge.",
        "- Phase targets: Phase 1 8%, Phase 2 5%.",
        "- External daily loss: 5% of initial balance, reset at 00:00 GMT+3.",
        "- Malaysia conversion: 00:00 GMT+3 equals 05:00 Malaysia time.",
        "- Daily floor: day_start_equity_or_balance_baseline - initial_balance * 0.05.",
        "- Overall floor: initial_balance * 0.90, static, no trailing drawdown modeled.",
        "- Internal 4% overlay is reported separately and never masquerades as the external rule.",
        "- Runtime actions are limited to ALLOW, REDUCE_RISK, DEFER_UNTIL_RESET, or BLOCK.",
        "",
        "## Replay Prop-Risk Baseline",
        "",
        f"- Prop metric rows: {prop['row_count']}.",
        f"- Breach rows: {prop['breach_rows']}; deterministic pass rows: {prop['deterministic_pass_rows']}.",
        f"- Trade count range: {prop['trade_count_min']} to {prop['trade_count_max']}.",
        f"- Max trades/day: {prop['max_trades_day']}.",
        f"- Max loss streak: {prop['max_loss_streak']}.",
        f"- Max drawdown proxy pct: {prop['max_drawdown_pct']:.6f}.",
        f"- Pass proxy range: {prop['pass_probability_proxy_min']:.6f} to {prop['pass_probability_proxy_max']:.6f}.",
        "",
        "## R And Expectancy",
        "",
        "- R/expectancy source: full replay robustness prop metric chunks; these are overlapping group metrics, not a single account curve.",
        f"- Robustness rows: {robust['logical_row_count']} across {robust['chunk_count']} chunks.",
        f"- Aggregate overlapping performance rows: {robust['aggregate_performance_count_overlapping_groups']:.0f}.",
        f"- Aggregate overlapping total R: {robust['aggregate_total_r_overlapping_groups']:.6f}.",
        f"- Weighted overlapping expectancy R: {robust['weighted_expectancy_r_overlapping_groups']:.6f}.",
        f"- Profit factor range: {robust['profit_factor_min']:.6f} to {robust['profit_factor_max']:.6f}.",
        f"- Robustness max drawdown R: {robust['max_drawdown_r']:.6f}.",
        f"- Robustness max loss streak: {robust['max_loss_streak']}.",
        "",
        "## Missed Winners And Avoided Losers",
        "",
        f"- Source rows: {missed['logical_row_count']} across {missed['chunk_count']} chunks.",
        f"- Classification counts: {json.dumps(missed['classification_counts'], sort_keys=True)}.",
        "",
        "## Selector Behavior",
        "",
        f"- Scenario rows: {summary['scenario_row_count']}.",
        f"- Selector action counts: {json.dumps(action_counts, sort_keys=True)}.",
        f"- Selector would-action counts: {json.dumps(summary['selector_would_action_counts'], sort_keys=True)}.",
        f"- +2% intraday profit remaining daily cushion: {profit_row['remaining_daily_cushion']:.2f}.",
        f"- Reset before-row next reset UTC: {reset_before['reset_window']['next_reset_utc']}.",
        f"- Reset before-row next reset Malaysia: {reset_before['reset_window']['next_reset_malaysia_time']}.",
        "",
        "## Daily And Max-Loss Proximity",
        "",
        "- Daily-loss proximity is reported per row as remaining_daily_cushion and projected_daily_cushion_after_full_risk.",
        "- Max-loss proximity is reported per row as remaining_overall_cushion and projected_overall_cushion_after_full_risk.",
        "- Intraday profit increases the current-equity cushion; losing days reduce it.",
        "",
        "## Coverage",
        "",
        f"- Symbols: {json.dumps(robust['symbols'], sort_keys=True)}.",
        f"- Sessions: {json.dumps(robust['sessions'], sort_keys=True)}.",
        f"- Sides: {json.dumps(robust['sides'], sort_keys=True)}.",
        f"- Frameworks: {json.dumps(robust['frameworks'], sort_keys=True)}.",
        f"- Source modes: {json.dumps(robust['source_mode_counts'], sort_keys=True)}.",
        "",
        "## Activation Boundary",
        "",
        "- Current config enables selector telemetry but keeps prop_safe_selector_apply_to_execution=false.",
        "- No live trading, broker mutation, paid API, trailing drawdown assumption, or arbitrary no-trade collapse is introduced.",
        "- If budget remains available, the selector preserves opportunity through ALLOW or REDUCE_RISK.",
        "",
    ]
    STAGE05_DOSSIER_PATH.write_text("\n".join(lines), encoding="utf-8")


def verify_rows(rows: list[dict[str, Any]], summary: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    scenario_ids = {str(row["scenario_id"]) for row in rows}
    if scenario_ids != REQUIRED_SCENARIOS:
        failures.append(f"scenario coverage mismatch: {sorted(REQUIRED_SCENARIOS - scenario_ids)}")
    action_counts = Counter(str(row["selector_action"]) for row in rows)
    for action in ("ALLOW", "REDUCE_RISK", "DEFER_UNTIL_RESET", "BLOCK"):
        if action_counts.get(action, 0) <= 0:
            failures.append(f"missing selector action {action}")
    plus_profit = next(
        (
            row
            for row in rows
            if row["scenario_id"] == "intraday_profit_plus_2pct_daily_cushion_7000"
        ),
        None,
    )
    if not plus_profit or round(float(plus_profit["remaining_daily_cushion"]), 2) != 7000.0:
        failures.append("+2% intraday profit scenario did not produce 7000 daily cushion")
    before = next((row for row in rows if row["scenario_id"] == "reset_before_0000_gmt3"), None)
    after = next((row for row in rows if row["scenario_id"] == "reset_after_0000_gmt3"), None)
    if not before or before["reset_window"]["next_reset_utc"] != "2026-05-25T21:00:00+00:00":
        failures.append("before-reset UTC window mismatch")
    if not before or before["reset_window"]["next_reset_malaysia_time"] != "2026-05-26T05:00:00+08:00":
        failures.append("Malaysia reset conversion mismatch")
    if not after or after["reset_window"]["reset_window_start_utc"] != "2026-05-25T21:00:00+00:00":
        failures.append("after-reset window start mismatch")
    if any(row.get("trailing_drawdown_modeled") for row in rows):
        failures.append("selector modeled trailing drawdown")
    internal = next(
        (row for row in rows if row["scenario_id"] == "internal_4pct_overlay_reported_separately"),
        None,
    )
    if not internal or internal["internal_overlay_daily_loss_limit_pct"] != 4.0:
        failures.append("internal 4pct overlay scenario missing")
    if not internal or internal["external_daily_loss_limit_pct"] != 5.0:
        failures.append("external daily rule is not distinct 5pct")
    if summary["prop_replay_metrics"]["row_count"] != 24:
        failures.append("prop metrics row count must be 24")
    if summary["prop_replay_metrics"]["breach_rows"] != 24:
        failures.append("prop metrics breach row count must be 24")
    if summary["prop_replay_metrics"]["deterministic_pass_rows"] != 0:
        failures.append("prop metrics deterministic pass count must be zero")
    if not summary["non_trivial_no_trade_check"]["budget_allows_some_trades"]:
        failures.append("selector collapsed to no-trade despite budget availability")
    if summary["missed_winner_avoided_loser_metrics"]["logical_row_count"] != 253234:
        failures.append("missed winner / avoided loser source row count mismatch")
    if summary["robustness_metrics"]["logical_row_count"] != 6954:
        failures.append("robustness prop source row count mismatch")
    return failures


def update_state(summary: dict[str, Any], *, complete: bool) -> None:
    state_path = REPO_ROOT / STATE_PATH
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["updated_at_utc"] = utc_now()
    state["current_git_head"] = stage02.git_head()
    state["dirty_tracked_paths"] = stage02.git_status_short()
    state["current_stage"] = "STAGE_06_LTF_ENTRY_NOFILL_ENGINE" if complete else "STAGE_05_PROP_SAFE_SELECTOR"
    state["stage_status_table"]["STAGE_05_PROP_SAFE_SELECTOR"] = (
        "complete" if complete else "in_progress"
    )
    if complete:
        state["stage_status_table"]["STAGE_06_LTF_ENTRY_NOFILL_ENGINE"] = "in_progress"
        state["active_invariant"] = "fix_m15_blindness_with_ltf_path_aware_execution"
        state["first_incomplete_invariant"] = "STAGE_06_LTF_ENTRY_NOFILL_ENGINE"
        state["exact_next_action"] = (
            "Build and test the replayable LTF path-aware entry/no-fill engine "
            "without restarting Stage00-05."
        )
    else:
        state["active_invariant"] = "build_prop_safe_selector_and_trade_throttle"
        state["first_incomplete_invariant"] = "STAGE_05_PROP_SAFE_SELECTOR"
        state["exact_next_action"] = (
            "Run Stage05 verifier and focused runtime/config tests for redacted_account "
            "budget math, then mark Stage05 complete if checks pass."
        )
    state.setdefault("one_time_steers_applied", {}).setdefault(
        "redacted_account_prop_safe_budget_math_2026_05_25",
        {
            "applied_at_stage": "STAGE_05_PROP_SAFE_SELECTOR",
            "disposition": "apply_and_do_not_relitigate_after_implementation",
            "summary": (
                "Implement prop-safe selector as redacted_account 100k challenge budget "
                "governance with 5% reset-window daily loss, static 10% initial-balance "
                "max loss, intraday profit cushion, and separate internal 4% overlay."
            ),
        },
    )
    state["output_artifact_paths"]["prop_safe_selector_ledger"] = rel(PROP_SELECTOR_LEDGER_PATH)
    state["output_artifact_paths"]["stage05_prop_safe_selector_summary"] = rel(
        STAGE05_SUMMARY_PATH
    )
    state["output_artifact_paths"]["prop_safe_selector_dossier"] = rel(STAGE05_DOSSIER_PATH)
    state["output_artifact_paths"]["stage05_verification_result"] = rel(
        STAGE05_VERIFICATION_RESULT_PATH
    )
    state["rows_groups_processed"]["stage05_prop_safe_selector_scenarios"] = summary[
        "scenario_row_count"
    ]
    state["row_count_hash_coverage"]["stage05_prop_safe_selector_summary"] = {
        "scenario_row_count": summary["scenario_row_count"],
        "selector_action_counts": summary["selector_action_counts"],
        "selector_would_action_counts": summary["selector_would_action_counts"],
        "prop_metric_rows": summary["prop_replay_metrics"]["row_count"],
        "prop_metric_breach_rows": summary["prop_replay_metrics"]["breach_rows"],
        "missed_winner_avoided_loser_rows": summary[
            "missed_winner_avoided_loser_metrics"
        ]["logical_row_count"],
        "robustness_prop_metric_rows": summary["robustness_metrics"]["logical_row_count"],
    }
    state["verification_status"]["stage05_prop_safe_selector_built"] = True
    state["verification_status"]["stage05_prop_safe_selector_scenarios"] = summary[
        "scenario_row_count"
    ]
    state["verification_status"]["stage05_verifier_ok"] = complete
    state["remaining_executable_actions"] = (
        [
            "STAGE_06 LTF entry/no-fill engine",
            "STAGE_07 AI policy",
            "STAGE_08 AI supervisor",
            "STAGE_09 forward-only replay",
            "STAGE_10 activation dossier and completion audit",
        ]
        if complete
        else [
            "STAGE_05 prop-safe selector",
            "STAGE_06 LTF entry/no-fill engine",
            "STAGE_07 AI policy",
            "STAGE_08 AI supervisor",
            "STAGE_09 forward-only replay",
            "STAGE_10 activation dossier and completion audit",
        ]
    )
    stage02.stage01.stage00.atomic_json_write(state_path, state)


def main() -> int:
    rows = [evaluate_scenario(scenario) for scenario in selector_scenarios()]
    summary = build_summary(rows)
    failures = verify_rows(rows, summary)
    write_jsonl(PROP_SELECTOR_LEDGER_PATH, rows)
    atomic_json_write(STAGE05_SUMMARY_PATH, summary)
    write_dossier(rows, summary)
    update_state(summary, complete=False)
    result = {
        "schema_version": "vnext_production_change_stage05_verification_result_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": utc_now(),
        "ok": not failures,
        "failures": failures,
        "summary": summary,
        "first_incomplete_invariant": "STAGE_05_PROP_SAFE_SELECTOR",
    }
    atomic_json_write(STAGE05_VERIFICATION_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
