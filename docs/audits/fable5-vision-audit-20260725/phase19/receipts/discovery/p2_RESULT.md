# p2 — THE SEALED TEST. Result.

**The three held-out windows are now SPENT.** `june_2025`, `august_2025`, `september_2025` — 63 days,
470,472 candidate emissions, nothing in this estate had ever read them. One pass, on the hypotheses
and thresholds fixed in `p2_PREDECLARATION.md` before the first sealed row was opened.

**Headline.** On three never-read months the broad V4 family's gross expectancy is **+0.02718 R per
fill** against a **0.34262 R** broker toll — the signal is real, statistically non-zero, and pays
**7.9%** of its own broker bill. In price units it captures **0.0119 basis points per trade** and
pays **3.0159 basis points**. **The wave's verdict is CONFIRMED out of sample, and the surviving
candidate FAILED.**

| # | hypothesis | declared threshold | sealed result | verdict |
|---|---|---|---|---|
| **H1** | the signal is zero | `\|gross\| ≤ 0.05` and `net ≤ −0.10` | gross **+0.02718**, net **−0.31545** | **CONFIRMED** |
| **H2** | `structural_distance_extreme` is real | gross `≥ +0.03`, ≥2/3 windows | **+0.12522**, **3/3** | **REPLICATES** (1.7× stronger than in sample) |
| **H3** | exit swap `stop_only_horizon` | Δnet `≥ +0.02`, ≥2/3 | **+0.01002**, 3/3, CI crosses 0 | **DOES NOT REPLICATE** |
| **H4-a** | fill repair vs range-containment | Δnet `≥ +0.015`, ≥2/3 | **−0.00049** | **DOES NOT REPLICATE** |
| **H4-b** | fill repair vs d5's own baseline | Δnet `≥ +0.015`, ≥2/3 | **+0.02087**, **3/3** | **REPLICATES** |
| **H5a** | forming-bar paired effect | Δnet `≥ +0.10`, all windows | **+0.18063**, 1/1 | **REPLICATES** |
| **H5b** | **the surviving candidate is tradeable** | partial book `net > 0` and beats close in ≥2/3 | **−0.30551** vs close **−0.28041**, **0/1** | **FAILS** |
| **H6** | direction vs its own mirror | `≥ +0.02` with CI excluding 0 | **+0.02391**, CI95 [−0.00313, +0.05122] | **DIRECTION ZERO** (leaning positive; f2's sign, not d7's) |

---

## 0. What was run, and the proof it is the right object

The test is on the **reproduced sealed roster** — the generator's own emissions — not on the sealed
diagnostic pools, which are the counterfactual missed-opportunity ledger. Measured here: the three
pools hold 62,871 rows against 470,472 close-only emissions, i.e. the pool is **13.36%** of generator
output on these windows, consistent with the estate's 18.03% figure and confirming again that the
pool is a small conditioned subset, not the system's trades.

**Harness validation, done on an OPEN window before the seal was broken** (`p2_VALIDATE_JAN.json`):

| quantity | published | this harness |
|---|---|---|
| `EARLY5` setup keys, January 2026 | 17,237 | **17,237** |
| `EARLY5` paired Δnet, January 2026 | +0.19562372 | **+0.19562** |
| `EARLY5` phantom leg, January 2026 | −0.93653 (n 5,040) | **−0.93559 (n 5,047)** |
| regenerated January roster rows | 153,598 | **153,598** |
| d5 one-sided estate fill rate on `gap_r<0` rows | 0.9998 | **0.99979** |

**Every sealed number has an in-sample counterpart from identical code.** The same harness was run on
four open windows — Nov 2025, Dec 2025, Jan 2026, Apr 2026, 146,901 clean fills — so no comparison in
this receipt crosses a code boundary.

### Coverage

