"""Branch-local source-stress router helpers.

These helpers are research-only pure functions. They consume row dictionaries
from the weekend moonshot score-export/follow-up ledgers and return mechanical
same-resource routing labels. They do not read broker state, place orders, or
make live-readiness claims.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable


CLASS_COST_SENSITIVE = "SOURCE_COST_SENSITIVE_RISK_ROUTER_ACQUIRE_EXACT_OR_CAP_COST_MODEL"
CLASS_NEGATIVE = "SOURCE_CONSERVATIVE_NEGATIVE_AVOID_OR_ACQUIRE_EXACT_SOURCE"
CLASS_STRADDLE = "SOURCE_STRADDLE_BOUNDS_ACQUIRE_EXACT_OR_SPLIT_COST_MODEL"
CLASS_NOT_EXPORTED = "SOURCE_NOT_EXPORTED_PRESERVE_UPSTREAM_PROXY_OR_CLEAN_SOURCE"


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def interval_sign_class(lower: Any, upper: Any, midpoint: Any = None) -> str:
    """Classify a lower/upper proxy interval around zero."""

    lower_value = _to_float(lower)
    upper_value = _to_float(upper)
    midpoint_value = _to_float(midpoint)
    if lower_value is None or upper_value is None:
        return "INTERVAL_NOT_AVAILABLE"
    if lower_value > 0 and upper_value > 0:
        return "INTERVAL_ALL_POSITIVE"
    if lower_value < 0 and upper_value < 0:
        return "INTERVAL_ALL_NEGATIVE"
    if lower_value <= 0 <= upper_value:
        if midpoint_value is None:
            return "INTERVAL_STRADDLES_ZERO"
        if midpoint_value > 0:
            return "INTERVAL_STRADDLES_ZERO_MIDPOINT_POSITIVE"
        return "INTERVAL_STRADDLES_ZERO_MIDPOINT_NONPOSITIVE"
    return "INTERVAL_OTHER"


def classify_source_router(row: dict[str, Any] | None) -> dict[str, Any]:
    """Return the source-router class for one source export row."""

    if not row:
        return {
            "source_router_followup_class": CLASS_NOT_EXPORTED,
            "source_stress_interval_sign_class": "INTERVAL_NOT_AVAILABLE",
            "source_router_action": "preserve_upstream_proxy_or_clean_source",
        }

    export_class = row.get("source_export_class")
    if export_class == "SOURCE_ROUTER_POSITIVE_LOW_SPREAD_BUT_HIGH_SPREAD_FLIP":
        followup_class = CLASS_COST_SENSITIVE
        action = "acquire_exact_source_or_cap_cost_model_before_positive_use"
    elif export_class == "SOURCE_ROUTER_NEGATIVE_AVOID_OR_ACQUIRE_EXACT_SOURCE":
        followup_class = CLASS_NEGATIVE
        action = "avoid_or_require_exact_source_repair_before_reconsidering"
    else:
        followup_class = CLASS_STRADDLE
        action = "split_cost_model_bounds_and_acquire_exact_source"

    return {
        "source_router_followup_class": followup_class,
        "source_stress_interval_sign_class": interval_sign_class(
            row.get("stress_lower_mean"),
            row.get("stress_upper_mean"),
            row.get("stress_midpoint_mean"),
        ),
        "source_router_action": action,
    }


def summarize_source_router(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, int]]:
    """Summarize source-router classifications for a full ledger."""

    class_counts: Counter[str] = Counter()
    interval_counts: Counter[str] = Counter()
    export_counts: Counter[str] = Counter()
    for row in rows:
        classified = classify_source_router(row)
        class_counts[classified["source_router_followup_class"]] += 1
        interval_counts[classified["source_stress_interval_sign_class"]] += 1
        export_counts[str(row.get("source_export_class"))] += 1
    return {
        "source_router_followup_class": dict(sorted(class_counts.items())),
        "source_stress_interval_sign_class": dict(sorted(interval_counts.items())),
        "source_export_class": dict(sorted(export_counts.items())),
    }
