from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"

STATE_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_SESSION_STATE_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE}.json"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONTROL_LEDGER_{DATE}.jsonl"

CONFIG_PATH = REPO_ROOT / "config/agent_config.yaml"
STAGE03_CONTRACT = ROUTE_DIR / f"VNEXT_REPLACEMENT_PRODUCTION_CANDIDATE_CONTRACT_{DATE}.json"
STAGE05_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_SUMMARY_{DATE}.json"
STAGE05_VERIFIER = ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_VERIFIER_{DATE}.json"
STAGE06_VERIFIER = ROUTE_DIR / f"VNEXT_REPLACEMENT_LEGACY_VS_VNEXT_DELTA_VERIFIER_{DATE}.json"
STAGE08_MAP = ROUTE_DIR / f"VNEXT_REPLACEMENT_MARKET_SOURCE_ACTIVATION_MAP_{DATE}.json"
STAGE09_AI_MANIFEST = ROUTE_DIR / f"VNEXT_REPLACEMENT_AI_CALIBRATION_MANIFEST_{DATE}.json"
STAGE10_MAP = ROUTE_DIR / f"VNEXT_REPLACEMENT_ML_MONITORING_INTEGRATION_MAP_{DATE}.json"

MOONSHOT_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"
)
MOONSHOT_RUNTIME_MAP = MOONSHOT_DIR / f"VNEXT_MOONSHOT_RUNTIME_INTEGRATION_MAP_{DATE}.json"
MOONSHOT_BRANCH_SUMMARY = MOONSHOT_DIR / f"VNEXT_MOONSHOT_CORRECTED_BRANCH_SUMMARY_{DATE}.json"
MOONSHOT_CONDITION_MAP = MOONSHOT_DIR / f"VNEXT_MOONSHOT_STAGE11_CONDITION_ROUTER_INTEGRATION_MAP_{DATE}.json"

OUTPUT_DOSSIER = ROUTE_DIR / f"VNEXT_REPLACEMENT_PRODUCTION_ACTIVATION_DOSSIER_{DATE}.md"
OUTPUT_OVERLAY = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONFIG_OVERLAY_DIFF_{DATE}.yaml"
OUTPUT_ROLLBACK = ROUTE_DIR / f"VNEXT_REPLACEMENT_ROLLBACK_RUNBOOK_{DATE}.md"
OUTPUT_DEMO = ROUTE_DIR / f"VNEXT_REPLACEMENT_DEMO_SHADOW_ACTIVATION_RUNBOOK_{DATE}.md"
OUTPUT_MONITORING = ROUTE_DIR / f"VNEXT_REPLACEMENT_MONITORING_CHECKLIST_{DATE}.md"

MONITORING_LOG_PATH = "shadow_logs/gtos_vnext_replacement_monitoring.jsonl"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rel(path: Path | str) -> str:
    if isinstance(path, str):
        path = Path(path)
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _upsert_manifest_output(manifest: dict[str, Any], entry: dict[str, Any]) -> None:
    outputs = manifest.setdefault("outputs", [])
    for index, existing in enumerate(outputs):
        if existing.get("path") == entry["path"]:
            outputs[index] = {**existing, **entry}
            return
    outputs.append(entry)


def _append_control(row: dict[str, Any]) -> None:
    with CONTROL_LEDGER.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _append_test_result(state: dict[str, Any], command: str, result: str, timestamp: str) -> None:
    tests = state.setdefault("tests_verifiers_run", [])
    tests[:] = [row for row in tests if row.get("command") != command]
    tests.append({"command": command, "result": result, "timestamp_utc": timestamp})


def _fmt(value: Any, digits: int = 6) -> str:
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _scenario_metrics(stage06: dict[str, Any], key: str) -> dict[str, Any]:
    return dict(stage06.get("overall_scenario_metrics", {}).get(key, {}))


def _market_table(markets: list[dict[str, Any]]) -> str:
    rows = [
        "| Symbol | Activation status | Source class | Candidate rows | Complete source ratio |",
        "|---|---|---|---:|---:|",
    ]
    for market in sorted(markets, key=lambda row: str(row.get("symbol"))):
        ratio = market.get("source_window_complete_ratio")
        rows.append(
            "| {symbol} | {status} | {source_class} | {rows} | {ratio} |".format(
                symbol=market.get("symbol"),
                status=market.get("activation_status"),
                source_class=market.get("market_activation_class"),
                rows=market.get("candidate_rows"),
                ratio=_fmt(ratio, 3) if isinstance(ratio, float) else ratio,
            )
        )
    return "\n".join(rows)


def _commands_block(commands: list[str]) -> str:
    return "\n".join(f"- `{command}`" for command in commands)


