#!/usr/bin/env python3
"""Split date-sensitive Sierra/Route C cooccurrence rows by shared date."""

from __future__ import annotations

import bisect
import json
from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

COOCCURRENCE_CONTROL_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_COOCCURRENCE_CONTROL_LEDGER_{STAMP}.jsonl"
SIERRA_TARGET_EVENT_LEDGER = ROUTE_DIR / f"SIERRA_SCID_M15_TARGET_MOVEMENT_EVENT_LEDGER_{STAMP}.jsonl"
ROUTE_ROW_RECONSTRUCTION_LEDGER = ROUTE_DIR / f"TICK_M15_RESIDUAL_ROW_RECONSTRUCTION_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_ROUTE_C_DATE_REGIME_SPLIT_RESULT_{STAMP}.json"
DATE_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_DATE_REGIME_SPLIT_DATE_LEDGER_{STAMP}.jsonl"
EVENT_PAIR_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_DATE_REGIME_EVENT_PAIR_LEDGER_{STAMP}.jsonl"
DATE_SHIFT_CONTROL_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_DATE_REGIME_SHIFT_CONTROL_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_DATE_REGIME_SPLIT_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_DATE_REGIME_SPLIT_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_ROUTE_C_DATE_REGIME_SPLIT_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Date-regime split for Sierra/Route C cooccurrence controls only; no strategy "
    "validation, trade outcome, R/PnL, expectancy, live-readiness, or promotion"
)

INTRADAY_OFFSETS_MINUTES = [minutes for minutes in range(-1425, 1426, 15) if minutes != 0]
FOCUS_BUCKET = "OBSERVED_ABOVE_INTRADAY_PLACEBOS_DATE_COMPETES"


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


def mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None and value == value]
    if not clean:
        return None
    return sum(clean) / len(clean)


def share(values: list[bool]) -> float | None:
    if not values:
        return None
    return sum(1 for value in values if value) / len(values)


def nearest_event(route_dt: datetime, sierra_events: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, float | None]:
    if not sierra_events:
        return None, None
    dts = [event["dt"] for event in sierra_events]
    pos = bisect.bisect_left(dts, route_dt)
    candidates = []
    if pos < len(dts):
        candidates.append(sierra_events[pos])
    if pos > 0:
        candidates.append(sierra_events[pos - 1])
    best = min(candidates, key=lambda event: abs((event["dt"] - route_dt).total_seconds()))
    return best, abs((best["dt"] - route_dt).total_seconds()) / 60.0


def shares(route_events: list[dict[str, Any]], sierra_dts: list[datetime]) -> dict[str, Any]:
    if not route_events:
        return {"exact_count": 0, "within_15m_count": 0, "within_60m_count": 0, "within_15m_share": None}
    sierra_sorted = sorted(sierra_dts)
    exact = 0
    within15 = 0
    within60 = 0
    for route_event in route_events:
        if not sierra_sorted:
            continue
        route_dt = route_event["dt"]
        pos = bisect.bisect_left(sierra_sorted, route_dt)
        candidates = []
        if pos < len(sierra_sorted):
            candidates.append(sierra_sorted[pos])
        if pos > 0:
            candidates.append(sierra_sorted[pos - 1])
        minutes = abs((min(candidates, key=lambda dt: abs((dt - route_dt).total_seconds())) - route_dt).total_seconds()) / 60.0
        if minutes == 0:
            exact += 1
        if minutes <= 15:
            within15 += 1
        if minutes <= 60:
            within60 += 1
    n = len(route_events)
    return {
        "exact_count": exact,
        "within_15m_count": within15,
        "within_60m_count": within60,
        "within_15m_share": within15 / n,
    }


