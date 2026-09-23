# Q-11 — Cross-Instrument Portfolio Analysis

**Date:** 2026-04-17 10:36
**Script:** `research/academic_pipeline/scripts/q_11_portfolio.py`
**Seed:** 42 (reproducible)
**N_SIMS:** 10,000  **N_TRADES:** 200  **Start equity:** $100,000

---

## Hypothesis (pre-registered, before data)

- **H-11.1a** Proportional-to-Kelly allocation OUTPERFORMS equal-weight by >=2pp in P(pass FTMO).
- **H-11.1b** Outperformance gap is SMALL (<5pp) because all 4 traded instruments already sit in the 55-75% WR band.
- **H-11.2** 3-day JPY basket has predictive sign-correlation with next-day USDJPY (|r| >= 0.15, p < 0.05 at 1-day horizon); intraday (1h, 4h) noisier.
- **H-11.3** Dynamic 'hottest-only' selection UNDERPERFORMS equal-weight (rolling-20 WR is mostly noise; regression-to-mean).
- **H-11.4** Pairwise correlations JUMP under stress; in particular USDJPY-GBPJPY moves from ~0.3-0.5 to >0.7; XAUUSD-US30 mild-negative becomes significantly negative (~-0.4). |delta_corr| >= 0.2 in >= 3/10 pairs.

---

## Data

**Per-instrument R-distributions** (synthesised — batch JSON has no symbol field):
- XAUUSD batch provides the raw win/loss R pools (n=111, WR=64.9%, mean_R=+0.198).
- For each non-gold instrument, we generate a 2000-sample pool by drawing wins with probability = batch-validated WR and losses with probability (1-WR), using the XAUUSD win/loss R magnitudes.
- **This is a limitation**: it assumes per-instrument win/loss R magnitudes match XAUUSD. Different instruments may have different R distributions even at the same WR.

| Symbol | batch WR | pool WR | pool mean R | pool std R | source |
|---|---|---|---|---|---|
| XAUUSD | 62.0% (n=129) | 0.618 | +0.1420 | 1.0586 | CLAUDE.md |
| US30 | 58.5% (n=41) | 0.573 | +0.0568 | 1.0354 | CLAUDE.md |
| USDJPY | 75.8% (n=33) | 0.748 | +0.3233 | 1.0606 | CLAUDE.md |
| GBPJPY | 57.1% (n=42) | 0.573 | +0.0783 | 1.0519 | CLAUDE.md |
| GBPUSD | 55.0% (n=0) | 0.559 | +0.0272 | 1.0196 | CLAUDE.md |

**Cross-instrument statistics** (from D1 OHLCV CSVs, not trade outcomes):
- Source: `data/historical_2026/*_D1.csv` (Jan 2 – Apr 10, 2026 — ~70 days each)
- Used for: JPY basket correlation, correlation-stability regime analysis.
- **Caveat**: 70 daily observations is short; correlation CIs are wide.

---

## Method

### Q-11.1 Allocation MC
1. Per-instrument R-pool as above.
2. Draw 200 trades per sim. At each step: (a) pick instrument by `share_map`, (b) draw R from that instrument's pool, (c) apply risk from `risk_map`. H29 = 0.08.
3. 10,000 sims per rule. Compare P(pass +10%), P(DD breach >=10%), median DD, terminal equity percentiles.
4. Rules tested: A equal-weight equal-2%, B Kelly-scaled risk, C gold 40% trade-share equal-2%, D gold-solo.

### Q-11.2 JPY basket signal
1. Daily returns from USDJPY and GBPJPY D1 closes.
2. Basket = -0.5*(USDJPY_ret + GBPJPY_ret). Negative basket => yen weakness.
3. 3-day rolling basket return tested against next-day USDJPY return (both correlation and sign-agreement with binomial test).
4. Also test 1-day basket, H4 basket (next-H4), H1 basket (next-H1).

### Q-11.3 Dynamic selection
1. Synthesise a 600-trade-per-instrument stream from per-instrument pools.
2. Maintain rolling-20 WR per instrument.
3. At each step: pick hottest (max rolling WR) vs coldest vs round-robin. Record realised R.
4. Run 50 trials (diff seeds); paired t-test hottest vs equal mean_R.

