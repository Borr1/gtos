"""Tests for T5.24 D1-bias-lag shadow logger.

Covers:
- Trigger condition (D1 contradicts both H1 and H4).
- No-log when D1 agrees with H1 or H4.
- H4-missing path (collapses to D1 != H1, tags h4_missing=True).
- Rolling consecutive counter increments / resets on mismatch / resets on UTC-day rollover.
- Alert fires once per threshold crossing (not every candle past threshold).
- Alert re-fires on a subsequent crossing after a reset.
- Defensive behaviour: malformed MSO, missing structure, non-directional values.

All writes go to ``tmp_path`` via module-ref monkeypatch on SHADOW_LOG_PATH and
STATE_PATH (session 21 canonical pattern — see MEMORY.md
`project_pytest_contamination_forensics`).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.components import d1_bias_lag_logger as mod


# ─────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────


class _Structure:
    """Minimal structure shim exposing ``direction``."""

    def __init__(self, direction):
        self.direction = direction


class _TFState:
    """Minimal timeframe state exposing ``structure.direction``."""

    def __init__(self, direction):
        self.structure = _Structure(direction) if direction is not None else None


class _MSO:
    """Minimal MSO shim exposing ``timeframes`` dict + ``timestamp_utc``."""

    def __init__(self, *, d1=None, h4=None, h1=None, m15=None, timestamp_utc=""):
        self.timeframes = {}
        for tf_name, direction in (("D1", d1), ("H4", h4), ("H1", h1), ("M15", m15)):
            if direction is not None:
                self.timeframes[tf_name] = _TFState(direction)
        self.timestamp_utc = timestamp_utc


@pytest.fixture
def isolated_paths(tmp_path, monkeypatch):
    """Redirect log + state paths into tmp_path via module-ref monkeypatch."""
    log_path = tmp_path / "d1_bias_lag.jsonl"
    state_path = tmp_path / ".d1_bias_lag_state.json"
    monkeypatch.setattr(mod, "SHADOW_LOG_PATH", log_path)
    monkeypatch.setattr(mod, "STATE_PATH", state_path)
    return {"log": log_path, "state": state_path}


@pytest.fixture
def no_alert_calls(monkeypatch):
    """Capture send_threshold_alert calls without actually invoking Telegram."""
    calls = []
    monkeypatch.setattr(mod, "_send_threshold_alert",
                        lambda record: calls.append(record) or True)
    return calls


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def _read_state(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


# ─────────────────────────────────────────────────────────────────────────
# Trigger condition
# ─────────────────────────────────────────────────────────────────────────


class TestTriggerCondition:
    """D1 contradicts both H1 and H4 → must log."""

    def test_bearish_d1_bullish_h4_bullish_h1_triggers(self, isolated_paths, no_alert_calls):
        """NAS100 W14 scenario: D1 bearish, H4 bullish, H1 bullish."""
        mso = _MSO(d1="bearish", h4="bullish", h1="bullish")
        record = mod.log_if_d1_bias_lag(
            mso=mso, symbol="NAS100", timestamp_utc="2026-04-07T09:00:00+00:00",
            kill_zone="london",
        )
        assert record is not None
        assert record["d1_bias"] == "bearish"
        assert record["h4_bias"] == "bullish"
        assert record["h1_direction"] == "bullish"
        assert record["kill_zone"] == "london"
        assert record["h4_missing"] is False
        assert record["rolling_N_consecutive"] == 1
        assert record["symbol"] == "NAS100"
        assert record["timestamp"] == "2026-04-07T09:00:00+00:00"

        # Persisted to JSONL
        entries = _read_jsonl(isolated_paths["log"])
        assert len(entries) == 1
        assert entries[0] == record

    def test_bullish_d1_bearish_h4_bearish_h1_triggers(self, isolated_paths, no_alert_calls):
        """Mirror image: D1 bullish, H4/H1 bearish — same pattern, opposite direction."""
        mso = _MSO(d1="bullish", h4="bearish", h1="bearish")
        record = mod.log_if_d1_bias_lag(
            mso=mso, symbol="XAUUSD", timestamp_utc="2026-04-10T13:15:00+00:00",
        )
        assert record is not None
        assert record["d1_bias"] == "bullish"
        assert record["h4_bias"] == "bearish"
        assert record["h1_direction"] == "bearish"


# ─────────────────────────────────────────────────────────────────────────
# No-log scenarios
# ─────────────────────────────────────────────────────────────────────────


class TestNoLog:
    """D1 agrees with at least one of H1/H4 → must NOT log."""

    def test_d1_agrees_with_h4(self, isolated_paths, no_alert_calls):
        """D1=bullish, H4=bullish, H1=bearish — D1 agrees with H4, no log."""
        mso = _MSO(d1="bullish", h4="bullish", h1="bearish")
        record = mod.log_if_d1_bias_lag(
            mso=mso, symbol="XAUUSD", timestamp_utc="2026-04-10T13:00:00+00:00",
        )
        assert record is None
        assert _read_jsonl(isolated_paths["log"]) == []

    def test_d1_agrees_with_h1(self, isolated_paths, no_alert_calls):
        """D1=bearish, H4=bullish, H1=bearish — D1 agrees with H1, no log."""
        mso = _MSO(d1="bearish", h4="bullish", h1="bearish")
        record = mod.log_if_d1_bias_lag(
            mso=mso, symbol="XAUUSD", timestamp_utc="2026-04-10T13:00:00+00:00",
        )
        assert record is None
        assert _read_jsonl(isolated_paths["log"]) == []

    def test_full_agreement(self, isolated_paths, no_alert_calls):
        """All three directional and agreeing — no log."""
        mso = _MSO(d1="bullish", h4="bullish", h1="bullish")
        assert mod.log_if_d1_bias_lag(
            mso=mso, symbol="XAUUSD", timestamp_utc="2026-04-10T13:00:00+00:00",
        ) is None

    def test_d1_not_directional(self, isolated_paths, no_alert_calls):
        """D1=transitional is NOT directional → no log."""
        mso = _MSO(d1="transitional", h4="bullish", h1="bullish")
        assert mod.log_if_d1_bias_lag(
            mso=mso, symbol="XAUUSD", timestamp_utc="2026-04-10T13:00:00+00:00",
        ) is None

    def test_h1_not_directional(self, isolated_paths, no_alert_calls):
        """H1=insufficient_data is NOT directional → no log (H1 is required)."""
        mso = _MSO(d1="bearish", h4="bullish", h1="insufficient_data")
        assert mod.log_if_d1_bias_lag(
            mso=mso, symbol="XAUUSD", timestamp_utc="2026-04-10T13:00:00+00:00",
        ) is None

    def test_d1_missing_entirely(self, isolated_paths, no_alert_calls):
        """No D1 timeframe → no log."""
        mso = _MSO(d1=None, h4="bullish", h1="bullish")
        assert mod.log_if_d1_bias_lag(
            mso=mso, symbol="XAUUSD", timestamp_utc="2026-04-10T13:00:00+00:00",
        ) is None


# ─────────────────────────────────────────────────────────────────────────
# H4-missing path
# ─────────────────────────────────────────────────────────────────────────


class TestH4Missing:
    """When H4 is non-directional or absent, collapse to D1 != H1 and tag."""

    def test_h4_missing_triggers_when_d1_ne_h1(self, isolated_paths, no_alert_calls):
        mso = _MSO(d1="bearish", h4=None, h1="bullish")
        record = mod.log_if_d1_bias_lag(
            mso=mso, symbol="US30_cash", timestamp_utc="2026-04-10T14:00:00+00:00",
        )
        assert record is not None
        assert record["h4_missing"] is True
        assert record["h4_bias"] is None
        assert record["d1_bias"] == "bearish"
        assert record["h1_direction"] == "bullish"

    def test_h4_non_directional_triggers(self, isolated_paths, no_alert_calls):
        """H4=transitional is non-directional → h4_missing path."""
        mso = _MSO(d1="bearish", h4="transitional", h1="bullish")
        record = mod.log_if_d1_bias_lag(
            mso=mso, symbol="US30_cash", timestamp_utc="2026-04-10T14:00:00+00:00",
        )
        assert record is not None
        assert record["h4_missing"] is True
        assert record["h4_bias"] == "transitional"

    def test_h4_missing_no_log_when_d1_eq_h1(self, isolated_paths, no_alert_calls):
        """With H4 missing, D1=H1=bullish → no contradiction, no log."""
        mso = _MSO(d1="bullish", h4=None, h1="bullish")
        assert mod.log_if_d1_bias_lag(
            mso=mso, symbol="US30_cash", timestamp_utc="2026-04-10T14:00:00+00:00",
        ) is None


# ─────────────────────────────────────────────────────────────────────────
# Rolling counter
# ─────────────────────────────────────────────────────────────────────────


class TestRollingCounter:
    """Consecutive-count logic: increment, reset, per-symbol, UTC-day rollover."""

    def test_counter_increments_on_consecutive_triggers(self, isolated_paths, no_alert_calls):
        mso = _MSO(d1="bearish", h4="bullish", h1="bullish")
        counts = []
        for hour in range(5):
            rec = mod.log_if_d1_bias_lag(
                mso=mso, symbol="NAS100",
                timestamp_utc=f"2026-04-07T{hour:02d}:00:00+00:00",
            )
            counts.append(rec["rolling_N_consecutive"])
        assert counts == [1, 2, 3, 4, 5]

    def test_counter_resets_on_clean_candle(self, isolated_paths, no_alert_calls):
        """Any non-triggering candle resets the streak to zero."""
        trigger = _MSO(d1="bearish", h4="bullish", h1="bullish")
        clean = _MSO(d1="bullish", h4="bullish", h1="bullish")  # D1 agrees

        mod.log_if_d1_bias_lag(trigger, "NAS100", "2026-04-07T00:00:00+00:00")
        mod.log_if_d1_bias_lag(trigger, "NAS100", "2026-04-07T01:00:00+00:00")
        # After these, state should have consecutive=2.
        st_before = _read_state(isolated_paths["state"])
        assert st_before["NAS100"]["consecutive"] == 2

        # Clean candle — no log, state reset.
        mod.log_if_d1_bias_lag(clean, "NAS100", "2026-04-07T02:00:00+00:00")
        st_after = _read_state(isolated_paths["state"])
        assert st_after["NAS100"]["consecutive"] == 0
        assert st_after["NAS100"]["last_alert_threshold"] == 0

        # Next trigger should start at 1 again, not resume at 3.
        rec = mod.log_if_d1_bias_lag(trigger, "NAS100", "2026-04-07T03:00:00+00:00")
        assert rec["rolling_N_consecutive"] == 1

    def test_counter_resets_on_new_utc_day(self, isolated_paths, no_alert_calls):
        """A timestamp on a new UTC date resets the counter."""
        trigger = _MSO(d1="bearish", h4="bullish", h1="bullish")

        # Day 1
        for hour in range(3):
            mod.log_if_d1_bias_lag(
                trigger, "NAS100", f"2026-04-07T{hour:02d}:00:00+00:00"
            )
        st = _read_state(isolated_paths["state"])
        assert st["NAS100"]["consecutive"] == 3
        assert st["NAS100"]["date"] == "2026-04-07"

        # Day 2 — first trigger restarts from 1
        rec = mod.log_if_d1_bias_lag(
            trigger, "NAS100", "2026-04-08T00:00:00+00:00"
        )
        assert rec["rolling_N_consecutive"] == 1
        st2 = _read_state(isolated_paths["state"])
        assert st2["NAS100"]["consecutive"] == 1
        assert st2["NAS100"]["date"] == "2026-04-08"
        assert st2["NAS100"]["last_alert_threshold"] == 0

    def test_per_symbol_counters_are_independent(self, isolated_paths, no_alert_calls):
        """Different symbols maintain separate streaks."""
        trigger = _MSO(d1="bearish", h4="bullish", h1="bullish")
        mod.log_if_d1_bias_lag(trigger, "NAS100", "2026-04-07T00:00:00+00:00")
        mod.log_if_d1_bias_lag(trigger, "NAS100", "2026-04-07T01:00:00+00:00")
        rec_xau = mod.log_if_d1_bias_lag(trigger, "XAUUSD", "2026-04-07T00:00:00+00:00")
        assert rec_xau["rolling_N_consecutive"] == 1

        st = _read_state(isolated_paths["state"])
        assert st["NAS100"]["consecutive"] == 2
        assert st["XAUUSD"]["consecutive"] == 1


# ─────────────────────────────────────────────────────────────────────────
# Alert debouncing
# ─────────────────────────────────────────────────────────────────────────


class TestAlertDebounce:
    """Threshold alert fires once per crossing, not every candle past threshold."""

    def test_alert_fires_once_at_threshold(self, isolated_paths, no_alert_calls):
        """20 consecutive triggers → exactly 1 alert at count=20."""
        trigger = _MSO(d1="bearish", h4="bullish", h1="bullish")
        for i in range(25):
            mod.log_if_d1_bias_lag(
                trigger, "NAS100", f"2026-04-07T{i:02d}:00:00+00:00",
                alert_threshold_consecutive=20,
            )
        # Only 1 alert between count=1..25 (fires at count=20)
        assert len(no_alert_calls) == 1
        assert no_alert_calls[0]["rolling_N_consecutive"] == 20

    def test_alert_does_not_fire_below_threshold(self, isolated_paths, no_alert_calls):
        trigger = _MSO(d1="bearish", h4="bullish", h1="bullish")
        for i in range(19):
            mod.log_if_d1_bias_lag(
                trigger, "NAS100", f"2026-04-07T{i:02d}:00:00+00:00",
                alert_threshold_consecutive=20,
            )
        assert no_alert_calls == []

    def test_alert_re_fires_after_reset(self, isolated_paths, no_alert_calls):
        """Streak reset clears the debounce — next crossing alerts again."""
        trigger = _MSO(d1="bearish", h4="bullish", h1="bullish")
        clean = _MSO(d1="bullish", h4="bullish", h1="bullish")

        # First crossing at count=20
        for i in range(20):
            mod.log_if_d1_bias_lag(
                trigger, "NAS100", f"2026-04-07T{i:02d}:00:00+00:00",
                alert_threshold_consecutive=20,
            )
        assert len(no_alert_calls) == 1

        # Reset
        mod.log_if_d1_bias_lag(clean, "NAS100", "2026-04-07T20:00:00+00:00",
                               alert_threshold_consecutive=20)

        # Second crossing — use different hour stamps to keep them readable.
        for i in range(20):
            mod.log_if_d1_bias_lag(
                trigger, "NAS100", f"2026-04-07T21:{i:02d}:00+00:00",
                alert_threshold_consecutive=20,
            )
        assert len(no_alert_calls) == 2
        assert no_alert_calls[-1]["rolling_N_consecutive"] == 20

    def test_alert_re_fires_on_fresh_multiple(self, isolated_paths, no_alert_calls):
        """Very long streak: alert again when crossing 2x, 3x etc. of threshold."""
        trigger = _MSO(d1="bearish", h4="bullish", h1="bullish")
        # 45 consecutive → crosses 20 and 40
        for i in range(45):
            # Spread across multiple hours so we generate unique-enough stamps
            h, m = divmod(i, 4)
            mod.log_if_d1_bias_lag(
                trigger, "NAS100", f"2026-04-07T{h:02d}:{m * 15:02d}:00+00:00",
                alert_threshold_consecutive=20,
            )
        assert len(no_alert_calls) == 2
        # First at count=20, second at count=40
        counts = [c["rolling_N_consecutive"] for c in no_alert_calls]
        assert counts == [20, 40]

    def test_custom_threshold(self, isolated_paths, no_alert_calls):
        """Threshold is configurable per-call."""
        trigger = _MSO(d1="bearish", h4="bullish", h1="bullish")
        for i in range(5):
            mod.log_if_d1_bias_lag(
                trigger, "NAS100", f"2026-04-07T{i:02d}:00:00+00:00",
                alert_threshold_consecutive=3,
            )
        # Crossings at 3 (first time count >= 3); next fresh multiple is 6 — not reached.
        assert len(no_alert_calls) == 1
        assert no_alert_calls[0]["rolling_N_consecutive"] == 3


# ─────────────────────────────────────────────────────────────────────────
# Defensive / edge cases
# ─────────────────────────────────────────────────────────────────────────


class TestDefensive:
    """Malformed inputs must never raise."""

    def test_none_mso_returns_none(self, isolated_paths, no_alert_calls):
        assert mod.log_if_d1_bias_lag(
            None, "NAS100", "2026-04-07T00:00:00+00:00",
        ) is None

    def test_mso_without_timeframes_returns_none(self, isolated_paths, no_alert_calls):
        class EmptyMSO:
            pass
        assert mod.log_if_d1_bias_lag(
            EmptyMSO(), "NAS100", "2026-04-07T00:00:00+00:00",
        ) is None

    def test_structure_without_direction(self, isolated_paths, no_alert_calls):
        """A structure object with no ``direction`` attr should be treated as missing."""
        class WeirdStructure:
            pass

        class WeirdTF:
            structure = WeirdStructure()

        class MSO:
            timeframes = {"D1": WeirdTF(), "H4": WeirdTF(), "H1": WeirdTF()}

        assert mod.log_if_d1_bias_lag(
            MSO(), "NAS100", "2026-04-07T00:00:00+00:00",
        ) is None

    def test_unparseable_timestamp_does_not_crash(self, isolated_paths, no_alert_calls):
        """Garbage timestamp falls back to process UTC date, still logs."""
        mso = _MSO(d1="bearish", h4="bullish", h1="bullish")
        record = mod.log_if_d1_bias_lag(
            mso=mso, symbol="NAS100", timestamp_utc="not-a-date",
        )
        assert record is not None
        assert record["timestamp"] == "not-a-date"
        assert record["rolling_N_consecutive"] == 1
        # State file uses today's UTC date
        st = _read_state(isolated_paths["state"])
        assert "NAS100" in st
        assert len(st["NAS100"]["date"]) == 10  # YYYY-MM-DD

    def test_jsonl_append_creates_parseable_rows_and_lock_file(self, isolated_paths, no_alert_calls):
        """Append path emits complete JSONL rows and uses a sidecar lock file."""
        trigger = _MSO(d1="bearish", h4="bullish", h1="bullish")
        for i in range(3):
            mod.log_if_d1_bias_lag(
                trigger,
                "NAS100",
                f"2026-04-07T0{i}:00:00+00:00",
            )

        rows = _read_jsonl(isolated_paths["log"])
        assert [row["rolling_N_consecutive"] for row in rows] == [1, 2, 3]
        assert isolated_paths["log"].with_suffix(".jsonl.lock").exists()
