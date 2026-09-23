from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-26"
STAGE_ID = "STAGE_12_SATURATION_SELF_RED_TEAM_AND_FINAL_DECISION"

COMPLETION_AUDIT = ROUTE_DIR / f"VNEXT_MOONSHOT_COMPLETION_AUDIT_{DATE}.json"
QUESTION_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_QUESTION_STACK_LEDGER_{DATE}.jsonl"
FINAL_REPORT = ROUTE_DIR / f"VNEXT_MOONSHOT_FINAL_REPORT_{DATE}.md"
SATURATION_REPORT = ROUTE_DIR / f"VNEXT_MOONSHOT_SATURATION_SELF_RED_TEAM_{DATE}.md"
NEXT_PLAN = ROUTE_DIR / f"VNEXT_MOONSHOT_NEXT_PRODUCTION_CHANGE_OR_VALIDATION_PLAN_{DATE}.md"
SESSION_STATE = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE}.json"
SEMANTIC_RESULT = ROUTE_DIR / f"VNEXT_MOONSHOT_SEMANTIC_VERIFIER_RESULT_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE12_VERIFICATION_RESULT_{DATE}.json"


class Stage12VerificationError(AssertionError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            yield line_no, json.loads(line)


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def verify_stage12(
    *,
    route_dir: Path = ROUTE_DIR,
    write_result: bool = True,
) -> dict[str, Any]:
    errors: list[str] = []
    audit = read_json(route_dir / COMPLETION_AUDIT.name)
    state = read_json(route_dir / SESSION_STATE.name)
    semantic = read_json(route_dir / SEMANTIC_RESULT.name)

    require(errors, audit.get("stage_id") == STAGE_ID, "completion audit has wrong stage_id")
    require(errors, audit.get("ok") is True, "completion audit ok is not true")
    require(
        errors,
        audit.get("completion_gate_status") == "complete_local_route_owner_gated_activation_not_granted",
        "completion audit does not distinguish local completion from activation",
    )
    require(errors, audit.get("forbidden_boundaries_crossed") is False, "forbidden boundary crossed")
    require(errors, audit.get("no_live_trading_or_broker_mutation") is True, "no-live boundary missing")
    require(errors, audit.get("no_paid_api_or_vendor_call") is True, "no-paid boundary missing")
    require(errors, semantic.get("ok") is True, "Stage11 semantic verifier is not ok")
    require(
        errors,
        state.get("first_incomplete_invariant") == "NONE_LOCAL_ROUTE_COMPLETE_OWNER_GATED_ACTIVATION_NOT_GRANTED",
        "session state first incomplete is not the local-complete sentinel",
    )
    require(errors, state.get("completion_gate_status") == audit.get("completion_gate_status"), "state/audit completion mismatch")
    require(
        errors,
        state.get("stage_status_table", {}).get(STAGE_ID) == "complete_local_route_final_decision_written",
        "Stage12 is not marked complete in route state",
    )

    question_rows = 0
    missing_final_status = 0
    imported_rows = 0
    new_rows = 0
    status_counts: Counter[str] = Counter()
    for _line_no, row in iter_jsonl(route_dir / QUESTION_LEDGER.name):
        question_rows += 1
        if not row.get("stage12_final_question_status"):
            missing_final_status += 1
        if row.get("ledger_row_type") == "stage12_discovered_question":
            new_rows += 1
            require(errors, bool(row.get("evidence_path")), f"new question {row.get('question_id')} lacks evidence_path")
            require(errors, bool(row.get("answer")), f"new question {row.get('question_id')} lacks answer")
        else:
            imported_rows += 1
        status_counts[str(row.get("stage12_final_question_status"))] += 1
    audit_questions = audit.get("question_stack", {})
    require(errors, question_rows == audit_questions.get("final_question_rows"), "question ledger row count does not match audit")
    require(errors, imported_rows == 24327, "imported question rows were not fully preserved")
    require(errors, new_rows == audit_questions.get("new_stage12_question_rows"), "new question row count mismatch")
    require(errors, missing_final_status == 0, "question rows missing final Stage12 status")

    for issue in audit.get("active_local_issues_terminal_classification", []):
        terminal = str(issue.get("terminal_classification") or "")
        require(errors, bool(terminal), f"issue {issue.get('issue_id')} lacks terminal classification")
        require(errors, "known_issue" not in terminal and "caveat" not in terminal, f"issue {issue.get('issue_id')} buried as caveat/known issue")

    report_text = (route_dir / FINAL_REPORT.name).read_text(encoding="utf-8")
    saturation_text = (route_dir / SATURATION_REPORT.name).read_text(encoding="utf-8")
    plan_text = (route_dir / NEXT_PLAN.name).read_text(encoding="utf-8")
    require(errors, "Not Activation Approval" in report_text, "final report lacks no-activation section")
    require(errors, "condition router" in saturation_text, "saturation report does not attack condition router")
    require(errors, "owner approval" in plan_text.lower(), "next plan lacks owner approval gate")

    result = {
        "schema_version": "vnext_moonshot_stage12_verification_result_v1",
        "stage_id": STAGE_ID,
        "generated_at_utc": utc_now(),
        "ok": not errors,
        "errors": errors,
        "question_rows": question_rows,
        "imported_question_rows": imported_rows,
        "new_question_rows": new_rows,
        "question_status_counts": dict(sorted(status_counts.items())),
        "completion_gate_status": audit.get("completion_gate_status"),
        "first_incomplete_invariant": state.get("first_incomplete_invariant"),
    }
    if write_result:
        (route_dir / VERIFY_RESULT.name).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not errors:
            command = (
                "py -3 research/science_program_2026_05/06_outcome_testing/"
                "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/"
                "verify_vnext_moonshot_stage12_completion_2026_05_26.py"
            )
            if not any(entry.get("command") == command for entry in state.setdefault("verifiers_tests_run", [])):
                state["verifiers_tests_run"].append(
                    {
                        "command": command,
                        "status": "passed",
                        "result": f"ok=true; question_rows={question_rows}; completion_gate_status={audit.get('completion_gate_status')}",
                    }
                )
                (route_dir / SESSION_STATE.name).write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if errors:
        raise Stage12VerificationError("; ".join(errors))
    return result


def main() -> None:
    result = verify_stage12(write_result=True)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
