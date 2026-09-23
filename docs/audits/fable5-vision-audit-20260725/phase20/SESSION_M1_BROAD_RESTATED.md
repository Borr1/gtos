# THE BROAD V4 FAMILY, RESTATED ON THE REPAIRED INSTRUMENT

**Lane m1, wave 20, phase 20. 2026-08-07.**
Receipts: `phase20/receipts/m1/`. Population: **1,167,099 emissions** over the eight open
windows 2025-10 … 2026-05, every one of them, nothing sampled. The sealed three
(Jun/Aug/Sep 2025) are not opened.

---

## 0. THE VERDICT DOES NOT CHANGE. TWO OF ITS THREE LEGS DO, AND ONE OF THEM BREAKS.

> **On the repaired instrument not one of the ten families is gross-positive, where five
> were, and family-months gross-positive collapses from 36 / 80 to 2 / 80. The walker
> repair alone does all of it.**

That is the headline and it strengthens the verdict. But the wave-19 verdict rested on
three legs, and re-derived they behave differently from one another:

| leg | published | re-derived | standing |
|---|---|---|---|
| **1 — a 253× price-unit shortfall** | +0.0119 bps captured vs 3.0159 bps toll | on the eight OPEN windows the numerator was **already negative before any repair** (−0.643 bps) and is **−2.153 bps** after | **STRENGTHENED, and the ratio is undefined**: there is no shortfall factor because there is nothing in the numerator |
| **2 — 0.97× accumulation** | 0.965× vs a live sleeve's 37.58×, published with **no interval** | point estimate 0.867× (legacy roster, deterministic mirror) → **0.587×** (repaired); **CI95 [−2.07, +2.22]** | **DIES AS A NUMBER, SURVIVES AS A BOUND.** The ratio is not a measurable quantity. What is measurable: **P(growth ≥ 10×) = 0.0073** on the broad family against **0.63** on the live control |
| **3 — a free broker still leaves it negative** | −0.01327 R/trade, 104.72 % reduction needed | **−0.00600 R/trade**, 102.12 % needed | **UNCHANGED**, magnitude 2.2× smaller |

And one thing moves the *other* way, which no reader should be allowed to miss:

> **The family is materially LESS unprofitable than published.** 61.0 % of the published
> toll was a spread charged as a cost LEVEL, and the corrected walk charges it as geometry
> instead. Net per emission goes **−0.10704 → −0.07142** and net per fill
> **−0.36111 → −0.25575**. It is 29 % cheaper to run and has no positive family left.

**Two published headlines are overturned outright.**

1. *"Before costs they are within half a percentage point of break-even"* (owner report,
   Correction 2). At the correct quote side the gross gap is **−6.89 pp**, not −0.57 pp —
   **twelve times larger**. The win rate itself falls 42.28 % → 36.34 % because 11,870
   booked targets were stops and 4,223 path-ends were stops.
2. *"The toll falls 7.4× across the deciles; the gross never leaves a ±0.04 band and has no
   trend"* (FIND 2). Reproduced exactly on the old walker (7.49×, range 0.048,
   corr −0.84) and **INVERTED** on the corrected one: range **0.203**, corr **+0.87**. The
   gross is strongly monotone in stop width, and the tightest-stop decile — the only
   gross-positive cell in the published table — is now the **worst** at −0.292 R, because
   it hands the broker **29.4 %** of its risk unit at the door.

---

## 1. THE INSTRUMENT, AND FOUR CONTROLS IT HAD TO PASS

One walk of the whole population produces every table below; each arm is a groupby of the
same measurement, so no two numbers here can drift apart.

* **contract** — f1/r2's, unchanged: at-market families take a market order at the decision
  instant, the three POI families rest an honest limit at the emitted level, target 1.5 R
  (`risk.min_rr`), horizon 120 M1 bars, stop wins ties, the h1 four-term broker-true toll
  charged once on fill in price units and divided by that row's own risk distance.
* **generator repair (r2)** — rows the repaired emission contract refuses are dropped. The
  refusal predicates are **re-derived here from the roster**, not imported.
