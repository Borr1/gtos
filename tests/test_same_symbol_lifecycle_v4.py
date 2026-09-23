from __future__ import annotations

import pickle
from datetime import datetime, timezone
from types import SimpleNamespace

from src.components.permissions import check_permissions
from src.components.same_symbol_lifecycle_v4 import (
    PendingLifecycleSnapshot,
    TicketLifecycleSnapshot,
    build_candidate_lifecycle_context,
    evaluate_same_symbol_lifecycle_v4,
    load_same_symbol_lifecycle_store,
    load_same_symbol_pending_intents,
    record_same_symbol_lifecycle_entry_v4,
    symbol_aliases_for_config,
)
from src.mt5.mt5_interface import MAGIC_NUMBER, PositionInfo
from src.mt5.mt5_mock import MockMT5


def _candidate(
    *,
    symbol: str = "XAUUSD",
    side: str = "LONG",
    action: str | None = None,
    risk_pct: float | None = 0.25,
    probability: float | None = 0.66,
    ev_r: float | None = 0.35,
    thesis_id: str | None = "thesis-xau-london-continuation",
    candidate_id: str | None = "candidate-xau-london-continuation",
    poi_id: str | None = None,
    poi_state_hash_sha256: str | None = None,
):
    tp = SimpleNamespace(
        candidate_id=candidate_id,
        direction=side,
        entry_price=2652.0,
        stop_loss=2642.0,
        risk_reward_ratio=2.0,
        take_profit_1=2672.0,
        gtos_vnext_production_execution_path=True,
        gtos_vnext_dynamic_policy_applied=True,
        gtos_vnext_dynamic_policy_selected="momentum_exhaustion",
        gtos_vnext_execution_policy_id="unit-momentum-policy",
        gtos_vnext_selected_cell_risk_pct=risk_pct,
        gtos_vnext_selected_cell_risk_cell_id="risk-cell-xau",
        gtos_vnext_probability=probability,
        gtos_vnext_expected_value_r=ev_r,
        gtos_vnext_thesis_id=thesis_id,
        gtos_vnext_same_symbol_lifecycle_action=action,
        poi_id=poi_id,
        poi_state_hash_sha256=poi_state_hash_sha256,
    )
    return build_candidate_lifecycle_context(
        symbol=symbol,
        aliases=[symbol],
        trade_params=SimpleNamespace(trade_parameters=tp),
        proof={"selected_cell_risk_pct": risk_pct},
    )


def _position(
    *,
    ticket: int = 1001,
    symbol: str = "XAUUSD",
    side: str = "LONG",
    risk_pct: float | None = 0.25,
    probability_at_entry: float | None = 0.58,
    ev_r_at_entry: float | None = 0.20,
    thesis_id: str | None = "thesis-xau-london-continuation",
    phase: str = "open",
):
    position = SimpleNamespace(
        ticket=ticket,
        symbol=symbol,
        type=0 if side == "LONG" else 1,
        volume=0.10,
        price_open=2650.0,
        sl=2640.0,
        tp=2670.0,
        profit=0.0,
        magic=MAGIC_NUMBER,
        comment="unit",
        gtos_vnext_selected_cell_risk_pct=risk_pct,
        gtos_vnext_probability_at_entry=probability_at_entry,
        gtos_vnext_ev_r_at_entry=ev_r_at_entry,
        gtos_vnext_thesis_id=thesis_id,
        gtos_vnext_lifecycle_phase=phase,
    )
    return TicketLifecycleSnapshot.from_position(position)


def _decision(candidate, positions=(), pending=(), config=None):
    return evaluate_same_symbol_lifecycle_v4(
        candidate=candidate,
        open_positions=list(positions),
        pending_orders=list(pending),
        config=config or {"same_symbol_lifecycle_v4": {"pending_intent_source_enabled": False}},
    )


def test_new_position_allowed_when_no_same_symbol_exposure():
    decision = _decision(_candidate())

    assert decision.permitted_order_intent is True
    assert decision.action == "new_position"
    assert decision.reason == "no_same_symbol_open_or_pending_exposure"