def _overlay_yaml(
    *,
    generated_at: str,
    config: dict[str, Any],
    stage05: dict[str, Any],
    stage06: dict[str, Any],
    stage08: dict[str, Any],
    stage09: dict[str, Any],
    stage10: dict[str, Any],
    moonshot_runtime: dict[str, Any],
    moonshot_branch: dict[str, Any],
    condition_map: dict[str, Any],
) -> dict[str, Any]:
    runtime_cfg = config["gtos_vnext_runtime"]
    negative_projection = _scenario_metrics(stage06, "activated_default_source_bound_primary")
    be_metrics = _scenario_metrics(stage06, "moonshot_be_after_trigger")
    old_metrics = _scenario_metrics(stage06, "old_gtos_live_current_j46_j49")
    best_stream = moonshot_branch["best_overall_reference_fee599_payout8000"]
    selected_candidate = moonshot_runtime["selected_default_off_production_candidate"]
    prop_terminal = condition_map["prop_aware_terminal_decision"]

    base_flags = {
        "enabled": runtime_cfg.get("enabled"),
        "mode": runtime_cfg.get("mode"),
        "apply_to_execution": runtime_cfg.get("apply_to_execution"),
        "pre_ai_apply_to_ai_call": runtime_cfg.get("pre_ai_apply_to_ai_call"),
        "ai_policy_apply_to_ai_call": runtime_cfg.get("ai_policy_apply_to_ai_call"),
        "ai_policy_follow_no_ai_enabled": runtime_cfg.get("ai_policy_follow_no_ai_enabled"),
        "pending_policy_enabled": runtime_cfg.get("pending_policy_enabled"),
        "ltf_path_execution_apply_to_execution": runtime_cfg.get(
            "ltf_path_execution_apply_to_execution"
        ),
        "prop_safe_selector_apply_to_execution": runtime_cfg.get(
            "prop_safe_selector_apply_to_execution"
        ),
        "moonshot_dynamic_execution_router_enabled": runtime_cfg.get(
            "moonshot_dynamic_execution_router_enabled"
        ),
        "moonshot_dynamic_execution_router_apply_to_execution": runtime_cfg.get(
            "moonshot_dynamic_execution_router_apply_to_execution"
        ),
        "moonshot_dynamic_execution_router_policy": runtime_cfg.get(
            "moonshot_dynamic_execution_router_policy"
        ),
        "moonshot_dynamic_execution_router_condition_challenger_enabled": runtime_cfg.get(
            "moonshot_dynamic_execution_router_condition_challenger_enabled"
        ),
        "replacement_monitoring_enabled": runtime_cfg.get("replacement_monitoring_enabled"),
        "replacement_monitoring_log_enabled": runtime_cfg.get("replacement_monitoring_log_enabled"),
        "replacement_monitoring_log_path": runtime_cfg.get("replacement_monitoring_log_path"),
        "replacement_ml_apply_to_execution": runtime_cfg.get("replacement_ml_apply_to_execution"),
        "exit_management_residue_apply_to_execution": runtime_cfg.get(
            "exit_management_residue_apply_to_execution"
        ),
        "ready8_failure_control_residue_apply_to_execution": runtime_cfg.get(
            "ready8_failure_control_residue_apply_to_execution"
        ),
    }

    demo_shadow = {
        "gtos_vnext_runtime": {
            "enabled": True,
            "mode": "demo_shadow_vnext_replacement",
            "apply_to_execution": False,
            "pre_ai_apply_to_ai_call": False,
            "ai_policy_apply_to_ai_call": False,
            "ai_policy_follow_no_ai_enabled": False,
            "pending_policy_enabled": True,
            "ltf_path_execution_apply_to_execution": False,
            "prop_safe_selector_apply_to_execution": False,
            "moonshot_dynamic_execution_router_enabled": True,
            "moonshot_dynamic_execution_router_apply_to_execution": False,
            "moonshot_dynamic_execution_router_policy": "be_after_trigger",
            "moonshot_dynamic_execution_router_condition_challenger_enabled": False,
            "replacement_monitoring_enabled": True,
            "replacement_monitoring_log_enabled": True,
            "replacement_monitoring_log_path": MONITORING_LOG_PATH,
            "replacement_ml_apply_to_execution": False,
            "exit_management_residue_apply_to_execution": False,
            "ready8_failure_control_residue_apply_to_execution": False,
        }
    }
    production_candidate = {
        "gtos_vnext_runtime": {
            "enabled": True,
            "mode": "production_replacement_vnext_moonshot",
            "apply_to_execution": True,
            "pre_ai_apply_to_ai_call": True,
            "ai_policy_apply_to_ai_call": False,
            "ai_policy_follow_no_ai_enabled": True,
            "ai_policy_allow_mixed_ai_resolution": True,
            "pending_policy_enabled": True,
            "ltf_path_execution_apply_to_execution": True,
            "prop_safe_selector_apply_to_execution": True,
            "moonshot_dynamic_execution_router_enabled": True,
            "moonshot_dynamic_execution_router_apply_to_execution": True,
            "moonshot_dynamic_execution_router_policy": "be_after_trigger",
            "moonshot_dynamic_execution_router_condition_challenger_enabled": False,
            "moonshot_dynamic_execution_router_replaces_policy": "live_current_j46_j49",
            "replacement_monitoring_enabled": True,
            "replacement_monitoring_log_enabled": True,
            "replacement_monitoring_log_path": MONITORING_LOG_PATH,
            "replacement_ml_apply_to_execution": False,
            "risk_adjustment_enabled": True,
            "risk_zero_blocks_execution": True,
            "exit_management_residue_apply_to_execution": False,
            "ready8_failure_control_residue_apply_to_execution": False,
        }
    }
    rollback = {
        "gtos_vnext_runtime": {
            "enabled": True,
            "mode": "shadow",
            "apply_to_execution": False,
            "pre_ai_apply_to_ai_call": False,
            "ai_policy_apply_to_ai_call": False,
            "ai_policy_follow_no_ai_enabled": False,
            "pending_policy_enabled": True,
            "ltf_path_execution_apply_to_execution": False,
            "prop_safe_selector_apply_to_execution": False,
            "moonshot_dynamic_execution_router_enabled": False,
            "moonshot_dynamic_execution_router_apply_to_execution": False,
            "moonshot_dynamic_execution_router_policy": "be_after_trigger",
            "moonshot_dynamic_execution_router_condition_challenger_enabled": False,
            "replacement_monitoring_enabled": True,
            "replacement_monitoring_log_enabled": True,
            "replacement_monitoring_log_path": MONITORING_LOG_PATH,
            "replacement_ml_apply_to_execution": False,
            "exit_management_residue_apply_to_execution": False,
            "ready8_failure_control_residue_apply_to_execution": False,
        }
    }

    return {
        "route_id": ROUTE_ID,
        "stage_id": "stage_11_activation_dossier_and_config_overlay",
        "schema_version": "vnext_replacement_stage11_config_overlay_diff_v2",
        "generated_at_utc": generated_at,
        "repo_config_changed_by_stage11": False,
        "application_state": {
            "production_activation_overlay_applied_now": False,
            "required_gate_before_application": "stage_12_final_semantic_verifier_status_passed",
            "reason": (
                "Stage11 writes exact overlays only. The current default source-bound primary "
                "projection is negative and must block application unless Stage12 verifies a "
                "repaired production overlay behavior."
            ),
            "external_surfaces_not_used": [
                "live_trading",
                "broker_account_order_deal_position_history_mutation",
                "paid_api_or_vendor_model_calls",
                "credential_changes",
                "remote_push",
                "destructive_source_deletion",
                "history_rewrite",
            ],
        },
        "input_guardrails": {
            "candidate_rows": int(stage05["coverage"]["candidate_rows"]),
            "dynamic_policy_replay_rows": int(stage05["coverage"]["dynamic_policy_replay_rows"]),
            "old_gtos_live_current_j46_j49_expectancy_r": float(old_metrics["expectancy_r"]),
            "moonshot_be_after_trigger_expectancy_r": float(be_metrics["expectancy_r"]),
            "activated_default_source_bound_primary_expectancy_r": float(
                negative_projection["expectancy_r"]
            ),
            "activated_default_source_bound_primary_total_r": float(negative_projection["total_r"]),
            "activated_default_source_bound_primary_selected_count": int(
                negative_projection["selected_count"]
            ),
            "activated_default_source_bound_primary_blocks_production_overlay": True,
            "stage05_warnings": stage05.get("verifier_warnings")
            or ["activated_source_bound_primary_rows_have_nonpositive_expectancy_stage12_must_not_apply_overlay"],
            "stage09_paid_calls_made": int(
                stage09["ai_call_execution_state"]["paid_api_or_vendor_calls_made"]
            ),
            "stage09_route_state_budget_cap_usd": stage09["ai_call_execution_state"].get(
                "route_state_budget_cap_usd"
            ),
        },
        "selected_replacement": {
            "candidate_name": selected_candidate["candidate_name"],
            "primary_framework": selected_candidate["primary_framework"],
            "primary_branch": selected_candidate["primary_branch"],
            "dynamic_execution_policy": selected_candidate["default_policy"],
            "replaces": selected_candidate["replaces"],
            "prop_policy_reference": selected_candidate["prop_policy_reference"],
            "prop_default_retained_over_condition_challenger": bool(
                prop_terminal["prop_default_retained"]
            ),
            "condition_challenger_status": prop_terminal["terminal_classification"],
            "best_stream_allowed_trades": int(best_stream["allowed_trades"]),
            "best_stream_expectancy_r": float(best_stream["expectancy_r"]),
            "best_stream_total_r": float(best_stream["total_r"]),
            "best_stream_expected_payout_proxy_usd_fee599_payout8000": float(
                best_stream["expected_payout_proxy_usd_fee599_payout8000"]
            ),
            "best_stream_pass_probability_proxy": float(best_stream["pass_probability_proxy"]),
        },
        "current_shadow_base": {
            "config_path": "config/agent_config.yaml",
            "gtos_vnext_runtime": base_flags,
            "deployment_phase_change": "none",
        },
        "demo_shadow_overlay": {
            "allowed_without_broker_or_account_mutation": True,
            "purpose": "Log replacement decisions, dynamic policy, source completeness, and monitoring surfaces without changing orders.",
            "config": demo_shadow,
        },
        "semantic_gated_production_activation_overlay_candidate": {
            "application_gate": "Apply only after Stage12 semantic verifier passes overlay behavioral diff and rollback proof.",
            "must_fail_if": [
                "activated_default_source_bound_primary_expectancy_r_below_zero",
                "old_gtos_live_current_j46_j49_controls_dynamic_exit_when_overlay_enabled",
                "source_missing_or_same_bar_ambiguous_rows_receive_execution_effect",
                "prop_safe_selector_apply_to_execution_false",
                "ltf_path_execution_apply_to_execution_false",
                "monitoring_log_absent_or_missing_required_surfaces",
                "ml_apply_to_execution_true_without_sealed_validation",
            ],
            "deployment_phase_change": "none_in_this_route_without_owner_account_runtime_start_approval",
            "config": production_candidate,
        },
        "rollback_overlay": {
            "purpose": "Restore current shadow/default-off execution behavior while retaining monitoring.",
            "config": rollback,
        },
        "market_activation_phase_rules": {
            "broker_native_live_feed_symbols": stage08["broker_live_deployment_symbols"],
            "broker_native_activation_eligible_symbols": stage08.get(
                "broker_native_activation_eligible_symbols", stage08["broker_live_deployment_symbols"]
            ),
            "broker_native_symbols_initial_phase": "demo_shadow_or_paper_capture_only_until_stage12_and_owner_runtime_handoff",
            "broker_contract_verification_pending_not_excluded_symbols": stage08.get(
                "broker_native_pending_not_excluded_symbols", []
            ),
            "broker_exact_excluded_symbols": stage08.get("broker_native_exact_excluded_symbols", []),
            "excluded_until_broker_source_exists_count": int(
                stage08["activation_status_counts"].get("excluded_until_broker_source_exists", 0)
            ),
            "legacy_live_deployment_symbols_not_activation_ceiling": stage08.get(
                "legacy_live_deployment_symbols_not_activation_ceiling", []
            ),
            "proxy_context_excluded_count": int(
                stage08["activation_status_counts"].get("proxy_context_excluded_from_broker_execution", 0)
            ),
            "forward_capture_requirement_rows": int(stage08["capture_requirement_rows"]),
            "market_source_invariant": (
                "Do not cap activation to the stale legacy deployment list. Historical-only, "
                "source-missing, and Sierra-delayed context are not proof redacted_account lacks a market; "
                "broker-native MT5/redacted_account contract verification decides eligibility."
            ),
        },
        "monitoring": {
            "log_path": MONITORING_LOG_PATH,
            "surface_count": len(stage10["monitoring_surfaces"]),
            "surfaces": [row["surface"] for row in stage10["monitoring_surfaces"]],
            "ml_apply_to_execution": False,
        },
    }


