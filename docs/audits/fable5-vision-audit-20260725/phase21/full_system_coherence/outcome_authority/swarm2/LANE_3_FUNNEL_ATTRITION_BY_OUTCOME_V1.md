# Lane 3 — the funnel attrition audit, candidate by candidate, labelled by realized outcome

**The owner's question, verbatim:** *"did the swarm study whats wrong exactly in afterwards how do we
lose the positive candidates eventually and how do we keep allowing the negatives in"*

Nobody had answered it. Prior work established that the *ranker has no skill* and the *pool has no
drift*; neither is the same question. This lane traces **632,934 candidate occurrences** across the
five sealed-read months of 2026 (February, April, May, June, July) through **every gate of the frozen
funnel**, stamps each one with the first gate it failed, and joins that to its **realized M1
lifecycle outcome**.

**Scope discipline.** Measurement only. Nothing here touched a broker, a live config, a
decision-contract-bound file, or git. All computation ran from the sealed row cache and `/private/tmp`;
receipts under `lane3_receipts/`.

---

## 0. The answer in six lines

| # | finding | number |
|---|---|---|
| **1** | **The minimum-predicted-R gate (`pred ≥ 0.10`) is ANTI-SELECTIVE on realized outcomes.** It passes bottom-decile losers **1.34× more often** than top-decile winners. | survival ratio **0.747** (W 235/546 = 43.04 %, L 177/307 = 57.65 %); E[killed] − E[passed] = **+0.0185 R/window**, CI95 [−0.0213, +0.0659], 6,988 windows, **+129.4 R** notional |
| **2** | **The rank gate is ANTI-SELECTIVE on the worst-case basis, significantly.** The argmax candidate is more censor-prone than the 40 candidates it beat. | +0.0660 R/candidate, CI95 **[+0.0469, +0.0864]** (excludes 0), 370,199 candidates, **+24,437 R** notional; censor rate **18.18 % top vs 11.84 % beaten** |
| **3** | **The ranker's decision-point skill is significantly NEGATIVE.** It picks a winning candidate *less* often than a coin. | P(pick is positive) **0.0722** vs uniform **0.0862**, Δ **−0.0140** CI95 [−0.0228, −0.0040] **p 0.006**, n 7,558 windows; P(pick is THE best) **0.0184** vs **0.0264**, Δ −0.0080 CI95 [−0.0117, −0.0041] **p 0.001**, n 7,427 |
| **4** | **THE LIMIT-ABSTAIN NUMBER — the hypothesis is refuted, with a p-value.** The rule does *not* discard the cheap half of the book. Abstaining avoided **−73.63 R** of realized loss over five months, against a five-month book of **+0.95 R**. | −0.04326 R/abstained window, CI95 [−0.08991, −0.00261], **p 0.038**, 1,959 windows. Substituting a MARKET candidate instead is **2.15× worse still**: −158.60 R, p 0.001 |
| **5** | **The book's entire month-to-month record is a zero-mean within-window selection term.** February's PASS and July's collapse are the same coin. | book +0.954 = pool **−5.146** + selection **+6.101**; monthly selection **+16.04 / −5.91 / +4.96 / +3.58 / −12.57**; pooled selection/window +0.0216 CI95 [−0.0897, +0.1410] **p 0.734** |
| **6** | **The mechanism, in one sentence.** The ridge predicts `terminal_net_r` on a population where 70.5 % of LIMIT candidates — **84.8 % of the resolved LIMIT rows it trains on** — carry exactly 0.0 R (`RESOLVED_NO_FILL`), so a high prediction means *"this order will actually fill"* — and in a pool whose mean is negative, filling is the adverse event. | top-of-window prediction decile **D10** has the worst realized mean of all ten (**−0.0765 R**), the highest STOP rate (17.6 % vs 2–8 %) and the lowest no-fill rate (50.9 % vs 68–81 %) |

**The two answers to the owner's two halves.** *We lose the positive candidates at the rank gate* —
60.3 % of all winners die there, and the ranker's promoted set is measurably less winner-rich than a
random draw from the same window. *We keep allowing the negatives in through the 0.10 minimum-predicted
bar* — it is the one gate whose survivors are enriched in losers relative to winners, and it decides
75.7 % of all decisions.

---

## 1. Instrument — an EXACT reproduction, not an approximation

The three sealed reads chain prequentially (February r2 → April+May r3 → June+July r4), refitting the
ridge **every day** on everything read before it. `step2_daily_refit.py` reproduces that single
continuous pass from the sealed row cache and the dev+January bootstrap
(`w21_predecision_ridge.py:load_all`, 468 s), and emits a prediction for all **382,181** eligible
occurrences.

**It reproduces all three sealed reads exactly.**

