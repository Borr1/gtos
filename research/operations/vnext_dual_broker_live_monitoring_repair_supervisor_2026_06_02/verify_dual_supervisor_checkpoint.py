#!/usr/bin/env python3
"""Verify and checkpoint the dual-broker live supervisor route."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROUTE_ID = "vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]

REQUIRED_ARTIFACTS = [
    "DUAL_MEMORY_CONSCIOUS_ACTIVATION_PLAN.md",
    "probe_dual_mt5_readonly.py",
    "DUAL_SUPERVISOR_CONTEXT_ANCHOR.md",
    "DUAL_SUPERVISOR_STATE.json",
    "DUAL_SUPERVISOR_WORK_QUEUE.jsonl",
    "DUAL_SUPERVISOR_ACTION_LEDGER.jsonl",
    "DUAL_GIT_VERSION_AUDIT.json",
    "DUAL_SOURCE_INVENTORY_LEDGER.jsonl",
    "DUAL_REQUIRED_FILE_LEDGER.jsonl",
    "DUAL_ENVIRONMENT_LEDGER.jsonl",
    "DUAL_ACCOUNT_PROFILE_LEDGER.jsonl",
    "DUAL_MT5_TERMINAL_ACCOUNT_PROBE.json",
    "DUAL_MT5_SYMBOL_SPEC_LEDGER.jsonl",
    "DUAL_NAMESPACE_ISOLATION_LEDGER.jsonl",
    "DUAL_PROCESS_HEALTH_LEDGER.jsonl",
    "DUAL_WATCHDOG_SCHEDULER_LEDGER.jsonl",
    "DUAL_DATA_CAPTURE_HEALTH_LEDGER.jsonl",
    "DUAL_RUNTIME_DECISION_LEDGER.jsonl",
    "DUAL_CANDIDATE_PACKET_LEDGER.jsonl",
    "DUAL_CANDIDATE_AGENT_INSPECTION_LEDGER.jsonl",
    "DUAL_NO_CANDIDATE_PROOF_LEDGER.jsonl",
    "DUAL_OPEN_TRADE_LIFECYCLE_LEDGER.jsonl",
    "DUAL_TRADE_AGENT_INSPECTION_LEDGER.jsonl",
    "DUAL_BROKER_RECONCILIATION_LEDGER.jsonl",
    "DUAL_RISK_EXPOSURE_LEDGER.jsonl",
    "DUAL_V3_RUNTIME_DISPOSITION_LEDGER.jsonl",
    "DUAL_NOTIFICATION_LEDGER.jsonl",
    "DUAL_ANOMALY_LEDGER.jsonl",
    "DUAL_REPAIR_LEDGER.jsonl",
    "DUAL_RESTART_RELOAD_LEDGER.jsonl",
    "DUAL_SUPERVISOR_CHECKPOINTS.jsonl",
    "DUAL_VERIFICATION_RESULT.json",
    "DUAL_OUTPUT_MANIFEST.json",
    "DUAL_COMPLETION_OR_CONTINUATION_AUDIT.json",
]

CODE_SUBSTRINGS = {
    "start_all.bat": [
        "GTOS_NOTIFICATION_QUEUE_PATH=pipeline_state\\redacted_account_live_bee34003\\notification_queue.jsonl",
        "GTOS_RUNTIME_ROLE=primary_full",
        "secondary_execution_follower",
        "scripts\\dual_broker_execution_follower.py",
        "--worker --queue-path",
        "--runtime-namespace %GTOS_RUNTIME_NAMESPACE%",
        ".notification_queue_worker_%GTOS_RUNTIME_NAMESPACE%.lock",
    ],
    "scripts/watchdog.ps1": [
        'GTOS_RUNTIME_ROLE = "primary_full"',
        "Invoke-SecondaryExecutionFollowerRole",
        "dual_broker_execution_follower.py",
        "Skipping run_agent fleet, tick_capture fleet, m1_capture",
        "dual-broker bridge/follower active",
        "suppressing widening maintenance",
        "function Get-FreePhysicalMemoryPct",
        "$minFreeMemoryPct = 25.0",
        "maintenance/follow process already running",
        "preserving live trading footprint",
        "$NotificationQueuePath = $env:GTOS_NOTIFICATION_QUEUE_PATH",
        "$NotificationQueueLockName",
        "--queue-path \"\"${NotificationQueuePath}\"\"",
        "--runtime-namespace ${RuntimeNamespace}",
        ".notification_queue_worker_${RuntimeNamespace}.lock",
        "Invoke-DualBrokerTradeRecordProjectorBridge",
        "Invoke-DualBrokerExecutionFollowerBridge",
        ".dual_broker_trade_record_projector_${sourceNamespace}.lock",
        ".dual_broker_execution_follower_${targetNamespace}.lock",
        "$orderEnabled = $true",
        "DUAL_FOLLOWER_PRIMARY_BRIDGE",
        "Invoke-DualBrokerTradeRecordProjectorBridge | Out-Null",
    ],
    "src/utils/notification_queue.py": [
        "def _effective_default_queue_path()",
        "GTOS_NOTIFICATION_QUEUE_PATH",
        "def _worker_lock_path",
        "runtime_namespace",
    ],
    "src/components/orchestrator.py": [
        "configure_from_config as _configure_notification_queue",
        "_configure_notification_queue(config)",
        "DUAL_BROKER_MARKET_ENTRY",
        "DUAL_BROKER_PENDING_LIMIT",
        "_emit_dual_broker_intent",
    ],
    "src/components/dual_broker_intent_bus.py": [
        "DEFAULT_INTENT_LOG_PATH",
        "canonical_intent_id",
        "append_intent",
        "read_intents_from_offset",
        "_extract_vnext_projection_context",
        "vnext_projection_context_errors",
        "gtos_vnext_selected_cell_risk_selected_policy",
        "gtos_vnext_commission_model_status",
        "gtos_vnext_dynamic_partial_close_ratio",
        "_record_has_terminal_exit",
        "_execution_is_filled_entry_source",
        "_pending_is_open_entry_source",
        "repair/replay cannot duplicate the same source trade",
        "_source_lifecycle_key",
        "target_account_recompute_from_profile_and_current_broker_geometry",
    ],
    "scripts/dual_broker_execution_follower.py": [
        "class FollowerRuntime",
        "--order-enabled",
        "--replay-existing",
        "--portable-terminal",
        "resolve_mt5_portable_mode",
        "terminal_portable",
        "dry_run_intent_ready",
        "dual_broker_execution_follower_",
        "GTOS_NOTIFICATION_QUEUE_DISABLED",
        "target_tick_quality",
        "market_intent_deferred_target_tick_unavailable",
        "market_intent_expired_target_tick_unavailable",
        "target_execution_context_errors",
        "market_intent_missing_target_execution_context",
        "market_intent_deferred_no_target_order",
        "market_intent_expired_no_target_order",
        "market_intent_target_position_detected_before_retry",
        "pending_limit_deferred_target_tick_unavailable",
        "read_intents_with_offsets",
        "recover_target_state_on_startup",
        "target_startup_state_recovery",
        "symbols_with_pending_intents",
    ],
    "src/mt5/mt5_real.py": [
        "portable: bool = False",
        'kwargs["portable"] = True',
        "_tick_has_positive_quote",
        "_attempt_symbol_select_for_tick",
        "_tick_symbol_select_attempted",
    ],
    "src/utils/broker_profile.py": [
        "GTOS_MT5_PORTABLE",
        "def resolve_mt5_portable_mode",
    ],
    "config/profiles/operator_profile.yaml": [
        "portable: true",
        "terminal_data_path: C:\\MT5\\FTMO",
    ],
    "scripts/dual_broker_trade_record_projector.py": [
        "build_intent_from_trade_record",
        "initialized_at_end",
        "--replay-existing",
        "dual_broker_trade_record_projector_",
        "trade_record_projected",
    ],
    "scripts/run_live_monitoring_maintenance.py": [
        "DUAL_BROKER_HEARTBEAT_PATHS",
        "dual_broker_activation_guard_active",
        "dual_broker_activation_guard_suppressed_widening_maintenance",
    ],
    "research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/record_post_reboot_checkpoint.py": [
        "dual_broker_execution_follower_ftmo",
        "dual_broker_trade_record_projector",
        "secondary_execution_follower_present",
        "correct_memory_conscious_dual_shape",
        "continue_live_supervision_without_widening_footprint",
        "latest_read_only_process_observation",
        "active_supervision_checkpoint_repaired_bridge_live_continuation_required",
        "bridge_process_summary",
        "mt5_probe_summary",
    ],
    "research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/probe_dual_mt5_readonly.py": [
        "no_symbol_select_called",
        "positions_get",
        "orders_get",
        "symbol_info_tick",
        "portable",
        "read_only_mt5_account_terminal_position_order_symbol_inspection_no_symbol_select_no_broker_mutation",
        "dual_symbol_specs_checked_without_mass_symbol_select",
    ],
    "tests/test_run_live_monitoring_maintenance.py": [
        "test_dual_broker_guard_skips_widening_maintenance",
    ],
    "tests/test_dual_broker_intent_bus.py": [
        "test_canonical_intent_id_ignores_lifecycle_sltp_rewrites",
        "test_append_intent_dedupes_legacy_stored_id_by_current_identity",
        "test_append_intent_dedupes_pending_limit_source_fill_lifecycle",
        "test_build_intent_from_trade_record_defers_incomplete_vnext_context",
        "test_build_intent_from_trade_record_skips_ambiguous_execution",
        "test_build_intent_from_trade_record_skips_terminal_exit_update",
        "test_build_intent_from_trade_record_skips_terminal_pending_update",
    ],
    "tests/test_dual_broker_trade_record_projector.py": [
        "test_projector_replay_existing_enriches_vnext_execution_context",
        "test_projector_treats_sl_rewrite_as_duplicate_not_new_intent",
        "test_projector_skips_terminal_pending_rewrite",
    ],
    "tests/test_dual_broker_execution_follower.py": [
        "test_ftmo_follower_profile_covers_live_symbols_and_broker_geometry",
        "test_order_enabled_follower_defers_market_intent_when_target_tick_invalid",
        "test_order_enabled_follower_expires_old_market_intent_with_invalid_target_tick",
        "test_target_execution_context_errors_classifies_incomplete_vnext_intent",
        "test_order_enabled_follower_retries_market_intent_when_target_order_returns_none",
        "test_order_enabled_follower_logs_pretrade_refusal_when_target_order_returns_none",
        "test_order_enabled_follower_consumes_retry_when_target_position_appears",
        "test_order_enabled_follower_expires_old_market_intent_when_target_order_returns_none",
        "test_follower_offset_reader_exposes_row_end_for_retryable_deferral",
        "test_startup_recovery_instantiates_only_symbols_with_target_positions",
        "test_startup_recovery_restores_persisted_target_pending_intent",
        "EXPECTED_LIVE_SYMBOLS",
    ],
    "tests/test_mt5.py": [
        "test_zero_tick_does_not_poison_broker_offset_detection",
        "test_get_tick_lazily_selects_hidden_symbol_once",
    ],
    "src/research_infra/notification_queue_dead_zone_status.py": [
        "def default_queue_path()",
        "def default_lock_path()",
        "GTOS_RUNTIME_NAMESPACE",
    ],
    "scripts/audit_notification_queue_dead_zone.py": [
        "--queue-path",
        "--lock-path",
        "queue_path=args.queue_path",
        "lock_path=args.lock_path",
    ],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def git(args: list[str]) -> str:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return ""


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def base_row(name: str, status: str = "checkpoint_recorded") -> dict:
    return {
        "route_id": ROUTE_ID,
        "artifact": name,
        "recorded_at_utc": utc_now(),
        "status": status,
        "evidence_class": "DUAL_BROKER_VPS_LIVE_RUNTIME_DATA_BROKER_PROCESS_REPAIR_SUPERVISION",
        "checkpoint_scope": "notification_queue_namespace_repair_verified_pre_activation",
        "runtime_effect_boundary": "code_config_launcher_watchdog_repair_not_yet_reloaded",
    }


def build_initial_artifacts() -> None:
    now = utc_now()
    head = git(["rev-parse", "HEAD"])
    branch = git(["rev-parse", "--abbrev-ref", "HEAD"])
    status_paths = git([
        "status",
        "--short",
        "start_all.bat",
        "scripts/watchdog.ps1",
        "scripts/watchdog_e2e_verify.py",
        "scripts/audit_notification_queue_dead_zone.py",
        "src/components/orchestrator.py",
        "src/research_infra/notification_queue_dead_zone_status.py",
        "src/utils/notification_queue.py",
        "tests/test_notification_queue.py",
        "tests/test_start_all_runtime_contract.py",
        "tests/test_watchdog_e2e_verify.py",
    ])

    context_anchor = f"""# Dual-Broker Live Monitoring Repair Supervisor Context Anchor

