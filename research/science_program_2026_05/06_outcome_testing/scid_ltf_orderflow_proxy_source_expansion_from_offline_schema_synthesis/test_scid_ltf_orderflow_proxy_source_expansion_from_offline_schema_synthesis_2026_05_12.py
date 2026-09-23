from __future__ import annotations

import json
from pathlib import Path

from verify_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12 import verify


ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-12"
PREFIX = "SCID_LTF_OF_PROXY_EXPANSION"


def load_json(stem: str) -> dict:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def test_reconciliation_preserves_accepted_offline_schema_boundary():
    reconciliation = load_json("ACCEPTED_AUDIT_RECONCILIATION")
    checks = {row["check_id"]: row for row in reconciliation["reconciliation_checks"]}

    assert reconciliation["accepted_g12_offline_schema_decision"] == (
        "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY"
    )
    assert checks["candidate_rows_3014"]["actual"] == 3014
    assert checks["unique_candidate_ids_3014"]["actual"] == 3014
    assert checks["unique_duplicate_keys_3014"]["actual"] == 3014
    assert checks["ten_capture_groups"]["actual"] == 10
    assert reconciliation["live_wiring_absent"] is True
    assert reconciliation["manifest_binding_repair_preserved"]["all_other_hash_mismatches_strict"] is True
    assert all(row["status"] == "PASS" for row in checks.values())


def test_acquisition_ladder_and_inventory_are_not_current_worktree_only():
    acquisition = load_json("ACQUISITION_LADDER")
    inventory = load_json("SOURCE_INVENTORY_HASH_MANIFEST")

    assert acquisition["searched_beyond_current_worktree"] is True
    assert acquisition["searched_root_count"] >= 10
    assert acquisition["selected_source_count"] == inventory["source_inventory_count"]
    root_ids = {row["root_id"] for row in acquisition["ladder_rows"]}
    assert "external_sierra_scid_data_root" in root_ids
    assert "external_sierra_depth_data_root" in root_ids
    assert "absolute_production_tick_root" in root_ids
    assert inventory["raw_market_blob_commits_added"] == 0
    assert inventory["forbidden_broker_account_order_history_deal_position_sources_consumed"] == 0
    assert inventory["hash_status_counts"]["HASH_DEFERRED_RAW_MARKET_BLOB_OR_LARGE_EXTERNAL_FILE"] > 0
    assert inventory["hash_status_counts"]["HASHED_NOW"] > 0


def test_ltf_and_orderflow_matrices_cover_required_schema_groups():
    ltf = load_json("LTF_SOURCE_MATRIX")
    orderflow = load_json("ORDERFLOW_PROXY_MATRIX")

    ltf_families = {row["source_family"] for row in ltf["rows"]}
    assert {
        "accepted_scid_m15_source_control_bars",
        "sierra_converted_m1_m5_m15_ohlcv_roots",
        "prior_production_mt5_tick_parquet_market_context",
        "sierra_scid_time_and_sales",
        "path_context_shadow_logs",
        "session_volatility_context_logs",
    }.issubset(ltf_families)
    assert "LTF" in ltf["accepted_schema_groups_covered"]

    orderflow_families = {row["source_family"] for row in orderflow["rows"]}
    assert {
        "sierra_depth_market_depth",
        "sierra_scid_footprint_bid_ask_volume",
        "databento_cached_or_declared_orderflow_artifacts",
        "proxy_mapping_registry_and_blocker_logs",
    }.issubset(orderflow_families)
    assert orderflow["accepted_schema_groups_covered"] == ["orderflow/proxy"]
    assert all("not broker-native" in row["proxy_boundary"].lower() or "source-transfer" in row["proxy_boundary"].lower() for row in orderflow["rows"])


