# vNext Production Candidate Repair Decision Dossier

Route: `vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25`
Created: `2026-05-25T15:38:24Z`
Final state: `replay_viable_pending_ai_source_validation`

## Verdict

The repaired candidate is replay-viable after repair, but it is not broker-activated by this route. Viable here means the repaired as-of replay clears the hard candidate gates, the failed 10-trade route is rejected, the prop governor is segmented by account attempts, and the remaining work crosses owner approval, paid-AI, source-capture, or broker-facing activation boundaries.

## Repaired Replay Metrics

- Candidate universe rows: `253,234`.
- Repaired executable-stream rows: `79,320`.
- Best prop policy: `ACCOUNT_ABANDON_OR_RESTART`.
- Selected rows after best prop policy: `22,270`.
- Performance rows with target/stop result: `21,727`.
- Selected-to-baseline ratio: `0.618903371036`.
- Total R: `2434.896089846658`.
- Risk-adjusted R: `2429.284061660785`.
- Expectancy R: `0.11206775394`.
- Win rate: `0.445022322456`.
- Profit factor: `1.202010371798`.
- Max drawdown pct: `18.964617401667`.
- Max loss streak: `20`.
- Prop pass rate: `0.497753818509`.
- Account loss/abandon rate: `0.501347708895`.
- Reference EV per attempt at fee 599 / payout 8000: `3681.72327` USD.
- Reference EV per terminal day at fee 599 / payout 8000: `2666.997295` USD.

## Runtime And System Behavior Changed

- Stage09 and Stage10 acceptance gates now reject the failed old route instead of allowing artifact-existence completion.
- Stage03 route semantics removed `LEGACY`, `MIXED`, off-KZ, and pre-AI mechanical-skip rows from prop-budget eligibility.
- Stage04/Stage08 prop governance uses segmented redacted_account account/challenge attempts instead of one continuous multi-year account path.
- Stage05 demoted harmful broad AVOID/pre-AI pressure from hard execution blocking where row-level replay showed positive recovered R.
- Stage06 changed LTF/M1 evidence from score-only into monitor/source-capture execution behavior where justified.
- Stage07 made no-paid AI replay diagnostic-only for redacted_account selected rows and requires a real AI validator for production selection.

## Code Config And Tests Changed

- Runtime helper changes were made in `src/components/gtos_vnext_runtime.py` for paid/no-paid AI policy classification.
- Failed-route Stage09/Stage10 builders and focused tests were repaired so the old catastrophic output fails viability.
- Repair-route Stage00 through Stage09 builders, verifiers, and focused tests were added under the route directory.
- `config/agent_config.yaml` was not staged or changed for activation in this route.
- Changed files since failed-route commit `75a85d244a2d832f32315c08266855e6e14c48c5`: `75` files.

## Research And Replay Intelligence Consumed

- Stage08 replay summary: `research/science_program_2026_05/06_outcome_testing/vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25/VNEXT_PRODUCTION_CANDIDATE_REPAIR_REPLAY_METRICS_SUMMARY_2026-05-25.json` sha `e1cdef3f645dc415c47256c6913d67a2ac0eeca3fe47ec0dbcde231b46dd37f7`.
- Stage08 decision ledger: `research/science_program_2026_05/06_outcome_testing/vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25/VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE08_REPAIRED_REPLAY_DECISION_LEDGER_2026-05-25.jsonl` sha `36e48a0ef8fcc403a00bcbd8ed46d27563b441724dca1301d3fd129f14ce621d`.
- Stage08 attempt ledger: `research/science_program_2026_05/06_outcome_testing/vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25/VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE08_REPAIRED_PROP_ATTEMPT_LEDGER_2026-05-25.jsonl` sha `3f1860b0a7f1e8ff4edb0584283f1c158f544fec2a14922efe2cf2ecd2eb15ae`.
- Layer ablation summary: `research/science_program_2026_05/06_outcome_testing/vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25/VNEXT_PRODUCTION_CANDIDATE_REPAIR_LAYER_ABLATION_SUMMARY_2026-05-25.json` sha `207630ace9c0b448016fab75fa9c6d5cd5c79a73ef9cbb804f2360faa25c8969`.
- Failed-route forensic report: `research/science_program_2026_05/06_outcome_testing/vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25/VNEXT_PRODUCTION_CHANGE_FORENSIC_ACCOUNTABILITY_REPORT_DO_NOT_ACTIVATE_2026-05-25.md` sha `8aee5781c5a2ab88aaee39d419d29cac6d2c3c8d323cf735617338af26216367`.

