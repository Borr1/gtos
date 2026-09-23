"""test_ultimate_book_live_package.py — tests for the standalone deployable package.

Covers: registry/config integrity, confidence-weighted correlated-risk-unit sizing, fail-closed
governor (daily / max-DD / circuit-breaker / invalid-state), leak-free outcome labeling via
geometry_lib, and the replay-vs-module CONFIDENCE PARITY check against the locked integrator.

Run:
  ROOT=/Users/borr/Documents/gtos/repo/ai-trading-agent
  ROUTE=$ROOT/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10
  PYTHONPATH=$ROOT:$ROUTE python3 -m pytest $ROUTE/test_ultimate_book_live_package.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import ultimate_book_live_package as P
from ultimate_book_live_package import (
    SLEEVE_REGISTRY, CLUSTER_OF_SLEEVE, ALLOCATION_PROFILES, DEFAULT_PROFILE,
    GovernorState, GovernorLimits, DEFAULT_LIMITS, TradeIntent,
    size_correlated_units, evaluate_governor, admit_and_size, winsorize_R,
    confidence_for, describe_book,
    CLEAN3_REGISTRY, CLEAN3_VOL_SCALE, CLEAN3_DEFAULT_PROFILE, CONFLUENCE_OVERLAYS,
    OVERLAY_SIZEUP_MAX, SESSION_ACTIVE_HOURS, LEADER_IMPULSE_NONE,
    effective_registry, overlay_sizeup_for,
    CLEAN4_REGISTRY, CLEAN4_VOL_SCALE, CLEAN4_DEFAULT_PROFILE,
    STRESS_DERISK_OVERLAYS, DEFAULT_STRESS_OVERLAY, StressDeriskState, stress_derisk_multiplier,
    LADDER_STEPS, COLOSS_NEG_FRAC, COLOSS_SIZE_MULT, STRESS_DERISK_MIN_MULT,
    VP_ACCEPTANCE_TAG, VP_ACCEPTANCE_BASE,
    kelly_lite_conviction_multiplier, KELLY_LITE_BINS, KELLY_LITE_BINS_HALF,
)


# ---------------------------------------------------------------- registry integrity ----------
def test_registry_has_8_sleeves_and_locked_confidence():
    assert len(SLEEVE_REGISTRY) == 8
    want = {
        "metals_core": 1.00, "crypto": 0.85, "energy_agri": 0.80, "metals_softband": 0.50,
        "metals_ob_micro": 0.30, "fx_jpy_ny": 0.15, "idxrev": 0.15, "fx_jpy": 0.15,
    }
    for name, conf in want.items():
        assert SLEEVE_REGISTRY[name].confidence == conf, name


def test_nothing_deleted_falsified_sleeves_kept_at_breadth_size():
    # data_depth FALSIFIED fx_jpy + idxrev -> demoted to 0.15, NEVER zero (build doctrine).
    for n in ("fx_jpy", "idxrev"):
        assert SLEEVE_REGISTRY[n].confidence == 0.15
        assert SLEEVE_REGISTRY[n].status == "breadth_falsified"
    assert all(s.confidence > 0 for s in SLEEVE_REGISTRY.values())


def test_clusters_cover_four_asset_classes():
    classes = set(CLUSTER_OF_SLEEVE.values())
    assert {"metals", "crypto", "energy", "index", "jpy"} == classes  # 5 cluster ids, 4+ real classes


def test_allocation_default_is_balanced_0p75():
    assert DEFAULT_PROFILE == "balanced_0p75"
    p = ALLOCATION_PROFILES["balanced_0p75"]
    assert p.risk_per_unit_A == 0.0075 and p.risk_per_unit_B == 0.0075


def test_describe_book_is_json_serializable():
    import json
    d = describe_book()
    json.dumps(d, default=str)  # must not raise
    assert d["sleeve_count"] == 8


# ---------------------------------------------------------------- winsorize ----------
def test_winsorize_bounds():
    assert winsorize_R(10.0) == 5.0
    assert winsorize_R(-9.0) == -1.3
    assert winsorize_R(2.3) == 2.3


# ---------------------------------------------------------------- correlated-risk-unit sizing --
def _intent(sleeve, sym, day="2026-01-05", d=1, stop=1.0, intra=1.0, ll_impulse=None, decision_hour=None):
    return TradeIntent(sleeve=sleeve, symbol=sym, direction=d, decision_day=day,
                       stop_dist=stop, target_dist=2.0, intra_size=intra,
                       ll_impulse=ll_impulse, decision_hour=decision_hour)


def test_same_class_same_day_collapses_to_one_unit():
    # two metals sleeves firing the same day -> ONE correlated unit, risk split across trades.
    intents = [_intent("metals_core", "XAUUSD"), _intent("metals_softband", "XAGUSD", intra=1.0)]
    units = size_correlated_units(intents, base_risk_per_unit=0.0075)
    metals_units = [u for u in units if u.cluster == "metals"]
    assert len(metals_units) == 1
    u = metals_units[0]
    assert u.n_trades == 2
    # unit confidence = max sleeve conf among members (metals_core 1.00)
    assert abs(u.confidence - 1.00) < 1e-9
    # unit worst-case risk = base * conf; per-trade = unit/n
    assert abs(u.unit_risk_pct - 0.0075 * 1.00) < 1e-9
    assert abs(u.risk_pct_per_trade - 0.0075 / 2) < 1e-9


def test_cross_class_same_day_are_independent_units():
    intents = [_intent("metals_core", "XAUUSD"), _intent("crypto", "BTCUSD"),
               _intent("energy_agri", "USOIL_cash")]
    units = size_correlated_units(intents, base_risk_per_unit=0.0075)
    sized = [u for u in units if u.sized]
    assert len(sized) == 3  # three independent clusters -> three units
    clusters = sorted(u.cluster for u in sized)
    assert clusters == ["crypto", "energy", "metals"]


def test_confidence_scales_unit_risk():
    # crypto conf 0.85 -> unit risk = base * 0.85
    units = size_correlated_units([_intent("crypto", "BTCUSD")], base_risk_per_unit=0.01)
    u = [u for u in units if u.sized][0]
    assert abs(u.unit_risk_pct - 0.01 * 0.85) < 1e-9


def test_intra_size_ramp_applies():
    # softband intra ramp scales confidence
    units = size_correlated_units([_intent("metals_softband", "XAUUSD", intra=0.5)],
                                  base_risk_per_unit=0.0075)
    u = [u for u in units if u.sized][0]
    assert abs(u.confidence - 0.50 * 0.5) < 1e-9


def test_breadth_sleeve_sizes_small_not_zero():
    units = size_correlated_units([_intent("idxrev", "SPX500")], base_risk_per_unit=0.0075)
    u = [u for u in units if u.cluster == "index"][0]
    assert u.sized
    assert u.unit_risk_pct > 0
    assert abs(u.unit_risk_pct - 0.0075 * 0.15) < 1e-9


# ---------------------------------------------------------------- fail-closed sizing ----------
def test_unknown_sleeve_fails_closed():
    units = size_correlated_units([_intent("not_a_sleeve", "XXX")], base_risk_per_unit=0.0075)
    assert all(not u.sized for u in units)
    assert any("unknown_sleeve" in u.reason for u in units)


def test_nonpositive_stop_fails_closed_for_whole_unit():
    intents = [_intent("metals_core", "XAUUSD", stop=1.0), _intent("metals_softband", "XAGUSD", stop=0.0)]
    units = size_correlated_units(intents, base_risk_per_unit=0.0075)
    metals = [u for u in units if u.cluster == "metals"][0]
    assert not metals.sized and "nonpositive_stop" in metals.reason


def test_bad_direction_fails_closed():
    units = size_correlated_units([_intent("crypto", "BTCUSD", d=0)], base_risk_per_unit=0.0075)
    assert all(not u.sized for u in units)


# ---------------------------------------------------------------- governor ----------
def _state(**kw):
    base = dict(equity=100000.0, high_water=100000.0, realized_today_pct=0.0,
                open_risk_pct=0.0, operator_circuit_breaker=False)
    base.update(kw)
    return GovernorState(**base)


def test_governor_allows_clean_state():
    g = evaluate_governor(_state())
    assert g.allow_new_entries and g.size_cap_multiplier == 1.0


def test_circuit_breaker_blocks_all():
    g = evaluate_governor(_state(operator_circuit_breaker=True))
    assert not g.allow_new_entries and g.reason == "circuit_breaker_open"


def test_soft_daily_stop_blocks_new_entries():
    g = evaluate_governor(_state(realized_today_pct=-0.03))
    assert not g.allow_new_entries and g.reason == "soft_daily_stop_reached"
    # just above the soft stop still allowed
    g2 = evaluate_governor(_state(realized_today_pct=-0.0299))
    assert g2.allow_new_entries


def test_max_dd_limit_blocks():
    g = evaluate_governor(_state(equity=90000.0, high_water=100000.0))
    assert not g.allow_new_entries and g.reason == "max_dd_limit_reached"


def test_max_dd_derisk_band_shrinks_size():
    # dd between 7% and 10% -> size cap multiplier strictly between 0 and 1
    g = evaluate_governor(_state(equity=91500.0, high_water=100000.0))  # dd = 8.5%
    assert g.allow_new_entries
    assert 0.0 < g.size_cap_multiplier < 1.0
    assert g.reason == "derisking_into_maxdd_wall"


def test_gross_risk_cap_exhausted_blocks():
    g = evaluate_governor(_state(open_risk_pct=0.04))
    assert not g.allow_new_entries and g.reason == "gross_risk_cap_exhausted"


def test_nan_state_fails_closed():
    g = evaluate_governor(_state(realized_today_pct=float("nan")))
    assert not g.allow_new_entries and "fail_closed" in g.reason


def test_high_water_below_equity_fails_closed():
    g = evaluate_governor(_state(equity=110000.0, high_water=100000.0))
    assert not g.allow_new_entries and "fail_closed" in g.reason


def test_nonpositive_equity_fails_closed():
    g = evaluate_governor(_state(equity=0.0))
    assert not g.allow_new_entries and "fail_closed" in g.reason


# ---------------------------------------------------------------- top-level admit_and_size ----
def test_admit_and_size_blocks_when_governor_blocks():
    out = admit_and_size([_intent("metals_core", "XAUUSD")], _state(operator_circuit_breaker=True))
    assert out["ok"] and not out["new_entries_allowed"] and out["units"] == []


def test_admit_and_size_sizes_when_clean():
    out = admit_and_size([_intent("metals_core", "XAUUSD"), _intent("crypto", "BTCUSD")], _state())
    assert out["new_entries_allowed"]
    sized = [u for u in out["units"] if u["sized"]]
    assert len(sized) == 2


def test_admit_and_size_enforces_gross_cap():
    # build many independent cross-class units so cumulative unit risk exceeds the 4% gross cap.
    # metals 1.00, crypto 0.85, energy 0.80, jpy 0.15, index 0.15 at base 0.0075 ->
    # cumulative = 0.0075*(1.00+0.85+0.80+0.15+0.15)=0.022 < 0.04, so push base high to force cap.
    intents = [_intent("metals_core", "XAUUSD"), _intent("crypto", "BTCUSD"),
               _intent("energy_agri", "USOIL_cash"), _intent("idxrev", "SPX500"),
               _intent("fx_jpy_ny", "USDJPY")]
    out = admit_and_size(intents, _state(), profile="staggered_1p00_0p50", account="A")
    # account A here = 1.00% base; cumulative conf-wtd = 0.01*(1.00+0.85+0.80+0.15+0.15)=0.0295 < 0.04 ok
    # tighten the cap to force exhaustion
    tight = GovernorLimits(gross_open_risk_cap_pct=0.015)
    out2 = admit_and_size(intents, _state(), profile="staggered_1p00_0p50", account="A", limits=tight)
    blocked = [u for u in out2["units"] if not u["sized"]]
    assert any("gross_risk_cap_would_exceed" in u["reason"] for u in blocked)


def test_unknown_profile_returns_error():
    out = admit_and_size([_intent("metals_core", "XAUUSD")], _state(), profile="does_not_exist")
    assert not out["ok"] and "unknown_profile" in out["reason"]


# ---------------------------------------------------------------- leak-free labeling ----------
def test_label_intent_R_matches_geometry_simulate():
    from geometry_lib import simulate, Bar
    # synthetic uptrend bars; long with stop 1.0, target 2.0 should win ~+2R (net cost).
    bars = [Bar(100, 101, 99.5, 100.5, 0)]
    px = 100.5
    for _ in range(20):
        px += 0.6
        bars.append(Bar(px - 0.3, px + 0.5, px - 0.5, px, 0))
    it = TradeIntent("crypto", "BTCUSD", 1, "2026-01-01", stop_dist=1.0, target_dist=2.0)
    r_mod = P.label_intent_R(bars, 0, it, cost=0.0, maxbars=80)
    r_raw = winsorize_R(simulate(bars, 0, 1, stop_dist=1.0, target_dist=2.0, maxbars=80, cost=0.0))
    assert abs(r_mod - r_raw) < 1e-12


def test_label_intent_R_is_winsorized():
    from geometry_lib import Bar
    # huge favorable move -> raw R would exceed 5; winsorized to 5.
    bars = [Bar(100, 100, 100, 100, 0)]
    px = 100.0
    for _ in range(30):
        px += 5.0
        bars.append(Bar(px - 1, px + 1, px - 1, px, 0))
    it = TradeIntent("crypto", "BTCUSD", 1, "2026-01-01", stop_dist=1.0, target_dist=100.0)
    r = P.label_intent_R(bars, 0, it, cost=0.0, maxbars=80)
    assert r <= 5.0


# ---------------------------------------------------------------- REPLAY-vs-MODULE PARITY ------
def test_confidence_parity_with_integrator():
    """The module's locked SLEEVE_REGISTRY confidence MUST equal the integrator SLEEVE_CONF."""
    res = P.assert_confidence_parity()
    assert res["parity_ok"], res["mismatches"]


