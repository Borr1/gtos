import json
from collections import Counter
from pathlib import Path

from src.research_infra.branch_entry_adverse_redesign_router import (
    classify_entry_adverse_redesign,
    summarize_entry_adverse,
)
from src.research_infra.branch_m15_interval_router import classify_m15_interval, summarize_m15_interval
from src.research_infra.branch_m1_conflict_router import classify_m1_conflict, summarize_m1_conflict
from src.research_infra.branch_positive_challenger_router import (
    classify_positive_replay,
    summarize_positive_replay,
)
from src.research_infra.branch_source_router import classify_source_router, summarize_source_router


REPO = Path(__file__).resolve().parents[2]
ROUTE_DIR = (
    REPO
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "weekend_mechanical_edge_factory_moonshot_2026_05_15"
)


def _jsonl(name: str) -> list[dict]:
    path = ROUTE_DIR / name
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _by_branch(rows: list[dict]) -> dict[str, dict]:
    return {row["branch_queue_id"]: row for row in rows}


def test_source_router_matches_followup_packet_distribution():
    export_rows = _jsonl("HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_SOURCE_ROUTER_LEDGER_2026-05-16.jsonl")
    followup_rows = _by_branch(_jsonl("HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_SOURCE_ROUTER_LEDGER_2026-05-16.jsonl"))

    for row in export_rows:
        classified = classify_source_router(row)
        followup = followup_rows[row["branch_queue_id"]]
        assert classified["source_router_followup_class"] == followup["source_router_followup_class"]
        assert classified["source_stress_interval_sign_class"] == followup["source_stress_interval_sign_class"]

    summary = summarize_source_router(export_rows)
    assert summary["source_export_class"] == {
        "SOURCE_ROUTER_NEGATIVE_AVOID_OR_ACQUIRE_EXACT_SOURCE": 31,
        "SOURCE_ROUTER_POSITIVE_LOW_SPREAD_BUT_HIGH_SPREAD_FLIP": 87,
        "SOURCE_ROUTER_STRADDLE_BOUNDS_ACQUIRE_OR_COST_SPLIT": 20,
    }
    assert summary["source_router_followup_class"] == {
        "SOURCE_CONSERVATIVE_NEGATIVE_AVOID_OR_ACQUIRE_EXACT_SOURCE": 31,
        "SOURCE_COST_SENSITIVE_RISK_ROUTER_ACQUIRE_EXACT_OR_CAP_COST_MODEL": 87,
        "SOURCE_STRADDLE_BOUNDS_ACQUIRE_EXACT_OR_SPLIT_COST_MODEL": 20,
    }


def test_m15_interval_router_matches_followup_packet_distribution():
    export_rows = _jsonl("HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_M15_INTERVAL_LEDGER_2026-05-16.jsonl")
    followup_rows = _by_branch(_jsonl("HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_M15_LEDGER_2026-05-16.jsonl"))

    for row in export_rows:
        classified = classify_m15_interval(row)
        followup = followup_rows[row["branch_queue_id"]]
        assert classified["m15_followup_class"] == followup["m15_followup_class"]
        assert classified["m15_interval_sign_class"] == followup["m15_interval_sign_class"]
        assert followup["exact_chronology_claim"] is False
        assert followup["proxy_variant_count"] == 4

    summary = summarize_m15_interval(export_rows)
    assert summary["m15_export_class"] == {
        "M15_EXPORT_INTERVAL_BOUNDS_ROUTER": 37,
        "M15_EXPORT_STOP_FIRST_AVOID_OR_REDESIGN": 58,
        "M15_EXPORT_TARGET_FIRST_CHALLENGER": 91,
    }


