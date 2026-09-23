from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


DATE = "2026-05-27"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
sys.path.insert(0, str(REPO_ROOT))

from src.research.moonshot_default_off_policy_router import (  # noqa: E402
    EVIDENCE_BACKED_PARTIAL_BE_EXCEPTION_ORIGIN_FAMILIES,
    EXECUTION_POLICY_IDS,
)


OUT_DIR = ROUTE_DIR / "ei15r"
FINAL_DYNAMIC_MANIFEST = OUT_DIR / "final_dynamic_router_replay.manifest.jsonl"
DYNAMIC_COUNTERFACTUAL_MANIFEST = OUT_DIR / "dynamic_exit_counterfactual.manifest.jsonl"
PROMOTION_LEDGER_STEM = OUT_DIR / "momentum_policy_promotion"
PROMOTION_MANIFEST = OUT_DIR / "momentum_policy_promotion.manifest.jsonl"
PROMOTION_SUMMARY = OUT_DIR / "momentum_policy_promotion_summary.json"
EXCEPTION_LEDGER = OUT_DIR / "momentum_exception_decision_ledger.jsonl"
RISK_PROOF = OUT_DIR / "selected_policy_risk_proof_summary.json"
LIFECYCLE_PROOF = OUT_DIR / "momentum_policy_lifecycle_propagation_proof.json"
COMPLETION_EVIDENCE = (
    ROUTE_DIR
    / f"MOMENTUM_POLICY_PROMOTION_COMPLETION_EVIDENCE_{DATE}.json"
)

SHARD_ROWS = 100_000
PROMOTED_PRIMARY_POLICY = "momentum_exhaustion"
PROMOTED_EXCEPTION_POLICY = "partial_be_runner"
BASELINE_POLICY = "fixed_1_5r"
COMPARISON_FIELDS = {
    "fixed_1_5r": "comparison_fixed_1_5r_r",
    "be_after_trigger": "comparison_be_after_trigger_r",
    "partial_be_runner": "comparison_partial_be_runner_r",
    "trailing_runner": "comparison_trailing_runner_r",
    "momentum_exhaustion": "comparison_momentum_exhaustion_r",
    "time_stop": "comparison_time_stop_r",
}
SEGMENT_DIMENSIONS = (
    "symbol",
    "framework",
    "session_bucket",
    "origin_family",
    "year",
    "month",
    "source_mode",
    "m1_availability_status",
    "tick_availability_status",
    "same_bar_ambiguity",
    "replay_source_class",
    "non_replayable_path_status",
    "drawdown_path_status",
    "loss_streak_status",
    "prop_attempt_survival_class",
    "selected_cell_risk_cell_id",
    "broker_geometry_class",
    "policy_parameter_signature",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT.resolve())).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        for line_no, line in enumerate(handle, 1):
            if line.strip():
                yield line_no, json.loads(line)


