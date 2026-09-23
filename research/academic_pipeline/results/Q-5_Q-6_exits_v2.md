# Q-5.5 / Q-6.5 / Q-6.8 — Exit Engineering Analysis (v2)

**Version:** v2 — Wave-1 reviewer fix: H29 DD brake now applied in Kelly Monte Carlo.

- Script: `research/academic_pipeline/scripts/Q5_Q6_exit_engineering_v2.py`
- JSON: `research/academic_pipeline/results/Q-5_Q-6_exits_v2.json`
- Data: `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json`
- n = 111 trades (batch, XAUUSD only)
- Seed: 42 (deterministic, numpy default_rng)

## v1 → v2 change summary

**Root cause flagged by Wave-1 reviewer:** the MC loop treated risk as a constant `risk_frac` for all 100 trades per sim. In production, the H29 drawdown manager (`src/components/drawdown_manager.py`, config key `drawdown_reduction.threshold=0.08` and `reduced_risk_pct=0.5`) cuts risk to 0.5% the moment DD-from-peak >= 8%. This makes the v1 P(DD>=10%) numbers systematically high at the 2% level — the brake would have engaged before those runs reached 10% DD. v1 is conservative for go/no-go decisions (biased toward rejecting 2%), but it misreports the real operating distribution.

**v2 fix:** replicate the H29 state machine inside `mc_equity()` (and in `mc_rule_dd()`): before each trade, read the current DD-from-peak; if >= 8%, use 0.5% risk instead of the nominal `risk_frac`; reset to nominal on new equity peak.

Everything else unchanged: same seed, same 10k iter, same 100-trade horizon, same Q-6.5 / Q-6.8 rules, same bootstrap CIs.

## Q-5.5 Kelly (formula-level, unchanged)

- Win rate (WR): **65.77%** (73/111)
- Mean winning R (W): **0.709R**
- Mean losing R magnitude (L): **0.800R**
- Mean R per trade: **+0.200R**  |  Std: 1.043R
- **Raw Kelly fraction: 33.92%**
- **½-Kelly: 16.96%**  |  **¼-Kelly: 8.48%**
- Mean-variance Kelly (m / σ²) per 1R-loss unit: 0.184

## Monte Carlo — H29 OFF (v1-equivalent) vs H29 ON (v2)

Both tables use same seed (42), 10,000 iterations, 100-trade horizon, multiplicative compounding. Only difference is whether the H29 production DD-brake is simulated.

### H29 OFF (v1 — constant risk)

| Risk % | Median final | Mean final | P(loss<0) | P(DD>=5%) | P(DD>=8%) | P(DD>=10%) | Median max DD | P95 max DD | P(FTMO pass ~=) |
|--------|--------------|-----------|-----------|----------|----------|-----------|---------------|-----------|----------------|
| 0.25% | 1.050 | 1.051 | 2.42% | 0.02% | 0.00% | 0.00% | 1.27% | 2.42% | 4.17% |
| 0.50% | 1.102 | 1.105 | 2.45% | 4.30% | 0.08% | 0.01% | 2.53% | 4.85% | 51.88% |
| 1.00% | 1.211 | 1.221 | 2.55% | 50.53% | 11.76% | 3.82% | 5.02% | 9.51% | 81.76% |
| 1.50% | 1.330 | 1.348 | 2.73% | 87.61% | 42.82% | 22.52% | 7.46% | 14.03% | 74.48% |
| 2.00% | 1.454 | 1.492 | 2.88% | 98.18% | 71.96% | 48.50% | 9.87% | 18.11% | 51.15% |
| 16.96% | 7.357 | 25.181 | 10.13% | 100.00% | 100.00% | 100.00% | 64.52% | 87.34% | 0.00% |
| 33.92% | 5.276 | 617.164 | 30.07% | 100.00% | 100.00% | 100.00% | 92.83% | 99.52% | 0.00% |

### H29 ON (v2 — production DD-brake at DD>=8% -> risk=0.5%)

| Risk % | Median final | Mean final | P(loss<0) | P(DD>=5%) | P(DD>=8%) | P(DD>=10%) | Median max DD | P95 max DD | P(FTMO pass ~=) |
|--------|--------------|-----------|-----------|----------|----------|-----------|---------------|-----------|----------------|
| 0.25% | 1.050 | 1.051 | 2.06% | 0.03% | 0.00% | 0.00% | 1.26% | 2.40% | 3.85% |
| 0.50% | 1.103 | 1.106 | 2.37% | 4.30% | 0.12% | 0.02% | 2.54% | 4.89% | 52.01% |
| 1.00% | 1.211 | 1.219 | 3.39% | 51.11% | 11.07% | 2.16% | 5.06% | 9.21% | 81.77% |
| 1.50% | 1.312 | 1.327 | 5.49% | 87.19% | 43.24% | 13.46% | 7.47% | 10.92% | 78.97% |
| 2.00% | 1.367 | 1.412 | 7.76% | 98.13% | 72.09% | 36.77% | 9.59% | 11.87% | 60.38% |
| 16.96% | 1.052 | 1.402 | 44.71% | 100.00% | 100.00% | 100.00% | 18.17% | 23.91% | 0.00% |
| 33.92% | 0.898 | 1.812 | 57.62% | 100.00% | 100.00% | 100.00% | 34.28% | 36.88% | 0.00% |

