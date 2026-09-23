"""Research-only harvest stubs. No send path. No invented HIGH."""

from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.components.ultimate_book.primitives import Bar
from src.judgment.bars import StampedBar
from src.judgment.gold_state import assemble_gold_state_v0
from src.judgment.harvest_patterns import (
    CHAIR_NEXT_ACTIONS,
    CHAIR_ROUTE_CLASS_TABLE,
    CHAIR_ROUTE_CLASS_UNKNOWN_UNTIL_LANDED,
    CHALLENGE_LOGIN,
    CHALLENGE_MAGIC,
    CHALLENGE_NS,
    CHALLENGE_PASS_LINE,
    NEVER_INVENT_NEWS,
    NEVER_PLACE,
    NEVER_VENDOR,
    PROPOSED_QUESTIONS,
    QUARANTINE_LOGIN,
    REQUIRED_SURVEY_FIELDS,
    ROUTE_CLASS_CHOICES,
    SCHEMA_EXTRAS,
    SCHEMA_LOCK,
    allowed_route_classes,
    attach_harvest_blocks,
    catalog_reject_chat_llm,
    catalog_repos,
    chair_route_class_for,
    choice_route_class,
    feature_as_of_from_books,
    infer_tf_route,
    load_survey,
    noul_feature_as_of_honest,
    route_from_state,
    route_symbol,
    score_fill_realism,
)
from src.judgment.process_lock import ENVELOPE_WALL_IDS, FORBIDDEN_AUTO_EFFECTS

REPO = Path(__file__).resolve().parents[2]
HARVEST_SRC = REPO / "src" / "judgment" / "harvest_patterns.py"


def _base_state(**kwargs):
    kw = dict(
        as_of_utc=datetime(2026, 4, 15, 12, tzinfo=timezone.utc),
        side="short",
        sleeve="dsp_two_bar_t",
        origin_organism="f5_challenge",
        as_of_clock="as_of_open_study",
        books=None,
        spines={"spine_id": "x", "sources": [], "events": [], "n_files": 0},
    )
    kw.update(kwargs)
    return assemble_gold_state_v0(**kw)


def test_attach_completeness_null_visible_and_challenge_envelope():
    state = _base_state(
        geometry={"entry": 2300.0, "stop": 2305.0, "stop_dist": 5.0},
        cost={"spread_r_of_stop": 0.12, "source": "tick"},
        occupancy={"same_sleeve_orig_stops_utc_day": 1, "symbol_open": 0},
        sleeve_features={"ac60": 0.11, "vol_ratio": 1.2},
    )
    assert "harvest" not in state
    attached = attach_harvest_blocks(
        state,
        feature_as_of={"ac60": "2026-04-15T12:00:00Z", "vol_ratio": "2026-04-15T12:00:00Z"},
    )
    assert attached["harvest"]["schema"] == SCHEMA_EXTRAS
    assert attached["completeness"]["harvest"] is True
    assert attached["completeness"]["pit"] is True
    assert attached["completeness"]["envelope"] is True
    env = attached["harvest"]["envelope"]
    assert env["login"] == CHALLENGE_LOGIN
    assert env["ns"] == CHALLENGE_NS
    assert env["magic"] == CHALLENGE_MAGIC
    assert env["pass_line"] == CHALLENGE_PASS_LINE
    assert env["maxdd_rule"] == "static_floor"
    assert env["reset_clock"] == "cest_midnight"
    assert env["quarantine_login"] == QUARANTINE_LOGIN
    assert env["assembled"] is True
    assert attached["harvest"]["fill"]["model"] == "tick"
    assert attached["harvest"]["fill"]["cost_complete"] is True
    assert attached["harvest"]["route"]["tf_route"] == "unknown"
    assert attached["harvest"]["live_multiplier"] == 1.0
    assert attached["harvest"]["chair_named"] is False
    kinds = {p["kind"] for p in attached["harvest"]["protection"]}
    assert {"two_stop", "occupancy", "cluster", "maxdd"} <= kinds
    two = next(p for p in attached["harvest"]["protection"] if p["kind"] == "two_stop")
    assert two["remaining"] == 1
    assert two["fired"] is False
    assert attached["news"]["events"] == []
    assert attached["news"]["spine_empty"] is True
    assert NEVER_VENDOR and NEVER_PLACE and NEVER_INVENT_NEWS
    assert attached["harvest"]["law"]["schema_lock"] == SCHEMA_LOCK == "gold_state.v0_harvest_extras"


