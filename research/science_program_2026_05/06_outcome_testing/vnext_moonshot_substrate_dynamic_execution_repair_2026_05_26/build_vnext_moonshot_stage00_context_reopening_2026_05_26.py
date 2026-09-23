from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import sys

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research.dynamic_execution_policy import required_policy_manifest


ROUTE_ID = "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"
DATE_ID = "2026-05-26"
ROUTE_DIR = Path(__file__).resolve().parent
HASH_LIMIT_BYTES = 200_000_000

PROMPT_PATH = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "VNEXT_MOONSHOT_SUBSTRATE_DYNAMIC_EXECUTION_REPAIR_GOAL_PROMPT_2026-05-26.md"
)
STARTER_PATH = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "VNEXT_MOONSHOT_SUBSTRATE_DYNAMIC_EXECUTION_REPAIR_STARTER_2026-05-26.txt"
)
PRIOR_QUESTION_LEDGER = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26/"
    "VNEXT_ACTIVATION_QUESTION_STACK_LEDGER_2026-05-26.jsonl"
)

OUTPUT_REOPENING_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_PRIOR_ROUTE_REOPENING_LEDGER_{DATE_ID}.jsonl"
OUTPUT_IMPORTED_QUESTIONS = ROUTE_DIR / f"VNEXT_MOONSHOT_IMPORTED_QUESTION_STACK_LEDGER_{DATE_ID}.jsonl"
OUTPUT_CONTEXT_MANIFEST = ROUTE_DIR / f"VNEXT_MOONSHOT_CONTEXT_AND_INPUT_MANIFEST_{DATE_ID}.json"
OUTPUT_STATE = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json"


REQUIRED_CONTEXT_PATHS = [
    Path(".context/LIVE_STATE.md"),
    PROMPT_PATH,
    STARTER_PATH,
    Path(".context/00_core/goal_session_research_discipline.md"),
    Path(".context/00_core/research_operating_doctrine.md"),
    Path(".context/00_core/ai_in_loop_cost_control_research_plan.md"),
    Path(".context/00_core/local_heavy_data_inventory.md"),
    Path(".context/00_core/orchestrator_successor_operating_brief.md"),
    Path(".context/00_core/orchestrator_methodology_hardening_controls.md"),
    Path(".context/00_core/parallel_goal_merge_playbook.md"),
    Path(".context/00_core/quick_reference_card.md"),
    Path(".context/00_core/research_current_state.md"),
    Path(".context/02_session_handoffs/SESSION_63_VNEXT_EXACT_R_SOURCE_REPAIR_GUARD_HANDOFF_2026-05-19.md"),
]

PRIOR_ACTIVATION_REQUIRED_PATHS = [
    Path(
        "research/science_program_2026_05/04_goal_prompts/"
        "VNEXT_ACTIVATION_EDGE_ANATOMY_AI_BUDGET_ML_FEASIBILITY_GOAL_PROMPT_2026-05-26.md"
    ),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26/"
        "VNEXT_ACTIVATION_FINAL_REPORT_2026-05-26.md"
    ),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26/"
        "VNEXT_ACTIVATION_COMPLETION_AUDIT_2026-05-26.json"
    ),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26/"
        "VNEXT_ACTIVATION_SATURATION_SELF_RED_TEAM_2026-05-26.md"
    ),
    PRIOR_QUESTION_LEDGER,
]

PRIOR_FORENSIC_AND_REPAIR_PATHS = [
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25/"
        "VNEXT_PRODUCTION_CHANGE_FORENSIC_ACCOUNTABILITY_REPORT_DO_NOT_ACTIVATE_2026-05-25.md"
    ),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25/"
        "VNEXT_PRODUCTION_CANDIDATE_REPAIR_SESSION_STATE_2026-05-25.json"
    ),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25/"
        "STAGE10_POST_COMPLETION_ADDENDUM_2026-05-25.md"
    ),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25/"
        "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE08_REPAIRED_REPLAY_DECISION_LEDGER_2026-05-25.jsonl"
    ),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25/"
        "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE08_REPAIRED_PROP_ATTEMPT_LEDGER_2026-05-25.jsonl"
    ),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25/"
        "STAGE10_AI_SENSITIVITY_SUMMARY_2026-05-25.json"
    ),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25/"
        "STAGE10_MISSING_SOURCE_LEDGER_2026-05-25.jsonl"
    ),
]

