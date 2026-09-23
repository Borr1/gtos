#!/usr/bin/env python3
"""Execute replay-builder parameter policies into same-resource selector rows."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

PARAM_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET_RESULT_2026-05-16.json"
PARAM_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET_BRANCH_LEDGER_2026-05-16.jsonl"
PARAM_FAMILY = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET_FAMILY_LEDGER_2026-05-16.jsonl"
PARAM_SOURCE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET_SOURCE_LEDGER_2026-05-16.jsonl"
PARAM_M15 = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET_M15_LEDGER_2026-05-16.jsonl"
PARAM_M1 = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET_M1_LEDGER_2026-05-16.jsonl"
PARAM_POSITIVE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET_POSITIVE_LEDGER_2026-05-16.jsonl"
PARAM_ENTRY_ADVERSE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET_ENTRY_ADVERSE_LEDGER_2026-05-16.jsonl"
PARAM_BINDING = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET_BINDING_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_RESULT_2026-05-16.json"
BRANCH_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_BRANCH_LEDGER_2026-05-16.jsonl"
FAMILY_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_FAMILY_LEDGER_2026-05-16.jsonl"
SOURCE_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_SOURCE_COST_CAP_ACQUISITION_LEDGER_2026-05-16.jsonl"
M15_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_M15_BOUNDS_SELECTOR_LEDGER_2026-05-16.jsonl"
M1_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_M1_SUPPORT_CONFLICT_SELECTOR_LEDGER_2026-05-16.jsonl"
POSITIVE_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_POSITIVE_REPLAY_REPAIR_LEDGER_2026-05-16.jsonl"
ENTRY_ADVERSE_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_ENTRY_ADVERSE_REDESIGN_LEDGER_2026-05-16.jsonl"
BINDING_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_BINDING_PRESERVATION_LEDGER_2026-05-16.jsonl"
BUCKET_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_QUESTION_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Branch parameter execution/scoring packet only. It consumes replay-builder "
    "parameter rows, instantiates deterministic same-resource research builders "
    "for source, M15, M1, positive, and entry/adverse families, and emits "
    "accepted/rejected branch-builder results plus proxy score deltas. It does "
    "not change live behavior and does not claim broker R/PnL, realized "
    "expectancy, win-rate, live-readiness, promotion, or live effect."
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


def by_branch(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["branch_queue_id"]): row for row in rows if row.get("branch_queue_id") is not None}


def group_by_branch(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("branch_queue_id") is not None:
            grouped[str(row["branch_queue_id"])].append(row)
    return grouped


def branch_sort_key(branch_id: str) -> tuple[str, int]:
    try:
        prefix, suffix = branch_id.rsplit("-", 1)
        return prefix, int(suffix)
    except (ValueError, IndexError):
        return branch_id, 0


def fnum(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def round_or_none(value: Any, digits: int = 6) -> float | None:
    value_float = fnum(value)
    return round(value_float, digits) if value_float is not None else None


def sign_class(value: Any) -> str:
    value_float = fnum(value)
    if value_float is None:
        return "NO_SCALAR_SELECTOR_SCORE"
    if value_float > 0:
        return "SELECTOR_SCORE_POSITIVE"
    if value_float < 0:
        return "SELECTOR_SCORE_NEGATIVE"
    return "SELECTOR_SCORE_ZERO"


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def common_base(row: dict[str, Any]) -> dict[str, Any]:
    route_candidate_id = row.get("route_candidate_id")
    route_session = row.get("route_session")
    if route_session is None and isinstance(route_candidate_id, str):
        parts = route_candidate_id.split("|")
        if len(parts) >= 2 and parts[1]:
            route_session = parts[1]
    return {
        "branch_queue_id": row.get("branch_queue_id"),
        "matrix_branch_id": row.get("matrix_branch_id"),
        "route_candidate_id": route_candidate_id,
        "symbol": row.get("symbol"),
        "route_session": route_session,
        "side": row.get("side"),
        "entry_variant": row.get("entry_variant"),
        "target_stop_contract_id": row.get("target_stop_contract_id"),
    }


def common_base_with_branch(row: dict[str, Any], branch: dict[str, Any]) -> dict[str, Any]:
    """Preserve sidecar row identity while filling missing required joins from the branch."""

    row_base = common_base(row)
    branch_base = common_base(branch)
    return {key: row_base.get(key) if row_base.get(key) is not None else branch_base.get(key) for key in branch_base}


def source_manifest_rows(paths: list[Path], generated_at: str) -> tuple[list[dict[str, Any]], str]:
    rows = []
    for index, path in enumerate(paths, 1):
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-REPLAY-SELECTOR-SRC-{index:04d}",
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


def source_execution(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {
            "source_selector_policy": "SOURCE_SELECTOR_NOT_IN_SCOPE",
            "source_selector_execution_status": "NO_SOURCE_SELECTOR_EXECUTION",
            "source_selector_score": None,
            "source_selector_score_class": "NO_SCALAR_SELECTOR_SCORE",
        }
    policy = row.get("source_builder_policy")
    if policy == "USE_COST_CAP_LOWER_BOUND_AND_ACQUIRE_EXACT_SOURCE":
        status = "SOURCE_COST_CAP_LOWER_BOUND_EXECUTED_EXACT_SOURCE_QUEUED"
        action = "USE_COST_CAP_LOWER_BOUND_UNTIL_EXACT_SOURCE_AVAILABLE"
    elif policy == "AVOID_UNTIL_EXACT_SOURCE_REPAIR":
        status = "SOURCE_AVOID_EXECUTED_EXACT_SOURCE_REPAIR_QUEUED"
        action = "AVOID_OR_REPAIR_BEFORE_REPLAY"
    elif policy == "SPLIT_LOW_HIGH_COST_BOUNDS_AND_ACQUIRE_SOURCE":
        status = "SOURCE_LOW_HIGH_BOUNDS_SPLIT_EXECUTED_EXACT_SOURCE_QUEUED"
        action = "PRESERVE_LOW_HIGH_BOUNDS_AND_ACQUIRE_SOURCE"
    else:
        status = "SOURCE_CONTEXT_EXECUTED_NO_SOURCE_ACTION"
        action = "PRESERVE_CONTEXT"
    score = round_or_none(row.get("source_builder_parameter_score"))
    return {
        "source_selector_policy": policy,
        "source_selector_execution_status": status,
        "source_selector_action": action,
        "source_selector_score": score,
        "source_selector_score_class": sign_class(score),
        "source_exact_acquisition_required": row.get("source_exact_acquisition_required"),
        "source_cost_cap_required": row.get("source_cost_cap_required"),
        "source_cost_sensitivity_span": row.get("source_cost_sensitivity_span"),
    }


def m15_execution(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {
            "m15_selector_policy": "M15_SELECTOR_NOT_IN_SCOPE",
            "m15_selector_execution_status": "NO_M15_SELECTOR_EXECUTION",
            "m15_selector_score": None,
            "m15_selector_score_class": "NO_SCALAR_SELECTOR_SCORE",
        }
    policy = row.get("m15_builder_policy")
    lower = fnum(row.get("m15_interval_lower_mean"))
    midpoint = fnum(row.get("m15_interval_midpoint_mean"))
    upper = fnum(row.get("m15_interval_upper_mean"))
    if policy == "TARGET_FIRST_CONSERVATIVE_BOUND_SELECTOR":
        status = "M15_TARGET_FIRST_CONSERVATIVE_LOWER_BOUND_EXECUTED"
        action = "CHALLENGER_ONLY_IF_LOWER_BOUND_POSITIVE"
        score = lower
    elif policy == "STOP_FIRST_AVOID_OR_REDESIGN_SELECTOR":
        status = "M15_STOP_FIRST_AVOID_REDESIGN_BOUND_EXECUTED"
        action = "AVOID_OR_REDESIGN_UNLESS_REPAIRED"
        score = upper if upper is not None else midpoint
    elif policy == "TARGET_STOP_BOUNDS_SPLIT_SELECTOR":
        status = "M15_TARGET_STOP_BOUNDS_SPLIT_EXECUTED"
        action = "KEEP_LOWER_MID_UPPER_BOUNDS_FOR_NEXT_SPLIT"
        score = midpoint
    else:
        status = "M15_SIDE_CAR_CONTEXT_EXECUTED"
        action = "PRESERVE_SIDE_CAR_ORDERING_CONTEXT"
        score = midpoint
    return {
        "m15_selector_policy": policy,
        "m15_selector_execution_status": status,
        "m15_selector_action": action,
        "m15_selector_score": round_or_none(score),
        "m15_selector_score_class": sign_class(score),
        "m15_interval_lower_mean": row.get("m15_interval_lower_mean"),
        "m15_interval_midpoint_mean": row.get("m15_interval_midpoint_mean"),
        "m15_interval_upper_mean": row.get("m15_interval_upper_mean"),
        "m15_exact_chronology_claim": False,
    }


def m1_execution(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {
            "m1_selector_policy": "M1_SELECTOR_NOT_IN_SCOPE",
            "m1_selector_execution_status": "NO_M1_SELECTOR_EXECUTION",
            "m1_selector_score": None,
            "m1_selector_score_class": "NO_SCALAR_SELECTOR_SCORE",
        }
    policy = row.get("m1_builder_policy")
    score = round_or_none(row.get("m1_support_adjusted_midpoint"))
    if policy == "SUPPORT_STABLE_CHALLENGER_SELECTOR":
        status = "M1_SUPPORT_STABLE_CHALLENGER_EXECUTED"
        action = "KEEP_SUPPORT_STABLE_CHALLENGER"
    elif policy == "SUPPORT_POSITIVE_BRANCH_AGGREGATE_CONFLICT_SPLIT":
        status = "M1_SUPPORT_BRANCH_CONFLICT_SPLIT_EXECUTED"
        action = "SPLIT_SUPPORT_POSITIVE_FROM_BRANCH_AGGREGATE"
    elif policy == "M1_SIDE_CAR_CONTEXT_SELECTOR":
        status = "M1_SIDE_CAR_CONTEXT_EXECUTED"
        action = "PRESERVE_SIDE_CAR_SUPPORT_CONTEXT"
    else:
        status = "M1_CONTEXT_EXECUTED"
        action = "PRESERVE_CONTEXT"
    return {
        "m1_selector_policy": policy,
        "m1_selector_execution_status": status,
        "m1_selector_action": action,
        "m1_selector_score": score,
        "m1_selector_score_class": sign_class(score),
        "m1_support_adjusted_midpoint": row.get("m1_support_adjusted_midpoint"),
        "m1_exact_chronology_claim": False,
        "m1_tick_ordering_exact": False,
    }


def positive_execution(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {
            "positive_selector_policy": "POSITIVE_SELECTOR_NOT_IN_SCOPE",
            "positive_selector_execution_status": "NO_POSITIVE_SELECTOR_EXECUTION",
            "positive_selector_score": None,
            "positive_selector_score_class": "NO_SCALAR_SELECTOR_SCORE",
        }
    policy = row.get("positive_builder_policy")
    score = round_or_none(row.get("positive_adjusted_lower"))
    if score is None:
        score = round_or_none(row.get("positive_builder_parameter_score"))
    if policy == "REPLAY_NOW_WITH_MODIFIER_PENALTIES":
        status = "POSITIVE_REPLAY_NOW_SELECTOR_EXECUTED"
        action = "REPLAY_WITH_CONTROL_CONCENTRATION_MODIFIERS"
    elif policy == "REPAIR_SOURCE_OR_STRESS_BEFORE_REPLAY":
        status = "POSITIVE_REPAIR_STRESS_FIRST_SELECTOR_EXECUTED"
        action = "REPAIR_SOURCE_OR_STRESS_BEFORE_REPLAY"
    elif policy == "POSITIVE_SIDE_CAR_REPLAY_CONTEXT":
        status = "POSITIVE_SIDE_CAR_REPLAY_CONTEXT_EXECUTED"
        action = "PRESERVE_SIDE_CAR_REPLAY_CONTEXT"
    else:
        status = "POSITIVE_CONTEXT_EXECUTED"
        action = "PRESERVE_CONTEXT"
    return {
        "positive_selector_policy": policy,
        "positive_selector_execution_status": status,
        "positive_selector_action": action,
        "positive_selector_score": score,
        "positive_selector_score_class": sign_class(score),
        "positive_replayable_now": row.get("positive_replayable_now"),
        "positive_modifier_penalty": row.get("positive_modifier_penalty"),
        "positive_adjusted_lower": row.get("positive_adjusted_lower"),
        "positive_adjusted_midpoint": row.get("positive_adjusted_midpoint"),
        "positive_control_delta_modifier_class": row.get("positive_control_delta_modifier_class"),
        "positive_concentration_modifier_class": row.get("positive_concentration_modifier_class"),
    }


def entry_execution(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {
            "entry_adverse_selector_policy": "ENTRY_ADVERSE_SELECTOR_NOT_IN_SCOPE",
            "entry_adverse_selector_execution_status": "NO_ENTRY_ADVERSE_SELECTOR_EXECUTION",
            "entry_adverse_selector_score": None,
            "entry_adverse_selector_score_class": "NO_SCALAR_SELECTOR_SCORE",
        }
    policy = row.get("entry_adverse_builder_policy")
    score = round_or_none(row.get("redesign_pressure_score"))
    if policy == "ENTRY_AND_ADVERSE_REDESIGN_PRESSURE_SELECTOR":
        status = "ENTRY_AND_ADVERSE_REDESIGN_SELECTOR_EXECUTED"
        action = "REDESIGN_ENTRY_AND_ADVERSE_STOP_FIRST_GEOMETRY"
    elif policy == "ENTRY_REDESIGN_ADVERSE_PRESERVE_SELECTOR":
        status = "ENTRY_REDESIGN_ADVERSE_PRESERVE_SELECTOR_EXECUTED"
        action = "REDESIGN_ENTRY_GEOMETRY_PRESERVE_ADVERSE_CONTEXT"
    elif policy == "ENTRY_ADVERSE_PRESERVE_CONTEXT":
        status = "ENTRY_ADVERSE_PRESERVE_CONTEXT_EXECUTED"
        action = "PRESERVE_ENTRY_ADVERSE_CONTEXT"
    else:
        status = "ENTRY_ADVERSE_CONTEXT_EXECUTED"
        action = "PRESERVE_CONTEXT"
    return {
        "entry_adverse_selector_policy": policy,
        "entry_adverse_selector_execution_status": status,
        "entry_adverse_selector_action": action,
        "entry_adverse_selector_score": score,
        "entry_adverse_selector_score_class": sign_class(score),
        "entry_adverse_action_scope": row.get("entry_adverse_action_scope"),
        "target_first_rate": row.get("target_first_rate"),
        "stop_first_rate": row.get("stop_first_rate"),
        "no_fill_or_unfilled_rate": row.get("no_fill_or_unfilled_rate"),
        "fillability_rate": row.get("fillability_rate"),
        "entry_target_stop_balance_class": row.get("entry_target_stop_balance_class"),
        "redesign_pressure_score": row.get("redesign_pressure_score"),
    }


def primary_execution(branch: dict[str, Any], executions: dict[str, dict[str, Any]]) -> tuple[str, str, float | None, str]:
    family = branch.get("primary_export_family")
    if family == "SOURCE":
        row = executions["source"]
        return str(row.get("source_selector_execution_status")), str(row.get("source_selector_action")), row.get("source_selector_score"), str(row.get("source_selector_score_class"))
    if family == "M15":
        row = executions["m15"]
        return str(row.get("m15_selector_execution_status")), str(row.get("m15_selector_action")), row.get("m15_selector_score"), str(row.get("m15_selector_score_class"))
    if family == "M1":
        row = executions["m1"]
        return str(row.get("m1_selector_execution_status")), str(row.get("m1_selector_action")), row.get("m1_selector_score"), str(row.get("m1_selector_score_class"))
    if family == "POSITIVE":
        row = executions["positive"]
        return str(row.get("positive_selector_execution_status")), str(row.get("positive_selector_action")), row.get("positive_selector_score"), str(row.get("positive_selector_score_class"))
    if family == "ENTRY_ADVERSE":
        row = executions["entry"]
        return str(row.get("entry_adverse_selector_execution_status")), str(row.get("entry_adverse_selector_action")), row.get("entry_adverse_selector_score"), str(row.get("entry_adverse_selector_score_class"))
    return "BINDING_PROVENANCE_ONLY_NO_SELECTOR_EXECUTION", "PRESERVE_BINDING_NO_SCALAR_FILL", None, "NO_SCALAR_SELECTOR_SCORE"


def branch_builder_decision(
    branch: dict[str, Any],
    primary_status: str,
    primary_action: str,
    primary_score: float | None,
    primary_score_class: str,
    executions: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Convert selector output into a binary branch-builder decision."""

    family = branch.get("primary_export_family")
    score = fnum(primary_score)
    proxy_actionability = fnum(branch.get("proxy_actionability_score"))
    score_delta = score - proxy_actionability if score is not None and proxy_actionability is not None else None

    accepted = False
    decision_class = "REJECTED_NO_DECISION_RULE_MATCHED"
    recommendation = "KILL_OR_REPAIR_BEFORE_NEXT_BUILDER"
    success_decision = "NO_BUILDER_SUCCESS_DECISION"
    failure_decision = "REJECTED_BY_EXECUTABLE_SELECTOR_RULE"

    if family == "BINDING":
        decision_class = "REJECTED_BINDING_PROVENANCE_ONLY_NO_SCALAR"
        recommendation = "PRESERVE_BINDING_PROVENANCE_ONLY"
        failure_decision = "NO_SCALAR_TARGETSTOP_BINDING"
    elif family == "SOURCE":
        if primary_status == "SOURCE_COST_CAP_LOWER_BOUND_EXECUTED_EXACT_SOURCE_QUEUED" and score is not None and score > 0:
            accepted = True
            decision_class = "ACCEPTED_SOURCE_COST_CAP_LOWER_BOUND_WITH_EXACT_SOURCE_ACQUISITION"
            recommendation = "RUN_SOURCE_COST_CAP_CHALLENGER_AND_EXACT_SOURCE_ACQUISITION"
            success_decision = "LOWER_BOUND_REMAINS_POSITIVE_AFTER_COST_CAP"
            failure_decision = "EXACT_SOURCE_STILL_REQUIRED_FOR_HIGH_SPREAD_FLIP_PROOF"
        elif primary_status == "SOURCE_LOW_HIGH_BOUNDS_SPLIT_EXECUTED_EXACT_SOURCE_QUEUED" and score is not None and score > 0:
            accepted = True
            decision_class = "ACCEPTED_SOURCE_BOUNDS_SPLIT_FOR_EXACT_SOURCE_REPAIR"
            recommendation = "RUN_LOW_HIGH_SOURCE_BOUNDS_SPLIT_AND_ACQUIRE_EXACT_SOURCE"
            success_decision = "MIDPOINT_POSITIVE_BUT_INTERVAL_NEEDS_SOURCE_REPAIR"
            failure_decision = "LOW_HIGH_BOUNDS_NOT_COLLAPSED"
        else:
            decision_class = "REJECTED_SOURCE_REPAIR_OR_AVOID_REQUIRED"
            recommendation = "AVOID_SOURCE_BRANCH_UNTIL_EXACT_SOURCE_REPAIR_OR_COST_MODEL_CHANGE"
            failure_decision = "SOURCE_SELECTOR_NONPOSITIVE_OR_REPAIR_FIRST"
    elif family == "M15":
        if primary_status == "M15_TARGET_FIRST_CONSERVATIVE_LOWER_BOUND_EXECUTED" and score is not None and score > 0:
            accepted = True
            decision_class = "ACCEPTED_M15_TARGET_FIRST_CONSERVATIVE_BOUND"
            recommendation = "RUN_M15_TARGET_FIRST_CHALLENGER_BUILDER"
            success_decision = "TARGET_FIRST_LOWER_BOUND_POSITIVE"
            failure_decision = "NO_M15_FAILURE_DOMINANT"
        elif primary_status == "M15_TARGET_STOP_BOUNDS_SPLIT_EXECUTED" and score is not None and score > 0:
            accepted = True
            decision_class = "ACCEPTED_M15_BOUNDS_SPLIT_POSITIVE_MIDPOINT"
            recommendation = "RUN_M15_TARGET_STOP_BOUNDS_SPLIT_BUILDER"
            success_decision = "M15_BOUNDS_MIDPOINT_POSITIVE"
            failure_decision = "M15_INTERVAL_NOT_STRICTLY_COLLAPSED"
        else:
            decision_class = "REJECTED_M15_STOP_FIRST_OR_NONPOSITIVE_BOUND"
            recommendation = "BUILD_M15_AVOID_OR_REDESIGN_FILTER"
            failure_decision = "M15_STOP_FIRST_OR_NONPOSITIVE_SELECTOR_SCORE"
    elif family == "M1":
        if score is not None and score > 0:
            accepted = True
            if primary_status == "M1_SUPPORT_BRANCH_CONFLICT_SPLIT_EXECUTED":
                decision_class = "ACCEPTED_M1_SUPPORT_CONFLICT_SPLIT"
                recommendation = "RUN_M1_SUPPORT_CONFLICT_SPLIT_BUILDER"
                success_decision = "M1_SUPPORT_POSITIVE_DESPITE_BRANCH_AGGREGATE_CONFLICT"
                failure_decision = "BRANCH_AGGREGATE_CONFLICT_REMAINS_SPLIT_REQUIRED"
            else:
                decision_class = "ACCEPTED_M1_SUPPORT_STABLE_CHALLENGER"
                recommendation = "RUN_M1_SUPPORT_STABLE_CHALLENGER_BUILDER"
                success_decision = "M1_SUPPORT_ADJUSTED_MIDPOINT_POSITIVE"
                failure_decision = "NO_M1_FAILURE_DOMINANT"
        else:
            decision_class = "REJECTED_M1_SUPPORT_NONPOSITIVE"
            recommendation = "KILL_M1_BRANCH_OR_REPAIR_SUPPORT_SOURCE"
            failure_decision = "M1_SUPPORT_SELECTOR_NONPOSITIVE"
    elif family == "POSITIVE":
        if (
            primary_status == "POSITIVE_REPLAY_NOW_SELECTOR_EXECUTED"
            and executions["positive"].get("positive_replayable_now") is True
            and score is not None
            and score > 0
        ):
            accepted = True
            decision_class = "ACCEPTED_POSITIVE_REPLAY_NOW_AFTER_MODIFIERS"
            recommendation = "RUN_POSITIVE_CHALLENGER_REPLAY_BUILDER"
            success_decision = "POSITIVE_REPLAYABLE_AND_ADJUSTED_SCORE_POSITIVE"
            failure_decision = "CONTROL_CONCENTRATION_MODIFIERS_STILL_APPLY"
        else:
            decision_class = "REJECTED_POSITIVE_REPAIR_OR_NONPOSITIVE"
            recommendation = "REPAIR_SOURCE_OR_STRESS_POSITIVE_BRANCH_BEFORE_REPLAY"
            failure_decision = "POSITIVE_SELECTOR_REPAIR_FIRST_OR_NONPOSITIVE"
    elif family == "ENTRY_ADVERSE":
        if primary_status in {
            "ENTRY_AND_ADVERSE_REDESIGN_SELECTOR_EXECUTED",
            "ENTRY_REDESIGN_ADVERSE_PRESERVE_SELECTOR_EXECUTED",
        } and score is not None and score > 0:
            accepted = True
            decision_class = "ACCEPTED_ENTRY_ADVERSE_REDESIGN_BUILDER"
            recommendation = "RUN_ENTRY_ADVERSE_REDESIGN_BUILDER"
            success_decision = "ENTRY_ADVERSE_REDESIGN_PRESSURE_POSITIVE"
            failure_decision = "REDESIGN_IS_REQUIRED_BEFORE_ANY_CHALLENGER_USE"
        else:
            decision_class = "REJECTED_ENTRY_ADVERSE_PRESERVE_OR_NONPOSITIVE"
            recommendation = "PRESERVE_OR_KILL_ENTRY_ADVERSE_BRANCH"
            failure_decision = "ENTRY_ADVERSE_SELECTOR_NOT_ACTIONABLE"

    return {
        "branch_result_binary": "ACCEPTED" if accepted else "REJECTED",
        "branch_decision_class": decision_class,
        "branch_system_recommendation": recommendation,
        "success_decision": success_decision,
        "failure_decision": failure_decision,
        "proxy_score_delta_vs_actionability": round_or_none(score_delta),
        "proxy_score_delta_class": sign_class(score_delta),
        "accepted_for_next_executable_builder": accepted,
        "primary_selector_action": primary_action,
        "primary_selector_score_class": primary_score_class,
    }