def _build_dossier(
    *,
    generated_at: str,
    overlay: dict[str, Any],
    stage06: dict[str, Any],
    stage08: dict[str, Any],
    stage10: dict[str, Any],
    moonshot_runtime: dict[str, Any],
    condition_map: dict[str, Any],
) -> str:
    selected = overlay["selected_replacement"]
    old = _scenario_metrics(stage06, "old_gtos_live_current_j46_j49")
    be = _scenario_metrics(stage06, "moonshot_be_after_trigger")
    condition = _scenario_metrics(stage06, "condition_router_challenger")
    negative = _scenario_metrics(stage06, "activated_default_source_bound_primary")
    prop_terminal = condition_map["prop_aware_terminal_decision"]
    commands = [
        "python -m py_compile src\\components\\gtos_vnext_runtime.py src\\components\\orchestrator.py src\\components\\execution.py tests\\test_gtos_vnext_runtime.py tests\\test_j46_j49_policy.py tests\\test_limit_order_flow.py",
        "python -m pytest tests\\test_gtos_vnext_runtime.py::test_vnext_replacement_monitoring_snapshot_records_stage10_surfaces tests\\test_gtos_vnext_runtime.py::test_vnext_replacement_monitoring_flags_old_live_fallback_leakage tests\\test_gtos_vnext_runtime.py::test_agent_config_wires_vnext_runtime_shadow_execution_path -q",
        "python research\\science_program_2026_05\\06_outcome_testing\\vnext_moonshot_production_replacement_activation_2026_05_26\\verify_vnext_replacement_stage05_full_activated_replay.py",
        "python research\\science_program_2026_05\\06_outcome_testing\\vnext_moonshot_production_replacement_activation_2026_05_26\\verify_vnext_replacement_stage06_legacy_vs_vnext_delta.py",
        "python research\\science_program_2026_05\\06_outcome_testing\\vnext_moonshot_production_replacement_activation_2026_05_26\\verify_vnext_replacement_stage10_ml_monitoring_integration.py",
        "python research\\science_program_2026_05\\06_outcome_testing\\vnext_moonshot_production_replacement_activation_2026_05_26\\verify_vnext_replacement_stage11_activation_dossier.py",
        "python research\\science_program_2026_05\\06_outcome_testing\\vnext_moonshot_production_replacement_activation_2026_05_26\\verify_vnext_replacement_stage12_semantic_red_team.py",
    ]
    surfaces = ", ".join(row["surface"] for row in stage10["monitoring_surfaces"])
    return f"""# vNext Replacement Production Activation Dossier - {DATE}

Generated: `{generated_at}`

## Activation Verdict At Stage 11

Stage 11 does not apply the production overlay. It writes the exact demo-shadow overlay, the semantic-gated production overlay candidate, the rollback overlay, and the monitoring/operation package. Application is blocked until Stage 12 passes the semantic verifier and proves that the production overlay changes behavior without reactivating the negative current default source-bound primary slice.

The blocking fixture is explicit: `activated_default_source_bound_primary` has expectancy `{_fmt(float(negative["expectancy_r"]))}R`, total `{_fmt(float(negative["total_r"]))}R`, and selected `{negative["selected_count"]}` rows. That overlay must not be applied as production truth.

## What Replaces Old GTOS

- Old exit behavior replaced: `{selected["replaces"]}` and fixed `1.5R` comparator behavior stop being the target production exit path when the gated overlay is applied.
- vNext replacement behavior: `{selected["candidate_name"]}` using `{selected["dynamic_execution_policy"]}` on the source-bound `{selected["primary_branch"]}` / `{selected["primary_framework"]}` stream.
- Prop behavior: `{selected["prop_policy_reference"]}` remains the default prop policy reference. It allows when cushions are sufficient, reduces or defers near daily/overall limits, and treats abandon/restart as an owner-gated account-attempt decision rather than an automatic broker action.
- AI behavior: mechanical routing is primary. The Stage09 AI package remains budget-capped and unspent; AI-dependent surfaces stay disabled until a route-state budget cap exists.
- ML behavior: Stage10 ML roles are monitoring only. `replacement_ml_apply_to_execution` must remain false.

## Evidence Metrics

| Scenario | Selected/performance rows | Total R | Expectancy R | Win rate | Profit factor |
|---|---:|---:|---:|---:|---:|
| Old GTOS live-current J46/J49 | {old["selected_count"]} | {_fmt(float(old["total_r"]))} | {_fmt(float(old["expectancy_r"]))} | {_fmt(float(old["win_rate"]))} | {_fmt(float(old["profit_factor"]))} |
| Moonshot BE-after-trigger | {be["selected_count"]} | {_fmt(float(be["total_r"]))} | {_fmt(float(be["expectancy_r"]))} | {_fmt(float(be["win_rate"]))} | {_fmt(float(be["profit_factor"]))} |
| Condition-router challenger | {condition["selected_count"]} | {_fmt(float(condition["total_r"]))} | {_fmt(float(condition["expectancy_r"]))} | {_fmt(float(condition["win_rate"]))} | {_fmt(float(condition["profit_factor"]))} |
| Blocked current default source-bound primary | {negative["selected_count"]} | {_fmt(float(negative["total_r"]))} | {_fmt(float(negative["expectancy_r"]))} | {_fmt(float(negative["win_rate"]))} | {_fmt(float(negative["profit_factor"]))} |

Upstream best stream: `{selected["primary_branch"]}` with `{selected["dynamic_execution_policy"]}` and `{selected["prop_policy_reference"]}` allowed `{selected["best_stream_allowed_trades"]}` trades, total `{_fmt(selected["best_stream_total_r"])}`R, expectancy `{_fmt(selected["best_stream_expectancy_r"])}`R, pass-proxy `{_fmt(selected["best_stream_pass_probability_proxy"])}`, and expected payout proxy `${_fmt(selected["best_stream_expected_payout_proxy_usd_fee599_payout8000"], 3)}`.

Condition challenger status: `{prop_terminal["terminal_classification"]}`. It improves row expectancy, but Stage11 keeps BE-after-trigger as the prop-pass default because the prop replay retained better pass efficiency and accepted-trade count.

## Config Overlays

- Current shadow base: `gtos_vnext_runtime.apply_to_execution=false`, dynamic router disabled, LTF/prop execution-effect flags disabled, monitoring enabled.
- Demo shadow overlay: enables the moonshot dynamic router for logging while keeping global and dynamic `apply_to_execution=false`.
- Semantic-gated production overlay candidate: enables global vNext apply, pre-AI mechanical apply, LTF execution apply, prop selector apply, and moonshot dynamic execution apply, while keeping paid-AI execution and ML execution disabled.
- Rollback overlay: restores current shadow/default-off execution flags while retaining monitoring.

Exact YAML: `{OUTPUT_OVERLAY.name}`.

## Market And Source Activation

{_market_table(stage08["markets"])}

Broker-native eligible symbols are `{", ".join(stage08["broker_live_deployment_symbols"]) or "-"}` from the route onboarding verifier, not from the stale legacy deployment list. Pending-not-excluded replay symbols are `{", ".join(stage08.get("broker_native_pending_not_excluded_symbols", [])) or "-"}`. Exact broker exclusions are `{", ".join(stage08.get("broker_native_exact_excluded_symbols", [])) or "-"}`. Historical-only, source-missing, and Sierra/SCID context do not prove redacted_account lacks a market; Sierra remains context-only and broker-native MT5 availability decides live eligibility.

## Monitoring And Stop Rules

Monitoring log: `{MONITORING_LOG_PATH}`.

Required monitoring surfaces: {surfaces}.

Immediate block or rollback conditions:

- Stage12 semantic verifier does not pass.
- Any applied execution row has `old_live_fallback_leakage.detected=true`.
- Any applied execution row has missing source, incomplete source window, or same-bar ambiguity without ordered LTF/tick proof.
- Dynamic overlay applies while selected policy is not `be_after_trigger` or replacement target is not `live_current_j46_j49`.
- `replacement_ml_apply_to_execution=true`.
- Paid AI is invoked while route-state budget cap remains null.
- Prop projection emits `ACCOUNT_ABANDON_OR_RESTART` without owner account-attempt approval.
- Any emergency stop in `.context/00_core/quick_reference_card.md` fires.

## Commands

{_commands_block(commands)}

## External Surface Handoff Fields

- Paid AI spend: blocked until `route_state_budget_cap_usd` is non-null; Stage09 package has 32 prompt rows and hard-cap request only.
- Broker/account/order/deal/position/history mutation: out of route. Owner must provide demo/live account, server, broker symbol aliases, start window, risk ceiling, and explicit runtime-start/order-mutation approval.
- Remote push: out of route and requires explicit owner approval.
- Credential changes: out of route.
- Destructive deletion and history rewrite: out of route.
"""


