"""Live occupancy + governor extras on intent_gold_state / haircut / A1."""

from datetime import datetime, timezone

from src.judgment.a1_log import intent_gold_state, maybe_observe_fluid_at_place, maybe_observe_ub_plc_017
from src.judgment.apply_size import CHALLENGE_LOGIN, CHALLENGE_NS, haircut_challenge_unit
from src.judgment.host_occupancy import governor_from_host, host_occupancy_governor, live_occupancy_for


class _Intent:
    symbol = "XAUUSD"
    sleeve = "dsp_two_bar_t"
    side = "short"
    entry = 4331.45
    stop = 4336.9
    stop_dist = 5.45
    target = 4288.19
    candidate_id = "slate-xau"
    ticket = "slate-xau"
    order_type = "MARKET"


AS_OF = datetime(2026, 9, 17, 10, 0, tzinfo=timezone.utc)

_OPEN = {
    "ticket": 293332188,
    "symbol": "XAUUSD",
    "sleeve": "dsp_two_bar_t",
    "open_time_utc": "2026-09-17T07:30:55Z",
    "still_open": True,
    "_kind": "open",
}

_CLOSED_DOC = {
    "closed": [
        {
            "ticket": 291072108,
            "symbol": "XAUUSD",
            "sleeve": "dsp_walked_hi",
            "closed_utc": "2026-09-09T10:14:01Z",
            "exit_class": "orig_stop",
        }
    ],
    "two_stop_source": "closed[]",
}


def _f5_unit():
    return {
        "cluster": "book",
        "sleeve_members": ["dsp_two_bar_t"],
        "n_trades": 1,
        "confidence": 1.0,
        "risk_pct_per_trade": 0.0015,
        "unit_risk_pct": 0.0015,
        "sized": True,
        "reason": "ok",
    }


def test_live_occupancy_for_opens_sets_symbol_open_and_minutes():
    occ = live_occupancy_for(
        "XAUUSD",
        AS_OF,
        "slate-xau",
        [_OPEN],
        _CLOSED_DOC,
        sleeve="dsp_two_bar_t",
    )
    assert occ["symbol_open"] is True
    assert occ["minutes_since_flat"] is not None
    assert occ["occupancy_source"] == "host_tape"
    assert occ["two_stop_source"] == "closed[]"


def test_live_occupancy_absent_tape_stays_none():
    occ = live_occupancy_for("XAUUSD", AS_OF, "x", None, None)
    assert occ["symbol_open"] is None
    assert occ["minutes_since_flat"] is None
    assert occ["occupancy_source"] == "deal_tape_absent"
    assert occ["two_stop_source"] == "closed_absent"


def test_live_assemble_occupancy_complete_and_governor_mirrors():
    occ = live_occupancy_for(
        "XAUUSD",
        AS_OF,
        "slate-xau",
        [_OPEN],
        _CLOSED_DOC,
        sleeve="dsp_two_bar_t",
    )
    gov = {"open_risk_pct": 0.0125, "allow_new": True, "cap_mult": 0.85, "reason": "ok"}
    state = intent_gold_state(
        _Intent(),
        origin="f5_challenge",
        as_of_utc=AS_OF,
        occupancy=occ,
        governor=gov,
    )
    assert state is not None
    assert state["completeness"]["occupancy"] is True
    assert state["occupancy"]["symbol_open"] is True
    assert state["occupancy"]["minutes_since_flat"] is not None
    assert state["governor"]["open_risk_pct"] == 0.0125
    assert state["governor"]["allow_new"] is True
    assert state["governor"]["cap_mult"] == 0.85


def test_intent_without_occupancy_stays_incomplete():
    state = intent_gold_state(_Intent(), origin="f5_challenge", as_of_utc=AS_OF, books={})
    assert state["completeness"]["occupancy"] is False
    assert state["governor"]["open_risk_pct"] is None


