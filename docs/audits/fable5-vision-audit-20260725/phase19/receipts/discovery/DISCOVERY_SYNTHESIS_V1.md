# DISCOVERY SYNTHESIS V1 — Wave 19 broad forensic swarm

**Date** 2026-08-06 · **Lane** synthesis · **Inputs** w0 (3 lanes) + wave 1 (12 lanes) + wave 2 (7 lanes)
**Population** the broad-V4 diagnostic pools, January–May 2026, true UTC.
**Total candidates measured** 124,738 (Jan 27,658 · Feb 24,239 · Mar 26,500 · Apr 25,056 · May 21,285)
**Machine JSON** `DISCOVERY_SYNTHESIS_V1.json` beside this file.

> Every number here is measured. Where a lane's number was overturned by a later lane, the later
> number is used and the overturn is logged in §6. Nothing in this document is estimated.

---

## §0 — READ THIS FIRST: the three books, and why they disagree

Three different populations are quoted throughout this swarm. Mixing them is the single easiest way
to misread the whole thing.

| book | what it is | n (Jan) | why it exists |
|---|---|---:|---|
| **POOL** | every candidate, scored as the engine scored it | 27,658 | what every prior session quoted |
| **TAKEABLE** | pool minus the 3,516 whose stop was already breached at the decision instant | 24,142 | w0-capture: those rows were never orders |
| **LIVE-EXPRESSIBLE** | only orders the live engine can actually place — market orders at the decision price | 14,911 (53.9%) | l10-X3: 296/296 live entries equal the executable quote to floating-point exactness; the live engine has **no** `TRADE_ACTION_PENDING` path |

**The LIVE-EXPRESSIBLE book is the only one that can become money.** 46.088% of the January pool
(12,747 rows) is a passive limit order at a price level the live engine has never once placed and
cannot place. Everything this synthesis recommends is measured on that cohort, pooled over three
months (43,755 trades).

Two conventions also decide numbers, and both were wrong somewhere in this estate before this swarm:

- **fill-blind** scoring credits path value without requiring the entry limit to trade. It
  manufactures **+0.2776 R/trade** pool-wide (W0-F2). It is how CQ's V27 candidate got to +11.9.
- **fill-honest** requires the entry to trade first. Correct for a resting limit; but on the 53.9%
  that are market orders it makes you wait for a price you would already have been filled at, and
  **over-charges them by 0.06736 R/trade** (e-coherence). On the live-expressible cohort, blind and
  honest are the same thing by construction, which is a third reason to work there.

---

## §1 — THE ANSWER

> *"do we know WHAT to trade and not HOW, or the reverse, or both, or neither?"*

### The answer is: we know WHAT. We do not know HOW to pay for it.

That is the opposite of what every prior session in this estate concluded, and one table decides it.

**Under the repaired contract (market order, entry delayed 5 minutes, 0.25R trailing exit, no other
change), pooled over January + February + March, 43,755 live-expressible trades — ordered by
broker-true cost:**

| symbol | n | broker-true cost (R) | gross (R) | net (R) | edge (bps) | toll (bps) | edge:toll |
|---|---:|---:|---:|---:|---:|---:|---:|
| **GER40** | 1,858 | **0.0466** | **+0.06465** | **+0.01803** | +0.911 | 0.501 | **1.387** |
| NAS100 | 1,904 | 0.0516 | +0.02370 | −0.02787 | +0.259 | 0.575 | 0.460 |
| US30_cash | 1,942 | 0.0519 | +0.03254 | −0.01935 | +0.375 | 0.403 | 0.627 |
| XAUUSD | 1,996 | 0.0713 | +0.04661 | −0.02465 | +0.906 | 1.282 | 0.654 |
| JP225 | 1,627 | 0.0795 | +0.03476 | −0.04477 | +1.297 | 1.462 | 0.437 |
| UK100 | 2,002 | 0.1014 | +0.06153 | −0.03992 | +0.726 | 0.822 | 0.607 |
| … 17 more … | | 0.118 → 0.343 | all positive | all negative | | | 0.012 → 0.526 |
| USOIL_cash | 1,777 | 0.3428 | +0.03525 | −0.30758 | +0.348 | 9.772 | 0.103 |
| **ALL 24** | **43,755** | **0.18183** | **+0.03834** | **−0.14349** | **+0.231** | **2.457** | **0.211** |

Read the two facts in that table:

1. **The gross edge is universal. 24 of 24 instruments are gross-positive** (in price space, 19 of
   24). Pooled gross is **+0.03834 R/trade at t = +12.35**, bootstrap 95% CI **[+0.0301, +0.0462]**,
   P(≤0) = 0.0000 over 63 trading days, **53 of 63 days positive**, and it replicates month by month
   (Jan/Feb/Mar delay gains +0.06689 / +0.06610 / +0.06572 — three decimal places apart).
   **There is a signal, it is in every instrument, and it is statistically unambiguous.**

2. **The gross edge is flat across the cost ordering and the cost is not.** Gross runs +0.002 to
   +0.065 with **Spearman(gross, cost) = −0.157** — i.e. no relationship. Cost runs 0.047 to 0.343,
   a **7.4× spread**. Consequently **Spearman(net, cost) = −0.980**, and **cost explains 89.65% of
   the cross-sectional variance in net while gross explains 2.5%.**

**The signal is real and it is 9.4% of the cost of expressing it: +0.231 bps against a 2.457 bps
round trip.** In three months, across 24 instruments, in every decile of stop width and every cost
band, the edge:toll ratio **never exceeds 0.31** (e-stack E-F6). Exactly one instrument of 24 clears
1.0.

### The corollary that kills the obvious fix

Everyone's instinct — *widen the stops so the cost is a smaller fraction of risk* — is **measured at
literally zero**, and now we know why.

- e5-F3 factorised the whole L2-F6 "adaptive stop" result into SHRINK + WIDEN + TRAIL over 15
  rule×month cells. **WIDEN — the stop move itself — measures −0.006192 to +0.002079, negative in 13
  of 15 cells.** L2 *inferred* this from algebra; e5 measured it to three decimals in three months.
- l2-F2 independently swept stop distance over a 12× range and found price-space expectancy
  invariant: the entire spread from k=0.75 to k=3.00 is 0.0055 R.

**Stop width is a bet-size dial, not an edge dial.** It scales gross and cost by the *same* factor,
so it changes the magnitude of the bleed and never its sign. The sign is fixed by
`edge_bps > cost_bps`, which is a property of the instrument and the signal and of nothing else.

### So, precisely

- **WHAT to trade — known, and better than this estate believed.** After the repairs, every one of
  24 instruments carries a positive gross edge, at t = +12.35 over 43,755 trades and three months.
  No prior session had ever seen this because the signal was buried under a fill convention worth
  +0.278 R, an order-type fiction covering 46% of the book, a scrambled cost model, and an entry
  timing defect worth −0.066 R.
