from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from scripts import enrich_sierra_live_candidate_depth_features as mod
from scripts import extract_sierra_depth_features as depth_mod


def _us(value: datetime) -> int:
    return depth_mod.sierra_us(value)


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


def _write_depth(path: Path) -> None:
    records = [
        _record("2026-05-04T15:29:00+00:00", 1, 0, 0.0, 0),
        _record("2026-05-04T15:29:00+00:00", 2, 0, 100.0, 20),
        _record("2026-05-04T15:29:00+00:00", 3, depth_mod.END_OF_BATCH, 100.25, 20),
        _record("2026-05-04T16:16:00+00:00", 4, 0, 100.0, 10),
        _record("2026-05-04T16:16:00+00:00", 5, depth_mod.END_OF_BATCH, 100.25, 30),
        _record("2026-05-04T16:29:59+00:00", 4, 0, 100.0, 8),
        _record("2026-05-04T16:29:59+00:00", 5, depth_mod.END_OF_BATCH, 100.25, 32),
        _record("2026-05-04T16:30:00+00:00", 4, 0, 100.0, 99),
        _record("2026-05-04T16:30:00+00:00", 5, depth_mod.END_OF_BATCH, 100.25, 99),
    ]
    with path.open("wb") as handle:
        handle.write(depth_mod.HEADER_STRUCT.pack(depth_mod.MAGIC, 64, depth_mod.RECORD_STRUCT.size, 1))
        handle.write(b"\0" * 48)
        for record in records:
            handle.write(depth_mod.RECORD_STRUCT.pack(*record))


