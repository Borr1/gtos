import json
from pathlib import Path

import verify_r9_forward_packet_2026_05_16 as verifier


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


def test_required_row_counts_and_packet_coverage():
    assert count_jsonl(f"R9_ROW_IDENTITY_{DATE}.jsonl") == 182
    assert count_jsonl(f"R9_HAZ001_PACKET_{DATE}.jsonl") == 143
    assert count_jsonl(f"R9_MAC_PACKET_{DATE}.jsonl") == 32
    assert count_jsonl(f"R9_HAZ005_PACKET_{DATE}.jsonl") == 5
    assert count_jsonl(f"R9_UNC004_CONTRACT_{DATE}.jsonl") == 1154
    assert count_jsonl(f"R9_RESIDUAL_PACKET_{DATE}.jsonl") == 1
    assert count_jsonl(f"R9_REPAIRED_TARGETS_{DATE}.jsonl") == 5320
    assert count_jsonl(f"R9_FAILURE_INTEL_{DATE}.jsonl") == 2641
    assert count_jsonl(f"R9_SEQUENCE_{DATE}.jsonl") == 182

    identity_ids = {row["packet_row_id"] for row in iter_jsonl(ROUTE_DIR / f"R9_ROW_IDENTITY_{DATE}.jsonl")}
    sequence_ids = {row["packet_row_id"] for row in iter_jsonl(ROUTE_DIR / f"R9_SEQUENCE_{DATE}.jsonl")}
    source_capture_ids = {row["packet_row_id"] for row in iter_jsonl(ROUTE_DIR / f"R9_SOURCE_CAPTURE_REQS_{DATE}.jsonl")}
    assert identity_ids == sequence_ids == source_capture_ids


def test_safe_flags_closed_on_core_artifacts_and_rows():
    expected = {
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    for name in [
        f"R9_DECISION_{DATE}.json",
        f"R9_COMPLETION_{DATE}.json",
        f"R9_SOURCE_HASH_{DATE}.json",
        f"R9_METHOD_{DATE}.json",
    ]:
        data = read_json(ROUTE_DIR / name)
        for key, value in expected.items():
            assert data[key] == value

    for row in iter_jsonl(ROUTE_DIR / f"R9_ROW_IDENTITY_{DATE}.jsonl"):
        for key, value in expected.items():
            assert row[key] == value
        assert row["accepted_g12_packet_coverage_status"] == "PACKET_ROW_FULLY_COVERED"


def test_terminal_decision_and_completion_audit():
    decision = read_json(ROUTE_DIR / f"R9_DECISION_{DATE}.json")
    assert decision["terminal_decision"] == "MATERIALIZED_READY8_EXPANDED_FORWARD_RETEST_SOURCE_CAPTURE_PACKET_G12_AUDIT_REQUIRED_NO_PROMOTION"
    assert decision["g12_packet_audit_required"] is True
    assert decision["can_promote"] is False
    assert decision["validation_or_live_use_allowed"] is False

    completion = read_json(ROUTE_DIR / f"R9_COMPLETION_{DATE}.json")
    assert completion["same_evidence_class_intelligence_remaining"] == 0
    assert completion["independent_g12_packet_audit_required"] is True


def test_unc004_and_haz005_boundaries_are_explicit():
    unc_rows = list(iter_jsonl(ROUTE_DIR / f"R9_UNC004_CONTRACT_{DATE}.jsonl"))
    assert sum(1 for row in unc_rows if row["contract_scope"] == "packet_row") == 1
    assert sum(1 for row in unc_rows if row["contract_scope"] == "accepted_full_row_implication") == 1153
    assert all(row.get("native_capture_requirement") or row.get("source_capture_requirements") for row in unc_rows)
    assert "native" in " ".join(row for row in unc_rows[0]["source_capture_requirements"]).lower()

    haz005_rows = list(iter_jsonl(ROUTE_DIR / f"R9_HAZ005_PACKET_{DATE}.jsonl"))
    assert len(haz005_rows) == 5
    assert all(row["result_status"] == "SOURCE_CONTROL_REPAIR_CONSUMED_TARGET_RESULT_JOIN_FAIL_CLOSED_FOR_THIS_PACKET_ROW" for row in haz005_rows)
    assert all(row["exact_row_level_impossibility"] for row in haz005_rows)


def test_failure_intelligence_preserves_allowed_doctrine_classes():
    rows = list(iter_jsonl(ROUTE_DIR / f"R9_FAILURE_INTEL_{DATE}.jsonl"))
    assert len(rows) == 2641
    assert all(row["kill_scope"] == "unsupported edge claim only; preserve failure intelligence and downstream implication" for row in rows)
    assert all(not row["unknown_doctrine_classifications"] for row in rows)


def test_verifier_passes_current_artifacts():
    result = verifier.verify(update=False, require_focused_tests=False)
    assert result["ok"], result["errors"]