def test_symbol_aliases_do_not_import_unrelated_root_market_symbol():
    config = {
        "market": {"symbol": "XAUUSD"},
        "instruments": {
            "GBPJPY": {"market": {"symbol": "GBPJPY"}},
            "GER40": {"market": {"symbol": "GER40", "mt5_symbol": "GER30"}},
            "XAUUSD": {"market": {"symbol": "XAUUSD"}},
        },
    }

    assert symbol_aliases_for_config("GBPJPY", config) == ["GBPJPY"]
    assert "XAUUSD" in symbol_aliases_for_config("XAUUSD", config)
    assert set(symbol_aliases_for_config("GER40", config)) >= {"GER40", "GER30"}


def test_same_direction_without_explicit_scale_is_duplicate_rejected():
    decision = _decision(_candidate(action=None), [_position()])

    assert decision.permitted_order_intent is False
    assert decision.action == "no_trade_duplicate"
    assert decision.reason == "same_symbol_same_direction_requires_explicit_scale_in_action"
    assert decision.rejected_alternatives[0]["action"] == "same_direction_scale_in"


def test_same_direction_scale_in_passes_with_ticket_bound_thesis_risk_and_metrics():
    decision = _decision(_candidate(action="same_direction_scale_in"), [_position()])
    packet = decision.to_packet()

    assert decision.permitted_order_intent is True
    assert decision.action == "same_direction_scale_in"
    assert decision.parent_ticket == 1001
    assert decision.scale_in_risk_delta_pct == 0.25
    assert packet["broker_local_risk_result"]["total_risk_pct"] == 0.5
    assert packet["broker_local_risk_result"]["probability_delta"] > 0.03
    assert packet["broker_local_risk_result"]["ev_delta_r"] > 0.05
    assert packet["durable_lifecycle_capture"]["status"] == "complete"
    assert len(packet["durable_lifecycle_capture"]["capture_hash_sha256"]) == 64
    assert len(packet["source_event_hash_sha256"]) == 64
    assert len(packet["packet_hash_sha256"]) == 64


def test_same_symbol_missing_candidate_id_fails_durable_capture_contract():
    decision = _decision(_candidate(candidate_id=None))
    packet = decision.to_packet()

    assert decision.permitted_order_intent is False
    assert decision.action == "source_required_fail_closed"
    assert decision.reason == "same_symbol_candidate_durable_lifecycle_capture_missing"
    assert "candidate.candidate_id" in packet["durable_lifecycle_capture"]["missing_fields"]
    assert any(
        veto["veto"] == "durable_candidate_lifecycle_capture_missing"
        for veto in packet["vetoes"]
    )


def test_same_direction_scale_in_fails_closed_when_existing_risk_source_missing():
    decision = _decision(
        _candidate(action="scale_in"),
        [_position(risk_pct=None)],
    )

    assert decision.permitted_order_intent is False
    assert decision.action == "source_required_fail_closed"
    assert any(v["veto"] == "broker_local_risk_source_missing" for v in decision.vetoes)


def test_stale_thesis_ticket_vetoes_same_direction_scale_in():
    decision = _decision(
        _candidate(action="scale_in"),
        [_position(phase="stale_thesis")],
    )

    assert decision.permitted_order_intent is False
    assert any(v["veto"] == "existing_ticket_not_scale_eligible" for v in decision.vetoes)
    assert decision.to_packet()["open_position_snapshot"][0]["lifecycle_phase"] == "stale_thesis"


def test_empty_comment_broker_position_hydrates_from_durable_lifecycle_store():
    store = {
        "schema_version": "same_symbol_lifecycle_v4_store_v1",
        "tickets": {
            "1001": {
                "ticket": 1001,
                "symbol": "XAUUSD",
                "side": "LONG",
                "magic": MAGIC_NUMBER,
                "thesis_id": "thesis-xau-london-continuation",
                "risk_pct": 0.25,
                "probability_at_entry": 0.58,
                "ev_r_at_entry": 0.20,
                "lifecycle_phase": "open",
                "source_status": "durable_same_symbol_lifecycle_store_v4",
                "partial_state": "not_partial",
                "be_state": "initial_stop",
                "trailing_state": "not_trailing",
            }
        },
    }
    broker_position = SimpleNamespace(
        ticket=1001,
        symbol="XAUUSD",
        type=0,
        volume=0.10,
        price_open=2650.0,
        sl=2640.0,
        tp=2670.0,
        profit=0.0,
        magic=MAGIC_NUMBER,
        comment="",
    )

    hydrated = TicketLifecycleSnapshot.from_position(
        broker_position,
        lifecycle_store=store,
    )
    decision = _decision(_candidate(action="same_direction_scale_in"), [hydrated])
    packet = decision.to_packet()

    assert hydrated.thesis_id == "thesis-xau-london-continuation"
    assert hydrated.risk_pct == 0.25
    assert hydrated.probability_at_entry == 0.58
    assert hydrated.ev_r_at_entry == 0.20
    assert hydrated.source_status == "broker_position_snapshot_with_durable_lifecycle_store"
    assert decision.permitted_order_intent is True
    assert decision.action == "same_direction_scale_in"
    assert packet["durable_lifecycle_capture"]["status"] == "complete"


