from __future__ import annotations

import importlib.util
import json
from pathlib import Path


LANE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-09"
TARGET_ROW_IDS = {"NOFILL-CAT-ROW-0049", "NOFILL-CAT-ROW-0050", "NOFILL-CAT-ROW-0051"}
TERMINAL_STATUS = "MARKET_SESSION_NONTRADING_EMPTY_PROVEN_SOURCE_CONTROL"


def load_json(name: str):
    return json.loads((LANE_DIR / name).read_text(encoding="utf-8"))


def load_jsonl(name: str):
    rows = []
    with (LANE_DIR / name).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_verifier():
    path = LANE_DIR / "verify_nofill_may3_opening_range_market_closure_or_source_proof_2026_05_09.py"
    spec = importlib.util.spec_from_file_location("nofill_may3_verifier", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_exact_three_row_scope_and_terminal_status():
    rows = load_jsonl(f"NOFILL_MAY3_ROW_DECISION_LEDGER_{DATE}.jsonl")
    assert {row["packet_row_id"] for row in rows} == TARGET_ROW_IDS
    assert len(rows) == 3
    assert {row["terminal_source_control_status"] for row in rows} == {TERMINAL_STATUS}
    assert all(row["categorical_lifecycle_label"] is None for row in rows)
    assert all(row["cleared_into_accepted_denominator"] is False for row in rows)


def test_market_session_conversion_is_pre_open():
    packet = load_json(f"NOFILL_MAY3_SOURCE_PROOF_PACKET_{DATE}.json")
    conversion = packet["market_session_conversion"]
    assert conversion["frozen_window_utc"]["start"] == "2026-05-03T13:00:00Z"
    assert conversion["frozen_window_utc"]["end"] == "2026-05-03T13:30:00Z"
    assert conversion["official_globex_sunday_open_utc"] == "2026-05-03T22:00:00Z"
    assert conversion["window_is_before_official_sunday_open"] is True


def test_broker_tick_parquets_have_zero_window_rows():
    ledger = load_json(f"NOFILL_MAY3_MARKET_SESSION_SOURCE_LEDGER_{DATE}.json")
    broker_records = {
        record["symbol"]: record
        for record in ledger["source_records"]
        if record["source_family"] == "broker_tick_parquet"
    }
    assert broker_records["NAS100"]["window_rows"] == 0
    assert broker_records["XAUUSD"]["window_rows"] == 0
    assert broker_records["NAS100"]["first_timestamp_utc"].startswith("2026-05-03T22:00:00")
    assert broker_records["XAUUSD"]["first_timestamp_utc"].startswith("2026-05-03T22:00:00")


def test_duplicate_boundary_and_reject_preservation():
    noleak = load_json(f"NOFILL_MAY3_NOLEAK_DUPLICATE_AUDIT_{DATE}.json")
    assert noleak["reject_total_preserved_outside_labels_denominators"] == 65
    assert noleak["result_labels_assigned"] == 0
    assert noleak["rows_moved_into_accepted_denominator"] == 0
    xau_groups = [rows for key, rows in noleak["duplicate_key_groups"].items() if "XAUUSD" in key]
    assert xau_groups == [["NOFILL-CAT-ROW-0050", "NOFILL-CAT-ROW-0051"]]


def test_verifier_passes():
    verifier = load_verifier()
    result = verifier.verify()
    assert result["ok"], result["issues"]
