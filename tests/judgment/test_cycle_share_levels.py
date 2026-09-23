"""One cycle total, then a weight per candidate. The room is the top level. No orders."""

from src.components.ultimate_book.admission import (
    LAST_CYCLE_SHARE,
    _challenge_risk_units,
    _share_anchors,
)
from src.judgment.apply_size import binding_room_usd, money_exceeds

CARD = {
    "account_equity": 93522.57,
    "max_dd_reference_equity": 100000.0,
    "recorded_max_dd_limit_pct": 0.10,
    "recorded_hard_daily_limit_pct": 0.05,
    "realized_today_pct": 0.0,
    "open_risk_pct": 0.0,
    "cycle_risk_pct": 0.0,
    "launcher_usd": 150.0,
    "equity": 93522.57,
    "initial_balance": 100000.0,
    "overall_loss_pct": 10.0,
    "daily_percent_external": 5.0,
    "day_start_equity": 93678.44,
    "day_start_balance": 93670.92,
    "positions_total": 0,
    "open_risk_usd": 0.0,
    "currency_digits": 2,
}


def test_total_levels_top_out_at_the_binding_room():
    anchors = _share_anchors(CARD, trades=4)
    labels = [label for label, _value in anchors]
    assert labels[0] == "the launcher cash, in USD"
    assert "the room per candidate this cycle, in USD" in labels
    assert labels[-1] == "the binding room, in USD"
    assert not any("minimum lot" in label for label in labels)
    assert not any("daily room" in label for label in labels)
    values = [value for _label, value in anchors]
    assert values == sorted(values)
    room = binding_room_usd(CARD)[0]
    assert room is not None
    assert abs(values[-1] - room) < 1e-6
    assert all(value <= room + 1e-9 for value in values)


class _Intent:
    def __init__(self, sleeve, symbol, direction, min_lot=93.5):
        self.sleeve = sleeve
        self.symbol = symbol
        self.direction = direction
        self.stop_dist = 1.0
        self.intra_size = 1.0
        self.ll_impulse = None
        self.decision_hour = None
        self.vr = None
        self.entry_price = 100.0
        self.details = {}
        if min_lot is not None:
            self.details = {
                "min_lot_risk_pct": min_lot / 93522.57,
                "min_lot_risk_usd": min_lot,
            }


def _ask(monkeypatch, answers, pending):
    import src.components.ultimate_book.admission as admission
    import src.judgment.nineteen as nineteen

    posts = []

    def score_many(state, specs):
        posts.append((state, list(specs)))
        return answers(state, list(specs))

    monkeypatch.setattr(admission, "_spot", lambda _name: None)
    monkeypatch.setattr(nineteen, "score_many", score_many)
    units = _challenge_risk_units(
        pending,
        registry={},
        base_risk=0.02,
        equity_card=CARD,
        room=None,
        sqrt_n_pooling=False,
        kelly_lite=False,
        kelly_conservative=False,
        n_active_by_day={},
        stress_derisk=False,
        stress_state=None,
        overlays=False,
        cycle_taken=0.0,
    )
    return units, posts


def _two(min_lot=93.5):
    return [
        ("2026-09-23", "crypto", [_Intent("crypto", "BTCUSD", -1, min_lot)], ("crypto",), 1),
        ("2026-09-23", "energy", [_Intent("energy_agri", "USOIL_cash", -1, min_lot)], ("energy_agri",), 1),
    ]


def test_one_post_is_a_total_and_a_weight_per_candidate(monkeypatch):
    room = binding_room_usd(CARD)[0]

    def answers(state, specs):
        assert "share_arithmetic" in state
        assert abs(state["binding_room_usd"] - room) < 1e-6
        assert state["candidates"][0]["min_lot_risk_usd"] == 93.5
        out = {}
        for qid, text, _anchors in specs:
            assert "divided by the sum of the weights" in text
            out[qid] = room if qid == "unit_usd|cycle" else 1.0
        return out

    units, posts = _ask(monkeypatch, answers, _two())
    assert len(posts) == 1
    _state, specs = posts[0]
    assert [qid for qid, _text, _anchors in specs][0] == "unit_usd|cycle"
    assert len(specs) == 3
    assert {unit.reason for unit in units} == {"sized"}
    share = LAST_CYCLE_SHARE
    assert abs(share["total_usd"] - room) < 1e-6
    assert abs(sum(row["cash_usd"] for row in share["candidates"]) - room) < 1e-4
    assert abs(share["rounded_sum_usd"] - room) < 1e-4
    assert not money_exceeds(share["rounded_sum_usd"], room, CARD)


