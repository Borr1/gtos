"""Behavioural tests for owner manual SL/TP moves on a live position.

Owner directive (Borhen, 2026-08-05): "if i make a move on my ftmo account it should
reflect on the book, my manual moves should be allowed and 'normal' to have."

These tests exercise real engine methods against a fake broker. They assert BEHAVIOUR
(what the engine does to the broker and to its own state), never source text.
"""
import os
import sys, types, logging
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.components.execution import ExecutionEngine, TradeState  # noqa: E402

ARMED_SLEEVES = ("crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert")


class FakePos:
    def __init__(self, ticket, sl, tp, type_, entry=100.0, volume=1.0):
        self.ticket = ticket; self.sl = sl; self.tp = tp
        self.type = type_          # 0 = LONG (BUY), 1 = SHORT (SELL)
        self.price_open = entry; self.volume = volume
        self.comment = "W7:energy_agri"; self.profit = 0.0


class FakeResult:
    def __init__(self, success=True, retcode=10009, price=0.0):
        self.success = success; self.retcode = retcode
        self.price = price; self.order = 1; self.comment = "ok"
        self.deal = 1; self.volume = 1.0


class FakeMT5:
    def __init__(self, positions=None):
        self.positions = positions or []
        self.sent = []
    def get_positions(self, symbol=None): return list(self.positions)
    def get_tick(self, symbol=None):
        t = types.SimpleNamespace(bid=100.0, ask=100.1, spread_cents=None); return t
    def order_send(self, request):
        self.sent.append(dict(request))
        for p in self.positions:                       # reflect an accepted SLTP change
            if p.ticket == request.get("position"):
                p.sl = request.get("sl", p.sl); p.tp = request.get("tp", p.tp)
        return FakeResult()
    def get_symbol_info(self, symbol=None): return types.SimpleNamespace(point=0.001, digits=3)


def make_engine(positions):
    cfg = {"market": {"symbol": "UKOIL_cash", "mt5_symbol": "UKOIL.cash"}}
    eng = ExecutionEngine(FakeMT5(positions), cfg)
    eng._runtime_halt_snapshot = lambda *a, **k: None          # no disk halt-flag read
    eng._record_broker_runtime_lifecycle_event = lambda *a, **k: None
    return eng


def make_trade(direction="SHORT", entry=83.233, sl=89.984, tp=56.230, ticket=172916305):
    return TradeState(
        ticket=ticket, direction=direction, entry_price=entry, stop_loss=sl,
        take_profit_1=tp, take_profit_2=0.0, take_profit_3=0.0,
        initial_volume=1.91, current_volume=1.91,
        sl_distance=abs(entry - sl), trade_id="t1", entry_time="2026-08-04T13:00:28+00:00",
        gtos_vnext_book_native_exit_management=True,
    )


# ---------------------------------------------------------------- adoption ("reflect on the book")

def test_owner_tightened_stop_is_adopted_and_reflected_on_the_book():
    """The exact 2026-08-04 case: SHORT, owner moves the stop from 89.984 to 80.511."""
    pos = FakePos(172916305, sl=80.511, tp=56.230, type_=1, entry=83.233)
    eng = make_engine([pos]); tr = make_trade()
    eng._reconcile_broker_protective_levels(tr, pos)

    assert tr.stop_loss == pytest.approx(80.511), "the book must reflect the owner's move"
    assert tr.owner_sl_override_active is True
    assert tr.owner_sl_price == pytest.approx(80.511)
    assert tr.book_intended_sl == pytest.approx(89.984)
    assert tr.owner_override_events == 1
    ev = [e for e in tr.partial_close_events if e["type"] == "OWNER_PROTECTIVE_LEVEL_ADOPTED"]
    assert len(ev) == 1 and ev[0]["adopted"] is True and ev[0]["reverted"] is False


def test_locked_profit_stop_is_not_flagged_as_excess_risk():
    """A stop moved PAST entry into profit has negative risk - it must never warn."""
    pos = FakePos(172916305, sl=80.511, tp=56.230, type_=1, entry=83.233)
    eng = make_engine([pos]); tr = make_trade()
    eng._reconcile_broker_protective_levels(tr, pos)
    assert tr.owner_sl_risk_exceeds_sized is False
    assert tr.owner_sl_implied_risk_ratio < 0, "stop past entry = negative risk distance"


