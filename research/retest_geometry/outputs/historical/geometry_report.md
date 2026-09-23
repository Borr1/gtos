# Retest Geometry Study (v2, ADR 003) — Historical Report

**Generated:** 2026-04-17T21:23:25.516857+00:00
**Study window:** 2026-01-01 -> 2026-04-17
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
| GBPJPY | 19 | 15 | 3 | 1 | 83.3% |
| GBPUSD | 19 | 6 | 11 | 2 | 35.3% |
| US30_cash | 28 | 12 | 11 | 5 | 52.2% |
| USDJPY | 33 | 29 | 2 | 2 | 93.5% |
| XAUUSD | 22 | 15 | 6 | 1 | 71.4% |
| **combined** | 121 | 77 | 33 | 11 | 70.0% |


### Outcome distribution (Geometry A)

| symbol | n | %CONTINUED | %REVERSED | %UNRESOLVED |
|---|---|---|---|---|
| GBPJPY | 19 | 78.9% | 15.8% | 5.3% |
| GBPUSD | 19 | 31.6% | 57.9% | 10.5% |
| US30_cash | 28 | 42.9% | 39.3% | 17.9% |
| USDJPY | 33 | 87.9% | 6.1% | 6.1% |
| XAUUSD | 22 | 68.2% | 27.3% | 4.5% |
| **combined** | 121 | 63.6% | 27.3% | 9.1% |


### MAE percentiles (Geometry A)

### MAE (pips) — Geometry A

| scope | n | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| GBPJPY | 19 | 6.420 | 9.800 | 19.200 | 38.200 | 57.360 |
| GBPUSD | 19 | 4.220 | 12.800 | 17.300 | 23.700 | 34.900 |
| US30_cash | 28 | 29.274 | 58.750 | 122.155 | 186.387 | 303.690 |
| USDJPY | 33 | 2.640 | 5.000 | 7.800 | 16.800 | 33.020 |
| XAUUSD | 22 | 87.540 | 128.025 | 205.950 | 400.575 | 821.670 |
| **combined** | 121 | 4.900 | 11.400 | 30.600 | 121.000 | 267.500 |

### MAE (H1 ATR units) — Geometry A

| scope | n | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| GBPJPY | 19 | 0.188 | 0.316 | 0.724 | 1.438 | 1.677 |
| GBPUSD | 19 | 0.198 | 0.712 | 0.956 | 1.389 | 1.914 |
| US30_cash | 28 | 0.248 | 0.573 | 0.955 | 1.462 | 2.377 |
| USDJPY | 33 | 0.157 | 0.245 | 0.334 | 0.686 | 1.568 |
| XAUUSD | 22 | 0.315 | 0.441 | 0.727 | 1.225 | 1.884 |
| **combined** | 121 | 0.184 | 0.309 | 0.724 | 1.295 | 2.026 |

### MAE (% of OB body) — Geometry A

| scope | n | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| GBPJPY | 19 | 18.736 | 47.684 | 97.248 | 176.898 | 235.420 |
| GBPUSD | 19 | 35.000 | 67.272 | 118.050 | 184.209 | 227.451 |
| US30_cash | 28 | 19.585 | 55.382 | 96.724 | 165.040 | 291.784 |
| USDJPY | 33 | 20.113 | 28.404 | 58.182 | 107.362 | 218.770 |
| XAUUSD | 22 | 27.278 | 66.857 | 95.232 | 147.738 | 256.494 |
| **combined** | 121 | 20.567 | 46.711 | 89.698 | 161.029 | 238.554 |



### Penetration percentiles (Geometry A)

### Penetration (pips) — Geometry A

