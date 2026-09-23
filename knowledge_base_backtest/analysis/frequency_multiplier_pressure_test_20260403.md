# Pressure Test — Frequency Multiplier Investigation

**Date:** 2026-04-03
**Status:** COMPLETE
**Tested:** `frequency_multiplier_investigation_20260403.md`

---

## Results Summary

```
=== PRESSURE TEST RESULTS ===
Test 1 (H4 OB Spot-Check):         [PASS] — 9/9 verified
Test 2 (H4/H1 Overlap):            [FAIL] — CRITICAL LOGICAL BUG in overlap metric
Test 3 (Category 1 Cross-Check):    [PASS] — 5/5 correctly categorized, count 274 exact match
Test 4 (Hourly Sum Sanity):         [PASS] — all sums match, KZ% consistent, scan CSV within 0.04%
Test 5 (Suspicious Hours):          [PASS] — 4 low-n hours flagged, 0 affect recommendations
Test 6 (Extended London GBPUSD):    [PASS] — XAUUSD h10=45.6% confirms zero-trade; GBPUSD h10=50.4% supports extension
Test 7 (Effort Estimates):          [WARN] — 2 items underestimated, 1 missing dependency
Test 8 (Ranking Consistency):       [PASS] — rankings broadly consistent with computed metric
Test 9 (Novel vs Repackaged):       [INFO] — 4 genuinely new analyses, 1 repackaged

Errors found: 1 critical (Test 2 overlap bug)
Warnings: 2 (Test 7 effort estimates)
Impact on priorities: SIGNIFICANT — Lever 2 (H4 OB) should be RE-EVALUATED, not shelved
```

---

## Test 1: H4 OB Spot-Check — PASS (9/9)

Randomly selected 3 dates each from XAUUSD, GBPUSD, NAS100. All 9 verified:

| Instrument | Date | Direction | OB Zone | M15 KZ Touch |
|-----------|------|-----------|---------|--------------|
| XAUUSD | 2024-03-22 | bullish | $2154.68 - $2164.86 | Confirmed |
| XAUUSD | 2024-10-04 | bullish | $2655.05 - $2662.02 | Confirmed |
| XAUUSD | 2025-02-11 | bullish | $2853.25 - $2886.68 | Confirmed |
| GBPUSD | 2024-06-06 | bullish | 1.2800 - 1.2800 | Confirmed |
| GBPUSD | 2025-03-07 | bullish | 1.2900 - 1.2900 | Confirmed |
| GBPUSD | 2026-01-08 | bullish | 1.3400 - 1.3400 | Confirmed |
| NAS100 | 2024-04-10 | bullish | 17978 - 18221 | Confirmed |
| NAS100 | 2024-05-22 | bullish | 18643 - 18685 | Confirmed |
| NAS100 | 2025-07-11 | bullish | 22650 - 22710 | Confirmed |

D1+H4 alignment, OB formation, and M15 price reaching the zone during KZ hours all confirmed independently. The H4 OB detection methodology is sound.

---

## Test 2: H4 vs H1 Overlap — FAIL (Critical Logical Bug)

### The Bug

The investigation measures overlap as: "% of H4 OB retest dates that also pass the standard pre-screen."

This is **tautologically 100%** because:
- H4 OB retest requires D1 clear + H4 aligned with D1
- The pre-screen requires D1 clear + H4 aligned with D1
- They are the **same condition**

So the investigation's claim that "H4 OB retest adds ZERO new trade dates" is based on a faulty comparison. Passing the pre-screen ≠ having an H1 ob_retest trade.

### The Correct Metric

The correct question is: "On H4 OB retest dates, does the H1 ob_retest framework ALSO produce a trade?"

From existing batch results:
- XAUUSD batch: 36 trades over 182 prescreen-pass dates = **19.8% trade rate**
- GBPUSD batch: ~20 trades over 134 prescreen-pass dates = **~15% trade rate** (from deep analysis)

This means on any given prescreen-pass date, there's only a ~15-20% chance the H1 system fires. Therefore:
- **~80% of H4 OB retest dates would NOT have an H1 trade**
- The true overlap is likely **~20%, not 100%**
- H4 OB retest DOES add genuinely new trade dates

### Impact on Priorities

