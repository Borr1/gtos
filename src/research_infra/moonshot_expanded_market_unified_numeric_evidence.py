"""Numeric evidence joins for expanded-market unified final decisions."""

from __future__ import annotations

import os
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


EXPANDED_MARKET_UNIFIED_NUMERIC_EVIDENCE_SURFACE = (
    "src/research_infra/moonshot_expanded_market_unified_numeric_evidence.py"
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
    output["expanded_market_unified_numeric_evidence_surface"] = (
        EXPANDED_MARKET_UNIFIED_NUMERIC_EVIDENCE_SURFACE
    )
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


def weighted_average(rows: list[dict[str, Any]], value_field: str, weight_field: str) -> float | None:
    numerator = 0.0
    denominator = 0.0
    for row in rows:
        value = as_float(row.get(value_field))
        weight = as_float(row.get(weight_field))
        if value is None or weight is None or weight <= 0:
            continue
        numerator += value * weight
        denominator += weight
    return None if denominator == 0 else numerator / denominator


def average(values: list[float]) -> float | None:
    return mean(values) if values else None


def sha_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def long_path(path: Path) -> str:
    text = str(path)
    if os.name == "nt" and len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def file_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    hasher = hashlib.sha256()
    with open(long_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def profile_key(row: dict[str, Any], side_field: str, component_field: str = "source_component") -> tuple[str, ...]:
    return (
        normalized(row.get("symbol")),
        normalized(row.get("source_symbol")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get(component_field)),
        normalized(row.get("source_path")),
        normalized(row.get("source_file_sha256")),
        normalized(row.get(side_field)),
    )


def performance_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        normalized(row.get("symbol")),
        normalized(row.get("source_symbol")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("seed_source_component")),
        normalized(row.get("source_path")),
        normalized(row.get("source_file_sha256")),
        normalized(row.get("side")),
    )


def intrabar_key(row: dict[str, Any]) -> tuple[str, ...]:
    return profile_key(row, "side")


def source_access_rows(
    source_rows: list[dict[str, Any]],
    repo_root: Path,
) -> list[dict[str, Any]]:
    seen: dict[tuple[str, str], dict[str, Any]] = {}
    for row in source_rows:
        key = (normalized(row.get("source_path")), normalized(row.get("source_file_sha256")))
        if not key[0]:
            continue
        if key not in seen:
            seen[key] = row

    output: list[dict[str, Any]] = []
    for index, ((source_path, expected_hash), row) in enumerate(sorted(seen.items()), start=1):
        full_path = repo_root / source_path
        actual_hash = file_sha256(full_path)
        exists = full_path.exists() and full_path.is_file()
        hash_match = bool(actual_hash and expected_hash and actual_hash == expected_hash)
        output.append(
            boundary_row(
                {
                    "unified_numeric_source_access_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-NUMERIC-SOURCE-{index:06d}"
                    ),
                    "symbol": row.get("symbol"),
                    "source_symbol": row.get("source_symbol"),
                    "market_timeframe": row.get("market_timeframe"),
                    "source_path": source_path,
                    "source_file_sha256": expected_hash,
                    "actual_source_file_sha256": actual_hash,
                    "source_file_exists": exists,
                    "source_hash_match": hash_match,
                    "source_access_status": (
                        "SOURCE_PATH_HASH_CONFIRMED" if exists and hash_match else "SOURCE_PATH_OR_HASH_MISMATCH"
                    ),
                    "keep_kill_redesign_implement_decision": (
                        "IMPLEMENT_EXPANDED_MARKET_UNIFIED_NUMERIC_SOURCE_CONFIRMED"
                        if exists and hash_match
                        else "REDESIGN_EXPANDED_MARKET_UNIFIED_NUMERIC_SOURCE_ACCESS"
                    ),
                    "follow_inverse_default_off_avoid_class": (
                        "follow" if exists and hash_match else "redesign"
                    ),
                }
            )
        )
    return output


