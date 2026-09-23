# Pre-Replay Brief - 2026-07-04T14:18Z - V119C Passive Distance Queue Release

Scope: `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20`.

Broker/live/final remain closed. Local replay/package evaluation keeps full 82-sleeve authority.

## Latest Completed Run

`BROAD_LIVE_AS_IF_REPLAY_V119B_SCORECARD_REPORTED_AUTHORITY_BACKFILL_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`

- window: `2026-05-13..2026-05-17`
- scorecards: `288`
- order/trade rows: `4 / 1`
- trade net R: `-1.10389662`
- scorecard package authority true/false/selected-row top-level only: `158 / 128 / 2`
- scorecard order-executable true/false/selected-row top-level only: `95 / 191 / 2`
- false order-exec terminal rows: `0`
- missed rows: `2767`
- missed +R / -R / net: `224.65585079 / -1851.47117197 / -1626.81532118`

Main valid-probe transfer leaks by scorecard status:

- `risk_finalizer_synthesized_all_candidate_probe_diagnostic_only`: `105`, expected-net approx `+76.46801409R`
- `scheduler_option_runtime_ineligible`: `63`, expected-net approx `+72.851914R`
- `pre_order_materialization_preflight_blocked:passive_limit_fallback_envelope_unmet:passive_limit_fallback_envelope_distance_to_limit_risk_above_thesis_geometry_ceiling`: `58`, expected-net approx `+65.26179879R`
- `package_marketable_limit_entry_guard_blocked`: `20`, expected-net approx `+21.56396312R`
- `same_symbol_daily_loss_lockout_after_closed_trade`: `13`, expected-net approx `+15.6140103R`

## Patch Being Proven

File:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`

Change:

- `passive_limit_fallback_envelope_distance_to_limit_risk_above_thesis_geometry_ceiling` is now treated as a guarded-fallback-only unusability reason when passive queue route authority exists. It degrades to passive limit queue instead of hard-blocking order materialization.
- The same path still blocks refused broker-cost rows and true quality failures such as probability below floor.

Tests:

- `test_finalizer_preflight_degrades_distance_breach_to_passive_limit_queue`
- `test_finalizer_preflight_still_blocks_passive_limit_queue_on_fallback_envelope_quality_failure`
- `test_finalizer_preflight_refused_broker_cost_blocks_degraded_passive_queue_release`

Focused compile/tests passed before replay.

## Expected Effect

- Scorecard-to-order transfer should increase from the V119B `4` order rows if the 58 distance-blocked valid probes are otherwise executable.
- Those rows may become pending, expired, or filled. Any non-fill must carry explicit lifecycle/fillability reason.
- Trade R may get worse if newly expressed passive orders fill and lose; that is acceptable if the executable truth is more correct.
- Broker-cost REFUSED/source-gap/false order-executable terminal executions must remain `0`.

## Success / Failure Criteria

V119C helped if distance-blocked scorecard rows are no longer hard-rejected by pre-order materialization and convert to order/lifecycle artifacts or a deeper exact blocker.

V119C failed if distance-blocked rows remain under the same pre-order block reason, or if refused/source-gap/false-order-exec rows execute.

If V119C releases orders but still loses, next patch comes from the new largest V119C bucket: lifecycle expiry/fillability, scheduler runtime-ineligible, diagnostic-only exact-option gaps, same-symbol lockout, or exit/stop geometry.
