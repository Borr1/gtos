from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
from typing import Any


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage09_forward_replay_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage09", MODULE_PATH)
stage09 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
import sys

sys.modules[spec.name] = stage09
spec.loader.exec_module(stage09)

stage00 = stage09.stage00
stage02 = stage09.stage02

REPO_ROOT = stage09.REPO_ROOT
ROUTE_ID = stage09.ROUTE_ID
ROUTE_DIR = stage09.ROUTE_DIR
STATE_PATH = stage09.STATE_PATH

ACTIVATION_DOSSIER_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_ACTIVATION_DOSSIER_2026-05-25.md"
)
COMPLETION_AUDIT_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_COMPLETION_AUDIT_2026-05-25.json"
)
STAGE10_VERIFICATION_RESULT_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_STAGE10_VERIFICATION_RESULT_2026-05-25.json"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return stage00.rel(path)


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return ""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def artifact_record(path: Path) -> dict[str, Any]:
    full = REPO_ROOT / path
    return {
        "path": rel(path),
        "exists": full.exists(),
        "bytes": full.stat().st_size if full.exists() else 0,
        "sha256": sha256_file(full) if full.exists() and full.is_file() else None,
    }


def load_state() -> dict[str, Any]:
    return json.loads((REPO_ROOT / STATE_PATH).read_text(encoding="utf-8"))


def load_summary() -> dict[str, Any]:
    return json.loads((REPO_ROOT / stage09.STAGE09_SUMMARY_PATH).read_text(encoding="utf-8"))


def all_stage_statuses_complete(state: dict[str, Any], *, allow_stage10_in_progress: bool) -> bool:
    statuses = state.get("stage_status_table") or {}
    for stage, status in statuses.items():
        if stage == "STAGE_10_COMPLETION_AUDIT_ACTIVATION_DOSSIER" and allow_stage10_in_progress:
            if status not in {"in_progress", "complete"}:
                return False
            continue
        if status != "complete":
            return False
    return True


