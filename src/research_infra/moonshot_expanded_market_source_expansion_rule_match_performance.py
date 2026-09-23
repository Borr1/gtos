"""Compute rule-match performance from expanded-market source-expansion matches."""

from __future__ import annotations

from collections import Counter
from typing import Any

from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_PERFORMANCE = (
    "src/research_infra/moonshot_expanded_market_source_expansion_rule_match_performance.py"
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
    output["expanded_market_source_expansion_rule_match_performance_surface"] = (
        EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_PERFORMANCE
    )
    output["research_boundary"] = research_boundary()
    return output


def new_stats() -> dict[str, Any]:
    return {
        "count": 0,
        "gross_sum": 0.0,
        "cost_sum": 0.0,
        "stress_sum": 0.0,
        "win_count": 0,
        "loss_count": 0,
        "zero_count": 0,
        "win_sum": 0.0,
        "loss_sum": 0.0,
        "source_path_sha256": Counter(),
        "symbol_family": Counter(),
        "side": Counter(),
        "source_file_sha256": Counter(),
        "work_resolution_ids": set(),
    }


def update_stats(stats: dict[str, Any], match_row: dict[str, Any]) -> None:
    cost_r = as_float(match_row.get("cost_adjusted_simulated_r"))
    gross_r = as_float(match_row.get("gross_simulated_r"))
    stress_r = as_float(match_row.get("stress_simulated_r"))
    stats["count"] += 1
    stats["gross_sum"] += gross_r if gross_r is not None else 0.0
    stats["cost_sum"] += cost_r if cost_r is not None else 0.0
    stats["stress_sum"] += stress_r if stress_r is not None else 0.0
    if cost_r is None or cost_r == 0:
        stats["zero_count"] += 1
    elif cost_r > 0:
        stats["win_count"] += 1
        stats["win_sum"] += cost_r
    else:
        stats["loss_count"] += 1
        stats["loss_sum"] += cost_r
    for key in ("source_path_sha256", "symbol_family", "side", "source_file_sha256"):
        value = match_row.get(key)
        if value is not None:
            stats[key][str(value)] += 1
    work_id = match_row.get("input_work_resolution_row_id")
    if work_id:
        stats["work_resolution_ids"].add(str(work_id))


def _dominant(counter: Counter[str], total: int) -> tuple[str | None, float]:
    if not counter or total <= 0:
        return None, 0.0
    value, count = counter.most_common(1)[0]
    return value, rounded(count / total)


def finalize_stats(stats: dict[str, Any]) -> dict[str, Any]:
    count = int(stats["count"])
    dominant_source, dominant_source_share = _dominant(stats["source_path_sha256"], count)
    dominant_family, dominant_family_share = _dominant(stats["symbol_family"], count)
    dominant_side, dominant_side_share = _dominant(stats["side"], count)
    dominant_file, dominant_file_share = _dominant(stats["source_file_sha256"], count)
    avg_win = rounded(stats["win_sum"] / stats["win_count"]) if stats["win_count"] else 0.0
    avg_loss = rounded(stats["loss_sum"] / stats["loss_count"]) if stats["loss_count"] else 0.0
    return {
        "observed_match_rows": count,
        "unique_work_resolution_rows": len(stats["work_resolution_ids"]),
        "gross_simulated_r_expectancy": rounded(stats["gross_sum"] / count) if count else None,
        "cost_adjusted_simulated_r_expectancy": rounded(stats["cost_sum"] / count) if count else None,
        "stress_simulated_r_expectancy": rounded(stats["stress_sum"] / count) if count else None,
        "win_count": int(stats["win_count"]),
        "loss_count": int(stats["loss_count"]),
        "zero_count": int(stats["zero_count"]),
        "win_rate": rounded(stats["win_count"] / count) if count else None,
        "average_win": avg_win,
        "average_loss": avg_loss,
        "dominant_source_path_sha256": dominant_source,
        "dominant_source_path_share": dominant_source_share,
        "dominant_symbol_family": dominant_family,
        "dominant_symbol_family_share": dominant_family_share,
        "dominant_side": dominant_side,
        "dominant_side_share": dominant_side_share,
        "dominant_source_file_sha256": dominant_file,
        "dominant_source_file_share": dominant_file_share,
        "source_path_count": len(stats["source_path_sha256"]),
        "source_file_count": len(stats["source_file_sha256"]),
    }


def action_class(rule_row: dict[str, Any], summary: dict[str, Any]) -> str:
    candidate_class = str(rule_row.get("rule_candidate_class") or "")
    expectancy = as_float(summary.get("cost_adjusted_simulated_r_expectancy"))
    if "positive-follow" in candidate_class and expectancy is not None and expectancy > 0:
        return "follow"
    if "negative-avoid" in candidate_class and expectancy is not None and expectancy < 0:
        return "avoid"
    if "weak-neutral" in candidate_class:
        return "default-off"
    return "redesign"


def performance_decision(rule_row: dict[str, Any], summary: dict[str, Any]) -> str:
    count = int(summary.get("observed_match_rows") or 0)
    expectancy = as_float(summary.get("cost_adjusted_simulated_r_expectancy"))
    stress = as_float(summary.get("stress_simulated_r_expectancy"))
    win_rate = as_float(summary.get("win_rate"))
    candidate_class = str(rule_row.get("rule_candidate_class") or "")
    if count < 5:
        return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_UNDERPOWERED"
    if (
        "positive-follow" in candidate_class
        and expectancy is not None
        and stress is not None
        and win_rate is not None
        and expectancy >= 0.05
        and stress >= 0.0
        and win_rate >= 0.5
    ):
        return "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_FOLLOW"
    if (
        "negative-avoid" in candidate_class
        and expectancy is not None
        and stress is not None
        and win_rate is not None
        and expectancy <= -0.05
        and stress <= 0.0
        and win_rate <= 0.45
    ):
        return "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_AVOID"
    if expectancy is not None and expectancy <= -0.10 and "negative-avoid" not in candidate_class:
        return "KILL_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_ADVERSE"
    return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_MIXED"


def rule_match_performance_row(
    rule_row: dict[str, Any],
    stats: dict[str, Any],
    sequence: int,
) -> dict[str, Any]:
    summary = finalize_stats(stats)
    rule_effective_n = int(rule_row.get("effective_n") or 0)
    observed = int(summary.get("observed_match_rows") or 0)
    effective_n = min(rule_effective_n, observed) if rule_effective_n and observed else observed
    decision = performance_decision(rule_row, summary)
    cls = action_class(rule_row, summary)
    return boundary_row(
        {
            "expanded_market_source_expansion_rule_match_performance_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-RULE-MATCH-PERF-{sequence:07d}"
            ),
            "input_rule_candidate_execution_row_id": rule_row.get(
                "expanded_market_source_expansion_rule_candidate_execution_row_id"
            ),
            "input_rule_candidate_row_id": rule_row.get("input_rule_candidate_row_id"),
            "input_work_resolution_row_id": rule_row.get("input_work_resolution_row_id"),
            "rule_match_performance_status": "SOURCE_EXPANSION_RULE_MATCH_PERFORMANCE_COMPUTED",
            "rule_candidate_class": rule_row.get("rule_candidate_class"),
            "symbol_family": rule_row.get("symbol_family"),
            "symbol": rule_row.get("symbol"),
            "source_symbol": rule_row.get("source_symbol"),
            "market_timeframe": rule_row.get("market_timeframe"),
            "route_session": rule_row.get("route_session"),
            "horizon_id": rule_row.get("horizon_id"),
            "side": rule_row.get("side"),
            "source_path": rule_row.get("source_path"),
            "source_path_sha256": rule_row.get("source_path_sha256"),
            "source_file_sha256": rule_row.get("source_file_sha256"),
            "candidate_rows_scanned": rule_row.get("candidate_rows_scanned"),
            "candidate_reported_match_count": rule_row.get("match_count"),
            "observed_match_rows": observed,
            "unique_work_resolution_rows": summary["unique_work_resolution_rows"],
            "duplicate_row_count": observed - int(summary["unique_work_resolution_rows"]),
            "rule_effective_n": rule_effective_n,
            "effective_n": effective_n,
            "duplicate_inflation": rounded(observed / effective_n) if effective_n else None,
            "gross_simulated_r": summary["gross_simulated_r_expectancy"],
            "cost_adjusted_simulated_r": summary["cost_adjusted_simulated_r_expectancy"],
            "stress_simulated_r": summary["stress_simulated_r_expectancy"],
            "gross_simulated_r_expectancy": summary["gross_simulated_r_expectancy"],
            "cost_adjusted_simulated_r_expectancy": summary[
                "cost_adjusted_simulated_r_expectancy"
            ],
            "stress_simulated_r_expectancy": summary["stress_simulated_r_expectancy"],
            "win_count": summary["win_count"],
            "loss_count": summary["loss_count"],
            "zero_count": summary["zero_count"],
            "win_rate": summary["win_rate"],
            "average_win": summary["average_win"],
            "average_loss": summary["average_loss"],
            "dominant_source_path_sha256": summary["dominant_source_path_sha256"],
            "dominant_source_path_share": summary["dominant_source_path_share"],
            "dominant_symbol_family": summary["dominant_symbol_family"],
            "dominant_symbol_family_share": summary["dominant_symbol_family_share"],
            "dominant_side": summary["dominant_side"],
            "dominant_side_share": summary["dominant_side_share"],
            "dominant_source_file_sha256": summary["dominant_source_file_sha256"],
            "dominant_source_file_share": summary["dominant_source_file_share"],
            "source_path_count": summary["source_path_count"],
            "source_file_count": summary["source_file_count"],
            "follow_inverse_default_off_avoid_class": cls,
            "keep_kill_redesign_implement_decision": decision,
        }
    )


