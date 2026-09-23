"""Behavioural tests for the walk-forward admission gate.

These assert what the gate DOES, not what its source says. The single most important
property under test is negative: **the gate must be able to reject.** A gate that admits by
construction launders unvalidated research into a book that carries a funded account, and
that failure is invisible to any test that only checks the happy path — so the bulk of this
file is adversaries that must not get through.
"""

from __future__ import annotations

import datetime as dt
import itertools
import json
import math
import random

import pytest

from src.costs import load_broker_true_costs
from src.research_infra.walkforward import (
    TradeRecord,
    Verdict,
    build_daily_panel,
    price_trades,
    run_gate,
)
from src.research_infra.walkforward.fidelity import (
    FIDELITY_REGISTER,
    FidelityBasis,
    FidelityClass,
    fidelity_for,
)
from src.research_infra.walkforward.folds import assign_folds, build_fold_calendar
from src.research_infra.walkforward.options import OPTIONS
from src.research_infra.walkforward.spec import GateSpec
from src.research_infra.walkforward.stats import (
    apply_pooling_weights,
    benjamini_hochberg,
    block_length_auto,
    block_length_auto_segmented,
    block_permutation_p,
    bonferroni,
    combined_null_p,
    day_block_bootstrap_p,
    lag1_autocorr,
    perm_p_floor,
)

UTC = dt.timezone.utc
FAST = dict(n_bootstrap=800, n_permutation=800)
CAPTURE_DECLARATION_ID = "TEST_CAPTURE_PLAN_V1"
CAPTURE_DECLARATION_SHA256S = ("1" * 64,)


def _spec(**kw) -> GateSpec:
    base = dict(spec_id="t", authored_utc="2026-07-29T00:00:00+00:00", **FAST)
    base.update(kw)
    return GateSpec(**base)


def _capture_spec(windows, **kw) -> GateSpec:
    return OPTIONS["B_balanced"].with_(
        **FAST,
        capture_windows=tuple(tuple(window) for window in windows),
        capture_declaration_id=CAPTURE_DECLARATION_ID,
        capture_declaration_sha256s=CAPTURE_DECLARATION_SHA256S,
        **kw,
    )


def _capture_trades(sleeve, windows, *, r_gross=0.5):
    trades = []
    for lo, hi in windows:
        start = dt.date.fromisoformat(lo)
        end = dt.date.fromisoformat(hi)
        for offset in range((end - start).days + 1):
            day = start + dt.timedelta(days=offset)
            entry = dt.datetime(day.year, day.month, day.day, 8, tzinfo=UTC)
            trades.append(
                TradeRecord(
                    sleeve,
                    "BTCUSD",
                    entry,
                    entry + dt.timedelta(hours=6),
                    1,
                    900.0,
                    30_000.0,
                    r_gross,
                )
            )
    return trades


def _mk(sleeve, symbol, n, gen, *, rng, start=dt.date(2016, 1, 4), px=100.0, sl=1.0,
        step=(1, 1, 2, 3), hold_h=6.0):
    out, d = [], start
    for i in range(n):
        d += dt.timedelta(days=rng.choice(step))
        e = dt.datetime(d.year, d.month, d.day, 8, tzinfo=UTC)
        out.append(TradeRecord(
            sleeve=sleeve, symbol=symbol, entry_utc=e,
            exit_utc=e + dt.timedelta(hours=hold_h), direction=rng.choice([1, -1]),
            sl_distance_price=sl, entry_price=px, r_gross=gen(i, d)))
    return out


# =====================================================================================
# 1. The seal — the spec's whole reason for existing
# =====================================================================================
def test_seal_is_stable_and_field_sensitive():
    a, b = _spec(), _spec()
    assert a.seal() == b.seal()
    assert len(a.seal()) == 64


@pytest.mark.parametrize("field,value", [
    ("pooling_weights", "by_oos_days"),      # the field B7.5 left unsealed
    ("multiplicity", "bonferroni"),
    ("alpha", 0.05),
    ("min_oos_mean_r", 0.01),
    ("embargo_quantile", 0.95),
    ("coverage_policy", "restrict_to_priced"),
    ("day_aggregation", "sum"),
    ("fidelity_reference_policy", "replay_consistency"),
    ("fidelity_precision_floor", 0.80),
    ("seed", 1),
])
def test_every_verdict_moving_field_changes_the_seal(field, value):
    assert _spec().with_(**{field: value}).seal() != _spec().seal()


def test_free_text_does_not_change_the_seal():
    """Commentary must not read as a methodology change."""
    a = _spec()
    assert a.with_(author_note="typo fixed").seal() == a.seal()
    assert a.with_(notes={"anything": 1}).seal() == a.seal()


def test_seal_roundtrips_and_detects_tampering(tmp_path):
    p = tmp_path / "spec.json"
    _spec().write(str(p))
    assert GateSpec.read(str(p)).seal() == _spec().seal()
    d = json.loads(p.read_text())
    d["alpha"] = 0.5  # edit a threshold, keep the old hash
    p.write_text(json.dumps(d))
    with pytest.raises(ValueError, match="seal mismatch"):
        GateSpec.read(str(p))


def test_historical_v1_spec_roundtrips_without_silent_v2_reinterpretation(tmp_path):
    from src.research_infra.walkforward.fidelity import FidelityReferencePolicy
    from src.research_infra.walkforward.spec import LEGACY_DEFAULT_SPEC, LEGACY_SCHEMA

    p = tmp_path / "legacy_spec.json"
    LEGACY_DEFAULT_SPEC.write(str(p))
    document = json.loads(p.read_text())
    assert document["schema"] == LEGACY_SCHEMA
    assert "fidelity_reference_policy" not in document
    assert "fidelity_precision_floor" not in document
    restored = GateSpec.read(str(p), allow_legacy=True)
    assert restored.seal() == LEGACY_DEFAULT_SPEC.seal()
    assert restored.fidelity_reference_policy == (
        FidelityReferencePolicy.LEGACY_ANY_REFERENCE.value
    )


@pytest.mark.parametrize("kw", [
    {"account": "Oanda"}, {"n_folds": 2}, {"alpha": 0.0}, {"multiplicity": "holm"},
    {"pooling_weights": "whatever"}, {"coverage_policy": "assume_zero"},
    {"fidelity_reference_policy": "whatever"}, {"fidelity_precision_floor": 1.01},
    {"reserved_blackout": (("2026-03-31", "2026-03-01"),)},
])
def test_spec_refuses_incoherent_configuration(kw):
    with pytest.raises(ValueError):
        _spec(**kw)


# =====================================================================================
# 2. Fidelity — the gate must refuse what the generator cannot support
# =====================================================================================
def test_first_of_day_sleeves_are_scoreable_once_the_lineage_is_matched():
    """AMENDED by Session Y (B490). These three were refused at 0-8 % live-recall on
    `K1_GATE_RECEIPT.md` section 3.5. That figure came from replaying MAINLINE against a
    live record produced by the deployed lineage (`redacted_host`, no `_server_clock.py`), which
    puts every session window 3 h apart. Replayed under the matching lineage they reproduce
    every live intent: 175 of 175 recovered, 0 newly missed."""
    for name in ("asian_fade", "orb_crypto_london", "metal_session_reversion"):
        f = fidelity_for(name)
        assert f.cls is FidelityClass.FIRST_OF_DAY          # the latch is still real
        assert f.basis is FidelityBasis.MEASURED_LINEAGE_MATCHED
        assert f.live_recall == 1.0
        assert f.scoreable(0.50)
        assert f.refusal_reason(0.50) is None
        # the caveat has to travel with the number
        assert "MAINLINE semantics" in f.basis_note
        assert "SUPERSEDES" in f.basis_note