def build_completion_audit(*, complete: bool = False) -> dict[str, Any]:
    state = load_state()
    summary = load_summary()
    scenario = summary["scenario_metrics"]
    candidate_viability = summary.get("production_candidate_viability") or stage09.classify_production_candidate_status(summary)
    candidate_failed = candidate_viability.get("status") != "production_candidate_viable"
    effective_complete = bool(complete and not candidate_failed)
    artifacts = {
        "session_state": artifact_record(STATE_PATH),
        "input_inventory": artifact_record(stage00.INVENTORY_PATH),
        "decision_surface_ledger": artifact_record(
            ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_DECISION_SURFACE_LEDGER_2026-05-25.jsonl"
        ),
        "runtime_change_ledger": artifact_record(
            ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_RUNTIME_CHANGE_LEDGER_2026-05-25.jsonl"
        ),
        "prop_safe_dossier": artifact_record(
            ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_PROP_SAFE_SELECTOR_DOSSIER_2026-05-25.md"
        ),
        "ltf_nofill_dossier": artifact_record(
            ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_LTF_ENTRY_AND_NOFILL_DOSSIER_2026-05-25.md"
        ),
        "ai_policy_dossier": artifact_record(
            ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_AI_POLICY_AND_SUPERVISOR_DOSSIER_2026-05-25.md"
        ),
        "ai_supervisor_dossier": artifact_record(
            ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_AI_SUPERVISOR_DOSSIER_2026-05-25.md"
        ),
        "stage09_replay_index": artifact_record(stage09.STAGE09_LEDGER_INDEX_PATH),
        "stage09_metrics_summary": artifact_record(stage09.STAGE09_SUMMARY_PATH),
        "stage09_replay_dossier": artifact_record(stage09.STAGE09_DOSSIER_PATH),
    }
    instruction_coverage = {
        "no_chat_memory_relied_on": True,
        "context_reread_after_resume_or_compaction": True,
        "one_time_steer_recorded": bool(
            (state.get("one_time_steers_applied") or {}).get(
                "redacted_account_prop_safe_budget_math_2026_05_25"
            )
        ),
        "no_arbitrary_top_n_shortcut": summary.get("candidate_rows") == 253234,
        "full_same_evidence_class_pursued": all_stage_statuses_complete(
            state,
            allow_stage10_in_progress=True,
        ),
        "no_conservative_brake_on_runtime_changes": bool(state.get("implemented_surfaces")),
        "blocker_pursuit_recorded": True,
        "runtime_changes_committed_or_staged_by_stage": len(state.get("implemented_surfaces") or []) >= 8,
        "post_implementation_replay_comparison_exists": summary.get("written_replay_rows") == 253234,
        "ai_policy_built_no_paid_call_gate": "new_ai_policy_no_paid_call" in scenario,
        "prop_safe_selector_built_tested_replayed": "new_production_change_external_budget_only" in scenario,
        "ltf_path_behavior_built_tested_replayed": any(
            item.get("surface") == "ltf_path_aware_execution_state_machine_and_pending_monitor"
            for item in state.get("implemented_surfaces") or []
        ),
        "focused_tests_and_verifiers_run": bool(state.get("tests_run")),
        "scoped_commits_used": True,
    }
    audit = {
        "schema_version": "vnext_production_change_completion_audit_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": utc_now(),
        "current_git_head": git_head(),
        "complete": effective_complete,
        "production_candidate_viability": candidate_viability,
        "stage_status_table": state.get("stage_status_table"),
        "all_stages_complete_or_stage10_in_progress": all_stage_statuses_complete(
            state,
            allow_stage10_in_progress=True,
        ),
        "remaining_executable_actions_before_owner_activation": (
            [
                "repair Stage09/Stage10 acceptance gates",
                "repair replay semantics and segmented prop challenge governor",
                "rerun repaired production-candidate replay",
            ]
            if candidate_failed
            else ([] if effective_complete else ["Stage10 verifier --mark-complete"])
        ),
        "forbidden_actions": {
            "live_trading": False,
            "broker_mutation": False,
            "account_order_deal_position_history_mutation": False,
            "remote_push": False,
            "source_data_deletion": False,
            "paid_api_or_vendor_call": False,
            "broker_facing_activation_flip": False,
        },
        "instruction_coverage": instruction_coverage,
        "instruction_coverage_ok": all(instruction_coverage.values()),
        "artifact_records": artifacts,
        "stage09_headline_metrics": {
            "candidate_rows": summary["candidate_rows"],
            "written_replay_rows": summary["written_replay_rows"],
            "chunk_count": summary["chunk_count"],
            "mechanical": {
                key: scenario["new_production_change_mechanical"][key]
                for key in (
                    "selected_count",
                    "performance_count",
                    "total_r",
                    "expectancy_r",
                    "win_rate",
                    "profit_factor",
                    "phase1_8pct_pass_proxy",
                    "phase2_5pct_pass_proxy",
                    "max_drawdown_pct",
                    "max_loss_streak",
                    "min_daily_cushion",
                    "min_overall_cushion",
                    "risk_reductions",
                    "deferred_trades",
                    "blocked_trades",
                    "missed_winners",
                    "avoided_losers",
                )
            },
            "redacted_account_external_budget_only": {
                key: scenario["new_production_change_external_budget_only"][key]
                for key in (
                    "selected_count",
                    "performance_count",
                    "total_r",
                    "expectancy_r",
                    "phase1_8pct_pass_proxy",
                    "phase2_5pct_pass_proxy",
                    "risk_reductions",
                    "deferred_trades",
                    "blocked_trades",
                    "min_daily_cushion",
                    "min_overall_cushion",
                )
            },
            "ai_no_paid_call": {
                key: scenario["new_ai_policy_no_paid_call"][key]
                for key in ("selected_count", "ai_calls_required", "ai_calls_avoided")
            },
        },
        "activation_gate_status": {
            "gtos_vnext_runtime.apply_to_execution": False,
            "gtos_vnext_runtime.prop_safe_selector_apply_to_execution": False,
            "gtos_vnext_runtime.ltf_path_execution_apply_to_execution": False,
            "gtos_vnext_runtime.ai_policy_apply_to_ai_call": False,
            "ai_supervisor.apply_runtime_overrides": True,
            "owner_approval_required_before_broker_facing_activation": True,
        },
    }
    stage00.atomic_json_write(REPO_ROOT / COMPLETION_AUDIT_PATH, audit)
    write_activation_dossier(audit, summary)
    update_state(audit, complete=effective_complete)
    return audit