### Q-11.4 Correlation stability
1. D1 returns for all 5 instruments; aligned index.
2. XAUUSD 14-day rolling |ret| as vol proxy. Top 20% of days = high-vol regime.
3. Pairwise correlations in full / high-vol / low-vol subsets. Fisher-Z test for high vs low.
4. Flag |delta_corr| >= 0.20 as 'jumped'.

---

## Q-11.1 — Heterogeneous Allocation

### Kelly per instrument
| Symbol | WR | Kelly (fixed-R) | Kelly (empirical) | 1/2 Kelly | 1/4 Kelly |
|---|---|---|---|---|---|
| XAUUSD | 62.0% | 19.13% | 15.00% | 7.50% | 3.75% |
| US30 | 58.5% | 11.68% | 5.70% | 2.85% | 1.43% |
| USDJPY | 75.8% | 48.50% | 29.90% | 14.95% | 7.47% |
| GBPJPY | 57.1% | 8.70% | 7.80% | 3.90% | 1.95% |
| GBPUSD | 55.0% | 4.23% | 2.70% | 1.35% | 0.68% |

Note: Kelly computed from synthesised pools; fixed-R Kelly uses the XAUUSD win/loss means (0.709/-0.800). USDJPY has highest Kelly due to 75.8% WR.

### Rule B — Kelly-scaled risk
risk_i = 2% × (K_emp_i / max(K_emp)). Scaled so top instrument stays at 2%.

| Symbol | K_emp | Rule B risk |
|---|---|---|
| XAUUSD | 15.00% | 1.003% |
| US30 | 5.70% | 0.381% |
| USDJPY | 29.90% | 2.000% |
| GBPJPY | 7.80% | 0.522% |
| GBPUSD | 2.70% | 0.181% |

### Allocation Rules — Portfolio MC Outcomes
(FTMO-style: +10% target, 10% max DD, 200 trades, H29 on.)

| Rule | P(pass) | P(DD breach) | Median DD | p95 DD | Median terminal | P10 terminal | Sharpe (median) |
|---|---|---|---|---|---|---|---|
| A: equal 2% / equal traffic | **80.98%** | 12.75% | 3.72% | 10.21% | $110,961 | $89,940 | +3.068 |
| B: Kelly-scaled risk (raw) | **94.57%** | 0.45% | 1.28% | 7.15% | $110,893 | $110,045 | +3.142 |
| B_norm: Kelly-scaled, iso-risk vs Rule A | **89.30%** | 6.87% | 2.54% | 10.08% | $111,255 | $100,447 | +3.466 |
| B_norm_corrected: iso-risk post-clip mean==2% | **85.29%** | 11.04% | 3.25% | 10.23% | $111,242 | $89,969 | +3.441 |
| C: gold 40% trade share, equal 2% | **82.66%** | 11.57% | 3.60% | 10.20% | $110,995 | $89,959 | +3.134 |
| D: gold-only 2% | **84.52%** | 10.47% | 3.32% | 10.17% | $111,045 | $89,989 | +3.354 |

**Rule B_norm scaling:** each instrument's Kelly-derived risk multiplied by a constant so avg equals 2% (the Rule A baseline). Effective risk per instrument:

| Symbol | Rule B raw | Rule B_norm (iso-risk, buggy clip) | Rule B_norm_corrected (post-clip mean = 2%) |
|---|---|---|---|
| XAUUSD | 1.003% | 2.455% | 3.000% |
| US30 | 0.381% | 0.933% | 1.407% |
| USDJPY | 2.000% | 3.000% | 3.000% |
| GBPJPY | 0.522% | 1.277% | 1.926% |
| GBPUSD | 0.181% | 0.442% | 0.667% |

- Buggy B_norm uniform mean (post-clip): **1.621%** (should be 2.000%).
- Corrected B_norm_corrected uniform mean (post-clip): **2.000%** (matches Rule A exactly).

**Best rule by P(pass):** `B: Kelly-scaled risk (raw)` at 94.57% P(pass).

- Rule B (raw Kelly, low avg risk) vs Rule A: delta = +13.59pp
- Rule B_norm (BUGGY iso-risk Kelly, post-clip mean=1.62%) vs Rule A: delta = +8.32pp — retained for trail; see Reviewer correction section
- **Rule B_norm_corrected (iso-risk post-clip mean = 2.00%) vs Rule A: delta = +4.31pp** — the reviewer-corrected CLEAN comparison
- Rule C (gold 40% share) vs Rule A: delta = +1.68pp
- Rule D (solo) vs Rule A: delta = +3.54pp

