"""SYMBOL_STATE_V0 — XAU + EURUSD + USDJPY + US30 + GBPJPY. No APPLY. No place."""

from datetime import datetime, timedelta, timezone

from src.components.ultimate_book.primitives import Bar
from src.judgment.a1_log import intent_gold_state, intent_symbol_state
from src.judgment.apply_size import maybe_haircut_unit
from src.judgment.bars import StampedBar, load_challenge_books
from src.judgment.challenge_shadow import score_position
from src.judgment.compose import compose_shadow
from tests.judgment.cages import assert_live_cages
from src.judgment.gold_state import assemble_gold_state_v0
from src.judgment.symbol_class import (
    UNIVERSAL_BLOCKS,
    asset_class_for,
    field_map,
    news_currencies_for,
    peer_symbols_for,
    pip_scale,
    usd_from_pair_trend,
    usd_leg,
)
from src.judgment.non_xau_remeasure import (
    NON_XAU_REMEASURE_N,
    remasure_non_xau_sufficient,
)
from src.judgment.symbol_state import (
    SCHEMA,
    SIBLING_OF,
    assemble_symbol_peers,
    assemble_symbol_state_v0,
)

AS_OF = datetime(2026, 9, 17, 11, 5, tzinfo=timezone.utc)
EMPTY_SPINE = {"spine_id": None, "sources": [], "events": [], "n_files": 0}
CHALLENGE_AS_OF = datetime(2026, 9, 17, 7, 30, 55, tzinfo=timezone.utc)


def _tf_book(
    n: int,
    start: datetime,
    step_hours: float,
    closes: list[float] | None = None,
    *,
    half_range: float = 0.0008,
) -> list[StampedBar]:
    out: list[StampedBar] = []
    for i in range(n):
        utc = start + timedelta(hours=step_hours * i)
        close = closes[i] if closes and i < len(closes) else (closes[-1] if closes else 1.0)
        if closes is None:
            close = 1.0 + 0.0001 * i
        out.append(
            StampedBar(
                broker_naive=utc.replace(tzinfo=None) + timedelta(hours=3),
                utc=utc,
                bar=Bar(o=close, h=close + half_range, l=close - half_range, c=close, v=1.0),
                source_path="tmp",
            )
        )
    return out


def _books(start_px: float, step: float, *, half: float) -> dict[str, list[StampedBar]]:
    # 32 M15 from 05:00Z → 21+ closed bars at AS_OF 11:05 (comove_20 needs 21).
    m15_start = datetime(2026, 9, 17, 5, 0, tzinfo=timezone.utc)
    h4_start = datetime(2026, 9, 16, 1, 0, tzinfo=timezone.utc)
    d1_start = datetime(2026, 9, 9, 0, 0, tzinfo=timezone.utc)
    return {
        "m15": _tf_book(32, m15_start, 0.25, [start_px + step * i for i in range(32)], half_range=half),
        "h4": _tf_book(16, h4_start, 4.0, [start_px + step * 4 * i for i in range(16)], half_range=half * 4),
        "d1": _tf_book(10, d1_start, 24.0, [start_px + step * 16 * i for i in range(10)], half_range=half * 8),
    }


def _geo(entry: float, stop: float) -> dict:
    return {"entry": entry, "stop": stop, "stop_dist": abs(entry - stop), "order_type": "MARKET"}


FIXTURES = {
    "XAUUSD": {
        "asset": "metal",
        "sleeve": "dsp_two_bar_t",
        "side": "short",
        "books": None,  # Challenge tape when present
        "geo": _geo(4331.45, 4336.9),
        "cost": {"spread_r_of_stop": 0.08},
        "news_ccy": ("XAU", "USD", "ALL"),
    },
    "EURUSD": {
        "asset": "fx",
        "sleeve": "vss_fxcross_london_up_low",
        "side": "long",
        "books": _books(1.1700, 0.00015, half=0.0004),
        "geo": _geo(1.1720, 1.1695),
        "cost": {"spread_r_of_stop": 0.04},
        "news_ccy": ("EUR", "USD", "ALL"),
    },
    "USDJPY": {
        "asset": "fx",
        "sleeve": "vss_fxcross_london_up_low",
        "side": "short",
        "books": _books(148.20, 0.02, half=0.04),
        "geo": _geo(148.10, 148.45),
        "cost": {"spread_r_of_stop": 0.06},
        "news_ccy": ("USD", "JPY", "ALL"),
    },
    "US30": {
        "asset": "index",
        "sleeve": "mx_us30_d1_donchian",
        "side": "long",
        "books": _books(46200.0, 8.0, half=12.0),
        "geo": _geo(46300.0, 46150.0),
        "cost": {"spread_r_of_stop": 0.09},
        "news_ccy": ("USD", "ALL"),
    },
    "GBPJPY": {
        "asset": "fx",
        "sleeve": "vss_fxcross_london_up_low",
        "side": "long",
        "books": _books(199.40, 0.03, half=0.05),
        "geo": _geo(199.80, 199.20),
        "cost": {"spread_r_of_stop": 0.07},
        "news_ccy": ("GBP", "JPY", "ALL", "USD"),
    },
}


