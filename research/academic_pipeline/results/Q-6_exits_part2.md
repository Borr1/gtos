# Q-6.2 / Q-6.6 — Exit Engineering Part 2 (Partial Splits + Overnight Risk)

- Script: `research/academic_pipeline/scripts/q_6_exits_part2.py`
- Data: `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json`
- n = 111 trades (batch, XAUUSD only)
- Seed: 42 | Bootstrap iters: 5000
- Baseline for Q-6.2 bootstrap: **B_50_25_25 (current live-equivalent)**

## Hypothesis (pre-data, pre-registered)

- **Q-6.2**: Current live split (50/25/25 at 1R/2R/3R) is NOT optimal. Given wave-1 finding that 35.62% of winners give back ≥0.5R between MFE and close, optimum should concentrate close mass at TP1. Predicted ranking (best→worst): **F(50/50/0) ≥ A(100/0/0) > C(60/20/20) > B(50/25/25 baseline) > D(40/30/30) > E(33/33/34)**.
- **Q-6.6**: Gold has documented asymmetric overnight risk (Caporale 2014, Lucey 2014). Predicted: intra-session > cross-session > overnight on avg_R. Overnight bucket will show **left-skewed** r_multiple distribution (skew < 0) and a Kruskal-Wallis p<0.05 for distributional heterogeneity across the three buckets.

## Data & Method

- n = 111 trades (XAUUSD only, batch 2024-04 → 2026-03).
- Fields: `r_multiple`, `mfe_r`, `mae_r`, `hold_time_candles`, `kill_zone`, `date`, `day_of_week`.
- **TP level assumption (Q-6.2)**: we use canonical TP1=1R, TP2=2R, TP3=3R. Per-trade `take_profit_1/2/3` prices exist but translate inconsistently to R (they were in some cases static price ladders that did not match the realized SL distance). Using R multiples keeps the analysis continuous with wave-1.
- **Intracandle ordering (critical)**: we cannot know whether MFE or MAE hit first within a candle. We adopt wave-1's conservative gate: `was_stopped = (mae_r>=1.0 AND r_multiple<=-0.95)`. Stopped trades always realize -1R, even if MFE also touched a TP. This UNDER-counts TP hits on SL days, biasing expectancy DOWN for high-TP1-weight variants. Any observed win for early-close variants is therefore a conservative lower bound.
- **Bucketing (Q-6.6)**: inferred from kill_zone + hold_time_candles (no entry/exit timestamps in batch). Thresholds in UTC clock terms:
  - London KZ (07:00-10:30 UTC): intra ≤ 14c; cross ≤ 40c (to 17:00 UTC, NY close); overnight > 40c (past NY close into Asian).
  - NY KZ (13:00-17:00 UTC): intra ≤ 16c; cross ≤ 28c (to 20:00 UTC, pre-Asian); overnight > 28c (past 20:00 UTC → into Asian session).
  - Bucket assignment is a proxy. Accurate classification requires entry/exit timestamps — a known data gap, flagged.

## Q-6.2 Results — Partial-close variant comparison

### Variant expectancy table (all n=111)

| Variant | Fractions (TP1/TP2/TP3) | Expectancy (R) | WR | Median R | Sum R | Std R | Median max-DD (2%) | P95 max-DD (2%) |
|---------|-------------------------|----------------|------|----------|-------|-------|--------------------|-----------------|
| A_100_0_0 | 100/0/0 | **+0.114** | 66.67% | +0.18 | +12.7 | 0.753 | 9.53% | 18.03% |
| B_50_25_25 (baseline) | 50/25/25 | **+0.150** | 66.67% | +0.18 | +16.6 | 0.833 | 9.48% | 17.53% |
| C_60_20_20 | 60/20/20 | **+0.143** | 66.67% | +0.18 | +15.8 | 0.811 | 9.46% | 17.55% |
| D_40_30_30 | 40/30/30 | **+0.157** | 66.67% | +0.18 | +17.4 | 0.856 | 9.54% | 17.58% |
| E_33_33_34 | 33/33/34 | **+0.162** | 66.67% | +0.18 | +18.0 | 0.875 | 9.56% | 17.61% |
| F_50_50_0 | 50/50/0 | **+0.134** | 66.67% | +0.18 | +14.9 | 0.802 | 9.61% | 17.88% |

### Paired bootstrap: Δ expectancy vs baseline B_50_25_25 (seed=42, n_boot=5000)

| Variant | Δ expectancy (R) | 95% CI | p (two-sided boot) | Significant (CI excl 0)? |
|---------|------------------|--------|--------------------|--------------------------|
| A_100_0_0 | -0.036 | [-0.085, +0.010] | 0.136 | no |
| C_60_20_20 | -0.007 | [-0.017, +0.002] | 0.136 | no |
| D_40_30_30 | +0.007 | [-0.002, +0.017] | 0.136 | no |
| E_33_33_34 | +0.013 | [-0.003, +0.029] | 0.132 | no |
| F_50_50_0 | -0.016 | [-0.031, -0.002] | 0.033 | YES |

