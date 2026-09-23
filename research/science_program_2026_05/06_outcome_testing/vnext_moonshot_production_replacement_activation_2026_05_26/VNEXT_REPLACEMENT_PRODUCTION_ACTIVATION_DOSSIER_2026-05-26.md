# vNext Replacement Production Activation Dossier - 2026-05-26

Generated: `2026-05-26T14:59:45Z`

## Activation Verdict At Stage 11

Stage 11 does not apply the production overlay. It writes the exact demo-shadow overlay, the semantic-gated production overlay candidate, the rollback overlay, and the monitoring/operation package. Application is blocked until Stage 12 passes the semantic verifier and proves that the production overlay changes behavior without reactivating the negative current default source-bound primary slice.

The blocking fixture is explicit: `activated_default_source_bound_primary` has expectancy `-0.455542R`, total `-7197.108135R`, and selected `15799` rows. That overlay must not be applied as production truth.

## What Replaces Old GTOS

- Old exit behavior replaced: `live_current_j46_j49` and fixed `1.5R` comparator behavior stop being the target production exit path when the gated overlay is applied.
- vNext replacement behavior: `moonshot_fvg_be_after_trigger_prop_aware_router` using `be_after_trigger` on the source-bound `origin_current_fvg_fill` / `fvg_fill` stream.
- Prop behavior: `ACCOUNT_ABANDON_OR_RESTART` remains the default prop policy reference. It allows when cushions are sufficient, reduces or defers near daily/overall limits, and treats abandon/restart as an owner-gated account-attempt decision rather than an automatic broker action.
- AI behavior: mechanical routing is primary. The Stage09 AI package remains budget-capped and unspent; AI-dependent surfaces stay disabled until a route-state budget cap exists.
- ML behavior: Stage10 ML roles are monitoring only. `replacement_ml_apply_to_execution` must remain false.

## Evidence Metrics

| Scenario | Selected/performance rows | Total R | Expectancy R | Win rate | Profit factor |
|---|---:|---:|---:|---:|---:|
| Old GTOS live-current J46/J49 | 214536 | 38663.272287 | 0.180218 | 0.279715 | 1.299799 |
| Moonshot BE-after-trigger | 214536 | 83555.679219 | 0.389472 | 0.471525 | 2.286987 |
| Condition-router challenger | 214536 | 89405.920792 | 0.416741 | 0.505542 | 2.161894 |
| Blocked current default source-bound primary | 15799 | -7197.108135 | -0.455542 | 0.057472 | 0.157559 |

Upstream best stream: `origin_current_fvg_fill` with `be_after_trigger` and `ACCOUNT_ABANDON_OR_RESTART` allowed `49002` trades, total `28610.598206`R, expectancy `0.583866`R, pass-proxy `0.981666`, and expected payout proxy `$7842.540`.

Condition challenger status: `condition_router_beats_global_row_expectancy_but_is_rejected_as_primary_prop_default_from_local_prop_replay`. It improves row expectancy, but Stage11 keeps BE-after-trigger as the prop-pass default because the prop replay retained better pass efficiency and accepted-trade count.

## Config Overlays

- Current shadow base: `gtos_vnext_runtime.apply_to_execution=false`, dynamic router disabled, LTF/prop execution-effect flags disabled, monitoring enabled.
- Demo shadow overlay: enables the moonshot dynamic router for logging while keeping global and dynamic `apply_to_execution=false`.
- Semantic-gated production overlay candidate: enables global vNext apply, pre-AI mechanical apply, LTF execution apply, prop selector apply, and moonshot dynamic execution apply, while keeping paid-AI execution and ML execution disabled.
- Rollback overlay: restores current shadow/default-off execution flags while retaining monitoring.

Exact YAML: `VNEXT_REPLACEMENT_CONFIG_OVERLAY_DIFF_2026-05-26.yaml`.

## Market And Source Activation

| Symbol | Activation status | Source class | Candidate rows | Complete source ratio |
|---|---|---|---:|---:|
| AUDJPY | forward_capture_required_before_execution_activation | broker_native_redacted_account_contract_verified | 1261 | 0.592 |
| AUDUSD | forward_capture_required_before_execution_activation | broker_native_redacted_account_contract_verified | 1252 | 0.579 |
| BTCUSD | forward_capture_required_before_execution_activation | broker_native_redacted_account_contract_verified | 4003 | 0.943 |
| CHFJPY | forward_capture_required_before_execution_activation | broker_native_redacted_account_contract_verified | 1254 | 0.606 |
| ETHUSD | forward_capture_required_before_execution_activation | broker_native_redacted_account_contract_verified | 3318 | 0.951 |
| EURGBP | forward_capture_required_before_execution_activation | broker_native_redacted_account_contract_verified | 1173 | 0.581 |
| EURJPY | forward_capture_required_before_execution_activation | broker_native_redacted_account_contract_verified | 1230 | 0.589 |
| EURUSD | forward_capture_required_before_execution_activation | broker_native_redacted_account_contract_verified | 3999 | 0.613 |
| GBPJPY | forward_capture_required_before_execution_activation | broker_native_redacted_account_contract_verified | 34838 | 0.588 |
| GBPUSD | forward_capture_required_before_execution_activation | broker_native_redacted_account_contract_verified | 33592 | 0.594 |
| GER40 | excluded_broker_unavailable | broker_unavailable | 4667 | 0.559 |
| JP225 | forward_capture_required_before_execution_activation | broker_native_redacted_account_contract_verified | 2811 | 0.597 |
| NAS100 | forward_capture_required_before_execution_activation | broker_native_redacted_account_contract_verified | 25659 | 0.587 |
| NZDUSD | forward_capture_required_before_execution_activation | broker_native_redacted_account_contract_verified | 2505 | 0.597 |
| SPX500 | forward_capture_required_before_execution_activation | broker_native_redacted_account_contract_verified | 2020 | 0.587 |
| UK100 | forward_capture_required_before_execution_activation | broker_native_redacted_account_contract_verified | 4405 | 0.569 |
| UKOIL_cash | excluded_broker_unavailable | broker_unavailable | 1142 | 0.616 |
| US30_cash | forward_capture_required_before_execution_activation | broker_native_redacted_account_contract_verified | 27854 | 0.587 |
| USDCAD | forward_capture_required_before_execution_activation | broker_native_redacted_account_contract_verified | 1044 | 0.585 |
| USDCHF | forward_capture_required_before_execution_activation | broker_native_redacted_account_contract_verified | 1262 | 0.584 |
| USDJPY | forward_capture_required_before_execution_activation | broker_native_redacted_account_contract_verified | 35716 | 0.596 |
| USOIL_cash | excluded_broker_unavailable | broker_unavailable | 1013 | 0.616 |
| XAGUSD | forward_capture_required_before_execution_activation | broker_native_redacted_account_contract_verified | 27242 | 0.589 |
| XAUUSD | forward_capture_required_before_execution_activation | broker_native_redacted_account_contract_verified | 29974 | 0.587 |

