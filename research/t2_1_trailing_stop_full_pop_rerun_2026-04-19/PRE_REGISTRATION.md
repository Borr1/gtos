# T2.1 Trailing Stop Full-Population Rerun — Pre-Registration

**Date:** 2026-04-19
**Analyst:** Claude Code (Opus 4.7)
**Status:** Hypotheses frozen BEFORE examining variant results.

## Context

- CLAUDE.md "canonical numbers" cites batch population = 367 trades.
- After dedup of all three batch sources used by q62/q65 (`batch_api/*_results.json` + `analysis/unified_trades_v2_*.json` + `analysis/phase1_all_trades_merged.json`), the current merged batch universe is **336 unique trades** (318 from batch_api + 111 unified overlap + 18 phase1 carriers, dedup'd by trade_id / synth key). Symbol attribution is recovered by scanning each batch's `full_prompts.json` for the first-mentioned instrument token (XAUUSD/US30/USDJPY/GBPJPY/GBPUSD/EURUSD/NAS100/XAGUSD).
- Data gap note: the "367" figure in CLAUDE.md was coined before subsequent dedup / cleanup of batch sources. The 336 figure is the current canonical batch KB. This is NOT a fabrication — the full universe is reproducible from on-disk sources.
- Apr 6 (`45da076`) n=100 found Trail 0.5R after 0.5R MFE → +52.4R cumulative. Apr 7 (`decfecb`) n=100 across 2024-2026 refined that to ~+0.40R/trade mean. Full-pop was dispatched Apr 7–8 but the output was lost (handoff 07). This is the redo.

## Data columns used

Required per-trade (all present in the merged universe):
- `r_multiple` — realized R under current "100% at TP1" baseline
- `mfe_r` — max favorable excursion in R units, intra-trade peak
- `mae_r` — max adverse excursion in R units (for DD / hurt metric)
- `outcome` — WIN / LOSS
- `direction` — LONG / SHORT
- `framework` — ob_retest / session_sweep / breaker_retest (stratification)

Symbol is recovered at the **batch** level (one batch = one instrument) and
joined onto each trade via the `trade_id` → batch-id mapping.

## Approximation — no per-bar OHLC

The merged universe carries **MFE in R-units** (aggregated intra-trade peak), not a per-bar R path, for ≥95% of trades (18/336 carry `r_path`). Any trailing-stop backtest that requires bar-by-bar monotone trailing cannot be computed exactly from MFE alone, because the trail needs to know whether MFE was hit *before* the trade reversed, and by how much price retraced AFTER the trail was armed.

**Simplifying assumption (documented):**

- `mfe_r` is the highest R the trade reached. If `mfe_r ≥ activation_R`, the trail arms at `(mfe_r − trail_distance_R)` on the *peak* bar. The trade then exits at the better of either:
  - the trailed stop level (if price retraced back to it before hitting TP), or
  - TP (if price hit TP without retracing to the trailed stop).

- To decide that, we use the realized `r_multiple` as a proxy for retrace behavior:
  - If the baseline closed at TP (i.e., realized R == planned TP R), assume the trail was not hit → exit = TP = realized R.
  - If the baseline did NOT hit TP (realized R < planned TP R), assume price retraced at least back to the baseline exit → exit = max(baseline_R, peak_R − trail_distance_R) if that exit > activation level, else baseline.

This is an **upper-bound / optimistic** approximation when the trail would have locked in gains before the baseline exit, but a **lower-bound** when bar-level retracement would have hit the trail before a larger realized gain. For this rerun we adopt the Apr 6 `45da076` convention: **exit = peak − trail_distance** on any trade where `mfe_r ≥ activation_R`, capped at the baseline realized R if the baseline was a winner ≥ the trail exit. This matches the prior study's approach and is stated as an approximation in the verdict.

For the 18 trades with `r_path`, exact simulation is done.

## Variants (locked before seeing per-variant results)

| Variant | Activation R | Trail distance R | Notes |
|---------|--------------|------------------|-------|
| V0 baseline | — | — | Current live: 100% close at TP1 (realized `r_multiple`) |
| V1 | 0.5 | 0.5 | Trail 0.5R behind once MFE ≥ 0.5R |
| V2 | 0.5 | 1.5 | Trail 1.5R behind once MFE ≥ 0.5R (looser, Apr-6 winner) |
| V3 | 1.0 | 0.5 | Trail 0.5R behind once MFE ≥ 1.0R (tighter activation) |
| V4 | 1.0 | — | BE-only (+1R activates move SL to breakeven, no further trail) |

## Hypotheses (frozen before running)

- **H0_v1**: V1 (0.5/0.5) does NOT beat baseline expectancy by >0.15R/trade.
- **H0_v2**: V2 (0.5/1.5) does NOT beat baseline expectancy by >0.15R/trade.
- **H0_v3**: V3 (1.0/0.5) does NOT beat baseline expectancy by >0.15R/trade.
- **H0_v4**: V4 (1.0/BE) does NOT beat baseline expectancy by >0.15R/trade.
- **H0_hurt_v1**: V1's `hurt-trade count` (trades where variant closed at R < baseline R) is not more than 20% of the total traded population.
- Assume no stratification survives — declare per-instrument splits descriptive, not significance-testing.

## Significance discipline

- Bonferroni on 4 variants → α_corrected = 0.05 / 4 = **0.0125**.
- Paired Wilcoxon signed-rank on per-trade Δr.
- 10 000-resample bootstrap CI on mean Δr (seed 20260419).
- Wilson CI for WR.
- n ≥ 20 per variant; if MFE-gated n < 20, variant is reported as "underpowered" and excluded from promotion consideration.

## Decision rule (pre-registered)

**Promote** to a deployment RFC iff all of the following hold for at least one variant:

1. Mean Δr > +0.15 R/trade
2. Bootstrap 95 % CI lower bound > 0
3. Wilcoxon p < 0.0125 (Bonferroni)
4. Max 20-trade rolling Δr drawdown ≥ −5 R (i.e., variant doesn't add big losing streaks)
5. Hurt-trade count ≤ 25 % of MFE-eligible trades

Else: **reject** (baseline stays), or **more data** if the only blockers are n.
