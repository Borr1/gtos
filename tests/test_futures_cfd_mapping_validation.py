from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest

from scripts import run_futures_cfd_mapping_validation as mod
from src.research_infra.futures_cfd_mapping import MappingPair


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"futures_cfd_mapping_validation_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_parse_csv_ints():
    assert mod.parse_csv_ints("-240,-180,0") == [-240, -180, 0]


def test_primary_score_uses_primary_pairs_only():
    class D:
        def __init__(self, fut, mt5, corr, aligned=100):
            self.futures_symbol = fut
            self.mt5_symbol = mt5
            self.zero_lag_return_corr = corr
            self.aligned_minutes = aligned

    score = mod._primary_score(
        [
            D("GC.v.0", "XAUUSD", 0.9),
            D("NQ.v.0", "NAS100", -0.8),
            D("ES.v.0", "US30_cash", 0.1),
        ]
    )
    assert score["primary_count"] == 2
    assert score["median_abs_corr"] == 0.8500000000000001
    assert score["min_abs_corr"] == 0.8


def test_primary_score_can_use_custom_pair_set():
    class D:
        def __init__(self, fut, mt5, corr, aligned=100):
            self.futures_symbol = fut
            self.mt5_symbol = mt5
            self.zero_lag_return_corr = corr
            self.aligned_minutes = aligned

    score = mod._primary_score(
        [D("SI.v.0", "XAGUSD", 0.91)],
        primary_pair_keys={("SI.v.0", "XAGUSD")},
    )

    assert score["primary_count"] == 1
    assert score["min_abs_corr"] == 0.91


def test_format_pair_preserves_inverse_transform():
    assert mod.format_pair(MappingPair("6J.v.0", "USDJPY", "inverse_return")) == "6J.v.0:USDJPY:inverse_return"


def test_build_synthesis_keeps_no_alpha_claim():
    windows = [
        {
            "selected_shift_minutes": -180,
            "window_id": "w1",
            "selected_score": {
                "min_abs_corr": 0.9,
                "median_abs_corr": 0.95,
            },
        },
        {
            "selected_shift_minutes": -180,
            "window_id": "w2",
            "selected_score": {
                "min_abs_corr": 0.88,
                "median_abs_corr": 0.96,
            },
        },
    ]
    synthesis = mod.build_synthesis(windows)
    assert "not an alpha" in synthesis["summary"]
    assert "Timestamp correction is stable" in synthesis["bullets"][1]
    assert synthesis["ambiguities"]
    assert synthesis["next_steps"]
