"""Wave M: live books make state_sufficient true; remaining SHADOW axes get named tape."""

from datetime import datetime, timezone

from src.judgment.a1_log import intent_gold_state
from src.judgment.bars import load_challenge_books
from src.judgment.compose import compose_shadow
from src.judgment.fluid_local import local_answers
from src.judgment.host_events import named_final_sl, news_inventory_at, sl_differs
from src.judgment.news_spine import attach_news, load_spines
from src.judgment.sleeve_from_tape import features_from_books


class _Intent:
    symbol = "XAUUSD"
    sleeve = "dsp_two_bar_t"
    side = "short"
    entry = 4331.45
    stop = 4336.9
    stop_dist = 5.45
    target = 4288.19
    candidate_id = "292667008"
    ticket = "292667008"
    order_type = "MARKET"


AS_OF = datetime(2026, 9, 17, 7, 30, 55, tzinfo=timezone.utc)


def test_intent_gold_state_loads_challenge_books_and_is_sufficient():
    state = intent_gold_state(_Intent(), origin="f5_challenge", as_of_utc=AS_OF)
    assert state is not None
    assert state["completeness"]["timeframes_m15_h4"] is True
    assert state["completeness"]["state_sufficient_for_live"] is True
    assert state["identity"]["family_class"] != "unknown"
    assert state["timeframes"]["m15"]["last_utc"] == "2026-09-17T07:30:00Z"
    assert "timeframes.m15" not in state["completeness"]["missing_fields"]
    assert "timeframes.h4" not in state["completeness"]["missing_fields"]


def test_intent_without_books_stays_insufficient():
    state = intent_gold_state(_Intent(), origin="f5_challenge", books={}, as_of_utc=AS_OF)
    assert state["completeness"]["state_sufficient_for_live"] is False
    composed = compose_shadow(state)
    assert composed["shadow_size_tilt"] == 1.0
    assert composed["state_sufficient"] is False


def test_compose_flow_moves_off_one_when_sufficient():
    state = intent_gold_state(_Intent(), origin="f5_challenge", as_of_utc=AS_OF)
    composed = compose_shadow(state, ticket="292667008")
    assert composed["state_sufficient"] is True
    assert composed["local_flow_stance"] in {"with_flow", "against_flow", "no_clear_flow"}
    if composed["local_flow_stance"] in {"with_flow", "against_flow"}:
        assert composed["shadow_size_tilt"] != 1.0
        assert composed["shadow_size_tilt"] in {0.70, 1.15}
        assert composed["live_size_tilt"] == composed["shadow_size_tilt"]
    else:
        assert composed["shadow_size_tilt"] == 1.0


def test_a8_named_from_challenge_m15():
    books = load_challenge_books()
    feats = features_from_books(books, AS_OF, tag="dsp_two_bar_t")
    assert feats["a8_source"] == "challenge_m15_metals_a8"
    assert feats["htf_slope_norm"] is not None
    assert feats["mom_20_atr"] is not None
    assert feats["a8_k_of_4_pass"] in {True, False}
    state = intent_gold_state(_Intent(), origin="f5_challenge", as_of_utc=AS_OF)
    answers = local_answers(state, extra={"kind": "slate"}, ticket="292667008")
    assert answers["a8_agrees"]["decidable"] is True
    assert answers["a8_agrees"]["noul"] in {True, False}


def test_calendar_honest_false_when_host_writer_unread():
    state = {
        "identity": {"symbol": "XAUUSD", "side": "short", "family_class": "study", "sleeve": "dsp_two_bar_t"},
        "completeness": {"state_sufficient_for_live": True},
        "news": {
            "spine_empty": False,
            "events": [{"event": "CPI"}],
            "challenge_axis_covering": True,
            "high_in_f5_window": False,
        },
        "cost": {},
        "timeframes": {"h4": {"trend": 1}},
        "sessions": {"named": "london"},
        "clock": {"is_friday": False},
        "occupancy": {},
        "sleeve_features": {},
        "geometry": {},
    }
    honest = local_answers(state, extra={"kind": "slate"}, ticket="1")
    assert honest["calendar_honest"]["noul"] is True
    unread = local_answers(
        state,
        extra={"kind": "slate", "host_news_inventory_status": "NOT_READ", "host_news_n_in_window": 0},
        ticket="1",
    )
    assert unread["calendar_honest"]["noul"] is False
    assert unread["calendar_honest"]["decidable"] is True
    unknown = local_answers(
        state,
        extra={"kind": "slate", "host_news_inventory_status": "UNKNOWN"},
        ticket="1",
    )
    assert unknown["calendar_honest"]["noul"] is False
    writer_none = local_answers(
        state,
        extra={
            "kind": "slate",
            "host_news_source": "challenge_host_news_writer",
            "host_news_inventory_status": None,
        },
        ticket="1",
    )
    assert writer_none["calendar_honest"]["noul"] is False
    read_ok = local_answers(
        state,
        extra={
            "kind": "slate",
            "host_news_source": "challenge_host_news_writer",
            "host_news_inventory_status": "READ",
            "host_news_n_in_window": 1,
        },
        ticket="1",
    )
    assert read_ok["calendar_honest"]["noul"] is True


def test_host_events_trail_eps_ignores_monitor_jitter():
    assert sl_differs(4336.90, 4336.905) is False
    assert sl_differs(4336.90, 4337.00) is True
    assert sl_differs(None, 4336.90) is None
    assert named_final_sl(deal_final=4336.9, event_stop_now=4340.0) == 4336.9
    assert named_final_sl(deal_final=None, event_stop_now=4340.0) == 4340.0


def test_news_inventory_prefers_named_status_and_stays_unread():
    events = [
        {
            "event": "news_t60_expiry_reeval",
            "ts_utc": "2026-09-17T07:30:51Z",
            "inventory_status": None,
            "n_events_in_window": None,
        },
        {
            "event": "news_t15_pending_cancel",
            "ts_utc": "2026-09-17T07:31:10Z",
            "inventory_status": "NOT_READ",
            "n_events_in_window": 0,
        },
    ]
    inv = news_inventory_at(events, AS_OF)
    assert inv["host_news_source"] == "challenge_host_news_writer"
    assert inv["host_news_inventory_status"] == "NOT_READ"
    assert inv["host_news_n_in_window"] == 0
    far = news_inventory_at(events, datetime(2026, 9, 9, 9, 3, tzinfo=timezone.utc))
    assert far["host_news_source"] == "unassembled"


def test_challenge_axis_covering_named_on_september_as_of():
    news = attach_news(AS_OF, spines=load_spines())
    assert news["spine_empty"] is False
    assert news["challenge_axis_covering"] is True
    assert news["n_challenge_axis_nearby"] >= 1