def replay_task_performance_row(row: dict[str, Any], sequence: int) -> dict[str, Any]:
    return boundary_row(
        {
            "expanded_market_source_expansion_replay_task_performance_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-REPLAY-TASK-PERF-{sequence:07d}"
            ),
            "input_replay_task_execution_row_id": row.get(
                "expanded_market_source_expansion_replay_task_execution_row_id"
            ),
            "replay_task_performance_status": "SOURCE_EXPANSION_REPLAY_TASK_PERFORMANCE_PRESERVED",
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
            "missing_work_fields": row.get("missing_work_fields") or [],
            "follow_inverse_default_off_avoid_class": "redesign",
            "keep_kill_redesign_implement_decision": (
                "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_REPLAY_IMPLEMENTATION"
            ),
        }
    )


def source_task_performance_row(row: dict[str, Any], sequence: int) -> dict[str, Any]:
    return boundary_row(
        {
            "expanded_market_source_expansion_source_task_performance_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-SOURCE-TASK-PERF-{sequence:07d}"
            ),
            "input_source_task_execution_row_id": row.get(
                "expanded_market_source_expansion_source_task_execution_row_id"
            ),
            "source_task_performance_status": "SOURCE_EXPANSION_SOURCE_TASK_PERFORMANCE_PRESERVED",
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
            "missing_work_fields": row.get("missing_work_fields") or [],
            "discovered_same_symbol_timeframe_source_count": row.get(
                "discovered_same_symbol_timeframe_source_count"
            ),
            "follow_inverse_default_off_avoid_class": "redesign",
            "keep_kill_redesign_implement_decision": (
                "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_SOURCE_ACQUISITION"
            ),
        }
    )


