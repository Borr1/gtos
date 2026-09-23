"""Tests for scripts/analyze_prescreen_kills.py."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.analyze_prescreen_kills import (
    _check_ob_retest_preconditions,
    _time_in_kz,
)


# ── _time_in_kz tests ──


def test_time_in_london_kz():
    assert _time_in_kz("2024-04-10T07:15:00Z", (7, 0), (10, 30)) is True
    assert _time_in_kz("2024-04-10T09:30:00Z", (7, 0), (10, 30)) is True
    assert _time_in_kz("2024-04-10T10:30:00Z", (7, 0), (10, 30)) is True
    assert _time_in_kz("2024-04-10T06:59:00Z", (7, 0), (10, 30)) is False
    assert _time_in_kz("2024-04-10T10:31:00Z", (7, 0), (10, 30)) is False


def test_time_in_ny_kz():
    assert _time_in_kz("2024-04-10T13:15:00Z", (13, 0), (15, 30)) is True
    assert _time_in_kz("2024-04-10T15:30:00Z", (13, 0), (15, 30)) is True
    assert _time_in_kz("2024-04-10T12:59:00Z", (13, 0), (15, 30)) is False


# ── _check_ob_retest_preconditions tests ──


def _make_mock_swing(type_, price, time_, index=0):
    s = MagicMock()
    s.type = type_
    s.price = price
    s.time = time_
    s.index = index
    return s


def _make_mock_event(type_, direction, level, time_, disp=False):
    e = MagicMock()
    e.type = type_
    e.direction = direction
    e.level_broken = level
    e.time = time_
    e.displacement_present = disp
    return e


def _make_mock_ob(type_, high, low, mitigated=False, formation_time="2024-04-10T06:00:00Z", causing="BOS"):
    ob = MagicMock()
    ob.type = type_
    ob.high = high
    ob.low = low
    ob.mitigated = mitigated
    ob.formation_time = formation_time
    ob.causing_event_type = causing
    return ob


def _make_mock_mso(h1_events=None, h1_obs=None, m15_events=None):
    """Build a mock MSO with the given H1/M15 data."""
    mso = MagicMock()
    h1 = MagicMock()
    h1.structure_events = h1_events or []
    h1.order_blocks = h1_obs or []

    m15 = MagicMock()
    m15.structure_events = m15_events or []
    m15.swings = []

    mso.timeframes = {"H1": h1, "M15": m15}
    return mso


def test_all_preconditions_met():
    """Candle overlaps bullish OB + H1 BOS exists → all_preconditions_met."""
    mso = _make_mock_mso(
        h1_events=[_make_mock_event("BOS", "bullish", 2350.0, "2024-04-10T05:00:00Z")],
        h1_obs=[_make_mock_ob("bullish", high=2340.0, low=2335.0, mitigated=False)],
    )
    raw_data = {
        "timestamp_utc": "2024-04-10T07:15:00Z",
        "candles": {"M15": [{"time": "2024-04-10T07:15:00Z", "open": 2342.0, "high": 2345.0, "low": 2338.0, "close": 2341.0}]},
    }
    result = _check_ob_retest_preconditions(mso, raw_data, "london")
    assert result["all_preconditions_met"] is True
    assert result["h1_has_structural_break"] is True
    assert result["price_at_ob"] is True


def test_price_not_at_ob():
    """Candle doesn't reach OB zone → price_at_ob is False."""
    mso = _make_mock_mso(
        h1_events=[_make_mock_event("BOS", "bullish", 2350.0, "2024-04-10T05:00:00Z")],
        h1_obs=[_make_mock_ob("bullish", high=2300.0, low=2295.0, mitigated=False)],
    )
    raw_data = {
        "timestamp_utc": "2024-04-10T07:15:00Z",
        "candles": {"M15": [{"time": "2024-04-10T07:15:00Z", "open": 2342.0, "high": 2345.0, "low": 2338.0, "close": 2341.0}]},
    }
    result = _check_ob_retest_preconditions(mso, raw_data, "london")
    assert result["all_preconditions_met"] is False
    assert result["h1_has_structural_break"] is True
    assert result["price_at_ob"] is False


