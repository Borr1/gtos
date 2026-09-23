"""Named CA size wire — owner NAMED APPLY 2026-09-18 (size_tilt only)."""

from pathlib import Path

from src.judgment.apply_size import apply_named_tilts
from src.judgment.bars import admit_challenge_peer_csv
from src.judgment.ca_size import (
    CONSUMED_LABELS,
    CORR_WITH_USD_TILT,
    EVT_HIGH_TILT,
    IDX_WITH_US30_TILT,
    LIQ_THIN_TILT,
    OCC_CROWDED_TILT,
    RSK_ON_TILT,
    USD_ADVERSE_TILT,
    WIRE_ID,
    ca_cross_asset_size_tilt,
    score_ca_size,
)
from src.judgment.ca_size_prove import prove_ca_size_rows, run_prove
from src.judgment.compose import compose_shadow
from src.judgment.cross_asset_prove import run_prove as run_ca_label_prove
from src.judgment.process_lock import (
    APPLIED_WIRES,
    CA_TILT_MAX,
    CA_TILT_MIN,
    WIRE_CA_SIZE,
    WIRE_CANDIDATES,
    live_multiplier,
    wire_apply_open,
)


def _world(
    *,
    occ=None,
    liq=None,
    ev=None,
    usd=None,
    gold_usd=None,
    risk=None,
    gold_idx=None,
):
    occ_named = occ
    return {
        "usd_proxy": {"named": usd or "unassembled", "source": "fx_majors_equal_weight" if usd else "unassembled"},
        "gold_vs_usd": {"named": gold_usd or "unassembled"},
        "gold_vs_index": {"named": gold_idx or "unassembled"},
        "risk_on": {"named": risk or "unassembled"},
        "session_liquidity": (
            {"named": "overlap_london_ny", "overlap": True, "thin": False, "source": "clock_utc_hour"}
            if liq == 2
            else {"named": "london", "overlap": False, "thin": False, "source": "clock_utc_hour"}
            if liq == 1
            else {"named": "asia", "overlap": False, "thin": True, "source": "clock_utc_hour"}
            if liq == 0
            else {"named": "unknown", "overlap": None, "thin": None, "source": "unassembled"}
        ),
        "event_join": ev
        if ev is not None
        else {
            "usd_high_in_window": None,
            "gbp_high_in_window": None,
            "jpy_high_in_window": None,
            "eur_high_in_window": None,
            "spine_empty": True,
            "source": "news_spine_empty",
        },
        "occupancy_book": {
            "n_clusters_open": occ_named,
            "occupancy_source": "challenge_deals" if occ_named is not None else "unassembled",
        },
    }


def test_wire_id_is_named_new_fire_now_in_applied():
    assert WIRE_ID == "ca_cross_asset_size_tilt" == WIRE_CA_SIZE
    assert WIRE_CA_SIZE in APPLIED_WIRES
    assert WIRE_CA_SIZE not in WIRE_CANDIDATES
    assert set(CONSUMED_LABELS) == {
        "CA-OCC-001",
        "CA-LIQ-001",
        "CA-EVT-001",
        "CA-USD-001",
        "CA-CORR-001",
        "CA-RSK-001",
        "CA-IDX-001",
    }


def test_apply_open_like_other_named_size_wires(monkeypatch):
    monkeypatch.setenv("GTOS_JEV_APPLY_LIVE", "1")
    monkeypatch.setenv("GTOS_JEV_W_NAMED", WIRE_CA_SIZE)
    assert wire_apply_open(WIRE_CA_SIZE) is True
    assert wire_apply_open(WIRE_CA_SIZE, ticket="123") is True
    assert wire_apply_open(WIRE_CA_SIZE, ticket="293332188") is False
    assert live_multiplier(0.70, wire_id=WIRE_CA_SIZE) == 0.70
    assert live_multiplier(0.70, wire_id=WIRE_CA_SIZE, ticket="293332188") == 1.0


def test_missing_world_is_one_not_zero():
    assert ca_cross_asset_size_tilt(None) == 1.0
    assert ca_cross_asset_size_tilt({}) == 1.0
    scored = score_ca_size({})
    assert scored["shadow"] == 1.0
    assert scored["live"] == 1.0
    assert scored["apply"] is False
    assert scored["decidable"] is False
    assert scored["invented_news_protocol"] is False


def test_empty_spine_does_not_invent_high():
    world = _world(liq=1, occ=1, ev={
        "usd_high_in_window": None,
        "gbp_high_in_window": None,
        "jpy_high_in_window": None,
        "eur_high_in_window": None,
        "spine_empty": True,
        "source": "news_spine_empty",
    })
    scored = score_ca_size(world)
    assert scored["components"]["event_join"]["assembled"] is False
    assert scored["components"]["event_join"]["tilt"] == 1.0
    assert scored["shadow"] == 1.0


