# LANE a1 — THE VERDICT, WITH ITS MECHANISM

**Wave 19, phase 19. 2026-08-06.** Adjudication lane. No new measurement; this lane arbitrates the
thirteen lanes that measured.

> **NOTE ON THE LANE KEY.** `a1_RESULT.md` / `.json` in this directory belong to an **earlier
> swarm's** a1 ("PRICE IT JOINTLY, AND TEST IT WHERE IT WAS NOT FOUND", a1-SCORER-V1). They are
> untouched. This lane's receipt is `a1verdict_*` to avoid the collision.

**PRIMARY DELIVERABLE — read this, not the receipt:**
`docs/audits/fable5-vision-audit-20260725/phase19/SLEEVES_OR_USAGE_VERDICT.md`
Machine-readable: `phase19/SLEEVES_OR_USAGE_VERDICT.json`
Reconciliation arithmetic: reproduced by `/tmp/a1v/verdict_math.py` (inputs are all committed).

---

## THE ANSWER

**SIGNAL.**

Two numbers from the oracle ladder (`f2/F2_POOLED_V1.json → LADDER_TABLE_TRACK_B`, n = 141,230,
172 trading days, 8 windows):

1. Hand the **shipped** machinery a correct direction call — same gate, same M15-close instant, same
   2R/−1R exit — and the book goes **−0.29226 → +0.59673** R/trade. A correct direction call is worth
   **+0.88898**. This family delivers **+0.00221** of it = **0.249 %**.
2. Hand the **real** direction call perfect usage (oracle exit + oracle entry + oracle ranker +
   unlimited capacity) and it books **+2.33914**. A coin flip on the identical rows books **+2.31133**
   = **98.81 %**. Perfect usage is worth +2.63140 and **99.03 %** of that is available to anybody.

Not one rung's paired signal CI excludes zero (R1 +0.00315 ± 0.01026, 5/8 months; R4b +0.02877 ±
0.02816, 6/8).

---

## THE MECHANISM — three limbs

**1. SCALE.** Stops of **8.09 bps** median against a **0.716 bps** spread; s/d 0.0926 median, > 0.10
on 46.6 % of rows. On the sealed test: **+0.0119 bps captured vs a 3.0159 bps toll = 253.4× short**.
In R the same rows read 12.6×, because R divides by the generator's own tiny stop. The capture is
**1.66 % of one median spread**.

**2. NO ACCUMULATION.** Paired side-mirror, same walker, bps of price:

| horizon | broad V4 | live W7 sleeve |
|---:|---:|---:|
| 2 h | 0.2008 | 3.4067 |
| 320 h | 0.1938 | 128.0388 |
| **growth** | **0.965×** | **37.58×** |

The toll is paid once per trade; a signal that does not grow cannot outrun it by holding longer.
Widening the stop instead: **0 of 282** transplanted contracts net-positive, and at the crypto-shaped
cell (400 bps / 4R / 320 h) the family is **significantly worse than a coin flip** (−0.01504,
p(≤0) 0.9948). Reverse transplant: a working sleeve on the broad contract goes +0.6970 → **−0.9585**.

