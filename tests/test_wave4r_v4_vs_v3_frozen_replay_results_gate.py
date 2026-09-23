from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.components.live_decision_packet_v4 import validate_live_decision_packet_v4
from src.research_infra.wave4r_v4_vs_v3_frozen_replay_results_gate import (
    HARD_HALT_ROOT,
    WAVE4A_ROOT,
    LedgerHandles,
    ReplayPosition,
    ReplayState,
    ReplaySummary,
    compact_final_dynamic_router_row,
    count_jsonl_rows,
    day_session_integrity_stats,
    evaluate_row,
    evaluate_window,
    hard_halt_binding_rows,
    infer_replay_limit_fill,
    limitation_backlog_integrity_stats,
    momentum_2r_proxy,
    normalize_v4_config,
    ordered_target_stop_outcome,
    iter_jsonl,
    packet_ledger_integrity_stats,
    promoted_router_result,
    row_session,
    stage05_dynamic_row,
    write_aggregate_ledgers,
    write_limitations_and_fix_backlog,
    write_row_ledgers,
)
from src.research.moonshot_scheduler_v4_best_trade_allocator import allocate_decision_window


def test_candidate_trade_microscope_ledger_is_storage_alias(tmp_path: Path) -> None:
    with LedgerHandles(tmp_path) as ledgers:
        ledgers.write("WAVE4R_CANDIDATE_DECISION_MICROSCOPE_LEDGER.jsonl", {"candidate_id": "row-1"})
        ledgers.write("WAVE4R_CANDIDATE_TRADE_MICROSCOPE_LEDGER.jsonl", {"candidate_id": "row-1"})

    decision = tmp_path / "WAVE4R_CANDIDATE_DECISION_MICROSCOPE_LEDGER.jsonl"
    trade = tmp_path / "WAVE4R_CANDIDATE_TRADE_MICROSCOPE_LEDGER.jsonl"

    assert decision.read_text(encoding="utf-8") == trade.read_text(encoding="utf-8")
    assert decision.stat().st_ino == trade.stat().st_ino