| window | days generated | days used | emissions (close-only) | clean fills used |
|---|---:|---:|---:|---:|
| `june_2025` | 21 | **13** | 134,726 | 22,494 |
| `august_2025` | 21 | 21 | 168,039 | 36,403 |
| `september_2025` | 22 | 22 | 167,707 (2,321,399 incl. `k=1..14`) | 38,905 |
| **pooled** | 64 | **56** | **470,472** | **97,802** |

June loses 8 days to the declared data-availability rule (§1.1): the M15 bridge archive begins
2025-06-01T22:00Z and a decision instant needs 672 closed M15 bars, first satisfied 2025-06-12. The
rule was fixed before any outcome was computed. September carries the full partial-bar grid
(`k = 1..14`); August and June are close-only, per the compute allocation recorded in §6.1 of the
declaration, so **H5 is tested on one sealed window** and labelled as such throughout.

---

## 1. H1 — PRIMARY. The signal is zero. **CONFIRMED.**

Clean roster (all emissions minus `current_breaker_re_entry` minus born-past-stop), corrected
contract (at-market families as market orders, POI families as honest resting limits), 2.0R, 120 M1
bars, h1 broker-true cost.

| | sealed (3 windows) | in-sample (4 open windows) |
|---|---:|---:|
| clean fills | 97,802 | 146,901 |
| **gross R/fill** | **+0.02718** | +0.01842 |
| toll R/fill | 0.34262 | 0.30046 |
| **net R/fill** | **−0.31545** | −0.28204 |
| win rate | 39.337% | 39.154% |
| payoff | 1.61856 | 1.60611 |
| breakeven (gross) | 38.189% | 38.371% |
| breakeven (net) | **52.658%** | 51.133% |
| windows gross-positive | **3 / 3** | 3 / 4 |

Day-block bootstrap (4,000 draws, 56 day blocks): gross **+0.02718, CI95 [+0.01096, +0.04293]**,
p(≤0) = 0.001. Net **−0.31545, CI95 [−0.33641, −0.29372]**, p(≤0) = 1.000.

Per window — gross / net: `june_2025` **+0.04024 / −0.24127**; `august_2025` **+0.02501 / −0.32224**;
`september_2025` **+0.02166 / −0.35198**.

**Read the sign carefully, because it matters and it is not what the estate has been saying.** The
family's gross is **positive and statistically distinguishable from zero** (p(≤0) = 0.001, 3/3
windows) — it is not "zero" in the literal sense and it is certainly not negative. It falls inside the
declared zero-band because the band was set at ±0.05, five times f2's detection floor. What the
sealed data settles is the *ratio*, and the ratio is brutal:

* **gross / toll = 0.0793.** The family's entire directional content pays 7.9% of its own broker bill.
* The win rate is **1.15 percentage points above** its gross breakeven and **13.32 points below** its
  net breakeven. Every point of that 13.32 is the toll.
* In price units — the unit that does not divide by the generator's own stop width — the family
  captures **+0.0119 bps per trade** and pays **3.0159 bps**. **253× short.**

Secondary contracts, pooled sealed: f1 all-limit contract gross +0.02723 / net −0.31534 (n 97,163);
whole roster including the defective family gross +0.03052 / net −0.30801 (n 101,652); per emission
(no_fill booking 0) gross +0.00730 / net −0.08469 on 364,293 emissions. **The conclusion does not
move with the contract.**

### 1.1 The mechanism, on the sealed rows [post-hoc, descriptive]

Both the gross and the toll are functions of the generator's own stop width, and the toll wins at
every point on the curve.

| stop bps | n | median bps | gross | toll | net |
|---|---:|---:|---:|---:|---:|
| 0.42–2.56 | 9,781 | 1.97 | **+0.10653** | 0.72546 | −0.61893 |
| 2.56–3.53 | 9,780 | 3.04 | +0.06013 | 0.44231 | −0.38218 |
| 3.53–4.58 | 9,780 | 4.05 | +0.03131 | 0.34534 | −0.31403 |
| 4.58–5.70 | 9,780 | 5.13 | +0.04809 | 0.29980 | −0.25171 |
| 5.70–7.18 | 9,780 | 6.39 | +0.01339 | 0.32256 | −0.30917 |
| 7.18–9.10 | 9,780 | 8.07 | −0.00799 | 0.30400 | −0.31199 |
| 9.10–11.97 | 9,780 | 10.38 | +0.02461 | 0.29350 | −0.26889 |
| 11.97–16.70 | 9,780 | 13.95 | +0.00992 | 0.27706 | −0.26713 |
| 16.70–27.45 | 9,780 | 21.03 | +0.00066 | 0.25501 | −0.25435 |
| 27.45–853.79 | 9,781 | 43.03 | −0.01488 | 0.16119 | −0.17608 |

