# Session CN — live broker-true commission result (wave 17, B2750–B2799)

Commission `SESSION_CN_LIVE_COST_TRUTH.md`; owner authority `OD_ALL_IN_20260801.md`.
Starting commit `83867e65f6abe317411cbef48bf44414acf28111`; branch
`phase17/live-cost-truth`.

**Boundary:** this session changed mainline source, tests, offline receipts and an unapplied
activation carry. It did not touch the VPS, execute a broker-capable script, change a token-bound
config byte, read a TEST outcome, or activate live behavior.

## 0. Findings first

1. **H-CD-2 reproduced on the exact armed-money call chain and is fixed in mainline.** The first
   permission screen obtains the tick and calls the broker-net gate at `permissions.py:455-467`,
   builds/stores the packet at `permissions.py:1082-1100`, and refuses it there. The order path
   obtains a second fresh tick at `execution.py:3241-3260`, rebuilds the packet from current entry,
   stop and symbol geometry at `execution.py:2011-2035` / `execution.py:3407-3413`, and returns
   before a broker request at `execution.py:3438-3444`. At the starting commit both screens summed
   spread + expected slippage + swap while merely checking a commission status string. Commission
   was structurally zero in `total_cost_r`.

2. **Broker-true round-turn commission is now the default fourth term; missing truth fails closed.**
   `broker_net_cost_engine.py:489-582` resolves the account/symbol schedule through CD's prepared
   adapter and converts USD/lot to R using the candidate stop plus current
   `trade_tick_value / trade_tick_size`. `:674-706` adds it to the total. Unknown account or symbol,
   absent schedule, invalid entry/stop, or missing tick conversion makes the total null and produces
   the explicit refusal at `:875-887`. Zero is accepted only when the captured schedule says zero.
   The old behavior has no config switch: it is reachable only through the named
   `legacy_status_only_zero_commission_comparator_v1` function argument.

3. **The TRAIN decision surface moves materially, but only on one account in the observed sample.**
   On 174 same-input decisions, 147 receive a non-zero commission charge. Old pass/refuse is
   **138/36**; new is **131/43**. Seven decisions flip and every flip is conservative
   (**PASSED → REFUSED**). All seven are redacted_account oil decisions: one `energy_agri`, six
   `sub_mid_dn_revert`. FTMO has 95 non-zero charges over 117 decisions and no observed flip.
   That is not a claim of FTMO neutrality: the charge changes its cost headroom and 16 refusal
   reasons.

4. **The projection is bounded and incomplete by declaration.** It uses 2023 only for warm-up and
   generates/evaluates entry decisions only in 2024 TRAIN. The reader stops before decoding the
   first post-TRAIN bar; it reads no exit, P&L or R-result field. Twenty-one source prefixes were
   available. Fourteen account/sleeve/symbol surface slots lack input bars and 17 otherwise generated
   candidates lack a symbol in the corresponding live profile. redacted_account `sub_xvol_pullback` has
   zero evaluated candidates and is **NOT MEASURED**, not neutral.

5. **Historical learning packets remain readable without being reinterpreted.** New packets declare
   model v3, four expected components and no cost exclusion. `book_owner.py:1126-1227` emits only
   scalar cost/provenance fields, avoiding the nested packet's forbidden raw keys. Historical v2
   packets infer the original three-component contract and `commission` exclusion. The reader in
   `packet_economics.py:357-419` resolves the contract per row; `:452-485` refuses model/realized
   commission comparability for incomplete v2 rows and permits it for complete v3 rows.

6. **The carry is built against the host lineage, not wished-current mainline bytes.** It has seven
   dependency-first payloads and applies the engine last as the economic boundary. The engine starts
   from VPS lineage `redacted_host`; packet economics starts from Session S's carried bytes; BookOwner
   starts from Session CE's carried bytes. The composed payload preserves the VPS-only live-symbol-info
   swap guard. The offline payload verifier proves exact hashes, imports, known-account schedules,
   old-PASS/new-REFUSED arithmetic, unknown-account closure and v2/v3 compatibility without importing
   `run_book.py` or constructing a broker.

