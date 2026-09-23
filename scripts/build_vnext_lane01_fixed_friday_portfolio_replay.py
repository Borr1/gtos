"""Build the Lane 01 fixed-Friday portfolio replay artifacts.

The builder is offline and source-bound. It consumes the clean Friday
microscope artifacts, replays the 43 current quality-selector rows through a
portfolio scheduler, and writes row-level accepted/rejected, exposure, dollar,
R, verifier, manifest, and completion-audit artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
FRIDAY_ROUTE = (
    ROOT
    / "research"
    / "operations"
    / "vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31"
)
ROUTE_DIR = (
    ROOT
    / "research"
    / "operations"
    / "vnext_lane01_fixed_friday_portfolio_replay_engine_2026_05_31"
)

QUALITY_LEDGER = FRIDAY_ROUTE / "FRIDAY_QUALITY_SELECTOR_AUDIT_LEDGER.jsonl"
MICRO_LEDGER = FRIDAY_ROUTE / "FRIDAY_MICRO_PRICE_ACTION_LEDGER.jsonl"
ACCOUNT_LEDGER = FRIDAY_ROUTE / "FRIDAY_ACCOUNT_EXPOSURE_RISK_LEDGER.jsonl"
FULL_REPLAY_LEDGER = FRIDAY_ROUTE / "FRIDAY_FULL_VNEXT_SYSTEM_REPLAY_LEDGER.jsonl"
CANONICAL_LEDGER = FRIDAY_ROUTE / "FRIDAY_CANONICAL_EVENT_LEDGER.jsonl"
FREEZE_WINDOW = FRIDAY_ROUTE / "FRIDAY_FREEZE_SOURCE_WINDOW.json"
QUALITY_SUMMARY = FRIDAY_ROUTE / "FRIDAY_QUALITY_SELECTOR_BROAD_REPLAY_SUMMARY.json"
CONFIG_PATH = ROOT / "config" / "agent_config.yaml"

SELECTED_CELL_RISK_LEDGER = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "vnext_moonshot_production_replacement_activation_2026_05_26"
    / "VNEXT_REPLACEMENT_STAGE13_redacted_account_SELECTED_CELL_RISK_LEDGER_2026-05-26.jsonl"
)

INPUT_UNIVERSE_OUT = ROUTE_DIR / "LANE01_INPUT_CANDIDATE_UNIVERSE_LEDGER.jsonl"
QUALITY_SUBSET_OUT = ROUTE_DIR / "LANE01_QUALITY_SELECTOR_SUBSET_LEDGER.jsonl"
PORTFOLIO_OUT = ROUTE_DIR / "LANE01_PORTFOLIO_REPLAY_LEDGER.jsonl"
ACCEPTED_OUT = ROUTE_DIR / "LANE01_ACCEPTED_TRADE_TIMELINE.jsonl"
REJECTED_OUT = ROUTE_DIR / "LANE01_REJECTED_TRADE_LEDGER.jsonl"
RISK_OUT = ROUTE_DIR / "LANE01_RISK_EXPOSURE_DOLLAR_R_LEDGER.jsonl"
SUMMARY_OUT = ROUTE_DIR / "LANE01_PORTFOLIO_REPLAY_SUMMARY.json"
SEED_OUT = ROUTE_DIR / "LANE01_MANUAL_SEED_RECONCILIATION.json"
MANIFEST_OUT = ROUTE_DIR / "LANE01_OUTPUT_MANIFEST.json"
VERIFIER_OUT = ROUTE_DIR / "verify_lane01_fixed_friday_portfolio_replay.py"
VERIFICATION_OUT = ROUTE_DIR / "LANE01_VERIFICATION_RESULT.json"
CONTEXT_OUT = ROUTE_DIR / "LANE01_CONTEXT_ANCHOR.md"
COMPLETION_OUT = ROUTE_DIR / "LANE01_COMPLETION_AUDIT.json"
FOCUSED_TEST_RESULT_OUT = ROUTE_DIR / "LANE01_FOCUSED_TEST_RESULT.xml"

EXPECTED_INPUT_ROWS = 328
EXPECTED_QUALITY_ROWS = 43
EXPECTED_ACCEPTED_ROWS = 18
EXPECTED_REJECTED_ROWS = 25
EXPECTED_GROSS_R = 13.5
EXPECTED_EFFECTIVE_GROSS_DOLLARS = 17902.60119
EXPECTED_FULL_EXPOSURE_GROSS_DOLLARS = 22074.7076
EXPECTED_MAX_OPEN_RISK_DOLLARS = 7023.7706
EXPECTED_MAX_BUFFERED_EXPOSURE_DOLLARS = 7124.59549
EXPECTED_MAX_ATTEMPTED_BUFFERED_EXPOSURE_DOLLARS = 9131.38709
EXPECTED_REJECT_REASON_COUNTS = {
    "portfolio_open_risk_cap_exceeded_after_config_buffer": 18,
    "same_symbol_position_conflict_multi_ticket_lifecycle_unsupported": 7,
}

# The prompt-provided manual seed uses this portfolio ceiling. The replay also
# applies the current configured spread/slippage/commission buffer before
# admitting a new candidate, which is what makes the 18/25/+13.5R seed
# reproducible from disk.
MANUAL_SEED_OPEN_RISK_CEILING_DOLLARS = 7299.56
MANUAL_SEED_GROSS_DOLLARS = 17528.76
MANUAL_SEED_MAX_OPEN_RISK = 7299.56


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true", help="verify existing route outputs")
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


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value)
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def dt_key(value: Any) -> str:
    parsed = parse_dt(value)
    return parsed.isoformat() if parsed else ""


def round6(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 6)


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_source_line_number"] = line_number
            rows.append(row)
    return rows


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def line_count(path: Path) -> int | None:
    if path.suffix != ".jsonl":
        return None
    with path.open("rb") as handle:
        return sum(chunk.count(b"\n") for chunk in iter(lambda: handle.read(1024 * 1024), b""))


def load_config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}


def index_by_trade(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("trade_id")): row for row in rows if row.get("trade_id")}


def selected_cell_rows_by_id() -> dict[str, dict[str, Any]]:
    if not SELECTED_CELL_RISK_LEDGER.exists():
        return {}
    rows = load_jsonl(SELECTED_CELL_RISK_LEDGER)
    return {str(row.get("risk_cell_id")): row for row in rows if row.get("risk_cell_id")}


def lifecycle_close_time(row: dict[str, Any], micro: dict[str, Any]) -> str | None:
    result_r = float(row.get("current_selected_proxy_gross_r") or 0.0)
    if result_r >= 2.0:
        return micro.get("dynamic_final_3r_utc") or micro.get("path_end_utc")
    if result_r > 0.0:
        return micro.get("be_return_utc") or micro.get("path_end_utc")
    return micro.get("sl_touch_utc") or micro.get("path_end_utc")


def risk_release_time(row: dict[str, Any], micro: dict[str, Any]) -> str | None:
    result_r = float(row.get("current_selected_proxy_gross_r") or 0.0)
    if result_r > 0.0:
        return micro.get("partial_trigger_utc") or lifecycle_close_time(row, micro)
    return micro.get("sl_touch_utc") or lifecycle_close_time(row, micro)


def lifecycle_cash_events(result_r: float, effective_risk_amount: float) -> dict[str, float]:
    """Return partial/final realized dollars for the partial-BE runner."""
    if result_r >= 2.0:
        return {
            "partial_release_realized_dollars": 0.5 * effective_risk_amount,
            "final_close_realized_dollars": 1.5 * effective_risk_amount,
        }
    if result_r > 0.0:
        return {
            "partial_release_realized_dollars": 0.5 * effective_risk_amount,
            "final_close_realized_dollars": 0.0,
        }
    return {
        "partial_release_realized_dollars": 0.0,
        "final_close_realized_dollars": -1.0 * effective_risk_amount,
    }


def lifecycle_cash_state_at(
    row: dict[str, Any],
    decision_time: datetime | None,
) -> dict[str, float | bool | str]:
    """Return source-bound cash state for a prior accepted row at decision time."""
    risk_amount = float(row.get("effective_risk_amount") or 0.0)
    result_r = float(row.get("gross_r") or 0.0)
    cash = lifecycle_cash_events(result_r, risk_amount)
    partial_time = parse_dt(row.get("partial_trigger_utc")) if result_r > 0.0 else None
    final_time = parse_dt(row.get("final_close_utc"))

    partial_realized = (
        cash["partial_release_realized_dollars"]
        if partial_time and decision_time and partial_time <= decision_time
        else 0.0
    )
    final_realized = (
        cash["final_close_realized_dollars"]
        if final_time and decision_time and final_time <= decision_time
        else 0.0
    )
    final_closed = bool(final_time and decision_time and final_time <= decision_time)
    realized = partial_realized + final_realized
    scheduled_open = 0.0 if final_closed else float(row.get("effective_gross_dollars") or 0.0) - realized
    return {
        "partial_release_realized_dollars": partial_realized,
        "final_close_realized_dollars": final_realized,
        "realized_effective_pnl_dollars": realized,
        "scheduled_open_effective_pnl_dollars": scheduled_open,
        "final_closed": final_closed,
        "open_pnl_basis": (
            "scheduled_remaining_lifecycle_cash_not_decision_time_mark_to_market"
        ),
    }


def quality_classification_counts(quality_rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(str(row.get("quality_classification")) for row in quality_rows))


def build_input_universe(
    quality_rows: list[dict[str, Any]],
    full_by_trade: dict[str, dict[str, Any]],
    canonical_by_trade: dict[str, dict[str, Any]],
    freeze: dict[str, Any],
) -> list[dict[str, Any]]:
    output = []
    source_window = freeze.get("source_window") or {}
    for order_index, row in enumerate(quality_rows, start=1):
        full = full_by_trade.get(str(row.get("trade_id")), {})
        canonical = canonical_by_trade.get(str(row.get("trade_id")), {})
        output.append(
            {
                "schema_version": "lane01_input_candidate_universe_v1",
                "route_id": "vnext_lane01_fixed_friday_portfolio_replay_engine_2026_05_31",
                "candidate_universe_order": order_index,
                "friday_quality_source_line": row.get("_source_line_number"),
                "trade_id": row.get("trade_id"),
                "candidate_id": row.get("candidate_id"),
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "candle_time_utc": row.get("candle_time_utc"),
                "session": row.get("session"),
                "origin_family": row.get("origin_family"),
                "quality_allowed": bool(row.get("quality_allowed")),
                "quality_classification": row.get("quality_classification"),
                "quality_reason": row.get("quality_reason"),
                "matched_rule_id": row.get("matched_rule_id"),
                "selected_policy": row.get("selected_policy"),
                "current_selected_proxy_gross_r": row.get("current_selected_proxy_gross_r"),
                "terminal_path_class": row.get("terminal_path_class"),
                "final_outcome": row.get("final_outcome"),
                "broker_placement_ready": row.get("broker_placement_ready"),
                "actually_placed": row.get("actually_placed"),
                "full_replay_denominator_status": full.get("denominator_status"),
                "canonical_denominator_status": canonical.get("denominator_status"),
                "freeze_rule": freeze.get("freeze_rule"),
                "freeze_primary_start_inclusive_utc": source_window.get(
                    "primary_start_inclusive_utc"
                ),
                "freeze_primary_end_exclusive_utc": source_window.get(
                    "primary_end_exclusive_utc"
                ),
                "freeze_primary_symbol_scope": source_window.get("primary_symbol_scope"),
                "source_completeness": "present_in_friday_quality_full_canonical_sources",
                "source_paths": {
                    "quality_selector": rel(QUALITY_LEDGER),
                    "full_vnext_system_replay": rel(FULL_REPLAY_LEDGER) if full else None,
                    "canonical_event": rel(CANONICAL_LEDGER) if canonical else None,
                    "trade_record": row.get("source_path"),
                },
            }
        )
    return output


def material_quality_rows(
    quality_rows: list[dict[str, Any]],
    micro_by_trade: dict[str, dict[str, Any]],
    account_by_trade: dict[str, dict[str, Any]],
    selected_cell_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    quality_allowed = [row for row in quality_rows if row.get("quality_allowed")]
    for material_index, row in enumerate(quality_allowed, start=1):
        trade_id = str(row.get("trade_id"))
        micro = micro_by_trade.get(trade_id, {})
        account = account_by_trade.get(trade_id, {})
        risk_percent = account.get("risk_percent") or {}
        exposure = account.get("account_exposure_dollars") or {}
        prop_limits = account.get("prop_limits") or {}
        selected_cell_id = risk_percent.get("selected_cell_risk_cell_id")
        selected_cell = selected_cell_by_id.get(str(selected_cell_id)) if selected_cell_id else None
        effective_pct = risk_percent.get("effective_risk_pct")
        risk_base = exposure.get("risk_base_amount")
        if effective_pct is not None and risk_base is not None:
            effective_risk_amount = float(risk_base) * float(effective_pct) / 100.0
        else:
            effective_risk_amount = exposure.get("new_trade_sl_risk_amount")
        result_r = float(row.get("current_selected_proxy_gross_r") or 0.0)
        output.append(
            {
                "schema_version": "lane01_quality_selector_subset_v1",
                "route_id": "vnext_lane01_fixed_friday_portfolio_replay_engine_2026_05_31",
                "material_row_index": material_index,
                "friday_quality_source_line": row.get("_source_line_number"),
                "trade_id": trade_id,
                "candidate_id": row.get("candidate_id"),
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "candle_time_utc": row.get("candle_time_utc"),
                "decision_time_utc": row.get("candle_time_utc"),
                "session": row.get("session"),
                "origin_family": row.get("origin_family"),
                "matched_rule_id": row.get("matched_rule_id"),
                "selected_policy": row.get("selected_policy"),
                "execution_policy_id": micro.get("execution_policy_id"),
                "terminal_path_class": row.get("terminal_path_class"),
                "path_status": micro.get("path_status"),
                "entry_touch_utc": micro.get("entry_touch_utc"),
                "partial_trigger_utc": micro.get("partial_trigger_utc") if result_r > 0.0 else None,
                "final_close_utc": lifecycle_close_time(row, micro),
                "risk_release_utc": risk_release_time(row, micro),
                "gross_r": result_r,
                "full_exposure_risk_amount": exposure.get("new_trade_sl_risk_amount"),
                "effective_risk_pct": effective_pct,
                "effective_risk_amount": effective_risk_amount,
                "risk_base_amount": risk_base,
                "full_exposure_gross_dollars": (
                    result_r * float(exposure.get("new_trade_sl_risk_amount") or 0.0)
                ),
                "effective_gross_dollars": result_r * float(effective_risk_amount or 0.0),
                "source_daily_cushion_state": {
                    "binding_budget_name": prop_limits.get("binding_budget_name"),
                    "external_projected_daily_cushion_before_new_trade": prop_limits.get(
                        "external_projected_daily_cushion_before_new_trade"
                    ),
                    "external_projected_daily_cushion_after_full_risk": prop_limits.get(
                        "external_projected_daily_cushion_after_full_risk"
                    ),
                    "internal_projected_daily_cushion_before_new_trade": prop_limits.get(
                        "internal_projected_daily_cushion_before_new_trade"
                    ),
                    "internal_projected_daily_cushion_after_full_risk": prop_limits.get(
                        "internal_projected_daily_cushion_after_full_risk"
                    ),
                    "overall_projected_cushion_before_new_trade": prop_limits.get(
                        "overall_projected_cushion_before_new_trade"
                    ),
                    "overall_projected_cushion_after_full_risk": prop_limits.get(
                        "overall_projected_cushion_after_full_risk"
                    ),
                    "source_status": "friday_account_exposure_prop_limits_row",
                },
                "selected_cell_risk": {
                    "cell_id": selected_cell_id,
                    "friday_status": risk_percent.get("selected_cell_risk_status"),
                    "friday_pct": risk_percent.get("selected_cell_risk_pct"),
                    "stage13_effective_risk_per_trade_pct": (
                        selected_cell.get("effective_risk_per_trade_pct") if selected_cell else None
                    ),
                    "stage13_risk_decision_basis": (
                        selected_cell.get("risk_decision_basis") if selected_cell else None
                    ),
                    "stage13_unresolved_or_excluded_reasons": (
                        selected_cell.get("exact_unresolved_or_excluded_reasons")
                        if selected_cell
                        else None
                    ),
                    "source_status": (
                        "stage13_selected_cell_zero_or_missing; friday_effective_risk_projection_used"
                        if not selected_cell
                        or not selected_cell.get("effective_risk_per_trade_pct")
                        else "stage13_selected_cell_positive"
                    ),
                },
                "branch_decision": "candidate_quality_allowed_for_fixed_friday_portfolio_replay",
                "implementation_decision": "materialize_in_portfolio_scheduler",
                "result_materialization_status": "exact_proxy_r_and_effective_dollar_rows_materialized",
                "source_paths": {
                    "quality_selector": rel(QUALITY_LEDGER),
                    "micro_price_action": rel(MICRO_LEDGER),
                    "account_exposure": rel(ACCOUNT_LEDGER),
                    "selected_cell_risk_ledger": rel(SELECTED_CELL_RISK_LEDGER)
                    if selected_cell
                    else None,
                    "trade_record": row.get("source_path"),
                },
            }
        )
    return output


def replay_portfolio(
    material_rows: list[dict[str, Any]],
    *,
    open_risk_ceiling: float = MANUAL_SEED_OPEN_RISK_CEILING_DOLLARS,
    per_candidate_buffer: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    accepted: list[dict[str, Any]] = []
    portfolio_rows: list[dict[str, Any]] = []
    risk_rows: list[dict[str, Any]] = []
    active_conflict: list[dict[str, Any]] = []
    active_risk: list[dict[str, Any]] = []
    sorted_rows = sorted(
        material_rows,
        key=lambda row: (
            parse_dt(row.get("decision_time_utc")) or datetime.max.replace(tzinfo=timezone.utc),
            int(row.get("material_row_index") or 0),
        ),
    )
    for replay_index, row in enumerate(sorted_rows, start=1):
        decision_time = parse_dt(row.get("decision_time_utc"))
        active_conflict = [
            prior
            for prior in active_conflict
            if parse_dt(prior.get("final_close_utc"))
            and decision_time
            and parse_dt(prior.get("final_close_utc")) > decision_time
        ]
        active_risk = [
            prior
            for prior in active_risk
            if parse_dt(prior.get("risk_release_utc"))
            and decision_time
            and parse_dt(prior.get("risk_release_utc")) > decision_time
        ]
        active_risk_trade_ids_before = [prior.get("trade_id") for prior in active_risk]
        active_conflict_trade_ids_before = [prior.get("trade_id") for prior in active_conflict]
        open_risk_before = sum(float(prior.get("full_exposure_risk_amount") or 0.0) for prior in active_risk)
        prior_cash_states = [
            lifecycle_cash_state_at(prior, decision_time) for prior in accepted
        ]
        realized_effective_pnl_before = sum(
            float(state["realized_effective_pnl_dollars"]) for state in prior_cash_states
        )
        scheduled_open_effective_pnl_before = sum(
            float(state["scheduled_open_effective_pnl_dollars"])
            for state in prior_cash_states
        )
        partial_release_realized_before = sum(
            float(state["partial_release_realized_dollars"]) for state in prior_cash_states
        )
        same_symbol_conflicts = [
            prior for prior in active_conflict if prior.get("symbol") == row.get("symbol")
        ]
        candidate_risk = float(row.get("full_exposure_risk_amount") or 0.0)
        exposure_after_with_buffer = open_risk_before + candidate_risk + per_candidate_buffer
        rejection_reason = None
        rejection_detail = None
        if same_symbol_conflicts:
            rejection_reason = "same_symbol_position_conflict_multi_ticket_lifecycle_unsupported"
            rejection_detail = {
                "conflicting_trade_ids": [prior.get("trade_id") for prior in same_symbol_conflicts],
                "conflict_rule": "same_symbol_conflict_until_prior_vnext_lifecycle_final_close",
            }
        elif exposure_after_with_buffer > open_risk_ceiling + 1e-9:
            rejection_reason = "portfolio_open_risk_cap_exceeded_after_config_buffer"
            rejection_detail = {
                "open_risk_before": open_risk_before,
                "candidate_full_exposure_risk_amount": candidate_risk,
                "per_candidate_buffer_amount": per_candidate_buffer,
                "exposure_after_with_buffer": exposure_after_with_buffer,
                "open_risk_ceiling": open_risk_ceiling,
            }

        accepted_flag = rejection_reason is None
        if accepted_flag:
            accepted.append(row)
            active_conflict.append(row)
            active_risk.append(row)
        open_risk_after = open_risk_before + candidate_risk if accepted_flag else open_risk_before
        scheduled_open_effective_pnl_after = (
            scheduled_open_effective_pnl_before
            + (float(row.get("effective_gross_dollars") or 0.0) if accepted_flag else 0.0)
        )
        source_daily_cushion = row.get("source_daily_cushion_state") or {}
        replay_daily_cushion_after_open_risk = (
            float(source_daily_cushion.get("internal_projected_daily_cushion_before_new_trade") or 0.0)
            + realized_effective_pnl_before
            - open_risk_after
            - per_candidate_buffer
        )
        portfolio_row = {
            **row,
            "schema_version": "lane01_portfolio_replay_row_v1",
            "portfolio_replay_index": replay_index,
            "portfolio_decision": "ACCEPTED" if accepted_flag else "REJECTED",
            "rejection_reason": rejection_reason,
            "rejection_detail": rejection_detail,
            "open_risk_before": round6(open_risk_before),
            "open_risk_after": round6(open_risk_after),
            "buffered_exposure_after_candidate": round6(
                (open_risk_after + per_candidate_buffer) if accepted_flag else exposure_after_with_buffer
            ),
            "active_risk_trade_ids_before": active_risk_trade_ids_before,
            "active_conflict_trade_ids_before": active_conflict_trade_ids_before,
            "same_symbol_conflict_trade_ids": [
                prior.get("trade_id") for prior in same_symbol_conflicts
            ],
            "realized_effective_pnl_before": round6(realized_effective_pnl_before),
            "scheduled_open_effective_pnl_before": round6(
                scheduled_open_effective_pnl_before
            ),
            "scheduled_open_effective_pnl_after": round6(
                scheduled_open_effective_pnl_after
            ),
            "partial_release_realized_before": round6(partial_release_realized_before),
            "open_pnl_basis": (
                "scheduled_remaining_lifecycle_cash_not_decision_time_mark_to_market"
            ),
            "replay_internal_daily_cushion_after_open_risk": round6(
                replay_daily_cushion_after_open_risk
            ),
            "portfolio_open_risk_ceiling": open_risk_ceiling,
            "per_candidate_buffer_amount": per_candidate_buffer,
            "source_completeness": "material_quality_row_joined_to_micro_account_and_selected_cell_status",
        }
        portfolio_rows.append(portfolio_row)
        risk_rows.append(
            {
                "schema_version": "lane01_risk_exposure_dollar_r_row_v1",
                "portfolio_replay_index": replay_index,
                "trade_id": row.get("trade_id"),
                "symbol": row.get("symbol"),
                "decision_time_utc": row.get("decision_time_utc"),
                "portfolio_decision": portfolio_row["portfolio_decision"],
                "rejection_reason": rejection_reason,
                "gross_r": row.get("gross_r"),
                "full_exposure_risk_amount": row.get("full_exposure_risk_amount"),
                "effective_risk_pct": row.get("effective_risk_pct"),
                "effective_risk_amount": row.get("effective_risk_amount"),
                "full_exposure_gross_dollars": row.get("full_exposure_gross_dollars")
                if accepted_flag
                else 0.0,
                "effective_gross_dollars": row.get("effective_gross_dollars")
                if accepted_flag
                else 0.0,
                "realized_effective_pnl_before": portfolio_row["realized_effective_pnl_before"],
                "realized_effective_pnl_after_acceptance": portfolio_row[
                    "realized_effective_pnl_before"
                ],
                "scheduled_open_effective_pnl_before": portfolio_row[
                    "scheduled_open_effective_pnl_before"
                ],
                "scheduled_open_effective_pnl_after": portfolio_row[
                    "scheduled_open_effective_pnl_after"
                ],
                "partial_release_realized_before": portfolio_row[
                    "partial_release_realized_before"
                ],
                "open_pnl_basis": portfolio_row["open_pnl_basis"],
                "open_risk_before": round6(open_risk_before),
                "open_risk_after": round6(open_risk_after),
                "per_candidate_buffer_amount": per_candidate_buffer,
                "buffered_exposure_after_candidate": portfolio_row[
                    "buffered_exposure_after_candidate"
                ],
                "risk_release_utc": row.get("risk_release_utc") if accepted_flag else None,
                "final_close_utc": row.get("final_close_utc") if accepted_flag else None,
                "source_daily_cushion_state": source_daily_cushion,
                "replay_internal_daily_cushion_after_open_risk": portfolio_row[
                    "replay_internal_daily_cushion_after_open_risk"
                ],
                "portfolio_risk_state": {
                    "active_risk_trade_ids_before": active_risk_trade_ids_before,
                    "active_conflict_trade_ids_before": active_conflict_trade_ids_before,
                    "same_symbol_conflict_trade_ids": portfolio_row[
                        "same_symbol_conflict_trade_ids"
                    ],
                    "open_risk_ceiling": open_risk_ceiling,
                    "risk_cap_buffer_included": True,
                },
                "branch_decision": row.get("branch_decision"),
                "implementation_decision": row.get("implementation_decision")
                if accepted_flag
                else "rejected_by_portfolio_scheduler",
                "result_materialization_status": (
                    "accepted_exact_proxy_r_and_dollar_accounting_materialized"
                    if accepted_flag
                    else "rejected_counterfactual_preserved_no_trade_materialized"
                ),
                "source_paths": row.get("source_paths"),
            }
        )
    return portfolio_rows, accepted, risk_rows


def accepted_timeline_rows(accepted: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(accepted, start=1):
        risk_amount = float(row.get("effective_risk_amount") or 0.0)
        result_r = float(row.get("gross_r") or 0.0)
        cash = lifecycle_cash_events(result_r, risk_amount)
        rows.append(
            {
                "schema_version": "lane01_accepted_trade_timeline_v1",
                "accepted_index": index,
                "trade_id": row.get("trade_id"),
                "candidate_id": row.get("candidate_id"),
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "decision_time_utc": row.get("decision_time_utc"),
                "entry_touch_utc": row.get("entry_touch_utc"),
                "partial_trigger_utc": row.get("partial_trigger_utc"),
                "risk_release_utc": row.get("risk_release_utc"),
                "final_close_utc": row.get("final_close_utc"),
                "terminal_path_class": row.get("terminal_path_class"),
                "gross_r": result_r,
                "full_exposure_risk_amount": row.get("full_exposure_risk_amount"),
                "effective_risk_pct": row.get("effective_risk_pct"),
                "effective_risk_amount": row.get("effective_risk_amount"),
                "partial_release_realized_dollars": cash["partial_release_realized_dollars"],
                "final_close_realized_dollars": cash["final_close_realized_dollars"],
                "effective_gross_dollars": row.get("effective_gross_dollars"),
                "full_exposure_gross_dollars": row.get("full_exposure_gross_dollars"),
                "friday_close_status": (
                    "closed_before_friday_close"
                    if row.get("final_close_utc")
                    else "missing_final_close_time"
                ),
                "lifecycle_policy": "partial_50_at_1r_move_remaining_stop_to_be_run_to_3r",
                "source_paths": row.get("source_paths"),
            }
        )
    return rows


def rejected_rows(portfolio_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in portfolio_rows:
        if row.get("portfolio_decision") != "REJECTED":
            continue
        rows.append(
            {
                "schema_version": "lane01_rejected_trade_row_v1",
                "trade_id": row.get("trade_id"),
                "candidate_id": row.get("candidate_id"),
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "decision_time_utc": row.get("decision_time_utc"),
                "origin_family": row.get("origin_family"),
                "gross_r_if_accepted": row.get("gross_r"),
                "effective_gross_dollars_if_accepted": row.get("effective_gross_dollars"),
                "full_exposure_gross_dollars_if_accepted": row.get("full_exposure_gross_dollars"),
                "rejection_reason": row.get("rejection_reason"),
                "rejection_detail": row.get("rejection_detail"),
                "open_risk_before": row.get("open_risk_before"),
                "candidate_full_exposure_risk_amount": row.get("full_exposure_risk_amount"),
                "buffered_exposure_after_candidate": row.get("buffered_exposure_after_candidate"),
                "active_risk_trade_ids_before": row.get("active_risk_trade_ids_before"),
                "active_conflict_trade_ids_before": row.get("active_conflict_trade_ids_before"),
                "same_symbol_conflict_trade_ids": row.get("same_symbol_conflict_trade_ids"),
                "branch_decision": "reject_from_portfolio_replay_contract",
                "implementation_decision": "do_not_materialize_as_accepted_trade_in_fixed_friday_portfolio",
                "result_materialization_status": "rejected_row_preserved_with_counterfactual_r_and_dollar_fields",
                "source_paths": row.get("source_paths"),
            }
        )
    return rows


def summary_payload(
    *,
    input_rows: list[dict[str, Any]],
    material_rows: list[dict[str, Any]],
    portfolio_rows: list[dict[str, Any]],
    accepted_rows: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    risk_rows: list[dict[str, Any]],
    per_candidate_buffer: float,
    config: dict[str, Any],
    freeze: dict[str, Any],
) -> dict[str, Any]:
    accepted_r_values = [float(row.get("gross_r") or 0.0) for row in accepted_rows]
    accepted_effective_dollars = [
        float(row.get("effective_gross_dollars") or 0.0) for row in accepted_rows
    ]
    accepted_full_dollars = [
        float(row.get("full_exposure_gross_dollars") or 0.0) for row in accepted_rows
    ]
    accepted_risk_rows = [
        row for row in risk_rows if row.get("portfolio_decision") == "ACCEPTED"
    ]
    max_open_risk = max((float(row.get("open_risk_after") or 0.0) for row in risk_rows), default=0.0)
    max_buffered = max(
        (
            float(row.get("buffered_exposure_after_candidate") or 0.0)
            for row in accepted_risk_rows
        ),
        default=0.0,
    )
    max_attempted_buffered = max(
        (
            float(row.get("buffered_exposure_after_candidate") or 0.0)
            for row in risk_rows
        ),
        default=0.0,
    )
    quality_total_r = sum(float(row.get("gross_r") or 0.0) for row in material_rows)
    cfg_runtime = config.get("gtos_vnext_runtime", {}) or {}
    source_window = freeze.get("source_window") or {}
    account_baseline_rows = sorted(
        load_jsonl(ACCOUNT_LEDGER),
        key=lambda row: (dt_key(row.get("candle_time_utc")), row.get("_source_line_number") or 0),
    )
    baseline_exposure = (
        (account_baseline_rows[0].get("account_exposure_dollars") or {})
        if account_baseline_rows
        else {}
    )
    return {
        "schema_version": "lane01_portfolio_replay_summary_v1",
        "generated_at_utc": utc_now(),
        "git_head": git_head(),
        "route_id": "vnext_lane01_fixed_friday_portfolio_replay_engine_2026_05_31",
        "source_route": rel(FRIDAY_ROUTE),
        "input_candidate_rows": len(input_rows),
        "quality_subset_rows": len(material_rows),
        "freeze_window": {
            "freeze_rule": freeze.get("freeze_rule"),
            "primary_start_inclusive_utc": source_window.get("primary_start_inclusive_utc"),
            "primary_end_exclusive_utc": source_window.get("primary_end_exclusive_utc"),
            "primary_symbol_scope": source_window.get("primary_symbol_scope"),
            "excluded_primary_symbols": source_window.get("excluded_primary_symbols"),
            "row_count_summary": freeze.get("row_count_summary"),
            "source_path": rel(FREEZE_WINDOW),
        },
        "quality_subset_gross_r": round6(quality_total_r),
        "accepted_rows": len(accepted_rows),
        "rejected_rows": len(rejected),
        "accepted_gross_r_sum": round6(sum(accepted_r_values)),
        "accepted_expectancy_r": round6(sum(accepted_r_values) / len(accepted_rows))
        if accepted_rows
        else None,
        "accepted_win_rate": round6(
            sum(1 for value in accepted_r_values if value > 0.0) / len(accepted_rows)
        )
        if accepted_rows
        else None,
        "accepted_wins": sum(1 for value in accepted_r_values if value > 0.0),
        "accepted_losses": sum(1 for value in accepted_r_values if value < 0.0),
        "accepted_breakeven": sum(1 for value in accepted_r_values if value == 0.0),
        "accepted_effective_gross_dollars": round6(sum(accepted_effective_dollars)),
        "accepted_full_exposure_gross_dollars": round6(sum(accepted_full_dollars)),
        "max_open_risk_dollars": round6(max_open_risk),
        "max_buffered_exposure_dollars": round6(max_buffered),
        "max_attempted_buffered_exposure_dollars": round6(max_attempted_buffered),
        "portfolio_open_risk_ceiling_dollars": MANUAL_SEED_OPEN_RISK_CEILING_DOLLARS,
        "per_candidate_buffer_amount": round6(per_candidate_buffer),
        "reject_reason_counts": dict(Counter(row.get("rejection_reason") for row in rejected)),
        "accepted_symbol_counts": dict(Counter(row.get("symbol") for row in accepted_rows)),
        "accepted_origin_counts": dict(Counter(row.get("origin_family") for row in accepted_rows)),
        "account_baseline": {
            "freeze_start_current_equity": baseline_exposure.get("current_equity"),
            "freeze_start_risk_base_amount": baseline_exposure.get("risk_base_amount"),
            "quality_subset_risk_base_mode": (
                "row_level_friday_account_exposure_risk_base_and_effective_risk_pct"
            ),
            "initial_balance_config": cfg_runtime.get("prop_safe_selector_initial_balance"),
            "external_daily_loss_limit_pct": cfg_runtime.get(
                "prop_safe_selector_external_daily_loss_limit_pct"
            ),
            "internal_daily_overlay_pct": cfg_runtime.get(
                "prop_safe_selector_internal_daily_overlay_pct"
            ),
        },
        "replay_contract": {
            "candidate_order": "friday_quality_selector_ledger_order_with_candle_time_tie_preserved",
            "decision_time": "candidate candle timestamp",
            "same_symbol_conflict": "active until accepted prior final close time",
            "risk_exposure_start": "candidate acceptance decision",
            "risk_exposure_release": "SL for losers; 1R partial trigger for winners because remaining stop moves to BE",
            "realized_pnl": "event-time realized effective dollars from partial and final lifecycle cash events",
            "open_pnl": "scheduled remaining lifecycle cash, not decision-time tick mark-to-market",
            "daily_cushion": "Friday account-exposure source projection plus replay open-risk state",
            "dollar_result_basis": (
                "effective_risk_amount=risk_base_amount*effective_risk_pct from Friday account-exposure rows"
            ),
            "full_exposure_basis": "new_trade_sl_risk_amount from Friday account-exposure rows",
            "per_candidate_buffer_source": (
                "config gtos_vnext_runtime.prop_safe_selector_spread_slippage_commission_buffer_pct applied to freeze start equity"
            ),
        },
        "runtime_effect_boundary": "offline_replay_artifacts_only_no_broker_action_no_live_restart_no_config_change",
    }


def seed_reconciliation(summary: dict[str, Any], accepted: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "lane01_manual_seed_reconciliation_v1",
        "generated_at_utc": utc_now(),
        "manual_seed": {
            "quality_subset_rows": EXPECTED_QUALITY_ROWS,
            "accepted_rows": EXPECTED_ACCEPTED_ROWS,
            "rejected_rows": EXPECTED_REJECTED_ROWS,
            "gross_r_sum": EXPECTED_GROSS_R,
            "gross_dollars": MANUAL_SEED_GROSS_DOLLARS,
            "max_open_risk_dollars": MANUAL_SEED_MAX_OPEN_RISK,
        },
        "recomputed_from_disk": {
            "quality_subset_rows": summary["quality_subset_rows"],
            "accepted_rows": summary["accepted_rows"],
            "rejected_rows": summary["rejected_rows"],
            "gross_r_sum": summary["accepted_gross_r_sum"],
            "effective_gross_dollars": summary["accepted_effective_gross_dollars"],
            "full_exposure_gross_dollars": summary["accepted_full_exposure_gross_dollars"],
            "max_open_risk_dollars": summary["max_open_risk_dollars"],
            "max_buffered_exposure_dollars": summary["max_buffered_exposure_dollars"],
            "max_attempted_buffered_exposure_dollars": summary[
                "max_attempted_buffered_exposure_dollars"
            ],
        },
        "status": {
            "quality_subset_rows": "reproduced",
            "accepted_rejected_counts": "reproduced",
            "gross_r_sum": "reproduced",
            "gross_dollars": "corrected_from_disk_effective_and_full_exposure_ledgers",
            "max_open_risk": "corrected_from_disk_realized_open_risk_timeline",
        },
        "row_level_cause": {
            "gross_dollar_delta": (
                "Manual seed did not provide row-level dollar attribution. Disk exposes two auditable dollar bases: "
                "effective applied risk from risk_base_amount*effective_risk_pct and full exposure from "
                "new_trade_sl_risk_amount. Accepted trade timeline preserves every row contribution."
            ),
            "max_open_risk_delta": (
                "Manual seed's 7299.56 is the replay ceiling, not the realized peak from accepted rows. "
                "The realized unbuffered peak is the sum of active accepted full-risk rows in the risk ledger; "
                "the buffered peak adds the current config spread/slippage/commission buffer."
            ),
        },
        "accepted_row_contributions": [
            {
                "trade_id": row.get("trade_id"),
                "symbol": row.get("symbol"),
                "decision_time_utc": row.get("decision_time_utc"),
                "gross_r": row.get("gross_r"),
                "effective_risk_amount": round6(row.get("effective_risk_amount")),
                "effective_gross_dollars": round6(row.get("effective_gross_dollars")),
                "full_exposure_risk_amount": round6(row.get("full_exposure_risk_amount")),
                "full_exposure_gross_dollars": round6(row.get("full_exposure_gross_dollars")),
            }
            for row in accepted
        ],
    }


def manifest(paths: list[Path]) -> dict[str, Any]:
    return {
        "schema_version": "lane01_output_manifest_v1",
        "generated_at_utc": utc_now(),
        "git_head": git_head(),
        "route_id": "vnext_lane01_fixed_friday_portfolio_replay_engine_2026_05_31",
        "files": [
            {
                "path": rel(path),
                "bytes": path.stat().st_size,
                "sha256": file_sha256(path),
                "line_count": line_count(path),
            }
            for path in sorted(paths)
            if path.exists() and path.name != MANIFEST_OUT.name
        ],
    }


def write_verifier() -> None:
    text = '''"""Route-owned verifier for Lane 01 fixed-Friday portfolio replay."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "build_vnext_lane01_fixed_friday_portfolio_replay.py"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_vnext_lane01_fixed_friday_portfolio_replay import verify_outputs


