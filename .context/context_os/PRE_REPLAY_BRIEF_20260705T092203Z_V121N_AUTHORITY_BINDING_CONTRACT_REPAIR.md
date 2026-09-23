# Pre-Replay Brief — V121N Authority-Binding Contract Repair

Generated: `2026-07-05T09:22:03Z`

Broker/live/final remain `false/false/false`. Local replay/package authority remains full. This is a bounded repair proof, not global reservoir conversion proof.

## 1. Latest Completed Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V121M_FINALIZER_SCORE_HANDOFF_REPAIR_20260513_20260517_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`
- Window: `2026-05-13..2026-05-17`
- Rows: candidates `25006`, scorecards `288`, orders `55`, trades `21`
- R: net `4.39334958`, gross `5.855605791`, cash PnL `0.0`
- W/L/F: `9/12/0`
- Missed positive R: `10260.589507650517` over `14552` rows
- Missed negative R: `-15396.204096452155` over `10423` rows
- Cost REFUSED executed: `0`; source-gap cost executed: `0`

## 2. Active Process State

- No `BROAD_LIVE_AS_IF_REPLAY`, pytest, git, or V121 replay process was active at the pre-replay check.
- Do not start a duplicate run if a process appears later; parse or intentionally replace from current evidence.

## 3. Baseline Comparison

- V89D: baseline `34.84520454`R / `56` trades; V121M `4.39334958`R / `21` trades; delta `-30.45185496`R, `-35.0` trades; added `18` trades `6.46580395`R, removed `53` trades `36.91765891`R.
- V90: baseline `28.84201157`R / `51` trades; V121M `4.39334958`R / `21` trades; delta `-24.44866199`R, `-30.0` trades; added `20` trades `4.33440898`R, removed `50` trades `28.78307097`R.
- V92: baseline `29.35570236`R / `51` trades; V121M `4.39334958`R / `21` trades; delta `-24.96235278`R, `-30.0` trades; added `19` trades `5.43064401`R, removed `49` trades `30.39299679`R.

## 4. Dirty Files And Active Changes

- src/components/selector_v4.py - signed selector softening and raw/effective selector authority split are present from the active batch; focused selector tests already passed before this map update.
- src/research/moonshot_scheduler_v4_best_trade_allocator.py - source-aware signed fill alias validation and allocator/risk-ladder authority propagation are active; focused scheduler tests already passed before this map update.
- src/research_infra/v4_timewarp_simulated_live_research_loop.py - exact candidate-time synthesized probe binding, lookup-source provenance, immediate-marketable allocator re-release, fallback failure split, and probe proof propagation are active.
- research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py - immediate-marketable route/path transfer contract, signed open-reduced new-entry fatal, missing exact scheduler-option non-exec fatal, and cost/source-gap contract coverage active.
- tests/test_selector_v4.py, tests/test_moonshot_scheduler_v4_best_trade_allocator.py, tests/test_v4_timewarp_simulated_live_research_loop.py, tests/test_denominator_to_deployment_verifier.py, tests/test_broad_replay_repair_config.py - focused authority/proof tests added or carried forward.
- pre-existing unrelated route/context/code dirt remains in worktree; stage only scoped files after replay/verifier green.

## 5. Subagent Findings

- Boyle: `incorporated` — Verifier transfer contract now blocks immediate-marketable route rows that bind with non-immediate paths; next replay must prove route/path mismatch drops to zero or becomes explicit final_blocked marketable_guard.
- Linnaeus: `incorporated_with_replay_proof_pending` — Selector signed-authority path is on disk and verifier now fatals signed open-reduced new-entry rows with missing/mismatched hash; replay must prove zero executable softened rows without signed authority.
- Dewey: `incorporated` — Runtime backfill now indexes exact candidate instance keys, passes decision_time_utc, records exact vs scheduler-asof lookup source, and focused exact-time test passes.
- Archimedes: `incorporated` — Allocator release is re-applied after rebuild; scheduler accepts stamped source-aware package entry-quality fill alias; focused route/scheduler tests pass.
- Bernoulli: `incorporated` — Added verifier fatal checks and fixtures for signed open-reduced new-entry authority, immediate route/path binding, cost/source-gap execution leaks, and missing exact scheduler-option non-executability; focused verifier tests pass.
- Epicurus: `running` — Do not wait unless blocked; incorporate before launching replay if it returns in time.
- Newton: `running` — Incorporate any blocker before replay.
- Chandrasekhar: `running` — Use returned commands for post-replay verification/audit checkpoint.

## 6. Known Mismatch Classes

- `candidate_to_scorecard`: candidate->scorecard remains 25006->288, preserved versus V92; scorecard is per-window aggregation, not necessarily collapse by itself.
- `fill_to_exit`: filled losing buckets are bounded M1 proxy losses; no final/live broker truth claim. Exit/stop remains monitored after route authority fixes.
- `ledger_truth`: Verifier now asserts patched authority classes; V121N artifacts must carry exact lookup-source and route/fallback failure fields.
- `order_to_fill`: V121M fills 21 trades vs V92 51; accepted-expired and route-intent/order-path mismatches remain.
- `order_to_lifecycle_fill`: Immediate-marketable route intent must match immediate execution path or explicit marketable final blocker; no order_bound limit_first_probe route leaks.
- `risk_to_order`: Cost REFUSED/source-gap rows remain non-executable; risk/order authority must bind only source-complete cost-passed signed rows.
- `scheduler_to_risk`: Exact candidate-time all-candidate probe binding patched; V121N must measure missing_exact_scheduler_option bucket movement without allowing diagnostic probes to execute.
- `scorecard_to_order`: V121M improves V121L from 10 order rows to 55, but remains far below V92 239 order rows; route binding and authority projection still leak.
- `selector_to_scheduler`: Raw/effective selector split and signed softening exist; V121N must prove no unsigned softened open-reduced row reaches order/trade authority.
- `source_bound_to_candidate`: same-window candidate rows are present (25006) but this is a bounded five-day hostile bucket; do not compare directly to the full 1.249M global reservoir.

