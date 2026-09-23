# V189 B7 Pre-Replay Brief - Risk-Expression Namespace Parity

Generated UTC: 2026-07-08T12:49:58Z

## Latest Completed Replay

Latest completed targeted proof:
`BROAD_LIVE_AS_IF_REPLAY_V188_B7_CLOSE_REVERSE_TERMINAL_LIFECYCLE_CLOSE_R_PRODUCER_BOUNDARY_20260604_20260605_XAUUSD_TARGETED`

V188 counts and behavior:

- candidates / scorecards / orders / trades / missed / buckets:
  `1130 / 184 / 28 / 12 / 1116 / 34`
- W/L/F: `9 / 3 / 0`
- net/gross/final R: `2.29004187 / 3.19764809 / 3.19764809`
- cash PnL: `1362.61375829`
- risk cash: `7369.13533739`
- risk pct: `7.375`
- expected cost R: `0.90760621`
- executed broker-cost REFUSED/source-gap rows: `0 / 0`

V188 closed the close/reverse terminal lifecycle truth gap:
`not_committed_scheduler_close_and_reverse_close_r_missing` went to `0`, and
two close/reverse old legs are now source-bound ordered-tick close rows.

## Current Mismatch

The next B7 mismatch is ledger/action namespace parity, not sizing:

- V188 filled trade rows all show `effective_selector_action =
  open-reduced-risk`.
- But V188 order rows show six filled rows with `risk_decision=trade`,
  `full_risk_allowed=true`, `full_risk_applied=true`, and `risk_pct=1.0`.
- Therefore the system is not actually sizing every trade as reduced-risk; it
  is losing the final risk-expression action in order/trade provenance.

This causes downstream audits and owner-facing reports to read "all risk
reduced" even when finalizer authority applied full risk.

## Code Changes Under Test

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
  - Adds `apply_risk_expression_effective_action_fields(...)`.
  - Preserves raw/materialized package action fields:
    `raw_selector_action`, `materialized_selector_action`,
    `materialized_package_selector_action`,
    `risk_expression_materialized_package_action`.
  - Sets final risk-expression fields from `risk_decision`:
    `effective_selector_action`, `risk_expression_effective_action`,
    `effective_risk_decision`, `admission_risk_class`,
    `effective_admission_risk_class`.
  - Applies the helper to normalized ledger rows and filled open-position
    state so later trade rows inherit final risk-expression provenance.
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
  - Adds normalized-row full-risk namespace test.
  - Adds pending-to-filled position namespace test.

Focused proof already run:

- `python3 -m py_compile
  src/research_infra/v4_timewarp_simulated_live_research_loop.py
  tests/test_v4_timewarp_simulated_live_research_loop.py`: passed.
- Focused pytest selection: `6 passed, 584 deselected, 1 warning`.

## Expected Replay Effect

This patch should be behavior-neutral for trade selection and R:

- candidate -> scorecard transfer: unchanged
- scorecard -> order transfer: unchanged
- order -> fill transfer: unchanged
- trade count: unchanged
- net/gross/final R: unchanged except tiny cash drift only if row ordering or
  risk provenance mutation affects an unintended consumer
- W/L/F: unchanged
- cost REFUSED/source-gap execution: remains `0 / 0`

Expected ledger/proof effect:

- Filled rows with `risk_decision=trade` should show
  `effective_selector_action=trade`, `admission_risk_class=trade`, and
  `risk_expression_effective_action=trade`.
- Raw package softening remains visible as `raw_selector_action` and
  `materialized_selector_action=open-reduced-risk`.
- Reduced-risk rows should remain `open-reduced-risk`.

V189 helped if the V188 six full-risk rows no longer collapse to
`effective_selector_action=open-reduced-risk` while behavior stays neutral.

V189 failed if:

- any full-risk row still reports reduced effective/admission action;
- raw/materialized selector provenance is lost;
- trade count/R changes materially, which would mean the supposed ledger-only
  helper is leaking into behavior.

No broad replay is allowed for this checkpoint. Use the same bounded XAUUSD
2026-06-04..2026-06-05 targeted slice.

