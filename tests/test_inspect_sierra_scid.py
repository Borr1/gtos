from datetime import datetime, timezone
from pathlib import Path
import shutil
import struct
import uuid

import pytest

from scripts.inspect_sierra_scid import (
    HEADER_STRUCT,
    RECORD_STRUCT,
    SIERRA_EPOCH,
    export_slice_to_csv,
    parse_header,
    summarize_file,
)


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"inspect_sierra_scid_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _us(value: datetime) -> int:
    return int((value - SIERRA_EPOCH).total_seconds() * 1_000_000)


def _write_scid(path):
    records = [
        (
            _us(datetime(2026, 4, 15, 13, 0, tzinfo=timezone.utc)),
            100.0,
            101.0,
            99.0,
            100.5,
            2,
            10,
            4,
            6,
        ),
        (
            _us(datetime(2026, 4, 15, 13, 1, tzinfo=timezone.utc)),
            100.5,
            102.0,
            100.25,
            101.5,
            1,
            7,
            0,
            7,
        ),
        (
            _us(datetime(2026, 4, 15, 14, 0, tzinfo=timezone.utc)),
            101.5,
            103.0,
            101.0,
            102.0,
            3,
            11,
            8,
            3,
        ),
    ]
    with path.open("wb") as handle:
        handle.write(HEADER_STRUCT.pack(b"SCID", 56, 40, 1, 0, 0, b"\0" * 36))
        for rec in records:
            handle.write(RECORD_STRUCT.pack(*rec))


def test_parse_header_and_summary(tmp_path):
    path = tmp_path / "TEST.scid"
    _write_scid(path)

    header = parse_header(path)
    summary = summarize_file(path)

    assert header.record_count == 3
    assert header.remainder_bytes == 0
    assert summary["first_timestamp_utc"] == "2026-04-15T13:00:00+00:00"
    assert summary["last_timestamp_utc"] == "2026-04-15T14:00:00+00:00"
    assert summary["last_close"] == 102.0


def test_export_slice_to_csv(tmp_path):
    path = tmp_path / "TEST.scid"
    out = tmp_path / "slice.csv"
    _write_scid(path)

    summary = export_slice_to_csv(
        path,
        datetime(2026, 4, 15, 13, 0, tzinfo=timezone.utc),
        datetime(2026, 4, 15, 13, 30, tzinfo=timezone.utc),
        out,
    )

    assert summary["rows"] == 2
    assert summary["sum_total_volume"] == 17
    assert summary["sum_bid_volume"] == 4
    assert summary["sum_ask_volume"] == 13
    assert out.read_text(encoding="utf-8").splitlines()[0].startswith("timestamp_utc")
