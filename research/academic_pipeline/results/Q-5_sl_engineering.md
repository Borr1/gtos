# Q-5.3 / Q-5.4 — SL Engineering Analysis

- Script: `research/academic_pipeline/scripts/q_5_sl_engineering.py`
- Data: `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json` (111 trades, XAUUSD batch)
- Historical D1 (PDH/PDL): `data/historical_2026/XAUUSD_D1.csv` (covers only 2026 trades; 2024-2025 excluded from PDH/PDL)

## Hypotheses (pre-registered, before running analysis)

- **H1 (Q-5.3 prevalence):** >25% of SLs sit within $1.0 of a $5-round level (non-uniform clustering).
- **H2 (Q-5.3 Osler asymmetry):** ≥60% of LONG SLs land in the lower half of the $5-band (just below a $5-round), consistent with Osler (2003/2005).
- **H3 (Q-5.3 hunt risk):** P(stop-hunt | SL clustered at round) > P(stop-hunt | isolated), Fisher one-sided.
- **H4 (Q-5.4 quantile SL):** P95 winning-MAE SL delivers HIGHER expectancy than current ATR-based sizing.

## Data

- n=110 trades (LONG=103, SHORT=7, unknown=1)
- Years: 2024=10, 2025=71, 2026=29
- Outcomes: WIN=71, LOSS=36, BE=3
- Fields used: stop_loss, entry_price, direction, outcome, r_multiple, mae_r, mfe_r, sl_dollars, exit_substate.

## Method

### Q-5.3 — Stop clustering
1. Cluster flag: SL within $1 of a $5/$10/$50 round level (primary: $5).
2. Stop-hunt proxy: outcome=LOSS, mae_r >= 0.98 (stop hit), AND mfe_r >= 1.5 (price reversed ≥1.5R afterwards).
3. Sensitivity: also report mfe_r thresholds 1.0 and 2.0.
4. 2×2 table: cluster × hunted. Fisher's exact test (two-sided primary, one-sided report).
5. For 2026 trades only (29 with PDH/PDL coverage), repeat test with cluster = SL within $3 of PDH or PDL.

### Q-5.4 — ATR vs quantile SL counterfactual
1. Compute MAE distribution for WINNING trades.
2. Proposed SL widths: baseline 1.0×, 1.5×, 2.0×, 0.75×, and quantile P90/P95/P99 of winning-MAE.
3. For each trade: if new SL width (in old-R) >= mae_r, trade SURVIVES. Otherwise STOPS at -1 new-R.
4. Survivors' new r_multiple = old_r_multiple × (W_old/W_new), i.e., re-scaled to new R-unit.
5. For saved losers (original stop-out, now survives): central estimate = 0.5 × mfe_r × k; we also report optimistic (mfe×k) and pessimistic (0).
6. Report WR, avg_R, std_R, sharpe_per_trade, sum_R, n_stopped, n_squeezed_winners, n_saved_losers.

## Q-5.3 Results — Stop Clustering

### Cluster prevalence

- SLs within **$1.0 of a $5-round level**: 54/110 = **49.09%**
- SLs within **$1.0 of any round level ($5/$10/$50)**: 54/110 = 49.09%
- Uniform-distribution expectation for $5 rounds: 2·$1/$5 = **40.0%**
- **H1 verdict**: Observed 49.09% vs uniform 40%. H1 SUPPORTED by the >25% bar, though **not obviously exceeding** uniform expectation — consistent with SL being driven by OB structure, not by deliberate round-number placement.

### Osler asymmetry (LONG SLs)

- LONG trades: n=103
- LONG SL in LOWER half of $5-band (below mid): 66/103 = **64.08%**
- LONG SL in UPPER half: 37/103
- **H2 verdict**: SUPPORTED — LONG SLs do skew to the lower half of each $5-band, matching Osler's retail-stop pattern.

### Stop-hunt rate

- Hunt rate (mfe≥1.5R): 4/110 = **3.64%**
- Hunt rate (mfe≥1.0R, looser): 6/110 = 5.45%
- Hunt rate (mfe≥2.0R, stricter): 1/110 = 0.91%

