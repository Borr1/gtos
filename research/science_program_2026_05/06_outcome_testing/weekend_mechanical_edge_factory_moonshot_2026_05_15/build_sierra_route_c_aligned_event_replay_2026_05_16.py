#!/usr/bin/env python3
"""Replay aligned Sierra/Route C survivor joins at event level."""

from __future__ import annotations

import bisect
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

JOIN_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_PROXY_JOIN_LEDGER_{STAMP}.jsonl"
SIERRA_TARGET_EVENT_LEDGER = ROUTE_DIR / f"SIERRA_SCID_M15_TARGET_MOVEMENT_EVENT_LEDGER_{STAMP}.jsonl"
ROUTE_ROW_RECONSTRUCTION_LEDGER = ROUTE_DIR / f"TICK_M15_RESIDUAL_ROW_RECONSTRUCTION_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_ROUTE_C_ALIGNED_EVENT_REPLAY_RESULT_{STAMP}.json"
REPLAY_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_ALIGNED_EVENT_REPLAY_LEDGER_{STAMP}.jsonl"
ROUTE_EVENT_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_ALIGNED_ROUTE_EVENT_LEDGER_{STAMP}.jsonl"
SIERRA_EVENT_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_ALIGNED_SIERRA_EVENT_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_ALIGNED_EVENT_REPLAY_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_ALIGNED_EVENT_REPLAY_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_ROUTE_C_ALIGNED_EVENT_REPLAY_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Aligned Sierra/Route C event-level replay only; no strategy validation, "
    "trade outcome, R/PnL, expectancy, live-readiness, or promotion"
)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def relative(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


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


def safe_float(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if out != out or out in (float("inf"), float("-inf")):
        return None
    return out


def mean(values: list[float]) -> float | None:
    clean = [value for value in values if value is not None and value == value]
    if not clean:
        return None
    return sum(clean) / len(clean)


def share_true(values: list[bool]) -> float | None:
    if not values:
        return None
    return sum(1 for value in values if value) / len(values)


def aligned_joins() -> list[dict[str, Any]]:
    rows = []
    for row in read_jsonl(JOIN_LEDGER):
        if (
            row.get("sierra_gap_neighbor_control_bucket") == "SURVIVES_SOURCE_GAP_AND_NEIGHBOR_DESCRIPTIVE"
            and row.get("same_session") is True
            and row.get("same_horizon") is True
            and row.get("mechanism_compatible") is True
        ):
            rows.append(row)
    return rows


def join_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row["source_symbol"]),
        str(row["sierra_session_bucket"]),
        str(row["sierra_horizon_id"]),
        str(row["sierra_primitive_flag"]),
    )


def load_sierra_events(keys: set[tuple[str, str, str, str]]) -> dict[tuple[str, str, str, str], list[dict[str, Any]]]:
    by_key: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    source_symbols = {key[0] for key in keys}
    with SIERRA_TARGET_EVENT_LEDGER.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("source_symbol") not in source_symbols:
                continue
            flags = row.get("primitive_flags") or []
            if not flags:
                continue
            for flag in flags:
                key = (
                    str(row["source_symbol"]),
                    str(row["session_bucket"]),
                    str(row["horizon_id"]),
                    str(flag),
                )
                if key not in keys:
                    continue
                dt = parse_dt(str(row["bar_start_utc"]))
                by_key[key].append(
                    {
                        "source_symbol": row["source_symbol"],
                        "session_bucket": row["session_bucket"],
                        "horizon_id": row["horizon_id"],
                        "primitive_flag": flag,
                        "bar_start_utc": row["bar_start_utc"],
                        "bar_start_dt": dt,
                        "event_date": dt.date().isoformat(),
                        "event_month": f"{dt.year:04d}-{dt.month:02d}",
                        "future_change": row.get("future_change"),
                        "abs_future_change": row.get("abs_future_change"),
                        "future_change_per_current_range": row.get("future_change_per_current_range"),
                        "future_follows_delta_sign": row.get("future_follows_delta_sign"),
                        "future_follows_price_sign": row.get("future_follows_price_sign"),
                        "current_delta": row.get("current_delta"),
                        "current_price_range": row.get("current_price_range"),
                        "is_source_gap_bar": "post_source_gap_first_bar" in flags,
                        "source_audit_key": row.get("source_audit_key"),
                    }
                )
    for events in by_key.values():
        events.sort(key=lambda item: item["bar_start_dt"])
    return by_key


