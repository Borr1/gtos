import csv
import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts.convert_sierra_scid_to_ohlcv import (
    convert_batch,
    floor_time,
    normalize_record,
    parse_mapping,
)
from scripts.inspect_sierra_scid import HEADER_STRUCT, RECORD_STRUCT, SIERRA_EPOCH, ScidRecord


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"sierra_scid_to_ohlcv_{uuid.uuid4().hex}"
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
            _us(datetime(2026, 4, 15, 13, 0, 5, tzinfo=timezone.utc)),
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
            _us(datetime(2026, 4, 15, 13, 14, 59, tzinfo=timezone.utc)),
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
            _us(datetime(2026, 4, 15, 13, 15, 1, tzinfo=timezone.utc)),
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


def test_parse_mapping_defaults_to_proxy_transfer():
    mapping = parse_mapping("NQM26-CME=NAS100")

    assert mapping.source_symbol == "NQM26-CME"
    assert mapping.file_symbol == "NAS100"
    assert mapping.evidence_class == "FUTURES_PROXY_TRANSFER"
    assert mapping.price_transform == "identity"
    assert mapping.source_file_name == "NQM26-CME.scid"


def test_floor_time_uses_utc_buckets():
    value = datetime(2026, 4, 15, 13, 17, 44, 123, tzinfo=timezone.utc)

    assert floor_time(value, "M15").isoformat() == "2026-04-15T13:15:00+00:00"
    assert floor_time(value, "H1").isoformat() == "2026-04-15T13:00:00+00:00"
    assert floor_time(value, "D1").isoformat() == "2026-04-15T00:00:00+00:00"


def test_normalize_record_skips_invalid_close_and_handles_inverse():
    invalid = ScidRecord(
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        open=100.0,
        high=101.0,
        low=99.0,
        close=-1.0,
        num_trades=1,
        total_volume=2,
        bid_volume=1,
        ask_volume=1,
    )
    valid = ScidRecord(
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        open=0.5,
        high=0.25,
        low=1.0,
        close=0.5,
        num_trades=1,
        total_volume=2,
        bid_volume=1,
        ask_volume=1,
    )

    assert normalize_record(invalid, "identity") is None
    transformed = normalize_record(valid, "inverse")
    assert transformed["open"] == 2.0
    assert transformed["high"] == 4.0
    assert transformed["low"] == 1.0
    assert transformed["close"] == 2.0


def test_convert_batch_writes_gtos_csvs_and_manifest(tmp_path):
    data_dir = tmp_path / "sierra"
    output_root = tmp_path / "out"
    data_dir.mkdir()
    _write_scid(data_dir / "NQM26-CME.scid")

    manifest = convert_batch(
        data_dir=data_dir,
        output_root=output_root,
        batch_id="pilot",
        mappings=[parse_mapping("NQM26-CME=NAS100:FUTURES_PROXY_TRANSFER")],
        timeframes=["M15", "H1", "D1"],
        start=datetime(2026, 4, 15, 13, 0, tzinfo=timezone.utc),
        end=datetime(2026, 4, 15, 14, 0, tzinfo=timezone.utc),
        notes="test",
    )

    batch_root = output_root / "pilot"
    m15_path = batch_root / "NAS100_M15.csv"
    h1_path = batch_root / "NAS100_H1.csv"
    d1_path = batch_root / "NAS100_D1.csv"
    assert m15_path.exists()
    assert h1_path.exists()
    assert d1_path.exists()
    with m15_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["time"] for row in rows] == ["2026-04-15 13:00:00", "2026-04-15 13:15:00"]
    assert rows[0]["open"] == "100"
    assert rows[0]["high"] == "102"
    assert rows[0]["low"] == "99"
    assert rows[0]["close"] == "101.5"
    assert rows[0]["volume"] == "17"
    assert rows[0]["source_records"] == "2"
    manifest_on_disk = json.loads((batch_root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest_on_disk["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert manifest_on_disk["files"]["NAS100_M15"]["rows"] == 2
    assert manifest["files"]["NAS100_H1"]["rows"] == 1
