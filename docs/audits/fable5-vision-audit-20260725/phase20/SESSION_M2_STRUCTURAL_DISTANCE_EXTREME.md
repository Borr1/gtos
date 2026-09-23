# m2 — `structural_distance_extreme`, SETTLED ON REAL BID/ASK TICKS

**Lane m2, wave 20, phase 20. 2026-08-07.**

The brief: *"It is gross-positive in 15 consecutive windows across three independently written
harnesses… Settle it. Walk this family on real bid/ask ticks… treat it as a genuine question,
not a formality, and do not kill it for tidiness. If it survives, say what it would take to
trade it."*

Machine-readable: `phase20/receipts/m2/M2_SETTLEMENT_V1.json` and five supporting receipts.
**No production code was changed. No R2-bound file was touched. Nothing live was read.**

---

## 0. THE ANSWER

**The persistence is a property of the tape, not of the setups.** Both bar archives are BID on
open/high/low/close; every walker that produced the 15-window streak resolved the entry, the
stop and the target against one side of a book that a round trip crosses twice. Walked on the
broker's own bid/ask ticks with MT5's trigger sides, the family is negative **everywhere**:

| cohort | n | estate convention, tick ordering | **tick truth (MT5 sides)** | CI95 | p(≤0) |
|---|--:|--:|--:|---|--:|
| frozen roster, 4 tick instruments × 7 windows (2025-10 … 2026-04) | 3,315 | **+0.0418** | **−0.2131** | [−0.2608, −0.1624] | **1.0000** |
| **never-read** 2026-06-18 … 07-24, **24 instruments** | 3,269 | **+0.0124** | **−0.3586** | [−0.4097, −0.3054] | **1.0000** |

at the shipped 1.5R target and a 120-minute horizon. At p3's 2.0R / 240 min it is +0.0891 →
**−0.1878** and +0.0179 → **−0.3602**. Every horizon in {120, 240, 1440} min gives the same
answer to three decimals.

**Positivity counts, which is what "persistence" means:**

| | estate convention | tick truth |
|---|--:|--:|
| frozen windows | 6 / 7 | **0 / 7** |
| frozen instruments | 3 / 4 | **0 / 4** |
| never-read weeks | 4 / 6 | **0 / 6** |
| never-read instruments | 15 / 24 | **1 / 24** |
| never-read risk-distance quintiles | — | **0 / 5** |

The streak **does** extend into the never-read window at the estate's own convention — that is a
16th consecutive positive window, and it is honest to say so. It is +0.0124 R/trade with a CI of
[−0.052, +0.082]. At tick truth the same rows book −0.3586, CI95 [−0.4097, −0.3054],
p(≤0) = 1.0000 on 4,000 day-block draws.

### And the loss is the toll, not a wrong call

The exact side mirror — same instants, same |risk|, opposite direction, same MT5 trigger sides,
same fill anchoring:

| cohort | real | **mirror** | signal | CI95 | p(≤0) |
|---|--:|--:|--:|---|--:|
| frozen | −0.2131 | **−0.2504** | +0.0372 | [−0.045, +0.125] | 0.190 |
| never-read | −0.3586 | **−0.3453** | −0.0134 | [−0.112, +0.083] | 0.611 |

**The family and its exact mirror both lose 0.21–0.36 R per trade, and the difference between
them is smaller than its own error bar and changes sign between cohorts.** This family's
directional content is not negative and it is not positive; it is absent, and what kills it is
the cost of transacting a 1–20 bps idea across a 0.6–10 bps spread. That is d1b §4.1's
price-unit reading (−0.0350 bps, CI [−0.272, +0.203]) reproduced from primary tick data.

---

## 1. THE MECHANISM, MEASURED — the break-even in spread-over-risk

Both cohorts pooled, 6,584 rows, shipped contract, binned by the row's own spread ÷ risk
distance (`M2_BREAKEVEN_V1.json`):

