# LANE e4 — EXTENSION of the l12 fill-probability finding

**Posture:** extension, not refutation. The question was *how far does it reach and where does it live*.
**Answer in one line:** the finding is TWO findings with opposite fates — the calibration limb is
LOCAL to January's measurement convention and inverts when tested properly, while the selection limb
**replicates in all three months, survives every artifact control, and localises to two families**.

Everything below is measured. Scripts and JSON are in this directory, prefixed `e4_` / `E4_`.

---

## 0. WHAT WAS SPENT — the estate's record

| month | source | spent by this lane | note |
|---|---|---|---|
| **January 2026** | `CJ_RECLOCKED_S0R0_POOL_V1` + `w0_WORKING_SET` + `w0cap2_DECISION_ANCHOR` | yes (already spent many times) | 27,658 rows |
| **February 2026** | `CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz` | yes — **second read** (CP was the first) | 24,239 rows |
| **March 2026** | `FA2_M_R0_MISSED_OPPORTUNITY_LEDGER.jsonl.gz` (worktree `fa2-integration-20260803`, branch `phase19/march-confirm`) | yes — already read once by the March confirm | 130,004 ledger rows / 26,500 pool rows |
| **April 2026** | — | **NO. NOT SPENT.** | `CJ_PACKS_APRIL_V2.json` is a **prepared day-pack build receipt** (raw market data), not a replayed candidate pool. Extracting a diagnostic pool requires launching a sealed replay, which this lane is forbidden to do. **No April economics were read.** |
| **May 2026** | — | **NO. NOT SPENT.** | Same. `CJ_PACKS_MAY_V1.json` is a day-pack build receipt. **No May economics were read.** |

April and May remain economics-unread for the fill question. Answering it there costs a sealed replay
(~16.5 MH/window) and, per H1, a decision-contract regeneration.

---

## 1. STEP 1 — REPRODUCTION ON JANUARY: **EXACT**

`e4_jan_repro.py` → `E4_JAN_REPRO_V1.json`. Every l12 number reproduces to the printed decimal.

### 1.1 The distance-bucket table (`mkt_r` from the no-look-ahead anchor)

| bucket | n | model fill P | realised entry-touch | gross R | honest R | win |
|---|---:|---:|---:|---:|---:|---:|
| past_stop (mkt_r ≤ −1) | 3,516 | 0.9199 | 1.0000 | −0.9948 | −0.9933 | 0.0008 |
| marketable (−1 < mkt_r < 0) | 1,265 | 0.9200 | 0.9937 | −0.2566 | −0.3141 | 0.2870 |
| at_limit (mkt_r = 0) | 14,911 | 0.9202 | 0.9846 | −0.0904 | −0.1270 | 0.3947 |
| resting 0–0.25 R | 801 | 0.8918 | 0.9988 | −0.1534 | −0.1641 | 0.3695 |
| resting 0.25–0.5 R | 840 | 0.7683 | 0.9988 | −0.1361 | −0.1402 | 0.3917 |
| resting 0.5–1 R | 1,715 | 0.6270 | 0.9994 | −0.1405 | −0.1290 | 0.3761 |
| resting 1–2 R | 2,422 | 0.4537 | 1.0000 | −0.0919 | −0.0961 | 0.4290 |
| resting 2–5 R | 1,787 | 0.3067 | 1.0000 | −0.0760 | −0.0466 | 0.4606 |
| **resting > 5 R** | **384** | **0.1745** | **1.0000** | **+0.0069** | **+0.0883** | **0.5365** |
| unanchored | 17 | 0.2693 | 1.0000 | −0.6349 | −0.6349 | 0.2353 |

l12's table, to the decimal. ✔

### 1.2 Calibration (model P vs realised entry TOUCH within the 2 h path)

| population | n | model mean | realised touch | Brier | base Brier | **skill** |
|---|---:|---:|---:|---:|---:|---:|
| ALL | 27,506 | 0.805058 | 0.991238 | 0.093416 | 0.008685 | **−9.7561** |
| CLEAN (mkt_r > −1) | 24,012 | 0.788620 | 0.989963 | 0.105836 | 0.009936 | −9.6518 |

l12 reported 0.8051 / 0.9912 / 0.09342 / −9.756. ✔

### 1.3 Selection rule, window level (1,969 windows ALL / 1,966 CLEAN)

| population / instrument | PROD_score | LOWEST_fill | HIGHEST_fill | RANDOM | paired (LOW−PROD) | perm p |
|---|---:|---:|---:|---:|---:|---:|
| ALL / gross_r | −0.134178 | +0.052528 | −0.272646 | −0.280497 | **+0.186706** | 0.00025 |
| ALL / fill_honest | −0.169845 | +0.094575 | −0.305764 | −0.287752 | **+0.264420** | 0.00025 |
| CLEAN / gross_r | −0.074298 | +0.065751 | −0.126741 | −0.139584 | **+0.140049** | 0.00025 |
| CLEAN / fill_honest | −0.119812 | +0.107697 | −0.153161 | −0.143790 | **+0.227509** | 0.00025 |

l12: LOWEST-fill CLEAN honest +0.1077 / ALL +0.0946; paired CLEAN +0.2275, ALL +0.2644, p 0.00025. ✔
(l12's PROD CLEAN honest reads −0.1213 against my −0.1198 — l12's usable set did not additionally
require `execution_fill_probability` non-null. The paired delta, which is what is claimed, is identical.)

