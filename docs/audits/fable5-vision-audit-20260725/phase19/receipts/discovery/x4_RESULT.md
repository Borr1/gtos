# Lane x4 — THE MISSING PIECE: what separates a setup that continues from one that reverts

Wave 19 broad forensic. January 2026, true-UTC S0R0 pool (CJ re-clock), 27,658 candidates.
**Every number below is measured over the whole population.** Nothing is sampled or estimated.
Scripts and JSON are named at each claim. This is a DISCOVERY lane: **no multiplicity correction
is applied anywhere**, and every headline carries an odd/even-day split, a first/second-half-of-
month split and a trading-day block bootstrap — none of which substitutes for an out-of-window
test, which a later stage owns.

| artifact | what |
|---|---|
| `x4_build_intrabar.py` → `x4_INTRABAR_V1.jsonl.gz` | 87 intra-bar features for 27,230 of 27,658 candidates |
| `x4_01_rank.py` → `X4_RANK_V1.json` | every feature ranked at l3's own cohort definitions |
| `x4_02_econ.py` → `X4_ECON_V1.json` | decile economics, 4 populations |
| `x4_03_control.py` → `X4_CONTROL_V1.json` | symbol / born-state / geometry controls + bar-1 cohort |
| `x4_04_rules.py` → `X4_RULES_V1.json` | rules, sweeps, and the missing-minute substrate correction |
| `x4_05_reanchor.py` → `X4_REANCHOR_V1.json` | re-anchored entry at T+k, k ∈ {0,1,2,3,5,10,15,30} |
| `x4_06_policy.py` → `X4_POLICY_V1.json` | conditional policy, cost, cross-fitted CEILING |
| `x4_07_verify.py` → `X4_VERIFY_V1.json` | seven adversarial checks on x4's own claims |
| `x4_08_final.py` → `X4_FINAL_V1.json` | refused-set / kept-set decomposition, joint surface |
| `x4_09_ticks.py` → `X4_TICKS_V1.json` | tick mechanism, out of window, 6,860 M15 boundaries |

---

## 0. HEADLINE

**The separator exists, it is worth 0.321 R inside the exact cohort the system cannot answer
today, and it is one minute old rather than zero minutes old.**

Inside the 55.65 % of the pool whose entry level is touched almost immediately — the cohort l8
found is adversely selected and could not decompose — a single observable splits it:

| cohort | n | honest R/trade | 95 % day-block CI | odd days | even days |
|---|--:|--:|---|--:|--:|
| first minute has **not** run against the entry (`c0_close_fav_r > −0.15`) | 8,458 | **−0.06174** | [−0.09506, −0.02932] | −0.05641 | −0.06668 |
| first minute **has** run against it (`≤ −0.15`) | 4,389 | **−0.38238** | [−0.42524, −0.33782] | −0.38000 | −0.38461 |

**Cohen's d = 0.3348, AUC = 0.5912 — 2.2× the estate's standing ceiling of 0.152.** It holds on
23 of 24 symbols, 8 of 8 families, 24 of 26 sessions, and in both at-market (gap 0.305) and
resting-limit (gap 0.342) order populations.

**And the honest correction that must travel with it: that variable is not new.** It is
byte-for-byte `w0cap2_DECISION_ANCHOR_V1`'s `mkt_r_close` — max absolute difference 5e-7,
Pearson 1.0000, 100 % of 27,033 rows agree inside 1e-6 (`X4_VERIFY_V1.json` V1). x4 did not
discover a field. It discovered that the field the estate already computed and used only as a
**binary born-state classifier** is, as a continuous quantity inside the takeable population,
**the strongest single discriminator in the entire schema** — and that it is legal for an order
placed at T+1m, which the live book's 60-second poll (`run_book.py:99`) already supports.

**Bar shape is dead.** All 87 features were built and tested. Volume distribution across the 15
minutes, where in the bar the move happened, close-location, wick structure, directional
efficiency, trend/retrace counts, acceleration, range expansion, gaps — **every one is |d| < 0.06
on winner-vs-stop.** Cross-fitted with day-grouped folds, everything knowable strictly BEFORE the
decision reaches **AUC 0.553–0.557**; adding the one minute after it reaches **0.579–0.588**. The
ceiling moved, and it moved because of the confirm minute, not because of anything inside the bar.

