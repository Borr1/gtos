from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_ID = "vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25"
REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25"
)
STATE_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_SESSION_STATE_2026-05-25.json"
SUMMARY_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_REPLAY_METRICS_SUMMARY_2026-05-25.json"
)
DOSSIER_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_DECISION_DOSSIER_2026-05-25.md"
AUDIT_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_COMPLETION_AUDIT_2026-05-25.json"
VERIFY_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE09_VERIFICATION_RESULT_2026-05-25.json"
)

FINAL_STATES = {
    "production_candidate_viable_after_repair",
    "production_candidate_failed_with_full_failure_anatomy",
    "redesign_required_with_exact_repair_backlog",
}
REQUIRED_DOSSIER_HEADINGS = [
    "## Verdict",
    "## Runtime And System Behavior Changed",
    "## Code Config And Tests Changed",
    "## Research And Replay Intelligence Consumed",
    "## Coverage",
    "## What Still Fails Or Remains Bounded",
    "## Less Conservative Changes",
    "## Stricter Changes",
    "## Killed Demoted Redesigned Promoted",
    "## Expanded-Market Executability",
    "## Default-Off And Activation Path",
    "## Exact Next Action Before Broker-Facing Activation",
]


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def repo(path: Path) -> Path:
    return REPO_ROOT / path


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(repo(path).read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    repo(path).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with repo(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def git_status_short() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def validate(audit: dict[str, Any], summary: dict[str, Any], dossier_text: str) -> list[str]:
    failures: list[str] = []
    decision = audit.get("decision") or {}
    checks = audit.get("completion_checks") or {}
    final_state = audit.get("final_state")
    if audit.get("route_id") != ROUTE_ID:
        failures.append("route_id_mismatch")
    if final_state not in FINAL_STATES:
        failures.append("invalid_final_state")
    if audit.get("schema_version") != "vnext_production_candidate_repair_completion_audit_v1":
        failures.append("schema_version_mismatch")
    for name, passed in checks.items():
        if not bool(passed):
            failures.append(f"completion_check_failed:{name}")
    for heading in REQUIRED_DOSSIER_HEADINGS:
        if heading not in dossier_text:
            failures.append(f"dossier_missing_heading:{heading}")
    if final_state not in dossier_text:
        failures.append("dossier_missing_final_state")
    if decision.get("final_state") != final_state:
        failures.append("decision_final_state_mismatch")
    if final_state == "production_candidate_viable_after_repair":
        if decision.get("hard_failures"):
            failures.append("viable_state_has_hard_failures")
        if int(decision.get("selected_count") or 0) <= 0:
            failures.append("viable_state_selected_count_zero")
        if int(decision.get("performance_rows") or 0) <= 0:
            failures.append("viable_state_performance_rows_zero")
        if float(decision.get("risk_adjusted_r") or 0) <= 0:
            failures.append("viable_state_nonpositive_risk_adjusted_r")
        if float(decision.get("expectancy_r") or 0) <= 0:
            failures.append("viable_state_nonpositive_expectancy")
        if float(decision.get("profit_factor") or 0) < 1.0:
            failures.append("viable_state_profit_factor_below_one")
        if float(decision.get("selected_to_baseline_ratio") or 0) < 0.25:
            failures.append("viable_state_selected_ratio_below_floor")
    if summary.get("candidate_universe_rows") != 253234:
        failures.append("candidate_universe_rows_mismatch")
    if summary.get("executable_stream_rows") != 79320:
        failures.append("executable_stream_rows_mismatch")
    if summary.get("paid_api_or_vendor_calls_made") != 0:
        failures.append("paid_api_or_vendor_calls_made")
    if summary.get("broker_facing_activation_change") is not False:
        failures.append("broker_facing_activation_changed")
    if summary.get("off_kz_treatment", {}).get("off_kz_rows_in_repaired_selected_stream") != 0:
        failures.append("off_kz_rows_selected")
    if not summary.get("no_paid_call_replay_diagnostic_only"):
        failures.append("no_paid_call_not_diagnostic")
    if not all((summary.get("required_metric_coverage") or {}).values()):
        failures.append("required_metric_coverage_incomplete")
    if len(audit.get("remaining_actions_before_broker_activation") or []) < 3:
        failures.append("activation_prerequisites_missing")
    if audit.get("same_evidence_class_exhaustion_reason") in {None, ""}:
        failures.append("same_evidence_class_exhaustion_missing")
    return failures


def mark_complete(audit: dict[str, Any], verification_result: dict[str, Any]) -> None:
    audit["completion_gate_status"] = audit["final_state"]
    audit["stage09_verifier"] = {
        "ok": verification_result["ok"],
        "result_path": rel(VERIFY_PATH),
        "created_at_utc": verification_result["created_at_utc"],
    }
    write_json(AUDIT_PATH, audit)

    state = load_json(STATE_PATH)
    state["updated_at_utc"] = utc_now()
    state["current_git_head"] = git_head()
    state["dirty_tracked_and_untracked_path_summary"] = git_status_short()
    state["active_invariant"] = audit["final_state"]
    state["current_stage"] = "COMPLETE"
    state["first_incomplete_invariant"] = "NONE"
    state["completion_gate_status"] = audit["final_state"]
    state["exact_next_action"] = (
        "No broker-facing activation was performed. Next action before activation: "
        "owner-approved paid-AI validation, source-capture/exclusion handling, "
        "paper/shadow run, and a separate production-change activation dossier."
    )
    state.setdefault("stage_status_table", {})[
        "STAGE_09_PRODUCTION_CANDIDATE_DECISION_DOSSIER"
    ] = "complete"
    state.setdefault("repairs_applied", []).append(
        "stage09_truthful_decision_dossier_and_completion_audit_materialized"
    )
    state.setdefault("output_artifact_paths", {})[
        "stage09_decision_dossier"
    ] = rel(DOSSIER_PATH)
    state.setdefault("output_artifact_paths", {})[
        "completion_audit"
    ] = rel(AUDIT_PATH)
    state.setdefault("output_artifact_paths", {})[
        "stage09_verification_result"
    ] = rel(VERIFY_PATH)
    state.setdefault("row_count_hash_coverage", {}).update(
        {
            "stage09_decision_dossier_sha256": sha256_file(DOSSIER_PATH),
            "stage09_completion_audit_sha256": sha256_file(AUDIT_PATH),
            "stage09_verification_result_sha256": sha256_file(VERIFY_PATH),
        }
    )
    state.setdefault("verification_status", {})["stage09_verifier_ok"] = True
    state.setdefault("active_question_and_repair_ledger", []).append(
        {
            "question": "What is the final route state after the repaired production-candidate decision dossier?",
            "status": audit["final_state"],
            "evidence_path": rel(AUDIT_PATH),
            "selected_rows": audit["decision"]["selected_count"],
            "risk_adjusted_r": audit["decision"]["risk_adjusted_r"],
        }
    )
    state.setdefault("tests_and_verifiers_run", []).append(
        {
            "command": "py -3 verify_vnext_production_candidate_repair_stage09_decision_dossier_2026_05_25.py --mark-complete",
            "status": "passed",
            "result": {
                "ok": True,
                "final_state": audit["final_state"],
                "decision_dossier_sha256": sha256_file(DOSSIER_PATH),
                "completion_audit_sha256": sha256_file(AUDIT_PATH),
            },
        }
    )
    write_json(STATE_PATH, state)


def run(mark: bool) -> dict[str, Any]:
    audit = load_json(AUDIT_PATH)
    summary = load_json(SUMMARY_PATH)
    dossier_text = repo(DOSSIER_PATH).read_text(encoding="utf-8")
    failures = validate(audit, summary, dossier_text)
    result = {
        "schema_version": "vnext_production_candidate_repair_stage09_verification_v1",
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_09_PRODUCTION_CANDIDATE_DECISION_DOSSIER",
        "created_at_utc": utc_now(),
        "ok": not failures,
        "failures": failures,
        "final_state": audit.get("final_state"),
        "decision_dossier": rel(DOSSIER_PATH),
        "decision_dossier_sha256": sha256_file(DOSSIER_PATH),
        "completion_audit": rel(AUDIT_PATH),
        "completion_audit_sha256_before_mark": sha256_file(AUDIT_PATH),
        "candidate_universe_rows": summary.get("candidate_universe_rows"),
        "executable_stream_rows": summary.get("executable_stream_rows"),
        "selected_rows": audit.get("decision", {}).get("selected_count"),
        "performance_rows": audit.get("decision", {}).get("performance_rows"),
        "paid_api_or_vendor_calls_made": summary.get("paid_api_or_vendor_calls_made"),
        "broker_facing_activation_change": summary.get("broker_facing_activation_change"),
    }
    write_json(VERIFY_PATH, result)
    if failures:
        return result
    if mark:
        mark_complete(audit, result)
        result["completion_audit_sha256_after_mark"] = sha256_file(AUDIT_PATH)
        write_json(VERIFY_PATH, result)
        # Recompute the state hash after the final verification result changed.
        state = load_json(STATE_PATH)
        state.setdefault("row_count_hash_coverage", {})[
            "stage09_verification_result_sha256"
        ] = sha256_file(VERIFY_PATH)
        write_json(STATE_PATH, state)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-complete", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(mark=args.mark_complete), sort_keys=True))


if __name__ == "__main__":
    main()
