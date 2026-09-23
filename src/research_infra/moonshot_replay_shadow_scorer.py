"""Research-only executable scorer for moonshot replay code candidates.

The scorer consumes branch-local code/spec candidate rows and emits mechanical
shadow actions. It is deliberately side-effect free: no broker calls, no live
config mutation, no order placement, and no promotion claim.
"""

from __future__ import annotations

from typing import Any


SCORER_SURFACE = "src/research_infra/moonshot_replay_shadow_scorer.py"


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def clamp_score(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 6)


def _score_band(value: float) -> str:
    if value >= 0.70:
        return "SHADOW_SCORE_HIGH"
    if value >= 0.45:
        return "SHADOW_SCORE_MODERATE"
    if value >= 0.20:
        return "SHADOW_SCORE_REPAIRABLE"
    return "SHADOW_SCORE_LOW"


def score_code_candidate(row: dict[str, Any]) -> dict[str, Any]:
    """Map one code-candidate row to an executable shadow-scorer action."""

    status = str(row.get("code_candidate_status") or "")
    kind = str(row.get("code_candidate_kind") or "")
    proxy = to_float(row.get("proxy_score"))
    score = 0.15 + max(-0.10, min(0.20, (proxy or 0.0) / 3.0))
    action = "PRESERVE_CONTEXT_ONLY"
    action_family = "REPAIR_OR_PRESERVE"
    eligibility = "NOT_ELIGIBLE_PRESERVE_CONTEXT"
    component = "context"

    if status == "ENTRY_CODE_IMPLEMENT_SHADOW_RULE_SPEC":
        action = "ENABLE_ENTRY_GEOMETRY_SHADOW_RULE"
        action_family = "IMPLEMENT_SHADOW_RULE"
        eligibility = "IMMEDIATE_SHADOW_ENABLE"
        component = "entry_geometry"
        score += 0.62
    elif status == "AVOID_CODE_IMPLEMENT_SHADOW_FILTER_SPEC":
        action = "ENABLE_AVOID_FILTER_SHADOW_RULE"
        action_family = "IMPLEMENT_SHADOW_RULE"
        eligibility = "IMMEDIATE_SHADOW_ENABLE"
        component = "avoid_filter"
        score += 0.58
    elif status == "MARKET_GAP_CODE_IMPLEMENT_ENTRY_GEOMETRY_SPEC":
        action = "ENABLE_MARKET_GAP_ENTRY_GEOMETRY_SHADOW_RULE"
        action_family = "IMPLEMENT_SHADOW_RULE"
        eligibility = "IMMEDIATE_SHADOW_ENABLE"
        component = "market_gap_entry_geometry"
        score += 0.55
    elif status == "MARKET_GAP_CODE_IMPLEMENT_AVOID_FILTER_SPEC":
        action = "ENABLE_MARKET_GAP_AVOID_FILTER_SHADOW_RULE"
        action_family = "IMPLEMENT_SHADOW_RULE"
        eligibility = "IMMEDIATE_SHADOW_ENABLE"
        component = "market_gap_avoid_filter"
        score += 0.53
    elif status == "BRANCH_CODE_IMPLEMENT_MARKET_ENTRY_COMPARATOR_SPEC":
        action = "ENABLE_MARKET_ENTRY_COMPARATOR_SHADOW_RULE"
        action_family = "IMPLEMENT_SHADOW_RULE"
        eligibility = "IMMEDIATE_SHADOW_ENABLE"
        component = "market_entry_comparator"
        score += 0.57
    elif status == "BRANCH_CODE_KEEP_PROXY_SCORER_SPEC":
        action = "ENABLE_BRANCH_PROXY_SCORER_SHADOW_RULE"
        action_family = "IMPLEMENT_SHADOW_RULE"
        eligibility = "IMMEDIATE_SHADOW_ENABLE"
        component = "branch_proxy_scorer"
        score += 0.48
    elif status == "BRANCH_CODE_IMPLEMENT_AVOID_FROM_FAILURE_CAUSE":
        action = "ENABLE_BRANCH_FAILURE_AVOID_FILTER_SHADOW_RULE"
        action_family = "IMPLEMENT_SHADOW_RULE"
        eligibility = "IMMEDIATE_SHADOW_ENABLE"
        component = "branch_failure_avoid_filter"
        score += 0.50
    elif "SCORE" in status or "REDESIGN" in status:
        action = "SCORE_WITH_CONTROL_BEFORE_SHADOW_ENABLE"
        action_family = "SCORE_WITH_CONTROL"
        eligibility = "CONTROL_REQUIRED_BEFORE_ENABLE"
        component = "control_scored_redesign"
        score += 0.25
    elif status.startswith("SOURCE_CODE_MATERIALIZE"):
        needed = int(to_float(row.get("source_rows_needed_to_n20")) or 0)
        if status == "SOURCE_CODE_MATERIALIZE_HIGH_PRIORITY":
            action = "MATERIALIZE_SOURCE_DENOMINATOR_HIGH_PRIORITY"
            score += 0.48
        elif status == "SOURCE_CODE_MATERIALIZE_OUTSIDE_BRANCH_DENOMINATOR":
            action = "MATERIALIZE_OUTSIDE_BRANCH_SOURCE_DENOMINATOR"
            score += 0.42
        else:
            action = "MATERIALIZE_CURRENT_CONCENTRATION_CONTROL_SOURCE"
            score += 0.35
        score -= min(0.20, needed / 100.0)
        action_family = "MATERIALIZE_SOURCE"
        eligibility = "SOURCE_MATERIALIZATION_REQUIRED"
        component = "source_materialization"
    elif status.startswith("CONCENTRATION_CODE"):
        action = "ENFORCE_CONCENTRATION_DENOMINATOR_GUARD"
        action_family = "DENOMINATOR_GUARD"
        eligibility = "GUARD_REQUIRED"
        component = "concentration_denominator_guard"
        score += 0.40 if "FORCE_OUTSIDE" in status or "KEEP_MECHANISM" in status else 0.25
    elif status.startswith("SCORER_CODE_ADD"):
        action = "APPLY_BRANCH_LOCAL_SCORER_COMPONENT_SPEC"
        action_family = "SCORER_COMPONENT"
        eligibility = "SCORER_COMPONENT_READY"
        component = "scorer_patch"
        score += 0.45
    elif "CONTROL_ONLY" in status:
        action = "PRESERVE_CONTROL_ONLY_DO_NOT_ENABLE"
        action_family = "CONTROL_ONLY"
        eligibility = "CONTROL_ONLY_NOT_ENABLED"
        component = "control"
        score += 0.10

    if bool(row.get("outside_gbpjpy_xauusd_current_branch_box")) and action_family in {
        "IMPLEMENT_SHADOW_RULE",
        "MATERIALIZE_SOURCE",
    }:
        score += 0.05
    if kind == "SCORER_PATCH_SPEC":
        score += 0.03

    final_score = clamp_score(score)
    return {
        "shadow_scorer_surface": SCORER_SURFACE,
        "shadow_scorer_score": final_score,
        "shadow_scorer_score_band": _score_band(final_score),
        "shadow_scorer_action": action,
        "shadow_scorer_action_family": action_family,
        "shadow_scorer_component": component,
        "implementation_eligibility": eligibility,
        "live_effect": False,
    }