**3. THE INSTRUMENT WAS FLATTERING IT.** Bars are **BID** (100.00 % of 76,734 M15; 99.99 % of 223,239
M1, verified against the broker's own ticks). Every walker uses unshifted levels. Constant-sign
optimism **−0.0696 to −0.1160 R/fill**, of which 89 % is the quote side and 11 % intrabar ordering.

| positive gross claim | R/fill | smallest measured bias ÷ claim |
|---|---:|---:|
| f2 signal at perfect usage | +0.02877 | 2.42× |
| d1b at-market corrected | +0.02402 | 2.90× |
| p2 **sealed** clean roster | +0.02718 | 2.56× |
| d5/p3 broker-correct fill | +0.01140 | 6.10× |

Corrected on ticks the gross is **negative**: −0.0387 (Jan) / −0.1447 (Apr) R/fill.
**NET numbers survive** (error ±0.02–0.04, no consistent sign); **GROSS-positive claims do not.**

---

## WHY NOT USAGE

- Gate captures **83.8 %** of the range between a random gate and the best feasible one; exit capture
  **−0.44 %**; entry-timing capture **0 %** (no such layer exists).
- Reachable share of each oracle gap: gate **3.88 %**, exit **2.32 %**, timing **2.80 %**. The
  biggest gap (ranking) is 87.2 % unreachable — a 38-feature ridge captures 12.80 % and books −0.00009.
- All deployable repairs **priced jointly**: **+0.00553** against a **+0.29226** gap = **52.9×**
  (standalone sum +0.12114 → double-count factor 21.9×).
- The usage **ADDS**: +0.0667 R/trade over a geometry-matched roster draw.
- The one large usage number (shipped cost gate, +0.22601) is a **toll filter** — signal contribution
  **−0.00976**, and it turns **harmful** (−0.36933) under an oracle exit.

---

## WHAT WOULD HAVE TO BE TRUE — and the way to know

| lever | status |
|---|---|
| capture more price | **253×** needed; 282 contracts priced, 0 positive; direction gets *worse* as the contract widens |
| pay less toll | **CLOSED ON ARITHMETIC** — required toll is **negative**; a **free broker** leaves the book at **−0.01327** (`D7_STAGE1.json → L4_cost`: `required_C −0.013269`, `reduction_needed_pct 104.719`, `feasible false`) |
| select the good cells | cost rank travels **+0.9005**, edge rank **+0.0230**; edge ordering fails against a **random half of its own month** (+0.0466); **324 OOS arms, 0 positive books**, median 97.7 % of every gain is toll; **oracle** ceiling +0.02548 vs a 0.30825 toll = **12.1× short** |

Detection floor ±0.01026 pooled — resolves an effect **32.1×** smaller than the family needs, and
sees nothing. Injection recovers a known edge where only **1.03 %** of rows change side.

### THE REOPENING TEST — the accumulation screen

Paired side-mirror walk at {2, 8, 24, 72, 160, 320} h, signal in **bps of price, not R**. Admit to
economic evaluation only if **(i)** growth 2 h → 320 h ≥ **10×** and **(ii)** capture ÷ own toll ≥ 1.

Broad V4: **0.97× / 0.076.** Live W7 sleeves: **37.58× / 2.36–11.46.**

Pre-economic — reads no P&L, so it costs no multiplicity and no held-out month. It makes a **wide**
search affordable rather than narrowing one.

---

## WHAT SURVIVES

| item | axis | standing |
|---|---|---|
| exit contract `stop_only_horizon` > `target_2.0R` | usage | rank persistence **+0.6399 on gross**, cost delta **0.00000 in all 8 months**; +0.03500 in sample (8/8), **+0.01002 sealed** (3/3 but fails its declared +0.02 bar); d7's 56-cell surface is a coin flip at every cell → a **contract** improvement, not an edge. **Transferable — belongs on the sleeve book.** |
| POI gate in %-of-price vs an R contract | usage | real source defect (`broader_origin_generators.py:1201/:1391/:1446`); 11.2–13.5 R admission radius on a 1.5R trade; repaired book still **−0.24981 R/fill** |
| walker quote-side repair | neither | instrument, not result; **precondition for any future usage measurement in this estate** |
| the accumulation discriminant | neither | the wave's one generalising method |

**DIED, each with mechanism:** forming-bar candidate (98.0 % of the phantom's loss is booked before
the information arrives; sealed −0.30551 vs −0.28041) · `structural_distance_extreme` (edge only in
its two tightest-stop quintiles; own correction 1.54× its sealed gross) · affordability selection ·
entry offset j=5 (81.6 % fee schedule) · the cheapest-toll decile (killed inside its own lane) ·
breaker inversion.

---

## THE CORRECTED RECORD

17 rows, old vs new vs reason, in `SLEEVES_OR_USAGE_VERDICT.md` §4 and
`SLEEVES_OR_USAGE_VERDICT.json → CORRECTED_RECORD`. The four that matter most:

1. **−0.217496 was never a path walk** — it is `opportunity_net_proxy_r + cost_r`, the engine's own
   counterfactual proxy. Three walkable numbers exist on the same rows spanning 0.28 R.
2. **`risk.min_rr` is 1.5** — the published "needs 45.94 %, gets 34.68 %" (−11.26 pp) becomes
   **−0.57 pp** on the correct object at the correct target. Both geometries were then carried and
   **the sign of every conclusion is unchanged.**
3. **The population was a look-ahead** — 18.03 % of output, admitted by an outcome-decodability gate
   (`v4_timewarp:28130-28140`); fill rate 99.43 % vs 14.29 %, born-past-stop 10.57 % vs 0.15 %.
4. **The bars are BID** — h3's own #1 open question, closed, and it invalidates every GROSS-positive
   claim in the estate while leaving every NET number standing.

---

## WHAT TO DO NEXT

1. **Stop** spending measurement on the family as a source of tradeable edge. Cost 0. (The taken book
   cannot be adjudicated by running it — **14.4 years**.)
2. **Repair the walkers' quote side** — ~1 h; removes a bias **larger than every usage lever this
   wave found**; the same walkers price the live sleeve work.
3. **Port the exit contract to the sleeve book** — already wired (`--frontier-exits`, default off);
   one R there is 44–436 bps instead of 8.
4. **Fix the POI gate** — one predicate at three call sites, behind an absent-false key.
5. **Stand up the accumulation screen** as the pre-economic admission gate — ~1 day.
6. **Run it on `deep_universe_h4d1_2014_2026`** — 24 instruments (exactly the family's own), 2014–2026,
   439,895 bars, 27 MB, **zero references in the entire discovery corpus**. d3's 37.58× has **no null**;
   this decides whether the screen is a discriminant or a tautology, so it precedes trusting item 5.
7. **Capture new held-out data** — the estate is at **zero**.

**NOT recommended:** any further broad-family filter, ranker, cost cap, session rule, instrument
subset, entry offset, sizing rule or exit sweep.

---

## WHAT I GOT WRONG / UNRESOLVED

- **The direction sign is genuinely unresolved**: f2 +0.02877 · p2 sealed +0.02391 (3/3) · d7
  −0.04230 (0/5) · p3 paired mirror −0.00096 (2/8). Adjudicated as **zero within a band 10–30×
  smaller than the toll**, because the disagreement is smaller than the measurement error of the
  instrument that produced all four. **The verdict does not depend on it** — it rests on the 253×
  price-unit shortfall and the 0.97× accumulation.
- **Largest soft spot:** d3's live-sleeve control is in-sample, n = 134, and all five sleeves REJECT
  at the ratified gate, so the accumulation screen's threshold rests on one arguably-lucky sample
  until item 6 runs. A 10× haircut still leaves it 66× above the broad family.
- p3's tick truth is 4 symbols × 2 windows; the 8-window figure is modelled (agrees to within 4 % on
  January).
- **This lane's characteristic failure is manufacturing coherence.** Guarded by leading with the one
  construction that needs no synthesis (the oracle ladder — one artifact, one population) and by
  naming every disagreement rather than resolving it by assertion.
- Lane self-corrections published by the lanes themselves: d1b's cheapest-toll decile (killed in
  lane), d3's `partial_be_runner` walker (36.2× artifact), d6's correction of PB's double-count,
  d5's central claim overturned by p3 inside the same wave, f1's family table under the wrong order
  type, d1b's mirrored-limit artifact on POI, h2's false untestability premise.

**FALSIFIER:** a candidate family on these instruments that passes the accumulation screen. Nothing
else — the other three levers are closed arithmetically.