**Interpretation**: Heterogeneous allocation provides material edge >=2pp (using reviewer-corrected B_norm_corrected). Re-weight toward higher-Kelly instruments.

**Why Rule B wins by so much:**
Rule B scales risk of weaker instruments down by 5-10×: GBPUSD drops to 0.18%, US30 to 0.38%, GBPJPY to 0.52%, XAUUSD to 1.00%, USDJPY stays at 2%. Average portfolio risk per trade is ~0.82% vs Rule A's 2%. The P(pass) gap is therefore dominated by LOWER OVERALL RISK, not smart re-weighting. Rule A's P(DD breach) = 12.75% vs Rule B's 0.45% makes this obvious.

A fairer comparison would equalise total risk spent per month. Rule B at its current scaling is closer to a 1%-risk-equivalent allocation — and Q-7 shows 1% risk on FTMO already gives very high P(pass). The Kelly scaling's marginal contribution over a uniform-1% baseline is likely 1-3pp, not 13pp.

**Limitation**: Per-instrument R-pools are synthesised from XAUUSD magnitudes; real per-instrument R-distributions may differ. This analysis is suggestive, not definitive. To confirm, rerun with real per-instrument trade records once batch JSON is extended.

---

## Q-11.2 — JPY Basket Cross-Currency Signal

**Basket construction:** basket = -0.5 * (USDJPY_ret + GBPJPY_ret). Positive basket = yen strength.

Sign convention: yen strength (basket > 0) should predict USDJPY DOWN next day, so a useful signal produces NEGATIVE correlation between basket and next-day USDJPY return.

### Daily horizon
- **n observations:** 67
- **Correlation (3-day basket -> next-day USDJPY):** -0.0845
- **Correlation (1-day basket -> next-day USDJPY):** -0.1127
- **Correlation (3-day basket -> next-day GBPJPY):** +0.0113
- **Sign-agreement accuracy:** 56.7%  (sign(-basket_3d) vs sign(next_usdjpy), n=67)
- **Binomial p-value (vs 50%):** 0.3284

### Intraday horizons
- **H4 basket -> next-H4 USDJPY:** corr = -0.0575  (n=424)
- **H1 basket -> next-H1 USDJPY:** corr = -0.0061  (n=1702)

**Signal strength:** 3-day basket sign-agreement 56.7% with p=0.328 — NOT statistically significant.

**Interpretation:**
- No meaningful signal (|r|=0.085). The JPY basket is essentially uncorrelated with next-day USDJPY at this horizon in the 2026 sample.
- Intraday horizons produce r=-0.057 (H4) and r=-0.006 (H1), consistent with H-11.2's expectation that shorter horizons are noisier.
- Sample is only ~70 daily obs. Replication on 2023-2024 would raise confidence.

---

## Q-11.3 — Dynamic Instrument Selection

Strategy A (hottest-only) vs Strategy B (coldest) vs Strategy C (round-robin equal-weight).
Each strategy gets 50 trials at 600 trades per trial.

| Rule | mean R | mean R sd | WR | WR sd |
|---|---|---|---|---|
| hottest | +0.2511 | 0.1003 | 0.698 | 0.0543 |
| coldest | +0.0915 | 0.0492 | 0.587 | 0.0269 |
| equal | +0.1313 | 0.0473 | 0.618 | 0.0204 |

**Paired t-test (hottest vs equal):** t=+9.629, p=0.0000.

**Raw result:** HOTTEST outperforms equal by +0.1198R per trade (p=0.000).

**Critical caveat:** This result is dominated by *pool-selection bias*, not regime-momentum. Because each instrument has a *static* underlying WR and USDJPY's WR (75.8%) is permanently higher than peers, the rolling-20 WR ranks USDJPY at the top almost always after warm-up. 'Hottest' therefore collapses into 'trade USDJPY heavily' — effectively the same as a Kelly-weighted allocation (Rule B in Q-11.1).

**Corrected verdict:** the test as designed is degenerate — it cannot distinguish 'genuine regime momentum' from 'pick the highest-WR instrument'. To test regime-momentum properly, we would need either (a) regime-shifted R streams (hot periods vs cold periods for the same instrument), or (b) real per-instrument trade records where WR is measured dynamically rather than baked in. Without that, the signal here is a restatement of Q-11.1 Kelly-weighting.