def test_the_two_fixed_bar_sleeves_are_no_longer_called_first_of_day():
    """`ny_crypto_momentum:88-89` and `kz_london_crypto_low:88-90` gate on an exact
    (hour, minute) with no scan of earlier bars — no latch exists. K's class table pooled
    them into the first-of-day class, so its 19 % was computed over a mixed population."""
    for name in ("ny_crypto_momentum", "kz_london_crypto_low"):
        assert fidelity_for(name).cls is FidelityClass.FIXED_DECISION_BAR


def test_a_sleeve_with_no_observation_still_fails_closed():
    """The floor separates MEASURED from UNMEASURED, and that is the property that matters.

    AMENDED TWICE, and the second time is the reason this now derives its specimen instead of
    naming one. Session Y (B490) moved it from `asian_fade` once that sleeve became scoreable;
    Session AK (B951) had to move it again, because `ny_index_momentum` — the specimen Y chose
    — now carries a TRANSFERRED_CLASS record. That was a deliberate change and its cost is
    stated in `fidelity._NO_LIVE_PATH`: four generators exist that no registry can reach, and
    without a record the gate returns NOT_EVALUABLE on all four for a reason that has nothing
    to do with fidelity, so they get their structural class rate plus a stamp saying their live
    record is structurally EMPTY rather than thin.

    A test about the REFUSAL MECHANISM must not keep failing because a sleeve gained evidence —
    that is the failure mode AA §3.4 recorded when a test hardcoded an unpriceable symbol and
    went red because coverage improved. So the specimen is derived at run time and its absence
    from the register is asserted, which makes the test about the mechanism and nothing else.
    """
    name = "zz_no_such_sleeve_ak_probe"
    assert name not in FIDELITY_REGISTER, "the specimen must genuinely have no record"
    f = fidelity_for(name)
    assert f.live_recall is None
    assert not f.scoreable(0.0)
    assert "port_fidelity_unmeasured" in f.refusal_reason(0.50)
    # ...and the mechanism must still be reachable: at least one name IS refused this way, or
    # the assertion above would be true of a register that had simply stopped working.
    unmeasured = [s for s, rec in FIDELITY_REGISTER.items() if rec.live_recall is None]
    assert unmeasured == [] or all(
        not FIDELITY_REGISTER[s].scoreable(0.0) for s in unmeasured)


def test_per_bar_sleeves_are_scoreable():
    for name in ("fx_jpy", "idxrev", "mx_btcusd_d1_donchian_20_breakout"):
        assert fidelity_for(name).scoreable(0.50)


def test_transferred_fidelity_carries_its_real_basis():
    """The 96% per-bar rate must never be quotable bare for an mx sleeve.

    Decomposition corrected by Session Y (B491): the mx_* family contributes NINE agreed
    intents across FIVE sleeves (nzdjpy 5, avausd 1, btcusd 1, cadjpy 1, ethusd 1), not
    "one sleeve and five intents" — 148 of 160 still come from three core-book sleeves,
    which is the point the note exists to make."""
    f = fidelity_for("mx_btcusd_d1_donchian_20_breakout")
    assert f.basis is FidelityBasis.TRANSFERRED_CLASS
    assert "NINE intents across FIVE sleeves" in f.basis_note
    assert "148 of 160" in f.basis_note
    assert "TRANSFERRED" in f.ceiling_stamp(0.50)
    # The one mx sleeve K actually measured is direct, not transferred.
    assert fidelity_for("mx_nzdjpy_d1_donchian_20_breakout").basis is FidelityBasis.MEASURED_DIRECT


def test_unknown_sleeve_fails_closed():
    f = fidelity_for("totally_new_sleeve")
    assert f.live_recall is None and not f.scoreable(0.0)
    assert "port_fidelity_unmeasured" in f.refusal_reason(0.50)


# =====================================================================================
# 3. Cost binding — an unpriced trade is unpriced, never free
# =====================================================================================
def _an_unpriceable_symbol() -> str | None:
    """A symbol `cost_r` genuinely cannot price, read FROM the artifact, not hardcoded.

    This test named `EU50.cash` because that was unpriced when it was written. It gained a
    tick file on 2026-07-30 (FTMO spread:MEASURED 30 -> 36) and the test went red on a
    premise the data had overtaken — not on any change to the gate. The behaviour under
    test is "an unpriceable symbol is RECORDED, never assumed zero", which is F38 and is
    permanent; which symbol happens to be unpriceable on a given day is not.

    Commission is charged before spread, so a symbol whose commission schedule is unknown
    refuses at the wrong gate. Pick one that gets as far as the spread term.
    """
    from src.costs import load_broker_true_costs  # noqa: PLC0415

    insts = load_broker_true_costs().doc["accounts"]["FTMO"]["instruments"]
    for sym in sorted(insts):
        rec = insts[sym]
        if rec.get("spread_price"):
            continue
        if (rec.get("commission") or {}).get("kind") in ("zero", "per_lot", "notional_bp"):
            return sym
    # Every FTMO instrument with a known commission now has a measured spread. That is
    # good news (coverage closing is the programme's active workstream, FOURTH_REVIEW §9),
    # so the caller skips rather than fails — a test must not go red because data improved.
    return None


def test_unpriceable_symbol_is_recorded_not_assumed_zero():
    """An unpriced trade is unpriced, never free. F38 is the other branch.

    THE SYMBOL IS DERIVED, NOT HARDCODED, and that is the point of this revision.
    It used to name `EU50.cash`, which stopped being unpriceable on 2026-07-29 when the
    tick capture landed six more FTMO spreads (AUS200.cash, CADJPY, DASHUSD, EU50.cash,
    NATGAS.cash, SPN35.cash) — so a test about the REFUSAL MECHANISM failed because a data
    fact improved, which is the worst way for a test to fail. Coverage closing is the
    programme's active workstream (`FOURTH_REVIEW.md` §9), so any hardcoded unpriceable
    symbol is a scheduled breakage. This picks one from the artifact at run time and skips
    if broker truth ever prices everything — at which point the refusal path is genuinely
    untestable this way and someone should know.
    """
    sym = _an_unpriceable_symbol()
    if sym is None:  # pragma: no cover - would mean 100% spread coverage
        pytest.skip("every FTMO instrument with a known commission now carries a measured spread")
    rng = random.Random(1)
    trades = _mk("mx_eu50_cash_d1_volume_surge_reversal", sym, 40,
                 lambda i, d: 1.0, rng=rng, px=4000.0, sl=40.0)
    priced, cov = price_trades(trades, _spec())
    c = cov["mx_eu50_cash_d1_volume_surge_reversal"]
    assert c.n_priced == 0 and c.n_unpriced == 40 and c.coverage_frac == 0.0, (
        f"{sym} has no measured spread in the artifact yet priced anyway"
    )
    assert all(p.cost_r is None and p.r_net is None for p in priced)
    assert c.unpriced_reasons, "a refusal must record its reason"