- **HOW to trade — the repairs are now known** (§2 lists nine, with file:line and R). Composed they
  swing gross by **+0.104 R/trade** on the live-expressible cohort.
- **HOW to PAY — not known, and this is the binding constraint.** The toll is 18.2% of the risk
  committed at the geometry the generator emits. To make the median instrument affordable the toll
  would have to fall ~4.7×; to make the whole book affordable, ~10.6×.
- **The one lever that moves it is instrument selection on broker-true affordability**, and the
  system currently cannot express it — its affordability gate is R-denominated (a stop-width filter
  in disguise, Spearman(cost_r, 1/risk_distance) ≥ 0.9966 on 18 of 24 symbols) and it over-charges
  **GER40, the one instrument that pays, by 4.0–4.2×** through a config *refusal ceiling* used as an
  expected value.

**The owner's instinct was right and its object was wrong.** We are not over-engineering around an
edge that is there — we are engineering around an edge that is there *and is a tenth of the toll*.
The suppression is real (§2 prices it at +0.104 R/trade), it just is not the whole gap.

---

## §2 — THE RANKED LEVER LIST

Ranked by **expected value on the live-expressible book**, with double-counting removed.

**Why the naive ranking is wrong.** The e-coherence lane established the identity that governs every
number in this swarm:

```
per-opportunity delta  =  SELECTION  +  ABSTENTION
ABSTENTION = -(1 - keep_rate) x mu_pool
```

Abstention is free money whenever the pool is negative. It has **no ceiling and no skill** — a rule
that declines everything scores the entire deficit. Measured, only ONE mechanism in the whole swarm
is majority-SELECTION (dropping past-stop rows, 76.2%); the cost gate is 16.1% selection, the fill
floor is *negative* selection. **Ranking by per-opportunity delta over-ranks every abstention rule.**
The list below ranks by R/trade on the trades you still take.

**Why the naive sum is wrong.** The 13 lane headlines sum to **1.91271 R/trade** against a 0.21750
deficit — **8.8×**. The six wave-1 levers priced alone sum to +1.266 and deliver **+0.421** together;
**66.8% is double-counted** (Jan; 65.5% Feb, 63.4% Mar). Of 30 ordered pairs, **26 are substitutes**.

---

### L1 — Emit only orders the live engine can place *(VALIDITY, not R)*

- **Mechanism.** 46.088% of the pool (12,747 rows) is a passive limit at a level the market has left.
  `l10-X3`: on 296/296 live captures `entry_price` equals the executable quote (ask for long, bid for
  short) to floating-point equality — displacement mean/median/p05/p95 all exactly 0.0.
  `TRADE_ACTION_PENDING` is defined once (`src/mt5/mt5_interface.py:63`) and referenced only by a
  risk classifier. The only entry `order_send` is `src/execution/execution.py:3534`, `action=1`
  (`TRADE_ACTION_DEAL`). **The live engine has never placed a limit order and cannot.**
- **What it subsumes.** Inside the unplaceable 46% sit: the born-past-stop artifact (100%), the
  fill-probability inversion (100%), pseudo-replication (99.6%), the stale-entry population (100%),
  and CQ's V27 candidate (103.4%). **Ten wave-1 lane headlines are this one population seen from
  different angles.**
- **Value.** Not an R/trade lever — a truth lever. Pool gross −0.21750 → **−0.05965** on the retained
  rows; every downstream measurement becomes a claim about something that can happen.
- **n / months.** 124,738 candidates / 5 months. Past-stop share 12.71 / 7.54 / 5.76 / — / — %.
- **Confidence.** MEASURED. Two independent instruments (live broker captures; born-state census).
- **Engineering.** `src/components/broader_origin_generators.py` — the seven at-market families
  already do this. `current_fvg_fill`, `current_ob_retest`, `current_breaker_re_entry` are 99.9–100%
  POI-limit and must either (a) be suspended, or (b) wait for U1/U2 (§5). **Do not convert them to
  market orders — that was tested and it is −0.48201 R/trade at t = −56.83** (§7).
- **Rank 1 because nothing else is interpretable until it lands.**

---

### L2 — Delay the entry: do not enter at the trigger bar's close *(+0.0661 R/trade)*

- **Mechanism.** All seven at-market generating families set `entry = bar.close` — the extreme of the
  bar whose extremeness *is* the trigger
  (`broader_origin_generators.py:745-752`, `:862-897`, `:1023-1032`, `:708-742`). The market gives it
  back inside sixty seconds. Mean signed R against the signal at k = 1 min:
  **−0.064669 / −0.076711 / −0.067815** (Jan/Feb/Mar) = **−0.657 / −0.831 / −1.131 bps**, i.e.
  **27–46% of an entire broker-true round trip, conceded in the first minute.**
- **Value.** +0.06689 / +0.06610 / +0.06572 R/trade (Jan/Feb/Mar), n = 14,905 / 13,966 / 14,884.
  Pooled **+0.0661**. Ladder is a step at k = 1 and flat to k = 30 (pooled TRAIL025: k0 −0.02247,
  k1 +0.03000, k2 +0.03678, k5 +0.03834, k20 +0.04122, k30 +0.04451, k60 +0.03593).
- **Confidence.** MEASURED, three months, three independent lanes reaching it by different routes
  (l7-F1 +0.0670 · e-stack E-F5 +0.0661 · e-coherence reproduced the January cell exactly).
- **Engineering.** One change: place the market order at the close of the bar *after* the trigger.
  k = 5 M1 bars is the safe rung (interior of the plateau, not its edge).
- **Caveat.** l7 also found a directional *inversion* at delay 0 (+0.0764 R/trade, t 8.71) that is
  81% gone in two minutes. **Do not flip the side.** The delay captures the same quantity without
  taking directional risk, and the inversion does not clear the non-spread cost floor
  (+0.09312 edge vs 0.10484 R of commission + slippage + swap alone, unreachable at zero spread).

---

### L3 — Replace the 2R/−1R exit with a 0.25R trail *(+0.0377 R/trade)*

- **Mechanism.** l11 proved the exit identity `value(L) = P(first touch L) × (L − E[wall mark | touch L])`
  and measured it at all 22 levels on both sides: **every fixed exit level is value-destroying**,
  because the pool *continues through* every level it touches. E[wall | touch +2R] = **+2.1458**;
  E[wall | touch −1R] = **−0.9290**. The 2R/−1R contract therefore costs **0.0455 R/trade against
  having no exit contract at all**, and both limbs are negative independently.
- **Value.** Pooled at k = 5 on the at-market cohort: INC (as shipped) +0.00067 vs **TRAIL025
  +0.03834** = **+0.0377**. It wins at *every* delay rung. Standalone at k = 0 it is +0.0431.
  e5 measured the trail in price space at +0.04704 / +0.04156 / +0.05891 with a holding-time-matched
  permutation control at **p = 0/200 in all three months**.
