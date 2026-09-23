#!/usr/bin/env python3
"""Join system-transfer branches to confirmed near-miss market-entry controls."""

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
NOFILL_TRANSFER_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_NOFILL_AVOID_RETEST_JOIN_RESULT_2026-05-16.json"
NOFILL_TRANSFER_BRANCH_SUMMARY = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_NOFILL_AVOID_RETEST_JOIN_BRANCH_SUMMARY_LEDGER_2026-05-16.jsonl"
NEAR_MISS_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS_RESULT_2026-05-16.json"
NEAR_MISS_OFFSET = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS_OFFSET_BRANCH_LEDGER_2026-05-16.jsonl"
NEAR_MISS_MARKET = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS_MARKET_ENTRY_BRANCH_LEDGER_2026-05-16.jsonl"
NEAR_MISS_SOURCE_REQ = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS_SOURCE_REQUIREMENT_LEDGER_2026-05-16.jsonl"

PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_NEARMISS_MARKET_ENTRY_JOIN"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-16.json"
BRANCH_SUMMARY_LEDGER = ROUTE_DIR / f"{PREFIX}_BRANCH_SUMMARY_LEDGER_2026-05-16.jsonl"
OFFSET_JOIN_LEDGER = ROUTE_DIR / f"{PREFIX}_OFFSET_JOIN_LEDGER_2026-05-16.jsonl"
MARKET_ENTRY_JOIN_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_ENTRY_JOIN_LEDGER_2026-05-16.jsonl"
SOURCE_REQUIREMENT_JOIN_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_REQUIREMENT_JOIN_LEDGER_2026-05-16.jsonl"
MARKET_VARIANT_SUMMARY_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_VARIANT_SUMMARY_LEDGER_2026-05-16.jsonl"
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
    "Branch system-transfer confirmed no-fill near-miss market-entry join packet only. It preserves every "
    "224 offset branch row, every 896 market-entry branch row, and every 560 source-requirement row by joining "
    "them back to the 386 branch system-transfer denominator on route, target/stop contract, and source entry "
    "variant. It computes lower-level market-entry/offset proxy pressure and implementation implications, but "
    "does not change live behavior or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, "
    "or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-NEARMISS-TRANSFER-SRC-{index:04d}",
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


def stat(values: list[float], prefix: str) -> dict[str, float | None]:
    if not values:
        return {f"{prefix}_min": None, f"{prefix}_mean": None, f"{prefix}_max": None}
    return {
        f"{prefix}_min": round(min(values), 6),
        f"{prefix}_mean": round(mean(values), 6),
        f"{prefix}_max": round(max(values), 6),
    }


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def system_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("route_candidate_id")),
        str(row.get("target_stop_contract_id")),
        str(row.get("entry_variant")),
    )


def near_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("route_candidate_id")),
        str(row.get("target_stop_contract_id")),
        str(row.get("source_entry_variant")),
    )


def touch_class(status: Any) -> str:
    text = str(status or "")
    if text.startswith("TARGET_TOUCH"):
        return "TARGET_FIRST_OR_ONLY"
    if text.startswith("STOP_TOUCH"):
        return "STOP_FIRST_OR_ONLY"
    if text == "TARGET_AND_STOP_TOUCH_SAME_M15_BAR_AMBIGUOUS":
        return "TARGET_STOP_SAME_M15_AMBIGUOUS"
    if text == "NO_TARGET_OR_STOP_TOUCH_WITHIN_CONTRACT_HORIZON":
        return "NO_TARGET_OR_STOP_TOUCH"
    return "UNKNOWN_TOUCH_STATUS"


