"""Challenge open-trade reject reads the trade, not a V4 verdict."""

from datetime import datetime, timezone

from src.components.dynamic_target_stop_geometry_v4 import (
    build_target_stop_geometry_v4_contract,
)
from src.components.execution_manager_v4 import _prop_firm_headroom_context
from src.judgment.execution_choices import open_trade_reject_facts


def _source() -> dict:
    return {
        "source_mode": "ultimate_book_runtime_trade_params",
        "source_path_feature_status": "runtime_asof_ultimate_book_closed_bar_features",
        "source_window_complete": True,
        "selected_policy_ordered_path_status": (
            "asof_runtime_path_ordering_not_required_before_order_send"
        ),
        "selected_policy_same_bar_ambiguous": False,
    }


def test_challenge_geometry_uses_distances_and_skips_v4_only_gaps(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.components.dynamic_target_stop_geometry_v4._geometry_on_challenge",
        lambda: True,
    )
    contract = build_target_stop_geometry_v4_contract(
        config=None,
        selected_policy="time_stop",
        source_event=_source(),
        direction="LONG",
        entry_price=100.0,
        stop_loss=98.0,
        trade_params={
            "sleeve": "idxrev",
            "target_dist": 5.0,
            "stop_dist": 2.0,
            "direction": "LONG",
            "entry_price": 100.0,
            "stop_loss": 98.0,
        },
    )
    missing = contract["source_completeness"]["missing_source_fields"]
    assert contract["target_destination"]["final_target_r"] == 2.5
    assert contract["thesis_horizon"]["horizon_m15_bars"] is None
    assert contract["thesis_horizon"]["stale_review_m15_bars"] is None
    assert contract["thesis_horizon"]["time_stop_bars"] is None
    assert contract["target_destination"]["trigger_r"] is None
    for name in (
        "final_target_r",
        "trigger_r",
        "time_stop_bars",
        "thesis_horizon_m15_bars",
        "stale_review_m15_bars",
        "positive_final_target_r",
    ):
        assert name not in missing
    assert contract["status"] == "source_bound_geometry_contract_ready"


def test_challenge_headroom_snapshot_is_not_a_fatal(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.components.execution_manager_v4._geometry_on_challenge",
        lambda: True,
    )
    got = _prop_firm_headroom_context(
        config=None,
        trade_params={},
        requested_risk_pct=1.0,
        now_utc=datetime.now(timezone.utc),
    )
    assert got["blocking_reason"] is None


def test_off_challenge_headroom_snapshot_still_blocks() -> None:
    got = _prop_firm_headroom_context(
        config=None,
        trade_params={},
        requested_risk_pct=1.0,
        now_utc=datetime.now(timezone.utc),
    )
    assert got["blocking_reason"] == "prop_firm_headroom_v4_snapshot_missing"


def test_reject_card_is_cash_room_and_geometry() -> None:
    facts = open_trade_reject_facts(
        cash_usd=40.0,
        binding_room_usd=250.0,
        spread=0.12,
        stop_distance=2.0,
        entry=100.0,
        stop=98.0,
        target=105.0,
        side="LONG",
    )
    assert facts == {
        "side": "LONG",
        "cash_usd": 40.0,
        "binding_room_usd": 250.0,
        "spread": 0.12,
        "stop_distance": 2.0,
        "entry": 100.0,
        "stop": 98.0,
        "target": 105.0,
        "r": 2.5,
    }
    assert "should_block" not in facts
    assert "fatal_reasons" not in facts
    assert "sleeve" not in facts
    assert "unit_choice" not in facts
    assert "cash_source" not in facts

    decided = open_trade_reject_facts(
        cash_usd=40.0,
        binding_room_usd=250.0,
        spread=0.12,
        stop_distance=2.0,
        entry=100.0,
        stop=98.0,
        target=105.0,
        side="LONG",
        sleeve="metals_core",
        unit_choice="unit_long",
        unit_probability=0.43,
        allocation_weight=0.55,
        allocation_total_usd=100.0,
        cash_source="cycle_share",
    )
    assert decided["sleeve"] == "metals_core"
    assert decided["unit_choice"] == "unit_long"
    assert decided["unit_probability"] == 0.43
    assert decided["allocation_weight"] == 0.55
    assert decided["allocation_total_usd"] == 100.0
    assert decided["cash_source"] == "cycle_share"
    assert decided["cash_usd"] == 40.0
    omitted = open_trade_reject_facts(
        cash_usd=40.0,
        side="LONG",
        unit_probability=None,
        allocation_weight=0,
        allocation_total_usd=None,
        cash_source="",
    )
    assert "unit_probability" not in omitted
    assert "allocation_weight" not in omitted
    assert "allocation_total_usd" not in omitted
    assert "cash_source" not in omitted


