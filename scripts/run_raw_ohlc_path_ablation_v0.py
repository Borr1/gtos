#!/usr/bin/env python3
"""Run Phase 3 raw-OHLC exit-policy ablations on the same candidate stream.

V0 is deliberately narrow:

* reconstruct the raw-OHLC cohort TAKE stream with the existing no-leak adapter;
* compare fixed TP/SL, J46-J49, and lock-only path-scaling policies;
* keep reentry out of scope until lock-only behavior is understood;
* report gross R plus cost-sensitivity net R.

This is research/tooling only. It does not call AI and does not change live
trading behavior.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.analyze_raw_ohlc_replay_followups import (  # noqa: E402
    groups_for_key,
    rate_or_none,
)
from scripts.analyze_truth_layer_effective_n import effective_n_diagnostics  # noqa: E402
from scripts.analyze_truth_layer_posthoc_pbo import cscv_pbo  # noqa: E402
from scripts.build_historical_opportunity_dataset import (  # noqa: E402
    DEFAULT_MECHANICAL_MAX_HOLD_BARS,
    _load_outcome_rows,
    disable_component_side_effects,
    load_base_config,
)
from scripts.evaluate_truth_layer_methodology_readiness import compute_dsr_diagnostic  # noqa: E402
from scripts.run_raw_ohlc_prequential_replay import (  # noqa: E402
    DEFAULT_OUTPUT_ROOT,
    DEFAULT_SPEC_PATH,
    active_cohort_specs,
    build_asof_event_row,
    build_replay_events,
    decide_from_cohorts,
    git_commit_or_unknown,
    load_replay_spec,
    markdown_table,
    project_observation,
    sha256_file,
    spec_data_dirs,
    split_cohort_key,
)
from src.research_infra.dumb_baseline import MechanicalSetup  # noqa: E402


SCHEMA_VERSION = "raw_ohlc_path_ablation_v0_summary"
EVENT_SCHEMA_VERSION = "raw_ohlc_path_ablation_v0_event"
DEFAULT_REPORT_PATH = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_ARCHITECTURE_ABLATION_PATH_SCALING_V0_REPORT_2026-05-01.md"
)
DEFAULT_ABLATION_SPEC_PATH = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_ARCHITECTURE_ABLATION_SPEC_V1.json"
)
DEFAULT_ABLATION_PROTOCOL_PATH = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_ARCHITECTURE_ABLATION_AND_PATH_SCALING_PROTOCOL_2026-05-01.md"
)
RESOLVED_OUTCOMES = {"TP", "SL", "TIMEOUT", "BE_STOP", "LOCK_STOP"}
DEFAULT_COST_SCENARIOS_R = (0.0, 0.02, 0.05, 0.10)


@dataclass(frozen=True)
class LockStep:
    trigger_r: float
    floor_r: float


@dataclass(frozen=True)
class ExitPolicy:
    variant_id: str
    family: str
    description: str
    final_target_r: float | None
    time_stop_bars: int
    pending_expiry_bars: int = DEFAULT_MECHANICAL_MAX_HOLD_BARS
    lock_steps: tuple[LockStep, ...] = ()
    use_setup_tp: bool = False


@dataclass
class PathOutcome:
    variant_id: str
    outcome: str
    gross_r: float | None
    bars_to_fill: int
    bars_in_trade: int
    exit_time: str | None
    skip_reason: str | None = None
    mfe_r: float | None = None
    mae_r: float | None = None
    max_locked_floor_r: float | None = None
    locks_triggered: list[dict[str, float]] = field(default_factory=list)


@dataclass
class VariantStats:
    actions_seen: int = 0
    setup_ok: int = 0
    entries_filled: int = 0
    resolved_n: int = 0
    wins: int = 0
    gross_sum_r: float = 0.0
    gross_returns: list[float] = field(default_factory=list)
    net_returns_by_cost: dict[float, list[float]] = field(default_factory=lambda: defaultdict(list))
    outcomes: Counter[str] = field(default_factory=Counter)
    bars_in_trade: list[int] = field(default_factory=list)
    mfe_values: list[float] = field(default_factory=list)
    mae_values: list[float] = field(default_factory=list)
    locks_triggered: int = 0
    lock_then_stop: int = 0
    direct_3r_available: int = 0
    direct_6r_available: int = 0

    def add(self, outcome: PathOutcome, *, cost_scenarios: Sequence[float]) -> None:
        self.actions_seen += 1
        self.outcomes[outcome.outcome] += 1
        if outcome.outcome != "SETUP_NOT_REFINABLE":
            self.setup_ok += 1
        if outcome.outcome not in {"NO_ENTRY", "NO_DATA", "INVALID", "SAME_BAR", "SETUP_NOT_REFINABLE"}:
            self.entries_filled += 1
        if outcome.locks_triggered:
            self.locks_triggered += 1
            if outcome.outcome in {"BE_STOP", "LOCK_STOP"}:
                self.lock_then_stop += 1
        if outcome.mfe_r is not None:
            self.mfe_values.append(outcome.mfe_r)
            if outcome.mfe_r >= 3.0:
                self.direct_3r_available += 1
            if outcome.mfe_r >= 6.0:
                self.direct_6r_available += 1
        if outcome.mae_r is not None:
            self.mae_values.append(outcome.mae_r)
        if outcome.outcome not in RESOLVED_OUTCOMES or outcome.gross_r is None:
            return
        value = float(outcome.gross_r)
        self.resolved_n += 1
        self.gross_sum_r += value
        self.gross_returns.append(value)
        if value > 0:
            self.wins += 1
        self.bars_in_trade.append(int(outcome.bars_in_trade or 0))
        for cost in cost_scenarios:
            self.net_returns_by_cost[float(cost)].append(value - float(cost))


def registered_policies() -> list[ExitPolicy]:
    return [
        ExitPolicy(
            variant_id="BASE_RAW_FIXED_TP",
            family="baseline",
            description="Current raw mechanical fixed TP/SL with 96 M15-bar max hold.",
            final_target_r=None,
            time_stop_bars=DEFAULT_MECHANICAL_MAX_HOLD_BARS,
            use_setup_tp=True,
        ),
        ExitPolicy(
            variant_id="J46_J49_ONLY",
            family="j46_j49",
            description="0% partial, 3R trigger to BE, 6R final target, 12 M15-bar time stop after fill.",
            final_target_r=6.0,
            time_stop_bars=12,
            lock_steps=(LockStep(3.0, 0.0),),
        ),
        ExitPolicy(
            variant_id="PATH_LOCK_CONSERVATIVE_V0",
            family="path_lock_only",
            description="Lock-only ladder: 1.5R->0R, 2R->0.5R, 3R->1R, 6R final target.",
            final_target_r=6.0,
            time_stop_bars=12,
            lock_steps=(LockStep(1.5, 0.0), LockStep(2.0, 0.5), LockStep(3.0, 1.0)),
        ),
        ExitPolicy(
            variant_id="PATH_LOCK_HALF_GAIN_V0",
            family="path_lock_only",
            description="Lock-only ladder: 1.5R->0.5R, 2R->1R, 3R->1.5R, 6R final target.",
            final_target_r=6.0,
            time_stop_bars=12,
            lock_steps=(LockStep(1.5, 0.5), LockStep(2.0, 1.0), LockStep(3.0, 1.5)),
        ),
        ExitPolicy(
            variant_id="PATH_LOCK_EARLY_BE_V0",
            family="path_lock_only",
            description="Lock-only ladder: 1R->0R, 1.5R->0.5R, 2R->1R, 3R->1.5R, 6R final target.",
            final_target_r=6.0,
            time_stop_bars=12,
            lock_steps=(LockStep(1.0, 0.0), LockStep(1.5, 0.5), LockStep(2.0, 1.0), LockStep(3.0, 1.5)),
        ),
    ]


def run_path_ablation_v0(
    *,
    spec_path: str | Path = DEFAULT_SPEC_PATH,
    data_dirs: Sequence[str | Path] | None = None,
    start: str | datetime | None = None,
    end: str | datetime | None = None,
    max_candles_per_symbol: int | None = None,
    max_events: int | None = None,
    include_blocked_controls: bool = False,
    path_timeframe: str = "M15",
    cost_scenarios_r: Sequence[float] = DEFAULT_COST_SCENARIOS_R,
    event_log_path: str | Path | None = None,
) -> dict[str, Any]:
    spec = load_replay_spec(spec_path)
    selected_data_dirs = [Path(path) for path in (data_dirs or spec_data_dirs(spec))]
    active_cohorts = active_cohort_specs(spec, include_blocked_controls=include_blocked_controls)
    active_cohort_keys = {str(row["cohort_key"]) for row in active_cohorts}
    roles = {str(row["cohort_key"]): str(row.get("role")) for row in active_cohorts}
    blocked_cohort_keys = {
        str(cohort.get("cohort_key"))
        for cohort in spec.get("cohorts", [])
        if cohort.get("status") == "blocked_control"
    }
    symbols = sorted({split_cohort_key(str(row["cohort_key"]))[0] for row in active_cohorts})
    events, order_diagnostics = build_replay_events(
        data_dirs=selected_data_dirs,
        symbols=symbols,
        base_config=load_base_config(),
        start=start,
        end=end,
        max_candles_per_symbol=max_candles_per_symbol,
    )
    if max_events is not None:
        events = events[:max_events]

    policies = registered_policies()
    stats: dict[str, VariantStats] = {policy.variant_id: VariantStats() for policy in policies}
    group_stats: dict[tuple[str, str], VariantStats] = defaultdict(VariantStats)
    cohort_stats: dict[tuple[str, str, str], VariantStats] = defaultdict(VariantStats)
    month_returns: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    event_rows_written = 0
    take_rows_seen = 0
    setup_ok_rows = 0
    no_data_rows = 0
    path_cache: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    first_take_clock: str | None = None
    last_take_clock: str | None = None
    first_events: list[dict[str, Any]] = []

    event_handle = None
    if event_log_path is not None:
        target = Path(event_log_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        event_handle = target.open("w", encoding="utf-8", newline="\n")

    try:
        disable_component_side_effects()
        for replay_index, event in enumerate(events, start=1):
            row, _alignment, setup = build_asof_event_row(
                event=event,
                spec=spec,
                replay_index=replay_index,
            )
            observation = project_observation(row, spec)
            decision = decide_from_cohorts(
                observation,
                active_cohort_keys=active_cohort_keys,
                blocked_cohort_keys=blocked_cohort_keys,
                include_blocked_controls=include_blocked_controls,
            )
            if decision.get("action") != "TAKE":
                continue
            take_rows_seen += 1
            clock = str(row.get("candle_close_utc"))
            first_take_clock = first_take_clock or clock
            last_take_clock = clock
            key = str(observation.get("raw_cohort_key") or "")
            role = roles.get(key, "unknown")
            month = str(row.get("month") or "") or clock[:7]
            if row.get("mechanical_setup_status") == "OK" and setup is not None:
                setup_ok_rows += 1
                path_rows = _load_outcome_rows(
                    roots=selected_data_dirs,
                    symbol=event.symbol,
                    timeframe=path_timeframe,
                    cache=path_cache,
                )
            else:
                path_rows = []
            if setup is not None and not path_rows:
                no_data_rows += 1
            for policy in policies:
                outcome = (
                    resolve_policy_outcome(setup, path_rows, policy=policy)
                    if setup is not None and row.get("mechanical_setup_status") == "OK"
                    else PathOutcome(
                        variant_id=policy.variant_id,
                        outcome="SETUP_NOT_REFINABLE",
                        gross_r=None,
                        bars_to_fill=0,
                        bars_in_trade=0,
                        exit_time=None,
                        skip_reason=str(row.get("mechanical_skip_reason") or "missing_setup"),
                    )
                )
                stats[policy.variant_id].add(outcome, cost_scenarios=cost_scenarios_r)
                cohort_stats[(policy.variant_id, key, role)].add(outcome, cost_scenarios=cost_scenarios_r)
                for group in groups_for_key(key, role):
                    group_stats[(policy.variant_id, group)].add(outcome, cost_scenarios=cost_scenarios_r)
                if outcome.outcome in RESOLVED_OUTCOMES and outcome.gross_r is not None:
                    month_returns[month][policy.variant_id] += float(outcome.gross_r)
                event_record = path_event_record(
                    row=row,
                    raw_cohort_key=key,
                    role=role,
                    policy=policy,
                    outcome=outcome,
                    path_timeframe=path_timeframe,
                    cost_scenarios_r=cost_scenarios_r,
                )
                if len(first_events) < 10:
                    first_events.append(event_record)
                if event_handle is not None:
                    event_handle.write(json.dumps(event_record, sort_keys=True) + "\n")
                    event_rows_written += 1
    finally:
        if event_handle is not None:
            event_handle.close()

    cost_scenarios = [float(value) for value in cost_scenarios_r]
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "replay_spec_path": str(Path(spec_path)),
        "replay_spec_sha256": sha256_file(spec_path),
        "ablation_spec_path": DEFAULT_ABLATION_SPEC_PATH,
        "ablation_spec_sha256": sha256_file(DEFAULT_ABLATION_SPEC_PATH),
        "ablation_protocol_path": DEFAULT_ABLATION_PROTOCOL_PATH,
        "ablation_protocol_sha256": sha256_file(DEFAULT_ABLATION_PROTOCOL_PATH),
        "code_commit": git_commit_or_unknown(),
        "promotion_verdict_allowed": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "promotion_blocked_reason": "Same-dataset historical raw-OHLC exit-policy ablation.",
        "path_timeframe": path_timeframe.upper(),
        "path_timeframe_policy": "Full-corpus V0 uses one timeframe for comparability; lower-TF mixed precision is deferred.",
        "same_bar_policy": "Fill-and-exit on the same bar is unresolved; newly locked stops activate on the next bar.",
        "cost_model": {
            "unit": "R per completed round turn",
            "cost_scenarios_r": cost_scenarios,
            "actual_commission_spread_source": "not reliably available in historical OHLC; reported as sensitivity, not measured cost",
            "reentry_cost_note": "V0 has no reentries; future reentry variants must charge one additional round turn per reentry.",
        },
        "research_boundary": [
            "Research/tooling only",
            "No live trading logic changes",
            "No prompt edits",
            "No parameter optimization",
            "No paid AI/API calls",
        ],
        "start": str(start) if start else None,
        "end": str(end) if end else None,
        "max_candles_per_symbol": max_candles_per_symbol,
        "max_events": max_events,
        "source_scope": source_scope(start, end, max_candles_per_symbol, max_events),
        "include_blocked_controls": include_blocked_controls,
        "symbols": symbols,
        "active_cohorts": active_cohorts,
        "rows_replayed": len(events),
        "take_rows_seen": take_rows_seen,
        "setup_ok_rows": setup_ok_rows,
        "no_data_rows": no_data_rows,
        "first_take_clock": first_take_clock,
        "last_take_clock": last_take_clock,
        "input_order_diagnostics": order_diagnostics,
        "policies": [policy_row(policy) for policy in policies],
        "variant_summary": [
            variant_summary_row(policy, stats[policy.variant_id], cost_scenarios=cost_scenarios)
            for policy in policies
        ],
        "group_summary": build_group_rows(policies, group_stats, cost_scenarios=cost_scenarios),
        "cohort_summary": build_cohort_rows(policies, cohort_stats, cost_scenarios=cost_scenarios),
        "pbo_diagnostic": pbo_diagnostic(month_returns, [policy.variant_id for policy in policies]),
        "effective_n_diagnostic": effective_n_diagnostic(month_returns, [policy.variant_id for policy in policies]),
        "first_events": first_events,
        "event_log_path": str(event_log_path) if event_log_path else None,
        "event_rows_written": event_rows_written,
    }
    summary["synthesis"] = synthesize(summary)
    summary["ambiguity_ledger"] = ambiguity_ledger(summary)
    summary["next_steps"] = next_steps(summary)
    return summary


def resolve_policy_outcome(
    setup: MechanicalSetup | None,
    rows: Sequence[Mapping[str, Any]],
    *,
    policy: ExitPolicy,
) -> PathOutcome:
    if setup is None:
        return PathOutcome(policy.variant_id, "SETUP_NOT_REFINABLE", None, 0, 0, None, "missing_setup")
    if setup.skip_reason is not None:
        return PathOutcome(policy.variant_id, "INVALID", None, 0, 0, None, setup.skip_reason)
    sl_dist = abs(float(setup.entry) - float(setup.sl))
    if sl_dist <= 0:
        return PathOutcome(policy.variant_id, "INVALID", None, 0, 0, None, "DEGENERATE_SL")
    if not rows:
        return PathOutcome(policy.variant_id, "NO_DATA", None, 0, 0, None, "OHLCV_MISSING")

    start_idx = first_row_after(rows, setup.candle_close_time)
    walk = list(rows[start_idx : start_idx + policy.pending_expiry_bars])
    if not walk:
        return PathOutcome(policy.variant_id, "NO_DATA", None, 0, 0, None, "NO_FUTURE_BARS")

    final_target_r = float(setup.rr if policy.use_setup_tp else policy.final_target_r or setup.rr)
    active_stop_r = -1.0
    pending_stop_r = active_stop_r
    locks_triggered: list[dict[str, float]] = []
    triggered_levels: set[float] = set()
    filled = False
    bars_to_fill = 0
    bars_in_trade = 0
    last_close_r: float | None = None
    last_time: str | None = None
    mfe_r: float | None = None
    mae_r: float | None = None

    for bar in walk:
        high, low, close = bar_prices(bar)
        if high is None:
            continue
        last_time = str(bar.get("time")) if bar.get("time") is not None else None

        if not filled:
            bars_to_fill += 1
            if not fill_hit(setup, high=high, low=low):
                continue
            same_bar_exit = same_bar_exit_after_fill(
                setup,
                high=high,
                low=low,
                final_target_r=final_target_r,
                lock_steps=policy.lock_steps,
            )
            if same_bar_exit:
                return PathOutcome(
                    policy.variant_id,
                    "SAME_BAR",
                    None,
                    bars_to_fill,
                    bars_in_trade=bars_to_fill,
                    exit_time=last_time,
                    skip_reason="FILL_AND_PATH_EVENT_SAME_BAR",
                )
            filled = True
            continue

        bars_in_trade += 1
        active_stop_r = pending_stop_r
        favorable_r, adverse_r, close_r = bar_r_extremes(setup, high=high, low=low, close=close)
        mfe_r = favorable_r if mfe_r is None else max(mfe_r, favorable_r)
        mae_r = adverse_r if mae_r is None else min(mae_r, adverse_r)
        last_close_r = close_r

        if adverse_r <= active_stop_r:
            outcome_name = "SL" if active_stop_r < 0 else ("BE_STOP" if abs(active_stop_r) < 1e-12 else "LOCK_STOP")
            return PathOutcome(
                policy.variant_id,
                outcome_name,
                round(active_stop_r, 6),
                bars_to_fill,
                bars_in_trade,
                last_time,
                mfe_r=mfe_r,
                mae_r=mae_r,
                max_locked_floor_r=max([step["floor_r"] for step in locks_triggered], default=None),
                locks_triggered=locks_triggered,
            )
        if favorable_r >= final_target_r:
            return PathOutcome(
                policy.variant_id,
                "TP",
                round(final_target_r, 6),
                bars_to_fill,
                bars_in_trade,
                last_time,
                mfe_r=mfe_r,
                mae_r=mae_r,
                max_locked_floor_r=max([step["floor_r"] for step in locks_triggered], default=None),
                locks_triggered=locks_triggered,
            )

        for step in sorted(policy.lock_steps, key=lambda item: item.trigger_r):
            if step.trigger_r in triggered_levels:
                continue
            if favorable_r >= step.trigger_r:
                triggered_levels.add(step.trigger_r)
                if step.floor_r > pending_stop_r:
                    pending_stop_r = step.floor_r
                locks_triggered.append({"trigger_r": step.trigger_r, "floor_r": step.floor_r})

        if bars_in_trade >= policy.time_stop_bars:
            return PathOutcome(
                policy.variant_id,
                "TIMEOUT",
                round(float(last_close_r), 6) if last_close_r is not None else None,
                bars_to_fill,
                bars_in_trade,
                last_time,
                mfe_r=mfe_r,
                mae_r=mae_r,
                max_locked_floor_r=max([step["floor_r"] for step in locks_triggered], default=None),
                locks_triggered=locks_triggered,
            )

    if not filled:
        return PathOutcome(policy.variant_id, "NO_ENTRY", None, bars_to_fill, 0, last_time, "NEVER_FILLED")
    return PathOutcome(
        policy.variant_id,
        "TIMEOUT",
        round(float(last_close_r), 6) if last_close_r is not None else None,
        bars_to_fill,
        bars_in_trade,
        last_time,
        mfe_r=mfe_r,
        mae_r=mae_r,
        max_locked_floor_r=max([step["floor_r"] for step in locks_triggered], default=None),
        locks_triggered=locks_triggered,
    )


def first_row_after(rows: Sequence[Mapping[str, Any]], cutoff: datetime) -> int:
    lo, hi = 0, len(rows)
    while lo < hi:
        mid = (lo + hi) // 2
        value = rows[mid].get("time")
        if isinstance(value, datetime) and value <= cutoff:
            lo = mid + 1
        else:
            hi = mid
    return lo


def bar_prices(bar: Mapping[str, Any]) -> tuple[float | None, float | None, float | None]:
    try:
        return float(bar["high"]), float(bar["low"]), float(bar["close"])
    except (KeyError, TypeError, ValueError):
        return None, None, None


def fill_hit(setup: MechanicalSetup, *, high: float, low: float) -> bool:
    return low <= setup.entry if setup.side == "LONG" else high >= setup.entry


def same_bar_exit_after_fill(
    setup: MechanicalSetup,
    *,
    high: float,
    low: float,
    final_target_r: float,
    lock_steps: Sequence[LockStep],
) -> bool:
    favorable_r, adverse_r, _ = bar_r_extremes(setup, high=high, low=low, close=setup.entry)
    if adverse_r <= -1.0 or favorable_r >= final_target_r:
        return True
    return any(favorable_r >= step.trigger_r for step in lock_steps)


def bar_r_extremes(
    setup: MechanicalSetup,
    *,
    high: float,
    low: float,
    close: float,
) -> tuple[float, float, float]:
    sl_dist = abs(setup.entry - setup.sl)
    if setup.side == "LONG":
        favorable = (high - setup.entry) / sl_dist
        adverse = (low - setup.entry) / sl_dist
        close_r = (close - setup.entry) / sl_dist
    else:
        favorable = (setup.entry - low) / sl_dist
        adverse = (setup.entry - high) / sl_dist
        close_r = (setup.entry - close) / sl_dist
    return float(favorable), float(adverse), float(close_r)


def variant_summary_row(policy: ExitPolicy, stats: VariantStats, *, cost_scenarios: Sequence[float]) -> dict[str, Any]:
    row = {
        "variant_id": policy.variant_id,
        "family": policy.family,
        "actions_seen": stats.actions_seen,
        "setup_ok": stats.setup_ok,
        "entries_filled": stats.entries_filled,
        "resolved_n": stats.resolved_n,
        "gross_sum_r": round(stats.gross_sum_r, 6),
        "gross_mean_r": round(stats.gross_sum_r / stats.resolved_n, 6) if stats.resolved_n else None,
        "gross_median_r": round(float(np.median(stats.gross_returns)), 6) if stats.gross_returns else None,
        "gross_win_rate": rate_or_none(stats.wins, stats.resolved_n),
        "avg_bars_in_trade": round(sum(stats.bars_in_trade) / len(stats.bars_in_trade), 6)
        if stats.bars_in_trade
        else None,
        "lock_trigger_rate": rate_or_none(stats.locks_triggered, stats.entries_filled),
        "lock_then_stop_rate": rate_or_none(stats.lock_then_stop, stats.entries_filled),
        "direct_3r_available_rate": rate_or_none(stats.direct_3r_available, len(stats.mfe_values)),
        "direct_6r_available_rate": rate_or_none(stats.direct_6r_available, len(stats.mfe_values)),
        "mfe_p50": quantile(stats.mfe_values, 0.50),
        "mfe_p75": quantile(stats.mfe_values, 0.75),
        "mfe_p90": quantile(stats.mfe_values, 0.90),
        "mae_p10": quantile(stats.mae_values, 0.10),
        "outcomes": dict(sorted(stats.outcomes.items())),
        "same_dataset_dsr_p_gross": compute_dsr_diagnostic(stats.gross_returns, n_trials=200).get("dsr_corrected_p"),
    }
    for cost in cost_scenarios:
        returns = stats.net_returns_by_cost.get(float(cost), [])
        row[f"net_mean_r_cost_{cost:g}"] = round(sum(returns) / len(returns), 6) if returns else None
        row[f"net_sum_r_cost_{cost:g}"] = round(sum(returns), 6) if returns else None
        row[f"net_max_drawdown_r_cost_{cost:g}"] = max_drawdown(returns)
    return row


def build_group_rows(
    policies: Sequence[ExitPolicy],
    group_stats: Mapping[tuple[str, str], VariantStats],
    *,
    cost_scenarios: Sequence[float],
) -> list[dict[str, Any]]:
    groups = [
        "all_enabled",
        "all_excluding_gbpusd_control",
        "target_cohorts",
        "primary_controlled_family",
        "cleared_non_primary_targets",
        "negative_controls",
        "blocked_dominance_controls",
    ]
    rows = []
    report_cost = 0.05 if 0.05 in set(cost_scenarios) else float(cost_scenarios[0])
    for policy in policies:
        for group in groups:
            state = group_stats.get((policy.variant_id, group), VariantStats())
            returns = state.net_returns_by_cost.get(report_cost, [])
            rows.append(
                {
                    "variant_id": policy.variant_id,
                    "group": group,
                    "resolved_n": state.resolved_n,
                    "gross_mean_r": round(state.gross_sum_r / state.resolved_n, 6) if state.resolved_n else None,
                    "net_mean_r_cost_0.05": round(sum(returns) / len(returns), 6) if returns else None,
                    "gross_sum_r": round(state.gross_sum_r, 6),
                    "net_sum_r_cost_0.05": round(sum(returns), 6) if returns else None,
                    "gross_win_rate": rate_or_none(state.wins, state.resolved_n),
                    "lock_trigger_rate": rate_or_none(state.locks_triggered, state.entries_filled),
                    "outcomes": dict(sorted(state.outcomes.items())),
                }
            )
    return rows


def build_cohort_rows(
    policies: Sequence[ExitPolicy],
    cohort_stats: Mapping[tuple[str, str, str], VariantStats],
    *,
    cost_scenarios: Sequence[float],
) -> list[dict[str, Any]]:
    rows = []
    report_cost = 0.05 if 0.05 in set(cost_scenarios) else float(cost_scenarios[0])
    cohorts = sorted({(cohort_key, role) for _variant_id, cohort_key, role in cohort_stats})
    for policy in policies:
        for cohort_key, role in cohorts:
            state = cohort_stats.get((policy.variant_id, cohort_key, role), VariantStats())
            returns = state.net_returns_by_cost.get(report_cost, [])
            rows.append(
                {
                    "variant_id": policy.variant_id,
                    "cohort_key": cohort_key,
                    "role": role,
                    "resolved_n": state.resolved_n,
                    "gross_mean_r": round(state.gross_sum_r / state.resolved_n, 6) if state.resolved_n else None,
                    "net_mean_r_cost_0.05": round(sum(returns) / len(returns), 6) if returns else None,
                    "gross_sum_r": round(state.gross_sum_r, 6),
                    "net_sum_r_cost_0.05": round(sum(returns), 6) if returns else None,
                    "gross_win_rate": rate_or_none(state.wins, state.resolved_n),
                    "lock_trigger_rate": rate_or_none(state.locks_triggered, state.entries_filled),
                    "same_bar": state.outcomes.get("SAME_BAR", 0),
                    "outcomes": dict(sorted(state.outcomes.items())),
                }
            )
    return rows


def pbo_diagnostic(month_returns: Mapping[str, Mapping[str, float]], variants: Sequence[str]) -> dict[str, Any]:
    periods = sorted(month_returns)
    matrix = [
        [float((month_returns.get(period) or {}).get(variant) or 0.0) for variant in variants]
        for period in periods
    ]
    pbo, diagnostics = cscv_pbo(matrix)
    return {
        "promotion_usable": False,
        "period_unit": "calendar_month",
        "variant_count": len(variants),
        "period_count": len(periods),
        "pbo": round(pbo, 6) if pbo is not None else None,
        "status": diagnostics.get("status"),
        "diagnostics": diagnostics,
    }


def effective_n_diagnostic(month_returns: Mapping[str, Mapping[str, float]], variants: Sequence[str]) -> dict[str, Any]:
    periods = sorted(month_returns)
    matrix = np.array(
        [
            [float((month_returns.get(period) or {}).get(variant) or 0.0) for variant in variants]
            for period in periods
        ],
        dtype=float,
    )
    return {
        "promotion_usable": False,
        "period_unit": "calendar_month",
        "exit_policy_effective_n": effective_n_diagnostics(matrix, candidate_keys=list(variants), periods=periods),
    }


def policy_row(policy: ExitPolicy) -> dict[str, Any]:
    return {
        "variant_id": policy.variant_id,
        "family": policy.family,
        "description": policy.description,
        "final_target_r": policy.final_target_r,
        "time_stop_bars": policy.time_stop_bars,
        "pending_expiry_bars": policy.pending_expiry_bars,
        "use_setup_tp": policy.use_setup_tp,
        "lock_steps": [step.__dict__ for step in policy.lock_steps],
    }


def path_event_record(
    *,
    row: Mapping[str, Any],
    raw_cohort_key: str,
    role: str,
    policy: ExitPolicy,
    outcome: PathOutcome,
    path_timeframe: str,
    cost_scenarios_r: Sequence[float],
) -> dict[str, Any]:
    return {
        "schema_version": EVENT_SCHEMA_VERSION,
        "event_key": row.get("event_key"),
        "candle_close_utc": row.get("candle_close_utc"),
        "symbol": row.get("symbol"),
        "session": row.get("session"),
        "raw_cohort_key": raw_cohort_key,
        "role": role,
        "variant_id": policy.variant_id,
        "path_timeframe": path_timeframe.upper(),
        "mechanical_side": row.get("mechanical_side"),
        "mechanical_entry": row.get("mechanical_entry"),
        "mechanical_sl": row.get("mechanical_sl"),
        "mechanical_tp": row.get("mechanical_tp"),
        "outcome": outcome.outcome,
        "gross_r": outcome.gross_r,
        "net_r_by_cost": {
            f"{float(cost):g}": round(float(outcome.gross_r) - float(cost), 6)
            if outcome.gross_r is not None and outcome.outcome in RESOLVED_OUTCOMES
            else None
            for cost in cost_scenarios_r
        },
        "bars_to_fill": outcome.bars_to_fill,
        "bars_in_trade": outcome.bars_in_trade,
        "exit_time": outcome.exit_time,
        "mfe_r": outcome.mfe_r,
        "mae_r": outcome.mae_r,
        "max_locked_floor_r": outcome.max_locked_floor_r,
        "locks_triggered": outcome.locks_triggered,
        "skip_reason": outcome.skip_reason,
    }


def synthesize(summary: Mapping[str, Any]) -> list[dict[str, str]]:
    rows = list(summary.get("variant_summary") or [])
    if not rows:
        return []
    by_variant = {str(row.get("variant_id")): row for row in rows}
    best_gross = max(rows, key=lambda row: float(row.get("gross_mean_r") or -999.0))
    best_net = max(rows, key=lambda row: float(row.get("net_mean_r_cost_0.05") or -999.0))
    j46 = by_variant.get("J46_J49_ONLY", {})
    best_lock = max(
        [row for row in rows if str(row.get("variant_id", "")).startswith("PATH_LOCK")],
        key=lambda row: float(row.get("net_mean_r_cost_0.05") or -999.0),
        default={},
    )
    delta = None
    if best_lock and j46:
        delta = round(float(best_lock.get("net_mean_r_cost_0.05") or 0.0) - float(j46.get("net_mean_r_cost_0.05") or 0.0), 6)
    best_drawdown = max(
        rows,
        key=lambda row: float(row.get("net_max_drawdown_r_cost_0.05") or -999.0),
        default={},
    )
    target_delta = group_delta(summary, "target_cohorts", lock_prefix="PATH_LOCK", baseline_variant="J46_J49_ONLY")
    primary_delta = group_delta(summary, "primary_controlled_family", lock_prefix="PATH_LOCK", baseline_variant="J46_J49_ONLY")
    cleared_delta = group_delta(summary, "cleared_non_primary_targets", lock_prefix="PATH_LOCK", baseline_variant="J46_J49_ONLY")
    same_bar_worst = max(rows, key=lambda row: int((row.get("outcomes") or {}).get("SAME_BAR", 0)), default={})
    return [
        {
            "question": "Which variant leads on gross mean R?",
            "answer": f"{best_gross.get('variant_id')} with gross_mean_r={best_gross.get('gross_mean_r')}.",
        },
        {
            "question": "Which variant leads after a 0.05R round-turn cost sensitivity?",
            "answer": f"{best_net.get('variant_id')} with net_mean_r_cost_0.05={best_net.get('net_mean_r_cost_0.05')}.",
        },
        {
            "question": "Did lock-only V0 beat J46-J49 in this diagnostic?",
            "answer": (
                f"Best lock-only net-minus-J46 at 0.05R cost = {delta}. "
                "This is same-dataset diagnostic evidence only."
            ),
        },
        {
            "question": "What was the main tradeoff?",
            "answer": (
                f"{best_drawdown.get('variant_id')} had the shallowest reported 0.05R-cost max drawdown "
                f"({best_drawdown.get('net_max_drawdown_r_cost_0.05')}R), while J46-J49 kept the best mean R. "
                "The lock-only family improved some win-rate/median behavior but did not beat J46-J49 overall."
            ),
        },
        {
            "question": "Where did lock-only look most interesting?",
            "answer": (
                f"Target-family best-lock minus J46 at 0.05R cost = {target_delta}; "
                f"primary-family delta = {primary_delta}; cleared-non-primary delta = {cleared_delta}. "
                "This suggests the lock ladder may be cohort-sensitive, not universally better."
            ),
        },
        {
            "question": "What was the biggest unresolved measurement issue?",
            "answer": (
                f"{same_bar_worst.get('variant_id')} created the most same-bar unresolved cases "
                f"({(same_bar_worst.get('outcomes') or {}).get('SAME_BAR', 0)}). "
                "That keeps lower-timeframe path refinement on the critical path before reentry is trusted."
            ),
        },
        {
            "question": "Does this promote an exit policy?",
            "answer": "No. This is same-dataset historical ablation and remains NO_PROMOTION_VERDICT.",
        },
    ]


def group_delta(
    summary: Mapping[str, Any],
    group: str,
    *,
    lock_prefix: str,
    baseline_variant: str,
) -> float | None:
    rows = [
        row
        for row in (summary.get("group_summary") or [])
        if row.get("group") == group and row.get("net_mean_r_cost_0.05") is not None
    ]
    baseline = next((row for row in rows if row.get("variant_id") == baseline_variant), None)
    locks = [row for row in rows if str(row.get("variant_id", "")).startswith(lock_prefix)]
    if baseline is None or not locks:
        return None
    best_lock = max(locks, key=lambda row: float(row.get("net_mean_r_cost_0.05") or -999.0))
    return round(
        float(best_lock.get("net_mean_r_cost_0.05") or 0.0)
        - float(baseline.get("net_mean_r_cost_0.05") or 0.0),
        6,
    )


def ambiguity_ledger(summary: Mapping[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "item": "Cost model",
            "status": "SENSITIVITY_NOT_MEASURED_COST",
            "detail": "Historical OHLC does not contain reliable commission/spread/slippage. Report uses R-cost sensitivity.",
        },
        {
            "item": "Lower-timeframe execution",
            "status": "M15_V0_ONLY",
            "detail": "Full-corpus V0 uses M15 for comparability; M1/M5 refinement is a later precision lane because coverage is incomplete before late 2024/2026.",
        },
        {
            "item": "Reentry",
            "status": "INTENTIONALLY_BLOCKED",
            "detail": "No reentry is tested until lock-only proves value and incremental-risk accounting is implemented.",
        },
        {
            "item": "L2 attribution",
            "status": "NOT_IMPLEMENTED_IN_V0",
            "detail": "Requires deterministic L2 reconstruction on the pre-L2 candidate stream.",
        },
        {
            "item": "Promotion",
            "status": "BLOCKED_BY_DESIGN",
            "detail": str(summary.get("promotion_blocked_reason")),
        },
    ]


def next_steps(_summary: Mapping[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "rank": "1",
            "next_step": "Inspect V0 lock-only result versus J46-J49",
            "reason": "Only continue to structural/liquidity or reentry policies if lock-only has a robust advantage or useful drawdown reduction.",
        },
        {
            "rank": "2",
            "next_step": "Add M5/M1 refinement lane for post-coverage subsets",
            "reason": "Lower-timeframe ordering is needed before reentry decisions are trusted.",
        },
        {
            "rank": "3",
            "next_step": "Implement deterministic L2 reconstruction",
            "reason": "Needed for with/without architecture attribution.",
        },
    ]


def source_scope(start: Any, end: Any, max_candles_per_symbol: Any, max_events: Any) -> str:
    if start is None and end is None and max_candles_per_symbol is None and max_events is None:
        return "FULL_AVAILABLE_CORPUS"
    return "BOUNDED_DIAGNOSTIC"


def quantile(values: Sequence[float], q: float) -> float | None:
    if not values:
        return None
    return round(float(np.quantile(values, q)), 6)


def max_drawdown(returns: Sequence[float]) -> float | None:
    if not returns:
        return None
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for value in returns:
        equity += float(value)
        peak = max(peak, equity)
        max_dd = min(max_dd, equity - peak)
    return round(max_dd, 6)


def render_report(summary: Mapping[str, Any]) -> str:
    pbo = summary.get("pbo_diagnostic") or {}
    eff = (summary.get("effective_n_diagnostic") or {}).get("exit_policy_effective_n") or {}
    lines = [
        "# Phase 3 Raw-OHLC Architecture Ablation And Path-Scaling V0",
        "",
        f"**Created UTC:** {summary.get('created_at_utc')}",
        f"**Replay spec:** `{summary.get('replay_spec_path') or summary.get('spec_path')}`",
        f"**Ablation spec:** `{summary.get('ablation_spec_path') or DEFAULT_ABLATION_SPEC_PATH}`",
        f"**Ablation protocol:** `{summary.get('ablation_protocol_path') or DEFAULT_ABLATION_PROTOCOL_PATH}`",
        f"**Promotion verdict:** `{summary.get('promotion_verdict')}`",
        "",
        "## Boundary",
        "",
        "- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.",
        "- V0 uses the same raw-OHLC no-leak candidate reconstruction as the prequential replay.",
        "- Outcomes are attached only after the cohort decision is locked.",
        "- Costs are reported as R-per-round-turn sensitivity because reliable historical commission/spread/slippage is not present in OHLC.",
        "- Reentry and L2-on/off attribution are intentionally blocked in V0.",
        "",
        "## Run Scope",
        "",
        markdown_table(
            [
                {
                    "source_scope": summary.get("source_scope"),
                    "rows_replayed": summary.get("rows_replayed"),
                    "take_rows_seen": summary.get("take_rows_seen"),
                    "setup_ok_rows": summary.get("setup_ok_rows"),
                    "path_timeframe": summary.get("path_timeframe"),
                    "include_blocked_controls": summary.get("include_blocked_controls"),
                    "first_take_clock": summary.get("first_take_clock"),
                    "last_take_clock": summary.get("last_take_clock"),
                }
            ]
        ),
        "",
        "## Cost Model",
        "",
        markdown_table([summary.get("cost_model") or {}]),
        "",
        "## Policies",
        "",
        markdown_table(summary.get("policies") or []),
        "",
        "## Direct Answers",
        "",
        markdown_table(summary.get("synthesis") or []),
        "",
        "## Variant Summary",
        "",
        markdown_table(summary.get("variant_summary") or []),
        "",
        "## Group Summary",
        "",
        markdown_table(summary.get("group_summary") or []),
        "",
        "## Cohort Summary",
        "",
        markdown_table(summary.get("cohort_summary") or []),
        "",
        "## Methodology Diagnostics",
        "",
        markdown_table(
            [
                {
                    "exit_policy_pbo": pbo.get("pbo"),
                    "pbo_status": pbo.get("status"),
                    "pbo_promotion_usable": pbo.get("promotion_usable"),
                    "exit_policy_effective_N": eff.get("effective_n"),
                    "effective_N_promotion_usable": (summary.get("effective_n_diagnostic") or {}).get("promotion_usable"),
                }
            ]
        ),
        "",
        "## Ambiguity Ledger",
        "",
        markdown_table(summary.get("ambiguity_ledger") or []),
        "",
        "## Next Steps",
        "",
        markdown_table(summary.get("next_steps") or []),
        "",
        "## Synthesis",
        "",
        "- This report is the first V0 measurement of J46-J49 versus lock-only path scaling on the same reconstructed raw-OHLC stream.",
        "- The result should be read as an engineering diagnostic, not as a promotion verdict.",
        "- If lock-only improves a specific cohort's return/drawdown/cost tradeoff, the next lane must pre-register that cohort-specific question before lower-timeframe refinement or risk-budgeted reentry.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(
    summary: Mapping[str, Any],
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    report_path: str | Path = DEFAULT_REPORT_PATH,
) -> tuple[Path, Path]:
    output_dir = Path(output_root) / "path_ablation_v0"
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_path = output_dir / f"raw_ohlc_path_ablation_v0_{stamp}.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    report = Path(report_path)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(summary), encoding="utf-8")
    return summary_path, report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", default=DEFAULT_SPEC_PATH)
    parser.add_argument("--data-dir", action="append", dest="data_dirs")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--max-candles-per-symbol", type=int)
    parser.add_argument("--max-events", type=int)
    parser.add_argument("--include-blocked-controls", action="store_true")
    parser.add_argument("--path-timeframe", default="M15", choices=["M15", "M5", "M1"])
    parser.add_argument("--cost-r", action="append", type=float, dest="cost_scenarios")
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    event_log_path = None
    if args.write:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        event_log_path = (
            Path(args.output_root)
            / "path_ablation_v0"
            / f"raw_ohlc_path_ablation_v0_events_{stamp}.jsonl"
        )
    summary = run_path_ablation_v0(
        spec_path=args.spec,
        data_dirs=args.data_dirs,
        start=args.start,
        end=args.end,
        max_candles_per_symbol=args.max_candles_per_symbol,
        max_events=args.max_events,
        include_blocked_controls=args.include_blocked_controls,
        path_timeframe=args.path_timeframe,
        cost_scenarios_r=args.cost_scenarios or DEFAULT_COST_SCENARIOS_R,
        event_log_path=event_log_path,
    )
    if args.write:
        output_summary, report = write_outputs(
            summary,
            output_root=args.output_root,
            report_path=args.report_path,
        )
        summary = dict(summary)
        summary["output_summary"] = str(output_summary)
        summary["report_path"] = str(report)
    if args.quiet:
        best = max(summary.get("variant_summary") or [], key=lambda row: float(row.get("net_mean_r_cost_0.05") or -999.0), default={})
        print(
            json.dumps(
                {
                    "promotion_verdict": summary.get("promotion_verdict"),
                    "source_scope": summary.get("source_scope"),
                    "path_timeframe": summary.get("path_timeframe"),
                    "take_rows_seen": summary.get("take_rows_seen"),
                    "best_net_cost_0.05": best.get("variant_id"),
                    "best_net_mean_r_cost_0.05": best.get("net_mean_r_cost_0.05"),
                    "output_summary": summary.get("output_summary"),
                    "report_path": summary.get("report_path"),
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