* **walker repair (r1)** — the correction is taken from the shipped module
  (`src/research_infra/walkforward/quote_side.py`) and applied by order type:
  * **at-market (7 families)** — the entry IS the decision-instant close, so it is a market
    order; a market order transacts on the far side and `order_router.py:66-73` then hangs
    both exit legs off the transacted price, so the whole geometry translates by
    `direction × spread` (`replay_anchor`).
  * **POI limits (3 families)** — the order transacts AT its own level, so
    `level_anchor_for_replay` gives the exit anchor (LONG unchanged, SHORT level − spread)
    and `entry_trigger_level_on_tape` gives the fill trigger (LONG level − spread, i.e. a
    buy limit fills **later and less often**; SHORT unchanged).
* **spread** — primary is the toll's OWN hour-aware tick spread, so that dropping the toll's
  spread term and charging it in the geometry is an exact substitution rather than an
  approximation. The era-aware model (`quote_side.spread_for`) is carried per row as a
  sensitivity; the tick spread runs **6.0 % wider** than the era model at the median and the
  swap moves the emitted-stage net by 0.008 R (−0.07142 → −0.06328) (`M1_FUNNEL_V1.json → spread_sensitivity_era_model`).

| control | expected | measured | file |
|---|---|---|---|
| the uncorrected arm reproduces `R2_ARM_ECON_V1.json → arms.legacy` | n 1,167,099 / gross −0.022564 / cost 0.084479 / net −0.107043 / fills 345,963 | **identical to six decimals, Δn = 0, Δfills = 0** | `m1_walk.py`, `M1_FUNNEL_V1.json → control` |
| the repaired roster is the legacy roster minus refusals, nothing added | r2's blast radius | **8/8 windows, 0 added**, 90,217 removed; row-wise agreement with the repaired roster on **1,167,098 of 1,167,099** rows — the single disagreement is the cross-asset-leader refusal r2 itself named and no per-row test can see | `m1_walk.py → subtractive_check` |
| the whole-population refusal counts | r2: past_stop 25,243, stale 66,383 | **25,243 and 66,383**, kept 1,120,861 vs r2's emitted 1,120,860 (the same one row) | `accum2.log` |
| the accumulation harness reproduces d3's own REAL arm | `D3_CURVE.json → broad.gross_r` | **exact at all six horizons** on 144,725 rows (max \|Δ\| 6.9e-18) | `m1_accum.py` |
| the taken book reproduces f1's realised record | n 464 / gross +0.05505 / cost 0.07437 / net −0.01932 | **identical** | `M1_TAKEN_V1.json → realised_arm_record` |
| the day-restricted arm reproduces f1's population | 1,118,694 emissions | **1,118,694** | `M1_FUNNEL_V1.json → funnel_f1_day_restricted` |

### 1.1 Five arithmetic invariants the implementation had to satisfy

Controls prove the arm reproduces a published number. These prove the *correction itself*
is what the module says it is — each is a property it must have by construction, so a
violation would be a bug in this lane rather than a finding
(`receipts/m1/M1_INVARIANTS.txt`, whole population):

| # | invariant | measured |
|---|---|---|
| A | an at-market row can never be **helped**: the stop stays −1, the target stays +T but recedes, a path_end loses exactly `s/d` | 141,330 at-market rows, **0** with a positive delta, max delta exactly **0.0**; on the 31,401 path_end→path_end rows `\|Δ − (−s/d)\|` ≤ **5.7e-13** |
| B | `stop → target` is **impossible** at-market — both levels move the same way, so the stop can only fire earlier and the target later | 175 such rows in total, **0 at-market**, all 175 POI (where the fill bar itself moves) |
| C | losing a fill is a **LONG-only POI** event — a buy limit's trigger drops one spread, a sell limit's does not | 5,048 lost fills, **5,048 POI, 5,048 LONG, 0 SHORT**, and **0 gained** |
| D | POI **shorts** keep their fill set byte-for-byte | 463,953 rows, **0 changed** |
| E | a POI long that fills on the **same bar** keeps its R exactly | 95,985 filled in both arms, **93,618 (97.53 %) unchanged**; the other 2.47 % filled later, which is the entire mechanism |

**The net convention, stated once.** The published net charges the spread as a level
*and* the corrected walk charges it as a resolution effect; doing both double-counts it.
Following r1, the corrected net is `gross_corrected − (commission + slippage + swap)/d`.
The double-charged variant is published too, explicitly labelled, because it is the bound
a reader who rejects the substitution wants. Both are in every table.
Toll composition on the repaired filled cohort: **spread 60.98 %**, commission 28.30 %,
slippage 5.38 %, swap 5.35 %.

