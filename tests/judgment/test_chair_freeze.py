"""Chair FREEZE — SHADOW ready Choice on symbol_state and gold_state.

Edge fixtures t1–t4. Never admit. No NEWS_PROTOCOL invent.
BOJ 1.25% / 2026-09-24 is bucket timing only unless a spine stamp exists.
"""

from datetime import datetime, timezone

from src.judgment.chair_wires import (
    BOJ_LIVE,
    BOJ_RATE_FACT,
    IDENTITY_RESID_MAX,
    READY_CHOICES,
    boj_bucket,
)
from src.judgment.gold_state import assemble_gold_state_v0
from src.judgment.symbol_class import field_map
from src.judgment.symbol_state import assemble_symbol_state_v0
from tests.judgment.test_symbol_state import (
    AS_OF,
    EMPTY_SPINE,
    FIXTURES,
    _assemble,
    _books,
    _boj_print_spine,
    _covering_spine,
)


def _assert_ready(row, choice):
    assert row["choice"] == choice
    assert row["choice"] in READY_CHOICES
    assert row["choice"] != "admit"
    assert row["admit"] is None
    assert row["never_admit_choice"] is True
    assert row["apply"] is False
    assert row["shadow"] is True


def test_field_map_freeze_ready_and_boj():
    mapped = field_map()
    assert mapped["ready_choices"] == list(READY_CHOICES)
    assert mapped["identity_resid_max"] == IDENTITY_RESID_MAX == 0.15
    assert mapped["boj_rate_fact"]["rate_pct"] == 1.25
    assert mapped["boj_rate_fact"]["effective_date_utc"] == "2026-09-24"
    assert mapped["boj_rate_fact"]["use"] == "bucket_timing_only"
    assert set(mapped["boj_live"]) == set(BOJ_LIVE)
    assert mapped["never_admit_choice"] is True
    assert "NEWS_PROTOCOL" in mapped["never_invent"]
    assert mapped["n_non_xau_sufficient"] == 45
    assert mapped["non_xau_uses_symbol_state"] is True


def test_boj_rate_fact_timing_never_invents_print_or_guidance():
    empty = {"events": [], "spine_empty": True}
    pre = boj_bucket(datetime(2026, 9, 17, 11, 5, tzinfo=timezone.utc), empty)
    assert pre["label"] == "pre_effective"
    assert pre["source"] == "rate_fact_timing"
    assert pre["stamped"] is None
    assert pre["rate_fact"]["rate_pct"] == BOJ_RATE_FACT["rate_pct"] == 1.25
    assert pre["rate_fact"]["effective_date_utc"] == "2026-09-24"
    assert pre["rate_fact"]["use"] == "bucket_timing_only"
    assert pre["never_invent_news_protocol"] is True
    win = boj_bucket(datetime(2026, 9, 24, 0, tzinfo=timezone.utc), empty)
    assert win["label"] == "effective_window"
    assert win["source"] == "rate_fact_timing"
    assert win["label"] not in BOJ_LIVE
    post = boj_bucket(datetime(2026, 9, 26, 12, tzinfo=timezone.utc), empty)
    assert post["label"] == "post_effective"
    untitled = boj_bucket(
        AS_OF,
        {
            "events": [
                {
                    "event": "BOJ policy rate",
                    "currency": "JPY",
                    "datetime_utc": "2026-09-17T11:00:00Z",
                }
            ]
        },
    )
    assert untitled["label"] not in BOJ_LIVE
    assert untitled["source"] == "rate_fact_timing"
    assert untitled["stamped"] is None


def test_boj_print_and_guidance_live_require_spine_stamp():
    printed = boj_bucket(
        AS_OF,
        {
            "events": [
                {
                    "event": "BOJ policy rate",
                    "currency": "JPY",
                    "minutes_from_as_of": -10,
                    "datetime_utc": "2026-09-17T10:55:00Z",
                }
            ]
        },
    )
    assert printed["label"] == "print"
    assert printed["source"] == "spine_stamp"
    assert printed["boj_clear"] is False
    guidance = boj_bucket(
        AS_OF,
        {
            "events": [
                {
                    "event": "BOJ Governor Ueda press conference",
                    "currency": "JPY",
                    "minutes_from_as_of": 5,
                    "datetime_utc": "2026-09-17T11:10:00Z",
                }
            ]
        },
    )
    assert guidance["label"] == "guidance_live"
    assert guidance["source"] == "spine_stamp"
    assert guidance["boj_clear"] is False