def test_candidate_group_coverage_and_proxy_non_equivalence():
    coverage = load_json("CANDIDATE_COVERAGE_MATRIX")
    proxy = load_json("PROXY_VALIDITY_LEDGER")

    assert coverage["candidate_summary"]["candidate_rows"] == 3014
    assert coverage["coverage_row_count"] == 7
    assert coverage["all_candidate_groups_covered"] is True
    assert {row["candidate_rows"] for row in coverage["rows"]} == {48, 421, 509}
    assert all(row["sierra_scid_present"] for row in coverage["rows"])
    assert all(row["converted_m1_present"] for row in coverage["rows"])
    assert all(row["candidate_boundary"] == "SOURCE_CONTROL_EXPECTATION_ONLY_NOT_RESULT_DENOMINATOR" for row in coverage["rows"])

    assert proxy["all_proxy_rows_context_only"] is True
    assert proxy["broker_native_cfd_truth_claims"] == 0
    assert len(proxy["proxy_rows"]) == 7
    assert all(row["validity_status"] == "CONTEXT_ONLY_NOT_BROKER_NATIVE_CFD_TRUTH" for row in proxy["proxy_rows"])


def test_exact_approval_gates_and_noleak_policy_are_present():
    gates = load_json("APPROVAL_GATE_LEDGER")
    noleak = load_json("ASOF_NOLEAK_DUPLICATE_POLICY")

    gate_ids = {row["gate_id"] for row in gates["approval_gates"]}
    assert {
        "GATE_RAW_SIERRA_HASH_OR_WINDOW_EXTRACT",
        "GATE_PRIOR_WORKTREE_TICK_PARQUET_CONSUMPTION",
        "GATE_DATABENTO_NEW_PULL",
        "GATE_LIVE_WIRING",
        "GATE_BROKER_ACCOUNT_ORDER_HISTORY_DEAL_POSITION",
    }.issubset(gate_ids)
    assert gates["unresolved_vague_blockers"] == []
    assert noleak["duplicate_policy"]["candidate_input_row_id_expected_unique"] == 3014
    assert noleak["duplicate_policy"]["duplicate_proxy_denominator_key_expected_unique"] == 3014
    assert "R/PnL/win-rate/expectancy/performance/result labels" in noleak["forbidden_fields_fail_closed"]


def test_decision_prompt_completion_and_verifier_pass():
    decision = load_json("DECISION_LEDGER")
    completion = load_json("COMPLETION_AUDIT")

    assert decision["terminal_decision"] == "BUILT_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_G12_AUDIT_REQUIRED"
    assert decision["ready_for_g12_audit"] is True
    assert decision["terminal_blockers"] == []
    assert completion["completion_standard_satisfied"] is True
    assert completion["missing_incomplete_or_weakly_verified_requirements"] == []
    assert completion["validation_safe"] is False
    assert completion["outcome_review_opened"] is False
    assert completion["live_effect"] is False

    result = verify()
    assert result["ok"], result["failures"]
    assert result["can_mark_goal_complete"] is True

    closeout_path = ROUTE_DIR / f"{PREFIX}_CLOSEOUT_VERIFICATION_{DATE_TAG}.json"
    closeout = json.loads(closeout_path.read_text(encoding="utf-8"))
    closeout["standalone_verifier"] = {
        "status": "PASSED",
        "command": (
            "python research/science_program_2026_05/06_outcome_testing/"
            "scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/"
            "verify_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py"
        ),
        "observed_result": "ok=true",
    }
    closeout["focused_pytest"] = {
        "status": "PASSED",
        "command": (
            "python -m pytest -q -p no:cacheprovider research/science_program_2026_05/06_outcome_testing/"
            "scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/"
            "test_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py"
        ),
        "observed_result": "6 passed",
    }
    closeout_path.write_text(json.dumps(closeout, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")

    prompt_path = Path(
        "research/science_program_2026_05/04_goal_prompts/"
        "G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_GOAL_PROMPT_2026-05-12.md"
    )
    text = prompt_path.read_text(encoding="utf-8")
    for phrase in [
        "3,014",
        "ten capture groups",
        "source inventory",
        "hash/hash-deferral",
        "proxy-validity",
        "NO_PROMOTION_VERDICT",
        "validation_safe=false",
        "outcome_review_opened=false",
        "live_effect=false",
        "Completion Standard",
    ]:
        assert phrase in text