## 7. Fixed / Partial / Open

Fixed this checkpoint:
- V121M finalizer score handoff baseline remains +4.39334958R on 21 trades; this V121N patch is a pre-replay correctness/proof batch, not a new behavior result yet.
- Immediate-marketable package route rows can no longer pass verifier as order_bound/trade_bound unless order_execution_path is immediate_marketable_limit_at_decision; otherwise they must final_block with explicit marketable_guard reason.
- Signed open-reduced new-entry authority is now verifier-fatal when a valid-looking open-reduced family lacks or mismatches the package new-entry authority hash.
- Missing exact scheduler-option synthesized probes may remain diagnostic/scoreable missed rows but cannot become executable, final-selected, order-bound, or trade-bound.
- Cost REFUSED and cost source-gap rows are pinned non-executable across selected-package compact/disposition and order/trade cost authority scans.
- Exact candidate-time backfill provenance now records exact vs scheduler-asof vs unique-id fallback truth instead of flattering exact labels.
Still open or proof-pending:
- No V121N replay has run yet; all V121N claims are code/test/verifier-contract claims until a targeted smoke completes.
- V121M remains -24.96235278R and -30 trades versus V92 same-window; do not claim behavior solved from this patch.
- Selector/scheduler/order route fixes may add winners or losers. Improvement cannot be accepted if it only suppresses opportunity; report candidate->scorecard->order->fill transfer and missed positive/negative R.
- Full route verifier, route artifact audit, prompt hardening audit, stress/MC, and diff check are pending after replay or targeted proof.
- Epicurus/Newton/Chandrasekhar subagents are running; integrate blockers before replay if returned.

## 8. Highest-Leverage Same-Root Batch Next

- Batch: `V121N authority-binding contract repair targeted proof`
- Why: Same root is fragmented executable authority across selector softening, scheduler option binding, risk finalizer, immediate route intent, broker cost authority, order path binding, and verifier proof.
- Affected files/components:
- `src/components/selector_v4.py`
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `tests/test_selector_v4.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_denominator_to_deployment_verifier.py`
- `tests/test_broad_replay_repair_config.py`
- Patch classes:
- `exact_candidate_time_binding`: correctness + diagnostic repair
- `signed_selector_softening`: correctness repair
- `immediate_marketable_route_binding`: correctness repair
- `cost_source_gap_non_execution`: correctness + proof repair
- `missing_exact_scheduler_option_non_execution`: diagnostic/proof repair
- `verifier_assertions`: proof/diagnostic repair

## 9. Expected Measurable Effect Before Replay

- `candidate_to_scorecard_transfer`: no intentional top-N narrowing; candidate rows and scorecard rows should remain near V121M unless invalid unsigned softening becomes diagnostic before scorecard
- `scorecard_to_order_transfer`: valid signed source-complete cost-passed candidates should bind more consistently; unsigned/cost-gap rows should not order-bind
- `order_to_fill_transfer`: immediate-route/order-path mismatches should drop to zero or become final_blocked marketable_guard; accepted-expired suspect route rows should be explained
- `missed_positive_r`: positive missed R should move only if signed, cost-passed, fillable, exact scheduler-bound, and route-bound; otherwise reason stays explicit
- `missed_negative_r`: negative rows may also move under same causal rules; do not suppress them to improve net R
- `trade_count`: may rise, fall, or shift; not a pass/fail alone
- `net_gross_final_r`: may improve or worsen; pass/fail is authority correctness plus same-window transfer explanation
- `win_loss_flat`: report separately; do not infer live readiness
- `cost_refused_source_gap_execution`: must remain exactly zero
- `risk_reduced_full_risk_distribution`: no global promotion; full-risk rows still require all signed ladder conditions, reduced rows need tier causes

## 10. Replay Success / Failure Criteria

- Preferred next prefix: `BROAD_LIVE_AS_IF_REPLAY_V121N_AUTHORITY_BINDING_CONTRACT_REPAIR_20260513_20260517_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`
- Window: `2026-05-13..2026-05-17`
- Rule: run fastest targeted smoke/projection command from current route harness after subagent command check returns; do not broad historical replay before this local proof
- Helped if: zero verifier-fatal authority leaks in the patched classes; route/path mismatch count reduced to zero or explicit final_blocked; zero cost-refused/source-gap executions; no missing-exact probe executable rows; behavior metrics parsed same-window vs V121M and V92
- Failed/exposed next flaw if: if replay worsens because truth was corrected, keep truth and rank next root leak; if a patched verifier class remains nonzero, patch before broadening
- Not proof of: global 1.249M reservoir transfer or live readiness

## 11. Interpretation Rule

This smoke proves or disproves the local authority-binding repair; it does not prove total reservoir conversion. Normalize any source-bound transfer discussion to this exact replay window.

