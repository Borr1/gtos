# Q-7.3 / Q-7.6 — Risk Sizing & DD Monte Carlo

**Date:** 2026-04-17 09:35
**Script:** `research/academic_pipeline/scripts/q_7_monte_carlo.py`
**Seed:** 42 (reproducible)
**N_SIMS:** 10,000  **N_TRADES:** 200  **Start equity:** $100,000

---

## Hypothesis (pre-data)

**H1:** Current 2% risk on FTMO lands >= 95% P(pass +10%) given WR=65.8%, mean R=+0.20, H29 DD cut.
**H2:** 1% risk on redacted_account Stellar P1 (+8%) lands >= 95% P(pass); P2 (+5%) lands >= 99%.
**H3:** FTMO optimum (max P(pass) s.t. P(breach)<=1%) sits in 1.0-2.0% band; redacted_account Stellar optimum near 1.0%.
**H4:** Raw empirical Kelly is impractically aggressive; prop-firm optimum closer to 1/4-Kelly to 1/2-Kelly.
**H5:** WR drop 10pp (56% WR) collapses P(pass) < 50% at every risk and P(breach) > 10%.

---

## Data

**Source:** `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json`
**n trades:** 111  (72 WIN, 36 LOSS, 3 BE)

| metric | value |
|---|---|
| WR | 65.8% |
| mean R | +0.1997 |
| median R | +0.1600 |
| stdev R | 1.0433 |
| min R | -1.0000 |
| max R | +3.7700 |
| mean win R | +0.7093 |
| mean loss R | -0.8003 |
| expectancy | +0.1997R / trade |

---

## Method

- **Draw model:** Sample with replacement from empirical R distribution (i.i.d.).
- **Equity update:** `equity += r * equity * risk_pct`. Risk percent applied to *current* equity (floating).
- **H29 rule:** when DD from peak >= 8%, risk = risk/4; reverts on new equity peak.
- **DD measure (primary):** **static** — measured from start equity (FTMO Challenge + redacted_account Stellar 2-Step spec). 10% breach = instant fail.
- **DD measure (secondary, Table C2):** **trailing** — measured from running peak (legacy / funded-stage variant).
- **Daily DD proxy:** single-trade drop >= 5% of start equity — a conservative approximation (real daily DD aggregates multiple trades).
- **Pass:** equity reaches 1+target on or before trade 200 without prior breach. **Simulation terminates immediately on pass** (matches how a Challenge account is awarded).
- **Stress #1 (WR decay):** convert 10% of wins to losses (sampled from empirical loss pool).
- **Stress #2 (worst start):** force 3 losses at trade 1-3 before normal random draws.
- **Bootstrap CI:** 1,000 resamples over per-sim 0/1 outcome arrays.

---

## Results: Q-7.3 Max-DD Distribution

DD percentiles from running peak across 10,000 sims (baseline R-dist, N=200 trades, H29 on).

| Risk % | median DD | p75 DD | p95 DD | p99 DD | P(DD>=10%) |
|---|---|---|---|---|---|
| 0.25% | 0.27% | 0.69% | 1.59% | 2.53% | 0.00% |
| 0.50% | 0.53% | 1.40% | 3.27% | 4.97% | 0.00% |
| 1.00% | 1.11% | 2.76% | 5.97% | 8.36% | 0.08% |
| 1.50% | 1.57% | 3.99% | 8.25% | 10.04% | 1.34% |
| 2.00% | 2.00% | 4.99% | 9.62% | 10.25% | 3.78% |
| 2.50% | 2.50% | 5.73% | 10.13% | 10.42% | 7.41% |
| 3.00% | 3.00% | 6.77% | 10.34% | 10.60% | 11.99% |

**Notes:**
- DD values are *clipped* at 10% on breach (simulation stops), so p99 can read as 10% when breach rate is above 1%.
- At 1.0% risk, P(DD>=10%) = 0.08%; at 2.0% risk, P(DD>=10%) = 3.78%.

---

## Results: Q-7.6 — Survival × Risk Fraction

### Table A — FTMO $100K Challenge (+10% target, 10% max DD)

