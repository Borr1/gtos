"""Behavioural tests for the two proposed exit-contract activations (Session AS, AS-2).

Both candidate diffs are applied **in memory** and driven through the real
`build_book_trade_params`, so these tests exist and pass BEFORE any spec byte moves. That order is
not incidental: test 1 asks "does the edit do anything at all", and it can only prove that against
a tree where the edit has not landed.

The failure mode this file exists to prevent, stated once:

    `mx_btcusd_d1_donchian_20_breakout` carries `final_from_intent=True`. At
    execution_packets.py:249-256 that wins over the profile's own `final_target_r`, which is never
    read at :260. So setting `final_target_r=5.0` on this cohort leaves the BROKER TAKE-PROFIT at
    2R — the sleeve would be armed on the contract its own evidence REJECTS at every band, while
    the spec, the diff and the commit message all said 5R.

    CORRECTED after an adversarial pass: an earlier version of this docstring said "every log said
    5R" and that is FALSE. `build_book_trade_params` writes the RESOLVED 2.0 into
    `gtos_vnext_dynamic_final_target_r` (execution_packets.py:353), which is what `book_owner.py`
    persists and emits — so the runtime telemetry would correctly read 2R. The discrepancy is
    spec-versus-log and the log is the one telling the truth.

    ALSO NARROWED: there are TWO production resolvers, and only one of them is guarded.
    `native_policy_instrumentation` (execution_packets.py:152-181) reads `final_target_r` at
    :165-166 with NO `final_from_intent` guard, so under the naive edit it DOES resolve 5.0 and
    `book_owner.py` persists it on the adopt-missing-record path. It could not previously reach a
    broker, because the hydrator raised `KeyError('trigger_r')` first — and Session AS FIXED that
    (B1535), so this divergence is now reachable and is pinned below.

`test_the_naive_mx_edit_is_a_noop` is the regression guard on that. If it ever starts FAILING, the
resolution order in `execution_packets.py` has changed and the activation dossier's central claim
must be re-derived before anything is landed.
"""
from __future__ import annotations

import copy

import pytest

from src.components.ultimate_book.execution_packets import (
    DEFAULT_EXIT_PROFILE,
    RESEARCH_HORIZON_NATIVE_BARS,
    SLEEVE_EXIT_PROFILES,
    build_book_trade_params,
    time_stop_m15,
)
from src.components.ultimate_book.sleeves.market_expansion_d1 import TAG_TO_RULE, TARGET_R

BTC = "mx_btcusd_d1_donchian_20_breakout"
XVOL = "sub_xvol_pullback"
#: the five sleeves on live money (phase8/receipts/FIVE_SLEEVE_EXPANSION_20260730.md, host f855250cd)
ARMED = ("crypto", "energy_agri", "sub_xvol_pullback", "fx_jpy", "sub_mid_dn_revert")

ENTRY, RISK = 100_000.0, 1_000.0


class _Intent:
    symbol = "BTCUSD"
    direction = 1
    decision_day = "2026-07-30"

    def __init__(self, sleeve, target_dist, stop_dist=RISK):
        self.sleeve, self.target_dist, self.stop_dist = sleeve, target_dist, stop_dist


class _Sized:
    risk_pct_per_trade = 0.005
    cluster = "book"
    sleeve_members = ()
    confidence = 0.025
    n_trades = 232


ACCOUNT = {"balance": 100_000.0, "equity": 100_000.0, "day_start_equity": 100_000.0,
           "initial_capital": 100_000.0, "static_dd_floor": 90_000.0}
GEOMETRY = {"entry_price": ENTRY, "risk_distance": RISK, "stop_loss": ENTRY - RISK}


def resolve(sleeve: str, *, intent_target_mult: float = 2.0) -> dict:
    """The exit fields the live engine would place for `sleeve`, under whatever profile is current."""
    tp = build_book_trade_params(
        _Sized(), _Intent(sleeve, intent_target_mult * RISK), GEOMETRY, ACCOUNT,
        profile_namespace="operator_profile")
    return {
        "final_target_r": tp["gtos_vnext_dynamic_final_target_r"],
        "take_profit_1": tp["take_profit_1"],
        "time_stop_bars": tp.get("gtos_vnext_dynamic_time_stop_bars"),
        "policy": tp["gtos_vnext_dynamic_policy_selected"],
        "broker_take_profit_mode": tp["gtos_vnext_dynamic_broker_take_profit_mode"],
    }


def resolve_all(*, intent_target_mult: float = 2.0) -> dict:
    return {s: resolve(s, intent_target_mult=intent_target_mult)
            for s in sorted(SLEEVE_EXIT_PROFILES)}


