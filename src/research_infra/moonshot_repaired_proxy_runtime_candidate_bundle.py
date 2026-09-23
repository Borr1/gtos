"""Build branch-local runtime-candidate bundles from repaired-proxy registration specs."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any


RUNTIME_CANDIDATE_BUNDLE_SURFACE = "src/research_infra/moonshot_repaired_proxy_runtime_candidate_bundle.py"
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
    output["runtime_candidate_bundle_surface"] = RUNTIME_CANDIDATE_BUNDLE_SURFACE
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


def runtime_candidate_family(spec_family: str) -> tuple[str, str]:
    if spec_family == "default_off_repaired_proxy_scorer_comparator":
        return "branch_local_default_off_repaired_proxy_scorer_candidate", "DEFAULT_OFF_SCORER"
    return "branch_local_avoid_redesign_repaired_proxy_comparator_candidate", "AVOID_REDESIGN_COMPARATOR"


def runtime_candidate_rows(spec_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for spec in spec_rows:
        candidate_family, candidate_kind = runtime_candidate_family(normalized(spec.get("registration_spec_family")))
        output.append(
            boundary_row(
                {
                    "runtime_candidate_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-CANDIDATE-{len(output) + 1:05d}"
                    ),
                    "input_registration_spec_row_id": spec.get("registration_spec_row_id"),
                    "input_comparator_registration_row_id": spec.get("input_comparator_registration_row_id"),
                    "input_comparator_execution_row_id": spec.get("input_comparator_execution_row_id"),
                    "symbol": spec.get("symbol"),
                    "route_session": spec.get("route_session"),
                    "horizon_id": spec.get("horizon_id"),
                    "source_component": spec.get("source_component"),
                    "registration_family": spec.get("registration_family"),
                    "registration_spec_family": spec.get("registration_spec_family"),
                    "runtime_candidate_family": candidate_family,
                    "runtime_candidate_kind": candidate_kind,
                    "branch_local_parameters": spec.get("registration_parameters") or {},
                    "required_guards": list(spec.get("required_guards") or []),
                    "source_exhaustion_gate_status": spec.get("source_exhaustion_gate_status"),
                    "bridge_rows": int(spec.get("bridge_rows") or 0),
                    "net_proxy_r_mean": as_float(spec.get("net_proxy_r_mean")),
                    "score_context_index_mean": as_float(spec.get("score_context_index_mean")),
                    "production_import_path": False,
                    "mutates_order_risk_prompt_safety_or_mt5": False,
                    "candidate_status": "RUNTIME_CANDIDATE_MATERIALIZED_BRANCH_LOCAL",
                }
            )
        )
    return output


def guard_check_rows(
    candidate_rows: list[dict[str, Any]], guard_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    guards_by_spec = {row.get("input_registration_spec_row_id"): row for row in guard_rows}
    output: list[dict[str, Any]] = []
    for candidate in candidate_rows:
        guard = guards_by_spec.get(candidate.get("input_registration_spec_row_id"), {})
        guard_conditions = guard.get("guard_conditions") or {}
        checks = {
            "candidate_production_import_path_false": candidate.get("production_import_path") is False,
            "candidate_no_order_risk_prompt_safety_mt5_mutation": (
                candidate.get("mutates_order_risk_prompt_safety_or_mt5") is False
            ),
            "registration_guard_production_import_path_false": guard_conditions.get("production_import_path") is False,
            "registration_guard_no_order_risk_prompt_safety_mt5_mutation": (
                guard_conditions.get("order_risk_prompt_safety_mt5_mutation") is False
            ),
            "registration_guard_no_exact_proxy_repair_rerun_required": (
                guard_conditions.get("exact_proxy_repair_rerun_required") is False
            ),
            "source_exhaustion_gate_attached": bool(
                normalized(guard_conditions.get("source_exhaustion_gate_status"))
            ),
        }
        passed = all(checks.values())
        output.append(
            boundary_row(
                {
                    "guard_check_row_id": f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-GUARD-{len(output) + 1:05d}",
                    "input_runtime_candidate_row_id": candidate.get("runtime_candidate_row_id"),
                    "input_registration_spec_row_id": candidate.get("input_registration_spec_row_id"),
                    "input_runtime_guard_row_id": guard.get("runtime_guard_row_id"),
                    "symbol": candidate.get("symbol"),
                    "route_session": candidate.get("route_session"),
                    "horizon_id": candidate.get("horizon_id"),
                    "runtime_candidate_family": candidate.get("runtime_candidate_family"),
                    "guard_checks": checks,
                    "guard_check_passed": passed,
                    "guard_check_status": (
                        "RUNTIME_CANDIDATE_GUARD_CHECK_PASSED_BRANCH_LOCAL"
                        if passed
                        else "RUNTIME_CANDIDATE_GUARD_CHECK_BLOCKED_BRANCH_LOCAL"
                    ),
                }
            )
        )
    return output


def weighted_mean(rows: list[dict[str, Any]], field: str) -> float | None:
    pairs: list[tuple[float, int]] = []
    for row in rows:
        value = as_float(row.get(field))
        weight = int(row.get("bridge_rows") or 0)
        if value is not None and weight > 0:
            pairs.append((value, weight))
    total_weight = sum(weight for _, weight in pairs)
    if total_weight > 0:
        return sum(value * weight for value, weight in pairs) / total_weight
    values = [as_float(row.get(field)) for row in rows]
    clean = [value for value in values if value is not None]
    return mean(clean) if clean else None


def symbol_candidate_bundle_rows(
    candidate_rows: list[dict[str, Any]], guard_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    guard_by_candidate = {row.get("input_runtime_candidate_row_id"): row for row in guard_rows}
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidate_rows:
        grouped[
            (
                normalized(candidate.get("symbol")),
                normalized(candidate.get("route_session")),
                normalized(candidate.get("horizon_id")),
                normalized(candidate.get("runtime_candidate_family")),
            )
        ].append(candidate)

    output: list[dict[str, Any]] = []
    for (symbol, route_session, horizon_id, candidate_family), rows in sorted(grouped.items()):
        passed = sum(
            1
            for row in rows
            if guard_by_candidate.get(row.get("runtime_candidate_row_id"), {}).get("guard_check_passed") is True
        )
        output.append(
            boundary_row(
                {
                    "symbol_candidate_bundle_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SYMBOL-BUNDLE-{len(output) + 1:05d}"
                    ),
                    "symbol": symbol,
                    "route_session": route_session,
                    "horizon_id": horizon_id,
                    "runtime_candidate_family": candidate_family,
                    "candidate_rows": len(rows),
                    "guard_checks_passed": passed,
                    "guard_checks_blocked": len(rows) - passed,
                    "bridge_rows": sum(int(row.get("bridge_rows") or 0) for row in rows),
                    "net_proxy_r_weighted_mean": weighted_mean(rows, "net_proxy_r_mean"),
                    "score_context_index_weighted_mean": weighted_mean(rows, "score_context_index_mean"),
                    "source_components": sorted({normalized(row.get("source_component")) for row in rows}),
                    "symbol_candidate_bundle_status": (
                        "SYMBOL_RUNTIME_CANDIDATE_BUNDLE_MATERIALIZED_BRANCH_LOCAL"
                        if passed == len(rows)
                        else "SYMBOL_RUNTIME_CANDIDATE_BUNDLE_HAS_BLOCKED_GUARDS"
                    ),
                }
            )
        )
    return output


def nonregistration_review_rows(nonregistration_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in nonregistration_rows:
        action = normalized(row.get("comparator_execution_action"))
        if action == "HOLD_DEFAULT_OFF_SCORER_CONTEXT":
            review_action = "RETAIN_CONTEXT_FOR_BRANCH_LOCAL_THRESHOLD_REVIEW"
        elif action == "DO_NOT_REGISTER_AVOID_COMPARATOR":
            review_action = "KEEP_AVOID_COMPARATOR_OUT_OF_RUNTIME_CANDIDATE_BUNDLE"
        else:
            review_action = "KEEP_DEFAULT_OFF_SCORER_OUT_OF_RUNTIME_CANDIDATE_BUNDLE"
        output.append(
            boundary_row(
                {
                    "nonregistration_review_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-NONREG-REVIEW-{len(output) + 1:05d}"
                    ),
                    "input_nonregistration_context_row_id": row.get("nonregistration_context_row_id"),
                    "input_comparator_nonregistration_row_id": row.get("input_comparator_nonregistration_row_id"),
                    "input_comparator_execution_row_id": row.get("input_comparator_execution_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "comparator_execution_action": row.get("comparator_execution_action"),
                    "bridge_rows": int(row.get("bridge_rows") or 0),
                    "net_proxy_r_mean": as_float(row.get("net_proxy_r_mean")),
                    "score_context_index_mean": as_float(row.get("score_context_index_mean")),
                    "review_action": review_action,
                    "nonregistration_review_status": "NONREGISTRATION_CONTEXT_REVIEW_MATERIALIZED_BRANCH_LOCAL",
                }
            )
        )
    return output


def runtime_candidate_bucket_rows(
    candidate_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    bundle_rows: list[dict[str, Any]],
    nonregistration_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs = [
        ("runtime_candidate_family", candidate_rows, "runtime_candidate_family"),
        ("candidate_status", candidate_rows, "candidate_status"),
        ("guard_check_status", guard_rows, "guard_check_status"),
        ("symbol_candidate_bundle_status", bundle_rows, "symbol_candidate_bundle_status"),
        ("nonregistration_review_action", nonregistration_rows, "review_action"),
        ("nonregistration_review_status", nonregistration_rows, "nonregistration_review_status"),
    ]
    output: list[dict[str, Any]] = []
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "runtime_candidate_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