The investigation shelved Lever 2 entirely based on the 100% overlap claim. With corrected overlap (~20%), H4 OB retest becomes:
- 0.6-0.7 opportunities/month per instrument × 80% new = 0.5-0.6 new trades/month
- With 70-85% continuation rates and MFE/MAE 1.4-2.3
- Across 5 instruments: ~2.5-3.0 new high-quality trades/month

This is LOW frequency but VERY high edge quality. It should NOT be shelved — it should be Tier 2 (test via batch) rather than Tier 4 (shelve).

### Caveat

The 80% non-overlap estimate is approximate. The actual overlap could be higher if H4 OB retest dates are systematically higher-quality days where the H1 system also fires more often. A precise answer requires cross-referencing against actual batch trade dates, which we don't have loaded.

---

## Test 3: Category 1 Cross-Check — PASS (5/5)

Tested on GBPUSD. Recomputed Cat1 count independently: 274 dates. Investigation reported: 274. **Exact match.**

5 randomly selected Cat1 dates verified by independently computing D1/H4/H1 structure:

| Date | D1 | H4 | H1 | Cat1? |
|------|----|----|-----|-------|
| 2024-02-12 | transitional | bullish | bullish | Confirmed |
| 2024-02-13 | transitional | bullish | bullish | Confirmed |
| 2024-05-09 | transitional | bullish | bullish | Confirmed |
| 2024-12-20 | transitional | bullish | bullish | Confirmed |
| 2025-01-14 | transitional | bullish | bullish | Confirmed |

The categorization logic is correct. D1 is genuinely transitional/unclear, while H4 and H1 both show clear aligned direction.

---

## Test 4: Hourly Sum Sanity — PASS

All 5 instruments verified:

| Instrument | Hourly Sum | Reported Total | Match | KZ Capture |
|-----------|-----------|----------------|-------|-----------|
| XAUUSD | 7,500 | 7,500 | Exact | 29.7% = 29.7% |
| GBPUSD | 7,831 | 7,831 | Exact | 31.4% = 31.4% |
| EURUSD | 7,866 | 7,866 | Exact | 30.1% = 30.1% |
| NAS100 | 6,977 | 6,977 | Exact | 30.3% = 30.3% |
| XAGUSD | 7,698 | 7,698 | Exact | 28.1% = 28.1% |

Cross-check with displacement scan CSV: GBPUSD scan CSV = 7,828 rows vs investigation = 7,831. Difference of 3 rows (0.04%) — within expected tolerance from boundary effects and different start/end handling.

---

## Test 5: Suspicious Hours — PASS

### Flagged hours (cont > 60% or n < 50):

| Instrument | Hour | Cont% | n | Issue |
|-----------|------|-------|---|-------|
| XAUUSD | 00:00 | 25.9% | 27 | Low n |
| NAS100 | 00:00 | **66.7%** | **18** | Both: high cont + very low n |
| XAGUSD | 00:00 | 28.0% | 25 | Low n |

All are hour 00:00 (midnight UTC) — a dead zone with negligible activity. **None of these affect any recommended extension window.** All recommended windows have n > 100 (most have n > 500).

The NAS100 00:00 66.7% continuation rate at n=18 is pure noise. Correctly flagged as unreliable but correctly excluded from recommendations.

---

## Test 6: Extended London GBPUSD vs Gold — PASS

| Metric | XAUUSD 10:00 | GBPUSD 10:00 |
|--------|-------------|-------------|
| Displacements | 485 | 794 |
| Disps/day | 0.83 | 1.36 |
| 3h Continuation | **45.6%** (below 48.7% baseline) | **50.4%** (above baseline) |
| MFE/MAE | 1.03 | 1.03 |
| OB Retest Rate | 84.1% | 87.5% |

The investigation's explanation for the gold zero-trade result is confirmed:
1. Gold DOES have displacements at 10:00 (485 total, 0.83/day) — so it's not a "no activity" problem
2. Gold's 10:00 continuation rate is **below baseline** (45.6% vs 48.7%) — the AI correctly found no qualifying setups
3. GBPUSD's 10:00 hour is its **peak displacement hour** (794 disps, 1.36/day) with above-baseline continuation
4. The extended London failure was gold-specific, not structural

GBPUSD core London (07:00-08:59) has 50.0% continuation. GBPUSD 10:00 hour has 50.4% — essentially identical. The extension should perform comparably to core hours.

