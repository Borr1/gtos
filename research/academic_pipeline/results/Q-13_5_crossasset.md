# Q-13.5 — Cross-Asset Lead-Lag Analysis for XAUUSD

**Status:** PRE-REGISTERED (hypothesis written before data inspection)
**Date:** 2026-04-17
**Analyst:** GTOS Research Agent (Wave 3, $0 local)
**Data:** `data/historical_2026/{XAUUSD,USDJPY,US30_cash,GBPJPY,GBPUSD}_{M15,H1}.csv`, Jan 2 – Apr 10 2026

---

## 1. Hypothesis (PRE-REGISTERED — written before any data inspection)

### Primary research question
Does any of USDJPY, US30, GBPJPY, or GBPUSD *Granger-cause* XAUUSD log-returns at M15 or H1 horizons in a statistically and economically usable way, such that the lagged leader return can serve as a **directional filter or confirmation signal** for XAUUSD trades?

### H0 (null) and H1 (alternative)
- **H0:** Past returns of leader L add no information about future XAUUSD returns beyond XAUUSD's own past. Cross-correlation at lag k≥1 is indistinguishable from zero, sign-agreement ≈ 50%, and Granger p > 0.01.
- **H1:** At least one (leader, lag) pair satisfies ALL THREE pre-registered thresholds below.

### Directional prior (stated before data)
Economic priors going in:
1. **USDJPY → XAUUSD:** Expected NEGATIVE lead-lag. Dollar-yen strength typically accompanies dollar strength / risk-on, which pressures gold. Priced in partly contemporaneously; any residual lead should be short (1–3 M15 candles).
2. **US30 → XAUUSD:** Ambiguous direction. Equities and gold can co-move (liquidity regime) or trade inversely (risk-on/off). Expected WEAK lead; most information is contemporaneous.
3. **GBPJPY → XAUUSD:** Classic risk-on/risk-off cross; expected POSITIVE sign (risk-off drives JPY strength AND gold). Weaker than USDJPY because not dollar-denominated.
4. **GBPUSD → XAUUSD:** Pure dollar proxy. Expected POSITIVE sign (dollar weak → both GBPUSD and XAUUSD up). Largely contemporaneous.

Overall expectation (prior): **most predictive signal is contemporaneous**, not lead-lag. I predict the test FAILS the pre-registered thresholds for all four leaders, because liquid FX/index markets in the 2026 sample are efficient at M15 and the MT5 broker feed is effectively simultaneous. I will be surprised if any pair survives Bonferroni.

### Pre-registered decision rule (must be met to DEPLOY a leader signal)
A (leader, lag) pair qualifies if and only if ALL THREE conditions hold:

1. **|Spearman rho| >= 0.10** at lag k (leader leads by k M15 candles, strict k >= 1).
2. **Granger causality p < 0.01** (raw), AND Bonferroni-adjusted p < 0.004 (12 tests: 4 leaders × 3 lags {1, 3, 6}).
3. **Sign-agreement >= 55%** that sign(leader return[t, t-k+1:t]) matches sign(XAU return[t+1, t+k]) — i.e., 5pp above random.

Additionally — CORROBORATION requirement:
- Pair must show the same directional effect at H1 (lags 1–3) with consistent sign.
- Directional-filter WR test (see Method §4) must show >= 55% XAU 6-candle-ahead WR conditional on leader's |z| > 1.5 and aligned sign.

### Economic significance gate (applied AFTER statistical gate)
Even if all three thresholds are met, the effect must:
- Produce >= 1pp WR lift when used as a veto-style filter on historical OB retest entries, AND
- Not rely on a single macro regime (must appear in both first half and second half of sample, n >= 30 events per half).

If the statistical pass happens but economic gate fails: classify as **SIGNAL / NOT USABLE**.

### What I will NOT do (pre-registered discipline)
- I will NOT test lag = 0 as evidence of lead-lag. Any significance at lag 0 is contemporaneous co-movement, not a tradeable signal.
- I will NOT report post-hoc lag choices. Only lags {1, 3, 6} at M15 and {1, 2, 3} at H1 are in the pre-registered set.
- I will NOT subset the period to make a result pass. First-half / second-half split is a consistency check, not a p-hacking knob.
- I will NOT reuse the same data to "validate" any finding — a pass here is a candidate for out-of-sample testing on a separate window.

### Agent reliability note
In line with GTOS CLAUDE.md §"Agent Reliability Rules":
- All numbers below Section 1 are computed from the committed script (`scripts/q_13_5_crossasset_leadlag.py`).
- `file not found` or `insufficient data` results will be reported verbatim, not fabricated.
- No financial / trading / deployment decision is made in this file. Any "deploy" language is a conditional gate, not a recommendation.

