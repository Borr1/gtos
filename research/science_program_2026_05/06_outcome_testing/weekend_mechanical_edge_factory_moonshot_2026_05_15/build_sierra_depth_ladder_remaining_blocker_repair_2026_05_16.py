#!/usr/bin/env python3
"""Split and pursue remaining Sierra ladder blockers after CLEAR_BOOK repair.

The in-window CLEAR_BOOK packet left 51 rows:

- 43 rows had exact pre-boundary reconstruction but no END_OF_BATCH sample in
  the final event-boundary minute.
- 8 rows still had no in-window CLEAR_BOOK before canonical.

This builder does not wait for forward data. It replays the same local Sierra
depth files and samples record-level book state inside the event-boundary
minute. Rows with a prior clear can become exact record-level descriptors.
Rows without a clear remain explicitly proxy-only or blocked.
"""

from __future__ import annotations

import importlib.util
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

BASE_SCRIPT = ROUTE_DIR / "build_sierra_depth_ladder_in_window_clear_repair_2026_05_16.py"
BLOCKER_INPUT = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IN_WINDOW_CLEAR_REPAIR_BLOCKER_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_REMAINING_BLOCKER_REPAIR_RESULT_{STAMP}.json"
ROW_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_REMAINING_BLOCKER_REPAIR_ROW_LEDGER_{STAMP}.jsonl"
EXACT_FEATURE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_REMAINING_BLOCKER_REPAIR_EXACT_FEATURE_LEDGER_{STAMP}.jsonl"
PROXY_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_REMAINING_BLOCKER_REPAIR_PROXY_LEDGER_{STAMP}.jsonl"
SAMPLE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_REMAINING_BLOCKER_REPAIR_SAMPLE_LEDGER_{STAMP}.jsonl"
BLOCKER_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_REMAINING_BLOCKER_REPAIR_BLOCKER_LEDGER_{STAMP}.jsonl"
FILE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_REMAINING_BLOCKER_REPAIR_FILE_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_REMAINING_BLOCKER_REPAIR_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_REMAINING_BLOCKER_REPAIR_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_REMAINING_BLOCKER_REPAIR_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Sierra .depth remaining ladder blocker record-level repair/proxy packet; "
    "source-control and descriptor evidence only, with no strategy validation, "
    "trade outcome, R/PnL, expectancy, live-readiness, or live deployment"
)


