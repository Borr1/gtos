"""Split runtime replay inventory alignment rows into advancement surfaces."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


RUNTIME_REPLAY_ADVANCEMENT_SURFACE = "src/research_infra/moonshot_repaired_proxy_runtime_replay_advancement.py"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"
SIGNAL_ROUTE_CLASSES = {
    "DEFAULT_OFF_REPLAY_SIGNAL_CANDIDATE_BRANCH_LOCAL",
    "AVOID_REDESIGN_REPLAY_SIGNAL_CANDIDATE_BRANCH_LOCAL",
}


def research_boundary() -> dict[str, Any]:
    return {
        "boundary_schema": BOUNDARY_SCHEMA,
        "artifact_scope": "branch_local_research",
        "production_import_path": False,
        "mutates_order_risk_prompt_safety_or_mt5": False,
        "runtime_candidate_use_permitted": False,
        "unconditional_scalar_use_permitted": False,
    }


def boundary_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["runtime_replay_advancement_surface"] = RUNTIME_REPLAY_ADVANCEMENT_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def advancement_decision(row: dict[str, Any]) -> tuple[str, str]:
    alignment_class = normalized(row.get("inventory_alignment_class"))
    route_class = normalized(row.get("replay_signal_route_class"))
    if alignment_class == "INVENTORY_ALIGNMENT_EXACT_SCOPE_COMPATIBLE" and route_class in SIGNAL_ROUTE_CLASSES:
        return (
            "ADVANCE_REPRESENTED_REPLAY_SIGNAL_TO_COMPARISON_PACKET",
            "REPRESENTED_SIGNAL_ADVANCES",
        )
    if alignment_class == "INVENTORY_ALIGNMENT_EXACT_SCOPE_COMPATIBLE":
        return (
            "CARRY_REPRESENTED_REPLAY_CONTEXT_TO_COMPARISON_PACKET",
            "REPRESENTED_CONTEXT_ADVANCES",
        )
    if alignment_class == "INVENTORY_ALIGNMENT_EXACT_SCOPE_PRESENT_DIFFERENT_ACTION":
        return (
            "RECONCILE_REPLAY_SIGNAL_WITH_UNIFIED_ACTION_BEFORE_ADVANCEMENT",
            "EXACT_SCOPE_ACTION_CONFLICT_REVIEW",
        )
    if alignment_class == "INVENTORY_ALIGNMENT_BROAD_SCOPE_COMPATIBLE":
        return (
            "CARRY_BROAD_SCOPE_COMPATIBLE_REPLAY_SIGNAL_TO_COMPARISON_PACKET",
            "BROAD_SCOPE_COMPATIBLE_ADVANCES",
        )
    if alignment_class == "INVENTORY_ALIGNMENT_BROAD_SCOPE_PRESENT_DIFFERENT_ACTION":
        return (
            "RECONCILE_BROAD_SCOPE_REPLAY_SIGNAL_WITH_UNIFIED_ACTION",
            "BROAD_SCOPE_ACTION_CONFLICT_REVIEW",
        )
    if alignment_class == "INVENTORY_ALIGNMENT_REPLAY_SCOPE_UNMATCHED_REVIEW":
        return (
            "REVIEW_REPLAY_SCOPE_MATCH_BEFORE_ADVANCEMENT",
            "UNMATCHED_SCOPE_REVIEW",
        )
    return (
        "CREATE_SCOPE_INVENTORY_BEFORE_ADVANCEMENT",
        "NO_SCOPE_INVENTORY_REVIEW",
    )


def advancement_decision_rows(alignment_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in alignment_rows:
        action, family = advancement_decision(row)
        output.append(
            boundary_row(
                {
                    "advancement_decision_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-ADVANCE-DECISION-{len(output) + 1:06d}"
                    ),
                    "input_signal_inventory_alignment_row_id": row.get("signal_inventory_alignment_row_id"),
                    "input_replay_signal_route_row_id": row.get("input_replay_signal_route_row_id"),
                    "input_replay_registry_execution_row_id": row.get("input_replay_registry_execution_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "replay_signal_route_class": row.get("replay_signal_route_class"),
                    "inventory_alignment_class": row.get("inventory_alignment_class"),
                    "exact_inventory_candidate_rows": int(row.get("exact_inventory_candidate_rows") or 0),
                    "broad_inventory_candidate_rows": int(row.get("broad_inventory_candidate_rows") or 0),
                    "inventory_decision_group_counts": row.get("inventory_decision_group_counts") or {},
                    "inventory_action_classes": list(row.get("inventory_action_classes") or []),
                    "advancement_action": action,
                    "advancement_family": family,
                    "advancement_decision_status": "RUNTIME_REPLAY_ADVANCEMENT_DECISION_MATERIALIZED_BRANCH_LOCAL",
                }
            )
        )
    return output


def represented_surface_rows(decision_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in decision_rows:
        if row.get("advancement_family") not in {
            "REPRESENTED_SIGNAL_ADVANCES",
            "REPRESENTED_CONTEXT_ADVANCES",
            "BROAD_SCOPE_COMPATIBLE_ADVANCES",
        }:
            continue
        output.append(
            boundary_row(
                {
                    "represented_surface_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-ADVANCE-REPRESENTED-{len(output) + 1:06d}"
                    ),
                    "input_advancement_decision_row_id": row.get("advancement_decision_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "replay_signal_route_class": row.get("replay_signal_route_class"),
                    "inventory_alignment_class": row.get("inventory_alignment_class"),
                    "advancement_action": row.get("advancement_action"),
                    "represented_surface_status": "REPRESENTED_REPLAY_SURFACE_READY_FOR_COMPARISON_PACKET",
                }
            )
        )
    return output


def action_conflict_review_rows(decision_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in decision_rows:
        if row.get("advancement_family") not in {
            "EXACT_SCOPE_ACTION_CONFLICT_REVIEW",
            "BROAD_SCOPE_ACTION_CONFLICT_REVIEW",
        }:
            continue
        output.append(
            boundary_row(
                {
                    "action_conflict_review_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-ADVANCE-CONFLICT-{len(output) + 1:06d}"
                    ),
                    "input_advancement_decision_row_id": row.get("advancement_decision_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "replay_signal_route_class": row.get("replay_signal_route_class"),
                    "inventory_alignment_class": row.get("inventory_alignment_class"),
                    "inventory_decision_group_counts": row.get("inventory_decision_group_counts") or {},
                    "inventory_action_classes": list(row.get("inventory_action_classes") or []),
                    "action_conflict_review_status": "ACTION_CONFLICT_REVIEW_REQUIRED_BEFORE_COMPARISON_PACKET",
                }
            )
        )
    return output


def unmatched_scope_advancement_rows(decision_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in decision_rows:
        if row.get("advancement_family") not in {"UNMATCHED_SCOPE_REVIEW", "NO_SCOPE_INVENTORY_REVIEW"}:
            continue
        output.append(
            boundary_row(
                {
                    "unmatched_scope_advancement_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-ADVANCE-UNMATCHED-{len(output) + 1:06d}"
                    ),
                    "input_advancement_decision_row_id": row.get("advancement_decision_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "replay_signal_route_class": row.get("replay_signal_route_class"),
                    "inventory_alignment_class": row.get("inventory_alignment_class"),
                    "unmatched_scope_advancement_status": "SCOPE_MATCH_REVIEW_REQUIRED_BEFORE_COMPARISON_PACKET",
                }
            )
        )
    return output


def symbol_advancement_rows(decision_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in decision_rows:
        grouped[
            (
                normalized(row.get("symbol")),
                normalized(row.get("route_session")),
                normalized(row.get("horizon_id")),
                normalized(row.get("registry_family")),
            )
        ].append(row)
    output: list[dict[str, Any]] = []
    for (symbol, route_session, horizon_id, registry_family), rows in sorted(grouped.items()):
        family_counts = Counter(normalized(row.get("advancement_family")) for row in rows)
        output.append(
            boundary_row(
                {
                    "symbol_advancement_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-ADVANCE-SYMBOL-{len(output) + 1:05d}"
                    ),
                    "symbol": symbol,
                    "route_session": route_session,
                    "horizon_id": horizon_id,
                    "registry_family": registry_family,
                    "advancement_decision_rows": len(rows),
                    "advancement_family_counts": dict(sorted(family_counts.items())),
                    "symbol_advancement_status": "SYMBOL_RUNTIME_REPLAY_ADVANCEMENT_ROLLED_UP_BRANCH_LOCAL",
                }
            )
        )
    return output


def system_advancement_rows(decision_rows: list[dict[str, Any]], symbol_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    family_counts = Counter(normalized(row.get("advancement_family")) for row in decision_rows)
    action_counts = Counter(normalized(row.get("advancement_action")) for row in decision_rows)
    return [
        boundary_row(
            {
                "system_advancement_row_id": "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-ADVANCE-SYSTEM-0001",
                "advancement_decision_rows": len(decision_rows),
                "symbol_advancement_rows": len(symbol_rows),
                "advancement_family_counts": dict(sorted(family_counts.items())),
                "advancement_action_counts": dict(sorted(action_counts.items())),
                "system_advancement": (
                    "Advance represented replay surfaces to comparison, route exact-scope action conflicts to "
                    "reconciliation, and preserve unmatched scopes for review."
                ),
                "system_advancement_status": "RUNTIME_REPLAY_ADVANCEMENT_SYSTEM_DECISION_MATERIALIZED_BRANCH_LOCAL",
            }
        )
    ]


def advancement_bucket_rows(
    decision_rows: list[dict[str, Any]],
    represented_rows: list[dict[str, Any]],
    conflict_rows: list[dict[str, Any]],
    unmatched_rows: list[dict[str, Any]],
    symbol_rows: list[dict[str, Any]],
    system_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs = [
        ("advancement_family", decision_rows, "advancement_family"),
        ("advancement_action", decision_rows, "advancement_action"),
        ("represented_surface_status", represented_rows, "represented_surface_status"),
        ("action_conflict_review_status", conflict_rows, "action_conflict_review_status"),
        ("unmatched_scope_advancement_status", unmatched_rows, "unmatched_scope_advancement_status"),
        ("symbol_advancement_status", symbol_rows, "symbol_advancement_status"),
        ("system_advancement_status", system_rows, "system_advancement_status"),
    ]
    output: list[dict[str, Any]] = []
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "advancement_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-ADVANCE-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
