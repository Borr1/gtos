import json
from pathlib import Path


ROUTE = Path("research/operations/final_moonshot_market_expansion_observed_session_fillability_repair_2026_06_18")
EXPECTED_DECISION = "MARKET_EXPANSION_OBSERVED_SESSION_FILLABILITY_PROXY_REPAIRED_DEFAULT_OFF_NOT_LIVE_AUTHORITY"


def _load(name):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def _jsonl(name):
    return [json.loads(line) for line in (ROUTE / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_observed_session_fillability_boundary_and_counts():
    result = _load("OBSERVED_SESSION_FILLABILITY_REPAIR_RESULT.json")
    verifier = _load("OBSERVED_SESSION_FILLABILITY_REPAIR_VERIFIER_RESULT.json")
    completion = _load("COMPLETION_AUDIT.json")
    saturation = _load("SATURATION_SELF_RED_TEAM_AUDIT.json")
    session_rows = _jsonl("OBSERVED_SESSION_CALENDAR_LEDGER.jsonl")
    fill_rows = _jsonl("SOURCE_EVENT_FILLABILITY_PROXY_LEDGER.jsonl")
    manifest = _jsonl("SOURCE_MANIFEST_LEDGER.jsonl")

    assert result["ok"] is True
    assert verifier["ok"] is True
    assert completion["ok"] is True
    assert saturation["ok"] is True
    assert result["decision"] == EXPECTED_DECISION
    assert result["live_authority"] is False
    assert result["deployment_ready"] is False
    assert result["promotion_ready"] is False
    assert result["config_patch_applied"] is False
    assert result["runtime_effect"] == "none_observed_session_fillability_proxy_only"
    assert len(session_rows) == 14
    assert len(fill_rows) == 2596
    assert len(manifest) == 28
    assert all(row["present"] is True for row in manifest)


def test_observed_session_fillability_proxy_preserves_gaps():
    result = _load("OBSERVED_SESSION_FILLABILITY_REPAIR_RESULT.json")
    summary = _load("SOURCE_EVENT_FILLABILITY_PROXY_SUMMARY.json")
    requirements = _jsonl("UNRESOLVED_REQUIREMENT_LEDGER.jsonl")
    session_rows = _jsonl("OBSERVED_SESSION_CALENDAR_LEDGER.jsonl")
    fill_rows = _jsonl("SOURCE_EVENT_FILLABILITY_PROXY_LEDGER.jsonl")
    forbidden = _load("FORBIDDEN_CALL_SCAN.json")

    assert summary["event_count"] == 2596
    assert result["m1_computable_event_count"] == summary["m1_computable_event_count"]
    assert result["m1_computable_event_count"] > 0
    assert result["m1_not_computable_event_count"] > 0
    assert result["fillable_proxy_event_count"] > 0
    assert all(row["explicit_session_table_closed"] is False for row in session_rows)
    assert all(row["live_authority_ready"] is False for row in fill_rows)
    assert {row["requirement_id"] for row in requirements} == {
        "MX-FILLABILITY-REQ-001",
        "MX-FILLABILITY-REQ-002",
        "MX-FILLABILITY-REQ-003",
    }
    assert forbidden["ok"] is True
    assert forbidden["matches"] == []