**H-11.3 outcome:** UNDECIDABLE on this synthesised data. The test needs real data to produce a clean answer.

---

## Q-11.4 — Correlation Stability

**D1 returns:** 69 overlapping days across 5 instruments.
**Vol regime:** XAUUSD 14-day |ret| mean. Cutoff = 2.632% (p80).
- High-vol days: 12  (top 20%)
- Low-vol days: 44

### Full-sample correlation matrix

| pair | r_full | r_low | r_high | delta | Fisher z | Fisher p | jumped |
|---|---|---|---|---|---|---|---|
| XAUUSD/US30 | +0.248 | +0.133 | +0.560 | +0.427 | +1.36 | 0.175 | YES |
| XAUUSD/USDJPY | -0.210 | -0.324 | +0.123 | +0.446 | +1.25 | 0.212 | YES |
| XAUUSD/GBPJPY | +0.202 | +0.017 | +0.602 | +0.584 | +1.84 | 0.065 | YES |
| XAUUSD/GBPUSD | +0.416 | +0.366 | +0.678 | +0.312 | +1.20 | 0.230 | YES |
| US30/USDJPY | -0.139 | -0.228 | +0.162 | +0.390 | +1.07 | 0.283 | YES |
| US30/GBPJPY | +0.214 | +0.167 | +0.506 | +0.338 | +1.05 | 0.292 | YES |
| US30/GBPUSD | +0.348 | +0.375 | +0.491 | +0.115 | +0.39 | 0.699 | no |
| USDJPY/GBPJPY | +0.528 | +0.468 | +0.731 | +0.263 | +1.15 | 0.250 | YES |
| USDJPY/GBPUSD | -0.636 | -0.739 | -0.301 | +0.438 | +1.73 | 0.083 | YES |
| GBPJPY/GBPUSD | +0.320 | +0.249 | +0.430 | +0.181 | +0.56 | 0.577 | no |

**Largest correlation shift:** `XAUUSD/GBPJPY` delta = +0.584 (low=+0.017 -> high=+0.602, Fisher p=0.065).

**Pairs that jumped (|delta| >= 0.20):** 8 / 10

**Stress correlation risk: REAL.** Multiple pairs show large correlation jumps between low-vol and high-vol regimes. Concurrent positions during high-vol days carry hidden correlation exposure — a +0.3 static correlation can become +0.7 in stress, making simultaneous stops much more likely.

**Practical takeaway:** during high-vol regimes, the `correlation exposure` check in the emergency-stops list (>2% simultaneous) should treat existing correlation estimates as a LOWER bound — effective correlation during stress can be materially higher.

---

## Reviewer correction 2026-04-17 — iso-risk clip bug (MAJOR)

**Reviewer finding:** Original B_norm first scaled Kelly-weighted risks so the uniform mean equalled 2%, then CLIPPED any cell above 3%. USDJPY's post-scale value was ~5%, so it bound at 3% — but the other cells were left unchanged. Result: the post-clip uniform mean was ~1.62% (not 2%). Rule B_norm therefore combined 'Kelly re-weighting' with a 'hidden ~38 bp risk reduction', and the original +8.32pp P(pass) gap was partly risk-level artefact.

**Correction procedure (pre-registered before re-running):**
1. Scale raw Kelly risks by constant so pre-clip uniform mean = 2%.
2. Clip at 3%.
3. Iteratively re-scale the UNCLIPPED cells so post-clip uniform mean = 2.00% exactly. Stop when no new cell binds.
4. If all cells bind at the cap, fall back to uniform 2% (no feasible correction).

**Corrected per-instrument risk (post-clip uniform mean = 2.000%):**

| Symbol | Original B_norm (buggy) | Corrected B_norm_corrected |
|---|---|---|
| XAUUSD | 2.455% | 3.000% |
| US30 | 0.933% | 1.407% |
| USDJPY | 3.000% | 3.000% |
| GBPJPY | 1.277% | 1.926% |
| GBPUSD | 0.442% | 0.667% |

**Corrected P(pass) vs Rule A:**