def aggregate_performance_rows(
    performance_rows: list[dict[str, Any]],
    replay_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], dict[str, Any]] = {}
    for row in performance_rows:
        key = (
            "rule_match_performance",
            str(row.get("keep_kill_redesign_implement_decision") or ""),
            str(row.get("follow_inverse_default_off_avoid_class") or ""),
            str(row.get("symbol_family") or ""),
            str(row.get("market_timeframe") or ""),
            str(row.get("route_session") or ""),
            str(row.get("horizon_id") or ""),
            str(row.get("side") or ""),
        )
        bucket = grouped.setdefault(
            key,
            {
                "row_type": key[0],
                "keep_kill_redesign_implement_decision": key[1],
                "follow_inverse_default_off_avoid_class": key[2],
                "symbol_family": key[3],
                "market_timeframe": key[4],
                "route_session": key[5],
                "horizon_id": key[6],
                "side": key[7],
                "row_count": 0,
                "cost_sum": 0.0,
                "stress_sum": 0.0,
                "win_count": 0,
                "loss_count": 0,
                "zero_count": 0,
                "effective_n_sum": 0,
            },
        )
        bucket["row_count"] += 1
        bucket["cost_sum"] += as_float(row.get("cost_adjusted_simulated_r")) or 0.0
        bucket["stress_sum"] += as_float(row.get("stress_simulated_r")) or 0.0
        bucket["win_count"] += int(row.get("win_count") or 0)
        bucket["loss_count"] += int(row.get("loss_count") or 0)
        bucket["zero_count"] += int(row.get("zero_count") or 0)
        bucket["effective_n_sum"] += int(row.get("effective_n") or 0)
    for row_type, rows in (("replay_task_performance", replay_rows), ("source_task_performance", source_rows)):
        for row in rows:
            key = (
                row_type,
                str(row.get("keep_kill_redesign_implement_decision") or ""),
                str(row.get("follow_inverse_default_off_avoid_class") or ""),
                str(row.get("symbol_family") or ""),
                str(row.get("market_timeframe") or ""),
                str(row.get("route_session") or ""),
                str(row.get("horizon_id") or ""),
                str(row.get("side") or ""),
            )
            bucket = grouped.setdefault(
                key,
                {
                    "row_type": key[0],
                    "keep_kill_redesign_implement_decision": key[1],
                    "follow_inverse_default_off_avoid_class": key[2],
                    "symbol_family": key[3],
                    "market_timeframe": key[4],
                    "route_session": key[5],
                    "horizon_id": key[6],
                    "side": key[7],
                    "row_count": 0,
                    "cost_sum": 0.0,
                    "stress_sum": 0.0,
                    "win_count": 0,
                    "loss_count": 0,
                    "zero_count": 0,
                    "effective_n_sum": 0,
                },
            )
            bucket["row_count"] += 1
    rows_out: list[dict[str, Any]] = []
    for sequence, bucket in enumerate(grouped.values(), start=1):
        count = int(bucket["row_count"])
        rows_out.append(
            boundary_row(
                {
                    "expanded_market_source_expansion_rule_match_performance_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-RULE-MATCH-PERF-AGG-{sequence:07d}"
                    ),
                    **{
                        key: value
                        for key, value in bucket.items()
                        if key not in {"cost_sum", "stress_sum"}
                    },
                    "cost_adjusted_simulated_r_expectancy": (
                        rounded(bucket["cost_sum"] / count) if count and bucket["row_type"] == "rule_match_performance" else None
                    ),
                    "stress_simulated_r_expectancy": (
                        rounded(bucket["stress_sum"] / count) if count and bucket["row_type"] == "rule_match_performance" else None
                    ),
                }
            )
        )
    return rows_out
