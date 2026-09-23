from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


DATE = "2026-05-27"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
SPINE = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE_SPINE_{DATE}.json"
STAGE03 = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE03_BROKER_RUNTIME_SURFACE_{DATE}.json"
STAGE04_SUMMARY = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE04_CANONICAL_FREQUENCY_TRADE_R_SUMMARY_{DATE}.json"
STAGE05 = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE05_FULL_VERIFICATION_MATRIX_{DATE}.json"
STAGE06 = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE06_FINAL_ROUTE_STATE_{DATE}.json"
MANIFEST = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_CONTROL_LEDGER_{DATE}.jsonl"
FINAL_PROOF = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_FINAL_SEMANTIC_STATE_PROOF_{DATE}.json"
ANATOMY_MANIFEST = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE07_ANATOMY_INPUT_DEPENDENCY_MANIFEST_{DATE}.json"
EXECUTION_PACKET = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_EXECUTION_INTELLIGENCE_CONTINUATION_PACKET_{DATE}.json"
EXECUTION_SUMMARY = ROUTE_DIR / "ei15r" / "summary.json"
EXECUTION_BUILDER = ROUTE_DIR / "build_execution_intelligence_static_15r_ceiling_repair.py"
EXECUTION_VERIFIER = ROUTE_DIR / "verify_execution_intelligence_static_15r_ceiling_repair.py"
FINAL_ROUTER_SUMMARY = ROUTE_DIR / "ei15r" / "final_dynamic_router_replay_summary.json"
FINAL_ROUTER_BUILDER = ROUTE_DIR / "build_execution_intelligence_dynamic_router_replay.py"
FINAL_ROUTER_VERIFIER = ROUTE_DIR / "verify_execution_intelligence_dynamic_router_replay.py"
PROMOTION_SUMMARY = ROUTE_DIR / "ei15r" / "momentum_policy_promotion_summary.json"
PROMOTION_VERIFIER = ROUTE_DIR / "verify_execution_policy_momentum_promotion.py"
PROMOTION_RISK_PROOF = ROUTE_DIR / "ei15r" / "selected_policy_risk_proof_summary.json"
PROMOTION_LIFECYCLE_PROOF = ROUTE_DIR / "ei15r" / "momentum_policy_lifecycle_propagation_proof.json"
PROMOTION_VERIFIER_RESULT = ROUTE_DIR / "ei15r" / f"momentum_policy_promotion_verifier_result_{DATE}.json"
LAUNCH_DOSSIER = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_EXECUTION_ROUTER_LAUNCH_DOSSIER_{DATE}.json"
ACTIVATION_MAP = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_moonshot_production_replacement_activation_2026_05_26/"
    / "VNEXT_REPLACEMENT_MARKET_SOURCE_ACTIVATION_MAP_2026-05-26.json"
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def git_is_ancestor(base: str | None, current: str) -> bool:
    if not base:
        return False
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", base, current],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return proc.returncode == 0


def run_json_check(args: list[str]) -> tuple[dict[str, Any] | None, str]:
    proc = subprocess.run(
        args,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=900,
    )
    stdout = proc.stdout.strip()
    try:
        return json.loads(stdout.splitlines()[-1]), proc.stderr.strip()
    except (IndexError, json.JSONDecodeError):
        return None, stdout[-2000:] + proc.stderr[-2000:]


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def text_contains(path: Path, needle: str) -> bool:
    if not path.exists() or not path.is_file():
        return False
    try:
        return needle in path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False


def provenance_from(*payloads: dict[str, Any]) -> dict[str, Any]:
    for payload in payloads:
        provenance = payload.get("provenance")
        if isinstance(provenance, dict):
            return provenance
    return {}


