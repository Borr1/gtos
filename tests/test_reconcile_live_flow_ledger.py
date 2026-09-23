import json

from scripts.reconcile_live_flow_ledger import load_rows
from src.components.ultimate_book.runtime_learning_packet import build_runtime_learning_packet


def test_loader_discards_irrelevant_large_packet_payload_before_reconciliation(tmp_path):
    packet = build_runtime_learning_packet(
        namespace="operator_profile",
        event_type="candidate_generated",
        outcome={
            "candidate_id": "candidate-1",
            "sleeve": "metals_core",
            "symbol": "XAUUSD",
            "direction": "LONG",
            "decision_bar_iso": "2026-08-13T08:00:00+00:00",
        },
    )
    packet["irrelevant_bulk"] = "x" * 1_000_000
    path = tmp_path / "packets.jsonl"
    path.write_text(json.dumps(packet) + "\n", encoding="utf-8")

    rows, ingestion = load_rows(path)

    assert ingestion["status"] == "PASS"
    assert len(rows) == 1
    assert "irrelevant_bulk" not in rows[0]
    assert set(rows[0]) <= {
        "event_type",
        "created_at_utc",
        "live_flow",
        "sleeve",
        "symbol",
        "timeframe",
        "direction",
        "decision_bar_iso",
    }


def test_reconciler_accepts_one_pass_generator_without_materializing_source():
    from src.components.ultimate_book.live_flow import reconcile_live_flow_rows

    packets = (
        build_runtime_learning_packet(
            namespace="operator_profile",
            event_type="candidate_generated",
            outcome={
                "candidate_id": f"candidate-{index}",
                "sleeve": "metals_core",
                "symbol": f"SYM{index}",
                "direction": "LONG",
                "decision_bar_iso": "2026-08-13T08:00:00+00:00",
            },
        )
        for index in range(3)
    )
    report = reconcile_live_flow_rows(packets)
    assert report["counts"]["rows_total"] == 3
    assert report["counts"]["candidate_flows_missing_disposition"] == 3
