from __future__ import annotations

from scripts import audit_orderflow_nas100_hypothesis_readiness as mod


def _coverage(actual: int = 1) -> dict:
    rows = []
    for idx in range(12):
        rows.append(
            {
                "symbol": "NAS100",
                "synthetic_realized_r_available": True,
                "actual_realized_r_available": idx < actual,
                "coverage_class": "actual_realized_r_available" if idx < actual else "no_actual_by_design_pre_execution_reject",
                "final_outcome": "LIMIT_PLACED" if idx < actual else "REJECTED_L2",
                "synthetic_outcome": "TP" if idx == 0 else "SL",
            }
        )
    return {"audit_rows": rows}


def _diag(winners: int = 1, losers: int = 10, context: int = 32) -> dict:
    rows = []
    for idx in range(winners):
        rows.append(
            {
                "symbol": "NAS100",
                "is_primary_proxy": True,
                "data_status": "ok",
                "event_class": "candidate",
                "candidate__synthetic_realized_r": 1.5,
            }
        )
    for idx in range(losers):
        rows.append(
            {
                "symbol": "NAS100",
                "is_primary_proxy": True,
                "data_status": "ok",
                "event_class": "candidate",
                "candidate__synthetic_realized_r": -1.0,
            }
        )
    for idx in range(context):
        rows.append(
            {
                "symbol": "NAS100",
                "is_primary_proxy": True,
                "data_status": "ok",
                "event_class": "structural_context",
            }
        )
    return {
        "feature_rows": rows,
        "synthesis": {
            "candidate_context_by_symbol": {
                "NAS100": {
                    "candidate_minus_context": {
                        "event15_median_total_depth10": -28.0,
                        "event15_thin_depth10_rate": 0.03,
                    }
                }
            },
            "outcome_by_symbol": {
                "NAS100": {
                    "winner_minus_loser": {
                        "event15_median_total_depth10": 34.0,
                        "event15_thin_depth10_rate": -0.16,
                    }
                }
            },
            "readout": ["NAS100 readout"],
        },
    }


def test_sparse_current_evidence_blocks_registration():
    payload = mod.build_payload(
        coverage_payload=_coverage(actual=1),
        trades_diag=_diag(winners=1, losers=10),
        mbp1_diag=_diag(winners=1, losers=10),
        mbp10_diag=_diag(winners=1, losers=10),
        symbol="NAS100",
    )

    assert payload["registration_verdict"] == "DO_NOT_REGISTER_REPLAY_HYPOTHESIS_YET"
    assert payload["readiness_gates"]["passed"] is False
    assert "actual_r_coverage_min_20" in payload["readiness_gates"]["failed"]
    assert "synthetic_winner_min_10" in payload["readiness_gates"]["failed"]
    assert payload["candidate_hypothesis"]["status"] == "CANDIDATE_NOT_REGISTERED"


def test_readiness_gates_pass_when_sample_is_large_enough():
    coverage = {"audit_rows": []}
    for idx in range(30):
        coverage["audit_rows"].append(
            {
                "symbol": "NAS100",
                "synthetic_realized_r_available": True,
                "actual_realized_r_available": idx < 20,
                "coverage_class": "actual_realized_r_available" if idx < 20 else "synthetic_only",
                "final_outcome": "LIMIT_PLACED",
                "synthetic_outcome": "TP" if idx < 15 else "SL",
            }
        )

    payload = mod.build_payload(
        coverage_payload=coverage,
        trades_diag=_diag(winners=15, losers=15, context=30),
        mbp1_diag=_diag(winners=15, losers=15, context=30),
        mbp10_diag=_diag(winners=15, losers=15, context=30),
        symbol="NAS100",
    )

    assert payload["readiness_gates"]["passed"] is True
    assert payload["readiness_gates"]["failed"] == []
