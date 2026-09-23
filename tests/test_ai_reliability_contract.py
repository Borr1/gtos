from src.components.ai_reliability_contract import (
    build_budget_contract,
    build_cache_identity,
    build_fallback_behavior_contract,
    build_semantic_ownership_handoff,
)


def _config():
    return {
        "ai": {"primary_model": "claude-sonnet-4-6"},
        "ai_call_policy": {"max_research_ai_budget_usd": 5.0},
        "budget": {"monthly_cap_usd": 50.0},
    }


def test_cache_identity_requires_model_prompt_input_config_and_source_hashes():
    complete = build_cache_identity(
        model="claude-sonnet-4-6",
        prompt_bundle_sha256="p" * 64,
        user_message_sha256="u" * 64,
        config=_config(),
        source_context={"symbol": "XAUUSD", "candle_time": "2026-06-04T00:00:00Z"},
    )
    incomplete = build_cache_identity(
        model="claude-sonnet-4-6",
        prompt_bundle_sha256=None,
        user_message_sha256="u" * 64,
        config=_config(),
        source_context={"symbol": "XAUUSD"},
    )

    assert complete["cache_key_status"] == "complete"
    assert complete["content_addressed_cache_key"]
    assert incomplete["cache_key_status"] == "incomplete"
    assert "prompt_hash" in incomplete["missing_fields"]


def test_budget_contract_blocks_research_ai_over_cap():
    within = build_budget_contract(
        config=_config(),
        requested_budget_usd=1.25,
        policy_cfg=_config()["ai_call_policy"],
    )
    over = build_budget_contract(
        config=_config(),
        requested_budget_usd=10.0,
        policy_cfg=_config()["ai_call_policy"],
    )

    assert within["budget_within_cap"] is True
    assert over["budget_within_cap"] is False
    assert over["paid_broad_historical_replay_allowed"] is False


def test_fallback_and_ownership_contracts_preserve_boundaries():
    fallback = build_fallback_behavior_contract(
        reason="ai_output_malformed",
        response_status="malformed_demoted",
        parse_attempts=2,
    )
    ownership = build_semantic_ownership_handoff()

    assert fallback["fallback_active"] is True
    assert fallback["fallback_action"] == "NO_TRADE"
    assert fallback["broker_runtime_change"] is False
    assert "LLM schema/model versioning" in ownership["ai_reliability_cost_control_owns"]
    assert "Feature Store" in ownership["wave4_wave5_ml_owns"]
