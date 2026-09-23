from __future__ import annotations

import gzip
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator


DATE_ID = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"
STAGE_ID = "stage_05_full_activated_historical_replay"
REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
FULL_REPLAY_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_full_historical_candidate_generation_replay_2026_05_24"
)
MOONSHOT_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"
)

FULL_STAGE04_INDEX = FULL_REPLAY_DIR / "VNEXT_FULL_REPLAY_PATH_OUTCOME_R_LEDGER_2026-05-24.jsonl"
FULL_STAGE04_SUMMARY = FULL_REPLAY_DIR / "VNEXT_FULL_REPLAY_STAGE04_SOURCE_MODE_SUMMARY_2026-05-24.json"
FULL_CANDIDATE_SUMMARY = (
    FULL_REPLAY_DIR / "VNEXT_FULL_REPLAY_CANDIDATE_GENERATION_SUMMARY_2026-05-24.json"
)
MOONSHOT_DYNAMIC_SUMMARY = (
    MOONSHOT_DIR / "VNEXT_MOONSHOT_STAGE04_DYNAMIC_POLICY_REPLAY_SUMMARY_2026-05-26.json"
)
MOONSHOT_DYNAMIC_INDEX = (
    MOONSHOT_DIR / "VNEXT_MOONSHOT_STAGE04_DYNAMIC_POLICY_REPLAY_SHARD_INDEX_2026-05-26.jsonl"
)
MOONSHOT_ROUTER_LEDGER = MOONSHOT_DIR / "VNEXT_MOONSHOT_DEFAULT_OFF_ROUTER_REPLAY_LEDGER_2026-05-26.jsonl"
MOONSHOT_CONDITION_LEDGER = (
    MOONSHOT_DIR / "VNEXT_MOONSHOT_STAGE11_CONDITION_ROUTER_ROW_REPLAY_LEDGER_2026-05-26.jsonl"
)
MOONSHOT_PROP_COMPARISON = (
    MOONSHOT_DIR / "VNEXT_MOONSHOT_STAGE11_PROP_AWARE_ROUTER_COMPARISON_2026-05-26.jsonl"
)
MOONSHOT_CORRECTED_BRANCH_SUMMARY = (
    MOONSHOT_DIR / "VNEXT_MOONSHOT_CORRECTED_BRANCH_SUMMARY_2026-05-26.json"
)

OUTPUT_SHARD_DIR = ROUTE_DIR / "stage05_full_activated_replay_shards"
OUTPUT_SHARD_MANIFEST = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_SHARD_MANIFEST_{DATE_ID}.jsonl"
)
OUTPUT_HASH_MANIFEST = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_HASH_MANIFEST_{DATE_ID}.json"
)
OUTPUT_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_SUMMARY_{DATE_ID}.json"
OUTPUT_REPORT = ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_REPORT_{DATE_ID}.md"
OUTPUT_STATE = ROUTE_DIR / f"VNEXT_REPLACEMENT_SESSION_STATE_{DATE_ID}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE_ID}.json"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONTROL_LEDGER_{DATE_ID}.jsonl"

POLICY_FIELDS = (
    "legacy_fixed_1.5r",
    "ai_target",
    "live_current_j46_j49",
    "partial_be_runner",
    "be_after_trigger",
    "trailing_runner",
    "time_stop_only",
    "early_cut_if_no_progress",
    "path_aware_runner",
)
PRICE_PATH_MODES = (
    "bar_close_m15",
    "m1_path_aware",
    "m5_path_aware",
    "tick_or_sierra_path_aware",
    "ohlc_only_proxy",
)
RUNTIME_MODES = ("current_config_shadow", "hypothetical_activated_vnext")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def iter_gzip_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fnum(value: Any) -> float | None:
    if value is None or value == "" or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def compact_policy_result(result: dict[str, Any] | None) -> dict[str, Any] | None:
    if not result:
        return None
    return {
        "final_r": result.get("final_r"),
        "exit_reason": result.get("exit_reason"),
        "exit_time_utc": result.get("exit_time_utc"),
        "replay_status": result.get("replay_status"),
        "same_bar_ambiguity": result.get("same_bar_ambiguity"),
        "mfe_r": result.get("mfe_r"),
        "mae_r": result.get("mae_r"),
        "partial_realized_r": result.get("partial_realized_r"),
        "remaining_fraction": result.get("remaining_fraction"),
        "stop_r_at_exit": result.get("stop_r_at_exit"),
        "transition_count": len(result.get("transitions") or []),
        "source_gap_reason": result.get("source_gap_reason"),
    }


def compact_path_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "path_row_id": row.get("path_row_id"),
        "replay_mode": row.get("replay_mode"),
        "source_mode": row.get("source_mode"),
        "source_evidence_type": row.get("source_evidence_type"),
        "source_timeframe": row.get("source_timeframe"),
        "path_source_status": row.get("path_source_status"),
        "price_path_truth_status": row.get("price_path_truth_status"),
        "source_window_complete": row.get("source_window_complete"),
        "entry_touched": row.get("entry_touched"),
        "terminal_outcome": row.get("terminal_outcome"),
        "terminal_order_raw": row.get("terminal_order_raw"),
        "pending_lifecycle_state": row.get("pending_lifecycle_state"),
        "simulated_r": row.get("simulated_r"),
        "same_bar_ambiguity": row.get("same_bar_ambiguity"),
        "entry_first_touch_utc": row.get("entry_first_touch_utc"),
        "sl_first_touch_utc": row.get("sl_first_touch_utc"),
        "tp_first_touch_utc": row.get("tp_first_touch_utc"),
        "no_fill_equivalent_r": row.get("no_fill_equivalent_r"),
        "conservative_ambiguous_r": row.get("conservative_ambiguous_r"),
        "optimistic_ambiguous_r": row.get("optimistic_ambiguous_r"),
        "source_path": row.get("source_path"),
        "source_sha256": row.get("source_sha256"),
        "source_gap_class": row.get("source_gap_class"),
        "requested_replay_mode": row.get("requested_replay_mode"),
        "missing_replay_modes": row.get("missing_replay_modes"),
    }


