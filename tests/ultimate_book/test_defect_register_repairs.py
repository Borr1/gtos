"""Behavioural repairs for the Session-H sleeve-book defect register (D3-D11).

`docs/audits/fable5-vision-audit-20260725/phase2/SLEEVE_BOOK_DEFECT_REGISTER.md` recorded eleven
defects that Session H reproduced faithfully rather than fixed, because its port's whole value was
that it measured what actually trades. This file is the other half: the repairs, each pinned by a
test that FAILS against the unrepaired implementation.

Two rules held throughout, both from `SESSION_M_HYGIENE.md`:

* **No source-string assertions.** A test that greps source for a substring passes against a wrong
  implementation, and removing exactly that failure mode is why this session exists.
* **Every "X is excluded" assertion carries a positive control** proving X is included when the
  excluding condition is lifted. Without it, a test that excludes everything — or that evaluates
  nothing at all — reports the same green. That is the B41 vacuity, and it is cheap to not repeat.

D1, D2 and D9 are deliberately absent: each requires a risk-allocation or day-key decision that is
the owner's, not a hygiene fix. D5's repair is pinned in `tests/test_replay_policy_sleeve_book.py`
where its original defect-reproducing assertion lived.
"""
from __future__ import annotations

import tempfile

import pytest

from src.components.ultimate_book import admission as P
from src.components.ultimate_book.admission import (
    ALLOCATION_PROFILES,
    DEFAULT_LIMITS,
    GovernorLimits,
    GovernorState,
    TradeIntent,
    evaluate_governor,
    precount_intent_filter,
    size_correlated_units,
)
from src.components.ultimate_book.book_engine import UltimateBookLiveEngine
from src.components.ultimate_book.bridge import (
    REQUIRED_DIAL_KEYS,
    evaluate_vnext_ultimate_book_admission,
)

DAY = "2026-06-18"


def _metals(pass_a8: bool, symbol: str = "XAUUSD") -> TradeIntent:
    """A metals_core intent carrying the A8 confluence features, passing or failing K=3-of-4.

    Featureless metals intents are admitted-as-today by design, so the features must be POPULATED
    for the gate to be able to reject anything at all — a test that left them None would exercise
    the admit branch and prove nothing.
    """
    if pass_a8:  # UP_REGIME + FRESH + VOL_CAP + ASIAN = 4 of 4
        return TradeIntent("metals_core", symbol, 1, DAY, 1.0, htf_slope_norm=1.0, mom_20_atr=1.0,
                           fvg_freshness_bars=1.0, atr_ratio=1.0, session_hour=3)
    # ASIAN only = 1 of 4
    return TradeIntent("metals_core", symbol, 1, DAY, 1.0, htf_slope_norm=-1.0, mom_20_atr=-1.0,
                       fvg_freshness_bars=50.0, atr_ratio=3.0, session_hour=3)


def _crypto() -> TradeIntent:
    return TradeIntent("crypto", "BTCUSD", 1, DAY, 1.0)


def _engine_cfg(**over) -> dict:
    cfg = {
        "ultimate_book_enabled": True,
        "ultimate_book_apply_to_execution": False,
        "ultimate_book_live_activation_allowed": False,
        "ultimate_book_live_broker_authority": False,
        "ultimate_book_disable_broad_selector": True,
        "ultimate_book_profile": "clean3_w7_ceiling_nom2p00",
        "ultimate_book_derisk_mode": "smooth",
        "ultimate_book_include_clean3": False,
        "ultimate_book_include_candidate_book": False,
        "ultimate_book_include_market_expansion_book": False,
        "ultimate_book_kelly_lite": True,
        "ultimate_book_kelly_conservative": True,
        "ultimate_book_stress_derisk": False,
        "ultimate_book_drop_w7_symbols": True,
    }
    cfg.update(over)
    return cfg


