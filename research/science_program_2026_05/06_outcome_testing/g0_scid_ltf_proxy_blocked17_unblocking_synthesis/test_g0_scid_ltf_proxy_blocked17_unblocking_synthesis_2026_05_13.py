from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-13"
PREFIX = "G0_SCID_LTF_PROXY_BLOCKED17_SYNTHESIS"
BUILDER_PATH = ROUTE_DIR / "build_g0_scid_ltf_proxy_blocked17_unblocking_synthesis_2026_05_13.py"
VERIFIER_PATH = ROUTE_DIR / "verify_g0_scid_ltf_proxy_blocked17_unblocking_synthesis_2026_05_13.py"


def _load_json(name: str):
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_decision_preserves_denominators_and_source_inventory() -> None:
    builder = _load_module(BUILDER_PATH, "g0_ltf_proxy_builder_decision")
    decision = _load_json(f"{PREFIX}_DECISION_LEDGER_{DATE}.json")
    noleak = _load_json(f"{PREFIX}_DENOMINATOR_NOLEAK_SAFE_FLAG_AUDIT_{DATE}.json")

    assert decision["terminal_decision"] == builder.TERMINAL_DECISION
    assert decision["denominator_counts"]["blocked17_included"] == 17
    assert decision["denominator_counts"]["other_blocked15_excluded"] == 15
    assert decision["denominator_counts"]["ready8_excluded"] == 8
    assert decision["source_inventory_count"] == 13024
    assert noleak["ok"] is True
    assert noleak["included_card_count"] == 17
    assert noleak["excluded_blocked15_card_count"] == 15
    assert noleak["broker_native_cfd_truth_claims"] == 0
    assert noleak["raw_market_blob_commits_added"] == 0


def test_dependency_map_reconciles_all_17_cards_once() -> None:
    dependency = _load_json(f"{PREFIX}_BLOCKED17_DEPENDENCY_TO_ROUTE_MAP_{DATE}.json")

    assert dependency["card_count"] == 17
    assert len(dependency["cards"]) == 17
    card_ids = [row["card_id"] for row in dependency["cards"]]
    assert len(set(card_ids)) == 17
    assert dependency["route_counts"]["SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE"] >= 10
    assert dependency["route_counts"]["SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE"] >= 7
    for row in dependency["cards"]:
        assert row["denominator_inclusion"] == "blocked17_only"
        assert row["may_score_results_now"] is False
        assert row["recommended_route_ids"]
        assert row["future_result_gate"]


def test_route_ranking_is_broad_non_ob_and_prompt_packs_are_runnable() -> None:
    builder = _load_module(BUILDER_PATH, "g0_ltf_proxy_builder_prompts")
    ranking = _load_json(f"{PREFIX}_ROUTE_RANKING_MATRIX_{DATE}.json")
    prompt_pack = _load_json(f"{PREFIX}_PARSER_PROXY_CAPTURE_ACCESS_PROMPT_PACK_LEDGER_{DATE}.json")
    parallel = _load_json(f"{PREFIX}_PARALLELIZATION_LEDGER_{DATE}.json")

    expected_routes = [pack["route_id"] for pack in builder.PROMPT_PACKS]
    assert [row["route_id"] for row in ranking["ranked_routes"]] == expected_routes
    assert prompt_pack["prompt_pack_count"] == 5
    assert len(prompt_pack["rows"]) == 5
    assert parallel["parallelization_decision"] == "FIVE_DISJOINT_SOURCE_CONTROL_ROUTES_CAN_RUN_IN_PARALLEL_AFTER_THIS_G0_SYNTHESIS"
    for row in prompt_pack["rows"]:
        assert (builder.REPO_ROOT / row["prompt_path"]).exists()
        assert (builder.REPO_ROOT / row["starter_path"]).exists()
        assert "NO_PROMOTION_VERDICT" in row["one_line_starter"]
        assert "validation_safe=false" in row["one_line_starter"]
        assert "outcome_review_opened=false" in row["one_line_starter"]
        assert "live_effect=false" in row["one_line_starter"]


def test_source_materialization_saturation_and_completion_are_exact() -> None:
    materialization = _load_json(f"{PREFIX}_SOURCE_MATERIALIZATION_OPPORTUNITY_LEDGER_{DATE}.json")
    saturation = _load_json(f"{PREFIX}_SATURATION_SELF_REDTEAM_{DATE}.json")
    completion = _load_json(f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json")

    assert materialization["source_inventory_count"] == 13024
    assert materialization["source_status_rows_inspected"] == 17
    assert materialization["requirement_rows_inspected"] == 8
    assert materialization["proxy_equivalence_rows_inspected"] == 7
    assert len(materialization["opportunities"]) == 5
    assert len(saturation["anti_boxing_routes_considered"]) == 5
    assert len(saturation["saturation_questions"]) >= 7
    assert completion["completion_standard_satisfied"] is True
    assert completion["missing_incomplete_or_weak_requirements"] == []


def test_verifier_accepts_current_route_package() -> None:
    verifier = _load_module(VERIFIER_PATH, "g0_ltf_proxy_verifier")
    result = verifier.verify()

    assert result["ok"] is True
    assert result["can_mark_goal_complete"] is True
    assert result["terminal_decision"] == "ACCEPT_AS_G0_SOURCE_CONTROL_UNBLOCKING_ROUTE_BUNDLE_FOR_BLOCKED17"
    assert result["card_count"] == 17
    assert result["source_inventory_count"] == 13024
    assert result["ranked_route_count"] == 5
    assert result["prompt_pack_count"] == 5
