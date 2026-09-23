# LANE l12 — where value is destroyed in the decision path (SOURCE-BOUND)

Wave 19 broad-forensic discovery swarm. Worktree
`/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801`, branch `phase19/broad-forensic`.
Population: the January 2026 true-UTC diagnostic pool (`CJ_RECLOCKED_S0R0_POOL_V1`, 27,658
candidates) joined to its M1 ordered paths via wave 0's working set. All file:line references are to
this worktree at HEAD.

**Two populations are used throughout.**
`ALL` = all 27,658. `CLEAN` = the 24,125 whose stop price had NOT already been breached at the
decision instant (w0-capture's `born_past_stop` removed; no look-ahead, anchored on the last bar
that CLOSES at or before the decision). Every headline is given on both.
**Two outcome columns are used.** `gross_r` = the engine's own walked result with costs stripped.
`fill_honest_walk_r` = wave 0's contract that requires the entry limit to actually trade before the
path is scored. The honest column is the one to believe.

---

## 0. HEADLINE

**The scheduler's 15-component ranking score is worth nothing against a coin flip, and the reason is
one input used five times in the wrong direction.**

On CLEAN, honest R of the single candidate selected per decision window (n = 1,966 windows):

| rule | R/trade |
|---|---:|
| production score, as shipped | **−0.1213** |
| random pick from the same window (200 seeds) | **−0.1218** |
| no selection at all (population mean) | −0.1262 |
| rank on `candidate_probability` alone | −0.0337 |
| rank on `candidate_ev_r` alone | −0.0340 |
| **rank on the LOWEST modelled `execution_fill_probability`** | **+0.1077** |
| oracle (best in window, ceiling) | +1.6377 |

The production score and the random control are **0.0005 R apart**. The best rule in the table is
the production score's own fill term, read backwards.

Paired, per window, CLEAN, honest: lowest-fill-probability minus production score =
**+0.2275 R/trade, t = 6.542, sign-flip p = 0.00025** (4,000 permutations, p is at the resolution
floor). On ALL: **+0.2644, t = 7.598, p = 0.00025**.

---

## 1. THE DECISION PATH — stages, what each can drop

The full bar-to-broker walkthrough already exists and is not duplicated here:
`research/operations/wave19_broad_forensic_2026_08_01/cartographer/DECISION_CYCLE_MAP.md`
(596 lines, 15 stages with file:line). What that map does not carry, and what this lane adds, is the
**scoring layer's arithmetic** and the measured consequence of each constant in it.

Funnel as measured (w0-dictionary D11, reconfirmed here): generated 27,658 → cost gate PASSED 7,210
(26.07 %) → scheduler materialized 4,095 (14.81 %) → selector action `trade` 21 (0.076 %) →
admission `trade` 20 → executed 0 (the pool is counterfactual by construction — w0-dictionary D3).

The one ordering fact that matters for everything below: **the cost gate runs first and removes
73.9 % of the pool, and the ranking score never sees those rows.**

### 1.1 The score, in full

`SCHEDULER_LEGACY_SCORE_COMPONENT_KEYS` declares 15 components
(`src/research/moonshot_scheduler_v4_best_trade_allocator.py:15781-15797`), assembled at
`:21991-22090`. The seven with a numeric weight visible in the assembly, plus the three penalties
this lane reconstructed from their own source sites, are:

```
score = 0.55*ev_r                                   # :21992
      + 1.20*(probability - 0.50)                   # :21993
      + 0.20*confidence                             # :21994
      + 0.15*source_completeness                    # :21995
      + 0.10*execution_fill_probability             # :21996-21999  (config.fill_probability_score_weight = 0.10, :8735)
      + 6.00*max(0, ev_r - cost)*p*fill*completeness # :22000, weight :8736; the max() floor is executable_value_semantics.py:101-104
      - 0.20*uncertainty                            # :22076
      - 0.80*cost_total                             # :22077
      - 1.50*max(0, 0.80 - execution_fill_probability)  # :21936-21943, weight :8737, floor = dynamic_budget_min_fill_probability
      - 0.20  if selector action is *-reduced-risk  # :19504, config :1015
```

---

## 2. THE CONSTANT / HAIRCUT / FLOOR / DEFAULT REGISTER

### 2.1 Defaults that stand in for a measurement (`_candidate_option`, scheduler :19259-19276)