## Coverage

- Selected symbols: `{"EURUSD": 81, "GBPJPY": 4137, "GBPUSD": 1891, "NAS100": 2070, "US30_cash": 1282, "USDJPY": 7714, "XAGUSD": 2265, "XAUUSD": 2830}`.
- Selected sessions: `{"london": 13323, "ny": 2394, "tokyo": 6553}`.
- Selected sides: `{"LONG": 14935, "SHORT": 7335}`.
- Selected frameworks: `{"breaker_re_entry": 6127, "fvg_fill": 9079, "ob_retest": 7064}`.
- Selected source modes/timeframes: `{"LOCAL_TICK_PARQUET": 47, "MISSING_SOURCE": 457, "OHLC_M15_CSV": 44, "OHLC_M1_CSV": 21319, "OHLC_M5_CSV": 28, "SIERRA_SCID_CONVERTED_M1_PROXY": 375}`.
- Source status counts on repaired executable stream: `{"MISSING_SOURCE": 1935, "SIMULATED_FROM_LOCAL_OHLC": 76810, "SIMULATED_FROM_LOCAL_TICKS": 575}`.
- Off-KZ rows in candidate universe: `111762`.
- Off-KZ rows selected after repair: `0`.

## What Still Fails Or Remains Bounded

- The old production-change route still fails and remains invalidated; it is not an activation dossier.
- This route made zero paid API/vendor calls, so the 22,270 accepted rows still require approved AI-validation work before live activation.
- 457 accepted best-policy rows have `MISSING_SOURCE` source mode and must be source-captured or excluded before broker-facing activation.
- The best policy has a 0.501347708895 account-loss/abandon rate; it is economically positive only under the stated payout/fee/restart assumptions.
- No broker-facing activation, order, account, credential, remote, or config flip was made.

## Less Conservative Changes

- Stage05 recovered `42096` rows and `3929.02696473993` R by demoting broad AVOID/pre-AI pressure to context when it was harmful as a hard block.
- The prop governor stopped treating the full 2022-2026 replay as one doomed account and allowed segmented challenge restarts.

## Stricter Changes

- No-paid AI output cannot silently become a zero-trade production route.
- Generated `LEGACY` and `MIXED` rows cannot consume prop budget as production-selected rows.
- Old Stage09/Stage10 completion logic rejects negative/no-trade or near-no-trade candidates.

## Killed Demoted Redesigned Promoted

- Killed: the old `complete=true` activation conclusion for the failed route.
- Demoted: broad AVOID/pre-AI pressure that was net harmful as a hard block.
- Redesigned: prop governance from static continuous-account blocking to segmented EV account attempts.
- Promoted for replay candidate status: `ACCOUNT_ABANDON_OR_RESTART` as the best repaired prop policy.

## Expanded-Market Executability

Expanded-market intelligence is executable as a repaired replay policy for the source-covered selected rows across all eight symbols. Rows marked `MISSING_SOURCE` are preserved with source status and are not ready for broker-facing activation until captured or excluded.

## Default-Off And Activation Path

- Runtime/config activation remains off for broker-facing use in this route.
- Concrete next path before broker activation: owner-approved paid-AI validation, source-capture/exclusion handling, shadow/paper replay under current broker conditions, then a separate production-change activation dossier.

## AI And LTF Path

- AI calls required before prop governance: `79320`.
- AI calls required after best prop accept: `22270`.
- AI calls saved by prop block/defer: `57050`.
- Paid API/vendor calls made: `0`.
- LTF execution behavior changed rows: `72274`.
- Source-capture-required rows: `1935`.

## Layer Ablations

