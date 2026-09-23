# Lane l3 — what does a trade we WANT actually look like

Wave 19 broad-forensic discovery. January 2026, true-UTC S0R0 diagnostic pool, 27,658 candidates.
Every number below is measured. Scripts and JSON are named at each claim.

---

## 0. Headline

**Across all 28 pre-decision numeric fields the engine emits, the largest winner-vs-stop effect size
is Cohen's d = 0.152.** There is no field in the pool that tells a full-target winner from a full
stop. The system's *own* belief is inverted on the outcome it declares it forecasts — the
top-confidence decile reaches the 2R target **4.02 %** of the time against the bottom decile's
**20.47 %** — and the binding cost gate refuses the trades that reach target **2.87×** more often
than the ones it keeps.

The one profile that survives a split-half and is gross-positive in both halves
(`cost_r > 0.40 AND session = london`, n=860, +0.0532 R/trade, 29.88 % target rate = 2.35× base)
is **100.0 % refused by the live cost gates**, 0.0 % scheduler-materialised, 0.0 % selected.

---

## 1. Cohort integrity — the briefed comparison is contaminated on one side only

Script `l3_cohort_integrity.py` → `l3_COHORT_INTEGRITY_V1.json`; substrate `l3_build.py` →
`l3_COHORTS_V1.json`.

The mission briefs 3,072 full-target winners vs 15,057 full stops. Applying W0-capture's
no-look-ahead born-state anchor (`w0cap2_DECISION_ANCHOR_V1.jsonl.gz`, 27,641/27,658 anchored):

| cohort | briefed n | takeable n | survival |
|---|---:|---:|---:|
| full target (`ge_target`) | 3,072 | **3,069** | **99.90 %** |
| full stop | 15,057 | **11,534** | **76.60 %** |

**3,513 of the 15,057 full stops (23.34 %) were never takeable** — their stop price was already
breached at the decision instant. Only **3** of the 3,072 winners are. Profiling winners against
stops on the briefed cohorts therefore measures the W0-capture artifact, not trade shape. Lane l3
runs everything on the **TAKEABLE** population, n=24,125.

Band counts over the whole pool: `full_stop` 15,057 | `ge_target` 3,072 | `partial_loss` 3,008 |
`b_01_to_05` 2,602 | `b_05_to_1` 2,096 | `b_1_to_target` 1,173 | `scratch_0_to_01` 650.

Born-state counts: `born_at_limit` 14,911 | `born_resting` 7,949 | `born_past_stop` 3,516 |
`born_marketable` 1,265 | unanchored 17.
Winners by born state: at_limit 2,075 | resting 886 | marketable 108 | past_stop **3**.
Stops by born state: at_limit 7,242 | resting 3,631 | past_stop **3,513** | marketable 661 | unanchored 10.

### 1a. The winner cohort itself is 90.75 % honest

Of the 3,072 `ge_target` rows, the fill-honest first-touch walk says: **target 2,788 (90.75 %)**,
`no_fill` 145 (4.72 %), `stop` 116 (3.78 %), `neither` 23 (0.75 %). Mean `gross_r` +2.0153 vs mean
`fill_honest_walk_r` +1.7889 — an 11.2 % overstatement, not a fabrication. **The winners are real.**

On the takeable population the fill-blind bias is small: `gross_r` −0.10392 vs `fill_honest_walk_r`
−0.12617 (Δ 0.0222). W0-F2's +0.2776 R/trade of fiction lives almost entirely in the untakeable and
never-filled rows, not here.

Honest cohorts on takeable: target 3,709 (15.374 %), stop 12,331, other 8,085.

---

## 2. The master mechanism — risk distance is the axis everything rides on

Deciles of `risk_distance_pct_of_price`, TAKEABLE n=24,125 (`l3_COHORT_INTEGRITY_V1.json` →
`risk_distance_decile_takeable`):

| dec | n | riskD % of price | hit target % | full stop % | neither % | gross R | fill-honest R | cost_r | mfe R |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2,413 | 0.0211 | 22.34 | 66.35 | 1.99 | −0.1630 | −0.2145 | 1.6309 | 4.373 |
| 2 | 2,412 | 0.0372 | 20.36 | 60.57 | 9.04 | −0.1087 | −0.1368 | 1.2389 | 3.028 |
| 3 | 2,413 | 0.0536 | 16.70 | 54.87 | 12.93 | −0.0990 | −0.1671 | 0.8858 | 2.796 |
| 4 | 2,412 | 0.0697 | 12.85 | 54.52 | 18.91 | −0.1524 | −0.1576 | 0.6178 | 2.536 |
| 5 | 2,413 | 0.0896 | 11.19 | 50.56 | 25.69 | −0.1271 | −0.1674 | 0.5477 | 2.207 |
| 6 | 2,412 | 0.1177 | 12.35 | 47.47 | 27.86 | −0.1046 | −0.1132 | 0.4787 | 2.188 |
| 7 | 2,412 | 0.1585 | 12.27 | 43.12 | 33.54 | **−0.0526** | −0.0659 | 0.4048 | 1.835 |
| 8 | 2,413 | 0.2276 | 9.37 | 41.23 | 40.37 | −0.1044 | −0.1118 | 0.3597 | 1.508 |
| 9 | 2,412 | 0.3577 | 6.01 | 31.55 | 54.23 | −0.0614 | −0.0612 | 0.2890 | 1.180 |
| 10 | 2,413 | 0.9596 | 3.77 | 27.85 | 61.91 | −0.0659 | −0.0661 | 0.1693 | 0.974 |

Reading: **risk distance controls RESOLUTION, not edge.** Tight stops resolve (2 % neither); wide
stops do not (62 % neither). Both the target rate and the stop rate fall monotonically with width.
**No decile is gross-positive.** The deficit is present across the entire spectrum, so geometry
alone is not the repair.

The consequence for the mission's framing: `spearman(hit_target, gross_r)` on takeable is **+0.577**
at the *row* level (mechanically — a target hit IS +2R), but across *groups* the two point in
opposite directions, because the subsets that hit target more also stop out more. Any rule selected
for "reaches target more often" buys a worse gross. §6 reports both rankings for this reason.

---

## 3. Does the system's own belief predict outcome? No — it is inverted

Scripts `l3_belief.py` → `l3_BELIEF_V1.json`; `l3_belief_mech.py` → `l3_BELIEF_MECHANISM_V1.json`.

### 3a. Rank correlations (Spearman), belief vs realised

