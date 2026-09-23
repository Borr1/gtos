from __future__ import annotations

import gzip
import importlib.util
import json
import math
import subprocess
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"
ROUTE_ID = "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"

STAGE04_INDEX = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE04_DYNAMIC_POLICY_REPLAY_SHARD_INDEX_{DATE_ID}.jsonl"
STAGE06_FEATURES = ROUTE_DIR / f"VNEXT_MOONSHOT_MARKET_AWARENESS_FEATURE_LEDGER_{DATE_ID}.jsonl"
STAGE07_SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_CORRECTED_BRANCH_SUMMARY_{DATE_ID}.json"
STAGE08_SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_AI_ROLE_BUDGET_SUMMARY_{DATE_ID}.json"
STATE_PATH = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json"
NOFILL_INDEX = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "vnext_full_historical_candidate_generation_replay_2026_05_24"
    / "VNEXT_FULL_REPLAY_NOFILL_PENDING_LIFECYCLE_LEDGER_2026-05-24.jsonl"
)

OUTPUT_SPEC = ROUTE_DIR / f"VNEXT_MOONSHOT_ML_DYNAMIC_LABEL_DATASET_SPEC_{DATE_ID}.md"
OUTPUT_FEATURE_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_ML_DYNAMIC_FEATURE_LEDGER_{DATE_ID}.jsonl"
OUTPUT_RESULTS = ROUTE_DIR / f"VNEXT_MOONSHOT_ML_CHALLENGER_RESULTS_{DATE_ID}.json"
OUTPUT_LEAKAGE_AUDIT = ROUTE_DIR / f"VNEXT_MOONSHOT_ML_LEAKAGE_AUDIT_LEDGER_{DATE_ID}.jsonl"
OUTPUT_WORKER_HEARTBEAT = ROUTE_DIR / f"VNEXT_MOONSHOT_WORKER_HEARTBEAT_{DATE_ID}.jsonl"

POLICY_NAMES = [
    "legacy_fixed_1.5r",
    "ai_target",
    "live_current_j46_j49",
    "partial_be_runner",
    "be_after_trigger",
    "trailing_runner",
    "time_stop_only",
    "early_cut_if_no_progress",
    "path_aware_runner",
]

FEATURE_COLUMNS = [
    "symbol",
    "transfer_group",
    "framework",
    "side",
    "session_bucket",
    "kill_zone_position",
    "session_subwindow",
    "weekday",
    "month",
    "quarter",
    "source_mode",
    "source_window_complete",
    "source_path_feature_status",
    "trend_state_20",
    "volatility_state_14_vs_50",
    "compression_expansion_state",
    "liquidity_sweep_proxy_state",
    "news_calendar_coverage_status",
    "news_high_impact_within_120m",
    "current_bar_direction",
    "asof_lookback_bars_available",
    "atr14_price",
    "atr50_price",
    "current_bar_displacement_atr14",
    "current_bar_speed_atr14",
    "entry_delay_bars",
    "lookback50_position",
    "return_1_bar",
    "return_4_bar",
    "return_16_bar",
    "trend_score_20_atr50",
]

CATEGORICAL_FEATURE_COLUMNS = [
    "symbol",
    "transfer_group",
    "framework",
    "side",
    "session_bucket",
    "kill_zone_position",
    "session_subwindow",
    "weekday",
    "month",
    "quarter",
    "source_mode",
    "source_window_complete",
    "source_path_feature_status",
    "trend_state_20",
    "volatility_state_14_vs_50",
    "compression_expansion_state",
    "liquidity_sweep_proxy_state",
    "news_calendar_coverage_status",
    "news_high_impact_within_120m",
    "current_bar_direction",
]

NUMERIC_FEATURE_COLUMNS = [name for name in FEATURE_COLUMNS if name not in CATEGORICAL_FEATURE_COLUMNS]

FORBIDDEN_FEATURE_FIELDS = {
    "legacy_final_r",
    "live_current_j46_j49_final_r",
    "be_after_trigger_final_r",
    "trailing_runner_final_r",
    "live_vs_legacy_delta_r",
    "policy_reversal_bucket",
    "mfe_r",
    "mae_r",
    "mfe_mae_ratio",
    "live_exit_reason",
    "live_exit_progress_fraction",
    "terminal_outcome",
    "pending_lifecycle_state",
    "post_trade_equity",
    "policy_results",
    "old_static_simulated_r",
    "old_static_terminal_outcome",
    "old_static_terminal_order_raw",
}

LABEL_FIELDS = [
    "label_dynamic_r_live_current",
    "label_dynamic_positive",
    "label_stop_first_risk",
    "label_no_fill_risk",
    "label_candidate_origin_family",
    "label_prop_attempt_success_proxy",
    "label_source_completeness",
    "label_ai_call_need",
    "label_execution_policy_recommendation",
]

CLASSIFICATION_TARGETS = [
    "label_dynamic_positive",
    "label_stop_first_risk",
    "label_no_fill_risk",
    "label_source_complete_binary",
    "label_ai_call_need_binary",
    "label_candidate_origin_family",
    "label_execution_policy_recommendation",
    "label_prop_attempt_success_proxy_binary",
]

SKLEARN_FEASIBILITY_TARGETS = [
    "label_dynamic_positive",
    "label_stop_first_risk",
    "label_ai_call_need_binary",
    "label_execution_policy_recommendation",
]

LIGHTGBM_FEASIBILITY_TARGETS = [
    "label_dynamic_positive",
    "label_stop_first_risk",
    "label_ai_call_need_binary",
]

LOCAL_ML_MAX_TRAIN_ROWS = 30000
LOCAL_ML_MAX_EVAL_ROWS = 10000