def _build_rollback(overlay: dict[str, Any]) -> str:
    rollback_yaml = yaml.safe_dump(
        overlay["rollback_overlay"]["config"], sort_keys=True, allow_unicode=False
    ).rstrip()
    return f"""# vNext Replacement Rollback Runbook - {DATE}

## Purpose

Restore the current GTOS shadow/default-off behavior if Stage12 fails, monitoring detects leakage, or the owner stops the demo/prod activation sequence.

## Rollback Overlay

```yaml
{rollback_yaml}
```

## Required Checks

- Confirm `gtos_vnext_runtime.apply_to_execution=false`.
- Confirm `moonshot_dynamic_execution_router_apply_to_execution=false`.
- Confirm `moonshot_dynamic_execution_router_enabled=false`.
- Confirm `ltf_path_execution_apply_to_execution=false`.
- Confirm `prop_safe_selector_apply_to_execution=false`.
- Confirm `replacement_ml_apply_to_execution=false`.
- Confirm monitoring remains enabled at `{MONITORING_LOG_PATH}`.

## Verification Commands

- `python -m py_compile src\\components\\gtos_vnext_runtime.py src\\components\\orchestrator.py src\\components\\execution.py`
- `python -m pytest tests\\test_gtos_vnext_runtime.py::test_agent_config_wires_vnext_runtime_shadow_execution_path -q`
- `python research\\science_program_2026_05\\06_outcome_testing\\vnext_moonshot_production_replacement_activation_2026_05_26\\verify_vnext_replacement_stage11_activation_dossier.py`

## Stop Conditions

Do not restart an account-connected runtime from this runbook. Broker/account/order/deal/position/history mutation is an owner external surface. If a live/demo process exists outside this route, stop it first through the owner-approved operator path, then apply this config overlay and rerun the verification commands.
"""