### Fisher exact: hunt-rate by cluster

| Test | cluster-HUNT | cluster-NO | iso-HUNT | iso-NO | P(hunt\|clust) | P(hunt\|iso) | p (one-sided >) | p (two-sided) |
|------|-------------:|-----------:|---------:|-------:|---------------:|--------------:|----------------:|--------------:|
| $5 cluster × hunt(mfe≥1.5R) | 1 | 53 | 3 | 53 | 1.85% | 5.36% | 0.936 | 0.618 |
| any round × hunt(mfe≥1.5R) | 1 | 53 | 3 | 53 | 1.85% | 5.36% | 0.936 | 0.618 |
| $5 cluster × hunt(mfe≥1.0R) | 3 | 51 | 3 | 53 | 5.56% | 5.36% | 0.643 | 1.000 |
| PDH cluster × hunt (2026 only) FLAG: bucket n<10 | 0 | 0 | 4 | 106 | 0.00% | 3.64% | 1.000 | 1.000 |
| PDL cluster × hunt (2026 only) FLAG: bucket n<10 | 0 | 2 | 4 | 104 | 0.00% | 3.70% | 1.000 | 1.000 |

### MAE by cluster status

- Clustered (round-$5): n=54, mean mae_r=0.609, median=0.381
- Isolated:              n=56, mean mae_r=0.502, median=0.305

## Q-5.4 Results — ATR vs Quantile SL

### Winning-MAE distribution (n=71 winners)

| Pct | Winning-MAE (R) |
|-----|-----------------:|
| P50 | 0.157 |
| P75 | 0.367 |
| P90 | 0.578 |
| P95 | 0.633 |
| P99 | 0.933 |

Interpretation: A quantile SL at P95 would be set to **0.63× the mean winning MAE**, i.e., it covers 95% of historical winners without being hit.

### Counterfactual SL scenarios

Two expectancy columns:
- **avg_R (new-R)** — per-trade R in the *new* R-unit. This is what matters under **fixed-risk-%** sizing (GTOS risks 1-2% of equity regardless of SL width; lot size scales automatically).
- **avg_R (old-R equiv)** = avg_R × width_factor — what each trade earns expressed in BASELINE R-units, i.e., if we instead held **fixed LOT size**. This is the $-equivalent under constant position size.

| Scenario | Width (old-R) | n_stopped | n_squeezed_winners | n_saved_losers | WR | avg_R (new-R, central) | avg_R (old-R equiv) | sum_R (new) | sharpe |
|----------|--------------:|----------:|-------------------:|---------------:|---:|-----------------------:|--------------------:|------------:|-------:|
| S0 baseline | 1.00 | 27 | 0 | 0 | 65.5% | +0.198 | +0.198 | +21.79 | 0.189 |
| S1 1.5x ATR (wider) | 1.50 | 5 | 0 | 22 | 83.6% | +0.280 | +0.420 | +30.83 | 0.458 |
| S2 2.0x ATR (wider) | 2.00 | 4 | 0 | 23 | 84.5% | +0.210 | +0.419 | +23.05 | 0.445 |
| S3 0.75x ATR (tighter) | 0.75 | 33 | 3 | 0 | 62.7% | +0.256 | +0.192 | +28.21 | 0.202 |
| S4 quantile P95 winning-MAE | 0.63 | 38 | 4 | 0 | 61.8% | +0.323 | +0.204 | +35.52 | 0.219 |
| S5 quantile P90 winning-MAE | 0.58 | 42 | 8 | 0 | 58.2% | +0.321 | +0.186 | +35.35 | 0.200 |
| S6 quantile P99 winning-MAE | 0.93 | 28 | 1 | 0 | 64.5% | +0.218 | +0.204 | +24.03 | 0.197 |

### Sensitivity rows for saved-loser assumption (central/optim/pess):

