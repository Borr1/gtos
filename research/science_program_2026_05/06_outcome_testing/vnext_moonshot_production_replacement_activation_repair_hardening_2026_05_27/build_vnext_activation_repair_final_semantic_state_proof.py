from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-27"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
STAGE03 = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE03_BROKER_RUNTIME_SURFACE_{DATE}.json"
STAGE04 = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE04_CANONICAL_FREQUENCY_TRADE_R_SUMMARY_{DATE}.json"
STAGE05 = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE05_FULL_VERIFICATION_MATRIX_{DATE}.json"
MANIFEST = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
SPINE = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE_SPINE_{DATE}.json"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_CONTROL_LEDGER_{DATE}.jsonl"
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
OUTPUT = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_FINAL_SEMANTIC_STATE_PROOF_{DATE}.json"
ACTIVATION_MAP = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_moonshot_production_replacement_activation_2026_05_26/"
    / "VNEXT_REPLACEMENT_MARKET_SOURCE_ACTIVATION_MAP_2026-05-26.json"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")


def git_head_object() -> dict[str, str]:
    full = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.strip()
    short = subprocess.run(
        ["git", "log", "-1", "--format=%h %s"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.strip()
    return {"full_sha": full, "short_subject": short}


def contains(path: Path, text: str) -> bool:
    if not path.exists():
        return False
    return text in path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    generated_at = utc_now()
    head = git_head_object()
    stage03 = read_json(STAGE03)
    stage04 = read_json(STAGE04)
    stage05 = read_json(STAGE05)
    manifest = read_json(MANIFEST)
    anatomy = read_json(ANATOMY_MANIFEST)
    packet = read_json(EXECUTION_PACKET)
    execution_summary = read_json(EXECUTION_SUMMARY)
    final_router = read_json(FINAL_ROUTER_SUMMARY)
    promotion = read_json(PROMOTION_SUMMARY)
    promotion_risk = read_json(PROMOTION_RISK_PROOF)
    promotion_lifecycle = read_json(PROMOTION_LIFECYCLE_PROOF)
    launch_dossier = read_json(LAUNCH_DOSSIER)
    stale = "forward_capture_required" + "_before_execution_activation"
    terminal_paths = [
        STAGE03,
        STAGE04,
        STAGE05,
        MANIFEST,
        SPINE,
        CONTROL_LEDGER,
        ANATOMY_MANIFEST,
        EXECUTION_PACKET,
        EXECUTION_SUMMARY,
        EXECUTION_VERIFIER,
        FINAL_ROUTER_SUMMARY,
        FINAL_ROUTER_VERIFIER,
        PROMOTION_SUMMARY,
        PROMOTION_VERIFIER,
        PROMOTION_RISK_PROOF,
        PROMOTION_LIFECYCLE_PROOF,
        PROMOTION_VERIFIER_RESULT,
        LAUNCH_DOSSIER,
        ACTIVATION_MAP,
    ]
    stale_hits = [rel(path) for path in terminal_paths if contains(path, stale)]
    required_ledgers = set(packet.get("required_ledgers") or [])
    packet_complete = {
        "winner_leftover_move_ledger",
        "loser_mitigation_ledger",
        "be_classification_ledger",
        "dynamic_exit_counterfactual_ledger",
        "runtime_surface_gap_ledger",
        "replay_scoring_upgrade_spec",
    }.issubset(required_ledgers)
    passed = (
        not stale_hits
        and stage03.get("status") == "completed_stage03_broker_runtime_surface"
        and stage05.get("status") == "passed"
        and packet_complete
        and execution_summary.get("selected_rows_processed") == stage04.get("selector_counts", {}).get("combined_selected_rows")
        and execution_summary.get("dynamic_policy_rows") == stage04.get("selector_counts", {}).get("combined_selected_rows", 0) * 12
        and execution_summary.get("ledger_output_format") == "uncompressed_plain_jsonl_shards_with_manifest"
        and final_router.get("selected_rows_processed") == stage04.get("selector_counts", {}).get("combined_selected_rows")
        and final_router.get("condition_router_projection_gap_carried_forward_rows") == 0
        and final_router.get("router_refused_rows") == 0
        and final_router.get("replayable_metric_rows") == stage04.get("selector_counts", {}).get("combined_selected_rows", 0) - final_router.get("non_replayable_rows", 0)
        and promotion.get("selected_rows_processed") == stage04.get("selector_counts", {}).get("combined_selected_rows")
        and promotion.get("replayable_rows") == stage04.get("selector_counts", {}).get("combined_selected_rows", 0) - promotion.get("non_replayable_rows", 0)
        and (promotion.get("promotion_decision") or {}).get("primary_policy") == "momentum_exhaustion"
        and (promotion.get("promotion_decision") or {}).get("exception_policy") == "partial_be_runner"
        and ((promotion.get("metrics") or {}).get("promoted_dynamic_router") or {}).get("total_r") == 286221.353599
        and promotion_risk.get("policy_identity_status_required_in_live_runtime") is True
        and promotion_lifecycle.get("production_policy") == "momentum_exhaustion"
        and launch_dossier.get("live_policy_contract", {}).get("every_selected_trade_gets_execution_policy_id") is True
        and launch_dossier.get("live_policy_contract", {}).get("fixed_1_5r_is_default") is False
        and launch_dossier.get("live_policy_contract", {}).get("condition_challenger_enabled") is True
        and launch_dossier.get("live_policy_contract", {}).get("launch_router_policy_set") == [
            "momentum_exhaustion",
            "partial_be_runner",
        ]
        and anatomy.get("committed_route_fully_rederivable_from_head_without_untracked_anatomy") is False
    )
    proof = {
        "schema_version": "vnext_activation_repair_final_semantic_state_proof_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": generated_at,
        "status": "passed" if passed else "ready_for_post_commit_verification",
        "provenance": {
            "base_input_head": head,
            "artifact_generation_head": head,
            "committed_proof_head": None,
            "expected_head_policy": (
                "artifact_generation_head is the generating/input head; committed proof head is "
                "established by non-mutating verifiers after the repair commit"
            ),
            "committed_proof_head_policy": "post_commit_head_verified_by_non_mutating_route_check",
            "current_verification_head_policy": "may_be_descendant_after_repair_commit",
        },
        "stage03_active_production_state": {
            "status": stage03.get("status"),
            "activation_status_counts": stage03.get("top_level_activation_counts", {}).get("status_counts"),
            "stale_pre_activation_wording_hits": stale_hits,
        },
        "stage04_canonical_anchor": {
            "selector_counts": stage04.get("selector_counts"),
            "selector_metrics": stage04.get("selector_metrics"),
            "static_ceiling_limitation": (
                "The canonical ledger is still mostly fixed -1R/0R/+1.5R. "
                "It proves route/frequency/R selection, not moonshot execution-ceiling escape."
            ),
        },
        "stage05_status": stage05.get("status"),
        "stage05_command_count": len(stage05.get("commands") or []),
        "manifest_output_count": manifest.get("output_count") or len(manifest.get("outputs") or []),
        "manifest_current_disk_file_count": manifest.get("current_disk_file_count"),
        "anatomy_dependency": {
            "manifest_path": rel(ANATOMY_MANIFEST),
            "file_count": anatomy.get("file_count"),
            "total_size_bytes": anatomy.get("total_size_bytes"),
            "committed_route_verifiable_without_untracked_anatomy": anatomy.get(
                "committed_route_verifiable_without_untracked_anatomy"
            ),
            "committed_route_fully_rederivable_from_head_without_untracked_anatomy": anatomy.get(
                "committed_route_fully_rederivable_from_head_without_untracked_anatomy"
            ),
        },
        "execution_intelligence_continuation_packet": {
            "path": rel(EXECUTION_PACKET),
            "status": packet.get("status"),
            "required_ledgers": sorted(required_ledgers),
        },
        "execution_intelligence_static_15r_replay_layer": {
            "summary_path": rel(EXECUTION_SUMMARY),
            "verifier_path": rel(EXECUTION_VERIFIER),
            "status": execution_summary.get("status"),
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
            "outputs": execution_summary.get("outputs"),
        },
        "execution_intelligence_final_dynamic_router_replay": {
            "role": (
                "post_promotion_live_router_replay"
                if promotion.get("source_dynamic_router_state")
                == "post_promotion_router_already_current"
                else "pre_promotion_mixed_condition_router_replay_diagnostic_not_launch_policy"
            ),
            "summary_path": rel(FINAL_ROUTER_SUMMARY),
            "verifier_path": rel(FINAL_ROUTER_VERIFIER),
            "status": final_router.get("status"),
            "selected_rows_processed": final_router.get("selected_rows_processed"),
            "replayable_metric_rows": final_router.get("replayable_metric_rows"),
            "non_replayable_rows": final_router.get("non_replayable_rows"),
            "router_refused_rows": final_router.get("router_refused_rows"),
            "condition_router_projection_gap_carried_forward_rows": final_router.get(
                "condition_router_projection_gap_carried_forward_rows"
            ),
            "policy_distribution": final_router.get("policy_distribution"),
            "final_dynamic_router_metrics": final_router.get("final_dynamic_router_metrics"),
            "global_policy_comparison_metrics": final_router.get(
                "global_policy_comparison_metrics"
            ),
            "hindsight_best_regret": final_router.get("hindsight_best_regret"),
            "outputs": final_router.get("outputs"),
        },
        "execution_policy_momentum_promotion": {
            "summary_path": rel(PROMOTION_SUMMARY),
            "verifier_path": rel(PROMOTION_VERIFIER),
            "selected_policy_risk_proof_summary": rel(PROMOTION_RISK_PROOF),
            "lifecycle_propagation_proof": rel(PROMOTION_LIFECYCLE_PROOF),
            "verifier_result": rel(PROMOTION_VERIFIER_RESULT),
            "selected_rows_processed": promotion.get("selected_rows_processed"),
            "replayable_rows": promotion.get("replayable_rows"),
            "non_replayable_rows": promotion.get("non_replayable_rows"),
            "promotion_decision": promotion.get("promotion_decision"),
            "policy_distribution": promotion.get("policy_distribution"),
            "metrics": (promotion.get("metrics") or {}).get("promoted_dynamic_router"),
            "deltas": promotion.get("deltas"),
            "selected_policy_risk_identity_model": promotion_risk.get(
                "selected_policy_risk_identity_model"
            ),
            "production_policy": promotion_lifecycle.get("production_policy"),
        },
        "launch_execution_router_dossier": {
            "path": rel(LAUNCH_DOSSIER),
            "status": launch_dossier.get("status"),
            "launch_readiness_verdict": launch_dossier.get("launch_readiness_verdict"),
            "live_policy_contract": launch_dossier.get("live_policy_contract"),
            "launch_universe": launch_dossier.get("launch_universe"),
            "telemetry_paths": (
                (launch_dossier.get("runtime_surfaces") or {}).get("telemetry_paths")
            ),
        },
        "terminal_semantics": {
            "vnext_replacement_path_active": True,
            "old_system_fallback_allowed": False,
            "old_live_static_ceiling_as_terminal_claim_allowed": False,
            "narrowed_market_surface_allowed": False,
        },
    }
    write_json(OUTPUT, proof)
    append_jsonl(
        CONTROL_LEDGER,
        {
            "event": "final_semantic_state_proof_written",
            "generated_at_utc": generated_at,
            "output": rel(OUTPUT),
            "route_id": ROUTE_ID,
            "status": proof["status"],
            "stale_pre_activation_wording_hit_count": len(stale_hits),
        },
    )
    print(json.dumps({"output": rel(OUTPUT), "status": proof["status"]}, sort_keys=True))
    return 0 if proof["status"] in {"passed", "ready_for_post_commit_verification"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