- **Confidence.** MEASURED, three months, permutation-controlled, and the only non-shrink component
  of the entire L2-F6 result (positive in 15 of 15 cells).
- **Engineering.** `src/research_infra/walkforward/exits.py` and the live exit packet: no target,
  stop −1R, trail 0.25R behind running MFE. **A stop armed at bar *i* must only be checked from bar
  *i+1*** — l11 measured that violating this manufactures **+0.362 R/trade** of fiction. Also note
  the intrabar convention is **not one-signed**: it flatters mean-reverting populations (+0.759 on
  `asian_fade`, B613) and penalises this continuation population by 0.019–0.036. Measure per
  population; never carry the sign.
- **Additivity with L2 is measured and near-perfect.** delay alone +0.06624, exit alone +0.04311,
  sum +0.10935, **joint +0.10392 — 5.0% overlap**. This is the only genuinely additive pair in the
  swarm.

---

### L4 — Re-denominate the cost gate: broker-true, in MONEY, not R *(+0.0157 R selection; large DECIDABILITY)*

- **Mechanism, found and cited.** The frozen spread is not a model — it is a **four-tier config
  fallback** (`v4_timewarp_simulated_live_research_loop.py:58760-58832`) and **nine symbols land on
  tier 4, which charges `max_spread_cents/100` — the *refusal ceiling* — as the *expected* spread**
  (`:58822-58832`). Proof: the implied spread is exactly constant per symbol on every row of the
  month. Consequences:
  - Per-symbol charge error runs **0.017× to 33.90×** — a scramble, not a bias. NAS100 28.5–29.3×
    over-charged in every one of five months, because the numerator is a config constant.
  - **SPX500 and NAS100 are structurally deleted.** Minimum frozen `spread_r` over all 1,943 SPX500
    rows is **0.24479** and over all 1,622 NAS100 rows is **0.16326**, both above the 0.10 cap.
    **0 of 3,565 index candidates could pass in the entire month, under any circumstance.**
  - **GER40 — the one instrument that pays — is a tier-4 ceiling symbol** (`config/agent_config.yaml:4514`,
    `max_spread_cents: 500` → charged 5.0 price units) and is over-charged **4.0–4.2×**.
- **Value, stated honestly and in three parts** (e-coherence A2 adjudicated the L5/L8/L12 conflict):
  - **RE-ACCOUNTING: +0.473864 R/trade pool-wide and ZERO dollars move.** This is a bookkeeping
    correction, not profit. Every prior citation of it as recoverable value is wrong.
  - **SELECTION: +0.015695 R/trade** — the genuine value of gating on per-symbol broker truth instead
    of the frozen model, at matched population.
  - **DECIDABILITY: 3,565 index rows/month restored to evaluability**, including the winner.
- **The gate selects almost perfectly on its own error.** 100% of the overcharge sits on rows the
  gate REFUSES (+0.6521); on rows it ADMITS the error is **−0.0315** and in two of five months it
  *under*-charges. That is why the repair is not worth its headline.
- **n / months.** 5 months, all 124,738 rows; second instrument (`src/costs/spread_model.py` era-true)
  reproduces the ratio at 3.22 / 2.90 / 2.96 / 3.04 / 2.93.
- **Engineering.**
  1. Delete the ceiling branch from the expected-cost path. A refusal rail is not an expectation.
  2. Source the spread from `src/costs/spread_model.py` era-true per symbol.
  3. **Gate in money, not R.** `cost_r` is a rank-perfect proxy for `1/stop_distance` — Spearman
     exactly **1.0000** on four symbols and **≥ 0.9966** on eighteen. The gate has never been a cost
     gate; it is a stop-width filter.
  4. **Threshold: broker-true all-in round trip ≤ 2.5–3.0% of the money at risk.** l5-F6 measured the
     zero-crossing between **$25 and $30 per $1,000 risked**, on both truth sources and both outcome
     columns. The incumbent permits $150 (and $300 on a 2%-risk candidate).
  5. **Delete the separate `spread_r ≤ 0.10` limb** (`broker_net_cost_engine.py:859-866`). It binds
     **84.4% of all 20,448 refusals**, and its *exclusive* refusals are the only profitable refusals
     anywhere in the gate stack: n = 373, gross **+0.16942** (3.20 SE), win **56.30%** vs a pool
     39.72%, **net-positive at broker truth (+0.08886)**.

---

### L5 — Instrument affordability: the only remaining conditioning axis that works

- **Mechanism.** See §1. Gross is flat across the cost ordering (Spearman −0.157); cost spans 7.4×;
  Spearman(net, cost) = **−0.980**; cost explains **89.65%** of cross-sectional net variance.
- **Value, measured as cumulative baskets ordered by broker-true `cost_r`:**

  | basket | n | gross | cost | net | edge:toll |
  |---|---:|---:|---:|---:|---:|
  | GER40 only | 1,858 | +0.06465 | 0.0466 | **+0.01804** | **1.387** |
  | + NAS100 | 3,762 | +0.04392 | 0.0491 | −0.00520 | 0.894 |
  | + US30_cash | 5,704 | +0.04005 | 0.0501 | −0.01002 | 0.800 |
  | + XAUUSD | 7,700 | +0.04175 | 0.0556 | −0.01381 | 0.751 |
  | 4 cheap indices | 7,706 | +0.04563 | 0.0634 | −0.01778 | 0.720 |
  | 6 equity indices | 11,183 | +0.04062 | 0.0749 | −0.03423 | 0.543 |
  | ALL 24 | 43,755 | +0.03834 | 0.1818 | −0.14349 | 0.211 |

- **Confidence.** MEASURED on 3 months. **GER40 is positive in all three and monotonically improving
  (+0.012 / +0.019 / +0.023), t = +1.23 on n = 1,858.** That t clears no bar — it is a lead, not a
  result. The *basket ordering* is what is solid; the individual survivor is thin.
- **Engineering.** A per-symbol admission gate on measured broker-true `cost_r` at the emitted
  geometry. Note the axis must be `cost_r` (toll ÷ risk), **not** `cost_bps` — filtering on
  `cost_bps < 1.0` admits FX majors whose bps toll is low but whose emitted stops are so tight that
  the R toll is 1.7× the index basket's, and the ratio *falls* to 0.335.
- **Excludes on the evidence:** UKOIL_cash (edge:toll 0.045, true toll 97% of risk), USOIL_cash
  (0.103, 99%), ETHUSD (0.012), USDCAD (0.078), EURGBP (0.119).

---

### L6 — Delete the five `execution_fill_probability` floors *(0.0000 R on the live book — this is the swarm's biggest double-count)*

