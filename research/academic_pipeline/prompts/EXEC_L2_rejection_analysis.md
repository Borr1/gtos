# EXEC — L2 Rejection Analysis (XAUUSD Jan-Mar 2026)

**For:** Fresh Claude Code terminal (Sonnet, max effort)
**Task type:** Data analysis ($0 API cost, pure computation)
**Estimated time:** 30-45 minutes
**Output:** Committed markdown report + JSON summary

---

## YOUR ROLE

You are an execution agent analyzing why 66% of AI CANDIDATE decisions are rejected by L2 verification in the T7 production simulation. Your job is to produce NUMBERS, not opinions. Every claim must cite a file path and line/record.

**You DO:**
- Read the specified files
- Compute statistics from the data
- Report raw numbers with evidence
- Save results to specified output files

**You DO NOT:**
- Make trading recommendations
- Modify src/ or prompts/
- Speculate without data
- Round aggressively (keep 2 decimal places)

---

## CONTEXT (read this to understand the system)

### What is L2?
L2 verification (`src/components/verification.py`) runs AFTER the AI returns a CANDIDATE decision. It performs deterministic checks on the AI's proposed trade:

1. `entry_in_ob` — Is the AI's entry price within tolerance of an actual H1 OB zone?
2. `h1_poi_exists` — Does the H1 OB the AI cites actually exist in the MSO?
3. `sl_beyond_zone` — Is SL placed correctly beyond the zone?
4. `tp_geometry` — Is TP on the correct side of entry?
5. `rr_minimum` — Does R:R meet the 1.5 minimum?

### The problem
The T7 simulation (Jan 2 – Mar 11, 2026) produced:
- 899 AI CANDIDATEs
- 591 L2 rejections (66%)
- Only 7 final executable trades

This is a massive frequency problem. We need to understand WHICH L2 checks are rejecting and WHY.

### Key files to read

**Primary data source:**
- `research/t7_live_simulation/all_results_jan_mar11.json` — Full simulation results (1464 records)

**To understand L2 logic:**
- `src/components/verification.py` — L2 check implementations (read lines 200-350)

**For context on the simulation:**
- `research/t7_live_simulation/t7_live_simulation_report_jan_mar11.md` — Summary report

---

## TASK 1: L2 Rejection Breakdown

Parse `all_results_jan_mar11.json` and for every record where:
- `decision == "CANDIDATE"` (AI said trade)
- `l2_result == "REJECTED"` or similar rejection indicator

Extract and count:
1. **Which L2 check rejected?** Group by rejection reason.
2. **What was the actual outcome?** (win/loss) — This tells us if L2 is rejecting good or bad trades.

### Expected output format

```
L2 REJECTION BREAKDOWN (n=591)
==============================
Check                  | Count | % of rejects | Outcome if traded (WR)
-----------------------|-------|--------------|------------------------
entry_in_ob            |   XXX |        XX.X% | XX.X% (n=XX)
h1_poi_exists          |   XXX |        XX.X% | XX.X% (n=XX)
sl_beyond_zone         |   XXX |        XX.X% | XX.X% (n=XX)
tp_geometry            |   XXX |        XX.X% | XX.X% (n=XX)
rr_minimum             |   XXX |        XX.X% | XX.X% (n=XX)
parse_fail             |   XXX |        XX.X% | XX.X% (n=XX)
other/unknown          |   XXX |        XX.X% | XX.X% (n=XX)
```

**Critical:** For each rejected trade, determine what the OUTCOME would have been by checking if the candle sequence would have hit TP or SL. The simulation already computed this — look for `outcome` or `would_have_won` fields.

---

## TASK 2: Entry Distance Analysis (for entry_in_ob failures)

For every `entry_in_ob` rejection:

1. What entry price did the AI quote?
2. What H1 OBs were available in the MSO?
3. What is the distance (in price and %) from AI entry to nearest OB edge?

### Expected output format