def test_governor_from_host_mirrors_decision_and_state():
    class _Dec:
        governor = {
            "allow_new_entries": True,
            "size_cap_multiplier": 0.85,
            "reason": "derisking_into_maxdd_wall",
        }

    class _GS:
        open_risk_pct = 0.02
        realized_today_pct = -0.004

    gov = governor_from_host(decision=_Dec(), governor_state=_GS())
    assert gov["open_risk_pct"] == 0.02
    assert gov["realized_today_pct"] == -0.004
    assert gov["allow_new"] is True
    assert gov["cap_mult"] == 0.85
    assert gov["reason"] == "derisking_into_maxdd_wall"


def test_host_occupancy_governor_pack():
    class _Dec:
        governor = {"allow_new_entries": False, "size_cap_multiplier": 0.0, "reason": "soft_daily_stop_reached"}

    class _GS:
        open_risk_pct = 0.031

    pack = host_occupancy_governor(
        symbol="XAUUSD",
        as_of=AS_OF,
        ticket="slate-xau",
        sleeve="dsp_two_bar_t",
        opens=[_OPEN],
        closed_doc=_CLOSED_DOC,
        decision=_Dec(),
        governor_state=_GS(),
    )
    assert pack["never_place"] is True
    assert pack["occupancy"]["symbol_open"] is True
    assert pack["occupancy"]["minutes_since_flat"] is not None
    assert pack["governor"]["open_risk_pct"] == 0.031
    assert pack["governor"]["allow_new"] is False


def test_haircut_forwards_occupancy_and_governor(monkeypatch):
    captured: dict = {}

    def _fake(intent, tick=None, **kwargs):
        captured.update(kwargs)
        return {
            "identity": {
                "side": "short",
                "family_class": "study",
                "symbol": "XAUUSD",
                "sleeve": "dsp_two_bar_t",
            },
            "completeness": {"state_sufficient_for_live": False, "cost": False, "occupancy": True},
            "news": {"spine_empty": False},
            "cost": {},
            "timeframes": {},
            "occupancy": kwargs.get("occupancy") or {},
            "governor": kwargs.get("governor") or {},
        }

    monkeypatch.setattr("src.judgment.a1_log.intent_gold_state", _fake)
    monkeypatch.delenv("GTOS_JEV_APPLY_LIVE", raising=False)
    occ = {"symbol_open": True, "minutes_since_flat": 12.5}
    gov = {"open_risk_pct": 0.03}
    haircut_challenge_unit(
        _f5_unit(),
        intent=_Intent(),
        occupancy=occ,
        governor=gov,
        evaluate_jev=False,
        login=CHALLENGE_LOGIN,
        ns=CHALLENGE_NS,
    )
    assert captured["occupancy"]["symbol_open"] is True
    assert captured["occupancy"]["minutes_since_flat"] == 12.5
    assert captured["governor"]["open_risk_pct"] == 0.03


def test_a1_observe_forwards_occupancy_governor(monkeypatch):
    captured: dict = {}
    monkeypatch.setenv("GTOS_JEV_A1_LOG", "1")

    def _fake(intent, tick=None, **kwargs):
        captured.update(kwargs)
        return {
            "identity": {},
            "completeness": {"occupancy": True},
            "news": {},
            "cost": {},
            "timeframes": {},
        }

    monkeypatch.setattr("src.judgment.a1_log.intent_gold_state", _fake)
    monkeypatch.setattr("src.judgment.a1_log.observe", lambda *a, **k: {})
    monkeypatch.setattr("src.judgment.a1_log.observe_fluid_inventory", lambda *a, **k: {})

    class _Tick:
        bid = 1.0
        ask = 1.01

    occ = {"symbol_open": True, "minutes_since_flat": 4.0}
    gov = {"open_risk_pct": 0.011}
    maybe_observe_ub_plc_017(_Intent(), _Tick(), None, occupancy=occ, governor=gov)
    assert captured["occupancy"]["symbol_open"] is True
    assert captured["governor"]["open_risk_pct"] == 0.011
    captured.clear()
    maybe_observe_fluid_at_place(_Intent(), _Tick(), None, occupancy=occ, governor=gov)
    assert captured["occupancy"]["minutes_since_flat"] == 4.0
    assert captured["governor"]["open_risk_pct"] == 0.011