7. **This intentionally breaks future R2 source identity, not frozen history.** The one changed R2
   member is `src/components/broker_net_cost_engine.py`, expected
   `eb4ec5173ce28d4b2f6631fbe2e912a1dc5e20d392cd2a2517627d2cc2ab40d0`, now
   `f599f25f17008667442f926805a3738914d44e03aa0e29b75a293fdcffeb36ed`. A forward sealed replay
   must regenerate its decision authority and rerun affected windows. CN did not rewrite R2 or any
   accepted replay artifact. The execution-seal file, sealed root and four shared per-arm execution
   digests remain byte-identical.

## 1. What changed

The default packet now computes:

```text
commission_r = round_turn_commission_usd_per_lot
               / (sl_distance * trade_tick_value / trade_tick_size)

total_cost_r = spread_r + expected_slippage_r + swap_cost_r + commission_r
```

The implementation is deliberately account-exact. The existing profile resolution selects FTMO or
redacted_account, the adapter resolves that account's broker symbol in `BROKER_TRUE_COSTS_V1.json`, and the
live execution caller supplies the fresh symbol specification. The permission-stage packet can still
fail closed when its reduced geometry is insufficient; the order-stage packet performs the final
screen from fresh executable geometry.

Changed production paths:

| path | role | R2 status |
|---|---|---|
| `src/components/broker_net_cost_engine.py` | default fourth term, provenance, failure closure, explicit comparator | bound; authorized break recorded |
| `src/components/ultimate_book/book_owner.py` | additive scalar v3 learning emission with v2 inference | unbound |
| `src/components/ultimate_book/packet_economics.py` | per-row v2/v3 modeled/realized comparability | unbound |
| `src/costs/__init__.py` | removes the now-stale claim that live still charges zero | unbound |

No config knob was introduced. No order path, launcher, supervisor or activation token was changed.

## 2. Same-input decision A/B

Receipt: `phase17/receipts/CN_LIVE_COST_DECISION_AB_V1.json`, SHA-256
`15ad7c7a633cdf55dc67a13979ab59850d9a6f555ce2d3d542d23c39ca33ddc4`.
The 174 normalized decision rows independently hash to
`2f01d4ec0d0b1367a9ddbe07e114c097ec1eb819b4ae6a51830fda398904955d`.

Method: run the exact live sleeve generators over FTMO broker-wall-clock bars converted to true UTC;
use 2023 as warm-up and admit 2024 TRAIN decision bars only; project each generated intent to both
armed accounts; price the same entry/stop geometry with each account's captured symbol specification,
p50 spread and commission schedule; call the old explicit comparator and new default on the identical
packet input. This is a fixed p50 entry-gate projection, not a future-tick forecast or trade-outcome
backtest.

### Account summary

| account | decisions | non-zero commission | old pass/refuse | new pass/refuse | flips | commission R median / max | refusal reason changes |
|---|---:|---:|---:|---:|---:|---:|---:|
| FTMO | 117 | 95 | 95 / 22 | 95 / 22 | 0 | 0.013271 / 0.049542 | 16 |
| redacted_account | 57 | 52 | 43 / 14 | 36 / 21 | 7 | 0.016358 / 0.085826 | 21 |
| **all** | **174** | **147** | **138 / 36** | **131 / 43** | **7** | **0.014620 / 0.085826** | **37** |

### Armed-sleeve summary

| account / sleeve | decisions | charged | old pass → new pass | flips | commission R median / max | status |
|---|---:|---:|---:|---:|---:|---|
| FTMO / `crypto` | 20 | 20 | 20 → 20 | 0 | 0.020668 / 0.039489 | measured |
| FTMO / `energy_agri` | 5 | 0 | 4 → 4 | 0 | 0 / 0 | measured schedule zero |
| FTMO / `mx_btcusd_d1_donchian_20_breakout` | 43 | 43 | 43 → 43 | 0 | 0.017408 / 0.024233 | measured |
| FTMO / `sub_mid_dn_revert` | 48 | 31 | 27 → 27 | 0 | 0.001894 / 0.049542 | measured; 16 reasons move |
| FTMO / `sub_xvol_pullback` | 1 | 1 | 1 → 1 | 0 | 0.001329 / 0.001329 | measured, n=1 |
| redacted_account / `crypto` | 15 | 15 | 15 → 15 | 0 | 0.014370 / 0.024241 | measured |
| redacted_account / `energy_agri` | 5 | 5 | 4 → 3 | 1 | 0.026567 / 0.060683 | measured |
| redacted_account / `sub_mid_dn_revert` | 37 | 32 | 24 → 18 | 6 | 0.016795 / 0.085826 | measured |
| redacted_account / `sub_xvol_pullback` | 0 | 0 | 0 → 0 | 0 | n/a | **NOT MEASURED** |

