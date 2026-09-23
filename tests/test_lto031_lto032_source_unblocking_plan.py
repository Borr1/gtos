from __future__ import annotations

import json
from pathlib import Path

from scripts import build_lto031_lto032_source_unblocking_plan as mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _write_text(path: Path, text: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_inputs(tmp_path: Path) -> None:
    _write_json(
        tmp_path / mod.DEFAULT_LTO031,
        {
            "status": "SOURCE_BLOCKED_READINESS_REGISTERED",
            "sources": [
                {"source_key": "pre_2024_tick_lob", "status": "BLOCKED"},
                {"source_key": "pre_2022_ohlcv", "status": "BLOCKED"},
                {"source_key": "fx_cot", "status": "BLOCKED_SOURCE_MAPPING_REQUIRED"},
                {"source_key": "kmw_fx_fix", "status": "BLOCKED"},
                {"source_key": "hkm_intermediary_capital", "status": "BLOCKED"},
                {"source_key": "bis_macro", "status": "BLOCKED"},
                {"source_key": "fed_research_feed", "status": "BLOCKED_SOURCE_UNSPECIFIED"},
            ],
        },
    )
    _write_json(
        tmp_path / mod.DEFAULT_LTO032,
        {
            "status": "PARTIAL_FORWARD_CONTEXT_WITH_SOURCE_BLOCKERS_REGISTERED",
            "sources": [
                {"source_key": "flashalpha_basic_gex_forward_proxy", "status": "READY_FORWARD_CONTEXT_ONLY"},
                {"source_key": "official_or_historical_aggregate_gex", "status": "BLOCKED"},
                {"source_key": "vix1d_vix9d_spread", "status": "BLOCKED"},
                {"source_key": "vrp_delta", "status": "BLOCKED_CONSTRUCTION_REQUIRED"},
            ],
        },
    )
    _write_json(
        tmp_path / mod.DEFAULT_ORDERFLOW,
        {"status": "SIERRA_ACTIVE_DATABENTO_HISTORICAL_REPLAY_DATABENTO_LIVE_LICENSE_BLOCKED"},
    )
    _write_text(tmp_path / mod.DEFAULT_LTO_GOAL_PROMPT, "# goal prompt\n")


def test_plan_links_completed_goal_and_preserves_boundaries(tmp_path):
    _seed_inputs(tmp_path)

    payload = mod.build_payload(root=tmp_path, generated_at_utc="2026-05-05T00:00:00+00:00")

    assert payload["status"] == "GOAL_EXTENSION_READY_RESEARCH_ONLY"
    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["current_blocker_summary"]["lto031_source_count"] == 7
    assert payload["current_blocker_summary"]["lto032_source_count"] == 4
    assert payload["source_contract_count"] == 11
    assert payload["source_contract_counts_by_lto"] == {"LTO-031": 7, "LTO-032": 4}
    assert payload["paid_data_calls"] == 0
    assert payload["order_calls"] == 0
    assert "LIMITATIONS_TO_OPPORTUNITIES_COMPLETION_AUDIT" in payload["linked_completed_goal"]["completion_audit"]


def test_plan_uses_databento_credits_and_sierra_without_replacing_macro_sources(tmp_path):
    _seed_inputs(tmp_path)

    payload = mod.build_payload(root=tmp_path, generated_at_utc="2026-05-05T00:00:00+00:00")
    contracts = {row["source_key"]: row for row in payload["source_contracts"]}

    assert contracts["pre_2024_tick_lob"]["databento_use"] == "PRIMARY_HISTORICAL_COUNTERFACTUAL_REPLAY_SOURCE"
    assert contracts["pre_2024_tick_lob"]["free_or_existing"] == "EXISTING_DATABENTO_HISTORICAL_CREDITS_FIRST"
    assert contracts["fx_cot"]["databento_use"] == "NOT_APPLICABLE"
    assert contracts["bis_macro"]["databento_use"] == "NOT_APPLICABLE"
    assert "CFTC FX COT" in payload["databento_and_sierra_answer"]["databento_credits_do_not_replace"]
    assert ".scid footprint-style bid/ask volume and volume-profile features" in payload["databento_and_sierra_answer"]["sierra_is_useful_for"]


def test_budget_policy_requires_estimate_first_and_cost_caps(tmp_path):
    _seed_inputs(tmp_path)

    payload = mod.build_payload(root=tmp_path, generated_at_utc="2026-05-05T00:00:00+00:00")
    budget = payload["budget_policy"]
    policy = payload["budget_policy"]["databento_historical_credit_policy"]

    assert budget["budget_posture"] == "ZERO_NEW_EXTERNAL_CASH_FOR_NOW_FREE_PUBLIC_AND_EXISTING_CREDITS_ONLY"
    assert budget["current_external_cash_spend_cap_usd"] == 0.0
    assert budget["first_pass_public_sources_usd"] == {
        "min": 0,
        "max": 0,
        "note": "owner-set current rule: no new external cash spend for now",
    }
    assert "existing Databento historical credits only" in budget["current_allowed_cost_sources"]
    assert any("separate owner approval" in item for item in budget["paid_source_deferral"])
    assert policy["use_existing_credits"] is True
    assert policy["no_new_cash_spend"] is True
    assert policy["estimate_before_fetch"] is True
    assert policy["initial_total_credit_cap_usd"] == 25.0
    assert policy["initial_daily_credit_cap_usd"] == 8.0
    assert policy["initial_per_request_cap_usd"] == 1.0
    assert policy["schema_order"] == ["trades", "mbp-10", "mbo"]


def test_markdown_and_goal_extension_include_validation_and_k55_requirements(tmp_path):
    _seed_inputs(tmp_path)

    payload = mod.build_payload(root=tmp_path, generated_at_utc="2026-05-05T00:00:00+00:00")
    markdown = mod.render_markdown(payload)
    extension = mod.render_goal_extension(payload)

    assert "P2_DATABENTO_HISTORICAL_CREDIT_REPLAY" in markdown
    assert "P3_SIERRA_FULL_UTILIZATION" in markdown
    assert "P5_K55_AND_SHADOW_JOIN" in markdown
    assert "G2_NO_LOOKAHEAD" in markdown
    assert "NO_PROMOTION_VERDICT" in markdown
    assert "$0` to `$250" not in markdown
    assert "Current external cash spend cap: `$0`" in markdown
    assert "Current spend rule: `$0` new external cash spend for now" in extension
    assert "already-achieved limitations-to-opportunities goal" in extension
    assert "nothing should sit unused as raw data" in extension