---

## 1. Substrate and alignment (verified, not assumed)

`x4_build_intrabar.py`. Decision at T. The M15 bar the decision is made on is labelled **T−15m**
and spans the M1 bars labelled T−15 … T−1. Verified directly on BTCUSD 2026-01-02T00:15: the M15
bar labelled `00:00` closes at **88599.74** and `entry_price` is **88599.74** — exact. The M1 bar
`00:14` closes at the same figure.

Two feature classes, stamped in the output and never mixed:

| class | window | legal for |
|---|---|---|
| **PRE** | M1 bars with time < T (the 15 constituents, plus 15/30/60/240-minute context and a 16-bar M15 ATR) | an order placed **at T** |
| **CONFIRM** | the single M1 bar labelled T, i.e. `[T, T+1m)` | an order placed **at T+1m or later** |

**The CONFIRM class is not look-ahead for the outcome measure used here.** `fill_honest_walk_r`
walks the sidecar path, whose bar 1 is `[T+1m, T+2m)`. The confirm minute ends exactly where the
walk begins. There is no overlap.

Coverage: **27,230 of 27,658 rows (98.45 %)**. The 428 dropped had fewer than 5 M1 bars inside
their decision bar; 294 of them are at UTC hour 22 and 94 at hour 23 (the rollover). **They are
worse than average** — gross −0.38899 against the kept −0.21480 — so the x4 population is
optimistic by 0.0012 R/candidate against the full pool. Stated, not hidden.

---

## 2. X4-F8 — SUBSTRATE DEFECT: a whole minute is missing from every prior lane

`x4_04_rules.py` → `X4_RULES_V1.json` `MISSING_MINUTE`; `x4_07_verify.py` V5.

**The M1 path sidecar's bar 1 is `[T+1m, T+2m)`. The minute `[T, T+1m)` is in no prior lane's
substrate at all.** So `bars_to_entry_touch == 1` does not mean "touched within 60 seconds"; it
means "touched between 60 and 120 seconds", and every candidate whose entry was crossed inside
the first minute and not afterwards is invisible.

| quantity | measured |
|---|--:|
| entry level traded inside the missing minute | **19,206 / 27,033 = 70.53 %** |
| sidecar `bars_to_entry_touch == 1` | 16,685 / 27,230 = 61.27 % |
| **true "entry traded within 120 s"** | **72.65 %** |
| traded in the missing minute and **invisible** to the sidecar flag | **3,097 (11.37 % of the pool)** |

What the fill-honest walk does with those 3,097: **1,325 stop, 1,040 neither, 532 target, 200
no_fill.** It starts their position at the wrong time and the wrong price, booking −0.00713 while
the pool's own gross for the same rows is **+0.20206**. This is a bound on l8's headline and on
w0's `fill_honest_walk_r` for 11.37 % of the pool. Direction of the bias is not determined here —
resolving it needs the path re-materialised from T, not T+1m.

---

## 3. X4-F1 — the CEILING, cross-fitted

`x4_06_policy.py` → `X4_POLICY_V1.json` `CEILING`. `GroupKFold(5)` **grouped by trading day**, so
no day appears in both train and test. Population: takeable and honest-resolved, n = 15,484,
base target rate 0.2361. 87 features.

| feature set | model | cross-fitted AUC |
|---|---|--:|
| PRE only (everything knowable at T) | logistic | **0.5568** |
| PRE only | gradient boosting | 0.5528 |
| PRE + CONFIRM | logistic | 0.5786 |
| PRE + CONFIRM | gradient boosting | **0.5884** |

l3 measured that **every AUC in the emitted schema sits between 0.44 and 0.57**. So:

- **Everything inside the forming bar, before the decision, is worth ~nothing beyond what the
  engine already emits.** 0.553–0.557 against a prior best of 0.57.
- **The single minute after the decision is worth +0.035 AUC.**

Economics of the cross-fitted score (trade only the top slice):

