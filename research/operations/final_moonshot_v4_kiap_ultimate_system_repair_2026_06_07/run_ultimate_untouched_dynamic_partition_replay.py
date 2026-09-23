from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.v4_timewarp_simulated_live_research_loop import (  # noqa: E402
    CampaignConfig,
    REPAIRED_PENDING_EXPIRY_MINUTES,
    SimulatedBroker,
    atomic_write_json,
    build_source_package,
    load_config,
    run_campaign,
    stable_sha256,
    summarize_campaign,
    utc_now,
)


ROUTE = Path(__file__).resolve().parent
ROUTE_ID = "final_moonshot_v4_kiap_ultimate_system_repair_2026_06_07"
PREFIX = "ULTIMATE_UNTOUCHED_DYNAMIC"
SCHEMA_PREFIX = "ultimate_untouched_dynamic"
PARITY_SCHEMA_VERSION = "ultimate_untouched_live_replay_packet_parity_v1"
PARITY_CHECK_PREFIX = "untouched_dynamic"
PARITY_SCOPE = "local_untouched_dynamic_replay_packet_semantics_not_broker_mutation"
REPLAY_PHASE_FIELD = "untouched_replay_phase"
SOURCE_STRATEGY = "one_day_source_package_per_untouched_phase_day_bounded_materialization"
PHASE_HELP_NOUN = "untouched"


@dataclass(frozen=True)
class PhaseSpec:
    phase: str
    parent_partition_id: str
    days: tuple[str, ...]
    partition_role: str

    @property
    def campaign_name(self) -> str:
        return self.phase


PHASE_SPECS: tuple[PhaseSpec, ...] = (
    PhaseSpec(
        phase="ultimate_untouched_gap_rolling",
        parent_partition_id="untouched_gap_rolling_20260427_20260428",
        days=("2026-04-27", "2026-04-28"),
        partition_role="rolling_gap_after_mechanism_freeze",
    ),
    PhaseSpec(
        phase="ultimate_untouched_calendar_stress",
        parent_partition_id="untouched_calendar_stress_20260501_20260504",
        days=("2026-05-01", "2026-05-04"),
        partition_role="calendar_holiday_and_post_weekend_stress_after_mechanism_freeze",
    ),
)

LEDGER_FILES = {
    "asof": f"{PREFIX}_ASOF_MARKET_DATA_LEDGER.jsonl",
    "candidate": f"{PREFIX}_CANDIDATE_MICROSCOPE_LEDGER.jsonl",
    "packet_sidecar": f"{PREFIX}_PACKET_SIDECAR_LEDGER.jsonl",
    "scorecard": f"{PREFIX}_SELECTOR_SCHEDULER_SCORECARD.jsonl",
    "oracle": f"{PREFIX}_ORDERED_PATH_ORACLE_LEDGER.jsonl",
    "order": f"{PREFIX}_SIMULATED_ORDER_LEDGER.jsonl",
    "trade": f"{PREFIX}_SIMULATED_TRADE_LEDGER.jsonl",
    "event": f"{PREFIX}_SIMULATED_EVENT_LEDGER.jsonl",
    "account": f"{PREFIX}_SIMULATED_ACCOUNT_LEDGER.jsonl",
    "missed": f"{PREFIX}_MISSED_OPPORTUNITY_LEDGER.jsonl",
    "winner": f"{PREFIX}_WINNER_ANATOMY_LEDGER.jsonl",
    "loser": f"{PREFIX}_LOSER_ANATOMY_LEDGER.jsonl",
    "exit": f"{PREFIX}_EXIT_GEOMETRY_HARVEST_LEDGER.jsonl",
    "rollup": f"{PREFIX}_SYMBOL_SESSION_FRAMEWORK_POLICY_ROLLUP.jsonl",
    "daily": f"{PREFIX}_DAILY_MICROSCOPE_SUMMARY.jsonl",
}
SOURCE_LEDGER_FILES = (
    f"{PREFIX}_SOURCE_HYDRATION_LEDGER.jsonl",
    f"{PREFIX}_FTMO_HYDRATION_BLOCKER_LEDGER.jsonl",
    f"{PREFIX}_SYMBOL_MAPPING_LEDGER.jsonl",
    f"{PREFIX}_MARKET_STARVATION_LEDGER.jsonl",
    f"{PREFIX}_DAY_PROGRESS_LEDGER.jsonl",
    f"{PREFIX}_DEGRADATION_REPAIR_LEDGER.jsonl",
    f"{PREFIX}_LIVE_REPLAY_PACKET_PARITY_LEDGER.jsonl",
)


