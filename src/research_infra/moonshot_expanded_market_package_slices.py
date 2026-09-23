"""Branch-local package slices for final-review expanded-market artifacts."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from statistics import mean
from typing import Any


EXPANDED_MARKET_PACKAGE_SLICES_SURFACE = "src/research_infra/moonshot_expanded_market_package_slices.py"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"
IMPLEMENT_DECISION = "IMPLEMENT_EXPANDED_MARKET_FINAL_REVIEW_BRANCH_LOCAL"


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
    output["expanded_market_package_slices_surface"] = EXPANDED_MARKET_PACKAGE_SLICES_SURFACE
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


def as_int(value: Any) -> int:
    if value is None or value == "" or isinstance(value, bool):
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def rounded(value: float | None, places: int = 9) -> float | None:
    return None if value is None else round(float(value), places)


def average(values: list[float]) -> float | None:
    return mean(values) if values else None


def numeric_values(rows: list[dict[str, Any]], field: str) -> list[float]:
    values = [as_float(row.get(field)) for row in rows]
    return [value for value in values if value is not None]


def package_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        normalized(row.get("symbol")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("source_component")),
        normalized(row.get("selected_side")),
    )


def package_sha(key: tuple[str, ...]) -> str:
    return hashlib.sha256(json.dumps(key, sort_keys=True).encode("utf-8")).hexdigest()


def package_expression(key: tuple[str, ...]) -> str:
    fields = ("symbol", "market_timeframe", "route_session", "horizon_id", "source_component", "selected_side")
    clauses = [f"row[{field!r}] == {value!r}" for field, value in zip(fields, key)]
    clauses.append(f"row['keep_kill_redesign_implement_decision'] == {IMPLEMENT_DECISION!r}")
    return " and ".join(clauses)


def package_matches_row(key: tuple[str, ...], row: dict[str, Any]) -> bool:
    return package_key(row) == key and row.get("keep_kill_redesign_implement_decision") == IMPLEMENT_DECISION


def evidence_by_review_row(evidence_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in evidence_rows:
        grouped[normalized(row.get("input_final_review_row_id"))].append(row)
    return grouped


def package_slice_rows(
    review_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    evidence_lookup = evidence_by_review_row(evidence_rows)
    implement_rows = [row for row in review_rows if row.get("keep_kill_redesign_implement_decision") == IMPLEMENT_DECISION]
    redesign_rows = [row for row in review_rows if row.get("keep_kill_redesign_implement_decision") != IMPLEMENT_DECISION]
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in implement_rows:
        grouped[package_key(row)].append(row)

    package_rows: list[dict[str, Any]] = []
    member_rows: list[dict[str, Any]] = []
    package_evidence_rows: list[dict[str, Any]] = []
    redesign_carry_rows: list[dict[str, Any]] = []
    control_rows: list[dict[str, Any]] = []
    self_test_rows: list[dict[str, Any]] = []
    package_id_by_key: dict[tuple[str, ...], str] = {}

    for key in sorted(grouped):
        members = sorted(grouped[key], key=lambda row: normalized(row.get("final_review_row_id")))
        package_id = f"OHLC-GTOS-EXPANDED-MARKET-PACKAGE-SLICE-{len(package_rows) + 1:06d}"
        package_id_by_key[key] = package_id
        source_paths = sorted({normalized(row.get("source_path")) for row in members})
        source_hashes = sorted({normalized(row.get("source_file_sha256")) for row in members})
        evidence_count = sum(len(evidence_lookup.get(normalized(row.get("final_review_row_id")), [])) for row in members)
        same_scope_redesign = [row for row in redesign_rows if package_key(row) == key]
        package_rows.append(
            boundary_row(
                {
                    "package_slice_row_id": package_id,
                    "package_key_sha256": package_sha(key),
                    "symbol": key[0],
                    "market_timeframe": key[1],
                    "route_session": key[2],
                    "horizon_id": key[3],
                    "source_component": key[4],
                    "selected_side": key[5],
                    "branch_local_package_expression": package_expression(key),
                    "member_rows": len(members),
                    "package_evidence_rows": evidence_count,
                    "source_path_count": len(source_paths),
                    "source_file_sha256_count": len(source_hashes),
                    "source_paths": source_paths,
                    "source_file_sha256_values": source_hashes,
                    "average_selected_intrabar_cost_adjusted_simulated_r": rounded(
                        average(numeric_values(members, "row_average_selected_intrabar_cost_adjusted_simulated_r"))
                    ),
                    "average_recomputed_selected_intrabar_cost_adjusted_simulated_r": rounded(
                        average(numeric_values(members, "recomputed_average_selected_intrabar_cost_adjusted_simulated_r"))
                    ),
                    "average_final_review_score": rounded(average(numeric_values(members, "final_review_score"))),
                    "min_final_review_score": rounded(min(numeric_values(members, "final_review_score"))),
                    "max_final_review_score": rounded(max(numeric_values(members, "final_review_score"))),
                    "average_max_capacity_utilization": rounded(
                        average(numeric_values(members, "max_capacity_utilization"))
                    ),
                    "evidence_effective_n_sum": rounded(
                        sum(as_float(row.get("evidence_effective_n_sum")) or 0.0 for row in members)
                    ),
                    "same_scope_redesign_rows": len(same_scope_redesign),
                    "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_PACKAGE_SLICE",
                    "follow_inverse_default_off_avoid_class": "follow",
                }
            )
        )
        positive_matches = sum(1 for row in members if package_matches_row(key, row))
        negative_matches = sum(1 for row in redesign_rows if package_matches_row(key, row))
        self_test_rows.append(
            boundary_row(
                {
                    "package_self_test_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-PACKAGE-SELF-TEST-{len(self_test_rows) + 1:06d}"
                    ),
                    "input_package_slice_row_id": package_id,
                    "positive_member_rows": len(members),
                    "positive_package_match_rows": positive_matches,
                    "negative_redesign_rows": len(redesign_rows),
                    "negative_package_match_rows": negative_matches,
                    "self_test_status": "PACKAGE_SLICE_SELF_TEST_PASS"
                    if positive_matches == len(members) and negative_matches == 0
                    else "PACKAGE_SLICE_SELF_TEST_REPAIR",
                    "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_PACKAGE_SELF_TEST"
                    if positive_matches == len(members) and negative_matches == 0
                    else "REDESIGN_EXPANDED_MARKET_PACKAGE_SELF_TEST",
                }
            )
        )
        control_rows.append(
            boundary_row(
                {
                    "package_control_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-PACKAGE-CONTROL-{len(control_rows) + 1:06d}"
                    ),
                    "input_package_slice_row_id": package_id,
                    "same_scope_redesign_rows": len(same_scope_redesign),
                    "package_expression_rejected_redesign_rows": len(same_scope_redesign) - negative_matches,
                    "package_expression_leaked_redesign_rows": negative_matches,
                    "control_status": "PACKAGE_CONTROL_PASS" if negative_matches == 0 else "PACKAGE_CONTROL_REPAIR",
                    "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_PACKAGE_CONTROL"
                    if negative_matches == 0
                    else "REDESIGN_EXPANDED_MARKET_PACKAGE_CONTROL",
                }
            )
        )
        for member in members:
            member_rows.append(
                boundary_row(
                    {
                        "package_member_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-PACKAGE-MEMBER-{len(member_rows) + 1:07d}"
                        ),
                        "input_package_slice_row_id": package_id,
                        "input_final_review_row_id": member.get("final_review_row_id"),
                        "input_deconcentration_row_id": member.get("input_deconcentration_row_id"),
                        "symbol": member.get("symbol"),
                        "source_symbol": member.get("source_symbol"),
                        "market_timeframe": member.get("market_timeframe"),
                        "route_session": member.get("route_session"),
                        "horizon_id": member.get("horizon_id"),
                        "source_component": member.get("source_component"),
                        "source_path": member.get("source_path"),
                        "source_file_sha256": member.get("source_file_sha256"),
                        "selected_side": member.get("selected_side"),
                        "artifact_function_name": member.get("artifact_function_name"),
                        "artifact_scope_sha256": member.get("artifact_scope_sha256"),
                        "final_review_score": member.get("final_review_score"),
                        "final_review_evidence_rows": member.get("final_review_evidence_rows"),
                        "row_average_selected_intrabar_cost_adjusted_simulated_r": member.get(
                            "row_average_selected_intrabar_cost_adjusted_simulated_r"
                        ),
                        "max_capacity_utilization": member.get("max_capacity_utilization"),
                        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_PACKAGE_MEMBER",
                        "follow_inverse_default_off_avoid_class": "follow",
                    }
                )
            )

    for row in sorted(redesign_rows, key=lambda item: normalized(item.get("final_review_row_id"))):
        redesign_carry_rows.append(
            boundary_row(
                {
                    "package_redesign_carry_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-PACKAGE-REDESIGN-{len(redesign_carry_rows) + 1:06d}"
                    ),
                    "input_final_review_row_id": row.get("final_review_row_id"),
                    "input_deconcentration_row_id": row.get("input_deconcentration_row_id"),
                    "symbol": row.get("symbol"),
                    "source_symbol": row.get("source_symbol"),
                    "market_timeframe": row.get("market_timeframe"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "source_path": row.get("source_path"),
                    "source_file_sha256": row.get("source_file_sha256"),
                    "selected_side": row.get("selected_side"),
                    "capacity_blocking_dimensions": row.get("capacity_blocking_dimensions") or [],
                    "final_review_score": row.get("final_review_score"),
                    "final_review_evidence_rows": row.get("final_review_evidence_rows"),
                    "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_PACKAGE_CAPACITY_CARRY",
                    "follow_inverse_default_off_avoid_class": "redesign",
                }
            )
        )

    for row in evidence_rows:
        review_id = normalized(row.get("input_final_review_row_id"))
        review_row = next((candidate for candidate in review_rows if normalized(candidate.get("final_review_row_id")) == review_id), {})
        key = package_key(review_row)
        package_id = package_id_by_key.get(key, "")
        is_implement = review_row.get("keep_kill_redesign_implement_decision") == IMPLEMENT_DECISION
        package_evidence_rows.append(
            boundary_row(
                {
                    "package_evidence_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-PACKAGE-EVIDENCE-{len(package_evidence_rows) + 1:08d}"
                    ),
                    "input_package_slice_row_id": package_id if is_implement else None,
                    "input_final_review_row_id": row.get("input_final_review_row_id"),
                    "input_final_review_evidence_row_id": row.get("final_review_evidence_row_id"),
                    "symbol": row.get("symbol"),
                    "source_symbol": row.get("source_symbol"),
                    "market_timeframe": row.get("market_timeframe"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "source_path": row.get("source_path"),
                    "source_file_sha256": row.get("source_file_sha256"),
                    "selected_side": row.get("selected_side"),
                    "selected_intrabar_cost_adjusted_simulated_r": row.get(
                        "selected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "selected_minus_rejected_intrabar_cost_adjusted_r": row.get(
                        "selected_minus_rejected_intrabar_cost_adjusted_r"
                    ),
                    "effective_n": row.get("effective_n"),
                    "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_PACKAGE_EVIDENCE"
                    if is_implement
                    else "REDESIGN_EXPANDED_MARKET_PACKAGE_EVIDENCE_PRESERVED",
                }
            )
        )

    return package_rows, member_rows, package_evidence_rows, redesign_carry_rows, control_rows, self_test_rows


def aggregate_package_rows(package_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in package_rows:
        grouped[(normalized(row.get("symbol")), normalized(row.get("source_component")), normalized(row.get("selected_side")))].append(row)
    output: list[dict[str, Any]] = []
    total_members = sum(as_int(row.get("member_rows")) for row in package_rows) or 1
    for key in sorted(grouped):
        members = grouped[key]
        member_count = sum(as_int(row.get("member_rows")) for row in members)
        output.append(
            boundary_row(
                {
                    "package_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-PACKAGE-AGG-{len(output) + 1:06d}"
                    ),
                    "symbol": key[0],
                    "source_component": key[1],
                    "selected_side": key[2],
                    "package_slice_rows": len(members),
                    "package_member_rows": member_count,
                    "package_evidence_rows": sum(as_int(row.get("package_evidence_rows")) for row in members),
                    "average_selected_intrabar_cost_adjusted_simulated_r": rounded(
                        average(numeric_values(members, "average_selected_intrabar_cost_adjusted_simulated_r"))
                    ),
                    "average_final_review_score": rounded(average(numeric_values(members, "average_final_review_score"))),
                    "max_capacity_utilization": rounded(max(numeric_values(members, "average_max_capacity_utilization"))),
                    "concentration_share_of_package_members": rounded(member_count / total_members),
                    "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_PACKAGE_AGGREGATE",
                }
            )
        )
    return output


def system_package_rows(
    package_rows: list[dict[str, Any]],
    member_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    redesign_rows: list[dict[str, Any]],
    control_rows: list[dict[str, Any]],
    self_test_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    input_review_rows: int,
    input_evidence_rows: int,
) -> list[dict[str, Any]]:
    return [
        boundary_row(
            {
                "package_system_row_id": "OHLC-GTOS-EXPANDED-MARKET-PACKAGE-SYSTEM-0001",
                "input_final_review_rows": input_review_rows,
                "input_final_review_evidence_rows": input_evidence_rows,
                "package_slice_rows": len(package_rows),
                "package_member_rows": len(member_rows),
                "package_evidence_rows": len(evidence_rows),
                "package_redesign_carry_rows": len(redesign_rows),
                "package_control_rows": len(control_rows),
                "package_self_test_rows": len(self_test_rows),
                "aggregate_rows": len(aggregate_rows),
                "self_test_pass_rows": sum(
                    1 for row in self_test_rows if row.get("self_test_status") == "PACKAGE_SLICE_SELF_TEST_PASS"
                ),
                "control_pass_rows": sum(1 for row in control_rows if row.get("control_status") == "PACKAGE_CONTROL_PASS"),
                "decision_counts": dict(
                    sorted(
                        Counter(
                            [row.get("keep_kill_redesign_implement_decision") for row in package_rows]
                            + [row.get("keep_kill_redesign_implement_decision") for row in redesign_rows]
                        ).items()
                    )
                ),
            }
        )
    ]
