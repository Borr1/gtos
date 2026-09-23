# Cold Review — SL Buffer Gate Study (Path 1 + Path 2)

**Reviewer:** Claude Code (independent cold-review session)
**Date:** 2026-04-18
**Deliverable:** Verdict + per-task verification + deploy recommendation for Impl-A (sl_too_tight exception).

---

## Executive Summary

**Verdict: REWORK before any CEO decision.**

Both studies each got important things right, but **both made the same category error**: they labelled "Current-live" as `buffer ≥ 0.3 × ATR` and characterised the Impl-A / Option C change as a tweak of the same gate. The actual HEAD-committed live gate is `buffer ≥ 0.5 × ATR` (raised from 0.3 on 2026-04-17 in commit `1a22d92` as direct Apr-16-loss mitigation), while Impl-A **inverts the sign** to `buffer ≤ 0.5 × ATR`. That is a semantic inversion, not a calibration tweak. This is exactly what ADR 004 (`.context/06_decisions/004_sl_gate_reconciliation_2026-04-18.md`) already flagged — neither study cross-referenced that ADR or git HEAD.

Separately, Agent A's Path-2 buffer-distribution headline (`live median 0.40 ATR vs batch median 3.02 ATR, 46% live tight`) is built on a **look-ahead bias in the live side**: 7 of 13 deduped live trade records stored in `knowledge_base/trade_records/*/*.json` were re-saved later the same day with H1 order_blocks that formed AFTER the trade candle. The MSO snapshot used for the "stored OB" path is therefore not the MSO the system actually saw at decision time. Removing the 7 contaminated rows leaves n=6 — far too few to carry the headline.

The positive findings are:

- Agent B's walk-forward replay matches the existing `gate_results.csv` at 718/720 rows with max R-diff = 0 (**verified independently**). The 70R outlier is a real R-ratio artifact and Agent B correctly disclosed it.
- Agent A's Option E definition matches the CEO spec `0.3 ≤ buffer/M15_ATR ≤ 0.5` (**verified independently**, `path2_analysis.py:511-512`).
- The Apr-16 XAUUSD -1R trade at buffer 0.117 ATR is correctly rejected by Current-live-0.5 and by Option E, admitted by Options C and D. This is a confirmed regression hazard for Impl-A.

**Is Impl-A safe to deploy?** **No** — not without the CEO explicitly understanding this is a semantic inversion of the Apr-16 sweep protection, not a refinement of it. Recommend Option C from ADR 004 (additive bypass with liquidity-cluster shadow gate as mitigation) over plain Impl-A.

---

## Task 1 — Re-read both reports

- `research/sl_gate_buffer_analysis_v2/path1_report.md` (Agent B, policy-sensitivity / mechanical replay path).
- `research/sl_gate_buffer_analysis_v2/path2_report.md` (Agent A, buffer-distribution / live-vs-batch path).

Both read in full. Proceeding to task-by-task verification.

---

## Task 2 — Challenge the headline finding

**Claim under test:** Agent A, Path-2 report — live AI places SLs with median buffer 0.40 ATR while batch AI places SLs with median buffer 3.02 ATR, and 46% of live are "tight" (< 0.3 ATR).

### 2a. Live side — look-ahead contamination

Agent A's live-loading path is `path2_analysis.py:290-346`. It reads `knowledge_base/trade_records/<symbol>/*.json`, pulls `mso.timeframes.H1.order_blocks`, and picks an OB by range-containment on `entry_price`. This is correct in principle IF the stored MSO reflects what the system saw at the trade candle. It doesn't.

Spot-check of trade_record mtimes vs `candle_time`:

```
knowledge_base/trade_records/GBPUSD/2026-04-17_ny_1415.json
  candle_time     = 2026-04-17T14:15:05 UTC
  file mtime      = 2026-04-17 22:15 (local, 8h later)
  Stored H1 OBs   include formation_time=2026-04-17T17:00 and
                  formation_time=2026-04-17T21:00
  OB picked in live_deduped.csv row 5:
    ob_low=1.35198, ob_high=1.35366 — the 2026-04-17T21:00 OB
  Delta = +6 h 45 min AFTER the trade candle.
```