| scope | n | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| GBPJPY | 19 | 0.000 | 0.000 | 6.300 | 15.800 | 22.880 |
| GBPUSD | 19 | 0.000 | 0.000 | 8.600 | 17.300 | 19.100 |
| US30_cash | 28 | 0.000 | 0.000 | 10.385 | 73.870 | 150.079 |
| USDJPY | 33 | 0.000 | 0.000 | 0.000 | 3.700 | 12.760 |
| XAUUSD | 22 | 0.000 | 0.000 | 37.150 | 184.725 | 443.280 |
| **combined** | 121 | 0.000 | 0.000 | 0.000 | 21.300 | 119.400 |

### Penetration (H1 ATR units) — Geometry A

| scope | n | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| GBPJPY | 19 | 0.000 | 0.000 | 0.173 | 0.535 | 0.745 |
| GBPUSD | 19 | 0.000 | 0.000 | 0.588 | 0.870 | 1.155 |
| US30_cash | 28 | 0.000 | 0.000 | 0.090 | 0.646 | 0.951 |
| USDJPY | 33 | 0.000 | 0.000 | 0.000 | 0.134 | 0.671 |
| XAUUSD | 22 | 0.000 | 0.000 | 0.102 | 0.603 | 0.855 |
| **combined** | 121 | 0.000 | 0.000 | 0.000 | 0.629 | 1.013 |

**Fraction of retests that pierced the OB edge (Geometry A):** 58/121 = 47.9%



### Time-to-MAE distribution (Geometry A)

**Percentiles (M15 candles from retest to MAE) — Geometry A:**

| p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|
| 0.0 | 0.0 | 2.0 | 11.0 | 21.0 |


### Session breakdowns (Geometry A)

Continuation rate by session (CONTINUED / (CONTINUED+REVERSED)):

| symbol | London | NY | Tokyo | None |
|---|---|---|---|---|
| GBPJPY | 4/4 (100.0%) | 2/3 (66.7%) | 6/8 (75.0%) | 3/3 (100.0%) |
| GBPUSD | 1/3 (33.3%) | 2/4 (50.0%) | 3/8 (37.5%) | 0/2 (0.0%) |
| US30_cash | 2/3 (66.7%) | 6/12 (50.0%) | 3/7 (42.9%) | 1/1 (100.0%) |
| USDJPY | 8/9 (88.9%) | 3/3 (100.0%) | 17/18 (94.4%) | 1/1 (100.0%) |
| XAUUSD | 4/4 (100.0%) | 1/4 (25.0%) | 10/13 (76.9%) | - |
| **all** | 19/23 (82.6%) | 14/26 (53.8%) | 39/54 (72.2%) | 5/7 (71.4%) |


### MAE-tercile continuation (Geometry A)

Does deep MAE predict reversal?

| tercile | MAE (ATR) range | continued/n | rate | 95% CI |
|---|---|---|---|---|
| low | <= 0.349 | 37/37 | 100.0% | [90.6%, 100.0%] |
| mid | (0.349, 0.939] | 30/36 | 83.3% | [68.1%, 92.1%] |
| high | > 0.939 | 10/37 | 27.0% | [15.4%, 43.0%] |


### Penetration binary (Geometry A)

| group | result |
|---|---|
| pierced OB edge | 22/55 = 40.0% [28.1%, 53.2%] |
| did NOT pierce | 55/55 = 100.0% [93.5%, 100.0%] |


### OB-body-size tercile continuation (Geometry A)

Do small / medium / large OBs differ?

| tercile | body_size (ATR) range | continued/n | rate | 95% CI |
|---|---|---|---|---|
| low | <= 0.639 | 25/37 | 67.6% | [51.5%, 80.4%] |
| mid | (0.639, 0.980] | 26/36 | 72.2% | [56.0%, 84.2%] |
| high | > 0.980 | 26/37 | 70.3% | [54.2%, 82.5%] |



---

## Geometry B

**SL:** Test A rule: XAUUSD `ob_low - 0.001 * ob_low` (bullish); other symbols `ob_low - 0.00015` (absolute). Mirror for bearish.
**Target:** retest_entry + 1.5 x SL_distance
**Resolution window:** 12 M15 candles (3.0h)

