from __future__ import annotations

import json
import shutil
import struct
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts import extract_sierra_depth_features as mod


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"sierra_depth_features_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _us(value: datetime) -> int:
    return mod.sierra_us(value)


def _write_depth(path: Path, records: list[tuple]) -> None:
    with path.open("wb") as handle:
        handle.write(mod.HEADER_STRUCT.pack(mod.MAGIC, 64, mod.RECORD_STRUCT.size, 1))
        handle.write(b"\0" * 48)
        for record in records:
            handle.write(mod.RECORD_STRUCT.pack(*record))


def _record(ts: str, command: int, flags: int, price: float, quantity: int, orders: int = 1) -> tuple:
    return (
        _us(datetime.fromisoformat(ts.replace("Z", "+00:00"))),
        command,
        flags,
        orders,
        price,
        quantity,
        0,
    )


def test_header_validation_rejects_bad_magic(tmp_path):
    path = tmp_path / "bad.depth"
    path.write_bytes(struct.pack("<IIII", 0, 64, mod.RECORD_STRUCT.size, 1) + b"\0" * 48)

    with pytest.raises(ValueError, match="invalid magic"):
        mod.read_header(path)


def test_snapshot_features_top_depth_and_imbalance():
    features = mod.snapshot_features(
        bids={100.0: (10, 2), 99.75: (5, 1)},
        asks={100.25: (3, 1), 100.5: (7, 2)},
        timestamp_us=_us(datetime(2026, 4, 28, 7, 29, 59, tzinfo=timezone.utc)),
        tick_size=0.25,
    )

    assert features["best_bid"] == 100.0
    assert features["best_ask"] == 100.25
    assert features["spread_ticks"] == 1
    assert features["total_depth10"] == 25
    assert features["depth10_imbalance"] == pytest.approx(0.2)
    assert features["top_10_num_orders_bid"] == 3
    assert features["top_10_num_orders_ask"] == 3


def test_snapshot_features_mbp10_wall_and_near_far_definitions():
    features = mod.snapshot_features(
        bids={
            100.0: (10, 2),
            99.75: (5, 1),
            99.5: (4, 1),
            99.25: (1, 1),
        },
        asks={
            100.25: (3, 1),
            100.5: (7, 2),
            100.75: (2, 1),
            101.0: (10, 1),
        },
        timestamp_us=_us(datetime(2026, 4, 28, 7, 29, 59, tzinfo=timezone.utc)),
        tick_size=0.25,
    )

    assert features["total_depth10"] == 42
    assert features["near_far_ratio"] == pytest.approx(31 / 11)
    assert features["max_bid_wall10"] == 10
    assert features["max_ask_wall10"] == 10
    summary = mod.summarize_samples([features], "event15", tick_size=0.25)
    assert summary["event15_median_near_far_ratio"] == pytest.approx(31 / 11)
    assert summary["event15_median_max_bid_wall"] == 10
    assert summary["event15_median_max_ask_wall"] == 10


