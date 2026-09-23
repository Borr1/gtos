from __future__ import annotations

from scripts import audit_orderflow_actual_outcome_coverage as mod


def test_classify_coverage_prefers_candidate_actual_r():
    candidate = {
        "candidate__realized_r_available": True,
        "candidate__realized_r": -1.0,
        "candidate__final_outcome": "LIMIT_PLACED",
    }
    record = {"path_status": "exists"}
    assert mod.classify_coverage(candidate, record) == "actual_realized_r_available"


def test_classify_coverage_rejected_rows_have_no_broker_actual_by_design():
    candidate = {
        "candidate__realized_r_available": False,
        "candidate__realized_r": None,
        "candidate__final_outcome": "REJECTED_L2",
    }
    record = {"path_status": "exists"}
    assert mod.classify_coverage(candidate, record) == "no_actual_by_design_pre_execution_reject"


def test_build_audit_rows_uses_normalized_key_and_trade_record_path(monkeypatch):
    outcome_rows = [
        {
            "symbol": "US30_cash",
            "canonical_m15_close_utc": "2026-04-17T14:00:00+00:00",
            "candidate__synthetic_realized_r": 1.5,
            "candidate__synthetic_outcome": "TP",
        }
    ]
    candidate_index = {
        ("US30", "2026-04-17T14:00:00+00:00"): {
            "candidate__realized_r_available": False,
            "candidate__realized_r": None,
            "candidate__final_outcome": "LIMIT_PLACED",
            "candidate__trade_record_matched": True,
            "candidate__trade_record_path": "dummy.json",
        }
    }

    monkeypatch.setattr(
        mod,
        "inspect_trade_record",
        lambda path: {"path_status": "exists", "trade_record_actual_r": None},
    )

    rows = mod.build_audit_rows(outcome_rows, candidate_index)
    assert rows[0]["symbol"] == "US30"
    assert rows[0]["candidate_join_matched"] is True
    assert rows[0]["coverage_class"] == "limit_placed_no_broker_close_in_join"
