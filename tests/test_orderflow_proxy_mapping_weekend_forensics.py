from __future__ import annotations

from scripts import analyze_orderflow_proxy_mapping_weekend_forensics as mod


def _window(window_id: str, corr: float, shift: int, trades: int = 100, volume: int = 1000, beta: float = 0.8) -> dict:
    return {
        "window_id": window_id,
        "selected_shift_minutes": shift,
        "selected_diagnostics": [
            {
                "zero_lag_return_corr": corr,
                "directional_agreement": 0.93,
                "best_lag_minutes": 0,
                "best_lag_corr": corr,
                "aligned_minutes": 590,
                "futures_minutes": 590,
                "mt5_minutes": 600,
                "futures_trade_count_sum": trades,
                "futures_volume_sum": volume,
                "beta_mt5_per_futures": beta,
            }
        ],
    }


def _audit(weak_id: str) -> dict:
    return {
        "decision_readout": {"weak_windows": [weak_id]},
        "window_audit": [
            {
                "window_id": weak_id,
                "expected_shift_minutes": -180,
                "shift_policy_passed": True,
                "corr_gate_passed": False,
                "directional_gate_passed": True,
                "best_lag_gate_passed": True,
            }
        ],
    }


def test_weak_window_forensics_separates_timestamp_from_basis_noise():
    validation = {
        "windows": [
            _window("2026-04-24T07:00_2026-04-24T16:59", 0.90, -180, trades=200, volume=2000, beta=0.9),
            _window("2026-04-27T07:00_2026-04-27T16:59", 0.825, -180, trades=100, volume=1000, beta=0.75),
        ]
    }

    out = mod.weak_window_forensics(validation, _audit("2026-04-27T07:00_2026-04-27T16:59"))

    weak = out["weak_windows"][0]
    assert weak["shift_policy_passed"] is True
    assert weak["best_lag_minutes"] == 0
    assert out["cause_readout"]["timestamp_specific"] == "unlikely_from_artifacts"
    assert out["cause_readout"]["basis_specific"] == "plausible_not_proven"


def test_next_unresolved_symbol_prefers_usdjpy_transfer_followup():
    proxy_expansion = {"decision_readout": {"usdjpy_mapping_status": "TRANSFER_REVIEW_REQUIRED"}}
    priority = {
        "priority_queue": [
            {"symbol": "USDJPY", "current_candidate_rows": 34},
            {"symbol": "GBPJPY", "current_candidate_rows": 23},
        ]
    }

    out = mod.next_unresolved_symbol(proxy_expansion, priority)

    assert out["next_symbol"] == "USDJPY"
    assert out["next_lane"] == "registered_price_transfer_followup_only"
    assert out["usdjpy_candidate_rows"] == 34


def test_gbpjpy_stays_blocked_until_leg_and_two_book_protocols_exist():
    proxy_expansion = {
        "pair_audit": [
            {"pair": "6B.v.0->GBPUSD:direct", "status": "STRICT_TRANSFER_PASS"},
            {"pair": "6J.v.0->USDJPY:inverse_return", "status": "TRANSFER_REVIEW_REQUIRED"},
        ]
    }
    priority = {"priority_queue": [{"symbol": "GBPJPY", "current_candidate_rows": 23}]}

    out = mod.gbpjpy_feasibility(proxy_expansion, priority)

    assert out["price_transfer_feasibility"] == "CONCEPTUALLY_FEASIBLE_AFTER_LEG_VALIDATION"
    assert out["orderflow_depth_feasibility"] == "STAY_BLOCKED_TWO_BOOK_SEMANTICS"
    assert out["verdict"] == "DO_NOT_REGISTER_ORDERFLOW_MAPPING_YET"


def test_build_payload_preserves_no_activation_verdicts():
    validation = {"windows": [_window("2026-04-27T07:00_2026-04-27T16:59", 0.825, -180)]}
    payload = mod.build_payload(
        usdjpy_validation=validation,
        usdjpy_audit=_audit("2026-04-27T07:00_2026-04-27T16:59"),
        proxy_expansion={
            "decision_readout": {"usdjpy_mapping_status": "TRANSFER_REVIEW_REQUIRED"},
            "pair_audit": [],
        },
        priority_audit={"priority_queue": [{"symbol": "USDJPY", "current_candidate_rows": 34}]},
    )

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["registration_verdict"] == "NO_PROXY_MAP_ACTIVATION"
    assert payload["inputs"]["data_policy"] == "cached_artifacts_only_no_databento_fetch"
