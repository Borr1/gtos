# Retest Geometry Study (v2, ADR 003) — Historical Report

**Generated:** 2026-04-18T03:11:28.992090+00:00
**Study window:** 2024-04-01 -> 2026-04-17
**Symbols:** XAUUSD, US30_cash, USDJPY, GBPJPY, GBPUSD
**Data source:** C:\Users\MSI\Documents\ai-trading-agent\data\historical
**Methodology:** ADR 003 / `.context/06_decisions/003_retest_geometry_study_corrected_methodology.md`

**Corrected retest timing:** walk begins only from the first M15 candle whose open is >= the CLOSE time of the BOS-confirming H1 candle. This supersedes the v1 study which walked from OB formation time (creating the look-ahead bias A3 identified).

**Twin geometry:** every retest is classified under TWO outcome specs:

- **Geometry A** — wider SL (0.5 x H1 ATR beyond OB), 1 OB-body target, 12h window
- **Geometry B (Test A)** — tighter SL (0.1%/$0.00015 beyond OB), 1.5R target, 3h window

---

## Geometry A

**SL:** opposing side of OB + 0.5 x H1 ATR(14) at retest
**Target:** retest_entry + ob_body_size past far edge (1R = 1 OB body)
**Resolution window:** 48 M15 candles (12.0h)

### Summary — retests per symbol (Geometry A)

| symbol | n | CONTINUED | REVERSED | UNRESOLVED | rate (ex-UNR) |
|---|---|---|---|---|---|
| GBPJPY | 179 | 106 | 66 | 7 | 61.6% |
| GBPUSD | 145 | 75 | 63 | 7 | 54.3% |
| US30_cash | 117 | 59 | 40 | 18 | 59.6% |
| USDJPY | 222 | 133 | 80 | 9 | 62.4% |
| XAUUSD | 136 | 78 | 45 | 13 | 63.4% |
| **combined** | 799 | 451 | 294 | 54 | 60.5% |


### Outcome distribution (Geometry A)

| symbol | n | %CONTINUED | %REVERSED | %UNRESOLVED |
|---|---|---|---|---|
| GBPJPY | 179 | 59.2% | 36.9% | 3.9% |
| GBPUSD | 145 | 51.7% | 43.4% | 4.8% |
| US30_cash | 117 | 50.4% | 34.2% | 15.4% |
| USDJPY | 222 | 59.9% | 36.0% | 4.1% |
| XAUUSD | 136 | 57.4% | 33.1% | 9.6% |
| **combined** | 799 | 56.4% | 36.8% | 6.8% |


### MAE percentiles (Geometry A)

### MAE (pips) — Geometry A

| scope | n | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| GBPJPY | 179 | 4.300 | 12.150 | 26.300 | 46.900 | 66.200 |
| GBPUSD | 145 | 3.240 | 6.900 | 14.300 | 23.600 | 37.440 |
| US30_cash | 117 | 12.800 | 33.000 | 87.900 | 152.000 | 256.900 |
| USDJPY | 222 | 3.610 | 7.725 | 18.350 | 36.475 | 58.300 |
| XAUUSD | 136 | 31.750 | 51.975 | 86.250 | 155.875 | 231.000 |
| **combined** | 799 | 4.800 | 12.300 | 28.300 | 62.500 | 141.340 |

### MAE (H1 ATR units) — Geometry A

| scope | n | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| GBPJPY | 179 | 0.153 | 0.372 | 0.894 | 1.454 | 1.915 |
| GBPUSD | 145 | 0.213 | 0.435 | 0.942 | 1.496 | 2.222 |
| US30_cash | 117 | 0.190 | 0.395 | 0.862 | 1.568 | 2.509 |
| USDJPY | 222 | 0.164 | 0.354 | 0.800 | 1.441 | 2.182 |
| XAUUSD | 136 | 0.297 | 0.470 | 0.864 | 1.440 | 2.066 |
| **combined** | 799 | 0.188 | 0.391 | 0.865 | 1.477 | 2.160 |

### MAE (% of OB body) — Geometry A

| scope | n | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| GBPJPY | 179 | 20.293 | 51.042 | 117.647 | 201.597 | 318.421 |
| GBPUSD | 145 | 26.768 | 58.403 | 121.359 | 190.667 | 243.070 |
| US30_cash | 117 | 19.201 | 44.118 | 96.039 | 148.299 | 239.954 |
| USDJPY | 222 | 24.501 | 55.112 | 121.324 | 209.527 | 356.845 |
| XAUUSD | 136 | 31.616 | 56.580 | 105.317 | 173.187 | 316.495 |
| **combined** | 799 | 22.780 | 53.200 | 109.756 | 194.733 | 301.507 |



