"""Source-consensus robustness over combined expanded-market performance rows."""

from __future__ import annotations

from collections import Counter
from statistics import mean, pstdev
from typing import Any

from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_SOURCE_CONSENSUS_ROBUSTNESS_SURFACE = (
    "src/research_infra/moonshot_expanded_market_source_consensus_robustness.py"
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
    output["expanded_market_source_consensus_robustness_surface"] = (
        EXPANDED_MARKET_SOURCE_CONSENSUS_ROBUSTNESS_SURFACE
    )
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def average(values: list[float]) -> float | None:
    return mean(values) if values else None


def stdev(values: list[float]) -> float | None:
    return pstdev(values) if len(values) > 1 else 0.0 if values else None


def class_from_decision(decision: str) -> str:
    if decision.startswith("IMPLEMENT"):
        return "follow"
    if "AVOID" in decision:
        return "avoid"
    if decision.startswith("KILL"):
        return "default-off"
    return "redesign"


def symbol_family(symbol: Any) -> tuple[str, str]:
    text = normalized(symbol).upper()
    if not text:
        return "UNKNOWN_SYMBOL_FAMILY", "missing_symbol"
    if text in {"XAUUSD"} or "XAUUSD" in text or "GCM" in text or "MGC" in text:
        return "XAUUSD_GOLD_FAMILY", "xauusd_or_gc_mgc_proxy"
    if text in {"XAGUSD"} or "XAGUSD" in text or text.startswith("SI") or "SIL" in text:
        return "XAGUSD_SILVER_FAMILY", "xagusd_or_si_sil_proxy"
    if text in {"NAS100"} or "NAS100" in text or "NQM" in text or "MNQ" in text:
        return "NAS100_NQ_FAMILY", "nas100_or_nq_mnq_proxy"
    if text in {"US30", "US30_CASH"} or "US30" in text or "YMM" in text or "MYM" in text:
        return "US30_YM_FAMILY", "us30_or_ym_mym_proxy"
    if text in {"SPX500"} or "SPX" in text or "ESM" in text or "MES" in text:
        return "SPX500_ES_FAMILY", "spx500_or_es_mes_proxy"
    if text in {"USDJPY"} or "6JM" in text:
        return "USDJPY_6J_FAMILY", "usdjpy_or_6j_proxy"
    if text in {"EURUSD"} or "6EM" in text:
        return "EURUSD_6E_FAMILY", "eurusd_or_6e_proxy"
    if text in {"GBPUSD"} or "6BM" in text:
        return "GBPUSD_6B_FAMILY", "gbpusd_or_6b_proxy"
    if text in {"AUDUSD"} or "6AM" in text:
        return "AUDUSD_6A_FAMILY", "audusd_or_6a_proxy"
    if "CLM" in text or "MCL" in text or "USOIL" in text or "UKOIL" in text or "CL_PROXY" in text:
        return "OIL_CL_FAMILY", "oil_or_cl_mcl_proxy"
    if "VXM" in text or "VIX" in text:
        return "VIX_FAMILY", "vix_or_vx_proxy"
    if "BTC" in text:
        return "BTC_FAMILY", "btc_proxy"
    if "ETH" in text:
        return "ETH_FAMILY", "eth_proxy"
    if "ZNM" in text:
        return "ZN_RATE_FAMILY", "zn_rate_proxy"
    if "ZBM" in text:
        return "ZB_RATE_FAMILY", "zb_rate_proxy"
    return text, "exact_symbol"


def consensus_key(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    family, _ = symbol_family(row.get("symbol"))
    return (
        family,
        normalized(row.get("market_timeframe")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("side")),
    )


def group_profile(rows: list[dict[str, Any]]) -> dict[str, Any]:
    cost_values = [value for value in (as_float(row.get("cost_adjusted_simulated_r")) for row in rows) if value is not None]
    gross_values = [value for value in (as_float(row.get("gross_simulated_r")) for row in rows) if value is not None]
    stress_values = [value for value in (as_float(row.get("stress_simulated_r")) for row in rows) if value is not None]
    source_path_effective = Counter()
    source_family_effective = Counter()
    for row in rows:
        effective_n = int(row.get("effective_n") or 0)
        source_path_effective[normalized(row.get("source_path"))] += effective_n
        source_family_effective[normalized(row.get("performance_source_family"))] += effective_n
    effective_n_sum = sum(int(row.get("effective_n") or 0) for row in rows)
    top_source_effective = max(source_path_effective.values()) if source_path_effective else 0
    positive_rows = sum(1 for value in cost_values if value > 0)
    negative_rows = sum(1 for value in cost_values if value < 0)
    source_path_count = len({row.get("source_path") for row in rows})
    source_family_count = len({row.get("performance_source_family") for row in rows})
    cost_mean = average(cost_values)
    stress_mean = average(stress_values)
    cost_std = stdev(cost_values)
    sign_conflict = positive_rows > 0 and negative_rows > 0
    concentration = (top_source_effective / effective_n_sum) if effective_n_sum else 1.0
    decision = consensus_decision(
        cost_mean,
        stress_mean,
        cost_std,
        source_path_count,
        source_family_count,
        concentration,
        sign_conflict,
        len(cost_values),
    )
    return {
        "row_count": len(rows),
        "simulated_r_row_count": len(cost_values),
        "missing_simulated_row_count": len(rows) - len(cost_values),
        "source_path_count": source_path_count,
        "source_family_count": source_family_count,
        "source_symbol_count": len({row.get("source_symbol") for row in rows}),
        "raw_symbol_count": len({row.get("symbol") for row in rows}),
        "effective_n_sum": effective_n_sum,
        "effective_n_after_duplicate_collapse_sum": sum(
            int(row.get("effective_n_after_duplicate_collapse") or 0) for row in rows
        ),
        "duplicate_row_count_sum": sum(int(row.get("duplicate_row_count") or 0) for row in rows),
        "win_count_sum": sum(int(row.get("win_count") or 0) for row in rows),
        "loss_count_sum": sum(int(row.get("loss_count") or 0) for row in rows),
        "zero_count_sum": sum(int(row.get("zero_count") or 0) for row in rows),
        "target_first_count_sum": sum(int(row.get("target_first_count") or 0) for row in rows),
        "stop_first_count_sum": sum(int(row.get("stop_first_count") or 0) for row in rows),
        "neither_count_sum": sum(int(row.get("neither_count") or 0) for row in rows),
        "ambiguous_count_sum": sum(int(row.get("ambiguous_count") or 0) for row in rows),
        "consensus_gross_simulated_r": rounded(average(gross_values)),
        "consensus_cost_adjusted_simulated_r": rounded(cost_mean),
        "consensus_stress_simulated_r": rounded(stress_mean),
        "cost_adjusted_simulated_r_stddev": rounded(cost_std),
        "cost_adjusted_simulated_r_min": rounded(min(cost_values) if cost_values else None),
        "cost_adjusted_simulated_r_max": rounded(max(cost_values) if cost_values else None),
        "positive_cost_rows": positive_rows,
        "negative_cost_rows": negative_rows,
        "sign_conflict": sign_conflict,
        "source_path_effective_n": dict(sorted(source_path_effective.items())),
        "source_family_effective_n": dict(sorted(source_family_effective.items())),
        "top_source_path_effective_n_share": rounded(concentration),
        "keep_kill_redesign_implement_decision": decision,
        "follow_inverse_default_off_avoid_class": class_from_decision(decision),
    }


def consensus_decision(
    cost_mean: float | None,
    stress_mean: float | None,
    cost_std: float | None,
    source_path_count: int,
    source_family_count: int,
    concentration: float,
    sign_conflict: bool,
    simulated_rows: int,
) -> str:
    if cost_mean is None or stress_mean is None or simulated_rows == 0:
        return "REDESIGN_EXPANDED_MARKET_SOURCE_CONSENSUS_MISSING_SIMULATED_R"
    if source_path_count < 2:
        return "REDESIGN_EXPANDED_MARKET_SOURCE_CONSENSUS_SINGLE_SOURCE"
    if concentration > 0.80:
        return "REDESIGN_EXPANDED_MARKET_SOURCE_CONSENSUS_CONCENTRATION"
    if source_family_count > 1 and sign_conflict and (cost_std or 0.0) > 0.25:
        return "REDESIGN_EXPANDED_MARKET_SOURCE_CONSENSUS_DISAGREEMENT"
    if cost_mean >= 0.10 and stress_mean > -0.05:
        return "IMPLEMENT_EXPANDED_MARKET_SOURCE_CONSENSUS_ROBUST"
    if cost_mean <= -0.20 and stress_mean <= -0.20:
        return "KILL_EXPANDED_MARKET_SOURCE_CONSENSUS_BRANCH"
    if cost_mean < -0.05:
        return "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_SOURCE_CONSENSUS"
    return "REDESIGN_EXPANDED_MARKET_SOURCE_CONSENSUS_WEAK_EDGE"


def source_consensus_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(consensus_key(row), []).append(row)
    profiles = {key: group_profile(members) for key, members in grouped.items()}
    consensus_rows: list[dict[str, Any]] = []
    issue_rows: list[dict[str, Any]] = []
    for row in rows:
        key = consensus_key(row)
        profile = profiles[key]
        family, basis = symbol_family(row.get("symbol"))
        row_cost = as_float(row.get("cost_adjusted_simulated_r"))
        consensus_cost = as_float(profile.get("consensus_cost_adjusted_simulated_r"))
        missing = list(row.get("missing_simulated_fields") or [])
        if row_cost is None:
            missing.append("cost_adjusted_simulated_r")
        consensus_row = boundary_row(
            {
                "expanded_market_source_consensus_row_id": (
                    f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-CONSENSUS-{len(consensus_rows) + 1:07d}"
                ),
                "input_supplemental_performance_row_id": row.get(
                    "expanded_market_supplemental_performance_row_id"
                ),
                "performance_source_family": row.get("performance_source_family"),
                "symbol_family": family,
                "symbol_family_basis": basis,
                "symbol": row.get("symbol"),
                "source_symbol": row.get("source_symbol"),
                "market_timeframe": row.get("market_timeframe"),
                "route_session": row.get("route_session"),
                "horizon_id": row.get("horizon_id"),
                "side": row.get("side"),
                "source_component": row.get("source_component"),
                "source_path": row.get("source_path"),
                "source_file_sha256": row.get("source_file_sha256"),
                "source_record_selector": row.get("source_record_selector"),
                "entry_reference": row.get("entry_reference"),
                "entry_reference_time": row.get("entry_reference_time"),
                "proxy_entry_price": row.get("proxy_entry_price"),
                "proxy_denominator_price": row.get("proxy_denominator_price"),
                "proxy_target_price": row.get("proxy_target_price"),
                "proxy_stop_price": row.get("proxy_stop_price"),
                "path_order_result": row.get("path_order_result"),
                "fill_status": row.get("fill_status"),
                "gross_simulated_r": row.get("gross_simulated_r"),
                "cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
                "stress_simulated_r": row.get("stress_simulated_r"),
                "win_count": int(row.get("win_count") or 0),
                "loss_count": int(row.get("loss_count") or 0),
                "zero_count": int(row.get("zero_count") or 0),
                "target_first_count": int(row.get("target_first_count") or 0),
                "stop_first_count": int(row.get("stop_first_count") or 0),
                "neither_count": int(row.get("neither_count") or 0),
                "ambiguous_count": int(row.get("ambiguous_count") or 0),
                "effective_n": int(row.get("effective_n") or 0),
                "duplicate_row_count": int(row.get("duplicate_row_count") or 0),
                "effective_n_after_duplicate_collapse": int(row.get("effective_n_after_duplicate_collapse") or 0),
                "concentration_top_month_share": row.get("concentration_top_month_share"),
                "missing_simulated_fields": sorted(set(missing)),
                "consensus_row_count": profile.get("row_count"),
                "consensus_source_path_count": profile.get("source_path_count"),
                "consensus_source_family_count": profile.get("source_family_count"),
                "consensus_source_symbol_count": profile.get("source_symbol_count"),
                "consensus_effective_n_sum": profile.get("effective_n_sum"),
                "consensus_cost_adjusted_simulated_r": profile.get("consensus_cost_adjusted_simulated_r"),
                "consensus_stress_simulated_r": profile.get("consensus_stress_simulated_r"),
                "cost_adjusted_simulated_r_delta_vs_consensus": rounded(
                    row_cost - consensus_cost if row_cost is not None and consensus_cost is not None else None
                ),
                "cost_adjusted_simulated_r_stddev": profile.get("cost_adjusted_simulated_r_stddev"),
                "top_source_path_effective_n_share": profile.get("top_source_path_effective_n_share"),
                "sign_conflict": profile.get("sign_conflict"),
                "source_path_effective_n": profile.get("source_path_effective_n"),
                "source_family_effective_n": profile.get("source_family_effective_n"),
                "keep_kill_redesign_implement_decision": profile.get("keep_kill_redesign_implement_decision"),
                "follow_inverse_default_off_avoid_class": profile.get("follow_inverse_default_off_avoid_class"),
            }
        )
        consensus_rows.append(consensus_row)
        if missing:
            issue_rows.append(
                boundary_row(
                    {
                        "expanded_market_source_consensus_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-CONSENSUS-ISSUE-{len(issue_rows) + 1:06d}"
                        ),
                        "input_source_consensus_row_id": consensus_row["expanded_market_source_consensus_row_id"],
                        "input_supplemental_performance_row_id": row.get(
                            "expanded_market_supplemental_performance_row_id"
                        ),
                        "symbol_family": family,
                        "symbol": row.get("symbol"),
                        "market_timeframe": row.get("market_timeframe"),
                        "route_session": row.get("route_session"),
                        "horizon_id": row.get("horizon_id"),
                        "side": row.get("side"),
                        "source_path": row.get("source_path"),
                        "source_file_sha256": row.get("source_file_sha256"),
                        "missing_simulated_fields": sorted(set(missing)),
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_SOURCE_CONSENSUS_MISSING_SIMULATED_R"
                        ),
                    }
                )
            )
    return consensus_rows, issue_rows


