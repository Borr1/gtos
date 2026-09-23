import json
from pathlib import Path


ROUTE = Path("research/operations/final_moonshot_market_expansion_conditioned_sizing_refinement_2026_06_18")
EXPECTED_DECISION = "MARKET_EXPANSION_CONDITIONED_SIZING_REFINEMENT_BUILT_DEFAULT_OFF_NOT_LIVE_AUTHORITY"


def _load(name):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def _jsonl(name):
    return [json.loads(line) for line in (ROUTE / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_conditioned_sizing_boundary_and_counts():
    result = _load("CONDITIONED_SIZING_REFINEMENT_RESULT.json")
    verifier = _load("CONDITIONED_SIZING_REFINEMENT_VERIFIER_RESULT.json")
    metadata = _load("CONDITIONED_POLICY_REPLAY_METADATA.json")
    completion = _load("COMPLETION_AUDIT.json")
    saturation = _load("SATURATION_SELF_RED_TEAM_AUDIT.json")
    dispositions = _jsonl("CANDIDATE_CONDITIONED_DISPOSITION_LEDGER.jsonl")
    replay_rows = _jsonl("CONDITIONED_POLICY_REPLAY_LEDGER.jsonl")
    daily_rows = _jsonl("CONDITIONED_DAILY_REPLAY_LEDGER.jsonl")

    assert result["ok"] is True
    assert verifier["ok"] is True
    assert completion["ok"] is True
    assert saturation["ok"] is True
    assert result["decision"] == EXPECTED_DECISION
    assert result["live_authority"] is False
    assert result["deployment_ready"] is False
    assert result["promotion_ready"] is False
    assert result["config_patch_applied"] is False
    assert result["runtime_effect"] == "none_conditioned_sizing_refinement_only"
    assert len(dispositions) == 14
    assert len(replay_rows) == 26
    assert len(daily_rows) == metadata["all_days_count"] == 1679


def test_conditioned_sizing_improves_but_remains_default_off():
    result = _load("CONDITIONED_SIZING_REFINEMENT_RESULT.json")
    summary = _load("CONDITIONED_POLICY_SUMMARY.json")
    requirements = _jsonl("UNRESOLVED_REQUIREMENT_LEDGER.jsonl")
    dispositions = _jsonl("CANDIDATE_CONDITIONED_DISPOSITION_LEDGER.jsonl")
    forbidden = _load("FORBIDDEN_CALL_SCAN.json")

    assert summary["policy_tag_counts"] == {
        "all14_swap_adjusted": 14,
        "positive_weighted12_after_swap": 12,
        "robust6_every_split_positive": 6,
    }
    assert summary["best_monthly"]["monthly_pct"] > summary["candidate_reference"]["monthly_pct"]
    assert summary["best_sharpe"]["sharpe"] > summary["candidate_reference"]["sharpe"]
    assert summary["best_drawdown"]["maxDD_R"] < summary["candidate_reference"]["maxDD_R"]
    assert result["best_monthly_policy"]["monthly_pct"] == summary["best_monthly"]["monthly_pct"]
    assert all(row["live_authority_ready"] is False for row in dispositions)
    assert any(row["conditioned_disposition"] == "refined_default_off_core_candidate" for row in dispositions)
    assert any(row["conditioned_disposition"] == "preserve_as_feature_veto_or_redesign_input_not_sleeve_now" for row in dispositions)
    assert {row["requirement_id"] for row in requirements} == {
        "MX-COND-REQ-001",
        "MX-COND-REQ-002",
        "MX-COND-REQ-003",
    }
    assert forbidden["ok"] is True
    assert forbidden["matches"] == []
