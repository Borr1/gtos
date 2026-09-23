# d6 — THE SURVIVING CANDIDATE, GATED

Lane d6, wave 19. Everything below is measured over the **whole** population of three
months on this machine — **5,758,404 generator emissions collapsed to 595,801 setups**
across 24 instruments, 10 origin families and 63 trading days (January, February, March
2026). Nothing is sampled anywhere. Population is the **roster** (Session PB's reproduction
of the sealed arms' own candidate roster at 99.82 %), never the 27,658-row counterfactual
pool. Generator admission is `risk.min_rr = 1.5`. Cost is the h1 four-term hour-aware
broker-true model.

**Machine-readable:** `D6_MAIN_V1.json` (per-month arms + the 127-subset sweep),
`D6_DEDUP_V1.json` (live placement contract), `D6_GATE_V1.json` (the seven conditions),
`D6_FEAT_V1.json` (1,414-cell separator search), `D6_MECH_V1.json` (mechanism + ablation),
`D6_CANCEL_V1.json` (the obvious repair, priced), `D6_HORIZON_V1.json` (truncation
answered), `D6_FINAL_V1.json` (the decision table).
**Code:** `d6_build.py`, `d6_lib.py`, `d6_analyse.py`, `d6_dedup.py`, `d6_feat.py`,
`d6_gate.py`, `d6_mech.py`, `d6_cancel.py`, `d6_horizon.py`, `d6_final.py`.
Per-trade dataset: `/tmp/d6/trades/{202601,202602,202603}.jsonl.gz` (47 MB, regenerable in
45 s/month from `/tmp/pbg_full_{jan,feb,mar}` with `d6_build.py`).

---

## 0. THE ANSWER

**The lever is real, it is the largest and most stable usage effect this wave has produced,
and it cannot be harvested — because the population it lives on is defined by an event that
happens AFTER the decision, and by the time that event is observable the money is already
gone.**

Six numbers carry the verdict:

| | R/trade | implementable |
|---|---:|---|
| incumbent close-only book, live placement contract | **−0.15161** | yes |
| **forming-bar book, live placement contract** | **−0.17778** | yes — and **worse** than doing nothing |
| forming-bar book, PB's population | −0.24814 | yes |
| the obvious repair (flatten at the bar close if the setup does not re-emit) | −0.34314 | yes |
| a physically impossible **free** cancel | −0.15287 | no (and **loses more total R** than the incumbent: −7,406 vs −6,156) |
| **the paired arm — the +0.196 headline** | **+0.03700** | **NO. Its population is "the setups that also emitted at the M15 close", which is not knowable at T+k.** |

The paired arm passes all seven of the estate's evaluable gate conditions on the estate's
own fold structure: OOS **+0.054356 R/trade / +28.26 R/day, 5 of 5 positive folds**,
leave-best-fold retention **0.754**, day-blocked p at the bootstrap floor (**5.0e-5**,
block 4). Scored over all 63 days instead — fold 0 included — it is +0.03700 and p 0.00540. **The gate has no condition
that tests whether a population is knowable at decision time**, which is why it says yes to
a thing that cannot be traded. That is the single most transferable finding in this lane.

**The mechanism, in one sentence:** a setup that fires inside an M15 bar and does not
survive to that bar's close has *already* moved **−0.55503 R against you by the time the
bar closes** — 98.0 % of its entire 120-bar gross loss is realised inside those 1–14
minutes — so the information that would let you avoid it arrives after the loss is booked.

**What would have to be true**, quantified: a separator would have to reach **95.90 %
precision** on the confirming leg while leaving both legs' economics unchanged. Measured
precision is **67.8 %**. The best separator found anywhere — the forming bar's own
displacement, AUC **0.6071**, Cohen's d **0.2772** (1.82× the estate's published d = 0.152
ceiling over 28 pre-decision fields) — buys precision at **−0.00469 R of confirmed-leg edge
per percentage point**, so the confirmed leg's *entire* +0.03700 edge is exhausted at
**75.69 %** precision, twenty points short of the requirement. **The feasible set is empty,
and it is empty for a measured reason, not for want of looking.**

