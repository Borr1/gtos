#!/usr/bin/env python3
"""Run Phase 3 raw-OHLC path scaling V2 structural-level selectors.

V2 is research infrastructure only. It preserves the V1 MTF path resolver and
the V0/V1 fixed-R comparators, then adds lock-only structural stop floors.
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
from scripts.build_historical_opportunity_dataset import (  # noqa: E402
    DEFAULT_MECHANICAL_MAX_HOLD_BARS,
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
    group_delta,
    pbo_diagnostic,
    policy_row,
    registered_policies,
    resolve_policy_outcome,
    same_bar_exit_after_fill,
    source_scope,
    variant_summary_row,
)
from scripts.run_raw_ohlc_path_ablation_v1_mtf import (  # noqa: E402
    CoverageStats,
    M15_MINUTES,
    MtfPathOutcome,
    PathWindow,
    coverage_row,
    load_path_rows_by_timeframe,
    m15_bar_count,
    row_time_iso,
    resolve_policy_outcome_mtf,
    select_path_window,
    wrap_m15_outcome,
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


SCHEMA_VERSION = "raw_ohlc_path_scaling_v2_structural_level_summary"
EVENT_SCHEMA_VERSION = "raw_ohlc_path_scaling_v2_structural_level_event"
DEFAULT_REPORT_PATH = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V2_STRUCTURAL_LEVEL_SELECTOR_REPORT_2026-05-02.md"
)
DEFAULT_V2_SPEC_PATH = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V2_STRUCTURAL_LEVEL_SELECTOR_SPEC_V1.json"
)
DEFAULT_V2_PROTOCOL_PATH = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V2_STRUCTURAL_LEVEL_SELECTOR_PROTOCOL_2026-05-02.md"
)
DEFAULT_V1_FORENSICS_PATH = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V1_FAILURE_FORENSICS_2026-05-02.md"
)
STRUCTURAL_SELECTOR_IDS = (
    "PROTECTED_CONFIRMED_SWING",
    "BOS_BROKEN_LEVEL",
    "DISPLACEMENT_HALFBACK",
    "FVG_MIDPOINT",
    "FVG_PROTECTIVE_EDGE",
    "OB_PROTECTIVE_BOUNDARY",
    "PATH_HIGH_LOW_RUN",
    "EQUAL_HIGH_LOW_RUN",
)
STRUCTURAL_SELECTOR_FAMILIES = {
    "PROTECTED_CONFIRMED_SWING": "swing_structure",
    "BOS_BROKEN_LEVEL": "swing_structure",
    "DISPLACEMENT_HALFBACK": "volatility_displacement",
    "FVG_MIDPOINT": "poi_boundary",
    "FVG_PROTECTIVE_EDGE": "poi_boundary",
    "OB_PROTECTIVE_BOUNDARY": "poi_boundary",
    "PATH_HIGH_LOW_RUN": "liquidity",
    "EQUAL_HIGH_LOW_RUN": "liquidity",
}
GROUPS = (
    "all_enabled",
    "all_excluding_gbpusd_control",
    "target_cohorts",
    "primary_controlled_family",
    "cleared_non_primary_targets",
    "negative_controls",
    "blocked_dominance_controls",
)
EPS = 1e-12


@dataclass(frozen=True)
class StructuralPolicy:
    variant_id: str
    family: str
    description: str
    selector_ids: tuple[str, ...]
    final_target_r: float = 6.0
    time_stop_bars: int = 12
    pending_expiry_bars: int = DEFAULT_MECHANICAL_MAX_HOLD_BARS
    use_setup_tp: bool = False
    lock_steps: tuple[LockStep, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SwingPoint:
    swing_type: str
    price: float
    index: int
    time: str | None
    confirmed_index: int
    confirmed_time: str | None


@dataclass(frozen=True)
class StructuralLevelCandidate:
    selector_id: str
    family: str
    event_type: str
    price: float
    floor_r: float
    source_index: int
    source_time: str | None
    confirmed_index: int
    confirmed_time: str | None
    source_timeframe: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class StructuralPathFeatures:
    candidates_by_index: dict[int, list[StructuralLevelCandidate]] = field(default_factory=lambda: defaultdict(list))
    candidate_counts: Counter[str] = field(default_factory=Counter)
    diagnostic_counts: Counter[str] = field(default_factory=Counter)


@dataclass
class StressStats:
    resolved_returns: list[float] = field(default_factory=list)
    same_bar_n: int = 0

    def add(self, outcome: MtfPathOutcome | PathOutcome) -> None:
        if outcome.outcome in RESOLVED_OUTCOMES and outcome.gross_r is not None:
            self.resolved_returns.append(float(outcome.gross_r))
        elif outcome.outcome == "SAME_BAR":
            self.same_bar_n += 1

    def mean(self, treatment: str, *, cost_r: float) -> tuple[int, float | None]:
        values = list(self.resolved_returns)
        if treatment == "samebar_breakeven":
            values.extend([0.0] * self.same_bar_n)
        elif treatment == "samebar_pessimistic":
            values.extend([-1.0] * self.same_bar_n)
        elif treatment != "exclude_unresolved":
            raise ValueError(f"unknown same-bar treatment: {treatment}")
        if not values:
            return 0, None
        return len(values), round((sum(values) / len(values)) - float(cost_r), 6)


@dataclass
class PairwiseDeltaStats:
    paired_resolved_n: int = 0
    baseline_sum_r: float = 0.0
    candidate_sum_r: float = 0.0
    delta_sum_r: float = 0.0
    candidate_better_n: int = 0
    baseline_better_n: int = 0
    tie_n: int = 0
    baseline_positive_n: int = 0
    candidate_positive_n: int = 0
    both_positive_n: int = 0
    both_nonpositive_n: int = 0
    candidate_lock_triggered_n: int = 0
    truncation_n: int = 0
    truncation_lost_r: float = 0.0
    rescued_baseline_nonpositive_n: int = 0
    rescued_to_positive_n: int = 0
    candidate_made_positive_nonpositive_n: int = 0

    def add(self, *, baseline: Any, candidate: Any) -> None:
        if (
            baseline is None
            or candidate is None
            or baseline.outcome not in RESOLVED_OUTCOMES
            or candidate.outcome not in RESOLVED_OUTCOMES
            or baseline.gross_r is None
            or candidate.gross_r is None
        ):
            return
        base_r = float(baseline.gross_r)
        cand_r = float(candidate.gross_r)
        delta = cand_r - base_r
        self.paired_resolved_n += 1
        self.baseline_sum_r += base_r
        self.candidate_sum_r += cand_r
        self.delta_sum_r += delta
        if delta > EPS:
            self.candidate_better_n += 1
        elif delta < -EPS:
            self.baseline_better_n += 1
        else:
            self.tie_n += 1
        if base_r > 0:
            self.baseline_positive_n += 1
        if cand_r > 0:
            self.candidate_positive_n += 1
        if base_r > 0 and cand_r > 0:
            self.both_positive_n += 1
        if base_r <= 0 and cand_r <= 0:
            self.both_nonpositive_n += 1
        if candidate.locks_triggered:
            self.candidate_lock_triggered_n += 1
        if base_r > cand_r and base_r > 0:
            self.truncation_n += 1
            self.truncation_lost_r += base_r - cand_r
        if base_r <= 0 and cand_r > base_r:
            self.rescued_baseline_nonpositive_n += 1
            if cand_r > 0:
                self.rescued_to_positive_n += 1
        if base_r > 0 and cand_r <= 0:
            self.candidate_made_positive_nonpositive_n += 1


@dataclass
class SelectorFireStats:
    fires: int = 0
    resolved_n: int = 0
    gross_sum_r: float = 0.0
    outcomes: Counter[str] = field(default_factory=Counter)

    def add(self, outcome: MtfPathOutcome) -> None:
        self.fires += 1
        self.outcomes[outcome.outcome] += 1
        if outcome.outcome in RESOLVED_OUTCOMES and outcome.gross_r is not None:
            self.resolved_n += 1
            self.gross_sum_r += float(outcome.gross_r)


def registered_structural_policies() -> list[StructuralPolicy]:
    return [
        StructuralPolicy(
            "STRUCT_SWING_PROTECTED_V2",
            "swing_structure",
            "Lock behind the latest confirmed pullback swing in trade direction.",
            ("PROTECTED_CONFIRMED_SWING",),
        ),
        StructuralPolicy(
            "STRUCT_BOS_LEVEL_V2",
            "swing_structure",
            "Lock behind a confirmed swing level broken by an in-trade-direction BOS close.",
            ("BOS_BROKEN_LEVEL",),
        ),
        StructuralPolicy(
            "STRUCT_DISPLACEMENT_HALFBACK_V2",
            "volatility_displacement",
            "Lock behind the body halfback of an in-trade-direction displacement candle.",
            ("DISPLACEMENT_HALFBACK",),
        ),
        StructuralPolicy(
            "STRUCT_FVG_MID_EDGE_V2",
            "poi_boundary",
            "Lock behind the best valid in-trade-direction FVG midpoint or protective edge.",
            ("FVG_MIDPOINT", "FVG_PROTECTIVE_EDGE"),
        ),
        StructuralPolicy(
            "STRUCT_OB_BOUNDARY_V2",
            "poi_boundary",
            "Lock behind the protective boundary of the last opposing candle before an in-direction BOS close.",
            ("OB_PROTECTIVE_BOUNDARY",),
        ),
        StructuralPolicy(
            "STRUCT_LIQUIDITY_RUN_V2",
            "liquidity",
            "Lock behind prior path or equal high/low liquidity after an in-direction close through it.",
            ("PATH_HIGH_LOW_RUN", "EQUAL_HIGH_LOW_RUN"),
        ),
        StructuralPolicy(
            "STRUCT_COMPOSITE_ANY_V2",
            "composite",
            "Lock behind the best valid floor from all registered V2 structural selectors.",
            STRUCTURAL_SELECTOR_IDS,
        ),
    ]


def registered_v2_policies() -> list[ExitPolicy | StructuralPolicy]:
    return [*registered_policies(), *registered_structural_policies()]


def resolve_structural_policy_outcome(
    setup: MechanicalSetup | None,
    window: PathWindow | None,
    *,
    policy: StructuralPolicy,
    features: StructuralPathFeatures | None = None,
) -> MtfPathOutcome:
    if setup is None:
        return MtfPathOutcome(policy.variant_id, "SETUP_NOT_REFINABLE", None, 0, 0, None, "missing_setup")
    if setup.skip_reason is not None:
        return MtfPathOutcome(policy.variant_id, "INVALID", None, 0, 0, None, setup.skip_reason)
    sl_dist = abs(float(setup.entry) - float(setup.sl))
    if sl_dist <= 0:
        return MtfPathOutcome(policy.variant_id, "INVALID", None, 0, 0, None, "DEGENERATE_SL")
    if window is None or not window.selected_rows:
        return MtfPathOutcome(
            policy.variant_id,
            "NO_DATA",
            None,
            0,
            0,
            None,
            "NO_POST_DECISION_PATH_ROWS",
            selected_timeframe=(window.selected_timeframe if window else "M15"),
            fallback_reason=(window.fallback_reason if window else None),
            lower_tf_row_counts=(dict(window.row_counts) if window else {}),
        )

    rows = window.selected_rows
    features = features or build_structural_path_features(
        setup,
        rows,
        selected_timeframe=window.selected_timeframe,
    )
    active_stop_r = -1.0
    pending_stop_r = active_stop_r
    locks_triggered: list[dict[str, Any]] = []
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
    final_target_r = float(policy.final_target_r)
    selector_ids = set(policy.selector_ids)

    for row_index, bar in enumerate(rows):
        high, low, close = bar_prices(bar)
        bar_time = bar.get("time")
        if high is None or close is None or not isinstance(bar_time, datetime):
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
                lock_steps=(),
            ):
                return MtfPathOutcome(
                    policy.variant_id,
                    "SAME_BAR",
                    None,
                    bars_to_fill,
                    bars_in_trade=bars_to_fill,
                    exit_time=last_time,
                    skip_reason=f"FILL_AND_EXIT_SAME_{window.selected_timeframe}_BAR",
                    selected_timeframe=window.selected_timeframe,
                    fallback_reason=window.fallback_reason,
                    path_rows_to_fill=path_rows_to_fill,
                    path_rows_in_trade=path_rows_in_trade,
                    lower_tf_row_counts=dict(window.row_counts),
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
            outcome_name = "SL" if active_stop_r < 0 else ("BE_STOP" if abs(active_stop_r) < EPS else "LOCK_STOP")
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
                selected_timeframe=window.selected_timeframe,
                fallback_reason=window.fallback_reason,
                path_rows_to_fill=path_rows_to_fill,
                path_rows_in_trade=path_rows_in_trade,
                lower_tf_row_counts=dict(window.row_counts),
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
                selected_timeframe=window.selected_timeframe,
                fallback_reason=window.fallback_reason,
                path_rows_to_fill=path_rows_to_fill,
                path_rows_in_trade=path_rows_in_trade,
                lower_tf_row_counts=dict(window.row_counts),
            )

        candidates = [
            candidate
            for candidate in features.candidates_by_index.get(row_index, [])
            if candidate.selector_id in selector_ids and candidate.floor_r > pending_stop_r + EPS
        ]
        if candidates:
            selected = max(candidates, key=lambda item: item.floor_r)
            pending_stop_r = float(selected.floor_r)
            locks_triggered.append(candidate_record(selected))

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
                selected_timeframe=window.selected_timeframe,
                fallback_reason=window.fallback_reason,
                path_rows_to_fill=path_rows_to_fill,
                path_rows_in_trade=path_rows_in_trade,
                lower_tf_row_counts=dict(window.row_counts),
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
            selected_timeframe=window.selected_timeframe,
            fallback_reason=window.fallback_reason,
            path_rows_to_fill=path_rows_to_fill,
            path_rows_in_trade=path_rows_in_trade,
            lower_tf_row_counts=dict(window.row_counts),
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
        selected_timeframe=window.selected_timeframe,
        fallback_reason=window.fallback_reason,
        path_rows_to_fill=path_rows_to_fill,
        path_rows_in_trade=path_rows_in_trade,
        lower_tf_row_counts=dict(window.row_counts),
    )


def build_structural_path_features(
    setup: MechanicalSetup,
    rows: Sequence[Mapping[str, Any]],
    *,
    selected_timeframe: str,
) -> StructuralPathFeatures:
    features = StructuralPathFeatures()
    confirmed_swings: list[SwingPoint] = []
    broken_in_direction: set[tuple[str, int]] = set()
    broken_against_trade: set[tuple[str, int]] = set()
    body_history: list[float] = []
    prior_high: float | None = None
    prior_low: float | None = None
    decimals = infer_price_decimals(rows)
    equal_high_counts: Counter[float] = Counter()
    equal_low_counts: Counter[float] = Counter()

    for index, row in enumerate(rows):
        ohlc = bar_ohlc(row)
        if ohlc is None:
            continue
        open_, high, low, close = ohlc
        row_candidates: list[StructuralLevelCandidate] = []

        for swing in newly_confirmed_swings(rows, current_index=index):
            confirmed_swings.append(swing)
            features.diagnostic_counts[f"CONFIRMED_SWING_{swing.swing_type.upper()}"] += 1

        row_candidates.extend(
            protected_swing_candidates(
                setup,
                confirmed_swings,
                current_close=close,
                current_index=index,
                current_time=row_time_iso(row),
                selected_timeframe=selected_timeframe,
            )
        )

        bos_candidate, ob_candidate = bos_and_ob_candidates(
            setup,
            rows,
            confirmed_swings,
            current_index=index,
            current_close=close,
            selected_timeframe=selected_timeframe,
            broken_in_direction=broken_in_direction,
        )
        if bos_candidate is not None:
            row_candidates.append(bos_candidate)
        if ob_candidate is not None:
            row_candidates.append(ob_candidate)

        if choch_against_trade(
            setup,
            confirmed_swings,
            current_index=index,
            current_close=close,
            broken_against_trade=broken_against_trade,
        ):
            features.diagnostic_counts["CHOCH_AGAINST_TRADE"] += 1

        displacement = displacement_halfback_candidate(
            setup,
            row,
            open_=open_,
            close=close,
            body_history=body_history,
            selected_timeframe=selected_timeframe,
            current_index=index,
        )
        if displacement is not None:
            row_candidates.append(displacement)

        row_candidates.extend(
            fvg_candidates(
                setup,
                rows,
                current_index=index,
                selected_timeframe=selected_timeframe,
            )
        )

        row_candidates.extend(
            liquidity_run_candidates(
                setup,
                row,
                high=high,
                low=low,
                close=close,
                current_index=index,
                prior_high=prior_high,
                prior_low=prior_low,
                equal_high_levels=[level for level, count in equal_high_counts.items() if count >= 2],
                equal_low_levels=[level for level, count in equal_low_counts.items() if count >= 2],
                selected_timeframe=selected_timeframe,
            )
        )

        if prior_high is not None and high > prior_high and close <= prior_high:
            features.diagnostic_counts["FAILED_BREAK_RECLAIM_HIGH"] += 1
            features.diagnostic_counts["SWEEP_AND_RECLAIM"] += 1
        if prior_low is not None and low < prior_low and close >= prior_low:
            features.diagnostic_counts["FAILED_BREAK_RECLAIM_LOW"] += 1
            features.diagnostic_counts["SWEEP_AND_RECLAIM"] += 1

        for candidate in row_candidates:
            if candidate.floor_r >= -EPS:
                features.candidates_by_index[index].append(candidate)
                features.candidate_counts[candidate.selector_id] += 1

        body_history.append(abs(close - open_))
        prior_high = high if prior_high is None else max(prior_high, high)
        prior_low = low if prior_low is None else min(prior_low, low)
        equal_high_counts[round(high, decimals)] += 1
        equal_low_counts[round(low, decimals)] += 1

    return features


def confirmed_swings_as_of(
    rows: Sequence[Mapping[str, Any]],
    *,
    current_index: int,
    min_bars: int = 2,
) -> list[SwingPoint]:
    swings: list[SwingPoint] = []
    for confirmation_index in range(len(rows)):
        if confirmation_index > current_index:
            break
        swings.extend(newly_confirmed_swings(rows, current_index=confirmation_index, min_bars=min_bars))
    return swings


def newly_confirmed_swings(
    rows: Sequence[Mapping[str, Any]],
    *,
    current_index: int,
    min_bars: int = 2,
) -> list[SwingPoint]:
    pivot_index = current_index - min_bars
    if pivot_index < min_bars or current_index >= len(rows):
        return []
    pivot = bar_ohlc(rows[pivot_index])
    if pivot is None:
        return []
    _pivot_open, pivot_high, pivot_low, _pivot_close = pivot
    left_rows = rows[pivot_index - min_bars : pivot_index]
    right_rows = rows[pivot_index + 1 : pivot_index + min_bars + 1]
    if len(left_rows) != min_bars or len(right_rows) != min_bars:
        return []
    left_highs, left_lows = row_highs_lows(left_rows)
    right_highs, right_lows = row_highs_lows(right_rows)
    if len(left_highs) != min_bars or len(right_highs) != min_bars:
        return []
    swings: list[SwingPoint] = []
    pivot_time = row_time_iso(rows[pivot_index])
    confirmed_time = row_time_iso(rows[current_index])
    if pivot_high > max([*left_highs, *right_highs]):
        swings.append(
            SwingPoint(
                "high",
                pivot_high,
                pivot_index,
                pivot_time,
                current_index,
                confirmed_time,
            )
        )
    if pivot_low < min([*left_lows, *right_lows]):
        swings.append(
            SwingPoint(
                "low",
                pivot_low,
                pivot_index,
                pivot_time,
                current_index,
                confirmed_time,
            )
        )
    return swings


def protected_swing_candidates(
    setup: MechanicalSetup,
    swings: Sequence[SwingPoint],
    *,
    current_close: float,
    current_index: int,
    current_time: str | None,
    selected_timeframe: str,
) -> list[StructuralLevelCandidate]:
    wanted = "low" if setup.side == "LONG" else "high"
    for swing in sorted((item for item in swings if item.swing_type == wanted), key=lambda item: item.index, reverse=True):
        candidate = candidate_from_price(
            setup,
            selector_id="PROTECTED_CONFIRMED_SWING",
            event_type=f"confirmed_swing_{wanted}",
            price=swing.price,
            current_close=current_close,
            source_index=swing.index,
            source_time=swing.time,
            confirmed_index=current_index,
            confirmed_time=current_time,
            selected_timeframe=selected_timeframe,
            metadata={"swing_confirmed_index": swing.confirmed_index, "swing_confirmed_time": swing.confirmed_time},
        )
        if candidate is not None:
            return [candidate]
    return []


def bos_and_ob_candidates(
    setup: MechanicalSetup,
    rows: Sequence[Mapping[str, Any]],
    swings: Sequence[SwingPoint],
    *,
    current_index: int,
    current_close: float,
    selected_timeframe: str,
    broken_in_direction: set[tuple[str, int]],
) -> tuple[StructuralLevelCandidate | None, StructuralLevelCandidate | None]:
    if setup.side == "LONG":
        candidates = [
            swing
            for swing in swings
            if swing.swing_type == "high"
            and current_close > swing.price
            and ("high", swing.index) not in broken_in_direction
        ]
    else:
        candidates = [
            swing
            for swing in swings
            if swing.swing_type == "low"
            and current_close < swing.price
            and ("low", swing.index) not in broken_in_direction
        ]
    if not candidates:
        return None, None
    broken = max(candidates, key=lambda swing: swing.index)
    broken_in_direction.add((broken.swing_type, broken.index))
    current_time = row_time_iso(rows[current_index])
    bos = candidate_from_price(
        setup,
        selector_id="BOS_BROKEN_LEVEL",
        event_type=f"bos_break_{broken.swing_type}",
        price=broken.price,
        current_close=current_close,
        source_index=broken.index,
        source_time=broken.time,
        confirmed_index=current_index,
        confirmed_time=current_time,
        selected_timeframe=selected_timeframe,
        metadata={"break_index": current_index},
    )
    ob_price = last_opposing_candle_boundary(setup, rows, before_index=current_index)
    ob = None
    if ob_price is not None:
        ob = candidate_from_price(
            setup,
            selector_id="OB_PROTECTIVE_BOUNDARY",
            event_type="fresh_ob_boundary_after_bos",
            price=ob_price[0],
            current_close=current_close,
            source_index=ob_price[1],
            source_time=row_time_iso(rows[ob_price[1]]),
            confirmed_index=current_index,
            confirmed_time=current_time,
            selected_timeframe=selected_timeframe,
            metadata={"causing_bos_index": current_index},
        )
    return bos, ob


def choch_against_trade(
    setup: MechanicalSetup,
    swings: Sequence[SwingPoint],
    *,
    current_index: int,
    current_close: float,
    broken_against_trade: set[tuple[str, int]],
) -> bool:
    if setup.side == "LONG":
        candidates = [
            swing
            for swing in swings
            if swing.swing_type == "low"
            and current_close < swing.price
            and ("low", swing.index) not in broken_against_trade
        ]
    else:
        candidates = [
            swing
            for swing in swings
            if swing.swing_type == "high"
            and current_close > swing.price
            and ("high", swing.index) not in broken_against_trade
        ]
    if not candidates:
        return False
    broken = max(candidates, key=lambda swing: swing.index)
    broken_against_trade.add((broken.swing_type, broken.index))
    return current_index >= broken.confirmed_index


def displacement_halfback_candidate(
    setup: MechanicalSetup,
    row: Mapping[str, Any],
    *,
    open_: float,
    close: float,
    body_history: Sequence[float],
    selected_timeframe: str,
    current_index: int,
) -> StructuralLevelCandidate | None:
    if len(body_history) < 3:
        return None
    avg_body = sum(body_history) / len(body_history)
    if avg_body <= 0:
        return None
    body = abs(close - open_)
    directional = close > open_ if setup.side == "LONG" else close < open_
    if not directional or body < 1.5 * avg_body:
        return None
    price = (open_ + close) / 2.0
    return candidate_from_price(
        setup,
        selector_id="DISPLACEMENT_HALFBACK",
        event_type="displacement_body_halfback",
        price=price,
        current_close=close,
        source_index=current_index,
        source_time=row_time_iso(row),
        confirmed_index=current_index,
        confirmed_time=row_time_iso(row),
        selected_timeframe=selected_timeframe,
        metadata={"body": body, "avg_prior_body": avg_body, "threshold_ratio": 1.5},
    )


def fvg_candidates(
    setup: MechanicalSetup,
    rows: Sequence[Mapping[str, Any]],
    *,
    current_index: int,
    selected_timeframe: str,
) -> list[StructuralLevelCandidate]:
    if current_index < 2:
        return []
    left = bar_ohlc(rows[current_index - 2])
    current = bar_ohlc(rows[current_index])
    if left is None or current is None:
        return []
    _left_open, left_high, left_low, _left_close = left
    _cur_open, cur_high, cur_low, cur_close = current
    source_time = row_time_iso(rows[current_index])
    candidates: list[StructuralLevelCandidate] = []
    if setup.side == "LONG" and cur_low > left_high:
        midpoint = (cur_low + left_high) / 2.0
        edge = left_high
        for selector_id, price in (("FVG_MIDPOINT", midpoint), ("FVG_PROTECTIVE_EDGE", edge)):
            candidate = candidate_from_price(
                setup,
                selector_id=selector_id,
                event_type="bullish_fvg",
                price=price,
                current_close=cur_close,
                source_index=current_index,
                source_time=source_time,
                confirmed_index=current_index,
                confirmed_time=source_time,
                selected_timeframe=selected_timeframe,
                metadata={"left_index": current_index - 2, "gap_low": left_high, "gap_high": cur_low},
            )
            if candidate is not None:
                candidates.append(candidate)
    elif setup.side == "SHORT" and cur_high < left_low:
        midpoint = (left_low + cur_high) / 2.0
        edge = left_low
        for selector_id, price in (("FVG_MIDPOINT", midpoint), ("FVG_PROTECTIVE_EDGE", edge)):
            candidate = candidate_from_price(
                setup,
                selector_id=selector_id,
                event_type="bearish_fvg",
                price=price,
                current_close=cur_close,
                source_index=current_index,
                source_time=source_time,
                confirmed_index=current_index,
                confirmed_time=source_time,
                selected_timeframe=selected_timeframe,
                metadata={"left_index": current_index - 2, "gap_low": cur_high, "gap_high": left_low},
            )
            if candidate is not None:
                candidates.append(candidate)
    return candidates


def liquidity_run_candidates(
    setup: MechanicalSetup,
    row: Mapping[str, Any],
    *,
    high: float,
    low: float,
    close: float,
    current_index: int,
    prior_high: float | None,
    prior_low: float | None,
    equal_high_levels: Sequence[float],
    equal_low_levels: Sequence[float],
    selected_timeframe: str,
) -> list[StructuralLevelCandidate]:
    output: list[StructuralLevelCandidate] = []
    current_time = row_time_iso(row)
    if setup.side == "LONG":
        if prior_high is not None and close > prior_high:
            candidate = candidate_from_price(
                setup,
                selector_id="PATH_HIGH_LOW_RUN",
                event_type="prior_path_high_run",
                price=prior_high,
                current_close=close,
                source_index=current_index,
                source_time=current_time,
                confirmed_index=current_index,
                confirmed_time=current_time,
                selected_timeframe=selected_timeframe,
                metadata={"current_high": high},
            )
            if candidate is not None:
                output.append(candidate)
        eligible_equal = [level for level in equal_high_levels if close > level]
        if eligible_equal:
            level = max(eligible_equal)
            candidate = candidate_from_price(
                setup,
                selector_id="EQUAL_HIGH_LOW_RUN",
                event_type="equal_high_run",
                price=level,
                current_close=close,
                source_index=current_index,
                source_time=current_time,
                confirmed_index=current_index,
                confirmed_time=current_time,
                selected_timeframe=selected_timeframe,
                metadata={"equal_level": level},
            )
            if candidate is not None:
                output.append(candidate)
    else:
        if prior_low is not None and close < prior_low:
            candidate = candidate_from_price(
                setup,
                selector_id="PATH_HIGH_LOW_RUN",
                event_type="prior_path_low_run",
                price=prior_low,
                current_close=close,
                source_index=current_index,
                source_time=current_time,
                confirmed_index=current_index,
                confirmed_time=current_time,
                selected_timeframe=selected_timeframe,
                metadata={"current_low": low},
            )
            if candidate is not None:
                output.append(candidate)
        eligible_equal = [level for level in equal_low_levels if close < level]
        if eligible_equal:
            level = min(eligible_equal)
            candidate = candidate_from_price(
                setup,
                selector_id="EQUAL_HIGH_LOW_RUN",
                event_type="equal_low_run",
                price=level,
                current_close=close,
                source_index=current_index,
                source_time=current_time,
                confirmed_index=current_index,
                confirmed_time=current_time,
                selected_timeframe=selected_timeframe,
                metadata={"equal_level": level},
            )
            if candidate is not None:
                output.append(candidate)
    return output


def candidate_from_price(
    setup: MechanicalSetup,
    *,
    selector_id: str,
    event_type: str,
    price: float,
    current_close: float,
    source_index: int,
    source_time: str | None,
    confirmed_index: int,
    confirmed_time: str | None,
    selected_timeframe: str,
    metadata: Mapping[str, Any] | None = None,
) -> StructuralLevelCandidate | None:
    sl_dist = abs(float(setup.entry) - float(setup.sl))
    if sl_dist <= 0:
        return None
    price = float(price)
    if setup.side == "LONG":
        if price < float(setup.entry) - EPS or price > current_close + EPS:
            return None
        floor_r = (price - float(setup.entry)) / sl_dist
    else:
        if price > float(setup.entry) + EPS or price < current_close - EPS:
            return None
        floor_r = (float(setup.entry) - price) / sl_dist
    if floor_r < -EPS:
        return None
    return StructuralLevelCandidate(
        selector_id=selector_id,
        family=STRUCTURAL_SELECTOR_FAMILIES[selector_id],
        event_type=event_type,
        price=price,
        floor_r=float(floor_r),
        source_index=source_index,
        source_time=source_time,
        confirmed_index=confirmed_index,
        confirmed_time=confirmed_time,
        source_timeframe=selected_timeframe,
        metadata=dict(metadata or {}),
    )


def last_opposing_candle_boundary(
    setup: MechanicalSetup,
    rows: Sequence[Mapping[str, Any]],
    *,
    before_index: int,
    lookback: int = 10,
) -> tuple[float, int] | None:
    start = max(0, before_index - lookback)
    for index in range(before_index - 1, start - 1, -1):
        ohlc = bar_ohlc(rows[index])
        if ohlc is None:
            continue
        open_, high, low, close = ohlc
        if setup.side == "LONG" and close < open_:
            return low, index
        if setup.side == "SHORT" and close > open_:
            return high, index
    return None


def bar_ohlc(row: Mapping[str, Any]) -> tuple[float, float, float, float] | None:
    try:
        return float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"])
    except (KeyError, TypeError, ValueError):
        return None


def row_highs_lows(rows: Sequence[Mapping[str, Any]]) -> tuple[list[float], list[float]]:
    highs: list[float] = []
    lows: list[float] = []
    for row in rows:
        ohlc = bar_ohlc(row)
        if ohlc is None:
            continue
        _open, high, low, _close = ohlc
        highs.append(high)
        lows.append(low)
    return highs, lows


def infer_price_decimals(rows: Sequence[Mapping[str, Any]]) -> int:
    max_decimals = 0
    for row in rows[:200]:
        for field in ("open", "high", "low", "close"):
            value = row.get(field)
            if value is None:
                continue
            text = f"{float(value):.10f}".rstrip("0").rstrip(".")
            if "." in text:
                max_decimals = max(max_decimals, len(text.split(".", 1)[1]))
    return min(max_decimals, 5)


def candidate_record(candidate: StructuralLevelCandidate) -> dict[str, Any]:
    return {
        "selector_id": candidate.selector_id,
        "family": candidate.family,
        "event_type": candidate.event_type,
        "price": round(candidate.price, 10),
        "floor_r": round(candidate.floor_r, 6),
        "source_index": candidate.source_index,
        "source_time": candidate.source_time,
        "confirmed_index": candidate.confirmed_index,
        "confirmed_time": candidate.confirmed_time,
        "source_timeframe": candidate.source_timeframe,
        "metadata": dict(candidate.metadata),
    }


def run_path_scaling_v2_levels(
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

    policies = registered_v2_policies()
    structural_policies = [policy for policy in policies if isinstance(policy, StructuralPolicy)]
    policy_by_id = {policy.variant_id: policy for policy in policies}
    cost_scenarios = [float(value) for value in cost_scenarios_r]
    stats: dict[str, VariantStats] = {policy.variant_id: VariantStats() for policy in policies}
    group_stats: dict[tuple[str, str], VariantStats] = defaultdict(VariantStats)
    cohort_stats: dict[tuple[str, str, str], VariantStats] = defaultdict(VariantStats)
    stress_stats: dict[tuple[str, str], StressStats] = defaultdict(StressStats)
    pairwise_vs_j46: dict[str, PairwiseDeltaStats] = defaultdict(PairwiseDeltaStats)
    pairwise_vs_fixed: dict[str, PairwiseDeltaStats] = defaultdict(PairwiseDeltaStats)
    selector_fire_stats: dict[tuple[Any, ...], SelectorFireStats] = defaultdict(SelectorFireStats)
    structural_census: Counter[tuple[str, str, str]] = Counter()
    structural_diagnostics: Counter[tuple[str, str]] = Counter()
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
            groups = groups_for_key(key, role)

            rows_by_tf: dict[str, list[dict[str, Any]]] = {}
            window: PathWindow | None = None
            features: StructuralPathFeatures | None = None
            if row.get("mechanical_setup_status") == "OK" and setup is not None:
                setup_ok_rows += 1
                rows_by_tf = load_path_rows_by_timeframe(
                    roots=selected_data_dirs,
                    symbol=event.symbol,
                    cache=path_cache,
                )
                window = select_path_window(
                    setup,
                    rows_by_tf,
                    pending_expiry_bars=DEFAULT_MECHANICAL_MAX_HOLD_BARS,
                )
                coverage.add(window)
                features = build_structural_path_features(
                    setup,
                    window.selected_rows,
                    selected_timeframe=window.selected_timeframe,
                )
                for selector_id, count in features.candidate_counts.items():
                    structural_census[(window.selected_timeframe, setup.side, selector_id)] += int(count)
                for diagnostic, count in features.diagnostic_counts.items():
                    structural_diagnostics[(window.selected_timeframe, diagnostic)] += int(count)
            if setup is not None and not any(rows_by_tf.values()):
                no_data_rows += 1

            event_outcomes: dict[str, MtfPathOutcome | PathOutcome] = {}
            for policy in policies:
                if setup is not None and row.get("mechanical_setup_status") == "OK":
                    if isinstance(policy, StructuralPolicy):
                        outcome = resolve_structural_policy_outcome(
                            setup,
                            window,
                            policy=policy,
                            features=features,
                        )
                    else:
                        outcome = resolve_policy_outcome_mtf(
                            setup,
                            rows_by_tf,
                            policy=policy,
                            preselected_window=window,
                        )
                else:
                    base = PathOutcome(
                        variant_id=policy.variant_id,
                        outcome="SETUP_NOT_REFINABLE",
                        gross_r=None,
                        bars_to_fill=0,
                        bars_in_trade=0,
                        exit_time=None,
                        skip_reason=str(row.get("mechanical_skip_reason") or "missing_setup"),
                    )
                    outcome = wrap_m15_outcome(base, selected_timeframe="M15")

                event_outcomes[policy.variant_id] = outcome
                stats[policy.variant_id].add(outcome, cost_scenarios=cost_scenarios)
                cohort_stats[(policy.variant_id, key, role)].add(outcome, cost_scenarios=cost_scenarios)
                for group in groups:
                    group_stats[(policy.variant_id, group)].add(outcome, cost_scenarios=cost_scenarios)
                    stress_stats[(policy.variant_id, group)].add(outcome)
                if outcome.outcome in RESOLVED_OUTCOMES and outcome.gross_r is not None:
                    month_returns[month][policy.variant_id] += float(outcome.gross_r)

                if isinstance(policy, StructuralPolicy) and outcome.locks_triggered:
                    for lock in outcome.locks_triggered:
                        selector_key = (
                            policy.variant_id,
                            lock.get("selector_id"),
                            lock.get("family"),
                            outcome.selected_timeframe,
                            row.get("mechanical_side"),
                            row.get("symbol"),
                            row.get("session"),
                            role,
                        )
                        selector_fire_stats[selector_key].add(outcome)

                event_record = path_event_record_v2(
                    row=row,
                    raw_cohort_key=key,
                    role=role,
                    policy=policy,
                    outcome=outcome,
                    cost_scenarios_r=cost_scenarios,
                )
                if len(first_events) < 10:
                    first_events.append(event_record)
                if event_handle is not None:
                    event_handle.write(json.dumps(event_record, sort_keys=True) + "\n")
                    event_rows_written += 1

            j46_outcome = event_outcomes.get("J46_J49_ONLY")
            fixed_outcome = event_outcomes.get("PATH_LOCK_HALF_GAIN_V0")
            for policy in structural_policies:
                structural_outcome = event_outcomes.get(policy.variant_id)
                pairwise_vs_j46[policy.variant_id].add(baseline=j46_outcome, candidate=structural_outcome)
                pairwise_vs_fixed[policy.variant_id].add(baseline=fixed_outcome, candidate=structural_outcome)
    finally:
        if event_handle is not None:
            event_handle.close()

    variant_summary = [
        variant_summary_row(policy, stats[policy.variant_id], cost_scenarios=cost_scenarios)
        for policy in policies
    ]
    group_summary = build_group_rows(policies, group_stats, cost_scenarios=cost_scenarios)
    cohort_summary = build_cohort_rows(policies, cohort_stats, cost_scenarios=cost_scenarios)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "replay_spec_path": str(Path(spec_path)),
        "replay_spec_sha256": sha256_file(spec_path),
        "ablation_spec_path": DEFAULT_ABLATION_SPEC_PATH,
        "ablation_spec_sha256": sha256_file(DEFAULT_ABLATION_SPEC_PATH),
        "v2_spec_path": DEFAULT_V2_SPEC_PATH,
        "v2_spec_sha256": sha256_file(DEFAULT_V2_SPEC_PATH),
        "v2_protocol_path": DEFAULT_V2_PROTOCOL_PATH,
        "v2_protocol_sha256": sha256_file(DEFAULT_V2_PROTOCOL_PATH),
        "v1_failure_forensics_path": DEFAULT_V1_FORENSICS_PATH,
        "v1_failure_forensics_sha256": sha256_file(DEFAULT_V1_FORENSICS_PATH),
        "code_commit": git_commit_or_unknown(),
        "promotion_verdict_allowed": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "promotion_blocked_reason": "Same-dataset historical raw-OHLC structural-level exit-policy ablation.",
        "research_boundary": [
            "Research/tooling only",
            "No live trading logic changes",
            "No prompt edits",
            "No parameter optimization",
            "No paid AI/API calls",
            "No reentry in V2",
        ],
        "mtf_resolution_policy": {
            "decision_clock": "M15 candle close UTC",
            "path_timeframe_hierarchy": ["M1", "M5", "M15"],
            "lower_tf_start_rule": "strictly greater than setup candle close",
            "fallback": "M1 if available, else M5, else M15",
            "time_stop_unit": "registered M15 bars converted to elapsed UTC time for M1/M5 path rows",
        },
        "structural_selector_policy": {
            "swing_confirmation_lag_bars": 2,
            "displacement_threshold": "body >= 1.5x prior closed-body average",
            "candidate_floor_rule": "floor must be non-negative R, behind current close, and improve pending stop",
            "activation_rule": "new structural floors activate on the next selected path row",
            "multiple_candidates_rule": "highest floor R wins",
        },
        "same_bar_policy": {
            "fill_and_exit_same_selected_row": "SAME_BAR unresolved",
            "structural_locks_on_fill_row": "not evaluated; structural locks require an already-filled trade",
            "stress_treatments": ["exclude_unresolved", "samebar_breakeven", "samebar_pessimistic"],
        },
        "cost_model": {
            "unit": "R per completed round turn",
            "cost_scenarios_r": cost_scenarios,
            "actual_commission_spread_source": "not reliably available in historical OHLC; reported as sensitivity, not measured cost",
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
        "policies": [policy_row_any(policy) for policy in policies],
        "variant_summary": variant_summary,
        "group_summary": group_summary,
        "cohort_summary": cohort_summary,
        "samebar_stress_summary": build_samebar_stress_rows(
            stress_stats,
            policies=policies,
            cost_r=0.05 if 0.05 in set(cost_scenarios) else cost_scenarios[0],
        ),
        "selector_fire_summary": selector_fire_rows(selector_fire_stats),
        "structural_event_census": structural_census_rows(structural_census),
        "structural_diagnostic_census": structural_diagnostic_rows(structural_diagnostics),
        "pairwise_vs_j46": pairwise_rows(pairwise_vs_j46, baseline_variant="J46_J49_ONLY"),
        "pairwise_vs_fixed_r": pairwise_rows(pairwise_vs_fixed, baseline_variant="PATH_LOCK_HALF_GAIN_V0"),
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


def policy_row_any(policy: ExitPolicy | StructuralPolicy) -> dict[str, Any]:
    if isinstance(policy, StructuralPolicy):
        return {
            "variant_id": policy.variant_id,
            "family": policy.family,
            "description": policy.description,
            "final_target_r": policy.final_target_r,
            "time_stop_bars": policy.time_stop_bars,
            "pending_expiry_bars": policy.pending_expiry_bars,
            "use_setup_tp": policy.use_setup_tp,
            "lock_steps": [],
            "structural_selectors": list(policy.selector_ids),
        }
    return policy_row(policy)


def path_event_record_v2(
    *,
    row: Mapping[str, Any],
    raw_cohort_key: str,
    role: str,
    policy: ExitPolicy | StructuralPolicy,
    outcome: MtfPathOutcome | PathOutcome,
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
        "family": policy.family,
        "mechanical_side": row.get("mechanical_side"),
        "mechanical_entry": row.get("mechanical_entry"),
        "mechanical_sl": row.get("mechanical_sl"),
        "mechanical_tp": row.get("mechanical_tp"),
        "selected_timeframe": getattr(outcome, "selected_timeframe", "M15"),
        "fallback_reason": getattr(outcome, "fallback_reason", None),
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
        "path_rows_to_fill": getattr(outcome, "path_rows_to_fill", None),
        "path_rows_in_trade": getattr(outcome, "path_rows_in_trade", None),
        "exit_time": outcome.exit_time,
        "mfe_r": outcome.mfe_r,
        "mae_r": outcome.mae_r,
        "max_locked_floor_r": outcome.max_locked_floor_r,
        "locks_triggered": outcome.locks_triggered,
        "skip_reason": outcome.skip_reason,
    }


def build_samebar_stress_rows(
    stress_stats: Mapping[tuple[str, str], StressStats],
    *,
    policies: Sequence[ExitPolicy | StructuralPolicy],
    cost_r: float,
) -> list[dict[str, Any]]:
    structural_ids = [policy.variant_id for policy in policies if isinstance(policy, StructuralPolicy)]
    fixed_ids = [policy.variant_id for policy in policies if str(policy.variant_id).startswith("PATH_LOCK")]
    rows: list[dict[str, Any]] = []
    for treatment in ("exclude_unresolved", "samebar_breakeven", "samebar_pessimistic"):
        for group in GROUPS:
            j46_n, j46_mean = stress_stats.get(("J46_J49_ONLY", group), StressStats()).mean(treatment, cost_r=cost_r)
            best_struct = best_stress_variant(stress_stats, structural_ids, group=group, treatment=treatment, cost_r=cost_r)
            best_fixed = best_stress_variant(stress_stats, fixed_ids, group=group, treatment=treatment, cost_r=cost_r)
            rows.append(
                {
                    "treatment": treatment,
                    "group": group,
                    "j46_net_mean_r_cost_0.05": j46_mean,
                    "j46_n": j46_n,
                    "best_structural_variant": best_struct.get("variant_id"),
                    "best_structural_net_mean_r_cost_0.05": best_struct.get("net_mean"),
                    "best_structural_n": best_struct.get("n"),
                    "best_structural_minus_j46": none_safe_delta(best_struct.get("net_mean"), j46_mean),
                    "best_fixed_r_variant": best_fixed.get("variant_id"),
                    "best_fixed_r_net_mean_r_cost_0.05": best_fixed.get("net_mean"),
                    "best_fixed_r_n": best_fixed.get("n"),
                    "best_structural_minus_best_fixed_r": none_safe_delta(
                        best_struct.get("net_mean"),
                        best_fixed.get("net_mean"),
                    ),
                }
            )
    return rows


def best_stress_variant(
    stress_stats: Mapping[tuple[str, str], StressStats],
    variant_ids: Sequence[str],
    *,
    group: str,
    treatment: str,
    cost_r: float,
) -> dict[str, Any]:
    best: dict[str, Any] = {}
    for variant_id in variant_ids:
        n, mean = stress_stats.get((variant_id, group), StressStats()).mean(treatment, cost_r=cost_r)
        if mean is None:
            continue
        if not best or float(mean) > float(best.get("net_mean") or -999.0):
            best = {"variant_id": variant_id, "net_mean": mean, "n": n}
    return best


def pairwise_rows(stats: Mapping[str, PairwiseDeltaStats], *, baseline_variant: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for variant_id, state in sorted(stats.items()):
        n = state.paired_resolved_n
        rows.append(
            {
                "candidate_variant": variant_id,
                "baseline_variant": baseline_variant,
                "paired_resolved_n": n,
                "baseline_mean_r": round(state.baseline_sum_r / n, 6) if n else None,
                "candidate_mean_r": round(state.candidate_sum_r / n, 6) if n else None,
                "mean_delta_candidate_minus_baseline": round(state.delta_sum_r / n, 6) if n else None,
                "sum_delta_candidate_minus_baseline": round(state.delta_sum_r, 6),
                "candidate_better_rate": rate_or_none(state.candidate_better_n, n),
                "baseline_better_rate": rate_or_none(state.baseline_better_n, n),
                "candidate_better_n": state.candidate_better_n,
                "baseline_better_n": state.baseline_better_n,
                "tie_n": state.tie_n,
                "baseline_positive_n": state.baseline_positive_n,
                "candidate_positive_n": state.candidate_positive_n,
                "both_positive_n": state.both_positive_n,
                "both_nonpositive_n": state.both_nonpositive_n,
                "candidate_lock_triggered_n": state.candidate_lock_triggered_n,
                "candidate_lock_triggered_rate": rate_or_none(state.candidate_lock_triggered_n, n),
                "truncation_n": state.truncation_n,
                "truncation_lost_r": round(state.truncation_lost_r, 6),
                "truncation_lost_r_per_pair": round(state.truncation_lost_r / n, 6) if n else None,
                "rescued_baseline_nonpositive_n": state.rescued_baseline_nonpositive_n,
                "rescued_to_positive_n": state.rescued_to_positive_n,
                "candidate_made_positive_nonpositive_n": state.candidate_made_positive_nonpositive_n,
            }
        )
    return rows


def selector_fire_rows(stats: Mapping[tuple[Any, ...], SelectorFireStats]) -> list[dict[str, Any]]:
    rows = []
    for key, state in stats.items():
        variant_id, selector_id, family, timeframe, side, symbol, session, role = key
        rows.append(
            {
                "variant_id": variant_id,
                "selector_id": selector_id,
                "family": family,
                "selected_timeframe": timeframe,
                "side": side,
                "symbol": symbol,
                "session": session,
                "role": role,
                "fires": state.fires,
                "resolved_n": state.resolved_n,
                "gross_mean_r": round(state.gross_sum_r / state.resolved_n, 6) if state.resolved_n else None,
                "outcomes": dict(sorted(state.outcomes.items())),
            }
        )
    return sorted(rows, key=lambda row: (-int(row["fires"]), str(row["variant_id"]), str(row["selector_id"])))


def structural_census_rows(census: Counter[tuple[str, str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "selected_timeframe": timeframe,
            "side": side,
            "selector_id": selector_id,
            "family": STRUCTURAL_SELECTOR_FAMILIES.get(selector_id),
            "candidate_count": count,
        }
        for (timeframe, side, selector_id), count in sorted(census.items())
    ]


def structural_diagnostic_rows(census: Counter[tuple[str, str]]) -> list[dict[str, Any]]:
    return [
        {"selected_timeframe": timeframe, "diagnostic_event": event, "count": count}
        for (timeframe, event), count in sorted(census.items())
    ]


def none_safe_delta(left: Any, right: Any) -> float | None:
    if left is None or right is None:
        return None
    try:
        return round(float(left) - float(right), 6)
    except (TypeError, ValueError):
        return None


def synthesize(summary: Mapping[str, Any]) -> list[dict[str, str]]:
    rows = list(summary.get("variant_summary") or [])
    structural = [row for row in rows if str(row.get("variant_id", "")).startswith("STRUCT_")]
    j46 = next((row for row in rows if row.get("variant_id") == "J46_J49_ONLY"), {})
    fixed = [row for row in rows if str(row.get("variant_id", "")).startswith("PATH_LOCK")]
    best_struct = max(structural, key=lambda row: float(row.get("net_mean_r_cost_0.05") or -999.0), default={})
    best_fixed = max(fixed, key=lambda row: float(row.get("net_mean_r_cost_0.05") or -999.0), default={})
    best_overall = max(rows, key=lambda row: float(row.get("net_mean_r_cost_0.05") or -999.0), default={})
    struct_delta = none_safe_delta(best_struct.get("net_mean_r_cost_0.05"), j46.get("net_mean_r_cost_0.05"))
    fixed_delta = none_safe_delta(best_fixed.get("net_mean_r_cost_0.05"), j46.get("net_mean_r_cost_0.05"))
    stress_all = {
        (row.get("treatment"), row.get("group")): row for row in summary.get("samebar_stress_summary") or []
    }
    pessimistic = stress_all.get(("samebar_pessimistic", "all_enabled"), {})
    target_delta = group_delta(summary, "target_cohorts", lock_prefix="STRUCT_", baseline_variant="J46_J49_ONLY")
    selector_rows = summary.get("selector_fire_summary") or []
    top_selector = selector_rows[0] if selector_rows else {}
    return [
        {
            "question": "Which V2 structural policy leads after 0.05R cost?",
            "answer": (
                f"{best_struct.get('variant_id')} with net_mean_r_cost_0.05="
                f"{best_struct.get('net_mean_r_cost_0.05')}."
            ),
        },
        {
            "question": "Did the best structural policy beat J46 globally?",
            "answer": f"Best structural minus J46 at 0.05R cost = {struct_delta}.",
        },
        {
            "question": "Did structural selection beat the best fixed-R lock control?",
            "answer": f"Best fixed-R minus J46 = {fixed_delta}; compare best structural minus J46 = {struct_delta}.",
        },
        {
            "question": "Which variant leads overall?",
            "answer": (
                f"{best_overall.get('variant_id')} with net_mean_r_cost_0.05="
                f"{best_overall.get('net_mean_r_cost_0.05')}."
            ),
        },
        {
            "question": "Did the headline structural result survive pessimistic same-bar stress?",
            "answer": (
                "All-enabled pessimistic best structural minus J46 = "
                f"{pessimistic.get('best_structural_minus_j46')}."
            ),
        },
        {
            "question": "Where did structural selection look most interesting?",
            "answer": f"Target-cohort best structural minus J46 at 0.05R cost = {target_delta}.",
        },
        {
            "question": "Which selector fired most often?",
            "answer": (
                f"{top_selector.get('selector_id')} under {top_selector.get('variant_id')} "
                f"with fires={top_selector.get('fires')}."
            ),
        },
        {
            "question": "Does this promote live logic?",
            "answer": "No. V2 is same-dataset historical research and remains NO_PROMOTION_VERDICT.",
        },
    ]


def ambiguity_ledger(summary: Mapping[str, Any]) -> list[dict[str, str]]:
    coverage = summary.get("coverage_diagnostics") or {}
    stress = {
        (row.get("treatment"), row.get("group")): row for row in summary.get("samebar_stress_summary") or []
    }
    pessimistic = stress.get(("samebar_pessimistic", "all_enabled"), {})
    rows = summary.get("variant_summary") or []
    samebar_total = sum(int((row.get("outcomes") or {}).get("SAME_BAR", 0)) for row in rows)
    return [
        {
            "item": "Cost model",
            "status": "SENSITIVITY_NOT_MEASURED_COST",
            "detail": "Historical OHLC does not contain reliable commission/spread/slippage; report uses R-cost sensitivity.",
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
            "status": "QUANTIFIED",
            "detail": (
                f"Total SAME_BAR rows across all variants={samebar_total}; all-enabled pessimistic best structural "
                f"minus J46={pessimistic.get('best_structural_minus_j46')}."
            ),
        },
        {
            "item": "Future-swing leakage",
            "status": "RULED_OUT_BY_SELECTOR_RULE",
            "detail": "Confirmed swings are unavailable until two later selected-timeframe bars close; tests cover this.",
        },
        {
            "item": "Unimplemented structural catalog",
            "status": "EXPLICITLY_SCOPED",
            "detail": "Breaker, round-number, higher-timeframe composite, and reentry require fresh registered hypotheses.",
        },
        {
            "item": "Promotion",
            "status": "BLOCKED_BY_DESIGN",
            "detail": str(summary.get("promotion_blocked_reason")),
        },
    ]


def opened_questions(summary: Mapping[str, Any]) -> list[dict[str, str]]:
    stress = {
        (row.get("treatment"), row.get("group")): row for row in summary.get("samebar_stress_summary") or []
    }
    headline = stress.get(("exclude_unresolved", "all_enabled"), {})
    pessimistic = stress.get(("samebar_pessimistic", "all_enabled"), {})
    pairwise = summary.get("pairwise_vs_j46") or []
    best_pair = max(
        pairwise,
        key=lambda row: float(row.get("mean_delta_candidate_minus_baseline") or -999.0),
        default={},
    )
    return [
        {
            "question": "Does structural path scaling beat J46 on the registered global metric?",
            "status": "ANSWERED",
            "detail": f"Headline all-enabled best structural minus J46={headline.get('best_structural_minus_j46')}.",
        },
        {
            "question": "Does the same result survive pessimistic same-bar treatment?",
            "status": "ANSWERED",
            "detail": f"Pessimistic all-enabled best structural minus J46={pessimistic.get('best_structural_minus_j46')}.",
        },
        {
            "question": "Does structural selection reduce V1's fixed-R truncation problem?",
            "status": "ANSWERED",
            "detail": (
                f"Best pairwise structural candidate={best_pair.get('candidate_variant')} "
                f"truncation_lost_r={best_pair.get('truncation_lost_r')}, "
                f"rescued_to_positive_n={best_pair.get('rescued_to_positive_n')}."
            ),
        },
        {
            "question": "Can V2 answer breaker, round-number, or reentry hypotheses?",
            "status": "ANSWERED_NO",
            "detail": "Those events require separate registered hypotheses because they add state reconstruction or risk accounting.",
        },
    ]


def next_steps(summary: Mapping[str, Any]) -> list[dict[str, str]]:
    stress = {
        (row.get("treatment"), row.get("group")): row for row in summary.get("samebar_stress_summary") or []
    }
    headline = stress.get(("exclude_unresolved", "all_enabled"), {})
    pessimistic = stress.get(("samebar_pessimistic", "all_enabled"), {})
    head_delta = headline.get("best_structural_minus_j46")
    pess_delta = pessimistic.get("best_structural_minus_j46")
    accepted_for_next_stage = (
        head_delta is not None
        and pess_delta is not None
        and float(head_delta) > 0
        and float(pess_delta) >= 0
    )
    if accepted_for_next_stage:
        return [
            {
                "rank": "1",
                "next_step": "Write a fresh validation hypothesis for the winning structural family",
                "reason": "V2 can only register a later validation run, not promote live logic.",
            },
            {
                "rank": "2",
                "next_step": "Audit concentration by symbol/session/cohort before any V3 design",
                "reason": "A structural result concentrated in one pocket is not a general path-scaling edge.",
            },
        ]
    return [
        {
            "rank": "1",
            "next_step": "Reject or archive V2 structural lock-only as diagnostic evidence",
            "reason": "The registered global and pessimistic same-bar tests did not clear the next-stage gate.",
        },
        {
            "rank": "2",
            "next_step": "Use selector forensics to decide whether a fresh non-lock-only hypothesis is justified",
            "reason": "If a selector rescues losses but still truncates winners, the problem is exit architecture rather than level detection.",
        },
        {
            "rank": "3",
            "next_step": "Do not proceed to reentry without a separate risk-budgeted hypothesis",
            "reason": "V2 contains no composite risk accounting or second-fill cost model.",
        },
    ]


def render_report(summary: Mapping[str, Any]) -> str:
    pbo = summary.get("pbo_diagnostic") or {}
    eff = (summary.get("effective_n_diagnostic") or {}).get("exit_policy_effective_n") or {}
    lines = [
        "# Phase 3 Path Scaling V2 Structural Level Selector",
        "",
        f"**Created UTC:** {summary.get('created_at_utc')}",
        f"**Replay spec:** `{summary.get('replay_spec_path')}`",
        f"**V2 spec:** `{summary.get('v2_spec_path')}`",
        f"**V2 protocol:** `{summary.get('v2_protocol_path')}`",
        f"**V1 forensics:** `{summary.get('v1_failure_forensics_path')}`",
        f"**Promotion verdict:** `{summary.get('promotion_verdict')}`",
        "",
        "## Boundary",
        "",
        "- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.",
        "- V2 uses V1 MTF path resolution and adds structural lock floors only after the trade is already filled.",
        "- Reentry, breaker reconstruction, round-number selectors, and higher-timeframe composite selectors are not tested.",
        "- Costs are reported as R-per-round-turn sensitivity because reliable historical commission/spread/slippage is not present in OHLC.",
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
        "## Direct Answers",
        "",
        markdown_table(summary.get("synthesis") or []),
        "",
        "## MTF Coverage",
        "",
        markdown_table([summary.get("coverage_diagnostics") or {}]),
        "",
        "## Structural Selector Rules",
        "",
        markdown_table([summary.get("structural_selector_policy") or {}]),
        "",
        "## Policies",
        "",
        markdown_table(summary.get("policies") or []),
        "",
        "## Variant Summary",
        "",
        markdown_table(summary.get("variant_summary") or []),
        "",
        "## Same-Bar Stress Summary",
        "",
        markdown_table(summary.get("samebar_stress_summary") or []),
        "",
        "## Group Summary",
        "",
        markdown_table(summary.get("group_summary") or []),
        "",
        "## Cohort Summary",
        "",
        markdown_table(summary.get("cohort_summary") or []),
        "",
        "## Selector Fire Summary",
        "",
        markdown_table(summary.get("selector_fire_summary") or []),
        "",
        "## Structural Event Census",
        "",
        markdown_table(summary.get("structural_event_census") or []),
        "",
        "## Structural Diagnostic Census",
        "",
        markdown_table(summary.get("structural_diagnostic_census") or []),
        "",
        "## Pairwise Versus J46",
        "",
        markdown_table(summary.get("pairwise_vs_j46") or []),
        "",
        "## Pairwise Versus Fixed-R Control",
        "",
        markdown_table(summary.get("pairwise_vs_fixed_r") or []),
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
        "- V2 tests structural lock floors, not new entries, prompt behavior, live execution, or risk-budgeted reentry.",
        "- Structural candidates are generated only from closed post-decision path rows and are activated on the following selected path row.",
        "- Any favorable V2 result can only justify a later registered validation hypothesis; it cannot promote live logic.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(
    summary: Mapping[str, Any],
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    report_path: str | Path = DEFAULT_REPORT_PATH,
) -> tuple[Path, Path]:
    output_dir = Path(output_root) / "path_scaling_v2_structural_levels"
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_path = output_dir / f"raw_ohlc_path_scaling_v2_structural_levels_{stamp}.json"
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
            / "path_scaling_v2_structural_levels"
            / f"raw_ohlc_path_scaling_v2_structural_levels_events_{stamp}.jsonl"
        )
    summary = run_path_scaling_v2_levels(
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
        stress = {
            (row.get("treatment"), row.get("group")): row for row in summary.get("samebar_stress_summary") or []
        }
        print(
            json.dumps(
                {
                    "promotion_verdict": summary.get("promotion_verdict"),
                    "source_scope": summary.get("source_scope"),
                    "take_rows_seen": summary.get("take_rows_seen"),
                    "coverage_diagnostics": summary.get("coverage_diagnostics"),
                    "best_net_cost_0.05": best.get("variant_id"),
                    "best_net_mean_r_cost_0.05": best.get("net_mean_r_cost_0.05"),
                    "headline_best_structural_minus_j46": (
                        stress.get(("exclude_unresolved", "all_enabled"), {}).get("best_structural_minus_j46")
                    ),
                    "pessimistic_best_structural_minus_j46": (
                        stress.get(("samebar_pessimistic", "all_enabled"), {}).get("best_structural_minus_j46")
                    ),
                    "event_log_path": summary.get("event_log_path"),
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
