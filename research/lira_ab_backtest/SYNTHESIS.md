# LIRA A/B 12-Slice Backtest — Synthesis

**Generated:** 2026-04-25 00:24 UTC
**Branch:** research/lira-ab-backtest-p3 (DO NOT merge / push)
**Cost:** $32.70 of $80 budget
**Pre-reg hash:** `3d7a07e30eef41cf721e29969a1780e2d20fb883a9f9ba2849465f316ed58368` (LF-normalized)
**Verdict:** **LIRA-STAY**

---

## Executive summary

**LIRA underperforms V3 (production prompt) at full 12-slice methodological
parity.** The DP4-extension surprise (+0.486R Exp R on 3-slice n=17 mini
backtest) does NOT replicate at 12-slice scale (n=48 fills). LIRA's actual
fleet expectancy is **+0.094R**, well below A2's V3 baseline (+0.333R) and
below the DP4 mini-backtest result by **0.39R**.

The mechanism of LIRA's underperformance:

1. **LIRA emits MORE candidates than V3** (54 vs 37, +46%). The extra CANDs
   are mostly LONGs in USDJPY that V3's stricter filter would have rejected.
2. **The extra CANDs lose more often than they win**, dragging fleet WR down
   from V3's 53.3% to LIRA's 43.8%.
3. **Tighter SL placement** on shared setups: LIRA places SLs systematically
   closer to entry than V3 (median 0.2-0.4% tighter on common XAUUSD LONGs).
   In one case (xauusd_s3 01-30T08:00), the 12.94-point SL difference
   converted V3's WIN into LIRA's LOSS.
4. **MaxDD 9R vs 3R baseline** — LIRA fleet hits 3× the drawdown of V3.

**Recommendation: V3 stays as production prompt.** LIRA is shelved as a
research direction. The 3-slice DP4 surprise was a small-sample anomaly,
not a real edge.

---

## 3-way comparison: V2 (F3) vs V3 (A2) vs LIRA — same 12 slices

| Metric | V3 F3 (v2 detector) | V3 A2 (v2 detector) | **LIRA (this run)** | Delta vs A2 |
|---|---:|---:|---:|---:|
| Detector | v2 | v2 | v2 | identical |
| System prompt | V3 production | V3 production | LIRA decision-first | swapped |
| Fleet raw CAND | 588 | 37 | **54** | +17 |
| Fleet filled | 32 | 30 | **48** | +18 |
| Fleet WR | 56.2% | 53.3% | **43.8%** | -9.5pp |
| **Fleet Exp R** | **+0.407R** | **+0.333R** | **+0.094R** | **-0.239R** |
| Fleet Total R | +13.0R | +10.0R | **+4.5R** | -5.5R |
| Fleet MaxDD | n/a | 3.0R | **9.0R** | +6R |
| Parse rate | n/a | n/a | **0.0%** | clean |
| API cost | $37.50 | $37.59 | **$32.70** | -13% |
| Prompt size | 23,252 chars | 23,252 chars | **12,625 chars** | -45.7% |

LIRA delivered cost savings (45.7% shorter prompt → 13% lower API spend) but
those savings come with a ~0.24R/trade expectancy degradation. The economic
trade is not worth it.

Note: F3's higher raw-CAND count (588) is from the F3 logger schema which
emits a row for every prescreen-attempted candle. A2's lower count (37) and
LIRA's similar count (54) are post-prescreen API-call CANDs only — apples to
apples between A2 and LIRA.

---

## Why LIRA underperforms — three mechanisms

### Mechanism 1: Over-permissive on low-edge USDJPY LONGs

USDJPY in F3/A2 was the strongest pair (Exp R +0.447R). LIRA dropped that to
**+0.029R** — a **0.42R/trade collapse**. Per-slice:

| Slice | A2 USDJPY filled / R | LIRA USDJPY filled / R | Delta R |
|---|---:|---:|---:|
| usdjpy_s1 | 6 / +1.5R | 8 / +2.0R | +0.5R (LIRA caught more, even net+) |
| usdjpy_s2 | 6 / +6.5R | 9 / +3.5R | -3.0R (extra 3 LIRA CANDs lost) |
| usdjpy_s3 | 2 / +0.5R | 8 / -0.5R | -1.0R (LIRA produced 6 extra LONGs, only 3 WIN) |
| usdjpy_s4 | 5 / 0R | 9 / -4.0R | -4.0R (LIRA produced 4 extra LONGs, all LOSS) |

