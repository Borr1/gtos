#!/usr/bin/env python3
"""D-11 2022-2023 backfill data-quality bias check.

Research/tooling only. This script compares the 2022-2023 mechanical
backfill against newer mechanical/live-like records and emits an audit report.
It does not promote a rule, does not alter live trading behavior, and does not
fetch external data.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

GTOS_SYMBOLS = ["XAUUSD", "XAGUSD", "USDJPY", "GBPJPY", "GBPUSD", "US30_cash", "NAS100"]
TIMEFRAMES = ["M15", "H1", "H4", "D1"]
PERIODS = ["2022-2023", "2024-2025", "2026"]

DEFAULT_OLD_TRADE_CSV = "data/historical_2022_2023/trade_cohort.csv"
DEFAULT_OLD_TRADE_JSONL = "data/historical_2022_2023/trade_cohort.jsonl"
DEFAULT_RECENT_F11_POPULATION = "research/edge_decomposition/F11_ob_zone_original_geometry/population.jsonl"
DEFAULT_TRADE_INDEX = "knowledge_base/index/_trade_index.json"
DEFAULT_OLD_REGIME_BACKFILL = "shadow_logs/structure_detector_backfill_2022_2023.jsonl"
DEFAULT_RECENT_REGIME_BACKFILL = "shadow_logs/structure_detector_backfill_2026.jsonl"
DEFAULT_LIVE_REGIME_LOG = "shadow_logs/regime_classifications.jsonl"

DEFAULT_OUTPUT_JSON = "research/ml_program/audit/D11_2022_2023_BACKFILL_BIAS_CHECK_2026-05-03.json"
DEFAULT_OUTPUT_MD = "research/ml_program/audit/D11_2022_2023_BACKFILL_BIAS_CHECK_2026-05-03.md"


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    if " " in text and "T" not in text:
        text = text.replace(" ", "T", 1)
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def period_label(dt: datetime | None) -> str:
    if dt is None:
        return "unknown"
    year = dt.year
    if year in {2022, 2023}:
        return "2022-2023"
    if year in {2024, 2025}:
        return "2024-2025"
    if year == 2026:
        return "2026"
    return "out_of_scope"


def safe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def pct(part: int | float, total: int | float) -> float | None:
    if not total:
        return None
    return float(part) / float(total)


def quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[lo]
    frac = pos - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def mean(values: Iterable[float]) -> float | None:
    vals = list(values)
    return statistics.fmean(vals) if vals else None


def median(values: Iterable[float]) -> float | None:
    vals = list(values)
    return statistics.median(vals) if vals else None


def normalize_symbol(symbol: str | None) -> str:
    text = str(symbol or "").strip()
    if text.upper() in {"US30_CASH", "US30"}:
        return "US30_cash"
    return text


def candidate_ohlc_paths(symbol: str, timeframe: str) -> list[Path]:
    names = [f"{symbol}_{timeframe}.csv"]
    if symbol == "US30_cash":
        names.append(f"US30_CASH_{timeframe}.csv")
    candidates: list[Path] = []
    for root in ["data/historical_2022_2023", "data/historical", "data/historical_2026", "data"]:
        for name in names:
            p = Path(root) / name
            if p.exists() and p not in candidates:
                candidates.append(p)
    return candidates


def read_ohlc_rows(path: Path, wanted_period: str | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = parse_dt(row.get("time"))
            if wanted_period and period_label(dt) != wanted_period:
                continue
            rows.append(
                {
                    "time": dt,
                    "open": safe_float(row.get("open")),
                    "high": safe_float(row.get("high")),
                    "low": safe_float(row.get("low")),
                    "close": safe_float(row.get("close")),
                    "volume": safe_float(row.get("volume")),
                }
            )
    return rows


def best_ohlc_source(symbol: str, timeframe: str, period: str) -> dict[str, Any]:
    best_path: Path | None = None
    best_rows: list[dict[str, Any]] = []
    candidates = candidate_ohlc_paths(symbol, timeframe)
    for path in candidates:
        rows = read_ohlc_rows(path, period)
        if len(rows) > len(best_rows):
            best_path = path
            best_rows = rows
    stats = summarize_ohlc_rows(best_rows)
    stats.update(
        {
            "symbol": symbol,
            "timeframe": timeframe,
            "period": period,
            "path": str(best_path) if best_path else None,
            "candidate_paths": [str(p) for p in candidates],
        }
    )
    return stats


def summarize_ohlc_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "rows": 0,
            "first": None,
            "last": None,
            "duplicate_timestamps": 0,
            "invalid_ohlc_rows": 0,
            "zero_range_rows": 0,
            "nonpositive_volume_rows": 0,
            "median_step_minutes": None,
            "gap_count_gt_5x_median": 0,
            "large_gap_count_gt_60h": 0,
            "p99_abs_close_return": None,
            "max_abs_close_return": None,
        }
    ordered = sorted([row for row in rows if row["time"] is not None], key=lambda r: r["time"])
    seen: set[datetime] = set()
    duplicate_timestamps = 0
    invalid_ohlc_rows = 0
    zero_range_rows = 0
    nonpositive_volume_rows = 0
    closes: list[tuple[datetime, float]] = []
    for row in ordered:
        ts = row["time"]
        if ts in seen:
            duplicate_timestamps += 1
        seen.add(ts)
        o = row["open"]
        h = row["high"]
        l = row["low"]
        c = row["close"]
        v = row["volume"]
        if None in (o, h, l, c) or h < l or h < max(o, c) or l > min(o, c):
            invalid_ohlc_rows += 1
        if h is not None and l is not None and h == l:
            zero_range_rows += 1
        if v is not None and v <= 0:
            nonpositive_volume_rows += 1
        if c is not None:
            closes.append((ts, c))
    deltas = [
        (ordered[i]["time"] - ordered[i - 1]["time"]).total_seconds()
        for i in range(1, len(ordered))
        if ordered[i].get("time") and ordered[i - 1].get("time")
    ]
    median_step_seconds = statistics.median(deltas) if deltas else None
    gap_count = 0
    large_gap_count = 0
    if median_step_seconds:
        threshold = median_step_seconds * 5.0
        gap_count = sum(1 for delta in deltas if delta > threshold)
        large_gap_count = sum(1 for delta in deltas if delta > 60 * 60 * 60)
    abs_returns: list[float] = []
    for i in range(1, len(closes)):
        prev = closes[i - 1][1]
        cur = closes[i][1]
        if prev:
            abs_returns.append(abs(cur / prev - 1.0))
    return {
        "rows": len(rows),
        "first": ordered[0]["time"].isoformat() if ordered else None,
        "last": ordered[-1]["time"].isoformat() if ordered else None,
        "duplicate_timestamps": duplicate_timestamps,
        "invalid_ohlc_rows": invalid_ohlc_rows,
        "zero_range_rows": zero_range_rows,
        "nonpositive_volume_rows": nonpositive_volume_rows,
        "median_step_minutes": (median_step_seconds / 60.0) if median_step_seconds else None,
        "gap_count_gt_5x_median": gap_count,
        "large_gap_count_gt_60h": large_gap_count,
        "p99_abs_close_return": quantile(abs_returns, 0.99),
        "max_abs_close_return": max(abs_returns) if abs_returns else None,
    }


def load_csv_trade_rows(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    rows: list[dict[str, Any]] = []
    with p.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = parse_dt(row.get("date_iso"))
            rows.append(
                {
                    "trade_id": row.get("trade_id"),
                    "symbol": normalize_symbol(row.get("symbol")),
                    "date": dt,
                    "period": period_label(dt),
                    "side": row.get("direction_long_short") or row.get("direction"),
                    "kill_zone": row.get("kill_zone") or "unknown",
                    "realized_r": safe_float(row.get("realized_r")),
                    "win_label": row.get("win_label"),
                    "source": row.get("source") or "unknown",
                    "schema": "k54_like_filled_csv",
                }
            )
    return rows


def load_mechanical_jsonl_events(path: str | Path, *, source_name: str) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    events: list[dict[str, Any]] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            payload = json.loads(line)
            bos = payload.get("bos") or {}
            ob = payload.get("ob_retest") or {}
            dt = parse_dt(bos.get("bos_time") or ob.get("exit_time"))
            events.append(
                {
                    "event_id": ob.get("bos_id") or f"{bos.get('symbol')}|{bos.get('bos_time')}",
                    "symbol": normalize_symbol(bos.get("symbol")),
                    "date": dt,
                    "period": period_label(dt),
                    "side": bos.get("direction"),
                    "outcome": ob.get("outcome"),
                    "skip_reason": ob.get("skip_reason"),
                    "realized_r": safe_float(ob.get("realized_r")),
                    "bars_in_trade": safe_float(ob.get("bars_in_trade")),
                    "entry": safe_float(ob.get("entry")),
                    "sl": safe_float(ob.get("sl")),
                    "tp": safe_float(ob.get("tp")),
                    "rr": safe_float(ob.get("rr")),
                    "source": source_name,
                    "schema": "f11_population_jsonl",
                }
            )
    return events


def generic_kill_zone(dt: datetime | None) -> str:
    if dt is None:
        return "unknown"
    hour = dt.hour + dt.minute / 60.0
    if 0 <= hour < 3:
        return "tokyo"
    if 7 <= hour < 10.5:
        return "london"
    if 13 <= hour < 17:
        return "ny"
    return "other"


def summarize_trades(rows: list[dict[str, Any]]) -> dict[str, Any]:
    r_values = [row["realized_r"] for row in rows if row.get("realized_r") is not None]
    wins = sum(1 for r in r_values if r > 0)
    losses = sum(1 for r in r_values if r <= 0)
    symbols = Counter(row.get("symbol") or "unknown" for row in rows)
    periods = Counter(row.get("period") or "unknown" for row in rows)
    sides = Counter(str(row.get("side") or "unknown").upper() for row in rows)
    sessions = Counter(row.get("kill_zone") or generic_kill_zone(row.get("date")) for row in rows)
    return {
        "rows": len(rows),
        "resolved_r_rows": len(r_values),
        "wins": wins,
        "losses_or_nonwins": losses,
        "win_rate": pct(wins, len(r_values)),
        "mean_r": mean(r_values),
        "median_r": median(r_values),
        "sum_r": sum(r_values) if r_values else None,
        "symbols": dict(sorted(symbols.items())),
        "periods": dict(sorted(periods.items())),
        "sides": dict(sorted(sides.items())),
        "sessions": dict(sorted(sessions.items())),
    }


def summarize_event_population(events: list[dict[str, Any]]) -> dict[str, Any]:
    outcomes = Counter(str(row.get("outcome") or "unknown") for row in events)
    skip_reasons = Counter(str(row.get("skip_reason") or "none") for row in events)
    filled = [row for row in events if row.get("realized_r") is not None]
    no_entry = [row for row in events if row.get("outcome") == "NO_ENTRY"]
    same_bar = [row for row in events if row.get("outcome") == "SAME_BAR" or row.get("skip_reason") == "FILL_AND_TPSL_SAME_BAR"]
    by_symbol = Counter(row.get("symbol") or "unknown" for row in events)
    filled_by_symbol = Counter(row.get("symbol") or "unknown" for row in filled)
    return {
        "events": len(events),
        "filled_resolved": len(filled),
        "no_entry": len(no_entry),
        "same_bar_or_ambiguous": len(same_bar),
        "outcomes": dict(sorted(outcomes.items())),
        "skip_reasons": dict(sorted(skip_reasons.items())),
        "by_symbol_events": dict(sorted(by_symbol.items())),
        "by_symbol_filled": dict(sorted(filled_by_symbol.items())),
        "filled_summary": summarize_trades(filled),
    }


def load_trade_index(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    payload = json.loads(p.read_text(encoding="utf-8"))
    trades = payload.get("trades") if isinstance(payload, dict) else None
    if not isinstance(trades, list):
        return []
    rows: list[dict[str, Any]] = []
    for trade in trades:
        dt = parse_dt(trade.get("date"))
        r = safe_float(trade.get("r_multiple"))
        rows.append(
            {
                "trade_id": trade.get("trade_id"),
                "symbol": normalize_symbol(trade.get("symbol")),
                "date": dt,
                "period": period_label(dt),
                "side": trade.get("direction"),
                "kill_zone": trade.get("kill_zone") or "unknown",
                "realized_r": r,
                "source": trade.get("source") or "trade_index",
                "schema": "trade_index_live_like_mixed",
            }
        )
    return rows


def summarize_regime_jsonl(path: str | Path, *, schema: str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"path": str(p), "exists": False, "rows": 0}
    by_symbol: dict[str, Counter] = defaultdict(Counter)
    score_by_symbol: dict[str, list[float]] = defaultdict(list)
    rows = 0
    first_ts: dict[str, str] = {}
    last_ts: dict[str, str] = {}
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            payload = json.loads(line)
            symbol = normalize_symbol(payload.get("symbol"))
            if symbol not in GTOS_SYMBOLS:
                continue
            rows += 1
            if schema == "structure_backfill":
                label = payload.get("v2_direction") or payload.get("production_label") or "unknown"
                score = safe_float(payload.get("v2_score"))
                ts = payload.get("ts")
            else:
                label = payload.get("regime") or "unknown"
                raw = payload.get("raw_features") or {}
                score = safe_float(raw.get("score"))
                ts = payload.get("ts")
            by_symbol[symbol][str(label)] += 1
            if score is not None:
                score_by_symbol[symbol].append(score)
            if ts:
                first_ts[symbol] = min(first_ts.get(symbol, str(ts)), str(ts))
                last_ts[symbol] = max(last_ts.get(symbol, str(ts)), str(ts))
    return {
        "path": str(p),
        "exists": True,
        "rows": rows,
        "schema": schema,
        "by_symbol_label_counts": {symbol: dict(sorted(counter.items())) for symbol, counter in sorted(by_symbol.items())},
        "score_mean_by_symbol": {symbol: mean(vals) for symbol, vals in sorted(score_by_symbol.items())},
        "coverage_symbols": sorted(by_symbol),
        "missing_gtos_symbols": [symbol for symbol in GTOS_SYMBOLS if symbol not in by_symbol],
        "first_ts_by_symbol": dict(sorted(first_ts.items())),
        "last_ts_by_symbol": dict(sorted(last_ts.items())),
    }


def build_ohlc_audit() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for symbol in GTOS_SYMBOLS:
        for timeframe in TIMEFRAMES:
            for period in PERIODS:
                rows.append(best_ohlc_source(symbol, timeframe, period))
    m15 = [row for row in rows if row["timeframe"] == "M15"]
    old_m15 = [row for row in m15 if row["period"] == "2022-2023"]
    coverage_flags = []
    for row in old_m15:
        first = parse_dt(row.get("first"))
        if row["rows"] < 1000:
            coverage_flags.append({"symbol": row["symbol"], "flag": "OLD_M15_LT_1000_ROWS", "rows": row["rows"]})
        if first and first > datetime(2022, 2, 1, tzinfo=timezone.utc):
            coverage_flags.append({"symbol": row["symbol"], "flag": "LEFT_TRUNCATED_2022_START", "first": row["first"]})
        if row["symbol"] == "NAS100" and first and first > datetime(2022, 7, 1, tzinfo=timezone.utc):
            coverage_flags.append({"symbol": row["symbol"], "flag": "NAS100_NO_H1_2022", "first": row["first"]})
        if row["invalid_ohlc_rows"]:
            coverage_flags.append({"symbol": row["symbol"], "flag": "INVALID_OHLC_ROWS", "rows": row["invalid_ohlc_rows"]})
    return {
        "rows": rows,
        "old_m15_summary": old_m15,
        "coverage_flags": coverage_flags,
    }


def label_coverage_flags(old_trade_rows: list[dict[str, Any]], ohlc_audit: dict[str, Any]) -> list[dict[str, Any]]:
    old_counts = Counter(row["symbol"] for row in old_trade_rows)
    old_m15 = {row["symbol"]: row for row in ohlc_audit["old_m15_summary"]}
    flags: list[dict[str, Any]] = []
    for symbol in GTOS_SYMBOLS:
        m15_rows = (old_m15.get(symbol) or {}).get("rows", 0)
        label_rows = old_counts.get(symbol, 0)
        if m15_rows >= 1000 and label_rows == 0:
            flags.append(
                {
                    "symbol": symbol,
                    "flag": "OHLC_PRESENT_BUT_OLD_MECHANICAL_LABELS_MISSING",
                    "m15_rows_2022_2023": m15_rows,
                }
            )
        elif label_rows and m15_rows < 1000:
            flags.append(
                {
                    "symbol": symbol,
                    "flag": "LABELS_EXIST_WITH_WEAK_OHLC_COVERAGE",
                    "m15_rows_2022_2023": m15_rows,
                    "label_rows": label_rows,
                }
            )
    return flags


def make_bias_readout(
    *,
    old_trade_rows: list[dict[str, Any]],
    old_events: list[dict[str, Any]],
    recent_events: list[dict[str, Any]],
    trade_index_rows: list[dict[str, Any]],
    ohlc_audit: dict[str, Any],
    old_regime: dict[str, Any],
    recent_regime: dict[str, Any],
) -> dict[str, Any]:
    labels = label_coverage_flags(old_trade_rows, ohlc_audit)
    old_summary = summarize_trades(old_trade_rows)
    recent_event_summary = summarize_event_population(recent_events)
    recent_summary = recent_event_summary["filled_summary"]
    old_event_summary = summarize_event_population(old_events)
    old_wr = old_summary.get("win_rate")
    recent_wr = recent_summary.get("win_rate")
    wr_delta = (old_wr - recent_wr) if old_wr is not None and recent_wr is not None else None
    old_mean = old_summary.get("mean_r")
    recent_mean = recent_summary.get("mean_r")
    mean_delta = (old_mean - recent_mean) if old_mean is not None and recent_mean is not None else None
    missing_regime_old = old_regime.get("missing_gtos_symbols") or []
    missing_regime_recent = recent_regime.get("missing_gtos_symbols") or []
    return {
        "headline_verdict": "USABLE_WITH_DOWNSAMPLING_AND_SOURCE_FLAGS_NOT_LIVE_EQUIVALENT",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "label_schema_comparability": {
            "status": "COMPARABLE_FOR_MECHANICAL_F11_STYLE_FILLED_LABELS_ONLY",
            "old_builder_claim": "data_backfill_2022_2023 says build_trade_cohort_2022_2023 reuses extract_bos_events/find_ob_retest_outcome/resolve_mechanical_outcome",
            "blocked_live_equivalence_reason": "trade_index/live-like rows are mixed-source, frozen, and not schema-equivalent to pure mechanical backfill rows",
        },
        "outcome_drift": {
            "old_2022_2023_filled_wr": old_wr,
            "recent_f11_filled_wr": recent_wr,
            "old_minus_recent_wr": wr_delta,
            "old_2022_2023_mean_r": old_mean,
            "recent_f11_mean_r": recent_mean,
            "old_minus_recent_mean_r": mean_delta,
            "interpretation": "mechanical labels are directionally similar on WR but old mean R is not a validation lift because periods and symbol mix differ",
        },
        "coverage_bias_flags": ohlc_audit["coverage_flags"],
        "label_bias_flags": labels,
        "regime_coverage_flags": {
            "old_missing_symbols": missing_regime_old,
            "recent_backfill_missing_symbols": missing_regime_recent,
            "interpretation": "regime coverage is not symmetric across periods; do not train a pooled regime model without source/period flags",
        },
        "live_like_rows": {
            "trade_index_rows": len(trade_index_rows),
            "trade_index_summary": summarize_trades(trade_index_rows),
            "status": "AUXILIARY_ONLY_NOT_A_COMPARABLE_MECHANICAL_POPULATION",
        },
        "downweight_or_exclude": [
            {
                "cohort": "2022-2023 NAS100",
                "action": "downweight_or_keep_as_single_unsplit_2022_2023_block",
                "reason": "M15 starts late in 2022 and has no H1-2022 coverage",
            },
            {
                "cohort": "2022-2023 GBPJPY and US30_cash old mechanical labels",
                "action": "exclude_from_old_label_training_until_labels_are_generated_or_located",
                "reason": "OHLC exists but data/historical_2022_2023/trade_cohort.csv has zero rows for both symbols",
            },
            {
                "cohort": "all 2022-2023 mechanical labels",
                "action": "keep_source_partition_and_period_weights",
                "reason": "pure F11-style synthetic/mechanical rows are not live AI/broker outcomes",
            },
            {
                "cohort": "pooled old-vs-recent headline WR",
                "action": "do_not_use_without_symbol_period_controls",
                "reason": "symbol mix differs materially between old backfill and F11 2026 population",
            },
        ],
        "opened_questions": [
            "Can GBPJPY and US30_cash 2022-2023 mechanical labels be regenerated with the same F11-style builder?",
            "Does the old-vs-recent mean-R difference survive symbol-balanced sampling?",
            "Can live pending-limit lifecycle telemetry separate broker-realized outcomes from internal mechanical fills?",
            "Should K-family training add explicit source_period and mechanical_vs_live_like flags before any pooled model?",
        ],
    }


def build_payload(
    *,
    old_trade_csv: str | Path = DEFAULT_OLD_TRADE_CSV,
    old_trade_jsonl: str | Path = DEFAULT_OLD_TRADE_JSONL,
    recent_f11_population: str | Path = DEFAULT_RECENT_F11_POPULATION,
    trade_index_path: str | Path = DEFAULT_TRADE_INDEX,
    old_regime_backfill: str | Path = DEFAULT_OLD_REGIME_BACKFILL,
    recent_regime_backfill: str | Path = DEFAULT_RECENT_REGIME_BACKFILL,
    live_regime_log: str | Path = DEFAULT_LIVE_REGIME_LOG,
) -> dict[str, Any]:
    old_trade_rows = load_csv_trade_rows(old_trade_csv)
    old_events = load_mechanical_jsonl_events(old_trade_jsonl, source_name="backfill_2022_2023")
    recent_events = load_mechanical_jsonl_events(recent_f11_population, source_name="f11_recent_2026")
    trade_index_rows = load_trade_index(trade_index_path)
    ohlc_audit = build_ohlc_audit()
    old_regime = summarize_regime_jsonl(old_regime_backfill, schema="structure_backfill")
    recent_regime = summarize_regime_jsonl(recent_regime_backfill, schema="structure_backfill")
    live_regime = summarize_regime_jsonl(live_regime_log, schema="live_regime_classifier")
    bias_readout = make_bias_readout(
        old_trade_rows=old_trade_rows,
        old_events=old_events,
        recent_events=recent_events,
        trade_index_rows=trade_index_rows,
        ohlc_audit=ohlc_audit,
        old_regime=old_regime,
        recent_regime=recent_regime,
    )
    return {
        "schema_version": "d11_2022_2023_backfill_bias_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "hypothesis_before_outputs": (
            "The 2022-2023 backfill is likely useful as mechanical discovery augmentation, "
            "but not live-equivalent unless coverage gaps, source mix, and label-schema limits are explicit."
        ),
        "inputs": {
            "old_trade_csv": str(old_trade_csv),
            "old_trade_jsonl": str(old_trade_jsonl),
            "recent_f11_population": str(recent_f11_population),
            "trade_index": str(trade_index_path),
            "old_regime_backfill": str(old_regime_backfill),
            "recent_regime_backfill": str(recent_regime_backfill),
            "live_regime_log": str(live_regime_log),
            "data_policy": "local_existing_files_only_no_external_fetch",
        },
        "ohlc_audit": ohlc_audit,
        "mechanical_labels": {
            "old_2022_2023_filled_csv": summarize_trades(old_trade_rows),
            "old_2022_2023_event_jsonl": summarize_event_population(old_events),
            "recent_f11_event_jsonl": summarize_event_population(recent_events),
        },
        "regime_audit": {
            "old_2022_2023_backfill": old_regime,
            "recent_2026_backfill": recent_regime,
            "live_regime_shadow_log": live_regime,
        },
        "bias_readout": bias_readout,
    }


def fmt(value: Any, digits: int = 6) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(out)


def render_markdown(payload: dict[str, Any]) -> str:
    old_m15 = payload["ohlc_audit"]["old_m15_summary"]
    old_labels = payload["mechanical_labels"]["old_2022_2023_filled_csv"]
    old_events = payload["mechanical_labels"]["old_2022_2023_event_jsonl"]
    recent_events = payload["mechanical_labels"]["recent_f11_event_jsonl"]
    recent_labels = recent_events["filled_summary"]
    bias = payload["bias_readout"]
    old_regime = payload["regime_audit"]["old_2022_2023_backfill"]
    recent_regime = payload["regime_audit"]["recent_2026_backfill"]
    live_regime = payload["regime_audit"]["live_regime_shadow_log"]

    old_m15_rows = [
        [
            row["symbol"],
            row["rows"],
            row["first"],
            row["last"],
            row["path"],
            row["invalid_ohlc_rows"],
            row["large_gap_count_gt_60h"],
        ]
        for row in old_m15
    ]
    label_rows = []
    old_by_symbol = old_labels["symbols"]
    recent_by_symbol = recent_labels["symbols"]
    old_event_by_symbol = old_events["by_symbol_events"]
    for symbol in GTOS_SYMBOLS:
        label_rows.append(
            [
                symbol,
                old_event_by_symbol.get(symbol, 0),
                old_by_symbol.get(symbol, 0),
                recent_events["by_symbol_events"].get(symbol, 0),
                recent_by_symbol.get(symbol, 0),
            ]
        )
    drift_rows = [
        ["old_2022_2023_filled_csv", old_labels["resolved_r_rows"], fmt(old_labels["win_rate"]), fmt(old_labels["mean_r"]), fmt(old_labels["median_r"]), fmt(old_labels["sum_r"])],
        ["recent_f11_2026_filled", recent_labels["resolved_r_rows"], fmt(recent_labels["win_rate"]), fmt(recent_labels["mean_r"]), fmt(recent_labels["median_r"]), fmt(recent_labels["sum_r"])],
        ["old_minus_recent", "n/a", fmt(bias["outcome_drift"]["old_minus_recent_wr"]), fmt(bias["outcome_drift"]["old_minus_recent_mean_r"]), "n/a", "n/a"],
    ]
    flags = bias["coverage_bias_flags"] + bias["label_bias_flags"]
    flag_rows = [[item.get("symbol"), item.get("flag"), item.get("rows") or item.get("first") or item.get("m15_rows_2022_2023") or ""] for item in flags]
    downweight_rows = [[item["cohort"], item["action"], item["reason"]] for item in bias["downweight_or_exclude"]]

    lines = [
        "# D-11 2022-2023 Backfill Bias Check",
        "",
        f"Generated: {payload['generated_at_utc']}",
        "Scope: research/tooling only",
        "Promotion verdict: `NO_PROMOTION_VERDICT`",
        "",
        "## Question Registered Before Output",
        "",
        payload["hypothesis_before_outputs"],
        "",
        "## Headline",
        "",
        f"- Verdict: `{bias['headline_verdict']}`.",
        "- The old backfill is useful for mechanical discovery and cohort expansion only with source/period flags.",
        "- It is not live-equivalent: the comparable recent population is F11-style mechanical, while `_trade_index.json` is mixed-source and frozen.",
        "- The biggest concrete blocker is not raw OHLC: it is old mechanical label coverage for GBPJPY and US30_cash.",
        "",
        "## Inputs",
        "",
        markdown_table(
            ["Input", "Path"],
            [[key, value] for key, value in payload["inputs"].items()],
        ),
        "",
        "## 2022-2023 M15 Coverage",
        "",
        markdown_table(["Symbol", "Rows", "First", "Last", "Source", "Invalid OHLC", "Gaps >60h"], old_m15_rows),
        "",
        "## Mechanical Label Coverage",
        "",
        markdown_table(
            ["Symbol", "Old events", "Old filled CSV", "Recent F11 events", "Recent F11 filled"],
            label_rows,
        ),
        "",
        "## Outcome Drift Check",
        "",
        markdown_table(["Population", "n", "WR", "Mean R", "Median R", "Sum R"], drift_rows),
        "",
        "Interpretation: the old filled mechanical rows are not obviously broken by headline WR, but the old-vs-recent mean-R delta is not a validation result because symbol mix and period mix differ.",
        "",
        "## Event-State Comparability",
        "",
        markdown_table(
            ["Population", "Events", "Filled", "NO_ENTRY", "Same-bar/ambiguous"],
            [
                ["old_2022_2023_jsonl", old_events["events"], old_events["filled_resolved"], old_events["no_entry"], old_events["same_bar_or_ambiguous"]],
                ["recent_f11_jsonl", recent_events["events"], recent_events["filled_resolved"], recent_events["no_entry"], recent_events["same_bar_or_ambiguous"]],
            ],
        ),
        "",
        "The filled CSV is only a training-friendly subset. Same-bar and no-entry states exist in the JSONL and must remain separate from filled realized-R labels.",
        "",
        "## Regime Coverage",
        "",
        markdown_table(
            ["Source", "Rows", "Coverage symbols", "Missing GTOS symbols"],
            [
                ["old_2022_2023_structure_backfill", old_regime["rows"], ", ".join(old_regime.get("coverage_symbols") or []), ", ".join(old_regime.get("missing_gtos_symbols") or [])],
                ["recent_2026_structure_backfill", recent_regime["rows"], ", ".join(recent_regime.get("coverage_symbols") or []), ", ".join(recent_regime.get("missing_gtos_symbols") or [])],
                ["live_regime_shadow_log", live_regime["rows"], ", ".join(live_regime.get("coverage_symbols") or []), ", ".join(live_regime.get("missing_gtos_symbols") or [])],
            ],
        ),
        "",
        "Regime labels are not symmetric across the old structure-backfill, the 2026 structure-backfill, and the live regime shadow log. Treat regime as source-specific unless a rebuilt, schema-consistent backfill is produced.",
        "",
        "## Bias Flags",
        "",
        markdown_table(["Symbol", "Flag", "Evidence"], flag_rows) if flag_rows else "No bias flags found.",
        "",
        "## Downweight Or Exclude",
        "",
        markdown_table(["Cohort", "Action", "Reason"], downweight_rows),
        "",
        "## Opened Questions",
        "",
    ]
    lines.extend([f"- {question}" for question in bias["opened_questions"]])
    lines.extend(
        [
            "",
            "## NO_PROMOTION_VERDICT",
            "",
            "This audit does not validate a trading rule, model, risk setting, prompt, or live filter. It only classifies the 2022-2023 backfill as a mechanical research input with explicit coverage and label-source constraints.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(payload: dict[str, Any], output_json: str | Path, output_md: str | Path) -> None:
    json_path = Path(output_json)
    md_path = Path(output_md)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    args = parser.parse_args()
    payload = build_payload()
    write_outputs(payload, args.output_json, args.output_md)
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