| slice | n | honest R/trade | target rate |
|---|--:|--:|--:|
| PRE+CONFIRM GBM top 50 % | 7,742 | −0.15227 | 0.2825 |
| top 25 % | 3,871 | −0.10082 | 0.2997 |
| top 10 % | 1,549 | −0.05872 | 0.3138 |
| PRE+CONFIRM logistic top 10 % | 1,549 | **−0.02001** | 0.3267 |

**No slice of any model is positive.** A one-variable refusal rule beats every model at pool
level, because the problem is not ranking — it is refusal.

---

## 4. X4-F2 — the best strictly-PRE field the estate has: `stop_dist_over_bar_range`

`risk_distance ÷ (high − low of the 15 M1 bars composing the decision M15 bar)`.

| cohort definition | prior best (l3) | `stop_dist_over_bar_range` |
|---|--:|--:|
| briefed `ge_target` vs `full_stop`, takeable | 0.152 | **−0.1829** |
| honest first-touch target vs stop, takeable | — | **−0.1723** |
| honest, **within the confirm-clean population** | — | **−0.1983** |
| its target-side twin `target_dist_over_bar_range`, confirm-clean | — | **−0.2004** |

Decile economics over takeable (`X4_ECON_V1.json`), n = 2,347–2,348 per bin:

| bin | ratio range | honest R | stop rate | target rate |
|--:|---|--:|--:|--:|
| 0 | 0.057 – 0.405 | −0.1819 | **0.696** | 0.245 |
| 3 | 0.708 – 0.832 | −0.1022 | 0.572 | 0.196 |
| 6 | 1.026 – 1.107 | −0.0711 | 0.422 | 0.117 |
| 9 | 1.984 – 42.47 | −0.0898 | **0.207** | 0.024 |

**A stop set inside the noise the market just made in the last 15 minutes is hit 70 % of the
time.** Refusing the bottom (`≤ 0.60`, 6,295 rows = 23.1 %) refuses a cohort booking
**−0.30378 R each** [−0.36521, −0.23546], odd −0.28653 / even −0.32030.

**Three caveats that belong with it.**
1. It is a **better normalisation of the field that already held the record** — l3's
   `risk_distance_pct_of_price` (d = −0.1517). Normalising by the realised bar range instead of by
   price takes it 0.152 → 0.183. That is an improvement, not a new axis.
2. It is **partly a resolution-speed measure**, not purely edge: at bin 9 the target rate is
   0.024 because within the 2-hour path cap neither level is reached. Some of the gradient is the
   horizon cap.
3. It is **not circular but it is related**: correlation(`risk_distance`, decision-bar range) in
   price units is **0.862**, so the generator's stop already tracks volatility. Only 1.40 % of
   rows have the stop inside the decision bar's own range, and the ratio spans 0.057 to 42.47
   (median 0.927, 10.8 % inside [0.95, 1.05]) — the ratio carries real, non-degenerate information.

---

## 5. X4-F3/F5 — the confirm minute, and what it is worth on the whole pool

`c0_close_fav_r` = `s·(close of [T,T+1m) − entry_price) / risk_distance`, s = +1 LONG / −1 SHORT.
Negative means price has already run **against** the entry inside the first minute.

### 5.1 The whole pool, one variable (`X4_FINAL_V1.json`)

| rule | refused n | **refused-set R/trade** | 95 % CI | kept n | kept R/trade | pool R/opportunity |
|---|--:|--:|---|--:|--:|--:|
| none (baseline) | 0 | — | — | 27,230 | −0.23551 | −0.23551 |
| refuse `c0 ≤ −0.15` | 8,111 (29.8 %) | **−0.66506** | [−0.69693, −0.63193] | 19,119 | **−0.05327** | −0.03741 |
| refuse `c0 ≤ −0.05` | 11,008 (40.4 %) | −0.52044 | [−0.55048, −0.48800] | 16,222 | −0.04215 | −0.02511 |
| refuse `geo ≤ 0.60` | 6,295 (23.1 %) | −0.30378 | [−0.36521, −0.23546] | 20,935 | −0.21498 | −0.16528 |

Split-half on the refused set at `c0 ≤ −0.15`: **odd −0.66845, even −0.66179.** First half of
month −0.66, second half −0.67 (`X4_FINAL_V1.json`). It is the most stable large effect in this
lane.

