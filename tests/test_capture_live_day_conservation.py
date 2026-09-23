import json
from datetime import datetime, timezone

from scripts.capture_live_day_conservation import scan_ledger_window
from src.components.ultimate_book.runtime_learning_packet import build_runtime_learning_packet


def _packet(event_type: str, ts: str):
    return build_runtime_learning_packet(
        namespace="operator_profile",
        event_type=event_type,
        ts=ts,
        outcome={
            "candidate_id": "candidate-1",
            "sleeve": "metals_core",
            "symbol": "XAUUSD",
            "direction": "LONG",
            "decision_bar_iso": "2026-08-13T08:00:00+00:00",
            "placement_status": "placed" if event_type == "unit_placed" else None,
            "gtos_live_flow_execution": {
                "request_status": "sent",
                "result_status": "success",
                "fill_status": "broker_fill_observed",
            } if event_type == "unit_placed" else None,
        },
    )


def test_scan_ledger_window_reads_backwards_filters_and_reconciles(tmp_path):
    path = tmp_path / "packets.jsonl"
    rows = [
        _packet("candidate_generated", "2026-08-12T10:00:00+00:00"),
        _packet("candidate_generated", "2026-08-13T08:00:00+00:00"),
        _packet("unit_placed", "2026-08-13T08:00:01+00:00"),
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    report = scan_ledger_window(
        path,
        stream="main",
        starts={"FTMO": datetime(2026, 8, 13, tzinfo=timezone.utc)},
        end=datetime(2026, 8, 13, 9, tzinfo=timezone.utc),
    )

    assert report["status"] == "PASS"
    assert report["scan"]["selected_rows"] == 2
    assert report["summary"]["event_counts"] == {"candidate_generated": 1, "unit_placed": 1}
    assert report["summary"]["live_flow_reconciliation"]["status"] == "PASS"
    assert report["summary"]["candidate_path_counts"] == {
        "candidate_generated -> unit_placed": 1
    }


def test_scan_ledger_window_reports_packet_hash_failure(tmp_path):
    path = tmp_path / "packets.jsonl"
    row = _packet("candidate_generated", "2026-08-13T08:00:00+00:00")
    row["packet_hash_sha256"] = "tampered"
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    report = scan_ledger_window(
        path,
        stream="main",
        starts={"FTMO": datetime(2026, 8, 13, tzinfo=timezone.utc)},
        end=datetime(2026, 8, 13, 9, tzinfo=timezone.utc),
    )

    assert report["status"] == "FAIL"
    assert report["packet_validation_issue_counts"]["packet_hash_mismatch"] == 1
