from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest

from scripts import join_orderflow_features_to_candidate_outcomes as mod


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"orderflow_candidate_join_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_normalize_symbol_maps_us30_cash():
    assert mod.normalize_symbol("US30_cash") == "US30"
    assert mod.normalize_symbol("NAS100") == "NAS100"


def test_build_joined_rows_matches_primary_candidate_by_symbol_and_close():
    feature_payload = {
        "feature_rows": [
            {
                "event_id": "e1",
                "is_primary_proxy": True,
                "event_class": "candidate",
                "symbol": "US30_cash",
                "canonical_m15_close_utc": "2026-04-17T13:15:00+00:00",
                "event15_signed_volume": 5,
            },
            {
                "event_id": "e2",
                "is_primary_proxy": False,
                "event_class": "candidate",
                "symbol": "US30_cash",
                "canonical_m15_close_utc": "2026-04-17T13:15:00+00:00",
            },
        ]
    }
    candidate_rows = [
        {
            "candidate__symbol": "US30",
            "candidate__candle_close_utc": "2026-04-17T13:15:00+00:00",
            "candidate__synthetic_realized_r": -1.0,
        }
    ]
    rows = mod.build_joined_rows(feature_payload, candidate_rows)
    assert len(rows) == 1
    assert rows[0]["candidate_join_matched"] is True
    assert rows[0]["candidate__synthetic_realized_r"] == -1.0


def test_summarize_counts_winners_and_losers():
    joined = [
        {
            "candidate_join_matched": True,
            "candidate__synthetic_realized_r": 1.5,
            "symbol": "XAUUSD",
            "event15_signed_volume": 10,
        },
        {
            "candidate_join_matched": True,
            "candidate__synthetic_realized_r": -1.0,
            "symbol": "XAUUSD",
            "event15_signed_volume": -10,
        },
    ]
    summary = mod.summarize(joined)
    assert summary["target_available"] == 2
    assert summary["winner_count"] == 1
    assert summary["loser_count"] == 1
    assert summary["winner_medians"]["event15_signed_volume"] == 10
    assert summary["loser_medians"]["event15_signed_volume"] == -10


def test_readout_flags_symbol_without_loser_contrast():
    readout = mod.build_readout_bullets(
        2,
        {
            "GBPUSD": {
                "n": 2,
                "wins": 2,
                "losses": 0,
                "mean_synthetic_r": 1.5,
                "win_rate": 1.0,
            }
        },
    )

    assert any("GBPUSD has no loser contrast" in item for item in readout)
