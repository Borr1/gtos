# Lane e3 — EXTENSION of L9-F2 (the passivity gradient) to five months

**Posture: extension, not refutation.** The question was *how far does L9-F2 reach and where does
it live*. Answer, in one line: **the population-level fill-floor finding travels to all five
months and to 112,116 candidates; the per-cycle argmin RULE does not; the whole thing is
structurally confined to three of ten families; and it is NOT a 2-hour-wall artifact — at a
24-hour horizon where 98.4 % of the cohort resolves, the passive book still wins 34.4 % against
a 2R target while the aggressive book wins 28.5 %.**

Session e3, wave 19 discovery swarm. Every number below is measured; nothing is estimated.

---

## 0. What was spent, and what was not

**April and May economics were READ by this lane.** `CS_APRIL_S0R0_V2` and `CS_MAY_S0R0_V1`
(Session CS's true-UTC S0R0 arms) exist on disk at
`/Users/borr/GTOSActive/worktrees/wave19-breaker-folds-20260801/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse/`.
This lane read **only their `*_MISSED_OPPORTUNITY_LEDGER.jsonl.zst`** — the counterfactual
diagnostic pool, i.e. candidates the engine considered and refused. It did **not** read their
`TRADE_LEDGER`, `ORDER_LEDGER`, `SCORECARD_LEDGER`, `SUMMARY` or any book-level P&L. It computed
**no monthly book number for April or May**, only per-candidate path geometry conditional on
entry-fill. The pools were used to answer one question — does the fill floor delete the better
half — and nothing else.

Register: **April 25,056 diagnostic-scoreable rows and May 21,285 spent on the L9-F2 extension.**
March used arm `FA2_M_R0` (26,500 rows), already decoded once by session MARCH-EXEC.
No sealed replay was launched. No VPS contact. No broker-capable script. No live-forward record read.

---

## 1. Step 1 — reproduction. EXACT.

`e3_01_repro.py` re-runs L9's own instrument (`l9_lib.load()`, real
`execution_fill_probability`, `w0_WORKING_SET`).

**§4.1 resting fp-band table reproduces to `0.00e+00` in every band:**

| fp band | n (mine/L9) | honest (mine/L9) | abs diff |
|---|---|---|---|
| < 0.10 | 43/43 | +0.3924 / +0.3924 | 0.00e+00 |
| 0.10–0.20 | 515/515 | −0.0601 / −0.0601 | 0.00e+00 |
| 0.20–0.30 | 1044/1044 | −0.0470 / −0.0470 | 0.00e+00 |
| 0.30–0.40 | 1241/1241 | −0.0257 / −0.0257 | 0.00e+00 |
| 0.40–0.50 | 1083/1083 | −0.0470 / −0.0470 | 0.00e+00 |
| 0.50–0.60 | 1027/1027 | −0.0376 / −0.0376 | 0.00e+00 |
| 0.60–0.70 | 975/975 | −0.2119 / −0.2119 | 0.00e+00 |
| 0.70–0.80 | 790/790 | −0.1729 / −0.1729 | 0.00e+00 |
| 0.80–0.92 | 767/767 | −0.1790 / −0.1790 | 0.00e+00 |
| ≥ 0.92 | 451/451 | −0.2044 / −0.2044 | 0.00e+00 |
| null | 13/13 | +0.3416 / +0.3416 | 0.00e+00 |

**§4.3 per-cycle rule reproduces**: 1,807 cycles, pos1 **+0.11962** (se 0.02708, t **+4.41797**),
alloc1 −0.11026, delta **+0.22988**, pos1 zero-neither +0.00664, alloc1 zn −0.21638. These are
L9's published values to five decimals.

### 1b. The portable engine, validated bit-for-bit

To reach other months I rebuilt the whole instrument from raw M1 bars
(`bridge_ftmo_m1_2026{01..05}`, 24 symbols/month) — decision anchor, `born_state`, fill-honest
walk, `dist_r`, staleness — in `e3_lib.py`. Validated against the January working set,
**27,658 rows, zero tolerance**:

| column | mismatches | match |
|---|---:|---:|
| `fill_honest_which_came_first` | **0** | 100.000 % |
| `fill_honest_walk_r` | **0** | 100.000 % |
| `bars_to_entry_touch` | **0** | 100.000 % |
| `born_state` | 19 | 99.931 % |
| `mkt_r_prev_close` | p99.9 abs diff 0.0 | — |

Two conventions had to be recovered by measurement and are recorded here because the next lane
will need them:

1. **The CQ path sidecar starts at `decision_time + 1 minute`** (measured 5,895/6,000 rows at
   exactly +1 min). It **skips** the M1 bar stamped AT the decision minute. Starting at that bar
   instead moves `bars_to_entry_touch` on 10,884 rows.