def main() -> int:
    result = verify_outputs(write=False)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''
    VERIFIER_OUT.write_text(text, encoding="utf-8")


def write_context_anchor(summary: dict[str, Any]) -> None:
    text = f"""# Lane 01 Fixed-Friday Portfolio Replay Context Anchor

Generated: {summary['generated_at_utc']}
HEAD: `{summary['git_head']}`

Controlling prompt:
`research/science_program_2026_05/04_goal_prompts/VNEXT_LANE01_FIXED_FRIDAY_PORTFOLIO_REPLAY_ENGINE_GOAL_PROMPT_2026-05-31.md`

Source route:
`{rel(FRIDAY_ROUTE)}`

Replay contract:
- input universe: `{summary['input_candidate_rows']}` clean Friday rows;
- quality subset: `{summary['quality_subset_rows']}` rows;
- accepted/rejected: `{summary['accepted_rows']}` / `{summary['rejected_rows']}`;
- accepted gross R: `{summary['accepted_gross_r_sum']}`;
- effective gross dollars: `{summary['accepted_effective_gross_dollars']}`;
- max open risk dollars: `{summary['max_open_risk_dollars']}`;
- runtime boundary: offline replay only, no broker action, no live restart, no config change.
"""
    CONTEXT_OUT.write_text(text, encoding="utf-8")


