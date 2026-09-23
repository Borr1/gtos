"""APlusSleeveV0 rides the Challenge gate pipe. SHADOW only — no APPLY / place."""

from datetime import datetime, timezone

from src.judgment.a1_log import intent_gold_state
from src.judgment.apply_size import apply_named_tilts, maybe_haircut_unit
from src.judgment.aplus_sleeve import (
    CATALOG,
    GEOMETRY_KEYS,
    REQUIRED_STUB_SYMBOLS,
    SCHEMA,
    assemble_aplus_state,
    catalog_sleeves,
    from_catalog,
    is_aplus_shadow_only,
    score_aplus_shadow,
    spec_completeness,
    sleeve_name,
)
from src.judgment.chair_fields import CHAIR_FIELD_IDS, chair_gate_map
from src.judgment.pack2_fields import (
    PACK2_FIELD_IDS,
    assemble_pack2_fields,
    assert_pack2_maps_existing_families,
    pack2_gate_map,
)
from src.judgment.pack3_fields import (
    GBPJPY_FIXTURE_VECTORS,
    LONDON_EXPAND_FAIL,
    LONDON_EXPAND_PASS,
    NY_IMPULSE_CHOP,
    NY_IMPULSE_PASS,
    PACK3_FIELD_IDS,
    RESID_CAP,
    assemble_pack3_fields,
    assert_pack3_maps_existing_families,
    classify_gj_residual,
    classify_london_expand,
    classify_ny_impulse,
    coerce_time_utc,
    in_ldn_ny_overlap,
    in_london_open,
    in_us30_cash_open,
    locked_constants,
    pack3_gate_map,
    score_gbpjpy_fixture,
    time_utc_from_server,
    values_from_gbpjpy_fixture,
)
from src.judgment.pack4_fields import (
    ADMIT_ANSWERS,
    BOJ_BLOCK,
    CHOICE_ID,
    CHOICE_NOT_READY,
    CHOICE_READY,
    CHOICE_UNASSEMBLED,
    CONJUNCTS,
    PACK4_FIELD_IDS,
    SETUP_GBPJPY,
    SLEEVE_ATTACH_MAP,
    assemble_pack4_fields,
    assert_pack4_maps_existing_families,
    encode_gbpjpy_fixture,
    pack4_gate_map,
    pack4_values_from_gbpjpy_fixture,
    score_gbpjpy_aplus_ready,
)
from src.judgment.pack5_fields import (
    A_PLUS as PACK5_A_PLUS,
    ALMOST as PACK5_ALMOST,
    ATTACH_ALIASES,
    BLOCKED as PACK5_BLOCKED,
    CHOICE_ANSWERS as PACK5_CHOICE_ANSWERS,
    CHOICE_ID as PACK5_CHOICE_ID,
    NULL_STATE as PACK5_NULL,
    PACK5_FIELD_IDS,
    PACK5_FIXTURE_VECTORS,
    SCOUT_ATTACH_NAMES,
    SCOUT_PACKET_PATH,
    resolve_scout_packet_path,
    SCOUT_TIER1_ALIASES,
    SCOUT_TIER1_WIRES,
    SLEEVE_ATTACH_MAP as CHAIR_SLEEVE_ATTACH_MAP,
    assert_pack5_maps_existing_families,
    assert_pack5_t3_not_pack3_alias,
    assert_scout_attach_authority,
    assert_scout_tier1_observe_only,
    resolve_attach_name,
    resolve_gbpjpy_attach,
    encode_gbpjpy_a_plus,
    pack5_gate_map,
    pack5_values_from_gbpjpy_fixture,
    score_gbpjpy_a_plus_ready,
)
from src.judgment.pack6_fields import (
    A_PLUS as PACK6_A_PLUS,
    BLOCKED as PACK6_BLOCKED,
    CHOICE_ID as PACK6_CHOICE_ID,
    HONESTY as PACK6_HONESTY,
    N_IN,
    NULL_STATE as PACK6_NULL,
    PROVE_SEED_FIXTURES,
    PROVE_SEED_IDS,
    SEED_TICKET,
    SETUP_XAU,
    XAU_SHAKEOUT_FIXTURES,
    assert_pack6_maps_existing_families,
    assert_pack6_prove_seed,
    assert_pack6_revised_mute,
    event_mute,
    hypothesis_mute,
    pack6_gate_map,
    score_xau_dsp_shakeout,
)
from src.judgment.edge_freeze import (
    GBPJPY_READY,
    READY_CHOICES,
    XAU_READY,
    assert_edge_freeze,
)
from src.judgment.challenge_shadow import score_position
from src.judgment.compose import compose_shadow
from src.judgment.family import family_class_for
from src.judgment.fluid_gates import assert_inventory_shape, lookup
from src.judgment.fluid_local import session_score


AS_OF = datetime(2026, 9, 17, 8, 0, tzinfo=timezone.utc)
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"


def _geo(entry=4331.45, stop=4336.9, target=4288.19, stop_dist=5.45):
    return {
        "entry": entry,
        "stop": stop,
        "target": target,
        "stop_dist": stop_dist,
        "order_type": "MARKET",
    }


def test_catalog_covers_required_symbols_and_geometry_keys():
    sleeves = catalog_sleeves()
    symbols = {s.symbol for s in sleeves}
    for required in REQUIRED_STUB_SYMBOLS:
        assert required in symbols
    assert "USDJPY" in symbols
    assert set(CATALOG) >= {
        "xau_london_ob_retest",
        "gbpjpy_london_session_sweep",
        "eurusd_ny_ob_retest",
    }
    for spec in sleeves:
        complete = spec_completeness(spec)
        assert complete["spec_complete"] is True
        assert complete["geometry_keys"] == list(GEOMETRY_KEYS)
        assert complete["invented_peers"] is False
        assert complete["peers_assembled"] is False
        assert spec.sleeve == sleeve_name(spec.setup_id)
        assert spec.sleeve.startswith("aplus_")
        assert spec.peer_ca_hooks.get("dxy_hook") == "named_only"
        assert spec.occupancy_hooks.get("cluster")


def test_family_class_is_aplus_study_not_hard_off_or_w7():
    assert family_class_for("aplus_xau_london_ob_retest") == "a_plus_study"
    assert family_class_for("aplus_gbpjpy_london_session_sweep") == "a_plus_study"
    assert family_class_for("aplus_eurusd_ny_ob_retest", origin="w7_ultimate_book") == "a_plus_study"
    assert family_class_for("dsp_two_bar_t") == "study"


def test_assemble_three_symbols_attach_gold_state_without_inventing_peers():
    rows = []
    for setup_id, side, geo in (
        ("xau_london_ob_retest", "short", _geo()),
        ("gbpjpy_london_session_sweep", "long", _geo(185.20, 184.40, 186.80, 0.80)),
        ("eurusd_ny_ob_retest", "long", _geo(1.0850, 1.0820, 1.0910, 0.0030)),
    ):
        spec = from_catalog(setup_id)
        state = assemble_aplus_state(
            spec,
            as_of_utc=AS_OF,
            side=side,
            books=None,
            geometry=geo,
            cost={"spread_r_of_stop": 0.04, "source": "tick"},
        )
        rows.append(state)
        assert state["schema"] == "gtos.judgment.gold_state.v0"
        assert state["identity"]["sleeve"] == spec.sleeve
        assert state["identity"]["setup_id"] == setup_id
        assert state["identity"]["sleeve_kind"] == "aplus_v0"
        assert state["identity"]["family_class"] == "a_plus_study"
        assert state["identity"]["origin_organism"] == "aplus_research"
        assert state["identity"]["symbol"] == spec.symbol
        assert state["aplus"]["schema"] == SCHEMA
        assert state["aplus"]["session"] == spec.session
        assert state["aplus"]["never_apply_size"] is True
        assert state["peers"]["invented"] is False
        assert state["peers"]["assembled"] is False
        assert state["peers"]["peer_state"] is None
        assert "peers.peer_state" in state["completeness"]["missing_fields"]
        assert state["completeness"]["aplus_sleeve"] is True
        assert state["completeness"]["peers"] is False
        assert state["occupancy"]["cluster_named"] == spec.occupancy_hooks["cluster"]
        assert state["occupancy"]["keep_one_symbol"] is True
        assert state["occupancy"]["occupancy_source"] == "aplus_hooks_unassembled"
        assert state["occupancy"]["symbol_open"] is None
        assert state["completeness"]["occupancy"] is False
        assert state["geometry"]["order_type"] == "MARKET"
        assert state["geometry"]["plan_r"] == spec.geometry_defaults["plan_r"]
        assert state["sleeve_features"]["session"] == spec.session
    assert {r["identity"]["symbol"] for r in rows} == {"XAUUSD", "GBPJPY", "EURUSD"}


def test_score_shadow_stamps_48_fluid_and_never_applies(monkeypatch):
    monkeypatch.setenv("GTOS_JEV_APPLY_LIVE", "1")
    row = score_aplus_shadow(
        "xau_london_ob_retest",
        as_of_utc=AS_OF,
        side="short",
        candidate_id="aplus-xau-1",
        geometry=_geo(),
        cost={"spread_r_of_stop": 0.08, "source": "tick"},
        ticket="aplus-xau-1",
    )
    composed = row["compose"]
    assert row["never_place"] is True
    assert row["never_apply_size"] is True
    assert row["apply_this_row"] is False
    assert composed["aplus_shadow_only"] is True
    assert composed["apply_this_row"] is False
    assert composed["disposition"] == "log_only"
    assert composed["live_size_tilt"] == 1.0
    assert composed["live_cost_tilt"] == 1.0
    assert composed["fluid"]["n"] == 48
    assert composed["fluid"]["never_place"] is True
    flow = composed["fluid"]["gates"]["f5_xau_flow_alignment_size_tilt"]
    cost = composed["fluid"]["gates"]["F5-JEV-004"]
    assert flow["apply"] is False
    assert cost["apply"] is False
    assert flow["live"] == 1.0
    assert cost["live"] == 1.0
    assert is_aplus_shadow_only(row["state"], compose_row=composed) is True
    shape = assert_inventory_shape()
    assert shape["n_fluid"] == 48