### 5.2 Inside the adversely-selected cohort — the mission's item 3

Population: takeable ∧ `bars_to_entry_touch == 1`, n = 12,933, honest R **−0.17335**. (l8's own
figures on its slightly different population were 13,436 / −0.19754; reproduced within the 428
dropped rows and the takeable definition.)

| split | n | honest R | 95 % CI | target rate | stop rate | odd | even |
|---|--:|--:|---|--:|--:|--:|--:|
| all | 12,933 | −0.17335 | [−0.20260, −0.14431] | 0.148 | 0.542 | −0.16920 | −0.17719 |
| `c0 > −0.15` | 8,458 | **−0.06174** | [−0.09506, −0.02932] | 0.157 | 0.465 | −0.05641 | −0.06668 |
| `c0 ≤ −0.15` | 4,389 | **−0.38238** | [−0.42524, −0.33782] | 0.134 | 0.687 | −0.38000 | −0.38461 |
| `c0 > −0.05` | 5,563 | **−0.03352** | [−0.06992, **+0.00634**] | 0.162 | 0.451 | −0.04269 | −0.02477 |
| `c0 ≤ −0.05` | 7,284 | −0.27650 | [−0.31177, −0.24068] | 0.139 | 0.609 | −0.26520 | −0.28678 |

The strict cut's confidence interval **touches zero** — the only cohort in this lane that does.

Robustness (`X4_POLICY_V1.json` `HEADLINE_SPLIT`): the split has the right sign on **23 of 24
symbols, 8 of 8 families, 24 of 26 sessions**. Not an order-type artifact
(`X4_VERIFY_V1.json` V2): at-market rows gap **+0.30461** (7,609 vs 3,354), resting-limit rows
gap **+0.34214** (849 vs 1,035).

---

## 6. X4-F6 — the two axes are SUBSTITUTES, and the confirm minute dominates

`X4_FINAL_V1.json`. This is the check that decides where the effort goes.

| conditional test | refused n | refused-set R | kept-set R | verdict |
|---|--:|--:|--:|---|
| geometry applied **after** the confirm filter | 3,822 | **−0.04851** [−0.12038, +0.03263] | −0.05447 | **adds nothing (Δ −0.0012)** |
| confirm applied **after** the geometry filter | 5,638 | **−0.65047** [−0.68794, −0.60750] | −0.05447 | **the whole effect survives** |

The joint 5 × 5 surface says the same thing without any modelling. Rows = `c0` quintile
(0 = most adverse first minute), columns = geometry quintile (0 = tightest stop); cell = honest R
/ n:

| | geo 0 | geo 1 | geo 2 | geo 3 | geo 4 |
|---|---|---|---|---|---|
| **c0 0** | −0.8358/1609 | −0.8827/1307 | −0.8589/733 | −0.9070/691 | −0.8798/1067 |
| c0 1 | −0.2980/791 | −0.1379/1099 | −0.2005/1476 | −0.1201/1315 | −0.2242/725 |
| c0 2 | −0.0940/404 | −0.0235/775 | −0.0304/1352 | −0.0195/1578 | −0.0703/1298 |
| c0 3 | −0.0647/910 | +0.0186/1089 | −0.0827/1135 | −0.0160/1235 | −0.0257/1037 |
| c0 4 | +0.0148/1718 | −0.1475/1155 | −0.0395/729 | −0.0856/597 | −0.0211/1208 |

**The top row is −0.84 to −0.91 at every geometry quintile. There is no geometry gradient inside
any c0 row.** One variable owns the surface.

---

## 7. X4-F7 — RE-ANCHORING: the owner's question, answered

*"Can't we go early exactly when the signal tells us."* The mirror of that question is: if the
entry LEVEL is stale by the time the system can act, keep the signal and the risk distance and
enter where the market actually **is** k minutes later.

Arithmetic on the existing R paths, no new data: re-anchoring to price `p_k` with the same risk
distance shifts every excursion by `s·(p_k − e)/d`. Market order at T+k, so always filled;
first-touch walk at +2R / −1R with the same conservative same-bar tie to the stop.