def test_expost_rejected_on_live_intent_via_extra_and_learn():
    state = _base_state(as_of_clock="live_intent")
    with pytest.raises(ValueError, match="EXPOST"):
        attach_harvest_blocks(state, extra={"R": -1.0})
    with pytest.raises(ValueError, match="live_intent"):
        attach_harvest_blocks(state, learn={"label": "stop", "R": -1.0})


def test_learn_attaches_only_on_close_clock():
    live = _base_state(as_of_clock="as_of_open_study")
    with pytest.raises(ValueError, match="OnlineLabelAtom"):
        attach_harvest_blocks(live, learn={"label": "time_stop"})
    closed = _base_state(as_of_clock="as_of_close_illegal_for_live")
    attached = attach_harvest_blocks(closed, learn={"label": "time_stop", "R": 1.5})
    assert attached["harvest"]["learn"]["attached"] is True
    assert attached["harvest"]["learn"]["label"] == "time_stop"
    assert attached["harvest"]["learn"]["R"] == 1.5


def test_no_invented_high_or_news_protocol():
    state = _base_state()
    assert state["news"]["spine_empty"] is True
    assert state["news"]["events"] == []
    with pytest.raises(ValueError, match="NEWS_PROTOCOL"):
        attach_harvest_blocks(state, extra={"NEWS_PROTOCOL": {"fomc": True}})
    with pytest.raises(ValueError, match="invent"):
        attach_harvest_blocks(
            state,
            extra={"news": {"events": [{"impact": "HIGH", "event": "FOMC"}]}},
        )
    with pytest.raises(ValueError, match="empty spine"):
        attach_harvest_blocks(state, extra={"high_in_f5_window": True})
    attached = attach_harvest_blocks(state)
    assert attached["news"]["events"] == []
    assert attached["news"]["spine_empty"] is True
    assert attached["news"].get("high_in_f5_window") in {None, False}


def test_pit_leak_marks_dishonest_without_raising_on_study_clock():
    state = _base_state(sleeve_features={"ac60": 0.2})
    attached = attach_harvest_blocks(
        state,
        feature_as_of={"ac60": "2026-04-15T13:00:00Z"},
    )
    assert attached["completeness"]["pit"] is False
    assert attached["harvest"]["pit"]["honest"] is False
    assert "ac60" in attached["harvest"]["pit"]["leakage_keys"]


def test_missing_feature_as_of_is_visible_not_honest():
    state = _base_state(sleeve_features={"ac60": 0.2})
    attached = attach_harvest_blocks(state)
    assert attached["completeness"]["pit"] is False
    assert attached["harvest"]["pit"]["honest"] is False
    assert attached["harvest"]["pit"]["assembled"] is True


def test_non_challenge_envelope_stays_unassembled():
    state = _base_state(origin_organism="historical_lab")
    attached = attach_harvest_blocks(state)
    assert attached["completeness"]["envelope"] is False
    assert attached["harvest"]["envelope"]["assembled"] is False
    assert attached["harvest"]["envelope"]["login"] is None
    assert attached["harvest"]["envelope"]["quarantine_login"] == QUARANTINE_LOGIN