---

## Test 7: Implementation Effort Estimates — WARN

### Lever 4 (Extended Sessions): "Config change only"

**Verified as partially correct, but understated.**

Files that need changing:
1. `config/agent_config.yaml` — add per-instrument KZ overrides. Currently has only one london/ny KZ definition. Would need an `instrument_overrides` section or per-instrument KZ config. **~15 min.**

2. `scripts/historical_data_loader.py` — `replay_london_open()` and `replay_ny_open()` are **hardcoded to specific hour ranges**. Would need new `replay_extended_london()` / `replay_extended_ny()` functions or parameterization. **~1 hour, not mentioned in investigation.**

3. `scripts/batch_backtest.py:243-263` — calls `replay_london_open` and `replay_ny_open` explicitly. Would need to add calls for new windows. **~30 min.**

4. `src/components/orchestrator.py` — live system needs the same window changes. **~30 min.**

**Underestimated item:** The investigation says "config change only" but `replay_london_open`/`replay_ny_open` are hardcoded functions. Adding new windows requires code changes in at least 3 files. True effort: **~2-3 hours**, not "config change only."

### Lever 3 (Pre-screen Loosening): "2-4 hours"

**Verified as roughly correct, with one missing item.**

Files listed in investigation:
1. `batch_backtest.py:94-131` — `prescreen_date()`: Need to add Cat1 bypass. **~30 min.**
2. `orchestrator.py:590-606` — `prescreen_mso()`: Same change. **~30 min.**
3. `primary_analyzer_prompt.py:107-108` — U1/U2 rules say "Daily structure must be clearly bullish or bearish" and "H4 structure must agree with Daily bias direction." Need a secondary path for transitional D1. **~1 hour** — prompt engineering is delicate.
4. `permissions.py:92-98` — Gate 1 checks `daily_bias.direction`. **~30 min.**

**Missing item:** The `_safety_check()` function in `batch_backtest.py:737-753` ALSO checks `daily_bias.direction` against trade direction. This is a **5th code location** not listed in the investigation. If you change the prescreen but not the safety check, loosened dates would still get rejected post-AI. **~15 min to fix, but a gotcha if missed.**

Total effort: 2-4 hours is reasonable with the missing item included. **The 5th location (`_safety_check`) is the risk.**

### Lever 2 (H4 OB Retest): "Medium (new H4 framework in PA prompt)"

**Not verified in detail because the investigation shelved it.** But the effort assessment of "Medium" is reasonable — it would require a new framework section in the PA prompt (like OB1-OB7 but for H4 OBs), changes to MSO computation to pass H4 OBs through, and potentially a new entry model. **3-5 hours** is more accurate than "medium."

---

## Test 8: Ranking Consistency — PASS

Computed ranking metric: `trades_per_month × quality_score / effort`

Top 5 by computed metric:
1. Extended London 09:30-12:00 GBPUSD: score 6.60
2. Extended London 09:30-12:00 EURUSD: score 5.33
3. Loose Pre-screen XAUUSD: score 4.57
4. Extended NY 15:30-17:00 XAUUSD: score 4.52
5. Extended NY 15:30-17:00 NAS100: score 3.99

Investigation's priority order:
1. Extended NY 15:30-17:00 (XAUUSD, NAS100, XAGUSD)
2. Loose pre-screen (GBPUSD)
3. Extended London 09:30-12:00 (GBPUSD, EURUSD)

**Minor inconsistency:** By computed metric, Extended London GBPUSD (score 6.60) should be #1, not Extended NY XAUUSD (score 4.52). The investigation prioritized Extended NY first because it applies to 3 instruments vs 2, but per-instrument the London extension is higher value for GBPUSD.

This is a reasonable judgment call, not a bug. The investigation grouped by window type for implementation simplicity. If implementing per-instrument, Extended London for GBPUSD should go first.

**H4 OB Retest scored average 0.73** — lower than extensions (avg 2.74) even without the overlap bug, because of higher implementation effort (5 vs 1). But with corrected overlap (~20%), the score rises modestly since it now represents genuinely new trades. Still not #1 priority, but not worth shelving.

---

## Test 9: Novel vs Repackaged — INFO

### Genuinely New Analyses (4):

