from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest

from scripts import audit_usdjpy_6j_followup_validation as mod


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"usdjpy_6j_followup_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _window(window_id: str, shift: int, corr: float, direction: float = 0.95):
    return {
        "window_id": window_id,
        "futures_start_utc": window_id.split("_")[0] + ":00+00:00",
        "selected_shift_minutes": shift,
        "selected_diagnostics": [
            {
                "futures_symbol": "6J.v.0",
                "mt5_symbol": "USDJPY",
                "return_transform": "inverse_return",
                "aligned_minutes": 100,
                "zero_lag_return_corr": corr,
                "directional_agreement": direction,
                "best_lag_minutes": 0,
            }
        ],
    }


def test_expected_shift_policy_switches_on_transition_date():
    assert mod.expected_shift_for_date("2026-03-06", "2026-03-09") == -120
    assert mod.expected_shift_for_date("2026-03-09", "2026-03-09") == -180


def test_followup_status_keeps_review_open_for_single_weak_window():
    validation = {
        "windows": [
            _window("2026-03-06T07:00_2026-03-06T16:59", -120, 0.96),
            _window("2026-03-09T07:00_2026-03-09T16:59", -180, 0.94),
            _window("2026-04-02T07:00_2026-04-02T16:59", -180, 0.91),
            _window("2026-04-23T07:00_2026-04-23T16:59", -180, 0.86),
            _window("2026-04-24T07:00_2026-04-24T16:59", -180, 0.90),
            _window("2026-04-27T07:00_2026-04-27T16:59", -180, 0.82),
        ]
    }

    payload = mod.build_payload(validation, input_path="validation.json", min_windows=6)

    assert payload["decision_readout"]["status"] == "REVIEW_REMAINS_OPEN_SINGLE_WEAK_WINDOW"
    assert payload["decision_readout"]["corr_pass_count"] == 5
    assert payload["decision_readout"]["weak_windows"] == ["2026-04-27T07:00_2026-04-27T16:59"]
    assert payload["registration_verdict"] == "NO_PROXY_MAP_ACTIVATION"


def test_followup_status_passes_when_all_windows_clear_gates():
    validation = {
        "windows": [
            _window("2026-03-06T07:00_2026-03-06T16:59", -120, 0.96),
            _window("2026-03-09T07:00_2026-03-09T16:59", -180, 0.94),
            _window("2026-04-02T07:00_2026-04-02T16:59", -180, 0.91),
        ]
    }

    payload = mod.build_payload(validation, input_path="validation.json", min_windows=3)

    assert payload["decision_readout"]["status"] == "STRICT_TRANSFER_PASS"
    assert payload["decision_readout"]["strict_transfer_pass"] is True
