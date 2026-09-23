from datetime import datetime, timezone
from pathlib import Path
import shutil
import uuid

import pytest

from scripts.export_mt5_research_ohlcv import SymbolSpec
from scripts.inspect_mt5_tick_availability import (
    ProbeWindow,
    inspect_tick_availability,
    parse_windows,
)


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"mt5_tick_availability_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_parse_windows_accepts_colon_separated_iso_z_values():
    windows = parse_windows(
        ["recent:2026-04-30T13:00:00Z:2026-04-30T14:00:00Z"]
    )

    assert windows == [
        ProbeWindow(
            label="recent",
            start=datetime(2026, 4, 30, 13, 0, tzinfo=timezone.utc),
            end=datetime(2026, 4, 30, 14, 0, tzinfo=timezone.utc),
        )
    ]


def test_parse_windows_rejects_reversed_time_range():
    with pytest.raises(Exception):
        parse_windows(["bad:2026-04-30T14:00:00Z:2026-04-30T13:00:00Z"])


def test_inspect_tick_availability_counts_rows_and_timestamps():
    mt5 = FakeMT5()
    windows = parse_windows(["recent:2026-04-30T13:00:00Z:2026-04-30T14:00:00Z"])

    result = inspect_tick_availability(
        mt5_module=mt5,
        specs=[SymbolSpec(file_symbol="XAUUSD", mt5_symbol="XAUUSD")],
        windows=windows,
        copy_ticks_flag=mt5.COPY_TICKS_ALL,
    )

    row = result["files"]["XAUUSD_recent"]
    assert result["errors"] == []
    assert row["rows"] == 2
    assert row["has_ticks"] is True
    assert row["first_tick_utc"] == "2026-04-30T13:00:00.123000+00:00"
    assert row["last_tick_utc"] == "2026-04-30T13:00:01.456000+00:00"


def test_inspect_tick_availability_records_empty_window():
    mt5 = FakeMT5(empty=True)
    windows = parse_windows(["old:2025-12-01T13:00:00Z:2025-12-01T14:00:00Z"])

    result = inspect_tick_availability(
        mt5_module=mt5,
        specs=[SymbolSpec(file_symbol="XAUUSD", mt5_symbol="XAUUSD")],
        windows=windows,
        copy_ticks_flag=mt5.COPY_TICKS_ALL,
    )

    row = result["files"]["XAUUSD_old"]
    assert result["errors"] == []
    assert row["rows"] == 0
    assert row["has_ticks"] is False
    assert row["first_tick_utc"] is None
    assert row["last_tick_utc"] is None


class FakeMT5:
    COPY_TICKS_ALL = 1

    def __init__(self, empty=False):
        self.empty = empty

    def symbol_select(self, _symbol, _enabled):
        return True

    def copy_ticks_range(self, _symbol, _start, _end, _flag):
        if self.empty:
            return []
        return [
            {"time_msc": 1777554000123, "bid": 2300.1, "ask": 2300.2},
            {"time_msc": 1777554001456, "bid": 2300.2, "ask": 2300.3},
        ]

    def last_error(self):
        return (1, "Success")
