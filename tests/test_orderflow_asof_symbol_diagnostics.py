from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest

from scripts import analyze_orderflow_asof_symbol_diagnostics as mod


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"orderflow_asof_symbol_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_candidate_context_by_symbol_splits_primary_rows():
    rows = [
        {
            "symbol": "NAS100",
            "is_primary_proxy": True,
            "data_status": "ok",
            "event_class": "candidate",
            "profile_event_price_volume_percentile": 0.4,
            "profile_nearest_lvn_distance_ticks": 10,
        },
        {
            "symbol": "NAS100",
            "is_primary_proxy": True,
            "data_status": "ok",
            "event_class": "structural_context",
            "profile_event_price_volume_percentile": 0.7,
            "profile_nearest_lvn_distance_ticks": 5,
        },
    ]
    out = mod.candidate_context_by_symbol(rows)
    assert out["NAS100"]["candidate"]["n"] == 1
    assert out["NAS100"]["context"]["n"] == 1
    assert out["NAS100"]["candidate_minus_context"]["profile_event_price_volume_percentile"] == pytest.approx(-0.3)
    assert out["NAS100"]["candidate_minus_context"]["profile_nearest_lvn_distance_ticks"] == 5


def test_outcome_by_symbol_splits_winners_losers():
    rows = [
        {
            "symbol": "XAUUSD",
            "candidate__synthetic_realized_r": 1.5,
            "pre60_signed_volume": 100,
        },
        {
            "symbol": "XAUUSD",
            "candidate__synthetic_realized_r": -1.0,
            "pre60_signed_volume": -50,
        },
    ]
    out = mod.outcome_by_symbol(rows)
    assert out["XAUUSD"]["winner"]["n"] == 1
    assert out["XAUUSD"]["loser"]["n"] == 1
    assert out["XAUUSD"]["winner_minus_loser"]["pre60_signed_volume"] == 150


def test_build_readout_flags_symbols_without_contrast():
    candidate_context = {
        "GBPUSD": {
            "candidate": {"n": 2},
            "context": {"n": 3},
            "candidate_minus_context": {
                "profile_event_price_volume_percentile": 0.1,
                "profile_nearest_lvn_distance_ticks": 1.0,
            },
        }
    }
    outcome = {
        "GBPUSD": {
            "winner": {"n": 2},
            "loser": {"n": 0},
            "winner_minus_loser": {},
        }
    }

    readout = mod.build_readout(candidate_context, outcome)

    assert any("GBPUSD has winner n=2 and loser n=0" in item for item in readout)
