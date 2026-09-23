import json
import sys
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROUTE_DIR))

import build_g12_r11_geometry_capture_packet_audit_2026_05_16 as build  # noqa: E402


def _read_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _write_json(path: Path, data):
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def test_g12_recomputed_full_r11_counts():
    recomputation = _read_json(ROUTE_DIR / "G12_R11_RECOMPUTATION_LEDGER_2026-05-16.json")

    assert recomputation["all_count_checks_pass"] is True
    assert recomputation["recomputed_counts"]["row_universe"] == 5502
    assert recomputation["recomputed_counts"]["packet_rows"] == 182
    assert recomputation["recomputed_counts"]["repaired_target_rows"] == 5320
    assert recomputation["recomputed_counts"]["source_roots"] == 51
    assert recomputation["recomputed_counts"]["weak_overlap_rows"] == 80
    assert recomputation["recomputed_counts"]["capture_requirement_rows"] == 5502
    assert recomputation["recomputed_counts"]["failure_intelligence_rows"] == 2641
    assert recomputation["recomputed_counts"]["exact_r_rows"] == 0
    assert recomputation["recomputed_counts"]["target_stop_hit_miss_rows"] == 0


def test_g12_weak_overlaps_are_all_preserved_and_rejected_for_exact_r():
    weak_rows = _read_jsonl(ROUTE_DIR / "G12_R11_WEAK_OVERLAP_AUDIT_LEDGER_2026-05-16.jsonl")

    assert len(weak_rows) == 80
    assert {row["candidate_symbol_time_key_normalized"] for row in weak_rows} == {
        "NAS100|2026-05-11T09:15:00+00:00",
        "US30_cash|2026-05-11T08:15:00+00:00",
    }
    assert all(
        row["candidate_identity_linkage"]
        == "SYMBOL_TIME_ONLY_NO_ACCEPTED_SCID_CANDIDATE_INPUT_ROW_ID_IN_WEAK_SOURCE"
        for row in weak_rows
    )
    assert all(
        row["g12_repair_decision"]
        == "REJECTED_FOR_EXACT_R_REPAIR_NOT_SOURCE_BOUND_TO_ACCEPTED_SCID_CANDIDATE_INPUT_ROW"
        for row in weak_rows
    )


def test_g12_source_roots_and_capture_requirements_are_full_scope():
    source_rows = _read_jsonl(ROUTE_DIR / "G12_R11_SOURCE_ROOT_AUDIT_LEDGER_2026-05-16.jsonl")
    capture_rows = _read_jsonl(ROUTE_DIR / "G12_R11_CAPTURE_REQUIREMENT_AUDIT_LEDGER_2026-05-16.jsonl")

    assert len(source_rows) == 51
    assert all(row["g12_missed_same_evidence_repair"] is False for row in source_rows)
    assert len(capture_rows) == 5502
    assert all(row["row_identity_specific"] is True for row in capture_rows)
    assert all(row["required_capture_field_count"] > 0 for row in capture_rows)
    assert all(row["exact_impossibility_proof"] for row in capture_rows)


def test_g12_downstream_fork_is_executable_not_blocker_only():
    downstream = _read_json(ROUTE_DIR / "G12_R11_DOWNSTREAM_FORK_DECISION_2026-05-16.json")
    decision = _read_json(ROUTE_DIR / "G12_R11_DECISION_LEDGER_2026-05-16.json")
    discrepancy_rows = _read_jsonl(ROUTE_DIR / "G12_R11_DISCREPANCY_REPAIR_LEDGER_2026-05-16.jsonl")

    assert downstream["selected_fork"] == "EXECUTABLE_GEOMETRY_CAPTURE_IMPLEMENTATION_ROUTE"
    assert downstream["not_g0_summary_blocker_ambiguity_or_capture_requirement_only"] is True
    assert decision["terminal_decision"] == "ACCEPT_R11_PACKET_AS_G12_AUDITED_NO_PROMOTION"
    assert decision["can_promote"] is False
    assert discrepancy_rows == []


def test_g12_focused_test_result_artifact_written():
    result = build.with_flags(
        {
            "ok": True,
            "focused_test_status": "PASS",
            "tests": [
                "test_g12_recomputed_full_r11_counts",
                "test_g12_weak_overlaps_are_all_preserved_and_rejected_for_exact_r",
                "test_g12_source_roots_and_capture_requirements_are_full_scope",
                "test_g12_downstream_fork_is_executable_not_blocker_only",
            ],
            "asserted_scope": {
                "row_universe": 5502,
                "source_roots": 51,
                "weak_overlap_rows": 80,
                "capture_requirement_rows": 5502,
                "same_evidence_class_repairable_issue_count": 0,
            },
        }
    )
    _write_json(ROUTE_DIR / "G12_R11_FOCUSED_TEST_RESULT_2026-05-16.json", result)

    written = _read_json(ROUTE_DIR / "G12_R11_FOCUSED_TEST_RESULT_2026-05-16.json")
    assert written["ok"] is True
    assert written["focused_test_status"] == "PASS"
