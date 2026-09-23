# Session I — A/B by failure set

**Before:** `8ed443982`, the parent this branch was cut from.
**After:** `3e332cca2`, branch HEAD.
Tool: `scripts/pytest_failset.py capture` → `diff`, positional, **sets not counts**.
Raw artifacts: `receipts/session_i_ab/{before,after}.json`, `diff.txt`.

---

## 1. Result

```
before 8ed443982: 83 bad
after  3e332cca2: 74 bad
unchanged: 74   fixed: 9   REGRESSED: 0

No regressions.
```

**83 bad → 74 bad by failure set, 0 regressed, 9 fixed, +76 net new passing tests**
(1,006 → 1,082 passed).

The 9 fixed are not incidental — they are the point of §3.

## 2. Scope, stated plainly

This is a **scoped** A/B, not the whole suite, and the scope was chosen to contain every test
tree that consumes a file this session changed:

```
tests/safety  tests/ultimate_book  tests/test_execution.py  tests/test_mt5.py
tests/test_fn_smoke_trade.py  tests/test_heartbeat_monitor.py
tests/test_runtime_control_atomic_halt.py  tests/test_permissions.py
tests/test_run_book_importable.py  tests/test_run_book_account_identity.py
tests/test_dual_broker_execution_follower.py  tests/test_monitor_books_guard.py
tests/test_limit_order_flow.py  tests/test_trade_management_cascade_fix.py
tests/test_slippage_shadow_logger.py
```

1,156 tests per side, ~1 m 52 s per side.

Changed production files: `src/safety/activation_token.py`, `src/mt5/mt5_real.py`,
`src/mt5/mt5_interface.py`, `src/components/execution.py`,
`src/components/ultimate_book/launcher.py`, `run_book.py`, `.tools/monitor_books.py`,
`scripts/mt5_preflight.py`, `scripts/gtos_activation_token.py`, `scripts/fn_smoke_trade.py`
(comment only).

**The honest limit.** `execution.py` and `mt5_real.py` are widely imported, so a full-suite
run is the stronger claim and the working agreement asks for one. One full-suite `after`
capture did complete during this session — `652 failed / 33 errored / 10,277 passed` at
`2c8a0cc29` — but a matching `before` never did. Why is §4.

## 3. What the 9 fixed tests actually were

They were **failing for the wrong reason**, and that is a finding rather than a cleanup.

On any checkout that carries the runtime-halt flags — this worktree does, because
`pipeline_state/` was restored from the sparse profile — `enforce_runtime_not_halted`
resolves its flag paths against `Path.cwd()` when no `repo_root` is configured, found the
flags, tried to append its audit row into `pipeline_state/`, and hit `conftest`'s
production-write guard.

So these nine **errored on test infrastructure before reaching their assertions**:

| file | tests |
|---|---:|
| `tests/safety/test_raw_broker_script_guards.py` | 2 |
| `tests/test_fn_smoke_trade.py` | 7 |

Which means **the raw-broker guard and the raw-module smoke path had no live coverage at all
on a halted machine** — the guard covering `fn_smoke_trade.py` and
`dual_broker_execution_follower.py` was dark exactly when the system was in its safe state.
Fixed by isolating the halt root in those fixtures. The halt has its own tests; these are
about the token.

## 4. Three failed attempts at the full-suite A/B, and what each was

Recorded because the first one produced a confident wrong number and I nearly reported it.

**Attempt 1 — a false result.** The diff said `before: 0 bad / after: 685 bad /
REGRESSED: 685`. Artifact: the baseline exited 2 having executed **zero** tests
(`WARNING: no outcomes parsed`), so every failure in `after` looked new. **A capture log
reading `captured 0 failed / 0 errored (totals: {})` means the run is void, not clean** —
and a 685-regression diff built on it looks exactly like a catastrophe.

