from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace

from src.components.ultimate_book.admission import SizedUnit, TradeIntent, precount_intent_filter
from src.components.ultimate_book.book_owner import UltimateBookOwner
from src.components.ultimate_book.live_flow import GATE_ORDER, reconcile_live_flow_rows
from src.components.ultimate_book.order_router import UltimateBookOrderRouter
from src.components.ultimate_book.runtime_learning_packet import (
    RuntimeLearningPacketWriter,
    build_runtime_learning_packet,
    validate_runtime_learning_packet,
)


def _candidate_outcome(**extra):
    row = {
        "candidate_id": "W7_BOOK::metals::XAUUSD::2026-08-12::LONG::metals_core",
        "sleeve": "metals_core",
        "symbol": "XAUUSD",
        "direction": "LONG",
        "decision_bar_iso": "2026-08-12T08:00:00+00:00",
        "decision_day": "2026-08-12",
    }
    row.update(extra)
    return row


def test_production_and_f5_share_writer_but_keep_account_truth_separate(tmp_path):
    production = build_runtime_learning_packet(
        namespace="operator_profile",
        event_type="candidate_generated",
        outcome=_candidate_outcome(candidate_disposition="admission_unit_member"),
    )
    f5 = build_runtime_learning_packet(
        namespace="operator_profile_f5_minimal",
        event_type="candidate_generated",
        outcome=_candidate_outcome(
            candidate_disposition="admission_unit_member",
            f5_nominal_risk_usd=2000.0,
            f5_intended_risk_usd=10.0,
            f5_actual_risk_usd=10.21,
        ),
    )
    writer = RuntimeLearningPacketWriter(tmp_path)
    assert writer.append_many([production, f5]) == 2
    rows = [json.loads(line) for line in writer.path.read_text().splitlines()]

    assert {row["live_flow"]["surface"] for row in rows} == {"production", "f5_minimal"}
    assert rows[0]["live_flow"]["flow_id"] != rows[1]["live_flow"]["flow_id"]
    assert (
        rows[0]["live_flow"]["strategy_occurrence_id"]
        == rows[1]["live_flow"]["strategy_occurrence_id"]
    )
    assert rows[1]["live_flow"]["sizing"]["intended_risk_usd"] == 10.0


def test_gate_observations_are_sparse_and_never_fabricate_a_cleared_prefix():
    packet = build_runtime_learning_packet(
        namespace="operator_profile",
        event_type="unit_placed",
        outcome=_candidate_outcome(
            placement_status="placed",
            gtos_live_flow_execution={
                "request_status": "sent",
                "result_status": "success",
                "fill_status": "broker_fill_observed",
            },
        ),
    )
    observations = packet["live_flow"]["gate_observations"]
    assert [row["gate"] for row in observations] == [
        "broker_request",
        "broker_result",
        "broker_fill_reconciliation",
    ]
    assert not any(row["status"] == "cleared" for row in observations)
    assert packet["live_flow"]["gate_order_contract"] == list(GATE_ORDER)
    assert packet["live_flow"]["unobserved_gate_count"] == len(GATE_ORDER) - 3


