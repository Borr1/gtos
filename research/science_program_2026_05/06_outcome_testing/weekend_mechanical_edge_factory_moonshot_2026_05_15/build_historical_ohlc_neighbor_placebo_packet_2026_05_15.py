#!/usr/bin/env python3
"""Build neighbor and same-date/session placebo controls for OHLC route rows.

This consumes the same-context control-screen route queue. It preserves every
queued row and compares the event sample with nearby bars and deterministic
same-date/session placebo bars. It is still a discovery/control packet, not
sealed validation or strategy performance.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_historical_ohlc_primitives_2026_05_15 import (
    DATA_DIR,
    add_rolling_context,
    forward_metrics,
    read_bars,
)


ROUTE_DIR = Path(__file__).resolve().parent
EVENTS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_PRIMITIVE_EVENT_LEDGER_2026-05-15.jsonl"
CONTROL_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_CONTROL_SCREEN_LEDGER_2026-05-15.jsonl"
QUEUE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_CONTROL_SCREEN_ROUTE_QUEUE_2026-05-15.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_NEIGHBOR_PLACEBO_PACKET_RESULT_2026-05-15.json"
LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_NEIGHBOR_PLACEBO_PACKET_LEDGER_2026-05-15.jsonl"
SURVIVOR_QUEUE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_NEIGHBOR_PLACEBO_SURVIVOR_QUEUE_2026-05-15.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_NEIGHBOR_PLACEBO_PACKET_SUMMARY_2026-05-15.md"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Neighbor/placebo discovery control packet only. This is not sealed "
    "validation, R/PnL, expectancy, fillability, live-readiness, or a "
    "promotion verdict."
)

MIN_CONTROL_COVERAGE = 0.80


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            yield json.loads(line)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def safe_div(num: float | int | None, den: float | int | None) -> float | None:
    if den in (0, 0.0, None):
        return None
    if num is None:
        return None
    return float(num) / float(den)


def r6(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 6)


def key_for(row: dict[str, Any]) -> tuple[str, str, str, int]:
    return (row["symbol"], row["session"], row["primitive_id"], int(row["horizon_bars"]))


def load_queue() -> dict[tuple[str, str, str, int], dict[str, Any]]:
    return {key_for(row): row for row in read_jsonl(QUEUE_PATH)}


def load_control_signs() -> dict[tuple[str, str, str, int], int]:
    signs: dict[tuple[str, str, str, int], int] = {}
    for row in read_jsonl(CONTROL_LEDGER_PATH):
        key = (row["symbol"], row["session"], row["primitive_id"], int(row["horizon_bars"]))
        signs[key] = int(row["expected_sign"])
    return signs


def load_event_groups(queue_keys: set[tuple[str, str, str, int]]) -> dict[tuple[str, str, str, int], list[dict[str, Any]]]:
    groups: dict[tuple[str, str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in read_jsonl(EVENTS_PATH):
        key = (row["symbol"], row["session"], row["primitive_id"], int(row["horizon_bars"]))
        if key in queue_keys:
            groups[key].append(row)
    return groups


def deterministic_index(seed: str, length: int) -> int:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:16], 16) % length


def directional_metrics(metrics: dict[str, Any], expected_sign: int) -> dict[str, float] | None:
    if expected_sign == 0:
        return {
            "future_close": float(metrics["future_close_return_units"]),
            "abs_future_close": abs(float(metrics["future_close_return_units"])),
            "total_excursion": float(metrics["future_high_excursion_units"])
            + float(metrics["future_low_excursion_units"]),
        }
    future_close = float(metrics["future_close_return_units"])
    high = float(metrics["future_high_excursion_units"])
    low = float(metrics["future_low_excursion_units"])
    directional_close = expected_sign * future_close
    favorable = high if expected_sign > 0 else low
    adverse = low if expected_sign > 0 else high
    return {
        "directional_close": directional_close,
        "directional_positive": 1.0 if directional_close > 0 else 0.0,
        "directional_favorable": favorable,
        "directional_adverse": adverse,
        "total_excursion": high + low,
    }


def event_metrics_from_row(row: dict[str, Any], expected_sign: int) -> dict[str, float]:
    if expected_sign == 0:
        return {
            "future_close": float(row["future_close_return_units"]),
            "abs_future_close": abs(float(row["future_close_return_units"])),
            "total_excursion": float(row["future_high_excursion_units"])
            + float(row["future_low_excursion_units"]),
        }
    return {
        "directional_close": float(row["directional_close_units"]),
        "directional_positive": 1.0 if float(row["directional_close_units"]) > 0 else 0.0,
        "directional_favorable": float(row["directional_favorable_excursion_units"]),
        "directional_adverse": float(row["directional_adverse_excursion_units"]),
        "total_excursion": float(row["future_high_excursion_units"]) + float(row["future_low_excursion_units"]),
    }


def summarize_metric_rows(rows: list[dict[str, float]], expected_sign: int) -> dict[str, Any]:
    if not rows:
        return {
            "count": 0,
            "mean_directional_close": None,
            "directional_positive_share": None,
            "mean_directional_favorable": None,
            "mean_directional_adverse": None,
            "mean_total_excursion": None,
            "mean_abs_future_close": None,
        }
    total_excursion = sum(row["total_excursion"] for row in rows)
    if expected_sign == 0:
        return {
            "count": len(rows),
            "mean_directional_close": None,
            "directional_positive_share": None,
            "mean_directional_favorable": None,
            "mean_directional_adverse": None,
            "mean_total_excursion": total_excursion / len(rows),
            "mean_abs_future_close": sum(row["abs_future_close"] for row in rows) / len(rows),
        }
    return {
        "count": len(rows),
        "mean_directional_close": sum(row["directional_close"] for row in rows) / len(rows),
        "directional_positive_share": sum(row["directional_positive"] for row in rows) / len(rows),
        "mean_directional_favorable": sum(row["directional_favorable"] for row in rows) / len(rows),
        "mean_directional_adverse": sum(row["directional_adverse"] for row in rows) / len(rows),
        "mean_total_excursion": total_excursion / len(rows),
        "mean_abs_future_close": None,
    }


def load_symbol_bars(symbol: str) -> tuple[list[dict[str, Any]], dict[str, int], dict[tuple[str, str, int], list[int]]]:
    path = DATA_DIR / f"{symbol}_M15.csv"
    bars = read_bars(path)
    add_rolling_context(bars)
    time_to_index = {bar["time_utc"]: idx for idx, bar in enumerate(bars)}
    pools: dict[tuple[str, str, int], list[int]] = defaultdict(list)
    for idx, bar in enumerate(bars):
        if not bar.get("rolling_median_range"):
            continue
        for horizon in (4, 16, 32):
            if forward_metrics(bars, idx, horizon):
                pools[(bar["date"], bar["session"], horizon)].append(idx)
    return bars, time_to_index, pools


def select_permuted_index(
    pool: list[int],
    original_idx: int,
    seed: str,
) -> int | None:
    if not pool:
        return None
    if len(pool) == 1 and pool[0] == original_idx:
        return None
    start = deterministic_index(seed, len(pool))
    for offset in range(len(pool)):
        idx = pool[(start + offset) % len(pool)]
        if idx != original_idx:
            return idx
    return None


def evaluate_group(
    key: tuple[str, str, str, int],
    queue_row: dict[str, Any],
    event_rows: list[dict[str, Any]],
    expected_sign: int,
    bars_by_symbol: dict[str, tuple[list[dict[str, Any]], dict[str, int], dict[tuple[str, str, int], list[int]]]],
) -> dict[str, Any]:
    symbol, session, primitive_id, horizon = key
    if symbol not in bars_by_symbol:
        bars_by_symbol[symbol] = load_symbol_bars(symbol)
    bars, time_to_index, pools = bars_by_symbol[symbol]

    event_metric_rows: list[dict[str, float]] = []
    neighbor_minus_rows: list[dict[str, float]] = []
    neighbor_plus_rows: list[dict[str, float]] = []
    permuted_rows: list[dict[str, float]] = []
    missing = Counter()

    for event in event_rows:
        event_metric_rows.append(event_metrics_from_row(event, expected_sign))
        event_idx = time_to_index.get(event["time_utc"])
        if event_idx is None:
            missing["event_time_not_found"] += 1
            continue

        for label, offset, sink in (
            ("neighbor_minus_1", -1, neighbor_minus_rows),
            ("neighbor_plus_1", 1, neighbor_plus_rows),
        ):
            idx = event_idx + offset
            if idx < 0 or idx >= len(bars):
                missing[f"{label}_out_of_range"] += 1
                continue
            if bars[idx]["session"] != session:
                missing[f"{label}_session_mismatch"] += 1
                continue
            metrics = forward_metrics(bars, idx, horizon)
            if not metrics:
                missing[f"{label}_no_forward_metrics"] += 1
                continue
            sink.append(directional_metrics(metrics, expected_sign))

        pool_key = (event["date"], session, horizon)
        pool = pools.get(pool_key, [])
        permuted_idx = select_permuted_index(
            pool,
            event_idx,
            f"{symbol}|{session}|{primitive_id}|{horizon}|{event['time_utc']}",
        )
        if permuted_idx is None:
            missing["permuted_no_alternate_bar"] += 1
        else:
            metrics = forward_metrics(bars, permuted_idx, horizon)
            if not metrics:
                missing["permuted_no_forward_metrics"] += 1
            else:
                permuted_rows.append(directional_metrics(metrics, expected_sign))

    event_summary = summarize_metric_rows(event_metric_rows, expected_sign)
    neighbor_minus = summarize_metric_rows(neighbor_minus_rows, expected_sign)
    neighbor_plus = summarize_metric_rows(neighbor_plus_rows, expected_sign)
    permuted = summarize_metric_rows(permuted_rows, expected_sign)

    event_count = len(event_rows)
    neighbor_minus_coverage = safe_div(neighbor_minus["count"], event_count)
    neighbor_plus_coverage = safe_div(neighbor_plus["count"], event_count)
    permuted_coverage = safe_div(permuted["count"], event_count)
    enough_coverage = (
        (neighbor_minus_coverage or 0.0) >= MIN_CONTROL_COVERAGE
        and (neighbor_plus_coverage or 0.0) >= MIN_CONTROL_COVERAGE
        and (permuted_coverage or 0.0) >= MIN_CONTROL_COVERAGE
    )

    if not enough_coverage:
        status = "INSUFFICIENT_PLACEBO_COVERAGE"
    elif expected_sign == 0:
        event_value = event_summary["mean_total_excursion"]
        controls = [
            neighbor_minus["mean_total_excursion"],
            neighbor_plus["mean_total_excursion"],
            permuted["mean_total_excursion"],
        ]
        if event_value is not None and all(item is not None and event_value > item for item in controls):
            status = "DESCRIPTIVE_SURVIVES_NEIGHBOR_AND_PERMUTED_EXCURSION"
        else:
            status = "DESCRIPTIVE_FAILS_OR_MIXED_PLACEBO_EXCURSION"
    else:
        event_close = event_summary["mean_directional_close"]
        event_pos = event_summary["directional_positive_share"]
        control_close = [
            neighbor_minus["mean_directional_close"],
            neighbor_plus["mean_directional_close"],
            permuted["mean_directional_close"],
        ]
        control_pos = [
            neighbor_minus["directional_positive_share"],
            neighbor_plus["directional_positive_share"],
            permuted["directional_positive_share"],
        ]
        if (
            event_close is not None
            and event_pos is not None
            and all(item is not None and event_close > item for item in control_close)
            and all(item is not None and event_pos > item for item in control_pos)
        ):
            status = "DESCRIPTIVE_SURVIVES_NEIGHBOR_AND_PERMUTED_DIRECTIONAL"
        else:
            status = "DESCRIPTIVE_FAILS_OR_MIXED_PLACEBO_DIRECTIONAL"

    def delta(event_value: float | None, control_value: float | None) -> float | None:
        if event_value is None or control_value is None:
            return None
        return event_value - control_value

    return {
        "claim_boundary": CLAIM_BOUNDARY,
        "evidence_class": "HISTORICAL_OHLC_NEIGHBOR_PLACEBO_CONTROL_PACKET",
        "route_candidate_id": queue_row["route_candidate_id"],
        "symbol": symbol,
        "session": session,
        "primitive_family": queue_row["primitive_family"],
        "primitive_id": primitive_id,
        "horizon_bars": horizon,
        "expected_sign": expected_sign,
        "input_screen_bucket": queue_row["screen_bucket"],
        "event_count": event_count,
        "placebo_status": status,
        "control_coverage": {
            "neighbor_minus_1": r6(neighbor_minus_coverage),
            "neighbor_plus_1": r6(neighbor_plus_coverage),
            "same_date_session_permuted_time": r6(permuted_coverage),
        },
        "event": {key: r6(value) if isinstance(value, float) else value for key, value in event_summary.items()},
        "neighbor_minus_1": {key: r6(value) if isinstance(value, float) else value for key, value in neighbor_minus.items()},
        "neighbor_plus_1": {key: r6(value) if isinstance(value, float) else value for key, value in neighbor_plus.items()},
        "same_date_session_permuted_time": {
            key: r6(value) if isinstance(value, float) else value for key, value in permuted.items()
        },
        "deltas_vs_controls": {
            "directional_close_vs_neighbor_minus_1": r6(
                delta(event_summary["mean_directional_close"], neighbor_minus["mean_directional_close"])
            ),
            "directional_close_vs_neighbor_plus_1": r6(
                delta(event_summary["mean_directional_close"], neighbor_plus["mean_directional_close"])
            ),
            "directional_close_vs_permuted": r6(
                delta(event_summary["mean_directional_close"], permuted["mean_directional_close"])
            ),
            "directional_positive_share_vs_neighbor_minus_1": r6(
                delta(event_summary["directional_positive_share"], neighbor_minus["directional_positive_share"])
            ),
            "directional_positive_share_vs_neighbor_plus_1": r6(
                delta(event_summary["directional_positive_share"], neighbor_plus["directional_positive_share"])
            ),
            "directional_positive_share_vs_permuted": r6(
                delta(event_summary["directional_positive_share"], permuted["directional_positive_share"])
            ),
            "total_excursion_vs_neighbor_minus_1": r6(
                delta(event_summary["mean_total_excursion"], neighbor_minus["mean_total_excursion"])
            ),
            "total_excursion_vs_neighbor_plus_1": r6(
                delta(event_summary["mean_total_excursion"], neighbor_plus["mean_total_excursion"])
            ),
            "total_excursion_vs_permuted": r6(
                delta(event_summary["mean_total_excursion"], permuted["mean_total_excursion"])
            ),
        },
        "missing_control_counts": dict(sorted(missing.items())),
        "required_next_controls": [
            "event-cluster deduplication",
            "purged train/test or frozen forward route",
            "cost/fill model before any strategy projection",
            "cross-source replay before live use",
        ],
        "safe_flags": SAFE_FLAGS,
    }


def write_summary(result: dict[str, Any], status_counts: Counter[str]) -> None:
    lines = [
        "# Historical OHLC Neighbor/Placebo Control Packet",
        "",
        f"Generated UTC: `{result['generated_utc']}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, "
        "`outcome_review_opened=false`, `live_effect=false`",
        "",
        f"Evidence class: `{result['evidence_class']}`",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Counts",
        "",
    ]
    for key, value in result["counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Placebo Status", ""])
    for status, count in sorted(status_counts.items()):
        lines.append(f"- `{status}`: `{count}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- The survivor queue is a research queue, not a trade selector.",
            "- Same-date/session placebo controls reduce obvious timing bias but do not replace sealed validation.",
            "- No row includes spread, fillability, slippage, commission, or lifecycle truth.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    queue = load_queue()
    signs = load_control_signs()
    groups = load_event_groups(set(queue.keys()))
    bars_by_symbol: dict[str, tuple[list[dict[str, Any]], dict[str, int], dict[tuple[str, str, int], list[int]]]] = {}

    rows: list[dict[str, Any]] = []
    for key, queue_row in sorted(queue.items()):
        expected_sign = signs[key]
        rows.append(evaluate_group(key, queue_row, groups.get(key, []), expected_sign, bars_by_symbol))

    survivor_statuses = {
        "DESCRIPTIVE_SURVIVES_NEIGHBOR_AND_PERMUTED_DIRECTIONAL",
        "DESCRIPTIVE_SURVIVES_NEIGHBOR_AND_PERMUTED_EXCURSION",
    }
    survivor_rows = [row for row in rows if row["placebo_status"] in survivor_statuses]
    status_counts = Counter(row["placebo_status"] for row in rows)

    write_jsonl(LEDGER_PATH, rows)
    write_jsonl(SURVIVOR_QUEUE_PATH, survivor_rows)

    result = {
        "schema": "historical_ohlc_neighbor_placebo_packet_result_v1",
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "HISTORICAL_OHLC_NEIGHBOR_PLACEBO_CONTROL_PACKET",
        "claim_boundary": CLAIM_BOUNDARY,
        "parameters": {
            "input_route_queue_rule": "all rows from HISTORICAL_OHLC_CONTROL_SCREEN_ROUTE_QUEUE; no top-N cap",
            "neighbor_offsets_bars": [-1, 1],
            "same_date_session_permuted_time": "deterministic SHA256 alternate bar from same symbol/date/session/horizon",
            "minimum_control_coverage": MIN_CONTROL_COVERAGE,
        },
        "counts": {
            "input_route_queue_rows": len(queue),
            "event_groups_with_rows": sum(1 for key in queue if groups.get(key)),
            "placebo_packet_rows": len(rows),
            "survivor_queue_rows": len(survivor_rows),
            "symbols_loaded": len(bars_by_symbol),
        },
        "placebo_status_counts": dict(sorted(status_counts.items())),
        "required_next_controls": [
            "event-cluster deduplication",
            "purged train/test or frozen forward route",
            "cost/fill model before any strategy projection",
            "cross-source replay before live use",
        ],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result, status_counts)
    print(json.dumps({"ok": True, "counts": result["counts"], "generated_utc": generated_utc}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
