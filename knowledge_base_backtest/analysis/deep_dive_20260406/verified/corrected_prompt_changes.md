# CORRECTED Prompt Changes — Apr 6, 2026

Only changes supported by verified data with disc/val validation.

---
## Change 1: FVG Creation Signal (VALIDATED)

**Feature:** `creates_fvg`
**Evidence:** p=0.0, +11.0pp continuation when displacement creates FVG
**Disc:** True=0.5298 vs False=0.4121 (+11.8pp)
**Val:** True=0.5384 vs False=0.4365 (+10.2pp)
**Action:** When evaluating displacement quality, check if it created a Fair Value Gap.
If yes, this is a POSITIVE signal for continuation. Add to displacement quality assessment.

---
## Change 2: at_ob as CAUTION Signal (CORRECTED)

**Feature:** `at_ob`
**Evidence:** p=1.1e-05, -5.6pp continuation when at order block
**Disc:** True=0.4300 vs False=0.5040 (-7.4pp)
**Val:** True=0.4742 vs False=0.5106 (-3.6pp)
**PRIOR ERROR:** The prior session recommended at_ob as positive. It is NEGATIVE.
**Action:** When a displacement lands on an existing order block, treat this as a CAUTION.
The OB absorbs momentum and reduces continuation probability.
Do NOT weight at_ob positively in scoring.

---
## Change 3: Counter-Trend Caution (VALIDATED)

**Feature:** `ct`
**Evidence:** p=4.72e-04, 0.0515 effect
**Disc:** True=0.4659 vs False=0.4842 (-1.8pp)
**Val:** True=0.4396 vs False=0.5197 (-8.0pp)
**Action:** Counter-trend displacements have lower continuation. Downweight in scoring.

---
## Change 4: FVG Fill 80-100% Sweet Spot (FROM PER-RECORD)

**Evidence:** 80-100% fill has 0.7143 continuation (n=168)
**vs** <50% = 0.25 (n=272)
**vs** 50-80% = 0.449 (n=196)
**Action:** In FVG fill framework, prefer entries where fill is 80-100% of gap.
**Note:** No disc/val split available from per-record data. Use with caution.

---
## Change 5: Align >= 2 Filter (NEW — from untested features)

**Evidence:** p=0.0, monotonic 0.449→0.586
**Disc:** above_med=0.5169 vs below=0.442 (7.5pp)
**Val:** above_med=0.5465 vs below=0.4526 (9.4pp)
**Action:** Add timeframe alignment count to displacement evaluation.
Require align >= 2 (at least 2 of D1/H4/H1 agreeing with displacement direction).
This is the strongest untested feature and is NOT currently in the AI prompt.

---
## REMOVED from Prior Recommendations

### H4 Alignment — REMOVED
p=0.4986, effect=0.9pp — not significant.
Prior session may have recommended H4 alignment changes. Remove them.

### OTE Zone — REMOVED
p=0.6075, effect=-1.0pp — not significant.

---
## Summary of Validated Changes

| # | Change | Direction | Disc Effect | Val Effect | Status |
|---|--------|-----------|-------------|------------|--------|
| 1 | creates_fvg positive | + | +11.8pp | +10.2pp | VALIDATED |
| 2 | at_ob CAUTION | - | -7.4pp | -3.6pp | CORRECTED |
| 3 | ct downweight | - | -1.8pp | -8.0pp | VALIDATED |
| 4 | FVG fill 80-100% | + | N/A | N/A | NO SPLIT |
| 5 | align >= 2 | + | +7.5pp | +9.4pp | VALIDATED |