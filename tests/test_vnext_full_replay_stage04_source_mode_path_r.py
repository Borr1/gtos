from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "research/science_program_2026_05/06_outcome_testing/"
    "vnext_full_historical_candidate_generation_replay_2026_05_24/"
    "build_vnext_full_replay_stage04_source_mode_path_r_2026_05_24.py"
)


def load_stage04_module():
    spec = importlib.util.spec_from_file_location("vnext_full_stage04", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _candidate() -> dict:
    return {
        "candidate_id": "cand_test",
        "source_universe_row_id": "denom_test",
        "market_state_packet_id": "msp_test",
        "source_origin": "market_bar_enumeration",
        "source_path": "data/test/XAUUSD_M15.csv",
        "source_sha256": "abc123",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "timeframe": "M15",
        "market_timeframe": "M15",
        "session_bucket": "ny_broad",
        "date_utc": "2026-05-01",
        "candle_time_utc": "2026-05-01 13:30:00",
        "side": "LONG",
        "framework": "ob_retest",
        "entry_reference": 100.0,
        "stop_or_invalidation": 99.0,
        "target_reference": 101.5,
        "rr": 1.5,
    }


def _series(stage04, lows, highs, closes):
    values = list(zip(lows, highs, closes))
    times = [
        datetime(2026, 5, 1, 13, 30 + index, tzinfo=timezone.utc)
        for index in range(len(values))
    ]
    if stage04.np is not None:
        lows = stage04.np.asarray(lows, dtype=float)
        highs = stage04.np.asarray(highs, dtype=float)
        closes = stage04.np.asarray(closes, dtype=float)
        opens = closes.copy()
        volumes = stage04.np.asarray([1.0] * len(values), dtype=float)
    else:
        opens = list(closes)
        volumes = [1.0] * len(values)
    return stage04.BarSeries(
        path=Path("data/test/XAUUSD_M1.csv"),
        symbol="XAUUSD",
        timeframe="M1",
        source_system="unit_test",
        times=times,
        opens=opens,
        highs=highs,
        lows=lows,
        closes=closes,
        volumes=volumes,
    )


def test_simulate_bar_path_target_stop_no_fill_and_same_bar():
    stage04 = load_stage04_module()
    event = stage04.event_from_candidate(_candidate())

    target = stage04.simulate_bar_path(
        event,
        _series(stage04, [100.2, 99.9, 100.6], [100.4, 100.2, 101.6], [100.3, 100.1, 101.5]),
        0,
        3,
        "m1_path_aware",
        "unit_test",
    )
    assert target["terminal_outcome"] == "target_first"
    assert target["simulated_r"] == 1.5

    stop = stage04.simulate_bar_path(
        event,
        _series(stage04, [100.2, 99.9, 98.8], [100.4, 100.2, 100.4], [100.3, 100.1, 99.0]),
        0,
        3,
        "m1_path_aware",
        "unit_test",
    )
    assert stop["terminal_outcome"] == "stop_first"
    assert stop["simulated_r"] == -1.0

    no_fill = stage04.simulate_bar_path(
        event,
        _series(stage04, [100.2, 100.3], [100.4, 100.6], [100.3, 100.5]),
        0,
        2,
        "m1_path_aware",
        "unit_test",
    )
    assert no_fill["terminal_outcome"] == "no_fill"
    assert no_fill["pending_lifecycle_state"] == "pending_expired_no_fill_48h"

    same_bar = stage04.simulate_bar_path(
        event,
        _series(stage04, [98.5], [102.0], [100.0]),
        0,
        1,
        "bar_close_m15",
        "unit_test",
    )
    assert same_bar["terminal_outcome"] == "same_bar_ambiguous_unresolved"
    assert same_bar["conservative_ambiguous_r"] == -1.0


def test_runtime_reference_row_preserves_no_price_path_boundary():
    stage04 = load_stage04_module()
    candidate = _candidate()
    event = stage04.event_from_candidate(candidate)
    rows = stage04.runtime_reference_rows(
        candidate,
        event,
        {
            "current_config_shadow": {
                "decision_summary": {"route_decision": "AVOID", "pending_would_action": "PLACE_LIMIT"}
            }
        },
    )

    assert rows[0]["replay_mode"] == "current_config_shadow"
    assert rows[0]["terminal_outcome"] == "runtime_trace_reference"
    assert rows[0]["price_path_truth_status"] == "not_claimed_runtime_reference_only"
    assert rows[0]["no_live_trading_or_broker_mutation"] is True


def test_source_repair_rows_bind_stage04_export_manifests():
    stage04 = load_stage04_module()
    export_rows, repair_rows = stage04.build_source_repair_rows()

    assert len(export_rows) == 76
    assert len(repair_rows) == 76
    assert all(row["readonly_mt5_export_executed"] is True for row in export_rows)
    assert all(row["terminal_disposition"] is True for row in export_rows)
    assert all(row["source_hashes"] for row in repair_rows)


def test_disagreement_detection_flags_ltf_terminal_change():
    stage04 = load_stage04_module()
    candidate = _candidate()
    base = {
        "candidate_id": "cand_test",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "candle_time_utc": "2026-05-01 13:30:00",
        "side": "LONG",
        "framework": "ob_retest",
    }
    rows = [
        base | {"replay_mode": "bar_close_m15", "terminal_outcome": "target_first", "simulated_r": 1.5},
        base | {"replay_mode": "m1_path_aware", "terminal_outcome": "stop_first", "simulated_r": -1.0},
    ]

    disagreements = stage04.disagreement_rows(candidate, rows)

    assert len(disagreements) == 1
    assert disagreements[0]["would_change_execution_or_decision"] is True
    assert disagreements[0]["ltf_terminal_outcome"] == "stop_first"