**verdict_axis: BOTH, and the split is measurable.** The usage half is real (+0.14284
R/trade at matched geometry, 63 of 63 trading days). The signal half is what closes it: the
generator's early emissions are, on the 32.2 % that do not confirm, an *anti*-signal worth
−0.56652 R gross, and the incumbent close-only book those emissions are measured against is
itself −0.15161 R/trade before any of this.

---

## 1. THE FIVE FAMILIES, AND HOW THEY WERE SELECTED

Named exactly, from `pbg_analyze.py:44-50`:

```python
EARLY5 = ("displacement_continuation", "liquidity_sweep_reclaim",
          "session_open_range_break", "regime_transition_break",
          "volatility_compression_expansion")
```

**They were selected on their own outcome, and PB says so in the code comment**
(`pbg_analyze.py:43-45`): *"the five at-market families whose PAIRED partial-vs-close delta
is positive in January (measured, `PBG_JAN_V1 -> by_family`)"*. That is a **sign filter over
the seven at-market families, fitted on January's own realised delta** — selection, and it
must be priced. Three measurements price it:

**(a) The selection is not fragile.** Every one of the seven families keeps the same sign in
all three months, and the magnitudes barely move (paired delta at matched geometry `d₀`,
2R, net, broker-true):

| family | 202601 | 202602 | 202603 | in EARLY5 |
|---|---:|---:|---:|:--:|
| `liquidity_sweep_reclaim` | **+0.2637** (n 4,923) | **+0.2408** (n 4,848) | **+0.2582** (n 5,192) | ✔ |
| `session_open_range_break` | +0.1305 (975) | +0.1023 (932) | +0.1815 (1,008) | ✔ |
| `regime_transition_break` | +0.0887 (265) | +0.0773 (231) | +0.0693 (253) | ✔ |
| `volatility_compression_expansion` | +0.0530 (588) | +0.0232 (534) | +0.0296 (616) | ✔ |
| `displacement_continuation` | +0.0518 (4,345) | +0.0176 (3,813) | +0.0174 (4,386) | ✔ |
| `cross_asset_lead_lag` | −0.1048 (2,591) | −0.0908 (2,427) | −0.0903 (2,630) | ✗ |
| `structural_distance_extreme` | −0.5743 (2,706) | −0.5816 (2,483) | −0.5927 (2,810) | ✗ |

**7 of 7 signs reproduce, 3 of 3 months.** So the selection is a real per-family property,
not an in-sample fluke — which makes the *lever* credible and changes nothing about whether
it can be traded.

**(b) EARLY5 is not the in-sample argmax, which is the honest reading of a sign filter.**
Over all **127 non-empty subsets** of the seven at-market families, pooled on 3 months,
EARLY5 ranks **16th of 127** by paired delta and **16th of 127** by implementable book net.
The argmax by delta is `liquidity_sweep_reclaim` **alone** (+0.25436); the argmax by book is
`regime_transition_break` alone (−0.04134).

**(c) The selection carries more of the headline than the timing does.** At matched geometry
the same lever measured over **all seven** at-market families is **−0.01425** (p(≤0) 0.9962,
26/63 days). The five-family restriction is therefore worth **+0.157 R/trade** — larger than
the +0.14284 timing effect it is applied to. `structural_distance_extreme` alone loses
0.574 R/trade at matched geometry on **16.5 %** of the at-market paired rows (2,706 of
16,393 in January).

**And the part that decides it: not one of the 127 subsets produces a positive implementable
book, in either arm.** Best partial-bar book over all 127: **−0.04134**. Best close-only
book over all 127: **−0.03190**. Zero positive cells out of 254.

---

## 2. A CORRECTION TO PB'S PUBLISHED BOOK FIGURES — both books double-count, and it goes the wrong way

`pbg_analyze.py:351-352`:

```python
r["BOOK_close_only"] = summarise(close_arm + closeonly_only, "BOOK_close")
r["BOOK_partial"]    = summarise(part_arm  + phantom,        "BOOK_partial")
```

`close_arm` is **already** every setup carrying a close row (paired + close-only-only), and
`part_arm` is **already** every setup carrying a partial row (paired + phantom). So
`BOOK_close_only` counts the close-only-only setups **twice**, and `BOOK_partial` counts the
**phantom leg twice** — the −0.94 R/trade leg — while omitting the close-only-only setups a
live book would still take at the close. Verified arithmetically on all six published cells:

| month · cohort | PB n | PB net | correct n | correct net |
|---|---:|---:|---:|---:|
| 202601 EARLY5 close | 13,148 = 11,096 + 2×1,026 | −0.19746 | 12,122 | **−0.20040** |
| 202601 EARLY5 partial | 21,183 ≈ 11,096 + 2×5,040 | −0.45006 | 17,169 | **−0.29009** |
| 202601 AT_MARKET close | 19,051 = 16,393 + 2×1,329 | −0.29148 | 17,722 | **−0.29743** |
| 202601 AT_MARKET partial | 41,837 ≈ 16,393 + 2×12,714 | −0.53855 | 30,452 | **−0.48037** |
| 202602 AT_MARKET partial | 39,228 | −0.44843 | 28,485 | **−0.40148** |
| 202603 AT_MARKET partial | 43,082 | −0.35933 | 31,242 | **−0.31977** |

Reproduction of the defect, exactly: `(11,096×(−0.00826) + 2×5,040×(−0.93653)) / 21,176 =
−0.4501`, PB's published −0.45006.

**The correction makes the candidate look BETTER**, which is the honest direction to correct
in. PB's headline *"the January book goes −0.29148 → −0.53855"* is really **−0.29743 →
−0.48037**: the deterioration is 0.183 R/trade, not 0.247 — 26 % smaller. **Every sign and
every verdict is unchanged.** Everything else in `PARTIAL_BAR_GENERATOR_RESULT.md`
reproduces to 4–5 decimals against my independent rebuild (paired close −0.20388 vs
−0.20388; paired partial −0.00826 vs −0.00826; Δ net +0.19562 vs +0.19562; Δ at d₀ +0.15368
vs +0.15368; February +0.19302 vs +0.1930; March +0.23656 vs +0.2366).

---

## 3. THE ARMS, POOLED OVER THREE MONTHS

2R target, 120 M1 bars, conservative tie, h1 four-term hour-aware broker-true cost charged
once in R of each arm's own risk distance.

