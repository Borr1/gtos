"""Tests for the Q71 Slippage Shadow Logger.

Closes the data gap identified by Q71 (zero usable fill records across
160 trade_records, 7 yaml backups, 49 fn_smoke fills) by validating:

Unit:
    - JSONL schema integrity (every required field, exact types)
    - Pip conversion is correct for XAU, JPY, FX-major, indices
    - Pip is null for unknown symbols (no silent fabrication)
    - Slippage sign convention (LONG: +ve = adverse fill above ask;
      SHORT: +ve = adverse fill below bid)
    - Spread null when unavailable
    - Append-only behaviour (multiple writes accumulate)
    - Parent directory auto-created

Integration:
    - ExecutionEngine.open_trade emits exactly ONE log line on a
      mocked successful fill, with correct field plumbing.
    - The wire-in passes through kill_zone + trigger from kwargs.
    - LIMIT-fill path tags trigger="limit_fill" automatically.

Error path / fail-open contract:
    - Spread call returning None still produces a complete log entry
      (spread_at_request=null).
    - A logger write failure (mocked write exception) does NOT
      propagate -- open_trade still returns the TradeState.
    - Unknown direction logs raw delta but null directional view.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.components.slippage_shadow_logger import (
    SHADOW_LOG_PATH,
    _append_path,
    _resolve_pip_size,
    record_close_slippage,
    record_slippage,
)


# =============================================================================
# Unit tests -- record_slippage in isolation
# =============================================================================


class TestSchemaIntegrity:
    """Every required field is present and correctly typed."""

    REQUIRED_FIELDS = (
        "ts", "ticket", "symbol", "direction",
        "requested_price", "fill_price",
        "slippage_price", "slippage_directional", "slippage_pips",
        "spread_at_request", "kill_zone", "trigger", "notes",
    )

    def test_all_required_fields_present(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        record_slippage(
            ticket=12345, symbol="XAUUSD", direction="LONG",
            requested_price=2650.00, fill_price=2650.10,
            spread_at_request=18.0, kill_zone="london",
            trigger="candidate_market", log_path=log_path,
        )
        with open(log_path) as f:
            entry = json.loads(f.readline())
        for field in self.REQUIRED_FIELDS:
            assert field in entry, f"Missing field: {field}"

    def test_ts_is_iso8601_with_timezone(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        record_slippage(
            ticket=1, symbol="XAUUSD", direction="LONG",
            requested_price=2650.0, fill_price=2650.0,
            log_path=log_path,
        )
        entry = json.loads(Path(log_path).read_text().splitlines()[0])
        # ISO-8601 with offset (e.g. ...+00:00 or Z). datetime.isoformat()
        # of a tz-aware datetime always includes a colon-separated offset.
        assert "T" in entry["ts"]
        assert entry["ts"].endswith("+00:00") or entry["ts"].endswith("Z")

    def test_ticket_is_int(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        record_slippage(
            ticket=99, symbol="XAUUSD", direction="LONG",
            requested_price=1.0, fill_price=1.0, log_path=log_path,
        )
        entry = json.loads(Path(log_path).read_text().splitlines()[0])
        assert isinstance(entry["ticket"], int)
        assert entry["ticket"] == 99

    def test_lfs_pointer_destination_redirects_to_runtime_log(self, tmp_path):
        pointer_path = tmp_path / "slippage.jsonl"
        pointer_path.write_text(
            "version https://git-lfs.github.com/spec/v1\n"
            "oid sha256:abc\n"
            "size 123\n",
            encoding="utf-8",
        )

        record_slippage(
            ticket=99, symbol="XAUUSD", direction="LONG",
            requested_price=1.0, fill_price=1.0, log_path=str(pointer_path),
        )

        runtime_path = tmp_path / "slippage_runtime.jsonl"
        assert _append_path(pointer_path) == runtime_path
        assert pointer_path.read_text(encoding="utf-8").startswith("version https://git-lfs.github.com/spec/v1")
        rows = [json.loads(line) for line in runtime_path.read_text(encoding="utf-8").splitlines()]
        assert rows[0]["ticket"] == 99

    def test_source_repair_geometry_fields_are_schema_stable(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        record_slippage(
            ticket=99,
            deal_ticket=1001,
            symbol="XAUUSD",
            direction="LONG",
            requested_price=2650.0,
            fill_price=2650.1,
            broker_fill_time_utc="2026-05-18T00:00:00Z",
            executed_entry_price=2650.1,
            executed_stop_price=2640.0,
            executed_target_price=2670.0,
            executed_lot_size=0.1,
            log_path=log_path,
        )
        entry = json.loads(Path(log_path).read_text().splitlines()[0])
        assert entry["source_repair_geometry_contract_version"] == "numeric_router_source_repair_geometry_v1"
        assert entry["slippage_schema_version"] == "entry_slippage_shadow_v3"
        assert entry["order_ticket"] == 99
        assert entry["deal_ticket"] == 1001
        assert entry["broker_fill_time_utc"] == "2026-05-18T00:00:00+00:00"
        assert entry["executed_entry_price"] == pytest.approx(2650.1)
        assert entry["executed_stop_price"] == pytest.approx(2640.0)
        assert entry["executed_target_price"] == pytest.approx(2670.0)
        assert entry["executed_lot_size"] == pytest.approx(0.1)
        assert entry["executed_exit_price"] is None
        assert entry["commission_status"] == "ACCOUNT_HISTORY_REQUIRED"
        assert entry["swap_status"] == "ACCOUNT_HISTORY_REQUIRED"
        assert entry["partial_exit_lifecycle"] == "ENTRY_FULL_POSITION_OPENED"
        assert entry["source_repair_row_identity_status"] == "NOT_BOUND_TO_NUMERIC_ROUTER_SOURCE_REPAIR_QUEUE"
        assert entry["source_repair_identity_key"] is None

    def test_entry_deal_zero_is_not_captured(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        record_slippage(
            ticket=99,
            deal_ticket=0,
            symbol="XAUUSD",
            direction="LONG",
            requested_price=2650.0,
            fill_price=2650.1,
            log_path=log_path,
        )

        entry = json.loads(Path(log_path).read_text().splitlines()[0])
        assert entry["deal_ticket"] is None
        assert entry["deal_ticket_status"] == "SOURCE_NOT_CAPTURED"

    def test_stage03_cost_fill_lifecycle_fields_are_captured(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        record_slippage(
            ticket=99,
            symbol="GER40",
            direction="LONG",
            requested_price=25240.0,
            fill_price=25240.2,
            spread_at_request=200,
            decision_spread=180,
            decision_spread_unit="points",
            order_send_spread=200,
            fill_spread=210,
            order_send_time_utc="2026-05-27T05:00:00+00:00",
            order_result_time_utc="2026-05-27T05:00:01+00:00",
            reject_or_fill_latency_ms=1000,
            pending_age_seconds=450,
            pending_candles_elapsed=3,
            sl_distance=6.0,
            order_outcome_status="ORDER_FILLED",
            dynamic_policy="be_after_trigger",
            dynamic_exit_action_timeline={"stage": "entry_order_fill"},
            log_path=log_path,
        )

        entry = json.loads(Path(log_path).read_text().splitlines()[0])
        assert entry["decision_spread"] == 180
        assert entry["order_send_spread"] == 200
        assert entry["fill_spread"] == 210
        assert entry["reject_or_fill_latency_ms"] == 1000
        assert entry["pending_age_seconds"] == 450
        assert entry["pending_candles_elapsed"] == 3
        assert entry["slippage_r"] == pytest.approx(0.033333)
        assert entry["order_outcome_status"] == "ORDER_FILLED"
        assert entry["dynamic_policy"] == "be_after_trigger"
        assert entry["dynamic_exit_action_timeline"] == {"stage": "entry_order_fill"}

    def test_account_history_unresolved_status_requires_attempt_metadata(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        record_slippage(
            ticket=99,
            deal_ticket=1001,
            symbol="XAUUSD",
            direction="LONG",
            requested_price=2650.0,
            fill_price=2650.0,
            account_history_lookup_attempted=True,
            account_history_lookup_status="UNRESOLVED_AFTER_HISTORY_ATTEMPT",
            account_history_lookup_window_start_utc="2026-05-27T05:00:00+00:00",
            account_history_lookup_window_end_utc="2026-05-27T05:10:00+00:00",
            account_history_lookup_match_keys={"order": 99, "deal": 1001},
            pretrade_cost_model_status="PASSED",
            pretrade_cost_model={"spread_r": 0.02, "commission_model_status": "verified"},
            log_path=log_path,
        )

        entry = json.loads(Path(log_path).read_text().splitlines()[0])
        assert entry["commission_status"] == "UNRESOLVED_AFTER_HISTORY_ATTEMPT"
        assert entry["swap_status"] == "UNRESOLVED_AFTER_HISTORY_ATTEMPT"
        assert entry["account_history_lookup_attempted"] is True
        assert entry["account_history_lookup_status"] == "UNRESOLVED_AFTER_HISTORY_ATTEMPT"
        assert entry["account_history_lookup_match_keys"] == {"order": 99, "deal": 1001}
        assert entry["pretrade_cost_model_status"] == "PASSED"
        assert entry["pretrade_cost_model"]["spread_r"] == pytest.approx(0.02)

    def test_zero_order_result_price_uses_executed_entry_for_slippage(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        record_slippage(
            ticket=241725208,
            symbol="XAUUSD",
            direction="SHORT",
            requested_price=4489.76,
            fill_price=0.0,
            raw_order_result_fill_price=0.0,
            executed_entry_price=4489.76,
            sl_distance=27.63157142857108,
            order_outcome_status="ORDER_FILLED",
            log_path=log_path,
        )

        entry = json.loads(Path(log_path).read_text().splitlines()[0])
        assert entry["fill_price"] == pytest.approx(4489.76)
        assert entry["raw_order_result_fill_price"] == pytest.approx(0.0)
        assert entry["fill_price_source"] == "executed_entry_price_fallback_for_zero_order_result"
        assert entry["fill_price_status"] == "ZERO_ORDER_RESULT_REPAIRED"
        assert entry["slippage_price"] == pytest.approx(0.0)
        assert entry["slippage_directional"] == pytest.approx(0.0)
        assert entry["slippage_pips"] == pytest.approx(0.0)
        assert entry["slippage_r"] == pytest.approx(0.0)

    def test_source_repair_identity_can_be_bound_prospectively(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        record_slippage(
            ticket=99,
            symbol="XAUUSD",
            direction="LONG",
            requested_price=2650.0,
            fill_price=2650.1,
            source_repair_identity={
                "source_repair_plan_row_id": "PLAN-1",
                "input_numeric_router_catalog_entry_id": "CAT-1",
                "input_numeric_router_family_spec_id": "SPEC-1",
            },
            log_path=log_path,
        )
        entry = json.loads(Path(log_path).read_text().splitlines()[0])
        assert entry["source_repair_plan_row_id"] == "PLAN-1"
        assert entry["input_numeric_router_catalog_entry_id"] == "CAT-1"
        assert entry["input_numeric_router_family_spec_id"] == "SPEC-1"
        assert entry["source_repair_identity_key"] == "PLAN-1|CAT-1|SPEC-1"
        assert entry["source_repair_row_identity_status"] == "BOUND_TO_NUMERIC_ROUTER_SOURCE_REPAIR_QUEUE"


class TestSlippageDirectionLong:
    """LONG: positive slippage_directional = adverse (fill above ask)."""

    def test_long_adverse_fill(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        # Requested 2650.00, filled at 2650.50 (50 cents adverse)
        record_slippage(
            ticket=1, symbol="XAUUSD", direction="LONG",
            requested_price=2650.00, fill_price=2650.50,
            log_path=log_path,
        )
        entry = json.loads(Path(log_path).read_text().splitlines()[0])
        assert entry["slippage_price"] == 0.5
        assert entry["slippage_directional"] == 0.5  # +ve = adverse for LONG
        # Pip size for XAU = 0.01, so 0.5 / 0.01 = 50.0 pips
        assert entry["slippage_pips"] == 50.0

    def test_long_favorable_fill(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        record_slippage(
            ticket=1, symbol="XAUUSD", direction="LONG",
            requested_price=2650.00, fill_price=2649.50,
            log_path=log_path,
        )
        entry = json.loads(Path(log_path).read_text().splitlines()[0])
        assert entry["slippage_price"] == -0.5
        assert entry["slippage_directional"] == -0.5  # -ve = favorable
        assert entry["slippage_pips"] == -50.0

    def test_long_zero_slippage(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        record_slippage(
            ticket=1, symbol="XAUUSD", direction="LONG",
            requested_price=2650.00, fill_price=2650.00,
            log_path=log_path,
        )
        entry = json.loads(Path(log_path).read_text().splitlines()[0])
        assert entry["slippage_price"] == 0.0
        assert entry["slippage_directional"] == 0.0
        assert entry["slippage_pips"] == 0.0


class TestSlippageDirectionShort:
    """SHORT: positive slippage_directional = adverse (fill below bid)."""

    def test_short_adverse_fill(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        # Requested 2650.00, filled at 2649.50 (50 cents adverse for SHORT)
        record_slippage(
            ticket=1, symbol="XAUUSD", direction="SHORT",
            requested_price=2650.00, fill_price=2649.50,
            log_path=log_path,
        )
        entry = json.loads(Path(log_path).read_text().splitlines()[0])
        # Raw price diff is fill - requested = -0.5 (sign-preserving)
        assert entry["slippage_price"] == -0.5
        # Directional = requested - fill = +0.5 (positive = adverse)
        assert entry["slippage_directional"] == 0.5
        assert entry["slippage_pips"] == 50.0

    def test_short_favorable_fill(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        record_slippage(
            ticket=1, symbol="XAUUSD", direction="SHORT",
            requested_price=2650.00, fill_price=2650.50,
            log_path=log_path,
        )
        entry = json.loads(Path(log_path).read_text().splitlines()[0])
        assert entry["slippage_price"] == 0.5
        assert entry["slippage_directional"] == -0.5  # negative = favorable
        assert entry["slippage_pips"] == -50.0


class TestPipResolution:
    """Pip-size lookup table coverage and broker-suffix handling."""

    def test_xau_pip(self):
        assert _resolve_pip_size("XAUUSD") == 0.01

    def test_jpy_pip(self):
        assert _resolve_pip_size("USDJPY") == 0.01
        assert _resolve_pip_size("GBPJPY") == 0.01

    def test_fx_major_pip(self):
        assert _resolve_pip_size("EURUSD") == 0.0001
        assert _resolve_pip_size("GBPUSD") == 0.0001

    def test_index_pip(self):
        assert _resolve_pip_size("US30") == 1.0
        assert _resolve_pip_size("NAS100") == 1.0

    def test_broker_suffix_cash(self):
        # "US30_cash" should resolve to the "US30" entry.
        assert _resolve_pip_size("US30_cash") == 1.0
        assert _resolve_pip_size("US30.cash") == 1.0
        assert _resolve_pip_size("NAS100_cash") == 1.0

    def test_unknown_symbol_returns_none(self):
        assert _resolve_pip_size("NEVERTRADED_SYMBOL") is None
        assert _resolve_pip_size("") is None

    def test_unknown_symbol_pips_field_is_null(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        record_slippage(
            ticket=1, symbol="EXOTIC_PAIR", direction="LONG",
            requested_price=100.0, fill_price=100.5,
            log_path=log_path,
        )
        entry = json.loads(Path(log_path).read_text().splitlines()[0])
        # Raw price diff still recorded
        assert entry["slippage_price"] == 0.5
        assert entry["slippage_directional"] == 0.5
        # But pips is null because we can't convert without a known pip size.
        assert entry["slippage_pips"] is None


class TestUnknownDirection:
    """Unknown direction string: log raw delta but leave directional null."""

    def test_unknown_direction_logs_raw_only(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        record_slippage(
            ticket=1, symbol="XAUUSD", direction="UNKNOWN",
            requested_price=2650.0, fill_price=2650.5,
            log_path=log_path,
        )
        entry = json.loads(Path(log_path).read_text().splitlines()[0])
        assert entry["slippage_price"] == 0.5
        assert entry["slippage_directional"] is None
        assert entry["slippage_pips"] is None  # Can't compute without sign


class TestSpreadCapture:
    """Spread can be present, null, or coerced from string-like values."""

    def test_spread_present(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        record_slippage(
            ticket=1, symbol="XAUUSD", direction="LONG",
            requested_price=2650.0, fill_price=2650.0,
            spread_at_request=22.5, log_path=log_path,
        )
        entry = json.loads(Path(log_path).read_text().splitlines()[0])
        assert entry["spread_at_request"] == 22.5

    def test_spread_none(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        record_slippage(
            ticket=1, symbol="XAUUSD", direction="LONG",
            requested_price=2650.0, fill_price=2650.0,
            spread_at_request=None, log_path=log_path,
        )
        entry = json.loads(Path(log_path).read_text().splitlines()[0])
        assert entry["spread_at_request"] is None

    def test_spread_garbage_input_safely_nulls(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        # Simulate a TickData attribute that returns a non-numeric value
        record_slippage(
            ticket=1, symbol="XAUUSD", direction="LONG",
            requested_price=2650.0, fill_price=2650.0,
            spread_at_request="bad",  # type: ignore[arg-type]
            log_path=log_path,
        )
        entry = json.loads(Path(log_path).read_text().splitlines()[0])
        assert entry["spread_at_request"] is None  # Coerced safely


class TestAppendBehaviour:
    """Multiple writes append; parent dirs created on demand."""

    def test_appends_multiple_lines(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        for i in range(5):
            record_slippage(
                ticket=i, symbol="XAUUSD", direction="LONG",
                requested_price=2650.0, fill_price=2650.0 + i,
                log_path=log_path,
            )
        lines = Path(log_path).read_text().splitlines()
        assert len(lines) == 5
        # Tickets are sequential 0..4
        for i, line in enumerate(lines):
            assert json.loads(line)["ticket"] == i

    def test_creates_parent_directory(self, tmp_path):
        log_path = str(tmp_path / "deep" / "nested" / "slippage.jsonl")
        record_slippage(
            ticket=1, symbol="XAUUSD", direction="LONG",
            requested_price=1.0, fill_price=1.0, log_path=log_path,
        )
        assert Path(log_path).exists()


class TestFailOpenContract:
    """A logger failure must NEVER propagate to the caller."""

    def test_open_failure_is_swallowed(self, tmp_path, monkeypatch):
        log_path = str(tmp_path / "slippage.jsonl")

        def _boom(*args, **kwargs):
            raise OSError("simulated disk full")

        # Patch builtins.open as seen from the slippage module so the
        # write fails. record_slippage MUST NOT raise.
        import src.components.slippage_shadow_logger as _mod
        monkeypatch.setattr(_mod, "open", _boom, raising=False)

        # Also patch the builtin fallback to ensure no other path can
        # write -- the call should still return cleanly.
        try:
            import builtins
            with patch.object(builtins, "open", _boom):
                record_slippage(
                    ticket=1, symbol="XAUUSD", direction="LONG",
                    requested_price=2650.0, fill_price=2650.0,
                    log_path=log_path,
                )
        except Exception as e:
            pytest.fail(f"record_slippage raised on write failure: {e}")

    def test_garbage_numeric_inputs_dont_raise(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        # None / non-numeric requested or fill -- record_slippage coerces.
        record_slippage(
            ticket=1, symbol="XAUUSD", direction="LONG",
            requested_price=None,  # type: ignore[arg-type]
            fill_price="bad",  # type: ignore[arg-type]
            log_path=log_path,
        )
        # Line still emitted, with coerced 0.0 values.
        entry = json.loads(Path(log_path).read_text().splitlines()[0])
        assert entry["requested_price"] == 0.0
        assert entry["fill_price"] == 0.0


class TestCloseSideSlippage:
    """Close telemetry uses positive-is-adverse exit-side convention."""

    def test_long_close_adverse_fill(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        record_close_slippage(
            ticket=123,
            symbol="XAUUSD",
            direction="LONG",
            requested_price=2650.00,
            fill_price=2649.90,
            close_reason="manual",
            close_event_type="FULL_POSITION_CLOSE",
            volume_closed=0.1,
            initial_volume=0.1,
            remaining_volume=0.0,
            entry_price=2640.0,
            stop_loss=2630.0,
            sl_distance=10.0,
            entry_time="2026-05-05T01:00:00+00:00",
            sl_at_breakeven=True,
            mt5_order_id=456,
            mt5_deal_id=789,
            commission=-0.7,
            swap=0.0,
            broker_profit=100.0,
            cash_risk_amount=200.0,
            dynamic_exit_action_timeline=[
                {"type": "SL_TO_BREAKEVEN_MODIFY_SUCCESS", "ticket": 123},
            ],
            log_path=log_path,
        )

        entry = json.loads(Path(log_path).read_text().splitlines()[0])
        assert entry["slippage_event_type"] == "close"
        assert entry["directional_slippage_convention"] == "POSITIVE_IS_ADVERSE_EXIT_FILL"
        assert entry["slippage_price"] == pytest.approx(-0.10)
        assert entry["slippage_directional"] == pytest.approx(0.10)
        assert entry["slippage_pips"] == pytest.approx(10.0)
        assert entry["partial_close"] is False
        assert entry["be_status"] == "SL_AT_BREAKEVEN"
        assert entry["mt5_deal_id"] == 789
        assert entry["commission_status"] == "CAPTURED"
        assert entry["broker_profit"] == pytest.approx(100.0)
        assert entry["broker_net_profit"] == pytest.approx(99.3)
        assert entry["cash_risk_amount"] == pytest.approx(200.0)
        assert entry["broker_net_r"] == pytest.approx(0.4965)
        assert entry["broker_net_r_status"] == "CAPTURED"
        assert entry["gross_close_r_multiple"] == pytest.approx(0.99)
        assert entry["cost_adjustment_r"] == pytest.approx(-0.4935)
        assert entry["order_ticket"] == 456
        assert entry["deal_ticket"] == 789
        assert entry["executed_entry_price"] == pytest.approx(2640.0)
        assert entry["executed_exit_price"] == pytest.approx(2649.90)
        assert entry["executed_stop_price"] == pytest.approx(2630.0)
        assert entry["executed_lot_size"] == pytest.approx(0.1)
        assert entry["partial_exit_lifecycle"] == "FULL_EXIT"
        assert entry["dynamic_exit_action_timeline"] == [
            {"type": "SL_TO_BREAKEVEN_MODIFY_SUCCESS", "ticket": 123},
        ]
        assert entry["dynamic_exit_action_timeline_status"] == "CAPTURED"
        assert entry["source_repair_row_identity_status"] == "NOT_BOUND_TO_NUMERIC_ROUTER_SOURCE_REPAIR_QUEUE"

    def test_close_source_repair_identity_can_be_bound_prospectively(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        record_close_slippage(
            ticket=123,
            symbol="XAUUSD",
            direction="LONG",
            requested_price=2650.00,
            fill_price=2649.90,
            close_reason="manual",
            close_event_type="FULL_POSITION_CLOSE",
            volume_closed=0.1,
            initial_volume=0.1,
            remaining_volume=0.0,
            entry_price=2640.0,
            stop_loss=2630.0,
            sl_distance=10.0,
            mt5_order_id=456,
            mt5_deal_id=789,
            commission=-0.7,
            swap=0.0,
            executed_target_price=2660.0,
            source_repair_identity={
                "source_repair_plan_row_id": "PLAN-1",
                "input_numeric_router_catalog_entry_id": "CAT-1",
                "input_numeric_router_family_spec_id": "SPEC-1",
            },
            log_path=log_path,
        )

        entry = json.loads(Path(log_path).read_text().splitlines()[0])
        assert entry["executed_target_price"] == pytest.approx(2660.0)
        assert entry["executed_target_price_status"] == "CAPTURED"
        assert entry["source_repair_plan_row_id"] == "PLAN-1"
        assert entry["input_numeric_router_catalog_entry_id"] == "CAT-1"
        assert entry["input_numeric_router_family_spec_id"] == "SPEC-1"
        assert entry["source_repair_identity_key"] == "PLAN-1|CAT-1|SPEC-1"
        assert entry["source_repair_identity_key_status"] == "CAPTURED"
        assert entry["source_repair_row_identity_status"] == "BOUND_TO_NUMERIC_ROUTER_SOURCE_REPAIR_QUEUE"

    def test_close_deal_zero_is_not_captured(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        record_close_slippage(
            ticket=123,
            symbol="XAUUSD",
            direction="LONG",
            requested_price=2650.00,
            fill_price=2649.90,
            close_reason="tp1_partial",
            close_event_type="TP1_PARTIAL",
            mt5_order_id=456,
            mt5_deal_id=0,
            log_path=log_path,
        )

        entry = json.loads(Path(log_path).read_text().splitlines()[0])
        assert entry["mt5_deal_id"] is None
        assert entry["mt5_deal_id_status"] == "ACCOUNT_HISTORY_REQUIRED"
        assert entry["deal_ticket"] is None
        assert entry["deal_ticket_status"] == "ACCOUNT_HISTORY_REQUIRED"

    def test_short_close_adverse_fill(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        record_close_slippage(
            ticket=123,
            symbol="XAUUSD",
            direction="SHORT",
            requested_price=2650.00,
            fill_price=2650.20,
            close_reason="manual",
            close_event_type="FULL_POSITION_CLOSE",
            log_path=log_path,
        )

        entry = json.loads(Path(log_path).read_text().splitlines()[0])
        assert entry["slippage_price"] == pytest.approx(0.20)
        assert entry["slippage_directional"] == pytest.approx(0.20)
        assert entry["slippage_pips"] == pytest.approx(20.0)

    def test_broker_closed_unknown_request_does_not_fabricate_slippage(self, tmp_path):
        log_path = str(tmp_path / "slippage.jsonl")
        record_close_slippage(
            ticket=123,
            symbol="NAS100",
            direction="LONG",
            requested_price=None,
            fill_price=21000.0,
            close_reason="broker_closed",
            requested_price_status="SOURCE_NOT_CAPTURED_FOR_BROKER_CLOSED",
            accounting_source="MT5_HISTORY_DEALS_READONLY",
            log_path=log_path,
        )

        entry = json.loads(Path(log_path).read_text().splitlines()[0])
        assert entry["requested_price"] is None
        assert entry["slippage_directional"] is None
        assert entry["requested_price_status"] == "SOURCE_NOT_CAPTURED_FOR_BROKER_CLOSED"
        assert entry["accounting_source"] == "MT5_HISTORY_DEALS_READONLY"


# =============================================================================
# Integration tests -- ExecutionEngine.open_trade wires through to logger
# =============================================================================


def _build_engine_with_mock_mt5(tmp_path):
    """Construct an ExecutionEngine wrapping a fully-mocked MT5 surface.

    Returns (engine, mt5, tick) so individual tests can poke at the mocks
    to simulate fill scenarios.
    """
    from src.mt5.mt5_interface import OrderResult, TickData
    from datetime import datetime, timezone

    mt5 = MagicMock()

    # Tick at bid=2649.90 / ask=2650.00 / spread_cents=10.0
    tick = TickData(
        bid=2649.90, ask=2650.00,
        time=datetime.now(timezone.utc),
        spread_cents=10.0,
    )
    mt5.get_tick.return_value = tick

    # Successful order send: filled at 2650.05 (5 cents adverse for LONG)
    order_result = OrderResult(
        retcode=10009, order=987654, volume=0.01,
        price=2650.05, comment="ok",
    )
    mt5.order_send.return_value = order_result

    # Lot-sizing path needs a non-None symbol_info with trade_tick_size > 0.
    sym_info = MagicMock()
    sym_info.trade_tick_size = 0.01
    sym_info.trade_tick_value = 1.0
    sym_info.volume_min = 0.01
    sym_info.volume_step = 0.01
    sym_info.volume_max = 100.0
    # mt5._mt5 is the underlying MetaTrader5 module; some code paths
    # reference it directly (see execution.py:989).
    mt5._mt5.symbol_info.return_value = sym_info

    # Account-balance is passed in to open_trade; mt5.get_account_balance
    # is not used inside open_trade, but mock it for safety.
    mt5.get_account_balance.return_value = 100000.0

    # No existing positions -> new ticket is always novel.
    mt5.get_positions.return_value = []

    # Configure a minimal config that survives lot-sizing.
    config = {
        "market": {"symbol": "XAUUSD"},
        "risk": {"risk_per_trade_pct": 1.0, "min_rr": 1.5},
        "deployment": {"phase": 3},
    }

    # Redirect checkpoint + pending_intent file paths to tmp_path so the
    # test isolation guard doesn't fire.
    import src.components.execution as _exec_mod
    return _exec_mod, mt5, tick, config


def test_open_trade_emits_one_slippage_log_entry(tmp_path, monkeypatch):
    """Successful open_trade -> exactly one slippage log line with correct fields."""
    _exec_mod, mt5, tick, config = _build_engine_with_mock_mt5(tmp_path)

    # Redirect the slippage logger's default path to tmp_path so we can
    # assert on it without writing to production paths.
    import src.components.slippage_shadow_logger as _sl_mod
    log_file = tmp_path / "slippage.jsonl"
    monkeypatch.setattr(_sl_mod, "SHADOW_LOG_PATH", str(log_file))

    # Also redirect execution's persistence dirs to tmp_path -- the conftest
    # write guard would otherwise reject knowledge_base/meta writes.
    monkeypatch.setattr(_exec_mod, "CHECKPOINT_PATH",
                        str(tmp_path / "execution_checkpoint.json"))
    monkeypatch.setattr(_exec_mod, "PENDING_INTENT_DIR",
                        str(tmp_path / "meta"))

    engine = _exec_mod.ExecutionEngine(mt5, config)

    trade_params = {
        "direction": "LONG",
        "entry_price": 2650.00,
        "stop_loss": 2640.00,
        "take_profit_1": 2670.00,
        "take_profit_2": 0.0,
        "take_profit_3": 0.0,
        "risk_reward_ratio": 2.0,
        "source_repair_identity": {
            "source_repair_plan_row_id": "PLAN-1",
            "input_numeric_router_catalog_entry_id": "CAT-1",
            "input_numeric_router_family_spec_id": "SPEC-1",
        },
    }
    state = engine.open_trade(
        trade_params, account_balance=100000.0,
        kill_zone="london", trigger="candidate_market",
    )

    assert state is not None, "open_trade returned None on the success path"
    assert state.ticket == 987654
    assert state.source_repair_identity == trade_params["source_repair_identity"]

    # Exactly ONE log line was written.
    assert log_file.exists(), "Slippage log file was not created"
    lines = log_file.read_text().splitlines()
    assert len(lines) == 1, f"Expected 1 log line, got {len(lines)}"

    entry = json.loads(lines[0])
    assert entry["ticket"] == 987654
    assert entry["symbol"] == "XAUUSD"
    assert entry["direction"] == "LONG"
    assert entry["requested_price"] == 2650.00
    assert entry["fill_price"] == 2650.05
    # 5 cents adverse for LONG -> +0.05 directional, +5 pips at 0.01 pip_size
    assert entry["slippage_directional"] == pytest.approx(0.05)
    assert entry["slippage_pips"] == pytest.approx(5.0)
    assert entry["spread_at_request"] == 10.0  # From TickData.spread_cents
    assert entry["kill_zone"] == "london"
    assert entry["trigger"] == "candidate_market"
    assert entry["notes"] == "ok"  # OrderResult.comment passed through
    assert entry["order_ticket"] == 987654
    assert entry["executed_entry_price"] == pytest.approx(2650.05)
    assert entry["executed_stop_price"] == pytest.approx(2640.00)
    assert entry["executed_target_price"] == pytest.approx(2670.00)
    assert entry["executed_lot_size"] == pytest.approx(1.0)
    assert entry["source_repair_geometry_contract_version"] == "numeric_router_source_repair_geometry_v1"
    assert entry["source_repair_identity_key"] == "PLAN-1|CAT-1|SPEC-1"
    assert entry["source_repair_row_identity_status"] == "BOUND_TO_NUMERIC_ROUTER_SOURCE_REPAIR_QUEUE"


def test_open_trade_zero_order_result_price_logs_effective_fill(tmp_path, monkeypatch):
    """MT5 can return OrderResult.price=0.0 for a filled order; log usable slippage."""
    from src.mt5.mt5_interface import OrderResult

    _exec_mod, mt5, tick, config = _build_engine_with_mock_mt5(tmp_path)
    mt5.order_send.return_value = OrderResult(
        retcode=10009,
        order=987654,
        volume=0.01,
        price=0.0,
        comment="ok_zero_price",
    )

    import src.components.slippage_shadow_logger as _sl_mod
    log_file = tmp_path / "slippage.jsonl"
    monkeypatch.setattr(_sl_mod, "SHADOW_LOG_PATH", str(log_file))
    monkeypatch.setattr(_exec_mod, "CHECKPOINT_PATH",
                        str(tmp_path / "execution_checkpoint.json"))
    monkeypatch.setattr(_exec_mod, "PENDING_INTENT_DIR",
                        str(tmp_path / "meta"))

    engine = _exec_mod.ExecutionEngine(mt5, config)
    state = engine.open_trade(
        {
            "direction": "LONG",
            "entry_price": 2650.00,
            "stop_loss": 2640.00,
            "take_profit_1": 2670.00,
            "take_profit_2": 0.0,
            "take_profit_3": 0.0,
            "risk_reward_ratio": 2.0,
        },
        account_balance=100000.0,
        kill_zone="london",
        trigger="candidate_market",
    )

    assert state is not None
    entry = json.loads(log_file.read_text().splitlines()[0])
    assert entry["fill_price"] == pytest.approx(2650.00)
    assert entry["raw_order_result_fill_price"] == pytest.approx(0.0)
    assert entry["fill_price_source"] == "executed_entry_price_fallback_for_zero_order_result"
    assert entry["fill_price_status"] == "ZERO_ORDER_RESULT_REPAIRED"
    assert entry["slippage_price"] == pytest.approx(0.0)
    assert entry["slippage_directional"] == pytest.approx(0.0)
    assert entry["slippage_r"] == pytest.approx(0.0)


def test_close_slippage_wire_carries_source_repair_identity(tmp_path, monkeypatch):
    from src.mt5.mt5_interface import OrderResult

    _exec_mod, mt5, tick, config = _build_engine_with_mock_mt5(tmp_path)

    import src.components.slippage_shadow_logger as _sl_mod
    log_file = tmp_path / "slippage.jsonl"
    monkeypatch.setattr(_sl_mod, "SHADOW_LOG_PATH", str(log_file))
    monkeypatch.setattr(_exec_mod, "CHECKPOINT_PATH",
                        str(tmp_path / "execution_checkpoint.json"))
    monkeypatch.setattr(_exec_mod, "PENDING_INTENT_DIR",
                        str(tmp_path / "meta"))

    engine = _exec_mod.ExecutionEngine(mt5, config)
    trade_params = {
        "direction": "LONG",
        "entry_price": 2650.00,
        "stop_loss": 2640.00,
        "take_profit_1": 2670.00,
        "take_profit_2": 0.0,
        "take_profit_3": 0.0,
        "risk_reward_ratio": 2.0,
        "source_repair_identity": {
            "source_repair_plan_row_id": "PLAN-1",
            "input_numeric_router_catalog_entry_id": "CAT-1",
            "input_numeric_router_family_spec_id": "SPEC-1",
        },
    }
    state = engine.open_trade(trade_params, account_balance=100000.0)
    assert state is not None

    close_result = OrderResult(retcode=10009, order=222333, volume=0.01, price=2651.00, comment="closed")
    engine._record_close_slippage_event(
        trade=state,
        result=close_result,
        close_reason="manual",
        close_event_type="FULL_POSITION_CLOSE",
        close_price=2651.00,
        close_volume=1.0,
        expected_close_price=2650.95,
        spread_at_request=8.0,
        partial_close=False,
        remaining_volume=0.0,
    )

    rows = [json.loads(line) for line in log_file.read_text().splitlines()]
    assert len(rows) == 2
    close_row = rows[-1]
    assert close_row["slippage_event_type"] == "close"
    assert close_row["source_repair_identity_key"] == "PLAN-1|CAT-1|SPEC-1"
    assert close_row["source_repair_row_identity_status"] == "BOUND_TO_NUMERIC_ROUTER_SOURCE_REPAIR_QUEUE"
    assert close_row["executed_target_price"] == pytest.approx(2670.00)
    assert close_row["executed_target_price_status"] == "CAPTURED"
    assert close_row["cash_risk_amount"] == pytest.approx(1000.0)
    assert close_row["broker_net_r_status"] == "BROKER_PROFIT_SOURCE_NOT_CAPTURED"


def test_open_trade_with_none_tick_still_returns_none_does_not_log(
    tmp_path, monkeypatch,
):
    """If get_tick returns None, open_trade aborts BEFORE placing the
    order -- no log line should be emitted (no fill happened)."""
    _exec_mod, mt5, tick, config = _build_engine_with_mock_mt5(tmp_path)
    mt5.get_tick.return_value = None  # Force the abort path

    import src.components.slippage_shadow_logger as _sl_mod
    log_file = tmp_path / "slippage.jsonl"
    monkeypatch.setattr(_sl_mod, "SHADOW_LOG_PATH", str(log_file))
    monkeypatch.setattr(_exec_mod, "CHECKPOINT_PATH",
                        str(tmp_path / "execution_checkpoint.json"))
    monkeypatch.setattr(_exec_mod, "PENDING_INTENT_DIR",
                        str(tmp_path / "meta"))

    engine = _exec_mod.ExecutionEngine(mt5, config)
    trade_params = {
        "direction": "LONG", "entry_price": 2650.00,
        "stop_loss": 2640.00, "take_profit_1": 2670.00,
        "take_profit_2": 0.0, "take_profit_3": 0.0,
        "risk_reward_ratio": 2.0,
    }
    state = engine.open_trade(trade_params, account_balance=100000.0)
    assert state is None, "open_trade should return None when tick is unavailable"
    # No fill happened -> no log line.
    assert not log_file.exists() or log_file.read_text() == ""


def test_open_trade_with_failed_order_logs_rejected_lifecycle(tmp_path, monkeypatch):
    """If safe_place_order fails, Stage03 still captures reject lifecycle telemetry."""
    from src.mt5.mt5_interface import OrderResult

    _exec_mod, mt5, tick, config = _build_engine_with_mock_mt5(tmp_path)
    # Simulate failed order send (non-success retcode).
    mt5.order_send.return_value = OrderResult(
        retcode=10004, order=0, volume=0.0, price=0.0, comment="rejected",
    )

    import src.components.slippage_shadow_logger as _sl_mod
    log_file = tmp_path / "slippage.jsonl"
    monkeypatch.setattr(_sl_mod, "SHADOW_LOG_PATH", str(log_file))
    monkeypatch.setattr(_exec_mod, "CHECKPOINT_PATH",
                        str(tmp_path / "execution_checkpoint.json"))
    monkeypatch.setattr(_exec_mod, "PENDING_INTENT_DIR",
                        str(tmp_path / "meta"))

    engine = _exec_mod.ExecutionEngine(mt5, config)
    trade_params = {
        "direction": "LONG", "entry_price": 2650.00,
        "stop_loss": 2640.00, "take_profit_1": 2670.00,
        "take_profit_2": 0.0, "take_profit_3": 0.0,
        "risk_reward_ratio": 2.0,
    }
    state = engine.open_trade(trade_params, account_balance=100000.0)
    assert state is None, "open_trade should return None on order failure"
    rows = [json.loads(line) for line in log_file.read_text().splitlines()]
    assert len(rows) == 1
    assert rows[0]["order_outcome_status"] == "ORDER_REJECTED_OR_TIMEOUT"
    assert rows[0]["fill_spread_status"] == "NOT_APPLICABLE_ORDER_NOT_FILLED"
    assert rows[0]["reject_or_fill_latency_ms"] is not None
    assert rows[0]["notes"] == "rejected"


def test_open_trade_logger_write_failure_does_not_break_trade(
    tmp_path, monkeypatch,
):
    """A logger write failure MUST NOT propagate to the caller.

    The fail-open contract means a failed shadow-log write is downgraded
    to a warning; open_trade still returns the TradeState so trade
    management proceeds normally.
    """
    _exec_mod, mt5, tick, config = _build_engine_with_mock_mt5(tmp_path)

    import src.components.slippage_shadow_logger as _sl_mod

    # Force record_slippage to raise -- this exercises the OUTER try/except
    # in execution.py (not the inner one in record_slippage). Both layers
    # MUST swallow.
    def _boom(**kwargs):
        raise RuntimeError("simulated logger crash")

    monkeypatch.setattr(_exec_mod, "record_slippage", _boom)
    monkeypatch.setattr(_exec_mod, "CHECKPOINT_PATH",
                        str(tmp_path / "execution_checkpoint.json"))
    monkeypatch.setattr(_exec_mod, "PENDING_INTENT_DIR",
                        str(tmp_path / "meta"))

    engine = _exec_mod.ExecutionEngine(mt5, config)
    trade_params = {
        "direction": "LONG", "entry_price": 2650.00,
        "stop_loss": 2640.00, "take_profit_1": 2670.00,
        "take_profit_2": 0.0, "take_profit_3": 0.0,
        "risk_reward_ratio": 2.0,
    }
    # MUST NOT raise even though record_slippage crashes.
    state = engine.open_trade(trade_params, account_balance=100000.0)
    assert state is not None
    assert state.ticket == 987654


def test_open_trade_with_none_spread_still_logs(tmp_path, monkeypatch):
    """If TickData has spread_cents=None (or attribute missing), log
    entry is still emitted with spread_at_request=None."""
    from src.mt5.mt5_interface import TickData
    from datetime import datetime, timezone

    _exec_mod, mt5, _tick, config = _build_engine_with_mock_mt5(tmp_path)
    # Build a TickData where spread_cents is None.
    tick_no_spread = TickData(
        bid=2649.90, ask=2650.00,
        time=datetime.now(timezone.utc), spread_cents=None,  # type: ignore[arg-type]
    )
    mt5.get_tick.return_value = tick_no_spread

    import src.components.slippage_shadow_logger as _sl_mod
    log_file = tmp_path / "slippage.jsonl"
    monkeypatch.setattr(_sl_mod, "SHADOW_LOG_PATH", str(log_file))
    monkeypatch.setattr(_exec_mod, "CHECKPOINT_PATH",
                        str(tmp_path / "execution_checkpoint.json"))
    monkeypatch.setattr(_exec_mod, "PENDING_INTENT_DIR",
                        str(tmp_path / "meta"))

    engine = _exec_mod.ExecutionEngine(mt5, config)
    trade_params = {
        "direction": "LONG", "entry_price": 2650.00,
        "stop_loss": 2640.00, "take_profit_1": 2670.00,
        "take_profit_2": 0.0, "take_profit_3": 0.0,
        "risk_reward_ratio": 2.0,
    }
    state = engine.open_trade(trade_params, account_balance=100000.0)
    assert state is not None

    entry = json.loads(log_file.read_text().splitlines()[0])
    assert entry["spread_at_request"] is None
    # Other fields must still be populated correctly.
    assert entry["ticket"] == 987654
    assert entry["fill_price"] == 2650.05


def test_default_kill_zone_and_trigger_are_null(tmp_path, monkeypatch):
    """Calling open_trade WITHOUT kwargs -> kill_zone=null, trigger=null
    in the log entry. Preserves backward-compat with existing call sites."""
    _exec_mod, mt5, tick, config = _build_engine_with_mock_mt5(tmp_path)

    import src.components.slippage_shadow_logger as _sl_mod
    log_file = tmp_path / "slippage.jsonl"
    monkeypatch.setattr(_sl_mod, "SHADOW_LOG_PATH", str(log_file))
    monkeypatch.setattr(_exec_mod, "CHECKPOINT_PATH",
                        str(tmp_path / "execution_checkpoint.json"))
    monkeypatch.setattr(_exec_mod, "PENDING_INTENT_DIR",
                        str(tmp_path / "meta"))

    engine = _exec_mod.ExecutionEngine(mt5, config)
    trade_params = {
        "direction": "LONG", "entry_price": 2650.00,
        "stop_loss": 2640.00, "take_profit_1": 2670.00,
        "take_profit_2": 0.0, "take_profit_3": 0.0,
        "risk_reward_ratio": 2.0,
    }
    # NO kill_zone / trigger kwargs -- mirrors the legacy test call sites.
    state = engine.open_trade(trade_params, account_balance=100000.0)
    assert state is not None
    entry = json.loads(log_file.read_text().splitlines()[0])
    assert entry["kill_zone"] is None
    assert entry["trigger"] is None