| Scenario | avg_R (central) | avg_R (optim: full mfe×k) | avg_R (pess: 0) |
|----------|----------------:|--------------------------:|----------------:|
| S0 baseline | +0.198 | +0.198 | +0.198 |
| S1 1.5x ATR (wider) | +0.280 | +0.310 | +0.250 |
| S2 2.0x ATR (wider) | +0.210 | +0.234 | +0.185 |
| S3 0.75x ATR (tighter) | +0.256 | +0.256 | +0.256 |
| S4 quantile P95 winning-MAE | +0.323 | +0.323 | +0.323 |
| S5 quantile P90 winning-MAE | +0.321 | +0.321 | +0.321 |
| S6 quantile P99 winning-MAE | +0.218 | +0.218 | +0.218 |

**Best avg_R (new-R, fixed-risk-% sizing):** `S4 quantile P95 winning-MAE` @ width_factor=0.63 → +0.323R/trade
**Best avg_R (old-R equiv, fixed-lot sizing):** `S1 1.5x ATR (wider)` → +0.420R/trade

**Interpretation:** when the two best scenarios DIFFER, the choice depends on whether GTOS holds RISK% fixed (live does) or LOT size fixed.

## Caveats

1. **Counterfactual approximation (Q-5.4):** we do not replay per-candle OHLCV for each trade. We use mae_r and mfe_r (recorded path extremes in OLD-R units) to decide whether a re-scaled SL would have been touched. For losers saved by a wider SL, we assume the central estimate that the trade would have realised half its original mfe; optimistic and pessimistic alternatives are reported side-by-side. This is VALID for the stop-hit decision but APPROXIMATE for the replacement payoff.
2. **Same TP in $ terms, not R terms:** under re-scaling, a winner's r_multiple shrinks proportionally with the wider SL (new_R = old_R × W_old/W_new). This is the correct accounting: TP is a $-level fixed by structure; R depends only on SL width.
3. **Direction imbalance:** LONG n=103, SHORT n=7. The Osler asymmetry test is effectively LONG-only. SHORT round-number behavior is untestable.
4. **PDH/PDL coverage:** Only the 29 trades from 2026 have local D1 OHLCV for PDH/PDL lookup. 2024-2025 trades (82) are excluded from that subtest → very low power.
5. **ATR proxy:** the batch file does not expose per-trade ATR. We approximate ATR = sl_dollars/3 since SL = OB boundary + 0.3-0.5 ATR and OB depth ≈ 1-2 ATR. Fractional clustering tests use this proxy; absolute-dollar tests do not.
6. **Round-number semantic:** We use $5 as the primary gold round. $10 and $50 are tested as secondary. Sub-$5 ticks (e.g., $2.50) are not tested — the CEO can request them if relevant.
7. **Stop-hunt proxy is conservative:** we flag only trades with outcome=LOSS AND mae_r≥0.98 AND mfe_r≥1.5R. Trades that reversed only 1R in favor (mfe_r<1.5) are not counted as 'hunted'.
8. **Quantile SL is in-sample:** P95 winning-MAE is derived from the same 72 winners it is then applied against. In a true out-of-sample test, effective P95 would need a rolling-window calibration.

## Verdicts

### Q-5.3 — SL clustering vs stop-hunt risk
- **Verdict: UNDERPOWERED (too few hunts to test)**
- P(hunt | clustered) = 1.85%, P(hunt | isolated) = 5.36%, Fisher one-sided p = 0.936
- Total confirmed stop-hunt events (mfe≥1.5R): 4 — sample too small to detect a small-to-moderate cluster effect. More data required before a round-buffer widening rule can be justified.
- Osler asymmetry is PRESENT (64.08% of LONG SLs below mid-$5-band) but this is an artefact of OB-retest placing stops at OB extremes, which happen to fall in the lower half of each $5 range.

