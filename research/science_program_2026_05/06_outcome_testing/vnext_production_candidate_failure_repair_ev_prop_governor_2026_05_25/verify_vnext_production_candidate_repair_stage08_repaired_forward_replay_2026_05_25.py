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
REPLAY_SUMMARY = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_REPLAY_METRICS_SUMMARY_2026-05-25.json"
ABLATION_SUMMARY = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_LAYER_ABLATION_SUMMARY_2026-05-25.json"
DECISION_LEDGER = (
    ROUTE_DIR
    / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE08_REPAIRED_REPLAY_DECISION_LEDGER_2026-05-25.jsonl"
)
ATTEMPT_LEDGER = (
    ROUTE_DIR
    / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE08_REPAIRED_PROP_ATTEMPT_LEDGER_2026-05-25.jsonl"
)
VERIFY_RESULT = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE08_VERIFICATION_RESULT_2026-05-25.json"


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


def scan_decision_ledger() -> dict[str, Any]:
    count = 0
    policy_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    selected_counts: Counter[str] = Counter()
    future_bad = 0
    paid_bad = 0
    off_kz_selected = 0
    with DECISION_LEDGER.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            count += 1
            policy = str(row.get("policy") or "")
            policy_counts[policy] += 1
            action_counts[str(row.get("action") or "")] += 1
            if row.get("selected"):
                selected_counts[policy] += 1
                if row.get("session") == "off_kz":
                    off_kz_selected += 1
            if not row.get("decision_inputs_no_future_r"):
                future_bad += 1
            if row.get("paid_api_or_vendor_call_made"):
                paid_bad += 1
    return {
        "row_count": count,
        "sha256": sha256_file(DECISION_LEDGER),
        "policy_counts": dict(policy_counts),
        "action_counts": dict(action_counts),
        "selected_counts_by_policy": dict(selected_counts),
        "future_input_bad_rows": future_bad,
        "paid_api_bad_rows": paid_bad,
        "off_kz_selected_rows": off_kz_selected,
    }


def scan_attempt_ledger() -> dict[str, Any]:
    count = 0
    terminal_counts: Counter[str] = Counter()
    nonsegmented = 0
    with ATTEMPT_LEDGER.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            count += 1
            terminal_counts[str(row.get("terminal_status") or "")] += 1
            if not row.get("segmented_account_attempt"):
                nonsegmented += 1
    return {
        "row_count": count,
        "sha256": sha256_file(ATTEMPT_LEDGER),
        "terminal_counts": dict(terminal_counts),
        "nonsegmented_attempt_rows": nonsegmented,
    }


def verify() -> dict[str, Any]:
    failures: list[str] = []
    for path, label in (
        (REPLAY_SUMMARY, "replay_summary"),
        (ABLATION_SUMMARY, "ablation_summary"),
        (DECISION_LEDGER, "decision_ledger"),
        (ATTEMPT_LEDGER, "attempt_ledger"),
    ):
        if not path.exists():
            failures.append(f"missing_{label}")
    if failures:
        return {"ok": False, "failures": failures}

    replay = json.loads(REPLAY_SUMMARY.read_text(encoding="utf-8"))
    ablation = json.loads(ABLATION_SUMMARY.read_text(encoding="utf-8"))
    decision_scan = scan_decision_ledger()
    attempt_scan = scan_attempt_ledger()
    executable_rows = int(replay.get("executable_stream_rows") or 0)
    policies = replay.get("policies_compared") or []
    if replay.get("candidate_universe_rows") != 253234:
        failures.append("candidate_universe_row_count_mismatch")
    if executable_rows != 79320:
        failures.append("executable_stream_row_count_mismatch")
    if decision_scan["row_count"] != executable_rows * len(policies):
        failures.append("decision_ledger_policy_row_count_mismatch")
    if decision_scan["future_input_bad_rows"] != 0:
        failures.append("decision_ledger_future_input_bad")
    if decision_scan["paid_api_bad_rows"] != 0 or replay.get("paid_api_or_vendor_calls_made") != 0:
        failures.append("paid_api_or_vendor_call_recorded")
    if attempt_scan["row_count"] <= 0:
        failures.append("attempt_ledger_empty")
    if attempt_scan["nonsegmented_attempt_rows"] != 0:
        failures.append("nonsegmented_attempt_rows_present")
    if decision_scan["off_kz_selected_rows"] != 0:
        failures.append("off_kz_rows_selected")
    required = replay.get("required_metric_coverage") or {}
    missing_required = [key for key, value in required.items() if value is not True]
    if missing_required:
        failures.append("required_metric_coverage_false:" + ",".join(sorted(missing_required)))
    best = replay.get("best_policy_reference_fee_599_payout_8000") or {}
    if not best.get("policy"):
        failures.append("missing_best_policy")
    best_record = (replay.get("policy_metrics") or {}).get(best.get("policy"), {})
    if not best_record:
        failures.append("missing_best_policy_record")
    elif int(best_record.get("input_rows") or 0) != executable_rows:
        failures.append("best_policy_input_rows_mismatch")
    if replay.get("no_paid_call_replay_diagnostic_only") is not True:
        failures.append("no_paid_call_not_diagnostic_only")
    if replay.get("broker_facing_activation_change"):
        failures.append("broker_facing_activation_change_true")
    if not ablation.get("stage08_replay_supersedes_stage04_prop_on_stage03_only_stream"):
        failures.append("ablation_does_not_mark_stage08_prop_supersession")
    if len(ablation.get("layers") or []) < 6:
        failures.append("ablation_layers_incomplete")
    return {
        "ok": not failures,
        "failures": failures,
        "replay_summary": rel(REPLAY_SUMMARY),
        "ablation_summary": rel(ABLATION_SUMMARY),
        "decision_ledger": rel(DECISION_LEDGER),
        "attempt_ledger": rel(ATTEMPT_LEDGER),
        "decision_scan": decision_scan,
        "attempt_scan": attempt_scan,
        "replay_summary_sha256": sha256_file(REPLAY_SUMMARY),
        "ablation_summary_sha256": sha256_file(ABLATION_SUMMARY),
    }