def test_sl_distance_is_not_rewritten_by_an_owner_move():
    """sl_distance defines 1R for every downstream computation; it must stay the SIZED value."""
    pos = FakePos(172916305, sl=80.511, tp=56.230, type_=1, entry=83.233)
    eng = make_engine([pos]); tr = make_trade()
    before = tr.sl_distance
    eng._reconcile_broker_protective_levels(tr, pos)
    assert tr.sl_distance == before == pytest.approx(6.751)


# ---------------------------------------------------------------- widened stop -> adopt + warn

def test_owner_widened_stop_is_adopted_and_warned(caplog):
    """LONG entry 100, sized stop 90 (1R = 10). Owner widens to 85 -> 1.5R of risk."""
    pos = FakePos(1, sl=85.0, tp=130.0, type_=0, entry=100.0)
    eng = make_engine([pos])
    tr = make_trade(direction="LONG", entry=100.0, sl=90.0, tp=130.0, ticket=1)
    with caplog.at_level(logging.WARNING):
        eng._reconcile_broker_protective_levels(tr, pos)

    assert tr.stop_loss == pytest.approx(85.0), "adopted, never silently re-tightened"
    assert tr.owner_sl_risk_exceeds_sized is True
    assert tr.owner_sl_implied_risk_ratio == pytest.approx(1.5)
    assert any("OWNER STOP WIDENS RISK BEYOND SIZED AMOUNT" in r.message for r in caplog.records)
    ev = [e for e in tr.partial_close_events if e["type"] == "OWNER_PROTECTIVE_LEVEL_ADOPTED"][0]
    assert ev["owner_sl_risk_exceeds_sized"] is True
    assert eng.mt5.sent == [], "adopting must not send ANY broker request"


def test_owner_widened_stop_within_sized_risk_does_not_warn(caplog):
    pos = FakePos(1, sl=92.0, tp=130.0, type_=0, entry=100.0)
    eng = make_engine([pos])
    tr = make_trade(direction="LONG", entry=100.0, sl=90.0, tp=130.0, ticket=1)
    with caplog.at_level(logging.WARNING):
        eng._reconcile_broker_protective_levels(tr, pos)
    assert tr.owner_sl_risk_exceeds_sized is False
    assert not any("WIDENS RISK" in r.message for r in caplog.records)


# ---------------------------------------------------------------- the never-worsen guard

def test_book_never_writes_a_stop_worse_than_the_live_broker_stop():
    """SHORT: a HIGHER stop is worse. The engine must refuse and send nothing."""
    pos = FakePos(172916305, sl=80.511, tp=56.230, type_=1, entry=83.233)
    eng = make_engine([pos]); tr = make_trade()
    ok = eng._modify_sl(172916305, 83.233, trade=tr, modify_reason="sl_to_breakeven")
    assert ok is False
    assert eng.mt5.sent == [], "no broker request may be sent for a worsening stop"
    assert pos.sl == pytest.approx(80.511), "the better stop stays live"
    ev = [e for e in tr.partial_close_events
          if e["type"] == "SL_MODIFY_REFUSED_WOULD_WORSEN_LIVE_STOP"]
    assert len(ev) == 1 and ev[0]["broker_live_sl"] == pytest.approx(80.511)


def test_book_never_worsens_a_long_stop():
    pos = FakePos(1, sl=95.0, tp=130.0, type_=0, entry=100.0)
    eng = make_engine([pos]); tr = make_trade("LONG", 100.0, 90.0, 130.0, 1)
    assert eng._modify_sl(1, 92.0, trade=tr, modify_reason="trail") is False
    assert eng.mt5.sent == []


def test_book_set_stop_still_moves_normally_when_tightening():
    """Regression: the guard must not block the book's ordinary risk-reducing moves."""
    pos = FakePos(1, sl=90.0, tp=130.0, type_=0, entry=100.0)
    eng = make_engine([pos]); tr = make_trade("LONG", 100.0, 90.0, 130.0, 1)
    assert eng._modify_sl(1, 100.0, trade=tr, modify_reason="sl_to_breakeven") is True
    assert len(eng.mt5.sent) == 1
    assert eng.mt5.sent[0]["sl"] == pytest.approx(100.0)
    assert tr.book_intended_sl == pytest.approx(100.0)
    assert tr.owner_sl_override_active is False


