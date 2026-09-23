from datetime import datetime, timezone

import pytest

from src.judgment.family import family_class_for
from src.judgment.gold_state import assemble_gold_state_v0, reject_expost
from src.judgment.news_spine import attach_news, load_spines
from tests.judgment.test_symbol_state import (
    AS_OF,
    EMPTY_SPINE,
    FIXTURES,
    _books,
    _boj_print_spine,
    _covering_spine,
)


def test_missing_calendar_or_uncovered_as_of_is_spine_empty():
    spines = {"spine_id": "x", "sources": [], "events": [], "n_files": 0}
    news = attach_news(datetime(2026, 4, 15, 12, tzinfo=timezone.utc), spines=spines)
    assert news["spine_empty"] is True
    assert news["events"] == []
    assert news["high_in_f5_window"] is None


def test_june_spine_covers_only_those_days():
    spines = load_spines()
    covered = attach_news(datetime(2026, 6, 5, 12, 30, tzinfo=timezone.utc), spines=spines)
    uncovered = attach_news(datetime(2026, 4, 15, 12, tzinfo=timezone.utc), spines=spines)
    # June week of record is on disk; April gold lab stays empty unless a real spine overlaps.
    if any("news_calendar.json" in s for s in spines["sources"]):
        assert covered["spine_empty"] is False
    assert uncovered["spine_empty"] is True or not any(
        e["datetime_utc"].startswith("2026-04-") for e in uncovered["events"]
    )


def test_host_f5_calendar_is_challenge_axis_and_parses_scheduled_utc():
    spines = load_spines()
    assert any("f5_high_calendar_host_20260916.json" in s for s in spines["sources"])
    assert spines.get("n_challenge_axis", 0) >= 13
    open_asof = attach_news(datetime(2026, 9, 17, 7, 30, 55, tzinfo=timezone.utc), spines=spines)
    assert open_asof["spine_empty"] is False
    host_hits = [e for e in open_asof["events"] if e.get("challenge_axis")]
    assert host_hits, "host Warsh-class calendar must cover ticket 293332188 as-of"
    # BOE 11:00Z is +209 min at 07:30Z — not yet in F5 T-15..T+60.
    assert open_asof["high_in_f5_window"] is False
    boe_window = attach_news(datetime(2026, 9, 17, 11, 0, tzinfo=timezone.utc), spines=spines)
    assert boe_window["high_in_f5_window"] is True
    assert any("BOE" in (e.get("event") or "") for e in boe_window["events"])


def test_expost_rejected_on_live_intent():
    with pytest.raises(ValueError, match="EXPOST"):
        assemble_gold_state_v0(
            as_of_utc=datetime(2026, 4, 15, 12, tzinfo=timezone.utc),
            side="short",
            sleeve="dsp_two_bar_t",
            as_of_clock="live_intent",
            extra={"broker_net": -12.0},
        )


def test_reject_expost_lists_keys():
    assert reject_expost({"R": -1.0, "entry": 1}, "live_intent") == ["R"]


def test_state_sufficient_false_without_timeframes():
    state = assemble_gold_state_v0(
        as_of_utc=datetime(2026, 4, 15, 12, tzinfo=timezone.utc),
        side="short",
        sleeve="dsp_two_bar_t",
        origin_organism="f5_challenge",
        books=None,
    )
    assert state["completeness"]["timeframes_m15_h4"] is False
    assert state["completeness"]["timeframes_m15_h4_d1"] is False
    assert state["completeness"]["state_sufficient_for_live"] is False
    assert "timeframes.m15" in state["completeness"]["missing_fields"]
    assert state["clock"]["weekday"] == 2  # Wednesday 2026-04-15, Monday=0


def test_family_class_mapping():
    assert family_class_for("dsp_spring_xau") == "house_keep"
    assert family_class_for("vss_fxcross_london_up_low") == "house_keep"
    assert family_class_for("dsp_bleed_hi") == "house_hard_off"
    assert family_class_for("dsp_two_bar_t") == "study"
    assert family_class_for("kz_london_cry", symbol="BTCUSD") == "house_hard_off"
    assert family_class_for("metals_core", origin="w7_ultimate_book") == "w7_metals"
    assert family_class_for("crypto", origin="w7_ultimate_book") == "w7_sleeve"
    assert family_class_for("", origin="f5_challenge") == "unknown"
    assert family_class_for("aplus_xau_london_ob_retest") == "a_plus_study"
    assert family_class_for("aplus_gbpjpy_london_session_sweep", origin="w7_ultimate_book") == "a_plus_study"
    assert family_class_for("aplus_eurusd_london_session_reclaim") == "a_plus_study"
    assert family_class_for("a_plus_xau_london_htf_align") == "a_plus_study"


def test_gold_state_pack4_paths_shadow_no_admit_us30_off():
    xau = _books(4330.0, -1.0, half=2.0)
    state = assemble_gold_state_v0(
        as_of_utc=AS_OF,
        side="short",
        sleeve="dsp_two_bar_t",
        symbol="XAUUSD",
        origin_organism="f5_challenge",
        books=xau,
        spines=EMPTY_SPINE,
        geometry=FIXTURES["XAUUSD"]["geo"],
        cost=FIXTURES["XAUUSD"]["cost"],
        sleeve_features={"tag": "dsp_two_bar_t"},
        peer_books={"EURUSD": FIXTURES["EURUSD"]["books"], "USDJPY": FIXTURES["USDJPY"]["books"]},
        surface={"us30_off": False},
    )
    assert state["schema"] == "gtos.judgment.gold_state.v0"
    assert state["sessions"]["in_ldn_ny_overlap"] is False
    assert "london_expand_ok" in state["sessions"]
    assert "london_expand_range" in state["sessions"]
    assert "london_expand_vol" in state["sessions"]
    assert state["sessions"]["ny_rth_us30"] is False
    assert state["cluster"]["eur_gbp"]["members"] == ["EURUSD", "GBPUSD", "EURGBP"]
    assert "gbpjpy" in state["cross"]
    assert state["information"]["boj_bucket"]["label"] == "pre_effective"
    assert state["information"]["boj_bucket"]["rate_fact"]["rate_pct"] == 1.25
    assert state["sleeve"]["gbpjpy_a_plus_ready"]["admit"] is None
    assert state["sleeve"]["xau_dsp_shakeout_ready"]["never_admit_choice"] is True
    assert "admit" not in state["chair_wires"]
    assert state["chair_wires"]["apply"] is False
    assert state["surface"]["us30_off"] is True
    assert state["completeness"]["chair_wires"] is True
    assert state["completeness"]["state_sufficient_for_live"] is True


