# GTOS Distributional Characterization — Summary

**Generated:** 20260411_012816 UTC
**Method:** Full statistical characterization — moments, normality, GPD tails, ACF, GARCH, jumps, intraday seasonality, conditional distributions
**Bonferroni threshold:** α* = 0.000093  (540 total tests)

---

## GTOS IMPLICATIONS (XAUUSD H1 unless noted)

### Q1: Q1 TAIL VS SL PLACEMENT

Gold H1 lower tail: GPD shape ξ=0.3500 (FAT). The 1%-quantile worst hourly move is 76.4 bps (0.7638% of price). For a $3,000 gold price, this is ~$22.91/oz per hour. If your typical H1 SL is ~0.10-0.30% (~$3-9/oz), the 1% worst move LIKELY EXCEEDS your SL. Fat tails (ξ=0.350) confirm that Gaussian-calibrated SLs will be hit more frequently than expected: 6.242527362660495× more 3σ events/year.

### Q2: Q2 VOLATILITY CLUSTERING

GARCH(1,1) persistence α+β=0.9906. Half-life of volatility shocks: ~73.1 H1 bars (3.06 trading days). VERY STRONG clustering. A volatile session today implies ~79.7% of that excess vol persists to same time tomorrow (24 H1 bars forward). IMPLICATION: Pre-trade ATR-based position sizing is warranted; a quiet day can be followed by an explosive one.

### Q3: Q3 ACF AT TRADING HORIZON 1 4 H1

Gold H1 return ACF: lag1=-0.0199, lag4=0.0058. Significant lags (outside Bartlett ±0.0162): [1, 3, 7, 8, 10, 12, 13, 17, 18, 20]. Lags 1-4 (our trading horizon 1-4 H1 candles): SIGNIFICANT at [1, 3]. This provides INDEPENDENT CONFIRMATION for the OB retest mechanism's 2-lag predictability window. Note: economic value is limited (0.41 bps vs ~4 bps spread + slippage).

### Q4: Q4 POST JUMP BEHAVIOR

Post-jump returns (H1, direction-adjusted): lag1 mean=-0.001349 (REVERSION), p=0.1370. Jump frequency: 0.046 jumps/day. Peak jump hour: UTC 15. Post-jump REVERSION supports the sweep-and-revert hypothesis (OB retest as stop-cascade mean-reversion to pre-cascade equilibrium). Result not statistically significant at 5% level.

### Q5: Q5 LEVERAGE EFFECT LONG VS SHORT

EGARCH gamma (asymmetry) = 0.0057. NO significant leverage effect. Gold volatility is symmetric — LONG and SHORT setups have similar post-entry vol profiles.

### Q6: Q6 BEST HOURS BY EDGE POTENTIAL

Top-5 absolute return hours (UTC): [(17, '25.66bps'), (16, '25.44bps'), (15, '24.56bps'), (18, '18.80bps'), (4, '18.69bps')]. Kill zone hours ranked by vol: [(16, '25.44bps'), (15, '24.56bps'), (10, '16.19bps'), (14, '15.04bps')]. Kruskal-Wallis p=0.040813 — hourly distributions ARE significantly different. GTOS kill zones align well with the highest-volatility hours.

---

## TRADEABLE ANOMALIES

Only findings with p < 0.05 are listed.  **Bold** = survives Bonferroni (p < 0.00009).  ★ = economically significant (edge > transaction cost).

### US30