| constant | value | site | binds on this pool? |
|---|---:|---|---|
| `confidence` default | **0.55** | `:19265` | **YES — 27,658/27,658**, `confidence_default_applied` True on every row. The confidence scorer never produces a value. |
| `uncertainty` default | **0.35** | `:19266` | YES — constant, so the `-0.20*uncertainty` limb is a fixed −0.070 |
| `fill_probability` (entry-quality) default | **0.25** | `:19268-19272` | populated on this pool |
| `probability` default | `clamp(0.50 + ev/4, 0.05, 0.95)` | `:19264` | populated on this pool |
| `confluence_reliability` default | **0.50** | `:19277` | — |
| `execution_fill_probability` for scoring when missing | **0.0** (fail-closed → ranks last) | `:19300-19304` | 152 rows (0.55 %) |
| `_reward_loss_cost` reward fallback | **1.5** | `probability_debate_v4.py:769` | see §2.4 |
| `_uncertainty` base | 0.08, completeness ×0.30, reliability ×0.18, disagreement cap 0.35, probability ×0.12, risk multiplier 1.15/0.85 | `probability_debate_v4.py:792-804` | — |
| `missing_penalty` | `min(0.40, 0.08 × n_missing)` | scheduler `:19352` | 0 here |
| `freshness_penalty` | `min(0.20, max(0, age−900)/7200)` | `:19355` | 0 here |
| `min_reduced_risk_pct` | 0.10 | `:8718` | — |
| `predecision_stop_hazard_risk_cap_pct` | 0.10 | `:8845` | — |

### 2.2 The fill-probability model itself — `poi_execution_lifecycle.py:162-194`

```
limit_marketable = (LONG and entry >= current) or (SHORT and entry <= current)   # :163-166
if limit_marketable:  atr_component = risk_component = 0.92                       # :175-177
else: atr_component  = 1/(1 + dist_atr **1.35)                                    # :180-183
      risk_component = 1/(1 + dist_risk**1.10)                                    # :184-187
fill_probability = max(0.03, min(0.95, 0.70*atr_component + 0.30*risk_component)) # :191-193
```

Constants with no justification anywhere in the tree: **0.92**, **1.35**, **1.10**, **0.70/0.30**,
**0.03**, **0.95**, and the 0.50 fallbacks at `:181` and `:186`.

The 0.92 branch covers **19,452 rows (70.33 %)** — every candidate whose entry is at or through the
market. Correcting the brief: `execution_fill_probability` is NOT a flat 0.92 (7,400 distinct values,
range 0.0401–0.95) — 0.92 is the value of one branch (w0-dictionary D5, reconfirmed).

**The model is monotone WRONG on both axes it claims to predict.** Bucketing by the entry limit's
signed distance from the market at the decision instant (`mkt_r`, no look-ahead), against the
realised entry-touch rate and the realised R:

| distance bucket | n | model fill P | realised entry-touch | gross R | win | honest R |
|---|---:|---:|---:|---:|---:|---:|
| past_stop (mkt_r ≤ −1) | 3,516 | 0.9199 | 100.00 % | −0.9948 | 0.08 % | −0.9933 |
| marketable (−1 < mkt_r < 0) | 1,265 | 0.9200 | 99.37 % | −0.2566 | 28.70 % | −0.3141 |
| at_limit (mkt_r = 0) | 14,911 | 0.9202 | 98.46 % | −0.0904 | 39.47 % | −0.1270 |
| resting 0–0.25 R | 801 | 0.8918 | 99.88 % | −0.1534 | 36.95 % | −0.1641 |
| resting 0.25–0.5 R | 840 | 0.7683 | 99.88 % | −0.1361 | 39.17 % | −0.1402 |
| resting 0.5–1 R | 1,715 | 0.6270 | 99.94 % | −0.1405 | 37.61 % | −0.1290 |
| resting 1–2 R | 2,422 | 0.4537 | **100.00 %** | −0.0919 | 42.90 % | −0.0961 |
| resting 2–5 R | 1,787 | 0.3068 | **100.00 %** | −0.0760 | 46.06 % | −0.0466 |
| **resting > 5 R** | **384** | **0.1745** | **100.00 %** | **+0.0069** | **53.65 %** | **+0.0883** |