def test_gbpjpy_and_eurusd_shadow_same_pipe():
    for setup_id, side, geo in (
        ("gbpjpy_london_session_sweep", "short", _geo(185.20, 186.00, 183.60, 0.80)),
        ("eurusd_ny_ob_retest", "long", _geo(1.0850, 1.0820, 1.0910, 0.0030)),
        ("usdjpy_tokyo_asia_fade", "short", _geo(149.80, 150.20, 148.90, 0.40)),
    ):
        row = score_aplus_shadow(
            setup_id,
            as_of_utc=AS_OF,
            side=side,
            geometry=geo,
            ticket=f"aplus-{setup_id}",
        )
        assert row["family_class"] == "a_plus_study"
        assert row["compose"]["fluid"]["n"] == 48
        assert row["compose"]["apply_this_row"] is False
        assert row["never_place"] is True


def test_challenge_score_position_routes_aplus_sleeve():
    row = score_position(
        {
            "ticket": "aplus-route-1",
            "symbol": "XAUUSD",
            "side": "SHORT",
            "sleeve": "aplus_xau_london_ob_retest",
            "setup_id": "xau_london_ob_retest",
            "entry": 4331.45,
            "orig_sl": 4336.9,
            "tp": 4288.19,
            "stop_dist": 5.45,
            "spread_R": 0.04,
            "open_time_utc": "2026-09-17T08:00:00Z",
            "_kind": "slate",
        },
        books={},
        spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
        sit_meta={"bal": 95196.4},
    )
    assert row["schema"] == "gtos.judgment.aplus_shadow.v0"
    assert row["house"]["aplus_shadow_only"] is True
    assert row["compose"]["apply_this_row"] is False
    assert row["state"]["identity"]["family_class"] == "a_plus_study"


def test_apply_named_tilts_and_haircut_refuse_aplus(monkeypatch):
    monkeypatch.setenv("GTOS_JEV_APPLY_LIVE", "1")
    state = assemble_aplus_state(
        "xau_london_ob_retest",
        as_of_utc=AS_OF,
        side="short",
        geometry=_geo(),
        cost={"spread_r_of_stop": 0.10, "source": "tick"},
    )
    composed = compose_shadow(state, ticket="aplus-no-apply")
    named = apply_named_tilts(composed, ticket="aplus-no-apply")
    assert named["apply_this_row"] is False
    assert named["flow"] == 1.0
    assert named["cost"] == 1.0
    unit = {"risk_pct_per_trade": 0.0015, "volume": 2.0, "sleeve": "aplus_xau_london_ob_retest"}
    out = maybe_haircut_unit(
        unit,
        composed,
        ticket="aplus-no-apply",
        login=CHALLENGE_LOGIN,
        ns=CHALLENGE_NS,
        sleeve="aplus_xau_london_ob_retest",
    )
    assert out["volume"] == 2.0
    assert out["risk_pct_per_trade"] == 0.0015


def test_intent_gold_state_assembles_aplus_without_place():
    class _Intent:
        symbol = "GBPJPY"
        sleeve = "aplus_gbpjpy_london_session_sweep"
        setup_id = "gbpjpy_london_session_sweep"
        side = "long"
        entry = 185.20
        stop = 184.40
        stop_dist = 0.80
        target = 186.80
        candidate_id = "aplus-gbpjpy-1"
        ticket = "aplus-gbpjpy-1"
        order_type = "MARKET"

    state = intent_gold_state(_Intent(), origin="f5_challenge", books={}, as_of_utc=AS_OF)
    assert state is not None
    assert state["identity"]["sleeve_kind"] == "aplus_v0"
    assert state["identity"]["family_class"] == "a_plus_study"
    assert state["aplus"]["setup_id"] == "gbpjpy_london_session_sweep"
    composed = compose_shadow(state, ticket="aplus-gbpjpy-1")
    assert composed["aplus_shadow_only"] is True
    assert composed["apply_this_row"] is False


def test_session_score_uses_aplus_preferred_session():
    london = {
        "sessions": {"named": "london"},
        "aplus": {"session": "london"},
        "sleeve_features": {},
    }
    asia_on_london_sleeve = {
        "sessions": {"named": "asia"},
        "aplus": {"session": "london"},
        "sleeve_features": {},
    }
    dead = {
        "sessions": {"named": "dead_21_00z"},
        "aplus": {"session": "london"},
        "sleeve_features": {},
    }
    tokyo = {
        "sessions": {"named": "asia"},
        "aplus": {"session": "tokyo"},
        "sleeve_features": {},
    }
    ordinary = {
        "sessions": {"named": "london"},
        "aplus": {},
        "sleeve_features": {},
    }
    assert session_score(london) == 2.0
    assert session_score(asia_on_london_sleeve) == 1.0
    assert session_score(dead) == 0.0
    assert session_score(tokyo) == 2.0
    assert session_score(ordinary) == 2.0


def test_missing_tape_keeps_occupancy_none_and_does_not_invent_high():
    state = assemble_aplus_state(
        "eurusd_ny_ob_retest",
        as_of_utc=AS_OF,
        side="long",
        books=None,
        geometry=_geo(1.0850, 1.0820, 1.0910, 0.0030),
        spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
    )
    assert state["occupancy"]["isolated_reentry_legal"] is None
    assert state["occupancy"]["corr_hold_named"] is None
    assert state["occupancy"]["cluster_named"] == "fx_major"
    assert state["completeness"]["occupancy"] is False
    assert state["news"]["spine_empty"] is True
    assert state["news"]["high_in_f5_window"] is None
    assert state["peers"]["invented"] is False


def test_chair_fields_closed_set_maps_onto_existing_gates():
    rows = chair_gate_map()
    assert [r["field"] for r in rows] == list(CHAIR_FIELD_IDS)
    assert len(rows) == 8
    for row in rows:
        assert row["shadow_only"] is True
        assert row["gate_questions"]
        assert row["gate_ids"]
        for gid in row["gate_ids"]:
            gate = lookup(gid)
            assert gate is not None, gid
            assert gate["class"] in {"fluid", "envelope"}
        if row["field"] == "us30_rth_vs_eth":
            assert row["envelope"] == "ENV-US30"
            assert lookup("ENV-US30")["class"] == "envelope"


def test_chair_clock_fields_assemble_peer_fields_stay_unassembled():
    london = assemble_aplus_state(
        "gbpjpy_london_session_sweep",
        as_of_utc=AS_OF,
        side="long",
        geometry=_geo(185.20, 184.40, 186.80, 0.80),
    )
    chair = london["chair_fields"]
    assert chair["schema"] == "gtos.judgment.aplus_chair_fields.v0"
    assert chair["n"] == 8
    assert chair["invented"] is False
    assert set(chair["fields"]) == set(CHAIR_FIELD_IDS)
    assert london["aplus"]["chair_fields"]["n"] == 8
    fields = chair["fields"]
    assert fields["fx_session_london_fit"]["applies"] is True
    assert fields["fx_session_london_fit"]["assembled"] is True
    assert fields["fx_session_london_fit"]["value"] == 2.0
    assert fields["sess.ldn_ny_overlap_vol"]["assembled"] is True
    assert fields["sess.ldn_ny_overlap_vol"]["value"]["in_window"] is False
    assert fields["sess.ldn_ny_overlap_vol"]["value"]["vol"] is None
    assert fields["tokyo_fix_window_label"]["assembled"] is True
    assert fields["tokyo_fix_window_label"]["value"] is False
    assert fields["gbpjpy_dual_leg_agree"]["applies"] is True
    assert fields["gbpjpy_dual_leg_agree"]["assembled"] is False
    assert fields["gbpjpy_dual_leg_agree"]["invented"] is False
    assert "chair_fields.gbpjpy_dual_leg_agree" in london["completeness"]["missing_fields"]
    assert fields["us30_rth_vs_eth"]["applies"] is False
    assert fields["us30_rth_vs_eth"]["envelope"] == "ENV-US30"
    xau = assemble_aplus_state("xau_london_ob_retest", as_of_utc=AS_OF, side="short", geometry=_geo())
    assert xau["chair_fields"]["fields"]["usd_proxy_vs_xau"]["applies"] is True
    assert xau["chair_fields"]["fields"]["usd_proxy_vs_xau"]["assembled"] is False
    assert xau["chair_fields"]["fields"]["fx_session_london_fit"]["applies"] is False
    assert xau["chair_fields"]["fields"]["corr.xau_vs_eur_proxy_usd"]["applies"] is True
    assert xau["chair_fields"]["fields"]["corr.xau_vs_eur_proxy_usd"]["assembled"] is False


def test_overlap_and_tokyo_fix_windows_from_clock():
    overlap = assemble_aplus_state(
        "eurusd_ny_ob_retest",
        as_of_utc=datetime(2026, 9, 17, 13, 15, tzinfo=timezone.utc),
        side="long",
        geometry=_geo(1.0850, 1.0820, 1.0910, 0.0030),
    )
    ov = overlap["chair_fields"]["fields"]["sess.ldn_ny_overlap_vol"]["value"]
    assert ov["in_window"] is True
    assert ov["vol"] is None
    assert overlap["chair_fields"]["fields"]["fx_session_london_fit"]["value"] == 1.0
    dead_fix = assemble_aplus_state(
        "usdjpy_tokyo_asia_fade",
        as_of_utc=datetime(2026, 9, 17, 0, 55, tzinfo=timezone.utc),
        side="short",
        geometry=_geo(149.80, 150.20, 148.90, 0.40),
    )
    assert dead_fix["chair_fields"]["fields"]["tokyo_fix_window_label"]["value"] is True
    assert dead_fix["sessions"]["named"] == "dead_21_00z"
    assert session_score(dead_fix) == 0.0
    asia_fix = assemble_aplus_state(
        "usdjpy_tokyo_asia_fade",
        as_of_utc=datetime(2026, 9, 17, 1, 5, tzinfo=timezone.utc),
        side="short",
        geometry=_geo(149.80, 150.20, 148.90, 0.40),
    )
    assert asia_fix["chair_fields"]["fields"]["tokyo_fix_window_label"]["value"] is True
    assert asia_fix["sessions"]["named"] == "asia"
    composed = compose_shadow(asia_fix, ticket="aplus-tokyo-fix")
    assert composed["apply_this_row"] is False
    assert composed["chair_fields"]["n"] == 8
    assert composed["pack2_fields"]["n"] == 9
    assert composed["fluid"]["gates"]["FLUID-ADM-004"]["source"] == (
        "sessions.named+aplus.chair_fields+aplus.pack2+aplus.pack3"
    )


