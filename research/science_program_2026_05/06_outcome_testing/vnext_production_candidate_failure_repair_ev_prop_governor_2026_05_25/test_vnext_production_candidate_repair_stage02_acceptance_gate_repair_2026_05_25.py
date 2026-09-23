from __future__ import annotations

import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
SUMMARY_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE02_ACCEPTANCE_GATE_REPAIR_SUMMARY_2026-05-25.json"
LEDGER_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE02_ACCEPTANCE_GATE_REPAIR_LEDGER_2026-05-25.jsonl"


def test_stage02_rejects_old_failed_stage09_and_stage10_outputs() -> None:
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    assert summary["old_failed_stage09_summary_rejected"] is True
    assert summary["old_failed_stage10_audit_rejected"] is True
    assert summary["old_failed_stage10_in_progress_completion_rejected"] is True
    assert summary["candidate_viability"]["status"] == "production_candidate_failed"
    assert "production_candidate_failed" in " ".join(summary["stage09_failures_on_old_summary"])
    assert "production_candidate_failed" in " ".join(summary["stage10_failures_on_old_audit"])


def test_stage02_ledger_records_all_repaired_gate_families() -> None:
    records = [json.loads(line) for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines()]
    families = {record["repair_family"] for record in records}

    assert len(records) == 5
    assert "stage09_production_candidate_viability_classifier" in families
    assert "stage09_verify_summary_rejects_failed_candidate" in families
    assert "stage10_completion_forces_failed_candidate_incomplete" in families
    assert "stage10_verify_audit_rejects_failed_candidate_and_in_progress_stage10" in families
    assert "old_behavior_regression_tests" in families