def _build_demo(overlay: dict[str, Any], stage08: dict[str, Any]) -> str:
    demo_yaml = yaml.safe_dump(
        overlay["demo_shadow_overlay"]["config"], sort_keys=True, allow_unicode=False
    ).rstrip()
    live_symbols = ", ".join(stage08["broker_live_deployment_symbols"]) or "-"
    pending_symbols = ", ".join(stage08.get("broker_native_pending_not_excluded_symbols", [])) or "-"
    return f"""# vNext Replacement Demo/Shadow Activation Runbook - {DATE}

## Scope

This is repo-local and demo-shadow only. It does not start `run_agent.py`, connect to an account, mutate broker state, place orders, modify orders, close positions, or read account/deal/history state.

## Demo Shadow Overlay

```yaml
{demo_yaml}
```

## Activation Sequence

1. Apply only the demo-shadow overlay from `{OUTPUT_OVERLAY.name}`.
2. Run the Stage05, Stage06, Stage10, and Stage11 verifiers.
3. Run the focused monitoring tests.
4. Inspect `{MONITORING_LOG_PATH}` for the required snapshot fields after a safe shadow/demo runtime has been started by an owner-approved external handoff.
5. Keep all broker-verified eligible symbols in capture/monitoring mode: {live_symbols}.
6. Do not treat pending replay markets as unavailable. Pending broker-contract verification symbols are: {pending_symbols}.

## Commands

- `python research\\science_program_2026_05\\06_outcome_testing\\vnext_moonshot_production_replacement_activation_2026_05_26\\verify_vnext_replacement_stage05_full_activated_replay.py`
- `python research\\science_program_2026_05\\06_outcome_testing\\vnext_moonshot_production_replacement_activation_2026_05_26\\verify_vnext_replacement_stage06_legacy_vs_vnext_delta.py`
- `python research\\science_program_2026_05\\06_outcome_testing\\vnext_moonshot_production_replacement_activation_2026_05_26\\verify_vnext_replacement_stage10_ml_monitoring_integration.py`
- `python research\\science_program_2026_05\\06_outcome_testing\\vnext_moonshot_production_replacement_activation_2026_05_26\\verify_vnext_replacement_stage11_activation_dossier.py`
- `python -m pytest tests\\test_gtos_vnext_runtime.py::test_vnext_replacement_monitoring_snapshot_records_stage10_surfaces tests\\test_gtos_vnext_runtime.py::test_vnext_replacement_monitoring_flags_old_live_fallback_leakage -q`

## External Handoff Required Before Runtime Startup

Owner must provide explicit permission and account details before any account-connected runtime process starts. Required fields: account type, account id, broker server, symbol alias map, allowed symbols, max risk, start/stop time, rollback operator, and confirmation that order/deal/position/history mutation is allowed for the selected demo/live surface.
"""