def test_module_cluster_map_matches_integrator_intent():
    # the integrator groups by sleeve name; the module's cluster map is the corr-unit grouping.
    # every integrator sleeve must be present in the module registry (no sleeve dropped).
    import INTEG_portfolio_build_w2 as W2
    for name in W2.SLEEVE_CONF:
        assert name in SLEEVE_REGISTRY, f"integrator sleeve {name} missing from module"


# ============================================================================================
# WAVE-5 clean_3 ADDITIVE SLEEVES + CONFLUENCE OVERLAYS (default-off deploy upgrade)
# ============================================================================================
# ---------------------------------------------------------------- clean_3 registry ------------
def test_clean3_registry_has_three_sleeves_locked_conf():
    want = {"sub_xvol_pullback": 0.45, "vp_euidx_pocgrav": 0.30, "sub_mid_dn_revert": 0.20}
    assert set(CLEAN3_REGISTRY) == set(want)
    for n, c in want.items():
        assert CLEAN3_REGISTRY[n].confidence == c, n


def test_clean3_is_default_off_unknown_to_base_book():
    # the locked default surface stays the 8-sleeve book; clean_3 sleeves are NOT in it.
    for n in CLEAN3_REGISTRY:
        assert n not in SLEEVE_REGISTRY
    assert describe_book()["sleeve_count"] == 8
    assert describe_book()["clean3"]["default_off"] is True
    assert describe_book()["clean3"]["deploy_sleeve_count"] == 11