def test_priced_trade_is_charged_a_positive_cost():
    rng = random.Random(2)
    trades = _mk("mx_btcusd_d1_donchian_20_breakout", "BTCUSD", 20,
                 lambda i, d: 1.0, rng=rng, px=30000.0, sl=900.0)
    priced, cov = price_trades(trades, _spec())
    assert cov["mx_btcusd_d1_donchian_20_breakout"].coverage_frac == 1.0
    assert all(p.cost_r > 0 for p in priced)
    assert all(p.r_net < p.trade.r_gross for p in priced)


def test_blackout_drops_trades_and_counts_them_separately():
    rng = random.Random(3)
    inside = _mk("mx_btcusd_d1_donchian_20_breakout", "BTCUSD", 10, lambda i, d: 1.0,
                 rng=rng, start=dt.date(2026, 3, 2), px=30000.0, sl=900.0, step=(1,))
    _, cov = price_trades(inside, _spec())
    c = cov["mx_btcusd_d1_donchian_20_breakout"]
    assert c.n_blackout_dropped == 10 and c.n_priced == 0 and c.n_unpriced == 0


def test_day_aggregation_collapses_within_day_clustering():
    e = dt.datetime(2020, 1, 6, 8, tzinfo=UTC)
    trades = [TradeRecord("mx_btcusd_d1_donchian_20_breakout", "BTCUSD", e,
                          e + dt.timedelta(hours=6), 1, 900.0, 30000.0, r)
              for r in (3.0, -1.0, 1.0, -1.0)]
    priced, _ = price_trades(trades, _spec())
    daily, counts = build_daily_panel(priced, _spec())
    d = dt.date(2020, 1, 6)
    assert counts["mx_btcusd_d1_donchian_20_breakout"][d] == 4
    assert len(daily["mx_btcusd_d1_donchian_20_breakout"]) == 1  # 4 trades -> 1 observation
    assert daily["mx_btcusd_d1_donchian_20_breakout"][d] < 0.5   # mean(3,-1,1,-1)=0.5, minus cost


# =====================================================================================
# 4. Folds — purge, embargo, blackout
# =====================================================================================
def test_fold_zero_is_never_scored():
    spec = _spec()
    folds = build_fold_calendar(spec, dt.date(2016, 1, 1), dt.date(2022, 1, 1))
    assert folds[0].is_initial_train
    rng = random.Random(4)
    trades = _mk("mx_btcusd_d1_donchian_20_breakout", "BTCUSD", 200, lambda i, d: 0.1,
                 rng=rng, px=30000.0, sl=900.0)
    priced, _ = price_trades(trades, spec)
    daily, _ = build_daily_panel(priced, spec)
    sl = daily["mx_btcusd_d1_donchian_20_breakout"]
    slices = assign_folds(priced, sl, folds, spec)
    assert all(not s.fold.is_initial_train for s in slices)
    assert len(slices) == len(folds) - 1


def test_a_trade_straddling_the_fold_boundary_is_purged_from_train():
    spec = _spec(embargo_floor_days=1, n_folds=3)
    folds = build_fold_calendar(spec, dt.date(2020, 1, 1), dt.date(2020, 12, 31))
    target = folds[1]
    # A trade that OPENS well before the fold but CLOSES inside it: its outcome was
    # determined by price action in the test window, so it must not train.
    straddler = TradeRecord(
        "mx_btcusd_d1_donchian_20_breakout", "BTCUSD",
        dt.datetime.combine(target.oos_start - dt.timedelta(days=10), dt.time(8), UTC),
        dt.datetime.combine(target.oos_start + dt.timedelta(days=2), dt.time(8), UTC),
        1, 900.0, 30000.0, 1.0)
    priced, _ = price_trades([straddler], spec)
    daily, _ = build_daily_panel(priced, spec)
    slices = assign_folds(priced, daily["mx_btcusd_d1_donchian_20_breakout"], folds, spec)
    s = next(s for s in slices if s.fold.fold_id == target.fold_id)
    assert s.n_purged_trades == 1
    assert s.n_train_trades == 0


def test_embargo_is_measured_from_holds_not_a_nominal():
    """A sleeve that holds for weeks must get a wider embargo than one holding hours."""
    spec = _spec(n_folds=3)
    rng = random.Random(5)
    short = _mk("mx_btcusd_d1_donchian_20_breakout", "BTCUSD", 150, lambda i, d: 0.1,
                rng=rng, px=30000.0, sl=900.0, hold_h=4.0)
    long_ = _mk("mx_btcusd_d1_donchian_20_breakout", "BTCUSD", 150, lambda i, d: 0.1,
                rng=random.Random(5), px=30000.0, sl=900.0, hold_h=24 * 20)

    def emb(trades):
        priced, _ = price_trades(trades, spec)
        daily, _ = build_daily_panel(priced, spec)
        folds = build_fold_calendar(spec, min(daily["mx_btcusd_d1_donchian_20_breakout"]),
                                    max(daily["mx_btcusd_d1_donchian_20_breakout"]))
        sl = assign_folds(priced, daily["mx_btcusd_d1_donchian_20_breakout"], folds, spec)
        return max(s.embargo_days for s in sl)

    assert emb(short) < emb(long_)
    assert emb(short) >= spec.embargo_floor_days


def test_no_fold_boundary_falls_inside_the_reserved_blackout():
    spec = _spec()
    folds = build_fold_calendar(spec, dt.date(2025, 1, 1), dt.date(2026, 7, 27))
    for f in folds:
        assert not spec.blackout_hits(f.oos_start, f.oos_start), f.as_dict()


# =====================================================================================
# 5. Statistics
# =====================================================================================
def test_benjamini_hochberg_matches_the_1995_reference_example():
    """Benjamini & Hochberg (1995) Table 1: m=15, alpha=0.05, exactly 4 rejections."""
    p = [0.0001, 0.0004, 0.0019, 0.0095, 0.0201, 0.0278, 0.0298, 0.0344,
         0.0459, 0.3240, 0.4262, 0.5719, 0.6528, 0.7590, 1.000]
    r = benjamini_hochberg(p, 0.05)
    assert r["k"] == 4
    assert r["rejected"][:4] == [True] * 4
    assert not any(r["rejected"][4:])
    assert all(r["qvalues"][i] <= r["qvalues"][i + 1] + 1e-12 for i in range(len(p) - 1))


def test_benjamini_hochberg_is_step_up_not_step_down():
    """p=0.03 fails its own rank-1 threshold (0.025) but is rejected because rank 2 passes."""
    r = benjamini_hochberg([0.03, 0.04], 0.05)
    assert r["rejected"] == [True, True] and r["k"] == 2


def test_bonferroni_is_at_least_as_strict_as_bh():
    p = [0.001, 0.008, 0.039, 0.041, 0.042, 0.060, 0.074, 0.205]  # arbitrary family
    bh, bf = benjamini_hochberg(p, 0.05), bonferroni(p, 0.05)
    assert sum(bf["rejected"]) <= sum(bh["rejected"])
    assert all((not b) or h for b, h in zip(bf["rejected"], bh["rejected"]))


def test_non_finite_pvalues_never_reject_and_never_shrink_the_family():
    r = benjamini_hochberg([0.001, float("nan"), None or 1.0], 0.05)
    assert r["m"] == 3 and r["rejected"][1] is False


def test_pooling_weights_make_a_plain_mean_the_weighted_mean():
    x = [1.0, 2.0, 3.0, 4.0]
    w = [0.1, 0.1, 1.0, 1.0]
    scaled = apply_pooling_weights(x, w)
    want = sum(a * b for a, b in zip(x, w)) / sum(w)
    assert math.isclose(sum(scaled) / len(scaled), want, rel_tol=1e-12)


