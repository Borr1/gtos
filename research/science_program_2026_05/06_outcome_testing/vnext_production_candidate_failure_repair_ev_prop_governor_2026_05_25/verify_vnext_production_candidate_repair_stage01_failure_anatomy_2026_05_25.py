from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
STATE_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_SESSION_STATE_2026-05-25.json"
SUMMARY_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE01_FAILURE_ANATOMY_SUMMARY_2026-05-25.json"
RESULT_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE01_VERIFICATION_RESULT_2026-05-25.json"

LEDGERS = {
    "failure_anatomy_rows": ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_FAILURE_ANATOMY_LEDGER_2026-05-25.jsonl",
    "selected_rows": ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_SELECTED_ROWS_LEDGER_2026-05-25.jsonl",
    "dropped_baseline_rows": ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_DROPPED_BASELINE_LEDGER_2026-05-25.jsonl",
    "avoid_ev_rows": ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_AVOID_EV_LEDGER_2026-05-25.jsonl",
    "route_semantics_legacy_mixed_rows": ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_ROUTE_SEMANTICS_LEDGER_2026-05-25.jsonl",
    "ltf_effect_rows": ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_LTF_ENTRY_EFFECT_LEDGER_2026-05-25.jsonl",
    "ai_policy_supervisor_rows": ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_AI_POLICY_SUPERVISOR_LEDGER_2026-05-25.jsonl",
    "acceptance_gate_failure_rows": ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_ACCEPTANCE_GATE_FAILURE_LEDGER_2026-05-25.jsonl",
}


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def scan_jsonl(path: Path, row_check: Callable[[dict[str, Any], int], list[str]] | None = None) -> dict[str, Any]:
    failures: list[str] = []
    h = hashlib.sha256()
    count = 0
    with path.open("rb") as raw:
        for raw_line in raw:
            h.update(raw_line)
            count += 1
            try:
                row = json.loads(raw_line.decode("utf-8"))
            except json.JSONDecodeError as exc:
                failures.append(f"json_decode:{count}:{exc}")
                continue
            if row_check:
                failures.extend(row_check(row, count))
    return {"count": count, "sha256": h.hexdigest(), "failures": failures}


def verify() -> dict[str, Any]:
    failures: list[str] = []
    if not SUMMARY_PATH.exists():
        failures.append(f"missing_summary:{rel(SUMMARY_PATH)}")
        summary: dict[str, Any] = {}
    else:
        summary = load_json(SUMMARY_PATH)

    row_counts = summary.get("row_counts") or {}

    def selected_check(row: dict[str, Any], line_no: int) -> list[str]:
        out = []
        if row.get("new_mechanical_selected") is not True:
            out.append(f"selected_row_not_selected:{line_no}")
        return out

    def dropped_check(row: dict[str, Any], line_no: int) -> list[str]:
        out = []
        if row.get("baseline_selection_reason") is None:
            out.append(f"dropped_row_missing_baseline_reason:{line_no}")
        if row.get("new_mechanical_selection_reason") is None:
            out.append(f"dropped_row_missing_new_reason:{line_no}")
        return out

    def avoid_check(row: dict[str, Any], line_no: int) -> list[str]:
        out = []
        if row.get("new_route_decision") != "AVOID":
            out.append(f"avoid_row_route_not_avoid:{line_no}")
        if row.get("avoid_dominance_join_status") != "joined":
            out.append(f"avoid_row_missing_dominance_join:{line_no}")
        return out

    def route_check(row: dict[str, Any], line_no: int) -> list[str]:
        out = []
        if row.get("route_decision") not in {"LEGACY", "MIXED"}:
            out.append(f"route_semantics_row_not_legacy_or_mixed:{line_no}")
        if row.get("route_reached_prop_budget") is not True:
            out.append(f"route_semantics_row_not_prop_budget_reached:{line_no}")
        return out

    checks = {
        "selected_rows": selected_check,
        "dropped_baseline_rows": dropped_check,
        "avoid_ev_rows": avoid_check,
        "route_semantics_legacy_mixed_rows": route_check,
    }

    ledger_scans: dict[str, Any] = {}
    for key, path in LEDGERS.items():
        if not path.exists():
            failures.append(f"missing_ledger:{rel(path)}")
            continue
        scan = scan_jsonl(path, checks.get(key))
        ledger_scans[key] = {"path": rel(path), "count": scan["count"], "sha256": scan["sha256"]}
        failures.extend(scan["failures"])
        if row_counts.get(key) != scan["count"]:
            failures.append(f"summary_count_mismatch:{key}:{row_counts.get(key)}!={scan['count']}")

    expected_counts = {
        "failure_anatomy_rows": 253234,
        "selected_rows": 10,
        "dropped_baseline_rows": 35977,
        "avoid_ev_rows": 37047,
        "route_semantics_legacy_mixed_rows": 174413,
        "ltf_effect_rows": 253234,
        "ai_policy_supervisor_rows": 253234,
        "acceptance_gate_failure_rows": 7,
    }
    for key, expected in expected_counts.items():
        if row_counts.get(key) != expected:
            failures.append(f"expected_count_mismatch:{key}:{row_counts.get(key)}!={expected}")

    expected_transition = {
        "baseline_false__new_false": 217247,
        "baseline_false__new_true": 4,
        "baseline_true__new_false": 35977,
        "baseline_true__new_true": 6,
    }
    if summary.get("transition_matrix") != expected_transition:
        failures.append("transition_matrix_mismatch")

    expected_routes = {"AVOID": 37047, "FOLLOW": 41774, "LEGACY": 166779, "MIXED": 7634}
    if summary.get("route_decision_distribution") != expected_routes:
        failures.append("route_decision_distribution_mismatch")

    source = summary.get("source_completeness") or {}
    if source.get("avoid_dominance_missing_rows") != 0:
        failures.append("avoid_dominance_missing_rows_nonzero")
    if source.get("all_stage09_rows_preserved") is not True:
        failures.append("all_stage09_rows_not_preserved")

    state = load_json(STATE_PATH) if STATE_PATH.exists() else {}
    if state.get("first_incomplete_invariant") != "STAGE_02_ACCEPTANCE_GATE_REPAIR":
        failures.append("state_first_incomplete_not_stage02")
    if state.get("stage_status_table", {}).get("STAGE_01_FULL_FAILURE_ANATOMY_LEDGER") != "complete":
        failures.append("state_stage01_not_complete")

    result = {
        "schema_version": "vnext_production_candidate_repair_stage01_verification_result_v1",
        "created_at_utc": utc_now(),
        "ok": not failures,
        "failures": failures,
        "summary_path": rel(SUMMARY_PATH),
        "ledger_scans": ledger_scans,
        "row_counts": row_counts,
        "transition_matrix": summary.get("transition_matrix"),
        "route_decision_distribution": summary.get("route_decision_distribution"),
        "first_incomplete_invariant": state.get("first_incomplete_invariant"),
    }
    return result


def mark_state(result: dict[str, Any], focused_test_result: str | None) -> None:
    state = load_json(STATE_PATH)
    state.setdefault("output_artifact_paths", {})["stage01_verification_result"] = rel(RESULT_PATH)
    state.setdefault("verification_status", {})["stage01_verifier_ok"] = result["ok"]
    state["verification_status"]["stage01_full_jsonl_scan_complete"] = True
    state["verification_status"]["stage01_ledger_scans"] = result["ledger_scans"]
    state.setdefault("tests_and_verifiers_run", []).append(
        {
            "command": "py -3 verify_vnext_production_candidate_repair_stage01_failure_anatomy_2026_05_25.py --mark-complete",
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