def _engine(**over) -> UltimateBookLiveEngine:
    return UltimateBookLiveEngine(_engine_cfg(**over), object(), tempfile.mkdtemp())


# ---------------------------------------------------------------------------------------------
# D3 — the running-conviction pre-count omitted the A8 gate, and A8 is armed live
# ---------------------------------------------------------------------------------------------

def test_d3_running_count_excludes_a8_rejected_metals_when_the_gate_is_armed():
    """The live-realized half of D3.

    `ultimate_book_metals_confluence_gate` is TRUE live (`agent_config.yaml:1315`) and
    `ultimate_book_kelly_running_count` is TRUE live (`:1305`), so this is not a latent path. Before
    the repair the running override counted `metals_core` even when A8 rejected it; because
    `na = max(per_cycle, running)` can only carry the count UPWARD, that inflated the Kelly
    multiplier in the size-INCREASING direction.
    """
    intents = [_metals(pass_a8=False), _crypto()]

    armed = _engine(ultimate_book_kelly_running_count=True,
                    ultimate_book_metals_confluence_gate=True)
    counted_armed = armed._running_conviction_override(intents)

    # POSITIVE CONTROL: with the gate disarmed, the SAME intents on a fresh ledger count both
    # sleeves. Without this, a repair that broke the override entirely (returning None or 0 for
    # everything) would pass the assertion below while destroying the feature.
    disarmed = _engine(ultimate_book_kelly_running_count=True,
                       ultimate_book_metals_confluence_gate=False)
    counted_disarmed = disarmed._running_conviction_override(intents)

    assert counted_disarmed is not None and counted_disarmed.get(DAY) == 2, (
        f"positive control failed: disarmed gate should count both sleeves, got {counted_disarmed!r}"
    )
    assert counted_armed is not None and counted_armed.get(DAY) == 1, (
        f"A8-rejected metals_core still entered the running count: {counted_armed!r}"
    )


def test_d3_running_count_never_exceeds_the_set_the_sizer_actually_counts():
    """The general property, which is what actually stops D3 recurring.

    D3's root cause was DUPLICATION: the filter set was written once in `size_correlated_units` and
    again in `_running_conviction_override`, and the copies drifted. Pinning only the A8 instance
    would leave the next added filter free to drift the same way. So this asserts the invariant the
    override's own docstring calls CORRECTNESS-CRITICAL — the running count is never taken over a
    WIDER sleeve set than the one the sizer counts — across the whole flag matrix.
    """
    intents = [_metals(pass_a8=False), _metals(pass_a8=True, symbol="XAGUSD"), _crypto()]
    checked_a_dropping_case = False

    for gate in (False, True):
        for rerate in ({}, {"crypto": 0.0}):
            cfg_over = {
                "ultimate_book_kelly_running_count": True,
                "ultimate_book_metals_confluence_gate": gate,
                "ultimate_book_learning_rerate": rerate,
            }
            running = _engine(**cfg_over)._running_conviction_override(intents)

            sized = size_correlated_units(
                intents, base_risk_per_unit=0.02, kelly_lite=True,
                metals_confluence_gate=gate, learning_rerate=rerate or None,
            )
            sizer_sleeves = {s for u in sized for s in u.sleeve_members}
            running_count = (running or {}).get(DAY, 0)

            assert running_count <= len(sizer_sleeves), (
                f"gate={gate} rerate={rerate}: running count {running_count} exceeds the "
                f"{len(sizer_sleeves)} sleeves the sizer counts ({sorted(sizer_sleeves)}) — the "
                f"bound the override's docstring calls CORRECTNESS-CRITICAL is broken"
            )
            if len(sizer_sleeves) < 3:
                checked_a_dropping_case = True

    # Control: if no flag combination above actually dropped a sleeve, every assertion was trivially
    # satisfied and this test proved nothing.
    assert checked_a_dropping_case, "no flag combination dropped a sleeve; the bound was untested"