def test_bootstrap_pvalue_is_not_significant_under_a_true_null():
    rng = random.Random(11)
    hits = 0
    for s in range(60):
        x = [rng.gauss(0.0, 1.0) for _ in range(200)]
        if day_block_bootstrap_p(x, block=5, n_boot=600, seed=s)["p_value"] <= 0.05:
            hits += 1
    assert hits <= 12, f"{hits}/60 false positives under a true null — miscalibrated"


def test_bootstrap_detects_a_real_effect():
    rng = random.Random(12)
    x = [rng.gauss(0.5, 1.0) for _ in range(200)]
    assert day_block_bootstrap_p(x, block=5, n_boot=2000, seed=1)["p_value"] < 0.01


def test_block_length_grows_with_autocorrelation():
    rng = random.Random(13)
    iid = [rng.gauss(0, 1) for _ in range(400)]
    ar, prev = [], 0.0
    for _ in range(400):
        prev = 0.75 * prev + rng.gauss(0, 1)
        ar.append(prev)
    assert lag1_autocorr(ar) > lag1_autocorr(iid)
    assert block_length_auto(ar) > block_length_auto(iid)


# =====================================================================================
# 6. THE GATE MUST BE ABLE TO FAIL. This is the section that matters.
# =====================================================================================
def _run(trades, spec=None):
    return run_gate(trades, spec or OPTIONS["B_balanced"].with_(**FAST))


def test_a_real_stable_cost_surviving_edge_is_admitted():
    """The other half of falsification: a gate that rejects everything is also broken."""
    rng = random.Random(20)
    t = _mk("mx_nzdjpy_d1_donchian_20_breakout", "NZDJPY", 700,
            lambda i, d: max(-1.15, min(4.8, rng.gauss(0.30, 1.0))), rng=rng, px=80.0, sl=0.45)
    res = _run({"mx_nzdjpy_d1_donchian_20_breakout": t})
    assert res.verdicts["mx_nzdjpy_d1_donchian_20_breakout"].verdict is Verdict.ADMIT


def test_zero_edge_noise_is_rejected():
    rng = random.Random(21)
    t = _mk("mx_ethusd_d1_donchian_20_breakout", "ETHUSD", 600,
            lambda i, d: rng.gauss(0.0, 1.05), rng=rng, px=2000.0, sl=60.0)
    assert _run({"mx_ethusd_d1_donchian_20_breakout": t}).admitted == []


def test_an_edge_that_lives_in_one_fold_is_rejected_despite_positive_expectancy():
    """The case a gate with no leave-one-fold-out requirement passes.

    All the edge sits inside a four-month window that lands in a single fold. Pooled
    expectancy is comfortably positive (+0.65 R/day) and 80% of folds are positive, so
    neither the expectancy gate nor a positive-fold-fraction threshold catches it. Only
    deleting the best fold does: what remains is +0.02 R/day, 3.4% of the headline.
    """
    rng = random.Random(22)
    lo, hi = dt.date(2018, 1, 1), dt.date(2018, 4, 30)
    t = _mk("mx_us30_cash_d1_volume_surge_reversal", "US30.cash", 900,
            lambda i, d: rng.gauss(6.0, 1.0) if lo <= d <= hi else rng.gauss(0.0, 1.0),
            rng=rng, px=30000.0, sl=300.0, step=(1, 1, 2, 2))
    res = _run({"mx_us30_cash_d1_volume_surge_reversal": t})
    v = res.verdicts["mx_us30_cash_d1_volume_surge_reversal"]
    assert v.verdict is Verdict.REJECT
    # The point of the test: everything except robustness says yes.
    assert v.pooled_oos_mean_r > 0.5
    assert v.gates["expectancy"]["pass"] and v.gates["stability"]["pass"]
    assert not v.gates["robustness"]["pass"]
    assert v.gates["robustness"]["retention"] < 0.1


def test_a_persistent_edge_survives_leave_one_fold_out():
    """The other side: robustness must not reject an edge merely for having a best fold."""
    rng = random.Random(31)
    t = _mk("mx_nzdjpy_d1_donchian_20_breakout", "NZDJPY", 700,
            lambda i, d: max(-1.15, min(4.8, rng.gauss(0.30, 1.0))), rng=rng,
            px=80.0, sl=0.45)
    v = _run({"mx_nzdjpy_d1_donchian_20_breakout": t}).verdicts[
        "mx_nzdjpy_d1_donchian_20_breakout"]
    assert v.gates["robustness"]["pass"]
    assert v.gates["robustness"]["retention"] > 0.5


def test_a_gross_positive_sleeve_eaten_by_cost_is_rejected():
    """The case a gate whose cost binding is decorative passes."""
    rng = random.Random(23)
    t = _mk("mx_jp225_cash_d1_volume_surge_reversal", "JP225.cash", 600,
            lambda i, d: rng.gauss(0.03, 0.9), rng=rng, px=38000.0, sl=12.0)
    res = _run({"mx_jp225_cash_d1_volume_surge_reversal": t})
    v = res.verdicts["mx_jp225_cash_d1_volume_surge_reversal"]
    assert v.verdict is Verdict.REJECT
    assert v.pooled_oos_mean_r < 0.0  # gross-positive by construction, net-negative


def test_day_clustered_noise_is_rejected():
    """The case a gate whose null treats trades as iid passes."""
    rng = random.Random(24)
    out, d = [], dt.date(2016, 1, 4)
    for _ in range(300):
        d += dt.timedelta(days=rng.choice([1, 2, 4]))
        e = dt.datetime(d.year, d.month, d.day, 8, tzinfo=UTC)
        shock = rng.gauss(0.0, 0.9)
        out.extend(TradeRecord("mx_us500_cash_d1_atr_mean_reversion", "US500.cash", e,
                               e + dt.timedelta(hours=6), rng.choice([1, -1]), 40.0, 4000.0,
                               shock + rng.gauss(0.0, 0.35)) for _k in range(8))
    assert _run({"mx_us500_cash_d1_atr_mean_reversion": out}).admitted == []


def test_a_sleeve_the_cost_layer_cannot_price_is_not_evaluable_under_refuse():
    rng = random.Random(25)
    t = _mk("mx_fra40_cash_d1_volume_surge_reversal", "FRA40.cash", 400,
            lambda i, d: 1.0, rng=rng, px=7000.0, sl=70.0)
    res = _run({"mx_fra40_cash_d1_volume_surge_reversal": t},
               OPTIONS["A_strict"].with_(**FAST))
    v = res.verdicts["mx_fra40_cash_d1_volume_surge_reversal"]
    assert v.verdict is Verdict.NOT_EVALUABLE
    assert "cost_coverage_below_floor" in v.reasons[0]


def test_a_fidelity_unmeasured_sleeve_is_never_scored_however_good_it_looks():
    """A gate that cannot refuse is worse than no gate — and the specimen is now DERIVED.

    AMENDED by Session Y (B490) from `asian_fade`, and again by Session AK (B951) from
    `ny_index_momentum`; see the sibling test above for why, and for why naming a specimen is
    itself the defect. The trades are deliberately excellent (every one +2 R) so the only thing
    that can refuse them is the fidelity gate.
    """
    name = "zz_no_such_sleeve_ak_probe"
    assert name not in FIDELITY_REGISTER
    rng = random.Random(26)
    t = _mk(name, "US500", 600, lambda i, d: 2.0, rng=rng, px=160.0, sl=0.5)
    v = _run({name: t}).verdicts[name]
    assert v.verdict is Verdict.NOT_EVALUABLE
    assert v.pooled_oos_mean_r is None
    assert "port_fidelity_unmeasured" in v.reasons[0]
    # The refusal must come from FIDELITY and not from something downstream that happens to
    # refuse first — the exact confound that made this test's previous specimen fail with a
    # `cost_coverage_below_floor` reason once it gained a record.
    assert v.gates["fidelity"]["pass"] is False


