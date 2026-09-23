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
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE05_AVOID_PRE_AI_REPAIR_SUMMARY_2026-05-25.json"
)
POLICY_LEDGER_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE05_AVOID_PRE_AI_REPAIR_LEDGER_2026-05-25.jsonl"
)
VERIFY_RESULT_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE05_VERIFICATION_RESULT_2026-05-25.json"
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


def scan_policy_ledger() -> dict[str, Any]:
    count = 0
    decision_counts: Counter[str] = Counter()
    classification_counts: Counter[str] = Counter()
    hard_block_bad_rows = 0
    missing_attribution_hard_block_rows = 0
    recovered_rows = 0
    recovered_r = 0.0
    stage03_executable_policy_rows = 0
    with POLICY_LEDGER_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            count += 1
            decision = str(row.get("implementation_decision") or "")
            classification = str(row.get("evidence_classification") or "")
            decision_counts[decision] += 1
            classification_counts[classification] += 1
            hard_block = bool(row.get("hard_block_allowed_after_repair"))
            missing_attr = bool(row.get("missing_attribution_demoted"))
            if hard_block and decision != "PRESERVE_BOUNDED_AVOID_FILTER":
                hard_block_bad_rows += 1
            if row.get("avoid_source_component") == "__NULL__" and hard_block:
                missing_attribution_hard_block_rows += 1
            if missing_attr and decision != "DEMOTE_TO_CONTEXT_NOT_EXECUTION_BLOCK":
                missing_attribution_hard_block_rows += 1
            if row.get("recovered_into_stage05_no_prop_stream"):
                recovered_rows += 1
                try:
                    recovered_r += float(row.get("simulated_r_if_taken") or 0.0)
                except (TypeError, ValueError):
                    pass
            if row.get("stage03_vnext_executable_stream_without_prop_governance"):
                stage03_executable_policy_rows += 1
    return {
        "row_count": count,
        "sha256": sha256_file(POLICY_LEDGER_PATH),
        "decision_counts": dict(decision_counts),
        "classification_counts": dict(classification_counts),
        "hard_block_bad_rows": hard_block_bad_rows,
        "missing_attribution_hard_block_rows": missing_attribution_hard_block_rows,
        "recovered_rows": recovered_rows,
        "recovered_r": round(recovered_r, 12),
        "stage03_executable_policy_rows": stage03_executable_policy_rows,
    }


def verify() -> dict[str, Any]:
    failures: list[str] = []
    for path, label in ((SUMMARY_PATH, "summary"), (POLICY_LEDGER_PATH, "policy_ledger")):
        if not path.exists():
            failures.append(f"missing_{label}")
    if failures:
        return {"ok": False, "failures": failures}

    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    scan = scan_policy_ledger()

    policy_rows = int(summary.get("avoid_pre_ai_policy_rows") or 0)
    input_rows = int(summary.get("avoid_pre_ai_input_rows") or 0)
    if policy_rows <= 0:
        failures.append("policy_rows_zero")
    if scan["row_count"] != policy_rows:
        failures.append("policy_ledger_row_count_mismatch")
    if policy_rows != input_rows:
        failures.append("policy_rows_input_rows_mismatch")
    if summary.get("missing_stage03_membership_rows") != 0:
        failures.append("missing_stage03_membership_rows_nonzero")

    stage03_counts = summary.get("stage03_membership_counts") or {}
    if stage03_counts.get("rows") != stage03_counts.get("unique_candidate_ids"):
        failures.append("stage03_membership_not_one_to_one")
    if stage03_counts.get("duplicate_candidate_ids") != 0:
        failures.append("stage03_duplicate_candidate_ids")

    stage04 = summary.get("stage04_selected_stream_context") or {}
    if not stage04.get("stage04_context_available"):
        failures.append("stage04_selected_stream_context_missing")
    if not stage04.get("vnext_best_policy_reference_fee_599_payout_8000"):
        failures.append("stage04_best_policy_missing")
    if int(stage04.get("selected_candidate_ids_for_best_policy") or 0) <= 0:
        failures.append("stage04_selected_candidate_context_empty")

    group_records = summary.get("group_decisions") or []
    if not group_records:
        failures.append("group_decisions_empty")
    summary_decision_counts = summary.get("decision_counts") or {}
    if scan["decision_counts"] != summary_decision_counts:
        failures.append("decision_counts_mismatch")
    required_dimensions = {
        "symbols",
        "sessions",
        "sides",
        "frameworks",
        "months",
        "source_modes",
        "route_families",
    }
    preserved_count = 0
    demoted_count = 0
    for group in group_records:
        decision = group.get("implementation_decision")
        component = group.get("source_component")
        r_sum = float(group.get("r_sum_if_taken") or 0.0)
        winners = int(group.get("winners_blocked") or 0)
        losers = int(group.get("losers_avoided") or 0)
        r_count = int(group.get("r_count") or 0)
        partition_ev = group.get("partition_ev") or {}
        if set(partition_ev) != required_dimensions:
            failures.append(f"partition_dimensions_missing:{component}")
        if decision == "PRESERVE_BOUNDED_AVOID_FILTER":
            preserved_count += 1
            if not (r_count >= 20 and r_sum < 0 and losers > winners):
                failures.append(f"preserved_group_not_net_useful:{component}")
        if decision == "DEMOTE_TO_CONTEXT_NOT_EXECUTION_BLOCK":
            demoted_count += 1
        if component == "__NULL__" and decision != "DEMOTE_TO_CONTEXT_NOT_EXECUTION_BLOCK":
            failures.append("null_component_not_demoted")
    if preserved_count <= 0:
        failures.append("no_useful_bounded_avoid_filter_preserved")
    if demoted_count <= 0:
        failures.append("no_harmful_or_context_avoid_filter_demoted")
    if scan["hard_block_bad_rows"] != 0:
        failures.append("hard_block_bad_rows_nonzero")
    if scan["missing_attribution_hard_block_rows"] != 0:
        failures.append("missing_attribution_hard_block_rows_nonzero")

    scenarios = summary.get("scenario_metrics") or {}
    baseline = scenarios.get("stage03_vnext_executable_without_prop_baseline") or {}
    repaired = scenarios.get("stage05_avoid_pre_ai_repaired_without_prop") or {}
    baseline_selected = int(baseline.get("selected_count") or 0)
    repaired_selected = int(repaired.get("selected_count") or 0)
    if baseline_selected <= 0:
        failures.append("baseline_selected_count_zero")
    if repaired_selected < baseline_selected:
        failures.append("repaired_selected_count_less_than_baseline")
    recovered_delta = repaired_selected - baseline_selected
    if recovered_delta != scan["recovered_rows"]:
        failures.append("recovered_row_delta_mismatch")
    repaired_recovered_r = round(float(repaired.get("recovered_r") or 0.0), 12)
    if abs(repaired_recovered_r - scan["recovered_r"]) > 0.000001:
        failures.append("recovered_r_mismatch")

    runtime_policy = summary.get("runtime_policy_recommendation") or {}
    if runtime_policy.get("broker_facing_activation_change"):
        failures.append("broker_facing_activation_change_true")
    if not runtime_policy.get("owner_approval_required_before_runtime_config_change"):
        failures.append("owner_approval_flag_missing")

    return {
        "ok": not failures,
        "failures": failures,
        "summary": rel(SUMMARY_PATH),
        "policy_ledger": rel(POLICY_LEDGER_PATH),
        "policy_scan": scan,
        "summary_sha256": sha256_file(SUMMARY_PATH),
    }


