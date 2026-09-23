"""The era-quality population rule, wired (Session AN, B1251-B1252).

What these pin, in the order they matter:

* the four rules produce four DIFFERENT seals — the defect being that AL's three
  implementations were pre-gate filters, so two runs on two populations sealed identically;
* `spread_require_decidable` is seal-honest: None and False hash like the pre-field spec,
  True does not;
* the flag actually reaches `spread_price` from a `GateSpec`, end to end through
  `panel.price_trades`, and the refusal it produces is recorded as an unpriced trade with a
  reason `decidability_refusals` can see;
* the population is band-INDEPENDENT, which is what licenses computing it once and reusing it
  at low/mid/high;
* filtering and flagging are NOT the same operation — the measured difference under the two
  coverage policies is the reason both halves exist.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from src.costs import Coverage
from src.costs.spread_model import load_spread_model
from src.research_infra.walkforward import era_population as EP
from src.research_infra.walkforward.options import OPTIONS
from src.research_infra.walkforward.panel import TradeRecord, price_trades

REPO = Path(__file__).resolve().parents[2]
MODEL = REPO / "research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json"

pytestmark = pytest.mark.skipif(not MODEL.is_file(), reason="SPREAD_MODEL_V1.json absent")

# BTCUSD, because it is the symbol the whole question was found on: 2020Q1 is RECORDED and
# UNDECIDABLE (a 204,058x band), 2024Q2 is RECORDED and decidable, 2021Q3 is SCHEDULE and
# "decidable" only because a degenerate zero-width band is floored to 0.18229.
_UNDECIDABLE = dt.datetime(2020, 2, 15, 12, tzinfo=dt.timezone.utc)
_DECIDABLE = dt.datetime(2024, 5, 15, 12, tzinfo=dt.timezone.utc)
_SCHEDULE = dt.datetime(2021, 8, 15, 12, tzinfo=dt.timezone.utc)


def _trade(entry: dt.datetime, sleeve: str = "probe") -> TradeRecord:
    return TradeRecord(
        sleeve=sleeve, symbol="BTCUSD", entry_utc=entry,
        exit_utc=entry + dt.timedelta(hours=6), direction=1,
        sl_distance_price=900.0, entry_price=9000.0, r_gross=1.0,
    )


@pytest.fixture(scope="module")
def model():
    return load_spread_model()


# ------------------------------------------------------------------ the rules themselves


def test_the_rule_set_is_closed_and_every_rule_carries_its_argument():
    assert set(EP.RULES) == {"ALL_ERAS", "RECORDED", "DECIDABLE", "RECORDED_AND_DECIDABLE",
                             "RECORDED_UNDECIDABLE"}
    assert EP.CANDIDATE_RULES == ("ALL_ERAS", "RECORDED", "DECIDABLE",
                                  "RECORDED_AND_DECIDABLE")
    assert "RECORDED_UNDECIDABLE" not in EP.CANDIDATE_RULES, (
        "the disputed-trade population is a diagnostic, never a candidate rule")
    for name, r in EP.RULES.items():
        assert r.name == name
        assert len(r.why) > 80, f"{name} has no argument attached to it"


def test_no_default_rule_exists():
    """The defect was a population that arrived by default. There must be no default."""
    assert not hasattr(EP, "DEFAULT_RULE")
    with pytest.raises(KeyError, match="unknown population rule"):
        EP.spec_for("recorded", OPTIONS["B_balanced"])       # case matters, deliberately


def test_the_four_rules_disagree_on_the_three_era_kinds():
    cases = {"ALL_ERAS": (True, True, True), "RECORDED": (True, True, False),
             "DECIDABLE": (False, True, True), "RECORDED_AND_DECIDABLE": (False, True, False),
             "RECORDED_UNDECIDABLE": (True, False, False)}
    for rule, want in cases.items():
        keep = EP.RULES[rule].keep
        got = (keep("RECORDED", False), keep("RECORDED", True), keep("SCHEDULE", True))
        assert got == want, f"{rule}: {got} != {want}"


# ------------------------------------------------------------------------------- the seal


def test_each_population_rule_produces_a_DIFFERENT_seal():
    """The wave-9 defect: two runs, two populations, one `spec_sha256`."""
    base = OPTIONS["B_balanced"]
    seals = {r: EP.spec_for(r, base).seal() for r in EP.RULES}
    assert len(set(seals.values())) == len(seals), (
        f"populations collide in the seal: {seals}")
    assert base.seal() not in set(seals.values()), (
        "a restricted population must not seal as the unrestricted spec")
    for r, spec in ((r, EP.spec_for(r, base)) for r in EP.RULES):
        assert spec.spec_id.endswith(f"|pop={r}")


def test_require_decidable_is_seal_honest():
    """None and False mean the pre-field behaviour, so they must hash like it. True must not.

    This is `spread_composition`'s rule and NOT `_ABSENT_MEANS_UNCHANGED`'s: dropping at None
    while keeping False would seal the same methodology two ways.
    """
    base = OPTIONS["B_balanced"]
    assert base.spread_require_decidable is None
    pre = base.seal()
    assert base.with_(spread_require_decidable=False).seal() == pre
    assert base.with_(spread_require_decidable=None).seal() == pre
    assert base.with_(spread_require_decidable=True).seal() != pre
    assert "spread_require_decidable" not in base.canonical()
    assert base.with_(spread_require_decidable=True).canonical()[
        "spread_require_decidable"] is True


def test_spec_for_sets_the_flag_only_where_the_rule_needs_it():
    base = OPTIONS["B_balanced"]
    for r in EP.RULES:
        got = EP.spec_for(r, base).spread_require_decidable
        assert bool(got) == EP.RULES[r].require_decidable, r
    assert EP.spec_for("RECORDED", base).spread_require_decidable is None, (
        "RECORDED must NOT refuse undecidable eras — that is the whole disagreement")


# ------------------------------------------------------- the flag reaches the cost layer


def test_the_flag_reaches_spread_price_from_a_gatespec(model):
    """End to end: GateSpec -> panel.price_trades -> cost_r -> spread_price."""
    spec = OPTIONS["B_balanced"].with_(spread_band="mid")
    trades = {"probe": [_trade(_UNDECIDABLE), _trade(_DECIDABLE)]}

    off, cov_off = price_trades(trades["probe"], spec)
    assert [p.status for p in off] == ["priced", "priced"], (
        "without the flag an undecidable era is priced — that is the pre-field behaviour")

    on, cov_on = price_trades(trades["probe"], spec.with_(spread_require_decidable=True))
    assert [p.status for p in on] == ["unpriced", "priced"]
    assert cov_on["probe"].n_unpriced == 1
    assert EP.decidability_refusals(cov_on["probe"].as_dict()) == 1, (
        f"the refusal reason is not recognisable: {cov_on['probe'].unpriced_reasons}")
    assert EP.decidability_refusals(cov_off["probe"].as_dict()) == 0


def test_the_undecidable_trade_is_still_MODELLED_when_the_flag_is_off(model):
    """The coverage repair and the flag are independent, and both must work.

    With the flag off the trade is priced — but its SPREAD term can no longer claim MEASURED
    (B1250), and the sleeve's `weakest_coverage` records it.

    The Wave-21 slippage repair is exact-account/symbol MEASURED on BTCUSD, so the good
    era can now be fully measured. The bad era still degrades through spread, which makes
    both the per-term class and `measured_frac` observable.
    """
    from src.costs import cost_r

    spec = OPTIONS["B_balanced"].with_(spread_band="mid")
    priced, cov = price_trades([_trade(_UNDECIDABLE), _trade(_DECIDABLE)], spec)
    assert cov["probe"].n_priced == 2
    assert cov["probe"].weakest_coverage is Coverage.MODELLED

    base = dict(holding_hours=6.0, sl_distance_price=900.0, entry_price=9000.0,
                spread_band="mid", spread_model=model)
    bad = cost_r("BTCUSD", "FTMO", entry_utc=_UNDECIDABLE, **base)
    good = cost_r("BTCUSD", "FTMO", entry_utc=_DECIDABLE, **base)
    assert bad.spread_r.coverage is Coverage.MODELLED
    assert good.spread_r.coverage is Coverage.MEASURED
    assert good.slippage_r.coverage is Coverage.MEASURED
    assert good.total_r.coverage is Coverage.MEASURED
    assert cov["probe"].measured_frac == pytest.approx(0.5)


# -------------------------------------------------------------- band independence


def test_the_population_is_band_independent(model):
    """`era_class` and `decidable` are not functions of the band. Only `era_ratio` is.

    Checked over every era in the model rather than argued from the source, because the whole
    point is that a caller may compute the population ONCE and reuse it at all three bands —
    and if that were ever false, three tables would silently disagree.
    """
    doc = json.loads(MODEL.read_text())
    from src.costs.symbols import canonical_symbol

    n = 0
    for account, syms in doc["accounts"].items():
        for sym, rec in syms.items():
            if canonical_symbol(sym) is None:
                continue
            for q in (rec.get("eras") or {}):
                t = dt.datetime(int(q[:4]), (int(q[-1]) - 1) * 3 + 2, 15, 12,
                               tzinfo=dt.timezone.utc)
                got = {b: model.estimate(sym, account, t, band=b) for b in
                       ("low", "mid", "high")}
                classes = {e.era_class for e in got.values()}
                decs = {bool(e.decidable) for e in got.values()}
                assert len(classes) == 1 and len(decs) == 1, f"{account} {sym} {q}"
                n += 1
    assert n >= 2000, f"only {n} era cells checked"


# ------------------------------- filtering and flagging are not the same operation


def test_filter_and_flag_agree_on_which_trades_are_in(model):
    """The redundancy control. After filtering, the flag must refuse nothing."""
    trades = [_trade(_UNDECIDABLE), _trade(_DECIDABLE), _trade(_SCHEDULE)]
    for rule in EP.CANDIDATE_RULES:
        kept, mix = EP.filter_records(rule, trades, "FTMO", model=model)
        spec = EP.spec_for(rule, OPTIONS["B_balanced"].with_(spread_band="mid"))
        if not kept:
            continue
        _, cov = price_trades(kept, spec)
        assert EP.decidability_refusals(cov["probe"].as_dict()) == 0, (
            f"{rule}: the filter kept a trade the model then refused — the filter and "
            f"`est.decidable` have diverged")
        assert mix["kept"] == len(kept)


def test_flagging_without_filtering_does_not_reproduce_the_population(model):
    """Stated as a test because the two are easy to confuse and the difference is a verdict.

    Same three trades, same band. SCHEDULE is no longer promoted by its degenerate band,
    so filtering gives a population of 1; flagging alone gives coverage 1/3, which `restrict_to_priced` narrows
    and `refuse` rejects outright.
    """
    trades = [_trade(_UNDECIDABLE), _trade(_DECIDABLE), _trade(_SCHEDULE)]
    filtered, _ = EP.filter_records("DECIDABLE", trades, "FTMO", model=model)
    assert len(filtered) == 1

    spec = OPTIONS["B_balanced"].with_(spread_band="mid", spread_require_decidable=True)
    _, cov = price_trades(trades, spec)          # unfiltered
    c = cov["probe"]
    assert c.n_total == 3 and c.n_priced == 1
    assert c.coverage_frac == pytest.approx(1 / 3)
    assert c.coverage_frac < spec.cost_coverage_floor, (
        "the shortfall is what makes this a DIFFERENT operation from filtering")
    assert OPTIONS["A_strict"].coverage_policy == "refuse"
    assert OPTIONS["B_balanced"].coverage_policy == "restrict_to_priced"


def test_unclassifiable_trades_are_kept_for_the_gate_to_refuse_and_stamp(model):
    """A trade with no era has no era quality — so this function must not judge it.

    Dropping it pre-gate would launder a coverage shortfall into a smaller population:
    `coverage_frac` would read 1.0, `restrict_to_priced` would have nothing to stamp, and
    `A_strict`'s refusal would never fire. The gate owns that accounting.
    """
    bad = TradeRecord(sleeve="probe", symbol="NOT_A_SYMBOL_AT_ALL",
                      entry_utc=_DECIDABLE, exit_utc=_DECIDABLE + dt.timedelta(hours=1),
                      direction=1, sl_distance_price=1.0, entry_price=100.0, r_gross=0.0)
    for rule in EP.CANDIDATE_RULES:
        kept, mix = EP.filter_records(rule, [bad, _trade(_DECIDABLE)], "FTMO", model=model)
        assert bad in kept, f"{rule} dropped an unclassifiable trade"
        assert mix["unpriceable"] == 1
    # ...and the gate does refuse it, so it is not silently free either.
    kept, _ = EP.filter_records("ALL_ERAS", [bad, _trade(_DECIDABLE)], "FTMO", model=model)
    _, cov = price_trades(kept, OPTIONS["B_balanced"].with_(spread_band="mid"))
    assert cov["probe"].n_unpriced == 1
    assert cov["probe"].coverage_frac == pytest.approx(0.5)


# ------------------------------------------------- the two fail-OPEN holes, closed (B1267)


def test_a_bad_band_token_raises_instead_of_disabling_the_filter(model):
    """The worst failure mode this module could have, and it had it.

    `classify` catches `Exception -> None` and `filter_records` KEEPS on None, so an
    unrecognised band made `estimate` raise on every trade, which read as "unclassifiable" and
    kept all of them — turning the strictest population into the unrestricted control, silently.
    Measured before the guard: `"MID"`, `"typo"`, `""` and `None` each took
    RECORDED_AND_DECIDABLE from 1-of-8 to 8-of-8 with `mix == {"kept": 0, "dropped": 0,
    "unpriceable": 8}`. Fail-open on a population rule is the one direction that must be
    impossible.
    """
    from src.costs.spread_model import SpreadModelError

    recs = [_trade(_UNDECIDABLE), _trade(_DECIDABLE), _trade(_SCHEDULE)]
    good, _ = EP.filter_records("RECORDED_AND_DECIDABLE", recs, "FTMO", model=model, band="mid")
    assert len(good) == 1, "the guarded path must still restrict"
    for bad in ("MID", "typo", "", None, "flat"):
        with pytest.raises(SpreadModelError, match="band must be one of"):
            EP.filter_records("RECORDED_AND_DECIDABLE", recs, "FTMO", model=model, band=bad)
        with pytest.raises(SpreadModelError, match="band must be one of"):
            EP.classify(recs[0], "FTMO", model=model, band=bad)


def test_a_population_that_classifies_nothing_raises(model):
    """Nothing kept AND nothing dropped is a broken call, not an empty population.

    The band guard above catches the known cause; this catches the unknown one — a wrong
    account, a model missing those symbols — where keep-on-None would again silently produce the
    unrestricted set under a restricted rule's name.
    """
    from src.costs.spread_model import SpreadModelError

    junk = [TradeRecord(sleeve="probe", symbol=f"NOT_A_SYMBOL_{i}", entry_utc=_DECIDABLE,
                        exit_utc=_DECIDABLE + dt.timedelta(hours=1), direction=1,
                        sl_distance_price=1.0, entry_price=100.0, r_gross=0.0)
            for i in range(3)]
    for rule in EP.CANDIDATE_RULES:
        with pytest.raises(SpreadModelError, match="classified NONE"):
            EP.filter_records(rule, junk, "FTMO", model=model)
    # ...but one unclassifiable trade among classifiable ones is still KEPT, not raised.
    kept, mix = EP.filter_records("ALL_ERAS", junk[:1] + [_trade(_DECIDABLE)], "FTMO",
                                  model=model)
    assert len(kept) == 2 and mix["unpriceable"] == 1


def test_apply_returns_the_filtered_records_and_the_sealed_spec(model):
    recs = {"probe": [_trade(_UNDECIDABLE), _trade(_DECIDABLE)]}
    out, spec, mix = EP.apply("RECORDED_AND_DECIDABLE", recs,
                              OPTIONS["B_balanced"].with_(spread_band="mid"), model=model)
    assert len(out["probe"]) == 1
    assert spec.spread_require_decidable is True
    assert spec.spec_id.endswith("|pop=RECORDED_AND_DECIDABLE")
    assert mix["kept"] == 1 and mix["dropped"] == 1


def test_a_sleeve_emptied_by_a_rule_disappears_rather_than_arriving_empty(model):
    recs = {"probe": [_trade(_UNDECIDABLE)]}
    out, _, mix = EP.apply("DECIDABLE", recs,
                           OPTIONS["B_balanced"].with_(spread_band="mid"), model=model)
    assert out == {}, "an empty sleeve list reaches the gate as a zero-trade sleeve"
    assert mix["dropped"] == 1