| read | sealed dispositions | reproduced | sealed book (actual R) | reproduced |
|---|---|---|---|---|
| February 2026 | `top_below_0p10` 1,164 / `top_limit_abstain` 601 / `trade` 106 | **1,164 / 601 / 106** | +14.168399 | **+14.1684** |
| April + May 2026 | 2,712 / 718 / 67 | **1,447+1,265 / 344+374 / 50+17** = 2,712 / 718 / 67 | −7.742114 / +5.130257 | **−7.7421 / +5.1303** |
| June + July 2026 | 3,112 / 640 / 117 | **1,575+1,537 / 414+226 / 49+68** = 3,112 / 640 / 117 | +3.963843 / −14.566020 | **+3.9638 / −14.5660** |

The populations match to the row: `occurrences` 264,122, `eligible_occurrences` 154,474,
`resolved_eligible_occurrences` 136,680 for June+July, and identically for the other two
(`lane3_receipts/step1_validation.json`). **No caveat is needed on any number below.**

### 1.1 The gates, read from the code and not from a sketch

The commission's sketch named a "live cluster cap". **There is none** — `select()` has exactly the
gates below and nothing else.

| gate | site | predicate |
|---|---|---|
| **G0** geometry | `w21_predecision_ridge.py:249-255` | `predecision_geometry_valid` |
| **G1** cost ceiling | same, `MAX_COST_R = 0.20` at `candidate_funnel_analysis.py:52` | `isfinite(cost_r) and cost_r <= 0.20` |
| **G2** same-symbol occupancy | `w21_score_feb_market_top_r2.py:240-246` | `row["symbol"] not in active` |
| **G3** rank | `:250` | `max(available, key=(prediction, −cost_r, key))` — **one survivor per window** |
| **G4** minimum predicted | `:251-253`, `MIN_EXPECTED_NET_R = 0.10` at `candidate_funnel_analysis.py:53` | `prediction >= 0.10` |
| **G5** MARKET-top-abstain | `:254-256` | `proposed_order_type == "MARKET"` |

**`proposed_order_type` is a pure function of `origin_family`** (`candidate_funnel_analysis.py:80-81`):
LIMIT iff family ∈ {`current_fvg_fill`, `current_ob_retest`, `current_breaker_re_entry`}. G5 is
therefore **a three-family exclusion wearing an order-type label**, and it is the single most
consequential fact about it.

---

## 2. (A) The gate-by-gate attrition ledger

Every candidate is stamped with the **first** gate it fails. `reached` = candidates alive at that
gate. Two outcome bases, both of which the estate uses: **actual** (resolved rows only, censored
excluded) and **worst-case** (`s2.summary:264-274`: resolved → `terminal_net_r`, censored →
`−1 − deductible_cost_r`). CI95 is a **day-clustered bootstrap** (2,000 draws, trading day as the
cluster unit, both arms resampled on the same day draw). `rank_metric` = (E[killed] − E[passed]) ×
n_killed, per the commission.

### 2.1 Pooled, five months, 632,934 occurrences — ACTUAL basis

| gate | reached | killed | kill % | E[killed] | E[passed] | diff | CI95 | rank metric (R) | anti-selective |
|---|---:|---:|---:|---:|---:|---:|---|---:|:--:|
| G0 geometry | 632,934 | 5,619 | 0.9 % | n/a¹ | −0.0636 | — | — | — | . |
| **G1 cost > 0.20** | 627,315 | **245,134** | **39.1 %** | **−0.1315** | −0.0234 | **−0.1081** | [−0.1174, −0.0990] | **−26,509.9** | . |
| G2 symbol occupied | 382,181 | 2,745 | 0.7 % | −0.0619 | −0.0231 | −0.0388 | [−0.0706, −0.0056] | −106.6 | . |
| G3 lost rank | 379,436 | **370,199** | **97.6 %** | −0.0231 | −0.0230 | −0.0001 | [−0.0167, +0.0181] | −35.8 | . |
| **G4 pred < 0.10** | 9,237 | 6,988 | 75.7 % | −0.0181 | −0.0366 | **+0.0185** | [−0.0213, +0.0659] | **+129.4** | **YES** |
| G5 LIMIT-top abstain | 2,249 | 1,959 | 87.1 % | −0.0433 | +0.0034 | −0.0466 | [−0.1734, +0.0780] | −91.4 | . |

¹ all 5,619 geometry-invalid rows are censored by construction (`CENSORED_GEOMETRY`), so they have no
actual; their worst-case is −1.0859 each.

### 2.2 Pooled — WORST-CASE basis

| gate | E[killed] | E[passed] | diff | CI95 | rank metric (R) | anti-selective |
|---|---:|---:|---:|---|---:|:--:|
| G0 geometry | −1.0859 | −0.2240 | −0.8619 | [−0.8716, −0.8525] | −4,843.0 | . |
| G1 cost > 0.20 | −0.3470 | −0.1451 | −0.2019 | [−0.2143, −0.1897] | −49,501.4 | . |
| G2 symbol occupied | −0.1518 | −0.1450 | −0.0067 | [−0.0640, +0.0453] | −18.5 | . |
| **G3 lost rank** | −0.1434 | −0.2095 | **+0.0660** | **[+0.0469, +0.0864]** | **+24,437.4** | **YES** |
| G4 pred < 0.10 | −0.2265 | −0.1565 | −0.0700 | [−0.1151, −0.0214] | −489.4 | . |
| G5 LIMIT-top abstain | −0.1759 | −0.0250 | −0.1509 | [−0.2937, −0.0187] | −295.6 | . |

