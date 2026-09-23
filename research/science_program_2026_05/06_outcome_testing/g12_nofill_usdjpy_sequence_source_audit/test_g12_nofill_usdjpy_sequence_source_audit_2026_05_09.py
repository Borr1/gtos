from __future__ import annotations

import json
from pathlib import Path

import build_g12_nofill_usdjpy_sequence_source_audit_2026_05_09 as builder
import verify_g12_nofill_usdjpy_sequence_source_audit_2026_05_09 as verifier


DATE = "2026-05-09"
PROMOTION = "NO_PROMOTION_VERDICT"
TARGET_ROWS = set(builder.TARGET_ROWS)
ROUTE_DIR = Path(__file__).resolve().parent


def load_json(name: str):
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def test_reconstructs_all_four_single_snapshot_rows() -> None:
    rows = builder.reconstruct_target_rows()
    assert {row["packet_row_id"] for row in rows} == TARGET_ROWS
    assert all(row["exact_timestamp_row_count"] == 1 for row in rows)
    assert all(row["single_broker_snapshot_with_simultaneous_predicates"] is True for row in rows)
    assert all(row["sequence_or_subrow_field_found"] is False for row in rows)
    assert all(row["promotion_verdict"] == PROMOTION for row in rows)


def test_source_search_reaudit_rejects_proxy_and_missed_route() -> None:
    builder.main()
    source_search = load_json(f"G12_NOFILL_USDJPY_SEQ_SOURCE_SEARCH_REAUDIT_{DATE}.json")
    checks = source_search["central_claim_checks"]
    assert checks["all_four_rows_reconstructed"] is True
    assert checks["any_sequence_or_subrow_field_found"] is False
    assert checks["source_access_lane_missed_source_safe_route"] is False
    assert checks["proxy_sources_can_clear_broker_native_sequence"] is False
    assert source_search["terminal_g12_verdict"] == "ACCEPT_AS_SOURCE_IMPOSSIBILITY_EVIDENCE_ONLY"
    assert source_search["source_search_conclusion"] == "NO_BROKER_NATIVE_SEQUENCE_SOURCE_FOUND"


def test_mql5_contract_and_external_request_are_bounded() -> None:
    builder.main()
    mql = (ROUTE_DIR / f"G12_NOFILL_USDJPY_SEQ_MQL5_SOURCE_CONTRACT_AUDIT_{DATE}.md").read_text(encoding="utf-8")
    request = (ROUTE_DIR / f"G12_NOFILL_USDJPY_SEQ_EXTERNAL_ACCESS_REQUEST_{DATE}.md").read_text(encoding="utf-8")
    assert "PASS_SOURCE_CONTRACT_LIMIT_CONFIRMED" in mql
    assert "sequence/event ID or sub-row timestamp" in mql
    assert "2026-04-20T00:15:04.153Z" in request
    assert "2026-05-01T00:30:00.083Z" in request
    assert "no account, order, history, deal, position" in request
    assert PROMOTION in request


def test_no_leak_denominator_and_hash_audits_pass() -> None:
    builder.main()
    noleak = load_json(f"G12_NOFILL_USDJPY_SEQ_NO_LEAK_DENOMINATOR_AUDIT_{DATE}.json")
    hash_audit = load_json(f"G12_NOFILL_USDJPY_SEQ_SOURCE_HASH_AUDIT_{DATE}.json")
    assert noleak["all_target_rows_in_source_impossible_exclusion_set"] is True
    assert noleak["accepted_denominator_movement"] == 0
    assert noleak["source_safe_input_only_rows"] == 0
    assert noleak["forbidden_json_key_hits"] == []
    assert not any(noleak["unsafe_flag_hits"].values())
    assert hash_audit["strict_hash_failures"] == []
    assert hash_audit["strict_hash_record_count"] >= 25


def test_verifier_passes() -> None:
    builder.main()
    result = verifier.verify()
    assert result["ok"] is True
    assert result["can_mark_goal_complete"] is True
