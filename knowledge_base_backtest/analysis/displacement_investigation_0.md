# Displacement Ratio Inversion Investigation

**Date:** 2026-04-01
**Finding:** Higher M15 displacement ratios (from reasoning JSON) correlate with WORSE outcomes

## The Paradox

From vertical analysis:
- disp_ratio < 1.6: 51 trades, 76.5% WR, +0.491R expectancy
- disp_ratio >= 1.6: 50 trades, 62.0% WR, -0.027R expectancy

This is counter-intuitive — stronger displacement should mean stronger confirmation.

## Root Cause: Data Quality Issue (Primary)

**47 out of 101 trades have disp_ratio = 0.0 with displacement_quality = "none".**

These zero-ratio trades come from earlier batch runs (2024 dates and some 2025 dates) where the AI did not consistently output the `displacement_candle_body_vs_avg_ratio` field. They defaulted to 0.0 in the Pydantic model.

These 47 trades have a 76.6% win rate — they're good trades, they just lack displacement data. When grouped into "disp_ratio < 1.6", they inflate that bucket's win rate, creating the illusion that low displacement is better.

**This is a data artifact, not a market insight.**

## Secondary Finding: High Displacement Losses Are Full SL Hits

Among the 18 high disp_ratio (>=1.6) losses:
- All 18 exited at CLOSED_SL (full -1R loss)
- High disp_ratio trades have avg SL = $54.2 vs $40.0 for low disp_ratio
- Several have "ambiguous" sweep quality, suggesting the displacement was genuine but the setup context was weak

Sample high-disp losses:
- bt_2025-02-25_london_001: 3.4x ratio, clean sweep, still full SL loss
- bt_2025-02-12_london_001: 3.3x ratio, clean sweep, still full SL loss
- bt_2026-01-13_ny_002: 2.8x ratio, **ambiguous** sweep — displacement strong but sweep was questionable

## Conclusion

1. **The inversion is a data artifact** caused by 47 trades with missing displacement data (ratio=0) being grouped with the "low displacement" bucket.

2. **When displacement data IS present** (54 trades), the relationship is too noisy to draw conclusions — both high and low displacement trades have mixed outcomes.

3. **Do not use disp_ratio as a confidence proxy.** The data is too inconsistent across batch runs.

4. **If re-running backtests**, ensure the PA consistently outputs the displacement ratio. The current Pydantic model defaults to 0.0 which masks missing data.

## Recommendation

No action needed. The displacement ratio field is not broken — it's just not consistently populated in historical data. Future runs with the current prompt will populate it correctly. The confidence scorer correctly ignores this field (uses price_level_count and hesitation_score instead, which are derived from the full reasoning text and don't suffer from missing data).