### Penetration percentiles (Geometry A)

### Penetration (pips) — Geometry A

| scope | n | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| GBPJPY | 179 | 0.000 | 0.000 | 5.900 | 21.200 | 33.400 |
| GBPUSD | 145 | 0.000 | 0.000 | 5.800 | 10.200 | 20.100 |
| US30_cash | 117 | 0.000 | 0.000 | 3.800 | 67.400 | 111.920 |
| USDJPY | 222 | 0.000 | 0.000 | 2.300 | 16.975 | 27.590 |
| XAUUSD | 136 | 0.000 | 0.000 | 6.800 | 51.025 | 138.300 |
| **combined** | 799 | 0.000 | 0.000 | 4.100 | 21.850 | 60.600 |

### Penetration (H1 ATR units) — Geometry A

| scope | n | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| GBPJPY | 179 | 0.000 | 0.000 | 0.184 | 0.637 | 1.043 |
| GBPUSD | 145 | 0.000 | 0.000 | 0.353 | 0.694 | 1.192 |
| US30_cash | 117 | 0.000 | 0.000 | 0.031 | 0.670 | 1.044 |
| USDJPY | 222 | 0.000 | 0.000 | 0.111 | 0.718 | 1.073 |
| XAUUSD | 136 | 0.000 | 0.000 | 0.055 | 0.635 | 0.893 |
| **combined** | 799 | 0.000 | 0.000 | 0.134 | 0.670 | 1.085 |

**Fraction of retests that pierced the OB edge (Geometry A):** 437/799 = 54.7%



### Time-to-MAE distribution (Geometry A)

**Percentiles (M15 candles from retest to MAE) — Geometry A:**

| p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|
| 0.0 | 0.0 | 2.0 | 8.0 | 20.0 |


### Session breakdowns (Geometry A)

Continuation rate by session (CONTINUED / (CONTINUED+REVERSED)):

| symbol | London | NY | Tokyo | None |
|---|---|---|---|---|
| GBPJPY | 24/36 (66.7%) | 15/29 (51.7%) | 51/89 (57.3%) | 16/18 (88.9%) |
| GBPUSD | 17/37 (45.9%) | 14/26 (53.8%) | 37/63 (58.7%) | 7/12 (58.3%) |
| US30_cash | 10/14 (71.4%) | 28/55 (50.9%) | 18/27 (66.7%) | 3/3 (100.0%) |
| USDJPY | 24/35 (68.6%) | 20/41 (48.8%) | 81/123 (65.9%) | 8/14 (57.1%) |
| XAUUSD | 21/26 (80.8%) | 21/38 (55.3%) | 35/58 (60.3%) | 1/1 (100.0%) |
| **all** | 96/148 (64.9%) | 98/189 (51.9%) | 222/360 (61.7%) | 35/48 (72.9%) |


### MAE-tercile continuation (Geometry A)

Does deep MAE predict reversal?

| tercile | MAE (ATR) range | continued/n | rate | 95% CI |
|---|---|---|---|---|
| low | <= 0.507 | 241/248 | 97.2% | [94.3%, 98.6%] |
| mid | (0.507, 1.166] | 168/249 | 67.5% | [61.4%, 73.0%] |
| high | > 1.166 | 42/248 | 16.9% | [12.8%, 22.1%] |


### Penetration binary (Geometry A)

| group | result |
|---|---|
| pierced OB edge | 130/424 = 30.7% [26.5%, 35.2%] |
| did NOT pierce | 321/321 = 100.0% [98.8%, 100.0%] |


### OB-body-size tercile continuation (Geometry A)

Do small / medium / large OBs differ?

| tercile | body_size (ATR) range | continued/n | rate | 95% CI |
|---|---|---|---|---|
| low | <= 0.565 | 149/248 | 60.1% | [53.9%, 66.0%] |
| mid | (0.565, 0.912] | 156/249 | 62.7% | [56.5%, 68.4%] |
| high | > 0.912 | 146/248 | 58.9% | [52.7%, 64.8%] |



---

## Geometry B

**SL:** Test A rule: XAUUSD `ob_low - 0.001 * ob_low` (bullish); other symbols `ob_low - 0.00015` (absolute). Mirror for bearish.
**Target:** retest_entry + 1.5 x SL_distance
**Resolution window:** 12 M15 candles (3.0h)

### Summary — retests per symbol (Geometry B)