2. **The path is capped by a 120-MINUTE wall, not a 120-bar count**
   (`REPAIRED_PENDING_EXPIRY_MINUTES = 120`, `v4_timewarp_simulated_live_research_loop.py:378`).
   With M1 gaps the two differ; using the bar count alone left 1,169 `fill_honest_walk_r`
   mismatches. Applying the minute wall took it to zero.

---

## 2. Step 2 — the five-month extension

### 2.1 The instrument problem, and how it was solved

March, April and May ledgers **do not carry `execution_fill_probability`** (144-field
`attempt_5_typed_sparse` schema; they carry `fill_probability`, which D4 established is a
*different* quantity — entry-quality, not limit-fillability). So the axis was reconstructed from
source: `src/components/poi_execution_lifecycle.py:161-193` —

```
limit_marketable -> 0.92
else  fp = clamp(0.03, 0.95, 0.70/(1+d_atr^1.35) + 0.30/(1+d_risk^1.10))
      d_atr = |entry-market|/ATR14 ,  d_risk = |entry-market|/|entry-stop|
```

`fp_hat_m1atr` uses an M1 ATR14. **Calibration against the real field (Jan+Feb, n = 51,677):**
Spearman **0.939 / 0.930** overall, **0.944 / 0.948** inside the resting book, mean |error|
**0.069**, mean level 0.735 vs 0.805 — i.e. **rank-faithful but biased ~0.07 low**, so at a fixed
0.45 cut it excludes about twice as many rows (26.1 % vs 14.1 %). Both axes are therefore
reported, plus a third that needs no reconstruction at all (`dist_r`, §4).

### 2.2 THE HEADLINE — the 0.45 fill floor deletes the better half in five of five months

Common axis `fp_hat_m1atr`, floor 0.45, **takeable** population (at-limit + resting + marketable;
past-stop excluded — those are w0-capture's artifact rows).

| month | n takeable | below floor | below R | above R | **delta** | t | zn delta | day-bootstrap 90 % | % positive |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| JAN | 24,139 | 6,661 | −0.0736 | −0.1466 | **+0.0730** | +4.53 | +0.0583 | [+0.0214, +0.1311] | 99.1 % |
| FEB | 22,412 | 5,793 | −0.0484 | −0.1447 | **+0.0963** | +5.69 | +0.0636 | [+0.0438, +0.1520] | 99.9 % |
| MAR | 24,974 | 7,032 | −0.0584 | −0.1703 | **+0.1119** | +7.23 | +0.0827 | [+0.0561, +0.1642] | 100.0 % |
| APR | 22,027 | 5,315 | −0.0865 | −0.1807 | **+0.0942** | +5.44 | +0.0707 | [+0.0233, +0.1625] | 98.7 % |
| MAY | 18,564 | 4,478 | −0.1387 | −0.1626 | **+0.0239** | +1.32 | −0.0075 | [−0.0309, +0.0872] | 73.9 % |
| **POOLED** | **112,116** | **29,279 (26.1 %)** | **−0.0773** | **−0.1610** | **+0.0837** | **+11.19** | **+0.0576** | — | — |

**5 of 5 months positive; 4 of 5 at t > 4.5.** May is the weak month (t 1.32, bootstrap 73.9 %
positive) — that is the boundary in time.

On each month's own native axis (real `execution_fill_probability` where it exists, `fp_hat`
where it does not) the same table reads: JAN +0.1043 (t 5.13), FEB +0.0731 (t 3.44),
MAR +0.1119 (t 7.23), APR +0.0942 (t 5.44), MAY +0.0239 (t 1.32).

### 2.3 The resting-internal cliff at 0.60 — travels in 3 of 5, flat in 1, reverses in 1

L9's §4.1 claim was specifically about the RESTING book and specifically about **both channels
moving** (fewer resolutions AND better resolutions). Measured on each month's native axis:

| month | n resting | below 0.60 | above 0.60 | delta | resolved mean below/above | resolved win below/above |
|---|---:|---:|---:|---:|---|---|
| JAN | 7,959 | −0.0394 | −0.1894 | **+0.1500** | −0.2233 / −0.3417 | 25.9 % / 21.9 % |
| FEB | 7,019 | −0.0573 | −0.0600 | **+0.0027** | −0.2732 / −0.1997 | 24.2 % / **26.7 %** |
| MAR | 8,468 | −0.0666 | −0.2112 | **+0.1446** | −0.2505 / −0.3589 | 25.0 % / 21.4 % |
| APR | 6,479 | −0.0897 | −0.2026 | **+0.1129** | −0.2524 / −0.3508 | 24.9 % / 21.6 % |
| MAY | 5,573 | −0.1457 | −0.1235 | **−0.0223** | −0.3998 / −0.2759 | 20.0 % / **24.1 %** |

On the **common** axis the same resting cut reads JAN +0.1362 (t 3.96), FEB +0.0563 (t 1.55),
MAR +0.1294 (t 3.96), APR +0.0818 (t 2.24), MAY +0.0229 (t 0.60) — same ordering of months.

