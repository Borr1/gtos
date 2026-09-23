from __future__ import annotations

import json
from pathlib import Path

from src.research_infra import nas100_orderflow_adverse_selection as mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _forensics(mbp10_candidates: int = 12, mbo_candidates: int = 12) -> dict:
    return {
        "synthesis": {"status": "DIAGNOSTIC_ONLY_LABEL_LIMITED"},
        "feature_family_forward_plan": [
            {
                "family": "depth_availability_thinness",
                "priority": "KEEP_FORWARD_DEFAULT",
                "fields": ["event15_median_total_depth10"],
            }
        ],
        "feeds": {
            "MBP10_TOP10": {
                "coverage": {"ok_rows": 73, "candidate_rows": mbp10_candidates, "context_rows": 61},
                "label_coverage": {"synthetic_label_n": 11, "actual_r_n": 1},
                "concentration": {"candidate_by_date": {"top_share": 0.75}},
                "stability": {
                    "event15_total_depth": {
                        "leave_one_date": {
                            "full_delta": -20.0,
                            "sign_flip_count": 1,
                            "max_abs_change_vs_full": 68.5,
                        }
                    }
                },
            },
            "MBO_TOP20": {
                "coverage": {"ok_rows": 59, "candidate_rows": mbo_candidates, "context_rows": 47},
                "label_coverage": {"synthetic_label_n": 11, "actual_r_n": 1},
                "concentration": {"candidate_by_date": {"top_share": 0.75}},
                "stability": {
                    "event15_total_depth": {
                        "leave_one_date": {
                            "full_delta": -33.5,
                            "sign_flip_count": 1,
                            "max_abs_change_vs_full": 144.5,
                        }
                    }
                },
            },
        },
    }


def test_build_status_row_tracks_license_blocker_and_sample_floors():
    row = mod.build_status_row(
        generated_at_utc="2026-05-05T00:00:00+00:00",
        source_dependency_signature="abc",
        forensics=_forensics(),
        forward_readiness={"current_counts": {"v2b_forward_pair_rows": 0}},
        databento_confluence_rows=[
            {
                "status": "LIVE_SESSION_FAILED_NO_LICENSE",
                "message": "A live data license is required",
                "paid_fetch_attempted": True,
                "databento_calls": 1,
            }
        ],
        databento_budget_rows=[{"budget_status": "LIVE_SESSION_FAILED_NO_LICENSE"}],
        broker_actual_r_rows=[
            {
                "symbol": "NAS100",
                "trade_id": "NAS100_1",
                "actual_r_claim_allowed": True,
                "accounting_evidence_class": "ACCOUNT_HISTORY_REALIZED",
                "broker_actual_r": -1.0,
            }
        ],
        forward_request_rows=[
            {"raw_symbol": "NQ.v.0", "schema": "mbp-10", "status": "DECLARED_NOT_FETCHED"},
            {"source_event_id": "NAS100_CONTEXT", "schema": "trades", "status": "DECLARED_NOT_FETCHED"},
        ],
    )

    assert row["schema_version"] == mod.SCHEMA_VERSION
    assert row["status"] == "WAITING_FOR_DATABENTO_LIVE_LICENSE"
    assert row["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert row["current_counts"]["cached_mbp10_candidate_rows"] == 12
    assert row["current_counts"]["broker_actual_r_rows_nas100_unique"] == 1
    assert row["databento_live_status"]["license_blocker"] is True
    assert row["readiness_gates"]["promotion_claim_allowed"] is False
    assert row["paid_data_calls"] == 0
    assert row["paid_fetch_attempted"] is False


def test_report_reads_local_artifacts_and_does_not_fetch(tmp_path):
    _write_json(tmp_path / mod.DEFAULT_FORENSICS_JSON, _forensics())
    _write_json(
        tmp_path / mod.DEFAULT_FORWARD_READINESS_JSON,
        {"current_counts": {"v2b_forward_pair_rows": 0}},
    )
    _write_jsonl(
        tmp_path / mod.DEFAULT_DATABENTO_CONFLUENCE_LOG,
        [{"status": "LIVE_SESSION_FAILED_NO_LICENSE", "message": "license required"}],
    )
    _write_jsonl(tmp_path / mod.DEFAULT_DATABENTO_BUDGET_LOG, [{"budget_status": "LIVE_SESSION_FAILED_NO_LICENSE"}])
    _write_jsonl(
        tmp_path / mod.DEFAULT_BROKER_ACTUAL_R_LOG,
        [
            {
                "symbol": "NAS100",
                "trade_id": "NAS100_1",
                "actual_r_claim_allowed": True,
                "accounting_evidence_class": "ACCOUNT_HISTORY_REALIZED",
                "broker_actual_r": -1.0,
            }
        ],
    )
    _write_jsonl(tmp_path / mod.DEFAULT_FORWARD_REQUESTS_LOG, [{"raw_symbol": "NQ.v.0", "schema": "mbp-10"}])

    report = mod.build_report(root=tmp_path, generated_at_utc="2026-05-05T00:00:00+00:00")

    assert report["schema_version"] == mod.REPORT_SCHEMA_VERSION
    assert report["status"] == "WAITING_FOR_DATABENTO_LIVE_LICENSE"
    assert report["completion_evidence"]["new_databento_fetches_made_by_audit"] == 0
    assert report["status_row"]["trigger_criteria"]["databento_raw_symbol"] == "NQ.FUT"


def test_missing_live_status_does_not_count_as_licensed():
    status = mod.readiness_status(
        cached_mbp10_candidate_rows=30,
        nas100_actual_r_rows=20,
        databento_live_license_available=False,
        live_license_status=None,
    )

    assert status == "WAITING_FOR_DATABENTO_LIVE_SUCCESSFUL_SAMPLE"


def test_append_status_row_if_missing_is_idempotent(tmp_path):
    path = tmp_path / "shadow_logs" / "nas100_orderflow.jsonl"
    row = {
        "schema_version": mod.SCHEMA_VERSION,
        "row_key": "same",
        "created_at_utc": "2026-05-05T00:00:00+00:00",
    }

    assert mod.append_status_row_if_missing(row, path) is True
    assert mod.append_status_row_if_missing(row, path) is False
    assert len(path.read_text(encoding="utf-8").splitlines()) == 1