| belief field | pop ALL ρ vs gross | ALL ρ vs hit_target | TAKEABLE ρ vs gross | **TAKEABLE ρ vs hit_target** |
|---|---:|---:|---:|---:|
| `candidate_probability` | +0.1067 | −0.0655 | +0.0603 | **−0.0940** |
| `candidate_ev_r` | +0.1065 | −0.0655 | +0.0601 | **−0.0941** |
| `expectancy_r` | +0.1065 | −0.0655 | +0.0601 | −0.0941 |
| `expected_net_r` | +0.1410 | −0.1259 | +0.1016 | **−0.1553** |
| `candidate_confidence` | n/a (constant 0.55) | n/a | n/a | n/a |
| `fill_probability` | +0.0054 | −0.0654 | +0.0279 | −0.0575 |
| `entry_quality_fill_probability` | +0.0054 | −0.0654 | +0.0279 | −0.0575 |
| `execution_fill_probability` | −0.0897 | +0.0066 | −0.0295 | +0.0358 |
| `limit_fillability_probability` | −0.0897 | +0.0066 | −0.0295 | +0.0358 |
| `source_bound_signal_r` | +0.0261 | +0.0911 | −0.0416 | +0.0697 |
| `cost_r` | −0.1400 | **+0.1383** | −0.1025 | **+0.1661** |
| `spread_r` | −0.1210 | +0.1058 | −0.0865 | +0.1295 |
| `broker_pretrade_diag_expected_cost_r` | −0.0898 | +0.0911 | −0.0967 | +0.1003 |
| `risk_finalizer_rank` | −0.0347 | +0.0033 | −0.0239 | +0.0099 |
| `matched_sleeve_count` | +0.0201 | +0.0191 | −0.0024 | +0.0090 |
| `effective_admission_count` | +0.0366 | +0.0500 | +0.0055 | +0.0366 |
| `ev_minus_cost_r` | +0.1410 | −0.1259 | +0.1016 | −0.1553 |

**Every forecast field is negatively rank-correlated with reaching the target it forecasts.** The
strongest *positive* predictor of a target hit in the whole table is `cost_r` (+0.1661) — the term
the gate uses to refuse.

### 3b. Decile table, `candidate_probability`, TAKEABLE

| decile | n | predicted p | realised gross R | hit target % | full stop % |
|---:|---:|---:|---:|---:|---:|
| 1 | 2,413 | 0.65472 | −0.14675 | **20.47** | 61.46 |
| 2 | 2,412 | 0.69084 | −0.17680 | 15.92 | 55.39 |
| 3 | 2,413 | 0.70927 | −0.08022 | 15.09 | 49.15 |
| 4 | 2,412 | 0.72921 | −0.07554 | 12.60 | 45.77 |
| 5 | 2,413 | 0.74486 | −0.11813 | 10.82 | 45.42 |
| 6 | 2,412 | 0.76057 | −0.12198 | 10.57 | 43.91 |
| 7 | 2,412 | 0.79124 | −0.12659 | 11.15 | 48.05 |
| 8 | 2,413 | 0.82911 | −0.10222 | 13.93 | 48.45 |
| 9 | 2,412 | 0.87042 | −0.05335 | 12.65 | 44.03 |
| 10 | 2,413 | 0.92761 | −0.03759 | **4.02** | 36.47 |

Top-minus-bottom: gross **+0.1092**, hit rate **−0.1645**. Confidence rises 41.7 % (0.655 → 0.928);
the full-target rate falls **5.09×**.

On ALL (n=27,658) the same shape: D1 p=0.65517 hit 17.64 %; D10 p=0.92287 hit **5.03 %**;
tmb_gross +0.2132, tmb_hit −0.1262.

`expected_net_r` TAKEABLE deciles: D1 pred −2.64072 hit 18.32 % gross −0.27188 → D10 pred +1.17689
hit **3.23 %** gross −0.05328. tmb_gross +0.2186, tmb_hit −0.1509.

### 3c. Why it is inverted — belief is a variance suppressor, not an edge detector

`l3_BELIEF_MECHANISM_V1.json`. Drivers of `candidate_probability` (Spearman, TAKEABLE n=24,125):

| driver | ρ |
|---|---:|
| `fill_probability` | **+0.7118** |
| `cost_r` | **−0.4782** |
| `spread_r` | −0.4384 |
| `risk_distance_pct_of_price` | +0.2253 |
| `source_bound_signal_r` | −0.1321 |
| `execution_fill_probability` | −0.0608 |
| `abs_entry_offset_r` | +0.0400 |
| `implied_target_r` | −0.0017 |

And vs movement: `excursion_total_r` **−0.1497**, `mfe_r` −0.0738, `neither` **+0.1205**.

Mechanism decile table (`candidate_probability`, TAKEABLE):

| dec | n | pred | neither % | hit % | stop % | mfe R | mae R | excursion R | riskD % | gross R |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2,413 | 0.6547 | 12.14 | 20.47 | 61.46 | 3.040 | −2.974 | 6.014 | 0.10611 | −0.1468 |
| 2 | 2,412 | 0.6908 | 20.94 | 15.92 | 55.39 | 2.543 | −2.433 | 4.976 | 0.15109 | −0.1768 |
| 3 | 2,413 | 0.7093 | 26.77 | 15.08 | 49.15 | 2.233 | −2.027 | 4.260 | 0.17009 | −0.0802 |
| 4 | 2,412 | 0.7292 | 28.77 | 12.60 | 45.77 | 2.273 | −1.945 | 4.218 | 0.20873 | −0.0755 |
| 5 | 2,413 | 0.7449 | 30.50 | 10.82 | 45.42 | 2.450 | −1.833 | 4.283 | 0.26792 | −0.1181 |
| 6 | 2,412 | 0.7606 | 35.95 | 10.57 | 43.91 | 1.865 | −1.767 | 3.632 | 0.25262 | −0.1220 |
| 7 | 2,412 | 0.7912 | 34.49 | 11.15 | 48.05 | 1.882 | −1.805 | 3.687 | 0.18231 | −0.1266 |
| 8 | 2,413 | 0.8291 | 31.29 | 13.92 | 48.45 | 2.057 | −1.942 | 3.999 | 0.21287 | −0.1022 |
| 9 | 2,412 | 0.8704 | 31.51 | 12.65 | 44.03 | 2.074 | −1.633 | 3.707 | 0.23487 | −0.0534 |
| 10 | 2,413 | 0.9276 | 34.11 | 4.02 | 36.47 | 2.208 | −1.780 | 3.988 | 0.30576 | −0.0376 |