### 2.3 Ranked by total R thrown away — **the two anti-selective gates, named**

| rank | gate | basis | rank metric | significance |
|---|---|---|---:|---|
| **1** | **G3 — the rank gate** | worst-case | **+24,437 R** | CI95 **excludes zero** |
| **2** | **G4 — the 0.10 minimum-predicted bar** | actual | **+129.4 R** | CI95 includes zero |

Every other gate is **pro-selective on both bases**, and the cost gate is pro-selective by an order of
magnitude more than anything else is anti-selective: it removes 245,134 candidates carrying
**−26,199 R of realized loss** (worst-case −85,070 R).

**Read the rank metrics as notional, not recoverable.** Only one candidate per window can ever be
traded, so "reversing" G3 for 370,199 candidates is not an available action. The *feasible* reversal
at each window-level gate is one candidate per window, and those are quantified in §4 and §6.

### 2.4 Per month — where the anti-selectivity lives

Anti-selective flags, **actual / worst-case** basis (`A` = E[killed] > E[passed]):

| gate | feb | apr | may | jun | jul |
|---|:--:|:--:|:--:|:--:|:--:|
| G1 cost | . / . | . / . | . / . | . / . | . / . |
| **G3 rank** | . / . | **A / A** | . / **A** | **A / A** | **A / A** |
| **G4 min-pred** | **A** / . | . / . | . / . | . / . | **A** / . |
| G5 abstain | . / . | **A** / . | . / . | **A / A** | **A / A** |

**February is the only month in which the rank gate is not anti-selective.** That is the same month
that produced the estate's one PASS. §5 shows the two facts are the same fact.

---

## 3. (B) The winner autopsy

Winners = top realized decile of the resolved population (threshold **> 0.0000 R**, n **51,747**, mean
**+1.2488 R**). Losers = bottom decile (**< −1.0200 R**, n **46,207**, mean **−1.3427 R**). The
decile thresholds are degenerate at 0 because **61.4 % of the population (388,912 of 632,934 rows) is
LIMIT that never filled** — an artifact I control for in §3.2.

### 3.1 Death-gate histograms

| death gate | winners n | winner share | losers n | loser share | all resolved n |
|---|---:|---:|---:|---:|---:|
| G1 cost > 0.20 | 19,762 | 0.38190 | 29,646 | **0.64159** | 199,227 |
| G2 symbol occupied | 216 | 0.00417 | 169 | 0.00366 | 2,493 |
| **G3 lost rank** | **31,223** | **0.60338** | 16,085 | 0.34811 | 326,379 |
| G4 pred < 0.10 | 311 | 0.00601 | 130 | 0.00281 | 5,574 |
| G5 LIMIT-top abstain | 115 | 0.00222 | 117 | 0.00253 | 1,702 |
| **TRADED** | **120** | 0.00232 | 60 | 0.00130 | 282 |

**Winners and losers do NOT die at the same gates.** Losers die at the **cost gate** (64.2 % of them);
winners die at the **rank gate** (60.3 % of them). The funnel's upstream half works: it is a loser
filter. The downstream half is where the winners are consumed.

### 3.2 The conditional form — the number that actually decides it

A death-gate share confounds "this gate killed me" with "an earlier gate did". The honest instrument
is **survival conditional on reaching the gate**:

| gate | winner survival | loser survival | **ratio (W/L)** | verdict |
|---|---:|---:|---:|---|
| G0 geometry | 1.0000 | 1.0000 | 1.000 | neutral |
| **G1 cost > 0.20** | **0.6181** (31,985/51,747) | **0.3584** (16,561/46,207) | **1.725** | strongly pro-selective |
| G2 occupancy | 0.9932 | 0.9898 | 1.003 | neutral |
| **G3 rank** | 0.0172 (546/31,769) | 0.0187 (307/16,392) | **0.918** | **anti-selective** |
| **G4 min-pred** | 0.4304 (235/546) | **0.5765** (177/307) | **0.747** | **anti-selective** |
| G5 abstain | 0.5106 (120/235) | 0.3390 (60/177) | 1.506 | pro-selective |

**MARKET-only control** (74,249 resolved candidates, every one of which fills, so no NO_FILL
denominator; deciles **> +1.6929** and **< −1.4603**):