The model runs 0.892 → 0.175 while the realised fill rate runs 99.88 % → 100.00 % and the realised
honest R runs −0.164 → **+0.088**. Calibration over the whole pool (n = 27,506):
modelled mean 0.8051 against a realised touch rate of 0.9912 — Brier 0.0934 against a base-rate
Brier of 0.0087, **Brier skill score −9.756**: the model is ~10× worse than a constant.

### 2.3 The same quantity is applied FIVE times

| # | application | weight/threshold | site |
|---|---|---|---|
| 1 | additive score term | ×0.10 | `:21996-21999`, weight `:8735` |
| 2 | multiplier on the dominant executable-transfer term | ×fill inside ×6.00 | `executable_value_semantics.py:101-104`, weight `:8736` |
| 3 | rank shortfall penalty | −1.50 × max(0, **0.80** − fill) | `:21936-21943`, weight `:8737` |
| 4 | package fill-floor execution-drag penalty | config-capped | `:21720-21735` |
| 5 | thirteen hard config floors | 0.25 / 0.35 / 0.45 / 0.70 / 0.80 / 0.90 | `config/agent_config.yaml:794, 798, 801, 811, 1002, 1016, 1030, 1043, 1049, 1053, 1058, 1075, 1080` |

Application 3 is the largest explicitly anti-predictive term in the score: a candidate at fill 0.17 —
the **best** cohort in the table above — is docked **−0.945** score units, while a past-stop
candidate at 0.92 is docked **0.000**.

**Every one of the thirteen floors rejects the better cohort.** Below/above the threshold, gross R
(ALL population):

| threshold | config line | n below | gross below | win below | n above | gross above | win above |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.25 | 798, 1080 | 1,033 | −0.0698 | 47.82 % | 26,473 | −0.2215 | 34.24 % |
| 0.35 | 801 | 2,203 | −0.0689 | 47.07 % | 25,303 | −0.2285 | 33.67 % |
| 0.45 | 811, 1030, 1043 | 3,407 | −0.0652 | 46.49 % | 24,099 | −0.2370 | 33.08 % |
| 0.70 | 794 | 5,939 | −0.0800 | 44.39 % | 21,567 | −0.2531 | 32.09 % |
| 0.80 | 1002, 1016, 1075 | 6,729 | −0.0932 | 43.25 % | 20,777 | −0.2554 | 31.99 % |
| 0.90 | 1049, 1053, 1058 | 7,367 | −0.0990 | 42.49 % | 20,139 | −0.2585 | 31.91 % |

On CLEAN the sign is unchanged (e.g. 0.45: below 3,400 at −0.0632 / 46.59 % vs above 20,612 at
−0.1089 / 38.67 %).

The one veto whose firing is recorded in the pool,
`scheduler_vetoed_candidate_package_fill_floor_quality_non_executable`, removes **1,443** candidates
worth **−0.0939** and keeps 26,215 worth **−0.2243** (CLEAN: 1,416 at −0.0767 vs 22,709 at −0.1056).

### 2.4 The EV haircut — `probability_debate_v4.py:673-678 (limbs :674-677)`

```
ev_r = calibrated_probability * reward_r
     - (1.0 - calibrated_probability) * loss_r
     - cost_r
     - uncertainty * 0.20
```

Measured over 27,658 rows, `candidate_ev_r` is an **exact affine function of
`candidate_probability`**: OLS slope **2.5876**, intercept **−1.1148**, R² **0.99993**, residual SD
0.001658 = **0.81 %** of the EV's own SD. With `loss_r = 1.0` that implies a mean reward multiple of
**≈1.588** — against a `take_profit_1` that is exactly **2.0000 R on 27,658 of 27,658 rows**
(w0-F4). The engine prices a 2R contract at 1.59R, then deducts a further 0.115 R.

**Correction to a claim this lane initially made and then refuted:** the `- cost_r` limb at `:676`
is INERT here. Regressing `ev` on `(probability, cost_r)` gives a cost coefficient of **+0.000833**
(R² 0.99995) — the broker cost never reaches the debate engine's context. There is no third cost
charge. The double charge in §3 stands; a triple charge does not.

**What the haircut costs.** The absolute `min_expected_net_r` floors are compared against the
haircut EV. Candidates passing, as shipped vs at the declared 2R geometry:

| floor | config sites | passes as shipped | passes at declared 2R | unlocked | share of pool |
|---:|---|---:|---:|---:|---:|
| 0.10 | 810 | 20,390 | 23,109 | +2,719 | 9.83 % |
| 0.20 | 1000 | 19,551 | 22,561 | +3,010 | 10.88 % |
| 0.70 | 1028, 1073 | 9,413 | 18,592 | +9,179 | 33.19 % |
| 0.80 | 1014, 1041, 1078 | 6,151 | 17,025 | +10,874 | 39.32 % |
| 1.10 | 1047, 1051, 1056 | 1,902 | 10,239 | +8,337 | 30.14 % |

### 2.5 Other haircuts found in the decision path

| site | expression | note |
|---|---|---|
| `selector_v4.py:1550-1552` | confluence = `strength*0.35 + confidence*0.25 + reliability*0.20` | undocumented weights |
| `selector_v4.py:1556` | `weight *= 1.0 - (0.35 * cost_sensitivity)` | a **cost**-driven haircut on a **confluence** weight |
| `selector_v4.py:1558` | `weight = 0.0` | hard zero |
| `selector_v4.py:1572` | `signed = alignment * weight * 0.25` | 75 % discount on one branch |
| `selector_v4.py:4965` | `gradient * (0.5 + 0.5 * segment_weight)` | shrinkage floor of 0.5 |
| `selector_v4.py:4250` | `min_expected_net_r = 0.55` | router-refusal materialization floor |
| `selector_v4.py:4270` | `min_fill_probability = 0.55` | a **14th** fill floor |
| `learned_edge_layer_v4.py:469` | `expected_net_r = p_fill * net_r_value` | fill multiplier again, in the learned lane |
| `scheduler:27090` | `risk_delta = -max(0, exposure.risk_pct) * 0.5` | the only literal 0.5 risk halving found |
| `scheduler:8743` | `ultimate_candidate_package_rank_score_weight = 0.65` | 35 % discount on the package rank |
| `scheduler:8740` | `learned_score_weight = 1.0` | — |

**Sizing.** `risk_per_trade_pct` takes exactly four values: 2.0 % (10,809), 0.5 % (9,865), 1.0 %
(4,847), 0.25 % (2,137). Of 4,509 risk-bearing decisions in the whole month, **21 (0.47 %) carry the
full-size `trade` action**; 4,488 (99.53 %) are softened/reduced-authority actions. The 21 full-size
rows book −0.0179 gross; the 4,488 book −0.1112.

---

## 3. DOUBLE APPLICATIONS

| # | quantity | first application | second (and later) | measured |
|---|---|---|---|---|
| **D1** | **broker cost** | inside the executable-transfer net edge, `net_edge = ev_r − cost_total` (`:15765`, `_candidate_edge_score`) | again as `cost_penalty = −0.80 × score_cost_total` (`:22077`) | **mean marginal d(score)/d(cost) = −3.706** against an intended −1.000, i.e. **3.71× over-charged in ranking units**. The guard at `:19329` (`score_cost_total = 0.0 if value_source == "decision_time_expected_net_r"`) **never fires**, because `_candidate_value` (`:15714-15722`) returns `ev_r` first and stamps `value_source = "decision_time_ev_r"` — `candidate_ev_r` is populated on 27,658/27,658 rows. |
| **D2** | **outcome probability** | inside `ev_r` (`probability_debate_v4.py:674-675`) — and `ev_r ≡ 2.5876·p − 1.1148` at R² 0.99993, so `ev_component` and `probability_component` are **the same signal twice** | a third time as the `probability_multiplier` on the transfer term (`executable_value_semantics.py:102`) | the score is quadratic in p through the transfer term; `ev_component` and `probability_component` have within-window SDs of 0.1060 and 0.0894 and deleting either moves nothing (\|t\| ≤ 0.5) |
| **D3** | **execution fill probability** | five applications — see §2.3 | | dropping the multiplier alone is **+0.0533 R/trade honest on CLEAN (t 3.195, p 0.002)** and **+0.0742 on ALL (t 4.472, p 0.0005)** |
| **D4** | **source completeness** | additive `0.15·k` (`:21995`) | multiplier on the transfer term (`executable_value_semantics.py:104`) | inert: `source_completeness` is **1.0 on 27,658/27,658** |
| **D5** | **uncertainty** | `− uncertainty × 0.20` inside `ev_r` (`probability_debate_v4.py:677`) | `uncertainty_penalty = −uncertainty × 0.20` in the score (`:22076`) — **the identical constant at two layers** | the scheduler limb is the 0.35 default → a fixed −0.070, so it cannot move a rank; the EV limb is real (implied mean uncertainty 0.593 from the fitted intercept) |
| **D6** | **slippage and swap** | already inside `cost_r` (`cost_r == expected_cost_r == spread_r + commission_r + expected_slippage_r + swap_cost_r`, w0-dictionary D4/D8) | `cost_total = cost_r + slippage_r + swap_r` (`:19322-19328`), fed from `row["slippage_r"]` and `row["swap_r"]` (`:10688-10689`) | **INERT on this pool** — the pool emits `expected_slippage_r`/`swap_cost_r`, not `slippage_r`/`swap_r`, so both resolve to 0.0. This is a live-path landmine, not a January defect: any producer that emits the short key names double-charges both terms. |

