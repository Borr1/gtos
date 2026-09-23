#!/usr/bin/env python3
"""Control Sierra/Route C event cooccurrence with time/date placebos."""

from __future__ import annotations

import bisect
import json
from collections import Counter, defaultdict
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

REPLAY_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_ALIGNED_EVENT_REPLAY_LEDGER_{STAMP}.jsonl"
ROUTE_EVENT_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_ALIGNED_ROUTE_EVENT_LEDGER_{STAMP}.jsonl"
SIERRA_EVENT_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_ALIGNED_SIERRA_EVENT_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_ROUTE_C_COOCCURRENCE_CONTROL_RESULT_{STAMP}.json"
CONTROL_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_COOCCURRENCE_CONTROL_LEDGER_{STAMP}.jsonl"
SHIFT_CONTROL_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_COOCCURRENCE_SHIFT_CONTROL_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_COOCCURRENCE_CONTROL_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_COOCCURRENCE_CONTROL_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_ROUTE_C_COOCCURRENCE_CONTROL_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Sierra/Route C cooccurrence placebo controls only; no strategy validation, "
    "trade outcome, R/PnL, expectancy, live-readiness, or promotion"
)

INTRADAY_OFFSETS_MINUTES = [minutes for minutes in range(-1425, 1426, 15) if minutes != 0]


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


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    sorted_values = sorted(values)
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (len(sorted_values) - 1) * p
    low = int(rank)
    high = min(low + 1, len(sorted_values) - 1)
    frac = rank - low
    return sorted_values[low] * (1 - frac) + sorted_values[high] * frac


def distribution(values: list[float], observed: float | None) -> dict[str, Any]:
    if not values:
        return {
            "control_count": 0,
            "control_mean": None,
            "control_max": None,
            "control_p50": None,
            "control_p95": None,
            "tail_fraction_ge_observed": None,
            "observed_minus_control_max": None,
        }
    control_max = max(values)
    return {
        "control_count": len(values),
        "control_mean": sum(values) / len(values),
        "control_max": control_max,
        "control_p50": percentile(values, 0.50),
        "control_p95": percentile(values, 0.95),
        "tail_fraction_ge_observed": (
            sum(1 for value in values if observed is not None and value >= observed) / len(values)
            if observed is not None
            else None
        ),
        "observed_minus_control_max": observed - control_max if observed is not None else None,
    }


def nearest_minutes(route_dt: datetime, sierra_dts: list[datetime]) -> float | None:
    if not sierra_dts:
        return None
    pos = bisect.bisect_left(sierra_dts, route_dt)
    candidates: list[datetime] = []
    if pos < len(sierra_dts):
        candidates.append(sierra_dts[pos])
    if pos > 0:
        candidates.append(sierra_dts[pos - 1])
    best = min(candidates, key=lambda dt: abs((dt - route_dt).total_seconds()))
    return abs((best - route_dt).total_seconds()) / 60.0


def shares(route_dts: list[datetime], sierra_dts: list[datetime]) -> dict[str, Any]:
    sierra_sorted = sorted(sierra_dts)
    route_n = len(route_dts)
    if route_n == 0:
        return {
            "route_event_n": 0,
            "same_date_count": 0,
            "exact_count": 0,
            "within_15m_count": 0,
            "within_60m_count": 0,
            "same_date_share": None,
            "exact_share": None,
            "within_15m_share": None,
            "within_60m_share": None,
        }
    sierra_dates = {dt.date() for dt in sierra_sorted}
    same_date_count = 0
    exact_count = 0
    within_15_count = 0
    within_60_count = 0
    for route_dt in route_dts:
        if route_dt.date() in sierra_dates:
            same_date_count += 1
        minutes = nearest_minutes(route_dt, sierra_sorted)
        if minutes is None:
            continue
        if minutes == 0:
            exact_count += 1
        if minutes <= 15:
            within_15_count += 1
        if minutes <= 60:
            within_60_count += 1
    return {
        "route_event_n": route_n,
        "same_date_count": same_date_count,
        "exact_count": exact_count,
        "within_15m_count": within_15_count,
        "within_60m_count": within_60_count,
        "same_date_share": same_date_count / route_n,
        "exact_share": exact_count / route_n,
        "within_15m_share": within_15_count / route_n,
        "within_60m_share": within_60_count / route_n,
    }


def load_replay_context() -> tuple[
    list[dict[str, Any]],
    dict[str, list[datetime]],
    dict[str, list[datetime]],
]:
    replay_rows = read_jsonl(REPLAY_LEDGER)
    route_by_replay: dict[str, list[datetime]] = defaultdict(list)
    sierra_by_replay: dict[str, list[datetime]] = defaultdict(list)
    for row in read_jsonl(ROUTE_EVENT_LEDGER):
        route_by_replay[str(row["replay_id"])].append(parse_dt(str(row["route_c_bar_open_utc"])))
    for row in read_jsonl(SIERRA_EVENT_LEDGER):
        sierra_by_replay[str(row["replay_id"])].append(parse_dt(str(row["sierra_bar_start_utc"])))
    for rows in route_by_replay.values():
        rows.sort()
    for rows in sierra_by_replay.values():
        rows.sort()
    return replay_rows, route_by_replay, sierra_by_replay


