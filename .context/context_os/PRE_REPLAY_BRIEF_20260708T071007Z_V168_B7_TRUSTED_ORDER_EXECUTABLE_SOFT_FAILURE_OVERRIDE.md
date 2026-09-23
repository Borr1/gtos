# Pre-Replay Brief - V168 B7 Trusted Order-Executable Soft-Failure Override

Generated UTC: 2026-07-08T07:10:07Z.

## Fable Matrix Position

- Active dependency batch: B7 full proof ladder, scheduler/order/risk-expression transfer.
- B0/B1/B2/B5 are DONE in the current Fable matrix.
- B3/B4/B6 are DONE WITH LABEL and must remain truthful but are not the active dependency.
- B8 is OPEN and ineligible until B7 gates pass.
- Broker mutation, live broker authority, and final selection remain false.

## Current Process State

- No `BROAD_LIVE_AS_IF_REPLAY` or `run_broad_live_as_if_replay_harness.py` process is active.
- This brief authorizes one targeted replay only, not a broad replay.

## Latest Completed Runtime Proofs

- V150 targeted five-symbol/same-window behavior proof remains the latest positive behavior baseline:
  - candidates `6633`, scorecards `480`, order event rows `13`, terminal order rows `6`, trades `3`;
  - W/L/F `3/0/0`;
  - net/gross/final R `0.84449709 / 1.09529478 / 1.09529478`;
  - cash PnL `211.19447407`, risk cash/risk pct `750.42443587 / 0.75`.
- V165 XAUUSD 2026-06-04..2026-06-05 targeted proof:
  - candidates `1130`, scorecards `184`, order rows `1`, trades `0`;
  - order row was `risk_rejected`; missed rows `1130`; net/gross/final R `0`.
- V166 same target:
  - same as V165; watched candidate rows had current package order authority true, but scorecard/missed demoted to `risk_pct_basis_missing`.
- V167 same target:
  - same as V166; candidate rows still carried order authority true, but scheduler option recomputed older reduce-risk/fill-floor failures into `package_replay_order_executable_candidate_use_allowed=false`.

## Patch Batch

Files changed for this pre-replay checkpoint:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`

Patch type:

- Correctness repair: trust current signed package/order authority over stale nested soft failures only when all broker-cost, source-completeness, raw-reject promotion, limit-fillability, and signed-authority checks pass.
- Risk-expression repair: clear stale reduced-risk hard-block/quality vetoes only after the trusted package-order soft-failure override passes.
- Diagnostic repair: emit `trusted_order_executable_soft_failure_override_*` fields into scheduler authority and candidate decision inputs.

Hard boundaries preserved:

- REFUSED broker-cost/source-gap rows remain non-executable.
- Non-soft failures remain hard blockers.
- No date/symbol/session loss-bucket rule was added.
- No top-N narrowing or trade suppression was added.

Focused proof already passed:

- `python3 -m py_compile src/research/moonshot_scheduler_v4_best_trade_allocator.py tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `python3 -m pytest tests/test_moonshot_scheduler_v4_best_trade_allocator.py -k "explicit_order_authority_soft_failures_release_without_top_level_order_field or explicit_order_authority_soft_failure_release_keeps_refused_cost_hard or order_executable_package_authority_releases_zero_requested_risk_basis or current_package_order_authority_supersedes_stale_nested_false_inputs or raw_reject_open_reduced_order_execution_derives_missing_contract_from_signed_authority or raw_reject_open_reduced_order_execution_requires_limit_fillability_contract or raw_reject_open_reduced_order_execution_canonicalizes_materialized_action" -q --tb=short`
  - Result: `7 passed, 256 deselected, 1 warning`.

## Expected V168 Effect

Replay target:

- `2026-06-04..2026-06-05`, symbol `XAUUSD`, profile `repaired_package_conversion_v3`.

Success criteria:

- Watched V150/V167 candidate IDs no longer end at `risk_pct_basis_missing`.
- Scorecard option rows show `trusted_order_executable_soft_failure_override_allowed=true` only for cost-passed/source-complete/signed rows.
- `package_replay_order_executable_candidate_use_allowed=true` reaches scorecard/order-transfer fields.
- Approved risk becomes non-zero for the trusted soft-failure class, bounded by reduced-risk caps.
- Executed REFUSED/source-gap counts remain `0`.
- If order rows/trades still remain `0`, the next B7 blocker is downstream scorecard/order/missed propagation rather than scheduler option authority.

Failure criteria:

- REFUSED or source-gap rows become executable.
- Trusted override fires with non-soft blockers, missing signed authority, missing broker-cost proof, or missing source-completeness proof.
- `risk_pct_basis_missing` remains on the watched trusted rows despite scheduler option authority being true.

This targeted replay proves or disproves the local B7 scheduler/order/risk-expression repair only. It does not prove full reservoir transfer.