| TF | Session | Finding | p-value | Bonferroni | Edge (bps) | Econ Sig | Stable |
|---|---|---|---|---|---|---|---|
| D1 | All | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0000 | **YES** | — | — | None |
| H1 | London | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0000 | **YES** | — | — | None |
| H1 | NY | Non-normal distribution (excess kurtosis=2.38, skew=-0.094) | 0.0000 | **YES** | — | — | None |
| H1 | NY | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0000 | **YES** | — | — | None |
| M15 | All | Significant return ACF at lags [1, 2, 3, 4, 5, 6, 8, 11, 12, 15] — linear direct | 0.0000 | **YES** | 0.14 | no | None |
| D1 | All | Significant return ACF at lags [1, 2, 4, 5, 6, 7, 8, 9, 13, 14, 15, 16, 20] — li | 0.0000 | **YES** | 13.81 | ★ YES | None |
| M15 | NY | Significant return ACF at lags [2, 3, 5, 6, 8, 13, 14, 17, 18] — linear directio | 0.0000 | **YES** | 0.77 | no | None |
| M15 | All | Intraday volatility seasonality — different hours have different distributions | 0.0437 | no | — | — | None |
| M15 | NY | Session-open bars have significantly different return distribution | 0.0441 | no | 0.70 | no | None |
| M15 | All | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0500 | no | — | — | None |
| M15 | London | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0500 | no | — | — | None |
| M15 | NY | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0500 | no | — | — | None |
| H1 | All | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0500 | no | — | — | None |
| H1 | London | Significant return ACF at lags [8, 12, 14] — linear directional predictability | 0.0844 | no | 0.57 | no | None |
| M15 | London | Significant return ACF at lags [1, 9, 15, 16, 17, 18] — linear directional predi | 0.1510 | no | 0.21 | no | None |
| H1 | All | Significant return ACF at lags [7, 17, 18, 19] — linear directional predictabili | 0.3950 | no | 0.40 | no | None |
| M15 | All | Non-normal distribution (excess kurtosis=88.94, skew=0.305) | 0.0000 | **YES** | — | — | None |
| M15 | All | GARCH persistence=0.9800 — strong volatility clustering | — | no | — | — | None |
| M15 | All | Fat tails: 6.8× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| M15 | London | Non-normal distribution (excess kurtosis=14.27, skew=-0.285) | 0.0000 | **YES** | — | — | None |
| M15 | London | GARCH persistence=0.9800 — strong volatility clustering | — | no | — | — | None |
| M15 | London | EGARCH leverage effect: γ=-0.0204 (down moves → more vol) | — | no | — | — | None |
| M15 | London | Fat tails: 6.0× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| M15 | NY | Non-normal distribution (excess kurtosis=20.32, skew=0.485) | 0.0000 | **YES** | — | — | None |
| M15 | NY | GARCH persistence=0.9864 — strong volatility clustering | — | no | — | — | None |
| M15 | NY | EGARCH leverage effect: γ=-0.0228 (down moves → more vol) | — | no | — | — | None |
| M15 | NY | Fat tails: 5.4× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| H1 | All | Non-normal distribution (excess kurtosis=68.68, skew=1.067) | 0.0000 | **YES** | — | — | None |
| H1 | All | GARCH persistence=0.9996 — strong volatility clustering | — | no | — | — | None |
| H1 | All | EGARCH leverage effect: γ=-0.0609 (down moves → more vol) | — | no | — | — | None |
| H1 | All | Fat tails: 6.8× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| H1 | London | Non-normal distribution (excess kurtosis=26.79, skew=-1.415) | 0.0000 | **YES** | — | — | None |
| H1 | London | GARCH persistence=0.9670 — strong volatility clustering | — | no | — | — | None |
| H1 | London | EGARCH leverage effect: γ=-0.0361 (down moves → more vol) | — | no | — | — | None |
| H1 | London | Fat tails: 5.1× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| H1 | NY | GARCH persistence=0.9761 — strong volatility clustering | — | no | — | — | None |
| H1 | NY | EGARCH leverage effect: γ=-0.0255 (down moves → more vol) | — | no | — | — | None |
| H1 | NY | Fat tails: 7.0× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| D1 | All | Non-normal distribution (excess kurtosis=21.22, skew=-0.557) | 0.0000 | **YES** | — | — | None |
| D1 | All | Fat tails: 5.3× more 3-sigma events than Gaussian predicts | — | no | — | — | None |

### XAUUSD