**LIRA produced 39 USDJPY raw CANDs vs V3's 24 — 63% MORE setups.** But
LIRA's USDJPY WR is 42.4% vs V3's 57.9%. The LIRA prompt loosened V3's
filter without preserving its discrimination.

### Mechanism 2: SL placement systematically tighter than V3

On 9 LONG/SHORT setups where LIRA + V3 produced the SAME (slice, candle,
direction) tuple with > 0.1% SL divergence:

- 7/9: LIRA SL was TIGHTER (closer to entry)
- 1 case turned WIN → LOSS (xauusd_s3 01-30T08:00, 12.94 point tighter SL)
- 0 cases turned LOSS → WIN

V3's "looser" SL is actually doing useful work — it's wide enough to absorb
typical noise while still capturing structural reversal. LIRA's tighter SL
gets stopped out on noise.

### Mechanism 3: SHORT-SL DP4 hypothesis does NOT replicate

DP4-extension claimed: "V3 misplaced SL on 2/3 SHORTs in xauusd_s7 (one
wrong-side, one tight-sweep); LIRA placed them correctly."

Actual 12-slice data on XAUUSD SHORTs:
- LIRA: 3 SHORT CANDs in s7, 2 WIN @ 1.5R, 1 UNFILLED. Total +3.0R.
- A2 (V3): 4 SHORT CANDs (s5 + s7), 2 WIN @ 1.5R, 2 UNFILLED. Total +3.0R.

**Both LIRA and V3 placed SHORT SLs CORRECTLY in this run.** No wrong-side or
tight-sweep failures observed. The DP4 surprise was a data-thin one-off,
not a systematic V3 weakness.

---

## Per-slice details