### Every decision flip

All costs below are R per candidate; every row is old `PASSED` → new `REFUSED` against the unchanged
0.15 R total-cost ceiling.

| account | sleeve | symbol → broker | decision UTC | side | stop distance | commission R | old total R | new total R |
|---|---|---|---|---|---:|---:|---:|---:|
| redacted_account | `energy_agri` | UKOIL_cash → UKOUSD | 2024-04-12 17:00 | SHORT | 0.823957 | 0.060683 | 0.147938 | 0.208621 |
| redacted_account | `sub_mid_dn_revert` | USOIL_cash → USOUSD | 2024-11-14 18:00 | LONG | 0.823214 | 0.060738 | 0.118496 | 0.179233 |
| redacted_account | `sub_mid_dn_revert` | USOIL_cash → USOUSD | 2024-11-18 14:00 | LONG | 0.817500 | 0.061162 | 0.119184 | 0.180346 |
| redacted_account | `sub_mid_dn_revert` | USOIL_cash → USOUSD | 2024-11-19 14:00 | LONG | 0.792643 | 0.063080 | 0.122294 | 0.185375 |
| redacted_account | `sub_mid_dn_revert` | USOIL_cash → USOUSD | 2024-11-19 18:00 | LONG | 0.763786 | 0.065463 | 0.126159 | 0.191623 |
| redacted_account | `sub_mid_dn_revert` | UKOIL_cash → UKOUSD | 2024-04-24 17:00 | LONG | 0.822500 | 0.060790 | 0.135974 | 0.196764 |
| redacted_account | `sub_mid_dn_revert` | UKOIL_cash → UKOUSD | 2024-11-14 18:00 | LONG | 0.794000 | 0.062972 | 0.140137 | 0.203109 |

There are zero new-PASS flips. The receipt also contains all 37 changed gate dispositions and the
closest surviving passes, not only the seven threshold crossings.

### Coverage boundary

- 21 bar prefixes decoded; seven absent H4 source files create 14 account-level surface-slot gaps.
- 17 generated candidates are excluded by actual account surface: DASHUSD 5, XAGAUD 4, XAGEUR 3,
  XAUAUD 4, XAUEUR 1.
- The input reader checks the timestamp and stops before OHLC decoding at the post-TRAIN boundary.
- `population.val_used`, `population.test_used` and `population.march_2026_outcomes_read` are false.

## 3. Packet contract and compatibility

Current v3 placed-trade learning rows carry:

```text
modelled_cost_model_version = vnext_selected_cell_pretrade_cost_model_v3
modelled_cost_components_expected = [spread_r, expected_slippage_r, swap_cost_r, commission_r]
modelled_cost_components.commission_r = <numeric>
modelled_commission_mode = broker_true_commission_default_v1
modelled_commission_cost_source_status = captured
modelled_commission_cost_artifact = BROKER_TRUE_COSTS_V1.json
modelled_cost_excludes = []
```