| s/d bin | n | median s/d | median stop (bps) | bid-tape (estate) | **tick truth** | CI95 |
|---|--:|--:|--:|--:|--:|---|
| [0.00, 0.02) | 398 | 0.0000 | 1.86 | +0.1518 | **+0.1138** | [−0.002, +0.236] |
| [0.02, 0.04) | 165 | 0.0312 | 3.78 | +0.0610 | **+0.0404** | [−0.168, +0.250] |
| [0.04, 0.06) | 279 | 0.0507 | 7.80 | −0.0678 | **−0.1143** | [−0.262, +0.038] |
| [0.06, 0.08) | 390 | 0.0696 | 6.56 | +0.0421 | **−0.0611** | [−0.183, +0.068] |
| [0.08, 0.12) | 883 | 0.0999 | 4.77 | −0.0737 | **−0.1772** | [−0.254, −0.093] |
| [0.12, 0.18) | 959 | 0.1468 | 3.47 | +0.0174 | **−0.1436** | [−0.224, −0.060] |
| [0.18, 0.25) | 737 | 0.2119 | 2.59 | +0.0955 | **−0.1734** | [−0.261, −0.083] |
| [0.25, 0.35) | 654 | 0.2964 | 2.45 | +0.0203 | **−0.2507** | [−0.344, −0.154] |
| [0.35, 0.50) | 745 | 0.4202 | 2.46 | +0.0517 | **−0.4101** | [−0.482, −0.332] |
| [0.50, 0.75) | 720 | 0.5969 | 8.51 | −0.0090 | **−0.5694** | [−0.629, −0.502] |
| [0.75, ∞) | 654 | 1.0326 | 5.76 | +0.0672 | **−0.8774** | [−0.933, −0.806] |

**Read the two right-hand columns together.** The bid-tape arm is flat — it wanders between
−0.068 and +0.152 with no trend across a 60× range of s/d. The tick-true arm falls
monotonically from +0.114 to −0.877. The correction is not a market effect; it is exactly one
spread of trigger displacement, and its size is governed by one ratio.

**Break-even is s/d ≈ 0.04.** The family's own median spread-over-risk, on the estate's
era-aware model over the whole 23,903-row population, is **0.2267** — **5.7× over the line**
(`M2_COVERAGE_V1.json`). And its edge is concentrated in its *tightest* stops, which is where
that ratio is *largest*: d1b §4.1's Q1 (median stop 1.324 bps) reads +0.1742 on the bid tape here
and **−0.0913 at tick truth**.

---

## 2. WHAT WAS WALKED, AND WHY THE UNCOVERED PART IS BOUNDED RATHER THAN GUESSED

Two independent tick archives, two clocks, two roster provenances.

**Cohort A — the frozen wave-19 roster's own rows.** `lane-inputs-true-utc-hold-20260805`
carries true-UTC bid/ask for XAUUSD, XAGUSD, EURUSD, USDJPY over 202510–202604: **7 of the 8
open windows**, 3,446 rows walked, 28 (symbol, month) cells, **88,305,487 ticks** loaded.
p3 used 2 of those 7 months; this is the whole hold.

**Cohort B — a window nobody has read.** `vps-ticks-20260726` (2026-06-18 … 07-24) begins after
the last roster window ends, so no economic read of this family exists in it. Candidates
regenerated from `vps-bars-20260727` M15 with the proven emitter; **all 24 universe instruments**;
3,277 rows; **88,740,570 ticks** loaded. 177,046,057 ticks across the two cohorts.

**2026-05 has no tick coverage in either archive.** It is measured on bars only and is excluded
from every tick number above. Said plainly rather than filled in.

**The bound.** The correction is one spread of displacement, so its magnitude is a function of
s/d. Measured (era-aware model, whole population):

| | median s/d | bar walk 2R/240 |
|---|--:|--:|
| whole family, 24 symbols, 8 windows | **0.2267** | +0.0424 |
| the 4 tick-covered instruments | **0.1476** | +0.0868 |
| the other 20 | 0.2421 | +0.0338 |
| the never-read cohort (tick-measured) | ≈ 0.29 | — |

The two measured cohorts **bracket** the family's own ratio, and both are decisively negative
(−0.213 and −0.359). Cohort A is additionally the *favourable* half — it is where the bar walk
looks best (+0.0868 vs +0.0338) and where the spread is cheapest — so the damage measured there
is a lower bound on the family's. No extrapolation is needed and none is offered.

---

## 3. THE ACCUMULATION SCREEN — FAILS BOTH CLAUSES