def test_no_h1_break():
    """No H1 structure events → h1_has_structural_break is False."""
    mso = _make_mock_mso(
        h1_events=[],
        h1_obs=[_make_mock_ob("bullish", high=2340.0, low=2335.0, mitigated=False)],
    )
    raw_data = {
        "timestamp_utc": "2024-04-10T07:15:00Z",
        "candles": {"M15": [{"time": "2024-04-10T07:15:00Z", "open": 2342.0, "high": 2345.0, "low": 2338.0, "close": 2341.0}]},
    }
    result = _check_ob_retest_preconditions(mso, raw_data, "london")
    assert result["all_preconditions_met"] is False
    assert result["h1_has_structural_break"] is False


def test_mitigated_obs_excluded():
    """Mitigated OBs should not count toward preconditions."""
    mso = _make_mock_mso(
        h1_events=[_make_mock_event("BOS", "bullish", 2350.0, "2024-04-10T05:00:00Z")],
        h1_obs=[_make_mock_ob("bullish", high=2340.0, low=2335.0, mitigated=True)],
    )
    raw_data = {
        "timestamp_utc": "2024-04-10T07:15:00Z",
        "candles": {"M15": [{"time": "2024-04-10T07:15:00Z", "open": 2342.0, "high": 2345.0, "low": 2338.0, "close": 2341.0}]},
    }
    result = _check_ob_retest_preconditions(mso, raw_data, "london")
    assert result["all_preconditions_met"] is False
    assert len(result["h1_unmitigated_obs"]) == 0


def test_bearish_ob_touch():
    """Candle reaches bearish OB zone → price_at_ob True."""
    mso = _make_mock_mso(
        h1_events=[_make_mock_event("BOS", "bearish", 2300.0, "2024-04-10T05:00:00Z")],
        h1_obs=[_make_mock_ob("bearish", high=2360.0, low=2355.0, mitigated=False)],
    )
    raw_data = {
        "timestamp_utc": "2024-04-10T13:15:00Z",
        "candles": {"M15": [{"time": "2024-04-10T13:15:00Z", "open": 2354.0, "high": 2358.0, "low": 2352.0, "close": 2356.0}]},
    }
    result = _check_ob_retest_preconditions(mso, raw_data, "ny")
    assert result["price_at_ob"] is True
    assert result["all_preconditions_met"] is True


def test_no_m15_candles():
    """Missing M15 candles in raw_data → price_at_ob remains False."""
    mso = _make_mock_mso(
        h1_events=[_make_mock_event("BOS", "bullish", 2350.0, "2024-04-10T05:00:00Z")],
        h1_obs=[_make_mock_ob("bullish", high=2340.0, low=2335.0, mitigated=False)],
    )
    raw_data = {
        "timestamp_utc": "2024-04-10T07:15:00Z",
        "candles": {"M15": []},
    }
    result = _check_ob_retest_preconditions(mso, raw_data, "london")
    assert result["price_at_ob"] is False
    assert result["all_preconditions_met"] is False


def test_m15_structural_activity():
    """M15 structure events flagged correctly."""
    mso = _make_mock_mso(
        h1_events=[_make_mock_event("BOS", "bullish", 2350.0, "2024-04-10T05:00:00Z")],
        h1_obs=[],
        m15_events=[_make_mock_event("CHoCH", "bullish", 2339.0, "2024-04-10T07:30:00Z")],
    )
    raw_data = {
        "timestamp_utc": "2024-04-10T07:30:00Z",
        "candles": {"M15": [{"time": "2024-04-10T07:30:00Z", "open": 2340.0, "high": 2342.0, "low": 2338.0, "close": 2341.0}]},
    }
    result = _check_ob_retest_preconditions(mso, raw_data, "london")
    assert result["m15_structural_activity"] is True
    assert len(result["m15_structure_events"]) == 1
