"""Align runtime replay recommendations with the branch-local unified decision inventory."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


RUNTIME_REPLAY_INVENTORY_ALIGNMENT_SURFACE = (
    "src/research_infra/moonshot_repaired_proxy_runtime_replay_inventory_alignment.py"
)
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"


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
    output["runtime_replay_inventory_alignment_surface"] = RUNTIME_REPLAY_INVENTORY_ALIGNMENT_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def scope_key(row: dict[str, Any], include_source: bool = True) -> tuple[str, str, str, str] | tuple[str, str, str]:
    base = (
        normalized(row.get("symbol")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
    )
    if include_source:
        return (*base, normalized(row.get("source_component")))
    return base


def candidate_indexes(
    unified_rows: list[dict[str, Any]],
) -> tuple[dict[tuple[str, str, str, str], list[dict[str, Any]]], dict[tuple[str, str, str], list[dict[str, Any]]]]:
    exact: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    broad: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in unified_rows:
        exact[scope_key(row, include_source=True)].append(row)
        broad[scope_key(row, include_source=False)].append(row)
    return exact, broad


def decision_group_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(normalized(row.get("unified_decision_group")) for row in rows).items()))


def action_classes(rows: list[dict[str, Any]]) -> list[str]:
    return sorted({normalized(row.get("unified_action_class")) for row in rows if row.get("unified_action_class")})


def compatible_alignment(route_class: str, rows: list[dict[str, Any]]) -> bool:
    groups = {normalized(row.get("unified_decision_group")) for row in rows}
    actions = {normalized(row.get("unified_action_class")) for row in rows}
    if route_class == "DEFAULT_OFF_REPLAY_SIGNAL_CANDIDATE_BRANCH_LOCAL":
        return bool(groups & {"IMPLEMENT", "SCORE_WITH_CONTROL"} or any("DEFAULT_OFF" in action for action in actions))
    if route_class == "AVOID_REDESIGN_REPLAY_SIGNAL_CANDIDATE_BRANCH_LOCAL":
        return bool(groups & {"REDESIGN", "IMPLEMENT"} or any("AVOID" in action or "REDESIGN" in action for action in actions))
    if route_class == "REPLAY_SIGNAL_CONTEXT_ONLY_BRANCH_LOCAL":
        return bool(groups & {"SCORE_WITH_CONTROL", "GUARD"})
    if route_class == "REPLAY_REPAIR_CONTEXT_CARRY_BRANCH_LOCAL":
        return bool(groups & {"SOURCE_OR_CONTROL_REPAIR"})
    return False


def alignment_class(route_row: dict[str, Any], exact_rows: list[dict[str, Any]], broad_rows: list[dict[str, Any]]) -> str:
    route = normalized(route_row.get("replay_signal_route_class"))
    if route == "REPLAY_SCOPE_UNMATCHED_REVIEW_BRANCH_LOCAL":
        return "INVENTORY_ALIGNMENT_REPLAY_SCOPE_UNMATCHED_REVIEW"
    if exact_rows and compatible_alignment(route, exact_rows):
        return "INVENTORY_ALIGNMENT_EXACT_SCOPE_COMPATIBLE"
    if exact_rows:
        return "INVENTORY_ALIGNMENT_EXACT_SCOPE_PRESENT_DIFFERENT_ACTION"
    if broad_rows and compatible_alignment(route, broad_rows):
        return "INVENTORY_ALIGNMENT_BROAD_SCOPE_COMPATIBLE"
    if broad_rows:
        return "INVENTORY_ALIGNMENT_BROAD_SCOPE_PRESENT_DIFFERENT_ACTION"
    return "INVENTORY_ALIGNMENT_NO_SCOPE_IN_UNIFIED_INVENTORY"


def signal_inventory_alignment_rows(
    signal_rows: list[dict[str, Any]], unified_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    exact_index, broad_index = candidate_indexes(unified_rows)
    output: list[dict[str, Any]] = []
    for row in signal_rows:
        exact_rows = exact_index.get(scope_key(row, include_source=True), [])
        broad_rows = broad_index.get(scope_key(row, include_source=False), [])
        chosen = exact_rows if exact_rows else broad_rows
        output.append(
            boundary_row(
                {
                    "signal_inventory_alignment_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-INVENTORY-ALIGN-{len(output) + 1:06d}"
                    ),
                    "input_replay_signal_route_row_id": row.get("replay_signal_route_row_id"),
                    "input_replay_registry_execution_row_id": row.get("input_replay_registry_execution_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "replay_signal_route_class": row.get("replay_signal_route_class"),
                    "exact_inventory_candidate_rows": len(exact_rows),
                    "broad_inventory_candidate_rows": len(broad_rows),
                    "inventory_decision_group_counts": decision_group_counts(chosen),
                    "inventory_action_classes": action_classes(chosen),
                    "inventory_alignment_class": alignment_class(row, exact_rows, broad_rows),
                    "signal_inventory_alignment_status": "SIGNAL_INVENTORY_ALIGNMENT_MATERIALIZED_BRANCH_LOCAL",
                }
            )
        )
    return output


def symbol_inventory_alignment_rows(alignment_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in alignment_rows:
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
        classes = Counter(normalized(row.get("inventory_alignment_class")) for row in rows)
        output.append(
            boundary_row(
                {
                    "symbol_inventory_alignment_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-INVENTORY-SYMBOL-{len(output) + 1:05d}"
                    ),
                    "symbol": symbol,
                    "route_session": route_session,
                    "horizon_id": horizon_id,
                    "registry_family": registry_family,
                    "signal_inventory_alignment_rows": len(rows),
                    "exact_inventory_candidate_rows": sum(int(row.get("exact_inventory_candidate_rows") or 0) for row in rows),
                    "broad_inventory_candidate_rows": sum(int(row.get("broad_inventory_candidate_rows") or 0) for row in rows),
                    "inventory_alignment_class_counts": dict(sorted(classes.items())),
                    "symbol_inventory_alignment_status": "SYMBOL_INVENTORY_ALIGNMENT_ROLLED_UP_BRANCH_LOCAL",
                }
            )
        )
    return output


def system_inventory_alignment_rows(alignment_rows: list[dict[str, Any]], symbol_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    class_counts = Counter(normalized(row.get("inventory_alignment_class")) for row in alignment_rows)
    return [
        boundary_row(
            {
                "system_inventory_alignment_row_id": "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-INVENTORY-SYSTEM-0001",
                "signal_inventory_alignment_rows": len(alignment_rows),
                "symbol_inventory_alignment_rows": len(symbol_rows),
                "inventory_alignment_class_counts": dict(sorted(class_counts.items())),
                "system_inventory_alignment": (
                    "Use exact and broad inventory alignment to separate replay signals already represented in the "
                    "unified decision inventory from unmatched scopes that need review."
                ),
                "system_inventory_alignment_status": "SYSTEM_INVENTORY_ALIGNMENT_MATERIALIZED_BRANCH_LOCAL",
            }
        )
    ]


def inventory_alignment_bucket_rows(
    alignment_rows: list[dict[str, Any]],
    symbol_rows: list[dict[str, Any]],
    system_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs = [
        ("inventory_alignment_class", alignment_rows, "inventory_alignment_class"),
        ("signal_inventory_alignment_status", alignment_rows, "signal_inventory_alignment_status"),
        ("symbol_inventory_alignment_status", symbol_rows, "symbol_inventory_alignment_status"),
        ("system_inventory_alignment_status", system_rows, "system_inventory_alignment_status"),
    ]
    output: list[dict[str, Any]] = []
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "inventory_alignment_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-INVENTORY-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