def test_extract_event_features_uses_predecision_windows(tmp_path):
    depth = tmp_path / "NQM26-CME.2026-04-28.depth"
    records = [
        _record("2026-04-28T06:29:00+00:00", 1, 0, 0.0, 0),
        _record("2026-04-28T06:29:00+00:00", 2, 0, 100.0, 20),
        _record("2026-04-28T06:29:00+00:00", 3, mod.END_OF_BATCH, 100.25, 20),
        _record("2026-04-28T07:16:00+00:00", 4, 0, 100.0, 10),
        _record("2026-04-28T07:16:00+00:00", 5, mod.END_OF_BATCH, 100.25, 30),
        _record("2026-04-28T07:29:59+00:00", 4, 0, 100.0, 8),
        _record("2026-04-28T07:29:59+00:00", 5, mod.END_OF_BATCH, 100.25, 32),
        _record("2026-04-28T07:30:00+00:00", 4, 0, 100.0, 99),
        _record("2026-04-28T07:30:00+00:00", 5, mod.END_OF_BATCH, 100.25, 99),
    ]
    _write_depth(depth, records)
    event = {
        "event_id": "NAS100_20260428T0730_candidate_141",
        "symbol": "NAS100",
        "event_class": "candidate",
        "decision": "CANDIDATE",
        "framework": "ob_retest",
        "direction": "LONG",
        "canonical_m15_close_utc": "2026-04-28T07:30:00+00:00",
        "window_start_utc": "2026-04-28T06:30:00+00:00",
        "window_end_utc": "2026-04-28T08:30:00+00:00",
    }

    extracted = mod.extract_event_features(
        depth_path=depth,
        event=event,
        source_symbol="NQM26-CME",
        futures_symbol="NQ.v.0",
        tick_size=0.25,
    )
    row = extracted["feature_row"]

    assert row["data_status"] == "ok"
    assert row["pre60_sample_count"] == 2
    assert row["event15_sample_count"] == 2
    assert row["event15_median_total_depth10"] == 40
    assert row["event15_median_depth10_imbalance"] == pytest.approx(-0.55)
    assert extracted["header"]["records_processed_until_canonical"] == 7
    assert row["event15_median_total_depth10"] != 198


def test_extract_event_features_replays_from_last_clear_before_window(tmp_path):
    depth = tmp_path / "NQM26-CME.2026-04-28.depth"
    records = [
        _record("2026-04-28T00:00:00+00:00", 1, 0, 0.0, 0),
        _record("2026-04-28T00:00:01+00:00", 2, 0, 99.0, 999),
        _record("2026-04-28T00:00:01+00:00", 3, mod.END_OF_BATCH, 101.0, 999),
        _record("2026-04-28T06:29:00+00:00", 1, 0, 0.0, 0),
        _record("2026-04-28T06:29:00+00:00", 2, 0, 100.0, 20),
        _record("2026-04-28T06:29:00+00:00", 3, mod.END_OF_BATCH, 100.25, 20),
        _record("2026-04-28T07:29:59+00:00", 4, 0, 100.0, 8),
        _record("2026-04-28T07:29:59+00:00", 5, mod.END_OF_BATCH, 100.25, 32),
    ]
    _write_depth(depth, records)
    event = {
        "event_id": "NAS100_20260428T0730_candidate_141",
        "symbol": "NAS100",
        "event_class": "candidate",
        "decision": "CANDIDATE",
        "framework": "ob_retest",
        "direction": "LONG",
        "canonical_m15_close_utc": "2026-04-28T07:30:00+00:00",
        "window_start_utc": "2026-04-28T06:30:00+00:00",
        "window_end_utc": "2026-04-28T08:30:00+00:00",
    }

    extracted = mod.extract_event_features(
        depth_path=depth,
        event=event,
        source_symbol="NQM26-CME",
        futures_symbol="NQ.v.0",
        tick_size=0.25,
    )

    assert extracted["header"]["replay_start_record_index"] == 3
    assert extracted["header"]["replay_start_reason"] == "LAST_CLEAR_BOOK_BEFORE_WINDOW"
    assert extracted["feature_row"]["event15_median_total_depth10"] == 40


def test_databento_comparison_matches_event_id(tmp_path):
    db_path = tmp_path / "db.json"
    feature_row = {
        "event_id": "e1",
        "futures_symbol": "YM.v.0",
        "event15_median_total_depth10": 12,
        "event15_sample_count": 2,
    }
    db_path.write_text(
        json.dumps(
            {
                "feature_rows": [
                    {
                        "event_id": "e1",
                        "futures_symbol": "ES.v.0",
                        "event15_median_total_depth10": 999,
                        "event15_sample_count": 2,
                    },
                    {
                        "event_id": "e1",
                        "futures_symbol": "YM.v.0",
                        "event15_median_total_depth10": 10,
                        "event15_sample_count": 2,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    out = mod.compare_databento(feature_row, db_path)

    assert out["status"] == "matched_cached_databento_feature_row"
    assert out["databento_futures_symbol"] == "YM.v.0"
    assert out["field_comparisons"]["event15_median_total_depth10"]["sierra_minus_databento"] == 2