| gate | winner survival | loser survival | ratio |
|---|---:|---:|---:|
| **G1 cost** | 0.6276 (4,660/7,425) | **0.0998** (741/7,425) | **6.289** |
| G2 occupancy | 0.9927 | 0.9879 | 1.005 |
| **G3 rank** | 0.0136 (63/4,626) | 0.0150 (11/732) | **0.906** |
| G4 min-pred | 0.6032 (38/63) | 0.6364 (7/11) | 0.948 |
| G5 abstain | 1.0000 | 1.0000 | 1.000 (a MARKET top is never abstained) |

**The cost gate is a 6.3× loser filter on MARKET candidates** — it removes 90.0 % of the big losers and
only 37.2 % of the big winners. Nothing else in the funnel comes close. Conversely G3 and G4 both sit
below 1.0 in both populations: **the only two gates in the funnel that see the model's opinion are the
only two that prefer losers.**

*Adversarial note, and it matters.* The MARKET-only G4 ratio (0.948, n 74) is much milder than the
all-population 0.747 (n 853). The strong G4 anti-selectivity is therefore carried by **LIMIT** tops,
not MARKET tops — consistent with §6's mechanism. Both are reported; neither is suppressed.

---

## 4. (C) The MARKET-top-abstain rule — the commission's headline question

> *"LIMIT orders execute at or better than a chosen price — they are the cheaper execution side… the
> rule may be systematically discarding the cheap half of the book."*

**Measured, and refuted.** Over the five sealed months the rule abstained from **1,959** decision
windows. Abstaining books exactly **0 R**, so the counterfactual mean *is* the rule's value with the
sign flipped.

| arm on the 1,959 abstained windows | n resolved | total actual R | mean/window | CI95 (day-clustered) | p |
|---|---:|---:|---:|---|---:|
| **abstain (shipped)** | — | **0.00** | 0.0000 | — | — |
| take the LIMIT top (`mixed` at the top slot) | 1,702 | **−73.63** | **−0.04326** | [−0.08991, −0.00261] | **0.038** |
| substitute the best MARKET candidate (`market_rerank`) | 1,545 | **−158.60** | −0.10265 | [−0.15766, −0.04815] | **0.001** |
| take the cheapest candidate in the window | 1,774 | −2.48 | −0.00140 | [−0.02451, +0.02109] | 0.902 |
| rank-2 instead of rank-1 | 1,730 | −33.50 | −0.01937 | [−0.04324, +0.00568] | 0.121 |
| *oracle ceiling (unattainable)* | 1,947 | *+2,959.30* | *+1.51993* | *[+1.46304, +1.57594]* | *0.000* |

**The rule is worth +73.63 R over five months against a five-month book of +0.95 R.** Without it the
funnel's actual result is **−72.68 R**. It is the single largest positive contributor to the record.
And the substitution alternative — the intuitive "trade something else instead" — is **2.15× worse
than taking the LIMIT top and 158.6 R worse than abstaining**, at p 0.001.

Whole-policy confirmation at full fidelity (five-month pooled, all occupancy knock-on included):

| policy | trades | actual R | worst-case R |
|---|---:|---:|---:|
| **`market_top_abstain` (shipped)** | 290 | **+0.954** | **−7.263** |
| `market_rerank` | 333 | −9.279 | −18.517 |
| `mixed` | 959 | −27.299 | −145.204 |

### 4.1 Why the "cheap half" intuition fails — and the number that replaces it

Of the 1,702 resolved abstained tops: **1,389 (81.6 %) are `RESOLVED_NO_FILL` at exactly 0.0 R**, 140
STOP, 140 TIME_STOP, 33 TARGET; 257 more are censored. So the entire −73.63 R sits in the **313 that
filled**:

> **E[net | a LIMIT top actually fills] = −0.2352 R.**

A resting limit is cheap to *place* and expensive when it *fills*: it fills precisely when price comes
to it, which is adverse selection. The rule is not discarding a cheap half — it is declining a lottery
whose only paying tickets are losses.

Family split of the abstained tops (all three LIMIT families are negative):

| family | n | no-fill | censored | total actual R | mean |
|---|---:|---:|---:|---:|---:|
| `current_fvg_fill` | 1,102 | 744 | 134 | −49.34 | −0.05097 |
| `current_breaker_re_entry` | 729 | 548 | 96 | −22.35 | −0.03531 |
| `current_ob_retest` | 128 | 97 | 27 | −1.94 | −0.01923 |

### 4.2 Is the LIMIT fill-modelling realistic? — **yes, and it is conservative**

Read directly at `src/research_infra/walkforward/quote_side.py:1032-1400`
(`resolve_post_submission_m1_lifecycle`). The commission's worry was "does it assume a fill that would
not have happened". It does the opposite:

- a LIMIT fills **only** on a correct-side touch of the **entry-quote-shifted** bar
  (`limit_touched`, `:1248-1249`; ASK for longs, BID for shorts via `entry_quote_offset`);
- the path must be **fully contiguous verified M1** to expiry — any gap is censored, never assumed
  (`contiguous`, `:1206-1210`);
- if the **submission bar itself** already touches the limit, the row is **censored** for ordering
  ambiguity rather than filled (`:1268-1273`);
