#!/usr/bin/env python3
"""Build source-bound Sierra SCID primitive target movement controls."""

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

PRIMITIVE_EVENT_LEDGER = ROUTE_DIR / f"SIERRA_SCID_M15_PRIMITIVE_EVENT_LEDGER_{STAMP}.jsonl"
RESULT_PATH = ROUTE_DIR / f"SIERRA_SCID_M15_TARGET_MOVEMENT_PACKET_RESULT_{STAMP}.json"
TARGET_EVENT_LEDGER = ROUTE_DIR / f"SIERRA_SCID_M15_TARGET_MOVEMENT_EVENT_LEDGER_{STAMP}.jsonl"
FLAG_CONTROL_LEDGER = ROUTE_DIR / f"SIERRA_SCID_M15_TARGET_MOVEMENT_FLAG_CONTROL_LEDGER_{STAMP}.jsonl"
FAIL_CLOSED_LEDGER = ROUTE_DIR / f"SIERRA_SCID_M15_TARGET_MOVEMENT_FAIL_CLOSED_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_SCID_M15_TARGET_MOVEMENT_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_SCID_M15_TARGET_MOVEMENT_PACKET_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Sierra SCID M15 primitive target movement controls only; no strategy "
    "validation, trade outcome, R/PnL, expectancy, live-readiness, or promotion"
)

