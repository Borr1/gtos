"""SHORT-side R computation coverage — closes audit finding F12.

Why this file exists
--------------------
``SessionOrchestrator._compute_r`` (``src/components/orchestrator.py:10248-10255``)
branches on direction:

    LONG :  (price - entry) / sl_distance
    SHORT:  (entry - price) / sl_distance

The LONG branch is well covered — ``tests/test_exit_wiring.py`` carries
hand-computed ``actual_r`` assertions (+1.6429 at :405, +0.75 at :238, -1.0 at
:475) driven through the real ``_finalize_exit`` chain. Every ``actual_r``
assertion in the repository was ``direction="LONG"``, so a sign flip in the
SHORT branch flipped no assertion anywhere (SECOND_AUDIT.md §3.5, F12).

This file mirrors those three LONG cases on the SHORT side, plus the
``mfe_r``/``mae_r`` emissions that route through the same branch.

Every expected value below is **hand-computed from the geometry stated in the
test**, never read back from the implementation. Geometry is chosen so a sign
flip in the SHORT branch inverts the sign of every assertion:

    entry 3080.0 · stop 3087.0 · sl_distance 7.0   (SHORT: stop is ABOVE entry)

      exit 3068.5 -> (3080.0 - 3068.5) / 7.0 = +11.5/7 = +1.642857...
      exit 3087.0 -> (3080.0 - 3087.0) / 7.0 =  -7.0/7 = -1.0
      exit 3069.5 -> (3080.0 - 3069.5) / 7.0 = +10.5/7 = +1.5
      exit 3080.0 -> (3080.0 - 3080.0) / 7.0 =   0.0/7 =  0.0

The LONG mirror values are deliberately numerically identical in magnitude to
``test_exit_wiring.py``'s (+1.6429, +0.75, -1.0), so the two files read as one
pair and a future reader can see at a glance that the branches are symmetric.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.components import orchestrator as _orch_mod
from src.components.orchestrator import SessionOrchestrator
from src.components.trade_capture import create_trade_record, update_execution
from src.components.execution import TradeState


# Same isolation contract as tests/test_exit_wiring.py: redirect every
# trade_capture write away from knowledge_base/trade_records, and pin LOCK_DIR.
@pytest.fixture(autouse=True)
def _isolate_production_paths(tmp_path, monkeypatch):
    tmp_meta = tmp_path / "meta"
    tmp_meta.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(_orch_mod, "LOCK_DIR", str(tmp_meta))
    monkeypatch.chdir(tmp_path)
    yield


# --- SHORT geometry, stated once ------------------------------------------
SHORT_ENTRY = 3080.0
SHORT_STOP = 3087.0          # above entry, as a SHORT stop must be
SHORT_SL_DISTANCE = 7.0


# ---------------------------------------------------------------------------
# Helpers — mirrors of test_exit_wiring.py's, with SHORT geometry
# ---------------------------------------------------------------------------

def _make_orchestrator() -> SessionOrchestrator:
    orch = object.__new__(SessionOrchestrator)
    orch.config = {
        "market": {"symbol": "XAUUSD"},
        "trade_capture": {"enabled": True, "base_path": "knowledge_base/trade_records"},
    }
    orch._symbol = "XAUUSD"
    orch._mt5_symbol = "XAUUSD"
    orch.mt5 = MagicMock()
    orch.execution = MagicMock()
    orch._active_trade_record = None
    orch._active_trade_record_path = None
    orch._trade_entry_price = None
    orch._trade_direction = None
    orch._trade_sl_distance = None
    orch._trade_entry_time = None
    orch._mfe_price = None
    orch._mae_price = None
    orch._last_tick_price = None
    return orch


def _make_short_trade_state(**overrides) -> TradeState:
    defaults = dict(
        ticket=87654321,
        direction="SHORT",
        entry_price=SHORT_ENTRY,
        stop_loss=SHORT_STOP,
        take_profit_1=3068.5,
        take_profit_2=0,
        take_profit_3=0,
        initial_volume=0.10,
        current_volume=0.10,
        sl_distance=SHORT_SL_DISTANCE,
        trade_id="tr_2026-04-07_0745_short",
        entry_time="2026-04-07T07:45:00+00:00",
    )
    defaults.update(overrides)
    return TradeState(**defaults)


def _make_short_record_with_execution() -> dict:
    """A SHORT trade record with execution filled in.

    Deliberately carries no ``stop_loss``/``sl_distance`` under ``execution``,
    exactly like ``test_exit_wiring.py::_make_record_with_execution``. That
    makes ``_resolve_exit_sl_distance`` (orchestrator.py:10966-11026) fall
    through to ``trade_snapshot.sl_distance``, so the R denominator in every
    test below is the stated 7.0 and not something reconstructed.
    """
    record = create_trade_record(
        symbol="XAUUSD",
        kill_zone="london",
        candle_time="2026-04-07T07:45:00+00:00",
        mso={"timeframes": {}},
        prompt_system="sys",
        prompt_user="usr",
        ai_response={
            "decision": "CANDIDATE",
            "confidence_score": 80,
            "framework": "ob_retest",
            "reasoning": {"setup_grade": "A+"},
            "trade_parameters": {
                "direction": "SHORT",
                "entry_price": SHORT_ENTRY,
                "stop_loss": SHORT_STOP,
                "take_profit_1": 3068.5,
                "risk_reward_ratio": 1.5,
            },
        },
        cross_instrument_context="",
        session_memory="",
        config={"trade_capture": {"enabled": True, "save_mso": True, "save_prompt": True}},
    )
    update_execution(record, {
        "executed": True,
        "timestamp": "2026-04-07T07:45:12+00:00",
        "entry_price_actual": SHORT_ENTRY,
        "entry_spread": 0.25,
        "slippage": 0.10,
        "mt5_ticket": 87654321,
        "lot_size": 0.10,
        "risk_pct": 1.0,
    })
    record["decision_pipeline"]["final_outcome"] = "EXECUTED"
    return record


# ---------------------------------------------------------------------------
# 1. The branch itself, in isolation
# ---------------------------------------------------------------------------

class TestComputeRShortBranch:
    """orchestrator.py:10254-10255 — the SHORT arm of ``_compute_r``."""

    def _short_orch(self) -> SessionOrchestrator:
        orch = _make_orchestrator()
        orch._init_trade_tracking(_make_short_trade_state())
        return orch

    @pytest.mark.parametrize("price,expected_r", [
        # price          hand-computed (3080.0 - price) / 7.0
        (3068.5,  1.5 + 1.0 / 7.0),   # +11.5/7 = +1.6428571...
        (3069.5,  1.5),               # +10.5/7 = +1.5 exactly
        (3080.0,  0.0),               # at entry
        (3083.5, -0.5),               #  -3.5/7 = -0.5
        (3087.0, -1.0),               #  -7.0/7 = -1.0 (full stop)
        (3094.0, -2.0),               # -14.0/7 = -2.0 (twice the stop)
    ])
    def test_short_r_is_favourable_when_price_falls(self, price, expected_r):
        assert self._short_orch()._compute_r(price) == pytest.approx(expected_r, abs=1e-9)

    def test_price_below_entry_is_a_gain_for_a_short(self):
        """The single assertion a sign flip cannot survive."""
        orch = self._short_orch()
        assert orch._compute_r(SHORT_ENTRY - 7.0) > 0
        assert orch._compute_r(SHORT_ENTRY + 7.0) < 0

    def test_short_and_long_are_exact_mirrors(self):
        """Same distance from entry, opposite direction, opposite sign."""
        short = self._short_orch()

        long_orch = _make_orchestrator()
        long_orch._init_trade_tracking(_make_short_trade_state(
            direction="LONG",
            entry_price=SHORT_ENTRY,
            stop_loss=SHORT_ENTRY - SHORT_SL_DISTANCE,
        ))

        for offset in (0.5, 3.5, 7.0, 11.5, 21.0):
            assert short._compute_r(SHORT_ENTRY - offset) == pytest.approx(
                long_orch._compute_r(SHORT_ENTRY + offset), abs=1e-12
            )
            assert short._compute_r(SHORT_ENTRY + offset) == pytest.approx(
                -long_orch._compute_r(SHORT_ENTRY + offset), abs=1e-12
            )

    def test_zero_sl_distance_returns_zero_not_zero_division(self):
        """orchestrator.py:10249-10250 — the guard, exercised on the SHORT path."""
        orch = _make_orchestrator()
        orch._init_trade_tracking(_make_short_trade_state(sl_distance=0.0))
        assert orch._compute_r(3050.0) == 0.0


# ---------------------------------------------------------------------------
# 2. Through the real _finalize_exit chain — mirrors of the three LONG cases
# ---------------------------------------------------------------------------

class TestShortFullCloseR:
    """Mirror of test_exit_wiring.py:405 (+1.6429) on the SHORT side."""

    def test_short_tp1_full_close_r(self):
        orch = _make_orchestrator()
        ts = _make_short_trade_state()
        ts.partial_close_events = [{
            "type": "TP1_FULL_CLOSE",
            "time": "2026-04-07T08:30:00+00:00",
            "price": 3068.5,
            "volume_closed": 0.10,
        }]

        record = _make_short_record_with_execution()
        orch._init_trade_tracking(ts)
        orch._active_trade_record = record
        orch._active_trade_record_path = "/tmp/fake"
        orch._last_tick_price = 3068.5

        with patch("src.components.orchestrator.save_trade_record"):
            orch._finalize_exit(ts, "tp1_full_close")

        # (3080.0 - 3068.5) / 7.0 = +1.642857...
        assert record["exit"]["actual_r"] == pytest.approx(1.6429, abs=0.01)
        assert record["exit"]["exit_price"] == 3068.5
        assert record["exit"]["exit_type"] == "tp1_full_close"
        # Pin the denominator too, so a future change to _resolve_exit_sl_distance
        # cannot silently move these numbers.
        assert record["exit"]["r_sl_distance"] == pytest.approx(7.0, abs=1e-9)


class TestShortSLExitRIsNegative:
    """Mirror of test_exit_wiring.py:475 (-1.0) on the SHORT side."""

    def test_short_sl_r(self):
        orch = _make_orchestrator()
        ts = _make_short_trade_state()
        ts.partial_close_events = []

        record = _make_short_record_with_execution()
        orch._init_trade_tracking(ts)
        orch._active_trade_record = record
        orch._active_trade_record_path = "/tmp/fake"
        orch._last_tick_price = SHORT_STOP  # stop hit, price rose against us

        with patch("src.components.orchestrator.save_trade_record"):
            orch._finalize_exit(ts, "broker_closed")

        # (3080.0 - 3087.0) / 7.0 = -1.0
        assert record["exit"]["actual_r"] == pytest.approx(-1.0, abs=0.01)
        assert record["exit"]["exit_type"] == "broker_closed"


class TestShortBlendedPartialR:
    """Mirror of test_exit_wiring.py:238 (+0.75 blended) on the SHORT side."""

    def test_short_blended_r(self):
        orch = _make_orchestrator()
        ts = _make_short_trade_state(current_volume=0.05)
        ts.partial_close_events = [
            {
                "type": "TP1_PARTIAL",
                "time": "2026-04-07T08:15:00+00:00",
                "price": 3069.5,      # (3080.0 - 3069.5)/7.0 = +1.5R
                "volume_closed": 0.05,
            },
            {
                "type": "CLOSE_TIMEOUT_2H",
                "time": "2026-04-07T10:00:00+00:00",
            },
        ]

        record = _make_short_record_with_execution()
        orch._init_trade_tracking(ts)
        orch._active_trade_record = record
        orch._active_trade_record_path = "/tmp/fake"
        orch._last_tick_price = SHORT_ENTRY  # final half closes at breakeven, 0R

        with patch("src.components.orchestrator.save_trade_record"):
            orch._finalize_exit(ts, "timeout_2h")

        # 50% at +1.5R + 50% at 0R = +0.75R
        assert record["exit"]["actual_r"] == pytest.approx(0.75, abs=0.01)
        assert record["exit"]["partial_closes"][0]["r_at_close"] == pytest.approx(1.5, abs=0.01)
        assert record["exit"]["partial_closes"][0]["pct_closed"] == pytest.approx(0.5, abs=1e-9)


# ---------------------------------------------------------------------------
# 3. mfe_r / mae_r — same branch, separate emission sites
# ---------------------------------------------------------------------------

class TestShortMFEMAERSigns:
    """orchestrator.py:11513-11515 — mfe_r/mae_r also route through _compute_r.

    For a SHORT, the *most favourable* excursion is the LOWEST price and must
    emit a POSITIVE mfe_r; the *most adverse* is the HIGHEST price and must emit
    a NEGATIVE mae_r. A sign flip inverts both.
    """

    def test_short_mfe_mae_r(self):
        orch = _make_orchestrator()
        ts = _make_short_trade_state()
        ts.partial_close_events = []

        record = _make_short_record_with_execution()
        orch._init_trade_tracking(ts)
        orch._active_trade_record = record
        orch._active_trade_record_path = "/tmp/fake"

        orch._update_mfe_mae(3066.0)   # favourable for a SHORT
        orch._update_mfe_mae(3083.5)   # adverse for a SHORT
        assert orch._mfe_price == 3066.0
        assert orch._mae_price == 3083.5

        orch._last_tick_price = 3080.0
        with patch("src.components.orchestrator.save_trade_record"):
            orch._finalize_exit(ts, "timeout_2h")

        # mfe: (3080.0 - 3066.0)/7.0 = +2.0
        # mae: (3080.0 - 3083.5)/7.0 = -0.5
        assert record["exit"]["mfe_r"] == pytest.approx(2.0, abs=1e-4)
        assert record["exit"]["mae_r"] == pytest.approx(-0.5, abs=1e-4)
        assert record["exit"]["mfe_r"] > 0
        assert record["exit"]["mae_r"] < 0


# ---------------------------------------------------------------------------
# 4. The exit record's R must agree with the cash the geometry implies
# ---------------------------------------------------------------------------

class TestShortRAgreesWithPriceGeometry:
    """Recompute R from the persisted prices alone and require agreement.

    This is the per-trade form of the shadow-reducer check: take
    ``exit_price``, ``entry_price`` and ``r_sl_distance`` out of the finished
    record and re-derive R without calling ``_compute_r`` at all.
    """

    @pytest.mark.parametrize("exit_price", [3068.5, 3074.0, 3080.0, 3083.5, 3087.0])
    def test_persisted_r_matches_independent_recomputation(self, exit_price):
        orch = _make_orchestrator()
        ts = _make_short_trade_state()
        ts.partial_close_events = []

        record = _make_short_record_with_execution()
        orch._init_trade_tracking(ts)
        orch._active_trade_record = record
        orch._active_trade_record_path = "/tmp/fake"
        orch._last_tick_price = exit_price

        with patch("src.components.orchestrator.save_trade_record"):
            orch._finalize_exit(ts, "timeout_2h")

        persisted_r = record["exit"]["actual_r"]
        persisted_exit = record["exit"]["exit_price"]
        persisted_denominator = record["exit"]["r_sl_distance"]

        # Independent recomputation: a SHORT gains when price falls.
        independent_r = (SHORT_ENTRY - persisted_exit) / persisted_denominator

        assert persisted_r == pytest.approx(independent_r, abs=1e-4)
