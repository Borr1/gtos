# KB2 — Hardened index failed-breakout reversion via cross-sectional risk-off gate (track: idxdeep)

Builds on `KB_index_reversion.md` (track idxrev). Goal: turn the highest-frequency index
reversion pocket (~1050 trades/yr, least-validated, 2024+ only) into a robust larger-size
sleeve by adding a CROSS-SECTIONAL / risk-off filter for the sign-flip symbols.
Status: **IMPROVEMENT** — forward EV up +43% (+0.061 -> +0.087R) with both forward years
now consistent and the sign-flip group repaired, robust to the basket lookback. Still a
confidence-weighted sleeve (NAS100 deep-train negative), not fully train-proven.

Code: `idxdeep_xsec.py` (cross-sectional gate + run/report), `idxdeep_m15.py` (M15 timing test).
Result: `IDXDEEP_XSEC_RESULT.json`. Baseline reproduced exactly (FWD25-26 n=1575 +0.061 w63%).

## Data reality (decides what's testable)
- NAS100 is STILL the only deep index (H4 2022-01+) -> only real TRAIN<=2024.
- Sign-flip symbols start 2025-04 (GER40/US30/JP225) — they have NO 2024 data at all; entirely forward.
- SPX500/AUS200 2025-11+, UK100 2025-04+, US2000 2024-09+, FRA40/EU50 2024-03+, N25 2023-08+.
- M15 exists for all 8 pocket symbols but only 2025-06+ (~12 mo, spans the 25/26 boundary) -> timing
  evidence only, not a holdout (matches KB_index_reversion caution).
- Deep H4 2015-2022 archive has NO indices (FX/metals/oil only) -> no deeper index H4 exists to mine.
- Cost 0.0638 (class index), scaled by 1/stop_atr; net R winsorized [-1.3,+5].

## The decisive finding — fade ONLY AGAINST the basket trend
The diagnostic that fixes the sign-flip symbols. Leak-free cross-sectional basket-trend feature:
for every basket member, normalized signed trend `(close[j]-close[j-lb]) / (ATR[j]*sqrt(lb))` over
the last lb=10 CLOSED bars at-or-before the H4 signal time (binary search; assertion T[j]<=ts<T[j+1]).
`signed` = (n_up - n_dn)/n in [-1,1]; `mean_abs_trend` = how strongly the basket is trending.

Splitting the pocket confirms WHERE the weakness is (baseline, FWD25-26):
- CONSISTENT (SPX500/UK100/US2000/EU50): +0.107R, both years strong.
- SIGN_FLIP  (GER40/US30/JP225):        +0.009R, 2025 -0.006 / 2026 +0.030 (the broken group).

Conditional EV on SIGN_FLIP (FWD25-26):
- fade ALIGNED with basket (d*signed>0): **-0.146R** (when the index over-extends the SAME way the
  herd is going, the breakout is real — fading it loses).
- fade AGAINST basket (d*signed<0):       **+0.027R**, BOTH years positive (+0.024 / +0.030).
- The earlier "ranging/low-trend basket = fade pays" idea is FALSIFIED (same lesson as the ac60 gate):
  basket-flat (mean_abs<=0.3) is the WORST slice (-0.259R). Low trend = pierce is a genuine breakout.

So the gate is DIRECTIONAL, not a range filter: **only fade an index move that goes AGAINST a
trending index basket** (idiosyncratic over-extension that snaps back toward the market).

## LOCKED RULE (the hardened sleeve)
Failed-breakout fade, lb_range=16, stop=1.5*ATR, target=0.75R, maxbars=60 (unchanged geometry), PLUS:
  CROSS-SECTIONAL GATE: take the fade only when d*signed < 0 (fade is AGAINST the basket trend);
  for the sign-flip symbols (GER40/US30/JP225) ALSO require basket mean_abs_trend >= 0.4 (a real
  trend to fade against). Basket = the 9 broad indices, trend lookback lb=10. All leak-free.

- FWD 2025: n=656  R/t=+0.086  win 65%
- FWD 2026: n=519  R/t=+0.089  win 65%
- FWD25-26: n=1175 R/t=+0.087  win 65%  (~810 trades/yr) vs baseline n=1575 +0.061 w63%.
- Per-symbol FWD25-26 (R/t, y25/y26): SPX500 +0.147(.221/.135), UK100 +0.121(.157/.064),
  EU50 +0.132(.079/.270), US2000 +0.102(.124/.065), US30 +0.076(-.043/.211), JP225 +0.055(-.043/.167),
  GER40 +0.054(.237/-.128), FRA40 -0.002(.025/-.066). FRA40 is the one negative-combined symbol.
- Drop FRA40 -> FWD25-26 +0.100R, both years +0.097/+0.103 (cleanest larger-size config).

## Robustness (not a single-parameter artifact)
Basket-trend lookback sync_lb in {5,8,10,14,20}: locked rule = +0.083..+0.099R, BOTH forward years
positive at every lb. Simpler "against-only" (no mabs floor) also robust: +0.068..+0.072R across lb.
The gate keeps ~75% of baseline trades (n 1575->1175) while lifting EV, so it is a true filter, not
a frequency-killing overfit. The improvement appears in BOTH 2025 and 2026 (two separate regimes).

## NAS100 honest comparator (why this stays confidence-weighted)
NAS100 is the only index with real TRAIN<=2024. The against-basket gate IMPROVES it on both splits
(TRAIN -0.096 -> -0.071, FWD -0.054 -> -0.038) — direction of the filter is structurally CORRECT —
but NAS100 stays NEGATIVE. The filter reduces the loss; it does not flip the deep-train sample
positive. So the pocket's positivity is still partly a 2024+ forward-only / single-regime effect.
=> KEEP as a confidence-weighted LARGER sleeve than baseline (the filter de-risks it), but do NOT
size it like a fully train-proven core. Suggested confidence weight ~0.45x (up from idxrev's 0.35x):
effective ~+0.039R/trade x ~810 trades/yr — meaningful, non-correlated (fade-direction) index breadth.

## M15 reclaim-timing — tested, adds nothing (clean learning, not a kill)
`idxdeep_m15.py`: for each gated H4 fade, wait for an M15 reclaim-confirm inside the next H4 window
and enter there instead of the H4 close. Leak-free (M15 bars only after the H4 bar closes). Result
(2025+ matched window): M15-timed +0.076R vs H4-close +0.087R. The H4 close IS already the reclaim
(the bar closed back inside the swept level), so an extra M15 confirm just enters later and gives
edge back. Finding: **H4-close entry is the correct timing for this fade; M15 confirmation does not
improve it** (consistent with KB_index_reversion's "M15 too thin" caution). Revisit once >=18mo M15.

## Next steps (build, don't kill)
1. Promote SPX500/UK100/EU50/US2000 (consistent both years, strong) to a higher size tier inside the
   sleeve; keep GER40/US30/JP225 at base size under the mabs>=0.4 gate; consider dropping/quarantining
   FRA40 until it holds a second clean year.
2. Re-validate each new forward quarter; the gate is directional+leak-free so it can run live as-is.
3. Try a graded size = f(basket trend strength against the fade): larger when |signed| and mean_abs
   are both high (cleanest over-extension), as the per-slice EV rises with a stronger basket to fade.
4. When 2027 H4 lands, re-run the NAS100 honest train check — a positive forward there would let this
   graduate from confidence-weighted to core.