Systematic check across all 13 deduped live entries (entry_price matched against each stored OB's `[low, high]` range; formation_time compared to candle_time):

| trade_id | candle_time | chosen OB formation | delta (h) | look-ahead? |
|---|---|---|---|---|
| GBPJPY_2026-04-14_ny_1530 | 15:30 | 2026-04-13T16:00 | −23.5 | No |
| GBPJPY_2026-04-15_tokyo_0030 | 00:30 | 2026-04-13T16:00 | −32.5 | No |
| GBPUSD_2026-04-14_london_0730 | 07:30 | 2026-04-14T02:00 | −5.5 | No |
| **GBPUSD_2026-04-17_ny_1415** | 14:15 | 2026-04-17T21:00 | **+6.7** | **Yes** |
| **US30_cash_2026-04-14_london_0816** | 08:16 | 2026-04-14T16:00 | **+7.7** | **Yes** |
| **US30_cash_2026-04-16_ny_1345** | 13:45 | 2026-04-16T20:00 | **+6.2** | **Yes** |
| **USDJPY_2026-04-15_ny_1315** | 13:15 | 2026-04-15T19:00 | **+5.7** | **Yes** |
| **USDJPY_2026-04-15_tokyo_0245** | 02:45 | 2026-04-15T10:00 | **+7.2** | **Yes** |
| **USDJPY_2026-04-16_ny_1500** | 15:00 | 2026-04-16T22:00 | **+7.0** | **Yes** |
| XAUUSD_2026-04-15_ny_1415 | 14:15 | 2026-04-14T23:00 | −15.3 | No |
| XAUUSD_2026-04-16_london_0930 | 09:30 | 2026-04-16T07:00 | −2.5 | No |
| XAUUSD_2026-04-16_ny_1316 | 13:16 | 2026-04-16T07:00 | −6.3 | No |
| **XAUUSD_2026-04-17_ny_1330** | 13:30 | 2026-04-17T21:00 | **+7.5** | **Yes** |

**7 of 13 (53.8%) live rows have look-ahead.** Across ALL trade_records (not just the deduped 13), 53 of the files contain OBs formed after the trade candle — the re-save pattern is systemic, likely because the per-candle orchestrator writes the MSO snapshot at each new candle close without preserving the original.

**Corrected live stats** (n=6 clean sample, 7 rows removed):

```
buffer_atr (clean): [0.052, 0.114, 0.117, 0.713, 0.927, 1.466]
median = 0.415, mean = 0.565
Tight (<0.3 ATR): 3/6 = 50.0%   [95% Clopper-Pearson CI: 11.8%, 88.2%]
```

The direction of Agent A's finding (live does place tighter SLs than batch) may be real, but at n=6 the CI spans essentially the full plausible range. The **46% headline** specifically is not supportable from this sample.

### 2b. Batch side — reconstruction methodology

`path2_analysis.py:95-145` runs Component 2's `identify_order_blocks()` on 200 H1 candles preceding the batch trade, then picks the "most recent formation" OB in-zone. The tolerance on FX is `tol = 0.02` which on GBPUSD price scale is ~200 pips — wide enough to match OBs well outside the decision zone.

Spot-check: `bt_2024-04-01_london_001` entry at 2261.19 on XAUUSD — no OB exists within 1000 preceding H1 candles at that level. Nearest is 2218-2222 (~$40 below entry). The batch simulator that produced the original trade evidently used a different OB definition; the reconstruction picks the nearest-by-midpoint, which for many batch trades is a distant OB. This inflates the batch "ob_edge_to_entry" distance, which in turn inflates `buffer_atr` — because `buffer = stop_loss − ob_edge` when the chosen `ob_edge` is far from the real one, the buffer reports large.

The 3.02-ATR batch median is therefore more likely an **artifact of OB re-detection not reproducing the simulator's original OB choices** than evidence that the batch AI placed loose SLs. The batch record format contains no stored MSO, so the only way to produce a trustworthy batch buffer distribution is to re-run the batch simulator end-to-end and persist its MSO — not reconstruct post-hoc.

**Verdict on Task 2:** Headline is not robust. Directional claim (live tighter than batch) may be true, but magnitudes are a compound of a live look-ahead bias and a batch methodology artifact. I do not recommend carrying the 0.40-vs-3.02 numbers or the 46% figure into the CEO decision.

---

## Task 3 — Option E definition

**Claim:** Option E = `0.3 ≤ buffer/M15_ATR ≤ 0.5`.

**Verified.** `path1_gate_analysis.py` — Option E evaluated in `path1_gate_cells.csv` (row 6 @ policy 0.2): admitted 672, sweep_events 1, consistent with a "band" gate that keeps the mid-range and excludes both the very-tight (sweep-prone) and the very-loose (discretionary). Agent A's `path2_analysis.py:511-512` shows the equivalent mask:

```python
# path2_analysis.py:511-512
option_e_mask = (df["buffer_atr"] >= 0.3) & (df["buffer_atr"] <= 0.5)
```

Matches the CEO spec.

---

## Task 4 — Outlier sweep

`research/sl_gate_buffer_analysis_v2/multi_sl_outcomes.csv` has 4356 rows. Extreme values verified directly:

- Max `abs(r_multiple)` = 70.0 at `policy_multiplier = 0.2`. Corresponds to a case where the replay SL was set at `entry_price × 0.2 × original_sl_distance` — i.e. a vanishingly tight SL combined with a normal target, yielding a mechanically inflated R. Agent B explicitly flags this as an **R-ratio artifact** in `path1_report.md` and mitigates by reporting expectancy `excl_unresolved` and by showing the `price_distance_expectancy` alongside. This is adequate disclosure.
- At policy_multiplier ≥ 0.3, max |R| drops to ≤ 28 and at ≥ 0.5 to ≤ 8. The contamination is confined to the aggressive-SL sweep, which is appropriate — it is a sensitivity test, not a strategy proposal.

Also verified: at policy 0.2 with Option C, the `sweep_events` column jumps to 14 (vs 1 for baseline and current_live at the same policy) — meaning that aggressively tight SLs under an upper-bound-only gate generate noticeably more sweep events. This is worth carrying forward to the CEO decision alongside the Apr-16 empirical sweep.

**No further contamination candidates** beyond the 0.2-policy R-inflation, which is properly disclosed.

---

## Task 5 — Agent B's 99.72% walk-forward match

**Claim:** `validation_vs_existing.csv` shows 718 of 720 matching R-outcomes between the replay script and the existing `gate_results.csv`, with max R-diff = 0.

**Verified.** Independently recomputed from `validation_vs_existing.csv` (721 lines incl. header → 720 rows). Rows where `outcome_match = True`: 718. Rows where `outcome_match = False`: 2. `max(abs(r_diff))` = 0. The two mismatches are degenerate (entry equals ob_edge, so the replay script and the legacy produce marginally different admission booleans). Agent B explicitly notes and accepts this.

This is a clean, self-contained mechanical validation. **Accept.**

---

## Task 6 — Sample-size sanity check on n=13 claims

Clopper-Pearson 95% CIs for the Path-2 headline figures at the live sample size:

| Claim | k/n | 95% CI |
|---|---|---|
| Tight rate (< 0.3 ATR), as reported | 6/13 | [19.2%, 74.9%] |
| Tight rate after look-ahead correction | 3/6 | [11.8%, 88.2%] |
| Deep-tight rate (< 0.3 ATR), whole live set | 3/13 | [5.0%, 53.8%] |

The "46%" point estimate has a CI that includes both 20% and 75% — the claim that live is "dominantly tight" cannot be distinguished from "occasionally tight" at this sample size. Agent A's report does not present Clopper-Pearson intervals and consequently overstates the confidence of the live-vs-batch contrast.

---

## Task 7 — Cross-check Agents A and B

Intersections of claims between the two reports:

1. **"Current-live" definition.** Path-1 encodes Current-live as `buffer ≥ 0.3 × ATR` (`path1_gate_analysis.py` — policy tables built under that assumption). Path-2 does the same textually. **Both wrong vs HEAD:** see git below.
2. **Number of live trades considered.** Path-1 uses the 720-row `multi_sl_outcomes.csv` derived from 14-row `live_deduped.csv` deduplicated to retest events. Path-2 uses the same 14-row input (dropping header → 13 trades). Sample sizes reconcile.
3. **Option E outcome.** Path-1 reports Option E at policy 1.0: admitted 700, expectancy 0.0198 R. Path-2 reports Option E rejects 46% of live + keeps all Apr-16-style sweep protection. The two views are consistent: both show Option E slightly tighter than Current-live with similar R-outcomes.
4. **Option C outcome.** Path-1 shows Option C @ policy 0.2 with sweep_events = 14 (the 14-sweep regime is new under the upper-bound-only rule). Path-2 shows Option C admits the Apr-16 trade that Current-live rejects. Both views converge on "Option C regresses sweep protection."
5. **Impl-A description.** Neither report explicitly names ADR 004 (`.context/06_decisions/004_sl_gate_reconciliation_2026-04-18.md`), which documents the exact inversion and is dated the same day as the studies. This is a significant omission.

---

## Task 8 — Is Impl-A safe to deploy?

### 8a. HEAD production gate (verified this session)

```
git show HEAD:src/components/permissions.py — _ob_retest_sl_exception_applies
  line 208: min_buffer_mult = gate1_cfg.get("ob_retest_sl_min_buffer_atr", 0.3)
  line 209: min_buffer = m15_atr * min_buffer_mult if m15_atr > 0 else 0
  line 221: if min_buffer > 0 and buffer < min_buffer:
            → REJECT exception if buffer < min_buffer
            → PASS exception if buffer ≥ min_buffer

git show HEAD:config/agent_config.yaml
  line 50: ob_retest_sl_min_buffer_atr: 0.5

Effective HEAD rule: exception fires when buffer ≥ 0.5 × M15_ATR
                    (no upper bound — any wider is fine)

git show 1a22d92 -- config/agent_config.yaml
  -  ob_retest_sl_min_buffer_atr: 0.3
  +  ob_retest_sl_min_buffer_atr: 0.5
  Commit message: "touch-count OB gate + pending intent persistence +
                   SL margin raise + 2R log fix"
  Date: 2026-04-17, explicitly in response to Apr-16 XAUUSD sweep loss.
```

### 8b. Impl-A uncommitted change (working-tree diff)

```
git diff HEAD -- src/components/permissions.py
  Replaces the ≥ check with a ≤ check:
  - if min_buffer > 0 and buffer < min_buffer: return False
  + max_buffer = m15_atr * 0.5
  + if not (0 <= buffer <= max_buffer + eps): return False
```

This flips the inequality direction. The HEAD rule says "SL must sit far enough from the OB to clear sweeps." Impl-A says "SL must sit close enough to the OB to be structural." They are not compatible — there is no overlap except at the exact point `buffer = 0.5 × ATR`.

### 8c. Apr-16 XAUUSD -1R regression test

From `research/sl_gate_buffer_analysis_v2/live_deduped.csv` row 12 (`XAUUSD_2026-04-16_ny_1316`): buffer = 6.73, buffer_atr = 0.117. Current HEAD gate (min 0.5) **rejects the exception** (0.117 < 0.5). Under Impl-A (max 0.5) the gate **accepts** (0.117 ≤ 0.5), and the confirmed -1R loss is admitted.

This is the failure mode the HEAD gate was specifically added to prevent — the Apr-16 handoff 18 describes the sequence.

### 8d. Deploy recommendation

- **Do not deploy Impl-A as-is.** It is a semantic inversion of the Apr-16 fix. Both studies describe it as a refinement of the gate — neither flags the sign flip.
- **Preferred path:** ADR 004 Option C (additive bypass). Structural placement (`buffer ≤ 0.5 ATR` + `sl_beyond_edge` + `framework=ob_retest`) triggers a **separate code path** that bypasses both the 1.5×ATR floor and the Apr-16 sweep margin, with the known tradeoff that the sweep protection is relaxed for structurally-tight SLs. Mitigation: the already-shadow-logging liquidity cluster gate (handoff 20).
- **Do not** commit the Impl-A diff until ADR 004 has been resolved by the CEO. The diff on the working tree today would remove the Apr-16 fix silently.

---

## Blocking Issues

1. **B1 — Semantic mislabel of "Current-live"** (both studies). HEAD config is `ob_retest_sl_min_buffer_atr: 0.5` and HEAD code checks `buffer >= min_buffer`. Both reports assume 0.3 and assume Impl-A is a refinement of the same sign. Impl-A is in fact the opposite inequality. Any CEO decision built on the current reports will be built on a false equivalence. Must be rewritten before CEO reads.

2. **B2 — Live look-ahead bias** (Path-2 / Agent A). 7 of 13 deduped live trade_records contain H1 OBs formed hours after the decision candle. The MSO snapshot stored by the orchestrator is re-saved at subsequent candle closes, so the "stored MSO" path in `path2_analysis.py:290-346` does not reproduce decision-time state. Headline numbers (median 0.40 ATR, 46% tight) are not trustworthy from this source. Correcting drops the clean sample to n=6.

3. **B3 — Batch reconstruction artifact** (Path-2 / Agent A). Batch records have no stored MSO; Agent A re-runs Component 2 with a wide tolerance (`tol=0.02` on FX = ~200 pips) and picks nearest-by-midpoint when in-zone is empty. Spot-check confirms the reconstruction picks OBs at $40 distances from the entry for XAUUSD batch rows. The "batch median 3.02 ATR" is likely an OB-identification mismatch, not an AI behaviour difference.

---

## Non-Blocking Concerns

1. **N1 — Neither study cites ADR 004.** `.context/06_decisions/004_sl_gate_reconciliation_2026-04-18.md` was written the same day and directly addresses the gate conflict. Neither report references it, suggesting the agents did not consult the decisions directory. Future studies on CEO-blocking decisions should mandate an ADR-check as a task-0 step.

2. **N2 — 70R outlier handling is adequate but borderline.** Agent B (Path-1) discloses the R-ratio artifact at policy 0.2. It would be cleaner to show a weighted or trimmed expectancy, but the current disclosure (report expectancy_ex_unresolved + price_distance_expectancy alongside) is defensible.

3. **N3 — Clopper-Pearson intervals missing.** Agent A's 46%, 92%, and comparable proportion claims would be dramatically weakened by explicit CI columns. Add `[lo, hi]` next to every proportion at n<30.

4. **N4 — Option C sweep regime.** Path-1 shows sweep_events jumps from 1 to 14 at policy 0.2 under Option C. This matches the theoretical concern that an upper-bound-only gate admits more sweep-vulnerable entries. Worth carrying explicitly into the ADR-004 resolution as quantitative backup.

5. **N5 — Unicode.** `path2_report.md` and `path1_report.md` both use curly quotes and em-dashes that may not render in the Windows cp1252 log viewer. Not a correctness issue.

---

## Recommendation

**Reject Impl-A as submitted.** Rework the study in three steps before a CEO decision:

1. Rewrite "Current-live" definitions in both reports to match HEAD (`buffer ≥ 0.5 × ATR`, raised from 0.3 on 2026-04-17). Re-label Impl-A as a sign inversion, not a calibration.
2. Re-run Path-2 with decision-time MSO (either from production logs if available, or by re-running the live loader at decision-candle time using only candles ≤ candle_time). If unavailable, the live headline should be withdrawn and the Path-1 mechanical replay carried forward alone.
3. Cite ADR 004 and propose Option A / C / D explicitly with numbers attached. Option C (additive bypass) is the strongest candidate because it unlocks the ~4-5 blocked trades/week while preserving the Apr-16 sweep protection for non-structural SLs, with the separate liquidity-cluster shadow gate as a second layer of defence.

Agent B's Path-1 (policy sensitivity, 720-row walk-forward match) is independently solid — it survives this review and should be the quantitative backbone of the revised analysis.
