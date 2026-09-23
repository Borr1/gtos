# V151F B7 Stable-Window Lifecycle Transfer Prepatch Brief

Generated UTC: 2026-07-07T15:10:29Z

No broad replay is authorized by this brief. The next proof is a focused
producer/consumer/verifier rebuild for selected-package lifecycle window
transfer status.

## Current Replay Anchor

- Latest completed behavior proof:
  `BROAD_LIVE_AS_IF_REPLAY_V150_B7_SIGNED_ACTION_FINALIZER_ROUTE_AND_IMMEDIATE_PREFLIGHT_CONSUMER_REPAIR_20260601_20260605_TARGETED`.
- Scope: 2026-06-01..2026-06-05, symbols `XAUUSD`, `XAGUSD`, `USDCAD`,
  `USDJPY`, `UKOIL_cash`.
- Rows: candidates `6633`, scorecards `480`, order event rows `13`, terminal
  orders `6`, trades `3`, missed rows `6627`.
- Headline: net `+0.84449709R`, gross/final `+1.09529478R / +1.09529478R`,
  cost `0.25079769R`, cash PnL `+211.19447407`, W/L/F `3/0/0`.
- Interpretation: bounded local B7 repair proof only; not full-reservoir
  conversion evidence.

## Process State

No broad replay, targeted replay, route builder, verifier, compile, or pytest
process is running.

## Fable Matrix

B0 DONE, B1 DONE, B2 DONE, B3 DONE WITH LABEL, B4 DONE WITH LABEL, B5 DONE,
B6 DONE WITH LABEL, B7 PARTIAL, B8 OPEN.

## Selected Same-Root Batch

V151F B7 stable-window lifecycle transfer status:

- producer: `build_denominator_to_deployment_execution.py`;
- consumer: `build_source_bound_execution_parity.py`;
- verifier: `verify_denominator_to_deployment_execution.py`;
- tests: `tests/test_build_source_bound_execution_parity.py` and
  `tests/test_denominator_to_deployment_verifier.py`.

The exact source-member surface has:

- `293` rows in
  `source_axis_selected_package_bridge_materialized_axis_lifecycle_label_context_not_stable_window_matched`;
- `162` rows in selected-package bridge materialized with no lifecycle context;
- `79` rows missing current selected-package replay source materialization;
- `21` candidate-namespace rows with lifecycle context source gap.

Lifecycle-related source-member rows currently show source-window samples
missing on `614/711`, bridge-window samples present on `601/711`, and only `4`
source/bridge window overlaps. That makes transfer status the next blocking
truth surface.

## Expected Effect

Behavior should be neutral or reclassification-only before runtime replay.
Candidate->scorecard, scorecard->order, order->fill, trade count, net/gross/final
R, and W/L/F should not change unless a runtime consumer is intentionally
patched. Cost-refused/source-gap execution must remain zero.

## Success Criteria

- Axis lifecycle IDs produce a deterministic transfer status:
  `bridge_window_overlap`, `source_window_missing`, `bridge_window_missing`,
  `bridge_window_mismatch`, or `no_axis_lifecycle_context`.
- Parity labels split the generic stable-window mismatch into exact subreasons.
- Verifier fails rows that have lifecycle IDs but lack transfer status.
- Focused tests and route verifier pass.
- No broad replay runs before producer/consumer/verifier proof is green.