def test_gold_state_usd_proxy_usdjpy_primary_eur_alias():
    xau = _books(4330.0, -1.0, half=2.0)
    primary = assemble_gold_state_v0(
        as_of_utc=AS_OF,
        side="short",
        sleeve="dsp_two_bar_t",
        symbol="XAUUSD",
        origin_organism="f5_challenge",
        books=xau,
        spines=EMPTY_SPINE,
        geometry=FIXTURES["XAUUSD"]["geo"],
        cost=FIXTURES["XAUUSD"]["cost"],
        sleeve_features={"tag": "dsp_two_bar_t"},
        peer_books={"EURUSD": _books(1.1700, -0.00015, half=0.0004), "USDJPY": FIXTURES["USDJPY"]["books"]},
    )
    row = primary["peers"]["usd_proxy_vs_xau"]
    assert row["primary_peer"] == "USDJPY"
    assert row["alias"] is False
    assert row["source"] == "peers.usdjpy"
    assert primary["peers"]["xau_eur_proxy"]["used"] is False
    alias = assemble_gold_state_v0(
        as_of_utc=AS_OF,
        side="short",
        sleeve="dsp_two_bar_t",
        symbol="XAUUSD",
        origin_organism="f5_challenge",
        books=xau,
        spines=EMPTY_SPINE,
        geometry=FIXTURES["XAUUSD"]["geo"],
        cost=FIXTURES["XAUUSD"]["cost"],
        sleeve_features={"tag": "dsp_two_bar_t"},
        peer_books={"EURUSD": _books(1.1700, -0.00015, half=0.0004)},
    )
    arow = alias["peers"]["usd_proxy_vs_xau"]
    assert arow["alias"] is True
    assert arow["source"] == "xau_eur_proxy"
    assert alias["peers"]["xau_eur_proxy"]["used"] is True


def test_gold_state_xau_ready_edge_t1_t4():
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
    t1 = assemble_gold_state_v0(as_of_utc=AS_OF, spines=_covering_spine(AS_OF), **kwargs)
    ready = t1["sleeve"]["xau_dsp_shakeout_ready"]
    assert t1["completeness"]["state_sufficient_for_live"] is True
    assert ready["choice"] == "a_plus"
    assert ready["admit"] is None
    assert ready["usd_proxy_source"] == "peers.usdjpy"
    t2 = assemble_gold_state_v0(
        as_of_utc=AS_OF,
        spines=_covering_spine(AS_OF),
        **{**kwargs, "peer_books": {"USDJPY": _books(148.20, -0.02, half=0.04), "EURUSD": peers["EURUSD"]}},
    )
    assert t2["sleeve"]["xau_dsp_shakeout_ready"]["choice"] == "almost"
    t3 = assemble_gold_state_v0(as_of_utc=AS_OF, spines=EMPTY_SPINE, **kwargs)
    assert t3["sleeve"]["xau_dsp_shakeout_ready"]["event_gap"] == "fail_closed_empty_spine"
    assert t3["sleeve"]["xau_dsp_shakeout_ready"]["choice"] == "blocked"
    t4 = assemble_gold_state_v0(
        as_of_utc=AS_OF,
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
    assert t4["sleeve"]["xau_dsp_shakeout_ready"]["choice"] == "null_state"
    assert t4["completeness"]["state_sufficient_for_live"] is False


def test_gold_state_gbpjpy_ready_binds_conjuncts():
    peers = {"GBPUSD": _books(1.3400, 0.00012, half=0.0003), "USDJPY": FIXTURES["USDJPY"]["books"]}
    t1 = assemble_gold_state_v0(
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
        peer_books=peers,
    )
    ready = t1["sleeve"]["gbpjpy_a_plus_ready"]
    assert ready["choice"] == "a_plus"
    assert ready["admit"] is None
    assert ready["conjuncts"]["session_ok"] is True
    assert ready["conjuncts"]["identity_ok"] is True
    assert ready["conjuncts"]["agree"] is True
    assert ready["conjuncts"]["dual_same"] is True
    assert ready["conjuncts"]["boj_clear"] is True
    t3 = assemble_gold_state_v0(
        as_of_utc=AS_OF,
        side="long",
        sleeve="vss_fxcross_london_up_low",
        symbol="GBPJPY",
        origin_organism="f5_challenge",
        books=FIXTURES["GBPJPY"]["books"],
        spines=_boj_print_spine(AS_OF),
        geometry=FIXTURES["GBPJPY"]["geo"],
        cost=FIXTURES["GBPJPY"]["cost"],
        sleeve_features={"tag": "vss_fxcross_london_up_low"},
        peer_books=peers,
    )
    assert t3["information"]["boj_bucket"]["label"] == "print"
    assert t3["sleeve"]["gbpjpy_a_plus_ready"]["choice"] == "blocked"