def compact_runtime_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    summary = row.get("runtime_decision_summary") or {}
    return {
        "runtime_trace_mode": row.get("runtime_trace_mode"),
        "route_decision": row.get("route_decision"),
        "pre_ai_action": row.get("pre_ai_action"),
        "pending_would_action": row.get("pending_would_action"),
        "risk_applied": summary.get("risk_applied"),
        "risk_reason": summary.get("risk_reason"),
        "risk_would_multiplier": summary.get("risk_would_multiplier"),
        "route_matched": summary.get("route_matched"),
        "route_reason": summary.get("route_reason"),
        "direct_decision": summary.get("direct_decision"),
        "pending_reason": summary.get("pending_reason"),
        "pre_ai_reason": summary.get("pre_ai_reason"),
    }


def dynamic_exclusion_reason(bar_close: dict[str, Any]) -> str:
    if bar_close.get("path_source_status") != "SIMULATED_FROM_LOCAL_OHLC":
        return "bar_close_path_source_not_simulated_from_local_ohlc"
    if bar_close.get("price_path_truth_status") != "measured":
        return "bar_close_price_path_not_measured"
    if bar_close.get("entry_touched") is not True:
        return "entry_not_touched_within_replay_horizon"
    if bar_close.get("trade_performance_denominator_inclusion") is not True:
        return "not_in_trade_performance_denominator"
    return "dynamic_policy_replay_row_missing_unexpected"


class Metrics:
    def __init__(self) -> None:
        self.output_rows = 0
        self.candidate_rows = 0
        self.dynamic_rows = 0
        self.stage04_should_replay_rows = 0
        self.runtime_effect_rows = 0
        self.source_excluded_rows = 0
        self.secondary_rows = 0
        self.dynamic_exclusion_counts: Counter[str] = Counter()
        self.disposition_counts: Counter[str] = Counter()
        self.framework_counts: Counter[str] = Counter()
        self.symbol_counts: Counter[str] = Counter()
        self.session_counts: Counter[str] = Counter()
        self.year_counts: Counter[str] = Counter()
        self.source_mode_counts: Counter[str] = Counter()
        self.source_window_complete_counts: Counter[str] = Counter()
        self.selected_policy_counts: Counter[str] = Counter()
        self.condition_selected_policy_counts: Counter[str] = Counter()
        self.old_current_total_r = 0.0
        self.legacy_fixed_total_r = 0.0
        self.be_after_trigger_total_r = 0.0
        self.condition_total_r = 0.0
        self.activated_runtime_total_r = 0.0
        self.activated_runtime_performance_rows = 0
        self.policy_total_r: defaultdict[str, float] = defaultdict(float)
        self.policy_counts: Counter[str] = Counter()
        self.policy_wins: Counter[str] = Counter()
        self.policy_gross_win: defaultdict[str, float] = defaultdict(float)
        self.policy_gross_loss: defaultdict[str, float] = defaultdict(float)

    def update_policy(self, policy: str, value: Any) -> None:
        r_value = fnum(value)
        if r_value is None:
            return
        self.policy_counts[policy] += 1
        self.policy_total_r[policy] += r_value
        if r_value > 0:
            self.policy_wins[policy] += 1
            self.policy_gross_win[policy] += r_value
        elif r_value < 0:
            self.policy_gross_loss[policy] += abs(r_value)

    def to_summary(self) -> dict[str, Any]:
        policy_metrics = {}
        for policy in sorted(self.policy_counts):
            count = self.policy_counts[policy]
            gross_loss = self.policy_gross_loss[policy]
            policy_metrics[policy] = {
                "performance_rows": count,
                "total_r": self.policy_total_r[policy],
                "expectancy_r": self.policy_total_r[policy] / count if count else None,
                "wins": self.policy_wins[policy],
                "gross_win_r": self.policy_gross_win[policy],
                "gross_loss_r": gross_loss,
                "win_rate": self.policy_wins[policy] / count if count else None,
                "profit_factor": (
                    self.policy_gross_win[policy] / gross_loss if gross_loss else None
                ),
            }
        return {
            "candidate_rows": self.candidate_rows,
            "output_rows": self.output_rows,
            "dynamic_policy_replay_rows": self.dynamic_rows,
            "stage04_should_replay_rows": self.stage04_should_replay_rows,
            "activated_runtime_effect_rows": self.runtime_effect_rows,
            "activated_runtime_performance_rows": self.activated_runtime_performance_rows,
            "source_excluded_rows": self.source_excluded_rows,
            "secondary_framework_replay_only_rows": self.secondary_rows,
            "dynamic_exclusion_counts": dict(sorted(self.dynamic_exclusion_counts.items())),
            "disposition_counts": dict(sorted(self.disposition_counts.items())),
            "framework_counts": dict(sorted(self.framework_counts.items())),
            "symbol_counts": dict(sorted(self.symbol_counts.items())),
            "session_counts": dict(sorted(self.session_counts.items())),
            "year_counts": dict(sorted(self.year_counts.items())),
            "source_mode_counts": dict(sorted(self.source_mode_counts.items())),
            "source_window_complete_counts": dict(
                sorted(self.source_window_complete_counts.items())
            ),
            "selected_policy_counts": dict(sorted(self.selected_policy_counts.items())),
            "condition_selected_policy_counts": dict(
                sorted(self.condition_selected_policy_counts.items())
            ),
            "policy_metrics": policy_metrics,
            "scenario_total_r": {
                "old_gtos_live_current_j46_j49_all_replayable": self.old_current_total_r,
                "legacy_fixed_1_5r_comparator_all_replayable": self.legacy_fixed_total_r,
                "moonshot_be_after_trigger_all_replayable": self.be_after_trigger_total_r,
                "condition_router_all_replayable": self.condition_total_r,
                "activated_runtime_effect_source_bound_primary_only": self.activated_runtime_total_r,
            },
            "scenario_expectancy_r": {
                "old_gtos_live_current_j46_j49_all_replayable": (
                    self.old_current_total_r / self.dynamic_rows if self.dynamic_rows else None
                ),
                "legacy_fixed_1_5r_comparator_all_replayable": (
                    self.legacy_fixed_total_r / self.dynamic_rows if self.dynamic_rows else None
                ),
                "moonshot_be_after_trigger_all_replayable": (
                    self.be_after_trigger_total_r / self.dynamic_rows if self.dynamic_rows else None
                ),
                "condition_router_all_replayable": (
                    self.condition_total_r / self.dynamic_rows if self.dynamic_rows else None
                ),
                "activated_runtime_effect_source_bound_primary_only": (
                    self.activated_runtime_total_r / self.activated_runtime_performance_rows
                    if self.activated_runtime_performance_rows
                    else None
                ),
            },
        }