def test_partial_be_trailing_ticket_state_is_preserved_in_decision_packet():
    position = SimpleNamespace(
        ticket=1002,
        symbol="XAUUSD",
        type=0,
        volume=0.05,
        price_open=2650.0,
        sl=2650.0,
        tp=2670.0,
        profit=25.0,
        magic=MAGIC_NUMBER,
        comment="unit",
        gtos_vnext_selected_cell_risk_pct=0.25,
        gtos_vnext_probability_at_entry=0.58,
        gtos_vnext_ev_r_at_entry=0.20,
        gtos_vnext_thesis_id="thesis-xau-london-continuation",
        gtos_vnext_lifecycle_phase="trailing",
        partial_state="partial_closed_residual_open",
        be_state="sl_moved_to_be",
        trailing_state="trailing_active",
    )

    decision = _decision(
        _candidate(action=None),
        [TicketLifecycleSnapshot.from_position(position)],
    )
    snapshot = decision.to_packet()["open_position_snapshot"][0]

    assert decision.action == "no_trade_duplicate"
    assert snapshot["partial_state"] == "partial_closed_residual_open"
    assert snapshot["be_state"] == "sl_moved_to_be"
    assert snapshot["trailing_state"] == "trailing_active"
    assert snapshot["lifecycle_phase"] == "trailing"


def test_opposite_direction_requires_close_or_reverse_before_new_order():
    decision = _decision(
        _candidate(side="SHORT", action="close_and_reverse", thesis_id="reverse-thesis"),
        [_position(side="LONG")],
    )

    assert decision.permitted_order_intent is False
    assert decision.action == "close_and_reverse"
    assert decision.close_ticket == 1001
    assert decision.reverse_intent_id == "candidate-xau-london-continuation"
    assert decision.reason == "same_symbol_close_reduce_reverse_requires_execution_manager_before_new_order"


def test_pending_same_symbol_blocks_duplicate_and_preserves_pending_snapshot(tmp_path):
    pending = SimpleNamespace(
        trade_id="lim_2026-06-04_1200",
        source_symbol="XAUUSD",
        direction="LONG",
        limit_price=2651.0,
        stop_loss=2641.0,
        take_profit_1=2671.0,
        gtos_vnext_selected_cell_risk_pct=0.25,
        placed_time="2026-06-04T12:00:00+00:00",
        expiry_candles=12,
        broker_pending_order_created=False,
        mt5_order_ticket=None,
        native_pending_order_type=None,
    )
    path = tmp_path / "pending_intent_XAUUSD.pkl"
    path.write_bytes(pickle.dumps(pending))
    source = load_same_symbol_pending_intents(
        symbol="XAUUSD",
        aliases=["XAUUSD"],
        config={
            "same_symbol_lifecycle_v4": {
                "pending_intent_dir": str(tmp_path),
            },
        },
    )

    decision = _decision(_candidate(), pending=source.snapshots)

    assert source.source_errors == []
    assert decision.permitted_order_intent is False
    assert decision.action == "no_trade_duplicate"
    assert decision.to_packet()["pending_order_snapshot"][0]["pending_id"] == (
        "lim_2026-06-04_1200"
    )