**The instrument matches. Everything below is a genuine extension.**

---

## 2. THE CALIBRATION LIMB — REFUTED AS STATED, AND THE TRUTH IS MORE USEFUL

### 2.1 The pool every lane reads is 100 % FILL-CONDITIONED (`E4_MAR_POOLBIAS_V1.json`)

March's raw arm ledger carries a field the January and February pools do not:
`counterfactual_order_fill_status` — **the engine's own honest limit-fill simulation**.

| | n | filled | not filled |
|---|---:|---:|---:|
| whole FA2_M_R0 missed-opportunity ledger | 130,004 | 43,231 (33.25 %) | 86,773 (66.75 %) |
| **the diagnostic pool** (`…non_executable_diagnostic_scoreable = True`) | **26,500** | **26,500 (100.00 %)** | **0** |
| everything outside the pool | 103,504 | 16,731 | 86,773 |

Fill-status detail inside the pool: `filled_from_ordered_m1_path` 16,424 · `filled_from_ordered_tick_path`
4,750 · `filled_immediate_marketable_limit_at_decision` 4,617 · `filled_before_or_at_asof` 709.
Outside: `not_filled_in_post_asof_m1_path` 78,139 · `not_filled_in_post_asof_tick_path` 8,192 ·
`not_filled_passive_limit_queue_realism_not_confirmed` 281 · `not_filled_fill_realism_diagnostic_only` 161.

Model-P distribution differs completely: **pool mean 0.794079** (median 0.92, p05 0.2778) vs
**non-pool mean 0.252454** (median 0.1829, p95 0.7577). 17,913 pool rows sit at exactly 0.92 vs 3,467 outside.

**Consequence.** The brief's "ZERO rows in the pool score as *did not fill*" is not an absence of
measurement — it is the pool's *definition*. Inside a 100 %-filled population the realised touch rate is
~99 % **by selection**, and any probabilistic model with variance scores catastrophically against a
near-constant. l12's Brier skill of −9.756 is that arithmetic, not a property of the model.

### 2.2 Against the engine's OWN fill verdict the model has REAL SKILL (`E4_MAR_CALIB_V1.json`)

Full March ledger, n = 128,596 (every row with both a model P and a fill verdict):

| | value |
|---|---:|
| model mean P | 0.363900 |
| **realised fill rate** | **0.335900** |
| Brier | 0.107200 |
| base-rate Brier | 0.223100 |
| **Brier skill score** | **+0.5194** |
| **Spearman(model P, filled)** | **+0.67496** |

| decile | n | model P | realised fill | gross R (pool rows only) |
|---:|---:|---:|---:|---:|
| 1 | 12,859 | 0.0527 | 0.0080 | (none scoreable) |
| 2 | 12,860 | 0.0894 | 0.0261 | −0.257623 |
| 3 | 12,859 | 0.1232 | 0.0595 | +0.002367 |
| 4 | 12,860 | 0.1613 | 0.0938 | −0.135893 |
| 5 | 12,860 | 0.2087 | 0.1439 | −0.203121 |
| 6 | 12,859 | 0.2712 | 0.2233 | −0.122723 |
| 7 | 12,860 | 0.3690 | 0.3635 | −0.145251 |
| 8 | 12,859 | 0.5538 | 0.5669 | −0.084562 |
| 9 | 12,860 | 0.8885 | 0.9161 | −0.134513 |
| 10 | 12,860 | 0.9216 | 0.9580 | −0.249408 |

**The model is a good fill model.** 0.0527 → 0.0080 and 0.9216 → 0.9580, monotone, ten of ten.
It is not "anti-predictive on both axes it claims to predict" — it is **right about fills and wrong
about money**, and only the second half is a defect.

**This is the correct statement of the defect: a well-calibrated fillability estimate is being consumed
as a QUALITY term in five places, and fillability is negatively priced.**

---

## 3. THE SELECTION LIMB — TRAVELS TO EVERY MONTH TESTED

### 3.1 Head-to-head across three months (`E4_FEB_V1.json`, `E4_MAR_V1.json`)

Window-level single pick, gross R, full population:

| month | windows | PROD_score | LOWEST_fill | HIGHEST_fill | RANDOM | LOWEST_cost | HIGHEST_ev | **LOW−PROD** | **LOW−RAND** | perm p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| JAN (ALL) | 1,969 | −0.134178 | +0.052528 | −0.272646 | −0.280497 | — | — | **+0.186706** | — | 0.00025 |
| JAN (CLEAN) | 1,966 | −0.074298 | +0.065751 | −0.126741 | −0.139584 | — | — | **+0.140049** | — | 0.00025 |
| **FEB** | 1,888 | −0.147268 | −0.003670 | −0.205574 | −0.162071 | −0.031605 | −0.093358 | **+0.143599** | +0.158402 | 0.00025 |
| **MAR** | 2,067 | −0.150813 | −0.005089 | −0.208636 | −0.216140 | −0.134931 | −0.109580 | **+0.145724** | +0.211050 | 0.00025 |

**Paired delta on the gross instrument: +0.1400 (Jan CLEAN) / +0.1436 (Feb) / +0.1457 (Mar).**
Three independent months, three sizes within 4 % of each other. This is the single most stable number
in the lane.

March paired t = 4.885, frac of windows better 0.43348 — as in January, the gain is **magnitude, not
frequency**: the rule is wrong more often than it is right and wins on the size of its wins.

