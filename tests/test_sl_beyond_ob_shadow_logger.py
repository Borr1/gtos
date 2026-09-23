"""Tests for the A.1 sl_beyond_ob L2 decision shadow logger.

Scope: verify ``src/components/sl_beyond_ob_shadow_logger.py`` writes
JSONL rows correctly under the four operational scenarios required by
the A.1 deferred-changes spec:

    1. Logger fires on PASS (SL placed beyond OB extreme, geometry valid)
    2. Logger fires on REJECT (SL inside OB zone, geometry invalid)
    3. Logger silent on SKIP (no matched OB/breaker)
    4. Logger captures correct entry / SL / TP1 / OB-low / OB-high values
    5. Logger handles missing analysis fields (writes null fields, no crash)
    6. Logger never raises into verification when disk I/O fails
    7. JSON schema round-trips
    8. Config gate (enabled=False -> no write)
    9. End-to-end: ``verify_candidate`` -> logger row consistency
   10. Symbol attribution flows through ``config["market"]["symbol"]``
   11. Both PASS + REJECT for same symbol go to the same file
   12. Verification result is unaffected by logger exceptions

All tests use ``tmp_path`` for log isolation. The autouse
``_isolate_sl_beyond_ob_log`` fixture in ``tests/conftest.py`` redirects
the default sink to ``tmp_path / sl_beyond_ob_decisions.jsonl`` for
indirect-call tests; direct-call tests pass ``log_path=`` explicitly.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.components.sl_beyond_ob_shadow_logger import (
    SHADOW_LOG_PATH,
    log_sl_beyond_ob_decision,
)
from src.components.verification import verify_candidate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ob(
    direction: str = "bullish",
    high: float = 2652.0,
    low: float = 2649.5,
    formation_time: str = "2026-04-25T07:00:00+00:00",
):
    """Return a simple OB-like namespace."""
    return SimpleNamespace(
        type=direction,
        high=high,
        low=low,
        open=high,
        close=low,
        touch_count=0,
        mitigated=False,
        formation_time=formation_time,
    )


def _make_bb(direction: str = "bullish", zone_high: float = 2652.0, zone_low: float = 2649.5):
    """Return a simple BreakerBlock-like namespace."""
    return SimpleNamespace(
        direction=direction,
        zone_high=zone_high,
        zone_low=zone_low,
        is_retested=False,
    )


def _make_check(status: str = "PASS", detail: str = "default detail"):
    """Return a VerificationCheck-like namespace."""
    return SimpleNamespace(name="sl_beyond_ob", status=status, detail=detail)


def _make_pa(
    direction: str = "LONG",
    entry: float = 2650.0,
    sl: float = 2640.0,
    tp1: float = 2670.0,
    framework: str = "ob_retest",
    confidence_score: int = 75,
):
    """PrimaryAnalysisOutput-like namespace."""
    tp = SimpleNamespace(
        direction=direction,
        entry_price=entry,
        stop_loss=sl,
        take_profit_1=tp1,
        risk_reward_ratio=2.0,
    )
    return SimpleNamespace(
        trade_parameters=tp,
        framework=framework,
        confidence_score=confidence_score,
    )


def _make_mso(timestamp_utc="2026-04-25T07:00:00+00:00", h1_atr=4.0):
    """MSO-like object with H1 ATR populated."""
    h1_tf = SimpleNamespace(atr_14=h1_atr, order_blocks=[], breaker_blocks=[])
    return SimpleNamespace(
        timestamp_utc=timestamp_utc,
        timeframes={"H1": h1_tf},
    )


def _read_log_rows(log_file: Path) -> list[dict]:
    """Parse JSONL rows out of the shadow log."""
    if not log_file.exists():
        return []
    rows = []
    for line in log_file.read_text(encoding="utf-8").strip().splitlines():
        if line:
            rows.append(json.loads(line))
    return rows


# ---------------------------------------------------------------------------
# Direct-call tests (bypass verify_candidate)
# ---------------------------------------------------------------------------


class TestDirectLoggerCalls:
    """Direct calls to ``log_sl_beyond_ob_decision`` for unit-level coverage."""

    def test_pass_row_includes_required_fields(self, tmp_path):
        """A.1 mandates these fields are present on every row."""
        log_file = tmp_path / "sl_log.jsonl"
        ob = _make_ob()
        mso = _make_mso()
        analysis = _make_pa()
        check = _make_check(
            "PASS", "SL 2640.00 is below OB low 2649.50",
        )

        log_sl_beyond_ob_decision(
            analysis=analysis,
            mso=mso,
            config={"market": {"symbol": "XAUUSD"}},
            matched_ob=ob,
            matched_bb=None,
            check_result=check,
            log_path=str(log_file),
        )

        rows = _read_log_rows(log_file)
        assert len(rows) == 1
        row = rows[0]

        # A.1 required fields
        assert "timestamp_utc" in row
        assert row["candle_time"] == "2026-04-25T07:00:00+00:00"
        assert row["symbol"] == "XAUUSD"
        assert row["framework"] == "ob_retest"
        assert row["l2_decision"] == "PASS"
        assert row["l2_reason"] == "SL 2640.00 is below OB low 2649.50"
        assert row["direction"] == "LONG"
        assert row["proposed_entry"] == 2650.0
        assert row["proposed_sl"] == 2640.0
        assert row["proposed_tp1"] == 2670.0
        assert row["ob_low"] == 2649.5
        assert row["ob_high"] == 2652.0
        assert row["zone_label"] == "OB"
        assert row["h1_atr"] == 4.0
        assert row["confidence_score"] == 75

    def test_reject_row_captures_correct_values(self, tmp_path):
        """REJECT row must record FAIL geometry (SL inside OB zone)."""
        log_file = tmp_path / "sl_log.jsonl"
        ob = _make_ob(low=2649.5, high=2652.0)
        mso = _make_mso()
        # SL inside the OB → would FAIL the strict-< check
        analysis = _make_pa(direction="LONG", entry=2650.5, sl=2650.0, tp1=2660.0)
        check = _make_check(
            "FAIL",
            "SL 2650.00 is NOT below OB low 2649.50 for LONG trade",
        )

        log_sl_beyond_ob_decision(
            analysis=analysis,
            mso=mso,
            config={"market": {"symbol": "USDJPY"}},
            matched_ob=ob,
            matched_bb=None,
            check_result=check,
            log_path=str(log_file),
        )

        rows = _read_log_rows(log_file)
        assert len(rows) == 1
        row = rows[0]
        assert row["l2_decision"] == "REJECT"
        assert row["proposed_sl"] == 2650.0
        assert row["ob_low"] == 2649.5
        assert row["symbol"] == "USDJPY"
        assert "NOT below" in row["l2_reason"]

    def test_skip_status_does_not_write_row(self, tmp_path):
        """SKIP results from _check_sl_beyond_ob are dropped silently."""
        log_file = tmp_path / "sl_log.jsonl"
        check = _make_check("SKIP", "No matched OB/breaker from Check 3")
        log_sl_beyond_ob_decision(
            analysis=_make_pa(),
            mso=_make_mso(),
            config={"market": {"symbol": "XAUUSD"}},
            matched_ob=None,
            matched_bb=None,
            check_result=check,
            log_path=str(log_file),
        )
        # No file at all (or file is empty)
        assert not log_file.exists() or _read_log_rows(log_file) == []

    def test_breaker_match_captures_zone_correctly(self, tmp_path):
        """When matched_bb is set, ob_low/ob_high pull from zone_low/zone_high
        and zone_label is 'breaker'."""
        log_file = tmp_path / "sl_log.jsonl"
        bb = _make_bb(zone_low=2645.0, zone_high=2648.0)
        check = _make_check(
            "PASS", "SL 2640.00 is below breaker low 2645.00",
        )

        log_sl_beyond_ob_decision(
            analysis=_make_pa(),
            mso=_make_mso(),
            config={"market": {"symbol": "GBPJPY"}},
            matched_ob=None,
            matched_bb=bb,
            check_result=check,
            log_path=str(log_file),
        )

        rows = _read_log_rows(log_file)
        assert len(rows) == 1
        assert rows[0]["ob_low"] == 2645.0
        assert rows[0]["ob_high"] == 2648.0
        assert rows[0]["zone_label"] == "breaker"

    def test_logger_handles_missing_trade_parameters(self, tmp_path):
        """When analysis.trade_parameters is None, fields are null."""
        log_file = tmp_path / "sl_log.jsonl"
        analysis = SimpleNamespace(
            trade_parameters=None,
            framework="ob_retest",
            confidence_score=80,
        )
        check = _make_check("PASS", "should not appear")

        log_sl_beyond_ob_decision(
            analysis=analysis,
            mso=_make_mso(),
            config={"market": {"symbol": "XAUUSD"}},
            matched_ob=_make_ob(),
            matched_bb=None,
            check_result=check,
            log_path=str(log_file),
        )

        rows = _read_log_rows(log_file)
        assert len(rows) == 1
        row = rows[0]
        assert row["direction"] is None
        assert row["proposed_entry"] is None
        assert row["proposed_sl"] is None
        assert row["proposed_tp1"] is None

    def test_logger_handles_missing_mso_fields(self, tmp_path):
        """Missing timestamp_utc and H1 ATR don't crash the logger."""
        log_file = tmp_path / "sl_log.jsonl"
        # MSO without timeframes attr
        mso = SimpleNamespace()
        check = _make_check("PASS", "ok")

        log_sl_beyond_ob_decision(
            analysis=_make_pa(),
            mso=mso,
            config={"market": {"symbol": "XAUUSD"}},
            matched_ob=_make_ob(),
            matched_bb=None,
            check_result=check,
            log_path=str(log_file),
        )

        rows = _read_log_rows(log_file)
        assert len(rows) == 1
        assert rows[0]["candle_time"] is None
        assert rows[0]["h1_atr"] is None

    def test_logger_never_raises_on_disk_error(self, tmp_path):
        """Disk-write failure must be swallowed — verification must
        be unaffected by logger errors.
        """
        bad_path = tmp_path / "nonexistent" / "deeply" / "nested" / "path"
        with patch(
            "src.components.sl_beyond_ob_shadow_logger.open",
            side_effect=OSError("disk full"),
        ):
            # Must not raise
            log_sl_beyond_ob_decision(
                analysis=_make_pa(),
                mso=_make_mso(),
                config={"market": {"symbol": "XAUUSD"}},
                matched_ob=_make_ob(),
                matched_bb=None,
                check_result=_make_check("PASS", "ok"),
                log_path=str(bad_path / "log.jsonl"),
            )
        # If we got here, the function did not raise.

    def test_logger_jsonl_round_trips(self, tmp_path):
        """Every row must be valid UTF-8 JSON, one per line."""
        log_file = tmp_path / "sl_log.jsonl"
        for _ in range(3):
            log_sl_beyond_ob_decision(
                analysis=_make_pa(),
                mso=_make_mso(),
                config={"market": {"symbol": "XAUUSD"}},
                matched_ob=_make_ob(),
                matched_bb=None,
                check_result=_make_check("PASS", "ok"),
                log_path=str(log_file),
            )

        text = log_file.read_text(encoding="utf-8")
        lines = [ln for ln in text.split("\n") if ln]
        assert len(lines) == 3
        for ln in lines:
            row = json.loads(ln)  # must not raise
            assert isinstance(row, dict)

    def test_config_gate_disabled_blocks_write(self, tmp_path):
        """When ``shadow_loggers.sl_beyond_ob_decisions_logger.enabled``
        is False, no row is written.
        """
        log_file = tmp_path / "sl_log.jsonl"
        config = {
            "market": {"symbol": "XAUUSD"},
            "shadow_loggers": {
                "sl_beyond_ob_decisions_logger": {"enabled": False},
            },
        }
        log_sl_beyond_ob_decision(
            analysis=_make_pa(),
            mso=_make_mso(),
            config=config,
            matched_ob=_make_ob(),
            matched_bb=None,
            check_result=_make_check("PASS", "ok"),
            log_path=str(log_file),
        )
        assert not log_file.exists() or _read_log_rows(log_file) == []

    def test_config_gate_enabled_explicitly(self, tmp_path):
        """When config explicitly sets enabled=True, the row is written."""
        log_file = tmp_path / "sl_log.jsonl"
        config = {
            "market": {"symbol": "XAUUSD"},
            "shadow_loggers": {
                "sl_beyond_ob_decisions_logger": {"enabled": True},
            },
        }
        log_sl_beyond_ob_decision(
            analysis=_make_pa(),
            mso=_make_mso(),
            config=config,
            matched_ob=_make_ob(),
            matched_bb=None,
            check_result=_make_check("PASS", "ok"),
            log_path=str(log_file),
        )
        rows = _read_log_rows(log_file)
        assert len(rows) == 1

    def test_config_gate_default_is_enabled(self, tmp_path):
        """When config lacks the shadow_loggers key, default is enabled."""
        log_file = tmp_path / "sl_log.jsonl"
        config = {"market": {"symbol": "XAUUSD"}}
        log_sl_beyond_ob_decision(
            analysis=_make_pa(),
            mso=_make_mso(),
            config=config,
            matched_ob=_make_ob(),
            matched_bb=None,
            check_result=_make_check("PASS", "ok"),
            log_path=str(log_file),
        )
        rows = _read_log_rows(log_file)
        assert len(rows) == 1

    def test_none_config_uses_default_enabled(self, tmp_path):
        """When config is None, logger uses defaults (enabled=True, symbol=None)."""
        log_file = tmp_path / "sl_log.jsonl"
        log_sl_beyond_ob_decision(
            analysis=_make_pa(),
            mso=_make_mso(),
            config=None,
            matched_ob=_make_ob(),
            matched_bb=None,
            check_result=_make_check("PASS", "ok"),
            log_path=str(log_file),
        )
        rows = _read_log_rows(log_file)
        assert len(rows) == 1
        assert rows[0]["symbol"] is None

    def test_pass_and_reject_share_same_log_file(self, tmp_path):
        """Sequential PASS + REJECT both append to the same JSONL file."""
        log_file = tmp_path / "sl_log.jsonl"
        ob = _make_ob()

        log_sl_beyond_ob_decision(
            analysis=_make_pa(direction="LONG", entry=2650.0, sl=2640.0),
            mso=_make_mso(),
            config={"market": {"symbol": "XAUUSD"}},
            matched_ob=ob,
            matched_bb=None,
            check_result=_make_check("PASS", "SL below OB low"),
            log_path=str(log_file),
        )
        log_sl_beyond_ob_decision(
            analysis=_make_pa(direction="LONG", entry=2650.5, sl=2650.0),
            mso=_make_mso(),
            config={"market": {"symbol": "XAUUSD"}},
            matched_ob=ob,
            matched_bb=None,
            check_result=_make_check("FAIL", "SL inside OB"),
            log_path=str(log_file),
        )

        rows = _read_log_rows(log_file)
        assert len(rows) == 2
        decisions = [r["l2_decision"] for r in rows]
        assert "PASS" in decisions
        assert "REJECT" in decisions

    def test_short_direction_handled(self, tmp_path):
        """SHORT direction with SL above OB high logs correctly."""
        log_file = tmp_path / "sl_log.jsonl"
        ob = _make_ob(direction="bearish", high=2652.0, low=2649.5)
        analysis = _make_pa(direction="SHORT", entry=2650.0, sl=2655.0, tp1=2640.0)
        check = _make_check("PASS", "SL 2655.00 is above OB high 2652.00")

        log_sl_beyond_ob_decision(
            analysis=analysis,
            mso=_make_mso(),
            config={"market": {"symbol": "XAUUSD"}},
            matched_ob=ob,
            matched_bb=None,
            check_result=check,
            log_path=str(log_file),
        )

        rows = _read_log_rows(log_file)
        assert len(rows) == 1
        row = rows[0]
        assert row["direction"] == "SHORT"
        assert row["proposed_sl"] == 2655.0


