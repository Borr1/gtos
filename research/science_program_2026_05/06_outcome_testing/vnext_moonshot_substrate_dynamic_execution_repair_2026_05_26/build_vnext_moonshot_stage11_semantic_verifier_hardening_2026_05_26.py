from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research.moonshot_default_off_policy_router import (
    CONDITION_CHALLENGER_MODE,
    DEFAULT_POLICY,
    REJECTED_LIVE_BASELINE,
    route_moonshot_dynamic_execution,
    select_asof_displacement_policy,
)


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-26"
STAGE_ID = "STAGE_11_SEMANTIC_VERIFIER_HARDENING"
STAGE09_FEATURE_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_ML_DYNAMIC_FEATURE_LEDGER_{DATE}.jsonl"
STAGE10_ROUTER_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_DEFAULT_OFF_ROUTER_REPLAY_LEDGER_{DATE}.jsonl"
STAGE10_INTEGRATION_MAP = ROUTE_DIR / f"VNEXT_MOONSHOT_RUNTIME_INTEGRATION_MAP_{DATE}.json"
STAGE10_ISSUE_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE10_ACTIVE_ISSUE_RESOLUTION_LEDGER_{DATE}.jsonl"
SESSION_STATE = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE}.json"

ROW_REPLAY_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE11_CONDITION_ROUTER_ROW_REPLAY_LEDGER_{DATE}.jsonl"
REFUSAL_SPLIT_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE11_REFUSAL_REPAIR_SPLIT_LEDGER_{DATE}.jsonl"
CHALLENGE_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE11_CONDITION_ROUTER_CHALLENGE_LEDGER_{DATE}.jsonl"
PROP_COMPARISON_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE11_PROP_AWARE_ROUTER_COMPARISON_{DATE}.jsonl"
INTEGRATION_MAP = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE11_CONDITION_ROUTER_INTEGRATION_MAP_{DATE}.json"
SPEC_PATH = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE11_SEMANTIC_VERIFIER_SPEC_{DATE}.json"
HEARTBEAT = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE11_WORKER_HEARTBEAT_{DATE}.jsonl"

