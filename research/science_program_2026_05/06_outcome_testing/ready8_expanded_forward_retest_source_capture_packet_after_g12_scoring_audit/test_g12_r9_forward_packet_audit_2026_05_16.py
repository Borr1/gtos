import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-16"


def read_json(name: str):
    with (ROUTE_DIR / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(name: str):
    with (ROUTE_DIR / name).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def count_jsonl(name: str) -> int:
    return sum(1 for _ in iter_jsonl(name))


def test_g12_r9_decision_accepts_no_promotion_packet_audit_only():
    decision = read_json(f"G12_R9_PACKET_AUDIT_DECISION_{DATE}.json")
    assert decision["terminal_decision"] == "ACCEPT_AS_G12_READY8_EXPANDED_FORWARD_RETEST_SOURCE_CAPTURE_PACKET_AUDIT_NO_PROMOTION"
    assert decision["can_promote"] is False
    assert decision["validation_or_live_use_allowed"] is False
    assert decision["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert decision["validation_safe"] is False
    assert decision["outcome_review_opened"] is False
    assert decision["live_effect"] is False


def test_full_material_row_counts_are_exhaustive():
    assert count_jsonl(f"G12_R9_PACKET_AUDIT_MATERIAL_ROWS_{DATE}.jsonl") == 10668
    assert count_jsonl(f"G12_R9_PACKET_AUDIT_JSON_ARTIFACTS_{DATE}.jsonl") == 20
    assert count_jsonl(f"G12_R9_PACKET_AUDIT_PACKET_COVERAGE_{DATE}.jsonl") == 182
    assert count_jsonl(f"G12_R9_PACKET_AUDIT_FAILURE_INTEL_{DATE}.jsonl") == 2641
    assert count_jsonl(f"G12_R9_PACKET_AUDIT_REPAIRED_TARGET_{DATE}.jsonl") == 5320
    assert count_jsonl(f"G12_R9_PACKET_AUDIT_BLOCKERS_{DATE}.jsonl") == 22
    assert count_jsonl(f"G12_R9_PACKET_AUDIT_SEQUENCE_{DATE}.jsonl") == 182
    assert count_jsonl(f"G12_R9_PACKET_AUDIT_SOURCE_DRIFT_{DATE}.jsonl") == 74
    assert count_jsonl(f"G12_R9_PACKET_AUDIT_R9_MANIFEST_{DATE}.jsonl") == 41


def test_packet_coverage_maps_every_row_to_accepted_r8_g12_coverage():
    rows = list(iter_jsonl(f"G12_R9_PACKET_AUDIT_PACKET_COVERAGE_{DATE}.jsonl"))
    assert all(row["audit_status"] == "PACKET_ROW_FULLY_COVERED_AND_R8_G12_TRACEABLE" for row in rows)
    families = {}
    for row in rows:
        families[row["packet_family"]] = families.get(row["packet_family"], 0) + 1
        coverage = row["coverage"]
        assert coverage["accepted_r8_g12_packet_coverage_present"] is True
        assert coverage["accepted_r8_g12_packet_coverage_status_ok"] is True
        assert coverage["accepted_r8_g12_branch_hash_match"] is True
        assert coverage["accepted_r8_g12_coverage_payload_match"] is True
        assert coverage["r9_identity_coverage_status_ok"] is True
        assert coverage["source_capture_present"] is True
        assert coverage["forward_implication_present"] is True
        assert coverage["sequence_present"] is True
        assert coverage["question_present"] is True
        assert coverage["open_door_count"] == 1
        assert coverage["closed_door_count"] == 1
        assert coverage["family_specific_row_present"] is True
        assert coverage["family_specific_boundary_ok"] is True
    assert families == {
        "HAZ001_DECONCENTRATED_RETEST": 143,
        "UNC004_SOURCE_CONFIDENCE_DIAGNOSTIC": 1,
        "MAC_INVERSE_AVOID_FILTER_DESIGN": 32,
        "HAZ005_REPAIRED_DESCRIPTOR_SOURCE_CONTROL": 5,
        "CONTROL_RESIDUAL_FAILURE_INTELLIGENCE": 1,
    }


def test_repaired_targets_failure_intelligence_blockers_and_sequence_are_verified():
    assert all(
        row["audit_status"] == "REPAIRED_TARGET_CONSUMPTION_VERIFIED"
        for row in iter_jsonl(f"G12_R9_PACKET_AUDIT_REPAIRED_TARGET_{DATE}.jsonl")
    )
    assert all(
        row["audit_status"] == "FAILURE_INTELLIGENCE_PRESERVED_NOT_ERASED"
        for row in iter_jsonl(f"G12_R9_PACKET_AUDIT_FAILURE_INTEL_{DATE}.jsonl")
    )
    assert all(
        row["audit_status"] == "BLOCKER_EXACTLY_BOUNDED_OR_REPAIRED"
        for row in iter_jsonl(f"G12_R9_PACKET_AUDIT_BLOCKERS_{DATE}.jsonl")
    )
    assert all(
        row["audit_status"] == "PACKET_SEQUENCE_BOUNDARY_VERIFIED"
        for row in iter_jsonl(f"G12_R9_PACKET_AUDIT_SEQUENCE_{DATE}.jsonl")
    )


def test_no_real_source_drift_or_manifest_mismatch():
    recomputation = read_json(f"G12_R9_PACKET_AUDIT_RECOMPUTATION_{DATE}.json")
    assert recomputation["real_immutable_source_drift_count"] == 0
    assert recomputation["r9_manifest_hash_mismatch_count"] == 0
    assert recomputation["packet_rows_full_coverage"] is True
    assert recomputation["all_issues"] == []

    source_drift = list(iter_jsonl(f"G12_R9_PACKET_AUDIT_SOURCE_DRIFT_{DATE}.jsonl"))
    assert all(row["blocking"] is False for row in source_drift)


def test_instruction_coverage_and_completion_cover_prompt_requirements():
    instruction = read_json(f"G12_R9_PACKET_AUDIT_INSTRUCTION_COVERAGE_{DATE}.json")
    completion = read_json(f"G12_R9_PACKET_AUDIT_COMPLETION_{DATE}.json")
    assert instruction["all_requirements_satisfied"] is True
    assert completion["completion_standard_met"] is True
    assert completion["same_g12_issue_count"] == 0
    assert completion["same_evidence_class_intelligence_remaining"] == 0
    requirements = {row["requirement"]: row["status"] for row in instruction["coverage"]}
    assert requirements["No arbitrary top-N, top 3/5/10, representative-only, or number-limited cutoff"] == "COVERED"
    assert requirements["Verify every packet row maps to accepted G12 R8 scoring packet coverage"] == "COVERED"
    assert requirements["Preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false, and forbidden surfaces"] == "COVERED"