def test_owner_emits_true_candidate_denominator_and_unit_member_join():
    owner = object.__new__(UltimateBookOwner)
    owner._namespace = "operator_profile"
    owner._convergence_advisory_enabled = False
    owner._convergence_advisory_log_enabled = False
    captured = []
    owner._append_runtime_learning_packets = lambda summary, packets: captured.extend(packets)

    sleeve = "metals_core"
    symbol = "XAUUSD"
    bar = "2026-08-12T08:00:00+00:00"
    unit = {
        "sleeve_members": [sleeve],
        "cluster": "metals",
        "risk_pct_per_trade": 0.005,
        "unit_risk_pct": 0.005,
        "sized": True,
        "reason": "ok",
    }
    decision = SimpleNamespace(
        realized_units=[unit],
        would_units=[unit],
        candidate_refusals=[],
        would_new_entries_allowed=True,
    )
    intents = [SimpleNamespace(
        sleeve=sleeve,
        symbol=symbol,
        direction=1,
        decision_day="2026-08-12",
    )]
    summary = {
        "ok": True,
        "reason": "ok",
        "runtime_effect_now": True,
        "bar_consumable": True,
        "bridge": {"runtime_effect_now": True, "n_candidates_in": 1, "n_candidates_after_drop": 1},
        "generation": {
            "active_symbol_slot_count": 1,
        },
        "generation_terminals": [{
            "sleeve": sleeve,
            "symbol": symbol,
            "timeframe": "H4",
            "terminal_status": "candidate_emitted",
            "decision_bar_iso": bar,
            "direction": 1,
        }],
        "skipped": [],
        "placed": [{
            "candidate_id": "W7_BOOK::metals::XAUUSD::2026-08-12::LONG::metals_core",
            "sleeve": sleeve,
            "symbol": symbol,
            "direction": "LONG",
            "decision_bar_iso": bar,
            "decision_day": "2026-08-12",
            "placement_observed_at_utc": "2026-08-12T08:01:00+00:00",
        }],
        "skip_context": owner._runtime_learning_skip_context(
            decision,
            intents,
            [{"tag": sleeve, "symbol": symbol, "decision_bar_iso": bar, "timeframe": "H4"}],
        ),
    }
    owner._emit_cycle_runtime_learning(
        summary,
        datetime(2026, 8, 12, 8, 1, tzinfo=timezone.utc),
        decision=decision,
        place=True,
    )

    assert [row["event_type"] for row in captured] == [
        "generation_cycle_complete",
        "candidate_generated",
        "unit_admitted",
        "unit_placed",
    ]
    generation_cycle, candidate, admitted, placed = captured
    assert generation_cycle["bridge"]["broker_profile_generation"][
        "active_symbol_slot_count"
    ] == len(generation_cycle["outcome"]["generation_slot_terminals"]) == 1
    assert generation_cycle["live_flow"]["event_disposition"] == "observed_complete"
    assert generation_cycle["live_flow"]["terminal_refusal_gate"] is None
    assert candidate["live_flow"]["denominator"]["candidate_disposition"] == "admission_unit_member"
    assert candidate["live_flow"]["flow_id"] in admitted["live_flow"]["member_flow_ids"]
    assert candidate["live_flow"]["flow_id"] == placed["live_flow"]["flow_id"]
    assert all(validate_runtime_learning_packet(row) == (True, []) for row in captured)
    report = reconcile_live_flow_rows(captured)
    assert report["status"] == "PASS", report
    assert report["counts"]["candidate_denominator_flows"] == 1
    assert report["counts"]["candidate_flows_resolved"] == 1
    assert report["counts"]["generation_cycles"] == 1
    assert report["counts"]["generation_expected_slots"] == 1
    assert report["counts"]["generation_terminal_slots"] == 1
    assert report["counts"]["generation_emitted_slots_missing_candidate_packet"] == 0


def test_generation_cycle_reconciliation_exposes_missing_candidate_and_duplicate_slots():
    ts = "2026-08-12T08:01:00+00:00"
    terminal = {
        "sleeve": "metals_core",
        "symbol": "XAUUSD",
        "timeframe": "H4",
        "terminal_status": "candidate_emitted",
        "decision_bar_iso": "2026-08-12T08:00:00+00:00",
        "direction": "LONG",
    }
    generation = build_runtime_learning_packet(
        namespace="operator_profile",
        event_type="generation_cycle_complete",
        ts=ts,
        bridge={"broker_profile_generation": {"active_symbol_slot_count": 1}},
        outcome={
            "generation_slot_terminals": [terminal],
        },
    )
    assert validate_runtime_learning_packet(generation) == (True, [])

    missing = reconcile_live_flow_rows([generation])
    assert missing["status"] == "FAIL"
    assert missing["counts"]["generation_emitted_slots_missing_candidate_packet"] == 1
    assert any(
        issue.get("issue") == "emitted_generation_slot_without_candidate_packet"
        for issue in missing["issues"]
    )

    duplicate = build_runtime_learning_packet(
        namespace="operator_profile",
        event_type="generation_cycle_complete",
        ts=ts,
        bridge={"broker_profile_generation": {"active_symbol_slot_count": 2}},
        outcome={
            "generation_slot_terminals": [terminal, dict(terminal)],
        },
    )
    valid, validation_issues = validate_runtime_learning_packet(duplicate)
    assert valid is False
    assert "generation_terminal_slot_keys_not_unique" in validation_issues
    duplicate_report = reconcile_live_flow_rows([duplicate])
    assert duplicate_report["status"] == "FAIL"
    assert any(
        issue.get("issue") == "generation_terminal_slot_keys_not_unique"
        for issue in duplicate_report["issues"]
    )