def test_high_in_window_is_veto_class_not_refuse():
    world = _world(
        liq=1,
        occ=1,
        ev={
            "usd_high_in_window": True,
            "gbp_high_in_window": False,
            "jpy_high_in_window": False,
            "eur_high_in_window": False,
            "spine_empty": False,
            "source": "news_spine",
        },
    )
    scored = score_ca_size(world)
    assert scored["shadow"] == EVT_HIGH_TILT
    assert scored["cannot_refuse"] is True
    assert scored["apply"] is False


def test_conservative_component_defaults():
    crowded = score_ca_size(_world(occ=2, liq=1))
    assert crowded["shadow"] == OCC_CROWDED_TILT
    thin = score_ca_size(_world(occ=1, liq=0))
    assert thin["shadow"] == LIQ_THIN_TILT
    usd_long = score_ca_size(_world(occ=1, liq=1, usd="usd_up"), side="long")
    assert usd_long["shadow"] == USD_ADVERSE_TILT
    usd_short_up = score_ca_size(_world(occ=1, liq=1, usd="usd_up"), side="short")
    assert usd_short_up["shadow"] == 1.0
    usd_short_down = score_ca_size(_world(occ=1, liq=1, usd="usd_down"), side="short")
    assert usd_short_down["shadow"] == USD_ADVERSE_TILT
    usd_no_side = score_ca_size(_world(occ=1, liq=1, usd="usd_up"))
    assert usd_no_side["shadow"] == 1.0
    with_usd = score_ca_size(_world(occ=1, liq=1, gold_usd="gold_with_usd"))
    assert with_usd["shadow"] == CORR_WITH_USD_TILT
    against_usd = score_ca_size(_world(occ=1, liq=1, gold_usd="gold_against_usd"))
    assert against_usd["shadow"] == 1.0
    risk_on = score_ca_size(_world(occ=1, liq=1, risk="risk_on"))
    assert risk_on["shadow"] == RSK_ON_TILT
    risk_off = score_ca_size(_world(occ=1, liq=1, risk="risk_off"))
    assert risk_off["shadow"] == 1.0
    with_idx = score_ca_size(_world(occ=1, liq=1, gold_idx="gold_with_us30"))
    assert with_idx["shadow"] == IDX_WITH_US30_TILT


def test_product_clamps_to_veto_class():
    world = _world(
        occ=2,
        liq=0,
        usd="usd_up",
        gold_usd="gold_with_usd",
        risk="risk_on",
        gold_idx="gold_with_us30",
        ev={
            "usd_high_in_window": True,
            "gbp_high_in_window": False,
            "jpy_high_in_window": False,
            "eur_high_in_window": False,
            "spine_empty": False,
            "source": "news_spine",
        },
    )
    tilt = ca_cross_asset_size_tilt(world, side="long")
    assert tilt == CA_TILT_MIN
    assert CA_TILT_MIN <= tilt <= CA_TILT_MAX


def test_compose_live_follows_ca_combined_is_flow_x_cost_x_ca():
    state = {
        "identity": {"side": "long", "symbol": "XAUUSD", "family_class": "study"},
        "completeness": {"state_sufficient_for_live": True},
        "news": {"spine_empty": False},
        "cost": {"spread_r_of_stop": 0.10},
        "timeframes": {"h4": {"trend": 1}},
        "world": _world(occ=2, liq=0, gold_idx="gold_with_us30"),
    }
    row = compose_shadow(state)
    assert row["shadow_ca_size_tilt"] < 1.0
    assert row["live_ca_size_tilt"] == row["shadow_ca_size_tilt"]
    assert row["ca_cross_asset_size_tilt_apply"] is True
    assert row["physical_size_stays_flow_x_cost_x_ca"] is True
    ca = row["wires"][WIRE_CA_SIZE]
    assert ca["apply"] is True
    assert ca["live"] == row["live_ca_size_tilt"]
    assert ca["cannot_refuse"] is True
    assert ca["range"] == [CA_TILT_MIN, CA_TILT_MAX]
    assert row["combined_live_tilt"] == round(
        row["live_size_tilt"] * row["live_cost_tilt"] * row["live_ca_size_tilt"], 4
    )
    held = compose_shadow(state, ticket="293332188")
    assert held["live_ca_size_tilt"] == 1.0
    assert held["wires"][WIRE_CA_SIZE]["apply"] is False
    assert held["combined_live_tilt"] == 1.0


def test_house_block_and_absent_world_do_not_move():
    blocked = compose_shadow(
        {
            "identity": {"side": "long", "family_class": "house_hard_off"},
            "completeness": {"state_sufficient_for_live": True},
            "news": {},
            "cost": {},
            "world": _world(occ=2, liq=0),
        }
    )
    assert blocked["shadow_ca_size_tilt"] == 1.0
    assert blocked["live_ca_size_tilt"] == 1.0
    bare = compose_shadow(
        {
            "identity": {"side": "long", "family_class": "study"},
            "completeness": {"state_sufficient_for_live": True},
            "news": {},
            "cost": {},
        }
    )
    assert bare["shadow_ca_size_tilt"] == 1.0
    assert WIRE_CA_SIZE in bare["wires"]
    assert blocked["wires"][WIRE_CA_SIZE]["apply"] is False