---

*Sections 2+ below are computed from the committed script. Do not edit Section 1 after data inspection.*

---

## 2. Data Summary

- M15 panel length (aligned): **6407** observations
- H1  panel length (aligned): **1601** observations
- Date range (M15): **2026-01-02 01:15:00 .. 2026-04-10 23:45:00**
- statsmodels available: **True**

## 3. M15 Cross-Correlation (Spearman rho, leader leads by k bars; k >= 1 required)

| Leader | k=-6 | k=-3 | k=-1 | k=0 | k=+1 | k=+3 | k=+6 |
|---|---|---|---|---|---|---|---|
| USDJPY | -0.001 | +0.002 | +0.002 | -0.230 | +0.023 | +0.013 | -0.009 |
| US30 | -0.028 | +0.010 | +0.010 | +0.288 | +0.020 | -0.027 | -0.003 |
| GBPJPY | -0.032 | +0.009 | +0.012 | +0.135 | +0.013 | -0.004 | -0.016 |
| GBPUSD | -0.036 | +0.006 | +0.014 | +0.338 | -0.011 | -0.013 | -0.006 |

*Interpretation: positive k means the leader moves first; k=0 is contemporaneous and NOT evidence of lead-lag.*

## 4. M15 Granger Causality (leader -> XAUUSD)

Pre-registered alpha = 0.01 raw; Bonferroni for 12 tests per spec = 0.004; strict = 0.00083

| Leader | lag=1 p | lag=3 p | lag=6 p | n |
|---|---|---|---|---|
| USDJPY | 0.5306 | 0.5889 | 0.6396 | 6407 |
| US30 | 0.5972 | 0.0010 | 0.0016 | 6407 |
| GBPJPY | 0.9836 | 0.3679 | 0.3349 | 6407 |
| GBPUSD | 0.4798 | 0.8407 | 0.7972 | 6407 |

## 5. M15 Sign-Agreement (k-bar leader momentum vs k-bar forward XAU momentum)

| Leader | k=1 | k=3 | k=6 | n(k=6) |
|---|---|---|---|---|
| USDJPY | 0.5149 | 0.4974 | 0.4995 | 6375 |
| US30 | 0.5030 | 0.5089 | 0.4920 | 6380 |
| GBPJPY | 0.5088 | 0.5078 | 0.5114 | 6382 |
| GBPUSD | 0.4972 | 0.4984 | 0.5038 | 6380 |

*Threshold for pass: >= 0.55.*

## 6. Directional Filter Test (|z| > 1.5 leader momentum over k bars)

Reading: given leader's k-bar return is an extreme move (|z|>1.5), does XAU's next k-bar move in the same direction?

| Leader | k | WR_up | n_up | WR_dn | n_dn | WR_combined | n_comb |
|---|---|---|---|---|---|---|---|
| USDJPY | 6 | 0.5067 | 298 | 0.4783 | 345 | 0.4914 | 643 |
| US30 | 6 | 0.5000 | 304 | 0.4369 | 309 | 0.4682 | 613 |
| GBPJPY | 6 | 0.5081 | 309 | 0.4474 | 409 | 0.4735 | 718 |
| GBPUSD | 6 | 0.5053 | 374 | 0.4533 | 364 | 0.4797 | 738 |

## 7. H1 Corroboration

### Cross-correlation (Spearman, lags -3..+3)

| Leader | k=-3 | k=-1 | k=0 | k=+1 | k=+2 | k=+3 |
|---|---|---|---|---|---|---|
| USDJPY | +0.011 | +0.011 | -0.220 | -0.014 | +0.024 | -0.020 |
| US30 | -0.013 | +0.009 | +0.363 | +0.010 | -0.043 | -0.020 |
| GBPJPY | -0.041 | -0.009 | +0.208 | +0.015 | +0.010 | -0.032 |
| GBPUSD | -0.043 | -0.012 | +0.383 | +0.016 | -0.009 | +0.002 |

### H1 Granger p (leader -> XAUUSD)

| Leader | lag=1 | lag=2 | lag=3 | n |
|---|---|---|---|---|
| USDJPY | 0.5396 | 0.8044 | 0.8836 | 1601 |
| US30 | 0.0438 | 0.1165 | 0.0741 | 1601 |
| GBPJPY | 0.4245 | 0.7454 | 0.5368 | 1601 |
| GBPUSD | 0.1516 | 0.3535 | 0.4337 | 1601 |