def load_route_events(queue_ids: set[str]) -> dict[str, list[dict[str, Any]]]:
    by_queue: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with ROUTE_ROW_RECONSTRUCTION_LEDGER.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("queue_id") not in queue_ids or row.get("is_flagged") is not True:
                continue
            dt = parse_dt(str(row["bar_open_utc"]))
            by_queue[str(row["queue_id"])].append(
                {
                    "queue_id": row["queue_id"],
                    "symbol": row["symbol"],
                    "session_bucket": row["session_bucket"],
                    "horizon_id": row["horizon_id"],
                    "primitive_flag": row["primitive_flag"],
                    "bar_open_utc": row["bar_open_utc"],
                    "bar_open_dt": dt,
                    "event_date": dt.date().isoformat(),
                    "event_month": f"{dt.year:04d}-{dt.month:02d}",
                    "future_change": row.get("future_change"),
                    "future_abs_change": row.get("future_abs_change"),
                    "future_change_per_current_range": row.get("future_change_per_current_range"),
                    "delta_aligned_with_future": row.get("delta_aligned_with_future"),
                    "delta_sign": row.get("delta_sign"),
                    "source_fields": row.get("source_fields"),
                    "row_id": row.get("row_id"),
                }
            )
    for events in by_queue.values():
        events.sort(key=lambda item: item["bar_open_dt"])
    return by_queue


def nearest_event(route_dt: datetime, sierra_events: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, float | None]:
    if not sierra_events:
        return None, None
    dts = [event["bar_start_dt"] for event in sierra_events]
    pos = bisect.bisect_left(dts, route_dt)
    candidates = []
    if pos < len(dts):
        candidates.append(sierra_events[pos])
    if pos > 0:
        candidates.append(sierra_events[pos - 1])
    best = min(candidates, key=lambda event: abs((event["bar_start_dt"] - route_dt).total_seconds()))
    minutes = abs((best["bar_start_dt"] - route_dt).total_seconds()) / 60.0
    return best, minutes


def date_hhi(events: list[dict[str, Any]], key: str) -> dict[str, Any]:
    counts = Counter(str(event[key]) for event in events)
    n = sum(counts.values())
    if n == 0:
        return {"n": 0, "unique": 0, "hhi": None, "top": None, "top_share": None}
    hhi = sum((count / n) ** 2 for count in counts.values())
    top, top_count = counts.most_common(1)[0]
    return {"n": n, "unique": len(counts), "hhi": hhi, "top": top, "top_share": top_count / n}


def event_stats(events: list[dict[str, Any]], source: str) -> dict[str, Any]:
    if source == "sierra":
        abs_key = "abs_future_change"
        aligned_delta_key = "future_follows_delta_sign"
        aligned_price_key = "future_follows_price_sign"
        range_key = "future_change_per_current_range"
    else:
        abs_key = "future_abs_change"
        aligned_delta_key = "delta_aligned_with_future"
        aligned_price_key = None
        range_key = "future_change_per_current_range"
    out = {
        "n": len(events),
        "mean_abs_future_change": mean([safe_float(event.get(abs_key)) for event in events]),
        "mean_future_change_per_current_range": mean([safe_float(event.get(range_key)) for event in events]),
        "delta_alignment_rate": share_true([bool(event.get(aligned_delta_key)) for event in events]),
        "date_concentration": date_hhi(events, "event_date"),
        "month_concentration": date_hhi(events, "event_month"),
    }
    if aligned_price_key:
        out["price_alignment_rate"] = share_true([bool(event.get(aligned_price_key)) for event in events])
    return out


