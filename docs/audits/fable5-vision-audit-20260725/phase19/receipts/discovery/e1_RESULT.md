# Lane e1 — EXTENSION of l10-broker-truth X5/X6

**Posture: extension, not refutation.** The l10 finding reproduces exactly. This receipt establishes
*why* it happens (a mechanism with file:line), *how far it reaches* (five months, an independent
instrument, a nine-symbol boundary), and *what it is and is not worth* (a decidability repair, not a
profit repair — and a correction to the l10 headline number that a later lane must not miss).

All numbers below are measured. Scripts under `e1_scripts/`, JSON artifacts named inline.

---

## 0. Reproduction — EXACT

Re-ran `l10_scripts/l10x_06_recost.py`'s instrument on `w0_WORKING_SET.jsonl.gz` and independently
recomputed the parts that need no tick data.

| quantity | l10 published | e1 measured | match |
|---|---:|---:|---|
| frozen total cost mean | 0.663161 | 0.663161 | exact |
| real total cost mean | 0.189297 | 0.189297 | exact |
| ratio frozen/real total | 3.503 | 3.503 | exact |
| ratio frozen/real spread | 4.520 | 4.520 | exact |
| gate pass FROZEN | 7,210 (26.068 %) | 7,210 | exact |
| gate pass REAL | 12,629 (45.661 %) | 12,629 | exact |
| SPX500 min frozen `spread_r` | 0.24479, 0/1,943 pass | 0.24479, 0/1,943 | exact |
| NAS100 min frozen `spread_r` | 0.16326, 0/1,622 pass | 0.16326, 0/1,622 | exact |

`n_pass_frozen` reproduces for **24 of 24 symbols**. Receipt `E1_JAN_REPRO_INDEP_V1.json`,
script `e1_scripts/e1_00_repro_jan.py`.

---

## 1. THE MECHANISM — a refusal ceiling charged as an expected cost

l10 said the cost model is "scrambled per symbol". It is not scrambled — it is a **four-tier
fallback chain**, and the symbols land on different tiers. Measured by computing the implied frozen
spread in price units (`spread_r × risk_distance`) per row: for 17 of 24 symbols it is **exactly
constant** (coefficient of variation < 1e-9), and the constants are recognisable.

| tier | source | file:line | January symbols |
|---|---|---|---|
| 1 | cached pre-decision tick row | `v4_timewarp_simulated_live_research_loop.py:58760-58795` | XAUUSD, XAGUSD, BTCUSD, EURUSD, USDJPY |
| 2 | `TICK_SPREAD_FLOOR_R` — a **floor in R**, used as the point estimate | `src/components/ultimate_book/admission.py:73-84`, applied at `v4_timewarp:58796-58805` | USOIL_cash 0.0270, UKOIL_cash 0.0258, BTCUSD 0.0001 |
| 3 | broker profile `market.spread × market.point` | `v4_timewarp:58807-58821`, `config/profiles/ftmo.yaml` | AUDJPY 0.011, GBPJPY 0.018, FX majors 5e-5…1e-4 |
| 4 | **`max_spread_cents / 100` — a REFUSAL CEILING** | `v4_timewarp:58822-58832`, `config/agent_config.yaml` | **NAS100, SPX500, JP225, UK100, GER40, US30_cash, ETHUSD, EURJPY, CHFJPY** |

**Proof for tier 4**: the implied frozen spread is exactly `max_spread_cents/100` for all nine
symbols, to 1e-6, in all five months.

| symbol | `agent_config.yaml` line | `max_spread_cents` | charged price units | inline comment on the same line |
|---|---:|---:|---:|---|
| NAS100 | 4430 | 5000 | 50.0 | `50 pts: (ask-bid)*100 convention` |
| JP225 | 5010 | 5000 | 50.0 | — |
| SPX500 | 5036 | 1000 | 10.0 | — |
| ETHUSD | 4927 | 1000 | 10.0 | — |
| US30_cash | 4706 | 800 | 8.0 | **`8 pts … Typical ~2 pts → 200`** |
| UK100 | 4472 | 500 | 5.0 | **`5 pts … typical 1 pt, p99 4 pts`** |
| GER40 | 4514 | 500 | 5.0 | — |
| EURJPY | 4982 | 5.0 | 0.05 | — |
| CHFJPY | 4901 | 5.0 | 0.05 | — |