def _assemble(symbol: str, **overrides):
    spec = FIXTURES[symbol]
    books = overrides.get("books", spec["books"])
    if books is None and symbol == "XAUUSD":
        books = load_challenge_books("XAUUSD")
        as_of = CHALLENGE_AS_OF
    else:
        as_of = overrides.get("as_of", AS_OF)
    return assemble_symbol_state_v0(
        as_of_utc=as_of,
        side=overrides.get("side", spec["side"]),
        sleeve=overrides.get("sleeve", spec["sleeve"]),
        symbol=symbol,
        origin_organism="f5_challenge",
        books=books,
        spines=overrides.get("spines", EMPTY_SPINE),
        geometry=overrides.get("geometry", spec["geo"]),
        cost=overrides.get("cost", spec["cost"]),
        sleeve_features=overrides.get("sleeve_features", {"tag": spec["sleeve"]}),
        peer_books=overrides.get("peer_books"),
        occupancy=overrides.get("occupancy", {}),
    )


def test_field_map_names_universal_vs_class_specific():
    mapped = field_map()
    assert mapped["universal"] == list(UNIVERSAL_BLOCKS)
    assert "class_specific.fx.usd_leg" in mapped["class_specific"]["fx"]
    assert "class_specific.metal.a8_source" in mapped["class_specific"]["metal"]
    assert "class_specific.index.house_us30_off" in mapped["class_specific"]["index"]
    assert "DXY" in mapped["never_invent"]
    assert "TIPS" in mapped["never_invent"]
    assert "NEWS_PROTOCOL" in mapped["never_invent"]
    assert mapped["gate_flow"] == "a_plus_sleeve_on_gate_flow"
    assert mapped["side_catalog"] is False
    assert mapped["chair_wires_apply"] is False
    assert "usd_proxy_vs_xau" in mapped["chair_wires"]
    assert "tokyo_fix_window_label" in mapped["chair_wires"]
    assert "session.in_ldn_ny_overlap" in mapped["gold_state_extensions"]
    assert "peers.usd_proxy_vs_xau" in mapped["gold_state_extensions"]
    assert mapped["never_admit_choice"] is True
    assert mapped["ready_choices"] == ["a_plus", "almost", "blocked", "null_state"]
    assert mapped["boj_rate_fact"]["rate_pct"] == 1.25
    assert mapped["boj_rate_fact"]["effective_date_utc"] == "2026-09-24"
    assert mapped["n_non_xau_sufficient"] == 45
    assert mapped["non_xau_uses_symbol_state"] is True
    assert mapped["us30_hard_off"] is True


def test_asset_class_and_usd_leg_code_facts():
    assert asset_class_for("XAUUSD") == "metal"
    assert asset_class_for("EURUSD") == "fx"
    assert asset_class_for("USDJPY") == "fx"
    assert asset_class_for("US30.cash") == "index"
    assert asset_class_for("GBPJPY") == "fx"
    assert usd_leg("EURUSD") == "quote"
    assert usd_leg("USDJPY") == "base"
    assert usd_leg("GBPJPY") is None
    assert usd_from_pair_trend("EURUSD", 1) == -1
    assert usd_from_pair_trend("USDJPY", 1) == 1
    assert usd_from_pair_trend("GBPJPY", 1) is None
    assert pip_scale("EURUSD") == 0.0001
    assert pip_scale("USDJPY") == 0.01
    assert pip_scale("GBPJPY") == 0.01
    assert pip_scale("US30") == 1.0
    assert news_currencies_for("GBPJPY") == ("GBP", "JPY", "ALL", "USD")
    assert "USDJPY" in peer_symbols_for("XAUUSD")
    assert "XAUUSD" in peer_symbols_for("GBPJPY")