- **the barrier clock starts at the FILL index, and `terminal_gross_r` is measured from `fill_price`**
  (`:1332`, `:1345-1348`) — this is the *repaired* instrument. The decision-anchored barrier clock that
  Lane 1's `ATTRITION_RECOVERY_V1.md` §2.2 killed FB's `current_ob_retest` cell with **does not apply
  here**;
- a gap through SL or TP on the first executable quote is censored, not booked (`:1355-1362`);
- no fill → `RESOLVED_NO_FILL` at **exactly 0.0 R** — verified across all five months:
  **388,912 NO_FILL rows, min 0.0, max 0.0, mean 0.0, zero non-zero values.**

The one place it is optimistic is the standard passive assumption: an **intrabar touch** fills at the
exact limit price with no queue model (`INTRABAR_TOUCH_M1_CLOSE_UPPER_BOUND`, `:1319-1326`). That
optimism biases the LIMIT arm **upward**, which makes the abstain rule's measured +73.63 R a
**lower bound** on its value. Naming it strengthens the finding rather than weakening it.

### 4.3 What would reverse finding 4

The rule becomes a cost the moment `E[net | LIMIT top fills]` turns positive. That is a single
measurement on any unread window: **the mean realized net of the LIMIT-topped windows' tops,
conditional on fill.** Today it is −0.2352 R on n = 313. A window in which that quantity is positive
with a day-clustered CI excluding zero reverses the verdict, and nothing else does.

---

## 5. (D) Survivorship in reverse — where the taken book's R actually came from

For every traded window the realized R decomposes **exactly**, with no residual:

```
pick  =  mean_of_available        +      (pick − mean_of_available)
         ^ POOL component                ^ SELECTION component
         what a uniform random draw      what the ranker's choice
         from the same window earns      added or subtracted
```

| month | trades | book (actual R) | **pool** | **selection** | target rate | breakeven target rate¹ |
|---|---:|---:|---:|---:|---:|---:|
| February | 105 | **+14.168** | −1.874 | **+16.042** | 0.190 | 0.352 |
| April | 49 | −7.742 | −1.835 | −5.907 | 0.020 | 0.364 |
| May | 17 | +5.130 | +0.172 | +4.958 | 0.176 | 0.376 |
| June | 45 | +3.964 | +0.387 | +3.576 | 0.289 | 0.348 |
| July | 66 | **−14.566** | −1.998 | **−12.568** | 0.242 | 0.402 |
| **pooled** | **282** | **+0.954** | **−5.146** | **+6.101** | | |

¹ `mean_stop_loss / (mean_target_payoff + mean_stop_loss)`, ignoring time stops.

**The selection term dominates every month and it flips sign every month: +16.04 / −5.91 / +4.96 /
+3.58 / −12.57.** Pooled it is **+0.0216 R/window, CI95 [−0.0897, +0.1410], p 0.734** — statistically
indistinguishable from zero, with a ±14 R monthly amplitude.

> **February's PASS was +16.04 R of selection and −1.87 R of pool. July's collapse was −12.57 R of
> selection and −2.00 R of pool.** They are the same coin landing twice. The pool component is small,
> stable and mildly negative in every month (−2.00 … +0.39).

### 5.1 The −16.722 R June/July worst case, attributed

| component | R | share |
|---|---:|---:|
| ranker's within-window selection (Jun +3.576, Jul −12.568) | **−8.992** | **53.8 %** |
| the pool itself (Jun +0.387, Jul −1.998) | −1.611 | 9.6 % |
| the censoring convention (6 censored trades × −1 − cost) | **−6.120** | **36.6 %** |
| **total** | **−16.722** | 100 % |

Exit detail of the 117 trades: **29 TARGET +49.12 R, 60 STOP −61.85 R, 22 TIME_STOP +2.13 R, 6
CENSORED −6.12 R.** Mean target payoff +1.694 R against a mean stop of −1.031 R, so the geometry needs
a **37.8 %** target rate and got **26.1 %**.

### 5.2 The −2.612 R April/May pooled result, attributed

| component | R | share |
|---|---:|---:|
| the pool itself (Apr −1.835, May +0.172) | −1.663 | 63.7 % |
| ranker's within-window selection (Apr −5.907, May +4.958) | −0.949 | 36.3 % |
| **total actual** | **−2.612** | 100 % |
| censoring convention (1 trade) | −1.073 | → worst case **−3.685** |

Exit detail of the 67 trades: **4 TARGET +7.66 R, 23 STOP −24.85 R, 39 TIME_STOP +14.57 R, 1 CENSORED
−1.07 R.** April+May's target rate was **6.1 %** against a **36.1 %** breakeven; the book was held up
entirely by time stops closing in profit.

**So the two REJECTs have different causes**: June/July is 53.8 % a selection failure, April/May is
63.7 % a pool failure. There is no single defect to fix, and the censoring convention is the third
largest line item in June/July at 36.6 %.