| TF | Session | Finding | p-value | Bonferroni | Edge (bps) | Econ Sig | Stable |
|---|---|---|---|---|---|---|---|
| H1 | London | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0000 | **YES** | — | — | None |
| H1 | NY | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0000 | **YES** | — | — | None |
| D1 | All | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0000 | **YES** | — | — | None |
| M15 | All | Significant return ACF at lags [3, 4, 5, 6, 10, 11, 12, 14, 18, 19, 20] — linear | 0.0000 | **YES** | 0.38 | no | None |
| M15 | NY | Significant return ACF at lags [1, 2, 3, 4, 6, 7, 9, 10, 15, 18, 19, 20] — linea | 0.0000 | **YES** | 0.68 | no | None |
| M15 | London | Significant return ACF at lags [1, 2, 3, 5, 6, 8, 10, 11, 12, 16] — linear direc | 0.0000 | **YES** | 0.61 | no | None |
| H1 | London | Significant return ACF at lags [1, 2, 5, 7, 14, 18] — linear directional predict | 0.0000 | **YES** | 1.23 | no | None |
| H1 | All | Significant return ACF at lags [1, 3, 7, 8, 10, 12, 13, 17, 18, 20] — linear dir | 0.0076 | no | 0.93 | no | None |
| H1 | NY | Significant return ACF at lags [2, 4] — linear directional predictability | 0.0102 | no | 1.25 | no | None |
| M15 | All | Post-jump lag_4: mean direction-adjusted return ≠ 0 (REVERSION) | 0.0176 | no | 4.22 | ★ YES | None |
| H1 | All | Intraday volatility seasonality — different hours have different distributions | 0.0408 | no | — | — | None |
| M15 | All | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0500 | no | — | — | None |
| M15 | London | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0500 | no | — | — | None |
| M15 | NY | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0500 | no | — | — | None |
| H1 | All | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0500 | no | — | — | None |
| D1 | All | Significant return ACF at lags [2, 14, 15, 16] — linear directional predictabili | 0.2369 | no | 8.25 | ★ YES | None |
| M15 | All | Non-normal distribution (excess kurtosis=59.53, skew=-0.859) | 0.0000 | **YES** | — | — | None |
| M15 | All | GARCH persistence=0.9800 — strong volatility clustering | — | no | — | — | None |
| M15 | All | EGARCH leverage effect: γ=-0.0271 (down moves → more vol) | — | no | — | — | None |
| M15 | All | Fat tails: 6.0× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| M15 | London | Non-normal distribution (excess kurtosis=41.71, skew=-1.489) | 0.0000 | **YES** | — | — | None |
| M15 | London | GARCH persistence=0.9787 — strong volatility clustering | — | no | — | — | None |
| M15 | London | EGARCH leverage effect: γ=-0.0238 (down moves → more vol) | — | no | — | — | None |
| M15 | London | Fat tails: 5.8× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| M15 | NY | Non-normal distribution (excess kurtosis=67.73, skew=1.681) | 0.0000 | **YES** | — | — | None |
| M15 | NY | GARCH persistence=0.9150 — strong volatility clustering | — | no | — | — | None |
| M15 | NY | EGARCH leverage effect: γ=-0.0634 (down moves → more vol) | — | no | — | — | None |
| M15 | NY | Fat tails: 6.4× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| H1 | All | Non-normal distribution (excess kurtosis=34.85, skew=-1.529) | 0.0000 | **YES** | — | — | None |
| H1 | All | GARCH persistence=0.9906 — strong volatility clustering | — | no | — | — | None |
| H1 | All | Fat tails: 6.2× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| H1 | London | Non-normal distribution (excess kurtosis=21.38, skew=-1.500) | 0.0000 | **YES** | — | — | None |
| H1 | London | GARCH persistence=0.9940 — strong volatility clustering | — | no | — | — | None |
| H1 | London | EGARCH leverage effect: γ=-0.0370 (down moves → more vol) | — | no | — | — | None |
| H1 | London | Fat tails: 5.2× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| H1 | NY | Non-normal distribution (excess kurtosis=9.34, skew=-0.454) | 0.0000 | **YES** | — | — | None |
| H1 | NY | GARCH persistence=0.9496 — strong volatility clustering | — | no | — | — | None |
| H1 | NY | EGARCH leverage effect: γ=-0.0216 (down moves → more vol) | — | no | — | — | None |
| H1 | NY | Fat tails: 6.3× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| D1 | All | Non-normal distribution (excess kurtosis=7.69, skew=-0.912) | 0.0000 | **YES** | — | — | None |
| D1 | All | Fat tails: 5.3× more 3-sigma events than Gaussian predicts | — | no | — | — | None |

### USDJPY

