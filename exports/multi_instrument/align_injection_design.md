# Align Score Injection — Design Doc

## What
Compute the 'align' score (0-4 timeframe consensus) for each instrument
and inject it into the AI prompt context. This is the strongest validated
predictor (+7.5pp on gold displacements, Bonferroni-surviving).

## How
1. In the orchestrator, after building the MSO:
   - Check D1 direction (bullish/bearish/unclear)
   - Check H4 direction (bullish/bearish/unclear)
   - Check H1 direction (bullish/bearish/unclear)
   - Check M15 direction (bullish/bearish/unclear)
   - align_score = count of timeframes agreeing with the displacement direction

2. Inject into prompt context:
   "Timeframe alignment score: {align_score}/4
    ({details: D1=bullish, H4=bullish, H1=bearish, M15=bullish})
    Higher alignment (3-4) historically shows +7-9% better continuation."

3. The AI uses this as a confidence modifier, not a hard gate
   (24% of good trades have align < 2, so gating kills too many)

## Dependencies
- MSO already contains direction per timeframe
- Orchestrator already has access to the MSO
- Just need to compute the score and format it for injection

## Estimated effort: 2 hours (implement + test + verify on gold data)
## Risk: Low — additive feature, doesn't change existing behavior