def load_router_map() -> dict[str, dict[str, Any]]:
    router_map: dict[str, dict[str, Any]] = {}
    for row in iter_jsonl(MOONSHOT_ROUTER_LEDGER):
        decision = row.get("router_decision") or {}
        router_map[row["candidate_id"]] = {
            "router_replay_row_id": row.get("router_replay_row_id"),
            "selected_policy": decision.get("selected_policy"),
            "selected_policy_final_r": row.get("selected_policy_final_r"),
            "selected_vs_live_delta_r": row.get("selected_vs_live_delta_r"),
            "selected_vs_fixed_delta_r": row.get("selected_vs_fixed_delta_r"),
            "decision_status": decision.get("decision_status"),
            "candidate_action": decision.get("candidate_action"),
            "selected_branch": decision.get("selected_branch"),
            "prop_action": decision.get("prop_action"),
            "ai_role": decision.get("ai_role"),
            "source_quality_action": decision.get("source_quality_action"),
            "exit_management_action": decision.get("exit_management_action"),
            "refusal_reasons": decision.get("refusal_reasons") or [],
            "candidate_use_allowed_now_default_off": decision.get("candidate_use_allowed_now"),
            "runtime_effect_now_default_off": decision.get("runtime_effect_now"),
            "source_path_feature_status": row.get("source_path_feature_status"),
            "source_window_complete": row.get("source_window_complete"),
            "same_bar_ambiguity_observed_in_replay": row.get(
                "same_bar_ambiguity_observed_in_replay"
            ),
            "terminal_classification": row.get("terminal_classification"),
            "liquidity_sweep_proxy_state": row.get("liquidity_sweep_proxy_state"),
            "volatility_state_14_vs_50": row.get("volatility_state_14_vs_50"),
            "trend_state_20": row.get("trend_state_20"),
        }
    return router_map


def load_condition_map() -> dict[str, dict[str, Any]]:
    condition_map: dict[str, dict[str, Any]] = {}
    for row in iter_jsonl(MOONSHOT_CONDITION_LEDGER):
        condition_map[row["candidate_id"]] = {
            "stage11_row_id": row.get("stage11_row_id"),
            "condition_selected_policy": row.get("condition_selected_policy"),
            "condition_selected_policy_final_r": row.get("condition_selected_policy_final_r"),
            "condition_vs_fixed_delta_r": row.get("condition_vs_fixed_delta_r"),
            "condition_vs_global_be_delta_r": row.get("condition_vs_global_be_delta_r"),
            "condition_vs_live_current_delta_r": row.get("condition_vs_live_current_delta_r"),
            "selector_condition_key": row.get("selector_condition_key"),
            "current_bar_displacement_atr14": row.get("current_bar_displacement_atr14"),
            "current_bar_displacement_bucket": row.get("current_bar_displacement_bucket"),
            "selector_uses_only_asof_feature_columns": row.get(
                "selector_uses_only_asof_feature_columns"
            ),
            "selector_excludes_expost_same_bar_outcome": row.get(
                "selector_excludes_expost_same_bar_outcome"
            ),
        }
    return condition_map


def load_prop_projection() -> dict[str, Any]:
    comparison_rows = list(iter_jsonl(MOONSHOT_PROP_COMPARISON))
    by_key = {
        (row.get("branch_id"), row.get("policy_name"), row.get("prop_policy")): row
        for row in comparison_rows
    }
    branch_summary = read_json(MOONSHOT_CORRECTED_BRANCH_SUMMARY)
    best = branch_summary.get("best_overall_reference_fee599_payout8000") or {}
    return {
        "best_overall": best,
        "comparison_rows": len(comparison_rows),
        "best_key": (
            best.get("branch_id"),
            "be_after_trigger_prop_pass_default",
            best.get("prop_policy"),
        ),
        "best_comparison_row": by_key.get(
            (
                best.get("branch_id"),
                "be_after_trigger_prop_pass_default",
                best.get("prop_policy"),
            )
        ),
        "candidate_level_prop_action_available": False,
        "candidate_level_prop_action_status": (
            "branch_aggregate_prop_projection_attached; historical per-trade prop action "
            "sequence is not present in upstream moonshot artifacts"
        ),
    }


def load_dynamic_rows(shard_id: str) -> dict[str, dict[str, Any]]:
    path = MOONSHOT_DIR / "stage04_dynamic_policy_shards" / shard_id / "dynamic_policy_replay.jsonl"
    rows: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return rows
    for row in iter_jsonl(path):
        rows[row["candidate_id"]] = row
    return rows


def stage04_chunks() -> list[dict[str, Any]]:
    return list(iter_jsonl(FULL_STAGE04_INDEX))


def is_stage04_should_replay(row: dict[str, Any]) -> bool:
    return (
        row.get("replay_mode") == "bar_close_m15"
        and row.get("path_source_status") == "SIMULATED_FROM_LOCAL_OHLC"
        and row.get("price_path_truth_status") == "measured"
        and row.get("entry_touched") is True
        and row.get("trade_performance_denominator_inclusion") is True
    )


