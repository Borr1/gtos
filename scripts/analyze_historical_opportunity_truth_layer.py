#!/usr/bin/env python3
"""Compress Phase 3 truth-layer rows into cohort diagnostics.

This is a research-only diagnostic pass over the rescued historical
opportunity truth layer. It does not rebuild labels, replay AI calls, tune
entry/SL parameters, or change live trading behavior.
"""

from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.build_external_feed_validation_dataset import TIMEFRAME_MINUTES  # noqa: E402
from scripts.build_historical_opportunity_dataset import (  # noqa: E402
    CandleSeries,
    _find_ohlcv_path,
)
from src.components.external_feeds import ensure_utc, safe_slug, utc_now  # noqa: E402


SCHEMA_VERSION = "historical_opportunity_truth_layer_cohort_diagnostics_v1"
DEFAULT_INPUT_GLOB = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "truth_layer/*_truth_layer_v2_*.jsonl"
)
DEFAULT_OUTPUT_ROOT = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "truth_layer/diagnostics"
)
DEFAULT_REPORT_PATH = (
    "research/phase_3_external_feed_validation/"
    "HISTORICAL_OPPORTUNITY_TRUTH_LAYER_COHORT_DIAGNOSTICS_2026-05-01.md"
)
DEFAULT_DATA_DIRS = (
    "data/mt5_research_exports/phase3_m15_2022_2026_fn_chunked_v1",
    "data/mt5_research_exports/phase3_rescue_all_m1_m5_chunk1_after_maxbars",
    "data/mt5_research_exports/phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1",
)
DEFAULT_M15_HOLD_BARS = 96
PAIR_DELIMITER = "|||"

RESOLVED_OUTCOMES = {"TP", "SL", "TIMEOUT"}
SETUP_OUTCOMES = {"TP", "SL", "TIMEOUT", "NO_ENTRY", "SAME_BAR", "LOWER_TF_GAPPY"}
LOW_CONFIDENCE_VALUES = {"LOW", "NONE"}
ANALYSIS_TIMEFRAMES = {"M1", "M5", "M15"}


@dataclass
class CohortStats:
    rows: int = 0
    setup_rows: int = 0
    high_confidence_rows: int = 0
    high_medium_confidence_rows: int = 0
    high_resolved_n: int = 0
    high_resolved_sum: float = 0.0
    high_wins: int = 0
    high_medium_resolved_n: int = 0
    high_medium_resolved_sum: float = 0.0
    high_medium_wins: int = 0
    all_resolved_n: int = 0
    all_resolved_sum: float = 0.0
    all_wins: int = 0
    outcomes: Counter[str] = field(default_factory=Counter)
    failure_buckets: Counter[str] = field(default_factory=Counter)
    confidence: Counter[str] = field(default_factory=Counter)
    source_timeframes: Counter[str] = field(default_factory=Counter)
    sides: Counter[str] = field(default_factory=Counter)

    def add(self, row: Mapping[str, Any]) -> None:
        self.rows += 1
        outcome = str(row.get("truth_outcome") or "UNKNOWN")
        confidence = str(row.get("truth_confidence") or "UNKNOWN")
        self.outcomes[outcome] += 1
        self.failure_buckets[str(row.get("truth_failure_bucket") or "UNKNOWN")] += 1
        self.confidence[confidence] += 1
        self.source_timeframes[str(row.get("truth_source_timeframe") or "UNKNOWN")] += 1
        self.sides[str(row.get("mechanical_side") or "UNKNOWN")] += 1
        if _is_setup_row(row):
            self.setup_rows += 1
        if confidence == "HIGH":
            self.high_confidence_rows += 1
        if confidence in {"HIGH", "MEDIUM"}:
            self.high_medium_confidence_rows += 1

        realized = _as_float(row.get("truth_realized_r"))
        if realized is None:
            return
        self.all_resolved_n += 1
        self.all_resolved_sum += realized
        if realized > 0:
            self.all_wins += 1
        if confidence == "HIGH":
            self.high_resolved_n += 1
            self.high_resolved_sum += realized
            if realized > 0:
                self.high_wins += 1
        if confidence in {"HIGH", "MEDIUM"}:
            self.high_medium_resolved_n += 1
            self.high_medium_resolved_sum += realized
            if realized > 0:
                self.high_medium_wins += 1

    def as_row(self, key_name: str, key: str) -> dict[str, Any]:
        filled = self.outcomes.get("TP", 0) + self.outcomes.get("SL", 0) + self.outcomes.get("TIMEOUT", 0)
        immediate = self.failure_buckets.get("FAIL_IMMEDIATE_STOP_AFTER_FILL", 0)
        ambiguous = (
            self.outcomes.get("SAME_BAR", 0)
            + self.outcomes.get("LOWER_TF_GAPPY", 0)
            + self.confidence.get("LOW", 0)
        )
        return {
            key_name: key,
            "rows": self.rows,
            "setup_rows": self.setup_rows,
            "resolved_r_n": self.all_resolved_n,
            "mean_r": _mean(self.all_resolved_sum, self.all_resolved_n),
            "win_rate": _rate(self.all_wins, self.all_resolved_n),
            "tp": self.outcomes.get("TP", 0),
            "sl": self.outcomes.get("SL", 0),
            "timeout": self.outcomes.get("TIMEOUT", 0),
            "no_entry": self.outcomes.get("NO_ENTRY", 0),
            "same_bar": self.outcomes.get("SAME_BAR", 0),
            "lower_tf_gappy": self.outcomes.get("LOWER_TF_GAPPY", 0),
            "immediate_stop": immediate,
            "no_entry_rate_setup": _rate(self.outcomes.get("NO_ENTRY", 0), self.setup_rows),
            "sl_rate_filled": _rate(self.outcomes.get("SL", 0), filled),
            "immediate_stop_rate_sl": _rate(immediate, self.outcomes.get("SL", 0)),
            "ambiguity_rate_setup": _rate(ambiguous, self.setup_rows),
            "high_confidence": self.high_confidence_rows,
            "high_medium_confidence": self.high_medium_confidence_rows,
            "high_resolved_n": self.high_resolved_n,
            "high_mean_r": _mean(self.high_resolved_sum, self.high_resolved_n),
            "high_win_rate": _rate(self.high_wins, self.high_resolved_n),
            "high_medium_resolved_n": self.high_medium_resolved_n,
            "high_medium_mean_r": _mean(
                self.high_medium_resolved_sum,
                self.high_medium_resolved_n,
            ),
            "high_medium_win_rate": _rate(
                self.high_medium_wins,
                self.high_medium_resolved_n,
            ),
        }


