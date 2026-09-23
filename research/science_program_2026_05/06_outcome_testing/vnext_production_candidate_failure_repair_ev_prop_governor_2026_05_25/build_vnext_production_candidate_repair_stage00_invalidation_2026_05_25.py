from __future__ import annotations

import gzip
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover - fallback for hosts without PyYAML
    yaml = None


ROUTE_ID = "vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25"
ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
FAILED_ROUTE_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25"
PROMPT_PATH = ROOT / "research/science_program_2026_05/04_goal_prompts/VNEXT_PRODUCTION_CANDIDATE_FAILURE_REPAIR_EV_PROP_GOVERNOR_GOAL_PROMPT_2026-05-25.md"
STARTER_PATH = ROOT / "research/science_program_2026_05/04_goal_prompts/VNEXT_PRODUCTION_CANDIDATE_FAILURE_REPAIR_EV_PROP_GOVERNOR_STARTER_2026-05-25.txt"
FORENSIC_PATH = FAILED_ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_FORENSIC_ACCOUNTABILITY_REPORT_DO_NOT_ACTIVATE_2026-05-25.md"
LIVE_STATE_PATH = ROOT / ".context/LIVE_STATE.md"
CONFIG_PATH = ROOT / "config/agent_config.yaml"


OUTPUT_MANIFEST = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_INPUT_MANIFEST_2026-05-25.json"
OUTPUT_LEDGER = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_FAILED_ROUTE_INVALIDATION_LEDGER_2026-05-25.jsonl"
OUTPUT_DOSSIER = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_FAILED_ROUTE_INVALIDATION_2026-05-25.md"
OUTPUT_STATE = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_SESSION_STATE_2026-05-25.json"


FAILED_ARTIFACTS = {
    "stage09_metrics_summary": "VNEXT_PRODUCTION_CHANGE_METRICS_SUMMARY_2026-05-25.json",
    "stage09_replay_dossier": "VNEXT_PRODUCTION_CHANGE_REPLAY_COMPARISON_DOSSIER_2026-05-25.md",
    "stage10_completion_audit": "VNEXT_PRODUCTION_CHANGE_COMPLETION_AUDIT_2026-05-25.json",
    "failed_session_state": "VNEXT_PRODUCTION_CHANGE_SESSION_STATE_2026-05-25.json",
    "stage09_builder": "build_vnext_production_change_stage09_forward_replay_2026_05_25.py",
    "stage09_test": "test_vnext_production_change_stage09_forward_replay_2026_05_25.py",
    "stage10_builder": "build_vnext_production_change_stage10_completion_audit_2026_05_25.py",
    "stage10_test": "test_vnext_production_change_stage10_completion_audit_2026_05_25.py",
    "stage09_verifier": "verify_vnext_production_change_stage09_forward_replay_2026_05_25.py",
    "stage10_verifier": "verify_vnext_production_change_stage10_completion_audit_2026_05_25.py",
}