**High belief = wide stop = the trade does nothing.** `neither` rises 12.1 % → 34.1 %; total
excursion falls 6.01 R → 3.99 R. In a pool whose mean is negative, compressing outcomes toward zero
*improves* the mean — which is the entire source of belief's apparent +0.06 correlation with gross R.
It is measuring quietness and being read as skill.

The inversion survives conditioning on movement (`belief_within_movement_stratum`, quintiles of
total excursion):

| excursion quintile | n | mean excursion R | belief Q1 hit | belief Q5 hit | Q1 gross | Q5 gross |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 4,826 | 1.027 | 0.0000 | 0.0000 | −0.1373 | −0.0389 |
| 2 | 4,824 | 1.987 | 0.0259 | 0.0166 | −0.1817 | +0.0271 |
| 3 | 4,825 | 3.057 | 0.2363 | 0.1699 | −0.0337 | +0.0156 |
| 4 | 4,825 | 4.731 | 0.2611 | 0.1617 | −0.1470 | −0.0823 |
| 5 | 4,825 | 10.580 | 0.2114 | 0.1140 | −0.2766 | −0.1320 |

At every stratum with resolution, higher belief means a **lower** target rate.

### 3d. The one place belief works

`l3_UNUSED_V1.json` → `belief_inside_liquidity_sweep_reclaim`, n=4,475 takeable:
ρ(belief, gross) +0.0472, ρ(belief, fill-honest) +0.0612.

| quintile | n | p | hit | honest hit | gross R | fill-honest R |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 895 | 0.6621 | 0.2045 | 0.2112 | −0.1241 | −0.1356 |
| 2 | 895 | 0.7050 | 0.1709 | 0.2022 | −0.0476 | −0.0823 |
| 3 | 895 | 0.7373 | 0.1821 | 0.2078 | −0.0204 | −0.0477 |
| 4 | 895 | 0.7900 | 0.1620 | 0.1709 | −0.0869 | −0.1169 |
| 5 | 895 | 0.8783 | 0.1575 | 0.1911 | **+0.0715** | **+0.0294** |

`cand_prob ≥ 0.85 AND family = liquidity_sweep_reclaim` is the **only** belief-conditioned rule that
is positive in both split halves at the fill-honest contract (§6). Belief is not globally useless —
it is useless *pooled across families* and mildly useful inside one.

---

## 4. Field ranking — nothing separates a winner from a stop

Script `l3_rank.py` → `l3_FIELD_RANKING_V1.json`. Information Value, AUC and Cohen's d computed
identically for numeric (decile-binned) and categorical fields; every field stamped PRE (known at
the decision instant) or POST (path-derived leakage).

### 4a. RAW population (3,072 vs 15,057, base 0.1695) — dominated by the artifact

| field | pos | IV | AUC | d |
|---|---|---:|---:|---:|
| `mkt_r_open` | PRE | 1.349 | 0.622 | 0.485 |
| `mkt_r_prev_close` | PRE | 1.322 | 0.614 | 0.484 |
| `entry_offset_r` | PRE | 1.322 | 0.614 | 0.484 |
| `born_state` | PRE | 1.313 | — | — |
| `abs_entry_offset_r` | PRE | 0.573 | 0.372 | −0.475 |
| `route_family`/`origin_family`/`framework` | PRE | 0.501 | — | — |
| `source_bound_signal_r` | PRE | 0.263 | 0.566 | 0.253 |
| `symbol` | PRE | 0.257 | — | — |
| `stop_loss` | PRE | 0.105 | 0.534 | 0.180 |
| `entry_price` | PRE | 0.093 | 0.534 | 0.180 |
| `take_profit_1` | PRE | 0.089 | 0.534 | 0.179 |
| `old_proxy_vs_broker_calibrated_delta_r` | PRE | 0.070 | 0.545 | 0.093 |
| `risk_distance` | PRE | 0.068 | 0.523 | 0.058 |
| `expected_cost_r`/`cost_r`/`cost_over_target` | PRE | 0.065 | 0.554 | 0.107 |
| `session_bucket` | PRE | 0.064 | — | — |
| `kill_zone`/`authority_session` | PRE | 0.063 | — | — |
| `miss_reason` | PRE | 0.063 | — | — |

The top four are all the same quantity — the signed distance from the decision-instant market to
`entry_price` — i.e. the W0-capture artifact, not trade shape.

### 4b. TAKEABLE population (3,069 vs 11,534, base 0.2102) — the artifact removed

| field | pos | IV | AUC | d |
|---|---|---:|---:|---:|
| `symbol` | PRE | 0.249 | — | — |
| `miss_reason` | PRE | 0.098 | — | — |
| `broker_pretrade_diag_expected_cost_r` | PRE | 0.093 | 0.518 | −0.008 |
| `risk_finalizer_reason` | PRE | 0.091 | — | — |
| `expected_cost_r`/`cost_r`/`cost_over_target` | PRE | 0.088 | 0.562 | 0.068 |
| `selector_reason`/`effective_selector_reason` | PRE | 0.088 | — | — |
| `final_blocker_class` | PRE | 0.080 | — | — |
| `commission_r` | PRE | 0.079 | 0.505 | 0.099 |
| `entry_price` | PRE | 0.072 | 0.507 | 0.081 |
| `pretrade_cost_packet_status` | PRE | 0.070 | — | — |
| `broker_pretrade_cost_executable` | PRE | 0.070 | — | — |
| `stop_loss` | PRE | 0.068 | 0.507 | 0.081 |
| `spread_r` | PRE | 0.067 | 0.548 | 0.054 |
| `risk_per_trade_pct` | PRE | 0.066 | — | — |
| `expected_net_r`/`ev_minus_cost_r` | PRE | 0.064 | 0.443 | −0.084 |
| `take_profit_1` | PRE | 0.060 | 0.507 | 0.081 |
| `effective_selector_action` | PRE | 0.057 | — | — |
| `admission_risk_class` | PRE | 0.057 | — | — |

**Every AUC is between 0.44 and 0.57.** The best single field in the entire emitted schema
discriminates a full-target winner from a full stop at a coin flip plus 6 points.

### 4c. Continuous winner-vs-stop profile, TAKEABLE (`l3_profile.py` → `l3_PROFILE_V1.json`)

