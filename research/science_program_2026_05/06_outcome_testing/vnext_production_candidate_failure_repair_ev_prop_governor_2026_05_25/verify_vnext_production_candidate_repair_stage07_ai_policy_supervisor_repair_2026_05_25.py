from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import yaml


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
STATE_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_SESSION_STATE_2026-05-25.json"
SUMMARY_PATH = (
    ROUTE_DIR
    / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE07_AI_POLICY_SUPERVISOR_REPAIR_SUMMARY_2026-05-25.json"
)
LEDGER_PATH = (
    ROUTE_DIR
    / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE07_AI_POLICY_SUPERVISOR_REPAIR_LEDGER_2026-05-25.jsonl"
)
VERIFY_RESULT_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE07_VERIFICATION_RESULT_2026-05-25.json"
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
    branch_counts: Counter[str] = Counter()
    no_paid_counts: Counter[str] = Counter()
    selected_stream_rows = 0
    ai_required_rows = 0
    prompt_packet_rows = 0
    prompt_packet_missing = 0
    stale_follow_without_ai_rows = 0
    future_input_bad_rows = 0
    paid_api_bad_rows = 0
    schema_bad_rows = 0
    supervisor_bad_rows = 0
    no_paid_selected_rows = 0
    with LEDGER_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            count += 1
            action = str(row.get("stage07_ai_policy_action") or "")
            action_counts[action] += 1
            branch_counts[str(row.get("stage07_policy_branch") or "")] += 1
            no_paid_counts[str(row.get("stage07_no_paid_call_status") or "")] += 1
            if row.get("stage06_selected_stream"):
                selected_stream_rows += 1
            if row.get("stage07_ai_call_required_for_production"):
                ai_required_rows += 1
                if not row.get("prompt_packet_sha256") or not row.get("cache_key_sha256"):
                    prompt_packet_missing += 1
            if row.get("prompt_packet_sha256"):
                prompt_packet_rows += 1
            if row.get("old_ai_policy_action") == "FOLLOW_WITHOUT_AI":
                stale_follow_without_ai_rows += 1
            if not row.get("decision_inputs_exclude_future_outcome_and_r"):
                future_input_bad_rows += 1
            if row.get("paid_api_or_vendor_call_made"):
                paid_api_bad_rows += 1
            schema = row.get("schema_contract") or {}
            if not schema.get("schema_validation_required") or not schema.get(
                "malformed_response_demotes_to_no_trade"
            ):
                schema_bad_rows += 1
            if row.get("old_ai_supervisor_action") != "HEALTHY":
                supervisor_bad_rows += 1
            if row.get("stage07_no_paid_call_selected"):
                no_paid_selected_rows += 1
    return {
        "row_count": count,
        "sha256": sha256_file(LEDGER_PATH),
        "action_counts": dict(action_counts),
        "branch_counts": dict(branch_counts),
        "no_paid_status_counts": dict(no_paid_counts),
        "selected_stream_rows": selected_stream_rows,
        "ai_required_rows": ai_required_rows,
        "prompt_packet_rows": prompt_packet_rows,
        "prompt_packet_missing_rows": prompt_packet_missing,
        "stale_follow_without_ai_rows": stale_follow_without_ai_rows,
        "future_input_bad_rows": future_input_bad_rows,
        "paid_api_bad_rows": paid_api_bad_rows,
        "schema_bad_rows": schema_bad_rows,
        "supervisor_nonhealthy_rows": supervisor_bad_rows,
        "no_paid_selected_rows": no_paid_selected_rows,
    }


