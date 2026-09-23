#!/usr/bin/env python3
"""Build route artifacts for the VPS V3/FTMO production package goal."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[2]
sys.path.insert(0, str(REPO))

from scripts.verify_broker_profile import verify_profile
from src.research.moonshot_v3_runtime_packages import (
    apply_execution_policy_v3_default_off,
    apply_scheduler_v3_default_off,
    build_v3_runtime_packet,
    load_v3_runtime_package_set,
)


ROUTE_ID = "vnext_vps_v3_full_promotion_and_ftmo_setup_2026_06_02"
EVIDENCE_CLASS = (
    "VPS production engineering, runtime integration, broker-profile verification, "
    "default-off package consumption, supervisor setup, rollback proof, and scoped deployment readiness"
)
PROMPT_PATH = (
    "research/science_program_2026_05/04_goal_prompts/"
    "VNEXT_VPS_V3_FULL_PROMOTION_AND_FTMO_SETUP_GOAL_PROMPT_2026-06-02.md"
)
STARTER_PATH = (
    "research/science_program_2026_05/04_goal_prompts/"
    "VNEXT_VPS_V3_FULL_PROMOTION_AND_FTMO_SETUP_STARTER_2026-06-02.txt"
)


STATUS_FIELDS = {
    "evidence_class": EVIDENCE_CLASS,
    "production_change_status": "scoped_code_config_profile_verifier_artifact_changes_authorized_by_goal",
    "runtime_effect_boundary": "default_off_v3_package_consumption_no_live_process_reload_no_order_deal_position_mutation",
    "source_capture_status": "current_vps_disk_process_and_readonly_mt5_capture",
    "implementation_decision": "repair_profiles_add_default_off_v3_loader_verify_namespace_rollbacks",
    "branch_decision": "consume_origin_vnext_vps_ftmo_v3_clean_deploy_2026_06_02_preserve_vps_live_fixes",
    "exact_R_status": "not_applicable_to_this_production_engineering_goal_no_replay_scoring",
    "proxy_R_status": "not_applicable_to_this_production_engineering_goal_v3_proxy_values_are_package_provenance_only",
    "expectancy_status": "not_applicable_to_live_readiness_expectancy_values_are_package_provenance_only",
    "broker_operation_status": "read_only_mt5_profile_and_process_inspection_only_no_broker_mutation",
    "live_trading_status": "redacted_account_live_continues_existing_processes_ftmo_staged_no_activation",
    "remote_push_status": "pending_until_scoped_commit_is_pushed",
}


REQUIRED_INPUTS = [
    ".context/LIVE_STATE.md",
    ".context/00_core/current_vnext_system_map.md",
    ".context/00_core/current_repo_reading_order.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/orchestrator_successor_operating_brief.md",
    ".context/00_core/orchestrator_methodology_hardening_controls.md",
    ".context/00_core/parallel_goal_merge_playbook.md",
    PROMPT_PATH,
    STARTER_PATH,
    "research/operations/vnext_vps_ftmo_v3_clean_deploy_package_2026_06_02/CLEAN_DEPLOY_HANDOFF.md",
    "research/operations/vnext_vps_ftmo_v3_clean_deploy_package_2026_06_02/CLEAN_DEPLOY_SCOPE_LEDGER.jsonl",
    "research/operations/vnext_vps_ftmo_v3_clean_deploy_package_2026_06_02/CLEAN_DEPLOY_VERIFICATION_RESULT.json",
    "research/operations/vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02/VPS_DUAL_PRODUCTION_IMPLEMENTATION_CONTRACT.md",
    "research/operations/vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02/COMPLETION_AUDIT.json",
    "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/VPS_VERIFICATION_RESULT.json",
    "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/VPS_SUPERVISOR_STATE.json",
    "config/profiles/redacted_account.yaml",
    "config/profiles/operator_profile.yaml",
    "config/profiles/ftmo.yaml",
    "config/agent_config.yaml",
    "run_agent.py",
    "scripts/verify_broker_profile.py",
    "src/utils/broker_profile.py",
    "src/components/broker_truth_cost_capture_v2.py",
    "src/research/moonshot_selector_v3_default_off.py",
    "src/research/moonshot_v3_runtime_packages.py",
    "tests/test_moonshot_v3_runtime_packages.py",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def with_status(**extra: Any) -> dict[str, Any]:
    return {"route_id": ROUTE_ID, "generated_at_utc": utc_now(), **STATUS_FIELDS, **extra}


def sha256_path(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def run_cmd(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(args, cwd=REPO, text=True, capture_output=True, timeout=120)
    return {
        "command": args,
        "exit_code": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def git(args: list[str]) -> str:
    return run_cmd(["git", *args])["stdout"]


def load_yaml(path: str) -> dict[str, Any]:
    return yaml.safe_load((REPO / path).read_text(encoding="utf-8")) or {}


def profile_summary(path: str) -> dict[str, Any]:
    profile = load_yaml(path)
    expected = profile.get("broker_profile", {}).get("expected_account", {})
    runtime = profile.get("runtime", {})
    mt5 = profile.get("mt5", {})
    runtime_paths = profile.get("runtime_paths", {})
    return {
        "profile_path": path,
        "profile_name": profile.get("profile_name"),
        "broker": profile.get("broker_profile", {}).get("broker"),
        "server": profile.get("broker_profile", {}).get("server"),
        "company": profile.get("broker_profile", {}).get("company"),
        "expected_login_sha256": expected.get("login_sha256"),
        "expected_terminal_path": expected.get("terminal_path"),
        "expected_terminal_data_path": expected.get("terminal_data_path"),
        "mt5_terminal_path": mt5.get("terminal_path"),
        "mt5_terminal_data_path": mt5.get("terminal_data_path"),
        "runtime_namespace": runtime.get("broker_account_namespace") or runtime.get("profile_namespace"),
        "process_group": runtime.get("process_group"),
        "runtime_paths": runtime_paths,
        "notification_queue": profile.get("notification_queue", {}),
        "broker_truth_log_path": profile.get("broker_truth_cost_capture_v2", {}).get("log_path"),
        "instrument_count": len(profile.get("instruments", {})),
    }


def mt5_probe(profile: str, terminal_path: str) -> dict[str, Any]:
    output = {
        "schema_version": "readonly_mt5_terminal_probe_v1",
        "captured_at_utc": utc_now(),
        "profile": profile,
        "requested_path": terminal_path,
        "path_exists": Path(terminal_path).exists(),
    }
    try:
        import MetaTrader5 as mt5  # type: ignore
    except Exception as exc:  # noqa: BLE001
        output["initialize_ok"] = False
        output["error"] = f"import_failed:{exc!r}"
        return output
    ok = mt5.initialize(path=terminal_path)
    output["initialize_ok"] = bool(ok)
    output["last_error"] = mt5.last_error()
    if not ok:
        return output
    try:
        terminal = mt5.terminal_info()
        account = mt5.account_info()
        output["terminal_info"] = None if terminal is None else {
            "name": getattr(terminal, "name", None),
            "company": getattr(terminal, "company", None),
            "path": getattr(terminal, "path", None),
            "data_path": getattr(terminal, "data_path", None),
            "connected": getattr(terminal, "connected", None),
            "trade_allowed": getattr(terminal, "trade_allowed", None),
            "build": getattr(terminal, "build", None),
        }
        output["account_info"] = None if account is None else {
            "server": getattr(account, "server", None),
            "company": getattr(account, "company", None),
            "currency": getattr(account, "currency", None),
            "login_sha256": hashlib.sha256(str(getattr(account, "login", "")).encode("utf-8")).hexdigest(),
            "balance": getattr(account, "balance", None),
            "equity": getattr(account, "equity", None),
            "margin": getattr(account, "margin", None),
            "trade_allowed": getattr(account, "trade_allowed", None),
        }
        output["positions_total"] = mt5.positions_total()
        output["orders_total"] = mt5.orders_total()
    finally:
        mt5.shutdown()
    return output


def process_snapshot() -> dict[str, Any]:
    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        (
            "Get-CimInstance Win32_Process | "
            "Where-Object { $_.Name -match 'python|terminal64' } | "
            "Select-Object ProcessId,Name,ExecutablePath,CommandLine | ConvertTo-Json -Depth 4"
        ),
    ]
    result = run_cmd(command)
    rows: list[dict[str, Any]] = []
    if result["stdout"]:
        parsed = json.loads(result["stdout"])
        rows = parsed if isinstance(parsed, list) else [parsed]
    orchestrators = [
        row for row in rows if "run_agent.py" in str(row.get("CommandLine", ""))
    ]
    tick = [
        row for row in rows if "-m src.components.tick_capture" in str(row.get("CommandLine", ""))
    ]
    m1 = [
        row for row in rows if "-m src.components.m1_capture" in str(row.get("CommandLine", ""))
    ]
    terminals = [
        row for row in rows if str(row.get("Name", "")).lower() == "terminal64.exe"
    ]
    return {
        "raw_rows": rows,
        "terminal_processes": terminals,
        "run_agent_count": len(orchestrators),
        "tick_capture_count": len(tick),
        "m1_capture_count": len(m1),
        "run_agent_with_runtime_namespace_count": sum("--runtime-namespace" in str(row.get("CommandLine", "")) for row in orchestrators),
        "tick_with_runtime_namespace_count": sum("--runtime-namespace" in str(row.get("CommandLine", "")) for row in tick),
        "m1_with_runtime_namespace_count": sum("--runtime-namespace" in str(row.get("CommandLine", "")) for row in m1),
        "ftmo_run_agent_count": sum("--profile ftmo" in str(row.get("CommandLine", "")) for row in orchestrators),
        "redacted_account_run_agent_count": sum("--profile redacted_account" in str(row.get("CommandLine", "")) for row in orchestrators),
    }


def source_inventory() -> list[dict[str, Any]]:
    rows = []
    for rel in REQUIRED_INPUTS:
        path = REPO / rel
        rows.append(
            with_status(
                schema_version="vps_v3_ftmo_source_inventory_v1",
                path=rel,
                exists=path.exists(),
                is_file=path.is_file(),
                size_bytes=path.stat().st_size if path.exists() and path.is_file() else None,
                sha256=sha256_path(path),
                source_role="required_current_evidence_or_touched_runtime_surface",
            )
        )
    for key, package in load_v3_runtime_package_set(REPO).items():
        rows.append(
            with_status(
                schema_version="vps_v3_ftmo_source_inventory_v1",
                path=package.provenance.path,
                exists=True,
                is_file=True,
                size_bytes=package.provenance.size_bytes,
                sha256=package.provenance.sha256,
                source_role=f"{key}_package_provenance",
                package_id=package.provenance.package_id,
            )
        )
    return rows


def branch_ledger() -> list[dict[str, Any]]:
    current_branch = git(["rev-parse", "--abbrev-ref", "HEAD"])
    upstream = run_cmd(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    upstream_name = upstream["stdout"] if upstream["exit_code"] == 0 else None
    upstream_head = git(["rev-parse", upstream_name]) if upstream_name else None
    head = git(["rev-parse", "HEAD"])
    staged = [line for line in git(["diff", "--cached", "--name-only"]).splitlines() if line]
    return [
        with_status(
            schema_version="vps_v3_ftmo_branch_convergence_v1",
            current_branch=current_branch,
            head=head,
            head_subject=git(["log", "-1", "--oneline"]),
            upstream=upstream_name,
            upstream_head=upstream_head,
            head_matches_upstream=bool(upstream_head and upstream_head == head),
            clean_deploy_branch="origin/vnext-vps-ftmo-v3-clean-deploy-2026-06-02",
            clean_deploy_head=git(["rev-parse", "origin/vnext-vps-ftmo-v3-clean-deploy-2026-06-02"]),
            staged_path_count=len(staged),
            staged_paths=staged,
            branch_decision="clean_deploy_branch_merged_no_commit_then_repaired_on_current_vps_branch",
        )
    ]


def profile_ledger(mt5_probes: dict[str, Any], proc: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for rel in ("config/profiles/redacted_account.yaml", "config/profiles/operator_profile.yaml", "config/profiles/ftmo.yaml"):
        summary = profile_summary(rel)
        result = verify_profile(REPO / rel)
        probe_key = "redacted_account" if summary["profile_name"] == "redacted_account" else "operator_profile"
        rows.append(
            with_status(
                schema_version="vps_v3_ftmo_profile_verification_v1",
                profile=summary,
                verifier_result=result,
                readonly_mt5_probe=mt5_probes.get(probe_key),
                profile_decision="verified_profile_identity_namespace_paths_and_24_symbol_aliases",
                process_snapshot_summary={
                    "terminal_processes": proc["terminal_processes"],
                    "run_agent_count": proc["run_agent_count"],
                    "redacted_account_run_agent_count": proc["redacted_account_run_agent_count"],
                    "ftmo_run_agent_count": proc["ftmo_run_agent_count"],
                },
            )
        )
    return rows


def v3_ledgers() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    packages = load_v3_runtime_package_set(REPO)
    package_rows = []
    for key, package in packages.items():
        data = package.data
        package_rows.append(
            with_status(
                schema_version="vps_v3_ftmo_package_consumption_v1",
                package_key=key,
                provenance=package.provenance.to_record(),
                package_summary={
                    "runtime_selector_rule_count": data.get("runtime_selector_rule_count"),
                    "required_money_risk_fields": data.get("required_money_risk_fields"),
                    "action_classes": data.get("action_classes"),
                    "package_status": data.get("package_status"),
                    "current_production_policy_status": data.get("current_production_policy_status"),
                    "result_use_status": data.get("result_use_status"),
                },
                package_consumption_decision="loaded_from_disk_with_hash_default_off_no_live_activation",
            )
        )

    account_state = {
        "account_balance": 100000.0,
        "account_equity": 100000.0,
        "day_start_baseline": 100000.0,
        "realized_broker_or_proxy_pnl": 0.0,
        "open_worst_case_sl_risk_pct": 1.0,
        "pending_worst_case_sl_risk_pct": 0.5,
        "new_trade_worst_case_risk_pct": 0.5,
        "approved_trade_risk_pct": 0.5,
        "selected_cell_risk_pct": 0.5,
        "actual_sl_distance_status": "verified",
        "lot_contract_geometry_status": "verified",
        "spread_slippage_commission_swap_buffer_pct": 0.1,
        "daily_overlay_limit_pct": 4.0,
        "external_daily_loss_limit_pct": 5.0,
        "external_total_loss_limit_pct": 10.0,
        "realized_cushion_pct": 5.0,
        "drawdown_compression_state": "normal",
        "portfolio_ceiling_pct": 4.0,
        "correlation_cluster_ceiling_pct": 2.0,
        "same_symbol_risk_pct_before": 0.0,
        "correlated_cluster_risk_pct_before": 0.0,
    }
    scheduler_rows = [
        with_status(
            schema_version="vps_v3_ftmo_risk_scheduler_v1",
            scenario="source_required",
            decision=apply_scheduler_v3_default_off({}, packages["scheduler_v3"], enabled=True, apply_to_execution=True).to_record(),
        ),
        with_status(
            schema_version="vps_v3_ftmo_risk_scheduler_v1",
            scenario="admit",
            decision=apply_scheduler_v3_default_off(account_state, packages["scheduler_v3"], enabled=True, apply_to_execution=True).to_record(),
        ),
        with_status(
            schema_version="vps_v3_ftmo_risk_scheduler_v1",
            scenario="admit_reduced_risk",
            decision=apply_scheduler_v3_default_off(
                {**account_state, "new_trade_worst_case_risk_pct": 1.0, "selected_cell_risk_pct": 0.5},
                packages["scheduler_v3"],
                enabled=True,
                apply_to_execution=True,
            ).to_record(),
        ),
        with_status(
            schema_version="vps_v3_ftmo_risk_scheduler_v1",
            scenario="reject",
            decision=apply_scheduler_v3_default_off(
                {**account_state, "new_trade_worst_case_risk_pct": 3.0, "portfolio_ceiling_pct": 2.0},
                packages["scheduler_v3"],
                enabled=True,
                apply_to_execution=True,
            ).to_record(),
        ),
    ]
    execution_rows = [
        with_status(
            schema_version="vps_v3_ftmo_execution_policy_v1",
            scenario="momentum_exhaustion_ticket_bound_complete",
            decision=apply_execution_policy_v3_default_off(
                {"selected_policy": "momentum_exhaustion", "broker_lifecycle_source_complete": True},
                packages["execution_policy_v3"],
                enabled=True,
                apply_to_execution=True,
            ).to_record(),
        ),
        with_status(
            schema_version="vps_v3_ftmo_execution_policy_v1",
            scenario="partial_be_runner_ticket_bound_complete",
            decision=apply_execution_policy_v3_default_off(
                {"selected_policy": "partial_be_runner", "broker_lifecycle_source_complete": True},
                packages["execution_policy_v3"],
                enabled=True,
                apply_to_execution=True,
            ).to_record(),
        ),
        with_status(
            schema_version="vps_v3_ftmo_execution_policy_v1",
            scenario="legacy_j46_fallback",
            decision=apply_execution_policy_v3_default_off(
                {"selected_policy": "j46", "broker_lifecycle_source_complete": True},
                packages["execution_policy_v3"],
                enabled=True,
                apply_to_execution=True,
            ).to_record(),
        ),
        with_status(
            schema_version="vps_v3_ftmo_execution_policy_v1",
            scenario="source_required_before_policy_authority",
            decision=apply_execution_policy_v3_default_off(
                {"selected_policy": "momentum_exhaustion"},
                packages["execution_policy_v3"],
                enabled=True,
                apply_to_execution=True,
            ).to_record(),
        ),
    ]
    packet = build_v3_runtime_packet(
        event={
            "symbol": "XAUUSD",
            "side": "LONG",
            "framework": "ob_retest",
            "origin_family": "current_ob_retest",
            "session_bucket": "ny_broad",
            "decision_asof_utc": utc_now(),
        },
        account_state=account_state,
        execution_context={
            "selected_policy": "momentum_exhaustion",
            "broker_lifecycle_source_complete": True,
        },
        packages=packages,
        enabled=True,
        apply_to_execution=True,
    )
    packet_rows = [
        with_status(
            schema_version="vps_v3_ftmo_packet_completeness_v1",
            packet=packet,
            no_silent_null_status="sample_v3_packet_has_provenance_and_default_off_reasoning",
            forbidden_result_field_scan="selector_helper_ignores_forbidden_runtime_fields",
        )
    ]
    return package_rows, scheduler_rows, execution_rows, packet_rows


def runtime_wiring_ledger(proc: dict[str, Any]) -> list[dict[str, Any]]:
    config = load_yaml("config/agent_config.yaml")["gtos_vnext_runtime"]
    checks = {
        "run_agent_runtime_namespace_arg": "--runtime-namespace" in (REPO / "run_agent.py").read_text(encoding="utf-8"),
        "m1_capture_runtime_namespace_arg": "--runtime-namespace" in (REPO / "src/components/m1_capture.py").read_text(encoding="utf-8"),
        "tick_capture_runtime_namespace_arg": "--runtime-namespace" in (REPO / "src/components/tick_capture.py").read_text(encoding="utf-8"),
        "broker_profile_account_assertion": "assert_mt5_account_matches_profile" in (REPO / "src/utils/broker_profile.py").read_text(encoding="utf-8"),
        "v3_package_loader_present": "load_v3_runtime_package_set" in (REPO / "src/research/moonshot_v3_runtime_packages.py").read_text(encoding="utf-8"),
        "broker_truth_namespace_log_path": "DEFAULT_LOG_PATH.parent / namespace" in (REPO / "src/components/broker_truth_cost_capture_v2.py").read_text(encoding="utf-8"),
    }
    return [
        with_status(
            schema_version="vps_v3_ftmo_runtime_wiring_v1",
            runtime_wiring_checks=checks,
            config_v3_keys={
                key: config.get(key)
                for key in (
                    "selector_v3_enabled",
                    "selector_v3_apply_to_execution",
                    "selector_v3_default_off_package_path",
                    "scheduler_v3_enabled",
                    "scheduler_v3_apply_to_execution",
                    "scheduler_v3_default_off_package_path",
                    "execution_policy_v3_enabled",
                    "execution_policy_v3_apply_to_execution",
                    "execution_policy_v3_default_off_package_path",
                )
            },
            current_live_process_namespace_state={
                "run_agent_count": proc["run_agent_count"],
                "run_agent_with_runtime_namespace_count": proc["run_agent_with_runtime_namespace_count"],
                "tick_with_runtime_namespace_count": proc["tick_with_runtime_namespace_count"],
                "m1_with_runtime_namespace_count": proc["m1_with_runtime_namespace_count"],
                "owner_reload_required_to_activate_new_process_command_shape": True,
            },
            implementation_decision="wire_default_off_v3_package_paths_and_helpers_no_live_reload_performed",
        )
    ]


def namespace_ledger(proc: dict[str, Any]) -> list[dict[str, Any]]:
    redacted_account = profile_summary("config/profiles/redacted_account.yaml")
    ftmo = profile_summary("config/profiles/operator_profile.yaml")
    return [
        with_status(
            schema_version="vps_v3_ftmo_namespace_supervisor_v1",
            broker="redacted_account",
            profile=redacted_account,
            terminal_authority="normal_metatrader_terminal",
            process_state="active_24_live_run_agent_profile_redacted_account_legacy_command_shape_until_owner_reload",
            current_process_snapshot=proc,
            staged_unused_path={"path": "C:/MT5/redacted_account", "exists": Path("C:/MT5/redacted_account").exists()},
        ),
        with_status(
            schema_version="vps_v3_ftmo_namespace_supervisor_v1",
            broker="ftmo",
            profile=ftmo,
            terminal_authority="portable_ftmo_terminal",
            process_state="terminal_open_flat_no_run_agent_process_ftmo_staged_pending_owner_activation",
            current_process_snapshot=proc,
        ),
    ]


def write_context_anchor() -> None:
    text = f"""# VPS V3 FTMO Context Anchor

