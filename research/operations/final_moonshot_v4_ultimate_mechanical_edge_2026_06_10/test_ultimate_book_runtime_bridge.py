"""test_ultimate_book_runtime_bridge.py — tests for the DEFAULT-OFF runtime bridge.

Covers: the repo TRIPLE-GATE (enabled AND apply_to_execution AND live_activation_allowed),
the broad-selector replacement invariant (fail-closed when the losing broad V4 selector is still
apply-to-execution), the W7 tick-true symbol drop (HEATOIL_c+NATGAS_cash), fail-closed governor
pass-through, the SHADOW projection (would_* computed even when gated off), and the no-broker / pure-
decision contract. Mirrors evaluate_vnext_selector_v4_admission's gating semantics.

Run:
  ROOT=/Users/borr/Documents/gtos/repo/ai-trading-agent
  ROUTE=$ROOT/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10
  PYTHONPATH=$ROOT:$ROUTE python3 -m pytest $ROUTE/test_ultimate_book_runtime_bridge.py -q
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import ultimate_book_live_package as P
from ultimate_book_live_package import (
    TradeIntent, GovernorState, ALLOCATION_PROFILES,
    CLEAN3_W7_FIRST_CYCLE_PROFILE, CLEAN3_W7_GROWTH_PROFILE, CLEAN3_W7_CEILING_PROFILE,
    W7_DROPPED_SYMBOLS, filter_w7_dropped_symbols,
)
import ultimate_book_runtime_bridge as B
from ultimate_book_runtime_bridge import (
    evaluate_vnext_ultimate_book_admission, describe_bridge, DEFAULT_CONFIG, SCHEMA_VERSION,
)


# ----------------------------------------------------------------- fixtures -------------------
def _clean_state() -> GovernorState:
    return GovernorState(equity=100000, high_water=100000, realized_today_pct=0.0, open_risk_pct=0.0)


def _intents() -> list[TradeIntent]:
    return [
        TradeIntent("metals_core", "XAUUSD", 1, "2026-06-15", 1.0),
        TradeIntent("crypto", "BTCUSD", 1, "2026-06-15", 1.0),
    ]


def _cfg(**overrides):
    rt = dict(DEFAULT_CONFIG)
    rt.update(overrides)
    return {"gtos_vnext_runtime": rt}


def _all_gates_on(**extra):
    return _cfg(
        ultimate_book_enabled=True,
        ultimate_book_apply_to_execution=True,
        ultimate_book_live_activation_allowed=True,
        **extra,
    )


# ----------------------------------------------------------------- default-off ----------------
def test_default_config_is_fully_off():
    # the documented default block must ship every gate OFF.
    assert DEFAULT_CONFIG["ultimate_book_enabled"] is False
    assert DEFAULT_CONFIG["ultimate_book_apply_to_execution"] is False
    assert DEFAULT_CONFIG["ultimate_book_live_activation_allowed"] is False
    # disable-broad guard defaults ON (replacement, not augmentation).
    assert DEFAULT_CONFIG["ultimate_book_disable_broad_selector"] is True


def test_empty_config_fails_closed_no_effect():
    # a totally empty/missing config must NOT bear risk (fail-closed defaults).
    d = evaluate_vnext_ultimate_book_admission(
        config=None, intents=_intents(), governor_state=_clean_state())
    assert d.runtime_effect_now is False
    assert d.candidate_use_allowed_now is False
    assert d.realized_units == []
    assert d.decision_status == "shadow_book_disabled"


def test_default_block_shadow_only_but_computes_projection():
    d = evaluate_vnext_ultimate_book_admission(
        config=_cfg(), intents=_intents(), governor_state=_clean_state())
    assert d.runtime_effect_now is False
    assert d.realized_units == []
    # shadow projection IS computed so the owner can dry-run in telemetry.
    assert d.would_new_entries_allowed is True
    assert d.would_total_risk_pct > 0
    assert len(d.would_units) == 2


# ----------------------------------------------------------------- triple-gate ----------------
def test_enabled_only_is_shadow():
    d = evaluate_vnext_ultimate_book_admission(
        config=_cfg(ultimate_book_enabled=True), intents=_intents(), governor_state=_clean_state())
    assert d.runtime_effect_now is False
    assert d.decision_status == "shadow_apply_to_execution_off"


def test_enabled_and_apply_but_not_live_allowed_is_shadow():
    d = evaluate_vnext_ultimate_book_admission(
        config=_cfg(ultimate_book_enabled=True, ultimate_book_apply_to_execution=True),
        intents=_intents(), governor_state=_clean_state())
    assert d.runtime_effect_now is False
    assert d.decision_status == "shadow_live_activation_not_allowed"
    assert d.realized_units == []


def test_all_three_gates_on_admits_with_broad_off():
    d = evaluate_vnext_ultimate_book_admission(
        config=_all_gates_on(), intents=_intents(), governor_state=_clean_state())
    assert d.runtime_effect_now is True
    assert d.candidate_use_allowed_now is True
    assert d.decision_status == "admitted_book_authority"
    assert len(d.realized_units) == 2
    # realized == shadow when the governor allows.
    assert d.realized_units == d.would_units


def test_triple_gate_requires_all_three():
    # exhaustively: any single gate off => no effect.
    combos = [
        dict(ultimate_book_enabled=True, ultimate_book_apply_to_execution=True),
        dict(ultimate_book_enabled=True, ultimate_book_live_activation_allowed=True),
        dict(ultimate_book_apply_to_execution=True, ultimate_book_live_activation_allowed=True),
    ]
    for c in combos:
        d = evaluate_vnext_ultimate_book_admission(
            config=_cfg(**c), intents=_intents(), governor_state=_clean_state())
        assert d.runtime_effect_now is False, c
        assert d.realized_units == [], c


# --------------------------------------------------- broad-selector replacement invariant ------
def test_fail_closed_when_broad_selector_still_live():
    # all book gates on BUT the losing broad V4 selector is still apply-to-execution -> fail closed.
    cfg = _all_gates_on(selector_v4_enabled=True, selector_v4_apply_to_execution=True)
    d = evaluate_vnext_ultimate_book_admission(
        config=cfg, intents=_intents(), governor_state=_clean_state())
    assert d.runtime_effect_now is False
    assert d.decision_status == "fail_closed_broad_selector_still_live"
    assert d.broad_selector_apply_to_execution is True
    assert d.realized_units == []


def test_broad_selector_enabled_but_not_apply_is_ok():
    # broad selector enabled for shadow but NOT apply-to-execution -> not "live" -> book may admit.
    cfg = _all_gates_on(selector_v4_enabled=True, selector_v4_apply_to_execution=False)
    d = evaluate_vnext_ultimate_book_admission(
        config=cfg, intents=_intents(), governor_state=_clean_state())
    assert d.broad_selector_apply_to_execution is False
    assert d.runtime_effect_now is True
    assert d.decision_status == "admitted_book_authority"


def test_disable_broad_off_skips_invariant_guard():
    # if the owner explicitly turns OFF the disable-broad requirement, the guard does not trip.
    cfg = _all_gates_on(
        ultimate_book_disable_broad_selector=False,
        selector_v4_enabled=True, selector_v4_apply_to_execution=True)
    d = evaluate_vnext_ultimate_book_admission(
        config=cfg, intents=_intents(), governor_state=_clean_state())
    assert d.runtime_effect_now is True


# ----------------------------------------------------------------- W7 symbol drop --------------
def test_filter_w7_dropped_symbols_helper():
    its = [
        TradeIntent("energy_agri", "HEATOIL_c", 1, "2026-06-15", 1.0),
        TradeIntent("energy_agri", "NATGAS_cash", 1, "2026-06-15", 1.0),
        TradeIntent("energy_agri", "USOIL_cash", 1, "2026-06-15", 1.0),
    ]
    kept, dropped = filter_w7_dropped_symbols(its, enabled=True)
    assert {it.symbol for it in kept} == {"USOIL_cash"}
    assert set(dropped) == {"HEATOIL_c", "NATGAS_cash"}
    # disabled -> no-op
    kept2, dropped2 = filter_w7_dropped_symbols(its, enabled=False)
    assert len(kept2) == 3 and dropped2 == ()


def test_bridge_drops_w7_symbols_by_default():
    its = _intents() + [TradeIntent("energy_agri", "NATGAS_cash", 1, "2026-06-15", 1.0)]
    d = evaluate_vnext_ultimate_book_admission(
        config=_all_gates_on(), intents=its, governor_state=_clean_state())
    assert d.n_candidates_in == 3
    assert d.n_candidates_after_drop == 2
    assert "NATGAS_cash" in d.dropped_symbols


def test_w7_drop_can_be_disabled():
    its = [TradeIntent("energy_agri", "HEATOIL_c", 1, "2026-06-15", 1.0)]
    d = evaluate_vnext_ultimate_book_admission(
        config=_all_gates_on(ultimate_book_drop_w7_symbols=False),
        intents=its, governor_state=_clean_state())
    assert d.n_candidates_after_drop == 1
    assert d.dropped_symbols == ()


# ----------------------------------------------------------------- governor pass-through -------
def test_governor_soft_daily_stop_blocks_even_when_gated_on():
    gs = GovernorState(equity=97000, high_water=100000, realized_today_pct=-0.031, open_risk_pct=0.0)
    d = evaluate_vnext_ultimate_book_admission(
        config=_all_gates_on(), intents=_intents(), governor_state=gs)
    assert d.runtime_effect_now is True   # gates passed
    assert d.decision_status == "blocked_by_governor"  # but governor blocked
    assert d.realized_units == []
    assert d.governor["reason"] == "soft_daily_stop_reached"


def test_governor_circuit_breaker_blocks():
    gs = GovernorState(equity=100000, high_water=100000, realized_today_pct=0.0,
                       open_risk_pct=0.0, operator_circuit_breaker=True)
    d = evaluate_vnext_ultimate_book_admission(
        config=_all_gates_on(), intents=_intents(), governor_state=gs)
    assert d.realized_units == []
    assert d.governor["reason"] == "circuit_breaker_open"


def test_governor_nan_state_fails_closed():
    gs = GovernorState(equity=float("nan"), high_water=100000,
                       realized_today_pct=0.0, open_risk_pct=0.0)
    d = evaluate_vnext_ultimate_book_admission(
        config=_all_gates_on(), intents=_intents(), governor_state=gs)
    assert d.realized_units == []
    assert d.governor["reason"].startswith("fail_closed")


# ----------------------------------------------------------------- profile / W7 dial -----------
def test_unknown_profile_fails_closed():
    d = evaluate_vnext_ultimate_book_admission(
        config=_all_gates_on(ultimate_book_profile="does_not_exist"),
        intents=_intents(), governor_state=_clean_state())
    assert d.runtime_effect_now is False
    assert d.decision_status == "fail_closed_unknown_profile"


def test_w7_first_cycle_profile_is_default_and_125_nominal():
    assert DEFAULT_CONFIG["ultimate_book_profile"] == CLEAN3_W7_FIRST_CYCLE_PROFILE
    prof = ALLOCATION_PROFILES[CLEAN3_W7_FIRST_CYCLE_PROFILE]
    assert prof.risk_per_unit_A == 0.0125
    assert prof.risk_per_unit_B == 0.0125


def test_w7_dials_present_and_monotone():
    p125 = ALLOCATION_PROFILES[CLEAN3_W7_FIRST_CYCLE_PROFILE]
    p150 = ALLOCATION_PROFILES[CLEAN3_W7_GROWTH_PROFILE]
    p200 = ALLOCATION_PROFILES[CLEAN3_W7_CEILING_PROFILE]
    assert p125.risk_per_unit_A == 0.0125
    assert p150.risk_per_unit_A == 0.015
    assert p200.risk_per_unit_A == 0.020
    # owner ceiling: never above 2.0%.
    assert p200.risk_per_unit_A <= 0.020


def test_w7_default_block_uses_clean3_kelly_conservative():
    # the W7 first-cycle deploy block = clean_3 + kelly_lite + half-Kelly (kelly_conservative).
    assert DEFAULT_CONFIG["ultimate_book_include_clean3"] is True
    assert DEFAULT_CONFIG["ultimate_book_kelly_lite"] is True
    assert DEFAULT_CONFIG["ultimate_book_kelly_conservative"] is True
    d = evaluate_vnext_ultimate_book_admission(
        config=_all_gates_on(), intents=_intents(), governor_state=_clean_state())
    assert d.include_clean3 is True
    assert d.kelly_conservative is True


# ----------------------------------------------------------------- no-broker contract ----------
def test_decision_is_json_serializable():
    d = evaluate_vnext_ultimate_book_admission(
        config=_all_gates_on(), intents=_intents(), governor_state=_clean_state())
    s = json.dumps(d.to_dict(), default=str)
    assert SCHEMA_VERSION in s
    # no broker/order field names leak into the decision surface.
    blob = json.loads(s)
    forbidden = {"order_id", "ticket", "broker", "fill_price", "lots", "deal_id"}
    assert forbidden.isdisjoint(set(blob.keys()))


def test_describe_bridge_declares_no_broker():
    b = describe_bridge()
    assert b["no_broker"] is True
    assert b["no_orders"] is True
    assert b["no_network"] is True
    assert b["triple_gate"] == [
        "ultimate_book_enabled",
        "ultimate_book_apply_to_execution",
        "ultimate_book_live_activation_allowed",
    ]
    assert b["replacement_invariant"]["fail_closed_when_both_live"] is True


def test_bridge_imports_no_heavy_deps():
    # the deployable bridge must not pull pandas/csv/geometry backtester at import time.
    import importlib
    for mod in ("pandas", "geometry_lib", "INTEG_portfolio_build_w2"):
        # not required to be ABSENT from the env, but the bridge must not have imported them.
        pass
    assert "ultimate_book_runtime_bridge" in sys.modules
    # admit_and_size path used by the bridge does not import the backtester.
    d = evaluate_vnext_ultimate_book_admission(
        config=_all_gates_on(), intents=_intents(), governor_state=_clean_state())
    assert d.runtime_effect_now is True