@dataclass
class PathAnatomyStats:
    no_entry_rows: int = 0
    no_entry_path_n: int = 0
    no_entry_fill_touched_in_path: int = 0
    no_entry_near_025r: int = 0
    no_entry_near_050r: int = 0
    no_entry_near_100r: int = 0
    no_entry_distance_r: list[float] = field(default_factory=list)
    no_entry_proximity_pct: list[float] = field(default_factory=list)
    no_entry_bars_until_nearest: list[int] = field(default_factory=list)
    sl_rows: int = 0
    sl_path_n: int = 0
    immediate_stop_rows: int = 0
    sl_mfe_before_stop_r: list[float] = field(default_factory=list)
    sl_bars_fill_to_stop: list[int] = field(default_factory=list)
    sl_mfe_ge_025r: int = 0
    sl_mfe_ge_050r: int = 0
    sl_mfe_ge_100r: int = 0

    def add_row(self, row: Mapping[str, Any]) -> None:
        outcome = row.get("truth_outcome")
        if outcome == "NO_ENTRY":
            self.no_entry_rows += 1
        if outcome == "SL":
            self.sl_rows += 1
        if row.get("truth_failure_bucket") == "FAIL_IMMEDIATE_STOP_AFTER_FILL":
            self.immediate_stop_rows += 1

    def add_no_entry_metric(self, metric: Mapping[str, Any] | None) -> None:
        if not metric or not metric.get("path_available"):
            return
        self.no_entry_path_n += 1
        if metric.get("fill_touched_in_path"):
            self.no_entry_fill_touched_in_path += 1
        distance_r = _as_float(metric.get("closest_distance_r"))
        proximity = _as_float(metric.get("entry_proximity_of_sl_distance"))
        bars = _as_int(metric.get("bars_until_nearest"))
        if distance_r is not None:
            self.no_entry_distance_r.append(distance_r)
            if distance_r <= 0.25:
                self.no_entry_near_025r += 1
            if distance_r <= 0.50:
                self.no_entry_near_050r += 1
            if distance_r <= 1.00:
                self.no_entry_near_100r += 1
        if proximity is not None:
            self.no_entry_proximity_pct.append(proximity)
        if bars is not None:
            self.no_entry_bars_until_nearest.append(bars)

    def add_sl_metric(self, metric: Mapping[str, Any] | None) -> None:
        if not metric or not metric.get("path_available"):
            return
        self.sl_path_n += 1
        mfe = _as_float(metric.get("mfe_before_stop_r"))
        bars = _as_int(metric.get("bars_fill_to_stop"))
        if mfe is not None:
            self.sl_mfe_before_stop_r.append(mfe)
            if mfe >= 0.25:
                self.sl_mfe_ge_025r += 1
            if mfe >= 0.50:
                self.sl_mfe_ge_050r += 1
            if mfe >= 1.00:
                self.sl_mfe_ge_100r += 1
        if bars is not None:
            self.sl_bars_fill_to_stop.append(bars)

    def no_entry_row(self, key_name: str, key: str) -> dict[str, Any]:
        distance = _describe_values(self.no_entry_distance_r)
        bars = _describe_values(self.no_entry_bars_until_nearest)
        return {
            key_name: key,
            "no_entry_rows": self.no_entry_rows,
            "path_n": self.no_entry_path_n,
            "path_coverage": _rate(self.no_entry_path_n, self.no_entry_rows),
            "median_closest_distance_r": distance.get("median"),
            "p75_closest_distance_r": distance.get("p75"),
            "mean_entry_proximity_pct": _mean_list(self.no_entry_proximity_pct),
            "near_entry_le_0_25r": self.no_entry_near_025r,
            "near_entry_le_0_25r_rate": _rate(self.no_entry_near_025r, self.no_entry_path_n),
            "near_entry_le_0_50r_rate": _rate(self.no_entry_near_050r, self.no_entry_path_n),
            "near_entry_le_1_00r_rate": _rate(self.no_entry_near_100r, self.no_entry_path_n),
            "fill_touched_in_path": self.no_entry_fill_touched_in_path,
            "median_bars_until_nearest": bars.get("median"),
        }

    def sl_row(self, key_name: str, key: str) -> dict[str, Any]:
        mfe = _describe_values(self.sl_mfe_before_stop_r)
        bars = _describe_values(self.sl_bars_fill_to_stop)
        return {
            key_name: key,
            "sl_rows": self.sl_rows,
            "path_n": self.sl_path_n,
            "path_coverage": _rate(self.sl_path_n, self.sl_rows),
            "immediate_stop": self.immediate_stop_rows,
            "immediate_stop_rate": _rate(self.immediate_stop_rows, self.sl_rows),
            "median_mfe_before_stop_r": mfe.get("median"),
            "p75_mfe_before_stop_r": mfe.get("p75"),
            "mfe_ge_0_25r_rate": _rate(self.sl_mfe_ge_025r, self.sl_path_n),
            "mfe_ge_0_50r_rate": _rate(self.sl_mfe_ge_050r, self.sl_path_n),
            "mfe_ge_1_00r_rate": _rate(self.sl_mfe_ge_100r, self.sl_path_n),
            "median_bars_fill_to_stop": bars.get("median"),
        }