The R-denominated gross is monotone in stop tightness because R divides by the stop; so is the toll,
and 4.5× faster. **No decile is net-positive and none is close.** This is d1b's toll-decile finding
reproduced on unseen data with a different harness.

---

## 2. H2 — the one family that looked real IS real. **REPLICATES, and got stronger.**

`structural_distance_extreme`, the estate's only reliably gross-positive broad family, was tested out
of sample for the first time.

| | sealed | in-sample (4 open) | d1b published (8 windows) |
|---|---:|---:|---:|
| clean fills | 7,470 | 11,407 | 22,612 |
| **gross R/fill** | **+0.12522** | +0.07250 | +0.06639 |
| toll | 0.70314 | 0.65485 | 0.6232 |
| net | −0.57791 | −0.58234 | −0.55683 |
| gross / toll | **0.178** | 0.111 | 0.107 |
| windows positive | **3 / 3** | 4 / 4 | 8 / 8 |

Bootstrap gross **+0.12522, CI95 [+0.07806, +0.17611]**, p(≤0) = 0.000. Per window: +0.10151 /
+0.13469 / +0.13027 — the tightest three-window spread of any family in the table.

**This is now 15 consecutive windows positive across three independent harnesses.** It is the single
most durable positive result in the broad-family estate, and it is the strongest evidence anywhere
that these setups are not noise.

**And it still cannot be traded, for a measured reason.** Its toll is 0.70314 R — the highest of any
family — because its edge lives at a median stop of 2.8 bps against a ~2.7 bps spread. In price units
it captures **+0.4099 bps** (34× the family average, so the signal is genuinely there) against a
**2.6856 bps** toll: **6.55× short**. By risk-distance quintile [post-hoc]:

| quintile | median stop | n | gross | toll | net | gross/toll |
|---|---:|---:|---:|---:|---:|---:|
| Q1 | 1.39 bps | 1,494 | **+0.24687** | 1.06093 | −0.81406 | 0.233 |
| Q2 | 2.08 bps | 1,494 | +0.13160 | 0.66388 | −0.53228 | 0.198 |
| Q3 | 2.83 bps | 1,494 | +0.10362 | 0.53448 | −0.43086 | 0.194 |
| Q4 | 4.13 bps | 1,494 | +0.03817 | 0.50299 | −0.46483 | 0.076 |
| Q5 | 7.99 bps | 1,494 | +0.10586 | 0.75340 | −0.64754 | 0.141 |

The edge is largest exactly where the toll is largest. **What would have to be true**: the toll would
have to fall to 0.125 R/trade — an 82% cut — or the same edge would have to survive at a stop wide
enough to dilute the toll, which d3 already tested and refuted across 282 transplanted contracts.

### 2.1 Every family, sealed (clean fills, corrected contract, 2.0R)