# ---------------------------------------------------------------------------------------------
# D6 — bridge.py claimed admission.py is a byte-identical copy of the route module
# ---------------------------------------------------------------------------------------------

def test_d6_admission_is_a_superset_of_the_route_module_not_a_copy():
    """Pins the TRUE relationship, so the false claim cannot be restored without a red test.

    The comment used to assert byte-identity. Asserting the real relationship — admission.py is the
    live authority, the route module is its ancestor, parity holds on the shared numeric core only —
    is what makes the correction load-bearing rather than cosmetic.
    """
    route = pytest.importorskip(
        "research.operations.final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
        ".ultimate_book_live_package",
        reason="route ancestor module not present in this checkout",
    )
    admission_names = {n for n in dir(P) if not n.startswith("__")}
    route_names = {n for n in dir(route) if not n.startswith("__")}

    # Control: the two modules must overlap substantially, or the comparison is between unrelated
    # objects and "superset" would be a meaningless claim.
    assert len(admission_names & route_names) > 50, "modules share too little to be related at all"

    assert admission_names - route_names, "admission.py carries no name the route module lacks"


def test_d6_the_registry_divergence_between_the_two_modules_is_exactly_the_known_one():
    """Found while repairing D6, and larger than D6 recorded: the registries genuinely DIVERGE.

    D6 said parity is asserted "on the shared numeric core only". That understates it — the sleeve
    registries themselves disagree, on a live-relevant field. As first written, this test recorded:

        admission.SLEEVE_REGISTRY["crypto"].symbols == ("BTCUSD", "DASHUSD")
        route     SLEEVE_REGISTRY["crypto"].symbols == ("BTCUSD", "DASHUSD", "ETHUSD")

    `tests/ultimate_book/test_vendor_parity.py::test_admission_parity` does not catch this, because
    its four-intent fixture uses BTCUSD for crypto and never touches the symbol the two modules
    disagree about. It therefore reports "parity" over a universe on which parity is not in question
    — the same shape as the B41 vacuous tests, on the module comparison D6 is about.

    CLOSED ON THE `symbols` AXIS 2026-08-11 (owner-authorized, lane B7). ETHUSD was added back to
    the live crypto surface on measured evidence, so the live authority and its route ancestor now
    agree on the symbol universe and only the prose `note` still differs. Read the direction
    honestly: the route ancestor was not "stale", it was carrying the surface the estate has now
    re-measured and re-adopted — the drop was the deviation.

    This test enumerates the divergence rather than asserting equality, so a NEW divergence — which
    would be a real problem — turns it red while the known one stays green.
    """
    route = pytest.importorskip(
        "research.operations.final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
        ".ultimate_book_live_package",
        reason="route ancestor module not present in this checkout",
    )
    known = {("crypto", "note")}
    # the `symbols` divergence is CLOSED: assert the agreement directly, so re-opening it fails
    # here with a clear message rather than only through the set comparison below.
    assert tuple(P.SLEEVE_REGISTRY["crypto"].symbols) == \
        tuple(route.SLEEVE_REGISTRY["crypto"].symbols) == ("BTCUSD", "DASHUSD", "ETHUSD")
    found = set()
    a, b = P.SLEEVE_REGISTRY, route.SLEEVE_REGISTRY
    assert set(a) == set(b), "the two registries no longer even carry the same sleeves"
    for name in sorted(a):
        for fld in a[name].__dataclass_fields__:
            if getattr(a[name], fld) != getattr(b[name], fld):
                found.add((name, fld))
    assert found == known, (
        f"registry divergence changed: expected {sorted(known)}, found {sorted(found)}. "
        f"A NEW divergence between the live authority and its route ancestor is a real finding."
    )