### 3.2 The pooled decile tables (for the record)

**February** (n 24,239, pool gross −0.15055, win 0.3731, mean cost_r 0.4895, model-P mean 0.8043,
17,052 rows at exactly 0.92; Spearman(fillp, gross) = **−0.06614**):

| d | n | p_lo | p_hi | gross | win | cost_r |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2,417 | 0.0439 | 0.3931 | −0.0836 | 0.4547 | 0.4705 |
| 2 | 2,417 | 0.3931 | 0.6417 | −0.0421 | 0.4638 | 0.5779 |
| 3 | 2,417 | 0.6420 | 0.9200 | −0.1487 | 0.3682 | 0.5992 |
| 4 | 2,417 | 0.9200 | 0.9200 | −0.1272 | 0.3810 | 0.4478 |
| 5 | 2,417 | 0.9200 | 0.9200 | −0.1893 | 0.3331 | 0.4290 |
| 6 | 2,417 | 0.9200 | 0.9200 | −0.1705 | 0.3260 | 0.4395 |
| 7 | 2,417 | 0.9200 | 0.9200 | −0.3835 | 0.2681 | 0.4129 |
| 8 | 2,417 | 0.9200 | 0.9200 | −0.1172 | 0.3724 | 0.4843 |
| 9 | 2,417 | 0.9200 | 0.9200 | −0.0799 | 0.4079 | 0.4937 |
| 10 | 2,418 | 0.9200 | 0.9500 | −0.1510 | 0.3598 | 0.5360 |

**March pool** (n 26,500, pool gross −0.17672, win 0.3632, mean cost_r 0.4046, model-P mean 0.7941,
17,913 rows at exactly 0.92; Spearman = **−0.05889**):

| d | n | p_lo | p_hi | gross | win | cost_r |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2,647 | 0.0774 | 0.3792 | −0.1492 | 0.4435 | 0.3822 |
| 2 | 2,647 | 0.3793 | 0.5957 | −0.0812 | 0.4348 | 0.4442 |
| 3 | 2,647 | 0.5958 | 0.9130 | −0.1524 | 0.3672 | 0.6097 |
| 4 | 2,647 | 0.9131 | 0.9200 | −0.1698 | 0.3468 | 0.3391 |
| 5 | 2,647 | 0.9200 | 0.9200 | −0.1453 | 0.3733 | 0.2847 |
| 6 | 2,647 | 0.9200 | 0.9200 | −0.0814 | 0.3955 | 0.3934 |
| 7 | 2,647 | 0.9200 | 0.9200 | −0.2301 | 0.3264 | 0.5346 |
| 8 | 2,647 | 0.9200 | 0.9200 | −0.1932 | 0.3381 | 0.3042 |
| 9 | 2,647 | 0.9200 | 0.9200 | −0.3511 | 0.2784 | 0.3574 |
| 10 | 2,648 | 0.9200 | 0.9500 | −0.2082 | 0.3297 | 0.3981 |

Note both months carry 70.3 % of their mass at exactly 0.92, so deciles 4–10 are ties — the decile view
is a weak instrument. Use §3.4 and §5 instead.

### 3.3 The thirteen config floors, replicated

| threshold | FEB below (n, gross, win) | FEB above (n, gross, win) | MAR below | MAR above |
|---:|---|---|---|---|
| 0.25 | 948, −0.1096, 0.4388 | 23,223, −0.1509, 0.3708 | 992, −0.1737 | 25,479, −0.1763 |
| 0.35 | 1,939, −0.0825, 0.4523 | 22,232, −0.1551, 0.3666 | 2,242, −0.1443 | 24,229, −0.1792 |
| 0.45 | 3,025, −0.0734, 0.4582 | 21,146, −0.1602, 0.3614 | 3,554, −0.1373 | 22,917, −0.1822 |
| 0.70 | 5,218, −0.0665, 0.4550 | 18,953, −0.1721, 0.3511 | 6,327, −0.1205 | 20,144, −0.1937 |
| 0.80 | 5,909, −0.0664, 0.4473 | 18,262, −0.1761, 0.3496 | 7,145, −0.1167 | 19,326, −0.1982 |
| 0.90 | 6,497, −0.0710, 0.4414 | 17,674, −0.1781, 0.3485 | 7,866, −0.1256 | 18,605, −0.1976 |

l12's January floor table (0.25 → 0.90) reproduces in both new months on **11 of 12 cells**; March's
0.25 cell is flat (−0.1737 vs −0.1763). **Every floor still rejects the better cohort in every month.**

### 3.4 The rule horse race — LOWEST_fill is not a proxy for anything else

`e4_rules.py` → `E4_RULES_V1.json`. Breaker family removed (see §4). Window-level pick, mean R:

| case | wins | PROD | **LOWEST_fill** | HIGH_fill | LOW_cost | LOW_spread | WIDEST_riskdist | HIGH_ev | HIGH_prob | LOWfill→cost | RANDOM |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| JAN gross | 1,966 | −0.0676 | **+0.0387** | −0.1189 | −0.0782 | −0.0849 | −0.0318 | −0.0146 | −0.0152 | +0.0454 | −0.0866 |
| JAN honest | 1,966 | −0.1109 | **+0.0821** | −0.1420 | −0.0807 | −0.0841 | −0.0244 | −0.0294 | −0.0291 | +0.0902 | −0.1108 |
| FEB gross | 1,873 | −0.0989 | **+0.0231** | −0.1078 | −0.0171 | −0.0859 | −0.0474 | −0.0618 | −0.0625 | +0.0228 | −0.0754 |
| MAR gross | 2,063 | −0.1018 | **−0.0147** | −0.1369 | −0.1045 | −0.1178 | −0.0549 | −0.0896 | −0.0895 | −0.0093 | −0.1473 |