def test_named_peer_chair_values_assemble_without_inventing():
    state = assemble_aplus_state(
        "xau_london_ob_retest",
        as_of_utc=AS_OF,
        side="short",
        geometry=_geo(),
        peer_state={"usd_proxy_vs_xau": {"value": 0.0, "source": "symbol_state_v0"}},
        chair_values={"corr.xau_vs_eur_proxy_usd": "against"},
    )
    fields = state["chair_fields"]["fields"]
    assert fields["usd_proxy_vs_xau"]["assembled"] is True
    assert fields["usd_proxy_vs_xau"]["value"] == 0.0
    assert fields["usd_proxy_vs_xau"]["invented"] is False
    assert fields["corr.xau_vs_eur_proxy_usd"]["assembled"] is True
    assert fields["corr.xau_vs_eur_proxy_usd"]["value"] == "against"
    composed = compose_shadow(state, ticket="aplus-xau-corr")
    veto = composed["fluid"]["gates"]["FLUID-PLC-001"]
    assert veto["decidable"] is True
    assert veto["shadow"] is True
    assert veto["source"] == "aplus.chair_fields.corr"
    assert composed["apply_this_row"] is False
    assert composed["live_size_tilt"] == 1.0


def test_chair_fields_never_apply_and_do_not_add_gates():
    row = score_aplus_shadow(
        "eurusd_ny_ob_retest",
        as_of_utc=datetime(2026, 9, 17, 13, 0, tzinfo=timezone.utc),
        side="long",
        geometry=_geo(1.0850, 1.0820, 1.0910, 0.0030),
        ticket="aplus-chair-shadow",
    )
    assert row["compose"]["fluid"]["n"] == 48
    assert row["compose"]["apply_this_row"] is False
    assert row["compose"]["chair_fields"]["invented"] is False
    assert lookup("ENV-US30")["class"] == "envelope"
    shape = assert_inventory_shape()
    assert shape["n_fluid"] == 48
    assert shape["n_envelope"] == 8


def test_pack2_closed_set_maps_onto_adm_siz_nws_only():
    rows = pack2_gate_map()
    assert [r["field"] for r in rows] == list(PACK2_FIELD_IDS)
    assert len(rows) == 9
    mapped = assert_pack2_maps_existing_families()
    assert mapped["ok"] is True, mapped["bad"]
    for row in rows:
        assert row["shadow_only"] is True
        assert row["never_refuse"] is True
        assert row["never_apply_size"] is True
        assert row["surface"] in {"gate_input", "sleeve_field", "info"}
        assert set(row["families"]) <= {"admit", "size", "news_window"}
        assert row["gate_questions"]
        assert row["gate_ids"]
        for gid in row["gate_ids"]:
            gate = lookup(gid)
            assert gate is not None, gid
            assert gate["family"] in {"admit", "size", "news_window"}
            assert not str(gid).startswith("FLUID-PLC")
            assert not str(gid).startswith("FLUID-REN")
            assert not str(gid).startswith("FLUID-HLD")
        if row["field"] == "gate.ny_rth_us30_act_ok":
            assert row["envelope"] == "ENV-US30"
            assert lookup("ENV-US30")["class"] == "envelope"
        if row["field"] == "info.risk_on_off_bundle":
            assert row["surface"] == "info"


def test_pack2_clock_stubs_assemble_peers_stay_unassembled():
    empty = {"spine_id": None, "sources": [], "events": [], "n_files": 0}
    london = assemble_aplus_state(
        "gbpjpy_london_session_sweep",
        as_of_utc=AS_OF,
        side="long",
        geometry=_geo(185.20, 184.40, 186.80, 0.80),
        spines=empty,
    )
    pack2 = london["pack2_fields"]
    assert pack2["schema"] == "gtos.judgment.aplus_pack2_fields.v0"
    assert pack2["n"] == 9
    assert pack2["invented"] is False
    assert pack2["never_refuse"] is True
    assert set(pack2["fields"]) == set(PACK2_FIELD_IDS)
    assert london["aplus"]["pack2_fields"]["n"] == 9
    fields = pack2["fields"]
    assert fields["gate.session_overlap_ok"]["applies"] is True
    assert fields["gate.session_overlap_ok"]["assembled"] is True
    assert fields["gate.session_overlap_ok"]["value"] is False
    assert fields["gate.asia_jpy_act_ok"]["applies"] is True
    assert fields["gate.asia_jpy_act_ok"]["value"] is False
    assert fields["sleeve.london_expand_eur_gbp"]["value"] == 2.0
    assert fields["gate.cross_stack_gbpjpy"]["applies"] is True
    assert fields["gate.cross_stack_gbpjpy"]["assembled"] is False
    assert fields["gate.cross_stack_gbpjpy"]["invented"] is False
    assert "pack2_fields.gate.cross_stack_gbpjpy" in london["completeness"]["missing_fields"]
    assert fields["gate.event_boj_window"]["assembled"] is False
    assert fields["info.risk_on_off_bundle"]["assembled"] is False
    assert fields["gate.ny_rth_us30_act_ok"]["applies"] is False
    assert fields["gate.ny_rth_us30_act_ok"]["envelope"] == "ENV-US30"
    xau = assemble_aplus_state(
        "xau_london_ob_retest",
        as_of_utc=AS_OF,
        side="short",
        geometry=_geo(),
        spines=empty,
    )
    xf = xau["pack2_fields"]["fields"]
    assert xf["sleeve.usd_common_factor"]["applies"] is True
    assert xf["sleeve.usd_common_factor"]["assembled"] is False
    assert xf["sleeve.xau_usd_proxy_align"]["applies"] is True
    assert xf["sleeve.xau_usd_proxy_align"]["assembled"] is False
    assert xf["sleeve.london_expand_eur_gbp"]["applies"] is False
    assert xf["gate.asia_jpy_act_ok"]["applies"] is False


def test_pack2_overlap_asia_rth_windows_from_clock():
    empty = {"spine_id": None, "sources": [], "events": [], "n_files": 0}
    overlap = assemble_aplus_state(
        "eurusd_ny_ob_retest",
        as_of_utc=datetime(2026, 9, 17, 13, 15, tzinfo=timezone.utc),
        side="long",
        geometry=_geo(1.0850, 1.0820, 1.0910, 0.0030),
        spines=empty,
    )
    pf = overlap["pack2_fields"]["fields"]
    assert pf["gate.session_overlap_ok"]["value"] is True
    assert pf["sleeve.london_expand_eur_gbp"]["value"] == 1.0
    assert pf["gate.asia_jpy_act_ok"]["applies"] is False
    dead = assemble_aplus_state(
        "usdjpy_tokyo_asia_fade",
        as_of_utc=datetime(2026, 9, 17, 0, 55, tzinfo=timezone.utc),
        side="short",
        geometry=_geo(149.80, 150.20, 148.90, 0.40),
        spines=empty,
    )
    assert dead["sessions"]["named"] == "dead_21_00z"
    assert dead["pack2_fields"]["fields"]["gate.asia_jpy_act_ok"]["value"] is False
    asia = assemble_aplus_state(
        "usdjpy_tokyo_asia_fade",
        as_of_utc=datetime(2026, 9, 17, 1, 5, tzinfo=timezone.utc),
        side="short",
        geometry=_geo(149.80, 150.20, 148.90, 0.40),
        spines=empty,
    )
    assert asia["sessions"]["named"] == "asia"
    assert asia["pack2_fields"]["fields"]["gate.asia_jpy_act_ok"]["value"] is True
    rth = assemble_pack2_fields(
        symbol="US30",
        as_of_utc=datetime(2026, 9, 17, 14, 0, tzinfo=timezone.utc),
        session_named="ny",
        news={"spine_empty": True, "events": []},
    )
    assert rth["fields"]["gate.ny_rth_us30_act_ok"]["applies"] is True
    assert rth["fields"]["gate.ny_rth_us30_act_ok"]["value"] is True
    assert rth["fields"]["gate.ny_rth_us30_act_ok"]["envelope_stays"] == "integer_off"
    eth = assemble_pack2_fields(
        symbol="US30",
        as_of_utc=datetime(2026, 9, 17, 8, 0, tzinfo=timezone.utc),
        session_named="london",
        news={"spine_empty": True, "events": []},
    )
    assert eth["fields"]["gate.ny_rth_us30_act_ok"]["value"] is False


def test_pack2_named_peer_and_boj_never_refuse():
    empty = {"spine_id": None, "sources": [], "events": [], "n_files": 0}
    state = assemble_aplus_state(
        "xau_london_ob_retest",
        as_of_utc=AS_OF,
        side="short",
        geometry=_geo(),
        spines=empty,
        peer_state={"sleeve.usd_common_factor": {"value": 0.4, "source": "symbol_state_v0"}},
        pack2_values={
            "sleeve.xau_usd_proxy_align": True,
            "info.risk_on_off_bundle": {"stance": "risk_off", "source": "symbol_state_v0"},
        },
    )
    fields = state["pack2_fields"]["fields"]
    assert fields["sleeve.usd_common_factor"]["assembled"] is True
    assert fields["sleeve.usd_common_factor"]["value"] == 0.4
    assert fields["sleeve.usd_common_factor"]["invented"] is False
    assert fields["sleeve.xau_usd_proxy_align"]["value"] is True
    assert fields["info.risk_on_off_bundle"]["value"]["stance"] == "risk_off"
    composed = compose_shadow(state, ticket="aplus-pack2-xau")
    assert composed["apply_this_row"] is False
    assert composed["live_size_tilt"] == 1.0
    assert composed["pack2_fields"]["never_refuse"] is True
    assert all(g["refuse"] is False for g in composed["fluid"]["gates"].values())
    boj = assemble_pack2_fields(
        symbol="USDJPY",
        as_of_utc=AS_OF,
        session_named="london",
        news={
            "spine_empty": False,
            "events": [
                {
                    "event": "BOJ Rate Decision",
                    "currency": "JPY",
                    "impact": "HIGH",
                    "minutes_from_as_of": 5,
                }
            ],
            "high_in_f5_window": True,
        },
    )
    assert boj["fields"]["gate.event_boj_window"]["assembled"] is True
    assert boj["fields"]["gate.event_boj_window"]["value"] is True
    assert boj["fields"]["gate.event_boj_window"]["never_refuse"] is True
    empty_boj = assemble_pack2_fields(
        symbol="USDJPY",
        as_of_utc=AS_OF,
        session_named="london",
        news={"spine_empty": True, "events": []},
    )
    assert empty_boj["fields"]["gate.event_boj_window"]["assembled"] is False
    assert empty_boj["invented"] is False


