"""Branch-local M1 support-conflict router helpers."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable


CLASS_STABLE = "M1_SUPPORT_AND_BRANCH_TARGET_STABLE_CHALLENGER_COMPUTED"
CLASS_CONFLICT = "M1_SUPPORT_POSITIVE_BRANCH_AGGREGATE_CONFLICT_SPLIT_COMPUTED"
CLASS_NOT_EXPORTED = "M1_NOT_EXPORTED_PRESERVE_NON_M1_ORDERING_ROUTE"


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def point_sign_class(value: Any) -> str:
    value_float = _to_float(value)
    if value_float is None:
        return "POINT_NOT_AVAILABLE"
    if value_float > 0:
        return "POINT_POSITIVE"
    if value_float < 0:
        return "POINT_NEGATIVE"
    return "POINT_ZERO"


def classify_m1_conflict(row: dict[str, Any] | None) -> dict[str, Any]:
    """Return the M1 support-vs-branch conflict class for one row."""

    if not row:
        return {
            "m1_followup_class": CLASS_NOT_EXPORTED,
            "m1_branch_midpoint_sign_class": "POINT_NOT_AVAILABLE",
            "m1_support_midpoint_sign_class": "POINT_NOT_AVAILABLE",
            "support_vs_branch_delta_sign_class": "POINT_NOT_AVAILABLE",
            "exact_chronology_claim": False,
            "tick_ordering_exact": False,
            "m1_action": "preserve_non_m1_ordering_route",
        }

    if row.get("m1_export_class") == "M1_EXPORT_SUPPORT_POSITIVE_BRANCH_CONFLICT_SPLIT":
        followup_class = CLASS_CONFLICT
        action = "split_support_positive_branch_aggregate_conflict"
    else:
        followup_class = CLASS_STABLE
        action = "score_support_and_branch_target_stable_challenger"

    return {
        "m1_followup_class": followup_class,
        "m1_branch_midpoint_sign_class": point_sign_class(row.get("branch_midpoint_mean")),
        "m1_support_midpoint_sign_class": point_sign_class(row.get("m1_support_midpoint_mean")),
        "support_vs_branch_delta_sign_class": point_sign_class(row.get("m1_support_minus_branch_midpoint")),
        "exact_chronology_claim": False,
        "tick_ordering_exact": False,
        "m1_action": action,
    }


def summarize_m1_conflict(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, int]]:
    class_counts: Counter[str] = Counter()
    branch_sign_counts: Counter[str] = Counter()
    support_sign_counts: Counter[str] = Counter()
    export_counts: Counter[str] = Counter()
    for row in rows:
        classified = classify_m1_conflict(row)
        class_counts[classified["m1_followup_class"]] += 1
        branch_sign_counts[classified["m1_branch_midpoint_sign_class"]] += 1
        support_sign_counts[classified["m1_support_midpoint_sign_class"]] += 1
        export_counts[str(row.get("m1_export_class"))] += 1
    return {
        "m1_followup_class": dict(sorted(class_counts.items())),
        "m1_branch_midpoint_sign_class": dict(sorted(branch_sign_counts.items())),
        "m1_support_midpoint_sign_class": dict(sorted(support_sign_counts.items())),
        "m1_export_class": dict(sorted(export_counts.items())),
    }