Route id: `{ROUTE_ID}`
Generated: `{now}`
HEAD: `{head}`
Branch: `{branch}`

## Active Objective

Follow the controlling prompt at
`research/science_program_2026_05/04_goal_prompts/VNEXT_DUAL_BROKER_LIVE_MONITORING_REPAIR_SUPERVISOR_GOAL_PROMPT_2026-06-02.md`.

## Current Checkpoint

The first verified defect class is notification queue namespace collision risk:
the prior default queue path and worker lock could mix redacted_account and FTMO
notifications or let one account worker satisfy the other account's watchdog
liveness check.

Repair applied in this checkpoint:
- profile/env-derived queue paths in `src/utils/notification_queue.py`;
- orchestrator profile hook before lazy queue singleton creation;
- account-scoped `GTOS_NOTIFICATION_QUEUE_PATH` defaults in `start_all.bat` and `scripts/watchdog.ps1`;
- namespace-scoped worker locks `.notification_queue_worker_<namespace>.lock`;
- dead-zone audit queue/lock path parameters;
- focused tests and watchdog verifier substrings.

## Verification

- `python -m py_compile src\\utils\\notification_queue.py src\\components\\orchestrator.py src\\research_infra\\notification_queue_dead_zone_status.py scripts\\audit_notification_queue_dead_zone.py scripts\\watchdog_e2e_verify.py`
- PowerShell parser check for `scripts/watchdog.ps1`
- `python -m pytest tests/test_notification_queue.py tests/test_notifications.py tests/test_start_all_runtime_contract.py tests/test_watchdog_e2e_verify.py -q --basetemp=.pytest-tmp-dual-notification-repair -o cache_dir=.pytest-tmp-dual-notification-repair-cache`
  - Result: `107 passed, 1 skipped`

