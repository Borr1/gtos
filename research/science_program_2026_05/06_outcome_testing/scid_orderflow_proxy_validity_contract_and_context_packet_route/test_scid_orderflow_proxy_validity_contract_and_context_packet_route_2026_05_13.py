from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-13"
PREFIX = "SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT"
BUILDER_PATH = ROUTE_DIR / "build_scid_orderflow_proxy_validity_contract_and_context_packet_route_2026_05_13.py"
VERIFIER_PATH = ROUTE_DIR / "verify_scid_orderflow_proxy_validity_contract_and_context_packet_route_2026_05_13.py"


def _load_json(name: str):
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_proxy_dependency_count_reconciles_field_and_card_surfaces() -> None:
    dependency = _load_json(f"{PREFIX}_SOURCE_DEPENDENCY_LEDGER_{DATE}.json")

    assert dependency["proxy_card_count"] == 8
    assert dependency["proxy_field_requirement_count"] == 64
    assert dependency["proxy_card_level_requirement_count"] == 8
    assert dependency["proxy_requirement_surface_count"] == 72
    assert dependency["route_count_reconciliation"]["reconciled_total_surfaces"] == 72
    assert len({row["card_id"] for row in dependency["proxy_cards"]}) == 8
    for row in dependency["proxy_dependency_rows"]:
        assert row["may_score_results_now"] is False
        assert row["broker_native_cfd_truth_claim_allowed"] is False
        assert row["attached_contract_ids"]
        assert row["exact_next_requirement"]


def test_source_family_contracts_are_context_only_and_fail_closed() -> None:
    contract = _load_json(f"{PREFIX}_SOURCE_FAMILY_CONTRACT_{DATE}.json")

    assert contract["contract_count"] == 4
    assert contract["broker_native_cfd_truth_claims"] == 0
    families = {row["source_family"]: row for row in contract["contracts"]}
    assert {
        "sierra_depth_market_depth",
        "sierra_scid_footprint_bid_ask_volume",
        "databento_cached_or_declared_orderflow_artifacts",
        "proxy_mapping_registry_and_blocker_logs",
    } == set(families)
    for row in contract["contracts"]:
        assert row["broker_native_cfd_truth_claim_allowed"] is False
        assert row["may_score_results_now"] is False
        assert row["parser_acceptance_criteria"]
        assert row["roll_session_asof_rule"]
        assert row["staleness_policy"]
        assert row["exact_access_requirement_if_unresolved"]
        assert row["invalid_contexts"]
    assert "Inverse" in _load_json(f"{PREFIX}_EQUIVALENCE_AND_INVALID_CONTEXT_MATRIX_{DATE}.json")["equivalence_rows"][4]["special_mapping_requirement"]


def test_context_packet_schema_and_invalid_contexts_block_misuse() -> None:
    schema = _load_json(f"{PREFIX}_CONTEXT_PACKET_SCHEMA_{DATE}.json")
    equivalence = _load_json(f"{PREFIX}_EQUIVALENCE_AND_INVALID_CONTEXT_MATRIX_{DATE}.json")
    blocker = _load_json(f"{PREFIX}_PAID_ACCESS_FREE_BLOCKER_LEDGER_{DATE}.json")

    for required in [
        "source_family",
        "proxy_mapping_version",
        "contract_month",
        "source_hash_or_deferral_id",
        "non_equivalence_label",
    ]:
        assert required in schema["fail_closed_if_missing"]
    assert schema["allowed_output"].startswith("Context/control packet")
    assert equivalence["equivalence_row_count"] == 7
    assert equivalence["broker_native_cfd_truth_claims"] == 0
    assert all(row["broker_cfd_truth_allowed"] is False for row in equivalence["equivalence_rows"])
    assert all(row["equivalence_status"] == "NON_EQUIVALENT_CONTEXT_OR_CONTROL_ONLY" for row in equivalence["equivalence_rows"])
    assert blocker["all_remainders_exact"] is True
    assert all(row["paid_access_required_now"] is False for row in blocker["rows"])
    assert all(row["exact_requirement"] for row in blocker["rows"])


def test_decision_noleak_completion_and_next_prompt_are_safe() -> None:
    builder = _load_module(BUILDER_PATH, "orderflow_proxy_contract_builder")
    decision = _load_json(f"{PREFIX}_ROUTE_DECISION_LEDGER_{DATE}.json")
    noleak = _load_json(f"{PREFIX}_NOLEAK_SAFE_FLAG_AUDIT_{DATE}.json")
    completion = _load_json(f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json")
    manifest = _load_json(f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.json")

    assert decision["terminal_decision"] == builder.TERMINAL_DECISION
    assert decision["proxy_requirement_surface_count"] == 72
    assert decision["broker_native_cfd_truth_claims"] == 0
    assert noleak["included_card_count"] == 17
    assert noleak["excluded_blocked15_card_count"] == 15
    assert noleak["raw_market_blob_commits_added"] == 0
    assert noleak["broker_account_order_history_deal_position_sources_consumed"] == 0
    assert completion["completion_standard_satisfied"] is True
    assert completion["missing_incomplete_or_weak_requirements"] == []
    assert manifest["raw_market_blob_commits_added"] == 0
    prompt = builder.PROMPT_ROOT / builder.NEXT_G12_PROMPT_NAME
    starter = builder.ROUTE_DIR / builder.NEXT_G12_STARTER_NAME
    assert prompt.exists()
    assert starter.exists()
    starter_text = starter.read_text(encoding="utf-8")
    assert "\n\n" not in starter_text
    for token in ("NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"):
        assert token in starter_text


def test_verifier_accepts_current_contract_packet() -> None:
    verifier = _load_module(VERIFIER_PATH, "orderflow_proxy_contract_verifier")
    result = verifier.verify()

    assert result["ok"], result["failures"]
    assert result["can_mark_goal_complete"] is True
    assert result["proxy_card_count"] == 8
    assert result["proxy_field_requirement_count"] == 64
    assert result["proxy_requirement_surface_count"] == 72
    assert result["source_family_contract_count"] == 4
    assert result["equivalence_row_count"] == 7
    assert result["broker_native_cfd_truth_claims"] == 0