Paired tests:

| case | LOW−PROD | t | perm p | frac windows better | LOW−RANDOM | t | perm p |
|---|---:|---:|---:|---:|---:|---:|---:|
| JAN gross | **+0.1063** | 3.36 | 0.00175 | 0.482 | +0.1253 | 4.05 | 0.00025 |
| JAN honest | **+0.1931** | 5.56 | 0.00025 | 0.417 | +0.1930 | 5.72 | 0.00025 |
| FEB gross | **+0.1220** | 3.88 | 0.00050 | 0.430 | +0.0985 | 3.23 | 0.00150 |
| MAR gross | **+0.0871** | 2.94 | 0.00300 | 0.413 | +0.1326 | 4.55 | 0.00025 |

LOWEST_fill is the **unique best rule in every month** (the only thing that touches it is
`LOWEST_fill_then_cost`, a tie-break variant of itself). It is **not** a disguised cost rule, spread
rule, geometry rule, EV rule or probability rule — every one of those is worse in every month.

---

## 4. THE ARTIFACT CONTROL — and what it kills

`e4_artifact_ctrl.py` → `E4_ARTIFACT_CTRL_V1.json`. w0-capture established that 12.72 % of the January
pool was born with its stop already breached, 98.61 % of it in `current_breaker_re_entry`, all of it
sitting at model P 0.92, all of it a mechanical −0.9948.

**Cohort comparison (passive fillp<0.92 vs marketable fillp≥0.92), gross R:**

| population | n passive | passive R | win | n marketable | marketable R | win | delta | z |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| JAN_ALL | 7,496 | −0.1014 | 0.423 | 20,010 | −0.2586 | 0.319 | **+0.1572** | 11.23 |
| JAN_CLEAN (mkt_r>−1) | 7,485 | −0.1001 | 0.424 | 16,527 | −0.1034 | 0.386 | **+0.0033** | 0.23 |
| JAN_no_breaker | 6,947 | −0.1108 | 0.420 | 16,340 | −0.1031 | 0.387 | **−0.0077** | −0.52 |
| JAN_CLEAN_no_breaker | 6,936 | −0.1094 | 0.421 | 16,292 | −0.1006 | 0.388 | **−0.0088** | −0.59 |
| FEB_ALL | 6,589 | −0.0715 | 0.440 | 17,582 | −0.1785 | 0.348 | **+0.1070** | 6.83 |
| FEB_no_breaker | 6,161 | −0.0781 | 0.434 | 15,647 | −0.0884 | 0.389 | **+0.0103** | 0.66 |
| MAR_ALL | 7,986 | −0.1277 | 0.415 | 18,485 | −0.1971 | 0.341 | **+0.0694** | 5.07 |
| MAR_no_breaker | 7,522 | −0.1356 | 0.411 | 16,822 | −0.1299 | 0.372 | **−0.0056** | −0.40 |
| JAN_ALL honest | 7,496 | −0.0902 | 0.377 | 20,010 | −0.2914 | 0.282 | **+0.2013** | 13.41 |
| JAN_CLEAN honest | 7,485 | −0.0888 | 0.378 | 16,527 | −0.1435 | 0.342 | **+0.0547** | 3.50 |
| JAN_CLEAN_no_breaker honest | 6,936 | −0.0987 | 0.373 | 16,292 | −0.1395 | 0.344 | **+0.0408** | 2.54 |

**CORRECTION TO l12's MECHANISM TABLE.** The *unconditional cohort* claim — "the far limits earn more" —
is 95–100 % the born-past-stop artifact on the gross instrument, in all three months. Once the breaker
family is out it is **−0.0077 (Jan) / +0.0103 (Feb) / −0.0056 (Mar)** — nothing.

**But the honest (fill-required) instrument survives both controls: +0.0408, z 2.54.**
And, decisively, **the SELECTION rule survives every control** (§3.4, §5): +0.1063 / +0.1220 / +0.0871
vs production and +0.1253 / +0.0985 / +0.1326 vs random, all with the breaker family removed.

---

## 5. THE MECHANISM — it is a WITHIN-WINDOW signal, and that is why the cohort test misses it

`e4_withinwindow.py` → `E4_WITHINWINDOW_V1.json`. Spearman(model P, gross R) computed *inside each
decision window* and averaged, against the same correlation computed pooled:

| case | n | pooled ρ | **within-window ρ** | t | frac windows negative | median window size | windows |
|---|---:|---:|---:|---:|---:|---:|---:|
| JAN_all | 27,658 | −0.08973 | **−0.1344** | −17.74 | 0.656 | 13 | 1,858 |
| JAN_no_breaker | 23,395 | −0.02478 | **−0.0660** | −7.55 | 0.559 | 11 | 1,826 |
| JAN_nb honest | 23,395 | −0.02835 | **−0.0796** | −8.76 | 0.562 | 11 | 1,795 |
| FEB_all | 24,239 | −0.06614 | **−0.1124** | −12.32 | 0.589 | 12 | 1,723 |
| FEB_no_breaker | 21,864 | −0.02071 | **−0.0630** | −6.51 | 0.542 | 11 | 1,695 |
| MAR_all | 26,500 | −0.05889 | **−0.1272** | −14.06 | 0.618 | 12 | 1,883 |
| MAR_no_breaker | 24,365 | −0.02185 | **−0.0843** | −8.75 | 0.564 | 11 | 1,829 |