def test_enriches_candidate_depth_out_of_band():
    root = Path(".test_tmp") / f"sierra_live_enrich_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    try:
        depth = root / "NQM26-CME.2026-05-04.depth"
        _write_depth(depth)
        source = root / "candidates.jsonl"
        output = root / "sierra_depth_feature_snapshots.jsonl"
        candidate = {
            "schema_version": "strategy_follow_candidate_v1",
            "candidate_id": "NAS100_2026-05-04T16:30:00+00:00",
            "symbol": "NAS100",
            "broker_symbol": "NDX100",
            "decision_time_utc": "2026-05-04T16:30:00+00:00",
            "side": "LONG",
            "framework": "ob_retest",
            "analysis_decision": "CANDIDATE",
            "created_at_utc": "2026-05-04T16:30:26+00:00",
            "external_confluence": {
                "sierra": {
                    "status": "LOCAL_DEPTH_FILE_PRESENT_FEATURE_EXTRACTION_DEFERRED",
                    "depth_path": str(depth),
                    "source_symbol": "NQM26-CME",
                    "futures_symbol": "NQ.v.0",
                    "source_status": "LOCAL_SIERRA_DEPTH_CAPTURED",
                    "parity_status": "DATABENTO_MBP10_PARITY_EXACT_ON_REGISTERED_NQ_PILOT",
                    "interpretation_status": "USABLE_AS_REGISTERED_NQ_DEPTH_CONTEXT",
                }
            },
        }
        source.write_text(json.dumps(candidate) + "\n", encoding="utf-8")

        checkpoint = root / "checkpoint.json"
        result = mod.run(source=source, output=output, max_hours=10_000, checkpoint=checkpoint)

        assert result["rows_written"] == 1
        row = json.loads(output.read_text(encoding="utf-8").splitlines()[0])
        assert row["schema_version"] == "sierra_depth_feature_snapshot_v1"
        assert row["feature_status"] == "FEATURES_EXTRACTED"
        assert row["features_present"] is True
        assert row["features"]["event15_median_total_depth10"] == 40
        assert row["paid_fetch_attempted"] is False
        assert row["paid_data_calls"] == 0
        assert row["no_leak_status"] == "PASS_PRE_DECISION_WINDOWS_ONLY"

        saved_checkpoint = json.loads(checkpoint.read_text(encoding="utf-8"))
        assert saved_checkpoint["depth_feature_version"] == mod.DEPTH_FEATURE_VERSION
        assert saved_checkpoint["candidates"][candidate["candidate_id"]]["last_feature_status"] == "FEATURES_EXTRACTED"

        second = mod.run(source=source, output=output, max_hours=10_000, checkpoint=checkpoint)
        assert second["rows_written"] == 0
        assert second["skipped"] == {"already_extracted": 1}
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_blocked_source_still_preserves_depth_features_with_boundary():
    root = Path(".test_tmp") / f"sierra_live_enrich_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    try:
        depth = root / "SIM26-COMEX.2026-05-04.depth"
        _write_depth(depth)
        candidate = {
            "candidate_id": "XAGUSD_2026-05-04T16:30:00+00:00",
            "symbol": "XAGUSD",
            "broker_symbol": "XAGUSD",
            "decision_time_utc": "2026-05-04T16:30:00+00:00",
            "side": "SHORT",
            "framework": "ob_retest",
            "analysis_decision": "CANDIDATE",
            "external_confluence": {
                "sierra": {
                    "status": "LOCAL_DEPTH_FILE_PRESENT_FEATURE_EXTRACTION_DEFERRED",
                    "depth_path": str(depth),
                    "source_symbol": "SIM26-COMEX",
                    "futures_symbol": "SI.v.0",
                    "source_status": "LOCAL_SIERRA_DEPTH_CAPTURED",
                    "parity_status": "SOURCE_DEPTH_DEFINITION_BLOCKED_SI",
                    "interpretation_status": "BLOCKED_DO_NOT_TREAT_AS_DATABENTO_EQUIVALENT",
                }
            },
        }

        row = mod.build_feature_row(candidate)

        assert row["feature_status"] == "FEATURES_EXTRACTED"
        assert row["features_present"] is True
        assert row["usable_as_databento_equivalent"] is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_pending_status_only_writes_coverage_without_scanning_depth():
    root = Path(".test_tmp") / f"sierra_live_enrich_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    try:
        source = root / "candidates.jsonl"
        output = root / "sierra_depth_feature_snapshots.jsonl"
        candidate = {
            "candidate_id": "NAS100_2026-05-04T17:00:00+00:00",
            "symbol": "NAS100",
            "broker_symbol": "NDX100",
            "decision_time_utc": "2026-05-04T17:00:00+00:00",
            "side": "LONG",
            "framework": "ob_retest",
            "created_at_utc": "2026-05-04T17:00:26+00:00",
            "external_confluence": {
                "sierra": {
                    "status": "LOCAL_DEPTH_FILE_PRESENT_FEATURE_EXTRACTION_DEFERRED",
                    "depth_path": str(root / "missing_large.depth"),
                    "source_symbol": "NQM26-CME",
                    "futures_symbol": "NQ.v.0",
                }
            },
        }
        source.write_text(json.dumps(candidate) + "\n", encoding="utf-8")

        result = mod.run(
            source=source,
            output=output,
            max_hours=10_000,
            pending_status_only=True,
            checkpoint=root / "checkpoint.json",
        )

        assert result["rows_written"] == 1
        row = json.loads(output.read_text(encoding="utf-8").splitlines()[0])
        assert row["feature_status"] == "FEATURE_EXTRACTION_PENDING_HEAVY_DEPTH_SCAN"
        assert row["features_present"] is False
        assert row["source_status"] == "LOCAL_SIERRA_DEPTH_CAPTURED"
        assert row["parity_status"] == "DATABENTO_MBP10_PARITY_EXACT_ON_REGISTERED_NQ_PILOT"

        second = mod.run(
            source=source,
            output=output,
            max_hours=10_000,
            pending_status_only=True,
            checkpoint=root / "checkpoint.json",
        )
        assert second["rows_written"] == 0
        assert second["skipped"] == {"duplicate_file_state": 1}
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_no_registered_proxy_without_depth_path_gets_source_blocked_status():
    candidate = {
        "candidate_id": "GBPJPY_2026-05-04T02:30:00+00:00",
        "symbol": "GBPJPY",
        "broker_symbol": "GBPJPY",
        "decision_time_utc": "2026-05-04T02:30:00+00:00",
        "external_confluence": {
            "sierra": {
                "status": "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL",
                "source_status": "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL",
                "parity_status": "SOURCE_BLOCKED",
                "interpretation_status": "BLOCKED_NO_PROXY",
            }
        },
    }

    row = mod.build_feature_row(candidate)

    assert row["feature_status"] == "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL"
    assert row["depth_path"] is None
    assert row["sierra_futures_symbol"] is None
    assert row["usable_as_databento_equivalent"] is False


