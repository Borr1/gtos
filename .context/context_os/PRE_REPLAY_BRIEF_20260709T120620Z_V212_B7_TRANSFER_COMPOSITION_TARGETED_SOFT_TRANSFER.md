# V212 B7 Transfer-Composition Targeted Soft-Transfer Proof

Generated UTC: 2026-07-09T12:06:20Z.

## Current Completed Replay

Latest completed replay:
`BROAD_LIVE_AS_IF_REPLAY_V211_B7_2_HOSTILE_5D_VALUE_TRANSFER_POST_B1_B5_PROOF_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`

V211 was verifier-clean but failed B7.2 value transfer:

- candidate / decision / scorecard / order-event / simulated-order / trade rows:
  `25006 / 11424 / 288 / 50 / 27 / 18`;
- W/L/F: `11 / 7 / 0`;
- net/gross/final R: `-3.47466796 / -1.91290882 / -1.91290882`;
- cash PnL: `-868.32556257`;
- cost REFUSED/source-gap executed rows: `0 / 0`;
- all filled trades/order risk decisions were reduced-risk; full-risk filled
  trades `0`.

Primary V211 leak class:
`candidate_generated_not_scheduler_selected`, with `276` leakage bucket rows,
`3807` candidate trace rows, and `354857.6686863841R` effective source-bound R.

## Active Patch Batch

Selected Fable batch:
`B7_TRANSFER_COMPOSITION_REPAIR_AFTER_V211`.

Patch scope:

- scheduler soft-transfer admission for signed, cost-passed, source-complete,
  order-executable package candidates blocked by soft selector/materialization
  reasons;
- reduced-risk proof propagation: risk pct basis/provenance and full-risk
  fill-floor proof fields now flow into compact/order/trade surfaces and the
  verifier scans reduced signed executable rows;
- broker-cost REFUSED/source-gap rows remain non-executable.

Touched files:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_denominator_to_deployment_verifier.py`

Focused proof already green before replay:

- `python3 -m py_compile` on touched scheduler/runtime/harness/verifier files;
- scheduler soft-transfer tests: `5 passed`;
- verifier/runtime risk-expression tests: `5 passed`.

## Targeted Replay

Run the smallest replay proof for the known V211 transfer leak:

Prefix:
`BROAD_LIVE_AS_IF_REPLAY_V212_B7_TRANSFER_COMPOSITION_TARGETED_SOFT_TRANSFER_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`

Scope:

- dates: `2026-05-13..2026-05-14`;
- symbols: `XAUUSD`, `USDCAD`, `USDJPY`;
- profile: `repaired_package_conversion_v3`;
- this is a targeted proof slice, not a full reservoir or B7.2 broad claim.

Target rows from V211 evidence:

- `broadorigin_22e015f281ec8e3a455e81ef@@2026-05-14T09:00:00+00:00`
  (`XAUUSD`) was cost-passed, source-complete, signed, fillable, and
  final-blocked by `selector_open_reduced_risk_package_fill_floor_authority`;
- `broadorigin_f7e279f72d749354a9e5dd2e@@2026-05-14T11:45:00+00:00`
  (`USDCAD`) had the same soft fill-floor-authority transfer blocker;
- `broadorigin_e5e2db0e76766b79f7bfa016@@2026-05-13T17:00:00+00:00`
  (`USDJPY`) was cost-passed, source-complete, signed, fillable, and blocked
  by same-decision/marketable soft-transfer handling.

## Expected Measurable Effect

This replay should prove or fail the B7 transfer-composition patch locally:

- scorecard/order transfer should increase for cost-passed, source-complete,
  fillable, signed soft-transfer candidates;
- REFUSED/source-gap execution must remain `0 / 0`;
- true not-order-executable and expiry rows must remain blocked;
- missed rows should retain risk pct basis/provenance and fill-floor proof when
  reduced signed executable candidates remain missed;
- if added transfers fill, report whether they are net positive or net
  negative versus the V211 same target slice;
- if target rows still do not reach scorecard/order/trade, their blocker must
  be a different explicit downstream cause, not the patched soft-transfer
  terminal filter.

## Acceptance

Helped:

- at least one target soft-transfer class moves from scheduler/missed space into
  scorecard/order transfer, or the replay exposes the next precise consumer
  blocker with risk/fill-floor proof fields present;
- executed REFUSED/source-gap remains `0 / 0`;
- no positive-by-suppression claim is made.

Failed:

- target rows remain blocked by
  `selector_open_reduced_risk_package_fill_floor_authority` or
  `same_decision_cluster_burst_guard` without a downstream causal consumer
  reason;
- reduced signed executable rows still omit risk pct provenance or full-risk
  fill-floor values;
- REFUSED/source-gap rows execute.

Broker/live/final remain closed.