def test_pending_same_poi_blocks_reused_candidate_instance_by_poi_identity():
    pending = PendingLifecycleSnapshot(
        pending_id="pending-old-instance",
        source_path="unit://pending-old-instance",
        symbol="XAUUSD",
        side="LONG",
        entry_price=2651.0,
        stop_loss=2641.0,
        take_profit_1=2671.0,
        risk_pct=0.25,
        created_time_utc="2026-06-04T12:00:00+00:00",
        expiry_candles=12,
        broker_pending_order_created=False,
        mt5_order_ticket=None,
        native_pending_order_type=None,
        source_status="unit_test",
        candidate_id="candidate-prior-decision-instance",
        decision_time_utc="2026-06-04T12:00:00+00:00",
        poi_id="poi_stable_fvg_1",
        poi_state_hash_sha256="a" * 64,
    )
    decision = _decision(
        _candidate(
            candidate_id="candidate-current-decision-instance",
            poi_id="poi_stable_fvg_1",
            poi_state_hash_sha256="b" * 64,
        ),
        pending=[pending],
    )

    assert decision.permitted_order_intent is False
    assert decision.reason == "same_poi_pending_reuse_blocks_duplicate_candidate_instance"
    assert decision.to_packet()["broker_local_risk_result"]["same_poi_pending_count"] == 1


def test_pending_distinct_poi_keeps_normal_same_symbol_conflict_semantics():
    pending = PendingLifecycleSnapshot(
        pending_id="pending-distinct-poi",
        source_path="unit://pending-distinct-poi",
        symbol="XAUUSD",
        side="LONG",
        entry_price=2651.0,
        stop_loss=2641.0,
        take_profit_1=2671.0,
        risk_pct=0.25,
        created_time_utc="2026-06-04T12:00:00+00:00",
        expiry_candles=12,
        broker_pending_order_created=False,
        mt5_order_ticket=None,
        native_pending_order_type=None,
        source_status="unit_test",
        candidate_id="candidate-prior",
        decision_time_utc="2026-06-04T12:00:00+00:00",
        poi_id="poi_other_fvg",
        poi_state_hash_sha256="a" * 64,
    )
    decision = _decision(
        _candidate(
            candidate_id="candidate-current",
            poi_id="poi_new_fvg",
            poi_state_hash_sha256="b" * 64,
        ),
        pending=[pending],
    )

    assert decision.permitted_order_intent is False
    assert decision.reason == "same_symbol_pending_conflict_blocks_new_or_scale_order"
    assert decision.to_packet()["broker_local_risk_result"]["same_poi_pending_count"] == 0


def test_pending_replace_action_routes_to_pending_manager_before_order(tmp_path):
    pending = SimpleNamespace(
        trade_id="lim_2026-06-04_1215",
        source_symbol="XAUUSD",
        direction="LONG",
        limit_price=2651.0,
        stop_loss=2641.0,
        take_profit_1=2671.0,
        gtos_vnext_selected_cell_risk_pct=0.25,
        placed_time="2026-06-04T12:15:00+00:00",
    )
    path = tmp_path / "pending_intent_XAUUSD.pkl"
    path.write_bytes(pickle.dumps(pending))
    source = load_same_symbol_pending_intents(
        symbol="XAUUSD",
        aliases=["XAUUSD"],
        config={
            "same_symbol_lifecycle_v4": {
                "pending_intent_dir": str(tmp_path),
            },
        },
    )

    decision = _decision(_candidate(action="replace_pending"), pending=source.snapshots)

    assert decision.permitted_order_intent is False
    assert decision.action == "replace_pending"
    assert decision.reason == (
        "same_symbol_pending_lifecycle_action_requires_pending_manager_before_order"
    )


def test_replay_pending_snapshot_created_time_alias_preserves_lifecycle_authority():
    pending = PendingLifecycleSnapshot.from_intent(
        {
            "pending_id": "order-xau-0515",
            "candidate_id": "candidate-xau-0515",
            "symbol": "XAUUSD",
            "side": "LONG",
            "entry_price": 2651.0,
            "stop_loss": 2641.0,
            "take_profit_1": 2671.0,
            "risk_pct": 0.25,
            "created_time_utc": "2026-05-13T05:00:00+00:00",
            "native_pending_order_type": "simulated_limit",
        },
        source_path="timewarp_simulated_account_pending_state",
        source_status="simulated_replay_pending_intent_read",
    )

    decision = _decision(_candidate(action="replace_pending"), pending=[pending])

    assert decision.action == "replace_pending"
    assert decision.reason == (
        "same_symbol_pending_lifecycle_action_requires_pending_manager_before_order"
    )
    packet = decision.to_packet()
    assert packet["source_completeness"].get("durable_capture_missing_fields") in (
        None,
        [],
    )
    assert packet["pending_order_snapshot"][0]["pending_id"] == "order-xau-0515"
    assert packet["pending_order_snapshot"][0]["created_time_utc"] == (
        "2026-05-13T05:00:00+00:00"
    )


