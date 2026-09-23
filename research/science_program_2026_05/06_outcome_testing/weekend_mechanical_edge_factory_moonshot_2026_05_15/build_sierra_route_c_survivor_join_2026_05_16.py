#!/usr/bin/env python3
"""Join Sierra SCID survivor/control families to Route C residual descriptors."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

SIERRA_CONTROL_LEDGER = ROUTE_DIR / f"SIERRA_SCID_M15_NEIGHBOR_GAP_CONTROL_LEDGER_{STAMP}.jsonl"
ROUTE_C_RESIDUAL_LEDGER = ROUTE_DIR / f"TICK_M15_ROUTE_C_RESIDUAL_DESCRIPTOR_QUEUE_{SOURCE_STAMP}.jsonl"
ROUTE_C_TRANSFER_LEDGER = ROUTE_DIR / f"TICK_M15_RESIDUAL_TRANSFER_DIAGNOSIS_LEDGER_{STAMP}.jsonl"
ROUTE_C_GEOMETRY_LEDGER = ROUTE_DIR / f"TICK_M15_ENTRY_GEOMETRY_DENOMINATOR_COMPARISON_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_ROUTE_C_SURVIVOR_JOIN_RESULT_{STAMP}.json"
SIERRA_SPLIT_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_SURVIVOR_SPLIT_LEDGER_{STAMP}.jsonl"
ROUTE_RESIDUAL_FAMILY_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_RESIDUAL_FAMILY_LEDGER_{STAMP}.jsonl"
PROXY_JOIN_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_PROXY_JOIN_LEDGER_{STAMP}.jsonl"
PROXY_JOIN_SUMMARY_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_PROXY_JOIN_SUMMARY_LEDGER_{STAMP}.jsonl"
FAILURE_INTELLIGENCE_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_FAILURE_INTELLIGENCE_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_SURVIVOR_JOIN_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_ROUTE_C_SURVIVOR_JOIN_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Sierra SCID to Route C proxy-family join only; no strategy validation, "
    "trade outcome, R/PnL, expectancy, live-readiness, or promotion"
)

NO_STATS = {
    "n": 0,
    "mean_abs_future_change": None,
    "mean_future_change_per_current_range": None,
    "future_follows_price_sign_rate": None,
    "future_follows_delta_sign_rate": None,
}


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def relative(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def safe_float(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if out != out or out in (float("inf"), float("-inf")):
        return None
    return out


def diff_float(left: Any, right: Any) -> float | None:
    left_float = safe_float(left)
    right_float = safe_float(right)
    if left_float is None or right_float is None:
        return None
    return left_float - right_float


def sierra_mechanism_family(flag: str) -> str:
    if flag == "post_source_gap_first_bar":
        return "source_gap_artifact"
    if "price_delta_divergence" in flag:
        return "price_delta_divergence"
    if "delta" in flag or "volume" in flag or "num_trades" in flag:
        return "orderflow_activity"
    if "range" in flag or "wick" in flag or "body" in flag or "close_near" in flag:
        return "price_path_geometry"
    return "other_sierra_primitive"


def route_c_mechanism_family(flag: str) -> str:
    if flag.startswith("ABSORPTION_PROXY_CVD_DIVERGENCE"):
        return "price_delta_divergence"
    if flag.startswith("DELTA_IMPULSE"):
        return "orderflow_activity"
    if flag.startswith("TICK_RANGE_EXPANSION"):
        return "price_path_geometry"
    if flag.startswith("TICK_VELOCITY_BURST"):
        return "orderflow_activity"
    if flag.startswith("SPREAD_SHOCK"):
        return "execution_friction_or_liquidity"
    return "other_route_c_primitive"


def mechanism_compatible(sierra_family: str, route_family: str) -> bool:
    if sierra_family == route_family:
        return True
    compatible_pairs = {
        ("orderflow_activity", "price_delta_divergence"),
        ("price_delta_divergence", "orderflow_activity"),
        ("price_path_geometry", "execution_friction_or_liquidity"),
        ("execution_friction_or_liquidity", "price_path_geometry"),
    }
    return (sierra_family, route_family) in compatible_pairs


def source_proxy(source_symbol: str) -> dict[str, Any]:
    exact_map = {
        "6BM26-CME": ["GBPUSD", "GBPJPY"],
        "6JM26-CME": ["USDJPY", "GBPJPY"],
        "NQM26-CME": ["NAS100"],
        "MNQM26-CME": ["NAS100"],
        "AAPL": ["NAS100"],
        "AMZN-NQTV": ["NAS100"],
        "SIM26-COMEX": ["XAGUSD"],
        "SILM26-COMEX": ["XAGUSD"],
    }
    broad_map = {
        "6AM26-CME": ["USDJPY", "GBPUSD", "GBPJPY"],
        "6CM26-CME": ["USDJPY", "GBPUSD", "GBPJPY"],
        "6EM26-CME": ["USDJPY", "GBPUSD", "GBPJPY"],
        "6SM26-CME": ["USDJPY", "GBPUSD", "GBPJPY"],
        "EURUSD": ["GBPUSD"],
        "ESM26-CME": ["NAS100"],
        "MESM26-CME": ["NAS100"],
        "RTYM26-CME": ["NAS100"],
        "M2KM26-CME": ["NAS100"],
        "YMM26-CBOT": ["NAS100"],
        "MYMM26-CBOT": ["NAS100"],
        "TICK-NYSE": ["NAS100"],
        "VXM26-CFE": ["NAS100", "USDJPY"],
        "VXMM26-CFE": ["NAS100", "USDJPY"],
        "GCM26-COMEX": ["XAGUSD"],
        "MGCM26-COMEX": ["XAGUSD"],
        "XAUUSD": ["XAGUSD"],
        "ZBM26-CBOT": ["USDJPY", "GBPJPY", "NAS100"],
        "ZNM26-CBOT": ["USDJPY", "GBPJPY", "NAS100"],
        "CLM26-NYMEX": ["NAS100"],
        "MCLM26-NYMEX": ["NAS100"],
        "BTCUSDT_PERP_BINANCE": ["NAS100"],
    }
    family_map = {
        "6AM26-CME": "fx_usd_macro",
        "6BM26-CME": "gbp_fx_direct",
        "6CM26-CME": "fx_usd_macro",
        "6EM26-CME": "fx_usd_macro",
        "6JM26-CME": "jpy_fx_direct",
        "6SM26-CME": "fx_usd_macro",
        "EURUSD": "eurusd_fx_macro",
        "NQM26-CME": "nasdaq_direct",
        "MNQM26-CME": "nasdaq_direct",
        "AAPL": "nasdaq_constituent_direct",
        "AMZN-NQTV": "nasdaq_constituent_direct",
        "ESM26-CME": "us_equity_index_broad",
        "MESM26-CME": "us_equity_index_broad",
        "RTYM26-CME": "us_equity_index_broad",
        "M2KM26-CME": "us_equity_index_broad",
        "YMM26-CBOT": "dow_equity_index_broad",
        "MYMM26-CBOT": "dow_equity_index_broad",
        "TICK-NYSE": "nyse_breadth_broad",
        "VXM26-CFE": "volatility_risk_broad",
        "VXMM26-CFE": "volatility_risk_broad",
        "SIM26-COMEX": "silver_direct",
        "SILM26-COMEX": "silver_direct",
        "GCM26-COMEX": "gold_silver_metals_broad",
        "MGCM26-COMEX": "gold_silver_metals_broad",
        "XAUUSD": "gold_silver_metals_broad",
        "ZBM26-CBOT": "rates_macro_broad",
        "ZNM26-CBOT": "rates_macro_broad",
        "CLM26-NYMEX": "oil_risk_broad",
        "MCLM26-NYMEX": "oil_risk_broad",
        "BTCUSDT_PERP_BINANCE": "crypto_risk_broad",
    }
    direct = exact_map.get(source_symbol, [])
    broad = [symbol for symbol in broad_map.get(source_symbol, []) if symbol not in direct]
    relation_notes = []
    if direct:
        relation_notes.append("direct_or_named_proxy_to_route_c_symbol")
    if broad:
        relation_notes.append("broad_macro_or_market_proxy_to_route_c_symbol")
    if not direct and not broad:
        relation_notes.append("no_route_c_proxy_symbol_in_current_residual_set")
    return {
        "source_proxy_family": family_map.get(source_symbol, "unmapped_to_route_c_symbols"),
        "direct_route_c_symbols": direct,
        "broad_route_c_symbols": broad,
        "relation_notes": relation_notes,
    }


def stats_deltas(row: dict[str, Any]) -> dict[str, Any]:
    original = row.get("original_flagged_stats") or NO_STATS
    no_gap = row.get("source_gap_excluded_stats") or NO_STATS
    denom = row.get("denominator_stats") or NO_STATS
    neighbor_stats = row.get("neighbor_placebo_stats") or {}
    best_neighbor_abs = None
    best_neighbor_offset = None
    for offset, stats in neighbor_stats.items():
        value = safe_float((stats or {}).get("mean_abs_future_change"))
        if value is not None and (best_neighbor_abs is None or value > best_neighbor_abs):
            best_neighbor_abs = value
            best_neighbor_offset = offset
    return {
        "original_minus_denominator_abs_future_change": diff_float(
            original.get("mean_abs_future_change"),
            denom.get("mean_abs_future_change"),
        ),
        "no_gap_minus_denominator_abs_future_change": diff_float(
            no_gap.get("mean_abs_future_change"),
            denom.get("mean_abs_future_change"),
        ),
        "no_gap_minus_best_neighbor_abs_future_change": diff_float(
            no_gap.get("mean_abs_future_change"),
            best_neighbor_abs,
        ),
        "original_minus_denominator_delta_follow_rate": diff_float(
            original.get("future_follows_delta_sign_rate"),
            denom.get("future_follows_delta_sign_rate"),
        ),
        "original_minus_denominator_price_follow_rate": diff_float(
            original.get("future_follows_price_sign_rate"),
            denom.get("future_follows_price_sign_rate"),
        ),
        "best_neighbor_offset_by_abs_future_change": best_neighbor_offset,
        "best_neighbor_abs_future_change": best_neighbor_abs,
    }


def split_implication(bucket: str, proxy: dict[str, Any]) -> str:
    if bucket == "SURVIVES_SOURCE_GAP_AND_NEIGHBOR_DESCRIPTIVE":
        if proxy["direct_route_c_symbols"] or proxy["broad_route_c_symbols"]:
            return "descriptive_survivor_ready_for_route_c_proxy_join"
        return "descriptive_survivor_without_current_route_c_proxy_requires_source_expansion"
    if bucket == "NEIGHBOR_PLACEBO_COMPETES_WITH_FLAG":
        return "local_neighbor_placebo_competes_convert_to_generic_state_or_avoid_intelligence"
    if bucket == "SOURCE_GAP_FILTER_WEAKENS_TO_DENOMINATOR":
        return "source_gap_filter_explains_or_weakens_convert_to_source_integrity_or_avoid_logic"
    if bucket == "SOURCE_GAP_DEPENDENT_OR_UNDERPOWERED_AFTER_GAP_FILTER":
        return "gap_dependent_or_underpowered_requires_clean_contiguous_capture"
    if bucket == "UNDERPOWERED_ORIGINAL_N_LT_20":
        return "underpowered_requires_more_rows_or_forward_capture"
    return "unclassified_control_bucket_requires_manual_review"


def build_sierra_split_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], Counter[str]]:
    split_rows: list[dict[str, Any]] = []
    bucket_counts: Counter[str] = Counter()
    for index, row in enumerate(rows, 1):
        proxy = source_proxy(str(row["source_symbol"]))
        mechanism = sierra_mechanism_family(str(row["primitive_flag"]))
        bucket = str(row["gap_neighbor_control_bucket"])
        bucket_counts[bucket] += 1
        split_rows.append(
            {
                "route_id": ROUTE_ID,
                "sierra_split_id": f"SIERRA-SPLIT-{index:04d}",
                "source_symbol": row["source_symbol"],
                "source_proxy_family": proxy["source_proxy_family"],
                "direct_route_c_symbols": proxy["direct_route_c_symbols"],
                "broad_route_c_symbols": proxy["broad_route_c_symbols"],
                "proxy_relation_notes": proxy["relation_notes"],
                "session_bucket": row["session_bucket"],
                "horizon_id": row["horizon_id"],
                "primitive_flag": row["primitive_flag"],
                "sierra_mechanism_family": mechanism,
                "original_control_bucket": row.get("original_control_bucket"),
                "gap_neighbor_control_bucket": bucket,
                "split_implication": split_implication(bucket, proxy),
                "original_flagged_n": (row.get("original_flagged_stats") or {}).get("n"),
                "source_gap_excluded_n": (row.get("source_gap_excluded_stats") or {}).get("n"),
                "denominator_n": (row.get("denominator_stats") or {}).get("n"),
                "stats_deltas": stats_deltas(row),
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return split_rows, bucket_counts


def geometry_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    bucket_counts = Counter(str(row.get("geometry_comparison_bucket")) for row in rows)
    direction_counts = Counter(str(row.get("direction_family")) for row in rows)
    strongest = []
    for row in rows:
        flagged = row.get("flagged_geometry") or {}
        denom = row.get("denominator_geometry") or {}
        strongest.append(
            {
                "direction_family": row.get("direction_family"),
                "geometry_comparison_bucket": row.get("geometry_comparison_bucket"),
                "flagged_minus_denominator_final_positive_share": diff_float(
                    flagged.get("final_positive_share"),
                    denom.get("final_positive_share"),
                ),
                "flagged_minus_denominator_two_spread_favorable_first_or_only_share": diff_float(
                    flagged.get("two_spread_favorable_first_or_only_share"),
                    denom.get("two_spread_favorable_first_or_only_share"),
                ),
                "flagged_minus_denominator_mean_final_to_spread_max": diff_float(
                    flagged.get("mean_final_to_spread_max"),
                    denom.get("mean_final_to_spread_max"),
                ),
            }
        )
    return {
        "geometry_direction_rows": len(rows),
        "geometry_bucket_counts": dict(sorted(bucket_counts.items())),
        "direction_family_counts": dict(sorted(direction_counts.items())),
        "direction_deltas": strongest,
    }


def build_route_residual_rows(
    residual_rows: list[dict[str, Any]],
    transfer_rows: list[dict[str, Any]],
    geometry_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    transfer_by_queue = {row["queue_id"]: row for row in transfer_rows}
    geometry_by_queue: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in geometry_rows:
        geometry_by_queue[str(row["queue_id"])].append(row)
    out: list[dict[str, Any]] = []
    for row in residual_rows:
        queue_id = str(row["queue_id"])
        transfer = transfer_by_queue.get(queue_id, {})
        route_family = route_c_mechanism_family(str(row["primitive_flag"]))
        out.append(
            {
                "route_id": ROUTE_ID,
                "queue_id": queue_id,
                "symbol": row["symbol"],
                "session_bucket": row["session_bucket"],
                "horizon_id": row["horizon_id"],
                "primitive_flag": row["primitive_flag"],
                "route_c_mechanism_family": route_family,
                "placebo_bucket": row.get("placebo_bucket"),
                "flagged_n": row.get("flagged_n"),
                "neighbor_n": row.get("neighbor_n"),
                "rotated_placebo_n": row.get("rotated_placebo_n"),
                "flagged_minus_neighbor_abs_change": row.get("flagged_minus_neighbor_abs_change"),
                "flagged_minus_rotated_placebo_abs_change": row.get("flagged_minus_rotated_placebo_abs_change"),
                "flagged_delta_alignment_rate": row.get("flagged_delta_alignment_rate"),
                "residual_transfer_class": transfer.get("residual_transfer_class"),
                "full_control_bucket": transfer.get("full_control_bucket"),
                "movement_status": transfer.get("movement_status"),
                "same_session_horizon_transfer_pattern": transfer.get("same_session_horizon_transfer_pattern"),
                "same_horizon_session_transfer_pattern": transfer.get("same_horizon_session_transfer_pattern"),
                "geometry_summary": geometry_summary(geometry_by_queue.get(queue_id, [])),
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return out


def relation_for(split_row: dict[str, Any], route_row: dict[str, Any]) -> str | None:
    symbol = str(route_row["symbol"])
    if symbol in split_row["direct_route_c_symbols"]:
        return "direct_proxy"
    if symbol in split_row["broad_route_c_symbols"]:
        return "broad_proxy"
    return None


def join_bucket(
    split_row: dict[str, Any],
    route_row: dict[str, Any],
    relation: str,
    same_session: bool,
    same_horizon: bool,
    compatible: bool,
) -> str:
    if same_session and same_horizon and compatible:
        suffix = "SAME_SESSION_HORIZON_MECHANISM"
    elif same_session and same_horizon:
        suffix = "SAME_SESSION_HORIZON_DIFFERENT_MECHANISM"
    elif compatible:
        suffix = "CROSS_SESSION_OR_HORIZON_MECHANISM"
    else:
        suffix = "CROSS_SESSION_OR_HORIZON_CONTEXT"
    return f"{relation.upper()}_{suffix}"


def join_implication(split_row: dict[str, Any], route_row: dict[str, Any], bucket: str) -> str:
    sierra_bucket = split_row["gap_neighbor_control_bucket"]
    route_transfer = route_row.get("residual_transfer_class")
    if sierra_bucket == "SURVIVES_SOURCE_GAP_AND_NEIGHBOR_DESCRIPTIVE" and "SAME_SESSION_HORIZON" in bucket:
        if route_transfer and "WEAKENED" not in str(route_transfer):
            return "cross_source_descriptive_triangulation_needs_replay_not_promotion"
        return "sierra_survives_but_route_c_transfer_weakened_split_before_candidate"
    if sierra_bucket == "SURVIVES_SOURCE_GAP_AND_NEIGHBOR_DESCRIPTIVE":
        return "sierra_survives_proxy_family_but_alignment_missing_requires_exact_capture"
    if sierra_bucket == "NEIGHBOR_PLACEBO_COMPETES_WITH_FLAG":
        return "sierra_neighbor_placebo_competes_route_c_should_not_inherit_without_unique_control"
    if sierra_bucket.startswith("SOURCE_GAP"):
        return "sierra_source_gap_weakness_route_c_requires_source_integrity_control"
    if sierra_bucket == "UNDERPOWERED_ORIGINAL_N_LT_20":
        return "sierra_underpowered_route_c_match_is_capture_requirement_only"
    return "descriptive_proxy_context_only"


def build_proxy_join_rows(
    split_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    join_rows: list[dict[str, Any]] = []
    summary_counter: Counter[tuple[str, str, str, str, str, str, str]] = Counter()
    for split in split_rows:
        for route in route_rows:
            relation = relation_for(split, route)
            if relation is None:
                continue
            same_session = split["session_bucket"] == route["session_bucket"]
            same_horizon = split["horizon_id"] == route["horizon_id"]
            compatible = mechanism_compatible(split["sierra_mechanism_family"], route["route_c_mechanism_family"])
            bucket = join_bucket(split, route, relation, same_session, same_horizon, compatible)
            summary_key = (
                split["gap_neighbor_control_bucket"],
                split["source_proxy_family"],
                relation,
                bucket,
                str(route["symbol"]),
                str(route["route_c_mechanism_family"]),
                str(split["sierra_mechanism_family"]),
            )
            summary_counter[summary_key] += 1
            join_rows.append(
                {
                    "route_id": ROUTE_ID,
                    "sierra_split_id": split["sierra_split_id"],
                    "source_symbol": split["source_symbol"],
                    "source_proxy_family": split["source_proxy_family"],
                    "proxy_relation": relation,
                    "join_bucket": bucket,
                    "same_session": same_session,
                    "same_horizon": same_horizon,
                    "mechanism_compatible": compatible,
                    "sierra_session_bucket": split["session_bucket"],
                    "sierra_horizon_id": split["horizon_id"],
                    "sierra_primitive_flag": split["primitive_flag"],
                    "sierra_mechanism_family": split["sierra_mechanism_family"],
                    "sierra_gap_neighbor_control_bucket": split["gap_neighbor_control_bucket"],
                    "sierra_stats_deltas": split["stats_deltas"],
                    "route_c_queue_id": route["queue_id"],
                    "route_c_symbol": route["symbol"],
                    "route_c_session_bucket": route["session_bucket"],
                    "route_c_horizon_id": route["horizon_id"],
                    "route_c_primitive_flag": route["primitive_flag"],
                    "route_c_mechanism_family": route["route_c_mechanism_family"],
                    "route_c_placebo_bucket": route["placebo_bucket"],
                    "route_c_residual_transfer_class": route["residual_transfer_class"],
                    "route_c_full_control_bucket": route["full_control_bucket"],
                    "route_c_geometry_bucket_counts": route["geometry_summary"]["geometry_bucket_counts"],
                    "join_implication": join_implication(split, route, bucket),
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "safe_flags": SAFE_FLAGS,
                }
            )
    summary_rows: list[dict[str, Any]] = []
    for key, count in sorted(summary_counter.items()):
        (
            sierra_bucket,
            source_proxy_family,
            relation,
            bucket,
            route_symbol,
            route_family,
            sierra_family,
        ) = key
        summary_rows.append(
            {
                "route_id": ROUTE_ID,
                "sierra_gap_neighbor_control_bucket": sierra_bucket,
                "source_proxy_family": source_proxy_family,
                "proxy_relation": relation,
                "join_bucket": bucket,
                "route_c_symbol": route_symbol,
                "route_c_mechanism_family": route_family,
                "sierra_mechanism_family": sierra_family,
                "row_count": count,
                "evidence_boundary": "proxy join summary only; no validation or promotion",
                "safe_flags": SAFE_FLAGS,
            }
        )
    return join_rows, summary_rows


def failure_next_action(bucket: str) -> str:
    if bucket == "SURVIVES_SOURCE_GAP_AND_NEIGHBOR_DESCRIPTIVE":
        return "split by proxy family and require aligned replay/forward capture before candidate logic"
    if bucket == "NEIGHBOR_PLACEBO_COMPETES_WITH_FLAG":
        return "test as generic local volatility/path-state descriptor or avoid duplicate signal claims"
    if bucket == "SOURCE_GAP_FILTER_WEAKENS_TO_DENOMINATOR":
        return "convert to source-gap integrity screen and avoid using gap-adjacent rows as signal evidence"
    if bucket == "SOURCE_GAP_DEPENDENT_OR_UNDERPOWERED_AFTER_GAP_FILTER":
        return "collect contiguous non-gap rows or prove insufficiency for this source/session/horizon"
    if bucket == "UNDERPOWERED_ORIGINAL_N_LT_20":
        return "route to more data or forward capture; do not interpret directionally"
    return "manual classification required"


def build_failure_rows(split_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str, str], dict[str, Any]] = {}
    for row in split_rows:
        key = (
            row["gap_neighbor_control_bucket"],
            row["source_proxy_family"],
            row["sierra_mechanism_family"],
            row["session_bucket"],
            row["horizon_id"],
            "has_route_c_proxy"
            if row["direct_route_c_symbols"] or row["broad_route_c_symbols"]
            else "no_current_route_c_proxy",
        )
        stats = grouped.setdefault(
            key,
            {
                "row_count": 0,
                "source_symbols": Counter(),
                "primitive_flags": Counter(),
                "direct_route_c_symbols": set(),
                "broad_route_c_symbols": set(),
            },
        )
        stats["row_count"] += 1
        stats["source_symbols"][row["source_symbol"]] += 1
        stats["primitive_flags"][row["primitive_flag"]] += 1
        stats["direct_route_c_symbols"].update(row["direct_route_c_symbols"])
        stats["broad_route_c_symbols"].update(row["broad_route_c_symbols"])
    out: list[dict[str, Any]] = []
    for key, stats in sorted(grouped.items()):
        bucket, proxy_family, mechanism, session, horizon, proxy_status = key
        out.append(
            {
                "route_id": ROUTE_ID,
                "gap_neighbor_control_bucket": bucket,
                "source_proxy_family": proxy_family,
                "sierra_mechanism_family": mechanism,
                "session_bucket": session,
                "horizon_id": horizon,
                "route_c_proxy_status": proxy_status,
                "row_count": stats["row_count"],
                "source_symbol_counts": dict(sorted(stats["source_symbols"].items())),
                "primitive_flag_counts": dict(sorted(stats["primitive_flags"].items())),
                "direct_route_c_symbols": sorted(stats["direct_route_c_symbols"]),
                "broad_route_c_symbols": sorted(stats["broad_route_c_symbols"]),
                "failure_or_survivor_intelligence": split_implication(bucket, {
                    "direct_route_c_symbols": sorted(stats["direct_route_c_symbols"]),
                    "broad_route_c_symbols": sorted(stats["broad_route_c_symbols"]),
                }),
                "next_same_resource_action": failure_next_action(bucket),
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return out


def build_questions(
    split_rows: list[dict[str, Any]],
    join_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    split_buckets = Counter(row["gap_neighbor_control_bucket"] for row in split_rows)
    for bucket, count in sorted(split_buckets.items()):
        questions.append(
            {
                "route_id": ROUTE_ID,
                "question_id": f"SIERRA_ROUTE_C_BUCKET_{bucket}",
                "question": f"What should be done with all {count} Sierra rows in bucket {bucket}?",
                "next_action": failure_next_action(bucket),
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    survivor_same_aligned = [
        row
        for row in join_rows
        if row["sierra_gap_neighbor_control_bucket"] == "SURVIVES_SOURCE_GAP_AND_NEIGHBOR_DESCRIPTIVE"
        and row["same_session"]
        and row["same_horizon"]
        and row["mechanism_compatible"]
    ]
    questions.append(
        {
            "route_id": ROUTE_ID,
            "question_id": "SIERRA_ROUTE_C_ALIGNED_SURVIVOR_REPLAY",
            "question": "Which exact aligned Sierra/Route C proxy joins deserve event-level replay rather than aggregate descriptor comparison?",
            "next_action": "Build event-level aligned replay for every same-session/horizon/mechanism-compatible survivor proxy join; do not select a top subset.",
            "aligned_survivor_join_rows": len(survivor_same_aligned),
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        }
    )
    no_proxy_groups = [row for row in failure_rows if row["route_c_proxy_status"] == "no_current_route_c_proxy"]
    questions.append(
        {
            "route_id": ROUTE_ID,
            "question_id": "SIERRA_SURVIVOR_SOURCE_EXPANSION",
            "question": "Which Sierra source families have no current Route C residual proxy but may still matter to GTOS?",
            "next_action": "Route every no-proxy family into either new Route C symbol extraction, cross-market proxy design, or exact no-current-symbol reason.",
            "no_proxy_group_rows": len(no_proxy_groups),
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        }
    )
    return questions


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_route_c_survivor_join_builder", "created"),
        (RESULT_PATH, "sierra_route_c_survivor_join_result", "created"),
        (SIERRA_SPLIT_LEDGER, "sierra_route_c_survivor_split_ledger", "created"),
        (ROUTE_RESIDUAL_FAMILY_LEDGER, "sierra_route_c_residual_family_ledger", "created"),
        (PROXY_JOIN_LEDGER, "sierra_route_c_proxy_join_ledger", "created"),
        (PROXY_JOIN_SUMMARY_LEDGER, "sierra_route_c_proxy_join_summary_ledger", "created"),
        (FAILURE_INTELLIGENCE_LEDGER, "sierra_route_c_failure_intelligence_ledger", "created"),
        (QUESTION_LEDGER, "sierra_route_c_survivor_join_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_route_c_survivor_join_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], bucket_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_route_c_survivor_join",
        "status": "done",
        "route": "sierra_source_contract_repair",
        "details": "Split all Sierra neighbor/gap control rows and joined every proxy-related row to all Route C residual descriptors without arbitrary top-N selection.",
        "counts": counts,
        "bucket_counts": bucket_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(SIERRA_SPLIT_LEDGER),
            relative(ROUTE_RESIDUAL_FAMILY_LEDGER),
            relative(PROXY_JOIN_LEDGER),
            relative(PROXY_JOIN_SUMMARY_LEDGER),
            relative(FAILURE_INTELLIGENCE_LEDGER),
            relative(QUESTION_LEDGER),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], bucket_counts: dict[str, int]) -> None:
    lines = [
        "# Sierra to Route C Survivor Join",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: proxy-family split/join diagnostics only. No strategy validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Sierra Buckets", ""])
    for key, value in sorted(bucket_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Same-Resource Next Work",
            "",
            "- Build event-level aligned replay for every same-session/horizon/mechanism-compatible survivor proxy join.",
            "- Convert neighbor-placebo-competing Sierra rows into generic-state or avoid-filter intelligence instead of discarding them.",
            "- Route no-proxy Sierra survivor/source families into source expansion or exact current-symbol impossibility rows.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    sierra_rows = read_jsonl(SIERRA_CONTROL_LEDGER)
    residual_rows = read_jsonl(ROUTE_C_RESIDUAL_LEDGER)
    transfer_rows = read_jsonl(ROUTE_C_TRANSFER_LEDGER)
    geometry_rows = read_jsonl(ROUTE_C_GEOMETRY_LEDGER)

    split_rows, bucket_counts = build_sierra_split_rows(sierra_rows)
    route_rows = build_route_residual_rows(residual_rows, transfer_rows, geometry_rows)
    join_rows, join_summary_rows = build_proxy_join_rows(split_rows, route_rows)
    failure_rows = build_failure_rows(split_rows)
    question_rows = build_questions(split_rows, join_rows, failure_rows)

    write_jsonl(SIERRA_SPLIT_LEDGER, split_rows)
    write_jsonl(ROUTE_RESIDUAL_FAMILY_LEDGER, route_rows)
    write_jsonl(PROXY_JOIN_LEDGER, join_rows)
    write_jsonl(PROXY_JOIN_SUMMARY_LEDGER, join_summary_rows)
    write_jsonl(FAILURE_INTELLIGENCE_LEDGER, failure_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)

    join_bucket_counts = Counter(row["join_bucket"] for row in join_rows)
    survivor_aligned_join_rows = sum(
        1
        for row in join_rows
        if row["sierra_gap_neighbor_control_bucket"] == "SURVIVES_SOURCE_GAP_AND_NEIGHBOR_DESCRIPTIVE"
        and row["same_session"]
        and row["same_horizon"]
        and row["mechanism_compatible"]
    )
    counts = {
        "sierra_control_rows": len(sierra_rows),
        "sierra_split_rows": len(split_rows),
        "sierra_survivor_rows": bucket_counts.get("SURVIVES_SOURCE_GAP_AND_NEIGHBOR_DESCRIPTIVE", 0),
        "route_c_residual_rows": len(route_rows),
        "route_c_geometry_rows": len(geometry_rows),
        "proxy_join_rows": len(join_rows),
        "proxy_join_summary_rows": len(join_summary_rows),
        "failure_intelligence_rows": len(failure_rows),
        "question_rows": len(question_rows),
        "survivor_same_session_horizon_mechanism_join_rows": survivor_aligned_join_rows,
    }
    result = {
        "schema": "sierra_route_c_survivor_join_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_ROUTE_C_PROXY_FAMILY_JOIN_DIAGNOSTIC_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "sierra_gap_neighbor_bucket_counts": dict(sorted(bucket_counts.items())),
        "proxy_join_bucket_counts": dict(sorted(join_bucket_counts.items())),
        "next_same_resource_work": [
            "event-level aligned replay for every same-session/horizon/mechanism-compatible survivor proxy join",
            "source expansion/impossibility routing for no-proxy Sierra survivor families",
            "generic-state and avoid-filter tests for neighbor-placebo-competing rows",
        ],
        "not_completion": "This join deepens Route C/Sierra diagnostics but does not complete the 60-hour objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, dict(bucket_counts))
    write_summary(generated_utc, counts, dict(bucket_counts))
    print(json.dumps({"ok": True, "counts": counts, "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