def _build_monitoring(stage10: dict[str, Any]) -> str:
    rows = [
        "| Surface | Snapshot field | Runtime effect | Rollback trigger |",
        "|---|---|---|---|",
    ]
    trigger_by_surface = {
        "vnext_apply_status": "global apply false when production overlay expected, or true before Stage12 pass",
        "router_decisions": "dynamic router absent or selected policy not be_after_trigger on applied rows",
        "label_effects": "AVOID/MIXED/LEGACY still inert when contract says execution effect",
        "avoid_mixed_legacy_distribution_and_execution_effect": "old-live behavior dominates without explicit rollback reason",
        "dynamic_exit_transitions": "J46/J49 remains active on applied replacement rows",
        "ltf_pending_monitor_health": "same-bar or path-ambiguous rows receive execution effect",
        "prop_budget_projection": "prop defer/reduce/abandon action ignored or auto-abandon attempted",
        "source_capture_completeness": "source missing, source window incomplete, or join id missing on applied rows",
        "old_live_fallback_leakage": "any detected leakage",
        "malformed_ai_responses": "AI schema/malformed rows affect execution or budget cap is absent",
    }
    for row in stage10["monitoring_surfaces"]:
        surface = row["surface"]
        rows.append(
            f"| {surface} | {row['schema_field']} | {row['runtime_effect']} | "
            f"{trigger_by_surface.get(surface, 'manual review')} |"
        )
    return f"""# vNext Replacement Monitoring Checklist - {DATE}

Monitoring log path: `{MONITORING_LOG_PATH}`

## Required Surfaces

{chr(10).join(rows)}

## Minimum Snapshot Fields

`schema_version`, `phase`, `symbol`, `kill_zone`, `candle_time_utc`, `vnext_apply_status`, `router_decision`, `label_effects`, `execution_effects`, `dynamic_exit_transition`, `ltf_pending_monitor_health`, `prop_budget_projection`, `source_capture_completeness`, `old_live_fallback_leakage`, `ai_malformed_monitoring`, `ml_assistant_roles`, `warnings`.

## Pass Criteria

- Every candidate/block path writes a replacement monitoring snapshot.
- Production overlay never applies before Stage12 pass.
- Applied replacement rows show dynamic exit replacement, source completeness, LTF/pending health, prop projection, and old-live leakage status.
- ML roles remain `monitor_only` with `replacement_ml_apply_to_execution=false`.
- Paid AI remains uncalled until a non-null route-state budget cap exists.

## Rollback Criteria

- Any `old_live_fallback_leakage` detected.
- Any applied row has source missing, incomplete source window, or same-bar ambiguity without ordered proof.
- Any monitoring snapshot omits a required field.
- Any AI malformed-response state affects execution.
- Any prop account abandon/restart action occurs without explicit owner handoff.
"""