| arm | n | gross R | cost R | **net R** | total R | trunc | days + | p(≤0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| EARLY5 close book (PB population) | 35,917 | +0.00995 | 0.18134 | **−0.17138** | −6,156 | 0.394 | 3/63 | 1.0000 |
| EARLY5 partial book (PB population) | 51,518 | +0.01578 | 0.26392 | **−0.24814** | −12,783 | 0.274 | 0/63 | 1.0000 |
| EARLY5 close book, **live placement** | 6,130 | −0.01056 | 0.14105 | **−0.15161** | −929 | 0.539 | 9/63 | 1.0000 |
| EARLY5 partial book, **live placement** | 6,518 | +0.00586 | 0.18365 | **−0.17778** | −1,159 | 0.483 | 5/63 | 1.0000 |
| ALL-7 close book | 52,358 | +0.02584 | 0.27951 | −0.25366 | — | 0.285 | 2/63 | 1.0000 |
| ALL-7 partial book | 90,179 | +0.03622 | 0.43603 | −0.39981 | — | 0.159 | 0/63 | 1.0000 |
| **paired close (counterfactual)** | 32,909 | +0.00752 | 0.17957 | −0.17205 | −5,662 | 0.394 | 4/63 | 1.0000 |
| **paired partial (counterfactual)** | 32,909 | +0.28993 | 0.25293 | **+0.03700** | +1,218 | 0.310 | **41/63** | **0.0054** |
| paired partial, **live placement** (counterfactual) | 5,998 | +0.20824 | 0.18940 | **+0.01884** | +113 | 0.480 | 39/63 | **0.1844** |
| phantom leg | 15,601 | −0.56652 | 0.29930 | **−0.86582** | — | 0.174 | 0/63 | 1.0000 |

**Paired deltas** (same setups, same days, paired day-block bootstrap, 4,000 draws):

| | value | CI95 | p(≤0) | days + |
|---|---:|---|---:|---:|
| Δ net, EARLY5 | **+0.20905** | [+0.19648, +0.22199] | 0.0000 | **63/63** |
| Δ net at matched geometry d₀ | **+0.14284** | [+0.13384, +0.15160] | 0.0000 | **63/63** |
| Δ net, all seven at-market families | −0.04689 | [−0.06305, −0.03083] | 1.0000 | 15/63 |
| Δ net at d₀, all seven | −0.01425 | [−0.02430, −0.00370] | 0.9962 | 26/63 |

**The live placement contract matters and had never been applied.** PB's setup key is
`(symbol, family, side, BAR)`, so its book takes ~5.4 entries per (family, symbol, day). The
live rule is `PlacementLedger.already_placed_today(sleeve, symbol, decision_day)`
(`src/components/ultimate_book/placement_ledger.py:166`, enforced at
`book_owner.py:2056`) — **one placement per (sleeve, symbol, decision_day), first qualifying
moment wins.** Under it the population falls 35,917 → 6,130 (close) and 51,518 → 6,518
(partial); the close book improves to −0.15161 and the partial book to −0.17778.
**The ordering does not change: the forming-bar decision is worse under every placement
contract tested.** Phantom share of the partial book is invariant to the dedup (0.3216 →
0.3238 → 0.3247).

---

## 4. THE GATE — the estate's own machinery, on this candidate

`d6_gate.py` uses `walkforward.stats.day_block_bootstrap_p`, `.block_length_auto`,
`.benjamini_hochberg` and `walkforward.spec.DEFAULT_SPEC` directly; it implements
`gate.py`'s seven conditions on this candidate's own trade series because `run_gate`
consumes a sleeve panel this candidate is not a member of. Six calendar folds, fold 0
consumed as train and never scored. `fidelity` is **NOT_EVALUABLE by construction** (no
fidelity-register entry: this is a research contract over the broad-origin generator, not a
registry sleeve) — the same status the estate gives CP's and CQ's factory candidates.
`coverage` is **MEASURED at 1.00** (0 unpriced trades).

| arm | n | R/trade | p | conditions FAILED | pos folds | retention |
|---|---:|---:|---:|---|---:|---:|
| EARLY5 partial book (PB pop) | 51,518 | −0.24814 | 1.0000 | expectancy, stability, robustness, significance | 0/5 | n/a |
| EARLY5 partial book (live) | 6,518 | −0.17778 | 1.0000 | expectancy, stability, robustness, significance | 0/5 | n/a |
| EARLY5 close book (PB pop) | 35,917 | −0.17138 | 1.0000 | expectancy, stability, robustness, significance | 0/5 | n/a |
| EARLY5 close book (live) | 6,130 | −0.15161 | 1.0000 | expectancy, stability, robustness, significance | 0/5 | n/a |
| ALL-7 partial book | 90,179 | −0.39981 | 1.0000 | expectancy, stability, robustness, significance | 0/5 | n/a |
| best single family (`regime_transition_break`) | 1,364 | −0.04134 | 0.8378 | expectancy, stability, robustness, significance | 1/5 | n/a |
| same, live placement | 940 | −0.01702 | 0.4892 | robustness, significance | 3/5 | −30.47 |
| **paired partial (COUNTERFACTUAL)** | 32,909 | **+0.05436** OOS † | **5.0e-5** | **none** | **5/5** | **0.754** |

† the gate scores OOS folds 1-5 only (fold 0 is the train block and is never scored), so its
R/trade is +0.054356 against the all-63-day +0.03700 used everywhere else in this receipt;
January's opening block is the difference. Fold R/day: 17.15 / 18.30 / 20.73 / 58.14 / 29.02.
p = 5.0e-5 is the add-one floor of the 20,000-draw bootstrap.

**Multiplicity, at the ratified rule.** `CANDIDATE_BOOK_V1` at the `CANDIDATE_FAMILY_V27`
tip is **59 declared / 57 looks**; with this candidate m = **60**, `basis: all_declared`,
sealed **α = 0.10**, so the BH rank-1 bar is **0.0016667** and Bonferroni is **0.000833**.

| cut | arm | p | q at m=60 | verdict at the ratified rule |
|---|---|---:|---:|---|
| 3 months | paired partial (PB pop) | 0.00540 | 0.324 | **REJECT** |
| 3 months | paired partial (live placement) | 0.18439 | 1.000 | **REJECT** — fails raw α before any bill |
| Feb+Mar only | paired partial (PB pop) | ≤ 5.0e-5 † | ≤ 0.003 | would pass — see † and §5 |
| Feb+Mar only | paired partial (live placement) | 0.00315 | 0.189 | **REJECT** |
| any cut | **every implementable arm** | 1.0000 | 1.000 | **REJECT on `expectancy` first** |

† 5.0e-5 is the add-one floor of a 20,000-draw bootstrap, i.e. *below the test's
resolution*. The lane's own honest look count is **≈1,867** (127 subsets × 3 arms; 126
single-rule + 1,288 pair-rule cells; 20 decile cells; 16 gate arms; 16 horizon cells; 4
cancel variants; 16 ablation cells). Billed at m = 59 + 1,867 = 1,926 the BH rank-1 bar is
**5.19e-5** — the observed p sits **exactly on it**, so the comparison is not resolvable
without ~10⁶ bootstrap draws. **Reported as unresolved rather than as a pass.** It is moot
regardless: the arm is not implementable.

