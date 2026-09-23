from __future__ import annotations

import json
from pathlib import Path

from scripts.audit_wave4r_ltf_coverage import build_report


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_ltf_coverage_audit_matches_symbol_date_files_without_inferring_fills(tmp_path):
    ledger = tmp_path / "ordered_path.jsonl"
    write_jsonl(
        ledger,
        [
            {
                "ordered_path_source_status": "ordered_touch_times_missing",
                "candidate_id": "c1",
                "symbol": "XAUUSD",
                "asof_utc": "2026-06-02T12:00:00+00:00",
                "recovery_status": "recovered",
            },
            {
                "ordered_path_source_status": "ordered_touch_times_missing",
                "candidate_id": "c2",
                "symbol": "EURUSD",
                "asof_utc": "2022-01-03T12:00:00+00:00",
                "recovery_status": "recovered",
            },
            {
                "ordered_path_source_status": "ordered_touch_times_from_path_row",
                "candidate_id": "c3",
                "symbol": "XAUUSD",
                "asof_utc": "2026-06-02T12:15:00+00:00",
            },
        ],
    )
    m1_file = tmp_path / "data" / "m1" / "XAUUSD" / "2026-06-02.csv"
    tick_file = (
        tmp_path
        / "data"
        / "ticks"
        / "redacted_account_live_bee34003"
        / "XAUUSD"
        / "2026-06-02.parquet"
    )
    m1_file.parent.mkdir(parents=True)
    tick_file.parent.mkdir(parents=True)
    m1_file.write_text("time_utc,open,high,low,close\n", encoding="utf-8")
    tick_file.write_bytes(b"PAR1")

    report, requirements = build_report(
        ordered_path_ledger=ledger,
        source_roots=(tmp_path / "data" / "m1", tmp_path / "data" / "ticks"),
    )

    summary = report["coverage_summary"]
    assert report["source_boundary"] == (
        "read_only_local_file_coverage_audit_no_fill_inference_no_replay_mutation"
    )
    assert summary["rows_scanned"] == 3
    assert summary["missing_ordered_touch_rows"] == 2
    assert summary["matched_local_m1_rows"] == 1
    assert summary["matched_local_tick_rows"] == 1
    assert summary["matched_any_local_ltf_rows"] == 1
    assert summary["unmatched_local_ltf_rows"] == 1
    assert len(requirements) == 2
    statuses = {row["symbol"]: row["coverage_status"] for row in requirements}
    assert statuses == {
        "EURUSD": "local_ltf_missing",
        "XAUUSD": "local_ltf_match_available",
    }
