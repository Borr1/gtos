import json
from pathlib import Path


ROUTE = Path("research/operations/final_moonshot_market_expansion_validation_scoring_2026_06_18")


def _load(name: str):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def _jsonl(name: str):
    path = ROUTE / name
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_market_expansion_scoring_denominator_and_boundaries():
    result = _load("MARKET_EXPANSION_VALIDATION_SCORING_RESULT.json")
    verification = _load("MARKET_EXPANSION_VALIDATION_SCORING_VERIFIER_RESULT.json")
    completion = _load("COMPLETION_AUDIT.json")
    concentration = _load("CONCENTRATION_STRESS_AUDIT.json")
    raw_manifest = _load("RAW_EVENT_EXPORT_MANIFEST.json")
    eligibility_rows = _jsonl("SYMBOL_TIMEFRAME_ELIGIBILITY_LEDGER.jsonl")

    assert result["ok"] is True
    assert verification["ok"] is True
    assert result["availability_coverage_gap_count"] == 0
    assert result["priority_symbol_count"] == 167
    assert result["scoring_eligible_symbol_count"] == 164
    assert result["scoring_excluded_symbol_count"] == 3
    assert result["scored_symbol_count"] == 164
    assert result["event_count"] > 100_000
    assert raw_manifest["row_count"] == result["event_count"]
    assert raw_manifest["path"].startswith("data/mt5_research_exports/")
    assert len(raw_manifest["sha256"]) == 64
    assert result["candidate_result_count"] == 820
    assert result["first_pass_promoted_for_followup_count"] == 33
    assert result["orderflow_used"] is False
    assert result["broker_or_order_mutation"] is False
    assert result["config_or_live_activation_changed"] is False
    assert result["vps_process_touched"] is False
    assert result["live_authority"] is False
    assert completion["runtime_effect"] == "none_research_scoring_only"
    assert concentration["hard_drops_not_scored"] is True
    assert concentration["spcx_quarantine_not_scored"] is True

    excluded = {row["file_symbol"]: row for row in eligibility_rows if not row["scoring_eligible"]}
    assert set(excluded) == {"SPCX", "NATGAS_cash", "HEATOIL_c"}
    assert "spec_status_not_trade_ready" in excluded["SPCX"]["eligibility_exclusion_reasons"]
    assert "hard_dropped_runtime_status" in excluded["NATGAS_cash"]["eligibility_exclusion_reasons"]
    assert "hard_dropped_runtime_status" in excluded["HEATOIL_c"]["eligibility_exclusion_reasons"]


def test_market_expansion_scoring_ledgers_and_promotion_gates():
    result = _load("MARKET_EXPANSION_VALIDATION_SCORING_RESULT.json")
    raw_manifest = _load("RAW_EVENT_EXPORT_MANIFEST.json")
    source_rows = _jsonl("SOURCE_HASH_LEDGER.jsonl")
    event_rows = _jsonl("EVENT_SCORE_LEDGER.jsonl")
    replay_rows = _jsonl("REPLAY_PACKET_LEDGER.jsonl")
    candidate_rows = _jsonl("CANDIDATE_RESULT_LEDGER.jsonl")
    candidate_alias_rows = _jsonl("CANDIDATE_MECHANISM_SCORE_LEDGER.jsonl")
    family_rows = _jsonl("FAMILY_SCORE_LEDGER.jsonl")
    split_rows = _jsonl("SPLIT_STABILITY_LEDGER.jsonl")
    placebo_rows = _jsonl("NULL_PLACEBO_LEDGER.jsonl")
    full_book_rows = _jsonl("FULL_BOOK_MC_INTERACTION_LEDGER.jsonl")
    inspire_rows = _jsonl("INSPIRE_NOT_KILL_LEDGER.jsonl")
    decision_rows = _jsonl("DECISION_LEDGER.jsonl")
    cost_audit = _load("COST_STRESS_AUDIT.json")
    repair = _load("REPAIR_LEDGER.json")
    saturation = _load("SATURATION_AUDIT.json")

    assert raw_manifest["row_count"] == result["event_count"]
    assert len(event_rows) == result["candidate_result_count"]
    assert len(replay_rows) == len(event_rows)
    assert len(candidate_rows) == result["candidate_result_count"]
    assert len(candidate_alias_rows) == len(candidate_rows)
    assert len(family_rows) == result["family_result_count"]
    assert len(split_rows) == len(candidate_rows)
    assert len(placebo_rows) == len(candidate_rows)
    assert any(row["source_used_for_scoring"] for row in source_rows)
    assert all(row["not_killed"] is True for row in inspire_rows)
    assert any(row["decision"] == result["decision"] for row in decision_rows)
    assert repair["ok"] is True
    assert repair["blockers"] == []
    assert saturation["ok"] is True
    assert saturation["no_arbitrary_top_n"] is True
    assert all(row["raw_event_export_sha256"] == raw_manifest["sha256"] for row in event_rows)
    assert cost_audit["ok"] is True
    assert "broker order lifecycle" in " ".join(cost_audit["limitations"])
    assert full_book_rows[0]["status"] == "not_computed_in_this_route"

    excluded_symbols = {"SPCX", "NATGAS_cash", "HEATOIL_c"}
    assert excluded_symbols.isdisjoint({row["file_symbol"] for row in candidate_rows})

    promoted = [row for row in candidate_rows if row["first_pass_promoted_for_followup"]]
    assert len(promoted) == result["first_pass_promoted_for_followup_count"]
    assert promoted
    assert all(row["family"] != "single_stock_cfd" for row in promoted)
    assert all(row["summary"]["populated_split_count"] >= 2 for row in promoted)
    assert all(row["summary"]["every_populated_split_positive"] is True for row in promoted)
    assert all(
        row["placebo"]["placebo_p_ge_observed"] is None
        or row["placebo"]["placebo_p_ge_observed"] <= 0.25
        for row in promoted
    )
    promoted_families = {row["family"] for row in promoted}
    assert {"crypto_alt_or_major", "indices_context", "agri_softs"} <= promoted_families
