"""Known-answer tests for the incremental tick-microstructure pipeline (feature derivation + store)."""
import json
import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.research_infra.validation_integrity.tick_microstructure_pipeline import (
    derive_bar_features, append_features,
)


def test_derive_features_known_answer():
    # 3 ticks in one H1 bar, rising mid -> 2 upticks, delta +2
    ticks = [
        {"time": "2026-01-01T10:00:00", "bid": 100.0, "ask": 100.2},  # mid 100.1
        {"time": "2026-01-01T10:05:00", "bid": 100.2, "ask": 100.4},  # mid 100.3 up
        {"time": "2026-01-01T10:50:00", "bid": 100.4, "ask": 100.6},  # mid 100.5 up
    ]
    f = derive_bar_features(ticks)
    assert set(f.keys()) == {"2026-01-01T10"}
    b = f["2026-01-01T10"]
    assert b["n_ticks"] == 3
    assert b["delta"] == 2  # 2 upticks, 0 downticks
    assert b["o"] == 100.1 and abs(b["c"] - 100.5) < 1e-9
    assert b["aggression"] == 2 / 3  # |delta|/n
    assert b["spread_mean"] > 0


def test_two_bars_and_downticks():
    ticks = [
        {"time": "2026-01-01T10:00:00", "bid": 50.0, "ask": 50.0},
        {"time": "2026-01-01T10:30:00", "bid": 49.0, "ask": 49.0},  # down
        {"time": "2026-01-01T11:00:00", "bid": 48.0, "ask": 48.0},  # down (new bar 11)
    ]
    f = derive_bar_features(ticks)
    assert "2026-01-01T10" in f and "2026-01-01T11" in f
    assert f["2026-01-01T10"]["delta"] == -1  # 50->49 within bar 10 = 1 downtick, delta -1


def test_append_store_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        sp = os.path.join(d, "store", "feat.jsonl")
        f = derive_bar_features([{"time": "2026-01-01T10:00:00", "bid": 1.0, "ask": 1.1},
                                 {"time": "2026-01-01T10:10:00", "bid": 1.1, "ask": 1.2}])
        n = append_features(f, "XAUUSD", sp)
        assert n == 1 and os.path.exists(sp)
        # append again -> grows (accumulation across windows)
        append_features(f, "XAUUSD", sp)
        rows = [json.loads(l) for l in open(sp)]
        assert len(rows) == 2 and rows[0]["symbol"] == "XAUUSD" and "delta" in rows[0]


if __name__ == "__main__":
    test_derive_features_known_answer(); test_two_bars_and_downticks(); test_append_store_roundtrip()
    print("tick_pipeline: 3/3 known-answer tests passed")