The emitter does not copy the nested profile/server/symbol-spec packet into the learning row. Old rows
without an explicit component declaration infer v2's three terms and `modelled_cost_excludes =
[commission]`; they remain readable, but are correctly marked incomparable when realized commission
was charged. This prevents a schema upgrade from rewriting historical absence as zero.

## 4. Carry package

Package: `phase17/activation_carry_live_cost_truth/`.

| order | destination | source basis | after SHA-256 prefix |
|---:|---|---|---|
| 1 | `src/costs/coverage.py` | new byte-identical dependency | `95dd8eb5b2b1` |
| 2 | `research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json` | exact truth artifact | `bde450876421` |
| 3 | `src/costs/model.py` | new byte-identical dependency | `b630b52f1a1f` |
| 4 | `src/costs/__init__.py` | new byte-identical dependency | `b7ee8c0b4dae` |
| 5 | `src/components/ultimate_book/packet_economics.py` | Session S host bytes + CN | `edda5f190213` |
| 6 | `src/components/ultimate_book/book_owner.py` | Session CE host bytes + CN | `69efc33e27e2` |
| 7 | `src/components/broker_net_cost_engine.py` | VPS lineage + CN, swap guard preserved | `82f61b57a413` |

`MANIFEST.json` owns full hashes, before-byte expectations, destination paths, composition rules,
stop conditions, proving fields and rollback. `build_carry.py --check` reproduces all 11 generated
files. `verify_carry.py --check payload` passes without a live import. CN did not apply this package.

## 5. Seal and config fence

Unchanged token-bound/read-only inputs:

| path | SHA-256 |
|---|---|
| `config/agent_config.yaml` | `175f6b3bc1a692a5c5add776845281ee92fad71e11074e0a3f38d72a619eff7d` |
| `config/profiles/operator_profile.yaml` | `ae9312e6c5c8e6b05f8e5eb5f9490166c44a1a3279b4eff5df10c3da2921e2b8` |
| `config/profiles/redacted_account.yaml` | `b856f0ee7f13c59dd407949c6937275da57c3e797ab2bae256755560bbd21305` |

Frozen history remains:

| artifact | digest |
|---|---|
| execution-seal file | `ff15505034e738e8b4e4cb09ab3e0e3f9d399c955974caa2e8fdffd893def340` |
| execution-seal root | `889686760fc89917dd945bdaa09b32f566ba6f632fc0d26cc5a7d6da70331eb2` |
| S0R0 shared contract | `76c1527a3ce48ea0c6fa607e6af0a34717df4a625aed19dbb66c92510a61d7c6` |
| S0R1 shared contract | `398f21bd8e1a3661bc4b7e4c7c49980670ce80805a67e3b63b76a0208886d2df` |
| S1R0 shared contract | `d4a0879c187b44d386dd457d35f83382e6eca44d258de3cdef6195b474d7ddc9` |
| S1R1 shared contract | `ab4489a899d80f5793ef951570de51ad56dc864d4865280998e477a98999888e` |

The final raw R2 worktree check reports one additional byte mismatch at
`ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl`: R2 expects
`19365f603bc06eb0354406e0f584a33900c85c29493c625c09fe4fee9d2998fa`, the SHA-256 of its
131-byte LFS pointer, while the hydrated payload is
`a5bcc0f81941a123d75f390e2cd7abca625de584033aad8e34d3e7898588b54e`, exactly the pointer's
declared LFS object OID. `git status` records no change for that path. This is checkout
materialization, not a second CN source edit, but a forward R2 run must still resolve its byte contract
deliberately instead of treating the raw drift check as green.

## 6. Verification

- Initial focused behavior fence: **59 passed** before CN; **62 passed** after the source repair.
- Expanded source/measurement/carry fence: **40 passed, 0 bad**.
- The first mechanically scoped capture exposed 25 bad tests. Fourteen were worktree materialization
  failures (three sparse evidence paths plus two LFS payloads across the affected tests; some tests
  shared the same missing artifact). Eleven were stale production fixtures: five execution and six
  broader-origin tests declared the live vnext path without naming an account whose commission could
  be charged. After exact hydration and fixture repair, the formerly failing six-file surface is
  **224 passed, 6 skipped, 0 bad**; no production or config byte changed in that repair.
- Materializing the candidate-boundary route made one previously skipped independent verifier runnable;
  it named a sixth sparse dependency, the normalized-slice receipt. After materializing that exact
  tracked route, the final 109-file capture is **4,100 passed, 19 skipped, 11 xfailed, 0 bad**.
- Receipt reproducibility: `PASS ... rows=174 flips=7`.
- Carry reproducibility: `PASS carry package reproducible: 11 files`.
- Payload verifier: all hashes/syntax/truth checks pass; behavior probe proves commission
  `0.0625 R`, old `PASSED`, new `REFUSED`, unknown account `REFUSED`, v2 readable and v3 comparable.
- `git diff --check`: pass after marking embedded unified-diff context syntax appropriately.

One repository-wide check outside the tool-selected CN closure is red at both CN's base and final
tree: `tests/scripts/test_ab_receipts_are_self_contained.py` reports the pre-existing
`receipts/WAVE16A_TRAIN_AB.md` prose receipt because it lacks an embedded tool fence. The offending
file and scanner already coexist at commission base `83867e65f`; CN's receipt is not an offender, and
its embedded fence is byte-identical to the standalone tool output. CN leaves that wave-train-owned
artifact to its owner rather than folding an unrelated historical receipt rewrite into the live-cost
carry.

The final tool-emitted failset fence is embedded below after the committed closure capture.

### Tool-emitted failure-set fence

**0 bad → 0 bad; 0 fixed; 0 regressed.** Before is the committed 12,600-pass whole-suite
ZERO baseline; after is 4,100 passed on the exact 109-file CN closure.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/"
 ],
 "before": {
  "commit": "6608eb969297ed8cbe218662f3987344a576bc6c",
  "commit_subject": "Merge Session CI: the vp time-depth blockade is solved; the comparability gate honestly refuses",
  "captured_utc": "2026-07-31T17:26:48Z",
  "dirty": true,
  "totals": {
   "passed": 12600,
   "skipped": 120,
   "xfailed": 32
  }
 },
 "after": {
  "commit": "b5a76fed499592ff90404380ceb5bd29cf66d5d8",
  "commit_subject": "test: model broker identity in live cost fixtures",
  "captured_utc": "2026-07-31T19:04:15Z",
  "dirty": true,
  "totals": {
   "passed": 4100,
   "skipped": 19,
   "xfailed": 11
  }
 },
 "bad_before": 0,
 "bad_after": 0,
 "unchanged": 0,
 "fixed": [],
 "regressed": [],
 "bad_before_nodeids": [],
 "bad_after_nodeids": [],
 "scope_difference": {
  "before": [
   "tests/"
  ],
  "after": [
   "tests/costs/test_cost_artifact_absence_message.py",
   "tests/replay/test_decision_invariance.py",
   "tests/research_infra/test_cn_live_cost_carry.py",
   "tests/research_infra/test_cn_live_cost_truth.py",
   "tests/research_infra/test_fast_engine_accel.py",
   "tests/research_infra/test_fast_engine_sealed_inputs.py",
   "tests/research_infra/test_train_engine_lane.py",
   "tests/safety/test_activation_token.py",
   "tests/test_ai_call_policy.py",
   "tests/test_ai_supervisor.py",
   "tests/test_autocorrelation_risk.py",
   "tests/test_b7_5_neutral_selection_factorial.py",
   "tests/test_b7_5_selection_sizing_factorial_runtime.py",
   "tests/test_broad_replay_repair_config.py",
   "tests/test_broker_net_cost_engine.py",
   "tests/test_broker_profile_namespace.py",
   "tests/test_bugfixes_0.py",
   "tests/test_build_source_bound_execution_parity.py",
   "tests/test_concurrent_cap.py",
   "tests/test_cross_instrument_correlation_gate.py",
   "tests/test_daily_loss_stop.py",
   "tests/test_deployment_prep.py",
   "tests/test_divergence_matrix.py",
   "tests/test_dual_broker_execution_follower.py",
   "tests/test_equity_guard.py",
   "tests/test_execution.py",
   "tests/test_execution_manager_v4.py",
   "tests/test_execution_volume_normalization.py",
   "tests/test_exit_wiring.py",
   "tests/test_exit_wiring_short_r.py",
   "tests/test_gbpusd_context_strip.py",
   "tests/test_gtos_vnext_runtime.py",
   "tests/test_implementation_state_block_citations.py",
   "tests/test_integration_live.py",
   "tests/test_j46_j49_policy.py",
   "tests/test_limit_order_flow.py",
   "tests/test_live_config_truth.py",
   "tests/test_m5_refinement.py",
   "tests/test_market_whiteboard_v2.py",
   "tests/test_mfe_mae_m5.py",
   "tests/test_opus5_architecture_audit_hardening.py",
   "tests/test_orchestrator.py",
   "tests/test_pending_limit_lifecycle_logger.py",
   "tests/test_permissions.py",
   "tests/test_prelaunch_audit.py",
   "tests/test_probability_debate_v4.py",
   "tests/test_replay_acceleration_attempt5_typed_sparse_runner.py",
   "tests/test_replay_acceleration_campaign_exact_cache.py",
   "tests/test_replay_acceleration_candidate_boundary.py",
   "tests/test_replay_acceleration_integrated_source.py",
   "tests/test_replay_acceleration_isolated_reducers.py",
   "tests/test_replay_acceleration_progressive_benchmark.py",
   "tests/test_replay_acceleration_resume.py",
   "tests/test_replay_acceleration_source_batch.py",
   "tests/test_replay_acceleration_task6_prepared_pack_acceptance.py",
   "tests/test_replay_acceleration_task7_isolated_runner.py",
   "tests/test_replay_acceleration_task8_profile_runner.py",
   "tests/test_replay_acceleration_task9_final_validation.py",
   "tests/test_replay_columnar_source.py",
   "tests/test_replay_prepared_day_pack.py",
   "tests/test_replay_prepared_day_pack_integration.py",
   "tests/test_replay_semantic_parity.py",
   "tests/test_runtime_control_atomic_halt.py",
   "tests/test_same_symbol_lifecycle_v4.py",
   "tests/test_shadow_data_collection.py",
   "tests/test_side_aware_sizing.py",
   "tests/test_simulation_fixes.py",
   "tests/test_sizing_profile_overlay_and_currency.py",
   "tests/test_skip_ny_open.py",
   "tests/test_slippage_shadow_logger.py",
   "tests/test_sprt_class_halt_runtime.py",
   "tests/test_structural_c_gate.py",
   "tests/test_t7_deployment.py",
   "tests/test_time_in_trade_shadow_logger.py",
   "tests/test_timewarp_order_fillability_policy.py",
   "tests/test_timewarp_profit_harvest_policy.py",
   "tests/test_timewarp_scheduler_materialization.py",
   "tests/test_timewarp_trade_params_live_shape.py",
   "tests/test_touch_count_shadow_logger.py",
   "tests/test_trade_capture.py",
   "tests/test_trade_management_cascade_fix.py",
   "tests/test_trailing_stop_shadow_logger.py",
   "tests/test_v4_kia_parity_tick_first_runtime_repair.py",
   "tests/test_v4_know_it_all_live_replay_runtime.py",
   "tests/test_v4_timewarp_simulated_live_research_loop.py",
   "tests/test_verification.py",
   "tests/test_vnext_broader_origin_orchestrator.py",
   "tests/test_vnext_lane05_portfolio_scheduler.py",
   "tests/ultimate_book/test_activation_carry_vps_lineage.py",
   "tests/ultimate_book/test_az_activation_carry_mx.py",
   "tests/ultimate_book/test_ba_weekend_policy.py",
   "tests/ultimate_book/test_book_owner.py",
   "tests/ultimate_book/test_book_sleeve_telemetry.py",
   "tests/ultimate_book/test_breach_flatten.py",
   "tests/ultimate_book/test_ce_entry_hour_lever.py",
   "tests/ultimate_book/test_frontier_exit_contracts.py",
   "tests/ultimate_book/test_market_expansion_runtime_generator.py",
   "tests/ultimate_book/test_order_route.py",
   "tests/ultimate_book/test_packet_carry_vps_lineage.py",
   "tests/ultimate_book/test_packet_emit_on_change.py",
   "tests/ultimate_book/test_packet_emitter_hardening.py",
   "tests/ultimate_book/test_packet_modelled_cost.py",
   "tests/ultimate_book/test_packet_unit_join_key.py",
   "tests/ultimate_book/test_pre_gap_bar_wiring.py",
   "tests/ultimate_book/test_runtime_learning_packet.py",
   "tests/ultimate_book/test_symbol_rename_adoption_gap.py",
   "tests/ultimate_book/test_time_stop_rehydration.py",
   "tests/ultimate_book/test_time_stop_units.py",
   "tests/ultimate_book/test_time_stop_window_coverage.py"
  ],
  "justification": "Before is the committed whole-suite ZERO baseline: 12,600 passed and 0 bad at 6608eb969. After is the tool-derived 109-file import/path closure of the exact Session CN diff from commission base 83867e65f through committed fixture repair b5a76fed4: 4,100 passed and 0 bad. Because the before side has zero failures and zero collection errors suite-wide, any bad test in the after scope would be a regression. The after dirty flag contains only mandatory preflight-generated .context/LIVE_STATE.md and the untracked SCOPE/AFTER receipt artifacts; every CN source, test, result, measurement and carry byte under comparison was committed before capture. Sparse/LFS hydration changed no tracked byte."
 }
}
```

