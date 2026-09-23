# WF-2 SHADOW GATES — Review July 7, 2026
# Version 2 — Updated 2026-04-06 after codebase investigation
# SUPERSEDES previous version

## DO NOT IMPLEMENT BEFORE JULY 7

---

## ELIMINATED CANDIDATES (already implemented)

These were promoted as priority actions but the codebase already has them:

| Finding | Why eliminated |
|---|---|
| Body-close BOS filter | Code uses `c["close"]` not highs/lows — src/components/market_state.py:187+ |
| ATR-scaled SL | SL = max(zone_dist, $10, 1.5 × M15 ATR) — src/components/m5_refinement.py:331+ |

**Lesson:** Agent 4 now has a mandatory codebase cross-reference step to prevent this.

---

## 2026 DECAY — MONITORING FRAMEWORK

WR dropped 70.5% → 59.5%, MFE collapsed 1.53R → 1.10R (p=0.0005).
SL and BOS are ruled out as causes. Four hypotheses remain:

### Hypothesis 1: ATR multiplier insufficient
Gold vol doubled. SL scales via 1.5× ATR, so SL doubled too. But if vol
*character* changed (spikes, V-reversals vs trending), 1.5× may not be enough.
**Monitor:** Compare average SL distance ($) and stop-hit rate for ATR-floored
vs zone-based trades, 2025 vs 2026.

### Hypothesis 2: Confidence inversion drives selectivity drift
Trade rate rose 25% → 32%. If the extra trades are disproportionately
HIGH-confidence (which lose at 46% vs LOW at 75%), the confidence scorer
is actively selecting worse trades in high-vol regimes.
**Monitor:** Weekly confidence distribution + WR by confidence bucket.
**Pre-test:** Run confidence-selectivity correlation from existing data (WP2 Task 3).

### Hypothesis 3: Regime change (trending → corrective)
OB retests work in trending markets. If gold shifted to choppy/corrective,
the edge shrinks regardless of parameters. This is SWOT weakness #1.
**Monitor:** Classify months by trending/ranging (ADX or directional run length),
compare WR within each regime type.

### Hypothesis 4: Mean reversion to true WR
70.5% was above the true rate. 59.5% is closer to reality. Blended = ~65%,
exactly what the system claims. Maybe nothing is broken.
**Monitor:** If WR stabilizes at 60-65% through WF-1, this is the answer.

---

## ACTIVE WF-2 CANDIDATES

| # | Change | Gate to pass | Current evidence | Confidence |
|---|---|---|---|---|
| 1 | TP optimization toward 2.5-3R | Shadow TP data shows 3R outperforms current TP on WF-1 trades (out-of-sample) | In-sample only: +24.1R on 367 trades | 25% |
| 2 | Kill session_sweep | n≥20 and WR still below 40% | 22% WR at n=9 (Wilson CI [3%, 56%]) | 50% |
| 3 | Friday filter (gold only) | n≥30 gold Fridays, still significantly negative on both WR and R-multiple | -1.80R at n=19 gold-only | 30% |
| 4 | Strip confidence scoring | WF-1 confirms it remains noise (r < 0.05) | r=-0.02, grade inversion confirmed | 70% |
| 5 | MAE early exit | First-3-candle MAE proves predictive (r>0.3, p<0.01) | Lifetime MAE is tautological | 10% |
| 6 | ATR multiplier increase | Stop-hit analysis shows 1.5× is insufficient in current regime | Not yet tested | 30% |

---

## SHADOW DATA TO COLLECT DURING WF-1

On every trade, log (all prefixed `shadow_`, no decision impact):

1. **ATR at entry:** `shadow_atr_14`, `shadow_atr_50`, `shadow_sl_as_atr_multiple`
2. **Alternative TP outcomes:** `shadow_tp_1R_hit` through `shadow_tp_3R_hit`
3. **Early MAE:** `shadow_mae_candle_1`, `shadow_mae_candle_2`, `shadow_mae_candle_3`
4. **Weekly trade rate:** `shadow_weekly_trade_rate`, sessions traded / total sessions
5. **Confidence distribution:** already logged, just track weekly

---

## CONFIRMED FINDINGS (implement at WF-2, no gate needed)

- **Confidence scoring is noise** — r=-0.022, inverted grade paradox. Strip from prompt.
- **NQ/indices claims don't transfer to gold** — Asian sweep (45.4%), FVG freshness (p=0.54). Permanent KB entry.
- **Parameters are robust** — no overfitting detected, max 1.1pp sensitivity.
- **Execution delay is tolerable** — zone matters, not exact timing.
- **Session performance is equal** — London 65.4% ≈ NY 65.7%. KB corrected.

---

## REVIEW PROTOCOL AT WF-2 BOUNDARY

1. Pull all shadow_ fields from WF-1 trade records
2. Run each decay hypothesis test
3. For each candidate, check its gate
4. Implement no more than 3 changes at once
5. Prioritize by confidence × expected R impact
6. **Before implementing anything, grep the codebase to confirm it's not already there**
