from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
BUILDER_PATH = ROUTE_DIR / "build_g12_fpb_sealed_source_pool_materialization_audit_2026_05_11.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("g12_fpb_sealed_source_pool_audit_builder", BUILDER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["g12_fpb_sealed_source_pool_audit_builder"] = module
    spec.loader.exec_module(module)
    return module


def test_scid_named_csv_inference_does_not_create_symbol_suffix_5() -> None:
    builder = load_builder()
    assert builder.infer_symbol_from_scid_named_csv(Path("EURUSD_SCID_M15.csv")) == "EURUSD"
    assert builder.infer_timeframe_from_scid_named_csv(Path("EURUSD_SCID_M15.csv")) == "M15"
    assert builder.infer_symbol_from_scid_named_csv(Path("XAUUSD_SCID_M15.csv")) == "XAUUSD"
    assert builder.infer_timeframe_from_scid_named_csv(Path("XAUUSD_SCID_M15.csv")) == "M15"


def test_parse_scid_independent_reads_minimal_header_and_records(tmp_path: Path) -> None:
    builder = load_builder()
    path = tmp_path / "TEST.scid"
    header = builder.SCID_HEADER.pack(b"SCID", builder.SCID_HEADER.size, builder.SCID_RECORD.size, 1, 0, 0, b"\x00" * 36)

    def micros(value: datetime) -> int:
        return int((value - builder.SIERRA_EPOCH).total_seconds() * 1_000_000)

    first = builder.SCID_RECORD.pack(
        micros(datetime(2026, 5, 2, 0, 0, tzinfo=timezone.utc)),
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
        micros(datetime(2026, 5, 3, 0, 0, tzinfo=timezone.utc)),
        10.5,
        12.0,
        10.0,
        11.5,
        5,
        6,
        7,
        8,
    )
    path.write_bytes(header + first + last)
    parsed = builder.parse_scid_independent(path)
    assert parsed["parser_status"] == "SCID_HEADER_AND_RECORD_PARSER_OK"
    assert parsed["coverage_start_utc"] == "2026-05-02T00:00:00Z"
    assert parsed["coverage_end_utc"] == "2026-05-03T00:00:00Z"
    assert parsed["record_count"] == 2
    assert parsed["source_sha256"]


def test_safe_flags_require_no_validation_or_live_surface() -> None:
    builder = load_builder()
    payload = {"promotion_verdict": "NO_PROMOTION_VERDICT"}
    for flag in builder.SAFE_FALSE_FLAGS:
        payload[flag] = False
    ok, failures = builder.safe_flags_ok(payload)
    assert ok
    assert failures == []
    payload["opens_validation"] = True
    ok, failures = builder.safe_flags_ok(payload)
    assert not ok
    assert failures == ["opens_validation"]


def test_selected_hash_overlap_blocks_discovery_exclusion() -> None:
    builder = load_builder()
    source_selection = {
        "selected_source_count": 1,
        "selected_sources": [{"source_sha256": "abc"}],
    }
    payloads = {
        "native_scid": {"accepted_native_scid_candidates": [{"source_sha256": "abc"}]},
        "selected_source": {"selected_source_coverage_rows": []},
    }
    selected = builder.selected_hash_set(source_selection)
    assert selected == {"abc"}
    candidate_hashes = {row["source_sha256"] for row in payloads["native_scid"]["accepted_native_scid_candidates"]}
    assert not selected.isdisjoint(candidate_hashes)
