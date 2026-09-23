# Lane G — reconciliation: Lane C vs Lane E vs Lane D vs the orchestrator's anti-predictive claim

**Commission:** orchestrator, 2026-08-12, two mid-task additions to Lane G. Reconcile Lane C's
"8 of 10 broad families gross-positive" against Lane E's "every family below the driftless
1/3 null", then against Lane D's finding that no walker crossed the spread.

**All four are measurable on one population and I measured all four.** Companion document:
`LANE_G_INDEPENDENT_VERIFICATION_V1.md` (the five original verification items). Receipts and
every script under `lane_g_receipts/`.

---

## 0. Lead answer, in the order the orchestrator asked for it

**(1) The wave-21 funnel caches are on the REPAIRED instrument. They cross the spread. Nothing
needs re-walking.** Proved three independent ways below (§1). Lane D's bent ruler is a
different walker on a different population; it does not reach these caches. *Today's swarm
numbers are not on a bent ruler.*

**(2) Lane C and Lane E are both correct and are the same fact seen from two sides. Neither is
evidence of anything.** They are linked by an exact arithmetic identity: for a driftless tape,
`E[net + cost_r] = 0` for any geometry, direction or horizon. That forces
`p_target = 1/3 − P(ts)·E[cf|ts] / (3·P(bar))`, so **a positive time-stop bucket REQUIRES a
target-hit rate below 1/3.** The time-stop bucket is positive for 10 of 10 families
(+0.056…+0.555) and the hit rate is below 1/3 for 10 of 10. Lane E withdrew the first as a
corridor artifact; the same withdrawal kills the second, and **kills the orchestrator's
anti-predictive headline with it.**

**(3) Lane C's "8/10 gross-positive" survives as arithmetic and dies as a claim about edge.**
`net + cost_r` is not "edge before avoidable cost" — it is the *tape travel* of the trade, which
is zero under a driftless tape by construction. Measured on the seven MARKET families it is
**+0.0078 ± 0.0042 R/fill (95 % CI [−0.0004, +0.0160], n = 74,249)** and a **direction-flipped
control on the identical paths gives +0.0055 ± 0.0042, paired difference +0.0012 ± 0.0075
(t = +0.16)**. The three LIMIT families' +0.049…+0.053 is **1.01×, 1.07× and 1.15× half their own
mean spread** — the signature of a resting order filling at a local extreme, and independently
bounded by Lane D's own G3 mirror-limit control at ≈0.179 R/trade, 3.3× larger than the number
it would have to explain.

**(4) The single reconciled statement.** On the correct instrument, over 146,745 filled candidate
occurrences across five months:

| quantity | MARKET families (n = 74,249) | cost-eligible MARKET (n = 41,147) |
|---|---:|---:|
| **cost-free expectancy** `E[gross + spread_r]` | **+0.0078 ± 0.0042** | **+0.0019 ± 0.0052** |
| direction-flipped control, same paths | +0.0055 ± 0.0042 | +0.0023 ± 0.0052 |
| paired difference (signal − flipped) | **+0.0012 ± 0.0075** | — |
| `E[spread_r]` | 0.1409 | 0.0563 |
| **realised `E[net]`** | **−0.2725** | **−0.1037** |

**The pool's gross directional expectancy is zero — bounded above at +0.016 R per fill at 95 %
confidence — and its realised expectancy is exactly minus its own transaction cost.**

---

## 1. Is the cached population pre- or post-repair? — POST. Three proofs.