def test_route_identity_multi_when_m15_and_h4_present():
    state = _base_state()
    state["timeframes"] = {"m15": {"close": 1}, "h4": {"close": 2}}
    assert infer_tf_route(state) == "multi_m15_h4"
    route = route_from_state(state)
    assert route.route_id == "dsp_two_bar_t|XAUUSD|multi_m15_h4"
    attached = attach_harvest_blocks(state)
    assert attached["identity"]["tf_route"] == "multi_m15_h4"
    assert attached["identity"]["route_id"] == route.route_id
    assert attached["harvest"]["route_class"]["choice"] == "metal"


def test_attach_eurusd_route_class_is_fx_major():
    state = _base_state(symbol="EURUSD")
    state["timeframes"] = {"m15": {"close": 1}, "h4": {"close": 2}}
    attached = attach_harvest_blocks(state)
    assert attached["identity"]["symbol"] == "EURUSD"
    assert attached["identity"]["tf_route"] == "multi_m15_h4"
    rc = attached["harvest"]["route_class"]
    assert rc["choice"] == "fx_major"
    assert rc["house_hard_off"] is False
    assert attached["harvest"]["live_multiplier"] == 1.0
    assert attached["harvest"]["chair_named"] is False


def test_attach_us30_index_house_hard_off():
    state = _base_state(symbol="US30.cash")
    state["timeframes"] = {"m15": {"close": 1}, "h4": {"close": 2}}
    attached = attach_harvest_blocks(state)
    rc = attached["harvest"]["route_class"]
    assert rc["choice"] == "index"
    assert rc["house_hard_off"] is True
    assert rc["reason"] == "chair_named_index_house_hard_off"
    assert attached["harvest"]["live_multiplier"] == 1.0
    assert attached["harvest"]["chair_named"] is False