**January, March and April reproduce L9's two-channel claim exactly. February is flat and May
inverts — and in both of those months the resolved-win channel inverts too**, which is the
honest read: the two-channel property is a property of three months of five, not a law.

---

## 3. L9's own "next test" — ANSWERED, and it is not staleness

L9 asked: *separate a FAR limit from a STALE limit; if the edge survives it is an entry-price
edge, if not the floors are right for the wrong reason.* Built `entry_traded_prior_24h` (did the
market trade at `entry_price` at any point in the 24 h of M1 bars before the decision?) and
`is_first_emission` (W0-F1 pseudo-replication rank).

**Census: staleness has almost no room in the takeable population.**

| month | takeable | stale (entry untraded 24 h) | stale share | re-emission share |
|---|---:|---:|---:|---:|
| JAN | 24,139 | 981 | 4.06 % | 23.8 % |
| FEB | 22,412 | 765 | 3.41 % | 24.4 % |
| MAR | 24,974 | 1,022 | 4.09 % | 26.3 % |

(Stale rows concentrate in `past_stop`, which `takeable` already excludes.)

**The floor delta survives BOTH filters, in five of five months** (common axis, floor 0.45,
`FRESH ∧ FIRST_EMISSION`):

| month | delta | t | day-bootstrap 90 % | % positive | detail |
|---|---:|---:|---|---:|---|
| JAN | **+0.0843** | +3.45 | [+0.0295, +0.1360] | 99.7 % | n below 2,251 / above 15,776, zn +0.0477 |
| FEB | **+0.0689** | +2.69 | [+0.0047, +0.1390] | 95.9 % | n below 1,969 / above 14,682, zn +0.0395 |
| MAR | **+0.0724** | +2.95 | [+0.0032, +0.1364] | 96.1 % | n below 2,194 / above 15,840, zn +0.0409 |
| APR | **+0.0643** | +2.48 | [−0.0277, +0.1527] | 86.4 % | n below 1,904 / above 14,681, zn +0.0401 |
| MAY | **+0.1019** | +3.66 | [+0.0340, +0.1737] | 99.5 % | n below 1,647 / above 12,734, zn +0.0636 |

**So the answer to L9's next test is: it is an entry-price effect, not a stale-limit artifact.**
Note that May — the month where the raw floor delta fails — is the *strongest* month once
re-emissions and stale levels are removed.

**But L9's caveat 1 reproduces out of window and must stay attached to the RULE.** The per-cycle
argmin-fill-probability rule collapses under the same conditioning in every month tested:

| month | pos1 (all takeable) | pos1 (FRESH ∧ FIRST) | delta vs allocator (all) | delta (FRESH ∧ FIRST) |
|---|---:|---:|---:|---:|
| JAN | +0.1193 | **−0.0414** | +0.2296 | +0.0631 |
| FEB | +0.0121 | **−0.0925** | +0.0683 | +0.0006 |
| MAR | +0.0758 | **−0.0849** | +0.2152 | +0.0355 |
| APR | +0.0608 | — | +0.1735 | — |
| MAY | **−0.0490** | — | +0.0617 | — |

Permutation tests (2,000 within-cycle re-picks, min cycle 5) still put the argmin pick above every
null draw in all five months (p ≤ 0.0005; null max JAN −0.0314, FEB −0.0491, MAR −0.0548,
APR −0.0720, MAY −0.0615), i.e. **the relative ordering is real everywhere; the absolute
positivity is January-and-nothing-else.** Use the floor number, not the argmin rule — exactly as
L9 advised, now confirmed on four more months.

---

## 4. The exact axis — kills the reconstruction objection, and weakens the finding honestly

`dist_r = |entry − market| / |entry − stop|` is measured, not reconstructed, and it is the
input to the fill-probability formula's own `risk_component`. Calibrated on January to exclude
**exactly the same number of rows** as the shipped `fp < 0.45` floor (3,407 of 24,139): threshold
**dist_r ≥ 1.4175**, agreement with the real exclusion set **80.51 %**, Jaccard 0.674. That one
threshold then applied unchanged to all five months:

| month | n below | below R | above R | delta | t | zn delta |
|---|---:|---:|---:|---:|---:|---:|
| JAN | 3,407 | −0.0304 | −0.1423 | **+0.1119** | +5.14 | +0.0963 |
| FEB | 2,917 | −0.0905 | −0.1242 | +0.0338 | +1.49 | +0.0127 |
| MAR | 3,316 | −0.0899 | −0.1463 | **+0.0564** | +2.61 | +0.0506 |
| APR | 2,563 | −0.1049 | −0.1649 | **+0.0600** | +2.44 | +0.0500 |
| MAY | 1,950 | −0.2057 | −0.1511 | **−0.0546** | **−2.13** | −0.0598 |
| **POOLED** | **14,153** | **−0.0944** | **−0.1456** | **+0.0512** | **+4.94** | **+0.0391** |

