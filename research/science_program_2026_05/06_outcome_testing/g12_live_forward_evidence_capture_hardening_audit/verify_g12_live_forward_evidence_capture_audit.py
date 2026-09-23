#!/usr/bin/env python3
"""Verify the G12 live-forward evidence capture hardening audit artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
TARGET = "3faa2b702f5eb64aba5485dc4155eb449565d359"

REQUIRED_CHANGED = {
    "src/research_infra/forward_capture.py",
    "scripts/backfill_fvg_ob_confluence_source_geometry.py",
    "src/research_infra/fvg_ob_confluence_audit.py",
    "src/research_infra/evidence_selection.py",
    "src/research_infra/missed_fill_opportunity_study.py",
    "scripts/analyze_missed_fill_opportunities.py",
    "src/components/tick_capture.py",
    "src/components/mt5_daemon_runtime.py",
    "scripts/watchdog.ps1",
    "scripts/_live_monitor_iter.py",
    "src/components/orchestrator.py",
    "scripts/backfill_account_pnl_truth_reconciliation.py",
    "scripts/backfill_broker_actual_r_audit.py",
    "scripts/verify_shadow_log_integrity.py",
}

FORBIDDEN_PREFIXES = (
    "config/",
    "prompts/",
    "shadow_logs/",
    "data/account_history/",
    "data/ticks/",
)

FORBIDDEN_EXACT = {
    "src/components/permissions.py",
    "src/components/execution.py",
}

REQUIRED_ARTIFACTS = [
    "DECISION_LEDGER_2026-05-12.json",
    "DECISION_LEDGER_2026-05-12.md",
    "COMMIT_DIFF_SCOPE_AUDIT_2026-05-12.md",
    "FVG_OB_GEOMETRY_CAPTURE_AUDIT_2026-05-12.md",
    "APPEND_ONLY_EVIDENCE_SELECTION_AUDIT_2026-05-12.md",
    "MISSED_FILL_STUDY_AUDIT_2026-05-12.md",
    "DAEMON_WATCHDOG_ORCHESTRATOR_SAFETY_AUDIT_2026-05-12.md",
    "NO_LEAK_FORBIDDEN_SURFACE_AUDIT_2026-05-12.md",
    "TARGETED_TEST_RESULT_2026-05-12.json",
    "TARGETED_TEST_RESULT_2026-05-12.md",
    "COMPLETION_AUDIT_2026-05-12.json",
    "COMPLETION_AUDIT_2026-05-12.md",
    "NEXT_LIVE_FORWARD_EVIDENCE_MONITORING_PROMPT_2026-05-12.md",
]


def _git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} is not a JSON object")
    return payload


def main() -> int:
    failures: list[str] = []
    changed = [line.strip() for line in _git(["diff-tree", "--no-commit-id", "--name-only", "-r", TARGET]).splitlines() if line.strip()]
    changed_set = set(changed)

    missing_changed = sorted(REQUIRED_CHANGED - changed_set)
    if missing_changed:
        failures.append(f"required target changed files missing: {missing_changed}")

    forbidden_paths = [
        path
        for path in changed
        if path in FORBIDDEN_EXACT or any(path.startswith(prefix) for prefix in FORBIDDEN_PREFIXES)
    ]
    if forbidden_paths:
        failures.append(f"forbidden target diff paths present: {forbidden_paths}")

    for name in REQUIRED_ARTIFACTS:
        if not (OUT / name).exists():
            failures.append(f"required artifact missing: {name}")

    decision = _read_json(OUT / "DECISION_LEDGER_2026-05-12.json")
    if decision.get("terminal_decision") != "ACCEPT_AS_G12_LIVE_FORWARD_EVIDENCE_CAPTURE_HARDENING_CONTROL_EVIDENCE":
        failures.append("decision ledger terminal decision mismatch")

    for json_name in ("DECISION_LEDGER_2026-05-12.json", "TARGETED_TEST_RESULT_2026-05-12.json"):
        payload = _read_json(OUT / json_name)
        if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            failures.append(f"{json_name} promotion_verdict mismatch")
        if payload.get("validation_safe") is not False:
            failures.append(f"{json_name} validation_safe is not false")
        if payload.get("outcome_review_opened") is not False:
            failures.append(f"{json_name} outcome_review_opened is not false")
        if payload.get("live_effect") is not False:
            failures.append(f"{json_name} live_effect is not false")

    test_result = _read_json(OUT / "TARGETED_TEST_RESULT_2026-05-12.json")
    if test_result.get("returncode") != 0 or "287 passed" not in str(test_result.get("summary", "")):
        failures.append("targeted test result does not record 287 passing tests")

    later = [line.strip() for line in _git(["diff", "--name-only", f"{TARGET}..HEAD"]).splitlines() if line.strip()]
    unexpected_later_source = [
        path
        for path in later
        if path.startswith("src/") or path.startswith("scripts/") or path.startswith("tests/") or path.startswith("config/") or path.startswith("prompts/")
    ]
    allowed_prompt = "research/science_program_2026_05/04_goal_prompts/G12_LIVE_FORWARD_EVIDENCE_CAPTURE_HARDENING_AUDIT_GOAL_PROMPT_2026-05-12.md"
    unexpected_later_source = [path for path in unexpected_later_source if path != allowed_prompt]
    if unexpected_later_source:
        failures.append(f"unexpected later source/script/test changes after target: {unexpected_later_source}")

    result = {
        "schema_version": "g12_live_forward_evidence_capture_hardening_verification_result_v1",
        "target_commit": TARGET,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "changed_files_checked": len(changed),
        "required_changed_files_present": not missing_changed,
        "forbidden_target_diff_paths": forbidden_paths,
        "required_artifacts_present": all((OUT / name).exists() for name in REQUIRED_ARTIFACTS),
        "targeted_tests_recorded": test_result.get("summary"),
        "failures": failures,
        "ok": not failures,
    }
    output = OUT / "G12_LIVE_FORWARD_EVIDENCE_CAPTURE_HARDENING_AUDIT_VERIFICATION_RESULT_2026-05-12.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