# ---------------------------------------------------------------------------------------------
# D7 — derisk_start_dd_pct is configured, visible, and inert in the mode live runs
# ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize("dd", [0.0, 0.01, 0.05, 0.069, 0.071, 0.09])
def test_d7_derisk_start_dd_pct_is_inert_in_smooth_mode(dd):
    """Makes the inertness CHECKED rather than asserted in prose.

    `agent_config.yaml:1333` sets `derisk_start_dd_pct: 0.07` with the comment "shrink size from -7%
    toward the -10% wall", and live runs `derisk_mode: smooth` (`:1340`; all 99,112 recorded packets
    agree). In smooth mode `evaluate_governor` takes the `if` branch and the key appears only in the
    `elif`/`else`, so size shrinks from the FIRST BASIS POINT of drawdown, not from -7%. An operator
    reading the config today would believe the opposite.

    Deliberately NOT repaired by making the smooth branch reject a set key: live sets BOTH, so that
    would fail the live book closed. The config comment is the honest repair and `agent_config.yaml`
    is decision-contract-bound (H1), so it is prepared for the owner rather than landed here.
    """
    equity = 100_000.0 * (1.0 - dd)
    state = GovernorState(equity=equity, high_water=100_000.0, realized_today_pct=0.0,
                          open_risk_pct=0.0, max_dd_reference_equity=100_000.0)

    def mult(start):
        limits = GovernorLimits(**{**DEFAULT_LIMITS.__dict__,
                                   "derisk_mode": "smooth", "derisk_start_dd_pct": start})
        return evaluate_governor(state, limits=limits).size_cap_multiplier

    assert mult(0.07) == mult(0.0) == mult(0.99), (
        "derisk_start_dd_pct changed the smooth-mode multiplier; D7's premise no longer holds"
    )

    # POSITIVE CONTROL: the key is NOT inert in band mode. Without this the assertion above would
    # also pass against a governor that ignored the key everywhere, or one whose multiplier was a
    # constant — neither of which is what is being claimed.
    def band_mult(start):
        limits = GovernorLimits(**{**DEFAULT_LIMITS.__dict__,
                                   "derisk_mode": "band", "derisk_start_dd_pct": start})
        return evaluate_governor(state, limits=limits).size_cap_multiplier

    if dd > 0.0:
        assert band_mult(0.0) != band_mult(0.09), (
            "control failed: derisk_start_dd_pct does nothing in band mode either, so the smooth-mode "
            "assertion above is vacuous"
        )


def test_d7_smooth_mode_derisks_from_the_first_basis_point_not_from_seven_percent():
    """States the operator-visible consequence directly: there is no full-size band below -7%."""
    limits = GovernorLimits(**{**DEFAULT_LIMITS.__dict__,
                               "derisk_mode": "smooth", "derisk_start_dd_pct": 0.07})
    tiny_dd = GovernorState(equity=99_900.0, high_water=100_000.0, realized_today_pct=0.0,
                            open_risk_pct=0.0, max_dd_reference_equity=100_000.0)
    assert evaluate_governor(tiny_dd, limits=limits).size_cap_multiplier < 1.0

    flat = GovernorState(equity=100_000.0, high_water=100_000.0, realized_today_pct=0.0,
                         open_risk_pct=0.0, max_dd_reference_equity=100_000.0)
    assert evaluate_governor(flat, limits=limits).size_cap_multiplier == 1.0  # control: 0 dd = full size


# ---------------------------------------------------------------------------------------------
# D8 — bridge.DEFAULT_CONFIG disagreed with the live YAML on the two keys that decide the dial
# ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize("missing", REQUIRED_DIAL_KEYS)
def test_d8_an_enabled_book_fails_closed_on_any_missing_dial_key(missing):
    """Refusal beats a mis-sized book.

    `DEFAULT_CONFIG` defaults the profile to the 1.25% first-cycle dial where live runs the 2.00%
    ceiling, and derisk_mode to "band" where live runs "smooth" — exactly the pair the ceiling
    interlock checks. A caller falling back to them would size at 62% of the live dial, or fail the
    whole book closed, and would not be told which.
    """
    cfg = _engine_cfg()
    cfg.pop(missing)
    decision = evaluate_vnext_ultimate_book_admission(
        config={"gtos_vnext_runtime": cfg}, intents=[_crypto()],
        governor_state=GovernorState(100_000.0, 100_000.0, 0.0, 0.0),
    )
    assert decision.decision_status == "fail_closed_missing_dial_keys"
    assert missing in decision.reason
    assert decision.realized_units == [] and decision.would_units == []


