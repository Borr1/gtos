"""test_admission_learning_wiring.py — the L5 learning actuator + A8 confluence gate wired into the
live admission/sizing path (admission.py), BOTH DEFAULT-OFF.

Proves: (1) default-off is byte-identical to today (no behavior change); (2) the owner-armed learning
rerate GATEs a non-edge (drops it), DOWN_WEIGHTs a soft-negative (halves conf), SIZE_UPs a validated
sleeve (bounded); (3) the A8 gate drops a featured-failing metals intent, keeps a passing one, and
ADMITS a featureless intent as today (the deploy-phase generator change arms it).
"""
import sys
# NOTE 2026-07-26: a hardcoded sys.path.insert(0, "/Users/borr/Documents/gtos/repo/
# ai-trading-agent") was removed here. It prepended a DIFFERENT, stale checkout, so this
# file silently tested that repo instead of the working tree whenever it ran in isolation
# (in a full-suite run sys.modules was already populated, so the same tests exercised the
# real code and could disagree). Tests must import the tree they are checked out in.
from src.components.ultimate_book.admission import (
    size_correlated_units, admit_and_size, TradeIntent, GovernorState, GovernorLimits,
    LEARNING_RERATE_MAX)

DAY = "2026-06-17"


def _intents():
    return [
        TradeIntent("metals_core", "XAUUSD", 1, DAY, 10.0, target_dist=20.0),
        TradeIntent("idxrev", "SPX500", -1, DAY, 5.0, target_dist=10.0),
        TradeIntent("fx_jpy", "USDJPY", 1, DAY, 0.5, target_dist=1.25),
    ]


def _by_cluster(units):
    return {u.cluster: u for u in units}


def test_default_off_byte_identical():
    base = size_correlated_units(_intents(), base_risk_per_unit=0.02)
    on_none = size_correlated_units(_intents(), base_risk_per_unit=0.02,
                                    learning_rerate=None, metals_confluence_gate=False)
    assert [(u.cluster, u.confidence, u.unit_risk_pct) for u in base] == \
           [(u.cluster, u.confidence, u.unit_risk_pct) for u in on_none], "default-off must be a no-op"


def test_learning_gate_drops_non_edge():
    units = size_correlated_units(_intents(), base_risk_per_unit=0.02, learning_rerate={"idxrev": 0.0})
    by = _by_cluster(units)
    assert "index" not in by, "GATE (mult 0.0) must DROP idxrev entirely (no index unit)"
    assert "metals" in by and "jpy" in by, "the other sleeves are untouched"


def test_learning_downweight_halves_confidence():
    base = _by_cluster(size_correlated_units(_intents(), base_risk_per_unit=0.02))
    dn = _by_cluster(size_correlated_units(_intents(), base_risk_per_unit=0.02,
                                           learning_rerate={"fx_jpy": 0.5}))
    assert abs(dn["jpy"].confidence - 0.5 * base["jpy"].confidence) < 1e-9, "DOWN_WEIGHT must halve conf"
    assert abs(dn["jpy"].unit_risk_pct - 0.5 * base["jpy"].unit_risk_pct) < 1e-12


def test_learning_sizeup_is_bounded():
    base = _by_cluster(size_correlated_units(_intents(), base_risk_per_unit=0.02))
    # ask for a 5x size-up; must clamp to LEARNING_RERATE_MAX (1.25x), never 5x
    up = _by_cluster(size_correlated_units(_intents(), base_risk_per_unit=0.02,
                                           learning_rerate={"metals_core": 5.0}))
    ratio = up["metals"].confidence / base["metals"].confidence
    assert abs(ratio - LEARNING_RERATE_MAX) < 1e-9, f"size-up clamped to {LEARNING_RERATE_MAX}, got {ratio:.3f}"