| symbol | n | CONTINUED | REVERSED | UNRESOLVED | rate (ex-UNR) |
|---|---|---|---|---|---|
| GBPJPY | 179 | 53 | 81 | 45 | 39.6% |
| GBPUSD | 145 | 24 | 70 | 51 | 25.5% |
| US30_cash | 117 | 24 | 40 | 53 | 37.5% |
| USDJPY | 222 | 63 | 90 | 69 | 41.2% |
| XAUUSD | 136 | 21 | 44 | 71 | 32.3% |
| **combined** | 799 | 185 | 325 | 289 | 36.3% |


### Outcome distribution (Geometry B)

| symbol | n | %CONTINUED | %REVERSED | %UNRESOLVED |
|---|---|---|---|---|
| GBPJPY | 179 | 29.6% | 45.3% | 25.1% |
| GBPUSD | 145 | 16.6% | 48.3% | 35.2% |
| US30_cash | 117 | 20.5% | 34.2% | 45.3% |
| USDJPY | 222 | 28.4% | 40.5% | 31.1% |
| XAUUSD | 136 | 15.4% | 32.4% | 52.2% |
| **combined** | 799 | 23.2% | 40.7% | 36.2% |


### MAE percentiles (Geometry B)

### MAE (pips) — Geometry B

| scope | n | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| GBPJPY | 179 | 4.300 | 11.550 | 21.400 | 33.150 | 54.780 |
| GBPUSD | 145 | 3.580 | 6.500 | 11.700 | 16.600 | 25.740 |
| US30_cash | 117 | 12.300 | 28.000 | 55.450 | 110.000 | 183.060 |
| USDJPY | 222 | 3.500 | 7.175 | 16.150 | 26.575 | 48.000 |
| XAUUSD | 136 | 32.750 | 51.800 | 85.600 | 141.200 | 226.100 |
| **combined** | 799 | 4.680 | 11.100 | 22.100 | 52.000 | 118.240 |

### MAE (H1 ATR units) — Geometry B

| scope | n | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| GBPJPY | 179 | 0.153 | 0.352 | 0.677 | 1.013 | 1.504 |
| GBPUSD | 145 | 0.245 | 0.418 | 0.751 | 1.157 | 1.647 |
| US30_cash | 117 | 0.141 | 0.310 | 0.629 | 1.106 | 1.831 |
| USDJPY | 222 | 0.156 | 0.334 | 0.688 | 1.095 | 1.851 |
| XAUUSD | 136 | 0.317 | 0.455 | 0.843 | 1.253 | 1.966 |
| **combined** | 799 | 0.183 | 0.372 | 0.702 | 1.117 | 1.771 |

### MAE (% of OB body) — Geometry B

| scope | n | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| GBPJPY | 179 | 16.918 | 50.142 | 87.500 | 156.902 | 259.601 |
| GBPUSD | 145 | 22.846 | 49.515 | 100.000 | 149.533 | 205.366 |
| US30_cash | 117 | 14.717 | 28.928 | 63.033 | 113.700 | 177.782 |
| USDJPY | 222 | 22.880 | 49.002 | 100.564 | 179.231 | 297.815 |
| XAUUSD | 136 | 29.792 | 57.077 | 97.528 | 163.271 | 291.716 |
| **combined** | 799 | 20.410 | 47.352 | 93.284 | 154.568 | 251.948 |



### Penetration percentiles (Geometry B)

### Penetration (pips) — Geometry B

| scope | n | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| GBPJPY | 179 | 0.000 | 0.000 | 0.400 | 8.500 | 23.920 |
| GBPUSD | 145 | 0.000 | 0.000 | 1.700 | 6.200 | 16.420 |
| US30_cash | 117 | 0.000 | 0.000 | 0.000 | 21.700 | 73.080 |
| USDJPY | 222 | 0.000 | 0.000 | 0.000 | 7.175 | 19.690 |
| XAUUSD | 136 | 0.000 | 0.000 | 2.400 | 46.275 | 135.200 |
| **combined** | 799 | 0.000 | 0.000 | 0.000 | 9.800 | 41.660 |

### Penetration (H1 ATR units) — Geometry B

| scope | n | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| GBPJPY | 179 | 0.000 | 0.000 | 0.012 | 0.248 | 0.749 |
| GBPUSD | 145 | 0.000 | 0.000 | 0.097 | 0.381 | 0.832 |
| US30_cash | 117 | 0.000 | 0.000 | 0.000 | 0.256 | 0.866 |
| USDJPY | 222 | 0.000 | 0.000 | 0.000 | 0.256 | 0.956 |
| XAUUSD | 136 | 0.000 | 0.000 | 0.009 | 0.551 | 0.860 |
| **combined** | 799 | 0.000 | 0.000 | 0.000 | 0.323 | 0.859 |

