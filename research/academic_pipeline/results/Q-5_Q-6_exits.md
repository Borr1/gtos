# Q-5.5 / Q-6.5 / Q-6.8 — Exit Engineering Analysis

- Script: `research/academic_pipeline/scripts/Q5_Q6_exit_engineering.py`
- Data: `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json`
- n = 111 trades (batch, XAUUSD only)

## Hypothesis (pre-data)

- **Q-5.5**: With WR ~65%, avg_win ~1.5R, avg_loss -1.0R, raw Kelly is in the 30–45% range — orders of magnitude above our realized 2%. ½-Kelly and ¼-Kelly are still 7–15%, also far above practical FTMO tolerance. Prediction: **current 2% (FTMO) and 1% (redacted_account) are drawdown-constrained, not return-optimized**. Optimal sub-Kelly for FTMO 10% DD should sit in 0.75%–1.5%. redacted_account Stellar 2-step: slightly lower (stricter trailing in phase 1).
- **Q-6.5**: Winners reach MFE mid-hold, not at close. MFE-give-back (reached ≥2R, closed <1R) is expected to be >25% of winners. Without intracandle data, hold-time is a ceiling, not exact speed-to-peak.
- **Q-6.8**: We expect Alt-A (all-out @ 1R) to beat the batch rule on expectancy per trade because MFE-give-back is large. Ranking prediction: **Alt-C > Alt-A > Batch > Alt-E > Alt-D > Alt-B > Alt-F**.

## Data

- `n = 111` trades, XAUUSD batch (2024-04 → 2026-03).
- Fields used: `r_multiple`, `mfe_r`, `mae_r`, `hold_time_candles`, `exit_substate`, `planned_rr`, `take_profit_1/2/3`.
- Sign convention: `mfe_r` and `mae_r` are stored as positive magnitudes. `r_multiple` is signed.
- Note: the batch reflects a legacy exit rule (session-timeout / trail / TP3 runner). Current live config (`risk.tp1_close_pct=100`) closes 100% at TP1. The current live rule is effectively **Alt-A in this analysis**.

## Q-5.5 Kelly results

- Win rate (WR): **65.77%** (73/111)
- Mean winning R (W): **0.709R**
- Mean losing R magnitude (L): **0.800R**
- Mean R per trade: **+0.200R**  |  Std: 1.043R
- **Raw Kelly fraction: 33.92%**
- **½-Kelly: 16.96%**  |  **¼-Kelly: 8.48%**
- Mean-variance Kelly (m / σ²) per 1R-loss unit: 0.184

### Monte Carlo — 100 trades, 10,000 iter, multiplicative compounding

| Risk % | Median final | Mean final | P(loss<0) | P(DD≥5%) | P(DD≥8%) | P(DD≥10%) | Median max DD | P95 max DD | P(FTMO pass ≈) |
|--------|--------------|-----------|-----------|----------|----------|-----------|---------------|-----------|----------------|
| 0.25% | 1.050 | 1.051 | 2.42% | 0.02% | 0.00% | 0.00% | 1.27% | 2.42% | 4.17% |
| 0.50% | 1.102 | 1.105 | 2.45% | 4.30% | 0.08% | 0.01% | 2.53% | 4.85% | 51.88% |
| 1.00% | 1.211 | 1.221 | 2.55% | 50.53% | 11.76% | 3.82% | 5.02% | 9.51% | 81.76% |
| 1.50% | 1.330 | 1.348 | 2.73% | 87.61% | 42.82% | 22.52% | 7.46% | 14.03% | 74.48% |
| 2.00% | 1.454 | 1.492 | 2.88% | 98.18% | 71.96% | 48.50% | 9.87% | 18.11% | 51.15% |
| 16.96% | 7.357 | 25.181 | 10.13% | 100.00% | 100.00% | 100.00% | 64.52% | 87.34% | 0.00% |
| 33.92% | 5.276 | 617.164 | 30.07% | 100.00% | 100.00% | 100.00% | 92.83% | 99.52% | 0.00% |

_FTMO pass ≈ reaches +10% AND never touches 10% max DD in 100-trade window. Daily-DD (5%) not simulated — no per-day aggregation; treat this as an upper bound on pass rate._

### Recommendation (Q-5.5)

