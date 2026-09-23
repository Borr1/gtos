"""Branch-local entry/adverse redesign router helpers."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable


CLASS_BOTH = "ENTRY_AND_ADVERSE_REDESIGN_COMPUTED"
CLASS_ENTRY_ONLY = "ENTRY_REDESIGN_COMPUTED_ADVERSE_PRESERVED"
CLASS_PRESERVE = "ENTRY_ADVERSE_PRESERVE_NO_REDESIGN_SCOPE"


def classify_entry_target_stop_balance(row: dict[str, Any] | None) -> str:
    if not row:
        return "ENTRY_BALANCE_NOT_AVAILABLE"
    target_first = int(row.get("target_first_rows") or 0)
    stop_first = int(row.get("stop_first_rows") or 0)
    no_fill = int(row.get("no_fill_or_unfilled_rows") or 0)
    if target_first > stop_first and target_first > no_fill:
        return "TARGET_FIRST_COUNT_DOMINANT"
    if stop_first > target_first and stop_first > no_fill:
        return "STOP_FIRST_COUNT_DOMINANT"
    if no_fill > target_first and no_fill > stop_first:
        return "NO_FILL_COUNT_DOMINANT"
    return "BALANCED_OR_TIED_COUNTS"


def classify_entry_adverse_redesign(row: dict[str, Any] | None) -> dict[str, Any]:
    """Return the entry/adverse redesign class for one row."""

    if not row:
        return {
            "entry_adverse_followup_class": "ENTRY_ADVERSE_MISSING_EXPORT",
            "entry_target_stop_balance_class": "ENTRY_BALANCE_NOT_AVAILABLE",
            "entry_adverse_action": "missing_entry_adverse_export",
        }

    export_class = row.get("entry_adverse_export_class")
    if export_class == "ENTRY_ADVERSE_EXPORT_BOTH_REDESIGN_SCORE":
        followup_class = CLASS_BOTH
        action = "score_entry_redesign_and_adverse_stop_first_redesign"
    elif export_class == "ENTRY_ADVERSE_EXPORT_ENTRY_REDESIGN_SCORE":
        followup_class = CLASS_ENTRY_ONLY
        action = "score_entry_redesign_preserve_adverse_context"
    else:
        followup_class = CLASS_PRESERVE
        action = "preserve_no_redesign_scope"

    return {
        "entry_adverse_followup_class": followup_class,
        "entry_target_stop_balance_class": classify_entry_target_stop_balance(row),
        "entry_adverse_action": action,
    }


def summarize_entry_adverse(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, int]]:
    class_counts: Counter[str] = Counter()
    balance_counts: Counter[str] = Counter()
    export_counts: Counter[str] = Counter()
    for row in rows:
        classified = classify_entry_adverse_redesign(row)
        class_counts[classified["entry_adverse_followup_class"]] += 1
        balance_counts[classified["entry_target_stop_balance_class"]] += 1
        export_counts[str(row.get("entry_adverse_export_class"))] += 1
    return {
        "entry_adverse_followup_class": dict(sorted(class_counts.items())),
        "entry_target_stop_balance_class": dict(sorted(balance_counts.items())),
        "entry_adverse_export_class": dict(sorted(export_counts.items())),
    }