**Fraction of retests that pierced the OB edge (Geometry B):** 390/799 = 48.8%



### Time-to-MAE distribution (Geometry B)

**Percentiles (M15 candles from retest to MAE) — Geometry B:**

| p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|
| 0.0 | 0.0 | 1.0 | 5.0 | 10.0 |


### Session breakdowns (Geometry B)

Continuation rate by session (CONTINUED / (CONTINUED+REVERSED)):

| symbol | London | NY | Tokyo | None |
|---|---|---|---|---|
| GBPJPY | 8/24 (33.3%) | 10/24 (41.7%) | 24/73 (32.9%) | 11/13 (84.6%) |
| GBPUSD | 2/28 (7.1%) | 7/19 (36.8%) | 15/39 (38.5%) | 0/8 (0.0%) |
| US30_cash | 4/7 (57.1%) | 13/45 (28.9%) | 5/10 (50.0%) | 2/2 (100.0%) |
| USDJPY | 9/25 (36.0%) | 8/29 (27.6%) | 41/87 (47.1%) | 5/12 (41.7%) |
| XAUUSD | 4/8 (50.0%) | 7/27 (25.9%) | 9/29 (31.0%) | 1/1 (100.0%) |
| **all** | 27/92 (29.3%) | 45/144 (31.2%) | 94/238 (39.5%) | 19/36 (52.8%) |


### MAE-tercile continuation (Geometry B)

Does deep MAE predict reversal?

| tercile | MAE (ATR) range | continued/n | rate | 95% CI |
|---|---|---|---|---|
| low | <= 0.460 | 134/170 | 78.8% | [72.1%, 84.3%] |
| mid | (0.460, 0.999] | 44/170 | 25.9% | [19.9%, 32.9%] |
| high | > 0.999 | 7/170 | 4.1% | [2.0%, 8.3%] |


### Penetration binary (Geometry B)

| group | result |
|---|---|
| pierced OB edge | 45/370 = 12.2% [9.2%, 15.9%] |
| did NOT pierce | 140/140 = 100.0% [97.3%, 100.0%] |


### OB-body-size tercile continuation (Geometry B)

Do small / medium / large OBs differ?

| tercile | body_size (ATR) range | continued/n | rate | 95% CI |
|---|---|---|---|---|
| low | <= 0.501 | 58/170 | 34.1% | [27.4%, 41.5%] |
| mid | (0.501, 0.742] | 65/170 | 38.2% | [31.3%, 45.7%] |
| high | > 0.742 | 62/170 | 36.5% | [29.6%, 43.9%] |



---

## Geometry A vs Geometry B — reconciliation

- Geometry A ex-UNR continuation rate (combined): **60.5%** (CONTINUED=451, REVERSED=294, UNRESOLVED=54)
- Geometry B ex-UNR continuation rate (combined): **36.3%** (CONTINUED=185, REVERSED=325, UNRESOLVED=289)

The two geometries measure different questions on the SAME retest:
- Geometry A asks 'does price continue one OB-body-length within 12h without wiping past the OB + 0.5 ATR buffer?'. The wider SL plus longer horizon make both CONTINUED and UNRESOLVED more likely than under Geometry B, while absolute REVERSED count is typically lower.
- Geometry B asks 'does price hit a 1.5R target within 3h without hitting the tight Test A SL?'. Tight SL + short horizon produce more REVERSED and fewer UNRESOLVED. This number is the one directly comparable to Test A's ~70% baseline (n=219, +17pp, p=0.003).

**Validation test:** if Geometry B's combined continuation rate is close to ~65-75%, the corrected timing is consistent with Test A's independent finding. A large gap in either direction indicates a methodology issue that deserves investigation beyond what this study can answer.

---

Notes:
- UNRESOLVED retests are EXCLUDED from ex-UNR continuation-rate tables.
- 95% CI is Wilson score.
- Tercile cut-points are per-bucket relative percentiles.
- Retest timing invariant enforced at classify-time: retest_ts > bos_confirm_ts (strict).
- Geometry B SL rule is taken verbatim from Test A (`scripts/ob_retest_comprehensive.py`). The `0.00015` absolute buffer is microscopic for JPY pairs and US30; this is faithful reproduction of Test A, not a recommended production SL.
