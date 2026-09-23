# TP Optimization Analysis — Session 4
Generated: 2026-03-31

## Data: 101 ob_retest trades with MFE data

## Key Finding: DO NOT CHANGE TP1

The simplified TP models (Model 1: TP1-only, Model 2: TP1 + trailing) both show
NEGATIVE expectancy at every TP1 level tested (0.3R to 2.5R). The "best" is 0.3R
at -0.097R/trade — still negative, and far worse than the actual +0.235R/trade.

**Why the models underperform reality:** The actual system uses a sophisticated
partial-close structure (50% at TP1, 25% at TP2, 25% runner to TP3 or trail) that
cannot be captured by a single-TP model. The 40 session timeout trades average
+0.81R — these are trades that went favorably but didn't hit any fixed TP level,
and the partial-close + trailing mechanism extracted significant value from them.

## Conclusion
The AI-set TP targets with the existing partial-close structure outperform any
fixed TP1 override. The current approach should be preserved as-is.

## Loser MFE Data (for future reference)
- 28 losers total
- 13/28 (46%) had MFE >= 0.3R before reversing to SL
- 9/28 (32%) had MFE >= 0.5R
- 8/28 (29%) had MFE >= 0.8R
- These "near-miss" losers suggest the AI is finding the right direction ~46% of
  the time even on losing trades — the issue is SL placement or timing, not direction.
