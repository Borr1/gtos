"""Run branch-local lookups for repaired-proxy repair acquisition requirements."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable


REPAIR_ACQUISITION_LOOKUP_SURFACE = "src/research_infra/moonshot_repaired_proxy_repair_acquisition_lookup.py"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "direct_trade_candidate_identifier": (
        "candidate_id",
        "trade_candidate_id",
        "candidate_row_id",
        "decision_id",
        "strategy_id",
        "row_id",
    ),
    "ticket_identifier": (
        "order_ticket",
        "deal_ticket",
        "position_ticket",
        "ticket",
        "order",
        "deal",
        "order_id",
        "deal_id",
        "position_id",
    ),
    "candidate_lock_metadata": (
        "candidate_lock_id",
        "candidate_lock",
        "lock_id",
        "snapshot_id",
        "mso_snapshot_id",
        "intent_id",
        "pending_intent_id",
        "decision_time_utc",
    ),
    "symbol": ("symbol", "broker_symbol"),
    "route_session": ("route_session", "session", "session_name", "kill_zone"),
    "horizon_id": ("horizon_id", "horizon", "timeframe"),
}

JOIN_KEY_NAMES = {
    "acquisition_requirement_row_id",
    "repair_execution_row_id",
    "input_repair_execution_row_id",
    "repair_work_order_row_id",
    "input_repair_work_order_row_id",
    "exact_proxy_bridge_row_id",
    "input_exact_proxy_bridge_row_id",
    "score_rebuilt_bridge_row_id",
    "input_score_rebuilt_bridge_row_id",
    "repaired_proxy_event_application_row_id",
    "input_repaired_proxy_event_application_row_id",
    "numeric_result_row_id",
    "input_numeric_result_row_id",
    "shadow_scorer_event_score_row_id",
    "input_shadow_scorer_event_score_row_id",
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
    output["repair_acquisition_lookup_surface"] = REPAIR_ACQUISITION_LOOKUP_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def clean_values(values: Iterable[Any]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = normalized(value).strip()
        if not text or text in seen:
            continue
        output.append(text)
        seen.add(text)
    return output


def _walk_values(value: Any, aliases: set[str], out: list[Any], depth: int = 0) -> None:
    if depth > 5:
        return
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower() in aliases:
                out.append(nested)
            _walk_values(nested, aliases, out, depth + 1)
    elif isinstance(value, list):
        for nested in value[:50]:
            _walk_values(nested, aliases, out, depth + 1)


def field_values(row: dict[str, Any], logical_field: str) -> list[str]:
    aliases = {alias.lower() for alias in FIELD_ALIASES.get(logical_field, (logical_field,))}
    values: list[Any] = []
    _walk_values(row, aliases, values)
    return clean_values(values)


def join_values(row: dict[str, Any]) -> list[str]:
    values: list[Any] = []

    def walk(value: Any, depth: int = 0) -> None:
        if depth > 5:
            return
        if isinstance(value, dict):
            for key, nested in value.items():
                key_text = str(key)
                if key_text in JOIN_KEY_NAMES or key_text.endswith("_row_id"):
                    values.append(nested)
                walk(nested, depth + 1)
        elif isinstance(value, list):
            for nested in value[:50]:
                walk(nested, depth + 1)

    walk(row)
    return clean_values(values)


def scope_values(row: dict[str, Any]) -> dict[str, str]:
    return {
        "symbol": (field_values(row, "symbol") or [""])[0],
        "route_session": (field_values(row, "route_session") or [""])[0],
        "horizon_id": (field_values(row, "horizon_id") or [""])[0],
        "source_component": normalized(row.get("source_component")).strip(),
    }


def requirement_scope_match(requirement: dict[str, Any], source_row: dict[str, Any]) -> bool:
    return requirement_scope_match_values(requirement, scope_values(source_row))


def requirement_scope_match_values(requirement: dict[str, Any], source_scope: dict[str, str]) -> bool:
    required_scope = scope_values(requirement)
    return scope_dict_match(required_scope, source_scope)


def scope_dict_match(required_scope: dict[str, str], source_scope: dict[str, str]) -> bool:
    comparable = [key for key in ("symbol", "route_session", "horizon_id") if required_scope.get(key)]
    if not comparable:
        return False
    for key in comparable:
        if required_scope.get(key) != source_scope.get(key):
            return False
    source_component = required_scope.get("source_component")
    if source_component and source_scope.get("source_component") and source_component != source_scope.get("source_component"):
        return False
    return True


def source_names_by_requirement(
    requirement_rows: list[dict[str, Any]], source_candidate_rows: list[dict[str, Any]]
) -> dict[str, list[str]]:
    grouped: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in source_candidate_rows:
        key = (normalized(row.get("acquisition_source_family")), normalized(row.get("missing_required_field")))
        grouped[key].append(normalized(row.get("source_candidate_name")))
    output: dict[str, list[str]] = {}
    for row in requirement_rows:
        key = (normalized(row.get("acquisition_source_family")), normalized(row.get("missing_required_field")))
        output[normalized(row.get("acquisition_requirement_row_id"))] = sorted(name for name in grouped.get(key, []) if name)
    return output


def scan_source_records(
    source_candidate_name: str,
    source_rows: Iterable[dict[str, Any]],
    requirement_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    metrics: dict[str, dict[str, Any]] = {}
    field_present_counts: Counter[str] = Counter()
    rows_scanned = 0
    for requirement in requirement_rows:
        requirement_id = normalized(requirement.get("acquisition_requirement_row_id"))
        metrics[requirement_id] = {
            "exact_join_rows": 0,
            "exact_field_value_rows": 0,
            "scope_join_rows": 0,
            "scope_field_value_rows": 0,
            "acquired_values": set(),
        }

    requirement_join_sets = {
        normalized(row.get("acquisition_requirement_row_id")): set(join_values(row)) for row in requirement_rows
    }
    requirement_scopes = {
        normalized(row.get("acquisition_requirement_row_id")): scope_values(row) for row in requirement_rows
    }

    for source_row in source_rows:
        rows_scanned += 1
        source_join_set = set(join_values(source_row))
        per_field_values: dict[str, list[str]] = {}
        for field in FIELD_ALIASES:
            values = field_values(source_row, field)
            per_field_values[field] = values
            if values:
                field_present_counts[field] += 1
        source_scope = scope_values(source_row)
        if not source_join_set and not any(per_field_values.values()) and not any(source_scope.values()):
            continue

        for requirement in requirement_rows:
            requirement_id = normalized(requirement.get("acquisition_requirement_row_id"))
            field = normalized(requirement.get("missing_required_field"))
            values = per_field_values.get(field, [])
            exact_match = bool(source_join_set and requirement_join_sets.get(requirement_id, set()) & source_join_set)
            scope_match = scope_dict_match(requirement_scopes.get(requirement_id, {}), source_scope)
            row_metrics = metrics[requirement_id]
            if exact_match:
                row_metrics["exact_join_rows"] += 1
                if values:
                    row_metrics["exact_field_value_rows"] += 1
                    row_metrics["acquired_values"].update(values)
            if scope_match:
                row_metrics["scope_join_rows"] += 1
                if values:
                    row_metrics["scope_field_value_rows"] += 1

    return {
        "source_candidate_name": source_candidate_name,
        "source_rows_scanned": rows_scanned,
        "field_present_counts": dict(sorted(field_present_counts.items())),
        "requirement_metrics": {
            requirement_id: {
                **{key: value for key, value in metric.items() if key != "acquired_values"},
                "acquired_values": sorted(metric["acquired_values"]),
            }
            for requirement_id, metric in sorted(metrics.items())
        },
    }


def lookup_status(metric: dict[str, Any], field_present_rows: int) -> str:
    values = metric.get("acquired_values") or []
    if metric.get("exact_field_value_rows", 0) > 0 and len(values) == 1:
        return "FIELD_ACQUIRED_FROM_EXACT_SOURCE_JOIN"
    if metric.get("exact_field_value_rows", 0) > 0 and len(values) > 1:
        return "FIELD_EXACT_JOIN_MULTIPLE_VALUES_NEEDS_DISAMBIGUATION"
    if metric.get("exact_join_rows", 0) > 0:
        return "EXACT_SOURCE_JOIN_FOUND_FIELD_ABSENT"
    if metric.get("scope_field_value_rows", 0) > 0:
        return "FIELD_OBSERVED_IN_SCOPE_MATCH_WITHOUT_ROW_KEY"
    if field_present_rows > 0:
        return "FIELD_PRESENT_IN_SOURCE_WITHOUT_REQUIREMENT_JOIN"
    return "FIELD_NOT_FOUND_IN_SOURCE_LOOKUP"


def lookup_execution_rows(
    requirement_rows: list[dict[str, Any]],
    source_candidate_rows: list[dict[str, Any]],
    source_scan_results: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    source_names = source_names_by_requirement(requirement_rows, source_candidate_rows)
    output: list[dict[str, Any]] = []
    for requirement in requirement_rows:
        requirement_id = normalized(requirement.get("acquisition_requirement_row_id"))
        field = normalized(requirement.get("missing_required_field"))
        for source_name in source_names.get(requirement_id, []):
            scan = source_scan_results.get(source_name, {})
            metric = (scan.get("requirement_metrics") or {}).get(requirement_id, {})
            field_present_rows = int((scan.get("field_present_counts") or {}).get(field, 0))
            values = metric.get("acquired_values") or []
            status = lookup_status(metric, field_present_rows)
            output.append(
                boundary_row(
                    {
                        "lookup_execution_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-LOOKUP-EXEC-{len(output) + 1:05d}"
                        ),
                        "input_acquisition_requirement_row_id": requirement_id,
                        "input_repair_execution_row_id": requirement.get("input_repair_execution_row_id"),
                        "input_repair_work_order_row_id": requirement.get("input_repair_work_order_row_id"),
                        "input_exact_proxy_bridge_row_id": requirement.get("input_exact_proxy_bridge_row_id"),
                        "missing_required_field": field,
                        "acquisition_source_family": requirement.get("acquisition_source_family"),
                        "source_candidate_name": source_name,
                        "source_rows_scanned": int(scan.get("source_rows_scanned", 0)),
                        "source_field_present_rows": field_present_rows,
                        "exact_join_rows": int(metric.get("exact_join_rows", 0)),
                        "exact_field_value_rows": int(metric.get("exact_field_value_rows", 0)),
                        "scope_join_rows": int(metric.get("scope_join_rows", 0)),
                        "scope_field_value_rows": int(metric.get("scope_field_value_rows", 0)),
                        "acquired_value": values[0] if status == "FIELD_ACQUIRED_FROM_EXACT_SOURCE_JOIN" else None,
                        "lookup_execution_status": status,
                    }
                )
            )
    return output


def source_candidate_lookup_rows(
    source_candidate_rows_in: list[dict[str, Any]],
    source_scan_results: dict[str, dict[str, Any]],
    source_path_counts: dict[str, int],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(source_candidate_rows_in, 1):
        source_name = normalized(row.get("source_candidate_name"))
        scan = source_scan_results.get(source_name, {})
        path_count = int(source_path_counts.get(source_name, 0))
        rows_scanned = int(scan.get("source_rows_scanned", 0))
        if path_count == 0:
            status = "SOURCE_CANDIDATE_LOOKUP_NO_LOCAL_FILES"
        elif rows_scanned == 0:
            status = "SOURCE_CANDIDATE_LOOKUP_NO_ROWS"
        else:
            status = "SOURCE_CANDIDATE_LOOKUP_STREAMED"
        output.append(
            boundary_row(
                {
                    "source_candidate_lookup_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-LOOKUP-SOURCE-{index:04d}"
                    ),
                    "input_source_candidate_row_id": row.get("source_candidate_row_id"),
                    "source_candidate_name": source_name,
                    "missing_required_field": row.get("missing_required_field"),
                    "acquisition_source_family": row.get("acquisition_source_family"),
                    "local_source_path_count": path_count,
                    "source_rows_scanned": rows_scanned,
                    "field_present_counts": scan.get("field_present_counts") or {},
                    "source_candidate_lookup_status": status,
                }
            )
        )
    return output


def field_fulfillment_rows(
    requirement_rows: list[dict[str, Any]], lookup_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in lookup_rows:
        grouped[normalized(row.get("input_acquisition_requirement_row_id"))].append(row)
    output: list[dict[str, Any]] = []
    for requirement in requirement_rows:
        requirement_id = normalized(requirement.get("acquisition_requirement_row_id"))
        rows = grouped.get(requirement_id, [])
        acquired = [row.get("acquired_value") for row in rows if row.get("acquired_value")]
        statuses = {normalized(row.get("lookup_execution_status")) for row in rows}
        if len(set(acquired)) == 1:
            status = "FIELD_FULFILLED_BY_BRANCH_LOCAL_LOOKUP"
            value = acquired[0]
        elif "EXACT_SOURCE_JOIN_FOUND_FIELD_ABSENT" in statuses:
            status = "FIELD_NOT_FULFILLED_EXACT_JOIN_FIELD_ABSENT"
            value = None
        elif "FIELD_OBSERVED_IN_SCOPE_MATCH_WITHOUT_ROW_KEY" in statuses:
            status = "FIELD_NOT_FULFILLED_SCOPE_MATCH_NOT_ROW_UNIQUE"
            value = None
        elif "FIELD_PRESENT_IN_SOURCE_WITHOUT_REQUIREMENT_JOIN" in statuses:
            status = "FIELD_NOT_FULFILLED_FIELD_PRESENT_WITHOUT_JOIN"
            value = None
        else:
            status = "FIELD_NOT_FULFILLED_NOT_FOUND"
            value = None
        output.append(
            boundary_row(
                {
                    "field_fulfillment_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-LOOKUP-FIELD-{len(output) + 1:05d}"
                    ),
                    "input_acquisition_requirement_row_id": requirement_id,
                    "input_repair_execution_row_id": requirement.get("input_repair_execution_row_id"),
                    "missing_required_field": requirement.get("missing_required_field"),
                    "acquisition_source_family": requirement.get("acquisition_source_family"),
                    "lookup_source_attempts": len(rows),
                    "fulfilled_value": value,
                    "field_fulfillment_status": status,
                }
            )
        )
    return output


def repair_rerun_readiness_rows(field_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in field_rows:
        grouped[normalized(row.get("input_repair_execution_row_id"))].append(row)
    output: list[dict[str, Any]] = []
    for execution_id in sorted(grouped):
        rows = grouped[execution_id]
        fulfilled = [row for row in rows if row.get("field_fulfillment_status") == "FIELD_FULFILLED_BY_BRANCH_LOCAL_LOOKUP"]
        ready = len(fulfilled) == len(rows)
        output.append(
            boundary_row(
                {
                    "repair_rerun_readiness_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-LOOKUP-RERUN-{len(output) + 1:05d}"
                    ),
                    "input_repair_execution_row_id": execution_id,
                    "required_field_rows": len(rows),
                    "fulfilled_field_rows": len(fulfilled),
                    "missing_after_lookup_rows": len(rows) - len(fulfilled),
                    "repair_rerun_ready": ready,
                    "repair_rerun_readiness_status": (
                        "REPAIR_RERUN_READY_AFTER_FIELD_LOOKUP"
                        if ready
                        else "REPAIR_RERUN_NOT_READY_AFTER_FIELD_LOOKUP"
                    ),
                }
            )
        )
    return output


def rerun_gate_rows(readiness_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    eligible = [row for row in readiness_rows if row.get("repair_rerun_ready") is True]
    return [
        boundary_row(
            {
                "repair_lookup_rerun_gate_row_id": "OHLC-GTOS-REPAIRED-PROXY-REPAIR-LOOKUP-GATE-0001",
                "repair_execution_rows_checked": len(readiness_rows),
                "repair_rerun_ready_rows": len(eligible),
                "repair_rerun_gate_status": (
                    "EXACT_PROXY_RERUN_GATE_OPEN_FIELD_LOOKUP_REPAIRED_ROWS_PRESENT"
                    if eligible
                    else "EXACT_PROXY_RERUN_GATE_HELD_NO_FIELD_LOOKUP_REPAIRED_ROWS"
                ),
            }
        )
    ]


def lookup_bucket_rows(
    lookup_rows: list[dict[str, Any]],
    field_rows: list[dict[str, Any]],
    readiness_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs = [
        ("lookup_execution_status", lookup_rows, "lookup_execution_status"),
        ("field_fulfillment_status", field_rows, "field_fulfillment_status"),
        ("repair_rerun_readiness_status", readiness_rows, "repair_rerun_readiness_status"),
        ("source_candidate_lookup_status", source_rows, "source_candidate_lookup_status"),
    ]
    output: list[dict[str, Any]] = []
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "lookup_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-LOOKUP-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