def test_jsonl_readers_support_gzip_payload_with_jsonl_suffix(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("WAVE4R_COMPRESS_JSONL", "1")
    with LedgerHandles(tmp_path) as ledgers:
        ledgers.write("WAVE4R_RESULTS_LEDGER.jsonl", {"candidate_id": "compressed"})

    path = tmp_path / "WAVE4R_RESULTS_LEDGER.jsonl"

    assert path.read_bytes()[:2] == b"\x1f\x8b"
    assert count_jsonl_rows(path) == 1
    assert list(iter_jsonl(path))[0]["candidate_id"] == "compressed"


def _config() -> dict:
    return normalize_v4_config(
        {
            "gtos_vnext_runtime": {
                "probability_debate_team_engine_v4": {
                    "enabled": True,
                    "apply_to_execution": True,
                },
                "moonshot_dynamic_execution_router_policy": "momentum_exhaustion",
                "moonshot_dynamic_execution_router_momentum_final_target_r": 2.0,
                "moonshot_exit_policy_v4_enabled": True,
                "moonshot_exit_policy_v4_apply_to_execution": True,
            },
            "risk": {
                "risk_per_trade_pct": 2.0,
                "same_symbol_lifecycle_v4": {
                    "enabled": True,
                    "max_same_symbol_risk_pct": 2.5,
                    "scale_in_min_probability_improvement": 0.05,
                    "scale_in_min_ev_improvement_r": 0.05,
                },
            },
        }
    )


def _policy(final_r: float, mfe_r: float, mae_r: float, exit_time: str) -> dict:
    return {
        "final_r": final_r,
        "mfe_r": mfe_r,
        "mae_r": mae_r,
        "exit_reason": "fixture_exit",
        "exit_time_utc": exit_time,
        "same_bar_ambiguity": False,
    }


def _write_m15_csv(path: Path, closes_by_time: dict[str, float]) -> str:
    lines = ["time,open,high,low,close,volume"]
    for timestamp, close in closes_by_time.items():
        lines.append(f"{timestamp},{close},{close},{close},{close},1")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _row(
    candidate: str,
    *,
    asof: str,
    symbol: str = "XAUUSD",
    side: str = "LONG",
    source_complete: bool = True,
    **extra: object,
) -> dict:
    return {
        "candidate_id": candidate,
        "symbol": symbol,
        "session": "NY",
        "framework": "fvg_fill",
        "side": side,
        "candle_time_utc": asof,
        "entry_first_touch_utc": asof,
        "entry_reference": 2000.0,
        "stop_or_invalidation": 1990.0,
        "source_window_complete": source_complete,
        "source_path_feature_status": "asof_complete" if source_complete else "source_gap",
        "source_path": "fixture.jsonl",
        "source_sha256": "abc123",
        "policy_results": {
            "legacy_fixed_1.5r": _policy(1.5, 2.2, -0.2, "2026-01-01T01:00:00+00:00"),
            "be_after_trigger": _policy(1.0, 2.2, -0.2, "2026-01-01T01:00:00+00:00"),
            "partial_be_runner": _policy(0.8, 2.2, -0.2, "2026-01-01T01:00:00+00:00"),
            "live_current_j46_j49": _policy(0.2, 2.2, -0.2, "2026-01-01T01:00:00+00:00"),
            "path_aware_runner": _policy(0.5, 2.2, -0.2, "2026-01-01T01:00:00+00:00"),
            "trailing_runner": _policy(0.5, 2.2, -0.2, "2026-01-01T01:00:00+00:00"),
            "ai_target": _policy(0.5, 2.2, -0.2, "2026-01-01T01:00:00+00:00"),
        },
        **extra,
    }


def test_momentum_2r_proxy_is_conservative_when_target_and_stop_ordering_ambiguous() -> None:
    row = _row("ambiguous", asof="2026-01-01T00:00:00+00:00")
    for result in row["policy_results"].values():
        result["mfe_r"] = 2.4
        result["mae_r"] = -1.2

    proxy = momentum_2r_proxy(row)

    assert proxy["final_r"] == -1.0
    assert proxy["same_bar_ambiguity"] is True
    assert "ordered_ltf_or_tick_required_for_exact_static_2r" in proxy["source_gaps"]


def test_root_market_symbol_does_not_create_unrelated_same_symbol_conflict() -> None:
    config = _config()
    config["market"] = {"symbol": "XAUUSD"}
    state = ReplayState(
        open_positions=[
            ReplayPosition(
                ticket=45,
                candidate_id="open-gold",
                symbol="XAUUSD",
                side="LONG",
                opened_at_utc="2026-01-01T00:00:00+00:00",
                exit_time_utc="2026-01-01T03:00:00+00:00",
                final_r=0.0,
                risk_pct=0.5,
                probability=0.6,
                ev_r=0.3,
                thesis_id="open-gold",
            )
        ],
        open_risk_r=0.25,
    )

    result = evaluate_row(
        _row("gbp-candidate", asof="2026-01-01T00:15:00+00:00", symbol="GBPJPY"),
        state,
        config,
    )

    assert result["result"]["same_symbol_action"] == "new_position"
    assert result["lifecycle"]["open_position_snapshot"] == []


def test_broker_alias_opposite_dominance_infers_replay_close_reverse() -> None:
    state = ReplayState(
        open_positions=[
            ReplayPosition(
                ticket=46,
                candidate_id="weak-ger30-parent",
                symbol="GER30",
                side="SHORT",
                opened_at_utc="2026-01-01T00:00:00+00:00",
                exit_time_utc="2026-01-01T03:00:00+00:00",
                final_r=0.0,
                risk_pct=0.5,
                probability=0.1,
                ev_r=-0.2,
                thesis_id="old-ger30-thesis",
            )
        ],
        open_risk_r=0.25,
    )

    result = evaluate_row(
        _row("dominant-ger40", asof="2026-01-01T00:15:00+00:00", symbol="GER40", side="LONG"),
        state,
        _config(),
    )

    proof = result["lifecycle"]["candidate"]["proof"]
    assert result["result"]["same_symbol_action"] == "close_and_reverse"
    assert result["lifecycle"]["close_ticket"] == 46
    assert proof["replay_lifecycle_intent_source_status"] == (
        "source_complete_opposite_side_close_reverse_inferred"
    )
    assert set(proof["same_symbol_aliases"]) >= {"GER40", "GER30"}


def test_broker_alias_same_direction_improvement_infers_replay_scale_in() -> None:
    state = ReplayState(
        open_positions=[
            ReplayPosition(
                ticket=47,
                candidate_id="weak-ger30-parent",
                symbol="GER30",
                side="LONG",
                opened_at_utc="2026-01-01T00:00:00+00:00",
                exit_time_utc="2026-01-01T03:00:00+00:00",
                final_r=0.0,
                risk_pct=0.5,
                probability=0.1,
                ev_r=-0.2,
                thesis_id="shared-ger-thesis",
            )
        ],
        open_risk_r=0.25,
    )

    result = evaluate_row(
        _row(
            "scale-ger40",
            asof="2026-01-01T00:15:00+00:00",
            symbol="GER40",
            side="LONG",
            thesis_id="shared-ger-thesis",
        ),
        state,
        _config(),
    )

    proof = result["lifecycle"]["candidate"]["proof"]
    assert result["result"]["same_symbol_action"] == "same_direction_scale_in"
    assert result["lifecycle"]["parent_ticket"] == 47
    assert proof["replay_lifecycle_intent_source_status"] == (
        "source_complete_same_thesis_scale_in_inferred"
    )
    assert set(proof["same_symbol_aliases"]) >= {"GER40", "GER30"}


def test_better_thesis_same_direction_scale_in_does_not_bypass_risk_headroom() -> None:
    state = ReplayState(
        open_positions=[
            ReplayPosition(
                ticket=50,
                candidate_id="full-risk-xau-parent",
                symbol="XAUUSD",
                side="LONG",
                opened_at_utc="2026-01-01T00:00:00+00:00",
                exit_time_utc="2026-01-01T03:00:00+00:00",
                final_r=0.0,
                risk_pct=2.0,
                probability=0.1,
                ev_r=-0.2,
                thesis_id="old-xau-thesis",
            )
        ],
        open_risk_r=1.0,
    )

    result = evaluate_row(
        _row(
            "risk-capped-better-xau-thesis",
            asof="2026-01-01T00:15:00+00:00",
            symbol="XAUUSD",
            side="LONG",
            thesis_id="new-xau-thesis",
        ),
        state,
        _config(),
    )

    lifecycle = result["lifecycle"]
    proof = lifecycle["candidate"]["proof"]
    vetoes = lifecycle["vetoes"]
    assert result["result"]["same_symbol_action"] == "no_trade_duplicate"
    assert result["result"]["branch_decision"] == "zero_trade_or_reject"
    assert proof["replay_lifecycle_intent_source_status"] == (
        "source_complete_better_thesis_same_direction_scale_in_inferred"
    )
    assert any(veto["veto"] == "same_symbol_risk_headroom_exceeded" for veto in vetoes)


def test_live_packet_binding_uses_current_contract_hashes_and_field_groups() -> None:
    state = ReplayState()
    evaluated = evaluate_row(
        _row("packet_binding", asof="2026-01-01T00:00:00+00:00"),
        state,
        _config(),
    )

    result = evaluated["result"]
    summary = evaluated["live_packet_summary"]
    packet = evaluated["live_packet"]
    groups = packet["field_groups"]

    assert len(result["packet_hash_sha256"]) == 64
    assert result["packet_hash"] == result["packet_hash_sha256"]
    assert len(result["source_event_hash_sha256"]) == 64
    assert summary["packet_hash_sha256"] == result["packet_hash_sha256"]
    assert summary["source_event_hash_sha256"] == result["source_event_hash_sha256"]
    assert summary["field_group_status_summary"]["present_group_count"] > 0
    assert isinstance(summary["validation_issues"], list)
    assert "field_group_statuses" not in summary
    assert "source_event_hash" not in summary
    assert validate_live_decision_packet_v4(dict(packet)) == []
    probability_group = groups["probability_debate_numeric_theses"]
    assert probability_group["group_source_status"] == "captured_present"
    assert not [
        field
        for field in probability_group["missing_fields"]
        if str(field).startswith("numeric_theses.")
    ]
    assert set(probability_group["numeric_theses"]) == {
        "long",
        "short",
        "no_trade",
        "wait",
        "scale",
        "reduce",
        "close",
        "reverse",
    }
    confluence_group = groups["follow_avoid_mixed_numeric_confluence"]
    assert confluence_group["group_source_status"] == "captured_present"
    for field in ("direction", "strength", "confidence", "source_completeness"):
        assert confluence_group[field]["source_status"] == "captured"
    scheduler_group = groups["selector_allocator_final_say"]
    assert scheduler_group["decision_window_id"]["source_status"] == "captured"
    assert scheduler_group["candidate_set_id"]["source_status"] == "captured"
    assert scheduler_group["alternative_candidate_count"]["source_status"] == "captured"
    assert scheduler_group["selected_action_class"]["source_status"] == "captured"
    assert "decision_window_id" not in scheduler_group["missing_fields"]
    assert "candidate_set_id" not in scheduler_group["missing_fields"]
    assert "alternative_candidate_count" not in scheduler_group["missing_fields"]
    assert "selected_action_class" not in scheduler_group["missing_fields"]
    lifecycle_group = groups["same_symbol_lifecycle_and_ticket_state"]
    assert lifecycle_group["group_source_status"] == "captured_complete"
    assert lifecycle_group["missing_fields"] == []
    assert lifecycle_group["same_symbol_lifecycle_packet_source"] == (
        "decision_pipeline.same_symbol_lifecycle_v4"
    )
    assert lifecycle_group["durable_lifecycle_capture"]["status"] == "complete"
    assert lifecycle_group["candidate_lifecycle_capture"]["candidate_id"] == (
        "packet_binding"
    )
    assert lifecycle_group["candidate_lifecycle_capture"]["thesis_id"] == (
        "wave4r:packet_binding"
    )
    assert lifecycle_group["candidate_lifecycle_capture"]["risk_pct"] == 2.0
    assert lifecycle_group["candidate_lifecycle_capture"]["probability_at_decision"] > 0
    assert lifecycle_group["candidate_lifecycle_capture"]["ev_r_at_decision"] > 0
    assert lifecycle_group["candidate_lifecycle_capture"][
        "source_completeness_status"
    ] == "source_window_complete"
    assert lifecycle_group["candidate_lifecycle_capture"]["freshness_status"] == "fresh"
    assert lifecycle_group["scale_reduce_close_reverse_state"]["value"]["action"] == (
        "new_position"
    )
    assert lifecycle_group["scale_reduce_close_reverse_state"]["value"][
        "permitted_order_intent"
    ] is True


def test_live_packet_validation_recomputes_hashes_and_preserves_source_boundary() -> None:
    evaluated = evaluate_row(
        _row("packet_hash_validation", asof="2026-01-01T00:00:00+00:00"),
        ReplayState(),
        _config(),
    )
    packet = json.loads(json.dumps(evaluated["live_packet"]))
    original_source_hash = packet["source_event_hash_sha256"]

    mutated_execution = json.loads(json.dumps(packet))
    mutated_execution["field_groups"]["execution_geometry_policy_and_order_readiness"][
        "order_readiness"
    ]["action"] = "mutated_after_build"
    execution_issues = validate_live_decision_packet_v4(mutated_execution)
    assert any(issue["code"] == "packet_hash_mismatch" for issue in execution_issues)
    assert not any(issue["code"] == "source_event_hash_mismatch" for issue in execution_issues)
    assert mutated_execution["source_event_hash_sha256"] == original_source_hash

    mutated_source = json.loads(json.dumps(packet))
    mutated_source["source_event_hash_material"]["raw_data_identity"]["source_hash"] = "changed"
    source_issues = validate_live_decision_packet_v4(mutated_source)
    assert any(issue["code"] == "source_event_hash_mismatch" for issue in source_issues)


def test_packet_binding_integrity_scanner_rejects_stale_null_keys(tmp_path: Path) -> None:
    route = tmp_path
    ledger = route / "WAVE4R_V4_ASOF_PACKET_LEDGER.jsonl"
    ledger.write_text(
        json.dumps(
            {
                "candidate_id": "bad_packet",
                "packet_hash": None,
                "packet_hash_sha256": None,
                "source_event_hash_sha256": None,
                "field_group_statuses": None,
                "source_event_hash": None,
                "live_decision_packet_v4_summary": {
                    "field_group_statuses": None,
                    "source_event_hash": None,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    stats = packet_ledger_integrity_stats(route)

    assert stats["rows"] == 1
    assert stats["missing_packet_hash"] == 1
    assert stats["missing_source_event_hash_sha256"] >= 1
    assert stats["missing_field_group_status_summary"] == 1
    assert stats["stale_key_rows"] == 1
    assert stats["top_level_stale_key_rows"] == 1


def test_packet_binding_integrity_scanner_rejects_semantic_unbound_groups(
    tmp_path: Path,
) -> None:
    route = tmp_path
    valid_hash = "a" * 64
    ledger = route / "WAVE4R_V4_ASOF_PACKET_LEDGER.jsonl"
    missing = {
        "probability_debate_numeric_theses": [
            "numeric_theses.long",
            "numeric_theses.short",
        ],
        "follow_avoid_mixed_numeric_confluence": [
            "direction",
            "strength",
            "confidence",
            "source_completeness",
        ],
        "selector_allocator_final_say": [
            "decision_window_id",
            "candidate_set_id",
            "alternative_candidate_count",
            "selected_action_class",
        ],
    }
    summary = {
        "packet_hash_sha256": valid_hash,
        "source_event_hash_sha256": valid_hash,
        "field_group_status_summary": {"status_counts": {"captured_incomplete": 3}},
        "missing_fields_by_group": missing,
        "capture_status": "bound_with_explicit_source_gap_groups",
        "validation_issues": [],
    }
    ledger.write_text(
        json.dumps(
            {
                "candidate_id": "semantic_bad_packet",
                "packet_hash": valid_hash,
                "packet_hash_sha256": valid_hash,
                "source_event_hash_sha256": valid_hash,
                "field_group_status_summary": summary["field_group_status_summary"],
                "missing_fields_by_group": missing,
                "packet_validation_issue_count": 0,
                "live_decision_packet_v4_summary": summary,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    stats = packet_ledger_integrity_stats(route)

    assert stats["probability_semantic_unbound_rows"] == 1
    assert stats["confluence_semantic_unbound_rows"] == 1
    assert stats["scheduler_semantic_unbound_rows"] == 1


def test_same_symbol_scale_in_and_reverse_are_materialized() -> None:
    config = _config()
    scale_state = ReplayState(
        open_positions=[
            ReplayPosition(
                ticket=1,
                candidate_id="parent",
                symbol="XAUUSD",
                side="LONG",
                opened_at_utc="2026-01-01T00:00:00+00:00",
                exit_time_utc="2026-01-01T03:00:00+00:00",
                final_r=0.0,
                risk_pct=0.5,
                probability=0.1,
                ev_r=-0.2,
                thesis_id="shared-thesis",
            )
        ]
    )
    scale = evaluate_row(
        _row(
            "scale",
            asof="2026-01-01T00:15:00+00:00",
            same_symbol_lifecycle_action="same_direction_scale_in",
            thesis_id="shared-thesis",
        ),
        scale_state,
        config,
    )
    assert scale["result"]["same_symbol_action"] == "same_direction_scale_in"
    scale_group = scale["live_packet"]["field_groups"][
        "same_symbol_lifecycle_and_ticket_state"
    ]
    assert scale_group["group_source_status"] == "captured_complete"
    assert scale_group["parent_ticket"] == 1
    assert scale_group["parent_thesis_id"] == "shared-thesis"
    assert scale_group["selected_tickets"] == [1]
    assert scale_group["candidate_lifecycle_capture"]["thesis_id"] == "shared-thesis"
    assert scale_group["open_position_snapshot"][0]["ticket"] == 1
    assert scale_group["open_position_snapshot"][0]["thesis_id"] == "shared-thesis"
    assert scale_group["partial_be_trailing_stale_thesis_state"]["source_status"] == (
        "captured"
    )
    assert scale_group["scale_reduce_close_reverse_state"]["value"]["action"] == (
        "same_direction_scale_in"
    )

    reverse_state = ReplayState(
        open_positions=[
            ReplayPosition(
                ticket=2,
                candidate_id="parent-short",
                symbol="XAUUSD",
                side="SHORT",
                opened_at_utc="2026-01-01T00:00:00+00:00",
                exit_time_utc="2026-01-01T03:00:00+00:00",
                final_r=0.0,
                risk_pct=0.5,
                probability=0.7,
                ev_r=0.2,
                thesis_id="old-thesis",
            )
        ]
    )
    reverse = evaluate_row(
        _row(
            "reverse",
            asof="2026-01-01T00:15:00+00:00",
            side="LONG",
            same_symbol_lifecycle_action="close_and_reverse",
        ),
        reverse_state,
        config,
    )
    assert reverse["result"]["same_symbol_action"] == "close_and_reverse"


def test_ordered_target_stop_sequence_overrides_mfe_mae_ambiguity() -> None:
    row = _row(
        "ordered",
        asof="2026-01-01T00:00:00+00:00",
        configured_target_first_touch_utc="2026-01-01T00:30:00+00:00",
        configured_stop_first_touch_utc="2026-01-01T00:45:00+00:00",
    )
    for result in row["policy_results"].values():
        result["mfe_r"] = 2.5
        result["mae_r"] = -1.2

    proxy = momentum_2r_proxy(row)

    assert proxy["final_r"] == 2.0
    assert proxy["status"] == "ordered_target_first"
    assert proxy["same_bar_ambiguity"] is False
    assert ordered_target_stop_outcome(row)["terminal_outcome"] == "target_2r_first_ordered"


def test_replay_limit_fill_infers_post_decision_entry_touch_without_broker_order_truth() -> None:
    row = _row(
        "limit-fill",
        asof="2026-01-01T00:00:00+00:00",
        entry_first_touch_utc="2026-01-01T00:30:00+00:00",
    )

    inference = infer_replay_limit_fill(row)
    promoted = promoted_router_result(row)

    assert inference["filled"] is True
    assert inference["status"] == "synthetic_limit_filled_from_ordered_price_action"
    assert inference["broker_truth_required_for_synthetic_fill"] is False
    assert promoted["fill_status"] == "synthetic_replay_filled_from_ordered_price_action"
    assert promoted["limit_fill_status"] == "synthetic_replay_entry_touch_after_decision"
    assert promoted["replay_limit_fill_inference"]["minutes_to_fill"] == 30.0


def test_replay_limit_fill_rejects_pre_decision_entry_touch() -> None:
    row = _row(
        "pre-touch",
        asof="2026-01-01T00:15:00+00:00",
        entry_first_touch_utc="2026-01-01T00:00:00+00:00",
    )

    inference = infer_replay_limit_fill(row)

    assert inference["filled"] is False
    assert inference["status"] == "entry_touch_before_replay_order_time_not_counted_as_fill"


def test_adverse_first_then_mfe_and_static_dynamic_geometry_are_labeled() -> None:
    row = _row("adverse", asof="2026-01-01T00:00:00+00:00")
    for result in row["policy_results"].values():
        result["mfe_r"] = 1.7
        result["mae_r"] = -0.8
        result["final_r"] = 1.5

    evaluated = evaluate_row(row, ReplayState(), _config())

    assert evaluated["result"]["adverse_before_profit_flag"] is True
    assert evaluated["result"]["static_2r_vs_dynamic_geometry"]["policy_id"] == "momentum_exhaustion_configured_2r_proxy"
    assert evaluated["result"]["legacy_fixed_1_5r_r"] == 1.5


def test_promoted_router_result_binds_may27_replay_instead_of_j46_static() -> None:
    row = _row("promoted", asof="2026-01-01T00:00:00+00:00")
    row["_promoted_router_replay"] = {
        "chosen_policy": "momentum_exhaustion",
        "execution_policy_id": "vnext_exec_momentum_1r_pullback_04r_cap_2r",
        "final_r": 2.313169,
        "mfe_r": 2.713169,
        "mae_r": -0.250998,
        "exit_reason": "momentum_exhaustion_pullback",
        "exit_time_utc": "2026-01-01T01:00:00+00:00",
        "comparison_fixed_1_5r_r": 1.5,
        "comparison_partial_be_runner_r": 1.25,
        "cost_status": "missing_historical_live_cost_lifecycle_fields",
    }

    promoted = promoted_router_result(row)

    assert promoted["policy_id"] == "promoted_momentum_primary_partial_exception_router"
    assert promoted["selected_policy"] == "momentum_exhaustion"
    assert promoted["final_r"] == 2.313169
    assert promoted["comparison_policy_r"]["legacy_fixed_1.5r"] == 1.5
    assert "missing_historical_live_cost_lifecycle_fields" in promoted["source_gaps"]


def test_promoted_router_compact_row_preserves_source_record_and_timing_fields() -> None:
    compact = compact_final_dynamic_router_row(
        {
            "candidate_id": "router-row-id",
            "source_record_candidate_id": "may26-candidate-id",
            "selected_row_id": "stage04_order_123",
            "chosen_policy": "momentum_exhaustion",
            "entry_touch_time_utc": "2026-01-01 00:15:00",
            "source_time_utc": "2026-01-01 00:00:00",
            "exit_time_utc": "2026-01-01 01:00:00",
            "entry_timing": "source_entry_touch_bar",
            "fill_status": "filled_in_replay",
            "limit_fill_status": "filled_on_source_entry_touch",
            "delayed_fill_bars": "1",
            "final_r": "2.0",
            "dynamic_policy_transition_trace": {"pullback_from_mfe_r": 0.4},
            "exit_policy_close_mark_r": "0.375",
            "exit_policy_close_mark_time_utc": "2026-01-01T08:00:00+00:00",
            "exit_policy_close_mark_action": "CLOSE_TIME_STOP",
            "exit_policy_close_mark_close_reason": "v4_time_stop",
            "exit_policy_close_mark_bars_elapsed": "32",
            "exit_policy_close_mark_policy_id": "v4_exit_policy_close_mark_v1",
            "exit_policy_close_mark_source_status": "m15_close_mark_replay_bound",
        }
    )

    assert compact["source_record_candidate_id"] == "may26-candidate-id"
    assert compact["entry_touch_time_utc"] == "2026-01-01T00:15:00+00:00"
    assert compact["source_time_utc"] == "2026-01-01T00:00:00+00:00"
    assert compact["delayed_fill_bars"] == 1
    assert compact["dynamic_policy_transition_trace"]["pullback_from_mfe_r"] == 0.4
    assert compact["exit_policy_close_mark_r"] == "0.375"
    assert compact["exit_policy_close_mark_action"] == "CLOSE_TIME_STOP"


def test_day_session_microscope_aggregates_milestones_and_risk_status(tmp_path: Path) -> None:
    evaluated = evaluate_row(
        _row("day-session", asof="2026-01-01T00:00:00+00:00"),
        ReplayState(),
        _config(),
    )
    summary = ReplaySummary()
    summary.update(evaluated["result"])

    write_aggregate_ledgers(tmp_path, summary)
    stats = day_session_integrity_stats(tmp_path)
    rows = [
        json.loads(line)
        for line in (tmp_path / "WAVE4R_DAY_SESSION_MICROSCOPE_LEDGER.jsonl").read_text().splitlines()
    ]

    assert stats["rows"] == 1
    assert stats["missing_prop_risk_evidence_status"] == 0
    assert rows[0]["trade_date"] == "2026-01-01"
    assert rows[0]["prop_firm_risk_source_gap_rows"] == 0
    assert "prop_firm_replay_blocked_rows" in rows[0]
    assert "accepted_winners" in rows[0]
    assert "accepted_losers" in rows[0]
    assert "accepted_breakeven" in rows[0]
    assert "average_duration_minutes" in rows[0]


def test_limitations_backlog_materializes_system_fix_queue(tmp_path: Path) -> None:
    summary = {
        "processed_dynamic_policy_rows": 214536,
        "decision_windows": 73959,
        "multi_candidate_decision_windows": 46703,
        "max_decision_window_size": 58,
        "accepted_v4_simulated_rows": 14150,
        "zero_trade_or_rejected_rows": 200386,
        "positive_zero_trade_opportunity_cost_rows": 91664,
        "v4_total_proxy_r": 5580.259328736,
        "promoted_router_total_replay_r": 56872.791504935,
        "delta_v4_minus_promoted_router_total_r": -51292.532176199,
        "promoted_router_source_status_counts": {
            "may27_final_dynamic_router_replay_bound": 72115,
            "fallback_momentum_proxy_due_missing_promoted_router_row": 142421,
        },
        "same_bar_ambiguity_rows": 4263,
        "adverse_before_profit_rows": 100,
        "source_gap_rows": 1000,
        "prop_firm_replay_blocked_rows": 12,
    }
    for name, rows in {
        "WAVE4R_ACCEPTED_LOSER_FORENSIC_LEDGER.jsonl": 2,
        "WAVE4R_REJECTED_WINNER_OPPORTUNITY_LEDGER.jsonl": 3,
        "WAVE4R_SCHEDULER_ALLOCATION_REGRET_LEDGER.jsonl": 4,
        "WAVE4R_EXIT_HARVEST_COUNTERFACTUAL_LEDGER.jsonl": 5,
        "WAVE4R_DAY_SESSION_MICROSCOPE_LEDGER.jsonl": 6,
        "WAVE4R_ACTIONABLE_V4_REPAIR_FINDINGS_LEDGER.jsonl": 1,
    }.items():
        (tmp_path / name).write_text(
            "".join(json.dumps({"row": index}) + "\n" for index in range(rows)),
            encoding="utf-8",
        )

    write_limitations_and_fix_backlog(tmp_path, summary)
    stats = limitation_backlog_integrity_stats(tmp_path)
    backlog = json.loads((tmp_path / "WAVE4R_V4_LIMITATIONS_AND_FIX_BACKLOG.json").read_text())

    assert stats["rows"] >= 10
    assert stats["missing_required_areas"] == []
    assert stats["missing_fix_or_feature"] == 0
    assert stats["missing_production_code_ownership"] == 0
    assert stats["missing_tests_required"] == 0
    assert stats["implementation_required_rows"] == 0
    assert stats["source_capture_required_rows"] > 0
    assert stats["production_fix_rows"] > 0
    assert stats["microstructure_hydration_rows"] > 0
    assert stats["missing_storage_policy"] == 0
    assert stats["missing_scratch_pruning_policy"] == 0
    assert backlog["primary_comparator"] == "promoted_momentum_primary_partial_exception_router"
    assert backlog["refresh_status"] == "current_v4u_backlog_refresh_no_live_state_generation"
    assert "positive" in backlog["system_verdict"]
    assert "delete" in backlog["storage_policy"]["mt5_hydration_scratch"]
    statuses = {
        item["limitation_id"]: item["current_status"]
        for item in backlog["limitations"]
    }
    assert not any(status == "open_backlog" for status in statuses.values())
    assert statuses["same_symbol_lifecycle_needs_durable_ticket_thesis_state"].startswith(
        "implemented_runtime_durable_ticket_lifecycle_store"
    )
    assert statuses["intrabar_ordered_path_requires_m1_or_tick_export"].startswith(
        "source_capture_required_m1_tick_ltf_data_gated"
    )
    assert (
        "simulated replay prerequisite"
        in " ".join(backlog["fixable_data_or_execution_build_requirements"])
    )


def test_stale_thesis_scheduler_prefers_closing_existing_exposure() -> None:
    packet = allocate_decision_window(
        {
            "decision_window_id": "stale-window",
            "candidate_set_id": "stale-set",
            "asof_utc": "2026-01-01T00:00:00+00:00",
            "candidates": [],
            "open_positions": [
                {
                    "exposure_id": "ticket:1",
                    "symbol": "XAUUSD",
                    "side": "LONG",
                    "risk_pct": 1.0,
                    "stale_thesis_score": 0.9,
                    "time_in_trade_minutes": 1800,
                    "source_completeness": 0.9,
                }
            ],
            "pending_orders": [],
        },
        {"enabled": True, "apply_to_execution": True, "live_activation_allowed": True},
    )

    assert packet["decision"]["selected_action_class"] == "close_existing"


def test_replay_window_closes_stale_open_position_before_new_risk() -> None:
    state = ReplayState(
        open_positions=[
            ReplayPosition(
                ticket=1,
                candidate_id="old-thesis",
                symbol="XAUUSD",
                side="LONG",
                opened_at_utc="2025-12-30T00:00:00+00:00",
                exit_time_utc="2026-01-04T00:00:00+00:00",
                final_r=-1.0,
                risk_pct=2.0,
                probability=0.2,
                ev_r=-1.0,
                thesis_id="old-thesis",
                risk_r=1.0,
            )
        ]
    )
    evaluated = evaluate_window(
        [_row("fresh-window-opportunity", asof="2026-01-01T00:00:00+00:00")],
        state,
        _config(),
    )[0]
    result = evaluated["result"]

    assert result["scheduler_action"] == "close_existing"
    assert result["scheduler_selected_exposure_id"] == "ticket:1"
    assert result["branch_decision"] == "zero_trade_or_reject"
    assert result["scheduler_exposure_actions"][0]["candidate_id"] == "old-thesis"
    assert result["open_position_count_after_decision"] == 0
    assert state.open_positions == []


def test_stale_holding_ledger_records_replay_bound_scheduler_close(tmp_path: Path) -> None:
    state = ReplayState(
        open_positions=[
            ReplayPosition(
                ticket=1,
                candidate_id="old-thesis",
                symbol="XAUUSD",
                side="LONG",
                opened_at_utc="2025-12-30T00:00:00+00:00",
                exit_time_utc="2026-01-04T00:00:00+00:00",
                final_r=-1.0,
                risk_pct=2.0,
                probability=0.2,
                ev_r=-1.0,
                thesis_id="old-thesis",
                risk_r=1.0,
            )
        ]
    )
    evaluated = evaluate_window(
        [_row("ledger-stale-close", asof="2026-01-01T00:00:00+00:00")],
        state,
        _config(),
    )[0]

    with LedgerHandles(tmp_path) as ledgers:
        write_row_ledgers(ledgers, evaluated, state)

    stale_rows = [
        json.loads(line)
        for line in (tmp_path / "WAVE4R_STALE_HOLDINGS_THESIS_AGE_LEDGER.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]

    assert stale_rows[0]["stale_holding_source_status"] == (
        "scheduler_v4_stale_exposure_action_replay_bound"
    )
    assert stale_rows[0]["evidence_label"] == "chronological replay state proxy"
    assert stale_rows[0]["source_gaps"] == []


def test_stage05_activated_replay_row_recovers_missing_dynamic_shard_shape(tmp_path: Path) -> None:
    source = tmp_path / "activated_replay.jsonl.gz"
    row = {
        "candidate_id": "cand-recovered",
        "candle_time_utc": "2026-01-01 00:00:00",
        "entry_reference": 10.0,
        "framework": "fvg_fill",
        "path_row_id": "path1",
        "session_bucket": "ny_broad",
        "side": "LONG",
        "source_path": "source.csv",
        "source_sha256": "hash",
        "source_window_complete": True,
        "stop_or_invalidation": 9.0,
        "symbol": "XAUUSD",
        "bar_close_m15_path": {
            "entry_first_touch_utc": "2026-01-01T00:15:00Z",
            "terminal_order_raw": "TARGET_FIRST",
            "terminal_outcome": "target_first",
        },
        "dynamic_policy_replay": {
            "available": True,
            "observation_count": 4,
            "policy_results": {"legacy_fixed_1.5r": _policy(1.5, 1.6, -0.1, "2026-01-01T01:00:00+00:00")},
        },
    }

    recovered = stage05_dynamic_row(row, source_path=source, repo_root=tmp_path)

    assert recovered is not None
    assert recovered["candidate_id"] == "cand-recovered"
    assert recovered["policy_results"]["legacy_fixed_1.5r"]["final_r"] == 1.5
    assert recovered["_wave4r_recovery_status"] == "recovered_from_stage05_activated_replay_missing_stage04_dynamic_shard"


def test_session_bucket_is_bound_from_may26_dynamic_rows() -> None:
    assert row_session({"session_bucket": "london_broad"}) == "LONDON_BROAD"


def test_hard_halt_binding_rows_keep_broker_real_boundary(tmp_path: Path) -> None:
    wave4a = tmp_path / WAVE4A_ROOT
    wave4a.mkdir(parents=True)
    row = {
        "row_id": "broker-real-row",
        "symbol": "XAUUSD",
        "evidence_label": "broker-real PnL",
        "broker_real_cash": -12.34,
        "entry_first_touch_utc": "2026-01-01T00:00:00+00:00",
    }
    (wave4a / "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl").write_text(json.dumps(row) + "\n")
    (tmp_path / HARD_HALT_ROOT).mkdir(parents=True)

    rows = hard_halt_binding_rows(tmp_path, _config())

    assert rows
    assert rows[0]["broker_real_fields_allowed"] is True
    assert rows[0]["hard_boundary"]["broker_order_mutation"] is False
