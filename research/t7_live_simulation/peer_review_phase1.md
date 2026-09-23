# T7 Simulation Peer Review — Phase 1: Independent Data Review

**Reviewer:** Claude Code (independent instance)
**Date:** 2026-04-13
**Methodology:** Read all source files, ran independent counts against raw JSON, did not read any prior analysis before forming conclusions.

---

## Files Reviewed (in order)

1. `CLAUDE.md` — system context, edge mechanism, architecture
2. `scripts/simulate_t7_live_period.py` — full simulation pipeline (~981 lines)
3. `research/t7_live_simulation/XAUUSD_t7_simulation.json` — 1,464 per-candle records
4. `research/t7_live_simulation/t7_live_simulation_report.md` — auto-generated report
5. `research/academic_pipeline/data/T7_pure_cgate_results_v1.json` — 121 batch evaluations
6. `src/components/primary_analyzer.py` (lines 240-450) — production parse/validate path
7. `tests/test_simulation_fixes.py` — what was fixed and why

---

## A. Final Executable Trades — Count and Detail

**7 trades total.** Verified by direct count from raw JSON (decision="CANDIDATE").

| # | Date | Time | KZ | Dir | Entry | SL | TP | Outcome | R | l2_passed |
|---|------|------|-----|-----|-------|----|----|---------|---|-----------|
| 1 | 2026-01-15 | 13:15 | ny | LONG | 4618.93 | 4597.79 | 4650.62 | LOSS | -1.0R | True |
| 2 | 2026-01-20 | 16:00 | ny | LONG | 4727.61 | 4715.35 | 4745.99 | WIN | +1.5R | True |
| 3 | 2026-01-21 | 15:00 | ny | LONG | 4869.07 | 4855.09 | 4890.04 | LOSS | -1.0R | True |
| 4 | 2026-01-27 | 07:00 | london | LONG | 5064.67 | 5055.17 | 5079.42 | WIN | +1.55R | True |
| 5 | 2026-02-06 | 07:00 | london | LONG | 4826.29 | 4801.10 | 4864.03 | WIN | +1.5R | True |
| 6 | 2026-02-20 | 15:00 | ny | LONG | 5042.42 | 5007.00 | 5095.49 | LOSS | -1.0R | True |
| 7 | 2026-03-10 | 16:00 | ny | LONG | 5200.47 | 5162.26 | 5257.78 | LOSS | -1.0R | True |

**Observation:** All 7 trades are LONG. Zero SHORT trades over 10 weeks.

---

## B. WR and Total R — Report vs Raw Data

| Metric | Report Claims | Raw Data | Match? |
|--------|--------------|----------|--------|
| Final trades | 7 | 7 | ✓ |
| Wins | 3 | 3 | ✓ |
| Losses | 4 | 4 | ✓ |
| WR | 42.9% | 42.86% | ✓ (rounding) |
| Total R | +0.6R | +0.55R | ✗ Off by 0.05R |

**The report claims +0.6R but the actual sum is +0.55R:**
- Wins: 1.50 + 1.55 + 1.50 = +4.55R
- Losses: 4 × (-1.0R) = -4.0R
- Net: +0.55R

This is a rounding discrepancy of 0.05R in the report. Not a fabrication — just imprecise rounding. The sign (positive) is correct.

---

## C. NO_TRADE_PARSE_FAIL Records — What They Mean

**289 records** with decision=`NO_TRADE_PARSE_FAIL`.

These are cases where:
1. The API was called (cost was incurred)
2. The AI returned a syntactically valid JSON response with `decision: "CANDIDATE"`
3. `PrimaryAnalysisOutput.model_validate(data)` failed — the JSON structure didn't match the Pydantic schema
4. The simulation set `decision = "NO_TRADE_PARSE_FAIL"` and `l2_passed = "skipped"`
5. **L2 was NEVER run on these 289 records**

This is confirmed by all 289 records having `l2_passed = 'skipped'` (verified in raw data).

These records did NOT bypass L2 — they were eliminated BEFORE L2 by the parse failure gate.

---

## D. Did the 7 CANDIDATE Trades Go Through L2?

**Yes — all 7 went through L2 and PASSED.**

Every CANDIDATE record in the raw JSON has `l2_passed = True`. This is the exact opposite of "bypassed L2."

The pipeline logic (confirmed from `simulate_t7_live_period.py` lines 681-705):
```
IF pa_obj is not None:
    run verify_candidate(pa_obj, mso) → if fails, REJECTED_L2
    if passes → stays CANDIDATE (l2_passed=True)
ELSE (pa_obj is None):
    decision = NO_TRADE_PARSE_FAIL, l2_passed = 'skipped'
```

The 7 final trades are the records where: (a) AI parsed successfully into PrimaryAnalysisOutput AND (b) L2 passed all 6 checks.

---

## E. Production vs Simulation Parse-Failure Handling

**They differ:**

**Simulation path** (lines 699-705 in simulate_t7_live_period.py):
```
pa_obj is None → NO_TRADE_PARSE_FAIL immediately
(cannot retry — too expensive)
```