def system_recommendation(branch_rows: list[dict[str, Any]]) -> dict[str, Any]:
    accepted_by_family = Counter(
        row.get("primary_export_family")
        for row in branch_rows
        if row.get("branch_result_binary") == "ACCEPTED"
    )
    rejected_by_family = Counter(
        row.get("primary_export_family")
        for row in branch_rows
        if row.get("branch_result_binary") == "REJECTED"
    )
    return {
        "system_recommendation": (
            "EXECUTE_ACCEPTED_BUILDER_BRANCHES_NOW_AND_REJECT_OR_REPAIR_THE_REST: "
            "run accepted source cost-cap/source-repair, M15 bounds, M1 support, "
            "positive replay, and entry/adverse redesign builders as branch-local "
            "research; do not carry rejected branches forward except through their "
            "explicit repair/avoid recommendations."
        ),
        "accepted_branch_count": int(sum(accepted_by_family.values())),
        "rejected_branch_count": int(sum(rejected_by_family.values())),
        "accepted_by_primary_family": compact_counter(accepted_by_family),
        "rejected_by_primary_family": compact_counter(rejected_by_family),
    }


def write_summary(result: dict[str, Any]) -> None:
    lines = [
        "# Historical OHLC GTOS Replay Branch Parameter Execution Scoring Packet",
        "",
        f"Generated UTC: `{result['generated_utc']}`",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Decisive System Recommendation",
        "",
        result["system_decision"]["system_recommendation"],
        "",
        "## Counts",
        "",
    ]
    for key, value in result["counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Selector Distributions", ""])
    for category in [
        "primary_selector_execution_status",
        "source_selector_execution_status",
        "m15_selector_execution_status",
        "m1_selector_execution_status",
        "positive_selector_execution_status",
        "entry_adverse_selector_execution_status",
    ]:
        lines.append(f"### {category}")
        for bucket, count in result["bucket_distributions"].get(category, {}).items():
            lines.append(f"- `{bucket}`: `{count}`")
        lines.append("")
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def update_manifest(result: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST) if OUTPUT_MANIFEST.exists() else {
        "schema": "weekend_mechanical_edge_factory_output_manifest_v1",
        "artifacts": [],
    }
    output_paths = [
        RESULT_PATH,
        BRANCH_LEDGER,
        FAMILY_LEDGER,
        SOURCE_LEDGER,
        M15_LEDGER,
        M1_LEDGER,
        POSITIVE_LEDGER,
        ENTRY_ADVERSE_LEDGER,
        BINDING_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        SUMMARY_PATH,
    ]
    output_path_strings = {path.relative_to(REPO).as_posix() for path in output_paths}
    manifest["artifacts"] = [item for item in manifest.get("artifacts", []) if item.get("path") not in output_path_strings]
    for path in output_paths:
        manifest["artifacts"].append(
            {
                "path": path.relative_to(REPO).as_posix(),
                "status": "created",
                "type": "branch_replay_selector_execution_packet",
                "generated_utc": generated_at,
                "counts": result["counts"],
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest["safe_flags"] = SAFE_FLAGS
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_sprint_ledger(result: dict[str, Any], generated_at: str) -> None:
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "timestamp_utc": generated_at,
                    "event_type": "branch_replay_selector_execution_packet_built",
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


def main() -> int:
    generated_at = now_utc()
    param_result = read_json(PARAM_RESULT)
    branch_rows_in = read_jsonl(PARAM_BRANCH)
    family_rows_in = read_jsonl(PARAM_FAMILY)
    source_rows_in = read_jsonl(PARAM_SOURCE)
    m15_rows_in = read_jsonl(PARAM_M15)
    m1_rows_in = read_jsonl(PARAM_M1)
    positive_rows_in = read_jsonl(PARAM_POSITIVE)
    entry_rows_in = read_jsonl(PARAM_ENTRY_ADVERSE)
    binding_rows_in = read_jsonl(PARAM_BINDING)

    branch_by_id = by_branch(branch_rows_in)
    family_by_id = group_by_branch(family_rows_in)
    source_by_id = by_branch(source_rows_in)
    m15_by_id = by_branch(m15_rows_in)
    m1_by_id = by_branch(m1_rows_in)
    positive_by_id = by_branch(positive_rows_in)
    entry_by_id = by_branch(entry_rows_in)
    binding_by_id = by_branch(binding_rows_in)

    source_manifest, manifest_hash = source_manifest_rows(
        [PARAM_RESULT, PARAM_BRANCH, PARAM_FAMILY, PARAM_SOURCE, PARAM_M15, PARAM_M1, PARAM_POSITIVE, PARAM_ENTRY_ADVERSE, PARAM_BINDING],
        generated_at,
    )

    branch_rows: list[dict[str, Any]] = []
    family_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    m15_rows: list[dict[str, Any]] = []
    m1_rows: list[dict[str, Any]] = []
    positive_rows: list[dict[str, Any]] = []
    entry_rows: list[dict[str, Any]] = []
    binding_rows: list[dict[str, Any]] = []
    bucket_counters: dict[str, Counter[Any]] = defaultdict(Counter)

    for branch_id in sorted(branch_by_id, key=branch_sort_key):
        branch = branch_by_id[branch_id]
        source_exec = source_execution(source_by_id.get(branch_id))
        m15_exec = m15_execution(m15_by_id.get(branch_id))
        m1_exec = m1_execution(m1_by_id.get(branch_id))
        positive_exec = positive_execution(positive_by_id.get(branch_id))
        entry_exec = entry_execution(entry_by_id.get(branch_id))
        executions = {"source": source_exec, "m15": m15_exec, "m1": m1_exec, "positive": positive_exec, "entry": entry_exec}
        primary_status, primary_action, primary_score, primary_score_class = primary_execution(branch, executions)
        decision = branch_builder_decision(branch, primary_status, primary_action, primary_score, primary_score_class, executions)

        branch_record = {
            **common_base(branch),
            "selector_execution_branch_id": f"OHLC-GTOS-REPLAY-SELECTOR-BRANCH-{len(branch_rows) + 1:05d}",
            "replay_builder_parameter_branch_id": branch.get("replay_builder_parameter_branch_id"),
            "work_unit_id": branch.get("work_unit_id"),
            "primary_export_family": branch.get("primary_export_family"),
            "primary_builder_policy": branch.get("primary_builder_policy"),
            "primary_selector_execution_status": primary_status,
            "primary_selector_action": primary_action,
            "primary_selector_score": round_or_none(primary_score),
            "primary_selector_score_class": primary_score_class,
            "proxy_actionability_score": branch.get("proxy_actionability_score"),
            "proxy_score_delta_vs_actionability": decision["proxy_score_delta_vs_actionability"],
            "proxy_score_delta_class": decision["proxy_score_delta_class"],
            "branch_result_binary": decision["branch_result_binary"],
            "branch_decision_class": decision["branch_decision_class"],
            "branch_system_recommendation": decision["branch_system_recommendation"],
            "accepted_for_next_executable_builder": decision["accepted_for_next_executable_builder"],
            "success_decision": decision["success_decision"],
            "failure_decision": decision["failure_decision"],
            "same_resource_execution_status": branch.get("same_resource_execution_status"),
            "replay_builder_surface": branch.get("replay_builder_surface"),
            "source_selector_execution_status": source_exec.get("source_selector_execution_status"),
            "m15_selector_execution_status": m15_exec.get("m15_selector_execution_status"),
            "m1_selector_execution_status": m1_exec.get("m1_selector_execution_status"),
            "positive_selector_execution_status": positive_exec.get("positive_selector_execution_status"),
            "entry_adverse_selector_execution_status": entry_exec.get("entry_adverse_selector_execution_status"),
            "source_exact_acquisition_required": source_exec.get("source_exact_acquisition_required"),
            "source_cost_cap_required": source_exec.get("source_cost_cap_required"),
            "m15_exact_chronology_claim": False,
            "m1_tick_ordering_exact": False,
            "positive_replayable_now": positive_exec.get("positive_replayable_now"),
            "entry_adverse_action_scope": entry_exec.get("entry_adverse_action_scope"),
            "target_stop_result": branch.get("target_stop_result"),
            "sealed_proxy_class": branch.get("sealed_proxy_class"),
            "exact_success_cause": branch.get("exact_success_cause"),
            "exact_failure_cause": branch.get("exact_failure_cause"),
            "exact_missing_geometry_or_source_reason": branch.get("exact_missing_geometry_or_source_reason"),
            "next_computation_hint": "execute_selector_rows_into_family_specific_replay_and_redesign_builders",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "not_completion": True,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }
        branch_rows.append(branch_record)

        if source_by_id.get(branch_id):
            source_row = source_by_id[branch_id]
            source_rows.append({**common_base_with_branch(source_row, branch), "source_selector_execution_id": f"OHLC-GTOS-REPLAY-SELECTOR-SOURCE-{len(source_rows) + 1:05d}", "source_parameter_id": source_row.get("source_parameter_id"), "source_decision_id": source_row.get("source_decision_id"), **source_exec, "safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "not_completion": True, "generated_utc": generated_at, "source_manifest_hash": manifest_hash})
        if m15_by_id.get(branch_id):
            m15_row = m15_by_id[branch_id]
            m15_rows.append({**common_base_with_branch(m15_row, branch), "m15_selector_execution_id": f"OHLC-GTOS-REPLAY-SELECTOR-M15-{len(m15_rows) + 1:05d}", "m15_parameter_id": m15_row.get("m15_parameter_id"), "m15_decision_id": m15_row.get("m15_decision_id"), **m15_exec, "safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "not_completion": True, "generated_utc": generated_at, "source_manifest_hash": manifest_hash})
        if m1_by_id.get(branch_id):
            m1_row = m1_by_id[branch_id]
            m1_rows.append({**common_base_with_branch(m1_row, branch), "m1_selector_execution_id": f"OHLC-GTOS-REPLAY-SELECTOR-M1-{len(m1_rows) + 1:05d}", "m1_parameter_id": m1_row.get("m1_parameter_id"), "m1_decision_id": m1_row.get("m1_decision_id"), **m1_exec, "safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "not_completion": True, "generated_utc": generated_at, "source_manifest_hash": manifest_hash})
        if positive_by_id.get(branch_id):
            positive_row = positive_by_id[branch_id]
            positive_rows.append({**common_base_with_branch(positive_row, branch), "positive_selector_execution_id": f"OHLC-GTOS-REPLAY-SELECTOR-POSITIVE-{len(positive_rows) + 1:05d}", "positive_parameter_id": positive_row.get("positive_parameter_id"), "positive_decision_id": positive_row.get("positive_decision_id"), **positive_exec, "safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "not_completion": True, "generated_utc": generated_at, "source_manifest_hash": manifest_hash})
        if entry_by_id.get(branch_id):
            entry_row = entry_by_id[branch_id]
            entry_rows.append({**common_base_with_branch(entry_row, branch), "entry_adverse_selector_execution_id": f"OHLC-GTOS-REPLAY-SELECTOR-ENTRY-ADVERSE-{len(entry_rows) + 1:05d}", "entry_adverse_parameter_id": entry_row.get("entry_adverse_parameter_id"), "entry_adverse_decision_id": entry_row.get("entry_adverse_decision_id"), **entry_exec, "safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "not_completion": True, "generated_utc": generated_at, "source_manifest_hash": manifest_hash})
        if binding_by_id.get(branch_id):
            binding_row = binding_by_id[branch_id]
            binding_rows.append({**common_base_with_branch(binding_row, branch), "binding_selector_execution_id": f"OHLC-GTOS-REPLAY-SELECTOR-BINDING-{len(binding_rows) + 1:05d}", "binding_parameter_id": binding_row.get("binding_parameter_id"), "binding_decision_id": binding_row.get("binding_decision_id"), "binding_selector_execution_status": "BINDING_PROVENANCE_ONLY_NO_SELECTOR_EXECUTION", "binding_selector_action": "PRESERVE_BINDING_NO_SCALAR_FILL", "no_scalar_fill": True, "primary_selector_score": None, "safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "not_completion": True, "generated_utc": generated_at, "source_manifest_hash": manifest_hash})

        family_policy_lookup = {
            "SOURCE": source_exec.get("source_selector_execution_status"),
            "ORDERING": m15_exec.get("m15_selector_execution_status") if branch_id in m15_by_id else m1_exec.get("m1_selector_execution_status"),
            "ENTRY": entry_exec.get("entry_adverse_selector_execution_status"),
            "ADVERSE": entry_exec.get("entry_adverse_selector_execution_status"),
            "POSITIVE": positive_exec.get("positive_selector_execution_status"),
        }
        family_score_lookup = {
            "SOURCE": source_exec.get("source_selector_score"),
            "ORDERING": m15_exec.get("m15_selector_score") if branch_id in m15_by_id else m1_exec.get("m1_selector_score"),
            "ENTRY": entry_exec.get("entry_adverse_selector_score"),
            "ADVERSE": entry_exec.get("entry_adverse_selector_score"),
            "POSITIVE": positive_exec.get("positive_selector_score"),
        }
        for family_row in sorted(family_by_id.get(branch_id, []), key=lambda row: row.get("family_parameter_id") or ""):
            family = family_row.get("action_family")
            family_rows.append(
                {
                    **common_base_with_branch(family_row, branch),
                    "family_selector_execution_id": f"OHLC-GTOS-REPLAY-SELECTOR-FAMILY-{len(family_rows) + 1:05d}",
                    "family_parameter_id": family_row.get("family_parameter_id"),
                    "family_decision_id": family_row.get("family_decision_id"),
                    "action_family": family,
                    "family_builder_policy": family_row.get("family_builder_policy"),
                    "family_selector_execution_status": family_policy_lookup.get(family),
                    "family_selector_score": round_or_none(family_score_lookup.get(family)),
                    "family_selector_score_class": sign_class(family_score_lookup.get(family)),
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "not_completion": True,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

        for category, value in [
            ("primary_export_family", branch.get("primary_export_family")),
            ("primary_builder_policy", branch.get("primary_builder_policy")),
            ("primary_selector_execution_status", primary_status),
            ("primary_selector_score_class", primary_score_class),
            ("branch_result_binary", decision["branch_result_binary"]),
            ("branch_decision_class", decision["branch_decision_class"]),
            ("branch_system_recommendation", decision["branch_system_recommendation"]),
            ("proxy_score_delta_class", decision["proxy_score_delta_class"]),
            ("source_selector_execution_status", source_exec.get("source_selector_execution_status")),
            ("m15_selector_execution_status", m15_exec.get("m15_selector_execution_status")),
            ("m1_selector_execution_status", m1_exec.get("m1_selector_execution_status")),
            ("positive_selector_execution_status", positive_exec.get("positive_selector_execution_status")),
            ("entry_adverse_selector_execution_status", entry_exec.get("entry_adverse_selector_execution_status")),
            ("same_resource_execution_status", branch.get("same_resource_execution_status")),
        ]:
            bucket_counters[category][str(value)] += 1

    for row in family_rows:
        bucket_counters["action_family"][row.get("action_family")] += 1
        bucket_counters["family_selector_execution_status"][row.get("family_selector_execution_status")] += 1
    for row in source_rows:
        bucket_counters["source_selector_execution_status_subset"][row.get("source_selector_execution_status")] += 1
    for row in m15_rows:
        bucket_counters["m15_selector_execution_status_subset"][row.get("m15_selector_execution_status")] += 1
    for row in m1_rows:
        bucket_counters["m1_selector_execution_status_subset"][row.get("m1_selector_execution_status")] += 1
    for row in positive_rows:
        bucket_counters["positive_selector_execution_status_subset"][row.get("positive_selector_execution_status")] += 1
    for row in entry_rows:
        bucket_counters["entry_adverse_selector_execution_status_subset"][row.get("entry_adverse_selector_execution_status")] += 1
    for row in binding_rows:
        bucket_counters["binding_selector_execution_status"][row.get("binding_selector_execution_status")] += 1

    bucket_rows = []
    for category, counter in sorted(bucket_counters.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                {
                    "bucket_id": f"OHLC-GTOS-REPLAY-SELECTOR-BUCKET-{len(bucket_rows) + 1:05d}",
                    "bucket_category": category,
                    "bucket": str(bucket),
                    "row_count": int(count),
                    "share": round(count / total, 9) if total else None,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

    question_rows = [
        {"question_id": "OHLC-GTOS-REPLAY-SELECTOR-QUESTION-001", "question": "Which branch-primary selector executions are now computable from the parameter packet?", "answer_route": "Use branch selector rows and primary_selector_execution_status."},
        {"question_id": "OHLC-GTOS-REPLAY-SELECTOR-QUESTION-002", "question": "Which source selectors execute cost-cap, exact-source repair, or low/high bound splits?", "answer_route": "Use source selector rows and source_selector_execution_status."},
        {"question_id": "OHLC-GTOS-REPLAY-SELECTOR-QUESTION-003", "question": "Which M15/M1 selectors preserve lower-level ordering bounds without exact chronology/tick claims?", "answer_route": "Use M15/M1 selector rows and exact flags."},
        {"question_id": "OHLC-GTOS-REPLAY-SELECTOR-QUESTION-004", "question": "Which positive and entry/adverse selectors can feed the next replay/redesign builders?", "answer_route": "Use positive and entry/adverse selector execution rows."},
    ]
    for row in question_rows:
        row.update({"safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "not_completion": True, "generated_utc": generated_at, "source_manifest_hash": manifest_hash})

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_parameter_branch_rows": len(branch_rows_in),
            "input_parameter_family_rows": len(family_rows_in),
            "input_parameter_source_rows": len(source_rows_in),
            "input_parameter_m15_rows": len(m15_rows_in),
            "input_parameter_m1_rows": len(m1_rows_in),
            "input_parameter_positive_rows": len(positive_rows_in),
            "input_parameter_entry_adverse_rows": len(entry_rows_in),
            "input_parameter_binding_rows": len(binding_rows_in),
            "branch_selector_rows": len(branch_rows),
            "family_selector_rows": len(family_rows),
            "source_selector_rows": len(source_rows),
            "m15_selector_rows": len(m15_rows),
            "m1_selector_rows": len(m1_rows),
            "positive_selector_rows": len(positive_rows),
            "entry_adverse_selector_rows": len(entry_rows),
            "binding_selector_rows": len(binding_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_manifest),
        },
        "upstream_parameter_counts": param_result.get("counts", {}),
        "system_decision": system_recommendation(branch_rows),
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_counters.items())},
        "coverage": {
            "branch_denominator_preserved": len(branch_rows) == 386,
            "family_rows_per_branch": 5,
            "source_scope": len(source_rows),
            "m15_scope": len(m15_rows),
            "m1_scope": len(m1_rows),
            "positive_scope": len(positive_rows),
            "entry_adverse_scope": len(entry_rows),
            "binding_scope": len(binding_rows),
        },
        "source_manifest_hash": manifest_hash,
    }

    for path, rows in [
        (BRANCH_LEDGER, branch_rows),
        (FAMILY_LEDGER, family_rows),
        (SOURCE_LEDGER, source_rows),
        (M15_LEDGER, m15_rows),
        (M1_LEDGER, m1_rows),
        (POSITIVE_LEDGER, positive_rows),
        (ENTRY_ADVERSE_LEDGER, entry_rows),
        (BINDING_LEDGER, binding_rows),
        (BUCKET_LEDGER, bucket_rows),
        (QUESTION_LEDGER, question_rows),
        (SOURCE_MANIFEST_LEDGER, source_manifest),
    ]:
        write_jsonl(path, rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result)
    update_manifest(result, generated_at)
    append_sprint_ledger(result, generated_at)
    print(json.dumps({"ok": True, "counts": result["counts"], "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