def activated_overlay_would_apply(router: dict[str, Any] | None) -> bool:
    if not router:
        return False
    return bool(
        router.get("decision_status") == "default_off_candidate_ready"
        and router.get("candidate_action") == "TRADE_DEFAULT_OFF_PRIMARY_CANDIDATE"
        and router.get("prop_action") == "ALLOW_UNLESS_EXTERNAL_PROP_GOVERNOR_BLOCKS"
    )


def row_year(row: dict[str, Any]) -> str:
    text = str(row.get("candle_time_utc") or "")
    return text[:4] if len(text) >= 4 else "unknown"


def build_output_row(
    *,
    bar_close: dict[str, Any],
    path_modes: dict[str, dict[str, Any]],
    runtime_modes: dict[str, dict[str, Any]],
    dynamic_row: dict[str, Any] | None,
    router: dict[str, Any] | None,
    condition: dict[str, Any] | None,
    prop_projection: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    candidate_id = bar_close["candidate_id"]
    compact_policies = {
        policy: compact_policy_result((dynamic_row or {}).get("policy_results", {}).get(policy))
        for policy in POLICY_FIELDS
    }
    selected_policy = (router or {}).get("selected_policy")
    selected_policy_row = compact_policies.get(selected_policy) if selected_policy else None
    default_runtime_effect = activated_overlay_would_apply(router)
    if not dynamic_row:
        disposition = "dynamic_policy_replay_excluded"
    elif default_runtime_effect:
        disposition = "activated_runtime_effect_source_bound_primary_candidate"
    elif router and router.get("candidate_action") == "SECONDARY_BASELINE_REPLACEMENT_REPLAY_ONLY":
        disposition = "secondary_framework_replay_only"
    else:
        disposition = "source_or_scope_excluded_forward_capture_required"

    prop_best = prop_projection.get("best_overall") or {}
    row = {
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "schema_version": "vnext_replacement_full_activated_replay_row_v1",
        "candidate_id": candidate_id,
        "path_row_id": bar_close.get("path_row_id"),
        "symbol": bar_close.get("symbol"),
        "side": bar_close.get("side"),
        "framework": bar_close.get("framework"),
        "candidate_origin_family": f"origin_current_{bar_close.get('framework')}",
        "session_bucket": bar_close.get("session_bucket"),
        "year": row_year(bar_close),
        "candle_time_utc": bar_close.get("candle_time_utc"),
        "entry_reference": bar_close.get("entry_reference"),
        "stop_or_invalidation": bar_close.get("stop_or_invalidation"),
        "target_reference": bar_close.get("target_reference"),
        "rr": bar_close.get("rr"),
        "source_mode": bar_close.get("source_mode"),
        "source_path": bar_close.get("source_path"),
        "source_sha256": bar_close.get("source_sha256"),
        "source_window_complete": (router or {}).get(
            "source_window_complete", bar_close.get("source_window_complete")
        ),
        "bar_close_m15_path": compact_path_row(bar_close),
        "path_modes": {mode: compact_path_row(path_modes.get(mode)) for mode in PRICE_PATH_MODES},
        "runtime_reference": {
            mode: compact_runtime_row(runtime_modes.get(mode)) for mode in RUNTIME_MODES
        },
        "dynamic_policy_replay": {
            "available": dynamic_row is not None,
            "source_replay_mode": (dynamic_row or {}).get("source_replay_mode"),
            "same_bar_policy": (dynamic_row or {}).get("same_bar_policy"),
            "observation_count": (dynamic_row or {}).get("observation_count"),
            "exclusion_reason": None if dynamic_row else dynamic_exclusion_reason(bar_close),
            "policy_results": compact_policies if dynamic_row else {},
        },
        "old_gtos_current_shadow": {
            "policy": "live_current_j46_j49",
            "final_r": (compact_policies.get("live_current_j46_j49") or {}).get("final_r"),
            "exit_reason": (compact_policies.get("live_current_j46_j49") or {}).get(
                "exit_reason"
            ),
            "status": "baseline_comparator_and_rollback_implementation",
        },
        "legacy_fixed_1_5r_comparator": {
            "policy": "legacy_fixed_1.5r",
            "final_r": (compact_policies.get("legacy_fixed_1.5r") or {}).get("final_r"),
            "status": "comparator_only_not_activation_truth",
        },
        "moonshot_be_after_trigger": {
            "policy": "be_after_trigger",
            "final_r": (compact_policies.get("be_after_trigger") or {}).get("final_r"),
            "exit_reason": (compact_policies.get("be_after_trigger") or {}).get("exit_reason"),
        },
        "activated_default_router_projection": {
            "router_available": router is not None,
            "enabled_overlay_assumed": True,
            "apply_to_execution_overlay_assumed": True,
            "selected_policy": selected_policy,
            "selected_policy_final_r": (
                (selected_policy_row or {}).get("final_r")
                if selected_policy_row
                else (router or {}).get("selected_policy_final_r")
            ),
            "selected_vs_live_delta_r": (router or {}).get("selected_vs_live_delta_r"),
            "selected_vs_fixed_delta_r": (router or {}).get("selected_vs_fixed_delta_r"),
            "decision_status": (router or {}).get("decision_status"),
            "candidate_action": (router or {}).get("candidate_action"),
            "selected_branch": (router or {}).get("selected_branch"),
            "prop_action": (router or {}).get("prop_action"),
            "ai_role": (router or {}).get("ai_role"),
            "source_quality_action": (router or {}).get("source_quality_action"),
            "exit_management_action": (router or {}).get("exit_management_action"),
            "refusal_reasons": (router or {}).get("refusal_reasons", []),
            "activated_runtime_effect_would_apply": default_runtime_effect,
        },
        "condition_router_projection": {
            "available": condition is not None,
            "selected_policy": (condition or {}).get("condition_selected_policy"),
            "selected_policy_final_r": (condition or {}).get("condition_selected_policy_final_r"),
            "condition_vs_live_current_delta_r": (condition or {}).get(
                "condition_vs_live_current_delta_r"
            ),
            "condition_vs_global_be_delta_r": (condition or {}).get(
                "condition_vs_global_be_delta_r"
            ),
            "condition_vs_fixed_delta_r": (condition or {}).get("condition_vs_fixed_delta_r"),
            "selector_condition_key": (condition or {}).get("selector_condition_key"),
            "current_bar_displacement_bucket": (condition or {}).get(
                "current_bar_displacement_bucket"
            ),
            "selector_uses_only_asof_feature_columns": (condition or {}).get(
                "selector_uses_only_asof_feature_columns"
            ),
            "selector_excludes_expost_same_bar_outcome": (condition or {}).get(
                "selector_excludes_expost_same_bar_outcome"
            ),
        },
        "ltf_path_effect_projection": {
            "m15_final_r": bar_close.get("simulated_r"),
            "m1_final_r": (path_modes.get("m1_path_aware") or {}).get("simulated_r"),
            "m5_final_r": (path_modes.get("m5_path_aware") or {}).get("simulated_r"),
            "tick_or_sierra_final_r": (path_modes.get("tick_or_sierra_path_aware") or {}).get(
                "simulated_r"
            ),
            "m1_delta_vs_m15_r": delta_r(path_modes.get("m1_path_aware"), bar_close),
            "m5_delta_vs_m15_r": delta_r(path_modes.get("m5_path_aware"), bar_close),
            "tick_or_sierra_delta_vs_m15_r": delta_r(
                path_modes.get("tick_or_sierra_path_aware"), bar_close
            ),
        },
        "prop_governor_projection": {
            "candidate_level_prop_action_available": prop_projection.get(
                "candidate_level_prop_action_available"
            ),
            "candidate_level_prop_action_status": prop_projection.get(
                "candidate_level_prop_action_status"
            ),
            "best_branch_id": prop_best.get("branch_id"),
            "best_policy_name": prop_best.get("policy_name"),
            "best_prop_policy": prop_best.get("prop_policy"),
            "best_allowed_trades": prop_best.get("allowed_trades"),
            "best_pass_probability_proxy": prop_best.get("pass_probability_proxy"),
            "best_total_r": prop_best.get("total_r"),
            "best_expectancy_r": prop_best.get("expectancy_r"),
            "candidate_matches_best_branch": (router or {}).get("selected_branch")
            == prop_best.get("branch_id"),
        },
        "ai_policy_scenario": {
            "paid_ai_or_vendor_call": False,
            "budget_cap_present": False,
            "activation_role": (router or {}).get("ai_role")
            or "mechanical_replay_no_paid_ai_calibration_yet",
        },
        "ml_shadow_scenario": {
            "live_controller": False,
            "role": "monitoring_only_ai_call_reducer_source_confidence_partition_drift",
        },
        "activated_replay_disposition": disposition,
        "no_live_trading_or_broker_mutation": True,
    }
    return row, disposition


def delta_r(path_row: dict[str, Any] | None, bar_close: dict[str, Any]) -> float | None:
    left = fnum((path_row or {}).get("simulated_r"))
    right = fnum(bar_close.get("simulated_r"))
    if left is None or right is None:
        return None
    return left - right


def update_metrics(
    metrics: Metrics,
    row: dict[str, Any],
    bar_close: dict[str, Any],
    dynamic_row: dict[str, Any] | None,
    router: dict[str, Any] | None,
    condition: dict[str, Any] | None,
    disposition: str,
) -> None:
    metrics.output_rows += 1
    metrics.candidate_rows += 1
    metrics.disposition_counts[disposition] += 1
    metrics.framework_counts[str(row.get("framework"))] += 1
    metrics.symbol_counts[str(row.get("symbol"))] += 1
    metrics.session_counts[str(row.get("session_bucket"))] += 1
    metrics.year_counts[str(row.get("year"))] += 1
    metrics.source_mode_counts[str(row.get("source_mode"))] += 1
    metrics.source_window_complete_counts[str(row.get("source_window_complete"))] += 1
    if is_stage04_should_replay(bar_close):
        metrics.stage04_should_replay_rows += 1
    if not dynamic_row:
        metrics.dynamic_exclusion_counts[dynamic_exclusion_reason(bar_close)] += 1
        return
    metrics.dynamic_rows += 1
    if disposition == "activated_runtime_effect_source_bound_primary_candidate":
        metrics.runtime_effect_rows += 1
    if disposition == "source_or_scope_excluded_forward_capture_required":
        metrics.source_excluded_rows += 1
    if disposition == "secondary_framework_replay_only":
        metrics.secondary_rows += 1

    policy_results = dynamic_row.get("policy_results") or {}
    for policy in POLICY_FIELDS:
        compact = policy_results.get(policy) or {}
        metrics.update_policy(policy, compact.get("final_r"))
    metrics.old_current_total_r += fnum((policy_results.get("live_current_j46_j49") or {}).get("final_r")) or 0.0
    metrics.legacy_fixed_total_r += fnum((policy_results.get("legacy_fixed_1.5r") or {}).get("final_r")) or 0.0
    metrics.be_after_trigger_total_r += fnum((policy_results.get("be_after_trigger") or {}).get("final_r")) or 0.0
    if condition:
        metrics.condition_selected_policy_counts[str(condition.get("condition_selected_policy"))] += 1
        metrics.condition_total_r += fnum(condition.get("condition_selected_policy_final_r")) or 0.0
    selected_policy = (router or {}).get("selected_policy")
    if selected_policy:
        metrics.selected_policy_counts[str(selected_policy)] += 1
    if activated_overlay_would_apply(router):
        selected = policy_results.get(selected_policy or "") or {}
        selected_r = fnum(selected.get("final_r"))
        if selected_r is not None:
            metrics.activated_runtime_total_r += selected_r
            metrics.activated_runtime_performance_rows += 1


def process_chunk(
    chunk_row: dict[str, Any],
    router_map: dict[str, dict[str, Any]],
    condition_map: dict[str, dict[str, Any]],
    prop_projection: dict[str, Any],
) -> dict[str, Any]:
    input_path = REPO_ROOT / chunk_row["chunk_path"]
    shard_id = chunk_row["shard_id"]
    output_dir = OUTPUT_SHARD_DIR / shard_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "activated_replay.jsonl.gz"
    dynamic_rows = load_dynamic_rows(shard_id)
    bar_close_rows: list[dict[str, Any]] = []
    path_modes_by_candidate: defaultdict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    runtime_modes_by_candidate: defaultdict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    missing_source_rows_by_candidate: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)

    input_rows = 0
    for source_row in iter_gzip_jsonl(input_path):
        input_rows += 1
        candidate_id = source_row.get("candidate_id")
        mode = source_row.get("replay_mode")
        if not candidate_id:
            continue
        if mode == "bar_close_m15":
            bar_close_rows.append(source_row)
            path_modes_by_candidate[candidate_id][mode] = source_row
        elif mode in PRICE_PATH_MODES:
            path_modes_by_candidate[candidate_id][mode] = source_row
        elif mode in RUNTIME_MODES:
            runtime_modes_by_candidate[candidate_id][mode] = source_row
        elif mode == "missing_source":
            missing_source_rows_by_candidate[candidate_id].append(source_row)

    metrics = Metrics()
    with gzip.open(output_path, "wt", encoding="utf-8", newline="\n") as output_handle:
        for bar_close in bar_close_rows:
            candidate_id = bar_close["candidate_id"]
            path_modes = path_modes_by_candidate.get(candidate_id, {})
            if missing_source_rows_by_candidate.get(candidate_id):
                path_modes["missing_source"] = missing_source_rows_by_candidate[candidate_id][0]
            output_row, disposition = build_output_row(
                bar_close=bar_close,
                path_modes=path_modes,
                runtime_modes=runtime_modes_by_candidate.get(candidate_id, {}),
                dynamic_row=dynamic_rows.get(candidate_id),
                router=router_map.get(candidate_id),
                condition=condition_map.get(candidate_id),
                prop_projection=prop_projection,
            )
            output_handle.write(json.dumps(output_row, sort_keys=True) + "\n")
            update_metrics(
                metrics,
                output_row,
                bar_close,
                dynamic_rows.get(candidate_id),
                router_map.get(candidate_id),
                condition_map.get(candidate_id),
                disposition,
            )

    return {
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "schema_version": "vnext_replacement_full_activated_replay_shard_manifest_v1",
        "shard_id": shard_id,
        "source_index": chunk_row.get("source_index"),
        "source_path": chunk_row.get("source_path"),
        "input_path_outcome_chunk_path": chunk_row.get("chunk_path"),
        "input_path_outcome_rows": input_rows,
        "input_path_outcome_sha256": sha256_file(input_path),
        "input_dynamic_replay_path": rel(
            MOONSHOT_DIR / "stage04_dynamic_policy_shards" / shard_id / "dynamic_policy_replay.jsonl"
        ),
        "input_dynamic_replay_rows": len(dynamic_rows),
        "output_chunk_path": rel(output_path),
        "output_rows": metrics.output_rows,
        "output_bytes": output_path.stat().st_size,
        "output_sha256": sha256_file(output_path),
        "status": "complete",
        "metrics": metrics.to_summary(),
    }