def test_import_graph_isolation():
    tree = ast.parse(HARVEST_SRC.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            imported.add(root)
            if node.module:
                imported.add(node.module)
    forbidden = {
        "mt5",
        "MetaTrader5",
        "src.mt5",
        "src.components.execution",
        "execution",
        "src.judgment.challenge_shadow",
        "src.judgment.apply_size",
        "src.judgment.compose",
    }
    assert imported.isdisjoint(forbidden)
    text = HARVEST_SRC.read_text(encoding="utf-8")
    for needle in ("order_send", "open_trade", "mt5.order", "RealMT5"):
        assert needle not in text
    assert "never places" in text.lower() or "Never places" in text


def test_catalog_required_fields_and_reject_class():
    survey = load_survey()
    assert survey["never_vendor"] is True
    assert survey["never_place"] is True
    assert survey["never_invent_news_protocol"] is True
    repos = catalog_repos()
    assert len(repos) >= 25
    for row in repos:
        for key in REQUIRED_SURVEY_FIELDS:
            assert key in row
        assert isinstance(row["stars"], int) and row["stars"] >= 0
    names = {r["full_name"] for r in repos}
    assert "microsoft/qlib" in names
    assert "nautechsystems/nautilus_trader" in names
    assert "jesse-ai/jesse" in names
    assert "feast-dev/feast" in names
    assert "TauricResearch/TradingAgents" in names
    rejected = catalog_reject_chat_llm()
    assert "TauricResearch/TradingAgents" in rejected
    assert "HKUDS/Vibe-Trading" in rejected
    assert "isaiahbjork/Auto-GPT-MetaTrader-Plugin" in rejected
    assert "Ichinga-Samuel/aiomql" in rejected
    qlib = next(r for r in repos if r["full_name"] == "microsoft/qlib")
    assert qlib["license"] == "MIT"
    freq = next(r for r in repos if r["full_name"] == "freqtrade/freqtrade")
    assert freq["license"] == "GPL-3.0"
    assert freq["class"] == "absorb_pattern_license_block"
    vectorbt = next(r for r in repos if r["full_name"] == "polakowo/vectorbt")
    assert "Commons-Clause" in vectorbt["license"]


def test_proposed_questions_and_chair_actions_do_not_lift_walls():
    assert set(PROPOSED_QUESTIONS) >= {
        "feature_as_of_honest",
        "route_class",
        "protection_still_earns",
        "would_be_nth_stop",
        "cost_complete",
        "fill_realism",
    }
    assert PROPOSED_QUESTIONS["route_class"]["gist"].startswith("metal")
    assert PROPOSED_QUESTIONS["would_be_nth_stop"]["primitive"] == "noul"
    assert "flatten" not in str(PROPOSED_QUESTIONS).lower()
    assert "do_not_vendor" in CHAIR_NEXT_ACTIONS
    assert "schema_locked_v0_extras" in CHAIR_NEXT_ACTIONS
    assert "p0_1_proved_shadow_0" in CHAIR_NEXT_ACTIONS
    assert "p0_2_chair_named_route_class_table_shadow_only" in CHAIR_NEXT_ACTIONS
    assert "p0_3_p0_4_idle_until_asked" in CHAIR_NEXT_ACTIONS
    assert "do_not_invent_route_class_outside_chair_table" in CHAIR_NEXT_ACTIONS
    assert "p0_5_proved_shadow_fill_realism" in CHAIR_NEXT_ACTIONS
    assert "envelope_walls_stay_integers" in CHAIR_NEXT_ACTIONS
    assert "ENV-H8" in ENVELOPE_WALL_IDS
    assert "place" in FORBIDDEN_AUTO_EFFECTS
    assert "flatten" in FORBIDDEN_AUTO_EFFECTS
    assert "envelope" in FORBIDDEN_AUTO_EFFECTS


def test_attach_does_not_mutate_input():
    state = _base_state()
    before = dict(state)
    attach_harvest_blocks(state)
    assert "harvest" not in state
    assert state["identity"] == before["identity"]


def test_noul_feature_as_of_honest_cases():
    empty = noul_feature_as_of_honest({"assembled": False})
    assert empty["decidable"] is False
    assert empty["abstain"] is True
    assert empty["moved"] is False
    honest = noul_feature_as_of_honest({"assembled": True, "honest": True})
    assert honest["decidable"] is True
    assert honest["noul"] is True
    assert honest["moved"] is False
    leak = noul_feature_as_of_honest(
        {"assembled": True, "honest": False, "leakage_keys": ["ac60"]}
    )
    assert leak["decidable"] is True
    assert leak["noul"] is False
    assert leak["moved"] is True
    assert leak["leakage_keys"] == ["ac60"]


def test_feature_as_of_from_books_stamps_last_closed_only():
    start = datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc)
    m15 = []
    for i in range(5):
        utc = start + timedelta(minutes=15 * i)
        m15.append(
            StampedBar(
                broker_naive=utc.replace(tzinfo=None) + timedelta(hours=3),
                utc=utc,
                bar=Bar(o=1.0, h=1.1, l=0.9, c=1.0, v=1.0),
                source_path="tmp",
            )
        )
    as_of = datetime(2026, 9, 9, 8, 40, tzinfo=timezone.utc)
    stamps = feature_as_of_from_books(
        {"m15": m15}, as_of, {"ac60": 0.11, "vol_ratio": 1.2, "session_hour": None}
    )
    assert stamps["ac60"] == "2026-09-09T08:30:00Z"
    assert stamps["vol_ratio"] == "2026-09-09T08:30:00Z"
    assert "session_hour" not in stamps
    assert feature_as_of_from_books({"m15": []}, as_of, {"ac60": 0.1}) == {}


