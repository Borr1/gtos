# Session 13 Handoff — Prompt Optimization T5-T8 + Strategic Decision Point

**Date:** April 13, 2026, 00:06 - 02:30 UTC
**Session type:** Strategic Advisor + Engineering
**Branch:** main
**Last commit:** `913d0d7` research: T3-T8 prompt optimization pipeline
**Status:** T7 and post-trade Phase 2 still running at handoff time

---

## EXECUTIVE SUMMARY

This session discovered that the AI evaluation prompt's discriminative signal comes ENTIRELY from the structural C-gate (H1 directional bias + M15 non-opposition). The Q1-Q7 scoring system, zone proximity checks, and all macro inputs have zero predictive power. Through T5→T6→T7→T8, we progressively stripped the prompt down to its minimum effective components.

**The key insight:** The LLM's only useful job is answering "Does H1 have clear directional bias, and is M15 not fighting it?" Everything else — zone proximity, RR calculation, scoring — either adds noise or actively destroys value.

**Three parallel agents were launched and may still be running:**
1. T7 (pure C-gate, zero zone info in prompt) — fixes 22 decision integrity violations from T6
2. T8 (C1+C3 only, no C2/M15 gate) — tests if M15 filtering adds value
3. Post-trade analysis (121 trades, wins AND losses) — searches for qualitative patterns

---

## WHAT YOU NEED TO DO

### Step 1: Check if agents finished

Look for these files:
- `research/academic_pipeline/data/T7_pure_cgate_results_v1.json` — T7 results
- `research/academic_pipeline/results/T7_pure_cgate_results_v1.md` — T7 report
- `research/academic_pipeline/data/post_trade_patterns_v1.json` — Post-trade Phase 2
- `research/academic_pipeline/results/post_trade_analysis_v1.md` — Post-trade report

If missing, the agents haven't finished. You may need to run the scripts manually:
```bash
# T7 (if not done)
source .venv/bin/activate && export $(grep ANTHROPIC_API_KEY .env | xargs)
python research/academic_pipeline/T7_pure_cgate_prompt.py --budget 4

# Post-trade Phase 2 (if Phase 1 done but Phase 2 not)
# Check post_trade_analysis.py for Phase 2 entry point
```

### Step 2: Read the results