### 5.3 "Correctly selected but badly executed" — the split the commission asked for

Of the 290 taken trades, **none** were mis-executed in a way the labeller can see. Every fill is the
first complete successor M1 open at the executable entry quote (`quote_side.py:1284-1290`); every exit
is a modelled barrier or the horizon close; and every R already carries the complete four-component
cost — `terminal_net_r = terminal_gross_r − deductible_cost_r` at
`candidate_funnel_analysis.py:173-174`, with the deductible summed at `:164`. There is no partial, no
scale-out and no re-entry in this contract, so **there is no execution/exit bucket to attribute loss
to**: every trade got exactly the contract it was scored under.

The decomposition therefore has three buckets, not the commission's two. What §5.1–5.2 calls
"selection" is the *within-window choice*; "pool" is the *candidate population's own drift*; and the
third — **censoring** — is a **bookkeeping** loss rather than an economic one, and it is 36.6 % of
June/July.

---

## 6. The mechanism — measured, not argued

Take the **9,237 top-of-window candidates** (the ones that reached G4) and bin them by their own
prediction:

| pred decile | n | mean pred | **mean realized net R** | TARGET % | STOP % | TIME_STOP % | NO_FILL % | CENSORED % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| D1 | 923 | −0.1194 | −0.0734 | 0.5 | 2.0 | 2.6 | 15.9 | **79.0** |
| D2 | 923 | +0.0219 | −0.0236 | 1.0 | 3.9 | 3.0 | 80.9 | 11.2 |
| D3 | 923 | +0.0369 | −0.0274 | 1.3 | 4.6 | 6.0 | 77.6 | 10.6 |
| D4 | 923 | +0.0473 | −0.0385 | 0.9 | 5.9 | 5.4 | 76.2 | 11.7 |
| D5 | 923 | +0.0571 | −0.0087 | 1.4 | 5.1 | 7.0 | 76.2 | 10.3 |
| D6 | 923 | +0.0681 | −0.0062 | 2.3 | 5.7 | 6.5 | 75.6 | 9.9 |
| D7 | 923 | +0.0812 | **+0.0220** | 2.5 | 4.1 | 7.2 | 73.1 | 13.1 |
| D8 | 923 | +0.0985 | −0.0292 | 2.1 | 7.4 | 6.7 | 71.6 | 12.2 |
| D9 | 923 | +0.1181 | −0.0058 | 2.9 | 7.6 | 8.8 | 68.3 | 12.5 |
| **D10** | 930 | **+0.1690** | **−0.0765** | **5.3** | **17.6** | **14.8** | **50.9** | 11.4 |

**D10 is the decile the 0.10 bar selects, and it has the worst realized mean of the ten.** Its
composition says why: as the prediction rises the **no-fill rate collapses** (81 % → 51 %) and the
**stop rate quadruples** (3.9 % → 17.6 %) while the target rate only triples (1.0 % → 5.3 %). The
model has learned to predict **"this order will actually trade"** — because **84.8 % of the resolved
LIMIT rows the ridge trains on** (`resolved_eligible`, `w21_predecision_ridge.py:240-247`) carry
exactly 0.0 R, and 0.0 is *above* the −0.0369 mean of the candidates available in a decision window —
and in a negative-expectancy pool, trading is the adverse event.

Within MARKET-only tops (n 652, where every candidate fills, so the no-fill channel is closed):

| pred quintile | n | mean pred | mean net R | TARGET % | STOP % |
|---|---:|---:|---:|---:|---:|
| Q1 | 130 | −0.0240 | −0.1640 | 9.2 | 30.0 |
| Q2 | 130 | +0.0576 | −0.2192 | 7.7 | 42.3 |
| Q3 | 130 | +0.0897 | −0.0397 | 16.2 | 37.7 |
| **Q4** | 130 | +0.1278 | **+0.0545** | 16.9 | 36.9 |
| Q5 | 132 | +0.2155 | −0.0687 | 18.9 | **48.5** |

The relation is **non-monotone with its worst point at the top**: Q5 has the best target rate *and* the
worst stop rate. The ranker is a **variance** detector, not a **direction** detector.

### 6.1 The censoring channel, which is the same defect in a second dress

`resolved_eligible` (`w21_predecision_ridge.py:240-247`) **drops every censored row from training**.
The model therefore carries no penalty for preferring candidates whose lifecycle cannot be resolved,
and it duly prefers them:

| population | n | censor rate | LIMIT share | no-fill share |
|---|---:|---:|---:|---:|
| the ranked **top** of each window | 9,237 | **18.18 %** | 92.94 % | 66.61 % |
| the candidates it **beat** | 370,199 | **11.84 %** | 88.56 % | 65.83 % |
| — LIMIT tops only | 8,585 | **19.17 %** | — | 71.67 % |
| — MARKET tops only | 652 | **5.06 %** | — | 0.00 % |