@dataclass
class M1M5DisagreementStats:
    comparable_rows: int = 0
    agreement_rows: int = 0
    disagreement_rows: int = 0
    pair_counts: Counter[str] = field(default_factory=Counter)
    disagreement_by_truth: Counter[str] = field(default_factory=Counter)
    disagreement_by_m15: Counter[str] = field(default_factory=Counter)
    disagreement_by_gappy: Counter[str] = field(default_factory=Counter)
    disagreement_by_same_bar: Counter[str] = field(default_factory=Counter)

    def add(self, row: Mapping[str, Any]) -> None:
        if not (
            row.get("m1_refinement_attempted")
            and row.get("m5_refinement_attempted")
            and row.get("m1_local_coverage")
            and row.get("m5_local_coverage")
        ):
            return
        m1 = row.get("m1_refined_outcome")
        m5 = row.get("m5_refined_outcome")
        if not m1 or not m5:
            return
        self.comparable_rows += 1
        pair = f"{m1}->{m5}"
        self.pair_counts[pair] += 1
        if m1 == m5:
            self.agreement_rows += 1
            return
        self.disagreement_rows += 1
        self.disagreement_by_truth[str(row.get("truth_outcome") or "UNKNOWN")] += 1
        self.disagreement_by_m15[str(row.get("m15_outcome") or "UNKNOWN")] += 1
        gappy = bool(row.get("m1_gap_count_in_horizon") or row.get("m5_gap_count_in_horizon"))
        self.disagreement_by_gappy["gappy" if gappy else "not_gappy"] += 1
        same_bar = "SAME_BAR" in {str(m1), str(m5), str(row.get("truth_outcome") or "")}
        self.disagreement_by_same_bar["same_bar_involved" if same_bar else "no_same_bar"] += 1

    def to_summary(self) -> dict[str, Any]:
        return {
            "comparable_rows": self.comparable_rows,
            "agreement_rows": self.agreement_rows,
            "disagreement_rows": self.disagreement_rows,
            "disagreement_rate": _rate(self.disagreement_rows, self.comparable_rows),
            "top_pairs": _counter_rows(self.pair_counts, "m1_to_m5_outcome", limit=20),
            "disagreement_by_truth_outcome": _counter_rows(
                self.disagreement_by_truth,
                "truth_outcome",
            ),
            "disagreement_by_m15_outcome": _counter_rows(
                self.disagreement_by_m15,
                "m15_outcome",
            ),
            "disagreement_by_gappy_flag": _counter_rows(
                self.disagreement_by_gappy,
                "gappy_flag",
            ),
            "disagreement_by_same_bar_flag": _counter_rows(
                self.disagreement_by_same_bar,
                "same_bar_flag",
            ),
        }


class OhlcvCache:
    def __init__(self, data_dirs: Sequence[str | Path]):
        self.roots = [Path(path) for path in data_dirs]
        self._cache: dict[tuple[str, str], list[dict[str, Any]]] = {}
        self._times: dict[tuple[str, str], list[Any]] = {}

    def rows(self, symbol: str, timeframe: str) -> list[dict[str, Any]]:
        key = (symbol.upper(), timeframe.upper())
        if key in self._cache:
            return self._cache[key]
        path = _find_ohlcv_path(self.roots, symbol, timeframe)
        if path is None:
            self._cache[key] = []
            return []
        series = CandleSeries.from_csv(path, timeframe=timeframe)
        rows = [
            {
                "time": close_time,
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
            }
            for row, close_time in zip(series.rows, series.close_times)
        ]
        self._cache[key] = rows
        self._times[key] = [row["time"] for row in rows]
        return rows

    def future_slice(self, row: Mapping[str, Any], timeframe: str) -> list[Mapping[str, Any]]:
        symbol = str(row.get("symbol") or "")
        key = (symbol.upper(), timeframe.upper())
        rows = self.rows(symbol, timeframe)
        if not rows:
            return []
        try:
            candle_close = ensure_utc(str(row.get("candle_close_utc")))
        except (TypeError, ValueError):
            return []
        times = self._times.get(key) or [bar.get("time") for bar in rows]
        start_idx = bisect.bisect_right(times, candle_close)
        horizon = _horizon_bars(row, timeframe)
        return list(rows[start_idx : start_idx + horizon])