## 7. What I got wrong

1. **My first projection used the thin profile market map as if it were the live caller's symbol
   specification.** That manufactured missing swap geometry on redacted_account and made the initial result
   appear to have zero flips. The live caller supplies fresh `symbol_info`; switching the offline
   projection to the captured account-specific MT5 specification exposed the seven redacted_account oil
   refusals. The receipt test now pins the same-input oil flip.

2. **I initially counted missing generation inputs and excluded generated candidates in one bucket.**
   That would have called unknown surface slots "candidates" even though no generator output existed.
   The receipt now has separate units: 14 `surface_slot` gaps and 17 `candidate` gaps.

3. **My first carry shape assumed the mainline whole files were portable to the host.** They are not:
   BookOwner and packet economics already have carry-owned host bytes, while the engine retains a
   VPS-lineage-only swap-source guard. The delivered builder applies anchored CN edits to the latest
   known host bases and stops on any unrecognised hash or sibling collision.

4. **The generated nested unified diffs tripped the repository's whitespace fence.** Their required
   blank context marker is trailing whitespace when viewed as a file inside another git diff. The
   builder now removes that marker only on whitespace-only rows in the human audit view; exact copy
   bytes remain in `files/` and are hash-bound by the manifest.

5. **I miscounted the first failset classification before writing it down.** I initially described
   13 materialization failures and 12 fixture failures. The nodeid-level count is **14 and 11**.
   Hydration removed the 14 without a tracked diff; explicit broker identity/geometry repaired the
   11. The result records the exact corrected split.

