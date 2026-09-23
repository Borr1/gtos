"""Materialize repaired-proxy comparator registration candidates into branch-local specs."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any


REGISTRATION_SPEC_SURFACE = "src/research_infra/moonshot_repaired_proxy_registration_specs.py"
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
    output["registration_spec_surface"] = REGISTRATION_SPEC_SURFACE
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


def spec_parameters(row: dict[str, Any]) -> tuple[str, dict[str, Any], list[str]]:
    family = normalized(row.get("registration_family"))
    if family == "DEFAULT_OFF_SCORER_COMPARATOR_REGISTRATION":
        return (
            "default_off_repaired_proxy_scorer_comparator",
            {
                "score_context_index_min": 0.05,
                "net_proxy_r_min": 0.0,
                "decision": "register_default_off_scorer_when_context_and_proxy_positive",
            },
            ["source_exhaustion_gate_attached", "exact_proxy_repair_rerun_not_required", "branch_local_only"],
        )
    return (
        "avoid_redesign_repaired_proxy_comparator",
        {
            "score_context_index_max": -0.05,
            "net_proxy_r_max": 0.0,
            "decision": "register_avoid_redesign_when_context_or_proxy_negative",
        },
        ["source_exhaustion_gate_attached", "exact_proxy_repair_rerun_not_required", "branch_local_only"],
    )


def registration_spec_rows(registration_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in registration_rows:
        spec_family, parameters, guards = spec_parameters(row)
        output.append(
            boundary_row(
                {
                    "registration_spec_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-REGISTRATION-SPEC-{len(output) + 1:05d}"
                    ),
                    "input_comparator_registration_row_id": row.get("comparator_registration_row_id"),
                    "input_comparator_execution_row_id": row.get("input_comparator_execution_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registration_family": row.get("registration_family"),
                    "registration_spec_family": spec_family,
                    "bridge_rows": int(row.get("bridge_rows") or 0),
                    "net_proxy_r_mean": as_float(row.get("net_proxy_r_mean")),
                    "score_context_index_mean": as_float(row.get("score_context_index_mean")),
                    "source_exhaustion_gate_status": row.get("source_exhaustion_gate_status"),
                    "registration_parameters": parameters,
                    "required_guards": guards,
                    "registration_spec_status": "BRANCH_LOCAL_REGISTRATION_SPEC_MATERIALIZED",
                }
            )
        )
    return output


def runtime_guard_rows(spec_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for spec in spec_rows:
        output.append(
            boundary_row(
                {
                    "runtime_guard_row_id": f"OHLC-GTOS-REPAIRED-PROXY-REGISTRATION-GUARD-{len(output) + 1:05d}",
                    "input_registration_spec_row_id": spec.get("registration_spec_row_id"),
                    "registration_spec_family": spec.get("registration_spec_family"),
                    "symbol": spec.get("symbol"),
                    "route_session": spec.get("route_session"),
                    "horizon_id": spec.get("horizon_id"),
                    "guard_conditions": {
                        "production_import_path": False,
                        "order_risk_prompt_safety_mt5_mutation": False,
                        "source_exhaustion_gate_status": spec.get("source_exhaustion_gate_status"),
                        "exact_proxy_repair_rerun_required": False,
                    },
                    "runtime_guard_status": "BRANCH_LOCAL_REGISTRATION_GUARD_MATERIALIZED",
                }
            )
        )
    return output


def symbol_registration_summary_rows(spec_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in spec_rows:
        grouped[
            (
                normalized(row.get("symbol")),
                normalized(row.get("route_session")),
                normalized(row.get("registration_spec_family")),
            )
        ].append(row)
    output: list[dict[str, Any]] = []
    for (symbol, route_session, family), rows in sorted(grouped.items()):
        net_values = [as_float(row.get("net_proxy_r_mean")) for row in rows]
        score_values = [as_float(row.get("score_context_index_mean")) for row in rows]
        net_clean = [value for value in net_values if value is not None]
        score_clean = [value for value in score_values if value is not None]
        output.append(
            boundary_row(
                {
                    "symbol_registration_summary_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-REGISTRATION-SYMBOL-{len(output) + 1:04d}"
                    ),
                    "symbol": symbol,
                    "route_session": route_session,
                    "registration_spec_family": family,
                    "registration_spec_rows": len(rows),
                    "bridge_rows": sum(int(row.get("bridge_rows") or 0) for row in rows),
                    "net_proxy_r_mean": mean(net_clean) if net_clean else None,
                    "score_context_index_mean": mean(score_clean) if score_clean else None,
                    "symbol_registration_summary_status": "SYMBOL_REGISTRATION_SPECS_SUMMARIZED",
                }
            )
        )
    return output


def nonregistration_context_rows(nonregistration_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in nonregistration_rows:
        output.append(
            boundary_row(
                {
                    "nonregistration_context_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-REGISTRATION-NONREG-{len(output) + 1:05d}"
                    ),
                    "input_comparator_nonregistration_row_id": row.get("comparator_nonregistration_row_id"),
                    "input_comparator_execution_row_id": row.get("input_comparator_execution_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "comparator_execution_action": row.get("comparator_execution_action"),
                    "bridge_rows": int(row.get("bridge_rows") or 0),
                    "net_proxy_r_mean": as_float(row.get("net_proxy_r_mean")),
                    "score_context_index_mean": as_float(row.get("score_context_index_mean")),
                    "nonregistration_context_status": "NONREGISTRATION_CONTEXT_PRESERVED_FOR_BRANCH_LOCAL_REVIEW",
                }
            )
        )
    return output


def registration_bucket_rows(
    spec_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    nonregistration_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs = [
        ("registration_spec_family", spec_rows, "registration_spec_family"),
        ("registration_spec_status", spec_rows, "registration_spec_status"),
        ("runtime_guard_status", guard_rows, "runtime_guard_status"),
        ("symbol_registration_summary_status", summary_rows, "symbol_registration_summary_status"),
        ("nonregistration_context_status", nonregistration_rows, "nonregistration_context_status"),
    ]
    output: list[dict[str, Any]] = []
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "registration_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-REGISTRATION-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
