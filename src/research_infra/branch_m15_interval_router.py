"""Branch-local M15 interval router helpers."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from .branch_source_router import interval_sign_class


CLASS_TARGET = "M15_TARGET_FIRST_CHALLENGER_INTERVAL_COMPUTED"
CLASS_STOP = "M15_STOP_FIRST_AVOID_OR_REDESIGN_INTERVAL_COMPUTED"
CLASS_BOUNDS = "M15_INTERVAL_BOUNDS_ROUTER_COMPUTED"
CLASS_NOT_EXPORTED = "M15_NOT_EXPORTED_PRESERVE_NON_M15_ORDERING_ROUTE"


def classify_m15_interval(row: dict[str, Any] | None) -> dict[str, Any]:
    """Return the M15 target/stop/bounds class for one M15 export row."""

    if not row:
        return {
            "m15_followup_class": CLASS_NOT_EXPORTED,
            "m15_interval_sign_class": "INTERVAL_NOT_AVAILABLE",
            "exact_chronology_claim": False,
            "m15_action": "preserve_non_m15_ordering_route",
        }

    export_class = row.get("m15_export_class")
    if export_class == "M15_EXPORT_TARGET_FIRST_CHALLENGER":
        followup_class = CLASS_TARGET
        action = "score_target_first_challenger_with_interval_bounds"
    elif export_class == "M15_EXPORT_STOP_FIRST_AVOID_OR_REDESIGN":
        followup_class = CLASS_STOP
        action = "score_stop_first_avoid_or_redesign_with_interval_bounds"
    else:
        followup_class = CLASS_BOUNDS
        action = "preserve_target_first_stop_first_midpoint_bounds"

    return {
        "m15_followup_class": followup_class,
        "m15_interval_sign_class": interval_sign_class(
            row.get("interval_lower_mean"),
            row.get("interval_upper_mean"),
            row.get("interval_midpoint_mean"),
        ),
        "exact_chronology_claim": False,
        "m15_action": action,
    }


def summarize_m15_interval(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, int]]:
    class_counts: Counter[str] = Counter()
    interval_counts: Counter[str] = Counter()
    export_counts: Counter[str] = Counter()
    for row in rows:
        classified = classify_m15_interval(row)
        class_counts[classified["m15_followup_class"]] += 1
        interval_counts[classified["m15_interval_sign_class"]] += 1
        export_counts[str(row.get("m15_export_class"))] += 1
    return {
        "m15_followup_class": dict(sorted(class_counts.items())),
        "m15_interval_sign_class": dict(sorted(interval_counts.items())),
        "m15_export_class": dict(sorted(export_counts.items())),
    }