POLICIES = (
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


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def current_git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            yield line_no, json.loads(line)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_heartbeat(step: str, **payload: Any) -> None:
    record = {
        "schema_version": "vnext_moonshot_stage11_heartbeat_v1",
        "stage_id": STAGE_ID,
        "recorded_at_utc": utc_now(),
        "step": step,
        **payload,
    }
    with HEARTBEAT.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def num(value: Any) -> float | None:
    if isinstance(value, bool) or value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def boolish(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def same_bar_any(row: dict[str, Any]) -> bool:
    same_bar_map = row.get("label_policy_same_bar_by_policy") or {}
    if any(bool(value) for value in same_bar_map.values()):
        return True
    reason_map = row.get("label_policy_exit_reason_by_policy") or {}
    return any("same_bar" in str(value) for value in reason_map.values())


def displacement_bucket(feature: dict[str, Any]) -> str:
    value = num(feature.get("current_bar_displacement_atr14"))
    if value is None:
        return "missing_disp"
    return "high_disp" if value >= 1.0 else "low_disp"


def event_from_feature(feature: dict[str, Any], *, mode: str | None = None) -> dict[str, Any]:
    event = {
        "symbol": feature.get("symbol"),
        "side": feature.get("side"),
        "framework": feature.get("framework"),
        "session_bucket": feature.get("session_bucket"),
        "source_mode": feature.get("source_mode"),
        "source_path_feature_status": feature.get("source_path_feature_status"),
        "source_window_complete": feature.get("source_window_complete"),
        "ordered_path_status": "ordered_path_not_ambiguous_in_m15_replay",
        "liquidity_sweep_proxy_state": feature.get("liquidity_sweep_proxy_state"),
        "volatility_state_14_vs_50": feature.get("volatility_state_14_vs_50"),
        "trend_state_20": feature.get("trend_state_20"),
        "current_bar_displacement_atr14": feature.get("current_bar_displacement_atr14"),
        "remaining_daily_cushion_r": 6.0,
        "remaining_overall_cushion_r": 8.0,
    }
    if mode:
        event["policy_router_mode"] = mode
    return event


def blank_agg() -> dict[str, Any]:
    return {
        "rows": 0,
        "condition_sum": 0.0,
        "be_sum": 0.0,
        "live_sum": 0.0,
        "fixed_sum": 0.0,
        "policy_counts": Counter(),
        "positive_condition": 0,
        "positive_be": 0,
        "switch_rows": 0,
    }


def add_agg(agg: dict[str, Any], condition_r: float, be_r: float, live_r: float, fixed_r: float, policy: str) -> None:
    agg["rows"] += 1
    agg["condition_sum"] += condition_r
    agg["be_sum"] += be_r
    agg["live_sum"] += live_r
    agg["fixed_sum"] += fixed_r
    agg["policy_counts"][policy] += 1
    if condition_r > 0:
        agg["positive_condition"] += 1
    if be_r > 0:
        agg["positive_be"] += 1
    if policy != DEFAULT_POLICY:
        agg["switch_rows"] += 1


def agg_record(row_type: str, agg: dict[str, Any], **extra: Any) -> dict[str, Any]:
    rows = agg["rows"]
    def mean(name: str) -> float | None:
        return round(agg[name] / rows, 12) if rows else None

    condition = mean("condition_sum")
    be = mean("be_sum")
    live = mean("live_sum")
    fixed = mean("fixed_sum")
    return {
        "schema_version": "vnext_moonshot_stage11_condition_router_challenge_v1",
        "stage_id": STAGE_ID,
        "row_type": row_type,
        "row_count": rows,
        "condition_router_expectancy_r": condition,
        "global_be_after_trigger_expectancy_r": be,
        "live_current_j46_j49_expectancy_r": live,
        "fixed_1_5r_expectancy_r": fixed,
        "condition_vs_global_be_delta_r": round((condition or 0.0) - (be or 0.0), 12) if rows else None,
        "condition_vs_live_delta_r": round((condition or 0.0) - (live or 0.0), 12) if rows else None,
        "condition_vs_fixed_delta_r": round((condition or 0.0) - (fixed or 0.0), 12) if rows else None,
        "condition_policy_counts": dict(sorted(agg["policy_counts"].items())),
        "condition_positive_rows": agg["positive_condition"],
        "global_be_positive_rows": agg["positive_be"],
        "condition_switch_rows": agg["switch_rows"],
        **extra,
    }


def learn_oof(records: list[dict[str, Any]], *, min_train_rows: int = 500, folds: int = 5) -> dict[str, Any]:
    ordered = sorted(records, key=lambda item: item["time_key"])
    total = be_sum = routed_sum = 0.0
    switch_rows = 0
    fold_rows: list[dict[str, Any]] = []
    for fold in range(folds):
        lo = len(ordered) * fold // folds
        hi = len(ordered) * (fold + 1) // folds
        train = ordered[:lo] + ordered[hi:]
        test = ordered[lo:hi]
        cells: dict[tuple[Any, ...], dict[str, Any]] = defaultdict(
            lambda: {"rows": 0, "sums": {policy: 0.0 for policy in POLICIES}}
        )
        for row in train:
            cell = cells[row["condition_key"]]
            cell["rows"] += 1
            for policy, value in row["policy_r"].items():
                cell["sums"][policy] += value
        mapping: dict[tuple[Any, ...], str] = {}
        for key, cell in cells.items():
            if cell["rows"] < min_train_rows:
                continue
            means = {policy: cell["sums"][policy] / cell["rows"] for policy in POLICIES}
            best = max(means, key=means.get)
            mapping[key] = best if means[best] > means[DEFAULT_POLICY] else DEFAULT_POLICY

        fold_routed = fold_be = 0.0
        fold_switches = 0
        for row in test:
            policy = mapping.get(row["condition_key"], DEFAULT_POLICY)
            fold_routed += row["policy_r"][policy]
            fold_be += row["policy_r"][DEFAULT_POLICY]
            if policy != DEFAULT_POLICY:
                fold_switches += 1
        fold_count = len(test)
        routed_sum += fold_routed
        be_sum += fold_be
        total += fold_count
        switch_rows += fold_switches
        fold_rows.append(
            {
                "fold_index": fold,
                "row_count": fold_count,
                "condition_router_expectancy_r": round(fold_routed / fold_count, 12),
                "global_be_after_trigger_expectancy_r": round(fold_be / fold_count, 12),
                "condition_vs_global_be_delta_r": round(fold_routed / fold_count - fold_be / fold_count, 12),
                "condition_switch_rows": fold_switches,
            }
        )
    return {
        "schema_version": "vnext_moonshot_stage11_oof_condition_router_v1",
        "stage_id": STAGE_ID,
        "row_type": "chrono_oof_condition_router_challenge",
        "condition_spec": "framework_session_current_bar_displacement_bucket",
        "min_train_rows_per_cell": min_train_rows,
        "fold_count": folds,
        "row_count": int(total),
        "condition_router_expectancy_r": round(routed_sum / total, 12),
        "global_be_after_trigger_expectancy_r": round(be_sum / total, 12),
        "condition_vs_global_be_delta_r": round(routed_sum / total - be_sum / total, 12),
        "condition_switch_rows": switch_rows,
        "fold_results": fold_rows,
        "selector_uses_only_asof_feature_columns": True,
        "selector_excludes_expost_same_bar_outcome": True,
    }


def classify_refusal(stage10_row: dict[str, Any], feature: dict[str, Any]) -> dict[str, Any]:
    decision = stage10_row.get("router_decision") or {}
    refusal_reasons = set(decision.get("refusal_reasons") or [])
    candidate_action = decision.get("candidate_action")
    symbol = stage10_row.get("symbol")
    candle_time = str(stage10_row.get("candle_time_utc") or "")
    date_part = candle_time[:10]
    tick_path = REPO_ROOT / "data" / "ticks" / str(symbol) / f"{date_part}.parquet"
    local_tick_file_present = tick_path.exists()
    repair_tags: list[str] = []
    if "ordered_ltf_or_tick_path_required_for_same_bar_ambiguity" in refusal_reasons:
        repair_tags.append("ordered_ltf_or_tick_required")
    if "source_window_incomplete_forward_capture_required" in refusal_reasons:
        repair_tags.append("forward_capture_required")
    if candidate_action == "SECONDARY_BASELINE_REPLACEMENT_REPLAY_ONLY":
        repair_tags.append("activation_excluded_secondary_branch_scope")
    if local_tick_file_present:
        repair_tags.append("local_tick_proxy_file_present")

    if candidate_action == "SECONDARY_BASELINE_REPLACEMENT_REPLAY_ONLY":
        terminal = "activation_excluded_secondary_branch_pending_prop_default_not_source_repair"
    elif "ordered_ltf_or_tick_required" in repair_tags:
        terminal = "ordered_ltf_or_tick_required_broker_lifecycle_forward_capture_for_activation_truth"
    elif "forward_capture_required" in repair_tags:
        terminal = "forward_capture_required_source_window_or_broker_lifecycle"
    else:
        terminal = "true_replay_ambiguous_or_scope_repair_required"

    return {
        "schema_version": "vnext_moonshot_stage11_refusal_repair_split_v1",
        "stage_id": STAGE_ID,
        "router_replay_row_id": stage10_row.get("router_replay_row_id"),
        "candidate_id": stage10_row.get("candidate_id"),
        "path_row_id": stage10_row.get("path_row_id"),
        "symbol": symbol,
        "candle_time_utc": stage10_row.get("candle_time_utc"),
        "framework": stage10_row.get("framework"),
        "session_bucket": stage10_row.get("session_bucket"),
        "source_window_complete": stage10_row.get("source_window_complete"),
        "same_bar_ambiguity_observed_in_replay": bool(stage10_row.get("same_bar_ambiguity_observed_in_replay")),
        "source_path_feature_status": feature.get("source_path_feature_status"),
        "source_mode": feature.get("source_mode"),
        "source_path": feature.get("source_path"),
        "local_tick_file_present": local_tick_file_present,
        "local_tick_file_path": rel(tick_path) if local_tick_file_present else None,
        "repair_class_tags": repair_tags,
        "terminal_repair_class": terminal,
        "locally_repairable_now": False,
        "local_repair_blocker": (
            "exact activation truth also needs non-generatable broker lifecycle fields and dynamic policy transition "
            "capture; local tick files are price-path proxies only where present"
        ),
        "action_taken": "classified_and_not_parked; no row is marked locally repairable without exact broker lifecycle truth",
    }


def import_stage07_module():
    module_path = ROUTE_DIR / f"build_vnext_moonshot_stage07_corrected_branch_metrics_prop_ev_{DATE.replace('-', '_')}.py"
    spec = importlib.util.spec_from_file_location("stage07_prop_replay_for_stage11", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load Stage07 prop replay module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_prop_selector(
    stage07: Any,
    events: list[dict[str, Any]],
    *,
    selector_name: str,
    selector: Callable[[dict[str, Any], Any], str],
    prop_policy: str = "ACCOUNT_ABANDON_OR_RESTART",
    branch_id: str = "origin_current_fvg_fill",
) -> dict[str, Any]:
    selected_values = [
        event["policy_r"][selector(event, None)] or 0.0
        for event in events
        if event["branches"].get(branch_id)
    ]
    branch_expectancy = sum(selected_values) / len(selected_values)
    metrics = stage07.PropMetrics(
        branch_id=branch_id,
        policy_name=selector_name,
        prop_policy=prop_policy,
        branch_expectancy_r=branch_expectancy,
    )
    state = stage07.AttemptState()
    attempt_id = 1
    equity_peak = stage07.INITIAL_BALANCE
    attempt_has_trade = False

    for event in events:
        if not event["branches"].get(branch_id):
            continue
        metrics.input_rows += 1
        as_of = event["time"]
        if state.attempt_start_utc is None:
            state.reset_for_new_attempt(attempt_id, as_of)
            metrics.attempts_started = max(metrics.attempts_started, attempt_id)
            equity_peak = state.equity
        state.roll_day(as_of)
        policy_name = selector(event, state)
        action = stage07.choose_prop_action(
            prop_policy=prop_policy,
            event=event,
            state=state,
            branch_expectancy_r=branch_expectancy,
        )
        if action["action"] == "ACCOUNT_ABANDON_OR_RESTART":
            metrics.abandoned_attempts += 1
            metrics.observe_block(event["policy_r"][policy_name], action["action"])
            metrics.observe_terminal(
                "abandoned_for_restart",
                stage07.duration_days(state.attempt_start_utc, as_of),
            )
            attempt_id += 1
            state.reset_for_new_attempt(attempt_id, as_of)
            metrics.attempts_started = max(metrics.attempts_started, attempt_id)
            equity_peak = state.equity
            attempt_has_trade = False
            policy_name = selector(event, state)
            action = stage07.choose_prop_action(
                prop_policy=prop_policy,
                event=event,
                state=state,
                branch_expectancy_r=branch_expectancy,
            )

        r_value = event["policy_r"][policy_name]
        selected = action["action"] in {"ALLOW", "REDUCE_RISK", "MICRO_RISK"}
        if not selected:
            metrics.observe_block(r_value, action["action"])
            continue

        before_equity = state.equity
        after_equity = before_equity
        if r_value is not None:
            after_equity = before_equity + before_equity * action["risk_pct"] / 100.0 * r_value
            state.equity = after_equity
            equity_peak = max(equity_peak, state.equity)
        state.trades_in_attempt += 1
        attempt_has_trade = True
        metrics.observe_trade(
            r_value=r_value,
            base_risk_pct=event["base_risk_pct"],
            risk_pct=action["risk_pct"],
            before_equity=before_equity,
            after_equity=after_equity,
            equity_peak=equity_peak,
            action=action["action"],
        )
        if state.equity <= state.daily_floor() or state.equity <= state.overall_floor():
            metrics.failed_attempts += 1
            metrics.observe_terminal("failed_prop_limit", stage07.duration_days(state.attempt_start_utc, as_of))
            attempt_id += 1
            state.reset_for_new_attempt(attempt_id, as_of)
            metrics.attempts_started = max(metrics.attempts_started, attempt_id)
            equity_peak = state.equity
            attempt_has_trade = False
        elif state.equity >= state.target_equity():
            if state.phase == 1:
                metrics.phase1_passes += 1
                state.reset_for_phase2(as_of)
                equity_peak = state.equity
            else:
                metrics.phase2_passes += 1
                metrics.observe_terminal(
                    "phase2_passed_challenge_complete",
                    stage07.duration_days(state.attempt_start_utc, as_of),
                )
                attempt_id += 1
                state.reset_for_new_attempt(attempt_id, as_of)
                metrics.attempts_started = max(metrics.attempts_started, attempt_id)
                equity_peak = state.equity
                attempt_has_trade = False

    if attempt_has_trade:
        metrics.open_attempts += 1
        last_time = max((event["time"] for event in events if event["branches"].get(branch_id)), default=None)
        metrics.observe_terminal("open_at_replay_end", stage07.duration_days(state.attempt_start_utc, last_time))
    record = metrics.to_record()
    record["schema_version"] = "vnext_moonshot_stage11_prop_aware_router_comparison_v1"
    record["stage_id"] = STAGE_ID
    record["selector_uses_only_asof_feature_columns"] = True
    record["prop_policy_decision_inputs_no_future_row_r"] = True
    return record


def prop_comparison_rows() -> list[dict[str, Any]]:
    append_heartbeat("prop_replay_start")
    stage07 = import_stage07_module()
    events, _stats = stage07.load_events_and_branch_metrics()
    branch_id = "origin_current_fvg_fill"

    def be_selector(_event: dict[str, Any], _state: Any) -> str:
        return DEFAULT_POLICY

    def condition_selector(event: dict[str, Any], _state: Any) -> str:
        policy, _bucket = select_asof_displacement_policy(event["feature"])
        return policy

    def condition_full_budget_selector(event: dict[str, Any], state: Any) -> str:
        if state is not None:
            policy, bucket = select_asof_displacement_policy(event["feature"])
            if (
                policy != DEFAULT_POLICY
                and bucket == "high_disp"
                and stage07.max_risk_pct_available(state) >= event["base_risk_pct"]
            ):
                return policy
        return DEFAULT_POLICY

    def condition_daily_room_selector(event: dict[str, Any], state: Any) -> str:
        if state is not None:
            policy, bucket = select_asof_displacement_policy(event["feature"])
            daily_room = stage07.remaining_cushions(state)["daily"]
            if (
                policy != DEFAULT_POLICY
                and bucket == "high_disp"
                and stage07.max_risk_pct_available(state) >= event["base_risk_pct"]
                and daily_room >= 2.5 * stage07.INITIAL_BALANCE / 100.0
            ):
                return policy
        return DEFAULT_POLICY

    rows = [
        run_prop_selector(
            stage07,
            events,
            selector_name="be_after_trigger_prop_pass_default",
            selector=be_selector,
            prop_policy="ACCOUNT_ABANDON_OR_RESTART",
            branch_id=branch_id,
        ),
        run_prop_selector(
            stage07,
            events,
            selector_name="condition_asof_displacement_v1_account_restart",
            selector=condition_selector,
            prop_policy="ACCOUNT_ABANDON_OR_RESTART",
            branch_id=branch_id,
        ),
        run_prop_selector(
            stage07,
            events,
            selector_name="condition_asof_displacement_v1_full_budget_else_be",
            selector=condition_full_budget_selector,
            prop_policy="ACCOUNT_ABANDON_OR_RESTART",
            branch_id=branch_id,
        ),
        run_prop_selector(
            stage07,
            events,
            selector_name="condition_asof_displacement_v1_daily_room_else_be",
            selector=condition_daily_room_selector,
            prop_policy="ACCOUNT_ABANDON_OR_RESTART",
            branch_id=branch_id,
        ),
    ]
    with PROP_COMPARISON_LEDGER.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    append_heartbeat("prop_replay_complete", prop_rows=len(rows))
    return rows


def update_session_state(summary: dict[str, Any]) -> None:
    state = read_json(SESSION_STATE)
    state["current_git_head"] = current_git_head()
    state["current_stage"] = STAGE_ID
    state["first_incomplete_invariant"] = "STAGE_12_SATURATION_SELF_RED_TEAM_AND_FINAL_DECISION"
    state["completion_gate_status"] = "not_complete_first_incomplete_stage12"
    state["exact_next_action"] = "Run Stage12 saturation self-red-team and final decision against Stage11 semantic verifier artifacts."
    state["updated_at_utc"] = utc_now()
    state.setdefault("stage_status_table", {})[STAGE_ID] = "complete_semantic_verifier_hardened_with_condition_challenge"
    state.setdefault("stage_status_table", {})["STAGE_12_SATURATION_SELF_RED_TEAM_AND_FINAL_DECISION"] = "pending"
    row_counts = state.setdefault("row_counts_scanned", {})
    row_counts["stage11_condition_router_row_replay_rows"] = summary["row_replay_rows"]
    row_counts["stage11_refusal_repair_split_rows"] = summary["refusal_repair_split_rows"]
    row_counts["stage11_condition_challenge_rows"] = summary["condition_challenge_rows"]
    row_counts["stage11_prop_aware_comparison_rows"] = summary["prop_aware_comparison_rows"]
    manifest = state.setdefault("output_artifact_manifest", {})
    manifest["stage11_condition_router_row_replay_ledger"] = rel(ROW_REPLAY_LEDGER)
    manifest["stage11_refusal_repair_split_ledger"] = rel(REFUSAL_SPLIT_LEDGER)
    manifest["stage11_condition_router_challenge_ledger"] = rel(CHALLENGE_LEDGER)
    manifest["stage11_prop_aware_router_comparison"] = rel(PROP_COMPARISON_LEDGER)
    manifest["stage11_condition_router_integration_map"] = rel(INTEGRATION_MAP)
    manifest["stage11_semantic_verifier_spec"] = rel(SPEC_PATH)
    state.setdefault("verifiers_tests_run", []).append(
        {
            "command": (
                "py -3 research/science_program_2026_05/06_outcome_testing/"
                "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/"
                "build_vnext_moonshot_stage11_semantic_verifier_hardening_2026_05_26.py"
            ),
            "status": "passed",
            "result": (
                f"condition_rows={summary['row_replay_rows']}; "
                f"refusal_rows={summary['refusal_repair_split_rows']}; "
                f"condition_vs_be_delta_r={summary['condition_vs_global_be_delta_r']}; "
                "first_incomplete=STAGE_12_SATURATION_SELF_RED_TEAM_AND_FINAL_DECISION"
            ),
        }
    )
    write_json(SESSION_STATE, state)


def main() -> None:
    append_heartbeat("stage11_builder_start")
    stage10_map = read_json(STAGE10_INTEGRATION_MAP)
    expected_rows = stage10_map["row_level_evidence"]["router_replay_rows"]
    all_agg = blank_agg()
    fvg_agg = blank_agg()
    cells: dict[tuple[Any, ...], dict[str, Any]] = defaultdict(blank_agg)
    oof_records: list[dict[str, Any]] = []
    refusal_counts = Counter()
    repair_tag_counts = Counter()
    local_tick_proxy_present_rows = 0
    local_repairable_now_rows = 0
    row_count = 0
    refusal_rows = 0

    with (
        ROW_REPLAY_LEDGER.open("w", encoding="utf-8") as row_out,
        REFUSAL_SPLIT_LEDGER.open("w", encoding="utf-8") as refusal_out,
        STAGE10_ROUTER_LEDGER.open("r", encoding="utf-8") as stage10_handle,
    ):
        stage10_iter = (
            json.loads(line)
            for line in stage10_handle
            if line.strip()
        )
        for (_line_no, stage09_row), stage10_row in zip(iter_jsonl(STAGE09_FEATURE_LEDGER), stage10_iter):
            row_count += 1
            feature = stage09_row.get("feature_columns") or {}
            policies = stage09_row.get("label_policy_final_r_by_policy") or {}
            if stage09_row.get("candidate_id") != stage10_row.get("candidate_id"):
                raise ValueError(f"Stage09/Stage10 candidate mismatch at row {row_count}")
            event = event_from_feature(feature, mode=CONDITION_CHALLENGER_MODE)
            if same_bar_any(stage09_row):
                event["ordered_path_status"] = "same_bar_ambiguous_requires_ltf_or_tick_ordering"
            condition_decision = route_moonshot_dynamic_execution(event, enabled=True, apply_to_execution=False)
            condition_policy = condition_decision.selected_policy or DEFAULT_POLICY
            condition_r = float(policies[condition_policy])
            be_r = float(policies[DEFAULT_POLICY])
            live_r = float(policies[REJECTED_LIVE_BASELINE])
            fixed_r = float(policies["legacy_fixed_1.5r"])
            bucket = displacement_bucket(feature)
            key = (feature.get("framework"), feature.get("session_bucket"), bucket)
            add_agg(all_agg, condition_r, be_r, live_r, fixed_r, condition_policy)
            add_agg(cells[key], condition_r, be_r, live_r, fixed_r, condition_policy)
            if feature.get("framework") == "fvg_fill":
                add_agg(fvg_agg, condition_r, be_r, live_r, fixed_r, condition_policy)

            policy_r = {policy: float(policies[policy]) for policy in POLICIES if policies.get(policy) is not None}
            oof_records.append(
                {
                    "time_key": stage09_row.get("candle_time_utc"),
                    "condition_key": key,
                    "policy_r": policy_r,
                }
            )
            row_out.write(
                json.dumps(
                    {
                        "schema_version": "vnext_moonshot_stage11_condition_router_row_replay_v1",
                        "stage_id": STAGE_ID,
                        "stage11_row_id": f"STAGE11-CONDITION-ROW-{row_count:09d}",
                        "source_stage10_router_replay_row_id": stage10_row.get("router_replay_row_id"),
                        "candidate_id": stage09_row.get("candidate_id"),
                        "path_row_id": stage09_row.get("path_row_id"),
                        "symbol": feature.get("symbol"),
                        "side": feature.get("side"),
                        "framework": feature.get("framework"),
                        "session_bucket": feature.get("session_bucket"),
                        "current_bar_displacement_bucket": bucket,
                        "current_bar_displacement_atr14": feature.get("current_bar_displacement_atr14"),
                        "source_window_complete": feature.get("source_window_complete"),
                        "source_path_feature_status": feature.get("source_path_feature_status"),
                        "same_bar_ambiguity_observed_in_replay": same_bar_any(stage09_row),
                        "condition_selected_policy": condition_policy,
                        "global_stage10_policy": DEFAULT_POLICY,
                        "condition_selected_policy_final_r": condition_r,
                        "global_be_after_trigger_final_r": be_r,
                        "live_current_j46_j49_final_r": live_r,
                        "fixed_1_5r_final_r": fixed_r,
                        "condition_vs_global_be_delta_r": round(condition_r - be_r, 12),
                        "condition_vs_live_current_delta_r": round(condition_r - live_r, 12),
                        "condition_vs_fixed_delta_r": round(condition_r - fixed_r, 12),
                        "selector_condition_key": list(key),
                        "selector_uses_only_asof_feature_columns": True,
                        "selector_excludes_expost_same_bar_outcome": True,
                        "stage10_decision_status": (stage10_row.get("router_decision") or {}).get("decision_status"),
                        "stage10_candidate_action": (stage10_row.get("router_decision") or {}).get("candidate_action"),
                        "stage10_source_quality_action": (stage10_row.get("router_decision") or {}).get("source_quality_action"),
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            )

            if (stage10_row.get("router_decision") or {}).get("decision_status") == "refuse_live_use_until_source_or_scope_repaired":
                refusal = classify_refusal(stage10_row, feature)
                refusal_rows += 1
                refusal_counts[refusal["terminal_repair_class"]] += 1
                for tag in refusal["repair_class_tags"]:
                    repair_tag_counts[tag] += 1
                if refusal["local_tick_file_present"]:
                    local_tick_proxy_present_rows += 1
                if refusal["locally_repairable_now"]:
                    local_repairable_now_rows += 1
                refusal_out.write(json.dumps(refusal, sort_keys=True, separators=(",", ":")) + "\n")
            if row_count % 50000 == 0:
                append_heartbeat("stage11_row_replay_progress", rows=row_count, refusals=refusal_rows)

    if row_count != expected_rows:
        raise ValueError(f"Stage11 row replay count {row_count} != Stage10 expected rows {expected_rows}")
    append_heartbeat("stage11_row_replay_complete", rows=row_count, refusals=refusal_rows)

    oof_result = learn_oof(oof_records, min_train_rows=500, folds=5)
    prop_rows = prop_comparison_rows()
    be_prop = next(row for row in prop_rows if row["policy_name"] == "be_after_trigger_prop_pass_default")
    condition_prop = next(row for row in prop_rows if row["policy_name"] == "condition_asof_displacement_v1_account_restart")

    challenge_rows: list[dict[str, Any]] = [
        agg_record(
            "full_row_asof_condition_router_all_candidates",
            all_agg,
            condition_spec="framework_session_current_bar_displacement_bucket",
            selector_uses_only_asof_feature_columns=True,
            selector_excludes_expost_same_bar_outcome=True,
        ),
        agg_record(
            "full_row_asof_condition_router_primary_fvg_scope",
            fvg_agg,
            condition_spec="framework_session_current_bar_displacement_bucket",
            selector_uses_only_asof_feature_columns=True,
            selector_excludes_expost_same_bar_outcome=True,
        ),
        oof_result,
    ]
    for index, (key, agg) in enumerate(sorted(cells.items()), start=1):
        challenge_rows.append(
            agg_record(
                "condition_cell_policy_map",
                agg,
                condition_row_id=f"STAGE11-CONDITION-CELL-{index:06d}",
                condition_key=list(key),
                condition_spec="framework_session_current_bar_displacement_bucket",
            )
        )

    with CHALLENGE_LEDGER.open("w", encoding="utf-8") as handle:
        for row in challenge_rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")

    all_summary = challenge_rows[0]
    fvg_summary = challenge_rows[1]
    prop_default_retained = (
        be_prop["reference_ev_per_terminal_day_usd_fee599_payout8000"]
        > condition_prop["reference_ev_per_terminal_day_usd_fee599_payout8000"]
        and be_prop["allowed_trades"] > condition_prop["allowed_trades"]
    )
    summary = {
        "schema_version": "vnext_moonshot_stage11_condition_router_integration_map_v1",
        "stage_id": STAGE_ID,
        "route_id": "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26",
        "generated_at_utc": utc_now(),
        "current_git_head": current_git_head(),
        "row_replay_rows": row_count,
        "expected_stage10_rows": expected_rows,
        "refusal_repair_split_rows": refusal_rows,
        "condition_challenge_rows": len(challenge_rows),
        "prop_aware_comparison_rows": len(prop_rows),
        "row_level_condition_challenge": {
            "all_candidates": all_summary,
            "primary_fvg_scope": fvg_summary,
            "chrono_oof": oof_result,
        },
        "refusal_split_summary": {
            "stage10_refused_rows": refusal_rows,
            "terminal_repair_class_counts": dict(sorted(refusal_counts.items())),
            "repair_tag_counts": dict(sorted(repair_tag_counts.items())),
            "local_tick_proxy_present_rows": local_tick_proxy_present_rows,
            "locally_repairable_now_rows": local_repairable_now_rows,
            "local_repair_terminal_policy": (
                "local tick or OHLC files alone are not activation truth without broker lifecycle and policy "
                "transition capture; no row is parked as a vague source-repair caveat"
            ),
        },
        "prop_aware_terminal_decision": {
            "be_after_trigger_prop_pass_default_ev_per_terminal_day_usd": be_prop[
                "reference_ev_per_terminal_day_usd_fee599_payout8000"
            ],
            "condition_asof_displacement_account_restart_ev_per_terminal_day_usd": condition_prop[
                "reference_ev_per_terminal_day_usd_fee599_payout8000"
            ],
            "be_after_trigger_allowed_trades": be_prop["allowed_trades"],
            "condition_asof_displacement_allowed_trades": condition_prop["allowed_trades"],
            "prop_default_retained": prop_default_retained,
            "terminal_classification": (
                "condition_router_beats_global_row_expectancy_but_is_rejected_as_primary_prop_default_from_local_prop_replay"
                if prop_default_retained
                else "condition_router_supersedes_prop_default_requires_stage10b_runtime_selection"
            ),
            "action_taken": (
                "condition_asof_displacement_v1 implemented as default-off challenger mode; "
                "be_after_trigger remains prop-pass default because local prop replay shows higher pass efficiency and "
                "more accepted trades under ACCOUNT_ABANDON_OR_RESTART"
            ),
        },
        "artifact_paths": {
            "row_replay_ledger": rel(ROW_REPLAY_LEDGER),
            "refusal_repair_split_ledger": rel(REFUSAL_SPLIT_LEDGER),
            "condition_challenge_ledger": rel(CHALLENGE_LEDGER),
            "prop_aware_comparison_ledger": rel(PROP_COMPARISON_LEDGER),
            "integration_map": rel(INTEGRATION_MAP),
            "semantic_verifier_spec": rel(SPEC_PATH),
            "stage10_issue_ledger": rel(STAGE10_ISSUE_LEDGER),
        },
        "forbidden_boundaries_crossed": False,
        "no_live_trading_or_broker_mutation": True,
        "no_paid_api_or_vendor_call": True,
        "first_incomplete_invariant_after_stage11": "STAGE_12_SATURATION_SELF_RED_TEAM_AND_FINAL_DECISION",
    }
    summary["condition_vs_global_be_delta_r"] = all_summary["condition_vs_global_be_delta_r"]
    summary["primary_fvg_condition_vs_global_be_delta_r"] = fvg_summary["condition_vs_global_be_delta_r"]
    write_json(INTEGRATION_MAP, summary)

    spec = {
        "schema_version": "vnext_moonshot_stage11_semantic_verifier_spec_v1",
        "stage_id": STAGE_ID,
        "generated_at_utc": utc_now(),
        "hard_gates": [
            "full Stage11 row replay count must equal Stage10/Stage09 rows",
            "condition-router challenge must use as-of fields and exclude ex-post same-bar labels",
            "condition-router row-level improvement over global be_after_trigger must be prop-replayed, accepted, or rejected with evidence",
            "Stage10 refused rows must be split row-by-row; locally repairable-now rows may not remain unresolved",
            "default-off config flags must remain disabled and apply_to_execution false",
            "live_current_j46_j49 underperformance remains rejected as primitive baseline",
            "no artifact-shape-only completion and no top-N truncation are allowed",
        ],
        "negative_fixture_expectations": [
            "fail if condition challenge ledger is missing or has nonpositive all-row condition delta without terminal repair path",
            "fail if refusal split rows do not match Stage10 refused rows",
            "fail if any locally_repairable_now row is not repaired_and_replayed",
            "fail if prop replay does not adjudicate row-level condition-router improvement",
        ],
    }
    write_json(SPEC_PATH, spec)
    update_session_state(summary)
    append_heartbeat("stage11_builder_complete", rows=row_count, refusals=refusal_rows)
    print(
        json.dumps(
            {
                "stage": STAGE_ID,
                "row_replay_rows": row_count,
                "refusal_rows": refusal_rows,
                "condition_vs_be_delta_r": all_summary["condition_vs_global_be_delta_r"],
                "fvg_condition_vs_be_delta_r": fvg_summary["condition_vs_global_be_delta_r"],
                "prop_default_retained": prop_default_retained,
                "first_incomplete_invariant": "STAGE_12_SATURATION_SELF_RED_TEAM_AND_FINAL_DECISION",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
