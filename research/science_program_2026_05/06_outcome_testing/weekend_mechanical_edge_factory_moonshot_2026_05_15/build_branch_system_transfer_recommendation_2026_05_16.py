#!/usr/bin/env python3
"""Join executable family details into branch/system transfer recommendations."""

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

ACCEPTED_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_RESULT_2026-05-16.json"
ACCEPTED_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_BRANCH_LEDGER_2026-05-16.jsonl"
NEXT_LAYER_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_RESULT_2026-05-16.json"
NEXT_LAYER_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_BRANCH_LEDGER_2026-05-16.jsonl"
SOURCE_IMPLICATION_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_UPGRADED_DEGRADED_IMPLICATION_RESULT_2026-05-16.json"
SOURCE_IMPLICATION_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_UPGRADED_DEGRADED_IMPLICATION_BRANCH_LEDGER_2026-05-16.jsonl"
M15_DETAIL_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_BOUNDED_ORDERING_DETAIL_RESULT_2026-05-16.json"
M15_SCOPE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_BOUNDED_ORDERING_DETAIL_SCOPE_LEDGER_2026-05-16.jsonl"
M15_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_BOUNDED_ORDERING_DETAIL_BRANCH_DETAIL_LEDGER_2026-05-16.jsonl"
M1_DETAIL_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_SUPPORT_CONFLICT_DETAIL_RESULT_2026-05-16.json"
M1_SCOPE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_SUPPORT_CONFLICT_DETAIL_SCOPE_LEDGER_2026-05-16.jsonl"
M1_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_SUPPORT_CONFLICT_DETAIL_BRANCH_DETAIL_LEDGER_2026-05-16.jsonl"
POSITIVE_DETAIL_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_POSITIVE_CHALLENGER_DETAIL_RESULT_2026-05-16.json"
POSITIVE_SCOPE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_POSITIVE_CHALLENGER_DETAIL_SCOPE_LEDGER_2026-05-16.jsonl"
POSITIVE_ACCEPTED = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_POSITIVE_CHALLENGER_DETAIL_ACCEPTED_DETAIL_LEDGER_2026-05-16.jsonl"
ENTRY_ADVERSE_DETAIL_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_ADVERSE_REDESIGN_DETAIL_RESULT_2026-05-16.json"
ENTRY_ADVERSE_SCOPE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_ADVERSE_REDESIGN_DETAIL_SCOPE_LEDGER_2026-05-16.jsonl"
ENTRY_ADVERSE_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_ADVERSE_REDESIGN_DETAIL_BRANCH_DETAIL_LEDGER_2026-05-16.jsonl"
ENTRY_ADVERSE_REJECTED = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_ADVERSE_REDESIGN_DETAIL_REJECTED_REPAIR_LEDGER_2026-05-16.jsonl"

PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_RECOMMENDATION"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-16.json"
BRANCH_LEDGER = ROUTE_DIR / f"{PREFIX}_BRANCH_LEDGER_2026-05-16.jsonl"
KEEP_KILL_REDESIGN_LEDGER = ROUTE_DIR / f"{PREFIX}_KEEP_KILL_REDESIGN_LEDGER_2026-05-16.jsonl"
MARKET_SESSION_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_SESSION_DECISION_LEDGER_2026-05-16.jsonl"
TRANSFER_MATRIX_LEDGER = ROUTE_DIR / f"{PREFIX}_TRANSFER_MATRIX_LEDGER_2026-05-16.jsonl"
FAMILY_RECOMMENDATION_LEDGER = ROUTE_DIR / f"{PREFIX}_FAMILY_RECOMMENDATION_LEDGER_2026-05-16.jsonl"
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
    "Branch system-transfer recommendation packet only. It joins branch-local SOURCE/M15/M1/"
    "POSITIVE/ENTRY_ADVERSE detail packets over the full 386-branch denominator, computes "
    "keep/kill/redesign/repair and transfer classifications by symbol/session/primitive, and "
    "keeps market-specific concentration explicit. It does not change live behavior and does "
    "not claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-SYSTEM-TRANSFER-SRC-{index:04d}",
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


def by_branch(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["branch_queue_id"]: row for row in rows if row.get("branch_queue_id")}


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def route_descriptor(route_candidate_id: str | None) -> str:
    parts = str(route_candidate_id or "").split("|")
    return parts[2] if len(parts) >= 3 else "UNKNOWN_DESCRIPTOR"


def primitive_family(descriptor: str) -> str:
    if descriptor.startswith("SWEEP_") and "CLOSE_BACK_INSIDE" in descriptor:
        return "SWEEP_CLOSE_BACK_INSIDE"
    if "WICK_EXHAUSTION" in descriptor:
        return "WICK_EXHAUSTION"
    if "BREAK" in descriptor:
        return "BREAKOUT_OR_STRUCTURE_BREAK"
    return descriptor or "UNKNOWN_PRIMITIVE"