**Strict out-of-sample cut** — January, the month that *chose* the five families, removed
entirely (`D6_FINAL_V1.json → cuts.OOS_EXCLUDING_THE_SELECTION_MONTH`, 42 trading days):

| arm | n | net R | total R | days + | p |
|---|---:|---:|---:|---:|---:|
| close book, live placement | 4,072 | −0.14447 | −588 | 6/42 | 1.0000 |
| partial book, live placement | 4,342 | −0.15543 | −675 | 3/42 | 1.0000 |
| paired partial (counterfactual) | 21,813 | +0.06002 | +1,309 | 31/42 | ≤5.0e-5 |
| paired partial, live placement (counterfactual) | 3,989 | +0.05679 | +227 | 31/42 | 0.00315 |

The candidate's OOS behaviour is *better* than its in-sample behaviour, on both the
counterfactual and the implementable side. **The problem was never overfitting.**

---

## 5. THE MECHANISM — precision IS edge, on a second and continuous instrument

x3 and PB established the cancellation on **one** axis (the minute floor). This lane
re-establishes it on the strongest separator that exists, measured over the whole
population, and adds the reason.

**Separability of paired vs phantom, pooled, 32,909 vs 15,601 rows.** Every feature is
computed from prints **at or before** the decision instant:

| feature | mean (paired) | mean (phantom) | Cohen's d | AUC |
|---|---:|---:|---:|---:|
| `disp_r` — how far the forming bar has already run **in the trade's direction**, in R | +0.0475 | −0.1965 | **+0.2772** | **0.6071** |
| `k` — minute of the bar | 7.441 | 6.218 | +0.2994 | 0.5856 |
| `pos` — position of the entry in the forming bar's range | 0.7116 | 0.6297 | +0.2661 | 0.5781 |
| `mae_r` — adverse excursion already taken inside the bar | 0.5817 | 0.7514 | −0.2180 | 0.4136 |
| `risk_bps` — the arm's own stop width | 27.55 | 22.32 | +0.1101 | 0.5589 |
| `rng_r` — forming-bar range in R | 1.118 | 1.194 | −0.0986 | 0.4824 |
| `hr` — broker hour | 11.05 | 11.32 | −0.0458 | 0.4870 |

**The separator EXISTS.** d = 0.2772 / AUC 0.6071 is 1.82× the estate's published pre-decision
ceiling (max d = 0.152 over 28 fields) and comparable to the only strong observable the wave
found all week (d = 0.3348 at T+60 s).

**And it does not help, and here is why.** Displacement deciles (equal-n, 4,851 each):

| decile | `disp_r` range | precision (paired share) | paired-leg net R | phantom-leg net R | combined book |
|---:|---|---:|---:|---:|---:|
| 1 | −8.28 … −1.18 | 0.604 | **+0.0820** | −1.1911 | −0.4221 |
| 2 | −1.18 … −0.60 | 0.611 | +0.1049 | −1.1338 | −0.3764 |
| 3 | −0.60 … −0.24 | 0.617 | +0.0940 | −1.1075 | −0.3660 |
| 4 | −0.24 … +0.02 | 0.602 | +0.0874 | −1.0544 | −0.3666 |
| 5 | +0.02 … +0.18 | 0.634 | **+0.1109** | −0.7573 | −0.2066 |
| 6 | +0.18 … +0.36 | 0.660 | +0.0291 | −0.5757 | −0.1765 |
| 7 | +0.36 … +0.56 | 0.615 | +0.0195 | **−0.4948** | −0.1787 |
| 8 | +0.56 … +0.72 | 0.725 | −0.0067 | −0.5497 | −0.1559 |
| 9 | +0.72 … +0.81 | **0.841** | −0.0262 | −0.7069 | −0.1346 |
| 10 | +0.81 … +1.28 | **0.874** | **−0.0549** | −0.8102 | −0.1500 |