def test_equal_weights_split_the_room(monkeypatch):
    room = binding_room_usd(CARD)[0]
    pending = _two()

    def answers(_state, specs):
        return {qid: room if qid == "unit_usd|cycle" else 1.0 for qid, _text, _anchors in specs}

    units, _posts = _ask(monkeypatch, answers, pending)
    assert {unit.reason for unit in units} == {"sized"}
    cash = []
    for _day, _cluster, group, _members, _n in pending:
        cash.append(group[0].details["allocation_cash_usd"])
        assert group[0].details["candidate_share"] is True
    assert abs(cash[0] - room / 2) < 1e-6
    assert abs(cash[1] - room / 2) < 1e-6
    assert abs(sum(cash) - room) < 1e-6


def test_stays_out_and_an_unset_total_leave_every_share_unset(monkeypatch):
    room = binding_room_usd(CARD)[0]
    pending = _two()

    def stays(_state, specs):
        return {qid: room if qid == "unit_usd|cycle" else 0.0 for qid, _text, _anchors in specs}

    units, _posts = _ask(monkeypatch, stays, pending)
    assert {unit.reason for unit in units} == {"risk_unset"}
    assert all(unit.unit_risk_pct is None for unit in units)
    assert all(unit.risk_pct_per_trade is None for unit in units)
    for _day, _cluster, group, _members, _n in pending:
        assert "allocation_cash_usd" not in group[0].details
        assert group[0].details.get("candidate_risk_pct") is None or "candidate_share" not in group[0].details

    def missing_total(_state, specs):
        return {qid: None if qid == "unit_usd|cycle" else 1.0 for qid, _text, _anchors in specs}

    units, _posts = _ask(monkeypatch, missing_total, _two())
    assert {unit.reason for unit in units} == {"risk_unset"}
    assert all(unit.unit_risk_pct is None for unit in units)


def test_rounded_minimum_lot_above_the_room_leaves_every_share_unset(monkeypatch):
    room = binding_room_usd(CARD)[0]
    pending = _two(min_lot=room)

    def answers(_state, specs):
        return {qid: 100.0 if qid == "unit_usd|cycle" else 1.0 for qid, _text, _anchors in specs}

    units, _posts = _ask(monkeypatch, answers, pending)
    assert {unit.reason for unit in units} == {"risk_unset:rounded_above_room"}
    assert all(unit.sized is False for unit in units)
    assert all(unit.unit_risk_pct is None for unit in units)
    assert LAST_CYCLE_SHARE["reason"] == "risk_unset:rounded_above_room"
    assert money_exceeds(LAST_CYCLE_SHARE["rounded_sum_usd"], room, CARD)
    for _day, _cluster, group, _members, _n in pending:
        assert "allocation_cash_usd" not in group[0].details


def test_an_unread_minimum_lot_leaves_every_share_unset(monkeypatch):
    room = binding_room_usd(CARD)[0]
    pending = _two(min_lot=None)

    def answers(_state, specs):
        return {qid: room if qid == "unit_usd|cycle" else 1.0 for qid, _text, _anchors in specs}

    units, _posts = _ask(monkeypatch, answers, pending)
    assert {unit.reason for unit in units} == {"risk_unset:min_lot_unread"}
    assert all(unit.unit_risk_pct is None for unit in units)
    assert LAST_CYCLE_SHARE["rounded_sum_usd"] is None


def test_minimum_lot_uses_the_live_bid_when_the_intent_has_no_entry():
    from src.components.ultimate_book.admission import min_lot_stop_risk_usd

    intent = _Intent("crypto", "BTCUSD", 1, min_lot=None)
    intent.entry_price = None

    class _Tick:
        bid = 100.0
        ask = 100.2

    class _Module:
        def symbol_info_tick(self, symbol):
            assert symbol == "BTCUSD"
            return _Tick()

    def calc(order_type, symbol, volume, price_open, price_close):
        assert order_type == 0
        assert price_open == 100.0
        assert price_close == 99.0
        assert volume == 0.01
        return -4.5

    usd = min_lot_stop_risk_usd(
        intent, {"volume_min": 0.01}, calc, module=_Module(),
    )
    assert usd == 4.5


