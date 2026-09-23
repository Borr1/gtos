from __future__ import annotations

import json
from pathlib import Path

from scripts import build_science_goal_program as script
from src.research_infra import science_goal_program as mod


def test_payload_defines_expected_lanes_and_orchestration():
    payload = mod.build_payload(generated_at_utc="2026-05-06T00:00:00+00:00")
    lanes = {lane["lane_id"]: lane for lane in payload["lanes"]}

    assert payload["status"] == mod.STATUS_READY
    assert payload["result_boundary"] == mod.RESULT_BOUNDARY
    assert payload["lane_count"] == 13
    assert payload["science_lane_count"] == 11
    assert set(lanes) == {f"G{i}" for i in range(13)}
    assert lanes["G0"]["role"] == "coordinator"
    assert lanes["G12"]["role"] == "red_team"
    assert payload["orchestration_plan"]["max_parallel_lanes"] == 8
    assert payload["first_wave_priority"] == "primitive_sciences_not_missed_move_only_or_market_expansion_only"
    assert payload["no_live_trading_behavior_change"] is True
    assert payload["ai_calls"] == 0
    assert payload["mt5_calls"] == 0
    assert payload["paid_data_calls"] == 0


def test_schema_contracts_include_required_interfaces():
    payload = mod.build_payload(generated_at_utc="2026-05-06T00:00:00+00:00")
    schemas = payload["schema_contracts"]

    assert set(schemas) == {
        "science_mechanism_v1",
        "science_hypothesis_v1",
        "experiment_prereg_v1",
        "source_contract_v2",
        "goal_status_v1",
    }
    for schema_name, fields in mod.SCHEMA_REQUIRED_FIELDS.items():
        assert schemas[schema_name]["required_fields"] == fields
        assert schemas[schema_name]["result_boundary"] == mod.RESULT_BOUNDARY


def test_schema_row_validation_blocks_live_change_and_bad_source_state():
    source_row = {
        "source_id": "paid_gex",
        "url_or_vendor": "licensed vendor",
        "access_legal_state": "PAID_OR_LICENSE_REQUIRED_SEPARATE_OWNER_APPROVAL",
        "cost_rule": "PAID_SOURCE_BLOCKED_SEPARATE_OWNER_APPROVAL_REQUIRED",
        "publication_asof_timestamp_rule": "provider as-of timestamp required",
        "cache_path": "research/science_program_2026_05/raw/paid_gex/",
        "allowed_feature_role": "FORWARD_CONTEXT_ONLY",
        "source_use_state": "READY_FOR_VALIDATION_USE",
        "source_use_blockers": ["OWNER_APPROVAL_MISSING"],
        "result_boundary": mod.RESULT_BOUNDARY,
    }

    issues = mod.validate_schema_row("source_contract_v2", source_row)

    assert "source_contract_v2:SOURCE_USE_READY_WITH_BLOCKERS" in issues
    assert "source_contract_v2:BLOCKED_OR_INCOMPLETE_SOURCE_MARKED_READY_FOR_USE" in issues
    assert "source_contract_v2:PAID_SOURCE_MARKED_READY_WITHOUT_APPROVAL" in issues
    assert "source_contract_v2:NON_VALIDATION_ROLE_MARKED_READY_FOR_USE" in issues


def test_prereg_validation_requires_frozen_closed_outcome_and_label_separation():
    row = {
        "experiment_id": "EXP-TEST",
        "hypothesis_id": "H-TEST",
        "frozen_at_utc": "",
        "outcome_window_state": "OPENED",
        "metric": "mean_r",
        "cohort": "xauusd_ny",
        "exclusions": [],
        "duplicate_policy": "dedupe_by_candidate_id",
        "cost_slippage_assumptions": "use recorded spread",
        "dsr_pbo_effective_n_policy": "not_computable: fixture",
        "label_separation_policy": "broker_actual_r only",
        "reproducibility_key": "abc",
        "result_boundary": mod.RESULT_BOUNDARY,
    }

    issues = mod.validate_schema_row("experiment_prereg_v1", row)

    assert "experiment_prereg_v1:OUTCOME_WINDOW_MUST_BE_CLOSED_AT_REGISTRATION" in issues
    assert "experiment_prereg_v1:MISSING_FREEZE_TIMESTAMP" in issues
    assert "experiment_prereg_v1:LABEL_POLICY_MISSING_SYNTHETIC_PATH_R" in issues
    assert "experiment_prereg_v1:LABEL_POLICY_MISSING_LIFECYCLE" in issues
    assert "experiment_prereg_v1:LABEL_POLICY_MISSING_OBSERVATION" in issues


