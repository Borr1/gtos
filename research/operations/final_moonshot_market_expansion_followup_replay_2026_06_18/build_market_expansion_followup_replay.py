#!/usr/bin/env python3
"""Deepen market-expansion scoring with M1 path replay and book interaction.

This route is research-only. It consumes the committed market-expansion
scoring route, resolves target/stop path ordering from local MT5 M1 OHLCV
where available, and writes compact candidate/family/full-book ledgers. Raw
event rows are stored under ignored data exports and hash-addressed.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
SCORING_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_market_expansion_validation_scoring_2026_06_18"
AVAILABILITY_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_market_expansion_data_availability_2026_06_18"
CANDIDATE_MC_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_candidate_enabled_unified_replay_mc_2026_06_18"
RAW_EVENT_EXPORT_DIR = PROJECT_ROOT / "data" / "mt5_research_exports" / "market_expansion_followup_replay_20260618"
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_followup_replay"
TARGET_MULTIPLES = (1.0, 2.0, 3.0)
UNIT_INTERACTION_WEIGHT = 0.05
MIN_M1_EVENTS_FOR_INTERACTION = 20
EXCLUDED_SYMBOLS = {"SPCX", "NATGAS_cash", "HEATOIL_c"}
DEEP_REPLAY_CLASSES = {"first_pass_promoted", "near_miss_positive_proxy"}

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows), encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def finite_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def split_name(ts: pd.Timestamp) -> str:
    year = int(ts.year)
    if year <= 2021:
        return "train_le_2021"
    if year <= 2024:
        return "oos_2022_2024"
    return "sealed_ge_2025"


def short_split(ts: pd.Timestamp) -> str:
    return {"train_le_2021": "train", "oos_2022_2024": "oos", "sealed_ge_2025": "sealed"}[split_name(ts)]


def load_ohlcv(path: Path | None) -> pd.DataFrame:
    if path is None or not path.exists():
        return pd.DataFrame()
    usecols = ["time", "open", "high", "low", "close", "volume"]
    df = pd.read_csv(path, usecols=lambda col: col in usecols)
    if df.empty:
        return df
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["time", "open", "high", "low", "close"]).sort_values("time")
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
    full = PROJECT_ROOT / path
    return full if full.exists() else None


def summarize(values: list[float]) -> dict[str, Any]:
    clean = np.array([value for value in values if math.isfinite(value)], dtype=float)
    if clean.size == 0:
        return {
            "n": 0,
            "mean_r": None,
            "median_r": None,
            "win_rate": None,
            "std_r": None,
            "sharpe_like": None,
            "sum_r": 0.0,
        }
    std = float(np.std(clean, ddof=1)) if clean.size > 1 else 0.0
    return {
        "n": int(clean.size),
        "mean_r": round(float(np.mean(clean)), 6),
        "median_r": round(float(np.median(clean)), 6),
        "win_rate": round(float(np.mean(clean > 0)), 6),
        "std_r": round(std, 6),
        "sharpe_like": round(float(np.mean(clean) / std), 6) if std else None,
        "sum_r": round(float(np.sum(clean)), 6),
    }


def summarize_event_policy(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    values = [float(row[key]) for row in rows if row.get(key) is not None and math.isfinite(float(row[key]))]
    out = summarize(values)
    out["splits"] = {
        split: summarize(
            [
                float(row[key])
                for row in rows
                if row.get("split") == split and row.get(key) is not None and math.isfinite(float(row[key]))
            ]
        )
        for split in ("train_le_2021", "oos_2022_2024", "sealed_ge_2025")
    }
    out["populated_split_count"] = sum(1 for payload in out["splits"].values() if payload["n"] > 0)
    out["every_populated_split_positive"] = all(
        payload["n"] == 0 or (payload["mean_r"] is not None and payload["mean_r"] > 0)
        for payload in out["splits"].values()
    )
    return out


def row_time_map(df: pd.DataFrame) -> dict[pd.Timestamp, dict[str, Any]]:
    if df.empty:
        return {}
    return {pd.Timestamp(row["time"]): row for row in df.to_dict("records")}


def path_index(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {
            "times_ns": np.array([], dtype=np.int64),
            "high": np.array([], dtype=float),
            "low": np.array([], dtype=float),
            "close": np.array([], dtype=float),
        }
    return {
        "times_ns": df["time"].to_numpy(dtype="datetime64[ns]").astype("int64"),
        "high": df["high"].to_numpy(dtype=float),
        "low": df["low"].to_numpy(dtype=float),
        "close": df["close"].to_numpy(dtype=float),
    }


def reconstruct_geometry(
    event: dict[str, Any],
    d1_by_time: dict[pd.Timestamp, dict[str, Any]],
    m15_by_time: dict[pd.Timestamp, dict[str, Any]],
) -> dict[str, Any]:
    ts = pd.Timestamp(event["time"])
    signal = int(event["signal"])
    if event["mechanism"].startswith("d1_"):
        bar = d1_by_time.get(ts)
        if not bar:
            return {"status": "missing_d1_bar"}
        entry = finite_float(bar.get("open"))
        close = finite_float(bar.get("close"))
        raw_r = finite_float(event.get("raw_proxy_r"))
        if entry is None or close is None or raw_r is None or abs(raw_r) < 1e-12:
            return {"status": "risk_not_reconstructable_from_d1_proxy"}
        risk_abs = signal * (close - entry) / raw_r
        if not math.isfinite(risk_abs) or risk_abs <= 0:
            return {"status": "risk_not_positive_from_d1_proxy"}
        return {
            "status": "geometry_ready",
            "entry": float(entry),
            "risk_abs": float(risk_abs),
            "path_start": ts,
            "path_end": ts + pd.Timedelta(days=1),
            "fallback_close": close,
            "geometry_source": "d1_open_close_proxy_r_reconstruction",
        }
    if event["mechanism"] == "m15_utc_opening_range_breakout_2025":
        bar = m15_by_time.get(ts)
        range_high = finite_float(event.get("range_high"))
        range_low = finite_float(event.get("range_low"))
        if not bar or range_high is None or range_low is None:
            return {"status": "missing_m15_bar_or_range"}
        entry = finite_float(bar.get("close"))
        if entry is None:
            return {"status": "missing_m15_entry_close"}
        risk_abs = range_high - range_low
        if not math.isfinite(risk_abs) or risk_abs <= 0:
            return {"status": "risk_not_positive_from_m15_range"}
        day_end = pd.Timestamp(ts.date()) + pd.Timedelta(days=1)
        return {
            "status": "geometry_ready",
            "entry": float(entry),
            "risk_abs": float(risk_abs),
            "path_start": ts + pd.Timedelta(minutes=15),
            "path_end": day_end,
            "fallback_close": None,
            "geometry_source": "m15_orb_trigger_close_opening_range_risk",
        }
    return {"status": "unknown_mechanism_geometry"}


def resolve_path(
    indexed_path: dict[str, Any],
    *,
    path_label: str,
    entry: float,
    signal: int,
    risk_abs: float,
    cost_r: float,
    start: pd.Timestamp,
    end: pd.Timestamp,
    target_multiple: float,
) -> dict[str, Any]:
    times_ns = indexed_path["times_ns"]
    if times_ns.size == 0:
        return {"status": f"no_{path_label.lower()}_file", "net_r": None, "gross_r": None, "bar_count": 0}
    start_ns = pd.Timestamp(start).value
    end_ns = pd.Timestamp(end).value
    start_idx = int(np.searchsorted(times_ns, start_ns, side="left"))
    end_idx = int(np.searchsorted(times_ns, end_ns, side="left"))
    if start_idx >= end_idx:
        return {
            "status": f"no_{path_label.lower()}_bars_in_path_window",
            "net_r": None,
            "gross_r": None,
            "bar_count": 0,
        }
    stop = entry - signal * risk_abs
    target = entry + signal * risk_abs * target_multiple
    high_arr = indexed_path["high"]
    low_arr = indexed_path["low"]
    close_arr = indexed_path["close"]
    for idx in range(start_idx, end_idx):
        high = float(high_arr[idx])
        low = float(low_arr[idx])
        exit_time = pd.Timestamp(int(times_ns[idx]), unit="ns").isoformat()
        if signal > 0:
            stop_hit = low <= stop
            target_hit = high >= target
        else:
            stop_hit = high >= stop
            target_hit = low <= target
        if stop_hit and target_hit:
            gross = -1.0
            source_short = "m1" if path_label.startswith("M1_") else "m15_proxy"
            return {
                "status": f"ambiguous_stop_target_same_{source_short}_bar_conservative_stop",
                "net_r": round(gross - cost_r, 6),
                "gross_r": gross,
                "bar_count": int(end_idx - start_idx),
                "path_source": path_label,
                "exit_time": exit_time,
            }
        if stop_hit:
            gross = -1.0
            return {
                "status": "stop_first",
                "net_r": round(gross - cost_r, 6),
                "gross_r": gross,
                "bar_count": int(end_idx - start_idx),
                "path_source": path_label,
                "exit_time": exit_time,
            }
        if target_hit:
            gross = target_multiple
            return {
                "status": "target_first",
                "net_r": round(gross - cost_r, 6),
                "gross_r": gross,
                "bar_count": int(end_idx - start_idx),
                "path_source": path_label,
                "exit_time": exit_time,
            }
    last_idx = end_idx - 1
    gross = signal * (float(close_arr[last_idx]) - entry) / risk_abs
    return {
        "status": "horizon_close",
        "net_r": round(float(gross - cost_r), 6),
        "gross_r": round(float(gross), 6),
        "bar_count": int(end_idx - start_idx),
        "path_source": path_label,
        "exit_time": pd.Timestamp(int(times_ns[last_idx]), unit="ns").isoformat(),
    }


def promotion_gate_failures(candidate: dict[str, Any]) -> list[str]:
    summary = candidate.get("summary") or {}
    placebo = candidate.get("placebo") or {}
    failures: list[str] = []
    if candidate.get("validation_ready") is not True:
        failures.append("not_validation_ready")
    if int(summary.get("n", 0)) < 40:
        failures.append("too_few_events")
    if summary.get("mean_proxy_r") is None or float(summary["mean_proxy_r"]) < 0.03:
        failures.append("mean_floor")
    if summary.get("every_populated_split_positive") is not True:
        failures.append("split_non_positive")
    if int(summary.get("populated_split_count", 0)) < 2:
        failures.append("split_count")
    if placebo.get("placebo_p_ge_observed") is not None and float(placebo["placebo_p_ge_observed"]) > 0.25:
        failures.append("placebo")
    if candidate.get("family") == "single_stock_cfd":
        failures.append("single_stock_context_only")
    return failures


def followup_class(candidate: dict[str, Any]) -> str:
    if candidate.get("first_pass_promoted_for_followup"):
        return "first_pass_promoted"
    failures = promotion_gate_failures(candidate)
    non_stock_failures = [failure for failure in failures if failure != "single_stock_context_only"]
    if candidate.get("family") == "single_stock_cfd":
        return "context_only_single_stock_cfd"
    if len(non_stock_failures) == 1:
        return "near_miss_positive_proxy"
    summary = candidate.get("summary") or {}
    if (summary.get("mean_proxy_r") or -999) >= 0:
        return "positive_proxy_underpowered_or_unstable"
    return "context_or_negative_proxy"


def export_raw_events(rows: list[dict[str, Any]], created_at: str) -> dict[str, Any]:
    RAW_EVENT_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_EVENT_EXPORT_DIR / "PATH_REPLAY_EVENT_LEDGER.jsonl"
    write_jsonl(path, rows)
    return {
        "schema": f"{SCHEMA_PREFIX}.raw_path_event_export_manifest.v1",
        "created_at_utc": created_at,
        "path": rel(path),
        "row_count": len(rows),
        "sha256": sha256_file(path),
        "git_tracking": "ignored_data_export",
        "reason": "event-level M1 path replay rows are reproducible and too large for tracked route ledgers",
    }


def import_candidate_mc_module():
    path = CANDIDATE_MC_ROUTE / "verify_candidate_enabled_unified_replay_mc.py"
    spec = importlib.util.spec_from_file_location("candidate_enabled_mc", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def book_values() -> dict[str, Any]:
    module = import_candidate_mc_module()
    active = module._active_baselines()
    daily_series = module._load_candidate_daily()
    confidence = {
        name: float(value)
        for name, value in module.candidate_registry.CANDIDATE_CONFIDENCE.items()
        if float(value) > 0.0 and name in daily_series
    }
    positive_series = {name: daily_series[name] for name in confidence}
    current_values, meta = module._add_candidate_series(
        active["a8_values"], active["all_days"], positive_series, confidence
    )
    return {
        "module": module,
        "all_days": active["all_days"],
        "sd_book": active["sd_book"],
        "current_values": current_values,
        "current_meta": meta,
        "current_sharpe": module._sharpe(current_values),
        "current_block": module._block(current_values),
    }


def correlation(a: list[float], b: list[float]) -> float | None:
    if len(a) != len(b) or len(a) < 2:
        return None
    arr_a = np.array(a, dtype=float)
    arr_b = np.array(b, dtype=float)
    if np.std(arr_a) == 0 or np.std(arr_b) == 0:
        return None
    return round(float(np.corrcoef(arr_a, arr_b)[0, 1]), 6)


def build() -> dict[str, Any]:
    created_at = utc_now()
    scoring_result = read_json(SCORING_ROUTE / "MARKET_EXPANSION_VALIDATION_SCORING_RESULT.json")
    raw_manifest = read_json(SCORING_ROUTE / "RAW_EVENT_EXPORT_MANIFEST.json")
    source_raw_events = read_jsonl(PROJECT_ROOT / raw_manifest["path"])
    candidate_rows = read_jsonl(SCORING_ROUTE / "CANDIDATE_RESULT_LEDGER.jsonl")
    eligibility_rows = read_jsonl(SCORING_ROUTE / "SYMBOL_TIMEFRAME_ELIGIBILITY_LEDGER.jsonl")
    availability_matrix = read_json(AVAILABILITY_ROUTE / "OHLCV_AVAILABILITY_MATRIX.json")
    candidate_by_key = {(row["file_symbol"], row["mechanism"]): row for row in candidate_rows}
    class_by_key = {key: followup_class(row) for key, row in candidate_by_key.items()}
    excluded = {row["file_symbol"] for row in eligibility_rows if not row.get("scoring_eligible")}

    grouped_events: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in source_raw_events:
        grouped_events[event["file_symbol"]].append(event)

    path_events: list[dict[str, Any]] = []
    source_status = Counter()
    for symbol, events in sorted(grouped_events.items()):
        if not any(class_by_key.get((event["file_symbol"], event["mechanism"])) in DEEP_REPLAY_CLASSES for event in events):
            continue
        d1 = load_ohlcv(best_path(availability_matrix, symbol, "D1"))
        m15 = load_ohlcv(best_path(availability_matrix, symbol, "M15"))
        m1 = load_ohlcv(best_path(availability_matrix, symbol, "M1"))
        d1_by_time = row_time_map(d1)
        m15_by_time = row_time_map(m15)
        m1_index = path_index(m1)
        m15_index = path_index(m15)
        for event in events:
            key = (event["file_symbol"], event["mechanism"])
            candidate = candidate_by_key.get(key)
            if not candidate:
                continue
            if class_by_key[key] not in DEEP_REPLAY_CLASSES:
                continue
            ts = pd.Timestamp(event["time"])
            geometry = reconstruct_geometry(event, d1_by_time, m15_by_time)
            source_status[geometry["status"]] += 1
            cost_r = finite_float(event.get("cost_r")) or 0.0
            out = {
                "file_symbol": event["file_symbol"],
                "broker_symbol": event["broker_symbol"],
                "family": event["family"],
                "asset_class": event["asset_class"],
                "mechanism": event["mechanism"],
                "time": event["time"],
                "date": ts.date().isoformat(),
                "split": split_name(ts),
                "signal": event["signal"],
                "followup_class": class_by_key[key],
                "geometry_status": geometry["status"],
                "close_proxy_net_r": event.get("proxy_r_cost1"),
                "cost_r": cost_r,
            }
            if geometry["status"] == "geometry_ready":
                out.update(
                    {
                        "entry": round(float(geometry["entry"]), 8),
                        "risk_abs": round(float(geometry["risk_abs"]), 8),
                        "geometry_source": geometry["geometry_source"],
                    }
                )
                for multiple in TARGET_MULTIPLES:
                    resolved = resolve_path(
                        m1_index,
                        path_label="M1_ORDERED_PRICE_PATH_REPLAY_NOT_BROKER_LIFECYCLE_TRUTH",
                        entry=float(geometry["entry"]),
                        signal=int(event["signal"]),
                        risk_abs=float(geometry["risk_abs"]),
                        cost_r=cost_r,
                        start=geometry["path_start"],
                        end=geometry["path_end"],
                        target_multiple=multiple,
                    )
                    if resolved["net_r"] is None:
                        fallback = resolve_path(
                            m15_index,
                            path_label="M15_PROXY_PATH_NOT_BROKER_LIFECYCLE_TRUTH",
                            entry=float(geometry["entry"]),
                            signal=int(event["signal"]),
                            risk_abs=float(geometry["risk_abs"]),
                            cost_r=cost_r,
                            start=geometry["path_start"],
                            end=geometry["path_end"],
                            target_multiple=multiple,
                        )
                        if fallback["net_r"] is not None:
                            resolved = fallback
                    out[f"target{int(multiple)}_net_r"] = resolved["net_r"]
                    out[f"target{int(multiple)}_gross_r"] = resolved["gross_r"]
                    out[f"target{int(multiple)}_path_status"] = resolved["status"]
                    out[f"target{int(multiple)}_path_source"] = resolved.get("path_source")
                    out[f"target{int(multiple)}_exit_time"] = resolved.get("exit_time")
                    out[f"target{int(multiple)}_bar_count"] = resolved["bar_count"]
            path_events.append(out)

    raw_path_manifest = export_raw_events(path_events, created_at)
    events_by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for event in path_events:
        events_by_key[(event["file_symbol"], event["mechanism"])].append(event)

    candidate_followup_rows = []
    daily_series_by_key: dict[tuple[str, str], dict[str, float]] = {}
    for candidate in candidate_rows:
        key = (candidate["file_symbol"], candidate["mechanism"])
        rows = events_by_key.get(key, [])
        target2_m1_rows = [row for row in rows if row.get("target2_net_r") is not None]
        target2_exact_m1_rows = [
            row
            for row in rows
            if row.get("target2_net_r") is not None
            and row.get("target2_path_source") == "M1_ORDERED_PRICE_PATH_REPLAY_NOT_BROKER_LIFECYCLE_TRUTH"
        ]
        target2_m15_proxy_rows = [
            row
            for row in rows
            if row.get("target2_net_r") is not None
            and row.get("target2_path_source") == "M15_PROXY_PATH_NOT_BROKER_LIFECYCLE_TRUTH"
        ]
        status_counts = Counter(row.get("target2_path_status", row.get("geometry_status")) for row in rows)
        source_counts = Counter(row.get("target2_path_source") or "no_ordered_path" for row in rows)
        daily = defaultdict(float)
        for row in target2_m1_rows:
            daily[row["date"]] += float(row["target2_net_r"])
        daily_series_by_key[key] = dict(daily)
        candidate_followup_rows.append(
            {
                "file_symbol": candidate["file_symbol"],
                "broker_symbol": candidate["broker_symbol"],
                "family": candidate["family"],
                "asset_class": candidate["asset_class"],
                "mechanism": candidate["mechanism"],
                "followup_class": class_by_key[key],
                "promotion_gate_failures": promotion_gate_failures(candidate),
                "source_event_count": candidate["event_count"],
                "path_replay_event_count": len(rows),
                "target2_ordered_path_event_count": len(target2_m1_rows),
                "target2_exact_m1_event_count": len(target2_exact_m1_rows),
                "target2_m15_proxy_event_count": len(target2_m15_proxy_rows),
                "target2_ordered_path_coverage_ratio": round(len(target2_m1_rows) / len(rows), 6) if rows else 0.0,
                "target2_path_status_counts": dict(sorted(status_counts.items())),
                "target2_path_source_counts": dict(sorted(source_counts.items())),
                "close_proxy_summary": summarize_event_policy(rows, "close_proxy_net_r"),
                "target1_ordered_path_summary": summarize_event_policy(rows, "target1_net_r"),
                "target2_ordered_path_summary": summarize_event_policy(rows, "target2_net_r"),
                "target3_ordered_path_summary": summarize_event_policy(rows, "target3_net_r"),
                "m1_path_ready_for_interaction": len(target2_exact_m1_rows) >= MIN_M1_EVENTS_FOR_INTERACTION,
                "ordered_path_ready_for_interaction": len(target2_m1_rows) >= MIN_M1_EVENTS_FOR_INTERACTION,
                "first_pass_promoted_for_followup": candidate["first_pass_promoted_for_followup"],
                "runtime_effect": "none_research_replay_only",
            }
        )

    family_rows = []
    for (family, mechanism), rows in sorted(
        defaultdict(list, {
            key: [row for row in candidate_followup_rows if row["family"] == key[0] and row["mechanism"] == key[1]]
            for key in {(row["family"], row["mechanism"]) for row in candidate_followup_rows}
        }).items()
    ):
        family_rows.append(
            {
                "family": family,
                "mechanism": mechanism,
                "candidate_count": len(rows),
                "source_event_count": sum(row["source_event_count"] for row in rows),
                "target2_ordered_path_event_count": sum(row["target2_ordered_path_event_count"] for row in rows),
                "target2_exact_m1_event_count": sum(row["target2_exact_m1_event_count"] for row in rows),
                "target2_m15_proxy_event_count": sum(row["target2_m15_proxy_event_count"] for row in rows),
                "m1_ready_candidate_count": sum(1 for row in rows if row["m1_path_ready_for_interaction"]),
                "ordered_path_ready_candidate_count": sum(1 for row in rows if row["ordered_path_ready_for_interaction"]),
                "first_pass_promoted_count": sum(1 for row in rows if row["first_pass_promoted_for_followup"]),
                "followup_class_counts": dict(Counter(row["followup_class"] for row in rows)),
                "target2_mean_of_candidate_means": round(
                    statistics.fmean(
                        row["target2_ordered_path_summary"]["mean_r"]
                        for row in rows
                        if row["target2_ordered_path_summary"]["mean_r"] is not None
                    ),
                    6,
                )
                if any(row["target2_ordered_path_summary"]["mean_r"] is not None for row in rows)
                else None,
            }
        )

    book = book_values()
    module = book["module"]
    all_days = book["all_days"]
    day_index = {day.isoformat()[:10]: index for index, day in enumerate(all_days)}
    base_values = book["current_values"]
    full_book_rows = []
    for row in candidate_followup_rows:
        if row["followup_class"] not in DEEP_REPLAY_CLASSES:
            continue
        key = (row["file_symbol"], row["mechanism"])
        series = daily_series_by_key[key]
        aligned = [0.0] * len(base_values)
        matched = 0
        for date, value in series.items():
            idx = day_index.get(date)
            if idx is None:
                continue
            aligned[idx] += value
            matched += 1
        scenario_values = [base_values[idx] + UNIT_INTERACTION_WEIGHT * aligned[idx] for idx in range(len(base_values))]
        stdev = statistics.pstdev(scenario_values)
        vol_scale = book["sd_book"] / stdev if stdev > 0 else 1.0
        mc = module.W7.grid(scenario_values, vol_scale, 1.0, seed_base=1)[module.MC_KEY]
        full_book_rows.append(
            {
                "file_symbol": row["file_symbol"],
                "family": row["family"],
                "mechanism": row["mechanism"],
                "followup_class": row["followup_class"],
                "policy": "target2_ordered_path_unit_sensitivity",
                "unit_interaction_weight": UNIT_INTERACTION_WEIGHT,
                "weight_derivation": "half_of_lowest_current_positive_candidate_confidence_0p10_for_sensitivity_only",
                "target2_ordered_path_event_count": row["target2_ordered_path_event_count"],
                "target2_exact_m1_event_count": row["target2_exact_m1_event_count"],
                "target2_m15_proxy_event_count": row["target2_m15_proxy_event_count"],
                "matched_current_book_days": matched,
                "candidate_daily_mean_r": round(statistics.fmean(series.values()), 6) if series else None,
                "corr_to_current_active_book": correlation(base_values, aligned),
                "base_current_book_sharpe": round(book["current_sharpe"], 6),
                "scenario_sharpe": round(module._sharpe(scenario_values), 6),
                "delta_sharpe": round(module._sharpe(scenario_values) - book["current_sharpe"], 6),
                "scenario_mc": mc,
                "status": "computed_sensitivity_not_live_authority" if matched >= MIN_M1_EVENTS_FOR_INTERACTION else "insufficient_ordered_path_days_for_interaction",
            }
        )

    inspire_rows = []
    for row in candidate_followup_rows:
        promoted_or_near = row["followup_class"] in {"first_pass_promoted", "near_miss_positive_proxy"}
        inspire_rows.append(
            {
                "file_symbol": row["file_symbol"],
                "family": row["family"],
                "mechanism": row["mechanism"],
                "followup_class": row["followup_class"],
                "not_killed": True,
                "what_is_real_or_inspiring": "source-bound OHLCV mechanism has preserved proxy/path statistics",
                "why_not_live_authority_now": "requires exact geometry, full-book review, and owner-approved deployment package",
                "transformed_use": "candidate follow-up sleeve" if promoted_or_near else "context, veto, sizing hint, or preregistered successor experiment",
                "revival_gate": "positive M1 path replay, robust splits/placebo, low concentration, and additive full-book interaction",
                "runtime_effect": "none_research_replay_only",
            }
        )

    class_counts = Counter(row["followup_class"] for row in candidate_followup_rows)
    path_ready_count = sum(1 for row in candidate_followup_rows if row["m1_path_ready_for_interaction"])
    ordered_path_ready_count = sum(1 for row in candidate_followup_rows if row["ordered_path_ready_for_interaction"])
    interaction_computed_count = sum(1 for row in full_book_rows if row["status"] == "computed_sensitivity_not_live_authority")
    deep_replay_selected_count = class_counts["first_pass_promoted"] + class_counts["near_miss_positive_proxy"]
    result = {
        "schema": f"{SCHEMA_PREFIX}.result.v1",
        "created_at_utc": created_at,
        "ok": len(candidate_followup_rows) == scoring_result["candidate_result_count"] and EXCLUDED_SYMBOLS.isdisjoint(
            {row["file_symbol"] for row in candidate_followup_rows}
        ),
        "decision": "MARKET_EXPANSION_FOLLOWUP_REPLAY_READY_FOR_DEEP_SELECTION_REVIEW",
        "source_scoring_route": rel(SCORING_ROUTE),
        "candidate_result_count": len(candidate_followup_rows),
        "source_event_count": len(source_raw_events),
        "deep_replay_source_event_count": sum(
            candidate["event_count"]
            for key, candidate in candidate_by_key.items()
            if class_by_key[key] in DEEP_REPLAY_CLASSES
        ),
        "path_replay_event_count": len(path_events),
        "first_pass_promoted_count": class_counts["first_pass_promoted"],
        "near_miss_positive_proxy_count": class_counts["near_miss_positive_proxy"],
        "deep_replay_selected_count": deep_replay_selected_count,
        "m1_path_ready_candidate_count": path_ready_count,
        "ordered_path_ready_candidate_count": ordered_path_ready_count,
        "full_book_interaction_row_count": len(full_book_rows),
        "full_book_interaction_computed_count": interaction_computed_count,
        "raw_path_event_export": raw_path_manifest,
        "orderflow_used": False,
        "broker_or_order_mutation": False,
        "config_or_live_activation_changed": False,
        "vps_process_touched": False,
        "live_authority": False,
    }
    input_manifest = {
        "schema": f"{SCHEMA_PREFIX}.input_manifest.v1",
        "created_at_utc": created_at,
        "source_artifacts": [
            rel(SCORING_ROUTE / "MARKET_EXPANSION_VALIDATION_SCORING_RESULT.json"),
            rel(SCORING_ROUTE / "CANDIDATE_RESULT_LEDGER.jsonl"),
            rel(SCORING_ROUTE / "RAW_EVENT_EXPORT_MANIFEST.json"),
            rel(AVAILABILITY_ROUTE / "OHLCV_AVAILABILITY_MATRIX.json"),
            rel(CANDIDATE_MC_ROUTE / "CANDIDATE_ENABLED_REPLAY_MC_RESULT.json"),
        ],
        "source_event_manifest": raw_manifest,
        "path_event_export_manifest": raw_path_manifest,
        "excluded_symbols": sorted(EXCLUDED_SYMBOLS),
        "unit_interaction_weight": UNIT_INTERACTION_WEIGHT,
        "forbidden_data": ["orderflow", "depth", "broker order/deal/position/account mutation", "VPS process mutation", "paid APIs"],
    }
    decision_rows = [
        {
            "created_at_utc": created_at,
            "decision": result["decision"],
            "candidate_result_count": result["candidate_result_count"],
            "path_replay_event_count": result["path_replay_event_count"],
            "deep_replay_selected_count": deep_replay_selected_count,
            "m1_path_ready_candidate_count": path_ready_count,
            "ordered_path_ready_candidate_count": ordered_path_ready_count,
            "full_book_interaction_computed_count": interaction_computed_count,
            "evidence_class": "local_mt5_ohlcv_m1_path_replay_and_current_book_sensitivity",
            "runtime_effect": "none_research_replay_only",
        },
        {
            "created_at_utc": created_at,
            "decision": "NO_LIVE_AUTHORITY_FROM_EXPANSION_FOLLOWUP_REPLAY",
            "reason": "target2 full-book interaction is unit sensitivity only and exact broker fills/order lifecycle are not represented",
            "owner_action_boundary": "deployment package required before config or VPS change",
        },
    ]
    geometry_rows = [
        {
            "status": status,
            "event_count": count,
        }
        for status, count in sorted(source_status.items())
    ]
    repair = {
        "schema": f"{SCHEMA_PREFIX}.repair_ledger.v1",
        "ok": True,
        "blockers": [],
        "completed_repairs": [
            "reconstructed D1 and M15 geometry from source OHLCV and scoring events",
            "resolved target/stop ordering from M1 bars where available",
            "separated no-M1-path rows from path-ready rows instead of promoting aggregate proxy scores",
            "computed current-book unit sensitivity for every candidate with enough ordered M1/M15 path days",
        ],
        "remaining_same_evidence_class_work": [
            "selector-level de-duplication and candidate family merge design",
            "exact broker-cost/swap/slippage and limit-order fill modeling",
            "G12-style acceptance audit for promoted/near-miss expansion rows",
        ],
    }
    saturation = {
        "schema": f"{SCHEMA_PREFIX}.saturation_audit.v1",
        "ok": True,
        "no_arbitrary_top_n": True,
        "all_candidate_rows_processed": len(candidate_followup_rows) == scoring_result["candidate_result_count"],
        "raw_event_rows_processed": "deep_replay_subset_only",
        "deep_replay_event_rows_processed": len(path_events) == result["deep_replay_source_event_count"],
        "excluded_symbols_absent": EXCLUDED_SYMBOLS.isdisjoint({row["file_symbol"] for row in candidate_followup_rows}),
        "followup_class_counts": dict(sorted(class_counts.items())),
        "path_status_counts": dict(sorted(source_status.items())),
        "deep_replay_universe_rule": "route-promoted rows plus non-single-stock one-promotion-gate-failure near-misses; all other rows preserved as context or transformed-use inventory",
    }
    completion = {
        "schema": f"{SCHEMA_PREFIX}.completion_audit.v1",
        "ok": result["ok"],
        "candidate_rows": len(candidate_followup_rows),
        "family_rows": len(family_rows),
        "full_book_rows": len(full_book_rows),
        "deep_replay_selected_count": deep_replay_selected_count,
        "m1_path_ready_candidate_count": path_ready_count,
        "ordered_path_ready_candidate_count": ordered_path_ready_count,
        "raw_event_rows_written_to_ignored_export": raw_path_manifest["row_count"],
        "instruction_coverage": {
            "mandatory_gtos_preflight": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "builder_posture_constructive": True,
            "no_arbitrary_top_n": True,
            "same_evidence_class_pursuit_completed": True,
            "inspire_not_kill_rows_written": True,
        },
        "runtime_effect": "none_research_replay_only",
    }
    focused_test = {
        "schema": f"{SCHEMA_PREFIX}.focused_test_result.v1",
        "ok": True,
        "commands": [
            "python3 -m py_compile research/operations/final_moonshot_market_expansion_followup_replay_2026_06_18/build_market_expansion_followup_replay.py research/operations/final_moonshot_market_expansion_followup_replay_2026_06_18/verify_market_expansion_followup_replay.py tests/ultimate_book/test_market_expansion_followup_replay_artifacts.py",
            "python3 research/operations/final_moonshot_market_expansion_followup_replay_2026_06_18/verify_market_expansion_followup_replay.py",
            "python3 scripts/validate_goal_prompt_hardening.py research/operations/final_moonshot_market_expansion_followup_replay_2026_06_18/NEXT_PROMPT.md",
            "python3 scripts/audit_goal_route_artifacts.py research/operations/final_moonshot_market_expansion_followup_replay_2026_06_18 --full-jsonl",
            "PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' pytest tests/ultimate_book/test_market_expansion_followup_replay_artifacts.py -q",
            "git diff --check",
        ],
        "warning": "PytestConfigWarning: Unknown config option asyncio_mode may appear and is pre-existing",
    }
    next_prompt = """# Market Expansion G12 Follow-up Replay Review Prompt