---

## 2. THE FUNNEL, END TO END

Eight open windows, all 1,167,099 emissions. `OLD` = published instrument; `GEN` =
generator repaired only; `WALK` = walker repaired only; `BOTH` = repaired instrument.

| stage | arm | n | gross | toll | **net** |
|---|---|---:|---:|---:|---:|
| every candidate emitted | OLD | 1,167,099 | −0.02256 | 0.08448 | **−0.10704** |
| every candidate emitted | WALK | 1,167,099 | −0.06022 | 0.03236 | −0.09258 |
| **…after the repaired emission contract** | GEN | 1,117,986 | −0.00170 | 0.08039 | −0.08209 |
| **…after the repaired emission contract** | **BOTH** | **1,117,986** | **−0.04040** | **0.03102** | **−0.07142** |
| …those that actually filled | OLD | 345,963 | −0.07612 | 0.28499 | −0.36111 |
| …those that actually filled | GEN | 317,127 | −0.00600 | 0.28340 | −0.28941 |
| **…those that actually filled** | **BOTH** | **312,223** | **−0.14466** | **0.11109** | **−0.25575** |
| the legacy "clean" cohort (defect family and past-stop rows removed by hand) | OLD | 311,562 | −0.00611 | 0.28586 | −0.29197 |
| the legacy "clean" cohort | BOTH | 306,776 | −0.14607 | 0.11034 | −0.25641 |
| **the trades the system actually took** (walked, t=1.5 R) | OLD | 507 | +0.18045 | 0.14938 | +0.03107 |
| **the trades the system actually took** | **BOTH** | **507** | **+0.05216** | **0.01108** | **+0.04108** |
| the trades the system actually took — the arm's own realised record | — | 464 | +0.05505 | 0.07437 | −0.01932 |

Double-charged bound (spread charged twice, for the sceptic): emitted **−0.11862**, filled
**−0.42473**, taken **−0.09722**.

Day-restricted to f1's own arm trading days, so the rows line up with the published table:
emitted 1,118,694 → net −0.10629 (OLD) / **−0.07080** (BOTH); filled 332,845 → −0.35722 /
**−0.25249**; clean 299,832 → −0.28785 / **−0.25287**.

**Three things to read out of this table.**

1. **The generator repair and the walker repair push the gross in opposite directions and
   the net in the same direction.** GEN moves the emitted gross +0.02086 (it removes rows
   that were mechanically dead); WALK moves it −0.03766 (it charges the crossing). Both
   improve the net, for different reasons.
2. **The taken book is net-positive on the walked contract under every arm except the
   double-charged one — and it is still indistinguishable from zero.** Day-block
   CI95 [−0.0525, +0.1389], p(≤0) = 0.20 on 153 day blocks. The verdict's statement that
   this book cannot be adjudicated by running it survives intact.
3. **The published clean-cohort gross of −0.01327 is not the like-for-like predecessor of
   my −0.00611.** f1 priced all ten families as limits; d1b established that seven of them
   emit at-market. −0.00611 is that correction applied, on the same days.

---

## 3. WIN RATE AGAINST ITS OWN BREAKEVEN, AT `min_rr` = 1.5

| basis | n | win rate | breakeven | gap |
|---|---:|---:|---:|---:|
| published (owner report, Correction 2) — gross | 298,537 | 37.98 % | 38.55 % | **−0.57 pp** |
| repaired roster, filled, **old walker** — gross | 317,127 | 42.28 % | 42.57 % | −0.28 pp |
| **repaired roster, filled, corrected — gross** | **312,223** | **36.34 %** | **43.22 %** | **−6.89 pp** |
| published — net | 298,537 | 37.98 % | 50.58 % | −12.60 pp |
| **repaired roster, filled, corrected — net** | **312,223** | **35.53 %** | **47.58 %** | **−12.05 pp** |
| repaired roster, filled, old walker — net | 317,127 | 39.71 % | 53.06 % | −13.35 pp |

**The "half a percentage point from break-even before costs" line is an artifact of the
uncorrected walker and it is the single most-quoted number in the owner report.** The
mechanism is 23,073 exit-reason changes on the repaired population (1.98 % of rows), and
they are almost one-directional:

| transition | n |
|---|---:|
| target → stop | 11,870 |
| path_end → stop | 4,223 |
| target → no_fill | 3,347 |
| target → path_end | 1,892 |
| path_end → no_fill | 1,418 |
| stop → target | **168** |
| stop → no_fill | 139 |
| stop → path_end | 16 |

93.13 % of the whole gross delta sits on the rows that changed exit reason. **No cost term
can undo a trade that is booked as reaching its target and in truth stopped first.**

---

## 4. THE FAMILY TABLE — the part that is not close

Gross R per emission, and how many of the eight windows are gross-positive.

| family | kind | OLD | mo | GEN | mo | WALK | mo | **BOTH** | **mo** |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| structural_distance_extreme | at_market | **+0.04525** | **8** | +0.04549 | 8 | −0.23509 | 0 | **−0.23688** | **0** |
| liquidity_sweep_reclaim | at_market | +0.02054 | 6 | +0.02093 | 6 | −0.14185 | 0 | −0.14150 | 0 |
| cross_asset_lead_lag | at_market | +0.01362 | 6 | +0.00843 | 4 | −0.19403 | 0 | −0.19915 | 0 |
| displacement_continuation | at_market | +0.00130 | 5 | +0.00084 | 5 | −0.08915 | 0 | −0.08890 | 0 |
| session_open_range_break | at_market | +0.00103 | 5 | +0.00103 | 5 | −0.05924 | 1 | −0.05924 | 1 |
| current_ob_retest | POI_limit | −0.00204 | 2 | −0.00084 | 3 | −0.00811 | 0 | −0.00694 | 0 |
| regime_transition_break | at_market | −0.00196 | 3 | −0.00196 | 3 | −0.03452 | 1 | −0.03452 | 1 |
| current_fvg_fill | POI_limit | −0.00560 | 1 | −0.00479 | 1 | −0.03408 | 0 | −0.03343 | 0 |
| volatility_compression_expansion | at_market | −0.04011 | 0 | −0.04046 | 0 | −0.09540 | 0 | −0.09561 | 0 |
| current_breaker_re_entry | POI_limit | −0.26166 | 0 | **−0.00746** | 2 | −0.27295 | 0 | −0.02253 | 0 |
| **families gross-positive** | | **5 / 10** | | 5 / 10 | | **0 / 10** | | **0 / 10** | |
| **family-months gross-positive** | | **36 / 80** | | 37 / 80 | | 2 / 80 | | **2 / 80** | |

**`structural_distance_extreme` — the estate's one real family, "the single most
interesting unsettled thing in the estate", positive in fifteen consecutive windows across
three harnesses — is negative in eight of eight and the mechanism is arithmetic.** Its
median stop is **3.117 bps** and its median spread-over-risk is **0.2499**: it pays a
quarter of its risk unit to cross the book. This is the third independent kill (p3 §10
published +0.06293 → −0.13028; r1's broad rewalk +0.06303 → −0.11278; here +0.04525 →
−0.23688 on a different contract, a different cohort and a different spread source), and
the first one that is per-window.

The mechanism generalises across the whole family: on the repaired fills the median
spread-over-risk is **0.0945**, **47.9 %** of rows are above 0.10 and **16.4 %** above 0.25.

The one family the generator repair rescues is `current_breaker_re_entry`: −0.26166 →
−0.00746, exactly r2's claim, and it is still negative and still 0 of 8 once the quote side
is charged.

---

## 5. THE ACCUMULATION CURVE — the load-bearing leg, and it does not survive as a number

d3's construction, unchanged: horizons {8, 32, 96, 288, 640, 1280} **printed** M15 bars =
{2, 8, 24, 72, 160, 320} trading hours, native stop, target 3.0 R, paired against a
side-flipped control. Two things are fixed:

* **the control.** d3 paired against a single coin flip, which discards half the pairs. A
  deterministic **mirror** (every row walked both sides, difference halved) estimates the
  same quantity with zero draw variance. **The coin was worth 27 % of the published broad
  signal**: my walk reproduces d3's REAL arm to 1e-18, and its placebo differs by
  0.0056 R against a published signal of 0.0207 R.