def test_hypothesis_validation_requires_allowed_label_and_no_leak_fields():
    row = {
        "hypothesis_id": "H-TEST",
        "mechanism_id": "M-TEST",
        "null": "no difference",
        "alternative": "improves mean R",
        "symbols": ["XAUUSD"],
        "timeframes": ["M15"],
        "entry_or_filter_or_exit_role": "filter",
        "label_class": "mixed_label",
        "no_leak_fields": [],
        "sample_floor": {"n": 30},
        "test_method": "blocked until prereg",
        "live_change_blockers": ["fixture"],
        "result_boundary": mod.RESULT_BOUNDARY,
    }

    issues = mod.validate_schema_row("science_hypothesis_v1", row)

    assert "science_hypothesis_v1:NO_LEAK_FIELDS_REQUIRED" in issues
    assert "science_hypothesis_v1:LABEL_CLASS_NOT_ALLOWED" in issues


def test_lane_prompts_contain_contract_terms():
    payload = mod.build_payload(generated_at_utc="2026-05-06T00:00:00+00:00")

    for lane in payload["lanes"]:
        prompt = mod.render_lane_prompt(lane)
        assert "Mandatory Preflight" in prompt
        assert "Do not touch `main`" in prompt
        assert "Access Request Policy" in prompt
        assert "request access instead of stopping" in prompt
        assert "`curl.exe`" in prompt
        assert "sitemaps" in prompt
        assert "does not authorize paid external spend" in prompt
        assert "paywall/credential bypass" in prompt
        assert "Deep Research Mode" in prompt
        assert "Do not perform one shallow web search" in prompt
        assert "Context And Ambiguity Discipline" in prompt
        assert "Maintain a lane context ledger" in prompt
        assert "Every new ambiguity" in prompt
        assert "Science-First Requirement" in prompt
        assert "Repo Cross-Check" in prompt
        assert "Hypothesis Translation" in prompt
        assert "Required Stop Outputs" in prompt
        assert mod.RESULT_BOUNDARY in prompt
        if lane["role"] == "science_lane":
            assert "mechanism rows" in prompt
            assert "experiment prereg specs" in prompt


def test_source_budget_ledger_blocks_spend_until_owner_cap():
    payload = mod.build_payload(generated_at_utc="2026-05-06T00:00:00+00:00")
    ledger = payload["source_budget_ledger"]

    assert ledger["current_external_cash_spend_cap_usd"] == 0.0
    assert ledger["per_source_limit_usd"] is None
    assert ledger["spend_allowed"] is False
    assert "new subscriptions" in ledger["disallowed_until_owner_approval"]
    assert ledger["result_boundary"] == mod.RESULT_BOUNDARY


def test_write_outputs_creates_control_artifacts_and_prompts(tmp_path: Path):
    payload = mod.build_payload(generated_at_utc="2026-05-06T00:00:00+00:00")
    outputs = mod.write_outputs(payload, root=tmp_path)

    assert len(outputs) == 30
    base = tmp_path / mod.PROGRAM_ROOT
    assert (base / "00_control" / "PROGRAM_GOVERNOR_2026-05-06.md").exists()
    assert (base / "00_control" / "SCHEMA_CONTRACTS_2026-05-06.json").exists()
    assert (base / "00_control" / "SOURCE_BUDGET_LEDGER_2026-05-06.md").exists()
    assert (base / "00_control" / "CREATE_WORKTREES_2026-05-06.ps1").exists()
    assert (base / "04_goal_prompts" / "CANONICAL_LANE_GOAL_PROMPT_TEMPLATE_2026-05-06.md").exists()
    assert (base / "04_goal_prompts" / "G12_G12_RED_TEAM_GOAL_PROMPT_2026-05-06.md").exists()
    assert (base / "05_synthesis" / "SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.json").exists()
    assert mod.RESULT_BOUNDARY in (base / "00_control" / "PROGRAM_GOVERNOR_2026-05-06.md").read_text(encoding="utf-8")


def test_script_writes_program_outputs(tmp_path: Path):
    assert script.main(["--root", str(tmp_path), "--generated-at-utc", "2026-05-06T00:00:00+00:00"]) == 0

    payload_path = tmp_path / mod.PROGRAM_ROOT / "00_control" / "PROGRAM_GOVERNOR_2026-05-06.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))

    assert payload["schema_version"] == mod.SCHEMA_VERSION
    assert payload["status"] == mod.STATUS_READY
    assert payload["result_boundary"] == mod.RESULT_BOUNDARY
    assert payload["lane_count"] == 13
    assert payload["paid_data_calls"] == 0