def test_candidate_lifecycle_bridge_reads_outer_signed_identity_surface():
    lifecycle_hash = "b" * 64
    lifecycle = {
        "poi_lifecycle_state": "unmitigated",
        "scheduler_rankable_now": True,
        "lifecycle_hash_sha256": lifecycle_hash,
    }
    nested = SimpleNamespace(
        candidate_id="candidate-outer-lifecycle",
        direction="LONG",
        gtos_vnext_selected_cell_risk_pct=0.25,
        gtos_vnext_probability=0.72,
        gtos_vnext_expected_value_r=0.45,
        gtos_vnext_thesis_id="thesis-outer-lifecycle",
    )
    wrapped = SimpleNamespace(
        trade_parameters=nested,
        poi_id="poi-outer-lifecycle",
        poi_state_hash_sha256="a" * 64,
        causal_poi_lifecycle_required=True,
        causal_poi_lifecycle=lifecycle,
        causal_poi_lifecycle_hash_sha256=lifecycle_hash,
        canonical_replay_candidate_instance_key="candidate-outer-lifecycle@@t0",
        source_bound_replay_candidate_instance_key="candidate-outer-lifecycle@@t0",
        candidate_instance_identity_status="materialized",
    )

    candidate = build_candidate_lifecycle_context(
        symbol="XAUUSD",
        aliases=["XAUUSD"],
        trade_params=wrapped,
    )

    assert candidate.poi_id == "poi-outer-lifecycle"
    assert candidate.causal_poi_lifecycle == lifecycle
    assert candidate.causal_poi_lifecycle_hash_sha256 == lifecycle_hash
    assert candidate.canonical_replay_candidate_instance_key == (
        "candidate-outer-lifecycle@@t0"
    )
    assert candidate.candidate_instance_identity_status == "materialized"


def test_terminal_same_poi_candidate_requires_exact_pending_cancel():
    poi_id = "poi-terminal-pending"
    lifecycle_hash = "c" * 64
    nested = SimpleNamespace(
        candidate_id="candidate-terminal-pending",
        direction="LONG",
        gtos_vnext_selected_cell_risk_pct=0.25,
        gtos_vnext_probability=0.72,
        gtos_vnext_expected_value_r=0.45,
        gtos_vnext_thesis_id="thesis-terminal-pending",
    )
    candidate = build_candidate_lifecycle_context(
        symbol="XAUUSD",
        aliases=["XAUUSD"],
        trade_params=SimpleNamespace(
            trade_parameters=nested,
            poi_id=poi_id,
            causal_poi_lifecycle_required=True,
            causal_poi_lifecycle={
                "poi_lifecycle_state": "invalidated",
                "scheduler_rankable_now": False,
                "lifecycle_hash_sha256": lifecycle_hash,
            },
            causal_poi_lifecycle_hash_sha256=lifecycle_hash,
        ),
    )
    pending = PendingLifecycleSnapshot.from_intent(
        {
            "pending_id": "pending-terminal-poi",
            "candidate_id": "older-candidate",
            "symbol": "XAUUSD",
            "side": "LONG",
            "entry_price": 2651.0,
            "stop_loss": 2641.0,
            "take_profit_1": 2671.0,
            "risk_pct": 0.25,
            "created_time_utc": "2026-05-13T05:00:00+00:00",
            "poi_id": poi_id,
            "causal_poi_lifecycle_hash_sha256": "d" * 64,
        },
        source_path="timewarp_simulated_account_pending_state",
    )

    decision = _decision(candidate, pending=[pending])
    packet = decision.to_packet()

    assert decision.permitted_order_intent is False
    assert decision.action == "cancel_pending"
    assert decision.reason == "terminal_poi_requires_pending_cancel_by_stable_poi_id"
    assert packet["broker_local_risk_result"]["matching_pending_ids"] == [
        "pending-terminal-poi"
    ]


