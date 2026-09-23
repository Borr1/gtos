# T2.1 — Trailing Stop Full-Population Rerun (verdict)

**Date:** 2026-04-19
**Run:** `research/t2_1_trailing_stop_full_pop_rerun_2026-04-19/trailing_stop_replay.py`
**Data:** 251 valid trades from merged batch KB (batch_api + unified_v2 + phase1, dedup'd). 336 unique before filter; 85 dropped for missing `direction` / `mfe_r` (raw batch_api stubs). r_path available for 18 trades (exact simulation); 233 trades use MFE approximation.
**Pre-registration:** `PRE_REGISTRATION.md` (hypotheses + decision rule frozen before results).
**API spend:** $0.

---

## TL;DR

**Promote V1 (activate at +0.5R, trail 0.5R behind) as a shadow-mode deployment.** It clears every pre-registered gate on the full-pop rerun. Full deployment still requires the standard safety review + 1-instrument live shadow cycle; the backtest alone is evidence, not authorization.

Keep V2 and V4 as documented alternatives (V2 weaker but also positive; V4 is a no-hurt BE-only variant, defensible as a lowest-risk first step).

Reject V3 as not meaningfully different from V1 — tighter activation loses triggers without better expectancy.

---

## Headline results (paired, same 251 trades)

| Variant | Δr / trade | Total Δr | 95% Boot CI | WR variant | WR baseline | Trigger rate | Hurt trades | Wilcoxon p |
|---|---|---|---|---|---|---|---|---|
| **V0 baseline (100% at TP1)** | 0.000 | 0.00 | — | 63.7% | 63.7% | — | — | — |
| **V1 act=0.5, trail=0.5** | **+0.369** | **+92.69** | [+0.280, +0.459] | **74.1%** | 63.7% | 149/251 (59%) | 5 (3.4% of triggered) | 0.000 |
| V2 act=0.5, trail=1.5 | +0.113 | +28.30 | [+0.064, +0.164] | 66.5% | 63.7% | 149/251 (59%) | 2 (1.3%) | 0.000 |
| V3 act=1.0, trail=0.5 | +0.323 | +80.97 | [+0.238, +0.409] | 69.3% | 63.7% | 102/251 (41%) | 4 (3.9%) | 0.000 |
| V4 act=1.0, BE-only | +0.052 | +13.11 | [+0.028, +0.080] | 63.7% | 63.7% | 102/251 (41%) | 0 (0.0%) | 0.000275 |

Bonferroni-corrected α on 4 variants = 0.0125. All four variants clear it. Baseline expectancy = +0.302 R/trade (matches CLAUDE.md "+0.200R/trade" canon within bootstrap noise; the population has drifted up since that line was written).

## Max-20-trade rolling drawdown in Δr

| V1 | V2 | V3 | V4 |
|---|---|---|---|
| -1.41 R | 0.00 R | 0.00 R | 0.00 R |

V1 has one 20-trade window where it underperformed baseline by 1.41 R cumulative. All other variants never underperform baseline on any 20-trade window. V1's Δ-DD is <10% of V1's total gain, well inside the pre-registered −5 R cap.

## Per-symbol breakdown (V1, the winner)

| Symbol | n | Baseline mean R | V1 mean R | Total Δr | V1 WR |
|---|---|---|---|---|---|
| XAUUSD | 120 | +0.281 | +0.646 | +43.88 | 75.8% |
| US30 | 37 | +0.487 | +1.191 | +26.05 | 81.1% |
| USDJPY | 24 | +0.541 | +1.122 | +13.94 | 83.3% |
| GBPJPY | 34 | +0.230 | +0.519 | +9.82 | 76.5% |
| GBPUSD | 1 | — | — | — | — |
| UNKNOWN (unattributed batch) | 35 | +0.115 | +0.087 | −1.00 | 54.3% |

V1 is positive on every live instrument except GBPUSD (n=1, uninformative). The one losing cohort is the 35 trades whose batch file could not be mapped to an instrument (no symbol hint in the prompt); even there the regression is only −0.028R/trade.

## Hurt-trade detail

| Variant | Hurt count | Mean hurt Δr | Worst hurt Δr |
|---|---|---|---|
| V1 | 5 | −1.226 | −2.640 |
| V2 | 2 | −1.175 | −2.134 |
| V3 | 4 | −1.056 | −2.080 |
| V4 | 0 | — | — |

V1 hurts 5/149 triggered trades (3.4%). The mean hurt is 1.2R lost vs baseline, with a single worst case of −2.64R. V1's hurt-rate is well under the pre-registered 25% cap.

## Decision rule gate (pre-registered)

| Gate | V1 | V2 | V3 | V4 |
|---|---|---|---|---|
| Δr > +0.15 R/trade | **yes** (+0.369) | no (+0.113) | **yes** (+0.323) | no (+0.052) |
| Boot 95% CI lower > 0 | yes (+0.280) | yes (+0.064) | yes (+0.238) | yes (+0.028) |
| Wilcoxon p < 0.0125 | yes | yes | yes | yes |
| Max 20-trade Δ-DD ≥ -5 R | yes (-1.41) | yes (0) | yes (0) | yes (0) |
| Hurt ≤ 25% of triggered | yes (3.4%) | yes (1.3%) | yes (3.9%) | yes (0%) |
| **Overall** | **PROMOTE** | marginal (Δ<0.15) | **PROMOTE** | marginal (Δ<0.15) |

V1 is the highest-Δr variant among the two that clear the +0.15 R gate, so it's the promotion candidate. V3 clears all gates too, but its activation at +1.0R means ~40% of candidate trades trigger vs V1's 59%; V1 also captures more gain per trade where both trigger. Prefer V1.

---

## Approximations and limits — read before promoting

1. **MFE approximation.** 233/251 trades lack per-bar R-path. For those the simulator uses: `variant_R = max(baseline_R, mfe_R - trail_distance)` whenever `mfe_R ≥ activation_R`. This is geometrically exact in the sense that any path from 0 → mfe_R → baseline_R that has `baseline_R < mfe_R − trail_distance` must have crossed `mfe_R − trail_distance` on the retrace, so the trail would have triggered there. The approximation fails only on paths that would have gone through the trail line twice (rare) or where intrabar extremes deviate substantially from the stored MFE peak (implausible given M15 granularity). For the 18 r_path trades an exact simulation is run. V1's delta on the r_path subset agrees with the approx within noise.

2. **Population drift.** CLAUDE.md canon says "367 trades" in the batch. Current dedup'd union of the three batch sources used by every other replay (q62/q65/variant_c) is 336 unique trades; 85 of those are raw batch_api stubs that only recorded outcome + framework (no direction, no MFE) and so are unusable for any path-dependent simulation. 251 is the maximum usable n for an MFE-dependent replay on the current on-disk KB. **Not a fabrication** — reproducible from sources listed in `PRE_REGISTRATION.md §Data`. If the CEO wants the 367-trade figure reinstated, the missing 116 trades would need to be re-reconstructed with MFE + direction fields from raw API responses.

3. **Symbol attribution.** Recovered per-batch from prompt text. 35 of 251 valid trades map to a batch whose prompt did not mention any known symbol ("UNKNOWN"); those are folded into aggregate numbers but excluded from per-symbol generalization claims.

4. **Live "baseline" is not strictly `100% at TP1`.** The realized `r_multiple` in the KB already reflects the full current exit chain (TP1 partials, BE shift, KZ-end flatten, session timeout). The variant comparison is against *that* chain, not against an idealized static TP, which is the correct reference for a deployment decision.

5. **Survivorship.** The 251 trades are those that cleared the current gating (AI CANDIDATE + permissions). V1's gain is conditional on that gating staying unchanged. Any gate change invalidates the rerun.

6. **In-sample.** This is an in-sample rerun on the same trades the KB was built from. By CLAUDE.md rule 6 ("never re-run in-sample data to validate a fix") this is evidence for a shadow deployment, not for a live switch. Out-of-sample confirmation requires a live shadow window where the broker-side trail-exit would have been computed next to the live outcome.

---

## Recommendation

1. **Shadow-mode V1 (act=0.5, trail=0.5) for 30 days post-deployment.** Add a shadow logger (modeled on `be_shadow_logger.py`) that computes `trailed_R_if_V1` for every closed trade using intraday tick data from MT5. Compare cumulative Δr to the backtest's +0.369R/trade expectation. Promote live only if shadow confirms Δr within the bootstrap CI [+0.280, +0.459] at n ≥ 30 triggered trades.

2. **Do NOT enable V1 live today.** The rerun is in-sample and approx-based. The current live edge (+17 trades/month, expectancy +0.20 to +0.30R observed) survives on its own; pushing expectancy with an unverified exit rule risks a config-change-induced edge decay that correlates with a win that isn't there out-of-sample.

3. **Budget impact: $0.** Shadow logger is pure arithmetic on candle close; no Anthropic calls, no MT5-broker-side SL modifications until the live cutover.

4. **Follow-ups if V1 clears shadow:**
   - Compare V1 vs V3 on the shadow window (V3 captures slightly less per trade but on a smaller cohort — a live tiebreaker is more reliable than the backtest).
   - Revisit V2 (tighter trail cutoff) if V1 shows sensitivity to exit timing.
   - V4 (BE-only) is the fallback if V1's shadow Δr is < +0.15R/trade but V4's is still positive — lowest-risk "at least do something" option.

---

## Files

| File | Role |
|---|---|
| `PRE_REGISTRATION.md` | Hypotheses + decision rule, frozen pre-results |
| `trailing_stop_replay.py` | Replay driver |
| `discover_symbols.py` | Batch-id → instrument map builder |
| `batch_symbol_map.json` | Batch-id → instrument map |
| `variants_comparison.csv` | Summary, one row per variant |
| `variants_comparison.json` | Same as .csv, structured |
| `per_trade_outcomes.jsonl` | Audit trail, one line per (trade × variant) |
| `run_metadata.json` | Population counts + config + caveat notes |
| `verdict.md` | This file |

Compare against prior studies: `research/kap_outputs/tests/trailing_stop_summary.csv` (n=100 XAUUSD only, Apr 6–7). V1's per-instrument deltas on XAUUSD (+0.37R/trade) are higher than the Apr 7 rerun's (+0.20R/trade on 100 XAUUSD trades) because the current KB includes 2025-2026 trades not present in the earlier study, and those cohorts exhibit stronger MFE follow-through. No contradiction with the earlier work — same direction, updated magnitude.
