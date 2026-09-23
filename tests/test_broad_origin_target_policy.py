"""The take-profit is a declared decision, not an inherited risk floor.

WHAT THIS PINS, and why each test exists rather than a source grep.

Until 2026-08-07 `broader_origin_generators._target_rr` read `risk.min_rr` -- a key whose own
config comment (`config/agent_config.yaml:39`) calls it a *"vNext sanity floor only"* -- and
that single scalar became `take_profit_1` for every broader-origin family. Two consequences,
both pinned below:

* moving the RISK dial moved eleven EXIT contracts, silently (`test_min_rr_no_longer_moves_*`);
* no family's target had a provenance anyone could read (`test_provenance_*`).

`test_min_rr_no_longer_moves_the_declared_target` and
`test_unregistered_family_fails_loud_instead_of_inheriting_the_floor` FAIL against the
pre-repair implementation. That is deliberate: a test that passes against the old code proves
the change is different, not that it is a fix.

`test_default_path_preserves_legacy_geometry` is the inertness proof: with the
key absent, the legacy geometry and legacy candidate-id payload are unchanged.
Additive target provenance and identity receipts are intentionally present.
"""

from __future__ import annotations

import datetime as dt

import pytest

from src.components.broader_origin_generators import (
    FAMILY_TARGET_RR,
    PRODUCTION_ORIGIN_FAMILIES,
    TARGET_POLICY_ENABLE_KEY,
    Bar,
    BarSeries,
    CURRENT_FRAMEWORK_ORIGIN_FAMILY,
    SESSION_WINDOWS,
    TargetRRPolicy,
    _canonical_symbol,
    _generate_single_symbol_candidates,
    _target_rr,
)


def _cfg(min_rr=1.5, enabled=None):
    cfg = {"risk": {"min_rr": min_rr}}
    if enabled is not None:
        cfg["gtos_vnext_runtime"] = {TARGET_POLICY_ENABLE_KEY: enabled}
    return cfg