def intraday_shift_control_rows(replay_id: str, route_dts: list[datetime], sierra_dts: list[datetime]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for offset in INTRADAY_OFFSETS_MINUTES:
        shifted = [dt + timedelta(minutes=offset) for dt in sierra_dts]
        shifted_shares = shares(route_dts, shifted)
        out.append(
            {
                "route_id": ROUTE_ID,
                "replay_id": replay_id,
                "control_family": "intraday_m15_offset_full_day_nonzero",
                "offset_minutes": offset,
                "rotation_steps": None,
                "same_date_share": shifted_shares["same_date_share"],
                "exact_share": shifted_shares["exact_share"],
                "within_15m_share": shifted_shares["within_15m_share"],
                "within_60m_share": shifted_shares["within_60m_share"],
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return out


def rotate_date(original: datetime, mapping: dict[date, date]) -> datetime:
    new_date = mapping[original.date()]
    original_time: time = original.timetz().replace(tzinfo=None)
    return datetime.combine(new_date, original_time, tzinfo=UTC)


def date_rotation_control_rows(replay_id: str, route_dts: list[datetime], sierra_dts: list[datetime]) -> list[dict[str, Any]]:
    all_dates = sorted({dt.date() for dt in route_dts} | {dt.date() for dt in sierra_dts})
    if len(all_dates) < 2:
        return []
    out: list[dict[str, Any]] = []
    for steps in range(1, len(all_dates)):
        mapping = {day: all_dates[(index + steps) % len(all_dates)] for index, day in enumerate(all_dates)}
        shifted = [rotate_date(dt, mapping) for dt in sierra_dts]
        shifted_shares = shares(route_dts, shifted)
        out.append(
            {
                "route_id": ROUTE_ID,
                "replay_id": replay_id,
                "control_family": "date_rotation_all_nonzero_steps",
                "offset_minutes": None,
                "rotation_steps": steps,
                "same_date_share": shifted_shares["same_date_share"],
                "exact_share": shifted_shares["exact_share"],
                "within_15m_share": shifted_shares["within_15m_share"],
                "within_60m_share": shifted_shares["within_60m_share"],
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return out


def classify_control(observed: dict[str, Any], intraday_dist: dict[str, Any], date_dist: dict[str, Any]) -> str:
    observed_within15 = observed.get("within_15m_share")
    if observed_within15 is None or observed_within15 == 0:
        return "NO_INTRADAY_COOCCURRENCE_OBSERVED"
    intraday_max = intraday_dist.get("control_max")
    date_max = date_dist.get("control_max")
    above_intraday = intraday_max is not None and observed_within15 > intraday_max
    above_date = date_max is not None and observed_within15 > date_max
    if above_intraday and above_date:
        return "OBSERVED_ABOVE_ALL_TIME_AND_DATE_PLACEBOS"
    if above_intraday:
        return "OBSERVED_ABOVE_INTRADAY_PLACEBOS_DATE_COMPETES"
    if above_date:
        return "OBSERVED_ABOVE_DATE_PLACEBOS_INTRADAY_COMPETES"
    return "PLACEBO_COMPETES_WITH_OBSERVED_COOCCURRENCE"


def build_controls() -> tuple[list[dict[str, Any]], list[dict[str, Any]], Counter[str]]:
    replay_rows, route_by_replay, sierra_by_replay = load_replay_context()
    control_rows: list[dict[str, Any]] = []
    shift_rows: list[dict[str, Any]] = []
    bucket_counts: Counter[str] = Counter()
    for row in replay_rows:
        replay_id = str(row["replay_id"])
        route_dts = route_by_replay.get(replay_id, [])
        sierra_dts = sierra_by_replay.get(replay_id, [])
        observed = shares(route_dts, sierra_dts)
        intraday_rows = intraday_shift_control_rows(replay_id, route_dts, sierra_dts)
        date_rows = date_rotation_control_rows(replay_id, route_dts, sierra_dts)
        shift_rows.extend(intraday_rows)
        shift_rows.extend(date_rows)
        intraday_within15 = [float(item["within_15m_share"]) for item in intraday_rows if item["within_15m_share"] is not None]
        date_within15 = [float(item["within_15m_share"]) for item in date_rows if item["within_15m_share"] is not None]
        intraday_dist = distribution(intraday_within15, observed.get("within_15m_share"))
        date_dist = distribution(date_within15, observed.get("within_15m_share"))
        bucket = classify_control(observed, intraday_dist, date_dist)
        bucket_counts[bucket] += 1
        control_rows.append(
            {
                "route_id": ROUTE_ID,
                "replay_id": replay_id,
                "source_symbol": row["source_symbol"],
                "source_proxy_family": row["source_proxy_family"],
                "proxy_relation": row["proxy_relation"],
                "route_c_symbol": row["route_c_symbol"],
                "route_c_queue_id": row["route_c_queue_id"],
                "route_c_primitive_flag": row["route_c_primitive_flag"],
                "sierra_primitive_flag": row["sierra_primitive_flag"],
                "event_replay_bucket": row["event_replay_bucket"],
                "observed_cooccurrence": observed,
                "intraday_shift_within15_distribution": intraday_dist,
                "date_rotation_within15_distribution": date_dist,
                "intraday_shift_control_rows": len(intraday_rows),
                "date_rotation_control_rows": len(date_rows),
                "cooccurrence_control_bucket": bucket,
                "next_same_resource_action": control_next_action(bucket),
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return control_rows, shift_rows, bucket_counts


def control_next_action(bucket: str) -> str:
    if bucket == "OBSERVED_ABOVE_ALL_TIME_AND_DATE_PLACEBOS":
        return "open event-direction and source-confirmation replay for every row in this bucket"
    if bucket == "OBSERVED_ABOVE_INTRADAY_PLACEBOS_DATE_COMPETES":
        return "treat as date/regime-sensitive; split by shared date before mechanism claims"
    if bucket == "OBSERVED_ABOVE_DATE_PLACEBOS_INTRADAY_COMPETES":
        return "treat as intraday-timing-sensitive but check nonzero time offsets before candidate logic"
    if bucket == "PLACEBO_COMPETES_WITH_OBSERVED_COOCCURRENCE":
        return "do not use cooccurrence as unique confirmation; convert to generic context or avoid logic"
    if bucket == "NO_INTRADAY_COOCCURRENCE_OBSERVED":
        return "date-level only; run date-regime controls or capture finer aligned source"
    return "manual cooccurrence-control review required"


def build_bucket_rows(bucket_counts: Counter[str]) -> list[dict[str, Any]]:
    return [
        {
            "route_id": ROUTE_ID,
            "cooccurrence_control_bucket": bucket,
            "row_count": count,
            "evidence_boundary": "cooccurrence control bucket count only; no validation or promotion",
            "safe_flags": SAFE_FLAGS,
        }
        for bucket, count in sorted(bucket_counts.items())
    ]


def build_questions(bucket_counts: Counter[str]) -> list[dict[str, Any]]:
    return [
        {
            "route_id": ROUTE_ID,
            "cooccurrence_control_bucket": bucket,
            "question": f"What exact replay, split, or failure-intelligence route follows for all {count} rows in {bucket}?",
            "next_action": control_next_action(bucket),
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        }
        for bucket, count in sorted(bucket_counts.items())
    ]


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_route_c_cooccurrence_control_builder", "created"),
        (RESULT_PATH, "sierra_route_c_cooccurrence_control_result", "created"),
        (CONTROL_LEDGER, "sierra_route_c_cooccurrence_control_ledger", "created"),
        (SHIFT_CONTROL_LEDGER, "sierra_route_c_cooccurrence_shift_control_ledger", "created"),
        (BUCKET_LEDGER, "sierra_route_c_cooccurrence_control_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_route_c_cooccurrence_control_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_route_c_cooccurrence_control_summary", "created"),
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
        "event_type": "sierra_route_c_cooccurrence_controls",
        "status": "done",
        "route": "sierra_source_contract_repair",
        "details": "Controlled aligned Sierra/Route C replay cooccurrence with every nonzero full-day 15-minute offset and every nonzero date rotation per replay row.",
        "counts": counts,
        "bucket_counts": bucket_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(CONTROL_LEDGER),
            relative(SHIFT_CONTROL_LEDGER),
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
        "# Sierra to Route C Cooccurrence Controls",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: cooccurrence placebo controls only. No strategy validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
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
            "- For rows above all time/date placebos, replay direction and event path mechanics.",
            "- For placebo-competing rows, preserve them as generic context or avoid-filter intelligence.",
            "- For date-regime-sensitive rows, split by shared date before any source-confirmation claim.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    control_rows, shift_rows, bucket_counts = build_controls()
    bucket_rows = build_bucket_rows(bucket_counts)
    question_rows = build_questions(bucket_counts)
    write_jsonl(CONTROL_LEDGER, control_rows)
    write_jsonl(SHIFT_CONTROL_LEDGER, shift_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    counts = {
        "control_rows": len(control_rows),
        "shift_control_rows": len(shift_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
        "intraday_offset_count_per_replay": len(INTRADAY_OFFSETS_MINUTES),
    }
    result = {
        "schema": "sierra_route_c_cooccurrence_control_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_ROUTE_C_COOCCURRENCE_CONTROL_DIAGNOSTIC_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "cooccurrence_control_bucket_counts": dict(sorted(bucket_counts.items())),
        "control_families": [
            "intraday_m15_offset_full_day_nonzero",
            "date_rotation_all_nonzero_steps",
        ],
        "next_same_resource_work": [
            "direction/path replay for rows above all time/date placebos",
            "date-regime split for rows where date controls compete",
            "generic-context or avoid-filter conversion for placebo-competing rows",
        ],
        "not_completion": "This cooccurrence control packet deepens aligned replay but does not complete the 60-hour objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, dict(bucket_counts))
    write_summary(generated_utc, counts, dict(bucket_counts))
    print(json.dumps({"ok": True, "counts": counts, "bucket_counts": dict(bucket_counts), "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