### Summary — retests per symbol (Geometry B)

| symbol | n | CONTINUED | REVERSED | UNRESOLVED | rate (ex-UNR) |
|---|---|---|---|---|---|
| GBPJPY | 19 | 9 | 6 | 4 | 60.0% |
| GBPUSD | 19 | 5 | 7 | 7 | 41.7% |
| US30_cash | 28 | 3 | 8 | 17 | 27.3% |
| USDJPY | 33 | 14 | 5 | 14 | 73.7% |
| XAUUSD | 22 | 2 | 9 | 11 | 18.2% |
| **combined** | 121 | 33 | 35 | 53 | 48.5% |


### Outcome distribution (Geometry B)

| symbol | n | %CONTINUED | %REVERSED | %UNRESOLVED |
|---|---|---|---|---|
| GBPJPY | 19 | 47.4% | 31.6% | 21.1% |
| GBPUSD | 19 | 26.3% | 36.8% | 36.8% |
| US30_cash | 28 | 10.7% | 28.6% | 60.7% |
| USDJPY | 33 | 42.4% | 15.2% | 42.4% |
| XAUUSD | 22 | 9.1% | 40.9% | 50.0% |
| **combined** | 121 | 27.3% | 28.9% | 43.8% |


### MAE percentiles (Geometry B)

### MAE (pips) — Geometry B

| scope | n | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| GBPJPY | 19 | 8.620 | 11.250 | 19.200 | 30.400 | 48.920 |
| GBPUSD | 19 | 4.340 | 5.900 | 11.600 | 18.550 | 23.820 |
| US30_cash | 28 | 16.885 | 38.955 | 69.450 | 142.913 | 191.793 |
| USDJPY | 33 | 2.640 | 5.000 | 8.900 | 15.500 | 26.400 |
| XAUUSD | 22 | 87.540 | 108.125 | 220.500 | 382.575 | 684.690 |
| **combined** | 121 | 5.000 | 9.200 | 23.800 | 99.600 | 230.500 |

### MAE (H1 ATR units) — Geometry B

| scope | n | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| GBPJPY | 19 | 0.217 | 0.371 | 0.802 | 1.038 | 1.428 |
| GBPUSD | 19 | 0.208 | 0.312 | 0.638 | 1.009 | 1.222 |
| US30_cash | 28 | 0.145 | 0.284 | 0.605 | 1.049 | 1.469 |
| USDJPY | 33 | 0.157 | 0.245 | 0.419 | 0.637 | 1.215 |
| XAUUSD | 22 | 0.315 | 0.398 | 0.715 | 1.225 | 2.006 |
| **combined** | 121 | 0.184 | 0.297 | 0.565 | 1.019 | 1.519 |

### MAE (% of OB body) — Geometry B

| scope | n | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| GBPJPY | 19 | 39.602 | 49.713 | 80.168 | 147.098 | 172.039 |
| GBPUSD | 19 | 35.664 | 44.901 | 65.854 | 103.122 | 169.902 |
| US30_cash | 28 | 15.044 | 26.942 | 65.155 | 134.627 | 165.911 |
| USDJPY | 33 | 20.113 | 26.471 | 58.182 | 112.500 | 179.385 |
| XAUUSD | 22 | 26.869 | 61.603 | 90.133 | 172.849 | 255.802 |
| **combined** | 121 | 19.787 | 37.500 | 74.667 | 128.025 | 180.422 |



### Penetration percentiles (Geometry B)

### Penetration (pips) — Geometry B

