"""Execute branch-local source-expansion action packs against candidate rows."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any

from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACK_EXECUTION = (
    "src/research_infra/moonshot_expanded_market_source_expansion_action_pack_execution.py"
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
    output["expanded_market_source_expansion_action_pack_execution_surface"] = (
        EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACK_EXECUTION
    )
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def stable_sha256(payload: dict[str, Any]) -> str:
    import json

    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def candidate_match_contract(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol_family": row.get("symbol_family"),
        "symbol": row.get("symbol"),
        "source_symbol": row.get("source_symbol"),
        "market_timeframe": row.get("market_timeframe"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "side": row.get("side"),
        "source_path_sha256": row.get("source_path_sha256"),
        "source_file_sha256": row.get("source_file_sha256"),
        "entry_reference": row.get("entry_reference"),
    }


def contract_matches(pack: dict[str, Any], candidate: dict[str, Any]) -> bool:
    pack_contract = pack.get("branch_local_action_pack_match_contract") or {}
    candidate_contract = candidate_match_contract(candidate)
    return all(
        normalized(pack_contract.get(key)) == normalized(candidate_contract.get(key))
        for key in pack_contract
    )


def pack_execution_summary(
    pack: dict[str, Any],
    application_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    matched = [row for row in application_rows if contract_matches(pack, row)]
    pack_decision = normalized(pack.get("keep_kill_redesign_implement_decision"))
    pack_class = normalized(pack.get("follow_inverse_default_off_avoid_class"))
    decision_leaks = [
        row
        for row in matched
        if normalized(row.get("keep_kill_redesign_implement_decision")) != pack_decision
    ]
    class_leaks = [
        row
        for row in matched
        if normalized(row.get("follow_inverse_default_off_avoid_class")) != pack_class
    ]
    cost_mismatches = [
        row
        for row in matched
        if as_float(row.get("cost_adjusted_simulated_r"))
        != as_float(pack.get("cost_adjusted_simulated_r"))
    ]
    expected_id = normalized(pack.get("input_source_expansion_action_application_row_id"))
    matched_ids = [
        normalized(row.get("expanded_market_source_expansion_action_application_row_id"))
        for row in matched
    ]
    return {
        "candidate_rows_scanned": len(application_rows),
        "matched_application_row_ids": matched_ids,
        "match_count": len(matched),
        "negative_mismatch_count": len(application_rows) - len(matched),
        "expected_application_row_matched": expected_id in matched_ids,
        "decision_leak_count": len(decision_leaks),
        "class_leak_count": len(class_leaks),
        "cost_mismatch_count": len(cost_mismatches),
        "execution_pass": (
            bool(matched)
            and expected_id in matched_ids
            and not decision_leaks
            and not class_leaks
            and not cost_mismatches
        ),
    }


def pack_execution_row(
    pack: dict[str, Any],
    application_rows: list[dict[str, Any]],
    sequence: int,
) -> dict[str, Any]:
    summary = pack_execution_summary(pack, application_rows)
    expression = {
        "pack_row_id": pack.get("expanded_market_source_expansion_action_pack_row_id"),
        "match_contract": pack.get("branch_local_action_pack_match_contract"),
        "emit_contract": pack.get("branch_local_action_pack_emit_contract"),
        "matched_application_row_ids": summary["matched_application_row_ids"],
    }
    return boundary_row(
        {
            "expanded_market_source_expansion_action_pack_execution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ACTION-PACK-EXEC-{sequence:07d}"
            ),
            "input_action_pack_row_id": pack.get(
                "expanded_market_source_expansion_action_pack_row_id"
            ),
            "input_source_expansion_action_application_row_id": pack.get(
                "input_source_expansion_action_application_row_id"
            ),
            "action_pack_execution_status": "ACTION_PACK_EXECUTION_PASS"
            if summary["execution_pass"]
            else "ACTION_PACK_EXECUTION_REPAIR_REQUIRED",
            "action_pack_kind": pack.get("action_pack_kind"),
            "symbol_family": pack.get("symbol_family"),
            "symbol": pack.get("symbol"),
            "source_symbol": pack.get("source_symbol"),
            "market_timeframe": pack.get("market_timeframe"),
            "route_session": pack.get("route_session"),
            "horizon_id": pack.get("horizon_id"),
            "side": pack.get("side"),
            "source_path": pack.get("source_path"),
            "source_path_sha256": pack.get("source_path_sha256"),
            "source_file_sha256": pack.get("source_file_sha256"),
            "entry_reference": pack.get("entry_reference"),
            "proxy_denominator_price": pack.get("proxy_denominator_price"),
            "path_order_result": pack.get("path_order_result"),
            "fill_status": pack.get("fill_status"),
            "gross_simulated_r": pack.get("gross_simulated_r"),
            "cost_adjusted_simulated_r": pack.get("cost_adjusted_simulated_r"),
            "stress_simulated_r": pack.get("stress_simulated_r"),
            "effective_n": pack.get("effective_n"),
            "concentration_top_month_share": pack.get("concentration_top_month_share"),
            **summary,
            "branch_local_action_pack_execution_expression": expression,
            "branch_local_action_pack_execution_expression_sha256": stable_sha256(expression),
            "follow_inverse_default_off_avoid_class": pack.get(
                "follow_inverse_default_off_avoid_class"
            ),
            "keep_kill_redesign_implement_decision": pack.get(
                "keep_kill_redesign_implement_decision"
            ),
        }
    )


def pack_match_rows(
    pack: dict[str, Any],
    execution: dict[str, Any],
    application_rows_by_id: dict[str, dict[str, Any]],
    start_sequence: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for offset, application_id in enumerate(execution.get("matched_application_row_ids") or []):
        application = application_rows_by_id.get(application_id) or {}
        rows.append(
            boundary_row(
                {
                    "expanded_market_source_expansion_action_pack_match_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ACTION-PACK-MATCH-{start_sequence + offset:07d}"
                    ),
                    "input_action_pack_execution_row_id": execution.get(
                        "expanded_market_source_expansion_action_pack_execution_row_id"
                    ),
                    "input_action_pack_row_id": pack.get(
                        "expanded_market_source_expansion_action_pack_row_id"
                    ),
                    "input_source_expansion_action_application_row_id": application_id,
                    "match_status": "ACTION_PACK_CONTRACT_MATCH",
                    "symbol_family": application.get("symbol_family"),
                    "symbol": application.get("symbol"),
                    "source_symbol": application.get("source_symbol"),
                    "market_timeframe": application.get("market_timeframe"),
                    "route_session": application.get("route_session"),
                    "horizon_id": application.get("horizon_id"),
                    "side": application.get("side"),
                    "source_path": application.get("source_path"),
                    "source_path_sha256": application.get("source_path_sha256"),
                    "source_file_sha256": application.get("source_file_sha256"),
                    "gross_simulated_r": application.get("gross_simulated_r"),
                    "cost_adjusted_simulated_r": application.get("cost_adjusted_simulated_r"),
                    "stress_simulated_r": application.get("stress_simulated_r"),
                    "follow_inverse_default_off_avoid_class": application.get(
                        "follow_inverse_default_off_avoid_class"
                    ),
                    "keep_kill_redesign_implement_decision": application.get(
                        "keep_kill_redesign_implement_decision"
                    ),
                }
            )
        )
    return rows


def work_execution_row(row: dict[str, Any], sequence: int) -> dict[str, Any]:
    expression = {
        "work_row_id": row.get("expanded_market_source_expansion_action_pack_work_row_id"),
        "work_status": row.get("work_status"),
        "missing_work_fields": row.get("missing_work_fields") or [],
    }
    return boundary_row(
        {
            "expanded_market_source_expansion_action_pack_work_execution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ACTION-PACK-WORK-EXEC-{sequence:07d}"
            ),
            "input_action_pack_work_row_id": row.get(
                "expanded_market_source_expansion_action_pack_work_row_id"
            ),
            "input_source_expansion_action_application_row_id": row.get(
                "input_source_expansion_action_application_row_id"
            ),
            "work_execution_status": "ACTION_PACK_WORK_EXECUTION_PRESERVED",
            "work_status": row.get("work_status"),
            "symbol_family": row.get("symbol_family"),
            "symbol": row.get("symbol"),
            "source_symbol": row.get("source_symbol"),
            "market_timeframe": row.get("market_timeframe"),
            "route_session": row.get("route_session"),
            "horizon_id": row.get("horizon_id"),
            "side": row.get("side"),
            "source_path": row.get("source_path"),
            "source_path_sha256": row.get("source_path_sha256"),
            "source_file_sha256": row.get("source_file_sha256"),
            "gross_simulated_r": row.get("gross_simulated_r"),
            "cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
            "stress_simulated_r": row.get("stress_simulated_r"),
            "effective_n": row.get("effective_n"),
            "missing_work_fields": row.get("missing_work_fields") or [],
            "branch_local_action_pack_work_execution_expression": expression,
            "branch_local_action_pack_work_execution_expression_sha256": stable_sha256(expression),
            "follow_inverse_default_off_avoid_class": row.get(
                "follow_inverse_default_off_avoid_class"
            ),
            "keep_kill_redesign_implement_decision": row.get(
                "keep_kill_redesign_implement_decision"
            ),
        }
    )


def aggregate_pack_execution_rows(
    execution_rows: list[dict[str, Any]],
    work_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for kind, rows in (("pack_execution", execution_rows), ("work_execution", work_rows)):
        for row in rows:
            key = (
                kind,
                normalized(row.get("symbol_family")),
                normalized(row.get("symbol")),
                normalized(row.get("market_timeframe")),
                normalized(row.get("route_session")),
                normalized(row.get("horizon_id")),
                normalized(row.get("side")),
                normalized(row.get("follow_inverse_default_off_avoid_class")),
            )
            grouped.setdefault(key, []).append(row)
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        values = [
            as_float(row.get("cost_adjusted_simulated_r"))
            for row in members
            if as_float(row.get("cost_adjusted_simulated_r")) is not None
        ]
        decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in members)
        output.append(
            boundary_row(
                {
                    "expanded_market_source_expansion_action_pack_execution_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ACTION-PACK-EXEC-AGG-{len(output) + 1:07d}"
                    ),
                    "row_kind": key[0],
                    "symbol_family": key[1],
                    "symbol": key[2],
                    "market_timeframe": key[3],
                    "route_session": key[4],
                    "horizon_id": key[5],
                    "side": key[6],
                    "follow_inverse_default_off_avoid_class": key[7],
                    "row_count": len(members),
                    "rows_with_simulated_r": len(values),
                    "average_cost_adjusted_simulated_r": rounded(
                        sum(values) / len(values) if values else None
                    ),
                    "effective_n_sum": sum(int(row.get("effective_n") or 0) for row in members),
                    "decision_counts": dict(sorted(decisions.items())),
                    "keep_kill_redesign_implement_decision": decisions.most_common(1)[0][0],
                }
            )
        )
    return output