- **Four wave-1 lanes made this their headline** (L4-F8, L6-F3, L9-F1, L12-F1), and on the POOL they
  are all correct and enormous: the refused cohort is **+0.0837 R/trade better** than the kept one
  across 112,116 candidates in 5 months at **t = +11.19**, with zero reversals in 569 conditioning
  cells.
- **On the live-expressible cohort it is identically zero.** `execution_fill_probability` takes
  exactly **two values** there (0.92 on 14,708 rows = 98.64%, 0.95 on 107) and **zero rows fall
  below any configured floor** (0.45 / 0.70 / 0.80). `poi_execution_lifecycle.py:164-176` hardcodes
  0.92 for any entry at or through the market — so the field is a *flag for "this is a market
  order"*, and the floor cannot fire on an order the live engine can place.
- **Verdict: delete them as a correctness item, bank ZERO for them.** Any plan that adds the
  +0.0837 to a live projection is double-counting L1.
- **Second sign error in the same family:** l12 measured Brier skill **−9.756** and called the model
  useless. e4 re-measured it against **March's own engine limit-fill verdict** (128,596 ledger rows,
  43,231 filled / 86,773 not) and got **+0.5194**, Spearman +0.675, monotone in all ten deciles.
  l12's −9.756 was measured on a population that is **100% fill-conditioned by construction**.
  **The model has real skill; the floors are pointed the wrong way; neither matters on a market order.**
- **Config sites to remove:** `config/agent_config.yaml:794, 798, 801, 811, 1002`.

---

### L7 — Delete the eight inert or sign-inverted gate predicates *(0.0000 R by construction; large simplification)*

Measured by l6 over all 27,658 rows:

| predicate | unique blocks | verdict |
|---|---:|---|
| `selector_v4_calibrated_min_probability` 0.58 (`config:810`) | **0 of 27,658** | never fires — `candidate_probability` min is 0.584298 |
| scheduler min probability 0.58 (`config:1001`) | **0 of 27,658** | never fires, same reason |
| P3 `ev_negative` | 0 unique (6,453 blocked) | strict subset of the cost gate |
| P4 `min_ev 0.10` | 0 unique (7,268) | strict subset |
| P6 `fill_floor 0.45` | 0 unique (3,407) | strict subset + L6 |
| P8 `min_expected_net` | 0 unique (8,107) | strict subset |
| `numeric_confluence_structured_disagreement` (`selector_v4.py:4644-4648`) | 484 rows | **SIGN-INVERTED**: the demoted cohort is +0.15367 gross / **+0.1534 honest / 67.15% win** — the best identifiable cohort in the pool |
| `package_positive_reduce_risk_signed_authority_invalid` | 247 rows | **a cryptographic signing failure**, not an economic test; the cohort is **+0.23213** gross and survives dedup at **+0.27619** on 37 distinct setups |

- **The stack is strictly dominated by its own first gate.** All 2⁸ subsets enumerated: the as-shipped
  8-gate stack yields 2,986 trades at −0.11062; **its cost gate ALONE yields 7,584 at −0.07056.**
  The other seven gates subtract 0.04006 R/trade and 60.6% of the trades.
- **At the full stack, removing `A1_STOPVALID` or `A2_NOMKT` changes the book by EXACTLY ZERO** in
  all three months; the six ablation marginals sum to 5.0–7.6% of the joint effect. The stack is so
  over-determined that any single gate can be deleted with no measurable consequence.
- **The EV gate is the cost gate wearing a different name.** `selector_v4.py:3827-3832` takes a
  `min()` over four estimators, and `candidate_ev_r`'s pool **minimum is +0.398495** — negative on
  **0 of 27,658 rows**. Every rejection comes from the cost-subtracted limbs. Separately,
  `candidate_ev_r` and `candidate_probability` are the *same number*: `ev = 2.5876p − 1.1148` at
  **R² = 0.99993**.

---

### L8 — Fix the EV engine's declared geometry *(+0.0245 R/trade at the selection layer)*

- **Mechanism.** The EV engine prices a 2R contract at **1.59R**: OLS `ev ~ probability` gives slope
  2.5876 / intercept −1.1148 at R² 0.99993, implying a mean reward multiple of ~1.588 against
  `take_profit_1` = exactly 2.0000 R on **27,658/27,658 rows**. A further ~0.115 R is deducted as
  uncertainty. The haircut number is then compared against **absolute** floors of 0.10–1.10 R.
  Fallback constant at `src/components/probability_debate_v4.py:769`.
- **Value.** +0.0245 R/trade at t = 3.057 (p 0.0045) on the CLEAN population, and it unlocks 39.3%
  of the pool at the 0.80 floor (as shipped: 19.6%).
- **Confidence.** MEASURED, one month. Thin on months, strong on mechanism.

---

### L9 — Charge broker cost once, not three times *(+0.0149 R/trade at the selection layer)*

- **Mechanism.** The ranking objective's mean marginal `d(score)/d(cost)` is **−3.706** against an
  intended −1.000: **3.71× over-charged in ranking units.** The guard that was supposed to prevent it
  (`moonshot_scheduler_v4_best_trade_allocator.py:19329`) tests `value_source == 'decision_time_expected_net_r'`,
  but `_candidate_value` (`:15714-15722`) returns `ev_r` **first** and stamps `'decision_time_ev_r'`,
  and `candidate_ev_r` is populated on 27,658/27,658 rows — **so the guard is structurally unreachable.**
- **Value.** +0.0149 R/trade, t 2.379, p 0.0170.
- **Also delete:** three of the fifteen score components (`confidence`, `source_completeness`,
  `uncertainty_penalty`) have **exactly one distinct value across 27,658 rows** and add a fixed
  +0.190 to every candidate — they can never change a ranking.
- **And know this before touching the allocator:** on the CLEAN population the whole 15-component
  score and a **random pick from the same window are 0.0005 R apart** (−0.1213 vs −0.1218, n = 1,966
  windows). Everything it beats random by on the raw pool is L1's artifact.

---

### Levers priced and REJECTED (report, do not bank)

| lever | measured | why not |
|---|---|---|
| Widen the stop | **−0.0062 to +0.0021** over 15 rule×month cells | bet-size dial, not an edge dial (§1) |
| Break-even stops | +0.00275 best of five settings | `be_at_0.25` converts **5,220 winners** to scratches |
| Invert the direction | +0.0764 R at delay 0, **81% gone in 2 min** | 0.783 bps vs a 1.566 bps two-leg spread; doesn't clear the non-spread floor at zero spread |
| Convert POI limits to market orders | **−0.48201 R/trade, t −56.83** | the POI families' edge *is* the level; hard no in every cut |
| Flat 7.3× spread divisor | **−0.0316** on newly admitted rows | wrong instrument — see §6 item 6 |
| Correct costs, then re-rank | Jan −0.1213 → −0.1263 | fixing costs is not a *selection* lever |
| Member/breadth conditioning | prior estate (AF): 0 of 246 admit | refuted before this swarm |
| Family exit design | +0.0923 out-of-fit, perm p 0/400 | **does not survive dedup** (+0.0130 → −0.0391) |

