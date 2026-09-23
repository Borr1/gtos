#!/usr/bin/env python3
"""Run Phase 3 raw-OHLC path ablation V1 with MTF path resolution.

V1 is measurement infrastructure only. It reuses the V0 raw-OHLC TAKE stream
and frozen exit policies, then compares V0 M15-only outcomes with a path
resolver that prefers M1, falls back to M5, then falls back to M15.

It does not call AI and does not change live trading behavior.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.analyze_raw_ohlc_replay_followups import groups_for_key, rate_or_none  # noqa: E402
from scripts.build_external_feed_validation_dataset import TIMEFRAME_MINUTES  # noqa: E402
from scripts.build_historical_opportunity_dataset import (  # noqa: E402
    DEFAULT_MECHANICAL_MAX_HOLD_BARS,
    _load_outcome_rows,
    disable_component_side_effects,
    load_base_config,
)
from scripts.run_raw_ohlc_path_ablation_v0 import (  # noqa: E402
    DEFAULT_ABLATION_SPEC_PATH,
    DEFAULT_COST_SCENARIOS_R,
    RESOLVED_OUTCOMES,
    ExitPolicy,
    LockStep,
    PathOutcome,
    VariantStats,
    bar_prices,
    bar_r_extremes,
    build_cohort_rows,
    build_group_rows,
    effective_n_diagnostic,
    fill_hit,
    first_row_after,
    group_delta,
    pbo_diagnostic,
    policy_row,
    registered_policies,
    resolve_policy_outcome,
    same_bar_exit_after_fill,
    source_scope,
    variant_summary_row,
)
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


SCHEMA_VERSION = "raw_ohlc_path_ablation_v1_mtf_summary"
EVENT_SCHEMA_VERSION = "raw_ohlc_path_ablation_v1_mtf_event"
DEFAULT_REPORT_PATH = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V1_MTF_REPORT_2026-05-02.md"
)
DEFAULT_V1_SPEC_PATH = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V1_MTF_SPEC_V1.json"
)
DEFAULT_V1_PROTOCOL_PATH = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V1_MTF_PROTOCOL_2026-05-02.md"
)
DEFAULT_V0_REPORT_PATH = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_ARCHITECTURE_ABLATION_PATH_SCALING_V0_REPORT_2026-05-01.md"
)
M15_MINUTES = TIMEFRAME_MINUTES["M15"]
LOWER_TF_HIERARCHY = ("M1", "M5")
PATH_TF_HIERARCHY = ("M1", "M5", "M15")


@dataclass
class PathWindow:
    selected_timeframe: str
    selected_rows: list[Mapping[str, Any]]
    fallback_reason: str | None
    row_counts: dict[str, int]
    first_close: dict[str, str | None]
    last_close: dict[str, str | None]
    start_violations: int = 0


@dataclass
class MtfPathOutcome:
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
    selected_timeframe: str = "M15"
    fallback_reason: str | None = None
    path_rows_to_fill: int = 0
    path_rows_in_trade: int = 0
    lower_tf_row_counts: dict[str, int] = field(default_factory=dict)


@dataclass
class CoverageStats:
    setup_windows: int = 0
    m1_available_windows: int = 0
    m1_available_rows: int = 0
    m5_available_windows: int = 0
    m5_available_rows: int = 0
    m15_available_windows: int = 0
    m15_available_rows: int = 0
    m15_fallback_windows: int = 0
    start_violations: int = 0
    selected_timeframes: Counter[str] = field(default_factory=Counter)

    def add(self, window: PathWindow) -> None:
        self.setup_windows += 1
        m1_count = int(window.row_counts.get("M1") or 0)
        m5_count = int(window.row_counts.get("M5") or 0)
        m15_count = int(window.row_counts.get("M15") or 0)
        if m1_count:
            self.m1_available_windows += 1
            self.m1_available_rows += m1_count
        if m5_count:
            self.m5_available_windows += 1
            self.m5_available_rows += m5_count
        if m15_count:
            self.m15_available_windows += 1
            self.m15_available_rows += m15_count
        if window.selected_timeframe == "M15":
            self.m15_fallback_windows += 1
        self.start_violations += int(window.start_violations)
        self.selected_timeframes[window.selected_timeframe] += 1


@dataclass
class VariantComparisonStats:
    actions_seen: int = 0
    v0_resolved_n: int = 0
    v1_resolved_n: int = 0
    both_resolved_n: int = 0
    v0_same_bar: int = 0
    v1_same_bar: int = 0
    same_bar_resolved_by_mtf: int = 0
    same_bar_still_unresolved: int = 0
    v1_new_same_bar: int = 0
    outcome_changed: int = 0
    gross_delta_sum: float = 0.0
    gross_deltas: list[float] = field(default_factory=list)
    selected_timeframes: Counter[str] = field(default_factory=Counter)

    def add(self, *, v0: PathOutcome, v1: MtfPathOutcome) -> None:
        self.actions_seen += 1
        self.selected_timeframes[v1.selected_timeframe] += 1
        v0_resolved = v0.outcome in RESOLVED_OUTCOMES and v0.gross_r is not None
        v1_resolved = v1.outcome in RESOLVED_OUTCOMES and v1.gross_r is not None
        if v0_resolved:
            self.v0_resolved_n += 1
        if v1_resolved:
            self.v1_resolved_n += 1
        if v0.outcome == "SAME_BAR":
            self.v0_same_bar += 1
            if v1_resolved:
                self.same_bar_resolved_by_mtf += 1
            elif v1.outcome == "SAME_BAR":
                self.same_bar_still_unresolved += 1
        if v1.outcome == "SAME_BAR":
            self.v1_same_bar += 1
            if v0.outcome != "SAME_BAR":
                self.v1_new_same_bar += 1
        if outcome_signature(v0) != outcome_signature(v1):
            self.outcome_changed += 1
        if v0_resolved and v1_resolved:
            delta = float(v1.gross_r) - float(v0.gross_r)
            self.both_resolved_n += 1
            self.gross_delta_sum += delta
            self.gross_deltas.append(delta)


def run_path_ablation_v1_mtf(
    *,
    spec_path: str | Path = DEFAULT_SPEC_PATH,
    data_dirs: Sequence[str | Path] | None = None,
    start: str | datetime | None = None,
    end: str | datetime | None = None,
    max_candles_per_symbol: int | None = None,
    max_events: int | None = None,
    include_blocked_controls: bool = False,
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
    cost_scenarios = [float(value) for value in cost_scenarios_r]
    v0_stats: dict[str, VariantStats] = {policy.variant_id: VariantStats() for policy in policies}
    v1_stats: dict[str, VariantStats] = {policy.variant_id: VariantStats() for policy in policies}
    v0_group_stats: dict[tuple[str, str], VariantStats] = defaultdict(VariantStats)
    v1_group_stats: dict[tuple[str, str], VariantStats] = defaultdict(VariantStats)
    v0_cohort_stats: dict[tuple[str, str, str], VariantStats] = defaultdict(VariantStats)
    v1_cohort_stats: dict[tuple[str, str, str], VariantStats] = defaultdict(VariantStats)
    comparison_stats: dict[str, VariantComparisonStats] = {
        policy.variant_id: VariantComparisonStats() for policy in policies
    }
    coverage = CoverageStats()
    month_returns: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    path_cache: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    first_events: list[dict[str, Any]] = []
    event_rows_written = 0
    take_rows_seen = 0
    setup_ok_rows = 0
    no_data_rows = 0
    first_take_clock: str | None = None
    last_take_clock: str | None = None

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

            rows_by_tf: dict[str, list[dict[str, Any]]] = {}
            window: PathWindow | None = None
            if row.get("mechanical_setup_status") == "OK" and setup is not None:
                setup_ok_rows += 1
                rows_by_tf = load_path_rows_by_timeframe(
                    roots=selected_data_dirs,
                    symbol=event.symbol,
                    cache=path_cache,
                )
                window = select_path_window(setup, rows_by_tf, pending_expiry_bars=DEFAULT_MECHANICAL_MAX_HOLD_BARS)
                coverage.add(window)
            if setup is not None and not any(rows_by_tf.values()):
                no_data_rows += 1

            for policy in policies:
                if setup is not None and row.get("mechanical_setup_status") == "OK":
                    m15_rows = rows_by_tf.get("M15") or []
                    v0_outcome = resolve_policy_outcome(setup, m15_rows, policy=policy)
                    v1_outcome = resolve_policy_outcome_mtf(
                        setup,
                        rows_by_tf,
                        policy=policy,
                        preselected_window=window,
                    )
                else:
                    v0_outcome = PathOutcome(
                        variant_id=policy.variant_id,
                        outcome="SETUP_NOT_REFINABLE",
                        gross_r=None,
                        bars_to_fill=0,
                        bars_in_trade=0,
                        exit_time=None,
                        skip_reason=str(row.get("mechanical_skip_reason") or "missing_setup"),
                    )
                    v1_outcome = wrap_m15_outcome(v0_outcome, selected_timeframe="M15")

                v0_stats[policy.variant_id].add(v0_outcome, cost_scenarios=cost_scenarios)
                v1_stats[policy.variant_id].add(v1_outcome, cost_scenarios=cost_scenarios)
                comparison_stats[policy.variant_id].add(v0=v0_outcome, v1=v1_outcome)
                v0_cohort_stats[(policy.variant_id, key, role)].add(v0_outcome, cost_scenarios=cost_scenarios)
                v1_cohort_stats[(policy.variant_id, key, role)].add(v1_outcome, cost_scenarios=cost_scenarios)
                for group in groups_for_key(key, role):
                    v0_group_stats[(policy.variant_id, group)].add(v0_outcome, cost_scenarios=cost_scenarios)
                    v1_group_stats[(policy.variant_id, group)].add(v1_outcome, cost_scenarios=cost_scenarios)
                if v1_outcome.outcome in RESOLVED_OUTCOMES and v1_outcome.gross_r is not None:
                    month_returns[month][policy.variant_id] += float(v1_outcome.gross_r)

                event_record = path_event_record_v1(
                    row=row,
                    raw_cohort_key=key,
                    role=role,
                    policy=policy,
                    v0_outcome=v0_outcome,
                    v1_outcome=v1_outcome,
                    cost_scenarios_r=cost_scenarios,
                )
                if len(first_events) < 10:
                    first_events.append(event_record)
                if event_handle is not None:
                    event_handle.write(json.dumps(event_record, sort_keys=True) + "\n")
                    event_rows_written += 1
    finally:
        if event_handle is not None:
            event_handle.close()

    v0_variant_summary = [
        variant_summary_row(policy, v0_stats[policy.variant_id], cost_scenarios=cost_scenarios)
        for policy in policies
    ]
    v1_variant_summary = [
        variant_summary_row(policy, v1_stats[policy.variant_id], cost_scenarios=cost_scenarios)
        for policy in policies
    ]
    v0_group_summary = build_group_rows(policies, v0_group_stats, cost_scenarios=cost_scenarios)
    v1_group_summary = build_group_rows(policies, v1_group_stats, cost_scenarios=cost_scenarios)
    v0_cohort_summary = build_cohort_rows(policies, v0_cohort_stats, cost_scenarios=cost_scenarios)
    v1_cohort_summary = build_cohort_rows(policies, v1_cohort_stats, cost_scenarios=cost_scenarios)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "replay_spec_path": str(Path(spec_path)),
        "replay_spec_sha256": sha256_file(spec_path),
        "ablation_spec_path": DEFAULT_ABLATION_SPEC_PATH,
        "ablation_spec_sha256": sha256_file(DEFAULT_ABLATION_SPEC_PATH),
        "v1_spec_path": DEFAULT_V1_SPEC_PATH,
        "v1_spec_sha256": sha256_file(DEFAULT_V1_SPEC_PATH),
        "v1_protocol_path": DEFAULT_V1_PROTOCOL_PATH,
        "v1_protocol_sha256": sha256_file(DEFAULT_V1_PROTOCOL_PATH),
        "v0_report_path": DEFAULT_V0_REPORT_PATH,
        "v0_report_sha256": sha256_file(DEFAULT_V0_REPORT_PATH),
        "code_commit": git_commit_or_unknown(),
        "promotion_verdict_allowed": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "promotion_blocked_reason": "Same-dataset historical raw-OHLC MTF path-resolution ablation.",
        "research_boundary": [
            "Research/tooling only",
            "No live trading logic changes",
            "No prompt edits",
            "No parameter optimization",
            "No paid AI/API calls",
        ],
        "mtf_resolution_policy": {
            "decision_clock": "M15 candle close UTC",
            "path_timeframe_hierarchy": list(PATH_TF_HIERARCHY),
            "lower_tf_start_rule": "strictly greater than setup candle close",
            "level_selection": "frozen V0 exit-policy R levels only; no lower-timeframe level selection",
            "time_stop_unit": "registered M15 bars converted to elapsed UTC time for M1/M5 path rows",
            "fallback": "M1 if available in the post-decision path window, else M5, else M15",
        },
        "same_bar_policy": {
            "v0": "Fill-and-exit on the same M15 bar is unresolved; newly locked stops activate on the next M15 bar.",
            "v1": "The same policy is applied on the selected M1/M5/M15 path rows. Same-bar ambiguity can remain inside the selected row.",
        },
        "cost_model": {
            "unit": "R per completed round turn",
            "cost_scenarios_r": cost_scenarios,
            "actual_commission_spread_source": "not reliably available in historical OHLC; reported as sensitivity, not measured cost",
            "reentry_cost_note": "V1 has no reentries; future reentry variants must charge one additional round turn per reentry.",
        },
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
        "coverage_diagnostics": coverage_row(coverage),
        "policies": [policy_row(policy) for policy in policies],
        "variant_summary": v1_variant_summary,
        "v0_m15_variant_summary": v0_variant_summary,
        "comparison_summary": [
            comparison_summary_row(policy.variant_id, comparison_stats[policy.variant_id])
            for policy in policies
        ],
        "group_summary": v1_group_summary,
        "v0_m15_group_summary": v0_group_summary,
        "group_delta_summary": delta_rows(
            v0_rows=v0_group_summary,
            v1_rows=v1_group_summary,
            key_fields=("variant_id", "group"),
        ),
        "cohort_summary": v1_cohort_summary,
        "v0_m15_cohort_summary": v0_cohort_summary,
        "cohort_delta_summary": delta_rows(
            v0_rows=v0_cohort_summary,
            v1_rows=v1_cohort_summary,
            key_fields=("variant_id", "cohort_key", "role"),
        ),
        "conclusion_changes": conclusion_change_rows(
            v0_group_rows=v0_group_summary,
            v1_group_rows=v1_group_summary,
            v0_cohort_rows=v0_cohort_summary,
            v1_cohort_rows=v1_cohort_summary,
        ),
        "pbo_diagnostic": pbo_diagnostic(month_returns, [policy.variant_id for policy in policies]),
        "effective_n_diagnostic": effective_n_diagnostic(month_returns, [policy.variant_id for policy in policies]),
        "first_events": first_events,
        "event_log_path": str(event_log_path) if event_log_path else None,
        "event_rows_written": event_rows_written,
    }
    summary["synthesis"] = synthesize(summary)
    summary["ambiguity_ledger"] = ambiguity_ledger(summary)
    summary["opened_questions"] = opened_questions(summary)
    summary["next_steps"] = next_steps(summary)
    return summary


def load_path_rows_by_timeframe(
    *,
    roots: Sequence[Path],
    symbol: str,
    cache: dict[tuple[str, str, str], list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    return {
        timeframe: _load_outcome_rows(
            roots=roots,
            symbol=symbol,
            timeframe=timeframe,
            cache=cache,
        )
        for timeframe in PATH_TF_HIERARCHY
    }


def resolve_policy_outcome_mtf(
    setup: MechanicalSetup | None,
    rows_by_tf: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    policy: ExitPolicy,
    preselected_window: PathWindow | None = None,
) -> MtfPathOutcome:
    if setup is None:
        return MtfPathOutcome(policy.variant_id, "SETUP_NOT_REFINABLE", None, 0, 0, None, "missing_setup")
    if setup.skip_reason is not None:
        return MtfPathOutcome(policy.variant_id, "INVALID", None, 0, 0, None, setup.skip_reason)
    sl_dist = abs(float(setup.entry) - float(setup.sl))
    if sl_dist <= 0:
        return MtfPathOutcome(policy.variant_id, "INVALID", None, 0, 0, None, "DEGENERATE_SL")

    window = preselected_window or select_path_window(setup, rows_by_tf, pending_expiry_bars=policy.pending_expiry_bars)
    if window.selected_timeframe == "M15":
        v0 = resolve_policy_outcome(setup, list(rows_by_tf.get("M15") or []), policy=policy)
        return wrap_m15_outcome(
            v0,
            selected_timeframe="M15",
            fallback_reason=window.fallback_reason,
            lower_tf_row_counts=window.row_counts,
        )
    return resolve_policy_outcome_on_selected_rows(
        setup,
        window.selected_rows,
        policy=policy,
        selected_timeframe=window.selected_timeframe,
        fallback_reason=window.fallback_reason,
        lower_tf_row_counts=window.row_counts,
    )


def select_path_window(
    setup: MechanicalSetup,
    rows_by_tf: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    pending_expiry_bars: int,
) -> PathWindow:
    start = setup.candle_close_time
    end = start + timedelta(minutes=M15_MINUTES * int(pending_expiry_bars))
    windows = {
        timeframe: rows_in_window(list(rows_by_tf.get(timeframe) or []), start=start, end=end)
        for timeframe in PATH_TF_HIERARCHY
    }
    selected = "M15"
    fallback_reason = "M1_M5_UNAVAILABLE_IN_POST_DECISION_WINDOW"
    for timeframe in LOWER_TF_HIERARCHY:
        if windows[timeframe]:
            selected = timeframe
            fallback_reason = None if timeframe == "M1" else "M1_UNAVAILABLE_IN_POST_DECISION_WINDOW"
            break

    first_close = {timeframe: row_time_iso(rows[0]) if rows else None for timeframe, rows in windows.items()}
    last_close = {timeframe: row_time_iso(rows[-1]) if rows else None for timeframe, rows in windows.items()}
    start_violations = sum(
        1
        for rows in windows.values()
        for row in rows
        if isinstance(row.get("time"), datetime) and row["time"] <= start
    )
    return PathWindow(
        selected_timeframe=selected,
        selected_rows=list(windows[selected]),
        fallback_reason=fallback_reason,
        row_counts={timeframe: len(rows) for timeframe, rows in windows.items()},
        first_close=first_close,
        last_close=last_close,
        start_violations=start_violations,
    )


def rows_in_window(
    rows: Sequence[Mapping[str, Any]],
    *,
    start: datetime,
    end: datetime,
) -> list[Mapping[str, Any]]:
    if not rows:
        return []
    idx = first_row_after(rows, start)
    selected: list[Mapping[str, Any]] = []
    for row in rows[idx:]:
        value = row.get("time")
        if not isinstance(value, datetime):
            continue
        if value > end:
            break
        selected.append(row)
    return selected


def resolve_policy_outcome_on_selected_rows(
    setup: MechanicalSetup,
    rows: Sequence[Mapping[str, Any]],
    *,
    policy: ExitPolicy,
    selected_timeframe: str,
    fallback_reason: str | None,
    lower_tf_row_counts: Mapping[str, int],
) -> MtfPathOutcome:
    if not rows:
        return MtfPathOutcome(
            policy.variant_id,
            "NO_DATA",
            None,
            0,
            0,
            None,
            "NO_POST_DECISION_PATH_ROWS",
            selected_timeframe=selected_timeframe,
            fallback_reason=fallback_reason,
            lower_tf_row_counts=dict(lower_tf_row_counts),
        )

    final_target_r = float(setup.rr if policy.use_setup_tp else policy.final_target_r or setup.rr)
    active_stop_r = -1.0
    pending_stop_r = active_stop_r
    locks_triggered: list[dict[str, float]] = []
    triggered_levels: set[float] = set()
    filled = False
    fill_time: datetime | None = None
    bars_to_fill = 0
    bars_in_trade = 0
    path_rows_to_fill = 0
    path_rows_in_trade = 0
    last_close_r: float | None = None
    last_time: str | None = None
    mfe_r: float | None = None
    mae_r: float | None = None
    time_stop_deadline: datetime | None = None

    for bar in rows:
        high, low, close = bar_prices(bar)
        bar_time = bar.get("time")
        if high is None or not isinstance(bar_time, datetime):
            continue
        last_time = row_time_iso(bar)

        if not filled:
            path_rows_to_fill += 1
            bars_to_fill = m15_bar_count(setup.candle_close_time, bar_time)
            if not fill_hit(setup, high=high, low=low):
                continue
            if same_bar_exit_after_fill(
                setup,
                high=high,
                low=low,
                final_target_r=final_target_r,
                lock_steps=policy.lock_steps,
            ):
                return MtfPathOutcome(
                    policy.variant_id,
                    "SAME_BAR",
                    None,
                    bars_to_fill,
                    bars_in_trade=bars_to_fill,
                    exit_time=last_time,
                    skip_reason=f"FILL_AND_PATH_EVENT_SAME_{selected_timeframe}_BAR",
                    selected_timeframe=selected_timeframe,
                    fallback_reason=fallback_reason,
                    path_rows_to_fill=path_rows_to_fill,
                    path_rows_in_trade=path_rows_in_trade,
                    lower_tf_row_counts=dict(lower_tf_row_counts),
                )
            filled = True
            fill_time = bar_time
            time_stop_deadline = fill_time + timedelta(minutes=M15_MINUTES * int(policy.time_stop_bars))
            continue

        path_rows_in_trade += 1
        active_stop_r = pending_stop_r
        favorable_r, adverse_r, close_r = bar_r_extremes(setup, high=high, low=low, close=close)
        mfe_r = favorable_r if mfe_r is None else max(mfe_r, favorable_r)
        mae_r = adverse_r if mae_r is None else min(mae_r, adverse_r)
        last_close_r = close_r
        bars_in_trade = m15_bar_count(fill_time or bar_time, bar_time)

        if adverse_r <= active_stop_r:
            outcome_name = "SL" if active_stop_r < 0 else ("BE_STOP" if abs(active_stop_r) < 1e-12 else "LOCK_STOP")
            return MtfPathOutcome(
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
                selected_timeframe=selected_timeframe,
                fallback_reason=fallback_reason,
                path_rows_to_fill=path_rows_to_fill,
                path_rows_in_trade=path_rows_in_trade,
                lower_tf_row_counts=dict(lower_tf_row_counts),
            )
        if favorable_r >= final_target_r:
            return MtfPathOutcome(
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
                selected_timeframe=selected_timeframe,
                fallback_reason=fallback_reason,
                path_rows_to_fill=path_rows_to_fill,
                path_rows_in_trade=path_rows_in_trade,
                lower_tf_row_counts=dict(lower_tf_row_counts),
            )

        for step in sorted(policy.lock_steps, key=lambda item: item.trigger_r):
            if step.trigger_r in triggered_levels:
                continue
            if favorable_r >= step.trigger_r:
                triggered_levels.add(step.trigger_r)
                if step.floor_r > pending_stop_r:
                    pending_stop_r = step.floor_r
                locks_triggered.append({"trigger_r": step.trigger_r, "floor_r": step.floor_r})

        if time_stop_deadline is not None and bar_time >= time_stop_deadline:
            return MtfPathOutcome(
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
                selected_timeframe=selected_timeframe,
                fallback_reason=fallback_reason,
                path_rows_to_fill=path_rows_to_fill,
                path_rows_in_trade=path_rows_in_trade,
                lower_tf_row_counts=dict(lower_tf_row_counts),
            )

    if not filled:
        return MtfPathOutcome(
            policy.variant_id,
            "NO_ENTRY",
            None,
            bars_to_fill,
            0,
            last_time,
            "NEVER_FILLED",
            selected_timeframe=selected_timeframe,
            fallback_reason=fallback_reason,
            path_rows_to_fill=path_rows_to_fill,
            path_rows_in_trade=path_rows_in_trade,
            lower_tf_row_counts=dict(lower_tf_row_counts),
        )
    return MtfPathOutcome(
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
        selected_timeframe=selected_timeframe,
        fallback_reason=fallback_reason,
        path_rows_to_fill=path_rows_to_fill,
        path_rows_in_trade=path_rows_in_trade,
        lower_tf_row_counts=dict(lower_tf_row_counts),
    )


def wrap_m15_outcome(
    outcome: PathOutcome,
    *,
    selected_timeframe: str,
    fallback_reason: str | None = None,
    lower_tf_row_counts: Mapping[str, int] | None = None,
) -> MtfPathOutcome:
    return MtfPathOutcome(
        variant_id=outcome.variant_id,
        outcome=outcome.outcome,
        gross_r=outcome.gross_r,
        bars_to_fill=outcome.bars_to_fill,
        bars_in_trade=outcome.bars_in_trade,
        exit_time=outcome.exit_time,
        skip_reason=outcome.skip_reason,
        mfe_r=outcome.mfe_r,
        mae_r=outcome.mae_r,
        max_locked_floor_r=outcome.max_locked_floor_r,
        locks_triggered=list(outcome.locks_triggered),
        selected_timeframe=selected_timeframe,
        fallback_reason=fallback_reason,
        lower_tf_row_counts=dict(lower_tf_row_counts or {}),
    )


def m15_bar_count(start: datetime, end: datetime) -> int:
    seconds = max(0.0, (end - start).total_seconds())
    return int(max(1, math.ceil(seconds / (M15_MINUTES * 60.0))))


def row_time_iso(row: Mapping[str, Any]) -> str | None:
    value = row.get("time")
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value) if value is not None else None


def outcome_signature(outcome: Any) -> tuple[Any, Any]:
    gross = outcome.gross_r
    return outcome.outcome, round(float(gross), 6) if gross is not None else None


def coverage_row(coverage: CoverageStats) -> dict[str, Any]:
    return {
        "setup_windows": coverage.setup_windows,
        "m1_available_windows": coverage.m1_available_windows,
        "m1_available_rows": coverage.m1_available_rows,
        "m5_available_windows": coverage.m5_available_windows,
        "m5_available_rows": coverage.m5_available_rows,
        "m15_available_windows": coverage.m15_available_windows,
        "m15_available_rows": coverage.m15_available_rows,
        "m15_fallback_windows": coverage.m15_fallback_windows,
        "selected_timeframes": dict(sorted(coverage.selected_timeframes.items())),
        "lower_tf_start_violations": coverage.start_violations,
    }


def comparison_summary_row(variant_id: str, stats: VariantComparisonStats) -> dict[str, Any]:
    mean_delta = (
        round(stats.gross_delta_sum / stats.both_resolved_n, 6)
        if stats.both_resolved_n
        else None
    )
    return {
        "variant_id": variant_id,
        "actions_seen": stats.actions_seen,
        "v0_resolved_n": stats.v0_resolved_n,
        "v1_resolved_n": stats.v1_resolved_n,
        "both_resolved_n": stats.both_resolved_n,
        "v0_same_bar": stats.v0_same_bar,
        "v1_same_bar": stats.v1_same_bar,
        "same_bar_resolved_by_mtf": stats.same_bar_resolved_by_mtf,
        "same_bar_still_unresolved": stats.same_bar_still_unresolved,
        "v1_new_same_bar": stats.v1_new_same_bar,
        "same_bar_delta": stats.v1_same_bar - stats.v0_same_bar,
        "outcome_changed": stats.outcome_changed,
        "paired_gross_mean_delta_r": mean_delta,
        "paired_gross_sum_delta_r": round(stats.gross_delta_sum, 6),
        "selected_timeframes": dict(sorted(stats.selected_timeframes.items())),
    }


def delta_rows(
    *,
    v0_rows: Sequence[Mapping[str, Any]],
    v1_rows: Sequence[Mapping[str, Any]],
    key_fields: Sequence[str],
) -> list[dict[str, Any]]:
    v0_index = {tuple(row.get(field) for field in key_fields): row for row in v0_rows}
    rows = []
    for v1 in v1_rows:
        key = tuple(v1.get(field) for field in key_fields)
        v0 = v0_index.get(key) or {}
        row = {field: v1.get(field) for field in key_fields}
        row.update(
            {
                "v0_resolved_n": v0.get("resolved_n"),
                "v1_resolved_n": v1.get("resolved_n"),
                "resolved_n_delta": none_safe_delta(v1.get("resolved_n"), v0.get("resolved_n")),
                "v0_net_mean_r_cost_0.05": v0.get("net_mean_r_cost_0.05"),
                "v1_net_mean_r_cost_0.05": v1.get("net_mean_r_cost_0.05"),
                "net_mean_delta_cost_0.05": none_safe_delta(
                    v1.get("net_mean_r_cost_0.05"),
                    v0.get("net_mean_r_cost_0.05"),
                ),
                "v0_same_bar": v0.get("same_bar") or (v0.get("outcomes") or {}).get("SAME_BAR", 0),
                "v1_same_bar": v1.get("same_bar") or (v1.get("outcomes") or {}).get("SAME_BAR", 0),
            }
        )
        rows.append(row)
    return rows


def none_safe_delta(left: Any, right: Any) -> float | int | None:
    if left is None or right is None:
        return None
    try:
        delta = float(left) - float(right)
    except (TypeError, ValueError):
        return None
    if isinstance(left, int) and isinstance(right, int):
        return int(delta)
    return round(delta, 6)


def conclusion_change_rows(
    *,
    v0_group_rows: Sequence[Mapping[str, Any]],
    v1_group_rows: Sequence[Mapping[str, Any]],
    v0_cohort_rows: Sequence[Mapping[str, Any]],
    v1_cohort_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    rows.extend(
        best_variant_changes(
            scope="group",
            v0_rows=v0_group_rows,
            v1_rows=v1_group_rows,
            partition_fields=("group",),
        )
    )
    rows.extend(
        best_variant_changes(
            scope="cohort",
            v0_rows=v0_cohort_rows,
            v1_rows=v1_cohort_rows,
            partition_fields=("cohort_key", "role"),
        )
    )
    return rows


def best_variant_changes(
    *,
    scope: str,
    v0_rows: Sequence[Mapping[str, Any]],
    v1_rows: Sequence[Mapping[str, Any]],
    partition_fields: Sequence[str],
) -> list[dict[str, Any]]:
    v0_groups = partition_rows(v0_rows, partition_fields=partition_fields)
    v1_groups = partition_rows(v1_rows, partition_fields=partition_fields)
    output = []
    for key, v1_partition in sorted(v1_groups.items()):
        v0_partition = v0_groups.get(key) or []
        if not v0_partition:
            continue
        v0_best = best_net_row(v0_partition)
        v1_best = best_net_row(v1_partition)
        if not v0_best or not v1_best:
            continue
        lock_sign_changed = lock_vs_j46_sign(v0_partition) != lock_vs_j46_sign(v1_partition)
        if v0_best.get("variant_id") == v1_best.get("variant_id") and not lock_sign_changed:
            continue
        row = {
            "scope": scope,
            "v0_best_variant": v0_best.get("variant_id"),
            "v0_best_net_mean_r_cost_0.05": v0_best.get("net_mean_r_cost_0.05"),
            "v1_best_variant": v1_best.get("variant_id"),
            "v1_best_net_mean_r_cost_0.05": v1_best.get("net_mean_r_cost_0.05"),
            "lock_vs_j46_sign_changed": lock_sign_changed,
        }
        for field, value in zip(partition_fields, key):
            row[field] = value
        output.append(row)
    return output


def partition_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    partition_fields: Sequence[str],
) -> dict[tuple[Any, ...], list[Mapping[str, Any]]]:
    output: dict[tuple[Any, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        output[tuple(row.get(field) for field in partition_fields)].append(row)
    return output


def best_net_row(rows: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    candidates = [row for row in rows if row.get("net_mean_r_cost_0.05") is not None]
    if not candidates:
        return None
    return max(candidates, key=lambda row: float(row.get("net_mean_r_cost_0.05") or -999.0))


def lock_vs_j46_sign(rows: Sequence[Mapping[str, Any]]) -> str | None:
    j46 = next((row for row in rows if row.get("variant_id") == "J46_J49_ONLY"), None)
    locks = [row for row in rows if str(row.get("variant_id", "")).startswith("PATH_LOCK")]
    if not j46 or not locks or j46.get("net_mean_r_cost_0.05") is None:
        return None
    best_lock = best_net_row(locks)
    if best_lock is None or best_lock.get("net_mean_r_cost_0.05") is None:
        return None
    delta = float(best_lock.get("net_mean_r_cost_0.05")) - float(j46.get("net_mean_r_cost_0.05"))
    if abs(delta) < 1e-12:
        return "flat"
    return "positive" if delta > 0 else "negative"


def path_event_record_v1(
    *,
    row: Mapping[str, Any],
    raw_cohort_key: str,
    role: str,
    policy: ExitPolicy,
    v0_outcome: PathOutcome,
    v1_outcome: MtfPathOutcome,
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
        "mechanical_side": row.get("mechanical_side"),
        "mechanical_entry": row.get("mechanical_entry"),
        "mechanical_sl": row.get("mechanical_sl"),
        "mechanical_tp": row.get("mechanical_tp"),
        "v0_path_timeframe": "M15",
        "v0_outcome": v0_outcome.outcome,
        "v0_gross_r": v0_outcome.gross_r,
        "v1_selected_timeframe": v1_outcome.selected_timeframe,
        "v1_fallback_reason": v1_outcome.fallback_reason,
        "v1_outcome": v1_outcome.outcome,
        "v1_gross_r": v1_outcome.gross_r,
        "v1_net_r_by_cost": {
            f"{float(cost):g}": round(float(v1_outcome.gross_r) - float(cost), 6)
            if v1_outcome.gross_r is not None and v1_outcome.outcome in RESOLVED_OUTCOMES
            else None
            for cost in cost_scenarios_r
        },
        "outcome_changed": outcome_signature(v0_outcome) != outcome_signature(v1_outcome),
        "bars_to_fill": v1_outcome.bars_to_fill,
        "bars_in_trade": v1_outcome.bars_in_trade,
        "path_rows_to_fill": v1_outcome.path_rows_to_fill,
        "path_rows_in_trade": v1_outcome.path_rows_in_trade,
        "exit_time": v1_outcome.exit_time,
        "mfe_r": v1_outcome.mfe_r,
        "mae_r": v1_outcome.mae_r,
        "max_locked_floor_r": v1_outcome.max_locked_floor_r,
        "locks_triggered": v1_outcome.locks_triggered,
        "skip_reason": v1_outcome.skip_reason,
        "lower_tf_row_counts": v1_outcome.lower_tf_row_counts,
    }


def synthesize(summary: Mapping[str, Any]) -> list[dict[str, str]]:
    rows = list(summary.get("variant_summary") or [])
    comparisons = {str(row.get("variant_id")): row for row in summary.get("comparison_summary") or []}
    if not rows:
        return []
    best_net = max(rows, key=lambda row: float(row.get("net_mean_r_cost_0.05") or -999.0))
    best_gross = max(rows, key=lambda row: float(row.get("gross_mean_r") or -999.0))
    j46 = next((row for row in rows if row.get("variant_id") == "J46_J49_ONLY"), {})
    best_lock = max(
        [row for row in rows if str(row.get("variant_id", "")).startswith("PATH_LOCK")],
        key=lambda row: float(row.get("net_mean_r_cost_0.05") or -999.0),
        default={},
    )
    lock_delta = None
    if best_lock and j46:
        lock_delta = round(
            float(best_lock.get("net_mean_r_cost_0.05") or 0.0)
            - float(j46.get("net_mean_r_cost_0.05") or 0.0),
            6,
        )
    total_v0_same = sum(int(row.get("v0_same_bar") or 0) for row in comparisons.values())
    total_v1_same = sum(int(row.get("v1_same_bar") or 0) for row in comparisons.values())
    total_resolved = sum(int(row.get("same_bar_resolved_by_mtf") or 0) for row in comparisons.values())
    target_delta = group_delta(summary, "target_cohorts", lock_prefix="PATH_LOCK", baseline_variant="J46_J49_ONLY")
    primary_delta = group_delta(summary, "primary_controlled_family", lock_prefix="PATH_LOCK", baseline_variant="J46_J49_ONLY")
    cleared_delta = group_delta(summary, "cleared_non_primary_targets", lock_prefix="PATH_LOCK", baseline_variant="J46_J49_ONLY")
    conclusion_changes = summary.get("conclusion_changes") or []
    return [
        {
            "question": "Which V1 variant leads on gross mean R?",
            "answer": f"{best_gross.get('variant_id')} with gross_mean_r={best_gross.get('gross_mean_r')}.",
        },
        {
            "question": "Which V1 variant leads after a 0.05R round-turn cost sensitivity?",
            "answer": f"{best_net.get('variant_id')} with net_mean_r_cost_0.05={best_net.get('net_mean_r_cost_0.05')}.",
        },
        {
            "question": "Did lock-only V1 beat J46-J49 globally?",
            "answer": (
                f"Best lock-only net-minus-J46 at 0.05R cost = {lock_delta}. "
                "This remains same-dataset diagnostic evidence only."
            ),
        },
        {
            "question": "How much did MTF path resolution reduce same-bar ambiguity?",
            "answer": (
                f"Across policy-event rows, V0 same-bar count={total_v0_same}, "
                f"V1 same-bar count={total_v1_same}, and V0 same-bars resolved by MTF={total_resolved}."
            ),
        },
        {
            "question": "Where did lock-only look most interesting under V1?",
            "answer": (
                f"Target-family best-lock minus J46 at 0.05R cost = {target_delta}; "
                f"primary-family delta = {primary_delta}; cleared-non-primary delta = {cleared_delta}."
            ),
        },
        {
            "question": "Did MTF resolution change any group/cohort conclusion flags?",
            "answer": (
                f"{len(conclusion_changes)} group/cohort best-variant or lock-vs-J46 sign changes were detected. "
                "See the Conclusion Changes table before moving to V2."
            ),
        },
        {
            "question": "Does this promote an exit policy?",
            "answer": "No. This is same-dataset historical MTF path-resolution research and remains NO_PROMOTION_VERDICT.",
        },
    ]


def ambiguity_ledger(summary: Mapping[str, Any]) -> list[dict[str, str]]:
    coverage = summary.get("coverage_diagnostics") or {}
    comparison = summary.get("comparison_summary") or []
    v1_same = sum(int(row.get("v1_same_bar") or 0) for row in comparison)
    return [
        {
            "item": "Cost model",
            "status": "SENSITIVITY_NOT_MEASURED_COST",
            "detail": "Historical OHLC does not contain reliable commission/spread/slippage. Report uses R-cost sensitivity.",
        },
        {
            "item": "Lower-timeframe coverage",
            "status": "QUANTIFIED",
            "detail": (
                f"M1 windows={coverage.get('m1_available_windows')}, "
                f"M5 windows={coverage.get('m5_available_windows')}, "
                f"M15 fallback windows={coverage.get('m15_fallback_windows')}."
            ),
        },
        {
            "item": "Post-decision lower-TF start",
            "status": "PASS" if not coverage.get("lower_tf_start_violations") else "BLOCKED",
            "detail": f"Lower-timeframe rows with close_time <= setup decision clock: {coverage.get('lower_tf_start_violations')}.",
        },
        {
            "item": "Remaining same-bar ambiguity",
            "status": "CLEAR" if v1_same == 0 else "REMAINS_QUANTIFIED",
            "detail": f"V1 same-bar unresolved policy-event rows: {v1_same}. These are inside the selected M1/M5/M15 bar.",
        },
        {
            "item": "Reentry",
            "status": "INTENTIONALLY_BLOCKED",
            "detail": "No reentry is tested in V1. Risk-budgeted reentry remains V3-only.",
        },
        {
            "item": "L2 attribution",
            "status": "NOT_IMPLEMENTED_IN_V1",
            "detail": "V1 preserves V0's raw cohort stream and does not reconstruct deterministic L2.",
        },
        {
            "item": "Promotion",
            "status": "BLOCKED_BY_DESIGN",
            "detail": str(summary.get("promotion_blocked_reason")),
        },
    ]


def opened_questions(summary: Mapping[str, Any]) -> list[dict[str, str]]:
    changes = summary.get("conclusion_changes") or []
    coverage = summary.get("coverage_diagnostics") or {}
    comparison = summary.get("comparison_summary") or []
    v1_same = sum(int(row.get("v1_same_bar") or 0) for row in comparison)
    return [
        {
            "question": "Are remaining same-bar cases material enough to block V2?",
            "status": "OPEN" if v1_same else "CLEARED",
            "detail": f"Remaining V1 same-bar policy-event rows: {v1_same}.",
        },
        {
            "question": "Does lower-timeframe coverage create a cohort comparability problem?",
            "status": "OPEN" if coverage.get("m15_fallback_windows") else "CLEARED",
            "detail": (
                f"Selected timeframe mix: {coverage.get('selected_timeframes')}. "
                "Any V2 structural-level run must preserve this coverage ledger."
            ),
        },
        {
            "question": "Did MTF resolution change the interpretation of any cohort?",
            "status": "OPEN" if changes else "CLEARED",
            "detail": f"Conclusion change rows detected: {len(changes)}.",
        },
    ]


def next_steps(summary: Mapping[str, Any]) -> list[dict[str, str]]:
    comparison = summary.get("comparison_summary") or []
    v1_same = sum(int(row.get("v1_same_bar") or 0) for row in comparison)
    changes = summary.get("conclusion_changes") or []
    steps = [
        {
            "rank": "1",
            "next_step": "Review remaining same-bar rows from the V1 event log",
            "reason": "V2 should not start if unresolved ordering is concentrated in a decision-critical cohort or variant.",
        },
        {
            "rank": "2",
            "next_step": "Review conclusion-change rows",
            "reason": "Any cohort where MTF changes the best variant or lock-vs-J46 sign needs explicit synthesis before V2.",
        },
        {
            "rank": "3",
            "next_step": "Only then decide whether V1 ambiguity is cleared for V2 structural levels",
            "reason": "The next layer should inherit a stable path-resolution measurement layer, not fix V1 retroactively.",
        },
    ]
    if v1_same or changes:
        return steps
    return [
        {
            "rank": "1",
            "next_step": "Archive V1 as the path-resolution baseline for V2",
            "reason": "No blocking same-bar or interpretation ambiguity remains in the summary diagnostics.",
        },
        {
            "rank": "2",
            "next_step": "Pre-register V2 structural level selectors before coding",
            "reason": "V2 must avoid level fitting after seeing MTF-resolved path outcomes.",
        },
    ]


def render_report(summary: Mapping[str, Any]) -> str:
    pbo = summary.get("pbo_diagnostic") or {}
    eff = (summary.get("effective_n_diagnostic") or {}).get("exit_policy_effective_n") or {}
    lines = [
        "# Phase 3 Path Scaling V1 MTF Path Resolution",
        "",
        f"**Created UTC:** {summary.get('created_at_utc')}",
        f"**Replay spec:** `{summary.get('replay_spec_path')}`",
        f"**V1 spec:** `{summary.get('v1_spec_path')}`",
        f"**V1 protocol:** `{summary.get('v1_protocol_path')}`",
        f"**V0 comparison report:** `{summary.get('v0_report_path')}`",
        f"**Promotion verdict:** `{summary.get('promotion_verdict')}`",
        "",
        "## Boundary",
        "",
        "- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.",
        "- V1 uses the same raw-OHLC no-leak candidate reconstruction and frozen V0 exit policies.",
        "- Outcomes are attached only after the cohort decision is locked.",
        "- M1/M5 rows are used only for post-decision path ordering, never for level selection.",
        "- Costs are reported as R-per-round-turn sensitivity because reliable historical commission/spread/slippage is not present in OHLC.",
        "- Reentry and L2-on/off attribution remain intentionally blocked.",
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
                    "include_blocked_controls": summary.get("include_blocked_controls"),
                    "first_take_clock": summary.get("first_take_clock"),
                    "last_take_clock": summary.get("last_take_clock"),
                }
            ]
        ),
        "",
        "## MTF Resolution Policy",
        "",
        markdown_table([summary.get("mtf_resolution_policy") or {}]),
        "",
        "## Coverage Diagnostics",
        "",
        markdown_table([summary.get("coverage_diagnostics") or {}]),
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
        "## V1 Variant Summary",
        "",
        markdown_table(summary.get("variant_summary") or []),
        "",
        "## V0 M15 Variant Summary",
        "",
        markdown_table(summary.get("v0_m15_variant_summary") or []),
        "",
        "## V0 Versus V1 Comparison",
        "",
        markdown_table(summary.get("comparison_summary") or []),
        "",
        "## V1 Group Summary",
        "",
        markdown_table(summary.get("group_summary") or []),
        "",
        "## Group Delta Summary",
        "",
        markdown_table(summary.get("group_delta_summary") or []),
        "",
        "## V1 Cohort Summary",
        "",
        markdown_table(summary.get("cohort_summary") or []),
        "",
        "## Cohort Delta Summary",
        "",
        markdown_table(summary.get("cohort_delta_summary") or []),
        "",
        "## Conclusion Changes",
        "",
        markdown_table(summary.get("conclusion_changes") or []),
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
        "## Opened Questions",
        "",
        markdown_table(summary.get("opened_questions") or []),
        "",
        "## Next Steps",
        "",
        markdown_table(summary.get("next_steps") or []),
        "",
        "## Synthesis",
        "",
        "- V1 is a path-ordering measurement layer, not a new strategy or promotion dossier.",
        "- The decision stream and exit levels are inherited from V0; lower timeframes only resolve post-decision path order where available.",
        "- V2 should not begin until the ambiguity ledger and conclusion-change rows are reviewed.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(
    summary: Mapping[str, Any],
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    report_path: str | Path = DEFAULT_REPORT_PATH,
) -> tuple[Path, Path]:
    output_dir = Path(output_root) / "path_ablation_v1_mtf"
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_path = output_dir / f"raw_ohlc_path_ablation_v1_mtf_{stamp}.json"
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
            / "path_ablation_v1_mtf"
            / f"raw_ohlc_path_ablation_v1_mtf_events_{stamp}.jsonl"
        )
    summary = run_path_ablation_v1_mtf(
        spec_path=args.spec,
        data_dirs=args.data_dirs,
        start=args.start,
        end=args.end,
        max_candles_per_symbol=args.max_candles_per_symbol,
        max_events=args.max_events,
        include_blocked_controls=args.include_blocked_controls,
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
        best = max(
            summary.get("variant_summary") or [],
            key=lambda row: float(row.get("net_mean_r_cost_0.05") or -999.0),
            default={},
        )
        comparison = summary.get("comparison_summary") or []
        print(
            json.dumps(
                {
                    "promotion_verdict": summary.get("promotion_verdict"),
                    "source_scope": summary.get("source_scope"),
                    "take_rows_seen": summary.get("take_rows_seen"),
                    "coverage_diagnostics": summary.get("coverage_diagnostics"),
                    "v0_same_bar_total": sum(int(row.get("v0_same_bar") or 0) for row in comparison),
                    "v1_same_bar_total": sum(int(row.get("v1_same_bar") or 0) for row in comparison),
                    "best_net_cost_0.05": best.get("variant_id"),
                    "best_net_mean_r_cost_0.05": best.get("net_mean_r_cost_0.05"),
                    "conclusion_change_count": len(summary.get("conclusion_changes") or []),
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
