# Pre-Replay Brief - V167 B7 Order-Executable Risk Basis Release

Generated UTC: 2026-07-08T06:52:04Z.

## Current Batch

Fable dependency batch: B7 full proof ladder, targeted transfer repair.

Current latest completed focused runtime proof:

- V166 prefix: `BROAD_LIVE_AS_IF_REPLAY_V166_B7_STALE_NESTED_ORDER_AUTHORITY_TRANSFER_REPAIR_20260604_20260605_XAUUSD_TARGETED`
- Window: XAUUSD, 2026-06-04 through 2026-06-05.
- Result: `1130` candidates, `184` scorecards, `1` order row, `0` trades, `1130` missed rows, net/gross/final R `0/0/0`, cash PnL `0`.
- Same-window V150 subset had `1201` candidates, `7` order rows, `3` trades, W/L/F `3/0/0`, net/gross/final R `0.84449709/1.09529478/1.09529478`, cash PnL `211.19447407`.

## Root Failure

V166 proved the previous candidate-level patch was not enough. The three watched V150 winner IDs:

- `broadorigin_62cb335107ef114d9725321c`
- `broadorigin_e59c330b1467251e45c3fd09`
- `broadorigin_a143179e468040fcc9bd5c71`

all carried `package_replay_order_executable_candidate_use_allowed=true` in the candidate ledger, but scorecard/missed propagation still reached no order/trade. Missed rows were blocked as `risk_pct_basis_missing`, with scheduler risk fields at zero.

Root class: signed package order-executable authority was not consumed by the scheduler risk-basis release path when the row had zero requested/selected risk and stale reducer/fill-floor/off-session blockers from older authority paths.

## Patch

File changed:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`

Test changed:

- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`

Behavior-changing repair:

- Preserve the original nonpositive requested-risk basis.
- Allow a bounded zero-risk release for signed package order-executable rows only when all of these hold: package replay executable, package replay order executable, signed new-entry authority valid, broker cost PASSED with no source-gap/fallback authority, source complete, no execution authority veto, no selected-policy calibration blocker, and no non-bypassable source/calibration fill-floor blocker.
- Clear only stale risk-basis/dynamic-fill/reducer vetoes that are superseded by the same explicit order-executable authority.
- Preserve REFUSED/source-gap/unfillable rows as non-executable.

Focused checks already passed:

- `python3 -m py_compile src/research/moonshot_scheduler_v4_best_trade_allocator.py tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `python3 -m pytest tests/test_moonshot_scheduler_v4_best_trade_allocator.py -k "order_executable_package_authority_releases_zero_requested_risk_basis or current_package_order_authority_supersedes_stale_nested_false_inputs or raw_reject_open_reduced_order_execution_derives_missing_contract_from_signed_authority or raw_reject_open_reduced_order_execution_requires_limit_fillability_contract or raw_reject_open_reduced_order_execution_canonicalizes_materialized_action" -q`

## Expected Focused Replay Effect

V167 targeted proof should be run on the same V166 window and config:

- Window: XAUUSD, 2026-06-04 through 2026-06-05.
- Profile: `repaired_package_conversion_v3`.

Success criteria:

- Candidate rows for the three watched V150 winners remain package order-authorized.
- Their scorecard/missed/order surfaces no longer block solely as `risk_pct_basis_missing`.
- Order rows and/or trade rows increase versus V166 if lifecycle/fillability permits.
- Executed broker-cost REFUSED/source-gap rows remain `0`.
- If trades still do not fill, the next blocker must be a later executable stage, not missing risk basis.

This is a bounded B7 repair proof. It does not prove full reservoir conversion or live readiness. Broker/live/final remain false.
