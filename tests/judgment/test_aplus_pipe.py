"""A+ catalog stays off the W7 pipe. Gold A+ still assembles. No APPLY."""

from datetime import datetime, timezone

from src.components.ultimate_book.sleeves.registry import BUILT, CANDIDATE_BUILT
from src.judgment.a1_log import intent_gold_state
from src.judgment.aplus_pipe import (
    A_PLUS_FRAMEWORKS,
    ARMED_W7_SLEEVES,
    MODEL_A_ENABLED,
    OBSERVE_GATE,
    aplus_catalog,
    aplus_host_land,
    aplus_sleeve_tag,
    assemble_aplus_observe_state,
    maybe_observe_aplus_at_place,
    observe_aplus_candidate,
)
from src.judgment.gold_state import SCHEMA as SCHEMA_GOLD
from src.judgment.gold_state import assemble_gold_state_v0
from src.judgment.symbol_state import SCHEMA as SCHEMA_SYMBOL
from src.judgment.symbol_state import gold_keys_equal


AS_OF = datetime(2026, 4, 15, 12, tzinfo=timezone.utc)


def _gold_aplus_packet(**kwargs):
    packet = {
        "symbol": "XAUUSD",
        "side": "short",
        "framework": "ob_retest",
        "setup_grade": "A+",
        "kill_zone": "london",
        "entry": 2300.0,
        "stop": 2305.0,
        "stop_dist": 5.0,
        "target": 2290.0,
        "candidate_id": "aplus-xau-ob",
        "h1_setup": {
            "poi_identified": True,
            "poi_type": "OB",
            "poi_price_level": 2302.5,
            "zone": "premium",
            "causing_event_type": "BOS",
        },
    }
    packet.update(kwargs)
    return packet


def _gbp_aplus_packet(**kwargs):
    packet = {
        "symbol": "GBPUSD",
        "side": "long",
        "framework": "fvg_fill",
        "setup_grade": "A+",
        "kill_zone": "london",
        "entry": 1.34,
        "stop": 1.338,
        "stop_dist": 0.002,
        "target": 1.344,
        "h1_setup": {
            "poi_identified": True,
            "poi_type": "FVG",
            "poi_price_level": 1.3395,
            "zone": "discount",
            "causing_event_type": "CHoCH",
        },
    }
    packet.update(kwargs)
    return packet


def test_catalog_names_every_framework_off_the_w7_pipe():
    catalog = aplus_catalog()
    assert catalog["never_place"] is True
    assert catalog["never_apply"] is True
    assert catalog["do_not_edit_selector_v4"] is True
    assert catalog["do_not_expand_armed_tags"] is True
    assert catalog["observe_default_off"] is True
    assert catalog["observe_body_fields"] == [
        "setup_grade",
        "framework",
        "kill_zone",
        "poi",
    ]
    assert catalog["observe_wired_to_bridge"] is False
    assert catalog["observe_wired_to_book_owner"] is False
    assert catalog["observe_wired_to_selector_v4"] is False
    assert catalog["host_land"]["wired_on_this_tree"] is False
    assert catalog["host_land"]["do_not_wholesale_copy_book_owner"] is True
    assert catalog["host_land"]["do_not_expand_armed_tags"] is True
    assert catalog["host_land"]["envelope_stays_integer"] is True
    assert catalog["trade_intent_has_setup_grade"] is False
    assert catalog["trade_intent_has_framework"] is False
    assert catalog["trade_intent_missing_aplus_fields"] == [
        "setup_grade",
        "framework",
        "kill_zone",
    ]
    names = {row["framework"] for row in catalog["frameworks"]}
    assert names == set(A_PLUS_FRAMEWORKS)
    for row in catalog["frameworks"]:
        assert row["pipe_status"] == "catalog_only_not_on_w7_gate"
        assert row["on_w7_built"] is False
        assert row["on_w7_candidate_built"] is False
        assert row["on_armed_tags"] is False
        assert row["generate_ready"] is False
        assert row["apply_ready"] is False
        assert "catalog_only" in row["walls"]
        assert "gold_only" in row["walls"]
    assert set(MODEL_A_ENABLED) <= names
    assert catalog["armed_w7_sleeves"] == list(ARMED_W7_SLEEVES)


def test_aplus_frameworks_are_absent_from_w7_registries():
    for name in A_PLUS_FRAMEWORKS:
        assert name not in BUILT
        assert name not in CANDIDATE_BUILT
        assert aplus_sleeve_tag(name) not in BUILT
        assert aplus_sleeve_tag(name) not in CANDIDATE_BUILT
    for tag in ARMED_W7_SLEEVES:
        assert tag in BUILT