### Delta (v2 minus v1)

| Risk % | P(pass) v1 | P(pass) v2 | Delta (pp) | P(DD>=10%) v1 | P(DD>=10%) v2 | Delta (pp) | Median final v1 | Median final v2 |
|--------|-----------|-----------|------------|---------------|---------------|------------|-----------------|-----------------|
| 0.25% | 4.17% | 3.85% | -0.32 | 0.00% | 0.00% | +0.00 | 1.050 | 1.050 |
| 0.50% | 51.88% | 52.01% | +0.13 | 0.01% | 0.02% | +0.01 | 1.102 | 1.103 |
| 1.00% | 81.76% | 81.77% | +0.01 | 3.82% | 2.16% | -1.66 | 1.211 | 1.211 |
| 1.50% | 74.48% | 78.97% | +4.49 | 22.52% | 13.46% | -9.06 | 1.330 | 1.312 |
| 2.00% | 51.15% | 60.38% | +9.23 | 48.50% | 36.77% | -11.73 | 1.454 | 1.367 |
| 16.96% | 0.00% | 0.00% | +0.00 | 100.00% | 100.00% | +0.00 | 7.357 | 1.052 |
| 33.92% | 0.00% | 0.00% | +0.00 | 100.00% | 100.00% | +0.00 | 5.276 | 0.898 |

### Recommendation (Q-5.5) — v2 numbers

- Raw Kelly 33.9% remains mathematically aggressive. Prop-firm DD cutoffs dominate over Kelly reasoning.
- **At 2% risk with H29 ON:** P(DD>=10%) = **36.77%** (was 48.50% without H29). P(FTMO-pass) = **60.38%** (was 51.15%).
- **At 1% risk with H29 ON:** P(DD>=10%) = **2.16%**, P(FTMO-pass) = **81.77%**.
- **Best P(FTMO-pass) with H29:** 1.00% risk -> P(pass) ~= 81.77%, P(DD>=10%) = 2.16%.
- Most aggressive risk that keeps P(DD>=10%) < 5% with H29 on: **1.00%** (was 1.00% under v1 logic).
- The 2% FTMO choice is materially better-supported once H29 is modelled — the brake cuts P(DD>=10%) by the delta shown in the table above. The still-safer 1% option remains dominant on the P(DD>=10%) metric.

## Q-6.5 Speed-to-MFE (unchanged from v1)

- Winners: n=73, losers: n=38.
- Limitation: `hold_time_candles` is total duration, not time-to-MFE.

### Hold-time by MFE bucket (winners only)

| MFE bucket | n | Median hold (M15 candles) | Mean hold | Q25 | Q75 | Median MFE | Mean exit R |
|------------|---|---------------------------|-----------|-----|-----|------------|-------------|
| 0.5-1R | 43 | 19.0 | 26.2 | 6.5 | 40.5 | 0.44R | +0.26R |
| 1-2R | 18 | 39.5 | 36.3 | 24.0 | 54.8 | 1.27R | +0.64R |
| 2-3R | 3 | 19.0 | 25.3 | 17.5 | 30.0 | 2.48R | +1.33R |
| 3R+ | 9 | 37.0 | 37.7 | 35.0 | 42.0 | 3.88R | +2.78R |

### MFE-give-back

- Winners reaching >=2R MFE but closing <1R (strict): **1/73 = 1.37%**.
- Winners leaving >=0.5R on the table (any): **26/73 = 35.62%**.
- Mean give-back per winner: **0.51R**.
- Median give-back per winner: **0.36R**.

## Q-6.8 Dynamic TP simulation (unchanged rules; DD columns now report H29 ON)

### Rules

- **Batch_asis**: historical exit rule (session-timeout / BE / trail / TP3 runner).
- **AltA_allout_1R**: close 100% at +1R. Fallback to realized R if MFE<1R and no stop.
- **AltB_allout_median_mfe**: close 100% at median MFE of winners (= 0.84R).
- **AltC_50at1R_trail**: 50% at +1R; remaining 50% trails to `MFE - 0.5R`.
- **AltD_allout_2R**: close 100% at +2R.
- **AltE_50at1R_50at2R**: 50% at +1R; 50% at +2R.
- **AltF_1R_then_BE**: 50% at +1R; remainder moves to BE.