| family | n | gross | toll | net | per-window gross (jun/aug/sep) |
|---|---:|---:|---:|---:|---|
| `structural_distance_extreme` | 7,470 | **+0.12522** | 0.70314 | −0.57791 | +0.102 / +0.135 / +0.130 |
| `current_fvg_fill` | 46,054 | **+0.03616** | 0.34878 | −0.31262 | +0.056 / +0.033 / +0.028 |
| `liquidity_sweep_reclaim` | 14,124 | +0.02293 | 0.34941 | −0.32648 | −0.018 / +0.049 / +0.021 |
| `current_ob_retest` | 5,651 | +0.01706 | 0.18795 | −0.17089 | +0.030 / −0.038 / +0.066 |
| `session_open_range_break` | 2,655 | +0.00384 | 0.09111 | −0.08727 | +0.066 / +0.005 / −0.034 |
| `cross_asset_lead_lag` | 6,777 | +0.00291 | 0.52665 | −0.52375 | +0.022 / −0.022 / +0.015 |
| `regime_transition_break` | 758 | −0.00251 | 0.06445 | −0.06696 | +0.012 / +0.007 / −0.020 |
| `displacement_continuation` | 12,660 | −0.02408 | 0.17185 | −0.19593 | +0.019 / −0.023 / −0.048 |
| `volatility_compression_expansion` | 1,653 | −0.05208 | 0.09785 | −0.14992 | +0.030 / −0.048 / −0.105 |

**Nine families, zero net-positive, and the two cheapest tolls (`regime_transition_break` 0.064,
`volatility_compression_expansion` 0.098) belong to the two families with negative gross.** That is
the coupling d7 named — affordability and edge sit on opposite ends of the same axis — reproduced on
unseen data.

---

## 3. H3 — the exit swap. **DOES NOT REPLICATE.**

Δnet from swapping the shipped `target_2.0R` for `stop_only_horizon`: **+0.01002**, CI95
[−0.01537, +0.03774], p(≤0) = 0.225. Positive in 3/3 windows (+0.01248 / +0.01822 / +0.00093) but
less than half its in-sample size (+0.02127, 4/4) and under a third of d2's published +0.03500.
Against the declared threshold (`≥ +0.02`) it **fails**.

The direction is right in every window and the magnitude is not. Read it as: the shipped exit is
mildly suboptimal, worth about one third of a percent of a risk unit, not the +0.035 lever d2 priced
— and nowhere near the 0.315 R gap it would need to close.

---

## 4. H4 — the fill-contract repair. **The repair is real; it repairs a WALKER, not the family.**

Two baselines, both declared before the read (§6 addendum), because the declared baseline turned out
not to contain the defect d5 repaired.

| | sealed | in-sample |
|---|---:|---:|
| **H4-a** vs `pbg_econ.walk_limit` range containment | **−0.00049**, CI95 [−0.00088, −0.00011] | −0.00048 |
| **H4-b** vs d5's one-sided `low ≤ e` baseline | **+0.02087**, CI95 [+0.01805, +0.02380], 3/3 | +0.03762, 4/4 |

Mechanism, measured: the d5-style walker fills **99.963%** of `gap_r < 0` rows (rows whose entry the
market had already left) and books **−0.03546 gross per fill**; the range-containment walker fills
**39.4%** of them and the side-aware contract **39.5%** — a 0.1 percentage-point difference, hence
the ≈0 in H4-a. `gap_r < 0` is **2.03%** of sealed emissions.

**So d5's +0.02995 is confirmed as a real defect of a specific walker convention, and is not a
property of the broad family.** Any lane using a `low ≤ e` fill test is overstating losses by about
2 R per hundred opportunities; any lane using range containment already has it right. That is a
method correction worth carrying, and it changes no economic verdict: at H4-b's own repaired
contract the family's net per opportunity is **−0.07801**, still deeply negative.

---

## 5. H5 — THE SURVIVING CANDIDATE. **FAILED.**

Tested on `september_2025` (22 days, the full `k = 1..14` grid, 18,626 `EARLY5` setup keys).

### H5a — the paired effect: **REPLICATES**, for the fifth independent window.

Paired Δnet (partial minus close, setups present in both arms): **+0.18063** on 11,750 pairs,
CI95 [+0.16242, +0.19786], p(≤0) = 0.000, mean earliness 7.65 minutes. Against +0.19562 (Jan),
+0.19302 (Feb), +0.23656 (Mar) and +0.1949 (this harness, 4 open windows). Close leg −0.27400,
partial leg −0.09338.

