#!/usr/bin/env python3
"""Join system-transfer branches to tick primitive transfer context."""

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
TICK_TRANSFER_RESULT = ROUTE_DIR / "TICK_M15_CROSS_HORIZON_SESSION_TRANSFER_RESULT_2026-05-16.json"
TICK_TRANSFER_BASE = ROUTE_DIR / "TICK_M15_CROSS_TRANSFER_BASE_ROW_LEDGER_2026-05-16.jsonl"
TICK_FLAG_SUMMARY = ROUTE_DIR / "TICK_M15_PRIMITIVE_FLAG_SUMMARY_LEDGER_2026-05-15.jsonl"
TICK_HORIZON_MATRIX = ROUTE_DIR / "TICK_M15_CROSS_HORIZON_TRANSFER_MATRIX_2026-05-16.jsonl"
TICK_SESSION_MATRIX = ROUTE_DIR / "TICK_M15_CROSS_SESSION_TRANSFER_MATRIX_2026-05-16.jsonl"

PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_TICK_PRIMITIVE_CONTEXT"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-16.json"
BRANCH_CONTEXT_LEDGER = ROUTE_DIR / f"{PREFIX}_BRANCH_CONTEXT_LEDGER_2026-05-16.jsonl"
BRANCH_SUMMARY_LEDGER = ROUTE_DIR / f"{PREFIX}_BRANCH_SUMMARY_LEDGER_2026-05-16.jsonl"
MARKET_GAP_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_GAP_LEDGER_2026-05-16.jsonl"
KEY_COVERAGE_LEDGER = ROUTE_DIR / f"{PREFIX}_KEY_COVERAGE_LEDGER_2026-05-16.jsonl"
FAMILY_PRIMITIVE_LEDGER = ROUTE_DIR / f"{PREFIX}_FAMILY_PRIMITIVE_LEDGER_2026-05-16.jsonl"
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
    "Tick primitive context join packet only. It joins every 386 system-transfer branch to "
    "all available tick primitive transfer rows for the matching symbol/session/horizon key, "
    "preserves unmatched market/session/horizon primitive rows as expansion gaps, and does not "
    "change live behavior or claim broker R/PnL, realized expectancy, win-rate, validation, "
    "live-readiness, or promotion."
)

SESSION_MAP = {
    "ny_core": "ny_core_1300_1700",
    "tokyo_kz": "tokyo_core_0000_0300",
    "london_core": "london_core_0700_1030",
}


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
                "source_manifest_id": f"OHLC-GTOS-TICK-PRIM-CONTEXT-SRC-{index:04d}",
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


def route_horizon(route_candidate_id: str | None) -> str:
    parts = str(route_candidate_id or "").split("|")
    return parts[3] if len(parts) >= 4 else "UNKNOWN_HORIZON"


def branch_tick_key(branch: dict[str, Any]) -> tuple[str, str, str]:
    session_bucket = SESSION_MAP.get(str(branch.get("route_session")), f"UNMAPPED_{branch.get('route_session')}")
    return (str(branch.get("symbol")), session_bucket, route_horizon(branch.get("route_candidate_id")))


def tick_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (str(row.get("symbol")), str(row.get("session_bucket")), str(row.get("horizon_id")))


def tick_combo(row: dict[str, Any]) -> tuple[str, str, str, str]:
    symbol, session_bucket, horizon_id = tick_key(row)
    return (symbol, session_bucket, horizon_id, str(row.get("primitive_flag")))


def tick_context_decision(row: dict[str, Any]) -> str:
    status = str(row.get("movement_status") or "")
    triage = str(row.get("triage_bucket") or "")
    if status == "POSITIVE_ABS_AND_NONNEGATIVE_ALIGNMENT_DELTA":
        return "TICK_PRIMITIVE_SUPPORTS_TRANSFER_CONTEXT"
    if status == "POSITIVE_ABS_NEGATIVE_ALIGNMENT_DELTA":
        return "TICK_PRIMITIVE_MIXED_ALIGNMENT_CONTEXT"
    if status == "FLAT_OR_NEGATIVE_ABS_DELTA":
        return "TICK_PRIMITIVE_WEAK_OR_INVERSE_CONTEXT"
    if "SMALL_N" in status or "SMALL_N" in triage:
        return "TICK_PRIMITIVE_SMALL_N_CONTEXT"
    return "TICK_PRIMITIVE_CONTEXT_PRESERVED"