Top 16 by |Cohen's d|, briefed cohorts (3,069 vs 11,534):

| field | d | mean win | mean stop | honest-cohort mean diff |
|---|---:|---:|---:|---:|
| `risk_distance_pct_of_price` | **−0.1517** | 0.11572 | 0.14863 | −0.00821 |
| `candidate_ev_r` | −0.1453 | 0.82699 | 0.85646 | −0.00400 |
| `candidate_probability` | −0.1449 | 0.75040 | 0.76175 | −0.00153 |
| `commission_r` | +0.0994 | 0.09053 | 0.07653 | +0.00674 |
| `fill_probability` | −0.0961 | 0.88402 | 0.88870 | −0.00050 |
| `expected_net_r` | −0.0843 | −0.10687 | +0.01044 | +0.03059 |
| `swap_cost_r` | +0.0842 | 0.02122 | 0.01831 | +0.00047 |
| `setup_dup_rank` | −0.0818 | 1.95764 | 2.40732 | −0.26750 |
| `entry_price` | +0.0813 | 17203.49 | 15257.26 | −78.35 |
| `source_bound_signal_r` | +0.0724 | 96469.82 | 91164.63 | +6369.05 |
| `cost_r` | +0.0676 | 0.93385 | 0.84602 | −0.03459 |
| `effective_admission_count` | +0.0590 | 0.66927 | 0.64097 | +0.06109 |
| `spread_r` | +0.0545 | 0.80210 | 0.73118 | −0.04179 |
| `utc_hour` | −0.0536 | 10.24373 | 10.57161 | +0.15216 |
| `execution_fill_probability` | +0.0428 | 0.81354 | 0.80442 | −0.01641 |
| `risk_finalizer_rank` | −0.0344 | 36.92115 | 37.86111 | +0.62053 |

**Maximum |d| = 0.152.** Conventionally, d < 0.2 is "negligible". The winners and the stops are the
same distribution on every quantity the engine knows.

---

## 5. Every gate anti-selects on the outcome it exists to protect

Script `l3_gate_shape.py` → `l3_GATE_SHAPE_V1.json`. TAKEABLE n=24,125, pool hit_target 12.721 %,
pool mean excursion 4.2764 R.

| gate | keeps n | keep % | **kept hit %** | **refused hit %** | ratio | kept gross | refused gross | kept riskD % | refused riskD % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `spread_cap_0.10` (`broker_net_cost_engine.py:859-866`) | 9,615 | 39.86 | 7.53 | 16.16 | **2.146** | −0.0808 | −0.1192 | 0.324 | 0.133 |
| `total_cost_cap_0.15` (`:923-927`) | 7,353 | 30.48 | 5.78 | 15.76 | **2.727** | −0.0709 | −0.1184 | 0.386 | 0.132 |
| **BOTH live cost gates** | 6,980 | 28.93 | **5.46** | **15.68** | **2.872** | −0.0837 | −0.1121 | 0.392 | 0.135 |
| spread cap at 7.3× corrected | 19,357 | 80.24 | 11.16 | 19.06 | 1.708 | −0.0836 | −0.1865 | 0.239 | 0.090 |
| spread cap at 8.5× corrected | 19,881 | 82.41 | 11.38 | 19.02 | 1.671 | −0.0827 | −0.2032 | 0.236 | 0.085 |
| both gates at 7.3× corrected | 14,826 | 61.45 | 8.63 | 19.24 | 2.228 | −0.0873 | −0.1304 | 0.276 | 0.103 |
| `scheduler_materialized` | 3,951 | 16.38 | 5.97 | 14.04 | 2.351 | −0.0938 | −0.1059 | 0.381 | 0.176 |
| **`selector_action == trade`** | **21** | **0.09** | **0.00** | 12.73 | **∞** | −0.0179 | −0.1040 | 0.468 | 0.209 |
| `effective_order_type != none` | 19,732 | 81.79 | 12.81 | 12.31 | 0.961 | −0.1003 | −0.1203 | 0.189 | 0.300 |
| `final_blocker none/nonfatal` | 6,980 | 28.93 | 5.46 | 15.68 | 2.872 | −0.0837 | −0.1121 | 0.392 | 0.135 |

Also: kept `neither` rate 42.32 % vs refused 23.08 %; kept mean excursion 3.0912 R vs refused
4.7590 R (ratio 1.540).

**Three findings.**

1. **The cost gate is a risk-distance filter wearing a cost mask.** `cost_r` is R-denominated
   (spread ÷ risk distance), so a tight stop mechanically produces a large `cost_r`. The gate keeps
   the widest-stop 28.93 % (median risk distance 0.2155 % of price) and refuses the tightest
   71.07 % (median 0.0724 %). It is selecting for trades that resolve less — 42.3 % of what it
   keeps touches neither target nor stop inside the horizon.
2. **Correcting the measured 7.3–8.5× spread overcharge roughly halves the anti-selection** at the
   spread limb (ratio 2.146 → 1.708) and raises kept share 39.9 % → 80.2 %. The gate's *direction*
   is wrong partly because its *input* is wrong.
3. **`selector_action == trade` fires on 21 of 24,125 candidates and not one of them reaches the
   declared target.** 33.33 % full stop, 57.14 % neither. That is the terminal selection in the
   stack.

---

## 6. The interpretable profile, split-half honest

Scripts `l3_rules.py` → `l3_RULES_V1.json`; `l3_profile_deep.py` → `l3_PROFILE_DEEP_V1.json`;
discovery-only CART at `l3_tree.py` → `l3_TREE_V1.json`.

94 pre-decision predicates, all 1- and 2-condition combinations, **2,975 rules scored**, minimum 300
rows in *each* half. H1 = January 1–15, H2 = January 16–31. Base: n=24,125, hit 0.1263 / 0.1280,
gross −0.1110 / −0.0976, fill-honest −0.1322 / −0.1208.

### 6a. Top 14 by worst-half full-target rate

