"""Live mechanical strategy shadow outcome rows.

This module is observation-only. It consumes already-written live candidate and
path-follow rows and emits one append-only row per candidate, strategy, and
as-of candle. It does not call AI, canary, Databento, or order APIs.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.components.gtos_vnext_event_fields import enrich_cp281_event_contract_fields
from src.research_infra.forward_capture import (
    FVG_OB_CONFLUENCE_PATH,
    FOLLOW_STRATEGY_REGISTRY,
    MOONSHOT_SELECTED_ACTION_SOURCE_CAPTURE_PATH,
    MOONSHOT_SELECTED_ACTION_STRATEGY_REGISTRY,
    append_jsonl,
)

SCHEMA_VERSION = "live_mechanical_strategy_shadow_outcome_v1"
DEFAULT_CANDIDATES = Path("shadow_logs/strategy_follow_candidates.jsonl")
DEFAULT_PATHS = Path("shadow_logs/candidate_path_follow.jsonl")
DEFAULT_PENDING_LIFECYCLE = Path("shadow_logs/pending_limit_lifecycle.jsonl")
DEFAULT_LTF_PATH_ORDER = Path("shadow_logs/candidate_ltf_path_order.jsonl")
DEFAULT_FVG_OB_CONFLUENCE = Path(FVG_OB_CONFLUENCE_PATH)
DEFAULT_STRUCTURAL_METADATA = Path("shadow_logs/live_structural_strategy_metadata.jsonl")
DEFAULT_NOFILL_FORWARD_SOURCE_CAPTURE = Path("shadow_logs/nofill_forward_source_capture.jsonl")
DEFAULT_MOONSHOT_SELECTED_ACTION_SOURCE_CAPTURE = Path(
    MOONSHOT_SELECTED_ACTION_SOURCE_CAPTURE_PATH
)
DEFAULT_PENDING_TICK_SPREAD_RECONSTRUCTION = Path(
    "shadow_logs/pending_lifecycle_tick_spread_reconstruction.jsonl"
)
DEFAULT_STANDALONE_FVG_REPAIR_DECISIONS = Path(
    "shadow_logs/standalone_fvg_poi_current_claim_repair_decisions.jsonl"
)
DEFAULT_SWING_PROTECTED_REPAIR_DECISIONS = Path(
    "shadow_logs/swing_protected_stop_current_claim_repair_decisions.jsonl"
)
DEFAULT_NAS100_DEPTH_THINNESS_SOURCE_REPAIRS = Path(
    "shadow_logs/nas100_depth_thinness_current_source_repair_decisions.jsonl"
)
DEFAULT_FVG_OB_TRADE_RECORD_BOUNDS_REPAIRS = Path(
    "shadow_logs/fvg_ob_trade_record_bounds_current_repair_decisions.jsonl"
)
DEFAULT_OUTPUT = Path("shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl")

SAME_ENTRY_SCORE_IDS = {
    "LIVE_AI_J46_J49_BASELINE_COMPARATOR",
}
PENDING_LIMIT_STRATEGY_ID = "PENDING_LIMIT_LIFECYCLE"
PREFILL_DELIVERY_STRATEGY_ID = "PREFILL_DELIVERY_REVERSAL_PATH"
ENTRY_OFFSET_050R_STRATEGY_ID = "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER"
MOONSHOT_SELECTED_ACTION_STRATEGY_IDS = {
    str(item.get("strategy_id")) for item in MOONSHOT_SELECTED_ACTION_STRATEGY_REGISTRY
}
LIMIT_PLACED_OUTCOMES = {"LIMIT_PLACED", "ORDER_PLACED", "PENDING_LIMIT"}
OB_BOUNDARY_PROXY_IDS = {
    "V2_STRUCT_OB_BOUNDARY",
    "V2B_OB_BOUNDARY_PROSPECTIVE",
}
CONTEXT_ONLY_IDS = {
    "J46_J49_PORTFOLIO_POLICY",
    "S79_UNIFORM_FN_RISK_POLICY",
}
FVG_REQUIRED_IDS = {
    "V2_STRUCT_FVG_MID_EDGE",
    "V3_FVG_ONLY_RESCUE_RISK_BANK",
}
FVG_OB_CONFLUENCE_ID = "FVG_OB_CONFLUENCE_OB_AFTER_FVG"
STRUCTURAL_LOCK_REQUIRED_IDS = {
    "V2_STRUCT_SWING_PROTECTED",
    "V2_STRUCT_COMPOSITE_ANY",
    "V3_FVG_THEN_OB_TAIL_RISK_BANK",
    "V3_OB_LOCK_PULLBACK_RISK_BANK",
    "V3_OB_LOCK_COST_AWARE_MIN_R",
}
SWING_PROTECTED_STRATEGY_ID = "V2_STRUCT_SWING_PROTECTED"
NAS100_DEPTH_THINNESS_STRATEGY_ID = "NAS100_NQ_DEPTH_THINNESS_DIAGNOSTIC"
CANONICAL_STRUCTURAL_SHARED_PATH_ID = "V2_STRUCT_COMPOSITE_ANY"
DUPLICATE_STRUCTURAL_SHARED_PATH_IDS = {
    "V3_FVG_THEN_OB_TAIL_RISK_BANK",
    "V3_OB_LOCK_PULLBACK_RISK_BANK",
    "V3_OB_LOCK_COST_AWARE_MIN_R",
}
SOURCE_MISSING_STATUSES = {"", "SOURCE_NOT_CAPTURED", "DECISION_TIME_SOURCE_NOT_AVAILABLE"}
FVG_OB_CONFLUENCE_BUCKETS = {
    "both_fvg_and_ob_fire",
    "fvg_only",
    "ob_only",
    "no_poi",
    "disagreement",
}
PENDING_LIFECYCLE_CAPTURE_FIELDS = (
    "pending_horizon_start_utc",
    "pending_horizon_end_utc",
    "cancel_expiry_reason_status",
    "decision_spread_value_source_safe",
    "decision_spread_unit",
    "entry_touch_spread_value_source_safe",
    "entry_touch_spread_unit",
    "terminal_area_touch_status",
    "terminal_area_first_touch_utc",
    "protective_area_touch_status",
    "protective_area_first_touch_utc",
    "event_order_resolution_method",
    "same_tick_same_bar_ambiguity_status",
)
ENTRY_OFFSET_050R_CAPTURE_FIELDS = (
    "tick_replay_status",
    "outcome_status",
    "proxy_r",
    "shifted_entry_price",
    "shifted_target_r",
    "fill_first_touch_utc",
    "terminal_event_utc",
    "source_files",
)
ENTRY_OFFSET_050R_M15_HARD_NO_FILL_MIN_DISTANCE_R = 1.0
ENTRY_OFFSET_050R_CONCENTRATION_GUARDED_BRANCH = (
    "IMPLEMENT_DEFAULT_OFF_ENTRY_OFFSET_050R_CONCENTRATION_GUARDED_CANDIDATE"
)
PREFILL_ENTRY_OFFSET_CONCENTRATION_GUARD_REFERENCE_BRANCH = (
    "MERGE_PREFILL_ENTRY_OFFSET_CONCENTRATION_GUARD_REFERENCE"
)
ENTRY_OFFSET_050R_CLUSTER_GUARDED_IMPLEMENTATION_CANDIDATE = (
    "ENTRY_OFFSET_050R_CLUSTER_GUARDED_DEFAULT_OFF_CHALLENGER"
)
PREFILL_ENTRY_OFFSET_CLUSTER_REFERENCE_CANDIDATE = (
    "PREFILL_TP_AFTER_FILL_CONTEXT_MERGED_TO_ENTRY_OFFSET_CLUSTER_GUARD"
)
ENTRY_OFFSET_050R_CURRENT_EVIDENCE = {
    "artifact": "MAIN_ORCH24_ACTION_AFTER_ENTRY_OFFSET_CONCENTRATION_GUARD",
    "owner_rows": 13,
    "owner_proxy_r_sum": 8.66977687,
    "effective_cluster_count": 3,
    "largest_cluster_key": "US30_cash|2026-05-08",
    "largest_cluster_rows": 11,
    "largest_cluster_proxy_r_sum": 7.33544301,
    "largest_cluster_row_share": 0.84615385,
    "largest_cluster_proxy_r_share": 0.84609363,
    "prefill_reference_rows": 13,
    "prefill_reference_proxy_r_sum": 8.66977687,
    "no_fill_control_rows": 168,
}
DEPTH_THINNESS_FEATURE_FIELDS = (
    "pre60_median_total_depth10",
    "pre60_median_depth10_imbalance",
    "event15_median_total_depth10",
    "event15_thin_depth10_rate",
    "event15_median_depth10_imbalance",
    "event15_median_near_far_ratio",
    "event15_median_max_bid_wall",
    "event15_median_max_ask_wall",
    "event15_sample_count",
)


def _candidate_symbol_date_cluster_key(candidate_id: str) -> str:
    marker = "_20"
    position = candidate_id.find(marker)
    if position < 0 or len(candidate_id) < position + 11:
        return "UNKNOWN|UNKNOWN"
    return f"{candidate_id[:position]}|{candidate_id[position + 1:position + 11]}"


def _entry_offset_050r_concentration_guard_extra(
    *,
    candidate: dict[str, Any],
    status: str,
    subtype: str,
    proxy_r: float | None,
    proxy_reference_status: str,
) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_id") or "")
    cluster_key = _candidate_symbol_date_cluster_key(candidate_id)
    largest_key = str(ENTRY_OFFSET_050R_CURRENT_EVIDENCE["largest_cluster_key"])
    largest_cluster = cluster_key == largest_key
    useful_mechanism = (
        "Spread-aware 0.50R entry shift and prefill TP-after-fill timing remain useful as a "
        "default-off entry-offset component, but current evidence requires symbol-date cluster control."
    )
    return {
        "entry_offset_concentration_guard_status": status,
        "entry_offset_original_subtype": subtype,
        "entry_offset_concentration_cluster_key": cluster_key,
        "entry_offset_concentration_effective_cluster_count": ENTRY_OFFSET_050R_CURRENT_EVIDENCE[
            "effective_cluster_count"
        ],
        "entry_offset_largest_cluster_key": largest_key,
        "entry_offset_largest_cluster_guard_required": largest_cluster,
        "entry_offset_current_evidence_owner_rows": ENTRY_OFFSET_050R_CURRENT_EVIDENCE["owner_rows"],
        "entry_offset_current_evidence_proxy_r_sum": ENTRY_OFFSET_050R_CURRENT_EVIDENCE["owner_proxy_r_sum"],
        "entry_offset_largest_cluster_row_count": ENTRY_OFFSET_050R_CURRENT_EVIDENCE[
            "largest_cluster_rows"
        ],
        "entry_offset_largest_cluster_proxy_r_sum": ENTRY_OFFSET_050R_CURRENT_EVIDENCE[
            "largest_cluster_proxy_r_sum"
        ],
        "entry_offset_largest_cluster_row_share": ENTRY_OFFSET_050R_CURRENT_EVIDENCE[
            "largest_cluster_row_share"
        ],
        "entry_offset_largest_cluster_proxy_r_share": ENTRY_OFFSET_050R_CURRENT_EVIDENCE[
            "largest_cluster_proxy_r_share"
        ],
        "entry_offset_proxy_owner_strategy_id": ENTRY_OFFSET_050R_STRATEGY_ID,
        "entry_offset_proxy_owner_candidate_id": candidate_id,
        "entry_offset_proxy_r_reference": proxy_r,
        "entry_offset_proxy_reference_status": proxy_reference_status,
        "entry_offset_cluster_guard_decision": (
            "CLUSTER_GUARD_REQUIRED_BECAUSE_CURRENT_US30_CASH_2026_05_08_CLUSTER_OWNS_11_OF_13_POSITIVE_ROWS"
            if largest_cluster
            else "FUTURE_OR_DIVERSIFYING_SUPPORT_ROW_REQUIRES_CLUSTER_CAPPED_REPLAY_BEFORE_IMPLEMENTATION"
        ),
        "claim_decision_scope": "DEFAULT_OFF_DISCOVERY_ONLY_CLUSTER_GUARDED",
        "underlying_intelligence_preserved": True,
        "opportunity_preservation_status": "ENTRY_OFFSET_CONCENTRATION_GUARD_OPPORTUNITY_PRESERVED",
        "opportunity_proxy_r_reference": proxy_r,
        "opportunity_proxy_reference_status": proxy_reference_status,
        "opportunity_not_independently_countable_reason": (
            "Proxy R is counted only on the entry-offset owner row and is not duplicated by prefill "
            "references; the implementation remains default-off because current evidence is concentrated "
            "in one US30_cash symbol-date cluster."
        ),
        "opportunity_useful_mechanism": useful_mechanism,
        "opportunity_downstream_paths": [
            "entry-offset merge",
            "redesign",
            "avoid/inverse",
            "context feature",
            "source requirement",
            "tighter target",
            "shorter horizon",
            "broader system component",
        ],
        "missed_opportunity_audit": {
            "kill_scope": "NOT_KILLED_DEFAULT_OFF_OWNER_CLUSTER_GUARDED",
            "current_claim": "ENTRY_OFFSET_050R_SPREAD_AWARE_SHIFT_FILL_OR_PREFILL_TP_AFTER_FILL",
            "unsupported_reason": (
                "POSITIVE_PROXY_CLUSTER_CONCENTRATED_IN_US30_CASH_2026_05_08_SO_NOT_STANDALONE_PROMOTABLE"
            ),
            "what_was_tried": "M15_OR_TICK_REPAIRED_ENTRY_OFFSET_050R_REPLAY_WITH_PREFILL_OWNER_MERGE",
            "what_could_make_it_work": (
                "DUPLICATE_AWARE_REPLAY_WITH_SYMBOL_DATE_CLUSTER_CAP_AND_OUT_OF_CLUSTER_SUPPORT"
            ),
            "preserve_as": "ENTRY_OFFSET_050R_CLUSTER_GUARDED_DEFAULT_OFF_CANDIDATE",
            "next_route": (
                "REPLAY_ENTRY_OFFSET_050R_WITH_SYMBOL_DATE_CLUSTER_CAP_FAR_NEAR_SPLIT_COST_AND_FILL_REPAIR"
            ),
            "path_status": {
                "proxy_r_reference": proxy_r,
                "proxy_reference_status": proxy_reference_status,
                "cluster_key": cluster_key,
                "current_evidence_artifact": ENTRY_OFFSET_050R_CURRENT_EVIDENCE["artifact"],
            },
        },
    }


def _fvg_scorer_blocker_extra(*, captured_metadata: bool) -> dict[str, str]:
    if captured_metadata:
        return {
            "branch_decision": "IMPLEMENTATION_CANDIDATE_DEFAULT_OFF_FVG_SCORER",
            "decision_evidence": "CAPTURED_FVG_METADATA_PRESENT_BUT_STANDALONE_FVG_SCORER_NOT_IMPLEMENTED",
            "scoring_boundary": "CAPTURED_FVG_LOCK_METADATA_NO_STANDALONE_FVG_ENTRY_SCORER",
            "implementation_candidate": "BUILD_DEFAULT_OFF_FVG_ENTRY_LOCK_SCORER_WITH_ENTRY_STOP_TARGET_CONTRACT",
        }
    return {
        "branch_decision": "SOURCE_CAPTURE_REQUIRED_FOR_FVG_SCORER",
        "decision_evidence": "MISSING_STANDALONE_FVG_ENTRY_OR_LOCK_METADATA_FOR_FVG_SCORER",
        "scoring_boundary": "NO_FVG_PROXY_R_WITHOUT_ENTRY_LOCK_AND_POST_LOCK_PATH_METADATA",
        "implementation_candidate": "CAPTURE_STANDALONE_FVG_ENTRY_LOCK_AND_POST_LOCK_REENTRY_FIELDS",
    }


def _current_claim_only_preservation_extra(
    *,
    current_claim: str,
    unsupported_reason: str,
    what_was_tried: str,
    what_could_make_it_work: str,
    preserve_as: str,
    next_route: str,
    path_status: dict[str, Any] | None = None,
    current_claim_proxy_counted: bool = False,
) -> dict[str, Any]:
    audit = {
        "kill_scope": "CURRENT_CLAIM_ONLY",
        "current_claim": current_claim,
        "unsupported_reason": unsupported_reason,
        "what_was_tried": what_was_tried,
        "what_could_make_it_work": what_could_make_it_work,
        "preserve_as": preserve_as,
        "next_route": next_route,
    }
    out: dict[str, Any] = {
        "claim_decision_scope": "CURRENT_STRATEGY_CLAIM_ONLY_UNDERLYING_INTELLIGENCE_PRESERVED",
        "underlying_intelligence_preserved": True,
        "missed_opportunity_audit": audit,
        "current_claim_proxy_counted": current_claim_proxy_counted,
    }
    if path_status is not None:
        out.update(
            {
                "preserved_candidate_path_proxy_r": path_status.get("strategy_proxy_r"),
                "preserved_candidate_path_outcome_source": path_status.get("outcome_source"),
                "preserved_candidate_path_outcome_status": path_status.get("outcome_status"),
            }
        )
    return out


def _numeric_reference_from_row(row: dict[str, Any]) -> float | None:
    for field in (
        "strategy_proxy_r",
        "linked_entry_offset_050r_proxy_r",
        "linked_entry_offset_after_proxy_r",
        "linked_entry_offset_selected_proxy_r",
        "preserved_candidate_path_proxy_r",
    ):
        value = row.get(field)
        if value is None or isinstance(value, bool):
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if number == number and number not in (float("inf"), float("-inf")):
            return number
    return None


def _opportunity_paths_from_text(text: str) -> list[str]:
    lowered = text.lower()
    paths: list[str] = []
    if "entry-offset" in lowered or "entry_offset" in lowered:
        paths.append("entry-offset merge")
    if "redesign" in lowered or "retest" in lowered or "offset" in lowered:
        paths.append("redesign")
    if "avoid" in lowered or "inverse" in lowered or "adverse" in lowered:
        paths.append("avoid/inverse")
    if "context" in lowered or "feature" in lowered:
        paths.append("context feature")
    if "source" in lowered or "capture" in lowered or "repair" in lowered or "tick" in lowered:
        paths.append("source requirement")
    if "tighter" in lowered or "target" in lowered:
        paths.append("tighter target")
    if "shorter" in lowered or "horizon" in lowered:
        paths.append("shorter horizon")
    paths.append("broader system component")
    return list(dict.fromkeys(paths))


def _opportunity_reason_for_row(row: dict[str, Any]) -> str:
    branch = str(row.get("branch_decision") or "")
    upper = branch.upper()
    if row.get("prefill_proxy_counting_decision") == "PROXY_R_OWNED_BY_ENTRY_OFFSET_050R_NOT_DUPLICATED":
        return (
            "Prefill metadata references entry-offset proxy evidence; it is not independently countable "
            "as standalone prefill R without duplicating the entry-offset scorer owner."
        )
    if upper.startswith("KILL_ROW_NOT_"):
        return "Row is outside the current branch denominator; only this current claim is rejected."
    if "DUPLICATE" in upper:
        return "Current row duplicates another owner/shared proxy path and is not independently countable."
    if "SOURCE" in upper or "REPAIR" in upper:
        return "Current row requires source/cost/fill/order repair before an independent scorer claim."
    if upper.startswith("KILL"):
        return "Current claim is contradicted by available path/source evidence; underlying mechanism is preserved."
    if upper.startswith("REDESIGN"):
        return "Current standalone claim is not independently countable without redesign or context isolation."
    return "Current row is preserved as scoped opportunity intelligence, not an independent standalone claim."


def _complete_opportunity_preservation_fields(row: dict[str, Any]) -> None:
    branch = str(row.get("branch_decision") or "")
    branch_upper = branch.upper()
    audit = row.get("missed_opportunity_audit")
    required = (
        isinstance(audit, dict)
        or row.get("underlying_intelligence_preserved") is True
        or row.get("prefill_proxy_counting_decision") == "PROXY_R_OWNED_BY_ENTRY_OFFSET_050R_NOT_DUPLICATED"
        or branch_upper.startswith(("KILL", "REDESIGN", "SOURCE", "PRESERVE"))
    )
    if not required:
        return

    if not isinstance(audit, dict):
        audit = {}
    proxy_reference = _numeric_reference_from_row(row)
    preserve_as = str(
        audit.get("preserve_as")
        or row.get("implementation_candidate")
        or row.get("strategy_status")
        or "CURRENT_CLAIM_SCOPE_ONLY_REDESIGN_OR_CONTEXT_COMPONENT"
    )
    next_route = str(
        audit.get("next_route")
        or row.get("implementation_candidate")
        or "CONSUME_PRESERVED_ROW_INTELLIGENCE_IN_APPLICABLE_BRANCH_OWNER_OR_REDESIGN"
    )
    row["underlying_intelligence_preserved"] = True
    row.setdefault("opportunity_preservation_status", "SCORER_ROW_OPPORTUNITY_PRESERVED")
    row.setdefault(
        "opportunity_owner_row_id",
        "|".join(
            str(part or "")
            for part in (
                row.get("candidate_id"),
                row.get("strategy_id"),
                row.get("asof_latest_candle_utc"),
            )
        ),
    )
    row.setdefault("opportunity_owner_source_artifact", str(row.get("source_file") or DEFAULT_OUTPUT))
    row.setdefault("opportunity_proxy_r_reference", proxy_reference)
    row.setdefault(
        "opportunity_proxy_reference_status",
        "REFERENCE_ONLY_NOT_COUNTED_DUPLICATE_ENTRY_OFFSET_OWNER"
        if row.get("prefill_proxy_counting_decision") == "PROXY_R_OWNED_BY_ENTRY_OFFSET_050R_NOT_DUPLICATED"
        else (
            "CURRENT_ROW_PROXY_REFERENCE"
            if proxy_reference is not None
            else "NO_CURRENT_NUMERIC_PROXY_REFERENCE"
        ),
    )
    row.setdefault("opportunity_not_independently_countable_reason", _opportunity_reason_for_row(row))
    row.setdefault("opportunity_useful_mechanism", preserve_as)
    row.setdefault(
        "opportunity_downstream_paths",
        _opportunity_paths_from_text(" ".join([branch, preserve_as, next_route])),
    )
    audit.setdefault(
        "kill_scope",
        "CURRENT_CLAIM_ONLY" if branch_upper.startswith("KILL") else "NOT_KILLED_REDESIGN_OR_REQUIREMENT",
    )
    audit.setdefault("current_claim", branch)
    audit.setdefault("unsupported_reason", _opportunity_reason_for_row(row))
    audit.setdefault("what_was_tried", str(row.get("decision_evidence") or row.get("status_reason") or "SCORER_BRANCH_EVALUATION"))
    audit.setdefault("what_could_make_it_work", next_route)
    audit.setdefault("preserve_as", preserve_as)
    audit.setdefault("next_route", next_route)
    audit.setdefault(
        "path_status",
        {
            "proxy_r_reference": proxy_reference,
            "proxy_reference_status": row.get("opportunity_proxy_reference_status"),
            "source_artifact": row.get("opportunity_owner_source_artifact"),
        },
    )
    row["missed_opportunity_audit"] = audit


def _structural_scorer_blocker_extra(*, captured_metadata: bool) -> dict[str, str]:
    if captured_metadata:
        return {
            "branch_decision": "IMPLEMENTATION_CANDIDATE_DEFAULT_OFF_STRUCTURAL_LOCK_SCORER",
            "decision_evidence": "CAPTURED_STRUCTURAL_LOCK_METADATA_PRESENT_BUT_ALTERNATE_SCORER_NOT_IMPLEMENTED",
            "scoring_boundary": "CAPTURED_STRUCTURAL_LOCK_METADATA_NO_ALTERNATE_ENTRY_SCORER",
            "implementation_candidate": "BUILD_DEFAULT_OFF_STRUCTURAL_LOCK_REENTRY_SCORER_WITH_LOCK_REENTRY_COST_CONTRACT",
        }
    return {
        "branch_decision": "SOURCE_CAPTURE_REQUIRED_FOR_STRUCTURAL_LOCK_SCORER",
        "decision_evidence": "MISSING_STRUCTURAL_LOCK_REENTRY_OR_COST_METADATA_FOR_ALTERNATE_SCORER",
        "scoring_boundary": "NO_STRUCTURAL_PROXY_R_WITHOUT_LOCK_REENTRY_AND_COST_METADATA",
        "implementation_candidate": "CAPTURE_STRUCTURAL_LOCK_REENTRY_AND_COST_AWARE_MIN_R_FIELDS",
    }


def _field_capture_status(value: Any, derivation: str | None = None) -> str:
    if derivation and derivation.startswith("NOT_APPLICABLE_"):
        return derivation
    if value in (None, "", [], {}):
        return "SOURCE_NOT_CAPTURED_IN_CURRENT_ROW"
    if derivation:
        return derivation
    return "SOURCE_CAPTURED"


def _source_value_present(value: Any) -> bool:
    return value not in (None, "", [], {})


def _moonshot_selected_action_status(
    strategy: dict[str, Any],
    candidate: dict[str, Any],
    path_row: dict[str, Any],
    source_capture_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    required_fields = [
        str(field) for field in strategy.get("source_capture_required_fields") or []
    ]
    source_capture_fields = {}
    if isinstance(source_capture_row, dict) and isinstance(source_capture_row.get("source_capture_fields"), dict):
        source_capture_fields = source_capture_row["source_capture_fields"]
    missing_fields = [
        field
        for field in required_fields
        if not _source_value_present(candidate.get(field))
        and not _source_value_present(path_row.get(field))
        and not _source_value_present(source_capture_fields.get(field))
    ]
    source_ready = not missing_fields and bool(required_fields)
    if source_ready:
        strategy_status = "MOONSHOT_SELECTED_ACTION_SOURCE_READY_SCORER_NOT_IMPLEMENTED"
        score_status = "SOURCE_READY_DEFAULT_OFF_SCORER_NOT_IMPLEMENTED"
        reason = (
            "Moonshot selected-action source fields are present, but the default-off scorer "
            "has not been implemented for this strategy id."
        )
    else:
        strategy_status = "WAITING_FOR_MOONSHOT_SELECTED_ACTION_SOURCE_CAPTURE"
        score_status = "WAITING_SOURCE"
        reason = (
            "Moonshot selected-action evidence is default-off only; current candidate/path rows "
            "do not carry the required source/control fields for replay scoring."
        )
    return {
        "strategy_status": strategy_status,
        "score_status": score_status,
        "outcome_status": "NOT_SCORED",
        "reason": reason,
        "extra": {
            "branch_decision": strategy.get("branch_decision"),
            "decision_evidence": strategy.get("decision_evidence"),
            "implementation_candidate": strategy.get("implementation_candidate"),
            "scoring_boundary": (
                "MOONSHOT_SELECTED_ACTION_SOURCE_READY_NEEDS_DEFAULT_OFF_SCORER_IMPLEMENTATION"
                if source_ready
                else "NO_MOONSHOT_SELECTED_ACTION_PROXY_R_WITHOUT_REQUIRED_SOURCE_CAPTURE"
            ),
            "source_capture_required_fields": required_fields,
            "source_capture_missing_fields": missing_fields,
            "source_capture_ready": source_ready,
            "moonshot_selected_action_source_capture_status": (
                source_capture_row.get("source_capture_status")
                if isinstance(source_capture_row, dict)
                else "SOURCE_CAPTURE_ROW_NOT_FOUND"
            ),
            "moonshot_selected_action_source_capture_created_at_utc": (
                source_capture_row.get("created_at_utc")
                if isinstance(source_capture_row, dict)
                else None
            ),
            "claim_decision_scope": (
                "DEFAULT_OFF_MOONSHOT_SELECTED_ACTION_ONLY_NO_LIVE_BEHAVIOR"
            ),
            "underlying_intelligence_preserved": True,
            "missed_opportunity_audit": {
                "kill_scope": "NO_KILL_SOURCE_CAPTURE_OR_SCORER_REQUIRED",
                "current_claim": str(strategy.get("strategy_id") or ""),
                "unsupported_reason": (
                    "source fields present but scorer implementation is still default-off"
                    if source_ready
                    else "current live candidate/path rows do not carry the selected-action source fields"
                ),
                "what_was_tried": "registered selected moonshot action as a forward shadow strategy snapshot",
                "what_could_make_it_work": (
                    "capture required fields and implement the default-off scorer for this selected action"
                ),
                "preserve_as": "default_off_implementation_candidate_or_source_requirement",
                "next_route": str(strategy.get("implementation_candidate") or ""),
            },
            "current_claim_proxy_counted": False,
        },
    }


def _touch_status(hit: Any) -> str | None:
    if hit is True:
        return "TOUCHED"
    if hit is False:
        return "NOT_TOUCHED_BY_ASOF"
    return None


def _pending_cancel_reason_status(lifecycle: dict[str, Any]) -> str | None:
    state = str(lifecycle.get("intent_after_check") or "")
    label = str(lifecycle.get("fill_no_fill_label") or "")
    if not state and not label:
        return None
    if state.startswith("cancelled") or state in {"expired_48h", "manual_or_system_cancelled"}:
        return state or label
    if label.startswith("no_fill_cancelled") or label.startswith("no_fill_expired"):
        return label
    if state == "still_pending_no_trigger":
        return "NOT_CANCELLED_OR_EXPIRED_STILL_PENDING"
    if state == "order_send_success_filled":
        return "NOT_CANCELLED_FILLED"
    return "NOT_CANCELLED_OR_EXPIRED"


def _pending_event_order_resolution(path_row: dict[str, Any] | None, ltf_row: dict[str, Any] | None) -> tuple[str | None, str | None]:
    path_row = path_row or {}
    ltf_row = ltf_row or {}
    terminal_status = str(ltf_row.get("terminal_outcome_status") or "")
    if terminal_status:
        ambiguous = "AMBIGUOUS" if "AMBIGUOUS" in terminal_status else "NOT_AMBIGUOUS"
        return "RESOLVED_FROM_CANDIDATE_LTF_PATH_ORDER", ambiguous
    if path_row.get("hit_tp1") is True and path_row.get("hit_sl") is True:
        return "M15_PATH_AMBIGUOUS_LTF_NOT_AVAILABLE", "AMBIGUOUS_M15_SAME_BAR_OR_ORDER_UNKNOWN"
    if path_row:
        return "M15_PATH_SINGLE_OR_NO_TERMINAL_EVENT", "NOT_AMBIGUOUS_ON_M15_PATH"
    return None, None


def _pending_no_entry_touch(lifecycle: dict[str, Any]) -> bool:
    state = str(lifecycle.get("intent_after_check") or "")
    label = str(lifecycle.get("fill_no_fill_label") or "")
    if lifecycle.get("trigger_condition_met") is False:
        return True
    if "without_entry_touch" in label:
        return True
    return state in {
        "still_pending_no_trigger",
        "cancelled_target_reached_without_fill",
        "cancelled_wrong_side",
        "cancelled_sl_too_close",
        "manual_or_system_cancelled",
        "expired_48h",
    }


def _pending_entry_touch_spread(lifecycle: dict[str, Any]) -> tuple[Any, str] | None:
    spread = lifecycle.get("entry_touch_spread_value_source_safe")
    if spread not in (None, "", [], {}):
        return spread, str(lifecycle.get("entry_touch_spread_unit") or "spread_cents")
    legacy_spread = lifecycle.get("spread")
    if legacy_spread not in (None, "", [], {}) and not _pending_no_entry_touch(lifecycle):
        return legacy_spread, "spread_cents"
    return None


def _pending_decision_spread(
    lifecycle: dict[str, Any],
    nofill_forward_capture_row: dict[str, Any] | None = None,
    tick_spread_reconstruction_row: dict[str, Any] | None = None,
) -> tuple[Any, Any, str, dict[str, Any]]:
    spread = lifecycle.get("decision_spread_value_source_safe")
    if spread not in (None, "", [], {}):
        return (
            spread,
            str(lifecycle.get("decision_spread_unit") or "spread_cents"),
            "CAPTURED_IN_PENDING_LIFECYCLE_ROW",
            {},
        )
    if nofill_forward_capture_row:
        forward_spread = nofill_forward_capture_row.get("decision_spread_value_source_safe")
        forward_status = str(nofill_forward_capture_row.get("decision_spread_status") or "")
        if forward_spread not in (None, "", [], {}) and forward_status == "QUOTE_SNAPSHOT_CAPTURED_SOURCE_SAFE":
            return (
                forward_spread,
                str(nofill_forward_capture_row.get("decision_spread_unit") or "spread_cents"),
                "DERIVED_FROM_NOFILL_FORWARD_SOURCE_CAPTURE_DECISION_SPREAD",
                {
                    "pending_lifecycle_decision_spread_reconstruction_source": "nofill_forward_source_capture",
                    "pending_lifecycle_decision_spread_reconstruction_source_created_at_utc": (
                        nofill_forward_capture_row.get("created_at_utc")
                    ),
                    "pending_lifecycle_decision_spread_reconstruction_source_status": forward_status,
                },
            )
    if tick_spread_reconstruction_row:
        tick_spread = tick_spread_reconstruction_row.get("decision_spread_value_source_safe")
        tick_status = str(tick_spread_reconstruction_row.get("decision_spread_status") or "")
        if (
            tick_spread not in (None, "", [], {})
            and tick_status == "TICK_PARQUET_AT_OR_BEFORE_DECISION_WITHIN_2S_SOURCE_SAFE"
        ):
            return (
                tick_spread,
                str(tick_spread_reconstruction_row.get("decision_spread_unit") or "spread_cents"),
                "DERIVED_FROM_TICK_PARQUET_AT_OR_BEFORE_DECISION_SPREAD",
                {
                    "pending_lifecycle_decision_spread_reconstruction_source": "tick_parquet_decision_time",
                    "pending_lifecycle_decision_spread_reconstruction_source_created_at_utc": (
                        tick_spread_reconstruction_row.get("created_at_utc")
                    ),
                    "pending_lifecycle_decision_spread_reconstruction_source_status": tick_status,
                    "pending_lifecycle_decision_spread_reconstruction_tick_ts_utc": (
                        tick_spread_reconstruction_row.get("tick_ts_utc")
                    ),
                    "pending_lifecycle_decision_spread_reconstruction_tick_offset_seconds": (
                        tick_spread_reconstruction_row.get("tick_offset_seconds")
                    ),
                    "pending_lifecycle_decision_spread_reconstruction_tick_source_path": (
                        tick_spread_reconstruction_row.get("tick_source_path")
                    ),
                    "pending_lifecycle_decision_spread_reconstruction_tick_source_sha256": (
                        tick_spread_reconstruction_row.get("tick_source_sha256")
                    ),
                },
            )
    legacy_spread = lifecycle.get("spread")
    if legacy_spread not in (None, "", [], {}):
        return (
            legacy_spread,
            "spread_cents",
            "DERIVED_FROM_PENDING_LIFECYCLE_LEGACY_SPREAD_AS_DECISION_SPREAD_PROXY",
            {
                "pending_lifecycle_decision_spread_reconstruction_source": "pending_lifecycle_legacy_spread",
                "pending_lifecycle_decision_spread_reconstruction_source_created_at_utc": lifecycle.get(
                    "timestamp_utc"
                ),
                "pending_lifecycle_decision_spread_reconstruction_source_status": "LEGACY_SPREAD_FIELD_PRESENT",
            },
        )
    return None, None, "", {}


def _pending_lifecycle_capture_extra(
    lifecycle: dict[str, Any],
    path_row: dict[str, Any] | None = None,
    ltf_row: dict[str, Any] | None = None,
    nofill_forward_capture_row: dict[str, Any] | None = None,
    tick_spread_reconstruction_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    path_row = path_row or {}
    ltf_row = ltf_row or {}
    derived: dict[str, tuple[Any, str]] = {}
    if not lifecycle.get("pending_horizon_start_utc"):
        value = lifecycle.get("timestamp_utc") or path_row.get("decision_time_utc")
        if value:
            derived["pending_horizon_start_utc"] = (value, "DERIVED_FROM_PENDING_LIFECYCLE_OR_PATH_TIME")
    if not lifecycle.get("pending_horizon_end_utc"):
        value = (
            lifecycle.get("checked_candle_time_utc")
            or lifecycle.get("asof_cutoff_utc")
            or path_row.get("asof_latest_candle_utc")
        )
        if value:
            derived["pending_horizon_end_utc"] = (value, "DERIVED_FROM_PENDING_LIFECYCLE_OR_PATH_ASOF")
    if not lifecycle.get("cancel_expiry_reason_status"):
        value = _pending_cancel_reason_status(lifecycle)
        if value:
            derived["cancel_expiry_reason_status"] = (value, "DERIVED_FROM_PENDING_LIFECYCLE_STATE")
    if not lifecycle.get("terminal_area_touch_status"):
        value = _touch_status(path_row.get("hit_tp1"))
        value_source = "DERIVED_FROM_CANDIDATE_PATH_FOLLOW"
        if value is None and ltf_row.get("tp1_first_touch_utc"):
            value = "TOUCHED"
            value_source = "DERIVED_FROM_CANDIDATE_LTF_PATH_ORDER"
        if value:
            derived["terminal_area_touch_status"] = (value, value_source)
    if not lifecycle.get("terminal_area_first_touch_utc") and path_row.get("tp1_first_touch_utc"):
        derived["terminal_area_first_touch_utc"] = (
            path_row.get("tp1_first_touch_utc"),
            "DERIVED_FROM_CANDIDATE_PATH_FOLLOW",
        )
    if (
        not lifecycle.get("terminal_area_first_touch_utc")
        and "terminal_area_first_touch_utc" not in derived
        and ltf_row.get("tp1_first_touch_utc")
    ):
        derived["terminal_area_first_touch_utc"] = (
            ltf_row.get("tp1_first_touch_utc"),
            "DERIVED_FROM_CANDIDATE_LTF_PATH_ORDER",
        )
    terminal_touch = lifecycle.get("terminal_area_touch_status") or derived.get(
        "terminal_area_touch_status", (None, None)
    )[0]
    if (
        not lifecycle.get("terminal_area_first_touch_utc")
        and "terminal_area_first_touch_utc" not in derived
        and terminal_touch == "NOT_TOUCHED_BY_ASOF"
    ):
        derived["terminal_area_first_touch_utc"] = (
            None,
            "NOT_APPLICABLE_TERMINAL_AREA_NOT_TOUCHED_BY_ASOF",
        )
    if not lifecycle.get("protective_area_touch_status"):
        value = _touch_status(path_row.get("hit_sl"))
        value_source = "DERIVED_FROM_CANDIDATE_PATH_FOLLOW"
        if value is None and ltf_row.get("sl_first_touch_utc"):
            value = "TOUCHED"
            value_source = "DERIVED_FROM_CANDIDATE_LTF_PATH_ORDER"
        if value:
            derived["protective_area_touch_status"] = (value, value_source)
    if not lifecycle.get("protective_area_first_touch_utc") and path_row.get("sl_first_touch_utc"):
        derived["protective_area_first_touch_utc"] = (
            path_row.get("sl_first_touch_utc"),
            "DERIVED_FROM_CANDIDATE_PATH_FOLLOW",
        )
    if (
        not lifecycle.get("protective_area_first_touch_utc")
        and "protective_area_first_touch_utc" not in derived
        and ltf_row.get("sl_first_touch_utc")
    ):
        derived["protective_area_first_touch_utc"] = (
            ltf_row.get("sl_first_touch_utc"),
            "DERIVED_FROM_CANDIDATE_LTF_PATH_ORDER",
        )
    protective_touch = lifecycle.get("protective_area_touch_status") or derived.get(
        "protective_area_touch_status", (None, None)
    )[0]
    if (
        not lifecycle.get("protective_area_first_touch_utc")
        and "protective_area_first_touch_utc" not in derived
        and protective_touch == "NOT_TOUCHED_BY_ASOF"
    ):
        derived["protective_area_first_touch_utc"] = (
            None,
            "NOT_APPLICABLE_PROTECTIVE_AREA_NOT_TOUCHED_BY_ASOF",
        )
    decision_spread_value, decision_spread_unit, decision_spread_derivation, decision_spread_extra = (
        _pending_decision_spread(lifecycle, nofill_forward_capture_row, tick_spread_reconstruction_row)
    )
    if (
        not lifecycle.get("decision_spread_value_source_safe")
        and decision_spread_value not in (None, "", [], {})
        and decision_spread_derivation
    ):
        out_extra = decision_spread_extra
        derived["decision_spread_value_source_safe"] = (
            decision_spread_value,
            decision_spread_derivation,
        )
        if not lifecycle.get("decision_spread_unit"):
            derived["decision_spread_unit"] = (
                decision_spread_unit,
                decision_spread_derivation,
            )
    elif not lifecycle.get("decision_spread_value_source_safe") and _pending_no_entry_touch(lifecycle):
        derived["decision_spread_value_source_safe"] = (
            None,
            "NOT_APPLICABLE_NO_ENTRY_TOUCH_NO_SPREAD_COST",
        )
        if not lifecycle.get("decision_spread_unit"):
            derived["decision_spread_unit"] = (
                None,
                "NOT_APPLICABLE_NO_ENTRY_TOUCH_NO_SPREAD_COST",
            )
        out_extra = {}
    else:
        out_extra = {}
    entry_touch_spread = _pending_entry_touch_spread(lifecycle)
    if not lifecycle.get("entry_touch_spread_value_source_safe") and entry_touch_spread:
        spread_value, spread_unit = entry_touch_spread
        derived["entry_touch_spread_value_source_safe"] = (
            spread_value,
            "DERIVED_FROM_PENDING_LIFECYCLE_LEGACY_SPREAD_AT_ENTRY_TOUCH",
        )
        if not lifecycle.get("entry_touch_spread_unit"):
            derived["entry_touch_spread_unit"] = (
                spread_unit,
                "DERIVED_FROM_PENDING_LIFECYCLE_LEGACY_SPREAD_AT_ENTRY_TOUCH",
            )
    elif not lifecycle.get("entry_touch_spread_value_source_safe") and _pending_no_entry_touch(lifecycle):
        derived["entry_touch_spread_value_source_safe"] = (
            None,
            "NOT_APPLICABLE_NO_ENTRY_TOUCH_BY_ASOF",
        )
        if not lifecycle.get("entry_touch_spread_unit"):
            derived["entry_touch_spread_unit"] = (
                None,
                "NOT_APPLICABLE_NO_ENTRY_TOUCH_BY_ASOF",
            )
    event_resolution, ambiguity = _pending_event_order_resolution(path_row, ltf_row)
    if not lifecycle.get("event_order_resolution_method") and event_resolution:
        derived["event_order_resolution_method"] = (
            event_resolution,
            "DERIVED_FROM_CANDIDATE_PATH_OR_LTF_ORDER",
        )
    if not lifecycle.get("same_tick_same_bar_ambiguity_status") and ambiguity:
        derived["same_tick_same_bar_ambiguity_status"] = (
            ambiguity,
            "DERIVED_FROM_CANDIDATE_PATH_OR_LTF_ORDER",
        )

    out: dict[str, Any] = {
        "pending_lifecycle_source_capture_contract": "pending_limit_lifecycle_v1_source_capture_fields",
        **out_extra,
    }
    statuses: dict[str, str] = {}
    derivations: dict[str, str] = {}
    for field in PENDING_LIFECYCLE_CAPTURE_FIELDS:
        value = lifecycle.get(field)
        derivation = None
        if value in (None, "", [], {}) and field in derived:
            value, derivation = derived[field]
            derivations[field] = derivation
        out[f"pending_lifecycle_{field}"] = value
        statuses[field] = _field_capture_status(value, derivation)
    out["pending_lifecycle_source_capture_statuses"] = statuses
    out["pending_lifecycle_source_capture_derivations"] = derivations
    out["pending_lifecycle_source_capture_complete"] = all(
        status != "SOURCE_NOT_CAPTURED_IN_CURRENT_ROW" for status in statuses.values()
    )
    return out


def _entry_offset_050r_extra(path_row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "entry_offset_050r_source_capture_contract": "entry_offset_050r_spread_aware_tick_replay_v1",
    }
    statuses: dict[str, str] = {}
    for field in ENTRY_OFFSET_050R_CAPTURE_FIELDS:
        value = path_row.get(f"entry_offset_050r_{field}")
        out[f"entry_offset_050r_{field}"] = value
        statuses[field] = _field_capture_status(value)
    out["entry_offset_050r_source_capture_statuses"] = statuses
    out["entry_offset_050r_source_capture_complete"] = all(
        status != "SOURCE_NOT_CAPTURED_IN_CURRENT_ROW" for status in statuses.values()
    )
    return out


def _entry_offset_050r_m15_hard_no_fill_proof(redesign: dict[str, Any]) -> bool:
    """Allow M15 range proof only to kill obvious no-fill rows, never to infer fills."""
    bucket = str(redesign.get("entry_retest_redesign_bucket") or "")
    nearest_distance_r = _safe_float(redesign.get("nearest_distance_to_entry_r"))
    return (
        bucket == "FAR_MISS_RETEST_REDESIGN_CONTROL_QUEUE"
        and nearest_distance_r is not None
        and nearest_distance_r >= ENTRY_OFFSET_050R_M15_HARD_NO_FILL_MIN_DISTANCE_R
    )


def _entry_offset_050r_strategy_status(
    candidate: dict[str, Any],
    path_row: dict[str, Any],
) -> dict[str, Any]:
    redesign = entry_retest_redesign_context(candidate, path_row)
    bucket = str(redesign.get("entry_retest_redesign_bucket") or "")
    capture_extra = _entry_offset_050r_extra(path_row)
    outcome = str(path_row.get("entry_offset_050r_outcome_status") or "")
    tick_status = str(path_row.get("entry_offset_050r_tick_replay_status") or "")
    proxy_r = _safe_float(path_row.get("entry_offset_050r_proxy_r"))
    if bucket == "NOT_A_NO_FILL_TP1_ENTRY_REDESIGN_ROW":
        return {
            "strategy_status": "NOT_APPLICABLE_NOT_ENTRY_REDESIGN_DENOMINATOR",
            "score_status": "NOT_APPLICABLE",
            "outcome_status": "NOT_SCORED",
            "reason": "Candidate is not in the no-fill TP1 entry-offset redesign denominator.",
            "extra": {
                **capture_extra,
                "branch_decision": "KEEP_CURRENT_ENTRY_MODEL_NOT_IN_ENTRY_REDESIGN_DENOMINATOR",
                "decision_evidence": "CURRENT_ENTRY_MODEL_ROW_NOT_NO_FILL_TP1_OFFSET_REDESIGN",
                "scoring_boundary": "CURRENT_ENTRY_MODEL_ROW_NOT_NO_FILL_TP1_OFFSET_REDESIGN",
                "implementation_candidate": "NONE_CURRENT_ENTRY_ALREADY_TOUCHED_OR_NOT_TP1_NO_FILL",
            },
        }
    if tick_status != "TICK_REPLAY_SOURCE_COMPLETE" and _entry_offset_050r_m15_hard_no_fill_proof(redesign):
        return {
            "strategy_status": "KILLED_ENTRY_OFFSET_050R_M15_HARD_NO_FILL",
            "score_status": "COMPUTED_FROM_M15_HARD_NO_FILL_RANGE_PROOF",
            "outcome_status": "NO_FILL_AT_SHIFT",
            "reason": (
                "M15/LTF path proves the row stayed at least 1.0R from original entry with no entry touch; "
                "the 0.50R entry-offset cannot fill, so tick replay is not needed to kill this scorer row."
            ),
            "extra": {
                **capture_extra,
                "outcome_source": "m15_hard_no_fill_range_proof",
                "strategy_proxy_r": 0.0,
                "branch_decision": "KILL_FAR_MISS_050R_OFFSET_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL",
                "decision_evidence": "ENTRY_OFFSET_050R_M15_HARD_NO_FILL_GT_1R_NO_TICK_NEEDED",
                "scoring_boundary": "M15_HARD_NO_FILL_RANGE_PROOF_ONLY_NO_FILL_OR_TP_INFERENCE",
                "implementation_candidate": "NONE_FAR_MISS_050R_NO_FILL_KEEP_AS_RETEST_REDESIGN_FAILURE",
                "entry_offset_no_fill_control_status": "CURRENT_050R_FILL_CLAIM_UNSUPPORTED_REDESIGN_PATH_PRESERVED",
                "entry_offset_no_fill_repair_branch_candidate": (
                    "REDESIGN_ENTRY_OFFSET_NO_FILL_RETEST_SOURCE_COST_FILL_REPAIR_REQUIRED"
                ),
                **_current_claim_only_preservation_extra(
                    current_claim="ENTRY_OFFSET_050R_SPREAD_AWARE_SHIFT_FILL",
                    unsupported_reason="M15_HARD_NO_FILL_RANGE_PROOF_GT_1R_FROM_ORIGINAL_ENTRY",
                    what_was_tried="M15_RANGE_DISTANCE_REPAIR_FOR_INCOMPLETE_TICK_REPLAY_ROW",
                    what_could_make_it_work=(
                        "WIDER_RETEST_CONTROL_ENTRY_OR_MARKET_CONTROL_FILTER_WITH_SPREAD_AWARE_TICK_REPLAY"
                    ),
                    preserve_as="FAR_MISS_RETEST_CONTROL_REDESIGN_OR_AVOID_CONTEXT",
                    next_route="TEST_WIDER_RETEST_OFFSETS_AND_MARKET_CONTROL_BUCKETS_FOR_FAR_MISS_ROWS",
                    path_status={
                        "strategy_proxy_r": 0.0,
                        "outcome_source": "m15_hard_no_fill_range_proof",
                        "outcome_status": "NO_FILL_AT_SHIFT",
                    },
                    current_claim_proxy_counted=True,
                ),
            },
        }
    if tick_status == "TICK_REPLAY_SOURCE_COMPLETE" and outcome == "TP1_AFTER_SHIFT_FILL":
        near = bucket == "NEAR_MISS_ENTRY_OFFSET_CONTROL_QUEUE"
        return {
            "strategy_status": "SCORED_ENTRY_OFFSET_050R_CONCENTRATION_GUARDED_DEFAULT_OFF"
            if near
            else "SCORED_ENTRY_OFFSET_050R_FAR_MISS_CONCENTRATION_GUARDED_DEFAULT_OFF",
            "score_status": "COMPUTED_FROM_SPREAD_AWARE_TICK_REPLAY",
            "outcome_status": outcome,
            "reason": (
                "0.50R entry-offset replay filled and reached TP1 using spread-aware tick source. "
                "Rows are default-off entry-offset owner rows with the current symbol-date "
                "concentration guard applied before any implementation route."
            ),
            "extra": {
                **capture_extra,
                "outcome_source": "entry_offset_050r_spread_aware_tick_replay",
                "strategy_proxy_r": proxy_r,
                "branch_decision": ENTRY_OFFSET_050R_CONCENTRATION_GUARDED_BRANCH,
                "decision_evidence": (
                    "ENTRY_OFFSET_050R_TICK_REPLAY_TP_AFTER_FILL_WITH_CURRENT_CONCENTRATION_GUARD:"
                    " 13 owner rows, +8.66977687R, largest cluster US30_cash|2026-05-08 has 11 rows"
                ),
                "scoring_boundary": "PROXY_R_COUNTED_ON_OWNER_ROW_DEFAULT_OFF_CLUSTER_CAP_REQUIRED",
                "implementation_candidate": ENTRY_OFFSET_050R_CLUSTER_GUARDED_IMPLEMENTATION_CANDIDATE,
                **_entry_offset_050r_concentration_guard_extra(
                    candidate=candidate,
                    status="ENTRY_OFFSET_OWNER_CLUSTER_GUARDED",
                    subtype="NEAR_MISS" if near else "FAR_MISS",
                    proxy_r=proxy_r,
                    proxy_reference_status="COUNTED_ON_ENTRY_OFFSET_OWNER_ROW_ONLY",
                ),
            },
        }
    if tick_status == "TICK_REPLAY_SOURCE_COMPLETE" and outcome == "NO_FILL_AT_SHIFT":
        return {
            "strategy_status": "KILLED_ENTRY_OFFSET_050R_NO_FILL",
            "score_status": "COMPUTED_FROM_SPREAD_AWARE_TICK_REPLAY",
            "outcome_status": outcome,
            "reason": "0.50R offset still did not fill in spread-aware tick replay.",
            "extra": {
                **capture_extra,
                "outcome_source": "entry_offset_050r_spread_aware_tick_replay",
                "strategy_proxy_r": proxy_r,
                "branch_decision": "KILL_FAR_MISS_050R_OFFSET_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL",
                "decision_evidence": "ENTRY_OFFSET_050R_TICK_REPLAY_NO_FILL",
                "scoring_boundary": "NO_ENTRY_OFFSET_PROXY_UPLIFT_WHEN_050R_SHIFT_STILL_NO_FILL",
                "implementation_candidate": "NONE_FAR_MISS_050R_NO_FILL_KEEP_AS_RETEST_REDESIGN_FAILURE",
                "entry_offset_no_fill_control_status": "CURRENT_050R_FILL_CLAIM_UNSUPPORTED_REDESIGN_PATH_PRESERVED",
                "entry_offset_no_fill_repair_branch_candidate": (
                    "REDESIGN_ENTRY_OFFSET_NO_FILL_RETEST_SOURCE_COST_FILL_REPAIR_REQUIRED"
                ),
                **_current_claim_only_preservation_extra(
                    current_claim="ENTRY_OFFSET_050R_SPREAD_AWARE_SHIFT_FILL",
                    unsupported_reason="SPREAD_AWARE_TICK_REPLAY_STILL_NO_FILL_AT_050R_SHIFT",
                    what_was_tried="SPREAD_AWARE_TICK_REPLAY_OF_050R_ENTRY_OFFSET",
                    what_could_make_it_work=(
                        "WIDER_RETEST_OFFSET_OR_MARKET_CONTROL_CONDITION_THAT_REACHES_FILL_BEFORE_TARGET_AREA"
                    ),
                    preserve_as="FAR_MISS_RETEST_CONTROL_REDESIGN_OR_AVOID_CONTEXT",
                    next_route="ISOLATE_NO_FILL_ROWS_BY_DISTANCE_SYMBOL_SESSION_AND_TEST_WIDER_RETEST_CONTROL",
                    path_status={
                        "strategy_proxy_r": proxy_r,
                        "outcome_source": "entry_offset_050r_spread_aware_tick_replay",
                        "outcome_status": outcome,
                    },
                    current_claim_proxy_counted=True,
                ),
            },
        }
    if tick_status and tick_status != "TICK_REPLAY_SOURCE_COMPLETE":
        return {
            "strategy_status": "SOURCE_REPAIR_REQUIRED_TICK_REPLAY_INCOMPLETE",
            "score_status": "SOURCE_REPAIR_REQUIRED",
            "outcome_status": "NOT_SCORED",
            "reason": f"Entry-offset 0.50R tick replay source is incomplete: {tick_status}.",
            "extra": {
                **capture_extra,
                "branch_decision": "SOURCE_REPAIR_REQUIRED_FOR_ENTRY_OFFSET_SCORER",
                "decision_evidence": "ENTRY_OFFSET_050R_TICK_REPLAY_SOURCE_INCOMPLETE",
                "scoring_boundary": "NO_ENTRY_OFFSET_PROXY_R_WITHOUT_READABLE_TICK_REPLAY_SOURCE",
                "implementation_candidate": "REPAIR_TICK_PARQUET_SOURCE_BEFORE_ENTRY_OFFSET_SCORING",
            },
        }
    return {
        "strategy_status": "WAITING_FOR_ENTRY_OFFSET_050R_TICK_REPLAY_SOURCE",
        "score_status": "WAITING_SOURCE",
        "outcome_status": "NOT_SCORED",
        "reason": (
            "Entry-offset 0.50R scorer requires spread-aware tick replay; M15 distance alone is not a "
            "valid fill proxy after current replay killed 0.25R for all tick-complete affected rows."
        ),
        "extra": {
            **capture_extra,
            "branch_decision": "SOURCE_CAPTURE_REQUIRED_FOR_ENTRY_OFFSET_TICK_REPLAY_SCORER",
            "decision_evidence": "ENTRY_OFFSET_SCORER_REQUIRES_SPREAD_AWARE_TICK_REPLAY_NOT_M15_DISTANCE",
            "scoring_boundary": "NO_ENTRY_OFFSET_PROXY_R_WITHOUT_SPREAD_AWARE_TICK_REPLAY",
            "implementation_candidate": "BUILD_DEFAULT_OFF_ENTRY_OFFSET_050R_TICK_REPLAY_SCORER_WITH_SPREAD_AWARE_FILL_CONTRACT",
        },
    }


def _prefill_delivery_strategy_status(
    candidate: dict[str, Any],
    path_row: dict[str, Any],
) -> dict[str, Any]:
    redesign = entry_retest_redesign_context(candidate, path_row)
    bucket = str(redesign.get("entry_retest_redesign_bucket") or "")
    offset_outcome = str(path_row.get("entry_offset_050r_outcome_status") or "")
    offset_tick_status = str(path_row.get("entry_offset_050r_tick_replay_status") or "")
    offset_proxy_r = _safe_float(path_row.get("entry_offset_050r_proxy_r"))
    if bucket == "NOT_A_NO_FILL_TP1_ENTRY_REDESIGN_ROW":
        return {
            "strategy_status": "NOT_APPLICABLE_NOT_PREFILL_REDESIGN_DENOMINATOR",
            "score_status": "NOT_APPLICABLE",
            "outcome_status": "NOT_SCORED",
            "reason": "Candidate is outside the no-fill TP1 prefill/adverse redesign denominator.",
            "extra": {
                **redesign,
                "branch_decision": "KEEP_CURRENT_ENTRY_MODEL_NOT_IN_PREFILL_REDESIGN_DENOMINATOR",
                "decision_evidence": "CURRENT_ENTRY_MODEL_ROW_NOT_NO_FILL_TP1_PREFILL_REDESIGN",
                "scoring_boundary": "PREFILL_REDESIGN_NOT_APPLICABLE_OUTSIDE_NO_FILL_TP1_DENOMINATOR",
                "implementation_candidate": "NONE_CURRENT_ENTRY_ALREADY_TOUCHED_OR_NOT_TP1_NO_FILL",
            },
        }
    if bucket == "NEAR_MISS_ENTRY_OFFSET_CONTROL_QUEUE":
        if offset_tick_status == "TICK_REPLAY_SOURCE_COMPLETE" and offset_outcome == "TP1_AFTER_SHIFT_FILL":
            return {
                "strategy_status": "MERGED_PREFILL_ENTRY_OFFSET_CONCENTRATION_GUARD_REFERENCE",
                "score_status": "METADATA_MERGED_TO_ENTRY_OFFSET_SCORER",
                "outcome_status": "LINKED_ENTRY_OFFSET_TP1_AFTER_SHIFT_FILL",
                "reason": (
                    "Near-miss prefill metadata row links to a spread-aware 0.50R entry-offset TP-after-fill "
                    "scorer row; keep it as concentration-guarded source context for that scorer and do not "
                    "create a duplicate default-off prefill implementation."
                ),
                "extra": {
                    **redesign,
                    "linked_entry_offset_050r_outcome_status": offset_outcome,
                    "linked_entry_offset_050r_score_status": "COMPUTED_FROM_SPREAD_AWARE_TICK_REPLAY",
                    "linked_entry_offset_050r_proxy_r": offset_proxy_r,
                    "linked_entry_offset_proxy_r_owner": "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER",
                    "branch_decision": PREFILL_ENTRY_OFFSET_CONCENTRATION_GUARD_REFERENCE_BRANCH,
                    "decision_evidence": (
                        "PREFILL_NEAR_MISS_LINKED_ENTRY_OFFSET_050R_TICK_REPLAY_TP_AFTER_FILL_REFERENCE_ONLY"
                    ),
                    "scoring_boundary": "REFERENCE_ONLY_PREFILL_PROXY_R_NOT_COUNTED_STANDALONE",
                    "implementation_candidate": PREFILL_ENTRY_OFFSET_CLUSTER_REFERENCE_CANDIDATE,
                    "prefill_proxy_counting_decision": "PROXY_R_OWNED_BY_ENTRY_OFFSET_050R_NOT_DUPLICATED",
                    **_entry_offset_050r_concentration_guard_extra(
                        candidate=candidate,
                        status="PREFILL_REFERENCE_CLUSTER_GUARDED",
                        subtype="NEAR_MISS",
                        proxy_r=offset_proxy_r,
                        proxy_reference_status="REFERENCE_ONLY_NOT_COUNTED_DUPLICATE_ENTRY_OFFSET_OWNER",
                    ),
                },
            }
        if offset_tick_status == "TICK_REPLAY_SOURCE_COMPLETE" and offset_outcome == "NO_FILL_AT_SHIFT":
            return {
                "strategy_status": "KILL_PREFILL_NEAR_MISS_ENTRY_OFFSET_050R_NO_FILL",
                "score_status": "COMPUTED_FROM_SPREAD_AWARE_TICK_REPLAY",
                "outcome_status": offset_outcome,
                "reason": "Near-miss prefill metadata row links to a 0.50R entry-offset no-fill replay.",
                "extra": {
                    **redesign,
                    "linked_entry_offset_050r_outcome_status": offset_outcome,
                    "linked_entry_offset_050r_score_status": "COMPUTED_FROM_SPREAD_AWARE_TICK_REPLAY",
                    "linked_entry_offset_050r_proxy_r": offset_proxy_r,
                    "linked_entry_offset_proxy_r_owner": "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER",
                    "branch_decision": "KILL_PREFILL_NEAR_MISS_ENTRY_OFFSET_050R_NO_FILL",
                    "decision_evidence": "PREFILL_NEAR_MISS_LINKED_ENTRY_OFFSET_050R_TICK_REPLAY_NO_FILL",
                    "scoring_boundary": "PREFILL_METADATA_ONLY_LINKED_ENTRY_OFFSET_NO_FILL",
                    "implementation_candidate": "NONE_PREFILL_NEAR_MISS_050R_NO_FILL",
                    "entry_offset_no_fill_control_status": "CURRENT_050R_FILL_CLAIM_UNSUPPORTED_REDESIGN_PATH_PRESERVED",
                    "entry_offset_no_fill_repair_branch_candidate": (
                        "REDESIGN_ENTRY_OFFSET_NO_FILL_RETEST_SOURCE_COST_FILL_REPAIR_REQUIRED"
                    ),
                    **_current_claim_only_preservation_extra(
                        current_claim="PREFILL_NEAR_MISS_ENTRY_OFFSET_050R_FILL",
                        unsupported_reason="LINKED_ENTRY_OFFSET_050R_TICK_REPLAY_NO_FILL",
                        what_was_tried="LINKED_PREFILL_METADATA_TO_SPREAD_AWARE_ENTRY_OFFSET_REPLAY",
                        what_could_make_it_work=(
                            "DIFFERENT_OFFSET_OR_MARKET_CONTROL_STATE_THAT_FILLS_BEFORE_TARGET_AREA"
                        ),
                        preserve_as="NEAR_MISS_PREFILL_CONTEXT_OR_AVOID_FILTER_CANDIDATE",
                        next_route="TEST_NEAR_MISS_PREFILL_BY_SYMBOL_SESSION_SPREAD_AND_OFFSET_GRID",
                        path_status={
                            "strategy_proxy_r": offset_proxy_r,
                            "outcome_source": "entry_offset_050r_spread_aware_tick_replay",
                            "outcome_status": offset_outcome,
                        },
                        current_claim_proxy_counted=True,
                    ),
                },
            }
        return {
            "strategy_status": "REDESIGN_PREFILL_NEAR_MISS_ENTRY_OFFSET_050R_CHALLENGER",
            "score_status": "REDESIGN_CONTROL_ROW",
            "outcome_status": "NOT_SCORED",
            "reason": (
                "No-fill TP1 row came within 0.25R of entry; route it to the default-off 0.50R "
                "entry-offset challenger rather than a generic prefill no-scorer bucket."
            ),
            "extra": {
                **redesign,
                "branch_decision": "REDESIGN_WITH_ENTRY_OFFSET_050R_NEAR_MISS_CHALLENGER",
                "decision_evidence": "PREFILL_NEAR_MISS_ROW_ROUTES_TO_ENTRY_OFFSET_050R_SCORER",
                "scoring_boundary": "PREFILL_REDESIGN_METADATA_ONLY_ENTRY_OFFSET_SCORER_OWNS_PROXY_R",
                "implementation_candidate": "ENTRY_OFFSET_050R_NEAR_MISS_SPREAD_AWARE_CHALLENGER",
            },
        }
    if bucket == "FAR_MISS_RETEST_REDESIGN_CONTROL_QUEUE":
        if offset_tick_status == "TICK_REPLAY_SOURCE_COMPLETE" and offset_outcome == "TP1_AFTER_SHIFT_FILL":
            return {
                "strategy_status": "MERGED_PREFILL_ENTRY_OFFSET_CONCENTRATION_GUARD_REFERENCE",
                "score_status": "METADATA_MERGED_TO_ENTRY_OFFSET_SCORER",
                "outcome_status": "LINKED_ENTRY_OFFSET_TP1_AFTER_SHIFT_FILL",
                "reason": (
                    "Far-miss prefill metadata row links to a spread-aware 0.50R retest-control TP-after-fill "
                    "scorer row. Preserve the far-miss retest-control intelligence as an entry-offset "
                    "concentration-guarded component; proxy R remains owned by ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER."
                ),
                "extra": {
                    **redesign,
                    "linked_entry_offset_050r_outcome_status": offset_outcome,
                    "linked_entry_offset_050r_score_status": "COMPUTED_FROM_SPREAD_AWARE_TICK_REPLAY",
                    "linked_entry_offset_050r_proxy_r": offset_proxy_r,
                    "linked_entry_offset_proxy_r_owner": "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER",
                    "branch_decision": PREFILL_ENTRY_OFFSET_CONCENTRATION_GUARD_REFERENCE_BRANCH,
                    "decision_evidence": (
                        "PREFILL_FAR_MISS_LINKED_ENTRY_OFFSET_050R_TICK_REPLAY_TP_AFTER_FILL_REFERENCE_ONLY"
                    ),
                    "scoring_boundary": "REFERENCE_ONLY_PREFILL_PROXY_R_NOT_COUNTED_STANDALONE",
                    "implementation_candidate": PREFILL_ENTRY_OFFSET_CLUSTER_REFERENCE_CANDIDATE,
                    "prefill_proxy_counting_decision": "PROXY_R_OWNED_BY_ENTRY_OFFSET_050R_NOT_DUPLICATED",
                    **_entry_offset_050r_concentration_guard_extra(
                        candidate=candidate,
                        status="PREFILL_REFERENCE_CLUSTER_GUARDED",
                        subtype="FAR_MISS",
                        proxy_r=offset_proxy_r,
                        proxy_reference_status="REFERENCE_ONLY_NOT_COUNTED_DUPLICATE_ENTRY_OFFSET_OWNER",
                    ),
                },
            }
        if offset_tick_status == "TICK_REPLAY_SOURCE_COMPLETE" and offset_outcome == "NO_FILL_AT_SHIFT":
            return {
                "strategy_status": "KILL_PREFILL_FAR_MISS_050R_OFFSET_NO_FILL",
                "score_status": "COMPUTED_FROM_SPREAD_AWARE_TICK_REPLAY",
                "outcome_status": offset_outcome,
                "reason": "Far-miss prefill metadata row links to a 0.50R entry-offset no-fill replay.",
                "extra": {
                    **redesign,
                    "linked_entry_offset_050r_outcome_status": offset_outcome,
                    "linked_entry_offset_050r_score_status": "COMPUTED_FROM_SPREAD_AWARE_TICK_REPLAY",
                    "linked_entry_offset_050r_proxy_r": offset_proxy_r,
                    "linked_entry_offset_proxy_r_owner": "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER",
                    "branch_decision": "KILL_PREFILL_FAR_MISS_050R_OFFSET_NO_FILL_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL",
                    "decision_evidence": "PREFILL_FAR_MISS_LINKED_ENTRY_OFFSET_050R_TICK_REPLAY_NO_FILL",
                    "scoring_boundary": "PREFILL_METADATA_ONLY_LINKED_ENTRY_OFFSET_NO_FILL",
                    "implementation_candidate": "NONE_PREFILL_FAR_MISS_050R_NO_FILL_KEEP_AS_RETEST_REDESIGN_FAILURE",
                    "entry_offset_no_fill_control_status": "CURRENT_050R_FILL_CLAIM_UNSUPPORTED_REDESIGN_PATH_PRESERVED",
                    "entry_offset_no_fill_repair_branch_candidate": (
                        "REDESIGN_ENTRY_OFFSET_NO_FILL_RETEST_SOURCE_COST_FILL_REPAIR_REQUIRED"
                    ),
                    **_current_claim_only_preservation_extra(
                        current_claim="PREFILL_FAR_MISS_ENTRY_OFFSET_050R_RETEST_CONTROL_FILL",
                        unsupported_reason="LINKED_ENTRY_OFFSET_050R_TICK_REPLAY_NO_FILL",
                        what_was_tried="LINKED_PREFILL_FAR_MISS_METADATA_TO_SPREAD_AWARE_ENTRY_OFFSET_REPLAY",
                        what_could_make_it_work=(
                            "WIDER_RETEST_OFFSET_OR_MARKET_CONTROL_STATE_THAT_REACHES_FILL_BEFORE_TARGET_AREA"
                        ),
                        preserve_as="FAR_MISS_RETEST_CONTROL_REDESIGN_OR_AVOID_CONTEXT",
                        next_route="TEST_WIDER_RETEST_OFFSETS_AND_MARKET_CONTROL_BUCKETS_FOR_FAR_MISS_PREFILL_ROWS",
                        path_status={
                            "strategy_proxy_r": offset_proxy_r,
                            "outcome_source": "entry_offset_050r_spread_aware_tick_replay",
                            "outcome_status": offset_outcome,
                        },
                        current_claim_proxy_counted=True,
                    ),
                },
            }
        if offset_tick_status != "TICK_REPLAY_SOURCE_COMPLETE" and _entry_offset_050r_m15_hard_no_fill_proof(redesign):
            return {
                "strategy_status": "KILL_PREFILL_FAR_MISS_050R_M15_HARD_NO_FILL",
                "score_status": "COMPUTED_FROM_M15_HARD_NO_FILL_RANGE_PROOF",
                "outcome_status": "NO_FILL_AT_SHIFT",
                "reason": (
                    "M15/LTF path proves the far-miss row stayed at least 1.0R from original entry with no "
                    "entry touch; use this only to kill no-fill, not infer any fill or TP sequence."
                ),
                "extra": {
                    **redesign,
                    "linked_entry_offset_050r_outcome_status": "NO_FILL_AT_SHIFT",
                    "linked_entry_offset_050r_score_status": "COMPUTED_FROM_M15_HARD_NO_FILL_RANGE_PROOF",
                    "linked_entry_offset_050r_proxy_r": 0.0,
                    "linked_entry_offset_proxy_r_owner": "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER",
                    "branch_decision": "KILL_PREFILL_FAR_MISS_050R_OFFSET_NO_FILL_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL",
                    "decision_evidence": "PREFILL_FAR_MISS_ENTRY_OFFSET_050R_M15_HARD_NO_FILL_GT_1R_NO_TICK_NEEDED",
                    "scoring_boundary": "M15_HARD_NO_FILL_RANGE_PROOF_ONLY_NO_FILL_OR_TP_INFERENCE",
                    "implementation_candidate": "NONE_PREFILL_FAR_MISS_050R_NO_FILL_KEEP_AS_RETEST_REDESIGN_FAILURE",
                    "entry_offset_no_fill_control_status": "CURRENT_050R_FILL_CLAIM_UNSUPPORTED_REDESIGN_PATH_PRESERVED",
                    "entry_offset_no_fill_repair_branch_candidate": (
                        "REDESIGN_ENTRY_OFFSET_NO_FILL_RETEST_SOURCE_COST_FILL_REPAIR_REQUIRED"
                    ),
                    **_current_claim_only_preservation_extra(
                        current_claim="PREFILL_FAR_MISS_ENTRY_OFFSET_050R_RETEST_CONTROL_FILL",
                        unsupported_reason="M15_HARD_NO_FILL_RANGE_PROOF_GT_1R_FROM_ORIGINAL_ENTRY",
                        what_was_tried="M15_RANGE_DISTANCE_REPAIR_FOR_INCOMPLETE_TICK_REPLAY_PREFILL_ROW",
                        what_could_make_it_work=(
                            "WIDER_RETEST_CONTROL_ENTRY_OR_MARKET_CONTROL_FILTER_WITH_SPREAD_AWARE_TICK_REPLAY"
                        ),
                        preserve_as="FAR_MISS_RETEST_CONTROL_REDESIGN_OR_AVOID_CONTEXT",
                        next_route="TEST_WIDER_RETEST_OFFSETS_AND_MARKET_CONTROL_BUCKETS_FOR_FAR_MISS_PREFILL_ROWS",
                        path_status={
                            "strategy_proxy_r": 0.0,
                            "outcome_source": "m15_hard_no_fill_range_proof",
                            "outcome_status": "NO_FILL_AT_SHIFT",
                        },
                        current_claim_proxy_counted=True,
                    ),
                },
            }
        return {
            "strategy_status": "REDESIGN_PREFILL_FAR_MISS_RETEST_WITH_050R_OFFSET_CONTROL",
            "score_status": "REDESIGN_CONTROL_ROW",
            "outcome_status": "NOT_SCORED",
            "reason": (
                "No-fill TP1 row missed entry by more than 0.25R; keep it in a far-miss retest "
                "redesign/control bucket instead of treating it as a generic prefill no-scorer row."
            ),
            "extra": {
                **redesign,
                "branch_decision": "REDESIGN_FAR_MISS_RETEST_WITH_050R_OFFSET_CONTROL",
                "decision_evidence": "PREFILL_FAR_MISS_ROW_ROUTES_TO_RETEST_REDESIGN_CONTROL",
                "scoring_boundary": "PREFILL_REDESIGN_METADATA_ONLY_FAR_MISS_CONTROL_NOT_DEFAULT_ENTRY",
                "implementation_candidate": "ENTRY_OFFSET_050R_FAR_MISS_RETEST_CONTROL_NOT_DEFAULT_ENTRY",
            },
        }
    return {
        "strategy_status": "SOURCE_REPAIR_REQUIRED_PREFILL_ENTRY_REDESIGN_BUCKET",
        "score_status": "SOURCE_REPAIR_REQUIRED",
        "outcome_status": "NOT_SCORED",
        "reason": "Prefill redesign row lacks a reliable entry-distance bucket.",
        "extra": {
            **redesign,
            "branch_decision": "SOURCE_REPAIR_REQUIRED_FOR_PREFILL_ENTRY_REDESIGN_BUCKET",
            "decision_evidence": "PREFILL_ENTRY_REDESIGN_BUCKET_SOURCE_INCOMPLETE",
            "scoring_boundary": "NO_PREFILL_REDESIGN_DECISION_WITHOUT_ENTRY_DISTANCE_BUCKET",
            "implementation_candidate": "REPAIR_ENTRY_DISTANCE_SOURCE_BEFORE_PREFILL_REDESIGN_ROUTING",
        },
    }


def _metadata_shared_path_extra(
    *,
    kind: str,
    path_status: dict[str, Any],
) -> dict[str, Any]:
    if kind == "fvg":
        return {
            "outcome_source": path_status["outcome_source"],
            "strategy_proxy_r": path_status["strategy_proxy_r"],
            "scoring_boundary": "FVG_METADATA_SHARED_CANDIDATE_PATH_PROXY_NOT_STANDALONE_FVG_ENTRY",
            "branch_decision": "IMPLEMENT_DEFAULT_OFF_FVG_METADATA_SHARED_PATH_SCORER",
            "decision_evidence": "CAPTURED_FVG_METADATA_SCORED_WITH_SHARED_CANDIDATE_PATH_PROXY",
            "implementation_candidate": (
                "IMPLEMENT_DEFAULT_OFF_FVG_METADATA_SHARED_PATH_SCORER_AND_DESIGN_STANDALONE_ENTRY_LOCK_SCORER"
            ),
        }
    if kind == "structural":
        return {
            "outcome_source": path_status["outcome_source"],
            "strategy_proxy_r": path_status["strategy_proxy_r"],
            "scoring_boundary": "STRUCTURAL_LOCK_METADATA_SHARED_CANDIDATE_PATH_PROXY_NOT_ALTERNATE_REENTRY",
            "branch_decision": "IMPLEMENT_DEFAULT_OFF_STRUCTURAL_COMPOSITE_CAPTURED_METADATA_SHARED_PATH_SCORER",
            "decision_evidence": "CAPTURED_STRUCTURAL_LOCK_METADATA_SCORED_WITH_SHARED_CANDIDATE_PATH_PROXY",
            "implementation_candidate": (
                "IMPLEMENT_DEFAULT_OFF_STRUCTURAL_METADATA_SHARED_PATH_SCORER_AND_DESIGN_LOCK_REENTRY_SCORER"
            ),
        }
    raise ValueError(f"Unknown metadata scorer kind: {kind}")


def _duplicate_structural_shared_path_extra(path_status: dict[str, Any]) -> dict[str, Any]:
    proxy_reference = path_status["strategy_proxy_r"]
    return {
        "outcome_source": path_status["outcome_source"],
        "strategy_proxy_r": None,
        "scoring_boundary": (
            "NO_SEPARATE_V3_STRUCTURAL_LOCK_IMPLEMENTATION_FROM_DUPLICATED_SHARED_CANDIDATE_PATH_PROXY"
        ),
        "branch_decision": "MERGE_DUPLICATE_STRUCTURAL_LOCK_SHARED_PATH_PROXY_INTO_V2_STRUCT_COMPOSITE_ANY",
        "decision_evidence": (
            "V3 structural-lock rows share the same candidate-path proxy as "
            "V2_STRUCT_COMPOSITE_ANY; preserve the evidence as reference-only and count no "
            "independent strategy proxy R."
        ),
        "implementation_candidate": (
            "MERGE_INTO_CANONICAL_V2_STRUCT_COMPOSITE_ANY_SCORER_NO_DUPLICATE_R"
        ),
        "structural_duplicate_merge_status": (
            "MERGED_DUPLICATE_STRUCTURAL_LOCK_SHARED_PATH_PROXY_REFERENCE_ONLY"
        ),
        "structural_duplicate_proxy_owner_strategy_id": CANONICAL_STRUCTURAL_SHARED_PATH_ID,
        "structural_duplicate_proxy_reference_r": proxy_reference,
        "structural_duplicate_proxy_reference_status": (
            "REFERENCE_ONLY_DUPLICATE_STRUCTURAL_LOCK_SHARED_PATH_NOT_COUNTED"
        ),
        "preserved_candidate_path_proxy_r": proxy_reference,
        "preserved_candidate_path_outcome_source": path_status.get("outcome_source"),
        "preserved_candidate_path_outcome_status": path_status.get("outcome_status"),
        "opportunity_preservation_status": "DUPLICATE_STRUCTURAL_LOCK_SHARED_PATH_PROXY_MERGED",
        "opportunity_owner_row_id": CANONICAL_STRUCTURAL_SHARED_PATH_ID,
        "opportunity_owner_source_artifact": "src/research_infra/live_mechanical_shadow.py",
        "opportunity_proxy_r_reference": proxy_reference,
        "opportunity_proxy_reference_status": (
            "REFERENCE_ONLY_DUPLICATE_STRUCTURAL_LOCK_SHARED_PATH_NOT_COUNTED"
        ),
        "opportunity_not_independently_countable_reason": (
            "This V3 structural-lock variant duplicates the canonical V2_STRUCT_COMPOSITE_ANY "
            "candidate-path proxy and is not independently countable as strategy R."
        ),
        "opportunity_useful_mechanism": (
            "V3 structural-lock variants remain useful as redesign inputs for separate lock/reentry "
            "or cost-aware scorers, but current shared-path evidence is owned by V2_STRUCT_COMPOSITE_ANY."
        ),
        "opportunity_downstream_paths": [
            "redesign",
            "context feature",
            "source requirement",
            "broader system component",
        ],
        "underlying_intelligence_preserved": True,
        "missed_opportunity_audit": {
            "kill_scope": "NOT_KILLED_DUPLICATE_MERGED_TO_CANONICAL_OWNER",
            "current_claim": "V3_STRUCTURAL_LOCK_VARIANT_INDEPENDENT_SHARED_PATH_PROXY",
            "unsupported_reason": (
                "Duplicate candidate-path proxy is already owned by V2_STRUCT_COMPOSITE_ANY."
            ),
            "what_was_tried": "Compared strategy_id and candidate_id shared-path proxy ownership.",
            "what_could_make_it_work": (
                "A distinct source-bound V3 lock/reentry/cost scorer with non-duplicated entry, "
                "stop, target, fill, and path contract."
            ),
            "preserve_as": "STRUCTURAL_LOCK_VARIANT_REDESIGN_OR_CONTEXT_COMPONENT",
            "next_route": "BUILD_DISTINCT_STRUCTURAL_LOCK_REENTRY_COST_AWARE_SCORER_BEFORE_COUNTING_V3_R",
        },
    }


def _gbpjpy_long_adverse_cluster_applies(candidate: dict[str, Any]) -> bool:
    symbol = str(candidate.get("symbol") or candidate.get("broker_symbol") or "").upper()
    side = str(candidate.get("side") or "").upper()
    return symbol == "GBPJPY" and side == "LONG"


def _gbpjpy_long_adverse_avoid_interval(path_status: dict[str, Any]) -> tuple[float, float, str] | None:
    outcome = str(path_status.get("outcome_status") or "").upper()
    if outcome == "ENTRY_THEN_TP1_SL_SAME_M1_AMBIGUOUS":
        return -1.5, 1.0, "TP1_OR_SL_SAME_M1_AVOID_SAVED_R_INTERVAL"
    if outcome == "ENTRY_THEN_TP1_SAME_M1_AMBIGUOUS":
        return -1.5, 0.0, "TP1_OR_NO_FILL_SAME_M1_AVOID_SAVED_R_INTERVAL"
    if outcome == "ENTRY_THEN_SL_SAME_M1_AMBIGUOUS":
        return 0.0, 1.0, "SL_OR_NO_FILL_SAME_M1_AVOID_SAVED_R_INTERVAL"
    return None


def _gbpjpy_long_adverse_cluster_extra(
    path_status: dict[str, Any],
    *,
    strategy_id: str,
    path_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    proxy_r = _safe_float(path_status.get("strategy_proxy_r"))
    canonical_owner = strategy_id == CANONICAL_STRUCTURAL_SHARED_PATH_ID
    numeric_adverse = proxy_r is not None and proxy_r < 0
    numeric_non_adverse = canonical_owner and proxy_r is not None and proxy_r >= 0
    bounded_interval = _gbpjpy_long_adverse_avoid_interval(path_status) if canonical_owner else None
    unresolved_horizon = (
        canonical_owner
        and proxy_r is None
        and str(path_status.get("outcome_status") or "") == "ENTRY_TOUCHED_UNRESOLVED"
    )
    unresolved_metrics = entry_reference_metrics(path_row or {}) if unresolved_horizon else {}
    unresolved_mfe_r = _safe_float(unresolved_metrics.get("max_favorable_r_from_entry"))
    unresolved_mae_r = _safe_float(unresolved_metrics.get("max_adverse_r_from_entry"))
    saved_proxy_r = round(-proxy_r, 8) if canonical_owner and numeric_adverse else None
    if saved_proxy_r is not None:
        avoid_status = "CANONICAL_AVOID_FILTER_SAVED_R_OWNER"
        avoid_decision = "IMPLEMENT_DEFAULT_OFF_GBPJPY_LONG_STRUCTURAL_FVG_OB_ADVERSE_AVOID_FILTER"
        reference_status = "NUMERIC_ADVERSE_PROXY_REFERENCE_COUNTED_AS_SAVED_R"
        decision_evidence = "NUMERIC_ADVERSE_PROXY_ROW_COUNTED_AS_CANONICAL_AVOID_FILTER_SAVED_R"
    elif numeric_adverse:
        avoid_status = "DUPLICATE_AVOID_FILTER_PROXY_REFERENCE_NOT_COUNTED"
        avoid_decision = "MERGE_DUPLICATE_GBPJPY_LONG_ADVERSE_AVOID_EVIDENCE_TO_CANONICAL_OWNER"
        reference_status = "DUPLICATE_NUMERIC_ADVERSE_PROXY_REFERENCE_NOT_COUNTED"
        decision_evidence = "NUMERIC_ADVERSE_PROXY_ROW_MERGED_TO_CANONICAL_AVOID_FILTER_OWNER"
    elif bounded_interval is not None:
        avoid_status = "BOUNDED_AVOID_FILTER_SAVED_R_INTERVAL_NOT_COUNTED"
        avoid_decision = "REDESIGN_GBPJPY_LONG_ADVERSE_AVOID_FILTER_BOUNDED_PROXY_REPAIR"
        reference_status = "BOUNDED_AMBIGUOUS_PROXY_INTERVAL_REFERENCE_NOT_COUNTED"
        decision_evidence = "AMBIGUOUS_SAME_M1_TERMINAL_ORDER_BOUND_AS_AVOID_FILTER_SAVED_R_INTERVAL"
    elif numeric_non_adverse:
        avoid_status = "REDESIGN_AVOID_FILTER_FALSE_POSITIVE_PROXY_REFERENCE"
        avoid_decision = "REDESIGN_GBPJPY_LONG_ADVERSE_AVOID_FILTER_FALSE_POSITIVE_CONTEXT_REQUIRED"
        reference_status = "NUMERIC_NON_ADVERSE_PROXY_REFERENCE_REDESIGN_FALSE_POSITIVE"
        decision_evidence = "NUMERIC_NON_ADVERSE_PROXY_ROW_SHOWS_BROAD_AVOID_FILTER_FALSE_POSITIVE"
    elif unresolved_horizon:
        avoid_status = "UNRESOLVED_HORIZON_AVOID_FILTER_REFERENCE_NOT_COUNTED"
        avoid_decision = "REDESIGN_GBPJPY_LONG_ADVERSE_AVOID_FILTER_UNRESOLVED_HORIZON_CONTEXT_REQUIRED"
        reference_status = "UNRESOLVED_HORIZON_MFE_MAE_REFERENCE_NOT_COUNTED"
        decision_evidence = "ENTRY_TOUCHED_UNRESOLVED_HORIZON_WITH_MFE_MAE_REFERENCE_NO_TERMINAL_R"
    else:
        avoid_status = "SOURCE_REQUIRED_BEFORE_AVOID_SAVED_R_COUNT"
        avoid_decision = "REDESIGN_GBPJPY_LONG_ADVERSE_AVOID_FILTER_SOURCE_REQUIRED"
        reference_status = "NO_NUMERIC_PROXY_CURRENT_ROW_SOURCE_OR_LTF_REQUIRED"
        decision_evidence = "CURRENT_ROW_LACKS_NUMERIC_OR_BOUNDED_PROXY_BEFORE_AVOID_FILTER_R_COUNT"
    interval_low = bounded_interval[0] if bounded_interval is not None else None
    interval_high = bounded_interval[1] if bounded_interval is not None else None
    interval_status = bounded_interval[2] if bounded_interval is not None else None
    non_saved_reference = round(-proxy_r, 8) if numeric_non_adverse else None
    return {
        "outcome_source": path_status["outcome_source"],
        "strategy_proxy_r": path_status["strategy_proxy_r"],
        "scoring_boundary": (
            "CURRENT_CLAIM_NOT_IMPLEMENTED_FOR_GBPJPY_LONG_UNTIL_AVOID_OR_CONTEXT_FILTER_REDESIGN"
        ),
        "branch_decision": (
            "REDESIGN_GBPJPY_LONG_STRUCTURAL_FVG_OB_ADVERSE_CLUSTER_AVOID_FILTER_CANDIDATE"
        ),
        "decision_evidence": decision_evidence,
        "implementation_candidate": "REDESIGN_GBPJPY_LONG_STRUCTURAL_FVG_OB_AVOID_OR_CONTEXT_FILTER",
        "gbpjpy_long_adverse_avoid_materialization_status": avoid_status,
        "gbpjpy_long_adverse_avoid_candidate_decision": avoid_decision,
        "gbpjpy_long_adverse_current_claim_proxy_r_reference": proxy_r,
        "gbpjpy_long_adverse_current_claim_proxy_reference_status": reference_status,
        "gbpjpy_long_adverse_avoid_saved_proxy_r": saved_proxy_r,
        "gbpjpy_long_adverse_avoid_saved_proxy_counted": saved_proxy_r is not None,
        "gbpjpy_long_adverse_avoid_saved_proxy_r_interval_low": interval_low,
        "gbpjpy_long_adverse_avoid_saved_proxy_r_interval_high": interval_high,
        "gbpjpy_long_adverse_avoid_saved_proxy_interval_status": interval_status,
        "gbpjpy_long_adverse_avoid_saved_proxy_interval_counted": False,
        "gbpjpy_long_adverse_avoid_non_saved_proxy_r_reference": non_saved_reference,
        "gbpjpy_long_adverse_unresolved_horizon_mfe_r_reference": (
            _round(unresolved_mfe_r) if unresolved_horizon else None
        ),
        "gbpjpy_long_adverse_unresolved_horizon_mae_r_reference": (
            _round(-unresolved_mae_r) if unresolved_horizon and unresolved_mae_r is not None else None
        ),
        "gbpjpy_long_adverse_avoid_duplicate_policy": (
            "COUNT_SAVED_R_ONCE_PER_CANDIDATE_USING_CANONICAL_STRUCTURAL_COMPOSITE_ROW"
        ),
        "underlying_intelligence_preserved": True,
        "missed_opportunity_audit": {
            "kill_scope": "NOT_KILLED_REDESIGN_ADVERSE_CLUSTER",
            "preserve_as": "GBPJPY_LONG_AVOID_INVERSE_OR_CONTEXT_FILTER_CANDIDATE",
            "unsupported_current_claim": (
                "BROAD_STRUCTURAL_OR_FVG_OB_DEFAULT_OFF_IMPLEMENTATION_FOR_GBPJPY_LONG"
            ),
            "what_was_tried": "CONDITION_SPLIT_BY_BRANCH_SYMBOL_SIDE_ON_CURRENT_PROXY_ROWS",
            "what_could_make_it_work": (
                "SOURCE_BOUND_FILTER_THAT_SEPARATES_ADVERSE_GBPJPY_LONG_CONTEXTS_OR_INVERSE_AVOID_RULE"
            ),
            "next_route": (
                "TEST_GBPJPY_LONG_BY_SESSION_TIMEFRAME_REGIME_SOURCE_AND_AS_AVOID_OR_INVERSE_FILTER"
            ),
        },
    }


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                item = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                rows.append(item)
    return rows


def latest_path_rows_by_candidate(path_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest: dict[str, tuple[datetime, int, dict[str, Any]]] = {}
    for idx, row in enumerate(path_rows):
        candidate_id = str(row.get("candidate_id") or "")
        if not candidate_id:
            continue
        asof = (
            _parse_utc(row.get("asof_latest_candle_utc"))
            or _parse_utc(row.get("created_at_utc"))
            or datetime.min.replace(tzinfo=timezone.utc)
        )
        previous = latest.get(candidate_id)
        if previous is None or (asof, idx) >= (previous[0], previous[1]):
            latest[candidate_id] = (asof, idx, row)
    return [item[2] for item in sorted(latest.values(), key=lambda item: item[1])]


def latest_existing_by_key(path: Path) -> dict[tuple[str, str, str], dict[str, Any]]:
    rows: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in read_jsonl(path):
        candidate_id = str(row.get("candidate_id") or "")
        strategy_id = str(row.get("strategy_id") or "")
        asof = str(row.get("asof_latest_candle_utc") or "")
        if candidate_id and strategy_id and asof:
            key = (candidate_id, strategy_id, asof)
            current = _parse_utc(row.get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
            previous = _parse_utc(rows.get(key, {}).get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
            if current >= previous:
                rows[key] = row
    return rows


def latest_structural_metadata_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, tuple[datetime, int, dict[str, Any]]] = {}
    for idx, row in enumerate(rows):
        candidate_id = str(row.get("candidate_id") or "")
        fields = row.get("captured_structural_source_fields")
        if not candidate_id or not isinstance(fields, dict):
            continue
        observed = (
            _parse_utc(row.get("created_at_utc"))
            or _parse_utc(row.get("backfilled_at_utc"))
            or datetime.min.replace(tzinfo=timezone.utc)
        )
        previous = latest.get(candidate_id)
        if previous is None or (observed, idx) >= (previous[0], previous[1]):
            latest[candidate_id] = (observed, idx, row)
    return {candidate_id: item[2] for candidate_id, item in latest.items()}


def latest_nofill_forward_capture_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, tuple[datetime, int, dict[str, Any]]] = {}
    for idx, row in enumerate(rows):
        candidate_id = str(row.get("candidate_id") or "")
        if not candidate_id:
            continue
        observed = (
            _parse_utc(row.get("created_at_utc"))
            or _parse_utc(row.get("capture_write_completed_at_utc"))
            or datetime.min.replace(tzinfo=timezone.utc)
        )
        previous = latest.get(candidate_id)
        if previous is None or (observed, idx) >= (previous[0], previous[1]):
            latest[candidate_id] = (observed, idx, row)
    return {candidate_id: item[2] for candidate_id, item in latest.items()}


def latest_moonshot_selected_action_source_capture(
    rows: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    latest: dict[tuple[str, str], tuple[datetime, int, dict[str, Any]]] = {}
    for idx, row in enumerate(rows):
        candidate_id = str(row.get("candidate_id") or "")
        strategy_id = str(row.get("strategy_id") or "")
        if not candidate_id or not strategy_id:
            continue
        observed = (
            _parse_utc(row.get("created_at_utc"))
            or _parse_utc(row.get("decision_time_utc"))
            or datetime.min.replace(tzinfo=timezone.utc)
        )
        key = (candidate_id, strategy_id)
        previous = latest.get(key)
        if previous is None or (observed, idx) >= (previous[0], previous[1]):
            latest[key] = (observed, idx, row)
    return {key: item[2] for key, item in latest.items()}


def latest_pending_tick_spread_reconstruction_by_candidate(
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    latest: dict[str, tuple[datetime, int, dict[str, Any]]] = {}
    for idx, row in enumerate(rows):
        candidate_id = str(row.get("candidate_id") or "")
        if not candidate_id:
            continue
        observed = (
            _parse_utc(row.get("created_at_utc"))
            or _parse_utc(row.get("decision_time_utc"))
            or datetime.min.replace(tzinfo=timezone.utc)
        )
        previous = latest.get(candidate_id)
        if previous is None or (observed, idx) >= (previous[0], previous[1]):
            latest[candidate_id] = (observed, idx, row)
    return {candidate_id: item[2] for candidate_id, item in latest.items()}


def latest_standalone_fvg_repair_decision_by_key(
    rows: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    latest: dict[tuple[str, str], tuple[datetime, int, dict[str, Any]]] = {}
    for idx, row in enumerate(rows):
        candidate_id = str(row.get("candidate_id") or "")
        strategy_id = str(row.get("strategy_id") or "")
        if not candidate_id or not strategy_id:
            continue
        if row.get("source_decision_status") != "ACTION_LEDGER_REPAIRED_CURRENT_CLAIM_DECISION":
            continue
        observed = (
            _parse_utc(row.get("created_at_utc"))
            or _parse_utc(row.get("generated_utc"))
            or _parse_utc(row.get("decision_time_utc"))
            or datetime.min.replace(tzinfo=timezone.utc)
        )
        key = (candidate_id, strategy_id)
        previous = latest.get(key)
        if previous is None or (observed, idx) >= (previous[0], previous[1]):
            latest[key] = (observed, idx, row)
    return {key: item[2] for key, item in latest.items()}


def latest_swing_protected_repair_decision_by_key(
    rows: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    latest: dict[tuple[str, str], tuple[datetime, int, dict[str, Any]]] = {}
    for idx, row in enumerate(rows):
        candidate_id = str(row.get("candidate_id") or "")
        strategy_id = str(row.get("strategy_id") or "")
        if not candidate_id or strategy_id != SWING_PROTECTED_STRATEGY_ID:
            continue
        if row.get("source_decision_status") != "ACTION_LEDGER_REPAIRED_SWING_PROTECTED_CURRENT_CLAIM_DECISION":
            continue
        observed = (
            _parse_utc(row.get("created_at_utc"))
            or _parse_utc(row.get("generated_utc"))
            or _parse_utc(row.get("decision_time_utc"))
            or datetime.min.replace(tzinfo=timezone.utc)
        )
        key = (candidate_id, strategy_id)
        previous = latest.get(key)
        if previous is None or (observed, idx) >= (previous[0], previous[1]):
            latest[key] = (observed, idx, row)
    return {key: item[2] for key, item in latest.items()}


def latest_nas100_depth_thinness_source_repair_by_key(
    rows: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    latest: dict[tuple[str, str], tuple[datetime, int, dict[str, Any]]] = {}
    for idx, row in enumerate(rows):
        candidate_id = str(row.get("candidate_id") or "")
        strategy_id = str(row.get("strategy_id") or "")
        if not candidate_id or strategy_id != NAS100_DEPTH_THINNESS_STRATEGY_ID:
            continue
        observed = (
            _parse_utc(row.get("created_at_utc"))
            or _parse_utc(row.get("generated_utc"))
            or _parse_utc(row.get("decision_time_utc"))
            or datetime.min.replace(tzinfo=timezone.utc)
        )
        key = (candidate_id, strategy_id)
        previous = latest.get(key)
        if previous is None or (observed, idx) >= (previous[0], previous[1]):
            latest[key] = (observed, idx, row)
    return {key: item[2] for key, item in latest.items()}


def latest_fvg_ob_trade_record_bounds_repair_by_key(
    rows: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    latest: dict[tuple[str, str], tuple[datetime, int, dict[str, Any]]] = {}
    for idx, row in enumerate(rows):
        candidate_id = str(row.get("candidate_id") or "")
        strategy_id = str(row.get("strategy_id") or "")
        if not candidate_id or strategy_id != FVG_OB_CONFLUENCE_ID:
            continue
        if row.get("source_decision_status") != (
            "ACTION_LEDGER_REPAIRED_FVG_OB_TRADE_RECORD_BOUNDS_DECISION"
        ):
            continue
        observed = (
            _parse_utc(row.get("created_at_utc"))
            or _parse_utc(row.get("generated_utc"))
            or _parse_utc(row.get("decision_time_utc"))
            or datetime.min.replace(tzinfo=timezone.utc)
        )
        key = (candidate_id, strategy_id)
        previous = latest.get(key)
        if previous is None or (observed, idx) >= (previous[0], previous[1]):
            latest[key] = (observed, idx, row)
    return {key: item[2] for key, item in latest.items()}


def _decision_time_geometry_from_trade_parameters(candidate: dict[str, Any]) -> dict[str, Any] | None:
    params = candidate.get("trade_parameters")
    if not isinstance(params, dict):
        return None
    entry = _safe_float(params.get("entry_price"))
    stop = _safe_float(params.get("stop_loss"))
    tp1 = _safe_float(params.get("take_profit_1"))
    direction = str(params.get("direction") or candidate.get("side") or "").upper()
    if entry is None or stop is None or tp1 is None or direction not in {"LONG", "SHORT"}:
        return None
    risk_price = abs(entry - stop)
    gross_tp1_r = None if risk_price == 0 else abs(tp1 - entry) / risk_price
    return {
        "direction": direction,
        "entry_price": entry,
        "stop_loss": stop,
        "take_profit_1": tp1,
        "risk_price": risk_price,
        "gross_tp1_r": gross_tp1_r,
        "reported_risk_reward_ratio": params.get("risk_reward_ratio"),
        "sl_buffer_applied": params.get("sl_buffer_applied"),
    }


def merge_structural_metadata_candidate(
    candidate: dict[str, Any],
    metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    if not metadata:
        return candidate
    source_fields = metadata.get("captured_structural_source_fields")
    if not isinstance(source_fields, dict):
        return candidate

    out = dict(candidate)
    structural = out.get("decision_time_structural_fields")
    structural = dict(structural) if isinstance(structural, dict) else {}
    existing_fields = structural.get("fields")
    merged_fields = dict(existing_fields) if isinstance(existing_fields, dict) else {}
    for field, payload in source_fields.items():
        if field not in merged_fields or merged_fields.get(field) in (None, "", [], {}):
            merged_fields[field] = payload

    if merged_fields.get("cost_aware_min_r_fields") in (None, "", [], {}):
        geometry = _decision_time_geometry_from_trade_parameters(out)
        if geometry is not None:
            merged_fields["cost_aware_min_r_fields"] = {
                "source_status": "DECISION_TIME_TRADE_PARAMETERS_DERIVED_COST_GEOMETRY",
                "candidate_geometry": geometry,
                "cost_model_status": "RAW_DECISION_GEOMETRY_FROM_TRADE_PARAMETERS_COST_MODEL_NOT_APPLIED",
            }

    existing_statuses = structural.get("field_statuses")
    merged_statuses = dict(existing_statuses) if isinstance(existing_statuses, dict) else {}
    source_statuses = metadata.get("structural_source_field_statuses")
    if isinstance(source_statuses, dict):
        for field, status in source_statuses.items():
            if not merged_statuses.get(field):
                merged_statuses[field] = status
    if (
        merged_fields.get("cost_aware_min_r_fields")
        and not merged_statuses.get("cost_aware_min_r_fields")
    ):
        payload = merged_fields.get("cost_aware_min_r_fields")
        if isinstance(payload, dict):
            merged_statuses["cost_aware_min_r_fields"] = payload.get("source_status")

    structural.update(
        {
            "capture_status": structural.get("capture_status")
            or metadata.get("decision_time_structural_capture_status")
            or "LIVE_STRUCTURAL_METADATA_MERGED",
            "field_statuses": merged_statuses,
            "fields": merged_fields,
            "live_structural_metadata_created_at_utc": metadata.get("created_at_utc"),
            "live_structural_metadata_backfilled_at_utc": metadata.get("backfilled_at_utc"),
            "live_structural_metadata_manual_backfill_status": metadata.get("manual_backfill_status"),
            "live_structural_metadata_no_leak_status": metadata.get("no_leak_status"),
        }
    )
    out["decision_time_structural_fields"] = structural

    recovered = metadata.get("recovered_decision_time_fields")
    if isinstance(recovered, dict):
        for key in ("frameworks_evaluated", "h1_setup", "m15_confirmation"):
            if not out.get(key) and recovered.get(key):
                out[key] = recovered[key]
    return out


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _round(value: float | None) -> float | None:
    return None if value is None else round(value, 8)


def _parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def path_outcome_status(path_row: dict[str, Any]) -> str:
    label = str(path_row.get("path_label") or "")
    touched = path_row.get("touched_entry")
    hit_tp1 = path_row.get("hit_tp1")
    hit_sl = path_row.get("hit_sl")
    if hit_tp1 is True and hit_sl is True:
        return "M15_PATH_AMBIGUOUS_TP1_AND_SL"
    if touched is False and "without_entry_touch" in label:
        return "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH"
    if touched is False:
        return "NO_ENTRY_TOUCH_BY_ASOF"
    if touched is True and hit_tp1 is True:
        return "ENTRY_TOUCHED_THEN_TP1"
    if touched is True and hit_sl is True:
        return "ENTRY_TOUCHED_THEN_SL"
    if touched is True:
        return "ENTRY_TOUCHED_UNRESOLVED"
    return "PATH_STATUS_UNKNOWN"


def entry_reference_metrics(path_row: dict[str, Any]) -> dict[str, Any]:
    params = path_row.get("trade_parameters") or {}
    side = str(path_row.get("side") or params.get("direction") or "").upper()
    entry = _safe_float(params.get("entry_price"))
    stop = _safe_float(params.get("stop_loss"))
    tp1 = _safe_float(params.get("take_profit_1"))
    min_low = _safe_float(path_row.get("min_low"))
    max_high = _safe_float(path_row.get("max_high"))
    last_close = _safe_float(path_row.get("last_close"))
    base_r = abs(entry - stop) if entry is not None and stop is not None else None
    favorable_price = adverse_price = None
    if entry is not None and max_high is not None and min_low is not None and side == "LONG":
        favorable_price = max_high - entry
        adverse_price = entry - min_low
    elif entry is not None and max_high is not None and min_low is not None and side == "SHORT":
        favorable_price = entry - min_low
        adverse_price = max_high - entry
    return {
        "entry_price": entry,
        "stop_loss": stop,
        "take_profit_1": tp1,
        "base_r_price": _round(base_r),
        "max_favorable_price_from_entry": _round(favorable_price),
        "max_adverse_price_from_entry": _round(adverse_price),
        "max_favorable_r_from_entry": _round(favorable_price / base_r)
        if favorable_price is not None and base_r and base_r > 0
        else None,
        "max_adverse_r_from_entry": _round(adverse_price / base_r)
        if adverse_price is not None and base_r and base_r > 0
        else None,
        "last_close": last_close,
        "min_low": min_low,
        "max_high": max_high,
        "r_metrics_reference": "ENTRY_REFERENCE_NOT_REALIZED_UNLESS_ENTRY_TOUCHED",
    }


def entry_retest_redesign_context(candidate: dict[str, Any], path_row: dict[str, Any]) -> dict[str, Any]:
    params = candidate.get("trade_parameters") or path_row.get("trade_parameters") or {}
    entry = _safe_float(params.get("entry_price"))
    stop = _safe_float(params.get("stop_loss"))
    side = str(candidate.get("side") or path_row.get("side") or params.get("direction") or "").upper()
    base_r = abs(entry - stop) if entry is not None and stop is not None else None
    nearest_distance_r = _safe_float(path_row.get("nearest_distance_to_entry_r"))
    if nearest_distance_r is None:
        nearest_distance = _safe_float(path_row.get("nearest_abs_distance_to_entry"))
        if nearest_distance is None:
            signed_distance = _safe_float(path_row.get("nearest_distance_to_entry"))
            nearest_distance = abs(signed_distance) if signed_distance is not None else None
        if nearest_distance is None and entry is not None:
            min_low = _safe_float(path_row.get("min_low"))
            max_high = _safe_float(path_row.get("max_high"))
            if side == "LONG" and min_low is not None:
                nearest_distance = abs(min_low - entry)
            elif side == "SHORT" and max_high is not None:
                nearest_distance = abs(entry - max_high)
        nearest_distance_r = nearest_distance / base_r if nearest_distance is not None and base_r and base_r > 0 else None

    entry_touch_distance_status = str(path_row.get("entry_touch_distance_status") or "")
    if not entry_touch_distance_status:
        if path_row.get("touched_entry") is True:
            entry_touch_distance_status = "ENTRY_TOUCHED"
        elif nearest_distance_r is None:
            entry_touch_distance_status = "ENTRY_DISTANCE_UNKNOWN"
        elif nearest_distance_r <= 0.25:
            entry_touch_distance_status = "NEAR_MISS_LE_0_25R"
        else:
            entry_touch_distance_status = "FAR_MISS_GT_0_25R"

    path_status = path_outcome_status(path_row)
    if path_status != "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH":
        redesign_bucket = "NOT_A_NO_FILL_TP1_ENTRY_REDESIGN_ROW"
        bucket_basis = "NOT_ENTRY_REDESIGN_DENOMINATOR"
        fill_claim_status = "NOT_APPLICABLE"
        tick_replay_requirement = "NOT_REQUIRED"
    elif entry_touch_distance_status == "NEAR_MISS_LE_0_25R":
        redesign_bucket = "NEAR_MISS_ENTRY_OFFSET_CONTROL_QUEUE"
        bucket_basis = "M15_RANGE_DISTANCE_TO_ORIGINAL_ENTRY"
        fill_claim_status = "NO_FILL_CLAIM_WITHOUT_SPREAD_AWARE_LTF_OR_TICK_REPLAY"
        tick_replay_requirement = "REQUIRED_BEFORE_OFFSET_SCORER_R"
    elif entry_touch_distance_status == "FAR_MISS_GT_0_25R":
        redesign_bucket = "FAR_MISS_RETEST_REDESIGN_CONTROL_QUEUE"
        bucket_basis = "M15_RANGE_DISTANCE_TO_ORIGINAL_ENTRY"
        fill_claim_status = "NO_FILL_CLAIM_WITHOUT_SPREAD_AWARE_LTF_OR_TICK_REPLAY"
        tick_replay_requirement = "REQUIRED_BEFORE_OFFSET_SCORER_R"
    else:
        redesign_bucket = "ENTRY_DISTANCE_UNKNOWN_REPAIR_REQUIRED"
        bucket_basis = "ENTRY_DISTANCE_SOURCE_INCOMPLETE"
        fill_claim_status = "NO_FILL_CLAIM_WITHOUT_DISTANCE_SOURCE"
        tick_replay_requirement = "REQUIRED_BEFORE_OFFSET_SCORER_R"
    return {
        "entry_touch_distance_status": entry_touch_distance_status,
        "nearest_distance_to_entry_r": _round(nearest_distance_r),
        "entry_retest_redesign_bucket": redesign_bucket,
        "entry_retest_redesign_bucket_basis": bucket_basis,
        "entry_retest_redesign_fill_claim_status": fill_claim_status,
        "entry_retest_redesign_tick_replay_requirement": tick_replay_requirement,
    }


def _snapshot_map(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    snapshots = candidate.get("strategy_snapshots")
    if isinstance(snapshots, list) and snapshots:
        return [item for item in snapshots if isinstance(item, dict)]
    return [dict(item) for item in FOLLOW_STRATEGY_REGISTRY]


def _structural_source_status(candidate: dict[str, Any], field: str) -> str:
    structural = candidate.get("decision_time_structural_fields")
    if not isinstance(structural, dict):
        return "SOURCE_NOT_CAPTURED"
    fields = structural.get("fields")
    if not isinstance(fields, dict):
        return "SOURCE_NOT_CAPTURED"
    payload = fields.get(field)
    if isinstance(payload, dict):
        return str(payload.get("source_status") or "CAPTURED")
    return "CAPTURED" if payload not in (None, "", [], {}) else "SOURCE_NOT_CAPTURED"


def _structural_sources_available(candidate: dict[str, Any], fields: set[str]) -> bool:
    return all(
        _structural_source_status(candidate, field) not in SOURCE_MISSING_STATUSES
        for field in fields
    )


def _structural_field_payload(candidate: dict[str, Any], field: str) -> dict[str, Any]:
    structural = candidate.get("decision_time_structural_fields")
    if not isinstance(structural, dict):
        return {}
    fields = structural.get("fields")
    if not isinstance(fields, dict):
        return {}
    payload = fields.get(field)
    return payload if isinstance(payload, dict) else {}


def _risk_payload(candidate: dict[str, Any]) -> dict[str, Any]:
    params = candidate.get("trade_parameters")
    if isinstance(params, dict):
        return params
    cost = _structural_field_payload(candidate, "cost_aware_min_r_fields")
    candidate_geometry = cost.get("candidate_geometry")
    return candidate_geometry if isinstance(candidate_geometry, dict) else {}


def _fvg_ob_confluence_bucket_context(candidate: dict[str, Any]) -> dict[str, Any]:
    context = candidate.get("fvg_ob_confluence_context")
    if not isinstance(context, dict):
        return {
            "fvg_ob_confluence_bucket": None,
            "fvg_ob_confluence_bucket_source_status": "SOURCE_NOT_CAPTURED",
        }
    bucket = str(context.get("bucket") or "").lower()
    if bucket not in FVG_OB_CONFLUENCE_BUCKETS:
        return {
            "fvg_ob_confluence_bucket": bucket or None,
            "fvg_ob_confluence_bucket_source_status": "UNRECOGNIZED_FVG_OB_BUCKET",
        }
    return {
        "fvg_ob_confluence_bucket": bucket,
        "fvg_ob_confluence_bucket_source_status": "DECISION_TIME_FVG_OB_BUCKET_CAPTURED",
        "fvg_ob_confluence_bucket_source_created_at_utc": context.get("created_at_utc"),
        "fvg_ob_confluence_bucket_source_file": context.get("source_file"),
    }


def _gap_contains_price(gap: dict[str, Any], price: float | None) -> bool:
    if price is None:
        return False
    bottom = _safe_float(gap.get("bottom"))
    top = _safe_float(gap.get("top"))
    if bottom is None or top is None:
        return False
    low = min(bottom, top)
    high = max(bottom, top)
    return low <= price <= high


def standalone_fvg_poi_context(candidate: dict[str, Any]) -> dict[str, Any]:
    payload = _structural_field_payload(candidate, "standalone_fvg_entry_geometry")
    source_status = _structural_source_status(candidate, "standalone_fvg_entry_geometry")
    risk = _risk_payload(candidate)
    entry = _safe_float(payload.get("candidate_entry_price")) or _safe_float(risk.get("entry_price"))
    poi_price = _safe_float(payload.get("candidate_h1_poi_price_level"))
    poi_type = str(payload.get("candidate_h1_poi_type") or "").upper()
    selected_poi_type_source_status = source_status
    h1_setup = candidate.get("h1_setup")
    if isinstance(h1_setup, dict):
        if not poi_type:
            poi_type = str(h1_setup.get("poi_type") or "").upper()
            if poi_type:
                selected_poi_type_source_status = "DECISION_TIME_H1_SETUP_POI_TYPE_CAPTURED_ONLY"
        if poi_price is None:
            poi_price = _safe_float(h1_setup.get("poi_price_level"))
    h1_gaps = [gap for gap in payload.get("h1_fair_value_gaps") or [] if isinstance(gap, dict)]
    m15_gaps = [gap for gap in payload.get("m15_fair_value_gaps") or [] if isinstance(gap, dict)]
    matching_timeframes: list[str] = []
    for timeframe, gaps in (("H1", h1_gaps), ("M15", m15_gaps)):
        if any(_gap_contains_price(gap, entry) for gap in gaps):
            matching_timeframes.append(timeframe)
    poi_matching_timeframes: list[str] = []
    for timeframe, gaps in (("H1", h1_gaps), ("M15", m15_gaps)):
        if any(_gap_contains_price(gap, poi_price) for gap in gaps):
            poi_matching_timeframes.append(timeframe)

    entry_inside_gap = bool(matching_timeframes)
    poi_price_inside_gap = bool(poi_matching_timeframes)
    full_geometry_captured = source_status not in SOURCE_MISSING_STATUSES
    if not full_geometry_captured and poi_type and poi_type != "FVG":
        status = "NON_FVG_POI_METADATA_CAPTURED"
    elif not full_geometry_captured:
        status = "STANDALONE_FVG_POI_SOURCE_NOT_CAPTURED"
    elif poi_type != "FVG":
        status = "NON_FVG_POI_METADATA_CAPTURED"
    elif not entry_inside_gap:
        status = "FVG_POI_CAPTURED_ENTRY_NOT_INSIDE_GAP"
    else:
        status = "SELECTED_FVG_POI_ENTRY_GEOMETRY_CAPTURED"
    return {
        "standalone_fvg_source_status": source_status,
        "standalone_fvg_selected_poi_type_source_status": selected_poi_type_source_status,
        "standalone_fvg_poi_status": status,
        "standalone_fvg_poi_type": poi_type or None,
        "standalone_fvg_entry_price": _round(entry),
        "standalone_fvg_poi_price_level": _round(poi_price),
        "standalone_fvg_entry_inside_gap": entry_inside_gap,
        "standalone_fvg_poi_price_inside_gap": poi_price_inside_gap,
        "standalone_fvg_matching_gap_timeframes": matching_timeframes,
        "standalone_fvg_poi_matching_gap_timeframes": poi_matching_timeframes,
    }


def _standalone_fvg_repair_decision_status(
    *,
    strategy_id: str,
    path_status: dict[str, Any],
    fvg_context: dict[str, Any],
    repair_row: dict[str, Any],
) -> dict[str, Any]:
    proxy_reference = _safe_float(repair_row.get("after_proxy_r"))
    if proxy_reference is None:
        proxy_reference = _safe_float(repair_row.get("opportunity_proxy_r_reference"))
    audit = repair_row.get("missed_opportunity_audit")
    opportunity_paths = repair_row.get("opportunity_downstream_paths")
    return {
        "strategy_status": "REDESIGN_STANDALONE_FVG_POI_CURRENT_CLAIM_REPAIRED_REFERENCE",
        "score_status": path_status["score_status"],
        "outcome_status": path_status["outcome_status"],
        "reason": (
            "A verified action-ledger repair already scoped this selected-FVG POI row as a current-claim "
            "redesign, with any shared-path proxy preserved as reference-only rather than a standalone "
            f"FVG implementation count. {path_status['reason_suffix']}"
        ),
        "extra": {
            "outcome_source": path_status["outcome_source"],
            "branch_decision": repair_row.get("branch_decision")
            or "REDESIGN_STANDALONE_FVG_POI_SCORER_CURRENT_PROXY_NEGATIVE_SMALL_N",
            "decision_evidence": repair_row.get("decision_evidence")
            or "ACTION_LEDGER_REPAIRED_STANDALONE_FVG_CURRENT_CLAIM",
            "scoring_boundary": repair_row.get("scoring_boundary")
            or "NO_STANDALONE_FVG_DEFAULT_OFF_IMPLEMENTATION_WITH_CURRENT_SHARED_PATH_PROXY",
            "implementation_candidate": repair_row.get("implementation_candidate")
            or "REDESIGN_STANDALONE_FVG_ENTRY_SELECTOR_BEFORE_DEFAULT_OFF_IMPLEMENTATION",
            "current_action": repair_row.get("current_action"),
            "next_action": repair_row.get("next_action"),
            "implementation_decision": repair_row.get("implementation_decision"),
            "data_requirement_state": repair_row.get("data_requirement_state"),
            "coverage_status": repair_row.get("coverage_status"),
            "source_capture_surface": repair_row.get("source_capture_surface")
            or "standalone_fvg_poi_scorer",
            "standalone_fvg_current_claim_repair_status": (
                "CONSUMED_REPAIRED_ACTION_DECISION_REFERENCE_ONLY"
            ),
            "standalone_fvg_current_claim_repair_source_row_id": repair_row.get("source_row_id")
            or repair_row.get("row_id"),
            "standalone_fvg_current_claim_repair_source_artifact": repair_row.get(
                "source_artifact"
            )
            or repair_row.get("source_ledger"),
            "standalone_fvg_current_claim_proxy_r_reference": proxy_reference,
            "standalone_fvg_current_claim_proxy_reference_status": (
                "REFERENCE_ONLY_CURRENT_STANDALONE_FVG_CLAIM_NOT_COUNTED"
            ),
            "preserved_candidate_path_proxy_r": proxy_reference,
            "preserved_candidate_path_outcome_source": path_status.get("outcome_source"),
            "preserved_candidate_path_outcome_status": path_status.get("outcome_status"),
            "opportunity_preservation_status": repair_row.get("opportunity_preservation_status")
            or "STANDALONE_FVG_CURRENT_CLAIM_REDESIGN_PRESERVED",
            "opportunity_owner_row_id": repair_row.get("row_id")
            or repair_row.get("source_row_id")
            or "|".join([str(repair_row.get("candidate_id") or ""), strategy_id]),
            "opportunity_owner_source_artifact": repair_row.get("source_ledger")
            or repair_row.get("source_artifact")
            or "shadow_logs/standalone_fvg_poi_current_claim_repair_decisions.jsonl",
            "opportunity_proxy_r_reference": proxy_reference,
            "opportunity_proxy_reference_status": repair_row.get("opportunity_proxy_reference_status")
            or "REFERENCE_ONLY_CURRENT_STANDALONE_FVG_CLAIM_NOT_COUNTED",
            "opportunity_not_independently_countable_reason": repair_row.get(
                "opportunity_not_independently_countable_reason"
            )
            or "The current standalone-FVG claim is a repaired redesign/reference row, not an independent implementation count.",
            "opportunity_useful_mechanism": repair_row.get("opportunity_useful_mechanism")
            or "Standalone FVG POI intelligence remains useful as entry selector redesign, context feature, source requirement, or tighter target component.",
            "opportunity_downstream_paths": opportunity_paths
            if isinstance(opportunity_paths, list) and opportunity_paths
            else [
                "redesign",
                "context feature",
                "source requirement",
                "tighter target",
                "shorter horizon",
                "broader system component",
            ],
            "underlying_intelligence_preserved": True,
            "missed_opportunity_audit": audit if isinstance(audit, dict) else {},
            **fvg_context,
        },
    }


def _swing_protected_repair_decision_status(
    *,
    path_status: dict[str, Any],
    repair_row: dict[str, Any],
) -> dict[str, Any]:
    proxy_reference = _safe_float(repair_row.get("after_proxy_r"))
    if proxy_reference is None:
        proxy_reference = _safe_float(repair_row.get("opportunity_proxy_r_reference"))
    branch = str(repair_row.get("branch_decision") or "")
    action_class = str(repair_row.get("action_class") or "")
    proxy_counted = (
        action_class == "IMPLEMENT_DEFAULT_OFF"
        and branch.startswith("IMPLEMENT")
        and proxy_reference is not None
    )
    audit = repair_row.get("missed_opportunity_audit")
    opportunity_paths = repair_row.get("opportunity_downstream_paths")
    if proxy_counted:
        strategy_status = repair_row.get("after_strategy_status") or (
            "SCORED_SWING_PROTECTED_STOP_PROXY_SHARED_CANDIDATE_PATH"
        )
        score_status = repair_row.get("after_score_status") or path_status["score_status"]
    elif action_class == "KILL" or branch.startswith("KILL"):
        strategy_status = repair_row.get("after_strategy_status") or (
            "KILLED_SWING_PROTECTED_STOP_NOT_CONFIRMED"
        )
        score_status = "NOT_APPLICABLE_TO_ROW"
    else:
        strategy_status = repair_row.get("after_strategy_status") or (
            "REDESIGN_SWING_PROTECTED_STOP_CURRENT_CLAIM_REPAIRED_REFERENCE"
        )
        score_status = (
            "REFERENCE_ONLY_PROXY_NOT_COUNTED"
            if proxy_reference is not None
            else repair_row.get("after_score_status")
            or "SOURCE_OR_REDESIGN_REQUIRED"
        )

    reference_status = (
        "COUNTED_AS_DEFAULT_OFF_SWING_PROTECTED_PROXY_R"
        if proxy_counted
        else repair_row.get("opportunity_proxy_reference_status")
        or (
            "REFERENCE_ONLY_CURRENT_SWING_PROTECTED_CLAIM_NOT_COUNTED"
            if proxy_reference is not None
            else "NO_CURRENT_NUMERIC_PROXY_REFERENCE"
        )
    )
    return {
        "strategy_status": strategy_status,
        "score_status": score_status,
        "outcome_status": repair_row.get("after_outcome_status") or path_status["outcome_status"],
        "reason": (
            "A verified action-ledger repair already resolved this swing-protected current-claim row. "
            "Default-off implementation rows keep counted proxy R; merge/redesign/current-claim "
            f"rejection rows preserve proxy evidence as reference-only. {path_status['reason_suffix']}"
        ),
        "extra": {
            "outcome_source": repair_row.get("outcome_source") or path_status["outcome_source"],
            "strategy_proxy_r": proxy_reference if proxy_counted else None,
            "branch_decision": repair_row.get("branch_decision")
            or "REDESIGN_SWING_PROTECTED_STOP_CURRENT_CLAIM_REPAIRED_REFERENCE",
            "decision_evidence": repair_row.get("decision_evidence")
            or "ACTION_LEDGER_REPAIRED_SWING_PROTECTED_CURRENT_CLAIM",
            "scoring_boundary": repair_row.get("scoring_boundary")
            or "SWING_PROTECTED_CURRENT_CLAIM_REPAIR_CONSUMED_FROM_ACTION_LEDGER",
            "implementation_candidate": repair_row.get("implementation_candidate"),
            "current_action": repair_row.get("current_action"),
            "next_action": repair_row.get("next_action"),
            "implementation_decision": repair_row.get("implementation_decision"),
            "data_requirement_state": repair_row.get("data_requirement_state"),
            "coverage_status": repair_row.get("coverage_status"),
            "source_capture_surface": repair_row.get("source_capture_surface")
            or "swing_protected_stop_scorer",
            "swing_protected_current_claim_repair_status": (
                "CONSUMED_REPAIRED_ACTION_DECISION_COUNTED_DEFAULT_OFF_PROXY"
                if proxy_counted
                else (
                    "CONSUMED_REPAIRED_ACTION_DECISION_CURRENT_CLAIM_KILL"
                    if action_class == "KILL" or branch.startswith("KILL")
                    else "CONSUMED_REPAIRED_ACTION_DECISION_REFERENCE_ONLY"
                )
            ),
            "swing_protected_current_claim_repair_source_row_id": repair_row.get("source_row_id")
            or repair_row.get("row_id"),
            "swing_protected_current_claim_repair_source_artifact": repair_row.get(
                "source_ledger"
            )
            or repair_row.get("source_artifact"),
            "swing_protected_current_claim_proxy_r_reference": proxy_reference,
            "swing_protected_current_claim_proxy_reference_status": reference_status,
            "swing_protected_action_class": action_class,
            "swing_protected_tick_structural_derivation_repair_status": repair_row.get(
                "tick_structural_derivation_repair_status"
            ),
            "preserved_candidate_path_proxy_r": proxy_reference,
            "preserved_candidate_path_outcome_source": path_status.get("outcome_source"),
            "preserved_candidate_path_outcome_status": path_status.get("outcome_status"),
            "opportunity_preservation_status": repair_row.get("opportunity_preservation_status")
            or (
                None
                if proxy_counted
                else "SWING_PROTECTED_CURRENT_CLAIM_REPAIR_OPPORTUNITY_PRESERVED"
            ),
            "opportunity_owner_row_id": repair_row.get("row_id")
            or repair_row.get("source_row_id")
            or "|".join(
                [
                    str(repair_row.get("candidate_id") or ""),
                    SWING_PROTECTED_STRATEGY_ID,
                ]
            ),
            "opportunity_owner_source_artifact": repair_row.get("source_ledger")
            or repair_row.get("source_artifact")
            or "shadow_logs/swing_protected_stop_current_claim_repair_decisions.jsonl",
            "opportunity_proxy_r_reference": proxy_reference,
            "opportunity_proxy_reference_status": reference_status,
            "opportunity_not_independently_countable_reason": repair_row.get(
                "opportunity_not_independently_countable_reason"
            )
            or (
                "The repaired swing-protected row is counted only when it remains a default-off "
                "implementation candidate; otherwise it is preserved as current-claim rejection, "
                "avoid/inverse, context, source, or redesign intelligence."
            ),
            "opportunity_useful_mechanism": repair_row.get("opportunity_useful_mechanism")
            or "Swing-protected stop intelligence remains useful as source-repaired default-off scorer, stop-placement context, avoid filter, or broader structural component.",
            "opportunity_downstream_paths": opportunity_paths
            if isinstance(opportunity_paths, list) and opportunity_paths
            else [
                "entry-offset merge",
                "redesign",
                "avoid/inverse",
                "context feature",
                "source requirement",
                "broader system component",
            ],
            "underlying_intelligence_preserved": repair_row.get(
                "underlying_intelligence_preserved"
            )
            if repair_row.get("underlying_intelligence_preserved") is not None
            else (None if proxy_counted else True),
            "missed_opportunity_audit": audit
            if isinstance(audit, dict)
            else (None if proxy_counted else {}),
            "swing_protected_source_status": repair_row.get("swing_protected_source_status"),
            "swing_protected_stop_status": repair_row.get("swing_protected_stop_status"),
            "swing_protected_stop_side": repair_row.get("swing_protected_stop_side"),
            "swing_protected_stop_loss": repair_row.get("swing_protected_stop_loss"),
            "swing_protected_match_timeframe": repair_row.get("swing_protected_match_timeframe"),
            "swing_protected_match_price": repair_row.get("swing_protected_match_price"),
            "swing_protected_match_type": repair_row.get("swing_protected_match_type"),
            "swing_protected_match_time_utc": repair_row.get("swing_protected_match_time_utc"),
            "swing_protected_stop_distance_price": repair_row.get(
                "swing_protected_stop_distance_price"
            ),
            "swing_protected_compatible_swing_count": repair_row.get(
                "swing_protected_compatible_swing_count"
            ),
            "swing_protected_type_mismatches": repair_row.get(
                "swing_protected_type_mismatches"
            ),
        },
    }


def _nas100_depth_thinness_source_repair_status(
    *,
    repair_row: dict[str, Any],
    path_status: dict[str, Any],
) -> dict[str, Any]:
    decision_status = str(repair_row.get("source_decision_status") or "")
    feature_status = str(repair_row.get("feature_status") or "")
    features = repair_row.get("features") if isinstance(repair_row.get("features"), dict) else {}
    branch = str(repair_row.get("branch_decision") or "")
    base_extra: dict[str, Any] = {
        "branch_decision": branch,
        "decision_evidence": repair_row.get("decision_evidence")
        or "NAS100_DEPTH_THINNESS_SOURCE_REPAIR_LEDGER",
        "scoring_boundary": repair_row.get("scoring_boundary")
        or "DEPTH_CONTEXT_DIAGNOSTIC_NO_ENTRY_PROXY_R",
        "implementation_candidate": repair_row.get("implementation_candidate"),
        "depth_thinness_source_repair_status": decision_status,
        "depth_thinness_feature_status": feature_status,
        "depth_thinness_features_present": repair_row.get("features_present"),
        "depth_thinness_source_row_id": repair_row.get("row_id")
        or repair_row.get("source_row_id"),
        "depth_thinness_source_artifact": repair_row.get("source_artifact")
        or "shadow_logs/nas100_depth_thinness_current_source_repair_decisions.jsonl",
        "depth_thinness_depth_path": repair_row.get("depth_path"),
        "depth_thinness_feature_row_key": repair_row.get("feature_row_key"),
        "depth_thinness_proxy_r_reference_status": repair_row.get(
            "proxy_r_reference_status"
        )
        or "CONTEXT_DIAGNOSTIC_NOT_INDEPENDENT_ENTRY_R",
        "depth_thinness_path_proxy_r": repair_row.get("path_proxy_r"),
        "depth_thinness_path_proxy_r_basis": repair_row.get("path_proxy_r_basis"),
        "depth_thinness_pre60_depth_record_count": repair_row.get("pre60_depth_record_count"),
        "depth_thinness_event15_depth_record_count": repair_row.get("event15_depth_record_count"),
        "depth_thinness_record_count": repair_row.get("depth_record_count"),
        "depth_thinness_window_presence_status": repair_row.get("window_presence_status"),
        "depth_thinness_path_mfe_r_reference": repair_row.get(
            "path_max_favorable_r_from_entry"
        ),
        "depth_thinness_path_mae_r_reference": repair_row.get(
            "path_max_adverse_r_from_entry"
        ),
        "depth_thinness_extraction_attempt_status": repair_row.get(
            "extraction_attempt_status"
        ),
        "depth_thinness_missing_field": repair_row.get("missing_field"),
        "source_capture_surface": repair_row.get("source_capture_surface")
        or "nas100_sierra_depth_thinness_context",
        "strategy_proxy_r": None,
    }
    for field in DEPTH_THINNESS_FEATURE_FIELDS:
        base_extra[f"depth_thinness_{field}"] = features.get(field)

    if decision_status == "SIERRA_DEPTH_FEATURES_EXTRACTED_SOURCE_COMPLETE":
        if not base_extra.get("implementation_candidate"):
            base_extra["implementation_candidate"] = (
                "KEEP_DEFAULT_OFF_NAS100_DEPTH_THINNESS_CONTEXT_DIAGNOSTIC_SOURCE_COMPLETE"
            )
        return {
            "strategy_status": "SCORED_DEPTH_THINNESS_CONTEXT_SOURCE_COMPLETE",
            "score_status": "CONTEXT_ATTACHED",
            "outcome_status": path_status["outcome_status"],
            "reason": (
                "Sierra depth feature extraction is source-complete for this NAS100 current row; "
                "attach the context fields without counting standalone entry R. "
                f"{path_status['reason_suffix']}"
            ),
            "extra": base_extra,
        }

    if decision_status == "SIERRA_DEPTH_WINDOW_HAS_RECORDS_PATH_PROXY_MATERIALIZED":
        proxy_r = _safe_float(repair_row.get("path_proxy_r"))
        base_extra["strategy_proxy_r"] = proxy_r
        base_extra["proxy_r_reference_status"] = "DEPTH_WINDOW_PATH_PROXY_COUNTED"
        if not base_extra.get("implementation_candidate"):
            base_extra["implementation_candidate"] = (
                "IMPLEMENT_DEPTH_WINDOW_PRESENCE_CONTEXT_COMPARATOR_DEFAULT_OFF"
            )
        return {
            "strategy_status": "SCORED_DEPTH_THINNESS_WINDOW_PATH_PROXY",
            "score_status": "PATH_PROXY_R_MATERIALIZED",
            "outcome_status": path_status["outcome_status"],
            "reason": (
                "Sierra depth records exist inside the pre-decision window; the row now has "
                "a source-bound path proxy from the current entry-touch terminal path. "
                f"{path_status['reason_suffix']}"
            ),
            "extra": base_extra,
        }

    if decision_status == "SIERRA_DEPTH_ATTEMPTED_NO_SAMPLES_SOURCE_COMPLETE_NO_CONTEXT":
        if not base_extra.get("implementation_candidate"):
            base_extra["implementation_candidate"] = (
                "REDESIGN_NAS100_DEPTH_CONTEXT_REQUIRE_NONEMPTY_PREDECISION_DEPTH_WINDOW"
            )
        base_extra.setdefault("underlying_intelligence_preserved", True)
        base_extra.setdefault(
            "opportunity_useful_mechanism",
            "NAS100 depth-thinness context remains useful, but this current row has no source samples.",
        )
        base_extra.setdefault(
            "opportunity_downstream_paths",
            ["redesign", "source requirement", "context feature", "broader system component"],
        )
        return {
            "strategy_status": "REDESIGN_DEPTH_THINNESS_CONTEXT_NO_SAMPLES",
            "score_status": "SOURCE_COMPLETE_NO_SAMPLES",
            "outcome_status": path_status["outcome_status"],
            "reason": (
                "Sierra depth extraction ran for this row but produced no pre-decision depth samples; "
                "reject only the current row's context attachment and preserve the mechanism. "
                f"{path_status['reason_suffix']}"
            ),
            "extra": base_extra,
        }

    if not base_extra.get("implementation_candidate"):
        base_extra["implementation_candidate"] = (
            "RUN_BOUNDED_SIERRA_DEPTH_HEAVY_SCAN_OR_REGISTER_EQUIVALENT_DEPTH_SOURCE"
        )
    base_extra.setdefault("underlying_intelligence_preserved", True)
    base_extra.setdefault(
        "opportunity_useful_mechanism",
        "NAS100 depth-thinness context remains useful but needs source-safe heavy depth extraction.",
    )
    base_extra.setdefault(
        "opportunity_downstream_paths",
        ["source requirement", "context feature", "redesign", "broader system component"],
    )
    return {
        "strategy_status": "SOURCE_REQUIRED_NAS100_DEPTH_FEATURE_HEAVY_SCAN",
        "score_status": "SOURCE_REPAIR_REQUIRED",
        "outcome_status": path_status["outcome_status"],
        "reason": (
            "NAS100 Sierra depth feature extraction is not complete for this current row; "
            "the row is converted from generic waiting to an exact heavy-scan source requirement. "
            f"{path_status['reason_suffix']}"
        ),
        "extra": base_extra,
    }


def _fvg_ob_trade_record_bounds_repair_status(
    *,
    repair_row: dict[str, Any],
    path_status: dict[str, Any],
    bucket_context: dict[str, Any],
) -> dict[str, Any]:
    proxy_reference = _safe_float(repair_row.get("after_proxy_r"))
    if proxy_reference is None:
        proxy_reference = _safe_float(repair_row.get("opportunity_proxy_r_reference"))
    audit = repair_row.get("missed_opportunity_audit")
    opportunity_paths = repair_row.get("opportunity_downstream_paths")
    return {
        "strategy_status": "REDESIGN_FVG_OB_CONFLUENCE_REPAIRED_AS_FVG_ONLY_NO_OB_LEG",
        "score_status": "NOT_COUNTED_FVG_ONLY_SOURCE_REPAIR_NOT_FVG_OB_CONFLUENCE",
        "outcome_status": "NOT_SCORED",
        "reason": (
            "A verified trade-record repair recovered exact FVG bounds for this both-fire bucket, "
            "but the source record has no OB leg: OB L2 checks were skipped on the FVG-fill path. "
            "Reject only the current FVG/OB confluence claim and preserve the exact FVG intelligence "
            "as a standalone-FVG/source-capture redesign. "
            f"{path_status['reason_suffix']}"
        ),
        "extra": {
            **bucket_context,
            "outcome_source": "fvg_ob_trade_record_bounds_repair_reference_only",
            "strategy_proxy_r": None,
            "branch_decision": repair_row.get("branch_decision")
            or "REDESIGN_FVG_OB_BUCKET_REPAIRED_AS_FVG_ONLY_NO_OB_CONFLUENCE",
            "decision_evidence": repair_row.get("decision_evidence")
            or "TRADE_RECORD_L2_ENTRY_IN_FVG_PASS_WITH_OB_CHECKS_SKIPPED",
            "scoring_boundary": repair_row.get("scoring_boundary")
            or "FVG_ONLY_EXACT_BOUNDS_REPAIRED_NOT_FVG_OB_OB_AFTER_FVG_IMPLEMENTATION",
            "implementation_candidate": repair_row.get("implementation_candidate")
            or "REDESIGN_AS_FVG_ONLY_ENTRY_LOCK_OR_REQUIRE_OB_BOUNDS",
            "current_action": repair_row.get("current_action"),
            "next_action": repair_row.get("next_action"),
            "implementation_decision": repair_row.get("implementation_decision"),
            "data_requirement_state": repair_row.get("data_requirement_state"),
            "coverage_status": repair_row.get("coverage_status"),
            "source_capture_surface": repair_row.get("source_capture_surface")
            or "fvg_ob_confluence_shared_path_scorer",
            "fvg_ob_trade_record_bounds_repair_status": repair_row.get(
                "fvg_trade_record_bounds_repair_status"
            )
            or repair_row.get("source_decision_status"),
            "fvg_ob_trade_record_bounds_repair_source_row_id": repair_row.get("source_row_id")
            or repair_row.get("row_id"),
            "fvg_ob_trade_record_bounds_repair_source_artifact": repair_row.get(
                "source_ledger"
            )
            or repair_row.get("source_artifact"),
            "fvg_ob_current_claim_proxy_r_reference": proxy_reference,
            "fvg_ob_current_claim_proxy_reference_status": repair_row.get(
                "opportunity_proxy_reference_status"
            )
            or "REFERENCE_ONLY_SHARED_PATH_PROXY_NOT_FVG_OB_IMPLEMENTATION",
            "fvg_exact_bounds": repair_row.get("fvg_exact_bounds"),
            "fvg_ob_ob_leg_status": repair_row.get("ob_leg_status"),
            "fvg_ob_ob_check_statuses": repair_row.get("ob_check_statuses"),
            "fvg_ob_trade_record_source_file": repair_row.get("trade_record_source_file")
            or repair_row.get("repair_source_file"),
            "fvg_ob_trade_record_source_sha256": repair_row.get("trade_record_source_sha256")
            or repair_row.get("repair_source_sha256"),
            "preserved_candidate_path_proxy_r": proxy_reference,
            "preserved_candidate_path_outcome_source": path_status.get("outcome_source"),
            "preserved_candidate_path_outcome_status": path_status.get("outcome_status"),
            "opportunity_preservation_status": repair_row.get("opportunity_preservation_status")
            or "FVG_OB_TRADE_RECORD_BOUNDS_REPAIR_OPPORTUNITY_PRESERVED",
            "opportunity_owner_row_id": repair_row.get("row_id")
            or repair_row.get("source_row_id")
            or "|".join(
                [
                    str(repair_row.get("candidate_id") or ""),
                    FVG_OB_CONFLUENCE_ID,
                ]
            ),
            "opportunity_owner_source_artifact": repair_row.get("source_ledger")
            or repair_row.get("source_artifact")
            or "shadow_logs/fvg_ob_trade_record_bounds_current_repair_decisions.jsonl",
            "opportunity_proxy_r_reference": proxy_reference,
            "opportunity_proxy_reference_status": repair_row.get(
                "opportunity_proxy_reference_status"
            )
            or "REFERENCE_ONLY_SHARED_PATH_PROXY_NOT_FVG_OB_IMPLEMENTATION",
            "opportunity_not_independently_countable_reason": repair_row.get(
                "opportunity_not_independently_countable_reason"
            )
            or (
                "Exact FVG bounds are repaired, but the OB leg is absent in the source record; "
                "this row is not independently countable as FVG/OB confluence R."
            ),
            "opportunity_useful_mechanism": repair_row.get("opportunity_useful_mechanism")
            or (
                "Exact FVG entry geometry remains useful for standalone FVG entry-lock redesign, "
                "FVG/OB source-capture requirements, and context/avoid analysis."
            ),
            "opportunity_downstream_paths": opportunity_paths
            if isinstance(opportunity_paths, list) and opportunity_paths
            else ["redesign", "source requirement", "context feature", "broader system component"],
            "underlying_intelligence_preserved": True,
            "missed_opportunity_audit": audit if isinstance(audit, dict) else {},
        },
    }


def swing_protected_stop_context(candidate: dict[str, Any]) -> dict[str, Any]:
    payload = _structural_field_payload(candidate, "swing_protected_lock_level")
    source_status = _structural_source_status(candidate, "swing_protected_lock_level")
    risk = _risk_payload(candidate)
    side = str(candidate.get("side") or risk.get("direction") or "").upper()
    stop = _safe_float(risk.get("stop_loss"))
    compatible: list[dict[str, Any]] = []
    type_mismatches: list[str] = []
    for timeframe, key in (("H1", "h1_protected_swing"), ("M15", "m15_protected_swing")):
        swing = payload.get(key)
        if not isinstance(swing, dict):
            continue
        price = _safe_float(swing.get("price"))
        swing_type = str(swing.get("type") or "").lower()
        if price is None:
            continue
        if (side == "LONG" and swing_type == "low") or (side == "SHORT" and swing_type == "high"):
            compatible.append(
                {
                    "timeframe": timeframe,
                    "price": price,
                    "type": swing_type,
                    "time": swing.get("time"),
                }
            )
        elif swing_type:
            type_mismatches.append(f"{timeframe}:{swing_type}")

    matched: dict[str, Any] | None = None
    for swing in compatible:
        price = _safe_float(swing.get("price"))
        if side == "LONG" and stop is not None and price is not None and stop <= price:
            matched = swing
            break
        if side == "SHORT" and stop is not None and price is not None and stop >= price:
            matched = swing
            break

    if source_status in SOURCE_MISSING_STATUSES:
        status = "SWING_PROTECTED_SOURCE_NOT_CAPTURED"
    elif stop is None or side not in {"LONG", "SHORT"}:
        status = "SWING_PROTECTED_GEOMETRY_NOT_CAPTURED"
    elif matched:
        status = "SWING_PROTECTED_STOP_CONFIRMED"
    elif compatible:
        status = "STOP_DOES_NOT_PROTECT_COMPATIBLE_SWING"
    else:
        status = "NO_SIDE_COMPATIBLE_PROTECTED_SWING"

    matched_price = _safe_float((matched or {}).get("price"))
    distance = None
    if matched_price is not None and stop is not None:
        distance = matched_price - stop if side == "LONG" else stop - matched_price
    return {
        "swing_protected_source_status": source_status,
        "swing_protected_stop_status": status,
        "swing_protected_stop_side": side or None,
        "swing_protected_stop_loss": _round(stop),
        "swing_protected_match_timeframe": (matched or {}).get("timeframe"),
        "swing_protected_match_price": _round(matched_price),
        "swing_protected_match_type": (matched or {}).get("type"),
        "swing_protected_match_time_utc": (matched or {}).get("time"),
        "swing_protected_stop_distance_price": _round(distance),
        "swing_protected_compatible_swing_count": len(compatible),
        "swing_protected_type_mismatches": type_mismatches,
    }


def _price_matches(left: Any, right: Any, *, tolerance: float = 1e-6) -> bool:
    a = _safe_float(left)
    b = _safe_float(right)
    return a is not None and b is not None and abs(a - b) <= tolerance


def _candidate_limit_geometry(candidate: dict[str, Any]) -> dict[str, Any]:
    params = candidate.get("trade_parameters") or {}
    return {
        "symbol": candidate.get("symbol"),
        "side": candidate.get("side") or params.get("direction"),
        "entry_price": params.get("entry_price"),
        "stop_loss": params.get("stop_loss"),
        "take_profit_1": params.get("take_profit_1"),
    }


def _lifecycle_matches_candidate(lifecycle: dict[str, Any], candidate: dict[str, Any]) -> bool:
    cid = str(candidate.get("candidate_id") or "")
    if lifecycle.get("candidate_id"):
        return str(lifecycle.get("candidate_id")) == cid
    geometry = _candidate_limit_geometry(candidate)
    if str(lifecycle.get("symbol") or "") != str(geometry.get("symbol") or ""):
        return False
    if str(lifecycle.get("side") or "").upper() != str(geometry.get("side") or "").upper():
        return False
    return (
        _price_matches(lifecycle.get("entry_price"), geometry.get("entry_price"))
        and _price_matches(lifecycle.get("stop_loss"), geometry.get("stop_loss"))
        and _price_matches(lifecycle.get("take_profit_1"), geometry.get("take_profit_1"))
    )


def latest_lifecycle_for_candidate_asof(
    candidate: dict[str, Any],
    path_row: dict[str, Any],
    lifecycle_rows: list[dict[str, Any]],
) -> dict[str, Any] | None:
    asof = _parse_utc(path_row.get("asof_latest_candle_utc"))
    match_candidate = dict(candidate)
    if not match_candidate.get("trade_parameters") and path_row.get("trade_parameters"):
        match_candidate["trade_parameters"] = path_row.get("trade_parameters")
    best: dict[str, Any] | None = None
    best_ts: datetime | None = None
    for row in lifecycle_rows:
        if not _lifecycle_matches_candidate(row, match_candidate):
            continue
        row_ts = (
            _parse_utc(row.get("checked_candle_time_utc"))
            or _parse_utc(row.get("asof_cutoff_utc"))
            or _parse_utc(row.get("timestamp_utc"))
        )
        if row_ts is None:
            continue
        if asof is not None and row_ts > asof:
            continue
        if best_ts is None or row_ts >= best_ts:
            best = row
            best_ts = row_ts
    return best


def latest_ltf_for_candidate_asof(
    candidate: dict[str, Any],
    path_row: dict[str, Any],
    ltf_rows: list[dict[str, Any]],
) -> dict[str, Any] | None:
    cid = str(candidate.get("candidate_id") or path_row.get("candidate_id") or "")
    asof = str(path_row.get("asof_latest_candle_utc") or "")
    best: dict[str, Any] | None = None
    best_rank: tuple[int, datetime] | None = None
    for row in ltf_rows:
        if str(row.get("candidate_id") or "") != cid:
            continue
        if str(row.get("asof_latest_candle_utc") or "") != asof:
            continue
        created = _parse_utc(row.get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        terminal_status = str(row.get("terminal_outcome_status") or "")
        ltf_status = str(row.get("ltf_status") or "")
        m1_count = _safe_float(row.get("m1_bar_count")) or 0.0
        if ltf_status == "M1_PATH_RECOVERED" and terminal_status in {
            "ENTRY_THEN_TP1",
            "ENTRY_THEN_SL",
            "ENTRY_THEN_TP1_SL_SAME_M1_AMBIGUOUS",
            "ENTRY_THEN_TP1_SAME_M1_AMBIGUOUS",
            "ENTRY_THEN_SL_SAME_M1_AMBIGUOUS",
        }:
            quality = 3
        elif ltf_status == "M1_PATH_RECOVERED" and m1_count > 0:
            quality = 2
        elif terminal_status and not row.get("mt5_read_error"):
            quality = 1
        else:
            quality = 0
        rank = (quality, created)
        if best_rank is None or rank >= best_rank:
            best = row
            best_rank = rank
    return best


def pending_lifecycle_outcome_status(lifecycle: dict[str, Any]) -> tuple[str, float | None]:
    state = str(lifecycle.get("intent_after_check") or "")
    fill_label = str(lifecycle.get("fill_no_fill_label") or "")
    actual_r = _safe_float(lifecycle.get("actual_r"))
    synthetic_r = _safe_float(lifecycle.get("synthetic_path_r"))
    if state == "cancelled_wrong_side":
        return "NO_FILL_CANCELLED_WRONG_SIDE", 0.0
    if state == "cancelled_sl_too_close":
        return "NO_FILL_CANCELLED_SL_TOO_CLOSE", 0.0
    if state == "expired_48h":
        return "NO_FILL_EXPIRED", 0.0
    if state == "manual_or_system_cancelled":
        return "NO_FILL_CANCELLED", 0.0
    if state == "still_pending_no_trigger":
        return "NO_FILL_STILL_PENDING", 0.0
    if state == "triggered_tick_missing_retry":
        return "TRIGGERED_TICK_MISSING_RETRY", None
    if state == "order_send_failed_retry":
        return "TRIGGERED_ORDER_SEND_FAILED_RETRY", None
    if state == "order_send_success_filled":
        if actual_r is not None:
            return "BROKER_FILLED_ACTUAL_R_KNOWN", actual_r
        if synthetic_r is not None:
            return "BROKER_FILLED_SYNTHETIC_PATH_R_KNOWN", synthetic_r
        return "BROKER_FILLED_AWAITING_EXIT_R", None
    if fill_label.startswith("no_fill"):
        return fill_label.upper(), 0.0
    return "PENDING_LIFECYCLE_STATUS_UNKNOWN", None


def _proxy_r_for_outcome(outcome_status: str) -> float | None:
    if outcome_status == "ENTRY_TOUCHED_THEN_TP1":
        return 1.5
    if outcome_status == "ENTRY_TOUCHED_THEN_SL":
        return -1.0
    if outcome_status.startswith("NO_FILL_") or outcome_status == "NO_ENTRY_TOUCH_BY_ASOF":
        return 0.0
    return None


def resolved_path_status(path_row: dict[str, Any], ltf_row: dict[str, Any] | None = None) -> dict[str, Any]:
    base_status = path_outcome_status(path_row)
    if base_status != "M15_PATH_AMBIGUOUS_TP1_AND_SL":
        return {
            "outcome_status": base_status,
            "score_status": "COMPUTED_FROM_CANDIDATE_PATH",
            "strategy_proxy_r": _proxy_r_for_outcome(base_status),
            "outcome_source": "candidate_path_follow",
            "reason_suffix": "No lower-timeframe terminal disambiguation was required.",
        }
    if not ltf_row:
        return {
            "outcome_status": base_status,
            "score_status": "AMBIGUOUS_M15_ORDER_REQUIRES_LTF",
            "strategy_proxy_r": None,
            "outcome_source": "candidate_path_follow",
            "reason_suffix": "M15 TP/SL ambiguity has no matching LTF path-order row yet; do not count R.",
        }

    terminal_status = str(ltf_row.get("terminal_outcome_status") or "")
    if terminal_status == "ENTRY_THEN_TP1":
        return {
            "outcome_status": "ENTRY_TOUCHED_THEN_TP1",
            "score_status": "COMPUTED_FROM_LTF_PATH_ORDER",
            "strategy_proxy_r": 1.5,
            "outcome_source": "candidate_ltf_path_order",
            "reason_suffix": "M15 TP/SL ambiguity resolved by post-entry M1 terminal event: TP1 before SL.",
        }
    if terminal_status == "ENTRY_THEN_SL":
        return {
            "outcome_status": "ENTRY_TOUCHED_THEN_SL",
            "score_status": "COMPUTED_FROM_LTF_PATH_ORDER",
            "strategy_proxy_r": -1.0,
            "outcome_source": "candidate_ltf_path_order",
            "reason_suffix": "M15 TP/SL ambiguity resolved by post-entry M1 terminal event: SL before TP1.",
        }
    if terminal_status in {
        "ENTRY_THEN_TP1_SL_SAME_M1_AMBIGUOUS",
        "ENTRY_THEN_TP1_SAME_M1_AMBIGUOUS",
        "ENTRY_THEN_SL_SAME_M1_AMBIGUOUS",
    }:
        return {
            "outcome_status": terminal_status,
            "score_status": "AMBIGUOUS_LTF_ORDER",
            "strategy_proxy_r": None,
            "outcome_source": "candidate_ltf_path_order",
            "reason_suffix": "M15 ambiguity narrowed to same-M1 ordering ambiguity; do not count R without tick order.",
        }
    return {
        "outcome_status": base_status,
        "score_status": "AMBIGUOUS_M15_ORDER_REQUIRES_LTF",
        "strategy_proxy_r": None,
        "outcome_source": "candidate_ltf_path_order" if terminal_status else "candidate_path_follow",
        "reason_suffix": f"M15 TP/SL ambiguity not resolved by LTF terminal status {terminal_status!r}.",
    }


def _pending_limit_strategy_status(
    candidate: dict[str, Any],
    path_row: dict[str, Any],
    lifecycle_row: dict[str, Any] | None,
    ltf_row: dict[str, Any] | None = None,
    nofill_forward_capture_row: dict[str, Any] | None = None,
    tick_spread_reconstruction_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    final_outcome = str(candidate.get("final_outcome_at_log") or "")
    path_status = resolved_path_status(path_row, ltf_row)
    if final_outcome not in LIMIT_PLACED_OUTCOMES:
        proxy_reference = path_status["strategy_proxy_r"]
        return {
            "strategy_status": "MERGED_PENDING_LIFECYCLE_HYPOTHETICAL_PATH_PROXY_REFERENCE",
            "score_status": path_status["score_status"],
            "outcome_status": path_status["outcome_status"],
            "reason": (
                "No live limit intent existed for this candidate; preserve the hypothetical pending-limit "
                "path as reference-only entry-geometry evidence instead of counting duplicate pending "
                f"lifecycle strategy R. {path_status['reason_suffix']}"
            ),
            "extra": {
                "outcome_source": path_status["outcome_source"],
                "strategy_proxy_r": None,
                "branch_decision": "MERGE_PENDING_LIFECYCLE_HYPOTHETICAL_PATH_PROXY_TO_ENTRY_GEOMETRY_OWNER",
                "decision_evidence": (
                    "NO_LIVE_PENDING_LIMIT_INTENT_SHARED_CANDIDATE_PATH_DUPLICATE_NOT_LIFECYCLE_TRUTH"
                ),
                "scoring_boundary": (
                    "REFERENCE_ONLY_HYPOTHETICAL_PENDING_LIMIT_PATH_PROXY_NOT_LIFECYCLE_TRUTH"
                ),
                "implementation_candidate": (
                    "MERGE_HYPOTHETICAL_PENDING_LIMIT_PATH_EVIDENCE_TO_ENTRY_GEOMETRY_OWNER"
                ),
                "pending_hypothetical_merge_status": (
                    "MERGED_REFERENCE_ONLY_NO_LIVE_PENDING_LIMIT_INTENT"
                ),
                "pending_hypothetical_proxy_reference_r": proxy_reference,
                "pending_hypothetical_proxy_reference_status": (
                    "REFERENCE_ONLY_NO_LIVE_PENDING_LIMIT_INTENT_NOT_COUNTED"
                ),
                "pending_hypothetical_proxy_owner": "CANDIDATE_ENTRY_GEOMETRY_PATH",
                "preserved_candidate_path_proxy_r": proxy_reference,
                "preserved_candidate_path_outcome_source": path_status.get("outcome_source"),
                "preserved_candidate_path_outcome_status": path_status.get("outcome_status"),
                "opportunity_preservation_status": (
                    "PENDING_LIFECYCLE_HYPOTHETICAL_PATH_PROXY_MERGED"
                ),
                "opportunity_owner_row_id": "|".join(
                    [
                        str(candidate.get("candidate_id") or path_row.get("candidate_id") or ""),
                        "CANDIDATE_ENTRY_GEOMETRY_PATH",
                    ]
                ),
                "opportunity_owner_source_artifact": "candidate_path_follow",
                "opportunity_proxy_r_reference": proxy_reference,
                "opportunity_proxy_reference_status": (
                    "REFERENCE_ONLY_NO_LIVE_PENDING_LIMIT_INTENT_NOT_COUNTED"
                ),
                "opportunity_not_independently_countable_reason": (
                    "No live pending-limit intent exists for this row, so the hypothetical pending "
                    "path duplicates the candidate entry-geometry path and is not independently countable."
                ),
                "opportunity_useful_mechanism": (
                    "Hypothetical pending-limit behavior remains useful for entry-geometry redesign, "
                    "fillability/no-fill context, and source-bound pending-intent scorer design."
                ),
                "opportunity_downstream_paths": [
                    "entry-offset merge",
                    "redesign",
                    "source requirement",
                    "context feature",
                    "broader system component",
                ],
                "underlying_intelligence_preserved": True,
                "missed_opportunity_audit": {
                    "kill_scope": "NOT_KILLED_HYPOTHETICAL_PENDING_PATH_MERGED",
                    "current_claim": "PENDING_LIFECYCLE_HYPOTHETICAL_SHARED_PATH_PROXY",
                    "unsupported_reason": "NO_LIVE_PENDING_LIMIT_INTENT_FOR_LIFECYCLE_TRUTH",
                    "what_was_tried": (
                        "Checked candidate final outcome and pending lifecycle source availability."
                    ),
                    "what_could_make_it_work": (
                        "A source-bound pending intent/lifecycle row, or a distinct pending entry model "
                        "with fill/cancel/expiry truth."
                    ),
                    "preserve_as": (
                        "ENTRY_GEOMETRY_FILLABILITY_CONTEXT_OR_PENDING_INTENT_SOURCE_REQUIREMENT"
                    ),
                    "next_route": (
                        "DESIGN_SOURCE_BOUND_PENDING_ENTRY_MODEL_WITH_INTENT_LIFECYCLE_DENOMINATOR"
                    ),
                },
            },
        }
    if lifecycle_row is None:
        return {
            "strategy_status": "WAITING_FOR_PENDING_LIFECYCLE_SOURCE",
            "score_status": "WAITING_FOR_PENDING_LIFECYCLE",
            "outcome_status": "PENDING_LIFECYCLE_SOURCE_NOT_AVAILABLE",
            "reason": "The production record says a limit intent existed, but no lifecycle row matched this candidate by id or exact price geometry as of this candle.",
            "extra": {
                "outcome_source": "pending_limit_lifecycle_missing",
                "strategy_proxy_r": None,
                "branch_decision": "SOURCE_CAPTURE_REQUIRED_FOR_PENDING_LIFECYCLE_SCORER",
                "decision_evidence": "LIMIT_INTENT_PRESENT_BUT_PENDING_LIFECYCLE_ROW_NOT_MATCHED",
                "scoring_boundary": "NO_PENDING_LIFECYCLE_PROXY_R_WITHOUT_MATCHED_LIFECYCLE_SOURCE",
                "implementation_candidate": "REPAIR_PENDING_LIFECYCLE_CANDIDATE_ID_OR_PRICE_GEOMETRY_JOIN",
            },
        }
    outcome, proxy_r = pending_lifecycle_outcome_status(lifecycle_row)
    score_status = "COMPUTED_FROM_PENDING_LIFECYCLE" if proxy_r is not None else "WAITING_FOR_PENDING_LIFECYCLE_R"
    outcome_source = "pending_limit_lifecycle"
    proxy_repair_extra: dict[str, Any] = {}
    path_proxy_r = path_status.get("strategy_proxy_r")
    path_outcome = str(path_status.get("outcome_status") or "")
    if (
        outcome == "BROKER_FILLED_AWAITING_EXIT_R"
        and proxy_r is None
        and path_proxy_r is not None
        and path_outcome in {"ENTRY_TOUCHED_THEN_TP1", "ENTRY_TOUCHED_THEN_SL"}
    ):
        proxy_r = path_proxy_r
        outcome = "BROKER_FILLED_SYNTHETIC_PATH_R_REPAIRED"
        score_status = "COMPUTED_FROM_PENDING_LIFECYCLE_PATH_PROXY_REPAIR"
        outcome_source = str(path_status.get("outcome_source") or "candidate_path_follow")
        proxy_repair_extra = {
            "pending_lifecycle_r_repair_status": "FILLED_R_REPAIRED_FROM_CANDIDATE_PATH_PROXY",
            "pending_lifecycle_original_outcome_status": "BROKER_FILLED_AWAITING_EXIT_R",
            "pending_lifecycle_proxy_r_source": outcome_source,
            "pending_lifecycle_proxy_r_reference": proxy_r,
            "pending_lifecycle_broker_actual_r_status": "BROKER_ACTUAL_R_NOT_CAPTURED_PATH_PROXY_ONLY",
            "pending_lifecycle_path_proxy_outcome_status": path_outcome,
        }
    capture_extra = _pending_lifecycle_capture_extra(
        lifecycle_row,
        path_row,
        ltf_row,
        nofill_forward_capture_row,
        tick_spread_reconstruction_row,
    )
    source_statuses = capture_extra.get("pending_lifecycle_source_capture_statuses")
    derived_count = (
        sum(1 for status in source_statuses.values() if str(status).startswith("DERIVED_"))
        if isinstance(source_statuses, dict)
        else 0
    )
    if capture_extra.get("pending_lifecycle_source_capture_complete") is True and proxy_r is not None and derived_count:
        if proxy_repair_extra:
            branch_decision = "IMPLEMENT_DEFAULT_OFF_PENDING_LIFECYCLE_FILLED_PATH_PROXY_REPAIRED"
            decision_evidence = (
                "PENDING_LIFECYCLE_FILLED_BROKER_TICKET_WITH_SOURCE_SAFE_CANDIDATE_PATH_R_PROXY"
            )
            scoring_boundary = (
                "PENDING_LIFECYCLE_FILLED_PATH_PROXY_DEFAULT_OFF_NO_BROKER_ACTUAL_R_RESULT_BOUNDARY"
            )
            implementation_candidate = (
                "IMPLEMENT_DEFAULT_OFF_PENDING_LIFECYCLE_FILLED_PATH_PROXY_SCORER_WITH_ACCOUNT_R_REPAIR_FIELD"
            )
        else:
            branch_decision = "IMPLEMENT_DEFAULT_OFF_PENDING_LIFECYCLE_RECONSTRUCTED_SOURCE_SCORER"
            decision_evidence = (
                "PENDING_LIFECYCLE_INTERNAL_TRUTH_WITH_SOURCE_SAFE_RECONSTRUCTED_FIELDS_READY_FOR_DEFAULT_OFF_SCORER"
            )
            scoring_boundary = (
                "PENDING_LIFECYCLE_RECONSTRUCTED_SOURCE_FIELDS_DEFAULT_OFF_NO_EXACT_BROKER_R_RESULT_BOUNDARY"
            )
            implementation_candidate = (
                "IMPLEMENT_DEFAULT_OFF_PENDING_LIFECYCLE_INTERNAL_TRUTH_SCORER_WITH_RECONSTRUCTED_SOURCE_FIELDS"
            )
    elif capture_extra.get("pending_lifecycle_source_capture_complete") is True and proxy_r is not None:
        if proxy_repair_extra:
            branch_decision = "IMPLEMENT_DEFAULT_OFF_PENDING_LIFECYCLE_FILLED_PATH_PROXY_REPAIRED"
            decision_evidence = (
                "PENDING_LIFECYCLE_FILLED_BROKER_TICKET_WITH_SOURCE_SAFE_CANDIDATE_PATH_R_PROXY"
            )
            scoring_boundary = (
                "PENDING_LIFECYCLE_FILLED_PATH_PROXY_DEFAULT_OFF_NO_BROKER_ACTUAL_R_RESULT_BOUNDARY"
            )
            implementation_candidate = (
                "IMPLEMENT_DEFAULT_OFF_PENDING_LIFECYCLE_FILLED_PATH_PROXY_SCORER_WITH_ACCOUNT_R_REPAIR_FIELD"
            )
        else:
            branch_decision = "IMPLEMENT_DEFAULT_OFF_PENDING_LIFECYCLE_CAPTURE_COMPLETE_SCORER"
            decision_evidence = "PENDING_LIFECYCLE_INTERNAL_TRUTH_CAPTURE_FIELDS_READY_FOR_DEFAULT_OFF_SCORER"
            scoring_boundary = "PENDING_LIFECYCLE_CAPTURE_COMPLETE_DEFAULT_OFF_NO_EXACT_BROKER_R_RESULT_BOUNDARY"
            implementation_candidate = "IMPLEMENT_DEFAULT_OFF_PENDING_LIFECYCLE_INTERNAL_TRUTH_SCORER_WITH_COMPLETE_SOURCE_FIELDS"
    elif capture_extra.get("pending_lifecycle_source_capture_complete") is True:
        branch_decision = "REDESIGN_PENDING_LIFECYCLE_R_OUTCOME_SOURCE_REQUIRED"
        decision_evidence = "PENDING_LIFECYCLE_SOURCE_FIELDS_COMPLETE_BUT_R_OUTCOME_NOT_COMPUTABLE"
        scoring_boundary = "PENDING_LIFECYCLE_SOURCE_COMPLETE_BUT_R_OUTCOME_REQUIRED_BEFORE_IMPLEMENTATION"
        implementation_candidate = "REPAIR_PENDING_LIFECYCLE_FILLED_OR_RETRY_R_OUTCOME_SOURCE"
    elif derived_count:
        branch_decision = "REDESIGN_PENDING_LIFECYCLE_SOURCE_PARTIAL_REPAIR_REQUIRED"
        decision_evidence = "PENDING_LIFECYCLE_INTERNAL_TRUTH_WITH_SOURCE_SAFE_DERIVED_FIELDS"
        scoring_boundary = "PENDING_LIFECYCLE_SOURCE_FIELDS_PARTIAL_REPAIR_REQUIRED_BEFORE_IMPLEMENTATION"
        implementation_candidate = (
            "REPAIR_PENDING_LIFECYCLE_SCORER_SOURCE_FIELDS_OR_MERGE_WITH_ENTRY_GEOMETRY"
        )
    else:
        branch_decision = "REDESIGN_PENDING_LIFECYCLE_FORWARD_CAPTURE_FIELDS_PARTIAL_REPAIR_REQUIRED"
        decision_evidence = "PENDING_LIFECYCLE_INTERNAL_TRUTH_FORWARD_CAPTURE_FIELDS_PRESENT_BUT_CURRENT_ROW_PARTIAL"
        scoring_boundary = "PENDING_LIFECYCLE_FORWARD_CAPTURE_FIELDS_PARTIAL_REPAIR_REQUIRED_BEFORE_IMPLEMENTATION"
        implementation_candidate = (
            "REPAIR_PENDING_LIFECYCLE_FORWARD_CAPTURE_MISSING_SOURCE_FIELDS"
        )
    return {
        "strategy_status": "SCORED_PENDING_LIFECYCLE_INTERNAL_TRUTH",
        "score_status": score_status,
        "outcome_status": outcome,
        "reason": "Uses internal pending-limit lifecycle telemetry instead of generic M15 path because this candidate created a live limit intent.",
        "extra": {
            "outcome_source": outcome_source,
            "strategy_proxy_r": proxy_r,
            "pending_lifecycle_intent_after_check": lifecycle_row.get("intent_after_check"),
            "pending_lifecycle_fill_no_fill_label": lifecycle_row.get("fill_no_fill_label"),
            "pending_lifecycle_source_timestamp_utc": lifecycle_row.get("timestamp_utc"),
            "pending_lifecycle_checked_candle_time_utc": lifecycle_row.get("checked_candle_time_utc"),
            "pending_lifecycle_trade_id": lifecycle_row.get("trade_id"),
            "pending_lifecycle_candidate_id": lifecycle_row.get("candidate_id"),
            "pending_lifecycle_match_method": "candidate_id"
            if lifecycle_row.get("candidate_id")
            else "symbol_side_exact_price_geometry",
            "branch_decision": branch_decision,
            "decision_evidence": decision_evidence,
            "scoring_boundary": scoring_boundary,
            "implementation_candidate": implementation_candidate,
            **capture_extra,
            **proxy_repair_extra,
        },
    }


def _status_for_strategy(
    strategy: dict[str, Any],
    candidate: dict[str, Any],
    path_row: dict[str, Any],
    pending_lifecycle_row: dict[str, Any] | None = None,
    ltf_row: dict[str, Any] | None = None,
    nofill_forward_capture_row: dict[str, Any] | None = None,
    tick_spread_reconstruction_row: dict[str, Any] | None = None,
    moonshot_selected_action_source_capture_row: dict[str, Any] | None = None,
    standalone_fvg_repair_decision_row: dict[str, Any] | None = None,
    swing_protected_repair_decision_row: dict[str, Any] | None = None,
    nas100_depth_source_repair_row: dict[str, Any] | None = None,
    fvg_ob_trade_record_bounds_repair_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    strategy_id = str(strategy.get("strategy_id") or "")
    framework = str(candidate.get("framework") or "").lower()
    final_outcome = str(candidate.get("final_outcome_at_log") or "")
    path_status = resolved_path_status(path_row, ltf_row)
    sierra_status = (
        ((path_row.get("external_confluence") or {}).get("sierra") or {}).get("status")
        or ((candidate.get("external_confluence") or {}).get("sierra") or {}).get("status")
    )

    if strategy_id in CONTEXT_ONLY_IDS:
        return {
            "strategy_status": "CONTEXT_ONLY_NO_ALTERNATE_ENTRY_MODEL",
            "score_status": "NOT_AN_ENTRY_STRATEGY",
            "outcome_status": path_status["outcome_status"],
            "reason": "Policy/context comparator; preserve alongside candidate but do not synthesize an entry.",
        }
    if strategy_id in SAME_ENTRY_SCORE_IDS:
        return {
            "strategy_status": "SCORED_SHARED_CANDIDATE_PATH",
            "score_status": path_status["score_status"],
            "outcome_status": path_status["outcome_status"],
            "reason": (
                "Uses the candidate's live limit geometry and post-decision path-follow row. "
                f"{path_status['reason_suffix']}"
            ),
            "extra": {
                "outcome_source": path_status["outcome_source"],
                "strategy_proxy_r": path_status["strategy_proxy_r"],
            },
        }
    if strategy_id == PENDING_LIMIT_STRATEGY_ID:
        return _pending_limit_strategy_status(
            candidate,
            path_row,
            pending_lifecycle_row,
            ltf_row,
            nofill_forward_capture_row,
            tick_spread_reconstruction_row,
        )
    if strategy_id in OB_BOUNDARY_PROXY_IDS:
        if framework == "ob_retest":
            return {
                "strategy_status": "SCORED_OB_BOUNDARY_PROXY_SHARED_CANDIDATE_PATH",
                "score_status": path_status["score_status"],
                "outcome_status": path_status["outcome_status"],
                "reason": (
                    "Candidate is an OB-retest; current live row contains OB-boundary geometry but not "
                    f"separate V2 lock metadata. {path_status['reason_suffix']}"
                ),
                "extra": {
                    "outcome_source": path_status["outcome_source"],
                    "strategy_proxy_r": path_status["strategy_proxy_r"],
                },
            }
        return {
            "strategy_status": "NOT_APPLICABLE_NON_OB_FRAMEWORK",
            "score_status": "NOT_APPLICABLE",
            "outcome_status": "NOT_APPLICABLE",
            "reason": f"Candidate framework is {framework or 'unknown'}, not ob_retest.",
        }
    if strategy_id == FVG_OB_CONFLUENCE_ID:
        bucket_context = _fvg_ob_confluence_bucket_context(candidate)
        bucket = bucket_context.get("fvg_ob_confluence_bucket")
        if fvg_ob_trade_record_bounds_repair_row is not None:
            return _fvg_ob_trade_record_bounds_repair_status(
                repair_row=fvg_ob_trade_record_bounds_repair_row,
                path_status=path_status,
                bucket_context=bucket_context,
            )
        if bucket in {"ob_only", "fvg_only", "no_poi", "disagreement"}:
            return {
                "strategy_status": "KILLED_FVG_OB_CONFLUENCE_NOT_PRESENT",
                "score_status": "NOT_APPLICABLE_TO_ROW",
                "outcome_status": "NOT_SCORED",
                "reason": (
                    "Decision-time FVG/OB confluence bucket did not contain both FVG and OB fire; "
                    "do not require exact confluence geometry before excluding this row."
                ),
                "extra": {
                    **bucket_context,
                    "branch_decision": "KILL_ROW_NOT_FVG_OB_CONFLUENCE",
                    "decision_evidence": "DECISION_TIME_FVG_OB_BUCKET_NOT_BOTH_FVG_AND_OB_FIRE",
                    "scoring_boundary": "NO_FVG_OB_CONFLUENCE_PROXY_R_FOR_SINGLE_FAMILY_BUCKET",
                    "implementation_candidate": "KILL_FVG_OB_CONFLUENCE_SCORER_FOR_SINGLE_FAMILY_BUCKET_ROWS",
                    **_current_claim_only_preservation_extra(
                        current_claim="FVG_OB_CONFLUENCE_BOTH_FVG_AND_OB_FIRE",
                        unsupported_reason="DECISION_TIME_FVG_OB_BUCKET_NOT_BOTH_FVG_AND_OB_FIRE",
                        what_was_tried=(
                            "RECOMPUTED_FVG_OB_CONFLUENCE_BUCKET_WITH_DECISION_TIME_BUCKET_SOURCE"
                        ),
                        what_could_make_it_work=(
                            "BOTH_FVG_AND_OB_FIRE_BUCKET_WITH_EXACT_FVG_OB_BOUNDS_AND_ENTRY_LOCK_BINDING"
                        ),
                        preserve_as=(
                            "SINGLE_FAMILY_OB_OR_FVG_CONTEXT_FEATURE_AVOID_FILTER_OR_MARKET_SESSION_CANDIDATE"
                        ),
                        next_route=(
                            "ISOLATE_SINGLE_FAMILY_BUCKET_BY_SYMBOL_SESSION_TIMEFRAME_AND_TEST_AVOID_INVERSE_CONTEXT"
                        ),
                        path_status=path_status,
                    ),
                },
            }
        if bucket == "both_fvg_and_ob_fire":
            return {
                "strategy_status": "SOURCE_REQUIRED_FVG_OB_CONFLUENCE_EXACT_BOUNDS_MISSING",
                "score_status": "SOURCE_CAPTURE_REQUIRED",
                "outcome_status": "NOT_SCORED",
                "reason": (
                    "Decision-time FVG/OB bucket shows both FVG and OB fired, but exact FVG/OB bounds "
                    "and entry-lock binding are still missing; preserve the source requirement instead "
                    "of counting shared candidate-path R as FVG/OB confluence evidence."
                ),
                "extra": {
                    **bucket_context,
                    "outcome_source": "fvg_ob_confluence_bucket_source_requirement",
                    "strategy_proxy_r": None,
                    "scoring_boundary": (
                        "FVG_OB_CONFLUENCE_BUCKET_SOURCE_REQUIREMENT_EXACT_BOUNDS_MISSING"
                    ),
                    "branch_decision": "PRESERVE_FVG_OB_BUCKET_BOTH_FIRE_EXACT_BOUNDS_REQUIRED",
                    "decision_evidence": "DECISION_TIME_FVG_OB_BUCKET_BOTH_FIRE_EXACT_BOUNDS_MISSING",
                    "implementation_candidate": (
                        "PRESERVE_FVG_OB_EXACT_BOUNDS_AND_ENTRY_LOCK_SOURCE_REQUIREMENT"
                    ),
                },
            }
        if _structural_sources_available(candidate, {"standalone_fvg_entry_geometry", "fvg_lock_state"}):
            if _gbpjpy_long_adverse_cluster_applies(candidate):
                return {
                    "strategy_status": "REDESIGN_GBPJPY_LONG_FVG_OB_ADVERSE_CLUSTER",
                    "score_status": path_status["score_status"],
                    "outcome_status": path_status["outcome_status"],
                    "reason": (
                        "GBPJPY LONG rows in the current FVG/OB confluence default-off scorer cluster are "
                        "adverse in the materialized proxy ledger; preserve the row as an avoid/context "
                        f"redesign candidate. {path_status['reason_suffix']}"
                    ),
                    "extra": _gbpjpy_long_adverse_cluster_extra(
                        path_status,
                        strategy_id=strategy_id,
                        path_row=path_row,
                    ),
                }
            return {
                "strategy_status": "SCORED_FVG_OB_CONFLUENCE_PROXY_SHARED_CANDIDATE_PATH",
                "score_status": path_status["score_status"],
                "outcome_status": path_status["outcome_status"],
                "reason": (
                    "Decision-time FVG/OB confluence metadata is captured; score the confluence bucket with "
                    "the candidate's live limit geometry and post-decision path row. This is not a standalone "
                    f"FVG-entry scorer. {path_status['reason_suffix']}"
                ),
                "extra": {
                    "outcome_source": path_status["outcome_source"],
                    "strategy_proxy_r": path_status["strategy_proxy_r"],
                    "scoring_boundary": "FVG_OB_CONFLUENCE_SHARED_CANDIDATE_PATH_PROXY_NOT_STANDALONE_FVG_ENTRY",
                    "branch_decision": "IMPLEMENT_DEFAULT_OFF_FVG_OB_CONFLUENCE_CAPTURED_METADATA_SHARED_PATH_SCORER",
                    "decision_evidence": (
                        "CAPTURED_FVG_OB_CONFLUENCE_METADATA_SCORED_WITH_SHARED_CANDIDATE_PATH_PROXY"
                    ),
                    "implementation_candidate": (
                        "IMPLEMENT_DEFAULT_OFF_FVG_OB_CONFLUENCE_SHARED_PATH_PROXY_SCORER"
                    ),
                },
            }
        return {
            "strategy_status": "NOT_COMPUTABLE_MISSING_FVG_ENTRY_OR_LOCK_METADATA",
            "score_status": "MISSING_REQUIRED_LIVE_METADATA",
            "outcome_status": "NOT_SCORED",
            "reason": "Live candidate/path rows do not yet contain a standalone FVG entry, FVG lock, and post-lock reentry state.",
            "extra": _fvg_scorer_blocker_extra(captured_metadata=False),
        }
    if strategy_id == PREFILL_DELIVERY_STRATEGY_ID:
        return _prefill_delivery_strategy_status(candidate, path_row)
    if strategy_id == ENTRY_OFFSET_050R_STRATEGY_ID:
        return _entry_offset_050r_strategy_status(candidate, path_row)
    if strategy_id in FVG_REQUIRED_IDS:
        fvg_context = standalone_fvg_poi_context(candidate)
        if standalone_fvg_repair_decision_row is not None:
            return _standalone_fvg_repair_decision_status(
                strategy_id=strategy_id,
                path_status=path_status,
                fvg_context=fvg_context,
                repair_row=standalone_fvg_repair_decision_row,
            )
        if fvg_context["standalone_fvg_poi_status"] == "NON_FVG_POI_METADATA_CAPTURED":
            return {
                "strategy_status": "KILLED_STANDALONE_FVG_POI_NOT_SELECTED",
                "score_status": "NOT_APPLICABLE_TO_ROW",
                "outcome_status": "NOT_SCORED",
                "reason": (
                    "Decision-time selected H1 POI type is not FVG; do not require full FVG lock "
                    "metadata before excluding this row from the standalone FVG scorer."
                ),
                "extra": {
                    "branch_decision": "KILL_ROW_NOT_STANDALONE_FVG_POI",
                    "decision_evidence": "SELECTED_POI_TYPE_IS_NOT_FVG",
                    "scoring_boundary": "NO_STANDALONE_FVG_PROXY_R_FOR_NON_FVG_SELECTED_POI",
                    "implementation_candidate": (
                        "KILL_STANDALONE_FVG_SCORER_FOR_NON_FVG_POI_ROWS_REDESIGN_FVG_RESCUE_SELECTOR"
                    ),
                    **_current_claim_only_preservation_extra(
                        current_claim="STANDALONE_FVG_SELECTED_POI_ENTRY",
                        unsupported_reason="SELECTED_POI_TYPE_IS_NOT_FVG",
                        what_was_tried=(
                            "RECOMPUTED_STANDALONE_FVG_SELECTOR_AGAINST_DECISION_TIME_POI_TYPE_AND_FVG_GEOMETRY"
                        ),
                        what_could_make_it_work=(
                            "SELECTED_FVG_POI_WITH_ENTRY_BOUND_TO_CAPTURED_FVG_AND_LOCK_PATH_FIELDS"
                        ),
                        preserve_as=(
                            "NON_FVG_POI_CONTEXT_FEATURE_OR_REDESIGN_SOURCE_FOR_OB_FVG_SWITCHING"
                        ),
                        next_route=(
                            "MERGE_NON_FVG_SELECTED_POI_ROWS_INTO_OB_CONTEXT_OR_FVG_SELECTOR_REDESIGN_AUDIT"
                        ),
                        path_status=path_status,
                    ),
                    **fvg_context,
                },
            }
        if _structural_sources_available(candidate, {"standalone_fvg_entry_geometry", "fvg_lock_state"}):
            if fvg_context["standalone_fvg_poi_status"] == "SELECTED_FVG_POI_ENTRY_GEOMETRY_CAPTURED":
                return {
                    "strategy_status": "SCORED_STANDALONE_FVG_POI_PROXY_CANDIDATE_PATH",
                    "score_status": path_status["score_status"],
                    "outcome_status": path_status["outcome_status"],
                    "reason": (
                        "Decision-time structural metadata shows the selected H1 POI is an FVG and the "
                        "candidate entry is inside captured FVG geometry; score this default-off standalone "
                        "FVG-POI bucket with the candidate path. This does not synthesize an alternate FVG "
                        f"entry. {path_status['reason_suffix']}"
                    ),
                    "extra": {
                        "outcome_source": path_status["outcome_source"],
                        "strategy_proxy_r": path_status["strategy_proxy_r"],
                        "scoring_boundary": "FVG_POI_CANDIDATE_PATH_PROXY_NO_ALTERNATE_ENTRY_SYNTHESIS",
                        "branch_decision": "IMPLEMENT_SHADOW_SCORER_STANDALONE_FVG_POI_DEFAULT_OFF",
                        "decision_evidence": (
                            "SELECTED_FVG_POI_ENTRY_GEOMETRY_CAPTURED_AND_SCORED_WITH_CANDIDATE_PATH"
                        ),
                        "implementation_candidate": (
                            "IMPLEMENT_DEFAULT_OFF_STANDALONE_FVG_POI_PATH_SCORER_NOW"
                        ),
                        **fvg_context,
                    },
                }
            return {
                "strategy_status": "REDESIGN_REQUIRED_FVG_POI_ENTRY_NOT_BOUND_TO_GAP",
                "score_status": "NOT_COMPUTABLE",
                "outcome_status": "NOT_SCORED",
                "reason": (
                    "FVG metadata was captured, but the selected FVG POI cannot be bound to a captured gap "
                    "containing the candidate entry; preserve the row as a selector-redesign branch."
                ),
                "extra": {
                    "branch_decision": "REDESIGN_FVG_ENTRY_SELECTOR_REQUIRED",
                    "decision_evidence": "FVG_POI_PRESENT_BUT_ENTRY_NOT_BOUND_TO_CAPTURED_GAP",
                    "scoring_boundary": "NO_FVG_PROXY_R_WITHOUT_SELECTED_FVG_ENTRY_BOUND_TO_GAP",
                    "implementation_candidate": "REDESIGN_FVG_ENTRY_SELECTOR_AND_LOCK_BINDING",
                    **fvg_context,
                },
            }
        return {
            "strategy_status": "NOT_COMPUTABLE_MISSING_FVG_ENTRY_OR_LOCK_METADATA",
            "score_status": "MISSING_REQUIRED_LIVE_METADATA",
            "outcome_status": "NOT_SCORED",
            "reason": "Live candidate/path rows do not yet contain a standalone FVG entry, FVG lock, and post-lock reentry state.",
            "extra": {**_fvg_scorer_blocker_extra(captured_metadata=False), **fvg_context},
        }
    if strategy_id in STRUCTURAL_LOCK_REQUIRED_IDS:
        if strategy_id == SWING_PROTECTED_STRATEGY_ID:
            if swing_protected_repair_decision_row is not None:
                return _swing_protected_repair_decision_status(
                    path_status=path_status,
                    repair_row=swing_protected_repair_decision_row,
                )
            swing_context = swing_protected_stop_context(candidate)
            if swing_context["swing_protected_stop_status"] == "SWING_PROTECTED_STOP_CONFIRMED":
                if _gbpjpy_long_adverse_cluster_applies(candidate):
                    return {
                        "strategy_status": "REDESIGN_GBPJPY_LONG_SWING_PROTECTED_ADVERSE_CLUSTER",
                        "score_status": path_status["score_status"],
                        "outcome_status": path_status["outcome_status"],
                        "reason": (
                            "GBPJPY LONG rows in the current swing-protected default-off scorer cluster are "
                            "adverse in the materialized proxy ledger; preserve the row as an avoid/context "
                            f"redesign candidate. {path_status['reason_suffix']}"
                        ),
                        "extra": {
                            **_gbpjpy_long_adverse_cluster_extra(
                                path_status,
                                strategy_id=strategy_id,
                                path_row=path_row,
                            ),
                            **swing_context,
                        },
                    }
                return {
                    "strategy_status": "SCORED_SWING_PROTECTED_STOP_PROXY_SHARED_CANDIDATE_PATH",
                    "score_status": path_status["score_status"],
                    "outcome_status": path_status["outcome_status"],
                    "reason": (
                        "Decision-time structural metadata confirms the candidate stop protects a captured "
                        "side-compatible swing; score this default-off swing-protected-stop bucket with the "
                        f"candidate path. {path_status['reason_suffix']}"
                    ),
                    "extra": {
                        "outcome_source": path_status["outcome_source"],
                        "strategy_proxy_r": path_status["strategy_proxy_r"],
                        "scoring_boundary": "SWING_PROTECTED_STOP_CANDIDATE_PATH_PROXY_NOT_LOCK_REENTRY",
                        "branch_decision": "IMPLEMENT_DEFAULT_OFF_SWING_PROTECTED_STOP_CAPTURED_METADATA_SCORER",
                        "decision_evidence": "CANDIDATE_STOP_PROTECTS_CAPTURED_SIDE_COMPATIBLE_SWING",
                        "implementation_candidate": (
                            "IMPLEMENT_DEFAULT_OFF_SWING_PROTECTED_STOP_PATH_SCORER_NOW"
                        ),
                        **swing_context,
                    },
                }
            if swing_context["swing_protected_stop_status"] in {
                "STOP_DOES_NOT_PROTECT_COMPATIBLE_SWING",
                "NO_SIDE_COMPATIBLE_PROTECTED_SWING",
            }:
                return {
                    "strategy_status": "KILLED_SWING_PROTECTED_STOP_NOT_CONFIRMED",
                    "score_status": "NOT_APPLICABLE_TO_ROW",
                    "outcome_status": "NOT_SCORED",
                    "reason": (
                        "A protected-swing source exists, but the candidate stop does not protect a "
                        "side-compatible swing; do not grant V2 swing-protected proxy R to this row."
                    ),
                    "extra": {
                        "branch_decision": "KILL_ROW_NOT_SWING_PROTECTED_STOP",
                        "decision_evidence": swing_context["swing_protected_stop_status"],
                        "scoring_boundary": "NO_SWING_PROTECTED_PROXY_R_UNLESS_STOP_PROTECTS_SWING",
                        "implementation_candidate": (
                            "KILL_SWING_PROTECTED_ROW_USE_ONLY_CONFIRMED_STOP_PROTECTS_SWING"
                        ),
                        **_current_claim_only_preservation_extra(
                            current_claim="SWING_PROTECTED_STOP_SCORER",
                            unsupported_reason=swing_context["swing_protected_stop_status"],
                            what_was_tried=(
                                "CHECKED_CANDIDATE_STOP_AGAINST_CAPTURED_SIDE_COMPATIBLE_PROTECTED_SWING"
                            ),
                            what_could_make_it_work=(
                                "STOP_PROTECTS_SIDE_COMPATIBLE_SWING_OR_REDESIGNED_SWING_LEVEL_BINDING"
                            ),
                            preserve_as="SWING_DISTANCE_STOP_PLACEMENT_CONTEXT_OR_AVOID_FILTER",
                            next_route=(
                                "ISOLATE_SWING_PROTECTION_FAILURE_BY_SYMBOL_SESSION_SIDE_AND_REDESIGN_STOP_LEVEL_BINDING"
                            ),
                            path_status=path_status,
                        ),
                        **swing_context,
                    },
                }
            return {
                "strategy_status": "NOT_COMPUTABLE_MISSING_SWING_PROTECTED_STOP_METADATA",
                "score_status": "MISSING_REQUIRED_LIVE_METADATA",
                "outcome_status": "NOT_SCORED",
                "reason": "Swing-protected-stop scorer requires protected swing and candidate stop geometry.",
                "extra": {
                    **_structural_scorer_blocker_extra(captured_metadata=False),
                    **swing_context,
                },
            }
        if _structural_sources_available(
            candidate,
            {
                "structural_lock_event_time_price",
                "post_lock_reentry_state",
                "cost_aware_min_r_fields",
            },
        ):
            if strategy_id in DUPLICATE_STRUCTURAL_SHARED_PATH_IDS:
                return {
                    "strategy_status": "REDESIGN_DUPLICATE_STRUCTURAL_LOCK_SHARED_PATH_PROXY",
                    "score_status": path_status["score_status"],
                    "outcome_status": path_status["outcome_status"],
                    "reason": (
                        "Decision-time structural lock metadata is captured, but this V3 strategy currently "
                        "shares the same candidate-path proxy as the canonical structural metadata scorer. "
                        "Preserve the proxy R as evidence and redesign a distinct lock-reentry/cost-aware "
                        f"scorer before treating it as a separate implementation candidate. {path_status['reason_suffix']}"
                    ),
                    "extra": _duplicate_structural_shared_path_extra(path_status),
                }
            if _gbpjpy_long_adverse_cluster_applies(candidate):
                return {
                    "strategy_status": "REDESIGN_GBPJPY_LONG_STRUCTURAL_LOCK_ADVERSE_CLUSTER",
                    "score_status": path_status["score_status"],
                    "outcome_status": path_status["outcome_status"],
                    "reason": (
                        "GBPJPY LONG rows in the current structural-lock default-off scorer cluster are "
                        "adverse in the materialized proxy ledger; preserve the row as an avoid/context "
                        f"redesign candidate. {path_status['reason_suffix']}"
                    ),
                    "extra": _gbpjpy_long_adverse_cluster_extra(
                        path_status,
                        strategy_id=strategy_id,
                        path_row=path_row,
                    ),
                }
            return {
                "strategy_status": "SCORED_STRUCTURAL_LOCK_METADATA_PROXY_SHARED_CANDIDATE_PATH",
                "score_status": path_status["score_status"],
                "outcome_status": path_status["outcome_status"],
                "reason": (
                    "Decision-time structural lock metadata is captured; score this default-off structural "
                    "metadata bucket with the candidate's live limit geometry and post-decision path row. "
                    "This is not an alternate lock-reentry scorer. "
                    f"{path_status['reason_suffix']}"
                ),
                "extra": _metadata_shared_path_extra(kind="structural", path_status=path_status),
            }
        return {
            "strategy_status": "NOT_COMPUTABLE_MISSING_STRUCTURAL_LOCK_METADATA",
            "score_status": "MISSING_REQUIRED_LIVE_METADATA",
            "outcome_status": "NOT_SCORED",
            "reason": "V2/V3 structural variants require lock-time metadata not present in the current live candidate rows.",
            "extra": _structural_scorer_blocker_extra(captured_metadata=False),
        }
    if strategy_id == NAS100_DEPTH_THINNESS_STRATEGY_ID:
        if str(candidate.get("symbol") or "").upper() == "NAS100":
            if nas100_depth_source_repair_row is not None:
                return _nas100_depth_thinness_source_repair_status(
                    repair_row=nas100_depth_source_repair_row,
                    path_status=path_status,
                )
            status = "SCORED_CONTEXT_ATTACHED" if sierra_status == "FEATURES_EXTRACTED" else "WAITING_FOR_DEPTH_FEATURES"
            return {
                "strategy_status": status,
                "score_status": "CONTEXT_ATTACHED" if sierra_status == "FEATURES_EXTRACTED" else "WAITING",
                "outcome_status": path_status["outcome_status"],
                "reason": f"Sierra depth status is {sierra_status!r}; no Databento paid fetch attempted.",
            }
        return {
            "strategy_status": "NOT_APPLICABLE_SYMBOL_SPECIFIC",
            "score_status": "NOT_APPLICABLE",
            "outcome_status": "NOT_APPLICABLE",
            "reason": "NQ depth diagnostic only applies to NAS100.",
        }
    if strategy_id in MOONSHOT_SELECTED_ACTION_STRATEGY_IDS:
        return _moonshot_selected_action_status(
            strategy,
            candidate,
            path_row,
            moonshot_selected_action_source_capture_row,
        )
    return {
        "strategy_status": "REGISTERED_NO_SCORER_IMPLEMENTED",
        "score_status": "NOT_COMPUTABLE",
        "outcome_status": "NOT_SCORED",
        "reason": "Strategy id is registered but has no live mechanical scorer mapping.",
    }


def _m15_path_provenance_status(path_row: dict[str, Any]) -> str:
    spread_status = str(path_row.get("m15_spread_source_status") or "")
    tick_status = str(path_row.get("m15_tick_volume_source_status") or "")
    real_status = str(path_row.get("m15_real_volume_source_status") or "")
    if spread_status == "SPREAD_CAPTURED":
        return "M15_SPREAD_SOURCE_CAPTURED"
    if tick_status == "TICK_VOLUME_CAPTURED" or real_status == "REAL_VOLUME_CAPTURED":
        return "M15_VOLUME_ONLY_SOURCE_CAPTURED"
    if spread_status or tick_status or real_status:
        return "M15_PATH_PROVENANCE_PRESENT_NO_SPREAD_OR_VOLUME"
    return "M15_PATH_PROVENANCE_NOT_CAPTURED"


def build_strategy_outcome_rows(
    candidate: dict[str, Any],
    path_row: dict[str, Any],
    *,
    pending_lifecycle_row: dict[str, Any] | None = None,
    ltf_row: dict[str, Any] | None = None,
    nofill_forward_capture_row: dict[str, Any] | None = None,
    tick_spread_reconstruction_row: dict[str, Any] | None = None,
    moonshot_selected_action_source_capture: dict[tuple[str, str], dict[str, Any]] | None = None,
    standalone_fvg_repair_decisions: dict[tuple[str, str], dict[str, Any]] | None = None,
    swing_protected_repair_decisions: dict[tuple[str, str], dict[str, Any]] | None = None,
    nas100_depth_source_repairs: dict[tuple[str, str], dict[str, Any]] | None = None,
    fvg_ob_trade_record_bounds_repairs: dict[tuple[str, str], dict[str, Any]] | None = None,
    created_at_utc: str | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    metrics = entry_reference_metrics(path_row)
    redesign_context = entry_retest_redesign_context(candidate, path_row)
    now = created_at_utc or utc_now_iso()
    for strategy in _snapshot_map(candidate):
        status = _status_for_strategy(
            strategy,
            candidate,
            path_row,
            pending_lifecycle_row,
            ltf_row,
            nofill_forward_capture_row,
            tick_spread_reconstruction_row,
            (moonshot_selected_action_source_capture or {}).get(
                (str(candidate.get("candidate_id") or ""), str(strategy.get("strategy_id") or ""))
            ),
            (standalone_fvg_repair_decisions or {}).get(
                (str(candidate.get("candidate_id") or ""), str(strategy.get("strategy_id") or ""))
            ),
            (swing_protected_repair_decisions or {}).get(
                (str(candidate.get("candidate_id") or ""), str(strategy.get("strategy_id") or ""))
            ),
            (nas100_depth_source_repairs or {}).get(
                (str(candidate.get("candidate_id") or ""), str(strategy.get("strategy_id") or ""))
            ),
            (fvg_ob_trade_record_bounds_repairs or {}).get(
                (str(candidate.get("candidate_id") or ""), str(strategy.get("strategy_id") or ""))
            ),
        )
        extra = status.get("extra") if isinstance(status.get("extra"), dict) else {}
        branch_decision = extra.get("branch_decision") or strategy.get("branch_decision")
        decision_evidence = extra.get("decision_evidence") or strategy.get("decision_evidence")
        row = {
            "schema_version": SCHEMA_VERSION,
            "created_at_utc": now,
            "evidence_class": "FORWARD_SHADOW_PATH_FOLLOW",
            "candidate_id": candidate.get("candidate_id") or path_row.get("candidate_id"),
            "trade_id": candidate.get("trade_id") or path_row.get("trade_id"),
            "symbol": candidate.get("symbol") or path_row.get("symbol"),
            "broker_symbol": candidate.get("broker_symbol") or path_row.get("broker_symbol"),
            "route_session": (
                candidate.get("route_session")
                or candidate.get("session")
                or candidate.get("session_tag")
                or candidate.get("kill_zone")
                or path_row.get("route_session")
                or path_row.get("session")
                or path_row.get("session_tag")
                or path_row.get("kill_zone")
            ),
            "decision_time_utc": candidate.get("decision_time_utc") or path_row.get("decision_time_utc"),
            "asof_latest_candle_utc": path_row.get("asof_latest_candle_utc"),
            "side": candidate.get("side") or path_row.get("side"),
            "framework": candidate.get("framework") or path_row.get("framework"),
            "candidate_final_outcome_at_log": candidate.get("final_outcome_at_log")
            or path_row.get("final_outcome_at_candidate_log"),
            "strategy_id": strategy.get("strategy_id"),
            "strategy_family": strategy.get("family"),
            "strategy_evidence_role": strategy.get("evidence_role"),
            "strategy_applicability": strategy.get("applicability"),
            "strategy_status": status["strategy_status"],
            "score_status": status["score_status"],
            "outcome_status": status["outcome_status"],
            "status_reason": status["reason"],
            **extra,
            "branch_decision": branch_decision,
            "decision_evidence": decision_evidence,
            "path_label": path_row.get("path_label"),
            "touched_entry": path_row.get("touched_entry"),
            "hit_tp1": path_row.get("hit_tp1"),
            "hit_sl": path_row.get("hit_sl"),
            "bars_elapsed": path_row.get("bars_elapsed"),
            "ltf_path_order_label": (ltf_row or {}).get("path_order_label"),
            "ltf_terminal_outcome_status": (ltf_row or {}).get("terminal_outcome_status"),
            "ltf_terminal_event_utc": (ltf_row or {}).get("terminal_event_utc"),
            "ltf_terminal_order_ambiguity": (ltf_row or {}).get("terminal_order_ambiguity"),
            "entry_touch_distance_status": redesign_context["entry_touch_distance_status"],
            "nearest_abs_distance_to_entry": path_row.get("nearest_abs_distance_to_entry"),
            "nearest_distance_to_entry_r": redesign_context["nearest_distance_to_entry_r"],
            "entry_retest_redesign_bucket": redesign_context["entry_retest_redesign_bucket"],
            "entry_retest_redesign_bucket_basis": redesign_context[
                "entry_retest_redesign_bucket_basis"
            ],
            "entry_retest_redesign_fill_claim_status": redesign_context[
                "entry_retest_redesign_fill_claim_status"
            ],
            "entry_retest_redesign_tick_replay_requirement": redesign_context[
                "entry_retest_redesign_tick_replay_requirement"
            ],
            "max_favorable_r_from_entry": metrics.get("max_favorable_r_from_entry"),
            "max_adverse_r_from_entry": metrics.get("max_adverse_r_from_entry"),
            "m15_path_provenance_status": _m15_path_provenance_status(path_row),
            "m15_spread_source_status": path_row.get("m15_spread_source_status"),
            "m15_spread_count": path_row.get("m15_spread_count"),
            "m15_spread_min": path_row.get("m15_spread_min"),
            "m15_spread_max": path_row.get("m15_spread_max"),
            "m15_spread_mean": path_row.get("m15_spread_mean"),
            "m15_tick_volume_source_status": path_row.get("m15_tick_volume_source_status"),
            "m15_tick_volume_count": path_row.get("m15_tick_volume_count"),
            "m15_tick_volume_min": path_row.get("m15_tick_volume_min"),
            "m15_tick_volume_max": path_row.get("m15_tick_volume_max"),
            "m15_tick_volume_mean": path_row.get("m15_tick_volume_mean"),
            "m15_real_volume_source_status": path_row.get("m15_real_volume_source_status"),
            "m15_real_volume_count": path_row.get("m15_real_volume_count"),
            "m15_real_volume_min": path_row.get("m15_real_volume_min"),
            "m15_real_volume_max": path_row.get("m15_real_volume_max"),
            "m15_real_volume_mean": path_row.get("m15_real_volume_mean"),
            "path_metrics": metrics,
            "source_candidate_created_at_utc": candidate.get("created_at_utc"),
            "source_path_created_at_utc": path_row.get("created_at_utc"),
            "source_file": "candidate_path_follow+strategy_follow_candidates",
            "no_leak_status": "POST_DECISION_FORWARD_OBSERVATION_NOT_DECISION_FEATURE",
            "manual_backfill_status": "BACKFILLED_OR_REFRESHED_FROM_LIVE_SHADOW_ROWS",
            "no_ai_calls": True,
            "no_canary_required": True,
            "paid_fetch_attempted": False,
        }
        _complete_opportunity_preservation_fields(row)
        enrich_cp281_event_contract_fields(row, source_path=DEFAULT_OUTPUT)
        rows.append(row)
    return rows


CORRECTION_FIELDS = (
    "strategy_status",
    "score_status",
    "outcome_status",
    "status_reason",
    "outcome_source",
    "strategy_proxy_r",
    "pending_lifecycle_intent_after_check",
    "pending_lifecycle_fill_no_fill_label",
    "pending_lifecycle_source_timestamp_utc",
    "pending_lifecycle_checked_candle_time_utc",
    "ltf_path_order_label",
    "ltf_terminal_outcome_status",
    "ltf_terminal_event_utc",
    "ltf_terminal_order_ambiguity",
    "entry_touch_distance_status",
    "nearest_abs_distance_to_entry",
    "nearest_distance_to_entry_r",
    "entry_retest_redesign_bucket",
    "entry_retest_redesign_bucket_basis",
    "entry_retest_redesign_fill_claim_status",
    "entry_retest_redesign_tick_replay_requirement",
    "pending_hypothetical_merge_status",
    "pending_hypothetical_proxy_reference_r",
    "pending_hypothetical_proxy_reference_status",
    "pending_hypothetical_proxy_owner",
    "max_favorable_r_from_entry",
    "max_adverse_r_from_entry",
    "branch_decision",
    "decision_evidence",
    "scoring_boundary",
    "implementation_candidate",
    "implementation_decision",
    "current_action",
    "next_action",
    "coverage_status",
    "data_requirement_state",
    "source_capture_surface",
    "fvg_ob_confluence_bucket",
    "fvg_ob_confluence_bucket_source_status",
    "fvg_ob_confluence_bucket_source_created_at_utc",
    "fvg_ob_confluence_bucket_source_file",
    "fvg_ob_trade_record_bounds_repair_status",
    "fvg_ob_trade_record_bounds_repair_source_row_id",
    "fvg_ob_trade_record_bounds_repair_source_artifact",
    "fvg_ob_current_claim_proxy_r_reference",
    "fvg_ob_current_claim_proxy_reference_status",
    "fvg_exact_bounds",
    "fvg_ob_ob_leg_status",
    "fvg_ob_ob_check_statuses",
    "fvg_ob_trade_record_source_file",
    "fvg_ob_trade_record_source_sha256",
    "standalone_fvg_source_status",
    "standalone_fvg_selected_poi_type_source_status",
    "standalone_fvg_poi_status",
    "standalone_fvg_poi_type",
    "standalone_fvg_entry_price",
    "standalone_fvg_poi_price_level",
    "standalone_fvg_entry_inside_gap",
    "standalone_fvg_poi_price_inside_gap",
    "standalone_fvg_matching_gap_timeframes",
    "standalone_fvg_poi_matching_gap_timeframes",
    "standalone_fvg_current_claim_repair_status",
    "standalone_fvg_current_claim_repair_source_row_id",
    "standalone_fvg_current_claim_repair_source_artifact",
    "standalone_fvg_current_claim_proxy_r_reference",
    "standalone_fvg_current_claim_proxy_reference_status",
    "swing_protected_source_status",
    "swing_protected_stop_status",
    "swing_protected_stop_side",
    "swing_protected_stop_loss",
    "swing_protected_match_timeframe",
    "swing_protected_match_price",
    "swing_protected_match_type",
    "swing_protected_match_time_utc",
    "swing_protected_stop_distance_price",
    "swing_protected_compatible_swing_count",
    "swing_protected_type_mismatches",
    "swing_protected_current_claim_repair_status",
    "swing_protected_current_claim_repair_source_row_id",
    "swing_protected_current_claim_repair_source_artifact",
    "swing_protected_current_claim_proxy_r_reference",
    "swing_protected_current_claim_proxy_reference_status",
    "swing_protected_action_class",
    "swing_protected_tick_structural_derivation_repair_status",
    "structural_duplicate_merge_status",
    "structural_duplicate_proxy_owner_strategy_id",
    "structural_duplicate_proxy_reference_r",
    "structural_duplicate_proxy_reference_status",
    "depth_thinness_source_repair_status",
    "depth_thinness_feature_status",
    "depth_thinness_features_present",
    "depth_thinness_source_row_id",
    "depth_thinness_source_artifact",
    "depth_thinness_depth_path",
    "depth_thinness_feature_row_key",
    "depth_thinness_proxy_r_reference_status",
    "depth_thinness_path_proxy_r",
    "depth_thinness_path_proxy_r_basis",
    "depth_thinness_pre60_depth_record_count",
    "depth_thinness_event15_depth_record_count",
    "depth_thinness_record_count",
    "depth_thinness_window_presence_status",
    "depth_thinness_path_mfe_r_reference",
    "depth_thinness_path_mae_r_reference",
    "depth_thinness_extraction_attempt_status",
    "depth_thinness_missing_field",
    "depth_thinness_pre60_median_total_depth10",
    "depth_thinness_pre60_median_depth10_imbalance",
    "depth_thinness_event15_median_total_depth10",
    "depth_thinness_event15_thin_depth10_rate",
    "depth_thinness_event15_median_depth10_imbalance",
    "depth_thinness_event15_median_near_far_ratio",
    "depth_thinness_event15_median_max_bid_wall",
    "depth_thinness_event15_median_max_ask_wall",
    "depth_thinness_event15_sample_count",
    "m15_path_provenance_status",
    "m15_spread_source_status",
    "m15_spread_count",
    "m15_spread_min",
    "m15_spread_max",
    "m15_spread_mean",
    "m15_tick_volume_source_status",
    "m15_tick_volume_count",
    "m15_tick_volume_min",
    "m15_tick_volume_max",
    "m15_tick_volume_mean",
    "m15_real_volume_source_status",
    "m15_real_volume_count",
    "m15_real_volume_min",
    "m15_real_volume_max",
    "m15_real_volume_mean",
    "pending_lifecycle_source_capture_contract",
    "pending_lifecycle_pending_horizon_start_utc",
    "pending_lifecycle_pending_horizon_end_utc",
    "pending_lifecycle_cancel_expiry_reason_status",
    "pending_lifecycle_decision_spread_value_source_safe",
    "pending_lifecycle_decision_spread_unit",
    "pending_lifecycle_decision_spread_reconstruction_source",
    "pending_lifecycle_decision_spread_reconstruction_source_created_at_utc",
    "pending_lifecycle_decision_spread_reconstruction_source_status",
    "pending_lifecycle_decision_spread_reconstruction_tick_ts_utc",
    "pending_lifecycle_decision_spread_reconstruction_tick_offset_seconds",
    "pending_lifecycle_decision_spread_reconstruction_tick_source_path",
    "pending_lifecycle_decision_spread_reconstruction_tick_source_sha256",
    "pending_lifecycle_entry_touch_spread_value_source_safe",
    "pending_lifecycle_entry_touch_spread_unit",
    "pending_lifecycle_terminal_area_touch_status",
    "pending_lifecycle_terminal_area_first_touch_utc",
    "pending_lifecycle_protective_area_touch_status",
    "pending_lifecycle_protective_area_first_touch_utc",
    "pending_lifecycle_event_order_resolution_method",
    "pending_lifecycle_same_tick_same_bar_ambiguity_status",
    "pending_lifecycle_source_capture_statuses",
    "pending_lifecycle_source_capture_derivations",
    "pending_lifecycle_source_capture_complete",
    "entry_offset_050r_source_capture_contract",
    "entry_offset_050r_tick_replay_status",
    "entry_offset_050r_outcome_status",
    "entry_offset_050r_proxy_r",
    "entry_offset_050r_shifted_entry_price",
    "entry_offset_050r_shifted_target_r",
    "entry_offset_050r_fill_first_touch_utc",
    "entry_offset_050r_terminal_event_utc",
    "entry_offset_050r_source_files",
    "entry_offset_050r_source_capture_statuses",
    "entry_offset_050r_source_capture_complete",
    "entry_offset_concentration_guard_status",
    "entry_offset_original_subtype",
    "entry_offset_concentration_cluster_key",
    "entry_offset_concentration_effective_cluster_count",
    "entry_offset_largest_cluster_key",
    "entry_offset_largest_cluster_guard_required",
    "entry_offset_current_evidence_owner_rows",
    "entry_offset_current_evidence_proxy_r_sum",
    "entry_offset_largest_cluster_row_count",
    "entry_offset_largest_cluster_proxy_r_sum",
    "entry_offset_largest_cluster_row_share",
    "entry_offset_largest_cluster_proxy_r_share",
    "entry_offset_proxy_owner_strategy_id",
    "entry_offset_proxy_owner_candidate_id",
    "entry_offset_proxy_r_reference",
    "entry_offset_proxy_reference_status",
    "entry_offset_cluster_guard_decision",
    "entry_offset_no_fill_control_status",
    "entry_offset_no_fill_repair_branch_candidate",
    "opportunity_preservation_status",
    "opportunity_owner_row_id",
    "opportunity_owner_source_artifact",
    "opportunity_proxy_r_reference",
    "opportunity_proxy_reference_status",
    "opportunity_not_independently_countable_reason",
    "opportunity_useful_mechanism",
    "opportunity_downstream_paths",
    "underlying_intelligence_preserved",
    "missed_opportunity_audit",
)


def _materially_same(existing: dict[str, Any], new: dict[str, Any]) -> bool:
    return all(existing.get(field) == new.get(field) for field in CORRECTION_FIELDS)


def run(
    *,
    candidates_path: Path = DEFAULT_CANDIDATES,
    paths_path: Path = DEFAULT_PATHS,
    pending_lifecycle_path: Path = DEFAULT_PENDING_LIFECYCLE,
    ltf_path_order_path: Path = DEFAULT_LTF_PATH_ORDER,
    fvg_ob_confluence_path: Path = DEFAULT_FVG_OB_CONFLUENCE,
    structural_metadata_path: Path = DEFAULT_STRUCTURAL_METADATA,
    nofill_forward_capture_path: Path = DEFAULT_NOFILL_FORWARD_SOURCE_CAPTURE,
    moonshot_selected_action_source_capture_path: Path = DEFAULT_MOONSHOT_SELECTED_ACTION_SOURCE_CAPTURE,
    pending_tick_spread_reconstruction_path: Path = DEFAULT_PENDING_TICK_SPREAD_RECONSTRUCTION,
    standalone_fvg_repair_decisions_path: Path = DEFAULT_STANDALONE_FVG_REPAIR_DECISIONS,
    swing_protected_repair_decisions_path: Path = DEFAULT_SWING_PROTECTED_REPAIR_DECISIONS,
    nas100_depth_source_repairs_path: Path = DEFAULT_NAS100_DEPTH_THINNESS_SOURCE_REPAIRS,
    fvg_ob_trade_record_bounds_repairs_path: Path = DEFAULT_FVG_OB_TRADE_RECORD_BOUNDS_REPAIRS,
    output_path: Path = DEFAULT_OUTPUT,
    latest_paths_only: bool = False,
    dry_run: bool = False,
    dry_run_output_path: Path | None = None,
) -> dict[str, Any]:
    candidates = {
        str(row.get("candidate_id") or ""): row
        for row in read_jsonl(candidates_path)
        if row.get("candidate_id")
    }
    raw_path_rows = read_jsonl(paths_path)
    path_rows = latest_path_rows_by_candidate(raw_path_rows) if latest_paths_only else raw_path_rows
    pending_lifecycle_rows = read_jsonl(pending_lifecycle_path)
    ltf_rows = read_jsonl(ltf_path_order_path)
    fvg_ob_rows = {
        str(row.get("candidate_id") or ""): row
        for row in read_jsonl(fvg_ob_confluence_path)
        if row.get("candidate_id")
    }
    structural_metadata_rows = read_jsonl(structural_metadata_path)
    structural_metadata = latest_structural_metadata_by_candidate(structural_metadata_rows)
    nofill_forward_capture_rows = read_jsonl(nofill_forward_capture_path)
    nofill_forward_capture = latest_nofill_forward_capture_by_candidate(
        nofill_forward_capture_rows
    )
    moonshot_source_capture_rows = read_jsonl(moonshot_selected_action_source_capture_path)
    moonshot_source_capture = latest_moonshot_selected_action_source_capture(
        moonshot_source_capture_rows
    )
    pending_tick_spread_reconstruction_rows = read_jsonl(pending_tick_spread_reconstruction_path)
    pending_tick_spread_reconstruction = latest_pending_tick_spread_reconstruction_by_candidate(
        pending_tick_spread_reconstruction_rows
    )
    standalone_fvg_repair_decision_rows = read_jsonl(standalone_fvg_repair_decisions_path)
    standalone_fvg_repair_decisions = latest_standalone_fvg_repair_decision_by_key(
        standalone_fvg_repair_decision_rows
    )
    swing_protected_repair_decision_rows = read_jsonl(swing_protected_repair_decisions_path)
    swing_protected_repair_decisions = latest_swing_protected_repair_decision_by_key(
        swing_protected_repair_decision_rows
    )
    nas100_depth_source_repair_rows = read_jsonl(nas100_depth_source_repairs_path)
    nas100_depth_source_repairs = latest_nas100_depth_thinness_source_repair_by_key(
        nas100_depth_source_repair_rows
    )
    fvg_ob_trade_record_bounds_repair_rows = read_jsonl(
        fvg_ob_trade_record_bounds_repairs_path
    )
    fvg_ob_trade_record_bounds_repairs = latest_fvg_ob_trade_record_bounds_repair_by_key(
        fvg_ob_trade_record_bounds_repair_rows
    )
    latest_existing = latest_existing_by_key(output_path)
    written = 0
    would_write = 0
    dry_run_rows: list[dict[str, Any]] = []
    skipped: dict[str, int] = {}
    for path_row in path_rows:
        candidate_id = str(path_row.get("candidate_id") or "")
        candidate = candidates.get(candidate_id)
        if not candidate:
            skipped["candidate_missing_for_path"] = skipped.get("candidate_missing_for_path", 0) + 1
            continue
        candidate = merge_structural_metadata_candidate(
            candidate,
            structural_metadata.get(candidate_id),
        )
        fvg_ob_context = fvg_ob_rows.get(candidate_id)
        if fvg_ob_context:
            candidate = {
                **candidate,
                "fvg_ob_confluence_context": {
                    "bucket": fvg_ob_context.get("bucket"),
                    "created_at_utc": fvg_ob_context.get("created_at_utc"),
                    "source_file": fvg_ob_context.get("source_file"),
                },
            }
        pending_lifecycle = latest_lifecycle_for_candidate_asof(candidate, path_row, pending_lifecycle_rows)
        ltf_row = latest_ltf_for_candidate_asof(candidate, path_row, ltf_rows)
        nofill_forward_row = nofill_forward_capture.get(candidate_id)
        tick_spread_row = pending_tick_spread_reconstruction.get(candidate_id)
        for row in build_strategy_outcome_rows(
            candidate,
            path_row,
            pending_lifecycle_row=pending_lifecycle,
            ltf_row=ltf_row,
            nofill_forward_capture_row=nofill_forward_row,
            tick_spread_reconstruction_row=tick_spread_row,
            moonshot_selected_action_source_capture=moonshot_source_capture,
            standalone_fvg_repair_decisions=standalone_fvg_repair_decisions,
            swing_protected_repair_decisions=swing_protected_repair_decisions,
            nas100_depth_source_repairs=nas100_depth_source_repairs,
            fvg_ob_trade_record_bounds_repairs=fvg_ob_trade_record_bounds_repairs,
        ):
            key = (
                str(row.get("candidate_id") or ""),
                str(row.get("strategy_id") or ""),
                str(row.get("asof_latest_candle_utc") or ""),
            )
            existing = latest_existing.get(key)
            if existing and _materially_same(existing, row):
                skipped["duplicate_candidate_strategy_asof"] = skipped.get(
                    "duplicate_candidate_strategy_asof", 0
                ) + 1
                continue
            if existing:
                row["correction_of_created_at_utc"] = existing.get("created_at_utc")
                row["correction_reason"] = "latest_computed_shadow_outcome_changed_after_source_reconciliation"
                row["manual_backfill_status"] = "CORRECTED_OR_REFRESHED_FROM_LIVE_SHADOW_ROWS"
            if dry_run:
                row["dry_run_append_status"] = "WOULD_APPEND_CORRECTION" if existing else "WOULD_APPEND_NEW"
                dry_run_rows.append(row)
                would_write += 1
            else:
                append_jsonl(output_path, row)
                written += 1
            latest_existing[key] = row
    if dry_run_output_path is not None:
        dry_run_output_path.parent.mkdir(parents=True, exist_ok=True)
        with dry_run_output_path.open("w", encoding="utf-8", newline="\n") as handle:
            for row in dry_run_rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
    return {
        "schema_version": "live_mechanical_strategy_shadow_backfill_summary_v1",
        "candidates_seen": len(candidates),
        "path_rows_seen": len(raw_path_rows),
        "path_rows_evaluated": len(path_rows),
        "latest_paths_only": latest_paths_only,
        "pending_lifecycle_rows_seen": len(pending_lifecycle_rows),
        "ltf_path_order_rows_seen": len(ltf_rows),
        "structural_metadata_rows_seen": len(structural_metadata_rows),
        "structural_metadata_candidates_seen": len(structural_metadata),
        "nofill_forward_capture_rows_seen": len(nofill_forward_capture_rows),
        "nofill_forward_capture_candidates_seen": len(nofill_forward_capture),
        "moonshot_selected_action_source_capture_rows_seen": len(moonshot_source_capture_rows),
        "moonshot_selected_action_source_capture_keys_seen": len(moonshot_source_capture),
        "pending_tick_spread_reconstruction_rows_seen": len(pending_tick_spread_reconstruction_rows),
        "pending_tick_spread_reconstruction_candidates_seen": len(pending_tick_spread_reconstruction),
        "standalone_fvg_repair_decision_rows_seen": len(standalone_fvg_repair_decision_rows),
        "standalone_fvg_repair_decision_keys_seen": len(standalone_fvg_repair_decisions),
        "swing_protected_repair_decision_rows_seen": len(swing_protected_repair_decision_rows),
        "swing_protected_repair_decision_keys_seen": len(swing_protected_repair_decisions),
        "nas100_depth_source_repair_rows_seen": len(nas100_depth_source_repair_rows),
        "nas100_depth_source_repair_keys_seen": len(nas100_depth_source_repairs),
        "fvg_ob_trade_record_bounds_repair_rows_seen": len(
            fvg_ob_trade_record_bounds_repair_rows
        ),
        "fvg_ob_trade_record_bounds_repair_keys_seen": len(
            fvg_ob_trade_record_bounds_repairs
        ),
        "output": str(output_path),
        "dry_run": dry_run,
        "dry_run_output": str(dry_run_output_path) if dry_run_output_path is not None else None,
        "rows_written": written,
        "rows_would_write": would_write if dry_run else written,
        "skipped": dict(sorted(skipped.items())),
    }