def test_apply_named_tilts_includes_ca_on_xau_ignores_leave_orig_forge(monkeypatch):
    monkeypatch.setenv("GTOS_JEV_APPLY_LIVE", "1")
    state = {
        "identity": {"side": "short", "symbol": "XAUUSD", "family_class": "study"},
        "completeness": {"state_sufficient_for_live": True, "cost": True},
        "news": {"spine_empty": False},
        "cost": {"spread_r_of_stop": 0.10},
        "timeframes": {"h4": {"trend": 1}},
        "world": _world(occ=2, liq=0),
    }
    row = compose_shadow(state)
    named = apply_named_tilts(row)
    assert named["ca_apply"] is True
    assert named["ca_live"] == row["live_ca_size_tilt"]
    assert named["combined"] == round(named["flow"] * named["cost"] * named["ca"], 4)
    assert named[WIRE_CA_SIZE]["apply"] is True
    forged = compose_shadow(state, ticket="293332188")
    forged["live_ca_size_tilt"] = 0.70
    forged["wires"][WIRE_CA_SIZE]["apply"] = True
    held = apply_named_tilts(forged, ticket="293332188")
    assert held["ca_apply"] is False
    assert held["ca_live"] == 1.0
    assert held["combined"] == 1.0


def test_prove_synthetic_moved_distinct_and_live_lock():
    rows = []
    for i in range(24):
        world = _world(occ=2 if i < 8 else 1, liq=0 if i >= 16 else 1)
        rows.append(
            {
                "ticket": str(i),
                "side": "long",
                "symbol": "XAUUSD",
                "world": world,
                "state": {
                    "identity": {"side": "long", "symbol": "XAUUSD", "family_class": "study"},
                    "completeness": {"state_sufficient_for_live": True},
                    "news": {"spine_empty": False},
                    "cost": {},
                    "occupancy": {},
                    "timeframes": {},
                },
            }
        )
    receipt = prove_ca_size_rows(rows)
    assert receipt["verdict"] == "PROVED_SHADOW"
    assert receipt["apply"] is False
    assert receipt["apply_claimed"] == 0
    assert receipt["owner_named"] is True
    assert receipt["n_decidable"] >= 20
    assert receipt["n_moved"] >= 5
    assert receipt["n_distinct"] >= 2
    assert receipt["n_invented_high"] == 0


def test_challenge_harness_and_label_apply_stay_false():
    labels = run_ca_label_prove(write=False)
    assert labels.get("apply_any") is False
    assert all(t["apply"] is False for t in labels["targets"])
    payload = run_prove(write=False)
    assert payload["wire_candidate"] == WIRE_CA_SIZE
    assert payload["apply"] is False
    assert payload["apply_claimed"] == 0
    assert payload["wire_apply"] is True
    assert payload["owner_named"] is True
    assert payload["named_new_fire"] is True
    assert payload["not_silent_ca_apply_flip"] is True
    assert payload["ca_label_apply_any"] is False
    assert payload["never_place"] is True
    assert payload["invented_news_protocol"] is False
    assert payload["physical_size"]["stays_flow_x_cost_x_ca"] is True
    assert payload["physical_size"]["apply_claimed"] == 0
    assert payload["envelope_walls_stay_integers"] is True
    target = payload["target"]
    assert target["apply"] is False
    assert target["n_invented_high"] == 0
    assert target["verdict"] in {"PROVED_SHADOW", "NOT_PROVED"}
    if target["verdict"] == "PROVED_SHADOW":
        assert target["n_decidable"] >= 20
        assert target["n_moved"] >= 5
        assert target["n_distinct"] >= 2
        assert target["vals"]
    else:
        assert target["reasons"]
    # Same Challenge admit as the CA label pack.
    peer = (payload.get("survey") or {}).get("peer_admit") or {}
    wanted = (payload.get("survey") or {}).get("wanted_challenge_m15") or {}
    for sym in ("EURUSD", "GBPUSD", "USDJPY", "US30"):
        if wanted.get(sym):
            assert (peer.get(sym) or {}).get("ok") is True
    # Same admit as PR #13: April historical is not Challenge-true.
    april = Path(__file__).resolve().parents[2] / "exports" / "multi_instrument" / "EURUSD_M15.csv"
    if april.is_file():
        admit = admit_challenge_peer_csv(april)
        assert admit["ok"] is False
        assert "april" in str(admit.get("reason") or "").lower() or "time_utc" in str(admit.get("reason") or "")