* **the anchor for the POI families.** The screen is a statement about the SIGNAL, so all
  ten families are measured at market — anchored at the **decision-instant close**, not at
  the emitted level. For the seven at-market families those are the same number
  (fill_gap_R = 0 on 144,725 of 144,725 rows); for the three POI families they are not, and
  walking a POI candidate from a level 84 % of them are already through books an instant
  +3 R and measures the gate, not the direction call.

### 5.1 The broad family

| horizon | published (d3, coin, legacy) | legacy roster, mirror | repaired roster, old walker | **repaired instrument, mirror** | 95 % CI on the repaired signal (R) |
|---:|---:|---:|---:|---:|---|
| 2 h | 0.2008 bps | 0.1483 | 0.1115 | **0.0779** | [−0.00042, +0.01633] |
| 8 h | 0.2051 | 0.1441 | 0.1124 | 0.0718 | [−0.00204, +0.01646] |
| 24 h | 0.2077 | 0.1327 | 0.0982 | 0.0576 | [−0.00342, +0.01520] |
| 72 h | 0.1943 | 0.1290 | 0.0896 | 0.0474 | [−0.00476, +0.01464] |
| 160 h | 0.1904 | 0.1259 | 0.0866 | 0.0438 | [−0.00544, +0.01437] |
| 320 h | 0.1938 | 0.1285 | 0.0894 | **0.0457** | [−0.00517, +0.01442] |
| **growth 2 h → 320 h** | **0.965×** | 0.867× | 0.802× | **0.587×** | **CI95 [−2.07, +2.22]** |
| **P(growth ≥ 10×)** | — | 0.0015 | 0.0015 | **0.0073** | |

(bps in d3's own form — signal_R × the cohort's median stop width — so the columns are
comparable. Per-row price units are in `M1_ACCUM_V1.json`; they are noisier still.)

**The ratio is not a measurable quantity, and it never was.** Its 95 % interval spans
−2.07 to +2.22; its per-window values run 3.0×, 4.4×, 1.0×, −4.8×, −4.4×, −1.5×, −1.3×,
2.8×. d3 published `0.965×` and `37.58×` with no interval on either and made the
comparison the estate's admission screen.

**What survives, and it survives cleanly, is the screen's verdict expressed as a
probability and a level:**

| statement | broad family (repaired) | live sleeve control (repaired) |
|---|---:|---:|
| P(growth ≥ 10×) — the screen's own bar | **0.0073** | **0.629** |
| P(growth ≥ 3×) | 0.0180 | 0.853 |
| signal at 320 h, per-row bps | −0.107 | **+142.76** |
| its 95 % CI | [−0.630, +0.410] | [+40.94, +233.40] |
| p(≤0) at 320 h | 0.65 | **0.0035** |
| its own measured toll at 320 h (d3) | 3.19 bps | 29.23 bps |
| **320 h signal vs its own toll, at the 95 % bound favouring it** | upper bound **+0.410 bps = 7.4× SHORT** | lower bound **+40.94 bps = 1.40× OVER** |

Even at the **top** of its own 95 % interval the broad family's 320-hour signal is 7.4×
below the toll it must pay to transact, while the live control clears its own — larger —
toll at the **bottom** of its interval. That is the honest form of leg 2 and it needs no
ratio.

### 5.2 The live control moved too, and d3's 37.58× was mostly the coin

| arm | growth 2 h → 320 h | 320 h signal (R) |
|---|---:|---:|
| d3 published (coin flip, old walker) | **37.58×** | 0.5341 |
| old walker, deterministic mirror | 15.94× | 0.5819 |
| **repaired walker, deterministic mirror** | **16.65×** | 0.5671 |

More than half of the published 37.58× was one coin draw. The quote-side repair barely
touches it (15.94 → 16.65) — as it should, because these sleeves' median stop is
**215.4 bps** against the broad family's 9.9, so their spread-over-risk is two orders of
magnitude smaller. **That contrast is itself the discriminant**, and it is more robust than
the ratio d3 built the screen on.

Carried forward unchanged, because it is still the largest soft spot: **this control is
in-sample and n = 134.**

### 5.3 A finding the repair produced rather than removed