def test_exact_admission_filter_refusal_reaches_candidate_packet():
    intent = TradeIntent(
        sleeve="metals_core",
        symbol="XAUUSD",
        direction=1,
        decision_day="2026-08-12",
        stop_dist=10.0,
    )
    refusals = []
    kept = precount_intent_filter(
        [intent],
        learning_rerate={"metals_core": 0.0},
        candidate_refusal_sink=refusals,
    )
    assert kept == []
    assert refusals == [{
        "sleeve": "metals_core",
        "symbol": "XAUUSD",
        "direction": 1,
        "decision_day": "2026-08-12",
        "candidate_disposition": "refused",
        "candidate_disposition_gate": "book_admission_and_sizing",
        "candidate_disposition_reason": "learning_rerate_gate_zero",
    }]

    packet = build_runtime_learning_packet(
        namespace="operator_profile",
        event_type="candidate_generated",
        outcome=_candidate_outcome(**refusals[0]),
    )
    admission = [
        row for row in packet["live_flow"]["gate_observations"]
        if row["gate"] == "book_admission_and_sizing"
    ]
    assert admission == [{
        "order": 2,
        "gate": "book_admission_and_sizing",
        "status": "refused",
        "evidence": "outcome.reason",
    }]


def test_owner_candidate_context_joins_exact_admission_refusal_to_decision_bar():
    owner = object.__new__(UltimateBookOwner)
    decision = SimpleNamespace(
        realized_units=[],
        would_units=[],
        would_new_entries_allowed=True,
        candidate_refusals=[{
            "sleeve": "metals_core",
            "symbol": "XAUUSD",
            "direction": 1,
            "decision_day": "2026-08-12",
            "candidate_disposition": "refused",
            "candidate_disposition_gate": "book_admission_and_sizing",
            "candidate_disposition_reason": "learning_rerate_gate_zero",
        }],
    )
    contexts = owner._runtime_learning_skip_context(
        decision,
        [SimpleNamespace(
            sleeve="metals_core",
            symbol="XAUUSD",
            direction=1,
            decision_day="2026-08-12",
        )],
        [{
            "tag": "metals_core",
            "symbol": "XAUUSD",
            "decision_bar_iso": "2026-08-12T08:00:00+00:00",
            "timeframe": "H4",
        }],
    )
    context = next(iter(contexts.values()))
    assert context["candidate_disposition_reason"] == "learning_rerate_gate_zero"
    assert context["candidate_disposition_evidence"] == "exact_predicate_capture"
    assert context["decision_bar_iso"] == "2026-08-12T08:00:00+00:00"


class _Tick:
    bid = 2999.7
    ask = 3000.0


def _router_inputs():
    unit = SizedUnit(
        cluster="metals",
        sleeve_members=("metals_core",),
        n_trades=1,
        confidence=1.0,
        risk_pct_per_trade=0.005,
        unit_risk_pct=0.005,
        sized=True,
        reason="ok",
    )
    intent = TradeIntent(
        sleeve="metals_core",
        symbol="XAUUSD",
        direction=1,
        decision_day="2026-08-12",
        stop_dist=10.0,
    )
    account = {
        "current_equity": 100000.0,
        "balance": 100000.0,
        "account_login": 123456,
        "day_start_equity_or_balance_baseline": 100000.0,
        "daily_reset_window_id": "2026-08-12",
    }
    return unit, intent, account