def numeric_row(
    source_row: dict[str, Any],
    performance_row: dict[str, Any] | None,
    intrabar_row: dict[str, Any] | None,
    output_id: str,
    input_id_field: str,
    input_id_value: str,
    numeric_row_kind: str,
) -> dict[str, Any]:
    missing_fields: list[str] = []
    if performance_row is None:
        missing_fields.append("expanded_market_proxy_r_performance_row")
    if intrabar_row is None:
        missing_fields.append("expanded_market_intrabar_geometry_row")

    perf = performance_row or {}
    intra = intrabar_row or {}
    effective_n = as_int(intra.get("effective_n") or perf.get("effective_n"))
    fill_status = intra.get("fill_status") or perf.get("fill_status")
    no_fill_count = effective_n if normalized(fill_status).startswith("NO_") else 0
    status = "UNIFIED_NUMERIC_EVIDENCE_REPLAYED" if not missing_fields else "UNIFIED_NUMERIC_EVIDENCE_INCOMPLETE"
    base_decision = source_row.get("keep_kill_redesign_implement_decision")
    terminal = numeric_row_kind == "unified_terminal_redesign"
    decision = (
        "REDESIGN_EXPANDED_MARKET_UNIFIED_NUMERIC_TERMINAL"
        if terminal
        else (
            "IMPLEMENT_EXPANDED_MARKET_UNIFIED_NUMERIC_EVIDENCE"
            if not missing_fields
            else "REDESIGN_EXPANDED_MARKET_UNIFIED_NUMERIC_REPLAY_FIELD"
        )
    )
    output = {
        "unified_numeric_evidence_row_id": output_id,
        input_id_field: input_id_value,
        "input_unified_final_decision_row_id": source_row.get("input_unified_final_decision_row_id"),
        "input_expanded_market_performance_row_id": perf.get("expanded_market_performance_row_id"),
        "input_intrabar_geometry_row_id": intra.get("intrabar_geometry_row_id"),
        "numeric_row_kind": numeric_row_kind,
        "symbol": source_row.get("symbol"),
        "source_symbol": source_row.get("source_symbol"),
        "market_timeframe": source_row.get("market_timeframe"),
        "route_session": source_row.get("route_session"),
        "horizon_id": source_row.get("horizon_id"),
        "source_component": source_row.get("source_component"),
        "source_path": source_row.get("source_path"),
        "source_file_sha256": source_row.get("source_file_sha256"),
        "selected_side": source_row.get("selected_side"),
        "side": source_row.get("selected_side"),
        "branch_family": source_row.get("source_component"),
        "entry_reference": intra.get("entry_reference") or perf.get("entry_reference"),
        "entry_reference_time": intra.get("entry_reference_time") or perf.get("entry_reference_time"),
        "proxy_entry_price": intra.get("proxy_entry_price") or perf.get("proxy_entry_price"),
        "proxy_stop_price": intra.get("proxy_stop_price") or perf.get("proxy_stop_price"),
        "proxy_target_price": intra.get("proxy_target_price") or perf.get("proxy_target_price"),
        "proxy_denominator_price": intra.get("proxy_denominator_price") or perf.get("proxy_denominator_price"),
        "path_order_result": intra.get("path_order_result") or perf.get("path_order_result"),
        "fill_status": fill_status,
        "gross_simulated_r": rounded(as_float(intra.get("gross_simulated_r") or perf.get("gross_simulated_r"))),
        "cost_adjusted_simulated_r": rounded(
            as_float(intra.get("cost_adjusted_simulated_r") or perf.get("cost_adjusted_simulated_r"))
        ),
        "horizon_close_cost_adjusted_simulated_r": rounded(
            as_float(intra.get("horizon_close_proxy_cost_adjusted_simulated_r") or perf.get("cost_adjusted_simulated_r"))
        ),
        "stress_simulated_r": rounded(as_float(intra.get("stress_simulated_r") or perf.get("stress_simulated_r"))),
        "expectancy": rounded(
            as_float(intra.get("cost_adjusted_simulated_r") or perf.get("cost_adjusted_simulated_r"))
        ),
        "average_win": rounded(as_float(intra.get("average_win"))),
        "average_loss": rounded(as_float(intra.get("average_loss"))),
        "win_count": as_int(intra.get("win_count") or perf.get("win_count")),
        "loss_count": as_int(intra.get("loss_count") or perf.get("loss_count")),
        "flat_count": as_int(intra.get("zero_count") or perf.get("zero_count")),
        "zero_count": as_int(intra.get("zero_count") or perf.get("zero_count")),
        "no_fill_count": no_fill_count,
        "target_first_count": as_int(intra.get("target_first_count") or perf.get("target_first_count")),
        "stop_first_count": as_int(intra.get("stop_first_count") or perf.get("stop_first_count")),
        "neither_count": as_int(intra.get("neither_count") or perf.get("neither_count")),
        "ambiguous_count": as_int(intra.get("ambiguous_count") or perf.get("ambiguous_count")),
        "duplicate_row_count": as_int(intra.get("duplicate_row_count") or perf.get("duplicate_row_count")),
        "effective_n": effective_n,
        "effective_n_after_duplicate_collapse": as_int(
            intra.get("effective_n_after_duplicate_collapse") or perf.get("effective_n_after_duplicate_collapse")
        ),
        "concentration_top_month_share": rounded(
            as_float(intra.get("concentration_top_month_share") or perf.get("concentration_top_month_share"))
        ),
        "average_first_touch_bars": rounded(as_float(intra.get("average_first_touch_bars"))),
        "source_row_cost_adjusted_simulated_r": rounded(
            as_float(source_row.get("selected_intrabar_cost_adjusted_simulated_r"))
        ),
        "source_row_effective_n": as_int(source_row.get("effective_n")),
        "missing_simulated_fields": missing_fields,
        "numeric_evidence_status": status,
        "source_keep_kill_redesign_implement_decision": base_decision,
        "keep_kill_redesign_implement_decision": decision,
        "follow_inverse_default_off_avoid_class": (
            "redesign" if terminal else source_row.get("follow_inverse_default_off_avoid_class")
        ),
    }
    output["numeric_evidence_payload_sha256"] = sha_payload(
        {
            "kind": numeric_row_kind,
            "input_id": input_id_value,
            "performance_id": output.get("input_expanded_market_performance_row_id"),
            "intrabar_id": output.get("input_intrabar_geometry_row_id"),
        }
    )
    return boundary_row(output)