def test_gold_aplus_observe_preserves_gold_body_and_grade():
    packet = _gold_aplus_packet()
    state = assemble_aplus_observe_state(packet, books={}, as_of_utc=AS_OF)
    gold = assemble_gold_state_v0(
        as_of_utc=AS_OF,
        side="short",
        sleeve="aplus_ob_retest",
        symbol="XAUUSD",
        candidate_id="aplus-xau-ob",
        origin_organism="aplus_catalog_observe",
        as_of_clock="aplus_observe",
        books={},
        geometry={
            "entry": 2300.0,
            "stop": 2305.0,
            "target": 2290.0,
            "stop_dist": 5.0,
            "order_type": "MARKET",
        },
        cost={
            "spread_r_of_stop": None,
            "source": "unassembled",
            "cost_screen_would_refuse": False,
        },
        sleeve_features={
            "tag": "aplus_ob_retest",
            "a8_source": "not_aplus_features",
            "metals_a8_applied": False,
        },
    )
    assert state is not None
    drifted = gold_keys_equal(gold, state)
    assert drifted == [], drifted
    assert state["schema"] == SCHEMA_GOLD
    assert state["identity"]["symbol"] == "XAUUSD"
    assert state["surface"]["us30_off"] is True
    assert state["aplus"]["setup_grade"] == "A+"
    assert state["aplus"]["framework"] == "ob_retest"
    assert state["aplus"]["kill_zone"] == "london"
    assert state["aplus"]["poi"]["poi_type"] == "OB"
    assert state["aplus"]["poi"]["price"] == 2302.5
    assert state["aplus"]["poi"]["zone"] == "premium"
    assert state["aplus"]["poi"]["invented"] is False
    assert state["aplus"]["poi"]["gold_levels_poi_untouched"] is True
    assert state["levels"]["poi"] is None
    assert state["aplus"]["gate1_would_admit"] is True
    assert state["aplus"]["metals_a8_applied"] is False
    assert state["aplus"]["on_w7_built"] is False
    assert state["sleeve_features"]["a8_source"] == "not_aplus_features"


def test_gbpusd_aplus_stays_gbpusd_with_observe_body():
    state = assemble_aplus_observe_state(
        _gbp_aplus_packet(),
        books={"m15": [], "h4": [], "d1": []},
        as_of_utc=AS_OF,
    )
    assert state is not None
    assert state["identity"]["symbol"] == "GBPUSD"
    assert state["schema"] == SCHEMA_SYMBOL
    assert state["generality"]["identity_defaulted_to_xau"] is False
    assert state["generality"]["symbol_class"] == "fx"
    assert state["generality"]["xau_peer_d1"]["xau_d1_injected"] is False
    assert state["aplus"]["framework"] == "fvg_fill"
    assert state["aplus"]["setup_grade"] == "A+"
    assert state["aplus"]["kill_zone"] == "london"
    assert state["aplus"]["poi"]["poi_type"] == "FVG"
    assert state["aplus"]["poi"]["price"] == 1.3395
    assert state["aplus"]["poi"]["zone"] == "discount"
    assert state["aplus"]["poi"]["source"] == "packet"
    assert state["levels"]["poi"] is None
    assert state["aplus"]["pipe_status"] == "catalog_only_not_on_w7_gate"

    row = observe_aplus_candidate(_gbp_aplus_packet(), books={}, as_of_utc=AS_OF)
    assert row["skipped"] == "GTOS_JEV_A1_LOG_off"
    assert row["aplus"]["identity_symbol"] == "GBPUSD"
    assert row["aplus"]["setup_grade"] == "A+"
    assert row["aplus"]["framework"] == "fvg_fill"
    assert row["aplus"]["kill_zone"] == "london"
    assert row["aplus"]["poi"]["poi_type"] == "FVG"
    assert row["extra"]["setup_grade"] == "A+"
    assert row["extra"]["framework"] == "fvg_fill"
    assert row["extra"]["kill_zone"] == "london"
    assert row["extra"]["poi"]["price"] == 1.3395


def test_missing_symbol_aplus_stays_empty():
    state = assemble_aplus_observe_state(
        {
            "framework": "breaker_re_entry",
            "setup_grade": "A",
            "side": "short",
            "entry": 1.08,
            "stop": 1.082,
            "stop_dist": 0.002,
        },
        books={},
        as_of_utc=AS_OF,
    )
    assert state is not None
    assert state["identity"]["symbol"] == ""
    assert state["schema"] == SCHEMA_SYMBOL
    assert state["completeness"]["state_sufficient_for_live"] is False
    assert state["aplus"]["gate1_would_admit"] is True


def test_below_grade_is_named_not_admitted():
    state = assemble_aplus_observe_state(
        _gold_aplus_packet(setup_grade="B+"),
        books={},
        as_of_utc=AS_OF,
    )
    assert state is not None
    assert state["aplus"]["setup_grade"] == "B+"
    assert state["aplus"]["gate1_would_admit"] is False