| k (minutes) | n | R/trade | 95 % day-block CI | vs stale-limit baseline | target | stop |
|--:|--:|--:|---|--:|--:|--:|
| baseline: rest the limit at the stale level | 27,230 | **−0.23551** | — | — | — | — |
| 1 | 27,033 | −0.19346 | [−0.22422, −0.16053] | +0.04205 | 0.170 | 0.587 |
| 2 | 27,230 | −0.17529 | [−0.20464, −0.14526] | +0.06022 | 0.174 | 0.581 |
| 3 | 27,230 | −0.17294 | [−0.20334, −0.14231] | +0.06257 | 0.174 | 0.577 |
| **5** | 27,216 | **−0.16879** | [−0.19434, −0.14224] | **+0.06672** | 0.174 | 0.575 |
| 10 | 27,204 | −0.13798 | [−0.16279, −0.10933] | +0.09753 | 0.179 | 0.557 |
| 15 | 27,200 | −0.12773 | [−0.15290, −0.10123] | +0.10778 | 0.179 | 0.548 |
| 30 | 27,156 | −0.09955 | [−0.12230, −0.07463] | **+0.13596** | 0.172 | 0.513 |

**k = 5 is +0.06672. L7 measured +0.0670** for the same 5-minute delay by a completely different
construction (its own at-market book, not a fill-honest first-touch walk on M1 paths).
**Independent reproduction to four decimals.** And it does not peak at 5: the improvement is
monotone out to 30 minutes here.

**Where the value lives, which L7 could not see.** Re-anchoring is not a uniform good:

| cohort | stale limit | re-anchored at T+1m | Δ |
|---|--:|--:|--:|
| bar-1 ∧ `c0 ≤ −0.15` (price ran away) | −0.38238 | **−0.02177** | **+0.36061** |
| bar-1 ∧ `c0 > −0.15` (price did not) | −0.06174 | −0.06462 | −0.00288 |
| all rows with `c0 > −0.15` | −0.05327 | −0.27420 | **−0.22093** |

**Re-anchoring the rows where price has not moved away is strongly destructive** — you give up the
limit's price improvement for nothing. The correct policy is conditional, and refusal beats
re-anchoring on the bad cohort anyway (0.0 > −0.022):

| policy | pool R / opportunity | 95 % CI | odd | even |
|---|--:|---|--:|--:|
| rest the limit as today | −0.23551 | — | −0.21674 | −0.25303 |
| refuse `c0 ≤ −0.15` | **−0.03741** | [−0.05763, −0.01421] | — | — |
| refuse `c0 ≤ 0.00` | −0.02266 | [−0.04147, −0.00045] | — | — |
| re-anchor at T+5m where `c0 ≤ 0.00` | **−0.01667** | — | — | — |
| refuse `≤ −0.30` + re-anchor at T+5m in (−0.30, −0.05] | −0.02376 | [−0.04488, **+0.00109**] | +0.00071 | −0.04661 |

The last row is the only policy whose interval crosses zero, and its split halves disagree
(+0.0007 / −0.0466). **Reported, not recommended.**

**One trap in that sweep, flagged because it is easy to misread.** The `k = 0` arm measures
**+0.04241**. That is not an at-market baseline — it is the **fill-blind convention**, which W0-F2
established manufactures +0.2776 R/trade of edge a limit order could never take. Never compare
delayed entries against it.

---

## 8. X4-F9 — what does NOT separate, so nobody spends there again

All measured on the takeable population, honest target-vs-stop, |Cohen's d| (`X4_RANK_V1.json`):