---

## §3 — THE PROPOSED CONTRACT

A single, implementable specification. Every clause carries the measurement that justifies it.

### 3.1 Generation

```
ORDER TYPE          MARKET only. Never emit an entry at a price the market is not at.
                    [l10-X3: 296/296 live entries == executable quote, exactly;
                     no TRADE_ACTION_PENDING path exists]

FAMILIES ENABLED    The seven at-market families:
                      liquidity_sweep_reclaim, displacement_continuation,
                      cross_asset_lead_lag, structural_distance_extreme,
                      session_open_range_break, volatility_compression_expansion,
                      regime_transition_break
FAMILIES SUSPENDED  current_fvg_fill, current_ob_retest, current_breaker_re_entry
                    (99.9-100% POI-limit; 46.088% of the pool; unmeasurable live)
                    -> gated on U1/U2 (§5), NOT deleted.

ENTRY INSTANT       close of the M1 bar 5 minutes AFTER the trigger bar.
                    [+0.0661 R/trade pooled; ladder flat k=1..k=30; k=5 is interior]
                    Rationale: entry = bar.close is the trigger bar's own extreme;
                    the market concedes 0.657-1.131 bps of it in the first 60 seconds.

STOP                unchanged from the generator (structural).
                    Do NOT widen. [WIDEN measures -0.0062..+0.0021 over 15 cells]

REFUSE              if the stop price is already breached at the decision instant.
                    (Vacuous under MARKET-only; keep as a fail-closed assertion.)
```

### 3.2 Exit

```
DEFAULT (all seven enabled families):
    target        NONE
    stop          -1.0 R, fixed
    trail         0.25 R behind the running MFE
    arming rule   a stop armed at bar i is checked from bar i+1 ONLY
                  [violating this manufactures +0.362 R/trade of fiction - l11 S5]
    horizon       declared per sleeve. NOT 2 hours - that is the pool's pending-expiry
                  window (REPAIRED_PENDING_EXPIRY_MINUTES=120, v4_timewarp:378),
                  not a holding contract. The armed sleeves run 1280 M15 bars: a 160x
                  mismatch. Nothing in this pool transfers to a live holding horizon.

MEASURED PER-FAMILY DEVIATION (l11-F5, incumbent-minus-hold, whole month):
    HURT by a 2R target (never use one):
      current_fvg_fill -0.1760 | current_ob_retest -0.1248 |
      current_breaker_re_entry -0.0821 | cross_asset_lead_lag -0.0438 |
      liquidity_sweep_reclaim -0.0320 | volatility_compression_expansion -0.0173
    HELPED by a 2R target (may keep one):
      structural_distance_extreme +0.1097 | session_open_range_break +0.0893 |
      displacement_continuation +0.0331 | regime_transition_break +0.0186
    CAVEAT: per-family exit DESIGN beats a shared contract by +0.0923 out of fit and
    passes a 400x family-label permutation at p=0/400, but does NOT survive
    de-duplication (+0.0130 -> -0.0391). Ship the shared TRAIL025; treat per-family
    as a hypothesis for U4.
```

### 3.3 Cost model and gate

```
SPREAD SOURCE   src/costs/spread_model.py, era-true, per symbol.
                DELETE the four-tier fallback's ceiling branch
                (v4_timewarp_simulated_live_research_loop.py:58822-58832) from the
                EXPECTED-cost path. max_spread_cents is a refusal rail; charging it as
                an expectation over-charges 9 symbols 2.0x-33.9x, structurally deletes
                SPX500 and NAS100 (0 of 3,565 admissible in a month), and over-charges
                GER40 - the only instrument that pays - by 4.0-4.2x.

DENOMINATION    MONEY. cost_usd, not cost_r.
                [cost_r is a rank-perfect proxy for 1/stop_distance: Spearman exactly
                 1.0000 on 4 symbols, >= 0.9966 on 18]

THRESHOLD       broker-true all-in round trip <= 3.0% of the money at risk
                (~$30 per $1,000 risked; l5-F6 measured the zero-crossing at $25-$30).
                Incumbent permits $150, and $300 on a 2%-risk candidate.

DELETE          the separate spread_r <= 0.10 limb (broker_net_cost_engine.py:859-866).
                84.4% of all refusals; its exclusive refusals are +0.16942 gross,
                56.30% win, net-POSITIVE at broker truth. It is the only limb in the
                stack whose exclusive refusals make money.
```

### 3.4 Gates to remove

```
1. All five execution_fill_probability floors  (config:794, 798, 801, 811, 1002)
     sign-inverted on the pool; identically inert on a market order.
2. Both candidate_probability floors at 0.58   (config:810, 1001)
     block 0 of 27,658 rows: the belief layer's own minimum is 0.584298.
3. P3 ev_negative, P4 min_ev 0.10, P6, P8      0 unique blocks each.
4. numeric_confluence_structured_disagreement  (selector_v4.py:4644-4648)
     SIGN-INVERTED: component disagreement is a +0.15 to +0.28 R POSITIVE predictor.
5. package_positive_reduce_risk_signed_authority_invalid
     a signing ceremony refusing the pool's best cohort (+0.23213, +0.27619 deduped).
6. The three constant score components (confidence, source_completeness,
     uncertainty_penalty) - one distinct value across 27,658 rows.

OWNER DECISION, NOT MINE:
   same_symbol_daily_loss_lockout refuses +0.12887 R/trade (n=55) and daily_lockout is
   the ONLY positive class in the whole blocker census (+0.242 mean realized net).
   The economics say remove it; prop-firm drawdown discipline says keep it. n=55 is thin.
```

### 3.5 Conditioning

```
INSTRUMENT      admit only symbols whose measured broker-true cost_r at the emitted
                geometry is <= 0.08.
                ADMITS  GER40 0.0466 | NAS100 0.0516 | US30_cash 0.0519 |
                        XAUUSD 0.0713 | JP225 0.0795         (n=9,327 / 3 months)
                REFUSES the other 19, including UKOIL 0.3387, USOIL 0.3428,
                        EURGBP 0.3166, NZDUSD 0.2824, USDCAD 0.2621.
                Measured basket net: -0.01921 R/trade at edge:toll 0.678
                (vs ALL-24 at -0.14349 and 0.211).

SESSION         NONE supported on the at-market cohort. (The NY/London conditioning
                that works lives on the deep-resting cohort, which L1 deletes.)

FAMILY          NONE supported. No family-level exclusion survives de-duplication.

FIRST-EMISSION  not required: the at-market cohort is already 99.35% first-emission.
                (The POI cohort is 24.39% pseudo-replicated - another reason it is
                 suspended rather than trusted.)
```