def test_observe_aplus_is_default_off_and_never_places():
    row = observe_aplus_candidate(_gold_aplus_packet(), books={}, as_of_utc=AS_OF)
    assert row["gate_id"] == OBSERVE_GATE
    assert row["never_place"] is True
    assert row["never_remint"] is True
    assert row["never_flatten"] is True
    assert row["skipped"] == "GTOS_JEV_A1_LOG_off"
    assert row["fluid_inventory"]["n_fluid"] == 48
    assert row["fluid_inventory"]["skipped"] == "GTOS_JEV_A1_LOG_off"
    assert row["fluid_inventory"]["never_place"] is True
    assert row["aplus"]["pipe_status"] == "catalog_only_not_on_w7_gate"
    assert row["aplus"]["identity_symbol"] == "XAUUSD"
    assert row["aplus"]["state_schema"] == SCHEMA_GOLD
    assert row["aplus"]["setup_grade"] == "A+"
    assert row["aplus"]["framework"] == "ob_retest"
    assert row["aplus"]["kill_zone"] == "london"
    assert row["aplus"]["poi"]["poi_type"] == "OB"
    assert row["extra"]["wired_to_host"] is False
    assert row["extra"]["cannot_apply"] is True
    assert row["extra"]["do_not_expand_armed_tags"] is True


def test_observe_aplus_not_wired_into_live_hooks():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    bridge = (root / "src/components/ultimate_book/bridge.py").read_text(encoding="utf-8")
    owner = (root / "src/components/ultimate_book/book_owner.py").read_text(encoding="utf-8")
    selector = (root / "src/components/selector_v4.py").read_text(encoding="utf-8")
    assert "observe_aplus_candidate" not in bridge
    assert "observe_aplus_candidate" not in owner
    assert "observe_aplus_candidate" not in selector
    assert "maybe_observe_aplus_at_place" not in bridge
    assert "maybe_observe_aplus_at_place" not in owner
    assert "maybe_observe_aplus_at_place" not in selector
    assert "from src.judgment" not in selector
    assert "maybe_observe_ub_auth_010" in bridge
    assert "maybe_observe_ub_plc_017" in owner


def test_live_a1_gold_default_still_documented():
    class _Bare:
        sleeve = "dsp_two_bar_t"
        side = "short"
        entry = 2300.0
        stop = 2305.0
        stop_dist = 5.0

    gold = intent_gold_state(_Bare(), origin="f5_challenge", books={}, as_of_utc=AS_OF)
    assert gold is not None
    assert gold["identity"]["symbol"] == "XAUUSD"


def test_xau_gold_state_path_unbroken_without_aplus():
    gold = assemble_gold_state_v0(
        as_of_utc=AS_OF,
        side="short",
        sleeve="dsp_two_bar_t",
        symbol="XAUUSD",
        origin_organism="f5_challenge",
        spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
        geometry={"entry": 2300.0, "stop": 2305.0, "stop_dist": 5.0},
        cost={"spread_r_of_stop": 0.04},
        sleeve_features={"tag": "dsp_two_bar_t"},
    )
    assert gold["schema"] == SCHEMA_GOLD
    assert gold["identity"]["symbol"] == "XAUUSD"
    assert gold["surface"]["us30_off"] is True
    assert gold["levels"]["poi"] is None
    assert "aplus" not in gold


def test_missing_poi_is_unassembled_not_invented():
    state = assemble_aplus_observe_state(
        _gold_aplus_packet(h1_setup={"poi_identified": False, "poi_type": "none", "poi_price_level": 0.0}),
        books={},
        as_of_utc=AS_OF,
    )
    assert state is not None
    assert state["aplus"]["poi"]["source"] == "unassembled"
    assert state["aplus"]["poi"]["invented"] is False
    assert state["aplus"]["poi"]["price"] is None
    assert state["levels"]["poi"] is None


def test_maybe_observe_aplus_at_place_does_not_mutate_cost_skip():
    skip = "spread_too_wide"
    row = maybe_observe_aplus_at_place(_gbp_aplus_packet(), None, skip)
    assert skip == "spread_too_wide"
    assert row["gate_id"] == OBSERVE_GATE
    assert row["skipped"] == "GTOS_JEV_A1_LOG_off"
    assert row["never_place"] is True
    assert row["never_apply"] is True
    assert row["extra"]["cost_skip"] == "spread_too_wide"
    assert row["extra"]["must_not_mutate_cost_skip"] is True
    assert row["extra"]["do_not_expand_armed_tags"] is True
    assert row["extra"]["envelope_stays_integer"] is True


def test_host_land_note_is_shadow_and_env_gated():
    from pathlib import Path

    land = aplus_host_land()
    assert land["shadow_only"] is True
    assert land["wired_on_this_tree"] is False
    assert land["do_not_wholesale_copy_book_owner"] is True
    assert land["do_not_edit_selector_v4"] is True
    assert land["do_not_expand_armed_tags"] is True
    assert land["envelope_stays_integer"] is True
    assert land["helper"] == "src.judgment.aplus_pipe.maybe_observe_aplus_at_place"
    assert "GTOS_JEV_A1_LOG" in land["env_before_import"]
    note = Path(__file__).resolve().parents[2] / land["note_path"]
    text = note.read_text(encoding="utf-8")
    assert "maybe_observe_aplus_at_place" in text
    assert "Env-gate BEFORE import" in text
    assert "Wholesale-copy" in text or "wholesale-copy" in text
    assert "selector_v4.py" in text
    assert "--tags" in text
    assert "us30_off" in text