| Risk % | P(pass +10%) | P(DD breach 10%) | P(daily DD breach) | median terminal | p10 terminal |
|---|---|---|---|---|---|
| 0.25% | **58.41%** | 0.00% | 0.00% | $110,032 | $105,408 |
| 0.50% | **94.61%** | 0.00% | 0.00% | $110,318 | $110,023 |
| 1.00% | **98.27%** | 0.08% | 0.00% | $110,692 | $110,078 |
| 1.50% | **96.61%** | 1.34% | 0.00% | $110,989 | $110,091 |
| 2.00% | **94.57%** | 3.78% | 0.00% | $111,243 | $110,083 |
| 2.50% | **91.64%** | 7.41% | 0.00% | $111,402 | $110,038 |
| 3.00% | **87.46%** | 11.99% | 0.00% | $111,449 | $89,917 |

**Bootstrap 95% CIs (FTMO):**
- 1.0% risk: P(pass) = 98.27% [97.98%, 98.52%]; P(breach) = 0.08% [0.03%, 0.14%]
- 2.0% risk: P(pass) = 94.57% [94.10%, 95.01%]; P(breach) = 3.78% [3.42%, 4.19%]

### Table B1 — redacted_account Stellar Phase 1 (+8% target, 10% max DD)

| Risk % | P(pass +8%) | P(DD breach 10%) | P(daily DD breach) | median terminal | p10 terminal |
|---|---|---|---|---|---|
| 0.25% | **77.70%** | 0.00% | 0.00% | $108,102 | $105,420 |
| 0.50% | **96.99%** | 0.00% | 0.00% | $108,328 | $108,032 |
| 1.00% | **98.83%** | 0.08% | 0.00% | $108,641 | $108,072 |
| 1.50% | **97.32%** | 1.34% | 0.00% | $108,967 | $108,099 |
| 2.00% | **94.93%** | 3.78% | 0.00% | $109,194 | $108,089 |
| 2.50% | **91.94%** | 7.41% | 0.00% | $109,387 | $108,049 |
| 3.00% | **87.74%** | 11.93% | 0.00% | $109,676 | $89,921 |

**Bootstrap 95% CIs (redacted_account P1):**
- 1.0% risk: P(pass) = 98.83% [98.61%, 99.03%]; P(breach) = 0.08% [0.03%, 0.14%]
- 2.0% risk: P(pass) = 94.93% [94.50%, 95.36%]; P(breach) = 3.78% [3.42%, 4.19%]

### Table B2 — redacted_account Stellar Phase 2 (+5% target, 10% max DD)

| Risk % | P(pass +5%) | P(DD breach 10%) | P(daily DD breach) | median terminal | p10 terminal |
|---|---|---|---|---|---|
| 0.25% | **94.35%** | 0.00% | 0.00% | $105,149 | $105,010 |
| 0.50% | **99.11%** | 0.00% | 0.00% | $105,331 | $105,042 |
| 1.00% | **99.33%** | 0.08% | 0.00% | $105,673 | $105,080 |
| 1.50% | **98.06%** | 1.34% | 0.00% | $105,886 | $105,093 |
| 2.00% | **95.71%** | 3.77% | 0.00% | $106,276 | $105,105 |
| 2.50% | **92.48%** | 7.30% | 0.00% | $106,558 | $105,062 |
| 3.00% | **88.27%** | 11.69% | 0.00% | $106,742 | $89,929 |

### Table C — Stress: WR drop 10pp (simulated decay)

Decayed pool WR = 55.9%, mean R = +0.0651. Re-run FTMO survival.

| Risk % | P(pass +10%) | P(DD breach 10%) | median terminal | p10 terminal |
|---|---|---|---|---|
| 0.25% | **6.63%** | 0.00% | $103,136 | $98,527 |
| 0.50% | **43.56%** | 0.13% | $106,819 | $95,965 |
| 1.00% | **63.95%** | 6.34% | $110,237 | $92,244 |
| 1.50% | **64.99%** | 16.83% | $110,389 | $89,906 |
| 2.00% | **63.24%** | 25.57% | $110,455 | $89,784 |
| 2.50% | **62.30%** | 31.67% | $110,473 | $89,703 |
| 3.00% | **59.23%** | 37.84% | $110,360 | $89,565 |