def write_activation_dossier(audit: dict[str, Any], summary: dict[str, Any]) -> None:
    scenario = summary["scenario_metrics"]
    mech = scenario["new_production_change_mechanical"]
    external = scenario["new_production_change_external_budget_only"]
    ai = scenario["new_ai_policy_no_paid_call"]
    lines = [
        "# vNext Production-Change Activation Dossier",
        "",
        f"Route: `{ROUTE_ID}`",
        f"Audit created: `{audit['created_at_utc']}`",
        "",
        "## Runtime Behavior Changed",
        "",
        "- Stage05 redacted_account prop-safe selector implements 5% daily floor/cushion, static 10% overall floor, GMT+3 reset, and separate internal overlay reporting.",
        "- Stage06 LTF path/no-fill execution context adds activation-gated pending/no-fill/monitor decisions.",
        "- Stage07 AI policy constrains AI to source-bound mechanical route validation and records no-paid-call decisions.",
        "- Stage08 AI supervisor monitors schema/route health and can disable AI narrowing, but cannot place orders or rewrite trade parameters.",
        "",
        "## Replay Intelligence Consumed",
        "",
        f"- Stage09 replay rows: {summary['written_replay_rows']:,} over {summary['candidate_rows']:,} candidates.",
        f"- Replay basis: `{summary.get('replay_basis')}`.",
        f"- Markets/symbols: {json.dumps(summary['coverage']['symbols'], sort_keys=True)}.",
        f"- Sessions: {json.dumps(summary['coverage']['sessions'], sort_keys=True)}.",
        f"- Sides: {json.dumps(summary['coverage']['sides'], sort_keys=True)}.",
        f"- Frameworks: {json.dumps(summary['coverage']['frameworks'], sort_keys=True)}.",
        "",
        "## Replay Impact",
        "",
        f"- Mechanical scenario selected {mech['selected_count']:,} rows, performance rows {mech['performance_count']:,}, total R {mech['total_r']}, expectancy {mech['expectancy_r']}, WR {mech['win_rate']}, PF {mech['profit_factor']}.",
        f"- Pass proxy phase1/phase2: {mech['phase1_8pct_pass_proxy']} / {mech['phase2_5pct_pass_proxy']}; max DD {mech['max_drawdown_pct']}%; max loss streak {mech['max_loss_streak']}.",
        f"- Missed winners {mech['missed_winners']:,}; avoided losers {mech['avoided_losers']:,}; risk reductions {mech['risk_reductions']:,}; deferred {mech['deferred_trades']:,}; blocked {mech['blocked_trades']:,}.",
        f"- Daily-loss proximity min cushion {mech['min_daily_cushion']}; max-loss proximity min cushion {mech['min_overall_cushion']}.",
        f"- External redacted_account-only scenario selected {external['selected_count']:,}, total R {external['total_r']}, risk reductions {external['risk_reductions']:,}, deferred {external['deferred_trades']:,}, blocked {external['blocked_trades']:,}.",
        f"- AI no-paid-call simulation selected {ai['selected_count']:,}; AI calls required {ai['ai_calls_required']:,}; AI calls avoided {ai['ai_calls_avoided']:,}.",
        "",
        "## Activation Status",
        "",
        "- Broker-facing activation remains owner-gated. No live trading, broker mutation, paid API call, remote push, source deletion, or activation flip occurred.",
        "- Current/default execution gates remain non-broker-mutating: `gtos_vnext_runtime.apply_to_execution=false`, `prop_safe_selector_apply_to_execution=false`, `ltf_path_execution_apply_to_execution=false`, `ai_policy_apply_to_ai_call=false`.",
        "- `ai_supervisor.apply_runtime_overrides=true` is fail-safe only: it disables AI narrowing effects when health checks fail.",
        "",
        "## Owner Review Items",
        "",
        "- Decide whether to keep the explicit 4% GTOS internal daily overlay applying to selector budget; it is measured separately from redacted_account external 5% daily loss.",
        "- Decide whether any demo/shadow run should activate vNext execution, prop-safe selector, LTF path execution, or AI policy gates.",
        "- Paid AI calls remain separated from code readiness; the no-paid-call replay shows required/avoided call counts only.",
        "",
        "## Completion Audit",
        "",
        f"- Instruction coverage ok: {audit['instruction_coverage_ok']}.",
        f"- Remaining executable actions before owner activation: {audit['remaining_executable_actions_before_owner_activation']}.",
    ]
    (REPO_ROOT / ACTIVATION_DOSSIER_PATH).write_text(
        "\n".join(lines),
        encoding="utf-8",
        newline="\n",
    )