def source_decision(row: dict[str, Any]) -> tuple[str, str, str]:
    implication = str(row.get("source_implication_class") or "")
    if "ACCEPTED_CONFIRMED" in implication:
        return (
            "KEEP_CHALLENGER",
            "SOURCE_KEEP_BAR_PROXY_CONFIRMED",
            "PRESERVE_SOURCE_ACCEPTED_CHALLENGER_CANDIDATE",
        )
    if "ACCEPTED_DEGRADED" in implication:
        return (
            "KILL_OR_REDESIGN",
            "SOURCE_KILL_ACCEPTED_UNTIL_EXACT_SOURCE_OR_M15_REPAIR",
            "DOWNGRADE_ACCEPTED_SOURCE_OR_ROUTE_TO_M15_ORDERING_REPAIR",
        )
    if "REPAIR_UPGRADED" in implication:
        return (
            "REPAIR_THEN_REVIEW_CHALLENGER",
            "SOURCE_REOPEN_REPAIR_AS_CHALLENGER_REVIEW",
            "REVIEW_SOURCE_REPAIR_UPGRADE_AFTER_M15_ORDERING_WHERE_REQUIRED",
        )
    if "REPAIR_CONFIRMED" in implication or "REPAIR_SUPPORTED" in implication:
        return (
            "KEEP_REPAIR_OR_AVOID",
            "SOURCE_KEEP_REPAIR_OR_AVOID_DECISION",
            "KEEP_SOURCE_REPAIR_OR_AVOID_DECISION",
        )
    if "NO_SCALAR" in implication:
        return (
            "PRESERVE_REQUIREMENT",
            "SOURCE_PRESERVE_NO_SCALAR_REQUIREMENT",
            "PRESERVE_SOURCE_REQUIREMENT_NO_SCALAR_DECISION",
        )
    return ("PRESERVE_CONTEXT", "SOURCE_CONTEXT_NOT_PRIMARY_DETAIL", "PRESERVE_SOURCE_CONTEXT")


def m15_decision(scope: dict[str, Any], detail: dict[str, Any]) -> tuple[str, str, str]:
    status = str(scope.get("m15_builder_result_status") or detail.get("m15_detail_status") or "")
    if "TARGET_FIRST_ACCEPTED" in status or "TARGET_FIRST_CONSERVATIVE" in status:
        return ("KEEP_CHALLENGER", "M15_KEEP_TARGET_FIRST_CONSERVATIVE_BOUND", "PRESERVE_M15_TARGET_FIRST_CHALLENGER")
    if "BOUNDS_SPLIT_ACCEPTED" in status or "BOUNDS_SPLIT_POSITIVE" in status:
        return ("REPAIR_THEN_REVIEW_CHALLENGER", "M15_KEEP_BOUNDS_SPLIT_WITH_ORDERING_REPAIR", "PRESERVE_M15_BOUNDS_SPLIT_CHALLENGER_WITH_ORDERING_LIMIT")
    if "REJECTED" in status:
        return ("KILL_OR_REDESIGN", "M15_KILL_OR_REDESIGN_STOP_FIRST_NONPOSITIVE_BOUND", "USE_M15_AS_AVOID_OR_REDESIGN_SIGNAL")
    if "SIDE_CAR" in status:
        return ("PRESERVE_CONTEXT", "M15_PRESERVE_SIDECAR_CONTEXT", "PRESERVE_M15_CONTEXT")
    return ("PRESERVE_CONTEXT", "M15_CONTEXT_NOT_PRIMARY_DETAIL", "PRESERVE_M15_CONTEXT")


def m1_decision(scope: dict[str, Any], detail: dict[str, Any]) -> tuple[str, str, str]:
    status = str(scope.get("m1_builder_result_status") or detail.get("support_detail_status") or "")
    if "STABLE_ACCEPTED" in status or status == "M1_SUPPORT_STABLE":
        return ("KEEP_CHALLENGER", "M1_KEEP_SUPPORT_STABLE_CHALLENGER", "PRESERVE_STABLE_M1_SUPPORT_CHALLENGER")
    if "CONFLICT_SPLIT_ACCEPTED" in status or "CONFLICT" in status:
        return ("SPLIT_REDESIGN", "M1_SPLIT_SUPPORT_POSITIVE_FROM_BRANCH_CONFLICT", "SPLIT_M1_SUPPORT_FROM_BRANCH_AGGREGATE_CONFLICT")
    if "SIDE_CAR" in status:
        return ("PRESERVE_CONTEXT", "M1_PRESERVE_SIDECAR_CONTEXT", "PRESERVE_M1_SUPPORT_CONTEXT")
    return ("PRESERVE_CONTEXT", "M1_CONTEXT_NOT_PRIMARY_DETAIL", "PRESERVE_M1_CONTEXT")