**Precision rises 0.604 → 0.874 and the confirmed leg's own edge falls +0.0820 → −0.0549 in
lockstep. The combined book is negative in all ten deciles.** Raising a displacement floor
(cumulative, `D6_MECH_V1.json → cumulative_displacement_floor`) reproduces it: precision
0.678 → 0.874, confirmed-leg edge +0.0370 → −0.0549, book never leaves −0.130 … −0.253.

**The causal reason is now explicit and it is not a coincidence:** a setup confirms at the
M15 close *precisely because* the bar has already run in the trade's direction — and at a
market entry you have already **paid** that move. Selecting for confirmation is selecting
for a worse entry. That is why precision and edge are the same variable with opposite signs,
and why this generalises off the minute axis.

**The search was exhaustive within its feature set: 126 single-threshold cells and 1,288
two-feature conjunctions — 1,414 rules — and NOT ONE is net-positive, not even in sample.**
Best single rule `risk_bps ≥ 46.21`: train −0.09653, test −0.07760. Best pair
`hr ≥ 17 AND mae_r ≤ 0.0531`: train −0.04867, test −0.11510.

**The arithmetic bound.** book(p) = p·paired + (1−p)·phantom = 0 requires
p* = |−0.86582| / (0.86582 + 0.03700) = **0.95900**. Measured p = **0.678**. The measured
price of precision along the only axis that supplies it is **−0.46888 R per unit** (−0.00469
per pp), so the confirmed leg's entire +0.03700 edge is gone at p = **0.7569** — **20.2
points short**. A separator that works must therefore be **orthogonal to displacement**, and
none of the seven features available inside the bar is.

---

## 6. THE OBVIOUS REPAIR, PRICED — and why it fails for a new reason

The natural fix: enter on the forming bar, and **flatten at the bar close if the generator
does not re-emit the setup**. The wait is 1–14 minutes and the rule is fully implementable.

| leg / book | n | net R | days + | CI95 |
|---|---:|---:|---:|---|
| paired leg, held (unchanged) | 32,909 | +0.03700 | 41/63 | [+0.0123, +0.0618] |
| **phantom leg GROSS at the bar close** | 15,537 | **−0.55503** | 0/63 | [−0.5640, −0.5453] |
| phantom leg net at the bar close, double toll | 15,537 | −1.14831 | 0/63 | [−1.1836, −1.1117] |
| **BOOK: cancel at the close, double toll** | 48,446 | **−0.34314** | 0/63 | [−0.3670, −0.3184] |
| BOOK: cancel at the close, single toll | 48,446 | −0.24800 | 0/63 | [−0.2679, −0.2277] |
| BOOK: cancel one bar later, double toll | 48,381 | −0.25802 | 0/63 | [−0.2843, −0.2319] |
| **BOOK: FREE cancel (impossible upper bound)** | 48,446 | **−0.15287** | 1/63 | [−0.1690, −0.1362] |

**The new number is −0.55503.** The phantom leg's gross loss at the bar close is **98.0 % of
its entire 120-bar gross loss (−0.56652)**. The adverse selection is not a slow bleed you
can cut short — **it is complete within minutes, before the confirmation signal exists.**
Cancelling buys nothing because there is nothing left to save.

And the impossible bound is the closing argument: even at a **zero-cost, zero-slippage,
instantaneous** cancel the book is −0.15287 R/trade on 48,446 trades = **−7,406 R total,
against the incumbent close-only book's −6,156 R on 35,917 trades.** Trading more, earlier,
for free, still loses more money.

---

## 7. ABLATION — which component carries it

All cells priced on the **same rows** (paired setups only), so nothing is summed across
populations. `Δ total` is the full paired delta; `Δ at d₀` holds the risk distance at the
close-only arm's value, isolating timing from stop geometry.

