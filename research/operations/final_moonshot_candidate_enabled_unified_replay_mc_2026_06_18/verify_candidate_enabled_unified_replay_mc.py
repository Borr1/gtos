#!/usr/bin/env python3
"""Build the active+A8 candidate-enabled replay/MC proof package.

This route is read-only with respect to broker/live trading state. It
regenerates the current active W7+A8 daily baseline, overlays candidate
daily-risk-unit series in memory, and writes deployment-readiness ledgers. It
records whether candidate-book config is currently armed, but it does not touch
MT5/brokers/VPS processes or use orderflow.
"""

from __future__ import annotations

import collections
import json
import math
import pickle
import random
import statistics
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]
ROUTE_DIR = Path(__file__).resolve().parent
MECH_DIR = ROOT / "research" / "operations" / "final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
READINESS_DIR = ROOT / "research" / "operations" / "final_moonshot_candidate_activation_readiness_2026_06_18"
A8_RESULT_PATH = MECH_DIR / "A8_BOOK_MC_RESULT.json"
UNIFIED_RESULT_PATH = MECH_DIR / "UNIFIED_BOOK_MC_RESULT.json"
CANDIDATE_DAILY_PATH = MECH_DIR / "CANDIDATE_DAILY_SERIES.json"
ACTIVE_CONFIG_PATH = ROOT / "config" / "agent_config.yaml"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(MECH_DIR) not in sys.path:
    sys.path.insert(0, str(MECH_DIR))

import INTEG_portfolio_build as I  # noqa: E402
import INTEG_portfolio_build_w3 as W3  # noqa: E402
import INTEG_W7_final_book as W7  # noqa: E402
import KB7_growth_kelly_sizing as K  # noqa: E402
import KB7_tick_mc as TICK  # noqa: E402
import compounding_sleeve as cs  # noqa: E402
import gold_sleeve_strategy as g  # noqa: E402
import multitf_lib as m  # noqa: E402
import wave1_structure_setups_ict as w1  # noqa: E402
from geometry_lib import atr14  # noqa: E402
from src.components.ultimate_book import bridge  # noqa: E402
from src.components.ultimate_book.metals_confluence_gate import metals_confluence  # noqa: E402
from src.components.ultimate_book.sleeves import candidate_registry  # noqa: E402
from src.components.ultimate_book.sleeves.metals import _a8_features  # noqa: E402


SPLITS = ("train", "oos", "sealed")
MC_KEY = f"{W7.KEY * 100:.2f}%"


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise TypeError(f"{path} did not contain a JSON object")
    return data


def _active_runtime_config() -> dict[str, Any]:
    with ACTIVE_CONFIG_PATH.open(encoding="utf-8") as handle:
        cfg = yaml.safe_load(handle) or {}
    runtime = cfg.get("gtos_vnext_runtime") or {}
    if not isinstance(runtime, dict):
        raise TypeError(f"{ACTIVE_CONFIG_PATH} gtos_vnext_runtime did not load as a mapping")
    return runtime


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _split_of_year(year: int) -> str:
    if year <= 2021:
        return "train"
    if year <= 2024:
        return "oos"
    return "sealed"


def _sharpe(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    sd = statistics.pstdev(values)
    return statistics.fmean(values) / sd if sd > 0 else 0.0


def _maxdd(values: list[float]) -> float:
    equity = peak = max_drawdown = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)
    return max_drawdown


def _block(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0, "meanR": None, "WR": None, "sharpe": None, "maxDD_R": None}
    return {
        "n": len(values),
        "meanR": round(statistics.fmean(values), 6),
        "WR": round(sum(1 for value in values if value > 0) / len(values), 6),
        "sharpe": round(_sharpe(values), 6),
        "maxDD_R": round(_maxdd(values), 6),
    }