- `baseline_current_shadow`: `{"expectancy_r": 0.118432019538, "interpretation": "current baseline executable stream before vNext repair layers", "layer": "baseline_current_shadow", "selected_count": 35983, "total_r": 4008.331701256812}`.
- `stage03_repaired_executable_stream_no_prop`: `{"expectancy_r": 0.117327195147, "interpretation": "LEGACY/MIXED/off-KZ/pre-AI rows no longer consume prop budget", "layer": "stage03_repaired_executable_stream_no_prop", "selected_count": 37224, "total_r": 4111.26224513762}`.
- `stage05_avoid_pre_ai_demotion`: `{"delta_r_vs_stage03_vnext_no_prop": 3929.026964739895, "expectancy_r": 0.104771754471, "interpretation": "harmful broad AVOID/pre-AI pressure demoted to context", "layer": "stage05_avoid_pre_ai_demotion", "recovered_r": 3929.02696473993, "recovered_rows": 42096, "selected_count": 79320, "total_r": 8040.289209877515}`.
- `stage06_ltf_execution_monitor`: `{"execution_behavior_changed_rows": 72274, "interpretation": "LTF changes behavior via monitor/source-capture, not a hard skip", "layer": "stage06_ltf_execution_monitor", "selected_count": 79320, "source_capture_required_rows": 1935}`.
- `stage07_ai_policy_contract`: `{"ai_required_rows": 79320, "interpretation": "no-paid route is diagnostic only; production stream requires AI validation", "layer": "stage07_ai_policy_contract", "no_paid_selected_count": 0, "selected_count": 79320}`.
- `stage04_prop_on_pre_stage05_stream`: `{"account_loss_rate": 0.472527472527, "best_policy": "ACCOUNT_ABANDON_OR_RESTART", "interpretation": "old prop repair over Stage03-only stream, superseded by Stage08", "layer": "stage04_prop_on_pre_stage05_stream", "pass_rate": 0.526373626374, "reference_ev_per_terminal_day": 2342.416514, "selected_count": null}`.
- `stage08_prop_on_repaired_stage07_stream`: `{"account_loss_rate": 0.501347708895, "best_policy": "ACCOUNT_ABANDON_OR_RESTART", "interpretation": "segmented prop governor recomputed after Stage05-07 repairs", "layer": "stage08_prop_on_repaired_stage07_stream", "pass_rate": 0.497753818509, "reference_ev_per_terminal_day": 2666.997295, "risk_adjusted_r": 2429.284061660785, "selected_count": 22270}`.

## Exact Next Action Before Broker-Facing Activation

1. Freeze this repaired candidate as replay-viable but not broker-activated.
2. Prepare an owner-approved paid-AI validation/shadow plan for the 22,270 accepted rows or a preregistered stratified sample with cache rules.
3. Add/verify source-capture or exclusion behavior for accepted `MISSING_SOURCE` rows.
4. Run paper/shadow with live broker spread/latency and AI-supervisor telemetry.
5. Only then write a separate broker-facing production-change dossier for owner approval.

## Boundary Statement

No live trading, broker/account/order/history/deal/position mutation, paid API/vendor call, source deletion, remote push, credential change, or broker-facing activation flip was performed.

## Stage10 Post-Completion Hardening Addendum

Post-completion state: `replay_viable_pending_ai_source_validation`.

Stage08 replay facts remain frozen: best policy `ACCOUNT_ABANDON_OR_RESTART` selected
22,270 rows, total R 2,434.896089846658, expectancy 0.11206775394,
PF 1.202010371798, pass rate 0.497753818509, and account loss rate
0.501347708895. The repair route is replay-viable, but it is not
broker-facing activation-ready.

The unresolved production dependencies are now explicit:

- AI validation is not paid-vendor validated. Stage10 modeled 82 AI sensitivity rows from disk with zero paid API/vendor calls.
- Accepted `MISSING_SOURCE` rows remain unresolved: 457 accepted rows must be source-captured or excluded before activation.
- Push safety is blocked until large artifacts are packaged, chunked, migrated to LFS, or otherwise removed from normal Git history without data loss. Large-file blockers detected: 9.

Therefore the correct post-completion state is
`replay_viable_pending_ai_source_validation`. Artifact existence and verifier success are not substitutes for
paid AI/source validation or push-safe artifact handling.