HORIZON_BARS = {"h4": 4, "h16": 16, "h32": 32}


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def relative(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def append_jsonl(handle: Any, row: dict[str, Any]) -> None:
    handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def safe_float(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if out != out or out in (float("inf"), float("-inf")):
        return None
    return out


def sign(value: Any) -> int:
    numeric = safe_float(value)
    if numeric is None:
        return 0
    if numeric > 0:
        return 1
    if numeric < 0:
        return -1
    return 0


def load_events() -> pd.DataFrame:
    df = pd.read_json(PRIMITIVE_EVENT_LEDGER, lines=True)
    df["bar_start_utc"] = pd.to_datetime(df["bar_start_utc"], utc=True)
    df["bar_end_exclusive_utc"] = pd.to_datetime(df["bar_end_exclusive_utc"], utc=True)
    for col in (
        "open",
        "high",
        "low",
        "close",
        "price_change",
        "price_range",
        "delta",
        "abs_delta",
        "source_records",
        "source_gap_minutes",
    ):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["price_sign"] = df["price_change"].map(sign)
    df["delta_sign"] = df["delta"].map(sign)
    df.sort_values(["source_symbol", "bar_start_utc"], inplace=True)
    return df


def build_targets(df: pd.DataFrame) -> tuple[int, int, Counter[str]]:
    target_rows = 0
    fail_rows = 0
    fail_reason_counts: Counter[str] = Counter()
    with TARGET_EVENT_LEDGER.open("w", encoding="utf-8") as target_handle, FAIL_CLOSED_LEDGER.open(
        "w", encoding="utf-8"
    ) as fail_handle:
        for source_symbol, group in df.groupby("source_symbol", sort=True):
            group = group.sort_values("bar_start_utc").reset_index(drop=True)
            for horizon_id, bars in HORIZON_BARS.items():
                future = group.shift(-bars)
                expected_future_start = group["bar_start_utc"] + pd.to_timedelta(bars * 15, unit="min")
                has_future = future["bar_start_utc"].notna()
                contiguous = has_future & (future["bar_start_utc"] == expected_future_start)
                for idx, row in group.iterrows():
                    if not bool(contiguous.iloc[idx]):
                        reason = "insufficient_future_rows" if not bool(has_future.iloc[idx]) else "non_contiguous_future_gap"
                        fail_reason_counts[reason] += 1
                        append_jsonl(
                            fail_handle,
                            {
                                "route_id": ROUTE_ID,
                                "source_symbol": source_symbol,
                                "bar_start_utc": row["bar_start_utc"].isoformat().replace("+00:00", "Z"),
                                "session_bucket": row["session_bucket"],
                                "horizon_id": horizon_id,
                                "reason": reason,
                                "expected_future_bar_start_utc": expected_future_start.iloc[idx].isoformat().replace(
                                    "+00:00", "Z"
                                ),
                                "observed_future_bar_start_utc": (
                                    future["bar_start_utc"].iloc[idx].isoformat().replace("+00:00", "Z")
                                    if bool(has_future.iloc[idx])
                                    else None
                                ),
                                "primitive_flags": row["primitive_flags"],
                                "evidence_boundary": EVIDENCE_BOUNDARY,
                                "safe_flags": SAFE_FLAGS,
                            },
                        )
                        fail_rows += 1
                        continue
                    future_row = future.iloc[idx]
                    future_change = safe_float(future_row["close"] - row["close"])
                    price_range = safe_float(row["price_range"])
                    future_change_per_range = (
                        future_change / price_range
                        if future_change is not None and price_range is not None and price_range > 0
                        else None
                    )
                    future_sign = sign(future_change)
                    price_sign = int(row["price_sign"])
                    delta_sign = int(row["delta_sign"])
                    event = {
                        "route_id": ROUTE_ID,
                        "source_symbol": source_symbol,
                        "bar_start_utc": row["bar_start_utc"].isoformat().replace("+00:00", "Z"),
                        "bar_end_exclusive_utc": row["bar_end_exclusive_utc"].isoformat().replace("+00:00", "Z"),
                        "future_bar_start_utc": future_row["bar_start_utc"].isoformat().replace("+00:00", "Z"),
                        "session_bucket": row["session_bucket"],
                        "horizon_id": horizon_id,
                        "horizon_bars": bars,
                        "current_close": safe_float(row["close"]),
                        "future_close": safe_float(future_row["close"]),
                        "future_change": future_change,
                        "abs_future_change": abs(future_change) if future_change is not None else None,
                        "future_change_per_current_range": future_change_per_range,
                        "current_price_range": price_range,
                        "current_price_change": safe_float(row["price_change"]),
                        "current_delta": safe_float(row["delta"]),
                        "price_sign": price_sign,
                        "delta_sign": delta_sign,
                        "future_sign": future_sign,
                        "future_follows_price_sign": bool(price_sign and future_sign and price_sign == future_sign),
                        "future_follows_delta_sign": bool(delta_sign and future_sign and delta_sign == future_sign),
                        "primitive_flags": row["primitive_flags"],
                        "primitive_flag_count": len(row["primitive_flags"] or []),
                        "source_audit_key": row["source_audit_key"],
                        "evidence_boundary": EVIDENCE_BOUNDARY,
                        "safe_flags": SAFE_FLAGS,
                    }
                    append_jsonl(target_handle, event)
                    target_rows += 1
    return target_rows, fail_rows, fail_reason_counts


def aggregate_stats(group: pd.DataFrame) -> dict[str, Any]:
    n = int(len(group))
    if n == 0:
        return {
            "n": 0,
            "mean_future_change": None,
            "median_future_change": None,
            "mean_abs_future_change": None,
            "mean_future_change_per_current_range": None,
            "future_follows_price_sign_rate": None,
            "future_follows_delta_sign_rate": None,
        }
    return {
        "n": n,
        "mean_future_change": safe_float(group["future_change"].mean()),
        "median_future_change": safe_float(group["future_change"].median()),
        "mean_abs_future_change": safe_float(group["abs_future_change"].mean()),
        "mean_future_change_per_current_range": safe_float(group["future_change_per_current_range"].mean()),
        "future_follows_price_sign_rate": safe_float(group["future_follows_price_sign"].mean()),
        "future_follows_delta_sign_rate": safe_float(group["future_follows_delta_sign"].mean()),
    }


def build_flag_controls() -> tuple[int, Counter[str]]:
    target = pd.read_json(TARGET_EVENT_LEDGER, lines=True)
    if target.empty:
        write_jsonl(FLAG_CONTROL_LEDGER, [])
        return 0, Counter()
    target["future_follows_price_sign"] = target["future_follows_price_sign"].astype(bool)
    target["future_follows_delta_sign"] = target["future_follows_delta_sign"].astype(bool)
    denominator_stats = {
        key: aggregate_stats(group)
        for key, group in target.groupby(["source_symbol", "session_bucket", "horizon_id"], sort=True)
    }
    exploded = target.explode("primitive_flags")
    exploded = exploded[exploded["primitive_flags"].notna() & (exploded["primitive_flags"].astype(str) != "")]
    rows: list[dict[str, Any]] = []
    bucket_counts: Counter[str] = Counter()
    for key, group in exploded.groupby(["source_symbol", "session_bucket", "horizon_id", "primitive_flags"], sort=True):
        symbol, session, horizon_id, primitive_flag = key
        flagged_stats = aggregate_stats(group)
        denom = denominator_stats[(symbol, session, horizon_id)]
        bucket = classify_control(flagged_stats, denom)
        bucket_counts[bucket] += 1
        rows.append(
            {
                "route_id": ROUTE_ID,
                "source_symbol": symbol,
                "session_bucket": session,
                "horizon_id": horizon_id,
                "primitive_flag": primitive_flag,
                "flagged_stats": flagged_stats,
                "denominator_stats": denom,
                "control_bucket": bucket,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    write_jsonl(FLAG_CONTROL_LEDGER, rows)
    return len(rows), bucket_counts


def classify_control(flagged: dict[str, Any], denom: dict[str, Any]) -> str:
    if int(flagged.get("n") or 0) < 20:
        return "UNDERPOWERED_N_LT_20"
    flagged_abs = safe_float(flagged.get("mean_abs_future_change"))
    denom_abs = safe_float(denom.get("mean_abs_future_change"))
    flagged_price = safe_float(flagged.get("future_follows_price_sign_rate"))
    denom_price = safe_float(denom.get("future_follows_price_sign_rate"))
    flagged_delta = safe_float(flagged.get("future_follows_delta_sign_rate"))
    denom_delta = safe_float(denom.get("future_follows_delta_sign_rate"))
    if flagged_abs is None or denom_abs is None:
        return "MISSING_MOVEMENT_STATS"
    if flagged_abs > denom_abs and (
        (flagged_price is not None and denom_price is not None and flagged_price > denom_price)
        or (flagged_delta is not None and denom_delta is not None and flagged_delta > denom_delta)
    ):
        return "DESCRIPTIVE_MOVEMENT_ABOVE_DENOMINATOR_WITH_DIRECTION_ALIGNMENT"
    if flagged_abs > denom_abs:
        return "DESCRIPTIVE_MOVEMENT_ABOVE_DENOMINATOR_NO_ALIGNMENT"
    return "DENOMINATOR_EXPLAINS_OR_WEAKENS"


def build_questions(control_bucket_counts: Counter[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for bucket in sorted(control_bucket_counts):
        rows.append(
            {
                "route_id": ROUTE_ID,
                "control_bucket": bucket,
                "question": "Which flags in this bucket survive neighbor placebo, source-gap, and cross-source controls?",
                "next_action": "Build Sierra neighbor placebo/control triage and split by source gap before any residual interpretation.",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    rows.append(
        {
            "route_id": ROUTE_ID,
            "control_bucket": "ALL",
            "question": "Do Sierra futures proxy primitives explain or contradict Route C tick primitive residuals on overlapping sessions?",
            "next_action": "Join Sierra proxy target controls to existing Route C tick residual descriptors by symbol family/session/horizon.",
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        }
    )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_scid_m15_target_movement_packet_builder", "created"),
        (RESULT_PATH, "sierra_scid_m15_target_movement_packet_result", "created"),
        (TARGET_EVENT_LEDGER, "sierra_scid_m15_target_movement_event_ledger", "created"),
        (FLAG_CONTROL_LEDGER, "sierra_scid_m15_target_movement_flag_control_ledger", "created"),
        (FAIL_CLOSED_LEDGER, "sierra_scid_m15_target_movement_fail_closed_ledger", "created"),
        (QUESTION_LEDGER, "sierra_scid_m15_target_movement_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_scid_m15_target_movement_packet_summary", "created"),
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
        "event_type": "sierra_scid_m15_target_movement_packet",
        "status": "done",
        "route": "sierra_source_contract_repair",
        "details": (
            "Built target movement, fail-closed gap accounting, and same-symbol/session/horizon controls "
            "for Sierra SCID M15 primitive descriptors."
        ),
        "counts": counts,
        "control_bucket_counts": bucket_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(TARGET_EVENT_LEDGER),
            relative(FLAG_CONTROL_LEDGER),
            relative(FAIL_CLOSED_LEDGER),
            relative(QUESTION_LEDGER),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], bucket_counts: dict[str, int]) -> None:
    lines = [
        "# Sierra SCID M15 Target Movement Packet",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: target movement controls only. No strategy validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Control Buckets", ""])
    for key, value in sorted(bucket_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Next Same-Resource Work",
            "",
            "- Build neighbor-placebo and source-gap controls over this same packet.",
            "- Join overlapping Sierra proxy families with Route C tick residual descriptors.",
            "- Split above-denominator rows into continuation, inverse, avoid, and source-gap families.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    df = load_events()
    target_rows, fail_rows, fail_reason_counts = build_targets(df)
    flag_control_rows, control_bucket_counts = build_flag_controls()
    question_rows = build_questions(control_bucket_counts)
    write_jsonl(QUESTION_LEDGER, question_rows)
    counts = {
        "input_primitive_event_rows": int(len(df)),
        "target_event_rows": target_rows,
        "flag_control_rows": flag_control_rows,
        "fail_closed_rows": fail_rows,
        "question_rows": len(question_rows),
        "source_symbols": int(df["source_symbol"].nunique()),
        "horizon_rows": len(HORIZON_BARS),
    }
    result = {
        "schema": "sierra_scid_m15_target_movement_packet_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_SCID_M15_TARGET_MOVEMENT_CONTROL_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "fail_reason_counts": dict(sorted(fail_reason_counts.items())),
        "control_bucket_counts": dict(sorted(control_bucket_counts.items())),
        "horizons": HORIZON_BARS,
        "next_same_resource_work": [
            "build neighbor placebo/source-gap controls",
            "join Sierra proxy controls to Route C tick residual descriptors",
            "split control-surviving families into continuation/inverse/avoid candidates",
        ],
        "not_completion": "This creates movement controls for Sierra descriptors; it does not complete the 60-hour objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(generated_utc, counts, dict(control_bucket_counts))
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, dict(control_bucket_counts))
    print(json.dumps({"ok": True, "counts": counts, "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