```
ENTRY DISTANCE ANALYSIS (entry_in_ob failures)
==============================================
Distance from OB edge | Count | % | WR if traded
----------------------|-------|---|-------------
0-0.1%                |   XXX | X% | XX.X%
0.1-0.2%              |   XXX | X% | XX.X%
0.2-0.5%              |   XXX | X% | XX.X%
0.5-1.0%              |   XXX | X% | XX.X%
>1.0%                 |   XXX | X% | XX.X%

Current L2 tolerance: 0.2% of price
```

**Question to answer:** If we widened the `entry_in_ob` tolerance from 0.2% to 0.5%, how many more trades would pass L2? What would their WR be?

---

## TASK 3: H1 POI Existence Failures

For every `h1_poi_exists` rejection:

1. What H1 level did the AI cite?
2. What H1 OBs were actually in the MSO?
3. Is there a pattern? (AI citing mitigated OBs? AI citing wrong price levels? AI fabricating?)

### Expected output format

```
H1 POI EXISTENCE FAILURES (n=XXX)
=================================
Failure reason             | Count | %
---------------------------|-------|----
AI cited mitigated OB      |   XXX | XX%
AI price far from any OB   |   XXX | XX%
No OBs in MSO at all       |   XXX | XX%
Other                      |   XXX | XX%
```

---

## TASK 4: Parse Failures (pool_type issues)

The simulation had 289 parse failures, all caused by `pool_type` normalization (now fixed). For completeness:

1. How many of the 289 were in the CANDIDATE pool?
2. What would their outcomes have been?
3. Does the fix (deployed Apr 13) change the frequency picture?

---

## TASK 5: Actionable Recommendations

Based on the data (NOT speculation), answer:

1. **Would widening `entry_in_ob` tolerance improve frequency without killing WR?**
   - Report: "At X% tolerance, Y additional trades pass with Z% WR"

2. **Is the AI systematically citing wrong zones?**
   - Report: "X% of h1_poi_exists failures are [pattern]"

3. **What's the hypothetical ceiling?**
   - Report: "If L2 passed all CANDIDATEs, WR would be X%, Total R would be Y"

---

## OUTPUT FILES

Save your results to:

1. `research/academic_pipeline/results/L2_rejection_analysis_v1.md` — Full report with all tables
2. `research/academic_pipeline/data/L2_rejection_summary.json` — Machine-readable summary:

```json
{
  "total_candidates": 899,
  "total_l2_rejected": 591,
  "rejection_rate": 0.657,
  "breakdown": {
    "entry_in_ob": {"count": N, "pct": X, "hypothetical_wr": Y},
    "h1_poi_exists": {"count": N, "pct": X, "hypothetical_wr": Y},
    ...
  },
  "tolerance_sensitivity": {
    "current_0.2pct": {"passes": N, "wr": X},
    "widened_0.5pct": {"passes": N, "wr": X},
    "widened_1.0pct": {"passes": N, "wr": X}
  },
  "if_no_l2": {"total_r": X, "wr": Y}
}
```

---

## VALIDATION CHECKS (do these to verify your work)

1. **Sum check:** rejection breakdown counts should sum to total L2 rejections
2. **Source verification:** For 3 random records, manually verify by reading the JSON
3. **WR sanity:** Hypothetical WR for rejected trades should be computable from outcome fields
4. **Parse fail count:** Should be 289 (known from prior analysis)

---

## PITFALLS TO AVOID

1. **Don't confuse decision fields.** `decision` is what AI said. `l2_result` is verification outcome. `outcome` is what would have happened.

2. **Don't assume field names.** First read a few records to understand the actual JSON structure. Report the field names you find.

3. **Don't fabricate outcomes.** If outcome data is missing for some records, report "N/A" not a guess.

4. **Don't modify source files.** This is read-only analysis.

5. **Pool_type fix is deployed.** The 289 parse failures are from BEFORE the fix. In production, these now parse correctly.

---

## WHAT "DONE" LOOKS LIKE

- [ ] All 5 tasks completed with tables
- [ ] Both output files created and saved
- [ ] All 4 validation checks passed
- [ ] Raw numbers reported (not just "most failures are X")
- [ ] File paths cited for key claims

---

*Prompt written by Strategic Advisor, April 13, 2026*
*For execution by fresh Claude Code terminal*