| scope | n | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| GBPJPY | 19 | 0.000 | 0.000 | 0.000 | 6.400 | 13.680 |
| GBPUSD | 19 | 0.000 | 0.000 | 0.000 | 5.150 | 19.100 |
| US30_cash | 28 | 0.000 | 0.000 | 0.000 | 16.985 | 51.990 |
| USDJPY | 33 | 0.000 | 0.000 | 0.000 | 2.000 | 5.480 |
| XAUUSD | 22 | 0.000 | 0.000 | 37.150 | 155.900 | 440.530 |
| **combined** | 121 | 0.000 | 0.000 | 0.000 | 6.200 | 74.300 |

### Penetration (H1 ATR units) — Geometry B

| scope | n | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| GBPJPY | 19 | 0.000 | 0.000 | 0.000 | 0.217 | 0.434 |
| GBPUSD | 19 | 0.000 | 0.000 | 0.000 | 0.248 | 1.052 |
| US30_cash | 28 | 0.000 | 0.000 | 0.000 | 0.144 | 0.652 |
| USDJPY | 33 | 0.000 | 0.000 | 0.000 | 0.094 | 0.251 |
| XAUUSD | 22 | 0.000 | 0.000 | 0.102 | 0.485 | 0.959 |
| **combined** | 121 | 0.000 | 0.000 | 0.000 | 0.240 | 0.805 |

**Fraction of retests that pierced the OB edge (Geometry B):** 47/121 = 38.8%



### Time-to-MAE distribution (Geometry B)

**Percentiles (M15 candles from retest to MAE) — Geometry B:**

| p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|
| 0.0 | 0.0 | 1.0 | 7.0 | 10.0 |


### Session breakdowns (Geometry B)

Continuation rate by session (CONTINUED / (CONTINUED+REVERSED)):

| symbol | London | NY | Tokyo | None |
|---|---|---|---|---|
| GBPJPY | 2/3 (66.7%) | 2/3 (66.7%) | 3/7 (42.9%) | 2/2 (100.0%) |
| GBPUSD | 0/1 (0.0%) | 3/4 (75.0%) | 2/5 (40.0%) | 0/2 (0.0%) |
| US30_cash | - | 2/7 (28.6%) | 1/4 (25.0%) | - |
| USDJPY | 4/6 (66.7%) | 2/3 (66.7%) | 7/9 (77.8%) | 1/1 (100.0%) |
| XAUUSD | 1/1 (100.0%) | 0/3 (0.0%) | 1/7 (14.3%) | - |
| **all** | 7/11 (63.6%) | 9/20 (45.0%) | 14/32 (43.8%) | 3/5 (60.0%) |


### MAE-tercile continuation (Geometry B)

Does deep MAE predict reversal?

| tercile | MAE (ATR) range | continued/n | rate | 95% CI |
|---|---|---|---|---|
| low | <= 0.318 | 22/23 | 95.7% | [79.0%, 99.2%] |
| mid | (0.318, 0.952] | 8/22 | 36.4% | [19.7%, 57.0%] |
| high | > 0.952 | 3/23 | 13.0% | [4.5%, 32.1%] |


### Penetration binary (Geometry B)

| group | result |
|---|---|
| pierced OB edge | 9/44 = 20.5% [11.2%, 34.5%] |
| did NOT pierce | 24/24 = 100.0% [86.2%, 100.0%] |


### OB-body-size tercile continuation (Geometry B)

Do small / medium / large OBs differ?

| tercile | body_size (ATR) range | continued/n | rate | 95% CI |
|---|---|---|---|---|
| low | <= 0.518 | 9/23 | 39.1% | [22.2%, 59.2%] |
| mid | (0.518, 0.832] | 11/22 | 50.0% | [30.7%, 69.3%] |
| high | > 0.832 | 13/23 | 56.5% | [36.8%, 74.4%] |



---

## Geometry A vs Geometry B — reconciliation

- Geometry A ex-UNR continuation rate (combined): **70.0%** (CONTINUED=77, REVERSED=33, UNRESOLVED=11)
- Geometry B ex-UNR continuation rate (combined): **48.5%** (CONTINUED=33, REVERSED=35, UNRESOLVED=53)

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
