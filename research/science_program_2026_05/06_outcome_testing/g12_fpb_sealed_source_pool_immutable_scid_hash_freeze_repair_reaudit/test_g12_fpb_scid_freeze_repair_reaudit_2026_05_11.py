from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
BUILDER_PATH = ROUTE_DIR / "build_g12_fpb_scid_freeze_repair_reaudit_2026_05_11.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("g12_fpb_scid_freeze_reaudit_builder", BUILDER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["g12_fpb_scid_freeze_reaudit_builder"] = module
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
                int((ts - builder.SIERRA_EPOCH).total_seconds() * 1_000_000),
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


def test_raw_byte_rehash_uses_manifest_byte_range_and_survives_append(tmp_path: Path) -> None:
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
    header = builder.parse_scid_header(path)
    start = header["header_size"] + header["record_size"]
    end = header["header_size"] + 3 * header["record_size"]
    expected_hash = builder.hash_range(path, start, end)
    manifest = {
        "segments": [
            {
                "source": "NQM26-CME.scid",
                "symbol": "NAS100_NQ",
                "source_path": str(path),
                "eligible_segment_start_utc_hard_floor": "2026-05-02T00:00:00Z",
                "segment_record_start_index": 1,
                "segment_record_end_index_inclusive": 2,
                "segment_record_count": 2,
                "segment_byte_start": start,
                "segment_byte_end_exclusive": end,
                "segment_first_record_utc": "2026-05-02T00:00:00Z",
                "segment_last_record_utc": "2026-05-03T00:00:00Z",
                "segment_records_sha256": expected_hash,
            }
        ]
    }
    source_freeze = {
        "freeze_rows": [
            {
                "source": "NQM26-CME.scid",
                "repair_partition_assignment": "SEALED_HISTORICAL_SOURCE_POOL_CANDIDATE_G12_REAUDIT_REQUIRED",
                "duplicate_source_decision_repaired": "UNIQUE_SEGMENT_HASH_NOT_DISCOVERY_SELECTED_AND_G12_REAUDIT_REQUIRED",
                "parser_asof_status": "SOURCE_LOCAL_FILE_ONLY_REQUIRES_SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_BEFORE_REPLAY",
                "no_leak_status": "SOURCE_TIME_ORDERED_NATIVE_RECORDS_NO_BROKER_ACCOUNT_ORDER_OR_RESULT_FIELDS_READ",
            }
        ]
    }
    with path.open("ab") as handle:
        handle.write(
            builder.SCID_RECORD.pack(
                int((datetime(2026, 5, 4, 0, 0, tzinfo=timezone.utc) - builder.SIERRA_EPOCH).total_seconds() * 1_000_000),
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

    audit_rows, blockers = builder.audit_segments(manifest, source_freeze, set(), require_all_expected=False)
    assert blockers == []
    assert audit_rows[0]["raw_byte_rehash_sha256_first_pass"] == expected_hash
    assert audit_rows[0]["raw_byte_rehash_sha256_second_pass"] == expected_hash
    assert audit_rows[0]["current_file_bytes_after_segment"] == builder.SCID_RECORD.size
    assert audit_rows[0]["append_observed_after_manifest_segment"] is True


def test_hard_floor_requires_previous_record_before_floor(tmp_path: Path) -> None:
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
    header = builder.parse_scid_header(path)
    start = header["header_size"] + header["record_size"]
    end = header["header_size"] + 3 * header["record_size"]
    manifest = {
        "segments": [
            {
                "source": "6BM26-CME.scid",
                "symbol": "GBPUSD_6B",
                "source_path": str(path),
                "eligible_segment_start_utc_hard_floor": "2026-05-01T20:59:01Z",
                "segment_record_start_index": 1,
                "segment_record_end_index_inclusive": 2,
                "segment_record_count": 2,
                "segment_byte_start": start,
                "segment_byte_end_exclusive": end,
                "segment_first_record_utc": "2026-05-01T20:59:01Z",
                "segment_last_record_utc": "2026-05-01T21:00:00Z",
                "segment_records_sha256": builder.hash_range(path, start, end),
            }
        ]
    }
    source_freeze = {"freeze_rows": [{"source": "6BM26-CME.scid"}]}
    audit_rows, blockers = builder.audit_segments(manifest, source_freeze, set(), require_all_expected=False)
    assert blockers == []
    checks = audit_rows[0]["checks"]
    assert checks["first_record_at_or_after_hard_floor"]
    assert checks["previous_record_before_floor_or_no_previous"]
    assert checks["timestamp_scan_has_no_pre_floor_records"]


def test_selected_hash_overlap_blocks_acceptance(tmp_path: Path) -> None:
    builder = load_builder()
    path = tmp_path / "YMM26-CBOT.scid"
    write_scid(builder, path, [datetime(2026, 5, 2, 0, 0, tzinfo=timezone.utc)])
    header = builder.parse_scid_header(path)
    start = header["header_size"]
    end = header["header_size"] + header["record_size"]
    segment_hash = builder.hash_range(path, start, end)
    manifest = {
        "segments": [
            {
                "source": "YMM26-CBOT.scid",
                "symbol": "US30_YM",
                "source_path": str(path),
                "eligible_segment_start_utc_hard_floor": "2026-05-01T20:59:01Z",
                "segment_record_start_index": 0,
                "segment_record_end_index_inclusive": 0,
                "segment_record_count": 1,
                "segment_byte_start": start,
                "segment_byte_end_exclusive": end,
                "segment_first_record_utc": "2026-05-02T00:00:00Z",
                "segment_last_record_utc": "2026-05-02T00:00:00Z",
                "segment_records_sha256": segment_hash,
            }
        ]
    }
    source_freeze = {"freeze_rows": [{"source": "YMM26-CBOT.scid"}]}
    audit_rows, blockers = builder.audit_segments(manifest, source_freeze, {segment_hash}, require_all_expected=False)
    assert blockers
    assert "segment_hash_disjoint_from_selected_discovery_hashes" in audit_rows[0]["failed_checks"]


def test_safe_flags_require_no_validation_or_live_surface() -> None:
    builder = load_builder()
    flags = builder.safe_flags()
    ok, failures = builder.safe_flags_ok(flags)
    assert ok
    assert failures == []
    flags["opens_result_scoring"] = True
    ok, failures = builder.safe_flags_ok(flags)
    assert not ok
    assert failures == ["opens_result_scoring"]
