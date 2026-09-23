from __future__ import annotations

from collections import namedtuple
from pathlib import Path

from scripts import export_mt5_account_history_readonly as exporter
from src.research_infra.broker_actual_r_audit import (
    ACCOUNT_HISTORY_REALIZED,
    ACTION_REQUIRED,
    COMPLETE_WITH_LIMITATIONS,
    LIVE_R_ARTIFACT,
    build_broker_actual_r_audit_rows,
    build_rolling_status,
)


def _account_row(**overrides):
    row = {
        "schema_version": "account_truth_reconciliation_status_v1",
        "row_key": "acct1",
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "account_truth_status": "NO_REALIZED_ACCOUNT_HISTORY_FOR_CANDIDATE_OR_NOT_QUERIED_IN_CLOSURE",
        "truth_lane": "ACCOUNT_HISTORY_REQUIRED_FOR_DOLLAR_OR_ACTUAL_R_CLAIMS",
        "actual_r_claim_allowed": False,
        "manual_backfill_status": "SOURCE_BLOCKED",
    }
    row.update(overrides)
    return row


def _j46_row(**overrides):
    row = {
        "fill_id": "NAS100_2026-04-29_ny_1500",
        "instrument": "NAS100",
        "direction": "LONG",
        "entry_time": "2026-04-29T15:15:05+00:00",
        "entry_price": 27100.36,
        "actual_close": {
            "exit_time": "2026-04-29T20:15:06+00:00",
            "exit_reason": "sl_hit",
            "realized_R": -1.0167,
            "broker_deal_reconciled": True,
        },
    }
    row.update(overrides)
    return row


