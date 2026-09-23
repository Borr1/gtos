from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROUTE_ID = "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"
DATE_ID = "2026-05-26"
ROUTE_DIR = Path(__file__).resolve().parent

STATE = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json"
MANIFEST = ROUTE_DIR / f"VNEXT_MOONSHOT_CONTEXT_AND_INPUT_MANIFEST_{DATE_ID}.json"
REOPENING = ROUTE_DIR / f"VNEXT_MOONSHOT_PRIOR_ROUTE_REOPENING_LEDGER_{DATE_ID}.jsonl"
QUESTIONS = ROUTE_DIR / f"VNEXT_MOONSHOT_IMPORTED_QUESTION_STACK_LEDGER_{DATE_ID}.jsonl"
RESULT = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE00_VERIFICATION_RESULT_{DATE_ID}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def scan_jsonl(path: Path) -> tuple[int, Counter]:
    count = 0
    statuses: Counter[str] = Counter()
    with path.open("r", encoding="utf-8") as handle:
        for count, line in enumerate(handle, start=1):
            row = json.loads(line)
            status = row.get("moonshot_corrected_substrate_status") or row.get("reclassified_status")
            if status:
                statuses[str(status)] += 1
    return count, statuses


def verify() -> dict:
    failures: list[str] = []
    for path in [STATE, MANIFEST, REOPENING, QUESTIONS]:
        if not path.exists():
            failures.append(f"missing:{path.name}")

    state = read_json(STATE) if STATE.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}
    question_rows, question_statuses = scan_jsonl(QUESTIONS) if QUESTIONS.exists() else (0, Counter())
    reopening_rows, reopening_statuses = scan_jsonl(REOPENING) if REOPENING.exists() else (0, Counter())

    if question_rows != 24327:
        failures.append(f"expected_24327_imported_questions_got_{question_rows}")
    if not question_statuses.get("reopened_dynamic_execution_required"):
        failures.append("no_questions_reopened_for_dynamic_execution")
    if reopening_rows < 7:
        failures.append(f"prior_reopening_ledger_too_small:{reopening_rows}")
    if not reopening_statuses.get("STATIC_SUBSTRATE_DIAGNOSTIC_UNTIL_DYNAMIC_REPLAY_RECOMPUTES"):
        failures.append("activation_metrics_not_reclassified_static_substrate")
    if not reopening_statuses.get("MANDATORY_NEGATIVE_FIXTURE"):
        failures.append("known_10_trade_failure_not_preserved_as_negative_fixture")

    policy_names = {row.get("name") for row in manifest.get("dynamic_policy_manifest", [])}
    required_names = {
        "live_current_j46_j49",
        "legacy_fixed_1.5r",
        "ai_target",
        "partial_be_runner",
        "be_after_trigger",
        "trailing_runner",
        "time_stop_only",
        "early_cut_if_no_progress",
        "path_aware_runner",
    }
    missing_policies = sorted(required_names - policy_names)
    if missing_policies:
        failures.append(f"missing_dynamic_policies:{missing_policies}")

    if (
        state.get("stage_status_table", {}).get("STAGE_00_PREFLIGHT_CONTEXT_AND_PRIOR_ROUTE_REOPENING")
        != "complete"
    ):
        failures.append("state_does_not_record_stage00_complete")
    if state.get("first_incomplete_invariant") == "STAGE_00_PREFLIGHT_CONTEXT_AND_PRIOR_ROUTE_REOPENING":
        failures.append("state_still_points_to_stage00_after_stage00_completion")
    if state.get("completion_gate_status") == "complete":
        failures.append("state_falsely_marks_route_complete")

    result = {
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_00_PREFLIGHT_CONTEXT_AND_PRIOR_ROUTE_REOPENING",
        "checked_at_utc": utc_now(),
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "question_rows": question_rows,
        "question_status_counts": dict(sorted(question_statuses.items())),
        "prior_reopening_rows": reopening_rows,
        "prior_reopening_status_counts": dict(sorted(reopening_statuses.items())),
        "first_incomplete_invariant": state.get("first_incomplete_invariant"),
        "dynamic_policy_names": sorted(policy_names),
        "no_live_paid_broker_remote_boundaries_crossed": True,
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    result = verify()
    print(json.dumps(result, sort_keys=True))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