def test_pack2_never_apply_and_does_not_add_gates():
    row = score_aplus_shadow(
        "eurusd_ny_ob_retest",
        as_of_utc=datetime(2026, 9, 17, 13, 0, tzinfo=timezone.utc),
        side="long",
        geometry=_geo(1.0850, 1.0820, 1.0910, 0.0030),
        ticket="aplus-pack2-shadow",
        spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
    )
    assert row["compose"]["fluid"]["n"] == 48
    assert row["compose"]["apply_this_row"] is False
    assert row["compose"]["pack2_fields"]["n"] == 9
    assert row["compose"]["pack2_fields"]["invented"] is False
    assert row["compose"]["pack2_fields"]["never_refuse"] is True
    assert all(g["refuse"] is False for g in row["compose"]["fluid"]["gates"].values())
    shape = assert_inventory_shape()
    assert shape["n_fluid"] == 48
    assert shape["n_envelope"] == 8


def test_pack3_locked_constants_and_classifiers():
    constants = locked_constants()
    assert constants["resid_cap"] == 0.15
    assert constants["resid_unit"] == "GJ"
    assert constants["london_expand_pass"] == 1.25
    assert constants["london_expand_fail"] == 1.0
    assert constants["ny_impulse_pass"] == 1.5
    assert constants["ny_impulse_chop"] == 1.0
    assert constants["clock_source"] == "time_utc"
    assert constants["server_minus_hours"] == 3
    assert RESID_CAP == 0.15
    assert LONDON_EXPAND_PASS == 1.25
    assert LONDON_EXPAND_FAIL == 1.0
    assert NY_IMPULSE_PASS == 1.5
    assert NY_IMPULSE_CHOP == 1.0
    assert classify_london_expand(1.25) == "pass"
    assert classify_london_expand(1.40) == "pass"
    assert classify_london_expand(0.99) == "fail"
    assert classify_london_expand(1.10) == "mid"
    assert classify_ny_impulse(1.5) == "impulse"
    assert classify_ny_impulse(0.80) == "chop"
    assert classify_ny_impulse(1.20) == "mid"
    assert classify_gj_residual(0.15) == "pass"
    assert classify_gj_residual(0.08) == "pass"
    assert classify_gj_residual(0.1500001) == "fail"
    assert classify_gj_residual(0.22) == "fail"


def test_pack3_clocks_on_time_utc_winter_summer_and_server_minus_3h():
    winter = datetime(2026, 1, 15, 7, 30, tzinfo=timezone.utc)
    summer = datetime(2026, 7, 15, 6, 30, tzinfo=timezone.utc)
    assert in_london_open(winter) is True
    assert in_london_open(datetime(2026, 1, 15, 6, 30, tzinfo=timezone.utc)) is False
    assert in_london_open(summer) is True
    assert in_london_open(datetime(2026, 7, 15, 8, 30, tzinfo=timezone.utc)) is False
    assert in_us30_cash_open(datetime(2026, 1, 15, 14, 30, tzinfo=timezone.utc)) is True
    assert in_us30_cash_open(datetime(2026, 1, 15, 13, 30, tzinfo=timezone.utc)) is False
    assert in_us30_cash_open(datetime(2026, 7, 15, 13, 30, tzinfo=timezone.utc)) is True
    assert in_us30_cash_open(datetime(2026, 7, 15, 14, 30, tzinfo=timezone.utc)) is False
    assert in_ldn_ny_overlap(datetime(2026, 1, 15, 13, 0, tzinfo=timezone.utc)) is True
    assert in_ldn_ny_overlap(datetime(2026, 1, 15, 12, 30, tzinfo=timezone.utc)) is False
    assert in_ldn_ny_overlap(datetime(2026, 7, 15, 12, 30, tzinfo=timezone.utc)) is True
    assert in_ldn_ny_overlap(datetime(2026, 7, 15, 16, 0, tzinfo=timezone.utc)) is False
    server_winter_ldn = datetime(2026, 1, 15, 10, 30, tzinfo=timezone.utc)
    assert time_utc_from_server(server_winter_ldn) == winter
    assert coerce_time_utc(server_time=server_winter_ldn) == winter
    assert in_london_open(time_utc_from_server(server_winter_ldn)) is True
    named = coerce_time_utc(
        datetime(2026, 1, 15, 7, 30, tzinfo=timezone.utc),
        server_time=datetime(2026, 1, 15, 20, 0, tzinfo=timezone.utc),
    )
    assert named == winter


def test_pack3_closed_set_maps_onto_adm_siz_nws_only():
    rows = pack3_gate_map()
    assert [r["field"] for r in rows] == list(PACK3_FIELD_IDS)
    assert len(rows) == 7
    mapped = assert_pack3_maps_existing_families()
    assert mapped["ok"] is True, mapped["bad"]
    for row in rows:
        assert row["shadow_only"] is True
        assert row["never_refuse"] is True
        assert row["never_apply_size"] is True
        assert row["surface"] in {"gate_input", "sleeve_field"}
        assert set(row["families"]) <= {"admit", "size", "news_window"}
        assert row["gate_questions"]
        assert row["gate_ids"]
        for gid in row["gate_ids"]:
            gate = lookup(gid)
            assert gate is not None, gid
            assert gate["family"] in {"admit", "size", "news_window"}
            assert not str(gid).startswith("FLUID-PLC")
            assert not str(gid).startswith("FLUID-REN")
            assert not str(gid).startswith("FLUID-HLD")
        if row["field"] == "ny_cash_open_us30":
            assert row["envelope"] == "ENV-US30"
            assert lookup("ENV-US30")["class"] == "envelope"


def test_pack3_clock_features_assemble_peers_stay_unassembled():
    empty = {"spine_id": None, "sources": [], "events": [], "n_files": 0}
    london = assemble_aplus_state(
        "gbpjpy_london_session_sweep",
        as_of_utc=datetime(2026, 1, 15, 7, 30, tzinfo=timezone.utc),
        side="long",
        geometry=_geo(185.20, 184.40, 186.80, 0.80),
        spines=empty,
    )
    pack3 = london["pack3_fields"]
    assert pack3["schema"] == "gtos.judgment.aplus_pack3_fields.v0"
    assert pack3["n"] == 7
    assert pack3["invented"] is False
    assert pack3["never_refuse"] is True
    assert pack3["clock_source"] == "time_utc"
    assert pack3["constants"]["resid_cap"] == 0.15
    assert set(pack3["fields"]) == set(PACK3_FIELD_IDS)
    assert london["aplus"]["pack3_fields"]["n"] == 7
    fields = pack3["fields"]
    assert fields["sess.ldn_ny_overlap_vol"]["assembled"] is True
    assert fields["sess.ldn_ny_overlap_vol"]["value"]["in_window"] is False
    assert fields["sess.ldn_ny_overlap_vol"]["value"]["season"] == "winter"
    assert fields["sess.ldn_ny_overlap_vol"]["value"]["vol"] is None
    assert fields["london_open_eur_gbp_expand"]["value"]["in_window"] is True
    assert fields["london_open_eur_gbp_expand"]["value"]["class"] is None
    assert fields["corr.gbpjpy_risk_cross"]["applies"] is True
    assert fields["corr.gbpjpy_risk_cross"]["assembled"] is False
    assert fields["corr.gbpjpy_risk_cross"]["invented"] is False
    assert "pack3_fields.corr.gbpjpy_risk_cross" in london["completeness"]["missing_fields"]
    assert fields["corr.eur_gbp_usd_co_move"]["assembled"] is False
    assert fields["macro.boj_guidance_window"]["assembled"] is False
    assert fields["ny_cash_open_us30"]["applies"] is False
    assert fields["ny_cash_open_us30"]["envelope"] == "ENV-US30"
    xau = assemble_aplus_state(
        "xau_london_ob_retest",
        as_of_utc=datetime(2026, 1, 15, 7, 30, tzinfo=timezone.utc),
        side="short",
        geometry=_geo(),
        spines=empty,
    )
    xf = xau["pack3_fields"]["fields"]
    assert xf["corr.xau_vs_eur_proxy_usd"]["applies"] is True
    assert xf["corr.xau_vs_eur_proxy_usd"]["assembled"] is False
    assert xf["london_open_eur_gbp_expand"]["applies"] is False
    assert xf["corr.gbpjpy_risk_cross"]["applies"] is False


def test_pack3_overlap_london_open_us30_windows_from_time_utc():
    empty = {"spine_id": None, "sources": [], "events": [], "n_files": 0}
    overlap_summer = assemble_aplus_state(
        "eurusd_ny_ob_retest",
        as_of_utc=datetime(2026, 7, 15, 12, 30, tzinfo=timezone.utc),
        side="long",
        geometry=_geo(1.0850, 1.0820, 1.0910, 0.0030),
        spines=empty,
    )
    ov = overlap_summer["pack3_fields"]["fields"]["sess.ldn_ny_overlap_vol"]["value"]
    assert ov["in_window"] is True
    assert ov["season"] == "summer"
    assert ov["window_utc"] == [12, 16]
    overlap_winter = assemble_pack3_fields(
        symbol="EURUSD",
        time_utc=datetime(2026, 1, 15, 13, 15, tzinfo=timezone.utc),
        news={"spine_empty": True, "events": []},
    )
    assert overlap_winter["fields"]["sess.ldn_ny_overlap_vol"]["value"]["in_window"] is True
    assert overlap_winter["fields"]["sess.ldn_ny_overlap_vol"]["value"]["season"] == "winter"
    assert overlap_winter["fields"]["sess.ldn_ny_overlap_vol"]["value"]["window_utc"] == [13, 17]
    rth_winter = assemble_pack3_fields(
        symbol="US30",
        time_utc=datetime(2026, 1, 15, 14, 30, tzinfo=timezone.utc),
        news={"spine_empty": True, "events": []},
        pack3_values={"ny_cash_open_us30": 1.80},
    )
    ny = rth_winter["fields"]["ny_cash_open_us30"]
    assert ny["applies"] is True
    assert ny["value"]["in_window"] is True
    assert ny["value"]["open_utc"] == "14:30"
    assert ny["value"]["class"] == "impulse"
    assert ny["envelope_stays"] == "integer_off"
    eth_summer = assemble_pack3_fields(
        symbol="US30",
        time_utc=datetime(2026, 7, 15, 12, 0, tzinfo=timezone.utc),
        news={"spine_empty": True, "events": []},
        pack3_values={"ny_cash_open_us30": 0.70},
    )
    assert eth_summer["fields"]["ny_cash_open_us30"]["value"]["in_window"] is False
    assert eth_summer["fields"]["ny_cash_open_us30"]["value"]["class"] == "chop"
    assert eth_summer["fields"]["ny_cash_open_us30"]["value"]["open_utc"] == "13:30"