def positive_decision(scope: dict[str, Any], detail: dict[str, Any]) -> tuple[str, str, str]:
    status = str(scope.get("positive_builder_result_status") or detail.get("positive_detail_status") or "")
    if "REPLAY_ACCEPTED" in status or "POSITIVE_ACCEPTED" in status:
        return ("KEEP_CHALLENGER", "POSITIVE_KEEP_M1_SPREAD_PROXY_CHALLENGER_WITH_MODIFIERS", "PRESERVE_POSITIVE_REPLAY_CHALLENGER_WITH_MODIFIERS")
    if "REPAIR" in status or "STRESS" in status:
        return ("REPAIR_THEN_REVIEW_CHALLENGER", "POSITIVE_REPAIR_STRESS_FIRST_BEFORE_KEEP", "REPAIR_POSITIVE_SOURCE_OR_STRESS_FIRST")
    if "REJECTED" in status:
        return ("KILL_OR_REDESIGN", "POSITIVE_KILL_NONPOSITIVE_OR_CONTROL_EXPLAINED", "KILL_OR_REDESIGN_POSITIVE_NONPOSITIVE_BRANCH")
    if "SIDE_CAR" in status:
        return ("PRESERVE_CONTEXT", "POSITIVE_PRESERVE_SIDECAR_CONTEXT", "PRESERVE_POSITIVE_CONTEXT")
    return ("PRESERVE_CONTEXT", "POSITIVE_CONTEXT_NOT_PRIMARY_DETAIL", "PRESERVE_POSITIVE_CONTEXT")


def entry_adverse_decision(scope: dict[str, Any], detail: dict[str, Any], rejected: dict[str, Any]) -> tuple[str, str, str]:
    status = str(scope.get("entry_adverse_builder_result_status") or detail.get("entry_adverse_builder_result_status") or rejected.get("entry_adverse_builder_result_status") or "")
    if status == "ENTRY_AND_ADVERSE_REDESIGN_ACCEPTED":
        return (
            "KILL_OR_REDESIGN",
            "ENTRY_ADVERSE_USE_AS_AVOID_OR_ENTRY_REDESIGN_NOT_DIRECT_TRADE",
            "TEST_STOP_FIRST_AVOID_FILTER_AND_ENTRY_REDESIGN_VARIANTS",
        )
    if status == "ENTRY_ADVERSE_REJECTED_NONPOSITIVE":
        return (
            "KEEP_REPAIR_OR_AVOID",
            "ENTRY_ADVERSE_REJECTED_NONPOSITIVE_PRESERVE_REPAIR_ROW",
            "PRESERVE_REJECTED_ENTRY_ADVERSE_REPAIR_ROW",
        )
    if status == "ENTRY_ADVERSE_SIDE_CAR_REDESIGN_CONTEXT":
        return ("PRESERVE_CONTEXT", "ENTRY_ADVERSE_PRESERVE_SIDECAR_CONTEXT", "PRESERVE_ENTRY_ADVERSE_CONTEXT")
    if status == "ENTRY_ADVERSE_CONTEXT_PRESERVED":
        return ("PRESERVE_CONTEXT", "ENTRY_ADVERSE_PRESERVE_NON_REDESIGN_CONTEXT", "PRESERVE_ENTRY_ADVERSE_CONTEXT")
    return ("PRESERVE_CONTEXT", "ENTRY_ADVERSE_CONTEXT_NOT_PRIMARY_DETAIL", "PRESERVE_ENTRY_ADVERSE_CONTEXT")


def binding_decision(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        "PRESERVE_REQUIREMENT",
        "BINDING_PRESERVE_TARGETSTOP_NA_NO_SCALAR_PROVENANCE",
        row.get("branch_system_recommendation") or "PRESERVE_BINDING_NO_SCALAR_PROVENANCE",
    )


def classify_branch_decision(
    accepted: dict[str, Any],
    source_row: dict[str, Any],
    m15_scope: dict[str, Any],
    m15_detail: dict[str, Any],
    m1_scope: dict[str, Any],
    m1_detail: dict[str, Any],
    positive_scope: dict[str, Any],
    positive_detail: dict[str, Any],
    entry_scope: dict[str, Any],
    entry_detail: dict[str, Any],
    entry_rejected: dict[str, Any],
) -> tuple[str, str, str]:
    family = accepted.get("primary_export_family")
    if family == "SOURCE":
        return source_decision(source_row)
    if family == "M15":
        return m15_decision(m15_scope, m15_detail)
    if family == "M1":
        return m1_decision(m1_scope, m1_detail)
    if family == "POSITIVE":
        return positive_decision(positive_scope, positive_detail)
    if family == "ENTRY_ADVERSE":
        return entry_adverse_decision(entry_scope, entry_detail, entry_rejected)
    if family == "BINDING":
        return binding_decision(accepted)
    return ("PRESERVE_CONTEXT", "UNKNOWN_FAMILY_PRESERVE_CONTEXT", "PRESERVE_CONTEXT")