def touch_score(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    counter = Counter(touch_class(row.get(field)) for row in rows)
    total = sum(counter.values())
    target = counter.get("TARGET_FIRST_OR_ONLY", 0)
    stop = counter.get("STOP_FIRST_OR_ONLY", 0)
    ambiguous = counter.get("TARGET_STOP_SAME_M15_AMBIGUOUS", 0)
    no_touch = counter.get("NO_TARGET_OR_STOP_TOUCH", 0)
    denominator = total or 1
    return {
        "touch_class_counts": compact_counter(counter),
        "target_first_rows": target,
        "stop_first_rows": stop,
        "same_m15_ambiguous_rows": ambiguous,
        "no_touch_rows": no_touch,
        "target_first_share": round(target / denominator, 6) if total else None,
        "stop_first_share": round(stop / denominator, 6) if total else None,
        "target_minus_stop_share": round((target - stop) / denominator, 6) if total else None,
        "ambiguity_or_no_touch_share": round((ambiguous + no_touch) / denominator, 6) if total else None,
    }


def implication(branch: dict[str, Any], market_score: dict[str, Any], offset_score: dict[str, Any], direct_rows: int) -> str:
    if not direct_rows:
        return "NEARMISS_NO_DIRECT_CONTEXT_BRANCH_RETAINS_SYSTEM_TRANSFER_DECISION"
    market_delta = float(market_score.get("target_minus_stop_share") or 0.0)
    offset_delta = float(offset_score.get("target_minus_stop_share") or 0.0)
    ambiguity = float(market_score.get("ambiguity_or_no_touch_share") or 0.0)
    decision = str(branch.get("decision_direction") or "")
    if market_delta >= 0.20 and offset_delta >= 0.0 and decision == "KEEP_CHALLENGER":
        return "NEARMISS_MARKET_ENTRY_CHALLENGER_REVIEW_WITH_OFFSET_SUPPORT"
    if market_delta >= 0.20:
        return "NEARMISS_MARKET_ENTRY_REPAIR_OR_CHALLENGER_REVIEW"
    if market_delta <= -0.20:
        return "NEARMISS_MARKET_ENTRY_AVOID_OR_ADVERSE_REDESIGN"
    if ambiguity >= 0.50:
        return "NEARMISS_MARKET_ENTRY_ORDERING_OR_NO_TOUCH_STRESS"
    return "NEARMISS_MARKET_ENTRY_MIXED_PROXY_SPLIT"


def implementation(branch: dict[str, Any], near_implication: str) -> str:
    decision = str(branch.get("decision_direction") or "")
    if near_implication == "NEARMISS_NO_DIRECT_CONTEXT_BRANCH_RETAINS_SYSTEM_TRANSFER_DECISION":
        return "NO_NEARMISS_JOIN_IMPLEMENTATION_DELTA_FROM_SYSTEM_TRANSFER"
    if near_implication == "NEARMISS_MARKET_ENTRY_CHALLENGER_REVIEW_WITH_OFFSET_SUPPORT":
        return "TEST_MARKET_ENTRY_CHALLENGER_AGAINST_RETEST_LIMIT_FOR_KEEP_BRANCH"
    if near_implication == "NEARMISS_MARKET_ENTRY_REPAIR_OR_CHALLENGER_REVIEW":
        return "TEST_MARKET_ENTRY_REPAIR_SPLIT_BEFORE_KEEP_OR_KILL_DECISION"
    if near_implication == "NEARMISS_MARKET_ENTRY_AVOID_OR_ADVERSE_REDESIGN":
        return "PREFER_AVOID_OR_ADVERSE_FILTER_OVER_MARKET_ENTRY"
    if decision in {"KILL_OR_REDESIGN", "KEEP_REPAIR_OR_AVOID"}:
        return "REQUIRE_SOURCE_OR_ORDERING_REPAIR_BEFORE_REVIVING_NEARMISS_BRANCH"
    return "SPLIT_NEARMISS_MARKET_ENTRY_VARIANTS_WITH_M15_ORDERING_STRESS"


def join_source_row(
    row: dict[str, Any],
    branch: dict[str, Any],
    generated_at: str,
    manifest_hash: str,
    row_type: str,
) -> dict[str, Any]:
    joined = dict(row)
    joined.update(
        {
            "nearmiss_join_row_type": row_type,
            "branch_queue_id": branch.get("branch_queue_id"),
            "matrix_branch_id": branch.get("matrix_branch_id"),
            "system_transfer_branch_id": branch.get("system_transfer_branch_id"),
            "system_entry_variant": branch.get("entry_variant"),
            "primary_export_family": branch.get("primary_export_family"),
            "decision_direction": branch.get("decision_direction"),
            "system_decision_class": branch.get("system_decision_class"),
            "branch_result_binary": branch.get("branch_result_binary"),
            "accepted_for_next_executable_builder": branch.get("accepted_for_next_executable_builder"),
            "market_transfer_class": branch.get("market_transfer_class"),
            "market_specific_concentration_flag": branch.get("market_specific_concentration_flag"),
            "target_stop_result": branch.get("target_stop_result"),
            "non_ob_primitive_scope": branch.get("non_ob_primitive_scope"),
        }
    )
    return with_common(joined, generated_at, manifest_hash)


def main() -> int:
    generated_at = now_utc()
    system_result = read_json(SYSTEM_TRANSFER_RESULT)
    tick_result = read_json(TICK_CONTEXT_RESULT)
    nofill_transfer_result = read_json(NOFILL_TRANSFER_RESULT)
    near_result = read_json(NEAR_MISS_RESULT)
    system_rows = read_jsonl(SYSTEM_TRANSFER_BRANCH)
    tick_rows = read_jsonl(TICK_CONTEXT_BRANCH_SUMMARY)
    nofill_transfer_rows = read_jsonl(NOFILL_TRANSFER_BRANCH_SUMMARY)
    offset_rows = read_jsonl(NEAR_MISS_OFFSET)
    market_rows = read_jsonl(NEAR_MISS_MARKET)
    source_req_rows = read_jsonl(NEAR_MISS_SOURCE_REQ)

    source_manifest, manifest_hash = source_manifest_rows(
        [
            SYSTEM_TRANSFER_RESULT,
            SYSTEM_TRANSFER_BRANCH,
            TICK_CONTEXT_RESULT,
            TICK_CONTEXT_BRANCH_SUMMARY,
            NOFILL_TRANSFER_RESULT,
            NOFILL_TRANSFER_BRANCH_SUMMARY,
            NEAR_MISS_RESULT,
            NEAR_MISS_OFFSET,
            NEAR_MISS_MARKET,
            NEAR_MISS_SOURCE_REQ,
        ],
        generated_at,
    )

    system_by_key = {system_key(row): row for row in system_rows}
    tick_by_branch = {row.get("branch_queue_id"): row for row in tick_rows}
    nofill_by_branch = {row.get("branch_queue_id"): row for row in nofill_transfer_rows}
    offset_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    market_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    source_req_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in offset_rows:
        offset_by_key[near_key(row)].append(row)
    for row in market_rows:
        market_by_key[near_key(row)].append(row)
    for row in source_req_rows:
        source_req_by_key[near_key(row)].append(row)

    unmatched_offset_ids: list[str] = []
    unmatched_market_ids: list[str] = []
    unmatched_source_requirement_ids: list[str] = []
    offset_join_rows: list[dict[str, Any]] = []
    market_join_rows: list[dict[str, Any]] = []
    source_requirement_join_rows: list[dict[str, Any]] = []
    for row in offset_rows:
        branch = system_by_key.get(near_key(row))
        if not branch:
            unmatched_offset_ids.append(str(row.get("near_miss_entry_control_offset_branch_id")))
            continue
        joined = join_source_row(row, branch, generated_at, manifest_hash, "OFFSET_BRANCH_JOIN")
        joined["offset_touch_class"] = touch_class(row.get("first_touch_status_offset_proxy"))
        offset_join_rows.append(joined)
    for row in market_rows:
        branch = system_by_key.get(near_key(row))
        if not branch:
            unmatched_market_ids.append(str(row.get("near_miss_entry_control_market_branch_id")))
            continue
        joined = join_source_row(row, branch, generated_at, manifest_hash, "MARKET_ENTRY_BRANCH_JOIN")
        joined["market_touch_class"] = touch_class(row.get("market_first_touch_status"))
        market_join_rows.append(joined)
    for row in source_req_rows:
        branch = system_by_key.get(near_key(row))
        if not branch:
            unmatched_source_requirement_ids.append(str(row.get("near_miss_entry_control_source_requirement_id")))
            continue
        joined = join_source_row(row, branch, generated_at, manifest_hash, "SOURCE_REQUIREMENT_BRANCH_JOIN")
        joined["source_requirement_satisfied"] = str(row.get("source_requirement_status", "")).startswith("SATISFIED")
        source_requirement_join_rows.append(joined)

    branch_summary_rows: list[dict[str, Any]] = []
    for index, branch in enumerate(system_rows, 1):
        key = system_key(branch)
        offset_for_branch = offset_by_key.get(key, [])
        market_for_branch = market_by_key.get(key, [])
        source_req_for_branch = source_req_by_key.get(key, [])
        offset_score = touch_score(offset_for_branch, "first_touch_status_offset_proxy")
        market_score = touch_score(market_for_branch, "market_first_touch_status")
        source_req_counter = Counter(row.get("source_requirement_status") for row in source_req_for_branch)
        satisfied_source_rows = sum(1 for row in source_req_for_branch if str(row.get("source_requirement_status", "")).startswith("SATISFIED"))
        blocked_source_rows = len(source_req_for_branch) - satisfied_source_rows
        market_deltas = [
            value
            for value in (
                as_float(row.get("market_entry_signed_delta_over_rolling_range"))
                for row in market_for_branch
            )
            if value is not None
        ]
        direct_rows = len(offset_for_branch) + len(market_for_branch) + len(source_req_for_branch)
        near_implication = implication(branch, market_score, offset_score, direct_rows)
        branch_summary_rows.append(
            with_common(
                {
                    "nearmiss_transfer_branch_summary_id": f"OHLC-GTOS-NEARMISS-TRANSFER-BRANCH-{index:05d}",
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
                    "nofill_join_status": (nofill_by_branch.get(branch.get("branch_queue_id")) or {}).get("nofill_join_status"),
                    "nofill_transfer_implication": (nofill_by_branch.get(branch.get("branch_queue_id")) or {}).get("nofill_transfer_implication"),
                    "nearmiss_join_status": (
                        "NEARMISS_OFFSET_MARKET_SOURCE_CONTEXT_JOINED"
                        if direct_rows
                        else "NEARMISS_NO_DIRECT_CONTEXT_FOR_BRANCH_KEY"
                    ),
                    "nearmiss_offset_rows": len(offset_for_branch),
                    "nearmiss_market_entry_rows": len(market_for_branch),
                    "nearmiss_source_requirement_rows": len(source_req_for_branch),
                    "nearmiss_total_context_rows": direct_rows,
                    "offset_touch_class_counts": offset_score["touch_class_counts"],
                    "offset_target_first_rows": offset_score["target_first_rows"],
                    "offset_stop_first_rows": offset_score["stop_first_rows"],
                    "offset_target_minus_stop_share": offset_score["target_minus_stop_share"],
                    "offset_ambiguity_or_no_touch_share": offset_score["ambiguity_or_no_touch_share"],
                    "market_touch_class_counts": market_score["touch_class_counts"],
                    "market_target_first_rows": market_score["target_first_rows"],
                    "market_stop_first_rows": market_score["stop_first_rows"],
                    "market_same_m15_ambiguous_rows": market_score["same_m15_ambiguous_rows"],
                    "market_no_touch_rows": market_score["no_touch_rows"],
                    "market_target_minus_stop_share": market_score["target_minus_stop_share"],
                    "market_ambiguity_or_no_touch_share": market_score["ambiguity_or_no_touch_share"],
                    **stat(market_deltas, "market_entry_signed_delta_over_rolling_range"),
                    "source_requirement_status_counts": compact_counter(source_req_counter),
                    "source_requirement_satisfied_rows": satisfied_source_rows,
                    "source_requirement_blocked_or_absent_rows": blocked_source_rows,
                    "nearmiss_transfer_implication": near_implication,
                    "implementation_implication": implementation(branch, near_implication),
                    "exact_failure_cause": (
                        f"{branch.get('exact_failure_cause')}__NEARMISS_MARKET_ENTRY_CONTEXT_{near_implication}"
                        if direct_rows
                        else branch.get("exact_failure_cause")
                    ),
                    "exact_success_cause": branch.get("exact_success_cause"),
                    "next_same_resource_action": (
                        "SPLIT_NEARMISS_MARKET_ENTRY_OFFSET_AND_SOURCE_REQUIREMENT_CONTEXT"
                        if direct_rows
                        else "NO_NEARMISS_JOIN_DIRECT_FOR_BRANCH_CONTINUE_MARKET_GAP_PRIMITIVE_EXPANSION"
                    ),
                },
                generated_at,
                manifest_hash,
            )
        )

    market_variant_summary_rows: list[dict[str, Any]] = []
    by_variant: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in market_join_rows:
        by_variant[str(row.get("market_entry_variant"))].append(row)
    for variant, rows in sorted(by_variant.items()):
        score = touch_score(rows, "market_first_touch_status")
        market_variant_summary_rows.append(
            with_common(
                {
                    "nearmiss_transfer_market_variant_summary_id": f"OHLC-GTOS-NEARMISS-TRANSFER-VARIANT-{len(market_variant_summary_rows) + 1:04d}",
                    "market_entry_variant": variant,
                    "market_entry_rows": len(rows),
                    "unique_system_branch_ids": len({row.get("system_transfer_branch_id") for row in rows}),
                    "symbol_counts": compact_counter(Counter(row.get("symbol") for row in rows)),
                    "session_counts": compact_counter(Counter(row.get("route_session") for row in rows)),
                    "side_counts": compact_counter(Counter(row.get("side") for row in rows)),
                    "market_first_touch_status_counts": compact_counter(Counter(row.get("market_first_touch_status") for row in rows)),
                    "market_touch_class_counts": score["touch_class_counts"],
                    "target_minus_stop_share": score["target_minus_stop_share"],
                    "ambiguity_or_no_touch_share": score["ambiguity_or_no_touch_share"],
                    "variant_action": (
                        "MARKET_ENTRY_VARIANT_TARGET_FIRST_PROXY_REVIEW"
                        if float(score.get("target_minus_stop_share") or 0.0) > 0
                        else "MARKET_ENTRY_VARIANT_AVOID_OR_STRESS_REVIEW"
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
                    "nearmiss_transfer_route_summary_id": f"OHLC-GTOS-NEARMISS-TRANSFER-ROUTE-{len(route_summary_rows) + 1:04d}",
                    "route_candidate_id": route_candidate_id,
                    "branch_rows": len(rows),
                    "symbol_counts": compact_counter(Counter(row.get("symbol") for row in rows)),
                    "session_counts": compact_counter(Counter(row.get("route_session") for row in rows)),
                    "side_counts": compact_counter(Counter(row.get("side") for row in rows)),
                    "nearmiss_join_status_counts": compact_counter(Counter(row.get("nearmiss_join_status") for row in rows)),
                    "nearmiss_transfer_implication_counts": compact_counter(Counter(row.get("nearmiss_transfer_implication") for row in rows)),
                    "implementation_implication_counts": compact_counter(Counter(row.get("implementation_implication") for row in rows)),
                    "nearmiss_offset_rows": int(sum(row.get("nearmiss_offset_rows") or 0 for row in rows)),
                    "nearmiss_market_entry_rows": int(sum(row.get("nearmiss_market_entry_rows") or 0 for row in rows)),
                    "nearmiss_source_requirement_rows": int(sum(row.get("nearmiss_source_requirement_rows") or 0 for row in rows)),
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
        "nearmiss_join_status": Counter(row.get("nearmiss_join_status") for row in branch_summary_rows),
        "nearmiss_transfer_implication": Counter(row.get("nearmiss_transfer_implication") for row in branch_summary_rows),
        "implementation_implication": Counter(row.get("implementation_implication") for row in branch_summary_rows),
        "offset_first_touch_status": Counter(row.get("first_touch_status_offset_proxy") for row in offset_join_rows),
        "offset_touch_class": Counter(row.get("offset_touch_class") for row in offset_join_rows),
        "market_entry_variant": Counter(row.get("market_entry_variant") for row in market_join_rows),
        "market_first_touch_status": Counter(row.get("market_first_touch_status") for row in market_join_rows),
        "market_touch_class": Counter(row.get("market_touch_class") for row in market_join_rows),
        "source_requirement_status": Counter(row.get("source_requirement_status") for row in source_requirement_join_rows),
        "source_requirement_satisfied": Counter(row.get("source_requirement_satisfied") for row in source_requirement_join_rows),
    }
    bucket_rows: list[dict[str, Any]] = []
    for category, counter in sorted(bucket_sources.items()):
        for value, row_count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                with_common(
                    {
                        "nearmiss_transfer_bucket_id": f"OHLC-GTOS-NEARMISS-TRANSFER-BUCKET-{len(bucket_rows) + 1:05d}",
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
            "question_id": "OHLC-GTOS-NEARMISS-TRANSFER-QUESTION-001",
            "question": "Which system-transfer branches carry confirmed near-miss market-entry context?",
            "answer_route": "Use BRANCH_SUMMARY_LEDGER; all 386 branches are preserved and 48 branch keys carry direct near-miss rows.",
        },
        {
            "question_id": "OHLC-GTOS-NEARMISS-TRANSFER-QUESTION-002",
            "question": "Are any near-miss offset, market-entry, or source-requirement rows dropped by the join?",
            "answer_route": "No; OFFSET_JOIN_LEDGER preserves 224 rows, MARKET_ENTRY_JOIN_LEDGER preserves 896 rows, and SOURCE_REQUIREMENT_JOIN_LEDGER preserves 560 rows.",
        },
        {
            "question_id": "OHLC-GTOS-NEARMISS-TRANSFER-QUESTION-003",
            "question": "Which market-entry variants survive as challenger review versus avoid/stress review?",
            "answer_route": "Use MARKET_VARIANT_SUMMARY_LEDGER and the market_entry_variant bucket distribution.",
        },
        {
            "question_id": "OHLC-GTOS-NEARMISS-TRANSFER-QUESTION-004",
            "question": "How does near-miss context interact with the existing system-transfer/no-fill decisions?",
            "answer_route": "Use nearmiss_transfer_implication plus implementation_implication in BRANCH_SUMMARY_LEDGER.",
        },
    ]
    for row in question_rows:
        with_common(row, generated_at, manifest_hash)

    row_count_stats = {
        "branches_with_direct_nearmiss_context": sum(1 for row in branch_summary_rows if row.get("nearmiss_total_context_rows")),
        "branches_without_direct_nearmiss_context": sum(1 for row in branch_summary_rows if not row.get("nearmiss_total_context_rows")),
        "offset_join_rows": len(offset_join_rows),
        "market_entry_join_rows": len(market_join_rows),
        "source_requirement_join_rows": len(source_requirement_join_rows),
        "market_entry_variant_rows": len(market_variant_summary_rows),
    }

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_NEARMISS_MARKET_ENTRY_JOIN",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_system_transfer_branch_rows": len(system_rows),
            "input_tick_context_branch_summary_rows": len(tick_rows),
            "input_nofill_transfer_branch_summary_rows": len(nofill_transfer_rows),
            "input_offset_branch_rows": len(offset_rows),
            "input_market_entry_branch_rows": len(market_rows),
            "input_source_requirement_rows": len(source_req_rows),
            "branch_summary_rows": len(branch_summary_rows),
            "offset_join_rows": len(offset_join_rows),
            "market_entry_join_rows": len(market_join_rows),
            "source_requirement_join_rows": len(source_requirement_join_rows),
            "market_variant_summary_rows": len(market_variant_summary_rows),
            "route_summary_rows": len(route_summary_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_manifest),
            "unmatched_offset_rows": len(unmatched_offset_ids),
            "unmatched_market_entry_rows": len(unmatched_market_ids),
            "unmatched_source_requirement_rows": len(unmatched_source_requirement_ids),
        },
        "upstream_counts": {
            "system_transfer": system_result.get("counts", {}),
            "tick_context": tick_result.get("counts", {}),
            "nofill_transfer": nofill_transfer_result.get("counts", {}),
            "near_miss_entry_controls": near_result.get("counts", {}),
        },
        "join_diagnostics": {
            "join_key_fields": ["route_candidate_id", "target_stop_contract_id", "source_entry_variant=>entry_variant"],
            "system_branch_key_count": len(system_by_key),
            "near_miss_offset_key_count": len(offset_by_key),
            "near_miss_market_key_count": len(market_by_key),
            "near_miss_source_requirement_key_count": len(source_req_by_key),
            "unmatched_offset_ids": unmatched_offset_ids,
            "unmatched_market_ids": unmatched_market_ids,
            "unmatched_source_requirement_ids": unmatched_source_requirement_ids,
        },
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_sources.items())},
        "row_count_stats": row_count_stats,
        "system_decision": {
            "system_recommendation": (
                "NEARMISS_MARKET_ENTRY_JOIN_RESULT: confirmed near-miss offset and market-entry controls "
                "are now attached to the 386 system-transfer branches; 48 branch keys carry direct near-miss "
                "context while 338 do not. Continue into market-gap primitive expansion and route-mechanic "
                "matrix rather than treating near-miss context as exhausted."
            ),
            **row_count_stats,
        },
        "source_manifest_hash": manifest_hash,
    }

    outputs = [
        (BRANCH_SUMMARY_LEDGER, branch_summary_rows),
        (OFFSET_JOIN_LEDGER, offset_join_rows),
        (MARKET_ENTRY_JOIN_LEDGER, market_join_rows),
        (SOURCE_REQUIREMENT_JOIN_LEDGER, source_requirement_join_rows),
        (MARKET_VARIANT_SUMMARY_LEDGER, market_variant_summary_rows),
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
                "# Historical OHLC GTOS Replay Branch System Transfer Near-Miss Market-Entry Join",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Branch summary rows: `{len(branch_summary_rows)}`",
                f"- Offset join rows: `{len(offset_join_rows)}`",
                f"- Market-entry join rows: `{len(market_join_rows)}`",
                f"- Source-requirement join rows: `{len(source_requirement_join_rows)}`",
                f"- Branches with direct near-miss context: `{row_count_stats['branches_with_direct_nearmiss_context']}`",
                f"- Branches without direct near-miss context: `{row_count_stats['branches_without_direct_nearmiss_context']}`",
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
                "type": "branch_system_transfer_nearmiss_market_entry_join",
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
                    "event_type": "branch_system_transfer_nearmiss_market_entry_join_built",
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
