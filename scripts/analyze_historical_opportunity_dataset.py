#!/usr/bin/env python3
"""Analyze and refine Phase 3 historical pre-AI opportunity datasets.

This research-only script consumes the output of
``build_historical_opportunity_dataset.py``. It produces compact synthesis
artifacts, optional lower-timeframe mechanical refinements, and exploratory
feature-separation tables without calling any AI API or changing live logic.
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
from typing import Any, Iterable, Iterator, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.build_external_feed_validation_dataset import TIMEFRAME_MINUTES  # noqa: E402
from scripts.build_historical_opportunity_dataset import (  # noqa: E402
    DEFAULT_DATA_DIRS,
    DEFAULT_BUNDLE_ID,
    CandleSeries,
    _find_ohlcv_path,
)
from src.components.external_feeds import ensure_utc, safe_slug, utc_now  # noqa: E402
from src.research_infra.dumb_baseline import (  # noqa: E402
    MechanicalSetup,
    resolve_mechanical_outcome,
)


DEFAULT_INPUT_GLOB = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "phase3_historical_pre_ai_opportunities_v1_*.jsonl"
)
DEFAULT_REPORT_PATH = (
    "research/phase_3_external_feed_validation/"
    "HISTORICAL_OPPORTUNITY_SYNTHESIS_2026-05-01.md"
)
DEFAULT_OUTPUT_ROOT = (
    "data/external/validation/calendar_macro_bundle_v1/"
    "historical_opportunities/analysis"
)
DEFAULT_MAX_HOLD_M15_BARS = 96
EXTERNAL_PREFIXES = ("fred__", "cftc_cot__", "wgc__", "lbma_calendar__", "flashalpha_gex__")
TIMESTAMP_FIELD_SUFFIXES = (
    "_utc",
    "__published_at_utc",
    "__as_of_utc",
    "__fix_time_utc",
    "__fetched_at_utc",
)
NON_FEATURE_TOKENS = (
    "__available",
    "__source",
    "__series_id",
    "__report_type",
    "__dataset",
    "__proxy_symbol",
    "__market_name",
    "__observation_date",
    "__report_date",
    "__realtime_start",
    "__realtime_end",
    "__publication_time_model",
)


@dataclass
class GroupStats:
    rows: int = 0
    would_send_ai: int = 0
    all_timeframes_complete: int = 0
    realized_n: int = 0
    realized_sum: float = 0.0
    realized_wins: int = 0
    gate_status: Counter[str] = field(default_factory=Counter)
    mechanical_outcomes: Counter[str] = field(default_factory=Counter)

    def add(self, row: Mapping[str, Any]) -> None:
        self.rows += 1
        if row.get("all_timeframes_complete"):
            self.all_timeframes_complete += 1
        status = str(row.get("pre_ai_gate_status") or "")
        self.gate_status[status] += 1
        if row.get("would_send_ai"):
            self.would_send_ai += 1
        outcome = str(row.get("mechanical_outcome") or "NOT_EVALUATED")
        self.mechanical_outcomes[outcome] += 1
        realized = row.get("mechanical_realized_r")
        if realized is not None:
            try:
                value = float(realized)
            except (TypeError, ValueError):
                return
            self.realized_n += 1
            self.realized_sum += value
            if value > 0:
                self.realized_wins += 1

    def as_row(self, key_name: str, key: str) -> dict[str, Any]:
        return {
            key_name: key,
            "rows": self.rows,
            "would_send_ai": self.would_send_ai,
            "would_send_ai_rate": _rate(self.would_send_ai, self.rows),
            "complete_rate": _rate(self.all_timeframes_complete, self.rows),
            "mechanical_realized_n": self.realized_n,
            "mechanical_mean_r_realized": _mean(self.realized_sum, self.realized_n),
            "mechanical_win_rate_realized": _rate(self.realized_wins, self.realized_n),
            "m15_tp": self.mechanical_outcomes.get("TP", 0),
            "m15_sl": self.mechanical_outcomes.get("SL", 0),
            "m15_timeout": self.mechanical_outcomes.get("TIMEOUT", 0),
            "m15_same_bar": self.mechanical_outcomes.get("SAME_BAR", 0),
            "m15_no_entry": self.mechanical_outcomes.get("NO_ENTRY", 0),
        }


@dataclass
class DatasetAccumulator:
    by_symbol: dict[str, GroupStats] = field(default_factory=lambda: defaultdict(GroupStats))
    by_year: dict[str, GroupStats] = field(default_factory=lambda: defaultdict(GroupStats))
    by_session: dict[str, GroupStats] = field(default_factory=lambda: defaultdict(GroupStats))
    by_symbol_session: dict[str, GroupStats] = field(default_factory=lambda: defaultdict(GroupStats))
    by_symbol_year: dict[str, GroupStats] = field(default_factory=lambda: defaultdict(GroupStats))
    gate_reasons: Counter[str] = field(default_factory=Counter)
    feature_available_all: Counter[str] = field(default_factory=Counter)
    feature_available_would: Counter[str] = field(default_factory=Counter)
    feature_missing_all: Counter[str] = field(default_factory=Counter)
    feature_missing_would: Counter[str] = field(default_factory=Counter)
    feature_values: dict[str, list[tuple[float, float, str, str]]] = field(
        default_factory=lambda: defaultdict(list)
    )
    rows: int = 0
    would_send_ai: int = 0
    realized_n: int = 0
    realized_sum: float = 0.0
    same_bar: int = 0
    no_entry: int = 0
    no_ai_calls: int = 0
    ai_attempted: int = 0
    duplicate_keys: int = 0
    keys_seen: set[str] = field(default_factory=set)

    def add(self, row: Mapping[str, Any]) -> None:
        self.rows += 1
        key = str(row.get("opportunity_key") or "")
        if key:
            if key in self.keys_seen:
                self.duplicate_keys += 1
            self.keys_seen.add(key)
        if row.get("ai_call_attempted"):
            self.ai_attempted += 1
        self.no_ai_calls += int(row.get("ai_call_count") or 0)
        if row.get("would_send_ai"):
            self.would_send_ai += 1
        if row.get("mechanical_outcome") == "SAME_BAR":
            self.same_bar += 1
        if row.get("mechanical_outcome") == "NO_ENTRY":
            self.no_entry += 1

        for stats in (
            self.by_symbol[str(row.get("symbol") or "")],
            self.by_year[str(row.get("year") or "")],
            self.by_session[str(row.get("session") or "")],
            self.by_symbol_session[f"{row.get('symbol')}|{row.get('session')}"],
            self.by_symbol_year[f"{row.get('symbol')}|{row.get('year')}"],
        ):
            stats.add(row)

        self.gate_reasons[str(row.get("pre_ai_gate_reason") or "")] += 1
        flags = row.get("feature_availability_flags") or {}
        for source, available in flags.items():
            source_key = str(source)
            if available:
                self.feature_available_all[source_key] += 1
                if row.get("would_send_ai"):
                    self.feature_available_would[source_key] += 1
            else:
                self.feature_missing_all[source_key] += 1
                if row.get("would_send_ai"):
                    self.feature_missing_would[source_key] += 1

        realized = row.get("mechanical_realized_r")
        if realized is None:
            return
        try:
            realized_r = float(realized)
        except (TypeError, ValueError):
            return
        self.realized_n += 1
        self.realized_sum += realized_r
        symbol = str(row.get("symbol") or "")
        session = str(row.get("session") or "")
        for feature_key, feature_value in _iter_numeric_external_features(row):
            self.feature_values[feature_key].append(
                (float(feature_value), realized_r, symbol, session)
            )

    def to_summary(self) -> dict[str, Any]:
        return {
            "rows": self.rows,
            "unique_keys": len(self.keys_seen),
            "duplicate_keys": self.duplicate_keys,
            "would_send_ai": self.would_send_ai,
            "would_send_ai_rate": _rate(self.would_send_ai, self.rows),
            "ai_attempted_rows": self.ai_attempted,
            "ai_call_count_sum": self.no_ai_calls,
            "mechanical_realized_n": self.realized_n,
            "mechanical_mean_r_realized": _mean(self.realized_sum, self.realized_n),
            "m15_same_bar": self.same_bar,
            "m15_no_entry": self.no_entry,
            "top_gate_reasons": [
                {"pre_ai_gate_reason": reason, "rows": count}
                for reason, count in self.gate_reasons.most_common(15)
            ],
            "by_symbol": _stats_rows(self.by_symbol, "symbol"),
            "by_year": _stats_rows(self.by_year, "year"),
            "by_session": _stats_rows(self.by_session, "session"),
            "by_symbol_session": _stats_rows(self.by_symbol_session, "symbol_session"),
            "by_symbol_year": _stats_rows(self.by_symbol_year, "symbol_year"),
            "feature_coverage_all": _feature_rows(
                self.feature_available_all,
                self.feature_missing_all,
            ),
            "feature_coverage_would_send_ai": _feature_rows(
                self.feature_available_would,
                self.feature_missing_would,
            ),
            "external_feature_quintiles": _feature_quintiles(self.feature_values),
        }


@dataclass
class RefinementAccumulator:
    timeframe: str
    attempted: int = 0
    written: int = 0
    outcomes: Counter[str] = field(default_factory=Counter)
    by_original_outcome: Counter[str] = field(default_factory=Counter)
    by_symbol_outcome: Counter[str] = field(default_factory=Counter)
    resolved_r_n: int = 0
    resolved_r_sum: float = 0.0
    local_coverage: int = 0

    def add(self, row: Mapping[str, Any], refined: Mapping[str, Any]) -> None:
        self.attempted += 1
        self.written += 1
        outcome = str(refined.get("refined_outcome") or "UNKNOWN")
        original = str(row.get("mechanical_outcome") or "UNKNOWN")
        symbol = str(row.get("symbol") or "")
        self.outcomes[outcome] += 1
        self.by_original_outcome[f"{original}|{outcome}"] += 1
        self.by_symbol_outcome[f"{symbol}|{outcome}"] += 1
        if refined.get("lower_tf_local_coverage"):
            self.local_coverage += 1
        realized = refined.get("refined_realized_r")
        if realized is not None:
            self.resolved_r_n += 1
            self.resolved_r_sum += float(realized)

    def to_summary(self) -> dict[str, Any]:
        return {
            "timeframe": self.timeframe,
            "attempted": self.attempted,
            "written": self.written,
            "local_coverage": self.local_coverage,
            "local_coverage_rate": _rate(self.local_coverage, self.attempted),
            "resolved_r_n": self.resolved_r_n,
            "mean_r_realized": _mean(self.resolved_r_sum, self.resolved_r_n),
            "outcomes": dict(sorted(self.outcomes.items())),
            "by_original_outcome": _counter_pair_rows(
                self.by_original_outcome,
                ("m15_outcome", "refined_outcome"),
            ),
            "by_symbol_outcome": _counter_pair_rows(
                self.by_symbol_outcome,
                ("symbol", "refined_outcome"),
            ),
        }


def iter_jsonl(path: str | Path) -> Iterator[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def find_latest_input(pattern: str = DEFAULT_INPUT_GLOB) -> Path:
    paths = [
        path
        for path in Path().glob(pattern)
        if "closed_only" not in path.name and path.suffix == ".jsonl"
    ]
    if not paths:
        raise FileNotFoundError(f"no opportunity JSONL matches {pattern!r}")
    return max(paths, key=lambda path: path.stat().st_mtime)


def infer_summary_path(input_path: str | Path) -> Path | None:
    path = Path(input_path)
    candidate = path.with_name(path.stem + "_summary.json")
    return candidate if candidate.exists() else None


def analyze_dataset(
    *,
    input_path: str | Path,
    data_dirs: Sequence[str | Path],
    refine_timeframes: Sequence[str],
    refine_filter: str,
    output_root: str | Path,
    max_refine_rows: int | None,
) -> dict[str, Any]:
    input_path = Path(input_path)
    output_dir = Path(output_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    accumulator = DatasetAccumulator()
    refiners = {
        timeframe.upper(): RefinementAccumulator(timeframe=timeframe.upper())
        for timeframe in refine_timeframes
    }
    refinement_paths = {
        timeframe: output_dir / f"{safe_slug(input_path.stem)}_{timeframe.lower()}_refinements_{stamp}.jsonl"
        for timeframe in refiners
    }
    handles = {
        timeframe: path.open("w", encoding="utf-8", newline="\n")
        for timeframe, path in refinement_paths.items()
    }
    lower_cache: dict[tuple[str, str], list[dict[str, Any]]] = {}
    try:
        for row in iter_jsonl(input_path):
            accumulator.add(row)
            if not refiners or not _row_qualifies_for_refinement(row, refine_filter):
                continue
            for timeframe, refiner in refiners.items():
                if max_refine_rows is not None and refiner.attempted >= max_refine_rows:
                    continue
                refined = refine_mechanical_outcome(
                    row,
                    timeframe=timeframe,
                    data_dirs=data_dirs,
                    cache=lower_cache,
                )
                refiner.add(row, refined)
                handles[timeframe].write(json.dumps(refined, sort_keys=True) + "\n")
    finally:
        for handle in handles.values():
            handle.close()

    summary = accumulator.to_summary()
    summary.update(
        {
            "schema_version": "historical_opportunity_synthesis_v1",
            "created_at_utc": utc_now().isoformat(),
            "input_jsonl": str(input_path),
            "data_dirs": [str(Path(path)) for path in data_dirs],
            "refine_filter": refine_filter,
            "refinement_outputs": {
                timeframe: str(path) for timeframe, path in refinement_paths.items()
            },
            "refinements": {
                timeframe: refiner.to_summary()
                for timeframe, refiner in refiners.items()
            },
        }
    )
    summary_path = output_dir / f"{safe_slug(input_path.stem)}_synthesis_{stamp}.json"
    summary["output_summary"] = str(summary_path)
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return summary


def refine_mechanical_outcome(
    row: Mapping[str, Any],
    *,
    timeframe: str,
    data_dirs: Sequence[str | Path],
    cache: dict[tuple[str, str], list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    timeframe_key = timeframe.upper()
    if timeframe_key not in TIMEFRAME_MINUTES:
        raise ValueError(f"unsupported timeframe {timeframe!r}")
    cache = cache if cache is not None else {}
    symbol = str(row.get("symbol") or "")
    candle_close = ensure_utc(str(row.get("candle_close_utc")))
    setup = _setup_from_row(row, candle_close)
    output = {
        "opportunity_key": row.get("opportunity_key"),
        "symbol": symbol,
        "candle_close_utc": candle_close.isoformat(),
        "m15_outcome": row.get("mechanical_outcome"),
        "m15_realized_r": row.get("mechanical_realized_r"),
        "refined_timeframe": timeframe_key,
        "refined_max_hold_bars": _scaled_hold_bars(timeframe_key),
        "lower_tf_local_coverage": False,
    }
    if setup is None:
        return {
            **output,
            "refined_outcome": "NOT_REFINABLE",
            "refined_realized_r": None,
            "refined_bars_in_trade": None,
            "refined_exit_time": None,
            "refined_skip_reason": "missing_mechanical_setup",
        }
    rows = _load_lower_timeframe_rows(
        symbol=symbol,
        timeframe=timeframe_key,
        data_dirs=data_dirs,
        cache=cache,
    )
    if not rows:
        return {
            **output,
            "refined_outcome": "NO_DATA",
            "refined_realized_r": None,
            "refined_bars_in_trade": 0,
            "refined_exit_time": None,
            "refined_skip_reason": "lower_timeframe_missing",
        }
    start_idx = _first_after(rows, candle_close)
    max_gap = timedelta(minutes=TIMEFRAME_MINUTES[timeframe_key] * 2)
    if start_idx >= len(rows) or rows[start_idx]["time"] - candle_close > max_gap:
        return {
            **output,
            "refined_outcome": "NO_LOCAL_OHLCV",
            "refined_realized_r": None,
            "refined_bars_in_trade": 0,
            "refined_exit_time": None,
            "refined_skip_reason": "lower_timeframe_not_contiguous_at_candle",
            "first_future_bar_utc": (
                rows[start_idx]["time"].isoformat() if start_idx < len(rows) else None
            ),
        }

    max_hold_bars = _scaled_hold_bars(timeframe_key)
    future_rows_available = len(rows) - start_idx
    outcome = resolve_mechanical_outcome(
        setup,
        ohlcv_rows=rows,
        max_hold_bars=max_hold_bars,
        require_pending_fill=True,
    )
    refined_outcome = outcome.outcome
    refined_skip_reason = outcome.skip_reason
    if (
        future_rows_available < max_hold_bars
        and outcome.outcome in {"NO_ENTRY", "TIMEOUT"}
    ):
        refined_outcome = "NO_FULL_HORIZON"
        refined_skip_reason = "lower_timeframe_future_horizon_incomplete"
    return {
        **output,
        "lower_tf_local_coverage": True,
        "lower_tf_future_rows_available": future_rows_available,
        "refined_outcome": refined_outcome,
        "refined_realized_r": outcome.realized_r,
        "refined_bars_in_trade": outcome.bars_in_trade,
        "refined_exit_time": outcome.exit_time,
        "refined_skip_reason": refined_skip_reason,
    }


def render_report(
    summary: Mapping[str, Any],
    *,
    base_builder_summary: Mapping[str, Any] | None = None,
    closed_only_summary: Mapping[str, Any] | None = None,
) -> str:
    synthesis = _synthesis_bullets(
        summary,
        base_builder_summary=base_builder_summary,
        closed_only_summary=closed_only_summary,
    )
    lines = [
        "# Phase 3 Historical Opportunity Synthesis",
        "",
        f"**Created UTC:** {summary.get('created_at_utc')}",
        f"**Input:** `{summary.get('input_jsonl')}`",
        f"**Rows scanned:** {summary.get('rows')}",
        f"**Would send AI:** {summary.get('would_send_ai')} "
        f"({float(summary.get('would_send_ai_rate') or 0.0):.2%})",
        "",
        "## Interpretation Boundary",
        "",
        "- This is a research synthesis over deterministic pre-AI opportunity rows, not a paid AI replay.",
        "- `WOULD_SEND_AI` means deterministic pre-AI gates pass; it is not an AI CANDIDATE, L2 pass, or trade.",
        "- Mechanical R is diagnostic OB-retest behavior and is not a substitute for production-faithful AI outcome data.",
        "- External feature tables are exploratory screens; they are not DSR/PBO-cleared alpha claims.",
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
        "## Pre-AI Gate Shape",
        "",
        _markdown_table(summary.get("top_gate_reasons") or []),
        "",
        "## Symbol Diagnostics",
        "",
        _markdown_table(summary.get("by_symbol") or []),
        "",
        "## Year Diagnostics",
        "",
        _markdown_table(summary.get("by_year") or []),
        "",
        "## Session Diagnostics",
        "",
        _markdown_table(summary.get("by_session") or []),
        "",
        "## Symbol x Session Diagnostics",
        "",
        _markdown_table(summary.get("by_symbol_session") or []),
        "",
        "## Symbol x Year Diagnostics",
        "",
        _markdown_table(summary.get("by_symbol_year") or []),
        "",
    ]
    if closed_only_summary:
        lines.extend(
            [
                "## HTF Sensitivity",
                "",
                _markdown_table(_compare_builder_summaries(base_builder_summary, closed_only_summary)),
                "",
            ]
        )
    lines.extend(
        [
            "## Lower-Timeframe Mechanical Refinement",
            "",
            _markdown_refinements(summary.get("refinements") or {}),
            "",
            "## External Feature Coverage",
            "",
            "### All Opportunity Rows",
            "",
            _markdown_table(summary.get("feature_coverage_all") or []),
            "",
            "### `WOULD_SEND_AI` Rows",
            "",
            _markdown_table(summary.get("feature_coverage_would_send_ai") or []),
            "",
            "## Exploratory External Feature Separation",
            "",
            _markdown_table((summary.get("external_feature_quintiles") or [])[:20]),
            "",
            "## Synthesis",
            "",
            *synthesis,
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _synthesis_bullets(
    summary: Mapping[str, Any],
    *,
    base_builder_summary: Mapping[str, Any] | None = None,
    closed_only_summary: Mapping[str, Any] | None = None,
) -> list[str]:
    rows = int(summary.get("rows") or 0)
    would = int(summary.get("would_send_ai") or 0)
    realized_n = int(summary.get("mechanical_realized_n") or 0)
    realized_mean = summary.get("mechanical_mean_r_realized")
    same_bar = int(summary.get("m15_same_bar") or 0)
    no_entry = int(summary.get("m15_no_entry") or 0)
    bullets = [
        "- The historical pre-AI population is broad: "
        f"{would:,}/{rows:,} rows ({_rate(would, rows):.2%}) pass deterministic gates. "
        "That is enough substrate for downstream selection research, but it is not a trade signal.",
        "- Data-integrity checks are clean for this artifact: "
        f"{summary.get('unique_keys'):,} unique keys, "
        f"{summary.get('duplicate_keys')} duplicates, "
        f"{summary.get('ai_attempted_rows')} AI-attempted rows, "
        f"and {summary.get('ai_call_count_sum')} summed AI calls.",
    ]
    if realized_n:
        bullets.append(
            "- M15 mechanical OB-retest diagnostics remain positive but ambiguous: "
            f"{realized_n:,} resolved outcomes average {float(realized_mean):+.4f}R, "
            f"while {same_bar:,} same-bar and {no_entry:,} no-entry rows can distort "
            "fill/exit interpretation without lower-timeframe confirmation."
        )
    if base_builder_summary and closed_only_summary:
        base_would = int(base_builder_summary.get("would_send_ai") or 0)
        closed_would = int(closed_only_summary.get("would_send_ai") or 0)
        base_rate = float(base_builder_summary.get("would_send_ai_rate") or 0.0)
        closed_rate = float(closed_only_summary.get("would_send_ai_rate") or 0.0)
        bullets.append(
            "- HTF replay sensitivity is small at the population level: closed-only HTF context "
            f"changes `WOULD_SEND_AI` by {closed_would - base_would:+,} rows "
            f"({closed_rate - base_rate:+.2%}). Exact row-level studies should still pin one "
            "HTF policy because individual gates can flip near boundaries."
        )

    refinements = summary.get("refinements") or {}
    for timeframe in ("M5", "M1"):
        payload = refinements.get(timeframe)
        if not payload:
            continue
        attempted = int(payload.get("attempted") or 0)
        local = int(payload.get("local_coverage") or 0)
        resolved = int(payload.get("resolved_r_n") or 0)
        mean_r = payload.get("mean_r_realized")
        bullets.append(
            f"- {timeframe} refinement has limited local coverage "
            f"({local:,}/{attempted:,}, {_rate(local, attempted):.2%}) and "
            f"{resolved:,} resolved R outcomes averaging {float(mean_r):+.4f}R. "
            "The positive sign is useful as a diagnostic, but historical lower-timeframe depth "
            "is not yet sufficient for threshold or pip-offset optimization."
        )

    coverage = {
        str(row.get("source")): row
        for row in (summary.get("feature_coverage_would_send_ai") or [])
    }
    if coverage:
        fred = float((coverage.get("fred") or {}).get("available_rate") or 0.0)
        cftc = float((coverage.get("cftc_cot") or {}).get("available_rate") or 0.0)
        lbma = float((coverage.get("lbma_calendar") or {}).get("available_rate") or 0.0)
        flash = float((coverage.get("flashalpha_gex") or {}).get("available_rate") or 0.0)
        wgc = float((coverage.get("wgc") or {}).get("available_rate") or 0.0)
        bullets.append(
            "- External-feed interpretation is currently coverage-limited: "
            f"FRED covers {fred:.2%} of `WOULD_SEND_AI` rows, CFTC {cftc:.2%}, "
            f"LBMA {lbma:.2%}, FlashAlpha {flash:.2%}, and WGC {wgc:.2%}. "
            "The current substrate can screen macro/regime features, but it cannot yet prove "
            "multi-feed confluence."
        )
    bullets.extend(
        [
            "- The strongest next hypotheses are session/symbol/year conditioning, "
            "lower-timeframe entry realization, and DSR-controlled external-feature screens. "
            "Tokyo strength and 2026 strength should be treated as composition-confounded until "
            "split by symbol and deeper intraday coverage.",
            "- Parameter sweeps on buffers, offsets, or percentage levels should wait until the "
            "measurement layer is pinned: fixed HTF policy, enough M1/M5 history, explicit "
            "same-bar handling, and DSR/PBO accounting for all tested variants.",
        ]
    )
    return bullets


def write_report(path: str | Path, content: str) -> Path:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(content, encoding="utf-8")
    return report_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Historical opportunity JSONL. Defaults to latest base run.")
    parser.add_argument("--summary", help="Builder summary JSON for base input.")
    parser.add_argument("--closed-only-summary", help="Optional closed-only summary JSON for HTF comparison.")
    parser.add_argument("--data-dir", action="append", help="MT5 export directory. Repeatable.")
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument(
        "--refine-timeframe",
        action="append",
        choices=sorted(TIMEFRAME_MINUTES),
        help="Lower timeframe to use for mechanical outcome refinement. Repeatable.",
    )
    parser.add_argument(
        "--refine-filter",
        choices=("setup_ok", "same_bar", "realized_or_same_bar"),
        default="setup_ok",
    )
    parser.add_argument("--max-refine-rows", type=int)
    parser.add_argument("--write", action="store_true", help="Write synthesis report.")
    parser.add_argument("--quiet", action="store_true", help="Print only a compact run summary.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_path = Path(args.input) if args.input else find_latest_input()
    data_dirs = args.data_dir or list(DEFAULT_DATA_DIRS)
    summary_path = Path(args.summary) if args.summary else infer_summary_path(input_path)
    base_summary = _read_json(summary_path) if summary_path else None
    closed_summary = _read_json(args.closed_only_summary) if args.closed_only_summary else None
    summary = analyze_dataset(
        input_path=input_path,
        data_dirs=data_dirs,
        refine_timeframes=args.refine_timeframe or [],
        refine_filter=args.refine_filter,
        output_root=args.output_root,
        max_refine_rows=args.max_refine_rows,
    )
    report = render_report(
        summary,
        base_builder_summary=base_summary,
        closed_only_summary=closed_summary,
    )
    if args.write:
        report_path = write_report(args.report_path, report)
        summary["report_path"] = str(report_path)
    if args.quiet:
        print(
            json.dumps(
                {
                    "rows": summary.get("rows"),
                    "would_send_ai": summary.get("would_send_ai"),
                    "output_summary": summary.get("output_summary"),
                    "report_path": summary.get("report_path"),
                    "refinement_outputs": summary.get("refinement_outputs"),
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _setup_from_row(row: Mapping[str, Any], candle_close: datetime) -> MechanicalSetup | None:
    required = ("mechanical_entry", "mechanical_sl", "mechanical_tp", "mechanical_side")
    if any(row.get(key) in (None, "") for key in required):
        return None
    try:
        return MechanicalSetup(
            cand_id=str(row.get("opportunity_key") or ""),
            symbol=str(row.get("symbol") or ""),
            candle_close_time=candle_close,
            side=str(row.get("mechanical_side") or ""),
            framework=str(row.get("mechanical_framework") or "ob_retest"),
            ob_high=0.0,
            ob_low=0.0,
            entry=float(row["mechanical_entry"]),
            sl=float(row["mechanical_sl"]),
            tp=float(row["mechanical_tp"]),
            rr=float(row.get("mechanical_rr") or 0.0),
            sl_buffer_used=float(row.get("mechanical_sl_buffer_used") or 0.0),
            h1_atr=_float_or_none(row.get("mechanical_h1_atr")),
            tp_source=str(row.get("mechanical_tp_source") or ""),
        )
    except (TypeError, ValueError):
        return None


def _load_lower_timeframe_rows(
    *,
    symbol: str,
    timeframe: str,
    data_dirs: Sequence[str | Path],
    cache: dict[tuple[str, str], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    cache_key = (symbol.upper(), timeframe.upper())
    if cache_key in cache:
        return cache[cache_key]
    roots = [Path(root) for root in data_dirs]
    path = _find_ohlcv_path(roots, symbol, timeframe)
    if path is None:
        cache[cache_key] = []
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
    cache[cache_key] = rows
    return rows


def _row_qualifies_for_refinement(row: Mapping[str, Any], refine_filter: str) -> bool:
    if row.get("mechanical_setup_status") != "OK":
        return False
    outcome = row.get("mechanical_outcome")
    if refine_filter == "setup_ok":
        return True
    if refine_filter == "same_bar":
        return outcome == "SAME_BAR"
    if refine_filter == "realized_or_same_bar":
        return outcome in {"TP", "SL", "TIMEOUT", "SAME_BAR"}
    raise ValueError(f"unknown refine_filter {refine_filter!r}")


def _scaled_hold_bars(timeframe: str) -> int:
    minutes = TIMEFRAME_MINUTES[timeframe.upper()]
    return max(1, math.ceil(DEFAULT_MAX_HOLD_M15_BARS * 15 / minutes))


def _first_after(rows: Sequence[Mapping[str, Any]], cutoff: datetime) -> int:
    lo, hi = 0, len(rows)
    while lo < hi:
        mid = (lo + hi) // 2
        if rows[mid]["time"] <= cutoff:
            lo = mid + 1
        else:
            hi = mid
    return lo


def _iter_numeric_external_features(row: Mapping[str, Any]) -> Iterator[tuple[str, float]]:
    for key, value in row.items():
        if not key.startswith(EXTERNAL_PREFIXES):
            continue
        if any(token in key for token in NON_FEATURE_TOKENS):
            continue
        if key.endswith(TIMESTAMP_FIELD_SUFFIXES):
            continue
        if isinstance(value, bool) or value in (None, ""):
            continue
        if isinstance(value, (int, float)):
            yield key, float(value)


def _feature_quintiles(
    feature_values: Mapping[str, list[tuple[float, float, str, str]]],
    *,
    min_n: int = 500,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for feature, values in sorted(feature_values.items()):
        clean = [item for item in values if math.isfinite(item[0]) and math.isfinite(item[1])]
        if len(clean) < min_n:
            continue
        clean.sort(key=lambda item: item[0])
        buckets = []
        for idx in range(5):
            start = math.floor(len(clean) * idx / 5)
            end = math.floor(len(clean) * (idx + 1) / 5)
            bucket = clean[start:end]
            if not bucket:
                continue
            mean_r = sum(item[1] for item in bucket) / len(bucket)
            buckets.append(
                {
                    "feature": feature,
                    "quintile": idx + 1,
                    "n": len(bucket),
                    "min": round(bucket[0][0], 6),
                    "max": round(bucket[-1][0], 6),
                    "mean_r": round(mean_r, 4),
                }
            )
        if len(buckets) == 5:
            spread = buckets[-1]["mean_r"] - buckets[0]["mean_r"]
            for bucket in buckets:
                bucket["q5_minus_q1_mean_r"] = round(spread, 4)
            rows.extend(buckets)
    rows.sort(key=lambda row: abs(float(row.get("q5_minus_q1_mean_r") or 0.0)), reverse=True)
    return rows


def _feature_rows(available: Counter[str], missing: Counter[str]) -> list[dict[str, Any]]:
    rows = []
    for source in sorted(set(available) | set(missing)):
        a = available.get(source, 0)
        m = missing.get(source, 0)
        rows.append(
            {
                "source": source,
                "available_rows": a,
                "missing_rows": m,
                "available_rate": _rate(a, a + m),
            }
        )
    return rows


def _stats_rows(groups: Mapping[str, GroupStats], key_name: str) -> list[dict[str, Any]]:
    return [stats.as_row(key_name, key) for key, stats in sorted(groups.items())]


def _compare_builder_summaries(
    base: Mapping[str, Any] | None,
    closed: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows = []
    if not base:
        return rows
    for label, summary in (("partial_htf", base), ("closed_only", closed)):
        rows.append(
            {
                "htf_policy": label,
                "rows": summary.get("rows"),
                "would_send_ai": summary.get("would_send_ai"),
                "would_send_ai_rate": round(float(summary.get("would_send_ai_rate") or 0.0), 4),
                "pre_screen_reject": (summary.get("by_gate_status") or {}).get("PRE_SCREEN_REJECT", 0),
                "pre_ai_poi_reject": (summary.get("by_gate_status") or {}).get("PRE_AI_POI_REJECT", 0),
                "skip_first_ny": (summary.get("by_gate_status") or {}).get("SKIP_FIRST_NY_CANDLE", 0),
            }
        )
    return rows


def _markdown_refinements(refinements: Mapping[str, Any]) -> str:
    if not refinements:
        return "_No lower-timeframe refinements were requested._"
    lines = []
    for timeframe, payload in sorted(refinements.items()):
        lines.extend(
            [
                f"### {timeframe}",
                "",
                _markdown_table(
                    [
                        {
                            "timeframe": timeframe,
                            "attempted": payload.get("attempted"),
                            "local_coverage": payload.get("local_coverage"),
                            "local_coverage_rate": payload.get("local_coverage_rate"),
                            "resolved_r_n": payload.get("resolved_r_n"),
                            "mean_r_realized": payload.get("mean_r_realized"),
                        }
                    ]
                ),
                "",
                _markdown_table(
                    [
                        {"refined_outcome": outcome, "rows": count}
                        for outcome, count in sorted((payload.get("outcomes") or {}).items())
                    ]
                ),
                "",
                "M15 outcome -> refined outcome:",
                "",
                _markdown_table(payload.get("by_original_outcome") or []),
                "",
                "Symbol -> refined outcome:",
                "",
                _markdown_table(payload.get("by_symbol_outcome") or []),
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _markdown_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    preferred = (
        "symbol",
        "m15_outcome",
        "year",
        "session",
        "symbol_session",
        "symbol_year",
        "timeframe",
        "feature",
        "quintile",
        "source",
        "refined_outcome",
        "pre_ai_gate_reason",
        "rows",
        "would_send_ai",
        "would_send_ai_rate",
        "complete_rate",
        "mechanical_realized_n",
        "mechanical_mean_r_realized",
        "mechanical_win_rate_realized",
        "m15_tp",
        "m15_sl",
        "m15_timeout",
        "m15_same_bar",
        "m15_no_entry",
        "available_rows",
        "missing_rows",
        "available_rate",
        "attempted",
        "local_coverage",
        "local_coverage_rate",
        "resolved_r_n",
        "mean_r_realized",
        "n",
        "min",
        "max",
        "mean_r",
        "q5_minus_q1_mean_r",
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


def _counter_pair_rows(counter: Counter[str], columns: tuple[str, str]) -> list[dict[str, Any]]:
    rows = []
    for key, value in sorted(counter.items()):
        left, right = key.split("|", 1)
        rows.append({columns[0]: left, columns[1]: right, "rows": value})
    return rows


def _read_json(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    source = Path(path)
    if not source.exists():
        return None
    return json.loads(source.read_text(encoding="utf-8"))


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


if __name__ == "__main__":
    raise SystemExit(main())