def test_minimum_lot_lands_on_a_frozen_intent():
    from src.components.ultimate_book.admission import TradeIntent, stamp_min_lot_risk

    intent = TradeIntent(
        sleeve="crypto", symbol="BTCUSD", direction=1,
        decision_day="2026-09-23", stop_dist=1.0, entry_price=100.0,
    )

    def calc(order_type, symbol, volume, price_open, price_close):
        assert order_type == 0
        assert price_open == 100.0
        assert price_close == 99.0
        assert volume == 0.01
        return -4.5

    stamp_min_lot_risk([intent], 93522.57, lambda _symbol: {"volume_min": 0.01}, calc)
    assert intent.details["min_lot_risk_read"] == "read"
    assert intent.details["min_lot_risk_usd"] == 4.5


def test_minimum_lot_selects_the_symbol_when_info_is_missing():
    from src.components.ultimate_book.admission import TradeIntent, stamp_min_lot_risk

    intent = TradeIntent(
        sleeve="energy_agri", symbol="USOIL_cash", direction=-1,
        decision_day="2026-09-23", stop_dist=1.0, entry_price=90.0,
    )
    selected = []

    class _Info:
        volume_min = 0.01

    class _Module:
        def symbol_info(self, symbol):
            if symbol in selected:
                return _Info()
            return None

        def symbol_select(self, symbol, enable):
            assert enable is True
            selected.append(symbol)
            return True

    def calc(order_type, symbol, volume, price_open, price_close):
        assert order_type == 1
        assert symbol == "USOIL_cash"
        assert price_open == 90.0
        assert price_close == 91.0
        return -6.0

    stamp_min_lot_risk(
        [intent], 93522.57, lambda _symbol: None, calc, module=_Module(),
    )
    assert selected == ["USOIL_cash"]
    assert intent.details["min_lot_risk_read"] == "read"
    assert intent.details["min_lot_risk_usd"] == 6.0


def test_minimum_lot_uses_the_broker_symbol():
    from src.components.ultimate_book.admission import TradeIntent, stamp_min_lot_risk

    intent = TradeIntent(
        sleeve="idxrev", symbol="GER40", direction=1,
        decision_day="2026-09-23", stop_dist=10.0, entry_price=25000.0,
    )
    asked = []

    def info_for(symbol):
        asked.append(symbol)
        if symbol == "GER40.cash":
            return {"volume_min": 0.01}
        return None

    def calc(order_type, symbol, volume, price_open, price_close):
        assert symbol == "GER40.cash"
        assert price_open == 25000.0
        assert price_close == 24990.0
        return -12.0

    stamp_min_lot_risk(
        [intent], 93522.57, info_for, calc, resolve=lambda name: "GER40.cash",
    )
    assert asked == ["GER40.cash"]
    assert intent.symbol == "GER40"
    assert intent.details["min_lot_risk_usd"] == 12.0


def test_the_internal_overlay_and_the_second_room_are_gone():
    import src.components.ultimate_book.admission as admission

    assert not hasattr(admission, "_internal_daily_from_config")
    assert not hasattr(admission, "_binding_room_fraction")
    assert not hasattr(admission, "_room_parts")
    assert "internal_daily_limit_pct" not in admission.GovernorLimits.__dataclass_fields__
    assert "internal_daily_source" not in admission.GovernorLimits.__dataclass_fields__


def test_money_uses_the_account_currency_digits_or_compares_exactly():
    room = 100.0
    assert money_exceeds(room + 0.009, room, {}) is True
    assert money_exceeds(room + 0.004, room, {"currency_digits": 2}) is False
    assert money_exceeds(room + 0.006, room, {"currency_digits": 2}) is True
    assert money_exceeds(room + 0.004, room, {"currency_digits": True}) is True
    assert money_exceeds(room + 0.004, room, {"currency_digits": -1}) is True
    assert money_exceeds(None, room, {"currency_digits": 2}) is False


def test_size_room_reads_the_account_currency_digits():
    from src.components.execution import ExecutionEngine

    class _Raw:
        def __init__(self, digits):
            self.digits = digits

        def account_info(self):
            return {"currency_digits": self.digits}

        def positions_get(self):
            return []

        def orders_get(self):
            return []

    engine = object.__new__(ExecutionEngine)
    engine.mt5 = _Raw(2)
    engine.config = {}
    engine._runtime_namespace = None
    assert engine._size_room_facts(0.0)["currency_digits"] == 2

    engine.mt5 = _Raw(True)
    assert "currency_digits" not in engine._size_room_facts(0.0)
