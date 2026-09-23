"""Tests for the dumb-momentum-baseline shadow logger.

Covers:

- Synthetic H1+M15 candle paths with known BOS + 80%-retrace produce ENTER.
- Out-of-KZ short-circuit returns SKIP_OUT_OF_KZ without firing.
- Daily fire gate prevents a second hypothesis on the same UTC date.
- Outcome resolution at TP / SL / TIMEOUT bumps `outcome` + `realized_r`.
- JSONL is rewritten in-place when an outcome resolves.
- Bad / missing data paths return ERROR/SKIP_NO_DATA without raising.
- State persistence + restore round-trips an open hypothetical.
- The orchestrator-style outer try wrap never re-raises into the caller.

All writes go to ``tmp_path`` via module-ref monkeypatch on SHADOW_LOG_PATH /
STATE_PATH / DEBUG_LOG_PATH (canonical pattern — see MEMORY.md
`project_pytest_contamination_forensics`).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.components import dumb_baseline_shadow_logger as mod


# ─────────────────────────────────────────────────────────────────────────
# Helpers — synthetic candle generators
# ─────────────────────────────────────────────────────────────────────────


def _make_candle(t: str, o: float, h: float, l: float, c: float, v: float = 1000.0) -> dict:
    """Build a candle dict matching `data_ingestion.ingest_live_data` schema."""
    return {"time": t, "open": o, "high": h, "low": l, "close": c, "volume": v}


def _bullish_bos_path(*, m15_close: float = 100.5) -> tuple[list[dict], list[dict]]:
    """Build (h1_candles, m15_candles) with one bullish BOS + impulse range = 6.0.

    Geometry (verified by hand against detect_swings + detect_structure_breaks):

    - swing high at index 3, price=102.5
    - swing low  at index 6, price=99.0
    - BOS candle at index 9 (close=104.5 > 102.5)
    - impulse leg = candles[3..9] -> impulse_low=99.0, impulse_high=105.0
      (impulse_high is the BOS candle's high, NOT the post-BOS candle's high)
    - impulse_range = 6.0
    - 80% retrace target for LONG = 105.0 - 0.80 * 6.0 = 100.2

    Pass m15_close <= 100.2 to fire ENTER. Pass m15_close > 100.2 to skip.

    M15 has 30 candles (enough for ATR(14)) ending at 2026-04-25T21:15 UTC.
    """
    h1 = [
        # Buffer candles
        _make_candle("2026-04-25T00:00:00+00:00", 100.0, 100.2, 99.9, 100.0),
        _make_candle("2026-04-25T01:00:00+00:00", 100.0, 100.3, 99.9, 100.1),
        _make_candle("2026-04-25T02:00:00+00:00", 100.1, 100.4, 100.0, 100.2),
        # Swing high at index 3 (price 102.5)
        _make_candle("2026-04-25T03:00:00+00:00", 100.2, 102.5, 100.0, 100.3),
        _make_candle("2026-04-25T04:00:00+00:00", 100.3, 100.5, 100.0, 100.2),
        _make_candle("2026-04-25T05:00:00+00:00", 100.2, 100.4, 99.5, 99.8),
        # Swing low at index 6 (price 99.0)
        _make_candle("2026-04-25T06:00:00+00:00", 99.8, 100.0, 99.0, 99.5),
        _make_candle("2026-04-25T07:00:00+00:00", 99.5, 100.0, 99.4, 99.9),
        _make_candle("2026-04-25T08:00:00+00:00", 99.9, 101.0, 99.8, 100.5),
        # BOS candle at index 9 (close 104.5 > swing high 102.5; high=105.0)
        _make_candle("2026-04-25T09:00:00+00:00", 100.5, 105.0, 100.4, 104.5),
        # Continued climb (no new BOS — no fresh swing high broken)
        _make_candle("2026-04-25T10:00:00+00:00", 104.5, 110.0, 104.0, 109.5),
        # Pullback toward 80%-retrace zone
        _make_candle("2026-04-25T11:00:00+00:00", 109.5, 109.7, 105.0, 105.5),
        _make_candle("2026-04-25T12:00:00+00:00", 105.5, 105.7, 101.0, 101.2),
        _make_candle("2026-04-25T13:00:00+00:00", 101.2, 101.5, 100.5, 100.9),
        _make_candle("2026-04-25T14:00:00+00:00", 100.9, 101.2, 100.6, 101.0),
    ]

    # M15: 30 candles down through ATR-stable decline, ending at m15_close.
    m15 = []
    for i in range(29):
        hh = 14 + (i // 4)
        mm = (i % 4) * 15
        t = f"2026-04-25T{hh:02d}:{mm:02d}:00+00:00"
        # ~0.05 unit per candle decline from 105 (entry baseline) — ATR settles ~ 0.4
        price_now = 105.0 - 0.05 * (i + 1)
        m15.append(_make_candle(
            t,
            o=price_now + 0.1, h=price_now + 0.3, l=price_now - 0.3,
            c=price_now,
        ))
    # Final candle lands exactly at m15_close.
    m15.append(_make_candle(
        "2026-04-25T21:15:00+00:00",
        o=m15_close + 0.2, h=m15_close + 0.4, l=m15_close - 0.3,
        c=m15_close,
    ))
    return h1, m15


# ─────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────


@pytest.fixture
def isolated_paths(tmp_path, monkeypatch):
    """Redirect log + state + debug paths into tmp_path.

    ``state`` is the legacy combined-file location (kept for migration-fallback
    test scenarios). ``state_for(symbol)`` returns the per-symbol file path
    used in production since 2026-04-29.
    """
    log_path = tmp_path / "dumb_baseline_hypotheticals.jsonl"
    state_path = tmp_path / ".dumb_baseline_state.json"
    debug_path = tmp_path / "dumb_baseline_debug.jsonl"
    monkeypatch.setattr(mod, "SHADOW_LOG_PATH", log_path)
    monkeypatch.setattr(mod, "STATE_PATH", state_path)
    monkeypatch.setattr(mod, "DEBUG_LOG_PATH", debug_path)
    return {
        "log": log_path,
        "state": state_path,  # legacy combined-file path
        "state_for": lambda symbol: mod._state_path_for(symbol),
        "debug": debug_path,
    }


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    out = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


# ─────────────────────────────────────────────────────────────────────────
# 80%-retrace fire path
# ─────────────────────────────────────────────────────────────────────────


class TestRetraceTrigger:
    """ENTER path: BOS + 80% retrace + KZ active."""

    def test_bullish_bos_80pct_retrace_fires(self, isolated_paths):
        """Synthetic bullish BOS (impulse 99->105) + M15 close at 100.0 fires LONG.

        Entry target = 105.0 - 0.80 * 6.0 = 100.2. M15 close 100.0 < 100.2 => fire.
        """
        h1, m15 = _bullish_bos_path(m15_close=100.0)
        raw_data = {"candles": {"H1": h1, "M15": m15}}

        result = mod.process_candle(
            symbol="XAUUSD",
            raw_data=raw_data,
            kz="ny",
            timestamp_utc="2026-04-25T21:15:05+00:00",
        )

        assert result["action"] == "ENTER", f"Expected ENTER, got {result}"
        records = _read_jsonl(isolated_paths["log"])
        assert len(records) == 1
        rec = records[0]
        assert rec["symbol"] == "XAUUSD"
        assert rec["direction"] == "LONG"
        assert rec["bos_direction"] == "bullish"
        assert rec["kz"] == "ny"
        assert rec["outcome"] is None
        # Entry = M15 close that triggered the retrace.
        assert abs(rec["entry"] - 100.0) < 0.001
        assert rec["sl"] < rec["entry"]  # LONG SL below entry
        assert rec["tp"] > rec["entry"]  # LONG TP above entry
        assert rec["impulse_range"] > 0
        # SL = entry - ATR; TP = entry + 1.5*ATR.
        sl_dist = rec["entry"] - rec["sl"]
        tp_dist = rec["tp"] - rec["entry"]
        assert abs(tp_dist / sl_dist - 1.5) < 0.01

    def test_no_retrace_returns_no_fire(self, isolated_paths):
        """Price still above the 80% retrace target -> NO_FIRE (NO_RETRACE).

        Entry target=100.2, M15 close=104.0 (above target -> not yet retraced).
        """
        h1, m15 = _bullish_bos_path(m15_close=104.0)
        raw_data = {"candles": {"H1": h1, "M15": m15}}

        result = mod.process_candle(
            symbol="XAUUSD",
            raw_data=raw_data,
            kz="ny",
            timestamp_utc="2026-04-25T21:15:05+00:00",
        )

        assert result["action"] == "NO_FIRE"
        assert result["reason"] == "NO_RETRACE"
        assert _read_jsonl(isolated_paths["log"]) == []


# ─────────────────────────────────────────────────────────────────────────
# Out-of-KZ
# ─────────────────────────────────────────────────────────────────────────


class TestOutOfKZ:

    def test_empty_kz_short_circuits(self, isolated_paths):
        """kz='' -> SKIP_OUT_OF_KZ (no fire, no JSONL append)."""
        h1, m15 = _bullish_bos_path()
        raw_data = {"candles": {"H1": h1, "M15": m15}}

        result = mod.process_candle(
            symbol="XAUUSD",
            raw_data=raw_data,
            kz="",
            timestamp_utc="2026-04-25T03:00:00+00:00",
        )

        assert result["action"] == "SKIP_OUT_OF_KZ"
        assert _read_jsonl(isolated_paths["log"]) == []


# ─────────────────────────────────────────────────────────────────────────
# Daily fire gate
# ─────────────────────────────────────────────────────────────────────────


class TestDailyFireGate:

    def test_second_fire_same_day_blocked(self, isolated_paths):
        """Two ENTER-eligible calls on the same UTC date — second is gated."""
        h1, m15 = _bullish_bos_path(m15_close=100.0)
        raw_data = {"candles": {"H1": h1, "M15": m15}}

        first = mod.process_candle(
            symbol="XAUUSD",
            raw_data=raw_data,
            kz="ny",
            timestamp_utc="2026-04-25T21:15:05+00:00",
        )
        assert first["action"] == "ENTER"

        # Second call same UTC date.
        second = mod.process_candle(
            symbol="XAUUSD",
            raw_data=raw_data,
            kz="ny",
            timestamp_utc="2026-04-25T21:30:05+00:00",
        )
        assert second["action"] == "SKIP_DAILY_GATE"
        assert second["reason"] == "already_fired_today"
        # Still only one record.
        assert len(_read_jsonl(isolated_paths["log"])) == 1

    def test_next_day_can_fire(self, isolated_paths):
        """A fire on day N + a fire on day N+1 both succeed (independent symbols' state)."""
        h1, m15 = _bullish_bos_path(m15_close=100.0)
        raw_data = {"candles": {"H1": h1, "M15": m15}}

        r1 = mod.process_candle(
            symbol="XAUUSD",
            raw_data=raw_data,
            kz="ny",
            timestamp_utc="2026-04-25T21:15:05+00:00",
        )
        assert r1["action"] == "ENTER"

        # Different UTC date -> ENTER again.
        # Build a slightly different raw_data so the hypothesis_id is unique.
        m15b = list(m15)
        m15b[-1] = dict(m15b[-1])
        m15b[-1]["time"] = "2026-04-26T13:15:00+00:00"
        raw_data2 = {"candles": {"H1": h1, "M15": m15b}}

        r2 = mod.process_candle(
            symbol="XAUUSD",
            raw_data=raw_data2,
            kz="ny",
            timestamp_utc="2026-04-26T13:15:05+00:00",
        )
        assert r2["action"] == "ENTER", f"Day 2 should fire: {r2}"
        assert len(_read_jsonl(isolated_paths["log"])) == 2


# ─────────────────────────────────────────────────────────────────────────
# Outcome resolution
# ─────────────────────────────────────────────────────────────────────────


class TestOutcomeResolution:

    def test_tp_resolves_long(self, isolated_paths):
        """A LONG hypothetical resolves TP when next candle high >= TP."""
        h1, m15 = _bullish_bos_path(m15_close=100.0)
        raw_data = {"candles": {"H1": h1, "M15": m15}}
        first = mod.process_candle(
            symbol="XAUUSD", raw_data=raw_data, kz="ny",
            timestamp_utc="2026-04-25T21:15:05+00:00",
        )
        assert first["action"] == "ENTER"

        rec = _read_jsonl(isolated_paths["log"])[0]
        tp = rec["tp"]

        # Build a follow-up M15 candle that hits TP. Mark it as a different day to
        # avoid the daily fire gate masking the resolve path on a re-fire.
        next_m15 = m15 + [_make_candle(
            "2026-04-26T13:15:00+00:00",
            o=rec["entry"], h=tp + 0.5, l=rec["entry"] - 0.1,
            c=rec["entry"] + (tp - rec["entry"]) * 0.95,
        )]
        # H1 unchanged.
        raw_data2 = {"candles": {"H1": h1, "M15": next_m15}}

        # Note: the follow-up call may also fire (next day) — but the OPEN
        # hypothetical from day 1 should resolve first.
        mod.process_candle(
            symbol="XAUUSD", raw_data=raw_data2, kz="ny",
            timestamp_utc="2026-04-26T13:15:05+00:00",
        )

        records = _read_jsonl(isolated_paths["log"])
        # Find the original (day-1) record by timestamp/candle_time prefix.
        day1 = [r for r in records if r["candle_time"].startswith("2026-04-25T21:15")]
        assert day1, "Day 1 hypothetical missing from log"
        assert day1[0]["outcome"] == "TP"
        assert day1[0]["realized_r"] == round(mod.MIN_RR, 4)
        assert day1[0]["time_in_trade_bars"] >= 1

    def test_sl_resolves_long(self, isolated_paths):
        """A LONG hypothetical resolves SL when next candle low <= SL."""
        h1, m15 = _bullish_bos_path(m15_close=100.0)
        raw_data = {"candles": {"H1": h1, "M15": m15}}
        first = mod.process_candle(
            symbol="XAUUSD", raw_data=raw_data, kz="ny",
            timestamp_utc="2026-04-25T21:15:05+00:00",
        )
        assert first["action"] == "ENTER"
        rec = _read_jsonl(isolated_paths["log"])[0]
        sl = rec["sl"]

        next_m15 = m15 + [_make_candle(
            "2026-04-26T13:15:00+00:00",
            o=rec["entry"], h=rec["entry"] + 0.1, l=sl - 0.5, c=sl - 0.2,
        )]
        raw_data2 = {"candles": {"H1": h1, "M15": next_m15}}
        mod.process_candle(
            symbol="XAUUSD", raw_data=raw_data2, kz="ny",
            timestamp_utc="2026-04-26T13:15:05+00:00",
        )

        records = _read_jsonl(isolated_paths["log"])
        day1 = [r for r in records if r["candle_time"].startswith("2026-04-25T21:15")]
        assert day1
        assert day1[0]["outcome"] == "SL"
        assert day1[0]["realized_r"] == -1.0

    def test_timeout_resolves(self, isolated_paths, monkeypatch):
        """A hypothetical with no TP/SL resolves at OUTCOME_TIMEOUT_M15_BARS bars."""
        # Drop the timeout to a small number so the test stays fast.
        monkeypatch.setattr(mod, "OUTCOME_TIMEOUT_M15_BARS", 2)

        h1, m15 = _bullish_bos_path(m15_close=100.0)
        raw_data = {"candles": {"H1": h1, "M15": m15}}
        first = mod.process_candle(
            symbol="XAUUSD", raw_data=raw_data, kz="ny",
            timestamp_utc="2026-04-25T21:15:05+00:00",
        )
        assert first["action"] == "ENTER"
        rec = _read_jsonl(isolated_paths["log"])[0]
        # Pick a "neutral" follow-up candle that doesn't touch SL or TP.
        neutral_high = (rec["entry"] + rec["tp"]) / 2 - 0.01
        neutral_low = (rec["entry"] + rec["sl"]) / 2 + 0.01

        # Two follow-ups -> bars_elapsed reaches 2 -> TIMEOUT.
        for i, ts in enumerate([
            "2026-04-26T13:15:00+00:00",
            "2026-04-26T13:30:00+00:00",
        ], start=1):
            next_m15 = m15 + [_make_candle(
                ts, o=rec["entry"], h=neutral_high, l=neutral_low,
                c=(neutral_high + neutral_low) / 2,
            )]
            raw_data2 = {"candles": {"H1": h1, "M15": next_m15}}
            mod.process_candle(
                symbol="XAUUSD", raw_data=raw_data2, kz="ny",
                timestamp_utc=f"2026-04-26T13:{15 * i:02d}:05+00:00",
            )

        records = _read_jsonl(isolated_paths["log"])
        day1 = [r for r in records if r["candle_time"].startswith("2026-04-25T21:15")]
        assert day1
        assert day1[0]["outcome"] == "TIMEOUT"
        assert day1[0]["time_in_trade_bars"] == 2


# ─────────────────────────────────────────────────────────────────────────
# Bad / missing data — fail-open
# ─────────────────────────────────────────────────────────────────────────


class TestFailOpen:

    def test_missing_candles_dict(self, isolated_paths):
        """raw_data with no candles -> SKIP_NO_DATA, no raise."""
        result = mod.process_candle(
            symbol="XAUUSD", raw_data={"candles": {}}, kz="ny",
            timestamp_utc="2026-04-25T13:15:05+00:00",
        )
        assert result["action"] == "SKIP_NO_DATA"
        assert result["open_count"] == 0

    def test_none_raw_data(self, isolated_paths):
        """raw_data is None -> SKIP_NO_DATA without raising."""
        result = mod.process_candle(
            symbol="XAUUSD", raw_data=None, kz="ny",
            timestamp_utc="2026-04-25T13:15:05+00:00",
        )
        # Either SKIP_NO_DATA or ERROR — both are acceptable failure-isolation
        # paths so long as no exception leaks.
        assert result["action"] in ("SKIP_NO_DATA", "ERROR")

    def test_no_bos_returns_no_fire(self, isolated_paths):
        """H1 candles with no swing/BOS pattern -> NO_FIRE (NO_BOS or NO_RECENT_BOS)."""
        # Flat H1 — no swings, no BOS.
        flat_h1 = [
            _make_candle(f"2026-04-25T{i:02d}:00:00+00:00", 100.0, 100.1, 99.9, 100.0)
            for i in range(20)
        ]
        flat_m15 = [
            _make_candle(f"2026-04-25T13:{(i % 4) * 15:02d}:00+00:00", 100.0, 100.1, 99.9, 100.0)
            for i in range(30)
        ]
        raw_data = {"candles": {"H1": flat_h1, "M15": flat_m15}}
        result = mod.process_candle(
            symbol="XAUUSD", raw_data=raw_data, kz="ny",
            timestamp_utc="2026-04-25T13:15:05+00:00",
        )
        assert result["action"] == "NO_FIRE"
        assert result["reason"] in ("NO_BOS", "NO_RECENT_BOS")


# ─────────────────────────────────────────────────────────────────────────
# State persistence
# ─────────────────────────────────────────────────────────────────────────


class TestStatePersistence:

    def test_state_round_trips_open_hypothetical(self, isolated_paths):
        """After ENTER, state on disk has the hypothetical in 'open'."""
        h1, m15 = _bullish_bos_path(m15_close=100.0)
        raw_data = {"candles": {"H1": h1, "M15": m15}}
        result = mod.process_candle(
            symbol="XAUUSD", raw_data=raw_data, kz="ny",
            timestamp_utc="2026-04-25T21:15:05+00:00",
        )
        assert result["action"] == "ENTER"

        # Per-symbol state file (since 2026-04-29). Reads sym_state directly,
        # no legacy {symbol: sym_state} wrapping.
        sym_state = json.loads(
            isolated_paths["state_for"]("XAUUSD").read_text(encoding="utf-8")
        )
        opens = sym_state.get("open", [])
        assert len(opens) == 1
        assert opens[0]["direction"] == "LONG"
        assert opens[0]["outcome"] is None
        assert sym_state.get("last_fire_date") == "2026-04-25"

    def test_state_independent_per_symbol(self, isolated_paths):
        """A fire on XAUUSD does NOT block USDJPY firing on the same day."""
        h1, m15 = _bullish_bos_path(m15_close=100.0)
        raw_data = {"candles": {"H1": h1, "M15": m15}}

        r1 = mod.process_candle(
            symbol="XAUUSD", raw_data=raw_data, kz="ny",
            timestamp_utc="2026-04-25T21:15:05+00:00",
        )
        assert r1["action"] == "ENTER"

        r2 = mod.process_candle(
            symbol="USDJPY", raw_data=raw_data, kz="ny",
            timestamp_utc="2026-04-25T21:15:05+00:00",
        )
        assert r2["action"] == "ENTER", f"USDJPY should fire independently: {r2}"
        records = _read_jsonl(isolated_paths["log"])
        assert len(records) == 2
        symbols = {r["symbol"] for r in records}
        assert symbols == {"XAUUSD", "USDJPY"}


# ─────────────────────────────────────────────────────────────────────────
# Outcome rewrite preserves un-resolved entries
# ─────────────────────────────────────────────────────────────────────────


class TestJsonlRewrite:

    def test_rewrite_preserves_other_records(self, isolated_paths):
        """Resolving record A must not mutate or drop unrelated record B."""
        # Fire on day 1.
        h1, m15 = _bullish_bos_path(m15_close=100.0)
        raw_data = {"candles": {"H1": h1, "M15": m15}}
        mod.process_candle(
            symbol="XAUUSD", raw_data=raw_data, kz="ny",
            timestamp_utc="2026-04-25T21:15:05+00:00",
        )
        # Drop a manual unrelated record into the JSONL.
        with open(isolated_paths["log"], "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "hypothesis_id": "MANUAL_OTHER",
                "outcome": None, "realized_r": None,
                "candle_time": "2026-04-25T22:00:00+00:00",
            }) + "\n")

        rec = [r for r in _read_jsonl(isolated_paths["log"])
               if r.get("hypothesis_id", "").startswith("XAUUSD_dumb_")][0]
        # Now resolve the XAUUSD record via TP touch on day 2.
        tp = rec["tp"]
        next_m15 = m15 + [_make_candle(
            "2026-04-26T13:15:00+00:00",
            o=rec["entry"], h=tp + 0.5, l=rec["entry"] - 0.1,
            c=tp - 0.05,
        )]
        raw_data2 = {"candles": {"H1": h1, "M15": next_m15}}
        mod.process_candle(
            symbol="XAUUSD", raw_data=raw_data2, kz="ny",
            timestamp_utc="2026-04-26T13:15:05+00:00",
        )

        all_records = _read_jsonl(isolated_paths["log"])
        manuals = [r for r in all_records if r.get("hypothesis_id") == "MANUAL_OTHER"]
        assert len(manuals) == 1
        assert manuals[0]["outcome"] is None  # untouched

        xauusd_resolved = [r for r in all_records
                          if r.get("hypothesis_id", "").startswith("XAUUSD_dumb_2026_04_25")]
        assert len(xauusd_resolved) == 1
        assert xauusd_resolved[0]["outcome"] == "TP"


# ─────────────────────────────────────────────────────────────────────────
# Outer-guard: orchestrator-style wrap never re-raises
# ─────────────────────────────────────────────────────────────────────────


class TestNeverRaises:

    def test_garbage_raw_data_returns_dict(self, isolated_paths):
        """A wildly malformed raw_data must produce a dict, not raise."""
        result = mod.process_candle(
            symbol="XAUUSD", raw_data={"candles": "not a dict"}, kz="ny",
            timestamp_utc="2026-04-25T13:15:05+00:00",
        )
        assert isinstance(result, dict)
        assert "action" in result

    def test_corrupt_state_file_recovers(self, isolated_paths):
        """A corrupt state.json on disk must not block firing — start clean."""
        isolated_paths["state"].write_text("not-valid-json{", encoding="utf-8")

        h1, m15 = _bullish_bos_path(m15_close=100.0)
        raw_data = {"candles": {"H1": h1, "M15": m15}}
        result = mod.process_candle(
            symbol="XAUUSD", raw_data=raw_data, kz="ny",
            timestamp_utc="2026-04-25T21:15:05+00:00",
        )
        assert result["action"] == "ENTER"