def unified_numeric_evidence_rows(
    decision_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    terminal_rows: list[dict[str, Any]],
    performance_rows: list[dict[str, Any]],
    intrabar_rows: list[dict[str, Any]],
    repo_root: Path,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    performance_by_key = {performance_key(row): row for row in performance_rows}
    intrabar_by_key = {intrabar_key(row): row for row in intrabar_rows}
    source_access = source_access_rows(evidence_rows + terminal_rows, repo_root)
    source_status = {
        (row.get("source_path"), row.get("source_file_sha256")): row.get("source_access_status")
        for row in source_access
    }

    evidence_output: list[dict[str, Any]] = []
    terminal_output: list[dict[str, Any]] = []
    issue_rows: list[dict[str, Any]] = []

    for row in sorted(evidence_rows, key=lambda item: normalized(item.get("unified_final_evidence_row_id"))):
        key = profile_key(row, "selected_side")
        output = numeric_row(
            row,
            performance_by_key.get(key),
            intrabar_by_key.get(key),
            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-NUMERIC-EVIDENCE-{len(evidence_output) + 1:08d}",
            "input_unified_final_evidence_row_id",
            normalized(row.get("unified_final_evidence_row_id")),
            "unified_final_evidence",
        )
        output["source_access_status"] = source_status.get(
            (row.get("source_path"), row.get("source_file_sha256")),
            "SOURCE_PATH_ACCESS_NOT_CHECKED",
        )
        evidence_output.append(output)
        if output["missing_simulated_fields"]:
            issue_rows.append(
                boundary_row(
                    {
                        "unified_numeric_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-NUMERIC-ISSUE-{len(issue_rows) + 1:06d}"
                        ),
                        "input_unified_final_evidence_row_id": row.get("unified_final_evidence_row_id"),
                        "missing_simulated_fields": output["missing_simulated_fields"],
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_UNIFIED_NUMERIC_REPLAY_FIELD"
                        ),
                        "follow_inverse_default_off_avoid_class": "redesign",
                    }
                )
            )

    for row in sorted(terminal_rows, key=lambda item: normalized(item.get("unified_final_terminal_redesign_row_id"))):
        key = profile_key(row, "selected_side")
        output = numeric_row(
            row,
            performance_by_key.get(key),
            intrabar_by_key.get(key),
            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-NUMERIC-TERMINAL-{len(terminal_output) + 1:08d}",
            "input_unified_final_terminal_redesign_row_id",
            normalized(row.get("unified_final_terminal_redesign_row_id")),
            "unified_terminal_redesign",
        )
        output["source_access_status"] = source_status.get(
            (row.get("source_path"), row.get("source_file_sha256")),
            "SOURCE_PATH_ACCESS_NOT_CHECKED",
        )
        terminal_output.append(output)
        if output["missing_simulated_fields"]:
            issue_rows.append(
                boundary_row(
                    {
                        "unified_numeric_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-NUMERIC-ISSUE-{len(issue_rows) + 1:06d}"
                        ),
                        "input_unified_final_terminal_redesign_row_id": row.get(
                            "unified_final_terminal_redesign_row_id"
                        ),
                        "missing_simulated_fields": output["missing_simulated_fields"],
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_UNIFIED_NUMERIC_REPLAY_FIELD"
                        ),
                        "follow_inverse_default_off_avoid_class": "redesign",
                    }
                )
            )

    decision_output = decision_numeric_rows(decision_rows, evidence_output)
    aggregate_output = aggregate_numeric_rows(evidence_output + terminal_output)
    return evidence_output, terminal_output, decision_output, source_access, aggregate_output, issue_rows