def test_d8_a_complete_dial_is_not_refused():
    """Control for the parametrised test above: it must be the ABSENCE that triggers refusal."""
    decision = evaluate_vnext_ultimate_book_admission(
        config={"gtos_vnext_runtime": _engine_cfg()}, intents=[_crypto()],
        governor_state=GovernorState(100_000.0, 100_000.0, 0.0, 0.0),
    )
    assert decision.decision_status != "fail_closed_missing_dial_keys"


def test_d8_a_disabled_book_is_not_refused_for_a_missing_dial_key():
    """The guard is scoped to enabled=True on purpose; a disabled book already bears zero risk."""
    cfg = _engine_cfg(ultimate_book_enabled=False)
    cfg.pop("ultimate_book_profile")
    decision = evaluate_vnext_ultimate_book_admission(
        config={"gtos_vnext_runtime": cfg}, intents=[_crypto()],
        governor_state=GovernorState(100_000.0, 100_000.0, 0.0, 0.0),
    )
    assert decision.decision_status != "fail_closed_missing_dial_keys"


def test_d8_required_dial_keys_match_the_replay_policy_list():
    """The live bridge and the replay policy must not disagree about what a complete dial is."""
    from src.research_infra.replay_policy.sleeve_book import SleeveBookPolicy
    assert set(REQUIRED_DIAL_KEYS) == set(SleeveBookPolicy.DIAL_KEYS)


# ---------------------------------------------------------------------------------------------
# D10 — account is hard-wired to "A", so risk_per_unit_B is unreachable
# ---------------------------------------------------------------------------------------------

def test_d10_asymmetric_profile_without_an_explicit_account_fails_closed():
    """Converts a silent 2x risk error on one account into a named refusal.

    `staggered_1p00_0p50` sizes A at 1.00% and B at 0.50%. With the side hard-wired to "A" and
    `book_owner.py` never passing one, BOTH live namespaces would run 1.00% — a 2x error on one
    account with no error message. Choosing which account gets which side is the owner's decision,
    so the repair is the refusal, not the derivation.
    """
    prof = ALLOCATION_PROFILES["staggered_1p00_0p50"]
    assert prof.risk_per_unit_A != prof.risk_per_unit_B, "fixture is no longer asymmetric"

    guard = _engine(ultimate_book_profile="staggered_1p00_0p50")._asymmetric_profile_guard()
    assert guard is not None and "asymmetric_profile_without_explicit_account" in guard


def test_d10_an_explicit_account_is_allowed_through():
    """Control: it is the ABSENCE of a chosen side that refuses, not the profile itself."""
    eng = UltimateBookLiveEngine(
        _engine_cfg(ultimate_book_profile="staggered_1p00_0p50"), object(), tempfile.mkdtemp(),
        account="B",
    )
    assert eng._asymmetric_profile_guard() is None
    assert eng._account == "B"


def test_d10_balanced_profiles_are_never_refused():
    """Every dial live today is balanced, so the guard must be completely silent on them."""
    for name, prof in ALLOCATION_PROFILES.items():
        if prof.risk_per_unit_A != prof.risk_per_unit_B:
            continue
        assert _engine(ultimate_book_profile=name)._asymmetric_profile_guard() is None, name

    # Control: the loop above must have actually examined the live dial.
    live = ALLOCATION_PROFILES["clean3_w7_ceiling_nom2p00"]
    assert live.risk_per_unit_A == live.risk_per_unit_B


