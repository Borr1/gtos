from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
STATE_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_SESSION_STATE_2026-05-25.json"
SUMMARY_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE06_LTF_ENTRY_NOFILL_REPAIR_SUMMARY_2026-05-25.json"
)
LEDGER_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE06_LTF_ENTRY_NOFILL_REPAIR_LEDGER_2026-05-25.jsonl"
)
VERIFY_RESULT_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE06_VERIFICATION_RESULT_2026-05-25.json"
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


def git_status_short() -> list[str]:
    try:
        output = subprocess.check_output(
            ["git", "status", "--short"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return ["GIT_STATUS_FAILED"]
    return [line for line in output.splitlines() if line.strip()]


def scan_ledger() -> dict[str, Any]:
    count = 0
    action_counts: Counter[str] = Counter()
    current_action_counts: Counter[str] = Counter()
    branch_counts: Counter[str] = Counter()
    future_input_bad = 0
    joined_path_rows = 0
    changed_rows = 0
    selected_after_rows = 0
    source_capture_rows = 0
    missing_path_rows = 0
    m15_ltf_disagreement_rows = 0
    with LEDGER_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            count += 1
            action = str(row.get("stage06_ltf_action") or "")
            current = str(row.get("current_ltf_action") or "")
            branch = str(row.get("stage06_repair_branch") or "")
            action_counts[action] += 1
            current_action_counts[current] += 1
            branch_counts[branch] += 1
            if not row.get("decision_inputs_exclude_future_r"):
                future_input_bad += 1
            if row.get("joined_path_row"):
                joined_path_rows += 1
            else:
                missing_path_rows += 1
            if row.get("execution_behavior_changed"):
                changed_rows += 1
            if row.get("selected_after_stage06_ltf"):
                selected_after_rows += 1
            if action == "SOURCE_CAPTURE_REQUIRED":
                source_capture_rows += 1
            if row.get("m15_vs_ltf_disagreement_joined"):
                m15_ltf_disagreement_rows += 1
    return {
        "row_count": count,
        "sha256": sha256_file(LEDGER_PATH),
        "action_counts": dict(action_counts),
        "current_action_counts": dict(current_action_counts),
        "branch_counts": dict(branch_counts),
        "future_input_bad_rows": future_input_bad,
        "joined_path_rows": joined_path_rows,
        "missing_path_rows": missing_path_rows,
        "execution_behavior_changed_rows": changed_rows,
        "selected_after_stage06_ltf_rows": selected_after_rows,
        "source_capture_required_rows": source_capture_rows,
        "m15_ltf_disagreement_rows": m15_ltf_disagreement_rows,
    }


def verify() -> dict[str, Any]:
    failures: list[str] = []
    for path, label in ((SUMMARY_PATH, "summary"), (LEDGER_PATH, "ledger")):
        if not path.exists():
            failures.append(f"missing_{label}")
    if failures:
        return {"ok": False, "failures": failures}

    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    scan = scan_ledger()
    if scan["row_count"] != int(summary.get("ledger_rows") or 0):
        failures.append("ledger_row_count_mismatch")
    selected_counts = summary.get("selected_stream_counts") or {}
    if scan["row_count"] != int(selected_counts.get("stage06_selected_stream_ids") or 0):
        failures.append("selected_stream_count_mismatch")
    if scan["future_input_bad_rows"] != 0:
        failures.append("future_input_bad_rows_nonzero")
    if scan["joined_path_rows"] <= 0:
        failures.append("no_path_rows_joined")
    if scan["execution_behavior_changed_rows"] <= 0:
        failures.append("no_ltf_execution_behavior_changed_rows")
    if scan["m15_ltf_disagreement_rows"] <= 0:
        failures.append("no_selected_stream_m15_ltf_disagreements_joined")
    if scan["current_action_counts"] != summary.get("current_ltf_action_counts"):
        failures.append("current_ltf_action_counts_mismatch")
    if scan["action_counts"] != summary.get("stage06_ltf_action_counts"):
        failures.append("stage06_ltf_action_counts_mismatch")
    if set(scan["current_action_counts"]) != {"PLACE_LIMIT"}:
        failures.append("current_ltf_replay_not_all_place_limit")

    path_join = summary.get("path_join") or {}
    if int(path_join.get("path_rows_joined") or 0) != scan["joined_path_rows"]:
        failures.append("path_join_count_mismatch")
    disagreement_join = summary.get("m15_vs_ltf_join") or {}
    if int(disagreement_join.get("m15_vs_ltf_selected_stream_rows_joined") or 0) != scan[
        "m15_ltf_disagreement_rows"
    ]:
        failures.append("m15_ltf_join_count_mismatch")

    scenarios = summary.get("scenario_metrics") or {}
    current = scenarios.get("stage05_stream_current_ltf_place_limit") or {}
    repaired = scenarios.get("stage06_ltf_repaired_execution_policy") or {}
    if int(current.get("selected_count") or 0) != scan["row_count"]:
        failures.append("current_scenario_selected_count_mismatch")
    if int(repaired.get("selected_count") or 0) != scan["selected_after_stage06_ltf_rows"]:
        failures.append("repaired_scenario_selected_count_mismatch")
    if int(repaired.get("selected_count") or 0) > int(current.get("selected_count") or 0):
        failures.append("repaired_selected_count_exceeds_current")

    runtime_surface = summary.get("runtime_surface_proof") or {}
    gate = runtime_surface.get("config_activation_gate") or {}
    if gate.get("broker_facing_activation_change"):
        failures.append("broker_facing_activation_change_true")
    if gate.get("ltf_path_execution_apply_to_execution") is not False:
        failures.append("ltf_apply_gate_not_false")
    if not runtime_surface.get("orchestrator_ltf_pending_monitor"):
        failures.append("runtime_pending_monitor_proof_missing")

    return {
        "ok": not failures,
        "failures": failures,
        "summary": rel(SUMMARY_PATH),
        "ledger": rel(LEDGER_PATH),
        "ledger_scan": scan,
        "summary_sha256": sha256_file(SUMMARY_PATH),
    }


def mark_complete(result: dict[str, Any]) -> None:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    state["current_git_head"] = git_head()
    state["dirty_tracked_and_untracked_path_summary"] = git_status_short()
    state["current_stage"] = "STAGE_07_AI_POLICY_AND_SUPERVISOR_REPAIR"
    state["active_invariant"] = "repair_ai_policy_no_paid_call_and_supervisor_behavior"
    state["first_incomplete_invariant"] = "STAGE_07_AI_POLICY_AND_SUPERVISOR_REPAIR"
    state["exact_next_action"] = (
        "Repair AI/no-paid-call/supervisor behavior so diagnostic zero-output paths cannot be treated as production selectors."
    )
    state["completion_gate_status"] = "not_complete_stage07_first_incomplete"
    state.setdefault("stage_status_table", {})[
        "STAGE_06_LTF_ENTRY_NOFILL_EXECUTION_REPAIR"
    ] = "complete"
    state.setdefault("stage_status_table", {})[
        "STAGE_07_AI_POLICY_AND_SUPERVISOR_REPAIR"
    ] = "pending"
    state.setdefault("output_artifact_paths", {})[
        "stage06_verification_result"
    ] = rel(VERIFY_RESULT_PATH)
    state.setdefault("row_count_hash_coverage", {}).update(
        {
            "stage06_ltf_entry_nofill_repair_rows": result["ledger_scan"]["row_count"],
            "stage06_ltf_entry_nofill_repair_ledger_sha256": result["ledger_scan"][
                "sha256"
            ],
            "stage06_ltf_entry_nofill_repair_summary_sha256": result["summary_sha256"],
        }
    )
    state.setdefault("verification_status", {}).update(
        {
            "stage06_verifier_ok": result["ok"],
            "stage06_ltf_repair_rows": result["ledger_scan"]["row_count"],
            "stage06_ltf_execution_behavior_changed_rows": result["ledger_scan"][
                "execution_behavior_changed_rows"
            ],
            "stage06_ltf_source_capture_required_rows": result["ledger_scan"][
                "source_capture_required_rows"
            ],
            "stage06_ltf_future_input_bad_rows": result["ledger_scan"][
                "future_input_bad_rows"
            ],
        }
    )
    state.setdefault("tests_and_verifiers_run", []).append(
        {
            "command": "py -3 verify_vnext_production_candidate_repair_stage06_ltf_entry_nofill_repair_2026_05_25.py --mark-complete",
            "status": "passed" if result["ok"] else "failed",
            "result": {
                "ok": result["ok"],
                "failures": result["failures"],
                "first_incomplete_invariant": "STAGE_07_AI_POLICY_AND_SUPERVISOR_REPAIR",
            },
        }
    )
    state.setdefault("active_question_and_repair_ledger", []).append(
        {
            "question": "Did Stage06 prove LTF/M1 behavior changes on the selected stream without live activation?",
            "status": "closed_stage06_verified_ltf_execution_repair",
            "evidence_path": rel(VERIFY_RESULT_PATH),
            "ledger_rows": result["ledger_scan"]["row_count"],
            "execution_behavior_changed_rows": result["ledger_scan"][
                "execution_behavior_changed_rows"
            ],
        }
    )
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-complete", action="store_true")
    args = parser.parse_args()
    result = verify()
    VERIFY_RESULT_PATH.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if args.mark_complete and result["ok"]:
        mark_complete(result)
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