def mark_complete(result: dict[str, Any]) -> None:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    state["current_git_head"] = git_head()
    state["dirty_tracked_and_untracked_path_summary"] = git_status_short()
    state["current_stage"] = "STAGE_09_PRODUCTION_CANDIDATE_DECISION_DOSSIER"
    state["active_invariant"] = "write_truthful_production_candidate_decision_dossier"
    state["first_incomplete_invariant"] = "STAGE_09_PRODUCTION_CANDIDATE_DECISION_DOSSIER"
    state["exact_next_action"] = (
        "Write the truthful Stage09 decision dossier from the repaired Stage08 replay, ending in viable, failed, or redesign-required state."
    )
    state["completion_gate_status"] = "not_complete_stage09_first_incomplete"
    state.setdefault("stage_status_table", {})["STAGE_08_REPAIRED_FORWARD_ONLY_REPLAY"] = "complete"
    state.setdefault("stage_status_table", {})[
        "STAGE_09_PRODUCTION_CANDIDATE_DECISION_DOSSIER"
    ] = "pending"
    state.setdefault("output_artifact_paths", {}).update(
        {
            "replay_metrics_summary": rel(REPLAY_SUMMARY),
            "layer_ablation_summary": rel(ABLATION_SUMMARY),
            "stage08_repaired_replay_decision_ledger": rel(DECISION_LEDGER),
            "stage08_repaired_prop_attempt_ledger": rel(ATTEMPT_LEDGER),
            "stage08_verification_result": rel(VERIFY_RESULT),
        }
    )
    state.setdefault("row_count_hash_coverage", {}).update(
        {
            "stage08_repaired_replay_decision_rows": result["decision_scan"]["row_count"],
            "stage08_repaired_replay_decision_ledger_sha256": result["decision_scan"][
                "sha256"
            ],
            "stage08_repaired_prop_attempt_rows": result["attempt_scan"]["row_count"],
            "stage08_repaired_prop_attempt_ledger_sha256": result["attempt_scan"][
                "sha256"
            ],
            "stage08_replay_summary_sha256": result["replay_summary_sha256"],
            "stage08_ablation_summary_sha256": result["ablation_summary_sha256"],
        }
    )
    state.setdefault("verification_status", {}).update(
        {
            "stage08_verifier_ok": result["ok"],
            "stage08_repaired_replay_decision_rows": result["decision_scan"]["row_count"],
            "stage08_repaired_prop_attempt_rows": result["attempt_scan"]["row_count"],
            "stage08_future_input_bad_rows": result["decision_scan"][
                "future_input_bad_rows"
            ],
            "stage08_paid_api_bad_rows": result["decision_scan"]["paid_api_bad_rows"],
            "stage08_off_kz_selected_rows": result["decision_scan"]["off_kz_selected_rows"],
        }
    )
    state.setdefault("repairs_applied", []).append(
        "stage08_full_repaired_forward_replay_and_layer_ablations_materialized"
    )
    state.setdefault("tests_and_verifiers_run", []).append(
        {
            "command": "py -3 verify_vnext_production_candidate_repair_stage08_repaired_forward_replay_2026_05_25.py --mark-complete",
            "status": "passed" if result["ok"] else "failed",
            "result": {
                "ok": result["ok"],
                "failures": result["failures"],
                "first_incomplete_invariant": "STAGE_09_PRODUCTION_CANDIDATE_DECISION_DOSSIER",
            },
        }
    )
    state.setdefault("active_question_and_repair_ledger", []).append(
        {
            "question": "Did the repaired Stage08 replay run over the full universe and repaired selected stream?",
            "status": "closed_stage08_verified_full_repaired_replay_materialized",
            "evidence_path": rel(VERIFY_RESULT),
            "decision_rows": result["decision_scan"]["row_count"],
            "attempt_rows": result["attempt_scan"]["row_count"],
        }
    )
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-complete", action="store_true")
    args = parser.parse_args()
    result = verify()
    VERIFY_RESULT.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if args.mark_complete and result["ok"]:
        mark_complete(result)
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