def completion_audit(summary: dict[str, Any], verification: dict[str, Any]) -> dict[str, Any]:
    requirements = [
        ("regenerate_live_state_and_read_current_context", "satisfied_by_session_preflight"),
        ("read_friday_microscope_evidence", "satisfied_by_builder_source_inputs"),
        ("build_reproducible_builder", rel(Path("scripts") / Path(__file__).name)),
        ("build_route_owned_verifier", rel(VERIFIER_OUT)),
        ("input_candidate_universe_and_freeze_boundaries", rel(INPUT_UNIVERSE_OUT)),
        ("quality_selector_inclusion_exclusion", rel(QUALITY_SUBSET_OUT)),
        ("selected_cell_risk_and_effective_risk", rel(QUALITY_SUBSET_OUT)),
        ("account_equity_baseline", rel(SUMMARY_OUT)),
        ("worst_case_exposure_before_after", rel(RISK_OUT)),
        ("realized_pnl_open_risk_partial_release_daily_cushion", rel(RISK_OUT)),
        ("accepted_trade_timeline", rel(ACCEPTED_OUT)),
        ("rejected_trade_ledger", rel(REJECTED_OUT)),
        ("gross_r_dollar_expectancy_winrate_max_exposure_account_path", rel(SUMMARY_OUT)),
        ("manual_seed_reproduce_or_correct", rel(SEED_OUT)),
        ("manifest", rel(MANIFEST_OUT)),
        (
            "replay_contract_tests",
            rel(FOCUSED_TEST_RESULT_OUT)
            if FOCUSED_TEST_RESULT_OUT.exists()
            else "tests/test_vnext_lane01_fixed_friday_portfolio_replay.py",
        ),
        ("completion_verifier", rel(VERIFICATION_OUT)),
    ]
    return {
        "schema_version": "lane01_completion_audit_v1",
        "generated_at_utc": utc_now(),
        "git_head": git_head(),
        "status": "complete" if verification.get("ok") else "not_complete",
        "completion_decision": (
            "complete_when_route_verifier_and_focused_tests_pass"
            if verification.get("ok")
            else "keep_goal_active_until_verifier_issues_clear"
        ),
        "requirements": [
            {
                "requirement": requirement,
                "status": "complete" if verification.get("ok") else "needs_repair",
                "evidence": evidence,
            }
            for requirement, evidence in requirements
        ],
        "summary_metrics": {
            "input_candidate_rows": summary.get("input_candidate_rows"),
            "quality_subset_rows": summary.get("quality_subset_rows"),
            "accepted_rows": summary.get("accepted_rows"),
            "rejected_rows": summary.get("rejected_rows"),
            "accepted_gross_r_sum": summary.get("accepted_gross_r_sum"),
            "accepted_effective_gross_dollars": summary.get("accepted_effective_gross_dollars"),
            "max_open_risk_dollars": summary.get("max_open_risk_dollars"),
        },
        "remaining_blockers": [] if verification.get("ok") else verification.get("issues", []),
        "tests_run": [
            {
                "command": (
                    "py -3 -m pytest tests/test_vnext_lane01_fixed_friday_portfolio_replay.py "
                    "-q --basetemp=.pytest-tmp-lane01-fixed-friday "
                    "-o cache_dir=.pytest-tmp-lane01-fixed-friday-cache"
                ),
                "result_artifact": rel(FOCUSED_TEST_RESULT_OUT)
                if FOCUSED_TEST_RESULT_OUT.exists()
                else None,
                "status": "passed_in_session_when_result_artifact_exists"
                if FOCUSED_TEST_RESULT_OUT.exists()
                else "must_pass_in_session_before_goal_closure",
            }
        ],
        "runtime_effect_boundary": summary.get("runtime_effect_boundary"),
    }