def test_d10_the_default_side_is_still_a():
    """The guard must not have changed sizing on any balanced dial — "A" stays the effective default."""
    assert _engine()._account == "A"


# ---------------------------------------------------------------------------------------------
# D11 — when a gate blocks, the bridge discarded the reason the SIZING refused
# ---------------------------------------------------------------------------------------------

def test_d11_a_gated_book_still_reports_why_the_sizing_would_have_refused():
    """"We are not armed" and "we are not armed AND the dial is uncertified" are different facts.

    The 2.0% ceiling is only certified ruin-safe with smooth DD-defense, so pairing it with band
    defense makes `admit_and_size` refuse before the governor ever runs. Gated off, the top-level
    `reason` reports only the gate. Before D11 the sizing verdict was carried nowhere.
    """
    cfg = _engine_cfg(ultimate_book_profile="clean3_w7_ceiling_nom2p00",
                      ultimate_book_derisk_mode="band",
                      ultimate_book_apply_to_execution=True,
                      ultimate_book_live_activation_allowed=False)
    decision = evaluate_vnext_ultimate_book_admission(
        config={"gtos_vnext_runtime": cfg}, intents=[_crypto()],
        governor_state=GovernorState(100_000.0, 100_000.0, 0.0, 0.0),
    )
    assert decision.decision_status == "shadow_live_activation_not_allowed"
    assert decision.reason == "ultimate_book_live_activation_allowed_false"
    assert decision.sizing_reason == "ceiling_profile_requires_smooth_ddefense"


def test_d11_sizing_reason_reports_ok_when_only_the_gate_refused():
    """Control: `sizing_reason` must DISTINGUISH the two cases, not always echo a refusal.

    Note what supplying `limits` is doing here, because it is the whole point of D11. The bridge does
    NOT build `GovernorLimits` from `ultimate_book_derisk_mode` — it only RECORDS that key. The limits
    arrive from the caller, and the live engine is what reads the config into them
    (`book_engine.py:593-594`). So a caller that drives the bridge directly with `DEFAULT_LIMITS`
    while its config says `derisk_mode: smooth` silently gets BAND defense, and the 2.0% ceiling
    interlock refuses the whole book.

    That is exactly the replay-a-gated-config situation D11 says it bites on, and before the repair
    the resulting decision reported only the gate. The two tests together now separate a config that
    would size from one that would not.
    """
    smooth_limits = GovernorLimits(**{**DEFAULT_LIMITS.__dict__, "derisk_mode": "smooth"})
    cfg = _engine_cfg(ultimate_book_profile="clean3_w7_ceiling_nom2p00",
                      ultimate_book_derisk_mode="smooth",
                      ultimate_book_apply_to_execution=True,
                      ultimate_book_live_activation_allowed=False)
    decision = evaluate_vnext_ultimate_book_admission(
        config={"gtos_vnext_runtime": cfg}, intents=[_crypto()],
        governor_state=GovernorState(100_000.0, 100_000.0, 0.0, 0.0),
        limits=smooth_limits,
    )
    assert decision.decision_status == "shadow_live_activation_not_allowed"
    assert decision.sizing_reason != "ceiling_profile_requires_smooth_ddefense"


def test_d11_sizing_reason_is_none_when_sizing_was_never_attempted():
    """The pre-sizing fail-closed branches have no sizing verdict, and must not invent one."""
    cfg = _engine_cfg(ultimate_book_profile="a_profile_that_does_not_exist")
    decision = evaluate_vnext_ultimate_book_admission(
        config={"gtos_vnext_runtime": cfg}, intents=[_crypto()],
        governor_state=GovernorState(100_000.0, 100_000.0, 0.0, 0.0),
    )
    assert decision.decision_status == "fail_closed_unknown_profile"
    assert decision.sizing_reason is None