- **Best variant by point expectancy**: `E_33_33_34` @ **+0.162R/trade** (WR=66.67%, sum=+18.0R over 111 trades).
- Delta vs baseline B_50_25_25: **+0.013R/trade**, 95% CI [-0.003, +0.029], p=0.132 → **NOT significant** at α=0.05.

## Reviewer correction 2026-04-17 — H29 policy was missing (MAJOR)

**Finding:** The Q-6.2 variant expectancy and DD-envelope tables computed each variant's `expectancy` as an unweighted mean of per-trade new-R, implicitly assuming risk_pct is CONSTANT at 2.0%. The `dd_envelope` additionally sampled trades WITH REPLACEMENT in random order — so path-dependence and the Apr 11 2026 **H29 policy** (8% DD -> 0.5% risk until new equity high) are missing from the reported figures.

**Correction (pre-registered BEFORE running):**
- Walk trades in chronological order (by `date`).
- Maintain running equity (init=1.0) and peak-equity.
- Before each trade: if `(peak - equity) / peak >= 0.08` AND not already in DD-mode, switch to risk=0.5%. If already in DD-mode and equity >= peak, reset to risk=2.0%.
- Apply trade: `equity <- equity + r * active_risk * equity` (max 1e-9 floor).
- Track max-DD across the replay.
- Report terminal equity and max-DD for each variant with H29 ON and with H29 OFF (flat 2%).

### H29-corrected terminal-equity replay (chronological, deterministic)

| Variant | terminal_equity (H29 ON) | terminal_equity (flat 2%) | max_DD (H29) | max_DD (flat) | n_trades_reduced | pct_reduced |
|---------|-------------------------:|--------------------------:|-------------:|--------------:|-----------------:|------------:|
| A_100_0_0 | 1.1016 | 1.2718 | 8.40% | 8.67% | 70 | 63.1% |
| B_50_25_25 (baseline) | 1.1449 | 1.3734 | 8.04% | 8.11% | 68 | 61.3% |
| C_60_20_20 | 1.1357 | 1.3527 | 8.04% | 8.11% | 68 | 61.3% |
| D_40_30_30 | 1.1541 | 1.3942 | 8.04% | 8.11% | 68 | 61.3% |
| E_33_33_34 | 1.1608 | 1.4098 | 8.04% | 8.17% | 68 | 61.3% |
| F_50_50_0 | 1.1326 | 1.3278 | 8.04% | 8.11% | 68 | 61.3% |

- **Best terminal equity under H29 policy:** `E_33_33_34` -> 1.1608
- Baseline `B_50_25_25` under H29: 1.1449 vs 1.3734 (flat 2%). H29 triggered on 61.3% of trades; opportunity cost on this path = +22.848pp of final equity.
- **Verdict direction preserved:** same variant (`E_33_33_34`) is best under both H29 and flat-2% sizing.
- E_33_33_34 vs B_50_25_25: delta terminal equity = +0.0159 (H29) vs +0.0364 (flat 2%). Same sign; the underpowered finding from the paired bootstrap is unchanged in direction but magnitude is path-sensitive.

**Interpretation:** H29 is a safety overlay. In the specific chronological path of this batch (2024-04 -> 2026-03), H29 triggers on variants with larger early-loss clusters, reducing terminal equity relative to the counterfactual flat-2% world. This is the EXPECTED cost of carrying a DD brake — it pays for itself only on paths where the drawdown would have escalated to blow-up. A single historical path (n=111) cannot resolve whether H29's opportunity cost exceeds its expected protection; the Monte Carlo at Q-11 does, finding H29 pays for itself in P(FTMO-pass) terms.

## Q-6.6 Results — Session-close / overnight risk buckets

- Bucket counts: intra=39, cross=26, overnight=46, unknown=0.

### Per-bucket statistics

| Bucket | n | avg_R | std_R | WR | Median R | Skew | Kurt (excess) | Min | Max | Mean MFE | Mean MAE | Mean hold (candles) |
|--------|---|-------|-------|------|----------|------|---------------|-----|-----|----------|----------|---------------------|
| intra | 39 | **-0.136** | 0.674 | 66.67% | +0.12 | -0.012 | -0.454 | -1.00 | +1.68 | 0.56R | 0.60R | 7.6 |
| cross | 26 | **-0.150** | 0.802 | 57.69% | +0.15 | +0.182 | -1.238 | -1.00 | +1.37 | 0.88R | 0.72R | 26.4 |
| overnight | 46 | **+0.682** | 1.231 | 69.57% | +0.28 | +1.107 | +0.417 | -1.00 | +3.77 | 1.37R | 0.42R | 49.0 |

- **Kruskal-Wallis** across all 3 buckets: H=11.817, p=0.0027 → REJECT H0 (distributions differ) at α=0.05.

### Diagnostic: exit_substate by bucket (evidence of survivorship confound)