### Table C2 — Alternative DD spec: TRAILING DD (legacy FTMO, funded stage)

FTMO Challenge is currently **static** (measured from initial $100K); some older variants 
and the funded stage use **trailing** DD (measured from highest balance). Trailing is 
materially harder once equity goes above initial balance.

| Risk % | P(pass +10%) [FTMO trailing] | P(DD breach trailing 10%) | median terminal |
|---|---|---|---|
| 0.25% | **58.41%** | 0.00% | $110,032 |
| 0.50% | **94.61%** | 0.00% | $110,318 |
| 1.00% | **98.09%** | 0.66% | $110,689 |
| 1.50% | **93.36%** | 6.28% | $110,927 |
| 2.00% | **86.27%** | 13.72% | $111,033 |
| 2.50% | **80.51%** | 19.49% | $111,045 |
| 3.00% | **74.33%** | 25.67% | $110,944 |

Under trailing DD, 0.5-1.0% remains comfortable; 2%+ carries elevated breach risk.

### Table D — Stress: Worst-start (3 forced losses at T=1-3)

FTMO survival conditional on 3 consecutive losses at the start.

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

Criterion: **maximise P(pass) subject to P(DD breach) <= 1%** (within the discrete grid tested).

| Profile | Optimal Risk | P(pass) | P(DD breach) | Note |
|---|---|---|---|---|
| FTMO $100K Challenge | **1.00%** | 98.27% | 0.08% | feasible |
| redacted_account Stellar P1 (+8%) | **1.00%** | 98.83% | 0.08% | feasible |
| redacted_account Stellar P2 (+5%) | **1.00%** | 99.33% | 0.08% | feasible |

Relaxed criterion: P(DD breach) <= 5% (more aggressive).

| Profile | Optimal Risk | P(pass) | P(DD breach) |
|---|---|---|---|
| FTMO $100K Challenge | **1.00%** | 98.27% | 0.08% |
| redacted_account Stellar P1 (+8%) | **1.00%** | 98.83% | 0.08% |
| redacted_account Stellar P2 (+5%) | **1.00%** | 99.33% | 0.08% |

---

## Kelly Comparison

| fraction | value | notes |
|---|---|---|
| Kelly (fixed-R formula, WR=65.8%, win=0.709, loss=-0.800) | 27.14% | single-point approx |
| Kelly (empirical, maximises E[log(1+fR)] over R-distribution) | 22.90% | full-distribution grid search |
| 1/2-Kelly (empirical) | 11.45% | |
| 1/4-Kelly (empirical) | 5.73% | |

**Why found optimum differs from Kelly:**
- Kelly maximises long-run log-wealth with **no cutoff**; FTMO/redacted_account have **hard ruin thresholds**.
- Path dependency matters: even a Kelly-sized bet can breach 10% DD on a bad run (fat left tail in prop-firm MC), which Kelly does not penalise.
- Prop-firm optima are typically 1/4- to 1/2-Kelly in the literature (Thorp, Vince, Ziemba).
- Empirical Kelly here (22.9%) is aggressive relative to the 10% DD ceiling on 100K equity.

---

## H29 Trigger Sensitivity (FTMO 2% baseline)

Sweep the H29 trigger threshold 0%-15% at 2% risk to see whether 8% is optimal.

| H29 Trigger | P(pass +10%) | P(DD breach) | median terminal |
|---|---|---|---|
| 4% | 95.70% | 0.28% | $111,281 |
| 6% | 96.00% | 1.40% | $111,271 |
| 8% | 94.42% | 4.10% | $111,222 |
| 10% | 92.90% | 6.35% | $111,207 |
| 12% | 92.25% | 7.45% | $111,198 |
| 15% | 91.77% | 8.21% | $111,179 |
| 100% (DISABLED) | 91.63% | 8.37% | $111,175 |

Disable (trigger=1.0) is the no-H29 baseline.

### H29 Sensitivity at 1% baseline (redacted_account recommendation)

| H29 Trigger | P(pass +10%) | P(DD breach) | median terminal |
|---|---|---|---|
| 4% | 93.82% | 0.00% | $110,604 |
| 6% | 96.47% | 0.02% | $110,642 |
| 8% | 97.97% | 0.13% | $110,654 |
| 10% | 98.41% | 0.57% | $110,672 |
| 15% | 98.64% | 0.83% | $110,674 |
| 100% (DISABLED) | 98.64% | 0.82% | $110,674 |

