#!/usr/bin/env python3
"""Execute source materialization/proxy reconstruction for unified source rows.

This builder consumes the 309 source-materialization queue rows produced by the
shadow scorer and the tick/M15 source ledgers. It attempts every current
same-resource reconstruction available in this route: targetable event counts,
fail-closed horizon counts, primitive source flags, cross-session/symbol source
proxies, and transfer matrices. It emits decision rows rather than another
queue.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_source_materialization import (
    MATERIALIZATION_SURFACE,
    exact_missing_reason,
    materialization_proxy_fields,
)


SHADOW_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_SHADOW_SCORER_EXECUTION"
REPLAY_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_VARIANT_REPLAY_ACQUISITION"
MARKET_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_MARKET_GAP_PRIMITIVE_EXPANSION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_SOURCE_MATERIALIZATION_EXECUTION"

SHADOW_RESULT = ROUTE_DIR / f"{SHADOW_PREFIX}_RESULT_2026-05-17.json"
SOURCE_QUEUE = ROUTE_DIR / f"{SHADOW_PREFIX}_SOURCE_MATERIALIZATION_QUEUE_LEDGER_2026-05-17.jsonl"
REPLAY_SOURCE = ROUTE_DIR / f"{REPLAY_PREFIX}_SOURCE_ACQUISITION_PROXY_RESULT_LEDGER_2026-05-17.jsonl"
MARKET_SOURCE = ROUTE_DIR / f"{MARKET_PREFIX}_SOURCE_EXPANSION_QUEUE_LEDGER_2026-05-16.jsonl"
TICK_EVENT = ROUTE_DIR / "TICK_M15_TARGET_MOVEMENT_EVENT_LEDGER_2026-05-15.jsonl"
TICK_FAIL = ROUTE_DIR / "TICK_M15_TARGET_MOVEMENT_FAIL_CLOSED_LEDGER_2026-05-15.jsonl"
TICK_PRIMITIVE_SUMMARY = ROUTE_DIR / "TICK_M15_PRIMITIVE_FLAG_SUMMARY_LEDGER_2026-05-15.jsonl"
TICK_FLAG_CONTROL = ROUTE_DIR / "TICK_M15_TARGET_MOVEMENT_FLAG_CONTROL_LEDGER_2026-05-15.jsonl"
TICK_CROSS_BASE = ROUTE_DIR / "TICK_M15_CROSS_TRANSFER_BASE_ROW_LEDGER_2026-05-16.jsonl"
TICK_CROSS_HORIZON = ROUTE_DIR / "TICK_M15_CROSS_HORIZON_TRANSFER_MATRIX_2026-05-16.jsonl"
TICK_CROSS_SESSION = ROUTE_DIR / "TICK_M15_CROSS_SESSION_TRANSFER_MATRIX_2026-05-16.jsonl"
TICK_FULL_PERM = ROUTE_DIR / "TICK_M15_FULL_PERMUTATION_CONCENTRATION_LEDGER_2026-05-16.jsonl"
HELPER_MODULE = REPO / "src/research_infra/moonshot_source_materialization.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
MATERIALIZATION_LEDGER = ROUTE_DIR / f"{PREFIX}_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
GAP_CLOSURE_LEDGER = ROUTE_DIR / f"{PREFIX}_GAP_CLOSURE_LEDGER_2026-05-17.jsonl"
FAMILY_PROXY_LEDGER = ROUTE_DIR / f"{PREFIX}_FAMILY_PROXY_LEDGER_2026-05-17.jsonl"
SYMBOL_SESSION_HORIZON_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_HORIZON_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Unified source materialization execution packet only. It reconstructs current targetable rows, "
    "fail-closed horizon rows, source-flag denominators, and source-expansion proxies for the 309 source "
    "queue rows. It does not change live behavior, place orders, or claim broker R/PnL, realized expectancy, "
    "win-rate, validation, live-readiness, or promotion."
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def long_path(path: Path) -> str:
    path_text = str(path)
    if len(path_text) >= 240 and not path_text.startswith("\\\\?\\"):
        return "\\\\?\\" + path_text
    return path_text


def read_json(path: Path) -> dict[str, Any]:
    with open(long_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_text(path: Path, text: str) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str | None:
    digest = hashlib.sha256()
    try:
        with open(long_path(path), "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except FileNotFoundError:
        return None
    return digest.hexdigest()


def source_manifest_rows(paths: list[Path], generated_at: str) -> tuple[list[dict[str, Any]], str]:
    rows: list[dict[str, Any]] = []
    for index, path in enumerate(paths, 1):
        file_hash = sha256_file(path)
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-UNIFIED-SRCMAT-SRC-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": file_hash,
                "status": "HASHED" if file_hash else "MISSING",
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


def key4(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("symbol")),
        str(row.get("session_bucket")),
        str(row.get("horizon_id")),
        str(row.get("primitive_flag")),
    )


def key3(row: dict[str, Any]) -> tuple[str, str, str]:
    return (str(row.get("symbol")), str(row.get("session_bucket")), str(row.get("primitive_flag")))


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def mean_or_none(values: list[float]) -> float | None:
    return round(mean(values), 9) if values else None


def compact_counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(row.get(key)) for row in rows)
    return {key_: int(counter[key_]) for key_ in sorted(counter)}


def build_indexes(
    event_rows: list[dict[str, Any]],
    fail_rows: list[dict[str, Any]],
    primitive_rows: list[dict[str, Any]],
    base_rows: list[dict[str, Any]],
    flag_control_rows: list[dict[str, Any]],
    cross_horizon_rows: list[dict[str, Any]],
    cross_session_rows: list[dict[str, Any]],
    full_perm_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    targetable_by_combo: Counter[tuple[str, str, str, str]] = Counter()
    targetable_alignment_by_combo: Counter[tuple[str, str, str, str]] = Counter()
    targetable_abs_change_by_combo: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)
    targetable_by_symbol_horizon_primitive: Counter[tuple[str, str, str]] = Counter()
    targetable_by_session_horizon_primitive: Counter[tuple[str, str, str]] = Counter()
    targetable_by_primitive_horizon: Counter[tuple[str, str]] = Counter()
    targetable_by_symbol_session_horizon_all_primitives: Counter[tuple[str, str, str]] = Counter()

    for row in event_rows:
        flags = row.get("primitive_flags") or []
        if not flags:
            continue
        for flag in flags:
            combo = (str(row.get("symbol")), str(row.get("session_bucket")), str(row.get("horizon_id")), str(flag))
            targetable_by_combo[combo] += 1
            if row.get("delta_aligned_with_future"):
                targetable_alignment_by_combo[combo] += 1
            abs_change = to_float(row.get("future_abs_change"))
            if abs_change is not None:
                targetable_abs_change_by_combo[combo].append(abs_change)
            targetable_by_symbol_horizon_primitive[(combo[0], combo[2], combo[3])] += 1
            targetable_by_session_horizon_primitive[(combo[1], combo[2], combo[3])] += 1
            targetable_by_primitive_horizon[(combo[3], combo[2])] += 1
            targetable_by_symbol_session_horizon_all_primitives[(combo[0], combo[1], combo[2])] += 1

    fail_by_combo: Counter[tuple[str, str, str, str]] = Counter()
    fail_reasons_by_combo: dict[tuple[str, str, str, str], Counter[str]] = defaultdict(Counter)
    for row in fail_rows:
        for flag in row.get("primitive_flags") or []:
            combo = (str(row.get("symbol")), str(row.get("session_bucket")), str(row.get("horizon_id")), str(flag))
            fail_by_combo[combo] += 1
            fail_reasons_by_combo[combo][str(row.get("fail_reason") or "UNKNOWN_FAIL_REASON")] += 1

    primitive_summary = {
        (str(row.get("symbol")), str(row.get("session_bucket")), str(row.get("primitive_flag"))): row
        for row in primitive_rows
    }
    source_by_symbol_primitive: Counter[tuple[str, str]] = Counter()
    source_by_session_primitive: Counter[tuple[str, str]] = Counter()
    source_by_primitive: Counter[str] = Counter()
    source_by_symbol_session_all_primitives: Counter[tuple[str, str]] = Counter()
    for row in primitive_rows:
        flagged = int(row.get("flagged_bar_count") or 0)
        symbol = str(row.get("symbol"))
        session = str(row.get("session_bucket"))
        primitive = str(row.get("primitive_flag"))
        source_by_symbol_primitive[(symbol, primitive)] += flagged
        source_by_session_primitive[(session, primitive)] += flagged
        source_by_primitive[primitive] += flagged
        source_by_symbol_session_all_primitives[(symbol, session)] += flagged

    return {
        "targetable_by_combo": targetable_by_combo,
        "targetable_alignment_by_combo": targetable_alignment_by_combo,
        "targetable_abs_change_by_combo": targetable_abs_change_by_combo,
        "targetable_by_symbol_horizon_primitive": targetable_by_symbol_horizon_primitive,
        "targetable_by_session_horizon_primitive": targetable_by_session_horizon_primitive,
        "targetable_by_primitive_horizon": targetable_by_primitive_horizon,
        "targetable_by_symbol_session_horizon_all_primitives": targetable_by_symbol_session_horizon_all_primitives,
        "fail_by_combo": fail_by_combo,
        "fail_reasons_by_combo": fail_reasons_by_combo,
        "primitive_summary": primitive_summary,
        "source_by_symbol_primitive": source_by_symbol_primitive,
        "source_by_session_primitive": source_by_session_primitive,
        "source_by_primitive": source_by_primitive,
        "source_by_symbol_session_all_primitives": source_by_symbol_session_all_primitives,
        "base_by_combo": {key4(row): row for row in base_rows},
        "flag_control_by_combo": {key4(row): row for row in flag_control_rows},
        "cross_horizon_by_key": {
            (str(row.get("symbol")), str(row.get("session_bucket")), str(row.get("primitive_flag"))): row
            for row in cross_horizon_rows
        },
        "cross_session_by_key": {
            (str(row.get("symbol")), str(row.get("horizon_id")), str(row.get("primitive_flag"))): row
            for row in cross_session_rows
        },
        "full_perm_by_combo": {key4(row): row for row in full_perm_rows},
    }


def metrics_for_row(row: dict[str, Any], indexes: dict[str, Any]) -> dict[str, Any]:
    combo = key4(row)
    symbol, session, horizon, primitive = combo
    source_key = (symbol, session, primitive)
    primitive_summary = indexes["primitive_summary"].get(source_key, {})
    targetable = int(indexes["targetable_by_combo"].get(combo, 0))
    aligned = int(indexes["targetable_alignment_by_combo"].get(combo, 0))
    abs_changes = indexes["targetable_abs_change_by_combo"].get(combo, [])
    source_flagged = int(primitive_summary.get("flagged_bar_count") or 0)
    denominator_bars = int(primitive_summary.get("denominator_bar_count") or 0)
    failclosed = int(indexes["fail_by_combo"].get(combo, 0))
    same_symbol_targetable = int(indexes["targetable_by_symbol_horizon_primitive"].get((symbol, horizon, primitive), 0))
    same_session_targetable = int(indexes["targetable_by_session_horizon_primitive"].get((session, horizon, primitive), 0))
    all_market_targetable = int(indexes["targetable_by_primitive_horizon"].get((primitive, horizon), 0))
    symbol_session_all_primitives_targetable = int(
        indexes["targetable_by_symbol_session_horizon_all_primitives"].get((symbol, session, horizon), 0)
    )
    return {
        "current_targetable_flagged_n": targetable,
        "current_targetable_delta_alignment_n": aligned,
        "current_targetable_delta_alignment_rate": round(aligned / targetable, 9) if targetable else None,
        "current_targetable_mean_abs_future_change": mean_or_none(abs_changes),
        "current_source_flagged_n": source_flagged,
        "current_source_denominator_bar_count": denominator_bars,
        "current_source_flagged_pct": primitive_summary.get("flagged_bar_pct"),
        "current_failclosed_flagged_n": failclosed,
        "current_failclosed_reason_counts": {
            key: int(value) for key, value in sorted(indexes["fail_reasons_by_combo"].get(combo, {}).items())
        },
        "current_source_non_targetable_flagged_n": max(0, source_flagged - targetable),
        "current_source_unexplained_after_failclosed_n": max(0, source_flagged - targetable - failclosed),
        "same_symbol_all_sessions_source_flagged_n": int(
            indexes["source_by_symbol_primitive"].get((symbol, primitive), 0)
        ),
        "same_session_all_symbols_source_flagged_n": int(
            indexes["source_by_session_primitive"].get((session, primitive), 0)
        ),
        "all_market_primitive_source_flagged_n": int(indexes["source_by_primitive"].get(primitive, 0)),
        "same_symbol_session_all_primitives_source_flagged_n": int(
            indexes["source_by_symbol_session_all_primitives"].get((symbol, session), 0)
        ),
        "same_symbol_all_sessions_targetable_flagged_n": same_symbol_targetable,
        "same_session_all_symbols_targetable_flagged_n": same_session_targetable,
        "all_market_primitive_targetable_flagged_n": all_market_targetable,
        "same_symbol_session_all_primitives_targetable_flagged_n": symbol_session_all_primitives_targetable,
        "cross_horizon_transfer_pattern": (
            indexes["cross_horizon_by_key"].get((symbol, session, primitive), {}).get("transfer_pattern")
        ),
        "cross_session_transfer_pattern": (
            indexes["cross_session_by_key"].get((symbol, horizon, primitive), {}).get("transfer_pattern")
        ),
        "full_permutation_flagged_n": (
            indexes["full_perm_by_combo"].get(combo, {}).get("flagged_n")
            if combo in indexes["full_perm_by_combo"]
            else None
        ),
        "full_permutation_control_bucket": (
            indexes["full_perm_by_combo"].get(combo, {}).get("control_bucket")
            if combo in indexes["full_perm_by_combo"]
            else None
        ),
    }


def build_materialization_rows(
    queue_rows: list[dict[str, Any]],
    replay_source_rows: list[dict[str, Any]],
    market_source_rows: list[dict[str, Any]],
    indexes: dict[str, Any],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    replay_by_key = {key4(row): row for row in replay_source_rows}
    market_by_key = {key4(row): row for row in market_source_rows}
    materialized: list[dict[str, Any]] = []
    gap_rows: list[dict[str, Any]] = []
    for index, queue_row in enumerate(queue_rows, 1):
        combo = key4(queue_row)
        replay = replay_by_key.get(combo, {})
        market = market_by_key.get(combo, {})
        metrics = metrics_for_row(queue_row, indexes)
        proxy = materialization_proxy_fields({**replay, **queue_row}, metrics)
        row = with_common(
            {
                "source_materialization_execution_id": f"OHLC-GTOS-UNIFIED-SRCMAT-ROW-{index:05d}",
                "shadow_scorer_execution_id": queue_row.get("shadow_scorer_execution_id"),
                "source_code_candidate_id": queue_row.get("source_code_candidate_id"),
                "source_acquisition_proxy_result_id": replay.get("source_acquisition_proxy_result_id"),
                "market_gap_combo_id": replay.get("market_gap_combo_id") or market.get("market_gap_combo_id"),
                "source_expansion_requirement_id": replay.get("source_expansion_requirement_id"),
                "symbol": queue_row.get("symbol"),
                "route_session": queue_row.get("route_session"),
                "session_bucket": queue_row.get("session_bucket"),
                "horizon_id": queue_row.get("horizon_id"),
                "primitive_flag": queue_row.get("primitive_flag"),
                "outside_gbpjpy_xauusd_current_branch_box": queue_row.get(
                    "outside_gbpjpy_xauusd_current_branch_box"
                ),
                "shadow_scorer_action": queue_row.get("shadow_scorer_action"),
                "shadow_scorer_score": queue_row.get("shadow_scorer_score"),
                "source_acquisition_status": replay.get("source_acquisition_status"),
                "source_proxy_replay_result": replay.get("source_proxy_replay_result"),
                "source_replay_priority_score": replay.get("source_replay_priority_score"),
                "source_rows_needed_to_n20_original": queue_row.get("source_rows_needed_to_n20"),
                "source_acquisition_proxy_r_style_midpoint": replay.get("source_acquisition_proxy_r_style_midpoint"),
                "source_acquisition_proxy_r_style_result_class": replay.get(
                    "source_acquisition_proxy_r_style_result_class"
                ),
                "market_gap_source_action_class": market.get("action_class"),
                "market_gap_movement_status": market.get("movement_status"),
                "market_gap_delta_alignment_rate": market.get("delta_alignment_rate"),
                "market_gap_delta_mean_abs_future_change": market.get("delta_mean_abs_future_change"),
                "materialization_surface": MATERIALIZATION_SURFACE,
                **metrics,
                **proxy,
                "materialization_exact_missing_reason": exact_missing_reason(metrics),
            },
            generated_at,
            manifest_hash,
        )
        materialized.append(row)
        gap_rows.append(
            with_common(
                {
                    "source_materialization_gap_id": f"OHLC-GTOS-UNIFIED-SRCMAT-GAP-{index:05d}",
                    "source_materialization_execution_id": row["source_materialization_execution_id"],
                    "symbol": row["symbol"],
                    "route_session": row["route_session"],
                    "session_bucket": row["session_bucket"],
                    "horizon_id": row["horizon_id"],
                    "primitive_flag": row["primitive_flag"],
                    "source_rows_needed_to_n20_original": row["source_rows_needed_to_n20_original"],
                    "current_targetable_flagged_n": row["current_targetable_flagged_n"],
                    "current_source_flagged_n": row["current_source_flagged_n"],
                    "current_failclosed_flagged_n": row["current_failclosed_flagged_n"],
                    "current_exact_gap_to_n20": row["current_exact_gap_to_n20"],
                    "same_symbol_all_sessions_targetable_flagged_n": row[
                        "same_symbol_all_sessions_targetable_flagged_n"
                    ],
                    "same_symbol_all_sessions_source_flagged_n": row["same_symbol_all_sessions_source_flagged_n"],
                    "same_session_all_symbols_targetable_flagged_n": row[
                        "same_session_all_symbols_targetable_flagged_n"
                    ],
                    "all_market_primitive_targetable_flagged_n": row["all_market_primitive_targetable_flagged_n"],
                    "source_materialization_execution_status": row["source_materialization_execution_status"],
                    "source_materialization_decision": row["source_materialization_decision"],
                    "materialization_proxy_scope": row["materialization_proxy_scope"],
                    "materialization_proxy_r_style_result_class": row["materialization_proxy_r_style_result_class"],
                    "materialization_exact_missing_reason": row["materialization_exact_missing_reason"],
                },
                generated_at,
                manifest_hash,
            )
        )
    return materialized, gap_rows


def build_family_proxy_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[
            (
                str(row.get("materialization_proxy_scope")),
                str(row.get("symbol")),
                str(row.get("route_session")),
                str(row.get("primitive_flag")),
            )
        ].append(row)
    output: list[dict[str, Any]] = []
    for index, ((scope, symbol, route_session, primitive), members) in enumerate(sorted(groups.items()), 1):
        scores = [float(row.get("materialization_proxy_score") or 0.0) for row in members]
        output.append(
            with_common(
                {
                    "family_proxy_id": f"OHLC-GTOS-UNIFIED-SRCMAT-FAMILY-{index:05d}",
                    "materialization_proxy_scope": scope,
                    "symbol": symbol,
                    "route_session": route_session,
                    "primitive_flag": primitive,
                    "row_count": len(members),
                    "horizon_ids": sorted({str(row.get("horizon_id")) for row in members}),
                    "source_materialization_status_counts": compact_counter(
                        members, "source_materialization_execution_status"
                    ),
                    "materialization_decision_counts": compact_counter(members, "source_materialization_decision"),
                    "max_current_targetable_flagged_n": max(
                        int(row.get("current_targetable_flagged_n") or 0) for row in members
                    ),
                    "max_current_source_flagged_n": max(
                        int(row.get("current_source_flagged_n") or 0) for row in members
                    ),
                    "max_same_symbol_all_sessions_targetable_flagged_n": max(
                        int(row.get("same_symbol_all_sessions_targetable_flagged_n") or 0) for row in members
                    ),
                    "max_same_symbol_all_sessions_source_flagged_n": max(
                        int(row.get("same_symbol_all_sessions_source_flagged_n") or 0) for row in members
                    ),
                    "mean_materialization_proxy_score": mean_or_none(scores),
                    "positive_proxy_interval_rows": sum(
                        1
                        for row in members
                        if row.get("materialization_proxy_r_style_result_class") == "PROXY_R_INTERVAL_ALL_POSITIVE"
                    ),
                    "straddles_zero_proxy_interval_rows": sum(
                        1
                        for row in members
                        if row.get("materialization_proxy_r_style_result_class") == "PROXY_R_INTERVAL_STRADDLES_ZERO"
                    ),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_symbol_session_horizon_rows(
    rows: list[dict[str, Any]], generated_at: str, manifest_hash: str
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row.get("symbol")), str(row.get("route_session")), str(row.get("horizon_id")))].append(row)
    output: list[dict[str, Any]] = []
    for index, ((symbol, route_session, horizon), members) in enumerate(sorted(groups.items()), 1):
        output.append(
            with_common(
                {
                    "symbol_session_horizon_materialization_id": f"OHLC-GTOS-UNIFIED-SRCMAT-SSH-{index:04d}",
                    "symbol": symbol,
                    "route_session": route_session,
                    "horizon_id": horizon,
                    "row_count": len(members),
                    "outside_branch_rows": sum(1 for row in members if row.get("outside_gbpjpy_xauusd_current_branch_box")),
                    "current_targetable_n20_rows": sum(
                        1 for row in members if int(row.get("current_targetable_flagged_n") or 0) >= 20
                    ),
                    "current_source_n20_rows": sum(
                        1 for row in members if int(row.get("current_source_flagged_n") or 0) >= 20
                    ),
                    "current_source_under20_rows": sum(
                        1 for row in members if int(row.get("current_source_flagged_n") or 0) < 20
                    ),
                    "target_horizon_failclosed_guard_rows": sum(
                        1
                        for row in members
                        if row.get("source_materialization_execution_status")
                        == "SOURCE_MATERIALIZATION_CURRENT_SOURCE_N20_HORIZON_FAILCLOSED"
                    ),
                    "materialization_status_counts": compact_counter(
                        members, "source_materialization_execution_status"
                    ),
                    "decision_counts": compact_counter(members, "source_materialization_decision"),
                    "max_materialization_proxy_score": max(
                        float(row.get("materialization_proxy_score") or 0.0) for row in members
                    ),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_bucket_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    distributions = {
        "source_materialization_execution_status": compact_counter(rows, "source_materialization_execution_status"),
        "source_materialization_decision": compact_counter(rows, "source_materialization_decision"),
        "materialization_proxy_scope": compact_counter(rows, "materialization_proxy_scope"),
        "current_targetability_class": compact_counter(rows, "current_targetability_class"),
        "materialization_proxy_r_style_result_class": compact_counter(rows, "materialization_proxy_r_style_result_class"),
        "symbol": compact_counter(rows, "symbol"),
        "route_session": compact_counter(rows, "route_session"),
        "outside_gbpjpy_xauusd_current_branch_box": compact_counter(
            rows, "outside_gbpjpy_xauusd_current_branch_box"
        ),
    }
    bucket_rows: list[dict[str, Any]] = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            bucket_rows.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-UNIFIED-SRCMAT-BUCKET-{len(bucket_rows) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    return bucket_rows, distributions


def append_manifest(paths: list[Path], result: dict[str, Any]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    generated = manifest.setdefault("generated_artifacts", [])
    existing = {row.get("path") for row in generated if isinstance(row, dict)}
    for path in paths:
        rel = path.relative_to(REPO).as_posix()
        if rel not in existing:
            generated.append({"path": rel, "artifact": PREFIX, "sha256": sha256_file(path), "safe_flags": SAFE_FLAGS, "not_completion": True})
    manifest["latest_unified_source_materialization_execution"] = {
        "artifact": PREFIX,
        "counts": result["counts"],
        "generated_utc": result["generated_utc"],
        "source_manifest_hash": result["source_manifest_hash"],
    }
    write_text(OUTPUT_MANIFEST, json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def append_sprint_ledger(result: dict[str, Any]) -> None:
    row = {
        "timestamp_utc": result["generated_utc"],
        "route": PREFIX,
        "event": "unified_source_materialization_execution_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Executed source materialization/proxy reconstruction for all 309 unified source queue rows.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_paths = [
        SHADOW_RESULT,
        SOURCE_QUEUE,
        REPLAY_SOURCE,
        MARKET_SOURCE,
        TICK_EVENT,
        TICK_FAIL,
        TICK_PRIMITIVE_SUMMARY,
        TICK_FLAG_CONTROL,
        TICK_CROSS_BASE,
        TICK_CROSS_HORIZON,
        TICK_CROSS_SESSION,
        TICK_FULL_PERM,
        HELPER_MODULE,
    ]
    source_manifest, manifest_hash = source_manifest_rows(source_paths, generated_at)

    shadow_result = read_json(SHADOW_RESULT)
    source_queue_rows = read_jsonl(SOURCE_QUEUE)
    replay_source_rows = read_jsonl(REPLAY_SOURCE)
    market_source_rows = read_jsonl(MARKET_SOURCE)
    event_rows = read_jsonl(TICK_EVENT)
    fail_rows = read_jsonl(TICK_FAIL)
    primitive_rows = read_jsonl(TICK_PRIMITIVE_SUMMARY)
    flag_control_rows = read_jsonl(TICK_FLAG_CONTROL)
    base_rows = read_jsonl(TICK_CROSS_BASE)
    cross_horizon_rows = read_jsonl(TICK_CROSS_HORIZON)
    cross_session_rows = read_jsonl(TICK_CROSS_SESSION)
    full_perm_rows = read_jsonl(TICK_FULL_PERM)

    indexes = build_indexes(
        event_rows,
        fail_rows,
        primitive_rows,
        base_rows,
        flag_control_rows,
        cross_horizon_rows,
        cross_session_rows,
        full_perm_rows,
    )
    materialization_rows, gap_rows = build_materialization_rows(
        source_queue_rows,
        replay_source_rows,
        market_source_rows,
        indexes,
        generated_at,
        manifest_hash,
    )
    family_proxy_rows = build_family_proxy_rows(materialization_rows, generated_at, manifest_hash)
    ssh_rows = build_symbol_session_horizon_rows(materialization_rows, generated_at, manifest_hash)
    bucket_rows, distributions = build_bucket_rows(materialization_rows, generated_at, manifest_hash)
    question_rows = [
        with_common(
            {
                "question_id": "OHLC-GTOS-UNIFIED-SRCMAT-Q-001",
                "question": "Did the source pass materialize every source queue row rather than sampling rows?",
                "answer_route": "Yes: every 309 source-materialization queue row is emitted into materialization and gap-closure ledgers.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-UNIFIED-SRCMAT-Q-002",
                "question": "Which rows had current source flags already at N20 but not enough targetable horizon outcomes?",
                "answer_route": "Rows with SOURCE_MATERIALIZATION_CURRENT_SOURCE_N20_HORIZON_FAILCLOSED preserve exact current source flags and fail-closed horizon reasons.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-UNIFIED-SRCMAT-Q-003",
                "question": "How are current under-N20 rows scored without dropping outside markets?",
                "answer_route": "The packet computes same-symbol/all-session, same-session/all-symbol, symbol-session all-primitive, and all-market primitive targetable/source proxies for every row.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-UNIFIED-SRCMAT-Q-004",
                "question": "Does this alter implementation decisions?",
                "answer_route": "Yes: source rows now split into exact current targetability, current-source fail-closed guards, expanded-session targetable proxies, broader transfer proxies, or preserved source requirements.",
            },
            generated_at,
            manifest_hash,
        ),
    ]

    counts = {
        "input_source_materialization_queue_rows": len(source_queue_rows),
        "input_replay_source_acquisition_rows": len(replay_source_rows),
        "input_market_source_queue_rows": len(market_source_rows),
        "input_tick_event_rows": len(event_rows),
        "input_tick_fail_closed_rows": len(fail_rows),
        "input_primitive_summary_rows": len(primitive_rows),
        "materialization_execution_rows": len(materialization_rows),
        "gap_closure_rows": len(gap_rows),
        "family_proxy_rows": len(family_proxy_rows),
        "symbol_session_horizon_rows": len(ssh_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "current_targetable_n20_rows": sum(
            1 for row in materialization_rows if int(row.get("current_targetable_flagged_n") or 0) >= 20
        ),
        "current_source_flags_n20_rows": sum(
            1 for row in materialization_rows if int(row.get("current_source_flagged_n") or 0) >= 20
        ),
        "current_source_under20_rows": sum(
            1 for row in materialization_rows if int(row.get("current_source_flagged_n") or 0) < 20
        ),
        "target_horizon_failclosed_guard_rows": sum(
            1
            for row in materialization_rows
            if row.get("source_materialization_execution_status")
            == "SOURCE_MATERIALIZATION_CURRENT_SOURCE_N20_HORIZON_FAILCLOSED"
        ),
        "expanded_targetable_proxy_n20_rows": sum(
            1
            for row in materialization_rows
            if "TARGETABLE_PROXY_N20" in str(row.get("source_materialization_execution_status"))
        ),
        "expanded_source_proxy_n20_rows": sum(
            1
            for row in materialization_rows
            if row.get("source_materialization_execution_status")
            in {
                "SOURCE_MATERIALIZATION_SAME_SYMBOL_ALL_SESSION_PROXY_N20",
                "SOURCE_MATERIALIZATION_SAME_SESSION_ALL_SYMBOL_PROXY_N20",
                "SOURCE_MATERIALIZATION_SAME_SYMBOL_SESSION_ALL_PRIMITIVES_PROXY_N20",
                "SOURCE_MATERIALIZATION_ALL_MARKET_PRIMITIVE_PROXY_N20",
            }
        ),
        "outside_branch_materialization_rows": sum(
            1 for row in materialization_rows if row.get("outside_gbpjpy_xauusd_current_branch_box")
        ),
        "original_source_rows_needed_to_n20_total": sum(
            int(row.get("source_rows_needed_to_n20") or 0) for row in source_queue_rows
        ),
        "current_exact_targetable_gap_to_n20_total": sum(
            int(row.get("current_exact_gap_to_n20") or 0) for row in materialization_rows
        ),
    }
    system_decision = {
        "source_materialization_execution_status_counts": distributions[
            "source_materialization_execution_status"
        ],
        "source_materialization_decision_counts": distributions["source_materialization_decision"],
        "materialization_proxy_scope_counts": distributions["materialization_proxy_scope"],
        "system_recommendation": (
            "UNIFIED_SOURCE_MATERIALIZATION_EXECUTION_RESULT: the 309 source rows are now split by exact "
            "targetability, current source flags with fail-closed horizon guards, expanded targetable proxies, "
            "or source-proxy guards; branch-local implementation should use these guards before enabling source "
            "materialization candidates and must keep outside-market rows in scope."
        ),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "counts": counts,
        "upstream_counts": {"unified_shadow_scorer_execution": shadow_result.get("counts", {})},
        "bucket_distributions": distributions,
        "system_decision": system_decision,
    }

    generated_files = [
        MATERIALIZATION_LEDGER,
        GAP_CLOSURE_LEDGER,
        FAMILY_PROXY_LEDGER,
        SYMBOL_SESSION_HORIZON_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
    ]
    write_jsonl(MATERIALIZATION_LEDGER, materialization_rows)
    write_jsonl(GAP_CLOSURE_LEDGER, gap_rows)
    write_jsonl(FAMILY_PROXY_LEDGER, family_proxy_rows)
    write_jsonl(SYMBOL_SESSION_HORIZON_LEDGER, ssh_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Branch System Transfer Unified Source Materialization Execution",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Source materialization rows: `{counts['materialization_execution_rows']}`",
                f"- Current source flags N20 rows: `{counts['current_source_flags_n20_rows']}`",
                f"- Target horizon fail-closed guard rows: `{counts['target_horizon_failclosed_guard_rows']}`",
                f"- Expanded targetable proxy N20 rows: `{counts['expanded_targetable_proxy_n20_rows']}`",
                f"- Outside-branch materialization rows: `{counts['outside_branch_materialization_rows']}`",
                "",
                "Core result: source rows now carry exact targetable/source/fail-closed/proxy closure causes and decision guards.",
                "",
            ]
        ),
    )
    append_manifest([RESULT_PATH, SUMMARY_PATH, *generated_files], result)
    append_sprint_ledger(result)
    print(json.dumps({"ok": True, "counts": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