**The config records the right answer on the same line as the wrong one.** US30_cash's own comment
says the typical spread is 200 (2.0 px) beside the 800 (8.0 px) the engine charges — 4×. UK100's
says "typical 1 pt, p99 4 pts" beside the 5 pts charged — 5×, and above its own p99.

**Both safety rails are wired into the expectation, and each is wrong in its own direction.** The
refusal ceiling (tier 4) becomes the estimate and over-charges. The never-cheaper-than floor
(tier 2) becomes the estimate and under-charges the January oils to 0.28–0.38× of era truth. A
ceiling and a floor are both being read as point estimates.

---

## 2. It holds in ALL FIVE MONTHS — two independent instruments

Two spread instruments, deliberately different:

* **INSTRUMENT A (l10's)** — flat FTMO tick-archive median bps per symbol, measured 2026-06-18…07-24,
  applied to every month.
* **INSTRUMENT B (new)** — `src/costs/spread_model.spread_price(symbol, 'FTMO', <row timestamp>, band)`:
  tick anchor × **measured era ratio for that quarter** × intraweek multiplier. Coverage is
  `MEASURED` for 7 of the 9 ceiling symbols, `MODELLED` for ETHUSD and BTCUSD.

### 2.1 Diagnostic pool (the population l10 used)

Instrument A — `E1_MONTHS_V1.json`:

| month | n | frozen cost | real cost | ratio | pass FROZEN | pass REAL | uplift | index-cohort n | idx pass F | idx pass R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| JAN | 27,658 | 0.6632 | 0.1893 | **3.50×** | 7,210 (26.07 %) | 12,629 (45.66 %) | +75.2 % | 9,905 | 550 | 5,863 |
| FEB | 24,239 | 0.4895 | 0.1562 | **3.13×** | 6,579 (27.14 %) | 14,197 (58.57 %) | +115.8 % | 8,055 | 782 | 5,978 |
| MAR | 26,500 | 0.4046 | 0.1247 | **3.24×** | 9,240 (34.87 %) | 18,152 (68.50 %) | +96.5 % | 9,680 | 1,772 | 8,519 |
| APR | 25,056 | 0.6233 | 0.1810 | **3.44×** | 5,745 (22.93 %) | 12,378 (49.40 %) | +115.5 % | 7,930 | 1,072 | 5,774 |
| MAY | 21,285 | 0.6644 | 0.2009 | **3.31×** | 4,540 (21.33 %) | 9,720 (45.67 %) | +114.1 % | 7,094 | 713 | 5,139 |

Instrument B — `E1_ERATRUE_RECOST_V1.json`:

| month | frozen | era-true mid | ratio | era-true **high band** | ratio at high band | pass FROZEN | pass era-true | pass era-true HIGH |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| JAN | 0.6632 | 0.2059 | **3.22×** | 0.2312 | 2.87× | 7,210 | 12,700 | 11,529 |
| FEB | 0.4895 | 0.1690 | **2.90×** | 0.1910 | 2.56× | 6,579 | 14,289 | 13,064 |
| MAR | 0.4046 | 0.1365 | **2.96×** | 0.1486 | 2.72× | 9,240 | 18,472 | 17,437 |
| APR | 0.6233 | 0.2050 | **3.04×** | 0.2177 | 2.86× | 5,745 | 12,124 | 11,440 |
| MAY | 0.6644 | 0.2270 | **2.93×** | 0.2413 | 2.75× | 4,540 | 9,598 | 8,953 |

The two instruments agree to within 0.2–0.5× and the finding survives even at the model's
**conservative high band** in every month.

### 2.2 Full ledger — 82 % of it carries no economics, so this pass is free

`E1_FULLLEDGER_ERATRUE_V1.json`. `opportunity_net_proxy_r` is null on every row outside the
diagnostic pool (verified: 125,767 of 153,425 January rows), so this measurement reads **zero**
economics in any month.

| month | ledger rows | frozen | era-true | ratio | pass FROZEN | pass era-true | **restored rows** | restored % | ceiling-cohort n | idx pass F | idx pass era-true |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| JAN | 153,425 | 1.1307 | 0.1818 | **6.22×** | 25,132 | 64,602 | **+39,470** | +157.1 % | 100,584 (65.6 %) | 3,590 | 43,304 |
| FEB | 129,165 | 0.8086 | 0.1417 | **5.71×** | 19,572 | 74,658 | **+55,086** | +281.4 % | 80,351 (62.2 %) | 3,445 | 46,425 |
| MAR | 130,004 | 0.6475 | 0.1252 | **5.17×** | 31,117 | 87,196 | **+56,079** | +180.2 % | 80,270 (61.7 %) | 7,408 | 56,012 |
| APR | 134,443 | 0.9867 | 0.1826 | **5.40×** | 17,238 | 59,619 | **+42,381** | +245.9 % | 82,177 (61.1 %) | 4,388 | 36,125 |
| MAY | 132,445 | 0.9062 | 0.1950 | **4.65×** | 17,862 | 56,481 | **+38,619** | +216.2 % | 81,527 (61.6 %) | 3,114 | 39,486 |

**The ceiling cohort is 61–66 % of every candidate the engine ever considered**, and the frozen
model refuses 91–96 % of it.

---

## 3. THE BOUNDARY

### 3.1 By symbol — exactly nine, and stable to ±2 %

Era-true **total**-cost ratio (frozen ÷ era-true), median per month, `E1_ERATRUE_RECOST_V1.json`:

| symbol | tier | JAN | FEB | MAR | APR | MAY | l10 tick spread-only ratio |
|---|---|---:|---:|---:|---:|---:|---:|
| NAS100 | 4 ceiling | **28.63** | 28.46 | 28.94 | 29.31 | 28.66 | 33.90 |
| SPX500 | 4 ceiling | **16.72** | 16.64 | 16.86 | 15.05 | 15.09 | 18.16 |
| JP225 | 4 ceiling | **12.42** | 12.61 | 12.94 | 5.23 | 5.16 | 6.54 |
| ETHUSD | 4 ceiling | 6.03 | 6.28 | 5.72 | 6.46 | 6.40 | 9.31 |
| UK100 | 4 ceiling | 5.63 | 5.78 | 5.88 | 5.82 | 5.96 | 6.01 |
| US30_cash | 4 ceiling | 4.24 | 4.31 | 4.75 | 4.42 | 4.42 | 4.06 |
| GER40 | 4 ceiling | 4.15 | 2.21 | 4.55 | 3.69 | 3.04 | 4.01 |
| EURJPY | 4 ceiling | 2.53 | 2.87 | 2.58 | 2.99 | 3.11 | 4.16 |
| CHFJPY | 4 ceiling | 1.96 | 2.09 | 2.07 | 2.36 | 2.30 | 2.69 |
| — everything else — | 1/2/3 | 0.28–1.71 | 0.75–3.20 | 1.01–1.77 | 1.06–3.13 | 0.55–3.10 | 0.02–3.29 |

NAS100 sits at 28.5–29.3× in **every** month — a ±1.5 % band across five independent windows,
because the numerator is a config constant and the denominator is a measured era level.

**JP225 has a real era break**: 12.4–12.9× in Jan–Mar, 5.2× in Apr–May. The spread model's own era
ratio for JP225 is 0.414 at 2026Q1 and 1.000 at 2026Q2 (`E1_ERA_SPREAD_V1.json`). The defect is
constant; the *market* moved.

**Structural deletion, per month** (`E1_MONTHS_V1.json` → `per_symbol_POOL`, n / min frozen
`spread_r` / pass frozen / pass real):

| symbol | JAN | FEB | MAR | APR | MAY |
|---|---|---|---|---|---|
| SPX500 | 1943 / 0.245 / **0** / 973 | 1241 / 0.130 / **0** / 791 | 1592 / 0.039 / 2 / 1354 | 1210 / 0.090 / 2 / 704 | 1053 / 0.193 / **0** / 596 |
| NAS100 | 1622 / 0.163 / **0** / 1277 | 1021 / 0.126 / **0** / 933 | 1500 / 0.052 / 4 / 1436 | 1245 / 0.116 / **0** / 971 | 1021 / 0.114 / **0** / 882 |
| ETHUSD | 934 / 0.058 / 7 / 326 | 743 / 0.089 / 2 / 317 | 987 / 0.068 / 3 / 405 | 918 / 0.139 / **0** / 196 | 892 / 0.154 / **0** / 130 |
| UK100 | 2016 / 0.079 / 3 / 760 | 1446 / 0.059 / 11 / 829 | 1885 / 0.016 / 90 / 1405 | 1328 / 0.032 / 34 / 775 | 1607 / 0.042 / 39 / 1085 |
| JP225 | 1348 / 0.068 / 12 / 698 | 1243 / 0.043 / 71 / 778 | 1483 / 0.015 / 258 / 1201 | 1510 / 0.040 / 118 / 992 | 1260 / 0.041 / 33 / 715 |
| EURJPY | 1080 / 0.025 / 28 / 309 | 575 / 0.041 / 17 / 335 | 628 / 0.056 / 11 / 298 | 577 / 0.045 / 7 / 187 | 862 / 0.039 / 9 / 126 |

**SPX500 and NAS100 are deleted in every month.** Over the five pooled months that is
**0 + 0 + 2 + 2 + 0 = 4 admitted candidates out of 14,448.**

### 3.2 By family and session (January, `E1_BOUNDARY_V1.json`)

| family | n | frozen/real ratio | pass F | pass R | gross | median risk-distance % of price |
|---|---:|---:|---:|---:|---:|---:|
| current_fvg_fill | 7,146 | **6.49** | 1,605 | 3,311 | −0.1416 | 0.0982 |
| current_breaker_re_entry | 4,263 | 3.34 | 359 | 1,140 | −0.8254 | 0.0539 |
| volatility_compression_expansion | 605 | 3.38 | 409 | 565 | −0.0868 | 0.3392 |
| regime_transition_break | 297 | 2.83 | 226 | 288 | −0.0067 | 0.4454 |
| cross_asset_lead_lag | 2,083 | 2.71 | 368 | 526 | −0.1307 | 0.0594 |
| liquidity_sweep_reclaim | 4,475 | 2.63 | 1,013 | 1,700 | −0.0415 | 0.0770 |
| displacement_continuation | 4,469 | 2.61 | 2,020 | 3,320 | −0.0885 | 0.1642 |
| structural_distance_extreme | 1,993 | 2.50 | 137 | 108 | −0.1820 | 0.0300 |
| current_ob_retest | 1,340 | 2.33 | 505 | 865 | −0.1046 | 0.1137 |
| session_open_range_break | 987 | 2.21 | 568 | 806 | −0.0747 | 0.1681 |

`current_fvg_fill` — the largest family — carries the worst overcharge (6.49×) because it is
index-heavy: **66.9 % of its 7,146 January rows are ceiling-cohort symbols**, against 30.1–46.5 %
for every other family (measured; `liquidity_sweep_reclaim` 36.0 %, `displacement_continuation`
37.7 %, `current_breaker_re_entry` 46.5 %, `cross_asset_lead_lag` 30.1 %,
`volatility_compression_expansion` 43.1 %, `regime_transition_break` 38.4 %,
`structural_distance_extreme` 33.7 %, `current_ob_retest` 32.4 %, `session_open_range_break`
33.5 %). `structural_distance_extreme` is the one family the corrected gate admits **fewer** of
(137 → 108).

| session | n | ratio | pass F | pass R | gross |
|---|---:|---:|---:|---:|---:|
| off_configured_session | 16,562 (59.9 %) | 4.21 | 3,383 | 7,007 | −0.2582 |
| ny | 4,921 | 3.38 | 1,888 | 2,904 | −0.1689 |
| london | 4,867 | **1.60** | 1,666 | 2,103 | **−0.1317** |
| tokyo | 1,308 | 2.06 | 273 | 615 | −0.2040 |

London has both the smallest distortion and the best gross. The distortion is worst exactly where
the pool is worst (off-session).

---

## 4. THE EXTENSION THAT MATTERS — the gate selects on its own error

`E1_SELECTION_ON_ERROR_V1.json`. Define `error = frozen_cost − real_cost` per row.

| month | error on ALL rows | error on rows the gate **ADMITS** | error on rows the gate **REFUSES** | selection-on-error |
|---|---:|---:|---:|---:|
| JAN | **+0.4739** | **−0.0315** | +0.6521 | **−0.5054** |
| FEB | +0.3332 | −0.0186 | +0.4643 | −0.3519 |
| MAR | +0.2798 | +0.0213 | +0.4182 | −0.2585 |
| APR | +0.4423 | +0.0231 | +0.5670 | −0.4192 |
| MAY | +0.4635 | −0.0293 | +0.5971 | −0.4928 |

(Independently at era truth: error on ALL +0.2681…+0.4573, error on ADMITTED −0.0154…+0.0304.)

**This corrects the l10 headline.** l10 reported `r_per_trade: 0.473864` — the pool-wide overcharge.
But the gate keeps rows precisely where its own estimate is low, and its estimate is low exactly
where its error is smallest or negative. The result is that **the entire overcharge lives in the
rows the gate refuses.** On the book the system actually trades, the frozen model is accurate to
±0.03 R/trade, and in January and May it is *under*-charging.

So `0.473864` is not recoverable on the current book. It is the size of the **fictitious charge on
the refused universe** — a measure of how much the gate deletes, not of how much money is on the
table.

Additional measured detail: **28.6–33.1 % of the refused rows are net-positive at real cost**, at a
mean of +0.97 to +1.16 R each — while the refused cohort as a whole is net −0.35 to −0.49 R. A large
positive tail exists inside the refusals with no ex-ante selector for it.

---

## 5. THE SECOND EXTENSION — the cost gate is a disguised stop-width filter, and it is worth ≈ 0

Because frozen `spread_r = constant_price_units ÷ risk_distance` for 17 of 24 symbols, "cheap"
means "wide stop" by construction. Measured (`E1_STOPWIDTH_V1.json`), January pool:

| risk-distance decile | range (% of price) | gross R | fraction passing the frozen gate | median frozen `spread_r` |
|---:|---|---:|---:|---:|
| 1 (tightest) | 0.0047–0.0295 | −0.2753 | **0.0000** | 0.6277 |
| 2 | 0.0295–0.0417 | −0.3759 | 0.0148 | 0.2637 |
| 3 | 0.0417–0.0551 | −0.3762 | 0.0477 | 0.1844 |
| 4 | 0.0551–0.0700 | −0.2807 | 0.0889 | 0.2307 |
| 5 | 0.0700–0.0905 | −0.2115 | 0.2101 | 0.1903 |
| 6 | 0.0905–0.1195 | −0.2195 | 0.3179 | 0.1439 |
| 7 | 0.1195–0.1668 | −0.1353 | 0.3680 | 0.0958 |
| 8 | 0.1668–0.2497 | −0.1214 | 0.4324 | 0.0833 |
| 9 | 0.2497–0.4288 | −0.0941 | 0.4823 | 0.0574 |
| 10 (widest) | 0.4294–7.5826 | **−0.0851** | **0.6446** | 0.0315 |

Spearman(risk-distance rank, gross rank) is **+0.135 to +0.197 and positive in all five months**.

### 5.1 The control — 81 % of the gate's apparent value is the un-takeable artifact

W0-capture measured that 12.72 % of the January pool was born with its stop already breached and
books a mechanical −0.9948 R. Those rows have the tightest geometry, so they sit in exactly the
deciles the gate refuses. Removing them with the **clean no-look-ahead anchor**
(`mkt_r_prev_close`, which reproduces w0-capture's census exactly: 14,911 / 7,949 / 1,265 / **3,516**):

| population | n | pool gross | d1 gross | d10 gross | d10 − d1 | gate raw edge | gate edge **matched on stop width** |
|---|---:|---:|---:|---:|---:|---:|---:|
| ALL | 27,658 | −0.2175 | −0.2753 | −0.0851 | +0.1902 | **+0.1056** | +0.0403 |
| EX past-stop (clean anchor) | 24,125 | −0.1039 | −0.1627 | −0.0659 | +0.0967 | **+0.0202** | **+0.0039** |

(The ex-past-stop gross of −0.1039 reproduces w0-capture's −0.10392 exactly, validating the join.)

Portable control across all five months — drop `current_breaker_re_entry`, which is 98.61 % of the
January artifact (`E1_BOUNDARY_V1.json`):

| month | n ex-breaker | gate raw edge | gate edge matched on stop width | stop-width d10 − d1 |
|---|---:|---:|---:|---:|
| JAN | 23,395 | +0.0216 | +0.0045 | +0.0887 |
| FEB | 21,864 | +0.0373 | +0.0142 | +0.1369 |
| MAR | 24,365 | +0.0103 | **−0.0089** | +0.0574 |
| APR | 21,385 | +0.0370 | +0.0424 | +0.0396 |
| MAY | 17,914 | +0.0125 | **−0.0629** | +0.1431 |
| **mean** | | **+0.0237** | **−0.0021** | **+0.0931** |

**The gate that refuses 65–79 % of the pool (73.9 % JAN, 72.9 % FEB, 65.1 % MAR, 77.1 % APR,
78.7 % MAY) has a genuine selection value of −0.0021 R/trade averaged over five months, and its
sign flips 3 : 2.** Everything that looked like selection was (a) the un-takeable rows and
(b) stop width.

**The stop-width gradient itself survives**: +0.0396 to +0.1431 R/trade between the widest and
tightest decile, **positive in 5 of 5 months** after both controls. That is a real ordering the
system currently reaches only by accident, through a broken cost model, in the wrong units.

---

## 6. What the repair is worth — the honest answer

Restored universe = rows the frozen gate refuses that a real-cost gate admits, ex-breaker
(`E1_RESTORED_GRID_V1.json`):

| month | pool ex-breaker | restored rows | restored gross | restored **net at real cost** |
|---|---:|---:|---:|---:|
| JAN | 23,395 | 6,625 | −0.1007 | −0.1716 |
| FEB | 21,864 | 8,249 | −0.0304 | −0.1047 |
| MAR | 24,365 | 8,737 | −0.1109 | −0.1740 |
| APR | 21,385 | 6,898 | −0.1242 | −0.1974 |
| MAY | 17,914 | 6,320 | −0.0948 | −0.1682 |

Pre-declared grid (session × stop-width tercile × cost cohort, 4 × 3 × 3 plus `ANY` margins,
minimum 30 rows/month → 34 evaluable cells), scored on net-at-real-cost, requiring positivity in
5 of 5 months:

**No cell survives.** Best is `london | T3_wide | CEILING`: n = 910, pooled **+0.0660 R/trade**,
positive in **3 of 5** months (+0.0218, +0.1538, +0.2917, −0.0344, −0.0713). Second is
`london | T1_tight | CEILING`, 3/5, pooled −0.0247. Everything else is ≤ 2/5.

**So the l10 finding is a decidability repair, not a profit repair.** It restores 38,619–56,079
ledger rows per month (+157 % to +281 %) to judgeability — including 61–66 % of the universe that
was never judgeable at all — and none of what it restores is takeable today.

### 6.1 A correction to l10's per-symbol undercharge claim

l10 reported BTCUSD at "0.017×, 58× UNDER". That is a **spread-only** statement. On **total** cost
at era truth, BTCUSD is **1.71–3.20× OVER**-charged in every month, because the frozen model's
commission term for BTC is large. The genuine undercharge is narrower than l10 stated: only the
oils, and only in the earlier months — `USOIL_cash` 0.38× and `UKOIL_cash` 0.28× in January, rising
to 1.07–1.67× by April/May as their era ratio moves 0.52 → 1.03. A later lane must not carry
"58× under on Bitcoin" forward as a total-cost fact.

---

## 7. Economics spend register — April and May

Both windows were economics-unread before this lane. Registered honestly:

* **Spent**: `opportunity_net_proxy_r` on the **diagnostic pool only** — April 25,056 rows, May
  21,285 rows.
* **Used for**: four aggregates per month (pool gross; gross of the frozen-passed set; gross of the
  real-cost-passed set; gross of the newly-admitted set), the 10-bin stop-width decile table, and
  the 34-cell pre-declared restored-universe grid.
* **April**: pool gross −0.2319, pass-frozen −0.1070, pass-real −0.1623, newly-admitted −0.1959.
* **May**: pool gross −0.2387, pass-frozen −0.1415, pass-real −0.1240, newly-admitted −0.1227.
* **NOT spent**: no rule was fitted on either window, no arm scored, no candidate promoted, no
  per-trade selection made. The full-ledger pass in §2.2 reads **zero** economics — the 82 % of each
  ledger outside the pool has `opportunity_net_proxy_r` null by construction.
* **Verdict**: both months agree with January/February/March. They were spent to establish that a
  five-month result is five-month stable, and they confirmed it.

---

## 8. What would make this bankable

**Already bankable — no new data required.** The mechanism. Nine symbols' spread is
`max_spread_cents/100`, a refusal ceiling, provable from `config/agent_config.yaml` and
`v4_timewarp_simulated_live_research_loop.py:58822-58832`, confirmed by a second independent
instrument with `MEASURED` coverage for 7 of the 9, stable to ±1.5 % on NAS100 across five windows.

**Not bankable.** That correcting it earns anything. Everything it restores is negative in all five
months and no pre-declared conditioning rescues it.

**The four things that would put money behind it, in order:**

1. **A selector over the restored universe.** The repair hands back 38,619–56,079 ledger rows per
   month. Whether anything separates them is now the binding question, and it is answerable on data
   that already exists — no replay, no capture. This is the single highest-value follow-on.
2. **Re-derive the 0.10 / 0.15 caps at era-true cost.** They were calibrated against a scale 3–6×
   too high. At era truth the mean pool cost is 0.137–0.227 R, so a 0.15 total cap is now binding in
   its own right and has never been justified at the corrected scale. This is a config question, not
   a research question.
3. **Fill realism on the index complex before restoring it.** W0-F2 measured that 55.2 % of
   target-first paths reach +2 R before `entry_price` is ever traded. Every number here is
   fill-blind. Restoring SPX500 and NAS100 without a fill contract restores fictitious value along
   with real value, and those two are 100 % deleted today, so the fiction has never been priced on
   them.
4. **Do not gate this on a sealed replay.** `config/agent_config.yaml` is one of R2's 43 bound paths
   (H1), so editing the ceiling keys breaks the execution seal. It is not necessary: the ceiling is
   read **only** as tier 4, when tiers 1–3 miss. Supplying a tier-1 or tier-2 value for the nine
   symbols corrects the cost without touching a `max_spread_cents` byte.

---

## 9. Artifacts

| file | contents |
|---|---|
| `e1_RESULT.md` | this receipt |
| `e1_RESULT.json` | every table above, machine-readable, with the spend register |
| `E1_JAN_REPRO_INDEP_V1.json` | reproduction + implied frozen spread in price units and bps, per symbol |
| `E1_MONTHS_V1.json` | five months × {pool, full ledger} × {cost, gate, index cohort, economics} + per-symbol |
| `E1_ERATRUE_RECOST_V1.json` | instrument B (era-true) recost, mid and high band, per month, per symbol |
| `E1_FULLLEDGER_ERATRUE_V1.json` | era-true over all 679,482 ledger rows; zero economics read |
| `E1_SELECTION_ON_ERROR_V1.json` | error on all / admitted / refused rows, per month |
| `E1_STOPWIDTH_V1.json` | stop-width deciles, within-decile gate edge, Spearman, per month |
| `E1_CONTROL_PASTSTOP_V2.json` | clean-anchor past-stop control (January) |
| `E1_BOUNDARY_V1.json` | ex-breaker control, two-sided cohorts, per family, per session, per month |
| `E1_RESTORED_GRID_V1.json` | 34-cell pre-declared grid over the restored universe |
| `E1_ERA_SPREAD_V1.json` | `spread_model` mid/high/era-ratio per symbol for Jan–May vs the July reference |
| `e1_scripts/e1_00…e1_11` | every script, in order |