**The effect is one of the most reproducible numbers in this estate.** It is also not tradeable, and
the sealed window says so directly.

### H5b — the implementable book: **FAILS**, and by more than in sample.

Every setup the partial arm emits, phantom leg charged, deduplicated to one placement per
`(family, symbol, decision_day)` per the live `PlacementLedger` rule:

| book | n | gross | **net** |
|---|---:|---:|---:|
| close-only (incumbent) | 2,132 | −0.05776 | **−0.28041** |
| forming-bar (candidate) | 2,249 | −0.01664 | **−0.30551** |
| phantom leg (fires early, never confirms) | 5,666 | | **−0.95380** |

The candidate book is **−0.02510 R/trade worse** than the incumbent it was meant to improve, both are
negative, and it beat the incumbent in **0 of 1** sealed windows — against 0 of 4 open windows with
the same harness. The declared pass condition (`net > 0` **and** beats close in ≥2/3) fails on both
clauses.

**The mechanism d6 gave is confirmed on unseen data.** The phantom leg is **32.5%** of the partial
arm's setups (5,666 of 17,416 = 11,750 paired + 5,666 phantom) and books **−0.95380 R each** — against
PB's January figure of 31.2% at −0.93653, i.e. the adverse-selection rate is a stable property of the
generator, not a January accident. There is no version of "decide earlier" that gets
the +0.18 without also getting the phantom leg, because the pairing that defines the +0.18 is
knowable only at the close — fifteen minutes after the decision it is supposed to inform.

**Stated plainly: the wave's one surviving candidate failed its sealed test.**

---

## 6. H6 — is the direction call better than its own mirror? **ZERO, leaning positive — and it settles f2 vs d7.**

On at-market rows filled inside the decision bar (n = 41,013), where the market and honest-limit
contracts are identical by construction so no fill selection exists:

| window | n | real gross | mirror gross | signal | toll |
|---|---:|---:|---:|---:|---:|
| `june_2025` | 9,486 | +0.02280 | −0.00297 | **+0.02577** | 0.28793 |
| `august_2025` | 15,911 | +0.02175 | −0.00557 | **+0.02732** | 0.36345 |
| `september_2025` | 15,616 | +0.01286 | −0.00644 | **+0.01929** | 0.37855 |
| **pooled** | **41,013** | **+0.01861** | **−0.00530** | **+0.02391** | **0.35173** |

Bootstrap **CI95 [−0.00313, +0.05122]**, p(≤0) = 0.040. The point estimate clears the declared
+0.02 bar; the CI does not exclude zero, so the declared verdict is **DIRECTION ZERO**.

**But the sign question is answered, and it was the sharpest open disagreement in the wave.** f2
measured the paired directional signal at **+0.02877**; d7 measured **−0.04230** with a CI that
excluded zero and concluded the family is "significantly worse than its own mirror". On three unseen
months the signal is **+0.02391, positive in 3 of 3 windows**, and the mirror books **negative**
(−0.00530). **d7's inversion does not replicate. f2's sign does.** Nothing here is tradeable — the
direction call is worth 6.8% of the toll charged on the identical rows — but "the setups are
systematically wrong-way" is now refuted out of sample, and no inversion strategy should be built on
it.

---

## 7. What this settles for the owner's question

**It is the SIGNAL, and the mechanism is a ratio, not an absence.**

1. **There is a signal.** Gross is positive out of sample at p(≤0) = 0.001, in 3 of 3 unseen windows,
   and the direction call beats its own mirror in 3 of 3. One family (`structural_distance_extreme`)
   is positive in 15 consecutive windows across three harnesses and got *stronger* on the held-out
   set. The broad family is not noise. Anyone who says "the setups don't work" is overstating the
   evidence.
2. **The signal is two orders of magnitude too small to pay for itself, in the one unit that cannot
   be gamed.** In price terms the family captures **0.0119 bps per trade** and pays **3.0159 bps**.
   The best family captures 0.4099 bps and pays 2.6856. The deficit is not a few percent — it is
   **253×** for the family and **6.55×** for its best member.
