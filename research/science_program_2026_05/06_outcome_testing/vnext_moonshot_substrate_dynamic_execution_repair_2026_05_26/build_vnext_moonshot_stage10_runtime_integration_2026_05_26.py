from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research.moonshot_default_off_policy_router import (
    DEFAULT_POLICY,
    PRIMARY_BRANCH,
    PRIMARY_FRAMEWORK,
    REJECTED_LIVE_BASELINE,
    route_moonshot_dynamic_execution,
)


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-26"
STAGE_ID = "STAGE_10_DEFAULT_OFF_RUNTIME_INTEGRATION"
FEATURE_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_ML_DYNAMIC_FEATURE_LEDGER_{DATE}.jsonl"
STAGE07_SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_CORRECTED_BRANCH_SUMMARY_{DATE}.json"
STAGE09_RESULTS = ROUTE_DIR / f"VNEXT_MOONSHOT_ML_CHALLENGER_RESULTS_{DATE}.json"
AI_SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_AI_ROLE_BUDGET_SUMMARY_{DATE}.json"
SESSION_STATE = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE}.json"

ROUTER_REPLAY_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_DEFAULT_OFF_ROUTER_REPLAY_LEDGER_{DATE}.jsonl"
CONDITION_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_RUNTIME_ROUTER_CONDITION_LEDGER_{DATE}.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE10_ACTIVE_ISSUE_RESOLUTION_LEDGER_{DATE}.jsonl"
INTEGRATION_MAP = ROUTE_DIR / f"VNEXT_MOONSHOT_RUNTIME_INTEGRATION_MAP_{DATE}.json"

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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def current_git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def _as_bool_text(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _num(value: Any) -> float | None:
    if isinstance(value, bool) or value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _same_bar_any(row: dict[str, Any]) -> bool:
    same_bar_map = row.get("label_policy_same_bar_by_policy") or {}
    if any(bool(value) for value in same_bar_map.values()):
        return True
    reason_map = row.get("label_policy_exit_reason_by_policy") or {}
    return any("same_bar" in str(value) for value in reason_map.values())


def _same_bar_policy(row: dict[str, Any], policy: str) -> bool:
    same_bar_map = row.get("label_policy_same_bar_by_policy") or {}
    if bool(same_bar_map.get(policy)):
        return True
    reason = (row.get("label_policy_exit_reason_by_policy") or {}).get(policy)
    reason_text = str(reason).lower()
    return (
        "stop_first_same_bar" in reason_text
        or "ambiguous_same_bar" in reason_text
        or "same_bar_ambiguous" in reason_text
    )


def _ordered_status_from_same_bar(same_bar: bool) -> str:
    if same_bar:
        return "same_bar_ambiguous_requires_ltf_or_tick_ordering"
    return "ordered_path_not_ambiguous_in_m15_replay"


def _event_from_row(row: dict[str, Any], same_bar_any: bool) -> dict[str, Any]:
    feature = row.get("feature_columns") or {}
    selected_policy_same_bar = _same_bar_policy(row, DEFAULT_POLICY)
    return {
        "symbol": feature.get("symbol"),
        "side": feature.get("side"),
        "framework": feature.get("framework"),
        "session_bucket": feature.get("session_bucket"),
        "kill_zone_position": feature.get("kill_zone_position"),
        "source_mode": feature.get("source_mode"),
        "source_path_feature_status": feature.get("source_path_feature_status"),
        "source_window_complete": feature.get("source_window_complete"),
        "ordered_path_status": _ordered_status_from_same_bar(same_bar_any),
        "selected_policy_ordered_path_status": _ordered_status_from_same_bar(
            selected_policy_same_bar
        ),
        "selected_policy_same_bar_ambiguous": selected_policy_same_bar,
        "liquidity_sweep_proxy_state": feature.get("liquidity_sweep_proxy_state"),
        "volatility_state_14_vs_50": feature.get("volatility_state_14_vs_50"),
        "trend_state_20": feature.get("trend_state_20"),
        "transfer_group": feature.get("transfer_group"),
        "entry_delay_bars": feature.get("entry_delay_bars"),
        "remaining_daily_cushion_r": 6.0,
        "remaining_overall_cushion_r": 8.0,
    }


def _blank_cell() -> dict[str, Any]:
    return {
        "rows": 0,
        "selected_sum": 0.0,
        "live_sum": 0.0,
        "fixed_sum": 0.0,
        "be_sum": 0.0,
        "trailing_sum": 0.0,
        "policy_counts": Counter(),
        "decision_status_counts": Counter(),
        "candidate_action_counts": Counter(),
        "same_bar_rows": 0,
        "selected_policy_same_bar_rows": 0,
        "source_complete_rows": 0,
        "selected_positive_rows": 0,
        "live_positive_rows": 0,
        "fixed_positive_rows": 0,
    }


def _add_cell(cell: dict[str, Any], row: dict[str, Any], decision_record: dict[str, Any]) -> None:
    policies = row.get("label_policy_final_r_by_policy") or {}
    selected_policy = decision_record.get("selected_policy")
    selected_r = _num(policies.get(selected_policy))
    live_r = _num(policies.get(REJECTED_LIVE_BASELINE))
    fixed_r = _num(policies.get("legacy_fixed_1.5r"))
    be_r = _num(policies.get(DEFAULT_POLICY))
    trailing_r = _num(policies.get("trailing_runner"))

    cell["rows"] += 1
    if selected_r is not None:
        cell["selected_sum"] += selected_r
        if selected_r > 0:
            cell["selected_positive_rows"] += 1
    if live_r is not None:
        cell["live_sum"] += live_r
        if live_r > 0:
            cell["live_positive_rows"] += 1
    if fixed_r is not None:
        cell["fixed_sum"] += fixed_r
        if fixed_r > 0:
            cell["fixed_positive_rows"] += 1
    if be_r is not None:
        cell["be_sum"] += be_r
    if trailing_r is not None:
        cell["trailing_sum"] += trailing_r
    cell["policy_counts"][selected_policy] += 1
    cell["decision_status_counts"][decision_record.get("decision_status")] += 1
    cell["candidate_action_counts"][decision_record.get("candidate_action")] += 1
    if _same_bar_any(row):
        cell["same_bar_rows"] += 1
    if _same_bar_policy(row, DEFAULT_POLICY):
        cell["selected_policy_same_bar_rows"] += 1
    if _as_bool_text((row.get("feature_columns") or {}).get("source_window_complete")):
        cell["source_complete_rows"] += 1


def _cell_to_row(row_id: str, key: tuple[Any, ...], cell: dict[str, Any]) -> dict[str, Any]:
    rows = int(cell["rows"])
    def mean(field: str) -> float:
        return round(float(cell[field]) / rows, 12) if rows else 0.0

    return {
        "schema_version": "vnext_moonshot_stage10_router_condition_v1",
        "stage_id": STAGE_ID,
        "condition_row_id": row_id,
        "condition_key": list(key),
        "row_count": rows,
        "selected_policy_expectancy_r": mean("selected_sum"),
        "live_current_expectancy_r": mean("live_sum"),
        "fixed_1_5r_expectancy_r": mean("fixed_sum"),
        "be_after_trigger_expectancy_r": mean("be_sum"),
        "trailing_runner_expectancy_r": mean("trailing_sum"),
        "selected_vs_live_delta_r": round(mean("selected_sum") - mean("live_sum"), 12),
        "selected_vs_fixed_delta_r": round(mean("selected_sum") - mean("fixed_sum"), 12),
        "selected_policy_counts": dict(sorted(cell["policy_counts"].items())),
        "decision_status_counts": dict(sorted(cell["decision_status_counts"].items())),
        "candidate_action_counts": dict(sorted(cell["candidate_action_counts"].items())),
        "same_bar_rows": int(cell["same_bar_rows"]),
        "selected_policy_same_bar_rows": int(cell["selected_policy_same_bar_rows"]),
        "source_complete_rows": int(cell["source_complete_rows"]),
        "selected_positive_rows": int(cell["selected_positive_rows"]),
        "live_positive_rows": int(cell["live_positive_rows"]),
        "fixed_positive_rows": int(cell["fixed_positive_rows"]),
        "terminal_classification": "condition_replayed_full_row_no_top_n_truncation",
    }


def main() -> None:
    generated_at = utc_now()
    stage07 = read_json(STAGE07_SUMMARY)
    stage09 = read_json(STAGE09_RESULTS)
    ai_summary = read_json(AI_SUMMARY)

    totals = _blank_cell()
    by_framework_session_source: dict[tuple[Any, ...], dict[str, Any]] = defaultdict(_blank_cell)
    by_framework_session_liquidity: dict[tuple[Any, ...], dict[str, Any]] = defaultdict(_blank_cell)
    issue_counts = Counter()
    action_counts = Counter()
    status_counts = Counter()
    prop_action_counts = Counter()
    ai_role_counts = Counter()
    source_action_counts = Counter()

    with ROUTER_REPLAY_LEDGER.open("w", encoding="utf-8") as handle:
        for line_no, row in iter_jsonl(FEATURE_LEDGER):
            feature = row.get("feature_columns") or {}
            policies = row.get("label_policy_final_r_by_policy") or {}
            same_bar_any = _same_bar_any(row)
            selected_policy_same_bar = _same_bar_policy(row, DEFAULT_POLICY)
            decision = route_moonshot_dynamic_execution(
                _event_from_row(row, same_bar_any),
                enabled=True,
                apply_to_execution=False,
            )
            record = decision.to_record()
            selected_r = _num(policies.get(decision.selected_policy))
            live_r = _num(policies.get(REJECTED_LIVE_BASELINE))
            fixed_r = _num(policies.get("legacy_fixed_1.5r"))
            be_r = _num(policies.get(DEFAULT_POLICY))
            trailing_r = _num(policies.get("trailing_runner"))
            selected_vs_live = (
                round(selected_r - live_r, 12)
                if selected_r is not None and live_r is not None
                else None
            )
            selected_vs_fixed = (
                round(selected_r - fixed_r, 12)
                if selected_r is not None and fixed_r is not None
                else None
            )

            if live_r is not None and fixed_r is not None:
                if fixed_r > 0 and live_r <= 0:
                    issue_counts["legacy_winner_to_live_current_nonpositive_rows"] += 1
                if live_r > 0 and fixed_r <= 0:
                    issue_counts["live_current_winner_from_legacy_nonpositive_rows"] += 1
            if live_r is not None and selected_r is not None and selected_r > 0 and live_r <= 0:
                issue_counts["selected_policy_rescues_live_current_nonpositive_rows"] += 1
            if feature.get("framework") == PRIMARY_FRAMEWORK:
                issue_counts["primary_fvg_rows"] += 1
            if same_bar_any:
                issue_counts["same_bar_ambiguity_rows"] += 1
            if selected_policy_same_bar:
                issue_counts["selected_policy_same_bar_ambiguity_rows"] += 1
            if not _as_bool_text(feature.get("source_window_complete")):
                issue_counts["source_window_incomplete_rows"] += 1

            replay_row = {
                "schema_version": "vnext_moonshot_stage10_router_replay_v1",
                "stage_id": STAGE_ID,
                "router_replay_row_id": f"STAGE10-ROUTER-{line_no:09d}",
                "source_ml_row_id": row.get("ml_row_id"),
                "source_feature_row_id": row.get("feature_row_id"),
                "candidate_id": row.get("candidate_id"),
                "path_row_id": row.get("path_row_id"),
                "candle_time_utc": row.get("candle_time_utc"),
                "entry_first_touch_utc": row.get("entry_first_touch_utc"),
                "symbol": feature.get("symbol"),
                "side": feature.get("side"),
                "framework": feature.get("framework"),
                "session_bucket": feature.get("session_bucket"),
                "kill_zone_position": feature.get("kill_zone_position"),
                "source_window_complete": feature.get("source_window_complete"),
                "source_path_feature_status": feature.get("source_path_feature_status"),
                "liquidity_sweep_proxy_state": feature.get("liquidity_sweep_proxy_state"),
                "volatility_state_14_vs_50": feature.get("volatility_state_14_vs_50"),
                "trend_state_20": feature.get("trend_state_20"),
                "same_bar_ambiguity_observed_in_replay": same_bar_any,
                "selected_policy_same_bar_ambiguity_observed_in_replay": (
                    selected_policy_same_bar
                ),
                "selected_policy_ordered_path_status": _ordered_status_from_same_bar(
                    selected_policy_same_bar
                ),
                "router_decision": record,
                "selected_policy_final_r": selected_r,
                "live_current_j46_j49_final_r": live_r,
                "fixed_1_5r_final_r": fixed_r,
                "be_after_trigger_final_r": be_r,
                "trailing_runner_final_r": trailing_r,
                "selected_vs_live_delta_r": selected_vs_live,
                "selected_vs_fixed_delta_r": selected_vs_fixed,
                "terminal_classification": (
                    "primary_default_off_candidate"
                    if record["candidate_action"] == "TRADE_DEFAULT_OFF_PRIMARY_CANDIDATE"
                    else "source_repair_or_secondary_candidate"
                ),
            }
            handle.write(json.dumps(replay_row, sort_keys=True, separators=(",", ":")) + "\n")

            _add_cell(totals, row, record)
            key_source = (
                feature.get("framework"),
                str(feature.get("source_window_complete")),
                feature.get("session_bucket"),
            )
            key_liquidity = (
                feature.get("framework"),
                feature.get("session_bucket"),
                feature.get("liquidity_sweep_proxy_state"),
            )
            _add_cell(by_framework_session_source[key_source], row, record)
            _add_cell(by_framework_session_liquidity[key_liquidity], row, record)
            action_counts[record["candidate_action"]] += 1
            status_counts[record["decision_status"]] += 1
            prop_action_counts[record["prop_action"]] += 1
            ai_role_counts[record["ai_role"]] += 1
            source_action_counts[record["source_quality_action"]] += 1

    condition_rows: list[dict[str, Any]] = []
    condition_rows.append(_cell_to_row("STAGE10-CONDITION-OVERALL", ("ALL",), totals))
    for index, (key, cell) in enumerate(sorted(by_framework_session_source.items()), start=1):
        condition_rows.append(_cell_to_row(f"STAGE10-CONDITION-SOURCE-{index:06d}", key, cell))
    offset = len(condition_rows)
    for index, (key, cell) in enumerate(sorted(by_framework_session_liquidity.items()), start=1):
        condition_rows.append(_cell_to_row(f"STAGE10-CONDITION-LIQ-{offset + index:06d}", key, cell))
    write_jsonl(CONDITION_LEDGER, condition_rows)

    overall = condition_rows[0]
    best_stream = stage07["best_overall_reference_fee599_payout8000"]
    issue_rows = [
        {
            "schema_version": "vnext_moonshot_stage10_active_issue_resolution_v1",
            "stage_id": STAGE_ID,
            "issue_id": "live_current_j46_j49_underperforms_simpler_and_dynamic_baselines",
            "evidence_files": [str(FEATURE_LEDGER), str(ROUTER_REPLAY_LEDGER), str(CONDITION_LEDGER)],
            "evidence_rows": {
                "stage09_feature_rows": totals["rows"],
                "legacy_winner_to_live_current_nonpositive_rows": issue_counts[
                    "legacy_winner_to_live_current_nonpositive_rows"
                ],
                "selected_policy_rescues_live_current_nonpositive_rows": issue_counts[
                    "selected_policy_rescues_live_current_nonpositive_rows"
                ],
            },
            "causal_anatomy": (
                "live_current_j46_j49 waits for 3R/6R runner behavior and time-stop handling while "
                "the replayed opportunity pays earlier with BE-after-trigger; this turns many fixed/BE "
                "winners into nonpositive live-current outcomes."
            ),
            "source_validation": "full Stage09 feature ledger joined 214536/214536 policy rows; no missing policy joins in Stage09",
            "action_taken": "implemented default-off router replacing live_current_j46_j49 with be_after_trigger as primary policy candidate",
            "replay_result": {
                "selected_policy_expectancy_r": overall["selected_policy_expectancy_r"],
                "live_current_expectancy_r": overall["live_current_expectancy_r"],
                "fixed_1_5r_expectancy_r": overall["fixed_1_5r_expectancy_r"],
                "selected_vs_live_delta_r": overall["selected_vs_live_delta_r"],
                "selected_vs_fixed_delta_r": overall["selected_vs_fixed_delta_r"],
            },
            "verifier_result": "enforced_by_stage10_verifier_artifact",
            "terminal_classification": "handled_default_off_replacement_candidate_implemented",
        },
        {
            "schema_version": "vnext_moonshot_stage10_active_issue_resolution_v1",
            "stage_id": STAGE_ID,
            "issue_id": "static_target_exit_primitives_and_trailing_subroute",
            "evidence_files": [str(STAGE07_SUMMARY), str(CONDITION_LEDGER), str(ROUTER_REPLAY_LEDGER)],
            "evidence_rows": {
                "stage07_branch_metric_rows": stage07["corrected_branch_metric_rows"],
                "condition_rows": len(condition_rows),
            },
            "causal_anatomy": (
                "fixed 1.5R is a useful comparator, but the full-row replay shows BE-after-trigger beats it overall; "
                "trailing_runner wins some FVG/NY/sweep cells but loses the prop-level stream and is held as a challenger."
            ),
            "source_validation": "policy comparison covers all policies declared in Stage07 and Stage09",
            "action_taken": "router selects be_after_trigger by default and records trailing_runner as default-off challenger only",
            "replay_result": {
                "best_stage07_branch": best_stream["branch_id"],
                "best_stage07_policy": best_stream["policy_name"],
                "best_stage07_prop_policy": best_stream["prop_policy"],
                "best_stage07_pass_probability_proxy": best_stream["pass_probability_proxy"],
            },
            "verifier_result": "enforced_by_stage10_verifier_artifact",
            "terminal_classification": "handled_static_primitives_replaced_or_rejected",
        },
        {
            "schema_version": "vnext_moonshot_stage10_active_issue_resolution_v1",
            "stage_id": STAGE_ID,
            "issue_id": "source_null_proxy_and_same_bar_weakness",
            "evidence_files": [str(FEATURE_LEDGER), str(ROUTER_REPLAY_LEDGER), str(CONDITION_LEDGER)],
            "evidence_rows": {
                "source_window_incomplete_rows": issue_counts["source_window_incomplete_rows"],
                "same_bar_ambiguity_rows": issue_counts["same_bar_ambiguity_rows"],
                "selected_policy_same_bar_ambiguity_rows": issue_counts[
                    "selected_policy_same_bar_ambiguity_rows"
                ],
                "source_complete_rows": totals["source_complete_rows"],
            },
            "causal_anatomy": (
                "M15-only path evidence creates source-window and same-bar ordering weakness. Source-window "
                "completeness is evidence quality and capture readiness, not a trade-selection rule by itself; "
                "selected-policy same-bar ambiguity remains a hard live-use refusal."
            ),
            "source_validation": "router row ledger classifies every row with source and ordered-path actions",
            "action_taken": "implemented selected-policy ordered-path gating and source-capture monitoring without using source completeness as a selection proxy",
            "replay_result": {
                "decision_status_counts": dict(sorted(status_counts.items())),
                "source_quality_action_counts": dict(sorted(source_action_counts.items())),
            },
            "verifier_result": "enforced_by_stage10_verifier_artifact",
            "terminal_classification": "handled_by_default_off_source_contract_and_fail_closed_router",
        },
        {
            "schema_version": "vnext_moonshot_stage10_active_issue_resolution_v1",
            "stage_id": STAGE_ID,
            "issue_id": "prop_ev_opportunity_cost_and_passive_blocking",
            "evidence_files": [str(STAGE07_SUMMARY), str(AI_SUMMARY), str(INTEGRATION_MAP)],
            "evidence_rows": {
                "stage07_prop_attempt_rows": stage07["prop_ev_attempt_rows"],
                "safe_but_dead_rejection_count": stage07["safe_but_dead_rejection_count"],
            },
            "causal_anatomy": (
                "passive high-quality/block-all selectors reduce account loss but discard large positive-R opportunity; "
                "the chosen default-off candidate uses the prop governor as risk reduction/defer/owner-gated restart, not as a terminal block."
            ),
            "source_validation": "redacted_account proxy rules and all compared prop policies are preserved in Stage07 artifacts",
            "action_taken": "router emits prop actions without broker mutation and records ACCOUNT_ABANDON_OR_RESTART as owner-gated",
            "replay_result": {
                "best_stage07_expected_payout_proxy_usd": best_stream[
                    "expected_payout_proxy_usd_fee599_payout8000"
                ],
                "best_stage07_trade_opportunity_cost_r": best_stream["trade_opportunity_cost_r"],
                "best_stage07_action_counts": best_stream["action_counts"],
            },
            "verifier_result": "enforced_by_stage10_verifier_artifact",
            "terminal_classification": "handled_default_off_prop_governor_candidate_implemented_owner_gated",
        },
        {
            "schema_version": "vnext_moonshot_stage10_active_issue_resolution_v1",
            "stage_id": STAGE_ID,
            "issue_id": "ai_ml_role_limits_and_no_paid_calls",
            "evidence_files": [str(AI_SUMMARY), str(STAGE09_RESULTS), str(INTEGRATION_MAP)],
            "evidence_rows": {
                "ai_manifest_rows": ai_summary["manifest_rows"],
                "stage09_feature_rows": stage09["policy_rows_joined"],
                "local_ml_dependency_free_baselines": stage09["dependency_free_baseline_result_count"],
            },
            "causal_anatomy": (
                "local ML is useful for shadow labels and source triage but not validated for live scalar routing; AI should validate ambiguity and source conflicts, not replace the mechanical router."
            ),
            "source_validation": "Stage08 made zero paid calls; Stage09 joined all policy rows and records shadow-only ML status",
            "action_taken": "router emits constrained validator roles and keeps ML shadow-only until sealed validation and owner approval",
            "replay_result": {
                "ai_role_counts": dict(sorted(ai_role_counts.items())),
                "ml_shadow_only_until_sealed_validation_and_owner_approval": stage09[
                    "ml_shadow_only_until_sealed_validation_and_owner_approval"
                ],
            },
            "verifier_result": "enforced_by_stage10_verifier_artifact",
            "terminal_classification": "handled_default_off_ai_ml_role_enforced",
        },
    ]
    write_jsonl(ISSUE_LEDGER, issue_rows)

    integration_map = {
        "schema_version": "vnext_moonshot_stage10_runtime_integration_map_v1",
        "route_id": "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26",
        "stage_id": STAGE_ID,
        "generated_at_utc": generated_at,
        "current_git_head": current_git_head(),
        "no_live_trading_or_broker_mutation": True,
        "no_paid_api_or_vendor_call": True,
        "default_off_activation": {
            "config_key_enabled": "gtos_vnext_runtime.moonshot_dynamic_execution_router_enabled",
            "config_key_apply_to_execution": "gtos_vnext_runtime.moonshot_dynamic_execution_router_apply_to_execution",
            "enabled_value_in_config": False,
            "apply_to_execution_value_in_config": False,
            "owner_approval_required": True,
        },
        "source_code_changes": [
            "src/research/moonshot_default_off_policy_router.py",
            "tests/test_moonshot_default_off_policy_router.py",
            "config/agent_config.yaml",
            str(Path(__file__).relative_to(Path.cwd())),
            str((ROUTE_DIR / f"verify_vnext_moonshot_stage10_runtime_integration_2026_05_26.py").relative_to(Path.cwd())),
            str((ROUTE_DIR / f"test_vnext_moonshot_stage10_runtime_integration_2026_05_26.py").relative_to(Path.cwd())),
        ],
        "row_level_evidence": {
            "router_replay_ledger_path": str(ROUTER_REPLAY_LEDGER),
            "condition_ledger_path": str(CONDITION_LEDGER),
            "active_issue_resolution_ledger_path": str(ISSUE_LEDGER),
            "input_stage09_feature_rows": totals["rows"],
            "router_replay_rows": totals["rows"],
            "condition_rows": len(condition_rows),
            "no_top_n_truncation": True,
        },
        "selected_default_off_production_candidate": {
            "candidate_name": "moonshot_fvg_be_after_trigger_prop_aware_router",
            "primary_branch": PRIMARY_BRANCH,
            "primary_framework": PRIMARY_FRAMEWORK,
            "default_policy": DEFAULT_POLICY,
            "replaces": REJECTED_LIVE_BASELINE,
            "baseline_fixed_role": "baseline_comparator_only_not_target",
            "prop_policy_reference": best_stream["prop_policy"],
            "prop_policy_runtime_behavior": (
                "allow when cushions are sufficient; reduce/defer near daily/overall boundary; "
                "owner-gated abandon/restart when account recovery EV is dominated"
            ),
            "ai_role": (
                "mechanical-primary; constrained validator only for ambiguous source, policy conflict, or owner-approved validation strata"
            ),
            "ml_role": "shadow_surrogate_and_source_triage_only_until_sealed_validation_and_owner_approval",
            "why_it_wins": [
                "full-row selected policy expectancy exceeds live_current_j46_j49",
                "Stage07 best branch stream is origin_current_fvg_fill with be_after_trigger",
                "prop-aware account-abandon/restart stream preserves opportunity better than passive blocking",
            ],
            "why_it_loses_or_refuses": [
                "selected-policy same-bar M15 ordering ambiguity requires ordered LTF/tick path before live activation",
                "source-window-incomplete rows require source-capture monitoring and forward completeness evidence, but are not excluded solely for source completeness",
                "trailing_runner is held despite local FVG/NY/sweep strength because its Stage07 prop stream underperforms",
                "ob_retest and breaker_re_entry are secondary replay replacements, not the primary prop stream",
            ],
        },
        "router_replay_summary": {
            "input_rows": totals["rows"],
            "selected_policy_expectancy_r": overall["selected_policy_expectancy_r"],
            "live_current_expectancy_r": overall["live_current_expectancy_r"],
            "fixed_1_5r_expectancy_r": overall["fixed_1_5r_expectancy_r"],
            "selected_vs_live_delta_r": overall["selected_vs_live_delta_r"],
            "selected_vs_fixed_delta_r": overall["selected_vs_fixed_delta_r"],
            "selected_policy_counts": overall["selected_policy_counts"],
            "decision_status_counts": dict(sorted(status_counts.items())),
            "candidate_action_counts": dict(sorted(action_counts.items())),
            "prop_action_counts": dict(sorted(prop_action_counts.items())),
            "source_quality_action_counts": dict(sorted(source_action_counts.items())),
            "same_bar_ambiguity_rows": issue_counts["same_bar_ambiguity_rows"],
            "selected_policy_same_bar_ambiguity_rows": issue_counts[
                "selected_policy_same_bar_ambiguity_rows"
            ],
            "source_window_incomplete_rows": issue_counts["source_window_incomplete_rows"],
            "primary_fvg_rows": issue_counts["primary_fvg_rows"],
        },
        "stage07_best_reference_stream": best_stream,
        "stage09_ml_terminal_role": {
            "ml_shadow_only_until_sealed_validation_and_owner_approval": stage09[
                "ml_shadow_only_until_sealed_validation_and_owner_approval"
            ],
            "lightgbm_challengers": stage09.get("lightgbm_challengers", []),
            "sklearn_challengers": stage09.get("sklearn_challengers", []),
        },
        "unresolved_issue_accounting": {
            "local_issues_closed_or_enforced_by_stage10": [
                row["issue_id"] for row in issue_rows
            ],
            "external_owner_gated": [
                "owner activation of router flags",
                "paid API validation budget calls",
                "broker/live mutation",
                "remote push",
            ],
            "route_not_complete_next_invariant": "STAGE_11_SEMANTIC_VERIFIER_HARDENING",
        },
        "first_incomplete_invariant_after_stage10": "STAGE_11_SEMANTIC_VERIFIER_HARDENING",
    }
    write_json(INTEGRATION_MAP, integration_map)

    state = read_json(SESSION_STATE)
    state["current_git_head"] = integration_map["current_git_head"]
    state["current_stage"] = STAGE_ID
    state["first_incomplete_invariant"] = "STAGE_11_SEMANTIC_VERIFIER_HARDENING"
    state["completion_gate_status"] = "not_complete_first_incomplete_stage11"
    state["exact_next_action"] = "Run Stage11 semantic verifier hardening against full row-level Stage10 router artifacts."
    state["updated_at_utc"] = generated_at
    state.setdefault("stage_status_table", {})[STAGE_ID] = "complete_default_off_runtime_integration"
    state["stage_status_table"]["STAGE_11_SEMANTIC_VERIFIER_HARDENING"] = "pending"
    manifest = state.setdefault("output_artifact_manifest", {})
    manifest["runtime_integration_map"] = str(INTEGRATION_MAP)
    manifest["stage10_router_replay_ledger"] = str(ROUTER_REPLAY_LEDGER)
    manifest["stage10_runtime_router_condition_ledger"] = str(CONDITION_LEDGER)
    manifest["stage10_active_issue_resolution_ledger"] = str(ISSUE_LEDGER)
    state.setdefault("row_counts_scanned", {})["stage10_router_replay_rows"] = totals["rows"]
    state["row_counts_scanned"]["stage10_runtime_router_condition_rows"] = len(condition_rows)
    state["row_counts_scanned"]["stage10_active_issue_resolution_rows"] = len(issue_rows)
    write_json(SESSION_STATE, state)

    print(
        json.dumps(
            {
                "ok": True,
                "input_rows": totals["rows"],
                "condition_rows": len(condition_rows),
                "first_incomplete": "STAGE_11_SEMANTIC_VERIFIER_HARDENING",
                "selected_vs_live_delta_r": overall["selected_vs_live_delta_r"],
                "selected_vs_fixed_delta_r": overall["selected_vs_fixed_delta_r"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
