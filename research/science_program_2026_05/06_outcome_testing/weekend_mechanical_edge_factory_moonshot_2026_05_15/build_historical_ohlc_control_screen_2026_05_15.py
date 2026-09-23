#!/usr/bin/env python3
"""Build same-symbol/session/horizon controls for historical OHLC primitives.

This is a discovery control screen only. It compares each primitive group
against the generic movement baseline for the same symbol, session, and
horizon. It does not validate an edge or project strategy performance.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
EVENTS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_PRIMITIVE_EVENT_LEDGER_2026-05-15.jsonl"
BASELINE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_BASELINE_CONTROL_LEDGER_2026-05-15.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_CONTROL_SCREEN_RESULT_2026-05-15.json"
CONTROL_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_CONTROL_SCREEN_LEDGER_2026-05-15.jsonl"
BUCKET_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_CONTROL_SCREEN_BUCKET_LEDGER_2026-05-15.jsonl"
ROUTE_QUEUE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_CONTROL_SCREEN_ROUTE_QUEUE_2026-05-15.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_CONTROL_SCREEN_SUMMARY_2026-05-15.md"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Same-symbol/session/horizon control screen only. This is not sealed "
    "validation, strategy performance, expectancy, live-readiness, or a "
    "promotion verdict."
)

MIN_EVENTS = 100
MIN_DATES = 20
MAX_SINGLE_DATE_SHARE = 0.20


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


def load_baselines() -> dict[tuple[str, str, int], dict[str, Any]]:
    baselines: dict[tuple[str, str, int], dict[str, Any]] = {}
    for row in read_jsonl(BASELINE_PATH):
        key = (row["symbol"], row["session"], int(row["horizon_bars"]))
        baselines[key] = row
    return baselines


def aggregate_events() -> dict[tuple[str, str, str, str, int, int], dict[str, Any]]:
    groups: dict[tuple[str, str, str, str, int, int], dict[str, Any]] = {}

    def init(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "symbol": row["symbol"],
            "session": row["session"],
            "primitive_family": row["primitive_family"],
            "primitive_id": row["primitive_id"],
            "horizon_bars": int(row["horizon_bars"]),
            "expected_sign": int(row.get("expected_sign") or 0),
            "event_count": 0,
            "sum_future_close": 0.0,
            "sum_abs_future_close": 0.0,
            "sum_high_excursion": 0.0,
            "sum_low_excursion": 0.0,
            "positive_close_count": 0,
            "sum_directional_close": 0.0,
            "sum_directional_favorable": 0.0,
            "sum_directional_adverse": 0.0,
            "directional_positive_count": 0,
            "directional_count": 0,
            "date_counts": Counter(),
        }

    for row in read_jsonl(EVENTS_PATH):
        key = (
            row["symbol"],
            row["session"],
            row["primitive_family"],
            row["primitive_id"],
            int(row["horizon_bars"]),
            int(row.get("expected_sign") or 0),
        )
        group = groups.get(key)
        if group is None:
            group = init(row)
            groups[key] = group

        future_close = float(row["future_close_return_units"])
        high_excursion = float(row["future_high_excursion_units"])
        low_excursion = float(row["future_low_excursion_units"])

        group["event_count"] += 1
        group["sum_future_close"] += future_close
        group["sum_abs_future_close"] += abs(future_close)
        group["sum_high_excursion"] += high_excursion
        group["sum_low_excursion"] += low_excursion
        group["positive_close_count"] += int(future_close > 0)
        group["date_counts"][row["date"]] += 1

        directional_close = row.get("directional_close_units")
        if directional_close is not None:
            directional_close = float(directional_close)
            group["sum_directional_close"] += directional_close
            group["directional_positive_count"] += int(directional_close > 0)
            group["directional_count"] += 1
        directional_fav = row.get("directional_favorable_excursion_units")
        if directional_fav is not None:
            group["sum_directional_favorable"] += float(directional_fav)
        directional_adv = row.get("directional_adverse_excursion_units")
        if directional_adv is not None:
            group["sum_directional_adverse"] += float(directional_adv)

    return groups


def controlled_row(group: dict[str, Any], baseline: dict[str, Any] | None) -> dict[str, Any]:
    n = group["event_count"]
    dates = group["date_counts"]
    unique_dates = len(dates)
    max_single_date_share = safe_div(max(dates.values()) if dates else 0, n)
    expected_sign = group["expected_sign"]

    event_mean_close = safe_div(group["sum_future_close"], n)
    event_abs_close = safe_div(group["sum_abs_future_close"], n)
    event_high = safe_div(group["sum_high_excursion"], n)
    event_low = safe_div(group["sum_low_excursion"], n)
    event_total_excursion = (event_high or 0.0) + (event_low or 0.0)
    positive_close_share = safe_div(group["positive_close_count"], n)

    directional_n = group["directional_count"]
    event_dir_close = safe_div(group["sum_directional_close"], directional_n)
    event_dir_pos_share = safe_div(group["directional_positive_count"], directional_n)
    event_dir_fav = safe_div(group["sum_directional_favorable"], directional_n)
    event_dir_adv = safe_div(group["sum_directional_adverse"], directional_n)

    baseline_bar_count = None
    baseline_mean_close = None
    baseline_dir_close = None
    baseline_dir_pos_share = None
    baseline_fav = None
    baseline_adv = None
    baseline_total_excursion = None
    delta_dir_close = None
    delta_dir_pos_share = None
    delta_fav = None
    delta_adv = None
    delta_total_excursion = None

    if baseline is not None:
        baseline_bar_count = int(baseline["bar_count"])
        baseline_mean_close = float(baseline["mean_future_close_return_units"])
        baseline_high = float(baseline["mean_high_excursion_units"])
        baseline_low = float(baseline["mean_low_excursion_units"])
        baseline_total_excursion = baseline_high + baseline_low
        delta_total_excursion = event_total_excursion - baseline_total_excursion

        if expected_sign != 0:
            baseline_dir_close = expected_sign * baseline_mean_close
            positive_share = float(baseline["positive_close_share"])
            baseline_dir_pos_share = positive_share if expected_sign > 0 else 1.0 - positive_share
            baseline_fav = baseline_high if expected_sign > 0 else baseline_low
            baseline_adv = baseline_low if expected_sign > 0 else baseline_high
            if event_dir_close is not None:
                delta_dir_close = event_dir_close - baseline_dir_close
            if event_dir_pos_share is not None:
                delta_dir_pos_share = event_dir_pos_share - baseline_dir_pos_share
            if event_dir_fav is not None:
                delta_fav = event_dir_fav - baseline_fav
            if event_dir_adv is not None:
                delta_adv = event_dir_adv - baseline_adv

    material_sample = (
        n >= MIN_EVENTS
        and unique_dates >= MIN_DATES
        and (max_single_date_share is not None and max_single_date_share <= MAX_SINGLE_DATE_SHARE)
        and baseline is not None
    )

    if baseline is None:
        bucket = "NO_BASELINE"
    elif not material_sample:
        bucket = "SMALL_OR_CONCENTRATED_SAMPLE"
    elif expected_sign == 0:
        if delta_total_excursion is not None and delta_total_excursion > 0:
            bucket = "MATERIAL_EXPANSION_AFTER_NEUTRAL_PRIMITIVE"
        elif delta_total_excursion is not None and delta_total_excursion < 0:
            bucket = "MATERIAL_CONTRACTION_AFTER_NEUTRAL_PRIMITIVE"
        else:
            bucket = "MATERIAL_NEUTRAL_NO_EXCURSION_DELTA"
    elif (delta_dir_close or 0.0) > 0 and (delta_dir_pos_share or 0.0) > 0:
        bucket = "MATERIAL_POSITIVE_DIRECTIONAL_CONTROL_DELTA"
    elif (delta_dir_close or 0.0) < 0 and (delta_dir_pos_share or 0.0) < 0:
        bucket = "MATERIAL_NEGATIVE_DIRECTIONAL_CONTROL_DELTA"
    else:
        bucket = "MATERIAL_MIXED_DIRECTIONAL_CONTROL_DELTA"

    return {
        "claim_boundary": CLAIM_BOUNDARY,
        "evidence_class": "HISTORICAL_OHLC_SAME_CONTEXT_CONTROL_SCREEN",
        "symbol": group["symbol"],
        "session": group["session"],
        "primitive_family": group["primitive_family"],
        "primitive_id": group["primitive_id"],
        "horizon_bars": group["horizon_bars"],
        "expected_sign": expected_sign,
        "event_count": n,
        "baseline_bar_count": baseline_bar_count,
        "unique_dates": unique_dates,
        "max_single_date_share": r6(max_single_date_share),
        "material_sample": material_sample,
        "screen_bucket": bucket,
        "event_positive_close_share": r6(positive_close_share),
        "event_mean_future_close_units": r6(event_mean_close),
        "event_mean_abs_future_close_units": r6(event_abs_close),
        "event_mean_high_excursion_units": r6(event_high),
        "event_mean_low_excursion_units": r6(event_low),
        "event_total_excursion_units": r6(event_total_excursion),
        "baseline_mean_future_close_units": r6(baseline_mean_close),
        "baseline_total_excursion_units": r6(baseline_total_excursion),
        "delta_total_excursion_units": r6(delta_total_excursion),
        "event_directional_count": directional_n,
        "event_directional_positive_share": r6(event_dir_pos_share),
        "event_mean_directional_close_units": r6(event_dir_close),
        "event_mean_directional_favorable_excursion_units": r6(event_dir_fav),
        "event_mean_directional_adverse_excursion_units": r6(event_dir_adv),
        "baseline_directional_positive_share": r6(baseline_dir_pos_share),
        "baseline_mean_directional_close_units": r6(baseline_dir_close),
        "baseline_directional_favorable_excursion_units": r6(baseline_fav),
        "baseline_directional_adverse_excursion_units": r6(baseline_adv),
        "delta_directional_positive_share": r6(delta_dir_pos_share),
        "delta_mean_directional_close_units": r6(delta_dir_close),
        "delta_directional_favorable_excursion_units": r6(delta_fav),
        "delta_directional_adverse_excursion_units": r6(delta_adv),
        "required_next_controls": [
            "neighbor-window placebo",
            "time-block shuffled-label control",
            "duplicate/event clustering",
            "purged/embargoed split before learned thresholds",
            "cost/fill model before strategy projection",
        ],
        "safe_flags": SAFE_FLAGS,
    }


def bucket_rows(control_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str, str, int], dict[str, Any]] = {}

    def init(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "claim_boundary": CLAIM_BOUNDARY,
            "evidence_class": "HISTORICAL_OHLC_CONTROL_SCREEN_BUCKET_SUMMARY",
            "screen_bucket": row["screen_bucket"],
            "primitive_family": row["primitive_family"],
            "session": row["session"],
            "horizon_bars": row["horizon_bars"],
            "row_count": 0,
            "total_event_count": 0,
            "symbols": set(),
            "primitive_ids": set(),
            "mean_delta_directional_close_units_sum": 0.0,
            "mean_delta_directional_close_units_count": 0,
            "mean_delta_directional_positive_share_sum": 0.0,
            "mean_delta_directional_positive_share_count": 0,
            "mean_delta_total_excursion_units_sum": 0.0,
            "mean_delta_total_excursion_units_count": 0,
        }

    for row in control_rows:
        key = (
            row["screen_bucket"],
            row["primitive_family"],
            row["session"],
            int(row["horizon_bars"]),
        )
        bucket = buckets.get(key)
        if bucket is None:
            bucket = init(row)
            buckets[key] = bucket
        bucket["row_count"] += 1
        bucket["total_event_count"] += row["event_count"]
        bucket["symbols"].add(row["symbol"])
        bucket["primitive_ids"].add(row["primitive_id"])
        if row["delta_mean_directional_close_units"] is not None:
            bucket["mean_delta_directional_close_units_sum"] += row["delta_mean_directional_close_units"]
            bucket["mean_delta_directional_close_units_count"] += 1
        if row["delta_directional_positive_share"] is not None:
            bucket["mean_delta_directional_positive_share_sum"] += row["delta_directional_positive_share"]
            bucket["mean_delta_directional_positive_share_count"] += 1
        if row["delta_total_excursion_units"] is not None:
            bucket["mean_delta_total_excursion_units_sum"] += row["delta_total_excursion_units"]
            bucket["mean_delta_total_excursion_units_count"] += 1

    rendered: list[dict[str, Any]] = []
    for bucket in buckets.values():
        dir_count = bucket.pop("mean_delta_directional_close_units_count")
        dir_pos_count = bucket.pop("mean_delta_directional_positive_share_count")
        total_count = bucket.pop("mean_delta_total_excursion_units_count")
        dir_sum = bucket.pop("mean_delta_directional_close_units_sum")
        dir_pos_sum = bucket.pop("mean_delta_directional_positive_share_sum")
        total_sum = bucket.pop("mean_delta_total_excursion_units_sum")
        bucket["symbol_count"] = len(bucket.pop("symbols"))
        bucket["primitive_ids"] = sorted(bucket.pop("primitive_ids"))
        bucket["mean_delta_directional_close_units"] = r6(safe_div(dir_sum, dir_count))
        bucket["mean_delta_directional_positive_share"] = r6(safe_div(dir_pos_sum, dir_pos_count))
        bucket["mean_delta_total_excursion_units"] = r6(safe_div(total_sum, total_count))
        bucket["safe_flags"] = SAFE_FLAGS
        rendered.append(bucket)

    rendered.sort(
        key=lambda row: (
            row["screen_bucket"],
            row["primitive_family"],
            row["session"],
            row["horizon_bars"],
        )
    )
    return rendered


def queue_rows(control_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queue_buckets = {
        "MATERIAL_POSITIVE_DIRECTIONAL_CONTROL_DELTA",
        "MATERIAL_EXPANSION_AFTER_NEUTRAL_PRIMITIVE",
    }
    rows = []
    for row in control_rows:
        if row["screen_bucket"] not in queue_buckets:
            continue
        rows.append(
            {
                "claim_boundary": CLAIM_BOUNDARY,
                "evidence_class": "HISTORICAL_OHLC_CONTROL_SCREEN_ROUTE_QUEUE",
                "route_candidate_id": (
                    f"{row['symbol']}|{row['session']}|{row['primitive_id']}|"
                    f"h{row['horizon_bars']}"
                ),
                "screen_bucket": row["screen_bucket"],
                "symbol": row["symbol"],
                "session": row["session"],
                "primitive_family": row["primitive_family"],
                "primitive_id": row["primitive_id"],
                "horizon_bars": row["horizon_bars"],
                "event_count": row["event_count"],
                "baseline_bar_count": row["baseline_bar_count"],
                "unique_dates": row["unique_dates"],
                "max_single_date_share": row["max_single_date_share"],
                "delta_mean_directional_close_units": row["delta_mean_directional_close_units"],
                "delta_directional_positive_share": row["delta_directional_positive_share"],
                "delta_total_excursion_units": row["delta_total_excursion_units"],
                "next_route": (
                    "neighbor_and_shuffle_control_packet_before_any_strategy_projection"
                ),
                "safe_flags": SAFE_FLAGS,
            }
        )
    rows.sort(
        key=lambda row: (
            row["screen_bucket"],
            row["symbol"],
            row["session"],
            row["primitive_id"],
            row["horizon_bars"],
        )
    )
    return rows


def write_summary(result: dict[str, Any], bucket_counts: Counter[str]) -> None:
    lines = [
        "# Historical OHLC Same-Context Control Screen",
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

    lines.extend(["", "## Screen Buckets", ""])
    for bucket, count in sorted(bucket_counts.items()):
        lines.append(f"- `{bucket}`: `{count}`")

    lines.extend(
        [
            "",
            "## Next Controls",
            "",
            "- route-queue rows require neighbor-window placebo and time-block shuffled-label controls",
            "- directional movement deltas are not R, PnL, expectancy, fillability, or live validation",
            "- neutral compression rows are movement-volatility descriptors only",
            "- no row may be promoted without duplicate/concentration, split, and cost/fill controls",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    baselines = load_baselines()
    groups = aggregate_events()

    control_rows: list[dict[str, Any]] = []
    for group in groups.values():
        baseline = baselines.get((group["symbol"], group["session"], group["horizon_bars"]))
        control_rows.append(controlled_row(group, baseline))
    control_rows.sort(
        key=lambda row: (
            row["symbol"],
            row["session"],
            row["primitive_family"],
            row["primitive_id"],
            row["horizon_bars"],
        )
    )

    buckets = bucket_rows(control_rows)
    queued = queue_rows(control_rows)
    bucket_counts = Counter(row["screen_bucket"] for row in control_rows)

    write_jsonl(CONTROL_LEDGER_PATH, control_rows)
    write_jsonl(BUCKET_LEDGER_PATH, buckets)
    write_jsonl(ROUTE_QUEUE_PATH, queued)

    result = {
        "schema": "historical_ohlc_control_screen_result_v1",
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "HISTORICAL_OHLC_SAME_CONTEXT_CONTROL_SCREEN",
        "claim_boundary": CLAIM_BOUNDARY,
        "parameters": {
            "min_events_for_material_bucket": MIN_EVENTS,
            "min_unique_dates_for_material_bucket": MIN_DATES,
            "max_single_date_share_for_material_bucket": MAX_SINGLE_DATE_SHARE,
            "baseline_key": "same symbol + same session + same horizon",
            "route_queue_rule": (
                "all rows in MATERIAL_POSITIVE_DIRECTIONAL_CONTROL_DELTA or "
                "MATERIAL_EXPANSION_AFTER_NEUTRAL_PRIMITIVE; no top-N cap"
            ),
        },
        "counts": {
            "baseline_rows": len(baselines),
            "event_groups": len(groups),
            "control_screen_rows": len(control_rows),
            "bucket_summary_rows": len(buckets),
            "route_queue_rows": len(queued),
        },
        "screen_bucket_counts": dict(sorted(bucket_counts.items())),
        "required_next_controls": [
            "neighbor-window placebo",
            "time-block shuffled-label control",
            "duplicate/event clustering",
            "purged/embargoed split before learned thresholds",
            "cost/fill model before strategy projection",
        ],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result, bucket_counts)
    print(json.dumps({"ok": True, "counts": result["counts"], "generated_utc": generated_utc}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
