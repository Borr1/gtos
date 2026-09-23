"""sl_beyond_ob — precision-aware snap + tick_size production-config tests.

The Wave-1 sister-bug audit (research/sister_bug_audit_2026-04-27)
patched four downstream sites that compared AI-emitted prices against
unrendered MSO floats (entry_in_breaker, entry_in_fvg, m5_refinement).
``_check_sl_beyond_ob`` was listed at the time as "safe by audit"
because the ADR-006 tick floor was assumed to absorb any sub-tick
rendering delta.

The 2026-04-28 SL_BUFFER_AUDIT (cf.
``research/a4_trending_bull_replay_2026-04-28/``) re-tested that
assumption against the trending_bull replay cohort and found:

  1. The default 1-tick floor and the tight-FX 5-8-tick floor both
     leave residual edge cases when the underlying ``OrderBlock.low``
     carries an extra decimal beyond what the AI was shown.
  2. Six XAUUSD live trades on 2026-04-15 / 2026-04-16 hit
     ``sl_beyond_ob: FAIL`` deterministically when AI emitted SL at
     the rendered OB.low (then sl_buffer_applied:0.0 — FA-2 fixed
     that emission, but the verification gate would still reject the
     same geometry without the snap).
  3. ``XAUUSD`` and 5 sister instruments lacked a ``market.tick_size``
     in agent_config.yaml; the silent fallback to ``1e-5`` reduced the
     1-tick floor to a sub-tick noise threshold.

This module pins three behaviors the fix delivers:

  * :class:`TestSlBeyondObPrecisionSnap` — every (instrument × direction
    × boundary-condition) combination behaves correctly when the MSO
    underlying carries an extra decimal beyond display precision.
  * :class:`TestSlBeyondObTickSizeProductionConfig` — the production
    config (after FN profile overlay) resolves a per-instrument tick
    that yields a meaningful tick floor — regression protection that
    fails loudly if a future commit removes any of the six tick_size
    pins.
  * :class:`TestSlBeyondObXauusdHistoricalRegression` — the six 2026-04
    XAUUSD trades that originally failed the strict-binary gate STILL
    fail the precision-aware gate (the post-FA-2 prompt would never
    emit ``sl_buffer_applied:0.0`` again, but if it ever regresses the
    gate must still catch it).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from src.components.verification import _check_sl_beyond_ob, _sl_beyond_floor
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
from src.models.market_state_models import OrderBlock
from src.utils.config import apply_instrument_overrides, apply_profile_overrides

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_AGENT_CONFIG = _PROJECT_ROOT / "config" / "agent_config.yaml"


# ---------------------------------------------------------------------------
# Fixture builders (mirror tests/test_verification_sl_beyond_ob_tolerance.py
# pattern at line 134)
# ---------------------------------------------------------------------------

def _make_pa(direction: str, entry: float, sl: float, tp1: float) -> PrimaryAnalysisOutput:
    """Build a minimal CANDIDATE with the gate-relevant trade_parameters."""
    risk = abs(entry - sl) or 1.0
    reward = abs(tp1 - entry)
    rr = reward / risk if risk else 1.5
    return PrimaryAnalysisOutput(
        timestamp_utc="2026-04-28T08:00:00Z",
        model_used="test",
        decision="CANDIDATE",
        confidence_score=80,
        framework="ob_retest",
        kill_zone="ny",
        reasoning=PrimaryAnalysisReasoning(
            daily_bias=DailyBiasAnalysis(direction="bullish", confidence="high"),
            h4_alignment=H4AlignmentAnalysis(aligned=True),
            h1_setup=H1SetupAnalysis(
                poi_identified=True,
                poi_type="OB",
                poi_price_level=entry,
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
            risk_reward_ratio=rr,
        ),
    )


def _make_ob(low: float, high: float, direction: str = "bullish") -> OrderBlock:
    """Build a minimal OrderBlock. Only low/high matter for the gate."""
    return OrderBlock(
        type=direction,
        low=low,
        high=high,
        open=low,
        close=high,
        formation_index=10,
        formation_time="2026-04-28T08:00:00+00:00",
        causing_bos_index=11,
        mitigated=False,
        causing_event_type="BOS",
        touch_count=1,
    )


def _config(
    tick_size: float,
    floor_ticks: int = 1,
    price_format: str = ".2f",
) -> dict:
    """Synthetic config covering the keys the gate reads."""
    return {
        "market": {"tick_size": tick_size},
        "verification": {"sl_beyond_ob_tick_floor": floor_ticks},
        "prompt": {"price_format": price_format},
    }


# ---------------------------------------------------------------------------
# Per-instrument synthetic configs (mirror live profiles + ADR-006 overrides)
# ---------------------------------------------------------------------------

# All 7 instruments needed for the precision-snap matrix. Tick / floor /
# format chosen to mirror what production resolves under the FN profile
# overlay. Where the production floor is >1 (tight-FX 8 ticks), the
# precision-snap interaction with the floor is exercised separately.
_INSTRUMENT_PROFILES = {
    "XAUUSD": {"tick_size": 0.01, "floor_ticks": 1, "price_format": ".2f"},
    "US30_cash": {"tick_size": 0.10, "floor_ticks": 1, "price_format": ".2f"},
    "NAS100": {"tick_size": 0.10, "floor_ticks": 1, "price_format": ".1f"},
    "XAGUSD": {"tick_size": 0.001, "floor_ticks": 1, "price_format": ".3f"},
    "GBPJPY": {"tick_size": 0.001, "floor_ticks": 1, "price_format": ".3f"},
    "EURUSD": {"tick_size": 0.00001, "floor_ticks": 8, "price_format": ".5f"},
    "USDJPY": {"tick_size": 0.001, "floor_ticks": 5, "price_format": ".3f"},
}

# Geometry per instrument: the OB high/low pair lives one extra digit
# beyond display precision so the snap is a non-trivial round (e.g.
# XAUUSD .2f display + underlying carries .3f → snap moves the
# comparison plane). The "extra" digit is set so floor(low * 10^N) at
# N=display rounds DOWN, which is the case where the snap matters most
# (snap moves zone_low DOWN, making the LONG-side comparison stricter
# at the boundary).
_INSTRUMENT_GEOMETRY = {
    # OB.low underlying carries 1 extra decimal beyond the AI's display
    # plane. .2f rendering of 4762.144 = "4762.14"; AI sees 4762.14;
    # snap moves zone_low 4762.144 → 4762.14 for the gate comparison.
    "XAUUSD": {"ob_low": 4762.144, "ob_high": 4777.434},
    "US30_cash": {"ob_low": 38500.124, "ob_high": 38525.764},
    # NAS100 .1f: underlying 27262.16 → display 27262.2 (rounded UP),
    # so use a value where rounding goes DOWN to keep the LONG snap
    # tightening (zone_low decreases).
    "NAS100": {"ob_low": 18000.14, "ob_high": 18020.34},
    "XAGUSD": {"ob_low": 32.4324, "ob_high": 32.5824},
    "GBPJPY": {"ob_low": 187.4624, "ob_high": 187.6224},
    # EURUSD 5dp display is the underlying; geometry kept aligned.
    "EURUSD": {"ob_low": 1.10500, "ob_high": 1.10600},
    "USDJPY": {"ob_low": 150.5004, "ob_high": 150.8004},
}


def _display_decimals(price_format: str) -> int:
    """Return the trailing decimal count from a ``.Nf`` format spec."""
    return int(price_format.lstrip(".").rstrip("f"))


def _snapped_low(instrument: str) -> float:
    """The post-snap zone_low value the gate will use for comparison."""
    geom = _INSTRUMENT_GEOMETRY[instrument]
    decimals = _display_decimals(_INSTRUMENT_PROFILES[instrument]["price_format"])
    # Mirror precision._snap_to_precision via Decimal HALF_UP.
    from decimal import Decimal, ROUND_HALF_UP
    quantum = Decimal(10) ** -decimals
    return float(Decimal(str(geom["ob_low"])).quantize(quantum, rounding=ROUND_HALF_UP))


def _snapped_high(instrument: str) -> float:
    geom = _INSTRUMENT_GEOMETRY[instrument]
    decimals = _display_decimals(_INSTRUMENT_PROFILES[instrument]["price_format"])
    from decimal import Decimal, ROUND_HALF_UP
    quantum = Decimal(10) ** -decimals
    return float(Decimal(str(geom["ob_high"])).quantize(quantum, rounding=ROUND_HALF_UP))


# ---------------------------------------------------------------------------
# TestSlBeyondObPrecisionSnap — 7 instruments × 2 directions × 3 conditions
# ---------------------------------------------------------------------------

class TestSlBeyondObPrecisionSnap:
    """Precision-snap matrix.

    Per (instrument, direction):
      * ``sl_at_rendered_boundary``: SL exactly at rendered (snapped)
        OB extreme. Gate rejects (clearance == 0 < floor).
      * ``sl_one_tick_beyond``: SL at rendered extreme - 1 tick
        (LONG) / + 1 tick (SHORT). Gate accepts when floor==1; gate
        rejects when floor > 1 (tight-FX). The specific boundary
        depends on per-instrument floor.
      * ``sl_one_tick_inside``: SL at rendered extreme + 1 tick
        (LONG) / - 1 tick (SHORT). Always rejected (geometrically
        inside the zone).

    Total: 7 × 2 × 3 = 42 cases.
    """

    @pytest.mark.parametrize("instrument", list(_INSTRUMENT_PROFILES.keys()))
    @pytest.mark.parametrize("direction", ["LONG", "SHORT"])
    def test_sl_at_rendered_boundary_fails(self, instrument, direction):
        """SL exactly at the rendered (snapped) OB boundary → FAIL.

        Verifies the snap is applied: without it, comparison would be
        against the unrendered underlying and the AI's emission at the
        rendered boundary would NEITHER pass NOR fail consistently —
        depending on the unrendered float's parity, the gate would
        sometimes accept (when the unrendered low is HIGHER than display)
        and sometimes reject (when it's LOWER).
        """
        profile = _INSTRUMENT_PROFILES[instrument]
        geom = _INSTRUMENT_GEOMETRY[instrument]
        config = _config(**profile)
        ob = _make_ob(
            low=geom["ob_low"], high=geom["ob_high"],
            direction="bullish" if direction == "LONG" else "bearish",
        )

        # SL placed exactly at rendered (snapped) boundary
        snapped_low = _snapped_low(instrument)
        snapped_high = _snapped_high(instrument)
        if direction == "LONG":
            sl = snapped_low
            entry = snapped_low + 5 * profile["tick_size"]
            tp1 = snapped_high + 10 * profile["tick_size"]
        else:
            sl = snapped_high
            entry = snapped_high - 5 * profile["tick_size"]
            tp1 = snapped_low - 10 * profile["tick_size"]

        analysis = _make_pa(direction, entry=entry, sl=sl, tp1=tp1)
        result = _check_sl_beyond_ob(analysis, ob, None, config)
        assert result.status == "FAIL", (
            f"{instrument} {direction} SL at rendered boundary should FAIL: "
            f"{result.detail}"
        )

    @pytest.mark.parametrize("instrument", list(_INSTRUMENT_PROFILES.keys()))
    @pytest.mark.parametrize("direction", ["LONG", "SHORT"])
    def test_sl_one_tick_beyond_rendered(self, instrument, direction):
        """SL one floor-tick beyond rendered boundary → PASS.

        Floor is per-instrument: 1 tick for the broad-scale instruments,
        8 ticks for tight-FX EURUSD, 5 ticks for USDJPY. We place SL
        exactly ``floor_ticks`` ticks beyond, which is the gate's
        tightest accept condition. NB: 1-ULP FP rounding makes
        EXACTLY-floor-ticks an edge case; we add 1 extra tick to keep
        the comparison unambiguous (mirrors the
        test_verification_sl_beyond_ob_tolerance pattern at line 285).
        """
        profile = _INSTRUMENT_PROFILES[instrument]
        geom = _INSTRUMENT_GEOMETRY[instrument]
        config = _config(**profile)
        ob = _make_ob(
            low=geom["ob_low"], high=geom["ob_high"],
            direction="bullish" if direction == "LONG" else "bearish",
        )

        # +1 extra tick beyond the floor avoids the 1-ULP FP edge case
        # documented in test_verification_sl_beyond_ob_tolerance::test_quantization_xauusd.
        clearance_ticks = profile["floor_ticks"] + 1
        snapped_low = _snapped_low(instrument)
        snapped_high = _snapped_high(instrument)
        if direction == "LONG":
            sl = snapped_low - clearance_ticks * profile["tick_size"]
            entry = snapped_low + 5 * profile["tick_size"]
            tp1 = snapped_high + 10 * profile["tick_size"]
        else:
            sl = snapped_high + clearance_ticks * profile["tick_size"]
            entry = snapped_high - 5 * profile["tick_size"]
            tp1 = snapped_low - 10 * profile["tick_size"]

        analysis = _make_pa(direction, entry=entry, sl=sl, tp1=tp1)
        result = _check_sl_beyond_ob(analysis, ob, None, config)
        assert result.status == "PASS", (
            f"{instrument} {direction} SL {clearance_ticks} ticks beyond "
            f"rendered boundary should PASS: {result.detail}"
        )

    @pytest.mark.parametrize("instrument", list(_INSTRUMENT_PROFILES.keys()))
    @pytest.mark.parametrize("direction", ["LONG", "SHORT"])
    def test_sl_one_tick_inside_rendered(self, instrument, direction):
        """SL one tick inside the rendered boundary → FAIL (geometrically wrong)."""
        profile = _INSTRUMENT_PROFILES[instrument]
        geom = _INSTRUMENT_GEOMETRY[instrument]
        config = _config(**profile)
        ob = _make_ob(
            low=geom["ob_low"], high=geom["ob_high"],
            direction="bullish" if direction == "LONG" else "bearish",
        )

        snapped_low = _snapped_low(instrument)
        snapped_high = _snapped_high(instrument)
        if direction == "LONG":
            sl = snapped_low + 1 * profile["tick_size"]
            entry = snapped_low + 5 * profile["tick_size"]
            tp1 = snapped_high + 10 * profile["tick_size"]
        else:
            sl = snapped_high - 1 * profile["tick_size"]
            entry = snapped_high - 5 * profile["tick_size"]
            tp1 = snapped_low - 10 * profile["tick_size"]

        analysis = _make_pa(direction, entry=entry, sl=sl, tp1=tp1)
        result = _check_sl_beyond_ob(analysis, ob, None, config)
        assert result.status == "FAIL", (
            f"{instrument} {direction} SL 1 tick inside rendered boundary "
            f"should FAIL: {result.detail}"
        )


# ---------------------------------------------------------------------------
# TestSlBeyondObTickSizeProductionConfig — production-config regression test
# ---------------------------------------------------------------------------

class TestSlBeyondObTickSizeProductionConfig:
    """Verify the FN-profile resolved config exposes a meaningful tick.

    These tests fail loudly if a future commit removes any of the six
    instrument tick_size pins added 2026-04-28 (SL_BUFFER_AUDIT). The
    silent fallback to ``prompt.tick_size_fallback`` (``1e-5``) reduces
    the 1-tick ADR-006 floor to a sub-cent noise threshold for indices
    and metals, defeating the gate's purpose.
    """

    @staticmethod
    def _resolved_config(symbol: str) -> dict:
        with open(_AGENT_CONFIG, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        cfg_fn = apply_profile_overrides(cfg, "redacted_account")
        return apply_instrument_overrides(cfg_fn, symbol)

    @pytest.mark.parametrize(
        "symbol,expected_min_floor",
        [
            ("XAUUSD", 0.01),
            ("US30", 0.10),
            ("US30_cash", 0.10),
            ("NAS100", 0.10),
            ("XAGUSD", 0.001),
            ("GBPJPY", 0.001),
        ],
    )
    def test_resolved_floor_exceeds_expected_minimum(self, symbol, expected_min_floor):
        """The post-FN production config resolves a non-default tick floor.

        Pre-fix: ``XAUUSD`` (and the other 5) had no ``market.tick_size``,
        so ``_sl_beyond_floor`` fell through to the ``1e-5`` fallback,
        yielding a floor of 1e-5 regardless of ``floor_ticks``. The fix
        adds explicit ``tick_size`` pins so the floor is 1 instrument
        tick (or 5/8 ticks tight-FX, but those already had pins).
        """
        config = self._resolved_config(symbol)
        floor = _sl_beyond_floor(price=1.0, config=config)
        assert floor >= expected_min_floor, (
            f"{symbol} resolved floor {floor!r} < expected_min "
            f"{expected_min_floor}; tick_size pin removed?"
        )

    def test_resolved_xauusd_tick_size_in_config(self):
        """Direct inspection: XAUUSD's resolved market.tick_size is 0.01."""
        config = self._resolved_config("XAUUSD")
        assert config["market"]["tick_size"] == pytest.approx(0.01)

    def test_resolved_nas100_tick_size_in_config(self):
        """Direct inspection: NAS100's resolved market.tick_size is 0.10."""
        config = self._resolved_config("NAS100")
        assert config["market"]["tick_size"] == pytest.approx(0.10)


# ---------------------------------------------------------------------------
# TestSlBeyondObXauusdHistoricalRegression — A4 cohort regression protection
# ---------------------------------------------------------------------------

# The 6 historical XAUUSD trades from 2026-04-15 / 2026-04-16 that
# originally failed sl_beyond_ob with ``sl_buffer_applied: 0.0`` (the
# bug FA-2 fixed prompt-side; see SL_BUFFER_AUDIT). The post-fix gate
# must STILL FAIL these specific geometries — even though the post-FA-2
# prompt would never emit them again, regression protection ensures
# any future prompt revision that re-introduces the zero-buffer pattern
# is caught by the verifier rather than silently shipped to broker.
_A4_HISTORICAL_CASES = [
    # (label, entry, stop_loss, ob_low, ob_high, sl_buffer_applied)
    ("2026-04-15_ny_1315", 4777.43, 4762.14, 4762.14, 4777.43, 0.0),
    ("2026-04-15_ny_1330", 4777.43, 4762.14, 4762.14, 4777.43, 0.0),
    ("2026-04-15_ny_1345", 4777.43, 4762.14, 4762.14, 4777.43, 0.0),
    ("2026-04-15_ny_1615", 4777.43, 4762.14, 4762.14, 4777.43, 0.0),
    ("2026-04-15_ny_1700", 4777.43, 4762.14, 4762.14, 4777.43, 0.0),
    ("2026-04-16_london_0800", 4796.28, 4787.44, 4787.44, 4796.28, 0.0),
]


class TestSlBeyondObXauusdHistoricalRegression:
    """The 6 A4 historical CANDIDATEs that hit sl_buffer_applied:0.0
    must continue to fail sl_beyond_ob under the precision-aware gate.

    These were live production trades on 2026-04-15 / 2026-04-16 that
    L2-rejected as REJECTED_L2 (sl_beyond_ob) per the trade records at
    ``knowledge_base/trade_records/XAUUSD/``. The bug was AI-side
    (zero buffer); FA-2 (commit ``fa35cc0``) fixed the prompt. This
    test class is REGRESSION PROTECTION — the fix landed in the prompt,
    but the L2 gate is the safety net. If the prompt regresses, the
    gate must still catch the geometry.
    """

    @pytest.mark.parametrize(
        "label,entry,sl,ob_low,ob_high,sl_buffer_applied",
        _A4_HISTORICAL_CASES,
        ids=[c[0] for c in _A4_HISTORICAL_CASES],
    )
    def test_historical_sl_at_ob_low_still_fails(
        self, label, entry, sl, ob_low, ob_high, sl_buffer_applied
    ):
        """SL exactly at OB.low (sl_buffer_applied==0) must FAIL."""
        # Use XAUUSD config (production: 0.01 tick, 1-tick floor, .2f).
        config = _config(tick_size=0.01, floor_ticks=1, price_format=".2f")
        # OB.low is bit-exact-equal to the AI-emitted SL; no precision
        # delta between underlying and rendered. Snap is a no-op here;
        # the gate rejects on the ADR-006 tick-floor (sl > ob_low - floor
        # because sl == ob_low > ob_low - 0.01).
        ob = _make_ob(low=ob_low, high=ob_high, direction="bullish")
        tp1 = entry + 1.5 * abs(entry - sl)  # Fabricate plausible TP1
        analysis = _make_pa("LONG", entry=entry, sl=sl, tp1=tp1)
        result = _check_sl_beyond_ob(analysis, ob, None, config)
        assert result.status == "FAIL", (
            f"A4 historical case {label} should still FAIL "
            f"(sl_buffer_applied={sl_buffer_applied} → SL == OB.low geometrically): "
            f"{result.detail}"
        )

    def test_historical_with_proper_buffer_passes(self):
        """Counterfactual: the same geometry with a proper $0.02 buffer
        (post-FA-2 emission shape) PASSES the gate.

        Validates the precision-snap path doesn't accidentally tighten
        the gate beyond the ADR-006 tick floor — the floor remains the
        load-bearing tolerance for legitimate emissions.
        """
        config = _config(tick_size=0.01, floor_ticks=1, price_format=".2f")
        ob = _make_ob(low=4762.14, high=4777.43, direction="bullish")
        # SL $0.02 below boundary → 2-tick clearance → unambiguous PASS
        # (mirrors test_verification_sl_beyond_ob_tolerance::test_quantization_xauusd).
        analysis = _make_pa("LONG", entry=4777.43, sl=4762.12, tp1=4800.00)
        result = _check_sl_beyond_ob(analysis, ob, None, config)
        assert result.status == "PASS", (
            f"Post-FA-2 emission shape (proper buffer) should PASS: {result.detail}"
        )