| rule | n | hit H1 | hit H2 | gross H1 | gross H2 |
|---|---:|---:|---:|---:|---:|
| **`cost_r>0.40 AND sess=london`** | 860 | 0.2857 | 0.3180 | **+0.0576** | **+0.0467** |
| `riskdist<0.05% AND hour10-14` | 869 | 0.2679 | 0.2849 | −0.0016 | −0.0534 |
| `riskdist<0.05% AND hour07-12` | 1,290 | 0.2584 | 0.2948 | +0.0748 | +0.0026 |
| `cost_r>0.25 AND sym=GER40` | 667 | 0.2549 | 0.2742 | +0.0035 | −0.0301 |
| `riskdist<0.05% AND sess=london` | 908 | 0.2453 | 0.3169 | +0.0279 | +0.0999 |
| `spread_r>0.50 AND fam=structural_distance_extreme` | 783 | 0.2415 | 0.2762 | −0.2521 | −0.1413 |
| `cost_r>0.80 AND fam=structural_distance_extreme` | 793 | 0.2410 | 0.2751 | −0.2398 | −0.1547 |
| `spread_r>0.20 AND sym=GER40` | 751 | 0.2386 | 0.2661 | −0.0020 | −0.0107 |
| `cost_r>0.40 AND fam=liquidity_sweep_reclaim` | 1,655 | 0.2382 | 0.2473 | −0.0111 | −0.0513 |
| `riskdist<0.10% AND sym=GER40` | 749 | 0.2380 | 0.2655 | −0.0045 | −0.0199 |
| `cost_r>0.25 AND sess=london` | 1,543 | 0.2361 | 0.2729 | +0.0094 | +0.0364 |
| `riskdist<0.05% AND cost_r>0.80` | 2,218 | 0.2309 | 0.2480 | −0.1873 | −0.2008 |
| `spread_r>0.20 AND sess=london` | 1,259 | 0.2304 | 0.2818 | +0.0191 | +0.0732 |
| `riskdist<0.05% AND hour06-10` | 1,201 | 0.2279 | 0.2643 | −0.0392 | −0.0874 |

### 6b. Top 14 by worst-half gross R

| rule | n | gross H1 | gross H2 | hit H1 | hit H2 |
|---|---:|---:|---:|---:|---:|
| `cand_prob>=0.85 AND fam=liquidity_sweep_reclaim` | 672 | +0.0534 | +0.1435 | 0.1429 | 0.1778 |
| `cost_r<=0.40 AND sym=BTCUSD` | 786 | +0.0598 | +0.0472 | 0.1262 | 0.1045 |
| **`cost_r>0.40 AND sess=london`** | 860 | +0.0576 | +0.0467 | 0.2857 | 0.3180 |
| `riskdist>=0.20% AND sym=BTCUSD` | 761 | +0.0359 | +0.0373 | 0.1126 | 0.0959 |
| `riskdist<0.05% AND sess=london` | 908 | +0.0279 | +0.0999 | 0.2453 | 0.3169 |
| `fam=liquidity_sweep_reclaim AND sess=london` | 868 | +0.0271 | +0.1043 | 0.2297 | 0.2241 |
| `fam=liquidity_sweep_reclaim AND hour10-14` | 796 | +0.0264 | +0.0467 | 0.1944 | 0.2150 |
| `side=SHORT AND sess=london` | 2,192 | +0.0226 | +0.0378 | 0.1731 | 0.1692 |
| `spread_r>0.20 AND sess=london` | 1,259 | +0.0191 | +0.0732 | 0.2304 | 0.2818 |
| `cost_r>0.15 AND sess=london` | 2,430 | +0.0164 | +0.0100 | 0.1899 | 0.2266 |
| `cost_r>0.25 AND sess=london` | 1,543 | +0.0094 | +0.0364 | 0.2361 | 0.2729 |
| `cand_prob<0.80 AND sess=london` | 2,579 | +0.0210 | +0.0086 | 0.1774 | 0.1770 |
| `cand_prob>=0.80 AND fam=liquidity_sweep_reclaim` | 1,171 | +0.0081 | +0.0709 | 0.1492 | 0.1725 |
| `sess=london AND born=at_limit` | 2,939 | +0.0072 | +0.0226 | 0.1774 | 0.1818 |

**8 of the top 14 contain `session = london`.**

### 6c. Top by worst-half FILL-HONEST R — the contract a limit order can actually take

Only five rules are positive in both halves once the entry must be traded first:

| rule | n | fh H1 | fh H2 | honest hit H1 | honest hit H2 |
|---|---:|---:|---:|---:|---:|
| `cost_r<=0.40 AND sym=BTCUSD` | 786 | +0.0498 | +0.0444 | 0.1262 | 0.1045 |
| `cand_prob>=0.85 AND fam=liquidity_sweep_reclaim` | 672 | +0.0307 | +0.0533 | 0.1933 | 0.1936 |
| `riskdist>=0.20% AND sym=BTCUSD` | 761 | +0.0254 | +0.0345 | 0.1126 | 0.0959 |
| `sym=GER40 AND born=resting` | 675 | +0.0216 | +0.1725 | 0.2072 | 0.2480 |
| `fam=current_fvg_fill AND sym=GER40` | 674 | +0.0138 | +0.0792 | 0.2185 | 0.2312 |

### 6d. Decomposition of the headline rule

`l3_PROFILE_DEEP_V1.json`. Seven-cell decomposition, TAKEABLE:

| cell | n | hit % | honest hit % | gross R | fill-honest R | net @ frozen cost | net @ spread/7.3 | riskD % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ALL_TAKEABLE | 24,125 | 12.72 | 15.37 | −0.1039 | −0.1262 | −0.7662 | −0.2796 | 0.2092 |
| `london` only | 4,055 | 15.54 | 16.00 | −0.0176 | −0.0820 | −0.3123 | −0.1338 | 0.1804 |
| `cost_r>0.40` only | 9,498 | 18.52 | 18.49 | −0.1498 | −0.1769 | −1.5694 | −0.4628 | 0.1141 |
| **RULE: both** | **860** | **29.88** | **25.12** | **+0.0532** | −0.0899 | −0.7107 | −0.1849 | 0.0517 |
| `cost>0.40` NOT london | 8,638 | 17.39 | 17.83 | −0.1700 | −0.1855 | −1.6549 | −0.4905 | 0.1203 |
| london NOT `cost>0.40` | 3,195 | 11.67 | 13.55 | −0.0367 | −0.0798 | −0.2051 | −0.1200 | 0.2151 |
| neither | 11,432 | 8.20 | 13.30 | −0.0846 | −0.0970 | −0.2557 | −0.1719 | 0.2867 |

**The interaction is real, not additive.** London alone −0.0176; `cost_r>0.40` alone −0.1498;
together **+0.0532**. It is the only gross-positive cell of the seven.

Split halves: H1 n=511 hit 0.2857 gross +0.0576 fh −0.0686 | H2 n=349 hit 0.3180 gross +0.0467
fh −0.1212.

