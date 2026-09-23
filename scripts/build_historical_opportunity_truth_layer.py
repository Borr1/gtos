#!/usr/bin/env python3
"""Build Phase 3 historical opportunity truth/failure taxonomy v2.

This is a research-only label-quality layer over the historical pre-AI
opportunity dataset. It does not import live orchestrators, prompts, or paid AI
clients. The script reuses the existing lower-timeframe mechanical resolver,
adds contiguity diagnostics, selects the best available truth source per row,
and emits explicit success/failure anatomy buckets for cohort audits.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.analyze_historical_opportunity_dataset import (  # noqa: E402
    DEFAULT_INPUT_GLOB,
    _first_after,
    _load_lower_timeframe_rows,
    _scaled_hold_bars,
    _setup_from_row,
    find_latest_input,
    iter_jsonl,
)
from scripts.build_external_feed_validation_dataset import TIMEFRAME_MINUTES  # noqa: E402
from scripts.build_historical_opportunity_dataset import DEFAULT_DATA_DIRS  # noqa: E402
from src.components.external_feeds import ensure_utc, safe_slug, utc_now  # noqa: E402
from src.research_infra.dumb_baseline import resolve_mechanical_outcome  # noqa: E402


SCHEMA_VERSION = "historical_opportunity_truth_layer_v2"
SUMMARY_SCHEMA_VERSION = "historical_opportunity_truth_layer_summary_v2"
DEFAULT_OUTPUT_ROOT = (
    "data/external/validation/calendar_macro_bundle_v1/"
    "historical_opportunities/truth_layer"
)
DEFAULT_REPORT_PATH = (
    "research/phase_3_external_feed_validation/"
    "HISTORICAL_OPPORTUNITY_TRUTH_LAYER_V2_2026-05-01.md"
)
DEFAULT_LOWER_TIMEFRAMES = ("M1", "M5")
RESOLVED_OUTCOMES = {"TP", "SL", "TIMEOUT"}
FILL_TERMINAL_OUTCOMES = {"TP", "SL", "TIMEOUT", "SAME_BAR"}
NO_AI_CALLS_EXPECTED = 0
PAIR_DELIMITER = "|||"


@dataclass(frozen=True)
class LowerTimeframeDiagnostics:
    timeframe: str
    attempted: bool
    local_coverage: bool
    first_future_bar_utc: str | None
    future_rows_available: int
    horizon_bars: int
    contiguous_bars_from_candle: int
    gap_count_in_horizon: int
    first_gap_utc: str | None
    max_gap_minutes: float | None
    horizon_complete: bool
    skip_reason: str | None = None


@dataclass
class TruthGroupStats:
    rows: int = 0
    resolved_r_n: int = 0
    resolved_r_sum: float = 0.0
    wins: int = 0
    outcomes: Counter[str] = field(default_factory=Counter)
    failure_buckets: Counter[str] = field(default_factory=Counter)
    ambiguity_buckets: Counter[str] = field(default_factory=Counter)
    confidence: Counter[str] = field(default_factory=Counter)
    selected_timeframes: Counter[str] = field(default_factory=Counter)

    def add(self, row: Mapping[str, Any]) -> None:
        self.rows += 1
        outcome = str(row.get("truth_outcome") or "UNKNOWN")
        self.outcomes[outcome] += 1
        self.failure_buckets[str(row.get("truth_failure_bucket") or "UNKNOWN")] += 1
        self.ambiguity_buckets[str(row.get("truth_ambiguity_bucket") or "UNKNOWN")] += 1
        self.confidence[str(row.get("truth_confidence") or "UNKNOWN")] += 1
        self.selected_timeframes[str(row.get("truth_source_timeframe") or "UNKNOWN")] += 1
        realized = row.get("truth_realized_r")
        if realized is None:
            return
        try:
            value = float(realized)
        except (TypeError, ValueError):
            return
        self.resolved_r_n += 1
        self.resolved_r_sum += value
        if value > 0:
            self.wins += 1

    def as_row(self, key_name: str, key: str) -> dict[str, Any]:
        return {
            key_name: key,
            "rows": self.rows,
            "resolved_r_n": self.resolved_r_n,
            "mean_r": _mean(self.resolved_r_sum, self.resolved_r_n),
            "win_rate": _rate(self.wins, self.resolved_r_n),
            "tp": self.outcomes.get("TP", 0),
            "sl": self.outcomes.get("SL", 0),
            "timeout": self.outcomes.get("TIMEOUT", 0),
            "no_entry": self.outcomes.get("NO_ENTRY", 0),
            "same_bar": self.outcomes.get("SAME_BAR", 0),
            "no_full_horizon": self.outcomes.get("NO_FULL_HORIZON", 0),
            "lower_tf_gappy": self.outcomes.get("LOWER_TF_GAPPY", 0),
            "high_confidence": self.confidence.get("HIGH", 0),
            "medium_confidence": self.confidence.get("MEDIUM", 0),
            "low_confidence": self.confidence.get("LOW", 0),
            "none_confidence": self.confidence.get("NONE", 0),
        }


@dataclass
class TruthAccumulator:
    rows: int = 0
    ai_attempted_rows: int = 0
    ai_call_count_sum: int = 0
    duplicate_keys: int = 0
    keys_seen: set[str] = field(default_factory=set)
    truth_outcomes: Counter[str] = field(default_factory=Counter)
    fill_status: Counter[str] = field(default_factory=Counter)
    exit_status: Counter[str] = field(default_factory=Counter)
    failure_buckets: Counter[str] = field(default_factory=Counter)
    ambiguity_buckets: Counter[str] = field(default_factory=Counter)
    confidence: Counter[str] = field(default_factory=Counter)
    selected_timeframes: Counter[str] = field(default_factory=Counter)
    m15_to_truth: Counter[str] = field(default_factory=Counter)
    lower_timeframes: dict[str, Counter[str]] = field(
        default_factory=lambda: defaultdict(Counter)
    )
    by_symbol: dict[str, TruthGroupStats] = field(
        default_factory=lambda: defaultdict(TruthGroupStats)
    )
    by_session: dict[str, TruthGroupStats] = field(
        default_factory=lambda: defaultdict(TruthGroupStats)
    )
    by_year: dict[str, TruthGroupStats] = field(
        default_factory=lambda: defaultdict(TruthGroupStats)
    )
    by_framework: dict[str, TruthGroupStats] = field(
        default_factory=lambda: defaultdict(TruthGroupStats)
    )
    by_regime: dict[str, TruthGroupStats] = field(
        default_factory=lambda: defaultdict(TruthGroupStats)
    )
    by_symbol_session: dict[str, TruthGroupStats] = field(
        default_factory=lambda: defaultdict(TruthGroupStats)
    )
    failure_by_symbol: Counter[str] = field(default_factory=Counter)
    failure_by_session: Counter[str] = field(default_factory=Counter)
    failure_by_year: Counter[str] = field(default_factory=Counter)
    failure_by_framework: Counter[str] = field(default_factory=Counter)
    failure_by_regime: Counter[str] = field(default_factory=Counter)

    def add(self, row: Mapping[str, Any], lower_timeframes: Sequence[str]) -> None:
        self.rows += 1
        key = str(row.get("opportunity_key") or "")
        if key:
            if key in self.keys_seen:
                self.duplicate_keys += 1
            self.keys_seen.add(key)
        if row.get("ai_call_attempted"):
            self.ai_attempted_rows += 1
        self.ai_call_count_sum += int(row.get("ai_call_count") or 0)

        outcome = str(row.get("truth_outcome") or "UNKNOWN")
        failure = str(row.get("truth_failure_bucket") or "UNKNOWN")
        ambiguity = str(row.get("truth_ambiguity_bucket") or "UNKNOWN")
        confidence = str(row.get("truth_confidence") or "UNKNOWN")
        timeframe = str(row.get("truth_source_timeframe") or "UNKNOWN")
        m15_outcome = str(row.get("m15_outcome") or "NOT_EVALUATED")

        self.truth_outcomes[outcome] += 1
        self.fill_status[str(row.get("truth_fill_status") or "UNKNOWN")] += 1
        self.exit_status[str(row.get("truth_exit_status") or "UNKNOWN")] += 1
        self.failure_buckets[failure] += 1
        self.ambiguity_buckets[ambiguity] += 1
        self.confidence[confidence] += 1
        self.selected_timeframes[timeframe] += 1
        self.m15_to_truth[_pair_key(m15_outcome, outcome)] += 1

        for tf in lower_timeframes:
            prefix = tf.lower()
            if row.get(f"{prefix}_refinement_attempted"):
                self.lower_timeframes[tf]["attempted"] += 1
            if row.get(f"{prefix}_local_coverage"):
                self.lower_timeframes[tf]["local_coverage"] += 1
            if row.get(f"{prefix}_horizon_complete"):
                self.lower_timeframes[tf]["horizon_complete"] += 1
            if row.get(f"{prefix}_local_coverage") and row.get(f"{prefix}_gap_count_in_horizon"):
                self.lower_timeframes[tf]["gappy"] += 1
            refined = row.get(f"{prefix}_refined_outcome")
            if refined:
                self.lower_timeframes[tf][f"outcome:{refined}"] += 1
            if row.get("lower_tf_timeframe") == tf:
                self.lower_timeframes[tf]["selected"] += 1

        regime = str(row.get("truth_regime") or "none")
        framework = str(row.get("mechanical_framework") or "none")
        symbol = str(row.get("symbol") or "unknown")
        session = str(row.get("session") or "unknown")
        year = str(row.get("year") or "unknown")

        for group in (
            self.by_symbol[symbol],
            self.by_session[session],
            self.by_year[year],
            self.by_framework[framework],
            self.by_regime[regime],
            self.by_symbol_session[f"{symbol}|{session}"],
        ):
            group.add(row)

        self.failure_by_symbol[_pair_key(symbol, failure)] += 1
        self.failure_by_session[_pair_key(session, failure)] += 1
        self.failure_by_year[_pair_key(year, failure)] += 1
        self.failure_by_framework[_pair_key(framework, failure)] += 1
        self.failure_by_regime[_pair_key(regime, failure)] += 1

    def to_summary(self, lower_timeframes: Sequence[str]) -> dict[str, Any]:
        return {
            "rows": self.rows,
            "unique_keys": len(self.keys_seen),
            "duplicate_keys": self.duplicate_keys,
            "ai_attempted_rows": self.ai_attempted_rows,
            "ai_call_count_sum": self.ai_call_count_sum,
            "truth_outcomes": _counter_rows(self.truth_outcomes, "truth_outcome"),
            "fill_status": _counter_rows(self.fill_status, "truth_fill_status"),
            "exit_status": _counter_rows(self.exit_status, "truth_exit_status"),
            "failure_buckets": _counter_rows(
                self.failure_buckets,
                "truth_failure_bucket",
            ),
            "ambiguity_buckets": _counter_rows(
                self.ambiguity_buckets,
                "truth_ambiguity_bucket",
            ),
            "confidence": _counter_rows(self.confidence, "truth_confidence"),
            "selected_timeframes": _counter_rows(
                self.selected_timeframes,
                "truth_source_timeframe",
            ),
            "m15_to_truth": _counter_pair_rows(
                self.m15_to_truth,
                ("m15_outcome", "truth_outcome"),
            ),
            "lower_timeframe_stats": {
                tf: dict(sorted(self.lower_timeframes.get(tf, Counter()).items()))
                for tf in lower_timeframes
            },
            "by_symbol": _stats_rows(self.by_symbol, "symbol"),
            "by_session": _stats_rows(self.by_session, "session"),
            "by_year": _stats_rows(self.by_year, "year"),
            "by_framework": _stats_rows(self.by_framework, "framework"),
            "by_regime": _stats_rows(self.by_regime, "regime"),
            "by_symbol_session": _stats_rows(
                self.by_symbol_session,
                "symbol_session",
            ),
            "failure_by_symbol": _counter_pair_rows(
                self.failure_by_symbol,
                ("symbol", "truth_failure_bucket"),
            ),
            "failure_by_session": _counter_pair_rows(
                self.failure_by_session,
                ("session", "truth_failure_bucket"),
            ),
            "failure_by_year": _counter_pair_rows(
                self.failure_by_year,
                ("year", "truth_failure_bucket"),
            ),
            "failure_by_framework": _counter_pair_rows(
                self.failure_by_framework,
                ("framework", "truth_failure_bucket"),
            ),
            "failure_by_regime": _counter_pair_rows(
                self.failure_by_regime,
                ("regime", "truth_failure_bucket"),
            ),
        }


def build_truth_layer(
    *,
    input_path: str | Path,
    data_dirs: Sequence[str | Path],
    lower_timeframes: Sequence[str],
    output_root: str | Path,
    row_filter: str = "all",
    max_rows: int | None = None,
) -> dict[str, Any]:
    input_path = Path(input_path)
    output_dir = Path(output_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    safe_stem = safe_slug(input_path.stem)
    output_jsonl = output_dir / f"{safe_stem}_truth_layer_v2_{stamp}.jsonl"
    output_summary = output_dir / f"{safe_stem}_truth_layer_v2_summary_{stamp}.json"

    normalized_timeframes = _normalize_lower_timeframes(lower_timeframes)
    accumulator = TruthAccumulator()
    lower_cache: dict[tuple[str, str], list[dict[str, Any]]] = {}
    emitted = 0

    with output_jsonl.open("w", encoding="utf-8", newline="\n") as handle:
        for row in iter_jsonl(input_path):
            if not _row_matches_filter(row, row_filter):
                continue
            truth_row = classify_truth_row(
                row,
                lower_timeframes=normalized_timeframes,
                data_dirs=data_dirs,
                cache=lower_cache,
            )
            accumulator.add(truth_row, normalized_timeframes)
            handle.write(json.dumps(truth_row, sort_keys=True) + "\n")
            emitted += 1
            if max_rows is not None and emitted >= max_rows:
                break

    summary = accumulator.to_summary(normalized_timeframes)
    summary.update(
        {
            "schema_version": SUMMARY_SCHEMA_VERSION,
            "created_at_utc": utc_now().isoformat(),
            "input_jsonl": str(input_path),
            "output_jsonl": str(output_jsonl),
            "output_summary": str(output_summary),
            "data_dirs": [str(Path(path)) for path in data_dirs],
            "lower_timeframe_priority": list(normalized_timeframes),
            "row_filter": row_filter,
            "max_rows": max_rows,
            "paid_ai_replay": False,
            "ai_call_count_expected": NO_AI_CALLS_EXPECTED,
        }
    )
    output_summary.write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return summary


def classify_truth_row(
    row: Mapping[str, Any],
    *,
    lower_timeframes: Sequence[str],
    data_dirs: Sequence[str | Path],
    cache: dict[tuple[str, str], list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    cache = cache if cache is not None else {}
    output = _base_truth_row(row)
    normalized_timeframes = _normalize_lower_timeframes(lower_timeframes)
    output["lower_timeframe_priority"] = list(normalized_timeframes)

    if not row.get("would_send_ai"):
        classification = _classify_gate_reject(row)
        output.update(classification)
        _add_empty_lower_fields(output, normalized_timeframes)
        return output

    if row.get("mechanical_setup_status") != "OK":
        classification = _classify_setup_skip(row)
        output.update(classification)
        _add_empty_lower_fields(output, normalized_timeframes)
        return output

    lower_results: dict[str, dict[str, Any]] = {}
    lower_diagnostics: dict[str, LowerTimeframeDiagnostics] = {}
    for timeframe in normalized_timeframes:
        refined, diagnostics = refine_and_inspect_lower_timeframe(
            row,
            timeframe=timeframe,
            data_dirs=data_dirs,
            cache=cache,
        )
        lower_results[timeframe] = refined
        lower_diagnostics[timeframe] = diagnostics
        _add_lower_fields(output, timeframe, refined, diagnostics)

    selected = _select_truth_source(row, lower_results, lower_diagnostics)
    output.update(_truth_projection(row, selected, lower_diagnostics))
    return output


def inspect_lower_timeframe(
    row: Mapping[str, Any],
    *,
    timeframe: str,
    data_dirs: Sequence[str | Path],
    cache: dict[tuple[str, str], list[dict[str, Any]]] | None = None,
) -> LowerTimeframeDiagnostics:
    _, diagnostics = refine_and_inspect_lower_timeframe(
        row,
        timeframe=timeframe,
        data_dirs=data_dirs,
        cache=cache,
    )
    return diagnostics


def refine_and_inspect_lower_timeframe(
    row: Mapping[str, Any],
    *,
    timeframe: str,
    data_dirs: Sequence[str | Path],
    cache: dict[tuple[str, str], list[dict[str, Any]]] | None = None,
) -> tuple[dict[str, Any], LowerTimeframeDiagnostics]:
    """Resolve and diagnose one lower timeframe using one bounded row slice.

    The shared mechanical resolver copies ``ohlcv_rows`` internally. Passing a
    full multi-year M1/M5 series per opportunity is therefore prohibitively
    expensive once MT5 max-bars is lifted. This function preserves the existing
    selection semantics but gives the resolver only the future horizon it can
    legally inspect for this setup.
    """

    timeframe_key = timeframe.upper()
    if timeframe_key not in TIMEFRAME_MINUTES:
        raise ValueError(f"unsupported timeframe {timeframe!r}")
    cache = cache if cache is not None else {}
    symbol = str(row.get("symbol") or "")
    candle_close = ensure_utc(str(row.get("candle_close_utc")))
    horizon_bars = _scaled_hold_bars(timeframe_key)
    refined_base = _lower_refined_base(
        row,
        symbol=symbol,
        candle_close=candle_close,
        timeframe=timeframe_key,
        horizon_bars=horizon_bars,
    )
    setup = _setup_from_row(row, candle_close)
    rows = _load_lower_timeframe_rows(
        symbol=symbol,
        timeframe=timeframe_key,
        data_dirs=data_dirs,
        cache=cache,
    )
    if not rows:
        diagnostics = LowerTimeframeDiagnostics(
            timeframe=timeframe_key,
            attempted=True,
            local_coverage=False,
            first_future_bar_utc=None,
            future_rows_available=0,
            horizon_bars=horizon_bars,
            contiguous_bars_from_candle=0,
            gap_count_in_horizon=0,
            first_gap_utc=None,
            max_gap_minutes=None,
            horizon_complete=False,
            skip_reason="lower_timeframe_missing",
        )
        return (
            _lower_refined_unavailable(
                refined_base,
                setup_exists=setup is not None,
                outcome_if_setup_exists="NO_DATA",
                bars_in_trade=0,
                skip_reason="lower_timeframe_missing",
            ),
            diagnostics,
        )

    start_idx = _first_after(rows, candle_close)
    if start_idx >= len(rows):
        diagnostics = LowerTimeframeDiagnostics(
            timeframe=timeframe_key,
            attempted=True,
            local_coverage=False,
            first_future_bar_utc=None,
            future_rows_available=0,
            horizon_bars=horizon_bars,
            contiguous_bars_from_candle=0,
            gap_count_in_horizon=0,
            first_gap_utc=None,
            max_gap_minutes=None,
            horizon_complete=False,
            skip_reason="no_future_lower_timeframe_bars",
        )
        return (
            _lower_refined_unavailable(
                refined_base,
                setup_exists=setup is not None,
                outcome_if_setup_exists="NO_LOCAL_OHLCV",
                bars_in_trade=0,
                skip_reason="lower_timeframe_not_contiguous_at_candle",
                first_future_bar_utc=None,
            ),
            diagnostics,
        )

    delta = timedelta(minutes=TIMEFRAME_MINUTES[timeframe_key])
    local_gap = rows[start_idx]["time"] - candle_close
    local_coverage = local_gap <= delta * 2
    future_rows_available = len(rows) - start_idx
    first_future = rows[start_idx]["time"]
    if not local_coverage:
        diagnostics = LowerTimeframeDiagnostics(
            timeframe=timeframe_key,
            attempted=True,
            local_coverage=False,
            first_future_bar_utc=first_future.isoformat(),
            future_rows_available=future_rows_available,
            horizon_bars=horizon_bars,
            contiguous_bars_from_candle=0,
            gap_count_in_horizon=1,
            first_gap_utc=first_future.isoformat(),
            max_gap_minutes=round(local_gap.total_seconds() / 60.0, 6),
            horizon_complete=False,
            skip_reason="lower_timeframe_not_contiguous_at_candle",
        )
        return (
            _lower_refined_unavailable(
                refined_base,
                setup_exists=setup is not None,
                outcome_if_setup_exists="NO_LOCAL_OHLCV",
                bars_in_trade=0,
                skip_reason="lower_timeframe_not_contiguous_at_candle",
                first_future_bar_utc=first_future.isoformat(),
            ),
            diagnostics,
        )

    inspected = rows[start_idx : start_idx + min(horizon_bars, future_rows_available)]
    previous = candle_close
    contiguous_bars = 0
    gap_count = 0
    first_gap_utc: str | None = None
    max_gap_minutes: float | None = None
    strict_gap = delta * 1.5
    for bar in inspected:
        current = bar["time"]
        gap = current - previous
        gap_minutes = gap.total_seconds() / 60.0
        if max_gap_minutes is None or gap_minutes > max_gap_minutes:
            max_gap_minutes = gap_minutes
        if gap > strict_gap:
            gap_count += 1
            if first_gap_utc is None:
                first_gap_utc = current.isoformat()
            previous = current
            continue
        if gap_count == 0:
            contiguous_bars += 1
        previous = current

    horizon_complete = (
        future_rows_available >= horizon_bars
        and gap_count == 0
        and contiguous_bars >= horizon_bars
    )
    diagnostics = LowerTimeframeDiagnostics(
        timeframe=timeframe_key,
        attempted=True,
        local_coverage=True,
        first_future_bar_utc=first_future.isoformat(),
        future_rows_available=future_rows_available,
        horizon_bars=horizon_bars,
        contiguous_bars_from_candle=contiguous_bars,
        gap_count_in_horizon=gap_count,
        first_gap_utc=first_gap_utc,
        max_gap_minutes=round(max_gap_minutes, 6) if max_gap_minutes is not None else None,
        horizon_complete=horizon_complete,
        skip_reason=None if gap_count == 0 else "gap_inside_lower_timeframe_horizon",
    )
    if setup is None:
        return (
            _lower_refined_unavailable(
                refined_base,
                setup_exists=False,
                outcome_if_setup_exists="NO_DATA",
                bars_in_trade=None,
                skip_reason="missing_mechanical_setup",
            ),
            diagnostics,
        )

    outcome = resolve_mechanical_outcome(
        setup,
        ohlcv_rows=inspected,
        max_hold_bars=horizon_bars,
        require_pending_fill=True,
    )
    refined_outcome = outcome.outcome
    refined_skip_reason = outcome.skip_reason
    if future_rows_available < horizon_bars and outcome.outcome in {"NO_ENTRY", "TIMEOUT"}:
        refined_outcome = "NO_FULL_HORIZON"
        refined_skip_reason = "lower_timeframe_future_horizon_incomplete"
    return (
        {
            **refined_base,
            "lower_tf_local_coverage": True,
            "lower_tf_future_rows_available": future_rows_available,
            "refined_outcome": refined_outcome,
            "refined_realized_r": outcome.realized_r,
            "refined_bars_in_trade": outcome.bars_in_trade,
            "refined_exit_time": outcome.exit_time,
            "refined_skip_reason": refined_skip_reason,
        },
        diagnostics,
    )


def _lower_refined_base(
    row: Mapping[str, Any],
    *,
    symbol: str,
    candle_close: datetime,
    timeframe: str,
    horizon_bars: int,
) -> dict[str, Any]:
    return {
        "opportunity_key": row.get("opportunity_key"),
        "symbol": symbol,
        "candle_close_utc": candle_close.isoformat(),
        "m15_outcome": row.get("mechanical_outcome"),
        "m15_realized_r": row.get("mechanical_realized_r"),
        "refined_timeframe": timeframe,
        "refined_max_hold_bars": horizon_bars,
        "lower_tf_local_coverage": False,
    }


def _lower_refined_unavailable(
    base: Mapping[str, Any],
    *,
    setup_exists: bool,
    outcome_if_setup_exists: str,
    bars_in_trade: int | None,
    skip_reason: str,
    first_future_bar_utc: str | None = None,
) -> dict[str, Any]:
    outcome = outcome_if_setup_exists if setup_exists else "NOT_REFINABLE"
    reason = skip_reason if setup_exists else "missing_mechanical_setup"
    output = {
        **base,
        "refined_outcome": outcome,
        "refined_realized_r": None,
        "refined_bars_in_trade": bars_in_trade if setup_exists else None,
        "refined_exit_time": None,
        "refined_skip_reason": reason,
    }
    if first_future_bar_utc is not None:
        output["first_future_bar_utc"] = first_future_bar_utc
    return output


def render_report(summary: Mapping[str, Any]) -> str:
    lines = [
        "# Phase 3 Historical Opportunity Truth Layer v2",
        "",
        f"**Created UTC:** {summary.get('created_at_utc')}",
        f"**Input:** `{summary.get('input_jsonl')}`",
        f"**Output JSONL:** `{summary.get('output_jsonl')}`",
        f"**Rows classified:** {summary.get('rows')}",
        f"**Lower timeframe priority:** {', '.join(summary.get('lower_timeframe_priority') or [])}",
        "",
        "## Interpretation Boundary",
        "",
        "- Research/tooling only; no live trading logic, prompt, or config behavior is changed.",
        "- No paid AI/API replay is performed; AI-attempted rows and AI call counts must remain zero.",
        "- Truth labels are mechanical diagnostic labels, not production trade outcomes.",
        "- `truth_failure_bucket` includes success, failure, ambiguity, setup-reject, and data-quality anatomy buckets.",
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
        "## Truth Outcome Distribution",
        "",
        _markdown_table(summary.get("truth_outcomes") or []),
        "",
        "## Failure And Success Anatomy",
        "",
        _markdown_table(summary.get("failure_buckets") or []),
        "",
        "## Ambiguity And Confidence",
        "",
        "### Ambiguity Buckets",
        "",
        _markdown_table(summary.get("ambiguity_buckets") or []),
        "",
        "### Confidence",
        "",
        _markdown_table(summary.get("confidence") or []),
        "",
        "### Selected Truth Timeframe",
        "",
        _markdown_table(summary.get("selected_timeframes") or []),
        "",
        "## Lower-Timeframe Coverage",
        "",
        _markdown_lower_timeframes(summary.get("lower_timeframe_stats") or {}),
        "",
        "## M15 Outcome To Truth Outcome",
        "",
        _markdown_table(summary.get("m15_to_truth") or []),
        "",
        "## Cohort Diagnostics",
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
        "### Framework",
        "",
        _markdown_table(summary.get("by_framework") or []),
        "",
        "### Regime",
        "",
        _markdown_table(summary.get("by_regime") or []),
        "",
        "### Symbol x Session",
        "",
        _markdown_table(summary.get("by_symbol_session") or []),
        "",
        "## Top Failure Buckets By Cohort",
        "",
        "### Symbol",
        "",
        _markdown_table(_top_rows(summary.get("failure_by_symbol") or [], limit=30)),
        "",
        "### Session",
        "",
        _markdown_table(_top_rows(summary.get("failure_by_session") or [], limit=30)),
        "",
        "### Year",
        "",
        _markdown_table(_top_rows(summary.get("failure_by_year") or [], limit=30)),
        "",
        "### Framework",
        "",
        _markdown_table(_top_rows(summary.get("failure_by_framework") or [], limit=30)),
        "",
        "### Regime",
        "",
        _markdown_table(_top_rows(summary.get("failure_by_regime") or [], limit=30)),
        "",
        "## Synthesis",
        "",
        *_synthesis_bullets(summary),
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_report(path: str | Path, content: str) -> Path:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(content, encoding="utf-8")
    return report_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Historical opportunity JSONL. Defaults to latest base run.")
    parser.add_argument("--input-glob", default=DEFAULT_INPUT_GLOB)
    parser.add_argument("--data-dir", action="append", help="MT5 export directory. Repeatable.")
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument(
        "--lower-timeframe",
        action="append",
        choices=("M1", "M5"),
        help="Lower timeframe priority. Repeatable; default is M1 then M5.",
    )
    parser.add_argument(
        "--row-filter",
        choices=("all", "would_send_ai", "setup_ok", "same_bar", "no_entry"),
        default="all",
    )
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--write", action="store_true", help="Write markdown audit report.")
    parser.add_argument("--quiet", action="store_true", help="Print compact run summary.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_path = Path(args.input) if args.input else find_latest_input(args.input_glob)
    lower_timeframes = args.lower_timeframe or list(DEFAULT_LOWER_TIMEFRAMES)
    summary = build_truth_layer(
        input_path=input_path,
        data_dirs=args.data_dir or list(DEFAULT_DATA_DIRS),
        lower_timeframes=lower_timeframes,
        output_root=args.output_root,
        row_filter=args.row_filter,
        max_rows=args.max_rows,
    )
    report = render_report(summary)
    if args.write:
        report_path = write_report(args.report_path, report)
        summary["report_path"] = str(report_path)
    if args.quiet:
        print(
            json.dumps(
                {
                    "rows": summary.get("rows"),
                    "output_jsonl": summary.get("output_jsonl"),
                    "output_summary": summary.get("output_summary"),
                    "report_path": summary.get("report_path"),
                    "truth_outcomes": summary.get("truth_outcomes"),
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _base_truth_row(row: Mapping[str, Any]) -> dict[str, Any]:
    selected_fields = (
        "opportunity_key",
        "symbol",
        "broker_symbol",
        "external_symbol",
        "timeframe",
        "bar_time_utc",
        "candle_close_utc",
        "session",
        "kill_zone",
        "year",
        "month",
        "day_of_week",
        "hour_utc",
        "bundle_id",
        "pre_ai_gate_policy",
        "pre_ai_gate_status",
        "pre_ai_gate_reason",
        "would_send_ai",
        "deterministic_bias",
        "deterministic_bias_source",
        "deterministic_bias_d1",
        "deterministic_bias_h4",
        "deterministic_bias_h1",
        "deterministic_bias_m15",
        "all_timeframes_complete",
        "mechanical_setup_status",
        "mechanical_skip_reason",
        "mechanical_side",
        "mechanical_framework",
        "mechanical_entry",
        "mechanical_sl",
        "mechanical_tp",
        "mechanical_rr",
        "mechanical_sl_buffer_used",
        "mechanical_h1_atr",
        "mechanical_tp_source",
        "external_snapshot_match_status",
        "external_snapshot_as_of_utc",
        "external_snapshot_missing_sources",
        "feature_availability_flags",
        "paid_ai_replay",
        "ai_call_attempted",
        "ai_call_count",
    )
    output = {
        "schema_version": SCHEMA_VERSION,
        **{field: row.get(field) for field in selected_fields},
        "m15_outcome": row.get("mechanical_outcome"),
        "m15_realized_r": row.get("mechanical_realized_r"),
        "m15_bars_in_trade": row.get("mechanical_bars_in_trade"),
        "m15_exit_time": row.get("mechanical_exit_time"),
        "m15_outcome_skip_reason": row.get("mechanical_outcome_skip_reason"),
    }
    for source in ("fred", "cftc_cot", "lbma_calendar", "wgc", "flashalpha_gex"):
        output[f"feature_available__{source}"] = row.get(f"feature_available__{source}")
    output["truth_regime"] = _regime_label(row)
    output["truth_bias_stack"] = _bias_stack(row)
    return output


def _classify_gate_reject(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "truth_source": "deterministic_pre_ai_gate",
        "truth_source_timeframe": "NONE",
        "lower_tf_timeframe": None,
        "lower_tf_local_coverage": None,
        "lower_tf_future_rows_available": None,
        "truth_outcome": row.get("pre_ai_gate_status") or "PRE_AI_REJECT",
        "truth_realized_r": None,
        "truth_bars_in_trade": None,
        "truth_exit_time": None,
        "truth_fill_status": "NOT_APPLICABLE",
        "truth_exit_status": "NOT_APPLICABLE",
        "truth_failure_bucket": _gate_failure_bucket(row),
        "truth_ambiguity_bucket": "NOT_REFINABLE_PRE_AI_REJECT",
        "truth_confidence": "NONE",
        "truth_selection_reason": "row_failed_before_mechanical_setup",
    }


def _classify_setup_skip(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "truth_source": "mechanical_setup",
        "truth_source_timeframe": "NONE",
        "lower_tf_timeframe": None,
        "lower_tf_local_coverage": None,
        "lower_tf_future_rows_available": None,
        "truth_outcome": "SETUP_NOT_REFINABLE",
        "truth_realized_r": None,
        "truth_bars_in_trade": None,
        "truth_exit_time": None,
        "truth_fill_status": "NOT_APPLICABLE",
        "truth_exit_status": "NOT_APPLICABLE",
        "truth_failure_bucket": _setup_failure_bucket(row.get("mechanical_skip_reason")),
        "truth_ambiguity_bucket": "NOT_REFINABLE_MECHANICAL_SETUP",
        "truth_confidence": "NONE",
        "truth_selection_reason": "mechanical_setup_not_ok",
    }


def _truth_projection(
    row: Mapping[str, Any],
    selected: Mapping[str, Any],
    lower_diagnostics: Mapping[str, LowerTimeframeDiagnostics],
) -> dict[str, Any]:
    outcome = str(selected.get("outcome") or "UNKNOWN")
    realized = selected.get("realized_r")
    source = str(selected.get("source") or "m15")
    source_timeframe = str(selected.get("timeframe") or "M15")
    selected_diag = lower_diagnostics.get(source_timeframe)
    projection = {
        "truth_source": source,
        "truth_source_timeframe": source_timeframe,
        "lower_tf_timeframe": source_timeframe if source == "lower_timeframe" else None,
        "lower_tf_local_coverage": (
            selected_diag.local_coverage if selected_diag is not None else None
        ),
        "lower_tf_future_rows_available": (
            selected_diag.future_rows_available if selected_diag is not None else None
        ),
        "lower_tf_contiguous_bars_from_candle": (
            selected_diag.contiguous_bars_from_candle if selected_diag is not None else None
        ),
        "lower_tf_gap_count_in_horizon": (
            selected_diag.gap_count_in_horizon if selected_diag is not None else None
        ),
        "lower_tf_first_gap_utc": selected_diag.first_gap_utc if selected_diag is not None else None,
        "lower_tf_horizon_complete": (
            selected_diag.horizon_complete if selected_diag is not None else None
        ),
        "truth_outcome": outcome,
        "truth_realized_r": realized,
        "truth_bars_in_trade": selected.get("bars_in_trade"),
        "truth_exit_time": selected.get("exit_time"),
        "truth_fill_status": _fill_status(outcome),
        "truth_exit_status": _exit_status(outcome, realized),
        "truth_failure_bucket": _outcome_bucket(outcome, realized, selected),
        "truth_ambiguity_bucket": _ambiguity_bucket(
            row,
            outcome,
            source,
            selected_diag,
            lower_attempted=bool(lower_diagnostics),
        ),
        "truth_confidence": _confidence(row, outcome, source, selected_diag),
        "truth_selection_reason": selected.get("selection_reason"),
    }
    return projection


def _select_truth_source(
    row: Mapping[str, Any],
    lower_results: Mapping[str, Mapping[str, Any]],
    lower_diagnostics: Mapping[str, LowerTimeframeDiagnostics],
) -> dict[str, Any]:
    candidates: list[tuple[int, dict[str, Any]]] = []
    for timeframe, refined in lower_results.items():
        diagnostics = lower_diagnostics[timeframe]
        score = _lower_truth_score(refined, diagnostics)
        outcome = _lower_truth_outcome(refined, diagnostics, score)
        candidates.append(
            (
                score,
                {
                    "source": "lower_timeframe",
                    "timeframe": timeframe,
                    "outcome": outcome,
                    "raw_refined_outcome": refined.get("refined_outcome"),
                    "realized_r": refined.get("refined_realized_r")
                    if outcome == refined.get("refined_outcome")
                    else None,
                    "bars_in_trade": refined.get("refined_bars_in_trade"),
                    "exit_time": refined.get("refined_exit_time"),
                    "score": score,
                    "selection_reason": _lower_selection_reason(refined, diagnostics, score),
                },
            )
        )
    candidates.sort(key=lambda item: item[0], reverse=True)
    best = candidates[0][1] if candidates else None
    best_score = candidates[0][0] if candidates else 0
    m15_outcome = str(row.get("mechanical_outcome") or "UNKNOWN")

    if best is not None and best_score >= 70:
        return best
    if best is not None and m15_outcome == "SAME_BAR" and best_score >= 25:
        return best
    return {
        "source": "m15_mechanical",
        "timeframe": "M15",
        "outcome": m15_outcome,
        "realized_r": row.get("mechanical_realized_r"),
        "bars_in_trade": row.get("mechanical_bars_in_trade"),
        "exit_time": row.get("mechanical_exit_time"),
        "score": 50,
        "selection_reason": "lower_timeframe_unavailable_or_not_more_reliable",
    }


def _lower_truth_score(
    refined: Mapping[str, Any],
    diagnostics: LowerTimeframeDiagnostics,
) -> int:
    if not diagnostics.local_coverage:
        return 0
    outcome = str(refined.get("refined_outcome") or "")
    bonus = _timeframe_bonus(diagnostics.timeframe)
    if outcome in {"TP", "SL"} and _exit_before_first_gap(refined, diagnostics):
        return 100 + bonus
    if outcome == "TIMEOUT" and diagnostics.horizon_complete:
        return 95 + bonus
    if outcome == "NO_ENTRY" and diagnostics.horizon_complete:
        return 90 + bonus
    if outcome == "SAME_BAR" and _exit_before_first_gap(refined, diagnostics):
        return 75 + bonus
    if outcome == "NO_FULL_HORIZON":
        return 40 + bonus
    if diagnostics.gap_count_in_horizon:
        return 25 + bonus
    return 10 + bonus


def _lower_truth_outcome(
    refined: Mapping[str, Any],
    diagnostics: LowerTimeframeDiagnostics,
    score: int,
) -> str:
    outcome = str(refined.get("refined_outcome") or "UNKNOWN")
    if score >= 70:
        return outcome
    if diagnostics.gap_count_in_horizon:
        return "LOWER_TF_GAPPY"
    return outcome


def _lower_selection_reason(
    refined: Mapping[str, Any],
    diagnostics: LowerTimeframeDiagnostics,
    score: int,
) -> str:
    if score >= 70:
        return "lower_timeframe_local_contiguous_resolution"
    if not diagnostics.local_coverage:
        return diagnostics.skip_reason or "no_local_lower_timeframe_data"
    if diagnostics.gap_count_in_horizon:
        return "lower_timeframe_gap_before_trustworthy_resolution"
    return str(refined.get("refined_skip_reason") or "lower_timeframe_data_limited")


def _add_lower_fields(
    output: dict[str, Any],
    timeframe: str,
    refined: Mapping[str, Any],
    diagnostics: LowerTimeframeDiagnostics,
) -> None:
    prefix = timeframe.lower()
    output.update(
        {
            f"{prefix}_refinement_attempted": True,
            f"{prefix}_refined_outcome": refined.get("refined_outcome"),
            f"{prefix}_refined_realized_r": refined.get("refined_realized_r"),
            f"{prefix}_refined_bars_in_trade": refined.get("refined_bars_in_trade"),
            f"{prefix}_refined_exit_time": refined.get("refined_exit_time"),
            f"{prefix}_refined_skip_reason": refined.get("refined_skip_reason"),
            f"{prefix}_local_coverage": diagnostics.local_coverage,
            f"{prefix}_future_rows_available": diagnostics.future_rows_available,
            f"{prefix}_horizon_bars": diagnostics.horizon_bars,
            f"{prefix}_contiguous_bars_from_candle": diagnostics.contiguous_bars_from_candle,
            f"{prefix}_gap_count_in_horizon": diagnostics.gap_count_in_horizon,
            f"{prefix}_first_gap_utc": diagnostics.first_gap_utc,
            f"{prefix}_max_gap_minutes": diagnostics.max_gap_minutes,
            f"{prefix}_horizon_complete": diagnostics.horizon_complete,
            f"{prefix}_diagnostic_skip_reason": diagnostics.skip_reason,
        }
    )


def _add_empty_lower_fields(output: dict[str, Any], lower_timeframes: Sequence[str]) -> None:
    for timeframe in lower_timeframes:
        prefix = timeframe.lower()
        output.update(
            {
                f"{prefix}_refinement_attempted": False,
                f"{prefix}_refined_outcome": None,
                f"{prefix}_refined_realized_r": None,
                f"{prefix}_refined_bars_in_trade": None,
                f"{prefix}_refined_exit_time": None,
                f"{prefix}_refined_skip_reason": None,
                f"{prefix}_local_coverage": None,
                f"{prefix}_future_rows_available": None,
                f"{prefix}_horizon_bars": _scaled_hold_bars(timeframe),
                f"{prefix}_contiguous_bars_from_candle": None,
                f"{prefix}_gap_count_in_horizon": None,
                f"{prefix}_first_gap_utc": None,
                f"{prefix}_max_gap_minutes": None,
                f"{prefix}_horizon_complete": None,
                f"{prefix}_diagnostic_skip_reason": None,
            }
        )


def _gate_failure_bucket(row: Mapping[str, Any]) -> str:
    status = str(row.get("pre_ai_gate_status") or "")
    reason = str(row.get("pre_ai_gate_reason") or "")
    if status == "SKIP_FIRST_NY_CANDLE":
        return "SETUP_SKIP_FIRST_NY_CANDLE"
    if "L2_h4_conflict" in reason:
        return "SETUP_HTF_CONFLICT"
    if "L1_no_direction" in reason:
        return "SETUP_HTF_NO_DIRECTION"
    if "no_bullish_pois" in reason or "no_bearish_pois" in reason:
        return "SETUP_MISSING_OR_LOW_QUALITY_POI"
    if status == "PRE_AI_POI_REJECT":
        return "SETUP_PRE_AI_POI_REJECT"
    if status == "PRE_SCREEN_REJECT":
        return "SETUP_PRE_SCREEN_REJECT"
    return "SETUP_DETERMINISTIC_REJECT"


def _setup_failure_bucket(reason: Any) -> str:
    reason_text = str(reason or "")
    if any(token in reason_text for token in ("NO_OBS", "NO_BULLISH", "NO_BEARISH")):
        return "SETUP_MISSING_OR_LOW_QUALITY_POI"
    if "ALL_MITIGATED" in reason_text:
        return "SETUP_POI_ALREADY_MITIGATED"
    if any(token in reason_text for token in ("BAD_SL_BUFFER", "DEGENERATE_SL")):
        return "SETUP_INVALID_RISK_GEOMETRY"
    if "UNSUPPORTED_FRAMEWORK" in reason_text:
        return "SETUP_UNSUPPORTED_FRAMEWORK"
    return "SETUP_NOT_REFINABLE"


def _outcome_bucket(
    outcome: str,
    realized: Any,
    selected: Mapping[str, Any],
) -> str:
    if outcome == "TP":
        return "SUCCESS_TP_FIRST"
    if outcome == "SL":
        bars = _int_or_none(selected.get("bars_in_trade"))
        if bars is not None and bars <= 1:
            return "FAIL_IMMEDIATE_STOP_AFTER_FILL"
        return "FAIL_STOP_FIRST"
    if outcome == "TIMEOUT":
        value = _float_or_none(realized)
        if value is None:
            return "TIMEOUT_UNRESOLVED"
        if value > 0:
            return "MIXED_TIMEOUT_POSITIVE"
        if value < 0:
            return "FAIL_TIMEOUT_NEGATIVE"
        return "MIXED_TIMEOUT_FLAT"
    if outcome == "NO_ENTRY":
        return "FAIL_NO_FILL"
    if outcome == "SAME_BAR":
        return "AMBIGUOUS_FILL_AND_EXIT_SAME_BAR"
    if outcome == "NO_FULL_HORIZON":
        return "DATA_INCOMPLETE_FUTURE_HORIZON"
    if outcome == "LOWER_TF_GAPPY":
        return "DATA_LOWER_TF_GAP_BEFORE_RESOLUTION"
    if outcome in {"NO_LOCAL_OHLCV", "NO_DATA"}:
        return "DATA_NO_LOCAL_LOWER_TF"
    return "UNRESOLVED_TRUTH_OUTCOME"


def _ambiguity_bucket(
    row: Mapping[str, Any],
    outcome: str,
    source: str,
    diagnostics: LowerTimeframeDiagnostics | None,
    *,
    lower_attempted: bool,
) -> str:
    if source == "lower_timeframe":
        if outcome in RESOLVED_OUTCOMES or outcome == "NO_ENTRY":
            return "LOWER_TF_RESOLVED"
        if outcome == "SAME_BAR":
            return "LOWER_TF_SAME_BAR_REMAINS"
        if outcome == "NO_FULL_HORIZON":
            return "LOWER_TF_INCOMPLETE_HORIZON"
        if outcome == "LOWER_TF_GAPPY":
            return "LOWER_TF_GAPPY"
        if diagnostics is not None and not diagnostics.local_coverage:
            return "NO_LOCAL_LOWER_TF"
        return "LOWER_TF_UNRESOLVED"
    m15_outcome = str(row.get("mechanical_outcome") or "")
    if m15_outcome == "SAME_BAR":
        return "M15_SAME_BAR_NO_LOCAL_LOWER_TF"
    if not lower_attempted:
        return "M15_ONLY_NO_LOWER_TF_REQUESTED"
    return "M15_ONLY_LOWER_TF_UNAVAILABLE"


def _confidence(
    row: Mapping[str, Any],
    outcome: str,
    source: str,
    diagnostics: LowerTimeframeDiagnostics | None,
) -> str:
    if source == "lower_timeframe":
        if diagnostics is None or not diagnostics.local_coverage:
            return "LOW"
        if outcome in {"TP", "SL"}:
            return "HIGH"
        if outcome in {"NO_ENTRY", "TIMEOUT"} and diagnostics.horizon_complete:
            return "HIGH"
        if outcome == "SAME_BAR":
            return "LOW"
        if outcome in {"NO_FULL_HORIZON", "LOWER_TF_GAPPY"}:
            return "LOW"
        return "MEDIUM"
    if outcome == "SAME_BAR":
        return "LOW"
    if outcome in RESOLVED_OUTCOMES or outcome == "NO_ENTRY":
        return "MEDIUM" if row.get("all_timeframes_complete") else "LOW"
    return "NONE"


def _fill_status(outcome: str) -> str:
    if outcome in {"TP", "SL", "TIMEOUT"}:
        return "FILLED"
    if outcome == "NO_ENTRY":
        return "NOT_FILLED"
    if outcome == "SAME_BAR":
        return "FILL_AND_EXIT_AMBIGUOUS"
    if outcome in {"NO_FULL_HORIZON", "LOWER_TF_GAPPY", "NO_LOCAL_OHLCV", "NO_DATA"}:
        return "UNKNOWN_DATA_LIMITED"
    return "UNKNOWN"


def _exit_status(outcome: str, realized: Any) -> str:
    if outcome == "TP":
        return "TP_FIRST"
    if outcome == "SL":
        return "SL_FIRST"
    if outcome == "TIMEOUT":
        value = _float_or_none(realized)
        if value is None:
            return "TIMEOUT_UNRESOLVED"
        if value > 0:
            return "TIMEOUT_POSITIVE_MARK"
        if value < 0:
            return "TIMEOUT_NEGATIVE_MARK"
        return "TIMEOUT_FLAT_MARK"
    if outcome == "NO_ENTRY":
        return "NO_EXIT_NO_FILL"
    if outcome == "SAME_BAR":
        return "SAME_BAR_AMBIGUOUS"
    if outcome == "NO_FULL_HORIZON":
        return "NO_EXIT_INCOMPLETE_HORIZON"
    if outcome == "LOWER_TF_GAPPY":
        return "NO_EXIT_GAPPY_LOWER_TF"
    return "UNKNOWN"


def _exit_before_first_gap(
    refined: Mapping[str, Any],
    diagnostics: LowerTimeframeDiagnostics,
) -> bool:
    if diagnostics.first_gap_utc is None:
        return True
    exit_time = refined.get("refined_exit_time")
    if not exit_time:
        return False
    try:
        return ensure_utc(str(exit_time)) < ensure_utc(diagnostics.first_gap_utc)
    except (TypeError, ValueError):
        return False


def _normalize_lower_timeframes(timeframes: Sequence[str]) -> tuple[str, ...]:
    seen: list[str] = []
    for timeframe in timeframes:
        key = timeframe.upper()
        if key not in {"M1", "M5"}:
            raise ValueError(f"unsupported lower timeframe {timeframe!r}")
        if key not in seen:
            seen.append(key)
    return tuple(seen or DEFAULT_LOWER_TIMEFRAMES)


def _row_matches_filter(row: Mapping[str, Any], row_filter: str) -> bool:
    if row_filter == "all":
        return True
    if row_filter == "would_send_ai":
        return bool(row.get("would_send_ai"))
    if row_filter == "setup_ok":
        return row.get("mechanical_setup_status") == "OK"
    if row_filter == "same_bar":
        return row.get("mechanical_outcome") == "SAME_BAR"
    if row_filter == "no_entry":
        return row.get("mechanical_outcome") == "NO_ENTRY"
    raise ValueError(f"unknown row_filter {row_filter!r}")


def _regime_label(row: Mapping[str, Any]) -> str:
    bias = row.get("deterministic_bias") or "none"
    source = row.get("deterministic_bias_source") or "none"
    return f"{bias}|{source}"


def _bias_stack(row: Mapping[str, Any]) -> str:
    return (
        f"D1={row.get('deterministic_bias_d1') or row.get('structure_direction__D1') or 'unknown'}|"
        f"H4={row.get('deterministic_bias_h4') or row.get('structure_direction__H4') or 'unknown'}|"
        f"H1={row.get('deterministic_bias_h1') or row.get('structure_direction__H1') or 'unknown'}|"
        f"M15={row.get('deterministic_bias_m15') or row.get('structure_direction__M15') or 'unknown'}"
    )


def _timeframe_bonus(timeframe: str) -> int:
    return {"M1": 2, "M5": 1}.get(timeframe.upper(), 0)


def _synthesis_bullets(summary: Mapping[str, Any]) -> list[str]:
    rows = int(summary.get("rows") or 0)
    unique = int(summary.get("unique_keys") or 0)
    ai_calls = int(summary.get("ai_call_count_sum") or 0)
    outcomes = {row["truth_outcome"]: row["rows"] for row in summary.get("truth_outcomes") or []}
    confidence = {row["truth_confidence"]: row["rows"] for row in summary.get("confidence") or []}
    selected = {
        row["truth_source_timeframe"]: row["rows"]
        for row in summary.get("selected_timeframes") or []
    }
    bullets = [
        f"- Classified {rows:,} opportunity rows with {unique:,} unique keys and {ai_calls} AI calls.",
        "- The truth layer separates setup rejects, no-fill outcomes, resolved TP/SL paths, same-bar ambiguity, lower-timeframe gaps, and incomplete lower-timeframe horizons before any parameter sweep.",
    ]
    if outcomes:
        bullets.append(
            "- Core truth outcomes: "
            f"TP={outcomes.get('TP', 0):,}, SL={outcomes.get('SL', 0):,}, "
            f"TIMEOUT={outcomes.get('TIMEOUT', 0):,}, NO_ENTRY={outcomes.get('NO_ENTRY', 0):,}, "
            f"SAME_BAR={outcomes.get('SAME_BAR', 0):,}."
        )
    if selected:
        bullets.append(
            "- Selected truth source counts: "
            + ", ".join(f"{key}={value:,}" for key, value in sorted(selected.items()))
            + "."
        )
    if confidence:
        bullets.append(
            "- Confidence mix: "
            + ", ".join(f"{key}={value:,}" for key, value in sorted(confidence.items()))
            + ". Low/none-confidence rows should be excluded or sensitivity-tested before optimization."
        )
    bullets.append(
        "- This report is a label-quality audit only. It does not justify live trading changes, prompt changes, or buffer/offset tuning by itself."
    )
    return bullets


def _markdown_lower_timeframes(payload: Mapping[str, Any]) -> str:
    rows = []
    for timeframe, stats in sorted(payload.items()):
        attempted = int(stats.get("attempted") or 0)
        local = int(stats.get("local_coverage") or 0)
        complete = int(stats.get("horizon_complete") or 0)
        selected = int(stats.get("selected") or 0)
        gappy = int(stats.get("gappy") or 0)
        rows.append(
            {
                "timeframe": timeframe,
                "attempted": attempted,
                "local_coverage": local,
                "local_coverage_rate": _rate(local, attempted),
                "horizon_complete": complete,
                "horizon_complete_rate": _rate(complete, attempted),
                "gappy": gappy,
                "selected": selected,
                "tp": stats.get("outcome:TP", 0),
                "sl": stats.get("outcome:SL", 0),
                "timeout": stats.get("outcome:TIMEOUT", 0),
                "no_entry": stats.get("outcome:NO_ENTRY", 0),
                "same_bar": stats.get("outcome:SAME_BAR", 0),
                "no_full_horizon": stats.get("outcome:NO_FULL_HORIZON", 0),
            }
        )
    return _markdown_table(rows)


def _counter_rows(counter: Counter[str], key_name: str) -> list[dict[str, Any]]:
    return [
        {key_name: key, "rows": value}
        for key, value in counter.most_common()
    ]


def _counter_pair_rows(counter: Counter[str], columns: tuple[str, str]) -> list[dict[str, Any]]:
    rows = []
    for key, value in counter.most_common():
        if PAIR_DELIMITER in key:
            left, right = key.split(PAIR_DELIMITER, 1)
        else:
            left, right = key.split("|", 1)
        rows.append({columns[0]: left, columns[1]: right, "rows": value})
    return rows


def _pair_key(left: Any, right: Any) -> str:
    return f"{left}{PAIR_DELIMITER}{right}"


def _stats_rows(groups: Mapping[str, TruthGroupStats], key_name: str) -> list[dict[str, Any]]:
    return [stats.as_row(key_name, key) for key, stats in sorted(groups.items())]


def _top_rows(rows: Sequence[Mapping[str, Any]], *, limit: int) -> list[Mapping[str, Any]]:
    return sorted(rows, key=lambda row: int(row.get("rows") or 0), reverse=True)[:limit]


def _markdown_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    preferred = (
        "symbol",
        "session",
        "year",
        "framework",
        "regime",
        "symbol_session",
        "truth_outcome",
        "truth_failure_bucket",
        "truth_ambiguity_bucket",
        "truth_confidence",
        "truth_source_timeframe",
        "truth_fill_status",
        "truth_exit_status",
        "m15_outcome",
        "timeframe",
        "rows",
        "resolved_r_n",
        "mean_r",
        "win_rate",
        "tp",
        "sl",
        "timeout",
        "no_entry",
        "same_bar",
        "no_full_horizon",
        "lower_tf_gappy",
        "attempted",
        "local_coverage",
        "local_coverage_rate",
        "horizon_complete",
        "horizon_complete_rate",
        "gappy",
        "selected",
        "high_confidence",
        "medium_confidence",
        "low_confidence",
        "none_confidence",
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


def _rate(numer: int | float, denom: int | float) -> float:
    return round(float(numer) / float(denom), 6) if denom else 0.0


def _mean(total: float, count: int) -> float | None:
    return round(float(total) / count, 6) if count else None


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    raise SystemExit(main())
