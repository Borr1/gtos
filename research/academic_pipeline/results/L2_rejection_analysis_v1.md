# L2 Rejection Analysis — XAUUSD T7 Simulation (Jan 2 – Mar 11, 2026)

**Data source:** `research/t7_live_simulation/all_results_jan_mar11.json` (1464 records)
**Analyst:** Execution agent, April 13, 2026
**API cost of this analysis:** $0 (pure computation)

---

## VALIDATION CHECKS (run before analysis)

All 4 checks PASS:

1. **Sum check:** 439 + 141 + 6 + 5 + 0 = 591 = total L2 rejections ✓
2. **Manual verification (3 random records):**
   - `2026-01-23T16:00Z` → `REJECTED_L2`, reason=`entry_in_ob: Entry 4935.73 is outside OB zone 4818.79-4832.49` ✓
   - `2026-01-08T16:45Z` → `REJECTED_L2`, reason=`h1_poi_exists: AI reports poi_identified=False` ✓
   - `2026-02-10T15:45Z` → `REJECTED_L2`, reason=`entry_in_ob: Entry 5047.17 is outside OB zone 4936.53-4958.88` ✓
3. **WR sanity:** 7 executed trades, 3W/4L = 42.9% WR, +0.55R total ✓ (matches simulation report)
4. **Parse fail count:** 289 ✓ (expected 289)

---

## PIPELINE FUNNEL (full context)

| Stage | Count | % of prior |
|-------|-------|-----------|
| Total KZ candles | 1464 | — |
| Prescreen blocked (no D1/H4 bias or OB proximity) | 266 | 18.2% |
| **Sent to AI** | **1198** | **81.8%** |
| AI said NO_TRADE | 286 | 23.9% of AI calls |
| **AI said CANDIDATE (raw)** | **899** | **75.0% of AI calls** |
| → Parse fail (pool_type) | 289 | 32.1% of raw CANDIDATEs |
| → L2 rejected | 591 | 65.7% of raw CANDIDATEs |
| → Blocked by trade limit | 12 | 1.3% of raw CANDIDATEs |
| **Final executable trades** | **7** | **0.8% of raw CANDIDATEs, 0.6% of AI calls** |

Additional: 13 PARSE_ERROR records (double JSON block format failure, all were AI CANDIDATE)

**Prescreen tolerance:** 1.0% of price (OB proximity, simulation-only gate)
**L2 entry tolerance:** 0.2% of price (`ob_price_tolerance_pct` in config)

---

## TASK 1: L2 Rejection Breakdown (n=591)

| Check | Count | % of 591 | Notes |
|-------|-------|----------|-------|
| `entry_in_ob` | 439 | 74.28% | Entry outside matched OB zone |
| `h1_poi_exists` | 141 | 23.86% | No H1 OB matched AI's cited price |
| `sl_beyond_ob` | 6 | 1.01% | SL not placed beyond OB low/high |
| `m15_choch_exists` | 5 | 0.85% | No M15 CHoCH/BOS with displacement |
| Other/unknown | 0 | 0.00% | — |
| **TOTAL** | **591** | **100%** | — |

**Critical finding:** No outcome data exists for rejected trades. The simulation computes `outcome` and `r_multiple` only for records with `decision == "CANDIDATE"` (final executable trades). For all 591 REJECTED_L2 records, the `outcome` field is absent. Hypothetical WR for rejected trades cannot be computed from this dataset.

**Best proxy available:** Historical batch simulation (no L2 gate) on same instrument: WR=66.3%, +39.5R on n=121 trades. This includes the universe of setups that L2 now rejects. Source: `t7_live_simulation_report_jan_mar11.md` header.

---

## TASK 2: Entry Distance Analysis (entry_in_ob failures, n=439)

**Preface:** For `entry_in_ob` failures, L2's `_check_entry_in_ob` (verification.py:401) runs ONLY when `h1_poi_exists` has already matched an OB to the AI's cited POI. So these 439 records DID have a matched OB — but the AI's entry price was outside that OB zone.

**Entry position relative to OB zone:**
- Entry ABOVE OB high: 438 (99.77%)
- Entry BELOW OB low: 1 (0.23%)

**Interpretation:** In 99.77% of cases, the AI set entry at current market price (above the OB zone), while the OB is a discount level that price had not yet retested. The ob_retest strategy requires entry AT the OB, not at current price.

**Distance from nearest OB edge (% of entry price):**

| Bucket | Count | % of 439 | Notes |
|--------|-------|----------|-------|
| 0.00–0.10% | 0 | 0.00% | — |
| 0.10–0.20% | 0 | 0.00% | Within L2 tolerance (0.2%) — none exist |
| **0.20–0.50%** | **54** | **12.30%** | Marginally outside; widening to 0.5% captures these |
| 0.50–1.00% | 66 | 15.03% | Would pass at 1.0% tolerance |
| 1.00–2.00% | 152 | 34.62% | Entry 45–90 pts from OB at XAUUSD ~4500 |
| 2.00–5.00% | 154 | 35.08% | Entry 90–225 pts from OB |
| 5.00%+ | 13 | 2.96% | Entry >225 pts from OB |