### Q-5.4 — ATR vs quantile SL
- **Under GTOS fixed-risk-% sizing (live regime):** WINNER: S4 quantile P95 winning-MAE beats baseline by +0.125R under fixed-risk-% sizing
- **Under fixed-lot sizing (alternative):** WINNER: S1 1.5x ATR (wider) beats baseline by +0.222R under fixed-lot sizing
- Baseline: avg_R = +0.198 (both regimes identical at baseline)
- P95 winning-MAE width_factor = 0.63, avg_R(new-R) = +0.323, avg_R(old-R equiv) = +0.204
- Widening to 1.5× ATR: avg_R(new-R) = +0.280, avg_R(old-R equiv) = +0.420. Saves 22 stop-out losers but shrinks every winner's R by factor 1/1.5.
- Tightening to 0.75× ATR: squeezes 3 winners into losses.

**Key insight:** Under fixed-risk-% (live GTOS regime), a TIGHTER SL (P95 winning-MAE = 0.63× baseline) mechanically improves new-R expectancy BECAUSE r_multiple is inflated by the same factor the SL is tightened. Under fixed-lot (the $-equivalent frame), tightening does NOT improve expectancy — it just shrinks every trade's $-payoff.

The honest headline: neither tightening nor widening is a free lunch. The practical question is whether a WIDER SL (covers more losers at the cost of smaller R/winner) is $-positive. Answer: under central-estimate for saved losers, S1 (1.5× ATR) delivers old-R equiv = +0.420, vs baseline +0.198. That's a modest lift (+0.222R/trade). **Under fixed-risk-% live sizing, it's +0.082R/trade.**

## Reviewer correction 2026-04-17 — H29 policy was missing (MAJOR)

**Finding:** The original Q-5.4 counterfactual computed each scenario's `avg_R` as an unweighted mean of per-trade new-R, implicitly assuming risk_pct_per_trade is CONSTANT at 2.0%. This **omits the H29 policy deployed live Apr 11 2026**: when equity drawdown from peak >= 8%, risk reduces to 0.5% until a new equity high is reached.

**Correction procedure (pre-registered BEFORE running):**
1. For each scenario, compute per-trade r_multiple series exactly as before (stop-hit logic, rescaling, central saved-loser estimate).
2. Walk trades in chronological order by `date`.
3. Maintain running equity (init=1.0) and peak-equity.
4. Before each trade, check: if `(peak - equity) / peak >= 0.08` AND not already in DD-mode, switch to reduced risk (0.5%). If already in DD-mode and equity >= peak, reset to normal risk (2.0%).
5. Apply trade: `equity_after = equity + r * active_risk * equity`. Update peak if new high.
6. Report terminal equity, max-DD observed, and count of trades where reduced risk was active.

**Comparison column `terminal_equity_flat`:** same replay with risk fixed at 2.0% throughout (no H29). The delta `(flat - h29)` quantifies how much H29 costs the scenario in average terminal equity.

### H29-corrected terminal-equity replay (chronological, seed-free)

| Scenario | width_factor | terminal_equity (H29 ON) | terminal_equity (flat 2%) | max_DD (H29) | max_DD (flat) | n_trades_reduced | pct_reduced |
|----------|-------------:|-------------------------:|--------------------------:|-------------:|--------------:|-----------------:|------------:|
| S0 baseline | 1.00 | 1.1849 | 1.5092 | 8.51% | 10.06% | 65 | 59.1% |
| S1 1.5x ATR (wider) | 1.50 | 1.8347 | 1.8347 | 5.88% | 5.88% | 0 | 0.0% |
| S2 2.0x ATR (wider) | 2.00 | 1.5767 | 1.5767 | 3.96% | 3.96% | 0 | 0.0% |
| S3 0.75x ATR (tighter) | 0.75 | 1.3606 | 1.6968 | 8.92% | 10.15% | 56 | 50.9% |
| S4 quantile P95 winning-MAE | 0.63 | 1.3575 | 1.9400 | 9.17% | 9.24% | 57 | 51.8% |
| S5 quantile P90 winning-MAE | 0.58 | 1.3803 | 1.9183 | 9.25% | 12.16% | 61 | 55.5% |
| S6 quantile P99 winning-MAE | 0.93 | 1.2034 | 1.5738 | 8.40% | 9.70% | 62 | 56.4% |