def test_effective_registry_toggles_clean3():
    assert set(effective_registry(include_clean3=False)) == set(SLEEVE_REGISTRY)
    on = effective_registry(include_clean3=True)
    assert set(on) == set(SLEEVE_REGISTRY) | set(CLEAN3_REGISTRY)
    assert len(on) == 11


def test_clean3_sleeves_are_new_low_corr_clusters():
    # substrate + volprofile are NEW clusters (independent of the core's metals/crypto/energy/etc.)
    # and are NOT in the LOCKED-BOOK cluster map (default surface stays the 8-sleeve book).
    from ultimate_book_live_package import cluster_of
    for n in CLEAN3_REGISTRY:
        assert n not in CLUSTER_OF_SLEEVE
    assert cluster_of("sub_xvol_pullback") == "substrate"
    assert cluster_of("sub_mid_dn_revert") == "substrate"
    assert cluster_of("vp_euidx_pocgrav") == "volprofile"


def test_clean3_sleeve_unknown_when_off_sized_when_on():
    it = _intent("sub_xvol_pullback", "XAUUSD")
    off = size_correlated_units([it], base_risk_per_unit=0.0075, include_clean3=False)
    assert all(not u.sized for u in off)
    assert any("unknown_sleeve:sub_xvol_pullback" in u.reason for u in off)
    on = size_correlated_units([it], base_risk_per_unit=0.0075, include_clean3=True)
    u = [u for u in on if u.sized][0]
    assert u.cluster == "substrate"
    assert abs(u.unit_risk_pct - 0.0075 * 0.45) < 1e-9


def test_clean3_substrate_sleeves_collapse_to_one_unit():
    # sub_xvol_pullback + sub_mid_dn_revert same day -> ONE substrate correlated unit (max conf 0.45).
    intents = [_intent("sub_xvol_pullback", "XAUUSD"), _intent("sub_mid_dn_revert", "SPX500")]
    units = size_correlated_units(intents, base_risk_per_unit=0.0075, include_clean3=True)
    sub_units = [u for u in units if u.cluster == "substrate"]
    assert len(sub_units) == 1
    assert sub_units[0].n_trades == 2
    assert abs(sub_units[0].unit_risk_pct - 0.0075 * 0.45) < 1e-9


# ---------------------------------------------------------------- vol-matched rescale ----------
def test_clean3_vol_scale_matches_deploy_artifact():
    assert abs(CLEAN3_VOL_SCALE - 0.9481) < 1e-9


def test_clean3_balanced_profile_is_vol_matched_effective():
    # 0.75% nominal x vol_scale 0.948 = 0.711% effective on BOTH accounts.
    assert CLEAN3_DEFAULT_PROFILE == "clean3_balanced_eff0p71"
    p = ALLOCATION_PROFILES[CLEAN3_DEFAULT_PROFILE]
    eff = round(0.0075 * CLEAN3_VOL_SCALE, 6)
    assert p.risk_per_unit_A == eff and p.risk_per_unit_B == eff
    assert abs(eff - 0.007111) < 1e-6


def test_clean3_conservative_profile_present():
    p = ALLOCATION_PROFILES["clean3_conservative_eff0p47"]
    assert abs(p.risk_per_unit_A - round(0.0050 * CLEAN3_VOL_SCALE, 6)) < 1e-9


# ---------------------------------------------------------------- confluence overlays ----------
def test_overlay_off_by_default_no_sizeup():
    it = _intent("sub_xvol_pullback", "XAUUSD", ll_impulse="none", decision_hour=12)
    u = [u for u in size_correlated_units([it], base_risk_per_unit=0.0075, include_clean3=True,
                                          overlays=False) if u.sized][0]
    assert u.confidence == 0.45
    assert u.overlays_applied == ()


def test_leader_impulse_veto_sizes_up():
    # ll_impulse=none on a sub_xvol_pullback long -> 1.5x size-up -> conf 0.45*1.5=0.675.
    it = _intent("sub_xvol_pullback", "XAUUSD", ll_impulse=LEADER_IMPULSE_NONE)
    u = [u for u in size_correlated_units([it], base_risk_per_unit=0.0075, include_clean3=True,
                                          overlays=True) if u.sized][0]
    assert abs(u.confidence - 0.45 * 1.5) < 1e-9
    assert "leader_impulse_veto" in u.overlays_applied


def test_leader_impulse_present_does_not_size_up():
    # a leader IS impulsing (not 'none') -> the veto does NOT fire -> base conf only.
    it = _intent("sub_xvol_pullback", "XAUUSD", ll_impulse="up")
    u = [u for u in size_correlated_units([it], base_risk_per_unit=0.0075, include_clean3=True,
                                          overlays=True) if u.sized][0]
    assert u.confidence == 0.45 and u.overlays_applied == ()


def test_session_active_stack_sizes_up():
    for h in sorted(SESSION_ACTIVE_HOURS):
        it = _intent("sub_xvol_pullback", "XAUUSD", decision_hour=h)
        u = [u for u in size_correlated_units([it], base_risk_per_unit=0.0075, include_clean3=True,
                                              overlays=True) if u.sized][0]
        assert "session_active_stack" in u.overlays_applied
    # inactive hour (e.g. 0) -> no session size-up
    it0 = _intent("sub_xvol_pullback", "XAUUSD", decision_hour=0)
    u0 = [u for u in size_correlated_units([it0], base_risk_per_unit=0.0075, include_clean3=True,
                                           overlays=True) if u.sized][0]
    assert "session_active_stack" not in u0.overlays_applied


