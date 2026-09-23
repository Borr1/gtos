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


def test_g12_decision_accepts_no_promotion_audit_only():
    decision = read_json(f"G12_R8EXP_SCORING_AUDIT_DECISION_{DATE}.json")
    assert decision["terminal_decision"] == "ACCEPT_AS_G12_READY8_EXPANDED_VALIDATION_SCORING_RESULT_AUDIT_NO_PROMOTION"
    assert decision["can_promote"] is False
    assert decision["validation_or_live_use_allowed"] is False
    assert decision["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert decision["validation_safe"] is False
    assert decision["outcome_review_opened"] is False
    assert decision["live_effect"] is False


def test_full_material_row_counts_are_exhaustive():
    assert count_jsonl(f"G12_R8EXP_SCORING_AUDIT_MATERIAL_ROWS_{DATE}.jsonl") == 11112
    assert count_jsonl(f"G12_R8EXP_SCORING_AUDIT_PACKET_COVERAGE_{DATE}.jsonl") == 182
    assert count_jsonl(f"G12_R8EXP_SCORING_AUDIT_FAILURE_INTEL_{DATE}.jsonl") == 2641
    assert count_jsonl(f"G12_R8EXP_SCORING_AUDIT_REPAIRED_TARGET_{DATE}.jsonl") == 5320
    assert count_jsonl(f"G12_R8EXP_SCORING_AUDIT_SOURCE_DRIFT_{DATE}.jsonl") == 45
    assert count_jsonl(f"G12_R8EXP_SCORING_AUDIT_R8_MANIFEST_{DATE}.jsonl") == 38


def test_packet_coverage_has_no_missing_cross_ledger_rows():
    rows = list(iter_jsonl(f"G12_R8EXP_SCORING_AUDIT_PACKET_COVERAGE_{DATE}.jsonl"))
    assert all(row["audit_status"] == "PACKET_ROW_FULLY_COVERED" for row in rows)
    families = {}
    for row in rows:
        families[row["packet_family"]] = families.get(row["packet_family"], 0) + 1
        coverage = row["coverage"]
        assert coverage["row_branch_result_present"] is True
        assert coverage["adv_control_present"] is True
        assert coverage["duplicate_effective_n_present"] is True
        assert coverage["concentration_present"] is True
        assert coverage["question_ambiguity_present"] is True
        assert coverage["source_capture_forward_retest_present"] is True
        assert coverage["open_door_count"] == 1
        assert coverage["closed_door_count"] == 1
        assert coverage["family_specific_result_present"] is True
    assert families == {
        "HAZ001_DECONCENTRATED_RETEST": 143,
        "UNC004_SOURCE_CONFIDENCE_DIAGNOSTIC": 1,
        "MAC_INVERSE_AVOID_FILTER_DESIGN": 32,
        "HAZ005_REPAIRED_DESCRIPTOR_SOURCE_CONTROL": 5,
        "CONTROL_RESIDUAL_FAILURE_INTELLIGENCE": 1,
    }


def test_failure_intelligence_and_repaired_targets_are_preserved():
    assert all(
        row["audit_status"] == "FAILURE_INTELLIGENCE_PRESERVED_NOT_ERASED"
        for row in iter_jsonl(f"G12_R8EXP_SCORING_AUDIT_FAILURE_INTEL_{DATE}.jsonl")
    )
    assert all(
        row["audit_status"] == "REPAIRED_TARGET_CONSUMPTION_VERIFIED"
        for row in iter_jsonl(f"G12_R8EXP_SCORING_AUDIT_REPAIRED_TARGET_{DATE}.jsonl")
    )


def test_no_real_immutable_source_drift_and_no_manifest_mismatch():
    recomputation = read_json(f"G12_R8EXP_SCORING_AUDIT_RECOMPUTATION_{DATE}.json")
    assert recomputation["real_immutable_source_drift_count"] == 0
    assert recomputation["r8_manifest_hash_mismatch_count"] == 0
    assert recomputation["packet_rows_full_coverage"] is True
    assert recomputation["all_issues"] == []

    source_drift = list(iter_jsonl(f"G12_R8EXP_SCORING_AUDIT_SOURCE_DRIFT_{DATE}.jsonl"))
    assert all(row["blocking"] is False for row in source_drift)


def test_instruction_coverage_and_completion_audit_cover_prompt_requirements():
    instruction = read_json(f"G12_R8EXP_SCORING_AUDIT_INSTRUCTION_COVERAGE_{DATE}.json")
    completion = read_json(f"G12_R8EXP_SCORING_AUDIT_COMPLETION_{DATE}.json")
    assert completion["completion_standard_met"] is True
    assert completion["same_g12_issue_count"] == 0
    assert completion["same_evidence_class_intelligence_remaining"] == 0
    requirements = {row["requirement"]: row["status"] for row in instruction["coverage"]}
    assert requirements["Regenerate/read LIVE_STATE and required context files"] == "COVERED"
    assert requirements["Do not rely on chat memory, R8 verifier, manifest, completion audit, or summaries alone"] == "COVERED"
    assert requirements["No arbitrary top-N or representative-only sampling"] == "COVERED"
