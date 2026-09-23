from __future__ import annotations

import build_vps_supervisor_artifacts as builder
from verify_vps_supervisor_artifacts import verify_route


def test_vps_supervisor_artifacts_verify() -> None:
    result = verify_route(write_result=False)
    assert result["ok"], result["issues"]


def test_nas100_residual_status_ignores_distinct_current_position(monkeypatch) -> None:
    monkeypatch.setattr(
        builder,
        "nas100_broker_close_resolution",
        lambda: {
            "status": "resolved_broker_closed_deal_reconciled",
            "resolved": True,
            "ticket": "241779188",
        },
    )
    checkpoint = {
        "broker_lifecycle": {
            "open_positions": [
                {
                    "symbol": "NDX100",
                    "ticket": 242342001,
                    "identifier": 242342001,
                    "magic": 20260401,
                    "type": 0,
                    "volume": 0.21,
                    "price_open": 30612.68,
                    "price_current": 30590.87,
                    "sl": 30495.86,
                    "tp": 30962.45,
                }
            ]
        }
    }

    status = builder.nas100_residual_sltp_status(checkpoint)

    assert status["resolved"] is True
    assert status["ticket"] == "241779188"
    assert status["current_distinct_open_positions"][0]["ticket"] == "242342001"
    assert "distinct ticket" in status["broker_lifecycle_effect"]