@pytest.fixture
def profiles():
    """Mutate SLEEVE_EXIT_PROFILES inside a test and have it restored, whatever happens."""
    saved = copy.deepcopy(SLEEVE_EXIT_PROFILES)
    try:
        yield SLEEVE_EXIT_PROFILES
    finally:
        SLEEVE_EXIT_PROFILES.clear()
        SLEEVE_EXIT_PROFILES.update(saved)


# ---------------------------------------------------------------------------
# test 1 — the edit must do something, and the naive one does not
# ---------------------------------------------------------------------------
def test_the_naive_mx_edit_is_a_noop(profiles):
    """THE regression guard. If this starts failing, execution_packets.py's resolution order has
    changed and the activation dossier must be re-derived before anything lands."""
    before = resolve(BTC)
    assert before["final_target_r"] == 2.0
    profiles[BTC] = dict(profiles[BTC], final_target_r=5.0)
    after = resolve(BTC)
    assert after == before, (
        "the naive profile edit is no longer a no-op — the dossier's central claim has changed")


def test_the_correct_mx_diff_moves_the_broker_take_profit(profiles):
    profiles[BTC] = {k: v for k, v in profiles[BTC].items() if k != "final_from_intent"} \
        | {"final_target_r": 5.0}
    got = resolve(BTC)
    assert got["final_target_r"] == 5.0
    assert got["take_profit_1"] == pytest.approx(ENTRY + 5.0 * RISK)
    assert got["broker_take_profit_mode"] == "final_target"


def test_the_xvol_diff_moves_the_broker_take_profit(profiles):
    assert resolve(XVOL)["final_target_r"] == 3.0
    profiles[XVOL] = dict(profiles[XVOL], final_target_r=4.0)
    got = resolve(XVOL)
    assert got["final_target_r"] == 4.0
    assert got["take_profit_1"] == pytest.approx(ENTRY + 4.0 * RISK)


def test_the_mx_diff_leaves_the_repaired_time_stop_alone(profiles):
    """AQ's B1404 repair is the OTHER half of the admission; a target diff must not disturb it."""
    expected = time_stop_m15(RESEARCH_HORIZON_NATIVE_BARS, "D1")
    assert expected == 7680
    assert resolve(BTC)["time_stop_bars"] == expected
    profiles[BTC] = {k: v for k, v in profiles[BTC].items() if k != "final_from_intent"} \
        | {"final_target_r": 5.0}
    assert resolve(BTC)["time_stop_bars"] == expected


# ---------------------------------------------------------------------------
# test 2 — the no-op cannot be silently re-introduced
# ---------------------------------------------------------------------------
def test_final_from_intent_and_final_target_r_are_mutually_exclusive_by_construction(profiles):
    """A profile that sets BOTH is a latent no-op: the second value is dead. This asserts the
    property directly, so the trap is described rather than only worked around."""
    profiles[BTC] = dict(profiles[BTC], final_from_intent=True, final_target_r=5.0)
    assert resolve(BTC)["final_target_r"] == 2.0, "final_from_intent silently won"
    profiles[BTC] = {k: v for k, v in profiles[BTC].items() if k != "final_from_intent"}
    assert resolve(BTC)["final_target_r"] == 5.0


def test_every_profile_that_sets_both_keys_is_enumerated():
    """The cohort of sleeves whose declared `final_target_r` is currently DEAD CODE.

    Not a failure — several are deliberate (the fallback matters on the adopt-missing-record path,
    documented at execution_packets.py:158-161). But it must be a KNOWN list, because a future
    session reading one of these numbers as the live target would be reading a value the engine
    never uses.
    """
    both = sorted(s for s, p in SLEEVE_EXIT_PROFILES.items()
                  if p.get("final_from_intent") and p.get("final_target_r") is not None)
    # STALE EXPECTATION fixed 2026-08-25: `asian_fade_widen` and `orb_crypto_london_widen`
    # joined the cohort with the WIDEN wrapper ceremony (commit 68ca70e40, "Ceremony
    # 20260825 S1: three WIDEN wrapper sleeves beside incumbents", wrapper tests in
    # test_widen_wrappers.py). CHECKED per this test's own instruction: both carry
    # `final_from_intent=True` DELIBERATELY — the wrapper takes its target from the intent
    # by design, and the declared 2.0 is the documented adopt-missing-record fallback
    # (execution_packets.py:158-161), the exact shape incumbent `orb_crypto_london`
    # already had. Not a latent no-op like the mx_* cohort was. The third wrapper,
    # `ny_crypto_momentum_widen`, sets final_target_r=None and correctly stays out.
    assert both == sorted([
        "asia_pdl_fade", "asian_fade_widen", "liq_asia_up_low_metal", "orb_crypto_london",
        "orb_crypto_london_widen", "vol_compression", "vss_fxcross_london_up_low",
        *TAG_TO_RULE,
    ]), ("a profile gained or lost the dead-final_target_r property; update this list and check "
         "whether the new one is a latent no-op like the mx_* cohort was")
    # and none of them is armed
    assert not [s for s in both if s in ARMED]