def test_choice_route_class_chair_table():
    assert CHAIR_ROUTE_CLASS_TABLE["XAUUSD"] == "metal"
    assert CHAIR_ROUTE_CLASS_TABLE["EURUSD"] == "fx_major"
    assert CHAIR_ROUTE_CLASS_TABLE["GBPUSD"] == "fx_major"
    assert CHAIR_ROUTE_CLASS_TABLE["USDJPY"] == "fx_major"
    assert CHAIR_ROUTE_CLASS_TABLE["EURGBP"] == "fx_major"
    assert CHAIR_ROUTE_CLASS_TABLE["GBPJPY"] == "fx_cross"
    assert CHAIR_ROUTE_CLASS_TABLE["US30"] == "index"
    assert CHAIR_ROUTE_CLASS_UNKNOWN_UNTIL_LANDED == frozenset({"UK100", "BTCUSD", "ETHUSD"})
    assert ROUTE_CLASS_CHOICES == frozenset({"metal", "fx_major", "fx_cross", "index", "unknown"})
    assert set(CHAIR_ROUTE_CLASS_TABLE.values()) <= ROUTE_CLASS_CHOICES
    assert "crypto" not in ROUTE_CLASS_CHOICES
    assert "multi" not in ROUTE_CLASS_CHOICES

    assert chair_route_class_for("XAUUSD") == "metal"
    assert chair_route_class_for("EURUSD") == "fx_major"
    assert chair_route_class_for("GBPJPY") == "fx_cross"
    assert chair_route_class_for("US30.cash") == "index"
    assert chair_route_class_for("US30_cash") == "index"
    assert chair_route_class_for("UK100.cash") == "unknown"
    assert chair_route_class_for("BTCUSD") == "unknown"
    assert chair_route_class_for("ETHUSD") == "unknown"
    assert chair_route_class_for("AUDUSD") == "unknown"
    assert chair_route_class_for("") == "unknown"

    eurusd = choice_route_class("EURUSD", "multi_m15_h4")
    assert eurusd["choice"] == "fx_major"
    assert eurusd["moved"] is True
    assert eurusd["reason"] == "chair_named_fx_major"
    assert eurusd["house_hard_off"] is False
    assert eurusd["chair_named_table"] is True

    gbpjpy = choice_route_class("GBPJPY", "multi_m15_h4")
    assert gbpjpy["choice"] == "fx_cross"

    us30 = choice_route_class("US30.cash", "multi_m15_h4")
    assert us30["choice"] == "index"
    assert us30["house_hard_off"] is True
    assert us30["reason"] == "chair_named_index_house_hard_off"

    xau = choice_route_class("XAUUSD", "multi_m15_h4")
    assert xau["choice"] == "metal"
    assert xau["left_unknown"] is True
    assert xau["house_hard_off"] is False
    assert allowed_route_classes("XAUUSD") == frozenset({"metal", "multi"})

    uk = choice_route_class("UK100.cash", "unknown")
    assert uk["choice"] == "unknown"
    assert uk["reason"] == "unknown_until_landed"
    btc = choice_route_class("BTCUSD", "unknown")
    assert btc["choice"] == "unknown"
    eth = choice_route_class("ETH", "unknown")
    assert eth["choice"] == "unknown"
    assert route_symbol("ETH") == "ETHUSD"
    stray = choice_route_class("AUDUSD", "multi_m15_h4")
    assert stray["choice"] == "unknown"
    assert stray["reason"] == "not_in_chair_table"
    assert allowed_route_classes("AUDUSD") == frozenset({"unknown"})
    assert allowed_route_classes("UK100") == frozenset({"unknown"})
    assert "crypto" not in allowed_route_classes("BTCUSD")
    assert "index" not in allowed_route_classes("UK100")


def test_fill_realism_tick_moved_unknown_abstains():
    unknown = score_fill_realism({"model": "unknown", "cost_complete": False})
    assert unknown["abstain"] is True
    assert unknown["decidable"] is False
    tick = score_fill_realism({"model": "tick", "cost_complete": True})
    assert tick["score"] == 2.0
    assert tick["moved"] is True
    assert tick["decidable"] is True
    bar = score_fill_realism({"model": "bar_close", "cost_complete": True})
    assert bar["score"] == 0.0
    assert bar["moved"] is True