Unconditional signed price capture from the decision instant, one-sided BID tape both legs
(d3's own convention, so the curve is comparable to the published one), coverage-matched so
every horizon is the same rows, with a day-block CI (`M2_ACCUMULATION_V1.json`):

| horizon | frozen cohort (n=3,081) | CI95 | never-read (n=2,128) | CI95 |
|---|--:|---|--:|---|
| 15 m | −0.89 bps | [−2.02, +0.12] | −0.39 | [−1.29, +0.56] |
| **2 h** | **−0.07** | [−3.39, +3.31] | **−1.51** | [−5.63, +2.45] |
| 8 h | +3.38 | [−5.80, +13.02] | +0.20 | [−9.97, +9.65] |
| 24 h | −0.50 | [−17.86, +17.74] | +1.28 | [−20.49, +25.89] |
| 72 h | −22.51 | [−61.00, +20.81] | +8.48 | [−25.77, +39.60] |
| 160 h | −43.68 | [−102.38, +18.32] | −14.56 | [−60.16, +29.32] |
| **320 h** | **−40.27** | [−122.88, +41.91] | **−4.26** | [−62.55, +50.51] |

**Clause 1 (growth 2h → 320h ≥ 10×): FAIL.** The 2 h capture is not distinguishable from zero in
either cohort and its point estimate is negative in both, so the ratio is not a meaningful
quantity; the point estimates do not grow, they wander and change sign between cohorts.

**Clause 2 (capture ÷ own toll ≥ 1): FAIL.** Every horizon's CI spans zero on both cohorts. The
best point estimate anywhere is +8.48 bps at 72 h in the never-read cohort, CI [−25.8, +39.6],
against a median round-trip spread of 0.742 bps and the estate's own 3.02 bps h1 toll — i.e. the
one cell that would pass on a point estimate is a coin flip on its own error bar.

This is limb 2 of the wave-19 verdict, re-measured on ticks for this family alone, and it lands
in the same place.

---

## 4. CONTROLS — the reason to believe any of the above

**(a) The emitter is exact.** `structural_distance_extreme` was re-implemented standalone from
`broader_origin_generators.py:884-916` (+ `_atr` `:2511`, `_prior_high/_low` `:2500`,
`_close_position` `:2517`, `_valid_geometry` `:2841`) so it could be run on an archive the pbg
harness cannot reach. Against the frozen roster, all 8 windows × 24 symbols at k=15
(`M2_REPRO_V1.json`):

- **23,103 matched, 0 geometry mismatches, 0 over-emission.**
- 820 roster rows unmatched (3.43 %) — **all 820** declare a bar-open the archive does not
  contain, and **all 820** reproduce exactly from an earlier bar. That is r2's defect C (stale
  selected closed bar) seen inside this family; the roster records `b = T − 15 min`
  unconditionally (`pbg_run.py`, `emit_rows`) while the generator walked back.
- This family carries **zero** r2 defect-A rows: it is at-market by construction, so
  `fill_gap_R ≡ 0` and no candidate can be born past its own stop. The r2 repair therefore
  removes 3.4 % of this family and cannot change any verdict here.

**(b) The join is exact.** On the frozen cohort, `bid(last tick strictly before T) == the
roster's own entry price` on **99.45 %** of 3,446 rows (100.00 % in every month except 2026-04,
where the tick export stops on 04-29). A wrong clock, a wrong symbol map, or a MID/ASK tape all
fail that test.

**(c) The BID identity, settled a third time, on 24 symbols, in a window no lane had walked.**
In the never-read cohort the M15 close equals the last tick bid strictly before the bar's close
instant at **1.0000 on every one of 24 symbols** (60,152 in-window bars). One test simultaneously
validates the broker-clock conversion on *both* archives (`src/utils/broker_clock.py`,
NEW_YORK_PLUS_7 — never a hardcoded offset), the bar↔tick symbol mapping including
NAS100↔US100_cash and SPX500↔US500_cash, and d8x/p3/r1's BID finding.

**(d) Intrabar ordering is not the mechanism.** On the frozen cohort the M1 bar walk and a tick
walk using the BID on every leg agree on **99.94 %** of rows and differ by **0.0018 R** in the
mean. p3's 89 %/11 % decomposition is confirmed at the family level: essentially all of it is the
quote side.

