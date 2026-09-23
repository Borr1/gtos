from __future__ import annotations

from build_vnext_absolute_moonshot_selector_v3 import (
    DEFAULT_OFF_PACKAGE,
    EXPECTED_REPLAY_ROWS,
    FULL_EVIDENCE_LEDGER,
    RUNTIME_PACKET_SCHEMA,
    classify_selector_v3_action,
    iter_jsonl,
    read_json,
)
from src.research.moonshot_selector_v3_default_off import (
    FORBIDDEN_SELECTOR_V3_RUNTIME_FIELDS,
    apply_selector_v3_default_off,
    runtime_rules_from_selector_v3_package,
)


def _base_row(**overrides):
    row = {
        "scheduler_decision": "ACCEPTED",
        "scheduler_reason": "accepted_money_risk_portfolio_exposure",
        "risk_state": "accepted_full_risk",
        "result_r": 1.25,
        "result_r_class": "source_bound_proxy_r",
        "source_gap_count": 0,
        "source_gap_families": [],
        "source_completeness_state": "complete",
        "repairable_scheduler_block": False,
        "correct_rejection": False,
        "current_policy_cost_adjusted_median_r": 0.4,
        "current_policy_cost_adjusted_high_stress_r": 0.2,
        "best_policy_cost_adjusted_median_r": 0.5,
    }
    row.update(overrides)
    return row


def test_selector_v3_classifier_covers_all_required_actions():
    cases = {
        "trade": _base_row(result_r=1.0),
        "reduce_risk": _base_row(scheduler_decision="ACCEPTED_REDUCED_RISK"),
        "avoid": _base_row(result_r=-0.75),
        "capture_repair": _base_row(
            scheduler_decision="REJECTED",
            result_r=2.0,
            repairable_scheduler_block=True,
        ),
        "no_trade_by_evidence": _base_row(
            scheduler_decision="REJECTED",
            result_r=-1.0,
            correct_rejection=True,
        ),
        "source_required": _base_row(
            result_r=None,
            source_gap_count=1,
            source_gap_families=["historical_broker_intent_or_order_truth"],
            source_completeness_state="broker_intent_missing",
        ),
    }

    observed = {classify_selector_v3_action(row)[0] for row in cases.values()}

    assert observed == set(cases)


def test_package_is_default_off_and_has_full_rule_surface():
    package = read_json(DEFAULT_OFF_PACKAGE, {})

    assert package["enabled_by_default"] is False
    assert package["apply_to_execution_default"] is False
    assert package["live_activation_allowed_by_this_package"] is False
    assert package["runtime_effect_now"] is False
    assert package["runtime_selector_rule_count"] == len(package["runtime_selector_rules"])
    assert package["runtime_selector_rule_count"] > 0
    assert "time_is_friday" not in str(package["runtime_selector_rules"])


def test_full_evidence_ledger_preserves_289928_rows_and_runtime_packet_no_leak():
    count = 0
    forbidden_hits = 0
    for row in iter_jsonl(FULL_EVIDENCE_LEDGER):
        count += 1
        if count <= 1000:
            packet = row.get("runtime_packet_fields") or {}
            forbidden_hits += len(set(packet).intersection(FORBIDDEN_SELECTOR_V3_RUNTIME_FIELDS))

    assert count == EXPECTED_REPLAY_ROWS
    assert forbidden_hits == 0


def test_runtime_packet_schema_forbids_result_and_future_fields():
    schema = read_json(RUNTIME_PACKET_SCHEMA, {})

    forbidden = set(schema["forbidden_future_or_result_fields"])
    for field in {"result_r", "proxy_r", "exact_r", "broker_real_net_r", "path_class", "correct_rejection"}:
        assert field in forbidden
    assert "symbol" in schema["allowed_asof_decision_fields"]
    assert schema["live_activation_allowed_by_this_schema"] is False


def test_selector_v3_helper_ignores_future_fields_and_cannot_activate_package():
    package = read_json(DEFAULT_OFF_PACKAGE, {})
    rule = package["runtime_selector_rules"][0]
    event = {
        "symbol": rule["symbol"],
        "side": rule["side"],
        "framework": rule["framework"],
        "candidate_origin_family": rule["origin_family"],
        "session_bucket": rule["session_bucket"],
        "regime_h4_state": rule["regime_h4_state"],
        "spread_r_bucket": rule["spread_r_bucket"],
        "source_completeness_state": rule["source_completeness_state"],
        "result_r": 99.0,
        "broker_real_net_r": 99.0,
    }

    decision = apply_selector_v3_default_off(
        event,
        package,
        enabled=True,
        apply_to_execution=True,
    )
    router_rules = runtime_rules_from_selector_v3_package(package)

    assert decision.matched_rule_id == rule["rule_id"]
    assert "result_r" in decision.ignored_forbidden_fields
    assert "broker_real_net_r" in decision.ignored_forbidden_fields
    assert decision.runtime_effect_now is False
    assert decision.candidate_use_allowed_now is False
    assert router_rules
