"""Supplemental expanded-market proxy-R performance over reachable local sources."""

from __future__ import annotations

import os
import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

from src.research_infra.moonshot_expanded_market_proxy_r_performance import (
    as_float,
    cost_proxy_for_symbol,
    parse_dt,
    rounded,
    score_source_session_horizon,
    sha256_file,
)


EXPANDED_MARKET_SUPPLEMENTAL_SOURCE_PERFORMANCE_SURFACE = (
    "src/research_infra/moonshot_expanded_market_supplemental_source_performance.py"
)
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"
SUPPLEMENTAL_SESSIONS = ("ALL_SESSIONS", "tokyo_kz", "london_core", "ny_core", "off_core_session")
SUPPLEMENTAL_HORIZONS = ("h4", "h16", "h32")
SUPPLEMENTAL_SIDES = ("LONG", "SHORT")


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
    output["expanded_market_supplemental_source_performance_surface"] = (
        EXPANDED_MARKET_SUPPLEMENTAL_SOURCE_PERFORMANCE_SURFACE
    )
    output["research_boundary"] = research_boundary()
    return output


def average(values: list[float]) -> float | None:
    return mean(values) if values else None


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def long_path(path: Path) -> str:
    text = str(path)
    if os.name == "nt" and len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def row_digest(parts: list[Any]) -> str:
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def source_bound_m15_rows(repo_root: Path, source_path: str) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    path = repo_root / source_path
    file_hash = sha256_file(path)
    grouped: dict[str, list[dict[str, Any]]] = {}
    rows_streamed = 0
    if not path.exists():
        return [], {}

    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows_streamed += 1
            raw = json.loads(line)
            symbol = normalized(raw.get("source_symbol"))
            open_value = as_float(raw.get("open"))
            high_value = as_float(raw.get("high"))
            low_value = as_float(raw.get("low"))
            close_value = as_float(raw.get("close"))
            start_time = raw.get("bar_start_utc")
            if not symbol or None in (open_value, high_value, low_value, close_value):
                continue
            grouped.setdefault(symbol, []).append(
                {
                    "time": start_time,
                    "dt": parse_dt(start_time),
                    "open": open_value,
                    "high": high_value,
                    "low": low_value,
                    "close": close_value,
                    "source_audit_key": raw.get("source_audit_key"),
                    "source_records": raw.get("source_records"),
                }
            )

    source_rows: list[dict[str, Any]] = []
    for symbol, rows in sorted(grouped.items()):
        rows.sort(key=lambda item: (item.get("dt") is None, item.get("dt"), item.get("time") or ""))
        first_time = rows[0].get("time") if rows else None
        last_time = rows[-1].get("time") if rows else None
        audit_keys = {row.get("source_audit_key") for row in rows if row.get("source_audit_key")}
        source_rows.append(
            boundary_row(
                {
                    "supplemental_source_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-SUPP-SOURCE-{len(source_rows) + 1:04d}"
                    ),
                    "source_family": "sierra_scid_source_bound_m15",
                    "source_path": source_path,
                    "source_file_sha256": file_hash,
                    "source_symbol": symbol,
                    "symbol": symbol,
                    "source_timeframe": "M15",
                    "market_timeframe": "M15",
                    "source_access_status": "SIERRA_SOURCE_BOUND_M15_BARS_REACHABLE",
                    "source_rows_streamed": rows_streamed,
                    "source_parsed_ohlc_rows": len(rows),
                    "source_first_time": first_time,
                    "source_last_time": last_time,
                    "source_record_selector": f"source_symbol={symbol}",
                    "source_record_selector_sha256": row_digest([source_path, symbol, len(rows), first_time, last_time]),
                    "source_audit_key_count": len(audit_keys),
                }
            )
        )
    return source_rows, grouped


