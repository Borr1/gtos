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
SUMMARY_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_PROP_POLICY_COMPARISON_SUMMARY_2026-05-25.json"
ATTEMPT_LEDGER_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_PROP_ATTEMPT_LEDGER_2026-05-25.jsonl"
DECISION_LEDGER_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE04_PROP_GOVERNOR_DECISION_LEDGER_2026-05-25.jsonl"
)
VERIFY_RESULT_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE04_VERIFICATION_RESULT_2026-05-25.json"


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


def scan_decision_ledger() -> dict[str, Any]:
    count = 0
    future_input_bad = 0
    scenario_policy_counts: dict[str, int] = {}
    action_counts: dict[str, int] = {}
    selected_count = 0
    with DECISION_LEDGER_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            count += 1
            if not row.get("decision_inputs_no_future_r"):
                future_input_bad += 1
            key = f"{row.get('scenario')}|{row.get('policy')}"
            scenario_policy_counts[key] = scenario_policy_counts.get(key, 0) + 1
            action = str(row.get("action") or "")
            action_counts[action] = action_counts.get(action, 0) + 1
            if row.get("selected"):
                selected_count += 1
    return {
        "row_count": count,
        "sha256": sha256_file(DECISION_LEDGER_PATH),
        "future_input_bad_rows": future_input_bad,
        "scenario_policy_counts": scenario_policy_counts,
        "action_counts": action_counts,
        "selected_count": selected_count,
    }


def scan_attempt_ledger() -> dict[str, Any]:
    count = 0
    non_segmented = 0
    terminal_status_counts: dict[str, int] = {}
    with ATTEMPT_LEDGER_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            count += 1
            if not row.get("segmented_account_attempt"):
                non_segmented += 1
            status = str(row.get("terminal_status") or "")
            terminal_status_counts[status] = terminal_status_counts.get(status, 0) + 1
    return {
        "row_count": count,
        "sha256": sha256_file(ATTEMPT_LEDGER_PATH),
        "non_segmented_rows": non_segmented,
        "terminal_status_counts": terminal_status_counts,
    }


def verify() -> dict[str, Any]:
    failures: list[str] = []
    for path, label in (
        (SUMMARY_PATH, "summary"),
        (ATTEMPT_LEDGER_PATH, "attempt_ledger"),
        (DECISION_LEDGER_PATH, "decision_ledger"),
    ):
        if not path.exists():
            failures.append(f"missing_{label}")
    if failures:
        return {"ok": False, "failures": failures}
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    decision_scan = scan_decision_ledger()
    attempt_scan = scan_attempt_ledger()
    model = summary.get("segmented_attempt_model") or {}
    if not model.get("segmented_account_attempts_not_continuous_2022_2026"):
        failures.append("segmented_attempt_model_not_marked_true")
    if not model.get("decision_inputs_exclude_future_r"):
        failures.append("decision_input_future_r_guard_missing")
    if decision_scan["future_input_bad_rows"] != 0:
        failures.append("decision_rows_with_future_input_flag_bad")
    if attempt_scan["non_segmented_rows"] != 0:
        failures.append("attempt_rows_not_segmented")
    required_policies = set(summary.get("policies_compared") or [])
    expected_policies = {
        "ALLOW_FULL_RISK_SEGMENTED",
        "REDUCE_RISK_TO_BUDGET",
        "MICRO_RISK_NEAR_BUDGET",
        "HIGH_QUALITY_ONLY",
        "DEFER_UNTIL_RESET",
        "ACCOUNT_ABANDON_OR_RESTART",
        "BLOCK_ALL_NEAR_LIMIT",
    }
    if required_policies != expected_policies:
        failures.append("policy_set_mismatch")
    expected_decision_rows = 0
    for scenario, data in (summary.get("scenarios") or {}).items():
        input_rows = int(data.get("input_rows") or 0)
        expected_decision_rows += input_rows * len(expected_policies)
        metrics = data.get("policy_metrics") or {}
        if set(metrics) != expected_policies:
            failures.append(f"scenario_policy_metrics_missing:{scenario}")
        if input_rows <= 0:
            failures.append(f"scenario_input_rows_zero:{scenario}")
        if not data.get("best_policy_reference_fee_599_payout_8000"):
            failures.append(f"missing_best_policy:{scenario}")
        for policy, record in metrics.items():
            if "payout_sensitivity_grid" not in record:
                failures.append(f"missing_payout_grid:{scenario}|{policy}")
            if "selected_only_coverage" not in record:
                failures.append(f"missing_selected_coverage:{scenario}|{policy}")
            if "opportunity_cost_if_blocked_rows_taken_r" not in record:
                failures.append(f"missing_opportunity_cost:{scenario}|{policy}")
            if "avg_time_to_terminal_days" not in record:
                failures.append(f"missing_time_to_terminal:{scenario}|{policy}")
            if "reference_ev_per_terminal_day_usd_fee599_payout8000" not in record:
                failures.append(f"missing_time_adjusted_ev:{scenario}|{policy}")
            key = f"{scenario}|{policy}"
            if decision_scan["scenario_policy_counts"].get(key) != input_rows:
                failures.append(f"decision_row_count_mismatch:{key}")
    if decision_scan["row_count"] != expected_decision_rows:
        failures.append("total_decision_row_count_mismatch")
    if attempt_scan["row_count"] <= 0:
        failures.append("attempt_ledger_empty")
    return {
        "ok": not failures,
        "failures": failures,
        "summary": rel(SUMMARY_PATH),
        "decision_ledger": rel(DECISION_LEDGER_PATH),
        "attempt_ledger": rel(ATTEMPT_LEDGER_PATH),
        "decision_scan": decision_scan,
        "attempt_scan": attempt_scan,
    }