The argmax is **1.54× more likely to be unresolvable** than the average candidate it outranked, and the
estate charges every censored trade **−1 − cost**. That is the whole of G3's worst-case
anti-selectivity (+0.0660 R, CI excludes zero) and 36.6 % of the June/July worst case.

---

## 7. The ceiling — how much is actually there

Over the 9,237 windows that reached the ranker (mean **41.1** available candidates each):

| arm | n | total R | mean/window | CI95 |
|---|---:|---:|---:|---|
| **oracle — perfect within-window choice** | 8,705 | **+12,504.52** | **+1.43648** | [+1.40054, +1.46685] |
| rank-2 | 7,536 | −143.51 | −0.01904 | [−0.02986, −0.00775] |
| cheapest candidate | 7,712 | −136.37 | −0.01768 | [−0.02924, −0.00687] |
| **the shipped ranker's pick** | 7,558 | **−173.67** | **−0.02298** | [−0.04001, −0.00689] |
| uniform random draw | 8,705 | −321.03 | −0.03688 | [−0.04365, −0.03028] |
| best MARKET candidate | 6,777 | −649.75 | −0.09588 | [−0.12460, −0.06504] |
| anti-oracle — worst within-window choice | 8,705 | −8,971.56 | −1.03062 | [−1.04378, −1.01721] |

**The separability is real and enormous: +1.436 R/window sits inside these windows.** The ranker
captures **none** of it — paired against a random draw it is **+0.00066 R/window, CI95 [−0.01483,
+0.01577], p 0.897**. And restricting the choice to MARKET candidates is by far the worst rule tested,
at −0.096 R/window.

---

## 8. (E) The constructive conclusion — repairs ranked by expected R, each with its reversal

Every arm below is scored on the same five months and the same windows. **Nothing here is an admission,
a promotion, or an arming proposal**; the two never-funnel-read 2025 windows and the two reserve days
are untouched by this lane and must stay that way until a repair is pre-registered.

| rank | repair | expected R (5 months) | evidence class | reversal measurement | risk cost |
|---|---|---:|---|---|---|
| **R1** | **Retrain the ranker on `terminal_net_r` conditional on FILL, with a separate fill model** — or restrict ranking to the MARKET population where every candidate fills. The current label makes "will not trade" the highest-scoring property (§6). | unquantified; the *deficit it removes* is worth **+0.0140 in P(pick positive)** (p 0.006) and **+0.0080 in P(pick best)** (p 0.001) — restoring the ranker to *random* is worth this much, and it is currently below random | **MEASURED defect, unmeasured repair** | refit on filled-only rows; re-measure the two hit rates against the same uniform baselines (0.0862 / 0.0264). A repair that does not clear them has not worked. **Costs no new data.** | none — the arm is default-off research |
| **R2** | **Cap the prediction as well as floor it.** The shipped rule trades `pred ≥ 0.10` with no upper bound; D10 is the worst decile and MARKET Q5 has the highest stop rate. Trading the band `[0.10, cap]` improves the five-month actual at **every cap tested**. | cap 0.12 → **+9.99** (n 81); **0.15 → +11.83** (n 148); 0.18 → +8.70 (n 215); 0.20 → +2.42; 0.25 → +5.54; 0.30 → +5.48; 0.40 → +3.13; **uncapped (shipped) +0.95** | **IN-SAMPLE — hypothesis, not a finding.** The cap was chosen after seeing outcomes. The *mechanism* (§6) is independent of the cap and measured on 9,237 windows | pre-register one cap on an unread window before any belief. **This is the cheapest high-value test in the lane and it must not be run on the four 2025 validation windows** | halves-to-quarters the trade count; a cap that is too tight stands the book down entirely |
| **R3** | **Stop charging censored trades a full stop, or model censorship in the ranker.** Censoring is **36.6 %** of the June/July worst case and the argmax is 1.54× more censor-prone than the field, because censored rows are dropped from training (`w21_predecision_ridge.py:240-247`) | **+6.12 R** on June/July and **+1.07 R** on April/May as a *convention* change; as a *ranker* change, moving the top's censor rate from 18.18 % to the field's 11.84 % is worth ≈ **32 %** of that charge | MEASURED (the charge); the ranker repair is unmeasured | add censorship as a training target and re-measure the top-of-window censor rate against 11.84 % | a convention change is a **reporting** change and must not be used to make a REJECT look better — declare it as a second reported basis, never as the gate basis |
| **R4** | **Keep the MARKET-top-abstain rule and do not build on it.** It is worth **+73.63 R** (p 0.038) and is the largest positive line in the record — but it is a *trade-count* effect in a negative pool, as Lane 1 §5.4 established and this lane confirms per-candidate | keeping it: **+73.63 R**; replacing it with substitution: **−158.60 R** (p 0.001) | MEASURED both directions | `E[net | LIMIT top fills]`, today **−0.2352 R** on n 313. Positive with a CI excluding zero reverses it | none |
| **R5** | **Do not tighten the cost ceiling.** *This lane's own hypothesis, refuted by its own better instrument.* | at the month-boundary fit every tightened ceiling beat 0.20 (mean +6.1 R); at the **exact** fit the sweep is non-monotone noise (0.05 −5.60, 0.08 −5.14, 0.10 −5.88, 0.12 −9.20, 0.15 −6.37, 0.18 **+11.16**, 0.20 +0.95) and the 290 sealed trades show **no cost gradient at all** (bins: −4.82 / +7.79 / −6.29 / +4.27 R) | **REFUTED** | — | — |
| — | **Breadth of geometry is empty and it is a generator problem, not a gate problem.** Every MARKET stop-width bin is negative (best −0.0733 R at 5–10 ATR); the target/stop ratio has **only two populated bins** (1.0–1.5 and 1.5–2.0) and they are identical (−0.2657 vs −0.2757). There is no high-RR region for a gate to admit | nil | MEASURED, n 74,249 MARKET / 461,408 LIMIT | a generator emitting R:R > 2 would create the region; no gate can | — |