def copy_seed_floor_performance_rows(rows: list[dict[str, Any]], sequence_start: int = 1) -> list[dict[str, Any]]:
    copied: list[dict[str, Any]] = []
    for index, row in enumerate(rows, sequence_start):
        output = {
            "expanded_market_supplemental_performance_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SUPP-PERF-{index:07d}"
            ),
            "performance_source_family": "cp216_seed_floor_ohlc_csv",
            "input_expanded_market_performance_row_id": row.get("expanded_market_performance_row_id"),
            "input_supplemental_source_row_id": None,
            "source_component": row.get("seed_source_component") or row.get("source_component"),
            "symbol": row.get("symbol"),
            "source_symbol": row.get("source_symbol"),
            "market_timeframe": row.get("market_timeframe"),
            "route_session": row.get("route_session"),
            "horizon_id": row.get("horizon_id"),
            "side": row.get("side"),
            "source_path": row.get("source_path"),
            "source_file_sha256": row.get("source_file_sha256"),
            "source_record_selector": row.get("input_market_population_row_id")
            or row.get("input_expansion_matrix_row_id"),
            "source_access_status": row.get("source_access_status"),
            "source_rows_streamed": row.get("source_rows_streamed"),
            "source_parsed_ohlc_rows": row.get("source_parsed_ohlc_rows"),
            "source_first_time": row.get("source_first_time"),
            "source_last_time": row.get("source_last_time"),
            "score_status": row.get("score_status"),
            "entry_reference": row.get("entry_reference"),
            "entry_reference_time": row.get("entry_reference_time"),
            "proxy_entry_price": row.get("proxy_entry_price"),
            "proxy_denominator_price": row.get("proxy_denominator_price"),
            "proxy_target_price": row.get("proxy_target_price"),
            "proxy_stop_price": row.get("proxy_stop_price"),
            "path_order_result": row.get("path_order_result"),
            "path_order_counts": row.get("path_order_counts") or {},
            "fill_status": row.get("fill_status"),
            "gross_simulated_r": row.get("gross_simulated_r"),
            "cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
            "stress_simulated_r": row.get("stress_simulated_r"),
            "cost_adjustment_r": row.get("cost_adjustment_r"),
            "stress_cost_adjustment_r": row.get("stress_cost_adjustment_r"),
            "cost_proxy_status": row.get("cost_proxy_status"),
            "cost_proxy_symbol": row.get("cost_proxy_symbol"),
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
            "missing_simulated_fields": []
            if row.get("gross_simulated_r") is not None
            and row.get("cost_adjusted_simulated_r") is not None
            and row.get("stress_simulated_r") is not None
            else ["gross_cost_or_stress_simulated_r"],
            "follow_inverse_default_off_avoid_class": row.get("follow_inverse_default_off_avoid_class"),
            "keep_kill_redesign_implement_decision": row.get("keep_kill_redesign_implement_decision"),
        }
        copied.append(boundary_row(output))
    return copied


def noncomputable_score_fields(score: dict[str, Any]) -> list[str]:
    status = normalized(score.get("score_status"))
    if status == "NO_ELIGIBLE_SESSION_HORIZON_ENTRIES":
        return ["eligible_session_horizon_entries"]
    if status == "SOURCE_UNDER_HORIZON_LENGTH":
        return ["source_rows_beyond_horizon"]
    if status == "SOURCE_DENOMINATOR_RANGE_UNAVAILABLE":
        return ["proxy_denominator_price"]
    if status == "HORIZON_NOT_NUMERIC":
        return ["numeric_horizon_id"]
    return ["gross_cost_or_stress_simulated_r"]


