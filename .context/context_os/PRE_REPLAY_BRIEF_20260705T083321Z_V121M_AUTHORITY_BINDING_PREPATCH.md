# Pre-Replay Brief - V121M_AUTHORITY_BINDING_PREPATCH

Generated: 2026-07-05T08:33:21Z
Route: `final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20`

## 1. Latest Completed Replay

Prefix: `BROAD_LIVE_AS_IF_REPLAY_V121M_FINALIZER_SCORE_HANDOFF_REPAIR_20260513_20260517_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`
Window: 2026-05-13..2026-05-17 hostile five-day bucket. This is a bounded repair proof, not full global reservoir transfer proof.

Numbers: 25,006 candidates, 288 scorecards, 55 order rows, 21 filled trades, +4.39334958 net R, +5.855605791 gross R, cash PnL 0.0 in the summary ledger, W/L/F 9/12/0, cost-refused executed 0, source-gap executed 0. Missed positive: 14,552 rows / +10,260.589507650517R. Missed negative: 10,423 rows / -15,396.204096452155R.

Delta vs V121L: +20 trades and +5.48988944R. Added 21 trades and removed 1 trade.

## 2. Active Processes

No broad replay, verifier, pytest, or repair run was active when checked. The route-owned V121M comparison parsers completed. A stale git-add helper was observed and had exited before termination; no git-add process remains.

## 3. Baseline Comparisons

Against V89D same window: trades delta -35, net R delta -30.45185496, added 18 trades / +6.46580395R, removed 53 trades / +36.91765891R.

Against V90 same window: trades delta -30, net R delta -24.44866199, added 20 trades / +4.33440898R, removed 50 trades / +28.78307097R.

Against V92 same window: trades delta -30, net R delta -24.96235278, added 19 trades / +5.43064401R, removed 49 trades / +30.39299679R.

Interpretation: V121M proves the finalizer handoff repaired local transfer versus V121L and the added transfers are net positive, but it still trails V92 because it removed more positive historical transfers than it added.

## 4. Dirty Files And Active Code Changes

Active code changes currently implicated by this checkpoint:
- `src/components/selector_v4.py`
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- focused tests under `tests/`

There is substantial unrelated/pre-existing route/context dirt and deleted old JSONL ledgers. Do not stage broadly.

## 5. Subagent Findings

Boyle: incorporated into next batch. Main finding: package marketable route binding leak, with 18 order rows / 10 unique order IDs declaring immediate marketable route while actual order path was not immediate. Repair route-intent/order-path binding before broad replay.

Linnaeus: partially incorporated, one open B3 gap. B1/B2 mostly implemented. Remaining selector issue: fill-floor softening can become risk-bearing without signed package authority hash at selector decision time. Patch or demote to diagnostic until signed.

McClintock: incorporated as open scheduler binding gap. Missing exact scheduler option has 3,566 missed rows, 360 scoreable, -79.55749196R aggregate, with representative positive source-complete package-authority rows not materialized. Reclassify/repair scheduler-option/probe binding.

## 6. Mismatch Classes

Source-bound -> candidate: same-window candidates are present; no full-reservoir claim from this five-day proof.
Candidate -> scorecard: 25,006 -> 288 is preserved versus V92 and remains a per-window scorecard aggregation surface.
Scorecard -> order: V121M 55 order rows remains far below V92 239 order rows.
Selector -> scheduler: raw/effective split exists; signed softening and role disposition contracts still need final enforcement.
Scheduler -> risk: risk ladder exists; exact scheduler-option/probe binding remains open.
Risk -> order: REFUSED/source-gap rows stay non-executable; valid signed rows need consistent executable authority.
Order -> lifecycle/fill: route intent can diverge from actual path; accepted expiries need explicit honest cause.
Fill -> exit: filled losses are M1 proxy replay losses, not broker/final truth; continue monitoring after authority binding.
Ledger: control files were stale at V121L and are updated by this brief.

## 7. Fixed, Partial, Open

Fixed: V121M finalizer score handoff improved V121L from 1 trade -1.09653986R to 21 trades +4.39334958R. Role-disposition reduced-risk contract patch is in code and focused tests passed.

Partially fixed: transfer is improved but still weaker than V92/V90/V89D. Verifier is not green yet; latest route verifier output had stale/noisy issues.

Open: selector signed softening, package marketable route binding, scheduler option/probe materialization, verifier precision for these contracts.

## 8. Highest-Leverage Same-Root Batch

Patch `V121N authority-binding contract repair`: selector signed softening, package role disposition, scheduler exact-option/probe binding, marketable route intent, and order execution path must share one executable authority contract.

## 9. Affected Files

`src/components/selector_v4.py`, `src/research/moonshot_scheduler_v4_best_trade_allocator.py`, `src/research_infra/v4_timewarp_simulated_live_research_loop.py`, route harness/verifier, and focused tests listed in the root map.

## 10. Patch Types

Selector signed softening: correctness repair.
Package marketable route binding: correctness repair.
Scheduler option/probe reclassification: correctness plus diagnostic repair.
Verifier checks: proof/diagnostic repair.

## 11. Expected Effects Before Replay

Candidate -> scorecard: no intentional suppression; about 288 scorecards should remain unless unsigned softening is correctly demoted to diagnostic.
Scorecard -> order: valid signed cost-passed rows should transfer more cleanly.
Order -> fill: route-intent/order-path mismatch should drop to zero.
Missed positive/negative R: both may move if causal authority is satisfied; no positive-by-suppression.
Trade count and R: may rise or shift; success is correct transfer attribution, not just headline improvement.
Cost-refused/source-gap execution: must remain zero.
Risk distribution: reduced-risk role rows explicit; full-risk only with signed ladder conditions.

## 12. Replay Success/Failure Criteria

Helped: focused tests pass, route-intent/order-path mismatches drop to zero, unsigned fill-floor softening cannot become executable, and valid signed rows show better order transfer without REFUSED/source-gap execution.

Failed: trade count improves only by executing unsigned/cost-refused/source-gap rows, or route intent remains inconsistent with order path.

Next deeper flaw exposed: correct authority binding still leaves large positive missed R under fillability, lifecycle, or exit-specific blockers; then patch that stage before another broad loop.
