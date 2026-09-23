"""Unit tests for ``src/research_infra/dumb_baseline.py``.

Coverage targets (A1 brief):

  1. ``compute_mechanical_entry`` — hand-verified on 3 synthetic OB shapes
     (one bullish OB / LONG, one bearish OB / SHORT, one all-mitigated edge case).
  2. ``compute_mechanical_entry`` — sl_buffer floor (atr_mult vs min_ticks).
  3. ``compute_mechanical_entry`` — non-OB framework returns skip_reason.
  4. ``compute_mechanical_entry`` — TP from swing vs rr_floor fallback.
  5. ``resolve_mechanical_outcome`` — TP-hit, SL-hit, TIMEOUT scenarios on synthetic OHLCV.
  6. ``resolve_mechanical_outcome`` — SL-first conservative rule on a both-hit bar.
  7. End-to-end replay on a 5-CAND fixture set: result rows + aggregate.
  8. Realized-R join: 3 of 5 CANDs match trade records → those rows have
     ai_realized_r set; 2 None.
  9. ``aggregate`` produces the strategic verdict block with required keys.
 10. ``run_a1_dumb_baseline.py --dry-run`` prints plan, exits 0, writes nothing.

All tests use ``tmp_path`` for output isolation — the conftest production-write
guard blocks writes to ``research/`` from the pytest process so the
runner's default sink must be redirected to ``tmp_path`` per test.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping

import pytest

import src.research_infra.dumb_baseline as db
from src.research_infra.dumb_baseline import (
    BaselineConfig,
    DumbBaselineReplay,
    HARNESS_VERSION,
    MechanicalOutcome,
    MechanicalSetup,
    aggregate,
    compute_mechanical_entry,
    resolve_mechanical_outcome,
    write_report_md,
    write_results_jsonl,
    write_summary_json,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc(year: int, month: int, day: int, hour: int = 12, minute: int = 0) -> dt.datetime:
    return dt.datetime(year, month, day, hour, minute, tzinfo=dt.timezone.utc)


def _mso_with_h1(
    obs: List[Mapping[str, Any]],
    swings: List[Mapping[str, Any]] | None = None,
    atr_14: float = 1.0,
) -> Dict[str, Any]:
    return {
        "timeframes": {
            "H1": {
                "order_blocks": list(obs),
                "swings": list(swings or []),
                "atr_14": atr_14,
            }
        }
    }


# ---------------------------------------------------------------------------
# 1. compute_mechanical_entry — bullish OB / LONG
# ---------------------------------------------------------------------------


def test_long_bullish_ob_canonical_80pct_retrace():
    """Bullish OB high=100, low=90 → LONG entry at 90 + 0.8*10 = 98."""
    ob = {
        "type": "bullish",
        "high": 100.0,
        "low": 90.0,
        "formation_time": "2026-04-01T08:00:00",
        "mitigated": False,
    }
    swing = {
        "type": "high",
        "price": 110.0,
        "time": "2026-04-01T10:00:00",
    }
    mso = _mso_with_h1([ob], [swing], atr_14=2.0)
    setup = compute_mechanical_entry(
        mso,
        side="LONG",
        symbol="XAUUSD",
        candle_close_time=_utc(2026, 4, 5, 13, 15),
        framework="ob_retest",
        cfg=BaselineConfig(sl_buffer_atr_multiplier=0.25, sl_buffer_min_ticks=5),
    )
    assert setup.skip_reason is None, setup.skip_reason
    assert setup.side == "LONG"
    # 80% retrace into bullish OB: enter near OB top
    assert setup.entry == pytest.approx(98.0, rel=1e-4)
    # Buffer = max(0.25 * 2.0 = 0.5, 5 * 0.01 = 0.05) = 0.5
    assert setup.sl_buffer_used == pytest.approx(0.5, rel=1e-4)
    # SL = OB low - buffer = 90 - 0.5 = 89.5
    assert setup.sl == pytest.approx(89.5, rel=1e-4)
    # SL distance = 98 - 89.5 = 8.5
    # Swing TP candidate at 110: implied RR = (110 - 98) / 8.5 = 1.41 < 1.5 → fallback
    # rr_floor TP = 98 + 1.5 * 8.5 = 110.75
    assert setup.tp == pytest.approx(110.75, rel=1e-4)
    assert setup.tp_source == "rr_floor"
    assert setup.rr == pytest.approx(1.5, rel=1e-3)


def test_long_uses_swing_tp_when_implied_rr_meets_floor():
    """If a swing high gives RR ≥ 1.5, use the swing as TP."""
    ob = {
        "type": "bullish",
        "high": 100.0,
        "low": 90.0,
        "formation_time": "2026-04-01T08:00:00",
        "mitigated": False,
    }
    # Swing at 120 → RR = (120-98)/8.5 = 2.59 (well above 1.5)
    swing = {
        "type": "high",
        "price": 120.0,
        "time": "2026-04-01T10:00:00",
    }
    mso = _mso_with_h1([ob], [swing], atr_14=2.0)
    setup = compute_mechanical_entry(
        mso,
        side="LONG",
        symbol="XAUUSD",
        candle_close_time=_utc(2026, 4, 5, 13, 15),
        framework="ob_retest",
    )
    assert setup.skip_reason is None
    assert setup.tp == pytest.approx(120.0, rel=1e-4)
    assert setup.tp_source == "swing"


# ---------------------------------------------------------------------------
# 2. compute_mechanical_entry — bearish OB / SHORT
# ---------------------------------------------------------------------------


def test_short_bearish_ob_canonical_80pct_retrace():
    """Bearish OB high=200, low=190 → SHORT entry at 200 - 0.8*10 = 192."""
    ob = {
        "type": "bearish",
        "high": 200.0,
        "low": 190.0,
        "formation_time": "2026-04-01T08:00:00",
        "mitigated": False,
    }
    swing = {
        "type": "low",
        "price": 180.0,
        "time": "2026-04-01T09:00:00",
    }
    mso = _mso_with_h1([ob], [swing], atr_14=4.0)
    setup = compute_mechanical_entry(
        mso,
        side="SHORT",
        symbol="USDJPY",
        candle_close_time=_utc(2026, 4, 5, 13, 15),
        framework="ob_retest",
        cfg=BaselineConfig(sl_buffer_atr_multiplier=0.25, sl_buffer_min_ticks=5),
    )
    assert setup.skip_reason is None, setup.skip_reason
    assert setup.side == "SHORT"
    # 80% retrace into bearish OB: enter near OB bottom
    assert setup.entry == pytest.approx(192.0, rel=1e-4)
    # Buffer = max(0.25 * 4 = 1.0, 5 * 0.001 = 0.005) = 1.0
    assert setup.sl_buffer_used == pytest.approx(1.0, rel=1e-4)
    # SL = OB high + buffer = 200 + 1 = 201
    assert setup.sl == pytest.approx(201.0, rel=1e-4)
    # SL distance = 9 ; swing tp = 180 → RR = (192-180)/9 = 1.333 < 1.5 → rr_floor
    # rr_floor TP = 192 - 1.5*9 = 178.5
    assert setup.tp == pytest.approx(178.5, rel=1e-4)


# ---------------------------------------------------------------------------
# 3. Edge cases — mitigated / wrong-side / unsupported framework
# ---------------------------------------------------------------------------


def test_skips_when_all_obs_mitigated():
    obs = [
        {
            "type": "bullish",
            "high": 100.0, "low": 90.0,
            "formation_time": "2026-04-01T08:00:00",
            "mitigated": True,
        }
    ]
    mso = _mso_with_h1(obs, atr_14=2.0)
    setup = compute_mechanical_entry(
        mso, "LONG", symbol="XAUUSD",
        candle_close_time=_utc(2026, 4, 5, 13, 15),
    )
    assert setup.skip_reason == "ALL_MITIGATED"


def test_skips_when_no_matching_side_ob():
    """For a LONG, a bearish OB should be ignored."""
    obs = [
        {
            "type": "bearish", "high": 100.0, "low": 90.0,
            "formation_time": "2026-04-01T08:00:00", "mitigated": False,
        }
    ]
    mso = _mso_with_h1(obs, atr_14=2.0)
    setup = compute_mechanical_entry(
        mso, "LONG", symbol="XAUUSD",
        candle_close_time=_utc(2026, 4, 5, 13, 15),
    )
    assert setup.skip_reason in {"NO_BULLISH_OB", "NO_OBS"}


def test_unsupported_framework_skips():
    """fvg_fill / breaker_re_entry are out of scope for A1."""
    obs = [
        {"type": "bullish", "high": 100, "low": 90,
         "formation_time": "2026-04-01T08:00:00", "mitigated": False}
    ]
    mso = _mso_with_h1(obs, atr_14=2.0)
    setup = compute_mechanical_entry(
        mso, "LONG", symbol="XAUUSD",
        candle_close_time=_utc(2026, 4, 5, 13, 15),
        framework="fvg_fill",
    )
    assert setup.skip_reason == "UNSUPPORTED_FRAMEWORK"


def test_invalid_side_skips():
    obs = [{"type": "bullish", "high": 100, "low": 90,
            "formation_time": "2026-04-01T08:00:00", "mitigated": False}]
    mso = _mso_with_h1(obs, atr_14=2.0)
    setup = compute_mechanical_entry(
        mso, "WRONG", symbol="XAUUSD",
        candle_close_time=_utc(2026, 4, 5, 13, 15),
    )
    assert setup.skip_reason == "INVALID_SIDE"


def test_future_ob_excluded():
    """An OB whose formation_time is AFTER candle_close_time must be excluded."""
    obs = [
        {"type": "bullish", "high": 100, "low": 90,
         "formation_time": "2026-04-10T08:00:00", "mitigated": False}
    ]
    mso = _mso_with_h1(obs, atr_14=2.0)
    setup = compute_mechanical_entry(
        mso, "LONG", symbol="XAUUSD",
        candle_close_time=_utc(2026, 4, 5, 13, 15),
    )
    assert setup.skip_reason == "ALL_FUTURE_OR_UNDATED"


def test_min_ticks_buffer_dominates_when_atr_tiny():
    """For tight FX (USDJPY tick=0.001), if ATR is 0 we still get a min_ticks buffer."""
    obs = [
        {"type": "bullish", "high": 150.5, "low": 150.0,
         "formation_time": "2026-04-01T08:00:00", "mitigated": False}
    ]
    mso = _mso_with_h1(obs, atr_14=0.0)
    setup = compute_mechanical_entry(
        mso, "LONG", symbol="USDJPY",
        candle_close_time=_utc(2026, 4, 5, 13, 15),
        cfg=BaselineConfig(sl_buffer_atr_multiplier=0.25, sl_buffer_min_ticks=5),
    )
    assert setup.skip_reason is None
    # buffer = 5 * 0.001 = 0.005
    assert setup.sl_buffer_used == pytest.approx(0.005, rel=1e-4)


def test_picks_latest_unmitigated_ob():
    """Among multiple unmitigated bullish OBs, latest formation_time wins."""
    obs = [
        {"type": "bullish", "high": 100, "low": 90,
         "formation_time": "2026-04-01T08:00:00", "mitigated": False},
        {"type": "bullish", "high": 105, "low": 95,
         "formation_time": "2026-04-04T08:00:00", "mitigated": False},
        {"type": "bullish", "high": 110, "low": 100,
         "formation_time": "2026-04-02T08:00:00", "mitigated": False},
    ]
    mso = _mso_with_h1(obs, atr_14=2.0)
    setup = compute_mechanical_entry(
        mso, "LONG", symbol="XAUUSD",
        candle_close_time=_utc(2026, 4, 5, 13, 15),
    )
    assert setup.skip_reason is None
    assert setup.ob_high == 105.0
    assert setup.ob_low == 95.0


# ---------------------------------------------------------------------------
# 4. resolve_mechanical_outcome — synthetic OHLCV
# ---------------------------------------------------------------------------


def _setup(side: str = "LONG", entry: float = 100, sl: float = 95, tp: float = 110) -> MechanicalSetup:
    return MechanicalSetup(
        cand_id="TEST|2026-04-05T13:15:00+00:00",
        symbol="XAUUSD",
        candle_close_time=_utc(2026, 4, 5, 13, 15),
        side=side,
        framework="ob_retest",
        ob_high=110.0, ob_low=90.0,
        entry=entry, sl=sl, tp=tp,
        rr=(abs(tp - entry) / abs(entry - sl)) if entry != sl else 0,
    )


def _bars(start: dt.datetime, *bars: tuple) -> List[Dict[str, Any]]:
    """Build a list of OHLCV bar dicts; each tuple is (open, high, low, close)."""
    out = []
    for i, b in enumerate(bars):
        out.append({
            "time": start + dt.timedelta(minutes=15 * i),
            "open": float(b[0]),
            "high": float(b[1]),
            "low": float(b[2]),
            "close": float(b[3]),
        })
    return out


def test_outcome_tp_hit_long():
    setup = _setup("LONG", entry=100, sl=95, tp=110)  # 1.0R = 5; RR=2.0
    # Fill bar (price retraces to entry), then TP bar.
    bars = _bars(
        _utc(2026, 4, 5, 13, 30),
        (101, 102, 99, 100),    # bar 1: low=99 <= entry → fill
        (100, 105, 99, 104),    # bar 2: no hit
        (104, 111, 103, 110),   # bar 3: high >= 110 → TP hit
    )
    out = resolve_mechanical_outcome(setup, ohlcv_rows=bars)
    assert out.outcome == "TP"
    assert out.realized_r == pytest.approx(2.0, rel=1e-3)
    assert out.bars_in_trade == 2  # bars 2 + 3 are post-fill


def test_outcome_sl_hit_long():
    setup = _setup("LONG", entry=100, sl=95, tp=110)
    bars = _bars(
        _utc(2026, 4, 5, 13, 30),
        (101, 102, 99.5, 100),  # fill
        (100, 102, 94, 96),     # low <= 95 → SL hit
    )
    out = resolve_mechanical_outcome(setup, ohlcv_rows=bars)
    assert out.outcome == "SL"
    assert out.realized_r == pytest.approx(-1.0, rel=1e-3)
    assert out.bars_in_trade == 1


def test_outcome_sl_hit_short():
    setup = _setup("SHORT", entry=200, sl=205, tp=190)
    bars = _bars(
        _utc(2026, 4, 5, 13, 30),
        (199, 200.5, 198, 199.5),  # fill (high >= 200)
        (200, 206, 199, 205),       # high >= 205 → SL
    )
    out = resolve_mechanical_outcome(setup, ohlcv_rows=bars)
    assert out.outcome == "SL"
    assert out.realized_r == pytest.approx(-1.0, rel=1e-3)


def test_outcome_tp_hit_short():
    setup = _setup("SHORT", entry=200, sl=205, tp=190)  # RR=2.0
    bars = _bars(
        _utc(2026, 4, 5, 13, 30),
        (199, 200.5, 198, 199.5),  # fill
        (200, 202, 189, 191),      # low <= 190 → TP
    )
    out = resolve_mechanical_outcome(setup, ohlcv_rows=bars)
    assert out.outcome == "TP"
    assert out.realized_r == pytest.approx(2.0, rel=1e-3)


def test_outcome_sl_first_when_both_hit_same_bar():
    """A bar AFTER fill that touches BOTH SL and TP must resolve to SL."""
    setup = _setup("LONG", entry=100, sl=95, tp=110)
    bars = _bars(
        _utc(2026, 4, 5, 13, 30),
        (101, 102, 99.5, 100),  # fill
        (100, 115, 90, 100),     # both hit on a post-fill bar
    )
    out = resolve_mechanical_outcome(setup, ohlcv_rows=bars)
    assert out.outcome == "SL"


def test_outcome_same_bar_skipped():
    """A fill bar that ALSO hits TP/SL is flagged SAME_BAR (cannot resolve)."""
    setup = _setup("LONG", entry=100, sl=95, tp=110)
    bars = _bars(
        _utc(2026, 4, 5, 13, 30),
        (101, 115, 99.5, 100),  # fill AND TP same bar
    )
    out = resolve_mechanical_outcome(setup, ohlcv_rows=bars)
    assert out.outcome == "SAME_BAR"
    assert out.realized_r is None


def test_outcome_never_filled():
    """If price never visits entry, NO_ENTRY."""
    setup = _setup("LONG", entry=100, sl=95, tp=110)
    bars = _bars(
        _utc(2026, 4, 5, 13, 30),
        (105, 110, 102, 108),  # low never <= 100
        (108, 112, 105, 110),
    )
    out = resolve_mechanical_outcome(setup, ohlcv_rows=bars)
    assert out.outcome == "NO_ENTRY"
    assert out.realized_r is None


def test_outcome_timeout():
    setup = _setup("LONG", entry=100, sl=95, tp=110)
    # 5 bars of nothing happening — close at 102
    bars = _bars(
        _utc(2026, 4, 5, 13, 30),
        (101, 102, 99.5, 100),  # fill bar
        (100, 101, 99.6, 100),
        (100, 102, 99.6, 101),
        (101, 102, 100, 101),
        (101, 103, 100, 102),
        (102, 103, 101, 102),
    )
    out = resolve_mechanical_outcome(setup, ohlcv_rows=bars, max_hold_bars=6)
    assert out.outcome == "TIMEOUT"
    # MTM = (102 - 100) / 5 = 0.4
    assert out.realized_r == pytest.approx(0.4, rel=1e-3)


def test_outcome_market_order_mode_skips_fill_check():
    """require_pending_fill=False emulates market-order semantics."""
    setup = _setup("LONG", entry=100, sl=95, tp=110)
    bars = _bars(
        _utc(2026, 4, 5, 13, 30),
        (105, 111, 104, 110),  # high >= 110, no fill check needed
    )
    out = resolve_mechanical_outcome(setup, ohlcv_rows=bars, require_pending_fill=False)
    assert out.outcome == "TP"


def test_outcome_no_data():
    """An empty OHLCV ⇒ NO_DATA outcome."""
    setup = _setup("LONG")
    out = resolve_mechanical_outcome(setup, ohlcv_rows=[])
    assert out.outcome == "NO_DATA"
    assert out.realized_r is None


def test_outcome_skip_propagates_when_setup_invalid():
    """If the setup has a skip_reason, outcome resolution returns INVALID."""
    setup = MechanicalSetup(
        cand_id="T", symbol="XAUUSD",
        candle_close_time=_utc(2026, 4, 5, 13, 15),
        side="LONG", framework="ob_retest",
        ob_high=0, ob_low=0,
        skip_reason="NO_OBS",
    )
    out = resolve_mechanical_outcome(setup, ohlcv_rows=[])
    assert out.outcome == "INVALID"
    assert out.skip_reason == "NO_OBS"


# ---------------------------------------------------------------------------
# 5. End-to-end replay on synthetic 5-CAND fixture
# ---------------------------------------------------------------------------


def _build_trade_record(
    *,
    symbol: str,
    candle_time: dt.datetime,
    side: str,
    framework: str,
    obs_h1: List[Mapping[str, Any]],
    swings_h1: List[Mapping[str, Any]] | None,
    atr_14: float,
    realized_r: float | None,
    decision: str = "CANDIDATE",
) -> Mapping[str, Any]:
    """Build a minimal trade record dict matching the production schema."""
    rec: Dict[str, Any] = {
        "metadata": {
            "trade_id": f"{symbol}_{candle_time.date().isoformat()}_test",
            "date": candle_time.date().isoformat(),
            "symbol": symbol,
            "kill_zone": "ny",
            "candle_time": candle_time.isoformat(),
        },
        "decision_pipeline": {
            "ai_decision": decision,
            "ai_direction": side,
            "ai_framework": framework,
        },
        "mso": _mso_with_h1(obs_h1, swings_h1, atr_14=atr_14),
    }
    if realized_r is not None:
        rec["decision_pipeline"]["outcome"] = {"r_multiple": realized_r}
    return rec


def _write_fixture_records(
    root: Path, records: List[Mapping[str, Any]]
) -> None:
    """Write fixture trade records into ``root/{symbol}/<id>.json``."""
    for rec in records:
        meta = rec["metadata"]
        sym = meta["symbol"]
        path = root / sym / f"{meta['trade_id']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rec), encoding="utf-8")


def _write_fixture_csv(
    csv_dir: Path, symbol: str, bars: List[Mapping[str, Any]],
    file_stem: str | None = None,
) -> None:
    csv_dir.mkdir(parents=True, exist_ok=True)
    stem = file_stem or symbol
    path = csv_dir / f"{stem}_M15.csv"
    lines = ["time,open,high,low,close,volume"]
    for b in bars:
        ts = b["time"]
        if isinstance(ts, dt.datetime):
            # CSV format used by data/historical_2026: "YYYY-MM-DD HH:MM:SS"
            tstr = ts.strftime("%Y-%m-%d %H:%M:%S")
        else:
            tstr = str(ts)
        lines.append(
            f"{tstr},{b['open']},{b['high']},{b['low']},{b['close']},1"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _make_winning_bars(
    start: dt.datetime, side: str, entry: float, sl: float, tp: float
) -> List[Dict[str, Any]]:
    """Two bars: bar 1 fills (price visits entry), bar 2 hits TP."""
    if side == "LONG":
        return _bars(
            start,
            # Fill bar: low touches entry, high stays well below TP
            (entry + 0.5, entry + 0.5, entry - 0.05, entry + 0.1),
            # TP bar: high reaches TP without dropping back to SL
            (entry + 0.1, tp + 0.5, entry, tp),
        )
    return _bars(
        start,
        # Fill bar: high touches entry, low stays well above TP
        (entry - 0.5, entry + 0.05, entry - 0.5, entry - 0.1),
        # TP bar: low reaches TP without spiking back to SL
        (entry - 0.1, entry, tp - 0.5, tp),
    )


def _make_losing_bars(
    start: dt.datetime, side: str, entry: float, sl: float
) -> List[Dict[str, Any]]:
    """Two bars: bar 1 fills, bar 2 hits SL."""
    if side == "LONG":
        return _bars(
            start,
            (entry + 0.5, entry + 0.5, entry - 0.05, entry + 0.1),
            (entry, entry + 0.5, sl - 1.0, sl - 0.5),
        )
    return _bars(
        start,
        (entry - 0.5, entry + 0.05, entry - 0.5, entry - 0.1),
        (entry, sl + 1.0, entry, sl + 0.5),
    )


def test_end_to_end_replay_5_cands_with_partial_join(tmp_path, monkeypatch):
    """5 synthetic CANDs in trade_records; 3 have realized_r joined; 2 None.

    Validates:
      * replay produces 5 ReplayRows
      * 3 rows have ai_realized_r set; 2 are None
      * mechanical_realized_r is set on rows where the OHLCV resolved
      * aggregate emits halves + verdict block
    """
    # Layout
    trade_dir = tmp_path / "trade_records"
    csv_dir = tmp_path / "csv"

    candle_t1 = _utc(2026, 1, 15, 13, 15)   # H1
    candle_t2 = _utc(2026, 2, 15, 13, 15)
    candle_t3 = _utc(2026, 3, 15, 13, 15)
    candle_t4 = _utc(2026, 4, 5, 13, 15)
    candle_t5 = _utc(2026, 4, 10, 13, 15)

    # OBs all in the past
    base_ob = {
        "type": "bullish", "high": 100.0, "low": 90.0,
        "formation_time": "2026-01-01T08:00:00", "mitigated": False,
    }
    base_ob_short = {
        "type": "bearish", "high": 200.0, "low": 190.0,
        "formation_time": "2026-01-01T08:00:00", "mitigated": False,
    }

    # 3 with realized_r, 2 without
    records = [
        _build_trade_record(
            symbol="XAUUSD", candle_time=candle_t1, side="LONG",
            framework="ob_retest", obs_h1=[base_ob], swings_h1=[],
            atr_14=2.0, realized_r=+1.5,
        ),
        _build_trade_record(
            symbol="XAUUSD", candle_time=candle_t2, side="LONG",
            framework="ob_retest", obs_h1=[base_ob], swings_h1=[],
            atr_14=2.0, realized_r=-1.0,
        ),
        _build_trade_record(
            symbol="XAUUSD", candle_time=candle_t3, side="LONG",
            framework="ob_retest", obs_h1=[base_ob], swings_h1=[],
            atr_14=2.0, realized_r=None,  # no fill / no outcome
        ),
        _build_trade_record(
            symbol="USDJPY", candle_time=candle_t4, side="SHORT",
            framework="ob_retest", obs_h1=[base_ob_short], swings_h1=[],
            atr_14=4.0, realized_r=+1.5,
        ),
        _build_trade_record(
            symbol="USDJPY", candle_time=candle_t5, side="SHORT",
            framework="ob_retest", obs_h1=[base_ob_short], swings_h1=[],
            atr_14=4.0, realized_r=None,
        ),
    ]
    _write_fixture_records(trade_dir, records)

    # Build M15 CSV that resolves 4 of 5 mechanical setups (one misses
    # for OHLCV unavailable to test NO_DATA path).
    # XAUUSD setups: entry=98, sl=89.5, tp=110.75 (RR=1.5)
    # USDJPY setups: entry=192, sl=201, tp=178.5
    xau_bars = (
        _make_winning_bars(candle_t1 + dt.timedelta(minutes=15), "LONG", 98.0, 89.5, 110.75)
        + _make_losing_bars(candle_t2 + dt.timedelta(minutes=15), "LONG", 98.0, 89.5)
        + _make_winning_bars(candle_t3 + dt.timedelta(minutes=15), "LONG", 98.0, 89.5, 110.75)
    )
    usdjpy_bars = (
        _make_winning_bars(candle_t4 + dt.timedelta(minutes=15), "SHORT", 192.0, 201.0, 178.5)
        + _make_winning_bars(candle_t5 + dt.timedelta(minutes=15), "SHORT", 192.0, 201.0, 178.5)
    )
    _write_fixture_csv(csv_dir, "XAUUSD", xau_bars)
    _write_fixture_csv(csv_dir, "USDJPY", usdjpy_bars)

    # Reset the module-level OHLCV cache so the test's CSV is read fresh
    monkeypatch.setattr(db, "_OHLCV_CACHE", {})

    replay = DumbBaselineReplay(
        trade_records_dir=trade_dir,
        ohlcv_dir=csv_dir,
        cfg=BaselineConfig(),
    )
    rows = replay.run()

    # One row per trade record.
    assert len(rows) == 5

    # 3 rows have ai_realized_r; 2 None.
    ai_resolved_count = sum(1 for r in rows if r.ai_realized_r is not None)
    assert ai_resolved_count == 3

    # Mechanical fired on every row (none of our setups should be skipped)
    mech_fired = [r for r in rows if r.mechanical_fired]
    assert len(mech_fired) == 5

    # Mechanical outcomes should resolve on every row (we engineered the bars)
    mech_resolved = [r for r in rows if r.mechanical_realized_r is not None]
    assert len(mech_resolved) == 5

    # Per-row sanity: gap should be set ONLY where both arms have R
    matched = [r for r in rows if r.realized_r_gap is not None]
    assert len(matched) == 3

    # XAUUSD Jan: AI=+1.5, mech=+1.5 → gap=0 (because TP-hit win)
    jan_row = [r for r in rows if r.symbol == "XAUUSD" and r.period_month == "2026-01"][0]
    assert jan_row.ai_realized_r == pytest.approx(1.5, rel=1e-3)
    assert jan_row.mechanical_realized_r == pytest.approx(1.5, rel=1e-3)
    assert jan_row.realized_r_gap == pytest.approx(0.0, abs=1e-3)

    # XAUUSD Feb: AI=-1.0, mech=-1.0 → gap=0
    feb_row = [r for r in rows if r.symbol == "XAUUSD" and r.period_month == "2026-02"][0]
    assert feb_row.ai_realized_r == pytest.approx(-1.0, rel=1e-3)
    assert feb_row.mechanical_realized_r == pytest.approx(-1.0, rel=1e-3)


# ---------------------------------------------------------------------------
# 6. aggregate emits the verdict block
# ---------------------------------------------------------------------------


def test_aggregate_inconclusive_when_low_n():
    """With only a handful of matched pairs, verdict is INCONCLUSIVE."""
    rows = []
    for i in range(3):
        from src.research_infra.dumb_baseline import ReplayRow
        rows.append(ReplayRow(
            cand_id=f"X|{i}",
            symbol="XAUUSD",
            candle_close_time=f"2026-01-{i+1:02d}T13:15:00+00:00",
            period_month="2026-01",
            side="LONG", framework="ob_retest", kill_zone="ny",
            ai_decision="CANDIDATE",
            ai_realized_r=1.0, ai_outcome_resolved=True,
            mechanical_skip_reason=None,
            mechanical_entry=98.0, mechanical_sl=89.5,
            mechanical_tp=110.75, mechanical_rr=1.5,
            mechanical_outcome="TP", mechanical_realized_r=1.5,
            mechanical_bars_in_trade=2, mechanical_fired=True,
            realized_r_gap=-0.5,
        ))
    summary = aggregate(rows)
    verdict = summary["verdict"]
    assert verdict["diagnosis"] == "INCONCLUSIVE"
    # Required keys present
    assert "h1_gap_wr_pp" in verdict
    assert "h2_gap_wr_pp" in verdict
    assert "gap_delta_pp" in verdict
    assert "gap_stddev_pp" in verdict


def test_aggregate_system_decay_diagnosed():
    """Synthetic data: H1 AI dominates, H2 mechanical dominates → SYSTEM_DECAY."""
    from src.research_infra.dumb_baseline import ReplayRow
    rows: List[ReplayRow] = []
    # H1 (Jan + Feb): 12 pairs, AI WR 100%, mech WR 50% → +50pp gap
    for i in range(12):
        ai_r = 1.5
        mech_r = 1.5 if i < 6 else -1.0
        month = "2026-01" if i < 6 else "2026-02"
        rows.append(ReplayRow(
            cand_id=f"H1|{i}",
            symbol="XAUUSD",
            candle_close_time=f"{month}-15T13:15:00+00:00",
            period_month=month,
            side="LONG", framework="ob_retest", kill_zone="ny",
            ai_decision="CANDIDATE",
            ai_realized_r=ai_r, ai_outcome_resolved=True,
            mechanical_skip_reason=None,
            mechanical_entry=98.0, mechanical_sl=89.5,
            mechanical_tp=110.75, mechanical_rr=1.5,
            mechanical_outcome="TP" if mech_r > 0 else "SL",
            mechanical_realized_r=mech_r,
            mechanical_bars_in_trade=2, mechanical_fired=True,
            realized_r_gap=ai_r - mech_r,
        ))
    # H2 (Mar + Apr): 12 pairs, AI WR 25%, mech WR 75% → -50pp gap
    for i in range(12):
        ai_r = 1.5 if i < 3 else -1.0
        mech_r = 1.5 if i < 9 else -1.0
        month = "2026-03" if i < 6 else "2026-04"
        rows.append(ReplayRow(
            cand_id=f"H2|{i}",
            symbol="XAUUSD",
            candle_close_time=f"{month}-15T13:15:00+00:00",
            period_month=month,
            side="LONG", framework="ob_retest", kill_zone="ny",
            ai_decision="CANDIDATE",
            ai_realized_r=ai_r, ai_outcome_resolved=True,
            mechanical_skip_reason=None,
            mechanical_entry=98.0, mechanical_sl=89.5,
            mechanical_tp=110.75, mechanical_rr=1.5,
            mechanical_outcome="TP" if mech_r > 0 else "SL",
            mechanical_realized_r=mech_r,
            mechanical_bars_in_trade=2, mechanical_fired=True,
            realized_r_gap=ai_r - mech_r,
        ))
    summary = aggregate(rows)
    verdict = summary["verdict"]
    assert verdict["diagnosis"] == "SYSTEM_DECAY"
    assert verdict["h1_gap_wr_pp"] >= 40  # ~+50
    assert verdict["h2_gap_wr_pp"] <= -40  # ~-50


# ---------------------------------------------------------------------------
# 7. Output writers — schema sanity
# ---------------------------------------------------------------------------


def test_writers_emit_valid_files(tmp_path):
    """Headers + lines should be parseable JSON / Markdown."""
    from src.research_infra.dumb_baseline import ReplayRow
    rows = [
        ReplayRow(
            cand_id="X|2026-01-01T13:15:00+00:00",
            symbol="XAUUSD",
            candle_close_time="2026-01-01T13:15:00+00:00",
            period_month="2026-01",
            side="LONG", framework="ob_retest", kill_zone="ny",
            ai_decision="CANDIDATE",
            ai_realized_r=1.5, ai_outcome_resolved=True,
            mechanical_skip_reason=None,
            mechanical_entry=98.0, mechanical_sl=89.5,
            mechanical_tp=110.75, mechanical_rr=1.5,
            mechanical_outcome="TP", mechanical_realized_r=1.5,
            mechanical_bars_in_trade=2, mechanical_fired=True,
            realized_r_gap=0.0,
        )
    ]
    summary = aggregate(rows)
    write_results_jsonl(rows, tmp_path / "results.jsonl")
    write_summary_json(summary, tmp_path / "summary.json")
    write_report_md(rows, summary, tmp_path / "report.md")
    # results.jsonl
    jl_lines = (tmp_path / "results.jsonl").read_text().splitlines()
    assert len(jl_lines) == 1
    parsed = json.loads(jl_lines[0])
    assert parsed["symbol"] == "XAUUSD"
    # summary.json
    s = json.loads((tmp_path / "summary.json").read_text())
    assert s["harness_version"] == HARNESS_VERSION
    assert "verdict" in s
    # report.md
    md = (tmp_path / "report.md").read_text()
    assert "## Strategic verdict" in md
    assert "Diagnosis:" in md


# ---------------------------------------------------------------------------
# 8. CLI dry-run smoke
# ---------------------------------------------------------------------------


def test_cli_dry_run_writes_nothing(tmp_path):
    """--dry-run prints plan, exits 0, writes no files to --output-dir."""
    out_dir = tmp_path / "should_be_empty"
    out_dir.mkdir()
    project_root = Path(__file__).resolve().parents[2]
    cmd = [
        sys.executable,
        str(project_root / "scripts" / "research" / "run_a1_dumb_baseline.py"),
        "--output-dir",
        str(out_dir),
        "--dry-run",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)
    result = subprocess.run(
        cmd, env=env, capture_output=True, text=True, cwd=project_root,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    # The plan JSON is on stdout
    plan = json.loads(result.stdout.strip().split("\n")[-1] if "}" not in result.stdout.strip()[-1:] else _last_json_block(result.stdout))
    assert plan["dry_run"] is True
    # No files written to out_dir
    assert list(out_dir.iterdir()) == []


def _last_json_block(text: str) -> str:
    """Extract the last balanced JSON object from text."""
    depth = 0
    start = -1
    last_block = ""
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                last_block = text[start:i + 1]
                start = -1
    return last_block


# ---------------------------------------------------------------------------
# 9. Batch-session path (compute_mechanical_entry_from_ohlcv)
# ---------------------------------------------------------------------------


def test_ohlcv_mechanical_entry_long_after_bullish_bos(monkeypatch):
    """Constructed H1 series with a clear bullish BOS produces a LONG setup."""
    from src.research_infra.dumb_baseline import (
        compute_mechanical_entry_from_ohlcv,
    )

    # Build 20 H1 bars: 0-9 trending down, 10-15 build a swing low, 16+ break high
    bars = []
    base = _utc(2026, 1, 5, 0, 0)
    # Construct a swing-high at index 5 at 110, a swing-low at 12 at 80, BOS at 16 close 115
    highs = [105, 108, 112, 110, 108, 112, 105, 100, 90, 85, 82, 78, 75, 80, 95, 105, 118, 120, 122, 125]
    lows  = [100, 102, 104, 102, 102, 104, 98,  92,  82, 78, 75, 73, 70, 75, 88, 98,  110, 112, 115, 118]
    for i, (h, lo) in enumerate(zip(highs, lows)):
        bars.append({
            "time": base + dt.timedelta(hours=i),
            "open": (h + lo) / 2,
            "high": h, "low": lo,
            "close": (h + lo) / 2,
        })

    setup = compute_mechanical_entry_from_ohlcv(
        symbol="XAUUSD",
        candle_close_time=base + dt.timedelta(hours=19),
        side="LONG",
        h1_bars=bars,
        cfg=BaselineConfig(),
    )
    assert setup.skip_reason is None, setup.skip_reason
    assert setup.side == "LONG"
    # impulse = swing_low at index 12 -> BOS index ~16 high
    # impulse_low <= 70, impulse_high >= 110
    assert setup.ob_low <= 75
    assert setup.ob_high >= 110
    # entry should be 80% retrace into impulse (high side for LONG)
    assert setup.entry > setup.ob_low + 0.5 * (setup.ob_high - setup.ob_low)


def test_ohlcv_mechanical_entry_short_after_bearish_bos():
    """Constructed bearish BOS produces a SHORT setup."""
    from src.research_infra.dumb_baseline import (
        compute_mechanical_entry_from_ohlcv,
    )
    bars = []
    base = _utc(2026, 1, 5, 0, 0)
    # swing-low at 5 at 100, swing-high at 12 at 130, BOS at 16 close 95
    highs = [105, 108, 110, 108, 105, 105, 108, 115, 120, 125, 128, 130, 132, 130, 120, 110, 105, 100, 92, 88]
    lows  = [100, 102, 104, 100, 98,  100, 104, 110, 115, 120, 122, 125, 128, 125, 115, 102, 95, 88, 80, 78]
    for i, (h, lo) in enumerate(zip(highs, lows)):
        bars.append({
            "time": base + dt.timedelta(hours=i),
            "open": (h + lo) / 2,
            "high": h, "low": lo,
            "close": (h + lo) / 2,
        })
    setup = compute_mechanical_entry_from_ohlcv(
        symbol="XAUUSD",
        candle_close_time=base + dt.timedelta(hours=19),
        side="SHORT",
        h1_bars=bars,
        cfg=BaselineConfig(),
    )
    assert setup.skip_reason is None, setup.skip_reason
    assert setup.side == "SHORT"
    # entry near the impulse-low side (since SHORT enters near OB top in retrace)
    assert setup.entry < setup.ob_low + 0.5 * (setup.ob_high - setup.ob_low)


def test_ohlcv_no_bars_skips():
    from src.research_infra.dumb_baseline import (
        compute_mechanical_entry_from_ohlcv,
    )
    setup = compute_mechanical_entry_from_ohlcv(
        symbol="XAUUSD",
        candle_close_time=_utc(2026, 1, 5, 13, 15),
        side="LONG",
        h1_bars=[],
    )
    assert setup.skip_reason == "NO_H1_BARS"


def test_batch_session_replay_e2e(tmp_path, monkeypatch):
    """Synthetic batch session JSON + matching H1+M15 OHLCV → ReplayRow."""
    import src.research_infra.dumb_baseline as db
    monkeypatch.setattr(db, "_OHLCV_CACHE", {})

    sessions_root = tmp_path / "sessions"
    csv_dir = tmp_path / "csv"

    # Build OHLCV that has a clear bullish BOS before 2026-01-05T13:00 and then
    # the price retraces 80% into the impulse.
    csv_dir.mkdir()
    h1_lines = ["time,open,high,low,close,volume"]
    base = _utc(2026, 1, 4, 0, 0)
    # 30 H1 bars: build swing-low @ idx 12, BOS @ idx 18
    highs = [200, 198, 196, 195, 195, 197, 196, 195, 195, 192, 188, 185, 184, 187, 195, 200, 205, 210, 215, 220, 222, 225, 220, 215, 210, 208, 205, 202, 200, 198]
    lows  = [196, 194, 192, 191, 191, 192, 192, 190, 190, 187, 183, 180, 178, 182, 190, 195, 200, 205, 210, 215, 217, 220, 215, 210, 205, 203, 200, 197, 195, 193]
    for i, (h, lo) in enumerate(zip(highs, lows)):
        ts = (base + dt.timedelta(hours=i)).strftime("%Y-%m-%d %H:%M:%S")
        c = (h + lo) / 2
        h1_lines.append(f"{ts},{c},{h},{lo},{c},1")
    (csv_dir / "XAUUSD_H1.csv").write_text("\n".join(h1_lines) + "\n")

    # M15 walk-forward: pull back to the entry price first, then rally to TP.
    # The mechanical entry is 80% retrace into the impulse_low (~178) ->
    # impulse_high (~225). So entry ≈ 217, SL ≈ 174, TP at 1.5R from entry.
    cand_t = base + dt.timedelta(hours=19, minutes=0)
    m15_lines = ["time,open,high,low,close,volume"]
    # Bar 1: pull back to ~178 (visits OB low side), bars 2..N rally up
    # First bar: low dips to 200 (still above entry ~217? no, must be <= entry).
    # Build bars that take low all the way down to <= 200, then rally above 280.
    for i in range(20):
        ts = (cand_t + dt.timedelta(minutes=15 * (i + 1))).strftime("%Y-%m-%d %H:%M:%S")
        if i == 0:
            # Pull-back bar: low touches well below 220
            m15_lines.append(f"{ts},220,221,180,200,1")
        else:
            # Rally bars
            m15_lines.append(f"{ts},200,{220 + i * 8},{200 - i},{210 + i * 6},1")
    (csv_dir / "XAUUSD_M15.csv").write_text("\n".join(m15_lines) + "\n")

    # Synthetic batch session — match the real data format (Z suffix only,
    # no +00:00 offset).
    session = {
        "date": "2026-01-04",
        "candle_evaluations": [
            {
                "candle_time": cand_t.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "kill_zone": "ny",
                "decision": "CANDIDATE",
                "framework": "ob_retest",
                "trade_executed": True,
                "trade_id": "bt_2026-01-04_test_001",
            },
        ],
        "trade_summary": {
            "trades": [
                {
                    "trade_id": "bt_2026-01-04_test_001",
                    "outcome": "WIN",
                    "r_multiple": 1.5,
                    "framework": "ob_retest",
                    "kill_zone": "ny",
                },
            ],
        },
    }
    inst_dir = sessions_root / "XAUUSD"
    inst_dir.mkdir(parents=True)
    (inst_dir / "2026-01-04_session.json").write_text(json.dumps(session))

    from src.research_infra.dumb_baseline import BatchSessionReplay
    replay = BatchSessionReplay(
        sessions_root=sessions_root,
        ohlcv_dir=csv_dir,
        cfg=BaselineConfig(),
    )
    rows = replay.run()
    assert len(rows) == 1
    row = rows[0]
    assert row.symbol == "XAUUSD"
    assert row.ai_realized_r == pytest.approx(1.5, rel=1e-3)
    # Mechanical should resolve (TP hit on the engineered M15)
    assert row.mechanical_fired is True
    assert row.mechanical_outcome in {"TP", "SL", "TIMEOUT"}
    assert row.mechanical_realized_r is not None
    # Gap is computed
    assert row.realized_r_gap is not None


def test_batch_session_replay_no_h1_data(tmp_path):
    """Batch CAND for a symbol whose OHLCV is missing → row with skip_reason."""
    sessions_root = tmp_path / "sessions"
    inst_dir = sessions_root / "UNKNOWN"
    inst_dir.mkdir(parents=True)
    session = {
        "date": "2026-01-04",
        "candle_evaluations": [
            {
                "candle_time": "2026-01-04T13:15:00Z",
                "kill_zone": "ny",
                "decision": "CANDIDATE",
                "framework": "ob_retest",
                "trade_executed": True,
                "trade_id": "bt_2026-01-04_unknown_001",
            }
        ],
        "trade_summary": {
            "trades": [
                {"trade_id": "bt_2026-01-04_unknown_001",
                 "outcome": "WIN", "r_multiple": 1.0,
                 "framework": "ob_retest", "kill_zone": "ny"}
            ]
        },
    }
    (inst_dir / "2026-01-04_session.json").write_text(json.dumps(session))

    csv_dir = tmp_path / "csv_empty"
    csv_dir.mkdir()

    from src.research_infra.dumb_baseline import BatchSessionReplay
    replay = BatchSessionReplay(
        sessions_root=sessions_root,
        ohlcv_dir=csv_dir,
        cfg=BaselineConfig(),
    )
    rows = replay.run()
    assert len(rows) == 1
    # Skip reason should be NO_H1_OHLCV (no H1 file)
    assert rows[0].mechanical_skip_reason in {
        "NO_H1_OHLCV", "NO_AI_SIDE",
    }
    # AI realized R still joined
    assert rows[0].ai_realized_r == pytest.approx(1.0, rel=1e-3)