| cohort | n paired | Δ total (2R) | Δ at d₀ (2R) | Δ total (1.5R) | Δ at d₀ (1.5R) |
|---|---:|---:|---:|---:|---:|
| **EARLY5** | 32,909 | **+0.20905** | **+0.14284** | +0.19958 | +0.15178 |
| all 7 at-market | 48,556 | −0.04689 | −0.01425 | −0.02124 | +0.01663 |
| `liquidity_sweep_reclaim` alone | 14,963 | **+0.32971** | **+0.25436** | +0.30850 | +0.26940 |
| EARLY5 minus `liquidity_sweep_reclaim` | 17,946 | +0.10846 | +0.04986 | +0.10876 | +0.05371 |
| **POI (resting-limit contract)** | 215,860 | **+0.01457** | **+0.01452** | — | — |

**Decomposition of the +0.20905:**

| component | value | share |
|---|---:|---:|
| **timing** — the same setup decided 1–14 min earlier, geometry held | **+0.14284** | **68.3 %** |
| **geometry** — the forming bar's unfinished range gives a tighter ATR stop | +0.06621 | 31.7 % |

**And the family restriction is worth more than either:** the same lever over all seven
at-market families is −0.01425, so restricting to the five is worth **+0.157** — which is
the ablation's real headline. Within the five, `liquidity_sweep_reclaim` (45.5 % of rows)
carries +0.25436 of it; the other four together carry +0.04986.

**Contract axis:** on the three POI families (resting limit orders) the same timing change
is worth **+0.01457** with **no** geometry component (+0.01452 at d₀) — an order of
magnitude smaller, and 63/63 days. The lever is a property of the **at-market** contract.

**Target axis:** 1.5R and 2.0R agree to within 0.01 R on every cell, and the generator's own
emitted `take_profit_1` gives close −0.17682 / partial −0.25883 — same signs, same ordering.
**No conclusion here depends on the synthetic 2R target.**

---

## 8. TRUNCATION AT THE WINNER — disclosed *and* answered

The estate requires the maxbars share be published because an earlier frontier carried
20.6 % unreported. At the winner (paired partial, 2R, 120 M1 bars):

**truncation share = 0.3096**; exit mix `stop 0.3938 / target 0.2966 / path_end 0.3096`.
At 1.5R: 0.2531 (`stop 0.3532 / target 0.3938`). The incumbent close arm truncates **more**:
0.3972 (`stop 0.4338 / target 0.1691`).

**Answered rather than disclosed** — the horizon was swept 120 → 960 M1 bars (2 h → 16 h):

| horizon (M1) | paired close | **paired partial** | phantom | implementable book | trunc (winner) |
|---:|---:|---:|---:|---:|---:|
| 120 | −0.17205 | **+0.03700** | −0.86582 | −0.25335 | 0.310 |
| 240 | −0.17436 | +0.03986 | −0.86773 | −0.25202 | 0.198 |
| 480 | −0.17484 | +0.03622 | −0.86751 | −0.25442 | 0.110 |
| 960 | −0.17367 | +0.03696 | −0.86916 | −0.25445 | 0.057 |

Truncation falls 5.4× and **no number moves by more than 0.005 R.** The 31 % truncation
share is real and it is economically inert here.

---

## 9. THE EXACT LIVE CONTRACT IT WOULD IMPLY

Stated precisely enough to implement, so the estate has it on the record. **It books
−0.17778 R/trade and it is not recommended.**

