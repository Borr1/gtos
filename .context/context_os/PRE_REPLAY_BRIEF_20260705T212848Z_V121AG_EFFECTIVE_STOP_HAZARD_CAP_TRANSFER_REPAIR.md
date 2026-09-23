# Pre-Replay Brief - V121AG Effective Stop-Hazard Cap Transfer Repair

Generated: 2026-07-05T21:28:48Z

## 1. Latest Completed Replay

Latest completed prefix: `BROAD_LIVE_AS_IF_REPLAY_V121AF_STOP_HAZARD_DOMINANCE_R_RECONCILIATION_20260513_20260517`. This is a bounded 2026-05-13..2026-05-17 hostile/stress bucket, not a full-reservoir proof.

V121AF headline holdout repaired profile: 44 trades, net R 20.26032016, gross/final R 23.44256841/23.44256841, cash PnL 10420.02497129, W/L/F 26/18/0. Candidate rows 25006, scorecard rows 288, order rows 44, missed rows 24945.

Exact-window source-bound denominator: 407295.6072920759R across 1101 package axes; 886 axes generated candidates, 32 axes reached scorecard/order, 27 axes filled. Actual executable R in this window: 21.59326621. Interpretation: this smoke proves/disproves the local repair only; it does not prove total reservoir conversion.

## 2. Running Replay State

No broad replay is currently expected to be running. The route verifier completed with `ok=true`, `issue_count=0` after the stop-hazard effective-cap split repair, V121AF flow diagnostic generation, and manifest refresh.

## 3. Baseline Comparison

| Run | Trades | Net R | Gross/Final R | Cash PnL | W/L/F | Risk Decisions |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| V89D | 56 | 34.84520454 | 39.93441037/39.93441037 | 8178.90660707 | 41/15/0 | {'open-reduced-risk': 121} |
| V90 | 51 | 28.84201157 | 33.36349114/33.36349114 | 6371.80465431 | 37/14/0 | {'open-reduced-risk': 116} |
| V92 | 51 | 29.35570236 | 33.9321286/33.9321286 | 6228.63096022 | 37/14/0 | {'open-reduced-risk': 119} |
| V121AE | 46 | 19.20145378 | 22.480769/22.480769 | 10438.7343719 | 26/20/0 | {'open-reduced-risk': 29, 'reduce-risk': 1, 'trade': 16} |
| V121AF | 44 | 20.26032016 | 23.44256841/23.44256841 | 10420.02497129 | 26/18/0 | {'open-reduced-risk': 28, 'reduce-risk': 1, 'trade': 15} |

## 4. Dirty Files And Active Changes

Active checkpoint changes include scheduler effective stop-hazard cap derivation, verifier stop-hazard execution-authority scan, V121AF flow diagnostic artifacts, V121AF manifest refresh, and focused tests. Existing broader route dirty files remain route-owned/pre-existing and were not reverted.

## 5. Subagent Findings

- Franklin: incorporated. Effective selector action and missed-R truth propagation are represented in current code/tests.
- Aristotle: incorporated. Same-window executable comparator hard dominance is configured; this checkpoint adds the effective stop-hazard cap split he exposed as a selection-scoring risk.
- Jason: incorporated. V92/V121 comparisons are included and exact-window axis transfer is used instead of global-reservoir comparison.
- Euler: incorporated. Verifier now rejects false R reconciliation and broad headline/profile drift.
- Fable: incorporated as plan authority. Implementation sequence/root-cause audit are saved route docs and this checkpoint follows its live-closed proof ladder.

## 6. Mismatch Classes

Source-bound -> candidate is partially fixed: 886/1101 axes generate candidates, but 215 axis gaps remain.

Candidate -> selector is partially fixed: effective/raw action and quality propagation exist, but V121AF still compresses 25,006 candidates to 288 scorecard rows.

Selector -> scheduler is partially fixed: comparator hard dominance is active; V121AG repairs configured stop-hazard `cap` leaking into effective transfer score.

Scheduler -> risk is partially fixed: risk ladder exists, but V121AF distribution is {'open-reduced-risk': 28, 'reduce-risk': 1, 'trade': 15}; V121AG must prove stale cap scoring is gone.

Risk -> order -> lifecycle -> fill remains open: V121AF has {'fill_confirmed_from_predecision_marketable_price_source': 86, 'passive_limit_queue_realism_confirmed_by_penetration_or_repeated_touch': 2} and no guarded fallback applied.

Fill -> exit remains open: V121AF is positive but below V89D/V90/V92; next evidence must distinguish correctness losses from remaining misallocation/exit damage.

Ledger/verifier is fixed for this checkpoint: explicit V121AF verifier is green.

## 7. Fixed / Partial / Open

Fixed: configured-vs-effective stop-hazard cap authority split in scheduler and verifier; V121AF flow diagnostic generated; manifest refreshed; route verifier green.

Partial: exact-window parity, risk-expression ladder, same-window comparator dominance.

Open: V121AG replay proof, candidate->scorecard/order bottleneck, risk distribution proof, removed-winner analysis versus V92, non-May objective regime proof, broad historical proof.

## 8. Highest-Leverage Same-Root Batch Next

Run V121AG with the patched scheduler/verifier to test whether stale configured-cap transfer reduction was suppressing valid candidates. Do not tune exits or selector again until this truth repair is measured unless a hard verifier/truth violation appears.

## 9. Affected Files

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_denominator_to_deployment_verifier.py`
- V121AF flow diagnostic artifacts and `OUTPUT_MANIFEST.json`

## 10. Patch Classes

Correctness: configured/raw guard policy cannot act as runtime cap authority unless effective cap/status/applied truth says so.

Performance: passed/no-cap candidates are no longer transfer-downweighted by the 0.10 stop-hazard cap factor.

Diagnostic/ledger: verifier and manifest now select and scan the completed V121AF artifact set.

## 11. Expected Measurable Effect Before Replay

Candidate -> scorecard transfer may increase if stale cap-adjusted transfer displaced valid candidates. Scorecard -> order transfer may improve through reallocation ranking. Order -> fill transfer is not directly changed. Missed positive R should fall if valid candidates were demoted. Missed negative R may rise if more candidates execute and must be separated. Trade count should stay stable or modestly increase, not drop by suppression. Net/gross/final R should improve versus V121AF if the stale cap split was material. Cost-refused/source-gap execution must remain 0/0. Full-risk vs reduced-risk distribution should only change through causal signed-risk authority.

## 12. Replay Success / Failure Criteria

Helped: V121AG improves V121AF net R or transfer quality without suppressing opportunity, without cost-refused/source-gap execution, and with added trades net positive or correctly reallocated.

Failed: V121AG worsens net R through net-negative added transfers or removes true winners; then selector/ranking/exit quality becomes the next root blocker.

Exposed next flaw: if conversion remains near 886 -> 32 -> 27 with similar R, the limiting leak is candidate-to-scorecard/order admission or lifecycle/fillability/exit, not stop-hazard cap authority.

Broker/live/final remain false. Local replay/package evaluation remains full-authority within replay.