def head_full_from(value: Any) -> str | None:
    if isinstance(value, dict):
        text = value.get("full_sha") or value.get("sha")
        return str(text) if text else None
    if isinstance(value, str) and value:
        return value.split()[0]
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if not args.check:
        raise SystemExit("--check is required; verifier is non-mutating")

    spine = read_json(SPINE)
    stage04 = read_json(STAGE04_SUMMARY)
    stage03 = read_json(STAGE03) if STAGE03.exists() else {}
    stage05 = read_json(STAGE05) if STAGE05.exists() else {}
    stage06 = read_json(STAGE06) if STAGE06.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}
    final_proof = read_json(FINAL_PROOF) if FINAL_PROOF.exists() else {}
    anatomy = read_json(ANATOMY_MANIFEST) if ANATOMY_MANIFEST.exists() else {}
    execution_packet = read_json(EXECUTION_PACKET) if EXECUTION_PACKET.exists() else {}
    execution_summary = read_json(EXECUTION_SUMMARY) if EXECUTION_SUMMARY.exists() else {}
    final_router = read_json(FINAL_ROUTER_SUMMARY) if FINAL_ROUTER_SUMMARY.exists() else {}
    promotion = read_json(PROMOTION_SUMMARY) if PROMOTION_SUMMARY.exists() else {}
    promotion_risk = read_json(PROMOTION_RISK_PROOF) if PROMOTION_RISK_PROOF.exists() else {}
    promotion_lifecycle = read_json(PROMOTION_LIFECYCLE_PROOF) if PROMOTION_LIFECYCLE_PROOF.exists() else {}
    launch_dossier = read_json(LAUNCH_DOSSIER) if LAUNCH_DOSSIER.exists() else {}
    issues: list[str] = []
    completed = set(spine.get("completed_gates") or [])
    open_gates = set(spine.get("open_gates") or [])
    overlap = completed & open_gates
    if overlap:
        issues.append(f"gate_in_completed_and_open:{sorted(overlap)}")
    for gate in ("canonical_frequency_executable_trade_ledger", "prior_question_anatomy_consumption"):
        if gate not in completed:
            issues.append(f"missing_completed_gate:{gate}")
    if spine.get("current_stage") not in {"stage_05_full_verification_matrix", "stage_06_commit_and_final_route_state"}:
        issues.append(f"current_stage:{spine.get('current_stage')}")
    latest = spine.get("latest_numbers") or {}
    selector = stage04.get("selector_counts") or {}
    if latest.get("combined_selected_rows") != selector.get("combined_selected_rows"):
        issues.append("latest_numbers_combined_selected_rows_mismatch")
    if latest.get("old_three_selected_rows") != selector.get("old_three_selected_rows"):
        issues.append("latest_numbers_old_three_selected_rows_mismatch")
    if latest.get("broader_origin_selected_rows") != selector.get("broader_origin_selected_rows"):
        issues.append("latest_numbers_broader_origin_selected_rows_mismatch")
    if round(float(latest.get("total_r") or 0), 9) != round(float(stage04.get("selector_metrics", {}).get("total_r") or 0), 9):
        issues.append("latest_numbers_total_r_mismatch")
    expected_counts = {
        "combined_selected_rows": 289600,
        "broader_origin_selected_rows": 217485,
        "old_three_selected_rows": 72115,
        "broader_origin_outside_session_expanded_rows": 126483,
    }
    for key, expected in expected_counts.items():
        if selector.get(key) != expected:
            issues.append(f"stage04_expected_count_mismatch:{key}")
    metrics = stage04.get("selector_metrics") or {}
    expected_metrics = {
        "total_r": 129988.11498618065,
        "expectancy_r": 0.4488539882119498,
        "profit_factor": 2.4510790059629555,
        "win_rate": 0.5074861878453039,
    }
    for key, expected in expected_metrics.items():
        observed = metrics.get(key)
        if round(float(observed or 0), 9) != round(expected, 9):
            issues.append(f"stage04_expected_metric_mismatch:{key}")

    current_full = git_head_full()
    current_short = git_head_short_subject()
    provenance = provenance_from(spine, stage06, final_proof)
    artifact_head = head_full_from(provenance.get("artifact_generation_head"))
    if not artifact_head:
        issues.append("artifact_generation_head_missing")
    elif not git_is_ancestor(artifact_head, current_full):
        issues.append("artifact_generation_head_not_ancestor_of_current_verification_head")
    if provenance.get("current_verification_head_policy") != "may_be_descendant_after_repair_commit":
        issues.append("current_verification_head_policy_missing_or_stale")
    if provenance.get("committed_proof_head_policy") != "post_commit_head_verified_by_non_mutating_route_check":
        issues.append("committed_proof_head_policy_missing_or_stale")

    manifest_result, manifest_stderr = run_json_check(
        ["py", "-3", rel(ROUTE_DIR / "verify_vnext_activation_repair_output_manifest.py"), "--check"]
    )
    if not manifest_result or manifest_result.get("status") != "passed":
        issues.append(f"manifest_check_failed:{manifest_stderr or manifest_result}")
    elif manifest.get("output_count") != manifest_result.get("output_count"):
        issues.append("manifest_output_count_top_level_check_mismatch")

    stage04_result, stage04_stderr = run_json_check(
        ["py", "-3", rel(ROUTE_DIR / "verify_stage04_canonical_frequency_trade_r_ledger.py"), "--check"]
    )
    if not stage04_result or stage04_result.get("status") != "passed":
        issues.append(f"stage04_semantic_check_failed:{stage04_stderr or stage04_result}")
    prior_semantics = (stage04_result or {}).get("prior_intelligence_semantics") or {}
    if prior_semantics.get("blank_required_rows", 0) != 0:
        issues.append("prior_intelligence_blank_required_fields_remaining")
    if prior_semantics.get("blank_retained_production_question_closure_rows", 0) != 0:
        issues.append("prior_intelligence_blank_retained_production_replacement_rows_remaining")

    execution_result, execution_stderr = run_json_check(
        ["py", "-3", rel(EXECUTION_VERIFIER), "--check"]
    )
    if not execution_result or execution_result.get("status") != "passed":
        issues.append(f"execution_intelligence_check_failed:{execution_stderr or execution_result}")
    final_router_result, final_router_stderr = run_json_check(
        ["py", "-3", rel(FINAL_ROUTER_VERIFIER), "--check"]
    )
    if not final_router_result or final_router_result.get("status") != "passed":
        issues.append(f"final_dynamic_router_replay_check_failed:{final_router_stderr or final_router_result}")
    promotion_result, promotion_stderr = run_json_check(
        ["py", "-3", rel(PROMOTION_VERIFIER), "--check"]
    )
    if not promotion_result or promotion_result.get("status") != "passed":
        issues.append(f"momentum_promotion_check_failed:{promotion_stderr or promotion_result}")

    stale = "forward_capture_required" + "_before_execution_activation"
    terminal_paths = [
        STAGE03,
        STAGE04_SUMMARY,
        STAGE05,
        STAGE06,
        SPINE,
        MANIFEST,
        CONTROL_LEDGER,
        FINAL_PROOF,
        ANATOMY_MANIFEST,
        EXECUTION_PACKET,
        EXECUTION_SUMMARY,
        EXECUTION_BUILDER,
        EXECUTION_VERIFIER,
        FINAL_ROUTER_SUMMARY,
        FINAL_ROUTER_BUILDER,
        FINAL_ROUTER_VERIFIER,
        PROMOTION_SUMMARY,
        PROMOTION_VERIFIER,
        PROMOTION_RISK_PROOF,
        PROMOTION_LIFECYCLE_PROOF,
        PROMOTION_VERIFIER_RESULT,
        LAUNCH_DOSSIER,
        ACTIVATION_MAP,
    ]
    for path in terminal_paths:
        if text_contains(path, stale):
            issues.append(f"stale_pre_activation_wording:{rel(path)}")

    if stage03.get("status") != "completed_stage03_broker_runtime_surface":
        issues.append("stage03_not_completed")
    stage03_status_counts = (
        stage03.get("top_level_activation_counts", {}).get("status_counts") or {}
    )
    if "production_replacement_active_forward_capture_required_for_actual_cost_lifecycle_truth" not in stage03_status_counts:
        issues.append("stage03_active_production_capture_status_missing")

    if stage05.get("status") != "passed":
        issues.append("stage05_status_not_passed")
    if (
        stage06.get("provenance")
        and stage06.get("manifest_output_count") != manifest.get("output_count")
    ):
        issues.append("stage06_manifest_output_count_stale")
    if final_proof and final_proof.get("status") not in {"passed", "ready_for_post_commit_verification"}:
        issues.append("final_semantic_state_proof_not_passed")
    if not final_proof:
        issues.append("final_semantic_state_proof_missing")

    if not anatomy:
        issues.append("anatomy_dependency_manifest_missing")
    else:
        if anatomy.get("committed_route_fully_rederivable_from_head_without_untracked_anatomy") is not False:
            issues.append("anatomy_rederive_dependency_not_recorded")
        if int(anatomy.get("file_count") or 0) <= 0:
            issues.append("anatomy_manifest_file_count_missing")
        if int(anatomy.get("total_size_bytes") or 0) <= 0:
            issues.append("anatomy_manifest_total_size_missing")

    packet_requirements = set(execution_packet.get("required_ledgers") or [])
    for required in {
        "winner_leftover_move_ledger",
        "loser_mitigation_ledger",
        "be_classification_ledger",
        "dynamic_exit_counterfactual_ledger",
        "runtime_surface_gap_ledger",
        "replay_scoring_upgrade_spec",
    }:
        if required not in packet_requirements:
            issues.append(f"execution_packet_missing_required_ledger:{required}")

    if not execution_summary:
        issues.append("execution_intelligence_summary_missing")
    else:
        if execution_summary.get("ledger_output_format") != "uncompressed_plain_jsonl_shards_with_manifest":
            issues.append("execution_intelligence_not_plain_jsonl_shards")
        if execution_summary.get("selected_rows_processed") != 289600:
            issues.append("execution_intelligence_selected_rows_mismatch")
        if execution_summary.get("dynamic_policy_rows") != 3475200:
            issues.append("execution_intelligence_dynamic_policy_rows_mismatch")
        verdict = execution_summary.get("dynamic_layer_verdict") or {}
        if verdict.get("baseline_policy") != "fixed_1_5r":
            issues.append("execution_intelligence_baseline_missing")
        if verdict.get("best_implemented_policy") not in {
            "be_after_trigger",
            "partial_be_runner",
            "trailing_runner",
            "momentum_exhaustion",
            "time_stop",
        }:
            issues.append("execution_intelligence_best_implemented_policy_missing")
        if verdict.get("production_policy_selection_mode") != "condition_asof_displacement_v1_dynamic_router":
            issues.append("execution_intelligence_live_router_mode_missing")
        if verdict.get("production_policy_is_single_global_style") is not False:
            issues.append("execution_intelligence_collapsed_to_single_global_policy")
        if verdict.get("net_r_verdict") != "blocked_until_live_cost_slippage_commission_swap_and_deal_reconciliation_are_captured":
            issues.append("execution_intelligence_net_cost_blocker_missing")
        outputs = execution_summary.get("outputs") or {}
        for ledger_name in (
            "denominator_reconciliation_ledger",
            "winner_leftover_move_ledger",
            "loser_mitigation_ledger",
            "be_classification_ledger",
            "dynamic_exit_counterfactual_ledger",
            "runtime_surface_gap_ledger",
            "replay_scoring_upgrade_ledger",
        ):
            meta = outputs.get(ledger_name) or {}
            if not meta.get("plain_jsonl_shards") or meta.get("compressed") is not False:
                issues.append(f"execution_intelligence_ledger_not_plain:{ledger_name}")
            if int(meta.get("row_count") or 0) <= 0:
                issues.append(f"execution_intelligence_ledger_empty:{ledger_name}")
        stage06_execution_rows = stage06.get("execution_intelligence_dynamic_policy_rows")
        if stage06_execution_rows != execution_summary.get("dynamic_policy_rows"):
            issues.append("stage06_execution_intelligence_dynamic_rows_stale")

    if not final_router:
        issues.append("final_dynamic_router_replay_summary_missing")
    else:
        if final_router.get("selected_rows_processed") != 289600:
            issues.append("final_dynamic_router_selected_rows_mismatch")
        if final_router.get("condition_router_projection_gap_carried_forward_rows") != 0:
            issues.append("final_dynamic_router_condition_projection_gap_carried_forward")
        if final_router.get("prior_condition_router_projection_dependency") is not False:
            issues.append("final_dynamic_router_depends_on_prior_projection")
        if final_router.get("router_refused_rows") != 0:
            issues.append("final_dynamic_router_refused_rows_present")
        if final_router.get("replayable_metric_rows") != 289600 - int(final_router.get("non_replayable_rows") or 0):
            issues.append("final_dynamic_router_metric_row_accounting_mismatch")
        policy_distribution = final_router.get("policy_distribution") or {}
        if sum(int(value) for value in policy_distribution.values()) != 289600:
            issues.append("final_dynamic_router_policy_distribution_not_full_denominator")
        if "fixed_1_5r" in policy_distribution:
            issues.append("final_dynamic_router_chose_fixed_15r")
        if set(policy_distribution) != {
            "partial_be_runner",
            "momentum_exhaustion",
        }:
            issues.append("final_dynamic_router_missing_required_live_policy")
        metrics = final_router.get("final_dynamic_router_metrics") or {}
        for key in ("total_r", "expectancy_r", "profit_factor", "win_rate", "wins", "losses", "breakevens"):
            if key not in metrics:
                issues.append(f"final_dynamic_router_metric_missing:{key}")
        comparisons = final_router.get("global_policy_comparison_metrics") or {}
        for policy in (
            "fixed_1_5r",
            "be_after_trigger",
            "partial_be_runner",
            "trailing_runner",
            "momentum_exhaustion",
            "time_stop",
        ):
            if policy not in comparisons:
                issues.append(f"final_dynamic_router_comparison_missing:{policy}")
        if not (final_router.get("hindsight_best_regret") or {}).get("total_regret_r"):
            issues.append("final_dynamic_router_hindsight_regret_missing")
        if stage06.get("execution_intelligence_final_dynamic_router_rows") != final_router.get("selected_rows_processed"):
            issues.append("stage06_final_dynamic_router_rows_stale")

    if not promotion:
        issues.append("momentum_policy_promotion_summary_missing")
    else:
        if promotion.get("selected_rows_processed") != 289600:
            issues.append("momentum_promotion_selected_rows_mismatch")
        if promotion.get("replayable_rows") != 289599:
            issues.append("momentum_promotion_replayable_rows_mismatch")
        if promotion.get("non_replayable_rows") != 1:
            issues.append("momentum_promotion_non_replayable_rows_mismatch")
        decision = promotion.get("promotion_decision") or {}
        if decision.get("primary_policy") != "momentum_exhaustion":
            issues.append("momentum_promotion_primary_policy_not_momentum")
        if decision.get("exception_policy") != "partial_be_runner":
            issues.append("momentum_promotion_exception_policy_not_partial")
        if decision.get("fixed_1_5r_role") != "comparator_and_fail_closed_refusal_only_not_default":
            issues.append("momentum_promotion_fixed_15r_role_invalid")
        if decision.get("be_after_trigger_role") != "supported_legacy_policy_not_primary_not_exception":
            issues.append("momentum_promotion_be_after_trigger_role_invalid")
        metrics = (promotion.get("metrics") or {}).get("promoted_dynamic_router") or {}
        if metrics.get("total_r") != 286221.353599:
            issues.append("momentum_promotion_total_r_mismatch")
        if metrics.get("rows") != 289599:
            issues.append("momentum_promotion_metric_rows_mismatch")
        if promotion.get("policy_distribution") != {
            "momentum_exhaustion": 121112,
            "partial_be_runner": 168487,
            "non_replayable_no_policy": 1,
        }:
            issues.append("momentum_promotion_policy_distribution_mismatch")
        stage06_promotion = stage06.get("execution_policy_momentum_promotion_metrics") or {}
        if stage06_promotion.get("total_r") != metrics.get("total_r"):
            issues.append("stage06_momentum_promotion_metrics_stale")
    if promotion_risk.get("policy_identity_status_required_in_live_runtime") is not True:
        issues.append("selected_policy_risk_identity_not_required_in_runtime")
    if promotion_risk.get("be_keyed_risk_rows_allowed_only_with_policy_invariant_broker_geometry") is not True:
        issues.append("be_keyed_risk_rows_not_policy_invariant_only")
    if promotion_lifecycle.get("production_policy") != "momentum_exhaustion":
        issues.append("momentum_lifecycle_production_policy_mismatch")
    if promotion_lifecycle.get("fixed_1_5r_role") != "comparator_and_fail_closed_refusal_only_not_default":
        issues.append("momentum_lifecycle_fixed_15r_reactivation_risk")

    if not launch_dossier:
        issues.append("launch_execution_router_dossier_missing")
    else:
        contract = launch_dossier.get("live_policy_contract") or {}
        if contract.get("every_selected_trade_gets_execution_policy_id") is not True:
            issues.append("launch_dossier_execution_policy_id_contract_missing")
        if contract.get("fixed_1_5r_is_default") is not False:
            issues.append("launch_dossier_fixed_15r_default_reintroduced")
        if contract.get("condition_challenger_enabled") is not True:
            issues.append("launch_dossier_condition_router_not_enabled")
        if contract.get("primary_policy") != "momentum_exhaustion":
            issues.append("launch_dossier_primary_policy_not_momentum")
        if contract.get("exception_policy") != "partial_be_runner":
            issues.append("launch_dossier_exception_policy_not_partial")
        if contract.get("launch_router_policy_set") != [
            "momentum_exhaustion",
            "partial_be_runner",
        ]:
            issues.append("launch_dossier_policy_set_mismatch")
        universe = launch_dossier.get("launch_universe") or {}
        if universe.get("symbol_count") != 24:
            issues.append("launch_dossier_symbol_count_mismatch")
        evidence = (launch_dossier.get("execution_intelligence_evidence") or {}).get(
            "promoted_live_dynamic_router"
        ) or {}
        if evidence.get("selected_rows") != 289600:
            issues.append("launch_dossier_missing_promoted_router_rows")
        if (evidence.get("metrics") or {}).get("total_r") != 286221.353599:
            issues.append("launch_dossier_promoted_router_total_r_mismatch")

    for rpath in spine.get("active_files") or []:
        if not (REPO_ROOT / rpath).exists():
            issues.append(f"active_file_missing:{rpath}")
    result = {
        "mode": "check",
        "status": "passed" if not issues else "failed",
        "issue_count": len(issues),
        "issues": issues,
        "current_stage": spine.get("current_stage"),
        "current_verification_head": current_short,
        "artifact_generation_head": artifact_head,
        "open_gates": sorted(open_gates),
        "completed_gate_count": len(completed),
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