def test_router_execution_observation_survives_placed_refused_and_exception_paths():
    router = UltimateBookOrderRouter({}, namespace="operator_profile")
    unit, intent, account = _router_inputs()

    class PlacedEngine:
        def open_trade(self, trade_params, _balance, **_kwargs):
            self._last_order_send_diagnostic = {
                "status": "success",
                "request": {"symbol": "XAUUSD", "volume": 0.21, "price": 3000.0},
                "result": {"success": True, "order": 987, "deal": 654, "price": 3000.2, "volume": 0.21},
                "symbol_info": {"available": True, "volume_min": 0.01, "volume_step": 0.01},
                "tick": {"bid": 2999.7, "ask": 3000.0},
            }
            return SimpleNamespace(
                ticket=987,
                entry_price=3000.2,
                sl_distance=10.0,
                initial_volume=0.21,
                cash_risk_amount=210.0,
                cash_risk_amount_status="BROKER_ORDER_CALC_PROFIT_VERIFIED",
            )

    placed = router.place(PlacedEngine(), unit, intent, _Tick(), account, 100000.0)
    placed_ctx = UltimateBookOwner._runtime_learning_router_result_context(placed)
    assert placed_ctx["gtos_live_flow_execution"]["request_status"] == "sent"
    assert placed_ctx["gtos_live_flow_execution"]["fill_status"] == "broker_fill_observed"
    assert "order_ticket" in placed_ctx["gtos_live_flow_execution"]["result"]

    class RefusedEngine:
        def open_trade(self, _trade_params, _balance, **_kwargs):
            self._last_open_trade_block_reason = "order_rejected:no_money"
            self._last_order_send_diagnostic = {
                "status": "order_rejected",
                "request": {"symbol": "XAUUSD", "volume": 0.21, "price": 3000.0},
                "result": {"success": False, "retcode": 10019, "comment": "no_money"},
                "symbol_info": {"available": True, "volume_min": 0.01, "volume_step": 0.01},
                "tick": {"bid": 2999.7, "ask": 3000.0},
            }
            return None

    refused = router.place(RefusedEngine(), unit, intent, _Tick(), account, 100000.0)
    refused_ctx = UltimateBookOwner._runtime_learning_router_result_context(refused)
    assert refused_ctx["gtos_live_flow_execution"]["request_status"] == "sent"
    assert refused_ctx["gtos_live_flow_execution"]["result"]["retcode"] == 10019

    class ExplodingEngine:
        def open_trade(self, _trade_params, _balance, **_kwargs):
            raise RuntimeError("broker adapter unavailable")

    failed = router.place(ExplodingEngine(), unit, intent, _Tick(), account, 100000.0)
    failed_ctx = UltimateBookOwner._runtime_learning_router_result_context(failed)
    assert failed["reason"].startswith("router_exception:")
    assert failed_ctx["gtos_live_flow_execution"]["request_status"] == "not_reached"
    assert failed_ctx["gtos_live_flow_execution"]["result_status"] == "not_reached"
    assert failed_ctx["gtos_live_flow_execution"]["pre_request_status"].startswith(
        "router_exception:"
    )
    failed_packet = build_runtime_learning_packet(
        namespace="operator_profile",
        event_type="unit_skipped",
        decision_bar_iso="2026-08-12T08:00:00+00:00",
        outcome={**_candidate_outcome(), **failed_ctx, "reason": failed["reason"]},
    )
    assert failed_packet["live_flow"]["gate_observations"] == []
    assert failed_packet["live_flow"]["event_disposition"] == "refused_unclassified"
    assert validate_runtime_learning_packet(failed_packet) == (True, [])

    refused_packet = build_runtime_learning_packet(
        namespace="operator_profile",
        event_type="unit_skipped",
        decision_bar_iso="2026-08-12T08:00:00+00:00",
        outcome={**_candidate_outcome(), **refused_ctx, "reason": refused["reason"]},
    )
    result = refused_packet["live_flow"]["broker"]["result"]
    assert "order_ticket" not in result
    assert validate_runtime_learning_packet(refused_packet) == (True, [])


def test_reconciler_reports_every_missing_candidate_without_top_n_suppression():
    rows = [
        build_runtime_learning_packet(
            namespace="operator_profile",
            event_type="candidate_generated",
            outcome={
                **_candidate_outcome(
                    candidate_id=f"candidate-{index}",
                    symbol=f"SYM{index}",
                    candidate_disposition="unresolved_after_generation",
                )
            },
        )
        for index in range(17)
    ]
    report = reconcile_live_flow_rows(rows)
    assert report["status"] == "FAIL"
    assert report["counts"]["candidate_flows_missing_disposition"] == 17
    missing = [issue for issue in report["issues"] if issue.get("issue") == "candidate_without_downstream_disposition"]
    assert len(missing) == 17