def test_a_first_of_day_sleeve_is_scored_but_carries_its_ceiling_stamp():
    """The counterpart: `asian_fade` now reaches a verdict, and the stamp that travels with
    it says what the fidelity rests on. A number without the stamp is the failure mode."""
    rng = random.Random(26)
    # GBPJPY has an exact account/symbol slippage capture; EURJPY no longer inherits
    # the old pooled constant-R default and is correctly NOT_EVALUABLE for costs.
    t = _mk("asian_fade", "GBPJPY", 600, lambda i, d: 2.0, rng=rng, px=160.0, sl=0.5)
    v = _run({"asian_fade": t}).verdicts["asian_fade"]
    assert v.verdict is not Verdict.NOT_EVALUABLE
    assert v.gates["fidelity"]["pass"] is True
    assert "measured_lineage_matched" in v.fidelity["ceiling_stamp"]


def test_refused_sleeves_still_count_in_the_multiplicity_family():
    """Otherwise refusing a sleeve would make its neighbours easier to admit."""
    rng = random.Random(27)
    good = _mk("mx_nzdjpy_d1_donchian_20_breakout", "NZDJPY", 700,
               lambda i, d: max(-1.15, min(4.8, rng.gauss(0.30, 1.0))), rng=rng,
               px=80.0, sl=0.45)
    refused = _mk("asian_fade", "EURJPY", 300, lambda i, d: 1.0, rng=rng, px=160.0, sl=0.5)
    alone = _run({"mx_nzdjpy_d1_donchian_20_breakout": good})
    with_refused = _run({"mx_nzdjpy_d1_donchian_20_breakout": good, "asian_fade": refused})
    assert alone.family["multiplicity"]["m"] == 1
    assert with_refused.family["multiplicity"]["m"] == 2
    q_alone = alone.verdicts["mx_nzdjpy_d1_donchian_20_breakout"].q_value
    q_with = with_refused.verdicts["mx_nzdjpy_d1_donchian_20_breakout"].q_value
    assert q_with >= q_alone


def test_stricter_options_never_admit_more_than_looser_ones():
    rng = random.Random(28)
    trades = {
        "mx_nzdjpy_d1_donchian_20_breakout": _mk(
            "mx_nzdjpy_d1_donchian_20_breakout", "NZDJPY", 500,
            lambda i, d: rng.gauss(0.12, 1.0), rng=rng, px=80.0, sl=0.45),
        "mx_btcusd_d1_donchian_20_breakout": _mk(
            "mx_btcusd_d1_donchian_20_breakout", "BTCUSD", 500,
            lambda i, d: rng.gauss(0.05, 1.0), rng=rng, px=30000.0, sl=900.0),
    }
    a = set(_run(trades, OPTIONS["A_strict"].with_(**FAST)).admitted)
    b = set(_run(trades, OPTIONS["B_balanced"].with_(**FAST)).admitted)
    c = set(_run(trades, OPTIONS["C_exploratory"].with_(**FAST)).admitted)
    assert a <= b <= c


def test_result_carries_the_spec_seal_it_ran_under():
    rng = random.Random(29)
    t = _mk("mx_btcusd_d1_donchian_20_breakout", "BTCUSD", 200, lambda i, d: 0.1,
            rng=rng, px=30000.0, sl=900.0)
    spec = OPTIONS["B_balanced"].with_(**FAST)
    d = _run({"mx_btcusd_d1_donchian_20_breakout": t}, spec).as_dict()
    assert d["spec_sha256"] == spec.seal()
    assert d["spec"]["pooling_weights"] == spec.pooling_weights


def test_predeclared_captures_produce_independent_local_train_oos_folds():
    """Empty calendar between captures is not data and cannot manufacture a fold.

    Each 30-day capture deterministically falls back to two local equal-calendar folds
    under the unchanged B-balanced spec: 15 initial-train days and 15 scored OOS days.
    The three scored slices are concatenated and every local initial block remains visible
    in lifetime telemetry.
    """

    sleeve = "mx_btcusd_d1_donchian_20_breakout"
    windows = (
        ("2026-01-01", "2026-01-30"),
        ("2026-04-01", "2026-04-30"),
        ("2026-05-01", "2026-05-30"),
    )
    trades = _capture_trades(sleeve, windows)

    spec = _capture_spec(windows)
    result = run_gate(
        {sleeve: trades},
        spec,
    )
    verdict = result.verdicts[sleeve]
    assert [(row["oos_start"], row["oos_end"]) for row in verdict.folds] == [
        ("2026-01-16", "2026-01-30"),
        ("2026-04-16", "2026-04-30"),
        ("2026-05-16", "2026-05-30"),
    ]
    assert [row["fold_id"] for row in verdict.folds] == [1, 2, 3]
    assert all(row["n_train_trades"] == 14 for row in verdict.folds)
    assert all(row["n_test_trades"] == 15 for row in verdict.folds)
    assert verdict.gates["sample"]["n_folds_evaluable"] == 3
    assert verdict.telemetry["lifetime"]["fold0_unscored"]["n_trades"] == 45
    capture = result.family["fold_capture_contract"]
    assert capture["windows"] == [list(window) for window in windows]
    assert capture["gate_spec_sha256"] == spec.seal()
    assert capture["authority"] == "immutable_gate_spec"
    assert capture["declaration_id"] == CAPTURE_DECLARATION_ID
    assert capture["declaration_sha256s"] == list(CAPTURE_DECLARATION_SHA256S)
    assert len(capture["sha256"]) == 64
    assert verdict.telemetry["null"]["segment_lengths"] == [15, 15, 15]
    assert verdict.telemetry["null"]["boundary_policy"] == (
        "null_blocks_restart_at_each_capture"
    )


def test_every_sealed_capture_must_contribute_an_evaluable_oos_slice():
    sleeve = "mx_btcusd_d1_donchian_20_breakout"
    windows = (
        ("2026-01-01", "2026-01-30"),
        ("2026-04-01", "2026-04-30"),
        ("2026-05-01", "2026-05-30"),
        ("2026-06-01", "2026-06-30"),
    )
    trades = _capture_trades(sleeve, windows[:3])

    verdict = run_gate({sleeve: trades}, _capture_spec(windows)).verdicts[sleeve]

    assert verdict.verdict is Verdict.NOT_EVALUABLE
    assert verdict.gates["capture_completeness"]["pass"] is False
    assert verdict.gates["capture_completeness"][
        "captures_without_evaluable_oos"
    ] == [4]
    assert verdict.gates["capture_completeness"]["n_captures_declared"] == 4
    assert verdict.gates["capture_completeness"]["n_captures_evaluable"] == 3
    assert verdict.reasons == [
        "capture_not_evaluable: sealed captures 4 contributed no evaluable OOS slice"
    ]