Window sizes: JAN_nb 1,966 windows median 11 / p90 21 / max 60 / mean 11.90; FEB_nb 1,873, median 10 /
p90 20 / max 55 / mean 11.67; MAR_nb 2,063, median 10 / p90 22 / max 54 / mean 11.81.

**The within-window effect is 2.7–3.9× the pooled effect in every month.** That is the whole
reconciliation: fillability is a *relative* signal among contemporaneous candidates (same market state,
same instant), not an absolute property of a candidate. A global threshold cannot see it; a per-window
ranking — which is exactly what `moonshot_scheduler_v4_best_trade_allocator` computes — can.

---

## 6. THE BOUNDARY

`e4_fe_boundary.py` → `E4_FE_BOUNDARY_V1.json`. Within-window fixed-effects slope: R per full sweep of
the fill-probability rank from lowest to highest inside a window. **Negative = low fill probability is
worth more.** Breaker family removed unless marked.

### 6.1 Overall

| population | n | slope | se | t |
|---|---:|---:|---:|---:|
| JAN_no_breaker gross | 22,593 | **−0.11694** | 0.02666 | −4.39 |
| JAN_no_breaker honest | 22,593 | **−0.20908** | 0.02775 | −7.54 |
| FEB_no_breaker gross | 20,967 | **−0.05804** | 0.02756 | −2.11 |
| MAR_no_breaker gross | 23,349 | **−0.08651** | 0.02523 | −3.43 |
| JAN_all gross | 26,844 | −0.39369 | 0.02510 | −15.68 |
| FEB_all gross | 23,309 | −0.21282 | 0.03013 | −7.06 |
| MAR_all gross | 25,612 | −0.22334 | 0.02507 | −8.91 |

### 6.2 BY FAMILY — this is where it lives

| family | JAN slope (t) | FEB slope (t) | MAR slope (t) |
|---|---:|---:|---:|
| **current_fvg_fill** | **−0.3227 (−7.91)** | **−0.1427 (−3.57)** | **−0.2893 (−7.98)** |
| **current_ob_retest** | **−0.2123 (−2.20)** | **−0.3897 (−3.29)** | −0.1244 (−1.27) |
| structural_distance_extreme | −0.2455 (−0.97) | +0.4117 (+1.48) | +0.1262 (+0.52) |
| volatility_compression_expansion | −0.2937 (−1.21) | −0.3726 (−1.40) | +0.3965 (+1.75) |
| cross_asset_lead_lag | −0.1634 (−0.64) | +0.2011 (+0.76) | +0.0933 (+0.37) |
| liquidity_sweep_reclaim | −0.0077 (−0.04) | −0.1192 (−0.70) | +0.2552 (+1.62) |
| regime_transition_break | −0.0626 (−0.17) | +0.6951 (+1.41) | +0.3497 (+1.20) |
| session_open_range_break | +0.0955 (+0.24) | +0.3666 (+0.91) | −0.4661 (−1.60) |
| **displacement_continuation** | **+0.2641 (+1.62)** | **+0.1305 (+0.78)** | **+0.1980 (+1.34)** |

**Two families carry it, and they are the same two every month:** `current_fvg_fill` (significant in all
three) and `current_ob_retest` (negative in all three, significant in two). Both are **passive-retest
POI families** — the entry is a limit at a level price must come back to, so distance-from-market is a
real property of the setup. `displacement_continuation` is positive-signed in all three months (waiting
hurts a momentum entry), though never significant on its own.

Also in the (artifact-carrying) unconditional cohort view, `current_breaker_re_entry` shows
+0.9684 / +0.9310 / +0.8760 passive-minus-marketable in the three months — that is the born-past-stop
artifact reproducing in February and March, not an edge.

### 6.3 BY SYMBOL — indices

Negative in all three months: **SPX500** −0.3144 (−3.45) / −0.2753 (−2.47) / −0.2326 (−2.32) ·
**UK100** −0.4013 (−3.77) / −0.1593 (−1.53) / −0.2042 (−2.34) ·
**US30_cash** −0.1217 (−1.18) / −0.2061 (−1.80) / −0.2077 (−2.14) ·
EURJPY −0.1918 / −0.4256 / −0.2386. JP225 −0.4631 (−4.13) / +0.0399 / −0.2841 (−2.86).
Wrong-signed or unstable: EURUSD +0.1547 / +0.0217 / +0.3503 · USDCAD +0.2339 / +0.3859 / +0.0040 ·
CHFJPY +0.3139 / +1.0569 / +0.1812 · GBPJPY +0.0830 / +0.1264 / +0.7135.
XAUUSD is flat everywhere (−0.0699 / −0.0071 / +0.0023). Full table in `E4_FE_BOUNDARY_V1.json`.

### 6.4 BY SESSION