- Rule A (equal 2%, uniform traffic): P(pass) = 80.98%, P(DD breach) = 12.75%
- Rule B_norm (BUGGY, post-clip mean = 1.62%): P(pass) = 89.30%, delta vs A = +8.32pp
- Rule B_norm_corrected (iso-risk post-clip mean = 2.00%): P(pass) = 85.29%, delta vs A = +4.31pp

**Headline delta change:** original +8.32pp → corrected +4.31pp (difference = +4.01pp, the portion that was risk-level artefact).

**Corrected H-11.1a verdict:** delta_Bnorm_corrected_A = +4.31pp — remains >= 2pp → CONFIRMED. PROMOTE-to-shadow retained but headline magnitude is smaller than originally reported.

Trade data unchanged; only the scaling arithmetic was corrected. The original buggy numbers above are retained in-place so reviewers can see the trail.

---

## Caveats

1. **Per-instrument R-distributions synthesised, not measured.** Only XAUUSD has real trade records in the batch JSON. Non-gold pools are built using XAUUSD win/loss magnitudes scaled to each instrument's validated WR. Real per-instrument R distributions may have different magnitudes.
2. **Small sample (70 daily obs)** for JPY basket + correlation-stability analysis. CIs on correlations are wide; Fisher-Z p-values should be treated as directional not definitive. Replication on 2023-2024 history recommended.
3. **GBPUSD observer-only** — WR=55% is a neutral default, not a validated number. Excluded from 'gold-solo' reasoning.
4. **No intraday-concurrent positions modelled.** The allocation MC assumes sequential trades. The system can hold up to 3 concurrent positions, which changes the effective risk per equity slot. A more complete MC would model concurrent exposure and correlation jointly.
5. **Dynamic selection synthesised with i.i.d. draws.** By construction, there are no autocorrelated streaks. If real instruments have momentum, dynamic selection could win on real data. Rerun with real per-instrument trade records for proper test.
6. **Vol-regime cutoff at p80 is arbitrary.** Alternative definitions (ATR-based, realized-vol, VIX-based) could reorder regime membership.
7. **2026 regime only.** The correlation-jump finding is sample-specific; regimes dating from pre-2022 (low rates) may show different correlation dynamics.

---

## Verdicts

- **H-11.1a** (Kelly-scaled iso-risk beats equal by >=2pp): delta_Bnorm_corrected_A=+4.31pp (ORIGINAL buggy: +8.32pp) — **CONFIRMED**. (Raw-Kelly Rule B shows +13.59pp but that is mostly a risk-level artefact, not re-weighting.)
- **H-11.1b** (Gap <5pp): |delta_Bnorm_corr|=4.31pp, |delta_CA|=1.68pp — **CONFIRMED**.
- **H-11.2** (JPY basket signal |r|>=0.15, p<0.05 at 1d): |r_3d|=0.085, p=0.328 — **REJECTED**.
- **H-11.3** (Hottest UNDERPERFORMS equal): delta=+0.1198R/trade, p=0.000 — **UNDECIDABLE** (synthesised pools bake in static per-instrument WR; 'hottest' degenerates to 'always USDJPY'. Needs real per-instrument trade records).
- **H-11.4** (>=3 pairs jump |delta|>=0.20): 8/10 pairs jumped — **CONFIRMED**.

## Next Steps

1. **Instrument batch tagging.** Extend `unified_trades_v2` to include `symbol` field so future per-instrument analyses don't need synthesis.
2. **Replicate JPY basket on 2023-2024.** Current sample is 70 days; replication on 2+ years of daily data needed before any deployment decision.
3. **Implement correlation-exposure monitor** that switches between static and stress-regime correlations based on rolling XAUUSD ATR. Adjust concurrent-position cap dynamically.
4. **If real per-instrument trade records become available:** rerun Q-11.1 allocation MC with measured R-distributions; the current synthesis may overstate or understate the Kelly-weighted edge.
5. **WF-2 candidate:** USDJPY basket-gate as secondary filter (observation-only shadow log first). Flag that shortly-running symbols like GBPUSD observer should not be weighted up until validated.
6. **Dynamic selection on real data.** Current null result may be an artefact of i.i.d. synthesis. Even if real data shows hot streaks, the selection lag (~20 trades) likely negates them. Re-test with real streams.

---

*Generated: 2026-04-17 10:36:20*
*Script: `research/academic_pipeline/scripts/q_11_portfolio.py`*