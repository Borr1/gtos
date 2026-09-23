"""``spread_model_v1`` -- the quoted spread at any instant, for any symbol, as a BAND.

    spread_price(symbol, account, at_utc, band="mid") -> SpreadEstimate

What it is for
--------------
Two problems, one model.

**1. The look-ahead.** Every deep-history number this estate has produced charges the
37-day tick snapshot (2026-06-18..07-24) to as much as 26 years of bars. On a family
where cost runs 33-219% of gross R that is the largest disclosed bias in the programme
(`SESSION_W_WALKFORWARD_GATE_RESULT.md` §4 defect 4). It was disclosed and never sized.
It is now sized, and the size is not small:

    EURUSD 2000-2003   spread was  50x today's   [41.7, 60.0]
    USDJPY 2000-2003               20x           [16.0, 25.6]
    XAUUSD 2020-2024              0.18x          [0.15, 0.21]

**and the direction is not the one the disclosure assumed.** "Spreads compressed, so
every published historical result is optimistic" is true of FX and inverted for metals,
indices and energy, where today is the most expensive point in the recorded archive. A
2018-2024 metals result charged the 2026 snapshot was **over**charged, not under. Three
of the four armed sleeves trade metals, energy and crypto.

**2. The refusal.** `cost_r` hard-raises for any symbol with no measured spread
(`model.py:349-352`), which makes the sleeve unjudgeable rather than uncertain -- that is
what put `crypto`, a sleeve trading real money right now, at NOT_EVALUABLE. Thirteen more
symbols become priceable here because the bar archive records their spread even though the
tick archive never covered them: `CADJPY`, `DASHUSD`, `NATGAS_cash`, `XPTUSD`, `XPDUSD`,
`XCUUSD` and the rest. **A band is always better than a refusal.**

How it works
------------
Three multiplied terms, each measured:

    spread(sym, t) = anchor(sym) x era_ratio(sym, quarter(t)) x intraweek(class, hour, vol)

* **anchor** -- tick-measured p50 quoted spread over the reference window. MEASURED for
  37 symbols; for the other 13 it is the bar-recorded level times the class `tick/bar`
  factor (measured 1.00x-1.73x over the 22 symbols that have both), and is MODELLED.
* **era_ratio** -- from the MT5 bar ``spread`` column, which records a spread per bar back
  to 2000. Used for **ratios only, never levels**, so any constant bar-vs-tick bias
  divides out. H4, because the block holdout measured H4 skill 0.334 against D1's 0.007.
* **intraweek** -- hour-of-week and volatility-state multipliers from the 263.9M-tick
  archive, pooled per instrument class.

The band
--------
`low`/`mid`/`high` come from a per-era half-width in log space, every term measured:
cross-instrument dispersion (9 estimator variants), split-half sampling noise, D1-vs-H4
disagreement, floored per era-quality class at the measured median quarter-to-quarter move
of RECORDED eras. An era whose half-width exceeds the decidability threshold is published
as ``capture_required`` rather than as a band -- **a band too wide to decide anything is a
capture requirement, not a result** (9.3% of FTMO eras).

**Undecidability now costs something, which until 2026-07-30 it did not.** Two switches, and
they answer different questions:

* ``decidable=False`` **degrades ``coverage`` to MODELLED on every path** (Session AN, B1250).
  Before that repair it degraded only through the no-bar-history fallback, so 182 undecidable
  ``RECORDED`` eras -- including one whose own ``capture_requirement`` reads *"band spans
  204058.1x"* -- returned ``coverage=MEASURED`` and every ``restrict_to_priced`` consumer
  took them as priced.
* ``require_decidable=True`` **raises** instead, which is what a caller wants when an
  undecidable era should remove the trade from the population rather than merely stamp it.
  It is reachable from a gate run as ``GateSpec.spread_require_decidable``.
* A ``SCHEDULE`` era is unconditionally undecidable. Its backfilled constant has no
  within-era observations; the resulting zero dispersion is missing information, not
  a zero-width confidence band. This class veto closes the Wave-21 inversion in which
  all 867 SCHEDULE cells were promoted by their degeneracy.

A consequence worth knowing, and **stated with two qualifiers that a first version of this
paragraph left out** (found by an adversarial pass over this session's own claim). After the
repair, this estimate's ``coverage is Coverage.MEASURED`` holds exactly when

    anchor is tick-MEASURED  AND  era_gap_quarters == 0
    AND  era_class in ("RECORDED", "NO_BAR_HISTORY", "REFERENCE")  AND  decidable

-- 0 mismatches over an exhaustive 8,748-probe cross-product of every symbol against every era
key its account carries, plus the reference instant. Dropping either qualifier makes it FALSE,
and not marginally: without ``gap == 0`` it fails on 105 probes, because ``if gap`` below forces
MODELLED unconditionally while ``decidable`` is only overridden past ``MAX_ERA_GAP_QUARTERS``;
without the wider class set it fails on 63 REFERENCE and 23 ``NO_BAR_HISTORY`` probes, which are
MEASURED and are not RECORDED. **It matters on real samples, not only at the edges: 16 of the
232 RECORDED ``mx_btcusd`` trades in the estate's one admitting cell sit in a gap-extrapolated
era**, so "MEASURED == RECORDED and decidable" would misdescribe 6.9 % of them.

So the coverage class of *this* term is a near-miss for the strictest era population rather than
identical to it -- see `walkforward/era_population.py`. And it does not follow that a total-cost
coverage floor could express either: ``cost_r``'s ``total_r`` travels with the weakest of four
terms, while ``GateSpec.require_measured_cost_frac`` is declared and read by **no code at all**.
Wave 21 made BTCUSD slippage MEASURED from exact-account reconciled fills, so stale claims
that this term is always TRANSFERRED no longer hold.

The composition -- repaired 2026-07-30 by Session AH (was ``v1_multiplicative``)
--------------------------------------------------------------------------------
Each of the three terms above was validated ALONE. Session AF then found that their
PRODUCT is its own risk: on pre-2010 FX ``era_ratio x hour_of_week`` reaches 198x-880x the
modern base and charges up to 178 % of the risk unit as spread, which is not a market. The
hour term is a spike at the daily rollover (11x-23x on the fx class, 1.0x-1.4x everywhere
else) and multiplying it by a 14x-50x era ratio assumes the rollover PREMIUM scales
proportionally with the era's spread level.

Measured, on the three axes that carry level-vs-hour variation and restricted to the cells
where a rollover premium exists at all (`AH_COMPOSITION_TESTS.json`,
`SPREAD_MODEL_V2_VALIDATION.json`):

    log(hour-h level) = a + b x log(calm-hours level)

    fx cross-section (leave-one-symbol-out)   b = 0.310 +- 0.139   b=1 REJECTED at 5.0 sigma
    jpy_fx cross-section                      b = 0.721 +- 0.194   1.4 sigma
    era axis, M15 bar minima 2024Q1-2026Q3    b = 0.669 +- 0.219   1.5 sigma  (SYMBOL-CLUSTERED
                                                                    SE: 152 quarterly points
                                                                    from 14 symbols over 11
                                                                    shared quarters are not
                                                                    152 observations. The
                                                                    i.i.d. SE of 0.128 would
                                                                    read 2.6 sigma and is
                                                                    wrong; a symbol block
                                                                    bootstrap puts b=1 inside
                                                                    the 95 % CI.)
    cross-broker, same instrument/instant     b = 0.825 +- 0.935   (unidentified; the
                                                                    robust median pairwise
                                                                    slope is 0.103)

    -> b = 0.4947 +- 0.1003, envelope [0.310, 0.721]

**Where v1 is and is not refuted, stated precisely, because an adversarial pass over the first
version of this docstring found it overstated.** ``b = 1`` is rejected at 5.0 sigma on the fx
cross-section -- robustly: 4.98 i.i.d., 5.79 clustered by instrument, 3.8-5.6 under
leave-one-instrument-out. It is **NOT** rejected on the era axis, which is the axis this model
extrapolates along: 1.5 sigma clustered by symbol, and six of the fourteen per-symbol era slopes
are themselves >= 1. So the honest justification is narrower than "v1 is refuted where either
can be tested": v1 is refuted **on the class that pays the premium**, where its leave-one-out
prediction error is also 2.2x the damped form's (0.608 against 0.288 at hour 0), and the era axis
neither confirms nor refutes it. The functional form is not uniquely selected either -- MAX_PEAK
and ADD_PRICE score within 0.05 of DAMPED_B on that class. What the evidence supports is
"damped, by roughly half an exponent"; it does not single out this algebra.

``b = 1`` is v1 exactly. ``b < 1`` means the premium is damped as the level widens, so

    spread(sym, era, h) = anchor x era_ratio ** b x hour_mult(h)

which is identical to v1 in the reference window -- where the hour term was measured and is
therefore right -- and decays away from it at a measured rate. The multiplier is clamped at
>= 1.0: a rollover hour is never TIGHTER than its own era's calm level, and only the
premium is damped (an hour whose multiplier is already <= 1 is left alone).

Pass ``composition="v1_multiplicative"`` to reproduce any pre-2026-07-30 banded number, and
``era_exponent=`` to walk the envelope.

The honest limit, which is not to be softened
---------------------------------------------
**Bands narrow the look-ahead; they do not eliminate it. Only capture does.** The era
instrument is validated at ratios of 0.78-1.30 (188 held-out weekly block pairs) and at one
7-month out-of-sample point (XAUUSD, -0.45%). *Nothing validates it at the 20x-50x the
pre-2010 FX eras imply.* Those eras are class ``SCHEDULE`` -- a backfilled constant, the
broker's own statement about the era rather than a per-bar observation -- and they carry the
widest bands for exactly that reason. Forward tick capture is what tightens them.

**And the same limit applies to the exponent.** ``b`` is measured over level ranges of
2x-25x; the pre-2010 FX eras ask for 50x. It is an extrapolation, and the honest reason to
prefer it over v1 is not that it is validated there but that v1 is REFUTED where either can
be tested, on the axis the model extrapolates along. Session AH's fitted ``b`` is the
conservative half of that: the era axis alone would give 0.669, the affected class alone
0.310, and the point estimate sits between.

**One measured bias is NOT repaired here, and it compounds with the composition.** The
MT5 bar ``spread`` column is the MINIMUM spread within the bar -- measured at a 0.999 median
exact-match rate over 30 symbols against tick truth (`AH_BAR_SPREAD_SEMANTICS.json`) -- so
``era_ratio`` is a ratio of minima while the anchor is a tick p50. Where an era's recorded
series is a constant (class ``SCHEDULE``) its min IS its median, so the ratio is inflated by
the reference window's own min-to-median factor, which AG measured at 1.00x-1.73x. See
`SPREAD_MODEL_V2_VALIDATION.json` -> ``min_to_p50_era_ratio_bias``.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from src.costs.artifact_authority import (
    CostInputAuthorityError,
    read_current_file_bytes,
)
from src.costs.coverage import Coverage, weakest
from src.costs.symbols import resolve_account_symbol
from src.utils.broker_clock import resolve_rule, utc_to_broker_naive

__all__ = [
    "SpreadModel",
    "SpreadEstimate",
    "load_spread_model",
    "spread_price",
    "BANDS",
    "COMPOSITIONS",
    "DEFAULT_COMPOSITION",
    "ERA_HOUR_EXPONENT",
    "ERA_HOUR_EXPONENT_ENVELOPE",
    "DEFAULT_MODEL",
    "SpreadModelError",
]

REPO = Path(__file__).resolve().parents[2]
DEFAULT_MODEL = REPO / "research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json"

BANDS = ("low", "mid", "high")

COMPOSITIONS = ("v2_damped", "v1_multiplicative")
DEFAULT_COMPOSITION = "v2_damped"

#: The measured exponent on ``era_ratio`` in the hour-elevated component -- see the module
#: docstring and `SPREAD_MODEL_V2_VALIDATION.json`. Inverse-variance weighted mean over the
#: axes that identify it; 1.0 would be v1's unvalidated product.
ERA_HOUR_EXPONENT = 0.4947
ERA_HOUR_EXPONENT_ENVELOPE = (0.310, 0.721)

#: The exponent applies only to a PREMIUM, and only above the same threshold the fit itself
#: required a cell to clear to be included (`ah_spread_compose.MIN_EFFECT_MULT`). Below it
#: the hour multiplier is not a rollover spike, it is ordinary session structure, and the
#: exponent says nothing about it.
#:
#: ADDED AFTER TWO OF SESSION AG's TESTS WENT RED, and they were right. The first draft
#: guarded only on `mult_ref <= 1`, which let a 1.14x metals session multiplier be rescaled
#: by a parameter measured on a 10x-35x FX rollover -- and because XAUUSD's 2022 era ratio is
#: 0.178x, the rescaling went UPWARD, turning a repair that is supposed to shrink an
#: overcharge into a 2.3x increase on the one class AG had just shown was already
#: over-costed. `test_era_costing_changes_a_verdict_sized_amount` failed at 2.1x against its
#: own 3x floor. The defect AF filed is the FX rollover product; the repair is now exactly
#: that wide and no wider.
PREMIUM_FLOOR = 1.5

# How far the nearest-era fallback may reach before the answer stops being decidable.
# 8 quarters: two years is the outer edge of what the measured quarter-to-quarter drift
# (0.0911 log median) can plausibly span without the estimate becoming a guess.
MAX_ERA_GAP_QUARTERS = 8

# The quarter the tick archive was measured in. A symbol with no bar history is decidable
# only here, because this is the only instant its spread was actually observed.
_REFERENCE_INSTANT = datetime(2026, 7, 1, 12, tzinfo=timezone.utc)

# Broker server per account, for the wall-clock conversion. Hour-of-week is defined on
# the broker's own wall clock because that is what the session structure keys on, and it
# is NOT UTC -- FTMO-Server3 is America/New_York + 7h, which switches on US DST dates.
_SERVER = {"FTMO": "FTMO-Server3", "redacted_account": "redacted_account-Server 2"}


class SpreadModelError(RuntimeError):
    """Raised rather than guessing, in the same posture as `CostTruthError`."""


@dataclass(frozen=True)
class SpreadEstimate:
    """One spread in price units, with everything needed to defend it."""

    symbol: str
    account: str
    band: str
    spread_price: float
    coverage: Coverage
    era: str
    era_ratio: float
    era_class: str
    intraweek_mult: float
    anchor_price: float
    decidable: bool
    provenance: str
    detail: dict
    composition: str = DEFAULT_COMPOSITION

    def as_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "account": self.account,
            "band": self.band,
            "spread_price": self.spread_price,
            "coverage": self.coverage.value,
            "era": self.era,
            "era_ratio": self.era_ratio,
            "era_class": self.era_class,
            "intraweek_mult": self.intraweek_mult,
            "anchor_price": self.anchor_price,
            "decidable": self.decidable,
            "provenance": self.provenance,
            "composition": self.composition,
            "detail": self.detail,
        }


def damped_intraweek_mult(mult_ref: float, era_ratio: float, exponent: float) -> float:
    """The hour multiplier an era actually pays, under the measured composition.

    ``mult_ref`` is the reference window's multiplier for this hour (v1's whole hour term).
    The regression ``log h_level = a + b log base``, calibrated so the reference window is
    reproduced exactly, gives ``mult(era) = mult_ref x era_ratio ** (b - 1)``.

    Two guards, both load-bearing rather than defensive:

    * **An hour without a material premium is left alone** -- ``mult_ref < PREMIUM_FLOOR``.
      The exponent was fitted only on cells clearing that same threshold, so below it there
      is nothing it can honestly say. See `PREMIUM_FLOOR` for what went wrong without this.
    * **The result is clamped at 1.0.** A wide enough era would otherwise be charged a
      rollover spread TIGHTER than its own calm level, which no book ever quoted.
    """
    if mult_ref < PREMIUM_FLOOR or era_ratio <= 0.0:
        return mult_ref
    return max(1.0, mult_ref * (era_ratio ** (exponent - 1.0)))


class SpreadModel:
    """Loaded ``SPREAD_MODEL_V1.json``."""

    def __init__(
        self,
        doc: dict,
        source: Path | None = None,
        *,
        artifact_sha256: str | None = None,
    ):
        self.doc = doc
        self.source = source
        self.artifact_sha256 = artifact_sha256
        self.version = doc.get("version")
        self.schema = doc.get("schema")
        self.honest_limit = doc.get("honest_limit", "")

    # -- lookup ---------------------------------------------------------------

    def _account(self, account: str) -> dict:
        acc = self.doc.get("accounts", {}).get(account)
        if acc is None:
            raise SpreadModelError(
                f"no spread model for account {account!r}; have "
                f"{sorted(self.doc.get('accounts', {}))}"
            )
        return acc

    def record(self, symbol: str, account: str) -> dict:
        """Symbol record through the account profiles' declared equivalences.

        The tick archive writes `US100_cash`, the bar archive keys on the canonical GTOS
        name, and the broker quotes `US100.cash`. All three reach the same instrument.
        """
        acc = self._account(account)
        resolved = resolve_account_symbol(account, symbol, acc)
        if resolved is not None:
            return acc[resolved]
        raise SpreadModelError(
            f"{symbol!r} is not in the spread model for {account} "
            f"({len(acc)} symbols). It has neither a tick file nor a bar file, so its "
            "spread is unmeasured and unmodelled -- not zero."
        )

    def symbols(self, account: str) -> list[str]:
        return sorted(self._account(account))

    # -- the model ------------------------------------------------------------

    def era_key(self, at_utc: datetime, account: str) -> str:
        """Quarter label on the BROKER's wall clock, not UTC.

        A trade at 2019-12-31 22:30 UTC is 2020-01-01 01:30 on an FTMO server, i.e. a
        different quarter. The bar archive is stamped in broker wall clock, so the era
        table must be read the same way or the boundary quarters silently mismatch.
        """
        wall = utc_to_broker_naive(_as_utc(at_utc), resolve_rule(_SERVER.get(account, account)))
        return f"{wall.year}Q{(wall.month - 1) // 3 + 1}"

    def _nearest_era(self, eras: dict, want: str) -> tuple[str, int]:
        """The requested quarter, or the closest one that exists, and how far away it is.

        The distance matters and an earlier version threw it away. `NATGAS_cash` has bars
        from 2024Q4; asked for 2010Q2 it answers with 2024Q4 and, if the caller only sees a
        boolean "extrapolated", a **57-quarter** extrapolation is indistinguishable from a
        one-quarter gap. Returns the gap in quarters so the caller can refuse on it.
        """
        if want in eras:
            return want, 0
        if not eras:
            raise SpreadModelError("this symbol has no priced era at all")
        wy, wq = int(want[:4]), int(want[-1])
        dist = lambda k: abs((int(k[:4]) - wy) * 4 + int(k[-1]) - wq)
        best = min(sorted(eras), key=dist)
        return best, dist(best)

    def intraweek_mult(self, account: str, klass: str | None, at_utc: datetime,
                       vol_state: int | None = None, vol_kind: str = "trailing") -> tuple[float, dict]:
        """Hour-of-week x volatility-state multiplier on the era median."""
        shape = (self.doc.get("intraweek") or {}).get(account) or {}
        wall = utc_to_broker_naive(_as_utc(at_utc), resolve_rule(_SERVER.get(account, account)))
        how = str(wall.weekday() * 24 + wall.hour)
        h = ((shape.get("by_class_hour_of_week") or {}).get(klass) or {}).get(how)
        v = None
        if vol_state is not None:
            v = ((shape.get("by_class_vol_state") or {}).get(f"{klass}|{vol_kind}")
                 or {}).get(str(int(vol_state)))
        mult = float(h or 1.0) * float(v or 1.0)
        return mult, {"hour_of_week_brokerwall": int(how), "hour_mult": h,
                      "vol_state": vol_state, "vol_kind": vol_kind, "vol_mult": v}

    def estimate(self, symbol: str, account: str, at_utc: datetime | None = None, *,
                 band: str = "mid", vol_state: int | None = None,
                 vol_kind: str = "trailing",
                 composition: str = DEFAULT_COMPOSITION,
                 era_exponent: float | None = None,
                 require_decidable: bool = False) -> SpreadEstimate:
        if band not in BANDS:
            raise SpreadModelError(f"band must be one of {BANDS}, got {band!r}")
        if composition not in COMPOSITIONS:
            raise SpreadModelError(
                f"composition must be one of {COMPOSITIONS}, got {composition!r}")
        rec = self.record(symbol, account)
        anchor = float(rec["anchor_spread_price"])
        anchor_cov = Coverage(rec["anchor_coverage"])
        klass = rec.get("instrument_class")

        # A MODELLED anchor is a bar level; the class tick/bar factor converts it to the
        # tick-median quantity `cost_r` charges. Measured, never assumed: 1.00x-1.73x.
        tob_applied = None
        if anchor_cov is not Coverage.MEASURED:
            tob = (self.doc.get("tick_over_bar_factor") or {}).get(account) or {}
            f = (tob.get("by_class_median") or {}).get(klass) or tob.get("global_median")
            if f:
                anchor *= float(f)
                tob_applied = float(f)

        want = None
        fb = rec.get("era_fallback")
        if at_utc is None:
            era_key, ratio, era_class = "reference", 1.0, "REFERENCE"
            gap, decidable = 0, True
        elif fb is not None:
            # Tick-measured today, no bar file at all (EU50.cash, SPN35.cash, AUS200.cash).
            # Today's spread is known precisely; its history is not known at all. Charging
            # the reference level with the class-wide era spread as the band is strictly
            # better than refusing -- and refusing here would make `spread_band=` WORSE
            # than no band, since the flat snapshot prices these symbols happily.
            want = self.era_key(at_utc, account)
            era_key, era_class, gap = want, "NO_BAR_HISTORY", 0
            hw = float(fb["band_halfwidth_log"])
            ratio = {"low": math.exp(-hw), "mid": 1.0, "high": math.exp(hw)}[band]
            decidable = want == self.era_key(_REFERENCE_INSTANT, account)
        else:
            want = self.era_key(at_utc, account)
            era_key, gap = self._nearest_era(rec["eras"], want)
            e = rec["eras"][era_key]
            ratio = float(e[f"era_ratio_{band}"] if band != "mid" else e["era_ratio_mid"])
            era_class = e["class"]
            artifact_decidable = bool(e.get("decidable", True))
            # A SCHEDULE row is a backfilled constant, not an observed within-era
            # distribution.  Its zero dispersion made the generated band degenerate and
            # therefore marked every one of 867 SCHEDULE cells `decidable=true`: absence
            # of variation was inverted into strongest certainty.  Width can veto an
            # observed/modelled era, but it cannot promote this evidence class.
            decidable = artifact_decidable and era_class != "SCHEDULE"
            # A quarter borrowed from four years away is not that quarter's spread. The
            # era's own decidability says nothing about a gap this large, so it cannot be
            # inherited across one.
            if gap > MAX_ERA_GAP_QUARTERS:
                decidable = False

        mult_ref, mdetail = self.intraweek_mult(account, klass, at_utc, vol_state, vol_kind) \
            if at_utc is not None else (1.0, {})
        exponent = ERA_HOUR_EXPONENT if era_exponent is None else float(era_exponent)
        mult = (mult_ref if composition == "v1_multiplicative"
                else damped_intraweek_mult(mult_ref, ratio, exponent))
        mdetail = {**mdetail, "hour_mult_reference": mult_ref,
                   "hour_mult_effective": mult, "era_hour_exponent":
                       (None if composition == "v1_multiplicative" else exponent)}

        if require_decidable and not decidable:
            raise SpreadModelError(
                f"{symbol} {era_key} is not decidable"
                + (f": {fb['capture_requirement']}" if fb is not None else
                   f": the requested quarter {want} is {gap} quarters outside this "
                   "symbol's recorded range" if gap > MAX_ERA_GAP_QUARTERS else
                   ": the band spans more than the threshold, so it is a capture "
                   "requirement rather than a spread. "
                   + str(rec["eras"].get(era_key, {}).get("capture_requirement", "")))
            )

        # Coverage travels with the WEAKEST input, exactly as `cost_r` does it. Using
        # `weakest` rather than a hand-rolled min: `Coverage.strength` is 0 for MEASURED
        # and 2 for MODELLED, so `min(..., key=strength)` returns the STRONGEST -- which is
        # what an earlier revision here did, and it reported a QUANTIZED era on a
        # tick-anchored symbol as MEASURED.
        cov = anchor_cov
        if at_utc is not None and era_class not in ("RECORDED", "NO_BAR_HISTORY"):
            cov = weakest(cov, Coverage.MODELLED if era_class in ("SCHEDULE", "FLOORED")
                          else Coverage.TRANSFERRED)
        # UNDECIDABLE DEGRADES ON EVERY PATH, not only through `fb` -- repaired 2026-07-30 by
        # Session AN (B1250), and the defect it closes was measurable rather than theoretical.
        #
        # The previous form was `if fb is not None and ... not decidable: MODELLED` **elif**
        # `era_class not in ("RECORDED", "NO_BAR_HISTORY")`, so the `not decidable` branch was
        # reachable ONLY through the tick-measured-no-bar-history fallback. On the ordinary era
        # path an UNDECIDABLE **RECORDED** era matched neither branch and kept the anchor's own
        # coverage: `BTCUSD 2020Q1` returned `coverage=MEASURED` on a band whose own
        # `capture_requirement` field reads *"band spans 204058.1x, wider than any verdict can
        # survive"*, and every `coverage_policy="restrict_to_priced"` consumer accepted it as
        # priced (Session AL §3.3).
        #
        # It is not one quarter. **182 of the model's 275 undecidable eras are `RECORDED`**
        # (66.2 %: FTMO 134 of 195, redacted_account 48 of 80) and none of them degraded anything.
        # Counted exactly, over all 2,653 era cells, this branch fires on all 275 and **192
        # of them change coverage CLASS** (7.2 % of the model):
        #
        #     RECORDED,  MEASURED anchor      166   MEASURED    -> MODELLED
        #     QUANTIZED, MEASURED anchor       26   TRANSFERRED -> MODELLED
        #     RECORDED/QUANTIZED, MODELLED anchor   19   already MODELLED, no change
        #     FLOORED                          64   already MODELLED via the class branch
        #
        # The gap between 275 and 192 is the reason to count rather than to assert: 19 of the
        # newly-degraded eras belong to symbols whose ANCHOR is already MODELLED, so the honest
        # figure for "cells this repair moves" is 192 and not 211.
        #
        # The repair can only ever move coverage WEAKER -- `weakest()` is monotone, which is
        # what `test_undecidable_never_strengthens_coverage` pins over every era in the model.
        #
        # The `fb` case is subsumed rather than dropped: there `era_class` is "NO_BAR_HISTORY",
        # so the class branch above never fires and an undecidable fallback still lands on
        # MODELLED exactly as it did before.
        if at_utc is not None and not decidable:
            cov = weakest(cov, Coverage.MODELLED)
        if gap:
            cov = Coverage.MODELLED

        value = anchor * ratio * mult
        return SpreadEstimate(
            symbol=symbol, account=account, band=band, spread_price=value, coverage=cov,
            era=era_key, era_ratio=ratio, era_class=era_class, intraweek_mult=mult,
            anchor_price=anchor, decidable=decidable, composition=composition,
            provenance=(
                f"spread_model[{composition}]: anchor {anchor:.6g} [{anchor_cov.value}] "
                f"x era {era_key} {band}={ratio:.4g} [{era_class}] x intraweek {mult:.4g}"
                + (f" (reference {mult_ref:.4g} damped by era_ratio**({exponent:.4g}-1); "
                   f"AH composition repair)" if composition != "v1_multiplicative"
                   and mult != mult_ref else "")
                + (f"; anchor scaled by class tick/bar factor {tob_applied:.4g}"
                   if tob_applied else "")
                + (f"; ERA EXTRAPOLATED {gap} quarter(s): the requested quarter is outside "
                   "this symbol's recorded range" if gap else "")
            ),
            detail={"anchor_coverage": anchor_cov.value, "tick_over_bar_factor": tob_applied,
                    "era_extrapolated": bool(gap), "era_gap_quarters": gap,
                    "artifact_decidable": (artifact_decidable if at_utc is not None
                                             and fb is None else decidable),
                    "decidability_basis": (
                        "SCHEDULE is never decidable: zero within-era dispersion is "
                        "absence of observations, not a zero-width confidence band"
                        if era_class == "SCHEDULE" else "artifact band width plus era-gap rule"
                    ),
                    "instrument_class": klass, "composition": composition,
                    "model_version": self.version,
                    "artifact_sha256": self.artifact_sha256,
                    **mdetail},
        )


def _as_utc(t: datetime) -> datetime:
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


@lru_cache(maxsize=4)
def _parse_spread_model_cached(
    path_str: str, artifact_sha256: str, data: bytes
) -> SpreadModel:
    try:
        doc = json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SpreadModelError(f"spread model is not valid JSON at {path_str}") from exc
    return SpreadModel(
        doc,
        source=Path(path_str),
        artifact_sha256=artifact_sha256,
    )


def load_spread_model(path: Path | str | None = None) -> SpreadModel:
    p = Path(path or DEFAULT_MODEL)
    if not p.is_file():
        raise SpreadModelError(
            f"spread model not found at {p}. Build it with "
            "`python3 scripts/build_spread_model.py scan-ticks && ... scan-bars && ... fit`."
        )
    try:
        current = read_current_file_bytes(p, label="spread model artifact")
    except CostInputAuthorityError as exc:
        raise SpreadModelError(str(exc)) from exc
    return _parse_spread_model_cached(
        str(current.path), current.sha256, current.data
    )


def spread_price(symbol: str, account: str, at_utc: datetime | None = None, *,
                 band: str = "mid", vol_state: int | None = None,
                 vol_kind: str = "trailing", require_decidable: bool = False,
                 composition: str = DEFAULT_COMPOSITION,
                 era_exponent: float | None = None,
                 model: SpreadModel | None = None) -> SpreadEstimate:
    """Quoted spread in price units at `at_utc`, on the requested band.

    `composition` selects how the era and hour terms combine -- ``"v2_damped"`` (the
    measured default) or ``"v1_multiplicative"`` (the pre-2026-07-30 product, kept so any
    earlier banded number can be reproduced exactly). `era_exponent` overrides the fitted
    exponent, for walking `ERA_HOUR_EXPONENT_ENVELOPE`.
    """
    return (model or load_spread_model()).estimate(
        symbol, account, at_utc, band=band, vol_state=vol_state, vol_kind=vol_kind,
        composition=composition, era_exponent=era_exponent,
        require_decidable=require_decidable)
