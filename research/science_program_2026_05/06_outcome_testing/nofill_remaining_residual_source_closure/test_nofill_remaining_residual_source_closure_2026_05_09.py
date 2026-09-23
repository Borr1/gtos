import hashlib
import json
from collections import Counter
from pathlib import Path


LANE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-09"
TARGET_IDS = {
    "NOFILL-CAT-ROW-0241",
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
}
MAY3_IDS = {"NOFILL-CAT-ROW-0049", "NOFILL-CAT-ROW-0050", "NOFILL-CAT-ROW-0051"}


def read_json(name: str):
    return json.loads((LANE_DIR / name).read_text(encoding="utf-8"))


def read_jsonl(name: str):
    return [
        json.loads(line)
        for line in (LANE_DIR / name).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_row_decision_scope_and_terminal_statuses():
    rows = read_jsonl(f"NOFILL_REMAINING_ROW_DECISION_LEDGER_{DATE}.jsonl")
    assert {row["packet_row_id"] for row in rows} == TARGET_IDS
    assert not ({row["packet_row_id"] for row in rows} & MAY3_IDS)
    assert Counter(row["terminal_source_control_status"] for row in rows) == {
        "SOURCE_CONTROL_CLEARED_INPUT_ONLY": 1,
        "SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES": 4,
    }
    assert all(row["promotion_verdict"] == "NO_PROMOTION_VERDICT" for row in rows)
    assert all(row["validation_safe"] is False for row in rows)
    assert all(row["outcome_review_opened"] is False for row in rows)
    assert all(row["live_effect"] is False for row in rows)
    assert all(row["categorical_lifecycle_label"] is None for row in rows)
    assert all(row["cleared_into_accepted_denominator"] is False for row in rows)


def test_xauusd_active_window_source_clearance_packet():
    packet = read_json(f"NOFILL_REMAINING_XAUUSD_ACTIVE_WINDOW_PROOF_PACKET_{DATE}.json")
    assert packet["packet_row_id"] == "NOFILL-CAT-ROW-0241"
    assert packet["source_control_status"] == "SOURCE_CONTROL_CLEARED_INPUT_ONLY"
    assert packet["source_control_label"] == "source_control_no_entry_touch_through_cancel"
    assert packet["mt5_read_only_capture"]["status"] == "RECOVERED_READ_ONLY_QUOTE_TICKS"
    assert packet["broker_offset_evidence"]["rounded_broker_offset_seconds"] == 10800
    assert packet["recovered_gap_rows_through_cancel"] > 0
    assert packet["entry_touch_before_cancel"] is False
    assert packet["max_bid_through_cancel"] < packet["entry_price"]
    assert packet["mt5_read_only_capture"]["account_order_deal_position_history_calls"] == 0
    assert packet["mt5_read_only_capture"]["order_send_calls"] == 0
    assert packet["mt5_read_only_capture"]["paid_api_or_databento_calls"] == 0


def test_usdjpy_same_tick_contract_impossibility_packet():
    packet = read_json(f"NOFILL_REMAINING_USDJPY_SAME_TICK_EVENT_ORDER_PROOF_PACKET_{DATE}.json")
    assert set(packet["target_rows"]) == TARGET_IDS - {"NOFILL-CAT-ROW-0241"}
    assert packet["contract_status"] == "SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES_FOR_CURRENT_APPROVED_SOURCES"
    assert len(packet["row_evidence"]) == 4
    assert all(capture["exists"] for capture in packet["official_doc_contract"]["raw_captures"])
    for row in packet["row_evidence"]:
        assert row["terminal_source_control_status"] == "SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES"
        assert row["exact_timestamp_row_count"] == 1
        assert set(row["true_predicates_on_single_quote_row"]) == {"entry_touch", "protective_level"}
        assert "sequence" in row["exact_next_source_needed"].lower()
        assert "sub-row" in row["exact_next_source_needed"].lower()


def test_source_hash_manifest_recomputes():
    manifest = read_json(f"NOFILL_REMAINING_SOURCE_HASH_MANIFEST_{DATE}.json")
    assert manifest["record_count"] >= 12
    for record in manifest["records"]:
        assert record["exists"], record["path"]
        path = Path(record["path"])
        assert path.exists(), record["path"]
        if record.get("hash_verification_mode") == "presence_only_mutable_context":
            assert record.get("snapshot_sha256"), record["path"]
            continue
        assert record["sha256"] == sha256_file(path)


def test_noleak_duplicate_denominator_audit():
    audit = read_json(f"NOFILL_REMAINING_NOLEAK_DUPLICATE_DENOMINATOR_AUDIT_{DATE}.json")
    assert audit["target_row_count"] == 5
    assert audit["may3_rows_reopened"] == []
    assert audit["reject_total_preserved_outside_labels_denominators"] == 65
    assert audit["rows_moved_to_accepted_denominator"] == 0
    assert audit["lifecycle_labels_assigned"] == 0
    assert audit["result_or_performance_labels_assigned"] == 0
    assert audit["validation_safe_true_count"] == 0
    assert audit["outcome_review_opened_true_count"] == 0
    assert audit["live_effect_true_count"] == 0
    assert audit["forbidden_output_key_hits"] == []
    assert audit["violations"] == []
