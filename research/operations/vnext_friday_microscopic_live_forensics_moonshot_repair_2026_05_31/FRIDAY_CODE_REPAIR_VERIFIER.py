from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
ROUTE_DIR = ROOT / "research" / "operations" / "vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31"
OUTPUT = ROUTE_DIR / "FRIDAY_CODE_REPAIR_VERIFICATION.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def verify_same_symbol_fail_closed() -> dict:
    from src.components.permissions import _reject_if_same_symbol_vnext_lifecycle_conflict

    class BrokenMT5:
        def get_positions(self, symbol="XAUUSD"):
            raise RuntimeError(f"positions unavailable for {symbol}")

    trade_params = SimpleNamespace(
        gtos_vnext_production_execution_path=True,
        gtos_vnext_dynamic_policy_applied=True,
        gtos_vnext_dynamic_policy_selected="momentum_exhaustion",
        gtos_vnext_execution_policy_id="unit_momentum_policy",
        gtos_vnext_selected_cell_risk_pct=0.25,
    )
    denial = _reject_if_same_symbol_vnext_lifecycle_conflict(
        BrokenMT5(),
        "XAUUSD",
        {"risk": {"risk_per_trade_pct": 0.25}},
        trade_params,
    )
    return {
        "name": "same_symbol_vnext_position_source_error_fails_closed",
        "ok": bool(
            denial is not None
            and denial.reason == "same_symbol_position_source_unavailable_for_vnext_lifecycle_guard"
        ),
        "reason": getattr(denial, "reason", None),
        "details": getattr(denial, "details", None),
    }


def verify_pending_lifecycle_terminal_precedence() -> dict:
    from src.research_infra.pending_limit_lifecycle_audit import (
        build_pending_limit_lifecycle_audit_rows,
    )

    shared = {
        "symbol": "NAS100",
        "broker_symbol": "NDX100",
        "source_symbol": "NDX100",
        "trade_id": "lim_NAS100_2026-05-29_141505",
        "side": "SHORT",
        "candidate_id": "broadorigin_b08a864b1bb511080487d03a",
        "entry_price": 30393.76,
        "stop_loss": 30478.57107142857,
        "take_profit_1": 30139.32,
        "pending_created_time_utc": "2026-05-29T14:15:05.629135+00:00",
        "pending_order_mode": "INTERNAL_CANDLE_POLLED_INTENT",
        "broker_pending_order_created": False,
    }
    rows = build_pending_limit_lifecycle_audit_rows(
        [],
        [
            (
                1,
                {
                    **shared,
                    "checked_candle_time_utc": "2026-05-29T14:29:00+00:00",
                    "created_at_utc": "2026-05-29T14:30:05.003373+00:00",
                    "timestamp_utc": "2026-05-29T14:30:05.003373+00:00",
                    "intent_after_check": "still_pending_no_trigger",
                    "broker_fill_state": "not_filled",
                    "fill_no_fill_label": "no_fill_still_pending",
                    "order_send_attempted": False,
                    "order_send_success": False,
                },
            ),
            (
                2,
                {
                    **shared,
                    "checked_candle_time_utc": "2026-05-29T14:15:00+00:00",
                    "created_at_utc": "2026-05-29T14:30:06.151361+00:00",
                    "timestamp_utc": "2026-05-29T14:30:06.151361+00:00",
                    "fill_time_utc": "2026-05-29T14:30:06.151322+00:00",
                    "intent_after_check": "order_send_success_filled",
                    "broker_fill_state": "filled",
                    "fill_no_fill_label": "internal_filled_broker_ticket_known",
                    "order_send_attempted": True,
                    "order_send_success": True,
                    "trade_state_ticket": 241948220,
                },
            ),
        ],
        generated_at_utc="2026-05-31T00:00:00+00:00",
    )
    row = rows[0] if rows else {}
    return {
        "name": "pending_lifecycle_fill_event_wins_over_stale_checked_candle",
        "ok": bool(row.get("final_state") == "BROKER_FILLED_AWAITING_EXIT_OR_ACCOUNT_TRUTH"),
        "final_state": row.get("final_state"),
        "latest_lifecycle_intent_after_check": row.get("latest_lifecycle_intent_after_check"),
    }


def verify_close_net_r_fields() -> dict:
    from src.components.slippage_shadow_logger import record_close_slippage

    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / "slippage.jsonl"
        record_close_slippage(
            ticket=123,
            symbol="XAUUSD",
            direction="LONG",
            requested_price=2650.0,
            fill_price=2649.9,
            close_reason="manual",
            entry_price=2640.0,
            stop_loss=2630.0,
            sl_distance=10.0,
            commission=-0.7,
            swap=0.0,
            broker_profit=100.0,
            cash_risk_amount=200.0,
            log_path=str(log_path),
        )
        row = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
    return {
        "name": "close_slippage_net_broker_r_fields",
        "ok": bool(
            row.get("broker_net_r_status") == "CAPTURED"
            and row.get("broker_net_r") == 0.4965
            and row.get("gross_close_r_multiple") == 0.99
        ),
        "broker_net_r": row.get("broker_net_r"),
        "gross_close_r_multiple": row.get("gross_close_r_multiple"),
        "cost_adjustment_r": row.get("cost_adjustment_r"),
        "broker_net_r_status": row.get("broker_net_r_status"),
    }


def verify_broker_actual_net_r_fields() -> dict:
    from src.research_infra.broker_actual_r_audit import build_broker_actual_r_audit_rows

    rows = build_broker_actual_r_audit_rows(
        [],
        [(1, {"symbol": "NAS100", "ts": "2026-04-29T15:15:05+00:00", "ticket": 234, "fill_price": 27100.36})],
        [
            (
                1,
                {
                    "fill_id": "NAS100_2026-04-29_ny_1500",
                    "instrument": "NAS100",
                    "entry_time": "2026-04-29T15:15:05+00:00",
                    "cash_risk_amount": 100.0,
                    "actual_close": {
                        "exit_time": "2026-04-29T20:15:06+00:00",
                        "exit_reason": "sl_hit",
                        "realized_R": -1.0167,
                        "broker_deal_reconciled": True,
                    },
                },
            )
        ],
        [
            (
                1,
                {
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
        generated_at_utc="2026-05-31T00:00:00+00:00",
    )
    row = rows[0] if rows else {}
    return {
        "name": "broker_actual_r_audit_net_fields",
        "ok": bool(row.get("broker_net_r_status") == "CAPTURED" and row.get("broker_net_r") == -1.007),
        "broker_net_r": row.get("broker_net_r"),
        "broker_net_profit": row.get("broker_net_profit"),
        "broker_net_r_status": row.get("broker_net_r_status"),
    }


def run() -> dict:
    checks = [
        verify_same_symbol_fail_closed(),
        verify_pending_lifecycle_terminal_precedence(),
        verify_close_net_r_fields(),
        verify_broker_actual_net_r_fields(),
    ]
    issues = [check for check in checks if not check.get("ok")]
    return {
        "schema_version": "friday_code_repair_verification_v1",
        "ok": not issues,
        "issue_count": len(issues),
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.write:
        OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
