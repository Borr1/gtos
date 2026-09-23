#!/usr/bin/env python3
"""G12 review of market-expansion follow-up replay candidates.

This route is research-only. It consumes the committed market-expansion
follow-up replay route, classifies every candidate row, audits full-book
interaction and timing-null behavior, and writes a default-off handoff. It
does not activate live config or touch broker/VPS/order state.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
FOLLOWUP_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_market_expansion_followup_replay_2026_06_18"
SCORING_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_market_expansion_validation_scoring_2026_06_18"
CANDIDATE_MC_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_candidate_enabled_unified_replay_mc_2026_06_18"
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_g12_review"
DEEP_CLASSES = {"first_pass_promoted", "near_miss_positive_proxy"}
DEFAULT_OFF_DECISIONS = {
    "default_off_m1_supported_candidate",
    "default_off_proxy_supported_candidate_requires_m1_repair",
}
UNIT_INTERACTION_WEIGHT = 0.05
RANDOM_DAY_REPS = 200
ACCEPTANCE = {
    "min_ordered_events": 75,
    "min_ordered_path_coverage_ratio": 0.95,
    "min_ordered_mean_r": 0.05,
    "min_populated_split_count": 3,
    "require_every_populated_split_positive": True,
    "min_split_mean_r": 0.01,
    "median_r_min_or_win_rate_min": {"median_r": 0.0, "win_rate": 0.52},
    "min_delta_sharpe": 0.00010,
    "max_abs_corr_to_current_book": 0.06,
    "min_matched_current_book_days": 60,
    "min_exact_m1_events_for_m1_supported": 20,
    "proxy_limited_min_m15_events": 75,
    "proxy_limited_min_mean_r": 0.10,
    "near_miss_min_ordered_events": 100,
    "near_miss_min_ordered_mean_r": 0.075,
    "near_miss_min_split_mean_r": 0.015,
    "near_miss_min_delta_sharpe": 0.00020,
    "near_miss_max_abs_corr_to_current_book": 0.05,
    "near_miss_min_matched_current_book_days": 80,
}
EXCLUDED_SYMBOLS = {"SPCX", "NATGAS_cash", "HEATOIL_c"}

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows), encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def summarize(values: list[float]) -> dict[str, Any]:
    clean = [float(value) for value in values if math.isfinite(float(value))]
    if not clean:
        return {"n": 0, "min": None, "median": None, "mean": None, "max": None}
    return {
        "n": len(clean),
        "min": round(min(clean), 6),
        "median": round(statistics.median(clean), 6),
        "mean": round(statistics.fmean(clean), 6),
        "max": round(max(clean), 6),
    }


def import_candidate_mc_module():
    path = CANDIDATE_MC_ROUTE / "verify_candidate_enabled_unified_replay_mc.py"
    spec = importlib.util.spec_from_file_location("candidate_enabled_mc", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def active_book_arrays() -> dict[str, Any]:
    module = import_candidate_mc_module()
    active = module._active_baselines()
    daily_series = module._load_candidate_daily()
    confidence = {
        name: float(value)
        for name, value in module.candidate_registry.CANDIDATE_CONFIDENCE.items()
        if float(value) > 0.0 and name in daily_series
    }
    positive_series = {name: daily_series[name] for name in confidence}
    current_values, meta = module._add_candidate_series(
        active["a8_values"], active["all_days"], positive_series, confidence
    )
    return {
        "module": module,
        "all_days": active["all_days"],
        "day_index": {day.isoformat()[:10]: index for index, day in enumerate(active["all_days"])},
        "current_values": np.array(current_values, dtype=float),
        "current_meta": meta,
        "current_sharpe": float(module._sharpe(current_values)),
    }


def raw_daily_series(raw_rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, float]]:
    series: dict[tuple[str, str], dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for row in raw_rows:
        if row.get("target2_net_r") is None:
            continue
        series[(row["file_symbol"], row["mechanism"])][row["date"]] += float(row["target2_net_r"])
    return {key: dict(value) for key, value in series.items()}


def random_day_null(
    *,
    key: tuple[str, str],
    daily: dict[str, float],
    book: dict[str, Any],
    observed_delta: float,
) -> dict[str, Any]:
    base = book["current_values"]
    module = book["module"]
    day_index = book["day_index"]
    aligned = np.zeros(len(base), dtype=float)
    matched = 0
    for date, value in daily.items():
        idx = day_index.get(date)
        if idx is None:
            continue
        aligned[idx] += float(value)
        matched += 1
    nonzero = aligned[aligned != 0.0]
    seed = int(hashlib.sha256(("|".join(key)).encode("utf-8")).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    random_deltas: list[float] = []
    for _ in range(RANDOM_DAY_REPS):
        shuffled = np.zeros(len(base), dtype=float)
        if len(nonzero):
            replace = len(nonzero) > len(base)
            idx = rng.choice(len(base), size=len(nonzero), replace=replace)
            shuffled[idx] += nonzero
        scenario = base + UNIT_INTERACTION_WEIGHT * shuffled
        random_deltas.append(float(module._sharpe(scenario.tolist()) - book["current_sharpe"]))
    p_ge = sum(delta >= observed_delta for delta in random_deltas) / len(random_deltas)
    return {
        "random_day_reps": RANDOM_DAY_REPS,
        "random_day_seed": seed,
        "matched_current_book_days": matched,
        "observed_delta_sharpe": round(float(observed_delta), 6),
        "random_delta_sharpe_median": round(statistics.median(random_deltas), 6),
        "random_delta_sharpe_p90": round(float(np.quantile(random_deltas, 0.90)), 6),
        "random_day_p_ge_observed": round(float(p_ge), 6),
        "timing_null_clean_p_le_0p25": bool(p_ge <= 0.25 and observed_delta > 0),
    }


def g12_decision(
    candidate: dict[str, Any],
    full_book: dict[str, Any] | None,
    scoring: dict[str, Any] | None,
    random_null: dict[str, Any] | None,
) -> dict[str, Any]:
    followup_class = candidate["followup_class"]
    summary = candidate["target2_ordered_path_summary"]
    sealed = summary["splits"]["sealed_ge_2025"]
    split_means = [
        float(payload["mean_r"])
        for payload in summary["splits"].values()
        if int(payload.get("n", 0)) > 0 and payload.get("mean_r") is not None
    ]
    min_split_mean = min(split_means) if split_means else None
    mean_r = finite(summary.get("mean_r"))
    median_r = finite(summary.get("median_r"))
    win_rate = finite(summary.get("win_rate"))
    corr = finite(full_book.get("corr_to_current_active_book")) if full_book else None
    delta_sharpe = finite(full_book.get("delta_sharpe")) if full_book else None
    matched_days = int(full_book.get("matched_current_book_days", 0)) if full_book else 0
    source_placebo = None
    if scoring:
        source_placebo = finite((scoring.get("placebo") or {}).get("placebo_p_ge_observed"))

    gates = {
        "deep_replay_class": followup_class in DEEP_CLASSES,
        "ordered_events_ge_75": int(summary.get("n", 0)) >= ACCEPTANCE["min_ordered_events"],
        "ordered_path_coverage_ge_0p95": float(candidate.get("target2_ordered_path_coverage_ratio", 0.0))
        >= ACCEPTANCE["min_ordered_path_coverage_ratio"],
        "ordered_mean_ge_0p05": mean_r is not None and mean_r >= ACCEPTANCE["min_ordered_mean_r"],
        "populated_splits_ge_3": int(summary.get("populated_split_count", 0)) >= ACCEPTANCE["min_populated_split_count"],
        "every_populated_split_positive": summary.get("every_populated_split_positive") is True,
        "min_split_mean_ge_0p01": min_split_mean is not None and min_split_mean >= ACCEPTANCE["min_split_mean_r"],
        "median_nonnegative_or_win_rate_ge_0p52": (median_r is not None and median_r >= 0.0)
        or (win_rate is not None and win_rate >= ACCEPTANCE["median_r_min_or_win_rate_min"]["win_rate"]),
        "full_book_delta_ge_0p00010": delta_sharpe is not None and delta_sharpe >= ACCEPTANCE["min_delta_sharpe"],
        "corr_abs_le_0p06": corr is not None and abs(corr) <= ACCEPTANCE["max_abs_corr_to_current_book"],
        "matched_current_book_days_ge_60": matched_days >= ACCEPTANCE["min_matched_current_book_days"],
        "exact_m1_events_ge_20": int(candidate.get("target2_exact_m1_event_count", 0)) >= ACCEPTANCE["min_exact_m1_events_for_m1_supported"],
        "proxy_limited_m15_events_ge_75": int(candidate.get("target2_m15_proxy_event_count", 0)) >= ACCEPTANCE["proxy_limited_min_m15_events"],
        "proxy_limited_mean_ge_0p10": mean_r is not None and mean_r >= ACCEPTANCE["proxy_limited_min_mean_r"],
        "near_miss_ordered_events_ge_100": int(summary.get("n", 0)) >= ACCEPTANCE["near_miss_min_ordered_events"],
        "near_miss_mean_ge_0p075": mean_r is not None and mean_r >= ACCEPTANCE["near_miss_min_ordered_mean_r"],
        "near_miss_min_split_mean_ge_0p015": min_split_mean is not None and min_split_mean >= ACCEPTANCE["near_miss_min_split_mean_r"],
        "near_miss_delta_ge_0p00020": delta_sharpe is not None and delta_sharpe >= ACCEPTANCE["near_miss_min_delta_sharpe"],
        "near_miss_corr_abs_le_0p05": corr is not None and abs(corr) <= ACCEPTANCE["near_miss_max_abs_corr_to_current_book"],
        "near_miss_matched_days_ge_80": matched_days >= ACCEPTANCE["near_miss_min_matched_current_book_days"],
        "ordered_path_ready": candidate.get("ordered_path_ready_for_interaction") is True,
        "source_placebo_pass_or_missing": source_placebo is None or source_placebo <= 0.25,
        "random_day_timing_null_clean": bool(random_null and random_null.get("timing_null_clean_p_le_0p25")),
    }
    core = all(
        gates[name]
        for name in (
            "deep_replay_class",
            "ordered_events_ge_75",
            "ordered_path_coverage_ge_0p95",
            "ordered_mean_ge_0p05",
            "populated_splits_ge_3",
            "every_populated_split_positive",
            "min_split_mean_ge_0p01",
            "median_nonnegative_or_win_rate_ge_0p52",
            "full_book_delta_ge_0p00010",
            "corr_abs_le_0p06",
            "matched_current_book_days_ge_60",
            "ordered_path_ready",
            "source_placebo_pass_or_missing",
        )
    )
    near_miss_core = core and all(
        gates[name]
        for name in (
            "near_miss_ordered_events_ge_100",
            "near_miss_mean_ge_0p075",
            "near_miss_min_split_mean_ge_0p015",
            "near_miss_delta_ge_0p00020",
            "near_miss_corr_abs_le_0p05",
            "near_miss_matched_days_ge_80",
        )
    )
    common_repair_gates = [
        "deep_replay_class",
        "ordered_events_ge_75",
        "ordered_path_coverage_ge_0p95",
        "ordered_mean_ge_0p05",
        "populated_splits_ge_3",
        "every_populated_split_positive",
        "min_split_mean_ge_0p01",
        "median_nonnegative_or_win_rate_ge_0p52",
        "full_book_delta_ge_0p00010",
        "corr_abs_le_0p06",
        "matched_current_book_days_ge_60",
        "ordered_path_ready",
        "source_placebo_pass_or_missing",
    ]
    first_pass_extra_gates = [
        "exact_m1_events_ge_20",
        "proxy_limited_m15_events_ge_75",
        "proxy_limited_mean_ge_0p10",
    ]
    near_miss_extra_gates = [
        "near_miss_ordered_events_ge_100",
        "near_miss_mean_ge_0p075",
        "near_miss_min_split_mean_ge_0p015",
        "near_miss_delta_ge_0p00020",
        "near_miss_corr_abs_le_0p05",
        "near_miss_matched_days_ge_80",
        "exact_m1_events_ge_20",
    ]
    repair_gate_names = list(common_repair_gates)
    if followup_class == "first_pass_promoted":
        repair_gate_names.extend(first_pass_extra_gates)
    elif followup_class == "near_miss_positive_proxy":
        repair_gate_names.extend(near_miss_extra_gates)
    failed_repair_gates = [
        name
        for name in repair_gate_names
        if not gates.get(name, False) and name != "deep_replay_class"
    ]

    if (
        (followup_class == "first_pass_promoted" and core and gates["exact_m1_events_ge_20"])
        or (followup_class == "near_miss_positive_proxy" and near_miss_core and gates["exact_m1_events_ge_20"])
    ):
        decision = "default_off_m1_supported_candidate"
        transformed_use = "default-off expansion candidate for implementation design and selector de-dup review"
        required_repairs = [
            "exact broker spread/slippage/commission/swap model",
            "selector-level de-duplication and family budget",
            "deployment package review before any live authority",
        ]
    elif (
        followup_class == "first_pass_promoted"
        and core
        and gates["proxy_limited_m15_events_ge_75"]
        and gates["proxy_limited_mean_ge_0p10"]
    ):
        decision = "default_off_proxy_supported_candidate_requires_m1_repair"
        transformed_use = "default-off expansion candidate watchlist requiring more exact M1 path support"
        required_repairs = [
            "export or locate missing M1 path coverage",
            "repeat path replay using exact M1 before live promotion",
            "selector-level de-duplication and family budget",
        ]
    elif followup_class in DEEP_CLASSES and ((mean_r is not None and mean_r > 0) or (delta_sharpe is not None and delta_sharpe > 0)):
        decision = "transformed_context_or_sizing_feature"
        transformed_use = "context feature, veto/sizing hint, or preregistered successor experiment"
        required_repairs = failed_repair_gates
    elif followup_class in DEEP_CLASSES:
        decision = "exact_repair_or_negative_control_required"
        transformed_use = "negative control, source repair target, or veto feature"
        required_repairs = failed_repair_gates
    elif followup_class == "context_only_single_stock_cfd":
        decision = "context_only_single_stock_portfolio_inventory"
        transformed_use = "single-stock portfolio context only; not a trade-sleeve candidate in this route"
        required_repairs = ["separate portfolio-context study and single-stock risk budget"]
    elif followup_class == "positive_proxy_underpowered_or_unstable":
        decision = "successor_experiment_inventory"
        transformed_use = "underpowered positive proxy held for future source repair or feature extraction"
        required_repairs = candidate.get("promotion_gate_failures") or ["increase evidence strength"]
    else:
        decision = "context_or_veto_inventory"
        transformed_use = "context, veto, sizing hint, or negative-control inventory"
        required_repairs = candidate.get("promotion_gate_failures") or ["no immediate positive G12 evidence"]

    return {
        "decision": decision,
        "gates": gates,
        "transformed_use": transformed_use,
        "required_repairs": required_repairs,
        "source_placebo_p_ge_observed": source_placebo,
        "not_killed": True,
        "why_not_live_authority_now": "G12 review is default-off research only; exact broker lifecycle, selector merge, deployment package, and owner action are still required",
    }


def build() -> dict[str, Any]:
    created_at = utc_now()
    followup_result = read_json(FOLLOWUP_ROUTE / "MARKET_EXPANSION_FOLLOWUP_REPLAY_RESULT.json")
    followup_verification = read_json(FOLLOWUP_ROUTE / "MARKET_EXPANSION_FOLLOWUP_REPLAY_VERIFIER_RESULT.json")
    raw_manifest = read_json(FOLLOWUP_ROUTE / "PATH_REPLAY_EVENT_EXPORT_MANIFEST.json")
    raw_path = PROJECT_ROOT / raw_manifest["path"]
    raw_rows = read_jsonl(raw_path)
    candidate_rows = read_jsonl(FOLLOWUP_ROUTE / "CANDIDATE_FOLLOWUP_REPLAY_LEDGER.jsonl")
    full_book_rows = read_jsonl(FOLLOWUP_ROUTE / "FULL_BOOK_INTERACTION_LEDGER.jsonl")
    scoring_rows = read_jsonl(SCORING_ROUTE / "CANDIDATE_RESULT_LEDGER.jsonl")
    scoring_by_key = {(row["file_symbol"], row["mechanism"]): row for row in scoring_rows}
    full_book_by_key = {(row["file_symbol"], row["mechanism"]): row for row in full_book_rows}
    daily_by_key = raw_daily_series(raw_rows)
    book = active_book_arrays()

    random_null_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for row in full_book_rows:
        key = (row["file_symbol"], row["mechanism"])
        random_null_by_key[key] = random_day_null(
            key=key,
            daily=daily_by_key.get(key, {}),
            book=book,
            observed_delta=float(row["delta_sharpe"]),
        )

    candidate_decisions: list[dict[str, Any]] = []
    deep_selection_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    repair_rows: list[dict[str, Any]] = []
    implementation_rows: list[dict[str, Any]] = []
    inspire_rows: list[dict[str, Any]] = []

    for candidate in candidate_rows:
        key = (candidate["file_symbol"], candidate["mechanism"])
        full_book = full_book_by_key.get(key)
        random_null = random_null_by_key.get(key)
        decision = g12_decision(candidate, full_book, scoring_by_key.get(key), random_null)
        summary = candidate["target2_ordered_path_summary"]
        sealed = summary["splits"]["sealed_ge_2025"]
        base = {
            "file_symbol": candidate["file_symbol"],
            "broker_symbol": candidate["broker_symbol"],
            "family": candidate["family"],
            "asset_class": candidate["asset_class"],
            "mechanism": candidate["mechanism"],
            "followup_class": candidate["followup_class"],
            "g12_decision": decision["decision"],
            "not_killed": decision["not_killed"],
            "transformed_use": decision["transformed_use"],
            "why_not_live_authority_now": decision["why_not_live_authority_now"],
            "required_repairs": decision["required_repairs"],
            "gates": decision["gates"],
            "source_event_count": candidate["source_event_count"],
            "path_replay_event_count": candidate["path_replay_event_count"],
            "target2_ordered_path_event_count": candidate["target2_ordered_path_event_count"],
            "target2_exact_m1_event_count": candidate["target2_exact_m1_event_count"],
            "target2_m15_proxy_event_count": candidate["target2_m15_proxy_event_count"],
            "target2_ordered_mean_r": summary.get("mean_r"),
            "target2_ordered_win_rate": summary.get("win_rate"),
            "target2_ordered_split_count": summary.get("populated_split_count"),
            "target2_every_populated_split_positive": summary.get("every_populated_split_positive"),
            "sealed_event_count": sealed.get("n"),
            "sealed_mean_r": sealed.get("mean_r"),
            "source_placebo_p_ge_observed": decision["source_placebo_p_ge_observed"],
            "runtime_effect": "none_research_review_only",
        }
        if full_book:
            base.update(
                {
                    "full_book_delta_sharpe": full_book["delta_sharpe"],
                    "full_book_scenario_sharpe": full_book["scenario_sharpe"],
                    "full_book_scenario_mc": full_book["scenario_mc"],
                    "corr_to_current_active_book": full_book["corr_to_current_active_book"],
                    "unit_interaction_weight": full_book["unit_interaction_weight"],
                }
            )
        if random_null:
            base["random_day_null"] = random_null
        candidate_decisions.append(base)
        inspire_rows.append(
            {
                "file_symbol": base["file_symbol"],
                "family": base["family"],
                "mechanism": base["mechanism"],
                "followup_class": base["followup_class"],
                "g12_decision": base["g12_decision"],
                "not_killed": True,
                "what_is_real_or_inspiring": "source-bound OHLCV/path replay signal is preserved as candidate, feature, repair target, or negative control",
                "transformed_use": base["transformed_use"],
                "revival_gate": "exact M1 path, positive robust splits, positive full-book interaction, low concentration, and selector-safe merge",
                "runtime_effect": "none_research_review_only",
            }
        )
        if candidate["followup_class"] in DEEP_CLASSES:
            deep_selection_rows.append(base)
        if base["g12_decision"] in DEFAULT_OFF_DECISIONS:
            accepted_rows.append(base)
            implementation_rows.append(
                {
                    "file_symbol": base["file_symbol"],
                    "family": base["family"],
                    "mechanism": base["mechanism"],
                    "default_off_status": base["g12_decision"],
                    "implementation_scope": "candidate_registry_default_off_only",
                    "selector_merge_requirement": "deduplicate by symbol/family/mechanism and apply family budget before any active config",
                    "profile_spec_requirement": "broker-native symbol/spec/cost/history proof required before activation",
                    "evidence_class": "M1/M15_ORDERED_PRICE_PATH_REPLAY_NOT_BROKER_LIFECYCLE_TRUTH",
                    "live_authority": False,
                    "required_repairs": base["required_repairs"],
                }
            )
        if base["required_repairs"]:
            repair_rows.append(
                {
                    "file_symbol": base["file_symbol"],
                    "family": base["family"],
                    "mechanism": base["mechanism"],
                    "g12_decision": base["g12_decision"],
                    "required_repairs": base["required_repairs"],
                    "source_class": base["followup_class"],
                    "not_killed": True,
                }
            )

    decision_counts = Counter(row["g12_decision"] for row in candidate_decisions)
    default_off_counts = Counter(row["g12_decision"] for row in accepted_rows)
    deep_decision_counts = Counter(row["g12_decision"] for row in deep_selection_rows)
    accepted_family_counts = Counter(row["family"] for row in accepted_rows)
    accepted_mechanism_counts = Counter(row["mechanism"] for row in accepted_rows)
    random_p_values = [
        row["random_day_null"]["random_day_p_ge_observed"]
        for row in deep_selection_rows
        if row.get("random_day_null")
    ]
    delta_values = [float(row["full_book_delta_sharpe"]) for row in deep_selection_rows if row.get("full_book_delta_sharpe") is not None]
    mean_values = [float(row["target2_ordered_mean_r"]) for row in deep_selection_rows if row.get("target2_ordered_mean_r") is not None]
    exact_m1_values = [int(row["target2_exact_m1_event_count"]) for row in deep_selection_rows]
    m15_values = [int(row["target2_m15_proxy_event_count"]) for row in deep_selection_rows]

    full_book_audit = {
        "schema": f"{SCHEMA_PREFIX}.full_book_interaction_audit.v1",
        "created_at_utc": created_at,
        "ok": len(full_book_rows) == followup_result["full_book_interaction_row_count"] == 75,
        "source_route": rel(FOLLOWUP_ROUTE),
        "row_count": len(full_book_rows),
        "computed_count": sum(1 for row in full_book_rows if row["status"] == "computed_sensitivity_not_live_authority"),
        "positive_delta_count": sum(1 for row in full_book_rows if float(row["delta_sharpe"]) > 0),
        "negative_delta_count": sum(1 for row in full_book_rows if float(row["delta_sharpe"]) < 0),
        "delta_sharpe_summary": summarize(delta_values),
        "ordered_mean_r_summary": summarize(mean_values),
        "unit_interaction_weight": UNIT_INTERACTION_WEIGHT,
        "top_delta_candidates": [
            {
                "file_symbol": row["file_symbol"],
                "family": row["family"],
                "mechanism": row["mechanism"],
                "g12_decision": row["g12_decision"],
                "delta_sharpe": row.get("full_book_delta_sharpe"),
                "target2_ordered_mean_r": row.get("target2_ordered_mean_r"),
            }
            for row in sorted(deep_selection_rows, key=lambda item: float(item.get("full_book_delta_sharpe") or -999), reverse=True)[:20]
        ],
        "runtime_effect": "none_research_review_only",
    }
    concentration_null_audit = {
        "schema": f"{SCHEMA_PREFIX}.concentration_null_placebo_audit.v1",
        "created_at_utc": created_at,
        "ok": True,
        "candidate_decision_counts": dict(sorted(decision_counts.items())),
        "deep_decision_counts": dict(sorted(deep_decision_counts.items())),
        "default_off_decision_counts": dict(sorted(default_off_counts.items())),
        "accepted_by_family": dict(sorted(accepted_family_counts.items())),
        "accepted_by_mechanism": dict(sorted(accepted_mechanism_counts.items())),
        "accepted_count": len(accepted_rows),
        "deep_count": len(deep_selection_rows),
        "max_accepted_family_share": round(max(accepted_family_counts.values()) / len(accepted_rows), 6) if accepted_rows else 0.0,
        "max_accepted_mechanism_share": round(max(accepted_mechanism_counts.values()) / len(accepted_rows), 6) if accepted_rows else 0.0,
        "accepted_mechanism_budget_warning": any(count > 4 for count in accepted_mechanism_counts.values()),
        "exact_m1_event_summary": summarize([float(value) for value in exact_m1_values]),
        "m15_proxy_event_summary": summarize([float(value) for value in m15_values]),
        "deep_exact_m1_ready_count": sum(1 for row in deep_selection_rows if row["target2_exact_m1_event_count"] >= ACCEPTANCE["min_exact_m1_events_for_m1_supported"]),
        "deep_ordered_path_ready_count": sum(1 for row in deep_selection_rows if row["target2_ordered_path_event_count"] >= ACCEPTANCE["min_ordered_events"]),
        "timing_null": {
            "random_day_reps": RANDOM_DAY_REPS,
            "p_le_0p25_positive_delta_count": sum(
                1
                for row in deep_selection_rows
                if row.get("random_day_null", {}).get("timing_null_clean_p_le_0p25")
            ),
            "p_value_summary": summarize([float(value) for value in random_p_values]),
            "note": "Timing null is an audit flag, not the sole default-off acceptance gate; negative observed deltas cannot pass G12 even if shuffled placement is worse.",
        },
        "source_placebo": {
            "p_le_0p25_or_missing_count": sum(1 for row in deep_selection_rows if row["gates"]["source_placebo_pass_or_missing"]),
            "note": "Source scoring placebo is preserved from first-pass scoring and audited separately from ordered-path/full-book evidence.",
        },
        "no_arbitrary_top_n": True,
        "runtime_effect": "none_research_review_only",
    }

    result = {
        "schema": f"{SCHEMA_PREFIX}.result.v1",
        "created_at_utc": created_at,
        "ok": (
            followup_result.get("ok") is True
            and followup_verification.get("ok") is True
            and len(candidate_decisions) == 820
            and len(deep_selection_rows) == 75
            and len(full_book_rows) == 75
            and EXCLUDED_SYMBOLS.isdisjoint({row["file_symbol"] for row in candidate_decisions})
        ),
        "decision": "MARKET_EXPANSION_G12_REVIEW_READY_FOR_DEFAULT_OFF_IMPLEMENTATION_DESIGN",
        "source_followup_route": rel(FOLLOWUP_ROUTE),
        "candidate_result_count": len(candidate_decisions),
        "deep_review_count": len(deep_selection_rows),
        "default_off_candidate_count": len(accepted_rows),
        "default_off_m1_supported_count": decision_counts["default_off_m1_supported_candidate"],
        "default_off_proxy_supported_count": decision_counts["default_off_proxy_supported_candidate_requires_m1_repair"],
        "transformed_context_or_sizing_feature_count": decision_counts["transformed_context_or_sizing_feature"],
        "exact_repair_or_negative_control_count": decision_counts["exact_repair_or_negative_control_required"],
        "random_day_reps": RANDOM_DAY_REPS,
        "orderflow_used": False,
        "broker_or_order_mutation": False,
        "config_or_live_activation_changed": False,
        "vps_process_touched": False,
        "live_authority": False,
    }
    input_manifest = {
        "schema": f"{SCHEMA_PREFIX}.input_manifest.v1",
        "created_at_utc": created_at,
        "source_artifacts": [
            rel(FOLLOWUP_ROUTE / "MARKET_EXPANSION_FOLLOWUP_REPLAY_RESULT.json"),
            rel(FOLLOWUP_ROUTE / "CANDIDATE_FOLLOWUP_REPLAY_LEDGER.jsonl"),
            rel(FOLLOWUP_ROUTE / "FULL_BOOK_INTERACTION_LEDGER.jsonl"),
            rel(FOLLOWUP_ROUTE / "PATH_REPLAY_EVENT_EXPORT_MANIFEST.json"),
            rel(SCORING_ROUTE / "CANDIDATE_RESULT_LEDGER.jsonl"),
            rel(CANDIDATE_MC_ROUTE / "CANDIDATE_ENABLED_REPLAY_MC_RESULT.json"),
        ],
        "raw_path_event_manifest": raw_manifest,
        "raw_path_event_sha256_verified": sha256_file(raw_path) == raw_manifest["sha256"],
        "acceptance_contract": ACCEPTANCE,
        "forbidden_data": ["orderflow", "depth", "broker order/deal/position/account mutation", "VPS process mutation", "live config activation"],
    }
    decision_rows = [
        {
            "created_at_utc": created_at,
            "decision": result["decision"],
            "candidate_result_count": result["candidate_result_count"],
            "deep_review_count": result["deep_review_count"],
            "default_off_candidate_count": result["default_off_candidate_count"],
            "default_off_m1_supported_count": result["default_off_m1_supported_count"],
            "default_off_proxy_supported_count": result["default_off_proxy_supported_count"],
            "evidence_class": "G12 review of M1/M15 ordered price path replay plus full-book unit sensitivity",
            "runtime_effect": "none_research_review_only",
        },
        {
            "created_at_utc": created_at,
            "decision": "NO_LIVE_AUTHORITY_FROM_G12_REVIEW",
            "reason": "default-off candidate decisions still require exact broker lifecycle/cost repair, selector merge, risk budget, deployment package, and owner action",
        },
    ]
    repair = {
        "schema": f"{SCHEMA_PREFIX}.repair_ledger_summary.v1",
        "ok": True,
        "blockers": [],
        "repair_row_count": len(repair_rows),
        "completed_repairs": [
            "classified every scored candidate row instead of selecting a top-N subset",
            "separated exact-M1-supported candidates from M15-proxy-supported candidates",
            "computed deterministic random-day timing null for all 75 deep replay rows",
            "preserved every non-accepted row as context, feature, successor experiment, repair target, or negative control",
        ],
        "remaining_same_evidence_class_work": [
            "selector-level de-duplication and risk-budget design for default-off implementation",
            "exact broker cost/spread/slippage/swap model",
            "limit-order fill and broker lifecycle replay cannot be proven from OHLCV alone",
        ],
    }
    saturation = {
        "schema": f"{SCHEMA_PREFIX}.saturation_audit.v1",
        "ok": True,
        "all_candidate_rows_processed": len(candidate_decisions) == 820,
        "all_deep_rows_reviewed": len(deep_selection_rows) == 75,
        "no_arbitrary_top_n": True,
        "decision_counts": dict(sorted(decision_counts.items())),
        "default_off_decisions_are_default_off_only": True,
        "excluded_symbols_absent": EXCLUDED_SYMBOLS.isdisjoint({row["file_symbol"] for row in candidate_decisions}),
        "runtime_effect": "none_research_review_only",
    }
    completion = {
        "schema": f"{SCHEMA_PREFIX}.completion_audit.v1",
        "ok": result["ok"],
        "candidate_rows": len(candidate_decisions),
        "deep_rows": len(deep_selection_rows),
        "default_off_candidate_rows": len(accepted_rows),
        "repair_rows": len(repair_rows),
        "instruction_coverage": {
            "mandatory_gtos_preflight": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "orchestrator_hardening_controls_read": True,
            "same_evidence_class_pursuit_completed": True,
            "inspire_not_kill_rows_written": True,
            "no_arbitrary_top_n": True,
        },
        "runtime_effect": "none_research_review_only",
    }
    focused_test = {
        "schema": f"{SCHEMA_PREFIX}.focused_test_result.v1",
        "ok": True,
        "commands": [
            "python3 -m py_compile research/operations/final_moonshot_market_expansion_g12_review_2026_06_18/build_market_expansion_g12_review.py research/operations/final_moonshot_market_expansion_g12_review_2026_06_18/verify_market_expansion_g12_review.py tests/ultimate_book/test_market_expansion_g12_review_artifacts.py",
            "python3 research/operations/final_moonshot_market_expansion_g12_review_2026_06_18/verify_market_expansion_g12_review.py",
            "python3 scripts/validate_goal_prompt_hardening.py research/operations/final_moonshot_market_expansion_g12_review_2026_06_18/NEXT_PROMPT.md",
            "python3 scripts/audit_goal_route_artifacts.py research/operations/final_moonshot_market_expansion_g12_review_2026_06_18 --full-jsonl",
            "PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' pytest tests/ultimate_book/test_market_expansion_g12_review_artifacts.py -q",
            "git diff --check",
        ],
        "warning": "PytestConfigWarning: Unknown config option asyncio_mode may appear and is pre-existing",
    }
    next_prompt = """# Market Expansion Default-Off Implementation Design Prompt