def transfer_class(rows: list[dict[str, Any]]) -> str:
    symbols = {row.get("symbol") for row in rows if row.get("symbol")}
    sessions = {row.get("route_session") for row in rows if row.get("route_session")}
    sides = {row.get("side") for row in rows if row.get("side")}
    total = len(rows)
    pair_counts = Counter((row.get("symbol"), row.get("route_session")) for row in rows)
    dominant_share = max(pair_counts.values()) / total if total and pair_counts else 0.0
    if len(symbols) >= 2 and len(sessions) >= 2:
        base = "CURRENT_DENOMINATOR_MULTI_SYMBOL_MULTI_SESSION"
    elif len(symbols) >= 2:
        base = "CURRENT_DENOMINATOR_MULTI_SYMBOL_SINGLE_SESSION"
    elif len(sessions) >= 2:
        base = "CURRENT_DENOMINATOR_SINGLE_SYMBOL_MULTI_SESSION"
    else:
        base = "MARKET_SPECIFIC_SINGLE_SYMBOL_SESSION"
    if len(sides) >= 2:
        base += "_BOTH_SIDES"
    if dominant_share >= 0.80:
        base += "_CONCENTRATED"
    return base


def stat_values(rows: list[dict[str, Any]], key: str, prefix: str) -> dict[str, float | None]:
    values: list[float] = []
    for row in rows:
        value = row.get(key)
        if value is None:
            continue
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            continue
    if not values:
        return {f"{prefix}_min": None, f"{prefix}_mean": None, f"{prefix}_max": None}
    return {f"{prefix}_min": round(min(values), 6), f"{prefix}_mean": round(mean(values), 6), f"{prefix}_max": round(max(values), 6)}