def test_each_fixture_is_sufficient_and_never_not_xau_primary():
    for symbol, spec in FIXTURES.items():
        state = _assemble(symbol)
        assert state["schema"] == SCHEMA
        assert state["sibling_of"] == SIBLING_OF
        assert state["never_place"] is True
        assert state["never_remint"] is True
        assert state["never_flatten"] is True
        assert state["never_invent_news_protocol"] is True
        assert state["never_invent_dxy"] is True
        assert state["never_invent_tips"] is True
        assert state["identity"]["symbol"] == ("US30" if symbol == "US30" else symbol)
        assert state["never_apply_size_on_non_xau"] is True
        assert state["identity"]["asset_class"] == spec["asset"]
        assert state["completeness"]["timeframes_m15_h4"] is True
        assert state["completeness"]["state_sufficient_for_live"] is True
        assert "timeframes.m15" not in state["completeness"]["missing_fields"]
        assert "timeframes.h4" not in state["completeness"]["missing_fields"]
        sources = [row.get("source") for row in (state.get("peers") or {}).values()]
        assert "not_xau_primary" not in sources
        assert state["news"]["relevant_currencies"] == list(spec["news_ccy"])
        assert state["world"].get("dxy") is None or "never_invent_dxy" in state["world"]
        assert "US10Y" not in state
        if symbol == "XAUUSD":
            assert state["gold_state"]["schema"] == "gtos.judgment.gold_state.v0"
        else:
            assert state.get("gold_state") is None
        assert state["sleeve"]["schema"] == "gtos.judgment.sleeve.v0"
        assert state["sleeve"]["side_catalog"] is False
        assert state["sleeve"]["gate_flow"] == "a_plus_sleeve_on_gate_flow"
        assert state["gate_flow"]["name"] == "a_plus_sleeve_on_gate_flow"
        assert state["gate_flow"]["same_as_live_challenge"] is True
        assert state["completeness"]["sleeve"] is True
        assert state["completeness"]["gate_flow"] is True
        assert state["completeness"]["chair_wires"] is True
        assert state["chair_wires"]["apply"] is False
        assert state["chair_wires"]["shadow"] is True
        assert state["chair_wires"]["never_invent_dxy"] is True
        assert state["chair_wires"]["never_invent_tips"] is True
        assert "dxy" not in state["chair_wires"]
        assert "tips" not in state["chair_wires"]
        assert state["clock"]["tokyo_fix_window_label"] in {"tokyo_fix", "outside"}
        assert state["sleeve"]["ca_labels"]["chair_wires_apply"] is False
        assert state["sleeve"]["ca_labels"]["never_invent_tips"] is True


def test_xau_symbol_state_wraps_gold_and_keeps_sufficient():
    gold = assemble_gold_state_v0(
        as_of_utc=CHALLENGE_AS_OF,
        side="short",
        sleeve="dsp_two_bar_t",
        symbol="XAUUSD",
        origin_organism="f5_challenge",
        books=load_challenge_books("XAUUSD"),
        spines=EMPTY_SPINE,
        geometry=FIXTURES["XAUUSD"]["geo"],
        cost=FIXTURES["XAUUSD"]["cost"],
        sleeve_features={"tag": "dsp_two_bar_t"},
    )
    state = _assemble("XAUUSD")
    assert gold["completeness"]["state_sufficient_for_live"] is True
    assert state["completeness"]["state_sufficient_for_live"] is True
    assert state["gold_state"]["schema"] == "gtos.judgment.gold_state.v0"
    assert state["class_specific"]["metal"]["usd_sensitivity"] == "usd_proxy_only"
    assert state["surface"]["apply_named_wires"] is True
    assert state["surface"]["symbol_state_observe_only"] is False


def test_fx_and_index_class_blocks():
    eurusd = _assemble("EURUSD")
    usdjpy = _assemble("USDJPY")
    gbpjpy = _assemble("GBPJPY")
    us30 = _assemble("US30")
    assert eurusd["class_specific"]["fx"]["pair"] == {"base": "EUR", "quote": "USD"}
    assert eurusd["class_specific"]["fx"]["usd_leg"] == "quote"
    assert eurusd["class_specific"]["fx"]["session_bias"] == "london"
    assert usdjpy["class_specific"]["fx"]["usd_leg"] == "base"
    assert gbpjpy["class_specific"]["fx"]["usd_leg"] is None
    assert gbpjpy["class_specific"]["fx"]["relevant_news_ccys"] == ["GBP", "JPY", "ALL", "USD"]
    assert us30["class_specific"]["index"]["cash_alias"] == "US30.cash"
    assert us30["class_specific"]["index"]["house_us30_off"] is True
    assert us30["surface"]["us30_off"] is True
    assert us30["surface"]["apply_named_wires"] is False
    assert us30["surface"]["symbol_state_observe_only"] is True


def test_missing_tape_stays_visible_and_insufficient():
    state = assemble_symbol_state_v0(
        as_of_utc=AS_OF,
        side="long",
        sleeve="vss_fxcross_london_up_low",
        symbol="EURUSD",
        origin_organism="f5_challenge",
        books=None,
        spines=EMPTY_SPINE,
        geometry=FIXTURES["EURUSD"]["geo"],
        cost=FIXTURES["EURUSD"]["cost"],
        sleeve_features={"tag": "vss_fxcross_london_up_low"},
    )
    assert state["completeness"]["state_sufficient_for_live"] is False
    assert "timeframes.m15" in state["completeness"]["missing_fields"]
    assert "peers" in state["completeness"]["missing_fields"]
    assert all(row["present"] is False for row in state["peers"].values())
    assert all(row["source"] != "not_xau_primary" for row in state["peers"].values())


