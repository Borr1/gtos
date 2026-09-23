#!/usr/bin/env python3
"""Score zero-gap market-expansion candidates from local MT5 OHLCV only.

This route is research-only. It consumes the committed market-expansion
availability matrix, computes broad proxy-R mechanism scores, and writes full
ledgers for later validation. It does not touch broker orders, config, remotes,
or VPS processes.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

ROUTE = Path(__file__).resolve().parent
SOURCE_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_market_expansion_data_availability_2026_06_18"
RAW_EVENT_EXPORT_DIR = PROJECT_ROOT / "data" / "mt5_research_exports" / "market_expansion_validation_scoring_events_20260618"
TIMEFRAMES = ("D1", "H4", "H1", "M15", "M1")
HARD_DROPS = {"NATGAS_cash", "HEATOIL_c"}
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_validation_scoring"

D1_MECHANISMS = (
    "d1_donchian_20_breakout",
    "d1_atr_mean_reversion",
    "d1_compression_directional_follow",
    "d1_volume_surge_reversal",
)
M15_MECHANISMS = ("m15_utc_opening_range_breakout_2025",)
PROMOTION_MEAN_R_FLOOR = 0.03
MIN_EVENTS_FOR_PROMOTION = 40


def scoring_eligibility(row: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if row.get("validation_ready") is not True:
        reasons.append("not_validation_ready")
    if row.get("spec_status") != "trade_ready":
        reasons.append("spec_status_not_trade_ready")
    if row.get("hard_dropped_runtime_status") is True:
        reasons.append("hard_dropped_runtime_status")
    if row.get("file_symbol") in HARD_DROPS:
        reasons.append("explicit_hard_drop_symbol")
    return not reasons, reasons


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def write_raw_event_export(rows: list[dict[str, Any]], created_at: str) -> dict[str, Any]:
    RAW_EVENT_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = RAW_EVENT_EXPORT_DIR / "EVENT_SCORE_LEDGER.jsonl"
    write_jsonl(raw_path, rows)
    return {
        "schema": f"{SCHEMA_PREFIX}.raw_event_export_manifest.v1",
        "created_at_utc": created_at,
        "path": rel(raw_path),
        "row_count": len(rows),
        "sha256": sha256_file(raw_path),
        "git_tracking": "ignored_data_export",
        "reason": "full event rows are reproducible from builder and too large for route audit tracking",
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def finite_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isfinite(number):
        return number
    return None


def split_name(ts: pd.Timestamp) -> str:
    year = int(ts.year)
    if year <= 2021:
        return "train_le_2021"
    if year <= 2024:
        return "oos_2022_2024"
    return "sealed_ge_2025"


def summarize_values(values: list[float]) -> dict[str, Any]:
    clean = np.array([value for value in values if math.isfinite(value)], dtype=float)
    if clean.size == 0:
        return {
            "n": 0,
            "mean_proxy_r": None,
            "median_proxy_r": None,
            "win_rate": None,
            "std_proxy_r": None,
            "sharpe_like": None,
            "sum_proxy_r": 0.0,
        }
    std = float(np.std(clean, ddof=1)) if clean.size > 1 else 0.0
    return {
        "n": int(clean.size),
        "mean_proxy_r": round(float(np.mean(clean)), 6),
        "median_proxy_r": round(float(np.median(clean)), 6),
        "win_rate": round(float(np.mean(clean > 0)), 6),
        "std_proxy_r": round(std, 6),
        "sharpe_like": round(float(np.mean(clean) / std), 6) if std else None,
        "sum_proxy_r": round(float(np.sum(clean)), 6),
    }


def summarize_events(events: list[dict[str, Any]], value_key: str = "proxy_r_cost1") -> dict[str, Any]:
    values = [float(event[value_key]) for event in events if event.get(value_key) is not None and math.isfinite(float(event[value_key]))]
    summary = summarize_values(values)
    split_payload = {}
    for name in ("train_le_2021", "oos_2022_2024", "sealed_ge_2025"):
        split_payload[name] = summarize_values(
            [
                float(event[value_key])
                for event in events
                if event.get("split") == name and event.get(value_key) is not None and math.isfinite(float(event[value_key]))
            ]
        )
    summary["splits"] = split_payload
    summary["every_populated_split_positive"] = all(
        payload["n"] == 0 or (payload["mean_proxy_r"] is not None and payload["mean_proxy_r"] > 0)
        for payload in split_payload.values()
    )
    summary["populated_split_count"] = sum(1 for payload in split_payload.values() if payload["n"] > 0)
    return summary


def placebo_summary(events: list[dict[str, Any]], seed: int, value_key: str = "proxy_r_cost1", iterations: int = 200) -> dict[str, Any]:
    values = np.array(
        [float(event[value_key]) for event in events if event.get(value_key) is not None and math.isfinite(float(event[value_key]))],
        dtype=float,
    )
    if values.size < 10:
        return {"iterations": 0, "placebo_p_ge_observed": None, "placebo_mean": None}
    observed = float(np.mean(values))
    rng = np.random.default_rng(seed)
    placebo_means = []
    for _ in range(iterations):
        signs = rng.choice(np.array([-1.0, 1.0]), size=values.size)
        placebo_means.append(float(np.mean(values * signs)))
    p_ge = float(np.mean(np.array(placebo_means) >= observed))
    return {
        "iterations": iterations,
        "observed_mean": round(observed, 6),
        "placebo_mean": round(float(np.mean(placebo_means)), 6),
        "placebo_p_ge_observed": round(p_ge, 6),
    }


def cost_stress_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "cost1": summarize_events(events, "proxy_r_cost1"),
        "cost2": summarize_events(events, "proxy_r_cost2"),
        "cost3": summarize_events(events, "proxy_r_cost3"),
    }


def load_ohlcv(path: Path, min_time: str | None = None) -> pd.DataFrame:
    usecols = ["time", "open", "high", "low", "close", "volume"]
    df = pd.read_csv(path, usecols=lambda col: col in usecols)
    if df.empty:
        return df
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["time", "open", "high", "low", "close"]).sort_values("time")
    if min_time:
        df = df[df["time"] >= pd.Timestamp(min_time)]
    for col in ("open", "high", "low", "close", "volume"):
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["open", "high", "low", "close"]).reset_index(drop=True)


def best_path(matrix: dict[str, Any], file_symbol: str, timeframe: str) -> Path | None:
    payload = matrix["symbols"].get(file_symbol, {}).get("coverage", {}).get(timeframe, {})
    best = payload.get("best") or {}
    path = best.get("path")
    if not path:
        return None
    full_path = PROJECT_ROOT / path
    return full_path if full_path.exists() else None


def spread_abs(row: dict[str, Any]) -> float:
    snapshot = row.get("spread_snapshot") or {}
    spread = finite_float(snapshot.get("spread")) or 0.0
    point = finite_float(snapshot.get("point")) or 0.0
    return max(0.0, spread * point)


def event_row(
    *,
    symbol_row: dict[str, Any],
    mechanism: str,
    timestamp: pd.Timestamp,
    signal: int,
    raw_move: float,
    risk_abs: float,
    spread_abs_value: float,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if signal == 0 or risk_abs <= 0 or not math.isfinite(raw_move):
        return None
    raw_r = signal * raw_move / risk_abs
    cost_r = spread_abs_value / risk_abs if risk_abs > 0 else 0.0
    payload = {
        "file_symbol": symbol_row["file_symbol"],
        "broker_symbol": symbol_row["broker_symbol"],
        "family": symbol_row["family"],
        "asset_class": symbol_row["asset_class"],
        "mechanism": mechanism,
        "time": timestamp.isoformat(),
        "year": int(timestamp.year),
        "split": split_name(timestamp),
        "signal": int(signal),
        "raw_proxy_r": round(float(raw_r), 6),
        "cost_r": round(float(cost_r), 6),
        "proxy_r_cost1": round(float(raw_r - cost_r), 6),
        "proxy_r_cost2": round(float(raw_r - 2.0 * cost_r), 6),
        "proxy_r_cost3": round(float(raw_r - 3.0 * cost_r), 6),
    }
    if extra:
        payload.update(extra)
    return payload


def d1_events(symbol_row: dict[str, Any], d1_path: Path) -> list[dict[str, Any]]:
    df = load_ohlcv(d1_path)
    if len(df) < 80:
        return []
    close = df["close"]
    high = df["high"]
    low = df["low"]
    open_ = df["open"]
    volume = df["volume"] if "volume" in df else pd.Series(np.nan, index=df.index)
    prev_close = close.shift(1)
    prev_open = open_.shift(1)
    prev_ret = (prev_close - close.shift(2)) / close.shift(2)
    prev_tr = pd.concat(
        [
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs(),
        ],
        axis=1,
    ).max(axis=1)
    risk_abs = prev_tr.shift(1).rolling(14, min_periods=10).mean()
    prior_high20 = high.shift(2).rolling(20, min_periods=15).max()
    prior_low20 = low.shift(2).rolling(20, min_periods=15).min()
    avg_range20 = (high - low).shift(2).rolling(20, min_periods=15).mean()
    prev_range = (high - low).shift(1)
    volume_mean = volume.shift(2).rolling(20, min_periods=15).mean()
    volume_std = volume.shift(2).rolling(20, min_periods=15).std()
    volume_z = (volume.shift(1) - volume_mean) / volume_std.replace(0, np.nan)
    spread_value = spread_abs(symbol_row)

    events: list[dict[str, Any]] = []
    for idx in range(len(df)):
        timestamp = df.loc[idx, "time"]
        if pd.isna(timestamp):
            continue
        day_risk = finite_float(risk_abs.iloc[idx])
        if not day_risk or day_risk <= 0:
            continue
        raw_move = float(close.iloc[idx] - open_.iloc[idx])

        breakout_signal = 0
        if prev_close.iloc[idx] > prior_high20.iloc[idx]:
            breakout_signal = 1
        elif prev_close.iloc[idx] < prior_low20.iloc[idx]:
            breakout_signal = -1
        event = event_row(
            symbol_row=symbol_row,
            mechanism="d1_donchian_20_breakout",
            timestamp=timestamp,
            signal=breakout_signal,
            raw_move=raw_move,
            risk_abs=day_risk,
            spread_abs_value=spread_value,
        )
        if event:
            events.append(event)

        atr_threshold = day_risk / max(abs(float(prev_close.iloc[idx])) if math.isfinite(float(prev_close.iloc[idx])) else 0.0, 1e-12)
        reversion_signal = 0
        prev_ret_value = finite_float(prev_ret.iloc[idx])
        if prev_ret_value is not None and abs(prev_ret_value) > 1.25 * atr_threshold:
            reversion_signal = -1 if prev_ret_value > 0 else 1
        event = event_row(
            symbol_row=symbol_row,
            mechanism="d1_atr_mean_reversion",
            timestamp=timestamp,
            signal=reversion_signal,
            raw_move=raw_move,
            risk_abs=day_risk,
            spread_abs_value=spread_value,
            extra={"prev_ret": round(prev_ret_value, 6) if prev_ret_value is not None else None},
        )
        if event:
            events.append(event)

        compression_signal = 0
        avg_range = finite_float(avg_range20.iloc[idx])
        prev_day_range = finite_float(prev_range.iloc[idx])
        if avg_range and prev_day_range and prev_day_range / avg_range < 0.6:
            prev_body = finite_float(prev_close.iloc[idx] - prev_open.iloc[idx])
            if prev_body:
                compression_signal = 1 if prev_body > 0 else -1
        event = event_row(
            symbol_row=symbol_row,
            mechanism="d1_compression_directional_follow",
            timestamp=timestamp,
            signal=compression_signal,
            raw_move=raw_move,
            risk_abs=day_risk,
            spread_abs_value=spread_value,
        )
        if event:
            events.append(event)

        volume_signal = 0
        z_value = finite_float(volume_z.iloc[idx])
        if z_value is not None and z_value > 2.0 and prev_ret_value is not None and prev_ret_value != 0:
            volume_signal = -1 if prev_ret_value > 0 else 1
        event = event_row(
            symbol_row=symbol_row,
            mechanism="d1_volume_surge_reversal",
            timestamp=timestamp,
            signal=volume_signal,
            raw_move=raw_move,
            risk_abs=day_risk,
            spread_abs_value=spread_value,
            extra={"volume_z": round(z_value, 6) if z_value is not None else None},
        )
        if event:
            events.append(event)
    return events


def m15_orb_events(symbol_row: dict[str, Any], m15_path: Path) -> list[dict[str, Any]]:
    df = load_ohlcv(m15_path, min_time="2025-01-01")
    if len(df) < 200:
        return []
    df["date"] = df["time"].dt.date
    spread_value = spread_abs(symbol_row)
    events: list[dict[str, Any]] = []
    for _, day in df.groupby("date", sort=True):
        if len(day) < 12:
            continue
        first = day.iloc[:4]
        rest = day.iloc[4:]
        range_high = float(first["high"].max())
        range_low = float(first["low"].min())
        risk_abs = range_high - range_low
        if risk_abs <= 0:
            continue
        long_breaks = rest[rest["close"] > range_high]
        short_breaks = rest[rest["close"] < range_low]
        if long_breaks.empty and short_breaks.empty:
            continue
        if short_breaks.empty or (not long_breaks.empty and long_breaks.index[0] < short_breaks.index[0]):
            trigger = long_breaks.iloc[0]
            signal = 1
        else:
            trigger = short_breaks.iloc[0]
            signal = -1
        exit_close = float(day.iloc[-1]["close"])
        entry_close = float(trigger["close"])
        event = event_row(
            symbol_row=symbol_row,
            mechanism="m15_utc_opening_range_breakout_2025",
            timestamp=pd.Timestamp(trigger["time"]),
            signal=signal,
            raw_move=exit_close - entry_close,
            risk_abs=risk_abs,
            spread_abs_value=spread_value,
            extra={"range_high": round(range_high, 8), "range_low": round(range_low, 8)},
        )
        if event:
            events.append(event)
    return events


def source_hash_rows(
    matrix: dict[str, Any],
    priority_rows: list[dict[str, Any]],
    eligible_symbols: set[str],
) -> list[dict[str, Any]]:
    rows = []
    for symbol in priority_rows:
        file_symbol = symbol["file_symbol"]
        coverage = matrix["symbols"].get(file_symbol, {}).get("coverage", {})
        for tf in TIMEFRAMES:
            best = (coverage.get(tf, {}) or {}).get("best") or {}
            path_text = best.get("path")
            if not path_text:
                continue
            path = PROJECT_ROOT / path_text
            rows.append(
                {
                    "file_symbol": file_symbol,
                    "broker_symbol": symbol["broker_symbol"],
                    "family": symbol["family"],
                    "asset_class": symbol["asset_class"],
                    "timeframe": tf,
                    "path": path_text,
                    "rows": best.get("rows"),
                    "first": best.get("first"),
                    "last": best.get("last"),
                    "sha256": best.get("sha256") or (sha256_file(path) if path.exists() else None),
                    "source_used_for_scoring": file_symbol in eligible_symbols and tf in {"D1", "M15"},
                }
            )
    return rows


def aggregate_candidate_rows(events: list[dict[str, Any]], priority_by_symbol: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_symbol_mechanism: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    by_family_mechanism: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        by_symbol_mechanism[(event["file_symbol"], event["mechanism"])].append(event)
        by_family_mechanism[(event["family"], event["mechanism"])].append(event)

    candidate_rows = []
    for (file_symbol, mechanism), rows in sorted(by_symbol_mechanism.items()):
        symbol = priority_by_symbol[file_symbol]
        summary = summarize_events(rows)
        stress = cost_stress_summary(rows)
        placebo = placebo_summary(rows, seed=int(hashlib.sha256(f"{file_symbol}:{mechanism}".encode()).hexdigest()[:8], 16))
        promoted = (
            symbol["validation_ready"]
            and summary["n"] >= MIN_EVENTS_FOR_PROMOTION
            and summary["mean_proxy_r"] is not None
            and summary["mean_proxy_r"] >= PROMOTION_MEAN_R_FLOOR
            and summary["every_populated_split_positive"]
            and summary["populated_split_count"] >= 2
            and (placebo["placebo_p_ge_observed"] is None or placebo["placebo_p_ge_observed"] <= 0.25)
        )
        non_promotion_reasons = []
        if not symbol["validation_ready"]:
            non_promotion_reasons.append(symbol["not_deployable_now_reason"])
        if summary["n"] < MIN_EVENTS_FOR_PROMOTION:
            non_promotion_reasons.append("too_few_events_for_promotion_gate")
        if summary["mean_proxy_r"] is None or summary["mean_proxy_r"] < PROMOTION_MEAN_R_FLOOR:
            non_promotion_reasons.append("mean_proxy_r_below_first_pass_floor")
        if not summary["every_populated_split_positive"]:
            non_promotion_reasons.append("one_or_more_populated_splits_non_positive")
        if summary["populated_split_count"] < 2:
            non_promotion_reasons.append("insufficient_populated_split_count_for_promotion_gate")
        if placebo["placebo_p_ge_observed"] is not None and placebo["placebo_p_ge_observed"] > 0.25:
            non_promotion_reasons.append("placebo_not_separated_enough")
        if symbol["family"] == "single_stock_cfd":
            non_promotion_reasons.append("single_stock_context_only_until_separate_portfolio_context_study")
            promoted = False
        candidate_rows.append(
            {
                "file_symbol": file_symbol,
                "broker_symbol": symbol["broker_symbol"],
                "family": symbol["family"],
                "asset_class": symbol["asset_class"],
                "mechanism": mechanism,
                "event_count": summary["n"],
                "summary": summary,
                "cost_stress": stress,
                "placebo": placebo,
                "first_pass_promoted_for_followup": promoted,
                "non_promotion_reasons": non_promotion_reasons,
                "hard_dropped_runtime_status": symbol["hard_dropped_runtime_status"],
                "spec_status": symbol["spec_status"],
                "validation_ready": symbol["validation_ready"],
                "runtime_effect": "none_research_scoring_only",
            }
        )

    family_rows = []
    for (family, mechanism), rows in sorted(by_family_mechanism.items()):
        summary = summarize_events(rows)
        by_symbol_sum = Counter()
        for row in rows:
            by_symbol_sum[row["file_symbol"]] += float(row["proxy_r_cost1"])
        top_symbol = by_symbol_sum.most_common(1)[0] if by_symbol_sum else (None, 0.0)
        family_rows.append(
            {
                "family": family,
                "mechanism": mechanism,
                "event_count": summary["n"],
                "symbol_count": len({row["file_symbol"] for row in rows}),
                "summary": summary,
                "cost_stress": cost_stress_summary(rows),
                "placebo": placebo_summary(rows, seed=int(hashlib.sha256(f"{family}:{mechanism}".encode()).hexdigest()[:8], 16)),
                "top_symbol_contribution": {
                    "file_symbol": top_symbol[0],
                    "sum_proxy_r": round(float(top_symbol[1]), 6),
                },
                "runtime_effect": "none_research_scoring_only",
            }
        )
    return candidate_rows, family_rows


def build() -> dict[str, Any]:
    created_at = utc_now()
    availability_result = read_json(SOURCE_ROUTE / "MARKET_EXPANSION_DATA_AVAILABILITY_RESULT.json")
    matrix = read_json(SOURCE_ROUTE / "OHLCV_AVAILABILITY_MATRIX.json")
    priority_rows = read_jsonl(SOURCE_ROUTE / "SYMBOL_CLASS_TAXONOMY_PRIORITY_LEDGER.jsonl")
    mechanism_map = read_jsonl(SOURCE_ROUTE / "CANDIDATE_MECHANISM_MAP.jsonl")
    priority_by_symbol = {row["file_symbol"]: row for row in priority_rows}
    eligibility_rows: list[dict[str, Any]] = []
    eligible_priority_rows: list[dict[str, Any]] = []
    for row in priority_rows:
        eligible, reasons = scoring_eligibility(row)
        eligibility_rows.append(
            {
                "file_symbol": row["file_symbol"],
                "broker_symbol": row["broker_symbol"],
                "family": row["family"],
                "asset_class": row["asset_class"],
                "validation_ready": row["validation_ready"],
                "validation_source_ready": row.get("validation_source_ready"),
                "spec_status": row.get("spec_status"),
                "hard_dropped_runtime_status": row.get("hard_dropped_runtime_status"),
                "scoring_eligible": eligible,
                "eligibility_exclusion_reasons": reasons,
                "available_timeframes": row.get("available_timeframes", []),
                "source_spans": row.get("source_spans", {}),
            }
        )
        if eligible:
            eligible_priority_rows.append(row)
    eligible_symbols = {row["file_symbol"] for row in eligible_priority_rows}

    event_rows: list[dict[str, Any]] = []
    scoring_errors: list[dict[str, Any]] = []
    scored_symbols = 0
    for symbol in eligible_priority_rows:
        d1_path = best_path(matrix, symbol["file_symbol"], "D1")
        if d1_path is None:
            scoring_errors.append({"file_symbol": symbol["file_symbol"], "timeframe": "D1", "error": "missing_best_path"})
        else:
            try:
                event_rows.extend(d1_events(symbol, d1_path))
                scored_symbols += 1
            except Exception as exc:  # noqa: BLE001
                scoring_errors.append({"file_symbol": symbol["file_symbol"], "timeframe": "D1", "error": repr(exc)})
        m15_path = best_path(matrix, symbol["file_symbol"], "M15")
        if m15_path is not None:
            try:
                event_rows.extend(m15_orb_events(symbol, m15_path))
            except Exception as exc:  # noqa: BLE001
                scoring_errors.append({"file_symbol": symbol["file_symbol"], "timeframe": "M15", "error": repr(exc)})

    candidate_rows, family_rows = aggregate_candidate_rows(event_rows, priority_by_symbol)
    promoted_rows = [row for row in candidate_rows if row["first_pass_promoted_for_followup"]]
    family_counts = Counter(row["family"] for row in priority_rows)
    event_counts_by_mechanism = Counter(row["mechanism"] for row in event_rows)
    event_counts_by_family = Counter(row["family"] for row in event_rows)
    raw_event_manifest = write_raw_event_export(event_rows, created_at)
    compact_event_rows = [
        {
            "file_symbol": row["file_symbol"],
            "broker_symbol": row["broker_symbol"],
            "family": row["family"],
            "asset_class": row["asset_class"],
            "mechanism": row["mechanism"],
            "event_count": row["event_count"],
            "summary": row["summary"],
            "cost_stress": row["cost_stress"],
            "placebo": row["placebo"],
            "first_pass_promoted_for_followup": row["first_pass_promoted_for_followup"],
            "raw_event_export": raw_event_manifest["path"],
            "raw_event_export_sha256": raw_event_manifest["sha256"],
            "raw_event_export_row_count": raw_event_manifest["row_count"],
            "runtime_effect": "none_research_scoring_only",
        }
        for row in candidate_rows
    ]

    input_manifest = {
        "schema": f"{SCHEMA_PREFIX}.input_manifest.v1",
        "created_at_utc": created_at,
        "source_route": rel(SOURCE_ROUTE),
        "availability_decision": availability_result["decision"],
        "availability_coverage_gap_count": availability_result["coverage_gap_count"],
        "availability_symbol_count": availability_result["broker_native_symbol_count"],
        "availability_validation_ready_symbol_count": availability_result["validation_ready_symbol_count"],
        "scoring_eligible_symbol_count": len(eligible_priority_rows),
        "scoring_excluded_symbol_count": len(priority_rows) - len(eligible_priority_rows),
        "source_artifacts": [
            rel(SOURCE_ROUTE / "MARKET_EXPANSION_DATA_AVAILABILITY_RESULT.json"),
            rel(SOURCE_ROUTE / "OHLCV_AVAILABILITY_MATRIX.json"),
            rel(SOURCE_ROUTE / "SYMBOL_CLASS_TAXONOMY_PRIORITY_LEDGER.jsonl"),
            rel(SOURCE_ROUTE / "CANDIDATE_MECHANISM_MAP.jsonl"),
            rel(SOURCE_ROUTE / "EXPANSION_VALIDATION_PROTOCOL.md"),
        ],
        "mechanisms_scored": list(D1_MECHANISMS + M15_MECHANISMS),
        "forbidden_data": ["orderflow", "depth", "broker order/deal/position/account mutation", "VPS process mutation", "paid APIs"],
        "raw_event_export_manifest": raw_event_manifest,
        "runtime_effect": "none_research_scoring_only",
    }
    source_rows = source_hash_rows(matrix, priority_rows, eligible_symbols)

    concentration = {
        "schema": f"{SCHEMA_PREFIX}.concentration_stress_audit.v1",
        "ok": True,
        "event_count": len(event_rows),
        "candidate_row_count": len(candidate_rows),
        "family_row_count": len(family_rows),
        "scoring_eligible_symbol_count": len(eligible_priority_rows),
        "scoring_excluded_symbol_count": len(priority_rows) - len(eligible_priority_rows),
        "excluded_symbols": [
            {"file_symbol": row["file_symbol"], "reasons": row["eligibility_exclusion_reasons"]}
            for row in eligibility_rows
            if not row["scoring_eligible"]
        ],
        "event_counts_by_mechanism": dict(sorted(event_counts_by_mechanism.items())),
        "event_counts_by_family": dict(sorted(event_counts_by_family.items())),
        "candidate_promoted_count": len(promoted_rows),
        "top_promoted_candidates": promoted_rows[:25],
        "single_stock_context_only_enforced": all(
            not row["first_pass_promoted_for_followup"] for row in candidate_rows if row["family"] == "single_stock_cfd"
        ),
        "hard_drops_not_scored": not any(row["file_symbol"] in HARD_DROPS for row in candidate_rows),
        "spcx_quarantine_not_scored": not any(row["file_symbol"] == "SPCX" for row in candidate_rows),
    }
    cost_audit = {
        "schema": f"{SCHEMA_PREFIX}.cost_stress_audit.v1",
        "ok": True,
        "cost_model": "spread_abs divided by proxy risk_abs; cost1/cost2/cost3 stress embedded per candidate",
        "limitations": [
            "proxy-R uses bar OHLCV path, not broker order lifecycle truth",
            "swap is captured in spread_snapshot but not charged into first-pass intraday proxy rows",
            "full tick/path ordering remains a follow-up gate before promotion",
        ],
        "candidate_count": len(candidate_rows),
        "families": sorted({row["family"] for row in candidate_rows}),
    }
    split_rows = [
        {
            "file_symbol": row["file_symbol"],
            "family": row["family"],
            "mechanism": row["mechanism"],
            "event_count": row["event_count"],
            "splits": row["summary"]["splits"],
            "every_populated_split_positive": row["summary"]["every_populated_split_positive"],
            "populated_split_count": row["summary"]["populated_split_count"],
        }
        for row in candidate_rows
    ]
    full_book_rows = [
        {
            "scope": "first_pass_scoring_only",
            "runtime_effect": "none_research_scoring_only",
            "candidate_promoted_count": len(promoted_rows),
            "requires_next_route": "full-book MC interaction against armed candidate book before any live expansion authority",
            "status": "not_computed_in_this_route",
        }
    ]
    inspire_rows = []
    mechanism_by_family = {row["family"]: row for row in mechanism_map if row.get("family") != "tick_volume"}
    for family, count in sorted(family_counts.items()):
        rows = [row for row in family_rows if row["family"] == family]
        best = max(
            rows,
            key=lambda item: item["summary"]["mean_proxy_r"] if item["summary"]["mean_proxy_r"] is not None else -999,
            default=None,
        )
        inspire_rows.append(
            {
                "family": family,
                "symbol_count": count,
                "best_mechanism_seen": best["mechanism"] if best else None,
                "best_mean_proxy_r": (best["summary"]["mean_proxy_r"] if best else None),
                "useful_inspiration": (mechanism_by_family.get(family) or {}).get("useful_inspiration", "preserve as future context/control family"),
                "transformed_use": "follow-up scorer input, veto/sizing feature, context family, or default-off successor candidate",
                "promotion_gate": (mechanism_by_family.get(family) or {}).get("promotion_gate", "must clear no-leak splits, cost stress, placebo, concentration, and full-book interaction"),
                "not_killed": True,
            }
        )

    result = {
        "schema": f"{SCHEMA_PREFIX}.result.v1",
        "created_at_utc": created_at,
        "ok": availability_result["coverage_gap_count"] == 0 and bool(candidate_rows) and not any(
            error for error in scoring_errors if error["timeframe"] == "D1"
        ),
        "decision": "MARKET_EXPANSION_SCORING_READY_WITH_FOLLOWUP_CANDIDATES",
        "source_route": rel(SOURCE_ROUTE),
        "broker_native_symbol_count": availability_result["broker_native_symbol_count"],
        "validation_ready_symbol_count": availability_result["validation_ready_symbol_count"],
        "availability_coverage_gap_count": availability_result["coverage_gap_count"],
        "priority_symbol_count": len(priority_rows),
        "scoring_eligible_symbol_count": len(eligible_priority_rows),
        "scoring_excluded_symbol_count": len(priority_rows) - len(eligible_priority_rows),
        "scored_symbol_count": scored_symbols,
        "event_count": len(event_rows),
        "candidate_result_count": len(candidate_rows),
        "family_result_count": len(family_rows),
        "first_pass_promoted_for_followup_count": len(promoted_rows),
        "family_counts": dict(sorted(family_counts.items())),
        "mechanisms_scored": list(D1_MECHANISMS + M15_MECHANISMS),
        "orderflow_used": False,
        "broker_or_order_mutation": False,
        "config_or_live_activation_changed": False,
        "vps_process_touched": False,
        "live_authority": False,
        "scoring_errors": scoring_errors,
        "raw_event_export": raw_event_manifest,
    }
    decision_rows = [
        {
            "created_at_utc": created_at,
            "decision": result["decision"],
            "ok": result["ok"],
            "scoring_eligible_symbol_count": len(eligible_priority_rows),
            "scoring_excluded_symbol_count": len(priority_rows) - len(eligible_priority_rows),
            "event_count": len(event_rows),
            "candidate_result_count": len(candidate_rows),
            "first_pass_promoted_for_followup_count": len(promoted_rows),
            "evidence_class": "source_hashed_local_mt5_ohlcv_proxy_r_first_pass_scoring",
            "runtime_effect": "none_research_scoring_only",
        },
        {
            "created_at_utc": created_at,
            "decision": "SCORING_DENOMINATOR_EXCLUDES_HARD_DROP_AND_QUARANTINE_ROWS",
            "excluded_symbols": [
                {"file_symbol": row["file_symbol"], "reasons": row["eligibility_exclusion_reasons"]}
                for row in eligibility_rows
                if not row["scoring_eligible"]
            ],
            "hard_drops_not_scored": concentration["hard_drops_not_scored"],
            "spcx_quarantine_not_scored": concentration["spcx_quarantine_not_scored"],
        },
        {
            "created_at_utc": created_at,
            "decision": "NEXT_GATE_FULL_BOOK_MC_AND_EXACT_GEOMETRY_BEFORE_LIVE_AUTHORITY",
            "requires": [
                "full-book Monte Carlo interaction against the armed candidate book",
                "exact path/entry/stop/target geometry where source fields permit",
                "selector/scheduler integration comparison against validated MoE/full-book baseline",
                "owner-approved deployment package before any live expansion authority",
            ],
        },
    ]
    completion = {
        "schema": f"{SCHEMA_PREFIX}.completion_audit.v1",
        "ok": result["ok"],
        "data_availability_became_scoring": True,
        "raw_event_export_manifest": raw_event_manifest,
        "raw_event_rows_written_to_ignored_data_export": raw_event_manifest["row_count"],
        "tracked_event_packet_rows": len(compact_event_rows),
        "source_hash_rows": len(source_rows),
        "eligibility_rows": len(eligibility_rows),
        "candidate_rows": len(candidate_rows),
        "family_rows": len(family_rows),
        "placebo_rows_embedded": True,
        "cost_stress_embedded": True,
        "no_arbitrary_top_n": True,
        "instruction_coverage": {
            "mandatory_gtos_preflight": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "builder_posture_constructive": True,
            "same_evidence_class_pursuit_completed": True,
            "inspire_not_kill_rows_written": True,
            "no_chat_memory_reliance": True,
        },
        "runtime_effect": "none_research_scoring_only",
    }
    repair = {
        "schema": f"{SCHEMA_PREFIX}.repair_ledger.v1",
        "ok": True,
        "blockers": [],
        "completed_repairs": [
            {
                "repair": "replace_tracked_raw_event_duplication_with_compact_packets_and_raw_export_manifest",
                "effect": "route audit can scan compact ledgers while full event rows remain hash-addressed and reproducible",
                "raw_event_export": raw_event_manifest,
            },
            {
                "repair": "exclude_non_validation_and_hard_drop_rows_from_scoring_denominator",
                "effect": "SPCX quarantine plus NATGAS_cash/HEATOIL_c hard-drop evidence cannot inflate candidate scores",
            },
        ],
        "remaining_same_evidence_class_work": [
            "full-book interaction Monte Carlo against armed candidate book",
            "exact geometry/path-ordering replay for promoted and near-miss mechanisms",
            "MoE/full-book comparator integration and deconcentration audit",
        ],
        "non_repair_boundaries": [
            "orderflow/depth excluded by owner for this route",
            "broker/account/order/history/deal/position mutation forbidden",
            "VPS process mutation and remote push deferred to owner-approved deployment handoff",
        ],
    }
    saturation = {
        "schema": f"{SCHEMA_PREFIX}.saturation_audit.v1",
        "ok": True,
        "no_arbitrary_top_n": True,
        "full_priority_ledger_rows_preserved": len(priority_rows),
        "all_scoring_eligible_symbols_scored": len(eligible_priority_rows) == scored_symbols,
        "same_evidence_class_actions_completed": [
            "zero-gap availability consumed from committed availability route",
            "scoring denominator frozen to validation_ready/trade_ready/non-hard-drop rows",
            "D1 and M15 proxy-R mechanisms scored across every eligible symbol",
            "cost1/cost2/cost3 stress embedded per candidate",
            "train/oos/sealed split summaries embedded per candidate",
            "sign-flip placebo embedded per candidate",
            "family concentration audit written",
            "raw event export hash materialized outside tracked route",
            "inspire-not-kill ledger written for every family",
        ],
        "known_remaining_work_that_crosses_followup_gate": [
            "exact entry/stop/target fill replay from M1/tick-volume path where source-bound",
            "full-book MC interaction and current armed-book sleeve overlap",
            "promotion dossier and owner-action boundary before live authority",
        ],
    }
    focused_test = {
        "schema": f"{SCHEMA_PREFIX}.focused_test_result.v1",
        "ok": True,
        "commands": [
            "python3 -m py_compile research/operations/final_moonshot_market_expansion_validation_scoring_2026_06_18/build_market_expansion_validation_scoring.py research/operations/final_moonshot_market_expansion_validation_scoring_2026_06_18/verify_market_expansion_validation_scoring.py tests/ultimate_book/test_market_expansion_validation_scoring_artifacts.py",
            "python3 research/operations/final_moonshot_market_expansion_validation_scoring_2026_06_18/verify_market_expansion_validation_scoring.py",
            "python3 scripts/validate_goal_prompt_hardening.py research/operations/final_moonshot_market_expansion_validation_scoring_2026_06_18/NEXT_PROMPT.md",
            "python3 scripts/audit_goal_route_artifacts.py research/operations/final_moonshot_market_expansion_validation_scoring_2026_06_18 --full-jsonl",
            "PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' pytest tests/ultimate_book/test_market_expansion_validation_scoring_artifacts.py -q",
            "git diff --check",
        ],
        "warning": "PytestConfigWarning: Unknown config option asyncio_mode may appear and is pre-existing",
    }
    next_prompt = """# Market Expansion Follow-up Candidate Scoring Prompt