def stat(values: list[float], prefix: str) -> dict[str, float | None]:
    if not values:
        return {f"{prefix}_min": None, f"{prefix}_mean": None, f"{prefix}_max": None}
    return {
        f"{prefix}_min": round(min(values), 6),
        f"{prefix}_mean": round(mean(values), 6),
        f"{prefix}_max": round(max(values), 6),
    }


def main() -> int:
    generated_at = now_utc()
    system_result = read_json(SYSTEM_TRANSFER_RESULT)
    tick_result = read_json(TICK_TRANSFER_RESULT)
    branch_rows_input = read_jsonl(SYSTEM_TRANSFER_BRANCH)
    tick_rows = read_jsonl(TICK_TRANSFER_BASE)
    flag_summary_rows = read_jsonl(TICK_FLAG_SUMMARY)
    horizon_matrix_rows = read_jsonl(TICK_HORIZON_MATRIX)
    session_matrix_rows = read_jsonl(TICK_SESSION_MATRIX)

    source_manifest, manifest_hash = source_manifest_rows(
        [
            SYSTEM_TRANSFER_RESULT,
            SYSTEM_TRANSFER_BRANCH,
            TICK_TRANSFER_RESULT,
            TICK_TRANSFER_BASE,
            TICK_FLAG_SUMMARY,
            TICK_HORIZON_MATRIX,
            TICK_SESSION_MATRIX,
        ],
        generated_at,
    )

    tick_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in tick_rows:
        tick_by_key[tick_key(row)].append(row)

    branch_context_rows: list[dict[str, Any]] = []
    branch_summary_rows: list[dict[str, Any]] = []
    current_combos: set[tuple[str, str, str, str]] = set()
    current_keys: set[tuple[str, str, str]] = set()
    unmatched_branch_ids: list[str] = []

    for branch in branch_rows_input:
        key = branch_tick_key(branch)
        current_keys.add(key)
        matches = sorted(tick_by_key.get(key, []), key=lambda item: str(item.get("primitive_flag")))
        if not matches:
            unmatched_branch_ids.append(str(branch.get("branch_queue_id")))
        decisions: list[str] = []
        movement_statuses: list[str] = []
        delta_abs_values: list[float] = []
        flagged_abs_values: list[float] = []
        for tick_row in matches:
            combo = tick_combo(tick_row)
            current_combos.add(combo)
            decision = tick_context_decision(tick_row)
            decisions.append(decision)
            movement_statuses.append(str(tick_row.get("movement_status")))
            delta_value = as_float(tick_row.get("delta_mean_abs_future_change"))
            flagged_value = as_float(tick_row.get("flagged_mean_abs_future_change"))
            if delta_value is not None:
                delta_abs_values.append(delta_value)
            if flagged_value is not None:
                flagged_abs_values.append(flagged_value)
            branch_context_rows.append(
                with_common(
                    {
                        "tick_primitive_context_id": f"OHLC-GTOS-TICK-PRIM-CONTEXT-{len(branch_context_rows) + 1:06d}",
                        "branch_queue_id": branch.get("branch_queue_id"),
                        "matrix_branch_id": branch.get("matrix_branch_id"),
                        "route_candidate_id": branch.get("route_candidate_id"),
                        "route_descriptor": branch.get("route_descriptor"),
                        "branch_primitive_family": branch.get("primitive_family"),
                        "branch_system_decision_class": branch.get("system_decision_class"),
                        "branch_decision_direction": branch.get("decision_direction"),
                        "branch_market_transfer_class": branch.get("market_transfer_class"),
                        "branch_symbol": branch.get("symbol"),
                        "branch_route_session": branch.get("route_session"),
                        "branch_side": branch.get("side"),
                        "branch_target_stop_result": branch.get("target_stop_result"),
                        "join_symbol": key[0],
                        "join_session_bucket": key[1],
                        "join_horizon_id": key[2],
                        "tick_primitive_flag": tick_row.get("primitive_flag"),
                        "tick_movement_status": tick_row.get("movement_status"),
                        "tick_triage_bucket": tick_row.get("triage_bucket"),
                        "tick_context_decision": decision,
                        "tick_flagged_n": tick_row.get("flagged_n"),
                        "tick_control_n": tick_row.get("control_n"),
                        "tick_flagged_mean_abs_future_change": tick_row.get("flagged_mean_abs_future_change"),
                        "tick_control_mean_abs_future_change": tick_row.get("control_mean_abs_future_change"),
                        "tick_delta_mean_abs_future_change": tick_row.get("delta_mean_abs_future_change"),
                        "tick_flagged_delta_alignment_rate": tick_row.get("flagged_delta_alignment_rate"),
                        "tick_control_delta_alignment_rate": tick_row.get("control_delta_alignment_rate"),
                        "tick_delta_alignment_rate": tick_row.get("delta_alignment_rate"),
                        "tick_full_control_bucket": tick_row.get("full_control_bucket"),
                        "tick_placebo_bucket": tick_row.get("placebo_bucket"),
                        "tick_is_route_c_residual": tick_row.get("is_route_c_residual"),
                        "context_scope": "BRANCH_MATCHED_TICK_PRIMITIVE_CONTEXT",
                    },
                    generated_at,
                    manifest_hash,
                )
            )
        branch_summary_rows.append(
            with_common(
                {
                    "tick_primitive_branch_summary_id": f"OHLC-GTOS-TICK-PRIM-BRANCH-SUMMARY-{len(branch_summary_rows) + 1:05d}",
                    "branch_queue_id": branch.get("branch_queue_id"),
                    "matrix_branch_id": branch.get("matrix_branch_id"),
                    "route_candidate_id": branch.get("route_candidate_id"),
                    "route_descriptor": branch.get("route_descriptor"),
                    "branch_primitive_family": branch.get("primitive_family"),
                    "primary_export_family": branch.get("primary_export_family"),
                    "system_decision_class": branch.get("system_decision_class"),
                    "decision_direction": branch.get("decision_direction"),
                    "symbol": branch.get("symbol"),
                    "route_session": branch.get("route_session"),
                    "side": branch.get("side"),
                    "join_symbol": key[0],
                    "join_session_bucket": key[1],
                    "join_horizon_id": key[2],
                    "matched_tick_primitive_rows": len(matches),
                    "matched_tick_primitive_flags": [row.get("primitive_flag") for row in matches],
                    "tick_context_decision_counts": compact_counter(Counter(decisions)),
                    "tick_movement_status_counts": compact_counter(Counter(movement_statuses)),
                    **stat(delta_abs_values, "tick_delta_mean_abs_future_change"),
                    **stat(flagged_abs_values, "tick_flagged_mean_abs_future_change"),
                    "tick_context_join_status": "MATCHED_FIVE_TICK_PRIMITIVE_FLAGS" if len(matches) == 5 else "TICK_PRIMITIVE_CONTEXT_GAP",
                },
                generated_at,
                manifest_hash,
            )
        )

    market_gap_rows: list[dict[str, Any]] = []
    for row in tick_rows:
        combo = tick_combo(row)
        if combo in current_combos:
            continue
        market_gap_rows.append(
            with_common(
                {
                    "tick_market_gap_id": f"OHLC-GTOS-TICK-PRIM-MARKET-GAP-{len(market_gap_rows) + 1:05d}",
                    "symbol": row.get("symbol"),
                    "session_bucket": row.get("session_bucket"),
                    "horizon_id": row.get("horizon_id"),
                    "primitive_flag": row.get("primitive_flag"),
                    "movement_status": row.get("movement_status"),
                    "triage_bucket": row.get("triage_bucket"),
                    "tick_context_decision": tick_context_decision(row),
                    "flagged_n": row.get("flagged_n"),
                    "control_n": row.get("control_n"),
                    "flagged_mean_abs_future_change": row.get("flagged_mean_abs_future_change"),
                    "control_mean_abs_future_change": row.get("control_mean_abs_future_change"),
                    "delta_mean_abs_future_change": row.get("delta_mean_abs_future_change"),
                    "flagged_delta_alignment_rate": row.get("flagged_delta_alignment_rate"),
                    "control_delta_alignment_rate": row.get("control_delta_alignment_rate"),
                    "delta_alignment_rate": row.get("delta_alignment_rate"),
                    "gap_reason": "TICK_MARKET_SESSION_HORIZON_PRIMITIVE_OUTSIDE_CURRENT_386_BRANCH_DENOMINATOR",
                    "next_same_resource_action": "OPEN_MARKET_GAP_TRANSFER_OR_PRIMITIVE_FACTORY_EXPANSION",
                },
                generated_at,
                manifest_hash,
            )
        )

    all_tick_keys = sorted(tick_by_key.keys(), key=lambda item: tuple(str(part) for part in item))
    key_coverage_rows: list[dict[str, Any]] = []
    for key in all_tick_keys:
        matched_branch_ids = [
            str(branch.get("branch_queue_id"))
            for branch in branch_rows_input
            if branch_tick_key(branch) == key
        ]
        key_rows = tick_by_key[key]
        key_coverage_rows.append(
            with_common(
                {
                    "tick_key_coverage_id": f"OHLC-GTOS-TICK-PRIM-KEY-COVERAGE-{len(key_coverage_rows) + 1:05d}",
                    "symbol": key[0],
                    "session_bucket": key[1],
                    "horizon_id": key[2],
                    "tick_primitive_rows": len(key_rows),
                    "matched_branch_count": len(matched_branch_ids),
                    "matched_branch_ids": matched_branch_ids,
                    "coverage_status": "CURRENT_BRANCH_KEY_PRESENT" if matched_branch_ids else "MARKET_GAP_KEY_ONLY",
                    "primitive_flags": [row.get("primitive_flag") for row in sorted(key_rows, key=lambda item: str(item.get("primitive_flag")))],
                    "movement_status_counts": compact_counter(Counter(row.get("movement_status") for row in key_rows)),
                    "tick_context_decision_counts": compact_counter(Counter(tick_context_decision(row) for row in key_rows)),
                },
                generated_at,
                manifest_hash,
            )
        )

    family_groups: dict[tuple[Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in branch_context_rows:
        family_groups[(row.get("branch_system_decision_class"), row.get("tick_primitive_flag"))].append(row)
    family_primitive_rows: list[dict[str, Any]] = []
    for (decision_class, primitive_flag), rows in sorted(family_groups.items(), key=lambda item: (str(item[0][0]), str(item[0][1]))):
        family_primitive_rows.append(
            with_common(
                {
                    "tick_family_primitive_id": f"OHLC-GTOS-TICK-PRIM-FAMILY-{len(family_primitive_rows) + 1:05d}",
                    "branch_system_decision_class": decision_class,
                    "tick_primitive_flag": primitive_flag,
                    "context_row_count": len(rows),
                    "unique_branch_count": len({row.get("branch_queue_id") for row in rows}),
                    "symbol_counts": compact_counter(Counter(row.get("branch_symbol") for row in rows)),
                    "session_counts": compact_counter(Counter(row.get("branch_route_session") for row in rows)),
                    "side_counts": compact_counter(Counter(row.get("branch_side") for row in rows)),
                    "tick_context_decision_counts": compact_counter(Counter(row.get("tick_context_decision") for row in rows)),
                    "tick_movement_status_counts": compact_counter(Counter(row.get("tick_movement_status") for row in rows)),
                    **stat([value for value in (as_float(row.get("tick_delta_mean_abs_future_change")) for row in rows) if value is not None], "tick_delta_mean_abs_future_change"),
                    **stat([value for value in (as_float(row.get("tick_flagged_mean_abs_future_change")) for row in rows) if value is not None], "tick_flagged_mean_abs_future_change"),
                },
                generated_at,
                manifest_hash,
            )
        )

    question_rows = [
        {
            "question_id": "OHLC-GTOS-TICK-PRIM-CONTEXT-QUESTION-001",
            "question": "Which tick primitive contexts attach to each branch-system decision?",
            "answer_route": "Use BRANCH_CONTEXT_LEDGER; it preserves five tick primitive rows per branch.",
        },
        {
            "question_id": "OHLC-GTOS-TICK-PRIM-CONTEXT-QUESTION-002",
            "question": "Which tick symbol/session/horizon primitive rows are outside the current 386-branch denominator?",
            "answer_route": "Use MARKET_GAP_LEDGER and KEY_COVERAGE_LEDGER; no market gap is dropped.",
        },
        {
            "question_id": "OHLC-GTOS-TICK-PRIM-CONTEXT-QUESTION-003",
            "question": "Which branch-system decisions align with supportive, mixed, weak, or small-N tick primitive context?",
            "answer_route": "Use FAMILY_PRIMITIVE_LEDGER and branch summaries, preserving movement_status and tick_context_decision counts.",
        },
        {
            "question_id": "OHLC-GTOS-TICK-PRIM-CONTEXT-QUESTION-004",
            "question": "What immediate same-resource work follows?",
            "answer_route": "Join no-fill avoid/retest redesign rows to the system-transfer branch decisions and tick-context summaries.",
        },
    ]
    for row in question_rows:
        with_common(row, generated_at, manifest_hash)

    bucket_sources = {
        "branch_system_decision_class": Counter(row.get("branch_system_decision_class") for row in branch_context_rows),
        "branch_decision_direction": Counter(row.get("branch_decision_direction") for row in branch_context_rows),
        "branch_symbol": Counter(row.get("branch_symbol") for row in branch_context_rows),
        "branch_route_session": Counter(row.get("branch_route_session") for row in branch_context_rows),
        "branch_side": Counter(row.get("branch_side") for row in branch_context_rows),
        "join_session_bucket": Counter(row.get("join_session_bucket") for row in branch_context_rows),
        "join_horizon_id": Counter(row.get("join_horizon_id") for row in branch_context_rows),
        "tick_primitive_flag": Counter(row.get("tick_primitive_flag") for row in branch_context_rows),
        "tick_movement_status": Counter(row.get("tick_movement_status") for row in branch_context_rows),
        "tick_context_decision": Counter(row.get("tick_context_decision") for row in branch_context_rows),
        "market_gap_symbol": Counter(row.get("symbol") for row in market_gap_rows),
        "market_gap_session_bucket": Counter(row.get("session_bucket") for row in market_gap_rows),
        "market_gap_horizon_id": Counter(row.get("horizon_id") for row in market_gap_rows),
        "market_gap_tick_primitive_flag": Counter(row.get("primitive_flag") for row in market_gap_rows),
        "key_coverage_status": Counter(row.get("coverage_status") for row in key_coverage_rows),
    }

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_TICK_PRIMITIVE_CONTEXT",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_system_transfer_branch_rows": len(branch_rows_input),
            "input_tick_transfer_base_rows": len(tick_rows),
            "input_tick_flag_summary_rows": len(flag_summary_rows),
            "input_tick_horizon_matrix_rows": len(horizon_matrix_rows),
            "input_tick_session_matrix_rows": len(session_matrix_rows),
            "branch_tick_context_rows": len(branch_context_rows),
            "branch_tick_summary_rows": len(branch_summary_rows),
            "market_gap_rows": len(market_gap_rows),
            "key_coverage_rows": len(key_coverage_rows),
            "family_primitive_rows": len(family_primitive_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_manifest),
            "unmatched_branch_rows": len(unmatched_branch_ids),
        },
        "upstream_counts": {
            "system_transfer": system_result.get("counts", {}),
            "tick_transfer": tick_result.get("counts", {}),
        },
        "join_diagnostics": {
            "session_map": SESSION_MAP,
            "current_branch_key_count": len(current_keys),
            "current_tick_combo_count": len(current_combos),
            "expected_context_rows_from_branch_x_5": len(branch_rows_input) * 5,
            "unmatched_branch_ids": unmatched_branch_ids,
        },
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_sources.items())},
        "context_stats": {
            "matched_five_flag_branch_rows": sum(1 for row in branch_summary_rows if row.get("matched_tick_primitive_rows") == 5),
            "small_n_context_rows": sum(1 for row in branch_context_rows if row.get("tick_context_decision") == "TICK_PRIMITIVE_SMALL_N_CONTEXT"),
            "supportive_context_rows": sum(1 for row in branch_context_rows if row.get("tick_context_decision") == "TICK_PRIMITIVE_SUPPORTS_TRANSFER_CONTEXT"),
            "mixed_context_rows": sum(1 for row in branch_context_rows if row.get("tick_context_decision") == "TICK_PRIMITIVE_MIXED_ALIGNMENT_CONTEXT"),
            "weak_or_inverse_context_rows": sum(1 for row in branch_context_rows if row.get("tick_context_decision") == "TICK_PRIMITIVE_WEAK_OR_INVERSE_CONTEXT"),
            "market_gap_key_rows": sum(1 for row in key_coverage_rows if row.get("coverage_status") == "MARKET_GAP_KEY_ONLY"),
            "current_branch_key_rows": sum(1 for row in key_coverage_rows if row.get("coverage_status") == "CURRENT_BRANCH_KEY_PRESENT"),
        },
        "system_decision": {
            "system_recommendation": (
                "TICK_PRIMITIVE_CONTEXT_JOIN_RESULT: every system-transfer branch now carries five tick primitive "
                "context rows; current branch coverage uses four symbol/session/horizon keys, while 400 tick "
                "primitive rows remain market gaps for expansion beyond the GBPJPY/XAUUSD branch queue."
            ),
            "branch_tick_context_rows": len(branch_context_rows),
            "branch_tick_summary_rows": len(branch_summary_rows),
            "market_gap_rows": len(market_gap_rows),
            "key_coverage_rows": len(key_coverage_rows),
            "family_primitive_rows": len(family_primitive_rows),
        },
        "source_manifest_hash": manifest_hash,
    }

    outputs = [
        (BRANCH_CONTEXT_LEDGER, branch_context_rows),
        (BRANCH_SUMMARY_LEDGER, branch_summary_rows),
        (MARKET_GAP_LEDGER, market_gap_rows),
        (KEY_COVERAGE_LEDGER, key_coverage_rows),
        (FAMILY_PRIMITIVE_LEDGER, family_primitive_rows),
        (QUESTION_LEDGER, question_rows),
        (SOURCE_MANIFEST_LEDGER, source_manifest),
    ]
    for path, rows in outputs:
        write_jsonl(path, rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Branch System Transfer Tick Primitive Context",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Branch tick context rows: `{len(branch_context_rows)}`",
                f"- Branch tick summary rows: `{len(branch_summary_rows)}`",
                f"- Market gap rows: `{len(market_gap_rows)}`",
                f"- Key coverage rows: `{len(key_coverage_rows)}`",
                f"- Family primitive rows: `{len(family_primitive_rows)}`",
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
                "type": "branch_system_transfer_tick_primitive_context",
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
                    "event_type": "branch_system_transfer_tick_primitive_context_built",
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