**Required reading (in this order):**
1. This handoff (you're reading it)
2. `CLAUDE.md` — project instructions
3. `.context/00_core/quick_reference_card.md` — live numbers
4. The results files below (the core data)

**Result files to read and cross-reference:**

| Test | Results JSON | Report | What it tests |
|------|-------------|--------|---------------|
| T5 | `data/T5_structural_results_v1.json` | `results/T5_structural_results_v1.md` | C-gate + Q-checks as gates |
| T6 | `data/T6_cgate_only_results_v1.json` | `results/T6_cgate_only_results_v1.md` | C-gate only, zone "informational" |
| T7 | `data/T7_pure_cgate_results_v1.json` | `results/T7_pure_cgate_results_v1.md` | Pure C-gate, zero zone in prompt |
| T8 | `data/T8_c1c3_only_results_v1.json` | `results/T8_c1c3_only_results_v1.md` | C1+C3 only, no C2/M15 gate |
| Post-trade | `data/post_trade_individual_v1.json` | `results/post_trade_analysis_v1.md` | Win/loss pattern analysis |

**Also read the reviews (analysis context):**
- `results/T5_review_v1.md` — Sonnet agent's T5 review (3 bugs found)
- `results/T6_design_review_v1.md` — T6 design rationale and statistical analysis

### Step 3: Make the deployment decision

Compare all variants using this framework:

| Metric | P2A v1 (deployed) | Unfiltered | T5 | T6 | T7 | T8 |
|--------|-------------------|------------|----|----|----|----|
| CR | 38.0% | 100% | 24.0% | 66.9% | ? | ? |
| WR | 69.6% | 64.5% | 62.1% | 66.7% | ? | ? |
| CR×WR | 0.265 | 0.645 | 0.149 | 0.446 | ? | ? |
| Total R | +22.9R | +40.6R | +11.8R | +33.8R | ? | ? |
| Parse errors | 0 | — | 21 | 0 | ? | ? |

**Decision criteria:**
- Primary: highest Total R with WR ≥ 64.5% (unfiltered baseline)
- Secondary: highest CR×WR
- Constraint: WR must be statistically above 50% (p < 0.05)
- If T7/T8 ≈ unfiltered (+40.6R, 64.5% WR), the AI filter adds no value beyond H1 bias detection and the system should be simplified

---

## COMPLETE FINDINGS FROM THIS SESSION

### 1. Multi-Timeframe Expansion: KILLED

**File:** `results/multi_tf_foundation_test_v1.md`

Tested whether M15 OB setups aligned with H1 bias produce continuation rates >55%. Answer: NO.

- 42 statistical tests, 5 instruments, 37,831 M15 candles, 2+ years
- M15 OB at-candle continuation = 49.9% (random coin flip)
- Kill zone filtering makes it WORSE (48.4%)
- No filter combination survives Bonferroni correction
- The validated 70% rate is SPECIFIC to H1-structural-break context
- The 13pp gap (57% M15 revisit → 70% H1) IS the H1 edge

**Decision:** Multi-TF expansion as a frequency multiplier is permanently ruled out.

### 2. Scoring System Has Zero Predictive Power

**Evidence:** Point-biserial correlation r=-0.06, p=0.574. CANDIDATE losers score HIGHER (88.5) than winners (86.6). The Q1-Q7 scoring is noise.

The only discriminative component in P2A v1 was the C-gate (C1/C2/C3). The 4 high-score trades rejected by C-gate were ALL losers (+5.6pp WR lift from C-gate).

### 3. MSO Data Gap: Root Cause of Low Frequency

- H4 data present in 0% of the 121 matched MSOs
- D1 data present in 0% of the 121 matched MSOs
- H1 present in 100%, M15 present in 100%
- The P2A v1 prompt's C1 requires D1→H4→"2 of 3 agree" — impossible condition
- The LLM was FABRICATING H4 alignment from H1 data (all 46 CANDIDATEs had h4_alignment:true while saying "no H4 data provided")
- The 65-point scoring threshold was the real rejection gate (85% of rejections were score-based)

### 4. T5 Results: Q-Checks Destroy Best Trades

**File:** `results/T5_structural_results_v1.md`
**CR=24%, WR=62.1%, Total R=+11.8R** — worse than P2A v1

But the failure revealed the critical insight:

| Decision | n | WR | Total R |
|----------|---|-----|---------|
| CANDIDATE | 29 | 62.1% | +11.8R |
| WAIT (Q-check reject) | 35 | **74.3%** | **+23.0R** |
| PARSE_ERROR | 21 | 71.4% | +9.5R |
| NO_TRADE (C-gate reject) | 36 | 52.8% | -3.6R |

**Q-checks rejected the BEST trades.** 25 WAITs were Q2 proximity failures — the LLM computed close-price distance from zone, but entries happen at the wick (low for longs). The measurement was wrong.

**C-gate pass combined (CAND+WAIT+PARSE):** n=85, WR=69.4%, R=+44.2R — this became the target.

### 5. T6 Results: C-Gate Only, Zone "Informational"

**File:** `results/T6_cgate_only_results_v1.md`
**CR=66.9%, WR=66.7%, CR×WR=0.446, Total R=+33.8R** — beats P2A v1

But 22 out of 40 NO_TRADEs were **decision integrity violations**: the LLM acknowledged all C-gates pass but rejected anyway based on zone proximity. The "informational" label didn't prevent leakage. Many responses literally said "all three C-gates pass structurally, but the OB Retest framework requires price to be retesting an unmitigated order block."

Those 22 violations: 15 wins, 7 losses = 68.2% WR, +7.4R. Good trades thrown away.

**C-gate failure breakdown (corrected — the Sonnet agent's report was wrong):**
- Decision integrity violations (C pass, rejected on zone): 22
- True C2 failures (m15=opposing): 17
- True C1 failures (h1=unclear): ~1
- Total NO_TRADE: 40

The Sonnet agent's report claimed "C2 failures: 33, C1 failures: 7" — this was wrong because the report's parsing logic lumped violations into the wrong category. The actual m15_status distribution in NO_TRADEs: aligned=23, opposing=17.

If the LLM had followed instructions: 103 CANDIDATEs, CR=85%, WR≈67%, R≈+41.2R.

### 6. T8 Results (from agent — needs verification)

**File:** `results/T8_c1c3_only_results_v1.md` (read this — I haven't verified it)

The agent reported results but I didn't get to verify the raw numbers. The fresh session MUST verify T8 by loading `data/T8_c1c3_only_results_v1.json` and computing CR, WR, Total R independently.

### 7. T7 Results (may still be running)

Check for `data/T7_pure_cgate_results_v1.json`. If it exists, verify independently.

### 8. Post-Trade Analysis (may be partially complete)

- Phase 1 (individual analyses): `data/post_trade_individual_v1.json` — 121 trades analyzed
- Phase 2 (pattern aggregation): `data/post_trade_patterns_v1.json` — may not exist yet
- Report: `results/post_trade_analysis_v1.md` — may not exist yet

If Phase 2 didn't run, it needs to be executed. The script is `post_trade_analysis.py`.

### 9. Patrick Podcast Research (3 tests)

**File:** `research/kap_outputs/exbank_trader_patrick_transcript_analysis.md`

| Test | Verdict | Action |
|------|---------|--------|
| FTMO partial close Variant C (33% @ 1.0R) | INCONCLUSIVE (+4.9pp, gate was 5pp) | Shadow-log on live trades |
| OB touch decay (first touch 72.7% vs T2+ 31.7%) | CONFIRMED | None — already in architecture |
| Real rates gold filter | REJECT (p=0.74) | None — 3rd macro null result |

Variant C details: `results/FTMO_survival_optimization_results_v1.md`
- P(pass FTMO) improves from 93.4% to 98.3%
- 0% DD breach (vs 0.5% current)
- Terminal equity $134,784 (vs $131,655)
- The shadow logger needs to be built and deployed alongside whatever prompt wins

### 10. Macro Overlay Research Path: CLOSED

Three null results:
- COT data: p=0.495
- DXY correlation: R²=0.136
- Real rates: p=0.74

GTOS's edge is structural/mechanical, not macro-dependent at H1 frequency. No more macro inputs should be tested for the entry prompt.

---

## OPEN DECISIONS FOR THE FRESH SESSION

1. **Pick the deployment prompt:** Compare T6 vs T7 vs T8. The winner gets deployed.
   - If T7 ≈ T6 simulated ceiling (+41.2R), zone info removal fixed the violations
   - If T8 ≈ unfiltered, C2 adds nothing and the system simplifies to "H1 has bias? → CANDIDATE"
   - If T8 WR < T7 WR, C2 adds value and should be kept

2. **Post-trade analysis integration:** If patterns found, incorporate into the winning prompt as T9. If no patterns, accept that the C-gate is the ceiling.

3. **Variant C shadow logger:** Build and deploy alongside the winning prompt. Code task, no API cost.

4. **Live deployment path:** The winning prompt needs to be translated into `src/prompts/primary_analyzer_prompt.py` format, compatible with the orchestrator's JSON parser (`src/components/primary_analyzer.py`). Check the output schema matches what the orchestrator expects.

5. **Canary fixtures:** The 10 existing canary fixtures all baseline NO_TRADE. With a more permissive prompt (CR 65-85%), most will flip to CANDIDATE. New borderline canary fixtures are needed.

---

## STATISTICAL WARNINGS

- All findings are in-sample (n=121). No held-out set exists.
- WR differences between T6 (66.7%) and unfiltered (64.5%) are NOT statistically significant at n=81-121
- The meaningful comparison is Total R (captures both CR and WR effects)
- CR×WR is the best single metric for comparing prompt variants
- Any "pattern" from post-trade analysis at n=121 needs skepticism — especially if it only appears in <10 trades

---

## FILES NOT YET COMMITTED

These will exist after agents finish:
- T7 results (data/ and results/)
- Post-trade Phase 2 (data/post_trade_patterns_v1.json, results/post_trade_analysis_v1.md)
- Any files the agents create during execution

Commit these when they appear:
```bash
git add research/academic_pipeline/data/T7_* research/academic_pipeline/results/T7_*
git add research/academic_pipeline/data/post_trade_patterns* research/academic_pipeline/results/post_trade*
git commit -m "research: T7 + post-trade analysis results (pending verification)"
```

---

## SCRIPTS REFERENCE

All test scripts follow the same pattern and can be re-run:
```bash
source .venv/bin/activate && export $(grep ANTHROPIC_API_KEY .env | xargs)
python research/academic_pipeline/T7_pure_cgate_prompt.py --budget 4
python research/academic_pipeline/T8_c1c3_only_prompt.py --budget 4
python research/academic_pipeline/post_trade_analysis.py --budget 6
```

---

## VERIFIED NUMBERS (from this session's analysis)

| Fact | Value | Evidence |
|------|-------|----------|
| Q1-Q7 score correlation with wins | r=-0.06, p=0.574 | Point-biserial on 121 trades |
| P2A v1 rejection cause | 85% score-based, 13% C1, 0% H4 | no_trade_reason analysis |
| H4 in matched MSOs | 0/121 = 0% | MSO field search |
| D1 in matched MSOs | 0/121 = 0% | MSO field search |
| LLM fabricated H4 alignment | 46/46 CANDIDATEs | h4_alignment:true with "no H4 data" |
| T6 decision integrity violations | 22/40 NO_TRADEs | m15_status=aligned, h1=bullish, decision=NO_TRADE |
| T6 violation WR | 68.2% (15/22) | Direct count |
| T6 violation R | +7.4R | Sum of r_multiple |
| M15 OB continuation rate | 49.9% | 11,248 events, 5 instruments, 2+ years |
| OB touch decay cliff | T1=72.7%, T2=31.7% | 106,147 events, 13 instruments |
| Macro overlay signal | 0/3 tests significant | COT, DXY, real rates all null |

---

*Handoff complete. All artifacts are on main. The fresh session has everything it needs to make the deployment decision.*