def test_m1_conflict_router_matches_followup_packet_distribution():
    export_rows = _jsonl("HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_M1_CONFLICT_LEDGER_2026-05-16.jsonl")
    followup_rows = _by_branch(_jsonl("HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_M1_LEDGER_2026-05-16.jsonl"))

    for row in export_rows:
        classified = classify_m1_conflict(row)
        followup = followup_rows[row["branch_queue_id"]]
        assert classified["m1_followup_class"] == followup["m1_followup_class"]
        assert classified["m1_branch_midpoint_sign_class"] == followup["m1_branch_midpoint_sign_class"]
        assert classified["m1_support_midpoint_sign_class"] == followup["m1_support_midpoint_sign_class"]
        assert followup["exact_chronology_claim"] is False
        assert followup["tick_ordering_exact"] is False
        assert followup["proxy_variant_count"] == 6

    summary = summarize_m1_conflict(export_rows)
    assert summary["m1_export_class"] == {
        "M1_EXPORT_SUPPORT_AND_BRANCH_TARGET_STABLE": 70,
        "M1_EXPORT_SUPPORT_POSITIVE_BRANCH_CONFLICT_SPLIT": 40,
    }


def test_positive_challenger_router_preserves_repair_first_scope():
    export_rows = _jsonl("HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_POSITIVE_REPLAY_LEDGER_2026-05-16.jsonl")
    followup_rows = _by_branch(_jsonl("HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_POSITIVE_LEDGER_2026-05-16.jsonl"))

    for row in export_rows:
        classified = classify_positive_replay(row)
        followup = followup_rows[row["branch_queue_id"]]
        assert classified["positive_followup_class"] == followup["positive_followup_class"]
        assert classified["positive_interval_sign_class"] == followup["positive_interval_sign_class"]
        assert classified["positive_modifier_class"] == followup["positive_modifier_class"]

    summary = summarize_positive_replay(export_rows)
    assert summary["positive_export_class"] == {
        "POSITIVE_EXPORT_REPLAYABLE_CONSERVATIVE_POSITIVE": 156,
        "POSITIVE_EXPORT_SOURCE_REPAIR_OR_STRESS_FIRST": 87,
    }
    repair_first_rows = [
        row for row in followup_rows.values() if row["positive_followup_class"] == "POSITIVE_SOURCE_REPAIR_OR_STRESS_FIRST_BEFORE_REPLAY"
    ]
    assert len(repair_first_rows) == 87
    assert all(row["positive_replayable_now"] is False for row in repair_first_rows)


def test_entry_adverse_router_preserves_full_branch_scope_and_binding_rows():
    export_rows = _jsonl("HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_ENTRY_ADVERSE_LEDGER_2026-05-16.jsonl")
    followup_rows = _by_branch(_jsonl("HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_ENTRY_ADVERSE_LEDGER_2026-05-16.jsonl"))
    binding_rows = _jsonl("HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_BINDING_PRESERVE_LEDGER_2026-05-16.jsonl")

    assert len(export_rows) == 386
    assert len(followup_rows) == 386
    for row in export_rows:
        classified = classify_entry_adverse_redesign(row)
        followup = followup_rows[row["branch_queue_id"]]
        assert classified["entry_adverse_followup_class"] == followup["entry_adverse_followup_class"]
        assert classified["entry_target_stop_balance_class"] == followup["entry_target_stop_balance_class"]

    summary = summarize_entry_adverse(export_rows)
    assert summary["entry_adverse_export_class"] == {
        "ENTRY_ADVERSE_EXPORT_BOTH_REDESIGN_SCORE": 153,
        "ENTRY_ADVERSE_EXPORT_ENTRY_REDESIGN_SCORE": 151,
        "ENTRY_ADVERSE_EXPORT_NO_REDESIGN_SCOPE_PRESERVE": 82,
    }
    assert len(binding_rows) == 2
    assert {row["target_stop_contract_id"] for row in binding_rows} == {"TARGETSTOP_NA_NA"}
    assert all(row["no_scalar_fill"] is True for row in binding_rows)
    assert Counter(row["mechanical_triage_score_proxy"] for row in binding_rows) == Counter({None: 2})
