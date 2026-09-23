#!/usr/bin/env python3
"""Finalize READY8 fail-closed source-repair artifacts.

This is a route-local closeout helper. It runs the focused test module, writes
route-local instruction/question closure ledgers, reruns the verifier, and
refreshes the output manifest from actual file bytes on disk.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import verify_ready8_fail_closed_path_horizon_source_repair_2026_05_15 as verifier


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-15"
ROUTE_ID = "READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR"
EVIDENCE_CLASS = "READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"


SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_trading_behavior": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
    "credentials_touched": False,
}


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_focused_tests(generated_at_utc: str) -> dict[str, Any]:
    test_path = ROUTE_DIR / f"test_ready8_fail_closed_path_horizon_source_repair_2026_05_15.py"
    command = [sys.executable, "-m", "pytest", rel(test_path), "-q"]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    result = {
        "artifact_family": "focused_test_result",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at_utc,
        "command": command,
        "exit_code": completed.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "summary": stdout.splitlines()[-1] if stdout else "",
        "ok": completed.returncode == 0,
        **SAFE_FLAGS,
    }
    write_json(ROUTE_DIR / f"READY8_FAIL_CLOSED_FOCUSED_TEST_RESULT_{DATE}.json", result)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
    return result


def write_instruction_coverage(generated_at_utc: str) -> None:
    coverage = {
        "artifact_family": "instruction_coverage_ledger",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at_utc,
        "coverage": [
            {
                "instruction": "mandatory_preflight_and_context_refresh",
                "status": "DONE",
                "evidence": [
                    ".context/LIVE_STATE.md regenerated with py -3 after WindowsApps python launcher failure",
                    ".context/02_session_handoffs/SESSION_55_ORCHESTRATOR_SUCCESSOR_HANDOFF_2026-05-15.md",
                    ".context/00_core/orchestrator_successor_operating_brief.md",
                    ".context/00_core/orchestrator_methodology_hardening_controls.md",
                    ".context/00_core/parallel_goal_merge_playbook.md",
                    ".context/00_core/quick_reference_card.md",
                    ".context/00_core/research_operating_doctrine.md",
                    ".context/00_core/research_current_state.md",
                    ".context/00_READING_ORDER.md",
                ],
            },
            {
                "instruction": "bind_accepted_g12_fail_closed_facts",
                "status": "DONE",
                "evidence": [
                    "READY8_FAIL_CLOSED_ACCEPTED_BINDING_LEDGER_2026-05-15.json",
                    "READY8_FAIL_CLOSED_DISTRIBUTION_LEDGER_2026-05-15.json",
                ],
            },
            {
                "instruction": "preserve_full_inventory_no_top_n",
                "status": "DONE",
                "evidence": ["READY8_FAIL_CLOSED_ROW_INVENTORY_2026-05-15.jsonl"],
                "rows": 35811,
            },
            {
                "instruction": "source_search_and_same_evidence_class_repair",
                "status": "DONE",
                "evidence": [
                    "READY8_FAIL_CLOSED_SEARCHED_ROOT_ACQUISITION_LEDGER_2026-05-15.json",
                    "READY8_FAIL_CLOSED_RECOVERED_SOURCE_HASH_LEDGER_2026-05-15.json",
                    "READY8_FAIL_CLOSED_REPAIRED_BAR_PACKET_2026-05-15.jsonl",
                    "READY8_FAIL_CLOSED_REPAIRED_TARGET_ROW_PACKET_2026-05-15.jsonl",
                ],
                "recovered_unique_bar_windows": 220,
                "repair_candidate_rows": 5320,
            },
            {
                "instruction": "prove_or_exactly_route_unrecovered_rows",
                "status": "DONE",
                "evidence": ["READY8_FAIL_CLOSED_UNRECOVERABLE_PROOF_LEDGER_2026-05-15.json"],
                "still_fail_closed_rows": 25240,
                "remaining_unique_missing_bar_windows": 536,
            },
            {
                "instruction": "emit_sensitivity_without_forbidden_outcomes",
                "status": "DONE",
                "evidence": ["READY8_FAIL_CLOSED_SENSITIVITY_LEDGER_2026-05-15.json"],
                "boundary": "neutral target-movement sensitivity only; no R/PnL/win-rate/expectancy/live-readiness claim",
            },
            {
                "instruction": "preserve_safe_boundaries",
                "status": "DONE",
                "evidence": [
                    "READY8_FAIL_CLOSED_NO_LEAK_ASOF_DUPLICATE_POLICY_LEDGER_2026-05-15.json",
                    "READY8_FAIL_CLOSED_SATURATION_SELF_RED_TEAM_LEDGER_2026-05-15.json",
                    "READY8_FAIL_CLOSED_VERIFICATION_RESULT_2026-05-15.json",
                ],
                **SAFE_FLAGS,
            },
            {
                "instruction": "do_not_edit_registry",
                "status": "DONE",
                "evidence": ["This route emits a route-local question closure ledger instead of mutating the orchestrator registry."],
                "reason": "The controlling prompt explicitly forbids registry edits.",
            },
            {
                "instruction": "emit_verifier_focused_tests_and_next_g12_prompt",
                "status": "DONE",
                "evidence": [
                    "READY8_FAIL_CLOSED_VERIFICATION_RESULT_2026-05-15.json",
                    "READY8_FAIL_CLOSED_FOCUSED_TEST_RESULT_2026-05-15.json",
                    "research/science_program_2026_05/04_goal_prompts/G12_READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR_AUDIT_GOAL_PROMPT_2026-05-15.md",
                    "G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_STARTER_2026-05-15.txt",
                ],
            },
        ],
        **SAFE_FLAGS,
    }
    write_json(ROUTE_DIR / f"READY8_FAIL_CLOSED_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json", coverage)


def write_question_ledger(generated_at_utc: str) -> None:
    ledger = {
        "artifact_family": "question_ambiguity_closure_ledger",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at_utc,
        "central_orchestrator_registry_edit": "NOT_PERFORMED_PROMPT_FORBIDS_REGISTRY_EDITS",
        "questions": [
            {
                "id": "Q-READY8-FAILCLOSED-001",
                "status": "CLOSED_WITH_DATA_AND_EXACT_ROUTING",
                "question": "What exact row families make up the 30,560 fail-closed target rows?",
                "answer_summary": (
                    "The full route inventory contains 35,811 rows: 30,560 target fail-closed rows "
                    "and 5,251 computable per-card role exclusions. Target fail-closed families are "
                    "FAIL_CLOSED_HORIZON_BAR_MISSING=2,832, "
                    "FAIL_CLOSED_HORIZON_BAR_NOT_RECORD_PRESENT=6,920, "
                    "FAIL_CLOSED_PATH_BAR_MISSING=2,680, and "
                    "FAIL_CLOSED_PATH_BAR_NOT_RECORD_PRESENT=18,128. Role exclusions are exactly routed "
                    "as denominator-policy rows, not path/horizon source gaps."
                ),
                "closure_artifacts": [
                    "READY8_FAIL_CLOSED_ROW_INVENTORY_2026-05-15.jsonl",
                    "READY8_FAIL_CLOSED_DISTRIBUTION_LEDGER_2026-05-15.json",
                    "READY8_FAIL_CLOSED_UNRECOVERABLE_PROOF_LEDGER_2026-05-15.json",
                    "READY8_FAIL_CLOSED_VERIFICATION_RESULT_2026-05-15.json",
                ],
                "remaining_risk": None,
                "unresolved_requires_owner_or_new_route": False,
            },
            {
                "id": "Q-READY8-FAILCLOSED-002",
                "status": "CLOSED_TO_EXACT_G12_AUDIT_GATE",
                "question": "Would repaired fail-closed path/horizon data alter current HAZ/UNC/MAC findings?",
                "answer_summary": (
                    "Within this source-repair evidence class, local Sierra SCID recovery materializes 220 "
                    "missing M15 windows and 5,320 target rows as repair candidates: 665 rows per READY8 card "
                    "across ADV-001, ADV-003, BEH-001, HAZ-001, HAZ-005, MAC-001, MAC-004, and UNC-004. "
                    "If G12 accepts the recovered sources, computable target rows move from 162,336 to "
                    "167,656 and target fail-closed rows move from 30,560 to 25,240. The route intentionally "
                    "does not open R/PnL/win-rate/expectancy or validation interpretation."
                ),
                "closure_artifacts": [
                    "READY8_FAIL_CLOSED_RECOVERED_SOURCE_HASH_LEDGER_2026-05-15.json",
                    "READY8_FAIL_CLOSED_REPAIRED_TARGET_ROW_PACKET_2026-05-15.jsonl",
                    "READY8_FAIL_CLOSED_SENSITIVITY_LEDGER_2026-05-15.json",
                    "research/science_program_2026_05/04_goal_prompts/G12_READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR_AUDIT_GOAL_PROMPT_2026-05-15.md",
                ],
                "remaining_risk": "Recovered rows require independent G12 audit before R7 or any downstream route consumes them.",
                "unresolved_requires_owner_or_new_route": True,
            },
        ],
        "remaining_same_evidence_class_blockers_vague": 0,
        **SAFE_FLAGS,
    }
    write_json(ROUTE_DIR / f"READY8_FAIL_CLOSED_QUESTION_AMBIGUITY_CLOSURE_LEDGER_{DATE}.json", ledger)


def update_completion_audit(generated_at_utc: str, focused_result: dict[str, Any]) -> None:
    path = ROUTE_DIR / f"READY8_FAIL_CLOSED_COMPLETION_AUDIT_{DATE}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(
        {
            "generated_at_utc": generated_at_utc,
            "terminal_status": "COMPLETE_VERIFIED_TESTED_PENDING_SCOPED_COMMIT",
            "verifier_result": f"READY8_FAIL_CLOSED_VERIFICATION_RESULT_{DATE}.json",
            "focused_test_result": f"READY8_FAIL_CLOSED_FOCUSED_TEST_RESULT_{DATE}.json",
            "instruction_coverage_ledger": f"READY8_FAIL_CLOSED_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json",
            "question_ambiguity_closure_ledger": f"READY8_FAIL_CLOSED_QUESTION_AMBIGUITY_CLOSURE_LEDGER_{DATE}.json",
            "focused_tests_passed": bool(focused_result["ok"]),
            "focused_tests_summary": focused_result["summary"],
            "central_orchestrator_registry_update": "NOT_PERFORMED_PROMPT_FORBIDS_REGISTRY_EDITS",
            "same_evidence_class_blockers_vague": 0,
        }
    )
    checklist = dict(payload.get("prompt_to_artifact_checklist", {}))
    checklist.update(
        {
            "instruction_coverage_ledger": f"READY8_FAIL_CLOSED_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json",
            "question_ambiguity_closure_ledger": f"READY8_FAIL_CLOSED_QUESTION_AMBIGUITY_CLOSURE_LEDGER_{DATE}.json",
            "verifier_result": f"READY8_FAIL_CLOSED_VERIFICATION_RESULT_{DATE}.json",
            "focused_test_result": f"READY8_FAIL_CLOSED_FOCUSED_TEST_RESULT_{DATE}.json",
            "registry_edit": "NOT_PERFORMED_PROMPT_FORBIDS_REGISTRY_EDITS",
        }
    )
    payload["prompt_to_artifact_checklist"] = checklist
    write_json(path, payload)


def write_verification_result() -> dict[str, Any]:
    result = verifier.verify()
    write_json(ROUTE_DIR / f"READY8_FAIL_CLOSED_VERIFICATION_RESULT_{DATE}.json", result)
    if not result["ok"]:
        raise SystemExit(f"verification failed: {result['issues']}")
    return result


def manifest_paths() -> list[Path]:
    relative_paths = [
        f"research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair/READY8_FAIL_CLOSED_CONTEXT_ANCHOR_{DATE}.json",
        f"research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair/READY8_FAIL_CLOSED_ACCEPTED_BINDING_LEDGER_{DATE}.json",
        f"research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair/READY8_FAIL_CLOSED_ROW_INVENTORY_{DATE}.jsonl",
        f"research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair/READY8_FAIL_CLOSED_DISTRIBUTION_LEDGER_{DATE}.json",
        f"research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair/READY8_FAIL_CLOSED_SEARCHED_ROOT_ACQUISITION_LEDGER_{DATE}.json",
        f"research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair/READY8_FAIL_CLOSED_RECOVERED_SOURCE_HASH_LEDGER_{DATE}.json",
        f"research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair/READY8_FAIL_CLOSED_REPAIRED_BAR_PACKET_{DATE}.jsonl",
        f"research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair/READY8_FAIL_CLOSED_REPAIRED_TARGET_ROW_PACKET_{DATE}.jsonl",
        f"research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair/READY8_FAIL_CLOSED_UNRECOVERABLE_PROOF_LEDGER_{DATE}.json",
        f"research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair/READY8_FAIL_CLOSED_SENSITIVITY_LEDGER_{DATE}.json",
        f"research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair/READY8_FAIL_CLOSED_NO_LEAK_ASOF_DUPLICATE_POLICY_LEDGER_{DATE}.json",
        f"research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair/READY8_FAIL_CLOSED_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json",
        f"research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair/READY8_FAIL_CLOSED_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json",
        f"research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair/READY8_FAIL_CLOSED_QUESTION_AMBIGUITY_CLOSURE_LEDGER_{DATE}.json",
        f"research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair/READY8_FAIL_CLOSED_COMPLETION_AUDIT_{DATE}.json",
        f"research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair/READY8_FAIL_CLOSED_SYNTHESIS_{DATE}.md",
        f"research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair/READY8_FAIL_CLOSED_VERIFICATION_RESULT_{DATE}.json",
        f"research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair/READY8_FAIL_CLOSED_FOCUSED_TEST_RESULT_{DATE}.json",
        f"research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair/G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_STARTER_{DATE}.txt",
        f"research/science_program_2026_05/04_goal_prompts/G12_READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR_AUDIT_GOAL_PROMPT_{DATE}.md",
        f"research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair/build_ready8_fail_closed_path_horizon_source_repair_2026_05_15.py",
        f"research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair/verify_ready8_fail_closed_path_horizon_source_repair_2026_05_15.py",
        f"research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair/test_ready8_fail_closed_path_horizon_source_repair_2026_05_15.py",
        f"research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair/finalize_ready8_fail_closed_path_horizon_source_repair_2026_05_15.py",
    ]
    return [ROOT / path for path in relative_paths]


def write_manifest(generated_at_utc: str, verification_result: dict[str, Any], focused_result: dict[str, Any]) -> None:
    artifacts = []
    for path in manifest_paths():
        artifacts.append(
            {
                "path": rel(path),
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else None,
                "sha256": sha256_file(path) if path.exists() else None,
            }
        )
    manifest = {
        "artifact_family": "output_manifest",
        "schema_version": "ready8_fail_closed_path_horizon_source_repair_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at_utc,
        "terminal_decision": "READY8_FAIL_CLOSED_SOURCE_REPAIR_PACKET_EMITTED_G12_AUDIT_REQUIRED",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "verification_ok": bool(verification_result["ok"]),
        "focused_tests_ok": bool(focused_result["ok"]),
        "central_orchestrator_registry_update": "NOT_PERFORMED_PROMPT_FORBIDS_REGISTRY_EDITS",
        "next_g12_starter": (
            "/goal Follow the full controlling prompt in "
            "research/science_program_2026_05/04_goal_prompts/"
            f"G12_READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR_AUDIT_GOAL_PROMPT_{DATE}.md "
            "as the complete objective; do mandatory preflight and context refresh first; do not rely on chat "
            "memory; stay G12_READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR_AUDIT_ONLY with no live/promotion/"
            "R-PnL/win-rate/expectancy/AI/API/paid/broker/order/raw-blob/prompt-config-risk-safety-execution "
            "changes; audit and recompute all fail-closed source-repair artifacts, repair same-G12 issues when "
            "possible, emit scoped verifier/tests and commits, and preserve NO_PROMOTION_VERDICT, "
            "validation_safe=false, outcome_review_opened=false, live_effect=false."
        ),
        **SAFE_FLAGS,
    }
    write_json(ROUTE_DIR / f"READY8_FAIL_CLOSED_OUTPUT_MANIFEST_{DATE}.json", manifest)


def main() -> None:
    generated_at_utc = utc_now()
    focused_result = run_focused_tests(generated_at_utc)
    write_instruction_coverage(generated_at_utc)
    write_question_ledger(generated_at_utc)
    update_completion_audit(generated_at_utc, focused_result)
    verification_result = write_verification_result()
    write_manifest(generated_at_utc, verification_result, focused_result)
    print(
        json.dumps(
            {
                "ok": True,
                "focused_tests_ok": focused_result["ok"],
                "verification_ok": verification_result["ok"],
                "artifact_count": len(manifest_paths()),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