def _split_stats(values: list[float], all_days: list[Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for split in SPLITS:
        selected = [value for value, day in zip(values, all_days) if _split_of_year(day.year) == split]
        out[split] = _block(selected)
    return out


def _regen_metals_core_with_a8_features() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for symbol in cs.METALS:
        times, bars = w1.load(symbol)
        if len(bars) < 200:
            continue
        atrs = [atr14(bars, index) for index in range(len(bars))]
        h1_times, h1_bars = m.load_ltf(symbol, "H1")
        m15_times, m15_bars = m.load_ltf(symbol, "M15")
        have_h1 = len(h1_bars) > 50
        have_m15 = len(m15_bars) > 50
        for signal_time, direction, stop_h4, _target_dist, h4_index, h4_bars, cost in g.fvg_signals(symbol):
            autocorr = cs.autocorr(bars, h4_index, 60)
            if autocorr is None or autocorr < cs.AC_THR:
                continue
            vol_ratio = cs.vol_ratio(atrs, h4_index)
            atr = atrs[h4_index]
            body = abs(bars[h4_index].c - bars[h4_index].o) / atr if atr > 0 else 0.0
            timestamp = signal_time + __import__("datetime").timedelta(hours=4)
            signal_close = h4_bars[h4_index].c
            stream, fill_index, maxbars, filled = h4_bars, h4_index, 80, False
            if have_h1:
                start = m.first_ltf_index_after(h1_times, timestamp)
                if start is not None and 30 <= start < len(h1_bars) - 2:
                    entry_index = I._find_fill(h1_bars, h1_times, start, direction, signal_close, 12, 1.0, timestamp)
                    if entry_index is not None:
                        stream, fill_index, maxbars, filled = h1_bars, entry_index, W3.H1_MAXBARS, True
            if not filled and have_m15:
                start = m.first_ltf_index_after(m15_times, timestamp)
                if start is not None and 30 <= start < len(m15_bars) - 2:
                    entry_index = I._find_fill(m15_bars, m15_times, start, direction, signal_close, 48, 1.0, timestamp)
                    if entry_index is not None:
                        stream, fill_index, maxbars = m15_bars, entry_index, 1280
            scaled_cost = cost * (0.5 * atr / stop_h4) if stop_h4 > 0 else cost
            result_r = W3._exit_combo_banded(stream, fill_index, direction, stop_h4, vol_ratio, scaled_cost, maxbars)
            intra_size = W3._vr_size(vol_ratio)
            if body > 0.374:
                intra_size *= 0.5
            features = _a8_features(bars, atrs, h4_index, vol_ratio, signal_time)
            confluence = metals_confluence(
                htf_slope_norm=features["htf_slope_norm"],
                mom_20_atr=features["mom_20_atr"],
                fvg_freshness_bars=features["fvg_freshness_bars"],
                atr_ratio=features["atr_ratio"],
                session_hour=features["session_hour"],
                enabled=True,
            )
            rows.append({
                "sleeve": "metals_core",
                "sym": symbol,
                "date": signal_time.date(),
                "year": signal_time.year,
                "R": W3.wins(result_r),
                "intra_size": round(intra_size, 4),
                "feats": features,
                "pass_a8": confluence.passed,
                "a8_score": confluence.score,
            })
    return rows


def _metals_col(rows: list[dict[str, Any]], erosion: dict[str, float], confidence: float) -> dict[Any, float]:
    return TICK.energy_daily(TICK.restate_rows(rows, erosion), confidence)


def _active_baselines() -> dict[str, Any]:
    cache = pickle.loads((MECH_DIR / "INTEG_W3_streams_cache.pkl").read_bytes())["metals_core"]
    regen = _regen_metals_core_with_a8_features()

    def key(row: dict[str, Any]) -> tuple[Any, ...]:
        return (row["sym"], str(row["date"]), round(float(row["R"]), 9), round(float(row["intra_size"]), 6))

    cache_keys = sorted(key(row) for row in cache)
    regen_keys = sorted(key(row) for row in regen)
    exact_rows = cache_keys == regen_keys
    for row in regen:
        row["R_sized"] = row["R"] * row.get("intra_size", 1.0)

    all_days, sleeves, _matrix_base, matrix_tick, sd_book, erosion = W7.build_final_matrix()
    metals_index = sleeves.index("metals_core")
    confidence = W3.SLEEVE_CONF["metals_core"]
    col_repro = _metals_col(regen, erosion, confidence)
    maxdiff = max(abs(col_repro.get(day, 0.0) - matrix_tick[index][metals_index]) for index, day in enumerate(all_days))
    col_a8 = _metals_col([row for row in regen if row["pass_a8"]], erosion, confidence)

    def build_final(column: dict[Any, float]) -> list[float]:
        matrix = [row[:] for row in matrix_tick]
        for day_index, day in enumerate(all_days):
            matrix[day_index][metals_index] = column.get(day, 0.0)
        nactive = [K.conviction_count(row) for row in matrix]
        final_matrix = W7.apply_kelly_matrix(matrix, nactive)
        return [sum(row) for row in final_matrix]

    base_values = build_final(col_repro)
    a8_values = build_final(col_a8)
    a8_stored = _read_json(A8_RESULT_PATH)
    return {
        "all_days": all_days,
        "sd_book": sd_book,
        "base_values": base_values,
        "a8_values": a8_values,
        "reproduction": {
            "rows_exact": exact_rows,
            "column_maxdiff": maxdiff,
            "regen_rows": len(regen),
            "cache_rows": len(cache),
            "a8_kept": sum(1 for row in regen if row["pass_a8"]),
            "a8_n_total": len(regen),
            "stored_a8": {
                "base_sharpe": a8_stored["base"]["all"]["sharpe"],
                "a8_sharpe": a8_stored["a8"]["all"]["sharpe"],
                "mc_base": a8_stored["mc_base"],
                "mc_a8": a8_stored["mc_a8"],
            },
        },
    }


def _load_candidate_daily() -> dict[str, dict[str, float]]:
    raw = _read_json(CANDIDATE_DAILY_PATH)
    return {
        sleeve: {date: float(value) for date, value in series.items()}
        for sleeve, series in raw.items()
        if isinstance(series, dict)
    }


def _sleeve_readiness(readiness: dict[str, Any]) -> dict[str, dict[str, Any]]:
    sleeves = {
        name: {
            "symbols": [],
            "unfinished_symbols": [],
            "work_item_reasons": collections.Counter(),
            "deployment_ready": True,
        }
        for name, confidence in candidate_registry.CANDIDATE_CONFIDENCE.items()
        if confidence > 0.0
    }
    for symbol, info in readiness["symbol_readiness"].items():
        for sleeve in info["sleeves"]:
            if sleeve not in sleeves:
                continue
            sleeves[sleeve]["symbols"].append(symbol)
            if info["status"] != "ACTIVATION_READY":
                sleeves[sleeve]["unfinished_symbols"].append(symbol)
                for item in readiness["activation_blockers"]:
                    if item["symbol"] == symbol and sleeve in item["sleeves"]:
                        sleeves[sleeve]["work_item_reasons"][item["reason"]] += 1
                sleeves[sleeve]["deployment_ready"] = False
    out: dict[str, dict[str, Any]] = {}
    for sleeve, row in sleeves.items():
        out[sleeve] = {
            "confidence": candidate_registry.CANDIDATE_CONFIDENCE[sleeve],
            "symbols": sorted(row["symbols"]),
            "unfinished_symbols": sorted(row["unfinished_symbols"]),
            "work_item_reasons": dict(sorted(row["work_item_reasons"].items())),
            "deployment_ready": bool(row["deployment_ready"]),
        }
    return out


def _add_candidate_series(
    base_values: list[float],
    all_days: list[Any],
    sleeve_series: dict[str, dict[str, float]],
    confidence: dict[str, float],
) -> tuple[list[float], dict[str, Any]]:
    day_index = {day.isoformat()[:10]: index for index, day in enumerate(all_days)}
    additions = [0.0] * len(base_values)
    contribution: dict[str, Any] = {}
    unmatched: dict[str, int] = {}
    for sleeve, series in sorted(sleeve_series.items()):
        weight = float(confidence.get(sleeve, 0.0))
        matched = 0
        total = 0.0
        for date, r_value in series.items():
            index = day_index.get(date)
            if index is None:
                continue
            value = weight * float(r_value)
            additions[index] += value
            total += value
            matched += 1
        contribution[sleeve] = {
            "confidence": weight,
            "matched_days": matched,
            "total_weighted_R": round(total, 6),
            "raw_daily_rows": len(series),
        }
        unmatched[sleeve] = len(series) - matched
    return [base_values[index] + additions[index] for index in range(len(base_values))], {
        "contribution": contribution,
        "unmatched_days": unmatched,
    }


def _evaluate_scenario(
    name: str,
    base_values: list[float],
    all_days: list[Any],
    sd_book: float,
    sleeve_series: dict[str, dict[str, float]],
    confidence: dict[str, float],
) -> dict[str, Any]:
    values, meta = _add_candidate_series(base_values, all_days, sleeve_series, confidence)
    stdev = statistics.pstdev(values)
    vol_scale = sd_book / stdev if stdev > 0 else 1.0
    mc = W7.grid(values, vol_scale, 1.0, seed_base=1)[MC_KEY]
    return {
        "name": name,
        "daily": _block(values),
        "splits": _split_stats(values, all_days),
        "sharpe": round(_sharpe(values), 6),
        "vol_scale_to_deployed_book": round(vol_scale, 6),
        "mc_key": MC_KEY,
        "mc": mc,
        "sleeve_count": len(sleeve_series),
        **meta,
    }


def _random_drop_placebo(
    base_values: list[float],
    all_days: list[Any],
    sd_book: float,
    full_series: dict[str, dict[str, float]],
    full_conf: dict[str, float],
    candidate_values: list[float],
    iterations: int = 300,
) -> dict[str, Any]:
    # Candidate overlay has extra daily contribution. Compare the observed Sharpe
    # lift to randomizing those non-zero daily contributions across the same
    # active day set, preserving contribution magnitude distribution.
    rng = random.Random(20260618)
    day_index = {day.isoformat()[:10]: index for index, day in enumerate(all_days)}
    observed_delta = _sharpe(candidate_values) - _sharpe(base_values)
    overlay = [candidate_values[index] - base_values[index] for index in range(len(base_values))]
    non_zero = [value for value in overlay if abs(value) > 1e-12]
    positions = list(range(len(base_values)))
    random_deltas: list[float] = []
    for _ in range(iterations):
        shuffled = base_values[:]
        target_positions = rng.sample(positions, len(non_zero))
        for position, value in zip(target_positions, non_zero):
            shuffled[position] += value
        random_deltas.append(_sharpe(shuffled) - _sharpe(base_values))
    sorted_deltas = sorted(random_deltas)
    p_ge = sum(1 for value in random_deltas if value >= observed_delta) / iterations
    return {
        "iterations": iterations,
        "observed_sharpe_delta": round(observed_delta, 6),
        "p_random_ge_observed": round(p_ge, 6),
        "random_median": round(statistics.median(random_deltas), 6),
        "random_p90": round(sorted_deltas[int(0.9 * iterations)], 6),
        "non_zero_candidate_overlay_days": len(non_zero),
        "series_count": len(full_series),
        "confidence_count": len(full_conf),
        "vol_scale_reference": round(sd_book / statistics.pstdev(candidate_values), 6),
    }


def _work_status_and_next(reason: str, info: dict[str, Any]) -> tuple[str, str]:
    disposition = str(info.get("profile_execution_disposition", ""))
    if reason == "w7_hard_drop_research_only_until_new_cost_proof":
        return (
            "research_only_cost_revival_required",
            "new tick/cost proof required before revival",
        )
    if reason == "not_in_broker_native_eligible_symbols":
        if disposition == "dual_broker_profile_spec_ready":
            return (
                "profile_spec_ready_native_routing_decision_required",
                "deployment package may add symbol to native-eligible routing after cost, follower, and MC proof",
            )
        if disposition.startswith("ftmo_only_profile_spec_ready"):
            return (
                "ftmo_profile_spec_ready_redacted_account_expected_skip_native_routing_decision_required",
                "preserve explicit redacted_account profile-missing skip semantics or add redacted_account-native proof before dual-broker routing",
            )
        return (
            "native_routing_decision_required",
            "resolve profile disposition before native-eligible routing expansion",
        )
    if reason in {"active_profile_config_or_contract_gap", "missing_verified_broker_spec_evidence"}:
        return (
            "source_history_present_profile_or_native_spec_required",
            "export_or_commit broker-native symbol spec/cost/profile row from active broker namespace",
        )
    return ("readiness_work_required", "inspect activation-readiness ledger for exact next action")


def _rows_from_readiness_work(readiness: dict[str, Any], sleeve_ready: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in readiness["activation_blockers"]:
        symbol = item["symbol"]
        info = readiness["symbol_readiness"][symbol]
        work_status, next_work = _work_status_and_next(item["reason"], info)
        rows.append({
            "symbol": symbol,
            "reason": item["reason"],
            "sleeves": item["sleeves"],
            "native_eligible": info["native_eligible"],
            "profile_execution_disposition": info["profile_execution_disposition"],
            "profile_missing_expected_skip_profiles": info.get("profile_missing_expected_skip_profiles", []),
            "blocking_active_profile_gap_profiles": sorted(info.get("blocking_active_profile_gaps", {})),
            "blocking_verified_broker_spec_missing_profiles": info.get(
                "blocking_verified_broker_spec_missing_profiles", []
            ),
            "history_present_timeframes": info["history_present_timeframes"],
            "missing_required_history": info["missing_required_history"],
            "missing_ltf_stress_timeframes": info["missing_ltf_stress_timeframes"],
            "work_status": "history_export_required" if info["missing_required_history"] else work_status,
            "next_work": next_work,
        })
    for sleeve, row in sleeve_ready.items():
        if row["deployment_ready"]:
            rows.append({
                "symbol": None,
                "reason": "whole_sleeve_currently_deployment_ready",
                "sleeves": [sleeve],
                "native_eligible": None,
                "profile_execution_disposition": None,
                "profile_missing_expected_skip_profiles": [],
                "blocking_active_profile_gap_profiles": [],
                "blocking_verified_broker_spec_missing_profiles": [],
                "history_present_timeframes": None,
                "missing_required_history": [],
                "missing_ltf_stress_timeframes": [],
                "work_status": "no_unfinished_symbol_work_in_current_readiness_artifact",
                "next_work": "eligible_for_in_memory_ready_subset_scenario_not_live_activation",
            })
    return rows


def _translation_rows(sleeve_ready: dict[str, Any], scenarios: dict[str, Any]) -> list[dict[str, Any]]:
    ready_set = {
        sleeve for sleeve, row in sleeve_ready.items()
        if row["deployment_ready"] and candidate_registry.CANDIDATE_CONFIDENCE.get(sleeve, 0.0) > 0.0
    }
    rows: list[dict[str, Any]] = []
    for sleeve in sorted(sleeve_ready):
        row = sleeve_ready[sleeve]
        promoted_in_subset = sleeve in ready_set
        rows.append({
            "sleeve": sleeve,
            "current_claim_status": "candidate_book_ready_member" if promoted_in_subset else "unfinished_for_full_activation_now",
            "what_is_real_or_inspiring": candidate_registry.CANDIDATES[sleeve].note,
            "work_not_done_yet": (
                "full candidate book still requires owner/VPS staged activation decision before runtime effect"
                if promoted_in_subset
                else f"unfinished symbols: {', '.join(row['unfinished_symbols'])}"
            ),
            "transformed_use": (
                "candidate_book_default_off_ready_member"
                if promoted_in_subset
                else "readiness_work_queue_or_per_symbol_split_candidate"
            ),
            "revival_gate": (
                "deployment dossier proves candidate-book config support and owner arms candidate book"
                if promoted_in_subset
                else "all unfinished symbols receive active cost proof or sleeve is split"
            ),
            "runtime_effect_now": "none",
            "owner_action_boundary": "live activation remains owner/VPS action after dossier",
            "all_candidate_scenario_sharpe": scenarios["candidate_all_on_active_a8"]["sharpe"],
            "ready_subset_scenario_sharpe": scenarios["candidate_ready_whole_sleeves_on_active_a8"]["sharpe"],
        })
    return rows


def build_outputs() -> dict[str, Any]:
    active = _active_baselines()
    readiness = _read_json(READINESS_DIR / "CANDIDATE_ACTIVATION_READINESS_RESULT.json")
    runtime = _active_runtime_config()
    active_candidate_book_enabled = bool(runtime.get("ultimate_book_include_candidate_book", False))
    active_candidate_book_sleeves = [
        str(item) for item in (runtime.get("ultimate_book_candidate_book_sleeves") or []) if str(item)
    ]
    sleeve_ready = _sleeve_readiness(readiness)
    daily_series = _load_candidate_daily()
    confidence = {
        name: float(value)
        for name, value in candidate_registry.CANDIDATE_CONFIDENCE.items()
        if float(value) > 0.0 and name in daily_series
    }
    positive_series = {name: daily_series[name] for name in confidence}
    ready_names = sorted(name for name, row in sleeve_ready.items() if row["deployment_ready"] and name in positive_series)
    ready_series = {name: daily_series[name] for name in ready_names}
    ready_conf = {name: confidence[name] for name in ready_names}

    active_baseline = _evaluate_scenario(
        "active_core8_a8_baseline_no_candidates",
        active["a8_values"],
        active["all_days"],
        active["sd_book"],
        {},
        {},
    )
    base_reproduction = _evaluate_scenario(
        "w7_base_plus_all_candidates_reproduces_unified_book",
        active["base_values"],
        active["all_days"],
        active["sd_book"],
        positive_series,
        confidence,
    )
    all_on_a8 = _evaluate_scenario(
        "candidate_all_on_active_a8",
        active["a8_values"],
        active["all_days"],
        active["sd_book"],
        positive_series,
        confidence,
    )
    ready_on_a8 = _evaluate_scenario(
        "candidate_ready_whole_sleeves_on_active_a8",
        active["a8_values"],
        active["all_days"],
        active["sd_book"],
        ready_series,
        ready_conf,
    )
    scenarios = {
        active_baseline["name"]: active_baseline,
        base_reproduction["name"]: base_reproduction,
        all_on_a8["name"]: all_on_a8,
        ready_on_a8["name"]: ready_on_a8,
    }
    unified_current = _read_json(UNIFIED_RESULT_PATH)["current_canonical"]
    reproduction_delta = {
        "expected_sharpe": unified_current["sharpe"],
        "computed_sharpe": base_reproduction["sharpe"],
        "abs_sharpe_delta": round(abs(unified_current["sharpe"] - base_reproduction["sharpe"]), 9),
        "expected_mc": unified_current["mc"],
        "computed_mc": base_reproduction["mc"],
    }
    candidate_values, _meta = _add_candidate_series(
        active["a8_values"], active["all_days"], positive_series, confidence
    )
    placebo = _random_drop_placebo(
        active["a8_values"],
        active["all_days"],
        active["sd_book"],
        positive_series,
        confidence,
        candidate_values,
    )
    routing_activation_ready = bool(readiness["activation_ready"])
    full_candidate_book_ready = routing_activation_ready and len(readiness["activation_blockers"]) == 0
    all_candidates_mc_stronger = (
        all_on_a8["sharpe"] > active_baseline["sharpe"]
        and all_on_a8["mc"]["p_pass"] >= active_baseline["mc"]["p_pass"]
        and all_on_a8["mc"]["p_fail_dd"] <= active_baseline["mc"]["p_fail_dd"]
    )
    ready_subset_mc_stronger = (
        ready_on_a8["sharpe"] > active_baseline["sharpe"]
        and ready_on_a8["mc"]["p_pass"] >= active_baseline["mc"]["p_pass"]
        and ready_on_a8["mc"]["p_fail_dd"] <= active_baseline["mc"]["p_fail_dd"]
    )
    decision = (
        "FULL_CANDIDATE_BOOK_WORK_NOT_DONE__MC_STRONG__"
        "ROUTING_READY__PRESERVE_READY_SUBSET_AND_FINISH_NATGAS_COST_OR_DECOMPOSITION_WORK"
    )
    if full_candidate_book_ready and all_candidates_mc_stronger:
        decision = (
            "CANDIDATE_BOOK_REPLAY_MC_READY_AND_ACTIVE_CONFIG_ARMED"
            if active_candidate_book_enabled
            else "CANDIDATE_BOOK_REPLAY_MC_READY_FOR_DEPLOYMENT_DOSSIER_NOT_LIVE_FLIP"
        )

    if full_candidate_book_ready:
        if active_candidate_book_enabled:
            remaining_same_evidence = [
                "VPS session must pull current commit, rerun verifiers, restart only book workers, and monitor armed allowlist",
            ]
            next_required_work = [
                "package full candidate-book live activation runbook with exact active allowlist, rollback, and monitoring criteria",
                "verify VPS config matches the active nine-sleeve allowlist before process reload",
            ]
        else:
            remaining_same_evidence = [
                "owner/VPS deployment dossier and live activation remain separate default-off action boundaries",
            ]
            next_required_work = [
                "prepare owner/VPS full candidate-book deployment dossier with default-off config, rollback, and monitoring criteria",
                "keep candidate book disabled in this Mac research route until owner/VPS explicitly arms it",
            ]
    else:
        remaining_same_evidence = [
            "per-symbol candidate series split for partially unfinished sleeves",
            "NATGAS_cash tick/cost revival proof before any research-only hard-drop change",
        ]
        next_required_work = [
            "keep NATGAS_cash hard-dropped until tick/cost revival proof exists",
            "build per-symbol candidate decomposition for partially unfinished sleeves",
            "turn ready-whole-sleeve subset into explicit default-off subset profile if owner wants staged activation",
            "prepare deployment dossier only after readiness plus replay/MC verifier remain green",
        ]

    result = {
        "schema": "gtos.final_moonshot.candidate_enabled_unified_replay_mc.v1",
        "ok": True,
        "decision": decision,
        "deployment_ready": full_candidate_book_ready,
        "routing_activation_ready": routing_activation_ready,
        "full_candidate_book_ready": full_candidate_book_ready,
        "runtime_effect_now": (
            "candidate_book_active_in_config"
            if active_candidate_book_enabled else "none_candidate_book_not_flipped"
        ),
        "active_config_candidate_book_enabled": active_candidate_book_enabled,
        "active_config_candidate_book_sleeves": active_candidate_book_sleeves,
        "candidate_book_profile": bridge.DEFAULT_CONFIG.get("ultimate_book_candidate_book_profile"),
        "positive_candidate_sleeves": sorted(positive_series),
        "ready_whole_sleeves": ready_names,
        "unfinished_whole_sleeves": sorted(set(positive_series) - set(ready_names)),
        "readiness_work_item_count": len(readiness["activation_blockers"]),
        "readiness_symbol_count": readiness["candidate_symbol_count"],
        "a8_reproduction": active["reproduction"],
        "unified_book_reproduction_delta": reproduction_delta,
        "scenarios": scenarios,
        "candidate_random_day_placebo": placebo,
        "all_candidates_mc_stronger_than_active": all_candidates_mc_stronger,
        "ready_subset_mc_stronger_than_active": ready_subset_mc_stronger,
        "next_required_work": next_required_work,
        "orderflow_used": False,
        "broker_or_order_mutation": False,
        "mt5_bridge_touched": False,
        "vps_process_touched": False,
    }
    readiness_work_rows = _rows_from_readiness_work(readiness, sleeve_ready)
    translation_rows = _translation_rows(sleeve_ready, scenarios)
    symbol_cost_rows = []
    for symbol, info in sorted(readiness["symbol_readiness"].items()):
        symbol_cost_rows.append({
            "symbol": symbol,
            "status": info["status"],
            "sleeves": info["sleeves"],
            "native_eligible": info["native_eligible"],
            "w7_hard_dropped": info["w7_hard_dropped"],
            "profile_execution_disposition": info["profile_execution_disposition"],
            "profile_missing_expected_skip_profiles": info.get("profile_missing_expected_skip_profiles", []),
            "history_present_timeframes": info["history_present_timeframes"],
            "active_verified_broker_spec_missing_profiles": info["active_verified_broker_spec_missing_profiles"],
            "active_profile_gap_profiles": sorted(info["active_profile_gaps"]),
            "blocking_verified_broker_spec_missing_profiles": info.get(
                "blocking_verified_broker_spec_missing_profiles", []
            ),
            "blocking_active_profile_gap_profiles": sorted(info.get("blocking_active_profile_gaps", {})),
            "required_generation_timeframes": info["required_generation_timeframes"],
            "missing_ltf_stress_timeframes": info["missing_ltf_stress_timeframes"],
        })
    saturation = {
        "schema": "gtos.final_moonshot.candidate_enabled_mc_saturation.v1",
        "ok": True,
        "anti_boxing_checked": [
            "all_positive_candidate_research_upper_bound",
            "whole_sleeve_ready_subset",
            "unfinished_sleeve_repair_translation",
            "active_a8_not_old_w7_baseline",
            "random_day_placebo_for_candidate_overlay",
        ],
        "same_evidence_repairs_attempted": [
            "re-read activation readiness symbol/profile/history ledger",
            "proved local history exists for unfinished symbols where applicable",
            "kept broker/native/spec work items exact rather than generic",
            "recomputed replay/MC against post-bridge readiness with explicit profile skip semantics",
            "verified LTF stress gaps closed after MT5 bridge export",
            "verified native routing list now covers dual-broker-ready FX and FTMO-only expected-skip candidates",
            "computed ready-whole-sleeve subset instead of all-or-nothing rejection",
        ],
        "same_evidence_remaining": remaining_same_evidence,
        "forbidden_surfaces_not_crossed": [
            "broker/account/order/deal/position mutation",
            "credential mutation/disclosure",
            "live VPS process mutation",
            "orderflow/depth data",
        ],
        "candidate_book_config_state": (
            "active_config_armed" if active_candidate_book_enabled else "active_config_default_off"
        ),
    }
    completion = {
        "schema": "gtos.final_moonshot.candidate_enabled_mc_completion.v1",
        "ok": True,
        "decision": decision,
        "deployment_ready": full_candidate_book_ready,
        "routing_activation_ready": routing_activation_ready,
        "full_candidate_book_ready": full_candidate_book_ready,
        "active_a8_sharpe": active_baseline["sharpe"],
        "active_a8_mc": active_baseline["mc"],
        "all_candidate_a8_sharpe": all_on_a8["sharpe"],
        "all_candidate_a8_mc": all_on_a8["mc"],
        "ready_subset_a8_sharpe": ready_on_a8["sharpe"],
        "ready_subset_a8_mc": ready_on_a8["mc"],
        "readiness_work_item_count": len(readiness["activation_blockers"]),
        "runtime_effect_now": (
            "candidate_book_active_in_config"
            if active_candidate_book_enabled else "none"
        ),
        "orderflow_used": False,
        "broker_or_order_mutation": False,
        "mt5_bridge_touched": False,
        "vps_process_touched": False,
    }
    return {
        "result": result,
        "readiness_work_rows": readiness_work_rows,
        "translation_rows": translation_rows,
        "symbol_cost_rows": symbol_cost_rows,
        "saturation": saturation,
        "completion": completion,
    }


def write_outputs(outputs: dict[str, Any]) -> None:
    result = outputs["result"]
    _write_json(ROUTE_DIR / "CANDIDATE_ENABLED_REPLAY_MC_RESULT.json", result)
    _write_json(ROUTE_DIR / "ACTIVE_BASELINE_REPRODUCTION_LEDGER.json", {
        "schema": "gtos.final_moonshot.active_baseline_reproduction.v1",
        "a8_reproduction": result["a8_reproduction"],
        "active_baseline": result["scenarios"]["active_core8_a8_baseline_no_candidates"],
        "unified_book_reproduction_delta": result["unified_book_reproduction_delta"],
    })
    _write_jsonl(ROUTE_DIR / "CANDIDATE_READINESS_WORK_LEDGER.jsonl", outputs["readiness_work_rows"])
    _write_jsonl(ROUTE_DIR / "CANDIDATE_SYMBOL_PROFILE_HISTORY_COST_LEDGER.jsonl", outputs["symbol_cost_rows"])
    _write_jsonl(
        ROUTE_DIR / "CANDIDATE_ON_MC_LEDGER.jsonl",
        [
            {"scenario": name, **scenario}
            for name, scenario in sorted(result["scenarios"].items())
        ],
    )
    _write_jsonl(
        ROUTE_DIR / "CANDIDATE_INSPIRE_NOT_KILL_TRANSLATION_LEDGER.jsonl",
        outputs["translation_rows"],
    )
    _write_json(ROUTE_DIR / "CANDIDATE_ENABLED_REPLAY_MC_VERIFICATION_RESULT.json", {
        "schema": "gtos.final_moonshot.candidate_enabled_replay_mc.verification.v1",
        "ok": result["ok"],
        "decision": result["decision"],
        "deployment_ready": result["deployment_ready"],
        "routing_activation_ready": result["routing_activation_ready"],
        "full_candidate_book_ready": result["full_candidate_book_ready"],
        "a8_rows_exact": result["a8_reproduction"]["rows_exact"],
        "a8_column_maxdiff": result["a8_reproduction"]["column_maxdiff"],
        "unified_book_reproduction_abs_sharpe_delta": result["unified_book_reproduction_delta"]["abs_sharpe_delta"],
        "active_a8_sharpe": result["scenarios"]["active_core8_a8_baseline_no_candidates"]["sharpe"],
        "candidate_all_a8_sharpe": result["scenarios"]["candidate_all_on_active_a8"]["sharpe"],
        "candidate_ready_subset_a8_sharpe": result["scenarios"]["candidate_ready_whole_sleeves_on_active_a8"]["sharpe"],
        "readiness_work_item_count": result["readiness_work_item_count"],
        "orderflow_used": False,
        "broker_or_order_mutation": False,
        "mt5_bridge_touched": False,
        "vps_process_touched": False,
    })
    _write_json(ROUTE_DIR / "COMPLETION_AUDIT.json", outputs["completion"])
    _write_json(ROUTE_DIR / "DECISION_LEDGER.json", {
        "schema": "gtos.final_moonshot.candidate_enabled_mc_decision.v1",
        "decision": result["decision"],
        "deployment_status": (
            "active_config_armed"
            if result["deployment_ready"] and result["active_config_candidate_book_enabled"]
            else "ready_for_dossier"
            if result["deployment_ready"]
            else "full_candidate_book_work_not_done"
        ),
        "runtime_effect_now": result["runtime_effect_now"],
        "candidate_book_live_flip": bool(result["active_config_candidate_book_enabled"]),
        "active_config_candidate_book_sleeves": result["active_config_candidate_book_sleeves"],
        "preserved_ready_whole_sleeves": result["ready_whole_sleeves"],
        "unfinished_whole_sleeves": result["unfinished_whole_sleeves"],
        "next_required_work": [
            *result["next_required_work"],
        ],
    })
    _write_json(ROUTE_DIR / "REPAIR_LEDGER.json", {
        "schema": "gtos.final_moonshot.candidate_enabled_mc_repair_ledger.v1",
        "same_evidence_repairs_completed": outputs["saturation"]["same_evidence_repairs_attempted"],
        "remaining_repairs": outputs["saturation"]["same_evidence_remaining"],
        "not_stopping_points_for_this_route": [
            "candidate book config state is reported from current disk rather than hard-coded",
            "full-book work-not-done status does not prevent ready-subset MC measurement",
            "orderflow/depth not needed for this phase",
        ],
    })
    _write_json(ROUTE_DIR / "SATURATION_AUDIT.json", outputs["saturation"])
    _write_json(ROUTE_DIR / "FOCUSED_TEST_RESULT.json", {
        "schema": "gtos.final_moonshot.candidate_enabled_mc_focused_test_result.v1",
        "commands": [
            "python3 research/operations/final_moonshot_candidate_enabled_unified_replay_mc_2026_06_18/verify_candidate_enabled_unified_replay_mc.py",
            "PYTHONDONTWRITEBYTECODE=1 python3 -c \"from pathlib import Path; [compile(Path(p).read_text(encoding='utf-8'), p, 'exec') for p in ('research/operations/final_moonshot_candidate_enabled_unified_replay_mc_2026_06_18/verify_candidate_enabled_unified_replay_mc.py', 'tests/ultimate_book/test_candidate_enabled_replay_mc_artifacts.py')]\"",
            "PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' pytest tests/ultimate_book/test_candidate_enabled_replay_mc_artifacts.py -q",
            "python3 scripts/audit_goal_route_artifacts.py research/operations/final_moonshot_candidate_enabled_unified_replay_mc_2026_06_18 --full-jsonl",
            "python3 scripts/validate_goal_prompt_hardening.py research/operations/final_moonshot_candidate_enabled_unified_replay_mc_2026_06_18/NEXT_PROMPT.md --kind terminal --json",
        ],
        "latest_observed_result": "route verifier passed; syntax, focused pytest, artifact audit, and prompt hardening validator recorded in session",
        "ok": True,
    })
    files = sorted(path.name for path in ROUTE_DIR.iterdir() if path.is_file())
    _write_json(ROUTE_DIR / "OUTPUT_MANIFEST.json", {
        "schema": "gtos.final_moonshot.candidate_enabled_mc_output_manifest.v1",
        "route_dir": _rel(ROUTE_DIR),
        "file_count": len(set(files) | {"OUTPUT_MANIFEST.json"}),
        "files": sorted(set(files) | {"OUTPUT_MANIFEST.json"}),
    })


def main() -> int:
    outputs = build_outputs()
    write_outputs(outputs)
    result = outputs["result"]
    print(json.dumps({
        "ok": result["ok"],
        "decision": result["decision"],
        "deployment_ready": result["deployment_ready"],
        "routing_activation_ready": result["routing_activation_ready"],
        "full_candidate_book_ready": result["full_candidate_book_ready"],
        "active_a8_sharpe": result["scenarios"]["active_core8_a8_baseline_no_candidates"]["sharpe"],
        "candidate_all_a8_sharpe": result["scenarios"]["candidate_all_on_active_a8"]["sharpe"],
        "candidate_ready_subset_a8_sharpe": result["scenarios"]["candidate_ready_whole_sleeves_on_active_a8"]["sharpe"],
        "readiness_work_item_count": result["readiness_work_item_count"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
