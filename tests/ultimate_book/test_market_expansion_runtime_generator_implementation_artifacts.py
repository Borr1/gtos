import json
from pathlib import Path


ROUTE = Path("research/operations/final_moonshot_market_expansion_runtime_generator_implementation_2026_06_18")


def _load(name: str):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def _jsonl(name: str):
    return [json.loads(line) for line in (ROUTE / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_runtime_generator_implementation_counts_and_boundaries():
    result = _load("MARKET_EXPANSION_RUNTIME_GENERATOR_IMPLEMENTATION_RESULT.json")
    verifier = _load("MARKET_EXPANSION_RUNTIME_GENERATOR_IMPLEMENTATION_VERIFIER_RESULT.json")
    completion = _load("COMPLETION_AUDIT.json")
    saturation = _load("SATURATION_AUDIT.json")
    timing = _load("D1_NEXT_OPEN_TIMING_CONTRACT_PROOF.json")
    zero = _load("ZERO_ACTIVE_BEHAVIOR_AUDIT.json")
    replay = _load("FULL_GENERATOR_BOOK_REPLAY_PROOF.json")
    broker = _load("BROKER_SESSION_SPEC_CAPTURE_MANIFEST.json")
    parity = _jsonl("RUNTIME_GENERATOR_PARITY_LEDGER.jsonl")

    assert result["ok"] is True
    assert verifier["ok"] is True
    assert result["decision"] == "MARKET_EXPANSION_RUNTIME_GENERATOR_IMPLEMENTED_DEFAULT_OFF_NOT_LIVE_AUTHORITY"
    assert result["selectable_activation_candidate_count"] == len(parity) == 14
    assert result["runtime_generator_implemented_count"] == 14
    assert result["runtime_generator_not_implemented_count"] == 0
    assert result["runtime_generator_parity_pass_count"] == 14
    assert result["runtime_generator_parity_fail_count"] == 0
    assert result["total_recomputed_source_events"] == result["total_runtime_events"] == result["total_matched_events"]
    assert replay["generator_book_signal_replay_complete"] is True
    assert timing["runtime_now_preferred"] is True
    assert timing["all_runtime_decision_days_match_source_entry_dates"] is True
    assert timing["weekend_or_holiday_skip_sample_count"] > 0
    assert zero["zero_active_behavior_ok"] is True
    assert zero["activation_weight_sum"] == 0.0
    assert broker["account_info_read"] is False
    assert broker["symbol_select_called"] is False
    assert broker["broker_or_order_mutation"] is False
    assert broker["orderflow_used"] is False
    assert completion["runtime_effect_boundary"] == "none_default_off_code_path_only"
    assert completion["forbidden_surfaces_touched"] == []
    assert saturation["no_arbitrary_top_n"] is True
    assert result["deployment_ready"] is False
    assert result["live_authority"] is False
    assert result["activation_weight_now"] == 0.0


def test_runtime_generator_implementation_event_parity_and_execution_packets():
    parity = _jsonl("RUNTIME_GENERATOR_PARITY_LEDGER.jsonl")
    details = _jsonl("RUNTIME_GENERATOR_EVENT_PARITY_DETAIL.jsonl")
    execution = _load("EXECUTION_PACKET_DRY_RUN_PROOF.json")
    zero = _load("ZERO_ACTIVE_BEHAVIOR_AUDIT.json")

    assert {row["all_parity_passed"] for row in parity} == {True}
    assert sum(row["recomputed_source_event_count"] for row in parity) == len(details)
    assert {row["status"] for row in details} == {"matched"}
    for row in parity:
        assert row["recomputed_source_event_count"] == row["runtime_event_count"] == row["matched_event_count"]
        assert row["missing_event_count"] == 0
        assert row["extra_event_count"] == 0
        assert row["direction_mismatch_count"] == 0
        assert row["decision_day_mismatch_count"] == 0
        assert row["risk_mismatch_count"] == 0
        assert row["target_mismatch_count"] == 0

    assert execution["row_count"] == 14
    assert execution["target2_packet_ok_count"] == 14
    assert execution["all_target2_packets_ok"] is True
    assert execution["exit_profile_tags_match_selectable"] is True
    assert zero["market_expansion_names_in_candidate_built"] == []
    assert zero["market_expansion_names_in_candidate_book_specs"] == []
    assert zero["market_expansion_names_in_empty_allowlist_specs"] == []
