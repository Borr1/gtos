# KB cycle 74 — the next-level search verdict: STRUCTURAL beats PREDICTIVE (per-trade outcome is unpredictable)

Next-level geometry Workflow (wf_85847b95-57b, 282 trials, oracle-first, both sleeves, vs the FLAT DEEP-TARGET
baseline). Verdict: CONFIRMED_REAL = []. The deep target stands as the lone robust breakthrough.

## THE DECISIVE META-FINDING
Across cycle 69 (reach-selection) AND all 4 next-level cells, every PREDICTION-CONDITIONED policy FAILS or
deflates, while the ORACLE ceilings are LARGE. The latent (which trade runs / how far) genuinely EXISTS at the
per-trade level — but it is NOT forecastable from decision-bar features out-of-sample:
- **regime_conditional_depth:** oracle sealed +0.74 (and fixes the bear/chop years), but a realistic
  decision-bar regime gate is WORSE than flat (metals sealed −0.092 p=0.79, equity −0.172 p=0.997).
- **adaptive_target_mfe:** oracle sealed +3.3, but MFE is UNPREDICTABLE — sealed Ridge R² is NEGATIVE
  (−0.06 metals, −0.03 equity); realistic policy LOSES to flat (−0.19/−0.12).
- **stop_by_mae:** oracle ~7× (the c66 dead-width is real), but the realistic tighten is LEAK_OR_OVERFIT /
  within-noise (borderline p~0.10, vanishes at 282-trial deflation; 2026-only; win-rate 0.13).
- **size_by_regime:** fails overall — equity 0/2 years (sealed −0.04, p=0.62); metals-only partial
  (htf_slope sizing +49% wmeanR, p=0.0011, 2/2 yrs, Sharpe 0.21→0.25, pass 0.83→0.85) BUT maxDD WIDENS
  +7.75pp (concentrates tail risk) → a regime-dependent leverage tradeoff, not a robust cross-sleeve edge.

## INTERPRETATION (deep + decisive)
The metals/equity momentum edges are **outcome-memoryless at the decision bar**: positive EV is known (the
edge), but WHICH trade becomes the big runner is essentially unpredictable from decision-bar info on MT5 data.
Therefore the optimal policy is STRUCTURAL, not predictive: take every qualified trade, use a DEEP TARGET to
capture the fat tail in aggregate (downside-neutral — c71/c72/c73), and size FLAT (conviction-sizing is
metals-only + maxDD-widening). Per-trade prediction-conditioning is a DEAD END on this data — a valuable,
program-focusing negative: stop spending effort on decision-bar prediction; the remaining prediction upside
needs richer data (live fills, microstructure, paid sources), not more MT5 feature engineering.

## WHAT SURVIVES / DISPOSITION
- **DEPLOY (gated): the flat DEEP TARGET** (metals ~6R, us_equity ~8-10R) — robust, cross-sleeve, every-year
  (metals), downside-neutral, higher velocity (c73), lifts safe base to 2.0% (c71 sizing). THE breakthrough.
- **Per-trade prediction cells: CLOSED** (reach-selection, regime-depth, adaptive-MFE-target, stop-by-MAE) —
  outcome not decision-bar-predictable; large ceilings, no realistic capture.
- **size_by_regime (metals htf_slope): qualified marginal LEAD** — risk-adjusted-positive on metals but
  maxDD-widening + equity-fails → not deployed; revisit only with the maxDD controlled / live-confirmed.
- **The breakthrough FRAMEWORK (c70) is validated as a METHOD:** oracle-first + sealed-deflation correctly
  separated the one structural win (deep target) from many large-ceiling-but-unpredictable prediction mirages.

## NEXT
- DEPLOYMENT GATE: book-level sizing re-validation on the combined deep-target book (metals 6R + equity ~10R,
  correlated-risk-unit, smooth DD-defense, static floor, FN+8%/FTMO+10%) → confirm safe base + 0% daily-breach
  + the faster pass; then wire deep-target + vol-cap as gated live candidates (verify live W7 sleeve parity).
- Prediction upside is parked for the live-confirm / paid-data phase (richer features), not more MT5 mining.

**Files.** Workflow wf_85847b95-57b; nl_*.py + GEOM/validation JSONs in the route dir.