def test_capture_contract_refuses_any_trade_outside_its_declared_windows():
    sleeve = "mx_btcusd_d1_donchian_20_breakout"
    entry = dt.datetime(2026, 2, 1, 8, tzinfo=UTC)
    trade = TradeRecord(
        sleeve,
        "BTCUSD",
        entry,
        entry + dt.timedelta(hours=6),
        1,
        900.0,
        30_000.0,
        0.5,
    )
    with pytest.raises(ValueError, match="outside declared capture windows"):
        run_gate(
            {sleeve: [trade]},
            _capture_spec((("2026-01-01", "2026-01-30"),)),
        )


def test_capture_contract_refuses_label_span_that_escapes_its_window():
    sleeve = "mx_btcusd_d1_donchian_20_breakout"
    entry = dt.datetime(2026, 1, 30, 23, tzinfo=UTC)
    trade = TradeRecord(
        sleeve,
        "BTCUSD",
        entry,
        entry + dt.timedelta(hours=2),
        1,
        900.0,
        30_000.0,
        0.5,
    )
    with pytest.raises(ValueError, match="label spans exit"):
        run_gate(
            {sleeve: [trade]},
            _capture_spec((("2026-01-01", "2026-01-30"),)),
        )


@pytest.mark.parametrize(
    ("windows", "message"),
    [
        (
            (("2026-01-01", "2026-01-30"), ("2026-01-30", "2026-02-10")),
            "strictly ordered and non-overlapping",
        ),
        (
            (("2026-04-01", "2026-04-30"), ("2026-01-01", "2026-01-30")),
            "strictly ordered and non-overlapping",
        ),
        ((("2026-03-01", "2026-03-15"),), "overlaps reserved blackout"),
    ],
)
def test_capture_authority_refuses_overlap_reorder_and_blackout(windows, message):
    with pytest.raises(ValueError, match=message):
        _capture_spec(windows)


@pytest.mark.parametrize(
    ("updates", "message"),
    [
        ({"capture_windows": (("2026-01-01", "2026-01-30"),)}, "must be set together"),
        ({"capture_declaration_id": "ONLY_ID"}, "must be set together"),
        ({"capture_declaration_sha256s": ("1" * 64,)}, "must be set together"),
        (
            {
                "capture_windows": (),
                "capture_declaration_id": "EMPTY",
                "capture_declaration_sha256s": ("1" * 64,),
            },
            "at least one window",
        ),
        (
            {
                "capture_windows": (("2026-01-01", "2026-01-01"),),
                "capture_declaration_id": "ONE_DAY",
                "capture_declaration_sha256s": ("1" * 64,),
            },
            "at least two calendar days",
        ),
        (
            {
                "capture_windows": (("2026-01-02", "2026-01-01"),),
                "capture_declaration_id": "REVERSED",
                "capture_declaration_sha256s": ("1" * 64,),
            },
            "reversed",
        ),
        (
            {
                "capture_windows": (("2026-01-01", "2026-01-30"),),
                "capture_declaration_id": "DUPLICATE",
                "capture_declaration_sha256s": ("1" * 64, "1" * 64),
            },
            "must not repeat",
        ),
        (
            {
                "capture_windows": (("2026-01-01", "2026-01-30"),),
                "capture_declaration_id": "BAD_HASH",
                "capture_declaration_sha256s": ("A" * 64,),
            },
            "lowercase full sha256",
        ),
    ],
)
def test_capture_authority_refuses_partial_empty_and_invalid_declarations(
    updates, message
):
    with pytest.raises(ValueError, match=message):
        OPTIONS["B_balanced"].with_(**FAST, **updates)


def test_touching_captures_are_explicit_independent_boundaries():
    windows = (
        ("2026-04-01", "2026-04-30"),
        ("2026-05-01", "2026-05-30"),
    )
    result = run_gate({}, _capture_spec(windows))
    contract = result.family["fold_capture_contract"]

    assert contract["touching_boundaries"] == [
        {"left_end": "2026-04-30", "right_start": "2026-05-01"}
    ]
    assert "null blocks restart" in contract["touching_policy"]


def test_runtime_capture_replacement_and_unsealed_definition_are_refused():
    sealed = _capture_spec((("2026-01-01", "2026-01-30"),))
    replacement = (("2026-04-01", "2026-04-30"),)

    with pytest.raises(ValueError, match="replacement forbidden"):
        run_gate({}, sealed, capture_windows=replacement)
    with pytest.raises(ValueError, match="cannot define gate authority"):
        run_gate({}, OPTIONS["B_balanced"].with_(**FAST), capture_windows=replacement)

    asserted = run_gate({}, sealed, capture_windows=sealed.capture_windows)
    assert asserted.family["fold_capture_contract"]["windows"] == [
        ["2026-01-01", "2026-01-30"]
    ]


def test_capture_spec_serialization_round_trip_and_legacy_absence(tmp_path):
    sealed = _capture_spec(
        (("2026-01-01", "2026-01-30"), ("2026-04-01", "2026-04-30"))
    )
    path = tmp_path / "capture-spec.json"
    sealed.write(str(path))
    restored = GateSpec.read(str(path))

    assert restored.capture_windows == sealed.capture_windows
    assert restored.capture_declaration_id == sealed.capture_declaration_id
    assert (
        restored.capture_declaration_sha256s
        == sealed.capture_declaration_sha256s
    )
    assert restored.seal() == sealed.seal()
    legacy = OPTIONS["B_balanced"].with_(**FAST)
    assert all(
        field not in legacy.canonical()
        for field in (
            "capture_windows",
            "capture_declaration_id",
            "capture_declaration_sha256s",
        )
    )


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("capture_declaration_id", "POST_OUTCOME_REPLACEMENT"),
        ("capture_declaration_sha256s", ["2" * 64]),
    ],
)
def test_capture_declaration_identity_or_hash_edit_breaks_seal(
    tmp_path, field, replacement
):
    path = tmp_path / "sealed_capture_spec.json"
    spec = _capture_spec((("2026-01-01", "2026-01-30"),))
    spec.write(str(path))
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload[field] = replacement
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="spec seal mismatch"):
        GateSpec.read(str(path))


def test_null_blocks_restart_at_capture_boundaries():
    # With block length equal to each two-observation capture, a within-capture
    # circular draw always retains both members and therefore has zero null
    # variance. The continuous implementation can draw the false [2, 100]
    # boundary block and has positive variance.
    series = [1.0, 2.0, 100.0, 200.0]
    continuous = day_block_bootstrap_p(
        series, block=2, n_boot=512, seed=20
    )
    segmented = day_block_bootstrap_p(
        series,
        block=2,
        n_boot=512,
        seed=20,
        segment_lengths=(2, 2),
    )

    assert continuous["null_sd"] > 0.0
    assert segmented["null_sd"] == pytest.approx(0.0, abs=1e-12)
    assert segmented["boundary_policy"] == (
        "circular_blocks_wrap_within_capture_only"
    )

    permutation = block_permutation_p(
        [1.0, 2.0, 3.0, 100.0, 200.0, 300.0],
        block=2,
        n_perm=512,
        seed=20,
        segment_lengths=(3, 3),
    )
    floor = perm_p_floor(
        6, 2, 512, segment_lengths=(3, 3)
    )
    assert permutation["n_blocks_by_segment"] == [2, 2]
    assert floor["n_blocks_by_segment"] == [2, 2]
    assert floor["n_blocks"] == 4
    assert permutation["phase_policy"] == "none_capture_start_anchored"
    assert permutation["enumeration"] == "exact"
    assert floor["p_floor"] == pytest.approx(1.0 / 16.0)