def decision_numeric_rows(
    decision_rows: list[dict[str, Any]],
    evidence_output_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    evidence_by_decision: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in evidence_output_rows:
        evidence_by_decision[normalized(row.get("input_unified_final_decision_row_id"))].append(row)

    output: list[dict[str, Any]] = []
    for index, row in enumerate(
        sorted(decision_rows, key=lambda item: normalized(item.get("unified_final_decision_row_id"))), start=1
    ):
        decision_id = normalized(row.get("unified_final_decision_row_id"))
        members = evidence_by_decision.get(decision_id, [])
        output.append(
            boundary_row(
                {
                    "unified_numeric_decision_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-NUMERIC-DECISION-{index:06d}"
                    ),
                    "input_unified_final_decision_row_id": decision_id,
                    "decision_origin": row.get("decision_origin"),
                    "symbol": row.get("symbol"),
                    "market_timeframe": row.get("market_timeframe"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "selected_side": row.get("selected_side"),
                    "numeric_evidence_rows": len(members),
                    "source_path_count": len({member.get("source_path") for member in members}),
                    "source_hash_count": len({member.get("source_file_sha256") for member in members}),
                    **performance_rollup(members),
                    "unified_numeric_decision_status": (
                        "UNIFIED_NUMERIC_DECISION_REPLAYED"
                        if members and all(not member.get("missing_simulated_fields") for member in members)
                        else "UNIFIED_NUMERIC_DECISION_INCOMPLETE"
                    ),
                    "keep_kill_redesign_implement_decision": (
                        "IMPLEMENT_EXPANDED_MARKET_UNIFIED_NUMERIC_DECISION"
                        if members and all(not member.get("missing_simulated_fields") for member in members)
                        else "REDESIGN_EXPANDED_MARKET_UNIFIED_NUMERIC_DECISION"
                    ),
                    "follow_inverse_default_off_avoid_class": row.get("follow_inverse_default_off_avoid_class"),
                }
            )
        )
    return output


def performance_rollup(rows: list[dict[str, Any]]) -> dict[str, Any]:
    path_count = sum(
        as_int(row.get("target_first_count"))
        + as_int(row.get("stop_first_count"))
        + as_int(row.get("neither_count"))
        + as_int(row.get("ambiguous_count"))
        for row in rows
    )
    effective_n_sum = sum(as_int(row.get("effective_n")) for row in rows)
    win_count_sum = sum(as_int(row.get("win_count")) for row in rows)
    loss_count_sum = sum(as_int(row.get("loss_count")) for row in rows)
    return {
        "gross_simulated_r": rounded(weighted_average(rows, "gross_simulated_r", "effective_n")),
        "cost_adjusted_simulated_r": rounded(weighted_average(rows, "cost_adjusted_simulated_r", "effective_n")),
        "stress_simulated_r": rounded(weighted_average(rows, "stress_simulated_r", "effective_n")),
        "expectancy": rounded(weighted_average(rows, "expectancy", "effective_n")),
        "average_win": rounded(weighted_average(rows, "average_win", "win_count")),
        "average_loss": rounded(weighted_average(rows, "average_loss", "loss_count")),
        "win_count": win_count_sum,
        "loss_count": loss_count_sum,
        "flat_count": sum(as_int(row.get("flat_count")) for row in rows),
        "zero_count": sum(as_int(row.get("zero_count")) for row in rows),
        "no_fill_count": sum(as_int(row.get("no_fill_count")) for row in rows),
        "target_first_count": sum(as_int(row.get("target_first_count")) for row in rows),
        "stop_first_count": sum(as_int(row.get("stop_first_count")) for row in rows),
        "neither_count": sum(as_int(row.get("neither_count")) for row in rows),
        "ambiguous_count": sum(as_int(row.get("ambiguous_count")) for row in rows),
        "duplicate_row_count": sum(as_int(row.get("duplicate_row_count")) for row in rows),
        "effective_n": effective_n_sum,
        "effective_n_after_duplicate_collapse": sum(
            as_int(row.get("effective_n_after_duplicate_collapse")) for row in rows
        ),
        "concentration_top_month_share": rounded(max([as_float(row.get("concentration_top_month_share")) or 0 for row in rows], default=0.0)),
        "target_first_share": rounded(
            None if path_count == 0 else sum(as_int(row.get("target_first_count")) for row in rows) / path_count
        ),
        "stop_first_share": rounded(
            None if path_count == 0 else sum(as_int(row.get("stop_first_count")) for row in rows) / path_count
        ),
        "ambiguous_share": rounded(
            None if path_count == 0 else sum(as_int(row.get("ambiguous_count")) for row in rows) / path_count
        ),
        "win_rate": rounded(None if effective_n_sum == 0 else win_count_sum / effective_n_sum),
        "loss_rate": rounded(None if effective_n_sum == 0 else loss_count_sum / effective_n_sum),
    }


def aggregate_numeric_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = [
        ("portfolio", []),
        ("numeric_kind", ["numeric_row_kind"]),
        ("symbol", ["symbol"]),
        ("symbol_timeframe", ["symbol", "market_timeframe"]),
        (
            "symbol_timeframe_session_horizon",
            ["symbol", "market_timeframe", "route_session", "horizon_id"],
        ),
        (
            "symbol_timeframe_session_horizon_side_class",
            [
                "symbol",
                "market_timeframe",
                "route_session",
                "horizon_id",
                "selected_side",
                "follow_inverse_default_off_avoid_class",
            ],
        ),
        ("source_component", ["source_component"]),
        ("decision", ["keep_kill_redesign_implement_decision"]),
    ]
    output: list[dict[str, Any]] = []
    for aggregate_level, fields in specs:
        groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            groups[tuple(row.get(field) for field in fields)].append(row)
        for key, members in sorted(groups.items(), key=lambda item: tuple(normalized(part) for part in item[0])):
            dimensions = {field: value for field, value in zip(fields, key)}
            output.append(
                boundary_row(
                    {
                        "unified_numeric_aggregate_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-NUMERIC-AGG-{len(output) + 1:06d}"
                        ),
                        "aggregate_level": aggregate_level,
                        "aggregate_dimensions": dimensions,
                        "row_count": len(members),
                        "source_path_count": len({member.get("source_path") for member in members}),
                        "decision_row_count": len(
                            {
                                member.get("input_unified_final_decision_row_id")
                                for member in members
                                if member.get("input_unified_final_decision_row_id")
                            }
                        ),
                        **performance_rollup(members),
                        "keep_kill_redesign_implement_decision": aggregate_decision(members),
                        "follow_inverse_default_off_avoid_class": aggregate_class(members),
                    }
                )
            )
    return output