STAGES = [
    "STAGE_00_INPUT_FREEZE_AND_FAILED_ROUTE_INVALIDATION",
    "STAGE_01_FULL_FAILURE_ANATOMY_LEDGER",
    "STAGE_02_ACCEPTANCE_GATE_REPAIR",
    "STAGE_03_EXECUTABLE_STREAM_AND_ROUTE_SEMANTICS_REPAIR",
    "STAGE_04_EV_OPTIMIZED_PROP_CHALLENGE_GOVERNOR",
    "STAGE_05_VNEXT_AVOID_AND_PRE_AI_REPAIR",
    "STAGE_06_LTF_ENTRY_NOFILL_EXECUTION_REPAIR",
    "STAGE_07_AI_POLICY_AND_SUPERVISOR_REPAIR",
    "STAGE_08_REPAIRED_FORWARD_ONLY_REPLAY",
    "STAGE_09_PRODUCTION_CANDIDATE_DECISION_DOSSIER",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_record(path: Path) -> dict[str, Any]:
    exists = path.exists()
    return {
        "path": rel(path) if exists else path.as_posix(),
        "exists": exists,
        "bytes": path.stat().st_size if exists else None,
        "sha256": sha256_file(path) if exists and path.is_file() else None,
    }


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def run_git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def gzip_line_count(path: Path) -> int:
    count = 0
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for _ in handle:
            count += 1
    return count


def load_activation_flags() -> dict[str, Any]:
    if yaml is not None:
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            cfg = yaml.safe_load(handle) or {}
        vnext = cfg.get("gtos_vnext_runtime", {}) or {}
        ai_supervisor = cfg.get("ai_supervisor", {}) or {}
        return {
            "config_path": rel(CONFIG_PATH),
            "gtos_vnext_runtime.enabled": vnext.get("enabled"),
            "gtos_vnext_runtime.apply_to_execution": vnext.get("apply_to_execution"),
            "gtos_vnext_runtime.pre_ai_enabled": vnext.get("pre_ai_enabled"),
            "gtos_vnext_runtime.pre_ai_apply_to_ai_call": vnext.get("pre_ai_apply_to_ai_call"),
            "gtos_vnext_runtime.ltf_path_execution_apply_to_execution": vnext.get("ltf_path_execution_apply_to_execution"),
            "gtos_vnext_runtime.prop_safe_selector_enabled": vnext.get("prop_safe_selector_enabled"),
            "gtos_vnext_runtime.prop_safe_selector_apply_to_execution": vnext.get("prop_safe_selector_apply_to_execution"),
            "gtos_vnext_runtime.avoid_blocks_execution": vnext.get("avoid_blocks_execution"),
            "gtos_vnext_runtime.mixed_blocks_execution": vnext.get("mixed_blocks_execution"),
            "gtos_vnext_runtime.legacy_blocks_execution": vnext.get("legacy_blocks_execution"),
            "ai_supervisor.apply_runtime_overrides": ai_supervisor.get("apply_runtime_overrides"),
            "broker_facing_vnext_activation_flags_off": (
                vnext.get("apply_to_execution") is False
                and vnext.get("ltf_path_execution_apply_to_execution") is False
                and vnext.get("prop_safe_selector_apply_to_execution") is False
                and vnext.get("pre_ai_apply_to_ai_call") is False
            ),
        }

    text = CONFIG_PATH.read_text(encoding="utf-8")
    flags: dict[str, Any] = {"config_path": rel(CONFIG_PATH), "yaml_parser_available": False}
    for key in [
        "apply_to_execution",
        "pre_ai_apply_to_ai_call",
        "ltf_path_execution_apply_to_execution",
        "prop_safe_selector_apply_to_execution",
        "avoid_blocks_execution",
        "mixed_blocks_execution",
        "legacy_blocks_execution",
    ]:
        marker = f"{key}:"
        for line in text.splitlines():
            if line.strip().startswith(marker):
                flags[key] = line.split(":", 1)[1].strip()
    flags["broker_facing_vnext_activation_flags_off"] = (
        flags.get("apply_to_execution") == "false"
        and flags.get("pre_ai_apply_to_ai_call") == "false"
        and flags.get("ltf_path_execution_apply_to_execution") == "false"
        and flags.get("prop_safe_selector_apply_to_execution") == "false"
    )
    return flags


def summarize_failed_metrics(metrics: dict[str, Any], completion_audit: dict[str, Any], failed_state: dict[str, Any]) -> dict[str, Any]:
    scenario = metrics["scenario_metrics"]
    baseline = scenario["baseline_current_shadow"]
    new_mech = scenario["new_production_change_mechanical"]
    ai_no_paid = scenario["new_ai_policy_no_paid_call"]
    return {
        "failed_route_head_commit_from_live_state": "75a85d244 research: complete vnext production change route",
        "stage09_summary_git_head": metrics.get("current_git_head"),
        "stage10_audit_git_head": completion_audit.get("current_git_head"),
        "candidate_rows": metrics.get("candidate_rows"),
        "stage09_written_replay_rows": metrics.get("written_replay_rows"),
        "baseline_selected_count": baseline.get("selected_count"),
        "baseline_performance_count": baseline.get("performance_count"),
        "baseline_total_r": baseline.get("total_r"),
        "baseline_expectancy_r": baseline.get("expectancy_r"),
        "baseline_win_rate": baseline.get("win_rate"),
        "baseline_profit_factor": baseline.get("profit_factor"),
        "new_mechanical_selected_count": new_mech.get("selected_count"),
        "new_mechanical_performance_count": new_mech.get("performance_count"),
        "new_mechanical_total_r": new_mech.get("total_r"),
        "new_mechanical_expectancy_r": new_mech.get("expectancy_r"),
        "new_mechanical_win_rate": new_mech.get("win_rate"),
        "new_mechanical_profit_factor": new_mech.get("profit_factor"),
        "new_mechanical_skip_reasons": new_mech.get("skip_reasons", {}),
        "new_mechanical_missed_winners": new_mech.get("missed_winners"),
        "new_mechanical_avoided_losers": new_mech.get("avoided_losers"),
        "new_ai_no_paid_selected_count": ai_no_paid.get("selected_count"),
        "new_ai_no_paid_expectancy_r": ai_no_paid.get("expectancy_r"),
        "completion_audit_claimed_complete": completion_audit.get("complete"),
        "completion_audit_instruction_coverage_ok": completion_audit.get("instruction_coverage_ok"),
        "completion_audit_embedded_stage10_status": completion_audit.get("stage_status_table", {}).get("STAGE_10_COMPLETION_AUDIT_ACTIVATION_DOSSIER"),
        "failed_state_first_incomplete_invariant": failed_state.get("first_incomplete_invariant"),
        "failed_state_current_stage": failed_state.get("current_stage"),
        "failed_state_stage10_status": failed_state.get("stage_status_table", {}).get("STAGE_10_COMPLETION_AUDIT_ACTIVATION_DOSSIER"),
        "activation_safe": False,
        "activation_safety_reason": (
            "Stage09 selected 10 of 253234 generated rows, lost -4.999959R, "
            "had negative expectancy and PF below 1, while Stage10 still marked completion."
        ),
    }


def build() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    now = utc_now()
    current_head = run_git(["rev-parse", "HEAD"])
    git_status = run_git(["status", "--short"]).splitlines()

    required_inputs = {
        "live_state": file_record(LIVE_STATE_PATH),
        "prompt": file_record(PROMPT_PATH),
        "starter": file_record(STARTER_PATH),
        "forensic_report": file_record(FORENSIC_PATH),
        "goal_session_research_discipline": file_record(ROOT / ".context/00_core/goal_session_research_discipline.md"),
        "research_operating_doctrine": file_record(ROOT / ".context/00_core/research_operating_doctrine.md"),
        "orchestrator_successor_operating_brief": file_record(ROOT / ".context/00_core/orchestrator_successor_operating_brief.md"),
        "orchestrator_methodology_hardening_controls": file_record(ROOT / ".context/00_core/orchestrator_methodology_hardening_controls.md"),
        "parallel_goal_merge_playbook": file_record(ROOT / ".context/00_core/parallel_goal_merge_playbook.md"),
        "latest_session_handoff": file_record(ROOT / ".context/02_session_handoffs/SESSION_63_VNEXT_EXACT_R_SOURCE_REPAIR_GUARD_HANDOFF_2026-05-19.md"),
    }
    failed_artifacts = {name: file_record(FAILED_ROUTE_DIR / filename) for name, filename in FAILED_ARTIFACTS.items()}

    metrics = read_json(FAILED_ROUTE_DIR / FAILED_ARTIFACTS["stage09_metrics_summary"])
    completion_audit = read_json(FAILED_ROUTE_DIR / FAILED_ARTIFACTS["stage10_completion_audit"])
    failed_state = read_json(FAILED_ROUTE_DIR / FAILED_ARTIFACTS["failed_session_state"])
    failure_facts = summarize_failed_metrics(metrics, completion_audit, failed_state)

    shard_records = []
    for shard in sorted((FAILED_ROUTE_DIR / "stage09_shards").glob("*/replay_comparison.jsonl.gz")):
        shard_records.append(
            {
                **file_record(shard),
                "row_count": gzip_line_count(shard),
            }
        )
    total_shard_rows = sum(record["row_count"] for record in shard_records)
    shard_manifest_hash = hashlib.sha256(
        json.dumps(shard_records, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    activation_flags = load_activation_flags()
    stage_status = {stage: "pending" for stage in STAGES}
    stage_status["STAGE_00_INPUT_FREEZE_AND_FAILED_ROUTE_INVALIDATION"] = "complete"

    manifest = {
        "schema_version": "vnext_production_candidate_repair_stage00_input_manifest_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": now,
        "source_operation": "read_only_hash_and_failed_metric_preservation",
        "current_git_head": current_head,
        "dirty_tracked_and_untracked_path_summary": git_status,
        "required_context_inputs": required_inputs,
        "failed_route_artifacts": failed_artifacts,
        "stage09_replay_shards": {
            "glob": rel(FAILED_ROUTE_DIR / "stage09_shards/*/replay_comparison.jsonl.gz"),
            "shard_count": len(shard_records),
            "total_rows": total_shard_rows,
            "matches_stage09_written_replay_rows": total_shard_rows == failure_facts["stage09_written_replay_rows"],
            "sha256_manifest": shard_manifest_hash,
            "shards": shard_records,
        },
        "recomputed_failure_facts": failure_facts,
        "runtime_activation_flags": activation_flags,
        "branch_decision": "failed_route_completion_claim_invalidated",
        "implementation_decision": "do_not_activate_failed_route_continue_to_stage01_full_failure_anatomy",
        "replay_effect": {
            "baseline_total_r": failure_facts["baseline_total_r"],
            "new_mechanical_total_r": failure_facts["new_mechanical_total_r"],
            "selected_count_collapse": failure_facts["baseline_selected_count"] - failure_facts["new_mechanical_selected_count"],
            "selected_count_collapse_pct_of_baseline": round(
                (failure_facts["baseline_selected_count"] - failure_facts["new_mechanical_selected_count"])
                / failure_facts["baseline_selected_count"],
                12,
            ),
        },
        "forbidden_boundaries_respected": {
            "live_trading": True,
            "broker_operation": True,
            "broker_account_order_history_deal_position_mutation": True,
            "paid_api_or_vendor_calls": True,
            "source_deletion": True,
            "remote_push": True,
            "credentials": True,
            "broker_facing_activation_flips": True,
        },
        "first_incomplete_invariant_after_stage00": "STAGE_01_FULL_FAILURE_ANATOMY_LEDGER",
    }

    with OUTPUT_MANIFEST.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")

    ledger_records = [
        {
            "record_type": "stage00_artifact_freeze",
            "created_at_utc": now,
            "route_id": ROUTE_ID,
            "input_count": len(required_inputs),
            "failed_artifact_count": len(failed_artifacts),
            "stage09_shard_count": len(shard_records),
            "stage09_shard_rows": total_shard_rows,
            "stage09_shard_rows_match_summary": manifest["stage09_replay_shards"]["matches_stage09_written_replay_rows"],
            "prompt_sha256": required_inputs["prompt"]["sha256"],
            "starter_sha256": required_inputs["starter"]["sha256"],
            "forensic_report_sha256": required_inputs["forensic_report"]["sha256"],
        },
        {
            "record_type": "failed_completion_claim_invalidated",
            "created_at_utc": now,
            "candidate_rows": failure_facts["candidate_rows"],
            "baseline_selected_count": failure_facts["baseline_selected_count"],
            "baseline_total_r": failure_facts["baseline_total_r"],
            "new_mechanical_selected_count": failure_facts["new_mechanical_selected_count"],
            "new_mechanical_total_r": failure_facts["new_mechanical_total_r"],
            "new_mechanical_expectancy_r": failure_facts["new_mechanical_expectancy_r"],
            "new_mechanical_profit_factor": failure_facts["new_mechanical_profit_factor"],
            "completion_audit_claimed_complete": failure_facts["completion_audit_claimed_complete"],
            "completion_audit_embedded_stage10_status": failure_facts["completion_audit_embedded_stage10_status"],
            "activation_safe": False,
            "decision": "75a85d244_not_activation_safe",
        },
        {
            "record_type": "runtime_activation_boundary_preserved",
            "created_at_utc": now,
            "activation_flags": activation_flags,
            "broker_facing_activation_flags_off": activation_flags["broker_facing_vnext_activation_flags_off"],
            "boundary_note": "Disabled runtime flags are evidence of current broker safety only; they do not validate the failed candidate.",
        },
        {
            "record_type": "stage00_completion_and_next_invariant",
            "created_at_utc": now,
            "stage_status": "complete",
            "first_incomplete_invariant": "STAGE_01_FULL_FAILURE_ANATOMY_LEDGER",
            "next_action": "Build full row-level failure anatomy from Stage09 shards and old Stage09/Stage10 code.",
        },
    ]
    with OUTPUT_LEDGER.open("w", encoding="utf-8", newline="\n") as handle:
        for record in ledger_records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    dossier = f"""# vNext Production Candidate Repair - Failed Route Invalidation

Date: 2026-05-25

Route id: `{ROUTE_ID}`

## Verdict

`75a85d244 research: complete vnext production change route` is not activation-safe. The prior completion claim is preserved as evidence and invalidated for broker-facing activation.

## Evidence

- Failed Stage09 summary: `{rel(FAILED_ROUTE_DIR / FAILED_ARTIFACTS["stage09_metrics_summary"])}`
- Failed Stage10 completion audit: `{rel(FAILED_ROUTE_DIR / FAILED_ARTIFACTS["stage10_completion_audit"])}`
- Failed session state: `{rel(FAILED_ROUTE_DIR / FAILED_ARTIFACTS["failed_session_state"])}`
- Forensic report: `{rel(FORENSIC_PATH)}`
- Stage09 replay shards: `{manifest["stage09_replay_shards"]["shard_count"]}` shards, `{manifest["stage09_replay_shards"]["total_rows"]}` rows, shard-manifest hash `{manifest["stage09_replay_shards"]["sha256_manifest"]}`
- Input manifest: `{rel(OUTPUT_MANIFEST)}`
- Invalidation ledger: `{rel(OUTPUT_LEDGER)}`

## Recomputed Failure Facts

| Metric | Failed route value |
|---|---:|
| Candidate rows | {failure_facts["candidate_rows"]:,} |
| Baseline selected rows | {failure_facts["baseline_selected_count"]:,} |
| Baseline performance rows | {failure_facts["baseline_performance_count"]:,} |
| Baseline total R | {failure_facts["baseline_total_r"]:.12f} |
| Baseline expectancy R | {failure_facts["baseline_expectancy_r"]:.12f} |
| Baseline win rate | {failure_facts["baseline_win_rate"]:.12%} |
| Baseline profit factor | {failure_facts["baseline_profit_factor"]:.12f} |
| New mechanical selected rows | {failure_facts["new_mechanical_selected_count"]:,} |
| New mechanical performance rows | {failure_facts["new_mechanical_performance_count"]:,} |
| New mechanical total R | {failure_facts["new_mechanical_total_r"]:.12f} |
| New mechanical expectancy R | {failure_facts["new_mechanical_expectancy_r"]:.12f} |
| New mechanical win rate | {failure_facts["new_mechanical_win_rate"]:.12%} |
| New mechanical profit factor | {failure_facts["new_mechanical_profit_factor"]:.12f} |
| AI no-paid-call selected rows | {failure_facts["new_ai_no_paid_selected_count"]:,} |

The failed route selected only 10 of 253,234 generated candidates, lost about -5R, had negative expectancy, and had profit factor below 1. The baseline/current shadow stream selected 35,983 rows and produced about +4008.3317R.

## Invalidated Completion Claim

The Stage10 audit recorded `complete=true` and `instruction_coverage_ok=true`, but its embedded stage table still had `STAGE_10_COMPLETION_AUDIT_ACTIVATION_DOSSIER=in_progress`. More importantly, the completion gate did not reject the negative, near-zero-trade production candidate. Artifact existence and instruction coverage are not viability proof.

## Activation Boundary

Current config still keeps broker-facing vNext execution flags off:

| Flag | Value |
|---|---|
| `gtos_vnext_runtime.apply_to_execution` | `{activation_flags.get("gtos_vnext_runtime.apply_to_execution")}` |
| `gtos_vnext_runtime.pre_ai_apply_to_ai_call` | `{activation_flags.get("gtos_vnext_runtime.pre_ai_apply_to_ai_call")}` |
| `gtos_vnext_runtime.ltf_path_execution_apply_to_execution` | `{activation_flags.get("gtos_vnext_runtime.ltf_path_execution_apply_to_execution")}` |
| `gtos_vnext_runtime.prop_safe_selector_apply_to_execution` | `{activation_flags.get("gtos_vnext_runtime.prop_safe_selector_apply_to_execution")}` |

This proves current broker-facing safety only. It does not repair the failed candidate and cannot be used as completion.

## Stage 00 Decision

- Branch decision: `failed_route_completion_claim_invalidated`
- Implementation decision: continue repair route; do not activate the failed route.
- Replay effect preserved: baseline `+{failure_facts["baseline_total_r"]:.6f}R` versus new mechanical `{failure_facts["new_mechanical_total_r"]:.6f}R`.
- First incomplete invariant: `STAGE_01_FULL_FAILURE_ANATOMY_LEDGER`

## Next Same-Evidence-Class Work

Build the full row-level failure anatomy from `stage09_shards/*/replay_comparison.jsonl.gz`, Stage09/Stage10 source code, and upstream Stage03/Stage04 joins. The next artifact must preserve selected rows, dropped baseline rows, route-semantics bugs, selected-only coverage, AVOID pressure, LTF effect, AI/no-paid-call behavior, and acceptance-gate failures before moving to repair.
"""
    OUTPUT_DOSSIER.write_text(dossier, encoding="utf-8", newline="\n")

    session_state = {
        "schema_version": "vnext_production_candidate_repair_session_state_v1",
        "route_id": ROUTE_ID,
        "updated_at_utc": now,
        "current_stage": "STAGE_01_FULL_FAILURE_ANATOMY_LEDGER",
        "active_invariant": "build_full_row_level_failure_anatomy_from_failed_stage09_shards",
        "first_incomplete_invariant": "STAGE_01_FULL_FAILURE_ANATOMY_LEDGER",
        "exact_next_action": "Read failed Stage09 shards and old Stage09/Stage10 code, then write full row-level selected/dropped/avoid/route/coverage/acceptance anatomy ledgers.",
        "current_git_head": current_head,
        "dirty_tracked_and_untracked_path_summary": git_status,
        "prompt_path": rel(PROMPT_PATH),
        "prompt_hash": required_inputs["prompt"]["sha256"],
        "starter_path": rel(STARTER_PATH),
        "starter_hash": required_inputs["starter"]["sha256"],
        "forensic_report_path": rel(FORENSIC_PATH),
        "forensic_report_hash": required_inputs["forensic_report"]["sha256"],
        "failed_route_artifact_hashes_used": failed_artifacts,
        "replay_shard_count": len(shard_records),
        "replay_shard_row_count": total_shard_rows,
        "replay_shard_manifest_hash": shard_manifest_hash,
        "output_artifact_paths": {
            "session_state": rel(OUTPUT_STATE),
            "input_manifest": rel(OUTPUT_MANIFEST),
            "failed_route_invalidation_dossier": rel(OUTPUT_DOSSIER),
            "failed_route_invalidation_ledger": rel(OUTPUT_LEDGER),
        },
        "row_count_hash_coverage": {
            "stage09_summary_candidate_rows": failure_facts["candidate_rows"],
            "stage09_summary_written_replay_rows": failure_facts["stage09_written_replay_rows"],
            "stage09_gzip_shard_rows": total_shard_rows,
            "stage09_gzip_rows_match_summary": total_shard_rows == failure_facts["stage09_written_replay_rows"],
        },
        "stage_status_table": stage_status,
        "tests_and_verifiers_run": [],
        "failures_found": [
            "prior_stage10_completion_claim_invalid",
            "prior_stage09_production_candidate_selected_10_of_253234_and_lost_negative_r",
            "prior_prop_selector_replay_used_continuous_historical_account_path",
            "prior_acceptance_gates_allowed_no_trade_or_near_no_trade_failure",
        ],
        "repairs_applied": [
            "stage00_failed_route_artifacts_hashed_and_preserved",
            "stage00_failed_completion_claim_invalidated_in_new_route_artifacts",
            "stage00_initial_repair_session_state_created",
        ],
        "active_question_and_repair_ledger": [
            {
                "question": "Can the failed route be treated as activation-safe?",
                "status": "closed_no",
                "evidence_path": rel(OUTPUT_DOSSIER),
            },
            {
                "question": "What is the first incomplete invariant after invalidation?",
                "status": "closed_stage01_failure_anatomy",
                "evidence_path": rel(OUTPUT_STATE),
            },
        ],
        "remaining_same_evidence_class_actions": [
            "STAGE_01_FULL_FAILURE_ANATOMY_LEDGER",
            "STAGE_02_ACCEPTANCE_GATE_REPAIR",
            "STAGE_03_EXECUTABLE_STREAM_AND_ROUTE_SEMANTICS_REPAIR",
            "STAGE_04_EV_OPTIMIZED_PROP_CHALLENGE_GOVERNOR",
            "STAGE_05_VNEXT_AVOID_AND_PRE_AI_REPAIR",
            "STAGE_06_LTF_ENTRY_NOFILL_EXECUTION_REPAIR",
            "STAGE_07_AI_POLICY_AND_SUPERVISOR_REPAIR",
            "STAGE_08_REPAIRED_FORWARD_ONLY_REPLAY",
            "STAGE_09_PRODUCTION_CANDIDATE_DECISION_DOSSIER",
        ],
        "forbidden_boundary_actions_not_taken": [
            "live_trading",
            "broker_operation",
            "broker_account_order_history_deal_position_mutation",
            "paid_api_or_vendor_call",
            "source_deletion",
            "remote_push",
            "credential_change",
            "broker_facing_activation_flip",
        ],
        "context_refresh_timestamps": {
            "live_state_regenerated_before_stage00": True,
            "stage00_artifacts_created_at_utc": now,
        },
        "one_time_steers_applied": {},
        "completion_gate_status": "not_complete_stage01_first_incomplete",
    }
    with OUTPUT_STATE.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(session_state, handle, indent=2, sort_keys=True)
        handle.write("\n")

    return {
        "ok": True,
        "route_id": ROUTE_ID,
        "stage": "STAGE_00_INPUT_FREEZE_AND_FAILED_ROUTE_INVALIDATION",
        "first_incomplete_invariant": "STAGE_01_FULL_FAILURE_ANATOMY_LEDGER",
        "outputs": {
            "manifest": rel(OUTPUT_MANIFEST),
            "ledger": rel(OUTPUT_LEDGER),
            "dossier": rel(OUTPUT_DOSSIER),
            "session_state": rel(OUTPUT_STATE),
        },
        "candidate_rows": failure_facts["candidate_rows"],
        "baseline_selected_count": failure_facts["baseline_selected_count"],
        "new_mechanical_selected_count": failure_facts["new_mechanical_selected_count"],
        "new_mechanical_total_r": failure_facts["new_mechanical_total_r"],
        "stage09_shard_rows": total_shard_rows,
        "stage09_shard_rows_match_summary": total_shard_rows == failure_facts["stage09_written_replay_rows"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
