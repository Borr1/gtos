from src.components.ultimate_book.convergence_replay_matcher import attach_reservoir_matches
from src.components.ultimate_book.convergence_advisory import build_convergence_advisory
from src.components.ultimate_book.convergence_replay_record import (
    RESULT_FIELD_KEYS,
    normalize_historical_candidate,
    normalize_runtime_packet,
    validate_replay_record,
)
from src.components.ultimate_book.runtime_learning_packet import build_runtime_learning_packet


def test_runtime_packet_expands_grouped_unit_into_replay_records():
    packet = build_runtime_learning_packet(
        namespace="ftmo_test",
        event_type="unit_shadow",
        bridge={"runtime_effect_now": False, "market_expansion_policy": "positive_weighted12_after_swap"},
        unit={
            "sleeve_members": ["ny_crypto_momentum", "asian_fade"],
            "cluster": "crypto",
            "n_trades": 2,
            "confidence": 0.75,
            "risk_pct_per_trade": 0.001,
            "unit_risk_pct": 0.002,
            "sized": True,
            "overlays_applied": ["session_active_stack"],
        },
        outcome={
            "symbol": "BTCUSD",
            "direction": 1,
            "placement_status": "shadow",
            "candidate_id": "cand-1",
            "source_completeness_status": "runtime_cycle_summary_observed",
        },
        convergence_advisory={
            "schema_version": "ultimate_convergence_advisory_v1",
            "join_keys": {"symbol": "BTCUSD", "candidate_id": "cand-1"},
            "direct_execution_authority": False,
            "broker_runtime_change_status": False,
        },
    )

    records = normalize_runtime_packet(packet, source_path="shadow_logs/example.jsonl", source_line_no=7)

    assert [row["sleeve"] for row in records] == ["ny_crypto_momentum", "asian_fade"]
    assert all(row["schema_version"] == "ultimate_convergence_candidate_replay_record_v1" for row in records)
    assert all(row["source_kind"] == "runtime_packet" for row in records)
    assert all(row["broker_runtime_change_status"] is False for row in records)
    assert all(row["direct_execution_authority"] is False for row in records)
    assert records[0]["match_inputs"]["symbol"] == "BTCUSD"
    assert records[0]["match_inputs"]["side"] == "LONG"
    assert not set(records[0]["match_inputs"]).intersection(RESULT_FIELD_KEYS)
    ok, issues = validate_replay_record(records[0])
    assert ok, issues


def test_historical_candidate_preserves_cp281_match_fields_without_result_leakage():
    row = {
        "symbol_family": "USDJPY_6J",
        "symbol": "USDJPY_6J",
        "source_symbol": "USDJPY",
        "market_timeframe": "H1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h16",
        "side": "LONG",
        "source_path_sha256": "path-hash",
        "source_file_sha256": "file-hash",
        "cost_adjusted_simulated_r": 0.25,
        "effective_n": 100.0,
    }

    record = normalize_historical_candidate(row, source_path="cp281.jsonl", source_line_no=1)

    assert record["source_kind"] == "historical_replay_candidate"
    assert record["side"] == "LONG"
    assert record["match_inputs"]["source_path_sha256"] == "path-hash"
    assert "cost_adjusted_simulated_r" not in record["match_inputs"]
    ok, issues = validate_replay_record(record)
    assert ok, issues


def test_replay_matcher_attaches_observation_only_exact_matches():
    record = normalize_historical_candidate({
        "candidate_id": "cand-1",
        "symbol": "XAUUSD",
        "side": "LONG",
        "session_bucket": "london",
        "framework": "ob_retest",
        "origin_family": "current_ob_retest",
        "symbol_family": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "H1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h16",
        "source_path_sha256": "path-hash",
        "source_file_sha256": "file-hash",
    })
    indexes = {
        "selector_v3_index": {
            ("XAUUSD", "LONG", "LONDON", "OB_RETEST", "CURRENT_OB_RETEST"): [{
                "rule_id": "selector_v3_rule_test",
                "selector_v3_action": "tradeable_now",
                "risk_multiplier": 1.0,
                "known_proxy_r_rows": 12,
                "proxy_r_sum": 6.0,
                "expectancy_r": 0.5,
            }]
        },
        "scheduler_v3_rows": [{
            "candidate_id": "cand-1",
            "scheduler_v3_decision": "SELECTED",
            "scheduler_v3_action": "prioritize",
            "scheduler_v3_action_class": "priority",
            "result_r": 1.25,
            "result_r_class": "source_bound_proxy",
        }],
        "scheduler_v3_index": {},
        "cp281_index": {
            ("XAUUSD", "XAUUSD", "XAUUSD", "H1", "ALL_SESSIONS", "H16", "LONG", "PATH-HASH", "FILE-HASH"): [{
                "cp281_rule_row_id": "cp281-test",
                "action_class": "follow_rule",
                "candidate_use_allowed_now": False,
                "runtime_candidate_use_permitted": False,
                "cost_adjusted_simulated_r": 0.25,
                "gross_simulated_r": 0.3,
                "stress_simulated_r": 0.1,
                "effective_n": 100.0,
            }]
        },
    }

    matched = attach_reservoir_matches(record, indexes)

    assert matched["match_summary"]["exact_match_count"] == 3
    assert matched["match_summary"]["direct_execution_authority"] is False
    assert matched["match_summary"]["broker_runtime_change_status"] is False
    assert {row["reservoir"] for row in matched["reservoir_matches"]} == {
        "selector_v3_source_bound_proxy",
        "scheduler_v3_source_bound_proxy",
        "cp281_ready_runtime_mapping",
    }
    assert all(row["direct_execution_authority"] is False for row in matched["reservoir_matches"])


def test_convergence_advisory_can_carry_candidate_level_matches():
    advisory = build_convergence_advisory(
        config={
            "ultimate_convergence_advisory_enabled": True,
            "ultimate_convergence_advisory_log_enabled": True,
            "ultimate_convergence_advisory_apply_to_execution": False,
        },
        namespace="ftmo_test",
        event_type="unit_shadow",
        bridge={"runtime_effect_now": False},
        outcome={"symbol": "BTCUSD", "placement_status": "shadow"},
        candidate_match_inputs={"symbol": "BTCUSD", "side": "LONG"},
        candidate_matches=[{
            "reservoir": "selector_v3_source_bound_proxy",
            "match_status": "exact_runtime_rule_match",
            "direct_execution_authority": False,
            "broker_runtime_change_status": False,
        }],
    )

    assert advisory["match_status"] == "candidate_level_matches_attached_observation_only"
    assert advisory["candidate_level"]["match_inputs"]["symbol"] == "BTCUSD"
    assert advisory["candidate_level"]["candidate_matches"][0]["reservoir"] == "selector_v3_source_bound_proxy"
    assert advisory["candidate_level"]["direct_execution_authority"] is False
