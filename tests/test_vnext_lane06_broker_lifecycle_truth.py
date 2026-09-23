from __future__ import annotations

from datetime import datetime, timezone

from scripts import build_vnext_lane06_broker_lifecycle_truth as lane06
from scripts.verify_vnext_lane06_broker_lifecycle_truth import verify_route


def _sources():
    return {
        "friday_broker": [],
        "friday_placed": [
            {
                "ticket": 241948220,
                "symbol": "NAS100",
                "broker_symbol": "NDX100",
                "trade_id": "NAS100_2026-05-29_ny_1415",
                "candidate_id": "broadorigin_b08a864b1bb511080487d03a",
                "side": "SHORT",
                "selected_policy": "partial_be_runner",
                "execution_policy_id": "vnext_exec_partial_50_at_1r_be_runner_to_3r",
                "friday_lifecycle_status": "filled_partial_exit_residual_open_at_friday_close",
            },
            {
                "ticket": 241779188,
                "symbol": "NAS100",
                "broker_symbol": "NDX100",
                "trade_id": "NAS100_2026-05-29_moonshot_h06_07_0615",
                "candidate_id": "broadorigin_7a6daacd94f848e651899530",
                "side": "LONG",
                "selected_policy": "partial_be_runner",
                "execution_policy_id": "vnext_exec_partial_50_at_1r_be_runner_to_3r",
                "friday_lifecycle_status": "filled_partial_exit_residual_open_at_friday_close",
            },
        ],
        "friday_open_residual": [],
        "friday_manual": [],
        "slippage": [
            {
                "ticket": 241948220,
                "symbol": "NAS100",
                "slippage_event_type": "entry",
                "executed_entry_price": 30349.12,
                "executed_stop_price": 30478.57107142857,
                "executed_lot_size": 0.19,
            },
            {
                "ticket": 241779188,
                "symbol": "NAS100",
                "slippage_event_type": "entry",
                "executed_entry_price": 30255.07,
                "executed_stop_price": 30139.003142857142,
                "executed_lot_size": 0.21,
            },
        ],
        "pending": [
            {
                "trade_state_ticket": 241948220,
                "order_result_retcode": 10009,
                "order_send_success": True,
            }
        ],
        "daily_pnl": [
            {
                "ts_utc": "2026-05-31T02:59:05.243093+00:00",
                "symbol": "NAS100",
                "trade_id": "NAS100_2026-05-29_moonshot_h06_07_0615",
                "result_r": 0.4814,
                "realized_usd": 120.34,
                "actual_r_claim_allowed": False,
                "account_truth_status": "NOT_ACCOUNT_HISTORY_RECONCILED_AT_NOTIFICATION_TIME",
                "exit_type": "broker_closed",
            }
        ],
        "notification_queue": [
            {
                "alert_id": "8897c9f64b2a7563",
                "ts_utc": "2026-05-31T02:59:05.255776+00:00",
                "message": "WIN - NAS100 +0.48R\nExit: broker_closed\nLifecycle: broker_closed",
            }
        ],
    }