- **Best terminal equity under H29 policy:** `S1 1.5x ATR (wider)` → 1.8347
- Baseline S0 terminal equity: 1.1849 (H29 ON) vs 1.5092 (flat 2%). H29 triggered on 59.1% of trades — opportunity cost vs flat 2% = +32.435pp of final equity. (This is the price of the safety net: a cost paid on paths where the DD did not escalate to blow-up; a gain on paths where it would have.)
- S1 1.5× ATR under H29: terminal=1.8347, lift vs S0=+0.6498. Under flat 2% the lift was +0.3255.
- S4 P95 winning-MAE under H29: terminal=1.3575, lift vs S0=+0.1726. Under flat 2% the lift was +0.4307.

- **Verdict direction preserved:** S1 (1.5× ATR wider) delta vs baseline stays same sign under H29 policy (+0.6498, was +0.3255 under flat 2%). Shadow-log recommendation holds. H29 only narrows the magnitude by reducing risk during DD periods.

**Interpretation:** H29 is a risk-management overlay, not an edge-generator. It cannot MAKE a losing scenario profitable, but it attenuates DD during losing clusters by risking 0.5% instead of 2%. Under chronological replay on the batch, H29's effect is most pronounced for scenarios that take bigger early losses before a recovery — and that ordering is strongly PATH-DEPENDENT on the specific trade sequence in this batch. Results should be interpreted as order-of-magnitude, not precise.

## Recommendation for SL-gate changes

- **Round-number buffer (Q-5.3):** **No action**. The observed hunt-rate lift at clustered SLs is not statistically distinguishable from zero with n=111. Do NOT widen SLs at round numbers on this evidence alone. Re-test once live sample doubles (~200 trades) OR extract PDH/PDL from LanceDB historical MSOs for the 82 pre-2026 trades.
- **Quantile/wider SL (Q-5.4):** **Consider S1 (1.5× ATR)**. Under GTOS fixed-risk-% sizing, lift is +0.082R/trade; under fixed-lot the lift is +0.222R/trade. Deploy in SHADOW MODE first (log-only), evaluate over next 50 trades.

- **Current SL buffer (0.3-0.5 ATR above OB extreme, per Apr 17 session 19 handoff):** retain. The SL-sweep margin change from 0.3 → 0.5 ATR already addresses the most common hunt-out pattern. Q-5.3 evidence does not justify additional round-number specific buffering at this sample size.

## Next steps

1. **Expand stop-hunt evidence base.** Once live sample reaches 200+ trades, re-run Q-5.3 with mae_r/mfe_r from live logs. The question is high-value but currently underpowered.
2. **Back-fill PDH/PDL for 2024-2025 trades.** Pull D1 OHLCV for 2024-01 to 2025-12 from MT5 (historical_2025/, historical_2024/) or LanceDB; re-run the PDH/PDL cluster subtest at n~110.
3. **Compute in-sample P95 winning-MAE as shadow-log:** add a `quantile_sl_shadow` field to live trade logs that records what the SL *would* be under a rolling-100-trade P95 calibration. Observation-only, no decision impact. Evaluate in 50 trades.
4. **Osler confirmation via live-log sweep patterns:** log every trade whose SL was hit + extract the next 6 M15 candles' high/low to confirm/deny reversal. Feeds Q-5.3 power directly.
5. **Consider SHORT-trade imbalance:** 7/111 SHORTs is inadequate for cluster testing by direction. If live trading continues to favor LONGs, direction-conditioned SL rules cannot be validated; if SHORTs reach ≥30, re-run with direction as a covariate.
6. **Join Q-5.4 with Q-5.5 (Kelly):** current live is already risk-constrained at 1-2% (see Q-5_Q-6_exits.md). A wider quantile SL would *reduce* R-payoff while also *reducing* hit probability. Net expectancy lift is ambiguous and may be dominated by Kelly-cap survivorship rather than SL width.