**Proof 1 — the code path.** The wave-21 funnel population is built by
`candidate_funnel_analysis._lifecycle_row`, which calls
`resolve_post_submission_m1_lifecycle` with **both** `m1_price_basis=BarQuote.BID` **and**
`spread_by_bar=spreads[start:end]` (`candidate_funnel_analysis.py:146-162`). `BarQuote.BID` is
the *declaration that the OHLC archive is a bid archive*, not an instruction to ignore the
spread: the resolver shifts every bar by `entry_quote_offset` on the entry side and
`exit_quote_offset` on the exit side before any touch test
(`quote_side.py:1238-1244`, `:1247-1252`, offsets defined at `:385-412`). Under `BID` basis a
LONG transacts at `tape + spread` and is stopped against the raw tape; a SHORT transacts at the
tape and is stopped against `tape + spread`. One spread per round trip, on the correct side, per
direction. **This is the repaired instrument Lane D says the estate walkers lacked** — Lane D's
own ledger records it being built ("a quote-side walker with 27 hand-computed tests").

**Proof 2 — a per-row exact identity.** If the fill sits on the executable entry side and the
barriers are compared on the executable exit side, then for an intrabar stop touch
`gross = −1 − drift − spread_r` for a LONG and `−1 − drift` for a SHORT (the SHORT pays the same
spread, but it lands in the *barrier geometry* rather than in the P&L: a short's stop triggers
after only `R − s` of tape travel). Measured on the 52,655 barrier-resolved rows of the sealed
population, that identity holds to **|residual| < 1e-9 on 98.48 % / 98.38 % / 98.27 % / 98.68 %**
of (STOP,LONG) / (STOP,SHORT) / (TARGET,LONG) / (TARGET,SHORT) rows. The ~1.6 % residual is the
`SUCCESSOR_M1_OPEN_GAP` branch, exactly as the code says. Receipt: `frame_check2.py`.

**Proof 3 — the population-level martingale.** If the spread were *not* crossed, `E[gross]` would
be 0 for a driftless tape. If it is crossed once, `E[gross] = −E[spread_r]` exactly. Measured:
`E[gross] = −0.1331` against `−E[spread_r] = −0.1409`, residual **+0.0078 ± 0.0042**
(n = 74,249). Cost-eligible: residual **+0.0019 ± 0.0052**. Receipt: `martingale.json`.

**Consequence for Lane A's observation.** Lane A is right that the sealed deductible excludes the
spread (`candidate_funnel_analysis.py:163-166`) — and that is *because* the spread is already
inside `terminal_gross_r`. Verified: `net == gross − deductible` and
`cost_r == spread_r + deductible` hold on **0 of 74,249** rows as exceptions. So
`net + cost_r ≡ gross + spread_r` is arithmetically exact, and it adds back a spread that **was**
charged. Lane C's reconstruction is sound. Its interpretation is not.

---

## 2. The decomposition that reconciles Lane C and Lane E

Cost-free R (`net + cost_r`) by resolution type, five months, all ten families
(`reconcile.json`, `reconcile.py`):

| family | ord | n | TARGET share / mean | STOP share / mean | TIME_STOP share / mean | total | p_target | implied p_target |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `cross_asset_lead_lag` | MKT | 10,919 | 0.283 / +1.906 | 0.627 / −0.870 | 0.090 / **+0.413** | +0.0322 | 0.3113 | 0.3197 |
| `current_breaker_re_entry` | LIM | 3,982 | 0.168 / +2.109 | 0.479 / −0.885 | 0.353 / **+0.344** | +0.0523 | 0.2597 | 0.2707 |
| `current_fvg_fill` | LIM | 60,911 | 0.239 / +2.110 | 0.578 / −0.891 | 0.183 / **+0.354** | +0.0545 | 0.2927 | 0.3070 |
| `current_ob_retest` | LIM | 7,603 | 0.118 / +2.087 | 0.399 / −0.909 | 0.483 / **+0.344** | +0.0490 | 0.2277 | 0.2263 |
| `displacement_continuation` | MKT | 20,737 | 0.124 / +1.973 | 0.402 / −0.920 | 0.474 / **+0.284** | +0.0089 | 0.2353 | 0.2479 |
| `liquidity_sweep_reclaim` | MKT | 23,049 | 0.222 / +1.959 | 0.587 / −0.878 | 0.191 / **+0.409** | −0.0028 | 0.2742 | 0.3011 |
| `regime_transition_break` | MKT | 1,222 | 0.016 / +1.945 | 0.110 / −0.931 | 0.874 / **+0.093** | +0.0085 | 0.1234 | 0.1187 |
| `session_open_range_break` | MKT | 4,785 | 0.070 / +1.968 | 0.285 / −0.943 | 0.645 / **+0.233** | +0.0201 | 0.1984 | 0.1926 |
| `structural_distance_extreme` | MKT | 11,118 | 0.310 / +1.789 | 0.680 / −0.808 | 0.010 / **+0.555** | +0.0095 | 0.3128 | 0.3315 |
| `volatility_compression_expansion` | MKT | 2,419 | 0.013 / +1.920 | 0.116 / −0.836 | 0.871 / **+0.056** | −0.0234 | 0.1022 | 0.2087 |
| **ALL** | | **146,745** | 0.209 / +2.014 | 0.533 / −0.883 | 0.258 / **+0.309** | **+0.0309** | | |