def test_removing_the_stop_entirely_is_refused():
    pos = FakePos(1, sl=90.0, tp=130.0, type_=0, entry=100.0)
    eng = make_engine([pos]); tr = make_trade("LONG", 100.0, 90.0, 130.0, 1)
    assert eng._modify_sl(1, 0.0, trade=tr, modify_reason="clear") is False
    assert eng.mt5.sent == []


def test_setting_a_stop_where_none_exists_is_allowed():
    pos = FakePos(1, sl=0.0, tp=130.0, type_=0, entry=100.0)
    eng = make_engine([pos]); tr = make_trade("LONG", 100.0, 90.0, 130.0, 1)
    assert eng._modify_sl(1, 90.0, trade=tr, modify_reason="initial") is True
    assert len(eng.mt5.sent) == 1


# ------------------------------------------------- the 2026-08-04 scenario, end to end

def test_breakeven_trigger_cannot_revert_an_owner_locked_profit():
    """THE regression this work exists for.

    Owner locks +0.40R on a SHORT (stop 80.511 vs entry 83.233). The partial_be_runner
    2R trigger then fires and asks for break-even (= entry). Before this change the
    book would have written 83.233 and handed back the locked profit.
    """
    pos = FakePos(172916305, sl=80.511, tp=56.230, type_=1, entry=83.233)
    eng = make_engine([pos]); tr = make_trade()
    eng._reconcile_broker_protective_levels(tr, pos)      # adopt the owner's stop
    eng._move_sl_to_breakeven(tr, tr.ticket)              # 2R trigger fires

    assert pos.sl == pytest.approx(80.511), "owner's locked profit must survive"
    assert eng.mt5.sent == [], "not one worsening request may reach the broker"
    assert tr.stop_loss == pytest.approx(80.511)


def test_breakeven_still_works_on_an_untouched_book_stop():
    """Regression: with no owner move, break-even behaves exactly as before."""
    pos = FakePos(1, sl=90.0, tp=130.0, type_=0, entry=100.0)
    eng = make_engine([pos]); tr = make_trade("LONG", 100.0, 90.0, 130.0, 1)
    eng._reconcile_broker_protective_levels(tr, pos)
    eng._move_sl_to_breakeven(tr, tr.ticket)
    assert pos.sl == pytest.approx(100.0)
    assert tr.sl_at_breakeven is True
    assert len(eng.mt5.sent) == 1


def test_a_book_move_is_not_later_misread_as_an_owner_override():
    pos = FakePos(1, sl=90.0, tp=130.0, type_=0, entry=100.0)
    eng = make_engine([pos]); tr = make_trade("LONG", 100.0, 90.0, 130.0, 1)
    eng._reconcile_broker_protective_levels(tr, pos)
    eng._modify_sl(1, 100.0, trade=tr, modify_reason="sl_to_breakeven")
    eng._reconcile_broker_protective_levels(tr, pos)      # next tick
    assert tr.owner_sl_override_active is False
    assert [e for e in tr.partial_close_events
            if e["type"] == "OWNER_PROTECTIVE_LEVEL_ADOPTED"] == []


def test_reconcile_is_a_noop_when_broker_agrees_with_the_book():
    pos = FakePos(1, sl=90.0, tp=130.0, type_=0, entry=100.0)
    eng = make_engine([pos]); tr = make_trade("LONG", 100.0, 90.0, 130.0, 1)
    eng._reconcile_broker_protective_levels(tr, pos)
    assert tr.owner_sl_override_active is False
    assert tr.partial_close_events == []
    assert eng.mt5.sent == []


# ---------------------------------------------------------------- exit provenance

def test_exit_provenance_records_an_owner_set_level():
    pos = FakePos(172916305, sl=80.511, tp=56.230, type_=1, entry=83.233)
    eng = make_engine([pos]); tr = make_trade()
    eng.active_trade = tr
    eng._reconcile_broker_protective_levels(tr, pos)
    eng._record_close("broker_closed")
    ev = [e for e in tr.partial_close_events if e["type"] == "CLOSE_BROKER_CLOSED"][0]
    assert ev["exit_level_provenance"] == "owner_modified"
    assert ev["exit_stop_matches_book_intent"] is False
    assert ev["book_intended_sl"] == pytest.approx(89.984)
    assert ev["broker_sl_last_seen"] == pytest.approx(80.511)
    assert ev["provenance_contract_version"] == "owner_manual_override_provenance_v1"