def supplemental_performance_row_from_score(
    source: dict[str, Any],
    session: str,
    horizon_id: str,
    side: str,
    score: dict[str, Any],
    sequence: int,
) -> dict[str, Any]:
    scored = (
        score.get("gross_simulated_r") is not None
        and score.get("cost_adjusted_simulated_r") is not None
        and score.get("stress_simulated_r") is not None
    )
    decision = score.get("keep_kill_redesign_implement_decision")
    class_name = score.get("follow_inverse_default_off_avoid_class")
    if not scored:
        decision = "REDESIGN_EXPANDED_MARKET_SUPPLEMENTAL_REPLAY_IMPLEMENTATION"
        class_name = "redesign"
    row = {
        "expanded_market_supplemental_performance_row_id": (
            f"OHLC-GTOS-EXPANDED-MARKET-SUPP-PERF-{sequence:07d}"
        ),
        "performance_source_family": "sierra_scid_source_bound_m15",
        "input_expanded_market_performance_row_id": None,
        "input_supplemental_source_row_id": source.get("supplemental_source_row_id"),
        "source_component": "sierra_scid_source_bound_m15_bar_replay",
        "symbol": source.get("symbol"),
        "source_symbol": source.get("source_symbol"),
        "market_timeframe": "M15",
        "route_session": session,
        "horizon_id": horizon_id,
        "side": side,
        "source_path": source.get("source_path"),
        "source_file_sha256": source.get("source_file_sha256"),
        "source_record_selector": source.get("source_record_selector"),
        "source_record_selector_sha256": source.get("source_record_selector_sha256"),
        "source_access_status": source.get("source_access_status"),
        "source_rows_streamed": source.get("source_rows_streamed"),
        "source_parsed_ohlc_rows": source.get("source_parsed_ohlc_rows"),
        "source_first_time": source.get("source_first_time"),
        "source_last_time": source.get("source_last_time"),
        "score_status": score.get("score_status"),
        "entry_reference": score.get("entry_reference"),
        "entry_reference_time": score.get("entry_reference_time"),
        "proxy_entry_price": score.get("proxy_entry_price"),
        "proxy_denominator_price": score.get("proxy_denominator_price"),
        "proxy_target_price": score.get("proxy_target_price"),
        "proxy_stop_price": score.get("proxy_stop_price"),
        "path_order_result": score.get("path_order_result") or "NO_SCOREABLE_REPLAY_PATH",
        "path_order_counts": score.get("path_order_counts") or {},
        "fill_status": score.get("fill_status") or "NO_FILL_NO_SCOREABLE_REPLAY_PATH",
        "gross_simulated_r": score.get("gross_simulated_r"),
        "cost_adjusted_simulated_r": score.get("cost_adjusted_simulated_r"),
        "stress_simulated_r": score.get("stress_simulated_r"),
        "cost_adjustment_r": score.get("cost_adjustment_r"),
        "stress_cost_adjustment_r": score.get("stress_cost_adjustment_r"),
        "cost_proxy_status": score.get("cost_proxy_status"),
        "cost_proxy_symbol": score.get("cost_proxy_symbol"),
        "win_count": int(score.get("win_count") or 0),
        "loss_count": int(score.get("loss_count") or 0),
        "zero_count": int(score.get("zero_count") or 0),
        "target_first_count": int(score.get("target_first_count") or 0),
        "stop_first_count": int(score.get("stop_first_count") or 0),
        "neither_count": int(score.get("neither_count") or 0),
        "ambiguous_count": int(score.get("ambiguous_count") or 0),
        "effective_n": int(score.get("effective_n") or 0),
        "duplicate_row_count": int(score.get("duplicate_row_count") or 0),
        "effective_n_after_duplicate_collapse": int(score.get("effective_n_after_duplicate_collapse") or 0),
        "concentration_top_month_share": score.get("concentration_top_month_share"),
        "missing_simulated_fields": [] if scored else noncomputable_score_fields(score),
        "follow_inverse_default_off_avoid_class": class_name,
        "keep_kill_redesign_implement_decision": decision,
    }
    return boundary_row(row)


def supplemental_performance_rows(
    source_rows: list[dict[str, Any]],
    grouped_bars: dict[str, list[dict[str, Any]]],
    cost_by_symbol: dict[str, dict[str, Any]],
    sequence_start: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    sequence = sequence_start
    for source in source_rows:
        source_payload = {
            "source_symbol": source.get("source_symbol"),
            "source_timeframe": source.get("source_timeframe"),
        }
        bars = grouped_bars.get(normalized(source.get("source_symbol")), [])
        cost_proxy = cost_proxy_for_symbol(normalized(source.get("symbol")), cost_by_symbol)
        for session in SUPPLEMENTAL_SESSIONS:
            for horizon_id in SUPPLEMENTAL_HORIZONS:
                for side in SUPPLEMENTAL_SIDES:
                    score = score_source_session_horizon(source_payload, bars, session, horizon_id, side, cost_proxy)
                    rows.append(supplemental_performance_row_from_score(source, session, horizon_id, side, score, sequence))
                    sequence += 1
    return rows


def aggregate_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        normalized(row.get("performance_source_family")),
        normalized(row.get("symbol")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("side")),
        normalized(row.get("source_component")),
        normalized(row.get("follow_inverse_default_off_avoid_class")),
    )