def merge_summaries(manifests: list[dict[str, Any]], prop_projection: dict[str, Any]) -> dict[str, Any]:
    aggregate = Metrics()
    aggregate.candidate_rows = 0
    aggregate.output_rows = 0
    for manifest in manifests:
        shard = manifest["metrics"]
        aggregate.output_rows += shard["output_rows"]
        aggregate.candidate_rows += shard["candidate_rows"]
        aggregate.dynamic_rows += shard["dynamic_policy_replay_rows"]
        aggregate.stage04_should_replay_rows += shard["stage04_should_replay_rows"]
        aggregate.runtime_effect_rows += shard["activated_runtime_effect_rows"]
        aggregate.activated_runtime_performance_rows += shard[
            "activated_runtime_performance_rows"
        ]
        aggregate.source_excluded_rows += shard["source_excluded_rows"]
        aggregate.secondary_rows += shard["secondary_framework_replay_only_rows"]
        aggregate.dynamic_exclusion_counts.update(shard["dynamic_exclusion_counts"])
        aggregate.disposition_counts.update(shard["disposition_counts"])
        aggregate.framework_counts.update(shard["framework_counts"])
        aggregate.symbol_counts.update(shard["symbol_counts"])
        aggregate.session_counts.update(shard["session_counts"])
        aggregate.year_counts.update(shard["year_counts"])
        aggregate.source_mode_counts.update(shard["source_mode_counts"])
        aggregate.source_window_complete_counts.update(shard["source_window_complete_counts"])
        aggregate.selected_policy_counts.update(shard["selected_policy_counts"])
        aggregate.condition_selected_policy_counts.update(shard["condition_selected_policy_counts"])
        totals = shard["scenario_total_r"]
        aggregate.old_current_total_r += totals["old_gtos_live_current_j46_j49_all_replayable"]
        aggregate.legacy_fixed_total_r += totals["legacy_fixed_1_5r_comparator_all_replayable"]
        aggregate.be_after_trigger_total_r += totals["moonshot_be_after_trigger_all_replayable"]
        aggregate.condition_total_r += totals["condition_router_all_replayable"]
        aggregate.activated_runtime_total_r += totals[
            "activated_runtime_effect_source_bound_primary_only"
        ]
        for policy, pm in shard["policy_metrics"].items():
            rows = pm["performance_rows"]
            total_r = pm["total_r"]
            aggregate.policy_counts[policy] += rows
            aggregate.policy_total_r[policy] += total_r
            aggregate.policy_wins[policy] += int(pm.get("wins") or 0)
            aggregate.policy_gross_win[policy] += float(pm.get("gross_win_r") or 0.0)
            aggregate.policy_gross_loss[policy] += float(pm.get("gross_loss_r") or 0.0)

    candidate_summary = read_json(FULL_CANDIDATE_SUMMARY)
    stage04_summary = read_json(FULL_STAGE04_SUMMARY)
    dynamic_summary = read_json(MOONSHOT_DYNAMIC_SUMMARY)
    summary = {
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "schema_version": "vnext_replacement_full_activated_replay_summary_v1",
        "generated_at_utc": utc_now(),
        "input_routes": {
            "full_replay": rel(FULL_REPLAY_DIR),
            "moonshot_dynamic_execution": rel(MOONSHOT_DIR),
        },
        "input_counts": {
            "full_denominator_rows": candidate_summary["counts"]["denominator_rows"],
            "full_candidate_rows": candidate_summary["counts"]["candidate_rows"],
            "full_stage04_path_outcome_rows": stage04_summary["counts"]["path_outcome_r"],
            "moonshot_dynamic_replayable_rows": dynamic_summary["replayable_candidate_rows"],
        },
        "shard_count": len(manifests),
        "output_shard_manifest_path": rel(OUTPUT_SHARD_MANIFEST),
        "output_shard_dir": rel(OUTPUT_SHARD_DIR),
        "hash_manifest_path": rel(OUTPUT_HASH_MANIFEST),
        "report_path": rel(OUTPUT_REPORT),
        "coverage": aggregate.to_summary(),
        "source_mode_boundary": (
            "Every Stage04 bar-close candidate is represented. Dynamic policy performance is "
            "attached only when the upstream ordered-OHLC policy replay row exists; missing "
            "or source-repair rows remain explicit exclusions rather than silent shrinkage."
        ),
        "fixed_1_5r_used_as_activation_truth": False,
        "old_gtos_primary_under_activated_overlay": False,
        "activation_overlay_assumed_for_replay": {
            "gtos_vnext_runtime.enabled": True,
            "gtos_vnext_runtime.apply_to_execution": True,
            "gtos_vnext_runtime.moonshot_dynamic_execution_router_enabled": True,
            "gtos_vnext_runtime.moonshot_dynamic_execution_router_apply_to_execution": True,
            "gtos_vnext_runtime.moonshot_dynamic_execution_router_policy": "be_after_trigger",
            "condition_challenger_compared_but_not_default_activation": True,
            "live_trading_or_broker_mutation": False,
        },
        "prop_governor_projection": prop_projection,
        "first_incomplete_invariant_after_stage05": "stage_06_legacy_vs_vnext_delta_pending",
    }
    return summary


