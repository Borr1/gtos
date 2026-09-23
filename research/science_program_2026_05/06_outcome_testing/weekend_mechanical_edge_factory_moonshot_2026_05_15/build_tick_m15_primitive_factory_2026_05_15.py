#!/usr/bin/env python3
"""Build descriptor-only M15 tick primitives from local parquet sources.

The factory consumes the Route C tick source contract and emits one row per
captured M15 bar. Percentile flags are same-symbol/session descriptors only;
they are not entry signals, target results, R/PnL, validation, live-readiness,
or promotion evidence.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
STAMP = "2026-05-15"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

SOURCE_LEDGER = ROUTE_DIR / f"TICK_PARQUET_SOURCE_CONTRACT_LEDGER_{STAMP}.jsonl"
RESULT_PATH = ROUTE_DIR / f"TICK_M15_PRIMITIVE_FACTORY_RESULT_{STAMP}.json"
EVENT_LEDGER = ROUTE_DIR / f"TICK_M15_PRIMITIVE_EVENT_LEDGER_{STAMP}.jsonl"
BASELINE_LEDGER = ROUTE_DIR / f"TICK_M15_PRIMITIVE_BASELINE_LEDGER_{STAMP}.jsonl"
FLAG_SUMMARY_LEDGER = ROUTE_DIR / f"TICK_M15_PRIMITIVE_FLAG_SUMMARY_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"TICK_M15_PRIMITIVE_FACTORY_SUMMARY_{STAMP}.md"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def utc_iso(ts: Any) -> str | None:
    if ts is None:
        return None
    if hasattr(ts, "to_pydatetime"):
        ts = ts.to_pydatetime()
    if hasattr(ts, "tzinfo") and ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    if hasattr(ts, "isoformat"):
        return ts.isoformat().replace("+00:00", "Z")
    return str(ts)


def safe_float(value: Any) -> float | None:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if value != value or value in (float("inf"), float("-inf")):
        return None
    return value


def session_bucket(ts: Any) -> str:
    if hasattr(ts, "to_pydatetime"):
        ts = ts.to_pydatetime()
    minute = ts.hour * 60 + ts.minute
    if 0 <= minute < 3 * 60:
        return "tokyo_core_0000_0300"
    if 7 * 60 <= minute < 10 * 60 + 30:
        return "london_core_0700_1030"
    if 13 * 60 <= minute < 17 * 60:
        return "ny_core_1300_1700"
    return "off_core_session"


def quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    if len(values) == 1:
        return values[0]
    pos = (len(values) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(values) - 1)
    frac = pos - lo
    return values[lo] * (1.0 - frac) + values[hi] * frac


def compute_file_events(source_row: dict[str, Any]) -> list[dict[str, Any]]:
    import pandas as pd
    import pyarrow.parquet as pq

    path = Path(source_row["path"])
    table = pq.read_table(
        path,
        columns=["ts_utc", "ts_msc", "bid", "ask", "last", "volume", "flags", "inferred_aggressor"],
    )
    df = table.to_pandas()
    if df.empty:
        return []

    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    df = df.dropna(subset=["ts_utc", "bid", "ask"]).sort_values("ts_utc").reset_index(drop=True)
    if df.empty:
        return []

    df["bar_open_utc"] = df["ts_utc"].dt.floor("15min")
    df["mid"] = (df["bid"].astype(float) + df["ask"].astype(float)) / 2.0
    df["spread"] = df["ask"].astype(float) - df["bid"].astype(float)
    aggressor = df["inferred_aggressor"].astype(str)
    df["vol_eff"] = df["volume"].astype(float)
    df.loc[df["vol_eff"] <= 0, "vol_eff"] = 1.0
    df["signed_delta"] = 0.0
    df.loc[aggressor == "buy", "signed_delta"] = df.loc[aggressor == "buy", "vol_eff"]
    df.loc[aggressor == "sell", "signed_delta"] = -df.loc[aggressor == "sell", "vol_eff"]

    current_utc_date = datetime.now(UTC).date().isoformat()
    rows: list[dict[str, Any]] = []
    for bar_open, group in df.groupby("bar_open_utc", sort=True):
        group = group.sort_values("ts_utc")
        mid = group["mid"]
        spread = group["spread"]
        signed = group["signed_delta"]
        running_delta = signed.cumsum()
        n_ticks = int(len(group))
        buy_ticks = int((group["inferred_aggressor"].astype(str) == "buy").sum())
        sell_ticks = int((group["inferred_aggressor"].astype(str) == "sell").sum())
        neutral_ticks = int((group["inferred_aggressor"].astype(str) == "neutral").sum())
        n_classified = buy_ticks + sell_ticks
        mid_open = safe_float(mid.iloc[0])
        mid_close = safe_float(mid.iloc[-1])
        price_change = None
        if mid_open is not None and mid_close is not None:
            price_change = mid_close - mid_open
        cumulative_delta = safe_float(signed.sum()) or 0.0
        cvd_divergence = False
        if price_change is not None and abs(price_change) > 1e-12 and abs(cumulative_delta) > 1e-12:
            cvd_divergence = (price_change > 0) != (cumulative_delta > 0)
        duplicate_ts_msc_rows = int(group.duplicated(subset=["ts_msc"]).sum()) if "ts_msc" in group else 0
        bar_date = bar_open.date().isoformat()
        rows.append({
            "route_id": ROUTE_ID,
            "symbol": source_row["symbol"],
            "trade_date": source_row["trade_date"],
            "bar_open_utc": utc_iso(bar_open),
            "bar_close_utc": utc_iso(bar_open + pd.Timedelta(minutes=15)),
            "session_bucket": session_bucket(bar_open),
            "source_file": source_row["path"],
            "source_completeness": "current_day_partial_at_generation" if bar_date == current_utc_date else "closed_or_historical_capture_file",
            "n_ticks": n_ticks,
            "duplicate_ts_msc_rows": duplicate_ts_msc_rows,
            "mid_open": mid_open,
            "mid_close": mid_close,
            "mid_high": safe_float(mid.max()),
            "mid_low": safe_float(mid.min()),
            "price_change": safe_float(price_change),
            "price_range": safe_float(mid.max() - mid.min()),
            "cumulative_delta": cumulative_delta,
            "abs_cumulative_delta": abs(cumulative_delta),
            "max_running_delta": safe_float(running_delta.max()) or 0.0,
            "min_running_delta": safe_float(running_delta.min()) or 0.0,
            "buy_ticks": buy_ticks,
            "sell_ticks": sell_ticks,
            "neutral_ticks": neutral_ticks,
            "n_classified_ticks": n_classified,
            "buy_pct": safe_float(buy_ticks / n_classified) if n_classified > 0 else None,
            "spread_median": safe_float(spread.median()),
            "spread_max": safe_float(spread.max()),
            "spread_close": safe_float(spread.iloc[-1]),
            "tick_velocity_per_sec": safe_float(n_ticks / 900.0),
            "cvd_divergence_flag": cvd_divergence,
            "primitive_flags": [],
            "primitive_flag_count": 0,
            "evidence_boundary": "M15 tick descriptor only; no target outcome, R/PnL, live-readiness, or promotion",
            "safe_flags": SAFE_FLAGS,
        })
    return rows


def build_baselines(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in events:
        grouped.setdefault((row["symbol"], row["session_bucket"]), []).append(row)

    baseline_rows: list[dict[str, Any]] = []
    for (symbol, session), rows in sorted(grouped.items()):
        metrics = {
            "abs_cumulative_delta": [r["abs_cumulative_delta"] for r in rows if r.get("abs_cumulative_delta") is not None],
            "tick_velocity_per_sec": [r["tick_velocity_per_sec"] for r in rows if r.get("tick_velocity_per_sec") is not None],
            "spread_max": [r["spread_max"] for r in rows if r.get("spread_max") is not None],
            "price_range": [r["price_range"] for r in rows if r.get("price_range") is not None],
        }
        thresholds: dict[str, dict[str, float | None]] = {}
        for metric, values in metrics.items():
            thresholds[metric] = {
                "p50": safe_float(quantile(values, 0.50)),
                "p75": safe_float(quantile(values, 0.75)),
                "p90": safe_float(quantile(values, 0.90)),
                "p95": safe_float(quantile(values, 0.95)),
            }
        baseline_rows.append({
            "route_id": ROUTE_ID,
            "symbol": symbol,
            "session_bucket": session,
            "bar_count": len(rows),
            "first_bar_open_utc": min(r["bar_open_utc"] for r in rows),
            "last_bar_open_utc": max(r["bar_open_utc"] for r in rows),
            "thresholds": thresholds,
            "baseline_status": "descriptor_baseline_only",
            "safe_flags": SAFE_FLAGS,
        })
    return baseline_rows


def flag_events(events: list[dict[str, Any]], baselines: list[dict[str, Any]]) -> None:
    baseline_map = {(row["symbol"], row["session_bucket"]): row for row in baselines}
    for row in events:
        baseline = baseline_map[(row["symbol"], row["session_bucket"])]
        thresholds = baseline["thresholds"]
        flags: list[str] = []
        if baseline["bar_count"] < 20:
            flags.append("BASELINE_SMALL_SAMPLE_LT20")
        abs_delta_p95 = thresholds["abs_cumulative_delta"]["p95"]
        abs_delta_p75 = thresholds["abs_cumulative_delta"]["p75"]
        velocity_p95 = thresholds["tick_velocity_per_sec"]["p95"]
        spread_p95 = thresholds["spread_max"]["p95"]
        range_p95 = thresholds["price_range"]["p95"]
        buy_pct = row.get("buy_pct")
        if abs_delta_p95 is not None and row["abs_cumulative_delta"] >= abs_delta_p95 and row["n_classified_ticks"] >= 10:
            flags.append("DELTA_IMPULSE_P95_SAME_SYMBOL_SESSION")
        if velocity_p95 is not None and row["tick_velocity_per_sec"] >= velocity_p95:
            flags.append("TICK_VELOCITY_BURST_P95_SAME_SYMBOL_SESSION")
        if spread_p95 is not None and row["spread_max"] is not None and row["spread_max"] >= spread_p95:
            flags.append("SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION")
        if range_p95 is not None and row["price_range"] is not None and row["price_range"] >= range_p95:
            flags.append("TICK_RANGE_EXPANSION_P95_SAME_SYMBOL_SESSION")
        if (
            row["cvd_divergence_flag"]
            and abs_delta_p75 is not None
            and row["abs_cumulative_delta"] >= abs_delta_p75
            and row["n_classified_ticks"] >= 10
        ):
            flags.append("ABSORPTION_PROXY_CVD_DIVERGENCE_DELTA_P75")
        if buy_pct is not None and row["n_classified_ticks"] >= 10 and (buy_pct >= 0.90 or buy_pct <= 0.10):
            flags.append("ONE_SIDED_TICK_FLOW_P90")
        row["primitive_flags"] = flags
        row["primitive_flag_count"] = len(flags)


def build_flag_summary(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    denominator: dict[tuple[str, str], int] = {}
    counts: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in events:
        key = (row["symbol"], row["session_bucket"])
        denominator[key] = denominator.get(key, 0) + 1
        for flag in row["primitive_flags"]:
            flag_key = (row["symbol"], row["session_bucket"], flag)
            if flag_key not in counts:
                counts[flag_key] = {
                    "route_id": ROUTE_ID,
                    "symbol": row["symbol"],
                    "session_bucket": row["session_bucket"],
                    "primitive_flag": flag,
                    "flagged_bar_count": 0,
                    "first_bar_open_utc": row["bar_open_utc"],
                    "last_bar_open_utc": row["bar_open_utc"],
                    "evidence_boundary": "descriptor frequency only; no target outcome or strategy result",
                    "safe_flags": SAFE_FLAGS,
                }
            counts[flag_key]["flagged_bar_count"] += 1
            counts[flag_key]["first_bar_open_utc"] = min(counts[flag_key]["first_bar_open_utc"], row["bar_open_utc"])
            counts[flag_key]["last_bar_open_utc"] = max(counts[flag_key]["last_bar_open_utc"], row["bar_open_utc"])
    rows = []
    for key, row in sorted(counts.items()):
        denom = denominator[(key[0], key[1])]
        row["denominator_bar_count"] = denom
        row["flagged_bar_pct"] = safe_float(row["flagged_bar_count"] / denom) if denom else None
        rows.append(row)
    return rows


def main() -> int:
    generated_utc = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    source_rows = [
        row for row in read_jsonl(SOURCE_LEDGER)
        if row.get("schema_status") == "SCHEMA_OK"
    ]

    all_events: list[dict[str, Any]] = []
    read_errors: list[str] = []
    for source_row in source_rows:
        try:
            all_events.extend(compute_file_events(source_row))
        except Exception as exc:  # noqa: BLE001
            read_errors.append(f"{source_row.get('path')}:{type(exc).__name__}:{exc}")

    baselines = build_baselines(all_events)
    flag_events(all_events, baselines)
    flag_summary = build_flag_summary(all_events)

    write_jsonl(EVENT_LEDGER, all_events)
    write_jsonl(BASELINE_LEDGER, baselines)
    write_jsonl(FLAG_SUMMARY_LEDGER, flag_summary)

    symbols = sorted({row["symbol"] for row in all_events})
    sessions = sorted({row["session_bucket"] for row in all_events})
    partial_rows = sum(1 for row in all_events if row["source_completeness"] == "current_day_partial_at_generation")
    flagged_rows = sum(1 for row in all_events if row["primitive_flag_count"] > 0)

    result = {
        "schema": "tick_m15_primitive_factory_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "TICK_M15_DESCRIPTOR_FACTORY_ONLY",
        "claim_boundary": "M15 tick primitive descriptors only. No edge, R/PnL, expectancy, validation, live-readiness, or promotion claim.",
        "counts": {
            "source_file_rows": len(source_rows),
            "tick_event_rows": len(all_events),
            "baseline_rows": len(baselines),
            "flag_summary_rows": len(flag_summary),
            "primitive_flagged_rows": flagged_rows,
            "partial_current_day_event_rows": partial_rows,
            "read_error_rows": len(read_errors),
        },
        "symbols": symbols,
        "sessions": sessions,
        "read_errors": read_errors,
        "open_blockers": [
            "descriptor flags require target-movement and same-denominator controls before hypothesis testing",
            "current-day partial bars must not be used as sealed evidence",
            "MT5 tick aggressor remains proxy-only on current broker feed",
            "entry geometry, spread/slippage/commission, and fillability are not modeled here",
        ],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    top_flags = sorted(flag_summary, key=lambda r: (r["primitive_flag"], r["symbol"], r["session_bucket"]))
    summary = [
        "# Tick M15 Primitive Factory",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: descriptor factory only. No edge, R/PnL, validation, live-readiness, or promotion verdict.",
        "",
        "## Counts",
        "",
        f"- Source parquet files consumed: `{len(source_rows)}`",
        f"- M15 event rows: `{len(all_events)}`",
        f"- Baseline rows: `{len(baselines)}`",
        f"- Flag summary rows: `{len(flag_summary)}`",
        f"- Primitive-flagged rows: `{flagged_rows}`",
        f"- Current-day partial event rows: `{partial_rows}`",
        f"- Read error rows: `{len(read_errors)}`",
        "",
        "## Flag Families",
        "",
    ]
    for flag in sorted({row["primitive_flag"] for row in top_flags}):
        total = sum(row["flagged_bar_count"] for row in flag_summary if row["primitive_flag"] == flag)
        summary.append(f"- `{flag}`: `{total}` flagged descriptor rows")
    summary.extend([
        "",
        "## Boundary",
        "",
        "- Flags are same-symbol/session percentile descriptors, not signals.",
        "- No target outcome was attached.",
        "- Current-day partial rows are labelled and must be excluded from sealed evidence.",
        "",
    ])
    SUMMARY_PATH.write_text("\n".join(summary), encoding="utf-8")

    print(json.dumps({"ok": True, "result": str(RESULT_PATH), "event_rows": len(all_events), "read_errors": len(read_errors)}, sort_keys=True))
    return 0 if not read_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
