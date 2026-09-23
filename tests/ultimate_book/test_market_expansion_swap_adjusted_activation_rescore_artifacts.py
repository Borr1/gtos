import json
from pathlib import Path


ROUTE = Path("research/operations/final_moonshot_market_expansion_swap_adjusted_activation_rescore_2026_06_18")
EXPECTED_DECISION = "MARKET_EXPANSION_SWAP_ADJUSTED_RESCORING_POSITIVE_DEFAULT_OFF_NOT_LIVE_AUTHORITY"


def _load(name):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def _jsonl(name):
    return [json.loads(line) for line in (ROUTE / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_swap_adjusted_activation_boundary_and_counts():
    result = _load("SWAP_ADJUSTED_ACTIVATION_RESCORE_RESULT.json")
    verifier = _load("SWAP_ADJUSTED_ACTIVATION_RESCORE_VERIFIER_RESULT.json")
    metadata = _load("SWAP_ADJUSTED_PORTFOLIO_REPLAY_METADATA.json")
    completion = _load("COMPLETION_AUDIT.json")
    saturation = _load("SATURATION_SELF_RED_TEAM_AUDIT.json")
    replay_rows = _jsonl("SWAP_ADJUSTED_PORTFOLIO_REPLAY_LEDGER.jsonl")
    daily_rows = _jsonl("SWAP_ADJUSTED_DAILY_REPLAY_LEDGER.jsonl")
    contribution_rows = _jsonl("CANDIDATE_SWAP_ADJUSTED_CONTRIBUTION_LEDGER.jsonl")

    assert result["ok"] is True
    assert verifier["ok"] is True
    assert completion["ok"] is True
    assert saturation["ok"] is True
    assert result["decision"] == EXPECTED_DECISION
    assert result["live_authority"] is False
    assert result["deployment_ready"] is False
    assert result["promotion_ready"] is False
    assert result["config_patch_applied"] is False
    assert result["runtime_effect"] == "none_swap_adjusted_rescore_only"
    assert result["source_event_count"] == 2596
    assert len(replay_rows) == 8
    assert len(daily_rows) == metadata["all_days_count"] == 1679
    assert len(contribution_rows) == 14


def test_swap_adjusted_activation_positive_but_not_overstated():
    result = _load("SWAP_ADJUSTED_ACTIVATION_RESCORE_RESULT.json")
    delta = _load("SWAP_ADJUSTED_ACTIVATION_DELTA_SUMMARY.json")
    requirements = _jsonl("UNRESOLVED_REQUIREMENT_LEDGER.jsonl")
    contribution_rows = _jsonl("CANDIDATE_SWAP_ADJUSTED_CONTRIBUTION_LEDGER.jsonl")
    forbidden = _load("FORBIDDEN_CALL_SCAN.json")

    assert delta["candidate_reference"]["monthly_pct"] == 4.969
    assert delta["before_swap_seed"]["monthly_pct"] == 5.003
    assert delta["after_swap_seed"]["monthly_pct"] == 4.991
    assert delta["after_swap_seed_delta_vs_candidate"]["monthly_pct"] == result["after_swap_seed_delta_monthly_pct"]
    assert delta["after_swap_seed_delta_vs_candidate"]["monthly_pct"] > 0
    assert delta["swap_drag_delta_vs_before_seed"]["monthly_pct"] < 0
    assert result["after_swap_seed_delta_sharpe"] > 0
    assert all(row["live_authority_ready"] is False for row in contribution_rows)
    assert any(row["seed_weight_0p025_swap_drag_delta_R"] < 0 for row in contribution_rows)
    assert {row["requirement_id"] for row in requirements} == {
        "MX-SWAP-ADJ-REQ-001",
        "MX-SWAP-ADJ-REQ-002",
        "MX-SWAP-ADJ-REQ-003",
    }
    assert forbidden["ok"] is True
    assert forbidden["matches"] == []