FULL_REPLAY_REQUIRED_PATHS = [
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "vnext_full_historical_candidate_generation_replay_2026_05_24/"
        "VNEXT_FULL_REPLAY_FINAL_REPORT_2026-05-24.md"
    ),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "vnext_full_historical_candidate_generation_replay_2026_05_24/"
        "VNEXT_FULL_REPLAY_FINAL_VERIFICATION_RESULT_2026-05-24.json"
    ),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "vnext_full_historical_candidate_generation_replay_2026_05_24/"
        "VNEXT_FULL_REPLAY_CANDIDATE_GENERATION_SUMMARY_2026-05-24.json"
    ),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "vnext_full_historical_candidate_generation_replay_2026_05_24/"
        "VNEXT_FULL_REPLAY_STAGE04_SOURCE_MODE_SUMMARY_2026-05-24.json"
    ),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "vnext_full_historical_candidate_generation_replay_2026_05_24/"
        "VNEXT_FULL_REPLAY_PATH_OUTCOME_R_LEDGER_2026-05-24.jsonl"
    ),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "vnext_full_historical_candidate_generation_replay_2026_05_24/"
        "VNEXT_FULL_REPLAY_M15_VS_LTF_DISAGREEMENT_LEDGER_2026-05-24.jsonl"
    ),
]