def test_opposite_pending_snapshot_routes_to_replace_pending_manager():
    pending = PendingLifecycleSnapshot.from_intent(
        {
            "pending_id": "order-xau-short",
            "symbol": "XAUUSD",
            "side": "SHORT",
            "entry_price": 2648.0,
            "stop_loss": 2658.0,
            "take_profit_1": 2628.0,
            "risk_pct": 0.25,
            "created_time_utc": "2026-05-13T05:00:00+00:00",
            "native_pending_order_type": "simulated_limit",
        },
        source_path="timewarp_simulated_account_pending_state",
        source_status="simulated_replay_pending_intent_read",
    )

    decision = _decision(_candidate(side="LONG"), pending=[pending])

    assert decision.permitted_order_intent is False
    assert decision.action == "replace_pending"
    assert decision.reason == (
        "same_symbol_opposite_pending_requires_pending_manager_before_order"
    )
    assert decision.to_packet()["broker_local_risk_result"] == {
        "status": "opposite_pending_risk_reserved_requires_replacement",
        "pending_risk_pct": 0.25,
        "opposite_pending_count": 1,
    }


def test_pending_intent_loader_checks_broker_namespace_and_alias(tmp_path):
    pending = SimpleNamespace(
        trade_id="lim-nas",
        source_symbol="NDX100",
        direction="SHORT",
        limit_price=30100.0,
        stop_loss=30200.0,
        take_profit_1=29900.0,
        placed_time="2026-06-04T12:30:00+00:00",
    )
    path = tmp_path / "pending_intent_NAS100_ftmo_test.pkl"
    path.write_bytes(pickle.dumps(pending))

    source = load_same_symbol_pending_intents(
        symbol="NAS100",
        aliases=["NAS100", "NDX100"],
        config={
            "runtime": {"broker_account_namespace": "FTMO Test"},
            "same_symbol_lifecycle_v4": {
                "pending_intent_dir": str(tmp_path),
            },
        },
    )

    assert source.source_errors == []
    assert len(source.snapshots) == 1
    assert source.snapshots[0].symbol == "NDX100"


def _permission_pa(
    *,
    side: str = "LONG",
    action: str | None = "same_direction_scale_in",
    probability: float = 0.66,
    ev_r: float = 0.35,
    thesis_id: str = "thesis-xau-london-continuation",
):
    tp = SimpleNamespace(
        candidate_id="permission-candidate-xau",
        direction=side,
        entry_price=2652.0,
        stop_loss=2642.0,
        risk_reward_ratio=2.0,
        take_profit_1=2672.0,
        gtos_vnext_production_execution_path=True,
        gtos_vnext_dynamic_policy_applied=True,
        gtos_vnext_dynamic_policy_selected="momentum_exhaustion",
        gtos_vnext_execution_policy_id="unit-momentum-policy",
        gtos_vnext_selected_cell_risk_pct=0.25,
        gtos_vnext_selected_cell_risk_cell_id="risk-cell-xau",
        gtos_vnext_probability=probability,
        gtos_vnext_expected_value_r=ev_r,
        gtos_vnext_thesis_id=thesis_id,
        gtos_vnext_same_symbol_lifecycle_action=action,
    )
    reasoning = SimpleNamespace(
        setup_grade="A+",
        daily_bias=SimpleNamespace(direction="bullish"),
    )
    return SimpleNamespace(reasoning=reasoning, trade_parameters=tp)


def _permission_config(tmp_path):
    return {
        "deployment": {"phase": 3},
        "risk": {
            "max_spread_cents": 100,
            "same_symbol_lifecycle_v4": {
                "pending_intent_dir": str(tmp_path),
            },
        },
    }


def _mt5_position(side: str = "LONG") -> PositionInfo:
    position = PositionInfo(
        ticket=7001,
        symbol="XAUUSD",
        type=0 if side == "LONG" else 1,
        volume=0.10,
        price_open=2650.0,
        sl=2640.0,
        tp=2670.0,
        profit=0.0,
        magic=MAGIC_NUMBER,
        comment="unit",
        time=datetime.now(timezone.utc),
    )
    position.gtos_vnext_selected_cell_risk_pct = 0.25
    position.gtos_vnext_probability_at_entry = 0.58
    position.gtos_vnext_ev_r_at_entry = 0.20
    position.gtos_vnext_thesis_id = "thesis-xau-london-continuation"
    return position


