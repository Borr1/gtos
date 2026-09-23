from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_INPUT_MANIFEST_2026-05-25.json"
LEDGER_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_FAILED_ROUTE_INVALIDATION_LEDGER_2026-05-25.jsonl"
DOSSIER_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_FAILED_ROUTE_INVALIDATION_2026-05-25.md"
STATE_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_SESSION_STATE_2026-05-25.json"
RESULT_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE00_VERIFICATION_RESULT_2026-05-25.json"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def verify() -> dict[str, Any]:
    failures: list[str] = []
    for path in [MANIFEST_PATH, LEDGER_PATH, DOSSIER_PATH, STATE_PATH]:
        if not path.exists():
            failures.append(f"missing_required_output:{rel(path)}")

    manifest = load_json(MANIFEST_PATH) if MANIFEST_PATH.exists() else {}
    state = load_json(STATE_PATH) if STATE_PATH.exists() else {}
    ledger_records = []
    if LEDGER_PATH.exists():
        with LEDGER_PATH.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                try:
                    ledger_records.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    failures.append(f"ledger_json_decode_error:{line_no}:{exc}")

    facts = manifest.get("recomputed_failure_facts", {})
    if facts.get("candidate_rows") != 253234:
        failures.append("candidate_rows_not_253234")
    if facts.get("baseline_selected_count") != 35983:
        failures.append("baseline_selected_count_not_35983")
    if facts.get("new_mechanical_selected_count") != 10:
        failures.append("new_mechanical_selected_count_not_10")
    if facts.get("new_mechanical_total_r") != -4.999959196997:
        failures.append("new_mechanical_total_r_mismatch")
    if facts.get("activation_safe") is not False:
        failures.append("activation_safe_not_false")

    shards = manifest.get("stage09_replay_shards", {})
    if shards.get("total_rows") != 253234:
        failures.append("stage09_shard_total_rows_not_253234")
    if shards.get("matches_stage09_written_replay_rows") is not True:
        failures.append("stage09_shard_rows_do_not_match_summary")

    flags = manifest.get("runtime_activation_flags", {})
    if flags.get("broker_facing_vnext_activation_flags_off") is not True:
        failures.append("broker_facing_vnext_activation_flags_not_all_off")

    if manifest.get("branch_decision") != "failed_route_completion_claim_invalidated":
        failures.append("branch_decision_not_invalidation")
    if state.get("first_incomplete_invariant") != "STAGE_01_FULL_FAILURE_ANATOMY_LEDGER":
        failures.append("state_first_incomplete_not_stage01")
    if state.get("stage_status_table", {}).get("STAGE_00_INPUT_FREEZE_AND_FAILED_ROUTE_INVALIDATION") != "complete":
        failures.append("state_stage00_not_complete")

    record_types = {record.get("record_type") for record in ledger_records}
    for required in [
        "stage00_artifact_freeze",
        "failed_completion_claim_invalidated",
        "runtime_activation_boundary_preserved",
        "stage00_completion_and_next_invariant",
    ]:
        if required not in record_types:
            failures.append(f"missing_ledger_record_type:{required}")

    dossier_text = DOSSIER_PATH.read_text(encoding="utf-8") if DOSSIER_PATH.exists() else ""
    if "not activation-safe" not in dossier_text:
        failures.append("dossier_missing_not_activation_safe_verdict")
    if "First incomplete invariant: `STAGE_01_FULL_FAILURE_ANATOMY_LEDGER`" not in dossier_text:
        failures.append("dossier_missing_stage01_next_invariant")

    return {
        "schema_version": "vnext_production_candidate_repair_stage00_verification_result_v1",
        "created_at_utc": utc_now(),
        "ok": not failures,
        "failures": failures,
        "candidate_rows": facts.get("candidate_rows"),
        "baseline_selected_count": facts.get("baseline_selected_count"),
        "new_mechanical_selected_count": facts.get("new_mechanical_selected_count"),
        "new_mechanical_total_r": facts.get("new_mechanical_total_r"),
        "stage09_shard_rows": shards.get("total_rows"),
        "broker_facing_vnext_activation_flags_off": flags.get("broker_facing_vnext_activation_flags_off"),
        "first_incomplete_invariant": state.get("first_incomplete_invariant"),
        "verified_outputs": {
            "manifest": rel(MANIFEST_PATH),
            "ledger": rel(LEDGER_PATH),
            "dossier": rel(DOSSIER_PATH),
            "session_state": rel(STATE_PATH),
        },
    }


def mark_state(result: dict[str, Any], focused_test_result: str | None) -> None:
    state = load_json(STATE_PATH)
    state.setdefault("output_artifact_paths", {})["stage00_verification_result"] = rel(RESULT_PATH)
    state.setdefault("verification_status", {})["stage00_verifier_ok"] = result["ok"]
    state["verification_status"]["stage00_verified_candidate_rows"] = result["candidate_rows"]
    state["verification_status"]["stage00_verified_shard_rows"] = result["stage09_shard_rows"]
    state["verification_status"]["stage00_broker_facing_activation_flags_off"] = result["broker_facing_vnext_activation_flags_off"]
    state.setdefault("tests_and_verifiers_run", []).append(
        {
            "command": "py -3 verify_vnext_production_candidate_repair_stage00_invalidation_2026_05_25.py --mark-complete",
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
