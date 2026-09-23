# AW digest — what the first separability mine actually found, and exactly why it is stale

Source: `docs/audits/fable5-vision-audit-20260725/phase12/SESSION_AW_SEPARABILITY_MINE_RESULT.md`
(wave 12, B1750–B1799). Substrate: the four SEALED January arms + April partial — **all on the
wrong clock** (broker wall time mislabelled UTC, +2.0 h; CD B2255, closed by CJ). Everything below
is therefore a hypothesis about a population that no longer exists as stated: the true-UTC
re-materialization changed membership (scoreable 28,544→27,658 on S0R0, −3.10 %; 711 prepared
windows changed candidate count; session/kill_zone membership moved on ~84k/23k occurrences).

## 1. What AW found (verdicts, rules, discipline)

**Discipline.** Everything declared before outcomes were read (`AW_MINE_PROTOCOL_V1.json`,
`cells_sha256`-pinned): chronological split (TRAIN = first 13 January days, HOLDOUT = last 8),
categorical level cuts at ≥200 train rows, numeric train-tertile cuts, funnel
F1 train-mean>0 → F2 holdout-mean>0 → F3 holdout day-positivity ≥0.50 → F4 April-mean>0 →
F5 positive on the other three arms; day-blocked sign-flip permutation inference; family ratchet
265 → 477 (gross re-ask of the same 212 cells) → 486 (AW-3's nine arms).

**Verdicts, in order of importance:**

1. **Separability: NO at every declared resolution.** 0 of 212 cells pass F1 (train mean net > 0).
   Best cell `final_blocker_class==execution_fillability` at −0.1440 R/row vs pool −1.0135 —
   an +0.87 lift that is 86 % of the way to zero and still short. Its precision 0.591 vs the
   0.655 required. Model ceiling: HGB AUC 0.712 holdout / 0.669 April with **negative** top
   deciles; the fit-on-the-answers control reaches only 0.651 precision vs 0.655 breakeven.
2. **The axes are informative and it does not matter.** Train→holdout Spearman over cell means
   0.919 (April 0.903). "Real but insufficient" — prescription differs from "absent".
3. **Not a cost problem.** Gross mean −0.2199 before any cost; pure 2R/1R binary population
   16.9 % vs 33.3 % breakeven; 2/212 gross-positive TRAIN cells, neither survives; the
   cost-executable third of the pool is still gross-negative (−0.163).
4. **F38 confirmed and priced**: `commission_r` identically 0.0 on all 28,519 rows; broker truth
   prices all 24 symbols at mean 0.0654 R/row. With F31 + commission: pool −24,483.87 →
   −27,016.30 R, breakeven precision 63.92 % → 65.52 %.
5. **Degenerate-axis findings**: `candidate_confidence` = 0.55 on every row with
   `confidence_default_applied` = True on every row — the selection campaign carried **zero
   confidence information**; 22 axes declared `look_taken=false`.
6. **The transferable find is a generator defect**: cost > 1 R on 16.5 % of rows carrying
   49.6 % of the loss (max 18.856 R) — stop narrower than round-trip spread. (CD correction:
   the 16.5 % was masked on `cost_r` while the inline note said `spread_r`.)
7. **AW-3 (estate, out-of-window, controlled)**: the sealed `spread_r ≤ 0.10` limit is a
   **per-sleeve repair, not an estate rule** (median Δ 0.0000; 10/23 vs random 11/26);
   `asia_pdl_fade` +0.998 with clean inverse/random controls; 0 ADMIT anywhere;
   `sub_xvol_pullback` raw p 0.0020 misses every defensible bill.

## 2. Exactly why it is stale

- **Clock, by construction.** Every `B_TIME` cell (hour, session, kill-zone, day membership) was
  computed on labels +2 h ahead of true UTC. CJ finding 5: old labels 00/01 are prior-day
  true-UTC 22/23. AW's prose says 81 cells; the committed map has **83**.
  **Superseded by `phase18/receipts/CP_TRUE_UTC_B_TIME_MAP_V1.json`** — same 83 cell identities
  regenerated on the true-UTC pool, **all 83 optimistic TRAIN edges negative** (best:
  `session_bucket==london` −0.42798732), one verdict changes only on a denominator
  (`moonshot_h07_08` TRAIN n=193 < 200). Never cite AW's B_TIME economics.
- **Population, not just labels.** CJ proved re-clocking is not a relabel: −886 scoreable rows
  (−3.10 %), 711 changed prepared windows, trades 63→57, realized +3.435 R. Every AW cell's
  membership — including non-time axes — is drawn from a population that shifted.
- **Costs.** AW charged F38 commission and F31 gap-through post-hoc; the CJ/CP arms charge
  broker-true commission **in-engine** (Jan mean 0.06522413 — matching AW's post-hoc 0.0654 to
  four decimals — Feb 0.05024920). AW's `net_r_aw` column and the pool's recorded net are now
  different constructions; FA must not mix them.
- **The family bill.** AW's looks were billed at family 486 under the pre-ratchet accounting;
  `TRAINING_LANE_RATIFICATION.md` §1.2 later classified that as research triage over-billing.
  The lane now logs iteration unbilled and bills only at graduation (V27: 59/57).

## 3. AW findings the re-clocked pool should retest (FA shortlist)

1. **The full 212-cell separability map** (H03) — never recomputed at true UTC. Expectation
   from CD (§6 of its result: 0 of 71–76 cells positive on the regenerated arms) is
   confirmation, but that run predates the re-clock too.
2. **The degeneracy census** (H06): is `candidate_confidence` still 0.55-everywhere on the
   true-UTC arm? If yes, "wrong selection" has a structural ceiling no selector can beat.
3. **The alias-partition census** (H20): re-hash induced partitions on the new pool before
   declaring any FA look, so aliases bill once.
4. **The cost-tail geometry** (H07): already re-derived raw at true UTC (4,908 rows / 54.17 % of
   loss / max 18.7758) — the *generator stop-geometry* prescription (REPAIR_QUEUE_CD row 1)
   remains the open repair.
5. **The "information is real" persistence claim** (Spearman 0.919): worth re-measuring, because
   it is the one AW result that argues conditioning could matter if the pool's level were
   repaired — which is exactly the door CQ's inverted-breaker cell walked through.

**What FA should NOT retest from AW:** the estate-side archive gate (AW-3, §5) — different lane,
different population, and its transfer *into* the broad pool was already refuted by CD (killing
the cost tail leaves −0.49 R/row).
