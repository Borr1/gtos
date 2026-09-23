"""News join is candidate-symbol, not occupancy. GBP into a USD HIGH must hold."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(r"C:\Users\trader\intel-layer\calendar")
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import join_official_high as join  # noqa: E402


def test_warsh_usd_high_joins_gbpusd_candidate_not_occupancy():
    now = datetime(2026, 8, 28, 14, 1, tzinfo=timezone.utc)
    tape = {
        "schema": "gtos.live.news_tape.v1",
        "occupied": ["XAUUSD", "ETHUSD"],
        "candidates": ["GBPUSD", "EURUSD", "US30"],
        "hold": None,
    }
    brief = {
        "events": [{
            "official_high": True,
            "name": "Fed Chair Kevin Warsh Jackson Hole remarks",
            "time_utc": "2026-08-28T14:00:00Z",
            "tickets": ["US30", "EURUSD", "GER40"],
            "currency": "USD",
        }]
    }
    spine = {"events": []}
    merged = join.merge_official_high(tape, now=now, brief=brief, spine=spine)
    hold = merged.get("hold") or {}
    assert hold.get("reason") == "named_official_high_candidate_symbol"
    symbols = set(hold.get("symbols") or [])
    assert "GBPUSD" in symbols
    assert "EURUSD" in symbols
    assert "US30" in symbols


def test_occupancy_only_does_not_skip_gbp_candidate():
    now = datetime(2026, 8, 28, 14, 1, tzinfo=timezone.utc)
    tape = {"occupied": ["GER40", "US30"], "hold": None}
    brief = {
        "events": [{
            "official_high": True,
            "name": "Fed Chair Kevin Warsh Jackson Hole remarks",
            "time_utc": "2026-08-28T14:00:00Z",
            "tickets": ["US30", "EURUSD", "GER40"],
            "currency": "USD",
        }]
    }
    merged = join.merge_official_high(
        tape, now=now, brief=brief, spine={"events": []},
        candidates=["GBPUSD"],
    )
    hold = merged.get("hold") or {}
    assert "GBPUSD" in set(hold.get("symbols") or [])