def aggregate_supplemental_performance_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(aggregate_key(row), []).append(row)
    total_effective = sum(int(row.get("effective_n") or 0) for row in rows) or 1
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        gross = [value for value in (as_float(row.get("gross_simulated_r")) for row in members) if value is not None]
        cost = [
            value
            for value in (as_float(row.get("cost_adjusted_simulated_r")) for row in members)
            if value is not None
        ]
        stress = [value for value in (as_float(row.get("stress_simulated_r")) for row in members) if value is not None]
        wins = [value for value in cost if value > 0]
        losses = [value for value in cost if value < 0]
        decisions = Counter(normalized(row.get("keep_kill_redesign_implement_decision")) for row in members)
        path_counts: Counter[str] = Counter()
        for row in members:
            for path, count in (row.get("path_order_counts") or {}).items():
                path_counts[path] += int(count)
        effective_n = sum(int(row.get("effective_n") or 0) for row in members)
        output.append(
            boundary_row(
                {
                    "expanded_market_supplemental_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-SUPP-AGG-{len(output) + 1:06d}"
                    ),
                    "performance_source_family": key[0],
                    "symbol": key[1],
                    "market_timeframe": key[2],
                    "route_session": key[3],
                    "horizon_id": key[4],
                    "side": key[5],
                    "source_component": key[6],
                    "follow_inverse_default_off_avoid_class": key[7],
                    "row_count": len(members),
                    "source_path_count": len({row.get("source_path") for row in members}),
                    "simulated_r_row_count": len(cost),
                    "missing_simulated_row_count": len(members) - len(cost),
                    "effective_n": effective_n,
                    "duplicate_row_count": sum(int(row.get("duplicate_row_count") or 0) for row in members),
                    "effective_n_after_duplicate_collapse": sum(
                        int(row.get("effective_n_after_duplicate_collapse") or 0) for row in members
                    ),
                    "win_count": sum(int(row.get("win_count") or 0) for row in members),
                    "loss_count": sum(int(row.get("loss_count") or 0) for row in members),
                    "zero_count": sum(int(row.get("zero_count") or 0) for row in members),
                    "target_first_count": sum(int(row.get("target_first_count") or 0) for row in members),
                    "stop_first_count": sum(int(row.get("stop_first_count") or 0) for row in members),
                    "neither_count": sum(int(row.get("neither_count") or 0) for row in members),
                    "ambiguous_count": sum(int(row.get("ambiguous_count") or 0) for row in members),
                    "expectancy_gross_simulated_r": rounded(average(gross)),
                    "expectancy_cost_adjusted_simulated_r": rounded(average(cost)),
                    "expectancy_stress_simulated_r": rounded(average(stress)),
                    "average_win": rounded(average(wins)),
                    "average_loss": rounded(average(losses)),
                    "path_order_counts": dict(sorted(path_counts.items())),
                    "decision_counts": dict(sorted(decisions.items())),
                    "concentration_share_of_all_effective_n": rounded(effective_n / total_effective),
                    "keep_kill_redesign_implement_decision": decisions.most_common(1)[0][0]
                    if decisions
                    else "REDESIGN_EXPANDED_MARKET_SUPPLEMENTAL_REPLAY_IMPLEMENTATION",
                }
            )
        )
    return output


def missing_simulated_field_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        missing = row.get("missing_simulated_fields") or []
        if not missing:
            continue
        output.append(
            boundary_row(
                {
                    "expanded_market_supplemental_missing_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-SUPP-MISSING-{len(output) + 1:06d}"
                    ),
                    "input_supplemental_performance_row_id": row.get(
                        "expanded_market_supplemental_performance_row_id"
                    ),
                    "performance_source_family": row.get("performance_source_family"),
                    "symbol": row.get("symbol"),
                    "market_timeframe": row.get("market_timeframe"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "side": row.get("side"),
                    "source_path": row.get("source_path"),
                    "source_file_sha256": row.get("source_file_sha256"),
                    "missing_simulated_fields": missing,
                    "score_status": row.get("score_status"),
                    "fill_status": row.get("fill_status"),
                    "keep_kill_redesign_implement_decision": row.get("keep_kill_redesign_implement_decision"),
                }
            )
        )
    return output


def system_supplemental_performance_rows(
    performance_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    missing_rows: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    seed_floor_rows = [row for row in performance_rows if row.get("performance_source_family") == "cp216_seed_floor_ohlc_csv"]
    additional_rows = [
        row for row in performance_rows if row.get("performance_source_family") == "sierra_scid_source_bound_m15"
    ]
    return [
        boundary_row(
            {
                "expanded_market_supplemental_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-SUPP-SYSTEM-0001"
                ),
                "input_seed_floor_performance_rows": len(seed_floor_rows),
                "additional_source_rows": len(source_rows),
                "additional_source_performance_rows": len(additional_rows),
                "combined_performance_rows": len(performance_rows),
                "aggregate_rows": len(aggregate_rows),
                "missing_simulated_field_rows": len(missing_rows),
                "rows_with_simulated_r": len(performance_rows) - len(missing_rows),
                "source_path_count": len({row.get("source_path") for row in performance_rows}),
                "symbol_count": len({row.get("symbol") for row in performance_rows}),
                "timeframe_count": len({row.get("market_timeframe") for row in performance_rows}),
                "total_effective_n": sum(int(row.get("effective_n") or 0) for row in performance_rows),
                "decision_counts": dict(
                    sorted(Counter(row.get("keep_kill_redesign_implement_decision") for row in performance_rows).items())
                ),
                "metadata": metadata,
            }
        )
    ]
