"""Execute expanded-market branch-local code candidates against held selection rows."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any


EXPANDED_MARKET_CODE_CANDIDATE_EXECUTION_SURFACE = (
    "src/research_infra/moonshot_expanded_market_code_candidate_execution.py"
)
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"
SCOPE_KEYS = ("horizon_id", "market_timeframe", "route_session", "selected_side", "source_component", "source_symbol", "symbol")


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
    output["expanded_market_code_candidate_execution_surface"] = EXPANDED_MARKET_CODE_CANDIDATE_EXECUTION_SURFACE
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


def candidate_scope_key(candidate: dict[str, Any]) -> tuple[str, ...]:
    scope = candidate.get("candidate_scope") or {}
    return tuple(normalized(scope.get(key)) for key in SCOPE_KEYS)


def selection_scope_key(selection: dict[str, Any]) -> tuple[str, ...]:
    return tuple(normalized(selection.get(key)) for key in SCOPE_KEYS)


def execution_decision(implement_matches: int, nonimplement_matches: int, matched_rows: int) -> str:
    if matched_rows == 0:
        return "REDESIGN_EXPANDED_MARKET_CODE_CANDIDATE_EXECUTION_NO_MATCH"
    if implement_matches > 0 and nonimplement_matches == 0:
        return "IMPLEMENT_EXPANDED_MARKET_CODE_CANDIDATE_EXECUTION"
    if implement_matches > 0 and nonimplement_matches > 0:
        return "REDESIGN_EXPANDED_MARKET_CODE_CANDIDATE_SCOPE_LEAKAGE"
    return "KILL_EXPANDED_MARKET_CODE_CANDIDATE_EXECUTION"


def execute_code_candidates(
    candidates: list[dict[str, Any]],
    selection_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selection_index: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for selection in selection_rows:
        selection_index[selection_scope_key(selection)].append(selection)

    execution_rows: list[dict[str, Any]] = []
    match_rows: list[dict[str, Any]] = []
    for candidate in candidates:
        matches = selection_index.get(candidate_scope_key(candidate), [])
        family_counts = Counter(decision_family(row.get("keep_kill_redesign_implement_decision")) for row in matches)
        implement_matches = int(family_counts.get("implement", 0))
        nonimplement_matches = len(matches) - implement_matches
        selected_values = [as_float(row.get("selected_intrabar_cost_adjusted_simulated_r")) for row in matches]
        selected_values = [value for value in selected_values if value is not None]
        spread_values = [as_float(row.get("selected_minus_rejected_intrabar_cost_adjusted_r")) for row in matches]
        spread_values = [value for value in spread_values if value is not None]
        decision = execution_decision(implement_matches, nonimplement_matches, len(matches))
        execution_row_id = f"OHLC-GTOS-EXPANDED-MARKET-CODE-CANDIDATE-EXEC-{len(execution_rows) + 1:07d}"
        execution_rows.append(
            boundary_row(
                {
                    "code_candidate_execution_row_id": execution_row_id,
                    "input_code_candidate_row_id": candidate.get("code_candidate_row_id"),
                    "input_implementation_selection_row_id": candidate.get("input_implementation_selection_row_id"),
                    "candidate_scope_sha256": candidate.get("candidate_scope_sha256"),
                    "candidate_function_name": candidate.get("candidate_function_name"),
                    "symbol": candidate.get("symbol"),
                    "source_symbol": candidate.get("source_symbol"),
                    "market_timeframe": candidate.get("market_timeframe"),
                    "route_session": candidate.get("route_session"),
                    "horizon_id": candidate.get("horizon_id"),
                    "source_component": candidate.get("source_component"),
                    "selected_side": candidate.get("selected_side"),
                    "matched_selection_rows": len(matches),
                    "matched_implement_rows": implement_matches,
                    "matched_nonimplement_rows": nonimplement_matches,
                    "matched_avoid_rows": int(family_counts.get("avoid", 0)),
                    "matched_kill_rows": int(family_counts.get("kill", 0)),
                    "matched_redesign_rows": int(family_counts.get("redesign", 0)),
                    "selection_precision": rounded(implement_matches / len(matches) if matches else None),
                    "average_selected_intrabar_cost_adjusted_simulated_r": rounded(average(selected_values)),
                    "average_selected_minus_rejected_intrabar_cost_adjusted_r": rounded(average(spread_values)),
                    "execution_status": "CODE_CANDIDATE_EXECUTION_PASS"
                    if decision.startswith("IMPLEMENT")
                    else "CODE_CANDIDATE_EXECUTION_REPAIR",
                    "follow_inverse_default_off_avoid_class": class_from_decision(decision),
                    "keep_kill_redesign_implement_decision": decision,
                }
            )
        )
        for match in matches:
            match_family = decision_family(match.get("keep_kill_redesign_implement_decision"))
            match_rows.append(
                boundary_row(
                    {
                        "code_candidate_match_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-CODE-CANDIDATE-MATCH-{len(match_rows) + 1:08d}"
                        ),
                        "input_code_candidate_execution_row_id": execution_row_id,
                        "input_code_candidate_row_id": candidate.get("code_candidate_row_id"),
                        "input_matched_implementation_selection_row_id": match.get("implementation_selection_row_id"),
                        "candidate_scope_sha256": candidate.get("candidate_scope_sha256"),
                        "symbol": match.get("symbol"),
                        "source_symbol": match.get("source_symbol"),
                        "market_timeframe": match.get("market_timeframe"),
                        "route_session": match.get("route_session"),
                        "horizon_id": match.get("horizon_id"),
                        "source_component": match.get("source_component"),
                        "source_path": match.get("source_path"),
                        "source_file_sha256": match.get("source_file_sha256"),
                        "selected_side": match.get("selected_side"),
                        "matched_selection_decision": match.get("keep_kill_redesign_implement_decision"),
                        "matched_decision_family": match_family,
                        "selected_intrabar_cost_adjusted_simulated_r": match.get("selected_intrabar_cost_adjusted_simulated_r"),
                        "selected_minus_rejected_intrabar_cost_adjusted_r": match.get("selected_minus_rejected_intrabar_cost_adjusted_r"),
                        "match_status": "MATCHED_IMPLEMENT_SELECTION" if match_family == "implement" else "MATCHED_NONIMPLEMENT_SELECTION",
                        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_CODE_CANDIDATE_MATCH"
                        if match_family == "implement"
                        else "REDESIGN_EXPANDED_MARKET_CODE_CANDIDATE_MATCH_SCOPE_LEAKAGE",
                    }
                )
            )
    return execution_rows, match_rows


def aggregate_execution_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
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
    total_rows = len(rows) or 1
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in members)
        output.append(
            boundary_row(
                {
                    "code_candidate_execution_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-CODE-CANDIDATE-EXEC-AGG-{len(output) + 1:06d}"
                    ),
                    "symbol": key[0],
                    "market_timeframe": key[1],
                    "route_session": key[2],
                    "horizon_id": key[3],
                    "source_component": key[4],
                    "selected_side": key[5],
                    "follow_inverse_default_off_avoid_class": key[6],
                    "row_count": len(members),
                    "matched_selection_rows": sum(int(row.get("matched_selection_rows") or 0) for row in members),
                    "matched_implement_rows": sum(int(row.get("matched_implement_rows") or 0) for row in members),
                    "matched_nonimplement_rows": sum(int(row.get("matched_nonimplement_rows") or 0) for row in members),
                    "average_selection_precision": rounded(
                        average(
                            [
                                as_float(row.get("selection_precision"))
                                for row in members
                                if as_float(row.get("selection_precision")) is not None
                            ]
                        )
                    ),
                    "concentration_share_of_all_execution_rows": rounded(len(members) / total_rows),
                    "decision_counts": dict(sorted(decisions.items())),
                    "keep_kill_redesign_implement_decision": decisions.most_common(1)[0][0],
                }
            )
        )
    return output


def system_execution_rows(
    execution_rows: list[dict[str, Any]],
    match_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    input_candidate_rows: int,
    input_selection_rows: int,
) -> list[dict[str, Any]]:
    return [
        boundary_row(
            {
                "code_candidate_execution_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-CODE-CANDIDATE-EXEC-SYSTEM-0001"
                ),
                "input_code_candidate_rows": input_candidate_rows,
                "input_selection_rows": input_selection_rows,
                "code_candidate_execution_rows": len(execution_rows),
                "code_candidate_match_rows": len(match_rows),
                "aggregate_rows": len(aggregate_rows),
                "execution_pass_rows": sum(
                    1 for row in execution_rows if row.get("execution_status") == "CODE_CANDIDATE_EXECUTION_PASS"
                ),
                "execution_repair_rows": sum(
                    1 for row in execution_rows if row.get("execution_status") == "CODE_CANDIDATE_EXECUTION_REPAIR"
                ),
                "decision_counts": dict(
                    sorted(Counter(row.get("keep_kill_redesign_implement_decision") for row in execution_rows).items())
                ),
            }
        )
    ]
