import json
from pathlib import Path

import verify_g12_r10_sealed_historical_validation_result_audit_2026_05_16 as verifier


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


def test_repair_attempt_ledger_covers_all_r10_geometry_rows():
    rows = list(iter_jsonl(ROUTE_DIR / f"G12_R10_GEOMETRY_REPAIR_ATTEMPT_IMPOSSIBILITY_LEDGER_{DATE}.jsonl"))
    assert len(rows) == 5502
    assert {row["repair_status"] for row in rows} == {"NO_REPAIR_EXACT_IMPOSSIBILITY_WITHIN_G12_EVIDENCE_CLASS"}
    assert all(row["accepted_local_source_roots_searched"] for row in rows)
    assert all(row["exact_owner_access_source_capture_evidence_class_impossibility"] for row in rows)


def test_packet_rows_remain_aggregate_and_missing_entry_reference():
    rows = [
        row
        for row in iter_jsonl(ROUTE_DIR / f"G12_R10_GEOMETRY_REPAIR_ATTEMPT_IMPOSSIBILITY_LEDGER_{DATE}.jsonl")
        if row["source_row_type"] == "packet_row"
    ]
    assert len(rows) == 182
    assert all("entry_reference" in row["missing_geometry_fields_after_audit"] for row in rows)
    assert all(row["field_repair_results"]["entry_reference"].startswith("NOT_REPAIRED_PACKET_ROW") for row in rows)


def test_repaired_target_rows_repair_entry_horizon_only_and_preserve_neutral_proxy():
    rows = [
        row
        for row in iter_jsonl(ROUTE_DIR / f"G12_R10_GEOMETRY_REPAIR_ATTEMPT_IMPOSSIBILITY_LEDGER_{DATE}.jsonl")
        if row["source_row_type"] in {"repaired_target_row", "accepted_r5_repaired_target_row"}
    ]
    assert len(rows) == 5320
    assert all(row["source_control_side_if_found"] == "SIDE_NEUTRAL_SOURCE_CONTROL_INPUT" for row in rows)
    assert all(row["field_repair_results"]["entry_reference"] == "REPAIRED_SOURCE_BOUND_ENTRY_CLOSE_PRESENT" for row in rows)
    assert all(row["field_repair_results"]["horizon"] == "REPAIRED_SOURCE_BOUND_HORIZON_PRESENT" for row in rows)
    assert all(row["field_repair_results"]["trade_side"].startswith("NOT_REPAIRED_SOURCE_CONTROL_SIDE_IS_EXPLICITLY_NEUTRAL") for row in rows)
    assert all(row["strongest_proxy_preserved"]["proxy_type"] == "source_bound_neutral_target_movement" for row in rows)


def test_recomputation_accepts_no_exact_r_or_target_stop_hitmiss():
    metrics = read_json(ROUTE_DIR / f"G12_R10_METRIC_RECOMPUTATION_LEDGER_{DATE}.json")
    target_stop = read_json(ROUTE_DIR / f"G12_R10_TARGET_STOP_RECOMPUTATION_LEDGER_{DATE}.json")
    assert metrics["exact_r_expectancy_rows_computed_after_audit"] == 0
    assert metrics["target_stop_hit_miss_rows_computed_after_audit"] == 0
    assert target_stop["ambiguous_rows"] == 5502
    assert target_stop["computed_target_stop_hit_miss_rows"] == 0


def test_decision_completion_and_safe_flags():
    decision = read_json(ROUTE_DIR / f"G12_R10_DECISION_LEDGER_{DATE}.json")
    completion = read_json(ROUTE_DIR / f"G12_R10_COMPLETION_AUDIT_{DATE}.json")
    assert decision["terminal_decision"] == "ACCEPT_AS_G12_READY8_R9_SEALED_HISTORICAL_VALIDATION_RESULT_AUDIT_NO_PROMOTION"
    assert decision["can_promote"] is False
    assert decision["validation_or_live_use_allowed"] is False
    assert completion["completion_standard_met"] is True
    assert completion["same_evidence_class_intelligence_remaining"] == 0
    assert decision["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert decision["validation_safe"] is False
    assert decision["outcome_review_opened"] is False
    assert decision["live_effect"] is False


def test_verifier_passes_without_recorded_external_gates():
    result = verifier.verify(
        update=False,
        require_focused_tests=False,
        require_artifact_audit=False,
    )
    assert result["ok"], result["errors"]
