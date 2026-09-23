from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
STATE_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_SESSION_STATE_2026-05-25.json"
SUMMARY_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE02_ACCEPTANCE_GATE_REPAIR_SUMMARY_2026-05-25.json"
LEDGER_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE02_ACCEPTANCE_GATE_REPAIR_LEDGER_2026-05-25.jsonl"
RESULT_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE02_VERIFICATION_RESULT_2026-05-25.json"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def scan_ledger() -> dict[str, Any]:
    h = hashlib.sha256()
    records = []
    with LEDGER_PATH.open("rb") as raw:
        for line in raw:
            h.update(line)
            records.append(json.loads(line.decode("utf-8")))
    return {"count": len(records), "sha256": h.hexdigest(), "records": records}


def verify() -> dict[str, Any]:
    failures: list[str] = []
    summary = load_json(SUMMARY_PATH) if SUMMARY_PATH.exists() else {}
    state = load_json(STATE_PATH) if STATE_PATH.exists() else {}
    ledger = scan_ledger() if LEDGER_PATH.exists() else {"count": 0, "sha256": None, "records": []}
    families = {record.get("repair_family") for record in ledger["records"]}

    if not summary.get("old_failed_stage09_summary_rejected"):
        failures.append("old_failed_stage09_summary_not_rejected")
    if not summary.get("old_failed_stage10_audit_rejected"):
        failures.append("old_failed_stage10_audit_not_rejected")
    if not summary.get("old_failed_stage10_in_progress_completion_rejected"):
        failures.append("old_failed_stage10_in_progress_completion_not_rejected")
    if summary.get("candidate_viability", {}).get("status") != "production_candidate_failed":
        failures.append("candidate_viability_not_failed")
    if ledger["count"] != 5:
        failures.append(f"ledger_count_mismatch:{ledger['count']}")
    for required in {
        "stage09_production_candidate_viability_classifier",
        "stage09_verify_summary_rejects_failed_candidate",
        "stage10_completion_forces_failed_candidate_incomplete",
        "stage10_verify_audit_rejects_failed_candidate_and_in_progress_stage10",
        "old_behavior_regression_tests",
    }:
        if required not in families:
            failures.append(f"missing_repair_family:{required}")
    if state.get("first_incomplete_invariant") != "STAGE_03_EXECUTABLE_STREAM_AND_ROUTE_SEMANTICS_REPAIR":
        failures.append("state_first_incomplete_not_stage03")
    if state.get("stage_status_table", {}).get("STAGE_02_ACCEPTANCE_GATE_REPAIR") != "complete":
        failures.append("state_stage02_not_complete")

    return {
        "schema_version": "vnext_production_candidate_repair_stage02_verification_result_v1",
        "created_at_utc": utc_now(),
        "ok": not failures,
        "failures": failures,
        "summary_path": rel(SUMMARY_PATH),
        "ledger_path": rel(LEDGER_PATH),
        "ledger_count": ledger["count"],
        "ledger_sha256": ledger["sha256"],
        "old_failed_stage09_summary_rejected": summary.get("old_failed_stage09_summary_rejected"),
        "old_failed_stage10_audit_rejected": summary.get("old_failed_stage10_audit_rejected"),
        "candidate_viability_status": summary.get("candidate_viability", {}).get("status"),
        "first_incomplete_invariant": state.get("first_incomplete_invariant"),
    }


def mark_state(result: dict[str, Any], focused_test_result: str | None) -> None:
    state = load_json(STATE_PATH)
    state.setdefault("output_artifact_paths", {})["stage02_verification_result"] = rel(RESULT_PATH)
    state.setdefault("verification_status", {})["stage02_verifier_ok"] = result["ok"]
    state["verification_status"]["stage02_acceptance_gate_ledger_count"] = result["ledger_count"]
    state.setdefault("tests_and_verifiers_run", []).append(
        {
            "command": "py -3 verify_vnext_production_candidate_repair_stage02_acceptance_gate_repair_2026_05_25.py --mark-complete",
            "status": "passed" if result["ok"] else "failed",
            "result": {
                "ok": result["ok"],
                "failures": result["failures"],
                "first_incomplete_invariant": result["first_incomplete_invariant"],
            },
            "focused_test_result": focused_test_result,
        }
    )
    state["updated_at_utc"] = utc_now()
    with STATE_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-complete", action="store_true")
    parser.add_argument("--focused-test-result")
    args = parser.parse_args()
    result = verify()
    with RESULT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    if args.mark_complete:
        mark_state(result, args.focused_test_result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
