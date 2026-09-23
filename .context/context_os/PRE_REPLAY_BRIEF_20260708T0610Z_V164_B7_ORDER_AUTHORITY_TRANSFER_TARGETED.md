# V164 B7 Order Authority Transfer Targeted Pre-Replay Brief

Generated: 2026-07-08T06:10Z

Scope: Fable B7 targeted runtime proof only. This is a bounded local proof slice,
not a full-reservoir conversion claim.

## Current Matrix State

- B0: DONE.
- B1: DONE.
- B2: DONE.
- B3: DONE WITH LABEL.
- B4: DONE WITH LABEL.
- B5: DONE.
- B6: DONE WITH LABEL.
- B7: PARTIAL.
- B8: OPEN.

Current selected batch: B7 selected-package/source-bound signed order authority
transfer.

## Latest Completed Replay Baselines

V150 targeted 2026-06-01..2026-06-05, five-symbol repaired profile:
- candidates: 6633
- scorecards: 480
- order rows: 13
- trade rows: 3
- net R: 0.84449709
- gross/final R: 1.09529478 / 1.09529478
- cash PnL: 211.19447407
- W/L/F: 3/0/0
- missed rows: 6627
- missed proxy R: -882.54046433 total, +299.66180240 positive, -1182.20226673 negative

V162 targeted 2026-06-01..2026-06-05, five-symbol repaired profile:
- candidates: 6633
- scorecards: 480
- order rows: 1
- trade rows: 0
- net/gross/final R: 0/0/0
- W/L/F: 0/0/0
- missed rows: 6633
- missed proxy R: -881.69596724 total, +300.50629949 positive, -1182.20226673 negative

V163 targeted 2026-06-04..2026-06-05, XAUUSD repaired profile:
- candidates: 1130
- scorecards: 184
- order rows: 1
- trade rows: 0
- net/gross/final R: 0/0/0
- W/L/F: 0/0/0
- missed rows: 1130
- missed proxy R: -122.41917512 total, +63.60289010 positive, -186.02206522 negative

No broad replay, pytest, or py_compile process is currently running.

## Dirty Files In This Batch

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_broad_replay_repair_config.py`

Unrelated Context OS, cleanup, config, and science-program dirt is out of scope
for this checkpoint and must not be staged.

## Incorporated Findings

- Einstein: incorporated. The V162/V163 gap is a producer/consumer authority
  transfer failure: flattened booleans were stale/false while nested current
  package authority was exact/signable.
- Popper: incorporated. V150 winners were raw reject/off-session rows that
  materialized as `open-reduced-risk`; V162/V163 missed them through
  `package_replay_order_executable_authority_missing`.
- Cicero: incorporated. The same three V150 XAUUSD winners must be the first
  targeted proof rows; cost/source/fillability hard blockers remain non-executable.

## Same-Root Mismatch Chain

source-bound -> candidate:
- Current exact source-bound package authority existed in nested authority
  packets but stale flattened booleans could remain false.

candidate -> selector:
- Raw selector action/reason must remain preserved, while materialized replay
  selector action/reason can become `open-reduced-risk` only under signed
  predecision package authority.

selector -> scheduler:
- Signed package authority alias lookup previously failed for tuple aliases and
  stale-false row values could defeat packet-proven truth.

scheduler -> risk/order:
- Off-configured-session hard block must fail closed unless package executable,
  open-reduced authority, signed new-entry authority, and order-executable
  authority are all present.

order -> lifecycle/fill/exit:
- Unchanged in this patch; replay will reveal the next downstream blocker if
  the V150 winners now pass order authority but still fail later.

ledger:
- Direct and prefixed package-new-entry order-executable fields must be present
  on the authority, candidate/option, and ledger proof surfaces.

## Implemented Repairs Before Replay

Correctness repairs:
- Enabled strict selected-package bridge materialization only for repaired
  profile; raw/guarded remain closed and broker/live/final remain false.
- Fixed `_package_new_entry_authority_surface_value` to honor tuple aliases.
- Let signed package authority namespace refresh override stale false source-bound
  and order-executable aliases when packet-proven true.
- Propagated order-executable candidate-use fields through the selector-reject
  current exact source-bound package materializer.
- Fixed `selector_not_risk_bearing_materialization_skip_reason` to use an actual
  open-reduced authority boolean and to relax off-session only under signed
  order authority.

Diagnostic/proof repairs:
- Added focused tests for V150-style stale-flat/current-nested authority rows.
- Added signer hydration assertions for direct and prefixed order-executable
  authority fields.
- Updated selected-bridge low-fill behavior to fail closed.

## Focused Verification Already Passed

- `py_compile` for touched timewarp/harness/test modules: passed.
- B7 authority path tests: 6 passed.
- Harness repaired/raw/guarded profile split test: 1 passed.
- Scheduler selected-bridge tests: 2 passed.
- Related explicit-package/router-refusal/cost-refusal materialization tests:
  4 passed.

## Expected Replay Effect

Targeted replay prefix:
`BROAD_LIVE_AS_IF_REPLAY_V164_B7_ORDER_EXECUTABLE_AUTHORITY_TRANSFER_REPAIR_20260604_20260605_XAUUSD_TARGETED`

Replay window:
- 2026-06-04..2026-06-05
- symbol: XAUUSD
- profile: repaired package conversion v3

Expected measurable effects:
- candidate -> scorecard transfer: neutral versus V163 unless namespace repair
  exposes additional valid scorecard rows.
- scorecard/order -> fill transfer: should recover the three V150 XAUUSD winner
  order/trade rows or expose a later lifecycle/fill/exit blocker with exact
  reason.
- cost-refused/source-gap execution: must remain zero.
- trade count: expected from V163 0 toward V150 local 3 if the repaired authority
  transfers fully.
- net R: expected from V163 0 toward V150 local +0.84449709 if the same rows fill.
- W/L/F: expected from V163 0/0/0 toward V150 local 3/0/0 if the same rows fill.
- missed positive R: should decrease if valid positive rows transfer to orders.
- missed negative R: should not decrease simply by suppressing all opportunity.

Proof helped if:
- the three V150 candidate IDs materialize with signed order authority and either
  fill as trades or fail at a later, explicit, broker-cost/fillability/lifecycle
  blocker;
- no REFUSED/source-gap/unfillable rows become executable;
- broker/live/final stay false.

Proof failed if:
- V150 rows still show `package_replay_order_executable_authority_missing` or
  off-configured selector-not-risk-bearing skip after the focused code path tests.

Proof exposes next blocker if:
- signed order authority is present but order rows still do not fill due to
  lifecycle, fillability, same-symbol, terminal binding, or exit behavior.
