# Q-7.3 / Q-7.6 — Risk Sizing & DD Monte Carlo (v2)

**Version:** v2 — Wave-1 reviewer fixes: BE-labeling inconsistency resolved; misleading daily-DD column removed/relabeled.

**Date:** 2026-04-17 10:40
**Script:** `research/academic_pipeline/scripts/q_7_monte_carlo_v2.py`
**JSON:** `research/academic_pipeline/results/Q-7_risk_dd_monte_carlo_v2.json`
**Seed:** 42 (reproducible)
**N_SIMS:** 10,000  **N_TRADES:** 200  **Start equity:** $100,000

---

## v1 -> v2 change summary

**Fix 1 — BE labeling inconsistency.** v1 reported `(72 WIN, 36 LOSS, 3 BE)` in the Data table but used `(r_multiple > 0)` inside the simulator (which counts 73 wins / 38 losses, because two BREAKEVEN-labelled rows have r_multiple != 0: one at +0.02R, one at -0.01R). v2 reports counts from the explicit `outcome` field and uses the standard convention **BE excluded from the WR denominator**:
  - n_WIN = 72, n_LOSS = 36, n_BE = 3 (total 111).
  - WR (v2) = n_WIN / (n_WIN + n_LOSS) = 72/(72+36) = **0.6667**.
  - For reference, v1's implicit (r>0)/N was 0.6577.
  - The MC *draws* are still sampled from `r_multiple` across all 111 rows — BE-labelled trades have near-zero R and contribute accurately to the sampling distribution. Only the header label is corrected.

**Fix 2 — `P(daily DD breach)` column misleading.** v1 reported 0.00% in every row, computed as "P(single-trade drop >= 5% of start equity)". This is NOT the daily FTMO 5% rule (which aggregates multiple trades in one day). v2 renames the column to `P(trade-level drop >= 5%)` and demotes it to an explanatory note. Daily FTMO breach probability is left un-estimated pending a per-day aggregation model (future work — needs trade timestamps to group trades into calendar days).

Everything else unchanged: same seed, same 10k × 200 sims, same H29 rule, same bootstrap, same Kelly math.

---

## Hypothesis (pre-data) — unchanged from v1

**H1:** Current 2% risk on FTMO lands >= 95% P(pass +10%) given WR=66.67%, mean R=+0.20, H29 DD cut.
**H2:** 1% risk on redacted_account Stellar P1 (+8%) lands >= 95% P(pass); P2 (+5%) lands >= 99%.
**H3:** FTMO optimum (max P(pass) s.t. P(breach)<=1%) sits in 1.0-2.0% band; redacted_account Stellar optimum near 1.0%.
**H4:** Raw empirical Kelly is impractically aggressive; prop-firm optimum closer to 1/4-Kelly to 1/2-Kelly.
**H5:** WR drop 10pp collapses P(pass) < 50% at every risk and P(breach) > 10%.

---

## Data

**Source:** `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json`
**n_batch:** 111

| count-type | value |
|---|---|
| outcome == 'WIN' | 72 |
| outcome == 'LOSS' | 36 |
| outcome == 'BREAKEVEN' | 3 |
| WR (BE excluded, standard) | 0.6667 |
| WR (r>0 / N, v1 implicit) | 0.6577 |

| R-stat | value |
|---|---|
| mean R | +0.1997 |
| median R | +0.1600 |
| stdev R | 1.0433 |
| min R | -1.0000 |
| max R | +3.7700 |
| mean win R | +0.7093 |
| mean loss R | -0.8003 |
| expectancy | +0.1997R / trade |

**Note on BE rows:** two trades labelled BREAKEVEN have non-zero `r_multiple` (+0.02 and -0.01 — small costs from spread/commission at near-BE exits). The simulator uses `r_multiple` directly so they contribute ~0 to expectancy, as intended. Using outcome-field labels gives the WR that matches live reporting.

---

## Method