def classify_replay(route_events: list[dict[str, Any]], sierra_clean_events: list[dict[str, Any]], cooccurrence: dict[str, Any]) -> str:
    if len(route_events) < 20 or len(sierra_clean_events) < 20:
        return "UNDERPOWERED_EVENT_REPLAY"
    if cooccurrence["shared_date_count"] == 0:
        return "NO_DATE_OVERLAP_FORWARD_CAPTURE_REQUIRED"
    if cooccurrence["within_15m_route_event_share"] and cooccurrence["within_15m_route_event_share"] > 0:
        return "INTRADAY_COOCCURRENCE_PRESENT_DESCRIPTIVE"
    if cooccurrence["same_date_route_event_share"] and cooccurrence["same_date_route_event_share"] > 0:
        return "DATE_LEVEL_ONLY_NO_INTRADAY_COOCCURRENCE"
    return "DATE_OVERLAP_WITHOUT_ROUTE_EVENT_MATCH"


def build_replay() -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    Counter[str],
]:
    joins = aligned_joins()
    keys = {join_key(row) for row in joins}
    queue_ids = {str(row["route_c_queue_id"]) for row in joins}
    sierra_events_by_key = load_sierra_events(keys)
    route_events_by_queue = load_route_events(queue_ids)

    replay_rows: list[dict[str, Any]] = []
    route_event_rows: list[dict[str, Any]] = []
    sierra_event_rows: list[dict[str, Any]] = []
    bucket_counts: Counter[str] = Counter()

    for index, join in enumerate(joins, 1):
        replay_id = f"SIERRA-ROUTE-C-REPLAY-{index:04d}"
        key = join_key(join)
        all_sierra_events = sierra_events_by_key.get(key, [])
        clean_sierra_events = [event for event in all_sierra_events if not event["is_source_gap_bar"]]
        route_events = route_events_by_queue.get(str(join["route_c_queue_id"]), [])
        sierra_dates = {event["event_date"] for event in clean_sierra_events}
        route_dates = {event["event_date"] for event in route_events}
        shared_dates = sorted(sierra_dates & route_dates)
        sierra_months = {event["event_month"] for event in clean_sierra_events}
        route_months = {event["event_month"] for event in route_events}
        shared_months = sorted(sierra_months & route_months)

        exact_count = 0
        within_15_count = 0
        within_60_count = 0
        same_date_count = 0
        nearest_minutes_values: list[float] = []
        route_rows_for_join: list[dict[str, Any]] = []
        for route_event in route_events:
            same_date_sierra = [event for event in clean_sierra_events if event["event_date"] == route_event["event_date"]]
            nearest, minutes = nearest_event(route_event["bar_open_dt"], same_date_sierra)
            if same_date_sierra:
                same_date_count += 1
            if minutes is not None:
                nearest_minutes_values.append(minutes)
                if minutes == 0:
                    exact_count += 1
                if minutes <= 15:
                    within_15_count += 1
                if minutes <= 60:
                    within_60_count += 1
            route_row = {
                "route_id": ROUTE_ID,
                "replay_id": replay_id,
                "route_c_queue_id": join["route_c_queue_id"],
                "route_c_symbol": route_event["symbol"],
                "route_c_bar_open_utc": route_event["bar_open_utc"],
                "route_c_future_abs_change": route_event["future_abs_change"],
                "route_c_future_change_per_current_range": route_event["future_change_per_current_range"],
                "route_c_delta_aligned_with_future": route_event["delta_aligned_with_future"],
                "nearest_clean_sierra_bar_start_utc": nearest.get("bar_start_utc") if nearest else None,
                "nearest_clean_sierra_minutes_abs": minutes,
                "has_same_date_clean_sierra_event": bool(same_date_sierra),
                "within_exact_bar": bool(minutes == 0) if minutes is not None else False,
                "within_15m": bool(minutes is not None and minutes <= 15),
                "within_60m": bool(minutes is not None and minutes <= 60),
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
            route_rows_for_join.append(route_row)
        route_event_rows.extend(route_rows_for_join)

        for event in clean_sierra_events:
            sierra_event_rows.append(
                {
                    "route_id": ROUTE_ID,
                    "replay_id": replay_id,
                    "source_symbol": event["source_symbol"],
                    "source_proxy_family": join["source_proxy_family"],
                    "sierra_bar_start_utc": event["bar_start_utc"],
                    "sierra_session_bucket": event["session_bucket"],
                    "sierra_horizon_id": event["horizon_id"],
                    "sierra_primitive_flag": event["primitive_flag"],
                    "sierra_abs_future_change": event["abs_future_change"],
                    "sierra_future_change_per_current_range": event["future_change_per_current_range"],
                    "sierra_future_follows_delta_sign": event["future_follows_delta_sign"],
                    "sierra_future_follows_price_sign": event["future_follows_price_sign"],
                    "shared_with_route_date_set": event["event_date"] in route_dates,
                    "shared_with_route_month_set": event["event_month"] in route_months,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "safe_flags": SAFE_FLAGS,
                }
            )

        route_n = len(route_events)
        cooccurrence = {
            "shared_date_count": len(shared_dates),
            "shared_dates": shared_dates,
            "shared_months": shared_months,
            "same_date_route_event_count": same_date_count,
            "exact_bar_route_event_count": exact_count,
            "within_15m_route_event_count": within_15_count,
            "within_60m_route_event_count": within_60_count,
            "same_date_route_event_share": same_date_count / route_n if route_n else None,
            "exact_bar_route_event_share": exact_count / route_n if route_n else None,
            "within_15m_route_event_share": within_15_count / route_n if route_n else None,
            "within_60m_route_event_share": within_60_count / route_n if route_n else None,
            "mean_nearest_clean_sierra_minutes_abs": mean(nearest_minutes_values),
        }
        bucket = classify_replay(route_events, clean_sierra_events, cooccurrence)
        bucket_counts[bucket] += 1
        replay_rows.append(
            {
                "route_id": ROUTE_ID,
                "replay_id": replay_id,
                "source_symbol": join["source_symbol"],
                "source_proxy_family": join["source_proxy_family"],
                "proxy_relation": join["proxy_relation"],
                "route_c_symbol": join["route_c_symbol"],
                "route_c_queue_id": join["route_c_queue_id"],
                "route_c_primitive_flag": join["route_c_primitive_flag"],
                "sierra_primitive_flag": join["sierra_primitive_flag"],
                "session_bucket": join["sierra_session_bucket"],
                "horizon_id": join["sierra_horizon_id"],
                "route_c_full_control_bucket": join["route_c_full_control_bucket"],
                "route_c_residual_transfer_class": join["route_c_residual_transfer_class"],
                "all_sierra_event_n": len(all_sierra_events),
                "clean_sierra_event_n": len(clean_sierra_events),
                "source_gap_excluded_event_n": len(all_sierra_events) - len(clean_sierra_events),
                "route_c_flagged_event_n": len(route_events),
                "sierra_event_stats": event_stats(clean_sierra_events, "sierra"),
                "route_event_stats": event_stats(route_events, "route"),
                "cooccurrence": cooccurrence,
                "event_replay_bucket": bucket,
                "next_same_resource_action": replay_next_action(bucket),
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return replay_rows, route_event_rows, sierra_event_rows, bucket_counts


def replay_next_action(bucket: str) -> str:
    if bucket == "INTRADAY_COOCCURRENCE_PRESENT_DESCRIPTIVE":
        return "build same-timestamp proxy replay controls and direction-specific source confirmation"
    if bucket == "DATE_LEVEL_ONLY_NO_INTRADAY_COOCCURRENCE":
        return "treat as day-level regime/context only and test date-shuffled controls"
    if bucket == "NO_DATE_OVERLAP_FORWARD_CAPTURE_REQUIRED":
        return "route to aligned source capture or historical overlap acquisition"
    if bucket == "UNDERPOWERED_EVENT_REPLAY":
        return "collect more events or merge only if source/mechanism rationale remains coherent"
    return "manual replay classification required"


def build_bucket_rows(bucket_counts: Counter[str]) -> list[dict[str, Any]]:
    return [
        {
            "route_id": ROUTE_ID,
            "event_replay_bucket": bucket,
            "row_count": count,
            "evidence_boundary": "event replay bucket count only; no validation or promotion",
            "safe_flags": SAFE_FLAGS,
        }
        for bucket, count in sorted(bucket_counts.items())
    ]


def build_questions(bucket_counts: Counter[str], replay_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for bucket, count in sorted(bucket_counts.items()):
        rows.append(
            {
                "route_id": ROUTE_ID,
                "event_replay_bucket": bucket,
                "question": f"What exact replay/control route follows for all {count} aligned joins in {bucket}?",
                "next_action": replay_next_action(bucket),
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    missing_overlap = [row for row in replay_rows if row["event_replay_bucket"] == "NO_DATE_OVERLAP_FORWARD_CAPTURE_REQUIRED"]
    if missing_overlap:
        rows.append(
            {
                "route_id": ROUTE_ID,
                "event_replay_bucket": "NO_DATE_OVERLAP_FORWARD_CAPTURE_REQUIRED",
                "question": "Which aligned source pairs have no overlapping dates and therefore cannot confirm intraday behavior from current rows?",
                "next_action": "Emit aligned capture/acquisition requirements for every no-overlap source pair rather than dropping them.",
                "affected_replay_rows": len(missing_overlap),
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_route_c_aligned_event_replay_builder", "created"),
        (RESULT_PATH, "sierra_route_c_aligned_event_replay_result", "created"),
        (REPLAY_LEDGER, "sierra_route_c_aligned_event_replay_ledger", "created"),
        (ROUTE_EVENT_LEDGER, "sierra_route_c_aligned_route_event_ledger", "created"),
        (SIERRA_EVENT_LEDGER, "sierra_route_c_aligned_sierra_event_ledger", "created"),
        (BUCKET_LEDGER, "sierra_route_c_aligned_event_replay_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_route_c_aligned_event_replay_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_route_c_aligned_event_replay_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], bucket_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_route_c_aligned_event_replay",
        "status": "done",
        "route": "sierra_source_contract_repair",
        "details": "Replayed every same-session/horizon/mechanism-compatible Sierra survivor and Route C residual proxy join at event level with exact/near/date cooccurrence checks.",
        "counts": counts,
        "bucket_counts": bucket_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(REPLAY_LEDGER),
            relative(ROUTE_EVENT_LEDGER),
            relative(SIERRA_EVENT_LEDGER),
            relative(BUCKET_LEDGER),
            relative(QUESTION_LEDGER),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], bucket_counts: dict[str, int]) -> None:
    lines = [
        "# Sierra to Route C Aligned Event Replay",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: event-level cooccurrence diagnostics only. No strategy validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Buckets", ""])
    for key, value in sorted(bucket_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Next Same-Resource Work",
            "",
            "- For intraday cooccurrence rows, build same-timestamp source-confirmation controls.",
            "- For date-only rows, run date-shuffled controls before treating them as regime context.",
            "- For no-overlap rows, emit capture/acquisition requirements instead of dropping the source family.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    replay_rows, route_event_rows, sierra_event_rows, bucket_counts = build_replay()
    bucket_rows = build_bucket_rows(bucket_counts)
    question_rows = build_questions(bucket_counts, replay_rows)
    write_jsonl(REPLAY_LEDGER, replay_rows)
    write_jsonl(ROUTE_EVENT_LEDGER, route_event_rows)
    write_jsonl(SIERRA_EVENT_LEDGER, sierra_event_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    counts = {
        "aligned_join_rows": len(replay_rows),
        "route_event_rows": len(route_event_rows),
        "sierra_event_rows": len(sierra_event_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
    }
    result = {
        "schema": "sierra_route_c_aligned_event_replay_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_ROUTE_C_ALIGNED_EVENT_REPLAY_DIAGNOSTIC_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "event_replay_bucket_counts": dict(sorted(bucket_counts.items())),
        "next_same_resource_work": [
            "same-timestamp proxy replay controls for intraday cooccurrence rows",
            "date-shuffled controls for date-level-only rows",
            "capture/acquisition requirement ledger for no-overlap source pairs",
        ],
        "not_completion": "This event replay deepens aligned joins but does not complete the 60-hour objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, dict(bucket_counts))
    write_summary(generated_utc, counts, dict(bucket_counts))
    print(json.dumps({"ok": True, "counts": counts, "bucket_counts": dict(bucket_counts), "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