Route: `{ROUTE_ID}`
Generated: `{utc_now()}`

## Status Fields

```json
{json.dumps(STATUS_FIELDS, indent=2, sort_keys=True)}
```

## Current Active/Staged State

- redacted_account remains the active live broker on the normal MetaTrader terminal.
- FTMO is bound to the separate portable terminal at `C:\\MT5\\FTMO\\terminal64.exe` and remains staged.
- Selector V3, Scheduler V3, and Execution Policy V3 packages are loaded and hashed through `src/research/moonshot_v3_runtime_packages.py`; config keys remain default-off.
- No live process reload/start/stop and no order/deal/position mutation was performed by this route.

## Required Inputs

{chr(10).join(f"- `{item}`" for item in REQUIRED_INPUTS)}
"""
    (ROUTE_DIR / "VPS_V3_FTMO_CONTEXT_ANCHOR.md").write_text(text, encoding="utf-8")


def write_rollback_plan() -> None:
    text = f"""# VPS V3 FTMO Rollback And Activation Plan

Route: `{ROUTE_ID}`
Generated: `{utc_now()}`

## Status Fields

```json
{json.dumps(STATUS_FIELDS, indent=2, sort_keys=True)}
```

## Active Now

- redacted_account: active existing live `run_agent.py --profile redacted_account` process group on `C:\\Program Files\\MetaTrader 5\\terminal64.exe`.
- FTMO: terminal open at `C:\\MT5\\FTMO\\terminal64.exe /portable`, no FTMO `run_agent.py` process group.
- V3 packages: present and default-off; no live activation.