- **Draw model:** Sample with replacement from empirical R distribution (i.i.d.), all 111 rows including BE.
- **Equity update:** `equity += r * equity * risk_pct`. Risk on *current* equity.
- **H29 rule:** when DD from peak >= 8%, risk = risk/4; reverts on new equity peak.
- **DD measure (primary, Tables A/B/C/D):** static (from start equity). 10% breach = fail.
- **DD measure (secondary, Table C2):** trailing (from running peak).
- **`P(trade-level drop >= 5%)`:** fraction of sims where any single trade lost more than 5% of START_EQUITY. **This is NOT the FTMO daily 5% rule** — daily DD aggregates multiple trades per calendar day. Flagged explicitly per reviewer note.
- **Pass:** equity reaches target before trade 200 without prior breach. **Simulation terminates on pass.**
- **Stress #1 (WR decay):** convert 10% of wins to losses (sampled from empirical loss pool).
- **Stress #2 (worst start):** force 3 losses at T=1-3.
- **Bootstrap CI:** 1,000 resamples of per-sim 0/1 outcome arrays.

---

## Results: Q-7.3 Max-DD Distribution

DD percentiles across 10,000 sims (baseline R-dist, N=200 trades, H29 on, STATIC DD).

| Risk % | median DD | p75 DD | p95 DD | p99 DD | P(DD>=10%) |
|---|---|---|---|---|---|
| 0.25% | 0.27% | 0.69% | 1.59% | 2.53% | 0.00% |
| 0.50% | 0.53% | 1.40% | 3.27% | 4.97% | 0.00% |
| 1.00% | 1.11% | 2.76% | 5.97% | 8.36% | 0.08% |
| 1.50% | 1.57% | 3.99% | 8.25% | 10.04% | 1.34% |
| 2.00% | 2.00% | 4.99% | 9.62% | 10.25% | 3.78% |
| 2.50% | 2.50% | 5.73% | 10.13% | 10.42% | 7.41% |
| 3.00% | 3.00% | 6.77% | 10.34% | 10.60% | 11.99% |

Notes:
- DD values are clipped at 10% on breach (simulation stops).
- At 1.0% risk, P(DD>=10%) = 0.08%; at 2.0% risk, P(DD>=10%) = 3.78%.

---

## Results: Q-7.6 — Survival × Risk Fraction

### Table A — FTMO $100K Challenge (+10% target, 10% max DD)

| Risk % | P(pass +10%) | P(DD breach 10%) | median terminal | p10 terminal |
|---|---|---|---|---|
| 0.25% | **58.41%** | 0.00% | $110,032 | $105,408 |
| 0.50% | **94.61%** | 0.00% | $110,318 | $110,023 |
| 1.00% | **98.27%** | 0.08% | $110,692 | $110,078 |
| 1.50% | **96.61%** | 1.34% | $110,989 | $110,091 |
| 2.00% | **94.57%** | 3.78% | $111,243 | $110,083 |
| 2.50% | **91.64%** | 7.41% | $111,402 | $110,038 |
| 3.00% | **87.46%** | 11.99% | $111,449 | $89,917 |

*Footnote: `P(trade-level drop >= 5%)` is identically 0.00% in every row at these risk levels (no single trade can lose 5% at 1-2% risk). This is NOT the FTMO daily 5% rule — see method note above.*

**Bootstrap 95% CIs (FTMO):**
- 1.0% risk: P(pass) = 98.27% [97.98%, 98.52%]; P(breach) = 0.08% [0.03%, 0.14%]
- 2.0% risk: P(pass) = 94.57% [94.10%, 95.01%]; P(breach) = 3.78% [3.42%, 4.19%]

### Table B1 — redacted_account Stellar Phase 1 (+8% target, 10% max DD)

| Risk % | P(pass +8%) | P(DD breach 10%) | median terminal | p10 terminal |
|---|---|---|---|---|
| 0.25% | **77.70%** | 0.00% | $108,102 | $105,420 |
| 0.50% | **96.99%** | 0.00% | $108,328 | $108,032 |
| 1.00% | **98.83%** | 0.08% | $108,641 | $108,072 |
| 1.50% | **97.32%** | 1.34% | $108,967 | $108,099 |
| 2.00% | **94.93%** | 3.78% | $109,194 | $108,089 |
| 2.50% | **91.94%** | 7.41% | $109,387 | $108,049 |
| 3.00% | **87.74%** | 11.93% | $109,676 | $89,921 |