---

## 4. ORDER-OF-OPERATIONS DEFECTS

**O1 — the most decisive validity check is never performed; the least reliable one runs first.**
The cost gate (`broker_net_cost_engine.py:859-866` spread limb, `:923-927` total limb) refuses
**20,448 of 27,658 (73.9 %)** before the scheduler ranks anything, on a spread term measured
overcharged **7.3–8.5×**. Meanwhile nothing anywhere checks whether the entry's stop price has
already been breached — 3,516 rows (12.72 %) that are a mechanical −0.9948.

| filter | kept | gross | honest |
|---|---:|---:|---:|
| none | 27,658 | −0.2175 | −0.2367 |
| cost gate only (as shipped) | 7,210 | −0.1119 | — |
| **stop-validity only** | **24,142** | **−0.1043** | **−0.1265** |
| both | 6,984 | −0.0835 | −0.0800 |

**The stop-validity check alone keeps 3.35× more candidates at a better mean than the cost gate
achieves.** The cost gate catches 3,290 of the 3,516 past-stop rows (93.6 %) by accident — it is
doing the stop check's job while destroying 17,158 other candidates to do it. Adding the cost gate
on top of a stop check buys +0.0208 gross for a 71 % population cut.
`spearman(cost_r, risk_distance) = 0.115` — the cost gate is **not** simply a stop-width proxy.

**O2 — the marketability of the limit is computed AFTER the gate that assumes it.**
`limit_marketable_at_decision` is **85.19 % null**, and its non-null count (4,095) is **exactly** the
scheduler-materialized count — it is written at `poi_execution_lifecycle.py:224`, i.e. at
materialization, which is downstream of the cost gate. 20,448 candidates are refused before the
system knows whether their entry is a real limit (w0-dictionary D6, reconfirmed).

**O3 — the refusal is recorded before the softening can rescue it, and the softening is switched
off.** `ultimate_candidate_package_soften_selector_fill_floor_enabled: false`
(`config/agent_config.yaml:795`) and
`ultimate_candidate_package_positive_predecision_off_session_softening_enabled: false` (`:791`), so
the 0.25 and 0.70 fill-floor bypasses cannot fire at all. The floors are hard.

**O4 — `final_blocker_class` cannot answer the question it is being asked.** It is a substring
cascade whose first test is `cost_authority`, backed by a precedence table that ranks cost 1 of 10
(w0-dictionary D2). Cost wins every co-blocker tie-break by construction, so the 73.9 % cost share of
the blocker census is a property of the classifier, not of the pipeline.

---

## 5. DEAD MACHINERY

**5.1 Three of the ten reconstructable score components have exactly ONE distinct value across
27,658 rows.** They add a fixed +0.190 to every candidate and cannot change any ranking:

| component | value | distinct values | within-window SD |
|---|---:|---:|---:|
| `confidence_component` (0.20 × 0.55) | 0.110 | **1** | 0.0000 |
| `source_completeness_component` (0.15 × 1.0) | 0.150 | **1** | 0.0000 |
| `uncertainty_penalty` (−0.20 × 0.35) | −0.070 | **1** | 0.0000 |

**5.2 The 15-component score is, in practice, ONE component.** Within-window dispersion — the only
dispersion that can change a pick — and the paired cost of deleting each term (ALL / honest R):