def test_size_last_room_belongs_to_this_call() -> None:
    from src.judgment.apply_size import honor_f5_scaler_risk, size_last_names_this_trade

    previous = {
        "symbol": "USDJPY",
        "f5_symbol": "USDJPY",
        "candidate_id": "prev-call",
        "f5_candidate_id": "prev-call",
        "binding_room_usd": 10.0,
    }
    this = {"symbol": "XAUUSD", "candidate_id": "this-call"}
    assert size_last_names_this_trade(previous, this) is False
    assert size_last_names_this_trade(
        {"symbol": "XAUUSD", "candidate_id": "prev-call", "f5_candidate_id": "prev-call"},
        this,
    ) is False
    assert size_last_names_this_trade(
        {"symbol": "XAUUSD", "candidate_id": "this-call", "binding_room_usd": 20.0},
        this,
    ) is True

    class _Scaler:
        last = None

    scaler = _Scaler()
    _honored, stamp = honor_f5_scaler_risk(
        50.0,
        scaler=scaler,
        trade_params={"symbol": "XAUUSD", "candidate_id": "this-call"},
        login=1,
        ns="not-challenge",
    )
    assert stamp["symbol"] == "XAUUSD"
    assert stamp["candidate_id"] == "this-call"
    assert stamp["f5_symbol"] == "XAUUSD"
    assert stamp["f5_candidate_id"] == "this-call"
    assert size_last_names_this_trade(scaler.last, this) is True
    assert size_last_names_this_trade(scaler.last, {"symbol": "USDJPY", "candidate_id": "other"}) is False


def test_reject_card_omits_an_unset_target() -> None:
    facts = open_trade_reject_facts(
        cash_usd=10.0,
        binding_room_usd=20.0,
        spread=0.01,
        stop_distance=1.5,
        entry=50.0,
        stop=48.5,
        target=None,
        side="SHORT",
    )
    assert "target" not in facts
    assert "r" not in facts
    assert facts["side"] == "SHORT"


def test_lot_card_carries_the_calculated_lot_and_the_room() -> None:
    from src.judgment.execution_choices import (
        QUESTIONS,
        _question_pack,
        floor_lot_to_step,
        lot_volume,
        open_trade_lot_facts,
    )

    facts = open_trade_lot_facts(
        lots=1.25,
        volume_min=0.01,
        volume_max=5.0,
        volume_step=0.01,
        rounded_risk_usd=40.0,
        binding_room_usd=250.0,
        stop_distance=2.0,
        cash_usd=40.0,
    )
    assert facts["lots"] == 1.25
    assert facts["volume_min"] == 0.01
    assert facts["volume_max"] == 5.0
    assert facts["volume_step"] == 0.01
    assert facts["rounded_risk_usd"] == 40.0
    assert facts["binding_room_usd"] == 250.0
    assert facts["sl_distance"] == 2.0
    assert facts["risk_amount"] == 40.0

    empty = open_trade_lot_facts(
        lots=None,
        volume_min=0.01,
        volume_max=None,
        volume_step=0.01,
        rounded_risk_usd=None,
        binding_room_usd=None,
        stop_distance=2.0,
        cash_usd=None,
    )
    assert "lots" not in empty
    assert "rounded_risk_usd" not in empty
    assert "binding_room_usd" not in empty
    assert empty["volume_min"] == 0.01

    assert floor_lot_to_step(1.237, 0.01) == 1.23
    assert floor_lot_to_step(1.25, 0.01) == 1.25
    assert floor_lot_to_step(0.009, 0.01) is None
    assert floor_lot_to_step(1.25, None) is None

    placed = {
        "decision_emitted": True,
        "choice": "place",
        "score": 9.5,
        "facts": {"lots": 1.25},
    }
    assert lot_volume(placed) == 1.25
    assert lot_volume({"decision_emitted": True, "choice": "place", "score": 1.25}) is None
    assert lot_volume({"decision_emitted": True, "choice": "place", "facts": {"lots": None}}) is None
    assert lot_volume({"decision_emitted": True, "choice": "refuse", "facts": {"lots": 1.2}}) is None
    assert lot_volume({"decision_emitted": False, "choice": None, "facts": {"lots": 1.25}}) is None

    reject_text = QUESTIONS["reject"]["instructions"]
    assert "unit choice" in reject_text
    assert "risk weight" in reject_text
    assert "fit to send now" in reject_text
    assert "block does not send" not in reject_text
    assert "block weight" not in reject_text
    assert QUESTIONS["reject"]["criteria"]["continue"] == (
        "This order, as built, is fit to send now."
    )
    lot_text = QUESTIONS["lot"]["instructions"]
    assert "volume_step" in lot_text
    assert "paired parameter" not in lot_text
    card = {"facts": {"lots": 1.25, "volume_min": 0.01, "volume_step": 0.01, "volume_max": 5.0}}
    assert "exec_lot_parameter" not in _question_pack("lot", QUESTIONS["lot"], [], card)
    assert "exec_reject_parameter" not in _question_pack(
        "reject", QUESTIONS["reject"], [], {"facts": {"cash_usd": 40.0, "binding_room_usd": 250.0}}
    )