def control_distribution(route_events: list[dict[str, Any]], sierra_events: list[dict[str, Any]], observed_share: float | None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    values: list[float] = []
    base_dts = [event["dt"] for event in sierra_events]
    for offset in INTRADAY_OFFSETS_MINUTES:
        shifted = [dt + timedelta(minutes=offset) for dt in base_dts]
        shifted_shares = shares(route_events, shifted)
        value = shifted_shares["within_15m_share"]
        if value is not None:
            values.append(float(value))
        rows.append(
            {
                "offset_minutes": offset,
                "exact_count": shifted_shares["exact_count"],
                "within_15m_count": shifted_shares["within_15m_count"],
                "within_60m_count": shifted_shares["within_60m_count"],
                "within_15m_share": value,
            }
        )
    if not values:
        dist = {
            "control_count": 0,
            "control_mean": None,
            "control_max": None,
            "tail_fraction_ge_observed": None,
            "observed_minus_control_max": None,
        }
    else:
        control_max = max(values)
        dist = {
            "control_count": len(values),
            "control_mean": sum(values) / len(values),
            "control_max": control_max,
            "tail_fraction_ge_observed": (
                sum(1 for value in values if observed_share is not None and value >= observed_share) / len(values)
                if observed_share is not None
                else None
            ),
            "observed_minus_control_max": observed_share - control_max if observed_share is not None else None,
        }
    return dist, rows


def focus_rows() -> list[dict[str, Any]]:
    return [row for row in read_jsonl(COOCCURRENCE_CONTROL_LEDGER) if row.get("cooccurrence_control_bucket") == FOCUS_BUCKET]


def load_sierra_events(focus: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    keys = {
        (
            str(row["replay_id"]),
            str(row["source_symbol"]),
            str(row["sierra_primitive_flag"]),
        )
        for row in focus
    }
    source_symbols = {key[1] for key in keys}
    by_replay: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with SIERRA_TARGET_EVENT_LEDGER.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("source_symbol") not in source_symbols:
                continue
            flags = row.get("primitive_flags") or []
            if "post_source_gap_first_bar" in flags:
                continue
            for replay_id, source_symbol, primitive_flag in keys:
                if row.get("source_symbol") != source_symbol or primitive_flag not in flags:
                    continue
                dt = parse_dt(str(row["bar_start_utc"]))
                by_replay[replay_id].append(
                    {
                        "dt": dt,
                        "bar_start_utc": row["bar_start_utc"],
                        "event_date": dt.date().isoformat(),
                        "future_change": row.get("future_change"),
                        "future_sign": row.get("future_sign"),
                        "abs_future_change": row.get("abs_future_change"),
                        "future_change_per_current_range": row.get("future_change_per_current_range"),
                        "future_follows_delta_sign": row.get("future_follows_delta_sign"),
                        "future_follows_price_sign": row.get("future_follows_price_sign"),
                        "delta_sign": row.get("delta_sign"),
                        "price_sign": row.get("price_sign"),
                    }
                )
    for rows in by_replay.values():
        rows.sort(key=lambda item: item["dt"])
    return by_replay


def load_route_events(focus: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    queue_to_replay = {str(row["route_c_queue_id"]): str(row["replay_id"]) for row in focus}
    by_replay: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with ROUTE_ROW_RECONSTRUCTION_LEDGER.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            replay_id = queue_to_replay.get(str(row.get("queue_id")))
            if replay_id is None or row.get("is_flagged") is not True:
                continue
            dt = parse_dt(str(row["bar_open_utc"]))
            by_replay[replay_id].append(
                {
                    "dt": dt,
                    "bar_open_utc": row["bar_open_utc"],
                    "event_date": dt.date().isoformat(),
                    "future_change": row.get("future_change"),
                    "future_sign": row.get("future_sign"),
                    "future_abs_change": row.get("future_abs_change"),
                    "future_change_per_current_range": row.get("future_change_per_current_range"),
                    "delta_aligned_with_future": row.get("delta_aligned_with_future"),
                    "delta_sign": row.get("delta_sign"),
                    "row_id": row.get("row_id"),
                    "source_fields": row.get("source_fields"),
                }
            )
    for rows in by_replay.values():
        rows.sort(key=lambda item: item["dt"])
    return by_replay


def classify_date(route_events: list[dict[str, Any]], sierra_events: list[dict[str, Any]], observed: dict[str, Any], dist: dict[str, Any]) -> str:
    if not route_events and sierra_events:
        return "DATE_HAS_SIERRA_ONLY"
    if route_events and not sierra_events:
        return "DATE_HAS_ROUTE_ONLY"
    if not route_events and not sierra_events:
        return "EMPTY_DATE"
    observed_share = observed.get("within_15m_share")
    if observed_share is None or observed_share == 0:
        return "DATE_SHARED_NO_INTRADAY_COOCCURRENCE"
    control_max = dist.get("control_max")
    if control_max is not None and observed_share > control_max:
        return "DATE_OBSERVED_ABOVE_INTRADAY_OFFSETS"
    return "DATE_INTRADAY_PLACEBO_COMPETES"


def build_split() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], Counter[str]]:
    focus = focus_rows()
    sierra_by_replay = load_sierra_events(focus)
    route_by_replay = load_route_events(focus)
    date_rows: list[dict[str, Any]] = []
    pair_rows: list[dict[str, Any]] = []
    shift_rows: list[dict[str, Any]] = []
    bucket_counts: Counter[str] = Counter()

    for row in focus:
        replay_id = str(row["replay_id"])
        route_events = route_by_replay.get(replay_id, [])
        sierra_events = sierra_by_replay.get(replay_id, [])
        all_dates = sorted({event["dt"].date() for event in route_events} | {event["dt"].date() for event in sierra_events})
        for day in all_dates:
            route_on_day = [event for event in route_events if event["dt"].date() == day]
            sierra_on_day = [event for event in sierra_events if event["dt"].date() == day]
            observed = shares(route_on_day, [event["dt"] for event in sierra_on_day])
            dist, controls = control_distribution(route_on_day, sierra_on_day, observed.get("within_15m_share"))
            bucket = classify_date(route_on_day, sierra_on_day, observed, dist)
            bucket_counts[bucket] += 1
            date_row_id = f"{replay_id}|{day.isoformat()}"
            date_rows.append(
                {
                    "route_id": ROUTE_ID,
                    "date_row_id": date_row_id,
                    "replay_id": replay_id,
                    "event_date": day.isoformat(),
                    "source_symbol": row["source_symbol"],
                    "route_c_symbol": row["route_c_symbol"],
                    "source_proxy_family": row["source_proxy_family"],
                    "sierra_primitive_flag": row["sierra_primitive_flag"],
                    "route_c_primitive_flag": row["route_c_primitive_flag"],
                    "route_event_n": len(route_on_day),
                    "sierra_event_n": len(sierra_on_day),
                    "observed_cooccurrence": observed,
                    "intraday_shift_within15_distribution": dist,
                    "route_mean_future_change": mean([safe_float(event.get("future_change")) for event in route_on_day]),
                    "route_mean_abs_future_change": mean([safe_float(event.get("future_abs_change")) for event in route_on_day]),
                    "route_delta_alignment_rate": share([bool(event.get("delta_aligned_with_future")) for event in route_on_day]),
                    "sierra_mean_future_change": mean([safe_float(event.get("future_change")) for event in sierra_on_day]),
                    "sierra_mean_abs_future_change": mean([safe_float(event.get("abs_future_change")) for event in sierra_on_day]),
                    "sierra_delta_alignment_rate": share([bool(event.get("future_follows_delta_sign")) for event in sierra_on_day]),
                    "date_regime_bucket": bucket,
                    "next_same_resource_action": date_next_action(bucket),
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "safe_flags": SAFE_FLAGS,
                }
            )
            for control in controls:
                shift_rows.append(
                    {
                        "route_id": ROUTE_ID,
                        "date_row_id": date_row_id,
                        "replay_id": replay_id,
                        "event_date": day.isoformat(),
                        "control_family": "date_local_intraday_m15_offset_full_day_nonzero",
                        **control,
                        "evidence_boundary": EVIDENCE_BOUNDARY,
                        "safe_flags": SAFE_FLAGS,
                    }
                )
            for route_event in route_on_day:
                nearest, minutes = nearest_event(route_event["dt"], sierra_on_day)
                pair_rows.append(
                    {
                        "route_id": ROUTE_ID,
                        "date_row_id": date_row_id,
                        "replay_id": replay_id,
                        "route_c_bar_open_utc": route_event["bar_open_utc"],
                        "route_c_future_change": route_event["future_change"],
                        "route_c_future_sign": route_event["future_sign"],
                        "route_c_future_abs_change": route_event["future_abs_change"],
                        "route_c_delta_aligned_with_future": route_event["delta_aligned_with_future"],
                        "nearest_sierra_bar_start_utc": nearest.get("bar_start_utc") if nearest else None,
                        "nearest_sierra_minutes_abs": minutes,
                        "nearest_sierra_future_change": nearest.get("future_change") if nearest else None,
                        "nearest_sierra_future_sign": nearest.get("future_sign") if nearest else None,
                        "nearest_sierra_abs_future_change": nearest.get("abs_future_change") if nearest else None,
                        "nearest_sierra_future_follows_delta_sign": nearest.get("future_follows_delta_sign") if nearest else None,
                        "within_15m": bool(minutes is not None and minutes <= 15),
                        "within_60m": bool(minutes is not None and minutes <= 60),
                        "same_future_sign_as_nearest_sierra": (
                            route_event.get("future_sign") == nearest.get("future_sign") if nearest else None
                        ),
                        "evidence_boundary": EVIDENCE_BOUNDARY,
                        "safe_flags": SAFE_FLAGS,
                    }
                )
    return date_rows, pair_rows, shift_rows, bucket_counts


def date_next_action(bucket: str) -> str:
    if bucket == "DATE_OBSERVED_ABOVE_INTRADAY_OFFSETS":
        return "inspect every route/sierra event pair on this date and test directional agreement"
    if bucket == "DATE_INTRADAY_PLACEBO_COMPETES":
        return "treat as date-local generic timing; do not use as source confirmation"
    if bucket == "DATE_SHARED_NO_INTRADAY_COOCCURRENCE":
        return "date overlap only; preserve as regime context or capture finer event source"
    if bucket == "DATE_HAS_ROUTE_ONLY":
        return "route needs source capture for this date"
    if bucket == "DATE_HAS_SIERRA_ONLY":
        return "source activity lacks Route C residual event; preserve as non-confirming context"
    return "manual date-regime review required"


def build_bucket_rows(bucket_counts: Counter[str]) -> list[dict[str, Any]]:
    return [
        {
            "route_id": ROUTE_ID,
            "date_regime_bucket": bucket,
            "row_count": count,
            "evidence_boundary": "date-regime bucket count only; no validation or promotion",
            "safe_flags": SAFE_FLAGS,
        }
        for bucket, count in sorted(bucket_counts.items())
    ]


def build_questions(bucket_counts: Counter[str]) -> list[dict[str, Any]]:
    return [
        {
            "route_id": ROUTE_ID,
            "date_regime_bucket": bucket,
            "question": f"What exact date-level action follows for all {count} rows in {bucket}?",
            "next_action": date_next_action(bucket),
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        }
        for bucket, count in sorted(bucket_counts.items())
    ]


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_route_c_date_regime_split_builder", "created"),
        (RESULT_PATH, "sierra_route_c_date_regime_split_result", "created"),
        (DATE_LEDGER, "sierra_route_c_date_regime_split_date_ledger", "created"),
        (EVENT_PAIR_LEDGER, "sierra_route_c_date_regime_event_pair_ledger", "created"),
        (DATE_SHIFT_CONTROL_LEDGER, "sierra_route_c_date_regime_shift_control_ledger", "created"),
        (BUCKET_LEDGER, "sierra_route_c_date_regime_split_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_route_c_date_regime_split_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_route_c_date_regime_split_summary", "created"),
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
        "event_type": "sierra_route_c_date_regime_split",
        "status": "done",
        "route": "sierra_source_contract_repair",
        "details": "Split every date for the cooccurrence-control row that beat intraday offsets but not date rotations; preserved route/sierra event pairs and date-local shift controls.",
        "counts": counts,
        "bucket_counts": bucket_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(DATE_LEDGER),
            relative(EVENT_PAIR_LEDGER),
            relative(DATE_SHIFT_CONTROL_LEDGER),
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
        "# Sierra to Route C Date-Regime Split",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: date-regime split only. No strategy validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
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
            "- Inspect every event pair on dates above intraday offsets.",
            "- Convert date-local placebo-competing rows into generic timing/context rather than confirmation.",
            "- Emit capture requirements for route-only dates.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    date_rows, pair_rows, shift_rows, bucket_counts = build_split()
    bucket_rows = build_bucket_rows(bucket_counts)
    question_rows = build_questions(bucket_counts)
    write_jsonl(DATE_LEDGER, date_rows)
    write_jsonl(EVENT_PAIR_LEDGER, pair_rows)
    write_jsonl(DATE_SHIFT_CONTROL_LEDGER, shift_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    counts = {
        "focus_replay_rows": len(focus_rows()),
        "date_rows": len(date_rows),
        "event_pair_rows": len(pair_rows),
        "date_shift_control_rows": len(shift_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
        "intraday_offset_count_per_date": len(INTRADAY_OFFSETS_MINUTES),
    }
    result = {
        "schema": "sierra_route_c_date_regime_split_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_ROUTE_C_DATE_REGIME_SPLIT_DIAGNOSTIC_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "date_regime_bucket_counts": dict(sorted(bucket_counts.items())),
        "next_same_resource_work": [
            "event-pair direction inspection for date rows above intraday offsets",
            "generic context conversion for date-local placebo-competing rows",
            "source capture route for route-only dates",
        ],
        "not_completion": "This date-regime split deepens the only date-sensitive cooccurrence row but does not complete the 60-hour objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, dict(bucket_counts))
    write_summary(generated_utc, counts, dict(bucket_counts))
    print(json.dumps({"ok": True, "counts": counts, "bucket_counts": dict(bucket_counts), "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
