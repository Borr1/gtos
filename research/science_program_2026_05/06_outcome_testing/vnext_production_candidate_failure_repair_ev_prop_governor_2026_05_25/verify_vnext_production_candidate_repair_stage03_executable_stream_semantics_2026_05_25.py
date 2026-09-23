from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
STATE_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_SESSION_STATE_2026-05-25.json"
SUMMARY_PATH = (
    ROUTE_DIR
    / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE03_EXECUTABLE_STREAM_SEMANTICS_SUMMARY_2026-05-25.json"
)
LEDGER_PATH = (
    ROUTE_DIR
    / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE03_EXECUTABLE_STREAM_SEMANTICS_LEDGER_2026-05-25.jsonl"
)
VERIFY_RESULT_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE03_VERIFICATION_RESULT_2026-05-25.json"
)


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN"


def scan_ledger() -> dict[str, Any]:
    count = 0
    prop_eligible = 0
    legacy_mixed_bad = 0
    off_kz_bad = 0
    scenario_counts: dict[str, int] = {}
    old_selected_non_follow_now_nonexec = 0
    with LEDGER_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            count += 1
            semantics = row.get("repaired_route_semantics") or {}
            membership = row.get("scenario_membership") or {}
            if semantics.get("prop_governance_eligible_after_stage03"):
                prop_eligible += 1
            if semantics.get("legacy_or_mixed") and semantics.get(
                "prop_governance_eligible_after_stage03"
            ):
                legacy_mixed_bad += 1
            if semantics.get("off_kz") and semantics.get("prop_governance_eligible_after_stage03"):
                off_kz_bad += 1
            if row.get("old_new_mechanical_selected") and semantics.get("route_decision") != "FOLLOW":
                if not semantics.get("vnext_executable_stream_without_prop"):
                    old_selected_non_follow_now_nonexec += 1
            for name, selected in membership.items():
                if selected:
                    scenario_counts[name] = scenario_counts.get(name, 0) + 1
    return {
        "row_count": count,
        "sha256": sha256_file(LEDGER_PATH),
        "prop_eligible_rows": prop_eligible,
        "legacy_mixed_bad_prop_eligible_rows": legacy_mixed_bad,
        "off_kz_bad_prop_eligible_rows": off_kz_bad,
        "scenario_selected_counts": scenario_counts,
        "old_selected_non_follow_now_nonexecutable_rows": old_selected_non_follow_now_nonexec,
    }


def verify() -> dict[str, Any]:
    failures: list[str] = []
    if not SUMMARY_PATH.exists():
        failures.append("missing_stage03_summary")
    if not LEDGER_PATH.exists():
        failures.append("missing_stage03_ledger")
    if failures:
        return {"ok": False, "failures": failures}

    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    scan = scan_ledger()
    expected_rows = int(summary.get("row_count") or 0)
    if scan["row_count"] != expected_rows:
        failures.append(f"ledger_row_count_mismatch:{scan['row_count']}!={expected_rows}")
    repair = summary.get("prop_budget_application_repair") or {}
    if not repair.get("prop_budget_applies_only_to_executable_stream"):
        failures.append("prop_budget_not_marked_executable_stream_only")
    if scan["prop_eligible_rows"] != repair.get("corrected_prop_governance_input_rows"):
        failures.append("prop_eligible_count_mismatch")
    if scan["legacy_mixed_bad_prop_eligible_rows"] != 0:
        failures.append("legacy_mixed_rows_still_prop_eligible")
    if scan["off_kz_bad_prop_eligible_rows"] != 0:
        failures.append("off_kz_rows_still_prop_eligible")
    scenario_metrics = summary.get("scenario_metrics") or {}
    required_scenarios = {
        "current_baseline_executable_stream",
        "baseline_executable_stream_plus_prop_contract",
        "vnext_route_pressure_without_prop_governance",
        "vnext_executable_stream_without_prop_governance",
        "vnext_executable_stream_with_ev_prop_governance_contract",
        "external_budget_only_prop_comparison_contract",
        "ai_no_paid_call_diagnostic",
        "ltf_entry_nofill_execution_change_diagnostic",
    }
    missing_scenarios = sorted(required_scenarios - set(scenario_metrics))
    if missing_scenarios:
        failures.append(f"missing_scenarios:{','.join(missing_scenarios)}")
    for name in required_scenarios & set(scenario_metrics):
        record = scenario_metrics[name]
        if "selected_only_coverage" not in record:
            failures.append(f"missing_selected_only_coverage:{name}")
        selected_count = int(record.get("selected_count") or 0)
        if scan["scenario_selected_counts"].get(name, 0) != selected_count:
            failures.append(f"scenario_selected_count_mismatch:{name}")
    if not summary.get("clean_scenario_status"):
        failures.append("missing_clean_scenario_status")
    if repair.get("legacy_mixed_rows_removed_from_prop_budget", 0) <= 0:
        failures.append("legacy_mixed_removed_count_not_positive")
    if repair.get("off_kz_rows_removed_from_prop_budget", 0) <= 0:
        failures.append("off_kz_removed_count_not_positive")
    return {
        "ok": not failures,
        "failures": failures,
        "summary": rel(SUMMARY_PATH),
        "ledger": rel(LEDGER_PATH),
        "ledger_scan": scan,
        "corrected_prop_governance_input_rows": repair.get(
            "corrected_prop_governance_input_rows"
        ),
        "rows_removed_from_prop_budget_before_stage04": repair.get(
            "rows_removed_from_prop_budget_before_stage04"
        ),
    }