# ---------------------------------------------------------------------------
# Indirect tests via verify_candidate (production code path)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Indirect-test helpers — reuse the proven model construction pattern from
# tests/test_verification.py so the Pydantic field set matches production.
# ---------------------------------------------------------------------------


def _real_h1_tf(
    obs=None,
    breakers=None,
    pd_eq=2262.0,
    pd_impulse_low=2255.0,
    pd_impulse_high=2270.0,
    h1_atr=4.0,
):
    from src.models.market_state_models import (
        OrderBlock,
        PremiumDiscount,
        PriceZone,
        StructureAnalysis,
        StructureEvent,
        TimeframeState,
    )
    if obs is None:
        obs = [OrderBlock(
            type="bullish",
            high=2261.50,
            low=2259.80,
            open=2261.00,
            close=2260.00,
            formation_index=30,
            formation_time="2024-04-01T06:00:00",
            causing_bos_index=35,
            mitigated=False,
            causing_event_type="BOS",
        )]
    return TimeframeState(
        structure=StructureAnalysis(direction="bullish"),
        structure_events=[StructureEvent(
            type="BOS", direction="bullish",
            level_broken=2265.0, close_price=2266.0,
            candle_index=35, time="2024-04-01T06:30:00",
            displacement_present=True, displacement_ratio=2.5,
        )],
        order_blocks=obs,
        breaker_blocks=breakers or [],
        premium_discount=PremiumDiscount(
            impulse_low=pd_impulse_low,
            impulse_high=pd_impulse_high,
            equilibrium_50=pd_eq,
            fib_62=pd_impulse_high - (pd_impulse_high - pd_impulse_low) * 0.618,
            fib_79=pd_impulse_high - (pd_impulse_high - pd_impulse_low) * 0.786,
            discount_zone=PriceZone(top=pd_eq, bottom=pd_impulse_low),
            premium_zone=PriceZone(top=pd_impulse_high, bottom=pd_eq),
            ote_zone=PriceZone(
                top=pd_impulse_high - (pd_impulse_high - pd_impulse_low) * 0.618,
                bottom=pd_impulse_high - (pd_impulse_high - pd_impulse_low) * 0.786,
            ),
        ),
        avg_candle_body=2.0,
        atr_14=h1_atr,
    )


