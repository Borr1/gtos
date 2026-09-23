#!/usr/bin/env python3
"""Expand system-transfer work into tick primitive market-gap combinations."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

SYSTEM_TRANSFER_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_RECOMMENDATION_RESULT_2026-05-16.json"
SYSTEM_TRANSFER_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_RECOMMENDATION_BRANCH_LEDGER_2026-05-16.jsonl"
SYSTEM_TRANSFER_MARKET_SESSION = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_RECOMMENDATION_MARKET_SESSION_DECISION_LEDGER_2026-05-16.jsonl"
TICK_CONTEXT_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_TICK_PRIMITIVE_CONTEXT_RESULT_2026-05-16.json"
TICK_MARKET_GAP = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_TICK_PRIMITIVE_CONTEXT_MARKET_GAP_LEDGER_2026-05-16.jsonl"
TICK_KEY_COVERAGE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_TICK_PRIMITIVE_CONTEXT_KEY_COVERAGE_LEDGER_2026-05-16.jsonl"
TICK_BRANCH_SUMMARY = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_TICK_PRIMITIVE_CONTEXT_BRANCH_SUMMARY_LEDGER_2026-05-16.jsonl"
NOFILL_TRANSFER_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_NOFILL_AVOID_RETEST_JOIN_RESULT_2026-05-16.json"
NOFILL_TRANSFER_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_NOFILL_AVOID_RETEST_JOIN_BRANCH_SUMMARY_LEDGER_2026-05-16.jsonl"
CROSS_TRANSFER_RESULT = ROUTE_DIR / "TICK_M15_CROSS_HORIZON_SESSION_TRANSFER_RESULT_2026-05-16.json"
CROSS_BASE = ROUTE_DIR / "TICK_M15_CROSS_TRANSFER_BASE_ROW_LEDGER_2026-05-16.jsonl"
CROSS_HORIZON = ROUTE_DIR / "TICK_M15_CROSS_HORIZON_TRANSFER_MATRIX_2026-05-16.jsonl"
CROSS_SESSION = ROUTE_DIR / "TICK_M15_CROSS_SESSION_TRANSFER_MATRIX_2026-05-16.jsonl"
RESIDUAL_TRANSFER = ROUTE_DIR / "TICK_M15_RESIDUAL_TRANSFER_DIAGNOSIS_LEDGER_2026-05-16.jsonl"
RESIDUAL_MUTATION = ROUTE_DIR / "TICK_M15_TRANSFER_HYPOTHESIS_MUTATION_LEDGER_2026-05-16.jsonl"
PRIMITIVE_FLAG_SUMMARY = ROUTE_DIR / "TICK_M15_PRIMITIVE_FLAG_SUMMARY_LEDGER_2026-05-15.jsonl"
TARGET_MOVEMENT_FLAG_CONTROL = ROUTE_DIR / "TICK_M15_TARGET_MOVEMENT_FLAG_CONTROL_LEDGER_2026-05-15.jsonl"
TARGET_CONTROL_TRIAGE = ROUTE_DIR / "TICK_M15_TARGET_CONTROL_TRIAGE_LEDGER_2026-05-15.jsonl"
NEIGHBOR_PLACEBO = ROUTE_DIR / "TICK_M15_NEIGHBOR_PLACEBO_CONTROL_LEDGER_2026-05-15.jsonl"
FULL_PERMUTATION_CONCENTRATION = ROUTE_DIR / "TICK_M15_FULL_PERMUTATION_CONCENTRATION_LEDGER_2026-05-16.jsonl"
RESIDUAL_BLOCK_AWARE = ROUTE_DIR / "TICK_M15_RESIDUAL_BLOCK_AWARE_CONTROL_LEDGER_2026-05-16.jsonl"
TICK_PARQUET_SOURCE_CONTRACT = ROUTE_DIR / "TICK_PARQUET_SOURCE_CONTRACT_LEDGER_2026-05-15.jsonl"

PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_MARKET_GAP_PRIMITIVE_EXPANSION"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-16.json"
COMBO_LEDGER = ROUTE_DIR / f"{PREFIX}_COMBO_LEDGER_2026-05-16.jsonl"
KEY_LEDGER = ROUTE_DIR / f"{PREFIX}_KEY_LEDGER_2026-05-16.jsonl"
SYMBOL_SESSION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_LEDGER_2026-05-16.jsonl"
TRANSFER_CONTEXT_LEDGER = ROUTE_DIR / f"{PREFIX}_TRANSFER_CONTEXT_LEDGER_2026-05-16.jsonl"
ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_ACTION_LEDGER_2026-05-16.jsonl"
SOURCE_EXPANSION_QUEUE_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_EXPANSION_QUEUE_LEDGER_2026-05-16.jsonl"
ENTRY_GEOMETRY_QUEUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ENTRY_GEOMETRY_QUEUE_LEDGER_2026-05-16.jsonl"
AVOID_INVERSE_QUEUE_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_INVERSE_QUEUE_LEDGER_2026-05-16.jsonl"
RESIDUAL_TRANSFER_JOIN_LEDGER = ROUTE_DIR / f"{PREFIX}_RESIDUAL_TRANSFER_JOIN_LEDGER_2026-05-16.jsonl"
RESIDUAL_MUTATION_JOIN_LEDGER = ROUTE_DIR / f"{PREFIX}_RESIDUAL_MUTATION_JOIN_LEDGER_2026-05-16.jsonl"
NOFILL_CONTEXT_SIDECAR_LEDGER = ROUTE_DIR / f"{PREFIX}_NOFILL_CONTEXT_SIDECAR_LEDGER_2026-05-16.jsonl"
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
    "Branch system-transfer market-gap primitive expansion packet only. It preserves the 400 tick primitive "
    "market-gap combinations outside the current 386-branch denominator, routes them into source-expansion, "
    "entry-geometry, avoid/inverse, residual-transfer, and no-fill sidecar queues, and does not change live "
    "behavior or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion."
)

SESSION_MAP = {
    "ny_core_1300_1700": "ny_core",
    "tokyo_core_0000_0300": "tokyo_kz",
    "london_core_0700_1030": "london_core",
    "off_core_session": "off_core_session",
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
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def long_path(path: Path) -> str:
    path_text = str(path)
    if len(path_text) >= 240 and not path_text.startswith("\\\\?\\"):
        return "\\\\?\\" + path_text
    return path_text


def write_text(path: Path, text: str) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


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
                "source_manifest_id": f"OHLC-GTOS-MARKET-GAP-PRIM-SRC-{index:04d}",
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


def combo_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("symbol")),
        str(row.get("session_bucket")),
        str(row.get("horizon_id")),
        str(row.get("primitive_flag")),
    )


def key3(row: dict[str, Any]) -> tuple[str, str, str]:
    return (str(row.get("symbol")), str(row.get("session_bucket")), str(row.get("horizon_id")))


def action_for_movement(movement_status: str) -> tuple[str, str, bool]:
    if movement_status == "SMALL_N_LT20":
        return ("SOURCE_EXPANSION_QUEUE", "BUILD_SOURCE_EXPANSION_FOR_SMALL_N_MARKET_GAP", False)
    if movement_status == "POSITIVE_ABS_AND_NONNEGATIVE_ALIGNMENT_DELTA":
        return ("ENTRY_GEOMETRY_QUEUE", "BUILD_ENTRY_GEOMETRY_FOR_SUPPORTIVE_MARKET_GAP", False)
    if movement_status == "POSITIVE_ABS_NEGATIVE_ALIGNMENT_DELTA":
        return ("ENTRY_GEOMETRY_QUEUE", "BUILD_ENTRY_GEOMETRY_WITH_MIXED_ROUTER_FLAG", True)
    if movement_status == "FLAT_OR_NEGATIVE_ABS_DELTA":
        return ("AVOID_INVERSE_QUEUE", "BUILD_AVOID_INVERSE_CONTROL_FOR_WEAK_MARKET_GAP", False)
    return ("SOURCE_EXPANSION_QUEUE", "BUILD_SOURCE_EXPANSION_FOR_UNCLASSIFIED_MARKET_GAP", False)


def copy_metric_fields(row: dict[str, Any]) -> dict[str, Any]:
    fields = [
        "flagged_n",
        "control_n",
        "flagged_mean_abs_future_change",
        "control_mean_abs_future_change",
        "delta_mean_abs_future_change",
        "flagged_delta_alignment_rate",
        "control_delta_alignment_rate",
        "delta_alignment_rate",
        "movement_status",
        "triage_bucket",
        "placebo_bucket",
        "full_control_bucket",
        "block_low_tail_scheme_count",
        "block_weak_scheme_count",
    ]
    return {field: row.get(field) for field in fields if field in row}


def main() -> int:
    generated_at = now_utc()
    system_result = read_json(SYSTEM_TRANSFER_RESULT)
    tick_context_result = read_json(TICK_CONTEXT_RESULT)
    nofill_transfer_result = read_json(NOFILL_TRANSFER_RESULT)
    cross_transfer_result = read_json(CROSS_TRANSFER_RESULT)
    market_gap_rows = read_jsonl(TICK_MARKET_GAP)
    key_coverage_rows = read_jsonl(TICK_KEY_COVERAGE)
    branch_tick_rows = read_jsonl(TICK_BRANCH_SUMMARY)
    nofill_branch_rows = read_jsonl(NOFILL_TRANSFER_BRANCH)
    cross_base_rows = read_jsonl(CROSS_BASE)
    cross_horizon_rows = read_jsonl(CROSS_HORIZON)
    cross_session_rows = read_jsonl(CROSS_SESSION)
    residual_rows = read_jsonl(RESIDUAL_TRANSFER)
    mutation_rows = read_jsonl(RESIDUAL_MUTATION)

    source_inputs = [
        SYSTEM_TRANSFER_RESULT,
        SYSTEM_TRANSFER_BRANCH,
        SYSTEM_TRANSFER_MARKET_SESSION,
        TICK_CONTEXT_RESULT,
        TICK_MARKET_GAP,
        TICK_KEY_COVERAGE,
        TICK_BRANCH_SUMMARY,
        NOFILL_TRANSFER_RESULT,
        NOFILL_TRANSFER_BRANCH,
        CROSS_TRANSFER_RESULT,
        CROSS_BASE,
        CROSS_HORIZON,
        CROSS_SESSION,
        RESIDUAL_TRANSFER,
        RESIDUAL_MUTATION,
        PRIMITIVE_FLAG_SUMMARY,
        TARGET_MOVEMENT_FLAG_CONTROL,
        TARGET_CONTROL_TRIAGE,
        NEIGHBOR_PLACEBO,
        FULL_PERMUTATION_CONCENTRATION,
        RESIDUAL_BLOCK_AWARE,
        TICK_PARQUET_SOURCE_CONTRACT,
    ]
    source_manifest, manifest_hash = source_manifest_rows(source_inputs, generated_at)

    base_by_combo = {combo_key(row): row for row in cross_base_rows}
    horizon_by_key = {
        (str(row.get("symbol")), str(row.get("session_bucket")), str(row.get("primitive_flag"))): row
        for row in cross_horizon_rows
    }
    session_by_key = {
        (str(row.get("symbol")), str(row.get("primitive_flag")), str(row.get("horizon_id"))): row
        for row in cross_session_rows
    }
    residual_by_combo = {combo_key(row): row for row in residual_rows}
    mutations_by_queue: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in mutation_rows:
        mutations_by_queue[str(row.get("queue_id"))].append(row)
    current_branch_combos = {
        (
            str(row.get("join_symbol")),
            str(row.get("join_session_bucket")),
            str(row.get("join_horizon_id")),
            str(flag),
        )
        for row in branch_tick_rows
        for flag in (row.get("matched_tick_primitive_flags") or [])
    }
    if not current_branch_combos:
        current_branch_combos = {
            combo_key(row)
            for row in read_jsonl(ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_TICK_PRIMITIVE_CONTEXT_BRANCH_CONTEXT_LEDGER_2026-05-16.jsonl")
        }
    current_branch_keys = {combo[:3] for combo in current_branch_combos}
    market_gap_combos = {combo_key(row) for row in market_gap_rows}
    market_gap_keys = {combo[:3] for combo in market_gap_combos}
    nofill_context_by_symbol_session: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in nofill_branch_rows:
        nofill_context_by_symbol_session[(str(row.get("symbol")), str(row.get("route_session")))].append(row)

    combo_rows: list[dict[str, Any]] = []
    transfer_context_rows: list[dict[str, Any]] = []
    action_rows: list[dict[str, Any]] = []
    source_expansion_rows: list[dict[str, Any]] = []
    entry_geometry_rows: list[dict[str, Any]] = []
    avoid_inverse_rows: list[dict[str, Any]] = []
    residual_join_rows: list[dict[str, Any]] = []
    residual_mutation_join_rows: list[dict[str, Any]] = []
    nofill_sidecar_rows: list[dict[str, Any]] = []

    for index, row in enumerate(sorted(market_gap_rows, key=combo_key), 1):
        combo = combo_key(row)
        base = base_by_combo.get(combo, {})
        horizon_matrix = horizon_by_key.get((combo[0], combo[1], combo[3]), {})
        session_matrix = session_by_key.get((combo[0], combo[3], combo[2]), {})
        residual = residual_by_combo.get(combo)
        movement_status = str(row.get("movement_status"))
        action_class, action, mixed_router = action_for_movement(movement_status)
        mapped_session = SESSION_MAP.get(combo[1], combo[1])
        nofill_context_rows = nofill_context_by_symbol_session.get((combo[0], mapped_session), [])
        nofill_context_available = bool(nofill_context_rows)
        combo_common = {
            "market_gap_combo_id": f"OHLC-GTOS-MARKET-GAP-PRIM-COMBO-{index:05d}",
            "symbol": combo[0],
            "session_bucket": combo[1],
            "mapped_route_session": mapped_session,
            "horizon_id": combo[2],
            "primitive_flag": combo[3],
            "movement_status": movement_status,
            "tick_context_decision": row.get("tick_context_decision"),
            "triage_bucket": row.get("triage_bucket"),
            "gap_reason": row.get("gap_reason"),
            "action_class": action_class,
            "next_same_resource_action": action,
            "mixed_router_flag": mixed_router,
            "outside_current_branch_denominator": True,
            "outside_gbpjpy_xauusd_current_branch_box": combo[0] not in {"GBPJPY", "XAUUSD"},
            "current_branch_combo_overlap": combo in current_branch_combos,
            "current_branch_key_overlap": combo[:3] in current_branch_keys,
            "horizon_transfer_pattern": horizon_matrix.get("transfer_pattern"),
            "session_transfer_pattern": session_matrix.get("transfer_pattern"),
            "horizon_status_counts": horizon_matrix.get("status_counts"),
            "session_status_counts": session_matrix.get("status_counts"),
            "residual_queue_id": residual.get("queue_id") if residual else None,
            "residual_transfer_class": residual.get("residual_transfer_class") if residual else None,
            "nofill_sidecar_status": (
                "SAME_SYMBOL_SESSION_NOFILL_CONTEXT_AVAILABLE"
                if nofill_context_available
                else "NO_SAME_SYMBOL_SESSION_NOFILL_CONTEXT"
            ),
            "nofill_context_branch_rows": len(nofill_context_rows),
            **copy_metric_fields(row),
        }
        combo_rows.append(with_common(dict(combo_common), generated_at, manifest_hash))
        transfer_context_rows.append(
            with_common(
                {
                    "market_gap_transfer_context_id": f"OHLC-GTOS-MARKET-GAP-PRIM-TRANSFER-{index:05d}",
                    **combo_common,
                    "base_join_status": "JOINED_CROSS_TRANSFER_BASE_ROW" if base else "MISSING_CROSS_TRANSFER_BASE_ROW",
                    "horizon_matrix_join_status": "JOINED_CROSS_HORIZON_MATRIX_ROW" if horizon_matrix else "MISSING_CROSS_HORIZON_MATRIX_ROW",
                    "session_matrix_join_status": "JOINED_CROSS_SESSION_MATRIX_ROW" if session_matrix else "MISSING_CROSS_SESSION_MATRIX_ROW",
                    "residual_transfer_join_status": "JOINED_RESIDUAL_TRANSFER_ROW" if residual else "NO_RESIDUAL_TRANSFER_ROW_FOR_COMBO",
                    "base_metrics": copy_metric_fields(base),
                },
                generated_at,
                manifest_hash,
            )
        )
        action_row = with_common(
            {
                "market_gap_action_id": f"OHLC-GTOS-MARKET-GAP-PRIM-ACTION-{index:05d}",
                **combo_common,
                "action_status": "OPEN_SAME_RESOURCE_NEXT_PACKET",
            },
            generated_at,
            manifest_hash,
        )
        action_rows.append(action_row)
        if action_class == "SOURCE_EXPANSION_QUEUE":
            source_expansion_rows.append(dict(action_row, source_expansion_reason="SMALL_N_OR_UNCLASSIFIED_MARKET_GAP"))
        elif action_class == "ENTRY_GEOMETRY_QUEUE":
            entry_geometry_rows.append(
                dict(
                    action_row,
                    entry_geometry_reason=(
                        "POSITIVE_ABS_NEGATIVE_ALIGNMENT_MIXED_ROUTER"
                        if mixed_router
                        else "POSITIVE_ABS_NONNEGATIVE_ALIGNMENT_SUPPORTIVE_ROUTER"
                    ),
                )
            )
        elif action_class == "AVOID_INVERSE_QUEUE":
            avoid_inverse_rows.append(dict(action_row, avoid_inverse_reason="FLAT_OR_NEGATIVE_ABS_DELTA_MARKET_GAP"))
        if residual:
            residual_join = with_common(
                {
                    "market_gap_residual_transfer_join_id": f"OHLC-GTOS-MARKET-GAP-PRIM-RESIDUAL-{len(residual_join_rows) + 1:05d}",
                    **combo_common,
                    "queue_id": residual.get("queue_id"),
                    "residual_transfer_class": residual.get("residual_transfer_class"),
                    "same_session_horizon_transfer_pattern": residual.get("same_session_horizon_transfer_pattern"),
                    "same_horizon_session_transfer_pattern": residual.get("same_horizon_session_transfer_pattern"),
                    "same_session_horizon_status_counts": residual.get("same_session_horizon_status_counts"),
                    "same_horizon_session_status_counts": residual.get("same_horizon_session_status_counts"),
                    "residual_join_status": "JOINED_MARKET_GAP_RESIDUAL_TRANSFER",
                },
                generated_at,
                manifest_hash,
            )
            residual_join_rows.append(residual_join)
            for mutation in mutations_by_queue.get(str(residual.get("queue_id")), []):
                residual_mutation_join_rows.append(
                    with_common(
                        {
                            "market_gap_residual_mutation_join_id": f"OHLC-GTOS-MARKET-GAP-PRIM-MUTATION-{len(residual_mutation_join_rows) + 1:05d}",
                            **combo_common,
                            "queue_id": mutation.get("queue_id"),
                            "mutation_id": mutation.get("mutation_id"),
                            "mutation_type": mutation.get("mutation_type"),
                            "mutation_action": mutation.get("action"),
                            "transfer_class": mutation.get("transfer_class"),
                            "mutation_status": mutation.get("status"),
                        },
                        generated_at,
                        manifest_hash,
                    )
                )
        nofill_sidecar_rows.append(
            with_common(
                {
                    "market_gap_nofill_sidecar_id": f"OHLC-GTOS-MARKET-GAP-PRIM-NOFILL-{index:05d}",
                    **combo_common,
                    "nofill_context_status": (
                        "SAME_SYMBOL_SESSION_CONTEXT_AVAILABLE"
                        if nofill_context_available
                        else "NO_SAME_SYMBOL_SESSION_CONTEXT"
                    ),
                    "nofill_join_status_counts": compact_counter(Counter(context.get("nofill_join_status") for context in nofill_context_rows)),
                    "nofill_transfer_implication_counts": compact_counter(Counter(context.get("nofill_transfer_implication") for context in nofill_context_rows)),
                    "nofill_sidecar_filters_market_gap_denominator": False,
                },
                generated_at,
                manifest_hash,
            )
        )

    key_rows: list[dict[str, Any]] = []
    by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in combo_rows:
        by_key[(row["symbol"], row["session_bucket"], row["horizon_id"])].append(row)
    for key, rows in sorted(by_key.items()):
        key_rows.append(
            with_common(
                {
                    "market_gap_key_id": f"OHLC-GTOS-MARKET-GAP-PRIM-KEY-{len(key_rows) + 1:05d}",
                    "symbol": key[0],
                    "session_bucket": key[1],
                    "mapped_route_session": SESSION_MAP.get(key[1], key[1]),
                    "horizon_id": key[2],
                    "market_gap_combo_rows": len(rows),
                    "primitive_flags": sorted(row["primitive_flag"] for row in rows),
                    "movement_status_counts": compact_counter(Counter(row["movement_status"] for row in rows)),
                    "action_class_counts": compact_counter(Counter(row["action_class"] for row in rows)),
                    "coverage_status": "MARKET_GAP_KEY_ONLY",
                    "current_branch_key_overlap": key in current_branch_keys,
                },
                generated_at,
                manifest_hash,
            )
        )

    symbol_session_rows: list[dict[str, Any]] = []
    by_symbol_session: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in combo_rows:
        by_symbol_session[(row["symbol"], row["session_bucket"])].append(row)
    for key, rows in sorted(by_symbol_session.items()):
        symbol_session_rows.append(
            with_common(
                {
                    "market_gap_symbol_session_id": f"OHLC-GTOS-MARKET-GAP-PRIM-SYMSESS-{len(symbol_session_rows) + 1:04d}",
                    "symbol": key[0],
                    "session_bucket": key[1],
                    "mapped_route_session": SESSION_MAP.get(key[1], key[1]),
                    "market_gap_combo_rows": len(rows),
                    "horizon_counts": compact_counter(Counter(row["horizon_id"] for row in rows)),
                    "primitive_counts": compact_counter(Counter(row["primitive_flag"] for row in rows)),
                    "movement_status_counts": compact_counter(Counter(row["movement_status"] for row in rows)),
                    "action_class_counts": compact_counter(Counter(row["action_class"] for row in rows)),
                    "nofill_context_combo_rows": sum(1 for row in rows if row["nofill_sidecar_status"] == "SAME_SYMBOL_SESSION_NOFILL_CONTEXT_AVAILABLE"),
                },
                generated_at,
                manifest_hash,
            )
        )

    bucket_sources = {
        "symbol": Counter(row["symbol"] for row in combo_rows),
        "session_bucket": Counter(row["session_bucket"] for row in combo_rows),
        "horizon_id": Counter(row["horizon_id"] for row in combo_rows),
        "primitive_flag": Counter(row["primitive_flag"] for row in combo_rows),
        "movement_status": Counter(row["movement_status"] for row in combo_rows),
        "action_class": Counter(row["action_class"] for row in action_rows),
        "horizon_transfer_pattern": Counter(row.get("horizon_transfer_pattern") for row in combo_rows),
        "session_transfer_pattern": Counter(row.get("session_transfer_pattern") for row in combo_rows),
        "outside_gbpjpy_xauusd_current_branch_box": Counter(row.get("outside_gbpjpy_xauusd_current_branch_box") for row in combo_rows),
        "nofill_sidecar_status": Counter(row.get("nofill_sidecar_status") for row in combo_rows),
        "residual_transfer_join_status": Counter(row.get("residual_transfer_join_status") for row in transfer_context_rows),
        "mutation_type": Counter(row.get("mutation_type") for row in residual_mutation_join_rows),
    }
    bucket_rows: list[dict[str, Any]] = []
    for category, counter in sorted(bucket_sources.items()):
        for value, row_count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                with_common(
                    {
                        "market_gap_bucket_id": f"OHLC-GTOS-MARKET-GAP-PRIM-BUCKET-{len(bucket_rows) + 1:05d}",
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
            "question_id": "OHLC-GTOS-MARKET-GAP-PRIM-QUESTION-001",
            "question": "Which tick primitive combinations are outside the current branch denominator?",
            "answer_route": "Use COMBO_LEDGER; it preserves all 400 market-gap combinations with symbol, session, horizon, and primitive flag.",
        },
        {
            "question_id": "OHLC-GTOS-MARKET-GAP-PRIM-QUESTION-002",
            "question": "Which market gaps require source expansion rather than strategy scoring?",
            "answer_route": "Use SOURCE_EXPANSION_QUEUE_LEDGER; it preserves all 309 SMALL_N_LT20 market-gap rows.",
        },
        {
            "question_id": "OHLC-GTOS-MARKET-GAP-PRIM-QUESTION-003",
            "question": "Which market gaps become entry-geometry or mixed-router work?",
            "answer_route": "Use ENTRY_GEOMETRY_QUEUE_LEDGER; it preserves 42 supportive and 26 mixed-router rows.",
        },
        {
            "question_id": "OHLC-GTOS-MARKET-GAP-PRIM-QUESTION-004",
            "question": "Which market gaps become avoid/inverse controls?",
            "answer_route": "Use AVOID_INVERSE_QUEUE_LEDGER; it preserves all 23 FLAT_OR_NEGATIVE_ABS_DELTA rows.",
        },
        {
            "question_id": "OHLC-GTOS-MARKET-GAP-PRIM-QUESTION-005",
            "question": "Which market gaps have residual transfer and mutation context?",
            "answer_route": "Use RESIDUAL_TRANSFER_JOIN_LEDGER and RESIDUAL_MUTATION_JOIN_LEDGER; they preserve 18 residual rows and 54 mutation rows.",
        },
        {
            "question_id": "OHLC-GTOS-MARKET-GAP-PRIM-QUESTION-006",
            "question": "How does no-fill context attach without filtering the market-gap denominator?",
            "answer_route": "Use NOFILL_CONTEXT_SIDECAR_LEDGER; it preserves 400 rows and marks 25 same-symbol/session context rows as sidecar only.",
        },
    ]
    for row in question_rows:
        with_common(row, generated_at, manifest_hash)

    counts = {
        "input_system_transfer_branch_rows": len(read_jsonl(SYSTEM_TRANSFER_BRANCH)),
        "input_tick_market_gap_rows": len(market_gap_rows),
        "input_tick_key_coverage_rows": len(key_coverage_rows),
        "input_tick_branch_summary_rows": len(branch_tick_rows),
        "input_nofill_branch_summary_rows": len(nofill_branch_rows),
        "input_cross_base_rows": len(cross_base_rows),
        "input_cross_horizon_rows": len(cross_horizon_rows),
        "input_cross_session_rows": len(cross_session_rows),
        "input_residual_transfer_rows": len(residual_rows),
        "input_residual_mutation_rows": len(mutation_rows),
        "combo_rows": len(combo_rows),
        "key_rows": len(key_rows),
        "symbol_session_rows": len(symbol_session_rows),
        "transfer_context_rows": len(transfer_context_rows),
        "action_rows": len(action_rows),
        "source_expansion_queue_rows": len(source_expansion_rows),
        "entry_geometry_queue_rows": len(entry_geometry_rows),
        "avoid_inverse_queue_rows": len(avoid_inverse_rows),
        "residual_transfer_join_rows": len(residual_join_rows),
        "residual_mutation_join_rows": len(residual_mutation_join_rows),
        "nofill_context_sidecar_rows": len(nofill_sidecar_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "current_branch_combo_rows": len(current_branch_combos),
        "full_tick_transfer_base_rows": len(cross_base_rows),
        "market_gap_combo_rows_outside_gbpjpy_xauusd": sum(1 for row in combo_rows if row["outside_gbpjpy_xauusd_current_branch_box"]),
        "market_gap_combo_rows_inside_gbpjpy_xauusd_outside_current_keys": sum(1 for row in combo_rows if not row["outside_gbpjpy_xauusd_current_branch_box"]),
    }
    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_MARKET_GAP_PRIMITIVE_EXPANSION",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": counts,
        "upstream_counts": {
            "system_transfer": system_result.get("counts", {}),
            "tick_context": tick_context_result.get("counts", {}),
            "nofill_transfer": nofill_transfer_result.get("counts", {}),
            "cross_transfer": cross_transfer_result.get("counts", {}),
        },
        "join_diagnostics": {
            "join_key_fields": {
                "market_gap_to_cross_base": ["symbol", "session_bucket", "horizon_id", "primitive_flag"],
                "market_gap_to_key_coverage": ["symbol", "session_bucket", "horizon_id"],
                "market_gap_to_cross_horizon": ["symbol", "session_bucket", "primitive_flag"],
                "market_gap_to_cross_session": ["symbol", "primitive_flag", "horizon_id"],
                "market_gap_to_residual_transfer": ["symbol", "session_bucket", "primitive_flag", "horizon_id"],
                "residual_transfer_to_mutation": ["queue_id"],
                "market_gap_to_nofill_sidecar": ["symbol", "mapped_route_session"],
            },
            "market_gap_combo_count": len(market_gap_combos),
            "current_branch_combo_count": len(current_branch_combos),
            "union_combo_count": len(market_gap_combos | current_branch_combos),
            "market_gap_key_count": len(market_gap_keys),
            "current_branch_key_count": len(current_branch_keys),
            "union_key_count": len(market_gap_keys | current_branch_keys),
            "base_missing_combo_count": sum(1 for row in combo_rows if row.get("base_join_status") == "MISSING_CROSS_TRANSFER_BASE_ROW"),
            "residual_join_queue_ids": sorted(row.get("queue_id") for row in residual_join_rows),
        },
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_sources.items())},
        "system_decision": {
            "system_recommendation": (
                "MARKET_GAP_PRIMITIVE_EXPANSION_RESULT: the next denominator is 400 tick primitive "
                "market-gap combinations outside the current branch rows; route 309 to source expansion, "
                "68 to entry-geometry/mixed-router work, 23 to avoid/inverse controls, and preserve 18 "
                "residual transfer plus 54 mutation rows. Continue into these executable queues and the "
                "route-mechanic matrix rather than treating GBPJPY/XAUUSD concentration as the full search."
            ),
            "combo_rows": len(combo_rows),
            "source_expansion_queue_rows": len(source_expansion_rows),
            "entry_geometry_queue_rows": len(entry_geometry_rows),
            "avoid_inverse_queue_rows": len(avoid_inverse_rows),
            "residual_transfer_join_rows": len(residual_join_rows),
            "residual_mutation_join_rows": len(residual_mutation_join_rows),
            "nofill_context_sidecar_rows": len(nofill_sidecar_rows),
            "nofill_context_available_combo_rows": sum(
                1 for row in nofill_sidecar_rows if row.get("nofill_context_status") == "SAME_SYMBOL_SESSION_CONTEXT_AVAILABLE"
            ),
        },
        "source_manifest_hash": manifest_hash,
    }

    outputs = [
        (COMBO_LEDGER, combo_rows),
        (KEY_LEDGER, key_rows),
        (SYMBOL_SESSION_LEDGER, symbol_session_rows),
        (TRANSFER_CONTEXT_LEDGER, transfer_context_rows),
        (ACTION_LEDGER, action_rows),
        (SOURCE_EXPANSION_QUEUE_LEDGER, source_expansion_rows),
        (ENTRY_GEOMETRY_QUEUE_LEDGER, entry_geometry_rows),
        (AVOID_INVERSE_QUEUE_LEDGER, avoid_inverse_rows),
        (RESIDUAL_TRANSFER_JOIN_LEDGER, residual_join_rows),
        (RESIDUAL_MUTATION_JOIN_LEDGER, residual_mutation_join_rows),
        (NOFILL_CONTEXT_SIDECAR_LEDGER, nofill_sidecar_rows),
        (BUCKET_LEDGER, bucket_rows),
        (QUESTION_LEDGER, question_rows),
        (SOURCE_MANIFEST_LEDGER, source_manifest),
    ]
    for path, rows in outputs:
        write_jsonl(path, rows)
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Branch System Transfer Market-Gap Primitive Expansion",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Market-gap combo rows: `{len(combo_rows)}`",
                f"- Key rows: `{len(key_rows)}`",
                f"- Source-expansion queue rows: `{len(source_expansion_rows)}`",
                f"- Entry-geometry queue rows: `{len(entry_geometry_rows)}`",
                f"- Avoid/inverse queue rows: `{len(avoid_inverse_rows)}`",
                f"- Residual transfer rows: `{len(residual_join_rows)}`",
                f"- Residual mutation rows: `{len(residual_mutation_join_rows)}`",
            ]
        )
        + "\n"
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
                "type": "branch_system_transfer_market_gap_primitive_expansion",
                "generated_utc": generated_at,
                "counts": result["counts"],
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest["safe_flags"] = SAFE_FLAGS
    write_text(OUTPUT_MANIFEST, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "timestamp_utc": generated_at,
                    "event_type": "branch_system_transfer_market_gap_primitive_expansion_built",
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
    print(json.dumps({"ok": True, "counts": counts, "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