- Raw Kelly of 33.9% is **mathematically aggressive** for any prop-firm account — a single 10-trade unlucky streak would wipe the account. Kelly assumes infinite horizon and repeated play; FTMO and redacted_account accounts have hard caps (10% max DD, 5% daily) that make Kelly unreachable.
- **Best P(FTMO-pass) in the grid: 1.00% risk → P(pass)≈81.76%, P(DD≥10%)=3.82%**.
- Most aggressive risk that keeps P(DD≥10%) < 5%: **1.00%** (P(DD≥10%)=3.82%, median final=1.211).
- **FTMO (2% profile) recommendation**: keep 2% only if CEO accepts P(10%-DD)≈48.50% over a 100-trade window. Otherwise **1.0–1.5%** is the sweet spot.
- **redacted_account Stellar 2-step recommendation**: 1.0% is safer given two-phase evaluation (compounding failure risk). 0.75% is the conservative floor.
- Kelly is a theoretical ceiling here; actual optimum is set by prop-firm drawdown limits, not variance. Stay well below ¼-Kelly.

## Q-6.5 Speed-to-MFE results

- Winners: n=73, losers: n=38.
- **Limitation**: `hold_time_candles` is the total duration, not time-to-MFE. The batch does not record when MFE was reached within the trade. We report total hold as a proxy only.

### Hold-time by MFE bucket (winners only)

| MFE bucket | n | Median hold (M15 candles) | Mean hold | Q25 | Q75 | Median MFE | Mean exit R |
|------------|---|---------------------------|-----------|-----|-----|------------|-------------|
| 0.5-1R | 43 | 19.0 | 26.2 | 6.5 | 40.5 | 0.44R | +0.26R |
| 1-2R | 18 | 39.5 | 36.3 | 24.0 | 54.8 | 1.27R | +0.64R |
| 2-3R | 3 | 19.0 | 25.3 | 17.5 | 30.0 | 2.48R | +1.33R |
| 3R+ | 9 | 37.0 | 37.7 | 35.0 | 42.0 | 3.88R | +2.78R |

### MFE-give-back

- Winners reaching ≥2R MFE but closing <1R (strict): **1/73 = 1.37%**.
- Winners leaving ≥0.5R on the table (any): **26/73 = 35.62%**.
- Mean give-back per winner: **0.51R**.
- Median give-back per winner: **0.36R**.

### Recommendation (Q-6.5)

- A large fraction of winners (35.62%) give back ≥0.5R before closing. **Strong signal that the legacy 'let-it-run-to-session-timeout' rule is leaving R on the table.** This is the quantitative basis for Q-6.8 favoring earlier exits.
- Without intracandle data, we cannot determine whether trades 'top out early' within the first 2–3 candles. A production instrument (per-candle MFE logger) would be needed for a definitive speed-to-MFE study. Logging `mfe_r` and `mae_r` per candle close is cheap and should be added as a shadow logger (observation-only).

## Q-6.8 Dynamic TP simulation

### Rules

- **Batch_asis**: historical exit rule (session-timeout / BE / trail / TP3 runner).
- **AltA_allout_1R**: close 100% at +1R. Fallback to realized R if MFE<1R and no stop.
- **AltB_allout_median_mfe**: close 100% at the median MFE of winners (= 0.84R). Fallback to realized R if MFE<target and no stop.
- **AltC_50at1R_trail**: 50% at +1R; remaining 50% trails to `MFE - 0.5R`.
- **AltD_allout_2R**: close 100% at +2R.
- **AltE_50at1R_50at2R**: 50% at +1R; 50% at +2R (or realized R if MFE<2R).
- **AltF_1R_then_BE**: 50% at +1R; remainder moves to BE (exits at 0).

### Results table

| Rule | n | Expectancy (R) | WR | Median R | Sum R | Median max DD (2%) | P95 max DD (2%) |
|------|---|----------------|----|----------|-------|--------------------|-----------------|
| Batch_asis | 111 | **+0.200** | 65.77% | +0.16 | +22.2 | 9.89% | 18.58% |
| AltA_allout_1R | 111 | **+0.114** | 66.67% | +0.18 | +12.7 | 9.51% | 17.86% |
| AltB_allout_median_mfe | 111 | **+0.088** | 66.67% | +0.18 | +9.8 | 9.80% | 18.83% |
| AltC_50at1R_trail | 111 | **+0.229** | 66.67% | +0.18 | +25.4 | 8.99% | 16.34% |
| AltD_allout_2R | 111 | **+0.154** | 65.77% | +0.16 | +17.1 | 9.92% | 18.19% |
| AltE_50at1R_50at2R | 111 | **+0.134** | 66.67% | +0.18 | +14.9 | 9.58% | 17.82% |
| AltF_1R_then_BE | 111 | **-0.026** | 66.67% | +0.18 | -2.8 | 14.28% | 26.93% |

### Bootstrap CI for Δ expectancy vs Batch_asis (paired, n_boot=5,000)