def _append_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    count = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")
            count += 1
    return count


def _reset_outputs() -> None:
    for filename in tuple(LEDGER_FILES.values()) + SOURCE_LEDGER_FILES:
        (ROUTE / filename).write_text("", encoding="utf-8")


def _num(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if number != number or number in (float("inf"), float("-inf")):
        return default
    return number


def _phase_stats() -> dict[str, Any]:
    return {
        "candidate_rows": 0,
        "orders_seen": set(),
        "terminal_status_by_order": {},
        "not_filled_orders": 0,
        "filled_trades": 0,
        "gross_r": 0.0,
        "expected_cost_r": 0.0,
        "net_proxy_r": 0.0,
        "winners": 0,
        "losses": 0,
        "same_bar_ambiguity_count": 0,
        "risk_decision_reason_counts": Counter(),
        "order_status_counts": Counter(),
        "row_counts": Counter(),
    }


def _update_phase_stats(stats: dict[str, Any], ledgers: Mapping[str, list[dict[str, Any]]]) -> None:
    stats["candidate_rows"] += len(ledgers.get("candidate", []))
    for key, rows in ledgers.items():
        stats["row_counts"][key] += len(rows)
    for order in ledgers.get("order", []):
        order_id = str(order.get("simulated_order_id") or "")
        status = str(order.get("order_status") or "")
        if order_id:
            stats["orders_seen"].add(order_id)
        if status in {"filled", "expired_unfilled", "risk_rejected"}:
            stats["terminal_status_by_order"][order_id] = status
        stats["order_status_counts"][status or "missing"] += 1
        stats["risk_decision_reason_counts"][str(order.get("risk_decision_reason") or "missing")] += 1
    for oracle in ledgers.get("oracle", []):
        if str(oracle.get("fill_status") or "").startswith("not_filled"):
            stats["not_filled_orders"] += 1
        if oracle.get("same_bar_ambiguity") is True:
            stats["same_bar_ambiguity_count"] += 1
    for trade in ledgers.get("trade", []):
        if trade.get("net_proxy_r") is None:
            continue
        net = _num(trade.get("net_proxy_r"))
        stats["filled_trades"] += 1
        stats["gross_r"] += _num(trade.get("gross_r"))
        stats["expected_cost_r"] += _num(trade.get("expected_cost_r"))
        stats["net_proxy_r"] += net
        if net > 0:
            stats["winners"] += 1
        elif net < 0:
            stats["losses"] += 1


def _final_phase_summary(spec: PhaseSpec, stats: Mapping[str, Any], broker: SimulatedBroker) -> dict[str, Any]:
    terminal_statuses = stats["terminal_status_by_order"]
    filled = int(stats["filled_trades"])
    return {
        "phase": spec.phase,
        "parent_partition_id": spec.parent_partition_id,
        "partition_role": spec.partition_role,
        "days": list(spec.days),
        "touched_by_prior_iterative_rule_tuning": False,
        "candidate_rows": int(stats["candidate_rows"]),
        "simulated_orders": len(stats["orders_seen"]),
        "filled_trades": filled,
        "risk_rejected_orders": sum(1 for status in terminal_statuses.values() if status == "risk_rejected"),
        "expired_unfilled_orders": sum(1 for status in terminal_statuses.values() if status == "expired_unfilled"),
        "not_filled_orders": int(stats["not_filled_orders"]),
        "gross_r": round(float(stats["gross_r"]), 8),
        "expected_cost_r": round(float(stats["expected_cost_r"]), 8),
        "net_proxy_r": round(float(stats["net_proxy_r"]), 8),
        "total_r": round(float(stats["net_proxy_r"]), 8),
        "avg_r_per_filled_trade": round(float(stats["net_proxy_r"]) / filled, 8) if filled else None,
        "winners": int(stats["winners"]),
        "losses": int(stats["losses"]),
        "ending_balance": round(broker.account.balance, 8),
        "max_drawdown_pct": round(broker.account.max_drawdown_pct, 8),
        "same_bar_ambiguity_count": int(stats["same_bar_ambiguity_count"]),
        "risk_decision_reason_counts": dict(sorted(stats["risk_decision_reason_counts"].items())),
        "order_status_counts": dict(sorted(stats["order_status_counts"].items())),
        "row_counts": dict(sorted(stats["row_counts"].items())),
    }


def _risk_authority(row: Mapping[str, Any]) -> Mapping[str, Any]:
    auth = row.get("risk_authority")
    return auth if isinstance(auth, Mapping) else {}


def _allocator(row: Mapping[str, Any]) -> Mapping[str, Any]:
    packet = _risk_authority(row).get("dynamic_daily_drawdown_budget_allocator")
    return packet if isinstance(packet, Mapping) else {}


def _degradation_rows(
    ledgers: Mapping[str, list[dict[str, Any]]],
    *,
    spec: PhaseSpec,
    day: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for trade in ledgers.get("trade", []):
        net = _num(trade.get("net_proxy_r"))
        gross = _num(trade.get("gross_r"))
        cost = _num(trade.get("expected_cost_r"))
        if net < 0 or (gross > 0 and gross - cost < 0):
            rows.append(
                {
                    "schema_version": f"{SCHEMA_PREFIX}_degradation_repair_v1",
                    "route_id": ROUTE_ID,
                    "repair_family": "filled_trade_negative_or_cost_flip",
                    "phase": spec.phase,
                    "parent_partition_id": spec.parent_partition_id,
                    "trading_day": day,
                    "candidate_id": trade.get("candidate_id"),
                    "simulated_order_id": trade.get("simulated_order_id"),
                    "simulated_trade_id": trade.get("simulated_trade_id"),
                    "symbol": trade.get("symbol"),
                    "side": trade.get("side"),
                    "route_session": trade.get("route_session"),
                    "session": trade.get("session"),
                    "framework": trade.get("framework"),
                    "dynamic_geometry_policy": trade.get("dynamic_geometry_policy"),
                    "gross_r": trade.get("gross_r"),
                    "expected_cost_r": trade.get("expected_cost_r"),
                    "net_proxy_r": trade.get("net_proxy_r"),
                    "terminal_outcome": trade.get("terminal_outcome"),
                    "close_reason": trade.get("close_reason"),
                    "allocator_status": _allocator(trade).get("status"),
                    "allocator_reason": _allocator(trade).get("reason"),
                    "repair_instruction": "route into generalized mechanism repair only; do not tune exact touched block lists from this row",
                    "evidence_class": f"{PARITY_CHECK_PREFIX}_filled_trade_degradation_row",
                }
            )
    for missed in ledgers.get("missed", []):
        net = _num(missed.get("net_proxy_r"))
        if net <= 0:
            continue
        rows.append(
            {
                "schema_version": f"{SCHEMA_PREFIX}_degradation_repair_v1",
                "route_id": ROUTE_ID,
                "repair_family": "positive_missed_opportunity_requires_source_or_scheduler_review",
                "phase": spec.phase,
                "parent_partition_id": spec.parent_partition_id,
                "trading_day": day,
                "candidate_id": missed.get("candidate_id"),
                "symbol": missed.get("symbol"),
                "side": missed.get("side"),
                "decision_time_utc": missed.get("decision_time_utc"),
                "gross_r": missed.get("gross_r"),
                "expected_cost_r": missed.get("expected_cost_r"),
                "net_proxy_r": missed.get("net_proxy_r"),
                "path_source": missed.get("path_source"),
                "ordered_tick_truth_satisfied": missed.get("ordered_tick_truth_satisfied"),
                "repair_instruction": "generalize any promotion candidate across rolling/stress partitions before config changes",
                "evidence_class": f"{PARITY_CHECK_PREFIX}_missed_opportunity_repair_row",
            }
        )
    return rows


def _parity_counter() -> dict[str, Counter[str]]:
    return {
        "candidate_selector_packet": Counter(),
        "candidate_live_decision_packet_v4": Counter(),
        "candidate_pre_scheduler_risk_source": Counter(),
        "scheduler_window_packet": Counter(),
        "scheduler_symbol_risk_config": Counter(),
        "order_runtime_risk_authority": Counter(),
        "order_dynamic_daily_drawdown_allocator": Counter(),
        "execution_sidecar_order_packet": Counter(),
    }


def _record_parity(parity: dict[str, Counter[str]], ledgers: Mapping[str, list[dict[str, Any]]]) -> None:
    for row in ledgers.get("packet_sidecar", []):
        sidecar_type = row.get("sidecar_type")
        if sidecar_type == "candidate_v4_decision_stack":
            parity["candidate_selector_packet"]["rows"] += 1
            parity["candidate_live_decision_packet_v4"]["rows"] += 1
            parity["candidate_pre_scheduler_risk_source"]["rows"] += 1
            if isinstance(row.get("selector_packet"), Mapping):
                parity["candidate_selector_packet"]["present"] += 1
            if isinstance(row.get("live_decision_packet_v4"), Mapping):
                parity["candidate_live_decision_packet_v4"]["present"] += 1
            pre = row.get("risk_authority_pre_scheduler")
            if isinstance(pre, Mapping) and pre.get("risk_config_source"):
                parity["candidate_pre_scheduler_risk_source"]["present"] += 1
        elif sidecar_type == "scheduler_v4_window":
            parity["scheduler_window_packet"]["rows"] += 1
            if isinstance(row.get("scheduler_packet"), Mapping):
                parity["scheduler_window_packet"]["present"] += 1
        elif sidecar_type == "execution_manager_v4":
            parity["execution_sidecar_order_packet"]["rows"] += 1
            if isinstance(row.get("order_row"), Mapping):
                parity["execution_sidecar_order_packet"]["present"] += 1
    for row in ledgers.get("scorecard", []):
        parity["scheduler_symbol_risk_config"]["rows"] += 1
        if isinstance(row.get("scheduler_symbol_risk_config"), Mapping) and row.get("scheduler_symbol_risk_config"):
            parity["scheduler_symbol_risk_config"]["present"] += 1
    for row in ledgers.get("order", []):
        parity["order_runtime_risk_authority"]["rows"] += 1
        parity["order_dynamic_daily_drawdown_allocator"]["rows"] += 1
        auth = _risk_authority(row)
        if auth.get("risk_config_source"):
            parity["order_runtime_risk_authority"]["present"] += 1
        if isinstance(auth.get("dynamic_daily_drawdown_budget_allocator"), Mapping):
            parity["order_dynamic_daily_drawdown_allocator"]["present"] += 1


def _parity_rows(parity: Mapping[str, Counter[str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for check_id, counter in sorted(parity.items()):
        row_count = int(counter.get("rows", 0))
        present = int(counter.get("present", 0))
        if row_count == 0:
            status = "not_applicable_no_rows_after_calendar_no_session_breadth_guard"
        elif present == row_count:
            status = "pass"
        else:
            status = "missing_or_partial"
        rows.append(
            {
                "schema_version": PARITY_SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "check_id": f"{PARITY_CHECK_PREFIX}_{check_id}",
                "row_count": row_count,
                "present_count": present,
                "missing_count": row_count - present,
                "status": status,
                "live_replay_parity_scope": PARITY_SCOPE,
                "evidence_class": "packet_parity_checker_output",
            }
        )
    return rows


def _append_ledgers(ledgers: Mapping[str, list[dict[str, Any]]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for key, filename in LEDGER_FILES.items():
        counts[key] = _append_jsonl(ROUTE / filename, ledgers.get(key, []))
    return counts


def _decorate_source_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    spec: PhaseSpec,
    day: str,
    source_row_type: str,
) -> list[dict[str, Any]]:
    return [
        {
            "route_id": ROUTE_ID,
            REPLAY_PHASE_FIELD: spec.phase,
            "parent_partition_id": spec.parent_partition_id,
            "partition_role": spec.partition_role,
            "trading_day": day,
            "source_row_type": source_row_type,
            **dict(row),
        }
        for row in rows
    ]


def _append_source_package_rows(source_package: Mapping[str, Any], *, spec: PhaseSpec, day: str) -> dict[str, int]:
    return {
        "source_hydration": _append_jsonl(
            ROUTE / f"{PREFIX}_SOURCE_HYDRATION_LEDGER.jsonl",
            _decorate_source_rows(
                source_package.get("source_hydration_rows", []),
                spec=spec,
                day=day,
                source_row_type="source_hydration",
            ),
        ),
        "ftmo_blocker": _append_jsonl(
            ROUTE / f"{PREFIX}_FTMO_HYDRATION_BLOCKER_LEDGER.jsonl",
            _decorate_source_rows(
                source_package.get("ftmo_blocker_rows", []),
                spec=spec,
                day=day,
                source_row_type="ftmo_blocker",
            ),
        ),
        "symbol_mapping": _append_jsonl(
            ROUTE / f"{PREFIX}_SYMBOL_MAPPING_LEDGER.jsonl",
            _decorate_source_rows(
                source_package.get("symbol_mapping_rows", []),
                spec=spec,
                day=day,
                source_row_type="symbol_mapping",
            ),
        ),
        "starvation": _append_jsonl(
            ROUTE / f"{PREFIX}_MARKET_STARVATION_LEDGER.jsonl",
            _decorate_source_rows(
                source_package.get("starvation_rows", []),
                spec=spec,
                day=day,
                source_row_type="market_starvation",
            ),
        ),
    }


def _manifest_entry(row: Mapping[str, Any], *, spec: PhaseSpec, day: str) -> dict[str, Any]:
    entry = dict(row)
    entry["route_id"] = ROUTE_ID
    entry[REPLAY_PHASE_FIELD] = spec.phase
    entry["parent_partition_id"] = spec.parent_partition_id
    entry["partition_role"] = spec.partition_role
    entry["trading_day"] = day
    return entry


def _jsonl_rows(path: Path, *, phase: str | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                continue
            if phase is not None and row.get("phase") != phase:
                continue
            rows.append(row)
    return rows


def _run_phase(
    *,
    spec: PhaseSpec,
    config: Mapping[str, Any],
    source_manifest_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    broker = SimulatedBroker()
    order_sequence = 0
    stats = _phase_stats()
    parity = _parity_counter()
    day_results: list[dict[str, Any]] = []
    for day in spec.days:
        source_package = build_source_package((day,))
        source_counts = _append_source_package_rows(source_package, spec=spec, day=day)
        source_manifest_entries.extend(
            _manifest_entry(row, spec=spec, day=day)
            for row in source_package.get("manifest_sources", [])
        )
        progress_base: dict[str, Any] = {
            "schema_version": f"{SCHEMA_PREFIX}_day_progress_v1",
            "route_id": ROUTE_ID,
            "phase": spec.phase,
            "parent_partition_id": spec.parent_partition_id,
            "partition_role": spec.partition_role,
            "trading_day": day,
            "touched_by_prior_iterative_rule_tuning": False,
            "source_package_primary_hydration_complete": source_package.get("primary_hydration_complete"),
            "missing_symbols": source_package.get("missing_symbols"),
            "requested_history_end_utc": source_package.get("requested_history_end_utc"),
            "source_counts": source_counts,
            "source_strategy": SOURCE_STRATEGY,
            "one_shot_full_tick_load_used": False,
        }
        if source_package.get("primary_hydration_complete") is not True:
            progress = {**progress_base, "status": "not_run_primary_hydration_incomplete"}
            _append_jsonl(ROUTE / f"{PREFIX}_DAY_PROGRESS_LEDGER.jsonl", [progress])
            day_results.append(progress)
            continue

        campaign = CampaignConfig(
            name=spec.campaign_name,
            phase=spec.phase,
            days=(day,),
            pending_expiry_minutes=REPAIRED_PENDING_EXPIRY_MINUTES,
            use_repaired_pending_expiry=True,
            partial_be_runner=False,
        )
        result = run_campaign(
            campaign=campaign,
            config=config,
            sources=source_package["sources"],
            broker=broker,
            starting_order_sequence=order_sequence,
        )
        order_sequence = int(result.get("selected_order_sequence") or order_sequence)
        ledgers = result["ledgers"]
        ledger_counts = _append_ledgers(ledgers)
        degradation = _degradation_rows(ledgers, spec=spec, day=day)
        _append_jsonl(ROUTE / f"{PREFIX}_DEGRADATION_REPAIR_LEDGER.jsonl", degradation)
        _record_parity(parity, ledgers)
        _update_phase_stats(stats, ledgers)
        day_summary = summarize_campaign(result, phase=spec.phase)
        progress = {
            **progress_base,
            "status": "completed",
            "ledger_counts": ledger_counts,
            "degradation_repair_rows": len(degradation),
            "day_summary": day_summary,
            "selected_order_sequence_after_day": order_sequence,
            "ending_balance_after_day": broker.account.balance,
            "max_drawdown_pct_after_day": broker.account.max_drawdown_pct,
        }
        _append_jsonl(ROUTE / f"{PREFIX}_DAY_PROGRESS_LEDGER.jsonl", [progress])
        day_results.append(progress)
        atomic_write_json(
            ROUTE / f"{PREFIX}_RERUN_SUMMARY.json",
            {
                "schema_version": f"{SCHEMA_PREFIX}_rerun_summary_v1",
                "generated_at_utc": utc_now(),
                "route_id": ROUTE_ID,
                "status": "running",
                "completed_phase": spec.phase,
                "completed_day": day,
                "day_results": day_results,
            },
        )

    phase_summary = _final_phase_summary(spec, stats, broker)
    phase_summary["packet_parity_rows"] = _parity_rows(parity)
    _append_jsonl(ROUTE / f"{PREFIX}_LIVE_REPLAY_PACKET_PARITY_LEDGER.jsonl", phase_summary["packet_parity_rows"])
    return phase_summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase",
        action="append",
        choices=[spec.phase for spec in PHASE_SPECS],
        help=f"Run only the named {PHASE_HELP_NOUN} phase. Defaults to all {PHASE_HELP_NOUN} phases.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    selected_phases = set(args.phase or [spec.phase for spec in PHASE_SPECS])
    specs = [spec for spec in PHASE_SPECS if spec.phase in selected_phases]
    _reset_outputs()
    config = load_config(REPO_ROOT / "config/agent_config.yaml")
    source_manifest_entries: list[dict[str, Any]] = []
    summaries = [
        _run_phase(spec=spec, config=config, source_manifest_entries=source_manifest_entries)
        for spec in specs
    ]
    progress_rows = _jsonl_rows(ROUTE / f"{PREFIX}_DAY_PROGRESS_LEDGER.jsonl")
    phase_statuses = {
        summary["phase"]: "completed"
        if all(
            row.get("status") == "completed"
            for row in progress_rows
            if row.get("phase") == summary["phase"]
        )
        else "incomplete"
        for summary in summaries
    }
    result = {
        "schema_version": f"{SCHEMA_PREFIX}_rerun_summary_v1",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "status": "completed" if all(status == "completed" for status in phase_statuses.values()) else "incomplete",
        "source_strategy": SOURCE_STRATEGY,
        "one_shot_full_tick_load_used": False,
        "build_source_package_call_shape": f"build_source_package((single_day,)) inside {PHASE_HELP_NOUN} phase/day loop",
        "frozen_candidate_mechanism": "generalized_calibrated_selector_v4_admission_not_exact_touched_block_lists",
        "touched_april_20_30_boundary": "development_failure_anatomy_only_not_validation",
        "phase_statuses": phase_statuses,
        "phase_summaries": summaries,
        "source_manifest": f"{PREFIX}_SOURCE_MANIFEST.json",
        "full_ledger_prefix": PREFIX,
        "no_live_broker_mutation": True,
        "no_remote_push": True,
        "no_paid_api": True,
        "summary_hash_sha256": stable_sha256(summaries),
    }
    atomic_write_json(ROUTE / f"{PREFIX}_RERUN_SUMMARY.json", result)
    atomic_write_json(
        ROUTE / f"{PREFIX}_SOURCE_MANIFEST.json",
        {
            "schema_version": f"{SCHEMA_PREFIX}_source_manifest_v1",
            "generated_at_utc": utc_now(),
            "route_id": ROUTE_ID,
            "source_strategy": SOURCE_STRATEGY,
            "one_shot_full_tick_load_used": False,
            "sources": source_manifest_entries,
            "source_count": len(source_manifest_entries),
            "missing_symbols_by_phase_day": [
                {
                    "phase": row.get("phase"),
                    "trading_day": row.get("trading_day"),
                    "missing_symbols": row.get("missing_symbols"),
                }
                for row in progress_rows
                if row.get("missing_symbols")
            ],
        },
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