def test_gbpjpy_fixture_vectors_t1_pass_t2_dual_split_t4_residual():
    assert set(GBPJPY_FIXTURE_VECTORS) >= {"t1", "t2", "t4"}
    t1 = score_gbpjpy_fixture("t1")
    t2 = score_gbpjpy_fixture("t2")
    t4 = score_gbpjpy_fixture("t4")
    t3 = score_gbpjpy_fixture("t3")
    assert t1["verdict"] == "pass"
    assert t1["fail_reason"] is None
    assert t1["matches_lock"] is True
    assert t1["residual"] == 0.08
    assert t1["residual"] <= RESID_CAP
    assert t1["london_expand_class"] == "pass"
    assert t1["never_refuse"] is True
    assert t1["never_apply_size"] is True
    assert t2["verdict"] == "fail"
    assert t2["fail_reason"] == "dual_split"
    assert t2["matches_lock"] is True
    assert t2["dual_leg_agree"] is False
    assert t4["verdict"] == "fail"
    assert t4["fail_reason"] == "residual"
    assert t4["matches_lock"] is True
    assert t4["residual"] == 0.22
    assert t4["residual"] > RESID_CAP
    assert t3["fail_reason"] == "residual"
    assert GBPJPY_FIXTURE_VECTORS["t3"]["alias_of"] == "t4"
    empty = {"spine_id": None, "sources": [], "events": [], "n_files": 0}
    for vec_id, expect_reason in (("t1", None), ("t2", "dual_split"), ("t4", "residual")):
        scored = score_gbpjpy_fixture(vec_id)
        state = assemble_aplus_state(
            "gbpjpy_london_session_sweep",
            as_of_utc=datetime(2026, 1, 15, 7, 30, tzinfo=timezone.utc),
            side="long",
            geometry=_geo(185.20, 184.40, 186.80, 0.80),
            spines=empty,
            pack3_values=values_from_gbpjpy_fixture(vec_id),
        )
        cross = state["pack3_fields"]["fields"]["corr.gbpjpy_risk_cross"]
        expand = state["pack3_fields"]["fields"]["london_open_eur_gbp_expand"]
        assert cross["assembled"] is True
        assert cross["invented"] is False
        assert cross["value"]["resid_cap"] == 0.15
        assert expand["value"]["in_window"] is True
        assert expand["value"]["class"] == "pass"
        assert scored["fail_reason"] == expect_reason
        composed = compose_shadow(state, ticket=f"aplus-gj-{vec_id}")
        assert composed["apply_this_row"] is False
        assert composed["live_size_tilt"] == 1.0
        assert composed["pack3_fields"]["never_refuse"] is True
        assert all(g["refuse"] is False for g in composed["fluid"]["gates"].values())


def test_pack3_named_corr_and_boj_timing_never_refuse():
    empty = {"spine_id": None, "sources": [], "events": [], "n_files": 0}
    state = assemble_aplus_state(
        "xau_london_ob_retest",
        as_of_utc=datetime(2026, 1, 15, 7, 30, tzinfo=timezone.utc),
        side="short",
        geometry=_geo(),
        spines=empty,
        peer_state={"corr.xau_vs_eur_proxy_usd": {"value": "against", "source": "symbol_state_v0"}},
        pack3_values={"corr.xau_vs_eur_proxy_usd": "against"},
    )
    fields = state["pack3_fields"]["fields"]
    assert fields["corr.xau_vs_eur_proxy_usd"]["assembled"] is True
    assert fields["corr.xau_vs_eur_proxy_usd"]["value"] == "against"
    assert fields["corr.xau_vs_eur_proxy_usd"]["invented"] is False
    composed = compose_shadow(state, ticket="aplus-pack3-xau")
    assert composed["apply_this_row"] is False
    assert composed["live_size_tilt"] == 1.0
    assert composed["pack3_fields"]["never_refuse"] is True
    assert all(g["refuse"] is False for g in composed["fluid"]["gates"].values())
    boj = assemble_pack3_fields(
        symbol="USDJPY",
        time_utc=datetime(2026, 1, 15, 7, 30, tzinfo=timezone.utc),
        news={
            "spine_empty": False,
            "events": [
                {
                    "event": "BOJ Outlook Report",
                    "currency": "JPY",
                    "impact": "HIGH",
                    "minutes_from_as_of": 8,
                }
            ],
            "high_in_f5_window": True,
        },
    )
    assert boj["fields"]["macro.boj_guidance_window"]["assembled"] is True
    assert boj["fields"]["macro.boj_guidance_window"]["value"] is True
    assert boj["fields"]["macro.boj_guidance_window"]["minutes_from_as_of"] == 8
    assert boj["fields"]["macro.boj_guidance_window"]["never_refuse"] is True
    empty_boj = assemble_pack3_fields(
        symbol="USDJPY",
        time_utc=datetime(2026, 1, 15, 7, 30, tzinfo=timezone.utc),
        news={"spine_empty": True, "events": []},
    )
    assert empty_boj["fields"]["macro.boj_guidance_window"]["assembled"] is False
    assert empty_boj["invented"] is False


def test_pack3_never_apply_and_does_not_add_gates():
    row = score_aplus_shadow(
        "gbpjpy_london_session_sweep",
        as_of_utc=datetime(2026, 1, 15, 7, 30, tzinfo=timezone.utc),
        side="long",
        geometry=_geo(185.20, 184.40, 186.80, 0.80),
        ticket="aplus-pack3-shadow",
        spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
        pack3_values=values_from_gbpjpy_fixture("t1"),
    )
    assert row["compose"]["fluid"]["n"] == 48
    assert row["compose"]["apply_this_row"] is False
    assert row["compose"]["pack3_fields"]["n"] == 7
    assert row["compose"]["pack3_fields"]["invented"] is False
    assert row["compose"]["pack3_fields"]["never_refuse"] is True
    assert row["compose"]["live_size_tilt"] == 1.0
    assert all(g["refuse"] is False for g in row["compose"]["fluid"]["gates"].values())
    shape = assert_inventory_shape()
    assert shape["n_fluid"] == 48
    assert shape["n_envelope"] == 8


def test_pack4_sleeve_attach_map_gbpjpy_first_others_stub():
    assert set(SLEEVE_ATTACH_MAP) >= set(CATALOG)
    gj = SLEEVE_ATTACH_MAP[SETUP_GBPJPY]
    assert gj["implemented"] is True
    assert gj["choice"] == CHOICE_ID
    assert gj["symbol"] == "GBPJPY"
    assert tuple(gj["conjuncts"]) == CONJUNCTS
    assert set(gj["boj_block_buckets"]) == set(BOJ_BLOCK)
    assert gj["never_admit"] is True
    assert gj["state_paths"]["edge"] == "PACK 4"
    assert gj["state_paths"]["pack4"] == "pack4_fields"
    assert gj["state_paths"]["aplus"] == "aplus.pack4_fields"
    assert gj["state_paths"]["choice"] == f"pack4_fields.fields.{CHOICE_ID}"
    for setup_id in (
        "xau_london_ob_retest",
        "eurusd_ny_ob_retest",
        "usdjpy_tokyo_asia_fade",
        "xau_dsp_shakeout",
    ):
        row = SLEEVE_ATTACH_MAP[setup_id]
        assert row["implemented"] is False
        assert row["status"] == "not_applicable"
        assert row["choice"] is None
        assert row["never_admit"] is True


def test_pack4_choice_is_not_admit_and_maps_existing_inputs_only():
    rows = pack4_gate_map()
    assert [r["field"] for r in rows] == list(PACK4_FIELD_IDS)
    assert PACK4_FIELD_IDS == (CHOICE_ID,)
    mapped = assert_pack4_maps_existing_families()
    assert mapped["ok"] is True, mapped["bad"]
    assert mapped["never_admit"] is True
    for row in rows:
        assert row["kind"] == "choice"
        assert row["never_admit"] is True
        assert row["never_refuse"] is True
        assert row["never_apply_size"] is True
        assert row["edge"] == "PACK 4"
        assert "admit" not in row["gate_questions"]
        assert set(row["never_write_gate_ids"]) == {"FLUID-ADM-007", "UB-AUTH-010"}
        assert set(row["criteria"]) == {CHOICE_READY, CHOICE_NOT_READY, CHOICE_UNASSEMBLED}
        assert set(row["criteria"]).isdisjoint(ADMIT_ANSWERS)
        for gid in row["gate_ids"]:
            gate = lookup(gid)
            assert gate is not None, gid
            assert gate["family"] in {"admit", "size", "news_window"}
            assert not str(gid).startswith("FLUID-PLC")
            assert gid not in {"FLUID-ADM-007", "UB-AUTH-010"}