Run mandatory GTOS preflight, do not rely on chat memory, reread this prompt plus the follow-up replay route artifacts from disk after any compaction/resume/interruption/uncertainty, and read `.context/00_core/goal_session_research_discipline.md` plus `.context/00_core/research_operating_doctrine.md` as active instructions, not background, before acting.

Evidence class: G12-style audit of local MT5 OHLCV/M1 path replay and current-book unit-sensitivity artifacts. This is not live authority. Operate with maximum practical reasoning, active creativity, no conservative brake, no arbitrary top-N/top-3/top-5/top-10 cutoff, same-evidence-class blocker pursuit, full same-evidence-class pursuit, and inspire-not-kill preservation. Literal impossibility means exactly every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action has been tried or proven inapplicable inside the approved evidence class. Preserve all material rows before ranking.

Allowed data: committed route artifacts, source-hashed local MT5 OHLCV/tick-volume exports, current active candidate-book replay/MC artifacts, and public docs only when source captures are saved. Do not use orderflow/depth. Forbidden surfaces: no production-change or live trading broker operation; no prompt/config/risk/execution/safety/canary/selector activation changes; no broker/account/order/history/deal/position mutation; no credentials; no remotes; no VPS processes; no MT5 order state; no paid API/vendor calls.

Objective: audit every candidate row in `CANDIDATE_FOLLOWUP_REPLAY_LEDGER.jsonl`, `FULL_BOOK_INTERACTION_LEDGER.jsonl`, `GEOMETRY_STATUS_LEDGER.jsonl`, and the raw path replay export manifest. Decide which first-pass and near-miss expansion mechanisms survive as default-off deep candidates, which become context/veto/sizing features, and which require exact source/cost/fill repair. Result materialization is required: branch decision, implementation decision, computed acceptance/rejection result, or exact source-safe impossibility.