```
DECISION CLOCK   every minute T+k, k = 1..14, inside the M15 bar opening at T
                 (plus the existing close decision at k = 15)
GENERATOR        src.components.broader_origin_generators
                   .generate_live_broader_origin_candidates  — UNMODIFIED
INPUT raw_data   candles["M15"] = the 671 CLOSED bars ending at T,
                   + one forming bar synthesised from that bar's own M1 prints
                     over [T, T+k)
                 candle_open_utc  = T
                 candle_close_utc = T+k
                 selected_closed_bar_open_utc = T
                 timestamp_utc    = T+k
                 (this is the contract `_selected_closed_bar_open`,
                  broader_origin_generators.py:2179-2200, already honours —
                  NO edit to any R2-bound file is required)
MARKET STATE     compute_market_state as of T — CLOSED BARS ONLY.
                 Nothing from inside the forming bar ever enters the MSO.
FAMILIES         displacement_continuation, liquidity_sweep_reclaim,
                 session_open_range_break, regime_transition_break,
                 volatility_compression_expansion       (the other five: OFF)
ADMISSION        risk.min_rr = 1.5
ENTRY            market, at the decision instant; fill = last M1 close before it
STOP             the generator's own, from the PARTIAL bar's ATR
TARGET           2.0R  (1.5R and the generator's own take_profit_1 agree in sign)
HORIZON          any: 120..960 M1 bars measured invariant to within 0.005 R
PLACEMENT        one per (family, symbol, decision_day), first qualifying moment
                 wins — PlacementLedger.already_placed_today,
                 placement_ledger.py:166 / book_owner.py:2056
COST             h1 four-term hour-aware broker-true
MEASURED         net -0.17778 R/trade, n = 6,518, 5 of 63 days positive,
                 against the SAME contract at the M15 close: -0.15161, 9 of 63.
```

**The one variant worth naming for the record**, because it is the only one that is both
implementable and better than doing nothing on a *per-trade* basis, and it still loses
money: `regime_transition_break` alone, forming bar, live placement — **−0.01702 R/trade on
940 trades, 3/5 positive folds, p 0.4892, fails robustness (retention −30.47).** It is one
family, 15 trades a day, and its confidence interval contains −0.05.

---

## 10. WHAT WOULD HAVE TO BE TRUE

1. **A separator reaching 95.90 % precision that is orthogonal to displacement.** The
   coupling is measured at −0.00469 R per pp of precision; the confirmed leg's entire edge is
   spent at 75.69 %. Anything that buys precision *through* how far the bar has already run
   is self-defeating by construction.
2. **Or a phantom leg whose loss is not already complete at the bar close.** It is: −0.55503
   of −0.56652 gross, 98.0 %, inside 1–14 minutes.
3. **Or an incumbent worth improving.** The close-only book these five families run is
   −0.15161 R/trade under the live placement contract, 9 of 63 days positive. Applying the
   full +0.14284 timing lever *for free and without a phantom leg* lands at −0.029; the
   observed counterfactual ceiling, geometry included, is **+0.03700 R/trade at 522 trades a
   day** — a trade rate no account can carry — and **+0.01884 at the 95 trades/day the live
   placement contract permits, where it is no longer significant (p 0.1844).**

**The candidate is not killed by overfitting, by cost, by the horizon, by the target, by the
2R synthetic exit, or by multiplicity. It is killed by the fact that the information which
would make it tradeable arrives after the loss it would have avoided.**

---

## 11. LIMITS, AND WHAT WOULD SHARPEN IT

- **Three months, not eight.** The forming-bar ladder requires a full 14-minute generator
  re-run per month (~35 min/month on 5 free cores; this machine is at load 45 and October
  2025 completed 6 of 23 days in 110 minutes). `/tmp/d6/run_months.sh` is running
  202510, 202511, 202512, 202604, 202605 and will drop `pbg_*.jsonl.gz` into
  `/tmp/d6/pbg_<month>/`; `d6_build.py` then makes each a 45-second addition to every table
  here. **Nothing in the verdict is delicate** — 21 of 21 family-month cells are negative on
  the implementable side and 7 of 7 family signs reproduce across all three months — but the
  five extra windows are the honest completion.
- **The paired-vs-phantom split is measured against the generator's own re-emission at the
  close.** A live engine could define confirmation differently (e.g. a price-level
  condition). Any such definition is still an observable at T+15, so §6's −0.55503 bounds it.
- **The bootstrap floor.** 20,000 draws resolve p to 5.0e-5; the OOS counterfactual arm sits
  at that floor and at the lane's own honest multiplicity bar (5.19e-5) simultaneously. It is
  reported unresolved.
- **`liquidity_sweep_reclaim` is 45.5 % of the rows and 81.0 % of the five-family lever**
  (0.455 x 0.25436 + 0.545 x 0.04986 = 0.1429, reproducing the pooled +0.14284 exactly).** Its *own* implementable partial book is −0.4191 / −0.4075 / −0.3074
  across the three months — the worst of the five. The family with the biggest timing lever
  is the family with the worst book, which is itself a finding about where the lever comes
  from.