def test_floor_uses_the_step_decimal_and_a_subminimum_lot_stays_on_the_card(tmp_path, monkeypatch) -> None:
    from types import SimpleNamespace

    from src.components.execution import ExecutionEngine
    from src.judgment.execution_choices import (
        QUESTIONS,
        below_volume_min,
        choose,
        floor_lot_to_step,
        lot_on_card,
        open_trade_lot_facts,
    )
    import src.judgment.jev_questions as jq

    assert floor_lot_to_step(0.07, 0.01) == 0.07
    assert floor_lot_to_step(0.3, 0.1) == 0.3
    assert floor_lot_to_step(2.45, 0.1) == 2.4
    assert floor_lot_to_step(0.009, 0.01) is None
    assert lot_on_card(0.004, 0.01, 0.01) == 0.01
    assert lot_on_card(0.05, 0.01, 0.1) == 0.1
    assert lot_on_card(1.237, 0.01, 0.01) == 1.23
    assert lot_on_card(0.004, 0.01, None) is None
    assert below_volume_min("0.004", "0.01") is True
    assert below_volume_min(None, 0.01) is False
    assert below_volume_min(0.02, 0.01) is False

    seen = {}

    def calc(order_type, symbol, volume, price_open, price_close):
        seen["volume"] = volume
        seen["entry"] = price_open
        seen["stop"] = price_close
        return -18.4

    engine = ExecutionEngine.__new__(ExecutionEngine)
    engine.symbol = "XAGUSD"
    engine.mt5 = SimpleNamespace(_mt5=SimpleNamespace(order_calc_profit=calc))
    loss = engine._broker_cash_risk_amount(
        direction="LONG",
        volume=0.01,
        entry_price=65.18,
        stop_loss=65.03,
    )
    assert loss == 18.4
    assert seen == {"volume": 0.01, "entry": 65.18, "stop": 65.03}

    facts = open_trade_lot_facts(
        lots=lot_on_card(0.004, 0.01, 0.01),
        volume_min=0.01,
        volume_step=0.01,
        volume_max=5.0,
        binding_room_usd=3522.57,
        cash_usd=4.0,
        min_lot_loss_usd=loss,
    )
    names = list(facts)
    assert names.index("risk_amount") == names.index("binding_room_usd") + 1
    assert names.index("min_lot_loss_usd") == names.index("risk_amount") + 1
    assert facts["lots"] == 0.01
    assert facts["min_lot_loss_usd"] == 18.4
    assert facts["risk_amount"] == 4.0
    assert facts["binding_room_usd"] == 3522.57
    assert "volume_min" in QUESTIONS["lot"]["instructions"]
    assert "loss at the stop" in QUESTIONS["lot"]["instructions"]

    def ask(state, *, question_id, instructions, criteria):
        assert question_id == "exec_lot"
        assert set(criteria) == {"place", "refuse"}
        assert state["facts"]["lots"] == 0.01
        assert state["facts"]["min_lot_loss_usd"] == 18.4
        return {
            "choice": "refuse",
            "probability": 0.81,
            "probabilities": {"refuse": 0.81, "place": 0.19},
            "decision_emitted": True,
        }

    monkeypatch.setattr(jq, "prior_outcomes", lambda **_k: [])
    row = choose(
        "lot",
        symbol="XAGUSD",
        reason="open_trade",
        proposed=facts["lots"],
        facts=facts,
        ask=ask,
        use_cache=False,
        record=True,
        record_to=tmp_path / "execution_choices.jsonl",
    )
    assert row["choice"] == "refuse"
    assert row["decision_emitted"] is True