With the POI families measured at market from the decision instant, the **whole-family**
signal does grow: 0.00753 R at 2 h → 0.01148 R at 320 h, ratio 1.52× (CI95 [−0.98, +4.06]).
It still fails the screen — P(≥ 3×) = 0.056, P(≥ 10×) = 0.0055 — and at 320 h its per-row
price capture is **−0.208 bps**. But the direction call in the POI families is not flat,
and nobody has looked at it at market before, because d1b's mirrored-limit control was an
artifact and the unconditional POI direction test did not exist in wave 19.

---

## 6. TOLL DECILES — the table that inverts

Ten deciles of the generator's own stop width, on the repaired filled cohort.

| decile | stop (bps) | median spread/risk | gross **OLD** | gross **CORRECTED** | toll | net (corrected) |
|---:|---|---:|---:|---:|---:|---:|
| 0 | 0.26 – 2.89 | **0.2942** | **+0.01256** | **−0.29168** | 0.25120 | −0.54288 |
| 1 | 2.89 – 4.27 | 0.1869 | −0.00043 | −0.20656 | 0.09475 | −0.30132 |
| 2 | 4.27 – 5.67 | 0.1389 | +0.00759 | −0.16635 | 0.07376 | −0.24010 |
| 3 | 5.67 – 7.26 | 0.1103 | +0.01048 | −0.13073 | 0.09039 | −0.22112 |
| 4 | 7.26 – 9.27 | 0.0875 | −0.01559 | −0.14137 | 0.09739 | −0.23876 |
| 5 | 9.27 – 11.93 | 0.0695 | −0.00003 | −0.11129 | 0.11623 | −0.22752 |
| 6 | 11.93 – 15.98 | 0.0564 | −0.01393 | −0.10911 | 0.12811 | −0.23721 |
| 7 | 15.98 – 23.32 | 0.0475 | −0.00327 | −0.09661 | 0.12453 | −0.22114 |
| 8 | 23.32 – 41.22 | 0.0368 | −0.02409 | −0.10377 | 0.09232 | −0.19609 |
| 9 | 41.23 – 1624 | 0.0368 | −0.03332 | **−0.08916** | 0.04218 | −0.13134 |
| | | | corr(rank, gross) **−0.83** | corr(rank, gross) **+0.87** | | |

Published: *"the gross never leaves a ±0.04 band and has no trend."* Measured on the old
walker: range 0.046, correlation −0.83 — reproduced. Measured with the quote side charged:
range **0.203**, correlation **+0.87**. **The apparent edge in the tightest stops — the
thing that made `structural_distance_extreme` look real, and the whole "trade tighter to
make the edge a bigger fraction of R" argument — is the bid-ask, exactly and only.**

The net is still worst at the tight end and best at the wide end, so the shape of the
published conclusion survives; its stated cause does not.

---

## 7. THE THREE VERDICT LEGS, RE-DERIVED

### Leg 1 — the price-unit shortfall

The construction that reproduces the published toll to 0.2 % (3.0219 here vs 3.0159
published) is the per-row mean of `price move ÷ price`, in bps. Applied to the numerator on
the eight open windows:

| cohort | gross (bps) | toll (bps) | net (bps) | shortfall factor |
|---|---:|---:|---:|---|
| legacy clean, old walker | **−0.6431** | 3.0219 | −3.6650 | undefined — numerator negative |
| repaired filled, old walker | −0.6154 | 3.0290 | −3.6441 | undefined |
| **repaired filled, corrected** | **−2.1534** | 1.3581 | −3.5115 | undefined |

The published **253.4×** is a sealed-months figure (+0.0119 bps against 3.0159). **On the
eight open windows the numerator was already negative before any repair.** I have not
re-opened the sealed months, and this is a bound rather than a measurement: the correction
costs **−0.1270 R per fill** on the open windows with a constant sign, which is **4.7× the
sealed cohort's entire gross of +0.02718 R/fill**, so the sealed positive cannot survive it
unless those three months' spread-over-risk is five times smaller than these eight — same
instruments, adjacent era, so it is not.

**Leg 1 is stronger than published and its headline number should be retired**: "253×
short" implies a ratio, and there is nothing in the numerator to take a ratio of.

### Leg 2 — accumulation

§5. **The 0.97× is not a measurement.** The screen's verdict survives as
P(growth ≥ 10×) = 0.0073 and as a 320-hour signal whose own 95 % upper bound is 7.4× below
its toll. The discriminant against the live sleeves survives and widens
(0.0073 vs 0.629), but the two numbers that expressed it — 0.97× and 37.58× — should both
be replaced, because half of the second one was a coin flip.