| what the mission asked to test | features | best \|d\| |
|---|---|--:|
| **where in the bar the move happened** | `argmax_fav_pos` −0.0570, `argmax_adv_pos` +0.0250, `argmax_range_pos` +0.0019, `fav_after_adv` −0.0413 | **0.057** |
| **how many M1 bars trended vs retraced** | `up_min_frac` −0.0159, `net_min_frac` −0.0133, `max_run_fav` −0.0257, `max_run_adv` −0.0045, `max_run_diff` −0.0136, `n_dir_flips` +0.0526 | **0.053** |
| **close position within range** | `clv_fav` −0.0493, `retrace_from_fav` +0.0493, `wick_beyond_close_fav_r` +0.0544 | **0.054** |
| **range-expansion profile** | `range_expansion` −0.0461, `range_eff` −0.0325, `dir_eff` −0.0817, `max_min_range_share` +0.0349 | **0.082** |
| **volume / tick-count across the 15 minutes** | `vol_late3_share` −0.0115, `vol_late5_share` −0.0310, `vol_first5_share` −0.0005, `vol_centroid` −0.0222, `vol_at_fav_min_share` +0.0296, `vol_at_maxrange_share` +0.0272, `vol_late1_ratio` +0.0091, `bar_volume` −0.0292, `vol_expansion` −0.0367 | **0.037** |
| **shape of the approach to the entry level** | `entry_touch_minutes` +0.0279, `entry_touch_frac` +0.0256, `entry_first_touch_pos` −0.0772, `entry_last_touch_pos` +0.0499, `minutes_since_entry_touch` −0.0505, `entry_close_crossings` +0.0450 | **0.077** |
| **touched once or repeatedly** | `entry_touch_minutes` +0.0279, `entry_close_crossings` +0.0450 | **0.045** |
| **late momentum / exhaustion** | `late1_r` +0.0180, `late3_r` +0.0359, `late5_r` +0.0217, `accel_late_minus_first` +0.0419 | **0.042** |
| **prior-bar context** | `prev_bar_ret_r` −0.0243, `same_dir_as_prev` −0.0287, `prior_same_dir_bars` −0.0311, `gap_from_prev_close_r` −0.0544 | **0.054** |

**Conventionally d < 0.2 is negligible and d < 0.1 is not worth naming. Not one shape feature
reaches 0.09.** The pre-decision ceiling is a volatility-geometry axis and nothing else.

Two shape families have a **monotone economic gradient with no winner/stop discrimination** —
`up_min_frac` (decile ρ 0.960, spread 0.150), `net_min_frac` (ρ 0.864, spread 0.215), `clv_fav`
(ρ 0.856, spread 0.184), `late3_r` (ρ 0.767, spread 0.229). §6's stratification kills them: inside
`stop_dist_over_bar_range` quintiles their median-split deltas fall to +0.056, +0.036, +0.043 and
+0.067 and are not same-signed across all five strata for two of the four. **They are the geometry
axis wearing different clothes, and the geometry axis is a substitute for the confirm minute.**

Within-symbol rank normalisation (`X4_CONTROL_V1.json` C1) does not rescue any of them and does
not destroy the winners: `c0_close_fav_r` 0.1701 → **0.2189**, `atr16_m15_r` 0.1279 → 0.1629,
`stop_dist_over_bar_range` −0.1723 → −0.1323. **The result is not a re-discovery of `symbol`.**

---

## 9. X4-F10 — MECHANISM: how early is the confirm signal available (tick data)

`x4_09_ticks.py` → `X4_TICKS_V1.json`. **Out-of-window by construction** (2026-06-18 … 07-24) and
used only for mechanism, never to score a January candidate. Every M15 boundary in the tick
window, mid price, no clock conversion needed (the broker offset is a whole number of hours so
M15 boundaries coincide). n = 2,352 EURUSD / 2,091 GER40 / 2,417 XAUUSD boundaries.

| lag after the M15 close | median share of the 60-second move already made | sign agreement with the 60-second sign |
|---|---|---|
| 1 s | 0.27 / 0.26 / 0.23 | 0.619 / 0.590 / 0.585 |
| 5 s | 0.39 / 0.43 / 0.41 | 0.645 / 0.632 / 0.621 |
| **15 s** | **0.60 / 0.61 / 0.63** | **0.710 / 0.719 / 0.693** |
| 30 s | 0.80 / 0.80 / 0.80 | 0.793 / 0.800 / 0.772 |
| 45 s | 1.00 / 0.94 / 0.94 | 0.884 / 0.891 / 0.864 |

**76.1 – 97.7 % of boundaries have already moved within one second of the M15 close.** The market
reacts at the boundary immediately.