def test_pack4_encodes_pack3_fixtures_t1_ready_t2_dual_t4_residual():
    t1 = score_gbpjpy_aplus_ready("t1")
    t2 = score_gbpjpy_aplus_ready("t2")
    t4 = score_gbpjpy_aplus_ready("t4")
    t3 = score_gbpjpy_aplus_ready("t3")
    assert t1["choice"] == CHOICE_READY
    assert t1["fail_reason"] is None
    assert t1["fail_conjunct"] is None
    assert t1["matches_lock"] is True
    assert t1["boj_bucket"] == "none"
    assert t1["never_admit"] is True
    assert all(t1["conjuncts"].values())
    assert t1["conjuncts"]["session_ok"] is True
    assert t1["conjuncts"]["cross.identity_ok"] is True
    assert t1["conjuncts"]["agree"] is True
    assert t1["conjuncts"]["dual_same"] is True
    assert t1["conjuncts"]["boj_clear"] is True
    assert t2["choice"] == CHOICE_NOT_READY
    assert t2["fail_reason"] == "dual_split"
    assert t2["fail_conjunct"] == "dual_same"
    assert t2["matches_lock"] is True
    assert t2["conjuncts"]["dual_same"] is False
    assert t4["choice"] == CHOICE_NOT_READY
    assert t4["fail_reason"] == "residual"
    assert t4["fail_conjunct"] == "cross.identity_ok"
    assert t4["matches_lock"] is True
    assert t4["conjuncts"]["cross.identity_ok"] is False
    assert t4["conjuncts"]["dual_same"] is True
    assert t3["fail_reason"] == "residual"
    assert t3["choice"] == CHOICE_NOT_READY
    empty = {"spine_id": None, "sources": [], "events": [], "n_files": 0}
    for vec_id, expect_choice, expect_reason in (
        ("t1", CHOICE_READY, None),
        ("t2", CHOICE_NOT_READY, "dual_split"),
        ("t4", CHOICE_NOT_READY, "residual"),
    ):
        state = assemble_aplus_state(
            SETUP_GBPJPY,
            as_of_utc=datetime(2026, 1, 15, 7, 30, tzinfo=timezone.utc),
            side="long",
            geometry=_geo(185.20, 184.40, 186.80, 0.80),
            spines=empty,
            pack3_values=values_from_gbpjpy_fixture(vec_id),
            pack4_values=pack4_values_from_gbpjpy_fixture(vec_id),
        )
        pack4 = state["pack4_fields"]
        assert pack4["schema"] == "gtos.judgment.aplus_pack4_fields.v0"
        assert pack4["edge"] == "PACK 4"
        assert pack4["state_path"] == "pack4_fields"
        assert pack4["never_admit"] is True
        assert pack4["never_refuse"] is True
        assert state["aplus"]["pack4_fields"]["n"] == 1
        choice = pack4["fields"][CHOICE_ID]
        assert choice["assembled"] is True
        assert choice["choice"] == expect_choice
        assert choice["fail_reason"] == expect_reason
        assert choice["never_admit"] is True
        assert set(choice["never_write_gate_ids"]) == {"FLUID-ADM-007", "UB-AUTH-010"}
        composed = compose_shadow(state, ticket=f"aplus-pack4-{vec_id}")
        assert composed["apply_this_row"] is False
        assert composed["live_size_tilt"] == 1.0
        assert composed["pack4_fields"]["never_admit"] is True
        assert composed["pack4_fields"]["choice"] == expect_choice
        assert composed["pack4_fields"]["edge"] == "PACK 4"
        adm = composed["fluid"]["gates"]["FLUID-ADM-007"]
        auth = composed["fluid"]["gates"]["UB-AUTH-010"]
        assert adm["source"] == "flow_and_cost"
        assert adm["shadow"] in {"admit", "abstain", "hard_refuse"}
        assert adm["shadow"] != expect_choice
        assert adm["refuse"] is False
        assert auth["shadow"] in {"admit", "abstain", "hard_refuse"}
        assert auth["refuse"] is False
        assert all(g["refuse"] is False for g in composed["fluid"]["gates"].values())


def test_pack4_empty_spine_unassembled_and_boj_block_buckets():
    empty = {"spine_id": None, "sources": [], "events": [], "n_files": 0}
    live = assemble_aplus_state(
        SETUP_GBPJPY,
        as_of_utc=datetime(2026, 1, 15, 7, 30, tzinfo=timezone.utc),
        side="long",
        geometry=_geo(185.20, 184.40, 186.80, 0.80),
        spines=empty,
        pack3_values=values_from_gbpjpy_fixture("t1"),
    )
    choice = live["pack4_fields"]["fields"][CHOICE_ID]
    assert choice["assembled"] is False
    assert choice["choice"] == CHOICE_UNASSEMBLED
    assert choice["boj_bucket"] == "unassembled"
    assert choice["conjuncts"]["session_ok"] is True
    assert choice["conjuncts"]["boj_clear"] is None
    assert "pack4_fields.choice.gbpjpy_aplus_ready" in live["completeness"]["missing_fields"]
    assert live["pack4_fields"]["invented"] is False
    blocked = assemble_pack4_fields(
        symbol="GBPJPY",
        setup_id=SETUP_GBPJPY,
        pack3=live["pack3_fields"],
        pack4_values={"boj_bucket": "print"},
        session_named="london",
    )
    assert blocked["fields"][CHOICE_ID]["choice"] == CHOICE_NOT_READY
    assert blocked["fields"][CHOICE_ID]["fail_reason"] == "boj_bucket"
    assert blocked["fields"][CHOICE_ID]["fail_conjunct"] == "boj_clear"
    guidance = assemble_pack4_fields(
        symbol="GBPJPY",
        setup_id=SETUP_GBPJPY,
        pack3=live["pack3_fields"],
        pack4_values={"boj_bucket": "guidance_live"},
        session_named="london",
    )
    assert guidance["fields"][CHOICE_ID]["choice"] == CHOICE_NOT_READY
    away = assemble_pack4_fields(
        symbol="GBPJPY",
        setup_id=SETUP_GBPJPY,
        pack3=live["pack3_fields"],
        pack4_values={"boj_bucket": "guidance_away"},
        session_named="london",
    )
    assert away["fields"][CHOICE_ID]["choice"] == CHOICE_READY
    xau = assemble_aplus_state(
        "xau_london_ob_retest",
        as_of_utc=datetime(2026, 1, 15, 7, 30, tzinfo=timezone.utc),
        side="short",
        geometry=_geo(),
        spines=empty,
    )
    xf = xau["pack4_fields"]["fields"][CHOICE_ID]
    assert xf["applies"] is False
    assert xf["assembled"] is False
    assert xf["source"] == "not_applicable"
    assert xau["pack4_fields"]["attach"]["status"] == "not_applicable"


def test_pack4_never_apply_and_does_not_add_gates_or_write_admit():
    encoded = encode_gbpjpy_fixture("t1")
    assert encoded["choice"] == CHOICE_READY
    assert encoded["edge"] == "PACK 4"
    row = score_aplus_shadow(
        SETUP_GBPJPY,
        as_of_utc=datetime(2026, 1, 15, 7, 30, tzinfo=timezone.utc),
        side="long",
        geometry=_geo(185.20, 184.40, 186.80, 0.80),
        ticket="aplus-pack4-shadow",
        spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
        pack3_values=values_from_gbpjpy_fixture("t1"),
        pack4_values=pack4_values_from_gbpjpy_fixture("t1"),
    )
    assert row["compose"]["fluid"]["n"] == 48
    assert row["compose"]["apply_this_row"] is False
    assert row["compose"]["pack4_fields"]["n"] == 1
    assert row["compose"]["pack4_fields"]["invented"] is False
    assert row["compose"]["pack4_fields"]["never_admit"] is True
    assert row["compose"]["pack4_fields"]["choice"] == CHOICE_READY
    assert row["compose"]["live_size_tilt"] == 1.0
    assert row["compose"]["fluid"]["gates"]["FLUID-ADM-007"]["source"] == "flow_and_cost"
    assert row["compose"]["fluid"]["gates"]["FLUID-ADM-007"]["shadow"] != CHOICE_READY
    assert all(g["refuse"] is False for g in row["compose"]["fluid"]["gates"].values())
    shape = assert_inventory_shape()
    assert shape["n_fluid"] == 48
    assert shape["n_envelope"] == 8
    assert lookup("ENV-US30")["class"] == "envelope"


def test_scout_attach_map_resolves_chair_names():
    pin = assert_scout_attach_authority()
    assert pin["ok"] is True, pin["bad"]
    assert pin["never_admit"] is True
    assert pin["resid_cap"] == 0.15
    assert SCOUT_ATTACH_NAMES == (
        PACK5_CHOICE_ID,
        "gbpjpy_dual_leg",
        "tokyo_event",
        "london_fit",
    )
    assert SCOUT_PACKET_PATH.is_file()
    dual = resolve_attach_name("gbpjpy_dual_leg")
    assert dual["equiv"] == "gate.cross_stack_gbpjpy"
    assert dual["resid_cap"] == 0.15
    assert dual["shadow_only"] is True
    assert dual["never_refuse"] is True
    tokyo = resolve_attach_name("tokyo_event")
    assert tokyo["split"] == ("gate.asia_jpy_act_ok", "gate.event_boj_window")
    london = resolve_attach_name("london_fit")
    assert london["split"] == ("sleeve.london_expand_eur_gbp", "gate.session_overlap_ok")
    choice = resolve_attach_name(PACK5_CHOICE_ID)
    assert choice["kind"] == "choice"
    assert choice["never_admit"] is True
    resolved = resolve_gbpjpy_attach(pack2=None, pack5_choice="a_plus")
    assert resolved["never_admit"] is True
    assert resolved["names"][PACK5_CHOICE_ID]["assembled"] is True
    assert resolved["names"]["gbpjpy_dual_leg"]["assembled"] is False
    assert resolved["names"]["tokyo_event"]["assembled"] is False
    assert resolved["names"]["london_fit"]["assembled"] is False
    encoded = encode_gbpjpy_a_plus("t1")
    attach = encoded["pack5"]["attach_resolved"]
    assert attach["shadow_only"] is True
    assert attach["never_admit"] is True
    assert set(attach["names"]) == set(SCOUT_ATTACH_NAMES)
    composed = compose_shadow(
        assemble_aplus_state(
            SETUP_GBPJPY,
            as_of_utc=datetime(2026, 1, 15, 7, 30, tzinfo=timezone.utc),
            side="long",
            geometry=_geo(185.20, 184.40, 186.80, 0.80),
            spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
            pack3_values=values_from_gbpjpy_fixture("t1"),
            pack4_values=pack4_values_from_gbpjpy_fixture("t1"),
            pack5_values=pack5_values_from_gbpjpy_fixture("t1"),
        ),
        ticket="aplus-scout-attach-t1",
    )
    assert composed["pack5_fields"]["attach_names"] == list(attach["names"])
    assert composed["apply_this_row"] is False
    assert composed["fluid"]["gates"]["FLUID-ADM-007"]["source"] == "flow_and_cost"


