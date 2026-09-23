from __future__ import annotations

import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"


def test_stage02_summary_advances_to_policy_engine() -> None:
    summary = json.loads(
        (ROUTE_DIR / f"VNEXT_MOONSHOT_SOURCE_PATH_CAPABILITY_SUMMARY_{DATE_ID}.json").read_text(
            encoding="utf-8"
        )
    )
    state = json.loads(
        (ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json").read_text(encoding="utf-8")
    )
    assert summary["first_incomplete_invariant_after_stage02"] == "STAGE_03_DYNAMIC_EXECUTION_POLICY_ENGINE"
    assert summary["no_live_or_paid_access_used"] is True
    assert summary["forbidden_boundaries_crossed"] is False
    assert state["stage_status_table"]["STAGE_02_SOURCE_AND_PATH_CAPABILITY_INVENTORY"] == "complete"
    assert state["first_incomplete_invariant"] != "STAGE_02_SOURCE_AND_PATH_CAPABILITY_INVENTORY"
    assert state["source_gap_ledger_path"].endswith(
        f"VNEXT_MOONSHOT_FORWARD_CAPTURE_REQUIREMENTS_{DATE_ID}.jsonl"
    )


def test_stage02_capability_ledger_contains_ranked_dynamic_sources() -> None:
    ledger = ROUTE_DIR / f"VNEXT_MOONSHOT_SOURCE_PATH_CAPABILITY_LEDGER_{DATE_ID}.jsonl"
    families = set()
    priorities = set()
    usable_count = 0
    with ledger.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            families.add(row["source_family"])
            priorities.add(row["source_priority_rank"])
            if row["dynamic_execution_usable"]:
                usable_count += 1
    assert {"ohlc_bars", "tick_parquet", "shadow_log", "trade_record", "route_artifact"} <= families
    assert 1 in priorities
    assert 2 in priorities
    assert usable_count > 0


def test_stage02_forward_capture_blocks_price_only_reconstruction() -> None:
    forward = ROUTE_DIR / f"VNEXT_MOONSHOT_FORWARD_CAPTURE_REQUIREMENTS_{DATE_ID}.jsonl"
    rows = [json.loads(line) for line in forward.read_text(encoding="utf-8").splitlines() if line.strip()]
    fields = {row["field_or_contract"] for row in rows}
    assert "order_ticket" in fields
    assert "deal_ticket" in fields
    assert "partial_exit_lifecycle" in fields
    assert "bid_ask_tick_ordering_between_entry_stop_target" in fields
    assert any(row["historical_reconstruction_policy"] == "do_not_infer_from_price_alone" for row in rows)
