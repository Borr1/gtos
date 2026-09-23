"""Execute branch-local comparator decisions for repaired-proxy comparator inputs."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any


COMPARATOR_EXECUTION_SURFACE = "src/research_infra/moonshot_repaired_proxy_comparator_execution.py"
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
    output["comparator_execution_surface"] = COMPARATOR_EXECUTION_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def as_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def comparator_execution_decision(row: dict[str, Any]) -> tuple[str, str]:
    family = normalized(row.get("comparator_input_family"))
    score_index = as_float(row.get("score_context_index_mean"))
    net_proxy = as_float(row.get("net_proxy_r_mean"))
    bridge_rows = int(row.get("bridge_rows") or 0)

    if bridge_rows <= 0:
        return "COMPARATOR_EXECUTION_BLOCKED_EMPTY_INPUT", "BLOCK_EMPTY_COMPARATOR_INPUT"
    if family == "DEFAULT_OFF_SCORER_COMPARATOR_INPUT":
        if score_index is not None and net_proxy is not None and score_index > 0.05 and net_proxy > 0:
            return "COMPARATOR_EXECUTION_DEFAULT_OFF_SCORER_CANDIDATE", "REGISTER_DEFAULT_OFF_SCORER_COMPARATOR"
        if score_index is not None and score_index <= 0:
            return "COMPARATOR_EXECUTION_DEFAULT_OFF_REJECT_NEGATIVE_CONTEXT", "DO_NOT_REGISTER_DEFAULT_OFF_SCORER"
        return "COMPARATOR_EXECUTION_DEFAULT_OFF_HOLD_WEAK_OR_INCOMPLETE_CONTEXT", "HOLD_DEFAULT_OFF_SCORER_CONTEXT"
    if family == "AVOID_REDESIGN_COMPARATOR_INPUT":
        if (score_index is not None and score_index < -0.05) or (net_proxy is not None and net_proxy < 0):
            return "COMPARATOR_EXECUTION_AVOID_REDESIGN_CANDIDATE", "REGISTER_AVOID_REDESIGN_COMPARATOR"
        if score_index is not None and score_index >= 0:
            return "COMPARATOR_EXECUTION_AVOID_REJECT_NONNEGATIVE_CONTEXT", "DO_NOT_REGISTER_AVOID_COMPARATOR"
        return "COMPARATOR_EXECUTION_AVOID_HOLD_WEAK_OR_INCOMPLETE_CONTEXT", "HOLD_AVOID_COMPARATOR_CONTEXT"
    return "COMPARATOR_EXECUTION_UNKNOWN_INPUT_FAMILY", "HOLD_UNKNOWN_COMPARATOR_INPUT"


def comparator_execution_rows(
    comparator_input_rows: list[dict[str, Any]], source_exhaustion_gate_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    gate_status = (
        normalized(source_exhaustion_gate_rows[0].get("source_exhaustion_gate_status"))
        if source_exhaustion_gate_rows
        else ""
    )
    output: list[dict[str, Any]] = []
    for row in comparator_input_rows:
        status, action = comparator_execution_decision(row)
        output.append(
            boundary_row(
                {
                    "comparator_execution_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-COMPARATOR-EXEC-{len(output) + 1:05d}"
                    ),
                    "input_comparator_input_row_id": row.get("comparator_input_row_id"),
                    "input_action_scope_row_id": row.get("input_action_scope_row_id"),
                    "input_comparator_packet_row_id": row.get("input_comparator_packet_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "comparator_input_family": row.get("comparator_input_family"),
                    "rerun_registry_family": row.get("rerun_registry_family"),
                    "bridge_rows": int(row.get("bridge_rows") or 0),
                    "score_context_index_mean": as_float(row.get("score_context_index_mean")),
                    "net_proxy_r_mean": as_float(row.get("net_proxy_r_mean")),
                    "primitive_flag_count": int(row.get("primitive_flag_count") or 0),
                    "source_exhaustion_gate_status": gate_status,
                    "comparator_execution_status": status,
                    "comparator_execution_action": action,
                    "comparator_execution_use": "BRANCH_LOCAL_RESEARCH_COMPARATOR_EXECUTION_ONLY",
                }
            )
        )
    return output


def proxy_r_surface_rows(execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in execution_rows:
        net_proxy = as_float(row.get("net_proxy_r_mean"))
        score_index = as_float(row.get("score_context_index_mean"))
        output.append(
            boundary_row(
                {
                    "proxy_r_surface_row_id": f"OHLC-GTOS-REPAIRED-PROXY-COMPARATOR-PROXYR-{len(output) + 1:05d}",
                    "input_comparator_execution_row_id": row.get("comparator_execution_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "bridge_rows": row.get("bridge_rows"),
                    "net_proxy_r_mean": net_proxy,
                    "score_context_index_mean": score_index,
                    "proxy_context_delta": None if net_proxy is None or score_index is None else score_index - net_proxy,
                    "proxy_r_surface_status": "COMPARATOR_PROXY_R_SURFACE_AVAILABLE_CURRENT_BRANCH",
                }
            )
        )
    return output


def symbol_execution_summary_rows(execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in execution_rows:
        grouped[
            (
                normalized(row.get("symbol")),
                normalized(row.get("route_session")),
                normalized(row.get("comparator_input_family")),
            )
        ].append(row)
    output: list[dict[str, Any]] = []
    for (symbol, route_session, family), rows in sorted(grouped.items()):
        net_values = [as_float(row.get("net_proxy_r_mean")) for row in rows]
        score_values = [as_float(row.get("score_context_index_mean")) for row in rows]
        net_clean = [value for value in net_values if value is not None]
        score_clean = [value for value in score_values if value is not None]
        status_counts = Counter(normalized(row.get("comparator_execution_status")) for row in rows)
        output.append(
            boundary_row(
                {
                    "symbol_execution_summary_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-COMPARATOR-SUMMARY-{len(output) + 1:04d}"
                    ),
                    "symbol": symbol,
                    "route_session": route_session,
                    "comparator_input_family": family,
                    "comparator_execution_rows": len(rows),
                    "bridge_rows": sum(int(row.get("bridge_rows") or 0) for row in rows),
                    "net_proxy_r_mean": mean(net_clean) if net_clean else None,
                    "score_context_index_mean": mean(score_clean) if score_clean else None,
                    "execution_status_counts": dict(sorted(status_counts.items())),
                }
            )
        )
    return output


def comparator_action_rows(execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in execution_rows:
        grouped[normalized(row.get("comparator_execution_action"))].append(row)
    output: list[dict[str, Any]] = []
    for action, rows in sorted(grouped.items()):
        output.append(
            boundary_row(
                {
                    "comparator_action_row_id": f"OHLC-GTOS-REPAIRED-PROXY-COMPARATOR-ACTION-{len(output) + 1:04d}",
                    "comparator_execution_action": action,
                    "comparator_execution_rows": len(rows),
                    "bridge_rows": sum(int(row.get("bridge_rows") or 0) for row in rows),
                    "symbols": sorted({normalized(row.get("symbol")) for row in rows}),
                    "action_status": "COMPARATOR_ACTION_MATERIALIZED_BRANCH_LOCAL",
                }
            )
        )
    return output


def comparator_bucket_rows(
    execution_rows: list[dict[str, Any]],
    proxy_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    action_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs = [
        ("comparator_execution_status", execution_rows, "comparator_execution_status"),
        ("comparator_execution_action", execution_rows, "comparator_execution_action"),
        ("proxy_r_surface_status", proxy_rows, "proxy_r_surface_status"),
        ("symbol_family", summary_rows, "comparator_input_family"),
        ("action_status", action_rows, "action_status"),
    ]
    output: list[dict[str, Any]] = []
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "comparator_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-COMPARATOR-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