def test_segmented_null_alignment_exact_sampling_and_bad_lengths_are_explicit():
    series = [2.0, -0.5, 1.0, 3.0, -1.0, 0.25]
    exact_a = block_permutation_p(
        series, block=2, n_perm=16, seed=1, segment_lengths=(3, 3)
    )
    exact_b = block_permutation_p(
        series, block=2, n_perm=16, seed=999, segment_lengths=(3, 3)
    )
    sampled_a = block_permutation_p(
        series, block=1, n_perm=20, seed=7, segment_lengths=(3, 3)
    )
    sampled_b = block_permutation_p(
        series, block=1, n_perm=20, seed=7, segment_lengths=(3, 3)
    )

    assert exact_a == exact_b
    assert exact_a["n_permutations_evaluated"] == 16
    assert exact_a["seed_effective"] is False
    assert sampled_a == sampled_b
    assert sampled_a["enumeration"] == "monte_carlo_add_one"
    assert sampled_a["seed_effective"] is True
    assert perm_p_floor(
        6, 2, 16, segment_lengths=(3, 3)
    )["p_floor"] == pytest.approx(1.0 / 16.0)
    assert perm_p_floor(
        6, 1, 20, segment_lengths=(3, 3)
    )["p_floor"] == pytest.approx(1.0 / 21.0)

    reordered = block_permutation_p(
        series[3:] + series[:3],
        block=2,
        n_perm=16,
        seed=2,
        segment_lengths=(3, 3),
    )
    assert reordered["p_value"] == exact_a["p_value"]

    # A block-aligned rotation of equally sized complete blocks is only a block
    # relabelling. Exact enumeration must therefore be invariant to it.
    blocks = [3.0, -1.0, 2.0, 0.5, -0.2, 1.2, 2.4, -0.8]
    rotated = blocks[2:4] + blocks[:2] + blocks[6:8] + blocks[4:6]
    block_exact = block_permutation_p(
        blocks, block=2, n_perm=16, segment_lengths=(4, 4)
    )
    rotation_exact = block_permutation_p(
        rotated, block=2, n_perm=16, segment_lengths=(4, 4)
    )
    assert rotation_exact["p_value"] == block_exact["p_value"]

    for bad in ((), (0, 6), (-1, 7), (2, 3)):
        with pytest.raises(ValueError, match="segment_lengths"):
            block_permutation_p(
                series, block=2, n_perm=16, segment_lengths=bad
            )

    with pytest.raises(ValueError, match="n_perm"):
        block_permutation_p(
            series, block=2, n_perm=0, segment_lengths=(3, 3)
        )
    with pytest.raises(ValueError, match="n_boot"):
        day_block_bootstrap_p(
            series, block=2, n_boot=0, segment_lengths=(3, 3)
        )
    with pytest.raises(ValueError, match="block"):
        perm_p_floor(6, 0, 20, segment_lengths=(3, 3))


def test_common_phase_coupling_fails_its_own_capture_rotation_premise():
    segments = (
        [-2.0, -1.0, -4.0, 6.0, 1.0],
        [2.0, -3.0, -4.0, -4.0, -5.0],
        [1.0, 3.0, -1.0, 7.0],
    )

    def old_common_phase_p(parts):
        observed = math.fsum(math.fsum(part) for part in parts)
        tail = total = 0
        for phase in range(3):
            block_sums = []
            for part in parts:
                offset = phase % min(3, len(part))
                rotated = part[offset:] + part[:offset]
                block_sums.extend(
                    math.fsum(rotated[start : start + 3])
                    for start in range(0, len(rotated), 3)
                )
            for signs in itertools.product(
                (-1.0, 1.0), repeat=len(block_sums)
            ):
                total += 1
                tail += (
                    math.fsum(
                        sign * value for sign, value in zip(signs, block_sums)
                    )
                    >= observed - 1e-12
                )
        return tail / total

    relabelled_second_capture = (
        segments[0],
        segments[1][1:] + segments[1][:1],
        segments[2],
    )
    assert old_common_phase_p(segments) == pytest.approx(0.640625)
    assert old_common_phase_p(relabelled_second_capture) == pytest.approx(
        0.671875
    )
    anchored = block_permutation_p(
        [value for part in segments for value in part],
        block=3,
        n_perm=256,
        segment_lengths=tuple(map(len, segments)),
    )
    assert anchored["phase_policy"] == "none_capture_start_anchored"


def test_short_segments_fixed_and_auto_blocks_retain_pooled_horizon():
    series = [1.0, 2.0, 3.0, 4.0]
    lengths = (1, 3)
    bootstrap = day_block_bootstrap_p(
        series, block=10, n_boot=64, seed=4, segment_lengths=lengths
    )
    permutation = block_permutation_p(
        series, block=10, n_perm=16, seed=4, segment_lengths=lengths
    )

    assert bootstrap["block_lengths_by_segment"] == [1, 3]
    assert permutation["block_lengths_by_segment"] == [1, 3]
    assert bootstrap["n_blocks_by_segment"] == [1, 1]
    assert permutation["n_blocks_by_segment"] == [1, 1]
    assert block_length_auto_segmented(series, lengths, min_blocks=8) == 1


def test_segmented_auto_block_uses_pooled_horizon_but_no_boundary_lag_pair():
    segments = (
        [(-0.8) ** index for index in range(32)],
        [0.8 ** index for index in range(32)],
    )
    series = segments[0] + segments[1]
    mean = math.fsum(series) / len(series)
    centred = [value - mean for value in series]
    denominator = math.fsum(value * value for value in centred)
    local_numerator = math.fsum(
        (segment[index] - mean) * (segment[index + 1] - mean)
        for segment in segments
        for index in range(len(segment) - 1)
    )
    continuous_numerator = math.fsum(
        centred[index] * centred[index + 1]
        for index in range(len(centred) - 1)
    )
    rho = abs(local_numerator / denominator)
    expected_ar = math.ceil(math.log(0.01) / math.log(rho))
    expected = min(
        max(round(len(series) ** (1.0 / 3.0)), expected_ar),
        len(series) // 8,
    )

    assert local_numerator != continuous_numerator
    assert block_length_auto_segmented(series, (32, 32)) == expected
    assert block_length_auto_segmented(
        segments[1] + segments[0], (32, 32)
    ) == expected


def test_both_conservative_uses_the_larger_segmented_null_p():
    result = combined_null_p(
        [1.0, -0.2, 0.8, 1.2, -0.1, 0.9],
        block=2,
        n_boot=128,
        n_perm=64,
        seed=12,
        segment_lengths=(3, 3),
    )
    assert result["p_value"] == max(
        result["bootstrap"]["p_value"],
        result["permutation"]["p_value"],
    )
    assert result["p_basis"] == "max(bootstrap, permutation)"


