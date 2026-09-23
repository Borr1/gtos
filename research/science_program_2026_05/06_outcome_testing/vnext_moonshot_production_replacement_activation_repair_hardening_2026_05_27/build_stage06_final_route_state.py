from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-27"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27"
STAGE_ID = "stage_06_commit_and_final_route_state"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
OUTPUT = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE06_FINAL_ROUTE_STATE_{DATE}.json"
SPINE = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE_SPINE_{DATE}.json"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_CONTROL_LEDGER_{DATE}.jsonl"
STAGE03 = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE03_BROKER_RUNTIME_SURFACE_{DATE}.json"
STAGE04 = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE04_CANONICAL_FREQUENCY_TRADE_R_SUMMARY_{DATE}.json"
STAGE05 = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE05_FULL_VERIFICATION_MATRIX_{DATE}.json"
MANIFEST = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
FINAL_PROOF = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_FINAL_SEMANTIC_STATE_PROOF_{DATE}.json"
ANATOMY_MANIFEST = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE07_ANATOMY_INPUT_DEPENDENCY_MANIFEST_{DATE}.json"
EXECUTION_PACKET = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_EXECUTION_INTELLIGENCE_CONTINUATION_PACKET_{DATE}.json"
EXECUTION_SUMMARY = ROUTE_DIR / "ei15r" / "summary.json"
EXECUTION_VERIFIER = ROUTE_DIR / "verify_execution_intelligence_static_15r_ceiling_repair.py"
FINAL_ROUTER_SUMMARY = ROUTE_DIR / "ei15r" / "final_dynamic_router_replay_summary.json"
FINAL_ROUTER_VERIFIER = ROUTE_DIR / "verify_execution_intelligence_dynamic_router_replay.py"
PROMOTION_SUMMARY = ROUTE_DIR / "ei15r" / "momentum_policy_promotion_summary.json"
PROMOTION_VERIFIER = ROUTE_DIR / "verify_execution_policy_momentum_promotion.py"
PROMOTION_RISK_PROOF = ROUTE_DIR / "ei15r" / "selected_policy_risk_proof_summary.json"
PROMOTION_LIFECYCLE_PROOF = ROUTE_DIR / "ei15r" / "momentum_policy_lifecycle_propagation_proof.json"
PROMOTION_VERIFIER_RESULT = ROUTE_DIR / "ei15r" / f"momentum_policy_promotion_verifier_result_{DATE}.json"
LAUNCH_DOSSIER = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_EXECUTION_ROUTER_LAUNCH_DOSSIER_{DATE}.json"
LIVE_STATE = REPO_ROOT / ".context" / "LIVE_STATE.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_check(command_id: str, args: list[str]) -> dict[str, Any]:
    started = datetime.now(timezone.utc).replace(microsecond=0)
    try:
        proc = subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True, timeout=300)
        exit_code = proc.returncode
        stdout_tail = proc.stdout[-4000:]
        stderr_tail = proc.stderr[-4000:]
        status = "passed" if proc.returncode == 0 else "failed"
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        stdout_tail = (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else ""
        stderr_tail = (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else ""
        status = "timeout"
    ended = datetime.now(timezone.utc).replace(microsecond=0)
    return {
        "id": command_id,
        "command": " ".join(args),
        "duration_seconds": round((ended - started).total_seconds(), 3),
        "ended_at_utc": ended.isoformat().replace("+00:00", "Z"),
        "exit_code": exit_code,
        "started_at_utc": started.isoformat().replace("+00:00", "Z"),
        "status": status,
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
    }


def git_head_short_subject() -> str:
    proc = subprocess.run(
        ["git", "log", "-1", "--format=%h %s"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return proc.stdout.strip()


def git_head_full() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return proc.stdout.strip()


def git_head_object() -> dict[str, str]:
    return {
        "full_sha": git_head_full(),
        "short_subject": git_head_short_subject(),
    }


def main() -> int:
    generated_at = utc_now()
    stage03 = read_json(STAGE03)
    stage04 = read_json(STAGE04)
    stage05 = read_json(STAGE05)
    execution_summary = read_json(EXECUTION_SUMMARY) if EXECUTION_SUMMARY.exists() else {}
    final_router = read_json(FINAL_ROUTER_SUMMARY) if FINAL_ROUTER_SUMMARY.exists() else {}
    promotion = read_json(PROMOTION_SUMMARY) if PROMOTION_SUMMARY.exists() else {}
    promotion_risk = read_json(PROMOTION_RISK_PROOF) if PROMOTION_RISK_PROOF.exists() else {}
    promotion_lifecycle = read_json(PROMOTION_LIFECYCLE_PROOF) if PROMOTION_LIFECYCLE_PROOF.exists() else {}
    launch_dossier = read_json(LAUNCH_DOSSIER) if LAUNCH_DOSSIER.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}
    previous_stage06 = read_json(OUTPUT) if OUTPUT.exists() else {}
    previous_head = (
        previous_stage06.get("current_head")
        or previous_stage06.get("current_head_at_artifact_generation")
        or previous_stage06.get("provenance", {}).get("artifact_generation_head")
    )
    checks = [
        run_check(
            "stage06_git_diff_check_non_ei15r_row_ledgers",
            [
                "git",
                "diff",
                "--check",
                "--",
                ".",
                ":(exclude)research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27/ei15r/*.jsonl",
            ],
        ),
    ]
    passed = all(row["status"] == "passed" for row in checks) and stage05.get("status") == "passed"
    if execution_summary.get("selected_rows_processed") != stage04.get("selector_counts", {}).get("combined_selected_rows"):
        passed = False
    if execution_summary.get("dynamic_policy_rows") != stage04.get("selector_counts", {}).get("combined_selected_rows", 0) * 12:
        passed = False
    if final_router.get("selected_rows_processed") != stage04.get("selector_counts", {}).get("combined_selected_rows"):
        passed = False
    if final_router.get("condition_router_projection_gap_carried_forward_rows") != 0:
        passed = False
    if final_router.get("router_refused_rows") != 0:
        passed = False
    if final_router.get("replayable_metric_rows") != stage04.get("selector_counts", {}).get("combined_selected_rows", 0) - final_router.get("non_replayable_rows", 0):
        passed = False
    if promotion.get("selected_rows_processed") != stage04.get("selector_counts", {}).get("combined_selected_rows"):
        passed = False
    if (promotion.get("promotion_decision") or {}).get("primary_policy") != "momentum_exhaustion":
        passed = False
    if (promotion.get("promotion_decision") or {}).get("exception_policy") != "partial_be_runner":
        passed = False
    if ((promotion.get("metrics") or {}).get("promoted_dynamic_router") or {}).get("total_r") != 286221.353599:
        passed = False
    if promotion_risk.get("policy_identity_status_required_in_live_runtime") is not True:
        passed = False
    if promotion_lifecycle.get("production_policy") != "momentum_exhaustion":
        passed = False
    if set(final_router.get("policy_distribution") or {}) != {
        "partial_be_runner",
        "momentum_exhaustion",
    }:
        passed = False
    contract = launch_dossier.get("live_policy_contract") or {}
    if contract.get("every_selected_trade_gets_execution_policy_id") is not True:
        passed = False
    if contract.get("fixed_1_5r_is_default") is not False:
        passed = False
    if contract.get("condition_challenger_enabled") is not True:
        passed = False
    head = git_head_object()
    provenance = {
        "base_input_head": head,
        "previous_package_head": previous_head,
        "artifact_generation_head": head,
        "committed_proof_head": None,
        "expected_head_policy": (
            "artifact_generation_head may be pre-commit; committed proof is "
            "established by running non-mutating verifiers after the repair commit"
        ),
        "committed_proof_head_policy": "post_commit_head_verified_by_non_mutating_route_check",
        "current_verification_head_policy": "may_be_descendant_after_repair_commit",
    }
    final = {
        "schema_version": "vnext_activation_repair_stage06_final_route_state_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "generated_at_utc": generated_at,
        "status": "passed" if passed else "failed",
        "provenance": provenance,
        "current_head_at_artifact_generation": head,
        "manifest_output_count": manifest.get("output_count") or len(manifest.get("outputs") or []),
        "manifest_current_disk_file_count": manifest.get("current_disk_file_count"),
        "live_state_path": rel(LIVE_STATE),
        "live_state_sha256": sha256_file(LIVE_STATE),
        "stage03_status": stage03.get("status"),
        "stage03_discrepancy_reconciliation": stage03.get("discrepancy_reconciliation"),
        "stage04_selector_counts": stage04.get("selector_counts"),
        "stage04_selector_metrics": stage04.get("selector_metrics"),
        "stage04_delta_reconciliation": stage04.get("selector_count_delta_reconciliation"),
        "stage05_status": stage05.get("status"),
        "stage05_command_count": len(stage05.get("commands") or []),
        "stage05_failed_command_ids": [
            row["id"] for row in stage05.get("commands") or [] if row.get("status") != "passed"
        ],
        "stage05_runtime_shards": stage05.get("gtos_vnext_runtime_shards"),
        "final_semantic_state_proof_path": rel(FINAL_PROOF),
        "anatomy_dependency_manifest_path": rel(ANATOMY_MANIFEST),
        "execution_intelligence_continuation_packet_path": rel(EXECUTION_PACKET),
        "execution_intelligence_static_15r_summary_path": rel(EXECUTION_SUMMARY),
        "execution_intelligence_static_15r_verifier_path": rel(EXECUTION_VERIFIER),
        "execution_intelligence_final_dynamic_router_summary_path": rel(FINAL_ROUTER_SUMMARY),
        "execution_intelligence_final_dynamic_router_verifier_path": rel(FINAL_ROUTER_VERIFIER),
        "execution_intelligence_status": execution_summary.get("status"),
        "execution_intelligence_selected_rows_processed": execution_summary.get("selected_rows_processed"),
        "execution_intelligence_dynamic_policy_rows": execution_summary.get("dynamic_policy_rows"),
        "execution_intelligence_ledger_output_format": execution_summary.get("ledger_output_format"),
        "execution_intelligence_dynamic_layer_verdict": execution_summary.get("dynamic_layer_verdict"),
        "execution_intelligence_policy_metrics": {
            key: (execution_summary.get("policy_metrics") or {}).get(key)
            for key in (
                "fixed_1_5r",
                "be_after_trigger",
                "partial_be_runner",
                "trailing_runner",
                "momentum_exhaustion",
                "time_stop",
            )
        },
        "execution_intelligence_outputs": execution_summary.get("outputs"),
        "execution_intelligence_final_dynamic_router_status": final_router.get("status"),
        "execution_intelligence_final_dynamic_router_rows": final_router.get("selected_rows_processed"),
        "execution_intelligence_final_dynamic_router_metric_rows": final_router.get("replayable_metric_rows"),
        "execution_intelligence_final_dynamic_router_non_replayable_rows": final_router.get("non_replayable_rows"),
        "execution_intelligence_final_dynamic_router_refused_rows": final_router.get("router_refused_rows"),
        "execution_intelligence_final_dynamic_router_condition_projection_gap": final_router.get(
            "condition_router_projection_gap_carried_forward_rows"
        ),
        "execution_intelligence_final_dynamic_router_policy_distribution": final_router.get("policy_distribution"),
        "execution_intelligence_final_dynamic_router_metrics": final_router.get("final_dynamic_router_metrics"),
        "execution_intelligence_final_dynamic_router_comparisons": final_router.get("global_policy_comparison_metrics"),
        "execution_intelligence_final_dynamic_router_hindsight_regret": final_router.get("hindsight_best_regret"),
        "execution_intelligence_final_dynamic_router_outputs": final_router.get("outputs"),
        "execution_policy_momentum_promotion_summary_path": rel(PROMOTION_SUMMARY),
        "execution_policy_momentum_promotion_verifier_path": rel(PROMOTION_VERIFIER),
        "execution_policy_momentum_promotion_selected_rows": promotion.get("selected_rows_processed"),
        "execution_policy_momentum_promotion_replayable_rows": promotion.get("replayable_rows"),
        "execution_policy_momentum_promotion_non_replayable_rows": promotion.get("non_replayable_rows"),
        "execution_policy_momentum_promotion_decision": promotion.get("promotion_decision"),
        "execution_policy_momentum_promotion_policy_distribution": promotion.get("policy_distribution"),
        "execution_policy_momentum_promotion_metrics": (
            (promotion.get("metrics") or {}).get("promoted_dynamic_router")
        ),
        "execution_policy_momentum_promotion_deltas": promotion.get("deltas"),
        "selected_policy_risk_proof_summary_path": rel(PROMOTION_RISK_PROOF),
        "lifecycle_propagation_proof_path": rel(PROMOTION_LIFECYCLE_PROOF),
        "launch_execution_router_dossier_path": rel(LAUNCH_DOSSIER),
        "launch_execution_router_status": launch_dossier.get("status"),
        "launch_readiness_verdict": launch_dossier.get("launch_readiness_verdict"),
        "launch_live_policy_contract": contract,
        "launch_universe": launch_dossier.get("launch_universe"),
        "final_checks": checks,
        "closed_gates": [
            "broker_alias_repair_ger_oil",
            "broker_resolved_monitor_tick_parity",
            "redacted_account_risk_broker_geometry_current_specs",
            "pending_notification_parity",
            "cost_slippage_commission_fill_capture",
            "canonical_frequency_executable_trade_ledger",
            "prior_question_anatomy_consumption",
            "rollback_executable_proof",
            "non_mutating_check_mode",
            "stage05_full_verification_matrix",
            "runtime_leakage_no_old_fallback",
            "current_manifest_route_state_verification",
            "execution_intelligence_static_15r_replay_layer",
            "execution_intelligence_plain_jsonl_row_level_ledgers",
            "execution_intelligence_implemented_runtime_policies",
            "execution_intelligence_full_dynamic_router_replay_layer",
            "execution_policy_momentum_primary_promotion",
            "selected_policy_aware_risk_proof",
            "momentum_lifecycle_propagation_proof",
            "live_dynamic_execution_router_launch_dossier",
        ],
        "production_path": (
            "vNext moonshot production replacement remains the production path; no old-system ceiling, "
            "no old PrimaryAnalyzer/L2 fallback, and no narrowed market surface is used for closure."
        ),
        "stage04_static_ceiling_limitation": (
            "Stage04 canonical routing evidence is capped by fixed -1R/0R/+1.5R scoring; "
            "it proves production-replacement routing/frequency/R selection, not dynamic "
            "moonshot execution intelligence beyond the static target."
        ),
    }
    write_json(OUTPUT, final)
    spine = read_json(SPINE)
    spine["current_stage"] = STAGE_ID
    spine["generated_at_utc"] = generated_at
    spine["next_exact_action"] = "Stage06 closed; stage and commit scoped repair artifacts."
    spine.pop("current_head", None)
    spine["provenance"] = provenance
    spine["current_head_at_artifact_generation"] = head
    spine.setdefault("stage_status", {})[STAGE_ID] = "completed" if passed else "failed"
    spine["open_gates"] = []
    active = set(spine.get("active_files") or [])
    active.add(rel(OUTPUT))
    if EXECUTION_SUMMARY.exists():
        active.add(rel(EXECUTION_SUMMARY))
    if FINAL_ROUTER_SUMMARY.exists():
        active.add(rel(FINAL_ROUTER_SUMMARY))
    active.add(rel(EXECUTION_VERIFIER))
    active.add(rel(FINAL_ROUTER_VERIFIER))
    active.add(rel(PROMOTION_SUMMARY))
    active.add(rel(PROMOTION_VERIFIER))
    active.add(rel(PROMOTION_RISK_PROOF))
    active.add(rel(PROMOTION_LIFECYCLE_PROOF))
    if PROMOTION_VERIFIER_RESULT.exists():
        active.add(rel(PROMOTION_VERIFIER_RESULT))
    active.add(rel(ROUTE_DIR / "build_execution_policy_momentum_promotion.py"))
    active.add(rel(ROUTE_DIR / "build_execution_intelligence_static_15r_ceiling_repair.py"))
    active.add(rel(ROUTE_DIR / "build_execution_intelligence_dynamic_router_replay.py"))
    active.add(rel(LAUNCH_DOSSIER))
    active.add(rel(ROUTE_DIR / "build_launch_execution_router_dossier.py"))
    spine["active_files"] = sorted(active)
    spine["execution_intelligence_static_15r"] = {
        "summary_path": rel(EXECUTION_SUMMARY),
        "verifier_path": rel(EXECUTION_VERIFIER),
        "selected_rows_processed": execution_summary.get("selected_rows_processed"),
        "dynamic_policy_rows": execution_summary.get("dynamic_policy_rows"),
        "ledger_output_format": execution_summary.get("ledger_output_format"),
        "dynamic_layer_verdict": execution_summary.get("dynamic_layer_verdict"),
        "policy_metrics": {
            key: (execution_summary.get("policy_metrics") or {}).get(key)
            for key in (
                "fixed_1_5r",
                "be_after_trigger",
                "partial_be_runner",
                "trailing_runner",
                "momentum_exhaustion",
                "time_stop",
            )
        },
    }
    spine["execution_intelligence_final_dynamic_router_replay"] = {
        "role": (
            "post_promotion_live_router_replay"
            if promotion.get("source_dynamic_router_state")
            == "post_promotion_router_already_current"
            else "pre_promotion_mixed_condition_router_replay_diagnostic_not_launch_policy"
        ),
        "summary_path": rel(FINAL_ROUTER_SUMMARY),
        "verifier_path": rel(FINAL_ROUTER_VERIFIER),
        "selected_rows_processed": final_router.get("selected_rows_processed"),
        "replayable_metric_rows": final_router.get("replayable_metric_rows"),
        "non_replayable_rows": final_router.get("non_replayable_rows"),
        "router_refused_rows": final_router.get("router_refused_rows"),
        "condition_router_projection_gap_carried_forward_rows": final_router.get(
            "condition_router_projection_gap_carried_forward_rows"
        ),
        "policy_distribution": final_router.get("policy_distribution"),
        "metrics": final_router.get("final_dynamic_router_metrics"),
        "global_policy_comparisons": final_router.get("global_policy_comparison_metrics"),
        "hindsight_best_regret": final_router.get("hindsight_best_regret"),
    }
    spine["execution_policy_momentum_promotion"] = {
        "summary_path": rel(PROMOTION_SUMMARY),
        "verifier_path": rel(PROMOTION_VERIFIER),
        "selected_policy_risk_proof_summary": rel(PROMOTION_RISK_PROOF),
        "lifecycle_propagation_proof": rel(PROMOTION_LIFECYCLE_PROOF),
        "selected_rows_processed": promotion.get("selected_rows_processed"),
        "replayable_rows": promotion.get("replayable_rows"),
        "non_replayable_rows": promotion.get("non_replayable_rows"),
        "promotion_decision": promotion.get("promotion_decision"),
        "policy_distribution": promotion.get("policy_distribution"),
        "metrics": (promotion.get("metrics") or {}).get("promoted_dynamic_router"),
        "deltas": promotion.get("deltas"),
    }
    spine["launch_execution_router"] = {
        "dossier_path": rel(LAUNCH_DOSSIER),
        "status": launch_dossier.get("status"),
        "launch_readiness_verdict": launch_dossier.get("launch_readiness_verdict"),
        "live_policy_contract": contract,
    }
    write_json(SPINE, spine)
    append_jsonl(
        CONTROL_LEDGER,
        {
            "event": "stage06_final_route_state_written",
            "generated_at_utc": generated_at,
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "status": final["status"],
            "combined_selected_rows": stage04.get("selector_counts", {}).get("combined_selected_rows"),
            "execution_intelligence_dynamic_policy_rows": execution_summary.get("dynamic_policy_rows"),
            "execution_intelligence_best_implemented_policy": (
                execution_summary.get("dynamic_layer_verdict") or {}
            ).get("best_implemented_policy"),
            "execution_intelligence_final_dynamic_router_total_r": (
                final_router.get("final_dynamic_router_metrics") or {}
            ).get("total_r"),
            "execution_intelligence_final_dynamic_router_expectancy_r": (
                final_router.get("final_dynamic_router_metrics") or {}
            ).get("expectancy_r"),
            "execution_policy_momentum_promotion_total_r": (
                (promotion.get("metrics") or {}).get("promoted_dynamic_router") or {}
            ).get("total_r"),
            "execution_policy_momentum_promotion_policy_distribution": promotion.get(
                "policy_distribution"
            ),
            "artifact_generation_head": head,
        },
    )
    print(json.dumps({"status": final["status"], "output": rel(OUTPUT)}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
