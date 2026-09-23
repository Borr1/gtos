#!/usr/bin/env python3
"""Build historical OHLC market-behavior primitive ledgers from local M15 CSVs.

Evidence class:
    Historical discovery/descriptive primitive mining only. This opens forward
    movement descriptors from local OHLC bars for hypothesis generation and
    control design. It is not sealed validation, not a strategy projection, and
    not a performance claim.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
DATA_DIR = REPO / "data" / "historical_2026"
UTC_NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

HORIZONS = [4, 16, 32]  # 1h, 4h, 8h on M15 bars
ROLLING_RANGE_WINDOW = 32
BREAKOUT_LOOKBACK = 16


def parse_float(raw: str) -> float:
    return float(raw)


def parse_time(raw: str) -> datetime:
    return datetime.strptime(raw, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def session_tag(ts: datetime) -> str:
    minutes = ts.hour * 60 + ts.minute
    if 0 <= minutes < 180:
        return "tokyo_kz"
    if 420 <= minutes < 630:
        return "london_core"
    if 780 <= minutes < 1020:
        return "ny_core"
    if 570 <= minutes < 615:
        return "lbma_am_fix_window"
    if 840 <= minutes < 885:
        return "lbma_pm_fix_window"
    return "off_kz"


def read_bars(path: Path) -> list[dict[str, Any]]:
    bars: list[dict[str, Any]] = []
    symbol = path.name.removesuffix("_M15.csv")
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        for idx, row in enumerate(reader):
            try:
                ts = parse_time(row["time"])
                open_ = parse_float(row["open"])
                high = parse_float(row["high"])
                low = parse_float(row["low"])
                close = parse_float(row["close"])
                volume = parse_float(row.get("volume") or "0")
            except (KeyError, ValueError):
                continue
            range_ = high - low
            body = abs(close - open_)
            upper_wick = high - max(open_, close)
            lower_wick = min(open_, close) - low
            direction = "up" if close > open_ else "down" if close < open_ else "flat"
            bars.append(
                {
                    "symbol": symbol,
                    "idx": idx,
                    "time": ts,
                    "time_utc": ts.isoformat().replace("+00:00", "Z"),
                    "date": ts.date().isoformat(),
                    "session": session_tag(ts),
                    "open": open_,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume,
                    "range": range_,
                    "body": body,
                    "upper_wick": upper_wick,
                    "lower_wick": lower_wick,
                    "direction": direction,
                    "clv": None if range_ <= 0 else ((close - low) / range_) * 2 - 1,
                }
            )
    return bars


def add_rolling_context(bars: list[dict[str, Any]]) -> None:
    ranges: deque[float] = deque(maxlen=ROLLING_RANGE_WINDOW)
    highs: deque[float] = deque(maxlen=BREAKOUT_LOOKBACK)
    lows: deque[float] = deque(maxlen=BREAKOUT_LOOKBACK)
    for bar in bars:
        bar["rolling_median_range"] = median(ranges) if ranges else None
        bar["prev_lookback_high"] = max(highs) if highs else None
        bar["prev_lookback_low"] = min(lows) if lows else None
        ranges.append(bar["range"])
        highs.append(bar["high"])
        lows.append(bar["low"])


def primitive_events(bar: dict[str, Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    med_range = bar.get("rolling_median_range")
    if not med_range or med_range <= 0:
        return events
    range_ratio = bar["range"] / med_range if med_range else None
    body_ratio = bar["body"] / bar["range"] if bar["range"] > 0 else 0
    upper_wick_ratio = bar["upper_wick"] / bar["range"] if bar["range"] > 0 else 0
    lower_wick_ratio = bar["lower_wick"] / bar["range"] if bar["range"] > 0 else 0
    prev_high = bar.get("prev_lookback_high")
    prev_low = bar.get("prev_lookback_low")

    def add(name: str, expected_sign: int, family: str, detail: dict[str, Any]) -> None:
        events.append(
            {
                "primitive_id": name,
                "primitive_family": family,
                "expected_sign": expected_sign,
                "detail": detail,
            }
        )

    if range_ratio is not None and range_ratio >= 1.8 and bar["direction"] == "up":
        add("RANGE_EXPANSION_UP", 1, "volatility_expansion", {"range_ratio": round(range_ratio, 6)})
    if range_ratio is not None and range_ratio >= 1.8 and bar["direction"] == "down":
        add("RANGE_EXPANSION_DOWN", -1, "volatility_expansion", {"range_ratio": round(range_ratio, 6)})
    if range_ratio is not None and range_ratio <= 0.55:
        add("RANGE_COMPRESSION", 0, "volatility_compression", {"range_ratio": round(range_ratio, 6)})

    if prev_high is not None and bar["close"] > prev_high:
        add("CLOSE_BREAKOUT_UP_16", 1, "breakout", {"prev_high": prev_high})
    if prev_low is not None and bar["close"] < prev_low:
        add("CLOSE_BREAKOUT_DOWN_16", -1, "breakout", {"prev_low": prev_low})
    if prev_high is not None and bar["high"] > prev_high and bar["close"] <= prev_high:
        add("SWEEP_HIGH_CLOSE_BACK_INSIDE_16", -1, "failed_breakout_sweep", {"prev_high": prev_high})
    if prev_low is not None and bar["low"] < prev_low and bar["close"] >= prev_low:
        add("SWEEP_LOW_CLOSE_BACK_INSIDE_16", 1, "failed_breakout_sweep", {"prev_low": prev_low})

    if upper_wick_ratio >= 0.55 and body_ratio <= 0.35:
        add("UPPER_WICK_EXHAUSTION", -1, "wick_exhaustion", {"upper_wick_ratio": round(upper_wick_ratio, 6)})
    if lower_wick_ratio >= 0.55 and body_ratio <= 0.35:
        add("LOWER_WICK_EXHAUSTION", 1, "wick_exhaustion", {"lower_wick_ratio": round(lower_wick_ratio, 6)})

    return events


def forward_metrics(bars: list[dict[str, Any]], idx: int, horizon: int) -> dict[str, Any] | None:
    if idx + horizon >= len(bars):
        return None
    bar = bars[idx]
    med_range = bar.get("rolling_median_range")
    if not med_range or med_range <= 0:
        return None
    future = bars[idx + 1 : idx + horizon + 1]
    future_close = bars[idx + horizon]["close"]
    max_high = max(item["high"] for item in future)
    min_low = min(item["low"] for item in future)
    return {
        "horizon_bars": horizon,
        "future_close_return_units": (future_close - bar["close"]) / med_range,
        "future_high_excursion_units": (max_high - bar["close"]) / med_range,
        "future_low_excursion_units": (bar["close"] - min_low) / med_range,
    }


def event_rows_for_symbol(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    bars = read_bars(path)
    add_rolling_context(bars)
    events: list[dict[str, Any]] = []
    baselines: list[dict[str, Any]] = []

    for idx, bar in enumerate(bars):
        if not bar.get("rolling_median_range"):
            continue
        med_range = float(bar["rolling_median_range"])
        range_ratio = bar["range"] / med_range if med_range > 0 else None
        for horizon in HORIZONS:
            metrics = forward_metrics(bars, idx, horizon)
            if not metrics:
                continue
            baseline = {
                "symbol": bar["symbol"],
                "time_utc": bar["time_utc"],
                "date": bar["date"],
                "session": bar["session"],
                "horizon_bars": horizon,
                "range_ratio": round(range_ratio, 6) if range_ratio is not None else None,
                **metrics,
                "evidence_class": "HISTORICAL_OHLC_DISCOVERY_BASELINE",
            }
            baselines.append(baseline)
            for primitive in primitive_events(bar):
                expected = int(primitive["expected_sign"])
                directional_close = None
                directional_favorable = None
                directional_adverse = None
                if expected > 0:
                    directional_close = metrics["future_close_return_units"]
                    directional_favorable = metrics["future_high_excursion_units"]
                    directional_adverse = metrics["future_low_excursion_units"]
                elif expected < 0:
                    directional_close = -metrics["future_close_return_units"]
                    directional_favorable = metrics["future_low_excursion_units"]
                    directional_adverse = metrics["future_high_excursion_units"]
                events.append(
                    {
                        "symbol": bar["symbol"],
                        "time_utc": bar["time_utc"],
                        "date": bar["date"],
                        "session": bar["session"],
                        "primitive_id": primitive["primitive_id"],
                        "primitive_family": primitive["primitive_family"],
                        "expected_sign": expected,
                        "horizon_bars": horizon,
                        "rolling_median_range": med_range,
                        "range_ratio": round(range_ratio, 6) if range_ratio is not None else None,
                        "body_to_range": None if bar["range"] <= 0 else round(bar["body"] / bar["range"], 6),
                        "clv": bar["clv"],
                        "detail": primitive["detail"],
                        **metrics,
                        "directional_close_units": directional_close,
                        "directional_favorable_excursion_units": directional_favorable,
                        "directional_adverse_excursion_units": directional_adverse,
                        "evidence_class": "HISTORICAL_OHLC_DISCOVERY_PRIMITIVE",
                        "claim_boundary": "Discovery movement descriptor only; not a strategy result.",
                    }
                )
    return events, baselines


def summarize(rows: list[dict[str, Any]], key_fields: list[str]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(row.get(field) for field in key_fields)].append(row)
    output: list[dict[str, Any]] = []
    for key, items in sorted(groups.items()):
        directional = [
            item.get("directional_close_units")
            for item in items
            if item.get("directional_close_units") is not None
        ]
        forward = [item["future_close_return_units"] for item in items]
        favorable = [
            item.get("directional_favorable_excursion_units")
            for item in items
            if item.get("directional_favorable_excursion_units") is not None
        ]
        adverse = [
            item.get("directional_adverse_excursion_units")
            for item in items
            if item.get("directional_adverse_excursion_units") is not None
        ]
        record = {field: value for field, value in zip(key_fields, key)}
        record.update(
            {
                "event_count": len(items),
                "unique_dates": len({item["date"] for item in items}),
                "mean_future_close_return_units": round(sum(forward) / len(forward), 6) if forward else None,
                "mean_directional_close_units": round(sum(directional) / len(directional), 6)
                if directional
                else None,
                "directional_positive_share": round(
                    sum(1 for value in directional if value > 0) / len(directional), 6
                )
                if directional
                else None,
                "mean_directional_favorable_excursion_units": round(sum(favorable) / len(favorable), 6)
                if favorable
                else None,
                "mean_directional_adverse_excursion_units": round(sum(adverse) / len(adverse), 6)
                if adverse
                else None,
                "max_single_date_share": round(
                    max(Counter(item["date"] for item in items).values()) / len(items), 6
                )
                if items
                else None,
                "evidence_class": "HISTORICAL_OHLC_DISCOVERY_SUMMARY",
                "claim_boundary": "Discovery aggregate only; requires controls and sealed retest before validation language.",
            }
        )
        output.append(record)
    return output


def summarize_baseline(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["symbol"], row["session"], row["horizon_bars"])].append(row)
    output = []
    for (symbol, session, horizon), items in sorted(groups.items()):
        forward = [item["future_close_return_units"] for item in items]
        high = [item["future_high_excursion_units"] for item in items]
        low = [item["future_low_excursion_units"] for item in items]
        output.append(
            {
                "symbol": symbol,
                "session": session,
                "horizon_bars": horizon,
                "bar_count": len(items),
                "mean_future_close_return_units": round(sum(forward) / len(forward), 6),
                "positive_close_share": round(sum(1 for value in forward if value > 0) / len(forward), 6),
                "mean_high_excursion_units": round(sum(high) / len(high), 6),
                "mean_low_excursion_units": round(sum(low) / len(low), 6),
                "evidence_class": "HISTORICAL_OHLC_DISCOVERY_BASELINE",
            }
        )
    return output


def build_hypotheses(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hypotheses = []
    families = defaultdict(list)
    for row in summary_rows:
        if row.get("event_count", 0) >= 30:
            families[row["primitive_family"]].append(row)
    for family, rows in sorted(families.items()):
        hypotheses.append(
            {
                "hypothesis_id": f"HIST-OHLC-{family.upper()}",
                "family": family,
                "evidence_class": "HISTORICAL_OHLC_DISCOVERY_HYPOTHESIS",
                "mechanical_translation": "Use the primitive's symbol/session/horizon rows as discovery candidates for a future frozen same-denominator control packet.",
                "supporting_groups": rows,
                "required_controls": [
                    "same-symbol/session generic movement baseline",
                    "neighbor-window placebo",
                    "shuffled-label control within symbol/session/time block",
                    "leave-symbol/session/date-window stress",
                    "cost/fill model before strategy projection",
                ],
                "claim_boundary": "Hypothesis only. This is not validation or performance evidence.",
            }
        )
    return hypotheses


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def main() -> int:
    csv_paths = sorted(DATA_DIR.glob("*_M15.csv"))
    all_events: list[dict[str, Any]] = []
    all_baselines: list[dict[str, Any]] = []
    source_files = []
    for path in csv_paths:
        events, baselines = event_rows_for_symbol(path)
        all_events.extend(events)
        all_baselines.extend(baselines)
        source_files.append({"path": path.as_posix(), "events": len(events), "baselines": len(baselines)})

    primitive_summary = summarize(
        all_events, ["primitive_family", "primitive_id", "symbol", "session", "horizon_bars"]
    )
    family_summary = summarize(all_events, ["primitive_family", "primitive_id", "session", "horizon_bars"])
    baseline_summary = summarize_baseline(all_baselines)
    hypotheses = build_hypotheses(family_summary)

    result = {
        "schema": "historical_ohlc_primitive_factory_result_v1",
        "generated_utc": UTC_NOW,
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "HISTORICAL_OHLC_DISCOVERY_ONLY",
        "claim_boundary": "Historical OHLC primitives are discovery descriptors and hypothesis generators only. They are not sealed validation, strategy projection, R/PnL, win-rate, expectancy, live-readiness, or promotion evidence.",
        "source_dir": DATA_DIR.as_posix(),
        "csv_files": source_files,
        "parameters": {
            "timeframe": "M15",
            "horizons_bars": HORIZONS,
            "rolling_range_window": ROLLING_RANGE_WINDOW,
            "breakout_lookback": BREAKOUT_LOOKBACK,
        },
        "counts": {
            "m15_csv_files": len(csv_paths),
            "baseline_rows": len(all_baselines),
            "primitive_event_rows": len(all_events),
            "primitive_summary_rows": len(primitive_summary),
            "family_summary_rows": len(family_summary),
            "baseline_summary_rows": len(baseline_summary),
            "hypothesis_rows": len(hypotheses),
        },
        "primitive_counts": dict(Counter(row["primitive_id"] for row in all_events).most_common()),
        "required_next_controls": [
            "freeze any candidate primitive before outcome scoring in a separate route",
            "same-symbol/session/horizon generic movement baseline",
            "neighbor-window and shuffled-label controls",
            "duplicate/event clustering and concentration",
            "purged/embargoed split for learned thresholds",
            "cost/fill model before strategy projection",
        ],
    }

    write_json(ROUTE_DIR / "HISTORICAL_OHLC_PRIMITIVE_FACTORY_RESULT_2026-05-15.json", result)
    write_jsonl(ROUTE_DIR / "HISTORICAL_OHLC_PRIMITIVE_EVENT_LEDGER_2026-05-15.jsonl", all_events)
    write_jsonl(ROUTE_DIR / "HISTORICAL_OHLC_PRIMITIVE_SUMMARY_LEDGER_2026-05-15.jsonl", primitive_summary)
    write_jsonl(ROUTE_DIR / "HISTORICAL_OHLC_PRIMITIVE_FAMILY_SUMMARY_2026-05-15.jsonl", family_summary)
    write_jsonl(ROUTE_DIR / "HISTORICAL_OHLC_BASELINE_CONTROL_LEDGER_2026-05-15.jsonl", baseline_summary)
    write_jsonl(ROUTE_DIR / "HISTORICAL_OHLC_PRIMITIVE_HYPOTHESIS_LEDGER_2026-05-15.jsonl", hypotheses)

    md_lines = [
        "# Historical OHLC Primitive Factory",
        "",
        f"Generated UTC: `{UTC_NOW}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: `HISTORICAL_OHLC_DISCOVERY_ONLY`",
        "",
        "This factory converts M15 candles into primitive movement descriptors for hypothesis generation only. It is not sealed validation or strategy performance.",
        "",
        "## Counts",
        "",
    ]
    for key, value in result["counts"].items():
        md_lines.append(f"- `{key}`: `{value}`")
    md_lines.extend(["", "## Required Next Controls", ""])
    for item in result["required_next_controls"]:
        md_lines.append(f"- {item}")
    md_lines.extend(["", "## Primitive Counts", ""])
    for key, value in result["primitive_counts"].items():
        md_lines.append(f"- `{key}`: `{value}`")
    (ROUTE_DIR / "HISTORICAL_OHLC_PRIMITIVE_FACTORY_SUMMARY_2026-05-15.md").write_text(
        "\n".join(md_lines) + "\n", encoding="utf-8"
    )

    print(json.dumps({"ok": True, "generated_utc": UTC_NOW, "counts": result["counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