def _real_m15_tf():
    from src.models.market_state_models import (
        StructureAnalysis,
        StructureEvent,
        TimeframeState,
    )
    return TimeframeState(
        structure=StructureAnalysis(direction="bullish"),
        structure_events=[StructureEvent(
            type="CHoCH", direction="bullish",
            level_broken=2260.0, close_price=2262.0,
            candle_index=50, time="2024-04-01T08:00:00",
            displacement_present=True, displacement_ratio=2.0,
        )],
        avg_candle_body=1.0,
        atr_14=2.0,
    )


def _real_mso(h1_tf=None, m15_tf=None):
    from src.models.market_state_models import (
        DataQuality,
        MarketStateObject,
        SessionLevels,
        StructureAnalysis,
        TimeframeState,
    )
    return MarketStateObject(
        timestamp_utc="2024-04-01T08:00:00Z",
        timeframes={
            "D1": TimeframeState(structure=StructureAnalysis(direction="bullish")),
            "H4": TimeframeState(structure=StructureAnalysis(direction="bullish")),
            "H1": h1_tf or _real_h1_tf(),
            "M15": m15_tf or _real_m15_tf(),
        },
        session_levels=SessionLevels(
            asian_high=2265.0, asian_low=2258.0,
            pdh=2270.0, pdl=2250.0,
        ),
        data_quality=DataQuality(
            all_timeframes_complete=True,
            spread_normal=True,
            mt5_connected=True,
            timestamp_utc="2024-04-01T08:00:00Z",
        ),
    )


