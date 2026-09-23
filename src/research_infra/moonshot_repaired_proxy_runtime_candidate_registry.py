"""Register and probe repaired-proxy runtime candidates on branch-local data."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any


RUNTIME_CANDIDATE_REGISTRY_SURFACE = "src/research_infra/moonshot_repaired_proxy_runtime_candidate_registry.py"
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
    output["runtime_candidate_registry_surface"] = RUNTIME_CANDIDATE_REGISTRY_SURFACE
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


def guard_by_candidate(guard_rows: list[dict[str, Any]]) -> dict[Any, dict[str, Any]]:
    return {row.get("input_runtime_candidate_row_id"): row for row in guard_rows}


def scope_key(row: dict[str, Any]) -> str:
    parts = [
        normalized(row.get("symbol")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("source_component")),
    ]
    return "|".join(parts)


def registry_module_rows(
    candidate_rows: list[dict[str, Any]], guard_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    guards = guard_by_candidate(guard_rows)
    output: list[dict[str, Any]] = []
    for candidate in candidate_rows:
        guard = guards.get(candidate.get("runtime_candidate_row_id"), {})
        passed = guard.get("guard_check_passed") is True
        output.append(
            boundary_row(
                {
                    "registry_module_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REGISTRY-{len(output) + 1:05d}"
                    ),
                    "input_runtime_candidate_row_id": candidate.get("runtime_candidate_row_id"),
                    "input_registration_spec_row_id": candidate.get("input_registration_spec_row_id"),
                    "input_guard_check_row_id": guard.get("guard_check_row_id"),
                    "symbol": candidate.get("symbol"),
                    "route_session": candidate.get("route_session"),
                    "horizon_id": candidate.get("horizon_id"),
                    "source_component": candidate.get("source_component"),
                    "runtime_candidate_family": candidate.get("runtime_candidate_family"),
                    "runtime_candidate_kind": candidate.get("runtime_candidate_kind"),
                    "module_path": "src.research_infra.moonshot_repaired_proxy_runtime_candidate_registry",
                    "callable_name": "evaluate_runtime_candidate_event",
                    "module_scope_key": scope_key(candidate),
                    "branch_local_parameters": candidate.get("branch_local_parameters") or {},
                    "bridge_rows": int(candidate.get("bridge_rows") or 0),
                    "net_proxy_r_mean": as_float(candidate.get("net_proxy_r_mean")),
                    "score_context_index_mean": as_float(candidate.get("score_context_index_mean")),
                    "guard_check_status": guard.get("guard_check_status"),
                    "production_import_path": False,
                    "mutates_order_risk_prompt_safety_or_mt5": False,
                    "registry_entry_status": (
                        "RUNTIME_CANDIDATE_REGISTRY_ENTRY_REGISTERED_BRANCH_LOCAL"
                        if passed
                        else "RUNTIME_CANDIDATE_REGISTRY_ENTRY_BLOCKED_BY_GUARD"
                    ),
                }
            )
        )
    return output


def scope_matches(registry_row: dict[str, Any], event_row: dict[str, Any]) -> bool:
    for field in ("symbol", "route_session", "horizon_id", "source_component"):
        expected = normalized(registry_row.get(field))
        if expected and expected != normalized(event_row.get(field)):
            return False
    return True


def evaluate_runtime_candidate_event(registry_row: dict[str, Any], event_row: dict[str, Any]) -> dict[str, Any]:
    if registry_row.get("registry_entry_status") != "RUNTIME_CANDIDATE_REGISTRY_ENTRY_REGISTERED_BRANCH_LOCAL":
        return boundary_row(
            {
                "scope_match": False,
                "candidate_event_score": None,
                "candidate_event_outcome": "RUNTIME_CANDIDATE_EVENT_BLOCKED_BY_REGISTRY_GUARD",
            }
        )
    if not scope_matches(registry_row, event_row):
        return boundary_row(
            {
                "scope_match": False,
                "candidate_event_score": None,
                "candidate_event_outcome": "RUNTIME_CANDIDATE_EVENT_SCOPE_MISMATCH",
            }
        )
    parameters = registry_row.get("branch_local_parameters") or {}
    score_context = as_float(event_row.get("score_context_index"))
    net_proxy = as_float(event_row.get("net_proxy_r"))
    if score_context is None:
        score_context = as_float(registry_row.get("score_context_index_mean"))
    if net_proxy is None:
        net_proxy = as_float(registry_row.get("net_proxy_r_mean"))
    if score_context is None or net_proxy is None:
        return boundary_row(
            {
                "scope_match": True,
                "candidate_event_score": None,
                "candidate_event_outcome": "RUNTIME_CANDIDATE_EVENT_MISSING_PROXY_INPUT",
            }
        )
    if registry_row.get("runtime_candidate_kind") == "DEFAULT_OFF_SCORER":
        score_min = as_float(parameters.get("score_context_index_min"))
        proxy_min = as_float(parameters.get("net_proxy_r_min"))
        accepted = score_context >= (score_min if score_min is not None else 0.0) and net_proxy >= (
            proxy_min if proxy_min is not None else 0.0
        )
        return boundary_row(
            {
                "scope_match": True,
                "candidate_event_score": score_context + net_proxy,
                "candidate_event_outcome": (
                    "DEFAULT_OFF_SCORER_EVENT_ACCEPTED_BRANCH_LOCAL"
                    if accepted
                    else "DEFAULT_OFF_SCORER_EVENT_BELOW_THRESHOLD_BRANCH_LOCAL"
                ),
            }
        )
    score_max = as_float(parameters.get("score_context_index_max"))
    proxy_max = as_float(parameters.get("net_proxy_r_max"))
    triggered = score_context <= (score_max if score_max is not None else 0.0) or net_proxy <= (
        proxy_max if proxy_max is not None else 0.0
    )
    return boundary_row(
        {
            "scope_match": True,
            "candidate_event_score": min(score_context, net_proxy),
            "candidate_event_outcome": (
                "AVOID_REDESIGN_COMPARATOR_EVENT_TRIGGERED_BRANCH_LOCAL"
                if triggered
                else "AVOID_REDESIGN_COMPARATOR_EVENT_NOT_TRIGGERED_BRANCH_LOCAL"
            ),
        }
    )


def registry_event_probe_rows(registry_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in registry_rows:
        event = {
            "symbol": row.get("symbol"),
            "route_session": row.get("route_session"),
            "horizon_id": row.get("horizon_id"),
            "source_component": row.get("source_component"),
            "score_context_index": row.get("score_context_index_mean"),
            "net_proxy_r": row.get("net_proxy_r_mean"),
        }
        result = evaluate_runtime_candidate_event(row, event)
        output.append(
            boundary_row(
                {
                    "registry_event_probe_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-PROBE-{len(output) + 1:05d}"
                    ),
                    "input_registry_module_row_id": row.get("registry_module_row_id"),
                    "input_runtime_candidate_row_id": row.get("input_runtime_candidate_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "runtime_candidate_family": row.get("runtime_candidate_family"),
                    "runtime_candidate_kind": row.get("runtime_candidate_kind"),
                    "probe_scope_match": result.get("scope_match"),
                    "probe_event_score": result.get("candidate_event_score"),
                    "probe_event_outcome": result.get("candidate_event_outcome"),
                    "registry_event_probe_status": "RUNTIME_CANDIDATE_REGISTRY_PROBE_EXECUTED_BRANCH_LOCAL",
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


def symbol_registry_rollup_rows(
    registry_rows: list[dict[str, Any]], probe_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    probes_by_registry = {row.get("input_registry_module_row_id"): row for row in probe_rows}
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in registry_rows:
        grouped[
            (
                normalized(row.get("symbol")),
                normalized(row.get("route_session")),
                normalized(row.get("horizon_id")),
                normalized(row.get("runtime_candidate_family")),
            )
        ].append(row)
    output: list[dict[str, Any]] = []
    for (symbol, route_session, horizon_id, family), rows in sorted(grouped.items()):
        outcomes = Counter(
            normalized(probes_by_registry.get(row.get("registry_module_row_id"), {}).get("probe_event_outcome"))
            for row in rows
        )
        output.append(
            boundary_row(
                {
                    "symbol_registry_rollup_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REGISTRY-SYMBOL-{len(output) + 1:05d}"
                    ),
                    "symbol": symbol,
                    "route_session": route_session,
                    "horizon_id": horizon_id,
                    "runtime_candidate_family": family,
                    "registry_module_rows": len(rows),
                    "bridge_rows": sum(int(row.get("bridge_rows") or 0) for row in rows),
                    "net_proxy_r_weighted_mean": weighted_mean(rows, "net_proxy_r_mean"),
                    "score_context_index_weighted_mean": weighted_mean(rows, "score_context_index_mean"),
                    "probe_event_outcome_counts": dict(sorted(outcomes.items())),
                    "symbol_registry_rollup_status": "SYMBOL_RUNTIME_CANDIDATE_REGISTRY_ROLLED_UP_BRANCH_LOCAL",
                }
            )
        )
    return output


def nonregistration_registry_review_rows(review_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in review_rows:
        output.append(
            boundary_row(
                {
                    "nonregistration_registry_review_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REGISTRY-NONREG-{len(output) + 1:05d}"
                    ),
                    "input_nonregistration_review_row_id": row.get("nonregistration_review_row_id"),
                    "input_comparator_execution_row_id": row.get("input_comparator_execution_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "review_action": row.get("review_action"),
                    "bridge_rows": int(row.get("bridge_rows") or 0),
                    "nonregistration_registry_review_status": (
                        "NONREGISTRATION_CONTEXT_KEPT_OUT_OF_RUNTIME_REGISTRY_BRANCH_LOCAL"
                    ),
                }
            )
        )
    return output


def registry_bucket_rows(
    registry_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    rollup_rows: list[dict[str, Any]],
    nonregistration_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs = [
        ("runtime_candidate_family", registry_rows, "runtime_candidate_family"),
        ("registry_entry_status", registry_rows, "registry_entry_status"),
        ("probe_event_outcome", probe_rows, "probe_event_outcome"),
        ("registry_event_probe_status", probe_rows, "registry_event_probe_status"),
        ("symbol_registry_rollup_status", rollup_rows, "symbol_registry_rollup_status"),
        ("nonregistration_registry_review_status", nonregistration_rows, "nonregistration_registry_review_status"),
    ]
    output: list[dict[str, Any]] = []
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "registry_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REGISTRY-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