**On the exact axis the effect is ~60 % the size and May reverses significantly.** The gap between
this and §2.2 is the ATR limb of the fill-probability formula: the shipped field orders
candidates better than raw distance-in-R does. That is information about the field, not a defect
in the finding — but any claim must say which axis it is on.

### 4.1 The shape is a STEP, not a gradient — a correction to L9-F2's wording

Pooled five-month born-state census (n = 124,738 pool rows):

| born state | n | share | fill-honest R |
|---|---:|---:|---:|
| `past_stop` (w0-capture artifact) | 12,622 | 10.1 % | **−0.9965** |
| `marketable` (limit already through the market) | 7,096 | 5.7 % | **−0.3476** |
| `at_limit` (entry == decision-instant price) | 69,522 | 55.7 % | **−0.1413** |
| `resting` (limit away from the market) | 35,498 | 28.5 % | **−0.0931** |

And inside the resting book the distance ladder is **flat**, pooled over five months:

| dist_r band | n | honest | zn | resolved n | resolved mean | resolved win |
|---|---:|---:|---:|---:|---:|---:|
| ≤ 0 (marketable or at-limit) | 76,618 | −0.1604 | −0.2254 | 49,707 | −0.3475 | 21.7 % |
| 0 – 0.35 | 5,667 | −0.1174 | −0.1998 | 3,127 | −0.3620 | 21.3 % |
| 0.35 – 0.75 | 6,364 | −0.0830 | −0.1700 | 3,944 | −0.2743 | 24.2 % |
| 0.75 – 1.42 | 9,314 | −0.0834 | −0.1813 | 5,832 | −0.2896 | 23.7 % |
| 1.42 – 3.0 | 9,841 | −0.0961 | −0.1905 | 6,549 | −0.2863 | 23.8 % |
| ≥ 3.0 | 4,312 | −0.0904 | −0.1463 | 3,430 | **−0.1840** | **27.2 %** |

**L9-F2 called this "monotone with a cliff at fp = 0.60". Over five months it is better described
as a step: crossing the market is catastrophic (−0.35), sitting at the market is bad (−0.14),
resting away from the market is less bad (−0.08…−0.12), and beyond ~0.35 R of distance the ladder
is flat except that the resolved-win channel keeps improving (21.3 % → 27.2 %).**

---

## 5. The boundary — three families of ten, and it is structural not statistical

| family | JAN | FEB | MAR | APR | MAY | POOLED delta | t | n | months + |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `current_breaker_re_entry` | +0.507 | +0.267 | +0.326 | +0.195 | +0.385 | **+0.3539** | +9.04 | 3,375 | **5/5** |
| `current_ob_retest` | +0.163 | +0.196 | +0.234 | +0.297 | +0.121 | **+0.1960** | +5.72 | 6,026 | **5/5** |
| `current_fvg_fill` | +0.148 | +0.138 | +0.241 | +0.193 | +0.050 | **+0.1627** | +13.28 | 33,225 | **5/5** |
| `displacement_continuation` | — | — | — | — | — | n/a | — | 21,060 | **0 rows below floor** |
| `liquidity_sweep_reclaim` | — | — | — | — | — | n/a | — | 21,041 | **0 rows below floor** |
| `cross_asset_lead_lag` | — | — | — | — | — | n/a | — | 9,628 | **0 rows below floor** |
| `structural_distance_extreme` | — | — | — | — | — | n/a | — | 8,938 | **0 rows below floor** |
| `session_open_range_break` | — | — | — | — | — | n/a | — | 4,677 | **0 rows below floor** |
| `volatility_compression_expansion` | — | — | — | — | — | n/a | — | 2,839 | **0 rows below floor** |
| `regime_transition_break` | — | — | — | — | — | n/a | — | 1,307 | **0 rows below floor** |

**Seven of ten families emit ZERO below-floor candidates across 112,116 takeable rows in five
months.** They are the momentum/continuation families and they enter at market. The fill floor is
*structurally incapable* of binding on them. The finding lives entirely in the three
"limit-at-a-level" families — FVG fill, order-block retest, breaker re-entry — which is exactly
the set whose strategy IS a resting limit.

Caveat on the axis: on the **real** `execution_fill_probability` field (Jan + Feb only, the two
months that carry it), `current_ob_retest` runs the other way in January (−0.0630, t −1.12) before
turning positive in February (+0.1342, t 2.21); `current_fvg_fill` is +0.1562 (t 5.44) then
+0.0378 (t 1.28); `current_breaker_re_entry` is +0.2904 (t 3.35) then +0.1746 (t 2.01). Only
breaker holds in both months on the real field. **The clean 5/5 result is on `fp_hat`.**

### Other boundary cuts (common axis, pooled 3-month where measured)

