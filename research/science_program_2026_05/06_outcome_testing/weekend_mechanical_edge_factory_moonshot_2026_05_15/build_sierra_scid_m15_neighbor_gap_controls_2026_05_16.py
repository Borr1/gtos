#!/usr/bin/env python3
"""Challenge Sierra SCID target controls with source-gap and neighbor placebos."""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

TARGET_EVENT_LEDGER = ROUTE_DIR / f"SIERRA_SCID_M15_TARGET_MOVEMENT_EVENT_LEDGER_{STAMP}.jsonl"
FLAG_CONTROL_LEDGER = ROUTE_DIR / f"SIERRA_SCID_M15_TARGET_MOVEMENT_FLAG_CONTROL_LEDGER_{STAMP}.jsonl"
RESULT_PATH = ROUTE_DIR / f"SIERRA_SCID_M15_NEIGHBOR_GAP_CONTROL_RESULT_{STAMP}.json"
CONTROL_LEDGER = ROUTE_DIR / f"SIERRA_SCID_M15_NEIGHBOR_GAP_CONTROL_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_SCID_M15_NEIGHBOR_GAP_CONTROL_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_SCID_M15_NEIGHBOR_GAP_CONTROL_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_SCID_M15_NEIGHBOR_GAP_CONTROL_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Sierra SCID M15 source-gap and neighbor-placebo controls only; no strategy "
    "validation, trade outcome, R/PnL, expectancy, live-readiness, or promotion"
)

