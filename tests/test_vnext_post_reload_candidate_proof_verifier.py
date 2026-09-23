from __future__ import annotations

import json
from datetime import datetime, timezone

from scripts import build_vnext_post_reload_candidate_proof as builder
from scripts import verify_vnext_post_reload_candidate_proof as verifier


def test_verify_accepts_current_no_candidate_absence_proof(tmp_path, monkeypatch):
    reload_ts = "2026-05-28T22:38:40.246000+00:00"
    summary = {
        "schema_version": "vnext_post_reload_candidate_proof_summary_v1",
        "candidate_records_after_reload": 0,
        "reload_timestamp_utc": reload_ts,
    }
    ledger = tmp_path / "ledger.jsonl"
    summary_path = tmp_path / "summary.json"
    checkpoint = tmp_path / "checkpoint.json"
    ledger.write_text("", encoding="utf-8")
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    checkpoint.write_text(
        json.dumps(
            {
                "post_reload_candidate_flow": {
                    "reload_timestamp_utc": reload_ts,
                    "candidate_records_after_reload": 0,
                    "candidate_absence_proof_status": (
                        "no_post_reload_vnext_candidate_records_since_current_process_reload"
                    ),
                    "live_writer_packet_proof_status": (
                        "pending_next_post_patch_candidate_written_by_live_process"
                    ),
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "LEDGER_PATH", ledger)
    monkeypatch.setattr(verifier, "SUMMARY_PATH", summary_path)
    monkeypatch.setattr(verifier, "CHECKPOINT_PATH", checkpoint)
    monkeypatch.setattr(
        verifier,
        "build",
        lambda reload_ts_text: ([], dict(summary)),
    )

    result = verifier.verify(reload_ts_text=reload_ts)

    assert result["ok"] is True
    assert result["candidate_records_after_reload"] == 0
    assert result["candidate_absence_proof"]["proven"] is True


def test_verify_rejects_no_candidate_without_matching_checkpoint_proof(
    tmp_path, monkeypatch
):
    reload_ts = "2026-05-28T22:38:40.246000+00:00"
    summary = {
        "schema_version": "vnext_post_reload_candidate_proof_summary_v1",
        "candidate_records_after_reload": 0,
        "reload_timestamp_utc": reload_ts,
    }
    ledger = tmp_path / "ledger.jsonl"
    summary_path = tmp_path / "summary.json"
    checkpoint = tmp_path / "checkpoint.json"
    ledger.write_text("", encoding="utf-8")
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    checkpoint.write_text(
        json.dumps({"post_reload_candidate_flow": {"reload_timestamp_utc": "stale"}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "LEDGER_PATH", ledger)
    monkeypatch.setattr(verifier, "SUMMARY_PATH", summary_path)
    monkeypatch.setattr(verifier, "CHECKPOINT_PATH", checkpoint)
    monkeypatch.setattr(
        verifier,
        "build",
        lambda reload_ts_text: ([], dict(summary)),
    )

    result = verifier.verify(reload_ts_text=reload_ts)

    assert result["ok"] is False
    assert any(
        issue["code"] == "no_post_reload_candidate_records_found"
        for issue in result["issues"]
    )


def test_builder_excludes_touched_historical_candidate_records(tmp_path, monkeypatch):
    trade_root = tmp_path / "knowledge_base" / "trade_records" / "NAS100"
    trade_root.mkdir(parents=True)
    stale_record = trade_root / "2026-05-29_moonshot_h06_07_0615.json"
    stale_record.write_text(
        json.dumps(
            {
                "metadata": {
                    "candle_time": "2026-05-29T06:15:00+00:00",
                    "symbol": "NAS100",
                },
                "moonshot_broader_origin_candidate": {"candidate_id": "old"},
            }
        ),
        encoding="utf-8",
    )
    fresh_record = trade_root / "2026-05-30_moonshot_h23_00_2300.json"
    fresh_record.write_text(
        json.dumps(
            {
                "metadata": {
                    "candle_time": "2026-05-30T23:00:00+00:00",
                    "symbol": "NAS100",
                },
                "moonshot_broader_origin_candidate": {"candidate_id": "fresh"},
            }
        ),
        encoding="utf-8",
    )
    reload_ts = datetime.fromisoformat("2026-05-30T22:56:38+00:00")
    monkeypatch.setattr(builder, "REPO_ROOT", tmp_path)

    rows = builder._candidate_records_after(reload_ts)

    assert [row[0].name for row in rows] == [fresh_record.name]
