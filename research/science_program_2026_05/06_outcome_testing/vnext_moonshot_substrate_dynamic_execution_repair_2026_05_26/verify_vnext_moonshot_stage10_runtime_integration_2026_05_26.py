from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-26"
INTEGRATION_MAP = ROUTE_DIR / f"VNEXT_MOONSHOT_RUNTIME_INTEGRATION_MAP_{DATE}.json"
ROUTER_REPLAY_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_DEFAULT_OFF_ROUTER_REPLAY_LEDGER_{DATE}.jsonl"
CONDITION_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_RUNTIME_ROUTER_CONDITION_LEDGER_{DATE}.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE10_ACTIVE_ISSUE_RESOLUTION_LEDGER_{DATE}.jsonl"
SESSION_STATE = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE10_VERIFICATION_RESULT_{DATE}.json"
CONFIG = Path("config/agent_config.yaml")


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


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> None:
    errors: list[str] = []
    integration = read_json(INTEGRATION_MAP)
    state = read_json(SESSION_STATE)

    if integration.get("stage_id") != "STAGE_10_DEFAULT_OFF_RUNTIME_INTEGRATION":
        fail(errors, "integration map does not identify Stage10")
    if not integration.get("no_live_trading_or_broker_mutation"):
        fail(errors, "integration map does not preserve no-live/broker boundary")
    if not integration.get("no_paid_api_or_vendor_call"):
        fail(errors, "integration map does not preserve no-paid-call boundary")

    activation = integration.get("default_off_activation", {})
    if activation.get("enabled_value_in_config") is not False:
        fail(errors, "router enabled config value is not false")
    if activation.get("apply_to_execution_value_in_config") is not False:
        fail(errors, "router apply_to_execution config value is not false")

    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    runtime_cfg = cfg.get("gtos_vnext_runtime", {})
    if runtime_cfg.get("moonshot_dynamic_execution_router_enabled") is not False:
        fail(errors, "config moonshot_dynamic_execution_router_enabled is not false")
    if runtime_cfg.get("moonshot_dynamic_execution_router_apply_to_execution") is not False:
        fail(errors, "config moonshot_dynamic_execution_router_apply_to_execution is not false")
    if runtime_cfg.get("moonshot_dynamic_execution_router_policy") != "be_after_trigger":
        fail(errors, "config router policy is not be_after_trigger")
    if runtime_cfg.get("moonshot_dynamic_execution_router_replaces_policy") != "live_current_j46_j49":
        fail(errors, "config router replacement policy is not live_current_j46_j49")

    for path_text in integration.get("source_code_changes", []):
        if not Path(path_text).exists():
            fail(errors, f"declared source/test/config change path is missing: {path_text}")

    replay_rows = 0
    runtime_effect_rows = 0
    candidate_allowed_rows = 0
    selected_policy_counts = Counter()
    decision_status_counts = Counter()
    source_action_counts = Counter()
    selected_sum = 0.0
    live_sum = 0.0
    fixed_sum = 0.0
    null_selected_rows = 0
    for _line_no, row in iter_jsonl(ROUTER_REPLAY_LEDGER):
        replay_rows += 1
        decision = row.get("router_decision") or {}
        if decision.get("runtime_effect_now"):
            runtime_effect_rows += 1
        if decision.get("candidate_use_allowed_now"):
            candidate_allowed_rows += 1
        selected_policy_counts[decision.get("selected_policy")] += 1
        decision_status_counts[decision.get("decision_status")] += 1
        source_action_counts[decision.get("source_quality_action")] += 1
        selected = row.get("selected_policy_final_r")
        live = row.get("live_current_j46_j49_final_r")
        fixed = row.get("fixed_1_5r_final_r")
        if selected is None:
            null_selected_rows += 1
        else:
            selected_sum += float(selected)
        if live is not None:
            live_sum += float(live)
        if fixed is not None:
            fixed_sum += float(fixed)

    expected_rows = integration["row_level_evidence"]["input_stage09_feature_rows"]
    if replay_rows != expected_rows:
        fail(errors, f"router replay rows {replay_rows} != expected {expected_rows}")
    if replay_rows != integration["row_level_evidence"]["router_replay_rows"]:
        fail(errors, "router replay row count does not match integration map")
    if runtime_effect_rows or candidate_allowed_rows:
        fail(errors, "default-off replay emitted runtime effect or candidate-use rows")
    if null_selected_rows:
        fail(errors, f"router replay has {null_selected_rows} null selected-policy rows")
    if selected_policy_counts.get("be_after_trigger", 0) != replay_rows:
        fail(errors, "be_after_trigger is not selected for every replayed row")
    if "refuse_live_use_until_source_or_scope_repaired" not in decision_status_counts:
        fail(errors, "source/scope refusal path was not exercised")
    if "SOURCE_OK_FOR_DEFAULT_OFF_REPLAY" not in source_action_counts:
        fail(errors, "source-ok path was not exercised")

    selected_expectancy = selected_sum / replay_rows
    live_expectancy = live_sum / replay_rows
    fixed_expectancy = fixed_sum / replay_rows
    if selected_expectancy <= live_expectancy:
        fail(errors, "selected default-off policy does not beat live_current_j46_j49")
    if selected_expectancy <= fixed_expectancy:
        fail(errors, "selected default-off policy does not beat fixed 1.5R")

    condition_rows = sum(1 for _line_no, _row in iter_jsonl(CONDITION_LEDGER))
    if condition_rows != integration["row_level_evidence"]["condition_rows"]:
        fail(errors, "condition ledger row count does not match integration map")
    if condition_rows < 20:
        fail(errors, "condition ledger is too small to be semantic")

    issue_rows = [row for _line_no, row in iter_jsonl(ISSUE_LEDGER)]
    required_issue_ids = {
        "live_current_j46_j49_underperforms_simpler_and_dynamic_baselines",
        "static_target_exit_primitives_and_trailing_subroute",
        "source_null_proxy_and_same_bar_weakness",
        "prop_ev_opportunity_cost_and_passive_blocking",
        "ai_ml_role_limits_and_no_paid_calls",
    }
    found_issue_ids = {row.get("issue_id") for row in issue_rows}
    if required_issue_ids - found_issue_ids:
        fail(errors, f"missing active issue resolutions: {sorted(required_issue_ids - found_issue_ids)}")
    for row in issue_rows:
        terminal = str(row.get("terminal_classification") or "")
        if not terminal or "known_issue" in terminal or "caveat" in terminal:
            fail(errors, f"issue {row.get('issue_id')} has non-terminal classification {terminal!r}")
        if not row.get("action_taken") or not row.get("replay_result"):
            fail(errors, f"issue {row.get('issue_id')} lacks action/replay evidence")

    if state.get("first_incomplete_invariant") != "STAGE_11_SEMANTIC_VERIFIER_HARDENING":
        fail(errors, "session state did not advance to Stage11")
    if state.get("completion_gate_status") != "not_complete_first_incomplete_stage11":
        fail(errors, "completion gate status is not Stage11 incomplete")

    summary = integration.get("router_replay_summary", {})
    if summary.get("selected_vs_live_delta_r", 0) <= 0:
        fail(errors, "integration summary has nonpositive selected-vs-live delta")
    if summary.get("selected_vs_fixed_delta_r", 0) <= 0:
        fail(errors, "integration summary has nonpositive selected-vs-fixed delta")
    selected_candidate = integration.get("selected_default_off_production_candidate", {})
    if selected_candidate.get("default_policy") != "be_after_trigger":
        fail(errors, "selected candidate default policy is not be_after_trigger")
    if selected_candidate.get("replaces") != "live_current_j46_j49":
        fail(errors, "selected candidate does not replace live_current_j46_j49")

    result = {
        "schema_version": "vnext_moonshot_stage10_verification_result_v1",
        "stage_id": "STAGE_10_DEFAULT_OFF_RUNTIME_INTEGRATION",
        "generated_at_utc": utc_now(),
        "ok": not errors,
        "errors": errors,
        "router_replay_rows": replay_rows,
        "condition_rows": condition_rows,
        "issue_rows": len(issue_rows),
        "selected_expectancy_r": round(selected_expectancy, 12) if replay_rows else None,
        "live_current_expectancy_r": round(live_expectancy, 12) if replay_rows else None,
        "fixed_1_5r_expectancy_r": round(fixed_expectancy, 12) if replay_rows else None,
        "runtime_effect_rows": runtime_effect_rows,
        "candidate_allowed_rows": candidate_allowed_rows,
        "first_incomplete_invariant": state.get("first_incomplete_invariant"),
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
