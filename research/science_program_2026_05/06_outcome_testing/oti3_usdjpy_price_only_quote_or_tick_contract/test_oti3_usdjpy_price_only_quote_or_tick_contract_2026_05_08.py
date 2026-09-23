from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import build_oti3_usdjpy_price_only_quote_or_tick_contract_2026_05_08 as builder


def _row(side: str = "SHORT") -> dict:
    return {
        "packet_row_id": "NOFILL-CAT-ROW-TEST",
        "source_close_packet_row_id": "NOFILL-CLOSE-ROW-TEST",
        "source_inventory_id": "CNR-T3-CAND-TEST",
        "source_lane": "OTI3_G3_GEOMETRY",
        "source_packet_id": "OTG0-PKT-TEST",
        "source_row_id": "USDJPY_TEST",
        "symbol": "USDJPY",
        "session": "tokyo",
        "side": side,
        "decision_asof_utc": "2026-05-01T00:15:00Z",
        "entry_price": 160.0,
        "terminal_area_price": 159.5,
        "protective_level_price": 160.5,
        "nofill_duplicate_key": "k",
        "duplicate_group_id": "g",
        "source_references": [],
    }


def _write_ticks(path: Path, rows: list[dict]) -> None:
    df = pd.DataFrame(rows)
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    df.to_parquet(path, index=False)


def test_short_terminal_first_assigns_terminal_before_entry(tmp_path: Path):
    path = tmp_path / "ticks.parquet"
    _write_ticks(
        path,
        [
            {"ts_utc": "2026-05-01T00:16:00Z", "ts_msc": 1, "bid": 159.48, "ask": 159.49, "last": 0, "volume": 0, "flags": 0},
            {"ts_utc": "2026-05-01T00:17:00Z", "ts_msc": 2, "bid": 160.0, "ask": 160.01, "last": 0, "volume": 0, "flags": 0},
        ],
    )
    decision = builder.classify_row(_row("SHORT"), path, {})
    assert decision["eligibility_decision"] == "ELIGIBLE_CONTRACT_EVIDENCE"
    assert decision["categorical_lifecycle_label"] == "nofill_terminal_before_entry"
    assert decision["ordered_source_events"][0]["event"] == "terminal_area"


def test_short_entry_first_blocks_to_separate_fill_path(tmp_path: Path):
    path = tmp_path / "ticks.parquet"
    _write_ticks(
        path,
        [
            {"ts_utc": "2026-05-01T00:16:00Z", "ts_msc": 1, "bid": 160.0, "ask": 160.01, "last": 0, "volume": 0, "flags": 0},
            {"ts_utc": "2026-05-01T00:17:00Z", "ts_msc": 2, "bid": 159.48, "ask": 159.49, "last": 0, "volume": 0, "flags": 0},
        ],
    )
    decision = builder.classify_row(_row("SHORT"), path, {})
    assert decision["eligibility_decision"] == "BLOCKED_EXACT"
    assert "BLOCK_OTI3_ENTRY_TOUCH_BEFORE_TERMINAL_SEPARATE_FILL_PATH_CONTRACT_REQUIRED" in decision["exact_blocker_codes"]


def test_same_timestamp_conflict_blocks(tmp_path: Path):
    path = tmp_path / "ticks.parquet"
    _write_ticks(
        path,
        [
            {"ts_utc": "2026-05-01T00:16:00Z", "ts_msc": 1, "bid": 160.0, "ask": 159.4, "last": 0, "volume": 0, "flags": 0},
        ],
    )
    decision = builder.classify_row(_row("SHORT"), path, {})
    assert decision["eligibility_decision"] == "BLOCKED_EXACT"
    assert "BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS" in decision["exact_blocker_codes"]


def test_actual_oti3_universe_is_69_rows():
    rows = builder.load_oti3_rows()
    assert len(rows) == 69
    assert {row["symbol"] for row in rows} == {"USDJPY"}
    assert all("BLOCK_RESULT_LTF_PRICE_ONLY" in row["result_blocker_codes"] for row in rows)