def test_broker_actual_r_audit_separates_account_history_from_source_blocked_candidate():
    rows = build_broker_actual_r_audit_rows(
        [(1, _account_row())],
        [],
        [],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["broker_actual_r_audit_status"] == COMPLETE_WITH_LIMITATIONS
    assert row["accounting_evidence_class"] == LIVE_R_ARTIFACT
    assert row["actual_r_claim_allowed"] is False
    assert row["broker_actual_r"] is None
    assert "CANONICAL_ACCOUNT_HISTORY_EXPORT_MISSING" in row["documented_limitation_codes"]


def test_broker_actual_r_audit_allows_broker_reconciled_filled_trade_only():
    rows = build_broker_actual_r_audit_rows(
        [],
        [(1, {"symbol": "NAS100", "ts": "2026-04-29T15:15:05+00:00", "ticket": 234, "fill_price": 0.0})],
        [(1, _j46_row())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["accounting_evidence_class"] == ACCOUNT_HISTORY_REALIZED
    assert row["actual_r_claim_allowed"] is True
    assert row["broker_actual_r"] == -1.0167
    assert row["entry_slippage_status"] == "ENTRY_SLIPPAGE_ROW_BROKER_ZERO_FILL_PRICE_RECORDED_NOT_USED_AS_ACTUAL_FILL"


def test_broker_actual_r_audit_joins_mt5_account_history_export():
    rows = build_broker_actual_r_audit_rows(
        [],
        [(1, {"symbol": "NAS100", "ts": "2026-04-29T15:15:05+00:00", "ticket": 234, "fill_price": 27100.36})],
        [(1, _j46_row(cash_risk_amount=100.0))],
        [
            (
                1,
                {
                    "schema_version": "mt5_account_history_deal_export_v1",
                    "ticket": 9001,
                    "order": 8001,
                    "position_id": 234,
                    "entry": 1,
                    "symbol": "NAS100",
                    "time_utc": "2026-04-29T20:15:06+00:00",
                    "profit": -100.0,
                    "commission": -0.7,
                    "swap": 0.0,
                    "reason": 4,
                },
            )
        ],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["accounting_evidence_class"] == ACCOUNT_HISTORY_REALIZED
    assert row["commission_status"] == "COMMISSION_CAPTURED"
    assert row["swap_status"] == "SWAP_CAPTURED"
    assert row["source_links"]["mt5_export_deal_joined"] is True
    assert row["source_links"]["mt5_export_deal_id"] == 9001
    assert row["manual_backfill_status"] == "BACKFILLED_OR_REFRESHED_FROM_MT5_ACCOUNT_HISTORY_EXPORT"
    assert row["broker_profit"] == -100.0
    assert row["broker_commission"] == -0.7
    assert row["broker_swap"] == 0.0
    assert row["cash_risk_amount"] == 100.0
    assert row["broker_net_profit"] == -100.7
    assert row["broker_net_r"] == -1.007
    assert row["broker_net_r_status"] == "CAPTURED"


def test_mt5_export_join_promotes_legacy_false_broker_reconciled_flag():
    rows = build_broker_actual_r_audit_rows(
        [],
        [(1, {"symbol": "XAUUSD", "ts": "2026-05-01T14:00:05+00:00", "ticket": 235112399, "fill_price": 0.0})],
        [
            (
                1,
                _j46_row(
                    fill_id="XAUUSD_2026-05-01_london_0815",
                    instrument="XAUUSD",
                    entry_time="2026-05-01T14:00:05+00:00",
                    actual_close={
                        "exit_time": "2026-05-01T17:00:39+00:00",
                        "exit_reason": "sl_hit",
                        "realized_R": -0.7395,
                        "broker_deal_reconciled": False,
                    },
                ),
            )
        ],
        [
            (
                1,
                {
                    "ticket": 219581847,
                    "order": 235113710,
                    "position_id": 235112399,
                    "entry": 1,
                    "symbol": "XAUUSD",
                    "time_utc": "2026-05-01T17:00:39+00:00",
                    "profit": -9.85,
                    "commission": 0.0,
                    "swap": 0.0,
                    "reason": 4,
                },
            )
        ],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["accounting_evidence_class"] == ACCOUNT_HISTORY_REALIZED
    assert row["actual_r_claim_allowed"] is True
    assert row["broker_actual_r"] == -0.7395
    assert row["account_truth_status"] == "MT5_ACCOUNT_HISTORY_EXPORT_JOINED"
    assert "LEGACY_ROW_BROKER_DEAL_RECONCILED_FLAG_FALSE_BUT_MT5_EXPORT_JOINED" in row["documented_limitation_codes"]


def test_broker_actual_r_audit_flags_missing_realized_r_when_broker_reconciled():
    rows = build_broker_actual_r_audit_rows(
        [],
        [],
        [(1, _j46_row(actual_close={"broker_deal_reconciled": True}))],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert rows[0]["broker_actual_r_audit_status"] == ACTION_REQUIRED
    assert "BROKER_RECONCILED_FILL_MISSING_REALIZED_R" in rows[0]["action_required_codes"]


def test_broker_actual_r_rolling_status_counts_evidence_classes():
    rows = build_broker_actual_r_audit_rows(
        [(1, _account_row())],
        [],
        [(1, _j46_row())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    rolling = build_rolling_status(rows)

    assert rolling["audit_rows"] == 2
    assert rolling["accounting_evidence_class_counts"][ACCOUNT_HISTORY_REALIZED] == 1
    assert rolling["accounting_evidence_class_counts"][LIVE_R_ARTIFACT] == 1


def test_readonly_exporter_dry_run_and_normalize_deal():
    plan = exporter.build_query_plan(
        start=exporter.parse_day("2026-05-01"),
        end=exporter.parse_day("2026-05-05", end=True),
        symbol="XAUUSD",
        position_id=235112399,
        output=Path("out.jsonl"),
    )
    assert plan["read_only"] is True
    assert plan["no_order_calls"] is True
    assert plan["position_id_filter"] == 235112399

    Deal = namedtuple("Deal", "ticket time symbol profit commission swap")
    normalized = exporter.normalize_deal(Deal(1, 1777939200, "XAUUSD", 10.0, -0.5, 0.0))
    assert normalized["schema_version"] == "mt5_account_history_deal_export_v1"
    assert normalized["read_only_export"] is True
    assert normalized["time_utc"].endswith("+00:00")