def _real_analysis(
    direction="LONG",
    entry=2260.50,
    sl=2258.50,
    tp1=2263.50,
    poi_price=2260.50,
    framework="ob_retest",
    confidence_score=80,
):
    from src.models.analysis_models import (
        DailyBiasAnalysis,
        H1SetupAnalysis,
        H4AlignmentAnalysis,
        LiquiditySweepAnalysis,
        M15ConfirmationAnalysis,
        PrimaryAnalysisOutput,
        PrimaryAnalysisReasoning,
        TradeParameters,
    )
    return PrimaryAnalysisOutput(
        timestamp_utc="2024-04-01T08:00:00Z",
        model_used="test",
        decision="CANDIDATE",
        confidence_score=confidence_score,
        framework=framework,
        reasoning=PrimaryAnalysisReasoning(
            daily_bias=DailyBiasAnalysis(direction="bullish", confidence="high"),
            h4_alignment=H4AlignmentAnalysis(aligned=True),
            h1_setup=H1SetupAnalysis(
                poi_identified=True,
                poi_type="OB",
                poi_price_level=poi_price,
                zone="discount",
            ),
            liquidity_sweep=LiquiditySweepAnalysis(detected=False),
            m15_confirmation=M15ConfirmationAnalysis(
                choch_detected=True,
                displacement_quality="strong",
                displacement_candle_body_vs_avg_ratio=2.0,
            ),
            setup_grade="A+",
        ),
        trade_parameters=TradeParameters(
            direction=direction,
            entry_price=entry,
            stop_loss=sl,
            take_profit_1=tp1,
            risk_reward_ratio=1.5,
        ),
    )