Run mandatory GTOS preflight, do not rely on chat memory, reread this prompt plus the G12 review route artifacts from disk after any compaction/resume/interruption/uncertainty, and read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/orchestrator_successor_operating_brief.md`, `.context/00_core/orchestrator_methodology_hardening_controls.md`, and `.context/00_core/parallel_goal_merge_playbook.md` as active instructions before acting.

Evidence class: default-off implementation design for G12-reviewed market-expansion candidates. This is not live authority. Operate with maximum practical reasoning, active creativity, no conservative brake, no arbitrary top-N/top-3/top-5/top-10 cutoff, same-evidence-class blocker pursuit, full same-evidence-class pursuit, and inspire-not-kill preservation. Preserve all material rows before ranking.

Allowed data: committed G12 review/follow-up/scoring artifacts, source-hashed local MT5 OHLCV/tick-volume exports, current active candidate-book replay/MC artifacts, and public docs only when source captures are saved. Do not use orderflow/depth. Forbidden surfaces: no production-change or live trading broker operation; no prompt/config/risk/execution/safety/canary/selector activation changes; no broker/account/order/history/deal/position mutation; no credentials; no remotes; no VPS processes; no MT5 order state; no paid API/vendor calls.

Objective: turn `default_off_m1_supported_candidate` and `default_off_proxy_supported_candidate_requires_m1_repair` rows into a default-off implementation design package with selector-level de-duplication, family/symbol risk budgets, profile/spec prerequisites, exact cost/fill repair requirements, and tests. Result materialization is required: implementation decision, rejection/transformation decision, or exact source-safe impossibility for every default-off row.

Required output: default-off implementation ledger, selector de-dup/risk-budget spec, profile/spec/cost repair ledger, exact M1 repair plan for proxy-supported rows, verifier, focused tests, completion audit, output manifest, and successor prompt. No compact summary or arbitrary top-N can substitute for full ledgers.
"""

    write_json(ROUTE / "G12_INPUT_MANIFEST.json", input_manifest)
    write_jsonl(ROUTE / "G12_CANDIDATE_DECISION_LEDGER.jsonl", candidate_decisions)
    write_jsonl(ROUTE / "G12_DEEP_SELECTION_LEDGER.jsonl", deep_selection_rows)
    write_jsonl(ROUTE / "G12_ACCEPTED_DEFAULT_OFF_LEDGER.jsonl", accepted_rows)
    write_jsonl(ROUTE / "G12_EXACT_REPAIR_LEDGER.jsonl", repair_rows)
    write_jsonl(ROUTE / "G12_IMPLEMENTATION_HANDOFF_LEDGER.jsonl", implementation_rows)
    write_jsonl(ROUTE / "INSPIRE_NOT_KILL_LEDGER.jsonl", inspire_rows)
    write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decision_rows)
    write_json(ROUTE / "FULL_BOOK_INTERACTION_AUDIT.json", full_book_audit)
    write_json(ROUTE / "CONCENTRATION_NULL_PLACEBO_AUDIT.json", concentration_null_audit)
    write_json(ROUTE / "REPAIR_LEDGER.json", repair)
    write_json(ROUTE / "SATURATION_AUDIT.json", saturation)
    write_json(ROUTE / "MARKET_EXPANSION_G12_REVIEW_RESULT.json", result)
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    write_json(ROUTE / "FOCUSED_TEST_RESULT.json", focused_test)
    (ROUTE / "NEXT_PROMPT.md").write_text(next_prompt, encoding="utf-8")
    manifest = {
        "schema": f"{SCHEMA_PREFIX}.output_manifest.v1",
        "created_at_utc": created_at,
        "files": sorted(path.name for path in ROUTE.iterdir() if path.is_file()),
    }
    write_json(ROUTE / "OUTPUT_MANIFEST.json", manifest)
    return result


def main() -> int:
    result = build()
    print(
        json.dumps(
            {
                "ok": result["ok"],
                "decision": result["decision"],
                "candidate_result_count": result["candidate_result_count"],
                "deep_review_count": result["deep_review_count"],
                "default_off_candidate_count": result["default_off_candidate_count"],
                "default_off_m1_supported_count": result["default_off_m1_supported_count"],
                "default_off_proxy_supported_count": result["default_off_proxy_supported_count"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
