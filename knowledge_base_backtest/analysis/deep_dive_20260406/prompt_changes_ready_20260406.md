# Prompt Changes Ready to Implement — 2026-04-06

## Change 1: Remove OTE Zone Preference
**Finding**: N3 — OTE zone dead (p=0.61 on 7496 records, p=0.824 on 6641)
**Risk**: Low — removing a dead filter cannot hurt

**Current text to find**: Any reference to "OTE zone", "optimal trade entry", "62-79% retracement", or fib zone preferences in the primary analyzer prompt.

**Replacement**: Remove entirely. Do NOT replace with a different zone filter. Retracement depth matters (6A) but 95% of OBs are already >80%, so a zone filter is unnecessary.

---

## Change 2: Add Impulse Candle Count as Quality Signal
**Finding**: F6 — impulse_candle_count r=-0.31, p=0.0
**Risk**: Medium — new filter, needs forward validation

**Add to OB quality evaluation section**:
```
IMPULSE SHARPNESS: Prefer OBs formed by single-candle or 2-candle impulse moves. OBs with 4+ impulse candles have significantly lower continuation rates. The sharpness of the displacement (fewer candles) matters more than its absolute size (ATR multiple is irrelevant, p=0.97).
```

---

## Change 3: Add FVG Creation as Positive Signal
**Finding**: F2 — creates_fvg p=0.0, effect=+11.1pp
**Risk**: Low — adding a positive signal, not filtering

**Add to displacement evaluation**:
```
FVG CREATION: Displacements that create a Fair Value Gap have ~11% higher continuation rates. Note this as a confidence booster when evaluating displacement quality.
```

---

## Change 4: Remove H4 Elevation (Do NOT implement)
**Finding**: N1 — H4 alignment dead (p=0.76)
**Action**: If any prior session recommended elevating H4 above D1, DO NOT implement. H4 adds zero predictive value.

---

## Change 5: FVG Fill Depth Filter (For FVG Fill Framework Implementation)
**Finding**: F5 — 80-100% fill = 71.4% continuation
**Risk**: Medium — new framework, needs batch testing

**When implementing FVG Fill framework**:
```
FVG FILL DEPTH FILTER: Prioritize FVGs that have filled 80-100% of the gap. This is the sweet spot:
- <50% fill: ~25% continuation (avoid)
- 50-80%: ~35-50% continuation (marginal)
- 80-100%: 71.4% continuation (preferred)
- >100% fill: 63.6% continuation (acceptable but degraded)
```

---

## Change 6: Counter-Trend Downweight
**Finding**: F4 — ct flag effect=-5.2pp, p=0.000472
**Risk**: Low — small downweight on existing signal

**Add to confidence scoring**:
```
COUNTER-TREND PENALTY: Counter-trend displacements (against the prevailing session/daily flow) have approximately 5% lower continuation rates. Apply a small confidence penalty (-5 to -10 points) for counter-trend setups.
```

---

## Changes NOT Recommended

1. **BE Stop**: DO NOT implement. Net negative at every trigger.
2. **NY KZ Extension**: DO NOT extend to 17:00. p=0.52.
3. **DOW Filters**: DO NOT add day-of-week filtering. p=0.10.
4. **Body Ratio Threshold**: No consistent threshold found.
5. **FVG Size Filter**: p=0.57 — size doesn't matter.
6. **Regime-Based Adjustments**: All p > 0.05. Insufficient evidence.