def write_manifest(manifests: list[dict[str, Any]]) -> None:
    tmp = OUTPUT_SHARD_MANIFEST.with_suffix(OUTPUT_SHARD_MANIFEST.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as handle:
        for row in manifests:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    tmp.replace(OUTPUT_SHARD_MANIFEST)


def write_hash_manifest(manifests: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    inputs = [
        FULL_STAGE04_INDEX,
        FULL_STAGE04_SUMMARY,
        FULL_CANDIDATE_SUMMARY,
        MOONSHOT_DYNAMIC_SUMMARY,
        MOONSHOT_DYNAMIC_INDEX,
        MOONSHOT_ROUTER_LEDGER,
        MOONSHOT_CONDITION_LEDGER,
        MOONSHOT_PROP_COMPARISON,
        MOONSHOT_CORRECTED_BRANCH_SUMMARY,
    ]
    hash_manifest = {
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "generated_at_utc": utc_now(),
        "input_hashes": [
            {"path": rel(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
            for path in inputs
        ],
        "output_hashes": [
            {
                "path": row["output_chunk_path"],
                "sha256": row["output_sha256"],
                "bytes": row["output_bytes"],
                "rows": row["output_rows"],
            }
            for row in manifests
        ]
        + [
            {
                "path": rel(OUTPUT_SHARD_MANIFEST),
                "sha256": sha256_file(OUTPUT_SHARD_MANIFEST),
                "bytes": OUTPUT_SHARD_MANIFEST.stat().st_size,
                "rows": len(manifests),
            },
            {
                "path": rel(OUTPUT_SUMMARY),
                "sha256": sha256_file(OUTPUT_SUMMARY),
                "bytes": OUTPUT_SUMMARY.stat().st_size,
                "rows": 1,
            },
        ],
        "summary_counts": summary["coverage"],
    }
    write_json(OUTPUT_HASH_MANIFEST, hash_manifest)


def write_report(summary: dict[str, Any]) -> None:
    cov = summary["coverage"]
    scenario = cov["scenario_expectancy_r"]
    lines = [
        "# vNext Replacement Stage05 Full Activated Historical Replay",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "## Coverage",
        "",
        f"- Full denominator rows: `{summary['input_counts']['full_denominator_rows']}`",
        f"- Full candidate rows represented: `{cov['output_rows']}`",
        f"- Dynamic policy replay rows attached: `{cov['dynamic_policy_replay_rows']}`",
        f"- Activated runtime-effect rows: `{cov['activated_runtime_effect_rows']}`",
        f"- Shards: `{summary['shard_count']}`",
        "",
        "## Scenario Expectancy",
        "",
        f"- Old GTOS live-current J46/J49: `{scenario['old_gtos_live_current_j46_j49_all_replayable']}`",
        f"- Legacy fixed 1.5R comparator: `{scenario['legacy_fixed_1_5r_comparator_all_replayable']}`",
        f"- Moonshot BE-after-trigger: `{scenario['moonshot_be_after_trigger_all_replayable']}`",
        f"- Condition router challenger: `{scenario['condition_router_all_replayable']}`",
        f"- Activated source-bound primary rows: `{scenario['activated_runtime_effect_source_bound_primary_only']}`",
        "",
        "## Boundary",
        "",
        summary["source_mode_boundary"],
        "",
        "Fixed 1.5R remains a comparator only. Old GTOS live-current J46/J49 is the rollback baseline, not the activated target.",
        "",
    ]
    OUTPUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def update_output_manifest(summary: dict[str, Any]) -> None:
    manifest = read_json(OUTPUT_MANIFEST) if OUTPUT_MANIFEST.exists() else {}
    entries = [
        {
            "path": "VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_SUMMARY_2026-05-26.json",
            "stage": "stage_05",
            "status": "created",
            "rows": summary["coverage"]["output_rows"],
        },
        {
            "path": "VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_REPORT_2026-05-26.md",
            "stage": "stage_05",
            "status": "created",
        },
        {
            "path": "VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_SHARD_MANIFEST_2026-05-26.jsonl",
            "stage": "stage_05",
            "status": "created",
            "rows": summary["shard_count"],
        },
        {
            "path": "VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_HASH_MANIFEST_2026-05-26.json",
            "stage": "stage_05",
            "status": "created",
        },
        {
            "path": "stage05_full_activated_replay_shards/",
            "stage": "stage_05",
            "status": "created",
            "rows": summary["coverage"]["output_rows"],
        },
    ]
    outputs = manifest.setdefault("outputs", [])
    if isinstance(outputs, list):
        existing = {
            item.get("path") or item.get("path_glob"): index
            for index, item in enumerate(outputs)
            if isinstance(item, dict)
        }
        for entry in entries:
            old_pending_index = existing.get("VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_*")
            if old_pending_index is not None:
                outputs.pop(old_pending_index)
                existing = {
                    item.get("path") or item.get("path_glob"): index
                    for index, item in enumerate(outputs)
                    if isinstance(item, dict)
                }
            key = entry["path"]
            if key in existing:
                outputs[existing[key]] = entry
            else:
                outputs.append(entry)
    elif isinstance(outputs, dict):
        outputs["stage05_full_activated_replay_summary"] = rel(OUTPUT_SUMMARY)
        outputs["stage05_full_activated_replay_report"] = rel(OUTPUT_REPORT)
        outputs["stage05_full_activated_replay_shard_manifest"] = rel(OUTPUT_SHARD_MANIFEST)
        outputs["stage05_full_activated_replay_hash_manifest"] = rel(OUTPUT_HASH_MANIFEST)
        outputs["stage05_full_activated_replay_shard_dir"] = rel(OUTPUT_SHARD_DIR)
    else:
        manifest["outputs"] = entries
    manifest["last_updated_utc"] = utc_now()
    manifest["stage05_status"] = "completed_full_candidate_coverage_replay_written"
    manifest["stage05_counts"] = summary["coverage"]
    write_json(OUTPUT_MANIFEST, manifest)


def update_state(summary: dict[str, Any]) -> None:
    state = read_json(OUTPUT_STATE)
    state["last_updated_utc"] = utc_now()
    state["current_stage"] = "stage_06_legacy_vs_vnext_delta"
    state["first_incomplete_invariant"] = "stage_06_legacy_vs_vnext_delta_pending"
    state["exact_next_action"] = (
        "Build candidate-level and branch-level legacy-vs-vNext delta ledgers from "
        "the Stage05 full activated replay shards, including missed winners, avoided "
        "losers, source partitions, branch metrics, and prop opportunity cost."
    )
    state.setdefault("stage_status", {})[
        "stage_05_full_activated_historical_replay"
    ] = "completed_full_candidate_coverage_replay_written"
    state.setdefault("stage_status", {})["stage_06_legacy_vs_vnext_delta"] = "pending"
    rows = state.setdefault("evidence_rows_scanned", {})
    rows["stage05_full_candidate_rows_represented"] = summary["coverage"]["output_rows"]
    rows["stage05_dynamic_policy_rows_attached"] = summary["coverage"][
        "dynamic_policy_replay_rows"
    ]
    rows["stage05_activated_runtime_effect_rows"] = summary["coverage"][
        "activated_runtime_effect_rows"
    ]
    rows["stage05_shards_written"] = summary["shard_count"]
    state.setdefault("tests_verifiers_run", []).append(
        {
            "command": rel(Path(__file__)),
            "result": (
                "passed; wrote Stage05 full activated replay shards "
                f"rows={summary['coverage']['output_rows']}"
            ),
            "timestamp_utc": utc_now(),
        }
    )
    write_json(OUTPUT_STATE, state)


def main() -> None:
    OUTPUT_SHARD_DIR.mkdir(parents=True, exist_ok=True)
    router_map = load_router_map()
    condition_map = load_condition_map()
    prop_projection = load_prop_projection()
    manifests = []
    for chunk_row in stage04_chunks():
        manifests.append(process_chunk(chunk_row, router_map, condition_map, prop_projection))
        write_manifest(manifests)
    summary = merge_summaries(manifests, prop_projection)
    write_json(OUTPUT_SUMMARY, summary)
    write_report(summary)
    write_manifest(manifests)
    write_hash_manifest(manifests, summary)
    update_output_manifest(summary)
    update_state(summary)
    append_jsonl(
        CONTROL_LEDGER,
        {
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "timestamp_utc": utc_now(),
            "status": "completed_full_candidate_coverage_replay_written",
            "candidate_rows": summary["coverage"]["output_rows"],
            "dynamic_rows": summary["coverage"]["dynamic_policy_replay_rows"],
            "activated_runtime_effect_rows": summary["coverage"][
                "activated_runtime_effect_rows"
            ],
            "first_incomplete_invariant_after_stage": summary[
                "first_incomplete_invariant_after_stage05"
            ],
        },
    )
    print(
        json.dumps(
            {
                "stage": STAGE_ID,
                "candidate_rows": summary["coverage"]["output_rows"],
                "dynamic_rows": summary["coverage"]["dynamic_policy_replay_rows"],
                "activated_runtime_effect_rows": summary["coverage"][
                    "activated_runtime_effect_rows"
                ],
                "next": summary["first_incomplete_invariant_after_stage05"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