def test_overlays_compound_and_are_capped():
    # both overlays on xvol: 1.5 * 1.15 = 1.725 <= cap 1.75 -> conf 0.45*1.725.
    it = _intent("sub_xvol_pullback", "XAUUSD", ll_impulse=LEADER_IMPULSE_NONE, decision_hour=12)
    mult, names = overlay_sizeup_for(it, overlays=True)
    assert abs(mult - min(1.5 * 1.15, OVERLAY_SIZEUP_MAX)) < 1e-9
    assert set(names) == {"leader_impulse_veto", "session_active_stack"}
    u = [u for u in size_correlated_units([it], base_risk_per_unit=0.0075, include_clean3=True,
                                          overlays=True) if u.sized][0]
    assert abs(u.confidence - 0.45 * 1.725) < 1e-9


def test_overlay_only_applies_to_declared_base_sleeves():
    # leader_impulse_veto applies ONLY to sub_xvol_pullback, not to vp_euidx_pocgrav.
    it = _intent("vp_euidx_pocgrav", "GER40", ll_impulse=LEADER_IMPULSE_NONE)
    mult, names = overlay_sizeup_for(it, overlays=True)
    assert mult == 1.0 and names == ()
    # session_active_stack does NOT apply to a core sleeve either
    it2 = _intent("metals_core", "XAUUSD", decision_hour=12)
    m2, n2 = overlay_sizeup_for(it2, overlays=True)
    assert m2 == 1.0 and n2 == ()


def test_overlay_sizeup_never_below_one():
    it = _intent("sub_xvol_pullback", "XAUUSD")  # no overlay conditions present
    mult, names = overlay_sizeup_for(it, overlays=True)
    assert mult == 1.0 and names == ()


# ---------------------------------------------------------------- admit_and_size clean_3 -------
def test_admit_and_size_clean3_profile_uses_vol_matched_base():
    st = GovernorState(equity=100000.0, high_water=100000.0, realized_today_pct=0.0,
                       open_risk_pct=0.0, operator_circuit_breaker=False)
    out = admit_and_size([_intent("sub_xvol_pullback", "XAUUSD")], st,
                         profile=CLEAN3_DEFAULT_PROFILE, include_clean3=True, overlays=True)
    assert out["new_entries_allowed"] and out["include_clean3"] and out["overlays"]
    assert abs(out["base_risk_per_unit"] - round(0.0075 * CLEAN3_VOL_SCALE, 6)) < 1e-9
    u = [u for u in out["units"] if u["sized"]][0]
    assert abs(u["unit_risk_pct"] - round(0.0075 * CLEAN3_VOL_SCALE, 6) * 0.45) < 1e-8


def test_admit_and_size_clean3_off_rejects_new_sleeve():
    st = GovernorState(equity=100000.0, high_water=100000.0, realized_today_pct=0.0,
                       open_risk_pct=0.0, operator_circuit_breaker=False)
    out = admit_and_size([_intent("sub_xvol_pullback", "XAUUSD")], st)  # defaults: clean3 OFF
    assert out["new_entries_allowed"]
    assert all(not u["sized"] for u in out["units"])


# ---------------------------------------------------------------- clean_3 PARITY --------------
def test_clean3_parity_with_deploy_artifact():
    """Module CLEAN3_REGISTRY conf + vol_scale + 11-sleeve book == INTEG_W5_CLEAN3_DEPLOY.json."""
    res = P.assert_clean3_parity()
    assert res["parity_ok"], res


def test_describe_book_clean3_block_serializable():
    import json
    d = describe_book()
    json.dumps(d, default=str)  # must not raise
    assert d["schema_version"] == "ultimate_book_live_package_v3"
    assert set(d["clean3"]["sleeves"]) == set(CLEAN3_REGISTRY)
    assert set(d["clean3"]["overlays"]) == set(CONFLUENCE_OVERLAYS)