| term | pool SD | within-window SD | distinct | pick changes | Δ honest on deletion |
|---|---:|---:|---:|---:|---:|
| `executable_transfer_component` | 1.7084 | **1.5327** | 20,842 | 14.5 % | −0.0147 |
| `cost_penalty` | 0.8448 | 0.6644 | 25,897 | 3.3 % | +0.0075 |
| `execution_fill_shortfall_rank_penalty` | 0.2719 | 0.2340 | 6,520 | 2.9 % | +0.0039 |
| `ev_component` | 0.1128 | 0.1060 | 26,725 | 1.9 % | +0.0076 |
| `probability_component` | 0.0951 | 0.0894 | 26,730 | 1.5 % | +0.0043 |
| `selector_reduce_risk_new_entry_penalty` | 0.0636 | 0.0413 | 2 | 2.2 % | +0.0053 |
| `fill_probability_component` | 0.0227 | 0.0201 | 7,400 | 0.5 % | −0.0014 |
| `confidence_component` | 0.0000 | 0.0000 | 1 | 0 % | 0.0000 |
| `source_completeness_component` | 0.0000 | 0.0000 | 1 | 0 % | 0.0000 |
| `uncertainty_penalty` | 0.0000 | 0.0000 | 1 | 0 % | 0.0000 |

The transfer term carries **2.3× the within-window dispersion of every other term combined**, and it
is the term that carries all four defects at once: the anti-predictive fill multiplier, the
double-charged cost, the thrice-applied probability, and the `max(0, ·)` floor.

**5.3 The `max(0, ev − cost)` floor** (`executable_value_semantics.py:101-104`) zeroes the dominant term
outright on **6,453 rows (23.33 %)**. Those rows are genuinely worse (gross −0.3525 vs −0.1764), so
the floor is not itself destructive — deleting it moves 0.0000 on CLEAN. Reported for completeness.

**5.4 Machinery that emits a constant.**

| field | value | n | meaning |
|---|---|---:|---|
| `dynamic_geometry_policy` | `momentum_exhaustion` | 27,658 (100 %) | the "dynamic target/stop geometry V4" engine emits one policy for the whole month |
| `selected_policy_for_expected_net_r` | `momentum_exhaustion` | 27,658 (100 %) | same |
| `candidate_confidence` / `confidence_default_applied` | 0.55 / True | 27,658 (100 %) | the confidence scorer never produces a value |
| `source_completeness` | 1.0 | 27,658 (100 %) | |
| `expected_slippage_r` | 0.02 | 27,658 (100 %) | a flat allowance, documented in-repo as covering 80.3 % of measured slippage (`divergence_matrix.py:366`) |
| `fill_realism_executable`, `entry_fill_executable` | True | 27,658 (100 %) | two "executability" verdicts that never say no |
| `guarded_market_fallback_extra_cost_r`, `fallback_execution_surcharge_r` | 0.0 | 27,658 (100 %) | |
| `raw_target_r` / `take_profit_1` | 2.0 | 26,427 / 27,658 | the geometry the EV engine then prices at 1.59R |

**5.5 A good signal computed and then refused.** `numeric_confluence_structured_disagreement` — the
selector's own "my numbers disagree" refusal — marks **484 candidates that are the best identifiable
cohort in the pool**: gross **+0.0879**, win **67.15 %**, honest **+0.1534**, against a pool of
−0.2175 / 34.7 % / −0.2367. 473 of the 484 are routed to `reduce-risk`, 11 to `reject`.

Their softening path is guarded by four floors (`config/agent_config.yaml:1047-1051`). Pass rates:

| floor | threshold | passes |
|---|---:|---:|
| `min_source_completeness` | 0.95 | **484 / 484** |
| `min_expected_net_r` | 1.10 | 198 / 484 |
| `min_probability` | 0.90 | 198 / 484 |
| **`min_fill_probability`** | **0.90** | **22 / 484** |
| all four | | **22 / 484 (4.5 %)** |

**The binding constraint on the pool's best cohort is the fill floor** — the quantity §2.2 proves is
monotone wrong. `final_blocker_class` on these rows is `execution_fillability` on 245 (50.6 %).
Family composition: `current_fvg_fill` 429, `current_breaker_re_entry` 35,
`session_open_range_break` 14, `structural_distance_extreme` 6.

**5.6 The other positive refusal class**, from the brief and reconfirmed: `daily_lockout`, 47 rows,
the only blocker class with a positive mean realised net (+0.242).

---

## 6. RANKED REPAIRS, WITH R