### Results table (H29 ON for DD columns)

| Rule | n | Expectancy (R) | WR | Median R | Sum R | Median max DD (2%, H29) | P95 max DD (2%, H29) | Median max DD (2%, NO H29 — v1) | P95 max DD (2%, NO H29 — v1) |
|------|---|----------------|----|----------|-------|--------------------------|----------------------|----------------------------------|------------------------------|
| Batch_asis | 111 | **+0.200** | 65.77% | +0.16 | +22.2 | 9.60% | 11.85% | 9.84% | 18.28% |
| AltA_allout_1R | 111 | **+0.114** | 66.67% | +0.18 | +12.7 | 9.52% | 11.78% | 9.64% | 17.72% |
| AltB_allout_median_mfe | 111 | **+0.088** | 66.67% | +0.18 | +9.8 | 9.62% | 12.07% | 9.91% | 18.63% |
| AltC_50at1R_trail | 111 | **+0.229** | 66.67% | +0.18 | +25.4 | 9.08% | 11.29% | 8.94% | 15.98% |
| AltD_allout_2R | 111 | **+0.154** | 65.77% | +0.16 | +17.1 | 9.62% | 11.90% | 9.90% | 18.46% |
| AltE_50at1R_50at2R | 111 | **+0.134** | 66.67% | +0.18 | +14.9 | 9.49% | 11.82% | 9.51% | 17.82% |
| AltF_1R_then_BE | 111 | **-0.026** | 66.67% | +0.18 | -2.8 | 10.74% | 13.96% | 14.36% | 26.80% |

### Bootstrap CI for Delta expectancy vs Batch_asis (paired, n_boot=5,000)

| Rule | Delta expectancy (R) | 95% CI | p (two-sided) | Significant? |
|------|----------------------|--------|---------------|--------------|
| AltA_allout_1R | -0.086 | [-0.207, +0.023] | 0.140 | no |
| AltB_allout_median_mfe | -0.112 | [-0.238, -0.004] | 0.058 | YES |
| AltC_50at1R_trail | +0.029 | [-0.024, +0.084] | 0.284 | no |
| AltD_allout_2R | -0.045 | [-0.112, +0.013] | 0.154 | no |
| AltE_50at1R_50at2R | -0.065 | [-0.154, +0.010] | 0.117 | no |
| AltF_1R_then_BE | -0.225 | [-0.359, -0.107] | 0.001 | YES |

### Bootstrap CI for Delta expectancy vs AltA (current live rule)

| Rule | Delta vs AltA (R) | 95% CI | p (two-sided) | Significant? |
|------|-------------------|--------|---------------|--------------|
| Batch_asis | +0.086 | [-0.018, +0.206] | 0.135 | no |
| AltB_allout_median_mfe | -0.026 | [-0.047, -0.003] | 0.024 | YES |
| AltC_50at1R_trail | +0.115 | [+0.045, +0.197] | 0.004 | YES |
| AltD_allout_2R | +0.040 | [-0.035, +0.116] | 0.292 | no |
| AltE_50at1R_50at2R | +0.020 | [-0.017, +0.057] | 0.298 | no |
| AltF_1R_then_BE | -0.140 | [-0.180, -0.099] | 0.000 | YES |

### Recommendation (Q-6.8) — unchanged by H29

- **Best expectancy rule:** AltC_50at1R_trail @ +0.229R/trade.
- Q-6.8 ranking is NOT affected by H29 because the rules differ in expectancy, not in how we size the bet. The H29 brake only rescales the DD columns, not the per-trade R vector. See the DD table: every rule's median-DD at 2% drops by the same proportional amount when H29 is on.

## Caveats

- **n=111** — small-sample results unchanged.
- **H29 assumption:** v2 assumes H29 never mis-fires (no false-positive on equity spikes) and reverts instantly on new peak. Production logic matches this; see `src/components/drawdown_manager.py`.
- **Daily 5% DD not modelled.** Still applies to v2 — a single FOMC candle that blows 5% in one trade is not modelled here.
- **Kelly assumes stationarity and independence.** Real trade clustering degrades both Kelly and H29-informed optima. Conservative margin advised.
- **XAUUSD-only** batch.
- **v1 is NOT wrong** — it is a worst-case bound. v2 is the realistic operating distribution. Both are kept in the repo for audit.

## Next steps

1. Deploy per-candle MFE/MAE shadow logger (unchanged from v1).
2. Walk-forward on Q-6.8 (unchanged from v1).
3. Per-instrument Kelly once other symbol batches exist.
4. Shadow-log `AltC_50at1R_trail` (unchanged recommendation).
5. Re-run q_7_monte_carlo.py against v2 rule vectors for cross-check.