def test_peers_comove_when_aligned_and_never_not_xau_primary():
    eurusd = FIXTURES["EURUSD"]["books"]
    usdjpy = FIXTURES["USDJPY"]["books"]
    peers = assemble_symbol_peers(
        symbol="EURUSD",
        as_of_utc=AS_OF,
        books=eurusd,
        peer_books={"USDJPY": usdjpy},
    )
    assert peers["USDJPY"]["present"] is True
    assert peers["USDJPY"]["source"] == "challenge_csv"
    assert peers["USDJPY"]["comove_20"] is not None
    assert "not_xau_primary" not in {row["source"] for row in peers.values()}
    gbp = assemble_symbol_peers(symbol="GBPJPY", as_of_utc=AS_OF, books=FIXTURES["GBPJPY"]["books"])
    assert gbp["USDJPY"]["source"] == "unassembled"
    assert gbp["USDJPY"]["source"] != "not_xau_primary"


def test_intent_path_non_xau_is_symbol_state_not_gold_dead_end():
    class _I:
        symbol = "EURUSD"
        sleeve = "vss_fxcross_london_up_low"
        side = "long"
        entry = 1.1720
        stop = 1.1695
        stop_dist = 0.0025
        candidate_id = "fx-1"
        order_type = "MARKET"

    gold_path = intent_gold_state(
        _I(),
        origin="f5_challenge",
        books=FIXTURES["EURUSD"]["books"],
        as_of_utc=AS_OF,
    )
    symbol_path = intent_symbol_state(
        _I(),
        origin="f5_challenge",
        books=FIXTURES["EURUSD"]["books"],
        as_of_utc=AS_OF,
    )
    assert gold_path is not None
    assert symbol_path is not None
    assert gold_path["schema"] == SCHEMA
    assert symbol_path["schema"] == SCHEMA
    assert gold_path["identity"]["asset_class"] == "fx"
    assert "not_xau_primary" not in {row.get("source") for row in gold_path["peers"].values()}
    assert gold_path["completeness"]["state_sufficient_for_live"] is True


def test_intent_xau_stays_gold_state_schema():
    class _I:
        symbol = "XAUUSD"
        sleeve = "dsp_two_bar_t"
        side = "short"
        entry = 4331.45
        stop = 4336.9
        stop_dist = 5.45
        candidate_id = "292667008"
        order_type = "MARKET"

    state = intent_gold_state(_I(), origin="f5_challenge", as_of_utc=CHALLENGE_AS_OF)
    assert state is not None
    assert state["schema"] == "gtos.judgment.gold_state.v0"
    assert "in_ldn_ny_overlap" in state["sessions"]
    assert "london_expand_ok" in state["sessions"]
    assert "ny_rth_us30" in state["sessions"]
    assert state["cluster"]["eur_gbp"]["members"] == ["EURUSD", "GBPUSD", "EURGBP"]
    assert "gbpjpy" in state["cross"]
    assert "boj_bucket" in state["information"]
    assert state["sleeve"]["gbpjpy_a_plus_ready"]["admit"] is None
    assert state["sleeve"]["xau_dsp_shakeout_ready"]["never_admit_choice"] is True
    assert state["chair_wires"]["apply"] is False
    assert state["surface"]["us30_off"] is True
    wrapped = intent_symbol_state(_I(), origin="f5_challenge", as_of_utc=CHALLENGE_AS_OF)
    assert wrapped["schema"] == SCHEMA
    assert wrapped["completeness"]["state_sufficient_for_live"] is True
    assert wrapped["gold_state"]["schema"] == "gtos.judgment.gold_state.v0"
    assert wrapped["gold_state"]["sleeve"]["xau_dsp_shakeout_ready"]["admit"] is None


def test_compose_and_haircut_do_not_apply_size_on_non_xau(monkeypatch):
    state = _assemble("EURUSD")
    composed = compose_shadow(state, ticket="fx-observe")
    assert_live_cages(composed, ticket="fx-observe")
    assert composed["named_apply_symbol"] is False
    assert composed["apply_this_row"] is False
    assert composed["live_size_tilt"] == 1.0
    assert composed["live_cost_tilt"] == 1.0
    monkeypatch.setenv("GTOS_JEV_APPLY_LIVE", "1")
    unit = {"risk_pct_per_trade": 0.0015, "volume": 2.0, "symbol": "EURUSD"}
    cut = maybe_haircut_unit(
        unit,
        composed,
        login=0,
        ns="operator",
        symbol="EURUSD",
    )
    from src.judgment.apply_size import apply_named_tilts

    named = apply_named_tilts(composed)
    assert named["apply_this_row"] is False
    assert named["combined"] == 1.0
    assert cut["volume"] == 2.0
    assert cut["risk_pct_per_trade"] == 0.0015
    assert "jev_combined_live_tilt" not in cut


def test_challenge_shadow_non_xau_scores_symbol_state():
    row = score_position(
        {
            "ticket": 88001,
            "symbol": "USDJPY",
            "side": "SHORT",
            "sleeve": "vss_fxcross_london_up_low",
            "entry": 148.10,
            "orig_sl": 148.45,
            "stop_dist": 0.35,
            "spread_R": 0.06,
            "open_time_utc": "2026-09-17T11:05:00Z",
            "_kind": "open",
        },
        # Multi-symbol cache — never pass a single-tf XAU/USDJPY dict as peers.
        books={"USDJPY": FIXTURES["USDJPY"]["books"]},
        spines=EMPTY_SPINE,
        sit_meta={},
    )
    assert row["state"]["schema"] == SCHEMA
    assert row["state"]["identity"]["asset_class"] == "fx"
    assert_live_cages(row["compose"], ticket=88001)
    assert row["compose"]["apply_this_row"] is False
    assert row["compose"]["named_apply_symbol"] is False
    assert "not_xau_primary" not in (row.get("missing_state") or [])
    assert row["state"]["completeness"]["state_sufficient_for_live"] is True


