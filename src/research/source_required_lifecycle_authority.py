"""Shared replay-only source-required lifecycle authority helpers.

These constants describe local replay reconciliation authority only. They do
not grant broker mutation, live trading, or final-selection authority.
"""

from __future__ import annotations

from typing import Any, Mapping


SOURCE_REQUIRED_FAIL_CLOSED_REPLAY_OVERRIDE_REASONS = frozenset(
    {
        "source_required_fail_closed_package_source_reconciled_for_replay",
        "source_required_fail_closed_package_new_position_source_gap_reconciled_for_replay",
        "package_same_direction_scale_in_lifecycle_reconciled_for_replay",
        "source_required_fail_closed_package_close_reverse_reconciled_for_replay",
        "source_required_fail_closed_package_replace_pending_reconciled_for_replay",
    }
)
SOURCE_REQUIRED_SELECTOR_HOLD_REPLAY_OVERRIDE_REASONS = frozenset(
    {
        "source_required_selector_hold_package_source_reconciled_for_replay",
    }
)
REPLAY_LIFECYCLE_ACTION_RESOLVER_OVERRIDE_REASONS = frozenset(
    {
        "replay_lifecycle_action_resolver_same_direction_scale_in",
        "replay_lifecycle_action_resolver_same_side_pending_replace_pending",
        "replay_lifecycle_action_resolver_close_and_reverse",
        "replay_lifecycle_action_resolver_replace_pending",
    }
)
SOURCE_REQUIRED_REPLAY_OVERRIDE_REASONS = frozenset(
    set(SOURCE_REQUIRED_FAIL_CLOSED_REPLAY_OVERRIDE_REASONS)
    | set(SOURCE_REQUIRED_SELECTOR_HOLD_REPLAY_OVERRIDE_REASONS)
    | set(REPLAY_LIFECYCLE_ACTION_RESOLVER_OVERRIDE_REASONS)
)

SOURCE_REQUIRED_REPLAY_OVERRIDE_APPLIED_FIELDS = (
    "scheduler_materialization_source_required_selector_hold_override_applied",
    "scheduler_materialization_source_required_fail_closed_override_applied",
    "source_required_fail_closed_replay_override_applied",
    "scheduler_materialization_replay_lifecycle_action_resolver_applied",
    "source_required_lifecycle_resolver_replay_override_applied",
)


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on", "enabled"}
    return bool(value)


def source_required_replay_override_reason_allowed(reason: Any) -> bool:
    return str(reason or "").strip() in SOURCE_REQUIRED_REPLAY_OVERRIDE_REASONS


def source_required_replay_override_reason(row: Mapping[str, Any]) -> str:
    for field in (
        "scheduler_materialization_override_reason",
        "source_required_fail_closed_replay_override_reason",
        "scheduler_materialization_source_required_fail_closed_override_reason",
        "scheduler_materialization_replay_lifecycle_action_resolver_reason",
        "source_required_lifecycle_replay_override_reason",
        "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_reason",
    ):
        text = str(row.get(field) or "").strip()
        if text:
            return text
    return ""


def source_required_replay_override_reason_allowed_for_row(
    row: Mapping[str, Any],
) -> bool:
    return source_required_replay_override_reason_allowed(
        source_required_replay_override_reason(row)
    )


def source_required_replay_override_applied(row: Mapping[str, Any]) -> bool:
    return any(
        _truthy(row.get(field))
        for field in SOURCE_REQUIRED_REPLAY_OVERRIDE_APPLIED_FIELDS
    )


def source_required_replay_override_kind(row: Mapping[str, Any]) -> str | None:
    if _truthy(
        row.get("scheduler_materialization_source_required_selector_hold_override_applied")
    ):
        return "selector_hold"
    if _truthy(
        row.get("scheduler_materialization_source_required_fail_closed_override_applied")
    ):
        return "fail_closed"
    if _truthy(row.get("source_required_fail_closed_replay_override_applied")):
        return "fail_closed"
    if _truthy(
        row.get("scheduler_materialization_replay_lifecycle_action_resolver_applied")
    ):
        return "replay_lifecycle_action_resolver"
    if _truthy(row.get("source_required_lifecycle_resolver_replay_override_applied")):
        return "replay_lifecycle_action_resolver"
    return None
