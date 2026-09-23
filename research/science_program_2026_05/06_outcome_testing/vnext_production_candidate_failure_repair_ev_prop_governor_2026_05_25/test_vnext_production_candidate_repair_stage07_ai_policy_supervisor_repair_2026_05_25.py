from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_candidate_repair_stage07_ai_policy_supervisor_repair_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("stage07_ai_policy_repair", MODULE_PATH)
stage07 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = stage07
spec.loader.exec_module(stage07)


def _row() -> dict:
    return {
        "candidate_id": "cand-stage07",
        "as_of_utc": "2026-05-25T09:00:00+00:00",
        "symbol": "XAUUSD",
        "session": "london",
        "side": "LONG",
        "framework": "ob_retest",
    }


def test_stage07_recovered_stage05_avoid_calls_constrained_validator_not_skip():
    policy = stage07.classify_stage07_policy(
        _row(),
        stage03={"route_decision": "AVOID", "pre_ai_action": "SKIP_AI_AVOID_ONLY"},
        stage05={
            "implementation_decision": "DEMOTE_TO_CONTEXT_NOT_EXECUTION_BLOCK",
            "recovered": True,
            "hard_block_allowed_after_repair": False,
        },
        stage06={"selected": True},
    )

    assert policy["stage07_ai_policy_action"] == "CALL_AI_CONSTRAINED_VALIDATOR"
    assert policy["stage07_ai_call_required_for_production"] is True
    assert policy["stage07_no_paid_call_selected"] is False
    assert policy["stage07_no_paid_call_status"] == "diagnostic_ai_required_not_selected"


def test_stage07_preserved_bounded_avoid_skips_ai_and_no_paid_trade():
    policy = stage07.classify_stage07_policy(
        _row(),
        stage03={"route_decision": "AVOID", "pre_ai_action": "SKIP_AI_AVOID_ONLY"},
        stage05={
            "implementation_decision": "PRESERVE_BOUNDED_AVOID_FILTER",
            "recovered": False,
            "hard_block_allowed_after_repair": True,
        },
        stage06=None,
    )

    assert policy["stage07_ai_policy_action"] == "SKIP_AI_MECHANICAL_AVOID"
    assert policy["stage07_ai_call_required_for_production"] is False
    assert policy["stage07_no_paid_call_selected"] is False
    assert policy["stage07_no_paid_call_diagnostic_only"] is True


def test_stage07_repaired_follow_uses_ai_validator_under_funded_prop_route():
    narrowed = stage07.classify_stage07_policy(
        _row(),
        stage03={"route_decision": "FOLLOW", "pre_ai_action": "NARROW_AI_TO_SIDE"},
        stage05=None,
        stage06={"selected": True},
    )
    constrained = stage07.classify_stage07_policy(
        _row(),
        stage03={"route_decision": "FOLLOW", "pre_ai_action": "ALLOW_AI"},
        stage05=None,
        stage06={"selected": True},
    )

    assert narrowed["stage07_ai_policy_action"] == "CALL_AI_NARROWED_ROUTE"
    assert constrained["stage07_ai_policy_action"] == "CALL_AI_CONSTRAINED_VALIDATOR"
    assert narrowed["stage07_ai_call_required_for_production"] is True
    assert constrained["stage07_no_paid_call_status"] == "diagnostic_ai_required_not_selected"


def test_stage07_prompt_packet_hash_is_content_addressed_and_asof_only():
    packet = stage07.prompt_packet(
        _row(),
        action="CALL_AI_NARROWED_ROUTE",
        role="vnext_route_validator",
        branch="unit_test",
    )

    assert packet["prompt_packet_sha256"]
    assert packet["cache_key_sha256"]
    assert packet["decision_inputs_exclude_future_outcome_and_r"] is True
    assert "simulated_r" not in packet
