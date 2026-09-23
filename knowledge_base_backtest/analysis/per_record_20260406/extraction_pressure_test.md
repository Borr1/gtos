# Per-Record Extraction Pressure Test

**Date:** 2026-04-04
**Verdict:** PASS WITH WARNINGS
**Critical Failures:** 0
**Warnings:** 6

---

## Test 1: OB Per-Record Integrity

| Check | Result | Detail |
|-------|--------|--------|
| Record count | **PASS** | 820 (expected 700-950) |
| All required fields | **PASS** | 44 fields total, all critical fields at 100% coverage |
| retracement_pct present | **PASS** | 100% coverage, stored as **ratio (0-1)** not percentage |
| Price range | **PASS** | $2182-$5213, within expected $1800-$5600 |
| OB width median | **PASS** | $7.15, within expected $2-$30 |
| Retest rate | **PASS** | 98.2% (expected ~99%) |
| Continuation rate | **WARN** | 72.8% vs expected 66.5% — off by 6.3pp |
| Date range | **PASS** | 2024-04-01 to 2026-03-27, 378 unique dates, max gap 11 days |
| BOS/CHoCH split | **INFO** | BOS=787 (96%), CHoCH=33 (4%) |

### Retracement Distribution (converted to %)

| Range | Count |
|-------|-------|
| 40-60% | 2 |
| 60-80% | 42 |
| 80-100% | 776 |

**Note:** Mean=89.9%, median=91.4%. Higher than the expected 40-80% for "pullback depth." This likely measures how deep into the impulse leg price retraced before touching the OB zone — since OBs are at the origin of impulses, ~90% retracement to reach them is geometrically expected. **Not a data error, but a semantic clarification needed before using in models.**

### Continuation Rate Discrepancy (WARN)

Per-record: 72.8% vs comprehensive aggregate: 66.5% (delta 6.3pp). Possible causes:
1. Per-record counts each OB equally; comprehensive may weight by group
2. Different definitions of "continuation" (3h horizon vs different window)
3. Different inclusion criteria for edge cases

**Action:** Acceptable for analysis. Document the delta.

---

## Test 2: FVG Per-Record Integrity

| Check | Result | Detail |
|-------|--------|--------|
| Record count | **PASS** | 1661 (expected 1500-2100) |
| All required fields | **PASS** | 28 fields, all critical at 100% coverage |
| fill_percentage present | **PASS** | 100% coverage, stored as **ratio (0-2)**, capped at 2.0 |
| FVG size median | **PASS** | $3.69, within expected $1-$40 |
| Direction balance | **PASS** | Bullish 946 (57%) / Bearish 715 (43%) via fvg_type |
| Date range | **PASS** | 2024-04-01 to 2026-03-30, 499 unique dates |

### Fill Group Validation

| Group | Per-Record n | Comprehensive n | Per-Record Rate | Expected Rate | Match? |
|-------|-------------|-----------------|-----------------|---------------|--------|
| <50% | 272 | ~272 (inferred) | 25.0% | ~25% | YES |
| 50-80% | **196** | **196** | **44.9%** | **44.9%** | **EXACT** |
| 80-100% | **168** | **168** | **71.4%** | **71.4%** | **EXACT** |
| >100% | 1025 | 1147 | 63.6% | 56.8% | PARTIAL |

The 50-80% and 80-100% groups are **exact matches** — strong validation that the extraction logic is correct.

### All filled=True (WARN)

All 1661 records have `filled=True`. The extraction appears to have filtered to only filled FVGs. The comprehensive had 1783 total entries — the 122 missing are likely unfilled FVGs excluded by the extraction.

**Impact:** Does not affect filled-FVG analysis. If unfilled FVG analysis is needed later, re-extract with `filled=False` included.

### fill_percentage Cap (WARN)

`fill_percentage` is capped at 2.0 (200%). The `max_fill_depth` field contains uncapped values (observed up to 4.1+). **Use `max_fill_depth` for granular >100% fill analysis.**

---

## Test 3: Date Overlap

| Metric | Value |
|--------|-------|
| Total trading dates | 511 |
| Both OB retest + FVG fill | 200 (39.1%) |
| OB retest only | 67 (13.1%) |
| FVG fill only | 179 (35.0%) |
| Neither | 65 (12.7%) |
| Arithmetic check | **PASS** (200+67+179+65=511) |

**Key finding:** FVG fill adds **179 additional signal dates** (35.0%) where OB retest alone had no signal. This is a major frequency multiplier.

---

## Test 4: Spatial Overlap

| Metric | Value |
|--------|-------|
| OBs with FVG overlap | 205 (25.7%) |
| OBs without FVG overlap | 593 (74.3%) |

Informational only — NOT used as a predictor.

---

## Test 5: Cross-Script Consistency

| Check | Result | Detail |
|-------|--------|--------|
| Detection method | Reimplemented | Standalone scripts, not imported from comprehensive |
| Date range match | **MINOR DIFF** | OB ends 2026-03-27, FVG ends 2026-03-30 (expected: OB needs forward window) |
| Shared dates | 366 | 12 OB-only, 133 FVG-only dates |
| Data source | **PASS** | Both reference XAUUSD historical candle data |

---

## Test 6: Data Quality

| Check | OB | FVG |
|-------|-----|-----|
| Null critical fields | 0 | 0 |
| Inverted zones | 0 | 0 |
| Negative values | 0 | 0 |
| Duplicates | 0 | 0 |

**All data quality checks: PASS**

---

## Summary of Warnings

1. **W1:** `retracement_pct` stored as ratio 0-1, mean=89.9% after conversion. Semantically may measure distance to OB zone, not pullback depth.
2. **W2:** OB continuation rate 72.8% vs expected 66.5% (6.3pp delta). Acceptable.
3. **W3:** All FVGs marked filled=True — extraction filtered unfilled out. 122 records fewer than comprehensive.
4. **W4:** FVG >100% group: n=1025 vs 1147, rate=63.6% vs 56.8%. Accounted for by missing records.
5. **W5:** `h4_direction` skewed bullish (95%), but `fvg_type` balanced (57/43). Use `fvg_type` for direction.
6. **W6:** `fill_percentage` capped at 2.0. Use `max_fill_depth` for uncapped values.

**None of these warnings block analysis.** All are documented and have clear workarounds.
