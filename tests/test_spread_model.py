"""Behavioural tests for ``spread_model_v1`` (`src.costs.spread_model`).

These assert what the model *does*. The load-bearing ones are the four that would
have caught the four defects found while building it:

* ``test_every_symbol_with_bars_is_priceable`` -- the first build silently dropped
  EURUSD, the most-traded symbol in the archive, because 100% of its bars inside the
  reference window record spread 0 ("not stored", not "no spread").
* ``test_no_era_band_is_absurdly_wide_unless_flagged`` -- an early build published
  USDJPY 2021 as ``mid=20.25`` with a band of [0.47, 867]. A band that wide is a
  capture requirement, not a result, and it must say so.
* ``test_schedule_eras_are_never_certain`` -- a backfilled constant makes every
  estimator agree, which collapsed DASHUSD 2026Q1 to a zero-width band on the era
  where the data is *least* trustworthy.
* ``test_cost_r_is_byte_identical_without_a_band`` -- the integration is opt-in, and
  the whole point of opt-in is that nothing that does not ask for it can change.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.costs import Coverage, CostTruthError, cost_r
from src.costs.spread_model import (
    BANDS,
    SpreadModelError,
    load_spread_model,
    spread_price,
)

REPO = Path(__file__).resolve().parents[1]
MODEL = REPO / "research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json"

pytestmark = pytest.mark.skipif(
    not MODEL.is_file(),
    reason="SPREAD_MODEL_V1.json absent; build with scripts/build_spread_model.py",
)


@pytest.fixture(scope="module")
def model():
    return load_spread_model()


@pytest.fixture(scope="module")
def doc():
    return json.loads(MODEL.read_text())


# --------------------------------------------------------------- shape and ordering


def test_bands_are_ordered_low_mid_high(model):
    t = datetime(2019, 6, 15, 12, tzinfo=timezone.utc)
    for sym in ("XAUUSD", "USDJPY", "EURUSD", "US30_cash"):
        lo, mid, hi = (spread_price(sym, "FTMO", t, band=b, model=model).spread_price
                       for b in BANDS)
        assert lo <= mid <= hi, f"{sym}: band not ordered ({lo}, {mid}, {hi})"
        assert lo > 0


def test_every_symbol_with_bars_is_priceable(model, doc):
    """Every profile-declared symbol in the archive is priceable; stale extras are not."""
    from src.costs.symbols import canonical_symbol

    for acct in doc["accounts"]:
        syms = model.symbols(acct)
        assert syms, f"{acct} has no symbols"
        for sym in syms:
            if canonical_symbol(sym) is None:
                continue
            est = spread_price(sym, acct, datetime(2025, 6, 2, 12, tzinfo=timezone.utc),
                               model=model)
            assert est.spread_price > 0
    assert "EURUSD" in model.symbols("FTMO")
    with pytest.raises(SpreadModelError, match="not in the spread model"):
        spread_price("ADAUSD", "FTMO", model=model)


def test_the_three_naming_conventions_reach_the_same_instrument(model):
    """Ticks say `US30_cash`, bars say `US30_cash`, the broker quotes `US30.cash`."""
    t = datetime(2025, 6, 2, 12, tzinfo=timezone.utc)
    a = spread_price("US30_cash", "FTMO", t, model=model).spread_price
    b = spread_price("US30.cash", "FTMO", t, model=model).spread_price
    assert a == b


def test_unknown_symbol_refuses_rather_than_guessing(model):
    with pytest.raises(SpreadModelError, match="not in the spread model"):
        spread_price("NOT_A_SYMBOL", "FTMO", model=model)
    with pytest.raises(SpreadModelError, match="no spread model for account"):
        spread_price("XAUUSD", "NotABroker", model=model)


def test_bad_band_name_refuses(model):
    with pytest.raises(SpreadModelError, match="band must be one of"):
        spread_price("XAUUSD", "FTMO", band="p50", model=model)


# ------------------------------------------------------------------ band integrity


def test_no_era_band_is_absurdly_wide_unless_flagged(doc):
    """The artifact width bit is internally consistent; runtime also vetoes SCHEDULE.

    SCHEDULE's generated bit is historical evidence of the Wave-21 inversion, not the
    semantic answer: `SpreadModel.estimate` now makes those rows undecidable regardless
    of their degenerate width (covered adversarially in test_cost_truth_wave21.py).
    """
    thresh = 0.5
    for acct, syms in doc["accounts"].items():
        for sym, rec in syms.items():
            for q, e in rec["eras"].items():
                hw = e["band_halfwidth_log_floored"]
                if hw > thresh:
                    assert not e["decidable"], f"{acct} {sym} {q}: hw={hw} but decidable"
                    assert e.get("capture_requirement"), (
                        f"{acct} {sym} {q} is undecidable and publishes no capture "
                        "requirement -- an undecidable band must say what would close it")
                elif e["class"] != "SCHEDULE":
                    assert e["decidable"]


def test_schedule_eras_are_never_certain(doc):
    """A backfilled constant makes every estimator agree; that is not certainty."""
    floors = doc["class_halfwidth_floors"]
    for acct, syms in doc["accounts"].items():
        f = floors[acct]
        assert f["SCHEDULE"] > 0 and f["QUANTIZED"] > 0 and f["FLOORED"] > 0
        for sym, rec in syms.items():
            for q, e in rec["eras"].items():
                if e["class"] != "RECORDED":
                    # stored floored to 5dp, so compare at that precision
                    assert e["band_halfwidth_log_floored"] >= f[e["class"]] - 1e-5, (
                        f"{acct} {sym} {q} is {e['class']} with half-width "
                        f"{e['band_halfwidth_log_floored']} below the class floor")


def test_band_halfwidth_is_never_below_its_measured_components(doc):
    for acct, syms in doc["accounts"].items():
        for sym, rec in syms.items():
            for q, e in rec["eras"].items():
                parts = (e["cross_instrument_dispersion_log"], e["split_half_noise_log"],
                         e["d1_vs_h4_disagreement_log"])
                assert e["band_halfwidth_log"] >= max(parts) - 1e-9
                assert e["era_ratio_low"] <= e["era_ratio_mid"] <= e["era_ratio_high"]


def test_reference_era_ratio_is_about_one(doc):
    """The reference quarter must price to roughly the anchor, or the ratio is mis-scaled."""
    off = []
    for sym, rec in doc["accounts"]["FTMO"].items():
        e = rec["eras"].get("2026Q3")
        if e and e["class"] == "RECORDED":
            off.append(abs(math.log(e["era_ratio_mid"])))
    assert off, "no RECORDED 2026Q3 era to check the reference against"
    off.sort()
    assert off[len(off) // 2] < 0.35, f"median |log ratio| at the reference is {off[len(off)//2]}"


# ------------------------------------------------------- coverage class propagation


def test_schedule_era_is_modelled_not_measured(model):
    """EURUSD 2000 is a broker backfill constant. It cannot be reported as MEASURED."""
    e = spread_price("EURUSD", "FTMO", datetime(2002, 6, 3, 12, tzinfo=timezone.utc),
                     model=model)
    assert e.era_class == "SCHEDULE"
    assert e.coverage is Coverage.MODELLED


def test_recorded_era_on_a_tick_anchored_symbol_stays_measured(model):
    e = spread_price("XAUUSD", "FTMO", datetime(2026, 7, 1, 12, tzinfo=timezone.utc),
                     model=model)
    assert e.era_class == "RECORDED"
    # `decidable` is asserted explicitly, not assumed. RECORDED alone stopped being
    # sufficient for MEASURED on 2026-07-30 (B1250): if this era ever went undecidable the
    # test would fail for a reason that has nothing to do with what it is checking, and a
    # reader would chase the anchor instead of the band.
    assert e.decidable
    assert e.coverage is Coverage.MEASURED


# --------------------------------------------- undecidability degrades on EVERY path (B1250)
#
# The defect: `Coverage` degraded on `era_class` alone, so an UNDECIDABLE **RECORDED** era
# matched no branch and kept the anchor's own class. `BTCUSD 2020Q1` returned MEASURED on a
# band whose `capture_requirement` reads "band spans 204058.1x, wider than any verdict can
# survive", and every `coverage_policy="restrict_to_priced"` consumer accepted it as priced.
#
# These four are written as invariants over the whole model rather than as probes of that one
# quarter, because the quarter is an instance and the rule is the claim: 182 of the model's
# 275 undecidable eras are RECORDED.


def _quarter_mid(q: str) -> datetime:
    return datetime(int(q[:4]), (int(q[-1]) - 1) * 3 + 2, 15, 12, tzinfo=timezone.utc)


def test_the_204058x_band_no_longer_prices_as_measured(model, doc):
    """The named instance, kept because it is the one that was found in the field.

    Session AL measured `BTCUSD 2020Q1 -> RECORDED / decidable False / coverage MEASURED`
    while the era's own artifact called it a capture requirement.
    """
    era = doc["accounts"]["FTMO"]["BTCUSD"]["eras"]["2020Q1"]
    assert era["class"] == "RECORDED" and not era["decidable"]
    assert "204058" in str(era.get("capture_requirement", "")), (
        "this test is anchored on the era AL found; if the artifact was rebuilt, re-point it")
    e = spread_price("BTCUSD", "FTMO", _quarter_mid("2020Q1"), model=model)
    assert e.era == "2020Q1" and e.era_class == "RECORDED" and not e.decidable
    assert e.coverage is Coverage.MODELLED


def test_no_undecidable_era_anywhere_reports_measured(model, doc):
    """The general claim. One quarter is an anecdote; the rule is what a consumer relies on."""
    from src.costs.symbols import canonical_symbol

    checked = recorded = 0
    for account, syms in doc["accounts"].items():
        for sym, rec in syms.items():
            if canonical_symbol(sym) is None:
                continue
            if rec.get("era_fallback") is not None:
                continue
            for q, era in (rec.get("eras") or {}).items():
                if era.get("decidable", True):
                    continue
                e = spread_price(sym, account, _quarter_mid(q), model=model)
                if e.era != q:      # the nearest-era fallback moved us off this quarter
                    continue
                checked += 1
                recorded += era["class"] == "RECORDED"
                assert e.coverage is not Coverage.MEASURED, (
                    f"{account} {sym} {q} [{era['class']}] is undecidable and prices as "
                    f"MEASURED: {era.get('capture_requirement')}")
    assert checked >= 200, f"only {checked} undecidable eras reached; expected ~275"
    assert recorded >= 100, (
        f"only {recorded} of the undecidable eras checked are RECORDED — the class this "
        "repair exists for. If this collapses, the test has stopped covering the defect.")


def test_undecidable_never_strengthens_coverage(model, doc):
    """Monotonicity: the repair may only ever weaken a coverage class, never strengthen one.

    The pre-repair rule is reproduced inline from the two fields it read, so this test also
    documents what changed and would fail if a future edit made any era MORE confident than
    the class-only rule made it.
    """
    from src.costs.coverage import weakest
    from src.costs.symbols import canonical_symbol

    moved = 0
    for account, syms in doc["accounts"].items():
        for sym, rec in syms.items():
            if canonical_symbol(sym) is None:
                continue
            if rec.get("era_fallback") is not None:
                continue
            anchor = Coverage(rec["anchor_coverage"])
            for q, era in (rec.get("eras") or {}).items():
                e = spread_price(sym, account, _quarter_mid(q), model=model)
                if e.era != q:
                    continue
                before = anchor
                if e.era_class not in ("RECORDED", "NO_BAR_HISTORY"):
                    before = weakest(before, Coverage.MODELLED
                                     if e.era_class in ("SCHEDULE", "FLOORED")
                                     else Coverage.TRANSFERRED)
                if e.detail["era_gap_quarters"]:
                    before = Coverage.MODELLED
                assert e.coverage.strength >= before.strength, (
                    f"{account} {sym} {q} got STRONGER: {before.value} -> "
                    f"{e.coverage.value}")
                moved += e.coverage is not before
    assert moved >= 150, (
        f"only {moved} era cells changed coverage class; the measured figure is 192 "
        "(166 RECORDED MEASURED->MODELLED + 26 QUANTIZED TRANSFERRED->MODELLED)")


def test_what_measured_coverage_exactly_means(model, doc):
    """The exact predicate for `coverage is MEASURED`, and it needs FOUR clauses not three.

    A first version of this test asserted `MEASURED <=> anchor MEASURED and RECORDED and
    decidable` and passed — but only because its scope could not contain a counterexample: it
    skipped every `era_fallback` symbol and every cell where the nearest-era fallback moved off
    the requested quarter, which are the two families where that form breaks. An adversarial
    pass over the claim found 1,005 mismatches in an exhaustive probe.

    The scope here is deliberately the EXHAUSTIVE cross-product — every symbol against every era
    key its ACCOUNT carries, plus the reference instant — so the two missing clauses are
    reachable, and the test asserts they are individually load-bearing rather than trusting that
    they are.
    """
    from src.costs.symbols import canonical_symbol

    n = 0
    would_fail_without_gap = would_fail_without_class = 0
    for account, syms in doc["accounts"].items():
        all_q = sorted({q for r in syms.values() for q in (r.get("eras") or {})})
        for sym, rec in syms.items():
            if canonical_symbol(sym) is None:
                continue
            anchor_measured = Coverage(rec["anchor_coverage"]) is Coverage.MEASURED
            probes = [_quarter_mid(q) for q in all_q] + [None]
            for t in probes:
                try:
                    e = spread_price(sym, account, t, model=model)
                except SpreadModelError:
                    continue
                n += 1
                want = (anchor_measured
                        and e.detail["era_gap_quarters"] == 0
                        and e.era_class in ("RECORDED", "NO_BAR_HISTORY", "REFERENCE")
                        and e.decidable)
                assert (e.coverage is Coverage.MEASURED) is want, (
                    f"{account} {sym} at {t}: coverage {e.coverage.value}, class "
                    f"{e.era_class}, decidable {e.decidable}, gap "
                    f"{e.detail['era_gap_quarters']}, anchor_measured {anchor_measured}")
                # ...and each dropped clause must actually be doing work.
                three_clause = (anchor_measured and e.era_class == "RECORDED" and e.decidable)
                if three_clause != want:
                    if e.detail["era_gap_quarters"]:
                        would_fail_without_gap += 1
                    else:
                        would_fail_without_class += 1
    assert n >= 7500, (
        f"only {n} probes; the exhaustive profile-authorized cross-product should "
        "exceed 7,500"
    )
    assert would_fail_without_gap >= 50, (
        f"only {would_fail_without_gap} probes distinguish the `gap == 0` clause; if this "
        "collapses the test has stopped covering the family it was written for")
    assert would_fail_without_class >= 50, (
        f"only {would_fail_without_class} probes distinguish the wider era_class set")


def test_cost_r_carries_the_degradation_to_its_consumer(model):
    """The repair is worthless if it stops at the model. `cost_r` must hand it on."""
    base = dict(holding_hours=6.0, sl_distance_price=900.0, entry_price=9000.0)
    bad = cost_r("BTCUSD", "FTMO", entry_utc=_quarter_mid("2020Q1"), spread_band="mid",
                 spread_model=model, **base)
    assert bad.spread_r.coverage is Coverage.MODELLED
    assert bad.total_r.coverage is Coverage.MODELLED
    assert bad.detail["spread"]["decidable"] is False
    # ...and a decidable RECORDED era on the same symbol still prices as MEASURED, so the
    # degradation is about the band and not about the symbol.
    good = cost_r("BTCUSD", "FTMO", entry_utc=datetime(2024, 5, 15, 12, tzinfo=timezone.utc),
                  spread_band="mid", spread_model=model, **base)
    assert good.detail["spread"]["decidable"] is True
    assert good.spread_r.coverage is Coverage.MEASURED


def test_bar_anchored_symbol_is_never_measured(model, doc):
    """A symbol with no tick file cannot claim a measured spread, ever."""
    from src.costs.symbols import canonical_symbol

    bar_only = [s for s, r in doc["accounts"]["FTMO"].items()
                if canonical_symbol(s) is not None
                and r["anchor_coverage"] != "MEASURED"]
    assert bar_only, "expected symbols priced from bars alone"
    for sym in bar_only:
        e = spread_price(sym, "FTMO", datetime(2025, 6, 2, 12, tzinfo=timezone.utc),
                         model=model)
        assert e.coverage is not Coverage.MEASURED


def test_require_decidable_refuses_an_undecidable_era(model, doc):
    from src.costs.symbols import canonical_symbol

    hits = [(s, q) for s, r in doc["accounts"]["FTMO"].items()
            if canonical_symbol(s) is not None
            for q, e in r["eras"].items() if not e["decidable"]]
    assert hits, "expected at least one undecidable era"
    sym, q = hits[0]
    t = datetime(int(q[:4]), (int(q[-1]) - 1) * 3 + 2, 15, 12, tzinfo=timezone.utc)
    got = spread_price(sym, "FTMO", t, model=model)
    if got.era == q:  # the nearest-era fallback may have moved us to a decidable one
        with pytest.raises(SpreadModelError, match="not decidable"):
            spread_price(sym, "FTMO", t, require_decidable=True, model=model)


# ------------------------------------------------------------- the era claim itself


def test_the_era_effect_is_large_and_signed_both_ways(model):
    """The headline. If this ever collapses to ~1x the model has stopped doing its job.

    The estate's standing disclosure says spreads compressed, so history is optimistic.
    Measured: true for FX, INVERTED for metals. Both directions must survive.
    """
    fx = spread_price("EURUSD", "FTMO", datetime(2002, 6, 3, 12, tzinfo=timezone.utc),
                      model=model)
    now = spread_price("EURUSD", "FTMO", datetime(2026, 7, 1, 12, tzinfo=timezone.utc),
                       model=model)
    assert fx.era_ratio > 10, "EURUSD 2002 measured at 50x the reference snapshot"

    metal = spread_price("XAUUSD", "FTMO", datetime(2022, 6, 15, 12, tzinfo=timezone.utc),
                         model=model)
    assert metal.era_ratio < 0.5, "XAUUSD 2022 measured at ~0.18x -- today is DEARER"


def test_hour_of_week_is_read_on_the_broker_wall_clock(model):
    """Not UTC. FTMO-Server3 is America/New_York + 7h and switches on US DST dates."""
    # Mon 2026-01-05 22:30Z. New York is on EST in January, so the broker wall is
    # UTC+2 (NY+7), NOT the +3 that holds inside the summer tick window: 00:30 Tuesday.
    a = model.intraweek_mult("FTMO", "metals",
                             datetime(2026, 1, 5, 22, 30, tzinfo=timezone.utc))[1]
    assert a["hour_of_week_brokerwall"] == 1 * 24 + 0
    # ...and the same instant in July, when NY is on EDT, lands an hour later.
    c = model.intraweek_mult("FTMO", "metals",
                             datetime(2026, 7, 6, 22, 30, tzinfo=timezone.utc))[1]
    assert c["hour_of_week_brokerwall"] == 1 * 24 + 1
    b = model.era_key(datetime(2019, 12, 31, 22, 30, tzinfo=timezone.utc), "FTMO")
    assert b == "2020Q1", "a UTC-read quarter boundary silently mismatches the bar archive"


# -------------------------------------------------------------- cost_r integration


_BASE = dict(holding_hours=5.0, sl_distance_price=20.0, entry_price=4000.0)


def _a_symbol_the_snapshot_refuses() -> str:
    """A symbol with no measured spread, chosen FROM THE ARTIFACT rather than hardcoded.

    Three tests in this file originally named `CADJPY` and `EU50.cash`, because those were
    unpriced when it was written. Both gained a tick file **while this session was running**
    (FTMO spread:MEASURED went 30 -> 36), and all three went red on premises the data had
    overtaken rather than on any change to the code. The prompt for this session said in so
    many words: re-read the artifact rather than assuming any symbol is unpriced. A test
    that hardcodes a coverage fact has to be re-read too.
    """
    from src.costs import load_broker_true_costs
    from src.costs.symbols import canonical_symbol

    insts = load_broker_true_costs().doc["accounts"]["FTMO"]["instruments"]
    # Commission is charged BEFORE spread, and an instrument with an unknown commission
    # schedule refuses there first -- which would test the wrong refusal.
    unpriced = sorted(s for s, r in insts.items()
                      if canonical_symbol(s) is not None
                      and not r.get("spread_price") and _commission_resolves(r))
    assert unpriced, "every FTMO instrument now has a measured spread -- retire these tests"
    return unpriced[0]


def _commission_resolves(rec: dict) -> bool:
    return (rec.get("commission") or {}).get("kind") in ("zero", "per_lot", "notional_bp")


def test_cost_r_is_byte_identical_without_a_band():
    """Opt-in means opt-in: no band, no change, including the refusal path."""
    a = cost_r("XAUUSD", "FTMO", **_BASE)
    assert a.spread_r.coverage is Coverage.MEASURED
    assert a.detail["spread"]["percentile"] == "p50"
    assert "source" not in a.detail["spread"]
    with pytest.raises(CostTruthError, match="no measured spread"):
        cost_r(_a_symbol_the_snapshot_refuses(), "FTMO", 5.0,
               sl_distance_price=0.5, entry_price=110.0,
               entry_utc=datetime(2026, 6, 20, 12, tzinfo=timezone.utc))


def test_cost_r_bands_move_the_total_in_the_right_direction():
    t = datetime(2021, 6, 15, 12, tzinfo=timezone.utc)
    vals = [cost_r("XAUUSD", "FTMO", entry_utc=t, spread_band=b, **_BASE)
            for b in BANDS]
    assert vals[0].spread_r.value < vals[1].spread_r.value < vals[2].spread_r.value
    assert vals[0].total_r.value < vals[1].total_r.value < vals[2].total_r.value
    for v in vals:
        # Session AH added the composition to this label ("spread_model[v2_damped]") when it
        # repaired the era x hour product, so the assertion is on the model path being taken
        # rather than on the exact string. The three quantities above are the behaviour.
        assert v.detail["spread"]["source"].startswith("spread_model")
        assert v.detail["spread"]["era_ratio"] > 0


def test_cost_r_prices_a_symbol_the_snapshot_refuses(model):
    """The spread term becomes decidable; an absent slippage term stays unpriced.

    Whichever symbol that is today -- it was `CADJPY`, which made
    `mx_cadjpy_d1_volume_surge_reversal` unjudgeable in W's pilot until its tick file
    landed. The claim under test is the behaviour, not the symbol.
    """
    from src.costs import load_broker_true_costs
    from src.costs.symbols import canonical_symbol

    insts = load_broker_true_costs().doc["accounts"]["FTMO"]["instruments"]
    sym = next((s for s in model.symbols("FTMO") if canonical_symbol(s) is not None
                if _snapshot_refuses(s) and not _no_bar_history(model, s)
                and _commission_resolves(insts.get(s) or {})), None)
    if sym is None:
        pytest.skip("no symbol is currently snapshot-refused but bar-priceable")
    with pytest.raises(CostTruthError):
        cost_r(sym, "FTMO", 5.0, sl_distance_price=0.5, entry_price=110.0)
    at = datetime(2019, 6, 15, tzinfo=timezone.utc)
    e = model.estimate(sym, "FTMO", at, band="mid")
    assert e.spread_price > 0
    assert e.coverage is not Coverage.MEASURED
    with pytest.raises(CostTruthError, match="slippage|NOT_EVALUABLE"):
        cost_r(sym, "FTMO", 5.0, sl_distance_price=0.5, entry_price=110.0,
               entry_utc=at, spread_band="mid")


def _snapshot_refuses(sym: str) -> bool:
    from src.costs import load_broker_true_costs

    rec = load_broker_true_costs().doc["accounts"]["FTMO"]["instruments"].get(sym) or {}
    return not rec.get("spread_price")


def _no_bar_history(model, sym: str) -> bool:
    try:
        return bool(model.record(sym, "FTMO").get("no_bar_history"))
    except SpreadModelError:
        return True


def test_cost_r_still_refuses_a_symbol_with_neither_ticks_nor_bars(model):
    """Absence is still absence. A band is not a licence to invent one.

    (This named `EU50.cash` until its tick file landed mid-session. It is now
    tick-measured with no bar history, which is a band -- not a refusal. The symbol
    is therefore chosen from the data, like the others.)
    """
    from src.costs import load_broker_true_costs
    from src.costs.symbols import canonical_symbol

    insts = load_broker_true_costs().doc["accounts"]["FTMO"]["instruments"]
    sym = next((s for s in sorted(insts) if canonical_symbol(s) is not None
                if not insts[s].get("spread_price") and _no_bar_history(model, s)
                and _commission_resolves(insts[s])), None)
    assert sym, "expected at least one instrument with neither a tick file nor a bar file"
    with pytest.raises(CostTruthError, match="cannot price"):
        cost_r(sym, "FTMO", 5.0, sl_distance_price=50.0, entry_price=5000.0,
               entry_utc=datetime(2019, 6, 15, tzinfo=timezone.utc), spread_band="mid")


def test_era_costing_changes_a_verdict_sized_amount():
    """The look-ahead is first-order, which is the whole reason this exists."""
    flat = cost_r("XAUUSD", "FTMO", **_BASE).spread_r.value
    era = cost_r("XAUUSD", "FTMO", entry_utc=datetime(2022, 6, 15, tzinfo=timezone.utc),
                 spread_band="mid", **_BASE).spread_r.value
    assert era < flat / 3, (
        f"charging the 2026 snapshot to 2022 XAUUSD overcharges spread {flat/era:.1f}x")


def test_quantized_era_is_not_reported_as_measured(model):
    """A degraded era cannot come back MEASURED just because the anchor was.

    `Coverage.strength` is 0 for MEASURED and 2 for MODELLED, so a `min(..., key=strength)`
    over (anchor, TRANSFERRED) returns the STRONGEST of the two. An earlier revision did
    exactly that and reported a QUANTIZED era on a tick-anchored symbol as MEASURED.
    """
    e = spread_price("USDJPY", "FTMO", datetime(2026, 2, 3, 12, tzinfo=timezone.utc),
                     model=model)
    assert e.era_class == "QUANTIZED"
    assert e.coverage is not Coverage.MEASURED


def test_a_far_era_extrapolation_is_not_decidable(model):
    """BTCUSD starts years after 2010 and must not answer that era confidently."""
    t = datetime(2010, 6, 15, 12, tzinfo=timezone.utc)
    e = spread_price("BTCUSD", "FTMO", t, model=model)
    assert e.detail["era_gap_quarters"] > 8
    assert not e.decidable
    assert e.coverage is Coverage.MODELLED
    with pytest.raises(SpreadModelError, match="quarters outside"):
        spread_price("BTCUSD", "FTMO", t, require_decidable=True, model=model)


# ------------------------------------------- symbols with ticks but no bar history


def test_a_band_is_never_worse_than_no_band(model, doc):
    """The rule that makes the whole opt-in defensible.

    Tick files can exist outside the exact live-profile authority. For each profile-declared
    tick-measured instrument, passing a band must not turn a priceable symbol into a refusal.
    """
    from src.costs import CostTruthError, load_broker_true_costs
    from src.costs.symbols import canonical_symbol

    truth = load_broker_true_costs()
    when = datetime(2026, 7, 1, 12, tzinfo=timezone.utc)
    checked = 0
    for sym, rec in truth.doc["accounts"]["FTMO"]["instruments"].items():
        if canonical_symbol(sym) is None or not rec.get("spread_price"):
            continue          # the snapshot refuses it too; nothing to compare
        checked += 1
        spread_price(sym, "FTMO", when, band="mid", model=model)  # must not raise
    assert checked >= 30, f"only {checked} tick-measured symbols checked"


def test_no_bar_history_symbols_are_priced_and_flagged(model, doc):
    from src.costs.symbols import canonical_symbol

    tick_only = [s for s, r in doc["accounts"]["FTMO"].items()
                 if canonical_symbol(s) is not None and r.get("no_bar_history")]
    assert tick_only, "expected symbols with a tick file and no bar file"
    for sym in tick_only:
        at_ref = spread_price(sym, "FTMO", datetime(2026, 7, 1, 12, tzinfo=timezone.utc),
                              model=model)
        assert at_ref.spread_price > 0
        assert at_ref.era_class == "NO_BAR_HISTORY"
        # Known precisely today...
        assert at_ref.decidable and at_ref.coverage is Coverage.MEASURED
        # ...and not at all in the past.
        old = spread_price(sym, "FTMO", datetime(2015, 6, 15, 12, tzinfo=timezone.utc),
                           model=model)
        assert not old.decidable
        assert old.coverage is Coverage.MODELLED
        lo, hi = (spread_price(sym, "FTMO", datetime(2015, 6, 15, 12, tzinfo=timezone.utc),
                               band=b, model=model).spread_price for b in ("low", "high"))
        assert lo < old.spread_price < hi, "a symbol with no history must carry a real band"
        assert doc["accounts"]["FTMO"][sym]["era_fallback"]["capture_requirement"]