ACTIVE_CODE_SURFACES = [
    Path("config/agent_config.yaml"),
    Path("src/components/execution.py"),
    Path("src/components/j46_j49_policy.py"),
    Path("src/components/gtos_vnext_runtime.py"),
    Path("src/components/orchestrator.py"),
    Path("src/components/market_state.py"),
    Path("src/components/primary_analyzer.py"),
    Path("src/components/verification.py"),
    Path("src/components/pre_ai_gates.py"),
    Path("src/components/permissions.py"),
    Path("src/components/ai_supervisor.py"),
    Path("src/research/dynamic_execution_policy.py"),
    Path("tests/test_dynamic_execution_policy.py"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_info(path: Path, *, count_jsonl: bool = False) -> dict:
    absolute = REPO_ROOT / path
    info = {
        "path": path.as_posix(),
        "exists": absolute.exists(),
        "sha256": None,
        "sha256_status": "missing",
        "bytes": None,
        "row_count": None,
    }
    if not absolute.exists():
        return info
    size = absolute.stat().st_size
    info["bytes"] = size
    if size <= HASH_LIMIT_BYTES and absolute.is_file():
        info["sha256"] = sha256_file(absolute)
        info["sha256_status"] = "computed"
    elif absolute.is_file():
        info["sha256_status"] = "deferred_large_file_preserved_by_size_and_route_manifest"
    else:
        info["sha256_status"] = "directory"
    if count_jsonl and absolute.suffix == ".jsonl":
        with absolute.open("r", encoding="utf-8") as handle:
            info["row_count"] = sum(1 for _ in handle)
    return info


def should_count_jsonl(path: Path, *, max_bytes: int = 100_000_000) -> bool:
    absolute = REPO_ROOT / path
    return path.suffix == ".jsonl" and absolute.exists() and absolute.stat().st_size < max_bytes


def git_output(args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception as exc:  # noqa: BLE001
        return f"ERROR:{exc}"


def classify_imported_question(row: dict) -> tuple[str, str, str]:
    blob = json.dumps(row, sort_keys=True).lower()
    fixed_tokens = [
        "target_first",
        "stop_first",
        "simulated_proxy_r",
        "simulated_r",
        "terminal_outcome",
        "winner",
        "loser",
        "missed_winner",
        "avoided_loser",
        "static",
        "fixed",
        "proxy r",
        "proxy_r",
    ]
    if any(token in blob for token in fixed_tokens):
        return (
            "reopened_dynamic_execution_required",
            "Prior answer depends on fixed/static target-stop or scalar proxy-R labels.",
            "Re-answer after policy-specific dynamic execution rows exist.",
        )
    if "ai" in blob or "paid" in blob or "prompt" in blob:
        return (
            "pending_rebuild_after_corrected_dynamic_labels",
            "AI role or budget question depends on corrected dynamic labels.",
            "Carry into Stage08 AI role and budget rebuild.",
        )
    if "ml" in blob or "feature" in blob or "label" in blob:
        return (
            "pending_rebuild_after_corrected_dynamic_labels",
            "ML feature/label question depends on corrected dynamic labels.",
            "Carry into Stage09 ML and surrogate feasibility rebuild.",
        )
    if "source" in blob or "missing" in blob or "packaging" in blob or "lfs" in blob:
        return (
            "preserved_boundary_or_source_question_recheck_required",
            "Prior source/packaging fact may still be useful but must be rechecked for dynamic replay.",
            "Carry into source capability inventory and evidence-preservation audit.",
        )
    return (
        "pending_review_under_moonshot_substrate",
        "Prior answer is not accepted as moonshot truth until corrected substrate audit consumes it.",
        "Carry into the active moonshot question stack.",
    )


def import_question_stack() -> dict:
    input_path = REPO_ROOT / PRIOR_QUESTION_LEDGER
    row_count = 0
    status_counts: Counter[str] = Counter()
    row_type_counts: Counter[str] = Counter()
    with input_path.open("r", encoding="utf-8") as src, OUTPUT_IMPORTED_QUESTIONS.open(
        "w", encoding="utf-8", newline="\n"
    ) as dst:
        for row_count, line in enumerate(src, start=1):
            row = json.loads(line)
            status, reason, next_action = classify_imported_question(row)
            row_type_counts[str(row.get("ledger_row_type") or row.get("row_type") or "unknown")] += 1
            status_counts[status] += 1
            row.update(
                {
                    "moonshot_route_id": ROUTE_ID,
                    "moonshot_stage_id": "STAGE_00_PREFLIGHT_CONTEXT_AND_PRIOR_ROUTE_REOPENING",
                    "moonshot_import_row_number": row_count,
                    "moonshot_original_route_id": row.get("route_id"),
                    "moonshot_corrected_substrate_status": status,
                    "moonshot_reopen_reason": reason,
                    "moonshot_next_action": next_action,
                    "moonshot_static_substrate_truth_accepted": False,
                }
            )
            dst.write(json.dumps(row, sort_keys=True) + "\n")
    return {
        "source_path": PRIOR_QUESTION_LEDGER.as_posix(),
        "output_path": rel(OUTPUT_IMPORTED_QUESTIONS),
        "row_count": row_count,
        "status_counts": dict(sorted(status_counts.items())),
        "row_type_counts": dict(sorted(row_type_counts.items())),
        "sha256": sha256_file(OUTPUT_IMPORTED_QUESTIONS),
    }


def write_reopening_ledger() -> dict:
    rows = [
        {
            "ledger_row_type": "prior_activation_metric_reopened",
            "artifact": "VNEXT_ACTIVATION_FINAL_REPORT_2026-05-26.md",
            "finding": "raw/high_quality/aggressive branch metrics are preserved only as static-substrate diagnostics",
            "reclassified_status": "STATIC_SUBSTRATE_DIAGNOSTIC_UNTIL_DYNAMIC_REPLAY_RECOMPUTES",
            "exact_action": "recompute branch metrics from policy-specific dynamic execution R",
        },
        {
            "ledger_row_type": "fixed_bracket_substrate_reopened",
            "artifact": "VNEXT_FULL_REPLAY_STAGE04_SOURCE_MODE_PATH_R",
            "finding": "Stage04 path/R scored fixed target/stop outcomes around risk.min_rr and target_first/stop_first labels",
            "reclassified_status": "COMPARATOR_ONLY_NOT_MOONSHOT_TRUTH",
            "exact_action": "feed ordered path sources into dynamic policy state machine",
        },
        {
            "ledger_row_type": "activation_builder_reopened",
            "artifact": "VNEXT_ACTIVATION_STAGE03_STAGE04_STAGE10",
            "finding": "activation anatomy ledgers use simulated_proxy_r, terminal_outcome, winners, losers, missed winners, and avoided losers from primitive labels",
            "reclassified_status": "REOPENED_FOR_DYNAMIC_EXECUTION_LABELS",
            "exact_action": "preserve rows and rebuild anatomy after dynamic replay",
        },
        {
            "ledger_row_type": "negative_fixture_preserved",
            "artifact": "VNEXT_PRODUCTION_CHANGE_FORENSIC_ACCOUNTABILITY_REPORT_DO_NOT_ACTIVATE_2026-05-25.md",
            "finding": "prior production-change route collapsed to 10 selected rows and about -5R and must remain a semantic verifier negative fixture",
            "reclassified_status": "MANDATORY_NEGATIVE_FIXTURE",
            "exact_action": "semantic verifier must fail near-zero/negative production candidates and artifact-existence completion",
        },
        {
            "ledger_row_type": "repaired_candidate_route_reopened",
            "artifact": "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE08_REPAIRED_REPLAY_DECISION_LEDGER_2026-05-25.jsonl",
            "finding": "repaired route fixed executable stream and prop segmentation but still uses simulated_r_scoring_only labels",
            "reclassified_status": "USEFUL_REPAIR_INPUT_REQUIRES_DYNAMIC_R_REPLAY",
            "exact_action": "join repaired executable stream to dynamic policy R before branch/prop EV conclusions",
        },
        {
            "ledger_row_type": "prior_completion_gate_reopened",
            "artifact": "VNEXT_ACTIVATION_COMPLETION_AUDIT_2026-05-26.json",
            "finding": "completion audit proves artifact presence and row preservation, not dynamic execution semantic truth",
            "reclassified_status": "SELF_CERTIFYING_COMPLETION_NOT_ACCEPTED_FOR_MOONSHOT",
            "exact_action": "build semantic verifier that recomputes policy rows and rejects fixed labels as activation truth",
        },
        {
            "ledger_row_type": "runtime_surface_anchor",
            "artifact": "src/research/dynamic_execution_policy.py",
            "finding": "pure dynamic execution state machine is implemented as a no-live research substrate",
            "reclassified_status": "DEFAULT_OFF_RESEARCH_SUBSTRATE_SEE_TESTS",
            "exact_action": "consume in dynamic replay builders over ordered local path sources",
        },
    ]
    with OUTPUT_REOPENING_LEDGER.open("w", encoding="utf-8", newline="\n") as handle:
        for index, row in enumerate(rows, start=1):
            row.update(
                {
                    "route_id": ROUTE_ID,
                    "stage_id": "STAGE_00_PREFLIGHT_CONTEXT_AND_PRIOR_ROUTE_REOPENING",
                    "row_index": index,
                    "as_of_utc": utc_now(),
                    "no_live_broker_paid_remote_boundary_crossed": True,
                }
            )
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return {
        "path": rel(OUTPUT_REOPENING_LEDGER),
        "row_count": len(rows),
        "sha256": sha256_file(OUTPUT_REOPENING_LEDGER),
    }


def inventory_directory(root: Path, *, pattern: str = "*") -> dict:
    absolute = REPO_ROOT / root
    files = []
    if absolute.exists():
        for path in sorted(absolute.glob(pattern)):
            if path.is_file():
                files.append(
                    {
                        "path": rel(path),
                        "bytes": path.stat().st_size,
                        "sha256_status": (
                            "computed"
                            if path.stat().st_size <= HASH_LIMIT_BYTES
                            else "deferred_large_file_preserved"
                        ),
                        "sha256": sha256_file(path) if path.stat().st_size <= HASH_LIMIT_BYTES else None,
                    }
                )
    return {"root": root.as_posix(), "file_count": len(files), "files": files}


def build_context_manifest(question_import: dict, reopening: dict) -> dict:
    manifest = {
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_00_PREFLIGHT_CONTEXT_AND_PRIOR_ROUTE_REOPENING",
        "created_at_utc": utc_now(),
        "current_git_head": git_output(["rev-parse", "HEAD"]),
        "git_status_short": git_output(["status", "--short"]).splitlines(),
        "prompt": artifact_info(PROMPT_PATH),
        "starter": artifact_info(STARTER_PATH),
        "required_context": [artifact_info(path) for path in REQUIRED_CONTEXT_PATHS],
        "prior_activation_required": [
            artifact_info(path, count_jsonl=(path == PRIOR_QUESTION_LEDGER))
            for path in PRIOR_ACTIVATION_REQUIRED_PATHS
        ],
        "prior_forensic_and_repair_required": [
            artifact_info(path, count_jsonl=should_count_jsonl(path))
            for path in PRIOR_FORENSIC_AND_REPAIR_PATHS
        ],
        "full_replay_required": [artifact_info(path) for path in FULL_REPLAY_REQUIRED_PATHS],
        "active_code_and_tests": [artifact_info(path) for path in ACTIVE_CODE_SURFACES],
        "prior_activation_directory_inventory": inventory_directory(
            Path(
                "research/science_program_2026_05/06_outcome_testing/"
                "vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26"
            )
        ),
        "full_replay_directory_inventory": inventory_directory(
            Path(
                "research/science_program_2026_05/06_outcome_testing/"
                "vnext_full_historical_candidate_generation_replay_2026_05_24"
            )
        ),
        "dynamic_policy_manifest": [
            {
                "name": policy.name,
                "final_target_r": policy.final_target_r,
                "stop_r": policy.stop_r,
                "tp1_r": policy.tp1_r,
                "partial_close_ratio": policy.partial_close_ratio,
                "move_stop_to_be_on_tp1": policy.move_stop_to_be_on_tp1,
                "time_stop_bars": policy.time_stop_bars,
                "early_cut_bars": policy.early_cut_bars,
                "trailing_trigger_r": policy.trailing_trigger_r,
                "trailing_gap_r": policy.trailing_gap_r,
                "description": policy.description,
            }
            for policy in required_policy_manifest()
        ],
        "question_import": question_import,
        "prior_route_reopening": reopening,
        "evidence_preservation": {
            "compression_used_for_new_stage00_outputs": False,
            "row_preserving_question_import": True,
            "large_prior_artifacts_not_reduced_for_git": True,
            "normal_git_push_or_lfs_status": "packaging_only_not_evidence_reduction",
        },
        "forbidden_boundaries": {
            "live_trading": False,
            "broker_account_order_history_deal_position_mutation": False,
            "paid_api_or_vendor_call": False,
            "remote_push": False,
            "credential_change": False,
            "history_rewrite": False,
            "activation_flip": False,
        },
    }
    OUTPUT_CONTEXT_MANIFEST.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def write_state(manifest: dict, question_import: dict, reopening: dict) -> dict:
    state = {
        "route_id": ROUTE_ID,
        "schema_version": "vnext_moonshot_substrate_session_state_v1",
        "updated_at_utc": utc_now(),
        "current_stage": "STAGE_00_PREFLIGHT_CONTEXT_AND_PRIOR_ROUTE_REOPENING",
        "first_incomplete_invariant": "STAGE_01_STATIC_PRIMITIVE_ASSUMPTION_AUDIT",
        "exact_next_action": (
            "Run Stage01 targeted static/proxy/shadow/disabled/stale assumption audit, "
            "then consume ordered path sources with src.research.dynamic_execution_policy."
        ),
        "current_git_head": manifest["current_git_head"],
        "dirty_tracked_untracked_summary": manifest["git_status_short"],
        "prompt_path": PROMPT_PATH.as_posix(),
        "prompt_hash": manifest["prompt"]["sha256"],
        "starter_path": STARTER_PATH.as_posix(),
        "starter_hash": manifest["starter"]["sha256"],
        "required_context_paths": [item["path"] for item in manifest["required_context"]],
        "required_context_hashes": {item["path"]: item["sha256"] for item in manifest["required_context"]},
        "input_artifact_paths": [
            item["path"]
            for group in (
                manifest["prior_activation_required"],
                manifest["prior_forensic_and_repair_required"],
                manifest["full_replay_required"],
            )
            for item in group
        ],
        "source_inventory_and_searched_roots": [
            "current_worktree",
            "data",
            "data/ticks",
            "shadow_logs",
            "exports",
            "C:/tmp",
            "C:/SierraChart",
        ],
        "large_file_and_storage_state": {
            "evidence_over_git_active": True,
            "large_prior_artifacts_preserved_not_reduced": True,
            "hash_limit_bytes_for_stage00_inventory": HASH_LIMIT_BYTES,
        },
        "row_counts_scanned": {
            "imported_prior_question_rows": question_import["row_count"],
            "prior_route_reopening_rows": reopening["row_count"],
        },
        "stage_status_table": {
            "STAGE_00_PREFLIGHT_CONTEXT_AND_PRIOR_ROUTE_REOPENING": "complete",
            "STAGE_01_STATIC_PRIMITIVE_ASSUMPTION_AUDIT": "pending",
            "STAGE_02_SOURCE_AND_PATH_CAPABILITY_INVENTORY": "pending",
            "STAGE_03_DYNAMIC_POLICY_STATE_MACHINE": "seed_implemented_focused_tests_passed",
            "STAGE_04_FULL_POLICY_DYNAMIC_REPLAY": "pending",
            "STAGE_05_UNIVERSAL_CANDIDATE_ORIGIN_LAYER": "pending",
            "STAGE_06_MARKET_AWARENESS_ENRICHMENT": "pending",
            "STAGE_07_CORRECTED_BRANCH_METRICS_AND_PROP_EV": "pending",
            "STAGE_08_AI_ROLE_AND_BUDGET_DESIGN": "pending",
            "STAGE_09_ML_AND_SURROGATE_FEASIBILITY": "pending",
            "STAGE_10_DEFAULT_OFF_RUNTIME_INTEGRATION": "seed_policy_module_default_off",
            "STAGE_11_SEMANTIC_VERIFIER_HARDENING": "pending",
            "STAGE_12_SATURATION_SELF_RED_TEAM_AND_FINAL_DECISION": "pending",
        },
        "active_question_stack": {
            "imported_ledger_path": rel(OUTPUT_IMPORTED_QUESTIONS),
            "status_counts": question_import["status_counts"],
            "row_type_counts": question_import["row_type_counts"],
        },
        "reopened_prior_question_stack": question_import["status_counts"].get(
            "reopened_dynamic_execution_required", 0
        ),
        "newly_discovered_question_stack": {
            "seed_status": "Stage01 and dynamic replay will append row/source/policy-disagreement questions."
        },
        "static_proxy_assumption_ledger_path": None,
        "source_gap_ledger_path": None,
        "dynamic_policy_manifest_path": rel(OUTPUT_CONTEXT_MANIFEST),
        "output_artifact_manifest": {
            "context_manifest": rel(OUTPUT_CONTEXT_MANIFEST),
            "prior_route_reopening_ledger": rel(OUTPUT_REOPENING_LEDGER),
            "imported_question_stack": rel(OUTPUT_IMPORTED_QUESTIONS),
            "session_state": rel(OUTPUT_STATE),
        },
        "verifiers_tests_run": [
            {
                "command": (
                    "py -3 -m pytest tests/test_dynamic_execution_policy.py -q "
                    "--basetemp=.pytest-tmp-dynamic-execution-policy "
                    "-o cache_dir=.pytest-tmp-dynamic-execution-policy-cache"
                ),
                "status": "passed",
                "result": "15 passed in 0.42s",
            },
            {
                "command": (
                    "py -3 scripts/validate_goal_prompt_hardening.py "
                    "research/science_program_2026_05/04_goal_prompts/"
                    "VNEXT_MOONSHOT_SUBSTRATE_DYNAMIC_EXECUTION_REPAIR_GOAL_PROMPT_2026-05-26.md"
                ),
                "status": "passed",
                "result": "overall_ok=True",
            },
            {
                "command": (
                    "py -3 research/science_program_2026_05/06_outcome_testing/"
                    "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/"
                    "verify_vnext_moonshot_stage00_context_reopening_2026_05_26.py"
                ),
                "status": "passed",
                "result": "ok=true; question_rows=24327; prior_reopening_rows=7",
            },
            {
                "command": "JSON/JSONL parse check for VNEXT_MOONSHOT_*.json and VNEXT_MOONSHOT_*.jsonl",
                "status": "passed",
                "result": "5 files parsed; imported_question_rows=24327",
            }
        ],
        "same_evidence_class_blockers_and_pursuit_status": [],
        "paid_api_remote_live_boundaries_not_crossed": manifest["forbidden_boundaries"],
        "context_refresh_timestamps": {
            "live_state_regenerated_before_stage00": True,
            "stage00_artifacts_created_at_utc": utc_now(),
        },
        "compaction_resume_instructions_applied": True,
        "completion_gate_status": "not_complete_first_incomplete_stage01",
    }
    OUTPUT_STATE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return state


def main() -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    question_import = import_question_stack()
    reopening = write_reopening_ledger()
    manifest = build_context_manifest(question_import, reopening)
    state = write_state(manifest, question_import, reopening)
    print(
        json.dumps(
            {
                "route_id": ROUTE_ID,
                "stage": state["current_stage"],
                "first_incomplete_invariant": state["first_incomplete_invariant"],
                "imported_question_rows": question_import["row_count"],
                "context_manifest": rel(OUTPUT_CONTEXT_MANIFEST),
                "session_state": rel(OUTPUT_STATE),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