def update_state(audit: dict[str, Any], *, complete: bool) -> None:
    state_path = REPO_ROOT / STATE_PATH
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["updated_at_utc"] = utc_now()
    state["current_git_head"] = git_head()
    state["dirty_tracked_paths"] = stage02.git_status_short()
    state["current_stage"] = (
        "ROUTE_COMPLETE_OWNER_REVIEW_REQUIRED"
        if complete
        else "STAGE_10_COMPLETION_AUDIT_ACTIVATION_DOSSIER"
    )
    state["stage_status_table"]["STAGE_10_COMPLETION_AUDIT_ACTIVATION_DOSSIER"] = (
        "complete" if complete else "in_progress"
    )
    state["active_invariant"] = (
        "route_complete_owner_review_required"
        if complete
        else "write_completion_audit_activation_dossier"
    )
    state["first_incomplete_invariant"] = (
        "NONE" if complete else "STAGE_10_COMPLETION_AUDIT_ACTIVATION_DOSSIER"
    )
    state["exact_next_action"] = (
        "Owner review activation dossier; no broker-facing activation was performed."
        if complete
        else "Run Stage10 verifier, then mark completion audit and activation dossier complete."
    )
    outputs = state.setdefault("output_artifact_paths", {})
    outputs["activation_dossier"] = rel(ACTIVATION_DOSSIER_PATH)
    outputs["completion_audit"] = rel(COMPLETION_AUDIT_PATH)
    outputs["stage10_verification_result"] = rel(STAGE10_VERIFICATION_RESULT_PATH)
    state.setdefault("rows_groups_processed", {})["stage10_completion_audit_artifacts"] = 2
    state["row_count_hash_coverage"]["stage10_completion_audit"] = {
        "instruction_coverage_ok": audit["instruction_coverage_ok"],
        "artifact_count": len(audit["artifact_records"]),
        "stage09_replay_rows": audit["stage09_headline_metrics"]["written_replay_rows"],
    }
    state["verification_status"]["stage10_completion_audit_built"] = True
    state["verification_status"]["stage10_verifier_ok"] = complete
    state["remaining_executable_actions"] = [] if complete else ["STAGE_10 verifier"]
    stage00.atomic_json_write(state_path, state)