3. **The usage is not the problem, and the sealed set tightens that.** The two biggest usage repairs
   the wave found were tested here: the exit swap delivered under half its in-sample value and lost
   significance (H3), and the fill repair turned out to be a walker convention rather than a
   property of the system (H4). The one usage lever with a large effect (H5a, +0.18) is
   unimplementable for a reason that is now confirmed on unseen data. **Fixing usage cannot close a
   253× gap; the largest usage lever ever measured on this family was worth 0.035 R against a 0.315 R
   deficit.**
4. **What would have to be true, priced on the sealed rows.** The win rate would have to rise
   **13.32 percentage points** (39.34% → 52.66%); or the toll would have to fall **92.1%**
   (0.34262 → 0.02718); or price capture would have to rise **253×** in price terms. One correction
   to d7 here: because the sealed gross is *positive*, a free broker is no longer arithmetically
   impossible the way d7's negative-gross clean roster made it — it would leave the family at
   **+0.02718 R/trade**, a real but economically trivial book. The lever is not unavailable in
   principle; it is unavailable in practice, since the measured toll floor across every instrument
   and family in this estate is ~3 bps and the family captures 0.0119.

**Why the family is finished, in one sentence the owner asked for**: the setups carry real
directional information of about a hundredth of a basis point per trade, and the generator expresses
it through stops of 8 bps against a ~3 bps round-trip toll — so the edge is real, the edge is tiny,
and **the toll charged on the identical rows is 12.6× the entire edge in R and 253× in price**.

**What would reopen it.** Not a better filter, not a better exit, not an earlier decision — all three
were tested here and none moved the ratio. Only a generator whose setups capture *whole basis points*
rather than hundredths: either the same predicates expressed at a horizon and stop width where the
captured move is 30–100× larger (d3 tested 282 such contracts and found none, but never on the
2014–2026 deep archive), or a different predicate family entirely. The measurement that would settle
the reopening is the price-unit capture curve versus holding horizon on the untouched
`deep_universe_h4d1_2014_2026` archive — d8x's finding that it has never been opened stands.

---

## 8. Spend record

**These three windows are now SPENT.** They were spent on the seven hypotheses above and on nothing
else. No result in this receipt was chosen after seeing a number; the declaration file's git-visible
content preceded the first sealed read, and its two addenda (§6, §6.1) were written before any
sealed outcome existed and changed no threshold.

| window | spent on | days read | emissions read |
|---|---|---:|---:|
| `june_2025` | H1, H2, H3, H4, H6 (close-only grid) | 13 of 21 | 134,726 |
| `august_2025` | H1, H2, H3, H4, H6 (close-only grid) | 21 | 168,039 |
| `september_2025` | H1, H2, H3, H4, H6 **and H5** (full `k=1..14` grid) | 22 | 167,707 |

Note for any future session: the *pool artifacts* (`LP_*_S0R0_POOL_V1.jsonl.gz`) were never opened —
this lane worked from a regenerated roster, which is the better object. That does **not** leave the
windows unspent. The economics of these three months have now been read; treat them as in-sample from
this point on, exactly as January and February are.

## 9. Artifacts

* `p2_PREDECLARATION.md` — the declaration of record, with both addenda.
* `p2_RESULT.json` / `P2_SEALED_V1.json` — every sealed number, per window and pooled.
* `P2_SEALED_SEP_H5.json` — H5 on `september_2025` alone.
* `P2_INSAMPLE_4WIN.json` — the same harness on Nov/Dec 2025 + Jan/Apr 2026 (the comparator).
* `p2_VALIDATE_JAN.json` — the pre-seal harness validation against PB's published January figures.
* `P2_MECH.txt` — the post-hoc descriptive tables (risk-distance deciles, quintiles, price units).
* `p2_walk.py`, `p2_analyse.py`, `p2_print.py` — the harness. Generation used the unmodified
  `pbg_run.py` at `--min-rr 1.5`.