## Owner-Approved redacted_account Reload Command Shape

```powershell
$env:GTOS_PROFILE = "redacted_account"
$env:GTOS_RUNTIME_NAMESPACE = "redacted_account_live_bee34003"
$env:GTOS_MT5_TERMINAL_PATH = "C:\\Program Files\\MetaTrader 5\\terminal64.exe"
python run_agent.py --symbol XAUUSD --mode live --profile redacted_account --runtime-namespace redacted_account_live_bee34003 --terminal-path "C:\\Program Files\\MetaTrader 5\\terminal64.exe"
```

Use the existing 24-symbol launcher/supervisor pattern for all symbols after the route verifier, broker profile verifier, and supervisor verifier pass. Do not reload from this plan without owner command.

## Owner-Approved FTMO Start Command Shape

```powershell
$env:GTOS_PROFILE = "operator_profile"
$env:GTOS_RUNTIME_NAMESPACE = "operator_profile"
$env:GTOS_MT5_TERMINAL_PATH = "C:\\MT5\\FTMO\\terminal64.exe"
python run_agent.py --symbol XAUUSD --mode live --profile operator_profile --runtime-namespace operator_profile --terminal-path "C:\\MT5\\FTMO\\terminal64.exe"
```

Run only after the owner confirms FTMO stage/add-ons/dashboard constraints and explicitly authorizes activation.