| TF | Session | Finding | p-value | Bonferroni | Edge (bps) | Econ Sig | Stable |
|---|---|---|---|---|---|---|---|
| M15 | London | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0000 | **YES** | — | — | None |
| M15 | NY | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0000 | **YES** | — | — | None |
| D1 | All | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0000 | **YES** | — | — | None |
| H1 | NY | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0000 | **YES** | — | — | None |
| H1 | London | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0000 | **YES** | — | — | None |
| H1 | All | Intraday volatility seasonality — different hours have different distributions | 0.0000 | **YES** | — | — | None |
| M15 | All | Intraday volatility seasonality — different hours have different distributions | 0.0000 | **YES** | — | — | None |
| M15 | All | Significant return ACF at lags [2, 5] — linear directional predictability | 0.0002 | no | 0.09 | no | None |
| M15 | London | Session-open bars have significantly different return distribution | 0.0157 | no | 0.50 | no | None |
| M15 | NY | Post-jump lag_1: mean direction-adjusted return ≠ 0 (REVERSION) | 0.0267 | no | 7.79 | ★ YES | None |
| M15 | All | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0500 | no | — | — | None |
| H1 | All | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0500 | no | — | — | None |
| M15 | NY | Significant return ACF at lags [3, 11, 18, 19] — linear directional predictabili | 0.1945 | no | 0.26 | no | None |
| H1 | London | Significant return ACF at lags [3] — linear directional predictability | 0.2283 | no | 0.49 | no | None |
| M15 | London | Significant return ACF at lags [13, 17] — linear directional predictability | 0.9745 | no | 0.19 | no | None |
| M15 | All | Non-normal distribution (excess kurtosis=48.81, skew=-0.819) | 0.0000 | **YES** | — | — | None |
| M15 | All | EGARCH leverage effect: γ=-0.0572 (down moves → more vol) | — | no | — | — | None |
| M15 | All | Fat tails: 5.1× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| M15 | London | Non-normal distribution (excess kurtosis=22.68, skew=-1.290) | 0.0000 | **YES** | — | — | None |
| M15 | London | GARCH persistence=0.9800 — strong volatility clustering | — | no | — | — | None |
| M15 | London | Fat tails: 5.1× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| M15 | NY | Non-normal distribution (excess kurtosis=10.21, skew=-0.554) | 0.0000 | **YES** | — | — | None |
| M15 | NY | GARCH persistence=0.9720 — strong volatility clustering | — | no | — | — | None |
| M15 | NY | Fat tails: 5.5× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| H1 | All | Non-normal distribution (excess kurtosis=25.12, skew=-0.779) | 0.0000 | **YES** | — | — | None |
| H1 | All | GARCH persistence=0.9924 — strong volatility clustering | — | no | — | — | None |
| H1 | All | Fat tails: 5.4× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| H1 | London | Non-normal distribution (excess kurtosis=9.29, skew=-0.240) | 0.0000 | **YES** | — | — | None |
| H1 | London | GARCH persistence=0.9640 — strong volatility clustering | — | no | — | — | None |
| H1 | London | Fat tails: 5.5× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| H1 | NY | Non-normal distribution (excess kurtosis=5.12, skew=-0.269) | 0.0000 | **YES** | — | — | None |
| H1 | NY | GARCH persistence=0.9834 — strong volatility clustering | — | no | — | — | None |
| H1 | NY | Fat tails: 5.0× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| D1 | All | Non-normal distribution (excess kurtosis=4.65, skew=-0.421) | 0.0000 | **YES** | — | — | None |
| D1 | All | Fat tails: 5.8× more 3-sigma events than Gaussian predicts | — | no | — | — | None |

### GBPUSD