**Bootstrap 95% CIs (redacted_account P1):**
- 1.0% risk: P(pass) = 98.83% [98.61%, 99.03%]; P(breach) = 0.08% [0.03%, 0.14%]
- 2.0% risk: P(pass) = 94.93% [94.50%, 95.36%]; P(breach) = 3.78% [3.42%, 4.19%]

### Table B2 — redacted_account Stellar Phase 2 (+5% target, 10% max DD)

| Risk % | P(pass +5%) | P(DD breach 10%) | median terminal | p10 terminal |
|---|---|---|---|---|
| 0.25% | **94.35%** | 0.00% | $105,149 | $105,010 |
| 0.50% | **99.11%** | 0.00% | $105,331 | $105,042 |
| 1.00% | **99.33%** | 0.08% | $105,673 | $105,080 |
| 1.50% | **98.06%** | 1.34% | $105,886 | $105,093 |
| 2.00% | **95.71%** | 3.77% | $106,276 | $105,105 |
| 2.50% | **92.48%** | 7.30% | $106,558 | $105,062 |
| 3.00% | **88.27%** | 11.69% | $106,742 | $89,929 |

### Table C — Stress: WR drop 10pp (simulated decay)

Decayed pool WR = 55.9%, mean R = +0.0651.

| Risk % | P(pass +10%) | P(DD breach 10%) | median terminal | p10 terminal |
|---|---|---|---|---|
| 0.25% | **6.63%** | 0.00% | $103,136 | $98,527 |
| 0.50% | **43.56%** | 0.13% | $106,819 | $95,965 |
| 1.00% | **63.95%** | 6.34% | $110,237 | $92,244 |
| 1.50% | **64.99%** | 16.83% | $110,389 | $89,906 |
| 2.00% | **63.24%** | 25.57% | $110,455 | $89,784 |
| 2.50% | **62.30%** | 31.67% | $110,473 | $89,703 |
| 3.00% | **59.23%** | 37.84% | $110,360 | $89,565 |

### Table C2 — Trailing DD spec (legacy FTMO / funded stage)

| Risk % | P(pass +10%) | P(DD breach trailing 10%) | median terminal |
|---|---|---|---|
| 0.25% | **58.41%** | 0.00% | $110,032 |
| 0.50% | **94.61%** | 0.00% | $110,318 |
| 1.00% | **98.09%** | 0.66% | $110,689 |
| 1.50% | **93.36%** | 6.28% | $110,927 |
| 2.00% | **86.27%** | 13.72% | $111,033 |
| 2.50% | **80.51%** | 19.49% | $111,045 |
| 3.00% | **74.33%** | 25.67% | $110,944 |

### Table D — Stress: Worst-start (3 forced losses T=1-3)

| Risk % | P(pass +10%) | P(DD breach 10%) | median terminal |
|---|---|---|---|
| 0.25% | **49.88%** | 0.00% | $109,931 |
| 0.50% | **91.76%** | 0.00% | $110,298 |
| 1.00% | **96.54%** | 0.52% | $110,660 |
| 1.50% | **91.03%** | 6.74% | $110,885 |
| 2.00% | **79.08%** | 19.64% | $110,845 |
| 2.50% | **63.56%** | 35.49% | $110,512 |
| 3.00% | **47.52%** | 52.13% | $89,976 |

---

## Optimal Risk Recommendation

Criterion: maximise P(pass) subject to P(DD breach) <= 1%.

| Profile | Optimal Risk | P(pass) | P(DD breach) | Note |
|---|---|---|---|---|
| FTMO $100K Challenge | **1.00%** | 98.27% | 0.08% | feasible |
| redacted_account Stellar P1 (+8%) | **1.00%** | 98.83% | 0.08% | feasible |
| redacted_account Stellar P2 (+5%) | **1.00%** | 99.33% | 0.08% | feasible |

Relaxed criterion: P(DD breach) <= 5%.

| Profile | Optimal Risk | P(pass) | P(DD breach) |
|---|---|---|---|
| FTMO $100K Challenge | **1.00%** | 98.27% | 0.08% |
| redacted_account Stellar P1 (+8%) | **1.00%** | 98.83% | 0.08% |
| redacted_account Stellar P2 (+5%) | **1.00%** | 99.33% | 0.08% |