def _snapshot():
    return {
        "schema_version": "lane06_mt5_readonly_snapshot_v1",
        "read_only_check": "passed",
        "history_deal_details": [
            {
                "ticket": 225786309,
                "position_id": 241948220,
                "entry": 0,
                "type": 1,
                "symbol": "NDX100",
                "price": 30348.47,
                "volume": 0.19,
                "profit": 0.0,
                "commission": 0.0,
                "swap": 0.0,
                "fee": 0.0,
                "order": 241948220,
                "magic": 20260401,
            },
            {
                "ticket": 225794373,
                "position_id": 241948220,
                "entry": 1,
                "reason": 3,
                "symbol": "NDX100",
                "price": 30214.11,
                "volume": 0.1,
                "profit": 134.36,
                "commission": 0.0,
                "swap": 0.0,
                "fee": 0.0,
                "order": 241956697,
                "magic": 20260401,
            },
            {
                "ticket": 225795604,
                "position_id": 241948220,
                "entry": 1,
                "reason": 1,
                "symbol": "NDX100",
                "price": 30251.58,
                "volume": 0.09,
                "profit": 87.2,
                "commission": 0.0,
                "swap": 0.0,
                "fee": 0.0,
                "order": 241958000,
                "magic": 20260401,
            },
            {
                "ticket": 225628115,
                "position_id": 241779188,
                "entry": 0,
                "type": 0,
                "symbol": "NDX100",
                "price": 30255.17,
                "volume": 0.21,
                "profit": 0.0,
                "commission": 0.0,
                "swap": 0.0,
                "fee": 0.0,
                "order": 241779188,
                "magic": 20260401,
            },
            {
                "ticket": 225755854,
                "position_id": 241779188,
                "entry": 1,
                "reason": 3,
                "symbol": "NDX100",
                "price": 30374.76,
                "volume": 0.1,
                "profit": 119.59,
                "commission": 0.0,
                "swap": 0.0,
                "fee": 0.0,
                "order": 241900000,
                "magic": 20260401,
            },
        ],
        "history_order_details": [],
        "order_details": [],
        "position_details": [
            {
                "ticket": 241779188,
                "symbol": "NDX100",
                "volume": 0.11,
                "price_open": 30255.17,
                "profit": 40.0,
                "swap": 0.0,
                "magic": 20260401,
            }
        ],
        "symbol_info": {
            "NDX100": {"trade_contract_size": 10.0},
            "NAS100": {"trade_contract_size": 10.0},
        },
    }


def test_manual_residual_close_and_broker_net_r_are_captured():
    artifacts = lane06.build_artifacts(
        _snapshot(),
        _sources(),
        datetime(2026, 5, 31, tzinfo=timezone.utc),
        write=False,
    )

    lifecycle = {row["ticket"]: row for row in artifacts["lifecycle"]}
    cost = {row["ticket"]: row for row in artifacts["cost"]}
    manual = artifacts["manual"]

    assert lifecycle[241948220]["broker_lifecycle_status"] == (
        "PARTIAL_AND_RESIDUAL_CLOSED_BROKER_HISTORY"
    )
    assert lifecycle[241948220]["manual_or_client_deal_tickets"] == [225795604]
    assert cost[241948220]["initial_cash_risk_status"] == (
        "CAPTURED_FROM_BROKER_ENTRY_AND_LOCAL_STOP_GEOMETRY"
    )
    assert cost[241948220]["broker_final_net_r_status"] == "CAPTURED"
    assert cost[241948220]["broker_realized_net_r"] > 0
    assert any(row.get("deal_ticket") == 225795604 for row in manual)


def test_open_broker_position_contradicts_local_broker_closed_notification():
    artifacts = lane06.build_artifacts(
        _snapshot(),
        _sources(),
        datetime(2026, 5, 31, tzinfo=timezone.utc),
        write=False,
    )

    projected = artifacts["projected"]
    telegram = artifacts["telegram"]
    cost = {row["ticket"]: row for row in artifacts["cost"]}

    assert cost[241779188]["broker_final_net_r_status"] == (
        "OPEN_RESIDUAL_FINAL_NET_R_PENDING_BROKER_CLOSE"
    )
    assert any(
        row.get("ticket") == 241779188
        and row.get("reconciliation_status")
        == "BROKER_CONTRADICTION_OPEN_POSITION_FALSE_CLOSE_NOTIFICATION"
        for row in projected
    )
    assert any(
        row.get("ticket") == 241779188
        and row.get("parity_status") == "FALSE_CLOSE_TELEGRAM_SENT"
        for row in telegram
    )


def test_verifier_reports_missing_route_outputs(tmp_path):
    result = verify_route(tmp_path)
    assert result["ok"] is False
    assert any(issue.startswith("missing_output:") for issue in result["issues"])