def aggregate_consensus_rows(consensus_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = {}
    for row in consensus_rows:
        grouped.setdefault(
            (
                normalized(row.get("symbol_family")),
                normalized(row.get("market_timeframe")),
                normalized(row.get("route_session")),
                normalized(row.get("horizon_id")),
                normalized(row.get("side")),
            ),
            [],
        ).append(row)
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        cost_values = [
            value for value in (as_float(row.get("cost_adjusted_simulated_r")) for row in members) if value is not None
        ]
        stress_values = [
            value for value in (as_float(row.get("stress_simulated_r")) for row in members) if value is not None
        ]
        decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in members)
        classes = Counter(row.get("follow_inverse_default_off_avoid_class") for row in members)
        output.append(
            boundary_row(
                {
                    "expanded_market_source_consensus_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-CONSENSUS-AGG-{len(output) + 1:06d}"
                    ),
                    "symbol_family": key[0],
                    "market_timeframe": key[1],
                    "route_session": key[2],
                    "horizon_id": key[3],
                    "side": key[4],
                    "row_count": len(members),
                    "source_path_count": len({row.get("source_path") for row in members}),
                    "source_family_count": len({row.get("performance_source_family") for row in members}),
                    "source_symbol_count": len({row.get("source_symbol") for row in members}),
                    "simulated_r_row_count": len(cost_values),
                    "missing_simulated_row_count": sum(1 for row in members if row.get("missing_simulated_fields")),
                    "effective_n": sum(int(row.get("effective_n") or 0) for row in members),
                    "effective_n_after_duplicate_collapse": sum(
                        int(row.get("effective_n_after_duplicate_collapse") or 0) for row in members
                    ),
                    "duplicate_row_count": sum(int(row.get("duplicate_row_count") or 0) for row in members),
                    "win_count": sum(int(row.get("win_count") or 0) for row in members),
                    "loss_count": sum(int(row.get("loss_count") or 0) for row in members),
                    "zero_count": sum(int(row.get("zero_count") or 0) for row in members),
                    "target_first_count": sum(int(row.get("target_first_count") or 0) for row in members),
                    "stop_first_count": sum(int(row.get("stop_first_count") or 0) for row in members),
                    "neither_count": sum(int(row.get("neither_count") or 0) for row in members),
                    "ambiguous_count": sum(int(row.get("ambiguous_count") or 0) for row in members),
                    "expectancy_cost_adjusted_simulated_r": rounded(average(cost_values)),
                    "expectancy_stress_simulated_r": rounded(average(stress_values)),
                    "average_win": rounded(average([value for value in cost_values if value > 0])),
                    "average_loss": rounded(average([value for value in cost_values if value < 0])),
                    "cost_adjusted_simulated_r_stddev": rounded(stdev(cost_values)),
                    "decision_counts": dict(sorted(decisions.items())),
                    "class_counts": dict(sorted(classes.items())),
                    "keep_kill_redesign_implement_decision": decisions.most_common(1)[0][0] if decisions else None,
                }
            )
        )
    return output


def system_source_consensus_rows(
    consensus_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    issue_rows: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        boundary_row(
            {
                "expanded_market_source_consensus_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-SOURCE-CONSENSUS-SYSTEM-0001"
                ),
                "source_consensus_rows": len(consensus_rows),
                "aggregate_rows": len(aggregate_rows),
                "issue_rows": len(issue_rows),
                "rows_with_simulated_r": sum(1 for row in consensus_rows if not row.get("missing_simulated_fields")),
                "symbol_family_count": len({row.get("symbol_family") for row in consensus_rows}),
                "source_path_count": len({row.get("source_path") for row in consensus_rows}),
                "source_family_count": len({row.get("performance_source_family") for row in consensus_rows}),
                "decision_counts": dict(
                    sorted(Counter(row.get("keep_kill_redesign_implement_decision") for row in consensus_rows).items())
                ),
                "class_counts": dict(
                    sorted(Counter(row.get("follow_inverse_default_off_avoid_class") for row in consensus_rows).items())
                ),
                "metadata": metadata,
            }
        )
    ]