def test_a8_gate_drops_failing_keeps_passing_admits_featureless():
    # a metals intent that PASSES K=3-of-4 (up_regime + fresh + vol_cap + asian = 4/4)
    passing = TradeIntent("metals_core", "XAUUSD", 1, DAY, 10.0, target_dist=20.0,
                          htf_slope_norm=0.5, mom_20_atr=0.5, fvg_freshness_bars=2,
                          atr_ratio=1.0, session_hour=3)
    # a metals intent that FAILS (0/4: down-regime, stale, vol-extreme, NY-session)
    failing = TradeIntent("metals_core", "XAGUSD", 1, DAY, 10.0, target_dist=20.0,
                          htf_slope_norm=-0.5, mom_20_atr=-0.5, fvg_freshness_bars=99,
                          atr_ratio=2.5, session_hour=15)
    featureless = TradeIntent("metals_core", "XAUEUR", 1, DAY, 10.0, target_dist=20.0)  # no A8 features

    ig = [passing, failing, featureless]
    # gate OFF -> all kept (one metals cluster-unit with all 3 trades)
    off = _by_cluster(size_correlated_units(ig, base_risk_per_unit=0.02, metals_confluence_gate=False))
    assert off["metals"].n_trades == 3, "gate OFF keeps all 3 metals intents"
    # gate ON -> the FAILING featured intent is dropped; passing + featureless (admit-as-today) kept
    on = _by_cluster(size_correlated_units(ig, base_risk_per_unit=0.02, metals_confluence_gate=True))
    assert on["metals"].n_trades == 2, "gate ON drops only the featured-FAILING intent (keeps pass + featureless)"


def test_admit_and_size_records_flags_and_gating():
    state = GovernorState(equity=100000, high_water=100000, realized_today_pct=0.0,
                          open_risk_pct=0.0, max_dd_reference_equity=100000)
    lim = GovernorLimits(derisk_mode="smooth")
    out = admit_and_size(_intents(), state, profile="clean3_w7_ceiling_nom2p00", include_clean3=True,
                         kelly_lite=True, limits=lim, learning_rerate={"idxrev": 0.0, "fx_jpy": 0.5})
    assert out["learning_rerate_active"] is True
    assert out["learning_gated_sleeves"] == ["idxrev"]
    assert out["metals_confluence_gate"] is False
    # default-off call records inactive
    out0 = admit_and_size(_intents(), state, profile="clean3_w7_ceiling_nom2p00", include_clean3=True,
                          kelly_lite=True, limits=lim)
    assert out0["learning_rerate_active"] is False and out0["learning_gated_sleeves"] == []


def test_bridge_config_plumbing_default_off_and_armed():
    from src.components.ultimate_book.bridge import (
        evaluate_vnext_ultimate_book_admission, describe_bridge, DEFAULT_CONFIG)
    # the two new keys are registered with safe defaults (no-op / off)
    assert DEFAULT_CONFIG["ultimate_book_learning_rerate"] == {}
    assert DEFAULT_CONFIG["ultimate_book_metals_confluence_gate"] is False
    assert "ultimate_book_learning_rerate" in describe_bridge()["default_config"]

    st = GovernorState(equity=100000, high_water=100000, realized_today_pct=0.0,
                       open_risk_pct=0.0, max_dd_reference_equity=100000)
    ig = _intents()
    # default config -> idxrev present in the shadow projection (no rerate)
    d0 = evaluate_vnext_ultimate_book_admission(config={}, intents=ig, governor_state=st)
    assert "index" in {u["cluster"] for u in d0.would_units}
    # owner-armed rerate gating idxrev -> dropped from the shadow projection
    cfg = {"gtos_vnext_runtime": {"ultimate_book_learning_rerate": {"idxrev": 0.0}}}
    d1 = evaluate_vnext_ultimate_book_admission(config=cfg, intents=ig, governor_state=st)
    assert "index" not in {u["cluster"] for u in d1.would_units}


def test_bridge_malformed_rerate_is_safe_noop():
    # a malformed rerate map must never raise and never silently size up (fail-safe -> None/no-op)
    from src.components.ultimate_book.bridge import _rerate_map
    assert _rerate_map({"ultimate_book_learning_rerate": {}}) is None
    assert _rerate_map({"ultimate_book_learning_rerate": "garbage"}) is None
    assert _rerate_map({"ultimate_book_learning_rerate": {"idxrev": "x", "metals_core": 1.25}}) == {"metals_core": 1.25}


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    p = 0
    for fn in fns:
        try:
            fn(); p += 1; print(f"PASS {fn.__name__}")
        except Exception:
            print(f"FAIL {fn.__name__}"); traceback.print_exc()
    print(f"\n{p}/{len(fns)} admission-learning-wiring tests passed")
    assert p == len(fns)