**(e) M15 resolution is not innocent, and it is disclosed.** The never-read archive has no M1, so
its bar arm is M15 and reads −0.1134 against the tick-BID arm's +0.0124 — **0.126 R of pessimism
from bar coarseness alone**, on a family whose median time-to-stop is 3 minutes (g3 §1.5). Every
estate-convention comparison in §0 for that cohort therefore uses the **tick-BID** arm, not the
M15 arm. Doing otherwise would have flattered my own conclusion.

**(f) The published bar-walk level reproduces in sign and order with independent code.** My
full-population walk reads +0.0424 (2R/240) against r1's +0.06303 and p3's +0.06293. The gap is
explained, not waved at: r1 (`contract.path`) and p3 (`outcome(..., fi+1, ...)`) both start the
path at `[i+1]`, skipping the first minute after the decision instant. On a family that stops out
at a 3 bps level in a median 3 minutes, that minute is the riskiest one, so my baseline is the
more conservative of the two — and it still starts positive.

**(g) The tie rule is INERT in every tick arm, and the entry anchor was attacked.** A single tick
cannot satisfy both the stop and the target predicate (that would require `sl ≥ tp`), so no tick
number here carries a tie-rule assumption; only the M1/M15 bar arms do. And the entry is anchored
at the quote standing at T, which is a fiction if the market was shut at T. Re-read on the rows
whose *next* tick arrives within 5 seconds — 95.5 % of cohort A — the answer moves **against** my
conclusion's favour and does not change it (`M2_GAP_ROBUSTNESS_V1.json`):

| tradability filter | n | share | estate convention | **tick truth** | CI95 |
|---|--:|--:|--:|--:|---|
| none | 3,315 | 1.000 | +0.0418 | **−0.2131** | [−0.260, −0.164] |
| next tick ≤ 600 s | 3,257 | 0.983 | +0.0404 | **−0.2191** | [−0.264, −0.172] |
| next tick ≤ 60 s | 3,231 | 0.975 | +0.0356 | **−0.2229** | [−0.268, −0.175] |
| next tick ≤ 5 s | 3,167 | 0.955 | +0.0294 | **−0.2269** | [−0.273, −0.179] |

---

## 5. THE ONE CELL THE EVIDENCE DOES NOT KILL — and it is the mechanism, not an exception

**BTCUSD**, in the never-read window (`M2_SETTLEMENT_V1.json → the_one_cell_the_evidence_does_not_kill`):

| | |
|---|--:|
| n / trading days | 100 / 32 |
| median spread ÷ risk | **0.0162** |
| median stop | 10.25 bps |
| median spread | 0.159 bps |
| tick-true, 1.5R / 120 m | **+0.1750**, CI95 [−0.045, +0.403], p(≤0) **0.063** |
| tick-true, 2R / 240 m | **+0.2000**, CI95 [−0.032, +0.453], p(≤0) **0.050** |
| side mirror | −0.1750 → signal **+0.350** |

It is the only instrument of 24 whose spread-over-risk sits below the measured break-even
(0.0084 on the era-aware model over the frozen population; 0.0162 tick-measured in the OOS
window). **The one cell that survives is exactly the one the mechanism predicts survives** — which
is corroboration of the mechanism, not a surviving edge.

**It is not admissible and I am not proposing it.** One instrument, one five-week window, n=100,
raw p only, and the family bill for "pick the best of 24 instruments" is unpaid. At the ratified
rule (`CANDIDATE_BOOK_V1`, all-declared basis, sealed α = 0.10) it does not begin to qualify. It
is a **pre-declarable hypothesis for a future test**, and that is all.

---

## 6. WHAT IT WOULD TAKE TO TRADE IT — stated as a requirement, then priced

1. **Spread ≤ ~4 % of the trade's own risk distance.** Measured, §1. The family's median is
   22.7 %.
2. **Widening the stop to buy that ratio is already refuted.** g3's paired natural experiment —
   28,268 rows, identical bar, instant, entry price and side, 2.83× stop width — is worth
   **+0.0329 bps [−0.346, +0.435]**, i.e. zero
   (`phase20/provenance/G3_REVERSION_AND_EXTREME_DOSSIERS.md` §1.5c). And g3's 21-cell
   price-space grid finds 20 of 21 cells negative for this family once every family is given the
   same stop. So the ratio cannot be bought from the denominator.