Negative in all three months: `moonshot_h01_02` −0.3056 (−2.30) / −0.2974 (−2.22) / −0.3442 (−3.01) ·
`moonshot_h02_03` −0.2288 / −0.3572 (−2.68) / −0.3711 (−3.04) · `moonshot_h10_11` −0.5370 (−3.29) /
−0.6250 (−3.31) / −0.1916 · `moonshot_h18_19` −0.0442 / −0.4627 (−2.82) / −0.4134 (−3.21) ·
`moonshot_h11_12`, `moonshot_h19_20`, `moonshot_h20_21` also negative in all three.
No session reverses consistently. Full table in the JSON.

---

## 7. PRICING THE CONDITIONED RULE

`e4_conditioned.py` → `E4_CONDITIONED_V1.json`. Windows restricted to the two retest families
(`current_fvg_fill`, `current_ob_retest`); pick one candidate per window.

| case | windows | candidates | mean window size | PROD | **LOWEST_fill** | HIGHEST_fill | RANDOM | **LOW−PROD** | perm p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| JAN retest gross | 1,700 | 8,478 | 4.88 | −0.1269 | **+0.0492** | −0.1733 | −0.1277 | **+0.1761** | 0.00025 |
| JAN retest honest | 1,700 | 8,478 | 4.88 | −0.1704 | **+0.1061** | −0.1995 | −0.1274 | **+0.2765** | 0.00025 |
| FEB retest gross | 1,594 | 7,898 | 4.83 | −0.1250 | **+0.0334** | −0.1414 | −0.0590 | **+0.1584** | 0.00025 |
| MAR retest gross | 1,776 | 9,473 | 5.23 | −0.1600 | **−0.0132** | −0.1817 | −0.1313 | **+0.1468** | 0.00025 |
| JAN displacement | 870 | 4,445 | 4.74 | −0.0983 | −0.0458 | −0.0464 | −0.0452 | +0.0525 | 0.13672 |
| FEB displacement | 778 | 4,029 | 4.79 | +0.0161 | +0.0730 | +0.0484 | +0.0165 | +0.0568 | 0.13947 |
| MAR displacement | 786 | 4,522 | 5.39 | −0.0246 | −0.0581 | −0.0562 | −0.0027 | −0.0334 | 0.35591 |

**Conditioning on the two families makes the rule stronger than the unconditional version in every
month** (+0.1761 / +0.1584 / +0.1468 vs +0.1063 / +0.1220 / +0.0871). And in two of three months the
conditioned rule's selected trade is **gross-POSITIVE** (+0.0492 Jan, +0.0334 Feb) against a production
score of −0.125 to −0.160. The displacement "reversal" is **not** established — three p-values of
0.137, 0.139, 0.356 and an inconsistent sign.

**Pooled three-month within-window slope, retest families: −0.23225, se 0.01642, t −14.142, n = 23,513.**

---

## 8. EX-ANTE DEPLOYABILITY — the hard limit, and the version that works

`e4_exante.py` and `e4_final2.py` → `E4_EXANTE_V1.json`, `E4_FINAL2_V1.json`.

### 8.1 The naive rule is NOT deployable ex ante

March full ledger (never-filled candidates included), pick the single lowest-model-P candidate per
window across 2,112 windows:

| rule | realised fill rate of the pick | n scored | E[R \| fill] | **R per PLACED order** |
|---|---:|---:|---:|---:|
| PROD_score | 0.8589 | 1,610 | −0.14741 | −0.12661 |
| **LOWEST_fill** | **0.0009** | 0 | — | — |
| HIGHEST_fill | 0.9342 | 1,609 | −0.22928 | −0.21419 |
| RANDOM | 0.3362 | 422 | −0.27326 | −0.09186 |

Retest-only: PROD fill 0.6492, per-placed −0.10753 · LOWEST_fill fill 0.0009 · HIGHEST_fill fill 0.8551,
per-placed −0.19358 · RANDOM fill 0.2349, per-placed **−0.03427**.
No-breaker: PROD fill 0.8456 per-placed −0.09239 · HIGHEST_fill fill 0.9299 per-placed −0.16118.

**"Always pick the single lowest modelled fill probability" fills 2 of 2,112 windows (0.09 %).** The
model's extreme tail is *correctly* identifying orders that never fill. Any lane proposing to invert
the fill term must state this: the measured selection experiment picks from a 100 %-filled pool, so it
is a **post-fill allocation rule, not a pre-fill placement rule.**

### 8.2 The version that IS ex-ante implementable, and it works in all three months

Within the two retest families only, split on the modelled fill probability at decision time (you know
at decision time whether your limit is through the market — no fill oracle needed):

| month / threshold | n below | R below | n above | R above | **delta** |
|---|---:|---:|---:|---:|---:|
| JAN / 0.45 | 3,136 | −0.0753 | 5,342 | −0.1717 | **+0.0964** |
| JAN / 0.80 | 6,220 | −0.1036 | 2,258 | −0.2253 | **+0.1217** |
| **JAN / 0.9199** | 6,947 | −0.1108 | 1,531 | −0.2503 | **+0.1395** |
| FEB / 0.45 | 2,812 | −0.0797 | 5,086 | −0.1157 | +0.0360 |
| FEB / 0.80 | 5,511 | −0.0731 | 2,387 | −0.1718 | +0.0988 |
| **FEB / 0.9199** | 6,161 | −0.0781 | 1,737 | −0.1909 | **+0.1128** |
| MAR / 0.45 | 3,310 | −0.1492 | 6,163 | −0.1911 | +0.0419 |
| MAR / 0.80 | 6,716 | −0.1250 | 2,757 | −0.3018 | +0.1768 |
| **MAR / 0.9199** | 7,522 | −0.1356 | 1,951 | −0.3343 | **+0.1988** |
| JAN honest / 0.45 | 3,136 | −0.0475 | 5,342 | −0.1832 | +0.1357 |
| JAN honest / 0.80 | 6,220 | −0.0903 | 2,258 | −0.2508 | +0.1605 |
| **JAN honest / 0.9199** | 6,947 | −0.1002 | 1,531 | −0.2821 | **+0.1820** |