Gate disposition of the rule: **100.0 % refused by the live cost gates**, `final_blocker_class =
cost_authority` on all 860; **0.0 % scheduler-materialised; 0.0 % `selector_action == trade`**.
It is 3.565 % of the takeable pool and the system takes none of it.

Composition — families:

| family | n | hit | gross R | fill-honest R | H1 gross | H2 gross |
|---|---:|---:|---:|---:|---:|---:|
| `liquidity_sweep_reclaim` | 242 | 0.3347 | +0.1394 | −0.0004 | +0.1138 | +0.1850 |
| `structural_distance_extreme` | 218 | 0.3486 | +0.1516 | −0.1051 | +0.0286 | +0.3022 |
| `current_fvg_fill` | 146 | 0.3425 | +0.1917 | **+0.1618** | +0.3694 | −0.0859 |
| `cross_asset_lead_lag` | 101 | 0.2673 | −0.1334 | −0.3876 | −0.0869 | −0.2105 |
| `current_ob_retest` | 46 | **0.0000** | −0.6195 | −0.6476 | −0.4371 | −0.8367 |
| `displacement_continuation` | 46 | 0.2609 | −0.1323 | −0.1323 | +0.0136 | −0.3397 |
| `current_breaker_re_entry` | 42 | 0.1667 | −0.0730 | −0.0730 | −0.4982 | +0.3523 |

Symbols (n≥20): UK100 210 (hit 0.2095, gross −0.2568) | EURGBP 85 (0.3412, +0.0711) |
JP225 80 (0.3000, **+0.3026**) | EURJPY 74 (0.2432, +0.0580) | NZDUSD 67 (0.4030, **+0.2967**) |
US30_cash 66 (0.3485, +0.1129) | USDCAD 44 (0.3864, +0.1591) | GBPUSD 40 (0.3000, −0.1000) |
USDCHF 38 (0.3947, +0.1842) | CHFJPY 37 (0.2703, +0.0429).

Hours (UTC): 07→207, 08→261, 09→203, 10→105, 11→70, 12→14. Sides: SHORT 488 / LONG 372.

**Honest limits on this rule, stated plainly.** Its gross +0.0532 does **not** survive the fill
requirement (fill-honest −0.0899); only `current_fvg_fill` and JP225/NZDUSD/US30/USDCAD stay
positive there. And it does not clear its own costs at any measured level: net −0.7107 at the frozen
model, **−0.1849** even at the 7.3× corrected spread. It is the best-*shaped* population in the
pool — not a profitable one.

### 6e. Discovery CART, split-half (`l3_TREE_V1.json`)

Depth 3, `min_samples_leaf=250`, fit H1 / test H2. Best leaf: `cost_r > 0.2727 AND
risk_distance_pct_of_price > 0.0712 AND swap_cost_r > 0.0088` — train n=3,524 hit 0.2228 gross
−0.1118; **test n=2,709 hit 0.2348 gross −0.1420**. A stable **1.83×** lift in target rate whose
gross is *worse* than base in both halves. This is the §2 anti-correlation in one leaf, and it is
why §6a and §6b are reported separately.

---

## 7. Fields the system computes and does not use

Script `l3_unused.py` → `l3_UNUSED_V1.json`.

### 7a. The ordering defect — the strongest discriminator is computed too late

`limit_marketable_at_decision` is the only field encoding "is my limit already through the market".
Written at `src/components/poi_execution_lifecycle.py:224`; consumed only by the scheduler
(`src/research/moonshot_scheduler_v4_best_trade_allocator.py:17462`, `:17530`, `:17820`, `:18386`).

**It is 85.19 % null, and its non-null count (4,095) is exactly the scheduler-materialised count
(4,095).** It is written at a stage that 83.6 % of candidates never reach, because the cost gate has
already refused 71 % of them.

| born state | n | field populated | mean gross R | cost gate refuses |
|---|---:|---:|---:|---:|
| `born_past_stop` | 3,516 | **4.10 %** | **−0.9948** | 93.6 % |
| `born_marketable` | 1,265 | 9.96 % | −0.2566 | 80.5 % |
| `born_at_limit` | 14,911 | 19.56 % | −0.0904 | 68.2 % |
| `born_resting` | 7,949 | 11.44 % | −0.1049 | 74.9 % |

The 3,516 rows worth **−0.9948 R each** — the single largest identified defect in the pool
(W0-capture: +0.11332 R/trade to remove) — have this field populated on **4.10 %** of themselves.
The information needed to reject them (`entry_price`, and the decision-instant market price) exists
at candidate generation. The field that would express it is computed **after** the gate that would
have used it. **The pool's top-IV discriminator (born_state, IV 1.313) is not a discovery about
markets; it is a discovery about pipeline ordering.**

### 7b. Should predict and does not

`candidate_confidence` is the constant **0.55** on all 27,658 rows with
`confidence_default_applied = True` on 100 % of them. It cannot correlate with anything. It is a
placeholder occupying the name of a belief.

Sixteen fields carry **zero information** — one distinct value across the whole pool:
`dynamic_geometry_policy` (`momentum_exhaustion`), `selected_policy_for_expected_net_r`
(`momentum_exhaustion`), `decision_timeframe` (M15), `market_timeframe` (M15),
`expected_slippage_r` (0.02), `fallback_execution_surcharge_r` (0.0),
`guarded_market_fallback_extra_cost_r` (0.0), `candidate_confidence` (0.55),
`confidence_default_applied` (True), `source_completeness` (1.0), `fill_realism_executable` (True),
`entry_fill_executable` (True), `missed_opportunity_r_scoreability_status`,
`missed_opportunity_non_executable_diagnostic_scoreable`, `path_source_timeframe` (M1),
`path_arm_id` (S0R0).

`fill_realism_executable` and `entry_fill_executable` are **True on every one of 27,658 rows** — two
named fill checks that have never once said no.

### 7c. Predicts unexpectedly

