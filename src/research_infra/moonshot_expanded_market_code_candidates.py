"""Branch-local code candidates from expanded-market implementation-selection rows."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from statistics import mean
from typing import Any


EXPANDED_MARKET_CODE_CANDIDATES_SURFACE = "src/research_infra/moonshot_expanded_market_code_candidates.py"
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
    output["expanded_market_code_candidates_surface"] = EXPANDED_MARKET_CODE_CANDIDATES_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def as_float(value: Any) -> float | None:
    if value is None or value == "" or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def rounded(value: float | None, places: int = 9) -> float | None:
    return None if value is None else round(float(value), places)


def average(values: list[float]) -> float | None:
    return mean(values) if values else None


def slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return text[:80] or "scope"


def stable_hash(payload: dict[str, Any], length: int = 12) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def decision_family(decision: str | None) -> str:
    text = normalized(decision)
    if text.startswith("IMPLEMENT"):
        return "implement"
    if "AVOID" in text:
        return "avoid"
    if text.startswith("KILL"):
        return "kill"
    if text.startswith("REDESIGN"):
        return "redesign"
    return "missing"


def class_from_decision(decision: str) -> str:
    if decision.startswith("IMPLEMENT"):
        return "follow"
    if "AVOID" in decision:
        return "avoid"
    if decision.startswith("KILL"):
        return "default-off"
    return "redesign"


def candidate_scope(selection_row: dict[str, Any]) -> dict[str, str]:
    return {
        "symbol": normalized(selection_row.get("symbol")),
        "source_symbol": normalized(selection_row.get("source_symbol")),
        "market_timeframe": normalized(selection_row.get("market_timeframe")),
        "route_session": normalized(selection_row.get("route_session")),
        "horizon_id": normalized(selection_row.get("horizon_id")),
        "source_component": normalized(selection_row.get("source_component")),
        "selected_side": normalized(selection_row.get("selected_side")),
    }


def candidate_matches_scope(candidate: dict[str, Any], row: dict[str, Any]) -> bool:
    scope = candidate.get("candidate_scope") or {}
    return all(normalized(row.get(key)) == normalized(value) for key, value in scope.items())


def code_expression_for_scope(scope: dict[str, str]) -> str:
    comparisons = [
        f"row.get({json.dumps(key)}) == {json.dumps(value)}"
        for key, value in scope.items()
    ]
    return " and ".join(comparisons)


def implement_candidate_row(selection_row: dict[str, Any], row_index: int) -> dict[str, Any]:
    scope = candidate_scope(selection_row)
    scope_hash = stable_hash(scope)
    function_name = f"expanded_market_side_filter_{slug(scope['symbol'])}_{slug(scope['market_timeframe'])}_{scope_hash}"
    selected_r = as_float(selection_row.get("selected_intrabar_cost_adjusted_simulated_r"))
    rejected_r = as_float(selection_row.get("rejected_intrabar_cost_adjusted_simulated_r"))
    spread = as_float(selection_row.get("selected_minus_rejected_intrabar_cost_adjusted_r"))
    return boundary_row(
        {
            "code_candidate_row_id": f"OHLC-GTOS-EXPANDED-MARKET-CODE-CANDIDATE-{row_index:07d}",
            "input_implementation_selection_row_id": selection_row.get("implementation_selection_row_id"),
            "input_side_pair_robustness_row_id": selection_row.get("input_side_pair_robustness_row_id"),
            "input_temporal_robustness_row_id": selection_row.get("input_temporal_robustness_row_id"),
            "input_selected_intrabar_geometry_row_id": selection_row.get("input_selected_intrabar_geometry_row_id"),
            "symbol": selection_row.get("symbol"),
            "source_symbol": selection_row.get("source_symbol"),
            "market_timeframe": selection_row.get("market_timeframe"),
            "route_session": selection_row.get("route_session"),
            "horizon_id": selection_row.get("horizon_id"),
            "source_component": selection_row.get("source_component"),
            "source_path": selection_row.get("source_path"),
            "source_file_sha256": selection_row.get("source_file_sha256"),
            "selected_side": selection_row.get("selected_side"),
            "rejected_side": selection_row.get("rejected_side"),
            "candidate_scope": scope,
            "candidate_scope_sha256": stable_hash(scope, 64),
            "candidate_function_name": function_name,
            "branch_local_code_expression": code_expression_for_scope(scope),
            "branch_local_action": "FOLLOW_SELECTED_SIDE_IN_BRANCH_LOCAL_REPLAY_ONLY",
            "selected_intrabar_cost_adjusted_simulated_r": rounded(selected_r),
            "rejected_intrabar_cost_adjusted_simulated_r": rounded(rejected_r),
            "selected_minus_rejected_intrabar_cost_adjusted_r": rounded(spread),
            "temporal_winner_consistency_share": selection_row.get("temporal_winner_consistency_share"),
            "temporal_positive_winner_fold_share": selection_row.get("temporal_positive_winner_fold_share"),
            "effective_n": selection_row.get("effective_n"),
            "source_selection_decision": selection_row.get("keep_kill_redesign_implement_decision"),
            "follow_inverse_default_off_avoid_class": "follow",
            "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_BRANCH_LOCAL_CODE_CANDIDATE",
        }
    )


def evidence_row(selection_row: dict[str, Any], row_index: int) -> dict[str, Any]:
    decision = normalized(selection_row.get("keep_kill_redesign_implement_decision"))
    family = decision_family(decision)
    evidence_decision = {
        "avoid": "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_CODE_EVIDENCE",
        "kill": "KILL_EXPANDED_MARKET_CODE_EVIDENCE",
        "redesign": "REDESIGN_EXPANDED_MARKET_CODE_EVIDENCE",
    }.get(family, "REDESIGN_EXPANDED_MARKET_CODE_EVIDENCE")
    return boundary_row(
        {
            "code_evidence_row_id": f"OHLC-GTOS-EXPANDED-MARKET-CODE-EVIDENCE-{row_index:07d}",
            "input_implementation_selection_row_id": selection_row.get("implementation_selection_row_id"),
            "input_side_pair_robustness_row_id": selection_row.get("input_side_pair_robustness_row_id"),
            "input_temporal_robustness_row_id": selection_row.get("input_temporal_robustness_row_id"),
            "input_selected_intrabar_geometry_row_id": selection_row.get("input_selected_intrabar_geometry_row_id"),
            "input_rejected_intrabar_geometry_row_id": selection_row.get("input_rejected_intrabar_geometry_row_id"),
            "symbol": selection_row.get("symbol"),
            "source_symbol": selection_row.get("source_symbol"),
            "market_timeframe": selection_row.get("market_timeframe"),
            "route_session": selection_row.get("route_session"),
            "horizon_id": selection_row.get("horizon_id"),
            "source_component": selection_row.get("source_component"),
            "source_path": selection_row.get("source_path"),
            "source_file_sha256": selection_row.get("source_file_sha256"),
            "selected_side": selection_row.get("selected_side"),
            "rejected_side": selection_row.get("rejected_side"),
            "selection_decision": decision,
            "selected_intrabar_cost_adjusted_simulated_r": selection_row.get("selected_intrabar_cost_adjusted_simulated_r"),
            "rejected_intrabar_cost_adjusted_simulated_r": selection_row.get("rejected_intrabar_cost_adjusted_simulated_r"),
            "selected_minus_rejected_intrabar_cost_adjusted_r": selection_row.get("selected_minus_rejected_intrabar_cost_adjusted_r"),
            "temporal_winner_consistency_share": selection_row.get("temporal_winner_consistency_share"),
            "temporal_recent_half_winner_cost_adjusted_r": selection_row.get("temporal_recent_half_winner_cost_adjusted_r"),
            "evidence_family": family,
            "branch_local_evidence_action": "PRESERVE_ROW_LEVEL_NON_IMPLEMENT_EVIDENCE",
            "follow_inverse_default_off_avoid_class": class_from_decision(evidence_decision),
            "keep_kill_redesign_implement_decision": evidence_decision,
        }
    )


def self_test_row(candidate: dict[str, Any], row_index: int) -> dict[str, Any]:
    scope = candidate.get("candidate_scope") or {}
    positive = dict(scope)
    negative = dict(scope)
    negative["selected_side"] = "SHORT" if scope.get("selected_side") == "LONG" else "LONG"
    positive_pass = candidate_matches_scope(candidate, positive)
    negative_pass = not candidate_matches_scope(candidate, negative)
    status = "CODE_CANDIDATE_SELF_TEST_PASS" if positive_pass and negative_pass else "CODE_CANDIDATE_SELF_TEST_REPAIR"
    return boundary_row(
        {
            "code_candidate_self_test_row_id": f"OHLC-GTOS-EXPANDED-MARKET-CODE-CANDIDATE-SELF-TEST-{row_index:07d}",
            "input_code_candidate_row_id": candidate.get("code_candidate_row_id"),
            "candidate_function_name": candidate.get("candidate_function_name"),
            "positive_scope_match": positive_pass,
            "negative_scope_reject": negative_pass,
            "self_test_status": status,
            "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_BRANCH_LOCAL_CODE_CANDIDATE"
            if status.endswith("PASS")
            else "REDESIGN_EXPANDED_MARKET_CODE_CANDIDATE_SELF_TEST",
        }
    )


def code_candidate_rows(
    selection_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    for row in selection_rows:
        if decision_family(row.get("keep_kill_redesign_implement_decision")) == "implement":
            candidates.append(implement_candidate_row(row, len(candidates) + 1))
        else:
            evidence.append(evidence_row(row, len(evidence) + 1))
    self_tests = [self_test_row(candidate, index) for index, candidate in enumerate(candidates, start=1)]
    return candidates, evidence, self_tests


def aggregate_code_candidate_rows(
    candidates: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        key = (
            normalized(row.get("symbol")),
            normalized(row.get("market_timeframe")),
            normalized(row.get("route_session")),
            normalized(row.get("horizon_id")),
            normalized(row.get("source_component")),
            normalized(row.get("selected_side")),
            "code_candidate",
        )
        grouped[key].append(row)
    for row in evidence:
        key = (
            normalized(row.get("symbol")),
            normalized(row.get("market_timeframe")),
            normalized(row.get("route_session")),
            normalized(row.get("horizon_id")),
            normalized(row.get("source_component")),
            normalized(row.get("selected_side")),
            normalized(row.get("follow_inverse_default_off_avoid_class")),
        )
        grouped[key].append(row)
    total_rows = len(candidates) + len(evidence) or 1
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        decisions = Counter(normalized(row.get("keep_kill_redesign_implement_decision")) for row in members)
        selected_values = [as_float(row.get("selected_intrabar_cost_adjusted_simulated_r")) for row in members]
        selected_values = [value for value in selected_values if value is not None]
        output.append(
            boundary_row(
                {
                    "code_candidate_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-CODE-CANDIDATE-AGG-{len(output) + 1:06d}"
                    ),
                    "symbol": key[0],
                    "market_timeframe": key[1],
                    "route_session": key[2],
                    "horizon_id": key[3],
                    "source_component": key[4],
                    "selected_side": key[5],
                    "aggregate_family": key[6],
                    "row_count": len(members),
                    "source_path_count": len({row.get("source_path") for row in members}),
                    "average_selected_intrabar_cost_adjusted_simulated_r": rounded(average(selected_values)),
                    "concentration_share_of_all_code_candidate_rows": rounded(len(members) / total_rows),
                    "decision_counts": dict(sorted(decisions.items())),
                    "keep_kill_redesign_implement_decision": decisions.most_common(1)[0][0],
                }
            )
        )
    return output


def system_code_candidate_rows(
    candidates: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    self_tests: list[dict[str, Any]],
    aggregates: list[dict[str, Any]],
    input_selection_rows: int,
) -> list[dict[str, Any]]:
    return [
        boundary_row(
            {
                "code_candidate_system_row_id": "OHLC-GTOS-EXPANDED-MARKET-CODE-CANDIDATE-SYSTEM-0001",
                "input_implementation_selection_rows": input_selection_rows,
                "code_candidate_rows": len(candidates),
                "code_evidence_rows": len(evidence),
                "self_test_rows": len(self_tests),
                "aggregate_rows": len(aggregates),
                "self_test_pass_rows": sum(
                    1 for row in self_tests if row.get("self_test_status") == "CODE_CANDIDATE_SELF_TEST_PASS"
                ),
                "source_path_count": len({row.get("source_path") for row in candidates + evidence}),
                "symbol_count": len({row.get("symbol") for row in candidates + evidence}),
                "decision_counts": dict(
                    sorted(
                        Counter(
                            row.get("keep_kill_redesign_implement_decision")
                            for row in candidates + evidence
                        ).items()
                    )
                ),
            }
        )
    ]