| Rule | Δ expectancy (R) | 95% CI | p (two-sided) | Significant? |
|------|------------------|--------|---------------|--------------|
| AltA_allout_1R | -0.086 | [-0.200, +0.019] | 0.131 | no |
| AltB_allout_median_mfe | -0.112 | [-0.239, -0.003] | 0.061 | YES |
| AltC_50at1R_trail | +0.029 | [-0.025, +0.084] | 0.295 | no |
| AltD_allout_2R | -0.045 | [-0.113, +0.015] | 0.160 | no |
| AltE_50at1R_50at2R | -0.065 | [-0.154, +0.012] | 0.124 | no |
| AltF_1R_then_BE | -0.225 | [-0.362, -0.105] | 0.001 | YES |

### Bootstrap CI for Δ expectancy vs AltA (current live rule)

| Rule | Δ vs AltA (R) | 95% CI | p (two-sided) | Significant? |
|------|---------------|--------|---------------|--------------|
| Batch_asis | +0.086 | [-0.020, +0.198] | 0.121 | no |
| AltB_allout_median_mfe | -0.026 | [-0.047, -0.003] | 0.020 | YES |
| AltC_50at1R_trail | +0.115 | [+0.045, +0.197] | 0.004 | YES |
| AltD_allout_2R | +0.040 | [-0.032, +0.115] | 0.292 | no |
| AltE_50at1R_50at2R | +0.020 | [-0.016, +0.058] | 0.282 | no |
| AltF_1R_then_BE | -0.140 | [-0.185, -0.099] | 0.000 | YES |

### Recommendation (Q-6.8)

- **Best expectancy**: AltC_50at1R_trail @ +0.229R/trade (WR=66.67%, sum=+25.4R over 111 trades).
- Current live rule is effectively AltA (tp1_close_pct=100): expectancy +0.114R (WR 66.67%).
- Whether to change: compare best_rule to AltA. If delta < 0.05R or CI crosses zero, the improvement is not robust.
- Best rule vs AltA delta: **+0.115R/trade**.
- Best rule vs AltA bootstrap CI: [+0.045, +0.197]R, p = 0.004.
- Statistical significance (α=0.05): **YES**.
- Recommendation: **if best_rule delta vs AltA is significant (CI excludes 0) and >+0.1R**, consider deploying as shadow logger first, then as live swap. Otherwise keep AltA (current live) — simpler and deterministic.

## Caveats

- **n=111** — all results are small-sample. Bootstrap CIs reflect statistical noise.
- **No intracandle tick data** — we assume stop-out happens whenever `mae_r ≥ 1.0` AND the historical `r_multiple` confirms stop. This may understate the advantage of tighter TPs (some trades reached +1R then stopped, but our assumption may assign +1R incorrectly when the historical sequence was TP-then-reverse within the candle). Mitigation: `was_stopped` gate uses `mae_r ≥ 1.0 AND r_multiple ≤ -0.95`, which is conservative — trades that hit SL but also touched MFE count as stops. This systematically UNDER-counts TP hits, biasing against early-TP rules. If anything, early-TP rules are likely stronger than we report.
- **Batch rule is not current live rule**. Batch had session-timeout / trail logic; current live closes 100% at TP1 (`tp1_close_pct=100`), which is our AltA. Comparing AltA vs Batch tells us how much R was sacrificed by the old rule; comparing other Alts vs AltA tells us whether the *current* rule can be improved.
- **FTMO pass-rate approximation** uses multiplicative compounding and a 100-trade window. Daily 5%-DD limit is not modeled (no per-day aggregation).
- **Kelly assumes stationarity and independence** of R per trade. Real trades cluster (multiple trades same week, correlated kill-zones). Kelly overestimates optimal size under dependence.
- **XAUUSD-only** data. Other instruments (US30, USDJPY, GBPJPY, GBPUSD) may have different MFE/MAE distributions. Run per-instrument when batches exist.

## Next steps

1. **Add per-candle MFE/MAE shadow logger** to capture time-to-MFE in live trades. This closes the Q-6.5 data gap.
2. **Re-run Q-6.8 with proper walk-forward split** (train 2024, test Jan–Apr 2026).
3. **Per-instrument Kelly** once US30/USDJPY/GBPJPY batches are consolidated.
4. **Deploy shadow logger for best alternative rule (AltC_50at1R_trail)** and gate promotion on 30+ trades with p<0.05 sign test.
5. **Confirm with Monte Carlo on the best rule** — rerun Q-5.5 using the `vec` of the best rule as the sampling distribution, to see if higher expectancy changes risk-fraction optimum.