| field | n | ρ vs hit_target | ρ vs gross R | ρ vs fill-honest R |
|---|---:|---:|---:|---:|
| `cost_r` | 24,125 | **+0.1661** | −0.1025 | −0.1094 |
| `expected_net_r` | 24,125 | −0.1553 | +0.1016 | +0.1025 |
| `risk_distance_pct_of_price` | 24,125 | −0.1603 | +0.1003 | **+0.1397** |
| `broker_pretrade_diag_expected_cost_r` | 17,145 | +0.1003 | −0.0967 | −0.0953 |
| `spread_r` | 24,125 | +0.1295 | −0.0865 | −0.0916 |
| `candidate_probability` | 24,125 | −0.0940 | +0.0603 | +0.0569 |
| `swap_cost_r` | 24,125 | +0.0749 | −0.0449 | −0.0552 |
| `source_bound_signal_r` | 24,125 | +0.0697 | −0.0416 | −0.0690 |
| `execution_fill_probability` | 24,012 | +0.0358 | −0.0295 | −0.0355 |
| `mkt_r_prev_close` | 24,125 | −0.0185 | +0.0291 | +0.0285 |
| `fill_probability` | 24,125 | −0.0575 | +0.0279 | +0.0230 |
| `risk_finalizer_rank` | 24,125 | +0.0099 | −0.0239 | −0.0362 |
| `risk_per_trade_pct` | 24,125 | −0.0272 | +0.0149 | −0.0013 |
| `setup_dup_rank` | 24,125 | −0.0377 | +0.0081 | +0.0103 |
| `utc_hour` | 24,125 | −0.0214 | +0.0080 | +0.0090 |
| `abs_entry_offset_r` | 24,125 | −0.0407 | +0.0057 | +0.0097 |
| `effective_admission_count` | 24,125 | +0.0366 | +0.0055 | −0.0004 |

The three strongest predictors of a target hit are **all cost terms**, all positive, and all used by
the system with the opposite sign.

---

## 8. Engine scoring vs measured price path — four symbols disagree, and the mission's cohort inherits it

Scripts `l3_scoring_gap.py`, `l3_scoring_gap2.py`, `l3_scoring_gap3.py`, `l3_scoring_case.py`,
`l3_scoring_repair.py` → `l3_SCORING_GAP{,2,3}_V1.json`, `l3_SCORING_CASE_V1.json`,
`l3_SCORING_REPAIR_V1.json`.

On rows where the **fill-honest M1 walk** says the +2R target was touched first, the engine's own
`gross_r`:

| group | n | honest-target n | engine mean | engine median | engine `ge_target` % on those rows |
|---|---:|---:|---:|---:|---:|
| OTHER20 | 19,251 | 2,772 | **+1.9532** | **+2.0000** | **97.01 %** |
| **SUSPECT4** (XAUUSD, XAGUSD, USDJPY, EURUSD) | 4,874 | 937 | **+0.7252** | **+0.7008** | **10.35 %** |

Per symbol, engine `gross_r` on honest-target rows: XAGUSD +0.5437 (8.98 % ge_target) | USDJPY
+0.6510 (8.59 %) | EURUSD +0.7949 (12.61 %) | XAUUSD +0.7951 (10.89 %) — against every other symbol
at +1.876 … +2.000 and 94.32 % … 100.00 %.

The engine's `gross_r` also loses its discrete structure on exactly those four, **on both sides**:
share of rows at exactly +2R or −1R is **40.02 – 43.80 %** for SUSPECT4 against **58.28 – 71.17 %**
for the other twenty. On honest-*stop* rows OTHER20 books full_stop on 97.75 % (mean −0.9544) while
SUSPECT4 books it on **73.81 %** (mean −0.6053). Correlation of engine `gross_r` with
`r_at_path_end` on SUSPECT4 honest-target rows is **+0.0525** — none.

Geometry is *not* the cause: on sampled cases `take_profit_1` implies exactly 2.0000 R and
`stop_loss` exactly 1.0000 R, the sidecar's `risk_distance` matches the pool's to 1e-9, and
`policy_target_r` median is 2.0000 on every symbol. The two sides walked different price
information.

### 8a. Self-correction — the one-sided read overstates this 9.3×

Reading only the target side gives +1.2748 R × 937 rows = **+1,194.49 R**, i.e. +0.2451 R per
SUSPECT4 trade and +0.0495 per takeable pool trade. **That is wrong**, because the engine
under-books stops on the same symbols by +1,000.6 R in the other direction. Re-scoring every
takeable row at the path's own contract (honest target → +2.0, honest stop → −1.0, no_fill → 0,
else `r_at_path_end`):

| group | n | engine gross R | path contract R | Δ per trade | target-side ΔR | stop-side ΔR | other ΔR |
|---|---:|---:|---:|---:|---:|---:|---:|
| SUSPECT4 | 4,874 | −0.09206 | −0.06558 | **+0.02648** | +1,194.5 | −1,000.6 | −64.8 |
| OTHER20 | 19,251 | −0.10692 | −0.14190 | −0.03498 | +129.8 | −446.4 | −356.9 |
| ALL takeable | 24,125 | −0.10392 | −0.12648 | **−0.02257** | +1,324.3 | −1,447.0 | −421.7 |

**The economic repair is +0.00535 R per takeable pool trade, not +0.0495.** Pool-wide the engine is
in fact slightly *optimistic* against the path contract (−0.02257).

### 8b. What the finding actually is — measurement blindness, not lost money

SUSPECT4 is **20.20 % of takeable rows** but contributes ~3.6 % of the briefed winner cohort,
because the engine scores it to contract so rarely. XAUUSD's engine `ge_target` rate is **2.62 %**
against a fill-honest path rate of **21.30 %** — an **8.1×** per-symbol error.

Consequence for this lane and every later one: **the briefed 3,072-winner cohort is a biased sample
that structurally under-represents gold, silver, USDJPY and EURUSD by ~5.6×.** §4c's per-symbol
table shows it directly — XAUUSD briefed win-share 5.98 % vs honest 27.28 %; XAGUSD 5.32 % vs
28.84 %; USDJPY 4.48 % vs 26.94 %. Any lane that profiles "what a winner looks like" from
`outcome_band` will conclude those four instruments never win. **Use
`fill_honest_which_came_first`, not `outcome_band`, for anything per-symbol.**

Of the 11,534 takeable full stops, 54 are SUSPECT4 rows whose honest path says *target*, against
only 8 in all of OTHER20.

---

## 9. The winner in words

Measured description of the highest-quality population l3 found (`cost_r > 0.40 AND
session = london`, n=860, 29.88 % full-target rate = 2.35× base, +0.0532 R/trade gross, stable
across both halves):

- **When.** London morning, UTC hours 07–11, mode 08:00 UTC. 78.0 % of the cell sits in hours 07–09, 90.2 % in hours 07–10.
  Hour 08 is the best single hour in the whole pool on its own (n=1,652, 26.44 % win share,
  lift 1.26, gross **+0.0141** — one of only two positive hours).