---

## §4 — THE MEASURED BOOK

### 4.1 The live-expressible book — the one that matters

**Contract:** market order · entry delayed 5 min · TRAIL025 exit · no other change.
**Population:** at-market cohort (`entry_price` == decision-instant market price), 3 months.

| arm | n | gross R | cost R | net R | t (gross) |
|---|---:|---:|---:|---:|---:|
| **D0E0G0** as shipped (no delay, 2R/−1R, no gate) | 43,755 | **−0.065576** | 0.181834 | −0.247410 | −11.79 |
| D0E1G0 + trail only | 43,755 | −0.022470 | 0.181834 | −0.204304 | −6.25 |
| D1E0G0 + delay only | 43,755 | +0.000668 | 0.181834 | −0.181166 | +0.12 |
| **D1E1G0 + both** | **43,755** | **+0.038342** | **0.181834** | **−0.143492** | **+12.35** |
| **D1E1G1 + broker-true cost gate** | **24,490** | **+0.011260** | **0.064745** | **−0.053485** | **+3.15** |

- **Bootstrap on D1E1G0 gross** (2,000 resamples, 63 day-blocks, seed 20260806):
  **+0.038342, CI95 [+0.030076, +0.046177], P(≤0) = 0.0000.**
- **Days gross-positive: 53 of 63** — Jan 20/21 (+0.04501), Feb 17/20 (+0.03880), Mar 16/22 (+0.03123).
- **The swing from as-shipped to repaired is +0.103918 R/trade of gross**, and it is 95.0% additive
  across its two components.
- **Applying the cost gate improves net (−0.1435 → −0.0535) and makes the RATIO worse**: gross falls
  70.6% while cost falls 64.4%. Confirmed independently: edge:toll never exceeds 0.31 in any of ten
  stop-width deciles or any cost band, in any of three months.

### 4.2 The best instrument basket under the same contract

| basket | n | gross | cost | net | edge:toll | months positive |
|---|---:|---:|---:|---:|---:|---|
| GER40 only | 1,858 | +0.06465 | 0.0466 | **+0.01804** | 1.387 | **3 of 3** (+0.012/+0.019/+0.023) |
| cost_r ≤ 0.08 (5 symbols) | 9,327 | +0.04053 | 0.0597 | −0.01921 | 0.678 | — |
| 4 cheap indices | 7,706 | +0.04563 | 0.0634 | −0.01778 | 0.720 | — |
| ALL 24 | 43,755 | +0.03834 | 0.1818 | −0.14349 | 0.211 | — |

**GER40 is the only net-positive instrument of 24 and the only one positive in all three months. t = +1.23 on n = 1,858 — that clears nothing. Report it, do not size on it.**

### 4.3 The maximal stack (all six e-stack levers, retains the deep-resting cohort)

| month | trades | gross R | cost R | net R | total R | days net+ | t | max DD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-01 | 1,855 | +0.019663 | 0.072098 | **−0.052435** | −97.267 | 7/21 | −4.01 | −97.27 |
| 2026-02 | 2,368 | +0.078181 | 0.071995 | **+0.006186** | +14.648 | 9/20 | +0.49 | −89.53 |
| 2026-03 | 3,202 | +0.068450 | 0.063277 | **+0.005173** | +16.563 | 12/22 | +0.52 | −79.30 |

Day-block bootstrap P(net ≤ 0): Jan **0.965**, Feb 0.415, Mar 0.395. **Not significant anywhere.**

> **This book is the LESS trustworthy of the two and must not be quoted as the result.** Its
> positivity lives on the deep-resting cohort (depth ≥ 1R), which is exactly where the pool's
> fill-conditioning is worst: the entry-touch magnet ratio there is **5.36 / 5.52 / 5.69** across the
> three months (P(entry touched) = 1.0000 vs a distance-matched mirror at 0.176–0.187). Sized on
> XAUUSD the conditioning bias is **≈ 0.179 R/trade**. Those are also the orders the live engine
> cannot place.

### 4.4 The baseline it is measured against

| month | pool n | as-shipped gross per opportunity | trades |
|---|---:|---:|---:|
| 2026-01 | 27,658 | −0.237151 | 27,417 |
| 2026-02 | 24,239 | −0.185856 | 23,901 |
| 2026-03 | 26,500 | −0.188031 | 26,240 |

### 4.5 Bottom line in one line

> **Gross: positive, universal, significant (+0.03834 R/trade, t +12.35, 43,755 trades, 3 months,
> 53/63 days). Net: negative on 23 of 24 instruments, and the cost explains 89.65% of the
> cross-section. The system has an edge. It cannot afford it.**

---

## §5 — WHAT IS STILL UNKNOWN, PRICED

Ordered by *decision value per unit of effort*.

### U1 — Do the POI-limit families have any edge at all? *(46.1% of the book)*
- **Why unknown.** `path_final_r` returns `None` for any candidate whose entry was never traded
  (`v4_timewarp_simulated_live_research_loop.py:60309-60310`), and the pool filter requires the
  field — so **every row in every pool is a row whose limit filled.** The magnet ratio at depth ≥ 1R
  is 5.36–5.69: the pool has retained the level-touching half of the distribution and discarded the
  other half. Sized at ~0.179 R/trade on XAUUSD.
- **How to know it — and it is nearly free.** **March's raw ledger already carries the engine's own
  limit-fill verdict**: 128,596 rows, 43,231 filled / 86,773 **not** filled (e4). The pool drops
  those 86,773. Re-scoring the POI families over the *full* March ledger with non-fills booked at
  0.0 R is a **read of an artifact already on disk.**
- **Effort: ~2–4 hours, no replay, no new data. PRIORITY 1.** This is the single largest unmeasured
  quantity in the estate and it is one script away.

### U2 — Would a 3.4× wider emitted stop make the toll affordable in MONEY?
- **Why unknown.** The toll is **18.2% of the risk committed**. l10-X8 measured the live W7 book's
  stops at **0.306320%** of price against the pool's **0.090509% — 3.384×**. §1 establishes that
  widening cannot change the *sign*; what is unmeasured is the money book at fixed-fractional sizing
  across the whole cost distribution, and whether the *signal* survives being expressed at 3.4×
  (the target moves with it, so the trade is a different trade).
- **How to know it.** Re-walk the existing at-market working sets at scaled stops with
  money-denominated accounting. The substrate exists (`e5_{january,february,march}_WS_V1`).
- **Effort: ~2 hours of compute, no replay. PRIORITY 2 — it is the most decision-relevant unknown.**

### U3 — Does the +0.03834 gross edge exist outside January–March 2026?
- **Why unknown.** Three months, all 2026, one generator family. April and May at-market cohorts have
  **never been built**; e1/e2 spent only their *pool-level* economics.