def test_repair_existing_feature_row_fills_source_boundary_without_reextracting():
    candidate = {
        "candidate_id": "XAGUSD_2026-05-04T17:00:00+00:00",
        "symbol": "XAGUSD",
        "external_confluence": {"sierra": {"source_symbol": "SIM26-COMEX"}},
    }
    existing = {
        "schema_version": "sierra_depth_feature_snapshot_v1",
        "row_key": "old",
        "candidate_id": candidate["candidate_id"],
        "created_at_utc": "2026-05-04T17:00:01+00:00",
        "feature_status": "FEATURES_EXTRACTED",
        "features_present": True,
        "features": {"event15_sample_count": 10},
        "source_status": None,
        "parity_status": None,
        "interpretation_status": None,
    }

    repaired = mod.repair_existing_feature_row(candidate, existing)

    assert repaired is not None
    assert repaired["features"] == existing["features"]
    assert repaired["source_status"] == "LOCAL_SIERRA_DEPTH_CAPTURED"
    assert repaired["parity_status"] == "SOURCE_DEPTH_DEFINITION_BLOCKED_SI"
    assert repaired["proxy_class"] == "SOURCE_DEFINITION_BLOCKED"
    assert repaired["allowed_use"] == "source_status_only_until_si_depth_definition_is_registered"
    assert repaired["usable_as_databento_equivalent"] is False