**The orchestrator's hypothesis is confirmed exactly as stated.** The barrier bucket is
below-null in every family; the time-stop bucket is positive in every family; and they nearly
cancel. The `implied p_target` column is not fitted — it is what the martingale identity *demands*
given the measured time-stop bucket, and it tracks the observed hit rate to within 0.001–0.027 on
9 of 10 families (`volatility_compression_expansion` is the exception at 313 barrier rows).

### 2.1 Lane E's corridor control kills Lane E's own headline too — and mine

Lane E withdrew its positive-time-stop reading as a corridor-midpoint artifact on
Spearman(corridor width in ATR, time-stop mean) = −0.612. On my measurement over the same ten
families that correlation is **−0.9394 (p = 0.0001)** — stronger than published. And the decisive
addition nobody made:

> **Spearman(corridor width in ATR, target-hit rate) = −0.9636 (p = 0.00003).**

The *same* corridor artifact drives the *same* rank order in the hit rate. Lane E's withdrawal was
correct and it is not partial: it removes the interpretation of both buckets. A driftless walk
inside an asymmetric corridor `[−1R, +2R]` with a finite horizon has a conditional terminal value
biased toward the corridor midpoint, and correspondingly a barrier-conditional target rate below
`1/3`. That is a property of the *contract*, not of the entries.

### 2.2 The direct control: a direction-randomised arm reproduces the whole effect

I re-walked the identical 81,968 MARKET candidates through the identical frozen labeler with a
third arm: **MIRROR** — same instant, same 1R stop, same 2R target, direction flipped
(`laneg_walk.py`). Control: my ORIG and INV arms reproduce Phase 0's walk on **81,968 rows,
0 mismatches, max |net difference| 0.0**.

| | signal direction | flipped direction |
|---|---:|---:|
| target-hit rate, barrier-resolved | **0.2773** (n 52,655) | **0.2772** (n 52,304) |
| vs corrected driftless benchmark | z = **−17.49** | z = **−19.78** |
| cost-free R per fill | +0.01525 ± 0.00429 | +0.01406 ± 0.00428 |

Geometry-matched, assumption-free (compare only same-side/same-geometry rows: signal-endorsed
LONGs against flipped-from-SHORT LONGs, and likewise for SHORTs): **endorsed 0.2773 vs opposed
0.2772, z = +0.02, p = 0.985** (`mirror_geometry_matched.json`).

**A control that cannot carry directional information by construction reproduces the entire
"anti-predictive" signature.** Every reading built on the `1/3` null — Lane E's, and the funnel
plan's z = −10.8…−48.9, and Phase 0's z = −5.6…−25.0 — is measuring the contract, not the entries.

### 2.3 Where Lane C's residual comes from

After the two buckets cancel, a residual remains: +0.031 pooled, +0.0084 MARKET-only, +0.0538
LIMIT-only. Two candidate mechanisms, both tested:

* **Asymmetric gap censoring** — `CENSORED_INVALID_GAP_THROUGH_SL_OR_TP` drops rows whose fill-bar
  exit-side open is already through the stop (1R away) *or* the target (2R away), so adverse gaps
  ≥1R are dropped while favourable gaps need ≥2R. Plausible, and **refuted**:
  Spearman(invalid-gap rate, cost-free edge) = **−0.43 (p 0.21)**, wrong sign, and the three LIMIT
  families carry **0.00–0.01 %** invalid-gap censoring with the *largest* residual
  (`residual_probe.py`).
* **Directional information** — **refuted for MARKET** by the paired mirror: +0.0012 ± 0.0075,
  t = +0.16.
* **For the three LIMIT families the residual is almost exactly half their own spread**
  (`final_checks.py`):

| family | mean `spread_r` | half | cost-free edge | ratio |
|---|---:|---:|---:|---:|
| `current_breaker_re_entry` | 0.1049 | 0.0525 | +0.0528 | **1.01** |
| `current_fvg_fill` | 0.1021 | 0.0510 | +0.0545 | **1.07** |
| `current_ob_retest` | 0.0861 | 0.0430 | +0.0496 | **1.15** |

The seven MARKET families show no such relation (ratios 0.36, 0.24, −0.04, 0.55, 0.73, 0.06,
−0.89). A resting limit fills at the instant the entry-side bar touches its level — a local
extreme of the sampled path — and measuring tape travel forward from a running extreme is biased
in the order's own favour. **Lane D already measured this and it is larger than the number it
would have to explain**: G3's mirror-limit control on `current_fvg_fill` finds a 5.4–5.7× magnet
ratio worth **≈0.179 R/trade**, against the +0.0545 in question. The committed machinery cannot
express a mirrored LIMIT (Phase 0 T4: 4,258 of 4,360 rows censor), so this cannot be closed
inside the funnel harness — but it does not need to be. **The three LIMIT families are not
evidence of edge.**

---

## 3. Lane D reconciled

Lane D's finding stands and does not touch these caches. The distinction to record:

| | Lane D's population | the wave-21 funnel population |
|---|---|---|
| walker | the estate / discovery-swarm walkers (G-series, 43,755 trades; H1's 97,802 fills) | `quote_side.resolve_post_submission_m1_lifecycle` |
| spread crossing | **absent** — repaired later | **present**, verified per-row and at population level |
| Lane D's own verdict on the funnel caches | — | its A14 row prices Phase 0 on exactly these rows without an instrument caveat |

Lane D's "broad origin family 5/10 → 0/10 gross-positive" is a statement about the *pre-repair*
estate walk of the broad-origin generators. Lane C's "8/10 gross-positive" is a statement about
the *post-repair* funnel walk with the spread added back afterwards. **They are not the same
measurement of the same thing, and the apparent contradiction dissolves once the two bases are
named.** With the spread left where the repaired walker puts it, the funnel population is
**0 of 10 gross-positive** — every family's `E[terminal_gross_r]` is negative, from **−0.0219**
(`regime_transition_break`) to **−0.2796** (`structural_distance_extreme`) — which is Lane D's
number, on Lane D's basis, arrived at independently.

---

## 4. What this means for the R-unit / stop-width thesis

Lane C's recommendation — that `moonshot_broader_origin_stop_width_atr_scale` is the only
unsearched axis arithmetically connected to the dominant loss term — is **directionally right and
bounded much more tightly than Lane C states.**

Right, because `cost_r` is cost-in-price divided by the stop distance: doubling the stop halves
`spread_r` *and* halves the position at fixed fractional risk, so it halves the loss in both R and
currency. Nothing else on the parameter surface touches the term that is 100 % of the measured
loss.

Bounded, because the gross edge it would be collecting is **measured at zero**:

* point estimate **+0.0078 R/fill**, 95 % CI **[−0.0004, +0.0160]** (MARKET, n = 74,249);
* a direction-flipped control on the same paths gives +0.0055;
* so the *best attainable* net expectancy as the stop widens without limit is **0**, and it is
  reached only asymptotically.

Concretely: the median MARKET `spread_r` is 0.087. To push the cost term below the **upper** 95 %
bound on the edge (+0.016) the stop would have to be ≈**5.4× wider**, and the point estimate of net
at that setting is still ≈−0.008 R/fill. **Widening the stop cannot make this pool profitable; it
can only make it less unprofitable.** The stop-width sweep is worth running as the cheapest way to
establish that ceiling exactly — but it should be commissioned as a *bound-establishing* experiment,
not as a repair, and no plan should be built on it producing a positive.

The one honest caveat in the other direction: an edge of **+0.05 R/fill** is excluded by this
population (it is 10 σ away), but an edge of **+0.01** is not. If a generator change moved gross to
+0.05, a stop wide enough to hold `spread_r` near 0.02 would make it a real strategy. That is a
statement about a *different pool*, and it is the only version of the thesis the evidence supports.

---

## 5. Claims that must be amended (reconciliation scope)

| document | claim | required action |
|---|---|---|
| `LANE_C_PARAMETER_SPACE_AUDIT_V1.md` | "8 of 10 families gross-POSITIVE, −0.023…+0.055 R/fill" | **AMEND.** Arithmetically reproduced exactly. But `net + cost_r` is tape travel, which is zero under a driftless tape by construction; MARKET = +0.008 ± 0.004 with a direction-flipped control at +0.006; LIMIT = 1.0–1.15× half the spread. State as "gross expectancy is zero", not "positive". |
| `LANE_C_PARAMETER_SPACE_AUDIT_V1.md` | stop-width is the unsearched axis connected to the loss | **STRENGTHEN + BOUND.** Correct that it is the only lever on the dominant term; add that the attainable ceiling is 0, not positive, because the gross edge is +0.008 ± 0.004. |
| `LANE_E_GENERATOR_LOGIC_REVIEW_V1.md` | every family below the 1/3 driftless null over 108,790 resolutions | **AMEND.** Rates reproduced exactly. But a direction-flipped control on the identical paths gives 0.2772 against 0.2773, and Spearman(corridor width, hit rate) = −0.96. Below-1/3 is the corridor + horizon, not the entries. Lane E's own corridor withdrawal applies to its headline. |
| `LANE_D_POSITIVE_FINDINGS_LEDGER_V1.md` | "every walker in the estate resolved against a BID archive without crossing the spread" | **QUALIFY.** True of the estate/discovery walkers. **Not** true of `quote_side.resolve_post_submission_m1_lifecycle`, which produced the wave-21 funnel caches — verified per-row. Name the exception so the next reader does not retract sound numbers. |
| `FUNNEL_ROOT_CAUSE_AND_V2_PLAN.md` §0/§1/§3 | "every candidate family is directionally anti-predictive" | **STRIKE.** See `LANE_G_INDEPENDENT_VERIFICATION_V1.md` §1. |
| `PHASE0_INVERSION_TRUTH_V1.md` §2/§7(a) | "the anti-signal survives correction, z = −5.6…−25.0" | **STRIKE.** See `LANE_G_INDEPENDENT_VERIFICATION_V1.md` §1. Phase 0's *kill verdict* survives unchanged and is independently reproduced. |

---

*Receipts: `lane_g_receipts/` — `laneg_walk.py` (three-arm walk),
`reconcile.py`/`reconcile.json`, `martingale.py`/`martingale.json`,
`mirror*.py`/`mirror_*.json`, `residual_probe.py`, `final_checks.py`, `frame_check2.py`.
Population: `/private/tmp/w21-puzzle-cache` (durable copy under the evidence hold), the sealed
candidate roots `/private/tmp/w21-market-top-{feb-r2,aprmay-r3,junjul-r4}`, and the frozen M1
sources at `lane-inputs-true-utc-hold-20260805`.*