def test_expost_rejected_on_live_symbol_state():
    import pytest

    with pytest.raises(ValueError, match="EXPOST"):
        assemble_symbol_state_v0(
            as_of_utc=AS_OF,
            side="long",
            sleeve="vss_fxcross_london_up_low",
            symbol="EURUSD",
            as_of_clock="live_intent",
            extra={"broker_net": -4.0},
        )


def test_a_plus_library_is_first_class_sleeve_on_same_gate_flow():
    from src.judgment.a_plus_sleeve import (
        GATE_FLOW_NAME,
        library_for,
        observe_a_plus_on_gate_flow,
    )
    from src.judgment.family import family_class_for

    for symbol in ("XAUUSD", "EURUSD", "USDJPY", "US30", "GBPJPY"):
        rows = library_for(symbol)
        assert rows, symbol
        assert all(r["tag"].startswith("aplus_") for r in rows)
        assert family_class_for(rows[0]["tag"]) == "a_plus_study"

    state = _assemble("EURUSD", sleeve="aplus_eurusd_london_session_reclaim")
    assert state["identity"]["family_class"] == "a_plus_study"
    assert state["sleeve"]["a_plus"] is True
    assert state["sleeve"]["library"] == "per_symbol_a_plus"
    assert state["sleeve"]["side_catalog"] is False
    assert state["sleeve"]["observe_only"] is True
    assert state["sleeve"]["ca_labels"]["enriches_any_sleeve"] is True
    assert state["sleeve"]["ca_labels"]["never_invent_dxy"] is True
    assert state["gate_flow"]["name"] == GATE_FLOW_NAME
    assert "observe_fluid_inventory" in state["gate_flow"]["pipe"]
    assert "observe_sel_v4_002" in state["gate_flow"]["pipe"]
    assert "compose_shadow" in state["gate_flow"]["pipe"]
    assert set(state["gate_flow"]["consumers"]) == {"fluid", "admit", "selector", "size_observe"}
    composed = compose_shadow(state, ticket="aplus-eur")
    assert composed["a_plus_sleeve"] is True
    assert composed["named_apply_symbol"] is False
    assert composed["apply_this_row"] is False
    assert composed["size_observe"] is True
    assert composed["gate_flow"] == GATE_FLOW_NAME
    observed = observe_a_plus_on_gate_flow(state)
    assert observed["never_place"] is True
    assert observed["never_silent_apply"] is True
    assert observed["apply_this_row"] is False
    assert observed["side_catalog"] is False


def test_a_plus_on_xau_cannot_silent_apply():
    state = _assemble("XAUUSD", sleeve="aplus_xau_london_htf_align")
    assert state["sleeve"]["a_plus"] is True
    assert state["surface"]["apply_named_wires"] is False
    assert state["surface"]["symbol_state_observe_only"] is True
    composed = compose_shadow(state, ticket="aplus-xau")
    assert composed["named_apply_symbol"] is False
    assert composed["apply_this_row"] is False
    assert composed["never_silent_apply"] is True


def test_ca_labels_enrich_any_sleeve():
    from src.judgment.a_plus_sleeve import attach_sleeve_object, enrich_ca_labels

    world = {"source": "cross_asset_v0", "labels": {"usd_proxy": 1, "risk_off": False}}
    labels = enrich_ca_labels(world)
    assert labels["labels"]["usd_proxy"] == 1
    assert labels["never_invent_dxy"] is True
    live = attach_sleeve_object(
        symbol="USDJPY",
        sleeve="vss_fxcross_london_up_low",
        world=world,
    )
    assert live["a_plus"] is False
    assert live["library"] == "challenge_live"
    assert live["ca_labels"]["labels"]["usd_proxy"] == 1
    assert live["gate_flow"] == "a_plus_sleeve_on_gate_flow"
    assert live["side_catalog"] is False
    assert live["ca_labels"]["never_invent_tips"] is True


