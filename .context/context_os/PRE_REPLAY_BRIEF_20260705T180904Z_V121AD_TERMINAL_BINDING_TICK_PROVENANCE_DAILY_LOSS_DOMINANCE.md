# V121AD Pre-Replay Brief: Terminal Binding, Tick Provenance, Daily-Loss Dominance

Generated: 2026-07-05T18:09:04Z

## 1. Latest Completed Replay

Latest completed behavioral prefix:

`BROAD_LIVE_AS_IF_REPLAY_V121AB_HOSTILE_5D_RUNTIME_FINAL_RISK_AUTHORITY_GENERALIZATION_20260513_20260517`

Window: 2026-05-13..2026-05-17.

Numbers: 23,970 candidates; 288 scorecards; 139 order events; 56 filled trades; net +15.33728438R; gross/final +19.31963588R; expected cost 3.9823515R; cash PnL +6869.54005741; W/L/F 29/27/0; public final-risk mismatches 0; executed broker-cost REFUSED 0; executed source-gap 0; missed positive 907 rows / +969.17351333R; missed negative 3,447 rows / -5037.95529758R.

## 2. Active Process State

No broad replay, analyzer, pytest, or git helper process is running.

The temporary git auto-stage blocker lock is present at the linked worktree gitdir. It must remain in place until intentional git operations.

## 3. Same-Window Baselines

Against V121AB on 2026-05-13..2026-05-17:

- V89D: trades delta 0; net delta -19.50792016R; added 51 trades / +12.95924482R; removed 51 trades / +32.82987139R.
- V90: trades delta +5; net delta -13.50472719R; added 51 trades / +12.95924482R; removed 46 trades / +26.82667842R.
- V92: trades delta +5; net delta -14.01841798R; added 51 trades / +12.95924482R; removed 46 trades / +27.34036921R. Largest removed-winner bucket remains ordered-tick/fill-realism authority.
- V97: trades delta +9; net delta +1.44100707R; added 50 trades / +9.49159363R; removed 41 trades / +8.05058656R.

Do not compare this 5-day run to the global 1.249M source-bound reservoir.

## 4. Dirty Files And Active Code Changes

Active patch files:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_denominator_to_deployment_verifier.py`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP.json`
- this pre-replay brief.

Live-state reports many unrelated existing dirty files and old deleted raw ledgers. They are not part of this replay proof and must not be staged with this checkpoint.

## 5. Subagent Findings Status

- Mendel ordered-tick audit: incorporated. Tick query availability, source path, coverage start/end, window coverage, and local tick gap reason now survive M1 fallback into oracle provenance.
- Wegener terminal-binding audit: incorporated. Terminal lifecycle deferred rows now become `terminal_lifecycle_deferred_source_gap` with no executable bound trade id, including the producer append path; verifier rejects legacy bound terminal-deferred rows.
- Locke risk/scheduler audit: incorporated. Specialized same-symbol daily-loss release paths are dominated by the base daily-loss release flag; the ledger emits dominance provenance.
- Prior marketable guard findings: deferred. Broad guard release remained net negative; no causal safe release patch here.
- Prior stop-hazard target-margin findings: deferred. Stop-pressure was not discriminative enough for a causal policy patch.

## 6. Root Mismatch Chain

- Source-bound -> candidate: hostile-5d candidate generation remains present; exact full-reservoir claims remain disallowed for this bounded window.
- Candidate -> selector: still open for removed-winner materialization, but not the patch focus.
- Selector -> scheduler: still open for replacement allocation after removed V92 winners.
- Scheduler -> risk: public risk mismatch is fixed; same-symbol daily-loss release dominance is now patched as a causal risk-lockout truth repair.
- Risk -> order: cost REFUSED/source-gap rows must remain non-executable.
- Order -> lifecycle: terminal-deferred rows must be proof-only blocked, not order/trade bound.
- Lifecycle -> fill: ordered-tick provenance must distinguish true tick-source gaps from over-strict fill-realism authority.
- Fill -> exit: stop-first losses remain a possible next batch only after this transfer proof.
- Ledger: terminal binding/deferred ids and tick coverage fields must propagate deterministically.

## 7. Fixed, Partial, Open, Newly Exposed

Fixed in this batch: terminal-deferred executable binding leak; tick gap loss during M1 fallback; base-dominated same-symbol daily-loss release authority.

Partial: ordered-tick/fill-realism remains a large removed-winner class; V121AD only proves provenance unless source hydration becomes available. Risk-expression ladder still needs regime validation.

Open: same-window axis transfer fields; selector/scheduler replacement allocation; stop-first repeated losses; non-hostile regime generalization.

Newly exposed risk: V121AD can improve by blocking daily-loss release rows. That is acceptable only if the replay reports blocked winners, blocked losses, missed opportunity, and reallocation separately.

## 8. Highest-Leverage Same-Root Batch

Run V121AD hostile 5-day replay with the current code batch:

terminal binding truth + ordered-tick source provenance + base-dominated same-symbol daily-loss release.

## 9. Affected Components

- `package_order_executable_final_blocker_fields`
- `normalize_package_new_entry_authority_ledger_row`
- scheduler terminal lifecycle order-row append path
- `scheduler_missed_opportunity_attribution_fields`
- `path_source_and_oracle`
- `path_oracle_provenance_ledger_fields`
- same-symbol daily-loss cooldown release predicates
- `scan_broad_order_executable_transfer_contract`

## 10. Patch Classes

- Terminal binding: correctness + verifier repair.
- Ordered tick provenance: correctness + diagnostic/ledger repair.
- Daily-loss base dominance: correctness + performance-affecting risk-authority repair.

## 11. Expected Measurable Effects

- Candidate -> scorecard: unchanged.
- Scorecard -> order: terminal-deferred rows should not appear executable-bound.
- Order -> fill: daily-loss-only specialized release rows may no longer fill; valid replacements may fill if scheduler reallocates.
- Missed positive R: may rise if blocked daily-loss rows were winners; must be itemized.
- Missed negative R: may rise in magnitude if blocked daily-loss rows were losers; expected direct V121AB filled daily-loss release bucket was 10 trades / -1.938394R.
- Trade count: likely lower only for daily-loss release rows unless reallocation replaces them.
- Net/gross/final R: expected local lift is bounded by the removed loss bucket unless replacement behavior changes the set.
- W/L/F: should show whether blocked rows were primarily losers or winners.
- Cost-refused/source-gap execution: must remain zero.
- Risk-reduced/full-risk distribution: should only change through removed/reallocated daily-loss release rows.

## 12. Replay Success, Failure, Next Flaw

Helped if: tests remain green; executed REFUSED/source-gap remains zero; terminal-deferred rows are non-executable blocked rows; tick coverage fields exist in oracle/order-derived rows; daily-loss release rows are blocked or causally reallocated; delta is explained by blocked winners/losses and replacement behavior rather than silent suppression.

Failed if: terminal-deferred rows still bind trade ids; tick gap fields disappear in fallback; cost REFUSED/source-gap rows execute; net improves only by suppressing opportunity without clear missed-positive accounting; or scheduler fails to reallocate when valid next candidates exist.

Next deeper flaw if helped: rank remaining loss buckets after V121AD, especially stop-first/exit geometry, selector/scheduler removed-winner replacement, ordered-tick hydration or non-executable proof, and residual same-symbol lifecycle interactions.
