"""Execute materialized runtime replay specs against replay-score rows."""

from __future__ import annotations

from collections import Counter
from typing import Any


RUNTIME_REPLAY_SPEC_EXECUTION_SURFACE = (
    "src/research_infra/moonshot_repaired_proxy_runtime_replay_spec_execution.py"
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
    output["runtime_replay_spec_execution_surface"] = RUNTIME_REPLAY_SPEC_EXECUTION_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def scope_key(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        normalized(row.get("symbol")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("source_component")),
        normalized(row.get("registry_family")),
    )


def rerun_index(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str, str, str], dict[str, Any]]:
    return {scope_key(row): row for row in rows}


def scorer_execution_class(score: float | None) -> tuple[str, str]:
    if score is None:
        return ("SCORER_SPEC_EXECUTION_SCORE_MISSING", "CARRY_SCORER_SPEC_FOR_SCORE_REPAIR")
    if score >= 0.10:
        return ("SCORER_SPEC_EXECUTION_POSITIVE_REPLAY_SCORE", "KEEP_SCORER_SPEC_FOR_BRANCH_LOCAL_BATCH")
    if score >= 0.0:
        return ("SCORER_SPEC_EXECUTION_WEAK_POSITIVE_REPLAY_SCORE", "KEEP_SCORER_SPEC_WITH_CONTEXT")
    return ("SCORER_SPEC_EXECUTION_NEGATIVE_REPLAY_SCORE", "RECHECK_SCORER_SPEC_BEFORE_NEXT_BATCH")


def comparator_execution_class(score: float | None) -> tuple[str, str]:
    if score is None:
        return ("COMPARATOR_SPEC_EXECUTION_SCORE_MISSING", "CARRY_COMPARATOR_SPEC_FOR_SCORE_REPAIR")
    if score <= -0.10:
        return ("COMPARATOR_SPEC_EXECUTION_STRONG_AVOID_SCORE", "KEEP_COMPARATOR_SPEC_FOR_BRANCH_LOCAL_BATCH")
    if score < 0.0:
        return ("COMPARATOR_SPEC_EXECUTION_AVOID_SCORE", "KEEP_COMPARATOR_SPEC_WITH_CONTEXT")
    return ("COMPARATOR_SPEC_EXECUTION_WEAK_OR_POSITIVE_SCORE", "RECHECK_COMPARATOR_SPEC_BEFORE_NEXT_BATCH")


def execution_payload(spec: dict[str, Any], match: dict[str, Any] | None) -> dict[str, Any]:
    score = as_float(match.get("replay_rerun_score")) if match else None
    return {
        "symbol": spec.get("symbol"),
        "route_session": spec.get("route_session"),
        "horizon_id": spec.get("horizon_id"),
        "source_component": spec.get("source_component"),
        "registry_family": spec.get("registry_family"),
        "packet_rank": int(spec.get("packet_rank") or 0),
        "packet_rank_score": spec.get("packet_rank_score"),
        "spec_context_mode": spec.get("spec_context_mode"),
        "input_replay_score_rerun_row_id": match.get("replay_score_rerun_row_id") if match else None,
        "input_replay_numeric_event_row_id": match.get("input_replay_numeric_event_row_id") if match else None,
        "market_source_path": match.get("market_source_path") if match else None,
        "market_timeframe": match.get("market_timeframe") if match else None,
        "base_registry_scope_score": match.get("base_registry_scope_score") if match else None,
        "replay_context_modifier": match.get("replay_context_modifier") if match else None,
        "replay_rerun_score": score,
        "replay_score_rerun_action": match.get("replay_score_rerun_action") if match else None,
        "replay_score_rerun_status": match.get("replay_score_rerun_status") if match else None,
        "source_close_return_pct": match.get("source_close_return_pct") if match else None,
        "source_return_minus_control": match.get("source_return_minus_control") if match else None,
        "source_spread_mean": match.get("source_spread_mean") if match else None,
        "spec_execution_join_status": (
            "SPEC_EXECUTION_REPLAY_SCORE_JOINED_EXACT" if match else "SPEC_EXECUTION_REPLAY_SCORE_UNMATCHED"
        ),
    }


