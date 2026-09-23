#!/usr/bin/env python3
"""Compute Sierra .depth ladder snapshots where prior CLEAR_BOOK exists.

The earlier event-window packet preserved command-flow proxies for every local
depth window and marked full ladder reconstruction as too expensive for the
interactive path. A full per-second median ladder pass over every prior-clear
window also exceeded the interactive runtime budget. This probe repairs the
feasible subset with a no-lookahead boundary proxy: windows with a prior
CLEAR_BOOK are sampled only during the final 60 seconds before event15 start
and the final 60 seconds before canonical close. No-prior-clear rows remain
blockers.
"""

from __future__ import annotations

import json
import math
import sys
from heapq import nlargest, nsmallest
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
sys.path.insert(0, str(REPO))

from scripts import extract_sierra_depth_features as depth  # noqa: E402


SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

COMMAND_FEATURE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_EVENT_WINDOW_FEATURE_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SNAPSHOT_PROBE_RESULT_{STAMP}.json"
LADDER_FEATURE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SNAPSHOT_FEATURE_LEDGER_{STAMP}.jsonl"
BLOCKER_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SNAPSHOT_BLOCKER_LEDGER_{STAMP}.jsonl"
FILE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SNAPSHOT_FILE_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SNAPSHOT_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SNAPSHOT_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SNAPSHOT_PROBE_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Sierra .depth ladder snapshot probe for prior-clear local windows only; "
    "no strategy validation, trade outcome, R/PnL, expectancy, live-readiness, or promotion"
)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def relative(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


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


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def compact_context(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "request_id": row.get("request_id"),
        "request_family": row.get("request_family"),
        "replay_id": row.get("replay_id"),
        "route_c_queue_id": row.get("route_c_queue_id"),
        "route_c_symbol": row.get("route_c_symbol"),
        "route_c_primitive_flag": row.get("route_c_primitive_flag"),
        "sierra_primitive_flag": row.get("sierra_primitive_flag"),
        "horizon_id": row.get("horizon_id"),
        "source_symbol": row.get("source_symbol"),
        "source_proxy_family": row.get("source_proxy_family"),
        "proxy_relation": row.get("proxy_relation"),
        "source_date": row.get("source_date"),
        "bar_start_utc": row.get("bar_start_utc"),
        "canonical_m15_close_utc": row.get("canonical_m15_close_utc"),
        "window_start_utc": row.get("window_start_utc"),
        "event15_start_utc": row.get("event15_start_utc"),
        "route_c_delta_aligned_with_future": row.get("route_c_delta_aligned_with_future"),
        "route_c_future_change_per_current_range": row.get("route_c_future_change_per_current_range"),
        "route_c_future_abs_change": row.get("route_c_future_abs_change"),
        "sierra_future_follows_delta_sign": row.get("sierra_future_follows_delta_sign"),
        "sierra_future_follows_price_sign": row.get("sierra_future_follows_price_sign"),
        "sierra_future_change_per_current_range": row.get("sierra_future_change_per_current_range"),
        "sierra_abs_future_change": row.get("sierra_abs_future_change"),
        "command_feature_bucket": row.get("feature_bucket"),
        "command_event15_imbalance_sign": row.get("event15_imbalance_sign"),
        "command_event15_bid_quantity_share": row.get("event15_depth_bid_quantity_share"),
        "command_event15_bid_minus_ask_quantity_sum": row.get("event15_depth_bid_minus_ask_quantity_sum"),
    }


def _top_qty(levels: list[tuple[float, tuple[int, int]]], n: int) -> int:
    return sum(qty for _price, (qty, _orders) in levels[:n])


def _top_orders(levels: list[tuple[float, tuple[int, int]]], n: int) -> int:
    return sum(orders for _price, (_qty, orders) in levels[:n])


def _max_wall(levels: list[tuple[float, tuple[int, int]]], n: int) -> int:
    return max((qty for _price, (qty, _orders) in levels[:n]), default=0)


def _imbalance(bid_qty: float, ask_qty: float) -> float | None:
    denom = bid_qty + ask_qty
    return None if denom <= 0 else (bid_qty - ask_qty) / denom


def fast_snapshot_features(
    bids: dict[float, tuple[int, int]],
    asks: dict[float, tuple[int, int]],
    *,
    timestamp_us: int,
    tick_size: float,
) -> dict[str, Any]:
    """Compute the same top-20 feature contract without sorting full books."""
    bid_levels = nlargest(20, bids.items(), key=lambda item: item[0])
    ask_levels = nsmallest(20, asks.items(), key=lambda item: item[0])
    best_bid = bid_levels[0][0] if bid_levels else None
    best_ask = ask_levels[0][0] if ask_levels else None
    out: dict[str, Any] = {
        "timestamp_utc": depth.iso_utc(depth.sierra_datetime(timestamp_us)),
        "timestamp_us": timestamp_us,
        "book_levels_bid": len(bids),
        "book_levels_ask": len(asks),
        "best_bid": best_bid,
        "best_ask": best_ask,
        "mid_px": None,
        "spread_ticks": None,
    }
    if best_bid is not None and best_ask is not None:
        out["mid_px"] = (best_bid + best_ask) / 2.0
        out["spread_ticks"] = (best_ask - best_bid) / tick_size
    for n in (1, 5, 10, 20):
        bid_qty = _top_qty(bid_levels, n)
        ask_qty = _top_qty(ask_levels, n)
        out[f"top_{n}_bid_qty"] = bid_qty
        out[f"top_{n}_ask_qty"] = ask_qty
        out[f"total_depth{n}"] = bid_qty + ask_qty
        out[f"depth{n}_imbalance"] = _imbalance(bid_qty, ask_qty)
    near10 = _top_qty(bid_levels, 3) + _top_qty(ask_levels, 3)
    far10 = out["total_depth10"] - near10
    out["near_far_ratio"] = None if far10 <= 0 else near10 / far10
    near20 = out["total_depth5"]
    far20 = out["total_depth20"] - out["total_depth5"]
    out["near_far_ratio20"] = None if far20 <= 0 else near20 / far20
    max_bid_wall10 = _max_wall(bid_levels, 10)
    max_ask_wall10 = _max_wall(ask_levels, 10)
    max_bid_wall20 = _max_wall(bid_levels, 20)
    max_ask_wall20 = _max_wall(ask_levels, 20)
    out["max_bid_wall10"] = max_bid_wall10
    out["max_ask_wall10"] = max_ask_wall10
    out["max_bid_wall20"] = max_bid_wall20
    out["max_ask_wall20"] = max_ask_wall20
    out["wall_concentration10"] = None if out["total_depth10"] <= 0 else max(max_bid_wall10, max_ask_wall10) / out["total_depth10"]
    out["wall_concentration20"] = None if out["total_depth20"] <= 0 else max(max_bid_wall20, max_ask_wall20) / out["total_depth20"]
    out["top_10_num_orders_bid"] = _top_orders(bid_levels, 10)
    out["top_10_num_orders_ask"] = _top_orders(ask_levels, 10)
    return out


def classify_ladder_feature(feature: dict[str, Any]) -> str:
    if feature.get("event_boundary60_sample_count") == 0:
        return "LADDER_BOUNDARY60_NO_EVENT_SAMPLES"
    depth10 = safe_float(feature.get("event_boundary60_median_total_depth10"))
    imbalance = safe_float(feature.get("event_boundary60_median_depth10_imbalance"))
    if depth10 is None:
        return "LADDER_BOUNDARY60_EVENT_DEPTH10_MISSING"
    if imbalance is None:
        return "LADDER_BOUNDARY60_EVENT_IMBALANCE_MISSING"
    if abs(imbalance) >= 0.20:
        return "LADDER_BOUNDARY60_EVENT_DEPTH10_IMBALANCED"
    return "LADDER_BOUNDARY60_EVENT_DEPTH10_BALANCED"


def build_event(row: dict[str, Any]) -> dict[str, Any]:
    pre_start = parse_dt(str(row["window_start_utc"]))
    event15_start = parse_dt(str(row["event15_start_utc"]))
    canonical = parse_dt(str(row["canonical_m15_close_utc"]))
    boundary_us = 60 * 1_000_000
    return {
        "row": row,
        "pre_start_us": depth.sierra_us(pre_start),
        "event15_start_us": depth.sierra_us(event15_start),
        "canonical_us": depth.sierra_us(canonical),
        "pre_boundary_start_us": depth.sierra_us(event15_start) - boundary_us,
        "event_boundary_start_us": depth.sierra_us(canonical) - boundary_us,
        "replay_start_record_index": int(row.get("replay_start_record_index") or 0),
        "pre_boundary_by_second": {},
        "event_boundary_by_second": {},
    }


def process_file(path: Path, rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    header = depth.read_header(path)
    events = [build_event(row) for row in rows]
    events.sort(key=lambda item: (item["pre_start_us"], item["canonical_us"], str(item["row"].get("request_id"))))
    start_record = min(event["replay_start_record_index"] for event in events)
    max_canonical = max(event["canonical_us"] for event in events)
    add_index = 0
    active: list[dict[str, Any]] = []
    bids: dict[float, tuple[int, int]] = {}
    asks: dict[float, tuple[int, int]] = {}
    command_counts: Counter[str] = Counter()
    records_processed = 0
    batches_seen = 0
    sampled_batches = 0
    first_ts_us: int | None = None
    last_ts_us: int | None = None
    for dt_us, command, flags, num_orders, price, quantity in depth.iter_records(path, header, start_record=start_record):
        if dt_us >= max_canonical:
            break
        if first_ts_us is None:
            first_ts_us = dt_us
        last_ts_us = dt_us
        records_processed += 1
        command_counts[depth.COMMANDS.get(command, f"UNKNOWN_{command}")] += 1
        if command not in depth.COMMANDS:
            continue
        depth.apply_book_record(command, price, quantity, num_orders, bids, asks)
        while add_index < len(events) and events[add_index]["pre_start_us"] <= dt_us:
            active.append(events[add_index])
            add_index += 1
        if active:
            active = [event for event in active if dt_us < event["canonical_us"]]
        if active and (flags & depth.END_OF_BATCH):
            sample_targets = [
                event for event in active
                if (
                    event["pre_boundary_start_us"] <= dt_us < event["event15_start_us"]
                    or event["event_boundary_start_us"] <= dt_us < event["canonical_us"]
                )
            ]
            if not sample_targets:
                continue
            batches_seen += 1
            sample = fast_snapshot_features(
                bids,
                asks,
                timestamp_us=dt_us,
                tick_size=float(sample_targets[0]["row"].get("tick_size") or 0.01),
            )
            sampled_batches += 1
            second = dt_us // 1_000_000
            for event in sample_targets:
                if event["pre_boundary_start_us"] <= dt_us < event["event15_start_us"]:
                    event["pre_boundary_by_second"][second] = sample
                if event["event_boundary_start_us"] <= dt_us < event["canonical_us"]:
                    event["event_boundary_by_second"][second] = sample
    feature_rows: list[dict[str, Any]] = []
    blocker_rows: list[dict[str, Any]] = []
    for event in events:
        row = event["row"]
        tick_size = float(row.get("tick_size") or 0.01)
        pre_boundary = [event["pre_boundary_by_second"][key] for key in sorted(event["pre_boundary_by_second"])]
        event_boundary = [event["event_boundary_by_second"][key] for key in sorted(event["event_boundary_by_second"])]
        pre_boundary_threshold = depth.quantile([sample.get("total_depth10") for sample in pre_boundary], 0.2)
        feature = {
            "route_id": ROUTE_ID,
            "safe_flags": SAFE_FLAGS,
            "evidence_boundary": EVIDENCE_BOUNDARY,
            **compact_context(row),
            "depth_path": str(path),
            "tick_size": tick_size,
            "ladder_sample_method": "single_pass_end_of_batch_boundary60_prior_clear_only",
            "ladder_replay_start_record_index": event["replay_start_record_index"],
            "ladder_replay_status": "LADDER_BOUNDARY60_PRIOR_CLEAR_COMPUTED",
            "pre_boundary60_thin_depth10_threshold": pre_boundary_threshold,
            "full_per_second_median_attempt_status": "TIMED_OUT_20M_INTERACTIVE_PYTHON",
        }
        feature.update(depth.summarize_samples(pre_boundary, "pre_boundary60", tick_size=tick_size))
        feature.update(
            depth.summarize_samples(
                event_boundary,
                "event_boundary60",
                tick_size=tick_size,
                thin_threshold=pre_boundary_threshold,
            )
        )
        feature["ladder_snapshot_bucket"] = classify_ladder_feature(feature)
        feature_rows.append(feature)
        if feature["ladder_snapshot_bucket"] in {
            "LADDER_BOUNDARY60_NO_EVENT_SAMPLES",
            "LADDER_BOUNDARY60_EVENT_DEPTH10_MISSING",
            "LADDER_BOUNDARY60_EVENT_IMBALANCE_MISSING",
        }:
            blocker = dict(feature)
            blocker.update(
                {
                    "blocker_type": feature["ladder_snapshot_bucket"],
                    "next_same_resource_action": "inspect event/file timestamps and replay window before interpreting ladder features",
                }
            )
            blocker_rows.append(blocker)
    file_row = {
        "route_id": ROUTE_ID,
        "safe_flags": SAFE_FLAGS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "depth_path": str(path),
        "source_symbol": rows[0].get("source_symbol"),
        "source_date": rows[0].get("source_date"),
        "input_prior_clear_rows": len(rows),
        "feature_rows": len(feature_rows),
        "blocker_rows": len(blocker_rows),
        "start_record": start_record,
        "records_processed_until_max_canonical": records_processed,
        "batches_seen_with_boundary60_targets": batches_seen,
        "sampled_batches_with_boundary60_targets": sampled_batches,
        "command_counts_processed": dict(sorted(command_counts.items())),
        "first_timestamp_utc_seen": depth.iso_utc(depth.sierra_datetime(first_ts_us)) if first_ts_us is not None else None,
        "last_timestamp_utc_seen": depth.iso_utc(depth.sierra_datetime(last_ts_us)) if last_ts_us is not None else None,
        "header_record_count": header.record_count,
        "header_size": header.header_size,
        "record_size": header.record_size,
        "file_size_bytes": header.size_bytes,
    }
    return feature_rows, blocker_rows, file_row


def build_no_prior_clear_blockers(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                **compact_context(row),
                "depth_path": row.get("depth_path"),
                "blocker_type": "LADDER_BOUNDARY60_BLOCKED_NO_PRIOR_CLEAR_BOOK_BEFORE_WINDOW",
                "ladder_replay_status": "BLOCKED_NO_PRIOR_CLEAR_BOOK_BEFORE_WINDOW",
                "command_feature_bucket": row.get("feature_bucket"),
                "next_same_resource_action": "requires earlier source history, file-start book state, or a conservative no-ladder classification; do not compute ladder levels from empty book",
            }
        )
    return out


def bucket_rows(counter: Counter[str]) -> list[dict[str, Any]]:
    return [
        {
            "route_id": ROUTE_ID,
            "ladder_snapshot_bucket": bucket,
            "row_count": count,
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        }
        for bucket, count in sorted(counter.items())
    ]


def question_rows(bucket_counts: Counter[str], counts: dict[str, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    ordinal = 0
    for bucket, count in sorted(bucket_counts.items()):
        ordinal += 1
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-LADDER-Q-{ordinal:03d}",
                "question_family": "ladder_snapshot_bucket",
                "bucket": bucket,
                "row_count": count,
                "question": f"What same-source neighbor, command-flow, or source-repair route follows for all {count} rows in {bucket}?",
                "next_same_resource_action": ladder_next_action(bucket),
                "counts_context": counts,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return rows


def ladder_next_action(bucket: str) -> str:
    if bucket == "LADDER_BOUNDARY60_EVENT_DEPTH10_IMBALANCED":
        return "join imbalance sign/magnitude to command-flow and same-source neighbor controls"
    if bucket == "LADDER_BOUNDARY60_EVENT_DEPTH10_BALANCED":
        return "use as denominator/generic-depth context for command-flow rows"
    if bucket == "LADDER_BOUNDARY60_BLOCKED_NO_PRIOR_CLEAR_BOOK_BEFORE_WINDOW":
        return "route to earlier-source capture or conservative no-ladder blocker"
    if bucket.startswith("LADDER_BOUNDARY60_NO") or bucket.endswith("MISSING"):
        return "inspect timestamp alignment and parser samples before interpretation"
    return "manual ladder bucket review required"


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_snapshot_probe_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_snapshot_probe_result", "created"),
        (LADDER_FEATURE_LEDGER, "sierra_depth_ladder_snapshot_feature_ledger", "created"),
        (BLOCKER_LEDGER, "sierra_depth_ladder_snapshot_blocker_ledger", "created"),
        (FILE_LEDGER, "sierra_depth_ladder_snapshot_file_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_ladder_snapshot_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_snapshot_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_snapshot_probe_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], bucket_counts: Counter[str]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_snapshot_probe",
        "status": "done",
        "route": "sierra_depth_ladder_reconstruction_repair",
        "details": "Computed full ladder snapshot descriptors for every local depth window with a prior CLEAR_BOOK and preserved no-prior-clear rows as blockers.",
        "counts": counts,
        "bucket_counts": dict(sorted(bucket_counts.items())),
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(LADDER_FEATURE_LEDGER),
            relative(BLOCKER_LEDGER),
            relative(FILE_LEDGER),
            relative(BUCKET_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], bucket_counts: Counter[str]) -> None:
    lines = [
        "# Sierra Depth Ladder Snapshot Probe",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: prior-clear local Sierra `.depth` boundary-window ladder reconstruction only. No strategy validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Buckets", ""])
    for bucket, count in sorted(bucket_counts.items()):
        lines.append(f"- `{bucket}`: `{count}`")
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "- Prior-clear windows now have top-of-book/top-10/top-20 boundary60 snapshot descriptors from local Sierra `.depth` records.",
            "- Full per-second median ladder reconstruction was attempted and timed out after 20 minutes; this packet is the feasible no-lookahead boundary proxy.",
            "- No-prior-clear windows remain blockers; the packet does not infer a book from an empty state.",
            "- The result is a descriptor/control packet only, not a validation or trading-system promotion.",
            "",
            "## Next Same-Resource Work",
            "",
            "- Join ladder imbalance/wall/thinness buckets back to command-flow controls and same-source neighbors.",
            "- Treat no-prior-clear rows as exact earlier-source-history requirements.",
            "- Stress the single-pass ladder method against a smaller independent parser fixture before broader reuse.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    command_rows = read_jsonl(COMMAND_FEATURE_LEDGER)
    prior_clear_rows = [
        row for row in command_rows
        if row.get("clear_book_seen_at_or_before_window_start") is True
    ]
    no_prior_clear_rows = [
        row for row in command_rows
        if row.get("clear_book_seen_at_or_before_window_start") is not True
    ]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in prior_clear_rows:
        grouped[str(row["depth_path"])].append(row)

    feature_rows: list[dict[str, Any]] = []
    blocker_rows: list[dict[str, Any]] = build_no_prior_clear_blockers(no_prior_clear_rows)
    file_rows: list[dict[str, Any]] = []
    bucket_counts: Counter[str] = Counter(
        row["blocker_type"] for row in blocker_rows
    )
    for path_str, group in sorted(grouped.items()):
        path = Path(path_str)
        try:
            features, blockers, file_row = process_file(path, group)
        except Exception as exc:  # noqa: BLE001 - preserve exact local parser/replay failure.
            file_rows.append(
                {
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "depth_path": path_str,
                    "input_prior_clear_rows": len(group),
                    "feature_rows": 0,
                    "blocker_rows": len(group),
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            for row in group:
                blocker = {
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    **compact_context(row),
                    "depth_path": path_str,
                    "blocker_type": "LADDER_SNAPSHOT_REPLAY_ERROR",
                    "ladder_replay_status": "LOCAL_DEPTH_LADDER_REPLAY_ERROR",
                    "error": f"{type(exc).__name__}: {exc}",
                    "next_same_resource_action": "inspect parser/file window and rerun after fixing ladder replay error",
                }
                blocker_rows.append(blocker)
                bucket_counts["LADDER_SNAPSHOT_REPLAY_ERROR"] += 1
            continue
        feature_rows.extend(features)
        blocker_rows.extend(blockers)
        file_rows.append(file_row)
        for feature in features:
            bucket_counts[str(feature["ladder_snapshot_bucket"])] += 1
        for blocker in blockers:
            bucket_counts[str(blocker["blocker_type"])] += 1
    counts = {
        "input_local_depth_feature_rows": len(command_rows),
        "prior_clear_input_rows": len(prior_clear_rows),
        "no_prior_clear_blocker_rows": len(no_prior_clear_rows),
        "ladder_feature_rows": len(feature_rows),
        "blocker_rows": len(blocker_rows),
        "file_rows": len(file_rows),
        "bucket_rows": len(bucket_counts),
        "question_rows": 0,
    }
    questions = question_rows(bucket_counts, counts)
    counts["question_rows"] = len(questions)
    write_jsonl(LADDER_FEATURE_LEDGER, feature_rows)
    write_jsonl(BLOCKER_LEDGER, blocker_rows)
    write_jsonl(FILE_LEDGER, file_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows(bucket_counts))
    write_jsonl(QUESTION_LEDGER, questions)
    result = {
        "schema": "sierra_depth_ladder_snapshot_probe_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_DEPTH_LADDER_BOUNDARY60_PROBE_PRIOR_CLEAR_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "ladder_snapshot_bucket_counts": dict(sorted(bucket_counts.items())),
        "next_same_resource_work": [
            "join ladder buckets to command-flow controls and same-source neighbor controls",
            "route no-prior-clear rows to earlier-source-history requirements",
            "stress boundary60 ladder replay against independent parser fixtures",
        ],
        "not_completion": "This boundary60 ladder snapshot probe repairs the feasible local subset but does not complete the 60-hour objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, bucket_counts)
    write_summary(generated_utc, counts, bucket_counts)
    print(json.dumps({"ok": True, "counts": counts, "bucket_counts": dict(bucket_counts), "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