def iter_jsonl(path: str | Path) -> Iterator[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def find_latest_input(pattern: str = DEFAULT_INPUT_GLOB) -> Path:
    paths = [
        path
        for path in Path().glob(pattern)
        if path.is_file()
        and path.suffix == ".jsonl"
        and "_summary_" not in path.name
        and "_diagnostics_" not in path.name
    ]
    if not paths:
        raise FileNotFoundError(f"no truth-layer JSONL matches {pattern!r}")
    return max(paths, key=lambda path: path.stat().st_mtime)


def analyze_truth_layer(
    *,
    input_path: str | Path,
    data_dirs: Sequence[str | Path],
    compute_path_metrics: bool = True,
    max_rows: int | None = None,
    min_candidate_resolved_n: int = 150,
    min_candidate_confidence_rows: int = 200,
) -> dict[str, Any]:
    input_path = Path(input_path)
    global_stats = CohortStats()
    global_anatomy = PathAnatomyStats()
    cohorts: dict[str, dict[str, CohortStats]] = {
        name: defaultdict(CohortStats)
        for name in (
            "symbol",
            "session",
            "year",
            "regime",
            "symbol_session",
            "symbol_year",
            "symbol_session_regime",
        )
    }
    anatomies: dict[str, dict[str, PathAnatomyStats]] = {
        name: defaultdict(PathAnatomyStats)
        for name in ("symbol", "session", "year", "regime", "symbol_session", "symbol_session_regime")
    }
    disagreement = M1M5DisagreementStats()
    keys_seen: set[str] = set()
    duplicate_keys = 0
    ai_attempted_rows = 0
    ai_call_count_sum = 0
    path_cache = OhlcvCache(data_dirs) if compute_path_metrics else None

    for idx, row in enumerate(iter_jsonl(input_path), start=1):
        key = str(row.get("opportunity_key") or "")
        if key:
            if key in keys_seen:
                duplicate_keys += 1
            keys_seen.add(key)
        if row.get("ai_call_attempted"):
            ai_attempted_rows += 1
        ai_call_count_sum += int(row.get("ai_call_count") or 0)

        global_stats.add(row)
        global_anatomy.add_row(row)
        disagreement.add(row)
        group_keys = _group_keys(row)
        for dimension, group_key in group_keys.items():
            if dimension in cohorts:
                cohorts[dimension][group_key].add(row)
            if dimension in anatomies:
                anatomies[dimension][group_key].add_row(row)

        if compute_path_metrics and path_cache is not None:
            _add_path_metrics(row, path_cache, global_anatomy, anatomies, group_keys)

        if max_rows is not None and idx >= max_rows:
            break

    summary: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": utc_now().isoformat(),
        "input_jsonl": str(input_path),
        "data_dirs": [str(Path(path)) for path in data_dirs],
        "compute_path_metrics": compute_path_metrics,
        "max_rows": max_rows,
        "rows": global_stats.rows,
        "unique_keys": len(keys_seen),
        "duplicate_keys": duplicate_keys,
        "ai_attempted_rows": ai_attempted_rows,
        "ai_call_count_sum": ai_call_count_sum,
        "truth_outcomes": _counter_rows(global_stats.outcomes, "truth_outcome"),
        "failure_buckets": _counter_rows(global_stats.failure_buckets, "truth_failure_bucket"),
        "confidence": _counter_rows(global_stats.confidence, "truth_confidence"),
        "selected_timeframes": _counter_rows(
            global_stats.source_timeframes,
            "truth_source_timeframe",
        ),
        "global_cohort": global_stats.as_row("cohort", "all_rows"),
        "global_no_entry_anatomy": global_anatomy.no_entry_row("cohort", "all_rows"),
        "global_sl_anatomy": global_anatomy.sl_row("cohort", "all_rows"),
        "m1_m5_disagreement": disagreement.to_summary(),
        "min_candidate_resolved_n": min_candidate_resolved_n,
        "min_candidate_confidence_rows": min_candidate_confidence_rows,
    }
    for dimension, groups in cohorts.items():
        summary[f"by_{dimension}"] = _stats_rows(groups, dimension)
        summary[f"top_failure_buckets_by_{dimension}"] = _failure_rank_rows(groups, dimension)
    for dimension, groups in anatomies.items():
        summary[f"no_entry_anatomy_by_{dimension}"] = _anatomy_rows(groups, dimension, kind="no_entry")
        summary[f"sl_anatomy_by_{dimension}"] = _anatomy_rows(groups, dimension, kind="sl")

    ranking_groups = cohorts["symbol_session_regime"]
    summary["research_candidates_high_confidence"] = _candidate_rows(
        ranking_groups,
        "symbol_session_regime",
        scope="high",
        min_resolved_n=min_candidate_resolved_n,
        min_confidence_rows=min_candidate_confidence_rows,
    )
    summary["research_candidates_high_medium_confidence"] = _candidate_rows(
        ranking_groups,
        "symbol_session_regime",
        scope="high_medium",
        min_resolved_n=min_candidate_resolved_n,
        min_confidence_rows=min_candidate_confidence_rows,
    )
    summary["synthesis"] = _synthesis_bullets(summary)
    return summary