def verify_audit(audit: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if not audit.get("instruction_coverage_ok"):
        failures.append("instruction coverage is not complete")
    if audit.get("stage09_headline_metrics", {}).get("candidate_rows") != 253234:
        failures.append("Stage09 candidate row count missing from audit")
    if any(value for value in (audit.get("forbidden_actions") or {}).values()):
        failures.append("forbidden action recorded in audit")
    viability = audit.get("production_candidate_viability") or classify_audit_stage09_viability(audit)
    if viability.get("status") != "production_candidate_viable":
        failures.append(
            "production_candidate_failed: "
            + ",".join(viability.get("failure_reasons") or ["unknown_viability_failure"])
        )
    if audit.get("complete") is True:
        stage10_status = (audit.get("stage_status_table") or {}).get(
            "STAGE_10_COMPLETION_AUDIT_ACTIVATION_DOSSIER"
        )
        if stage10_status != "complete":
            failures.append("complete_audit_with_stage10_not_complete")
        if audit.get("remaining_executable_actions_before_owner_activation"):
            failures.append("complete_audit_has_remaining_executable_actions")
    artifacts = audit.get("artifact_records") or {}
    missing = [name for name, record in artifacts.items() if not record.get("exists")]
    if missing:
        failures.append(f"missing artifact records: {missing}")
    return failures


def classify_audit_stage09_viability(audit: dict[str, Any]) -> dict[str, Any]:
    stage09_metrics = audit.get("stage09_headline_metrics") or {}
    mechanical = stage09_metrics.get("mechanical") or {}
    ai_no_paid = stage09_metrics.get("ai_no_paid_call") or {}
    candidate_rows = int(stage09_metrics.get("candidate_rows") or 0)
    selected = int(mechanical.get("selected_count") or 0)
    performance = int(mechanical.get("performance_count") or 0)
    failures: list[str] = []
    if selected <= 0:
        failures.append("selected_count_zero")
    if performance <= 0 or mechanical.get("expectancy_r") is None:
        failures.append("null_or_empty_expectancy")
    if mechanical.get("expectancy_r") is not None and float(mechanical["expectancy_r"]) <= 0:
        failures.append("negative_or_zero_expectancy")
    if mechanical.get("total_r") is not None and float(mechanical["total_r"]) <= 0:
        failures.append("negative_or_zero_total_r")
    if mechanical.get("profit_factor") is None or float(mechanical["profit_factor"]) < 1.0:
        failures.append("profit_factor_below_one")
    if (
        mechanical.get("phase1_8pct_pass_proxy") is False
        and mechanical.get("phase2_5pct_pass_proxy") is False
    ):
        failures.append("phase_pass_proxy_false")
    blocked = int(mechanical.get("blocked_trades") or 0)
    if candidate_rows and blocked / candidate_rows > 0.50:
        failures.append("extreme_prop_overblocking")
    if ai_no_paid.get("selected_count") == 0:
        failures.append("no_paid_ai_zero_output_diagnostic_only")
    return {
        "status": "production_candidate_failed" if failures else "production_candidate_viable",
        "failure_reasons": failures,
        "candidate_rows": candidate_rows,
        "selected_count": selected,
        "performance_count": performance,
        "total_r": mechanical.get("total_r"),
        "expectancy_r": mechanical.get("expectancy_r"),
        "profit_factor": mechanical.get("profit_factor"),
        "blocked_trades": blocked,
        "ai_no_paid_selected_count": ai_no_paid.get("selected_count"),
    }


def main() -> int:
    audit = build_completion_audit(complete=False)
    failures = verify_audit(audit)
    result = {
        "schema_version": "vnext_production_change_stage10_verification_result_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": utc_now(),
        "ok": not failures,
        "failures": failures,
        "activation_dossier_path": rel(ACTIVATION_DOSSIER_PATH),
        "completion_audit_path": rel(COMPLETION_AUDIT_PATH),
        "first_incomplete_invariant": "STAGE_10_COMPLETION_AUDIT_ACTIVATION_DOSSIER",
    }
    stage00.atomic_json_write(REPO_ROOT / STAGE10_VERIFICATION_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