### H1 Sign-Agreement

| Leader | k=1 | k=2 | k=3 |
|---|---|---|---|
| USDJPY | 0.4900 | 0.5175 | 0.4956 |
| US30 | 0.5047 | 0.4750 | 0.4818 |
| GBPJPY | 0.5047 | 0.5172 | 0.5047 |
| GBPUSD | 0.4972 | 0.4966 | 0.5173 |

## 8. First-Half / Second-Half Consistency (M15 sign-agreement)

| Leader | lag | 1H agree | 1H n | 2H agree | 2H n | delta |
|---|---|---|---|---|---|---|
| USDJPY | 1 | 0.5138 | 3178 | 0.5161 | 3164 | -0.002 |
| USDJPY | 3 | 0.5009 | 3184 | 0.4943 | 3182 | +0.007 |
| USDJPY | 6 | 0.5143 | 3183 | 0.4851 | 3183 | +0.029 |
| US30 | 1 | 0.5051 | 3160 | 0.5011 | 3187 | +0.004 |
| US30 | 3 | 0.5152 | 3181 | 0.5025 | 3190 | +0.013 |
| US30 | 6 | 0.4961 | 3181 | 0.4876 | 3189 | +0.008 |
| GBPJPY | 1 | 0.5060 | 3190 | 0.5118 | 3175 | -0.006 |
| GBPJPY | 3 | 0.5146 | 3185 | 0.5008 | 3187 | +0.014 |
| GBPJPY | 6 | 0.5190 | 3187 | 0.5028 | 3184 | +0.016 |
| GBPUSD | 1 | 0.4960 | 3163 | 0.4984 | 3174 | -0.002 |
| GBPUSD | 3 | 0.4953 | 3182 | 0.5011 | 3185 | -0.006 |
| GBPUSD | 6 | 0.4929 | 3189 | 0.5138 | 3180 | -0.021 |

## 9. Pre-Registered Decision Gate (M15)

All three must hold: |rho|>=0.10, Granger p<0.004 (Bonferroni-spec), sign-agree>=0.55, strict lag>=1.

| Leader | lag | rho | Granger p | sign_agree | pass_rho | pass_granger | pass_sign | ALL PASS |
|---|---|---|---|---|---|---|---|---|
| USDJPY | 1 | +0.023 | 0.5306 | 0.5149 | N | N | N | N |
| USDJPY | 3 | +0.013 | 0.5889 | 0.4974 | N | N | N | N |
| USDJPY | 6 | -0.009 | 0.6396 | 0.4995 | N | N | N | N |
| US30 | 1 | +0.020 | 0.5972 | 0.5030 | N | N | N | N |
| US30 | 3 | -0.027 | 0.0010 | 0.5089 | N | Y | N | N |
| US30 | 6 | -0.003 | 0.0016 | 0.4920 | N | Y | N | N |
| GBPJPY | 1 | +0.013 | 0.9836 | 0.5088 | N | N | N | N |
| GBPJPY | 3 | -0.004 | 0.3679 | 0.5078 | N | N | N | N |
| GBPJPY | 6 | -0.016 | 0.3349 | 0.5114 | N | N | N | N |
| GBPUSD | 1 | -0.011 | 0.4798 | 0.4972 | N | N | N | N |
| GBPUSD | 3 | -0.013 | 0.8407 | 0.4984 | N | N | N | N |
| GBPUSD | 6 | -0.006 | 0.7972 | 0.5038 | N | N | N | N |

**Overall pre-registered pass:** NO — no (leader, lag) pair meets all three pre-registered gates.

## 10. Interpretation and Recommendation

No (leader, lag) pair survives the pre-registered gate. Directional cross-asset lead-lag is NOT a usable signal in the Jan 2 – Apr 10 2026 window at M15 with lag >= 1.


Most predictive values observed at lag 0 (contemporaneous) — expected for liquid FX/index instruments at M15 resolution. This reinforces the existing GTOS design: XAUUSD decisions should rely on own-symbol structure (OB, BOS, CHoCH), not on real-time FX leaders. The H1 panel shows the same pattern.

Result classification: **NULL — null finding consistent with prior expectation (liquid markets are efficient at M15 lead-lag horizons).**


## 11. Replication

- Script: `research/academic_pipeline/scripts/q_13_5_crossasset_leadlag.py`
- Data: `data/historical_2026/*_{M15,H1}.csv` (inner-joined on timestamp)
- No API calls; fully deterministic given the committed CSVs.
- Packages: scipy.stats.spearmanr, statsmodels.tsa.stattools.grangercausalitytests (available=True).
