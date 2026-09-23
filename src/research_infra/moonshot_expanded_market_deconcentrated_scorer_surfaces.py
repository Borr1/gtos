"""Callable branch-local scorer surfaces from deconcentrated selection rows."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from statistics import mean
from typing import Any

from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_DECONCENTRATED_SCORER_SURFACES_SURFACE = (
    "src/research_infra/moonshot_expanded_market_deconcentrated_scorer_surfaces.py"
)
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"
IMPLEMENT_DECISION = "IMPLEMENT_EXPANDED_MARKET_DECONCENTRATED_SCORER_CANDIDATE"


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
    output["expanded_market_deconcentrated_scorer_surfaces_surface"] = (
        EXPANDED_MARKET_DECONCENTRATED_SCORER_SURFACES_SURFACE
    )
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def average(values: list[float]) -> float | None:
    return mean(values) if values else None


def digest(parts: list[Any]) -> str:
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def is_implement(row: dict[str, Any]) -> bool:
    return row.get("keep_kill_redesign_implement_decision") == IMPLEMENT_DECISION


def surface_key(row: dict[str, Any]) -> tuple[str, str, str, str, str, str, str]:
    return (
        normalized(row.get("symbol_family")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("side")),
        normalized(row.get("source_path")),
        normalized(row.get("source_file_sha256")),
    )


def matches_surface(surface: dict[str, Any], row: dict[str, Any]) -> bool:
    return (
        row.get("symbol_family") == surface.get("symbol_family")
        and row.get("market_timeframe") == surface.get("market_timeframe")
        and row.get("route_session") == surface.get("route_session")
        and row.get("horizon_id") == surface.get("horizon_id")
        and row.get("side") == surface.get("side")
        and row.get("source_path") == surface.get("source_path")
        and row.get("source_file_sha256") == surface.get("source_file_sha256")
    )


def expression_for_key(key: tuple[str, str, str, str, str, str, str]) -> str:
    labels = ("symbol_family", "market_timeframe", "route_session", "horizon_id", "side", "source_path", "source_file_sha256")
    return " and ".join(f"{label}={value}" for label, value in zip(labels, key))


def surface_from_members(key: tuple[str, str, str, str, str, str, str], members: list[dict[str, Any]], sequence: int) -> dict[str, Any]:
    costs = [value for value in (as_float(row.get("deconcentrated_cost_adjusted_simulated_r")) for row in members) if value is not None]
    stress = [value for value in (as_float(row.get("deconcentrated_stress_simulated_r")) for row in members) if value is not None]
    scores = [value for value in (as_float(row.get("numeric_priority_score")) for row in members) if value is not None]
    scope_sha = digest(list(key))
    return boundary_row(
        {
            "expanded_market_deconcentrated_scorer_surface_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-DECON-SCORER-SURFACE-{sequence:06d}"
            ),
            "surface_scope_sha256": scope_sha,
            "surface_function_name": f"score_decon_market_{scope_sha[:16]}",
            "surface_expression": expression_for_key(key),
            "symbol_family": key[0],
            "market_timeframe": key[1],
            "route_session": key[2],
            "horizon_id": key[3],
            "side": key[4],
            "source_path": key[5],
            "source_file_sha256": key[6],
            "surface_member_rows": len(members),
            "source_path_count": len({row.get("source_path") for row in members}),
            "source_family_count": len({row.get("performance_source_family") for row in members}),
            "effective_n_sum": sum(int(row.get("effective_n") or 0) for row in members),
            "deconcentrated_effective_n_sum": rounded(
                sum(float(row.get("deconcentrated_effective_n") or 0.0) for row in members)
            ),
            "average_deconcentrated_cost_adjusted_simulated_r": rounded(average(costs)),
            "average_deconcentrated_stress_simulated_r": rounded(average(stress)),
            "average_numeric_priority_score": rounded(average(scores)),
            "target_first_count_sum": sum(int(row.get("target_first_count") or 0) for row in members),
            "stop_first_count_sum": sum(int(row.get("stop_first_count") or 0) for row in members),
            "neither_count_sum": sum(int(row.get("neither_count") or 0) for row in members),
            "ambiguous_count_sum": sum(int(row.get("ambiguous_count") or 0) for row in members),
            "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_DECONCENTRATED_SCORER_SURFACE",
            "follow_inverse_default_off_avoid_class": "follow",
        }
    )


def member_row(surface: dict[str, Any], row: dict[str, Any], sequence: int) -> dict[str, Any]:
    return boundary_row(
        {
            "expanded_market_deconcentrated_scorer_member_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-DECON-SCORER-MEMBER-{sequence:07d}"
            ),
            "input_scorer_surface_row_id": surface.get("expanded_market_deconcentrated_scorer_surface_row_id"),
            "input_selection_row_id": row.get("expanded_market_deconcentrated_selection_row_id"),
            "surface_scope_sha256": surface.get("surface_scope_sha256"),
            "symbol_family": row.get("symbol_family"),
            "symbol": row.get("symbol"),
            "source_symbol": row.get("source_symbol"),
            "market_timeframe": row.get("market_timeframe"),
            "route_session": row.get("route_session"),
            "horizon_id": row.get("horizon_id"),
            "side": row.get("side"),
            "source_path": row.get("source_path"),
            "source_file_sha256": row.get("source_file_sha256"),
            "entry_reference": row.get("entry_reference"),
            "proxy_entry_price": row.get("proxy_entry_price"),
            "proxy_denominator_price": row.get("proxy_denominator_price"),
            "proxy_target_price": row.get("proxy_target_price"),
            "proxy_stop_price": row.get("proxy_stop_price"),
            "path_order_result": row.get("path_order_result"),
            "fill_status": row.get("fill_status"),
            "gross_simulated_r": row.get("gross_simulated_r"),
            "cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
            "stress_simulated_r": row.get("stress_simulated_r"),
            "deconcentrated_effective_n": row.get("deconcentrated_effective_n"),
            "deconcentrated_cost_adjusted_simulated_r": row.get("deconcentrated_cost_adjusted_simulated_r"),
            "deconcentrated_stress_simulated_r": row.get("deconcentrated_stress_simulated_r"),
            "numeric_priority_score": row.get("numeric_priority_score"),
            "win_count": int(row.get("win_count") or 0),
            "loss_count": int(row.get("loss_count") or 0),
            "zero_count": int(row.get("zero_count") or 0),
            "target_first_count": int(row.get("target_first_count") or 0),
            "stop_first_count": int(row.get("stop_first_count") or 0),
            "neither_count": int(row.get("neither_count") or 0),
            "ambiguous_count": int(row.get("ambiguous_count") or 0),
            "keep_kill_redesign_implement_decision": row.get("keep_kill_redesign_implement_decision"),
            "follow_inverse_default_off_avoid_class": row.get("follow_inverse_default_off_avoid_class"),
        }
    )


def evidence_row(row: dict[str, Any], sequence: int) -> dict[str, Any]:
    return boundary_row(
        {
            "expanded_market_deconcentrated_nonimplement_evidence_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-DECON-NONIMPLEMENT-{sequence:07d}"
            ),
            "input_selection_row_id": row.get("expanded_market_deconcentrated_selection_row_id"),
            "symbol_family": row.get("symbol_family"),
            "symbol": row.get("symbol"),
            "source_symbol": row.get("source_symbol"),
            "market_timeframe": row.get("market_timeframe"),
            "route_session": row.get("route_session"),
            "horizon_id": row.get("horizon_id"),
            "side": row.get("side"),
            "source_path": row.get("source_path"),
            "source_file_sha256": row.get("source_file_sha256"),
            "entry_reference": row.get("entry_reference"),
            "proxy_entry_price": row.get("proxy_entry_price"),
            "proxy_denominator_price": row.get("proxy_denominator_price"),
            "proxy_target_price": row.get("proxy_target_price"),
            "proxy_stop_price": row.get("proxy_stop_price"),
            "path_order_result": row.get("path_order_result"),
            "fill_status": row.get("fill_status"),
            "gross_simulated_r": row.get("gross_simulated_r"),
            "cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
            "stress_simulated_r": row.get("stress_simulated_r"),
            "deconcentrated_effective_n": row.get("deconcentrated_effective_n"),
            "deconcentrated_cost_adjusted_simulated_r": row.get("deconcentrated_cost_adjusted_simulated_r"),
            "deconcentrated_stress_simulated_r": row.get("deconcentrated_stress_simulated_r"),
            "numeric_priority_score": row.get("numeric_priority_score"),
            "selection_reason": row.get("selection_reason"),
            "keep_kill_redesign_implement_decision": row.get("keep_kill_redesign_implement_decision"),
            "follow_inverse_default_off_avoid_class": row.get("follow_inverse_default_off_avoid_class"),
        }
    )


def self_test_row(surface: dict[str, Any], members: list[dict[str, Any]], sequence: int) -> dict[str, Any]:
    positive = members[0] if members else {}
    negative = dict(positive)
    negative["side"] = "SHORT" if positive.get("side") == "LONG" else "LONG"
    return boundary_row(
        {
            "expanded_market_deconcentrated_scorer_self_test_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-DECON-SCORER-SELFTEST-{sequence:06d}"
            ),
            "input_scorer_surface_row_id": surface.get("expanded_market_deconcentrated_scorer_surface_row_id"),
            "surface_scope_sha256": surface.get("surface_scope_sha256"),
            "positive_member_match": matches_surface(surface, positive),
            "negative_side_mismatch_rejected": not matches_surface(surface, negative),
            "self_test_status": "DECONCENTRATED_SCORER_SURFACE_SELF_TEST_PASS"
            if matches_surface(surface, positive) and not matches_surface(surface, negative)
            else "DECONCENTRATED_SCORER_SURFACE_SELF_TEST_FAIL",
        }
    )


def scorer_surface_rows(
    selection_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    implement_groups: dict[tuple[str, str, str, str, str, str, str], list[dict[str, Any]]] = {}
    nonimplement_rows: list[dict[str, Any]] = []
    for row in selection_rows:
        if is_implement(row):
            implement_groups.setdefault(surface_key(row), []).append(row)
        else:
            nonimplement_rows.append(row)

    surfaces: list[dict[str, Any]] = []
    members: list[dict[str, Any]] = []
    self_tests: list[dict[str, Any]] = []
    for key in sorted(implement_groups):
        group_members = implement_groups[key]
        surface = surface_from_members(key, group_members, len(surfaces) + 1)
        surfaces.append(surface)
        for row in group_members:
            members.append(member_row(surface, row, len(members) + 1))
        self_tests.append(self_test_row(surface, group_members, len(self_tests) + 1))

    evidence = [evidence_row(row, index) for index, row in enumerate(nonimplement_rows, 1)]
    issues = [
        boundary_row(
            {
                "expanded_market_deconcentrated_scorer_issue_row_id": (
                    f"OHLC-GTOS-EXPANDED-MARKET-DECON-SCORER-ISSUE-{index:06d}"
                ),
                "input_scorer_surface_row_id": row.get("input_scorer_surface_row_id"),
                "surface_scope_sha256": row.get("surface_scope_sha256"),
                "issue_status": row.get("self_test_status"),
            }
        )
        for index, row in enumerate(self_tests, 1)
        if row.get("self_test_status") != "DECONCENTRATED_SCORER_SURFACE_SELF_TEST_PASS"
    ]
    return surfaces, members, evidence, self_tests, issues


def aggregate_surface_rows(
    surfaces: list[dict[str, Any]],
    members: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    surface_decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in surfaces)
    member_costs = [
        value for value in (as_float(row.get("deconcentrated_cost_adjusted_simulated_r")) for row in members) if value is not None
    ]
    evidence_decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in evidence)
    for family, source_rows, decisions in (
        ("scorer_surface", surfaces, surface_decisions),
        ("scorer_member", members, Counter(row.get("keep_kill_redesign_implement_decision") for row in members)),
        ("nonimplement_evidence", evidence, evidence_decisions),
    ):
        rows.append(
            boundary_row(
                {
                    "expanded_market_deconcentrated_scorer_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-DECON-SCORER-AGG-{len(rows) + 1:04d}"
                    ),
                    "aggregate_family": family,
                    "row_count": len(source_rows),
                    "source_path_count": len({row.get("source_path") for row in source_rows}),
                    "symbol_family_count": len({row.get("symbol_family") for row in source_rows}),
                    "average_deconcentrated_cost_adjusted_simulated_r": rounded(average(member_costs))
                    if family == "scorer_member"
                    else None,
                    "decision_counts": dict(sorted(decisions.items())),
                }
            )
        )
    return rows


def system_surface_rows(
    surfaces: list[dict[str, Any]],
    members: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    self_tests: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    issue_rows: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        boundary_row(
            {
                "expanded_market_deconcentrated_scorer_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-DECON-SCORER-SYSTEM-0001"
                ),
                "scorer_surface_rows": len(surfaces),
                "scorer_member_rows": len(members),
                "nonimplement_evidence_rows": len(evidence),
                "self_test_rows": len(self_tests),
                "self_test_pass_rows": sum(
                    1 for row in self_tests if row.get("self_test_status") == "DECONCENTRATED_SCORER_SURFACE_SELF_TEST_PASS"
                ),
                "aggregate_rows": len(aggregate_rows),
                "issue_rows": len(issue_rows),
                "source_path_count": len({row.get("source_path") for row in members + evidence}),
                "symbol_family_count": len({row.get("symbol_family") for row in members + evidence}),
                "member_decision_counts": dict(
                    sorted(Counter(row.get("keep_kill_redesign_implement_decision") for row in members).items())
                ),
                "evidence_decision_counts": dict(
                    sorted(Counter(row.get("keep_kill_redesign_implement_decision") for row in evidence).items())
                ),
                "metadata": metadata,
            }
        )
    ]