def test_scout_packet_falls_back_when_workspace_drop_missing(monkeypatch, tmp_path):
    """VPS / sibling trees do not have /workspace/gtos/_scout_packets."""
    import src.judgment.pack5_fields as pack5

    monkeypatch.setattr(pack5, "_SCOUT_ABS_DROP", tmp_path / "missing" / "SLEEVE_ATTACH_MAP.md")
    resolved = resolve_scout_packet_path()
    assert resolved.is_file()
    assert resolved.name == "SLEEVE_ATTACH_MAP.md"
    assert resolved != tmp_path / "missing" / "SLEEVE_ATTACH_MAP.md"
    text = resolved.read_text(encoding="utf-8")
    assert "gbpjpy_dual_leg" in text
    assert "sleeve.gbpjpy_a_plus_ready" in text


def test_scout_tier1_wires_and_chair_attach_aliases():
    assert SCOUT_TIER1_WIRES["sess.ldn_ny_overlap_vol"] == ("FLUID-ADM-004", "FLUID-SIZ-003")
    assert SCOUT_TIER1_WIRES["sess.london_open_eur_gbp_expand"] == (
        "FLUID-ADM-004",
        "FLUID-ADM-005",
        "FLUID-SIZ-003",
    )
    assert SCOUT_TIER1_WIRES["sess.ny_cash_open_us30"] == ("FLUID-ADM-004", "FLUID-SIZ-003")
    assert SCOUT_TIER1_WIRES["corr.eur_gbp_usd_co_move"] == ("FLUID-ADM-002",)
    assert SCOUT_TIER1_WIRES["corr.xau_vs_eur_proxy_usd"] == ()
    assert SCOUT_TIER1_WIRES["corr.gbpjpy_risk_cross"] == ("FLUID-ADM-002",)
    assert SCOUT_TIER1_WIRES["macro.boj_guidance_window"] == (
        "FLUID-NWS-002",
        "FLUID-NWS-004",
        "FLUID-SIZ-006",
    )
    assert ATTACH_ALIASES["gbpjpy_dual_leg"]["equiv"] == "gate.cross_stack_gbpjpy"
    assert ATTACH_ALIASES["gbpjpy_dual_leg"]["resid_cap"] == 0.15
    assert ATTACH_ALIASES["tokyo_event"]["split"] == (
        "gate.asia_jpy_act_ok",
        "gate.event_boj_window",
    )
    assert ATTACH_ALIASES["london_fit"]["split"] == (
        "sleeve.london_expand_eur_gbp",
        "gate.session_overlap_ok",
    )
    assert ATTACH_ALIASES["corr.xau_vs_eur_proxy_usd"]["wire"] is None
    gj = CHAIR_SLEEVE_ATTACH_MAP[SETUP_GBPJPY]
    assert gj["choice"] == PACK5_CHOICE_ID
    assert gj["never_admit"] is True
    assert gj["pack4_choice"] == CHOICE_ID
    mapped = assert_pack5_maps_existing_families()
    assert mapped["ok"] is True
    observe = assert_scout_tier1_observe_only()
    assert observe["ok"] is True, observe["bad"]
    assert observe["never_refuse"] is True
    assert observe["never_admit"] is True
    assert observe["no_wire"] == ("corr.xau_vs_eur_proxy_usd",)
    assert SCOUT_TIER1_ALIASES["sess.london_open_eur_gbp_expand"] == "london_open_eur_gbp_expand"
    assert SCOUT_TIER1_ALIASES["sess.ny_cash_open_us30"] == "ny_cash_open_us30"
    assert SCOUT_TIER1_ALIASES["corr.xau_vs_eur_proxy_usd"] == "usd_proxy_vs_xau"
    for row in pack5_gate_map():
        assert "admit" not in row["gate_questions"]
        assert "FLUID-ADM-007" not in row["gate_ids"]
        assert "UB-AUTH-010" not in row["gate_ids"]
        assert set(row["criteria"]).isdisjoint(ADMIT_ANSWERS)
        assert row["never_admit"] is True


def test_pack5_t3_is_not_pack3_t4_alias():
    pin = assert_pack5_t3_not_pack3_alias()
    assert pin["ok"] is True, pin
    assert PACK5_CHOICE_ANSWERS == {"a_plus", "almost", "blocked", "null_state"}
    assert set(PACK5_FIXTURE_VECTORS) == {"t1", "t2", "t3", "t4"}
    p3_t3 = GBPJPY_FIXTURE_VECTORS["t3"]
    p5_t3 = PACK5_FIXTURE_VECTORS["t3"]
    assert p3_t3["alias_of"] == "t4"
    assert p3_t3["residual"] == GBPJPY_FIXTURE_VECTORS["t4"]["residual"] == 0.22
    assert p5_t3["residual"] == 0.10
    assert p5_t3["london_expand"] == 1.25
    assert p5_t3["tone"] == "neutral"
    assert p5_t3["expect"] == PACK5_A_PLUS
    assert score_gbpjpy_a_plus_ready("t3")["choice"] == PACK5_A_PLUS
    assert score_gbpjpy_fixture("t3")["fail_reason"] == "residual"


def test_pack5_encodes_t1_t3_a_plus_t2_dual_t4_residual():
    expect = {
        "t1": (PACK5_A_PLUS, None),
        "t3": (PACK5_A_PLUS, None),
        "t2": (PACK5_BLOCKED, "dual_split"),
        "t4": (PACK5_BLOCKED, "residual"),
    }
    t3_values = {
        "id": "t3",
        "time_utc": "2026-01-15T07:30:00Z",
        "dual_leg_agree": True,
        "residual": 0.10,
        "london_expand": 1.25,
        "corr.gbpjpy_risk_cross": "agree",
        "corr.eur_gbp_usd_co_move": True,
    }
    for vec_id, (choice, reason) in expect.items():
        scored = score_gbpjpy_a_plus_ready(vec_id)
        assert scored["matches_lock"] is True
        assert scored["choice"] == choice
        assert scored["fail_reason"] == reason
        assert scored["never_admit"] is True
        encoded = encode_gbpjpy_a_plus(vec_id)
        assert encoded["choice"] == choice
        assert encoded["edge"] == "PACK 5"
        pack3_values = values_from_gbpjpy_fixture(t3_values if vec_id == "t3" else vec_id)
        pack4_values = (
            {"boj_bucket": "none"}
            if vec_id == "t3"
            else pack4_values_from_gbpjpy_fixture(vec_id)
        )
        state = assemble_aplus_state(
            SETUP_GBPJPY,
            as_of_utc=datetime(2026, 1, 15, 7, 30, tzinfo=timezone.utc),
            side="long",
            geometry=_geo(185.20, 184.40, 186.80, 0.80),
            spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
            pack3_values=pack3_values,
            pack4_values=pack4_values,
            pack5_values=pack5_values_from_gbpjpy_fixture(vec_id),
        )
        pack5 = state["pack5_fields"]
        assert pack5["schema"] == "gtos.judgment.aplus_pack5_fields.v0"
        assert pack5["edge"] == "PACK 5"
        assert pack5["never_admit"] is True
        assert pack5["fields"][PACK5_CHOICE_ID]["choice"] == choice
        assert pack5["fields"][PACK5_CHOICE_ID]["fail_reason"] == reason
        composed = compose_shadow(state, ticket=f"aplus-pack5-{vec_id}")
        assert composed["pack5_fields"]["choice"] == choice
        assert composed["pack5_fields"]["never_admit"] is True
        assert composed["fluid"]["gates"]["FLUID-ADM-007"]["source"] == "flow_and_cost"
        assert composed["fluid"]["gates"]["FLUID-ADM-007"]["shadow"] != choice
        assert composed["apply_this_row"] is False
        if vec_id != "t3":
            assert state["pack4_fields"]["choice"] in {CHOICE_READY, CHOICE_NOT_READY}


def test_pack5_tone_risk_off_blocked_and_unassembled_almost():
    blocked = encode_gbpjpy_a_plus(
        {
            "id": "t1",
            "time_utc": "2026-01-15T07:30:00Z",
            "dual_leg_agree": True,
            "gbpusd_side": "long",
            "usdjpy_side": "long",
            "gbpjpy_side": "long",
            "residual": 0.08,
            "london_expand": 1.40,
            "corr.gbpjpy_risk_cross": "agree",
            "corr.eur_gbp_usd_co_move": True,
            "tone": "risk_off",
        }
    )
    assert blocked["choice"] == PACK5_BLOCKED
    assert blocked["fail_reason"] == "tone_risk_off"
    live = assemble_aplus_state(
        SETUP_GBPJPY,
        as_of_utc=datetime(2026, 1, 15, 7, 30, tzinfo=timezone.utc),
        side="long",
        geometry=_geo(185.20, 184.40, 186.80, 0.80),
        spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
        pack3_values=values_from_gbpjpy_fixture("t1"),
        pack4_values=pack4_values_from_gbpjpy_fixture("t1"),
    )
    choice = live["pack5_fields"]["fields"][PACK5_CHOICE_ID]
    assert choice["choice"] == PACK5_ALMOST
    assert choice["tone"] == "unassembled"
    assert choice["never_admit"] is True