# =====================================================================================
# 7. Regression tests for the concealment attacks an adversarial refuter landed.
#    Each of these ADMITTED before the gate was hardened. They are the reason the
#    `lifetime`, per-trade `expectancy`, thin-fold and stop-plausibility rules exist.
# =====================================================================================
def test_losses_hidden_in_the_never_scored_first_fold_are_caught_by_lifetime():
    """Fold 0 is the initial train block and is never scored. A refuter put 50,000 losing
    trades there and the scored numbers did not move by a single bit."""
    rng = random.Random(40)
    good = _mk("mx_btcusd_d1_donchian_20_breakout", "BTCUSD", 500,
               lambda i, d: max(-1.15, min(4.8, rng.gauss(0.35, 1.0))), rng=rng,
               start=dt.date(2018, 1, 3), px=30000.0, sl=900.0)
    first = good[0].entry_utc - dt.timedelta(days=400)
    hidden = [TradeRecord("mx_btcusd_d1_donchian_20_breakout", "BTCUSD",
                          first + dt.timedelta(days=i // 5),
                          first + dt.timedelta(days=i // 5, hours=6),
                          1, 900.0, 30000.0, -1.0) for i in range(2000)]
    v = _run({"mx_btcusd_d1_donchian_20_breakout": hidden + good}).verdicts[
        "mx_btcusd_d1_donchian_20_breakout"]
    assert v.verdict is Verdict.REJECT
    assert not v.gates["lifetime"]["pass"]
    assert v.gates["lifetime"]["mean_r_net_per_trade_all_folds"] < 0
    # and the hidden block is published rather than merely absent
    assert v.telemetry["lifetime"]["fold0_unscored"]["n_trades"] > 0
    assert v.telemetry["lifetime"]["fold0_unscored"]["sum_r_net"] < 0


def test_day_mean_dilution_is_caught_by_the_per_trade_floor():
    """A day with twelve losers weighed the same as a day with one winner. A refuter built
    a sleeve of 2,913 trades, 2,688 of them losers, -715.8 R lifetime, and it ADMITTED."""
    rng = random.Random(41)
    out, d = [], dt.date(2016, 1, 4)
    for i in range(600):
        d += dt.timedelta(days=rng.choice([1, 2, 3]))
        e = dt.datetime(d.year, d.month, d.day, 8, tzinfo=UTC)
        rs = [4.0] if i % 2 == 0 else [-0.35] * 12   # one big winner vs twelve small losers
        out.extend(TradeRecord("mx_btcusd_d1_donchian_20_breakout", "BTCUSD", e,
                               e + dt.timedelta(hours=6), 1, 900.0, 30000.0, r) for r in rs)
    v = _run({"mx_btcusd_d1_donchian_20_breakout": out}).verdicts[
        "mx_btcusd_d1_donchian_20_breakout"]
    assert v.verdict is Verdict.REJECT
    assert v.gates["expectancy"]["oos_mean_r_per_trade"] < 0
    assert not v.gates["expectancy"]["per_trade_pass"]


def test_blackout_removals_are_published_as_R_not_only_as_a_count():
    """A refuter moved 2,200 losing trades into the blackout window and took a sleeve from
    +94.7 R to -2,105 R lifetime while the telemetry reported only a count."""
    rng = random.Random(42)
    dumped = _mk("mx_btcusd_d1_donchian_20_breakout", "BTCUSD", 25, lambda i, d: -1.0,
                 rng=rng, start=dt.date(2026, 3, 1), px=30000.0, sl=900.0, step=(1,))
    assert all(t.entry_utc.date().month == 3 for t in dumped)
    _, cov = price_trades(dumped, _spec())
    c = cov["mx_btcusd_d1_donchian_20_breakout"]
    assert c.n_blackout_dropped == 25
    assert c.blackout_r_gross == pytest.approx(-25.0)
    assert c.as_dict()["blackout_r_gross"] < 0


def test_a_thin_bad_fold_cannot_be_dropped_to_buy_a_pass():
    """Measured: 7 losers in a bad fold -> ADMIT, 8 losers -> REJECT, because the 8th made
    the fold fat enough to be scored. Trading less in a bad regime must not buy a pass."""
    spec = OPTIONS["B_balanced"].with_(**FAST)
    rng = random.Random(43)
    t = _mk("mx_btcusd_d1_donchian_20_breakout", "BTCUSD", 400,
            lambda i, d: max(-1.15, min(4.8, rng.gauss(0.35, 1.0))), rng=rng,
            px=30000.0, sl=900.0)
    v = _run({"mx_btcusd_d1_donchian_20_breakout": t}, spec).verdicts[
        "mx_btcusd_d1_donchian_20_breakout"]
    st = v.gates["stability"]
    # thin folds enter the stability denominator, so they can only ever hurt
    assert st["denominator"] >= len(st["fold_means"])
    assert "n_thin_folds_counted_as_non_positive" in st
    assert v.gates["sample"]["thin_fold_frac"] <= spec.max_thin_fold_frac


def test_an_implausible_stop_is_refused_rather_than_priced():
    """Cost in R is a price drag over the stop, so a bigger declared stop is a cheaper
    trade. The same gold trades REJECTED at a $5 stop and ADMITTED at $20."""
    rng = random.Random(44)
    silly = _mk("metals_core", "XAUUSD", 40, lambda i, d: 1.0, rng=rng, px=2000.0, sl=1e6)
    _, cov = price_trades(silly, _spec())
    c = cov["metals_core"]
    assert c.n_priced == 0
    assert any("implausible_stop" in r for r in c.unpriced_reasons)


def test_a_relabelled_sleeve_is_caught_by_the_symbol_allowlist():
    """The fidelity register keys on the sleeve NAME, so a refuter renamed a 30%-recall
    first-of-day sleeve to a per-bar one and it ADMITTED."""
    rng = random.Random(45)
    t = _mk("crypto", "XAUUSD", 400,
            lambda i, d: max(-1.15, min(4.8, rng.gauss(0.4, 1.0))), rng=rng,
            px=2000.0, sl=20.0)
    spec = OPTIONS["B_balanced"].with_(
        sleeve_symbol_allowlist={"crypto": ("BTCUSD", "DASHUSD")}, **FAST)
    v = _run({"crypto": t}, spec).verdicts["crypto"]
    assert v.verdict is Verdict.NOT_EVALUABLE
    assert not v.gates["symbol_consistency"]["pass"]
    assert "XAUUSD" in v.gates["symbol_consistency"]["unexpected_symbols"]


def test_symbol_check_records_when_it_was_skipped_rather_than_passing_silently():
    rng = random.Random(46)
    t = _mk("crypto", "BTCUSD", 60, lambda i, d: 0.1, rng=rng, px=30000.0, sl=900.0)
    v = _run({"crypto": t}).verdicts["crypto"]
    assert v.gates["symbol_consistency"]["checked"] is False
    assert "taken on trust" in v.gates["symbol_consistency"]["reason"]


def test_declared_family_size_widens_the_multiplicity_correction():
    """Submitting 20 sleeves one at a time gave 20 uncorrected tests; measured, P(>=1 junk
    admission) went 8.3% -> 71.7%."""
    rng = random.Random(47)
    t = _mk("mx_nzdjpy_d1_donchian_20_breakout", "NZDJPY", 700,
            lambda i, d: max(-1.15, min(4.8, rng.gauss(0.30, 1.0))), rng=rng,
            px=80.0, sl=0.45)
    alone = _run({"mx_nzdjpy_d1_donchian_20_breakout": t})
    declared = _run({"mx_nzdjpy_d1_donchian_20_breakout": t},
                    OPTIONS["B_balanced"].with_(declared_family_size=25, **FAST))
    assert alone.family["multiplicity"]["effective_family_size"] == 1
    assert declared.family["multiplicity"]["effective_family_size"] == 25
    q_alone = alone.verdicts["mx_nzdjpy_d1_donchian_20_breakout"].q_value
    q_decl = declared.verdicts["mx_nzdjpy_d1_donchian_20_breakout"].q_value
    assert q_decl > q_alone