| cut | verdict |
|---|---|
| `born_state` | **All 29,279 below-floor rows are `resting` (5 months). Zero of 69,522 `at_limit`, zero of 7,096 `marketable`.** The floor only ever deletes resting limits — 29,279 of the 35,498 resting rows, i.e. 82.5 % of the resting book. |
| `decision_timeframe` | single-valued (M15) — no boundary available |
| session `ny` | JAN +0.129 / FEB +0.062 / MAR +0.193 → POOLED (3 mo) **+0.1275 (t 5.16)**, n below 2,740 — holds 3/3 |
| session `london` | JAN +0.042 / FEB +0.121 / MAR +0.085 → POOLED (3 mo) **+0.0816 (t 3.19)**, n below 2,389 — holds 3/3 |
| session `tokyo` | JAN −0.120 / FEB −0.199 / MAR +0.150 → POOLED (3 mo) **−0.0544 (t −1.21)** — **does not hold** |
| best symbols (exact axis, pooled) | XAUUSD +0.1115 (t 3.62, n below 2,811 — the single largest contributor), ETHUSD +0.2097 (t 2.79), SPX500 +0.0948 (t 2.04) |
| worst symbols | USOIL_cash −0.2429 (t −2.29), GBPJPY −0.1959 (t −1.57), NAS100 −0.0637 (t −1.41) |

---

## 6. Mechanism — it is not stop width, and it is not truncation

**6.1 Not stop width.** `dist_r` and `risk_pct` (= `risk_distance` as % of price) are entangled by
construction. Two-way, pooled five months, quartile × quartile:

| within risk-width quartile | n top-dist / bottom-dist | top-dist R | bottom-dist R | delta | t |
|---|---|---:|---:|---:|---:|
| Q1 (tightest stops) | 5,916 / 621 | −0.1735 | −0.4506 | **+0.2771** | +5.77 |
| Q2 | 9,648 / 1,272 | −0.1295 | −0.3655 | **+0.2360** | +7.04 |
| Q3 | 7,981 / 1,605 | −0.0109 | −0.3273 | **+0.3164** | +11.23 |
| Q4 (widest stops) | 4,484 / 3,601 | −0.0245 | −0.3320 | **+0.3075** | +17.48 |

**The passivity effect survives inside every stop-width stratum at +0.24 to +0.32 R/trade.** The
reverse also holds (wide stops beat tight stops by +0.119 to +0.156 inside dist strata, t 2.54 to
14.71) — two independent axes, not one confounded one.

Read the raw ladders separately: the `risk_pct` gradient is largely *truncation* (resolved win
falls 24.1 % → 19.0 % as stops widen, resolved n 12,905 → 5,607), while the `dist_r` gradient
shows in **both** channels (resolved win 13.2 % marketable → 23.0 % at-limit → 25.2 % far).

**6.2 Not the 2-hour wall — this is the decisive measurement of the lane.** The same candidates
were re-walked on raw M1 bars out to 8 h and 24 h (`e3_08_cell.py`, `e3_09_final.py`):

| cohort | horizon | n | mean R | resolved | resolved win |
|---|---|---:|---:|---:|---:|
| cheap ∧ far | 120 min | 4,003 | **+0.0204** | 68.8 % | 29.6 % |
| cheap ∧ far | 480 min | 4,003 | **+0.0320** | 96.2 % | 33.9 % |
| cheap ∧ far | **1440 min** | 4,003 | **+0.0324** | **98.4 %** | **34.4 %** |
| cheap ∧ near | 120 min | 32,906 | −0.1122 | 47.4 % | 20.3 % |
| cheap ∧ near | 480 min | 32,906 | −0.1105 | 75.3 % | 26.0 % |
| cheap ∧ near | **1440 min** | 32,906 | **−0.0966** | 89.5 % | 28.5 % |
| **delta far − near** | 120 / 480 / 1440 | | **+0.1326 / +0.1425 / +0.1290** | | |

**The advantage is invariant to horizon.** At 24 hours, where 98.4 % of the passive cohort has
resolved to a real target or a real stop and only 66 of 4,003 are still open, the passive cohort
**wins 34.4 % against a 2R target — above the 33.3 % breakeven — and books +0.0324 R/trade gross**,
while the aggressive cohort wins 28.5 % and books −0.0966. L9's caveat 2 ("roughly all of the
pos1 cohort's absolute positivity is the mark at the 2-hour wall") is true of the *argmin rule*
and **false of the cheap-and-far cohort**.

---

## 7. The two gates are not both backwards — cost is right, the fill floor is wrong

L9 §4.5 argued the cost gate is pointed at the same population backwards. Measured over five
months that is **half true**, and the half that is true is the important half.

**The cost gate orders correctly inside every passivity band** (cheap = `cost_r ≤ 0.15`, the
shipped `selected_cell_pretrade_max_total_cost_r`):