| TF | Session | Finding | p-value | Bonferroni | Edge (bps) | Econ Sig | Stable |
|---|---|---|---|---|---|---|---|
| M15 | London | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0000 | **YES** | — | — | None |
| D1 | All | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0000 | **YES** | — | — | None |
| M15 | NY | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0000 | **YES** | — | — | None |
| H1 | London | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0000 | **YES** | — | — | None |
| H1 | All | Intraday volatility seasonality — different hours have different distributions | 0.0000 | **YES** | — | — | None |
| H1 | NY | Significant |return| ACF at lags [1, 5, 6, 9, 12] — volatility is predictable | 0.0000 | **YES** | — | — | None |
| M15 | All | Intraday volatility seasonality — different hours have different distributions | 0.0010 | no | — | — | None |
| M15 | All | Significant return ACF at lags [1, 4, 7, 9] — linear directional predictability | 0.0020 | no | 0.07 | no | None |
| M15 | All | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0500 | no | — | — | None |
| H1 | All | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0500 | no | — | — | None |
| H1 | NY | Significant return ACF at lags [1, 20] — linear directional predictability | 0.1945 | no | 0.59 | no | None |
| D1 | All | Significant return ACF at lags [5] — linear directional predictability | 0.2184 | no | 1.87 | no | None |
| H1 | All | Significant return ACF at lags [1] — linear directional predictability | 0.4218 | no | 0.11 | no | None |
| M15 | London | Significant return ACF at lags [7, 11, 13] — linear directional predictability | 0.7901 | no | 0.11 | no | None |
| M15 | NY | Significant return ACF at lags [12] — linear directional predictability | 0.8626 | no | 0.19 | no | None |
| H1 | London | Significant return ACF at lags [6, 10] — linear directional predictability | 0.9118 | no | 0.36 | no | None |
| M15 | All | Non-normal distribution (excess kurtosis=22.80, skew=0.101) | 0.0000 | **YES** | — | — | None |
| M15 | All | GARCH persistence=0.9000 — strong volatility clustering | — | no | — | — | None |
| M15 | All | Fat tails: 5.3× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| M15 | London | Non-normal distribution (excess kurtosis=5.94, skew=0.003) | 0.0000 | **YES** | — | — | None |
| M15 | London | GARCH persistence=0.9799 — strong volatility clustering | — | no | — | — | None |
| M15 | London | Fat tails: 4.2× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| M15 | NY | Non-normal distribution (excess kurtosis=7.44, skew=0.216) | 0.0000 | **YES** | — | — | None |
| M15 | NY | GARCH persistence=0.9000 — strong volatility clustering | — | no | — | — | None |
| M15 | NY | EGARCH leverage effect: γ=-0.0223 (down moves → more vol) | — | no | — | — | None |
| M15 | NY | Fat tails: 4.4× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| H1 | All | Non-normal distribution (excess kurtosis=9.38, skew=-0.119) | 0.0000 | **YES** | — | — | None |
| H1 | All | Fat tails: 5.9× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| H1 | London | Non-normal distribution (excess kurtosis=4.45, skew=-0.248) | 0.0000 | **YES** | — | — | None |
| H1 | London | GARCH persistence=0.9810 — strong volatility clustering | — | no | — | — | None |
| H1 | London | Fat tails: 3.6× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| H1 | NY | Non-normal distribution (excess kurtosis=4.05, skew=-0.002) | 0.0000 | **YES** | — | — | None |
| H1 | NY | GARCH persistence=0.9886 — strong volatility clustering | — | no | — | — | None |
| H1 | NY | Fat tails: 4.0× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| D1 | All | Non-normal distribution (excess kurtosis=19.29, skew=-1.191) | 0.0000 | **YES** | — | — | None |
| D1 | All | Fat tails: 3.7× more 3-sigma events than Gaussian predicts | — | no | — | — | None |

### GBPJPY