1. **Hourly displacement breakdown (24-hour, per instrument)** — The existing displacement scan only had session-level granularity (asian/london/ny/late). The investigation computed hour-by-hour displacement counts, continuation rates, MFE/MAE, and OB retest rates. This is NEW and the core value of the Lever 4 analysis.

2. **Category 1 outcome quality (Cat1 with displacement + OB retest outcomes)** — The multi-instrument validation had D1 unclear / H4 mismatch counts but NOT the Cat1-Cat4 categorization with H1 alignment, and NOT the continuation rate / MFE-MAE analysis for Cat1 dates. The sub-categorization and outcome measurement are NEW.

3. **H4 OB retest opportunity sizing** — H4 OBs were computed in the MSO but never analyzed for retest frequency, zone width, or outcome quality. The H4 OB retest quantification is entirely NEW.

4. **Extension window value scoring** — The displacement scan identified sessions but never scored specific extension windows by (frequency × quality / effort) or made build-vs-skip recommendations. This synthesis is NEW.

### Repackaged (1):

5. **KZ capture percentage** — The displacement scan already showed session distribution (ny=2722, asian=2040, london=1514). The investigation recomputed this at hourly granularity, which is new, but the headline finding ("current KZ captures ~30%") could have been derived from existing session counts. **Partially repackaged, partially new** (the hourly detail is new, the headline is derivable).

### Not Repackaged:

The investigation did NOT copy from the Apr 2 pre-screen analysis because that analysis doesn't exist as a file — it was done in a prior session and referenced in the prompt context but not saved. The investigation recomputed everything from scratch.

---

## Errors Found

### Critical: Test 2 — Overlap Metric Logical Bug

**What:** The investigation concludes H4 OB retest has "100% overlap" and "adds ZERO new trade dates," leading to a Tier 4 (shelve) recommendation.

**Why it's wrong:** The overlap is measured against pre-screen pass dates, not against actual H1 trades. Since only ~15-20% of prescreen-pass dates produce trades, ~80% of H4 OB retest dates are genuinely new opportunities.

**Impact:** Lever 2 should be re-evaluated from Tier 4 (shelve) to Tier 2 (test via batch). With corrected overlap:
- ~2.5-3.0 new high-quality trades/month across all instruments
- 70-85% continuation rates (the best edge quality of any lever)
- Medium implementation effort

**Corrective action:** The investigation report's Lever 2 verdict and Tier 4 classification should be amended. H4 OB retest deserves a batch test, not a shelving.

---

## Warnings

### Warning 1: Test 7 — Extended Sessions Effort Underestimated

The investigation claims "config change only" for Lever 4, but `replay_london_open()`/`replay_ny_open()` are hardcoded functions that need code changes in `historical_data_loader.py`, `batch_backtest.py`, and `orchestrator.py`. True effort: ~2-3 hours, not config-only.

### Warning 2: Test 7 — Missing 5th Code Location for Pre-screen

The investigation lists 4 code locations for Lever 3 but misses `batch_backtest.py:_safety_check()` which also gates on `daily_bias.direction`. If this isn't updated, loosened dates would pass the pre-screen but get rejected post-AI.

---

## Corrected Priority Recommendations

After pressure test findings:

### Tier 1: Implement Now
1. **Extended NY 15:30-17:00** for XAUUSD/NAS100/XAGUSD — highest aggregate frequency, ~2-3h effort (not config-only)
2. **Extended London 09:30-12:00** for GBPUSD/EURUSD — highest per-instrument score, same effort

### Tier 2: Test via Batch
3. **Loose pre-screen (Cat1)** for GBPUSD — 53.4% cont, MFE/MAE 1.11 (best Cat1 edge). Include _safety_check fix.
4. **H4 OB Retest** for all instruments — RE-ELEVATED from Tier 4. 70-85% continuation, ~80% genuinely new dates. Medium effort but exceptional edge quality. Worth a focused batch test.

### Tier 3: Monitor
5. Pre-London 05:00-07:00, Asian open — lower frequency/edge
6. Loose pre-screen for XAGUSD — marginal MFE/MAE

### Tier 4: Don't Build
7. Loose pre-screen for EURUSD/NAS100 — no edge improvement

---

## Verification Script

All automated tests run via:
`knowledge_base_backtest/analysis/frequency_multiplier_pressure_test.py`

Runtime: ~12 seconds. Deterministic with `random.seed(42)`.
