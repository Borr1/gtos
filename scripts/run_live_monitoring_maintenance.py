#!/usr/bin/env python3
"""Run the read-only live-shadow maintenance chain.

This is the self-sustaining wrapper for the manual daily monitoring sequence.
It refreshes candidate path rows, appends dependent audit/status rows, and then
reruns the integrity and semantic health reports.

It does not call AI, canaries, broker order placement/cancel code, or paid data
fetchers. MT5 reads can still happen in the path/account/pulse lanes because
those are observation-only maintenance checks.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.safety.runtime_halt import read_runtime_halt_state

DEFAULT_RUN_LOG = Path("shadow_logs/live_monitoring_maintenance_runs.jsonl")
DEFAULT_STATE = Path("pipeline_state/live_monitoring_maintenance_state.json")
DEFAULT_MAX_HOURS = 24.0
DEFAULT_STEP_TIMEOUT_SECONDS = 900
RUNTIME_HALT_CONFIG = {
    "runtime_control": {
        "enabled": True,
        "audit_log_path": "pipeline_state/runtime_control_atomic_halt_audit.jsonl",
    }
}
DUAL_BROKER_HEARTBEAT_PATHS = (
    Path("pipeline_state/daemon_heartbeat_dual_broker_trade_record_projector_redacted_account_live_bee34003.json"),
    Path("pipeline_state/daemon_heartbeat_dual_broker_execution_follower_operator_profile.json"),
)
DUAL_BROKER_HEARTBEAT_MAX_AGE_SECONDS = 300.0


@dataclass(frozen=True)
class Step:
    name: str
    args: list[str]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def write_json(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(row, indent=2, sort_keys=True, default=str), encoding="utf-8")


def _tail(text: str, *, limit: int = 6000) -> str:
    text = text.strip()
    return text[-limit:] if len(text) > limit else text


def _json_from_stdout(stdout: str) -> dict[str, Any] | None:
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        return parsed if isinstance(parsed, dict) else None
    return None


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _heartbeat_time(path: Path) -> datetime | None:
    target = path if path.is_absolute() else ROOT / path
    if not target.exists():
        return None
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    for key in ("utc", "liveness_utc", "last_progress_utc"):
        raw = data.get(key) if isinstance(data, dict) else None
        if not raw:
            continue
        try:
            parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except ValueError:
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    return None


def dual_broker_activation_guard_active(
    *,
    max_age_seconds: float = DUAL_BROKER_HEARTBEAT_MAX_AGE_SECONDS,
) -> dict[str, Any]:
    if _truthy(os.environ.get("GTOS_ALLOW_LIVE_MONITORING_MAINTENANCE_WITH_DUAL_BROKER")):
        return {"active": False, "reason": "override_env_allows_maintenance"}
    if not _truthy(os.environ.get("GTOS_SUPPRESS_LIVE_MONITORING_MAINTENANCE_WITH_DUAL_BROKER")):
        return {
            "active": False,
            "reason": "dual_broker_heartbeat_observation_only_default_allows_maintenance",
        }
    now = datetime.now(timezone.utc)
    for path in DUAL_BROKER_HEARTBEAT_PATHS:
        stamp = _heartbeat_time(path)
        if stamp is None:
            continue
        age = (now - stamp).total_seconds()
        if age <= max_age_seconds:
            return {
                "active": True,
                "reason": "dual_broker_activation_heartbeat_recent",
                "heartbeat_path": str(path),
                "heartbeat_age_seconds": round(age, 3),
            }
    return {"active": False, "reason": "no_recent_dual_broker_heartbeat"}


def final_dependency_catchup_steps(*, max_hours: float) -> list[Step]:
    """Refresh candidate-driven audit rows immediately before final verifiers.

    During active kill zones, production writers can append new candidate rows
    while the longer maintenance chain is still running. A final idempotent
    catch-up pass keeps the integrity verifier from observing legitimate fresh
    candidates before their dependent audit/status rows exist.
    """

    return [
        Step("final_live_shadow_gap_closure", ["scripts/close_live_shadow_capture_gaps.py", "--max-hours", str(max_hours)]),
        Step("final_ai_narrowing_policy_shadow_evaluations", ["scripts/backfill_ai_narrowing_policy_shadow_evaluations.py"]),
        Step("final_candidate_registry_audit", ["scripts/backfill_candidate_registry_audit.py"]),
        Step("final_candidate_path_contract_audit", ["scripts/backfill_candidate_path_contract_audit.py"]),
        Step("final_opportunity_lifecycle_audit", ["scripts/backfill_opportunity_lifecycle_audit.py"]),
        Step(
            "final_pending_limit_lifecycle_audit",
            ["scripts/backfill_pending_limit_lifecycle_audit.py", "--decision-date-prefix", "all"],
        ),
        Step("final_v2b_forward_pair_resolution_audit", ["scripts/backfill_v2b_forward_pair_resolution_audit.py"]),
        Step("final_prefill_delivery_path_audit", ["scripts/backfill_prefill_delivery_path_audit.py"]),
        Step(
            "final_fvg_ob_confluence_source_geometry",
            ["scripts/backfill_fvg_ob_confluence_source_geometry.py"],
        ),
        Step("final_fvg_ob_confluence_audit", ["scripts/backfill_fvg_ob_confluence_audit.py"]),
        Step("final_context_control_audit", ["scripts/backfill_context_control_audit.py"]),
        Step("final_broker_actual_r_audit", ["scripts/backfill_broker_actual_r_audit.py"]),
        Step("final_j46_j49_exit_comparator_audit", ["scripts/backfill_j46_j49_exit_comparator_audit.py"]),
        Step("final_s79_side_aware_risk_context", ["scripts/backfill_s79_side_aware_risk_context.py"]),
        Step("final_regime_decay_outcome_join", ["scripts/backfill_regime_decay_outcome_join.py"]),
        Step("final_decision_layer_diagnostics_join", ["scripts/backfill_decision_layer_diagnostics_join.py"]),
        Step("final_mechanical_context_diagnostics_join", ["scripts/backfill_mechanical_context_diagnostics_join.py"]),
        Step("final_k55_ml_shadow_predictions", ["scripts/backfill_k55_ml_shadow_predictions.py"]),
        Step("final_exit_management_no_event_status", ["scripts/backfill_exit_management_no_event_status.py"]),
        Step("final_trade_index_lifecycle_audit", ["scripts/backfill_trade_index_lifecycle_audit.py"]),
        Step("final_v2_structural_selector_readiness", ["scripts/audit_v2_structural_selector_readiness.py"]),
        Step("final_xauusd_same_market_extension", ["scripts/audit_xauusd_same_market_extension.py"]),
    ]


def base_steps(
    *,
    max_hours: float,
    sierra_mode: str,
    skip_live_pulse: bool,
    skip_shadow_observer_once: bool,
) -> list[Step]:
    steps: list[Step] = []
    if not skip_live_pulse:
        steps.append(Step("live_monitor_pulse", ["scripts/_live_monitor_iter.py"]))
    steps.append(Step("follow_candidate_paths", ["scripts/follow_live_candidate_paths.py", "--max-hours", str(max_hours)]))
    steps.append(Step("post_follow_live_shadow_gap_closure", ["scripts/close_live_shadow_capture_gaps.py", "--max-hours", str(max_hours)]))
    steps.append(Step("ai_narrowing_policy_shadow_evaluations", ["scripts/backfill_ai_narrowing_policy_shadow_evaluations.py"]))
    if not skip_shadow_observer_once:
        steps.append(
            Step(
                "shadow_observer_once",
                ["scripts/run_shadow_observer.py", "--mode", "live", "--profile", "redacted_account", "--once"],
            )
        )

    steps.extend(
        [
            Step("candidate_registry_audit", ["scripts/backfill_candidate_registry_audit.py"]),
            Step("candidate_path_contract_audit", ["scripts/backfill_candidate_path_contract_audit.py"]),
            Step("opportunity_lifecycle_audit", ["scripts/backfill_opportunity_lifecycle_audit.py"]),
            Step(
                "pending_limit_lifecycle_audit",
                ["scripts/backfill_pending_limit_lifecycle_audit.py", "--decision-date-prefix", "all"],
            ),
            Step("v2b_forward_pair_resolution_audit", ["scripts/backfill_v2b_forward_pair_resolution_audit.py"]),
            Step("prefill_delivery_path_audit", ["scripts/backfill_prefill_delivery_path_audit.py"]),
            Step("fvg_ob_confluence_source_geometry", ["scripts/backfill_fvg_ob_confluence_source_geometry.py"]),
            Step("fvg_ob_confluence_audit", ["scripts/backfill_fvg_ob_confluence_audit.py"]),
            Step("context_control_audit", ["scripts/backfill_context_control_audit.py"]),
            Step("broker_actual_r_audit", ["scripts/backfill_broker_actual_r_audit.py"]),
            Step("v2_structural_selector_readiness", ["scripts/audit_v2_structural_selector_readiness.py"]),
            Step("j46_j49_exit_comparator_audit", ["scripts/backfill_j46_j49_exit_comparator_audit.py"]),
            Step("s79_side_aware_risk_context", ["scripts/backfill_s79_side_aware_risk_context.py"]),
            Step("regime_decay_outcome_join", ["scripts/backfill_regime_decay_outcome_join.py"]),
            Step("decision_layer_diagnostics_join", ["scripts/backfill_decision_layer_diagnostics_join.py"]),
            Step("mechanical_context_diagnostics_join", ["scripts/backfill_mechanical_context_diagnostics_join.py"]),
            Step("lto_blocked_lane_readiness", ["scripts/audit_lto_blocked_lane_readiness.py"]),
            Step("xauusd_same_market_extension", ["scripts/audit_xauusd_same_market_extension.py"]),
            Step("es_mes_preregistration", ["scripts/audit_es_mes_preregistration.py"]),
            Step("account_pnl_truth_reconciliation", ["scripts/backfill_account_pnl_truth_reconciliation.py"]),
            Step("trade_index_lifecycle_audit", ["scripts/backfill_trade_index_lifecycle_audit.py"]),
            Step("sierra_proxy_registry", ["scripts/audit_sierra_proxy_registry.py"]),
        ]
    )
    steps.append(Step("shadow_observer_hardening", ["scripts/audit_shadow_observer_hardening.py"]))

    if sierra_mode == "pending-status-only":
        steps.append(
            Step(
                "sierra_depth_pending_status",
                [
                    "scripts/enrich_sierra_live_candidate_depth_features.py",
                    "--max-hours",
                    str(max_hours),
                    "--pending-status-only",
                ],
            )
        )
    elif sierra_mode == "bounded-full":
        steps.append(
            Step(
                "sierra_depth_bounded_full",
                [
                    "scripts/enrich_sierra_live_candidate_depth_features.py",
                    "--max-hours",
                    str(max_hours),
                    "--max-file-size-mb",
                    "128",
                    "--max-per-symbol",
                    "2",
                    "--limit",
                    "6",
                ],
            )
        )

    steps.extend(
        [
            Step("sierra_live_depth_confluence", ["scripts/audit_sierra_live_depth_confluence.py"]),
            Step("nas100_orderflow_adverse_selection", ["scripts/audit_nas100_orderflow_adverse_selection.py"]),
            Step("gbpjpy_orderflow_proxy_gap", ["scripts/audit_gbpjpy_orderflow_proxy_gap.py"]),
            Step("sierra_6b_si_depth_policy", ["scripts/audit_sierra_6b_si_depth_policy.py"]),
            Step("orderflow_primitives", ["scripts/audit_orderflow_primitives.py"]),
            Step("k55_ml_shadow_predictions", ["scripts/backfill_k55_ml_shadow_predictions.py"]),
            Step("exit_management_no_event_status", ["scripts/backfill_exit_management_no_event_status.py"]),
            Step("session_volatility_sweep_status", ["scripts/audit_session_volatility_sweep_status.py"]),
            Step("notification_queue_dead_zone", ["scripts/audit_notification_queue_dead_zone.py"]),
            Step("storage_retention_dry_run", ["scripts/audit_storage_retention.py", "--dry-run"]),
            *final_dependency_catchup_steps(max_hours=max_hours),
            Step("summarize_live_shadow_opportunities", ["scripts/summarize_live_shadow_opportunities.py"]),
            Step(
                "final_shadow_observer_once",
                ["scripts/run_shadow_observer.py", "--mode", "live", "--profile", "redacted_account", "--once"],
            ),
            Step("final_shadow_observer_hardening", ["scripts/audit_shadow_observer_hardening.py"]),
            Step("verify_shadow_log_integrity", ["scripts/verify_shadow_log_integrity.py"]),
            Step("audit_live_shadow_data_health", ["scripts/audit_live_shadow_data_health.py"]),
        ]
    )
    return steps


def run_step(step: Step, *, timeout_seconds: int) -> dict[str, Any]:
    command = [sys.executable, *step.args]
    started = utc_now_iso()
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        finished = utc_now_iso()
        parsed = _json_from_stdout(completed.stdout)
        return {
            "name": step.name,
            "started_at_utc": started,
            "finished_at_utc": finished,
            "returncode": completed.returncode,
            "command": command,
            "stdout_tail": _tail(completed.stdout),
            "stderr_tail": _tail(completed.stderr),
            "parsed_stdout_json": parsed,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "name": step.name,
            "started_at_utc": started,
            "finished_at_utc": utc_now_iso(),
            "returncode": None,
            "command": command,
            "stdout_tail": _tail(exc.stdout or ""),
            "stderr_tail": _tail(exc.stderr or ""),
            "timeout_seconds": timeout_seconds,
            "error": "TIMEOUT",
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-hours", type=float, default=DEFAULT_MAX_HOURS)
    parser.add_argument("--step-timeout-seconds", type=int, default=DEFAULT_STEP_TIMEOUT_SECONDS)
    parser.add_argument("--skip-live-pulse", action="store_true")
    parser.add_argument("--skip-shadow-observer-once", action="store_true")
    parser.add_argument(
        "--sierra-mode",
        choices=("pending-status-only", "bounded-full", "skip"),
        default="pending-status-only",
    )
    parser.add_argument("--run-log", type=Path, default=DEFAULT_RUN_LOG)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--fail-fast", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    guard = dual_broker_activation_guard_active()
    if guard.get("active"):
        result = {
            "schema_version": "live_monitoring_maintenance_run_v1",
            "started_at_utc": utc_now_iso(),
            "finished_at_utc": utc_now_iso(),
            "status": "skipped",
            "reason": "dual_broker_activation_guard_suppressed_widening_maintenance",
            "guard": guard,
            "steps": [],
        }
        append_jsonl(args.run_log, result)
        write_json(args.state, result)
        print(json.dumps(result, sort_keys=True))
        return 0
    halt_snapshot = read_runtime_halt_state(RUNTIME_HALT_CONFIG, repo_root=ROOT)
    if halt_snapshot.active:
        result = {
            "schema_version": "live_monitoring_maintenance_run_v1",
            "created_at_utc": utc_now_iso(),
            "status": halt_snapshot.status.upper(),
            "reason": "live monitoring maintenance disabled while runtime halt is active",
            "halt_flags": halt_snapshot.to_dict().get("active_flags", []),
            "steps_run": 0,
        }
        append_jsonl(args.run_log, result)
        write_json(args.state, result)
        print(json.dumps(result, sort_keys=True))
        return 0
    started = utc_now_iso()
    step_results: list[dict[str, Any]] = []
    for step in base_steps(
        max_hours=args.max_hours,
        sierra_mode=args.sierra_mode,
        skip_live_pulse=args.skip_live_pulse,
        skip_shadow_observer_once=args.skip_shadow_observer_once,
    ):
        result = run_step(step, timeout_seconds=args.step_timeout_seconds)
        step_results.append(result)
        if args.fail_fast and result.get("returncode") not in (0,):
            break

    failures = [result for result in step_results if result.get("returncode") not in (0,)]
    final_integrity = next(
        (result.get("parsed_stdout_json") for result in reversed(step_results) if result.get("name") == "verify_shadow_log_integrity"),
        None,
    )
    final_data_health = next(
        (result.get("parsed_stdout_json") for result in reversed(step_results) if result.get("name") == "audit_live_shadow_data_health"),
        None,
    )
    status = "ACTION_REQUIRED" if failures else "MAINTENANCE_SEQUENCE_COMPLETED"
    summary = {
        "schema_version": "live_monitoring_maintenance_run_v1",
        "created_at_utc": utc_now_iso(),
        "started_at_utc": started,
        "status": status,
        "max_hours": args.max_hours,
        "sierra_mode": args.sierra_mode,
        "shadow_observer_once": not args.skip_shadow_observer_once,
        "steps_run": len(step_results),
        "failed_steps": [result["name"] for result in failures],
        "final_integrity": final_integrity,
        "final_data_health": final_data_health,
        "no_ai_calls": True,
        "no_execution": True,
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
        "steps": step_results,
    }
    append_jsonl(args.run_log, summary)
    write_json(args.state, summary)
    print(
        json.dumps(
            {
                "status": status,
                "steps_run": len(step_results),
                "failed_steps": [result["name"] for result in failures],
                "final_integrity_status": (final_integrity or {}).get("overall_status"),
                "final_data_health_status": (final_data_health or {}).get("status"),
                "state": str(args.state),
                "run_log": str(args.run_log),
            },
            sort_keys=True,
        )
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
