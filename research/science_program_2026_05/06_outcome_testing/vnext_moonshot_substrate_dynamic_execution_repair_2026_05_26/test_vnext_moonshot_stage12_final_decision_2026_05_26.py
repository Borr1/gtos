from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).with_name("verify_vnext_moonshot_stage12_completion_2026_05_26.py")
SPEC = importlib.util.spec_from_file_location("stage12_verifier", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
verifier = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = verifier
SPEC.loader.exec_module(verifier)

DATE = "2026-05-26"


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def _build_route(tmp_path: Path) -> Path:
    route = tmp_path
    _write_json(
        route / f"VNEXT_MOONSHOT_COMPLETION_AUDIT_{DATE}.json",
        {
            "stage_id": "STAGE_12_SATURATION_SELF_RED_TEAM_AND_FINAL_DECISION",
            "ok": True,
            "completion_gate_status": "complete_local_route_owner_gated_activation_not_granted",
            "forbidden_boundaries_crossed": False,
            "no_live_trading_or_broker_mutation": True,
            "no_paid_api_or_vendor_call": True,
            "question_stack": {"final_question_rows": 24328, "new_stage12_question_rows": 1},
            "active_local_issues_terminal_classification": [
                {"issue_id": "x", "terminal_classification": "handled_by_verifier"}
            ],
        },
    )
    _write_json(
        route / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE}.json",
        {
            "first_incomplete_invariant": "NONE_LOCAL_ROUTE_COMPLETE_OWNER_GATED_ACTIVATION_NOT_GRANTED",
            "completion_gate_status": "complete_local_route_owner_gated_activation_not_granted",
            "stage_status_table": {
                "STAGE_12_SATURATION_SELF_RED_TEAM_AND_FINAL_DECISION": "complete_local_route_final_decision_written"
            },
            "verifiers_tests_run": [],
        },
    )
    _write_json(route / f"VNEXT_MOONSHOT_SEMANTIC_VERIFIER_RESULT_{DATE}.json", {"ok": True})
    imported = [
        {
            "question_id": f"Q{i}",
            "stage12_final_question_status": "bounded_by_stage04_to_stage12_corrected_dynamic_artifacts",
        }
        for i in range(24327)
    ]
    imported.append(
        {
            "ledger_row_type": "stage12_discovered_question",
            "question_id": "N1",
            "stage12_final_question_status": "answered",
            "evidence_path": "x",
            "answer": "condition router evidence",
        }
    )
    _write_jsonl(route / f"VNEXT_MOONSHOT_QUESTION_STACK_LEDGER_{DATE}.jsonl", imported)
    (route / f"VNEXT_MOONSHOT_FINAL_REPORT_{DATE}.md").write_text("## Not Activation Approval\n", encoding="utf-8")
    (route / f"VNEXT_MOONSHOT_SATURATION_SELF_RED_TEAM_{DATE}.md").write_text("condition router attacked\n", encoding="utf-8")
    (route / f"VNEXT_MOONSHOT_NEXT_PRODUCTION_CHANGE_OR_VALIDATION_PLAN_{DATE}.md").write_text("owner approval required\n", encoding="utf-8")
    return route


def test_stage12_verifier_accepts_minimal_complete_route(tmp_path: Path) -> None:
    route = _build_route(tmp_path)

    result = verifier.verify_stage12(route_dir=route, write_result=False)

    assert result["ok"] is True
    assert result["imported_question_rows"] == 24327


def test_stage12_verifier_rejects_activation_claim(tmp_path: Path) -> None:
    route = _build_route(tmp_path)
    audit = json.loads((route / f"VNEXT_MOONSHOT_COMPLETION_AUDIT_{DATE}.json").read_text())
    audit["completion_gate_status"] = "complete_live_activation_ready"
    _write_json(route / f"VNEXT_MOONSHOT_COMPLETION_AUDIT_{DATE}.json", audit)

    with pytest.raises(verifier.Stage12VerificationError, match="local completion from activation"):
        verifier.verify_stage12(route_dir=route, write_result=False)


def test_stage12_verifier_rejects_missing_question_status(tmp_path: Path) -> None:
    route = _build_route(tmp_path)
    rows = [
        json.loads(line)
        for line in (route / f"VNEXT_MOONSHOT_QUESTION_STACK_LEDGER_{DATE}.jsonl").read_text().splitlines()
    ]
    rows[0].pop("stage12_final_question_status")
    _write_jsonl(route / f"VNEXT_MOONSHOT_QUESTION_STACK_LEDGER_{DATE}.jsonl", rows)

    with pytest.raises(verifier.Stage12VerificationError, match="missing final Stage12 status"):
        verifier.verify_stage12(route_dir=route, write_result=False)