def mark_complete(result: dict[str, Any]) -> None:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    state["current_git_head"] = git_head()
    state["dirty_tracked_and_untracked_path_summary"] = git_status_short()
    state["current_stage"] = "STAGE_06_LTF_ENTRY_NOFILL_EXECUTION_REPAIR"
    state["active_invariant"] = "repair_ltf_entry_nofill_execution_behavior"
    state["first_incomplete_invariant"] = "STAGE_06_LTF_ENTRY_NOFILL_EXECUTION_REPAIR"
    state["exact_next_action"] = (
        "Repair LTF/M1/M5/tick/Sierra path intelligence so selected-stream entry and no-fill behavior can change execution, not only scoring."
    )
    state["completion_gate_status"] = "not_complete_stage06_first_incomplete"
    state.setdefault("stage_status_table", {})[
        "STAGE_05_VNEXT_AVOID_AND_PRE_AI_REPAIR"
    ] = "complete"
    state.setdefault("stage_status_table", {})[
        "STAGE_06_LTF_ENTRY_NOFILL_EXECUTION_REPAIR"
    ] = "pending"
    state.setdefault("output_artifact_paths", {})[
        "stage05_verification_result"
    ] = rel(VERIFY_RESULT_PATH)
    state.setdefault("row_count_hash_coverage", {}).update(
        {
            "stage05_avoid_pre_ai_policy_rows": result["policy_scan"]["row_count"],
            "stage05_avoid_pre_ai_repair_ledger_sha256": result["policy_scan"]["sha256"],
            "stage05_avoid_pre_ai_repair_summary_sha256": result["summary_sha256"],
        }
    )
    state.setdefault("verification_status", {}).update(
        {
            "stage05_verifier_ok": result["ok"],
            "stage05_policy_rows": result["policy_scan"]["row_count"],
            "stage05_recovered_rows": result["policy_scan"]["recovered_rows"],
            "stage05_hard_block_bad_rows": result["policy_scan"]["hard_block_bad_rows"],
            "stage05_missing_attribution_hard_block_rows": result["policy_scan"][
                "missing_attribution_hard_block_rows"
            ],
        }
    )
    state.setdefault("tests_and_verifiers_run", []).append(
        {
            "command": "py -3 verify_vnext_production_candidate_repair_stage05_avoid_pre_ai_repair_2026_05_25.py --mark-complete",
            "status": "passed" if result["ok"] else "failed",
            "result": {
                "ok": result["ok"],
                "failures": result["failures"],
                "first_incomplete_invariant": "STAGE_06_LTF_ENTRY_NOFILL_EXECUTION_REPAIR",
            },
        }
    )
    state.setdefault("active_question_and_repair_ledger", []).append(
        {
            "question": "Can broad vNext AVOID/pre-AI pressure remain a hard execution block?",
            "status": "closed_stage05_verified_bounded_or_demoted",
            "evidence_path": rel(VERIFY_RESULT_PATH),
            "policy_rows": result["policy_scan"]["row_count"],
            "recovered_rows": result["policy_scan"]["recovered_rows"],
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