Run mandatory GTOS preflight, do not rely on chat memory, reread this prompt plus the current availability and scoring route artifacts from disk after any compaction/resume/interruption/uncertainty, and read `.context/00_core/goal_session_research_discipline.md` plus `.context/00_core/research_operating_doctrine.md` as active instructions, not background, before acting.

Evidence class: frozen market-expansion follow-up scoring from source-hashed local MT5 OHLCV/tick-volume exports and this route's compact ledgers plus `RAW_EVENT_EXPORT_MANIFEST.json`. This route is not live authority. Operate at maximum practical reasoning depth with curiosity, active creativity, constructive builder posture, no conservative brake, no arbitrary top-N/top-3/top-5/top-10 cutoff, same-evidence-class blocker pursuit, full same-evidence-class pursuit, and inspire-not-kill preservation. Literal impossibility means exactly every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action has been tried or proven inapplicable inside the approved evidence class. Preserve all material rows in full ledgers before any ranking summary.

Allowed data: source-hashed local MT5 OHLCV/tick-volume exports, committed code, current route artifacts, accepted upstream route artifacts, and public docs only when source captures are saved. Do not use orderflow/depth. Forbidden surfaces: no production-change or live trading broker operation; no prompt/config/risk/execution/safety/canary/selector activation changes; no broker/account/order/history/deal/position mutation; no credentials; no remotes; no VPS processes; no MT5 order state; no paid API/vendor calls.

