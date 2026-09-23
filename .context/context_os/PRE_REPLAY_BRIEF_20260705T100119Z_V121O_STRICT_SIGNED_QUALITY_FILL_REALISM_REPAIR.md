# Pre-Replay Brief — V121O Strict Signed Quality And Fill-Realism Repair

Generated: `2026-07-05T10:01:19Z`

Broker/live/final remain `false/false/false`. Local replay/package authority remains full. This is a bounded five-day hostile repair proof, not global reservoir conversion proof.

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

- No broad replay, pytest, verifier, py_compile, or git helper was active in the current pre-replay check.
- Only `gtos_context.py mcp-stdio` helper processes were observed.
- `V121N` partial/interrupted replay artifacts must not be used as behavior evidence.

## 3. Baseline Comparison

- V89D: baseline `34.84520454`R / `56` trades; V121M `4.39334958`R / `21` trades; delta `-30.45185496`R, `-35` trades.
- V90: baseline `28.84201157`R / `51` trades; V121M `4.39334958`R / `21` trades; delta `-24.44866199`R, `-30` trades.
- V92: baseline `29.35570236`R / `51` trades; V121M `4.39334958`R / `21` trades; delta `-24.96235278`R, `-30` trades.

## 4. Dirty Files And Active Changes

- `src/components/selector_v4.py`: strict signed selector authority binding.
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`: signed package-new-entry quality scalars and tightened fill-source authority.
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: row-time cache identity repair, model-vs-execution fill split, guarded fallback cost parity, signed router-refusal authority use, and diagnostic fill truth preservation.
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`: scorecard/order/trade/missed scheduler-status authority scan wiring.
- Focused tests updated for the stricter signed quality and non-executable diagnostic M1 first-touch behavior.

## 5. Subagent Findings

- Newton: `incorporated` — strict signed authority needs expected/current SHA-256, candidate id, decision time, instance keys, predecision/no-outcome boundary, and no-outcome flag. Scorecard/missed verifier wiring also needed.
- Epicurus: `incorporated` — use a fresh replay prefix and parse V121O, not interrupted V121N.
- Chandrasekhar: `incorporated` — post-replay verifier/audit command lane retained.
- Prior Boyle/Linnaeus/Dewey/Archimedes/Bernoulli findings remain incorporated from V121N.

## 6. Known Mismatch Classes

- `source_bound -> candidate`: same-window candidates exist; do not compare this five-day proof to the full global reservoir.
- `candidate -> selector -> scheduler`: signed open-reduced authority is now strict and carries signed quality scalars.
- `scheduler -> risk`: model fill probability and execution fill probability are separate; generic fill aliases remain rejected.
- `risk -> order`: cost REFUSED/source-gap rows remain non-executable but scoreable as missed.
- `order -> lifecycle -> fill`: M1 first-touch without ordered tick truth is diagnostic only; immediate-marketable routes require signed/causal authority.
- `fill -> exit`: diagnostic fills cannot open trades or drive final R.
- `ledger`: scheduler-status authority scan covers scorecard/order/trade/missed.

## 7. Fixed / Partial / Open

Fixed before replay:

- Strict selector signed-authority validation and tests.
- Verifier scorecard/missed path wiring.
- Row-time source cache stale-id repair.
- Scheduler full signed quality scalar propagation.
- Guarded fallback cost/net parity after execution surcharge.
- Diagnostic M1 first-touch preservation without executable fill authority.

Still open:

- No V121O behavior replay has completed yet.
- V121M remains materially below V92 same-window behavior.
- Selected-order exact binding has one medium-risk `candidate_id@@asof_utc` path; patch if V121O exposes non-asof selected-order leakage.
- Full verifier, route artifact audit, prompt hardening audit, stress/MC parse, and diff check are pending after replay.

## 8. Highest-Leverage Same-Root Batch Next

- Batch: `V121O strict signed quality and fill-realism replay proof`
- Affected files: selector, scheduler, timewarp harness, route verifier, focused tests.
- Patch types: correctness repairs for authority binding, signed quality propagation, model-vs-execution fill split, and diagnostic fill truth; proof repair for verifier wiring.

## 9. Expected Measurable Effect Before Replay

- Candidate->scorecard should remain near V121M unless invalid unsigned rows demote before scorecard.
- Scorecard->order should bind only signed, source-complete, broker-cost-passed rows.
- Order->fill may fall if diagnostic M1 fills were previously flattering; valid immediate-marketable routes may add fills.
- Missed positive R may rise if diagnostic winners stop executing; missed positive R may fall if signed routes now execute.
- Missed negative R can move under the same truth rules.
- Cost-refused/source-gap executions must stay zero.
- Risk-reduced/full-risk distribution must retain signed provenance.

## 10. Replay Success / Failure Criteria

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V121O_STRICT_SIGNED_AUTHORITY_BINDING_REPAIR_20260513_20260517_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`
- Window: `2026-05-13..2026-05-17`
- Helped if patched authority leaks are zero, route/order mismatches are gone or explicit final blocks, cost-refused/source-gap executions remain zero, and same-window transfer is parsed vs V121M and V92.
- Failed or exposed next flaw if headline R worsens from stricter truth; keep the truth, then rank and patch the next executable leak.
- Not proof of live readiness or full 1.249M reservoir conversion.