def mark_complete(result: dict[str, Any]) -> None:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    state["current_git_head"] = git_head()
    state["current_stage"] = "STAGE_05_VNEXT_AVOID_AND_PRE_AI_REPAIR"
    state["active_invariant"] = "repair_vnext_avoid_and_pre_ai_pressure_with_selected_only_ev"
    state["first_incomplete_invariant"] = "STAGE_05_VNEXT_AVOID_AND_PRE_AI_REPAIR"
    state["exact_next_action"] = (
        "Use Stage01 AVOID EV and Stage04 selected-stream evidence to demote harmful broad AVOID/pre-AI blocks and preserve only useful bounded avoid families."
    )
    state["completion_gate_status"] = "not_complete_stage05_first_incomplete"
    state.setdefault("stage_status_table", {})[
        "STAGE_04_EV_OPTIMIZED_PROP_CHALLENGE_GOVERNOR"
    ] = "complete"
    state.setdefault("stage_status_table", {})[
        "STAGE_05_VNEXT_AVOID_AND_PRE_AI_REPAIR"
    ] = "pending"
    state.setdefault("output_artifact_paths", {})[
        "stage04_verification_result"
    ] = rel(VERIFY_RESULT_PATH)
    state.setdefault("verification_status", {}).update(
        {
            "stage04_verifier_ok": result["ok"],
            "stage04_decision_ledger_rows": result["decision_scan"]["row_count"],
            "stage04_attempt_ledger_rows": result["attempt_scan"]["row_count"],
            "stage04_future_input_bad_rows": result["decision_scan"][
                "future_input_bad_rows"
            ],
        }
    )
    state.setdefault("row_count_hash_coverage", {}).update(
        {
            "stage04_prop_attempt_ledger_rows": result["attempt_scan"]["row_count"],
            "stage04_prop_attempt_ledger_sha256": result["attempt_scan"]["sha256"],
            "stage04_prop_decision_ledger_rows": result["decision_scan"]["row_count"],
            "stage04_prop_decision_ledger_sha256": result["decision_scan"]["sha256"],
        }
    )
    state.setdefault("tests_and_verifiers_run", []).append(
        {
            "command": "py -3 verify_vnext_production_candidate_repair_stage04_ev_prop_governor_2026_05_25.py --mark-complete",
            "status": "passed" if result["ok"] else "failed",
            "result": {
                "ok": result["ok"],
                "failures": result["failures"],
                "first_incomplete_invariant": "STAGE_05_VNEXT_AVOID_AND_PRE_AI_REPAIR",
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
