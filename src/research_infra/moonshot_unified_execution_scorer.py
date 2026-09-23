"""Research-only unified execution scoring helpers for the moonshot branch.

These pure functions combine branch-transfer, R-style proxy, no-fill, near-miss,
and market-gap rows into mechanical keep/kill/redesign/implementation labels.
They do not read broker state, place orders, mutate live config, or make
promotion/live-readiness claims.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable


def to_float(value: Any) -> float | None:
    """Convert a loose numeric field to float without raising."""

    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def rstyle_proxy_signal_class(row: dict[str, Any] | None) -> str:
    """Classify the strongest available R-style proxy signal for one branch."""

    if not row:
        return "RSTYLE_PROXY_MISSING"
    branch_class = str(row.get("branch_result_class") or "")
    sealed_status = str(row.get("sealed_or_proxy_outcome_status") or "")
    midpoint = to_float(row.get("rstyle_midpoint_mean"))
    if midpoint is None:
        proxy = row.get("expectancy_style_proxy") or {}
        midpoint = to_float(proxy.get("rstyle_midpoint_mean") or proxy.get("midpoint_mean"))
    if "NO_RSTYLE" in branch_class or "NO_RSTYLE" in sealed_status or midpoint is None:
        return "RSTYLE_PROXY_NO_SCALAR"
    if "STRADDLES_ZERO" in branch_class or "STRADDLES_ZERO" in sealed_status:
        return "RSTYLE_PROXY_AMBIGUOUS_INTERVAL"
    if midpoint > 0:
        return "RSTYLE_PROXY_POSITIVE_MIDPOINT"
    if midpoint < 0:
        return "RSTYLE_PROXY_NEGATIVE_MIDPOINT"
    return "RSTYLE_PROXY_FLAT_MIDPOINT"


def source_repair_pressure_class(row: dict[str, Any] | None) -> str:
    """Classify source/source-confidence pressure from joined branch rows."""

    if not row:
        return "SOURCE_PRESSURE_UNKNOWN"
    joined = " ".join(
        str(row.get(key) or "")
        for key in (
            "source_confidence_status",
            "source_implication_class",
            "source_recompute_decision",
            "source_execution_class",
            "cost_sensitivity_proxy_status",
            "cost_robustness_bucket",
        )
    ).upper()
    if "EXACT_SOURCE_SUPPORTED" in joined or "ACCEPTED_CONFIRMED" in joined:
        return "SOURCE_PRESSURE_EXACT_OR_CONFIRMED"
    if "SOURCE_STRESS" in joined or "PROXY" in joined or "UNAVAILABLE" in joined:
        return "SOURCE_PRESSURE_REPAIR_OR_STRESS"
    if "NO_SCALAR" in joined or "PROVENANCE" in joined:
        return "SOURCE_PRESSURE_PROVENANCE_ONLY"
    return "SOURCE_PRESSURE_NOT_DOMINANT"


def execution_pressure_class(row: dict[str, Any] | None) -> str:
    """Classify fillability/path-ordering pressure from branch rows."""

    if not row:
        return "EXECUTION_PRESSURE_UNKNOWN"
    joined = " ".join(
        str(row.get(key) or "")
        for key in (
            "ambiguity_status",
            "nofill_transfer_implication",
            "nofill_join_status",
            "nearmiss_transfer_implication",
            "target_stop_result",
            "branch_execution_class",
            "m15_builder_result_status",
            "m1_builder_result_status",
            "entry_adverse_builder_result_status",
        )
    ).upper()
    if "MARKET_ENTRY" in joined:
        return "EXECUTION_PRESSURE_MARKET_ENTRY_COMPARATOR"
    if "NOFILL" in joined or "FILLABILITY" in joined or "RETEST_REDESIGN" in joined:
        return "EXECUTION_PRESSURE_FILLABILITY_OR_RETEST_REDESIGN"
    if "NO_ORDERING_AMBIGUITY_RECORDED" in joined and "INTERVAL" not in joined:
        return "EXECUTION_PRESSURE_NOT_DOMINANT"
    if "AMBIG" in joined or "ORDERING" in joined or "INTERVAL" in joined:
        return "EXECUTION_PRESSURE_ORDERING_OR_INTERVAL_SPLIT"
    if "STOP_FIRST" in joined:
        return "EXECUTION_PRESSURE_STOP_FIRST_AVOID"
    return "EXECUTION_PRESSURE_NOT_DOMINANT"


def classify_unified_branch_decision(row: dict[str, Any]) -> dict[str, str]:
    """Return a unified branch decision from already-source-bound row fields."""

    decision_direction = str(row.get("decision_direction") or "").upper()
    system_decision = str(row.get("system_decision_class") or "").upper()
    primary_family = str(row.get("primary_export_family") or "").upper()
    rstyle_class = rstyle_proxy_signal_class(row)
    source_pressure = source_repair_pressure_class(row)
    execution_pressure = execution_pressure_class(row)

    if primary_family == "BINDING" or "NO_SCALAR" in system_decision:
        unified = "PRESERVE_PROVENANCE_REQUIREMENT"
        candidate_type = "PROVENANCE_REQUIREMENT"
        next_action = "preserve_target_stop_binding_and_exclude_from_scalar_scorer"
    elif "KILL" in decision_direction or "KILL" in system_decision:
        unified = "KILL_OR_AVOID_FILTER_CANDIDATE"
        candidate_type = "AVOID_OR_REDIRECT_SPEC"
        next_action = "preserve_kill_reason_and_use_as_avoid_or_redesign_pressure"
    elif execution_pressure == "EXECUTION_PRESSURE_MARKET_ENTRY_COMPARATOR":
        unified = "IMPLEMENT_MARKET_ENTRY_CHALLENGER_SPEC"
        candidate_type = "MARKET_ENTRY_COMPARATOR_SPEC"
        next_action = "score_market_entry_variant_against_retest_limit_proxy"
    elif execution_pressure == "EXECUTION_PRESSURE_FILLABILITY_OR_RETEST_REDESIGN":
        unified = "REDESIGN_FILLABILITY_OR_RETEST_BEFORE_IMPLEMENT"
        candidate_type = "FILLABILITY_RETEST_REDESIGN_SPEC"
        next_action = "compute_fillability_retest_and_entry_offset_variants"
    elif "SPLIT" in decision_direction or execution_pressure == "EXECUTION_PRESSURE_ORDERING_OR_INTERVAL_SPLIT":
        unified = "SPLIT_REDESIGN_AND_INTERVAL_SCORE"
        candidate_type = "ORDERING_INTERVAL_SPLIT_SPEC"
        next_action = "preserve conservative and optimistic path intervals separately"
    elif source_pressure == "SOURCE_PRESSURE_REPAIR_OR_STRESS":
        unified = "REPAIR_SOURCE_OR_COST_BEFORE_IMPLEMENT"
        candidate_type = "SOURCE_COST_REPAIR_SPEC"
        next_action = "materialize exact source where available or keep low/high stress bounds"
    elif "REPAIR" in decision_direction:
        unified = "REPAIR_THEN_REVIEW_IMPLEMENTATION_CANDIDATE"
        candidate_type = "REPAIR_REVIEW_SPEC"
        next_action = "repair blocker then rescore branch in same proxy framework"
    elif "KEEP" in decision_direction and rstyle_class == "RSTYLE_PROXY_POSITIVE_MIDPOINT":
        unified = "IMPLEMENT_PROXY_CHALLENGER_SPEC"
        candidate_type = "BRANCH_LOCAL_SCORER_SPEC"
        next_action = "instantiate branch-local scorer with source and cost caveats preserved"
    elif "KEEP" in decision_direction:
        unified = "KEEP_AS_CHALLENGER_WITH_AMBIGUITY"
        candidate_type = "CHALLENGER_AMBIGUITY_SPEC"
        next_action = "keep challenger but require ambiguity split before ranking"
    else:
        unified = "PRESERVE_CONTEXT_NO_DIRECT_IMPLEMENTATION"
        candidate_type = "CONTEXT_ONLY_SPEC"
        next_action = "preserve row as context for transfer and concentration tests"

    return {
        "unified_execution_decision": unified,
        "implementation_candidate_type": candidate_type,
        "unified_next_action": next_action,
        "rstyle_proxy_signal_class": rstyle_class,
        "source_repair_pressure_class": source_pressure,
        "execution_pressure_class": execution_pressure,
    }


def classify_market_gap_candidate(row: dict[str, Any]) -> dict[str, str]:
    """Classify market-gap primitive rows into implementation/execution work."""

    action_class = str(row.get("action_class") or "")
    movement_status = str(row.get("movement_status") or "")
    if action_class == "SOURCE_EXPANSION_QUEUE":
        return {
            "unified_execution_decision": "EXPAND_SOURCE_DENOMINATOR_BEFORE_BRANCH_DECISION",
            "implementation_candidate_type": "MARKET_GAP_SOURCE_EXPANSION_SPEC",
            "unified_next_action": "build source expansion for small-n market/session/horizon primitive",
            "market_gap_evidence_class": movement_status,
        }
    if action_class == "ENTRY_GEOMETRY_QUEUE":
        return {
            "unified_execution_decision": "IMPLEMENT_MARKET_GAP_ENTRY_GEOMETRY_CHALLENGER",
            "implementation_candidate_type": "MARKET_GAP_ENTRY_GEOMETRY_SPEC",
            "unified_next_action": "score entry geometry on supportive or mixed market-gap primitive",
            "market_gap_evidence_class": movement_status,
        }
    if action_class == "AVOID_INVERSE_QUEUE":
        return {
            "unified_execution_decision": "IMPLEMENT_MARKET_GAP_AVOID_INVERSE_CONTROL",
            "implementation_candidate_type": "MARKET_GAP_AVOID_INVERSE_SPEC",
            "unified_next_action": "score avoid or inverse control for weak market-gap primitive",
            "market_gap_evidence_class": movement_status,
        }
    return {
        "unified_execution_decision": "PRESERVE_MARKET_GAP_CONTEXT",
        "implementation_candidate_type": "MARKET_GAP_CONTEXT_SPEC",
        "unified_next_action": "preserve market-gap row as context",
        "market_gap_evidence_class": movement_status or "UNCLASSIFIED_MARKET_GAP",
    }


def _clamp_score(value: float) -> float:
    return round(max(-1.0, min(1.0, value)), 6)


def score_branch_candidate(row: dict[str, Any]) -> dict[str, Any]:
    """Score one branch-local implementation candidate from unified evidence fields."""

    decision = str(row.get("unified_execution_decision") or "")
    rstyle_class = str(row.get("rstyle_proxy_signal_class") or rstyle_proxy_signal_class(row))
    source_pressure = str(row.get("source_repair_pressure_class") or source_repair_pressure_class(row))
    execution_pressure = str(row.get("execution_pressure_class") or execution_pressure_class(row))
    target_stop_result = str(row.get("target_stop_result") or "")
    midpoint = to_float(row.get("rstyle_midpoint_mean"))

    score = 0.0
    if rstyle_class == "RSTYLE_PROXY_POSITIVE_MIDPOINT":
        score += 0.25
    elif rstyle_class == "RSTYLE_PROXY_AMBIGUOUS_INTERVAL":
        score += 0.05
    elif rstyle_class == "RSTYLE_PROXY_NEGATIVE_MIDPOINT":
        score -= 0.25
    elif rstyle_class == "RSTYLE_PROXY_NO_SCALAR":
        score -= 0.45
    if midpoint is not None:
        score += max(-0.2, min(0.2, midpoint / 2.0))

    if "TARGET_FIRST" in target_stop_result:
        score += 0.2
    elif "STOP_FIRST" in target_stop_result:
        score -= 0.3
    elif "NO_FILL" in target_stop_result or "UNFILLED" in target_stop_result:
        score -= 0.15
    elif "AMBIGUITY" in target_stop_result:
        score -= 0.1

    if source_pressure == "SOURCE_PRESSURE_EXACT_OR_CONFIRMED":
        score += 0.15
    elif source_pressure == "SOURCE_PRESSURE_REPAIR_OR_STRESS":
        score -= 0.1
    elif source_pressure == "SOURCE_PRESSURE_PROVENANCE_ONLY":
        score -= 0.35

    if execution_pressure == "EXECUTION_PRESSURE_MARKET_ENTRY_COMPARATOR":
        score += 0.2
    elif execution_pressure == "EXECUTION_PRESSURE_FILLABILITY_OR_RETEST_REDESIGN":
        score -= 0.05
    elif execution_pressure == "EXECUTION_PRESSURE_ORDERING_OR_INTERVAL_SPLIT":
        score -= 0.1
    elif execution_pressure == "EXECUTION_PRESSURE_STOP_FIRST_AVOID":
        score -= 0.2

    if decision == "IMPLEMENT_MARKET_ENTRY_CHALLENGER_SPEC":
        score += 0.25
    elif decision == "REDESIGN_FILLABILITY_OR_RETEST_BEFORE_IMPLEMENT":
        score -= 0.05
    elif decision == "KILL_OR_AVOID_FILTER_CANDIDATE":
        score -= 0.45
    elif decision == "PRESERVE_PROVENANCE_REQUIREMENT":
        score -= 0.55

    score = _clamp_score(score)
    if decision == "PRESERVE_PROVENANCE_REQUIREMENT":
        score_class = "BRANCH_PROVENANCE_EXCLUDE_FROM_SCALAR_SCORER"
        next_action = "preserve binding row and exclude from scalar branch ranking"
    elif decision == "KILL_OR_AVOID_FILTER_CANDIDATE":
        score_class = "BRANCH_AVOID_OR_KILL_PRESSURE"
        next_action = "materialize avoid/filter reason before considering any revival"
    elif decision == "IMPLEMENT_MARKET_ENTRY_CHALLENGER_SPEC" and score >= 0.25:
        score_class = "BRANCH_MARKET_ENTRY_CHALLENGER_SCORE_NOW"
        next_action = "score market-entry comparator against retest-limit branch path"
    elif decision == "REDESIGN_FILLABILITY_OR_RETEST_BEFORE_IMPLEMENT" and score >= 0.0:
        score_class = "BRANCH_FILLABILITY_REDESIGN_PRIORITY"
        next_action = "score fillability, retest, and entry-offset redesign variants"
    elif score >= 0.25:
        score_class = "BRANCH_CHALLENGER_SCORE_NOW"
        next_action = "score branch-local challenger with source and execution caveats preserved"
    elif score >= -0.1:
        score_class = "BRANCH_REPAIR_OR_REDESIGN_FIRST"
        next_action = "repair source/execution ambiguity then rescore"
    else:
        score_class = "BRANCH_LOW_PRIORITY_OR_AVOID_FIRST"
        next_action = "use as avoid, kill, or failure-intelligence row before implementation"

    return {
        "candidate_score_proxy": score,
        "candidate_score_class": score_class,
        "candidate_score_formula": (
            "rstyle_midpoint + target_stop_order + source_pressure + execution_pressure + unified_decision_adjustment"
        ),
        "candidate_next_action": next_action,
    }


def score_market_gap_candidate(row: dict[str, Any]) -> dict[str, Any]:
    """Score one market-gap primitive implementation row without dropping small-n rows."""

    action_class = str(row.get("action_class") or "")
    movement_status = str(row.get("movement_status") or "")
    flagged_n = int(to_float(row.get("flagged_n")) or 0)
    control_n = int(to_float(row.get("control_n")) or 0)
    delta_abs = to_float(row.get("delta_mean_abs_future_change")) or 0.0
    delta_alignment = to_float(row.get("delta_alignment_rate")) or 0.0

    score = 0.0
    if action_class == "ENTRY_GEOMETRY_QUEUE":
        score += 0.35
    elif action_class == "AVOID_INVERSE_QUEUE":
        score += 0.25
    elif action_class == "SOURCE_EXPANSION_QUEUE":
        score += 0.05

    if movement_status == "POSITIVE_ABS_AND_NONNEGATIVE_ALIGNMENT_DELTA":
        score += 0.3
    elif movement_status == "POSITIVE_ABS_NEGATIVE_ALIGNMENT_DELTA":
        score += 0.12
    elif movement_status == "FLAT_OR_NEGATIVE_ABS_DELTA":
        score += 0.2 if action_class == "AVOID_INVERSE_QUEUE" else -0.15
    elif movement_status == "SMALL_N_LT20":
        score += min(flagged_n, 19) / 100.0

    score += max(-0.15, min(0.15, delta_alignment))
    score += max(-0.1, min(0.1, delta_abs / 10.0))
    if row.get("nofill_sidecar_status") == "SAME_SYMBOL_SESSION_NOFILL_CONTEXT_AVAILABLE":
        score += 0.05
    if row.get("residual_transfer_class"):
        score += 0.05

    score = _clamp_score(score)
    additional_flagged_rows_needed = max(0, 20 - flagged_n)
    if action_class == "SOURCE_EXPANSION_QUEUE":
        if additional_flagged_rows_needed <= 5 or delta_abs >= 0.35:
            score_class = "MARKET_GAP_SOURCE_EXPANSION_HIGH_PRIORITY"
        else:
            score_class = "MARKET_GAP_SOURCE_EXPANSION_REQUIRED"
        next_action = "expand tick/source denominator for this market/session/horizon/primitive before branch scoring"
    elif action_class == "ENTRY_GEOMETRY_QUEUE":
        if movement_status == "POSITIVE_ABS_AND_NONNEGATIVE_ALIGNMENT_DELTA":
            score_class = "MARKET_GAP_ENTRY_GEOMETRY_SCORE_NOW"
        else:
            score_class = "MARKET_GAP_ENTRY_GEOMETRY_MIXED_ALIGNMENT_SCORE_WITH_CONTROL"
        next_action = "instantiate entry-geometry challenger for this market-gap primitive and compare controls"
    elif action_class == "AVOID_INVERSE_QUEUE":
        score_class = "MARKET_GAP_AVOID_INVERSE_SCORE_NOW"
        next_action = "instantiate avoid/inverse control for weak or adverse market-gap primitive"
    else:
        score_class = "MARKET_GAP_CONTEXT_ONLY"
        next_action = "preserve as context until a direct action class is available"

    return {
        "candidate_score_proxy": score,
        "candidate_score_class": score_class,
        "candidate_score_formula": (
            "action_class + movement_status + delta_alignment + delta_abs + nofill_sidecar + residual_transfer"
        ),
        "candidate_next_action": next_action,
        "additional_flagged_rows_needed_for_n20": additional_flagged_rows_needed,
        "flagged_to_control_ratio": round(flagged_n / control_n, 9) if control_n else None,
    }


def concentration_artifact_class(
    current_rows: int,
    market_gap_rows: int,
    full_tick_rows: int,
    current_total: int,
    market_gap_total: int,
) -> str:
    """Classify whether branch concentration is likely search artifact or mechanism."""

    current_share = current_rows / current_total if current_total else 0.0
    market_gap_share = market_gap_rows / market_gap_total if market_gap_total else 0.0
    if current_rows == 0 and market_gap_rows > 0:
        return "CURRENT_BRANCH_DENOMINATOR_ARTIFACT_SYMBOL_AVAILABLE_OUTSIDE_BRANCH_QUEUE"
    if current_share >= 0.75 and market_gap_rows > 0:
        return "MECHANISM_CONCENTRATED_BUT_DENOMINATOR_NARROWNESS_CONFIRMED"
    if current_rows > 0 and market_gap_rows > current_rows:
        return "PARTIAL_COVERAGE_WITH_LARGER_MARKET_GAP_DENOMINATOR"
    if full_tick_rows > 0 and current_rows == 0:
        return "AVAILABLE_TICK_CONTEXT_MISSING_FROM_BRANCH_QUEUE"
    if current_rows > 0:
        return "CURRENT_BRANCH_COVERAGE_PRESENT"
    return "NO_AVAILABLE_CURRENT_OR_MARKET_GAP_ROWS"


def summarize_labels(rows: Iterable[dict[str, Any]], key: str) -> dict[str, int]:
    """Return a sorted count dictionary for one field."""

    return dict(sorted(Counter(str(row.get(key)) for row in rows).items()))