def _mt5_position_without_v4_comment(side: str = "LONG") -> PositionInfo:
    return PositionInfo(
        ticket=7001,
        symbol="XAUUSD",
        type=0 if side == "LONG" else 1,
        volume=0.10,
        price_open=2650.0,
        sl=2640.0,
        tp=2670.0,
        profit=0.0,
        magic=MAGIC_NUMBER,
        comment="",
        time=datetime.now(timezone.utc),
    )


def test_permissions_allows_v4_same_direction_scale_in_when_requirements_pass(tmp_path):
    mt5 = MockMT5()
    mt5.connect()
    mt5.set_tick(2652.0, 2652.18)
    mt5._positions.append(_mt5_position())
    pa = _permission_pa()

    denial = check_permissions(
        pa,
        SimpleNamespace(m15_atr=3.0),
        {"daily_pnl_pct": 0.0},
        mt5,
        config=_permission_config(tmp_path),
        skip_gate1_safety=True,
    )

    assert denial is None
    packet = pa.trade_parameters.gtos_vnext_same_symbol_lifecycle_v4_packet
    assert packet["action"] == "same_direction_scale_in"
    assert packet["parent_ticket"] == 7001
    assert pa.trade_parameters.gtos_vnext_same_symbol_lifecycle_parent_ticket == 7001


def test_permissions_hydrates_empty_comment_position_from_lifecycle_store(tmp_path):
    mt5 = MockMT5()
    mt5.connect()
    mt5.set_tick(2652.0, 2652.18)
    mt5._positions.append(_mt5_position_without_v4_comment())
    store_path = tmp_path / "same_symbol_lifecycle_store.json"
    config = {
        "deployment": {"phase": 3},
        "risk": {
            "max_spread_cents": 100,
            "same_symbol_lifecycle_v4": {
                "pending_intent_dir": str(tmp_path),
                "lifecycle_store_path": str(store_path),
            },
        },
    }
    stored = record_same_symbol_lifecycle_entry_v4(
        config=config,
        ticket=7001,
        symbol="XAUUSD",
        side="LONG",
        trade_params={
            "candidate_id": "parent-candidate-xau",
            "gtos_vnext_thesis_id": "thesis-xau-london-continuation",
            "gtos_vnext_selected_cell_risk_pct": 0.25,
            "gtos_vnext_probability": 0.58,
            "gtos_vnext_expected_value_r": 0.20,
            "gtos_vnext_execution_policy_id": "unit-momentum-policy",
            "gtos_vnext_dynamic_policy_selected": "momentum_exhaustion",
        },
        trade_state=SimpleNamespace(
            current_volume=0.10,
            entry_price=2650.0,
            stop_loss=2640.0,
            take_profit_1=2670.0,
        ),
    )
    assert stored["record_hash_sha256"]
    assert load_same_symbol_lifecycle_store(config)["tickets"]["7001"]["thesis_id"] == (
        "thesis-xau-london-continuation"
    )
    pa = _permission_pa()

    denial = check_permissions(
        pa,
        SimpleNamespace(m15_atr=3.0),
        {"daily_pnl_pct": 0.0},
        mt5,
        config=config,
        skip_gate1_safety=True,
    )

    assert denial is None
    packet = pa.trade_parameters.gtos_vnext_same_symbol_lifecycle_v4_packet
    assert packet["action"] == "same_direction_scale_in"
    assert packet["parent_ticket"] == 7001
    assert packet["open_position_snapshot"][0]["source_status"] == (
        "broker_position_snapshot_with_durable_lifecycle_store"
    )


def test_permissions_blocks_opposite_direction_until_close_reverse_manager(tmp_path):
    mt5 = MockMT5()
    mt5.connect()
    mt5.set_tick(2652.0, 2652.18)
    mt5._positions.append(_mt5_position(side="LONG"))

    denial = check_permissions(
        _permission_pa(side="SHORT", action="close_and_reverse"),
        SimpleNamespace(m15_atr=3.0),
        {"daily_pnl_pct": 0.0},
        mt5,
        config=_permission_config(tmp_path),
        skip_gate1_safety=True,
    )

    assert denial is not None
    assert denial.reason == "same_symbol_lifecycle_v4_close_reduce_reverse_required"
    packet = denial.details["same_symbol_lifecycle_v4"]
    assert packet["action"] == "close_and_reverse"
    assert packet["close_ticket"] == 7001
    assert packet["permitted_order_intent"] is False