def test_pack6_s0_through_s6_revised_mute_and_n_in_honesty():
    mapped = assert_pack6_maps_existing_families()
    assert mapped["ok"] is True
    assert mapped["n_in"] == 3
    for row in pack6_gate_map():
        assert "admit" not in row["gate_questions"]
        assert "FLUID-ADM-007" not in row["gate_ids"]
        assert "UB-AUTH-010" not in row["gate_ids"]
        assert set(row["criteria"]).isdisjoint(ADMIT_ANSWERS)
    in_n = []
    for vec_id, vec in XAU_SHAKEOUT_FIXTURES.items():
        scored = score_xau_dsp_shakeout(vec_id)
        assert scored["matches_lock"] is True, (vec_id, scored)
        assert scored["choice"] == vec["expect"]
        assert scored["fail_reason"] == vec["expect_reason"]
        assert scored["n_in"] == N_IN
        assert scored["honesty"] == "prove_seed_n_in_3"
        assert scored["never_admit"] is True
        if vec["in_n"]:
            in_n.append(vec_id)
    assert in_n == ["S0", "S1", "S2"]
    s0 = score_xau_dsp_shakeout("S0")
    assert s0["ticket"] == SEED_TICKET
    assert s0["ticket"] == 293611741
    assert s0["choice"] == PACK6_BLOCKED
    assert s0["fail_reason"] == "fill_in_boj_warsh_t90_t60"
    s4 = event_mute(fill_mins=10, event_class="other_high", fill_in_any_high=True)
    assert s4["mute"] is False
    assert s4["fill_in_any_high_alone_mutes"] is False
    assert score_xau_dsp_shakeout("S4")["choice"] == PACK6_A_PLUS
    assert score_xau_dsp_shakeout("S3")["choice"] == PACK6_NULL
    state = assemble_aplus_state(
        SETUP_XAU,
        as_of_utc=datetime(2026, 9, 18, 1, 45, 50, tzinfo=timezone.utc),
        side="long",
        geometry=_geo(4347.32, 4343.11, 4380.73, 4.21),
        spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
        pack6_values={"fixture": "S0"},
    )
    pack6 = state["pack6_fields"]
    assert pack6["schema"] == "gtos.judgment.aplus_pack6_fields.v0"
    assert pack6["edge"] == "PACK 6"
    assert pack6["n_in"] == 3
    assert pack6["honesty"] == "prove_seed_n_in_3"
    assert pack6["fields"][PACK6_CHOICE_ID]["choice"] == PACK6_BLOCKED
    composed = compose_shadow(state, ticket="aplus-pack6-s0")
    assert composed["pack6_fields"]["choice"] == PACK6_BLOCKED
    assert composed["pack6_fields"]["never_admit"] is True
    assert composed["pack6_fields"]["n_in"] == 3
    assert composed["fluid"]["gates"]["FLUID-ADM-007"]["source"] == "flow_and_cost"
    assert composed["apply_this_row"] is False
    assert composed["live_size_tilt"] == 1.0
    assert all(g["refuse"] is False for g in composed["fluid"]["gates"].values())
    shadow = score_aplus_shadow(
        SETUP_XAU,
        as_of_utc=datetime(2026, 9, 18, 1, 45, 50, tzinfo=timezone.utc),
        side="long",
        geometry=_geo(4347.32, 4343.11, 4380.73, 4.21),
        ticket="aplus-pack6-shadow",
        spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
        pack6_values={"fixture": "S0"},
    )
    assert shadow["compose"]["fluid"]["n"] == 48
    assert shadow["compose"]["apply_this_row"] is False
    assert shadow["compose"]["pack6_fields"]["choice"] == PACK6_BLOCKED
    shape = assert_inventory_shape()
    assert shape["n_fluid"] == 48
    assert shape["n_envelope"] == 8
    assert lookup("ENV-US30")["class"] == "envelope"
    assert "xau_dsp_shakeout" in CATALOG
    assert PACK5_FIELD_IDS == (PACK5_CHOICE_ID,)
    assert PACK5_NULL == "null_state"


def test_pack6_prove_seed_s0_s5_n_in_honesty():
    pin = assert_pack6_prove_seed()
    assert pin["ok"] is True, pin["bad"]
    assert pin["prove_seed_ids"] == ["S0", "S1", "S2", "S3", "S4", "S5"]
    assert pin["in_n"] == ["S0", "S1", "S2"]
    assert pin["n_in"] == 3
    assert pin["honesty"] == "prove_seed_n_in_3"
    assert pin["seed_ticket"] == 293611741
    assert pin["never_admit"] is True
    assert pin["hypothesis_mute"] == "boj∈{print,guidance_live} OR Warsh T±60"
    assert "S6" not in PROVE_SEED_IDS
    assert set(PROVE_SEED_FIXTURES) == set(PROVE_SEED_IDS)
    assert "S6" in XAU_SHAKEOUT_FIXTURES
    for vec_id in PROVE_SEED_IDS:
        scored = score_xau_dsp_shakeout(vec_id)
        assert scored["matches_lock"] is True, (vec_id, scored)
        assert scored["honesty"] == PACK6_HONESTY
        assert scored["never_admit"] is True
        assert scored["n_in"] == 3
    s0 = score_xau_dsp_shakeout("S0")
    assert s0["choice"] == PACK6_BLOCKED
    assert s0["fail_reason"] == "fill_in_boj_warsh_t90_t60"
    assert s0["ticket"] == 293611741
    assert s0["in_n"] is True
    assert hypothesis_mute(event_class="print")["mute"] is True
    assert hypothesis_mute(event_class="guidance_live")["mute"] is True
    assert hypothesis_mute(event_class="warsh", fill_mins=-15)["reason"] == "warsh_t60"
    assert event_mute(event_class="print")["reason"] == "boj_print_or_guidance_live"
    assert event_mute(event_class="guidance_live")["reason"] == "boj_print_or_guidance_live"
    assert event_mute(event_class="warsh", fill_mins=-15)["reason"] == "fill_in_boj_warsh_t90_t60"
    print_row = score_xau_dsp_shakeout(
        {
            "id": "print_no_mins",
            "structure_ok": True,
            "event_class": "print",
            "expect": PACK6_BLOCKED,
            "expect_reason": "boj_print_or_guidance_live",
        }
    )
    assert print_row["matches_lock"] is True
    assert print_row["choice"] == PACK6_BLOCKED
    state = assemble_aplus_state(
        SETUP_XAU,
        as_of_utc=datetime(2026, 9, 18, 1, 45, 50, tzinfo=timezone.utc),
        side="long",
        geometry=_geo(4347.32, 4343.11, 4380.73, 4.21),
        spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
        pack6_values={"fixture": "S0"},
    )
    assert state["pack6_fields"]["prove_seed_ids"] == list(PROVE_SEED_IDS)
    composed = compose_shadow(state, ticket="aplus-pack6-prove-seed")
    assert composed["pack6_fields"]["honesty"] == "prove_seed_n_in_3"
    assert composed["pack6_fields"]["n_in"] == 3
    assert composed["pack6_fields"]["never_admit"] is True
    assert composed["pack6_fields"]["choice"] == PACK6_BLOCKED
    assert composed["fluid"]["gates"]["FLUID-ADM-007"]["source"] == "flow_and_cost"
    assert composed["apply_this_row"] is False
    shape = assert_inventory_shape()
    assert shape["n_fluid"] == 48
    assert shape["n_envelope"] == 8


def test_pack6_revised_mute_s0_s6_fill_in_any_high_not_mute():
    pin = assert_pack6_revised_mute()
    assert pin["ok"] is True, pin["bad"]
    assert pin["revised_ids"] == ["S0", "S1", "S2", "S3", "S4", "S5", "S6"]
    assert pin["fill_in_any_high_alone_mutes"] is False
    assert pin["prefer_close"] is True
    assert pin["prove_seed"] is True
    assert pin["n_in"] == 3
    assert pin["never_admit"] is True
    assert pin["revised_mute"] == "close∈boj/warsh T±60 OR fill∈T−90..T+60"
    for vec_id in pin["revised_ids"]:
        scored = score_xau_dsp_shakeout(vec_id)
        assert scored["matches_lock"] is True, (vec_id, scored)
        assert scored["never_admit"] is True
    assert score_xau_dsp_shakeout("S0")["fail_reason"] == "fill_in_boj_warsh_t90_t60"
    assert score_xau_dsp_shakeout("S4")["choice"] == PACK6_A_PLUS
    assert score_xau_dsp_shakeout("S5")["fail_reason"] == "close_in_boj_warsh_t60"
    assert score_xau_dsp_shakeout("S6")["fail_reason"] == "fill_in_boj_warsh_t90_t60"
    alone = event_mute(fill_in_any_high=True)
    assert alone["mute"] is False
    assert alone["fill_in_any_high_alone_mutes"] is False
    prefer = event_mute(event_class="warsh", fill_mins=-15, close_mins=20)
    assert prefer["mute"] is True
    assert prefer["reason"] == "close_in_boj_warsh_t60"
    state = assemble_aplus_state(
        SETUP_XAU,
        as_of_utc=datetime(2026, 9, 18, 1, 45, 50, tzinfo=timezone.utc),
        side="long",
        geometry=_geo(4347.32, 4343.11, 4380.73, 4.21),
        spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
        pack6_values={"fixture": "S6"},
    )
    assert state["pack6_fields"]["revised_ids"] == pin["revised_ids"]
    assert state["pack6_fields"]["fields"][PACK6_CHOICE_ID]["choice"] == PACK6_BLOCKED
    composed = compose_shadow(state, ticket="aplus-pack6-s6")
    assert composed["pack6_fields"]["never_admit"] is True
    assert composed["pack6_fields"]["choice"] == PACK6_BLOCKED
    assert composed["fluid"]["gates"]["FLUID-ADM-007"]["source"] == "flow_and_cost"
    assert composed["apply_this_row"] is False


def test_edge_freeze_both_ready_choices_shadow_no_admit():
    pin = assert_edge_freeze()
    assert pin["ok"] is True, pin["bad"]
    assert pin["choices"] == (GBPJPY_READY, XAU_READY)
    assert pin["never_admit"] is True
    assert pin["n_in"] == 3
    assert {row["choice"] for row in READY_CHOICES} == {GBPJPY_READY, XAU_READY}
    assert PACK5_CHOICE_ID == GBPJPY_READY
    assert PACK6_CHOICE_ID == XAU_READY
    gbpjpy = score_gbpjpy_a_plus_ready("t1")
    xau = score_xau_dsp_shakeout("S0")
    assert gbpjpy["choice"] == PACK5_A_PLUS
    assert gbpjpy["never_admit"] is True
    assert xau["choice"] == PACK6_BLOCKED
    assert xau["never_admit"] is True
    assert xau["ticket"] == SEED_TICKET


def test_pack6_edge_freeze_utf8_docs_from_foreign_cwd(monkeypatch, tmp_path):
    """Windows VPS may invoke pytest off-repo-root; unicode needles need utf-8."""
    monkeypatch.chdir(tmp_path)
    seed = assert_pack6_prove_seed()
    assert seed["ok"] is True, seed["bad"]
    mute = assert_pack6_revised_mute()
    assert mute["ok"] is True, mute["bad"]
    freeze = assert_edge_freeze()
    assert freeze["ok"] is True, freeze["bad"]