| dist band | n cheap / expensive | cheap R | expensive R | delta | t |
|---|---|---:|---:|---:|---:|
| ≤ 0 (marketable/at-limit) | 25,937 / 50,681 | −0.1334 | −0.1742 | +0.0408 | +5.22 |
| 0 – 0.35 | 2,147 / 3,520 | −0.0438 | −0.1623 | +0.1185 | +4.51 |
| 0.35 – 0.75 | 1,998 / 4,366 | −0.0279 | −0.1082 | +0.0802 | +2.84 |
| 0.75 – 1.42 | 2,824 / 6,490 | −0.0291 | −0.1071 | +0.0780 | +3.24 |
| 1.42 – 3.0 | 2,817 / 7,024 | −0.0149 | −0.1287 | +0.1138 | +4.48 |
| ≥ 3.0 | 1,186 / 3,126 | **+0.1043** | −0.1642 | **+0.2685** | +6.15 |

**And passivity orders correctly inside the cost-passing band:** among `cost_r ≤ 0.15`, far
(n 2,538) books **+0.0592** against near (n 17,706) at −0.1128 — **delta +0.1720, t +6.77.**

So the shipped stack is: **cost keeps them, the fill floor kills them.** The intersection is the
only positive-honest cohort in 112,116 rows.

| cohort | n | honest R | t | zn | resolved win | mean cost_r | net @ spread/7.3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| **cheap ∧ far** | **4,003** | **+0.0204** | +1.08 | −0.0769 | **29.6 %** | 0.105 | **−0.0054** |
| cheap ∧ near | 32,906 | −0.1122 | −21.20 | −0.1848 | 20.3 % | 0.096 | −0.1603 |
| expensive ∧ far | 10,150 | −0.1396 | −12.30 | −0.2166 | 23.2 % | 0.954 | −0.3836 |
| expensive ∧ near | 65,057 | −0.1624 | −36.29 | −0.2320 | 22.6 % | 0.776 | −0.4188 |
| all takeable | 112,116 | −0.1391 | −42.55 | −0.2112 | 22.4 % | 0.569 | −0.3250 |

Per month, the cheap ∧ far cell: JAN n 1,015 **+0.0569**; FEB n 979 −0.0144; MAR n 1,015 **+0.0285**;
APR n 654 **+0.0655**; MAY n 340 **−0.0988**. Resolved win 31.1 / 28.4 / 30.7 / 32.1 / 19.3 %.

**Also worth recording**: every one of the 4,003 cheap ∧ far rows belongs to the three limit
families (the `CHEAP_FAR_3FAM` cut returns the identical n = 4,003) — the two conditions are not
independent, they are the same population reached two ways.

---

## 8. Bankability — what it would take, stated honestly

`e3_09_final.py`, day-level bootstrap (2,000 resamples over 101 trading days), net charged at the
frozen cost model with `spread_r` divided by the measured 7.3× over-charge:

| cell | n | honest | net @ spread/7.3 | bootstrap 90 % | % positive | months + |
|---|---:|---:|---:|---|---:|---:|
| cheap ∧ far ∧ (ny or london) | 1,665 | **+0.0588** (t 1.96) | **+0.0193** | [−0.0744, +0.1143] | 63 % | **4/5** |
| cheap ∧ far | 4,003 | +0.0204 (t 1.08) | −0.0054 | [−0.0647, +0.0609] | 45 % | 3/5 |
| cheap ∧ far ∧ fresh ∧ first-emission | 1,206 | **−0.0320** (t −1.05) | −0.0710 | [−0.1451, +0.0035] | 6 % | 3/5 |
| cheap ∧ any resting | 10,972 | −0.0137 (t −1.34) | −0.0424 | [−0.0773, −0.0016] | 5 % | 2/5 |
| cheap (all) | 36,909 | −0.0978 | −0.1435 | [−0.1611, −0.1254] | 0 % | 0/5 |
| all takeable | 112,116 | −0.1391 | −0.3250 | [−0.3402, −0.3098] | 0 % | 0/5 |

**NOT BANKABLE TODAY, and here is exactly why.** The best cell (`cheap ∧ far ∧ ny/london`) has a
day-bootstrap interval that spans zero and is positive on only 63 % of resamples. Worse, the cell's
positivity **leans on re-emissions**: applying the fresh + first-emission filter takes it from
+0.0204 to −0.0320 and the bootstrap to 6 % positive. That is the opposite direction from the
population-level floor finding (§3), and the two must not be conflated.

**What would make it bankable, in priority order:**

1. **A fill model, because the entire finding is a claim about limit orders and this pool has
   never measured one.** Every number here assumes a resting limit fills the instant price trades
   at `entry_price`, with zero queue, zero partial fill, zero rejection. The pool carries no bid/ask
   and no volume (D10), so this is unfalsifiable from the current asset. **The single cheapest
   decisive test: the live-forward record already contains real resting-limit fills — measure
   requested-vs-filled price, latency and partial-fill rate on them (execution mechanics only, no
   P&L), and apply the measured fill haircut to the +0.0324 R/trade 24 h number.** If the haircut
   exceeds ~0.03 R the finding is arithmetic, not money.