def render_report(summary: Mapping[str, Any]) -> str:
    lines = [
        "# Phase 3 Historical Opportunity Truth-Layer Cohort Diagnostics",
        "",
        f"**Created UTC:** {summary.get('created_at_utc')}",
        f"**Input:** `{summary.get('input_jsonl')}`",
        f"**Rows scanned:** {summary.get('rows')}",
        f"**Path metrics:** `{summary.get('compute_path_metrics')}`",
        "",
        "## Interpretation Boundary",
        "",
        "- Research/tooling only; no live trading logic, prompt, or config behavior is changed.",
        "- No AI/API calls are made. `ai_attempted_rows` and `ai_call_count_sum` must stay zero.",
        "- Rankings are diagnostic triage, not alpha validation or promotion evidence.",
        "- No looser-entry or buffer simulation is included; that would be parameter optimization.",
        "- Low-confidence, same-bar, and gappy cohorts should be excluded or sensitivity-tested before any sweep.",
        "",
        "## Data Integrity",
        "",
        _markdown_table(
            [
                {
                    "rows": summary.get("rows"),
                    "unique_keys": summary.get("unique_keys"),
                    "duplicate_keys": summary.get("duplicate_keys"),
                    "ai_attempted_rows": summary.get("ai_attempted_rows"),
                    "ai_call_count_sum": summary.get("ai_call_count_sum"),
                }
            ]
        ),
        "",
        "## Outcome Shape",
        "",
        "### Truth Outcomes",
        "",
        _markdown_table(summary.get("truth_outcomes") or []),
        "",
        "### Failure And Success Buckets",
        "",
        _markdown_table(summary.get("failure_buckets") or []),
        "",
        "### Confidence And Source",
        "",
        _markdown_table(summary.get("confidence") or []),
        "",
        _markdown_table(summary.get("selected_timeframes") or []),
        "",
        "## Candidate Cohort Triage",
        "",
        "### High Confidence Only",
        "",
        _markdown_table((summary.get("research_candidates_high_confidence") or [])[:25]),
        "",
        "### High + Medium Confidence",
        "",
        _markdown_table((summary.get("research_candidates_high_medium_confidence") or [])[:25]),
        "",
        "## Cohort Anatomy",
        "",
        "### Symbol",
        "",
        _markdown_table(summary.get("by_symbol") or []),
        "",
        "### Session",
        "",
        _markdown_table(summary.get("by_session") or []),
        "",
        "### Year",
        "",
        _markdown_table(summary.get("by_year") or []),
        "",
        "### Regime",
        "",
        _markdown_table(summary.get("by_regime") or []),
        "",
        "### Symbol x Session",
        "",
        _markdown_table(summary.get("by_symbol_session") or []),
        "",
        "## Dominant Failure Buckets",
        "",
        "### By Symbol",
        "",
        _markdown_table((summary.get("top_failure_buckets_by_symbol") or [])[:35]),
        "",
        "### By Session",
        "",
        _markdown_table((summary.get("top_failure_buckets_by_session") or [])[:35]),
        "",
        "### By Regime",
        "",
        _markdown_table((summary.get("top_failure_buckets_by_regime") or [])[:35]),
        "",
        "## NO_ENTRY Anatomy",
        "",
        "### Global",
        "",
        _markdown_table([summary.get("global_no_entry_anatomy") or {}]),
        "",
        "### By Symbol x Session",
        "",
        _markdown_table((summary.get("no_entry_anatomy_by_symbol_session") or [])[:25]),
        "",
        "### By Regime",
        "",
        _markdown_table((summary.get("no_entry_anatomy_by_regime") or [])[:25]),
        "",
        "## SL Anatomy",
        "",
        "### Global",
        "",
        _markdown_table([summary.get("global_sl_anatomy") or {}]),
        "",
        "### By Symbol x Session",
        "",
        _markdown_table((summary.get("sl_anatomy_by_symbol_session") or [])[:25]),
        "",
        "### By Regime",
        "",
        _markdown_table((summary.get("sl_anatomy_by_regime") or [])[:25]),
        "",
        "## M1/M5 Agreement",
        "",
        _markdown_table(
            [
                {
                    "comparable_rows": (summary.get("m1_m5_disagreement") or {}).get("comparable_rows"),
                    "agreement_rows": (summary.get("m1_m5_disagreement") or {}).get("agreement_rows"),
                    "disagreement_rows": (summary.get("m1_m5_disagreement") or {}).get("disagreement_rows"),
                    "disagreement_rate": (summary.get("m1_m5_disagreement") or {}).get("disagreement_rate"),
                }
            ]
        ),
        "",
        "### Top M1 -> M5 Outcome Pairs",
        "",
        _markdown_table((summary.get("m1_m5_disagreement") or {}).get("top_pairs") or []),
        "",
        "### Disagreement Concentration",
        "",
        _markdown_table((summary.get("m1_m5_disagreement") or {}).get("disagreement_by_truth_outcome") or []),
        "",
        _markdown_table((summary.get("m1_m5_disagreement") or {}).get("disagreement_by_gappy_flag") or []),
        "",
        _markdown_table((summary.get("m1_m5_disagreement") or {}).get("disagreement_by_same_bar_flag") or []),
        "",
        "## Synthesis",
        "",
        *(summary.get("synthesis") or []),
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_summary(summary: Mapping[str, Any], *, output_root: str | Path, input_path: str | Path) -> Path:
    output_dir = Path(output_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    path = output_dir / f"{_short_artifact_slug(Path(input_path).stem)}_cohort_diagnostics_{stamp}.json"
    path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return path


def write_report(path: str | Path, content: str) -> Path:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(content, encoding="utf-8")
    return report_path


def _add_path_metrics(
    row: Mapping[str, Any],
    path_cache: OhlcvCache,
    global_anatomy: PathAnatomyStats,
    anatomies: Mapping[str, Mapping[str, PathAnatomyStats]],
    group_keys: Mapping[str, str],
) -> None:
    outcome = row.get("truth_outcome")
    if outcome not in {"NO_ENTRY", "SL"} or not _is_setup_row(row):
        return
    timeframe = _analysis_timeframe(row)
    if timeframe is None:
        return
    future = path_cache.future_slice(row, timeframe)
    if outcome == "NO_ENTRY":
        metric = compute_no_entry_path_metric(row, rows=[], timeframe=timeframe, future_slice=future)
        global_anatomy.add_no_entry_metric(metric)
        for dimension, key in group_keys.items():
            if dimension in anatomies:
                anatomies[dimension][key].add_no_entry_metric(metric)
    elif outcome == "SL":
        metric = compute_sl_path_metric(row, rows=[], timeframe=timeframe, future_slice=future)
        global_anatomy.add_sl_metric(metric)
        for dimension, key in group_keys.items():
            if dimension in anatomies:
                anatomies[dimension][key].add_sl_metric(metric)


def compute_no_entry_path_metric(
    row: Mapping[str, Any],
    *,
    rows: Sequence[Mapping[str, Any]],
    timeframe: str,
    future_slice: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    setup = _setup_values(row)
    if setup is None or (not rows and future_slice is None):
        return {"path_available": False, "skip_reason": "missing_setup_or_rows"}
    future = list(future_slice) if future_slice is not None else _future_rows(row, rows=rows, timeframe=timeframe)
    if not future:
        return {"path_available": False, "skip_reason": "no_future_rows"}
    side = setup["side"]
    entry = setup["entry"]
    risk = setup["risk"]
    if side == "LONG":
        indexed = [(idx, _as_float(bar.get("low"))) for idx, bar in enumerate(future, start=1)]
        indexed = [(idx, value) for idx, value in indexed if value is not None]
        if not indexed:
            return {"path_available": False, "skip_reason": "no_lows"}
        nearest_idx, nearest_price = min(indexed, key=lambda item: item[1])
        raw_distance = nearest_price - entry
    elif side == "SHORT":
        indexed = [(idx, _as_float(bar.get("high"))) for idx, bar in enumerate(future, start=1)]
        indexed = [(idx, value) for idx, value in indexed if value is not None]
        if not indexed:
            return {"path_available": False, "skip_reason": "no_highs"}
        nearest_idx, nearest_price = max(indexed, key=lambda item: item[1])
        raw_distance = entry - nearest_price
    else:
        return {"path_available": False, "skip_reason": "unsupported_side"}
    distance_abs = max(float(raw_distance), 0.0)
    distance_r = distance_abs / risk
    return {
        "path_available": True,
        "timeframe": timeframe,
        "bars_examined": len(future),
        "bars_until_nearest": nearest_idx,
        "nearest_price": round(float(nearest_price), 6),
        "closest_distance_abs": round(distance_abs, 6),
        "closest_distance_r": round(distance_r, 6),
        "entry_proximity_of_sl_distance": round(max(0.0, 1.0 - distance_r), 6),
        "fill_touched_in_path": raw_distance <= 0,
    }


def compute_sl_path_metric(
    row: Mapping[str, Any],
    *,
    rows: Sequence[Mapping[str, Any]],
    timeframe: str,
    future_slice: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    setup = _setup_values(row)
    if setup is None or (not rows and future_slice is None):
        return {"path_available": False, "skip_reason": "missing_setup_or_rows"}
    future = list(future_slice) if future_slice is not None else _future_rows(row, rows=rows, timeframe=timeframe)
    if not future:
        return {"path_available": False, "skip_reason": "no_future_rows"}
    side = setup["side"]
    entry = setup["entry"]
    sl = setup["sl"]
    risk = setup["risk"]
    fill_idx: int | None = None
    stop_idx: int | None = None
    mfe_before_stop = 0.0
    for idx, bar in enumerate(future, start=1):
        high = _as_float(bar.get("high"))
        low = _as_float(bar.get("low"))
        if high is None or low is None:
            continue
        if fill_idx is None:
            if side == "LONG" and low <= entry:
                fill_idx = idx
            elif side == "SHORT" and high >= entry:
                fill_idx = idx
        if fill_idx is None:
            continue
        stop_now = (side == "LONG" and low <= sl) or (side == "SHORT" and high >= sl)
        if stop_now:
            stop_idx = idx
            break
        favorable = high - entry if side == "LONG" else entry - low
        mfe_before_stop = max(mfe_before_stop, favorable)
    if fill_idx is None:
        return {"path_available": False, "skip_reason": "fill_not_reconstructed"}
    if stop_idx is None:
        truth_bars = _as_int(row.get("truth_bars_in_trade"))
        stop_idx = truth_bars if truth_bars and truth_bars >= fill_idx else len(future)
    bars_fill_to_stop = max(1, stop_idx - fill_idx + 1)
    mfe_r = max(0.0, mfe_before_stop / risk)
    return {
        "path_available": True,
        "timeframe": timeframe,
        "bars_examined": len(future),
        "fill_bar_index": fill_idx,
        "stop_bar_index": stop_idx,
        "bars_fill_to_stop": bars_fill_to_stop,
        "mfe_before_stop_r": round(mfe_r, 6),
        "stop_reconstructed": stop_idx is not None,
    }


def _future_rows(
    row: Mapping[str, Any],
    *,
    rows: Sequence[Mapping[str, Any]],
    timeframe: str,
) -> list[Mapping[str, Any]]:
    try:
        candle_close = ensure_utc(str(row.get("candle_close_utc")))
    except (TypeError, ValueError):
        return []
    times = [bar.get("time") for bar in rows]
    start_idx = bisect.bisect_right(times, candle_close)
    horizon = _horizon_bars(row, timeframe)
    return list(rows[start_idx : start_idx + horizon])


def _horizon_bars(row: Mapping[str, Any], timeframe: str) -> int:
    key = timeframe.upper()
    if key == "M15":
        return DEFAULT_M15_HOLD_BARS
    prefix_value = _as_int(row.get(f"{key.lower()}_horizon_bars"))
    if prefix_value:
        return prefix_value
    minutes = TIMEFRAME_MINUTES.get(key)
    if not minutes:
        return DEFAULT_M15_HOLD_BARS
    return max(1, math.ceil(DEFAULT_M15_HOLD_BARS * 15 / minutes))


def _setup_values(row: Mapping[str, Any]) -> dict[str, Any] | None:
    entry = _as_float(row.get("mechanical_entry"))
    sl = _as_float(row.get("mechanical_sl"))
    tp = _as_float(row.get("mechanical_tp"))
    side = str(row.get("mechanical_side") or "").upper()
    if entry is None or sl is None or tp is None or side not in {"LONG", "SHORT"}:
        return None
    risk = abs(entry - sl)
    if risk <= 0:
        return None
    return {"entry": entry, "sl": sl, "tp": tp, "side": side, "risk": risk}


def _analysis_timeframe(row: Mapping[str, Any]) -> str | None:
    truth_tf = str(row.get("truth_source_timeframe") or "").upper()
    if truth_tf in ANALYSIS_TIMEFRAMES:
        return truth_tf
    lower_tf = str(row.get("lower_tf_timeframe") or "").upper()
    if lower_tf in {"M1", "M5"}:
        return lower_tf
    truth_outcome = row.get("truth_outcome")
    for timeframe in ("M1", "M5"):
        if row.get(f"{timeframe.lower()}_refined_outcome") == truth_outcome and row.get(
            f"{timeframe.lower()}_local_coverage"
        ):
            return timeframe
    if row.get("m15_outcome") == truth_outcome:
        return "M15"
    return None


def _group_keys(row: Mapping[str, Any]) -> dict[str, str]:
    symbol = str(row.get("symbol") or "unknown")
    session = str(row.get("session") or "unknown")
    year = str(row.get("year") or "unknown")
    regime = str(row.get("truth_regime") or "none|none")
    return {
        "symbol": symbol,
        "session": session,
        "year": year,
        "regime": regime,
        "symbol_session": f"{symbol}|{session}",
        "symbol_year": f"{symbol}|{year}",
        "symbol_session_regime": f"{symbol}|{session}|{regime}",
    }


def _is_setup_row(row: Mapping[str, Any]) -> bool:
    return bool(row.get("would_send_ai")) and row.get("mechanical_setup_status") == "OK"


def _stats_rows(groups: Mapping[str, CohortStats], key_name: str) -> list[dict[str, Any]]:
    return [stats.as_row(key_name, key) for key, stats in sorted(groups.items())]


def _failure_rank_rows(
    groups: Mapping[str, CohortStats],
    key_name: str,
    *,
    limit_per_group: int = 5,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, stats in groups.items():
        for bucket, count in stats.failure_buckets.most_common(limit_per_group):
            rows.append(
                {
                    key_name: key,
                    "truth_failure_bucket": bucket,
                    "rows": count,
                    "bucket_share_of_cohort": _rate(count, stats.rows),
                    "bucket_share_of_setup": (
                        _rate(count, stats.setup_rows)
                        if _bucket_belongs_to_setup_population(bucket)
                        else None
                    ),
                }
            )
    return sorted(rows, key=lambda item: int(item.get("rows") or 0), reverse=True)


def _bucket_belongs_to_setup_population(bucket: str) -> bool:
    return bucket.startswith(
        (
            "FAIL_",
            "SUCCESS_",
            "MIXED_",
            "AMBIGUOUS_",
            "DATA_",
            "TIMEOUT_",
        )
    )


def _anatomy_rows(
    groups: Mapping[str, PathAnatomyStats],
    key_name: str,
    *,
    kind: str,
) -> list[dict[str, Any]]:
    rows = []
    for key, stats in groups.items():
        if kind == "no_entry" and stats.no_entry_rows:
            rows.append(stats.no_entry_row(key_name, key))
        elif kind == "sl" and stats.sl_rows:
            rows.append(stats.sl_row(key_name, key))
    primary = "no_entry_rows" if kind == "no_entry" else "sl_rows"
    return sorted(rows, key=lambda item: int(item.get(primary) or 0), reverse=True)


def _candidate_rows(
    groups: Mapping[str, CohortStats],
    key_name: str,
    *,
    scope: str,
    min_resolved_n: int,
    min_confidence_rows: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, stats in groups.items():
        if scope == "high":
            confidence_rows = stats.high_confidence_rows
            resolved_n = stats.high_resolved_n
            resolved_sum = stats.high_resolved_sum
            wins = stats.high_wins
            label = "HIGH"
        elif scope == "high_medium":
            confidence_rows = stats.high_medium_confidence_rows
            resolved_n = stats.high_medium_resolved_n
            resolved_sum = stats.high_medium_resolved_sum
            wins = stats.high_medium_wins
            label = "HIGH+MEDIUM"
        else:
            raise ValueError(f"unknown candidate scope {scope!r}")
        mean_r = _mean(resolved_sum, resolved_n)
        win_rate = _rate(wins, resolved_n)
        if confidence_rows < min_confidence_rows or resolved_n < min_resolved_n:
            continue
        if mean_r is None or mean_r <= 0:
            continue
        ambiguity = (
            stats.outcomes.get("SAME_BAR", 0)
            + stats.outcomes.get("LOWER_TF_GAPPY", 0)
            + stats.confidence.get("LOW", 0)
        )
        ambiguity_rate = _rate(ambiguity, stats.setup_rows)
        immediate_stop_rate = _rate(
            stats.failure_buckets.get("FAIL_IMMEDIATE_STOP_AFTER_FILL", 0),
            stats.outcomes.get("SL", 0),
        )
        no_entry_rate = _rate(stats.outcomes.get("NO_ENTRY", 0), stats.setup_rows)
        sample_factor = math.sqrt(min(resolved_n, 1000) / max(min_resolved_n, 1))
        score = mean_r * sample_factor + (win_rate - 0.45) * 0.25
        score -= ambiguity_rate * 0.50
        score -= immediate_stop_rate * 0.25
        rows.append(
            {
                key_name: key,
                "confidence_scope": label,
                "confidence_rows": confidence_rows,
                "resolved_r_n": resolved_n,
                "mean_r": mean_r,
                "win_rate": win_rate,
                "setup_rows": stats.setup_rows,
                "no_entry_rate_setup": no_entry_rate,
                "same_bar": stats.outcomes.get("SAME_BAR", 0),
                "lower_tf_gappy": stats.outcomes.get("LOWER_TF_GAPPY", 0),
                "ambiguity_rate_setup": ambiguity_rate,
                "immediate_stop_rate_sl": immediate_stop_rate,
                "diagnostic_priority_score": round(score, 6),
            }
        )
    return sorted(rows, key=lambda item: float(item.get("diagnostic_priority_score") or 0.0), reverse=True)


def _counter_rows(counter: Counter[str], key_name: str, *, limit: int | None = None) -> list[dict[str, Any]]:
    rows = [{key_name: key, "rows": value} for key, value in counter.most_common(limit)]
    return rows


def _short_artifact_slug(value: str, *, max_len: int = 72) -> str:
    slug = safe_slug(value)
    if len(slug) <= max_len:
        return slug
    digest = hashlib.sha1(slug.encode("utf-8")).hexdigest()[:10]
    return f"{slug[: max_len - 11]}_{digest}"


def _describe_values(values: Sequence[float | int]) -> dict[str, Any]:
    clean = [float(value) for value in values if math.isfinite(float(value))]
    if not clean:
        return {"n": 0, "mean": None, "median": None, "p25": None, "p75": None}
    clean.sort()
    return {
        "n": len(clean),
        "mean": round(sum(clean) / len(clean), 6),
        "median": round(_quantile(clean, 0.50), 6),
        "p25": round(_quantile(clean, 0.25), 6),
        "p75": round(_quantile(clean, 0.75), 6),
    }


def _quantile(sorted_values: Sequence[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    position = (len(sorted_values) - 1) * q
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return float(sorted_values[low])
    fraction = position - low
    return float(sorted_values[low]) * (1 - fraction) + float(sorted_values[high]) * fraction


def _synthesis_bullets(summary: Mapping[str, Any]) -> list[str]:
    outcomes = {row["truth_outcome"]: row["rows"] for row in summary.get("truth_outcomes") or []}
    candidates_high = summary.get("research_candidates_high_confidence") or []
    candidates_hm = summary.get("research_candidates_high_medium_confidence") or []
    no_entry = summary.get("global_no_entry_anatomy") or {}
    sl = summary.get("global_sl_anatomy") or {}
    disagreement = summary.get("m1_m5_disagreement") or {}
    bullets = [
        f"- Rows are clean for diagnostic use: {summary.get('rows'):,} rows, "
        f"{summary.get('unique_keys'):,} unique keys, {summary.get('duplicate_keys')} duplicates, "
        f"and {summary.get('ai_call_count_sum')} AI calls.",
        "- Dominant actionable buckets remain "
        f"NO_ENTRY={outcomes.get('NO_ENTRY', 0):,}, SL={outcomes.get('SL', 0):,}, "
        f"TP={outcomes.get('TP', 0):,}, SAME_BAR={outcomes.get('SAME_BAR', 0):,}, "
        f"LOWER_TF_GAPPY={outcomes.get('LOWER_TF_GAPPY', 0):,}.",
    ]
    if candidates_high:
        top = candidates_high[0]
        bullets.append(
            "- Best high-confidence diagnostic lead by the transparent priority score is "
            f"`{top.get('symbol_session_regime')}` with n={top.get('resolved_r_n')}, "
            f"mean R={float(top.get('mean_r') or 0.0):+.4f}, "
            f"WR={float(top.get('win_rate') or 0.0):.2%}. Treat this as a cohort to study, not a promotion claim."
        )
    elif candidates_hm:
        top = candidates_hm[0]
        bullets.append(
            "- No high-confidence cohort cleared the default candidate guard strongly enough; "
            f"the best high+medium diagnostic lead is `{top.get('symbol_session_regime')}` "
            f"with n={top.get('resolved_r_n')} and mean R={float(top.get('mean_r') or 0.0):+.4f}."
        )
    else:
        bullets.append(
            "- No cohort cleared the default positive-mean and sample-size candidate guard; "
            "deeper work should first loosen the diagnostic guard deliberately or aggregate broader cohorts."
        )
    if no_entry.get("path_n"):
        bullets.append(
            "- NO_ENTRY path anatomy is now measurable without tuning: "
            f"{no_entry.get('path_n'):,}/{no_entry.get('no_entry_rows'):,} rows had OHLCV path coverage; "
            f"{float(no_entry.get('near_entry_le_0_25r_rate') or 0.0):.2%} came within 0.25R of entry."
        )
    if sl.get("path_n"):
        bullets.append(
            "- SL path anatomy shows whether stops failed immediately or after usable excursion: "
            f"immediate-stop rate {float(sl.get('immediate_stop_rate') or 0.0):.2%}, "
            f"median pre-stop MFE {float(sl.get('median_mfe_before_stop_r') or 0.0):.3f}R."
        )
    if disagreement.get("comparable_rows"):
        bullets.append(
            "- M1/M5 disagreement is explicit: "
            f"{disagreement.get('disagreement_rows'):,}/{disagreement.get('comparable_rows'):,} "
            f"comparable rows disagree ({float(disagreement.get('disagreement_rate') or 0.0):.2%}); "
            "concentrated same-bar or gappy disagreements should be excluded before parameter work."
        )
    bullets.append(
        "- Recommended next research unit: pre-register 2-4 stable candidate cohorts from this report, "
        "then run controlled studies with DSR/PBO accounting. Do not sweep entry offsets from the full population."
    )
    return bullets


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Truth-layer JSONL. Defaults to latest rescued truth-layer artifact.")
    parser.add_argument("--data-dir", action="append", help="MT5 OHLCV export directory. Repeatable.")
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--min-candidate-resolved-n", type=int, default=150)
    parser.add_argument("--min-candidate-confidence-rows", type=int, default=200)
    parser.add_argument("--no-path-metrics", action="store_true")
    parser.add_argument("--write", action="store_true", help="Write markdown report.")
    parser.add_argument("--quiet", action="store_true", help="Print compact run summary.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_path = Path(args.input) if args.input else find_latest_input()
    data_dirs = args.data_dir or list(DEFAULT_DATA_DIRS)
    summary = analyze_truth_layer(
        input_path=input_path,
        data_dirs=data_dirs,
        compute_path_metrics=not args.no_path_metrics,
        max_rows=args.max_rows,
        min_candidate_resolved_n=args.min_candidate_resolved_n,
        min_candidate_confidence_rows=args.min_candidate_confidence_rows,
    )
    summary_path = write_summary(summary, output_root=args.output_root, input_path=input_path)
    summary["output_summary"] = str(summary_path)
    if args.write:
        report_path = write_report(args.report_path, render_report(summary))
        summary["report_path"] = str(report_path)
        summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    if args.quiet:
        print(
            json.dumps(
                {
                    "rows": summary.get("rows"),
                    "output_summary": summary.get("output_summary"),
                    "report_path": summary.get("report_path"),
                    "research_candidates_high_confidence": (
                        summary.get("research_candidates_high_confidence") or []
                    )[:5],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _rate(numer: int | float, denom: int | float) -> float:
    return round(float(numer) / float(denom), 6) if denom else 0.0


def _mean(total: float, count: int) -> float | None:
    return round(float(total) / count, 6) if count else None


def _mean_list(values: Sequence[float]) -> float | None:
    return round(sum(values) / len(values), 6) if values else None


def _markdown_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    preferred = (
        "cohort",
        "symbol",
        "session",
        "year",
        "regime",
        "symbol_session",
        "symbol_year",
        "symbol_session_regime",
        "confidence_scope",
        "truth_outcome",
        "truth_failure_bucket",
        "truth_confidence",
        "truth_source_timeframe",
        "m1_to_m5_outcome",
        "gappy_flag",
        "same_bar_flag",
        "rows",
        "setup_rows",
        "confidence_rows",
        "resolved_r_n",
        "mean_r",
        "win_rate",
        "tp",
        "sl",
        "timeout",
        "no_entry",
        "same_bar",
        "lower_tf_gappy",
        "immediate_stop",
        "no_entry_rate_setup",
        "sl_rate_filled",
        "immediate_stop_rate_sl",
        "ambiguity_rate_setup",
        "high_confidence",
        "high_medium_confidence",
        "high_resolved_n",
        "high_mean_r",
        "high_win_rate",
        "high_medium_resolved_n",
        "high_medium_mean_r",
        "high_medium_win_rate",
        "diagnostic_priority_score",
        "no_entry_rows",
        "path_n",
        "path_coverage",
        "median_closest_distance_r",
        "p75_closest_distance_r",
        "mean_entry_proximity_pct",
        "near_entry_le_0_25r",
        "near_entry_le_0_25r_rate",
        "near_entry_le_0_50r_rate",
        "near_entry_le_1_00r_rate",
        "fill_touched_in_path",
        "median_bars_until_nearest",
        "sl_rows",
        "immediate_stop_rate",
        "median_mfe_before_stop_r",
        "p75_mfe_before_stop_r",
        "mfe_ge_0_25r_rate",
        "mfe_ge_0_50r_rate",
        "mfe_ge_1_00r_rate",
        "median_bars_fill_to_stop",
        "comparable_rows",
        "agreement_rows",
        "disagreement_rows",
        "disagreement_rate",
        "bucket_share_of_cohort",
        "bucket_share_of_setup",
        "unique_keys",
        "duplicate_keys",
        "ai_attempted_rows",
        "ai_call_count_sum",
    )
    keys = list(rows[0].keys())
    columns = [key for key in preferred if key in keys]
    columns.extend(key for key in keys if key not in columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_markdown_cell(row.get(col, "")) for col in columns) + " |")
    return "\n".join(lines)


def _markdown_cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\n", " ").replace("|", "\\|")


if __name__ == "__main__":
    raise SystemExit(main())