- **How to know it.** e3 already built 5-month working sets on a common axis; e6 validated a bars-only
  path rebuild against the sealed CQ sidecar at **27,658/27,658 identical**. Building the April and
  May at-market cohorts and re-running §3's contract is mechanical.
- **Effort: ~1 session, no replay. PRIORITY 3.** Also answers U6 for free.
- **Note on cost:** February is the estate's used-once VAL month and has been read three times by
  this swarm. April and May pool economics were spent by e1/e2 under a pre-declared January-selected
  rule set. **March remains the only window never used for selection.**

### U4 — Is GER40 real, and is the affordability ordering stable?
- n = 1,858, t = +1.23, 3/3 months, monotone. The *ordering* (Spearman(net, cost) = −0.980) is solid;
  the *survivor* is thin. Closed for free by U3.
- **Effort: 1 hour on U3's substrate.**

### U5 — What does a 5-minute-delayed market order actually fill at, live?
- All 296 live captures are at-market at the trigger instant. Nothing measures the fill-price
  distribution of a delayed order. This is the one input that cannot be recovered from history.
- **Effort: zero compute; requires arming. Owner decision.**

### U6 — Can the live engine be given a limit-order path, and should it?
- `TRADE_ACTION_PENDING` is defined once and referenced only by a risk classifier. Adding the path is
  ~1 session in `execution.py` plus a demo test. **Do not start it until U1 answers** — otherwise it
  is a path to trades with no measured edge, and the only conversion test that exists came back
  −0.48201 R/trade.

### U7 — The February anomaly
- `current_breaker_re_entry`'s past-stop rate is **45.94%** in February against 69.42–81.78% in every
  other month. Unexplained, in the estate's used-once VAL window. **Effort: ~1 hour of generator
  inspection.**

### U8 — Does the signal survive past two hours?
- Every path in every pool is capped at **120 M1 bars** (86.12% are exactly 120) because that is the
  pending-order expiry, not a holding contract. e3 re-walked the *passive* cohort out to 24 h on raw
  M1 and found the advantage holds and its win rate rises to 34.4% at 98.4% resolution — but that is
  the cohort L1 deletes. **The at-market cohort has never been walked past two hours.**
- **Effort: ~3 hours on raw M1, no replay.**

---

## §6 — WHAT I GOT WRONG *(mandatory register)*

Every place this swarm overturned a previously published claim of this estate — or of its own
earlier lanes. Old claim, new measurement, citation.

| # | OLD claim (and where it was published) | NEW measurement | citation |
|---|---|---|---|
| 1 | **CQ's inverted-breaker V27 candidate: +11.9 net R/trade on TRAIN and January VAL**, standing at the factory family tip (`CANDIDATE_FAMILY_V27.json`, CLAUDE.md §4) | **103.4% artifact.** 81.33% of its trades have a source candidate whose stop was already breached at the decision instant; on those it wins **83.88%** and books +15.127 R; on the 596 genuinely takeable trades it wins **1.01%** and books **−2.644 R/trade** | `W0CAP2_CQ_NOLOOKAHEAD_V1.json` |
| 2 | **"EIGHT of ten families beat their own breakeven win rate"** (swarm brief, inherited from prior sessions) | Apples-to-oranges. 33.3% is breakeven at the *declared* 2.00 payoff; the pool realises **1.1768**, so its own breakeven is **45.94%** and it wins 34.68% — **11.25 pp short. At the realised payoff ZERO of ten families beat breakeven.** | l8-F0, `L8_RESWIN_V1.json` |
| 3 | **"`execution_fill_probability` is a flat constant 0.92 for every symbol and session (`poi_execution_lifecycle.py:176-178`)"** (swarm brief) | **7,400 distinct values**, range 0.0401–0.95. 0.92 is one branch (`:174-176`) covering 70.3% of rows; the else-branch is distance-scaled. Wrong line cited too. | w0-dictionary D5 |
| 4 | **"the gate is `total_cost_r` vs 0.15"** (swarm brief; inherited by every lane) | The **spread cap at 0.10 R is a separate limb in the same function** and it binds **84.4% of all 20,448 refusals** | w0-dictionary D1; `broker_net_cost_engine.py:859-866` |
| 5 | **"The frozen cost model overcharged SPREAD by 7.3–8.5×"** (established fact, measured on Jan and Mar) | Not a bias — a **SCRAMBLE**: 0.017× to 33.90× per symbol. Mechanism: a **four-tier config fallback** whose tier 4 charges `max_spread_cents/100` — the *refusal ceiling* — as the *expected* spread. Nine symbols land there. | l10-X5/X6; e1-F2; `v4_timewarp:58760-58832` |
| 6 | Consequence of 5: **l8 and l12 both concluded "correcting costs makes selection WORSE"** (−0.0316 and Jan −0.1213 → −0.1263) | Both tested the repair with the **flat 7.3× divisor** the brief supplied — an instrument l10 had already refuted. Per-symbol broker truth gives **+0.09512** (l5) / +0.015695 selection (adjudicated). **All three lanes are right about different instruments.** | e-coherence A2, `E_REALCOST_V1.json` |
| 7 | **"ZERO rows score as 'did not fill'"** (swarm brief, stated as a curiosity) | Correct, and the *reason* was never named: `path_final_r` returns `None` for unfilled candidates (`v4_timewarp:60309-60310`) and the pool filter requires the field. **Every pool in this estate is FILL-CONDITIONED by construction.** Magnet ratio at depth ≥1R: **5.36–5.69** | l7-F4; e-stack E-F7 |
| 8 | **T1 Screen B: "the exit-shape family is measured EMPTY on this pool"; "the 2R target is locally optimal among {1.5, 2, 3, 5}"** | On the takeable, fill-honest population **2R is a local MINIMUM** and the ladder improves monotonically toward no target. The exit contract is not neutral — it costs **0.0455 R/trade**, and **every one of 22 exit levels is value-destroying on both sides** | l11; `T1_SCREENS_V1.md:49-58` |
| 9 | **l10's own F7 (10.05×) and F8 (4.41×)** | **STRUCK by l10 itself** — pool-denominated `spread_r` divided by live-denominated `spread_r` across a 3.384× denominator gap | `l10_RESULT.json` → CORRECTIONS_TO_PRIOR_WORK |
| 10 | **l10: "BTCUSD 0.017×, 58× UNDER-charged"** | Spread-*only*. On **total** cost at era truth BTCUSD is **1.71–3.20× OVER-charged in every month**. The genuine undercharge is oils, and only in Q1. | e1; `E1_ERATRUE_RECOST_V1.json` |
| 11 | **l10-X11: "USDCHF +0.0117 is the only positive symbol"** | **January-only.** USDCHF five-month mean **−0.1053** on n = 3,508. **No symbol of 24 has positive mean gross over five months** on the pool instrument. | e2; `E2_DECOMP_V1.json` |
| 12 | **l12: "the fill model has NO skill — Brier skill −9.756"** | Against **March's own engine limit-fill verdict** (128,596 rows) the model scores Brier skill **+0.5194**, Spearman +0.675, monotone in all ten deciles. l12 measured it on a 100%-fill-conditioned population. | e4; `E4_MAR_CALIB_V1.json` |
| 13 | **Four lanes' headline: "the fill-probability floor is inverted and worth +0.084 to +0.228 R/trade"** (L4-F8, L6-F3, L9-F1, L12-F1) | True on the pool (5 months, 112,116 candidates, t +11.19) and **identically ZERO on the live-expressible cohort**, where the field takes two values and no row falls below any floor. | e-coherence; e-stack E-F11 |
| 14 | **w0's prior (dead) agent: two validation mismatches in the established band table** | A **comparison-tolerance bug** (1e-9 vs 1e-3), not a data defect. The established table reproduces exactly. | w0 §3a |
| 15 | **w0-capture's own V2 headline** | Built on an anchor using the M1 bar stamped at the decision minute, which under open-stamping is **entirely post-decision**. Manufactured **+0.21 R/trade** of fiction. Self-corrected. | `w0-capture_RESULT.md` §0.1 |
| 16 | **l11's own exit engine** | A stop *armed* onto a price the market had already passed booked its level instead of the last knowable price: **+0.362 R/trade** of fiction, producing a positive-net contract at t = 19.7. Self-caught. **Every exit-research engine in this estate is exposed to this defect class.** | fix at `l11_walk.py:109-122` |
| 17 | **The swarm's own shared working set** (`w0_ws.walk(require_fill=True)`) | Credits the **fill bar's own favourable extreme** — the wrong ordering for a limit approached from the far side. Worth **−0.0405 R/trade** on the trail measurement. **Every lane that walked resting rows with this helper inherits it.** | e5-F6; `E5_FILLBAR_V1.json` |
| 18 | **The naive sum of lane headlines** | **1.91271 R/trade against a 0.21750 deficit — 8.8×.** Six wave-1 levers sum to +1.266 alone, deliver **+0.421** together; **66.8% double-counted**; 26 of 30 ordered pairs are substitutes. | e-coherence; e-stack E-F1 |
| 19 | **CLAUDE.md §4 / `JANUARY_BANK.md` §3: "the reference arm's diagnostic pool carries ±38,317 R of separable opportunity, and whether ANY rule separates it is open and unmeasured at any useful resolution"** | **Now measured.** On the live-expressible cohort the separable, reachable opportunity is **+0.03834 R/trade gross = +0.231 bps**, against a 2.457 bps toll. The ±38,317 R is dominated by the fill-blind convention (+0.2776 R of fiction) and the perfect-foresight MFE ceiling (+1.8956 R), **neither of which is reachable by any policy.** | this synthesis §1, §4.1 |
| 20 | **CLAUDE.md §3 hazard framing: "the broad V4 stack's evidence is negative and unrepairable"** | Precisely: the incumbent **policy layers** are negative, and this swarm now shows the underlying **pool is gross-positive under a repaired contract** in 24 of 24 instruments. It remains net-negative. **"Unrepairable" was right about the outcome and wrong about the mechanism** — the mechanism is affordability, not absence of signal. | this synthesis §1 |

