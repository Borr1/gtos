import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-16"


def read_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def count_jsonl(name: str) -> int:
    return sum(1 for _ in iter_jsonl(ROUTE_DIR / name))


def test_required_counts_and_packet_coverage():
    assert count_jsonl(f"READY8_EXPANDED_SCORING_PACKET_ROW_ADMISSION_LEDGER_{DATE}.jsonl") == 182
    assert count_jsonl(f"READY8_EXPANDED_SCORING_ROW_BRANCH_RESULT_LEDGER_{DATE}.jsonl") == 182
    assert count_jsonl(f"READY8_EXPANDED_SCORING_HAZ001_RESULT_LEDGER_{DATE}.jsonl") == 143
    assert count_jsonl(f"READY8_EXPANDED_SCORING_MAC_INVERSE_AVOID_FILTER_RESULT_LEDGER_{DATE}.jsonl") == 32
    assert count_jsonl(f"READY8_EXPANDED_SCORING_HAZ005_REPAIRED_ROW_CONSUMPTION_RESULT_LEDGER_{DATE}.jsonl") == 5
    assert count_jsonl(f"READY8_EXPANDED_SCORING_RESIDUAL_FAILURE_INTELLIGENCE_RESULT_LEDGER_{DATE}.jsonl") == 1
    assert count_jsonl(f"READY8_EXPANDED_SCORING_REPAIRED_TARGET_CONSUMPTION_RESULT_LEDGER_{DATE}.jsonl") == 5320
    assert count_jsonl(f"READY8_EXPANDED_SCORING_KILLED_WEAKENED_DEFERRED_RESULT_FAILURE_INTELLIGENCE_LEDGER_{DATE}.jsonl") == 2641

    packet_ids = {row["packet_row_id"] for row in iter_jsonl(ROUTE_DIR / f"READY8_EXPANDED_SCORING_PACKET_ROW_ADMISSION_LEDGER_{DATE}.jsonl")}
    result_ids = {row["packet_row_id"] for row in iter_jsonl(ROUTE_DIR / f"READY8_EXPANDED_SCORING_ROW_BRANCH_RESULT_LEDGER_{DATE}.jsonl")}
    assert packet_ids == result_ids


def test_safe_flags_closed_on_core_artifacts():
    expected = {
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    for name in [
        f"READY8_EXPANDED_SCORING_DECISION_LEDGER_{DATE}.json",
        f"READY8_EXPANDED_SCORING_COMPLETION_AUDIT_{DATE}.json",
        f"READY8_EXPANDED_SCORING_METHOD_FREEZE_{DATE}.json",
        f"READY8_EXPANDED_SCORING_SOURCE_HASH_LEDGER_{DATE}.json",
    ]:
        data = read_json(ROUTE_DIR / name)
        for key, value in expected.items():
            assert data[key] == value

    for row in iter_jsonl(ROUTE_DIR / f"READY8_EXPANDED_SCORING_ROW_BRANCH_RESULT_LEDGER_{DATE}.jsonl"):
        for key, value in expected.items():
            assert row[key] == value


def test_terminal_decision_and_completion_audit():
    decision = read_json(ROUTE_DIR / f"READY8_EXPANDED_SCORING_DECISION_LEDGER_{DATE}.json")
    assert decision["terminal_decision"] == "MATERIALIZED_READY8_EXPANDED_VALIDATION_SCORING_RESULT_PACKET_G12_AUDIT_REQUIRED_NO_PROMOTION"
    assert decision["g12_post_result_audit_required"] is True
    assert decision["can_promote"] is False

    completion = read_json(ROUTE_DIR / f"READY8_EXPANDED_SCORING_COMPLETION_AUDIT_{DATE}.json")
    assert completion["same_evidence_class_intelligence_remaining"] == 0
    assert completion["requires_independent_g12_post_result_audit"] is True


def test_haz005_and_unc004_fail_closed_boundaries_are_explicit():
    haz005_rows = list(iter_jsonl(ROUTE_DIR / f"READY8_EXPANDED_SCORING_HAZ005_REPAIRED_ROW_CONSUMPTION_RESULT_LEDGER_{DATE}.jsonl"))
    assert all(row["result_status"] == "SOURCE_CONTROL_REPAIR_CONSUMED_TARGET_RESULT_JOIN_FAIL_CLOSED_FOR_THIS_PACKET_ROW" for row in haz005_rows)
    assert all("exact_impossibility_or_boundary" in row for row in haz005_rows)

    unc_rows = list(iter_jsonl(ROUTE_DIR / f"READY8_EXPANDED_SCORING_ROW_BRANCH_RESULT_LEDGER_{DATE}.jsonl"))
    unc_packet = [row for row in unc_rows if row["packet_family"] == "UNC004_SOURCE_CONFIDENCE_DIAGNOSTIC"]
    assert len(unc_packet) == 1
    assert unc_packet[0]["result_status"] == "SOURCE_CAPTURE_REQUIREMENT_NATIVE_SOURCE_CONFIDENCE_FIELDS_NOT_AVAILABLE"


def test_output_manifest_present_and_nonempty():
    manifest = read_json(ROUTE_DIR / f"READY8_EXPANDED_SCORING_OUTPUT_MANIFEST_{DATE}.json")
    assert manifest["file_count_excluding_manifest"] >= 30
    paths = {item["path"] for item in manifest["files"]}
    assert any(path.endswith(f"READY8_EXPANDED_SCORING_ROW_BRANCH_RESULT_LEDGER_{DATE}.jsonl") for path in paths)
    assert any(path.endswith(f"G12_READY8_EXPANDED_VALIDATION_SCORING_RESULT_AUDIT_GOAL_PROMPT_{DATE}.md") for path in paths)
    assert not any("G12_R8EXP_SCORING_AUDIT_" in path for path in paths)


def test_source_hash_ledger_has_portable_lf_hashes():
    source_hash = read_json(ROUTE_DIR / f"READY8_EXPANDED_SCORING_SOURCE_HASH_LEDGER_{DATE}.json")
    assert source_hash["sources"]
    mutable_paths = set(source_hash["source_hash_policy"]["mutable_coordination_source_policy"]["paths"])
    assert ".context/LIVE_STATE.md" in mutable_paths
    assert "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_ROUTE_STATUS_REGISTRY_2026-05-15.json" in mutable_paths
    for source in source_hash["sources"]:
        assert source["sha256"]
        assert source["sha256_canonical_lf"]