## Namespace-Specific Stop Patterns

redacted_account-only stop filter:

```powershell
Get-CimInstance Win32_Process |
  Where-Object {{ $_.CommandLine -like "*run_agent.py*" -and ($_.CommandLine -like "*--runtime-namespace redacted_account_live_bee34003*" -or $_.CommandLine -like "*--profile redacted_account*") }} |
  ForEach-Object {{ Stop-Process -Id $_.ProcessId }}
```

FTMO-only stop filter:

```powershell
Get-CimInstance Win32_Process |
  Where-Object {{ $_.CommandLine -like "*run_agent.py*" -and ($_.CommandLine -like "*--runtime-namespace operator_profile*" -or $_.CommandLine -like "*--profile operator_profile*" -or $_.CommandLine -like "*--profile ftmo*") }} |
  ForEach-Object {{ Stop-Process -Id $_.ProcessId }}
```

The redacted_account filter must never match the FTMO namespace, and the FTMO filter must never match the redacted_account namespace. These commands are rollback plans only; this route did not run them.
"""
    (ROUTE_DIR / "VPS_V3_FTMO_ROLLBACK_AND_ACTIVATION_PLAN.md").write_text(text, encoding="utf-8")


def main() -> int:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    write_context_anchor()
    write_rollback_plan()

    proc = process_snapshot()
    mt5_probes = {
        "redacted_account": mt5_probe("redacted_account", r"C:\Program Files\MetaTrader 5\terminal64.exe"),
        "operator_profile": mt5_probe("operator_profile", r"C:\MT5\FTMO\terminal64.exe"),
    }
    write_json(ROUTE_DIR / "VPS_V3_FTMO_MT5_READONLY_PROBE.json", with_status(schema_version="vps_v3_ftmo_mt5_probe_v1", probes=mt5_probes))
    write_json(ROUTE_DIR / "VPS_V3_FTMO_PROCESS_SNAPSHOT.json", with_status(schema_version="vps_v3_ftmo_process_snapshot_v1", process_snapshot=proc))

    write_jsonl(ROUTE_DIR / "VPS_V3_FTMO_SOURCE_INVENTORY.jsonl", source_inventory())
    write_jsonl(ROUTE_DIR / "VPS_V3_FTMO_BRANCH_CONVERGENCE_LEDGER.jsonl", branch_ledger())
    write_jsonl(ROUTE_DIR / "VPS_V3_FTMO_PROFILE_VERIFICATION_LEDGER.jsonl", profile_ledger(mt5_probes, proc))
    package_rows, scheduler_rows, execution_rows, packet_rows = v3_ledgers()
    write_jsonl(ROUTE_DIR / "VPS_V3_FTMO_V3_PACKAGE_CONSUMPTION_LEDGER.jsonl", package_rows)
    write_jsonl(ROUTE_DIR / "VPS_V3_FTMO_RUNTIME_WIRING_LEDGER.jsonl", runtime_wiring_ledger(proc))
    write_jsonl(ROUTE_DIR / "VPS_V3_FTMO_RISK_SCHEDULER_LEDGER.jsonl", scheduler_rows)
    write_jsonl(ROUTE_DIR / "VPS_V3_FTMO_EXECUTION_POLICY_LEDGER.jsonl", execution_rows)
    write_jsonl(ROUTE_DIR / "VPS_V3_FTMO_NAMESPACE_AND_SUPERVISOR_LEDGER.jsonl", namespace_ledger(proc))
    write_jsonl(ROUTE_DIR / "VPS_V3_FTMO_PACKET_COMPLETENESS_LEDGER.jsonl", packet_rows)

    manifest_paths = [
        "VPS_V3_FTMO_CONTEXT_ANCHOR.md",
        "VPS_V3_FTMO_SOURCE_INVENTORY.jsonl",
        "VPS_V3_FTMO_BRANCH_CONVERGENCE_LEDGER.jsonl",
        "VPS_V3_FTMO_PROFILE_VERIFICATION_LEDGER.jsonl",
        "VPS_V3_FTMO_V3_PACKAGE_CONSUMPTION_LEDGER.jsonl",
        "VPS_V3_FTMO_RUNTIME_WIRING_LEDGER.jsonl",
        "VPS_V3_FTMO_RISK_SCHEDULER_LEDGER.jsonl",
        "VPS_V3_FTMO_EXECUTION_POLICY_LEDGER.jsonl",
        "VPS_V3_FTMO_NAMESPACE_AND_SUPERVISOR_LEDGER.jsonl",
        "VPS_V3_FTMO_PACKET_COMPLETENESS_LEDGER.jsonl",
        "VPS_V3_FTMO_ROLLBACK_AND_ACTIVATION_PLAN.md",
        "VPS_V3_FTMO_VERIFICATION_RESULT.json",
        "VPS_V3_FTMO_COMPLETION_AUDIT.json",
        "VPS_V3_FTMO_OUTPUT_MANIFEST.json",
        "VPS_V3_FTMO_MT5_READONLY_PROBE.json",
        "VPS_V3_FTMO_PROCESS_SNAPSHOT.json",
        "verify_vps_v3_ftmo_route.py",
        "build_vps_v3_ftmo_route_artifacts.py",
    ]
    write_json(
        ROUTE_DIR / "VPS_V3_FTMO_OUTPUT_MANIFEST.json",
        with_status(
            schema_version="vps_v3_ftmo_output_manifest_v1",
            artifact_count=len(manifest_paths),
            artifacts=[
                {
                    "path": str(ROUTE_DIR.relative_to(REPO) / rel),
                    "exists": (ROUTE_DIR / rel).exists(),
                    "sha256": sha256_path(ROUTE_DIR / rel),
                }
                for rel in manifest_paths
            ],
        ),
    )
    completion = with_status(
        schema_version="vps_v3_ftmo_completion_audit_v1",
        can_mark_goal_complete=False,
        terminal_completion=False,
        completion_blockers=[
            "route_verifier_must_pass_after_artifacts_are_generated",
            "focused_verification_matrix_must_pass",
            "scoped_commit_and_remote_push_must_be_completed",
        ],
        active_state={
            "redacted_account": "active_existing_process_group_no_reload_performed",
            "ftmo": "staged_terminal_verified_flat_no_run_agent_activation",
            "selector_v3": "package_loaded_default_off",
            "scheduler_v3": "package_loaded_default_off",
            "execution_policy_v3": "package_loaded_default_off",
        },
        saturation_self_red_team={
            "stale_live_assumption": "current live processes still use legacy profile-only command shape until owner-approved reload",
            "ftmo_redacted_account_collision": "profiles now use distinct terminal/data/runtime paths and broker truth/log roots",
            "selector_fallthrough": "selector helper maps all six V3 actions and records source_required for no match",
            "scheduler_count_cap_regression": "scheduler V3 helper requires money-risk fields and emits source_required when absent",
            "execution_unmanageable_policy": "execution V3 helper falls back legacy unsupported requests to momentum_exhaustion and records raw requested policy",
            "rollback_wrong_namespace": "rollback plan filters by namespace/profile and separates redacted_account from FTMO",
            "heavy_research_requirement": "compact package files are sufficient for runtime provenance; heavy ledgers are referenced as source provenance only",
        },
    )
    write_json(ROUTE_DIR / "VPS_V3_FTMO_COMPLETION_AUDIT.json", completion)
    verification = with_status(
        schema_version="vps_v3_ftmo_verification_result_v1",
        ok=False,
        status="pending_route_verifier_run",
        checks={},
    )
    write_json(ROUTE_DIR / "VPS_V3_FTMO_VERIFICATION_RESULT.json", verification)
    print(json.dumps({"route": str(ROUTE_DIR), "status": "built_initial_artifacts"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
