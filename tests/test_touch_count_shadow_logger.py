"""Tests for the ADR-005 touch-count gate decision shadow logger.

Scope: verify ``src/components/touch_count_gate_logger.py`` writes
JSONL rows correctly under the four operational scenarios required by
ADR-005:

    1. Logger fires on PASS (touch_count < threshold)
    2. Logger fires on REJECT (touch_count >= threshold)
    3. Logger silent on non-ob_retest framework
    4. Logger captures correct touch_count + threshold values
    5. Logger handles missing target OB (writes null fields, no crash)
    6. Logger never raises into the gate when disk I/O fails
    7. JSON schema round-trips
    8. PASS-row + REJECT-row schemas are field-complete
    9. End-to-end: ``check_permissions`` -> logger row consistency
   10. Symbol attribution flows through ``check_permissions``
   11. Threshold knob propagates correctly to logged row
   12. Both PASS + REJECT for same symbol go to the same file

All tests use ``tmp_path`` for log isolation. The autouse
``_isolate_touch_count_gate_log`` fixture in ``tests/conftest.py`` redirects
the default sink to ``tmp_path / touch_count_gate_decisions.jsonl`` for
indirect-call tests; direct-call tests pass ``log_path=`` explicitly.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

import src.components.permissions as _perm_mod
from src.components.permissions import check_permissions
from src.components.touch_count_gate_logger import (
    _build_target_ob_id,
    _sanitize,
    log_touch_count_gate_decision,
)
from src.mt5.mt5_mock import MockMT5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ob(
    direction: str = "bullish",
    high: float = 2652.0,
    low: float = 2649.5,
    touch_count: int = 0,
    formation_time: str = "2026-04-25T07:00:00+00:00",
):
    return SimpleNamespace(
        type=direction,
        high=high,
        low=low,
        open=high,
        close=low,
        touch_count=touch_count,
        mitigated=False,
        formation_time=formation_time,
    )


def _make_mso(ob, m15_atr=3.0, timestamp_utc="2026-04-25T07:00:00+00:00"):
    """MSO-like object with one H1 OB at the entry price."""
    h1_tf = SimpleNamespace(order_blocks=[ob], breaker_blocks=[])
    m15_tf = SimpleNamespace(atr_14=m15_atr)
    return SimpleNamespace(
        timestamp_utc=timestamp_utc,
        timeframes={"M15": m15_tf, "H1": h1_tf},
    )


def _make_pa(
    direction: str = "LONG",
    entry: float = 2650.0,
    sl: float = 2640.0,
    rr: float = 1.5,
    framework: str = "ob_retest",
):
    """PrimaryAnalysisOutput with framework set."""
    daily_bias = "bullish" if direction == "LONG" else "bearish"
    sl_dist = abs(entry - sl)
    tp1 = (entry + sl_dist * rr) if direction == "LONG" else (entry - sl_dist * rr)
    tp = SimpleNamespace(
        direction=direction,
        entry_price=entry,
        stop_loss=sl,
        risk_reward_ratio=rr,
        take_profit_1=tp1,
    )
    reasoning = SimpleNamespace(
        setup_grade="A+",
        daily_bias=SimpleNamespace(direction=daily_bias),
    )
    return SimpleNamespace(
        reasoning=reasoning, trade_parameters=tp, framework=framework,
    )


def _good_state():
    mt5 = MockMT5()
    mt5.connect()
    mt5.set_tick(2650.0, 2650.18)
    state = {
        "daily_pnl_pct": 0,
        "trades_today": 0,
        "current_kill_zone": "london",
        "trades_london": 0,
        "losses_today": 0,
    }
    return mt5, state


def _read_log_rows(log_file: Path) -> list[dict]:
    if not log_file.exists():
        return []
    rows = []
    for line in log_file.read_text(encoding="utf-8").strip().splitlines():
        if line:
            rows.append(json.loads(line))
    return rows


# ---------------------------------------------------------------------------
# Direct-call tests (bypass check_permissions)
# ---------------------------------------------------------------------------


class TestDirectLoggerCalls:
    """Direct calls to ``log_touch_count_gate_decision`` for unit-level coverage."""

    def test_pass_row_includes_required_fields(self, tmp_path):
        """ADR-005 mandates these fields are present on every row."""
        log_file = tmp_path / "tc_log.jsonl"
        ob = _make_ob(touch_count=1)
        mso = _make_mso(ob)

        log_touch_count_gate_decision(
            symbol="XAUUSD",
            framework="ob_retest",
            target_ob=ob,
            threshold=2,
            decision="PASS",
            mso=mso,
            log_path=str(log_file),
        )

        rows = _read_log_rows(log_file)
        assert len(rows) == 1
        row = rows[0]

        # ADR-005 required fields
        assert "timestamp_utc" in row
        assert row["symbol"] == "XAUUSD"
        assert row["candle_time"] == "2026-04-25T07:00:00+00:00"
        assert row["framework"] == "ob_retest"
        assert row["gate_target_ob_touch"] == 1
        assert row["gate_threshold_at_eval"] == 2
        assert row["gate_decision"] == "PASS"
        assert row["gate_target_ob_id"].startswith("XAUUSD_bullish_")
        assert row["candidate_id"] is not None

    def test_reject_row_captures_correct_values(self, tmp_path):
        """REJECT row must record touch_count >= threshold."""
        log_file = tmp_path / "tc_log.jsonl"
        ob = _make_ob(touch_count=3)
        mso = _make_mso(ob)

        log_touch_count_gate_decision(
            symbol="USDJPY",
            framework="ob_retest",
            target_ob=ob,
            threshold=2,
            decision="REJECT",
            mso=mso,
            log_path=str(log_file),
        )

        rows = _read_log_rows(log_file)
        assert len(rows) == 1
        row = rows[0]
        assert row["gate_decision"] == "REJECT"
        assert row["gate_target_ob_touch"] == 3
        assert row["gate_threshold_at_eval"] == 2
        assert row["gate_target_ob_touch"] >= row["gate_threshold_at_eval"]
        assert row["symbol"] == "USDJPY"

    def test_logger_handles_missing_target_ob(self, tmp_path):
        """When ``target_ob=None`` the row must still be written with null
        fields — this is the atr_fallback / no-OB cohort.
        """
        log_file = tmp_path / "tc_log.jsonl"
        mso = _make_mso(_make_ob())  # mso has an OB but we pass target=None

        log_touch_count_gate_decision(
            symbol="XAUUSD",
            framework="ob_retest",
            target_ob=None,
            threshold=2,
            decision="PASS",
            mso=mso,
            log_path=str(log_file),
        )

        rows = _read_log_rows(log_file)
        assert len(rows) == 1
        row = rows[0]
        assert row["gate_target_ob_touch"] is None
        assert row["ob_low"] is None
        assert row["ob_high"] is None
        assert row["ob_type"] is None
        assert row["gate_target_ob_id"] == "XAUUSD_no_target_ob"
        assert row["gate_decision"] == "PASS"

    def test_logger_never_raises_on_disk_error(self, tmp_path):
        """Disk-write failure must be swallowed — gate evaluation must
        be unaffected by logger errors.
        """
        bad_path = tmp_path / "nonexistent" / "deeply" / "nested" / "path"
        # Path with parents missing — but we DON'T mkdir, simulate hard
        # failure by patching open() to raise.
        with patch("src.components.touch_count_gate_logger.open",
                   side_effect=OSError("disk full")):
            # Must not raise
            log_touch_count_gate_decision(
                symbol="XAUUSD",
                framework="ob_retest",
                target_ob=_make_ob(touch_count=1),
                threshold=2,
                decision="PASS",
                mso=_make_mso(_make_ob()),
                log_path=str(bad_path / "log.jsonl"),
            )
        # If we got here, the function did not raise.

    def test_logger_jsonl_round_trips(self, tmp_path):
        """Every row must be valid UTF-8 JSON, one per line."""
        log_file = tmp_path / "tc_log.jsonl"
        ob = _make_ob(touch_count=0)
        mso = _make_mso(ob)

        for _ in range(3):
            log_touch_count_gate_decision(
                symbol="XAUUSD",
                framework="ob_retest",
                target_ob=ob,
                threshold=2,
                decision="PASS",
                mso=mso,
                log_path=str(log_file),
            )

        text = log_file.read_text(encoding="utf-8")
        lines = [ln for ln in text.split("\n") if ln]
        assert len(lines) == 3
        for ln in lines:
            row = json.loads(ln)  # must not raise
            assert isinstance(row, dict)

    def test_target_ob_id_sanitization(self):
        """ID must strip colons / spaces from formation_time."""
        ob = _make_ob(formation_time="2026-04-25T07:00:00+00:00")
        result = _build_target_ob_id("XAUUSD", ob)
        # Colons → underscores; '+' → underscore
        assert ":" not in result
        assert " " not in result
        assert result.startswith("XAUUSD_bullish_")

    def test_sanitize_handles_none_and_empty(self):
        assert _sanitize(None) == "unknown"
        assert _sanitize("") == "unknown"
        assert _sanitize("XAUUSD") == "XAUUSD"
        assert _sanitize("a:b c+d") == "a_b_c_d"

    def test_decision_n_a_recorded_for_non_ob_retest(self, tmp_path):
        """Allowed for callers to log explicit ``N/A`` when invoking
        directly for diagnostic purposes.
        """
        log_file = tmp_path / "tc_log.jsonl"
        log_touch_count_gate_decision(
            symbol="XAUUSD",
            framework="fvg_fill",
            target_ob=None,
            threshold=2,
            decision="N/A",
            mso=None,
            log_path=str(log_file),
        )
        rows = _read_log_rows(log_file)
        assert len(rows) == 1
        assert rows[0]["gate_decision"] == "N/A"
        assert rows[0]["framework"] == "fvg_fill"


# ---------------------------------------------------------------------------
# Indirect tests via check_permissions (production code path)
# ---------------------------------------------------------------------------


class TestLoggerThroughCheckPermissions:
    """End-to-end: ``check_permissions`` triggers the logger via the gate."""

    def test_pass_logged_when_touch_below_threshold(
        self, _isolate_touch_count_gate_log,
    ):
        """A clean ob_retest CANDIDATE with touch=1 must PASS and log a row."""
        mt5, state = _good_state()
        ob = _make_ob(touch_count=1)
        mso = _make_mso(ob)
        pa = _make_pa(direction="LONG", entry=2650.0, sl=2640.0)

        denial = check_permissions(pa, mso, state, mt5, symbol="XAUUSD")
        assert denial is None

        rows = _read_log_rows(_isolate_touch_count_gate_log)
        # At least one PASS row must be logged. Other passes downstream
        # may not log; we only assert the first row matches the gate's
        # output for this evaluation.
        assert len(rows) >= 1
        first = rows[0]
        assert first["gate_decision"] == "PASS"
        assert first["gate_target_ob_touch"] == 1
        assert first["gate_threshold_at_eval"] == 2
        assert first["framework"] == "ob_retest"
        assert first["symbol"] == "XAUUSD"

    def test_reject_logged_when_touch_at_threshold(
        self, _isolate_touch_count_gate_log,
    ):
        """touch=2 must REJECT under default threshold 2 + log REJECT row."""
        mt5, state = _good_state()
        ob = _make_ob(touch_count=2)
        mso = _make_mso(ob)
        pa = _make_pa(direction="LONG", entry=2650.0, sl=2640.0)

        denial = check_permissions(pa, mso, state, mt5, symbol="XAUUSD")
        assert denial is not None
        assert denial.reason == "touch_count_too_high"

        rows = _read_log_rows(_isolate_touch_count_gate_log)
        assert len(rows) == 1
        row = rows[0]
        assert row["gate_decision"] == "REJECT"
        assert row["gate_target_ob_touch"] == 2
        assert row["gate_threshold_at_eval"] == 2
        assert row["symbol"] == "XAUUSD"

    def test_logger_silent_on_non_ob_retest_framework(
        self, _isolate_touch_count_gate_log,
    ):
        """Non-ob_retest framework: gate exits early; logger MUST NOT fire."""
        mt5, state = _good_state()
        ob = _make_ob(touch_count=5)  # would reject if logged
        mso = _make_mso(ob)
        # framework=fvg_fill should bypass the gate AND the logger
        pa = _make_pa(framework="fvg_fill")

        denial = check_permissions(pa, mso, state, mt5, symbol="XAUUSD")
        # We don't care whether downstream gates pass/fail; the
        # invariant under test is: NO touch-count log row was written.
        assert not _isolate_touch_count_gate_log.exists() or (
            _read_log_rows(_isolate_touch_count_gate_log) == []
        )

    def test_logger_silent_on_breaker_re_entry_framework(
        self, _isolate_touch_count_gate_log,
    ):
        """``breaker_re_entry`` framework also bypasses the touch gate."""
        mt5, state = _good_state()
        ob = _make_ob(touch_count=5)
        mso = _make_mso(ob)
        pa = _make_pa(framework="breaker_re_entry")

        check_permissions(pa, mso, state, mt5, symbol="XAUUSD")
        rows = _read_log_rows(_isolate_touch_count_gate_log)
        assert rows == []

    def test_threshold_knob_loosened_to_3_logs_correct_threshold(
        self, _isolate_touch_count_gate_log,
    ):
        """When config sets threshold=3, the logged row reflects 3."""
        mt5, state = _good_state()
        ob = _make_ob(touch_count=2)
        mso = _make_mso(ob)
        pa = _make_pa()

        cfg = {"gate1": {"touch_count_reject_threshold": 3}}
        denial = check_permissions(pa, mso, state, mt5, config=cfg, symbol="XAUUSD")
        # touch=2 < threshold=3 → PASS
        assert denial is None

        rows = _read_log_rows(_isolate_touch_count_gate_log)
        assert len(rows) >= 1
        first = rows[0]
        assert first["gate_decision"] == "PASS"
        assert first["gate_target_ob_touch"] == 2
        assert first["gate_threshold_at_eval"] == 3

    def test_symbol_attribution_flows_through(
        self, _isolate_touch_count_gate_log,
    ):
        """Different symbols must produce different ``symbol`` field values."""
        mt5, state = _good_state()
        ob = _make_ob(touch_count=3)  # ensure REJECT to limit row count
        mso = _make_mso(ob)
        pa = _make_pa()

        check_permissions(pa, mso, state, mt5, symbol="USDJPY")
        check_permissions(pa, mso, state, mt5, symbol="GBPJPY")

        rows = _read_log_rows(_isolate_touch_count_gate_log)
        assert len(rows) == 2
        assert rows[0]["symbol"] == "USDJPY"
        assert rows[1]["symbol"] == "GBPJPY"
        # Both should be REJECT (touch=3 >= threshold=2)
        assert all(r["gate_decision"] == "REJECT" for r in rows)

    def test_no_target_ob_logged_as_pass_with_null_fields(
        self, _isolate_touch_count_gate_log,
    ):
        """Entry price NOT inside any OB — gate silently passes;
        logger writes a row with ``gate_target_ob_touch=null``.
        """
        mt5, state = _good_state()
        # Build OB at 2649.5-2652.0 but entry at 2700.0 (way above the OB)
        ob = _make_ob(touch_count=1, high=2652.0, low=2649.5)
        mso = _make_mso(ob)
        # Entry 2700, SL 2690 — outside the OB zone
        pa = _make_pa(direction="LONG", entry=2700.0, sl=2690.0)

        check_permissions(pa, mso, state, mt5, symbol="XAUUSD")
        rows = _read_log_rows(_isolate_touch_count_gate_log)
        assert len(rows) >= 1
        first = rows[0]
        assert first["gate_decision"] == "PASS"
        assert first["gate_target_ob_touch"] is None
        assert first["gate_target_ob_id"] == "XAUUSD_no_target_ob"

    def test_pass_and_reject_share_same_log_file(
        self, _isolate_touch_count_gate_log,
    ):
        """Sequential PASS + REJECT both append to the same JSONL file."""
        mt5, state = _good_state()

        # 1st: touch=1 → PASS
        ob1 = _make_ob(touch_count=1)
        mso1 = _make_mso(ob1)
        pa1 = _make_pa()
        check_permissions(pa1, mso1, state, mt5, symbol="XAUUSD")

        # 2nd: touch=4 → REJECT
        ob2 = _make_ob(touch_count=4)
        mso2 = _make_mso(ob2)
        pa2 = _make_pa()
        check_permissions(pa2, mso2, state, mt5, symbol="XAUUSD")

        rows = _read_log_rows(_isolate_touch_count_gate_log)
        # At least 2 rows: 1 PASS + 1 REJECT
        decisions = [r["gate_decision"] for r in rows]
        assert "PASS" in decisions
        assert "REJECT" in decisions

    def test_logger_does_not_break_existing_gate_behavior(
        self, _isolate_touch_count_gate_log,
    ):
        """Adding the logger must NOT change the gate's pass/reject set.

        Sanity: feed touch_count=0,1,2,3 and assert the boolean outcome
        is identical to the documented threshold=2 semantics.
        """
        mt5, state = _good_state()
        for touches, should_reject in [(0, False), (1, False), (2, True), (3, True)]:
            ob = _make_ob(touch_count=touches)
            mso = _make_mso(ob)
            pa = _make_pa()
            denial = check_permissions(pa, mso, state, mt5, symbol="XAUUSD")
            if should_reject:
                assert denial is not None, f"touch={touches} expected REJECT"
                assert denial.reason == "touch_count_too_high"
            else:
                assert denial is None, (
                    f"touch={touches} expected PASS, got {denial}"
                )

    def test_mso_without_timestamp_logs_null_candle_time(
        self, _isolate_touch_count_gate_log,
    ):
        """MSO missing ``timestamp_utc`` must log ``candle_time=null``."""
        mt5, state = _good_state()
        ob = _make_ob(touch_count=2)
        mso = _make_mso(ob, timestamp_utc=None)
        # Force the attribute to be missing to test resilience
        del mso.timestamp_utc

        pa = _make_pa()
        check_permissions(pa, mso, state, mt5, symbol="XAUUSD")

        rows = _read_log_rows(_isolate_touch_count_gate_log)
        assert len(rows) == 1
        assert rows[0]["candle_time"] is None
        # candidate_id still derived (will use 'unknown')
        assert rows[0]["candidate_id"] is not None