### 8.1 The honest ceiling on all gate work

**There is no cost band, no stop-width band and no R:R band of this pool with positive expectancy.**
The best MARKET cell measured anywhere in §7 or the geometry curves is **−0.0733 R**. Every gate repair
above is therefore a *loss-reduction*, and the loss-reduction limit is the point at which the funnel
stops trading: the min-predicted sweep reaches **0 trades and 0 R at 1.00**, and the shipped 0.10 is
already at +0.95 R over five months.

**What is not bounded is §7's +1.436 R/window of within-window separability.** That is the only
reason to keep working on this funnel, and R1 is the only repair in the table that addresses it.
Everything else in the table is worth single-digit to low-double-digit R over five months; R1 is worth
whatever fraction of **+12,504 R** a real ranker can reach, and today the ranker reaches a
*significantly negative* fraction of it.

---

## 9. Adversarial checks run against this lane's own positives

| claim I made | check | outcome |
|---|---|---|
| "the ranker picks the window's best 2.62× more often than chance (0.1117 vs 0.0426)" | restrict to windows whose best is **strictly positive** — the headline counted ties at 0.0 R among NO_FILL rows, which the ranker over-selects | **FLIPPED.** 0.0184 vs 0.0264: the ranker is **worse** than chance, p 0.001. The original number is deleted, not softened |
| "the cost ceiling should be tightened; every tested setting beats 0.20 (mean +6.1 R)" | rerun at the **exact** daily refit; then check the 290 **sealed** trades for a cost gradient | **REFUTED.** Non-monotone at exact fit; no gradient in the sealed book (§8 R5) |
| "G5 is anti-selective (E[killed] −0.0103 > E[passed] −0.0402)" | rerun at the exact fit | **REVERSED.** E[killed] −0.0433 vs E[passed] +0.0034; pro-selective on worst-case at CI excluding zero |
| "the traded book is 4.4× winner-enriched" | the traded book is 100 % MARKET and MARKET has no NO_FILL; repeat inside MARKET | **CONFOUNDED and re-reported** as the MARKET-only table in §3.2 |
| "G4 is anti-selective at ratio 0.747" | repeat inside MARKET-only | **WEAKENED to 0.948** — the effect is carried by LIMIT tops. Both reported |
| "the LIMIT labeller might assume fills that never happened" | read `quote_side.py:1032-1400` line by line | **the opposite** — it is conservative in five named ways; its one optimism (intrabar touch, no queue model) biases *toward* LIMIT and makes +73.63 R a **lower bound** |
| the whole instrument | reproduce all three sealed reads | **exact** on dispositions, populations and per-month books (§1) |

---

## 10. Receipts

`lane3_receipts/` — all JSON is machine-written by the eight scripts beside it.

| file | what |
|---|---|
| `step1_validation.json` | the sealed-read reproduction proof |
| `attrition_daily.json` | (A) the gate ledger + (B) the winner autopsy, pooled and per month |
| `ceiling_daily.json` | (§7) the within-window ceiling, the sweeps, conditional survival, rank-gate censoring |
| `repairs_daily.json` | (C) the abstain counterfactual, the cost reversal curve, the repair arms |
| `geometry_daily.json` | the geometry/cost curves and the two pick-rate tests |
| `decompose_daily.json` | (D) the pool-vs-selection decomposition and the MARKET-only autopsy |
| `funnel_lib.py`, `step1..step7*.py` | the instrument; `step2_daily_refit.py` is the exact prequential reproduction |

Inputs: `/private/tmp/w21-puzzle-cache/rows_{feb,apr,may,jun,jul}.pkl.gz` (632,934 occurrences);
the frozen chain `w21_score_junjul_r4d.py` → `w21_score_aprmay_r3b.py` →
`w21_score_feb_market_top_r2.py` → `w21_predecision_ridge.py` → `candidate_funnel_analysis.py`.
Bootstrap seed 20260812; day-clustered, 2,000–4,000 draws.