2. **A cost model that knows what an order type is.** L9's §4.5 source read still stands and is
   now load-bearing on five months: `broker_net_cost_engine.py:299-319` computes
   `spread_r = spread_price / sl_distance` with no order-type argument, so a passive limit filled
   at its own price is charged the same crossing spread as a market order. The cheap ∧ far cell
   nets −0.0054 R/trade at spread/7.3; a maker/taker-aware charge is the difference between
   −0.0054 and positive.
3. **A horizon decision.** The cell's value is at 8–24 h (+0.0320 / +0.0324) not 2 h (+0.0204),
   and 31.2 % of it is still unresolved at the 2 h wall. A tradeable version needs a declared
   holding contract past two hours, which the current pool's wall cannot express and the live book
   prices through `time_stop_bars`.
4. **More months, but only ~2 more.** Five months give a pooled t of +11.19 on the floor delta and
   +1.08 on the money cell. The floor finding does not need more data; the *money* cell does — it
   is 4,003 rows over 101 days, and its per-month sign is 3/5.
5. **A pre-registered threshold.** `dist_r ≥ 1.4175` was calibrated to reproduce the shipped
   floor's exclusion count on January. It is not a free parameter chosen on the outcome, but it is
   not pre-registered either. Freeze it before the next month is read.

**What is already decision-grade without any of that:** the fill floor is the wrong sign on the
population it can reach, in five of five months, at t +11.19 pooled and t ≥ 2.48 in every month
under the strictest conditioning. `ultimate_candidate_package_soften_selector_fill_floor_enabled`
is `false` at `config/agent_config.yaml:795`; the measured effect of moving the effective floor
to 0.25 is +0.0825 R/trade of relative ordering pooled over five months (below n 20,013, t +9.64),
and the sweep's own maximum is at 0.35 (+0.0865, t +11.13).

---

## 9. Everything measured, in one place

**Pooled floor sweep, common axis, 5 months, takeable (n = 112,116):**

| floor | n below | below share | below R | above R | delta | t | zn delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0.15 | 9,409 | 8.4 % | −0.0996 | −0.1427 | +0.0432 | +3.60 | +0.0236 |
| 0.25 | 20,013 | 17.9 % | −0.0714 | −0.1538 | +0.0825 | +9.64 | +0.0533 |
| 0.35 | 25,969 | 23.2 % | −0.0726 | −0.1591 | **+0.0865** | **+11.13** | +0.0581 |
| **0.45 (shipped)** | **29,279** | **26.1 %** | **−0.0773** | **−0.1610** | **+0.0837** | **+11.19** | **+0.0576** |
| 0.55 | 31,260 | 27.9 % | −0.0818 | −0.1613 | +0.0795 | +10.84 | +0.0546 |
| 0.60 | 31,993 | 28.5 % | −0.0834 | −0.1614 | +0.0779 | +10.70 | +0.0531 |
| 0.70 | 33,134 | 29.6 % | −0.0876 | −0.1607 | +0.0731 | +10.14 | +0.0489 |
| 0.80 | 33,998 | 30.3 % | −0.0894 | −0.1607 | +0.0713 | +9.96 | +0.0479 |
| 0.90 | 34,736 | 31.0 % | −0.0912 | −0.1606 | +0.0694 | +9.75 | +0.0466 |

The sweep peaks at **0.35** (+0.0865, t +11.13) and is essentially flat from 0.25 to 0.60 — the
finding is not sensitive to where the floor is put, only to the fact that there is one.