The rule is: **inside a passive-retest family, do not take the marketable version of the setup — only
place the genuine passive limit.** Worth **+0.1395 (Jan) / +0.1128 (Feb) / +0.1988 (Mar)** gross R per
trade, +0.1820 on the fill-honest instrument.

**And it is NOT the past-stop artifact.** January retest families, split with and without the
born-past-stop rows:

| population / instrument | passive n | passive R | win | marketable n | marketable R | win | delta | z |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ALL / gross | 6,947 | −0.1108 | 0.420 | 1,531 | −0.2503 | 0.304 | +0.1395 | 4.86 |
| ALL / honest | 6,947 | −0.1002 | 0.373 | 1,531 | −0.2821 | 0.290 | +0.1820 | 6.41 |
| **CLEAN (mkt_r>−1) / gross** | 6,936 | −0.1094 | 0.421 | **1,483** | **−0.2281** | 0.314 | **+0.1187** | **4.06** |
| **CLEAN (mkt_r>−1) / honest** | 6,936 | −0.0987 | 0.373 | 1,483 | −0.2629 | 0.298 | **+0.1642** | **5.70** |

Only **48 of the 1,531** retest marketable rows are born-past-stop (3.1 %); 1,071 are ordinary
at-or-through-market. Removing them costs the effect 15 % and it stays at z 4.06 / 5.70.

### 8.3 The per-PLACED-ORDER curve — the true unit for a limit strategy

March full ledger, `E4_FINAL2_V1.json`. `per_placed_R = fill_rate × E[R | fill]` — what one placed
limit order is worth, counting the ones that never fill as exactly zero.

**No-breaker:**

| d | n | p_lo | p_hi | model P | fill rate | E[R\|fill] | **R per placed order** |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 11,909 | 0.0300 | 0.0748 | 0.0539 | 0.0094 | — | — |
| 2 | 11,909 | 0.0748 | 0.1083 | 0.0917 | 0.0296 | −0.10255 | **−0.00303** |
| 3 | 11,909 | 0.1083 | 0.1441 | 0.1259 | 0.0658 | +0.03078 | **+0.00202** |
| 4 | 11,910 | 0.1441 | 0.1857 | 0.1641 | 0.0989 | −0.17935 | −0.01774 |
| 5 | 11,909 | 0.1857 | 0.2392 | 0.2115 | 0.1509 | −0.20479 | −0.03090 |
| 6 | 11,909 | 0.2392 | 0.3148 | 0.2742 | 0.2324 | −0.13438 | −0.03122 |
| 7 | 11,910 | 0.3148 | 0.4451 | 0.3730 | 0.3762 | −0.16284 | −0.06127 |
| 8 | 11,909 | 0.4451 | 0.7185 | 0.5584 | 0.5781 | −0.08629 | −0.04989 |
| 9 | 11,909 | 0.7185 | 0.9200 | 0.8880 | 0.9145 | −0.11020 | −0.10078 |
| 10 | 11,910 | 0.9200 | 0.9500 | 0.9216 | 0.9554 | −0.15608 | **−0.14912** |

**Retest families:** d3 **+0.00416** (model P 0.1125, fill 0.0523, E[R|fill] +0.0796) is the only
positive cell anywhere in this lane; d10 **−0.17312** (model P 0.7629, fill 0.7685, E[R|fill] −0.22527).
**ALL families:** d3 **+0.00014**, d10 −0.23894.

**Monotone in every population.** A placed marketable order costs **−0.149 R** (no-breaker) or
**−0.239 R** (all families); a placed passive limit at model P ≈ 0.13 costs **+0.002 R** — i.e. free,
and in the retest families slightly profitable. **The spread between the two ends is 0.151 R per placed
order (no-breaker) and 0.177 R (retest).**

---

## 9. VERDICT — how far it reaches, and where it lives

| limb of the l12 finding | verdict | evidence |
|---|---|---|
| "The model is monotone anti-predictive of FILL" | **REFUTED as extended.** Against the engine's own limit-fill verdict: Brier skill **+0.5194**, Spearman **+0.675**, n 128,596. l12's −9.756 measured against *entry touch* on a population that is **100 % fill-conditioned by construction**. | §2 |
| "The far-limit cohort earns more" (unconditional) | **LOCAL to the born-past-stop artifact.** +0.1572/+0.1070/+0.0694 collapses to −0.0077/+0.0103/−0.0056 with the breaker family removed. Survives on the fill-honest instrument only (+0.0408, z 2.54). | §4 |
| **"Ranking on lowest modelled fill is a positive selection rule"** | **HOLDS IN ALL THREE MONTHS**, survives every control, is the unique best of nine rules, and beats a random control by +0.099…+0.133 R/window. | §3, §3.4 |
| the mechanism | **WITHIN-WINDOW, not global** — 2.7–3.9× stronger inside a window than pooled, in every month. | §5 |
| the boundary | **Two families** (`current_fvg_fill`, `current_ob_retest`), **indices** (SPX500/UK100/US30/JP225), no clean session. Conditioning STRENGTHENS it. | §6, §7 |
| deployability | The naive per-window pick is **not** ex-ante deployable (fills 0.09 %). The **family-conditioned passive-only filter is**, and is worth **+0.11…+0.20 R/trade** in all three months. | §8 |

