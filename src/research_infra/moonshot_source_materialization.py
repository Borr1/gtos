"""Research-only source materialization helpers for moonshot source queues.

These helpers classify whether a source queue row can be closed by current
targetable rows, current source flags plus fail-closed horizon evidence, or an
expanded source proxy. They are pure scoring utilities and have no live effect.
"""

from __future__ import annotations

from typing import Any


MATERIALIZATION_SURFACE = "src/research_infra/moonshot_source_materialization.py"


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value: Any) -> int:
    numeric = to_float(value)
    return int(numeric) if numeric is not None else 0


def clamp(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return round(max(low, min(high, value)), 6)


def clamp01(value: float) -> float:
    return clamp(value, 0.0, 1.0)


def classify_materialization(metrics: dict[str, Any]) -> dict[str, Any]:
    """Classify materialization and proxy closure from precomputed metrics."""

    targetable = to_int(metrics.get("current_targetable_flagged_n"))
    current_source = to_int(metrics.get("current_source_flagged_n"))
    failclosed = to_int(metrics.get("current_failclosed_flagged_n"))
    same_symbol_sessions = to_int(metrics.get("same_symbol_all_sessions_source_flagged_n"))
    same_session_symbols = to_int(metrics.get("same_session_all_symbols_source_flagged_n"))
    all_market_primitive = to_int(metrics.get("all_market_primitive_source_flagged_n"))
    symbol_session_all_primitives = to_int(metrics.get("same_symbol_session_all_primitives_source_flagged_n"))
    same_symbol_targetable = to_int(metrics.get("same_symbol_all_sessions_targetable_flagged_n"))
    same_session_targetable = to_int(metrics.get("same_session_all_symbols_targetable_flagged_n"))
    all_market_targetable = to_int(metrics.get("all_market_primitive_targetable_flagged_n"))
    symbol_session_all_primitives_targetable = to_int(
        metrics.get("same_symbol_session_all_primitives_targetable_flagged_n")
    )

    if targetable >= 20:
        status = "SOURCE_MATERIALIZATION_CURRENT_TARGETABLE_N20_EXACT"
        decision = "SCORE_CURRENT_SCOPE_TARGETABLE_N20"
        proxy_scope = "current_symbol_session_horizon_primitive"
        exact_gap = 0
        targetability_class = "TARGETABLE_ROWS_CLOSE_N20"
    elif current_source >= 20 and failclosed > 0:
        status = "SOURCE_MATERIALIZATION_CURRENT_SOURCE_N20_HORIZON_FAILCLOSED"
        decision = "SCORE_WITH_HORIZON_FAILCLOSED_GUARD_AND_REPAIR_ROUTE"
        proxy_scope = "current_symbol_session_primitive_source_flags"
        exact_gap = max(0, 20 - targetable)
        targetability_class = "SOURCE_FLAGS_CLOSE_N20_TARGET_HORIZON_FAILCLOSED"
    elif current_source >= 20:
        status = "SOURCE_MATERIALIZATION_CURRENT_SOURCE_N20_TARGETABILITY_GAP"
        decision = "SCORE_WITH_CURRENT_SOURCE_FLAG_GUARD_AND_TARGETABILITY_REPAIR"
        proxy_scope = "current_symbol_session_primitive_source_flags"
        exact_gap = max(0, 20 - targetable)
        targetability_class = "SOURCE_FLAGS_CLOSE_N20_TARGETABILITY_GAP"
    elif same_symbol_targetable >= 20:
        status = "SOURCE_MATERIALIZATION_SAME_SYMBOL_ALL_SESSION_TARGETABLE_PROXY_N20"
        decision = "SCORE_EXPANDED_SESSION_TARGETABLE_PROXY_WITH_SCOPE_GUARD"
        proxy_scope = "same_symbol_all_sessions_targetable_primitive"
        exact_gap = max(0, 20 - current_source)
        targetability_class = "CURRENT_SOURCE_UNDER_N20_TARGETABLE_PROXY_CLOSES"
    elif same_session_targetable >= 20:
        status = "SOURCE_MATERIALIZATION_SAME_SESSION_ALL_SYMBOL_TARGETABLE_PROXY_N20"
        decision = "SCORE_CROSS_SYMBOL_SESSION_TARGETABLE_PROXY_WITH_SCOPE_GUARD"
        proxy_scope = "same_session_all_symbols_targetable_primitive"
        exact_gap = max(0, 20 - current_source)
        targetability_class = "CURRENT_SOURCE_UNDER_N20_TARGETABLE_PROXY_CLOSES"
    elif symbol_session_all_primitives_targetable >= 20:
        status = "SOURCE_MATERIALIZATION_SAME_SYMBOL_SESSION_ALL_PRIMITIVES_TARGETABLE_PROXY_N20"
        decision = "SCORE_TARGETABLE_PRIMITIVE_FAMILY_PROXY_WITH_OVERLAP_GUARD"
        proxy_scope = "same_symbol_session_all_primitives_targetable"
        exact_gap = max(0, 20 - current_source)
        targetability_class = "CURRENT_SOURCE_UNDER_N20_TARGETABLE_PROXY_CLOSES"
    elif all_market_targetable >= 20:
        status = "SOURCE_MATERIALIZATION_ALL_MARKET_PRIMITIVE_TARGETABLE_PROXY_N20"
        decision = "SCORE_ALL_MARKET_TARGETABLE_PRIMITIVE_PROXY_WITH_TRANSFER_GUARD"
        proxy_scope = "all_market_targetable_primitive"
        exact_gap = max(0, 20 - current_source)
        targetability_class = "CURRENT_SOURCE_UNDER_N20_BROAD_TARGETABLE_PROXY_CLOSES"
    elif same_symbol_sessions >= 20:
        status = "SOURCE_MATERIALIZATION_SAME_SYMBOL_ALL_SESSION_PROXY_N20"
        decision = "SCORE_EXPANDED_SESSION_PROXY_WITH_SCOPE_GUARD"
        proxy_scope = "same_symbol_all_sessions_primitive"
        exact_gap = max(0, 20 - current_source)
        targetability_class = "CURRENT_SOURCE_UNDER_N20_PROXY_CLOSES"
    elif same_session_symbols >= 20:
        status = "SOURCE_MATERIALIZATION_SAME_SESSION_ALL_SYMBOL_PROXY_N20"
        decision = "SCORE_CROSS_SYMBOL_SESSION_PROXY_WITH_SCOPE_GUARD"
        proxy_scope = "same_session_all_symbols_primitive"
        exact_gap = max(0, 20 - current_source)
        targetability_class = "CURRENT_SOURCE_UNDER_N20_PROXY_CLOSES"
    elif symbol_session_all_primitives >= 20:
        status = "SOURCE_MATERIALIZATION_SAME_SYMBOL_SESSION_ALL_PRIMITIVES_PROXY_N20"
        decision = "SCORE_PRIMITIVE_FAMILY_PROXY_WITH_OVERLAP_GUARD"
        proxy_scope = "same_symbol_session_all_primitives"
        exact_gap = max(0, 20 - current_source)
        targetability_class = "CURRENT_SOURCE_UNDER_N20_PROXY_CLOSES"
    elif all_market_primitive >= 20:
        status = "SOURCE_MATERIALIZATION_ALL_MARKET_PRIMITIVE_PROXY_N20"
        decision = "SCORE_ALL_MARKET_PRIMITIVE_PROXY_WITH_TRANSFER_GUARD"
        proxy_scope = "all_market_primitive"
        exact_gap = max(0, 20 - current_source)
        targetability_class = "CURRENT_SOURCE_UNDER_N20_BROAD_PROXY_CLOSES"
    else:
        status = "SOURCE_MATERIALIZATION_NO_CURRENT_PROXY_N20"
        decision = "PRESERVE_EXACT_SOURCE_EXPANSION_REQUIREMENT"
        proxy_scope = "unclosed_current_resources"
        exact_gap = max(0, 20 - current_source)
        targetability_class = "NO_SOURCE_OR_PROXY_N20"

    return {
        "source_materialization_execution_status": status,
        "source_materialization_decision": decision,
        "materialization_proxy_scope": proxy_scope,
        "current_targetability_class": targetability_class,
        "current_exact_gap_to_n20": exact_gap,
    }


def materialization_proxy_fields(row: dict[str, Any], metrics: dict[str, Any]) -> dict[str, Any]:
    """Compute a bounded proxy-R style materialization score."""

    classification = classify_materialization(metrics)
    base_score = to_float(row.get("source_replay_priority_score"))
    if base_score is None:
        base_score = to_float(row.get("shadow_scorer_score")) or 0.0

    status = classification["source_materialization_execution_status"]
    targetable = to_int(metrics.get("current_targetable_flagged_n"))
    failclosed = to_int(metrics.get("current_failclosed_flagged_n"))
    outside = bool(row.get("outside_gbpjpy_xauusd_current_branch_box"))

    if status == "SOURCE_MATERIALIZATION_CURRENT_TARGETABLE_N20_EXACT":
        coverage_bonus = 0.15
        uncertainty = 0.08
    elif status == "SOURCE_MATERIALIZATION_CURRENT_SOURCE_N20_HORIZON_FAILCLOSED":
        coverage_bonus = 0.06
        uncertainty = 0.18
    elif status == "SOURCE_MATERIALIZATION_CURRENT_SOURCE_N20_TARGETABILITY_GAP":
        coverage_bonus = 0.04
        uncertainty = 0.20
    elif status == "SOURCE_MATERIALIZATION_SAME_SYMBOL_ALL_SESSION_TARGETABLE_PROXY_N20":
        coverage_bonus = 0.05
        uncertainty = 0.18
    elif status == "SOURCE_MATERIALIZATION_SAME_SESSION_ALL_SYMBOL_TARGETABLE_PROXY_N20":
        coverage_bonus = 0.03
        uncertainty = 0.22
    elif status == "SOURCE_MATERIALIZATION_SAME_SYMBOL_SESSION_ALL_PRIMITIVES_TARGETABLE_PROXY_N20":
        coverage_bonus = 0.02
        uncertainty = 0.24
    elif status == "SOURCE_MATERIALIZATION_ALL_MARKET_PRIMITIVE_TARGETABLE_PROXY_N20":
        coverage_bonus = 0.01
        uncertainty = 0.26
    elif status == "SOURCE_MATERIALIZATION_SAME_SYMBOL_ALL_SESSION_PROXY_N20":
        coverage_bonus = 0.03
        uncertainty = 0.22
    elif status == "SOURCE_MATERIALIZATION_SAME_SESSION_ALL_SYMBOL_PROXY_N20":
        coverage_bonus = 0.01
        uncertainty = 0.26
    elif status == "SOURCE_MATERIALIZATION_SAME_SYMBOL_SESSION_ALL_PRIMITIVES_PROXY_N20":
        coverage_bonus = 0.00
        uncertainty = 0.28
    elif status == "SOURCE_MATERIALIZATION_ALL_MARKET_PRIMITIVE_PROXY_N20":
        coverage_bonus = -0.02
        uncertainty = 0.30
    else:
        coverage_bonus = -0.10
        uncertainty = 0.35

    target_gap_penalty = min(0.12, max(0, 20 - targetable) / 200.0)
    failclosed_penalty = min(0.08, failclosed / 500.0)
    outside_bonus = 0.02 if outside else 0.0
    proxy_score = clamp01(base_score + coverage_bonus + outside_bonus - target_gap_penalty - failclosed_penalty)
    midpoint = clamp(proxy_score - 0.35)
    lower = clamp(midpoint - uncertainty)
    upper = clamp(midpoint + uncertainty)
    if lower > 0:
        result_class = "PROXY_R_INTERVAL_ALL_POSITIVE"
    elif upper < 0:
        result_class = "PROXY_R_INTERVAL_ALL_NEGATIVE"
    else:
        result_class = "PROXY_R_INTERVAL_STRADDLES_ZERO"

    return {
        **classification,
        "materialization_proxy_score": proxy_score,
        "materialization_proxy_score_formula": (
            "source_replay_priority_or_shadow_score + source_coverage_bonus + outside_branch_bonus "
            "- current_targetable_gap_penalty - failclosed_horizon_penalty"
        ),
        "materialization_proxy_r_style_midpoint": midpoint,
        "materialization_proxy_r_style_lower": lower,
        "materialization_proxy_r_style_upper": upper,
        "materialization_proxy_r_style_result_class": result_class,
        "materialization_proxy_r_style_uncertainty": uncertainty,
    }


def exact_missing_reason(metrics: dict[str, Any]) -> str:
    """Return an exact source/targetability explanation for one row."""

    classification = classify_materialization(metrics)
    status = classification["source_materialization_execution_status"]
    targetable = to_int(metrics.get("current_targetable_flagged_n"))
    current_source = to_int(metrics.get("current_source_flagged_n"))
    failclosed = to_int(metrics.get("current_failclosed_flagged_n"))
    same_symbol = to_int(metrics.get("same_symbol_all_sessions_source_flagged_n"))
    same_session = to_int(metrics.get("same_session_all_symbols_source_flagged_n"))
    all_market = to_int(metrics.get("all_market_primitive_source_flagged_n"))
    same_symbol_targetable = to_int(metrics.get("same_symbol_all_sessions_targetable_flagged_n"))
    same_session_targetable = to_int(metrics.get("same_session_all_symbols_targetable_flagged_n"))
    all_market_targetable = to_int(metrics.get("all_market_primitive_targetable_flagged_n"))
    fail_reasons = metrics.get("current_failclosed_reason_counts") or {}

    if status == "SOURCE_MATERIALIZATION_CURRENT_TARGETABLE_N20_EXACT":
        return (
            f"current targetable flagged rows already close N20: targetable_flagged_n={targetable}, "
            f"current_source_flagged_n={current_source}."
        )
    if "HORIZON_FAILCLOSED" in status:
        return (
            f"current source flags close N20 but targetable horizon rows do not: "
            f"targetable_flagged_n={targetable}, current_source_flagged_n={current_source}, "
            f"failclosed_flagged_n={failclosed}, failclosed_reasons={fail_reasons}."
        )
    if "TARGETABILITY_GAP" in status:
        return (
            f"current source flags close N20 but not enough targetable rows were materialized: "
            f"targetable_flagged_n={targetable}, current_source_flagged_n={current_source}, "
            f"failclosed_flagged_n={failclosed}."
        )
    if "PROXY_N20" in status:
        return (
            f"current exact source scope is under N20: targetable_flagged_n={targetable}, "
            f"current_source_flagged_n={current_source}. Expanded proxies close N20 with "
            f"same_symbol_all_sessions_targetable={same_symbol_targetable}, "
            f"same_session_all_symbols_targetable={same_session_targetable}, "
            f"all_market_primitive_targetable={all_market_targetable}, "
            f"same_symbol_all_sessions_source={same_symbol}, "
            f"same_session_all_symbols_source={same_session}, all_market_primitive_source={all_market}."
        )
    return (
        f"current and proxy source scopes remain under N20: targetable_flagged_n={targetable}, "
        f"current_source_flagged_n={current_source}, same_symbol_all_sessions={same_symbol}, "
        f"same_session_all_symbols={same_session}, all_market_primitive={all_market}."
    )