def test_edge_t1_t4_gbpjpy_on_symbol_and_gold():
    peers = {"GBPUSD": _books(1.3400, 0.00012, half=0.0003), "USDJPY": FIXTURES["USDJPY"]["books"]}
    gold_kwargs = dict(
        side="long",
        sleeve="vss_fxcross_london_up_low",
        symbol="GBPJPY",
        origin_organism="f5_challenge",
        books=FIXTURES["GBPJPY"]["books"],
        geometry=FIXTURES["GBPJPY"]["geo"],
        cost=FIXTURES["GBPJPY"]["cost"],
        sleeve_features={"tag": "vss_fxcross_london_up_low"},
        peer_books=peers,
    )
    t1_s = _assemble("GBPJPY", peer_books=peers)
    t1_g = assemble_gold_state_v0(as_of_utc=AS_OF, spines=EMPTY_SPINE, **gold_kwargs)
    for state in (t1_s, t1_g):
        ready = state["sleeve"]["gbpjpy_a_plus_ready"]
        _assert_ready(ready, "a_plus")
        assert ready["conjuncts"] == {
            "session_ok": True,
            "identity_ok": True,
            "agree": True,
            "dual_same": True,
            "boj_clear": True,
        }
        assert abs(ready["resid"]) <= IDENTITY_RESID_MAX
        assert state["information"]["boj_bucket"]["label"] == "pre_effective"

    t2_s = _assemble("GBPJPY", peer_books=peers, as_of=datetime(2026, 9, 17, 18, 0, tzinfo=timezone.utc))
    t2_g = assemble_gold_state_v0(
        as_of_utc=datetime(2026, 9, 17, 18, 0, tzinfo=timezone.utc),
        spines=EMPTY_SPINE,
        **gold_kwargs,
    )
    for state in (t2_s, t2_g):
        _assert_ready(state["sleeve"]["gbpjpy_a_plus_ready"], "almost")
        assert state["sessions"]["named"] == "ny"
        assert state["sessions"]["in_ldn_ny_overlap"] is False
        assert state["sleeve"]["gbpjpy_a_plus_ready"]["conjuncts"]["session_ok"] is False

    t3_s = _assemble("GBPJPY", peer_books=peers, spines=_boj_print_spine(AS_OF))
    t3_g = assemble_gold_state_v0(as_of_utc=AS_OF, spines=_boj_print_spine(AS_OF), **gold_kwargs)
    for state in (t3_s, t3_g):
        _assert_ready(state["sleeve"]["gbpjpy_a_plus_ready"], "blocked")
        assert state["information"]["boj_bucket"]["label"] == "print"
        assert state["information"]["boj_bucket"]["source"] == "spine_stamp"

    t4_s = _assemble("GBPJPY")
    t4_g = assemble_gold_state_v0(
        as_of_utc=AS_OF,
        side="long",
        sleeve="vss_fxcross_london_up_low",
        symbol="GBPJPY",
        origin_organism="f5_challenge",
        books=FIXTURES["GBPJPY"]["books"],
        spines=EMPTY_SPINE,
        geometry=FIXTURES["GBPJPY"]["geo"],
        cost=FIXTURES["GBPJPY"]["cost"],
        sleeve_features={"tag": "vss_fxcross_london_up_low"},
    )
    for state in (t4_s, t4_g):
        _assert_ready(state["sleeve"]["gbpjpy_a_plus_ready"], "null_state")
        assert state["cross"]["gbpjpy"]["present"] is False


def test_edge_t1_t4_xau_on_symbol_and_gold():
    xau = _books(4330.0, -1.0, half=2.0)
    peers = {
        "USDJPY": FIXTURES["USDJPY"]["books"],
        "EURUSD": _books(1.1700, -0.00015, half=0.0004),
    }
    kwargs = dict(
        side="short",
        sleeve="dsp_shakeout_holds_run_lows",
        symbol="XAUUSD",
        origin_organism="f5_challenge",
        books=xau,
        geometry=FIXTURES["XAUUSD"]["geo"],
        cost=FIXTURES["XAUUSD"]["cost"],
        sleeve_features={"tag": "dsp_shakeout_holds_run_lows"},
        peer_books=peers,
    )
    t1_s = assemble_symbol_state_v0(as_of_utc=AS_OF, spines=_covering_spine(AS_OF), **kwargs)
    t1_g = assemble_gold_state_v0(as_of_utc=AS_OF, spines=_covering_spine(AS_OF), **kwargs)
    for state in (t1_s, t1_g):
        ready = state["sleeve"]["xau_dsp_shakeout_ready"]
        _assert_ready(ready, "a_plus")
        assert ready["conjuncts"]["event_gap_ok"] is True
        assert ready["usd_proxy_source"] == "peers.usdjpy"
        assert state["peers"]["usd_proxy_vs_xau"]["primary_peer"] == "USDJPY"
        assert state["peers"]["usd_proxy_vs_xau"]["alias"] is False
        assert state["completeness"]["state_sufficient_for_live"] is True

    disagree = {**kwargs, "peer_books": {"USDJPY": _books(148.20, -0.02, half=0.04), "EURUSD": peers["EURUSD"]}}
    t2_s = assemble_symbol_state_v0(as_of_utc=AS_OF, spines=_covering_spine(AS_OF), **disagree)
    t2_g = assemble_gold_state_v0(as_of_utc=AS_OF, spines=_covering_spine(AS_OF), **disagree)
    for state in (t2_s, t2_g):
        _assert_ready(state["sleeve"]["xau_dsp_shakeout_ready"], "almost")
        assert state["sleeve"]["xau_dsp_shakeout_ready"]["usd_proxy_source"] == "peers.usdjpy"

    t3_s = assemble_symbol_state_v0(as_of_utc=AS_OF, spines=EMPTY_SPINE, **kwargs)
    t3_g = assemble_gold_state_v0(as_of_utc=AS_OF, spines=EMPTY_SPINE, **kwargs)
    for state in (t3_s, t3_g):
        ready = state["sleeve"]["xau_dsp_shakeout_ready"]
        _assert_ready(ready, "blocked")
        assert ready["event_gap"] == "fail_closed_empty_spine"

    empty_kwargs = dict(
        side="short",
        sleeve="dsp_shakeout_holds_run_lows",
        symbol="XAUUSD",
        origin_organism="f5_challenge",
        books=None,
        spines=EMPTY_SPINE,
        geometry=FIXTURES["XAUUSD"]["geo"],
        cost=FIXTURES["XAUUSD"]["cost"],
        sleeve_features={"tag": "dsp_shakeout_holds_run_lows"},
    )
    t4_s = assemble_symbol_state_v0(as_of_utc=AS_OF, **empty_kwargs)
    t4_g = assemble_gold_state_v0(as_of_utc=AS_OF, **empty_kwargs)
    for state in (t4_s, t4_g):
        _assert_ready(state["sleeve"]["xau_dsp_shakeout_ready"], "null_state")
        assert state["completeness"]["state_sufficient_for_live"] is False