def test_exit_provenance_records_a_book_set_level():
    pos = FakePos(1, sl=90.0, tp=130.0, type_=0, entry=100.0)
    eng = make_engine([pos]); tr = make_trade("LONG", 100.0, 90.0, 130.0, 1)
    eng.active_trade = tr
    eng._reconcile_broker_protective_levels(tr, pos)
    eng._record_close("broker_closed")
    ev = [e for e in tr.partial_close_events if e["type"] == "CLOSE_BROKER_CLOSED"][0]
    assert ev["exit_level_provenance"] == "book_set"
    assert ev["exit_stop_matches_book_intent"] is True
    assert ev["owner_override_events"] == 0


def test_close_reason_semantics_are_unchanged():
    """Additive only: the existing `reason` -> event-type contract must not move."""
    pos = FakePos(1, sl=90.0, tp=130.0, type_=0, entry=100.0)
    eng = make_engine([pos]); tr = make_trade("LONG", 100.0, 90.0, 130.0, 1)
    eng.active_trade = tr
    eng._record_close("broker_closed")
    types_ = [e["type"] for e in tr.partial_close_events]
    assert types_ == ["CLOSE_BROKER_CLOSED"]


# ---------------------------------------------------------------- armed sleeves pinned

@pytest.mark.parametrize("sleeve", ARMED_SLEEVES)
def test_armed_sleeve_with_no_owner_move_is_completely_unaffected(sleeve):
    """Pin the four ARMED sleeves by name: absent an owner move, nothing changes."""
    pos = FakePos(1, sl=90.0, tp=130.0, type_=0, entry=100.0)
    pos.comment = f"W7:{sleeve}"
    eng = make_engine([pos]); tr = make_trade("LONG", 100.0, 90.0, 130.0, 1)
    before = (tr.stop_loss, tr.sl_distance, tr.sl_at_breakeven, len(tr.partial_close_events))
    eng._reconcile_broker_protective_levels(tr, pos)
    assert (tr.stop_loss, tr.sl_distance, tr.sl_at_breakeven, len(tr.partial_close_events)) == before
    assert eng.mt5.sent == []
    assert tr.owner_sl_override_active is False


def test_tolerance_absorbs_float_noise_but_sees_one_tick():
    pos = FakePos(1, sl=90.0, tp=130.0, type_=0, entry=100.0)
    eng = make_engine([pos])
    assert eng._protective_level_differs(90.0, 90.0 + 1e-12) is False
    assert eng._protective_level_differs(90.0, 90.001) is True


def test_breakeven_is_skipped_cleanly_when_the_live_stop_is_already_better(caplog):
    """No futile retries and no false 'broker rejection' page when the owner is ahead."""
    pos = FakePos(172916305, sl=80.511, tp=56.230, type_=1, entry=83.233)
    eng = make_engine([pos]); tr = make_trade()
    eng._reconcile_broker_protective_levels(tr, pos)
    with caplog.at_level(logging.WARNING):
        eng._move_sl_to_breakeven(tr, tr.ticket)

    skip = [e for e in tr.partial_close_events
            if e["type"] == "SL_TO_BREAKEVEN_SKIPPED_LIVE_STOP_ALREADY_BETTER"]
    assert len(skip) == 1 and skip[0]["owner_sl_override_active"] is True
    assert [e for e in tr.partial_close_events
            if e["type"] == "SL_MODIFY_REFUSED_WOULD_WORSEN_LIVE_STOP"] == [], \
        "should not even reach the guard"
    assert eng.mt5.sent == []
    assert pos.sl == pytest.approx(80.511)
    assert tr.sl_at_breakeven is True
    assert not any("requires human investigation" in r.message for r in caplog.records), \
        "the owner must not be paged for moving his own stop"


def test_breakeven_skip_does_not_fire_when_the_stop_is_genuinely_worse():
    """Regression: a real BE move must still be attempted and sent."""
    pos = FakePos(1, sl=90.0, tp=130.0, type_=0, entry=100.0)
    eng = make_engine([pos]); tr = make_trade("LONG", 100.0, 90.0, 130.0, 1)
    eng._move_sl_to_breakeven(tr, 1)
    assert [e for e in tr.partial_close_events
            if e["type"] == "SL_TO_BREAKEVEN_SKIPPED_LIVE_STOP_ALREADY_BETTER"] == []
    assert len(eng.mt5.sent) == 1 and eng.mt5.sent[0]["sl"] == pytest.approx(100.0)
