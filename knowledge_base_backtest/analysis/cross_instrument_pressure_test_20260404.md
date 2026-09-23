# Pressure Test — H1 POI Guardrail + Cross-Instrument Context
**Date:** 2026-04-04
**Status:** ALL PASS (after critical fix)

---

## Results Summary

```
=== PRESSURE TEST RESULTS ===
Test 1 (H1 POI Guardrail):       PASS — Both rules present in both XAUUSD and GBPUSD prompts
Test 2 (GBPUSD Context Present):  PASS — All 8 required elements present, correct placement
Test 3 (Gold Context Absent):     PASS — Zero cross-instrument references in gold prompt
Test 4 (D1 Direction Accuracy):   PASS — 4/5 matched (1 "unknown" in expected data)
Test 5 (Asian Range Math):        PASS — 3/3 dates matched exactly (0.000000 diff)
Test 6 (Edge Cases):              PASS — All 4 edge cases degrade gracefully
Test 7 (Batch/Live Parity):       PASS — Both code paths use identical functions
Test 8 (Regression):              PASS — 485 tests passing
Test 9 (Config):                  PASS — Correct structure, GBPUSD only
```

---

## CRITICAL FIX APPLIED DURING TEST

### Test 4 initially FAILED: D1 Direction Methodology Mismatch (1/5 match)

**Root cause:** The initial implementation of `get_xauusd_d1_direction()` used 2-bar pivot swing detection with `identify_structure()` (HH/HL/LH/LL classification over 20 candles). The improvements analysis that produced the 31.7% WR spread used a simple close-over-previous-close comparison (`d1_dir_simple`).

These are fundamentally different:
- **Swing structure (original):** "Is the 20-day trend bullish?" → Often returns "unclear" on ranging days
- **Close-over-close (correct):** "Was today's D1 candle bullish?" → Always returns bullish or bearish

**Fix applied:** Rewrote `get_xauusd_d1_direction()` to use close-over-previous-close, matching the validated methodology. After fix: 4/5 dates match (the 5th has "unknown" expected value, not a real mismatch).

**Why this matters:** If we had deployed the swing-based version, the AI would see "unclear" on ~40% of days (returning "mixed" dollar signal), diluting the 31.7% WR spread that justified adding cross-instrument context. The close-over-close version always produces a directional signal, matching what was validated.

---

## Test Details

### Test 1: H1 POI Guardrail — Text Verification

Both internal consistency rules present in both XAUUSD and GBPUSD prompts:

```
## Internal Consistency Rules
- If decision is CANDIDATE, m15_confirmation.choch_detected MUST be true (otherwise violates U3).
- If m15_confirmation.choch_detected is false, decision MUST be NO_TRADE.
- If h1_setup.poi_identified is FALSE or h1_setup.poi_type is "none", the decision MUST
  be NO_TRADE. The ob_retest framework requires price to pull back to an H1 point of
  interest. Without a valid H1 POI, the setup sequence is incomplete regardless of M15
  confirmation quality.
```

H1 POI rule uses absolute language ("MUST be NO_TRADE") and references "ob_retest framework."

### Test 2: GBPUSD Cross-Instrument Context

All 8 required elements verified present:

| Element | Status |
|---|---|
| Section header | OK |
| XAUUSD D1 direction | OK |
| Dollar weakness/strength mapping | OK |
| Asian range value | OK |
| Asian range category | OK |
| Conflicting direction guidance | OK |
| Narrow Asian guidance | OK |
| Combined unfavorable rule | OK |

Placement: After session memory, before Current Time/MSO. Correct.

Dollar direction mapping verified:
- Gold bullish → "dollar weakness" (correct)
- Gold bearish → "dollar strength" (correct)

### Test 3: Gold Cross-Instrument Context Absent

Zero matches for: "Cross-Instrument", "GBPUSD", "dollar weakness", "dollar strength", "Asian range"

Gold config has `cross_instrument_context.enabled: False` (default — key absent from gold overrides).

### Test 4: D1 Direction Accuracy (After Fix)

| Date | Computed | Expected | Match |
|---|---|---|---|
| 2024-01-25 | bullish | bullish | Y |
| 2024-09-06 | bearish | bearish | Y |
| 2025-03-04 | bullish | bullish | Y |
| 2025-02-18 | bullish | bullish | Y |
| 2025-02-25 | bearish | unknown | N/A |

4/5 match. The 5th date (2025-02-25) was not in the improvements analysis trade details ("unknown" expected), so it cannot be verified — not a real mismatch.

### Test 5: Asian Range Math

| Date | Range | ADR | Pct | Category | Diff |
|---|---|---|---|---|---|
| 2024-01-25 | 0.002320 | 0.008487 | 27.3% | narrow | 0.000000 |
| 2025-03-04 | 0.003090 | 0.008769 | 35.2% | moderate | 0.000000 |
| 2025-12-10 | 0.001810 | 0.007416 | 24.4% | narrow | 0.000000 |

All exact matches — zero difference on all metrics.

### Test 6: Edge Cases

| Edge Case | Result |
|---|---|
| 6A: Empty XAUUSD D1 data | Returns "unavailable", context omitted |
| 6B: No Asian M15 data | Returns None, context omits Asian range |
| 6C: D1 direction "unclear" | N/A — new implementation never returns "unclear" |
| 6D: Empty cross_instrument_context | Clean prompt without section |

Note: With the close-over-close methodology, "unclear" is no longer possible — the function always returns bullish or bearish (or unavailable). This is correct behavior.

### Test 7: Batch/Live Parity

Both `scripts/batch_backtest.py` and `src/components/orchestrator.py`:
- Import the same functions from `src/utils/cross_instrument.py`
- Call `get_xauusd_d1_direction()` and `get_asian_range_pct()` identically
- Pass results through `format_cross_instrument_context()`
- Thread the formatted text to the prompt builder via `cross_instrument_context=`

Same inputs produce identical outputs — verified with 2025-03-04 data.

### Test 8: Regression

485 tests passing, 0 failures, 19 warnings (all deprecation).

### Test 9: Config

```yaml
GBPUSD:
  cross_instrument_context:
    enabled: true
    reference_instrument: "XAUUSD"
    reference_timeframe: "D1"
    dollar_direction_map:
      bullish: "weakness"
      bearish: "strength"
      unclear: "mixed"
      unavailable: "unknown"
```

Gold: no `cross_instrument_context` key (defaults to disabled).

---

## Files Modified During Pressure Test

| File | Change |
|---|---|
| `src/utils/cross_instrument.py` | Rewrote `get_xauusd_d1_direction()` from swing structure to close-over-close |
| `tests/test_cross_instrument.py` | Updated test fixtures for new methodology |

No other files changed.