**Attempt 2 — killed mid-checkout.** I stopped it myself (it was running each suite twice),
and the stop landed between the two `git checkout`s, leaving the worktree **detached at the
parent commit**. Nothing was lost — every commit was on the branch, tree clean — but a later
reader would have found a worktree that looked like the session's work had vanished. Every
attempt after that runs under `trap … EXIT INT TERM` restoring the branch however the job
ends. **Any session doing an in-place checkout A/B should copy that trap.**

**Attempt 3 — a zsh trap, and a real one.** Two separate causes, and I initially misdiagnosed
the first as the second:

- **`zsh does not word-split unquoted parameter expansions.** `pytest … $SCOPE` passed the
  entire path list as **one** argument, so pytest collected nothing and exited in 0.5 s.
  That is what made the scoped runs look like the full-suite failures. Use `${=SCOPE}`, an
  array, or explicit arguments.
- **Memory.** Four wave-3 sessions ran full suites on this machine concurrently; `vm_stat`
  reported **108 MB free of 16 GB**. Full-suite captures were killed part-way, which produces
  no summary line and therefore an empty parse. The scoped runs above completed once
  contention dropped to one competitor.

`CLAUDE.md` H3 already records memory as a measured constraint here. Add to it: **a
full-suite A/B on this machine is not reliable while other sessions are running one**, and
the failure mode is silent — an empty capture, not an error.

## 5. Tests added

| file | tests | fail at `8ed443982`? |
|---|---:|---|
| `tests/safety/test_activation_never_strand.py` | 17 | 12 fail; the other 5 are invariant-A controls that must pass on both sides |
| `tests/safety/test_activation_token_attacks.py` | 22 | collection fails at the parent — the symbols do not exist there |
| `tests/safety/test_gate_tripwire.py` | 16 | all 16 |
| `tests/safety/test_activation_token_cli.py` | 5 | guards added this session |
| `tests/safety/test_mt5_preflight_no_mutation.py` | 6 | 5 fail; the 6th records the VPS lineage state |
| **total** | **66** | |

---

## Added at integration (Session O, 2026-07-27) — the machine-readable block

`tests/scripts/test_ab_receipts_are_self_contained.py` (Session M) makes it a suite-enforced rule
that a committed A/B receipt must **embed** the captures it was derived from. This receipt predates
that rule. The block below was generated by `scripts/pytest_failset.py receipt` from the two
capture JSONs already committed beside this file — **nothing was re-run and no number was retyped**;
the prose above and the block below are two renderings of the same two files. Everything above this
line is Session I's, unaltered.

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/safety",
  "tests/ultimate_book",
  "tests/test_execution.py",
  "tests/test_mt5.py",
  "tests/test_fn_smoke_trade.py",
  "tests/test_heartbeat_monitor.py",
  "tests/test_runtime_control_atomic_halt.py",
  "tests/test_permissions.py",
  "tests/test_run_book_importable.py",
  "tests/test_run_book_account_identity.py",
  "tests/test_dual_broker_execution_follower.py",
  "tests/test_monitor_books_guard.py",
  "tests/test_limit_order_flow.py",
  "tests/test_trade_management_cascade_fix.py",
  "tests/test_slippage_shadow_logger.py"
 ],
 "before": {
  "commit": "8ed4439824f7ccd1fd5ce249509b8a24f9ea5a9d",
  "commit_subject": "Cleanup: retire twelve merged worktrees; preserve the unique .hermes campaign evidence",
  "captured_utc": "2026-07-26T23:22:00Z",
  "dirty": false,
  "totals": {
   "failed": 83,
   "passed": 1006
  }
 },
 "after": {
  "commit": "3e332cca2ccbe3d511304b269e88d37fc708ffa0",
  "commit_subject": "Safety spine: behavioural tests for hole 3, the one deliverable that had none",
  "captured_utc": "2026-07-26T23:19:58Z",
  "dirty": false,
  "totals": {
   "failed": 74,
   "passed": 1082
  }
 },
 "bad_before": 83,
 "bad_after": 74,
 "unchanged": 74,
 "fixed": [
  "tests/safety/test_raw_broker_script_guards.py::test_the_raw_guard_allows_a_close_without_a_token",
  "tests/safety/test_raw_broker_script_guards.py::test_the_raw_guard_refuses_a_new_entry_without_a_token",
  "tests/test_fn_smoke_trade.py::test_run_symbol_does_not_report_closed_on_transient_positions_get_none",
  "tests/test_fn_smoke_trade.py::test_run_symbol_handles_entry_retcode_failure_gracefully",
  "tests/test_fn_smoke_trade.py::test_run_symbol_handles_order_send_returning_none",
  "tests/test_fn_smoke_trade.py::test_run_symbol_refuses_without_an_activation_token",
  "tests/test_fn_smoke_trade.py::test_run_symbol_reports_closed_with_real_pnl_on_success",
  "tests/test_fn_smoke_trade.py::test_run_symbol_reports_failed_to_close_when_position_persists",
  "tests/test_fn_smoke_trade.py::test_run_symbol_skips_telegram_on_failed_to_close"
 ],
 "regressed": [],
 "bad_before_nodeids": [
  "tests/safety/test_raw_broker_script_guards.py::test_the_raw_guard_allows_a_close_without_a_token",
  "tests/safety/test_raw_broker_script_guards.py::test_the_raw_guard_refuses_a_new_entry_without_a_token",
  "tests/test_dual_broker_execution_follower.py::test_follower_reprocess_failed_recent_intent_before_live_recovery_skip",
  "tests/test_dual_broker_execution_follower.py::test_ftmo_follower_profile_covers_live_symbols_and_broker_geometry",
  "tests/test_dual_broker_execution_follower.py::test_order_enabled_follower_allows_many_positions_when_drawdown_budget_allows",
  "tests/test_dual_broker_execution_follower.py::test_order_enabled_follower_consumes_retry_when_target_position_appears",
  "tests/test_dual_broker_execution_follower.py::test_order_enabled_follower_expires_old_market_intent_when_target_order_returns_none",
  "tests/test_dual_broker_execution_follower.py::test_order_enabled_follower_logs_pretrade_refusal_when_target_order_returns_none",
  "tests/test_dual_broker_execution_follower.py::test_order_enabled_follower_reduces_risk_when_daily_budget_is_tight",
  "tests/test_dual_broker_execution_follower.py::test_order_enabled_follower_retries_market_intent_when_target_order_returns_none",
  "tests/test_fn_smoke_trade.py::test_run_symbol_does_not_report_closed_on_transient_positions_get_none",
  "tests/test_fn_smoke_trade.py::test_run_symbol_handles_entry_retcode_failure_gracefully",
  "tests/test_fn_smoke_trade.py::test_run_symbol_handles_order_send_returning_none",
  "tests/test_fn_smoke_trade.py::test_run_symbol_refuses_without_an_activation_token",
  "tests/test_fn_smoke_trade.py::test_run_symbol_reports_closed_with_real_pnl_on_success",
  "tests/test_fn_smoke_trade.py::test_run_symbol_reports_failed_to_close_when_position_persists",
  "tests/test_fn_smoke_trade.py::test_run_symbol_skips_telegram_on_failed_to_close",
  "tests/test_heartbeat_monitor.py::TestFullTriggerPath::test_enabled_and_in_kz_triggers_flatten",
  "tests/test_heartbeat_monitor.py::TestMt5RetryBehavior::test_order_send_exception_treated_as_failure",
  "tests/test_heartbeat_monitor.py::TestMt5RetryBehavior::test_order_send_fails_retries_three_times",
  "tests/test_heartbeat_monitor.py::TestMt5RetryBehavior::test_order_send_returns_none_treated_as_failure",
  "tests/test_heartbeat_monitor.py::TestMt5RetryBehavior::test_order_send_succeeds_on_second_attempt",
  "tests/test_trade_management_cascade_fix.py::TestCascadeEndToEnd::test_full_cascade_position_remains_open_with_original_sl",
  "tests/ultimate_book/test_a8_live_activation_config.py::test_active_live_config_arms_a8_gate_with_smooth_ceiling_profile",
  "tests/ultimate_book/test_book_engine.py::test_engine_gates_on_produces_realized_units_for_crypto",
  "tests/ultimate_book/test_candidate_activation_readiness_artifacts.py::test_candidate_activation_readiness_artifact_boundary",
  "tests/ultimate_book/test_candidate_activation_readiness_artifacts.py::test_candidate_activation_readiness_preserves_repair_lanes",
  "tests/ultimate_book/test_candidate_bridge_spec_ltf_work_artifacts.py::test_candidate_bridge_route_closes_ltf_gap_without_mutation",
  "tests/ultimate_book/test_candidate_bridge_spec_ltf_work_artifacts.py::test_candidate_bridge_route_preserves_broker_specific_work_split",
  "tests/ultimate_book/test_candidate_enabled_replay_mc_artifacts.py::test_candidate_enabled_route_core_numbers_and_boundaries",
  "tests/ultimate_book/test_candidate_enabled_replay_mc_artifacts.py::test_candidate_enabled_route_ledgers_preserve_unfinished_and_ready_ideas",
  "tests/ultimate_book/test_candidate_full_book_live_activation_artifacts.py::test_full_candidate_book_live_activation_bridge_and_successor_lanes",
  "tests/ultimate_book/test_candidate_full_book_live_activation_artifacts.py::test_full_candidate_book_live_activation_result_and_numbers",
  "tests/ultimate_book/test_candidate_natgas_decomposition_artifacts.py::test_natgas_decomposition_preserves_ex_natgas_sleeve",
  "tests/ultimate_book/test_candidate_natgas_decomposition_artifacts.py::test_natgas_decomposition_writes_bridge_and_daily_artifacts",
  "tests/ultimate_book/test_candidate_subset_routing_dossier_artifacts.py::test_candidate_subset_routing_dossier_result_and_boundaries",
  "tests/ultimate_book/test_candidate_subset_routing_dossier_artifacts.py::test_candidate_subset_routing_ledger_preserves_full_book_work",
  "tests/ultimate_book/test_market_expansion_activation_candidate_package_artifacts.py::test_activation_candidate_package_counts_and_boundaries",
  "tests/ultimate_book/test_market_expansion_activation_candidate_package_artifacts.py::test_activation_candidate_package_row_controls_and_generator_contracts",
  "tests/ultimate_book/test_market_expansion_activation_readiness_synthesis_artifacts.py::test_activation_readiness_synthesis_authority_detail_preserved",
  "tests/ultimate_book/test_market_expansion_activation_readiness_synthesis_artifacts.py::test_activation_readiness_synthesis_boundary_and_counts",
  "tests/ultimate_book/test_market_expansion_broker_authority_probe_artifacts.py::test_broker_authority_probe_default_off_and_verifier_clean",
  "tests/ultimate_book/test_market_expansion_broker_authority_probe_artifacts.py::test_broker_authority_probe_readonly_evidence_counts",
  "tests/ultimate_book/test_market_expansion_commission_family_transfer_artifacts.py::test_commission_family_transfer_counts_and_no_schedule_overclaim",
  "tests/ultimate_book/test_market_expansion_commission_family_transfer_artifacts.py::test_commission_family_transfer_default_off_and_verifier_clean",
  "tests/ultimate_book/test_market_expansion_conditioned_sizing_refinement_artifacts.py::test_conditioned_sizing_boundary_and_counts",
  "tests/ultimate_book/test_market_expansion_conditioned_sizing_refinement_artifacts.py::test_conditioned_sizing_improves_but_remains_default_off",
  "tests/ultimate_book/test_market_expansion_data_availability_artifacts.py::test_market_expansion_gap_commands_and_inspire_not_kill_rows",
  "tests/ultimate_book/test_market_expansion_data_availability_artifacts.py::test_market_expansion_inventory_and_boundaries",
  "tests/ultimate_book/test_market_expansion_default_off_design_artifacts.py::test_default_off_design_denominator_and_boundaries",
  "tests/ultimate_book/test_market_expansion_default_off_design_artifacts.py::test_default_off_design_risk_budget_and_repair_gates",
  "tests/ultimate_book/test_market_expansion_default_off_registry_artifacts.py::test_default_off_registry_artifacts_match_design_ledger_fields",
  "tests/ultimate_book/test_market_expansion_default_off_registry_artifacts.py::test_default_off_registry_artifacts_preserve_design_and_boundaries",
  "tests/ultimate_book/test_market_expansion_fill_session_probe_artifacts.py::test_fill_session_probe_aggregate_fill_and_session_counts",
  "tests/ultimate_book/test_market_expansion_fill_session_probe_artifacts.py::test_fill_session_probe_default_off_and_verifier_clean",
  "tests/ultimate_book/test_market_expansion_followup_replay_artifacts.py::test_followup_replay_denominator_and_boundaries",
  "tests/ultimate_book/test_market_expansion_followup_replay_artifacts.py::test_followup_replay_path_evidence_and_interaction_ledgers",
  "tests/ultimate_book/test_market_expansion_g12_review_artifacts.py::test_g12_review_acceptance_gates_concentration_and_handoff",
  "tests/ultimate_book/test_market_expansion_g12_review_artifacts.py::test_g12_review_denominator_decisions_and_boundaries",
  "tests/ultimate_book/test_market_expansion_live_authority_dossier_artifacts.py::test_live_authority_dossier_cost_session_and_fill_statuses",
  "tests/ultimate_book/test_market_expansion_live_authority_dossier_artifacts.py::test_live_authority_dossier_counts_boundaries_and_replay",
  "tests/ultimate_book/test_market_expansion_observed_session_fillability_repair_artifacts.py::test_observed_session_fillability_boundary_and_counts",
  "tests/ultimate_book/test_market_expansion_observed_session_fillability_repair_artifacts.py::test_observed_session_fillability_proxy_preserves_gaps",
  "tests/ultimate_book/test_market_expansion_promotion_boundary_artifacts.py::test_promotion_boundary_default_off_not_promoted",
  "tests/ultimate_book/test_market_expansion_promotion_boundary_artifacts.py::test_promotion_boundary_pretrade_packets_and_bridge_limits",
  "tests/ultimate_book/test_market_expansion_proxy_m1_repair_artifacts.py::test_proxy_m1_repair_candidate_decisions_are_row_level",
  "tests/ultimate_book/test_market_expansion_proxy_m1_repair_artifacts.py::test_proxy_m1_repair_result_boundaries_and_counts",
  "tests/ultimate_book/test_market_expansion_repaired_registry_integration_artifacts.py::test_repaired_registry_integration_counts_and_boundaries",
  "tests/ultimate_book/test_market_expansion_repaired_registry_integration_artifacts.py::test_repaired_registry_integration_preserves_row_level_repair_decisions",
  "tests/ultimate_book/test_market_expansion_runtime_generator.py::test_active_market_expansion_bridge_telemetry_exposes_reload_parity_flags",
  "tests/ultimate_book/test_market_expansion_runtime_generator_implementation_artifacts.py::test_runtime_generator_implementation_counts_and_boundaries",
  "tests/ultimate_book/test_market_expansion_runtime_generator_implementation_artifacts.py::test_runtime_generator_implementation_event_parity_and_execution_packets",
  "tests/ultimate_book/test_market_expansion_swap_adjusted_activation_rescore_artifacts.py::test_swap_adjusted_activation_boundary_and_counts",
  "tests/ultimate_book/test_market_expansion_swap_adjusted_activation_rescore_artifacts.py::test_swap_adjusted_activation_positive_but_not_overstated",
  "tests/ultimate_book/test_market_expansion_swap_mode5_holding_repair_artifacts.py::test_swap_mode5_holding_boundary_counts_and_sources",
  "tests/ultimate_book/test_market_expansion_swap_mode5_holding_repair_artifacts.py::test_swap_mode5_holding_proxy_preserves_live_gaps",
  "tests/ultimate_book/test_market_expansion_validation_scoring_artifacts.py::test_market_expansion_scoring_denominator_and_boundaries",
  "tests/ultimate_book/test_market_expansion_validation_scoring_artifacts.py::test_market_expansion_scoring_ledgers_and_promotion_gates",
  "tests/ultimate_book/test_rolling_stress_manifest_shadow_boundary.py::test_foundation_boundary_is_shadow_only_and_raw_payloads_are_cold",
  "tests/ultimate_book/test_rolling_stress_manifest_shadow_boundary.py::test_rolling_stress_manifest_seals_canonical_inputs",
  "tests/ultimate_book/test_wave_c_manifest_ohlcv_source.py::test_wave_c_manifest_source_get_candles_streams_bounded_window",
  "tests/ultimate_book/test_wave_c_manifest_ohlcv_source.py::test_wave_c_manifest_source_get_candles_streams_tail_without_full_materialization",
  "tests/ultimate_book/test_wave_c_manifest_ohlcv_source.py::test_wave_c_manifest_source_indexes_all_timeframes_and_aliases"
 ],
 "bad_after_nodeids": [
  "tests/test_dual_broker_execution_follower.py::test_follower_reprocess_failed_recent_intent_before_live_recovery_skip",
  "tests/test_dual_broker_execution_follower.py::test_ftmo_follower_profile_covers_live_symbols_and_broker_geometry",
  "tests/test_dual_broker_execution_follower.py::test_order_enabled_follower_allows_many_positions_when_drawdown_budget_allows",
  "tests/test_dual_broker_execution_follower.py::test_order_enabled_follower_consumes_retry_when_target_position_appears",
  "tests/test_dual_broker_execution_follower.py::test_order_enabled_follower_expires_old_market_intent_when_target_order_returns_none",
  "tests/test_dual_broker_execution_follower.py::test_order_enabled_follower_logs_pretrade_refusal_when_target_order_returns_none",
  "tests/test_dual_broker_execution_follower.py::test_order_enabled_follower_reduces_risk_when_daily_budget_is_tight",
  "tests/test_dual_broker_execution_follower.py::test_order_enabled_follower_retries_market_intent_when_target_order_returns_none",
  "tests/test_heartbeat_monitor.py::TestFullTriggerPath::test_enabled_and_in_kz_triggers_flatten",
  "tests/test_heartbeat_monitor.py::TestMt5RetryBehavior::test_order_send_exception_treated_as_failure",
  "tests/test_heartbeat_monitor.py::TestMt5RetryBehavior::test_order_send_fails_retries_three_times",
  "tests/test_heartbeat_monitor.py::TestMt5RetryBehavior::test_order_send_returns_none_treated_as_failure",
  "tests/test_heartbeat_monitor.py::TestMt5RetryBehavior::test_order_send_succeeds_on_second_attempt",
  "tests/test_trade_management_cascade_fix.py::TestCascadeEndToEnd::test_full_cascade_position_remains_open_with_original_sl",
  "tests/ultimate_book/test_a8_live_activation_config.py::test_active_live_config_arms_a8_gate_with_smooth_ceiling_profile",
  "tests/ultimate_book/test_book_engine.py::test_engine_gates_on_produces_realized_units_for_crypto",
  "tests/ultimate_book/test_candidate_activation_readiness_artifacts.py::test_candidate_activation_readiness_artifact_boundary",
  "tests/ultimate_book/test_candidate_activation_readiness_artifacts.py::test_candidate_activation_readiness_preserves_repair_lanes",
  "tests/ultimate_book/test_candidate_bridge_spec_ltf_work_artifacts.py::test_candidate_bridge_route_closes_ltf_gap_without_mutation",
  "tests/ultimate_book/test_candidate_bridge_spec_ltf_work_artifacts.py::test_candidate_bridge_route_preserves_broker_specific_work_split",
  "tests/ultimate_book/test_candidate_enabled_replay_mc_artifacts.py::test_candidate_enabled_route_core_numbers_and_boundaries",
  "tests/ultimate_book/test_candidate_enabled_replay_mc_artifacts.py::test_candidate_enabled_route_ledgers_preserve_unfinished_and_ready_ideas",
  "tests/ultimate_book/test_candidate_full_book_live_activation_artifacts.py::test_full_candidate_book_live_activation_bridge_and_successor_lanes",
  "tests/ultimate_book/test_candidate_full_book_live_activation_artifacts.py::test_full_candidate_book_live_activation_result_and_numbers",
  "tests/ultimate_book/test_candidate_natgas_decomposition_artifacts.py::test_natgas_decomposition_preserves_ex_natgas_sleeve",
  "tests/ultimate_book/test_candidate_natgas_decomposition_artifacts.py::test_natgas_decomposition_writes_bridge_and_daily_artifacts",
  "tests/ultimate_book/test_candidate_subset_routing_dossier_artifacts.py::test_candidate_subset_routing_dossier_result_and_boundaries",
  "tests/ultimate_book/test_candidate_subset_routing_dossier_artifacts.py::test_candidate_subset_routing_ledger_preserves_full_book_work",
  "tests/ultimate_book/test_market_expansion_activation_candidate_package_artifacts.py::test_activation_candidate_package_counts_and_boundaries",
  "tests/ultimate_book/test_market_expansion_activation_candidate_package_artifacts.py::test_activation_candidate_package_row_controls_and_generator_contracts",
  "tests/ultimate_book/test_market_expansion_activation_readiness_synthesis_artifacts.py::test_activation_readiness_synthesis_authority_detail_preserved",
  "tests/ultimate_book/test_market_expansion_activation_readiness_synthesis_artifacts.py::test_activation_readiness_synthesis_boundary_and_counts",
  "tests/ultimate_book/test_market_expansion_broker_authority_probe_artifacts.py::test_broker_authority_probe_default_off_and_verifier_clean",
  "tests/ultimate_book/test_market_expansion_broker_authority_probe_artifacts.py::test_broker_authority_probe_readonly_evidence_counts",
  "tests/ultimate_book/test_market_expansion_commission_family_transfer_artifacts.py::test_commission_family_transfer_counts_and_no_schedule_overclaim",
  "tests/ultimate_book/test_market_expansion_commission_family_transfer_artifacts.py::test_commission_family_transfer_default_off_and_verifier_clean",
  "tests/ultimate_book/test_market_expansion_conditioned_sizing_refinement_artifacts.py::test_conditioned_sizing_boundary_and_counts",
  "tests/ultimate_book/test_market_expansion_conditioned_sizing_refinement_artifacts.py::test_conditioned_sizing_improves_but_remains_default_off",
  "tests/ultimate_book/test_market_expansion_data_availability_artifacts.py::test_market_expansion_gap_commands_and_inspire_not_kill_rows",
  "tests/ultimate_book/test_market_expansion_data_availability_artifacts.py::test_market_expansion_inventory_and_boundaries",
  "tests/ultimate_book/test_market_expansion_default_off_design_artifacts.py::test_default_off_design_denominator_and_boundaries",
  "tests/ultimate_book/test_market_expansion_default_off_design_artifacts.py::test_default_off_design_risk_budget_and_repair_gates",
  "tests/ultimate_book/test_market_expansion_default_off_registry_artifacts.py::test_default_off_registry_artifacts_match_design_ledger_fields",
  "tests/ultimate_book/test_market_expansion_default_off_registry_artifacts.py::test_default_off_registry_artifacts_preserve_design_and_boundaries",
  "tests/ultimate_book/test_market_expansion_fill_session_probe_artifacts.py::test_fill_session_probe_aggregate_fill_and_session_counts",
  "tests/ultimate_book/test_market_expansion_fill_session_probe_artifacts.py::test_fill_session_probe_default_off_and_verifier_clean",
  "tests/ultimate_book/test_market_expansion_followup_replay_artifacts.py::test_followup_replay_denominator_and_boundaries",
  "tests/ultimate_book/test_market_expansion_followup_replay_artifacts.py::test_followup_replay_path_evidence_and_interaction_ledgers",
  "tests/ultimate_book/test_market_expansion_g12_review_artifacts.py::test_g12_review_acceptance_gates_concentration_and_handoff",
  "tests/ultimate_book/test_market_expansion_g12_review_artifacts.py::test_g12_review_denominator_decisions_and_boundaries",
  "tests/ultimate_book/test_market_expansion_live_authority_dossier_artifacts.py::test_live_authority_dossier_cost_session_and_fill_statuses",
  "tests/ultimate_book/test_market_expansion_live_authority_dossier_artifacts.py::test_live_authority_dossier_counts_boundaries_and_replay",
  "tests/ultimate_book/test_market_expansion_observed_session_fillability_repair_artifacts.py::test_observed_session_fillability_boundary_and_counts",
  "tests/ultimate_book/test_market_expansion_observed_session_fillability_repair_artifacts.py::test_observed_session_fillability_proxy_preserves_gaps",
  "tests/ultimate_book/test_market_expansion_promotion_boundary_artifacts.py::test_promotion_boundary_default_off_not_promoted",
  "tests/ultimate_book/test_market_expansion_promotion_boundary_artifacts.py::test_promotion_boundary_pretrade_packets_and_bridge_limits",
  "tests/ultimate_book/test_market_expansion_proxy_m1_repair_artifacts.py::test_proxy_m1_repair_candidate_decisions_are_row_level",
  "tests/ultimate_book/test_market_expansion_proxy_m1_repair_artifacts.py::test_proxy_m1_repair_result_boundaries_and_counts",
  "tests/ultimate_book/test_market_expansion_repaired_registry_integration_artifacts.py::test_repaired_registry_integration_counts_and_boundaries",
  "tests/ultimate_book/test_market_expansion_repaired_registry_integration_artifacts.py::test_repaired_registry_integration_preserves_row_level_repair_decisions",
  "tests/ultimate_book/test_market_expansion_runtime_generator.py::test_active_market_expansion_bridge_telemetry_exposes_reload_parity_flags",
  "tests/ultimate_book/test_market_expansion_runtime_generator_implementation_artifacts.py::test_runtime_generator_implementation_counts_and_boundaries",
  "tests/ultimate_book/test_market_expansion_runtime_generator_implementation_artifacts.py::test_runtime_generator_implementation_event_parity_and_execution_packets",
  "tests/ultimate_book/test_market_expansion_swap_adjusted_activation_rescore_artifacts.py::test_swap_adjusted_activation_boundary_and_counts",
  "tests/ultimate_book/test_market_expansion_swap_adjusted_activation_rescore_artifacts.py::test_swap_adjusted_activation_positive_but_not_overstated",
  "tests/ultimate_book/test_market_expansion_swap_mode5_holding_repair_artifacts.py::test_swap_mode5_holding_boundary_counts_and_sources",
  "tests/ultimate_book/test_market_expansion_swap_mode5_holding_repair_artifacts.py::test_swap_mode5_holding_proxy_preserves_live_gaps",
  "tests/ultimate_book/test_market_expansion_validation_scoring_artifacts.py::test_market_expansion_scoring_denominator_and_boundaries",
  "tests/ultimate_book/test_market_expansion_validation_scoring_artifacts.py::test_market_expansion_scoring_ledgers_and_promotion_gates",
  "tests/ultimate_book/test_rolling_stress_manifest_shadow_boundary.py::test_foundation_boundary_is_shadow_only_and_raw_payloads_are_cold",
  "tests/ultimate_book/test_rolling_stress_manifest_shadow_boundary.py::test_rolling_stress_manifest_seals_canonical_inputs",
  "tests/ultimate_book/test_wave_c_manifest_ohlcv_source.py::test_wave_c_manifest_source_get_candles_streams_bounded_window",
  "tests/ultimate_book/test_wave_c_manifest_ohlcv_source.py::test_wave_c_manifest_source_get_candles_streams_tail_without_full_materialization",
  "tests/ultimate_book/test_wave_c_manifest_ohlcv_source.py::test_wave_c_manifest_source_indexes_all_timeframes_and_aliases"
 ]
}
```