**Two structural facts about the estate's own instrumentation, also newly established:**

- **`final_blocker_class` is a substring cascade with fixed precedence, not a causal attribution**
  (`moonshot_scheduler_v4_best_trade_allocator.py:14265-14349`). `cost_authority` is tested *first*,
  so cost wins every co-blocker tie-break by construction. **`fill_realism` is the fallthrough
  DEFAULT at `:14349`** — its 148 rows mean *"no pattern matched"*, and they have been read as a
  fill-realism verdict. The 73.9% cost-authority share in every blocker census this estate has
  published is an artifact of test ordering.
- **The diagnostic pool contains ZERO executed trades and is only 18.03% of its own ledger** — the
  scoreability gate that builds it requires `not headline_r_scoreable`
  (`v4_timewarp:28130-28146`), so anything that reached execution is excluded *by construction*.
  125,767 January ledger rows were dropped.

---

## §7 — DO NOT REPEAT (dead ends, with their cost)

1. **Converting POI limits to market orders.** −0.48201 R/trade, t −56.83, n = 9,214; per-family
   −0.38 to −0.50; split-half −0.532 / −0.441. The POI families' edge *is* the level.
2. **Widening stops to make the cost affordable.** −0.0062 to +0.0021 across 15 rule×month cells.
   It is a bet-size dial.
3. **Break-even stops.** Not merely useless — destructive. `be_at_0.25` converts 5,220 winners into
   scratches for +0.00275 R/trade.
4. **Inverting the generator's direction.** +0.0764 at delay 0, 81% gone in two minutes, 0.783 bps
   wide against a 1.566 bps two-leg spread, and it fails the non-spread cost floor even at zero
   spread. The 5-minute delay captures the same quantity with no directional risk.
5. **Shuffled-path placebos within symbol.** Uninformative by construction — a mean-preserving
   permutation. Observed p ≈ 0.5 and excess ≈ 0.000 in all 12 cells.
6. **Reading `final_blocker_class` as causal attribution.** See §6.
7. **Improving the allocator's 15-component score.** On the CLEAN population it is 0.0005 R from a
   random pick. Three components are constants; two others are the same number (R² 0.99993).
8. **Any R-denominated improvement from a filter correlated with stop width.** That is the
   denominator, not the trade. `Spearman(cost_r, 1/risk_distance) = 1.0000` on four symbols.

---

## §8 — THE THREE THINGS TO DO NEXT

1. **Run U1 (~2–4 hours, no replay).** Re-score the three POI families over March's full ledger with
   its own limit-fill verdict, booking non-fills at 0.0 R. It decides the fate of 46% of the book
   and the artifact is already on disk.
2. **Run U2 (~2 hours, no replay).** Money-denominated re-walk at scaled stops. It decides whether
   the affordability gap is a geometry problem or a signal problem.
3. **Run U3 (~1 session, no replay).** Build the April and May at-market cohorts and re-run §3's
   contract. It is the only out-of-sample test of the one positive result this swarm produced.

**None of the three requires a sealed replay, the VPS, or an owner decision.** Everything that does
require an owner decision (U5, U6, the daily-lockout question, and any change to armed sizing) is
flagged as such and none of it is on the critical path.

---

*Every artifact cited lives in*
`docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/`.
*Read the lane `_RESULT.md` before relying on any number above; this document is an index with the
decisive figures inlined, not a replacement for the receipts.*