6. **The second capture was still one test short of green because hydration changed what could run.**
   Once the candidate-boundary evidence existed, its independent verifier stopped skipping and exposed
   a missing normalized-slice receipt. I materialized that sixth tracked dependency and reran the full
   unchanged scope; the final after side is 4,100 passed and 0 bad.

7. **My first final R2 summary counted tracked edits, not every raw worktree mismatch.** The statement
   that CN changed one R2 member is true, but the hydrated sleeve registry also differs from R2's
   pointer-byte hash. It is now recorded separately as hydration-only and still a forward-replay
   preflight concern.

## 8. Ceremony handoff to the orchestrator

1. Resolve CL and CM first. If either changes `book_owner.py`, rebuild CN's two anchored additions on
   the resolved bytes; never use last-copy-wins. Re-run both laptop checks.
2. On the host, run manifest preflight and capture exact hashes for all existing/new destinations,
   the three config files and activation-token state. An unrecognised byte is a STOP.
3. Stop both workers through the established supervisor procedure and back up the three existing
   destinations outside the repo.
4. Copy the seven payloads in the manifest order above. The engine is last and is the economic
   activation boundary.
5. With workers still stopped, run `verify_carry.py --check all --repo-root <host-root>` and prove the
   three config hashes are unchanged.
6. Restart one namespace at a time through the existing supervisor ceremony. Require a fresh process
   start and normal management of pre-existing positions. Do not use a smoke order.
7. Wait for the first naturally occurring post-restart `unit_placed` packet from **each** namespace.
   It must carry v3, broker-true default mode, `captured`, the artifact name, numeric `commission_r`
   and total, and an empty exclusion list. Until then the honest state is
   `CARRIED_RESTARTED_PROVING_PACKET_PENDING`, not activated/proven.
8. On any hash, dependency, restart, config or proving failure, stop both workers, restore exact
   backups, remove only paths proven absent at preflight, run rollback verification, re-check configs,
   restart prior code, and preserve the failed evidence.

Separately, any future use of the parked R2 replay path must regenerate its decision contract and rerun
the affected windows. That is replay-authority work, not part of the live carry ceremony.