| Slice | LIRA Filled / R | A2 Filled / R | Difference |
|---|---:|---:|---:|
| xauusd_s1 | 0 / 0R | 0 / 0R | tie (cold-start) |
| xauusd_s2 | 1 / -1R | 1 / -1R | tie |
| xauusd_s3 | 8 / +4.5R | 5 / +2.5R | LIRA +2R (3 extra LONG WINs) |
| xauusd_s4 | 0 / 0R | 0 / 0R | tie |
| xauusd_s5 | 2 / -2R | 2 / -2R | tie |
| xauusd_s6 | 0 / 0R | 1 / +1.5R | A2 +1.5R (LIRA missed 1 WIN) |
| xauusd_s7 | 2 / +3R | 2 / +3R | tie |
| xauusd_s8 | 1 / -1R | 0 / 0R | A2 +1R (LIRA produced extra LOSS) |
| usdjpy_s1 | 8 / +2R | 6 / +1.5R | LIRA +0.5R (caught more) |
| usdjpy_s2 | 9 / +3.5R | 6 / +6.5R | A2 +3R (LIRA's extra LOSE) |
| usdjpy_s3 | 8 / -0.5R | 2 / +0.5R | A2 +1R (LIRA's extra LOSE) |
| usdjpy_s4 | 9 / -4R | 5 / 0R | A2 +4R (LIRA's extra LOSE) |

**Net: LIRA +4.5R vs A2 +10R = -5.5R deficit over 12 slices.**

---

## Parse error rate at scale

**LIRA produced 0/1173 parse errors (0.0%)** — well under the 5% threshold.

This is contingent on the schema_adapter fix landed pre-launch (commit
4892008). Without that fix, LIRA's double-block self-correction emissions
would have produced ~5-15% parse errors.

The original 60-fixture LIRA canary (commit dec9554/f4a6daa) saw 0/60 parse
errors but didn't trigger the double-block path that production-like data
exposes. The fix is purely additive in the research code path
(`research/v4_prompt_engineering/dp4_lira/schema_adapter.py`); production
`src/utils/validation.py` was not modified.

---

## XAUUSD SHORT share replication

| Run | Detector | XAUUSD SHORT raw share |
|---|---|---:|
| F3 | v2 | 22.8% |
| A2 | v2 | 30.8% |
| **LIRA** | **v2** | **20.0%** |

LIRA's SHORT share (20%) is below A2's (30.8%) by 10.8pp, despite
identical detector + slices. The LIRA prompt produced FEWER XAUUSD SHORTs
than V3, even on the same MSO snapshots.

This is a SECOND independent finding against LIRA: not only does LIRA's
LONG discrimination loosen too far, its SHORT discrimination tightens
unexpectedly. Both moves are in the wrong direction relative to V3.

---

## Cost actual vs budget

| Allocation | Amount |
|---|---:|
| Budget (hard cap) | $80.00 |
| Expected ($6/slice * 12) | $72.00 |
| **Actual** | **$32.70** |
| Headroom remaining | $47.30 |

3 of 4 USDJPY slices hit the per-slice $6 budget (s1: $6.02, s3: $6.00,
s4: $6.01) — final results are partial coverage:
- usdjpy_s1: 436 of 544 candles (80%)
- usdjpy_s3: 469 of 544 candles (86%)
- usdjpy_s4: 406 of 608 candles (67%)

This means LIRA's effective USDJPY coverage is ~78% of A2/F3's. **A2 also
had usdjpy_s2 at $6.04 (full coverage)** — LIRA's coverage gap is real but
modest, and the fleet-level Exp R signal is still very clear at -0.24R below
A2 at the observed coverage. Even adding the lost USDJPY tails would have to
produce extreme positive R to flip the verdict (~+15R required across the
missing 30% of candles, vs LIRA's overall USDJPY rate of ~+0.03R/trade).

---

## Pre-registered criteria check (final)

| Criterion | Threshold | Observed | Status |
|---|---:|---:|---|
| LIRA fleet Exp R | >= +0.400R | +0.094R | **FAIL** |
| LIRA parse rate | <= 5.0% | 0.0% | PASS |
| LIRA XAUUSD SHORT WR | >= 40% if n>=3 | 100% (n=2) | PASS (auto, n<3) |
| LIRA fleet MaxDD | <= 8R | 9.00R | **FAIL** |

STAY trigger:
- `lira_fleet_exp_le_a2_baseline` (+0.333R): TRIGGERED — Exp R +0.094 ≤ +0.333

Result: **LIRA-STAY** (Exp R below A2 baseline AND below GO threshold).

---

## Recommendation

**Ship V3 as production prompt for Monday 2026-04-27 FTMO paid challenge.**
**Shelve LIRA architecture.**

Specific actions:
1. **Do NOT cutover** to LIRA. V3 stays in `src/prompts/primary_analyzer_prompt.py`.
2. **Save the schema_adapter fix** (commit 4892008) — it was a useful infrastructure
   addition that should land regardless of LIRA's fate. Future research prompts
   that emit double-block JSON will benefit.
3. **Update CLAUDE.md unresolved item #13** ("LIRA V5 priority post-Monday") to
   resolved-shelved with this synthesis as evidence.
4. **Document the pattern** — DP4 mini-backtest showed +0.486R LIRA win at n=17;
   12-slice replication showed LIRA -0.24R loss at n=48. **Lesson: 3-slice
   sims are insufficient for prompt-architecture decisions.** Future prompt
   variant decisions should require ≥10 slices / ≥30 fills before any cutover
   recommendation.
5. **Do NOT pursue further LIRA tuning.** The architectural change (label-first
   reasoning-after) has a clean axis tested and it underperformed. Effort is
   better spent on: (a) v2_shadow → v2 detector promotion gate evidence,
   (b) research items 5-12 in CLAUDE.md unresolved, (c) post-Monday FTMO
   challenge readiness.

---

## Files

- `PREREGISTRATION.md` — frozen criteria + pre-launch SHA256 hash
- `launch_slices.sh` — 12-slice parallel launcher
- `launch.log` — slice PIDs + completion timestamps
- `run_lira_slice.py` — single-slice runner
- `analyze.py` — verdict producer (LF-normalized hash, matches pre-reg)
- `analysis_output.json` — machine-readable analysis output
- `ANALYSIS.md` — full 3-way comparison
- `sl_geometry_diagnostic.py` — SL placement diff vs V3
- `SL_GEOMETRY_DIAGNOSTIC.md` — SL diff report
- `SYNTHESIS.md` — this file
- `slices/{slice}/all_results.json` — per-slice raw output
- `slices/{slice}/run.log` — per-slice execution log

## Git log

```
$(git log --oneline -10 research/lira-ab-backtest-p3)
```

(Filled by post-commit; this file is committed AFTER analyze.py runs to
capture the verdict in source control.)