def load_base_module() -> Any:
    spec = importlib.util.spec_from_file_location("in_window_clear_repair", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import in-window clear repair module from {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = load_base_module()
depth = BASE.depth


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


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def counter_dict(values: list[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def parse_us(value: str) -> int:
    return depth.sierra_us(BASE.parse_dt(value))


def event_from_row(row: dict[str, Any]) -> dict[str, Any]:
    canonical_us = parse_us(str(row["canonical_m15_close_utc"]))
    event_start_us = parse_us(str(row["event15_start_utc"]))
    boundary_start_us = canonical_us - 60 * 1_000_000
    first_clear_us = row.get("first_in_window_clear_us")
    return {
        "row": row,
        "request_id": str(row["request_id"]),
        "blocker_type": str(row["blocker_type"]),
        "window_start_us": parse_us(str(row["window_start_utc"])),
        "event15_start_us": event_start_us,
        "event_boundary_start_us": boundary_start_us,
        "canonical_us": canonical_us,
        "replay_start_record_index": int(row.get("ladder_replay_start_record_index") or 0),
        "first_in_window_clear_us": int(first_clear_us) if first_clear_us is not None else None,
        "first_in_window_clear_record_index": row.get("first_in_window_clear_record_index"),
        "samples": [],
        "proxy_samples": [],
        "event_boundary_record_count": 0,
        "event_boundary_end_of_batch_count": 0,
        "event_boundary_command_counts": Counter(),
        "first_event_record_us": None,
        "last_event_record_us": None,
        "discovered_clear_us": None,
        "discovered_clear_record_index": None,
    }


def summarize_event_samples(samples: list[dict[str, Any]], prefix: str, tick_size: float) -> dict[str, Any]:
    out = depth.summarize_samples(samples, prefix, tick_size=tick_size)
    out[f"{prefix}_record_count"] = len(samples)
    out[f"{prefix}_distinct_second_count"] = len({sample.get("timestamp_us", 0) // 1_000_000 for sample in samples})
    out[f"{prefix}_first_sample_utc"] = samples[0].get("timestamp_utc") if samples else None
    out[f"{prefix}_last_sample_utc"] = samples[-1].get("timestamp_utc") if samples else None
    return out


def classify_feature(summary: dict[str, Any], prefix: str) -> str:
    sample_count = int(summary.get(f"{prefix}_record_count") or 0)
    if sample_count == 0:
        return "RECORD_LEVEL_EVENT_BOUNDARY_NO_RECORDS"
    depth10 = safe_float(summary.get(f"{prefix}_median_total_depth10"))
    imbalance = safe_float(summary.get(f"{prefix}_median_depth10_imbalance"))
    if depth10 is None:
        return "RECORD_LEVEL_EVENT_BOUNDARY_DEPTH10_MISSING"
    if imbalance is None:
        return "RECORD_LEVEL_EVENT_BOUNDARY_IMBALANCE_MISSING"
    if abs(imbalance) >= 0.20:
        return "RECORD_LEVEL_EVENT_BOUNDARY_DEPTH10_IMBALANCED"
    return "RECORD_LEVEL_EVENT_BOUNDARY_DEPTH10_BALANCED"


def compact_row_context(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "request_id",
        "request_family",
        "replay_id",
        "route_c_queue_id",
        "route_c_symbol",
        "route_c_primitive_flag",
        "sierra_primitive_flag",
        "horizon_id",
        "source_symbol",
        "source_proxy_family",
        "proxy_relation",
        "source_date",
        "bar_start_utc",
        "canonical_m15_close_utc",
        "window_start_utc",
        "event15_start_utc",
        "route_c_delta_aligned_with_future",
        "route_c_future_change_per_current_range",
        "route_c_future_abs_change",
        "sierra_future_follows_delta_sign",
        "sierra_future_follows_price_sign",
        "sierra_future_change_per_current_range",
        "sierra_abs_future_change",
        "command_feature_bucket",
        "command_event15_imbalance_sign",
        "command_event15_bid_quantity_share",
        "command_event15_bid_minus_ask_quantity_sum",
        "requirement_id",
        "requirement_type",
        "requirement_status",
        "post_fallback_requirement_status",
        "requirement_recovery_bucket",
    ]
    return {key: row.get(key) for key in keys}


def status_for_event(event: dict[str, Any], feature_bucket: str | None, proxy_bucket: str | None) -> str:
    row = event["row"]
    if row.get("blocker_type") == "BLOCKED_IN_WINDOW_CLEAR_EXACT_EVENT_BOUNDARY_BUT_NO_EVENT_SAMPLES":
        if event["samples"]:
            return "REPAIRED_RECORD_LEVEL_EVENT_BOUNDARY_EXACT_AFTER_CLEAR"
        return "BLOCKED_TRUE_EVENT_BOUNDARY_NO_RECORDS_AFTER_CLEAR"
    if row.get("blocker_type") == "BLOCKED_NO_IN_WINDOW_CLEAR_BEFORE_CANONICAL":
        if event.get("discovered_clear_us") is not None and int(event["discovered_clear_us"]) <= event["event_boundary_start_us"] and event["samples"]:
            return "REPAIRED_RECORD_LEVEL_EVENT_BOUNDARY_EXACT_AFTER_DISCOVERED_CLEAR"
        if event["proxy_samples"]:
            return "PROXY_ONLY_FILE_LOCAL_NO_CLEAR_EVENT_BOUNDARY_RECORDS"
        return "BLOCKED_NO_CLEAR_AND_NO_EVENT_BOUNDARY_RECORDS"
    if feature_bucket:
        return "REPAIRED_RECORD_LEVEL_EVENT_BOUNDARY_EXACT_OTHER"
    if proxy_bucket:
        return "PROXY_ONLY_RECORD_LEVEL_OTHER"
    return "BLOCKED_UNCLASSIFIED_REMAINING_LADDER_ROW"


def build_event_output(event: dict[str, Any], path: Path) -> tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]:
    row = event["row"]
    tick_size = float(row.get("tick_size") or 0.01)
    exact_summary = summarize_event_samples(event["samples"], "record_event_boundary60", tick_size)
    proxy_summary = summarize_event_samples(event["proxy_samples"], "proxy_event_boundary60", tick_size)
    feature_bucket = classify_feature(exact_summary, "record_event_boundary60") if event["samples"] else None
    proxy_bucket = classify_feature(proxy_summary, "proxy_event_boundary60") if event["proxy_samples"] else None
    repair_status = status_for_event(event, feature_bucket, proxy_bucket)
    base = {
        "route_id": ROUTE_ID,
        "safe_flags": SAFE_FLAGS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        **compact_row_context(row),
        "depth_path": str(path),
        "tick_size": tick_size,
        "input_blocker_type": row.get("blocker_type"),
        "remaining_repair_status": repair_status,
        "record_level_feature_bucket": feature_bucket,
        "proxy_feature_bucket": proxy_bucket,
        "event_boundary_record_count": event["event_boundary_record_count"],
        "event_boundary_end_of_batch_count": event["event_boundary_end_of_batch_count"],
        "event_boundary_command_counts": dict(sorted(event["event_boundary_command_counts"].items())),
        "event_boundary_first_record_utc": depth.iso_utc(depth.sierra_datetime(event["first_event_record_us"]))
        if event.get("first_event_record_us") is not None
        else None,
        "event_boundary_last_record_utc": depth.iso_utc(depth.sierra_datetime(event["last_event_record_us"]))
        if event.get("last_event_record_us") is not None
        else None,
        "first_in_window_clear_utc": row.get("first_in_window_clear_utc"),
        "first_in_window_clear_us": event.get("first_in_window_clear_us"),
        "discovered_clear_utc": depth.iso_utc(depth.sierra_datetime(event["discovered_clear_us"]))
        if event.get("discovered_clear_us") is not None
        else None,
        "event_boundary_start_utc": depth.iso_utc(depth.sierra_datetime(event["event_boundary_start_us"])),
        "canonical_utc": row.get("canonical_m15_close_utc"),
        "next_same_resource_action": next_action_for_status(repair_status),
    }
    row_out = {**base, **exact_summary, **proxy_summary}
    feature_out = {**base, **exact_summary} if repair_status.startswith("REPAIRED_") else None
    proxy_out = {**base, **proxy_summary} if repair_status.startswith("PROXY_ONLY_") else None
    blocker_out = dict(row_out) if repair_status.startswith("BLOCKED_") else None
    return row_out, feature_out, proxy_out, blocker_out


def next_action_for_status(status: str) -> str:
    if status == "REPAIRED_RECORD_LEVEL_EVENT_BOUNDARY_EXACT_AFTER_CLEAR":
        return "join exact record-level event-boundary ladder descriptors back into Route C controls and mutation rows"
    if status == "REPAIRED_RECORD_LEVEL_EVENT_BOUNDARY_EXACT_AFTER_DISCOVERED_CLEAR":
        return "verify discovered clear against prior repair ledger, then join as exact record-level descriptor"
    if status == "PROXY_ONLY_FILE_LOCAL_NO_CLEAR_EVENT_BOUNDARY_RECORDS":
        return "use as source-quality proxy only and search earlier clear/source history before exact ladder interpretation"
    if status == "BLOCKED_TRUE_EVENT_BOUNDARY_NO_RECORDS_AFTER_CLEAR":
        return "treat as true source event-boundary silence; use neighbor/proxy controls and source-capture requirement"
    if status == "BLOCKED_NO_CLEAR_AND_NO_EVENT_BOUNDARY_RECORDS":
        return "search alternate roots/source-date files and same-source neighbors; keep exact ladder descriptor closed"
    return "manual remaining-blocker review required"


def sample_row(event: dict[str, Any], sample: dict[str, Any], sample_kind: str) -> dict[str, Any]:
    row = event["row"]
    payload = {
        "route_id": ROUTE_ID,
        "safe_flags": SAFE_FLAGS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "sample_id": f"SIERRA-LADDER-REMAINING-SAMPLE-{row.get('request_id')}-{len(event['samples']) + len(event['proxy_samples']):06d}",
        "sample_kind": sample_kind,
        "request_id": row.get("request_id"),
        "input_blocker_type": row.get("blocker_type"),
        "source_symbol": row.get("source_symbol"),
        "source_date": row.get("source_date"),
        "route_c_queue_id": row.get("route_c_queue_id"),
        "route_c_symbol": row.get("route_c_symbol"),
        "timestamp_utc": sample.get("timestamp_utc"),
        "timestamp_us": sample.get("timestamp_us"),
    }
    payload.update(sample)
    return payload


def process_file(path: Path, rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    header = depth.read_header(path)
    events = [event_from_row(row) for row in rows]
    events.sort(key=lambda event: (event["window_start_us"], event["canonical_us"], event["request_id"]))
    start_record = min(event["replay_start_record_index"] for event in events)
    max_canonical = max(event["canonical_us"] for event in events)
    add_index = 0
    active: list[dict[str, Any]] = []
    bids: dict[float, tuple[int, int]] = {}
    asks: dict[float, tuple[int, int]] = {}
    records_processed = 0
    first_ts_us: int | None = None
    last_ts_us: int | None = None
    clear_records_seen = 0
    command_counts: Counter[str] = Counter()

    for record_index, record in enumerate(depth.iter_records(path, header, start_record=start_record), start=start_record):
        dt_us, command, flags, num_orders, price, quantity = record
        if dt_us >= max_canonical:
            break
        if first_ts_us is None:
            first_ts_us = dt_us
        last_ts_us = dt_us
        records_processed += 1
        command_name = depth.COMMANDS.get(command, f"UNKNOWN_{command}")
        command_counts[command_name] += 1
        if command not in depth.COMMANDS:
            continue
        depth.apply_book_record(command, price, quantity, num_orders, bids, asks)
        if command == 1:
            clear_records_seen += 1
        while add_index < len(events) and events[add_index]["window_start_us"] <= dt_us:
            active.append(events[add_index])
            add_index += 1
        if command == 1:
            for event in active:
                if event["window_start_us"] <= dt_us < event["canonical_us"] and event.get("discovered_clear_us") is None:
                    event["discovered_clear_us"] = dt_us
                    event["discovered_clear_record_index"] = record_index
                    if event.get("first_in_window_clear_us") is None:
                        event["first_in_window_clear_us"] = dt_us
                        event["first_in_window_clear_record_index"] = record_index
        if active:
            active = [event for event in active if dt_us < event["canonical_us"]]
        boundary_events = [
            event for event in active
            if event["event_boundary_start_us"] <= dt_us < event["canonical_us"]
        ]
        if not boundary_events:
            continue
        sample = BASE.fast_snapshot_features(
            bids,
            asks,
            timestamp_us=dt_us,
            tick_size=float(boundary_events[0]["row"].get("tick_size") or 0.01),
        )
        for event in boundary_events:
            event["event_boundary_record_count"] += 1
            event["event_boundary_command_counts"][command_name] += 1
            if flags & depth.END_OF_BATCH:
                event["event_boundary_end_of_batch_count"] += 1
            if event.get("first_event_record_us") is None:
                event["first_event_record_us"] = dt_us
            event["last_event_record_us"] = dt_us
            first_clear_us = event.get("first_in_window_clear_us")
            if first_clear_us is not None and int(first_clear_us) <= event["event_boundary_start_us"]:
                event["samples"].append(sample)
            elif event["row"].get("blocker_type") == "BLOCKED_NO_IN_WINDOW_CLEAR_BEFORE_CANONICAL":
                event["proxy_samples"].append(sample)

    row_rows: list[dict[str, Any]] = []
    feature_rows: list[dict[str, Any]] = []
    proxy_rows: list[dict[str, Any]] = []
    sample_rows: list[dict[str, Any]] = []
    blocker_rows: list[dict[str, Any]] = []
    for event in events:
        row_out, feature_out, proxy_out, blocker_out = build_event_output(event, path)
        row_rows.append(row_out)
        if feature_out is not None:
            feature_rows.append(feature_out)
        if proxy_out is not None:
            proxy_rows.append(proxy_out)
        if blocker_out is not None:
            blocker_rows.append(blocker_out)
        for sample in event["samples"]:
            sample_rows.append(sample_row(event, sample, "exact_record_level_after_clear"))
        for sample in event["proxy_samples"]:
            sample_rows.append(sample_row(event, sample, "proxy_file_local_no_clear"))
    file_row = {
        "route_id": ROUTE_ID,
        "safe_flags": SAFE_FLAGS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "depth_path": str(path),
        "source_symbol": rows[0].get("source_symbol"),
        "source_date": rows[0].get("source_date"),
        "input_rows": len(rows),
        "row_rows": len(row_rows),
        "exact_feature_rows": len(feature_rows),
        "proxy_rows": len(proxy_rows),
        "sample_rows": len(sample_rows),
        "remaining_blocker_rows": len(blocker_rows),
        "remaining_repair_status_counts": dict(sorted(Counter(row["remaining_repair_status"] for row in row_rows).items())),
        "start_record": start_record,
        "records_processed_until_max_canonical": records_processed,
        "clear_records_seen_after_group_start": clear_records_seen,
        "command_counts_processed": dict(sorted(command_counts.items())),
        "first_timestamp_utc_seen": depth.iso_utc(depth.sierra_datetime(first_ts_us)) if first_ts_us is not None else None,
        "last_timestamp_utc_seen": depth.iso_utc(depth.sierra_datetime(last_ts_us)) if last_ts_us is not None else None,
        "header_record_count": header.record_count,
        "header_size": header.header_size,
        "record_size": header.record_size,
        "file_size_bytes": header.size_bytes,
    }
    return row_rows, feature_rows, proxy_rows, sample_rows, blocker_rows, file_row


def build_bucket_rows(row_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    families: list[tuple[str, list[str]]] = [
        ("remaining_repair_status", ["remaining_repair_status"]),
        ("input_blocker_type", ["input_blocker_type"]),
        ("status_by_input_blocker", ["input_blocker_type", "remaining_repair_status"]),
        ("status_by_source_symbol", ["source_symbol", "remaining_repair_status"]),
        ("status_by_route_queue", ["route_c_queue_id", "remaining_repair_status"]),
        ("status_by_command_bucket", ["command_feature_bucket", "remaining_repair_status"]),
        ("record_feature_bucket", ["record_level_feature_bucket"]),
        ("proxy_feature_bucket", ["proxy_feature_bucket"]),
    ]
    outputs: list[dict[str, Any]] = []
    for family, keys in families:
        grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in row_rows:
            grouped[tuple(row.get(key) for key in keys)].append(row)
        for values, group in sorted(grouped.items(), key=lambda item: tuple(str(value) for value in item[0])):
            outputs.append(
                {
                    "bucket_id": f"SIERRA-LADDER-REMAINING-BLOCKER-BUCKET-{len(outputs) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "bucket_family": family,
                    "bucket_values": {key: value for key, value in zip(keys, values, strict=True)},
                    "row_count": len(group),
                    "exact_feature_rows": sum(1 for row in group if str(row.get("remaining_repair_status")).startswith("REPAIRED_")),
                    "proxy_rows": sum(1 for row in group if str(row.get("remaining_repair_status")).startswith("PROXY_ONLY_")),
                    "remaining_blocker_rows": sum(1 for row in group if str(row.get("remaining_repair_status")).startswith("BLOCKED_")),
                    "mean_event_boundary_record_count": mean(
                        [float(row.get("event_boundary_record_count") or 0) for row in group]
                    ),
                    "source_symbol_counts": counter_dict([row.get("source_symbol") for row in group]),
                    "route_queue_counts": counter_dict([row.get("route_c_queue_id") for row in group]),
                }
            )
    return outputs


def build_questions(status_counts: Counter[str], counts: dict[str, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for status, count in sorted(status_counts.items()):
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-REMAINING-BLOCKER-Q-{len(rows) + 1:03d}",
                "question_family": "remaining_blocker_repair_status",
                "status": status,
                "row_count": count,
                "question": f"What same-resource join, proxy, or acquisition action follows for all {count} rows in {status}?",
                "next_same_resource_action": next_action_for_status(status),
                "counts_context": counts,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    rows.append(
        {
            "question_id": f"SIERRA-LADDER-REMAINING-BLOCKER-Q-{len(rows) + 1:03d}",
            "question_family": "mutation_join",
            "row_count": counts["row_rows"],
            "question": "How do exact record-level repairs and proxy-only no-clear diagnostics alter the 54 mutation rows?",
            "next_same_resource_action": "join this packet into all mutation rows without narrowing to previously affected queues",
            "counts_context": counts,
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        }
    )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_remaining_blocker_repair_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_remaining_blocker_repair_result", "created"),
        (ROW_LEDGER, "sierra_depth_ladder_remaining_blocker_repair_row_ledger", "created"),
        (EXACT_FEATURE_LEDGER, "sierra_depth_ladder_remaining_blocker_repair_exact_feature_ledger", "created"),
        (PROXY_LEDGER, "sierra_depth_ladder_remaining_blocker_repair_proxy_ledger", "created"),
        (SAMPLE_LEDGER, "sierra_depth_ladder_remaining_blocker_repair_sample_ledger", "created"),
        (BLOCKER_LEDGER, "sierra_depth_ladder_remaining_blocker_repair_blocker_ledger", "created"),
        (FILE_LEDGER, "sierra_depth_ladder_remaining_blocker_repair_file_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_ladder_remaining_blocker_repair_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_remaining_blocker_repair_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_remaining_blocker_repair_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {BASE.relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": BASE.relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], status_counts: Counter[str]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_remaining_blocker_repair",
        "status": "done",
        "route": "record_level_remaining_ladder_blocker_repair",
        "details": "Replayed the 51 remaining in-window-clear blockers at record level and split exact repairs, no-clear proxies, and true blockers.",
        "counts": counts,
        "remaining_repair_status_counts": dict(sorted(status_counts.items())),
        "artifacts": [
            BASE.relative(Path(__file__).resolve()),
            BASE.relative(RESULT_PATH),
            BASE.relative(ROW_LEDGER),
            BASE.relative(EXACT_FEATURE_LEDGER),
            BASE.relative(PROXY_LEDGER),
            BASE.relative(SAMPLE_LEDGER),
            BASE.relative(BLOCKER_LEDGER),
            BASE.relative(FILE_LEDGER),
            BASE.relative(BUCKET_LEDGER),
            BASE.relative(QUESTION_LEDGER),
            BASE.relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {BASE.relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], status_counts: Counter[str]) -> None:
    lines = [
        "# Sierra Depth Ladder Remaining Blocker Repair",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: record-level repair/proxy for remaining ladder blockers only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Remaining Repair Status", ""])
    for status, count in sorted(status_counts.items()):
        lines.append(f"- `{status}`: `{count}`")
    lines.extend(
        [
            "",
            "## Same-Resource Continuation",
            "",
            "- Join true no-record blocker statuses back into the active Route C ladder denominator and controls.",
            "- Keep no-clear rows proxy-only unless earlier source history or an exact clear is recovered.",
            "- Feed this blocker repair split into all `54` mutation rows and exact missing `.depth` source-date acquisition.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = BASE.utc_now()
    input_rows = read_jsonl(BLOCKER_INPUT)
    grouped: dict[Path, list[dict[str, Any]]] = defaultdict(list)
    for row in input_rows:
        grouped[Path(str(row["depth_path"]))].append(row)

    row_rows: list[dict[str, Any]] = []
    feature_rows: list[dict[str, Any]] = []
    proxy_rows: list[dict[str, Any]] = []
    sample_rows: list[dict[str, Any]] = []
    blocker_rows: list[dict[str, Any]] = []
    file_rows: list[dict[str, Any]] = []
    for path, rows in sorted(grouped.items(), key=lambda item: str(item[0])):
        out_rows, out_features, out_proxies, out_samples, out_blockers, file_row = process_file(path, rows)
        row_rows.extend(out_rows)
        feature_rows.extend(out_features)
        proxy_rows.extend(out_proxies)
        sample_rows.extend(out_samples)
        blocker_rows.extend(out_blockers)
        file_rows.append(file_row)

    bucket_rows = build_bucket_rows(row_rows)
    status_counts = Counter(str(row["remaining_repair_status"]) for row in row_rows)
    counts = {
        "input_blocker_rows": len(input_rows),
        "input_event_no_sample_rows": sum(
            1 for row in input_rows
            if row.get("blocker_type") == "BLOCKED_IN_WINDOW_CLEAR_EXACT_EVENT_BOUNDARY_BUT_NO_EVENT_SAMPLES"
        ),
        "input_no_clear_rows": sum(
            1 for row in input_rows
            if row.get("blocker_type") == "BLOCKED_NO_IN_WINDOW_CLEAR_BEFORE_CANONICAL"
        ),
        "row_rows": len(row_rows),
        "exact_feature_rows": len(feature_rows),
        "proxy_rows": len(proxy_rows),
        "sample_rows": len(sample_rows),
        "remaining_blocker_rows": len(blocker_rows),
        "file_rows": len(file_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": 0,
    }
    question_rows = build_questions(status_counts, counts)
    counts["question_rows"] = len(question_rows)

    write_jsonl(ROW_LEDGER, row_rows)
    write_jsonl(EXACT_FEATURE_LEDGER, feature_rows)
    write_jsonl(PROXY_LEDGER, proxy_rows)
    write_jsonl(SAMPLE_LEDGER, sample_rows)
    write_jsonl(BLOCKER_LEDGER, blocker_rows)
    write_jsonl(FILE_LEDGER, file_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    result = {
        "schema": "sierra_depth_ladder_remaining_blocker_repair_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_DEPTH_LADDER_REMAINING_BLOCKER_RECORD_LEVEL_REPAIR",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "remaining_repair_status_counts": dict(sorted(status_counts.items())),
        "not_completion": "This repairs/splits remaining ladder blockers but does not complete the 60-hour moonshot objective.",
        "next_same_resource_work": [
            "join true no-record blocker statuses into the active Route C ladder denominator and controls",
            "feed exact/proxy/blocker split into all current mutation rows",
            "continue exact missing .depth source-date acquisition and no-clear earlier-history search",
        ],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, status_counts)
    write_summary(generated_utc, counts, status_counts)
    print(json.dumps({"ok": True, "counts": counts, "status_counts": dict(sorted(status_counts.items()))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