def aggregate_decision(rows: list[dict[str, Any]]) -> str:
    if any((row.get("missing_simulated_fields") or []) for row in rows):
        return "REDESIGN_EXPANDED_MARKET_UNIFIED_NUMERIC_AGGREGATE"
    if all(row.get("numeric_row_kind") == "unified_terminal_redesign" for row in rows):
        return "REDESIGN_EXPANDED_MARKET_UNIFIED_NUMERIC_TERMINAL_AGGREGATE"
    cost_r = weighted_average(rows, "cost_adjusted_simulated_r", "effective_n")
    if cost_r is not None and cost_r > 0:
        return "IMPLEMENT_EXPANDED_MARKET_UNIFIED_NUMERIC_AGGREGATE"
    return "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_UNIFIED_NUMERIC_AGGREGATE"


def aggregate_class(rows: list[dict[str, Any]]) -> str:
    classes = {normalized(row.get("follow_inverse_default_off_avoid_class")) for row in rows}
    classes.discard("")
    if classes == {"follow"}:
        return "follow"
    if classes == {"redesign"}:
        return "redesign"
    if classes == {"avoid"}:
        return "avoid"
    if classes == {"default-off"}:
        return "default-off"
    return "mixed"


def system_unified_numeric_evidence_rows(
    evidence_rows: list[dict[str, Any]],
    terminal_rows: list[dict[str, Any]],
    decision_rows: list[dict[str, Any]],
    source_access_rows_: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    issue_rows: list[dict[str, Any]],
    input_counts: dict[str, Any],
) -> list[dict[str, Any]]:
    all_numeric = evidence_rows + terminal_rows
    return [
        boundary_row(
            {
                "system_row_id": "OHLC-GTOS-EXPANDED-MARKET-UNIFIED-NUMERIC-SYSTEM-000001",
                "input_counts": input_counts,
                "evidence_numeric_rows": len(evidence_rows),
                "terminal_numeric_rows": len(terminal_rows),
                "decision_numeric_rows": len(decision_rows),
                "source_access_proof_rows": len(source_access_rows_),
                "aggregate_rows": len(aggregate_rows),
                "issue_rows": len(issue_rows),
                "rows_with_simulated_r": sum(1 for row in all_numeric if not row.get("missing_simulated_fields")),
                "rows_without_simulated_r": sum(1 for row in all_numeric if row.get("missing_simulated_fields")),
                "source_access_confirmed_rows": sum(
                    1 for row in source_access_rows_ if row.get("source_access_status") == "SOURCE_PATH_HASH_CONFIRMED"
                ),
                "source_access_issue_rows": sum(
                    1 for row in source_access_rows_ if row.get("source_access_status") != "SOURCE_PATH_HASH_CONFIRMED"
                ),
                **performance_rollup(all_numeric),
                "keep_kill_redesign_implement_decision": (
                    "IMPLEMENT_EXPANDED_MARKET_UNIFIED_NUMERIC_EVIDENCE_SYSTEM"
                    if not issue_rows
                    else "REDESIGN_EXPANDED_MARKET_UNIFIED_NUMERIC_EVIDENCE_SYSTEM"
                ),
                "follow_inverse_default_off_avoid_class": "mixed",
            }
        )
    ]
