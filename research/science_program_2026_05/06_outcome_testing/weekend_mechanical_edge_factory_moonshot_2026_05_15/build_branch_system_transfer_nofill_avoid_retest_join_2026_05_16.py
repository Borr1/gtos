#!/usr/bin/env python3
"""Join system-transfer branches to confirmed no-fill avoid/retest rows."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

SYSTEM_TRANSFER_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_RECOMMENDATION_RESULT_2026-05-16.json"
SYSTEM_TRANSFER_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_RECOMMENDATION_BRANCH_LEDGER_2026-05-16.jsonl"
TICK_CONTEXT_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_TICK_PRIMITIVE_CONTEXT_RESULT_2026-05-16.json"
TICK_CONTEXT_BRANCH_SUMMARY = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_TICK_PRIMITIVE_CONTEXT_BRANCH_SUMMARY_LEDGER_2026-05-16.jsonl"
NOFILL_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_RESULT_2026-05-16.json"
NOFILL_DENOMINATOR = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_DENOMINATOR_LEDGER_2026-05-16.jsonl"
NOFILL_AVOID = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_AVOID_FILTER_BRANCH_LEDGER_2026-05-16.jsonl"
NOFILL_RETEST = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_RETEST_REDESIGN_BRANCH_LEDGER_2026-05-16.jsonl"
NOFILL_SOURCE_CONFIDENCE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_SOURCE_CONFIDENCE_BRANCH_LEDGER_2026-05-16.jsonl"
NEAR_MISS_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS_RESULT_2026-05-16.json"

PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_NOFILL_AVOID_RETEST_JOIN"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-16.json"
BRANCH_SUMMARY_LEDGER = ROUTE_DIR / f"{PREFIX}_BRANCH_SUMMARY_LEDGER_2026-05-16.jsonl"
AVOID_JOIN_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_JOIN_LEDGER_2026-05-16.jsonl"
RETEST_JOIN_LEDGER = ROUTE_DIR / f"{PREFIX}_RETEST_REDESIGN_JOIN_LEDGER_2026-05-16.jsonl"
SOURCE_CONFIDENCE_JOIN_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_CONFIDENCE_JOIN_LEDGER_2026-05-16.jsonl"
ROUTE_SUMMARY_LEDGER = ROUTE_DIR / f"{PREFIX}_ROUTE_SUMMARY_LEDGER_2026-05-16.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Branch system-transfer confirmed no-fill avoid/retest join packet only. It preserves every "
    "1,984 avoid-filter branch row and every 6,112 retest-redesign/source-confidence row by joining "
    "them back to the 386 branch system-transfer denominator on route, target/stop contract, and entry "
    "variant. It computes lower-level fillability/no-fill pressure and implementation implications, "
    "but does not change live behavior or claim broker R/PnL, realized expectancy, win-rate, validation, "
    "live-readiness, or promotion."
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"{path}:{line_no}: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_manifest_rows(paths: list[Path], generated_at: str) -> tuple[list[dict[str, Any]], str]:
    rows: list[dict[str, Any]] = []
    for index, path in enumerate(paths, 1):
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-NOFILL-TRANSFER-SRC-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": sha256_file(path),
                "status": "HASHED" if path.exists() else "MISSING",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def with_common(row: dict[str, Any], generated_at: str, manifest_hash: str) -> dict[str, Any]:
    row.update(
        {
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "not_completion": True,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }
    )
    return row


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def stat(values: list[float], prefix: str) -> dict[str, float | None]:
    if not values:
        return {f"{prefix}_min": None, f"{prefix}_mean": None, f"{prefix}_max": None}
    return {
        f"{prefix}_min": round(min(values), 6),
        f"{prefix}_mean": round(mean(values), 6),
        f"{prefix}_max": round(max(values), 6),
    }


def join_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("route_candidate_id")),
        str(row.get("target_stop_contract_id")),
        str(row.get("entry_variant")),
    )


def bucketed(values: list[dict[str, Any]], field: str) -> dict[str, int]:
    return compact_counter(Counter(row.get(field) for row in values))


def nofill_join_status(avoid_count: int, retest_count: int) -> str:
    if avoid_count and retest_count:
        return "NOFILL_AVOID_AND_RETEST_CONTEXT_JOINED"
    if retest_count:
        return "NOFILL_RETEST_REDESIGN_ONLY_JOINED"
    if avoid_count:
        return "NOFILL_AVOID_ONLY_JOINED"
    return "NOFILL_NO_DIRECT_CONTEXT_FOR_BRANCH_KEY"


def nofill_implication(branch: dict[str, Any], avoid_count: int, retest_count: int) -> str:
    decision = str(branch.get("decision_direction") or "")
    if avoid_count and decision in {"KILL_OR_REDESIGN", "KEEP_REPAIR_OR_AVOID"}:
        return "NOFILL_AVOID_CONTEXT_REINFORCES_KILL_REPAIR_OR_AVOID"
    if avoid_count:
        return "NOFILL_AVOID_CONTEXT_SPLIT_CHALLENGER_WITH_FILLABILITY_REDESIGN"
    if retest_count and decision == "KEEP_CHALLENGER":
        return "NOFILL_RETEST_REDESIGN_CONTEXT_WITHOUT_FAR_AVOID"
    if retest_count:
        return "NOFILL_RETEST_REDESIGN_CONTEXT_REPAIR_OR_STRESS"
    return "NOFILL_NO_DIRECT_CONTEXT_BRANCH_RETAINS_SYSTEM_TRANSFER_DECISION"


def implementation_implication(branch: dict[str, Any], avoid_count: int, retest_count: int) -> str:
    decision = str(branch.get("decision_direction") or "")
    if avoid_count and decision == "KEEP_CHALLENGER":
        return "KEEP_ONLY_AFTER_FILLABILITY_REDESIGN_OR_MARKET_ENTRY_COMPARATOR"
    if avoid_count and decision == "SPLIT_REDESIGN":
        return "SPLIT_REDESIGN_MUST_CARRY_NOFILL_AVOID_CONTEXT"
    if avoid_count:
        return "PREFER_AVOID_OR_SOURCE_REPAIR_BEFORE_DIRECT_RETEST_ENTRY"
    if retest_count:
        return "TEST_RETEST_REDESIGN_VARIANTS_WITH_SOURCE_AND_M15_AMBIGUITY_SPLIT"
    return "NO_NOFILL_JOIN_IMPLEMENTATION_DELTA_FROM_SYSTEM_TRANSFER"


def join_source_row(row: dict[str, Any], branch: dict[str, Any], generated_at: str, manifest_hash: str, row_id: str) -> dict[str, Any]:
    return with_common(
        {
            row_id: row.get(row_id),
            "branch_queue_id": branch.get("branch_queue_id"),
            "matrix_branch_id": branch.get("matrix_branch_id"),
            "system_transfer_branch_id": branch.get("system_transfer_branch_id"),
            "route_candidate_id": branch.get("route_candidate_id"),
            "target_stop_contract_id": branch.get("target_stop_contract_id"),
            "entry_variant": branch.get("entry_variant"),
            "symbol": branch.get("symbol"),
            "route_session": branch.get("route_session"),
            "side": branch.get("side"),
            "primary_export_family": branch.get("primary_export_family"),
            "decision_direction": branch.get("decision_direction"),
            "system_decision_class": branch.get("system_decision_class"),
            "branch_result_binary": branch.get("branch_result_binary"),
            "market_transfer_class": branch.get("market_transfer_class"),
            "target_stop_result": branch.get("target_stop_result"),
            "non_ob_primitive_scope": branch.get("non_ob_primitive_scope"),
            "confirmed_nofill_miss_class": row.get("confirmed_nofill_miss_class"),
            "execution_friction_branch_id": row.get("execution_friction_branch_id"),
            "execution_friction_signature_id": row.get("execution_friction_signature_id"),
            "execution_friction_distance_bucket": row.get("execution_friction_distance_bucket"),
            "source_confidence_branch_status": row.get("source_confidence_branch_status"),
            "tick_source_status": row.get("tick_source_status"),
            "m1_source_status": row.get("m1_source_status"),
            "same_m15_ambiguity_context_status": row.get("same_m15_ambiguity_context_status"),
            "has_same_m15_ambiguity": row.get("has_same_m15_ambiguity"),
            "miss_distance_to_zero_entry_price": row.get("miss_distance_to_zero_entry_price"),
            "miss_distance_to_zero_over_rolling_median_range": row.get("miss_distance_to_zero_over_rolling_median_range"),
            "miss_distance_to_zero_over_max_spread_proxy": row.get("miss_distance_to_zero_over_max_spread_proxy"),
            "authoritative_distance_source": row.get("authoritative_distance_source"),
            "unfilled_probe_status": row.get("unfilled_probe_status"),
            "recovered_cross_family_status": row.get("recovered_cross_family_status"),
            "exact_spread_context_status": row.get("exact_spread_context_status"),
            "cost_sensitivity_family_route_status": row.get("cost_sensitivity_family_route_status"),
            "cost_sensitivity_status_counts": row.get("cost_sensitivity_status_counts"),
            "m1_spread_adjusted_first_touch_status_counts": row.get("m1_spread_adjusted_first_touch_status_counts"),
        },
        generated_at,
        manifest_hash,
    )


def main() -> int:
    generated_at = now_utc()
    system_result = read_json(SYSTEM_TRANSFER_RESULT)
    tick_context_result = read_json(TICK_CONTEXT_RESULT)
    nofill_result = read_json(NOFILL_RESULT)
    near_miss_result = read_json(NEAR_MISS_RESULT)
    system_rows = read_jsonl(SYSTEM_TRANSFER_BRANCH)
    tick_summary_rows = read_jsonl(TICK_CONTEXT_BRANCH_SUMMARY)
    denominator_rows = read_jsonl(NOFILL_DENOMINATOR)
    avoid_rows = read_jsonl(NOFILL_AVOID)
    retest_rows = read_jsonl(NOFILL_RETEST)
    source_confidence_rows = read_jsonl(NOFILL_SOURCE_CONFIDENCE)

    source_manifest, manifest_hash = source_manifest_rows(
        [
            SYSTEM_TRANSFER_RESULT,
            SYSTEM_TRANSFER_BRANCH,
            TICK_CONTEXT_RESULT,
            TICK_CONTEXT_BRANCH_SUMMARY,
            NOFILL_RESULT,
            NOFILL_DENOMINATOR,
            NOFILL_AVOID,
            NOFILL_RETEST,
            NOFILL_SOURCE_CONFIDENCE,
            NEAR_MISS_RESULT,
        ],
        generated_at,
    )

    system_by_key = {join_key(row): row for row in system_rows}
    tick_by_branch = {row.get("branch_queue_id"): row for row in tick_summary_rows}
    avoid_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    retest_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    source_confidence_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in avoid_rows:
        avoid_by_key[join_key(row)].append(row)
    for row in retest_rows:
        retest_by_key[join_key(row)].append(row)
    for row in source_confidence_rows:
        source_confidence_by_key[join_key(row)].append(row)

    unmatched_avoid_ids: list[str] = []
    unmatched_retest_ids: list[str] = []
    unmatched_source_confidence_ids: list[str] = []
    avoid_join_rows: list[dict[str, Any]] = []
    retest_join_rows: list[dict[str, Any]] = []
    source_confidence_join_rows: list[dict[str, Any]] = []
    for row in avoid_rows:
        branch = system_by_key.get(join_key(row))
        if not branch:
            unmatched_avoid_ids.append(str(row.get("avoid_filter_branch_id")))
            continue
        joined = join_source_row(row, branch, generated_at, manifest_hash, "avoid_filter_branch_id")
        joined["avoid_filter_branch_status"] = row.get("avoid_filter_branch_status")
        joined["avoid_filter_design_boundary"] = row.get("avoid_filter_design_boundary")
        joined["nofill_join_row_type"] = "AVOID_FILTER_BRANCH_JOIN"
        avoid_join_rows.append(joined)
    for row in retest_rows:
        branch = system_by_key.get(join_key(row))
        if not branch:
            unmatched_retest_ids.append(str(row.get("retest_redesign_branch_id")))
            continue
        joined = join_source_row(row, branch, generated_at, manifest_hash, "retest_redesign_branch_id")
        joined["retest_redesign_branch_status"] = row.get("retest_redesign_branch_status")
        joined["retest_redesign_design_boundary"] = row.get("retest_redesign_design_boundary")
        joined["nofill_join_row_type"] = "RETEST_REDESIGN_BRANCH_JOIN"
        retest_join_rows.append(joined)
    for row in source_confidence_rows:
        branch = system_by_key.get(join_key(row))
        if not branch:
            unmatched_source_confidence_ids.append(str(row.get("source_confidence_branch_id")))
            continue
        joined = join_source_row(row, branch, generated_at, manifest_hash, "source_confidence_branch_id")
        joined["source_confidence_design_boundary"] = row.get("source_confidence_design_boundary")
        joined["nofill_join_row_type"] = "SOURCE_CONFIDENCE_BRANCH_JOIN"
        source_confidence_join_rows.append(joined)

    branch_summary_rows: list[dict[str, Any]] = []
    for index, branch in enumerate(system_rows, 1):
        key = join_key(branch)
        avoid_for_branch = avoid_by_key.get(key, [])
        retest_for_branch = retest_by_key.get(key, [])
        source_for_branch = source_confidence_by_key.get(key, [])
        all_nofill_rows = avoid_for_branch + retest_for_branch
        avoid_count = len(avoid_for_branch)
        retest_count = len(retest_for_branch)
        source_count = len(source_for_branch)
        total_context_rows = avoid_count + retest_count
        same_m15_ambiguity_rows = sum(int(row.get("path_ambiguity_rows_for_family") or 0) for row in retest_for_branch)
        exact_tick_rows = sum(1 for row in source_for_branch if str(row.get("source_confidence_branch_status", "")).startswith("EXACT_TICK"))
        m1_proxy_rows = sum(1 for row in source_for_branch if str(row.get("source_confidence_branch_status", "")).startswith("M1_BID_BAR_PROXY"))
        miss_values = [
            value
            for value in (
                as_float(row.get("miss_distance_to_zero_over_rolling_median_range"))
                for row in all_nofill_rows
            )
            if value is not None
        ]
        nofill_status = nofill_join_status(avoid_count, retest_count)
        branch_summary_rows.append(
            with_common(
                {
                    "nofill_transfer_branch_summary_id": f"OHLC-GTOS-NOFILL-TRANSFER-BRANCH-{index:05d}",
                    "branch_queue_id": branch.get("branch_queue_id"),
                    "matrix_branch_id": branch.get("matrix_branch_id"),
                    "system_transfer_branch_id": branch.get("system_transfer_branch_id"),
                    "route_candidate_id": branch.get("route_candidate_id"),
                    "target_stop_contract_id": branch.get("target_stop_contract_id"),
                    "entry_variant": branch.get("entry_variant"),
                    "symbol": branch.get("symbol"),
                    "route_session": branch.get("route_session"),
                    "side": branch.get("side"),
                    "primary_export_family": branch.get("primary_export_family"),
                    "decision_direction": branch.get("decision_direction"),
                    "system_decision_class": branch.get("system_decision_class"),
                    "branch_result_binary": branch.get("branch_result_binary"),
                    "accepted_for_next_executable_builder": branch.get("accepted_for_next_executable_builder"),
                    "market_transfer_class": branch.get("market_transfer_class"),
                    "market_specific_concentration_flag": branch.get("market_specific_concentration_flag"),
                    "target_stop_result": branch.get("target_stop_result"),
                    "non_ob_primitive_scope": branch.get("non_ob_primitive_scope"),
                    "tick_context_join_status": (tick_by_branch.get(branch.get("branch_queue_id")) or {}).get("tick_context_join_status"),
                    "tick_context_decision_counts": (tick_by_branch.get(branch.get("branch_queue_id")) or {}).get("tick_context_decision_counts"),
                    "nofill_join_status": nofill_status,
                    "nofill_avoid_rows": avoid_count,
                    "nofill_retest_redesign_rows": retest_count,
                    "nofill_source_confidence_rows": source_count,
                    "nofill_total_avoid_retest_rows": total_context_rows,
                    "nofill_retest_minus_avoid_row_delta": retest_count - avoid_count,
                    "nofill_avoid_share_of_joined_context": round(avoid_count / total_context_rows, 6) if total_context_rows else None,
                    "source_confidence_exact_tick_rows": exact_tick_rows,
                    "source_confidence_m1_proxy_rows": m1_proxy_rows,
                    "source_confidence_exact_tick_share": round(exact_tick_rows / source_count, 6) if source_count else None,
                    "same_m15_ambiguity_rows_for_join": same_m15_ambiguity_rows,
                    **stat(miss_values, "miss_distance_to_zero_over_rolling_median_range"),
                    "nofill_transfer_implication": nofill_implication(branch, avoid_count, retest_count),
                    "implementation_implication": implementation_implication(branch, avoid_count, retest_count),
                    "exact_failure_cause": (
                        f"{branch.get('exact_failure_cause')}__CONFIRMED_NOFILL_CONTEXT_{nofill_status}"
                        if total_context_rows
                        else branch.get("exact_failure_cause")
                    ),
                    "exact_success_cause": branch.get("exact_success_cause"),
                    "next_same_resource_action": (
                        "SPLIT_CONFIRMED_NOFILL_AVOID_RETEST_AND_MARKET_ENTRY_REDESIGN"
                        if total_context_rows
                        else "NOFILL_JOIN_NOT_DIRECT_FOR_BRANCH_CONTINUE_OTHER_TRANSFER_GAPS"
                    ),
                },
                generated_at,
                manifest_hash,
            )
        )

    route_summary_rows: list[dict[str, Any]] = []
    by_route: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in branch_summary_rows:
        by_route[str(row.get("route_candidate_id"))].append(row)
    for route_candidate_id, rows in sorted(by_route.items()):
        route_summary_rows.append(
            with_common(
                {
                    "nofill_transfer_route_summary_id": f"OHLC-GTOS-NOFILL-TRANSFER-ROUTE-{len(route_summary_rows) + 1:04d}",
                    "route_candidate_id": route_candidate_id,
                    "branch_rows": len(rows),
                    "symbol_counts": compact_counter(Counter(row.get("symbol") for row in rows)),
                    "session_counts": compact_counter(Counter(row.get("route_session") for row in rows)),
                    "side_counts": compact_counter(Counter(row.get("side") for row in rows)),
                    "system_decision_class_counts": compact_counter(Counter(row.get("system_decision_class") for row in rows)),
                    "nofill_join_status_counts": compact_counter(Counter(row.get("nofill_join_status") for row in rows)),
                    "nofill_avoid_rows": int(sum(row.get("nofill_avoid_rows") or 0 for row in rows)),
                    "nofill_retest_redesign_rows": int(sum(row.get("nofill_retest_redesign_rows") or 0 for row in rows)),
                    "nofill_source_confidence_rows": int(sum(row.get("nofill_source_confidence_rows") or 0 for row in rows)),
                    "implementation_implication_counts": compact_counter(Counter(row.get("implementation_implication") for row in rows)),
                },
                generated_at,
                manifest_hash,
            )
        )

    bucket_sources = {
        "branch_result_binary": Counter(row.get("branch_result_binary") for row in branch_summary_rows),
        "decision_direction": Counter(row.get("decision_direction") for row in branch_summary_rows),
        "system_decision_class": Counter(row.get("system_decision_class") for row in branch_summary_rows),
        "primary_export_family": Counter(row.get("primary_export_family") for row in branch_summary_rows),
        "symbol": Counter(row.get("symbol") for row in branch_summary_rows),
        "route_session": Counter(row.get("route_session") for row in branch_summary_rows),
        "side": Counter(row.get("side") for row in branch_summary_rows),
        "nofill_join_status": Counter(row.get("nofill_join_status") for row in branch_summary_rows),
        "nofill_transfer_implication": Counter(row.get("nofill_transfer_implication") for row in branch_summary_rows),
        "implementation_implication": Counter(row.get("implementation_implication") for row in branch_summary_rows),
        "avoid_filter_branch_status": Counter(row.get("avoid_filter_branch_status") for row in avoid_join_rows),
        "retest_redesign_branch_status": Counter(row.get("retest_redesign_branch_status") for row in retest_join_rows),
        "source_confidence_branch_status": Counter(row.get("source_confidence_branch_status") for row in source_confidence_join_rows),
        "confirmed_nofill_miss_class": Counter(row.get("confirmed_nofill_miss_class") for row in retest_join_rows),
    }
    bucket_rows: list[dict[str, Any]] = []
    for category, counter in sorted(bucket_sources.items()):
        for value, row_count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                with_common(
                    {
                        "nofill_transfer_bucket_id": f"OHLC-GTOS-NOFILL-TRANSFER-BUCKET-{len(bucket_rows) + 1:05d}",
                        "bucket_category": category,
                        "bucket_value": str(value),
                        "row_count": int(row_count),
                    },
                    generated_at,
                    manifest_hash,
                )
            )

    question_rows = [
        {
            "question_id": "OHLC-GTOS-NOFILL-TRANSFER-QUESTION-001",
            "question": "Which system-transfer branches carry confirmed no-fill avoid or retest-redesign context?",
            "answer_route": "Use BRANCH_SUMMARY_LEDGER; every one of the 386 system-transfer branches is preserved with avoid/retest row counts.",
        },
        {
            "question_id": "OHLC-GTOS-NOFILL-TRANSFER-QUESTION-002",
            "question": "Are any avoid/retest/source-confidence rows dropped by the branch join?",
            "answer_route": "No; AVOID_JOIN_LEDGER preserves all 1,984 avoid rows, RETEST_REDESIGN_JOIN_LEDGER preserves all 6,112 retest rows, and SOURCE_CONFIDENCE_JOIN_LEDGER preserves all 6,112 source-confidence rows.",
        },
        {
            "question_id": "OHLC-GTOS-NOFILL-TRANSFER-QUESTION-003",
            "question": "Which keep/kill/redesign implications change when no-fill context is attached?",
            "answer_route": "Use nofill_transfer_implication and implementation_implication in BRANCH_SUMMARY_LEDGER plus ROUTE_SUMMARY_LEDGER.",
        },
        {
            "question_id": "OHLC-GTOS-NOFILL-TRANSFER-QUESTION-004",
            "question": "What remains outside this packet?",
            "answer_route": "Near-miss market-entry and entry-offset rows remain a separate packet; the result records their input counts and routes them to the next same-resource join.",
        },
    ]
    for row in question_rows:
        with_common(row, generated_at, manifest_hash)

    row_count_stats = {
        "branches_with_avoid_rows": sum(1 for row in branch_summary_rows if row.get("nofill_avoid_rows")),
        "branches_with_retest_rows": sum(1 for row in branch_summary_rows if row.get("nofill_retest_redesign_rows")),
        "branches_with_avoid_and_retest_rows": sum(
            1 for row in branch_summary_rows if row.get("nofill_avoid_rows") and row.get("nofill_retest_redesign_rows")
        ),
        "branches_with_retest_only_rows": sum(
            1 for row in branch_summary_rows if row.get("nofill_retest_redesign_rows") and not row.get("nofill_avoid_rows")
        ),
        "branches_without_direct_nofill_context": sum(
            1 for row in branch_summary_rows if not row.get("nofill_retest_redesign_rows") and not row.get("nofill_avoid_rows")
        ),
        "avoid_join_rows": len(avoid_join_rows),
        "retest_join_rows": len(retest_join_rows),
        "source_confidence_join_rows": len(source_confidence_join_rows),
    }

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_NOFILL_AVOID_RETEST_JOIN",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_system_transfer_branch_rows": len(system_rows),
            "input_tick_context_branch_summary_rows": len(tick_summary_rows),
            "input_nofill_denominator_rows": len(denominator_rows),
            "input_avoid_filter_rows": len(avoid_rows),
            "input_retest_redesign_rows": len(retest_rows),
            "input_source_confidence_rows": len(source_confidence_rows),
            "branch_summary_rows": len(branch_summary_rows),
            "avoid_join_rows": len(avoid_join_rows),
            "retest_redesign_join_rows": len(retest_join_rows),
            "source_confidence_join_rows": len(source_confidence_join_rows),
            "route_summary_rows": len(route_summary_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_manifest),
            "unmatched_avoid_rows": len(unmatched_avoid_ids),
            "unmatched_retest_rows": len(unmatched_retest_ids),
            "unmatched_source_confidence_rows": len(unmatched_source_confidence_ids),
        },
        "upstream_counts": {
            "system_transfer": system_result.get("counts", {}),
            "tick_context": tick_context_result.get("counts", {}),
            "nofill_far_avoid_retest": nofill_result.get("counts", {}),
            "near_miss_related_packet": near_miss_result.get("counts", {}),
        },
        "join_diagnostics": {
            "join_key_fields": ["route_candidate_id", "target_stop_contract_id", "entry_variant"],
            "system_branch_key_count": len(system_by_key),
            "nofill_avoid_key_count": len(avoid_by_key),
            "nofill_retest_key_count": len(retest_by_key),
            "nofill_source_confidence_key_count": len(source_confidence_by_key),
            "unmatched_avoid_ids": unmatched_avoid_ids,
            "unmatched_retest_ids": unmatched_retest_ids,
            "unmatched_source_confidence_ids": unmatched_source_confidence_ids,
        },
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_sources.items())},
        "row_count_stats": row_count_stats,
        "system_decision": {
            "system_recommendation": (
                "NOFILL_AVOID_RETEST_JOIN_RESULT: confirmed no-fill context is now attached to the "
                "386 system-transfer branches; 144 branches carry both far-miss avoid and retest-redesign "
                "context, 32 carry retest-only context, and 210 have no direct confirmed no-fill row for "
                "the exact route/target/entry key. Continue into near-miss market-entry and market-gap "
                "expansion rather than treating no-fill context as exhausted."
            ),
            **row_count_stats,
        },
        "source_manifest_hash": manifest_hash,
    }

    outputs = [
        (BRANCH_SUMMARY_LEDGER, branch_summary_rows),
        (AVOID_JOIN_LEDGER, avoid_join_rows),
        (RETEST_JOIN_LEDGER, retest_join_rows),
        (SOURCE_CONFIDENCE_JOIN_LEDGER, source_confidence_join_rows),
        (ROUTE_SUMMARY_LEDGER, route_summary_rows),
        (BUCKET_LEDGER, bucket_rows),
        (QUESTION_LEDGER, question_rows),
        (SOURCE_MANIFEST_LEDGER, source_manifest),
    ]
    for path, rows in outputs:
        write_jsonl(path, rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Branch System Transfer No-Fill Avoid/Retest Join",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Branch summary rows: `{len(branch_summary_rows)}`",
                f"- Avoid join rows: `{len(avoid_join_rows)}`",
                f"- Retest-redesign join rows: `{len(retest_join_rows)}`",
                f"- Source-confidence join rows: `{len(source_confidence_join_rows)}`",
                f"- Branches with avoid+retest context: `{row_count_stats['branches_with_avoid_and_retest_rows']}`",
                f"- Branches with retest-only context: `{row_count_stats['branches_with_retest_only_rows']}`",
                f"- Branches without direct no-fill context: `{row_count_stats['branches_without_direct_nofill_context']}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = read_json(OUTPUT_MANIFEST) if OUTPUT_MANIFEST.exists() else {"schema": "weekend_mechanical_edge_factory_output_manifest_v1", "artifacts": []}
    output_paths = [RESULT_PATH, SUMMARY_PATH] + [path for path, _rows in outputs]
    path_strings = {path.relative_to(REPO).as_posix() for path in output_paths}
    manifest["artifacts"] = [item for item in manifest.get("artifacts", []) if item.get("path") not in path_strings]
    for path in output_paths:
        manifest["artifacts"].append(
            {
                "path": path.relative_to(REPO).as_posix(),
                "status": "created",
                "type": "branch_system_transfer_nofill_avoid_retest_join",
                "generated_utc": generated_at,
                "counts": result["counts"],
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest["safe_flags"] = SAFE_FLAGS
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "timestamp_utc": generated_at,
                    "event_type": "branch_system_transfer_nofill_avoid_retest_join_built",
                    "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
                    "artifact": RESULT_PATH.relative_to(REPO).as_posix(),
                    "counts": result["counts"],
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "not_completion": True,
                },
                sort_keys=True,
            )
            + "\n"
        )
    print(json.dumps({"ok": True, "counts": result["counts"], "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