### Leg 3 — a free broker

A zero spread means the correction has nothing to charge, so the free-broker book earns the
**uncorrected** gross. On the repaired roster that is **−0.00600 R per fill** (published
−0.01327 on the legacy clean cohort, −0.00611 here on the same cohort at the corrected
order-type assignment). Required cost reduction **102.12 %**. **Infeasible, unchanged, and
the arithmetic is the same one d7 ran.**

---

## 8. WHAT I GOT WRONG, AND WHAT IS STILL OPEN

* **The first accumulation pass was wrong and I caught it on the numbers, not by review.**
  Walking the POI families from their emitted level produced `signal_R = 1.53` and
  `real_R = 2.23` — an "edge" of 1.5 R per trade, which is the gate firing, not a direction
  call, because 84–92 % of those candidates are already through their own target when born
  (FIND 5; r2's census puts `current_fvg_fill`, the largest of the three, at 84.279 %).
  Anchoring at the decision-instant close fixes it. The published curve is unaffected
  (d3 measured the at-market cohort only) but the extension in §5.3 would have been a
  fabricated result.
* **The net convention is a choice and it is worth 0.17 R per fill.** Charging the spread
  once as geometry (r1's substitution) gives net −0.25575; charging it twice gives
  −0.42473. I have published both at every stage. My reading is that the substitution is
  right — a stop placed one risk distance below your *fill* loses exactly 1 R when it is
  hit, with no second spread to pay — but a reader who wants the pessimistic bound has it.
  **One residual double-count I could not eliminate:** the toll's slippage term (5.38 % of
  the toll) is measured from live deals against the broker's own mid, so it may already
  contain half a spread. If so the corrected net is pessimistic by up to ~0.008 R/fill.
* **The eight windows are all in-sample for this family.** Every rule, filter and family
  choice in the estate's history saw them. Nothing here is an out-of-sample test, and the
  three sealed months are spent. This lane changes the *instrument*, not the *evidence
  base*, and no measurement on these eight windows can now reopen the verdict.
* **The corrected POI long fill is modelled, not tick-verified.** A buy limit fills when
  the ask reaches the level, so on a bid tape the trigger sits one spread lower and 5,048
  rows lose their fill — 4,904 of them inside the repaired population, 3,347 of those having
  been booked as targets. All 5,048 are POI longs and none is a short (invariant C).
  v1's tick truth
  validated the at-market side of the correction directly; it did not walk a resting limit.
  That is the one limb of this measurement resting on the convention rather than on ticks.
* **What is NOT here.** No re-run of the sealed months, no new held-out data, no
  economic-selection sweep — §6 of the verdict explicitly closes that space and nothing
  measured here reopens it.

---

## 9. STANDING

**The verdict is SIGNAL, unchanged, and better supported than when it was written.** The
family emits setups whose risk distance is comparable to the spread, and once the walk
knows which side of the book it is on, **every one of its ten families is gross-negative in
essentially every month**. What has to change in the published record is the *rhetoric*,
because three of its most quotable numbers are artifacts of the bent ruler: the half-point
gross gap (really 6.9 points), the flat toll-decile gross (really monotone, sign-inverted),
and the 253× / 0.97× / 37.58× triple, of which the first has no numerator, the second has a
CI four units wide, and the third was mostly a coin flip.

**Nothing here touches either funded account.** The broad family has never traded live;
`src/components/broader_origin_generators.py` is absent from `run_book.py`'s import closure
(v1 measured 0 of 240 modules) and no armed sleeve resolves a callable in it. This lane
wrote no production code and edited no file under `src/`.

---

*Receipts: `phase20/receipts/m1/` — `m1_walk.py` → per-window `.npz` (kept in `/tmp/m1`,
5–6 MB each, regenerable in 9 s/window); `M1_FUNNEL_V1.json`, `M1_ACCUM_V1.json`,
`M1_ACCUM_CI_V1.json`, `M1_LIVE_ACCUM_V1.json`, `M1_TAKEN_V1.json`, `M1_DECILES_V1.json`,
`M1_DECILES.txt`, `M1_INVARIANTS.txt`.*
