from __future__ import annotations

import importlib.util
import struct
from datetime import datetime, timezone
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
BUILDER_PATH = ROUTE_DIR / "build_fpb_source_expansion_and_sealed_pool_materialization_2026_05_11.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("fpb_source_expansion_builder_test", BUILDER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_infer_timeframe_handles_scid_named_csv() -> None:
    builder = load_builder()
    assert builder.infer_timeframe(Path("EURUSD_SCID_M1.csv")) == "M1"
    assert builder.infer_timeframe(Path("XAUUSD_SCID_M15.csv")) == "M15"
    assert builder.infer_symbol(Path("EURUSD_SCID_M15.csv")) == "EURUSD"
    assert builder.infer_symbol(Path("XAUUSD_SCID_M15.csv")) == "XAUUSD"


def test_embargo_rejects_candidate_starting_inside_selected_window() -> None:
    builder = load_builder()
    selected_end = {"XAUUSD": builder.parse_time("2026-05-01T20:45:00Z")}
    rejected, reason = builder.coverage_overlaps_embargo(
        "XAUUSD",
        "2026-05-11T00:00:00Z",
        "2026-05-11T23:59:59Z",
        selected_end,
    )
    assert rejected is True
    assert "EMBARGO" in reason


def test_native_segment_starts_after_fourteen_day_embargo() -> None:
    builder = load_builder()
    selected_end = {"NAS100_NQ": builder.parse_time("2026-04-17T20:45:00Z")}
    segment_start, status = builder.eligible_segment_for_native(
        "NAS100_NQ",
        "2026-05-11T08:33:39Z",
        selected_end,
    )
    assert status == "HAS_POST_EMBARGO_NATIVE_SEGMENT"
    assert segment_start == "2026-05-01T20:45:01Z"


def test_parse_minimal_scid_header_and_records() -> None:
    builder = load_builder()
    path = ROUTE_DIR / "NQM26-CME.scid"
    header = builder.SCID_HEADER.pack(b"SCID", builder.SCID_HEADER.size, builder.SCID_RECORD.size, 1, 0, 0, b"\x00" * 36)

    def sierra_microseconds(value: datetime) -> int:
        return int((value - builder.SIERRA_EPOCH).total_seconds() * 1_000_000)

    first = builder.SCID_RECORD.pack(
        sierra_microseconds(datetime(2026, 5, 2, 0, 0, tzinfo=timezone.utc)),
        10.0,
        11.0,
        9.0,
        10.5,
        1,
        2,
        3,
        4,
    )
    last = builder.SCID_RECORD.pack(
        sierra_microseconds(datetime(2026, 5, 3, 0, 0, tzinfo=timezone.utc)),
        10.5,
        12.0,
        10.0,
        11.5,
        5,
        6,
        7,
        8,
    )
    try:
        path.write_bytes(header + first + last)
        parsed = builder.parse_scid(path)
        assert parsed["parser_status"] == "SCID_HEADER_AND_RECORD_PARSER_OK"
        assert parsed["symbol"] == "NAS100_NQ"
        assert parsed["coverage_start_utc"] == "2026-05-02T00:00:00Z"
        assert parsed["coverage_end_utc"] == "2026-05-03T00:00:00Z"
        assert parsed["source_sha256"]
    finally:
        path.unlink(missing_ok=True)