def scorer_spec_execution_rows(
    scorer_specs: list[dict[str, Any]], default_off_rerun_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    index = rerun_index(default_off_rerun_rows)
    output: list[dict[str, Any]] = []
    for spec in scorer_specs:
        match = index.get(scope_key(spec))
        score = as_float(match.get("replay_rerun_score")) if match else None
        execution_class, action = scorer_execution_class(score)
        row = execution_payload(spec, match)
        row.update(
            {
                "scorer_spec_execution_row_id": (
                    f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SPEC-EXEC-SCORER-{len(output) + 1:06d}"
                ),
                "input_scorer_spec_row_id": spec.get("scorer_spec_row_id"),
                "scorer_spec_execution_class": execution_class,
                "scorer_spec_execution_action": action,
                "scorer_spec_execution_status": "RUNTIME_REPLAY_SCORER_SPEC_EXECUTED_BRANCH_LOCAL",
            }
        )
        output.append(boundary_row(row))
    return output


def comparator_spec_execution_rows(
    comparator_specs: list[dict[str, Any]], avoid_rerun_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    index = rerun_index(avoid_rerun_rows)
    output: list[dict[str, Any]] = []
    for spec in comparator_specs:
        match = index.get(scope_key(spec))
        score = as_float(match.get("replay_rerun_score")) if match else None
        execution_class, action = comparator_execution_class(score)
        row = execution_payload(spec, match)
        row.update(
            {
                "comparator_spec_execution_row_id": (
                    f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SPEC-EXEC-COMPARATOR-{len(output) + 1:06d}"
                ),
                "input_comparator_spec_row_id": spec.get("comparator_spec_row_id"),
                "comparator_spec_execution_class": execution_class,
                "comparator_spec_execution_action": action,
                "comparator_spec_execution_status": "RUNTIME_REPLAY_COMPARATOR_SPEC_EXECUTED_BRANCH_LOCAL",
            }
        )
        output.append(boundary_row(row))
    return output


def spec_execution_result_rows(
    scorer_rows: list[dict[str, Any]], comparator_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    combined = [
        ("DEFAULT_OFF_REPAIRED_PROXY_SCORER_SPEC", row, row.get("scorer_spec_execution_class"))
        for row in scorer_rows
    ] + [
        ("AVOID_REDESIGN_REPAIRED_PROXY_COMPARATOR_SPEC", row, row.get("comparator_spec_execution_class"))
        for row in comparator_rows
    ]
    output: list[dict[str, Any]] = []
    for spec_kind, row, execution_class in combined:
        output.append(
            boundary_row(
                {
                    "spec_execution_result_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SPEC-EXEC-RESULT-{len(output) + 1:06d}"
                    ),
                    "branch_local_spec_kind": spec_kind,
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "packet_rank": row.get("packet_rank"),
                    "spec_context_mode": row.get("spec_context_mode"),
                    "replay_rerun_score": row.get("replay_rerun_score"),
                    "spec_execution_join_status": row.get("spec_execution_join_status"),
                    "spec_execution_class": execution_class,
                    "spec_execution_result_status": "RUNTIME_REPLAY_SPEC_EXECUTION_RESULT_MATERIALIZED",
                }
            )
        )
    return output


def spec_execution_scope_rollup_rows(result_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for row in result_rows:
        key = (
            normalized(row.get("branch_local_spec_kind")),
            normalized(row.get("symbol")),
            normalized(row.get("route_session")),
            normalized(row.get("spec_context_mode")),
        )
        grouped.setdefault(key, []).append(row)
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        rows = grouped[key]
        scores = [as_float(row.get("replay_rerun_score")) for row in rows]
        numeric_scores = [score for score in scores if score is not None]
        output.append(
            boundary_row(
                {
                    "spec_execution_scope_rollup_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SPEC-EXEC-SCOPE-{len(output) + 1:05d}"
                    ),
                    "branch_local_spec_kind": key[0],
                    "symbol": key[1],
                    "route_session": key[2],
                    "spec_context_mode": key[3],
                    "spec_execution_result_rows": len(rows),
                    "joined_exact_rows": sum(
                        row.get("spec_execution_join_status") == "SPEC_EXECUTION_REPLAY_SCORE_JOINED_EXACT"
                        for row in rows
                    ),
                    "mean_replay_rerun_score": (
                        round(sum(numeric_scores) / len(numeric_scores), 6) if numeric_scores else None
                    ),
                    "spec_execution_scope_rollup_status": "RUNTIME_REPLAY_SPEC_EXECUTION_SCOPE_ROLLUP_MATERIALIZED",
                }
            )
        )
    return output


def system_spec_execution_rows(
    scorer_rows: list[dict[str, Any]],
    comparator_rows: list[dict[str, Any]],
    result_rows: list[dict[str, Any]],
    rollup_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    result_counts = Counter(normalized(row.get("spec_execution_class")) for row in result_rows)
    join_counts = Counter(normalized(row.get("spec_execution_join_status")) for row in result_rows)
    return [
        boundary_row(
            {
                "system_spec_execution_row_id": "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SPEC-EXEC-SYSTEM-0001",
                "scorer_spec_execution_rows": len(scorer_rows),
                "comparator_spec_execution_rows": len(comparator_rows),
                "spec_execution_result_rows": len(result_rows),
                "spec_execution_scope_rollup_rows": len(rollup_rows),
                "spec_execution_class_counts": dict(sorted(result_counts.items())),
                "spec_execution_join_status_counts": dict(sorted(join_counts.items())),
                "system_spec_execution": (
                    "Execute materialized branch-local scorer and comparator specs against replay-score rows."
                ),
                "system_spec_execution_status": "RUNTIME_REPLAY_SPEC_EXECUTION_MATERIALIZED_BRANCH_LOCAL",
            }
        )
    ]


def spec_execution_bucket_rows(
    scorer_rows: list[dict[str, Any]],
    comparator_rows: list[dict[str, Any]],
    result_rows: list[dict[str, Any]],
    rollup_rows: list[dict[str, Any]],
    system_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs = [
        ("scorer_spec_execution_class", scorer_rows, "scorer_spec_execution_class"),
        ("comparator_spec_execution_class", comparator_rows, "comparator_spec_execution_class"),
        ("spec_execution_join_status", result_rows, "spec_execution_join_status"),
        ("spec_execution_scope_rollup_status", rollup_rows, "spec_execution_scope_rollup_status"),
        ("system_spec_execution_status", system_rows, "system_spec_execution_status"),
    ]
    output: list[dict[str, Any]] = []
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "spec_execution_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SPEC-EXEC-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