---

## Kelly Comparison

| fraction | value | notes |
|---|---|---|
| Kelly (fixed-R formula, WR=0.6667, win=0.709, loss=-0.800) | 29.06% | single-point approx; uses v2 (BE-excluded) WR |
| Kelly (empirical, maximises E[log(1+fR)]) | 22.90% | grid search |
| 1/2-Kelly | 11.45% | |
| 1/4-Kelly | 5.73% | |

## H29 Trigger Sensitivity

### 2% baseline

| H29 Trigger | P(pass +10%) | P(DD breach) | median terminal |
|---|---|---|---|
| 4% | 95.70% | 0.28% | $111,281 |
| 6% | 96.00% | 1.40% | $111,271 |
| 8% | 94.42% | 4.10% | $111,222 |
| 10% | 92.90% | 6.35% | $111,207 |
| 12% | 92.25% | 7.45% | $111,198 |
| 15% | 91.77% | 8.21% | $111,179 |
| 100% (DISABLED) | 91.63% | 8.37% | $111,175 |

### 1% baseline

| H29 Trigger | P(pass +10%) | P(DD breach) | median terminal |
|---|---|---|---|
| 4% | 93.82% | 0.00% | $110,604 |
| 6% | 96.47% | 0.02% | $110,642 |
| 8% | 97.97% | 0.13% | $110,654 |
| 10% | 98.41% | 0.57% | $110,672 |
| 15% | 98.64% | 0.83% | $110,674 |
| 100% (DISABLED) | 98.64% | 0.82% | $110,674 |

At 1% risk the H29 trigger barely matters — base risk is already safe.

---

## Hypothesis Evaluation (post-data)

- **H1** (2% FTMO >= 95%): P(pass)=94.57% — **VERY CLOSE**.
- **H2a** (1% redacted_account P1 >= 95%): P(pass)=98.83% — **CONFIRMED**.
- **H2b** (1% redacted_account P2 >= 99%): P(pass)=99.33% — **CONFIRMED**.
- **H3** (FTMO optimum in 1-2%): optimum = 1.00% — **CONFIRMED**.
- **H4** (optimum ~ 1/4-to-1/2-Kelly): 1/4K=5.7%, 1/2K=11.5%, observed=1.00% — **REJECTED (DD cutoff dominates)**.
- **H5** (WR-10pp decay): P(pass)=63.2%, P(breach)=25.6% — **PARTIALLY CONFIRMED**.

---

## Recommendations

**FTMO:** **1.00%** -> P(pass) = 98.27%, P(breach) = 0.08%.
**redacted_account P1:** **1.00%** -> P(pass) = 98.83%, P(breach) = 0.08%.
**redacted_account P2:** **1.00%** -> P(pass) = 99.33%, P(breach) = 0.08%.

No numerical change from v1 for these optima — the v2 fixes are labelling only. The MC draws themselves are seed-equivalent to v1 because the same `r_multiple` array is sampled.

---

## Caveats

1. **n=111** — empirical R tail may be thinner than the live regime's tail.
2. **i.i.d. assumption** ignores streak autocorrelation.
3. **Horizon** 200 trades = ~1 year; FTMO Challenge window is shorter.
4. **Trade-level drop proxy is not daily FTMO breach.** Daily DD aggregates multi-trade calendar days; this script does not model that aggregation.
5. **Max DD measurement:** static primary; trailing alternative in Table C2.
6. **WR decay** is one stress scenario, not a full regime-shift model.
7. **No per-instrument correlation** — pools all 111 rows.

---

## Next Steps

1. **Real daily DD model** — group trades into calendar days by timestamp, re-run the 5% check. Requires `entry_time` field (already present in batch).
2. **Confirm redacted_account trailing-vs-static** by reading Stellar 2-Step rules.
3. **30-trade horizon** for FTMO 30-day window.
4. **Per-instrument MC** once batches for US30/USDJPY/GBPJPY consolidated.
5. **GARCH volatility clustering** injection.
6. **Bootstrap R-distribution itself** (resample 111 trades then MC).

*Generated: 2026-04-17 10:40:47*
*Script: `research/academic_pipeline/scripts/q_7_monte_carlo_v2.py`*