## Continuation

This is a checkpoint, not terminal completion. Remaining work includes current
MT5/process proof, scoped process reload, FTMO order-capable activation after
verification, direct candidate/lifecycle inspection, and persistent dual-broker
supervision until CEO stop or tested persistent supervisor replacement.
"""
    (ROUTE_DIR / "DUAL_SUPERVISOR_CONTEXT_ANCHOR.md").write_text(context_anchor, encoding="utf-8")

    state = {
        "route_id": ROUTE_ID,
        "schema_version": "dual_supervisor_state_v1",
        "generated_at_utc": now,
        "status": "active_checkpoint_continuation_required",
        "terminal_completion": False,
        "current_head": head,
        "branch": branch,
        "worktree_owned_changes": status_paths.splitlines() if status_paths else [],
        "active_defect": "notification_queue_namespace_collision_risk",
        "active_defect_status": "repaired_and_focused_tests_passed_pending_runtime_reload",
        "redacted_account_runtime_status": "existing_live_runtime_not_reloaded_by_this_checkpoint",
        "ftmo_runtime_status": "activation_pending_current_process_mt5_rollback_reverification",
        "runtime_effect_boundary": "code_config_launcher_watchdog_repair_not_yet_reloaded",
        "next_required_action": "capture current process and MT5 read-only proof before scoped reload or FTMO activation",
        "goal_remains_active": True,
    }
    write_json(ROUTE_DIR / "DUAL_SUPERVISOR_STATE.json", state)
    write_json(ROUTE_DIR / "DUAL_GIT_VERSION_AUDIT.json", {
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "branch": branch,
        "head": head,
        "status_paths": status_paths.splitlines() if status_paths else [],
        "remote_push_status": "not_attempted_in_this_checkpoint",
    })

    work_queue = [
        {**base_row("notification_queue_namespace_repair", "validated"), "state": "closed", "next_action": "runtime_reload_after_process_mt5_proof"},
        {**base_row("current_mt5_process_account_probe", "pending"), "state": "discovered", "next_action": "read_only_dual_terminal_account_process_probe"},
        {**base_row("redacted_account_scoped_reload", "pending"), "state": "discovered", "next_action": "stop_legacy_unscoped_processes_then_start_namespaced_runtime_after proof"},
        {**base_row("ftmo_order_capable_activation", "pending"), "state": "discovered", "next_action": "activate_after terminal_account_namespace_risk_data_notification_rollback_verification"},
    ]
    write_jsonl(ROUTE_DIR / "DUAL_SUPERVISOR_WORK_QUEUE.jsonl", work_queue)

    ledger_defaults = {
        "DUAL_SUPERVISOR_ACTION_LEDGER.jsonl": [{**base_row("action", "validated"), "action": "repaired_notification_queue_namespace_contract"}],
        "DUAL_SOURCE_INVENTORY_LEDGER.jsonl": [{**base_row("source_inventory", "validated"), "sources": list(CODE_SUBSTRINGS)}],
        "DUAL_REQUIRED_FILE_LEDGER.jsonl": [{**base_row("required_files", "validated"), "required_artifact_count": len(REQUIRED_ARTIFACTS)}],
        "DUAL_ENVIRONMENT_LEDGER.jsonl": [{**base_row("environment", "observed"), "host_note": "PowerShell intermittently reported paging-file pressure before focused tests passed"}],
        "DUAL_ACCOUNT_PROFILE_LEDGER.jsonl": [
            {**base_row("redacted_account_profile", "validated"), "profile": "config/profiles/redacted_account.yaml", "queue_path": "pipeline_state/redacted_account_live_bee34003/notification_queue.jsonl"},
            {**base_row("ftmo_profile", "validated"), "profile": "config/profiles/operator_profile.yaml", "queue_path": "pipeline_state/operator_profile/notification_queue.jsonl"},
        ],
        "DUAL_MT5_SYMBOL_SPEC_LEDGER.jsonl": [{**base_row("mt5_symbol_spec", "pending"), "status_detail": "not refreshed in notification repair checkpoint"}],
        "DUAL_NAMESPACE_ISOLATION_LEDGER.jsonl": [{**base_row("namespace_isolation", "validated"), "repair": "notification queue path and worker lock now account scoped"}],
        "DUAL_PROCESS_HEALTH_LEDGER.jsonl": [{**base_row("process_health", "pending"), "status_detail": "process reload not performed before current MT5/process proof"}],
        "DUAL_WATCHDOG_SCHEDULER_LEDGER.jsonl": [{**base_row("watchdog_scheduler", "validated"), "repair": "watchdog now requires account queue path and namespace worker lock"}],
        "DUAL_DATA_CAPTURE_HEALTH_LEDGER.jsonl": [{**base_row("data_capture_health", "pending"), "status_detail": "not refreshed in notification repair checkpoint"}],
        "DUAL_RUNTIME_DECISION_LEDGER.jsonl": [{**base_row("runtime_decision", "pending"), "status_detail": "candidate packet inspection pending after reload proof"}],
        "DUAL_CANDIDATE_PACKET_LEDGER.jsonl": [{**base_row("candidate_packet", "pending"), "status_detail": "direct candidate inspection pending"}],
        "DUAL_CANDIDATE_AGENT_INSPECTION_LEDGER.jsonl": [{**base_row("candidate_agent_inspection", "pending"), "direct_inspection_status": "not_started_this_checkpoint"}],
        "DUAL_NO_CANDIDATE_PROOF_LEDGER.jsonl": [{**base_row("no_candidate_proof", "pending"), "status_detail": "not_started_this_checkpoint"}],
        "DUAL_OPEN_TRADE_LIFECYCLE_LEDGER.jsonl": [{**base_row("open_trade_lifecycle", "pending"), "status_detail": "not refreshed in notification repair checkpoint"}],
        "DUAL_TRADE_AGENT_INSPECTION_LEDGER.jsonl": [{**base_row("trade_agent_inspection", "pending"), "direct_inspection_status": "not_started_this_checkpoint"}],
        "DUAL_BROKER_RECONCILIATION_LEDGER.jsonl": [{**base_row("broker_reconciliation", "pending"), "status_detail": "read-only broker reconciliation pending"}],
        "DUAL_RISK_EXPOSURE_LEDGER.jsonl": [{**base_row("risk_exposure", "pending"), "status_detail": "dual-account risk exposure proof pending"}],
        "DUAL_V3_RUNTIME_DISPOSITION_LEDGER.jsonl": [{**base_row("v3_runtime_disposition", "pending"), "selector_v3": "current disposition pending post-repair inspection", "scheduler_v3": "current disposition pending post-repair inspection", "execution_policy_v3": "current disposition pending post-repair inspection"}],
        "DUAL_NOTIFICATION_LEDGER.jsonl": [{**base_row("notification", "validated"), "finding": "shared queue/worker collision risk repaired before activation"}],
        "DUAL_ANOMALY_LEDGER.jsonl": [{**base_row("anomaly", "validated"), "anomaly_id": "DUAL-NOTIFICATION-QUEUE-COLLISION-RISK-001", "severity": "activation_blocking_until_repaired", "status_detail": "repaired_and_focused_tests_passed"}],
        "DUAL_REPAIR_LEDGER.jsonl": [{**base_row("repair", "validated"), "repair_id": "DUAL-REPAIR-NOTIFICATION-QUEUE-NAMESPACE-001", "files": list(CODE_SUBSTRINGS)}],
        "DUAL_RESTART_RELOAD_LEDGER.jsonl": [{**base_row("restart_reload", "pending"), "restart_status": "not_performed", "reason": "current MT5/process proof required before scoped live reload"}],
        "DUAL_SUPERVISOR_CHECKPOINTS.jsonl": [{**base_row("checkpoint", "validated"), "checkpoint_id": "dual_checkpoint_notification_queue_namespace_repair_2026_06_02", "terminal_completion": False}],
    }
    for name, rows in ledger_defaults.items():
        write_jsonl(ROUTE_DIR / name, rows)

    write_json(ROUTE_DIR / "DUAL_MT5_TERMINAL_ACCOUNT_PROBE.json", {
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "status": "pending_refresh_after_notification_repair",
        "redacted_account": "prior artifacts prove existing live account; current probe not rerun in this checkpoint",
        "ftmo": "prior artifacts prove terminal/profile flat staged; current activation probe pending",
        "broker_mutation_status": "none",
    })

    manifest = {
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "artifact_count": len(REQUIRED_ARTIFACTS) + 1,
        "required_artifacts": REQUIRED_ARTIFACTS,
        "route_owned_verifier": str((ROUTE_DIR / "verify_dual_supervisor_checkpoint.py").relative_to(REPO_ROOT)),
        "focused_tests": [
            "tests/test_notification_queue.py",
            "tests/test_notifications.py",
            "tests/test_start_all_runtime_contract.py",
            "tests/test_watchdog_e2e_verify.py",
        ],
        "checkpoint_status": "active_continuation_required",
    }
    write_json(ROUTE_DIR / "DUAL_OUTPUT_MANIFEST.json", manifest)

    write_json(ROUTE_DIR / "DUAL_COMPLETION_OR_CONTINUATION_AUDIT.json", {
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "terminal_completion": False,
        "can_mark_goal_complete": False,
        "status": "checkpoint_only_continuation_required",
        "completed_this_checkpoint": [
            "mandatory preflight reread after resume",
            "notification queue namespace defect repaired",
            "focused syntax and pytest verification passed",
            "initial required route artifacts created",
        ],
        "remaining_exact_work": [
            "current dual MT5 terminal/account/process proof",
            "scoped live reload of affected redacted_account components",
            "FTMO order-capable activation after verification",
            "direct candidate/no-candidate/trade/lifecycle inspection",
            "dual account risk/exposure and V3 runtime disposition proof",
            "persistent supervisor or CEO stop condition",
        ],
        "instruction_coverage": {
            "live_state_regenerated": True,
            "controlling_prompt_read": True,
            "starter_read": True,
            "doctrine_files_read": True,
            "prior_vps_supervisor_artifacts_read": True,
            "vps_v3_ftmo_artifacts_read": True,
            "direct_candidate_trade_lifecycle_inspection_complete": False,
        },
    })


def verify() -> dict:
    now = utc_now()
    failures: list[dict] = []
    for name in REQUIRED_ARTIFACTS:
        path = ROUTE_DIR / name
        if not path.exists():
            if name == "DUAL_VERIFICATION_RESULT.json":
                continue
            failures.append({"type": "missing_artifact", "path": name})
            continue
        if name.endswith(".json"):
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                failures.append({"type": "json_parse_error", "path": name, "error": str(exc)})
        elif name.endswith(".jsonl"):
            for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if not line.strip():
                    continue
                try:
                    json.loads(line)
                except Exception as exc:
                    failures.append({"type": "jsonl_parse_error", "path": name, "line": idx, "error": str(exc)})

    for rel_path, snippets in CODE_SUBSTRINGS.items():
        text_path = REPO_ROOT / rel_path
        text = text_path.read_text(encoding="utf-8", errors="replace")
        for snippet in snippets:
            if snippet not in text:
                failures.append({"type": "missing_code_substring", "path": rel_path, "substring": snippet})

    result = {
        "route_id": ROUTE_ID,
        "schema_version": "dual_supervisor_verification_result_v1",
        "generated_at_utc": now,
        "status": "PASS" if not failures else "FAIL",
        "failure_count": len(failures),
        "failures": failures,
        "artifact_count_checked": len(REQUIRED_ARTIFACTS),
        "code_contracts_checked": CODE_SUBSTRINGS,
        "runtime_effect_boundary": "verification_only_no_process_or_broker_mutation",
    }
    write_json(ROUTE_DIR / "DUAL_VERIFICATION_RESULT.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-checkpoint", action="store_true")
    args = parser.parse_args()
    if args.write_checkpoint:
        build_initial_artifacts()
    result = verify()
    print(json.dumps({"status": result["status"], "failure_count": result["failure_count"]}, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