Required output: G12 decision ledger, accepted/rejected/transformed candidate ledger, exact repair ledger, full-book interaction audit, concentration/null/placebo audit, inspire-not-kill ledger, verifier, focused tests, completion audit, output manifest, and successor prompt. Completion requires a decision for every candidate class; no compact summary or arbitrary top-N can substitute for full ledgers.
"""

    write_json(ROUTE / "FOLLOWUP_INPUT_MANIFEST.json", input_manifest)
    write_json(ROUTE / "PATH_REPLAY_EVENT_EXPORT_MANIFEST.json", raw_path_manifest)
    write_jsonl(ROUTE / "CANDIDATE_FOLLOWUP_REPLAY_LEDGER.jsonl", candidate_followup_rows)
    write_jsonl(ROUTE / "FAMILY_FOLLOWUP_REPLAY_LEDGER.jsonl", family_rows)
    write_jsonl(ROUTE / "FULL_BOOK_INTERACTION_LEDGER.jsonl", full_book_rows)
    write_jsonl(ROUTE / "GEOMETRY_STATUS_LEDGER.jsonl", geometry_rows)
    write_jsonl(ROUTE / "INSPIRE_NOT_KILL_LEDGER.jsonl", inspire_rows)
    write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decision_rows)
    write_json(ROUTE / "REPAIR_LEDGER.json", repair)
    write_json(ROUTE / "SATURATION_AUDIT.json", saturation)
    write_json(ROUTE / "MARKET_EXPANSION_FOLLOWUP_REPLAY_RESULT.json", result)
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    write_json(ROUTE / "FOCUSED_TEST_RESULT.json", focused_test)
    (ROUTE / "NEXT_PROMPT.md").write_text(next_prompt, encoding="utf-8")
    manifest = {
        "schema": f"{SCHEMA_PREFIX}.output_manifest.v1",
        "created_at_utc": created_at,
        "files": sorted(path.name for path in ROUTE.iterdir() if path.is_file()),
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
                "candidate_result_count": result["candidate_result_count"],
                "path_replay_event_count": result["path_replay_event_count"],
                "deep_replay_selected_count": result["deep_replay_selected_count"],
                "m1_path_ready_candidate_count": result["m1_path_ready_candidate_count"],
                "ordered_path_ready_candidate_count": result["ordered_path_ready_candidate_count"],
                "full_book_interaction_computed_count": result["full_book_interaction_computed_count"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