def test_usd_proxy_vs_xau_from_fx_peers_no_dxy():
    xau = _books(4330.0, -1.0, half=2.0)
    eurusd_down = _books(1.1700, -0.00015, half=0.0004)
    usdjpy_up = FIXTURES["USDJPY"]["books"]
    state = assemble_symbol_state_v0(
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
        peer_books={"EURUSD": eurusd_down, "USDJPY": usdjpy_up},
    )
    row = state["peers"]["usd_proxy_vs_xau"]
    assert row["present"] is True
    assert row["apply"] is False
    assert row["never_invent_dxy"] is True
    assert row["usd_proxy"] == 1
    assert row["xau_usd"] == 1
    assert row["label"] == "agree"
    assert state["class_specific"]["metal"]["usd_proxy_vs_xau"] == "agree"
    assert state["sleeve"]["ca_labels"]["labels"]["usd_proxy_vs_xau"] == "agree"
    assert state["chair_wires"]["wires"]["usd_proxy_vs_xau"]["label"] == "agree"
    assert "DXY" not in state["peers"]
    assert state["world"].get("dxy") is None
    assert state["chair_wires"]["wires"]["corr.xau_vs_eur_proxy_usd"]["present"] is True
    assert state["chair_wires"]["wires"]["corr.eur_gbp_usd_co_move"]["source"] == "unassembled"


def test_gbpjpy_dual_leg_agree_from_gbpusd_usdjpy():
    gbpusd = _books(1.3400, 0.00012, half=0.0003)
    usdjpy = FIXTURES["USDJPY"]["books"]
    state = _assemble("GBPJPY", peer_books={"GBPUSD": gbpusd, "USDJPY": usdjpy})
    row = state["peers"]["gbpjpy_dual_leg_agree"]
    assert row["present"] is True
    assert row["apply"] is False
    assert row["composed"] == 1
    assert row["label"] == "agree"
    assert row["legs"]["GBPUSD"]["direction"] == 1
    assert row["legs"]["USDJPY"]["direction"] == 1
    assert state["chair_wires"]["wires"]["gbpjpy_dual_leg_agree"]["label"] == "agree"
    missing = _assemble("GBPJPY")
    assert missing["peers"]["gbpjpy_dual_leg_agree"]["present"] is False
    assert missing["peers"]["gbpjpy_dual_leg_agree"]["source"] == "unassembled"


def test_us30_rth_vs_eth_is_session_choice_house_off_stays():
    london = _assemble("US30")
    assert london["sessions"]["named"] == "london"
    assert london["sessions"]["us30_rth_vs_eth"] == "eth"
    assert london["class_specific"]["index"]["us30_rth_vs_eth"] == "eth"
    assert london["class_specific"]["index"]["house_us30_off"] is True
    assert london["surface"]["us30_off"] is True
    rth = _assemble("US30", as_of=datetime(2026, 9, 17, 14, 30, tzinfo=timezone.utc))
    assert rth["sessions"]["named"] == "ny"
    assert rth["sessions"]["us30_rth_vs_eth"] == "rth"
    assert rth["surface"]["us30_off"] is True
    assert rth["surface"]["apply_named_wires"] is False
    composed = compose_shadow(rth, ticket="us30-rth")
    assert composed["apply_this_row"] is False
    assert composed["named_apply_symbol"] is False


def test_usdjpy_tokyo_event_liquidity_uses_spine_not_invented_news():
    tokyo = datetime(2026, 9, 17, 3, 0, tzinfo=timezone.utc)
    quiet = _assemble("USDJPY", as_of=tokyo)
    assert quiet["sessions"]["named"] == "asia"
    assert quiet["class_specific"]["fx"]["usdjpy_tokyo_event_liquidity"] == "tokyo_clock_spine_empty"
    event_dt = datetime(2026, 9, 17, 2, 30, tzinfo=timezone.utc)
    spine = {
        "spine_id": "test-jpy",
        "sources": ["test"],
        "events": [
            {
                "datetime_utc": event_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "event": "BOJ",
                "impact": "HIGH",
                "currency": "JPY",
                "_dt": event_dt,
            }
        ],
        "n_files": 1,
    }
    hot = _assemble("USDJPY", as_of=tokyo, spines=spine)
    assert hot["news"]["pair_high_in_f5_window"] is True
    assert hot["class_specific"]["fx"]["usdjpy_tokyo_event_liquidity"] == "tokyo_pair_high"
    assert hot["chair_wires"]["wires"]["usdjpy_tokyo_event_liquidity"]["never_invent_news_protocol"] is True
    london = _assemble("USDJPY")
    assert london["class_specific"]["fx"]["usdjpy_tokyo_event_liquidity"] == "outside_tokyo"


def test_fx_session_london_fit_and_ldn_ny_overlap_vol():
    eurusd = _assemble("EURUSD")
    assert eurusd["sessions"]["named"] == "london"
    assert eurusd["sessions"]["fx_session_london_fit"] == "fit"
    assert eurusd["class_specific"]["fx"]["fx_session_london_fit"] == "fit"
    overlap = eurusd["sessions"]["ldn_ny_overlap_vol"]
    assert overlap["in_window"] is False
    assert overlap["present"] is False
    assert overlap["apply"] is False
    us30 = _assemble("US30")
    assert us30["sessions"]["fx_session_london_fit"] == "not_fx"
    inside = _assemble("EURUSD", as_of=datetime(2026, 9, 17, 13, 5, tzinfo=timezone.utc))
    assert inside["sessions"]["named"] == "ny"
    assert inside["sessions"]["fx_session_london_fit"] == "outside"
    ov = inside["sessions"]["ldn_ny_overlap_vol"]
    assert ov["in_window"] is True
    assert ov["present"] is True
    assert ov["n"] >= 1
    assert ov["apply"] is False