def write_jsonl_line(handle, payload: dict[str, Any]) -> None:
    handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def norm(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def float_or_none(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def round_metric(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 6)


def manifest_entries(path: Path) -> list[dict[str, Any]]:
    return [row for _, row in read_jsonl(path)]


def shard_paths(manifest: Path) -> list[Path]:
    paths: list[Path] = []
    for row in manifest_entries(manifest):
        rel_path = row.get("path")
        if rel_path:
            paths.append(REPO_ROOT / rel_path)
    return paths


def metric_bucket() -> dict[str, Any]:
    return {
        "rows": 0,
        "total_r": 0.0,
        "wins": 0,
        "losses": 0,
        "breakevens": 0,
        "gross_profit_r": 0.0,
        "gross_loss_r": 0.0,
    }


def add_metric(bucket: dict[str, Any], value: float | None) -> None:
    if value is None:
        return
    bucket["rows"] += 1
    bucket["total_r"] += float(value)
    if value > 0:
        bucket["wins"] += 1
        bucket["gross_profit_r"] += float(value)
    elif value < 0:
        bucket["losses"] += 1
        bucket["gross_loss_r"] += float(value)
    else:
        bucket["breakevens"] += 1


def close_metric(bucket: dict[str, Any]) -> dict[str, Any]:
    rows = int(bucket["rows"])
    wins = int(bucket["wins"])
    losses = int(bucket["losses"])
    breakevens = int(bucket["breakevens"])
    gross_loss = float(bucket["gross_loss_r"])
    gross_profit = float(bucket["gross_profit_r"])
    return {
        "rows": rows,
        "total_r": round(float(bucket["total_r"]), 6),
        "expectancy_r": round(float(bucket["total_r"]) / rows, 9) if rows else None,
        "wins": wins,
        "losses": losses,
        "breakevens": breakevens,
        "win_rate": round(wins / rows, 9) if rows else None,
        "win_rate_excluding_be": (
            round(wins / (wins + losses), 9) if wins + losses else None
        ),
        "gross_profit_r": round(gross_profit, 6),
        "gross_loss_r": round(gross_loss, 6),
        "profit_factor": round(gross_profit / abs(gross_loss), 9) if gross_loss else None,
    }


def policy_r(row: dict[str, Any], policy: str) -> float | None:
    return float_or_none(row.get(COMPARISON_FIELDS[policy]))


def origin_family(row: dict[str, Any]) -> str:
    value = norm(row.get("origin_family") or row.get("candidate_origin_family"))
    return value.removeprefix("origin_")


def selected_exception_policy_for_row(row: dict[str, Any]) -> tuple[str | None, str]:
    if row.get("non_replayable_reason"):
        return None, "non_replayable_row_not_routed_for_launch_metrics"
    family = origin_family(row)
    if family in EVIDENCE_BACKED_PARTIAL_BE_EXCEPTION_ORIGIN_FAMILIES:
        return PROMOTED_EXCEPTION_POLICY, f"evidence_backed_origin_family_exception:{family}"
    return PROMOTED_PRIMARY_POLICY, "momentum_primary_no_exception"


def source_year(row: dict[str, Any]) -> str:
    text = str(row.get("source_time_utc") or row.get("entry_touch_time_utc") or "")
    return text[:4] if len(text) >= 4 else "unknown_year"


def source_month(row: dict[str, Any]) -> str:
    text = str(row.get("source_time_utc") or row.get("entry_touch_time_utc") or "")
    return text[:7] if len(text) >= 7 else "unknown_month"


def broker_geometry_class(row: dict[str, Any]) -> str:
    dims = row.get("router_dimensions") if isinstance(row.get("router_dimensions"), dict) else {}
    eligible = dims.get("broker_native_eligible")
    if eligible is True:
        return "broker_native_geometry_bound"
    if eligible is False:
        return "broker_native_geometry_not_eligible"
    return "broker_geometry_status_not_materialized_in_final_router_row"


def prop_survival_class(row: dict[str, Any]) -> str:
    value = float_or_none(row.get("prop_account_delta_pct_gross"))
    if value is None:
        return "prop_path_survival_field_absent_gross_delta_absent"
    if value > 0:
        return "gross_prop_delta_positive_path_survival_not_scored"
    if value < 0:
        return "gross_prop_delta_negative_path_survival_not_scored"
    return "gross_prop_delta_flat_path_survival_not_scored"


def policy_params_from_config(config: dict[str, Any], policy: str) -> dict[str, Any]:
    cfg = (config.get("gtos_vnext_runtime") or {}) if isinstance(config, dict) else {}
    if policy == PROMOTED_PRIMARY_POLICY:
        return {
            "trigger_r": cfg.get("moonshot_dynamic_execution_router_momentum_trigger_r"),
            "pullback_r": cfg.get("moonshot_dynamic_execution_router_momentum_pullback_r"),
            "final_target_r": cfg.get("moonshot_dynamic_execution_router_momentum_final_target_r"),
            "time_stop_bars": cfg.get("moonshot_dynamic_execution_router_momentum_time_stop_bars"),
        }
    if policy == PROMOTED_EXCEPTION_POLICY:
        return {
            "trigger_r": cfg.get("moonshot_dynamic_execution_router_partial_trigger_r"),
            "partial_close_ratio": cfg.get("moonshot_dynamic_execution_router_partial_close_ratio"),
            "final_target_r": cfg.get("moonshot_dynamic_execution_router_partial_final_target_r"),
            "time_stop_bars": cfg.get("moonshot_dynamic_execution_router_partial_time_stop_bars"),
        }
    return {}


def policy_param_signature(config: dict[str, Any], policy: str | None) -> str:
    if not policy:
        return "non_replayable_no_policy"
    params = policy_params_from_config(config, policy)
    payload = ",".join(f"{key}={params.get(key)}" for key in sorted(params))
    return f"{policy}:{payload}"


def load_policy_exit_map() -> dict[tuple[str, str], dict[str, Any]]:
    wanted = {PROMOTED_PRIMARY_POLICY, PROMOTED_EXCEPTION_POLICY}
    exits: dict[tuple[str, str], dict[str, Any]] = {}
    if not DYNAMIC_COUNTERFACTUAL_MANIFEST.exists():
        return exits
    for shard in shard_paths(DYNAMIC_COUNTERFACTUAL_MANIFEST):
        for _, row in read_jsonl(shard):
            policy = norm(row.get("policy_name"))
            if policy not in wanted:
                continue
            rid = str(row.get("selected_row_id") or "")
            if not rid:
                continue
            exits[(rid, policy)] = {
                "exit_reason": row.get("exit_reason"),
                "exit_time_utc": row.get("exit_time_utc"),
                "transition_trace": row.get("transition_trace"),
                "policy_params": row.get("policy_params"),
                "order_modify_lifecycle_status": row.get("order_modify_lifecycle_status"),
                "close_order_lifecycle_status": row.get("close_order_lifecycle_status"),
                "fill_lifecycle_status": row.get("fill_lifecycle_status"),
                "runtime_supported_now": row.get("runtime_supported_now"),
            }
    return exits


def segment_key(row: dict[str, Any], config: dict[str, Any], policy: str | None) -> dict[str, str]:
    dims = row.get("router_dimensions") if isinstance(row.get("router_dimensions"), dict) else {}
    selected_cell = (
        dims.get("selected_cell_risk_cell_id")
        or row.get("selected_cell_risk_cell_id")
        or "missing_selected_cell_risk_cell_id"
    )
    return {
        "symbol": str(row.get("symbol") or "unknown_symbol"),
        "framework": str(row.get("framework") or "unknown_framework"),
        "session_bucket": str(row.get("session_bucket") or row.get("session") or "unknown_session"),
        "origin_family": origin_family(row) or "unknown_origin_family",
        "year": source_year(row),
        "month": source_month(row),
        "source_mode": str((row.get("router_inputs") or {}).get("source_mode") or "unknown_source_mode"),
        "m1_availability_status": str(row.get("m1_availability_status") or "missing_m1_status"),
        "tick_availability_status": str(row.get("tick_availability_status") or "missing_tick_status"),
        "same_bar_ambiguity": str(bool(row.get("same_bar_ambiguity"))).lower(),
        "replay_source_class": str(row.get("replay_source_class") or "missing_replay_source_class"),
        "non_replayable_path_status": (
            "non_replayable:" + str(row.get("non_replayable_reason"))
            if row.get("non_replayable_reason")
            else "replayable"
        ),
        "drawdown_path_status": str(row.get("drawdown_path_status") or "source_field_absent_in_final_dynamic_router_replay"),
        "loss_streak_status": str(row.get("loss_streak_status") or "source_field_absent_in_final_dynamic_router_replay"),
        "prop_attempt_survival_class": prop_survival_class(row),
        "selected_cell_risk_cell_id": str(selected_cell),
        "broker_geometry_class": broker_geometry_class(row),
        "policy_parameter_signature": policy_param_signature(config, policy),
    }


def add_segment(
    bucket: dict[str, Any],
    *,
    momentum_r: float | None,
    old_router_r: float | None,
    comparator_values: dict[str, float | None],
) -> None:
    bucket["rows"] += 1
    if momentum_r is not None:
        bucket["momentum_total_r"] += momentum_r
    if old_router_r is not None:
        bucket["old_router_total_r"] += old_router_r
    for policy, value in comparator_values.items():
        if value is not None:
            bucket[f"{policy}_total_r"] += value


def new_segment_bucket() -> dict[str, Any]:
    payload = {"rows": 0, "momentum_total_r": 0.0, "old_router_total_r": 0.0}
    for policy in COMPARISON_FIELDS:
        payload[f"{policy}_total_r"] = 0.0
    return payload


def clean_old_outputs() -> None:
    for path in OUT_DIR.glob("momentum_policy_promotion.part-*.jsonl"):
        path.unlink()
    for path in (
        PROMOTION_MANIFEST,
        PROMOTION_SUMMARY,
        EXCEPTION_LEDGER,
        RISK_PROOF,
        LIFECYCLE_PROOF,
        COMPLETION_EVIDENCE,
    ):
        if path.exists():
            path.unlink()


def main() -> int:
    started_at = utc_now()
    clean_old_outputs()
    config = yaml.safe_load((REPO_ROOT / "config" / "agent_config.yaml").read_text(encoding="utf-8")) or {}
    gtos_cfg = config.get("gtos_vnext_runtime") or {}
    exception_families = tuple(EVIDENCE_BACKED_PARTIAL_BE_EXCEPTION_ORIGIN_FAMILIES)
    policy_exit_map = load_policy_exit_map()

    total_rows = 0
    replayable_rows = 0
    non_replayable_rows = 0
    duplicate_ids: list[str] = []
    seen_ids: set[str] = set()
    policy_counts: Counter[str] = Counter()
    old_policy_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    cost_status_counts: Counter[str] = Counter()
    missing_field_counts: Counter[str] = Counter()
    m1_counts: Counter[str] = Counter()
    tick_counts: Counter[str] = Counter()
    risk_match_counts: Counter[str] = Counter()
    broker_geometry_counts: Counter[str] = Counter()
    lifecycle_counts: Counter[str] = Counter()
    metrics = {
        "promoted_dynamic_router": metric_bucket(),
        "old_condition_router": metric_bucket(),
        "global_fixed_1_5r": metric_bucket(),
        "global_be_after_trigger": metric_bucket(),
        "global_partial_be_runner": metric_bucket(),
        "global_trailing_runner": metric_bucket(),
        "global_momentum_exhaustion": metric_bucket(),
        "global_time_stop": metric_bucket(),
        "hindsight_best": metric_bucket(),
    }
    segment_buckets: dict[str, dict[str, dict[str, Any]]] = {
        dim: defaultdict(new_segment_bucket) for dim in SEGMENT_DIMENSIONS
    }
    origin_year_partial_delta: dict[str, Counter[str]] = defaultdict(Counter)
    origin_session_partial_delta: dict[str, Counter[str]] = defaultdict(Counter)

    shard_index = 0
    shard_row_count = 0
    shard_path = PROMOTION_LEDGER_STEM.with_name(
        f"{PROMOTION_LEDGER_STEM.name}.part-{shard_index:06d}.jsonl"
    )
    shard_handle = shard_path.open("w", encoding="utf-8", newline="\n")
    shard_infos: list[dict[str, Any]] = []

    def close_shard() -> None:
        nonlocal shard_handle, shard_path, shard_row_count
        shard_handle.close()
        shard_infos.append(
            {
                "ledger_name": "momentum_policy_promotion_ledger",
                "format": "plain_jsonl",
                "compressed": False,
                "shard_index": len(shard_infos),
                "path": rel(shard_path),
                "row_count": shard_row_count,
                "size_bytes": shard_path.stat().st_size,
                "sha256": sha256_file(shard_path),
            }
        )

    for source_shard in shard_paths(FINAL_DYNAMIC_MANIFEST):
        for _, row in read_jsonl(source_shard):
            total_rows += 1
            if shard_row_count >= SHARD_ROWS:
                close_shard()
                shard_index += 1
                shard_row_count = 0
                shard_path = PROMOTION_LEDGER_STEM.with_name(
                    f"{PROMOTION_LEDGER_STEM.name}.part-{shard_index:06d}.jsonl"
                )
                shard_handle = shard_path.open("w", encoding="utf-8", newline="\n")

            rid = str(row.get("selected_row_id") or "")
            if rid in seen_ids:
                duplicate_ids.append(rid)
            if rid:
                seen_ids.add(rid)

            promoted_policy, exception_reason = selected_exception_policy_for_row(row)
            replayable = promoted_policy is not None
            if replayable:
                replayable_rows += 1
            else:
                non_replayable_rows += 1
            policy_counts[promoted_policy or "non_replayable_no_policy"] += 1
            old_policy_counts[str(row.get("chosen_policy") or "missing_old_policy")] += 1
            reason_counts[exception_reason] += 1
            cost_status_counts[str(row.get("cost_status") or "missing_cost_status")] += 1
            for note in row.get("missing_field_notes") or []:
                missing_field_counts[str(note)] += 1
            m1_counts[str(row.get("m1_availability_status") or "missing_m1_status")] += 1
            tick_counts[str(row.get("tick_availability_status") or "missing_tick_status")] += 1

            dims = row.get("router_dimensions") if isinstance(row.get("router_dimensions"), dict) else {}
            risk_match_counts[str(dims.get("selected_cell_risk_match_reason") or "missing_selected_cell_risk_match_reason")] += 1
            broker_geometry_counts[broker_geometry_class(row)] += 1

            comparison_values = {policy: policy_r(row, policy) for policy in COMPARISON_FIELDS}
            momentum_r = comparison_values[PROMOTED_PRIMARY_POLICY]
            partial_r = comparison_values[PROMOTED_EXCEPTION_POLICY]
            old_router_r = float_or_none(row.get("final_r"))
            promoted_r = comparison_values.get(promoted_policy) if promoted_policy else None
            hindsight_r = float_or_none(row.get("hindsight_best_r"))
            selected_exit = policy_exit_map.get((rid, promoted_policy or ""))
            if selected_exit:
                lifecycle_counts[str(selected_exit.get("fill_lifecycle_status") or "missing_fill_lifecycle_status")] += 1
                lifecycle_counts[str(selected_exit.get("order_modify_lifecycle_status") or "missing_order_modify_lifecycle_status")] += 1
                lifecycle_counts[str(selected_exit.get("close_order_lifecycle_status") or "missing_close_order_lifecycle_status")] += 1

            if replayable:
                add_metric(metrics["promoted_dynamic_router"], promoted_r)
                add_metric(metrics["old_condition_router"], old_router_r)
                add_metric(metrics["global_fixed_1_5r"], comparison_values["fixed_1_5r"])
                add_metric(metrics["global_be_after_trigger"], comparison_values["be_after_trigger"])
                add_metric(metrics["global_partial_be_runner"], partial_r)
                add_metric(metrics["global_trailing_runner"], comparison_values["trailing_runner"])
                add_metric(metrics["global_momentum_exhaustion"], momentum_r)
                add_metric(metrics["global_time_stop"], comparison_values["time_stop"])
                add_metric(metrics["hindsight_best"], hindsight_r)

            segment_values = segment_key(row, config, promoted_policy)
            for dim, value in segment_values.items():
                add_segment(
                    segment_buckets[dim][value],
                    momentum_r=momentum_r,
                    old_router_r=old_router_r,
                    comparator_values=comparison_values,
                )
            family = segment_values["origin_family"]
            year = segment_values["year"]
            session = segment_values["session_bucket"]
            if momentum_r is not None and partial_r is not None:
                origin_year_partial_delta[family][year] += partial_r - momentum_r
                origin_session_partial_delta[family][session] += partial_r - momentum_r

            promotion_row = {
                "schema_version": "vnext_execution_policy_momentum_promotion_row_v1",
                "selected_row_id": rid,
                "candidate_id": row.get("candidate_id"),
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "framework": row.get("framework"),
                "session_bucket": row.get("session_bucket") or row.get("session"),
                "origin_family": family,
                "candidate_origin_family": row.get("candidate_origin_family"),
                "year": year,
                "month": segment_values["month"],
                "source_path": row.get("source_path"),
                "source_sha256": row.get("source_sha256"),
                "source_row_index": row.get("source_row_index"),
                "source_time_utc": row.get("source_time_utc"),
                "replay_source_class": row.get("replay_source_class"),
                "non_replayable_reason": row.get("non_replayable_reason"),
                "old_router_policy": row.get("chosen_policy"),
                "old_router_execution_policy_id": row.get("execution_policy_id"),
                "old_router_final_r": round_metric(old_router_r),
                "promoted_policy": promoted_policy,
                "execution_policy_id": EXECUTION_POLICY_IDS.get(promoted_policy or ""),
                "promotion_reason": exception_reason,
                "promoted_final_r": round_metric(promoted_r),
                "promoted_exit_reason": (
                    selected_exit.get("exit_reason") if selected_exit else None
                ),
                "promoted_exit_time_utc": (
                    selected_exit.get("exit_time_utc") if selected_exit else None
                ),
                "promoted_policy_params": (
                    selected_exit.get("policy_params")
                    if selected_exit
                    else policy_params_from_config(config, promoted_policy or "")
                ),
                "policy_parameter_signature": segment_values["policy_parameter_signature"],
                "dynamic_policy_transition_trace": (
                    selected_exit.get("transition_trace") if selected_exit else None
                ),
                "momentum_final_r": round_metric(momentum_r),
                "trailing_final_r": round_metric(comparison_values["trailing_runner"]),
                "partial_final_r": round_metric(partial_r),
                "be_after_trigger_final_r": round_metric(comparison_values["be_after_trigger"]),
                "fixed_1_5r_final_r": round_metric(comparison_values["fixed_1_5r"]),
                "time_stop_final_r": round_metric(comparison_values["time_stop"]),
                "hindsight_best_policy": row.get("hindsight_best_policy"),
                "hindsight_best_r": round_metric(hindsight_r),
                "delta_momentum_vs_old_router_r": round_metric(
                    (momentum_r - old_router_r) if momentum_r is not None and old_router_r is not None else None
                ),
                "delta_momentum_vs_trailing_r": round_metric(
                    (momentum_r - comparison_values["trailing_runner"])
                    if momentum_r is not None and comparison_values["trailing_runner"] is not None
                    else None
                ),
                "delta_momentum_vs_partial_r": round_metric(
                    (momentum_r - partial_r) if momentum_r is not None and partial_r is not None else None
                ),
                "delta_momentum_vs_be_after_trigger_r": round_metric(
                    (momentum_r - comparison_values["be_after_trigger"])
                    if momentum_r is not None and comparison_values["be_after_trigger"] is not None
                    else None
                ),
                "delta_momentum_vs_fixed_1_5r_r": round_metric(
                    (momentum_r - comparison_values["fixed_1_5r"])
                    if momentum_r is not None and comparison_values["fixed_1_5r"] is not None
                    else None
                ),
                "delta_promoted_vs_old_router_r": round_metric(
                    (promoted_r - old_router_r) if promoted_r is not None and old_router_r is not None else None
                ),
                "delta_promoted_vs_momentum_r": round_metric(
                    (promoted_r - momentum_r) if promoted_r is not None and momentum_r is not None else None
                ),
                "mfe_r": row.get("mfe_r"),
                "mae_r": row.get("mae_r"),
                "m1_availability_status": row.get("m1_availability_status"),
                "tick_availability_status": row.get("tick_availability_status"),
                "same_bar_ambiguity": row.get("same_bar_ambiguity"),
                "selected_policy_ordered_path_status": row.get(
                    "selected_policy_ordered_path_status_after_replay"
                ),
                "cost_status": row.get("cost_status"),
                "cost_notes": row.get("cost_notes"),
                "missing_field_notes": row.get("missing_field_notes"),
                "net_r": row.get("net_r"),
                "router_inputs": {
                    "candidate_origin_family": (row.get("router_inputs") or {}).get("candidate_origin_family"),
                    "current_bar_displacement_atr14": (row.get("router_inputs") or {}).get("current_bar_displacement_atr14"),
                    "liquidity_sweep_proxy_state": (row.get("router_inputs") or {}).get("liquidity_sweep_proxy_state"),
                    "volatility_state_14_vs_50": (row.get("router_inputs") or {}).get("volatility_state_14_vs_50"),
                    "trend_state_20": (row.get("router_inputs") or {}).get("trend_state_20"),
                    "source_mode": (row.get("router_inputs") or {}).get("source_mode"),
                },
                "risk_cell": {
                    "selected_cell_risk_cell_id": segment_values["selected_cell_risk_cell_id"],
                    "selected_cell_risk_match_reason": dims.get("selected_cell_risk_match_reason"),
                    "selected_cell_risk_pct": dims.get("selected_cell_risk_pct"),
                    "broker_geometry_class": segment_values["broker_geometry_class"],
                },
                "drawdown_path_status": segment_values["drawdown_path_status"],
                "loss_streak_status": segment_values["loss_streak_status"],
                "prop_attempt_survival_class": segment_values["prop_attempt_survival_class"],
            }
            write_jsonl_line(shard_handle, promotion_row)
            shard_row_count += 1

    close_shard()
    with PROMOTION_MANIFEST.open("w", encoding="utf-8", newline="\n") as handle:
        for info in shard_infos:
            write_jsonl_line(handle, info)

    closed_metrics = {name: close_metric(bucket) for name, bucket in metrics.items()}
    promoted = closed_metrics["promoted_dynamic_router"]
    old = closed_metrics["old_condition_router"]
    global_momentum = closed_metrics["global_momentum_exhaustion"]
    source_router_state = (
        "post_promotion_router_already_current"
        if set(old_policy_counts) <= {PROMOTED_PRIMARY_POLICY, PROMOTED_EXCEPTION_POLICY}
        and abs(float(promoted["total_r"]) - float(old["total_r"])) <= 0.000001
        else "pre_promotion_mixed_condition_router_source"
    )

    losing_segment_rows: list[dict[str, Any]] = []
    for dim, values in segment_buckets.items():
        for value, bucket in values.items():
            momentum_total = bucket["momentum_total_r"]
            for comparator in (
                "old_router",
                "fixed_1_5r",
                "be_after_trigger",
                "partial_be_runner",
                "trailing_runner",
                "time_stop",
            ):
                comp_key = (
                    "old_router_total_r"
                    if comparator == "old_router"
                    else f"{comparator}_total_r"
                )
                comparator_total = float(bucket.get(comp_key, 0.0))
                if comparator_total <= momentum_total + 0.000001:
                    continue
                family = str(value) if dim == "origin_family" else ""
                accepted = (
                    dim == "origin_family"
                    and comparator == PROMOTED_EXCEPTION_POLICY
                    and family in exception_families
                )
                decision = (
                    "promote_partial_be_runner_exception"
                    if accepted
                    else "reject_exception_keep_momentum_primary"
                )
                reason = "not_origin_family_partial_exception_or_not_stable_enough"
                stability = {}
                if dim == "origin_family":
                    years = dict(origin_year_partial_delta.get(str(value), {}))
                    sessions = dict(origin_session_partial_delta.get(str(value), {}))
                    year_positive = all(delta > 0 for delta in years.values()) if years else False
                    session_positive = all(delta > 0 for delta in sessions.values()) if sessions else False
                    stability = {
                        "partial_minus_momentum_by_year": {
                            key: round(delta, 6) for key, delta in sorted(years.items())
                        },
                        "partial_minus_momentum_by_session_bucket": {
                            key: round(delta, 6) for key, delta in sorted(sessions.items())
                        },
                        "stable_positive_all_years": year_positive,
                        "stable_positive_all_sessions": session_positive,
                    }
                    if accepted:
                        reason = (
                            "origin_family_partial_be_runner_beats_momentum_with_positive_year_and_session_stability"
                            if year_positive and session_positive
                            else "configured_exception_requires_reverification_stability_false"
                        )
                        if not (year_positive and session_positive):
                            decision = "reject_exception_keep_momentum_primary"
                losing_segment_rows.append(
                    {
                        "schema_version": "vnext_execution_policy_exception_decision_segment_v1",
                        "dimension": dim,
                        "segment_value": value,
                        "rows": int(bucket["rows"]),
                        "momentum_total_r": round(momentum_total, 6),
                        "comparator_policy": comparator,
                        "comparator_total_r": round(comparator_total, 6),
                        "delta_comparator_minus_momentum_r": round(comparator_total - momentum_total, 6),
                        "decision": decision,
                        "decision_reason": reason,
                        "runtime_config_required": (
                            {
                                "moonshot_dynamic_execution_router_policy": PROMOTED_PRIMARY_POLICY,
                                "moonshot_dynamic_execution_router_momentum_exception_policy": PROMOTED_EXCEPTION_POLICY,
                                "origin_family": value,
                            }
                            if decision == "promote_partial_be_runner_exception"
                            else None
                        ),
                        "stability": stability,
                    }
                )

    with EXCEPTION_LEDGER.open("w", encoding="utf-8", newline="\n") as handle:
        for row in sorted(
            losing_segment_rows,
            key=lambda item: (
                item["dimension"],
                str(item["segment_value"]),
                item["comparator_policy"],
            ),
        ):
            write_jsonl_line(handle, row)

    risk_proof = {
        "schema_version": "vnext_selected_policy_risk_proof_summary_v1",
        "generated_at_utc": utc_now(),
        "selected_policy_risk_identity_model": (
            "exact_selected_policy_match_or_policy_invariant_broker_geometry_only"
        ),
        "production_selected_policies": [PROMOTED_PRIMARY_POLICY, PROMOTED_EXCEPTION_POLICY],
        "forbidden_policy_identity_fallbacks": [
            "missing_policy_risk_identity",
            "mismatched_selected_policy_without_policy_invariant_geometry",
            "zero_risk",
            "unresolved_broker_geometry",
            "invalid_volume_step",
            "invalid_filling_mode",
            "invalid_deviation_geometry",
        ],
        "runtime_enforcement_paths": [
            "src/components/gtos_vnext_runtime.py::_moonshot_selected_cell_risk_match",
            "src/components/execution.py::_resolve_vnext_production_risk_pct",
            "src/components/execution.py::set_limit_intent",
            "src/components/execution.py::check_limit_fill",
            "src/components/execution.py::open_trade",
        ],
        "test_evidence": [
            "tests/test_gtos_vnext_runtime.py::test_moonshot_dynamic_execution_requires_positive_selected_cell_risk_when_configured",
            "tests/test_limit_order_flow.py::test_vnext_production_selected_cell_refuses_missing_policy_risk_identity",
            "tests/test_limit_order_flow.py::test_vnext_production_selected_cell_refuses_mismatched_policy_risk_identity",
        ],
        "final_replay_selected_cell_risk_match_reason_counts": dict(risk_match_counts),
        "broker_geometry_class_counts": dict(broker_geometry_counts),
        "policy_identity_status_required_in_live_runtime": True,
        "be_keyed_risk_rows_allowed_only_with_policy_invariant_broker_geometry": True,
        "config_policy_invariant_geometry_flag": bool(
            gtos_cfg.get(
                "moonshot_dynamic_execution_router_allow_policy_invariant_selected_cell_risk_geometry"
            )
        ),
    }
    write_json(RISK_PROOF, risk_proof)

    lifecycle_proof = {
        "schema_version": "vnext_momentum_policy_lifecycle_propagation_proof_v1",
        "generated_at_utc": utc_now(),
        "production_policy": PROMOTED_PRIMARY_POLICY,
        "exception_policy": PROMOTED_EXCEPTION_POLICY,
        "policy_id_map": {
            policy: EXECUTION_POLICY_IDS.get(policy)
            for policy in (PROMOTED_PRIMARY_POLICY, PROMOTED_EXCEPTION_POLICY)
        },
        "lifecycle_chain": [
            "selected_row",
            "router_decision",
            "set_limit_intent",
            "pending_fill",
            "open_trade",
            "active_trade_management",
            "order_modify",
            "close_order",
            "trade_record",
        ],
        "required_runtime_fields": [
            "gtos_vnext_dynamic_policy_selected",
            "gtos_vnext_execution_policy_id",
            "gtos_vnext_dynamic_be_trigger_r",
            "gtos_vnext_dynamic_final_target_r",
            "gtos_vnext_dynamic_momentum_pullback_r",
            "gtos_vnext_selected_cell_risk_selected_policy",
            "gtos_vnext_selected_cell_risk_source_policy",
            "gtos_vnext_selected_cell_risk_policy_identity_status",
        ],
        "causal_management_inputs": [
            "entry_price",
            "stop_loss",
            "direction",
            "current_mt5_tick_bid_ask",
            "mfe_r",
            "trigger_r",
            "pullback_r",
            "final_target_r",
            "broker_order_modify_close_results",
        ],
        "forbidden_live_selection_inputs": [
            "final_r",
            "hindsight_best_policy",
            "comparison_momentum_exhaustion_r",
            "comparison_partial_be_runner_r",
            "comparison_trailing_runner_r",
            "post_trade_scoring_fields",
        ],
        "runtime_lifecycle_status_counts_from_counterfactual_ledger": dict(lifecycle_counts),
        "test_evidence": [
            "tests/test_moonshot_default_off_policy_router.py::test_condition_router_ignores_future_outcome_labels_when_selecting_live_policy",
            "tests/test_limit_order_flow.py::test_vnext_momentum_exhaustion_pending_fill_closes_on_pullback_from_router",
            "tests/test_limit_order_flow.py::test_vnext_partial_be_runner_pending_fill_uses_router_decision_and_lifecycle",
            "tests/test_limit_order_flow.py::test_vnext_trailing_runner_pending_fill_trails_and_final_closes_from_router",
        ],
        "fixed_1_5r_role": "comparator_and_fail_closed_refusal_only_not_default",
        "j46_j49_role": "rejected_live_current_policy_replaced_when_dynamic_vnext_applies",
    }
    write_json(LIFECYCLE_PROOF, lifecycle_proof)

    summary = {
        "schema_version": "vnext_execution_policy_momentum_promotion_summary_v1",
        "generated_at_utc": utc_now(),
        "started_at_utc": started_at,
        "source_manifest": rel(FINAL_DYNAMIC_MANIFEST),
        "source_dynamic_counterfactual_manifest": rel(DYNAMIC_COUNTERFACTUAL_MANIFEST),
        "full_denominator_rows": total_rows,
        "selected_rows_processed": total_rows,
        "replayable_rows": replayable_rows,
        "non_replayable_rows": non_replayable_rows,
        "duplicate_selected_row_ids": duplicate_ids[:20],
        "duplicate_selected_row_id_count": len(duplicate_ids),
        "promotion_decision": {
            "primary_policy": PROMOTED_PRIMARY_POLICY,
            "primary_execution_policy_id": EXECUTION_POLICY_IDS[PROMOTED_PRIMARY_POLICY],
            "exception_policy": PROMOTED_EXCEPTION_POLICY,
            "exception_execution_policy_id": EXECUTION_POLICY_IDS[PROMOTED_EXCEPTION_POLICY],
            "exception_origin_families": list(exception_families),
            "fixed_1_5r_role": "comparator_and_fail_closed_refusal_only_not_default",
            "be_after_trigger_role": "supported_legacy_policy_not_primary_not_exception",
            "trailing_runner_role": "supported_runtime_diagnostic_not_selected_without_future_exception_proof",
            "old_condition_router_role": "superseded_pre_promotion_mixed_router",
        },
        "source_dynamic_router_state": source_router_state,
        "source_dynamic_router_role": (
            "current final_dynamic_router_replay is already regenerated through the promoted live router"
            if source_router_state == "post_promotion_router_already_current"
            else "source final_dynamic_router_replay is the pre-promotion mixed condition router"
        ),
        "metrics": closed_metrics,
        "deltas": {
            "promoted_minus_old_condition_router_r": round(
                promoted["total_r"] - old["total_r"], 6
            ),
            "promoted_minus_global_momentum_r": round(
                promoted["total_r"] - global_momentum["total_r"], 6
            ),
            "global_momentum_minus_old_condition_router_r": round(
                global_momentum["total_r"] - old["total_r"], 6
            ),
        },
        "policy_distribution": dict(policy_counts),
        "old_router_policy_distribution": dict(old_policy_counts),
        "promotion_reason_distribution": dict(reason_counts),
        "cost_status_counts": dict(cost_status_counts),
        "missing_field_counts": dict(missing_field_counts),
        "m1_availability_counts": dict(m1_counts),
        "tick_availability_counts": dict(tick_counts),
        "ledger_output_format": "uncompressed_plain_jsonl_shards_with_manifest",
        "outputs": {
            "promotion_ledger": {
                "manifest_path": rel(PROMOTION_MANIFEST),
                "plain_jsonl_shards": True,
                "compressed": False,
                "row_count": total_rows,
                "shards": len(shard_infos),
            },
            "exception_decision_ledger": {
                "path": rel(EXCEPTION_LEDGER),
                "plain_jsonl": True,
                "compressed": False,
                "row_count": len(losing_segment_rows),
            },
            "selected_policy_risk_proof_summary": rel(RISK_PROOF),
            "lifecycle_propagation_proof": rel(LIFECYCLE_PROOF),
        },
        "runtime_config_expected": {
            "moonshot_dynamic_execution_router_policy": PROMOTED_PRIMARY_POLICY,
            "moonshot_dynamic_execution_router_momentum_exception_policy": PROMOTED_EXCEPTION_POLICY,
            "moonshot_dynamic_execution_router_momentum_exception_origin_families_to_partial_be_runner": list(exception_families),
            "moonshot_dynamic_execution_router_apply_to_execution": True,
            "moonshot_dynamic_execution_router_enabled": True,
        },
        "rollback_proof": {
            "rollback_flags": [
                "gtos_vnext_runtime.moonshot_dynamic_execution_router_enabled=false",
                "gtos_vnext_runtime.moonshot_dynamic_execution_router_apply_to_execution=false",
            ],
            "rollback_result": "router_returns_no_live_effect_vnext_disabled_or_no_apply_without_reactivating_fixed_1_5r_or_j46_j49_for_vnext_rows",
            "stage05_rollback_proof_path": rel(
                ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE05_ROLLBACK_PROOF_{DATE}.json"
            ),
        },
    }
    write_json(PROMOTION_SUMMARY, summary)
    print(
        json.dumps(
            {
                "completion_evidence_owner": rel(
                    ROUTE_DIR / "verify_execution_policy_momentum_promotion.py"
                ),
                "status": "built",
                "summary": rel(PROMOTION_SUMMARY),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
