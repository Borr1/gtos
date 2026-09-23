"""The two owner-authorized 2026-08-11 changes to ARMED sleeves, pinned behaviourally.

  CHANGE 1  `crypto` trades ETHUSD as well as BTCUSD and DASHUSD.
  CHANGE 2  `energy_agri`'s committed exit is a plain 4R time-stop; the `partial_be_runner`
            scale-out is gone from the default path and survives only as a frontier override.

Both sleeves are ARMED on both funded accounts. These tests exist so that a later edit which
silently moves either contract fails here rather than on a broker.

The bias throughout is BEHAVIOURAL: a generator is driven with constructed bars and asked to emit
an intent, and an exit profile is pushed through the packet builder and asked what the broker
request would carry. Two assertions are deliberately by-value instead -- the armed contract table
and the two crypto surface declarations -- because "did this exact number move" is the question,
and a test that recomputes the value it is checking cannot answer it.
"""
from __future__ import annotations

import math

import pytest

from src.components.ultimate_book import execution_packets as EP
from src.components.ultimate_book.admission import SLEEVE_REGISTRY, TradeIntent
from src.components.ultimate_book.primitives import Bar
from src.components.ultimate_book.sleeves import crypto as SL_CRYPTO
from src.components.ultimate_book.sleeves import registry as SL_REGISTRY


# ======================================================================= CHANGE 1: ETHUSD ======
def test_ethusd_is_on_the_crypto_surface():
    assert "ETHUSD" in SL_CRYPTO.ON_SURFACE
    assert SL_CRYPTO.ON_SURFACE == ("BTCUSD", "DASHUSD", "ETHUSD")


def test_the_generation_registry_carries_the_surface_by_reference():
    """`book_engine.py:548` iterates `spec.on_surface`, so THIS is what decides live generation."""
    spec = SL_REGISTRY.BUILT["crypto"]
    assert spec.on_surface is SL_CRYPTO.ON_SURFACE
    assert "ETHUSD" in spec.on_surface


def test_the_second_surface_declaration_agrees_with_the_first():
    """`admission.SLEEVE_REGISTRY['crypto'].symbols` is a hand-maintained copy of the same tuple.

    It gates nothing live (only two forensics scripts read it) which is exactly why it went stale
    and stayed stale: it read ("BTCUSD","DASHUSD") with a comment asserting ETH was deliberately
    excluded, for as long as that claim was false. A silent second source of truth is the defect
    class this repository keeps paying for.
    """
    assert tuple(SLEEVE_REGISTRY["crypto"].symbols) == tuple(SL_CRYPTO.ON_SURFACE)