def test_corr_comove_eur_gbp_and_xau_eur_proxy():
    eurusd = FIXTURES["EURUSD"]["books"]
    gbpusd = _books(1.3400, 0.00012, half=0.0003)
    xau = _books(4330.0, 0.8, half=1.5)
    state = _assemble(
        "EURUSD",
        peer_books={"GBPUSD": gbpusd, "XAUUSD": xau, "USDJPY": FIXTURES["USDJPY"]["books"]},
    )
    corr = state["peers"]["corr"]
    assert corr["present"] is True
    assert corr["eur_gbp_usd_co_move"] is not None
    assert corr["xau_vs_eur_proxy_usd"] is not None
    assert corr["never_invent_dxy"] is True
    assert state["chair_wires"]["wires"]["corr.eur_gbp_usd_co_move"]["value"] == corr["eur_gbp_usd_co_move"]
    assert state["chair_wires"]["wires"]["corr.xau_vs_eur_proxy_usd"]["value"] == corr["xau_vs_eur_proxy_usd"]


def test_tokyo_fix_window_label_is_clock_only():
    from src.judgment.chair_wires import tokyo_fix_window_label

    fix_at = datetime(2026, 9, 17, 0, 55, tzinfo=timezone.utc)
    assert tokyo_fix_window_label(fix_at) == "tokyo_fix"
    assert tokyo_fix_window_label(AS_OF) == "outside"
    state = _assemble("USDJPY", as_of=fix_at)
    assert state["clock"]["tokyo_fix_window_label"] == "tokyo_fix"
    assert state["sessions"]["named"] == "dead_21_00z"
    assert state["chair_wires"]["wires"]["tokyo_fix_window_label"]["source"] == "clock_only"
    assert state["chair_wires"]["wires"]["tokyo_fix_window_label"]["never_invent_news_protocol"] is True
    assert state["sleeve"]["ca_labels"]["labels"]["tokyo_fix_window_label"] == "tokyo_fix"


def test_chair_wires_never_apply_and_never_flip_sufficient():
    empty = assemble_symbol_state_v0(
        as_of_utc=AS_OF,
        side="long",
        sleeve="vss_fxcross_london_up_low",
        symbol="EURUSD",
        origin_organism="f5_challenge",
        books=None,
        spines=EMPTY_SPINE,
        geometry=FIXTURES["EURUSD"]["geo"],
        cost=FIXTURES["EURUSD"]["cost"],
        sleeve_features={"tag": "vss_fxcross_london_up_low"},
    )
    assert empty["completeness"]["state_sufficient_for_live"] is False
    assert empty["completeness"]["chair_wires"] is True
    assert empty["chair_wires"]["apply"] is False
    composed = compose_shadow(empty, ticket="wires-empty")
    assert composed["apply_this_row"] is False
    assert composed["named_apply_symbol"] is False
    hot = _assemble("EURUSD")
    composed_hot = compose_shadow(hot, ticket="wires-hot")
    assert hot["chair_wires"]["apply"] is False
    assert composed_hot["apply_this_row"] is False
    assert composed_hot["live_size_tilt"] == 1.0


def _covering_spine(as_of, *, hours=48, currency="USD", event="CPI"):
    when = as_of + timedelta(hours=hours)
    return {
        "spine_id": "edge-cover",
        "sources": ["test"],
        "events": [
            {
                "datetime_utc": when.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "event": event,
                "impact": "HIGH",
                "currency": currency,
                "_dt": when,
            }
        ],
        "n_files": 1,
    }


def _boj_print_spine(as_of):
    when = as_of - timedelta(minutes=10)
    return {
        "spine_id": "edge-boj",
        "sources": ["test"],
        "events": [
            {
                "datetime_utc": when.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "event": "BOJ policy rate",
                "impact": "HIGH",
                "currency": "JPY",
                "_dt": when,
            }
        ],
        "n_files": 1,
    }