At 1% risk the H29 trigger barely matters — the base risk is already safe.

---

## Hypothesis Evaluation (post-data)

- **H1** (Current 2% FTMO >= 95% pass): P(pass)=94.57% — **VERY CLOSE (94.6%)**.
- **H2a** (1% redacted_account P1 >= 95%): P(pass)=98.83% — **CONFIRMED**.
- **H2b** (1% redacted_account P2 >= 99%): P(pass)=99.33% — **CONFIRMED**.
- **H3** (FTMO optimum in 1-2%): optimum = 1.00% — **CONFIRMED**.
- **H4** (optimum ≈ 1/4-to-1/2-Kelly): 1/4K=5.7%, 1/2K=11.5%, observed opt=1.00% — **REJECTED (found optimum is much more conservative than Kelly family — DD cutoff dominates)**.
- **H5** (WR-10pp crushes pass + spikes breach): at 2% risk decay P(pass)=63.2%, P(breach)=25.6% — **PARTIALLY CONFIRMED (breach spikes but pass holds at moderate risk)**.

---

## Recommendations

**FTMO $100K Challenge:** **1.00% risk**  → P(pass) = 98.27%, P(breach) = 0.08%.
**redacted_account Stellar P1 (+8%):** **1.00% risk**  → P(pass) = 98.83%, P(breach) = 0.08%.
**redacted_account Stellar P2 (+5%):** **1.00% risk**  → P(pass) = 99.33%, P(breach) = 0.08%.

**H29 trigger:** best observed at **6%** — P(pass)=96.00%, P(breach)=1.40%. Current 8% is CLOSE TO OPTIMAL — consider 6%.

**WR-decay robustness:** under 10pp WR drop, FTMO P(pass) at the 2% baseline falls to 63.24%, P(breach) rises to 25.57%. 

**Worst-start robustness:** with 3 forced losses at start, FTMO P(pass) at 2% = 79.08% (vs 94.57% baseline).

---

## Caveats

1. **Sample size:** n=111 R-values may not capture the live regime's full tail. True tail is likely fatter.
2. **i.i.d. assumption:** Monte Carlo draws trades independently. Live trading has autocorrelation (streaks, regime shifts).
3. **Horizon:** 200 trades = roughly 12 months at 17 trades/month. FTMO Challenge is 30-day window; actual is shorter.
   → For time-limited programs, reduce N_TRADES to 30-60 to stress test.
4. **Daily DD proxy:** Per-trade drop >= 5% is conservative (most days have multiple trades). Actual daily DD aggregates.
5. **Max DD measurement:** Primary (Tables A, B1, B2, C, D) uses **static** (from start equity) — matches current FTMO Challenge + redacted_account Stellar 2-Step Challenge spec. Table C2 shows trailing-DD (legacy FTMO / funded-stage). CEO should confirm the exact DD type on the redacted_account Stellar 2-Step contract before Monday Apr 20 go-live.
6. **R-distribution static:** WR decay stress is one simulated scenario, not an exhaustive regime-shift model.
7. **No correlation between instruments:** Real MC would sample per-instrument; this pools all 111 trades as one distribution.

---

## Next Steps

1. **Confirm redacted_account trailing-DD vs static-DD spec** by reading Stellar program rules (currently assumed trailing).
2. **Run 30-trade horizon MC** for FTMO 30-day window (N_TRADES=30). If P(pass) diverges from 200-trade baseline, prefer higher-risk sizing for speed.
3. **Per-instrument MC** — sample from each instrument's R-distribution separately, then aggregate.
4. **GARCH volatility clustering** — inject autocorrelated vol (rho=0.99 from prior dist work) into the draw process.
5. **Bootstrap pass/breach CIs over R-distribution itself** (resample 111 trades, then MC). Captures sample-size uncertainty.
6. **CEO decision on H29 threshold:** if current 8% is suboptimal, propose config change.

---

*Generated: 2026-04-17 09:36:01*
*Script: `research/academic_pipeline/scripts/q_7_monte_carlo.py`*