def _breakout_bars(n: int = 240, block: int = 30, fast: float = 2.0, slow: float = 0.1,
                   jump: float = 0.5) -> list[Bar]:
    """A series the crypto rule fires LONG on: a 20-bar Donchian break with ac60 >= 0.15.

    The gate is the lag-1 autocorrelation of the last 60 close-to-close CHANGES, so a constant
    drift scores ZERO (every change equals the mean; the denominator collapses). Persistence has
    to come from runs: 30-bar blocks alternating a fast and a slow advance put long stretches of
    same-signed deviation from the mean next to each other, which is what the statistic measures.
    This construction scores ac60 = 0.953 -- a wide margin over the 0.15 threshold, so the test
    pins the rule rather than a knife-edge input.
    """
    bars: list[Bar] = []
    px = 100.0
    for i in range(n):
        step = fast if (i // block) % 2 == 0 else slow
        px += step
        bars.append(Bar(px - step, px + 0.10, px - step - 0.10, px))
    close = max(b.h for b in bars[-20:]) + jump      # clears the prior 20-bar high
    bars.append(Bar(bars[-1].c, close + 0.1, bars[-1].c - 0.1, close))
    return bars


def test_the_fixture_exercises_the_gate_rather_than_dodging_it():
    """If the constructed series stopped clearing ac60, every generation test below would go
    green by never reaching the rule. Assert the gate is live and the margin is real."""
    from src.components.ultimate_book.primitives import autocorr
    bars = _breakout_bars()
    i = len(bars) - 1
    ac = autocorr(bars, i, 60)
    assert ac is not None and ac >= SL_CRYPTO.AC_THR
    assert bars[i].c > max(bars[k].h for k in range(i - SL_CRYPTO.DON_LB, i))
    # and the gate really does refuse: a driftless series has no persistence to measure
    flat = [Bar(100.0, 100.1, 99.9, 100.0) for _ in range(240)]
    flat.append(Bar(100.0, 105.0, 99.9, 105.0))
    assert SL_CRYPTO.generate("ETHUSD", flat, "2026-08-11") is None


def test_ethusd_actually_generates_an_intent_not_just_a_declaration():
    """Declared-but-not-generating is the failure mode `--tags` typos produce. Drive the rule."""
    bars = _breakout_bars()
    intent = SL_CRYPTO.generate("ETHUSD", bars, "2026-08-11")
    assert intent is not None, "ETHUSD is on the surface but the generator refused it"
    assert isinstance(intent, TradeIntent)
    assert intent.sleeve == "crypto" and intent.symbol == "ETHUSD"
    assert intent.direction == 1
    assert intent.stop_dist > 0
    # geometry is the sleeve's, unchanged by the surface widening: 4R off a 2*ATR stop
    assert math.isclose(intent.target_dist / intent.stop_dist, SL_CRYPTO.TARGET_R, rel_tol=1e-12)


def test_the_surface_is_still_bounded():
    """Widening a surface must not become 'any symbol'."""
    bars = _breakout_bars()
    assert SL_CRYPTO.generate("XAUUSD", bars, "2026-08-11") is None
    assert SL_CRYPTO.generate("SOLUSD", bars, "2026-08-11") is None


def test_ethusd_and_btcusd_take_the_same_rule():
    """Same bars, same decision -- the change adds a symbol, it does not add a rule."""
    bars = _breakout_bars()
    eth = SL_CRYPTO.generate("ETHUSD", bars, "2026-08-11")
    btc = SL_CRYPTO.generate("BTCUSD", bars, "2026-08-11")
    assert eth is not None and btc is not None
    assert (eth.direction, eth.stop_dist, eth.target_dist) == (btc.direction, btc.stop_dist,
                                                               btc.target_dist)


def test_the_four_symbols_the_measurement_rejected_are_not_on_the_surface():
    """ADAUSD/DOTUSD/LTCUSD/XRPUSD measure -0.3128 R/trade jointly (n=164) and would consume
    cluster-cap slots from a positive symbol. The expansion is ONE symbol, deliberately."""
    for sym in ("ADAUSD", "DOTUSD", "LTCUSD", "XRPUSD", "XTZUSD", "AVAUSD"):
        assert sym not in SL_CRYPTO.ON_SURFACE


# ================================================================= CHANGE 2: the energy exit ===
#: The contract `energy_agri` ran live from arming until 2026-08-11. Kept as a literal so the
#: rollback lever can be checked against the thing it claims to restore.
_PRE_CHANGE_ENERGY_CONTRACT = {
    "policy": "partial_be_runner", "trigger_r": 2.0, "final_target_r": 4.0,
    "partial_close_ratio": 0.5, "time_stop_bars": 1280,
}


def test_energy_agri_committed_exit_is_a_plain_4r_time_stop():
    prof = EP.SLEEVE_EXIT_PROFILES["energy_agri"]
    assert prof == {"policy": "time_stop", "final_target_r": 4.0, "time_stop_bars": 1280}
    assert "partial_close_ratio" not in prof
    assert "trigger_r" not in prof


def test_the_default_resolution_carries_no_scale_out():
    """With no frontier selection -- which is what both accounts run -- there is no partial leg."""
    prof = EP.resolve_exit_profile("energy_agri")
    assert prof is EP.SLEEVE_EXIT_PROFILES["energy_agri"]
    assert prof["policy"] == "time_stop"
    assert prof.get("partial_close_ratio") is None


def test_the_broker_facing_instrumentation_has_no_partial_leg():
    """What the runtime re-drives an adopted position from. A stale partial here would scale out
    a position placed under the plain contract."""
    inst = EP.native_policy_instrumentation("energy_agri")
    assert inst["gtos_vnext_dynamic_policy_selected"] == "time_stop"
    assert inst["gtos_vnext_execution_policy_id"] == "emv4_time_stop_v1"
    assert inst["gtos_vnext_dynamic_partial_close_ratio"] is None
    assert float(inst["gtos_vnext_dynamic_final_target_r"]) == 4.0
    assert int(inst["gtos_vnext_dynamic_time_stop_bars"]) == 1280
    # a `time_stop` sleeve's BE trigger resolves to its own final target, i.e. it never fires early
    assert float(inst["gtos_vnext_dynamic_be_trigger_r"]) == 4.0


def test_the_horizon_and_the_target_did_not_move():
    """The delta is the scale-out ALONE. If the target or the horizon moved with it, the measured
    -0.2883 R/trade would not be the quantity this change is buying."""
    before, after = _PRE_CHANGE_ENERGY_CONTRACT, EP.SLEEVE_EXIT_PROFILES["energy_agri"]
    assert after["final_target_r"] == before["final_target_r"] == 4.0
    assert after["time_stop_bars"] == before["time_stop_bars"] == 1280


def test_the_frontier_override_restores_the_previous_contract_exactly():
    """The rollback lever. `--frontier-exits energy_agri` must reproduce the pre-change contract
    by value, or it is not a rollback."""
    prof = EP.resolve_exit_profile("energy_agri", frontier_exits=("energy_agri",))
    contract = {k: v for k, v in prof.items() if k not in EP._FRONTIER_PROVENANCE_KEYS}
    assert contract == _PRE_CHANGE_ENERGY_CONTRACT


def test_the_override_is_not_a_silent_no_op():
    """An override that resolves to the committed dict is an operator believing they changed
    something. Whatever the override says, it must differ from the default."""
    default = EP.resolve_exit_profile("energy_agri")
    overridden = EP.resolve_exit_profile("energy_agri", frontier_exits=("energy_agri",))
    contract = {k: v for k, v in overridden.items() if k not in EP._FRONTIER_PROVENANCE_KEYS}
    assert contract != dict(default)
    assert EP.frontier_provenance(overridden)["frontier_cell"] == "partial_be_runner_restore"


def test_selecting_energy_does_not_select_crypto_or_xvol():
    """`--frontier-exits` is a per-sleeve list. `crypto`'s wired cell is `stop_1p5x_target_scale`,
    which was ARMED and then ROLLED BACK on 2026-08-10 by owner word, and `sub_xvol_pullback`'s is
    `target_4R`, which REJECTS at all four bands. Selecting energy must reach neither."""
    sel = ("energy_agri",)
    for other in ("crypto", "sub_xvol_pullback"):
        assert EP.resolve_exit_profile(other, frontier_exits=sel) is EP.SLEEVE_EXIT_PROFILES[other]


# ========================================================= the armed set, pinned by value ======
#: One row per sleeve that is armed, or was armed recently enough that a live position could still
#: be open under its contract. A change to any of these is a live-money behaviour change and must
#: be a deliberate edit to this table, never a side effect.
#:
#: `sub_mid_dn_revert` is DISARMED on both accounts as of 2026-08-11 (host `47d0960e6`, committed
#: `ed4d071f1` on `origin/main`). It is pinned anyway: this worktree's branch predates that commit
#: and still declares it, and a sleeve disarmed yesterday is exactly the one whose contract must
#: not drift while a position adopted under it is still being managed.
_ARMED_CONTRACTS = {
    "crypto": {"policy": "time_stop", "final_target_r": 4.0, "time_stop_bars": 1280},
    "energy_agri": {"policy": "time_stop", "final_target_r": 4.0, "time_stop_bars": 1280},
    "sub_xvol_pullback": {"policy": "time_stop", "final_target_r": 3.0, "time_stop_bars": 1280},
    "sub_mid_dn_revert": {"policy": "time_stop", "final_target_r": 3.0, "time_stop_bars": 1280},
}
_ARMED_SURFACES = {
    "crypto": ("BTCUSD", "DASHUSD", "ETHUSD"),
    "energy_agri": ("USOIL_cash", "UKOIL_cash"),
}


@pytest.mark.parametrize("sleeve", sorted(_ARMED_CONTRACTS))
def test_armed_sleeve_exit_contract_is_pinned(sleeve):
    assert EP.SLEEVE_EXIT_PROFILES[sleeve] == _ARMED_CONTRACTS[sleeve]


@pytest.mark.parametrize("sleeve", sorted(_ARMED_SURFACES))
def test_armed_sleeve_generation_surface_is_pinned(sleeve):
    assert tuple(SL_REGISTRY.BUILT[sleeve].on_surface) == _ARMED_SURFACES[sleeve]


def test_the_pinned_set_is_the_declared_armed_set():
    """If an arming decision adds a sleeve, this table must grow with it -- otherwise the pins
    above silently stop covering live money."""
    from src.safety.armed_set import armed_sleeves
    declared = set()
    for acct in ("operator_profile", "redacted_account_live_bee34003"):
        declared |= set(armed_sleeves(acct))
    assert declared <= set(_ARMED_CONTRACTS), (
        f"armed sleeves not pinned here: {sorted(declared - set(_ARMED_CONTRACTS))}")


def test_the_other_armed_sleeves_were_not_touched_by_either_change():
    """Named, because 'nothing else moved' is the claim a live carry rests on."""
    assert EP.SLEEVE_EXIT_PROFILES["crypto"] == {
        "policy": "time_stop", "final_target_r": 4.0, "time_stop_bars": 1280}
    assert EP.SLEEVE_EXIT_PROFILES["sub_xvol_pullback"] == {
        "policy": "time_stop", "final_target_r": 3.0, "time_stop_bars": 1280}
    assert "ETHUSD" not in SL_REGISTRY.BUILT["sub_mid_dn_revert"].on_surface
    assert SL_REGISTRY.BUILT["energy_agri"].on_surface == ("USOIL_cash", "UKOIL_cash")