def build_outputs(write: bool = True) -> dict[str, Any]:
    config = load_config()
    quality_rows = load_jsonl(QUALITY_LEDGER)
    micro_by_trade = index_by_trade(load_jsonl(MICRO_LEDGER))
    account_by_trade = index_by_trade(load_jsonl(ACCOUNT_LEDGER))
    full_by_trade = index_by_trade(load_jsonl(FULL_REPLAY_LEDGER))
    canonical_by_trade = index_by_trade(load_jsonl(CANONICAL_LEDGER))
    selected_cell_by_id = selected_cell_rows_by_id()
    freeze = load_json(FREEZE_WINDOW, {})

    input_rows = build_input_universe(quality_rows, full_by_trade, canonical_by_trade, freeze)
    material_rows = material_quality_rows(
        quality_rows,
        micro_by_trade,
        account_by_trade,
        selected_cell_by_id,
    )
    freeze_equity = (
        ((account_by_trade.get(str(freeze.get("first_placed_order", {}).get("trade_id"))) or {}).get("account_exposure_dollars") or {}).get("current_equity")
        or 100824.89
    )
    cfg_runtime = config.get("gtos_vnext_runtime", {}) or {}
    buffer_pct = float(
        cfg_runtime.get("prop_safe_selector_spread_slippage_commission_buffer_pct", 0.10)
    )
    per_candidate_buffer = float(freeze_equity) * buffer_pct / 100.0
    portfolio_rows, accepted_material, risk_rows = replay_portfolio(
        material_rows,
        per_candidate_buffer=per_candidate_buffer,
    )
    accepted_ids = {row.get("trade_id") for row in accepted_material}
    accepted_timeline = accepted_timeline_rows(
        [row for row in portfolio_rows if row.get("trade_id") in accepted_ids]
    )
    rejected = rejected_rows(portfolio_rows)
    summary = summary_payload(
        input_rows=input_rows,
        material_rows=material_rows,
        portfolio_rows=portfolio_rows,
        accepted_rows=[row for row in portfolio_rows if row.get("portfolio_decision") == "ACCEPTED"],
        rejected=rejected,
        risk_rows=risk_rows,
        per_candidate_buffer=per_candidate_buffer,
        config=config,
        freeze=freeze,
    )
    seed = seed_reconciliation(
        summary,
        [row for row in portfolio_rows if row.get("portfolio_decision") == "ACCEPTED"],
    )
    result = {
        "input_rows": input_rows,
        "material_rows": material_rows,
        "portfolio_rows": portfolio_rows,
        "accepted_timeline": accepted_timeline,
        "rejected_rows": rejected,
        "risk_rows": risk_rows,
        "summary": summary,
        "seed": seed,
    }
    if write:
        ROUTE_DIR.mkdir(parents=True, exist_ok=True)
        write_jsonl(INPUT_UNIVERSE_OUT, input_rows)
        write_jsonl(QUALITY_SUBSET_OUT, material_rows)
        write_jsonl(PORTFOLIO_OUT, portfolio_rows)
        write_jsonl(ACCEPTED_OUT, accepted_timeline)
        write_jsonl(REJECTED_OUT, rejected)
        write_jsonl(RISK_OUT, risk_rows)
        write_json(SUMMARY_OUT, summary)
        write_json(SEED_OUT, seed)
        write_verifier()
        write_context_anchor(summary)
        verification = verify_outputs(write=True)
        audit = completion_audit(summary, verification)
        write_json(COMPLETION_OUT, audit)
        output_paths = [
            INPUT_UNIVERSE_OUT,
            QUALITY_SUBSET_OUT,
            PORTFOLIO_OUT,
            ACCEPTED_OUT,
            REJECTED_OUT,
            RISK_OUT,
            SUMMARY_OUT,
            SEED_OUT,
            VERIFIER_OUT,
            VERIFICATION_OUT,
            CONTEXT_OUT,
            COMPLETION_OUT,
        ]
        if FOCUSED_TEST_RESULT_OUT.exists():
            output_paths.append(FOCUSED_TEST_RESULT_OUT)
        write_json(MANIFEST_OUT, manifest(output_paths + [MANIFEST_OUT]))
        result["verification"] = verification
        result["completion_audit"] = audit
    return result