**Distance statistics:**
- Minimum: 0.227%
- Maximum: 6.550%
- Median: 1.781%
- Mean: 1.729%

**Key finding:** The minimum distance (0.227%) is just above the current 0.2% tolerance. None of the 439 failures are "borderline" — they all represent genuine entries outside the OB zone. The median at 1.78% (~$80 at current XAUUSD prices) indicates most failures have the AI entering well above the OB.

**Tolerance sensitivity (entry_in_ob only):**

| Tolerance | Additional passes | WR (hypothetical) |
|-----------|------------------|-------------------|
| 0.2% (current) | 0 | — |
| 0.5% | +54 | N/A (no outcome data) |
| 1.0% | +120 | N/A (no outcome data) |
| 2.0% | +272 | N/A (no outcome data) |
| 5.0% | +426 | N/A (no outcome data) |

**Answer to Task 2 question:** At 0.5% tolerance, 54 additional entry_in_ob records would pass L2. At 1.0% tolerance, 120 would pass. Outcome WR for these records cannot be computed — outcome data was only recorded for executed trades.

---

## TASK 3: H1 POI Existence Failures (n=141)

Two sub-categories:

| Sub-category | Count | % of 141 |
|-------------|-------|----------|
| AI cited specific price, no matching OB in MSO | 84 | 59.57% |
| AI reported `poi_identified=False` (no POI at all) | 57 | 40.43% |

### Sub-category A: AI cited specific price, no OB match (n=84)

The AI cited a specific POI midpoint (e.g., 4405.04) that corresponds to a zone it described in reasoning (e.g., 4397.01–4413.07). L2's `_find_matching_ob` looked for an unmitigated OB within 0.2% tolerance of that midpoint but found none.

**Most likely cause:** The AI is citing an OB that was **mitigated** (price already passed through it) by the time of the candle close. The MSO removes mitigated OBs from the "unmitigated" list, but the AI was trained to see them in the prompt data.

Distribution by month:
- January 2026: 21 failures (25.0%)
- February 2026: 31 failures (36.9%)
- March 2026 (to Mar 11): 32 failures (38.1%)

**Trend:** Cited-wrong failures are roughly uniform across months, suggesting a persistent AI behavior, not a market-regime-specific issue.

### Sub-category B: AI reported poi_identified=False (n=57)

The AI set `poi_identified=False` in its JSON response while simultaneously setting `decision=CANDIDATE`. L2 fails because there is no POI price to validate.

Distribution by month:
- January 2026: 1 failure (1.8%)
- February 2026: 44 failures (77.2%)
- March 2026 (to Mar 11): 12 failures (21.1%)

**Trend:** This failure mode is heavily concentrated in February (77% of all cases). February 2026 was a period of strong upward trend in XAUUSD (price moved from ~$4600 → $5200+). The AI appears to have struggled to identify discount OBs in a fast-moving trending market, issuing CANDIDATE on C-gate logic alone without a valid POI.

**This is a prompt engineering issue:** The T7 C-gate prompt evaluates only C1/C2/C3 (directional bias, M15 alignment, direction match). It does not enforce that `poi_identified=True` before issuing CANDIDATE for the ob_retest framework.

---

## TASK 4: Parse Failures Analysis

### NO_TRADE_PARSE_FAIL (n=289)

- All 289 were `decision=CANDIDATE` in the AI's raw response (confirmed via raw_response field scan)
- Parse failure caused by: `pool_type` field containing compound values (e.g., `"session_high / equal_highs"`, `"PDL / session_high"`) that violate the Pydantic Literal constraint
- L2 was skipped: `l2_reason = "PA parse failed — L2 requires structured output"`
- These represent valid AI CANDIDATE responses that were discarded due to a data model constraint

**Fix status:** Pool_type normalization fix deployed April 13, 2026 (commit `3c0ca9e`). In production, these responses now parse correctly.

**Impact on frequency picture:**
- If these 289 had parsed successfully, they would have entered the L2 pipeline
- Given the entry_in_ob rejection rate of 74.3%, estimated ~215 would have been rejected by L2 (assumes same distribution)
- Estimated ~74 additional non-L2-rejected records would result (would then hit limits or execute)
- **The fix does NOT directly increase final trade count** — L2 would still apply. The fix eliminates a data loss issue, not a frequency bottleneck.

### PARSE_ERROR (n=13)

Caused by AI outputting two JSON blocks (main response + corrected trade parameters block), causing JSON decode failure. Not related to pool_type. Separate issue requiring a different fix (e.g., extracting first JSON block only).

