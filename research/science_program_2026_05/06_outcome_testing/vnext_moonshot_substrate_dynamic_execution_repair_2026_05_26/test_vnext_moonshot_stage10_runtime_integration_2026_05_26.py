from __future__ import annotations

import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-26"
INTEGRATION_MAP = ROUTE_DIR / f"VNEXT_MOONSHOT_RUNTIME_INTEGRATION_MAP_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE10_VERIFICATION_RESULT_{DATE}.json"
ISSUE_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE10_ACTIVE_ISSUE_RESOLUTION_LEDGER_{DATE}.jsonl"
CONDITION_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_RUNTIME_ROUTER_CONDITION_LEDGER_{DATE}.jsonl"


def _jsonl_rows(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def test_stage10_runtime_integration_map_selects_default_off_replacement() -> None:
    integration = json.loads(INTEGRATION_MAP.read_text(encoding="utf-8"))

    candidate = integration["selected_default_off_production_candidate"]
    activation = integration["default_off_activation"]
    summary = integration["router_replay_summary"]

    assert candidate["default_policy"] == "be_after_trigger"
    assert candidate["replaces"] == "live_current_j46_j49"
    assert activation["enabled_value_in_config"] is False
    assert activation["apply_to_execution_value_in_config"] is False
    assert summary["input_rows"] == integration["row_level_evidence"]["router_replay_rows"]
    assert summary["selected_vs_live_delta_r"] > 0
    assert summary["selected_vs_fixed_delta_r"] > 0


def test_stage10_issue_ledger_records_actions_not_caveats() -> None:
    rows = _jsonl_rows(ISSUE_LEDGER)
    issue_ids = {row["issue_id"] for row in rows}

    assert "live_current_j46_j49_underperforms_simpler_and_dynamic_baselines" in issue_ids
    assert "source_null_proxy_and_same_bar_weakness" in issue_ids
    for row in rows:
        assert row["action_taken"]
        assert row["replay_result"]
        assert "known_issue" not in row["terminal_classification"]
        assert "caveat" not in row["terminal_classification"]


def test_stage10_condition_ledger_is_semantic_and_full_row_aligned() -> None:
    integration = json.loads(INTEGRATION_MAP.read_text(encoding="utf-8"))
    rows = _jsonl_rows(CONDITION_LEDGER)
    overall = rows[0]

    assert len(rows) == integration["row_level_evidence"]["condition_rows"]
    assert overall["condition_key"] == ["ALL"]
    assert overall["row_count"] == integration["router_replay_summary"]["input_rows"]
    assert overall["selected_policy_expectancy_r"] > overall["live_current_expectancy_r"]
    assert overall["selected_policy_expectancy_r"] > overall["fixed_1_5r_expectancy_r"]


def test_stage10_verifier_result_is_green_and_stage11_next() -> None:
    result = json.loads(VERIFY_RESULT.read_text(encoding="utf-8"))

    assert result["ok"] is True
    assert result["runtime_effect_rows"] == 0
    assert result["candidate_allowed_rows"] == 0
    assert result["first_incomplete_invariant"] == "STAGE_11_SEMANTIC_VERIFIER_HARDENING"