# ---------------------------------------------------------------------------
# test 3 — the blast radius is exactly the named sleeve
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name,sleeve,override", [
    ("mx_btcusd_profile_route", BTC, "drop_intent_set_5R"),
    ("sub_xvol_target_4R", XVOL, "set_4R"),
])
def test_blast_radius_is_exactly_one_sleeve(profiles, name, sleeve, override):
    before = resolve_all()
    if override == "drop_intent_set_5R":
        profiles[sleeve] = {k: v for k, v in profiles[sleeve].items()
                            if k != "final_from_intent"} | {"final_target_r": 5.0}
    else:
        profiles[sleeve] = dict(profiles[sleeve], final_target_r=4.0)
    after = resolve_all()
    moved = sorted(s for s in set(before) | set(after) if before.get(s) != after.get(s))
    assert moved == [sleeve], f"{name} reached sleeves it does not name: {moved}"


def test_the_generator_route_is_not_scoped_to_one_sleeve():
    """Route B changes a MODULE constant every mx_* generator reads. Recorded so nobody proposes it
    as the surgical option."""
    assert TARGET_R == 2.0
    assert len(TAG_TO_RULE) == 14
    assert BTC in TAG_TO_RULE
    assert not [s for s in TAG_TO_RULE if s in ARMED]


# ---------------------------------------------------------------------------
# test 4 — live money does not move
# ---------------------------------------------------------------------------
def test_the_mx_diff_moves_no_armed_sleeve(profiles):
    before = {s: resolve(s) for s in ARMED}
    profiles[BTC] = {k: v for k, v in profiles[BTC].items() if k != "final_from_intent"} \
        | {"final_target_r": 5.0}
    assert {s: resolve(s) for s in ARMED} == before


def test_the_xvol_diff_moves_exactly_one_armed_sleeve_and_it_is_the_named_one(profiles):
    """Not a defect — it is the whole reason that change is an owner decision and not a merge."""
    before = {s: resolve(s) for s in ARMED}
    profiles[XVOL] = dict(profiles[XVOL], final_target_r=4.0)
    after = {s: resolve(s) for s in ARMED}
    moved = sorted(s for s in ARMED if before[s] != after[s])
    assert moved == [XVOL]
    assert after[XVOL]["final_target_r"] == 4.0 and before[XVOL]["final_target_r"] == 3.0


# ---------------------------------------------------------------------------
# test 6 — coverage, so tests 3/4 cannot silently stop covering the registry
# ---------------------------------------------------------------------------
def test_every_armed_sleeve_has_an_explicit_exit_profile():
    """An armed sleeve falling through to DEFAULT_EXIT_PROFILE would carry a 2R target and a
    1280-bar stop nobody chose for it."""
    for s in ARMED:
        assert s in SLEEVE_EXIT_PROFILES, f"{s} is armed and falls through to the default profile"


def test_the_registry_size_is_pinned_so_the_blast_radius_test_keeps_covering_it():
    """`resolve_all` diffs whatever is in the registry. If a sleeve is added and this number is not
    updated, the blast-radius tests silently stop covering it."""
    # STALE EXPECTATION fixed 2026-08-25: 34 -> 68. Two deliberate additions on this tree
    # (f5max-ship, the live F5 book source):
    #   +31 F5 full-surface sleeves (25 dsp_* + 6 xa_*) — commit 338553883, "f5max-base:
    #       live code surface of f5-live@68bad3751 overlaid";
    #   +3 *_widen wrapper sleeves — commit 68ca70e40, "Ceremony 20260825 S1: three WIDEN
    #       wrapper sleeves beside incumbents" (asian_fade_widen, ny_crypto_momentum_widen,
    #       orb_crypto_london_widen; contracts pinned by test_widen_wrappers.py).
    # Coverage CONFIRMED before repinning: `resolve_all` iterates
    # `sorted(SLEEVE_EXIT_PROFILES)`, so the blast-radius tests above diff all 68 — they
    # pass at the new size with no sleeve excluded.
    assert len(SLEEVE_EXIT_PROFILES) == 68, (
        f"the exit-profile registry is now {len(SLEEVE_EXIT_PROFILES)}; confirm the blast-radius "
        f"tests still cover every sleeve, then update this number")