- **What instrument.** Index and cross-rate, not the majors' quiet hours: UK100, EURGBP, JP225,
  EURJPY, NZDUSD, US30_cash, USDCAD, USDCHF, CHFJPY. Best behaved: JP225 (+0.3026), NZDUSD
  (+0.2967), USDCHF (+0.1842), USDCAD (+0.1591).
- **What structure.** Liquidity sweep / reclaim (n=242, +0.1394), structural distance extreme
  (n=218, +0.1516), FVG fill (n=146, +0.1917). **Order-block retest is the one to avoid — n=46,
  0.00 % target rate, −0.6195 R.**
- **What distance to stop.** **Very tight: 0.0517 % of price**, against 0.2092 % for the pool —
  a quarter of the typical stop. This is the entire reason `cost_r > 0.40`.
- **What volatility.** High realised movement: mfe +3.790 R, mae −3.350 R against a pool mfe of
  2.2625 R. Total excursion 7.140 R against a pool 4.2764 R.
- **How it resolves.** Fast — median **14 M1 bars to target** against the takeable full-target median of **31** (mean 39.54).
  Gross win rate 38.37 %, mean winner **+1.6922 R**, mean loser **−0.9672 R**, payoff 1.75:1
  (the pool's is 1.18:1).
- **Direction.** Mildly short-biased, 488 SHORT / 372 LONG. `side = SHORT AND sess = london` is
  itself positive in both halves (n=2,192, +0.0226 / +0.0378).
- **What the system thinks of it.** `candidate_probability` 0.7452 — dead average. The belief layer
  does not see it. The cost gate refuses **100 %** of it. The selector takes **0**.

In one sentence: **a tight-stopped sweep-reclaim or structural-extreme on an index or cross during
the first four hours of London, which resolves inside a quarter-hour, has twice the pool's chance of
paying 2R — and the stack rejects every one of them on a cost term that is large only because the
stop is tight.**

Session table for context (TAKEABLE, briefed win-share / lift / gross):
`london` 4,055 / 25.21 % / 1.20 / **−0.0176** — best major session;
`ny` 4,261 / 20.41 % / 0.97 / −0.0944; `tokyo` 1,176 / 21.16 % / 1.01 / −0.1146.
Two `moonshot_*` hour buckets are gross-positive: `h09_10` (n=312, 30.07 %, lift 1.43, **+0.0970**)
and `h13_14` (n=133, 32.77 %, lift 1.56, **+0.0125**).

Born-state: `born_at_limit` 14,911 / 22.27 % / −0.0904; `born_resting` 7,949 / 19.61 % / −0.1049;
`born_marketable` 1,265 / 14.04 % / **−0.2566** (the worst takeable state).

Family table (TAKEABLE, n / briefed win-share / honest win-share / gross / riskD % / neither %):
`current_fvg_fill` 7,135 / 18.94 / 23.43 / −0.1403 / 0.1884 / 22.6 —
`liquidity_sweep_reclaim` 4,475 / 25.10 / 26.22 / **−0.0415** / 0.1527 / 23.4 —
`displacement_continuation` 4,465 / 18.34 / 20.14 / −0.0888 / 0.3160 / 46.0 —
`cross_asset_lead_lag` 2,083 / 23.49 / 23.93 / −0.1307 / 0.1268 / 10.0 —
`structural_distance_extreme` 1,993 / 23.35 / 23.54 / −0.1820 / 0.0557 / 1.9 —
`current_ob_retest` 1,292 / 13.99 / 17.85 / −0.0736 / 0.1897 / 38.4 —
`session_open_range_break` 987 / 16.24 / 15.70 / −0.0747 / 0.2933 / 55.2 —
`current_breaker_re_entry` 793 / 22.43 / 24.11 / −0.0824 / 0.1557 / 15.3 —
`volatility_compression_expansion` 605 / 7.35 / 9.09 / −0.0868 / 0.5890 / 87.3 —
`regime_transition_break` 297 / 14.71 / 14.71 / **−0.0067** / 0.7385 / 88.2.

---

## 10. Caveats

- One month (January 2026), one arm (S0R0), true UTC. Nothing here is tested out-of-month; wave 2
  owns April/May, and February is used-once VAL.
- 2,975 rules were scored to find §6's profile. It is reported because it is stable across an
  honest split-half and because it tops **two** independent rankings, not because it survived a
  multiplicity correction — it has not been given one.
- `cost_r > 0.40 AND london` is gross-positive and **fill-honest-negative** (−0.0899). It is a
  shape finding, not a tradeable one.
- Per-symbol conclusions drawn from `outcome_band` are invalid on XAUUSD/XAGUSD/USDJPY/EURUSD (§8).
- The horizon is a hard 2 hours (W0-F3); nothing about holding beyond that is answerable here.
- Pseudo-replication (W0-F1) is not corrected in §4–§6; `setup_dup_rank` is carried as a predicate
  and `dup_rank=1` never entered a top-14 list.

## 11. Artifacts

`l3_COHORTS_V1.json` · `l3_COHORT_INTEGRITY_V1.json` · `l3_FIELD_RANKING_V1.json` ·
`l3_BELIEF_V1.json` · `l3_BELIEF_MECHANISM_V1.json` · `l3_GATE_SHAPE_V1.json` · `l3_TREE_V1.json` ·
`l3_PROFILE_V1.json` · `l3_RULES_V1.json` · `l3_PROFILE_DEEP_V1.json` · `l3_UNUSED_V1.json` ·
`l3_SCORING_GAP_V1.json` · `l3_SCORING_GAP2_V1.json` · `l3_SCORING_GAP3_V1.json` ·
`l3_SCORING_CASE_V1.json` · `l3_SCORING_REPAIR_V1.json` · `l3_RESULT.json`

Scripts: `l3_build.py` · `l3_rank.py` · `l3_belief.py` · `l3_belief_mech.py` · `l3_gate_shape.py` ·
`l3_tree.py` · `l3_cohort_integrity.py` · `l3_profile.py` · `l3_rules.py` · `l3_profile_deep.py` ·
`l3_unused.py` · `l3_scoring_gap.py` · `l3_scoring_gap2.py` · `l3_scoring_gap3.py` ·
`l3_scoring_case.py` · `l3_scoring_repair.py`

All under `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/`.
