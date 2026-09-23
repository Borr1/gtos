#!/usr/bin/env python3
"""Verify OTB6 G6 blocker-clearing proof-pack invariants."""

from __future__ import annotations

import json
from pathlib import Path


RUN_DATE = "2026-05-07"
TARGET_PACKET_IDS = {"OTG0-PKT-060", "OTG0-PKT-061", "OTG0-PKT-063", "OTG0-PKT-066"}
OUT_DIR = Path(__file__).resolve().parent


def load(name: str):
    with (OUT_DIR / name).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def assert_common_flags(payload: dict, name: str) -> None:
    assert payload.get("promotion_verdict") == "NO_PROMOTION_VERDICT", name
    assert payload.get("validation_safe") is False, name
    assert payload.get("outcome_review_opened") is False, name


def main() -> None:
    decision = load(f"OTB6_G6_BLOCKER_CLEARING_DECISION_LEDGER_{RUN_DATE}.json")
    proof = load(f"OTB6_G6_PROOF_MATRIX_{RUN_DATE}.json")
    contract = load(f"OTB6_G6_PROSPECTIVE_CAPTURE_CONTRACT_{RUN_DATE}.json")
    availability = load(f"OTB6_G6_LOCAL_DATA_AVAILABILITY_{RUN_DATE}.json")
    audit = load(f"OTB6_G6_COMPLETION_AUDIT_{RUN_DATE}.json")

    for name, payload in {
        "decision": decision,
        "proof": proof,
        "contract": contract,
        "availability": availability,
        "audit": audit,
    }.items():
        assert_common_flags(payload, name)

    assert set(decision["packet_decisions"]) == TARGET_PACKET_IDS
    assert set(proof["proof_matrix"]) == TARGET_PACKET_IDS
    assert set(contract["contracts"]) == TARGET_PACKET_IDS
    assert audit["can_mark_goal_complete"] is True
    assert audit["scope_checks"]["outcome_testing_run"] is False
    assert audit["scope_checks"]["forbidden_sources_opened"] is False
    assert audit["scope_checks"]["live_trading_surfaces_touched"] is False
    assert audit["scope_checks"]["packet_level_promotions_claimed"] is False

    for packet_id, row in decision["packet_decisions"].items():
        assert row["decision"] == "BLOCKED_WITH_EXACT_REMAINING_EVIDENCE", packet_id
        assert row["remaining_exact_blocker"], packet_id

    proof_status = {
        (packet_id, item["required_evidence"]): item["status"]
        for packet_id, items in proof["proof_matrix"].items()
        for item in items
    }
    assert proof_status[("OTG0-PKT-060", "matched generic retrace comparator")] == "PROVED_LOCALLY"
    assert proof_status[("OTG0-PKT-066", "round-number band packet")] == "PROVED_LOCALLY"
    assert proof_status[("OTG0-PKT-061", "exact executable decision price")] == "NOT_PROVED"
    assert proof_status[("OTG0-PKT-063", "preregistered changepoint parser/model output")] == "NOT_PROVED"

    assert availability["tick_parquet_summary"]["parquet_file_count"] == 0
    assert availability["coverage_verdict"] == "LOCAL_TICK_AND_M1_NOT_AVAILABLE_FOR_TARGET_DECISION_DATES"

    print(json.dumps({"ok": True, "verified_packets": sorted(TARGET_PACKET_IDS)}, indent=2))


if __name__ == "__main__":
    main()