_DEFAULT_CONFIG = {
    "market": {"symbol": "XAUUSD"},
    "model_a": {"displacement_min_ratio": 1.5},
    "verification": {
        "enabled": True,
        "ob_price_tolerance_pct": 0.002,
        "strict_zone_check": False,
        "log_warnings": False,
    },
}


class TestLoggerThroughVerifyCandidate:
    """End-to-end: ``verify_candidate`` triggers the logger via the L2 check."""

    def test_pass_logged_when_sl_beyond_ob(self, _isolate_sl_beyond_ob_log):
        """A clean ob_retest CANDIDATE with SL beyond OB low must PASS L2
        and log a PASS row.
        """
        # Default OB: high=2261.50, low=2259.80; SL 2258.50 < 2259.80 → PASS
        mso = _real_mso()
        pa = _real_analysis(direction="LONG", entry=2260.50, sl=2258.50)

        result = verify_candidate(pa, mso, _DEFAULT_CONFIG)
        sl_check = next(c for c in result.checks if c.name == "sl_beyond_ob")
        assert sl_check.status == "PASS"

        rows = _read_log_rows(_isolate_sl_beyond_ob_log)
        assert len(rows) == 1
        row = rows[0]
        assert row["l2_decision"] == "PASS"
        assert row["symbol"] == "XAUUSD"
        assert row["framework"] == "ob_retest"
        assert row["direction"] == "LONG"
        assert row["proposed_sl"] == 2258.50
        assert row["ob_low"] == 2259.80
        assert row["ob_high"] == 2261.50
        assert row["h1_atr"] == 4.0
        assert row["zone_label"] == "OB"

    def test_reject_logged_when_sl_inside_ob(self, _isolate_sl_beyond_ob_log):
        """SL inside OB zone must FAIL L2 and log a REJECT row."""
        # SL 2260.00 sits BETWEEN ob.low 2259.80 and ob.high 2261.50 → FAIL
        mso = _real_mso()
        pa = _real_analysis(direction="LONG", entry=2260.50, sl=2260.00)

        result = verify_candidate(pa, mso, _DEFAULT_CONFIG)
        sl_check = next(c for c in result.checks if c.name == "sl_beyond_ob")
        assert sl_check.status == "FAIL"

        rows = _read_log_rows(_isolate_sl_beyond_ob_log)
        assert len(rows) == 1
        row = rows[0]
        assert row["l2_decision"] == "REJECT"
        assert row["proposed_sl"] == 2260.00
        # ADR-006 (2026-04-26) reason format: "does not clear ... by floor".
        # Pre-ADR-006 format was "NOT below ..." — strict-< binary check.
        assert "does not clear" in row["l2_reason"]

    def test_logger_silent_on_fvg_fill_framework(self, _isolate_sl_beyond_ob_log):
        """fvg_fill framework SKIPs the sl_beyond_ob check (it's not
        OB-anchored). Logger MUST NOT fire — SKIP rows are dropped.

        Note: in the fvg_fill branch of verify_candidate, the check is
        emitted as ``VerificationCheck("sl_beyond_ob", "SKIP", ...)``
        WITHOUT calling ``_check_sl_beyond_ob``, and our hook only fires
        in the ob_retest branch. So no logger row should be written.
        """
        mso = _real_mso()
        pa = _real_analysis(framework="fvg_fill")

        verify_candidate(pa, mso, _DEFAULT_CONFIG)

        log_file = _isolate_sl_beyond_ob_log
        assert not log_file.exists() or _read_log_rows(log_file) == []

    def test_verification_unaffected_by_logger_exception(
        self, _isolate_sl_beyond_ob_log,
    ):
        """If the inner logger raises, the outer try/except in
        verify_candidate must catch it and the L2 result is unchanged.
        """
        mso = _real_mso()
        pa = _real_analysis(direction="LONG", entry=2260.50, sl=2258.50)

        with patch(
            "src.components.sl_beyond_ob_shadow_logger.log_sl_beyond_ob_decision",
            side_effect=RuntimeError("forced error"),
        ):
            result = verify_candidate(pa, mso, _DEFAULT_CONFIG)

        assert result is not None
        assert isinstance(result.checks, list)
        sl_check = next(c for c in result.checks if c.name == "sl_beyond_ob")
        assert sl_check.status == "PASS"

    def test_config_gate_disabled_via_verify_candidate(
        self, _isolate_sl_beyond_ob_log,
    ):
        """End-to-end: config-disabled gate stops the logger writing
        even when verify_candidate calls it.
        """
        mso = _real_mso()
        pa = _real_analysis(direction="LONG", entry=2260.50, sl=2258.50)
        config = {
            **_DEFAULT_CONFIG,
            "shadow_loggers": {
                "sl_beyond_ob_decisions_logger": {"enabled": False},
            },
        }
        verify_candidate(pa, mso, config)

        log_file = _isolate_sl_beyond_ob_log
        assert not log_file.exists() or _read_log_rows(log_file) == []


def test_default_log_path_is_correct():
    """The module constant points at the expected production sink."""
    assert SHADOW_LOG_PATH == "shadow_logs/sl_beyond_ob_decisions.jsonl"
