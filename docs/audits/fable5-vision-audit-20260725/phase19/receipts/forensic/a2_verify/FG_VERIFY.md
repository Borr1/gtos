# Lane FG verification — Sol repair integration fidelity (Phase A2)

**Verifier:** Fable verification agent, Session FA-continuation Phase A2 (2026-08-03).
**Subject:** `/Users/borr/GTOSActive/worktrees/wave19-sol-integration-20260801`, branch
`phase19/sol-integration`, head `ba3c18ddf268294813545501f84b635ccc0f25bb` (verified; worktree clean).

**Boundary statement.** All February reads in this verification (CP Feb pool, Feb lane trade
table, Feb trade ledger) were **attribution-only under `owner_mandate_20260801`**. No March 2026
outcome data was read (nothing under any `packs/` for March was touched). No live-forward
(2026-07-29+) outcomes were read. No test suites, lane arms, or replays were run. No source file
was edited. Every `.jsonl` / `.jsonl.gz` was streamed line-by-line with O(1) aggregates; the
3.2M-row ordered-path sidecar was never opened.

**Method rule honored:** recomputation is from RAW inputs (pools, trade ledgers, lane trade
tables) wherever a raw path exists; Sol/FG receipts were treated as claims, and where a claim is
only receipt-checkable (FB grid cells, FC overlay cells, CS gate) the named receipt's own
embedded raw series were re-aggregated where possible.

---

## Verdict summary

| claim | verdict |
|---|---|
| FG1 — 66/66 commits, content fidelity | **VERIFIED** |
| FG2 — A/B receipts exist + internally consistent | **VERIFIED** |
| FG3 — repair register: implementations exist, default-off | **VERIFIED** (10 entries, not 8 — see finding 2) |
| FG4 — 10 sampled quantitative statements | **10/10 VERIFIED** (two nuances noted) |

No claim was refuted. Six findings (nuances/caveats) are listed at the end — none changes a
direction or a decision.

---

## FG1 — content fidelity of the 66-commit integration

