from __future__ import annotations

from scripts import build_orderflow_forward_collection_plan as mod


def _manifest() -> dict:
    return {
        "schema_version": "orderflow_event_window_manifest_v1",
        "inputs": {
            "rows_loaded": 2,
            "available_end_utc": "2026-05-01T16:00:00+00:00",
            "supported_symbol_map": {"NAS100": ["NQ.v.0"], "XAUUSD": ["GC.v.0"]},
        },
        "events": [
            {"symbol": "NAS100", "event_class": "candidate", "event_id": "nas_1"},
            {"symbol": "XAUUSD", "event_class": "structural_context", "event_id": "xau_1"},
        ],
        "fetch_groups": [
            {
                "group_id": "ofwin_0001",
                "gtos_symbols": ["NAS100"],
                "event_count": 1,
                "event_classes": [["candidate", 1]],
                "start_utc": "2026-05-01T13:00:00+00:00",
                "end_utc": "2026-05-01T14:00:00+00:00",
            }
        ],
    }


def _fetch_plan(schema: str) -> dict:
    return {
        "executed": True,
        "blocked": False,
        "inputs": {"schema": schema},
        "groups": [{"status": "fetched"}],
        "total_estimated_cost_usd": 0.25,
    }


def _diag() -> dict:
    return {
        "feature_rows": [
            {
                "symbol": "NAS100",
                "is_primary_proxy": True,
                "data_status": "ok",
                "event_class": "candidate",
                "candidate__synthetic_realized_r": -1.0,
            },
            {
                "symbol": "NAS100",
                "is_primary_proxy": True,
                "data_status": "ok",
                "event_class": "structural_context",
            },
        ]
    }


def test_build_payload_surfaces_supported_and_unsupported_collection_constraints():
    payload = mod.build_payload(
        source_rows=[
            {"symbol": "NAS100", "decision": "CANDIDATE", "candle_close_utc": "2026-05-01T15:45:00+00:00"},
            {"symbol": "XAGUSD", "decision": "CANDIDATE", "candle_close_utc": "2026-05-01T16:15:00+00:00"},
        ],
        manifest=_manifest(),
        trades_fetch_plan=_fetch_plan("trades"),
        mbp1_fetch_plan=_fetch_plan("mbp-1"),
        mbp10_fetch_plan=_fetch_plan("mbp-10"),
        trades_diag=_diag(),
        mbp1_diag=_diag(),
        mbp10_diag=_diag(),
        coverage={
            "audit_rows": [
                {
                    "symbol": "NAS100",
                    "synthetic_realized_r_available": True,
                    "actual_realized_r_available": False,
                    "synthetic_outcome": "SL",
                    "coverage_class": "no_actual_by_design_pre_execution_reject",
                    "final_outcome": "REJECTED_L2",
                }
            ]
        },
        limit_recon={"counts": {"limit_rows_audited": 1, "broker_actual_r_rows": 0, "counterfactual_m1_tp_rows": 1}},
        nas_readiness={
            "readiness_gates": {"failed": ["synthetic_winner_min_10"]},
            "label_counts": {"synthetic_winners": 1, "synthetic_losers": 10},
        },
    )

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["source_log_summary"]["supported_candidate_count"] == 1
    assert payload["source_log_summary"]["unsupported_candidate_count"] == 1
    assert payload["source_log_summary"]["candidates_after_available_end"] == 1
    assert payload["manifest_summary"]["candidate_events_by_symbol"] == {"NAS100": 1}
    assert payload["coverage_by_symbol"]["NAS100"]["synthetic_outcomes"] == {"SL": 1}
    assert payload["collection_actions"][0]["action_id"] == "A1_NAS100_FORWARD_LABEL_AND_DEPTH_COLLECTION"
    assert payload["collection_actions"][0]["status"] == "COLLECT_FORWARD_NOT_REPLAY"
    assert payload["collection_actions"][1]["status"] == "BLOCKED_BY_MISSING_LIVE_TELEMETRY"


def test_limit_reconciliation_synthesis_counts_feed_action_evidence():
    payload = mod.build_payload(
        source_rows=[],
        manifest=_manifest(),
        trades_fetch_plan=_fetch_plan("trades"),
        mbp1_fetch_plan=_fetch_plan("mbp-1"),
        mbp10_fetch_plan=_fetch_plan("mbp-10"),
        trades_diag=_diag(),
        mbp1_diag=_diag(),
        mbp10_diag=_diag(),
        coverage={"audit_rows": []},
        limit_recon={
            "synthesis": {
                "limit_rows_audited": 1,
                "broker_actual_r_rows": 0,
                "counterfactual_m1_tp_rows": 1,
            }
        },
        nas_readiness={"readiness_gates": {"failed": []}, "label_counts": {}},
    )

    action = payload["collection_actions"][1]
    assert action["action_id"] == "A2_XAUUSD_LIMIT_INTENT_TELEMETRY"
    assert action["current_evidence"]["limit_rows_audited"] == 1
    assert action["current_evidence"]["broker_actual_r_rows"] == 0
    assert action["current_evidence"]["counterfactual_m1_tp_rows"] == 1


def test_summarize_feature_diag_counts_primary_candidate_labels():
    summary = mod.summarize_feature_diag(_diag())

    assert summary["primary_ok_rows"] == 2
    assert summary["candidate_rows"] == 1
    assert summary["context_rows"] == 1
    assert summary["candidate_synthetic_winners"] == 0
    assert summary["candidate_synthetic_losers"] == 1


def test_default_inputs_use_proxy_expanded_artifacts():
    assert "PROXY_EXPANDED" in mod.DEFAULT_MANIFEST
    assert "PROXY_EXPANDED" in mod.DEFAULT_TRADES_FETCH_PLAN
    assert "PROXY_EXPANDED" in mod.DEFAULT_TRADES_DIAG
    assert "PROXY_EXPANDED" in mod.DEFAULT_COVERAGE_AUDIT