def mark_complete(result: dict[str, Any]) -> None:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    state["current_git_head"] = git_head()
    state["current_stage"] = "STAGE_04_EV_OPTIMIZED_PROP_CHALLENGE_GOVERNOR"
    state["active_invariant"] = "build_segmented_ev_optimized_prop_challenge_governor"
    state["first_incomplete_invariant"] = "STAGE_04_EV_OPTIMIZED_PROP_CHALLENGE_GOVERNOR"
    state["exact_next_action"] = (
        "Build segmented redacted_account account-attempt EV prop governor using Stage03 executable-stream inputs."
    )
    state.setdefault("stage_status_table", {})[
        "STAGE_03_EXECUTABLE_STREAM_AND_ROUTE_SEMANTICS_REPAIR"
    ] = "complete"
    state.setdefault("stage_status_table", {})[
        "STAGE_04_EV_OPTIMIZED_PROP_CHALLENGE_GOVERNOR"
    ] = "pending"
    state.setdefault("output_artifact_paths", {})[
        "stage03_verification_result"
    ] = rel(VERIFY_RESULT_PATH)
    state.setdefault("row_count_hash_coverage", {})[
        "stage03_executable_stream_semantics_sha256"
    ] = result["ledger_scan"]["sha256"]
    state.setdefault("verification_status", {}).update(
        {
            "stage03_verifier_ok": result["ok"],
            "stage03_ledger_rows": result["ledger_scan"]["row_count"],
            "stage03_legacy_mixed_bad_prop_eligible_rows": result["ledger_scan"][
                "legacy_mixed_bad_prop_eligible_rows"
            ],
            "stage03_off_kz_bad_prop_eligible_rows": result["ledger_scan"][
                "off_kz_bad_prop_eligible_rows"
            ],
        }
    )
    state.setdefault("tests_and_verifiers_run", []).append(
        {
            "command": "py -3 verify_vnext_production_candidate_repair_stage03_executable_stream_semantics_2026_05_25.py --mark-complete",
            "status": "passed" if result["ok"] else "failed",
            "result": {
                "ok": result["ok"],
                "failures": result["failures"],
                "first_incomplete_invariant": "STAGE_04_EV_OPTIMIZED_PROP_CHALLENGE_GOVERNOR",
            },
        }
    )
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-complete", action="store_true")
    args = parser.parse_args()
    result = verify()
    VERIFY_RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.mark_complete and result["ok"]:
        mark_complete(result)
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
