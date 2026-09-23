"""The era-quality POPULATION rule — one named object, so nobody reimplements it again.

    recs, spec = era_population.apply("RECORDED", recs, spec, account="FTMO")

WHY THIS MODULE EXISTS
----------------------
The wave-8 agreement §4 and `AI_RECORDED_ERA_GATE_V1.json` restrict every admission-bearing
run to eras with ``era_class == "RECORDED"``, in order to keep the eras whose cost is known.
Session AL then measured what that choice is worth, and it is not a detail:

    mx_btcusd_d1_donchian_20_breakout @ target_5R, band mid, family 35, B_balanced
      ALL_ERAS        n 318   +0.547 R/day   p 0.0106   REJECT
      RECORDED        n 232   +0.982 R/day   p 0.0011   ADMIT     <- the standing rule
      DECIDABLE       n 240   +0.513 R/day   p 0.0581   REJECT    <- the model's OWN rule
      INTERSECTION    n 154   +0.892 R/day   p 0.0158   REJECT

**p ranges over 53x across this axis while the effect size ranges 1.9x.** The estate's first
and only ADMIT at the sealed alpha exists on exactly one of four defensible populations, and
the field that defines it was never chosen deliberately — it was inherited from a driver.

Three things follow, and this module is all three:

1. **The rule needs a name.** Four rules, spelled once, with the field each one reads and the
   argument for it. `RULES` below is that list and it is closed: a driver that wants a fifth
   adds it here, in front of a reader, rather than inline in a receipt script.
2. **The rule must reach the seal.** AL's three implementations were per-trade filters applied
   *before* `run_gate`, so two runs on two different populations produced the **same**
   `spec_sha256`. `apply()` stamps the rule name into `spec_id` — which `canonical()` hashes —
   so the population is part of the seal it was always supposed to be part of.
3. **The rule must be enforced by the model, not by the caller.** `SpreadModel.estimate` has
   taken ``require_decidable=`` since Session AG shipped it and no production path passed it;
   the switch that answers the question was sitting in the model, tested and unused. The
   decidable-family rules here set `GateSpec.spread_require_decidable=True` **as well as**
   filtering, deliberately.

THE REDUNDANCY IS THE CONTROL
-----------------------------
On DECIDABLE and INTERSECTION the filter and the flag say the same thing twice. That is not
belt-and-braces for its own sake: the filter reads `est.decidable` through
`SpreadModel.estimate`, and so does the flag, so if the two ever disagree — a stale filter, a
model rebuild, a band-dependence nobody expected — the trades the filter kept come back
**unpriced** and the sleeve's `coverage_frac` drops below 1.0. A silent divergence becomes a
visible number in the verdict. `decidability_refusals()` states that invariant — as a refusal
count and not as a coverage fraction, for a reason its own docstring gives — and
`test_era_population.py` pins it.

FILTERING AND FLAGGING ARE NOT THE SAME OPERATION, AND THE DIFFERENCE IS MEASURED
---------------------------------------------------------------------------------
Setting the flag alone, without filtering, does **not** reproduce the DECIDABLE population.
It produces a coverage shortfall, and what that costs depends on the option:

    B_balanced  coverage_policy="restrict_to_priced"  -> judged on the decidable subset,
                                                         stamped with what was dropped
    A_strict    coverage_policy="refuse"              -> NOT_EVALUABLE, because 24.5 % of
                                                         mx_btcusd's trades are undecidable
                                                         and the floor is 5 %

Both are the option behaving exactly as its docstring says. It means the flag on its own is a
*cost-honesty* statement ("this trade's price is not knowable") while the population rule is a
*population* statement ("this trade is not in the sample"), and only the second is what an
admission is claimed on. Hence: filter for the population, flag for the enforcement, both.

WHAT THIS MODULE DOES NOT DECIDE
--------------------------------
Which rule is right. That is Borhen's — a measurement-protocol call, priced in
`phase10/POPULATION_RULE_DECISION.md`. `DEFAULT_RULE` is deliberately **not** defined here;
a caller names its rule or gets a `KeyError`, because the whole defect this module repairs is
a population that arrived by default.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Sequence

from src.costs.spread_model import BANDS, SpreadModel, SpreadModelError, load_spread_model
from src.research_infra.walkforward.spec import GateSpec

__all__ = [
    "CANDIDATE_RULES",
    "RULES",
    "PopulationRule",
    "apply",
    "classify",
    "decidability_refusals",
    "filter_records",
    "spec_for",
]


@dataclass(frozen=True)
class PopulationRule:
    """One era-quality population, and why it is defensible.

    `keep` is evaluated on the model's own two published fields, never on anything that can
    see a return — which is what makes any of these restrictions legitimate rather than
    selection. `era_class` is assigned per calendar QUARTER and `decidable` is a property of
    that quarter's band width; neither can be computed from a trade's outcome.
    """

    name: str
    #: (era_class, decidable) -> in the population?
    keep: Callable[[str, bool], bool]
    #: Does this rule require the cost layer to REFUSE an undecidable era?
    require_decidable: bool
    why: str


#: The closed set. Order is the order they belong in a decision table: the control first, the
#: standing rule, the model's own rule, then the strictest.
RULES: dict[str, PopulationRule] = {
    "ALL_ERAS": PopulationRule(
        name="ALL_ERAS",
        keep=lambda cls, dec: True,
        require_decidable=False,
        why=("The control. Every era the model can price, including 20x-50x SCHEDULE "
             "backfills the model's own `honest_limit` warns are unvalidated. It is the only "
             "population that involves no choice, which is exactly why it belongs in the "
             "table: any other rule has to beat it on an argument, not on a p-value."),
    ),
    "RECORDED": PopulationRule(
        name="RECORDED",
        keep=lambda cls, dec: cls == "RECORDED",
        require_decidable=False,
        why=("The standing rule (wave-8 agreement §4). Keeps eras whose `era_ratio` came from "
             "an OBSERVED per-bar series rather than a broker backfill or a quantisation "
             "artefact. Selects on the DERIVATION of the ratio. Its weakness, measured: it "
             "retains 78 mx_btcusd trades in quarters the model itself calls UNDECIDABLE — "
             "one of them a 204,058x band — and drops 86 in quarters it calls decidable."),
    ),
    "DECIDABLE": PopulationRule(
        name="DECIDABLE",
        keep=lambda cls, dec: bool(dec),
        require_decidable=True,
        why=("The spread model's own rule: an observed/modelled era must have "
             "`hw <= 0.5`, and SCHEDULE is never decidable because a single backfilled "
             "constant makes every dispersion term identically zero. A narrow band caused "
             "by absence of observations is a capture requirement, not a result."),
    ),
    "RECORDED_AND_DECIDABLE": PopulationRule(
        name="RECORDED_AND_DECIDABLE",
        keep=lambda cls, dec: cls == "RECORDED" and bool(dec),
        require_decidable=True,
        why=("The strictest defensible population: observed derivation AND a band narrow "
             "enough to decide on. An admission that survives here does not depend on which "
             "era-quality field a reader prefers. It is CLOSE to `SpreadEstimate.coverage is "
             "Coverage.MEASURED` on a tick-anchored symbol and NOT equal to it — a first "
             "version of this note claimed equality and an adversarial pass refuted it. The "
             "coverage class additionally requires `era_gap_quarters == 0` (which this rule "
             "does not: 16 of the 232 RECORDED mx_btcusd trades in the estate's one admitting "
             "cell sit in a gap-extrapolated era, 6.9 %) and additionally admits "
             "`NO_BAR_HISTORY` and `REFERENCE` (which this rule does not: 23 tick-anchored "
             "fallback symbols and the reference instant). With both qualifiers the "
             "equivalence is exact — 0 mismatches over 8,748 probes — and without either it is "
             "false. Either way `GateSpec.require_measured_cost_frac` cannot express this "
             "era population: it reads the class of the TOTAL across four independent cost "
             "terms rather than the derivation of the spread era — and no code in src/ reads "
             "the field at all. Pinned by `test_era_population.py` and "
             "`test_spread_model.py`."),
    ),
    # Diagnostic, not a candidate rule: the population the standing rule KEEPS and the model's
    # own rule REJECTS. Its economics answer whether DECIDABLE's worse p is because these
    # trades were carrying the result or because dropping them broke the fold structure —
    # different findings, and only one of them is a problem with the claim. Measured on
    # mx_btcusd @ target_5R: +0.914 R/day on 78 trades, i.e. NOT free-riders.
    "RECORDED_UNDECIDABLE": PopulationRule(
        name="RECORDED_UNDECIDABLE",
        keep=lambda cls, dec: cls == "RECORDED" and not dec,
        require_decidable=False,
        why=("DIAGNOSTIC ONLY — the 78 disputed trades themselves, never a candidate rule. "
             "Do not read a verdict here as an admission of anything: it is the difference "
             "between two rules, isolated so it can be priced."),
    ),
}

CANDIDATE_RULES: tuple[str, ...] = ("ALL_ERAS", "RECORDED", "DECIDABLE",
                                   "RECORDED_AND_DECIDABLE")


def classify(rec: Any, account: str, *, model: SpreadModel | None = None,
             band: str = "mid") -> tuple[str, bool] | None:
    """`(era_class, decidable)` for one trade, or None when the model cannot price it.

    `band` is accepted and is **immaterial to the answer**, which is worth stating rather
    than leaving to be rediscovered: `era_class` and `decidable` are read off the era record
    and the extrapolation gap, and neither is a function of the band — only `era_ratio_{band}`
    is. `test_era_population.py::test_the_population_is_band_independent` pins it over every
    era in the model, so a caller may compute the population once and reuse it across all
    three bands.
    """
    if band not in BANDS:
        # FAIL LOUDLY ON A BAD BAND, because failing quietly here fails OPEN on a population
        # rule. Found by a completeness critic over this session's own claims (B1267). The
        # `except Exception -> None` below plus `filter_records`' keep-on-None means an
        # unrecognised band token made `estimate` raise on EVERY trade, which read as "the model
        # cannot classify any of them", which kept all of them -- so the STRICTEST population
        # silently became the control. Measured before the guard: `band="MID"` (wrong case),
        # `"typo"`, `""` and `None` each turned RECORDED_AND_DECIDABLE from 1-of-8 into 8-of-8
        # with `mix == {"kept": 0, "dropped": 0, "unpriceable": 8}`. A mix with zero kept and
        # zero dropped is not a population; it is a broken call.
        raise SpreadModelError(
            f"band must be one of {BANDS}, got {band!r}. A bad band token would make every "
            f"estimate raise, which this module would read as 'unclassifiable' and KEEP -- "
            f"turning the strictest population into the unrestricted control silently."
        )
    sm = model or load_spread_model()
    try:
        est = sm.estimate(rec.symbol, account, rec.entry_utc, band=band)
    except Exception:       # noqa: BLE001 — an unpriceable trade is not in any population
        return None
    return est.era_class, bool(est.decidable)


def filter_records(rule: str, records: dict[str, Sequence[Any]] | Iterable[Any],
                   account: str, *, model: SpreadModel | None = None,
                   band: str = "mid") -> tuple[Any, dict[str, int]]:
    """Apply one rule to `{sleeve: [TradeRecord]}` (or a flat iterable).

    Returns the restricted structure and a mix counter.

    **A trade the model cannot classify at all is KEPT, not dropped**, and that is the
    opposite of what the first version of this function did. It has no era, so the rule cannot
    speak about it — but dropping it pre-gate would launder a coverage shortfall into a
    smaller population: `coverage_frac` would read 1.0, `restrict_to_priced` would have nothing
    to stamp, and `A_strict`'s refusal would never fire on a sleeve whose symbols broker truth
    cannot price. The gate already has a correct, stamped mechanism for those trades; this
    function must not pre-empt it. They are counted as `unpriceable` so the number is visible
    either way.

    Measured consequence for the cells this was built for: **zero** — `mx_btcusd @ target_5R`,
    `sub_xvol_pullback @ target_4R` and `sub_mid_dn_revert` re-clocked have 0 unclassifiable
    trades each, so the four populations reproduce AL's published 318 / 232 / 240 / 154 (and
    88 / 85 / 56 / 53) exactly under either choice. The choice is made on the principle
    because the measurement could not make it.
    """
    if rule not in RULES:
        raise KeyError(f"unknown population rule {rule!r}; have {sorted(RULES)}")
    r = RULES[rule]
    sm = model or load_spread_model()
    mix = {"kept": 0, "dropped": 0, "unpriceable": 0}

    def _keep(rec: Any) -> bool:
        got = classify(rec, account, model=sm, band=band)
        if got is None:
            mix["unpriceable"] += 1
            return True         # the gate refuses it and stamps it; see the docstring
        ok = bool(r.keep(*got))
        mix["kept" if ok else "dropped"] += 1
        return ok

    if isinstance(records, dict):
        out = {s: [x for x in rs if _keep(x)] for s, rs in records.items()}
        result: Any = {s: rs for s, rs in out.items() if rs}
    else:
        result = [x for x in records if _keep(x)]
    # A mix with nothing kept AND nothing dropped is not a population -- it is a call in which
    # the model classified nothing, and under keep-on-None that produces the UNRESTRICTED set
    # under a restricted rule's name. The band guard in `classify` catches the known cause; this
    # catches the unknown one. Second half of B1267.
    if mix["kept"] == 0 and mix["dropped"] == 0 and mix["unpriceable"] > 0:
        raise SpreadModelError(
            f"population rule {rule!r} classified NONE of {mix['unpriceable']} trades, so the "
            f"restriction would silently keep all of them. This is a broken call (wrong "
            f"account? model without these symbols?), not an empty population."
        )
    return result, mix


def spec_for(rule: str, spec: GateSpec) -> GateSpec:
    """The same spec, carrying this rule in its SEAL.

    Two changes, and both are load-bearing:

    * `spec_id` gains ``|pop=<RULE>``. `canonical()` hashes `spec_id`, so two runs on two
      populations can no longer produce the same `spec_sha256` — which they could, and did,
      for the whole of wave 9.
    * `spread_require_decidable` is set for the rules that need the cost layer to refuse.
      Under `restrict_to_priced` this is redundant with the filter and acts as a control;
      under `refuse` it is what makes the option's own strictness apply to the population's
      own defect instead of only to missing tick files.
    """
    if rule not in RULES:
        raise KeyError(f"unknown population rule {rule!r}; have {sorted(RULES)}")
    r = RULES[rule]
    return spec.with_(
        spec_id=f"{spec.spec_id}|pop={r.name}",
        spread_require_decidable=(True if r.require_decidable else None),
    )


def apply(rule: str, records: dict[str, Sequence[Any]], spec: GateSpec, *,
          account: str | None = None, model: SpreadModel | None = None,
          band: str = "mid") -> tuple[dict[str, Sequence[Any]], GateSpec, dict[str, int]]:
    """`filter_records` + `spec_for`, which is the pair a caller always wants.

    `account` defaults to the spec's own, because a population computed on one account's era
    table and gated on another's costs is a defect with no symptom.
    """
    recs, mix = filter_records(rule, records, account or spec.account, model=model, band=band)
    return recs, spec_for(rule, spec), mix


def decidability_refusals(coverage: dict) -> int:
    """How many trades the COST LAYER refused for undecidability, from a verdict's coverage.

    This is the redundancy control, and it is stated as a reason count rather than as a
    coverage fraction because a coverage fraction cannot carry the claim. `coverage_frac` can
    sit below 1.0 after a correctly-applied rule for reasons that have nothing to do with era
    quality — `panel.price_trades` marks a trade unpriced for an `implausible_stop` before
    `cost_r` is even called, and a symbol can be missing from the broker-truth artifact. An
    earlier version of this module asserted `coverage_frac == 1.0` here and would have fired on
    those; the honest invariant is narrower and sharper:

        **after `apply(rule, ...)` this must be 0 for every rule.**

    Non-zero means the filter and the model disagree about which eras are decidable — the
    filter kept a trade `spread_price(..., require_decidable=True)` then refused — which is a
    real defect and the only thing this control exists to catch. Pass
    `verdict.coverage` (i.e. `SleeveCoverage.as_dict()`).
    """
    reasons = (coverage or {}).get("unpriced_reasons") or {}
    return sum(n for text, n in reasons.items() if "not decidable" in str(text))