Read for the owner: **the confirm observable is already available at the book's current cadence**
— `run_book.py --poll-seconds 60` puts the poll exactly where the measurement is. Moving to a
15-second poll would deliver about **60 % of the same displacement 45 seconds earlier, with ~70 %
sign agreement**. That is earlier action on the same information, not a new signal.

---

## 10. X4-F11 — cost: none of this makes the broad pool tradeable

`X4_POLICY_V1.json` `COST`. Mean `cost_r` **0.65486**, median **0.30075**.

| kept set | n | gross pool R | median cost | **net pool R** | net kept-mean |
|---|--:|--:|--:|--:|--:|
| all | 27,230 | −0.23551 | 0.301 | **−0.89037** | −0.89037 |
| `c0 > −0.15` | 19,119 | −0.03741 | 0.250 | −0.47007 | −0.66950 |
| `geo > 0.60` | 20,935 | −0.16528 | 0.259 | −0.59168 | −0.76959 |
| both | 15,297 | −0.03060 | 0.225 | **−0.33010** | −0.58761 |

Both filters are **also cost filters** — the confirm filter refuses rows with median cost 0.381
and keeps 0.250; the geometry filter refuses 0.515 and keeps 0.259 — so the net improvement
(+0.560) is larger than the gross one (+0.205). **The sign never changes.** Consistent with
wave 18's February rejection of broad V4: this lane explains where the gross deficit comes from,
it does not produce a tradeable book.

---

## 11. X4-F12 — a metric warning that applies to this lane and to l8's headline

**Pool R per candidate-opportunity rises whenever you refuse ANY subset with a negative mean**,
because refused rows book exactly 0.0. It therefore cannot rank filters. Same data, two metrics:

| filter | pool-R gain | **kept-set gain** | refused-set mean |
|---|--:|--:|--:|
| `geo > 0.60` | +0.07023 | **+0.02053** | −0.30378 |
| `c0 > −0.15` | +0.19810 | **+0.18223** | −0.66506 |

The geometry filter's pool gain overstates its per-trade value **3.4×**. Always report the
refused-set mean — it is the only figure that says what you actually avoided.

---

## 12. Multiplicity, and what x4 does NOT establish

- 87 features built; ~522 ranking cells at step 1, 130 stratified cells at step 3, 63 sweep cells
  at steps 4–6, plus the bar-1 re-ranking. **No correction applied anywhere.** This is a discovery
  lane and under-reporting is the failure mode named in the brief.
- Every headline carries odd/even-day and first/second-half-of-month splits and a trading-day
  block bootstrap. The two headline cohorts are stable to the third decimal across day parity.
- **Nothing here is out-of-window.** January only. February is used-once VAL and was not touched;
  March is under a separate pre-registration; April and May belong to CS. **The x4 feature builder
  runs unchanged on any month** — `M1DIRS` in `x4_build_intrabar.py` already lists 2025-12 through
  2026-05, and the M1 sources exist for all of them. Travel is one command, and it is the next
  stage's call, not this lane's.
- The 2-hour path cap bounds everything: no claim here survives past 120 minutes, and part of the
  geometry gradient is resolution speed inside that cap rather than edge.
- The re-anchor arithmetic assumes a market fill at the re-anchored price with no slippage beyond
  the frozen cost model. §10's net column is the honest bound.

---

## 13. What this lane says to do next, in order

1. **Stop looking inside the bar for shape.** It is measured: |d| < 0.09 on every shape family,
   cross-fitted PRE-only AUC 0.553. The money is not there.
2. **Test whether the confirm-minute split travels.** One variable, one threshold, no fitting:
   `c0_close_fav_r ≤ −0.15` on February, April, May. If the refused-set mean is ≈ −0.6 R in
   another month, the estate has its first entry-timing rule with an out-of-window number.
3. **Re-materialise the path from T, not T+1m.** 11.37 % of the pool is booked against a fill the
   substrate cannot see (§2). Every fill-honest number in wave 19 inherits that.
4. **Price a 15-second poll.** §9 says ~60 % of the confirm displacement exists at 15 s. The
   question for the live book is whether acting 45 seconds earlier is worth more than the 30 % of
   sign disagreement it buys.
