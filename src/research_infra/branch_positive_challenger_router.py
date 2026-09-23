"""Branch-local positive challenger replay router helpers."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from .branch_source_router import interval_sign_class


CLASS_REPLAY_NOW = "POSITIVE_REPLAY_NOW_PROXY_OR_EXACT_REPAIR_COMPUTED"
CLASS_REPAIR_FIRST = "POSITIVE_SOURCE_REPAIR_OR_STRESS_FIRST_BEFORE_REPLAY"
CLASS_NOT_EXPORTED = "POSITIVE_NOT_EXPORTED_NO_CHALLENGER_SCOPE"


def classify_positive_modifier(row: dict[str, Any] | None) -> str:
    if not row:
        return "POSITIVE_NO_MODIFIER_SCOPE"
    control_stressed = row.get("positive_control_delta_modifier_class") == "CONTROL_DELTA_ADVERSE_OR_BELOW_ROUTE_PEERS"
    concentration_stressed = row.get("positive_concentration_modifier_class") == "CONCENTRATION_OR_EFFECTIVE_N_STRESSED"
    if control_stressed and concentration_stressed:
        return "POSITIVE_CONTROL_AND_CONCENTRATION_STRESSED"
    if control_stressed:
        return "POSITIVE_CONTROL_STRESSED_ONLY"
    if concentration_stressed:
        return "POSITIVE_CONCENTRATION_STRESSED_ONLY"
    return "POSITIVE_MODIFIERS_NOT_STRESSED"


def classify_positive_replay(row: dict[str, Any] | None) -> dict[str, Any]:
    """Return the positive challenger replay class for one row."""

    if not row:
        return {
            "positive_followup_class": CLASS_NOT_EXPORTED,
            "positive_interval_sign_class": "INTERVAL_NOT_AVAILABLE",
            "positive_modifier_class": "POSITIVE_NO_MODIFIER_SCOPE",
            "positive_action": "no_positive_challenger_scope",
        }

    if row.get("positive_replayable_now") is True:
        followup_class = CLASS_REPLAY_NOW
        action = "replay_now_with_proxy_or_exact_repair_context"
    else:
        followup_class = CLASS_REPAIR_FIRST
        action = "repair_source_or_preserve_stress_bounds_before_replay"

    return {
        "positive_followup_class": followup_class,
        "positive_interval_sign_class": interval_sign_class(
            row.get("positive_lower_mean"),
            row.get("positive_upper_mean"),
            row.get("positive_midpoint_mean"),
        ),
        "positive_modifier_class": classify_positive_modifier(row),
        "positive_action": action,
    }


def summarize_positive_replay(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, int]]:
    class_counts: Counter[str] = Counter()
    interval_counts: Counter[str] = Counter()
    modifier_counts: Counter[str] = Counter()
    export_counts: Counter[str] = Counter()
    for row in rows:
        classified = classify_positive_replay(row)
        class_counts[classified["positive_followup_class"]] += 1
        interval_counts[classified["positive_interval_sign_class"]] += 1
        modifier_counts[classified["positive_modifier_class"]] += 1
        export_counts[str(row.get("positive_export_class"))] += 1
    return {
        "positive_followup_class": dict(sorted(class_counts.items())),
        "positive_interval_sign_class": dict(sorted(interval_counts.items())),
        "positive_modifier_class": dict(sorted(modifier_counts.items())),
        "positive_export_class": dict(sorted(export_counts.items())),
    }
