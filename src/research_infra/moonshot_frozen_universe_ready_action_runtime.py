"""Branch-local runtime rule materialization for frozen ready actions."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any


FROZEN_UNIVERSE_READY_ACTION_RUNTIME_SURFACE = (
    "src/research_infra/moonshot_frozen_universe_ready_action_runtime.py"
)

MATCH_FIELDS = (
    "symbol_family",
    "symbol",
    "source_symbol",
    "market_timeframe",
    "route_session",
    "horizon_id",
    "side",
    "source_path_sha256",
    "source_file_sha256",
)

EVIDENCE_FIELDS = (
    "source_path",
    "gross_simulated_r",
    "cost_adjusted_simulated_r",
    "stress_simulated_r",
    "gross_simulated_r_expectancy",
    "cost_adjusted_simulated_r_expectancy",
    "stress_simulated_r_expectancy",
    "effective_n",
    "source_row_count",
)


def research_boundary() -> dict[str, Any]:
    return {
        "boundary_schema": "concrete_branch_local_research_boundary_v1",
        "artifact_scope": "branch_local_research",
        "production_import_path": False,
        "mutates_order_risk_prompt_safety_or_mt5": False,
        "runtime_candidate_use_permitted": False,
        "unconditional_scalar_use_permitted": False,
    }


def boundary_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["frozen_universe_ready_action_runtime_surface"] = (
        FROZEN_UNIVERSE_READY_ACTION_RUNTIME_SURFACE
    )
    output["research_boundary"] = research_boundary()
    return output


def stable_sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def action_class(row: dict[str, Any]) -> str:
    role = str(row.get("scorer_filter_router_selector_role") or row.get("implementation_role") or "")
    decision = str(row.get("keep_kill_redesign_implement_decision") or "")
    text = f"{role} {decision}".lower()
    if "avoid" in text:
        return "avoid_filter"
    if "follow" in text:
        return "follow_rule"
    return "selector_rule"


def rule_scope(row: dict[str, Any]) -> dict[str, Any]:
    return {field: row.get(field) for field in MATCH_FIELDS if row.get(field) not in (None, "")}


def evidence(row: dict[str, Any]) -> dict[str, Any]:
    return {field: row.get(field) for field in EVIDENCE_FIELDS if row.get(field) not in (None, "")}


def missing_match_fields(row: dict[str, Any]) -> list[str]:
    return [field for field in MATCH_FIELDS if row.get(field) in (None, "")]


def ready_action_runtime_rule(row: dict[str, Any], sequence: int) -> dict[str, Any]:
    scope = rule_scope(row)
    action = action_class(row)
    expression = {
        "action_class": action,
        "match_scope": scope,
        "source_row_ids_sha256": row.get("source_row_ids_sha256"),
        "source_artifact_path": row.get("source_artifact_path"),
    }
    return boundary_row(
        {
            "frozen_ready_action_runtime_rule_row_id": (
                f"FROZEN-MOONSHOT-READY-ACTION-RUNTIME-RULE-{sequence:07d}"
            ),
            "input_implementation_ready_bundle_row_id": row.get(
                "implementation_ready_bundle_row_id"
            ),
            "action_class": action,
            "branch_local_runtime_role": (
                "branch-local avoid comparator/filter"
                if action == "avoid_filter"
                else "branch-local follow scorer/rule"
            ),
            "match_fields": list(MATCH_FIELDS),
            "missing_match_fields": missing_match_fields(row),
            "match_scope": scope,
            **scope,
            **evidence(row),
            "source_action_closure_artifact": row.get("source_artifact_path"),
            "source_action_closure_row_count": row.get("source_row_count"),
            "source_row_ids_sha256": row.get("source_row_ids_sha256"),
            "keep_kill_redesign_implement_decision": row.get(
                "keep_kill_redesign_implement_decision"
            ),
            "rule_expression_sha256": stable_sha256(expression),
            "tests_needed": [
                "tests/research_infra/test_moonshot_unified_execution_scorer.py",
                "research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/verify_frozen_universe_ready_action_runtime_2026_05_17.py",
            ],
        }
    )


def rule_matches_payload(rule: dict[str, Any], payload: dict[str, Any]) -> bool:
    scope = rule.get("match_scope") or {}
    return all(str(payload.get(field) or "") == str(value or "") for field, value in scope.items())


def self_test_row(rule: dict[str, Any], sequence: int) -> dict[str, Any]:
    payload = dict(rule.get("match_scope") or {})
    matched = rule_matches_payload(rule, payload)
    has_evidence = rule.get("cost_adjusted_simulated_r") is not None and rule.get(
        "stress_simulated_r"
    ) is not None
    missing = rule.get("missing_match_fields") or []
    return boundary_row(
        {
            "frozen_ready_action_runtime_self_test_row_id": (
                f"FROZEN-MOONSHOT-READY-ACTION-RUNTIME-SELF-TEST-{sequence:07d}"
            ),
            "input_runtime_rule_row_id": rule.get("frozen_ready_action_runtime_rule_row_id"),
            "self_test_status": (
                "FROZEN_READY_ACTION_RUNTIME_SELF_TEST_PASS"
                if matched and has_evidence and not missing
                else "FROZEN_READY_ACTION_RUNTIME_SELF_TEST_REPAIR_REQUIRED"
            ),
            "match_payload": payload,
            "matched": matched,
            "has_cost_stress_evidence": has_evidence,
            "missing_match_fields": missing,
            "action_class": rule.get("action_class"),
            "symbol_family": rule.get("symbol_family"),
            "market_timeframe": rule.get("market_timeframe"),
            "route_session": rule.get("route_session"),
            "horizon_id": rule.get("horizon_id"),
            "side": rule.get("side"),
        }
    )


def aggregate_rules(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], dict[str, Any]] = {}
    for row in rules:
        key = (
            str(row.get("action_class") or ""),
            str(row.get("symbol_family") or ""),
            str(row.get("market_timeframe") or ""),
            str(row.get("route_session") or ""),
            str(row.get("horizon_id") or ""),
            str(row.get("side") or ""),
        )
        bucket = groups.setdefault(
            key,
            {
                "action_class": key[0],
                "symbol_family": key[1],
                "market_timeframe": key[2],
                "route_session": key[3],
                "horizon_id": key[4],
                "side": key[5],
                "rule_count": 0,
                "source_row_count": 0,
                "effective_n_sum": 0.0,
                "cost_sum": 0.0,
                "stress_sum": 0.0,
            },
        )
        bucket["rule_count"] += 1
        bucket["source_row_count"] += int(row.get("source_action_closure_row_count") or 0)
        bucket["effective_n_sum"] += float(row.get("effective_n") or 0.0)
        bucket["cost_sum"] += float(row.get("cost_adjusted_simulated_r") or 0.0)
        bucket["stress_sum"] += float(row.get("stress_simulated_r") or 0.0)

    output: list[dict[str, Any]] = []
    for sequence, bucket in enumerate(groups.values(), start=1):
        count = int(bucket["rule_count"])
        output.append(
            boundary_row(
                {
                    "frozen_ready_action_runtime_aggregate_row_id": (
                        f"FROZEN-MOONSHOT-READY-ACTION-RUNTIME-AGG-{sequence:07d}"
                    ),
                    **{
                        key: value
                        for key, value in bucket.items()
                        if key not in {"cost_sum", "stress_sum"}
                    },
                    "average_cost_adjusted_simulated_r": (
                        round(bucket["cost_sum"] / count, 9) if count else None
                    ),
                    "average_stress_simulated_r": (
                        round(bucket["stress_sum"] / count, 9) if count else None
                    ),
                }
            )
        )
    return output


def status_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(row.get(field) for row in rows).items()))