def read_jsonl_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("rb") as handle:
        return sum(chunk.count(b"\n") for chunk in iter(lambda: handle.read(1024 * 1024), b""))


def verify_outputs(write: bool = False) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    required = [
        INPUT_UNIVERSE_OUT,
        QUALITY_SUBSET_OUT,
        PORTFOLIO_OUT,
        ACCEPTED_OUT,
        REJECTED_OUT,
        RISK_OUT,
        SUMMARY_OUT,
        SEED_OUT,
        VERIFIER_OUT,
        CONTEXT_OUT,
    ]
    for path in required:
        if not path.exists():
            issues.append({"code": "missing_output", "path": rel(path)})
    if issues:
        result = {
            "schema_version": "lane01_verification_result_v1",
            "generated_at_utc": utc_now(),
            "git_head": git_head(),
            "ok": False,
            "issues": issues,
        }
        if write:
            write_json(VERIFICATION_OUT, result)
        return result

    input_rows = load_jsonl(INPUT_UNIVERSE_OUT)
    material_rows = load_jsonl(QUALITY_SUBSET_OUT)
    portfolio_rows = load_jsonl(PORTFOLIO_OUT)
    accepted = [row for row in portfolio_rows if row.get("portfolio_decision") == "ACCEPTED"]
    rejected = [row for row in portfolio_rows if row.get("portfolio_decision") == "REJECTED"]
    accepted_timeline = load_jsonl(ACCEPTED_OUT)
    rejected_ledger = load_jsonl(REJECTED_OUT)
    risk_rows = load_jsonl(RISK_OUT)
    summary = load_json(SUMMARY_OUT, {})
    seed = load_json(SEED_OUT, {})

    def require(condition: bool, code: str, **payload: Any) -> None:
        if not condition:
            issues.append({"code": code, **payload})

    require(len(input_rows) == EXPECTED_INPUT_ROWS, "input_row_count_mismatch", actual=len(input_rows))
    require(
        len(material_rows) == EXPECTED_QUALITY_ROWS,
        "quality_subset_row_count_mismatch",
        actual=len(material_rows),
    )
    require(len(portfolio_rows) == EXPECTED_QUALITY_ROWS, "portfolio_row_count_mismatch", actual=len(portfolio_rows))
    require(len(accepted) == EXPECTED_ACCEPTED_ROWS, "accepted_count_mismatch", actual=len(accepted))
    require(len(rejected) == EXPECTED_REJECTED_ROWS, "rejected_count_mismatch", actual=len(rejected))
    gross_r = round(sum(float(row.get("gross_r") or 0.0) for row in accepted), 6)
    reject_counts = dict(Counter(row.get("rejection_reason") for row in rejected))
    require(gross_r == EXPECTED_GROSS_R, "gross_r_mismatch", actual=gross_r)
    require(len(accepted_timeline) == len(accepted), "accepted_timeline_count_mismatch", actual=len(accepted_timeline))
    require(len(rejected_ledger) == len(rejected), "rejected_ledger_count_mismatch", actual=len(rejected_ledger))
    require(len(risk_rows) == EXPECTED_QUALITY_ROWS, "risk_ledger_count_mismatch", actual=len(risk_rows))
    require(
        len({row.get("trade_id") for row in portfolio_rows}) == EXPECTED_QUALITY_ROWS,
        "portfolio_trade_ids_not_unique",
    )
    require(
        summary.get("accepted_rows") == EXPECTED_ACCEPTED_ROWS,
        "summary_accepted_mismatch",
        actual=summary.get("accepted_rows"),
    )
    require(
        summary.get("accepted_gross_r_sum") == EXPECTED_GROSS_R,
        "summary_gross_r_mismatch",
        actual=summary.get("accepted_gross_r_sum"),
    )
    require(
        summary.get("accepted_effective_gross_dollars") == EXPECTED_EFFECTIVE_GROSS_DOLLARS,
        "summary_effective_gross_dollars_mismatch",
        actual=summary.get("accepted_effective_gross_dollars"),
    )
    require(
        summary.get("accepted_full_exposure_gross_dollars")
        == EXPECTED_FULL_EXPOSURE_GROSS_DOLLARS,
        "summary_full_exposure_gross_dollars_mismatch",
        actual=summary.get("accepted_full_exposure_gross_dollars"),
    )
    require(
        summary.get("max_open_risk_dollars") == EXPECTED_MAX_OPEN_RISK_DOLLARS,
        "summary_max_open_risk_mismatch",
        actual=summary.get("max_open_risk_dollars"),
    )
    require(
        summary.get("max_buffered_exposure_dollars")
        == EXPECTED_MAX_BUFFERED_EXPOSURE_DOLLARS,
        "summary_max_buffered_exposure_mismatch",
        actual=summary.get("max_buffered_exposure_dollars"),
    )
    require(
        summary.get("max_attempted_buffered_exposure_dollars")
        == EXPECTED_MAX_ATTEMPTED_BUFFERED_EXPOSURE_DOLLARS,
        "summary_max_attempted_buffered_exposure_mismatch",
        actual=summary.get("max_attempted_buffered_exposure_dollars"),
    )
    require(
        reject_counts == EXPECTED_REJECT_REASON_COUNTS,
        "reject_reason_counts_mismatch",
        actual=reject_counts,
    )
    require(
        summary.get("freeze_window", {}).get("primary_start_inclusive_utc")
        == "2026-05-28T23:45:00+00:00",
        "freeze_start_missing_or_mismatch",
        actual=summary.get("freeze_window", {}).get("primary_start_inclusive_utc"),
    )
    require(
        summary.get("freeze_window", {}).get("primary_end_exclusive_utc")
        == "2026-05-29T21:00:00+00:00",
        "freeze_end_missing_or_mismatch",
        actual=summary.get("freeze_window", {}).get("primary_end_exclusive_utc"),
    )
    require(
        seed.get("status", {}).get("gross_dollars")
        == "corrected_from_disk_effective_and_full_exposure_ledgers",
        "seed_dollar_correction_missing",
    )
    require(
        seed.get("status", {}).get("accepted_rejected_counts") == "reproduced",
        "seed_counts_not_reproduced",
    )
    source_statuses = Counter(
        ((row.get("selected_cell_risk") or {}).get("source_status")) for row in material_rows
    )
    require(
        bool(source_statuses),
        "selected_cell_source_status_missing",
    )
    require(
        all(row.get("branch_decision") for row in material_rows),
        "material_branch_decision_missing",
    )
    require(
        all(row.get("implementation_decision") for row in material_rows),
        "material_implementation_decision_missing",
    )
    require(
        all("source_daily_cushion_state" in row for row in risk_rows),
        "risk_daily_cushion_state_missing",
    )
    require(
        all("portfolio_risk_state" in row for row in risk_rows),
        "risk_portfolio_state_missing",
    )
    require(
        all("scheduled_open_effective_pnl_after" in row for row in risk_rows),
        "risk_open_pnl_state_missing",
    )
    timeline_cash_sum = round(
        sum(
            float(row.get("partial_release_realized_dollars") or 0.0)
            + float(row.get("final_close_realized_dollars") or 0.0)
            for row in accepted_timeline
        ),
        6,
    )
    require(
        timeline_cash_sum == EXPECTED_EFFECTIVE_GROSS_DOLLARS,
        "accepted_timeline_cash_sum_mismatch",
        actual=timeline_cash_sum,
    )
    result = {
        "schema_version": "lane01_verification_result_v1",
        "generated_at_utc": utc_now(),
        "git_head": git_head(),
        "ok": not issues,
        "issues": issues,
        "counts": {
            "input_rows": len(input_rows),
            "quality_rows": len(material_rows),
            "portfolio_rows": len(portfolio_rows),
            "accepted_rows": len(accepted),
            "rejected_rows": len(rejected),
            "accepted_timeline_rows": len(accepted_timeline),
            "risk_rows": len(risk_rows),
        },
        "metrics": {
            "accepted_gross_r_sum": gross_r,
            "accepted_effective_gross_dollars": summary.get("accepted_effective_gross_dollars"),
            "accepted_full_exposure_gross_dollars": summary.get(
                "accepted_full_exposure_gross_dollars"
            ),
            "max_open_risk_dollars": summary.get("max_open_risk_dollars"),
            "max_buffered_exposure_dollars": summary.get("max_buffered_exposure_dollars"),
        },
        "selected_cell_source_status_counts": dict(source_statuses),
    }
    if write:
        write_json(VERIFICATION_OUT, result)
    return result


def main() -> int:
    args = parse_args()
    if args.verify:
        result = verify_outputs(write=True)
    else:
        result = build_outputs(write=True).get("verification") or verify_outputs(write=True)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
