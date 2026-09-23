from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-10"
PREFIX = "G0_NOFILL_SOURCE_RECOVERY_CLOSURE_SYNTHESIS"
BUILDER_PATH = ROUTE_DIR / "build_g0_nofill_source_recovery_closure_and_replay_handoff_synthesis_2026_05_10.py"
VERIFIER_PATH = ROUTE_DIR / "verify_g0_nofill_source_recovery_closure_and_replay_handoff_synthesis_2026_05_10.py"


def _load_json(name: str):
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_source_chain_reconciles_final_counts_and_closes_repair_loop() -> None:
    builder = _load_module(BUILDER_PATH, "g0_recovery_builder_counts")
    chain = _load_json(f"{PREFIX}_SOURCE_CHAIN_RECONCILIATION_LEDGER_{DATE}.json")

    assert chain["terminal_decision"] == builder.TERMINAL_DECISION
    assert len(chain["chain"]) == 11
    assert chain["source_control_repair_required_before_broader_replay"] is False
    assert chain["recovery_detour_closed_for_current_evidence_class"] is True
    for key, value in builder.EXPECTED_COUNTS.items():
        assert chain["reconciled_counts"][key] == value


def test_final_source_status_closes_owner_ticks_as_non_blocking() -> None:
    status = _load_json(f"{PREFIX}_FINAL_SOURCE_STATUS_CLOSURE_LEDGER_{DATE}.json")
    rows = {row["status_family"]: row for row in status["status_rows"]}

    assert status["owner_tick_0020_0021_closed_as_current_blocker"] is True
    assert status["owner_tick_0020_0021_future_mt5_native_need_only"] is True
    fallback = rows["exact_mt5_native_bid_ask_flags_fallback_requests"]
    assert fallback["can_block_broader_replay"] is False
    assert fallback["owner_request_ids"] == ["OWNER-TICK-0020", "OWNER-TICK-0021"]
    scid = rows["same_market_sierra_scid_context_evidence"]
    assert scid["final_status"] == "ACCEPTED_CONTEXT_ONLY_NOT_MT5_TICK_RECOVERY"
    assert "MT5 bid quote" in scid["not_eligible_for"]


def test_two_date_closure_preserves_field_blockers_and_exclusions() -> None:
    memo = _load_json(f"{PREFIX}_TWO_DATE_CLOSURE_MEMO_{DATE}.json")

    assert memo["owner_tick_requests"]["OWNER-TICK-0020"]["current_blocker_status"] == "NON_BLOCKING_CLOSED_FOR_CURRENT_SOURCE_CONTROL_CHAIN"
    assert memo["owner_tick_requests"]["OWNER-TICK-0021"]["future_condition_to_reopen"] == "only if a future route explicitly needs MT5-native bid, ask, or flags"
    assert memo["mt5_field_blockers"]["hard_absent_fields"] == ["bid", "ask", "flags"]
    assert memo["mt5_field_blockers"]["substitution_check"]["scid_ohlc_substituted_for_mt5_bid_or_ask"] is False
    assert len(memo["scid_context_evidence"]["candidate_windows"]) == 3
    assert sum(1 for row in memo["scid_context_evidence"]["candidate_windows"] if row["contamination_or_embargo_excluded"]) == 2


def test_next_route_ranking_selects_broad_no_api_replay() -> None:
    builder = _load_module(BUILDER_PATH, "g0_recovery_builder_ranking")
    readiness = _load_json(f"{PREFIX}_REPLAY_SOURCE_EXPANSION_READINESS_SYNTHESIS_{DATE}.json")
    ranking = _load_json(f"{PREFIX}_NEXT_ROUTE_RANKING_LEDGER_{DATE}.json")

    assert readiness["source_control_repair_required_before_broader_replay"] is False
    assert readiness["selected_next_route_id"] == builder.NEXT_ROUTE_ID
    assert ranking["real_unrepaired_source_control_defect_remains"] is False
    assert len(ranking["ranked_routes"]) >= 3
    assert ranking["ranked_routes"][0]["route_id"] == builder.NEXT_ROUTE_ID
    assert ranking["ranked_routes"][0]["selected"] is True


def test_prompt_and_one_line_starter_are_bound_to_selected_route() -> None:
    builder = _load_module(BUILDER_PATH, "g0_recovery_builder_prompt")
    starter = _load_json(f"{PREFIX}_ONE_LINE_STARTER_{DATE}.json")["one_line_starter"]
    prompt = builder.NEXT_PROMPT_PATH.read_text(encoding="utf-8")

    assert "\n" not in starter
    for token in (
        builder.NEXT_ROUTE_ID,
        "NO_PROMOTION_VERDICT",
        "validation_safe=false",
        "outcome_review_opened=false",
        "live_effect=false",
    ):
        assert token in starter
        assert token in prompt
    assert "Do not invent historical pending intent" in prompt
    assert "OWNER-TICK-0020" in prompt
    assert "OWNER-TICK-0021" in prompt


def test_completion_audit_and_noleak_flags_are_exact() -> None:
    completion = _load_json(f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json")
    noleak = _load_json(f"{PREFIX}_NOLEAK_SAFETY_BOUNDARY_AUDIT_{DATE}.json")

    assert completion["can_mark_goal_complete"] is True
    assert completion["completion_standard_satisfied"] is True
    assert completion["missing_incomplete_or_weak_requirements"] == []
    assert completion["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert completion["validation_safe"] is False
    assert completion["outcome_review_opened"] is False
    assert completion["live_effect"] is False
    assert set(noleak["forbidden_surface_results"].values()) == {"NOT_OPENED"}


def test_verifier_accepts_current_route_package() -> None:
    verifier = _load_module(VERIFIER_PATH, "g0_recovery_verifier")
    result = verifier.verify()

    assert result["ok"] is True
    assert result["can_mark_goal_complete"] is True
    assert result["terminal_decision"] == "ACCEPT_SOURCE_RECOVERY_DETOUR_CLOSED_ROUTE_TO_BROAD_NO_API_REPLAY"
    assert result["selected_next_route_id"] == "NO_API_HISTORICAL_REPLAY_ENGINE_AND_MISSED_OPPORTUNITY_INVENTORY"
    assert result["owner_tick_0020_0021_closed_as_current_blocker"] is True
    assert result["source_control_repair_required_before_broader_replay"] is False