def verify_config_gate() -> dict[str, Any]:
    cfg = yaml.safe_load((REPO_ROOT / "config" / "agent_config.yaml").read_text(encoding="utf-8"))
    runtime = cfg.get("gtos_vnext_runtime") or {}
    return {
        "ai_policy_enabled": runtime.get("ai_policy_enabled"),
        "ai_policy_apply_to_ai_call": runtime.get("ai_policy_apply_to_ai_call"),
        "apply_to_execution": runtime.get("apply_to_execution"),
        "ai_supervisor_enabled": (cfg.get("ai_supervisor") or {}).get("enabled"),
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
    config_gate = verify_config_gate()
    if scan["row_count"] != int(summary.get("ledger_rows") or 0):
        failures.append("ledger_row_count_mismatch")
    if scan["row_count"] != 253234:
        failures.append("stage07_did_not_preserve_full_ai_ledger_rows")
    if scan["selected_stream_rows"] != int(summary.get("stage07_selected_stream_rows") or 0):
        failures.append("selected_stream_row_count_mismatch")
    stage06_counts = summary.get("stage06_counts") or {}
    if scan["selected_stream_rows"] != int(stage06_counts.get("stage06_selected_stream") or 0):
        failures.append("selected_stream_not_equal_stage06")
    if scan["ai_required_rows"] != int(summary.get("stage07_ai_required_for_production_rows") or 0):
        failures.append("ai_required_row_count_mismatch")
    if scan["prompt_packet_rows"] != int(summary.get("stage07_prompt_packet_rows") or 0):
        failures.append("prompt_packet_row_count_mismatch")
    if scan["prompt_packet_missing_rows"] != 0:
        failures.append("prompt_packet_hash_missing")
    if scan["stale_follow_without_ai_rows"] != 0:
        failures.append("stale_follow_without_ai_string_present")
    if scan["future_input_bad_rows"] != 0:
        failures.append("future_input_bad_rows_nonzero")
    if scan["paid_api_bad_rows"] != 0:
        failures.append("paid_api_or_vendor_call_recorded")
    if scan["schema_bad_rows"] != 0:
        failures.append("schema_or_malformed_contract_bad_rows")
    if scan["supervisor_nonhealthy_rows"] != 0:
        failures.append("unexpected_nonhealthy_supervisor_rows")

    scenarios = summary.get("scenario_metrics") or {}
    production = scenarios.get("stage07_production_ai_policy_contract") or {}
    no_paid = scenarios.get("stage07_no_paid_call_diagnostic") or {}
    if int(production.get("selected_count") or 0) != scan["selected_stream_rows"]:
        failures.append("production_ai_policy_selected_count_not_stage06_stream")
    if int(no_paid.get("selected_count") or 0) != scan["no_paid_selected_rows"]:
        failures.append("no_paid_selected_count_mismatch")
    no_paid_diag = summary.get("no_paid_call_replay_diagnostic") or {}
    if no_paid_diag.get("production_selector") is not False:
        failures.append("no_paid_call_not_classified_diagnostic_only")
    if scan["no_paid_selected_rows"] != 0 and no_paid_diag.get("diagnostic_only"):
        failures.append("no_paid_diagnostic_selected_rows_nonzero")
    if scan["ai_required_rows"] <= 0:
        failures.append("no_ai_required_rows_found")
    if scan["prompt_packet_rows"] != scan["ai_required_rows"]:
        failures.append("prompt_packets_not_materialized_for_all_ai_required_rows")

    runtime = summary.get("runtime_surface_proof") or {}
    if runtime.get("broker_facing_activation_change"):
        failures.append("broker_facing_activation_change_true")
    if runtime.get("paid_api_or_vendor_calls_made") != 0:
        failures.append("summary_paid_api_calls_nonzero")
    if config_gate.get("ai_policy_apply_to_ai_call") is not False:
        failures.append("config_ai_policy_apply_to_ai_call_not_false")
    if config_gate.get("apply_to_execution") is not False:
        failures.append("config_apply_to_execution_not_false")

    return {
        "ok": not failures,
        "failures": failures,
        "summary": rel(SUMMARY_PATH),
        "ledger": rel(LEDGER_PATH),
        "ledger_scan": scan,
        "summary_sha256": sha256_file(SUMMARY_PATH),
        "config_gate": config_gate,
    }


def mark_complete(result: dict[str, Any]) -> None:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    state["current_git_head"] = git_head()
    state["dirty_tracked_and_untracked_path_summary"] = git_status_short()
    state["current_stage"] = "STAGE_08_REPAIRED_FORWARD_ONLY_REPLAY"
    state["active_invariant"] = "run_repaired_forward_only_replay_full_universe"
    state["first_incomplete_invariant"] = "STAGE_08_REPAIRED_FORWARD_ONLY_REPLAY"
    state["exact_next_action"] = (
        "Run the repaired full forward-only replay with Stage03-07 semantics, segmented prop governance, "
        "layer ablations, selected-only coverage, and completion-proof metrics."
    )
    state["completion_gate_status"] = "not_complete_stage08_first_incomplete"
    state.setdefault("stage_status_table", {})[
        "STAGE_07_AI_POLICY_AND_SUPERVISOR_REPAIR"
    ] = "complete"
    state.setdefault("stage_status_table", {})[
        "STAGE_08_REPAIRED_FORWARD_ONLY_REPLAY"
    ] = "pending"
    state.setdefault("output_artifact_paths", {}).update(
        {
            "stage07_ai_policy_supervisor_repair_ledger": rel(LEDGER_PATH),
            "stage07_ai_policy_supervisor_repair_summary": rel(SUMMARY_PATH),
            "stage07_verification_result": rel(VERIFY_RESULT_PATH),
        }
    )
    state.setdefault("row_count_hash_coverage", {}).update(
        {
            "stage07_ai_policy_supervisor_repair_rows": result["ledger_scan"]["row_count"],
            "stage07_ai_policy_supervisor_repair_ledger_sha256": result["ledger_scan"][
                "sha256"
            ],
            "stage07_ai_policy_supervisor_repair_summary_sha256": result[
                "summary_sha256"
            ],
            "stage07_ai_required_rows": result["ledger_scan"]["ai_required_rows"],
            "stage07_prompt_packet_rows": result["ledger_scan"]["prompt_packet_rows"],
        }
    )
    state.setdefault("verification_status", {}).update(
        {
            "stage07_verifier_ok": result["ok"],
            "stage07_ai_policy_repair_rows": result["ledger_scan"]["row_count"],
            "stage07_selected_stream_rows": result["ledger_scan"]["selected_stream_rows"],
            "stage07_ai_required_rows": result["ledger_scan"]["ai_required_rows"],
            "stage07_no_paid_selected_rows": result["ledger_scan"][
                "no_paid_selected_rows"
            ],
            "stage07_future_input_bad_rows": result["ledger_scan"][
                "future_input_bad_rows"
            ],
            "stage07_paid_api_bad_rows": result["ledger_scan"]["paid_api_bad_rows"],
        }
    )
    state.setdefault("repairs_applied", []).append(
        "stage07_ai_policy_no_paid_supervisor_diagnostic_contract_materialized"
    )
    state.setdefault("tests_and_verifiers_run", []).append(
        {
            "command": "py -3 verify_vnext_production_candidate_repair_stage07_ai_policy_supervisor_repair_2026_05_25.py --mark-complete",
            "status": "passed" if result["ok"] else "failed",
            "result": {
                "ok": result["ok"],
                "failures": result["failures"],
                "first_incomplete_invariant": "STAGE_08_REPAIRED_FORWARD_ONLY_REPLAY",
            },
        }
    )
    state.setdefault("active_question_and_repair_ledger", []).append(
        {
            "question": "Can no-paid AI replay be treated as a production selector after Stage07 repair?",
            "status": "closed_no_no_paid_is_diagnostic_only_under_funded_prop_selected_stream",
            "evidence_path": rel(VERIFY_RESULT_PATH),
            "ledger_rows": result["ledger_scan"]["row_count"],
            "ai_required_rows": result["ledger_scan"]["ai_required_rows"],
            "no_paid_selected_rows": result["ledger_scan"]["no_paid_selected_rows"],
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