---

## TASK 5: Actionable Findings (data-derived)

### Finding 1: entry_in_ob tolerance — marginal benefit

**Data:** At 0.5% tolerance, 54 additional records would pass (12.3% of entry_in_ob failures). At 1.0%, 120 additional records. No outcome data available for these records.

**Constraint:** The median distance (1.78%) is well beyond any reasonable tolerance widening. 87.7% of entry_in_ob failures are more than 0.5% outside the OB zone — tolerance widening cannot address these.

**Reported fact:** Widening from 0.2% to 0.5% adds at most 54 records to the L2-passing pool. Without outcome data, WR cannot be stated.

### Finding 2: AI systematically cites wrong zones

**Data:**
- 84 h1_poi_exists failures = AI cites specific price but MSO has no unmitigated OB there
- Most likely cause: AI referencing mitigated OBs still visible in MSO prompt data
- 57 additional failures = AI says `poi_identified=False` but still issues CANDIDATE (prompt enforcement gap)

**Reported fact:** 23.9% of L2 rejections involve the AI citing a POI that doesn't exist in the current MSO unmitigated OB list. The majority of these (59.6%) cite a specific price level; 40.4% explicitly say no POI was identified.

### Finding 3: Hypothetical ceiling

**From the data:**
- If L2 were removed entirely: 899 raw CANDIDATEs over 47 trading days
- With max 1 trade/KZ and max 2/day (production limits), actual trades would be capped
- Historical batch reference (no L2): 66.3% WR, +39.5R on n=121 setups (different methodology)
- 7 actual trades = 42.9% WR, +0.55R — sample too small for significance

**Reported fact (no speculation):** The batch simulation without L2 produced 121 trades at 66.3% WR over the historical period. The production simulation with L2 produced 7 trades at 42.9% WR. The frequency gap (121 vs 7) is largely attributable to L2 rejection (591 records) and parse failures (289 records), with L2 being the dominant gate. Whether L2's rejected trades would have 66.3% WR is unknown without outcome data.

### Finding 4: Prescreen-L2 gap

**Data:** Prescreen uses 1.0% tolerance (simulation.py:192). L2 uses 0.2% (verification.py:93). The prescreen passes when price is within 1.0% of any H1 OB edge. But if the AI sets entry at current price and current price is in the 0.2%–1.0% distance range from the OB, L2 will reject.

**Reported fact:** Tightening the prescreen from 1.0% to 0.2% would eliminate API calls for setups that L2 will reject anyway (entry_in_ob). This would reduce simulation/production costs without changing trade frequency. The 54 records in the 0.2%–0.5% range would remain — but only if the prescreen tolerance were set to exactly 0.5%.

---

## MONTHLY BREAKDOWN OF ALL L2 REJECTIONS

| Month | API Calls | AI CAND | L2 Rejected | entry_in_ob | h1_poi_exists | sl_beyond | m15_choch |
|-------|-----------|---------|-------------|-------------|---------------|-----------|-----------|
| Jan 2026 | 392 | 312 | 195 | — | — | — | — |
| Feb 2026 | 580 | 429 | 292 | — | — | — | — |
| Mar 2026 (to 11) | 226 | 158 | 104 | — | — | — | — |
| **TOTAL** | **1198** | **899** | **591** | **439** | **141** | **6** | **5** |

Note: Monthly entry_in_ob/h1_poi breakdown not disaggregated by month in this analysis.

---

## SUMMARY TABLE

| Metric | Value | Source |
|--------|-------|--------|
| Total KZ candles | 1464 | all_results_jan_mar11.json |
| AI calls made | 1198 | records with cost > 0 |
| Raw AI CANDIDATE rate | 75.0% (899/1198) | decision field in raw_response |
| Total L2 rejections | 591 | decision == REJECTED_L2 |
| L2 rejection rate vs raw CAND | 65.7% | 591/899 |
| entry_in_ob | 439 (74.3% of rejects) | l2_reason field |
| h1_poi_exists | 141 (23.9% of rejects) | l2_reason field |
| sl_beyond_ob | 6 (1.0% of rejects) | l2_reason field |
| m15_choch_exists | 5 (0.8% of rejects) | l2_reason field |
| Parse fails (pool_type) | 289 | decision == NO_TRADE_PARSE_FAIL |
| Parse errors (format) | 13 | decision == PARSE_ERROR |
| Blocked by trade limit | 12 | decision == BLOCKED_LIMIT |
| Final trades | 7 | decision == CANDIDATE |
| Live CR | 0.6% (7/1198) | — |
| Live WR | 42.9% (3W/4L) | outcome field, CANDIDATE only |
| Outcome data for rejected | None | rejected records have no outcome field |

---

*Analysis complete. All numbers sourced from `research/t7_live_simulation/all_results_jan_mar11.json`. No fabrication. No outcome data available for rejected trades.*