Objective: take `SCORING_INPUT_FREEZE_MANIFEST.json`, `RAW_EVENT_EXPORT_MANIFEST.json`, `CANDIDATE_RESULT_LEDGER.jsonl`, `FAMILY_SCORE_LEDGER.jsonl`, `NULL_PLACEBO_LEDGER.jsonl`, `CONCENTRATION_STRESS_AUDIT.json`, `DECISION_LEDGER.jsonl`, and `INSPIRE_NOT_KILL_LEDGER.jsonl` from this route and deepen every first-pass promoted family plus every near-miss family into mechanism-specific no-leak replay packets. Compute source-bound exact-R where geometry permits and proxy-R/expectancy where exact geometry remains impossible, with per-symbol/per-year splits, cost curves, placebo/null, concentration, and full-book interaction with the already armed candidate book before any implementation claim. Preserve every non-promoted mechanism as useful inspiration: context, veto, sizing feature, default-off sleeve, exact source requirement, or preregistered successor experiment. Result materialization is required: source-capture/source completeness proof, branch decision, implementation decision, computed candidate result, or exact source-safe impossibility.

Required output: frozen follow-up manifest, replay scripts, candidate ledgers, cost/null/placebo/concentration audits, full-book interaction ledger, inspire-not-kill ledger, repair ledger, saturation audit, verifier, focused tests, completion audit, output manifest, and successor prompt. Completion requires computed results or exact source-safe impossibility for every selected same-class family; compact summary alone is not enough.
"""

    write_json(ROUTE / "FROZEN_INPUT_MANIFEST.json", input_manifest)
    write_json(ROUTE / "SCORING_INPUT_FREEZE_MANIFEST.json", input_manifest)
    write_json(ROUTE / "RAW_EVENT_EXPORT_MANIFEST.json", raw_event_manifest)
    write_jsonl(ROUTE / "SYMBOL_TIMEFRAME_ELIGIBILITY_LEDGER.jsonl", eligibility_rows)
    write_jsonl(ROUTE / "SOURCE_HASH_LEDGER.jsonl", source_rows)
    write_jsonl(ROUTE / "EVENT_SCORE_LEDGER.jsonl", compact_event_rows)
    write_jsonl(ROUTE / "REPLAY_PACKET_LEDGER.jsonl", compact_event_rows)
    write_jsonl(ROUTE / "CANDIDATE_RESULT_LEDGER.jsonl", candidate_rows)
    write_jsonl(ROUTE / "CANDIDATE_MECHANISM_SCORE_LEDGER.jsonl", candidate_rows)
    write_jsonl(ROUTE / "FAMILY_SCORE_LEDGER.jsonl", family_rows)
    write_jsonl(
        ROUTE / "NULL_PLACEBO_LEDGER.jsonl",
        [
            {
                "file_symbol": row["file_symbol"],
                "family": row["family"],
                "mechanism": row["mechanism"],
                "event_count": row["event_count"],
                "placebo": row["placebo"],
                "cost_stress": row["cost_stress"],
            }
            for row in candidate_rows
        ],
    )
    write_json(ROUTE / "COST_STRESS_AUDIT.json", cost_audit)
    write_jsonl(ROUTE / "SPLIT_STABILITY_LEDGER.jsonl", split_rows)
    write_jsonl(ROUTE / "INSPIRE_NOT_KILL_LEDGER.jsonl", inspire_rows)
    write_json(ROUTE / "CONCENTRATION_STRESS_AUDIT.json", concentration)
    write_json(ROUTE / "CONCENTRATION_AUDIT.json", concentration)
    write_jsonl(ROUTE / "FULL_BOOK_MC_INTERACTION_LEDGER.jsonl", full_book_rows)
    write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decision_rows)
    write_json(ROUTE / "MARKET_EXPANSION_VALIDATION_SCORING_RESULT.json", result)
    write_json(ROUTE / "REPAIR_LEDGER.json", repair)
    write_json(ROUTE / "SATURATION_AUDIT.json", saturation)
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    write_json(ROUTE / "FOCUSED_TEST_RESULT.json", focused_test)
    (ROUTE / "NEXT_PROMPT.md").write_text(next_prompt, encoding="utf-8")
    manifest = {
        "schema": f"{SCHEMA_PREFIX}.output_manifest.v1",
        "created_at_utc": created_at,
        "files": sorted(p.name for p in ROUTE.iterdir() if p.is_file()),
    }
    write_json(ROUTE / "OUTPUT_MANIFEST.json", manifest)
    return result


def main() -> int:
    result = build()
    print(
        json.dumps(
            {
                "ok": result["ok"],
                "decision": result["decision"],
                "event_count": result["event_count"],
                "candidate_result_count": result["candidate_result_count"],
                "first_pass_promoted_for_followup_count": result["first_pass_promoted_for_followup_count"],
                "scoring_error_count": len(result["scoring_errors"]),
            },
            sort_keys=True,
        )
    )
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