def test_file_size_guard_defers_large_depth_without_scanning():
    root = Path(".test_tmp") / f"sierra_live_enrich_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    try:
        depth = root / "NQM26-CME.2026-05-04.depth"
        _write_depth(depth)
        candidate = {
            "candidate_id": "NAS100_2026-05-04T16:30:00+00:00",
            "symbol": "NAS100",
            "broker_symbol": "NDX100",
            "decision_time_utc": "2026-05-04T16:30:00+00:00",
            "external_confluence": {
                "sierra": {
                    "status": "LOCAL_DEPTH_FILE_PRESENT_FEATURE_EXTRACTION_DEFERRED",
                    "depth_path": str(depth),
                    "source_symbol": "NQM26-CME",
                    "futures_symbol": "NQ.v.0",
                }
            },
        }

        row = mod.build_feature_row(candidate, max_file_size_mb=0.0001)

        assert row["feature_status"] == "FEATURE_EXTRACTION_DEFERRED_FILE_SIZE_GUARD"
        assert row["features_present"] is False
        assert row["depth_feature_version"] == mod.DEPTH_FEATURE_VERSION
        assert row["file_size_guard"]["status"] == "DEFERRED_REQUIRES_EXPLICIT_HIGHER_CAP"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_run_applies_per_symbol_throttle():
    root = Path(".test_tmp") / f"sierra_live_enrich_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    try:
        depth = root / "NQM26-CME.2026-05-04.depth"
        _write_depth(depth)
        source = root / "candidates.jsonl"
        output = root / "sierra_depth_feature_snapshots.jsonl"
        rows = []
        for minute in ("16:30", "16:15"):
            rows.append(
                {
                    "candidate_id": f"NAS100_2026-05-04T{minute}:00+00:00",
                    "symbol": "NAS100",
                    "broker_symbol": "NDX100",
                    "decision_time_utc": f"2026-05-04T{minute}:00+00:00",
                    "created_at_utc": f"2026-05-04T{minute}:26+00:00",
                    "external_confluence": {
                        "sierra": {
                            "status": "LOCAL_DEPTH_FILE_PRESENT_FEATURE_EXTRACTION_DEFERRED",
                            "depth_path": str(depth),
                            "source_symbol": "NQM26-CME",
                            "futures_symbol": "NQ.v.0",
                        }
                    },
                }
            )
        source.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

        result = mod.run(
            source=source,
            output=output,
            max_hours=10_000,
            max_per_symbol=1,
            checkpoint=root / "checkpoint.json",
        )

        assert result["rows_written"] == 1
        assert result["rows_written_by_symbol"] == {"NAS100": 1}
        assert result["skipped"] == {"per_symbol_throttle": 1}
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_run_applies_symbol_filter():
    root = Path(".test_tmp") / f"sierra_live_enrich_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    try:
        depth = root / "NQM26-CME.2026-05-04.depth"
        _write_depth(depth)
        source = root / "candidates.jsonl"
        output = root / "features.jsonl"
        checkpoint = root / "checkpoint.json"
        rows = [
            {
                "schema_version": "strategy_follow_candidate_v1",
                "candidate_id": "NAS100_2026-05-04T16:30:00+00:00",
                "symbol": "NAS100",
                "broker_symbol": "NDX100",
                "decision_time_utc": "2026-05-04T16:30:00+00:00",
                "side": "LONG",
                "framework": "ob_retest",
                "created_at_utc": "2026-05-04T16:30:26+00:00",
                "external_confluence": {
                    "sierra": {
                        "status": "LOCAL_DEPTH_FILE_MISSING",
                        "depth_path": str(depth),
                        "source_symbol": "NQM26-CME",
                        "futures_symbol": "NQ.v.0",
                    }
                },
            },
            {
                "schema_version": "strategy_follow_candidate_v1",
                "candidate_id": "GBPJPY_2026-05-04T02:30:00+00:00",
                "symbol": "GBPJPY",
                "broker_symbol": "GBPJPY",
                "decision_time_utc": "2026-05-04T02:30:00+00:00",
                "side": "LONG",
                "framework": "ob_retest",
                "created_at_utc": "2026-05-04T02:30:26+00:00",
                "external_confluence": {
                    "sierra": {
                        "status": "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL",
                        "source_status": "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL",
                        "parity_status": "SOURCE_BLOCKED",
                        "interpretation_status": "BLOCKED_NO_PROXY",
                    }
                },
            },
        ]
        source.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

        result = mod.run(
            source=source,
            output=output,
            max_hours=10_000,
            checkpoint=checkpoint,
            symbols={"GBPJPY"},
        )

        assert result["rows_written"] == 1
        assert result["symbols"] == ["GBPJPY"]
        assert result["skipped"]["symbol_filter"] == 1
        row = json.loads(output.read_text(encoding="utf-8").strip())
        assert row["symbol"] == "GBPJPY"
        assert row["feature_status"] == "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_run_applies_candidate_id_filter_for_targeted_repair():
    root = Path(".test_tmp") / f"sierra_live_enrich_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    try:
        depth = root / "NQM26-CME.2026-05-04.depth"
        _write_depth(depth)
        source = root / "candidates.jsonl"
        output = root / "features.jsonl"
        checkpoint = root / "checkpoint.json"
        rows = [
            {
                "schema_version": "strategy_follow_candidate_v1",
                "candidate_id": "NAS100_2026-05-04T16:30:00+00:00",
                "symbol": "NAS100",
                "broker_symbol": "NDX100",
                "decision_time_utc": "2026-05-04T16:30:00+00:00",
                "side": "LONG",
                "framework": "ob_retest",
                "created_at_utc": "2026-05-04T16:30:26+00:00",
                "external_confluence": {
                    "sierra": {
                        "status": "LOCAL_DEPTH_FILE_MISSING",
                        "depth_path": str(depth),
                        "source_symbol": "NQM26-CME",
                        "futures_symbol": "NQ.v.0",
                    }
                },
            },
            {
                "schema_version": "strategy_follow_candidate_v1",
                "candidate_id": "NAS100_2026-05-04T16:15:00+00:00",
                "symbol": "NAS100",
                "broker_symbol": "NDX100",
                "decision_time_utc": "2026-05-04T16:15:00+00:00",
                "side": "LONG",
                "framework": "ob_retest",
                "created_at_utc": "2026-05-04T16:15:26+00:00",
                "external_confluence": {
                    "sierra": {
                        "status": "LOCAL_DEPTH_FILE_MISSING",
                        "depth_path": str(depth),
                        "source_symbol": "NQM26-CME",
                        "futures_symbol": "NQ.v.0",
                    }
                },
            },
        ]
        source.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

        result = mod.run(
            source=source,
            output=output,
            max_hours=10_000,
            checkpoint=checkpoint,
            candidate_ids={"NAS100_2026-05-04T16:15:00+00:00"},
        )

        assert result["rows_written"] == 1
        assert result["candidate_ids"] == ["NAS100_2026-05-04T16:15:00+00:00"]
        assert result["skipped"]["candidate_id_filter"] == 1
        row = json.loads(output.read_text(encoding="utf-8").strip())
        assert row["candidate_id"] == "NAS100_2026-05-04T16:15:00+00:00"
        assert row["feature_status"] == "FEATURES_ATTEMPTED_NO_SAMPLES"
        assert row["data_status"] == "no_depth_samples"
        assert row["sierra_status"] == "LOCAL_DEPTH_FILE_PRESENT_AFTER_INITIAL_MISSING_STATUS"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_build_feature_rows_batch_scans_depth_file_once_for_multiple_candidates():
    root = Path(".test_tmp") / f"sierra_live_enrich_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    try:
        depth = root / "NQM26-CME.2026-05-04.depth"
        _write_depth(depth)
        candidates = []
        for minute in ("16:30", "16:15"):
            candidates.append(
                {
                    "schema_version": "strategy_follow_candidate_v1",
                    "candidate_id": f"NAS100_2026-05-04T{minute}:00+00:00",
                    "symbol": "NAS100",
                    "broker_symbol": "NDX100",
                    "decision_time_utc": f"2026-05-04T{minute}:00+00:00",
                    "side": "LONG",
                    "framework": "ob_retest",
                    "analysis_decision": "CANDIDATE",
                    "created_at_utc": f"2026-05-04T{minute}:26+00:00",
                    "external_confluence": {
                        "sierra": {
                            "status": "LOCAL_DEPTH_FILE_PRESENT_FEATURE_EXTRACTION_DEFERRED",
                            "depth_path": str(depth),
                            "source_symbol": "NQM26-CME",
                            "futures_symbol": "NQ.v.0",
                            "source_status": "LOCAL_SIERRA_DEPTH_CAPTURED",
                            "parity_status": "DATABENTO_MBP10_PARITY_EXACT_ON_REGISTERED_NQ_PILOT",
                            "interpretation_status": "USABLE_AS_REGISTERED_NQ_DEPTH_CONTEXT",
                        }
                    },
                }
            )

        rows = mod.build_feature_rows_batch(candidates, max_file_size_mb=None)

        assert sorted(rows) == [
            "NAS100_2026-05-04T16:15:00+00:00",
            "NAS100_2026-05-04T16:30:00+00:00",
        ]
        row_1630 = rows["NAS100_2026-05-04T16:30:00+00:00"]
        assert row_1630["feature_status"] == "FEATURES_EXTRACTED"
        assert row_1630["features_present"] is True
        assert row_1630["features"]["event15_median_total_depth10"] == 40
        assert row_1630["batch_depth_file_extraction"] is True
        assert row_1630["depth_header"]["feature_extraction_mode"] == "batch_depth_file_single_pass"
        row_1615 = rows["NAS100_2026-05-04T16:15:00+00:00"]
        assert row_1615["feature_status"] == "FEATURES_ATTEMPTED_NO_SAMPLES"
        assert row_1615["data_status"] == "no_depth_samples"
    finally:
        shutil.rmtree(root, ignore_errors=True)