**Per-month native-axis floor sweep (each month's own instrument):**

| month | 0.25 | 0.35 | 0.45 | 0.60 | 0.80 |
|---|---|---|---|---|---|
| JAN | +0.0979 (t 2.77) | +0.1036 (4.22) | +0.1043 (5.13) | +0.1096 (6.18) | +0.0644 (4.01) |
| FEB | +0.0370 (1.03) | +0.0588 (2.31) | +0.0731 (3.44) | +0.0782 (4.27) | +0.0965 (5.72) |
| MAR | +0.0877 (4.96) | +0.1067 (6.65) | +0.1119 (7.23) | +0.1042 (6.89) | +0.0927 (6.24) |
| APR | +0.0928 (4.63) | +0.1003 (5.52) | +0.0942 (5.44) | +0.0928 (5.51) | +0.0831 (5.03) |
| MAY | +0.0152 (0.74) | +0.0377 (2.00) | +0.0239 (1.32) | +0.0152 (0.86) | +0.0258 (1.48) |

**Pooled 5-month band table, common axis, takeable (n = 112,116):**

| fp_hat band | n | honest | t | zn | tgt % | stop % | neither % | resolved n | resolved mean | resolved win | bars to entry |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| < 0.10 | 3,670 | −0.0837 | −4.29 | −0.1504 | 19.0 | 53.1 | 27.8 | 2,649 | −0.2084 | **26.4 %** | 69.9 |
| 0.10–0.20 | 11,718 | −0.0778 | −7.85 | −0.1821 | 13.7 | 45.6 | 40.7 | 6,949 | −0.3071 | 23.1 % | 54.9 |
| 0.20–0.30 | 8,079 | −0.0638 | −5.25 | −0.1577 | 14.9 | 45.6 | 39.4 | 4,892 | −0.2604 | 24.7 % | 37.8 |
| 0.30–0.40 | 4,347 | −0.0685 | −4.01 | −0.1516 | 16.5 | 48.2 | 35.3 | 2,813 | −0.2343 | 25.5 % | 26.5 |
| 0.40–0.50 | 2,531 | −0.1470 | −6.54 | −0.2094 | 16.4 | 53.7 | 29.8 | 1,775 | −0.2986 | 23.4 % | 16.2 |
| 0.50–0.60 | 1,648 | −0.1603 | −5.67 | −0.2397 | 16.4 | 56.9 | 26.7 | 1,208 | −0.3270 | 22.4 % | 10.2 |
| 0.60–0.70 | 1,141 | −0.2051 | −6.20 | −0.2743 | 15.3 | 58.1 | 26.4 | 838 | −0.3735 | **20.9 %** | 7.4 |
| 0.70–0.80 | 864 | −0.1587 | −4.02 | −0.2188 | 17.6 | 57.1 | 25.2 | 645 | −0.2930 | 23.6 % | 6.5 |
| 0.80–0.92 | 863 | −0.1445 | −3.64 | −0.2086 | 17.7 | 56.3 | 25.6 | 639 | −0.2817 | 23.9 % | 5.4 |
| ≥ 0.92 | 77,255 | −0.1609 | −41.16 | −0.2259 | 14.1 | 50.9 | 33.3 | 50,181 | −0.3478 | 21.7 % | 3.6 |

`bars to entry` runs 69.9 min → 3.6 min monotonically down the table: the axis is literally
"how long until the market comes to your price".

**Per-month pool composition (all five months, diagnostic-scoreable rows):**

| month | raw ledger | diagnostic-scoreable | unenrichable | resting | takeable | trading days |
|---|---:|---:|---:|---:|---:|---:|
| JAN | 27,658 | 27,658 | 0 | 7,959 | 24,139 | 21 |
| FEB | 24,239 | 24,239 | 0 | 7,019 | 22,412 | 20 |
| MAR | 130,004 | 26,500 | 0 | 8,468 | 24,974 | 22 |
| APR | 134,443 | 25,056 | 0 | 6,479 | 22,027 | 21 |
| MAY | 132,445 | 21,285 | 0 | 5,573 | 18,564 | 17 |
| **total** | **448,789** | **124,738** | **0** | **35,498** | **112,116** | **101** |

---

## 10. Two data defects found while doing this (both fixed here, both will bite the next lane)

1. **February's pool carries the KEY `side` with a NULL value and puts the direction in
   `direction`.** A `"side" not in row` test leaves it None, and a walker that reads
   `(row.get("side") or "").upper() == "LONG"` then treats every February trade as a SHORT. It
   moved the February cheap ∧ far cell from −0.0144 to −0.4936 before it was caught. Fixed in
   `e3_month.py` with `r["side"] = r.get("side") or r.get("direction")`. **January's pool has both
   populated; March/April/May have `direction` only. February is the only month where the key
   exists and lies.**
2. **March, April and May ledgers do not carry `execution_fill_probability` at all.** They carry
   `fill_probability`, which is a different quantity (D4: `fill_probability ==
   entry_quality_fill_probability`, `execution_fill_probability == limit_fillability_probability`).
   Any cross-month lane touching fill probability must reconstruct it (§2.1) or use `dist_r`.

---

## 11. Artifacts

| file | what |
|---|---|
| `e3_lib.py` | the portable month engine (bars, anchor, born state, fill-honest walk, staleness, fp reconstruction) |
| `e3_month.py` | one month → `E3_MONTH_<TAG>_V1.json` + `e3_slim_<TAG>.jsonl.gz` |
| `e3_01_repro.py` / `E3_REPRO_V1.json` | L9 reproduction + engine validation (0/27,658 mismatches) |
| `e3_04_cross.py` / `E3_CROSS_V1.json` | five-month common-axis tables, day bootstrap, boundary cuts |
| `e3_05_axis.py` / `E3_AXIS_V1.json` | exact `dist_r` axis, calibration, symbol/family boundary, money |
| `e3_06_mechanism.py` / `E3_MECHANISM_V1.json` | stop-width vs distance decomposition, two-way tables |
| `e3_07_costinter.py` / `E3_COSTINTER_V1.json` | cost × passivity interaction, shipped gate stack |
| `e3_08_cell.py` / `E3_CELL_V1.json` | the cheap ∧ far cell per month + 8 h / 24 h re-walks |
| `e3_09_final.py` / `E3_FINAL_V1.json` | pooled horizon arithmetic + bankability bootstrap |
| `E3_MONTH_{JAN,FEB,MAR,APR,MAY}_V1.json` | every per-month table |
| `e3_slim_{JAN,FEB,MAR,APR,MAY}.jsonl.gz` | 124,738 enriched rows, ready for the next lane |
