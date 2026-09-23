from __future__ import annotations

import json
from pathlib import Path

from scripts import audit_sierra_live_depth_confluence as mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _candidate(candidate_id: str, symbol: str = "NAS100") -> dict:
    return {
        "schema_version": "strategy_follow_candidate_v1",
        "row_key": f"candidate|{candidate_id}",
        "candidate_id": candidate_id,
        "symbol": symbol,
        "broker_symbol": "NDX100",
        "decision_time_utc": "2026-05-04T16:30:00+00:00",
        "created_at_utc": "2026-05-04T16:30:20+00:00",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }


def _feature(candidate_id: str, status: str, *, features_present: bool = False) -> dict:
    return {
        "schema_version": "sierra_depth_feature_snapshot_v1",
        "row_key": f"feature|{candidate_id}|{status}",
        "candidate_id": candidate_id,
        "symbol": "NAS100",
        "decision_time_utc": "2026-05-04T16:30:00+00:00",
        "created_at_utc": "2026-05-04T16:31:00+00:00",
        "source_system": "sierra_depth",
        "depth_path": "C:/SierraChart/Data/MarketDepthData/NQM26-CME.2026-05-04.depth",
        "depth_file_size_bytes": 750_000_000,
        "feature_status": status,
        "features_present": features_present,
        "features": {"event15_median_total_depth10": 100} if features_present else {},
        "source_status": "LOCAL_SIERRA_DEPTH_CAPTURED",
        "parity_status": "DATABENTO_MBP10_PARITY_EXACT_ON_REGISTERED_NQ_PILOT",
        "interpretation_status": "USABLE_AS_REGISTERED_NQ_DEPTH_CONTEXT",
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "no_leak_status": "PASS_PRE_DECISION_WINDOWS_ONLY",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }


def _source(candidate_id: str) -> dict:
    return {
        "schema_version": "sierra_confluence_source_status_v1",
        "row_key": f"source|{candidate_id}",
        "candidate_id": candidate_id,
        "symbol": "NAS100",
        "created_at_utc": "2026-05-04T16:30:30+00:00",
        "source_status": "LOCAL_SIERRA_DEPTH_CAPTURED",
        "parity_status": "DATABENTO_MBP10_PARITY_EXACT_ON_REGISTERED_NQ_PILOT",
        "interpretation_status": "USABLE_AS_REGISTERED_NQ_DEPTH_CONTEXT",
        "features_present": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }


def test_audit_reports_guarded_background_queue(tmp_path):
    cid_a = "NAS100_2026-05-04T16:30:00+00:00"
    cid_b = "NAS100_2026-05-04T16:15:00+00:00"
    _write_jsonl(tmp_path / "shadow_logs/strategy_follow_candidates.jsonl", [_candidate(cid_a), _candidate(cid_b)])
    _write_jsonl(
        tmp_path / "shadow_logs/sierra_depth_feature_snapshots.jsonl",
        [
            _feature(cid_a, "FEATURES_EXTRACTED", features_present=True),
            _feature(cid_b, "FEATURE_EXTRACTION_DEFERRED_FILE_SIZE_GUARD"),
        ],
    )
    _write_jsonl(tmp_path / "shadow_logs/sierra_confluence_source_status.jsonl", [_source(cid_a), _source(cid_b)])
    _write_json(
        tmp_path / "pipeline_state/sierra_depth_enrichment_checkpoint.json",
        {"schema_version": "sierra_depth_enrichment_checkpoint_v1", "candidates": {cid_a: {}, cid_b: {}}},
    )

    report = mod.build_report(root=tmp_path, generated_at_utc="2026-05-05T00:00:00+00:00")

    row = report["status_row"]
    assert report["status"] == "OK_WITH_FILE_SIZE_GUARDED_BACKGROUND_QUEUE"
    assert row["current_counts"]["features_extracted"] == 1
    assert row["current_counts"]["file_size_guard_candidates"] == 1
    assert row["current_counts"]["missing_feature_rows"] == 0
    assert row["paid_data_calls"] == 0
    assert row["paid_fetch_attempted"] is False
    assert row["background_queue_policy"]["file_size_guard"] == "supported_by_max_file_size_mb"


def test_audit_flags_missing_feature_rows(tmp_path):
    cid = "NAS100_2026-05-04T16:30:00+00:00"
    _write_jsonl(tmp_path / "shadow_logs/strategy_follow_candidates.jsonl", [_candidate(cid)])
    _write_jsonl(tmp_path / "shadow_logs/sierra_depth_feature_snapshots.jsonl", [])
    _write_jsonl(tmp_path / "shadow_logs/sierra_confluence_source_status.jsonl", [_source(cid)])

    report = mod.build_report(root=tmp_path, generated_at_utc="2026-05-05T00:00:00+00:00")

    assert report["status"] == "ACTION_REQUIRED_MISSING_FEATURE_ROWS"
    assert report["status_row"]["missing_feature_candidates"] == [cid]


def test_append_status_row_is_idempotent(tmp_path):
    cid = "NAS100_2026-05-04T16:30:00+00:00"
    _write_jsonl(tmp_path / "shadow_logs/strategy_follow_candidates.jsonl", [_candidate(cid)])
    _write_jsonl(
        tmp_path / "shadow_logs/sierra_depth_feature_snapshots.jsonl",
        [_feature(cid, "FEATURES_EXTRACTED", features_present=True)],
    )
    _write_jsonl(tmp_path / "shadow_logs/sierra_confluence_source_status.jsonl", [_source(cid)])
    report = mod.build_report(root=tmp_path, generated_at_utc="2026-05-05T00:00:00+00:00")
    target = tmp_path / "shadow_logs/sierra_depth_enrichment_status.jsonl"

    assert mod.append_status_row_if_missing(report["status_row"], target) is True
    assert mod.append_status_row_if_missing(report["status_row"], target) is False
    assert len(target.read_text(encoding="utf-8").splitlines()) == 1
