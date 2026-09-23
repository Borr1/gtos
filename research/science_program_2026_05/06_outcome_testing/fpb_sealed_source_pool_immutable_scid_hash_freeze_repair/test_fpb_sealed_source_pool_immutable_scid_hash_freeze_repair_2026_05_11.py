from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
BUILDER_PATH = ROUTE_DIR / "build_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_2026_05_11.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("fpb_scid_freeze_builder_test", BUILDER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_scid(builder, path: Path, timestamps: list[datetime]) -> None:
    header = builder.SCID_HEADER.pack(
        b"SCID",
        builder.SCID_HEADER.size,
        builder.SCID_RECORD.size,
        1,
        0,
        0,
        b"\x00" * 36,
    )
    records = []
    for idx, ts in enumerate(timestamps):
        records.append(
            builder.SCID_RECORD.pack(
                builder.sierra_microseconds(ts),
                10.0 + idx,
                11.0 + idx,
                9.0 + idx,
                10.5 + idx,
                100 + idx,
                2 + idx,
                50 + idx,
                50 + idx,
            )
        )
    path.write_bytes(header + b"".join(records))


def test_bounded_segment_hash_ignores_later_append(tmp_path: Path) -> None:
    builder = load_builder()
    path = tmp_path / "NQM26-CME.scid"
    write_scid(
        builder,
        path,
        [
            datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc),
            datetime(2026, 5, 2, 0, 0, tzinfo=timezone.utc),
            datetime(2026, 5, 3, 0, 0, tzinfo=timezone.utc),
        ],
    )
    metadata = builder.parse_scid_metadata(path)
    segment = builder.derive_segment(path, "2026-05-02T00:00:00Z", metadata)
    assert segment["segment_record_start_index"] == 1
    assert segment["segment_record_end_index_inclusive"] == 2
    original_hash = segment["segment_records_sha256"]
    original_end = segment["segment_byte_end_exclusive"]

    with path.open("ab") as handle:
        handle.write(
            builder.SCID_RECORD.pack(
                builder.sierra_microseconds(datetime(2026, 5, 4, 0, 0, tzinfo=timezone.utc)),
                20.0,
                21.0,
                19.0,
                20.5,
                1,
                1,
                1,
                1,
            )
        )

    assert builder.hash_range(path, segment["segment_byte_start"], original_end) == original_hash


def test_hard_floor_excludes_pre_eligible_records(tmp_path: Path) -> None:
    builder = load_builder()
    path = tmp_path / "6BM26-CME.scid"
    write_scid(
        builder,
        path,
        [
            datetime(2026, 5, 1, 20, 59, 0, tzinfo=timezone.utc),
            datetime(2026, 5, 1, 20, 59, 1, tzinfo=timezone.utc),
            datetime(2026, 5, 1, 21, 0, 0, tzinfo=timezone.utc),
        ],
    )
    metadata = builder.parse_scid_metadata(path)
    segment = builder.derive_segment(path, "2026-05-01T20:59:01Z", metadata)
    assert segment["segment_record_start_index"] == 1
    assert segment["pre_eligible_records_excluded"] == 1
    assert segment["segment_first_record_utc"] == "2026-05-01T20:59:01Z"


def test_descriptor_hash_is_stable_for_same_payload() -> None:
    builder = load_builder()
    payload = {"b": 2, "a": 1}
    assert builder.sha256_json(payload) == builder.sha256_json({"a": 1, "b": 2})


def test_safe_flags_keep_repair_out_of_validation() -> None:
    builder = load_builder()
    flags = builder.safe_flags()
    assert flags["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert flags["validation_safe"] is False
    assert flags["outcome_review_opened"] is False
    assert flags["live_effect"] is False
    assert flags["opens_result_scoring"] is False