**Commit accounting (recomputed from git, not from FG's ledger).** Source tips match the
commission exactly: sol-grid `6ef09b8f4` (9 commits from merge-base `f8c05d0ac`), sol-exit
`210307687` (15), sol-defects `a7d9260ed` (8), sol-conditions `674b81f61` (8), sol-composition
`9c95c28b7` (6), CR `47139bc35` (1 from `55de4a312`), CS `7f9ab73c2` (19). Total **66**. The
integration branch carries **67** commits from `f8c05d0ac`: 66 cherry-picks + FG's own closing
commit `ba3c18ddf`. All 66 matched 1:1 by subject with zero unmatched on either side.

**Patch-level.** 58/66 pairs are byte-equivalent as patches (`git patch-id --stable`). The 8
divergent pairs (CR 4b54c9550, CS 01b7975a6, FB a3f15587b, FC 33181552a, FD a23505600, FE
23ddb448b + b946b0969, FF 41ebaf260) were compared **per file**: every difference is confined to
the three multi-owner conflict files — `IMPLEMENTATION_STATE.md` (owned by CR, CS, FB, FC, FE),
`src/research_infra/train_engine/cuts.py` (CR, FD, FE, FF), and
`tests/test_implementation_state_block_citations.py` (CR, CS). **No pair dropped or added a
file.**

**Tree-level.** `git diff <tip> ba3c18ddf -- <owned paths>` per branch: **zero divergence on
every exclusively-owned path for all seven branches.** Divergence exists only on the 6 shared
paths, which is what composition requires. (An earlier all-empty diff was a zsh word-splitting
artifact and was discarded; the corrected run is in `fg1_raw_output.json`.)

**Composition on shared paths.** Every branch's added non-blank lines are present verbatim in the
final tree for all six shared paths, with one exception verified by direct read: 5 of CR's
`cuts.py` lines exist in **refactored** form — `row.get(...)` became `normalized.get(...)`
(rewrapped) because FD's `decision_semantics.normalize_evidence_row` repair now feeds CR's
opportunity-close projection. Same three-way branch (profit_harvest → selected_execution_policy →
counterfactual_order_path), same output fields. Composition, not loss.

**Whole-tree accounting.** 157 changed paths at `ba3c18ddf` = 141 branch-owned + 18
closing-commit paths (2 overlapping); **0 unexplained paths, 0 owned paths missing.**

**FG's own ledger cross-checked.** `FG_SOURCE_COMMIT_LEDGER.json`: 66 mappings, `unknown_count`
0; all 66 validated — each `source_commit` is on its named lane branch, each
`integration_commit` on the integration branch.

**Verdict: VERIFIED.**

## FG2 — the A/B claims

All receipts exist and cross-agree:

- **Before** (embedded `gtos-ab-receipt-v1` block in `session_fg_ab/SESSION_FG_AB_RECEIPT.md`)
  equals the committed suite-wide baseline `receipts/FAILSET_BASELINE_MAIN.json` value-for-value:
  commit `bca8c4466` (subject verified; it is an ancestor of the integration base), captured
  2026-07-31T23:43:36Z, dirty, totals 1 failed / 12,705 passed / 120 skipped / 32 xfailed, and
  the single failed nodeid is the registered mapping-order test.
- **After**: `AFTER.json` at `fcc9782e3` (subject verified, = integration HEAD~1), captured
  2026-08-01T05:23:52Z, dirty (declared), totals **736 passed / 1 skipped**, `failed=[]`,
  `errored=[]`, pytest rc 0, parse-complete, and `pytest_args` carries **exactly 42** test-file
  paths (the embedded block's scope-after list also counts 42).
- **1 bad → 0 bad, 1 fixed, 0 regressed**: bad_before nodeids = the baseline's single failure;
  bad_after empty; the fixed node exists at the after commit; the receipt explicitly does *not*
  attribute the pass to FG (registered intermittent carrier).
- **301/0 changed-test sweep**: `SESSION_FG_COMPLETE.json`
  `verification.combined_changed_behavior_preclose = {passed: 301, failed: 0, errored: 0}` and
  `FG_INTEGRATED_VERIFICATION.json` `metrics.combined_changed_tests_preclose_passed = 301`,
  `checks_failed = 0`.

Suites were **not** re-run, per commission. Caveats: both captures are declared dirty; the
301-node sweep is receipted as totals only.

**Verdict: VERIFIED (as receipts-exist-and-internally-consistent).**

## FG3 — FG_REPAIR_REGISTER.json

The file carries **10 entries**: ranks 1–8 are the repair dispositions (the claimed "8 rows");
ranks 9–10 are rejected hypotheses, both `NOT_IMPLEMENTED` as stated. Every named implementation
exists at `ba3c18ddf` and its default-off state is real in code:

| rank | named implementation | verified state |
|---|---|---|
| 1 FD | `train_engine/decision_semantics.py`, `repairs.py`, `cuts.py` | present; evidence/training lane |
| 2 CR | `walkforward/fidelity.py` | present; `CR_GENERATOR_FIDELITY_V1.json`: 249/249 agreed, recall 1.0, reference_only 0; caveat marks non-live basis |
| 3 FF | `hard_eligibility_observability` patch (`cuts.py:866`) | ABSENT from default+safe sets; reachable only via `safe+hard-eligibility-observability` |
| 4 FE | `condition_feature_propagation` patch + `sol_conditions.py` | ABSENT from default+safe; only in `safe+conditions`; `CONDITION_FEATURE_KEYS` = exactly 15 fields |
| 5 FB | `current_ob_retest_geometry_candidate.py` | `DEFAULT_ENABLED = False`; "intentionally unreachable from runtime"; imported only by its own test |
| 6 CS/CQ | `src/components/current_breaker_re_entry_repair.py` | `enabled=False` default; `phase18_current_breaker_re_entry_repair_enabled` has zero hits under `config/` (absent-false); gate `NOT_QUEUED`, `arming_authority` false |
| 7 FC | `exit_overlay.py` | "Pure, default-off" primitives; imported only by tests; FC2 protocol-only, 24-cell cap |
| 8 | global calibration repair | `NOT_IMPLEMENTED` — consistent absence |

**Verdict: VERIFIED** (with the 10-vs-8 precision note).

## FG4 — ten sampled quantitative statements from the ghost-written FA result

Six statements recomputed **from raw** (pools, trade ledgers, lane tables); four checked against
their named receipts, re-aggregating the receipts' own embedded raw series where present.

| # | statement (abbrev.) | recomputed | verdict |
|---|---|---|---|
| S1 | Jan pool: 27,658 rows, net −24,357.198914R, −0.880657R/row, gross −6,015.503029R, cost 18,341.695885R | RAW pool stream: all five figures **exact at 1e-6** (net = Σ`opportunity_net_proxy_r`, cost = Σ`cost_r`, gross = net+cost) | VERIFIED |
| S2 | Feb pool: 24,239 rows at −15,513.472827R net (−0.640021R/row) | RAW pool stream (attribution-only): **exact** | VERIFIED |
| S3 | prob means 0.765762 / 0.763777; realized positive rates 0.278617 / 0.309336 (7,706 / 7,498 rows) | RAW pool streams: **exact** | VERIFIED |
| S4 | chosen percentile 0.669969 / 0.684373; chosen net −0.100113R (n=55) / −0.068300R (n=58); set means −0.722471 / −0.665061 | chosen nets recomputed **exact from raw lane tables** (Jan 2 null net_r as registered); percentiles/set means match `scorecard/RANK_OUTCOME.json` at rounding; two independent paths agree on chosen net | VERIFIED |
| S5 | executed FVG −12.263583R (21 Jan trades) / −5.783454R (42 Feb); non-FVG +6.757375R / +1.822056R | RAW trade ledgers: sums **exact**; cross-anchor FVG+nonFVG = lane totals −5.506208 / −3.961399 | VERIFIED (nuance: Jan sum spans the 20 scored of 21 FVG trades; 1 has null net_r) |
| S6 | cost authority refused 20,448 Jan rows @ −1.12107R; 19,919 Feb @ −0.74728R | RAW pools, `final_blocker_class == cost_authority`: 20,448 @ −1.121065; 19,919 @ −0.747282 — match at stated rounding | VERIFIED |
| S7 | breaker inverted 5D/0.25D: +11.877105 / +11.928115 / +11.901108 over 4,263 | `GRID_FULL_RESULTS.json` cells[189] `family:current_breaker_re_entry`: 11.877104778 / 11.928115222 / 11.901108285, n 4,263 | VERIFIED |
| S8 | OB-retest 1.5D/0.25D: +1.630823 / +1.670197 / +1.646719 over 1,340 | same receipt cells[45] `family:current_ob_retest`: matches at rounding, n 1,340 | VERIFIED |
| S9 | V17: +0.197 TRAIN / −1.920 HOLDOUT / −0.381 Feb; q 0.4861; 0/40 persistent | V17 daily series re-summed: +0.197122 / −1.919983 / −0.380614; `q_bh_40` 0.4861111; 40 cells; Feb-positive set empty; V17 sole TRAIN-positive | VERIFIED |
| S10 | breaker folds +11.252342 / +7.453554 / +3.852045; REJECT p 0.002600, q 0.153385, 59 members; not queued, no arming | CS gate receipt: fold `test_mean_r` exact (n_test 1664/768/487); p 0.0025997; q 0.1533847; family 59; `NOT_QUEUED`; `arming_authority` false | VERIFIED (fold-population caveat below) |

## Findings (none refutes a claim)

1. **FVG count nuance (S5):** "−12.263583R on 21 January trades" sums the 20 scoreable of the 21
   executed FVG trades; 1 FVG trade carries null `net_r` (the lane's 2 registered null-net trades
   split 1 FVG / 1 non-FVG).
2. **Register length:** `FG_REPAIR_REGISTER.json` has 10 entries, not 8 — ranks 9–10 are
   rejected hypotheses (`NOT_IMPLEMENTED`). Substance consistent; the file is longer than billed.
3. **The 8 non-identical cherry-picks** are exactly the conflict resolutions on the 3 shared
   files; CR's 5 refactored `cuts.py` lines are composition with FD's normalization, semantics
   preserved.
4. **The 301/0 sweep is totals-only** — no per-node list is receipted for it (the 42-file
   closure, by contrast, has full args and totals in `AFTER.json`).
5. **CS fold means are not naively reproducible from the raw fold pools:** a date filter over
   `CS_{APRIL,MAY}_CURRENT_BREAKER_REPAIR_TRADES_V1.jsonl.gz` gives the pool-level OOS means
   (April 12.539079 over 2,059; May 7.320861 over 1,118), while the gate's folds test 768/487
   trades after embargo/purge/binding (purge counts disclosed in the receipt). Reproducing the
   published fold means requires the gate machinery — a reproducibility caveat, not an
   inconsistency.
6. **Join hazard corroborated from raw:** bare `candidate_id` multiplicity reaches 41 (Jan pool)
   and 128 (Feb pool); executed lane trades are entirely absent from the missed-opportunity pools
   (0/57 and 0/58 identity-tuple joins) — executed-trade family attribution lives in the TRADE
   ledgers only.

## Method receipts in this directory

- `fg1_content_fidelity.py` → `fg1_raw_output.json` — branch accounting, owned paths, tree
  diffs, added-line containment, the 66-pair patch-id table.
- `fg1_mismatch_detail.py` → `fg1_mismatch_detail.json` — per-file patch comparison of the 8
  divergent pairs.
- `fg4_pool_recompute.py` → `fg4_pool_recompute_result.json` — raw Jan/Feb pool streams.
- `fg4_lane_recompute.py` → `fg4_lane_recompute_result.json` — lane trade tables + the
  identity-tuple join demonstration.
- `FG_VERIFY.json` — machine-readable version of this document.