3. **Which leaves only the numerator: the instrument.** In this 24-symbol universe exactly one
   qualifies. The honest next step, if anyone wants one, is a **pre-declared, properly powered
   BTCUSD-only test with a stated family size** — not a reopening of the family.

**My recommendation: close the family.** Not for tidiness — the question was live, it was walked
on 6,723 rows of real bid/ask ticks across two archives, one of which had never been read, and
the answer came back negative in every cut with the mirror control showing there was never a
direction call to begin with.

---

## 7. WHAT THIS CHANGES ELSEWHERE

- **`SLEEVES_OR_USAGE_OWNER_REPORT.md` §7 item 3 is closed.** *"It needs one tick re-walk to
  settle, and it is the single most interesting unsettled thing in the estate."* It has had one.
  The tick answer is −0.213 / −0.359 R per trade.
- **`SLEEVES_OR_USAGE_VERDICT.md` §17 is confirmed and sharpened.** Its predicted mechanism —
  *"its edge exists only in its two tightest risk-distance quintiles, which is exactly where
  spread-over-risk is largest"* — is now a measured monotone curve with a break-even, not an
  inference.
- **p3 §10's `−0.13028` was a lower bound, as p3 said it would be.** Tick truth on the same
  contract is −0.188 (frozen cohort) to −0.360 (never-read). r1's modelled `delta_fill` of
  −0.2537 lands inside the two measured deltas (−0.2769 frozen, −0.3781 never-read,
  both at 2R/240 against the tick-BID base).
- **The wave-19 verdict does not move.** It rested on net and on the whole family; this lane
  removes its last named open question and does so in the direction the verdict already pointed.

---

## 8. OPEN, HONESTLY

1. **2026-05 is tick-unmeasured** in both archives. It is the one open window with no tick
   evidence; its bar walk is +0.0374 (2R/240). Its s/d is not distinguishable from the rest of the
   family, so the bracket in §2 covers it, but it is bounded rather than measured.
2. **BTCUSD is a live, pre-declarable hypothesis** (§5). It is the only thing in this lane worth
   another hour, and it is worth that hour only with the family bill declared first.
3. **The never-read window is now spent** for this family. It was opened once, on the
   pre-declared question in this brief, and the result is recorded above. Treat 2026-06-18 …
   07-24 as used-once VAL from here.
4. **The tick archives cover FTMO only.** Nothing here measures redacted_account, whose spread
   series is a different one (`AI`: 98 % of the two books' P2 gap is the cost series). This lane
   makes no claim about it in either direction.

---

### Receipts

| file | what |
|---|---|
| `receipts/m2/M2_SETTLEMENT_V1.json` | the verdict object; every number in §0–§6 |
| `receipts/m2/M2_REPRO_V1.json` | the emitter reproduction control (§4a) |
| `receipts/m2/M2_TICK_FROZEN_V1.json` | cohort A: grid, per-instrument, per-window, quintiles, mirror, exit migration, join control |
| `receipts/m2/M2_TICK_OOS_V1.json` | cohort B: the never-read window, same cuts, plus per-symbol BID-identity metadata |
| `receipts/m2/M2_BREAKEVEN_V1.json` | the s/d break-even table (§1) |
| `receipts/m2/M2_COVERAGE_V1.json` | full-population bar walk + era-aware s/d placement (§2) |
| `receipts/m2/M2_ACCUMULATION_V1.json` | the accumulation ladders with CIs (§3) and the BTCUSD cell (§5) |
| `receipts/m2/M2_GAP_ROBUSTNESS_V1.json` | the entry-anchor / tradability attack (§4g) |
| `receipts/m2/m2_emit.py` | the standalone emitter |
| `receipts/m2/m2_repro2.py` | the reproduction control |
| `receipts/m2/m2_tickcache.py` | lane-hold tick JSONL → binary cache |
| `receipts/m2/m2_tickwalk.py` | cohort A walker (4 arms + mirror) |
| `receipts/m2/m2_oos.py` | cohort B: regenerate + validate + walk |
| `receipts/m2/m2_barfull.py` | full-population bar walk + spread stamping |
| `receipts/m2/m2_final.py` | receipt builder |