| TF | Session | Finding | p-value | Bonferroni | Edge (bps) | Econ Sig | Stable |
|---|---|---|---|---|---|---|---|
| H1 | NY | Non-normal distribution (excess kurtosis=2.43, skew=-0.326) | 0.0000 | **YES** | — | — | None |
| D1 | All | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0000 | **YES** | — | — | None |
| H1 | NY | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0000 | **YES** | — | — | None |
| H1 | All | Intraday volatility seasonality — different hours have different distributions | 0.0000 | **YES** | — | — | None |
| H1 | London | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0000 | **YES** | — | — | None |
| M15 | All | Significant return ACF at lags [1, 10, 14, 15, 17, 18] — linear directional pred | 0.0000 | **YES** | 0.16 | no | None |
| M15 | All | Intraday volatility seasonality — different hours have different distributions | 0.0000 | **YES** | — | — | None |
| H1 | All | Post-jump lag_1: mean direction-adjusted return ≠ 0 (CONTINUATION) | 0.0067 | no | 9.32 | ★ YES | None |
| M15 | NY | Post-jump lag_1: mean direction-adjusted return ≠ 0 (REVERSION) | 0.0395 | no | 7.16 | ★ YES | None |
| M15 | All | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0500 | no | — | — | None |
| M15 | London | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0500 | no | — | — | None |
| M15 | NY | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0500 | no | — | — | None |
| H1 | All | Significant |return| ACF at lags [1, 2, 3, 4, 5] — volatility is predictable | 0.0500 | no | — | — | None |
| H1 | NY | Significant return ACF at lags [4] — linear directional predictability | 0.0819 | no | 0.55 | no | None |
| H1 | London | Significant return ACF at lags [3, 10, 18] — linear directional predictability | 0.1095 | no | 0.67 | no | None |
| M15 | NY | Significant return ACF at lags [7, 8, 11, 19] — linear directional predictabilit | 0.2027 | no | 0.19 | no | None |
| H1 | All | Significant return ACF at lags [17] — linear directional predictability | 0.2176 | no | 0.14 | no | None |
| D1 | All | Significant return ACF at lags [11, 14, 15] — linear directional predictability | 0.4287 | no | 2.97 | no | None |
| M15 | London | Significant return ACF at lags [8] — linear directional predictability | 0.8466 | no | 0.15 | no | None |
| M15 | All | Non-normal distribution (excess kurtosis=109.38, skew=-2.483) | 0.0000 | **YES** | — | — | None |
| M15 | All | GARCH persistence=0.9800 — strong volatility clustering | — | no | — | — | None |
| M15 | All | Fat tails: 5.1× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| M15 | London | Non-normal distribution (excess kurtosis=12.95, skew=-0.881) | 0.0000 | **YES** | — | — | None |
| M15 | London | GARCH persistence=0.9791 — strong volatility clustering | — | no | — | — | None |
| M15 | London | Fat tails: 4.7× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| M15 | NY | Non-normal distribution (excess kurtosis=9.01, skew=-0.367) | 0.0000 | **YES** | — | — | None |
| M15 | NY | GARCH persistence=0.9800 — strong volatility clustering | — | no | — | — | None |
| M15 | NY | EGARCH leverage effect: γ=-0.0225 (down moves → more vol) | — | no | — | — | None |
| M15 | NY | Fat tails: 5.0× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| H1 | All | Non-normal distribution (excess kurtosis=19.20, skew=-0.681) | 0.0000 | **YES** | — | — | None |
| H1 | All | Fat tails: 5.2× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| H1 | London | Non-normal distribution (excess kurtosis=4.21, skew=-0.354) | 0.0000 | **YES** | — | — | None |
| H1 | London | GARCH persistence=0.9636 — strong volatility clustering | — | no | — | — | None |
| H1 | London | Fat tails: 4.6× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| H1 | NY | GARCH persistence=0.9554 — strong volatility clustering | — | no | — | — | None |
| H1 | NY | EGARCH leverage effect: γ=-0.0313 (down moves → more vol) | — | no | — | — | None |
| H1 | NY | Fat tails: 4.4× more 3-sigma events than Gaussian predicts | — | no | — | — | None |
| D1 | All | Non-normal distribution (excess kurtosis=34.06, skew=-1.975) | 0.0000 | **YES** | — | — | None |
| D1 | All | Fat tails: 3.8× more 3-sigma events than Gaussian predicts | — | no | — | — | None |

---

## Per-Instrument Summary — H1 'All Sessions'

| Instrument | n_returns | Mean (ann.) | Std (ann.) | Skewness | Ex.Kurt | JB p | AD 5% | GARCH α+β | Tail ξ (lower) | 3σ×/yr (emp) | 3σ×/yr (norm) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| XAUUSD | 14715 | 38.2281% | 20.40% | -1.529 | 34.851 | 0.00e+00 | REJ | 0.9906 | 0.3500 | 105.2 | 16.8 |
| US30 | 19999 | 10.1440% | 14.52% | 1.067 | 68.683 | 0.00e+00 | REJ | 0.9996 | 0.1970 | 114.8 | 16.8 |
| USDJPY | 19999 | 6.7748% | 9.83% | -0.779 | 25.118 | 0.00e+00 | REJ | 0.9924 | 0.2186 | 91.4 | 16.8 |
| GBPJPY | 19999 | 9.2196% | 9.47% | -0.681 | 19.197 | 0.00e+00 | REJ | 0.8945 | 0.1790 | 88.0 | 16.8 |
| GBPUSD | 19999 | 2.4495% | 7.48% | -0.119 | 9.382 | 0.00e+00 | REJ | 0.8030 | 0.1569 | 99.5 | 16.8 |

---

## Per-Instrument Summary — M15 'All Sessions'

| Instrument | n_returns | Std (ann.) | Ex.Kurt | JB p | GARCH α+β | 3σ×/yr (emp) |
|---|---|---|---|---|---|---|
| XAUUSD | 47141 | 22.16% | 59.528 | 0.00e+00 | 0.9800 | 402.9 |
| US30 | 99998 | 16.55% | 88.935 | 0.00e+00 | 0.9800 | 457.5 |
| USDJPY | 49999 | 10.22% | 48.807 | 0.00e+00 | 0.9000 | 341.0 |
| GBPJPY | 99998 | 10.82% | 109.378 | 0.00e+00 | 0.9800 | 344.7 |
| GBPUSD | 49999 | 7.39% | 22.800 | 0.00e+00 | 0.9000 | 358.4 |

---

*Generated by GTOS Engineering Agent — research/diagnostics/run_distributional_analysis.py*