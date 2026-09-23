import csv
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.build_external_feed_snapshots_historical import prepare_snapshot_index
from scripts.build_historical_opportunity_dataset import (
    build_external_snapshot_projection,
    iter_historical_opportunities,
)
from src.components.external_feeds import ExternalFeedStore


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"historical_opportunities_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_snapshot_projection_uses_as_of_not_observation_date():
    snapshot_index = prepare_snapshot_index(
        {
            "flashalpha_gex": [
                {
                    "source": "flashalpha_gex",
                    "gtos_symbol": "NAS100",
                    "proxy_symbol": "QQQ",
                    "observation_date": "2026-05-02",
                    "as_of_utc": "2026-05-01T11:30:00Z",
                    "net_gex": 1.0,
                },
                {
                    "source": "flashalpha_gex",
                    "gtos_symbol": "NAS100",
                    "proxy_symbol": "QQQ",
                    "observation_date": "2026-04-01",
                    "as_of_utc": "2026-05-01T12:30:00Z",
                    "net_gex": 99.0,
                },
            ]
        }
    )

    projection = build_external_snapshot_projection(
        symbol="NAS100",
        candle_close_utc="2026-05-01T12:00:00Z",
        snapshot_index=snapshot_index,
        sources=["flashalpha_gex"],
    )

    assert projection["external_snapshot_match_status"] == "MATCHED_ALL_SOURCES"
    assert projection["feature_available__flashalpha_gex"] is True
    assert projection["flashalpha_gex__as_of_utc"] == "2026-05-01T11:30:00Z"
    assert projection["flashalpha_gex__net_gex"] == 1.0
    assert projection["external_snapshot_as_of_utc"] == "2026-05-01T11:30:00+00:00"


def test_missing_external_snapshot_sets_explicit_flags():
    projection = build_external_snapshot_projection(
        symbol="XAUUSD",
        candle_close_utc="2026-05-01T12:00:00Z",
        snapshot_index=prepare_snapshot_index({"fred": []}),
        sources=["fred"],
    )

    assert projection["external_snapshot_match_status"] == "MISSING_ALL_SOURCES"
    assert projection["external_snapshot_as_of_utc"] is None
    assert projection["external_snapshot_missing_sources"] == ["fred"]
    assert projection["feature_availability_flags"] == {"fred": False}
    assert projection["feature_available__fred"] is False


def test_far_future_lbma_schedule_is_missing_not_matched():
    snapshot_index = prepare_snapshot_index(
        {
            "lbma_calendar": [
                {
                    "source": "lbma_calendar",
                    "metal": "gold",
                    "fix_name": "AM",
                    "fix_time_utc": "2025-10-01T09:30:00Z",
                    "gtos_symbol": "XAUUSD",
                }
            ]
        }
    )

    projection = build_external_snapshot_projection(
        symbol="XAUUSD",
        candle_close_utc="2022-02-02T08:00:00Z",
        snapshot_index=snapshot_index,
        sources=["lbma_calendar"],
    )

    assert projection["external_snapshot_match_status"] == "MISSING_ALL_SOURCES"
    assert projection["feature_available__lbma_calendar"] is False
    assert projection["lbma_calendar__available"] is False
    assert "lbma_calendar__next_fix_time_utc" not in projection


def test_builder_import_does_not_load_paid_ai_clients():
    code = (
        "import sys\n"
        "import scripts.build_historical_opportunity_dataset\n"
        "print('anthropic' in sys.modules)\n"
        "print('openai' in sys.modules)\n"
    )

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=True,
    )

    assert result.stdout.strip().splitlines() == ["False", "False"]


def test_opportunity_rows_are_stable_and_keyed_by_symbol_candle(tmp_path):
    data_dir = tmp_path / "ohlcv"
    _write_ohlcv(
        data_dir / "XAUUSD_M15.csv",
        start=datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc),
        delta=timedelta(minutes=15),
        count=80,
        base=2300.0,
        step=0.08,
    )
    _write_ohlcv(
        data_dir / "XAUUSD_H1.csv",
        start=datetime(2026, 4, 20, 0, 0, tzinfo=timezone.utc),
        delta=timedelta(hours=1),
        count=300,
        base=2250.0,
        step=0.12,
    )
    _write_ohlcv(
        data_dir / "XAUUSD_D1.csv",
        start=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        delta=timedelta(days=1),
        count=130,
        base=2100.0,
        step=0.9,
    )
    config = {
        "market": {
            "symbol": "XAUUSD",
            "kill_zones": {"london": {"start_utc": "07:00", "end_utc": "08:00"}},
        },
        "model_a": {"enabled_frameworks": ["ob_retest"]},
        "pre_ai_gates": {"h1_poi_availability_enabled": False},
        "risk": {"sl_buffer_atr_multiplier": 0.25, "sl_buffer_min_ticks": 5},
    }
    store = ExternalFeedStore(tmp_path / "external")

    def build_rows():
        return list(
            iter_historical_opportunities(
                store=store,
                data_dirs=[data_dir],
                symbols=["XAUUSD"],
                base_config=config,
                sources=["fred"],
                include_mechanical=False,
                limit_per_symbol=3,
            )
        )

    rows1 = build_rows()
    rows2 = build_rows()
    keys1 = [row["opportunity_key"] for row in rows1]
    keys2 = [row["opportunity_key"] for row in rows2]

    assert len(rows1) == 3
    assert keys1 == keys2
    assert keys1 == sorted(keys1)
    assert len(keys1) == len(set(keys1))
    assert keys1[0] == "XAUUSD|2026-05-01T07:15:00+00:00"
    assert all(row["symbol"] == "XAUUSD" for row in rows1)
    assert all(row["timeframe"] == "M15" for row in rows1)
    assert all(row["ai_call_attempted"] is False for row in rows1)
    assert all(row["ai_call_count"] == 0 for row in rows1)
    assert all(row["paid_ai_replay"] is False for row in rows1)
    assert all(row["external_snapshot_match_status"] == "MISSING_ALL_SOURCES" for row in rows1)


def _write_ohlcv(
    path: Path,
    *,
    start: datetime,
    delta: timedelta,
    count: int,
    base: float,
    step: float,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["time", "open", "high", "low", "close", "volume"],
        )
        writer.writeheader()
        for idx in range(count):
            opened_at = start + delta * idx
            open_price = base + step * idx
            close_price = open_price + step * 0.5
            writer.writerow(
                {
                    "time": opened_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "open": f"{open_price:.5f}",
                    "high": f"{max(open_price, close_price) + 0.25:.5f}",
                    "low": f"{min(open_price, close_price) - 0.25:.5f}",
                    "close": f"{close_price:.5f}",
                    "volume": 1000 + idx,
                }
            )