Broker-native eligible symbols are `AUDJPY, AUDUSD, BTCUSD, CHFJPY, ETHUSD, EURGBP, EURJPY, EURUSD, GBPJPY, GBPUSD, JP225, NAS100, NZDUSD, SPX500, UK100, US30_cash, USDCAD, USDCHF, USDJPY, XAGUSD, XAUUSD` from the route onboarding verifier, not from the stale legacy deployment list. Pending-not-excluded replay symbols are `-`. Exact broker exclusions are `GER40, UKOIL_cash, USOIL_cash`. Historical-only, source-missing, and Sierra/SCID context do not prove redacted_account lacks a market; Sierra remains context-only and broker-native MT5 availability decides live eligibility.

## Monitoring And Stop Rules

Monitoring log: `shadow_logs/gtos_vnext_replacement_monitoring.jsonl`.

Required monitoring surfaces: vnext_apply_status, router_decisions, label_effects, avoid_mixed_legacy_distribution_and_execution_effect, dynamic_exit_transitions, ltf_pending_monitor_health, prop_budget_projection, source_capture_completeness, old_live_fallback_leakage, malformed_ai_responses.

Immediate block or rollback conditions:

- Stage12 semantic verifier does not pass.
- Any applied execution row has `old_live_fallback_leakage.detected=true`.
- Any applied execution row has missing source, incomplete source window, or same-bar ambiguity without ordered LTF/tick proof.
- Dynamic overlay applies while selected policy is not `be_after_trigger` or replacement target is not `live_current_j46_j49`.
- `replacement_ml_apply_to_execution=true`.
- Paid AI is invoked while route-state budget cap remains null.
- Prop projection emits `ACCOUNT_ABANDON_OR_RESTART` without owner account-attempt approval.
- Any emergency stop in `.context/00_core/quick_reference_card.md` fires.

## Commands

- `python -m py_compile src\components\gtos_vnext_runtime.py src\components\orchestrator.py src\components\execution.py tests\test_gtos_vnext_runtime.py tests\test_j46_j49_policy.py tests\test_limit_order_flow.py`
- `python -m pytest tests\test_gtos_vnext_runtime.py::test_vnext_replacement_monitoring_snapshot_records_stage10_surfaces tests\test_gtos_vnext_runtime.py::test_vnext_replacement_monitoring_flags_old_live_fallback_leakage tests\test_gtos_vnext_runtime.py::test_agent_config_wires_vnext_runtime_shadow_execution_path -q`
- `python research\science_program_2026_05\06_outcome_testing\vnext_moonshot_production_replacement_activation_2026_05_26\verify_vnext_replacement_stage05_full_activated_replay.py`
- `python research\science_program_2026_05\06_outcome_testing\vnext_moonshot_production_replacement_activation_2026_05_26\verify_vnext_replacement_stage06_legacy_vs_vnext_delta.py`
- `python research\science_program_2026_05\06_outcome_testing\vnext_moonshot_production_replacement_activation_2026_05_26\verify_vnext_replacement_stage10_ml_monitoring_integration.py`
- `python research\science_program_2026_05\06_outcome_testing\vnext_moonshot_production_replacement_activation_2026_05_26\verify_vnext_replacement_stage11_activation_dossier.py`
- `python research\science_program_2026_05\06_outcome_testing\vnext_moonshot_production_replacement_activation_2026_05_26\verify_vnext_replacement_stage12_semantic_red_team.py`

## External Surface Handoff Fields

- Paid AI spend: blocked until `route_state_budget_cap_usd` is non-null; Stage09 package has 32 prompt rows and hard-cap request only.
- Broker/account/order/deal/position/history mutation: out of route. Owner must provide demo/live account, server, broker symbol aliases, start window, risk ceiling, and explicit runtime-start/order-mutation approval.
- Remote push: out of route and requires explicit owner approval.
- Credential changes: out of route.
- Destructive deletion and history rewrite: out of route.