def _series(symbol="EURUSD", n=200, seed=7):
    """A deterministic synthetic M15 series rich enough to fire several families."""
    import random

    rng = random.Random(seed)
    t0 = dt.datetime(2026, 1, 5, 0, 0, tzinfo=dt.timezone.utc)
    px = 1.1000
    bars = []
    for i in range(n):
        drift = 0.0006 * (1 if (i // 17) % 2 == 0 else -1)
        o = px
        c = px + drift + rng.uniform(-0.0004, 0.0004)
        h = max(o, c) + rng.uniform(0.0, 0.0006)
        lo = min(o, c) - rng.uniform(0.0, 0.0006)
        bars.append(Bar(time=t0 + dt.timedelta(minutes=15 * i), open=o, high=h,
                        low=lo, close=c, volume=100.0))
        px = c
    return BarSeries(symbol=symbol, timeframe="M15", bars=tuple(bars),
                     source_path_feature_status="complete",
                     session_windows=SESSION_WINDOWS.get(_canonical_symbol(symbol), ()))


def _emit(cfg, series=None, mined=True):
    series = series or _series()
    rr = _target_rr(cfg)
    out = []
    for i in range(51, len(series.bars)):
        out.extend(_generate_single_symbol_candidates(
            series=series, index=i, target_rr=rr, kill_zone="none",
            enable_mined_families=mined, enable_microstructure=False,
        ))
    return out


# ---------------------------------------------------------------- the inertness proof

def test_default_path_preserves_legacy_geometry():
    """Key absent preserves legacy target geometry while naming its provenance."""
    cands = _emit(_cfg(min_rr=1.5))
    assert cands, "fixture must emit candidates or the test proves nothing"
    for c in cands:
        risk = abs(c.entry_price - c.stop_loss)
        want = (c.entry_price + 1.5 * risk if c.side == "LONG"
                else c.entry_price - 1.5 * risk)
        assert c.take_profit_1 == pytest.approx(want, rel=0, abs=1e-12)
        assert c.risk_reward_ratio == 1.5
        assert c.rr == 1.5
        decision = c.source_fields["target_decision"]
        assert decision["target_rr"] == 1.5
        assert decision["source"] == "risk_min_rr_inherited_as_target"


def test_default_path_still_tracks_min_rr():
    """The legacy coupling is preserved EXACTLY while the policy is off -- no silent change."""
    for rr in (1.5, 2.0, 3.25):
        for c in _emit(_cfg(min_rr=rr)):
            assert c.risk_reward_ratio == rr


def test_policy_object_is_the_legacy_scalar():
    p = _target_rr(_cfg(min_rr=2.0))
    assert isinstance(p, TargetRRPolicy)
    assert isinstance(p, float)
    assert p == 2.0
    assert p * 3 == 6.0
    assert not p.enabled


# ------------------------------------------------- the tests that FAIL against the old code

def _legacy_target_rr(cfg) -> float:
    """The pre-2026-08-07 resolver, verbatim, as the A/B reference.

    Encoded here rather than imported so this comparison keeps working after the old symbol is
    gone, and so an ImportError can never be mistaken for a behavioural difference:

        def _target_rr(config):
            risk = config.get("risk") if isinstance(config, dict) else {}
            rr = _fnum((risk or {}).get("min_rr") if isinstance(risk, dict) else None)
            return rr if rr is not None and rr > 0 else 1.5
    """
    risk = cfg.get("risk") if isinstance(cfg, dict) else {}
    rr = (risk or {}).get("min_rr") if isinstance(risk, dict) else None
    try:
        rr = float(rr)
    except (TypeError, ValueError):
        rr = None
    return rr if rr is not None and rr > 0 else 1.5


@pytest.mark.parametrize("min_rr", [0.5, 1.0, 1.5, 2.0, 3.25])
def test_ab_against_the_legacy_resolver(min_rr):
    """The whole repair in one assertion, both ways round.

    OFF  -> new behaviour is the legacy behaviour, at every min_rr (the inertness proof).
    ON   -> the two DIVERGE exactly where the legacy resolver let a risk floor act as a target,
            and agree exactly where the floor is genuinely binding.
    """
    legacy = _legacy_target_rr(_cfg(min_rr))

    off = {c.risk_reward_ratio for c in _emit(_cfg(min_rr))}
    assert off == {legacy}, "policy OFF must reproduce the legacy resolver exactly"

    on = {c.risk_reward_ratio for c in _emit(_cfg(min_rr, enabled=True))}
    declared = {rr for rr, _b, _p in FAMILY_TARGET_RR.values()}
    expected = {max(rr, min_rr) for rr in declared}
    assert on == expected

    if min_rr < max(declared):
        # the case the repair exists for: the legacy resolver would have shipped the FLOOR as
        # the take-profit; the declared policy does not.
        assert on != off, (
            f"at min_rr={min_rr} the legacy resolver gives {legacy} for every family; "
            f"the declared policy gives {sorted(on)}"
        )


def test_min_rr_no_longer_moves_the_declared_target():
    """THE REPAIR. With the policy on, changing the RISK floor upward floors the target (its
    documented job) but changing it DOWNWARD no longer drags eleven exit contracts with it.

    Against the pre-repair implementation every candidate's rr equals min_rr at both values, so
    this assertion fails.
    """
    low = {c.candidate_id: c.risk_reward_ratio for c in _emit(_cfg(0.5, enabled=True))}
    mid = {c.candidate_id: c.risk_reward_ratio for c in _emit(_cfg(1.5, enabled=True))}
    assert low, "fixture must emit candidates"
    # min_rr 0.5 is BELOW every declared target, so the declared target stands: 1.5, not 0.5.
    assert set(low.values()) == {1.5}
    assert set(mid.values()) == {1.5}
    # ... and the pre-repair behaviour would have been 0.5 here.
    assert 0.5 not in set(low.values())


def test_min_rr_floors_the_declared_target_which_is_its_documented_job():
    hi = _emit(_cfg(4.0, enabled=True))
    assert hi
    for c in hi:
        assert c.risk_reward_ratio == 4.0
        d = c.source_fields["target_decision"]
        assert d["floored_by_min_rr"] is True
        assert d["source"] == "declared_family_target_policy"


def test_unregistered_family_fails_loud_instead_of_inheriting_the_floor():
    """A new family with no declared target must raise, not silently become the risk floor.

    Against the pre-repair implementation there was no table and no possible failure, so this
    test cannot pass there.
    """
    p = _target_rr(_cfg(1.5, enabled=True))
    with pytest.raises(KeyError) as exc:
        p.decide("a_family_nobody_declared")
    assert "FAMILY_TARGET_RR" in str(exc.value)


# ------------------------------------------------------------------------ provenance

def test_provenance_is_on_every_emission_when_the_policy_is_on():
    cands = _emit(_cfg(1.5, enabled=True))
    assert cands
    for c in cands:
        d = c.source_fields["target_decision"]
        assert d["basis"] in {"FOUNDING_ARTIFACT", "MEASURED", "UNCHOSEN"}
        assert d["provenance"]
        assert d["target_rr"] == c.risk_reward_ratio


def test_every_production_family_has_a_declared_row():
    """The registry-completeness guard. A family added to PRODUCTION_ORIGIN_FAMILIES or to the
    current-framework map without a target row is the exact defect this table removes."""
    missing = [f for f in PRODUCTION_ORIGIN_FAMILIES if f not in FAMILY_TARGET_RR]
    missing += [f for f in CURRENT_FRAMEWORK_ORIGIN_FAMILY.values()
                if f not in FAMILY_TARGET_RR]
    assert not missing, f"families with no declared take-profit policy: {missing}"


def test_every_row_declares_a_basis_and_a_provenance():
    for fam, row in FAMILY_TARGET_RR.items():
        rr, basis, prov = row
        assert rr > 0, fam
        assert basis in {"FOUNDING_ARTIFACT", "MEASURED", "UNCHOSEN"}, fam
        assert len(prov) > 20, f"{fam}: provenance must say where the number came from"


def test_the_floor_still_binds_and_this_test_exists_to_stop_that_being_forgotten():
    """The honest limit of the repair, pinned so it cannot be quietly overstated.

    Every declared target is 1.5; `min_rr` is 1.5 on mainline and 2.0 in the sealed replay. So
    the floor binds on every emission the estate actually produces and the RISK dial still moves
    every take-profit upward with it. The decoupling is structural; it becomes effective the
    first time a family declares a target above the floor on evidence.

    If someone later declares such a target, this test fails and they must come back and update
    the claim in `FAMILY_TARGET_RR`'s banner rather than leave a stale "decoupled" story behind.
    """
    declared = {rr for rr, _b, _p in FAMILY_TARGET_RR.values()}
    assert declared == {1.5}, (
        "a family now declares a target other than the risk floor -- the repair has become "
        "effective; update FAMILY_TARGET_RR's 'THE LIMIT OF THIS REPAIR' note and this test"
    )
    for min_rr in (1.5, 2.0):
        for c in _emit(_cfg(min_rr, enabled=True)):
            d = c.source_fields["target_decision"]
            assert d["floored_by_min_rr"] is (min_rr > 1.5)
            assert c.risk_reward_ratio == max(1.5, min_rr)


def test_decide_is_stable_and_side_free():
    p = _target_rr(_cfg(1.5, enabled=True))
    for fam in FAMILY_TARGET_RR:
        a, b = p.decide(fam), p.decide(fam)
        assert a == b
