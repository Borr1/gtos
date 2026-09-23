from __future__ import annotations

from src.research_infra.account_pnl_truth_reconciler import (
    ACCOUNT_HISTORY_PROFIT,
    ACCOUNT_HISTORY_REALIZED_R,
    LOCAL_RISK_DOLLAR_PROJECTION,
    build_account_pnl_truth_rows,
    build_rolling_status,
)


def test_daily_pnl_history_gets_account_history_classes_when_joined():
    rows = build_account_pnl_truth_rows(
        daily_pnl_state=None,
        daily_pnl_history_rows=[
            (
                1,
                {
                    "ts_utc": "2026-05-01T14:01:05+00:00",
                    "symbol": "XAUUSD",
                    "trade_id": "XAUUSD_2026-05-01_london_0815",
                    "result_r": -0.7395,
                    "realized_usd": -739.49,
                    "risk_dollars": 1000.0,
                },
            )
        ],
        broker_actual_r_rows=[
            (
                1,
                {
                    "row_key": "broker1",
                    "trade_id": "XAUUSD_2026-05-01_london_0815",
                    "accounting_evidence_class": "ACCOUNT_HISTORY_REALIZED",
                    "broker_actual_r": -0.7395,
                    "source_links": {"mt5_export_deal_id": 219581847},
                },
            )
        ],
        mt5_deal_rows=[
            (
                1,
                {
                    "ticket": 219581847,
                    "order": 235113710,
                    "entry": 1,
                    "profit": -9.85,
                    "symbol": "XAUUSD",
                },
            )
        ],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["r_evidence_class"] == ACCOUNT_HISTORY_REALIZED_R
    assert row["dollar_evidence_class"] == ACCOUNT_HISTORY_PROFIT
    assert row["actual_r_claim_allowed"] is True
    assert row["actual_dollar_claim_allowed"] is True
    assert "LOCAL_RISK_DOLLAR_DIFFERS_FROM_BROKER_PROFIT" in row["documented_limitation_codes"]


def test_daily_pnl_history_without_deal_stays_local_projection():
    rows = build_account_pnl_truth_rows(
        daily_pnl_state=None,
        daily_pnl_history_rows=[
            (
                1,
                {
                    "symbol": "GBPJPY",
                    "trade_id": "t1",
                    "result_r": 1.0,
                    "realized_usd": 1000.0,
                    "r_evidence_class": "LOCAL_NOTIFICATION_R_INPUT",
                    "dollar_evidence_class": "LOCAL_RISK_DOLLAR_PROJECTION",
                },
            )
        ],
        broker_actual_r_rows=[],
        mt5_deal_rows=[],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["dollar_evidence_class"] == LOCAL_RISK_DOLLAR_PROJECTION
    assert row["actual_r_claim_allowed"] is False
    assert row["actual_dollar_claim_allowed"] is False
    assert "LEGACY_SOURCE_ROW_MISSING_NATIVE_EVIDENCE_CLASS_BACKFILLED_HERE" not in row["documented_limitation_codes"]


def test_rolling_status_counts_claim_boundaries():
    rows = build_account_pnl_truth_rows(
        daily_pnl_state={"date": "2026-05-01", "trades": [], "total_r": -1.0, "total_usd": -1000.0},
        daily_pnl_history_rows=[],
        broker_actual_r_rows=[],
        mt5_deal_rows=[(1, {"ticket": 1, "order": 2, "entry": 1, "profit": -1.5})],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    status = build_rolling_status(rows)

    assert status["reconciliation_rows"] == 2
    assert status["actual_r_claim_allowed_rows"] == 0
    assert status["actual_dollar_claim_allowed_rows"] == 1
