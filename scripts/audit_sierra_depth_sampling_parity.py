#!/usr/bin/env python3
"""Audit Sierra .depth versus cached Databento MBP-10 sampling parity.

Research/tooling only. This script compares sample-second coverage and
registered MBP-10 feature deltas for predeclared event windows. It does not
fetch new market data and does not touch live trading behavior.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts import analyze_orderflow_depth_mbp10_features as mbp10  # noqa: E402
from scripts import extract_sierra_depth_features as sierra  # noqa: E402
from src.research_infra.orderflow_features import parse_utc  # noqa: E402


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
REGISTERED_FEATURE_SUFFIXES = (
    "median_total_depth10",
    "median_depth10_imbalance",
    "thin_depth10_rate",
    "median_max_bid_wall",
    "median_max_ask_wall",
    "median_near_far_ratio",
    "mid_change_ticks",
    "sample_count",
)


def load_json(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_event(manifest: dict[str, Any], event_id: str) -> dict[str, Any]:
    for event in manifest.get("events") or []:
        if event.get("event_id") == event_id:
            return event
    raise ValueError(f"event_id {event_id!r} not found in manifest")


def find_databento_output_path(manifest: dict[str, Any], fetch_plan: dict[str, Any], event_id: str, futures_symbol: str) -> Path:
    group_by_id = {group["group_id"]: group for group in manifest.get("fetch_groups") or []}
    for fetch_group in fetch_plan.get("groups") or []:
        symbols = fetch_group.get("request", {}).get("symbols") or []
        if futures_symbol not in symbols:
            continue
        manifest_group = group_by_id.get(fetch_group.get("group_id"), {})
        event_ids = fetch_group.get("event_ids") or manifest_group.get("event_ids") or []
        if event_id in event_ids:
            return Path(fetch_group["output_path"])
    raise ValueError(f"No cached Databento output path for {event_id=} {futures_symbol=}")


def _second_key_from_ts(value: Any) -> int:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return int(ts.value // 1_000_000_000)


def _samples_from_df(df: pd.DataFrame) -> dict[int, dict[str, Any]]:
    if df.empty:
        return {}
    enriched = mbp10.add_ladder_columns(df)
    out: dict[int, dict[str, Any]] = {}
    for row in enriched.to_dict(orient="records"):
        second = _second_key_from_ts(row["ts_event"])
        out[second] = {
            "timestamp_utc": pd.Timestamp(row["ts_event"]).isoformat(),
            "timestamp_second": second,
            "total_depth10": _safe_float(row.get("total_depth10")),
            "depth10_imbalance": _safe_float(row.get("depth10_imbalance")),
            "near_far_ratio": _safe_float(row.get("near_far_ratio")),
            "max_bid_wall10": _safe_float(row.get("max_bid_wall")),
            "max_ask_wall10": _safe_float(row.get("max_ask_wall")),
            "mid_px": _safe_float(row.get("mid_px")),
            "spread_ticks": None,
        }
    return out


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def second_iso(second: int | None) -> str | None:
    if second is None:
        return None
    return datetime.fromtimestamp(second, tz=timezone.utc).isoformat()


def sample_coverage(left: dict[int, Any], right: dict[int, Any]) -> dict[str, Any]:
    left_keys = set(left)
    right_keys = set(right)
    common = left_keys & right_keys
    only_left = left_keys - right_keys
    only_right = right_keys - left_keys
    union_count = len(left_keys | right_keys)
    return {
        "sierra_count": len(left_keys),
        "databento_count": len(right_keys),
        "common_count": len(common),
        "sierra_only_count": len(only_left),
        "databento_only_count": len(only_right),
        "coverage_jaccard": None if union_count == 0 else len(common) / union_count,
        "first_sierra_second_utc": second_iso(min(left_keys) if left_keys else None),
        "last_sierra_second_utc": second_iso(max(left_keys) if left_keys else None),
        "first_databento_second_utc": second_iso(min(right_keys) if right_keys else None),
        "last_databento_second_utc": second_iso(max(right_keys) if right_keys else None),
        "first_sierra_only_seconds_utc": [second_iso(value) for value in sorted(only_left)[:10]],
        "first_databento_only_seconds_utc": [second_iso(value) for value in sorted(only_right)[:10]],
    }


def _ordered(samples: dict[int, dict[str, Any]], seconds: set[int] | None = None) -> list[dict[str, Any]]:
    keys = sorted(samples if seconds is None else (set(samples) & seconds))
    return [samples[key] for key in keys]


def summarize_databento_samples(
    samples: dict[int, dict[str, Any]],
    prefix: str,
    *,
    tick_size: float,
    thin_threshold: float | None = None,
    seconds: set[int] | None = None,
) -> dict[str, Any]:
    ordered = _ordered(samples, seconds)
    if not ordered:
        return {
            f"{prefix}_sample_count": 0,
            f"{prefix}_median_total_depth10": None,
            f"{prefix}_median_depth10_imbalance": None,
            f"{prefix}_thin_depth10_rate": None,
            f"{prefix}_median_max_bid_wall": None,
            f"{prefix}_median_max_ask_wall": None,
            f"{prefix}_median_near_far_ratio": None,
            f"{prefix}_mid_change_ticks": None,
        }
    total10 = [sample.get("total_depth10") for sample in ordered]
    mid = [sample.get("mid_px") for sample in ordered if sample.get("mid_px") is not None]
    mid_change = None
    if len(mid) >= 2:
        mid_change = (float(mid[-1]) - float(mid[0])) / tick_size
    thin_rate = None
    if thin_threshold is not None:
        thin_rate = sum(1 for value in total10 if _safe_float(value) is not None and float(value) <= thin_threshold) / len(total10)
    return {
        f"{prefix}_sample_count": len(ordered),
        f"{prefix}_median_total_depth10": sierra.median(total10),
        f"{prefix}_median_depth10_imbalance": sierra.median([sample.get("depth10_imbalance") for sample in ordered]),
        f"{prefix}_thin_depth10_rate": thin_rate,
        f"{prefix}_median_max_bid_wall": sierra.median([sample.get("max_bid_wall10") for sample in ordered]),
        f"{prefix}_median_max_ask_wall": sierra.median([sample.get("max_ask_wall10") for sample in ordered]),
        f"{prefix}_median_near_far_ratio": sierra.median([sample.get("near_far_ratio") for sample in ordered]),
        f"{prefix}_mid_change_ticks": mid_change,
    }


def extract_sierra_sample_maps(
    *,
    depth_path: Path,
    event: dict[str, Any],
    tick_size: float,
) -> dict[str, Any]:
    header = sierra.read_header(depth_path)
    canonical = sierra.parse_utc(event["canonical_m15_close_utc"])
    window_start = sierra.parse_utc(event["window_start_utc"])
    pre_start_us = sierra.sierra_us(window_start)
    canonical_us = sierra.sierra_us(canonical)
    event15_start_us = sierra.sierra_us(canonical - timedelta(minutes=15))
    bids: dict[float, tuple[int, int]] = {}
    asks: dict[float, tuple[int, int]] = {}
    pre60: dict[int, dict[str, Any]] = {}
    event15: dict[int, dict[str, Any]] = {}
    command_counts: Counter[str] = Counter()
    records_processed = 0
    batches_seen = 0
    for dt_us, command, flags, num_orders, price, quantity in sierra.iter_records(depth_path, header):
        if dt_us >= canonical_us:
            break
        records_processed += 1
        command_counts[sierra.COMMANDS.get(command, f"UNKNOWN_{command}")] += 1
        if command not in sierra.COMMANDS:
            continue
        sierra.apply_book_record(command, price, quantity, num_orders, bids, asks)
        if flags & sierra.END_OF_BATCH:
            batches_seen += 1
            if pre_start_us <= dt_us < canonical_us:
                sample = sierra.snapshot_features(bids, asks, timestamp_us=dt_us, tick_size=tick_size)
                second = int(sierra.sierra_datetime(dt_us).timestamp())
                sample["timestamp_second"] = second
                pre60[second] = sample
                if event15_start_us <= dt_us < canonical_us:
                    event15[second] = sample
    return {
        "pre60": pre60,
        "event15": event15,
        "header": {
            "record_count": header.record_count,
            "records_processed_until_canonical": records_processed,
            "batches_seen_until_canonical": batches_seen,
            "command_counts_until_canonical": dict(sorted(command_counts.items())),
        },
    }


def extract_databento_sample_maps(
    *,
    dbn_path: Path,
    event: dict[str, Any],
    futures_symbol: str,
) -> dict[str, dict[int, dict[str, Any]]]:
    raw = mbp10.load_databento_mbp10_sampled(dbn_path)
    symbol_df = raw[raw["symbol"] == futures_symbol].copy()
    canonical = parse_utc(event["canonical_m15_close_utc"])
    window_start = parse_utc(event["window_start_utc"])
    pre60 = mbp10.mbp1.slice_window(symbol_df, window_start, canonical)
    event15 = mbp10.mbp1.slice_window(symbol_df, canonical - pd.Timedelta(minutes=15), canonical)
    return {
        "pre60": _samples_from_df(pre60),
        "event15": _samples_from_df(event15),
    }


def feature_deltas(left: dict[str, Any], right: dict[str, Any], prefix: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for suffix in REGISTERED_FEATURE_SUFFIXES:
        field = f"{prefix}_{suffix}"
        left_value = left.get(field)
        right_value = right.get(field)
        delta = None
        if _safe_float(left_value) is not None and _safe_float(right_value) is not None:
            delta = float(left_value) - float(right_value)
        out[field] = {
            "sierra": left_value,
            "databento": right_value,
            "sierra_minus_databento": delta,
        }
    return out


def delta_summary(deltas: dict[str, Any]) -> dict[str, Any]:
    numeric = [abs(float(row["sierra_minus_databento"])) for row in deltas.values() if row.get("sierra_minus_databento") is not None]
    return {
        "nonzero_delta_count": sum(1 for value in numeric if value > 1e-9),
        "max_abs_delta": max(numeric) if numeric else None,
    }


def classify_window(all_summary: dict[str, Any], common_summary: dict[str, Any], coverage: dict[str, Any]) -> str:
    all_max = all_summary.get("max_abs_delta")
    common_max = common_summary.get("max_abs_delta")
    if all_max is not None and all_max <= 1e-9:
        return "EXACT_MATCH"
    if common_max is not None and common_max <= 1e-9 and coverage.get("common_count", 0) > 0:
        return "SAMPLING_CLOCK_ONLY_COMMON_SECONDS_EXACT"
    if (
        all_max is not None
        and common_max is not None
        and common_max < all_max * 0.25
        and coverage.get("coverage_jaccard") is not None
        and coverage["coverage_jaccard"] < 0.98
    ):
        return "SAMPLING_CLOCK_MAJOR_CONTRIBUTOR"
    return "SOURCE_OR_DEPTH_DEFINITION_DIFFERENCE_REMAINS"


def build_window_audit(
    *,
    prefix: str,
    sierra_samples: dict[int, dict[str, Any]],
    databento_samples: dict[int, dict[str, Any]],
    tick_size: float,
) -> dict[str, Any]:
    common_seconds = set(sierra_samples) & set(databento_samples)
    sierra_all_threshold = sierra.quantile([sample.get("total_depth10") for sample in _ordered(sierra_samples)], 0.2)
    db_all_threshold = sierra.quantile([sample.get("total_depth10") for sample in _ordered(databento_samples)], 0.2)
    sierra_all = sierra.summarize_samples(_ordered(sierra_samples), prefix, tick_size=tick_size, thin_threshold=sierra_all_threshold)
    db_all = summarize_databento_samples(databento_samples, prefix, tick_size=tick_size, thin_threshold=db_all_threshold)
    sierra_common = sierra.summarize_samples(
        _ordered(sierra_samples, common_seconds),
        prefix,
        tick_size=tick_size,
        thin_threshold=sierra_all_threshold,
    )
    db_common = summarize_databento_samples(
        databento_samples,
        prefix,
        tick_size=tick_size,
        thin_threshold=db_all_threshold,
        seconds=common_seconds,
    )
    all_deltas = feature_deltas(sierra_all, db_all, prefix)
    common_deltas = feature_deltas(sierra_common, db_common, prefix)
    all_delta_summary = delta_summary(all_deltas)
    common_delta_summary = delta_summary(common_deltas)
    coverage = sample_coverage(sierra_samples, databento_samples)
    return {
        "coverage": coverage,
        "thresholds": {
            "sierra_all_thin_depth10_threshold": sierra_all_threshold,
            "databento_all_thin_depth10_threshold": db_all_threshold,
        },
        "all_seconds": {
            "sierra_features": sierra_all,
            "databento_features": db_all,
            "deltas": all_deltas,
            "delta_summary": all_delta_summary,
        },
        "common_seconds": {
            "sierra_features": sierra_common,
            "databento_features": db_common,
            "deltas": common_deltas,
            "delta_summary": common_delta_summary,
        },
        "classification": classify_window(all_delta_summary, common_delta_summary, coverage),
    }


def build_event_audit(args: argparse.Namespace) -> dict[str, Any]:
    manifest = load_json(args.manifest)
    fetch_plan = load_json(args.databento_fetch_json)
    event = load_event(manifest, args.event_id)
    depth_path = Path(args.depth_path) if args.depth_path else sierra.depth_path_for_event(Path(args.depth_dir), args.source_symbol, event)
    dbn_path = find_databento_output_path(manifest, fetch_plan, args.event_id, args.futures_symbol)
    sierra_maps = extract_sierra_sample_maps(depth_path=depth_path, event=event, tick_size=args.tick_size)
    databento_maps = extract_databento_sample_maps(dbn_path=dbn_path, event=event, futures_symbol=args.futures_symbol)
    windows = {
        name: build_window_audit(
            prefix=name,
            sierra_samples=sierra_maps[name],
            databento_samples=databento_maps[name],
            tick_size=args.tick_size,
        )
        for name in ("pre60", "event15")
    }
    return {
        "schema_version": "sierra_depth_databento_sampling_parity_audit_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "research/tooling only",
        "promotion_verdict": PROMOTION_VERDICT,
        "event": {
            "event_id": args.event_id,
            "gtos_symbol": event.get("symbol"),
            "source_symbol": args.source_symbol,
            "futures_symbol": args.futures_symbol,
            "canonical_m15_close_utc": event["canonical_m15_close_utc"],
            "window_start_utc": event["window_start_utc"],
            "window_end_utc": event["window_end_utc"],
        },
        "inputs": {
            "manifest": args.manifest,
            "databento_fetch_json": args.databento_fetch_json,
            "depth_path": str(depth_path),
            "databento_dbn_path": str(dbn_path),
            "tick_size": args.tick_size,
        },
        "sierra_header": sierra_maps["header"],
        "windows": windows,
        "interpretation_boundary": "Sampling/source parity audit only; not replay validation, not OOS evidence, and not a live-filter claim.",
    }


def render_md(payload: dict[str, Any]) -> str:
    event = payload["event"]
    lines = [
        f"# Sierra Depth Sampling Parity Audit - {event['gtos_symbol']} / {event['futures_symbol']}",
        "",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`  ",
        "**Scope:** research-only; cached/local data only.",
        "",
        "## Event",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Event | `{event['event_id']}` |",
        f"| Source | `{event['source_symbol']}` |",
        f"| Futures | `{event['futures_symbol']}` |",
        f"| Canonical close | `{event['canonical_m15_close_utc']}` |",
        "",
        "## Window Audit",
        "",
        "| Window | Classification | Sierra samples | Databento samples | Common | Jaccard | All max abs delta | Common max abs delta |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, audit in payload["windows"].items():
        coverage = audit["coverage"]
        all_summary = audit["all_seconds"]["delta_summary"]
        common_summary = audit["common_seconds"]["delta_summary"]
        lines.append(
            "| {name} | `{classification}` | {sierra_count} | {databento_count} | {common_count} | {jaccard} | {all_delta} | {common_delta} |".format(
                name=name,
                classification=audit["classification"],
                sierra_count=coverage["sierra_count"],
                databento_count=coverage["databento_count"],
                common_count=coverage["common_count"],
                jaccard=_fmt(coverage["coverage_jaccard"]),
                all_delta=_fmt(all_summary["max_abs_delta"]),
                common_delta=_fmt(common_summary["max_abs_delta"]),
            )
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            payload["interpretation_boundary"],
        ]
    )
    return "\n".join(lines) + "\n"


def _fmt(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--databento-fetch-json", required=True)
    parser.add_argument("--event-id", required=True)
    parser.add_argument("--source-symbol", required=True)
    parser.add_argument("--futures-symbol", required=True)
    parser.add_argument("--tick-size", required=True, type=float)
    parser.add_argument("--depth-dir", required=True)
    parser.add_argument("--depth-path")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_event_audit(args)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    output_md.write_text(render_md(payload), encoding="utf-8")
    summary = {
        "event_id": payload["event"]["event_id"],
        "futures_symbol": payload["event"]["futures_symbol"],
        "promotion_verdict": payload["promotion_verdict"],
        "pre60_classification": payload["windows"]["pre60"]["classification"],
        "event15_classification": payload["windows"]["event15"]["classification"],
        "output_json": str(output_json),
        "output_md": str(output_md),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