def main() -> int:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    stage03 = _read_json(STAGE03_CONTRACT)
    stage05 = _read_json(STAGE05_SUMMARY)
    stage05_verifier = _read_json(STAGE05_VERIFIER)
    stage06 = _read_json(STAGE06_VERIFIER)
    stage08 = _read_json(STAGE08_MAP)
    stage09 = _read_json(STAGE09_AI_MANIFEST)
    stage10 = _read_json(STAGE10_MAP)
    moonshot_runtime = _read_json(MOONSHOT_RUNTIME_MAP)
    moonshot_branch = _read_json(MOONSHOT_BRANCH_SUMMARY)
    condition_map = _read_json(MOONSHOT_CONDITION_MAP)
    state = _read_json(STATE_PATH)
    manifest = _read_json(MANIFEST_PATH)
    previous_current_stage = state.get("current_stage")
    previous_first_incomplete = state.get("first_incomplete_invariant")
    previous_exact_next_action = state.get("exact_next_action")
    previous_overlay_state = dict(state.get("config_overlay_state", {}))

    overlay = _overlay_yaml(
        generated_at=generated_at,
        config=config,
        stage05=stage05,
        stage06=stage06,
        stage08=stage08,
        stage09=stage09,
        stage10=stage10,
        moonshot_runtime=moonshot_runtime,
        moonshot_branch=moonshot_branch,
        condition_map=condition_map,
    )
    overlay["input_artifacts"] = {
        "stage03_contract": {"path": _rel(STAGE03_CONTRACT), "sha256": _sha256(STAGE03_CONTRACT)},
        "stage05_summary": {"path": _rel(STAGE05_SUMMARY), "sha256": _sha256(STAGE05_SUMMARY)},
        "stage05_verifier": {"path": _rel(STAGE05_VERIFIER), "sha256": _sha256(STAGE05_VERIFIER)},
        "stage06_verifier": {"path": _rel(STAGE06_VERIFIER), "sha256": _sha256(STAGE06_VERIFIER)},
        "stage08_market_map": {"path": _rel(STAGE08_MAP), "sha256": _sha256(STAGE08_MAP)},
        "stage09_ai_manifest": {"path": _rel(STAGE09_AI_MANIFEST), "sha256": _sha256(STAGE09_AI_MANIFEST)},
        "stage10_monitoring_map": {"path": _rel(STAGE10_MAP), "sha256": _sha256(STAGE10_MAP)},
        "moonshot_runtime_map": {"path": _rel(MOONSHOT_RUNTIME_MAP), "sha256": _sha256(MOONSHOT_RUNTIME_MAP)},
        "moonshot_branch_summary": {
            "path": _rel(MOONSHOT_BRANCH_SUMMARY),
            "sha256": _sha256(MOONSHOT_BRANCH_SUMMARY),
        },
        "moonshot_condition_map": {
            "path": _rel(MOONSHOT_CONDITION_MAP),
            "sha256": _sha256(MOONSHOT_CONDITION_MAP),
        },
    }

    _write_text(
        OUTPUT_OVERLAY,
        yaml.safe_dump(overlay, sort_keys=False, allow_unicode=False, width=100),
    )
    _write_text(
        OUTPUT_DOSSIER,
        _build_dossier(
            generated_at=generated_at,
            overlay=overlay,
            stage06=stage06,
            stage08=stage08,
            stage10=stage10,
            moonshot_runtime=moonshot_runtime,
            condition_map=condition_map,
        ),
    )
    _write_text(OUTPUT_ROLLBACK, _build_rollback(overlay))
    _write_text(OUTPUT_DEMO, _build_demo(overlay, stage08))
    _write_text(OUTPUT_MONITORING, _build_monitoring(stage10))

    stage11_outputs = [
        OUTPUT_DOSSIER,
        OUTPUT_OVERLAY,
        OUTPUT_ROLLBACK,
        OUTPUT_DEMO,
        OUTPUT_MONITORING,
    ]
    for output in stage11_outputs:
        _upsert_manifest_output(
            manifest,
            {
                "path": output.name,
                "stage": "stage_11",
                "status": "created",
                "sha256": _sha256(output),
            },
        )
    _upsert_manifest_output(
        manifest,
        {
            "path": Path(__file__).name,
            "stage": "stage_11",
            "status": "created_and_ready_for_py_compile",
        },
    )
    manifest["last_updated_utc"] = generated_at
    _write_json(MANIFEST_PATH, manifest)

    evidence = state.setdefault("evidence_rows_scanned", {})
    evidence["stage11_activation_docs_written"] = len(stage11_outputs)
    evidence["stage11_overlay_sections"] = 5
    evidence["stage11_live_broker_symbols"] = len(stage08["broker_live_deployment_symbols"])
    evidence["stage11_broker_pending_not_excluded_symbols"] = len(
        stage08.get("broker_native_pending_not_excluded_symbols", [])
    )
    evidence["stage11_broker_exact_excluded_symbols"] = len(
        stage08.get("broker_native_exact_excluded_symbols", [])
    )
    evidence["stage11_market_rows_consumed"] = len(stage08["markets"])
    evidence["stage11_activation_exclusion_rows_consumed"] = int(stage08["exclusion_rows"])
    evidence["stage11_monitoring_surfaces_consumed"] = len(stage10["monitoring_surfaces"])
    evidence["stage11_ai_prompt_rows_consumed"] = int(
        stage09["prompt_pack"]["packet_rows"]
    )
    evidence["stage11_stage05_verifier_warnings_consumed"] = len(
        stage05_verifier.get("warnings", [])
    )
    if previous_first_incomplete == "stage_12_semantic_verification_and_red_team_pending" or previous_current_stage in {
        "stage_11_activation_dossier_and_config_overlay",
        "stage_12_semantic_verification_and_red_team",
    }:
        state["current_stage"] = "stage_12_semantic_verification_and_red_team"
        state["first_incomplete_invariant"] = "stage_12_semantic_verification_and_red_team_pending"
        state["exact_next_action"] = (
            "Run Stage12 semantic verification and self-red-team, including activation-overlay "
            "behavioral diff and the negative default-source-bound-primary guard."
        )
    else:
        state["current_stage"] = previous_current_stage
        state["first_incomplete_invariant"] = previous_first_incomplete
        state["exact_next_action"] = previous_exact_next_action
    state.setdefault("stage_status", {})[
        "stage_11_activation_dossier_and_config_overlay"
    ] = "completed_activation_package_written_overlay_not_applied_pending_semantic_verifier"
    state.setdefault("stage_status", {})[
        "stage_12_semantic_verification_and_red_team"
    ] = "pending"
    if previous_overlay_state.get("semantic_gate_state") == "failed_stage12_semantic_verifier":
        state["config_overlay_state"] = {
            **previous_overlay_state,
            "overlay_path": _rel(OUTPUT_OVERLAY),
            "rollback_path": _rel(OUTPUT_ROLLBACK),
            "production_activation_overlay_applied": False,
        }
    else:
        state["config_overlay_state"] = {
            "production_activation_overlay_applied": False,
            "semantic_gate_state": "pending_stage12_semantic_verifier",
            "reason": (
                "Stage11 wrote the overlay diff but did not apply it. Stage05/06 negative "
                "default source-bound primary projection must block production application unless "
                "Stage12 verifies repaired behavior."
            ),
            "overlay_path": _rel(OUTPUT_OVERLAY),
            "rollback_path": _rel(OUTPUT_ROLLBACK),
            "observed_base_flags": previous_overlay_state.get("observed_base_flags", {}),
        }
    _append_test_result(
        state,
        _rel(Path(__file__)),
        "passed; wrote Stage11 activation dossier, overlay diff, rollback, demo-shadow runbook, and monitoring checklist",
        generated_at,
    )
    state["last_updated_utc"] = generated_at
    _write_json(STATE_PATH, state)

    _append_control(
        {
            "event": "stage_11_activation_dossier_completed",
            "generated_at_utc": generated_at,
            "production_activation_overlay_applied": False,
            "negative_default_overlay_expectancy_r": overlay["input_guardrails"][
                "activated_default_source_bound_primary_expectancy_r"
            ],
            "broker_exact_excluded_symbols": stage08.get("broker_native_exact_excluded_symbols", []),
            "broker_pending_not_excluded_symbols": stage08.get("broker_native_pending_not_excluded_symbols", []),
            "broker_verified_symbols": stage08["broker_live_deployment_symbols"],
            "route_id": ROUTE_ID,
            "stage_id": "stage_11_activation_dossier_and_config_overlay",
            "outputs": [output.name for output in stage11_outputs],
        }
    )

    print(
        json.dumps(
            {
                "docs": len(stage11_outputs),
                "next": state["first_incomplete_invariant"],
                "production_overlay_applied": False,
                "stage": "stage_11_activation_dossier_and_config_overlay",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