def test_usd_proxy_usdjpy_primary_eur_alias_if_null():
    xau = _books(4330.0, -1.0, half=2.0)
    eurusd_up = _books(1.1700, 0.00015, half=0.0004)
    usdjpy_up = FIXTURES["USDJPY"]["books"]
    primary = assemble_symbol_state_v0(
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
        peer_books={"EURUSD": eurusd_up, "USDJPY": usdjpy_up},
    )
    row = primary["peers"]["usd_proxy_vs_xau"]
    assert row["primary_peer"] == "USDJPY"
    assert row["alias"] is False
    assert row["source"] == "peers.usdjpy"
    assert row["usd_proxy"] == 1
    assert row["label"] == "agree"
    alias = assemble_symbol_state_v0(
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
    assert arow["present"] is True


def test_pack4_canonical_paths_no_admit_us30_off_stays():
    eurusd = _assemble(
        "EURUSD",
        peer_books={"GBPUSD": _books(1.3400, 0.00012, half=0.0003)},
    )
    assert eurusd["sessions"]["in_ldn_ny_overlap"] is False
    assert "london_expand_ok" in eurusd["sessions"]
    assert eurusd["sessions"]["ny_rth_us30"] is False
    assert eurusd["cluster"]["eur_gbp"]["members"] == ["EURUSD", "GBPUSD", "EURGBP"]
    assert eurusd["information"]["boj_bucket"]["label"] == "pre_effective"
    assert eurusd["information"]["boj_bucket"]["rate_fact"]["rate_pct"] == 1.25
    assert eurusd["sleeve"]["gbpjpy_a_plus_ready"]["admit"] is None
    assert eurusd["sleeve"]["xau_dsp_shakeout_ready"]["never_admit_choice"] is True
    us30 = _assemble("US30", as_of=datetime(2026, 9, 17, 14, 30, tzinfo=timezone.utc))
    assert us30["sessions"]["ny_rth_us30"] is True
    assert us30["sessions"]["in_ldn_ny_overlap"] is True
    assert us30["surface"]["us30_off"] is True
    assert us30["class_specific"]["index"]["house_us30_off"] is True


def test_edge_t1_t4_gbpjpy_a_plus_ready():
    peers = {"GBPUSD": _books(1.3400, 0.00012, half=0.0003), "USDJPY": FIXTURES["USDJPY"]["books"]}
    t1 = _assemble("GBPJPY", peer_books=peers)
    ready = t1["sleeve"]["gbpjpy_a_plus_ready"]
    assert ready["choice"] == "a_plus"
    assert ready["admit"] is None
    assert ready["conjuncts"]["session_ok"] is True
    assert ready["conjuncts"]["identity_ok"] is True
    assert ready["conjuncts"]["agree"] is True
    assert ready["conjuncts"]["dual_same"] is True
    assert ready["conjuncts"]["boj_clear"] is True
    assert abs(ready["resid"]) <= 0.15
    t2 = _assemble("GBPJPY", peer_books=peers, as_of=datetime(2026, 9, 17, 18, 0, tzinfo=timezone.utc))
    assert t2["sessions"]["named"] == "ny"
    assert t2["sessions"]["in_ldn_ny_overlap"] is False
    assert t2["sleeve"]["gbpjpy_a_plus_ready"]["choice"] == "almost"
    t3 = _assemble("GBPJPY", peer_books=peers, spines=_boj_print_spine(AS_OF))
    assert t3["information"]["boj_bucket"]["label"] == "print"
    assert t3["sleeve"]["gbpjpy_a_plus_ready"]["choice"] == "blocked"
    t4 = _assemble("GBPJPY")
    assert t4["sleeve"]["gbpjpy_a_plus_ready"]["choice"] == "null_state"
    assert t4["cross"]["gbpjpy"]["present"] is False


def test_edge_t1_t4_xau_dsp_shakeout_ready():
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
    t1 = assemble_symbol_state_v0(as_of_utc=AS_OF, spines=_covering_spine(AS_OF), **kwargs)
    ready = t1["sleeve"]["xau_dsp_shakeout_ready"]
    assert t1["completeness"]["state_sufficient_for_live"] is True
    assert ready["choice"] == "a_plus"
    assert ready["admit"] is None
    assert ready["conjuncts"]["event_gap_ok"] is True
    assert ready["usd_proxy_source"] == "peers.usdjpy"
    t2 = assemble_symbol_state_v0(
        as_of_utc=AS_OF,
        spines=_covering_spine(AS_OF),
        **{**kwargs, "peer_books": {"USDJPY": _books(148.20, -0.02, half=0.04), "EURUSD": peers["EURUSD"]}},
    )
    assert t2["sleeve"]["xau_dsp_shakeout_ready"]["choice"] == "almost"
    t3 = assemble_symbol_state_v0(as_of_utc=AS_OF, spines=EMPTY_SPINE, **kwargs)
    assert t3["sleeve"]["xau_dsp_shakeout_ready"]["event_gap"] == "fail_closed_empty_spine"
    assert t3["sleeve"]["xau_dsp_shakeout_ready"]["choice"] == "blocked"
    t4 = assemble_symbol_state_v0(
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


def test_n_non_xau_sufficient_45_use_symbol_state():
    receipt = remasure_non_xau_sufficient()
    assert receipt["n_non_xau_sufficient"] == NON_XAU_REMEASURE_N == 45
    assert receipt["n_gold_default_leaks"] == 0
    assert receipt["named_apply_symbol"] == 0
    assert receipt["apply_this_row"] == 0
    assert receipt["live_size_tilt_locked"] is True
    assert receipt["never_place"] is True
    assert receipt["us30_hard_off"] == 9
    for row in receipt["rows"]:
        assert row["schema"] == SCHEMA
        assert row["gold_state_nested"] is False
        assert row["named_apply_symbol"] is False
        if row["symbol"] == "US30":
            assert row["family_class"] == "house_hard_off"