| exit_substate | intra | cross | overnight |
|---------------|-------|-------|-----------|
| CLOSED_BE | 22 (56%) | 10 (38%) | 1 (2%) |
| CLOSED_SESSION_TIMEOUT | 0 (0%) | 0 (0%) | 40 (87%) |
| CLOSED_SL | 13 (33%) | 11 (42%) | 3 (7%) |
| CLOSED_TP3_RUNNER | 3 (8%) | 3 (12%) | 1 (2%) |
| CLOSED_TRAIL | 1 (3%) | 2 (8%) | 1 (2%) |

If the 'intra' bucket is dominated by `CLOSED_SL` and 'overnight' by `CLOSED_TRAIL`/`CLOSED_TP3_RUNNER`/`CLOSED_SESSION_TIMEOUT`, the bucket label is tracking legacy exit rule outcome, not calendar session-crossing. **This is a confound** — see verdict below.


### Pairwise Mann-Whitney U (two-sided)

| Pair | U | p | n_a | n_b |
|------|---|---|-----|-----|
| intra_vs_cross | 480.5 | 0.7209 | 39 | 26 |
| intra_vs_overnight | 550.0 | 0.0022 | 39 | 46 |
| cross_vs_overnight | 376.5 | 0.0093 | 26 | 46 |

## Verdicts

- **Q-6.2**: **E_33_33_34 has highest point expectancy** (+0.013R vs baseline), but the 95% CI [-0.003, +0.029] crosses zero OR delta is <0.05R. **No statistical basis to change the current split.** Keep B_50_25_25.
- **Q-6.6**: **Buckets differ (KW p=0.0027)** but the ordering is **OPPOSITE of the asymmetric-overnight-risk hypothesis**: overnight is BEST (+0.682R, WR=69.57%), intra/cross are near-zero. **This is a survivorship confound, not a risk signal.** The legacy batch exit rule (session-timeout + trail + TP3 runner) couples hold_time to outcome: stopped-out trades exit quickly (→ intra bucket), winners that trail into the next session accumulate long holds (→ overnight bucket). Overnight skew is **+1.107 (right-tailed, winner-heavy)**, not the predicted left-tailed loss-heavy pattern. **Verdict: hypothesis UNTESTABLE with this dataset. No evidence of asymmetric overnight risk in gold — but no evidence against it either.** The proxy is confounded. Requires real entry/exit timestamps to retest.

## Caveats

- **n=111** — small sample. Bootstrap CIs widen quickly. Five of six variants in Q-6.2 produce expectancy estimates within the CI of the baseline; differences are driven by a handful of big-MFE trades.
- **Intracandle ordering** — wave-1's conservative gate under-counts TP hits on SL days and biases toward Batch-style let-it-run rules. Early-close variants (A, F) are likely stronger in production than reported here.
- **Q-6.6 bucketing is a proxy** — derived from KZ + hold_time_candles without entry/exit timestamps. Mis-classification near boundary candles is possible. Fix: add `entry_time_utc` and `exit_time_utc` to the next batch ingest.
- **TP-level assumption** — we use R multiples (1R/2R/3R), not per-trade TP1/TP2/TP3 prices. Some trades had asymmetric TP ladders (e.g., TP1 at 0.7R, TP2 at 1.8R). Re-running with per-trade `take_profit_i` prices and computed `R_at_TPi` would be more precise but requires a price-to-R remapping that wave-1 also chose not to do (for consistency).
- **XAUUSD-only** — US30/USDJPY/GBPJPY batches not yet unified at v2. Q-6.6 overnight asymmetry is most documented for gold; replicate on other instruments when data arrives.
- **No daily-DD modeling** — max-DD envelope uses trade-by-trade compounding at 2% risk, not FTMO daily 5% aggregation.
- **Do NOT confound with wave-1 AltC (trailing)** — this analysis is about split RATIOS only. Adding a trail on the final leg is a separate question (wave-1 Q-6.8 AltC was the winner on expectancy).

## Next steps

1. **Add entry_time_utc / exit_time_utc to batch ingest** → replaces Q-6.6 heuristic bucketing with real session classification. Cheap, high-value.
2. **Run Q-6.2 on US30/USDJPY/GBPJPY/GBPUSD** when those instruments are consolidated into unified_trades_v2.
3. **Shadow-log the best Q-6.2 variant** (if it beats B significantly) alongside the current AltC trail rule — measure combined edge.
4. **Do NOT add a session-close forced-exit rule** based on this result. Q-6.6 found buckets differ (KW p=0.0027), but the effect is a survivorship confound (87% of 'overnight' trades exit via `CLOSED_SESSION_TIMEOUT` — the legacy rule itself), not a real overnight-risk signal. Re-test the hypothesis after 100+ live T7 trades with `entry_time_utc`/`exit_time_utc` recorded.
5. **Cross-check with live T7 data** — the T7 XAUUSD simulation (Jan-Mar 2026) has 7 trades with exact timestamps; too few to replicate but can start building the real timestamped dataset.