def main() -> int:
    generated_at = now_utc()
    accepted_result = read_json(ACCEPTED_RESULT)
    next_layer_result = read_json(NEXT_LAYER_RESULT)
    source_result = read_json(SOURCE_IMPLICATION_RESULT)
    m15_result = read_json(M15_DETAIL_RESULT)
    m1_result = read_json(M1_DETAIL_RESULT)
    positive_result = read_json(POSITIVE_DETAIL_RESULT)
    entry_result = read_json(ENTRY_ADVERSE_DETAIL_RESULT)

    accepted_rows = read_jsonl(ACCEPTED_BRANCH)
    next_rows = read_jsonl(NEXT_LAYER_BRANCH)
    source_rows = read_jsonl(SOURCE_IMPLICATION_BRANCH)
    m15_scope_rows = read_jsonl(M15_SCOPE)
    m15_detail_rows = read_jsonl(M15_BRANCH)
    m1_scope_rows = read_jsonl(M1_SCOPE)
    m1_detail_rows = read_jsonl(M1_BRANCH)
    positive_scope_rows = read_jsonl(POSITIVE_SCOPE)
    positive_detail_rows = read_jsonl(POSITIVE_ACCEPTED)
    entry_scope_rows = read_jsonl(ENTRY_ADVERSE_SCOPE)
    entry_detail_rows = read_jsonl(ENTRY_ADVERSE_BRANCH)
    entry_rejected_rows = read_jsonl(ENTRY_ADVERSE_REJECTED)

    next_by_id = by_branch(next_rows)
    source_by_id = by_branch(source_rows)
    m15_scope_by_id = by_branch(m15_scope_rows)
    m15_detail_by_id = by_branch(m15_detail_rows)
    m1_scope_by_id = by_branch(m1_scope_rows)
    m1_detail_by_id = by_branch(m1_detail_rows)
    positive_scope_by_id = by_branch(positive_scope_rows)
    positive_detail_by_id = by_branch(positive_detail_rows)
    entry_scope_by_id = by_branch(entry_scope_rows)
    entry_detail_by_id = by_branch(entry_detail_rows)
    entry_rejected_by_id = by_branch(entry_rejected_rows)

    source_manifest, manifest_hash = source_manifest_rows(
        [
            ACCEPTED_RESULT,
            ACCEPTED_BRANCH,
            NEXT_LAYER_RESULT,
            NEXT_LAYER_BRANCH,
            SOURCE_IMPLICATION_RESULT,
            SOURCE_IMPLICATION_BRANCH,
            M15_DETAIL_RESULT,
            M15_SCOPE,
            M15_BRANCH,
            M1_DETAIL_RESULT,
            M1_SCOPE,
            M1_BRANCH,
            POSITIVE_DETAIL_RESULT,
            POSITIVE_SCOPE,
            POSITIVE_ACCEPTED,
            ENTRY_ADVERSE_DETAIL_RESULT,
            ENTRY_ADVERSE_SCOPE,
            ENTRY_ADVERSE_BRANCH,
            ENTRY_ADVERSE_REJECTED,
        ],
        generated_at,
    )

    branch_rows: list[dict[str, Any]] = []
    for accepted in accepted_rows:
        branch_id = accepted.get("branch_queue_id")
        source_row = source_by_id.get(branch_id, {})
        m15_scope = m15_scope_by_id.get(branch_id, {})
        m15_detail = m15_detail_by_id.get(branch_id, {})
        m1_scope = m1_scope_by_id.get(branch_id, {})
        m1_detail = m1_detail_by_id.get(branch_id, {})
        positive_scope = positive_scope_by_id.get(branch_id, {})
        positive_detail = positive_detail_by_id.get(branch_id, {})
        entry_scope = entry_scope_by_id.get(branch_id, {})
        entry_detail = entry_detail_by_id.get(branch_id, {})
        entry_rejected = entry_rejected_by_id.get(branch_id, {})
        next_row = next_by_id.get(branch_id, {})
        descriptor = route_descriptor(accepted.get("route_candidate_id"))
        primitive = primitive_family(descriptor)
        decision_direction, system_decision_class, next_action = classify_branch_decision(
            accepted,
            source_row,
            m15_scope,
            m15_detail,
            m1_scope,
            m1_detail,
            positive_scope,
            positive_detail,
            entry_scope,
            entry_detail,
            entry_rejected,
        )
        branch_rows.append(
            with_common(
                {
                    "system_transfer_branch_id": f"OHLC-GTOS-SYSTEM-TRANSFER-BRANCH-{len(branch_rows) + 1:05d}",
                    "branch_queue_id": branch_id,
                    "matrix_branch_id": accepted.get("matrix_branch_id"),
                    "route_candidate_id": accepted.get("route_candidate_id"),
                    "route_descriptor": descriptor,
                    "primitive_family": primitive,
                    "non_ob_primitive_scope": primitive not in {"OB_RETEST", "FVG_FILL", "BREAKER_RE_ENTRY"},
                    "sweep_or_wick_variant": descriptor if primitive in {"SWEEP_CLOSE_BACK_INSIDE", "WICK_EXHAUSTION"} else None,
                    "symbol": accepted.get("symbol"),
                    "route_session": accepted.get("route_session"),
                    "side": accepted.get("side"),
                    "entry_variant": accepted.get("entry_variant"),
                    "target_stop_contract_id": accepted.get("target_stop_contract_id"),
                    "target_stop_result": accepted.get("target_stop_result"),
                    "primary_export_family": accepted.get("primary_export_family"),
                    "branch_result_binary": accepted.get("branch_result_binary"),
                    "accepted_for_next_executable_builder": accepted.get("accepted_for_next_executable_builder"),
                    "accepted_branch_decision_class": accepted.get("branch_decision_class"),
                    "next_layer_branch_status": next_row.get("next_layer_branch_status"),
                    "next_layer_integrated_state": next_row.get("integrated_evidence_state"),
                    "source_implication_class": source_row.get("source_implication_class"),
                    "source_recompute_decision": source_row.get("bar_spread_recompute_decision"),
                    "source_bar_spread_sign_class": source_row.get("bar_spread_sign_class"),
                    "m15_scope_class": m15_scope.get("scope_class"),
                    "m15_builder_result_status": m15_scope.get("m15_builder_result_status") or m15_detail.get("m15_detail_status"),
                    "m15_interval_sign_class": m15_scope.get("interval_sign_class") or m15_detail.get("interval_sign_class"),
                    "m1_scope_class": m1_scope.get("scope_class"),
                    "m1_builder_result_status": m1_scope.get("m1_builder_result_status") or m1_detail.get("support_detail_status"),
                    "m1_support_interval_sign_class": m1_scope.get("m1_support_interval_sign_class") or m1_detail.get("m1_support_interval_sign_class"),
                    "positive_scope_class": positive_scope.get("scope_class"),
                    "positive_builder_result_status": positive_scope.get("positive_builder_result_status") or positive_detail.get("positive_detail_status"),
                    "positive_adjusted_midpoint": positive_scope.get("positive_adjusted_midpoint") or positive_detail.get("positive_adjusted_midpoint"),
                    "entry_adverse_scope_class": entry_scope.get("scope_class"),
                    "entry_adverse_builder_result_status": entry_scope.get("entry_adverse_builder_result_status") or entry_detail.get("entry_adverse_builder_result_status") or entry_rejected.get("entry_adverse_builder_result_status"),
                    "entry_adverse_stop_first_class": entry_detail.get("adverse_stop_first_class") or entry_rejected.get("adverse_stop_first_class"),
                    "fillability_rate": entry_detail.get("fillability_rate"),
                    "stop_first_rate": entry_detail.get("stop_first_rate"),
                    "decision_direction": decision_direction,
                    "system_decision_class": system_decision_class,
                    "next_same_resource_action": next_action,
                    "inverse_or_avoid_behavior": decision_direction in {"KILL_OR_REDESIGN", "KEEP_REPAIR_OR_AVOID"} or "AVOID" in system_decision_class,
                    "source_cost_behavior": bool(source_row or "SOURCE" in str(accepted.get("exact_failure_cause"))),
                    "path_behavior": accepted.get("target_stop_result"),
                    "m15_exact_chronology_claim": False,
                    "m1_exact_chronology_claim": False,
                    "m1_tick_ordering_exact": False,
                    "exact_success_cause": accepted.get("exact_success_cause"),
                    "exact_failure_cause": accepted.get("exact_failure_cause"),
                    "exact_missing_geometry_or_source_reason": accepted.get("exact_missing_geometry_or_source_reason"),
                },
                generated_at,
                manifest_hash,
            )
        )

    transfer_groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in branch_rows:
        key = (
            row.get("primary_export_family"),
            row.get("primitive_family"),
            row.get("system_decision_class"),
        )
        transfer_groups[key].append(row)
    transfer_lookup = {key: transfer_class(rows) for key, rows in transfer_groups.items()}
    for row in branch_rows:
        key = (row.get("primary_export_family"), row.get("primitive_family"), row.get("system_decision_class"))
        row["market_transfer_class"] = transfer_lookup[key]
        row["market_specific_concentration_flag"] = "CONCENTRATED" in row["market_transfer_class"] or row["market_transfer_class"].startswith("MARKET_SPECIFIC")

    keep_kill_rows = [
        with_common(
            {
                "keep_kill_redesign_id": f"OHLC-GTOS-SYSTEM-TRANSFER-KEEP-KILL-{index:05d}",
                "branch_queue_id": row.get("branch_queue_id"),
                "primary_export_family": row.get("primary_export_family"),
                "symbol": row.get("symbol"),
                "route_session": row.get("route_session"),
                "side": row.get("side"),
                "route_descriptor": row.get("route_descriptor"),
                "primitive_family": row.get("primitive_family"),
                "system_decision_class": row.get("system_decision_class"),
                "decision_direction": row.get("decision_direction"),
                "market_transfer_class": row.get("market_transfer_class"),
                "market_specific_concentration_flag": row.get("market_specific_concentration_flag"),
                "next_same_resource_action": row.get("next_same_resource_action"),
                "exact_success_cause": row.get("exact_success_cause"),
                "exact_failure_cause": row.get("exact_failure_cause"),
            },
            generated_at,
            manifest_hash,
        )
        for index, row in enumerate(branch_rows, 1)
    ]

    market_groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in branch_rows:
        market_groups[
            (
                row.get("primary_export_family"),
                row.get("symbol"),
                row.get("route_session"),
                row.get("side"),
                row.get("primitive_family"),
                row.get("system_decision_class"),
            )
        ].append(row)
    market_session_rows: list[dict[str, Any]] = []
    for key, rows in sorted(market_groups.items(), key=lambda item: tuple(str(part) for part in item[0])):
        family, symbol, session, side, primitive, decision = key
        market_session_rows.append(
            with_common(
                {
                    "market_session_decision_id": f"OHLC-GTOS-SYSTEM-TRANSFER-MARKET-SESSION-{len(market_session_rows) + 1:05d}",
                    "primary_export_family": family,
                    "symbol": symbol,
                    "route_session": session,
                    "side": side,
                    "primitive_family": primitive,
                    "system_decision_class": decision,
                    "branch_count": len(rows),
                    "accepted_count": sum(1 for row in rows if row.get("branch_result_binary") == "ACCEPTED"),
                    "rejected_count": sum(1 for row in rows if row.get("branch_result_binary") == "REJECTED"),
                    "decision_direction_counts": compact_counter(Counter(row.get("decision_direction") for row in rows)),
                    "target_stop_result_counts": compact_counter(Counter(row.get("target_stop_result") for row in rows)),
                    "entry_variant_counts": compact_counter(Counter(row.get("entry_variant") for row in rows)),
                    "branch_queue_ids": [row.get("branch_queue_id") for row in rows],
                    **stat_values(rows, "positive_adjusted_midpoint", "positive_adjusted_midpoint"),
                },
                generated_at,
                manifest_hash,
            )
        )

    transfer_matrix_rows: list[dict[str, Any]] = []
    for key, rows in sorted(transfer_groups.items(), key=lambda item: tuple(str(part) for part in item[0])):
        family, primitive, decision = key
        symbols = sorted({str(row.get("symbol")) for row in rows if row.get("symbol")})
        sessions = sorted({str(row.get("route_session")) for row in rows if row.get("route_session")})
        sides = sorted({str(row.get("side")) for row in rows if row.get("side")})
        transfer_matrix_rows.append(
            with_common(
                {
                    "transfer_matrix_id": f"OHLC-GTOS-SYSTEM-TRANSFER-MATRIX-{len(transfer_matrix_rows) + 1:05d}",
                    "primary_export_family": family,
                    "primitive_family": primitive,
                    "system_decision_class": decision,
                    "market_transfer_class": transfer_lookup[key],
                    "branch_count": len(rows),
                    "unique_symbol_count": len(symbols),
                    "unique_session_count": len(sessions),
                    "unique_side_count": len(sides),
                    "symbols": symbols,
                    "sessions": sessions,
                    "sides": sides,
                    "decision_direction_counts": compact_counter(Counter(row.get("decision_direction") for row in rows)),
                    "symbol_counts": compact_counter(Counter(row.get("symbol") for row in rows)),
                    "session_counts": compact_counter(Counter(row.get("route_session") for row in rows)),
                    "side_counts": compact_counter(Counter(row.get("side") for row in rows)),
                    "branch_queue_ids": [row.get("branch_queue_id") for row in rows],
                },
                generated_at,
                manifest_hash,
            )
        )

    family_groups: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for row in branch_rows:
        family_groups[row.get("primary_export_family")].append(row)
    family_recommendation_rows: list[dict[str, Any]] = []
    for family, rows in sorted(family_groups.items(), key=lambda item: str(item[0])):
        decision_counts = Counter(row.get("decision_direction") for row in rows)
        transfer_counts = Counter(row.get("market_transfer_class") for row in rows)
        if family == "SOURCE":
            family_recommendation = "SOURCE_ACCEPTED_WEAK_REPAIR_RESIDUE_PRESENT_SPLIT_BEFORE_SYSTEM_USE"
        elif family == "M15":
            family_recommendation = "M15_TARGET_FIRST_SURVIVES_BUT_EXACT_ORDERING_REMAINS_PROXY_BOUND"
        elif family == "M1":
            family_recommendation = "M1_SUPPORT_SURVIVES_WITH_STABLE_AND_CONFLICT_SPLIT_BRANCHES"
        elif family == "POSITIVE":
            family_recommendation = "POSITIVE_CHALLENGERS_SURVIVE_WITH_CONTROL_AND_CONCENTRATION_PENALTIES"
        elif family == "ENTRY_ADVERSE":
            family_recommendation = "ENTRY_ADVERSE_IS_AVOID_OR_ENTRY_REDESIGN_INTELLIGENCE_NOT_DIRECT_TRADE_SIGNAL"
        elif family == "BINDING":
            family_recommendation = "BINDING_ROWS_PRESERVE_NO_SCALAR_TARGETSTOP_PROVENANCE"
        else:
            family_recommendation = "PRESERVE_FAMILY_CONTEXT"
        family_recommendation_rows.append(
            with_common(
                {
                    "family_recommendation_id": f"OHLC-GTOS-SYSTEM-TRANSFER-FAMILY-{len(family_recommendation_rows) + 1:05d}",
                    "primary_export_family": family,
                    "branch_count": len(rows),
                    "decision_direction_counts": compact_counter(decision_counts),
                    "system_decision_class_counts": compact_counter(Counter(row.get("system_decision_class") for row in rows)),
                    "market_transfer_class_counts": compact_counter(transfer_counts),
                    "symbol_counts": compact_counter(Counter(row.get("symbol") for row in rows)),
                    "route_session_counts": compact_counter(Counter(row.get("route_session") for row in rows)),
                    "primitive_family_counts": compact_counter(Counter(row.get("primitive_family") for row in rows)),
                    "family_recommendation": family_recommendation,
                    "branch_queue_ids": [row.get("branch_queue_id") for row in rows],
                },
                generated_at,
                manifest_hash,
            )
        )

    bucket_sources = {
        "primary_export_family": Counter(row.get("primary_export_family") for row in branch_rows),
        "branch_result_binary": Counter(row.get("branch_result_binary") for row in branch_rows),
        "symbol": Counter(row.get("symbol") for row in branch_rows),
        "route_session": Counter(row.get("route_session") for row in branch_rows),
        "side": Counter(row.get("side") for row in branch_rows),
        "route_descriptor": Counter(row.get("route_descriptor") for row in branch_rows),
        "primitive_family": Counter(row.get("primitive_family") for row in branch_rows),
        "decision_direction": Counter(row.get("decision_direction") for row in branch_rows),
        "system_decision_class": Counter(row.get("system_decision_class") for row in branch_rows),
        "market_transfer_class": Counter(row.get("market_transfer_class") for row in branch_rows),
        "target_stop_result": Counter(row.get("target_stop_result") for row in branch_rows),
        "non_ob_primitive_scope": Counter(row.get("non_ob_primitive_scope") for row in branch_rows),
    }

    question_rows = [
        {
            "question_id": "OHLC-GTOS-SYSTEM-TRANSFER-QUESTION-001",
            "question": "Which branches become keep/kill/redesign/repair decisions after joining all executable family detail packets?",
            "answer_route": "Use BRANCH_LEDGER and KEEP_KILL_REDESIGN_LEDGER over all 386 branch IDs.",
        },
        {
            "question_id": "OHLC-GTOS-SYSTEM-TRANSFER-QUESTION-002",
            "question": "Which mechanics currently transfer across symbol/session/side and which are market-specific?",
            "answer_route": "Use TRANSFER_MATRIX_LEDGER and MARKET_SESSION_DECISION_LEDGER; concentration is preserved, not hidden.",
        },
        {
            "question_id": "OHLC-GTOS-SYSTEM-TRANSFER-QUESTION-003",
            "question": "Does this denominator cover non-OB primitives?",
            "answer_route": "Yes: route descriptors are sweep-close-back-inside and lower-wick-exhaustion; continue broadening from primitive factory roots beyond this branch queue.",
        },
        {
            "question_id": "OHLC-GTOS-SYSTEM-TRANSFER-QUESTION-004",
            "question": "What immediate same-resource work follows?",
            "answer_route": "Build transfer/failure expansion across primitive factory outputs by symbol/session/timeframe/data root, then test non-OB and inverse/avoid mechanics outside the current 386-branch queue.",
        },
    ]
    for row in question_rows:
        with_common(row, generated_at, manifest_hash)

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_RECOMMENDATION",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_accepted_branch_rows": len(accepted_rows),
            "input_next_layer_branch_rows": len(next_rows),
            "input_source_implication_branch_rows": len(source_rows),
            "input_m15_scope_rows": len(m15_scope_rows),
            "input_m15_detail_rows": len(m15_detail_rows),
            "input_m1_scope_rows": len(m1_scope_rows),
            "input_m1_detail_rows": len(m1_detail_rows),
            "input_positive_scope_rows": len(positive_scope_rows),
            "input_positive_detail_rows": len(positive_detail_rows),
            "input_entry_adverse_scope_rows": len(entry_scope_rows),
            "input_entry_adverse_detail_rows": len(entry_detail_rows),
            "input_entry_adverse_rejected_rows": len(entry_rejected_rows),
            "branch_recommendation_rows": len(branch_rows),
            "keep_kill_redesign_rows": len(keep_kill_rows),
            "market_session_decision_rows": len(market_session_rows),
            "transfer_matrix_rows": len(transfer_matrix_rows),
            "family_recommendation_rows": len(family_recommendation_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_manifest),
        },
        "upstream_counts": {
            "accepted_builder": accepted_result.get("counts", {}),
            "next_layer": next_layer_result.get("counts", {}),
            "source_implication": source_result.get("counts", {}),
            "m15_detail": m15_result.get("counts", {}),
            "m1_detail": m1_result.get("counts", {}),
            "positive_detail": positive_result.get("counts", {}),
            "entry_adverse_detail": entry_result.get("counts", {}),
        },
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_sources.items())},
        "decision_stats": {
            "branch_rows": len(branch_rows),
            "non_ob_primitive_rows": sum(1 for row in branch_rows if row.get("non_ob_primitive_scope")),
            "market_specific_or_concentrated_rows": sum(1 for row in branch_rows if row.get("market_specific_concentration_flag")),
            "keep_challenger_rows": sum(1 for row in branch_rows if row.get("decision_direction") == "KEEP_CHALLENGER"),
            "kill_or_redesign_rows": sum(1 for row in branch_rows if row.get("decision_direction") == "KILL_OR_REDESIGN"),
            "split_redesign_rows": sum(1 for row in branch_rows if row.get("decision_direction") == "SPLIT_REDESIGN"),
            "repair_then_review_rows": sum(1 for row in branch_rows if row.get("decision_direction") == "REPAIR_THEN_REVIEW_CHALLENGER"),
            "preserve_requirement_rows": sum(1 for row in branch_rows if row.get("decision_direction") == "PRESERVE_REQUIREMENT"),
        },
        "system_decision": {
            "system_recommendation": (
                "SYSTEM_TRANSFER_RECOMMENDATION_RESULT: keep M15/M1/POSITIVE challenger mechanics only where "
                "their family-specific evidence survives, downgrade or repair SOURCE where bar-spread proxy weakens it, "
                "use ENTRY_ADVERSE accepted rows as avoid/entry-redesign intelligence rather than direct trade signals, "
                "and immediately broaden transfer/failure testing beyond the current GBPJPY/XAUUSD sweep/wick branch queue."
            ),
            "branch_rows": len(branch_rows),
            "family_recommendation_rows": len(family_recommendation_rows),
            "transfer_matrix_rows": len(transfer_matrix_rows),
            "market_session_decision_rows": len(market_session_rows),
        },
        "source_manifest_hash": manifest_hash,
    }

    outputs = [
        (BRANCH_LEDGER, branch_rows),
        (KEEP_KILL_REDESIGN_LEDGER, keep_kill_rows),
        (MARKET_SESSION_LEDGER, market_session_rows),
        (TRANSFER_MATRIX_LEDGER, transfer_matrix_rows),
        (FAMILY_RECOMMENDATION_LEDGER, family_recommendation_rows),
        (QUESTION_LEDGER, question_rows),
        (SOURCE_MANIFEST_LEDGER, source_manifest),
    ]
    for path, rows in outputs:
        write_jsonl(path, rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Branch System Transfer Recommendation",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Branch recommendation rows: `{len(branch_rows)}`",
                f"- Keep/kill/redesign rows: `{len(keep_kill_rows)}`",
                f"- Market/session decision rows: `{len(market_session_rows)}`",
                f"- Transfer matrix rows: `{len(transfer_matrix_rows)}`",
                f"- Family recommendation rows: `{len(family_recommendation_rows)}`",
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
                "type": "branch_system_transfer_recommendation",
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
                    "event_type": "branch_system_transfer_recommendation_built",
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
