from __future__ import annotations

import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"


def load_jsonl(name: str) -> list[dict]:
    path = ROUTE_DIR / name
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_stage08_summary_advances_to_stage09_without_paid_calls() -> None:
    summary = json.loads(
        (ROUTE_DIR / f"VNEXT_MOONSHOT_AI_ROLE_BUDGET_SUMMARY_{DATE_ID}.json").read_text(encoding="utf-8")
    )
    state = json.loads(
        (ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json").read_text(encoding="utf-8")
    )
    assert summary["paid_api_or_vendor_calls_made"] == 0
    assert summary["packet_outcome_hidden"] is True
    assert summary["production_ai_api_distinct_from_monitoring_agent"] is True
    assert summary["manifest_rows"] > 0
    assert summary["mandatory_strata_covered"] == len(summary["mandatory_strata"])
    assert state["first_incomplete_invariant"] == "STAGE_09_ML_AND_SURROGATE_FEASIBILITY"


def test_stage08_role_ledger_keeps_ai_but_rejects_removal() -> None:
    rows = load_jsonl(f"VNEXT_MOONSHOT_AI_ROLE_DECISION_LEDGER_{DATE_ID}.jsonl")
    by_role = {row["role"]: row for row in rows}
    assert by_role["production_decision_gate"]["decision"] == "retain_pending_budgeted_ai_delta_validation"
    assert by_role["validator"]["decision"] == "recommended_primary_stage08_paid_validation_role"
    assert by_role["removable_component"]["decision"] == "rejected_for_now"
    assert by_role["malformed_response_repairer"]["monitoring_agent_role"] is True
    assert by_role["malformed_response_repairer"]["production_api_role"] is False


def test_stage08_manifest_is_outcome_hidden_and_cache_keyed() -> None:
    rows = load_jsonl(f"VNEXT_MOONSHOT_AI_VALIDATION_BUDGET_MANIFEST_{DATE_ID}.jsonl")
    assert rows
    forbidden = {
        "legacy_final_r",
        "live_current_j46_j49_final_r",
        "be_after_trigger_final_r",
        "trailing_runner_final_r",
        "mfe_r",
        "mae_r",
        "terminal_outcome",
        "pending_lifecycle_state",
    }
    for row in rows:
        assert row["outcome_hidden_from_ai_packet"] is True
        assert row["cache_key_sha256"]
        assert not (forbidden & set(row["packet_payload"].keys()))
        assert row["offline_scoring_label_sha256"]
    strata = {row["validation_stratum"] for row in rows}
    assert "nofill_pending_lifecycle" in strata
    assert "prop_near_boundary_ev_stream" in strata


def test_stage08_packet_spec_names_forbidden_fields_and_malformed_handling() -> None:
    text = (ROUTE_DIR / f"VNEXT_MOONSHOT_AI_PROMPT_PACKET_SPEC_{DATE_ID}.md").read_text(encoding="utf-8")
    assert "Forbidden Packet Fields" in text
    assert "Malformed Handling" in text
    assert "Cache Key" in text