**Production path** (primary_analyzer.py lines 256-268):
```
_parse_and_validate(raw) raises → retry with _FORMAT_CORRECTION prompt
If retry succeeds → normal CANDIDATE/NO_TRADE flow
If retry fails → NO_TRADE("ai_output_malformed")
```

**Implication:** Production gives the AI a second chance. Some of the 289 simulation parse failures might have become valid CANDIDATEs in production after the retry prompt. The simulation is MORE CONSERVATIVE than production for these cases. The retry could theoretically produce more trades — but whether those would pass L2 is unknown without running the retries.

---

## F. Batch Data: WR and R Split by Proximity (Independent Count)

Source: `T7_pure_cgate_results_v1.json`, rows with `decision == "CANDIDATE"` (n=104).

| Proximity | n | Wins | WR | Total R | % of All R |
|-----------|---|------|----|---------|------------|
| inside | 21 | 13 | 61.9% | +13.3R | 34% |
| approaching | 29 | 22 | 75.9% | +20.7R | 52% |
| far | 46 | 29 | 63.0% | +3.1R | 8% |
| none | 8 | 5 | 62.5% | +2.4R | 6% |

**Combined groups:**

| Group | n | WR | Total R | % of All R |
|-------|---|----|---------|------------|
| inside + approaching | 50 | 70.0% | +34.1R | **86%** |
| far + none | 54 | 63.0% | +5.5R | **14%** |
| **All CANDIDATE** | **104** | **66.3%** | **+39.5R** | 100% |

**Key finding:** inside+approaching trades (n=50) account for 86% of total batch R despite being 48% of trades. The "approaching" subcategory is the strongest: 75.9% WR and +20.7R.

---

## G. Is n=7 Sufficient for Conclusions?

**No. n=7 is statistically meaningless for this system.**

Using normal approximation for binomial proportion (p=3/7=0.429):
- SE = sqrt(0.429 × 0.571 / 7) = 0.187
- 95% CI: 0.429 ± 1.96 × 0.187 = **[6.2%, 79.5%]**

The confidence interval spans from "barely above chance" to "clearly profitable." No useful inference is possible.

Additional context: the system was designed with in-sample WR=66.3% (batch n=104). With n=7, we cannot distinguish between a WR of 43% being (a) true system performance, (b) normal variance around 66%, or (c) systematic degradation.

**Required sample size** for 80% power to detect 10pp degradation (66% → 56%): approximately n=200+.

---

## H. Gold Trend Context — Price Discrepancy

**The CEO's framing of "$2620 to $2920" does NOT match the simulation data.**

The simulation entry prices range from $4618.93 (Jan 15) to $5200.47 (Mar 10). This is the actual XAUUSD price context in the MT5 data.

- Simulation period: approximately $4619 to $5200 = +$581 (+12.6%) over ~8 weeks
- CEO framing: "$2620 to $2920" — these prices are inconsistent with the simulation data

**The direction is still correct:** strong bullish trend. The magnitude is approximately +12.6% over the simulation period. The implication for interpretation is valid: a zone-retest system (which requires price to return to prior support/resistance) will naturally trade less frequently in a strong uptrend, as price keeps making new highs and leaves zones behind below.

However, the specific dollar figures cited in the CEO's framing appear to be incorrect for this time period and should not be used as a market reference.

---

## Summary of Raw Counts (cross-checked against report)

| Record type | Raw count | Report says | Match? |
|-------------|-----------|-------------|--------|
| Total KZ candles | 1,464 | 1,464 | ✓ |
| Prescreen skip | 217 | 217 | ✓ |
| No bias skip | 0 | 0 | ✓ |
| First NY skip | 49 | 49 | ✓ |
| AI returned NO_TRADE | 286 | (not shown separately) | — |
| AI returned CANDIDATE (raw) | 899 | 899 | ✓ |
| PARSE_ERROR (non-JSON response) | 13 | (not shown separately) | — |
| REJECTED_L2 | 591 | 591 | ✓ |
| NO_TRADE_PARSE_FAIL | 289 | 289 | ✓ |
| BLOCKED_LIMIT | 12 | 12 | ✓ |
| Final CANDIDATE trades | 7 | 7 | ✓ |
| Total API calls (cost > 0) | 1,198 | 1,198 | ✓ |

**Report numbers are accurate** except for the +0.6R total R (actual is +0.55R).

---

## Additional Observations Not Asked

1. **Simulation ended March 11, not April 10.** The $30 budget was hit partway through ($35.03 final), so ~5 weeks of data (Mar 11 – Apr 10) were not simulated.

2. **0% SHORT rate.** Zero SHORT trades in 7 weeks. Combined with an all-LONG batch record, this suggests the bias injection strongly favors bullish setups. This is plausible given the 2026 gold uptrend.

3. **No inverted TP corrections.** All 0 corrections — consistent with the system's 2% inverted TP rate (~0.2 corrections expected at 7 trades, so 0 is within normal range).

4. **The 13 PARSE_ERROR records** (fully invalid JSON from API) are a separate category not discussed in the report. These failed before any decision extraction — JSON.loads() itself failed. They represent 1.1% of API calls.

---

## Ready for Phase 2

I have formed my independent conclusions from the raw data. I have not read any prior analysis from other agents. Ready to arbitrate the two competing analyses.
