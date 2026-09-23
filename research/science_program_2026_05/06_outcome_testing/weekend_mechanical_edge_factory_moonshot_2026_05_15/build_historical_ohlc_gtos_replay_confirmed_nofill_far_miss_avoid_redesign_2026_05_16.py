#!/usr/bin/env python3
"""Build far/within-range confirmed no-fill avoid and retest redesign controls."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

FRICTION_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_CONTROL_RESULT_2026-05-16.json"
FRICTION_ENTRY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_ENTRY_LEDGER_2026-05-16.jsonl"
FRICTION_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_BRANCH_LEDGER_2026-05-16.jsonl"
FRICTION_FAMILY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_FAMILY_LEDGER_2026-05-16.jsonl"

SOURCE_ALIGNMENT_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_RESULT_2026-05-16.json"
SOURCE_ALIGNMENT_SIGNATURE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_SIGNATURE_LEDGER_2026-05-16.jsonl"
SOURCE_ALIGNMENT_COST_MODEL_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_COST_MODEL_LEDGER_2026-05-16.jsonl"
SOURCE_ALIGNMENT_FAMILY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_FAMILY_LEDGER_2026-05-16.jsonl"

M1_SPREAD_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_RESULT_2026-05-16.json"
M1_SPREAD_SIGNATURE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_SIGNATURE_LEDGER_2026-05-16.jsonl"
M1_SPREAD_FAMILY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_FAMILY_LEDGER_2026-05-16.jsonl"

COST_SENSITIVITY_FAMILY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_FAMILY_AGGREGATE_LEDGER_2026-05-16.jsonl"
COST_FILL_STATUS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_COST_FILL_STATUS_LEDGER_2026-05-16.jsonl"
RECOVERED_CROSS_FAMILY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_CROSS_CONTROL_FAMILY_JOIN_LEDGER_2026-05-16.jsonl"

PATH_AMBIGUITY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_AMBIGUITY_LEDGER_2026-05-16.jsonl"
COST_SPLIT_AMBIGUITY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SPLIT_AMBIGUITY_SIGNATURE_LEDGER_2026-05-16.jsonl"

PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-16.json"
SOURCE_MANIFEST_PATH = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
DENOMINATOR_PATH = ROUTE_DIR / f"{PREFIX}_DENOMINATOR_LEDGER_2026-05-16.jsonl"
AVOID_BRANCH_PATH = ROUTE_DIR / f"{PREFIX}_AVOID_FILTER_BRANCH_LEDGER_2026-05-16.jsonl"
RETEST_BRANCH_PATH = ROUTE_DIR / f"{PREFIX}_RETEST_REDESIGN_BRANCH_LEDGER_2026-05-16.jsonl"
SOURCE_CONFIDENCE_PATH = ROUTE_DIR / f"{PREFIX}_SOURCE_CONFIDENCE_BRANCH_LEDGER_2026-05-16.jsonl"
FAMILY_PATH = ROUTE_DIR / f"{PREFIX}_FAMILY_SYNTHESIS_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-16.md"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Historical OHLC GTOS replay confirmed no-fill far/within-range avoid and retest-redesign packet only. "
    "Rows preserve the confirmed no-fill denominator, split beyond-rolling-median-range misses and "
    "within-rolling-median-range misses as separate branch-control classes, and attach source-confidence, "
    "cost/fill/path family, source-alignment, M1 spread replay, and ambiguity context. No validation, "
    "R/PnL, expectancy, win-rate, live-readiness, promotion, scoring, ranking, or live behavior change is claimed."
)

NOT_COMPLETION = "This far/within-range confirmed no-fill avoid/retest-redesign packet does not complete the 60-hour moonshot objective."

FAR_BUCKET = "CONFIRMED_NOFILL_MISS_BEYOND_ROLLING_MEDIAN_RANGE"
WITHIN_BUCKET = "CONFIRMED_NOFILL_MISS_WITHIN_ROLLING_MEDIAN_RANGE"
NEAR_BUCKET = "CONFIRMED_NOFILL_NEAR_MISS_WITHIN_EXACT_FIRST_SPREAD"
CONFLICT_BUCKET = "CONFIRMED_NOFILL_STATUS_CONFLICTS_WITH_EXISTING_COST_THRESHOLD"
IN_SCOPE_BUCKETS = {FAR_BUCKET, WITHIN_BUCKET}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                yield {"_parse_error": True, "_line_no": line_no}


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def source_manifest() -> tuple[list[dict[str, Any]], str]:
    paths = [
        FRICTION_RESULT_PATH,
        FRICTION_ENTRY_PATH,
        FRICTION_BRANCH_PATH,
        FRICTION_FAMILY_PATH,
        SOURCE_ALIGNMENT_RESULT_PATH,
        SOURCE_ALIGNMENT_SIGNATURE_PATH,
        SOURCE_ALIGNMENT_COST_MODEL_PATH,
        SOURCE_ALIGNMENT_FAMILY_PATH,
        M1_SPREAD_RESULT_PATH,
        M1_SPREAD_SIGNATURE_PATH,
        M1_SPREAD_FAMILY_PATH,
        COST_SENSITIVITY_FAMILY_PATH,
        COST_FILL_STATUS_PATH,
        RECOVERED_CROSS_FAMILY_PATH,
        PATH_AMBIGUITY_PATH,
        COST_SPLIT_AMBIGUITY_PATH,
    ]
    rows = [
        {
            "path": str(path.relative_to(REPO)).replace("\\", "/"),
            "sha256": sha256_file(path) if path.exists() else "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
            "status": "HASHED" if path.exists() else "MISSING_FAIL_CLOSED",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "not_completion": True,
        }
        for path in paths
    ]
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def route_session(route_candidate_id: str | None) -> str:
    parts = str(route_candidate_id or "").split("|")
    return parts[1] if len(parts) > 1 else "SESSION_UNKNOWN"


def family_key(row: dict[str, Any]) -> str:
    if row.get("family_key"):
        return str(row["family_key"])
    return "|".join(
        [
            str(row.get("route_candidate_id")),
            str(row.get("entry_variant")),
            str(row.get("target_stop_contract_id")),
        ]
    )


def family_descriptor_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("route_candidate_id"),
        row.get("entry_variant"),
        row.get("target_stop_contract_id"),
        row.get("target_multiple"),
        row.get("stop_multiple"),
    )


def cost_family_descriptor_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("route_candidate_id"),
        row.get("entry_variant"),
        row.get("target_multiple"),
        row.get("stop_multiple"),
    )


def miss_class(bucket: str) -> str:
    if bucket == FAR_BUCKET:
        return "FAR_MISS_BEYOND_ROLLING_MEDIAN_RANGE"
    if bucket == WITHIN_BUCKET:
        return "WITHIN_RANGE_MISS_AT_OR_BELOW_ROLLING_MEDIAN_RANGE"
    if bucket == NEAR_BUCKET:
        return "NEAR_MISS_WITHIN_EXACT_FIRST_SPREAD"
    if bucket == CONFLICT_BUCKET:
        return "SOURCE_ALIGNMENT_CONFLICT_COST_THRESHOLD_TOUCH"
    return "OTHER_CONFIRMED_NOFILL_BUCKET"


def denominator_scope(bucket: str) -> str:
    if bucket == FAR_BUCKET:
        return "IN_SCOPE_FAR_MISS_AVOID_AND_REDESIGN"
    if bucket == WITHIN_BUCKET:
        return "IN_SCOPE_WITHIN_RANGE_RETEST_REDESIGN"
    if bucket == NEAR_BUCKET:
        return "OUT_OF_SCOPE_NEAR_MISS_ENTRY_OFFSET_PACKET"
    if bucket == CONFLICT_BUCKET:
        return "OUT_OF_SCOPE_SOURCE_ALIGNMENT_CONFLICT_PACKET"
    return "OUT_OF_SCOPE_OTHER_CONFIRMED_NOFILL_BUCKET"


def source_confidence_status(row: dict[str, Any]) -> str:
    source = row.get("authoritative_distance_source")
    tick_status = row.get("tick_source_status")
    m1_status = row.get("m1_source_status")
    if source == "EXACT_TICK_FILL_SIDE_PRICE":
        return "EXACT_TICK_FILL_SIDE_SOURCE_CONFIDENCE_BRANCH"
    if source == "M1_BID_BAR_PROXY_PRICE" and m1_status == "MT5_M1_BARS_AVAILABLE":
        if tick_status == "MT5_NO_TICKS_IN_PROBE_WINDOW_FAIL_CLOSED":
            return "M1_BID_BAR_PROXY_SOURCE_CONFIDENCE_BRANCH_TICK_ABSENT"
        return "M1_BID_BAR_PROXY_SOURCE_CONFIDENCE_BRANCH"
    return "SOURCE_CONFIDENCE_FAIL_CLOSED_RECHECK_BRANCH"


def ambiguity_context_status(row: dict[str, Any], split_ambiguity: dict[str, Any] | None, path_ambiguity_rows: int) -> str:
    if row.get("has_same_m15_ambiguity") or (split_ambiguity and split_ambiguity.get("has_same_m15_ambiguity")):
        return "SIGNATURE_SAME_M15_AMBIGUITY_CONTEXT_PRESENT"
    if int(row.get("same_m15_ambiguity_rows_for_family") or 0) > 0 or path_ambiguity_rows > 0:
        return "FAMILY_SAME_M15_AMBIGUITY_CONTEXT_PRESENT"
    return "NO_SAME_M15_AMBIGUITY_CONTEXT_FROM_INPUTS"


def exact_spread_context_status(row: dict[str, Any], recovered_family: dict[str, Any] | None) -> str:
    exact_rows = int(row.get("family_exact_descriptor_delta_rows") or 0)
    unavailable_rows = int(row.get("family_exact_unavailable_stress_rows") or 0)
    if recovered_family:
        exact_rows = max(exact_rows, int(recovered_family.get("exact_descriptor_delta_rows") or 0))
        unavailable_rows = max(unavailable_rows, int(recovered_family.get("exact_unavailable_stress_rows") or 0))
    if exact_rows > 0 and unavailable_rows > 0:
        return "EXACT_SPREAD_AND_UNAVAILABLE_STRESS_FAMILY_CONTEXT"
    if exact_rows > 0:
        return "EXACT_SPREAD_DESCRIPTOR_DELTA_FAMILY_CONTEXT"
    if unavailable_rows > 0:
        return "EXACT_SPREAD_UNAVAILABLE_STRESS_FAMILY_CONTEXT"
    return "NO_EXACT_SPREAD_FAMILY_CONTEXT"


def avoid_filter_status(row: dict[str, Any], src_status: str, amb_status: str) -> str:
    if row.get("execution_friction_distance_bucket") != FAR_BUCKET:
        return "NOT_AVOID_FILTER_SCOPE_WITHIN_RANGE_REDESIGN_ONLY"
    if src_status == "EXACT_TICK_FILL_SIDE_SOURCE_CONFIDENCE_BRANCH" and amb_status == "NO_SAME_M15_AMBIGUITY_CONTEXT_FROM_INPUTS":
        return "FAR_MISS_AVOID_FILTER_EXACT_SOURCE_CLEAN_CONTEXT_BRANCH"
    if src_status.startswith("M1_BID_BAR_PROXY") and amb_status != "NO_SAME_M15_AMBIGUITY_CONTEXT_FROM_INPUTS":
        return "FAR_MISS_AVOID_FILTER_PROXY_SOURCE_WITH_AMBIGUITY_CONTEXT_BRANCH"
    if src_status.startswith("M1_BID_BAR_PROXY"):
        return "FAR_MISS_AVOID_FILTER_PROXY_SOURCE_BRANCH"
    return "FAR_MISS_AVOID_FILTER_SOURCE_RECHECK_BRANCH"


def retest_redesign_status(row: dict[str, Any], src_status: str, amb_status: str) -> str:
    bucket = row.get("execution_friction_distance_bucket")
    if bucket == FAR_BUCKET:
        return "FAR_MISS_RETEST_LIMIT_REDIRECT_TO_AVOID_OR_MARKET_PROXY_REDESIGN"
    if bucket == WITHIN_BUCKET and amb_status != "NO_SAME_M15_AMBIGUITY_CONTEXT_FROM_INPUTS":
        return "WITHIN_RANGE_RETEST_REDESIGN_WITH_TARGET_STOP_AMBIGUITY_STRESS"
    if bucket == WITHIN_BUCKET and src_status.startswith("M1_BID_BAR_PROXY"):
        return "WITHIN_RANGE_RETEST_ZONE_OR_ENTRY_OFFSET_REDESIGN_PROXY_SOURCE"
    if bucket == WITHIN_BUCKET:
        return "WITHIN_RANGE_RETEST_ZONE_OR_ENTRY_OFFSET_REDESIGN_EXACT_SOURCE"
    return "NOT_RETEST_REDESIGN_SCOPE"


def branch_base_row(
    row: dict[str, Any],
    source_manifest_hash: str,
    source_alignment_row: dict[str, Any] | None,
    source_alignment_family: dict[str, Any] | None,
    m1_family_summary: dict[str, Any] | None,
    cost_family_row: dict[str, Any] | None,
    recovered_family: dict[str, Any] | None,
    split_ambiguity: dict[str, Any] | None,
    path_ambiguity_rows: int,
) -> dict[str, Any]:
    src_status = source_confidence_status(row)
    amb_status = ambiguity_context_status(row, split_ambiguity, path_ambiguity_rows)
    exact_status = exact_spread_context_status(row, recovered_family)
    return {
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_BRANCH_CONTEXT",
        "source_manifest_hash": source_manifest_hash,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "cost_sensitivity_signature_id": row.get("cost_sensitivity_signature_id"),
        "execution_friction_branch_id": row.get("execution_friction_branch_id"),
        "execution_friction_signature_id": row.get("execution_friction_signature_id"),
        "entry_variant_id": row.get("entry_variant_id"),
        "event_id": row.get("event_id"),
        "route_candidate_id": row.get("route_candidate_id"),
        "route_session": route_session(row.get("route_candidate_id")),
        "symbol": row.get("symbol"),
        "side": row.get("side"),
        "entry_variant": row.get("entry_variant"),
        "target_stop_contract_id": row.get("target_stop_contract_id"),
        "target_multiple": row.get("target_multiple"),
        "stop_multiple": row.get("stop_multiple"),
        "family_key": family_key(row),
        "confirmed_nofill_miss_class": miss_class(str(row.get("execution_friction_distance_bucket"))),
        "execution_friction_distance_bucket": row.get("execution_friction_distance_bucket"),
        "miss_distance_to_zero_entry_price": row.get("miss_distance_to_zero_entry_price"),
        "miss_distance_to_easiest_existing_cost_threshold": row.get("miss_distance_to_easiest_existing_cost_threshold"),
        "miss_distance_to_zero_over_rolling_median_range": row.get("miss_distance_to_zero_over_rolling_median_range"),
        "miss_distance_to_zero_over_max_spread_proxy": row.get("miss_distance_to_zero_over_max_spread_proxy"),
        "miss_distance_to_zero_over_first_tick_spread": row.get("miss_distance_to_zero_over_first_tick_spread"),
        "authoritative_distance_source": row.get("authoritative_distance_source"),
        "unfilled_probe_status": row.get("unfilled_probe_status"),
        "m1_source_status": row.get("m1_source_status"),
        "tick_source_status": row.get("tick_source_status"),
        "source_confidence_branch_status": src_status,
        "same_m15_ambiguity_context_status": amb_status,
        "path_ambiguity_rows_for_family": path_ambiguity_rows,
        "has_same_m15_ambiguity": row.get("has_same_m15_ambiguity"),
        "same_m15_ambiguity_rows_for_family": row.get("same_m15_ambiguity_rows_for_family"),
        "same_m15_ambiguity_statuses_for_family": row.get("same_m15_ambiguity_statuses_for_family"),
        "cost_split_ambiguity_status": split_ambiguity.get("ambiguity_split_status") if split_ambiguity else None,
        "cost_split_transition_signature": split_ambiguity.get("transition_signature") if split_ambiguity else None,
        "exact_spread_context_status": exact_status,
        "cross_control_family_status": row.get("cross_control_family_status"),
        "family_exact_descriptor_delta_rows": row.get("family_exact_descriptor_delta_rows"),
        "family_exact_unavailable_stress_rows": row.get("family_exact_unavailable_stress_rows"),
        "cost_sensitivity_family_route_status": cost_family_row.get("family_route_status") if cost_family_row else None,
        "cost_sensitivity_status_counts": cost_family_row.get("cost_sensitivity_status_counts") if cost_family_row else None,
        "cost_sensitivity_changed_signature_rows": cost_family_row.get("changed_signature_rows") if cost_family_row else None,
        "cost_sensitivity_gradient_signature_rows": cost_family_row.get("gradient_signature_rows") if cost_family_row else None,
        "cost_sensitivity_unfilled_signature_rows": cost_family_row.get("unfilled_signature_rows") if cost_family_row else None,
        "source_alignment_signature_status": source_alignment_row.get("entry_alignment_status") if source_alignment_row else None,
        "source_alignment_family_signature_rows": source_alignment_family.get("signature_rows") if source_alignment_family else None,
        "source_alignment_family_status_counts": source_alignment_family.get("entry_alignment_status_counts") if source_alignment_family else None,
        "m1_spread_adjusted_family_signature_rows": m1_family_summary.get("signature_rows") if m1_family_summary else 0,
        "m1_spread_adjusted_first_touch_status_counts": (
            dict(sorted(m1_family_summary.get("m1_first_touch_status_counts", {}).items())) if m1_family_summary else {}
        ),
        "recovered_cross_family_status": recovered_family.get("cross_control_family_status") if recovered_family else None,
        "recovered_signature_rows": recovered_family.get("recovered_signature_rows") if recovered_family else None,
        "recovered_path_statuses": recovered_family.get("recovered_path_statuses") if recovered_family else None,
    }


def counter_row(
    row_id: str,
    ledger_name: str,
    dimension_name: str,
    dimension_value: str,
    count: int,
    source_manifest_hash: str,
    miss_class_value: str | None = None,
) -> dict[str, Any]:
    return {
        "bucket_row_id": row_id,
        "ledger_name": ledger_name,
        "dimension_name": dimension_name,
        "dimension_value": dimension_value,
        "confirmed_nofill_miss_class": miss_class_value,
        "row_count": count,
        "safe_flags": SAFE_FLAGS,
        "source_manifest_hash": source_manifest_hash,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
    }


def build_counter_rows(
    counters: dict[tuple[str, str, str | None], Counter[str]],
    source_manifest_hash: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seq = 1
    for (ledger_name, dimension_name, miss_class_value), counter in sorted(counters.items()):
        for dimension_value, count in sorted(counter.items()):
            rows.append(
                counter_row(
                    f"OHLC-GTOS-NOFILL-FAR-REDESIGN-BUCKET-{seq:05d}",
                    ledger_name,
                    dimension_name,
                    str(dimension_value),
                    int(count),
                    source_manifest_hash,
                    miss_class_value,
                )
            )
            seq += 1
    return rows


def main() -> int:
    generated_at = now_utc()
    manifest_rows, source_manifest_hash = source_manifest()

    friction_result = read_json(FRICTION_RESULT_PATH)
    source_alignment_result = read_json(SOURCE_ALIGNMENT_RESULT_PATH)
    m1_spread_result = read_json(M1_SPREAD_RESULT_PATH)

    friction_branch_rows = [row for row in read_jsonl(FRICTION_BRANCH_PATH) if not row.get("_parse_error")]
    friction_entry_rows = [row for row in read_jsonl(FRICTION_ENTRY_PATH) if not row.get("_parse_error")]
    friction_family_rows = [row for row in read_jsonl(FRICTION_FAMILY_PATH) if not row.get("_parse_error")]
    source_alignment_signature_rows = [row for row in read_jsonl(SOURCE_ALIGNMENT_SIGNATURE_PATH) if not row.get("_parse_error")]
    source_alignment_family_rows = [row for row in read_jsonl(SOURCE_ALIGNMENT_FAMILY_PATH) if not row.get("_parse_error")]
    m1_spread_family_rows = [row for row in read_jsonl(M1_SPREAD_FAMILY_PATH) if not row.get("_parse_error")]
    m1_spread_signature_rows = [row for row in read_jsonl(M1_SPREAD_SIGNATURE_PATH) if not row.get("_parse_error")]
    cost_family_rows = [row for row in read_jsonl(COST_SENSITIVITY_FAMILY_PATH) if not row.get("_parse_error")]
    recovered_family_rows = [row for row in read_jsonl(RECOVERED_CROSS_FAMILY_PATH) if not row.get("_parse_error")]
    path_ambiguity_rows_input = [row for row in read_jsonl(PATH_AMBIGUITY_PATH) if not row.get("_parse_error")]
    cost_split_ambiguity_rows = [row for row in read_jsonl(COST_SPLIT_AMBIGUITY_PATH) if not row.get("_parse_error")]
    cost_status_rows = [row for row in read_jsonl(COST_FILL_STATUS_PATH) if not row.get("_parse_error")]

    entry_by_id = {row.get("entry_variant_id"): row for row in friction_entry_rows}
    friction_family_by_key = {family_key(row): row for row in friction_family_rows}
    source_alignment_by_sig = {row.get("cost_sensitivity_signature_id"): row for row in source_alignment_signature_rows}
    source_alignment_family_by_key = {family_key(row): row for row in source_alignment_family_rows}
    recovered_family_by_key = {family_key(row): row for row in recovered_family_rows}
    cost_family_by_descriptor = {cost_family_descriptor_key(row): row for row in cost_family_rows}
    split_ambiguity_by_sig = {row.get("cost_sensitivity_signature_id"): row for row in cost_split_ambiguity_rows}

    path_ambiguity_by_family: Counter[str] = Counter()
    for row in path_ambiguity_rows_input:
        path_ambiguity_by_family[family_key(row)] += 1

    m1_family_summary: dict[str, dict[str, Any]] = {}
    for row in m1_spread_family_rows:
        key = family_key(row)
        summary = m1_family_summary.setdefault(
            key,
            {
                "signature_rows": 0,
                "cost_models": [],
                "m1_first_touch_status_counts": Counter(),
            },
        )
        summary["signature_rows"] += int(row.get("signature_rows") or 0)
        summary["cost_models"].append(row.get("cost_model"))
        summary["m1_first_touch_status_counts"].update(row.get("m1_first_touch_status_counts") or {})

    denominator_rows: list[dict[str, Any]] = []
    avoid_rows: list[dict[str, Any]] = []
    retest_rows: list[dict[str, Any]] = []
    source_confidence_rows: list[dict[str, Any]] = []
    branch_context_by_sig: dict[str, dict[str, Any]] = {}
    in_scope_rows: list[dict[str, Any]] = []

    counters: dict[tuple[str, str, str | None], Counter[str]] = defaultdict(Counter)

    for seq, row in enumerate(friction_branch_rows, 1):
        bucket = str(row.get("execution_friction_distance_bucket"))
        key = family_key(row)
        source_alignment_row = source_alignment_by_sig.get(row.get("cost_sensitivity_signature_id"))
        source_alignment_family = source_alignment_family_by_key.get(key)
        m1_summary = m1_family_summary.get(key)
        cost_family = cost_family_by_descriptor.get(cost_family_descriptor_key(row))
        recovered_family = recovered_family_by_key.get(key)
        split_ambiguity = split_ambiguity_by_sig.get(row.get("cost_sensitivity_signature_id"))
        path_ambiguity_count = int(path_ambiguity_by_family.get(key, 0))
        base = branch_base_row(
            row,
            source_manifest_hash,
            source_alignment_row,
            source_alignment_family,
            m1_summary,
            cost_family,
            recovered_family,
            split_ambiguity,
            path_ambiguity_count,
        )
        scope = denominator_scope(bucket)
        denom_row = {
            **base,
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_DENOMINATOR",
            "denominator_row_id": f"OHLC-GTOS-NOFILL-FAR-REDESIGN-DENOM-{seq:05d}",
            "denominator_scope": scope,
            "source_entry_distance_bucket": entry_by_id.get(row.get("entry_variant_id"), {}).get("execution_friction_distance_bucket"),
        }
        denominator_rows.append(denom_row)
        branch_context_by_sig[str(row.get("cost_sensitivity_signature_id"))] = base

        counters[("denominator", "denominator_scope", None)][scope] += 1
        counters[("denominator", "confirmed_nofill_miss_class", None)][base["confirmed_nofill_miss_class"]] += 1
        counters[("denominator", "authoritative_distance_source", base["confirmed_nofill_miss_class"])][
            str(base["authoritative_distance_source"])
        ] += 1
        counters[("denominator", "same_m15_ambiguity_context_status", base["confirmed_nofill_miss_class"])][
            str(base["same_m15_ambiguity_context_status"])
        ] += 1
        counters[("denominator", "exact_spread_context_status", base["confirmed_nofill_miss_class"])][
            str(base["exact_spread_context_status"])
        ] += 1

        if bucket not in IN_SCOPE_BUCKETS:
            continue

        in_scope_rows.append(base)
        src_status = str(base["source_confidence_branch_status"])
        amb_status = str(base["same_m15_ambiguity_context_status"])
        avoid_status = avoid_filter_status(row, src_status, amb_status)
        redesign_status = retest_redesign_status(row, src_status, amb_status)

        if bucket == FAR_BUCKET:
            avoid_rows.append(
                {
                    **base,
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_FILTER_BRANCH",
                    "avoid_filter_branch_id": f"OHLC-GTOS-NOFILL-FAR-AVOID-{len(avoid_rows) + 1:05d}",
                    "avoid_filter_branch_status": avoid_status,
                    "avoid_filter_design_boundary": (
                        "Branch-control row only: identifies far confirmed no-fill retest-limit contexts "
                        "for avoid-filter design review without scoring, ranking, validation, or live behavior."
                    ),
                }
            )
            counters[("avoid_filter", "avoid_filter_branch_status", base["confirmed_nofill_miss_class"])][avoid_status] += 1
            counters[("avoid_filter", "source_confidence_branch_status", base["confirmed_nofill_miss_class"])][src_status] += 1

        retest_rows.append(
            {
                **base,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_RETEST_REDESIGN_BRANCH",
                "retest_redesign_branch_id": f"OHLC-GTOS-NOFILL-RETEST-REDESIGN-{len(retest_rows) + 1:05d}",
                "retest_redesign_branch_status": redesign_status,
                "retest_redesign_design_boundary": (
                    "Branch-control row only: preserves a retest redesign route for the miss class "
                    "without scoring, ranking, validation, or live behavior."
                ),
            }
        )
        counters[("retest_redesign", "retest_redesign_branch_status", base["confirmed_nofill_miss_class"])][redesign_status] += 1
        counters[("retest_redesign", "source_confidence_branch_status", base["confirmed_nofill_miss_class"])][src_status] += 1

        source_confidence_rows.append(
            {
                **base,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_SOURCE_CONFIDENCE_BRANCH",
                "source_confidence_branch_id": f"OHLC-GTOS-NOFILL-SOURCE-CONFIDENCE-{len(source_confidence_rows) + 1:05d}",
                "source_confidence_design_boundary": (
                    "Source-confidence split only: exact tick and M1 bid-bar proxy rows remain separate; "
                    "no source is promoted to validation-safe performance evidence."
                ),
            }
        )
        counters[("source_confidence", "source_confidence_branch_status", base["confirmed_nofill_miss_class"])][src_status] += 1
        counters[("source_confidence", "same_m15_ambiguity_context_status", base["confirmed_nofill_miss_class"])][amb_status] += 1

    branch_rows_by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in denominator_rows:
        branch_rows_by_family[str(row["family_key"])].append(row)

    family_rows: list[dict[str, Any]] = []
    for seq, friction_family in enumerate(friction_family_rows, 1):
        key = family_key(friction_family)
        rows = branch_rows_by_family.get(key, [])
        cost_family = cost_family_by_descriptor.get(cost_family_descriptor_key(friction_family))
        recovered_family = recovered_family_by_key.get(key)
        source_alignment_family = source_alignment_family_by_key.get(key)
        m1_summary = m1_family_summary.get(key, {})
        class_counts = Counter(row.get("confirmed_nofill_miss_class") for row in rows)
        scope_counts = Counter(row.get("denominator_scope") for row in rows)
        source_counts = Counter(row.get("source_confidence_branch_status") for row in rows)
        ambiguity_counts = Counter(row.get("same_m15_ambiguity_context_status") for row in rows)
        exact_counts = Counter(row.get("exact_spread_context_status") for row in rows)
        family_rows.append(
            {
                "family_synthesis_id": f"OHLC-GTOS-NOFILL-FAR-REDESIGN-FAMILY-{seq:05d}",
                "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_FAMILY_SYNTHESIS",
                "source_manifest_hash": source_manifest_hash,
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "not_completion": True,
                "family_key": key,
                "route_candidate_id": friction_family.get("route_candidate_id"),
                "route_session": route_session(friction_family.get("route_candidate_id")),
                "symbol": friction_family.get("symbol"),
                "side": friction_family.get("side"),
                "entry_variant": friction_family.get("entry_variant"),
                "target_stop_contract_id": friction_family.get("target_stop_contract_id"),
                "target_multiple": friction_family.get("target_multiple"),
                "stop_multiple": friction_family.get("stop_multiple"),
                "friction_family_signature_rows": friction_family.get("signature_rows"),
                "friction_family_confirmed_nofill_signature_rows": friction_family.get("confirmed_nofill_signature_rows"),
                "friction_family_nonconfirmed_signature_rows": friction_family.get("nonconfirmed_signature_rows"),
                "denominator_branch_rows": len(rows),
                "denominator_scope_counts": dict(sorted(scope_counts.items())),
                "confirmed_nofill_miss_class_counts": dict(sorted(class_counts.items())),
                "source_confidence_branch_status_counts": dict(sorted(source_counts.items())),
                "same_m15_ambiguity_context_status_counts": dict(sorted(ambiguity_counts.items())),
                "exact_spread_context_status_counts": dict(sorted(exact_counts.items())),
                "max_confirmed_miss_distance_to_zero_entry_price": friction_family.get("max_confirmed_miss_distance_to_zero_entry_price"),
                "median_confirmed_miss_distance_to_zero_entry_price": friction_family.get("median_confirmed_miss_distance_to_zero_entry_price"),
                "min_confirmed_miss_distance_to_zero_entry_price": friction_family.get("min_confirmed_miss_distance_to_zero_entry_price"),
                "cost_sensitivity_family_route_status": cost_family.get("family_route_status") if cost_family else None,
                "cost_sensitivity_status_counts": cost_family.get("cost_sensitivity_status_counts") if cost_family else None,
                "cost_sensitivity_changed_signature_rows": cost_family.get("changed_signature_rows") if cost_family else None,
                "cost_sensitivity_gradient_signature_rows": cost_family.get("gradient_signature_rows") if cost_family else None,
                "cost_sensitivity_unfilled_signature_rows": cost_family.get("unfilled_signature_rows") if cost_family else None,
                "source_alignment_family_signature_rows": source_alignment_family.get("signature_rows") if source_alignment_family else 0,
                "source_alignment_family_status_counts": (
                    source_alignment_family.get("entry_alignment_status_counts") if source_alignment_family else {}
                ),
                "m1_spread_adjusted_family_signature_rows": m1_summary.get("signature_rows", 0),
                "m1_spread_adjusted_family_cost_models": sorted(set(m1_summary.get("cost_models", []))) if m1_summary else [],
                "m1_spread_adjusted_first_touch_status_counts": (
                    dict(sorted(m1_summary.get("m1_first_touch_status_counts", {}).items())) if m1_summary else {}
                ),
                "recovered_cross_family_status": recovered_family.get("cross_control_family_status") if recovered_family else None,
                "recovered_signature_rows": recovered_family.get("recovered_signature_rows") if recovered_family else None,
                "recovered_path_statuses": recovered_family.get("recovered_path_statuses") if recovered_family else None,
                "path_ambiguity_rows_for_family": int(path_ambiguity_by_family.get(key, 0)),
            }
        )

    question_rows = [
        {
            "question_id": "OHLC-GTOS-NOFILL-FAR-REDESIGN-Q001",
            "question": "For every far-miss branch, should the next source-safe packet test avoid-filter behavior against a non-retouched retest-limit denominator or redirect the branch to market-proxy redesign first?",
            "owning_next_packet": "far_miss_avoid_filter_stress_without_scoring_claims",
        },
        {
            "question_id": "OHLC-GTOS-NOFILL-FAR-REDESIGN-Q002",
            "question": "For every within-range branch, which entry-offset or wider-zone redesign preserves source confidence while avoiding same-M15 target/stop order ambiguity leakage?",
            "owning_next_packet": "within_range_retest_redesign_source_safe_branch_controls",
        },
        {
            "question_id": "OHLC-GTOS-NOFILL-FAR-REDESIGN-Q003",
            "question": "Which far/within branches are exact-tick confirmed versus M1 bid-bar proxy confirmed, and should those source classes remain separately routed in all later packets?",
            "owning_next_packet": "source_confidence_split_carry_forward",
        },
        {
            "question_id": "OHLC-GTOS-NOFILL-FAR-REDESIGN-Q004",
            "question": "Which families combine far/within no-fill, source-alignment replay context, M1 spread-adjusted target/stop ambiguity, and exact-spread unavailable stress context?",
            "owning_next_packet": "cost_fill_path_family_synthesis_join",
        },
        {
            "question_id": "OHLC-GTOS-NOFILL-FAR-REDESIGN-Q005",
            "question": "Do the near-miss and source-alignment conflict buckets need separate packets before any combined no-fill lifecycle synthesis?",
            "owning_next_packet": "near_miss_and_source_alignment_parallel_packets",
        },
        {
            "question_id": "OHLC-GTOS-NOFILL-FAR-REDESIGN-Q006",
            "question": "Which families have same-M15 ambiguity context and therefore require interval/order stress before any later target/stop descriptor comparison?",
            "owning_next_packet": "same_m15_ambiguity_stress_controls",
        },
    ]
    for row in question_rows:
        row.update(
            {
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_QUESTION",
                "source_manifest_hash": source_manifest_hash,
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "not_completion": True,
            }
        )

    bucket_rows = build_counter_rows(counters, source_manifest_hash)

    in_scope_class_counts = Counter(row["confirmed_nofill_miss_class"] for row in in_scope_rows)
    denominator_scope_counts = Counter(row["denominator_scope"] for row in denominator_rows)
    avoid_status_counts = Counter(row["avoid_filter_branch_status"] for row in avoid_rows)
    retest_status_counts = Counter(row["retest_redesign_branch_status"] for row in retest_rows)
    source_status_counts = Counter(row["source_confidence_branch_status"] for row in source_confidence_rows)
    ambiguity_status_counts = Counter(row["same_m15_ambiguity_context_status"] for row in source_confidence_rows)
    exact_context_counts = Counter(row["exact_spread_context_status"] for row in source_confidence_rows)

    counts = {
        "source_manifest_rows": len(manifest_rows),
        "friction_branch_input_rows": len(friction_branch_rows),
        "friction_entry_input_rows": len(friction_entry_rows),
        "friction_family_input_rows": len(friction_family_rows),
        "source_alignment_signature_input_rows": len(source_alignment_signature_rows),
        "source_alignment_cost_model_input_rows": len([row for row in read_jsonl(SOURCE_ALIGNMENT_COST_MODEL_PATH) if not row.get("_parse_error")]),
        "source_alignment_family_input_rows": len(source_alignment_family_rows),
        "m1_spread_signature_input_rows": len(m1_spread_signature_rows),
        "m1_spread_family_input_rows": len(m1_spread_family_rows),
        "cost_sensitivity_family_input_rows": len(cost_family_rows),
        "cost_fill_status_input_rows": len(cost_status_rows),
        "recovered_cross_family_input_rows": len(recovered_family_rows),
        "path_ambiguity_input_rows": len(path_ambiguity_rows_input),
        "cost_split_ambiguity_input_rows": len(cost_split_ambiguity_rows),
        "denominator_rows": len(denominator_rows),
        "in_scope_far_and_within_rows": len(in_scope_rows),
        "avoid_filter_branch_rows": len(avoid_rows),
        "retest_redesign_branch_rows": len(retest_rows),
        "source_confidence_branch_rows": len(source_confidence_rows),
        "family_synthesis_rows": len(family_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
    }

    output = {
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "schema": "historical_ohlc_gtos_replay_confirmed_nofill_far_miss_avoid_redesign_v1",
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_ONLY",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": NOT_COMPLETION,
        "counts": counts,
        "denominator_scope_counts": dict(sorted(denominator_scope_counts.items())),
        "in_scope_confirmed_nofill_miss_class_counts": dict(sorted(in_scope_class_counts.items())),
        "avoid_filter_branch_status_counts": dict(sorted(avoid_status_counts.items())),
        "retest_redesign_branch_status_counts": dict(sorted(retest_status_counts.items())),
        "source_confidence_branch_status_counts": dict(sorted(source_status_counts.items())),
        "source_confidence_ambiguity_context_counts": dict(sorted(ambiguity_status_counts.items())),
        "exact_spread_context_counts": dict(sorted(exact_context_counts.items())),
        "upstream_friction_counts": friction_result.get("counts", {}),
        "upstream_source_alignment_counts": source_alignment_result.get("counts", {}),
        "upstream_m1_spread_replay_counts": m1_spread_result.get("counts", {}),
        "source_manifest": manifest_rows,
        "source_manifest_hash": source_manifest_hash,
        "full_denominator_policy": (
            "The denominator ledger preserves every confirmed no-fill friction branch row. "
            "Far-miss and within-range miss classes are routed without top-N truncation; near-miss "
            "and source-alignment conflict buckets remain explicit out-of-scope denominator rows."
        ),
        "next_same_resource_work": [
            "stress far-miss avoid-filter branch rows without converting them into validation, score, rank, R/PnL, or live logic",
            "materialize within-range retest redesign variants while carrying source-confidence and same-M15 ambiguity splits forward",
            "build the separate near-miss market-entry/entry-offset packet from its full denominator",
            "join this packet with M1 spread-adjusted replay order-ambiguity repair and cost/fill/path family synthesis",
        ],
    }

    write_jsonl(SOURCE_MANIFEST_PATH, manifest_rows)
    write_jsonl(DENOMINATOR_PATH, denominator_rows)
    write_jsonl(AVOID_BRANCH_PATH, avoid_rows)
    write_jsonl(RETEST_BRANCH_PATH, retest_rows)
    write_jsonl(SOURCE_CONFIDENCE_PATH, source_confidence_rows)
    write_jsonl(FAMILY_PATH, family_rows)
    write_jsonl(BUCKET_PATH, bucket_rows)
    write_jsonl(QUESTION_PATH, question_rows)
    RESULT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Confirmed No-Fill Far-Miss Avoid/Retest Redesign",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                "This branch-local packet preserves the full confirmed no-fill friction denominator and routes far-miss and within-range miss rows into separate avoid/retest redesign and source-confidence ledgers.",
                "",
                "## Counts",
                "",
                *(f"- `{key}`: `{value}`" for key, value in counts.items()),
                "",
                "## In-Scope Miss Classes",
                "",
                *(f"- `{key}`: `{value}`" for key, value in sorted(in_scope_class_counts.items())),
                "",
                "## Claim Boundary",
                "",
                CLAIM_BOUNDARY,
                "",
                "## Not Completion",
                "",
                NOT_COMPLETION,
                "",
                "No scoring, ranking, validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(json.dumps({"ok": True, "counts": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