**The correct one-sentence statement of the defect:** GTOS computes a genuinely well-calibrated
probability that a limit order will fill, and then spends it in five places as though it were a measure
of trade quality — with the result that, inside the two passive-retest families, the scoring path
systematically prefers the marketable version of a setup that is worth **0.15–0.18 R per placed order
less** than the passive version of the same setup.

---

## 10. WHAT WOULD MAKE THIS BANKABLE

1. **A month it has never seen.** April or May, replayed and pooled. The three months here are Jan
   (spent to death), Feb (used-once VAL, now twice), Mar (used once). All three are *pre-2026-04*.
   The finding's stability (+0.140/+0.144/+0.146) is its strongest property and one more month is the
   cheapest way to break or bank it. Cost: one sealed replay window (~16.5 MH) + contract regeneration
   under H1.
2. **The multiplicity bill.** This lane ran 9 selection rules × 4 populations × 3 months plus 9 families
   × 3 months of slopes. The retest-family result must be declared against `CANDIDATE_FAMILY_V27` and
   gated at the ratified rule (`CANDIDATE_BOOK_V1`, all-declared, sealed α = 0.10, RECORDED population).
   Raw perm p of 0.00025 is at the 4,000-permutation resolution floor; a 100k-permutation re-run is
   needed for a q-value.
3. **The fill oracle question, closed properly.** The pool is fill-conditioned, so E[R | fill] is what
   is measured. §8.3 gives the per-placed curve for March only, because March is the only month whose
   ledger carries `counterfactual_order_fill_status`. **Re-cutting the January and February pools from
   their raw ledgers with the fill-status columns retained** would give three months of per-placed
   economics instead of one — and January's raw ledger (`CJ_RECLOCKED_S0R0_V7`, 80 fields) **does not
   carry them**, so that requires either a re-materialisation or acceptance of March-only.
4. **The live-contract parity check.** The ex-ante rule in §8.2 is "in a passive-retest family, refuse
   the marketable version." Before that reaches a book someone must establish that
   `poi_execution_lifecycle`'s `limit_marketable` boolean at decision time equals what the live broker
   path would see — this lane measured replay, and H7 applies.
5. **Sizing, not admission.** The measured effect is a *ranking* within a window. The natural repair is
   not a new sleeve but a sign change on `W_FILL` (0.10 additive), the `×fill` multiplier inside the
   6.00 transfer term, and the −1.50 × max(0, 0.80 − fill) rank penalty — restricted to the two retest
   families. That is a scheduler edit, not a strategy, and it is inside `active_specs`' declared family.

---

## 11. ARTIFACTS

Scripts (all in this directory, all runnable):
`e4_e4lib.py` (shared stats) · `e4_load3.py` (three-month loader) · `e4_jan_repro.py` ·
`e4_run_feb.py` · `e4_run_mar2.py` · `e4_mar_calib.py` · `e4_mar_pool_bias.py` ·
`e4_artifact_ctrl.py` · `e4_rules.py` · `e4_withinwindow.py` · `e4_fe_boundary.py` ·
`e4_conditioned.py` · `e4_exante.py` · `e4_final2.py` · `e4_mar_extract.py`

Data:
`e4_MAR_R0_SLIM_V1.jsonl.gz` — 130,004 rows × 56 fields extracted from March's
`FA2_M_R0_MISSED_OPPORTUNITY_LEDGER.jsonl.gz`, including `counterfactual_order_fill_status` and
`candidate_decision_quality.execution_fill_probability`. **This is the only artifact on this machine
that pairs a modelled fill probability with the engine's own fill verdict.**

Results: `e4_RESULT.json` (master, every table above) · `E4_JAN_REPRO_V1.json` · `E4_FEB_V1.json` ·
`E4_MAR_V1.json` · `E4_MAR_CALIB_V1.json` · `E4_MAR_POOLBIAS_V1.json` · `E4_ARTIFACT_CTRL_V1.json` ·
`E4_RULES_V1.json` · `E4_WITHINWINDOW_V1.json` · `E4_FE_BOUNDARY_V1.json` · `E4_BOUNDARY_V1.json` ·
`E4_CONDITIONED_V1.json` · `E4_EXANTE_V1.json` · `E4_FINAL2_V1.json`

Source citations: `src/components/poi_execution_lifecycle.py:163-193` (the model, verified by direct
read this session: `limit_marketable` at `:163-166`, the 0.92 branch at `:175-177`, the decay branches
at `:180-187`, the `max(0.03, min(0.95, 0.70·atr + 0.30·risk))` at `:191-193`) ·
`src/research_infra/b7_5_diagnostic_pool.py:233-236` (the pool reads
`candidate_decision_quality.execution_fill_probability`, which is why March's raw ledger carries it) ·
`src/research_infra/v4_timewarp_simulated_live_research_loop.py:28130-28146` (the scoreability gate that
makes the pool fill-conditioned).