def test_the_default_profile_is_unchanged_by_either_diff(profiles):
    before = dict(DEFAULT_EXIT_PROFILE)
    profiles[XVOL] = dict(profiles[XVOL], final_target_r=4.0)
    profiles[BTC] = {k: v for k, v in profiles[BTC].items() if k != "final_from_intent"} \
        | {"final_target_r": 5.0}
    resolve_all()
    assert dict(DEFAULT_EXIT_PROFILE) == before


# ---------------------------------------------------------------------------
# the seal answer, asserted rather than remembered
# ---------------------------------------------------------------------------
def test_neither_touched_file_is_bound_by_any_seal_mechanism():
    """The dossier's H1/R2 answer. If a future contract binds either file, this fails and the
    'no owner question to route' conclusion has to be re-derived."""
    import hashlib
    import json
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    touched = ("src/components/ultimate_book/execution_packets.py",
               "src/components/ultimate_book/sleeves/market_expansion_d1.py")
    for contract in ("B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json",
                     "B7_5_POST_ACCELERATION_DECISION_CONTRACT.json"):
        p = repo / ("research/operations/"
                    "final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16") / contract
        if not p.is_file():
            pytest.skip(f"{contract} absent from this worktree's sparse profile")
        ib = json.loads(p.read_text())["input_bindings"]
        bound = {r["path"] for g in ("common_behavior_inputs", "package_authority_inputs")
                 for r in ib.get(g, [])}
        for f in touched:
            assert f not in bound, f"{f} is now bound by {contract}; the dossier's seal answer moved"
        # and the contract itself must still be the one the dossier measured against
        assert hashlib.sha256(p.read_bytes()).hexdigest()

    runner = repo / "src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py"
    src = runner.read_text()
    start = src.index("code_authority_paths = (")
    block = src[start:src.index(")", src.index("verify_denominator_to_deployment_execution.py"))]
    for f in touched:
        assert f not in block, f"{f} is now in code_authority_paths; the seal answer moved"
    cfg_start = src.index('"config_file_hashes": {')
    cfg_block = src[cfg_start:src.index("}", cfg_start)]
    for f in touched:
        assert f not in cfg_block


# ---------------------------------------------------------------------------
# the SECOND production resolver, which the blast-radius instrument did not cover
# ---------------------------------------------------------------------------
def test_native_policy_instrumentation_is_the_unguarded_resolver(profiles):
    """`build_book_trade_params` honours `final_from_intent`; `native_policy_instrumentation` does
    NOT. Under the naive edit the two DISAGREE — 2.0 at the broker, 5.0 in the rehydration payload.

    That divergence used to be inert: the hydrator raised `KeyError('trigger_r')` on every
    `time_stop` record before it could reach `_modify_tp`. Session AS fixed that (B1535), so the
    divergence is now REACHABLE, and it is a second reason the naive edit must never be landed.
    """
    from src.components.ultimate_book.execution_packets import native_policy_instrumentation

    assert resolve(BTC)["final_target_r"] == 2.0
    assert native_policy_instrumentation(BTC)["gtos_vnext_dynamic_final_target_r"] == 2.0

    profiles[BTC] = dict(profiles[BTC], final_target_r=5.0)      # the naive edit
    assert resolve(BTC)["final_target_r"] == 2.0, "the broker TP correctly stays at 2R"
    assert native_policy_instrumentation(BTC)["gtos_vnext_dynamic_final_target_r"] == 5.0, \
        "the rehydration payload takes the profile value unguarded — the two resolvers diverge"


def test_the_recommended_route_a_makes_both_resolvers_agree(profiles):
    """The positive half, and the reason Route A is the recommendation rather than a preference:
    dropping `final_from_intent` is the ONLY form of the change under which the broker TP and the
    rehydration payload carry the same number."""
    from src.components.ultimate_book.execution_packets import native_policy_instrumentation

    profiles[BTC] = {k: v for k, v in profiles[BTC].items() if k != "final_from_intent"} \
        | {"final_target_r": 5.0}
    assert resolve(BTC)["final_target_r"] == 5.0
    assert native_policy_instrumentation(BTC)["gtos_vnext_dynamic_final_target_r"] == 5.0


@pytest.mark.parametrize("sleeve", ARMED)
def test_the_two_resolvers_agree_for_every_armed_sleeve_as_committed(sleeve):
    """No armed sleeve currently sits on the divergence. If one ever does, this fails."""
    from src.components.ultimate_book.execution_packets import native_policy_instrumentation

    assert resolve(sleeve)["final_target_r"] == pytest.approx(
        native_policy_instrumentation(sleeve)["gtos_vnext_dynamic_final_target_r"]), sleeve