def test_import_safety_no_heavy_deps_on_module_load():
    # the deployable surface must import with ZERO heavy deps (no numpy/pandas/data loaders).
    # checked in a CLEAN subprocess so other tests' lazy parity imports don't pollute sys.modules.
    import subprocess, json as _json
    forbidden = ["numpy", "pandas", "substrate", "wave1_structure_setups_ict",
                 "INTEG_portfolio_build_w2", "INTEG_portfolio_build_w5", "KB5_fold_new_sleeves"]
    code = (
        "import sys; "
        f"sys.path.insert(0, {str(ROOT)!r}); sys.path.insert(0, {str(HERE)!r}); "
        "import ultimate_book_live_package; "
        f"f={forbidden!r}; "
        "import json; print(json.dumps([m for m in f if m in sys.modules]))"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    pulled = _json.loads(out.stdout.strip().splitlines()[-1])
    assert pulled == [], f"deployable module pulled heavy deps on import: {pulled}"


# ================================================================ WAVE-6 clean_4 + overlays ====
def test_clean4_registry_has_one_sleeve_locked_conf():
    assert len(CLEAN4_REGISTRY) == 1
    spec = CLEAN4_REGISTRY["session_leadlag_genuine"]
    assert spec.confidence == 0.15
    assert spec.asset_class == "leadlag"
    assert spec.status == "forward_only"


def test_clean4_is_default_off_unknown_to_base_book():
    # the W6 sleeve is unknown to both the locked book and the clean_3 book.
    assert "session_leadlag_genuine" not in SLEEVE_REGISTRY
    assert "session_leadlag_genuine" not in CLEAN3_REGISTRY
    reg_off = effective_registry()  # locked book
    assert "session_leadlag_genuine" not in reg_off
    reg_c3 = effective_registry(include_clean3=True)
    assert "session_leadlag_genuine" not in reg_c3


def test_clean4_implies_clean3_and_adds_sleeve():
    reg = effective_registry(include_clean4=True)
    # include_clean4 implies clean_3 (the W6 book is clean_3 + 1)
    assert "session_leadlag_genuine" in reg
    for n in CLEAN3_REGISTRY:
        assert n in reg
    assert len(reg) == len(SLEEVE_REGISTRY) + len(CLEAN3_REGISTRY) + 1


def test_clean4_sleeve_fail_closed_when_off_sized_when_on():
    it = TradeIntent("session_leadlag_genuine", "US30_cash", 1, "2026-01-02", 1.0)
    off = size_correlated_units([it], base_risk_per_unit=0.0074)
    assert off[0].sized is False and "unknown_sleeve" in off[0].reason
    on = size_correlated_units([it], base_risk_per_unit=0.0074, include_clean4=True)
    assert on[0].sized is True
    assert abs(on[0].confidence - 0.15) < 1e-9
    assert on[0].cluster == "leadlag"


def test_clean4_vol_scale_and_profiles_present():
    assert abs(CLEAN4_VOL_SCALE - 0.9873) < 1e-9
    assert CLEAN4_DEFAULT_PROFILE in ALLOCATION_PROFILES
    prof = ALLOCATION_PROFILES[CLEAN4_DEFAULT_PROFILE]
    # 0.75% nominal x vol_scale 0.9873 = effective ~0.74%
    assert abs(prof.risk_per_unit_A - round(0.0075 * CLEAN4_VOL_SCALE, 6)) < 1e-12
    assert ALLOCATION_PROFILES["clean4_conservative_eff0p49"].risk_per_unit_A < prof.risk_per_unit_A


def test_clean4_leadlag_is_independent_cluster():
    # the W6 sleeve must NOT collide with any core/clean_3 cluster (it is a new diversifier).
    core_clusters = {s.asset_class for s in SLEEVE_REGISTRY.values()}
    c3_clusters = {s.asset_class for s in CLEAN3_REGISTRY.values()}
    assert "leadlag" not in core_clusters
    assert "leadlag" not in c3_clusters
    assert P.cluster_of("session_leadlag_genuine") == "leadlag"


# ---- W6 VP-acceptance exit-honest refinement of sub_mid_dn_revert ----
def test_vp_acceptance_drops_non_above_va_intents():
    ints = [
        TradeIntent(VP_ACCEPTANCE_BASE, "XAUUSD", 1, "2026-01-02", 1.0, vp_loc="below_va"),
        TradeIntent(VP_ACCEPTANCE_BASE, "XAGUSD", 1, "2026-01-02", 1.0, vp_loc=VP_ACCEPTANCE_TAG),
    ]
    kept = size_correlated_units(ints, base_risk_per_unit=0.0074,
                                 include_clean3=True, vp_acceptance=True)
    # both share the substrate cluster/day -> one unit, but only the above_va member survives the cut
    assert sum(u.n_trades for u in kept) == 1


def test_vp_acceptance_off_keeps_all_intents():
    ints = [
        TradeIntent(VP_ACCEPTANCE_BASE, "XAUUSD", 1, "2026-01-02", 1.0, vp_loc="below_va"),
        TradeIntent(VP_ACCEPTANCE_BASE, "XAGUSD", 1, "2026-01-02", 1.0, vp_loc=VP_ACCEPTANCE_TAG),
    ]
    kept = size_correlated_units(ints, base_risk_per_unit=0.0074, include_clean3=True)
    assert sum(u.n_trades for u in kept) == 2


def test_vp_acceptance_does_not_touch_other_sleeves():
    # a non-base sleeve with a missing vp_loc must NOT be dropped by the VP-acceptance cut.
    it = TradeIntent("sub_xvol_pullback", "XAUUSD", 1, "2026-01-02", 1.0, vp_loc=None)
    kept = size_correlated_units([it], base_risk_per_unit=0.0074,
                                 include_clean3=True, vp_acceptance=True)
    assert sum(u.n_trades for u in kept) == 1


# ---- W6 reactive temporal stress de-risk overlay (TIER-1 ladder+coloss) ----
def test_stress_overlays_registered_with_tiers():
    assert DEFAULT_STRESS_OVERLAY == "reactive_ladder_coloss"
    assert STRESS_DERISK_OVERLAYS[DEFAULT_STRESS_OVERLAY].tier == 1
    assert STRESS_DERISK_OVERLAYS["full_stack_regime_ladder_coloss"].tier == 2
    # tier-1 (forward-clean) is the deployable default; tier-2 forward-positive but regime opt-in
    assert STRESS_DERISK_OVERLAYS[DEFAULT_STRESS_OVERLAY].fwd_delta_1pct > 0


def test_stress_derisk_clean_state_is_neutral():
    m, reasons = stress_derisk_multiplier(StressDeriskState(0, 0.0))
    assert m == 1.0 and reasons == ()


def test_stress_derisk_ladder_steps():
    # step1 -> 0.80, step2+ -> 0.60 (capped at the deepest ladder step)
    m1, _ = stress_derisk_multiplier(StressDeriskState(consecutive_loss_days=1, trailing_neg_frac=0.0))
    assert abs(m1 - LADDER_STEPS[1]) < 1e-9
    m3, _ = stress_derisk_multiplier(StressDeriskState(consecutive_loss_days=9, trailing_neg_frac=0.0))
    assert abs(m3 - LADDER_STEPS[-1]) < 1e-9


def test_stress_derisk_coloss_breaker_and_floor():
    # ladder step2 (0.60) x coloss (0.60) = 0.36 -> floored at STRESS_DERISK_MIN_MULT (0.60)
    m, reasons = stress_derisk_multiplier(
        StressDeriskState(consecutive_loss_days=2, trailing_neg_frac=COLOSS_NEG_FRAC + 0.05))
    assert m == STRESS_DERISK_MIN_MULT
    assert "coloss_breaker" in reasons and any(r.startswith("ladder") for r in reasons)


def test_stress_derisk_only_ever_shrinks_size():
    base = size_correlated_units([TradeIntent("crypto", "BTCUSD", 1, "2026-01-02", 1.0)],
                                 base_risk_per_unit=0.01)
    derisked = size_correlated_units(
        [TradeIntent("crypto", "BTCUSD", 1, "2026-01-02", 1.0)], base_risk_per_unit=0.01,
        stress_derisk=True, stress_state=StressDeriskState(consecutive_loss_days=1, trailing_neg_frac=0.0))
    assert derisked[0].unit_risk_pct < base[0].unit_risk_pct
    assert "ladder_step1" in derisked[0].overlays_applied


def test_stress_derisk_off_by_default():
    u = size_correlated_units([TradeIntent("crypto", "BTCUSD", 1, "2026-01-02", 1.0)],
                              base_risk_per_unit=0.01,
                              stress_state=StressDeriskState(consecutive_loss_days=3, trailing_neg_frac=0.9))
    # stress_derisk defaults OFF -> the state is ignored, full size
    assert abs(u[0].unit_risk_pct - 0.01 * 0.85) < 1e-9


def test_admit_and_size_clean4_path_end_to_end():
    st = GovernorState(equity=100000, high_water=100000, realized_today_pct=0.0, open_risk_pct=0.0)
    res = admit_and_size(
        [TradeIntent("session_leadlag_genuine", "US30_cash", 1, "2026-01-02", 1.0)],
        st, profile=CLEAN4_DEFAULT_PROFILE, include_clean4=True, overlays=True,
        vp_acceptance=True, stress_derisk=True,
        stress_state=StressDeriskState(consecutive_loss_days=0, trailing_neg_frac=0.0))
    assert res["ok"] and res["new_entries_allowed"]
    assert res["include_clean4"] and res["vp_acceptance"] and res["stress_derisk"]
    assert res["units"][0]["sized"] is True


def test_describe_book_clean4_block_serializable_and_router_disabled():
    import json
    d = describe_book()
    json.dumps(d, default=str)  # must not raise
    assert set(d["clean4"]["sleeves"]) == set(CLEAN4_REGISTRY)
    assert d["clean4"]["deploy_sleeve_count"] == 12
    assert set(d["clean4"]["stress_derisk_overlays"]) == set(STRESS_DERISK_OVERLAYS)
    assert d["clean4"]["confluence_router"]["wired"] is False
    assert d["clean4"]["vp_acceptance"]["tag"] == VP_ACCEPTANCE_TAG


# ---------------------------------------------------------------- KB7 Kelly-lite conviction sizing
def test_kelly_lite_default_off_is_neutral():
    # disabled -> always 1.0 regardless of conviction
    for na in (0, 1, 2, 3, 4, 7, 20):
        assert kelly_lite_conviction_multiplier(na) == 1.0
        assert kelly_lite_conviction_multiplier(na, enabled=False) == 1.0


def test_kelly_lite_handset_bins_monotone():
    # enabled -> trim marginal single-edge day, size up multi-edge agreement (matches deployed bins)
    assert kelly_lite_conviction_multiplier(1, enabled=True) == 0.85
    assert kelly_lite_conviction_multiplier(2, enabled=True) == 1.10
    assert kelly_lite_conviction_multiplier(3, enabled=True) == 1.10
    assert kelly_lite_conviction_multiplier(4, enabled=True) == 1.60
    assert kelly_lite_conviction_multiplier(7, enabled=True) == 1.60
    # monotone non-decreasing across buckets
    vals = [kelly_lite_conviction_multiplier(n, enabled=True) for n in (1, 2, 4)]
    assert vals == sorted(vals)


def test_kelly_lite_conservative_is_breach_safe_lower_top():
    # half-Kelly conservative bins: tamer top (breach-free), de-risks bottom more gently
    assert kelly_lite_conviction_multiplier(1, enabled=True, conservative=True) == 0.748
    assert kelly_lite_conviction_multiplier(4, enabled=True, conservative=True) == 1.241
    # conservative top is strictly below the hand-set top (the breach guard)
    assert (kelly_lite_conviction_multiplier(4, enabled=True, conservative=True)
            < kelly_lite_conviction_multiplier(4, enabled=True))


def test_kelly_lite_bins_constants_well_formed():
    for bins in (KELLY_LITE_BINS, KELLY_LITE_BINS_HALF):
        assert bins[0][0] == 1 and bins[-1][1] == 99  # cover 1..many
        mults = [m for _, _, m in bins]
        assert mults == sorted(mults)  # monotone
        assert max(mults) <= OVERLAY_SIZEUP_MAX  # never exceeds the governor cap


def test_kelly_lite_sizes_up_high_conviction_day():
    # 4 distinct cross-class sleeves firing today -> n_active=4 -> x1.6 on each unit's conf
    day = "2026-02-10"
    intents = [_intent("metals_core", "XAUUSD", day=day),
               _intent("crypto", "BTCUSD", day=day),
               _intent("energy_agri", "USOIL_cash", day=day),
               _intent("fx_jpy", "USDJPY", day=day)]
    base = size_correlated_units(intents, base_risk_per_unit=0.01)
    kel = size_correlated_units(intents, base_risk_per_unit=0.01, kelly_lite=True)
    metals_base = [u for u in base if u.cluster == "metals"][0]
    metals_kel = [u for u in kel if u.cluster == "metals"][0]
    # metals_core conf 1.0 -> base unit risk 0.01; kelly x1.6 -> 0.016
    assert abs(metals_base.unit_risk_pct - 0.01) < 1e-9
    assert abs(metals_kel.unit_risk_pct - 0.016) < 1e-9
    assert any("kelly_lite_na4" in r for r in metals_kel.overlays_applied)


def test_kelly_lite_trims_marginal_single_edge_day():
    # only one sleeve fires today -> n_active=1 -> x0.85 (trim the marginal day)
    intents = [_intent("crypto", "BTCUSD", day="2026-03-01")]
    base = size_correlated_units(intents, base_risk_per_unit=0.01)[0]
    kel = size_correlated_units(intents, base_risk_per_unit=0.01, kelly_lite=True)[0]
    # crypto conf 0.85: base 0.0085, kelly x0.85 -> 0.007225
    assert abs(base.unit_risk_pct - 0.0085) < 1e-9
    assert abs(kel.unit_risk_pct - 0.0085 * 0.85) < 1e-9


def test_kelly_lite_combined_with_overlay_capped_at_governor():
    # xvol-pullback long with leader-veto (x1.5) on a 4-edge day (kelly x1.6) -> combined 2.4 capped 1.75
    day = "2026-04-01"
    intents = [
        TradeIntent("sub_xvol_pullback", "EURUSD", 1, day, stop_dist=1.0, target_dist=2.0,
                    intra_size=1.0, ll_impulse=LEADER_IMPULSE_NONE),
        _intent("crypto", "BTCUSD", day=day),
        _intent("metals_core", "XAUUSD", day=day),
        _intent("energy_agri", "USOIL_cash", day=day),
    ]
    kel = size_correlated_units(intents, base_risk_per_unit=0.01, overlays=True,
                                include_clean3=True, kelly_lite=True)
    xvol = [u for u in kel if "sub_xvol_pullback" in u.sleeve_members][0]
    conf = confidence_for("sub_xvol_pullback", effective_registry(include_clean3=True))
    # combined size-up (1.5 * 1.6 = 2.4) MUST be capped at OVERLAY_SIZEUP_MAX (1.75)
    assert abs(xvol.unit_risk_pct - 0.01 * conf * OVERLAY_SIZEUP_MAX) < 1e-9


def test_kelly_lite_admit_and_size_threads_flag():
    intents = [_intent("crypto", "BTCUSD", day="2026-05-01")]
    state = GovernorState(equity=100000, high_water=100000, realized_today_pct=0.0, open_risk_pct=0.0)
    res = admit_and_size(intents, state, profile=CLEAN3_DEFAULT_PROFILE, include_clean3=True,
                         kelly_lite=True)
    assert res["ok"] and res["new_entries_allowed"]
    assert res["kelly_lite"] is True


def test_growth_optimal_profiles_present_and_aggressive():
    g = ALLOCATION_PROFILES["clean3_growth_eff1p42"]
    a = ALLOCATION_PROFILES["clean3_aggressive_eff1p66"]
    # growth profile is the 1.5% nominal vol-matched effective (~1.42%)
    assert abs(g.risk_per_unit_A - round(0.015 * CLEAN3_VOL_SCALE, 6)) < 1e-9
    assert abs(a.risk_per_unit_A - round(0.0175 * CLEAN3_VOL_SCALE, 6)) < 1e-9
    # strictly bigger than the conservative fear-drag deploy (0.71% eff)
    assert g.risk_per_unit_A > ALLOCATION_PROFILES["clean3_balanced_eff0p71"].risk_per_unit_A
    assert a.risk_per_unit_A > g.risk_per_unit_A


def test_firstcycle_profile_is_owner_dial_and_between_balanced_and_growth():
    # GO-LIVE owner dial: 1.25% nominal first cycle (between the old 0.71% balanced
    # and the 1.5% growth-optimal). Effective = 1.25% nominal x CLEAN3_VOL_SCALE.
    fc = ALLOCATION_PROFILES["clean3_firstcycle_eff1p18"]
    assert abs(fc.risk_per_unit_A - round(0.0125 * CLEAN3_VOL_SCALE, 6)) < 1e-9
    assert fc.risk_per_unit_A == fc.risk_per_unit_B  # 2-account balanced
    bal = ALLOCATION_PROFILES["clean3_balanced_eff0p71"]
    growth = ALLOCATION_PROFILES["clean3_growth_eff1p42"]
    assert bal.risk_per_unit_A < fc.risk_per_unit_A < growth.risk_per_unit_A
    # documented MC: near-certain unstressed pass at the first-cycle dial
    assert fc.base_p_both >= 0.99


def test_firstcycle_profile_usable_in_admit_and_size_default_off_surface():
    # The first-cycle profile drives clean_3 sizing without flipping any default-off
    # upgrade flag implicitly; governor still gates fail-closed.
    out = admit_and_size([_intent("metals_core", "XAUUSD")], _state(),
                         profile="clean3_firstcycle_eff1p18", include_clean3=True)
    assert out["ok"] is True and out["new_entries_allowed"]
    # circuit-breaker (operator kill-switch) still flattens it regardless of the dial
    out_cb = admit_and_size([_intent("metals_core", "XAUUSD")],
                            _state(operator_circuit_breaker=True),
                            profile="clean3_firstcycle_eff1p18", include_clean3=True)
    assert out_cb["ok"] and not out_cb["new_entries_allowed"] and out_cb["units"] == []


# ============================================================================================
# WAVE-7 (UNLEASH) FINALIZE: energy drop + per-symbol tick spread floor + sqrt-N pooling + W7 dials
# ============================================================================================
from ultimate_book_live_package import (  # noqa: E402
    ENERGY_DROPPED_SYMBOLS, W7_DROPPED_SYMBOLS, TICK_SPREAD_FLOOR_R,
    TICK_SPREAD_FLOOR_UNTRADEABLE_R, tick_spread_floor_for, is_tick_tradeable,
    pool_same_day_sleeve_R, filter_w7_dropped_symbols,
    CLEAN3_W7_FIRST_CYCLE_PROFILE, CLEAN3_W7_GROWTH_PROFILE, CLEAN3_W7_CEILING_PROFILE,
)
import math as _math  # noqa: E402


# ---- (3) HEATOIL_c + NATGAS_cash dropped from energy_agri (tick-true) ----
def test_energy_agri_drops_heatoil_and_natgas():
    syms = SLEEVE_REGISTRY["energy_agri"].symbols
    assert "HEATOIL_c" not in syms and "NATGAS_cash" not in syms
    # the liquid crude + agri legs are kept
    assert "USOIL_cash" in syms and "UKOIL_cash" in syms
    assert "CORN_c" in syms and "COTTON_c" in syms


def test_w7_dropped_symbols_is_canonical_alias():
    # the W7 alias points at the canonical energy-dropped set (no drift between the two names)
    assert W7_DROPPED_SYMBOLS is ENERGY_DROPPED_SYMBOLS
    assert ENERGY_DROPPED_SYMBOLS == frozenset({"HEATOIL_c", "NATGAS_cash"})


def test_filter_w7_dropped_symbols_removes_only_dropped():
    ints = [TradeIntent("energy_agri", "USOIL_cash", 1, "2026-01-02", 1.0),
            TradeIntent("energy_agri", "HEATOIL_c", 1, "2026-01-02", 1.0),
            TradeIntent("energy_agri", "NATGAS_cash", 1, "2026-01-02", 1.0)]
    kept, dropped = filter_w7_dropped_symbols(ints, enabled=True)
    assert [k.symbol for k in kept] == ["USOIL_cash"]
    assert set(dropped) == {"HEATOIL_c", "NATGAS_cash"}
    # disabled -> no-op
    kept2, dropped2 = filter_w7_dropped_symbols(ints, enabled=False)
    assert len(kept2) == 3 and dropped2 == ()


# ---- (3) per-symbol tick spread floor (replaces the per-class cost map) ----
def test_tick_spread_floor_liquid_below_illiquid():
    # liquid carriers floor well below the illiquid dropped legs (the per-class proxy failed both ways)
    assert tick_spread_floor_for("XAUUSD") < tick_spread_floor_for("XAGUSD")
    assert tick_spread_floor_for("BTCUSD") < tick_spread_floor_for("USDJPY")
    assert tick_spread_floor_for("USOIL_cash") < tick_spread_floor_for("NATGAS_cash")
    assert tick_spread_floor_for("NATGAS_cash") < tick_spread_floor_for("HEATOIL_c")
    # an unknown / no-feed symbol returns None (caller transfers the same-class floor)
    assert tick_spread_floor_for("GBPJPY") is None


def test_is_tick_tradeable_gates_dropped_and_illiquid():
    # liquid carriers tradeable
    for s in ("XAUUSD", "XAGUSD", "USOIL_cash", "UKOIL_cash", "BTCUSD", "USDJPY"):
        assert is_tick_tradeable(s), s
    # dropped illiquid legs NOT tradeable (explicit drop AND floor swamps the stop)
    for s in ("HEATOIL_c", "NATGAS_cash"):
        assert not is_tick_tradeable(s), s
    # a symbol whose measured floor exceeds the untradeable threshold is gated even if not dropped
    assert TICK_SPREAD_FLOOR_R["HEATOIL_c"] >= TICK_SPREAD_FLOOR_UNTRADEABLE_R
    # no-feed symbol (None floor) is tradeable (transfer floor applies)
    assert is_tick_tradeable("GBPJPY")


# ---- (2) sqrt-N within-sleeve same-day pooling ----
def test_pool_mean_vs_sqrtn_convention():
    rs = [0.5, 0.5, 0.5, 0.5]   # n=4
    # DEPLOYED mean pooling = sum/n
    assert abs(pool_same_day_sleeve_R(rs) - 0.5) < 1e-12
    # WAVE-7 sqrt-N pooling = sum/sqrt(n) = 2.0/2.0 = 1.0
    assert abs(pool_same_day_sleeve_R(rs, sqrt_n=True) - (sum(rs) / _math.sqrt(len(rs)))) < 1e-12
    assert abs(pool_same_day_sleeve_R(rs, sqrt_n=True) - 1.0) < 1e-12


def test_pool_edge_cases_single_and_empty():
    assert pool_same_day_sleeve_R([]) == 0.0
    assert pool_same_day_sleeve_R([], sqrt_n=True) == 0.0
    # single trade: both conventions == the trade R (sqrt(1)=1)
    assert pool_same_day_sleeve_R([0.73]) == 0.73
    assert pool_same_day_sleeve_R([0.73], sqrt_n=True) == 0.73


def test_pool_sqrtn_gives_more_credit_than_mean_for_multi_trade():
    # for a same-sign multi-trade day, sqrt-N credits MORE than mean (partial pooling, not corr=1)
    rs = [0.4, 0.6, 0.8]
    assert pool_same_day_sleeve_R(rs, sqrt_n=True) > pool_same_day_sleeve_R(rs, sqrt_n=False)


def test_sqrt_n_pooling_flag_recorded_default_off_neutral_to_sizing():
    # same-day same-sleeve metals trades -> ONE unit; worst-case-stop risk is UNCHANGED by sqrt-N
    intents = [_intent("metals_core", "XAUUSD"), _intent("metals_core", "XAGUSD")]
    off = [u for u in size_correlated_units(intents, base_risk_per_unit=0.0075) if u.cluster == "metals"][0]
    on = [u for u in size_correlated_units(intents, base_risk_per_unit=0.0075, sqrt_n_pooling=True)
          if u.cluster == "metals"][0]
    # risk identical (correlated cap = base*conf) — sqrt-N is an EV-credit convention, not a size change
    assert abs(off.unit_risk_pct - on.unit_risk_pct) < 1e-12
    assert abs(off.risk_pct_per_trade - on.risk_pct_per_trade) < 1e-12
    # the convention IS recorded on the multi-trade unit when enabled, absent when off
    assert any(r.startswith("sqrtN_pool_n2") for r in on.overlays_applied)
    assert not any(r.startswith("sqrtN_pool") for r in off.overlays_applied)


def test_sqrt_n_pooling_not_recorded_for_single_trade_unit():
    on = size_correlated_units([_intent("crypto", "BTCUSD")], base_risk_per_unit=0.01,
                               sqrt_n_pooling=True)[0]
    assert not any(r.startswith("sqrtN_pool") for r in on.overlays_applied)


# ---- (1) WAVE-7 owner NOMINAL dials (1.25% first cycle / 1.50% step-up / 2.00% ceiling) ----
def test_w7_nominal_dials_present_and_owner_chosen_sizes():
    fc = ALLOCATION_PROFILES[CLEAN3_W7_FIRST_CYCLE_PROFILE]
    gr = ALLOCATION_PROFILES[CLEAN3_W7_GROWTH_PROFILE]
    ce = ALLOCATION_PROFILES[CLEAN3_W7_CEILING_PROFILE]
    # owner-chosen NOMINAL sizes, two-account balanced
    assert fc.risk_per_unit_A == 0.0125 and fc.risk_per_unit_B == 0.0125
    assert gr.risk_per_unit_A == 0.015 and gr.risk_per_unit_B == 0.015
    assert ce.risk_per_unit_A == 0.020 and ce.risk_per_unit_B == 0.020
    # documented 2-account P(both) matches the locked INTEG_W7_FINAL_RESULT two_account_final
    assert abs(fc.base_p_both - 0.9928) < 1e-9   # balanced_1.25_1.25
    assert abs(gr.base_p_both - 0.9852) < 1e-9   # balanced_1.50_1.50
    assert abs(ce.base_p_both - 0.9553) < 1e-9   # staggered_2.00_1.50 base (ceiling reference)
    # monotone: more size -> lower base pass, lower 1.5x-stress P(both)
    assert fc.base_p_both > gr.base_p_both > ce.base_p_both
    assert fc.stress15_p_both > gr.stress15_p_both > ce.stress15_p_both


def test_w7_dials_default_off_surface_and_governor_gated():
    # the W7 nominal dial drives clean_3 sizing WITH the kelly runtime; default surface stays locked.
    out = admit_and_size([_intent("crypto", "BTCUSD")], _state(),
                         profile=CLEAN3_W7_FIRST_CYCLE_PROFILE,
                         include_clean3=True, kelly_lite=True, kelly_conservative=True)
    assert out["ok"] and out["new_entries_allowed"]
    assert out["kelly_lite"] is True and out["kelly_conservative"] is True
    assert out["base_risk_per_unit"] == 0.0125
    # circuit breaker still flattens regardless of the dial
    cb = admit_and_size([_intent("crypto", "BTCUSD")], _state(operator_circuit_breaker=True),
                        profile=CLEAN3_W7_FIRST_CYCLE_PROFILE, include_clean3=True, kelly_lite=True)
    assert cb["ok"] and not cb["new_entries_allowed"] and cb["units"] == []


def test_admit_and_size_drop_w7_symbols_flag():
    # drop_w7_symbols filters HEATOIL/NATGAS intents before sizing; default OFF.
    intents = [_intent("energy_agri", "USOIL_cash"),
               TradeIntent("energy_agri", "NATGAS_cash", 1, "2026-01-05", 1.0)]
    on = admit_and_size(intents, _state(), drop_w7_symbols=True)
    assert on["drop_w7_symbols"] is True
    assert "NATGAS_cash" in on["dropped_w7_symbols"]
    # only the USOIL intent survives -> the energy unit is sized from 1 trade
    energy_units = [u for u in on["units"] if u["cluster"] == "energy"]
    assert energy_units and energy_units[0]["n_trades"] == 1
    # default off -> both intents pass to sizing (NATGAS would size, illiquid-but-not-filtered here)
    off = admit_and_size(intents, _state())
    assert off["drop_w7_symbols"] is False and off["dropped_w7_symbols"] == []


def test_describe_book_w7_block_has_tick_floor_and_sqrtn():
    d = describe_book()
    w7 = d["clean3"]["w7_final"]
    assert w7["dropped_symbols"] == ["HEATOIL_c", "NATGAS_cash"]
    assert w7["tick_spread_floor_r"]["XAUUSD"] == TICK_SPREAD_FLOOR_R["XAUUSD"]
    assert w7["sqrt_n_pooling"]["default_off"] is True
    assert w7["first_cycle_profile"] == CLEAN3_W7_FIRST_CYCLE_PROFILE
    assert w7["growth_profile"] == CLEAN3_W7_GROWTH_PROFILE
    assert w7["ceiling_profile"] == CLEAN3_W7_CEILING_PROFILE


# ---- REPLAY-vs-MODULE PARITY: module W7 constants == locked INTEG_W7_FINAL_RESULT.json ----
def test_w7_final_parity_with_locked_integrator_artifact():
    """The module's W7 dropped symbols + Kelly bins + owner-dial headline MUST equal the locked MC."""
    res = P.assert_w7_final_parity()
    assert res["parity_ok"], res["mismatches"]
    # the parity check surfaces the locked headline the deploy decision rests on
    assert abs(res["w7_final_1p25"]["p_pass"] - 0.99355) < 1e-9
    assert abs(res["w7_final_1p50"]["p_pass"] - 0.9859) < 1e-9
    assert res["w7_final_1p25"]["daily_breach_pct"] == 0.0
    assert res["w7_final_1p50"]["daily_breach_pct"] == 0.0


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