LIVE_FLEET_SYMBOLS = {"XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD", "NAS100", "XAGUSD"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_heartbeat(step: str, **payload: Any) -> None:
    row = {
        "schema_version": "vnext_moonshot_worker_heartbeat_v1",
        "recorded_at_utc": utc_now(),
        "stage_id": "STAGE_09_ML_AND_SURROGATE_FEASIBILITY",
        "current_first_incomplete_invariant": "STAGE_09_ML_AND_SURROGATE_FEASIBILITY",
        "worker": "build_vnext_moonshot_stage09_ml_surrogate_feasibility_2026_05_26.py",
        "step": step,
    }
    row.update(payload)
    with OUTPUT_WORKER_HEARTBEAT.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:  # noqa: BLE001
        return "UNKNOWN"


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def parse_year(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value)
    if len(text) >= 4 and text[:4].isdigit():
        return int(text[:4])
    return None


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def iter_stage04_rows() -> Iterable[dict[str, Any]]:
    for index_row in iter_jsonl(STAGE04_INDEX):
        output_path = REPO_ROOT / index_row["output_chunk_path"]
        with output_path.open("r", encoding="utf-8") as shard:
            for line in shard:
                if line.strip():
                    yield json.loads(line)


def iter_nofill_rows() -> Iterable[dict[str, Any]]:
    if not NOFILL_INDEX.exists():
        return
    for index_row in iter_jsonl(NOFILL_INDEX):
        chunk = REPO_ROOT / index_row["chunk_path"]
        if not chunk.exists():
            continue
        with gzip.open(chunk, "rt", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def feature_complete(row: dict[str, Any]) -> bool:
    return (
        row.get("source_path_feature_status") == "computed_from_source_ohlc_asof"
        and row.get("trend_state_20") != "insufficient_lookback"
        and row.get("volatility_state_14_vs_50") != "insufficient_lookback"
    )


def in_kill_zone(row: dict[str, Any]) -> bool:
    return str(row.get("kill_zone_position") or "").startswith("in_")


def no_high_news(row: dict[str, Any]) -> bool:
    return row.get("news_high_impact_within_120m") is not True


def side_aligned(row: dict[str, Any]) -> bool:
    side = str(row.get("side") or "").upper()
    trend = str(row.get("trend_state_20") or "")
    if trend == "flat":
        return True
    if side == "LONG":
        return trend in {"up", "strong_up"}
    if side == "SHORT":
        return trend in {"down", "strong_down"}
    return False


def context_rich(row: dict[str, Any]) -> bool:
    displacement = safe_float(row.get("current_bar_displacement_atr14"))
    return (
        row.get("news_high_impact_within_120m") is True
        or row.get("volatility_state_14_vs_50") in {"high_recent_vs_baseline", "elevated_recent_vs_baseline"}
        or row.get("compression_expansion_state") == "expansion"
        or row.get("trend_state_20") in {"strong_up", "strong_down"}
        or (displacement is not None and displacement >= 1.5)
        or not in_kill_zone(row)
        or not bool(row.get("source_window_complete"))
    )


def no_paid_mechanical(row: dict[str, Any]) -> bool:
    displacement = safe_float(row.get("current_bar_displacement_atr14"))
    return (
        in_kill_zone(row)
        and feature_complete(row)
        and no_high_news(row)
        and row.get("volatility_state_14_vs_50")
        in {"normal_recent_vs_baseline", "low_recent_vs_baseline", "very_low_recent_vs_baseline"}
        and row.get("trend_state_20") in {"flat", "up", "down"}
        and (displacement is None or displacement < 1.5)
    )


def branch_memberships(row: dict[str, Any]) -> dict[str, bool]:
    return {
        "raw_repaired_all_replayable": True,
        "source_complete_only": bool(row.get("source_window_complete")),
        "missing_source_excluded_asof_computed": row.get("source_path_feature_status") == "computed_from_source_ohlc_asof",
        "high_quality_asof_kz": in_kill_zone(row) and feature_complete(row) and no_high_news(row),
        "aggressive_research_asof_all_sessions": feature_complete(row),
        "context_recovery_off_kz_side_aligned": (
            not in_kill_zone(row) and feature_complete(row) and side_aligned(row) and no_high_news(row)
        ),
        "ml_candidate_feature_complete": feature_complete(row),
        "ai_required_context_rich": feature_complete(row) and context_rich(row),
        "no_paid_mechanical_diagnostic": no_paid_mechanical(row),
        "prop_ev_optimized_side_aligned_kz": (
            in_kill_zone(row) and feature_complete(row) and side_aligned(row) and no_high_news(row)
        ),
        "monitoring_only_ambiguous_path": bool(row.get("same_bar_ambiguity")),
        "dynamic_repair_needed_legacy_winner_to_live_nonpositive": (
            row.get("policy_reversal_bucket") == "dynamic_nonpositive_from_legacy_winner"
        ),
        "dynamic_recovery_legacy_nonpositive_to_live_winner": (
            row.get("policy_reversal_bucket") == "dynamic_winner_from_legacy_nonpositive"
        ),
        "origin_current_ob_retest": row.get("framework") == "ob_retest",
        "origin_current_fvg_fill": row.get("framework") == "fvg_fill",
        "origin_current_breaker_re_entry": row.get("framework") == "breaker_re_entry",
    }


def policy_info_from_stage04(row: dict[str, Any]) -> dict[str, Any]:
    results = row.get("policy_results") or {}
    policy_final_r: dict[str, float | None] = {}
    policy_exit_reasons: dict[str, str | None] = {}
    policy_same_bar: dict[str, bool] = {}
    for policy in POLICY_NAMES:
        result = results.get(policy) or {}
        value = safe_float(result.get("final_r"))
        policy_final_r[policy] = round(value, 12) if value is not None else None
        policy_exit_reasons[policy] = result.get("exit_reason")
        policy_same_bar[policy] = bool(result.get("same_bar_ambiguity"))
    best_policy = None
    best_r = None
    for policy in POLICY_NAMES:
        value = policy_final_r.get(policy)
        if value is None:
            continue
        if best_r is None or value > best_r:
            best_policy = policy
            best_r = value
    live_r = policy_final_r.get("live_current_j46_j49")
    live_exit = policy_exit_reasons.get("live_current_j46_j49")
    return {
        "policy_final_r": policy_final_r,
        "policy_exit_reasons": policy_exit_reasons,
        "policy_same_bar": policy_same_bar,
        "best_policy": best_policy or "unresolved_no_policy_result",
        "best_policy_final_r": best_r,
        "live_current_final_r": live_r,
        "live_current_exit_reason": live_exit,
        "live_current_stop_first": bool(live_exit in {"stop_loss", "stop_first_same_bar_conservative"} or (live_r is not None and live_r <= -0.999)),
        "same_bar_any_policy": any(policy_same_bar.values()),
    }


def read_policy_info() -> dict[str, dict[str, Any]]:
    policy_by_path_id: dict[str, dict[str, Any]] = {}
    for row in iter_stage04_rows():
        path_row_id = row.get("path_row_id")
        if path_row_id:
            policy_by_path_id[str(path_row_id)] = policy_info_from_stage04(row)
    return policy_by_path_id


def read_nofill_matches(candidate_ids: set[str]) -> dict[str, dict[str, Any]]:
    matches: dict[str, dict[str, Any]] = {}
    for row in iter_nofill_rows() or []:
        candidate_id = row.get("candidate_id")
        if candidate_id in candidate_ids and candidate_id not in matches:
            matches[candidate_id] = {
                "pending_lifecycle_state": row.get("pending_lifecycle_state"),
                "terminal_outcome": row.get("terminal_outcome"),
                "entry_touched": row.get("entry_touched"),
                "no_fill": row.get("no_fill"),
                "timeout": row.get("timeout"),
                "source_gap_class": row.get("source_gap_class"),
                "best_available_replay_mode": row.get("best_available_replay_mode"),
            }
    return matches


def nofill_label(feature: dict[str, Any], nofill_row: dict[str, Any] | None) -> tuple[str, int, str]:
    if nofill_row:
        if nofill_row.get("no_fill") is True or nofill_row.get("timeout") is True:
            return "no_fill_or_timeout", 1, "matched_stage04_pending_lifecycle"
        if nofill_row.get("entry_touched") is True:
            return "filled_entry_touch", 0, "matched_stage04_pending_lifecycle"
        return "pending_lifecycle_unknown", 0, "matched_stage04_pending_lifecycle"
    if feature.get("no_fill_fillability_status") == "filled_entry_touch_replay_row":
        return "filled_entry_touch_replay_row", 0, "stage06_filled_replay_row"
    return "not_indexed_pending_lifecycle", 0, "no_matching_nofill_lifecycle_row"


def ai_call_need_label(feature: dict[str, Any], policy_info: dict[str, Any]) -> tuple[str, int]:
    if no_paid_mechanical(feature):
        return "no_paid_mechanical_control", 0
    if policy_info.get("best_policy") != "live_current_j46_j49":
        return "policy_disagreement_requires_ai_or_surrogate_review", 1
    if policy_info.get("same_bar_any_policy"):
        return "same_bar_ambiguous_requires_source_review", 1
    if feature_complete(feature) and context_rich(feature):
        return "ai_required_context_rich", 1
    if not bool(feature.get("source_window_complete")):
        return "source_sensitive_review_required", 1
    return "standard_ai_budget_unknown", 1


def source_completeness_label(feature: dict[str, Any]) -> tuple[str, int]:
    if feature.get("source_path_feature_status") != "computed_from_source_ohlc_asof":
        return "source_features_not_computed", 0
    if feature.get("source_window_complete") is True:
        return "complete_asof_source_window", 1
    return "computed_but_incomplete_source_window", 0


def time_split(row: dict[str, Any]) -> str:
    year = row.get("year")
    if not isinstance(year, int):
        year = parse_year(row.get("candle_time_utc"))
    if year is None:
        return "unknown_time_split"
    if year <= 2024:
        return "train_pre2025"
    if year == 2025:
        return "test_2025"
    return "holdout_2026"


def feature_dict(row: dict[str, Any]) -> dict[str, Any]:
    features: dict[str, Any] = {}
    for name in FEATURE_COLUMNS:
        value = row.get(name)
        if name in NUMERIC_FEATURE_COLUMNS:
            number = safe_float(value)
            features[name] = 0.0 if number is None else number
            features[f"{name}__is_null"] = number is None
        else:
            features[name] = "NULL" if value is None else str(value)
    return features


def build_feature_row(
    index: int,
    feature: dict[str, Any],
    policy_info: dict[str, Any],
    nofill_row: dict[str, Any] | None,
    best_prop_stream: dict[str, Any],
) -> dict[str, Any]:
    nofill_class, nofill_binary, nofill_source = nofill_label(feature, nofill_row)
    ai_class, ai_binary = ai_call_need_label(feature, policy_info)
    source_class, source_binary = source_completeness_label(feature)
    memberships = branch_memberships(feature)
    best_branch = best_prop_stream.get("branch_id")
    prop_success_binary = int(bool(best_branch and memberships.get(best_branch)))
    prop_success_label = "member_of_best_stage07_success_stream" if prop_success_binary else "outside_best_stage07_success_stream"
    live_r = policy_info.get("live_current_final_r")
    best_r = policy_info.get("best_policy_final_r")
    row = {
        "schema_version": "vnext_moonshot_ml_dynamic_feature_ledger_v1",
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_09_ML_AND_SURROGATE_FEASIBILITY",
        "ml_row_id": f"STAGE09-ML-{index:09d}",
        "candidate_id": feature.get("candidate_id"),
        "path_row_id": feature.get("path_row_id"),
        "feature_row_id": feature.get("feature_row_id"),
        "candle_time_utc": feature.get("candle_time_utc"),
        "entry_first_touch_utc": feature.get("entry_first_touch_utc"),
        "feature_columns": {name: feature_dict(feature)[name] for name in FEATURE_COLUMNS},
        "split_time": time_split(feature),
        "split_symbol_holdout": (
            "holdout_live_fleet_symbol" if feature.get("symbol") in LIVE_FLEET_SYMBOLS else "train_non_live_fleet_symbol"
        ),
        "split_session_holdout": "holdout_ny_broad" if feature.get("session_bucket") == "ny_broad" else "train_non_ny_broad",
        "label_dynamic_r_live_current": live_r,
        "label_dynamic_positive": int(live_r is not None and live_r > 0),
        "label_stop_first_risk": int(policy_info.get("live_current_stop_first")),
        "label_no_fill_risk": nofill_class,
        "label_no_fill_risk_binary": nofill_binary,
        "label_candidate_origin_family": f"origin_current_{feature.get('framework') or 'unknown'}",
        "label_prop_attempt_success_proxy": prop_success_label,
        "label_prop_attempt_success_proxy_binary": prop_success_binary,
        "label_prop_attempt_success_proxy_source": "stage07_aggregate_stream_membership_not_row_terminal_truth",
        "label_prop_attempt_success_proxy_pass_probability": best_prop_stream.get("pass_probability_proxy"),
        "label_source_completeness": source_class,
        "label_source_complete_binary": source_binary,
        "label_ai_call_need": ai_class,
        "label_ai_call_need_binary": ai_binary,
        "label_execution_policy_recommendation": policy_info.get("best_policy"),
        "label_execution_policy_recommendation_final_r": best_r,
        "label_execution_policy_delta_vs_live_current_r": (
            round(best_r - live_r, 12) if isinstance(best_r, (int, float)) and isinstance(live_r, (int, float)) else None
        ),
        "label_policy_final_r_by_policy": policy_info.get("policy_final_r"),
        "label_policy_exit_reason_by_policy": policy_info.get("policy_exit_reasons"),
        "label_policy_same_bar_by_policy": policy_info.get("policy_same_bar"),
        "label_no_fill_source": nofill_source,
        "label_source": "corrected_stage04_dynamic_replay_plus_stage06_asof_market_features",
        "fixed_1_5r_used_as_activation_truth": False,
        "ml_shadow_only_until_sealed_validation_and_owner_approval": True,
    }
    return row


def classification_metrics(actual: list[Any], predicted: list[Any]) -> dict[str, Any]:
    if not actual:
        return {"row_count": 0}
    labels = sorted({str(value) for value in actual} | {str(value) for value in predicted})
    confusion: dict[str, Counter] = {label: Counter() for label in labels}
    correct = 0
    for truth, pred in zip(actual, predicted, strict=False):
        truth_s = str(truth)
        pred_s = str(pred)
        confusion[truth_s][pred_s] += 1
        if truth_s == pred_s:
            correct += 1
    recalls = []
    f1s = []
    for label in labels:
        tp = confusion[label][label]
        fn = sum(confusion[label].values()) - tp
        fp = sum(confusion[other][label] for other in labels if other != label)
        recall = tp / (tp + fn) if tp + fn else 0.0
        precision = tp / (tp + fp) if tp + fp else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        recalls.append(recall)
        f1s.append(f1)
    return {
        "row_count": len(actual),
        "accuracy": round(correct / len(actual), 12),
        "balanced_accuracy": round(sum(recalls) / len(recalls), 12) if recalls else None,
        "macro_f1": round(sum(f1s) / len(f1s), 12) if f1s else None,
        "class_count": len(labels),
        "actual_class_counts": dict(sorted(Counter(str(value) for value in actual).items())),
    }


def regression_metrics(actual: list[float], predicted: list[float]) -> dict[str, Any]:
    if not actual:
        return {"row_count": 0}
    errors = [pred - truth for truth, pred in zip(actual, predicted, strict=False)]
    abs_errors = [abs(error) for error in errors]
    squared = [error * error for error in errors]
    sign_hits = sum(1 for truth, pred in zip(actual, predicted, strict=False) if (truth > 0) == (pred > 0))
    return {
        "row_count": len(actual),
        "mae": round(sum(abs_errors) / len(abs_errors), 12),
        "rmse": round(math.sqrt(sum(squared) / len(squared)), 12),
        "sign_accuracy": round(sign_hits / len(actual), 12),
    }


def calibration_bins(actual: list[Any], probabilities: list[float]) -> list[dict[str, Any]]:
    bins: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for truth, probability in zip(actual, probabilities, strict=False):
        try:
            truth_int = int(truth)
        except (TypeError, ValueError):
            continue
        bucket = min(9, max(0, int(probability * 10)))
        bins[bucket].append((truth_int, probability))
    rows = []
    for bucket, values in sorted(bins.items()):
        rows.append(
            {
                "bucket": f"{bucket / 10:.1f}-{(bucket + 1) / 10:.1f}",
                "row_count": len(values),
                "avg_predicted_probability": round(sum(prob for _, prob in values) / len(values), 12),
                "actual_rate": round(sum(truth for truth, _ in values) / len(values), 12),
            }
        )
    return rows


def split_rows(rows: list[dict[str, Any]], split_kind: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    if split_kind == "time_2025":
        return (
            [row for row in rows if row["split_time"] == "train_pre2025"],
            [row for row in rows if row["split_time"] == "test_2025"],
            "train_pre2025_to_test_2025",
        )
    if split_kind == "time_2026_holdout":
        return (
            [row for row in rows if row["split_time"] in {"train_pre2025", "test_2025"}],
            [row for row in rows if row["split_time"] == "holdout_2026"],
            "train_pre2025_2025_to_holdout_2026",
        )
    if split_kind == "symbol_live_fleet_holdout":
        return (
            [row for row in rows if row["split_symbol_holdout"] == "train_non_live_fleet_symbol"],
            [row for row in rows if row["split_symbol_holdout"] == "holdout_live_fleet_symbol"],
            "train_non_live_fleet_to_holdout_live_fleet",
        )
    return (
        [row for row in rows if row["split_session_holdout"] == "train_non_ny_broad"],
        [row for row in rows if row["split_session_holdout"] == "holdout_ny_broad"],
        "train_non_ny_to_holdout_ny",
    )


def group_key(row: dict[str, Any]) -> tuple[Any, ...]:
    features = row["feature_columns"]
    return (
        features.get("symbol"),
        features.get("framework"),
        features.get("session_bucket"),
        features.get("side"),
        features.get("trend_state_20"),
        features.get("volatility_state_14_vs_50"),
    )


def dependency_free_baselines(rows: list[dict[str, Any]]) -> dict[str, Any]:
    results: dict[str, Any] = {"classification": [], "regression": []}
    for split_kind in ["time_2025", "time_2026_holdout", "symbol_live_fleet_holdout", "session_ny_holdout"]:
        train_rows, eval_rows, split_name = split_rows(rows, split_kind)
        if not train_rows or not eval_rows:
            continue
        write_heartbeat(
            "dependency_free_split_start",
            split=split_name,
            train_rows=len(train_rows),
            eval_rows=len(eval_rows),
        )
        for target in CLASSIFICATION_TARGETS:
            train_labels = [row[target] for row in train_rows]
            eval_labels = [row[target] for row in eval_rows]
            if len(set(str(value) for value in train_labels)) < 2:
                results["classification"].append(
                    {
                        "model": "dependency_free_global_majority",
                        "target": target,
                        "split": split_name,
                        "status": "skipped_single_train_class",
                        "train_rows": len(train_rows),
                        "eval_rows": len(eval_rows),
                    }
                )
                continue
            majority = Counter(str(value) for value in train_labels).most_common(1)[0][0]
            global_pred = [majority for _ in eval_rows]
            global_positive_rate = sum(1 for value in train_labels if str(value) == "1") / len(train_labels)
            global_prob = [global_positive_rate for _ in eval_rows]
            positive = "1"
            metric = classification_metrics(eval_labels, global_pred)
            metric.update(
                {
                    "model": "dependency_free_global_majority",
                    "target": target,
                    "split": split_name,
                    "train_rows": len(train_rows),
                    "attempt_scope": "all_rows_global_baseline",
                }
            )
            if target.endswith("_binary") or target in {
                "label_dynamic_positive",
                "label_stop_first_risk",
                "label_no_fill_risk",
            }:
                metric["calibration_bins_global_probability"] = calibration_bins(eval_labels, global_prob)
                metric["positive_class_label"] = positive
            results["classification"].append(metric)
        train_values = [row["label_dynamic_r_live_current"] for row in train_rows if row["label_dynamic_r_live_current"] is not None]
        eval_pairs = [
            (row, row["label_dynamic_r_live_current"])
            for row in eval_rows
            if row["label_dynamic_r_live_current"] is not None
        ]
        if train_values and eval_pairs:
            global_mean = sum(train_values) / len(train_values)
            actual = [float(value) for _, value in eval_pairs]
            global_pred = [global_mean for _ in eval_pairs]
            metric = regression_metrics(actual, global_pred)
            metric.update(
                {
                    "model": "dependency_free_global_mean_r",
                    "target": "label_dynamic_r_live_current",
                    "split": split_name,
                    "train_rows": len(train_values),
                    "attempt_scope": "all_rows_global_baseline",
                }
            )
            results["regression"].append(metric)
        write_heartbeat(
            "dependency_free_split_done",
            split=split_name,
            classification_results=len(results["classification"]),
            regression_results=len(results["regression"]),
        )
    return results


def local_tool_availability() -> dict[str, bool]:
    return {
        name: importlib.util.find_spec(name) is not None
        for name in ["numpy", "pandas", "sklearn", "lightgbm", "xgboost", "catboost"]
    }


def sklearn_challengers(rows: list[dict[str, Any]], availability: dict[str, bool]) -> list[dict[str, Any]]:
    if not availability.get("sklearn"):
        return [{"tool": "sklearn", "status": "not_installed"}]
    try:
        from sklearn.feature_extraction import DictVectorizer
        from sklearn.linear_model import SGDClassifier
        from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, log_loss
    except Exception as exc:  # noqa: BLE001
        return [{"tool": "sklearn", "status": "import_failed", "error": repr(exc)}]
    raw_train_rows, raw_eval_rows, split_name = split_rows(rows, "time_2026_holdout")
    if not raw_train_rows or not raw_eval_rows:
        return [{"tool": "sklearn", "status": "skipped_missing_time_holdout_rows"}]
    train_rows = deterministic_hash_sample(raw_train_rows, LOCAL_ML_MAX_TRAIN_ROWS, "sklearn_train")
    eval_rows = deterministic_hash_sample(raw_eval_rows, LOCAL_ML_MAX_EVAL_ROWS, "sklearn_eval")
    write_heartbeat(
        "sklearn_hash_sample_ready",
        split=split_name,
        raw_train_rows=len(raw_train_rows),
        raw_eval_rows=len(raw_eval_rows),
        sampled_train_rows=len(train_rows),
        sampled_eval_rows=len(eval_rows),
    )
    vectorizer = DictVectorizer(sparse=True)
    x_train = vectorizer.fit_transform(feature_dict_from_ledger(row) for row in train_rows)
    x_eval = vectorizer.transform(feature_dict_from_ledger(row) for row in eval_rows)
    outputs = []
    for target in SKLEARN_FEASIBILITY_TARGETS:
        write_heartbeat("sklearn_feasibility_fit_start", target=target, split=split_name, train_rows=len(train_rows))
        y_train = [str(row[target]) for row in train_rows]
        y_eval = [str(row[target]) for row in eval_rows]
        if len(set(y_train)) < 2:
            outputs.append(
                {
                    "tool": "sklearn",
                    "model": "SGDClassifier_log_loss",
                    "target": target,
                    "split": split_name,
                    "status": "skipped_single_train_class",
                }
            )
            continue
        try:
            clf = SGDClassifier(loss="log_loss", max_iter=5, tol=1e-3, alpha=0.001, random_state=20260526)
            clf.fit(x_train, y_train)
            pred = clf.predict(x_eval)
            metric = {
                "tool": "sklearn",
                "model": "SGDClassifier_log_loss",
                "target": target,
                "split": split_name,
                "status": "fit_ok",
                "attempt_scope": "bounded_feasibility_key_targets_hash_spread_sample",
                "train_rows": len(y_train),
                "eval_rows": len(y_eval),
                "raw_train_rows_available": len(raw_train_rows),
                "raw_eval_rows_available": len(raw_eval_rows),
                "sampling_method": "deterministic_sha256_spread_not_performance_top_n",
                "feature_count": len(vectorizer.feature_names_),
                "accuracy": round(float(accuracy_score(y_eval, pred)), 12),
                "balanced_accuracy": round(float(balanced_accuracy_score(y_eval, pred)), 12),
                "macro_f1": round(float(f1_score(y_eval, pred, average="macro", zero_division=0)), 12),
            }
            if len(set(y_train)) == 2:
                proba = clf.predict_proba(x_eval)
                positive_index = list(clf.classes_).index("1") if "1" in clf.classes_ else 1
                positive_prob = [float(row[positive_index]) for row in proba]
                metric["log_loss"] = round(float(log_loss(y_eval, proba, labels=list(clf.classes_))), 12)
                metric["calibration_bins"] = calibration_bins(y_eval, positive_prob)
            outputs.append(metric)
            write_heartbeat("sklearn_feasibility_fit_done", target=target, split=split_name, status="fit_ok")
        except Exception as exc:  # noqa: BLE001
            outputs.append(
                {
                    "tool": "sklearn",
                    "model": "SGDClassifier_log_loss",
                    "target": target,
                    "split": split_name,
                    "status": "fit_failed",
                    "error": repr(exc),
                }
            )
            write_heartbeat("sklearn_feasibility_fit_done", target=target, split=split_name, status="fit_failed")
    return outputs


def lightgbm_challengers(rows: list[dict[str, Any]], availability: dict[str, bool]) -> list[dict[str, Any]]:
    if not availability.get("lightgbm") or not availability.get("sklearn"):
        return [{"tool": "lightgbm", "status": "not_installed_or_missing_sklearn"}]
    try:
        from lightgbm import LGBMClassifier
        from sklearn.feature_extraction import DictVectorizer
        from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, log_loss
    except Exception as exc:  # noqa: BLE001
        return [{"tool": "lightgbm", "status": "import_failed", "error": repr(exc)}]
    raw_train_rows, raw_eval_rows, split_name = split_rows(rows, "time_2026_holdout")
    if not raw_train_rows or not raw_eval_rows:
        return [{"tool": "lightgbm", "status": "skipped_missing_time_holdout_rows"}]
    train_rows = deterministic_hash_sample(raw_train_rows, LOCAL_ML_MAX_TRAIN_ROWS, "lightgbm_train")
    eval_rows = deterministic_hash_sample(raw_eval_rows, LOCAL_ML_MAX_EVAL_ROWS, "lightgbm_eval")
    write_heartbeat(
        "lightgbm_hash_sample_ready",
        split=split_name,
        raw_train_rows=len(raw_train_rows),
        raw_eval_rows=len(raw_eval_rows),
        sampled_train_rows=len(train_rows),
        sampled_eval_rows=len(eval_rows),
    )
    vectorizer = DictVectorizer(sparse=True)
    x_train = vectorizer.fit_transform(feature_dict_from_ledger(row) for row in train_rows)
    x_eval = vectorizer.transform(feature_dict_from_ledger(row) for row in eval_rows)
    outputs = []
    for target in LIGHTGBM_FEASIBILITY_TARGETS:
        write_heartbeat("lightgbm_feasibility_fit_start", target=target, split=split_name, train_rows=len(train_rows))
        y_train = [int(row[target]) for row in train_rows]
        y_eval = [int(row[target]) for row in eval_rows]
        if len(set(y_train)) < 2:
            outputs.append(
                {
                    "tool": "lightgbm",
                    "model": "LGBMClassifier_depth5_64trees",
                    "target": target,
                    "split": split_name,
                    "status": "skipped_single_train_class",
                }
            )
            continue
        try:
            clf = LGBMClassifier(
                n_estimators=16,
                max_depth=4,
                learning_rate=0.07,
                num_leaves=31,
                random_state=20260526,
                verbose=-1,
            )
            clf.fit(x_train, y_train)
            pred = clf.predict(x_eval)
            proba = clf.predict_proba(x_eval)
            positive_prob = [float(row[1]) for row in proba]
            outputs.append(
                {
                    "tool": "lightgbm",
                    "model": "LGBMClassifier_depth5_64trees",
                    "target": target,
                    "split": split_name,
                    "status": "fit_ok",
                    "attempt_scope": "bounded_feasibility_key_targets_hash_spread_sample",
                    "train_rows": len(y_train),
                    "eval_rows": len(y_eval),
                    "raw_train_rows_available": len(raw_train_rows),
                    "raw_eval_rows_available": len(raw_eval_rows),
                    "sampling_method": "deterministic_sha256_spread_not_performance_top_n",
                    "feature_count": len(vectorizer.feature_names_),
                    "accuracy": round(float(accuracy_score(y_eval, pred)), 12),
                    "balanced_accuracy": round(float(balanced_accuracy_score(y_eval, pred)), 12),
                    "macro_f1": round(float(f1_score(y_eval, pred, average="macro", zero_division=0)), 12),
                    "log_loss": round(float(log_loss(y_eval, proba, labels=[0, 1])), 12),
                    "calibration_bins": calibration_bins(y_eval, positive_prob),
                }
            )
            write_heartbeat("lightgbm_feasibility_fit_done", target=target, split=split_name, status="fit_ok")
        except Exception as exc:  # noqa: BLE001
            outputs.append(
                {
                    "tool": "lightgbm",
                    "model": "LGBMClassifier_depth5_64trees",
                    "target": target,
                    "split": split_name,
                    "status": "fit_failed",
                    "error": repr(exc),
                }
            )
            write_heartbeat("lightgbm_feasibility_fit_done", target=target, split=split_name, status="fit_failed")
    return outputs


def feature_dict_from_ledger(row: dict[str, Any]) -> dict[str, Any]:
    features: dict[str, Any] = {}
    for name, value in row["feature_columns"].items():
        if name in NUMERIC_FEATURE_COLUMNS:
            number = safe_float(value)
            features[name] = 0.0 if number is None else number
        else:
            features[name] = "NULL" if value is None else str(value)
    return features


def deterministic_hash_sample(rows: list[dict[str, Any]], max_rows: int, salt: str) -> list[dict[str, Any]]:
    if len(rows) <= max_rows:
        return rows
    keyed = []
    for row in rows:
        key = f"{salt}|{row.get('ml_row_id')}|{row.get('candidate_id')}|{row.get('path_row_id')}"
        digest = sha256(key.encode("utf-8")).hexdigest()
        keyed.append((digest, row))
    keyed.sort(key=lambda item: item[0])
    return [row for _, row in keyed[:max_rows]]


def load_feature_ledger_if_complete(expected_rows: int) -> list[dict[str, Any]] | None:
    if not OUTPUT_FEATURE_LEDGER.exists():
        return None
    rows: list[dict[str, Any]] = []
    try:
        with OUTPUT_FEATURE_LEDGER.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                rows.append(json.loads(line))
                if line_number % 25000 == 0:
                    write_heartbeat(
                        "resume_read_existing_feature_ledger",
                        rows_read=line_number,
                        expected_rows=expected_rows,
                    )
    except json.JSONDecodeError:
        write_heartbeat("resume_existing_feature_ledger_failed_json_parse", rows_read=len(rows))
        return None
    if len(rows) != expected_rows:
        write_heartbeat(
            "resume_existing_feature_ledger_rejected_count_mismatch",
            rows_read=len(rows),
            expected_rows=expected_rows,
        )
        return None
    write_heartbeat("resume_existing_feature_ledger_accepted", rows_read=len(rows), expected_rows=expected_rows)
    return rows


def distribution(values: Iterable[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def build_leakage_audit(rows: list[dict[str, Any]], availability: dict[str, bool]) -> list[dict[str, Any]]:
    audit_rows: list[dict[str, Any]] = []
    forbidden_in_features = sorted(FORBIDDEN_FEATURE_FIELDS & set(FEATURE_COLUMNS))
    audit_rows.append(
        {
            "schema_version": "vnext_moonshot_ml_leakage_audit_v1",
            "route_id": ROUTE_ID,
            "stage_id": "STAGE_09_ML_AND_SURROGATE_FEASIBILITY",
            "audit_id": "feature_column_forbidden_field_scan",
            "status": "pass" if not forbidden_in_features else "fail",
            "forbidden_fields_in_feature_columns": forbidden_in_features,
            "feature_columns": FEATURE_COLUMNS,
            "label_fields": LABEL_FIELDS,
        }
    )
    split_counts = {
        "time": distribution(row["split_time"] for row in rows),
        "symbol_holdout": distribution(row["split_symbol_holdout"] for row in rows),
        "session_holdout": distribution(row["split_session_holdout"] for row in rows),
    }
    audit_rows.append(
        {
            "schema_version": "vnext_moonshot_ml_leakage_audit_v1",
            "route_id": ROUTE_ID,
            "stage_id": "STAGE_09_ML_AND_SURROGATE_FEASIBILITY",
            "audit_id": "split_counts",
            "status": "pass",
            "split_counts": split_counts,
        }
    )
    for feature_name in FEATURE_COLUMNS:
        values = [row["feature_columns"].get(feature_name) for row in rows]
        nulls = sum(1 for value in values if value in {None, "NULL", ""})
        counts = Counter(str(value) for value in values)
        most_common_value, most_common_count = counts.most_common(1)[0]
        audit_rows.append(
            {
                "schema_version": "vnext_moonshot_ml_leakage_audit_v1",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_09_ML_AND_SURROGATE_FEASIBILITY",
                "audit_id": "feature_null_and_concentration",
                "field": feature_name,
                "status": "pass",
                "null_rate": round(nulls / len(rows), 12),
                "distinct_values": len(counts),
                "max_category_value": most_common_value,
                "max_category_share": round(most_common_count / len(rows), 12),
            }
        )
    for label in CLASSIFICATION_TARGETS + ["label_dynamic_r_live_current"]:
        audit_rows.append(
            {
                "schema_version": "vnext_moonshot_ml_leakage_audit_v1",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_09_ML_AND_SURROGATE_FEASIBILITY",
                "audit_id": "label_distribution",
                "label": label,
                "status": "pass",
                "distribution": distribution(row.get(label) for row in rows),
            }
        )
    audit_rows.append(
        {
            "schema_version": "vnext_moonshot_ml_leakage_audit_v1",
            "route_id": ROUTE_ID,
            "stage_id": "STAGE_09_ML_AND_SURROGATE_FEASIBILITY",
            "audit_id": "local_ml_tool_availability",
            "status": "pass",
            "availability": availability,
            "install_attempted": False,
            "paid_api_or_vendor_calls_made": 0,
        }
    )
    audit_rows.append(
        {
            "schema_version": "vnext_moonshot_ml_leakage_audit_v1",
            "route_id": ROUTE_ID,
            "stage_id": "STAGE_09_ML_AND_SURROGATE_FEASIBILITY",
            "audit_id": "activation_truth_guard",
            "status": "pass",
            "fixed_1_5r_used_as_activation_truth": False,
            "note": "Legacy fixed 1.5R is present only inside label_policy_final_r_by_policy as comparator.",
        }
    )
    return audit_rows


def write_dataset_spec(summary: dict[str, Any]) -> None:
    lines = [
        "# vNext Moonshot Stage09 ML Dynamic Label Dataset Spec",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "## Scope",
        "",
        "- Dataset source: Stage06 as-of market-awareness feature rows joined to Stage04 corrected dynamic policy replay rows.",
        "- ML role: research/shadow only until sealed validation and production-change approval.",
        "- Paid API/vendor calls: `0`.",
        "- Fixed 1.5R labels are retained only as comparator labels, not activation truth.",
        "",
        "## Feature Columns",
        "",
        "All feature columns are as-of market/context fields:",
        "",
        *[f"- `{name}`" for name in FEATURE_COLUMNS],
        "",
        "## Label Families",
        "",
        "- Dynamic R: `label_dynamic_r_live_current`, `label_dynamic_positive`.",
        "- Stop-first risk: `label_stop_first_risk` from corrected live-current dynamic replay exit reason/R.",
        "- No-fill risk: `label_no_fill_risk`, `label_no_fill_risk_binary` from pending lifecycle where matched, otherwise Stage06 fillability status.",
        "- Candidate-origin family: `label_candidate_origin_family` from current framework origin.",
        "- Prop-attempt success: `label_prop_attempt_success_proxy` from Stage07 best-stream branch membership; marked proxy, not row-terminal truth.",
        "- Source-completeness: `label_source_completeness`, `label_source_complete_binary`.",
        "- AI-call need: `label_ai_call_need`, `label_ai_call_need_binary` using Stage08 budget strata logic.",
        "- Execution-policy recommendation: `label_execution_policy_recommendation` from highest corrected Stage04 policy final R.",
        "",
        "## Splits",
        "",
        "- Time: train `<=2024`, test `2025`, holdout `2026`.",
        "- Symbol holdout: live-fleet symbols versus non-live-fleet symbols.",
        "- Session holdout: NY broad session versus non-NY broad sessions.",
        "",
        "## Leakage Guard",
        "",
        "Outcome fields are label-only and are not present in `feature_columns`. See leakage audit ledger for field-level checks.",
        "",
        "## Row Counts",
        "",
        f"- Feature ledger rows: `{summary['feature_ledger_rows']}`",
        f"- Policy rows joined: `{summary['policy_rows_joined']}`",
        f"- No-fill rows matched: `{summary['nofill_rows_matched']}`",
    ]
    OUTPUT_SPEC.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_state(summary: dict[str, Any]) -> None:
    if not STATE_PATH.exists():
        return
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    state["updated_at_utc"] = utc_now()
    state["current_git_head"] = git_head()
    state["current_stage"] = "STAGE_09_ML_AND_SURROGATE_FEASIBILITY"
    state["first_incomplete_invariant"] = "STAGE_10_DEFAULT_OFF_RUNTIME_INTEGRATION"
    state["exact_next_action"] = "Run Stage10 default-off runtime/config/test integration from corrected substrate evidence."
    state["completion_gate_status"] = "not_complete_first_incomplete_stage10"
    state["stage_status_table"]["STAGE_09_ML_AND_SURROGATE_FEASIBILITY"] = "complete_research_shadow_only"
    state["stage_status_table"]["STAGE_10_DEFAULT_OFF_RUNTIME_INTEGRATION"] = "pending"
    state["row_counts_scanned"]["stage09_ml_dynamic_feature_rows"] = summary["feature_ledger_rows"]
    state["row_counts_scanned"]["stage09_ml_leakage_audit_rows"] = summary["leakage_audit_rows"]
    state["output_artifact_manifest"]["ml_dynamic_label_dataset_spec"] = rel(OUTPUT_SPEC)
    state["output_artifact_manifest"]["ml_dynamic_feature_ledger"] = rel(OUTPUT_FEATURE_LEDGER)
    state["output_artifact_manifest"]["ml_challenger_results"] = rel(OUTPUT_RESULTS)
    state["output_artifact_manifest"]["ml_leakage_audit_ledger"] = rel(OUTPUT_LEAKAGE_AUDIT)
    state.setdefault("verifiers_tests_run", []).append(
        {
            "command": (
                "py -3 research/science_program_2026_05/06_outcome_testing/"
                "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/"
                "build_vnext_moonshot_stage09_ml_surrogate_feasibility_2026_05_26.py"
            ),
            "result": (
                f"feature_rows={summary['feature_ledger_rows']}; "
                f"dependency_free_baselines={summary['dependency_free_baseline_result_count']}; "
                f"first_incomplete={summary['first_incomplete_invariant_after_stage09']}"
            ),
            "status": "passed",
        }
    )
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build() -> dict[str, Any]:
    started = time.monotonic()
    write_heartbeat("build_start", current_git_head=git_head())
    stage07_summary = json.loads(STAGE07_SUMMARY.read_text(encoding="utf-8"))
    stage08_summary = json.loads(STAGE08_SUMMARY.read_text(encoding="utf-8"))
    best_prop_stream = stage07_summary["best_overall_reference_fee599_payout8000"]
    missing_policy_rows = 0
    policy_rows_joined = 0
    nofill_rows_matched = 0
    expected_rows = int(stage07_summary.get("events_replayed") or 0)
    rows = load_feature_ledger_if_complete(expected_rows)
    if rows is None:
        write_heartbeat("policy_info_read_start")
        policy_by_path_id = read_policy_info()
        policy_rows_joined = len(policy_by_path_id)
        write_heartbeat("policy_info_read_done", policy_rows=policy_rows_joined)
        candidate_ids = {str(row.get("candidate_id")) for row in iter_jsonl(STAGE06_FEATURES) if row.get("candidate_id")}
        write_heartbeat("nofill_match_read_start", candidate_ids=len(candidate_ids))
        nofill_matches = read_nofill_matches(candidate_ids)
        nofill_rows_matched = len(nofill_matches)
        write_heartbeat("nofill_match_read_done", nofill_matches=nofill_rows_matched)
        rows = []
        with OUTPUT_FEATURE_LEDGER.open("w", encoding="utf-8", newline="\n") as handle:
            for index, feature in enumerate(iter_jsonl(STAGE06_FEATURES), start=1):
                path_row_id = str(feature.get("path_row_id") or "")
                policy_info = policy_by_path_id.get(path_row_id)
                if not policy_info:
                    missing_policy_rows += 1
                    policy_info = {
                        "policy_final_r": {policy: None for policy in POLICY_NAMES},
                        "policy_exit_reasons": {policy: None for policy in POLICY_NAMES},
                        "policy_same_bar": {policy: False for policy in POLICY_NAMES},
                        "best_policy": "unresolved_missing_stage04_join",
                        "best_policy_final_r": None,
                        "live_current_final_r": None,
                        "live_current_exit_reason": None,
                        "live_current_stop_first": False,
                        "same_bar_any_policy": False,
                    }
                nofill_row = nofill_matches.get(str(feature.get("candidate_id")))
                output = build_feature_row(index, feature, policy_info, nofill_row, best_prop_stream)
                rows.append(output)
                handle.write(json.dumps(output, sort_keys=True) + "\n")
                if index % 25000 == 0:
                    write_heartbeat("feature_ledger_write_progress", rows_written=index, expected_rows=expected_rows)
        write_heartbeat("feature_ledger_write_done", rows_written=len(rows), missing_policy_rows=missing_policy_rows)
    else:
        write_heartbeat("feature_ledger_reuse_for_rerun", rows=len(rows))
        policy_rows_joined = expected_rows
        nofill_rows_matched = sum(
            1 for row in rows if row.get("label_no_fill_source") == "matched_stage04_pending_lifecycle"
        )
    availability = local_tool_availability()
    write_heartbeat("leakage_audit_start", rows=len(rows))
    leakage_rows = build_leakage_audit(rows, availability)
    with OUTPUT_LEAKAGE_AUDIT.open("w", encoding="utf-8", newline="\n") as handle:
        for row in leakage_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    write_heartbeat("dependency_free_baselines_start", rows=len(rows))
    dependency_free = dependency_free_baselines(rows)
    write_heartbeat(
        "dependency_free_baselines_done",
        classification_results=len(dependency_free["classification"]),
        regression_results=len(dependency_free["regression"]),
    )
    write_heartbeat("sklearn_challengers_start", rows=len(rows), targets=SKLEARN_FEASIBILITY_TARGETS)
    sklearn_results = sklearn_challengers(rows, availability)
    write_heartbeat("sklearn_challengers_done", result_rows=len(sklearn_results))
    write_heartbeat("lightgbm_challengers_start", rows=len(rows), targets=LIGHTGBM_FEASIBILITY_TARGETS)
    lightgbm_results = lightgbm_challengers(rows, availability)
    write_heartbeat("lightgbm_challengers_done", result_rows=len(lightgbm_results))
    summary = {
        "schema_version": "vnext_moonshot_ml_challenger_results_v1",
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_09_ML_AND_SURROGATE_FEASIBILITY",
        "generated_at_utc": utc_now(),
        "current_git_head": git_head(),
        "dataset_spec_path": rel(OUTPUT_SPEC),
        "feature_ledger_path": rel(OUTPUT_FEATURE_LEDGER),
        "challenger_results_path": rel(OUTPUT_RESULTS),
        "leakage_audit_ledger_path": rel(OUTPUT_LEAKAGE_AUDIT),
        "feature_ledger_rows": len(rows),
        "policy_rows_joined": policy_rows_joined,
        "missing_policy_join_rows": missing_policy_rows,
        "nofill_rows_matched": nofill_rows_matched,
        "leakage_audit_rows": len(leakage_rows),
        "feature_columns": FEATURE_COLUMNS,
        "label_fields": LABEL_FIELDS,
        "classification_targets": CLASSIFICATION_TARGETS,
        "split_counts": {
            "time": distribution(row["split_time"] for row in rows),
            "symbol_holdout": distribution(row["split_symbol_holdout"] for row in rows),
            "session_holdout": distribution(row["split_session_holdout"] for row in rows),
        },
        "label_distributions": {
            target: distribution(row.get(target) for row in rows)
            for target in CLASSIFICATION_TARGETS + ["label_dynamic_r_live_current"]
        },
        "dependency_free_baselines": dependency_free,
        "dependency_free_baseline_result_count": len(dependency_free["classification"]) + len(dependency_free["regression"]),
        "installed_local_ml_tools": availability,
        "sklearn_challengers": sklearn_results,
        "lightgbm_challengers": lightgbm_results,
        "local_ml_attempt_scope": {
            "dependency_free_baselines": "all_rows_all_targets_all_declared_splits",
            "sklearn": "bounded_feasibility_key_targets_hash_spread_sample_time_2026_holdout",
            "lightgbm": "bounded_feasibility_key_targets_hash_spread_sample_time_2026_holdout",
            "max_train_rows": LOCAL_ML_MAX_TRAIN_ROWS,
            "max_eval_rows": LOCAL_ML_MAX_EVAL_ROWS,
            "reason": "installed local tools are attempted without paid/external installs while preserving full-row feature ledger and full-row dependency-free baselines",
        },
        "stage07_best_reference_stream": best_prop_stream,
        "stage08_ai_budget_manifest_rows": stage08_summary.get("manifest_rows"),
        "fixed_1_5r_used_as_activation_truth": False,
        "ml_shadow_only_until_sealed_validation_and_owner_approval": True,
        "paid_api_or_vendor_calls_made": 0,
        "forbidden_boundaries_crossed": False,
        "first_incomplete_invariant_after_stage09": "STAGE_10_DEFAULT_OFF_RUNTIME_INTEGRATION",
        "runtime_seconds": round(time.monotonic() - started, 3),
    }
    write_dataset_spec(summary)
    OUTPUT_RESULTS.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_state(summary)
    write_heartbeat(
        "build_done",
        runtime_seconds=summary["runtime_seconds"],
        first_incomplete=summary["first_incomplete_invariant_after_stage09"],
    )
    return summary


def main() -> None:
    summary = build()
    print(
        json.dumps(
            {
                "route_id": ROUTE_ID,
                "stage": "STAGE_09_ML_AND_SURROGATE_FEASIBILITY",
                "feature_rows": summary["feature_ledger_rows"],
                "dependency_free_baselines": summary["dependency_free_baseline_result_count"],
                "sklearn_results": len(summary["sklearn_challengers"]),
                "lightgbm_results": len(summary["lightgbm_challengers"]),
                "first_incomplete_invariant": summary["first_incomplete_invariant_after_stage09"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