NEIGHBOR_OFFSETS = [-2, -1, 1, 2]


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def relative(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


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


def aggregate_stats(group: pd.DataFrame) -> dict[str, Any]:
    n = int(len(group))
    if n == 0:
        return {
            "n": 0,
            "mean_abs_future_change": None,
            "mean_future_change_per_current_range": None,
            "future_follows_price_sign_rate": None,
            "future_follows_delta_sign_rate": None,
        }
    return {
        "n": n,
        "mean_abs_future_change": safe_float(group["abs_future_change"].mean()),
        "mean_future_change_per_current_range": safe_float(group["future_change_per_current_range"].mean()),
        "future_follows_price_sign_rate": safe_float(group["future_follows_price_sign"].mean()),
        "future_follows_delta_sign_rate": safe_float(group["future_follows_delta_sign"].mean()),
    }


def load_target() -> pd.DataFrame:
    df = pd.read_json(TARGET_EVENT_LEDGER, lines=True)
    df["bar_start_utc"] = pd.to_datetime(df["bar_start_utc"], utc=True)
    for col in ("future_change", "abs_future_change", "future_change_per_current_range"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["future_follows_price_sign"] = df["future_follows_price_sign"].astype(bool)
    df["future_follows_delta_sign"] = df["future_follows_delta_sign"].astype(bool)
    df["is_post_source_gap_bar"] = df["primitive_flags"].map(
        lambda flags: "post_source_gap_first_bar" in flags if isinstance(flags, list) else False
    )
    return df


def load_flag_controls() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with FLAG_CONTROL_LEDGER.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def build_exploded(target: pd.DataFrame) -> pd.DataFrame:
    exploded = target[
        [
            "source_symbol",
            "session_bucket",
            "horizon_id",
            "bar_start_utc",
            "primitive_flags",
            "is_post_source_gap_bar",
            "future_change",
            "abs_future_change",
            "future_change_per_current_range",
            "future_follows_price_sign",
            "future_follows_delta_sign",
        ]
    ].explode("primitive_flags")
    return exploded[exploded["primitive_flags"].notna() & (exploded["primitive_flags"].astype(str) != "")]


def build_neighbor_stats(target: pd.DataFrame, exploded: pd.DataFrame) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    base = target[
        [
            "source_symbol",
            "session_bucket",
            "horizon_id",
            "bar_start_utc",
            "future_change",
            "abs_future_change",
            "future_change_per_current_range",
            "future_follows_price_sign",
            "future_follows_delta_sign",
        ]
    ].rename(
        columns={
            "session_bucket": "neighbor_session_bucket",
            "bar_start_utc": "neighbor_bar_start_utc",
            "future_change": "neighbor_future_change",
            "abs_future_change": "neighbor_abs_future_change",
            "future_change_per_current_range": "neighbor_future_change_per_current_range",
            "future_follows_price_sign": "neighbor_future_follows_price_sign",
            "future_follows_delta_sign": "neighbor_future_follows_delta_sign",
        }
    )
    out: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for offset in NEIGHBOR_OFFSETS:
        candidate = exploded[
            ["source_symbol", "session_bucket", "horizon_id", "bar_start_utc", "primitive_flags"]
        ].copy()
        candidate["neighbor_bar_start_utc"] = candidate["bar_start_utc"] + pd.to_timedelta(offset * 15, unit="min")
        merged = candidate.merge(
            base,
            how="inner",
            on=["source_symbol", "horizon_id", "neighbor_bar_start_utc"],
        )
        merged = merged[merged["neighbor_session_bucket"] == merged["session_bucket"]]
        if merged.empty:
            continue
        stats_frame = merged.rename(
            columns={
                "neighbor_future_change": "future_change",
                "neighbor_abs_future_change": "abs_future_change",
                "neighbor_future_change_per_current_range": "future_change_per_current_range",
                "neighbor_future_follows_price_sign": "future_follows_price_sign",
                "neighbor_future_follows_delta_sign": "future_follows_delta_sign",
            }
        )
        for key, group in stats_frame.groupby(["source_symbol", "session_bucket", "horizon_id", "primitive_flags"], sort=True):
            out.setdefault(tuple(str(part) for part in key), {})[str(offset)] = aggregate_stats(group)
    return out


def classify(row: dict[str, Any]) -> str:
    original = row["original_flagged_stats"]
    denom = row["denominator_stats"]
    no_gap = row["source_gap_excluded_stats"]
    if int(original.get("n") or 0) < 20:
        return "UNDERPOWERED_ORIGINAL_N_LT_20"
    if int(no_gap.get("n") or 0) < 20:
        return "SOURCE_GAP_DEPENDENT_OR_UNDERPOWERED_AFTER_GAP_FILTER"
    no_gap_abs = safe_float(no_gap.get("mean_abs_future_change"))
    denom_abs = safe_float(denom.get("mean_abs_future_change"))
    if no_gap_abs is None or denom_abs is None:
        return "MISSING_STATS"
    if no_gap_abs <= denom_abs:
        return "SOURCE_GAP_FILTER_WEAKENS_TO_DENOMINATOR"
    neighbor_stats = row["neighbor_placebo_stats"]
    competing = False
    for stats in neighbor_stats.values():
        neighbor_abs = safe_float(stats.get("mean_abs_future_change"))
        if neighbor_abs is not None and no_gap_abs is not None and neighbor_abs >= no_gap_abs:
            competing = True
            break
    if competing:
        return "NEIGHBOR_PLACEBO_COMPETES_WITH_FLAG"
    return "SURVIVES_SOURCE_GAP_AND_NEIGHBOR_DESCRIPTIVE"


def build_controls() -> tuple[list[dict[str, Any]], Counter[str]]:
    target = load_target()
    flag_controls = load_flag_controls()
    exploded = build_exploded(target)
    no_gap_stats = {
        tuple(str(part) for part in key): aggregate_stats(group)
        for key, group in exploded[~exploded["is_post_source_gap_bar"]].groupby(
            ["source_symbol", "session_bucket", "horizon_id", "primitive_flags"],
            sort=True,
        )
    }
    neighbor_stats = build_neighbor_stats(target, exploded)
    rows: list[dict[str, Any]] = []
    bucket_counts: Counter[str] = Counter()
    for control in flag_controls:
        key = (
            str(control["source_symbol"]),
            str(control["session_bucket"]),
            str(control["horizon_id"]),
            str(control["primitive_flag"]),
        )
        row = {
            "route_id": ROUTE_ID,
            "source_symbol": key[0],
            "session_bucket": key[1],
            "horizon_id": key[2],
            "primitive_flag": key[3],
            "original_control_bucket": control.get("control_bucket"),
            "original_flagged_stats": control.get("flagged_stats"),
            "denominator_stats": control.get("denominator_stats"),
            "source_gap_excluded_stats": no_gap_stats.get(
                key,
                {
                    "n": 0,
                    "mean_abs_future_change": None,
                    "mean_future_change_per_current_range": None,
                    "future_follows_price_sign_rate": None,
                    "future_follows_delta_sign_rate": None,
                },
            ),
            "neighbor_placebo_stats": neighbor_stats.get(key, {}),
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        }
        row["gap_neighbor_control_bucket"] = classify(row)
        bucket_counts[row["gap_neighbor_control_bucket"]] += 1
        rows.append(row)
    return rows, bucket_counts


def build_bucket_rows(bucket_counts: Counter[str]) -> list[dict[str, Any]]:
    return [
        {
            "route_id": ROUTE_ID,
            "gap_neighbor_control_bucket": bucket,
            "row_count": count,
            "evidence_boundary": "bucket count only; no validation or promotion",
            "safe_flags": SAFE_FLAGS,
        }
        for bucket, count in sorted(bucket_counts.items())
    ]


def build_questions(bucket_counts: Counter[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for bucket in sorted(bucket_counts):
        rows.append(
            {
                "route_id": ROUTE_ID,
                "gap_neighbor_control_bucket": bucket,
                "question": "What exact source, session, and primitive families remain after this control bucket?",
                "next_action": "Split by source_symbol/session/horizon and join to Route C tick residual families before any candidate label.",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_scid_m15_neighbor_gap_control_builder", "created"),
        (RESULT_PATH, "sierra_scid_m15_neighbor_gap_control_result", "created"),
        (CONTROL_LEDGER, "sierra_scid_m15_neighbor_gap_control_ledger", "created"),
        (BUCKET_LEDGER, "sierra_scid_m15_neighbor_gap_control_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_scid_m15_neighbor_gap_control_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_scid_m15_neighbor_gap_control_summary", "created"),
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
        "event_type": "sierra_scid_m15_neighbor_gap_controls",
        "status": "done",
        "route": "sierra_source_contract_repair",
        "details": "Challenged every Sierra target-control primitive group with source-gap exclusion and ±1/±2 neighbor placebo controls.",
        "counts": counts,
        "bucket_counts": bucket_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(CONTROL_LEDGER),
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
        "# Sierra SCID M15 Neighbor/Gap Controls",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: source-gap and neighbor-placebo controls only. No strategy validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
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
            "- Split surviving descriptive rows by source/session/horizon rather than summarize only.",
            "- Join surviving/weakened families against Route C tick residual descriptors.",
            "- Turn weakened rows into source-gap avoid filters or capture requirements.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    rows, bucket_counts = build_controls()
    bucket_rows = build_bucket_rows(bucket_counts)
    question_rows = build_questions(bucket_counts)
    write_jsonl(CONTROL_LEDGER, rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    counts = {
        "control_rows": len(rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
        "neighbor_offsets": len(NEIGHBOR_OFFSETS),
    }
    result = {
        "schema": "sierra_scid_m15_neighbor_gap_control_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_SCID_M15_SOURCE_GAP_NEIGHBOR_CONTROL_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "bucket_counts": dict(sorted(bucket_counts.items())),
        "neighbor_offsets": NEIGHBOR_OFFSETS,
        "next_same_resource_work": [
            "split surviving rows by source/session/horizon and mechanism family",
            "join Sierra proxy control outcomes against Route C tick residual descriptors",
            "convert source-gap weakened families into source capture or avoid-filter intelligence",
        ],
        "not_completion": "This challenges target controls but does not complete the 60-hour objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(generated_utc, counts, dict(bucket_counts))
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, dict(bucket_counts))
    print(json.dumps({"ok": True, "counts": counts, "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
