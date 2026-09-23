# V183 B7 Pre-Replay Brief - Signed Executable Cooldown Release Promotion Contract

Generated UTC: 2026-07-08T10:41:51Z

## Control State

- Fable batch: B7 runtime transfer.
- Latest completed replay: `BROAD_LIVE_AS_IF_REPLAY_V182_B7_DERIVED_ROUTER_REFUSAL_MARKETABLE_AUTHORITY_RELEASE_20260604_20260605_XAUUSD_TARGETED`.
- Broker/live/final: closed. This patch does not alter broker mutation, live authority, or final selection.
- Replay scope for proof: same bounded XAUUSD 2026-06-04..2026-06-05 targeted slice. This remains a local repair proof, not full-reservoir conversion.

## V182 Evidence

V182 correctly transferred signed marketable-limit rows but exposed downstream displacement:
- V181 -> V182 trades: `6 -> 7`.
- Net R: `+1.43436072 -> +0.28315612`.
- V182 added four marketable immediate-limit trades with net group `+0.09980257R`.
- V182 removed three V181 winners totaling about `+1.250...R`.
- Two removed winners were selected pre-finalizer and signed/order-executable in missed accounting, but runtime rejected them with `recent_same_symbol_closed_trade_cooldown`.

The affected missed rows:
- `broadorigin_e59c330b1467251e45c3fd09@@2026-06-04T18:15:00+00:00`, missed proxy `+0.38818935R`.
- `broadorigin_de06e049904b34e7157320bc@@2026-06-05T20:30:00+00:00`, missed proxy `+0.57190978R`.

Both rows show:
- `scheduler_pre_finalizer_selected_candidate_instance_keys` present;
- `scheduler_option_risk_expression_ladder_tier = full`;
- `missed_package_replay_order_executable_candidate_use_allowed = true`;
- `missed_package_replay_order_executable_candidate_use_allowed_reason = raw_selector_reject_open_reduced_order_executable_promotion_contract_passed`;
- runtime `risk_finalizer_package_cooldown_release_applied = false`;
- runtime release reason `cooldown_release_reason_not_allowed:same_symbol_daily_loss_lockout_after_closed_trade`.

## Root Mismatch

The risk finalizer already has a narrow signed-executable package daily-loss-lockout release, and the repaired profile enables it. But the finalizer computed `signed_executable_package_order_allowed` only from stale scheduler/package executable fields. It did not consume the predecision raw-selector open-reduced promotion contract that the missed ledger later recognizes as order executable.

This is a producer/consumer mismatch:
- producer/proof: raw-selector open-reduced order-executable promotion contract;
- missing consumer: risk finalizer cooldown-release authority;
- proof surface: `package_cooldown_release.raw_selector_open_reduced_promotion_contract_passed`.

## Patch Batch

Files changed:
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`

Patch type:
- Behavior-changing correctness repair in local replay risk-finalizer authority.
- It does not enable broad daily-loss-lockout release.
- It only lets the existing signed-executable package release consume a passed raw-selector promotion contract with no failures, while preserving signed authority validation, predecision quality floors, broker-cost/source gates, and live/final closure.

Focused proof already run:
- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py`
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k 'package_cooldown_release_uses_raw_selector_promotion_contract_for_signed_executable_daily_loss_lockout or package_cooldown_release_daily_loss_lockout_requires_explicit_flag or package_fill_floor_authority_daily_loss_release_is_narrow_replay_path or package_cooldown_release_allows_ordinary_same_symbol_churn_only' -q --tb=short`

## Expected Replay Effect

Expected improvement class:
- better risk-finalizer/cooldown release conversion, not broad blocking or hardcoded bucket suppression.

Expected measurable movement:
- candidate/scorecard transfer: neutral.
- order/trade transfer: should restore the two selected signed package candidates blocked solely by `recent_same_symbol_closed_trade_cooldown` if no other runtime guard blocks them.
- missed positive R: should fall by about `+0.96009913R` for the two identified rows if restored.
- missed negative R: may also change if other signed promotion rows meet the same causal contract.
- trade count/net R: expected to improve relative to V182 if restored rows are executable; exact headline depends on risk budget and lifecycle interactions.
- cost-refused/source-gap executions must remain `0 / 0`.

## Pass / Fail Criteria

Helped:
- the two V182 cooldown-blocked selected rows move to order/trade or receive a different exact runtime blocker;
- no broad daily-loss/package-quality release opens;
- `package_cooldown_release.raw_selector_open_reduced_promotion_contract_passed` appears on affected release rows;
- broker/live/final remain false.

Failed:
- the same rows stay blocked by stale cooldown release fields;
- REFUSED/source-gap rows execute;
- replay improves only by suppressing opportunity;
- another downstream leak is exposed, in which case keep the truth and patch that next root cause.