Every number below is the mean honest R of the single candidate the scheduler would select per
decision window, paired against the production score on the same windows. Sign-flip p from
2,000–4,000 permutations; `0.0005` and `0.00025` are permutation-resolution floors.

### 6.1 Marginal — each repair alone against production

**CLEAN population (stop-validity prefilter applied), n = 1,966 windows, production = −0.1170:**

| rank | repair | site | level after | Δ R/trade | t | p |
|---:|---|---|---:|---:|---:|---:|
| 1 | **drop the fill multiplier from the transfer term** | `executable_value_semantics.py:101-104` | −0.0637 | **+0.0533** | 3.195 | 0.0020 |
| 2 | **price EV at the declared 2R geometry** | `probability_debate_v4.py:673-678 (limbs :674-677)` | −0.0924 | **+0.0245** | 3.057 | 0.0045 |
| 3 | **charge the broker cost once** | delete `:22077` or fix the guard at `:19329` | −0.1020 | **+0.0149** | 2.379 | 0.0170 |
| 4 | drop the two additive fill terms | `:21996`, `:21936-21943` | −0.1189 | −0.0019 | −0.34 | 0.754 |
| 5 | unfloor the net edge | `executable_value_semantics.py:101-104` | −0.1170 | 0.0000 | — | 1.000 |

**ALL population, n = 1,969 windows, production = −0.1784:** drop fill multiplier +0.0742
(t 4.472, p 0.0005); single cost charge +0.0075 (t 1.184, ns); declared 2R +0.0102 (t 1.237, ns);
drop fill additive +0.0039 (ns); unfloor +0.0015.

### 6.2 Cumulative

| stack | ALL gross | ALL honest | CLEAN gross | CLEAN honest |
|---|---:|---:|---:|---:|
| production | −0.1446 | −0.1784 | −0.0760 | −0.1170 |
| + drop fill additive | −0.1344 | −0.1745 | −0.0712 | −0.1189 |
| + drop fill multiplier | −0.0653 | −0.0710 | −0.0290 | −0.0374 |
| + single cost charge | −0.0640 | −0.0742 | −0.0282 | −0.0401 |
| + declared 2R EV | −0.0642 | −0.0667 | −0.0212 | −0.0286 |
| + unfloor | −0.0642 | −0.0667 | −0.0212 | −0.0286 |

**Production ALL −0.1784 → stop-validity prefilter + all score repairs −0.0286 = +0.1498 R/trade.**
Replacing the score outright with `rank on lowest modelled fill probability` reaches **+0.1077**
(CLEAN) / **+0.0946** (ALL) — **+0.2861 R/trade** against the shipped ALL production number.

### 6.3 Concrete repairs, in order

1. **Delete the fill multiplier and both fill penalties, or invert the sign of the fill term.**
   `executable_value_semantics.py:92-104` (drop `fill_multiplier` from the product),
   `scheduler:21936-21943` (delete `execution_fill_shortfall_rank_penalty`), `scheduler:21996-21999`
   (delete the additive term). Worth **+0.053 to +0.074 R/trade**. The evidence for inversion rather
   than deletion is §2.2: the quantity is monotone anti-predictive with a Brier skill of −9.756.
2. **Re-derive or retire the thirteen fill floors** at `agent_config.yaml:794, 798, 801, 811, 1002,
   1016, 1030, 1043, 1049, 1053, 1058, 1075, 1080` plus the 14th at `selector_v4.py:4270`. Every one
   rejects the better cohort; the 0.90 floor alone is what closes the gate on the pool's best 484
   candidates (§5.5). Not separately priced at the selection layer because they act as population
   filters, not rank terms.
3. **Add a stop-validity precondition at candidate emission** — refuse any candidate whose stop price
   is already breached by the last closed bar. 3,516 rows, worth **+0.1133 R/trade** on the pool mean
   (w0-capture, independently reconfirmed here at −0.2175 → −0.1043). This is the largest single
   number in the whole forensic and it belongs to w0-capture, not to this lane.
4. **Price EV at the order's own geometry.** `probability_debate_v4.py:769` falls back to a 1.5
   reward multiple and the fitted mean is 1.588 against a `take_profit_1` of exactly 2.0R. Worth
   **+0.0245 R/trade** at the selection layer, and it unlocks 10,874 candidates (39.3 % of the pool)
   at the 0.80 `min_expected_net_r` floor.
5. **Charge the broker cost once.** Fix the guard at `scheduler:19329` — it tests
   `value_source == "decision_time_expected_net_r"` but `_candidate_value` (`:15714-15722`) returns
   `ev_r` first, so the guard is unreachable whenever `candidate_ev_r` is populated. Worth
   **+0.0149 R/trade**; removes a 3.71× over-charge in ranking units.
6. **Delete the three constant score components** (`confidence_component`,
   `source_completeness_component`, `uncertainty_penalty`). Worth exactly 0.0000 R — this is a
   simplification, not a repair, and it is listed so nobody re-measures it.
7. **Rename `slippage_r`/`swap_r` at `scheduler:10688-10689` or subtract them from `cost_r` first.**
   Worth 0.0000 R on this pool; it is a live-path landmine (§3 D6).

---

## 7. METHOD, CAVEATS, AND WHAT THIS LANE DOES NOT CLAIM

- **Single month, single arm.** January 2026, S0R0, true UTC. Nothing here is tested out of window.
  February/April/May are Wave 2's fuel.
- **The score is a reconstruction.** Ten of the fifteen declared components are reproduced from their
  own source sites; five (`confluence_component`, `missing_source_penalty`, `freshness_penalty`,
  `package_fill_floor_execution_drag_penalty_component`,
  `selected_policy_expected_net_calibration_penalty_component`) are not reconstructable from the pool
  and are omitted. The reconstruction reproduces the pool's realised selection behaviour but is not
  byte-identical to the engine's own score, which the pool does not carry.
- **`FIELD_mfe_r_by_bar_5_HIGH` (+0.1114 honest) in the random-control table uses post-decision path
  information and is a ceiling reference, not a rule.** It is reported only to bound the table.
- **Selection-layer R is not book R.** These are per-window single-pick means over a counterfactual
  pool with no position limits, no portfolio interaction and no execution. They measure the ranking
  layer, nothing else.
- **The cost correction does not help the ranking.** Re-running the production score with the spread
  divided by 7.3 makes the selection **worse**: CLEAN honest −0.1213 → −0.1263, ALL −0.1698 →
  −0.1851 (`L12_WINDOW_SELECTION_V1.json`). Fixing costs is not the lever.
- **Self-correction recorded:** this lane first read `probability_debate_v4.py:676` as a third cost
  charge and refuted it by regression (cost coefficient +0.000833). The claim in §3 is a double
  charge, not a triple.
- **Restated correctly:** an earlier working note read "99.53 % of risk-bearing decisions are halved".
  The defensible statement is that 4,488 of 4,509 are softened/reduced-authority actions and only 21
  carry the full-size `trade` action; no literal 0.5 risk multiplier was found on that path.

---

## 8. ARTIFACTS

Scripts and JSON written by this lane (all under
`docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/`):

`l12b_random_control.py` → `L12B_RANDOM_CONTROL_V1.json`;
`l12b_fillprob_mechanism.py` → `L12B_FILLPROB_MECHANISM_V1.json`;
`l12b_component_power.py` → `L12B_COMPONENT_POWER_V1.json`;
`l12b_full_score.py` → `L12B_FULL_SCORE_V1.json`;
`l12b_doubles_and_order.py` → `L12B_DOUBLES_ORDER_V1.json`;
`l12b_ev_triple_charge.py` → `L12B_EV_TRIPLE_CHARGE_V1.json`;
`l12b_charge_accounting.py` → `L12B_CHARGE_ACCOUNTING_V1.json`;
`L12B_SELECTOR_REASON_CENSUS_V1.json`; `L12B_NUMERIC_DISAGREEMENT_V1.json`;
`l12_RESULT.md`; `l12_RESULT.json`.

Inherited from an earlier l12 attempt that left artifacts but no receipt, verified and built on here:
`l12_CONSTANT_SCAN_V1.json` (586 raw hits over 16 files), `L12_FLOOR_CENSUS_V1.json`,
`L12_GATE_ORDERING_V1.json`, `L12_FILLPROB_CALIBRATION_V1.json`, `L12_FILLPROB_INVERSION_V1.json`,
`L12_PAIRED_TEST_V1.json`, `L12_SCORE_ABLATION_V1.json`, `L12_SCORE_ABLATION2_V1.json`,
`L12_SIZING_GEOMETRY_V1.json`, `L12_WINDOW_SELECTION_V1.json`, `L12_POSTCOST_FUNNEL_V1.json`.
