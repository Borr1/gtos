# Fable Execution Matrix - 2026-07-06

Status: active control surface before the next patch or replay, refreshed through V142 targeted behavior and the B7 missed-row synthesized executable authority demotion proof.

Plan source:
- `.context/context_os/fable_ultimate_plan/FABLE_ULTIMATE_SYSTEM_IMPLEMENTATION_SEQUENCE_20260705.md`
- `.context/context_os/fable_ultimate_plan/FABLE_ULTIMATE_SYSTEM_ROOT_CAUSE_AUDIT_20260705.md`

Current disk anchors:
- Current root map: `.context/context_os/CURRENT_ROOT_CAUSE_MAP.json`
- Current pre-replay brief: `.context/context_os/PRE_REPLAY_BRIEF_20260707T0141Z_V142_B7_MISSED_NAMESPACE_EXECUTABLE_AUTHORITY_DEMOTION.md`; V142 is the latest completed targeted B7 repair proof generated from the Fable matrix checkpoint, while V128 remains the latest completed full 24-symbol five-day B7 broad proof.
- Latest completed broad Fable proof prefix: `BROAD_LIVE_AS_IF_REPLAY_V128_B7_ROUTER_REFUSAL_DERIVED_IMMEDIATE_AUTHORITY_REPAIR_20260601_20260605_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH`
- Latest targeted Fable proof prefix: `BROAD_LIVE_AS_IF_REPLAY_V142_B7_MISSED_NAMESPACE_EXECUTABLE_AUTHORITY_DEMOTION_20260601_20260605_TARGETED`
- Active process state at latest matrix update: no broad replay, route builder, route verifier, flow analyzer, pytest, py_compile, harness, or subagent process running.
- Authority boundary: `broker_live_final=false`; local replay/package authority remains full.

Latest V142 targeted B7 repair update:
- Targeted proof prefix: `BROAD_LIVE_AS_IF_REPLAY_V142_B7_MISSED_NAMESPACE_EXECUTABLE_AUTHORITY_DEMOTION_20260601_20260605_TARGETED`; window `2026-06-01..2026-06-05`; symbols `XAUUSD XAGUSD USDCAD USDJPY UKOIL_cash`; profile `repaired_package_conversion_v3`.
- Behavior: `6633` candidates, `480` scorecard rows, `15` order rows, `3` filled trades, `6626` missed rows, `62` source rows, net `+0.84449709R`, gross/final `+1.09529478R`, cash PnL `+$211.19447407`, W/L/F `3/0/0`, all `3` fills open-reduced-risk.
- Clean authority checks from summary/parsing/verifier: zero executed broker-cost REFUSED rows, zero executed source-gap rows, broker/live/final false, route verifier `ok=true`, `issue_count=0`, verified `2026-07-07T03:03:08Z`.
- V142 is behavior-neutral versus V141 and closes the remaining same-root proof leak: `2727` terminal-veto missed rows now have `0` true effective executable package/risk/order flags and `0` true `ledger_namespace_synthesized_executable_candidate_use_allowed` rows.
- Prompt hardening passes, route artifact audit passes for the active V142 prefix, and V142 flow/parity/leakage artifacts are materialized. This is a B7 proof-surface correctness checkpoint, not a B7 transfer pass; valid missed winner recovery and broader V104 transfer remain open.

Prior V138 targeted B7 repair update:
- Targeted proof prefix: `BROAD_LIVE_AS_IF_REPLAY_V138_B7_ROUTER_FLOOR_PREVALIDATION_PRODUCER_REPAIR_20260601_20260605_TARGETED`; window `2026-06-01..2026-06-05`; symbols `XAUUSD XAGUSD USDCAD USDJPY UKOIL_cash`; profile `repaired_package_conversion_v3`.
- Behavior: `6633` candidates, `480` scorecard rows, `15` order rows, `3` filled trades, `6626` missed rows, `62` source rows, net `+0.84449709R`, gross/final `+1.09529478R`, cash PnL `+$211.19447407`, W/L/F `3/0/0`, all `3` fills open-reduced-risk.
- Clean authority checks from summary parsing: zero executed broker-cost REFUSED rows, zero executed source-gap rows, broker/live/final false.
- V138 improved V137 by `+1.29650389R` by removing two source-bound router-refusal below-floor fills: `3a90...` `-1.09572776R` and `03f5...` `-0.20077613R`. Both now remain scoreable missed rows with `router_refusal_fill_probability_below_floor`.
- V138 remains worse than V129 by `-1.39344095R` because V129 winners `bf1a...` `+1.12241840R` and `aa4b...` `+0.56193059R` are still missed. The next B7 leak is not this router-floor prevalidation path; it is lifecycle/order/reallocation recovery for valid winners and broader same-window transfer proof.

Latest V122J hostile-five-day B4 proof update:
- Completed replay status: `broad_live_as_if_replay_materialized_broker_live_closed`; `tick_source_mode=resolved_when_available`; `broker_mutation_enabled=false`; `live_broker_authority=false`; `final_selection_claim=false`; `cost_authority=broker_calibrated_replay_cost`; synthetic candidate-cost authority remains false.
- Transfer counts: `23575` candidates, `288` scorecard rows, `54` filled trades, `23512` missed-opportunity rows, `54` oracle rows, and `252` source-universe rows.
- Behavior: `54` trades, `-3.52793853R` net, `+0.80431616R` gross/final, `-$2864.90534326` cash PnL, `$27475.85401543` risk cash, `28.0287795%` risk-pct sum, W/L/F `30/24/0`, frequency `10.8` trades/day over the five-day window.
- Risk expression: `16` full-risk fills for `-3.00374152R` and `38` reduced/other fills for `-0.52419701R`; zero executed broker-cost REFUSED/source-gap/live/final rows on executable surfaces.
- Fill realism: filled trades are only `source_safe_immediate_marketable=43` and `ordered_tick_entry_touch=11`; no executable `m15_proxy`, `first_touch_optimistic`, broker-cost REFUSED, or source-gap fills.
- Stress/MC: +0.05R/trade stress `-6.22793853R`; +0.10R/trade `-8.92793853R`; +0.20R/trade `-14.32793853R`; Monte Carlo 200 iterations, seed `99173`, total `-3.52793853R`, max-drawdown p50 `-7.74449039R`, p05 `-11.25690019R`, worst `-14.90573852R`.
- Same-window comparison versus V121AG: trades `+9`, net R `-25.35276828`; added trades `45` for `-2.09049432R`, removed trades `36` for `+20.32346821R`. Interpretation: V122J truth repair increased source-bound R in-window but worsened executable behavior; do not tune from headline positivity because there is none.
- Same-window comparison versus V92: trades `+3`, net R `-32.88364089`; added trades `50` for `-2.32476056R`, removed trades `47` for `+27.85725442R`.
- B4 blocker classification on missed rows: `B6_cost_refusal_or_cost_authority=16071` rows, scoreable `5002`, opportunity net `-3265.25532658R`; `B2_B3_scheduler_risk_reallocation_or_admission=1232` scoreable, net `-231.92926208R`; `B4_order_geometry_guard=752` rows, net `-195.41712479R`; residual true B4 source/m15/ordered-source rows `65`, unscoreable/non-executable diagnostic. B4 status after V122J is `DONE WITH LABEL`: full 24-symbol tick hydration is present and executable fill truth is clean; the remaining losses are selected-transfer/exit behavior and B6 cost calibration, not missing tick source.

Latest V123 targeted B6 proof update:
- Targeted proof prefix: `BROAD_LIVE_AS_IF_REPLAY_V123_B6_RAW_TICK_COST_AUTHORITY_USDJPY_20260513_20260515_REPAIRED_ONLY_COMPACT_FULLGRID`; active replay symbol universe `USDJPY`, configured universe count `24`.
- Targeted behavior: `424` candidates, `253` scorecard rows, `12` order rows, `6` filled trades, `418` missed rows, `-0.99254709R` net, gross/final `-0.54989629R`, cash PnL `-$595.06062467`, W/L/F `3/3/0`. This is a targeted producer proof, not a broad behavior proof.
- Full V122J B6 audit: `23575` candidate rows, `16069` cost-refused candidates, `27828` refusal reason instances, `795` cells, `10325` sampled rows. Counts: honest `9699`, source-gap/no predecision tick `607`, stale/mapping `12`, metadata-review honest-refused `7`.
- Repair shipped: `_broker_cost_tick_from_row` now preserves actual historical predecision bid/ask as quote authority; static `TICK_SPREAD_FLOOR_R` is fallback/metadata and no longer inflates valid historical tick spreads.
- Targeted V123 B6 audit: `424` candidate rows, `125` cost-refused candidates, `214` refusal reason instances, `38` cells, `210` sampled rows, all `210` classified `honest_refusal_measured_tick_matches_original_cost`, with zero stale/mapping cells. Ten old stale IDs that regenerated now have `PASSED` broker-cost packets under raw historical tick cost; two old stale IDs did not regenerate in the targeted candidate set.

Latest V125 targeted B7.1 proof update:
- Targeted proof prefix: `BROAD_LIVE_AS_IF_REPLAY_V125_FABLE_B7_1_SIGNED_AUTHORITY_ALIAS_REPAIR_20260603_REPAIRED_ONLY_COMPACT_FULLGRID`; window `2026-06-03`; profile `repaired_package_conversion_v3`; tick source mode `resolved_when_available`; broker/live/final false.
- Producer repairs proven before V125: signed package authority attribution promotes compact row identity and scalar quality sources; generic ledger namespace alias status no longer stands in for signed quality alias status; effective/materialized selector action is used for executable package labels; selected-policy/profit-harvest ordered fill-bar observation is flattened.
- V125 behavior: `6603` candidates, `96` scorecard rows, `31` order rows, `14` filled trades, `6589` missed rows, `156` source-universe rows, net `-1.82424590R`, gross/final `-0.74330096R`, cash PnL `-$1563.10136496`, risk cash `$8133.65061919`, W/L/F `5/9/0`, full/reduced fills `3/11`.
- V125 fill realism: `source_safe_immediate_marketable=11`, `passive_queue_confirmed=3`; no executed REFUSED/source-gap rows, no broker/live/final rows.
- V125 parity/verifier: `SOURCE_BOUND_TO_EXECUTED_PARITY_V125_FABLE_B7_1_SIGNED_AUTHORITY_ALIAS_REPAIR_20260603_REPAIRED_ONLY_COMPACT_FULLGRID_SUMMARY.json` has `5974` parity rows and `1101` leakage bucket rows. `VERIFICATION_RESULT.json` generated `2026-07-06T10:13:06Z` is `ok=true`, `issue_count=0`. Flow diagnostic summary/dossier are materialized for the same prefix.
- V125 same-window transfer metrics from verifier: package axes inside replay window `1101`, candidate-generated axes `843`, scorecard/order-present axes `12`, filled trade axes `12`, package/source-bound R available in window `219778.99743033803R`, actual axis-attributed executable R `-1.97612654R`. This is a local B7.1 proof slice, not full-reservoir conversion.

Latest V126 broad B7.2 hostile-five-day proof update:
- Proof prefix: `BROAD_LIVE_AS_IF_REPLAY_V126_FABLE_B7_2_HOSTILE_5D_SIGNED_AUTHORITY_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH`; window `2026-05-13..2026-05-17`; full 24-symbol surface; profile `repaired_package_conversion_v3`; tick source mode `resolved_when_available`; packet sidecar omitted; broker/live/final false.
- V126 behavior: `24510` candidates, `288` scorecard rows, `129` order rows, `55` filled trades, `24446` missed rows, `252` source-universe rows, net `-4.43962487R`, gross/final `-0.23004143R`, cash PnL `-$3004.85149455`, risk cash `$28458.50823549`, W/L/F `30/25/0`, full/reduced fills `16/39`.
- Fill realism remains clean: `source_safe_immediate_marketable=44`, `ordered_tick_entry_touch=11`; no broker/live/final, executed REFUSED-cost, or executed source-gap rows.
- Same-window V122J comparison: candidates `+935`, scorecard `0`, order rows `+1`, trades `+1`, net R `-0.91168634`, gross/final R `-1.03435759`, cash PnL `-$139.94615129`, risk cash `+$982.65422006`. V126 added `2` trades for `-2.16054439R` and removed `1` loser for `-1.06208299R`; the added transfers were net negative.
- V126 parity/verifier: `SOURCE_BOUND_TO_EXECUTED_PARITY_V126_FABLE_B7_2_HOSTILE_5D_SIGNED_AUTHORITY_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH_SUMMARY.json` has `18650` parity rows and `1101` leakage bucket rows. `VERIFICATION_RESULT.json` verified `2026-07-06T11:38:23Z` is `ok=true`, `issue_count=0`; flow diagnostic summary/dossier are materialized for the same prefix.
- V126 same-window transfer metrics: package axes `1101`, candidate-generated axes `886`, scorecard/order-present axes `42`, filled trade axes `38`, package/source-bound R available in window `492961.6332259947R`, actual axis-attributed executable R `-5.1146153R`. V122J had the same `886` generated axes, `41` scorecard/order axes, `37` filled axes, `475938.7001370051R` source-bound R, and `-4.0917195R` axis-attributed executable R.
- Interpretation: B7.2 is verifier-green and truth-clean but behavior-negative. The authority bridge did not improve hostile transfer; it admitted one extra filled axis and extra source-bound R, but the added executable trades were stop-loss losers. Do not call this ultimate/final/live. The next Fable dependency is a non-hostile B7.3 proof to separate hostile-regime failure from systemic transfer failure, while retaining stop-loss/additional-transfer leakage as the highest current repair candidate.

Latest V127B broad B7.3 non-hostile-five-day proof update:
- Proof prefix: `BROAD_LIVE_AS_IF_REPLAY_V127B_FABLE_B7_3_NON_HOSTILE_5D_MISSED_AUTHORITY_REPAIR_20260601_20260605_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH`; window `2026-06-01..2026-06-05`; full 24-symbol surface; profile `repaired_package_conversion_v3`; tick source mode `resolved_when_available`; packet sidecar omitted; broker/live/final false.
- Tick hydration precondition was met by `data/mt5_research_exports/bridge_ftmo_ticks_v127_b7_3_20260601_20260605_full_plus_expiry/manifest.json`: `24` files, `24` symbols, `0` errors, `15847737` tick rows.
- Producer repair shipped before final verification: candidate-owned missed-opportunity rows now reapply the candidate nested signed new-entry authority payload after scheduler/replacement overlays. Evidence: `src/research_infra/v4_timewarp_simulated_live_research_loop.py::candidate_package_new_entry_authority_payload_fields` and focused test `tests/test_v4_timewarp_simulated_live_research_loop.py::test_missed_candidate_owned_authority_survives_scheduler_replacement_overlay`.
- One emitted V127B missed row was deterministically repaired from the same-key candidate ledger after the producer patch. Evidence: `BROAD_LIVE_AS_IF_REPLAY_V127B_FABLE_B7_3_NON_HOSTILE_5D_MISSED_AUTHORITY_REPAIR_20260601_20260605_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH_MISSED_AUTHORITY_ARTIFACT_REPAIR.json`, candidate line `28541`, missed line `28443`, target `replace_pending -> new_position`, hash `bac39af... -> e02402...`.
- V127B behavior: `34016` candidates, `480` scorecard rows, `259` order events, `109` filled trades, `33890` missed rows, `276` source-universe rows, net `-7.50803319R`, gross/final `+0.96507064R`, cash PnL `-$2819.9636123`, risk cash `$53127.32362826`, risk pct `54.42260009`, W/L/F `70/39/0`, full/reduced fills `33/76`.
- Fill realism remains clean: `source_safe_immediate_marketable=71`, `ordered_tick_entry_touch=38`; no broker/live/final, executed REFUSED-cost, or executed source-gap rows.
- Stress/MC: +0.05R/trade stress `-12.95803319R`; +0.10R/trade `-18.40803319R`; +0.20R/trade `-29.30803319R`; Monte Carlo 200 iterations, seed `99173`, total `-7.50803319R`, max-drawdown p50 `-11.75184423R`, p05 `-16.47025215R`, worst `-18.9940841R`.
- Same-window V104 comparison: trades `+63`, net R `-22.23904810`; added trades `103` for `-8.35722625R`, removed trades `40` for `+14.58298486R`. Added transfers were net negative and removed positive V104 behavior was material. Axis transfer delta: source-bound R available `+104131.93523391R`, candidate-generated axes `-7`, scorecard/order axes `+23`, filled axes `+27`, axis-attributed actual executable R `-35.68821996R`.
- V127B vs V127 comparison: trades `+2`, net R `+2.36357803`; added trades `3` for `+2.38357803R`, removed trade `1` for `+0.02R`. This delta is a replay reproducibility warning because the intended code change was ledger/authority truth, not policy.
- V127B parity/verifier: `SOURCE_BOUND_TO_EXECUTED_PARITY_V127B_FABLE_B7_3_NON_HOSTILE_5D_MISSED_AUTHORITY_REPAIR_20260601_20260605_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH_SUMMARY.json` has `22476` parity rows and `1101` leakage bucket rows. `VERIFICATION_RESULT.json` is `ok=true`, `issue_count=0`; flow diagnostic summary/dossier are materialized for the same prefix; prompt hardening, route artifact audit, py_compile, focused regression test, and `git diff --check` passed.
- V127B same-window transfer metrics: package axes `1101`, candidate-generated axes `887`, scorecard/order-present axes `56`, filled trade axes `54`, package/source-bound R available in window `530733.3290964501R`, headline replay net `-7.50803319R`, axis-attributed actual executable R `-22.3190414R`.
- Interpretation: B7.3 is verifier-green and truth-clean but behavior-negative. The non-hostile slice disproves the idea that B7.2 failure was only the hostile May regime. The next Fable dependency is not B8/live; it is a B7 transfer/exit repair batch focused on why current signed authority transfers many more trades than V104 while removing V104 winners and adding net-negative stop/profit-harvest/giveback paths.

## Baseline Context

These are comparator anchors, not proof denominators for B1. Replay proof must use same-window normalization.

| Run | Window | Trades | Net R | Gross/Final R | Cash PnL | W/L/F | Evidence |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| V89D | 2026-05-13..17 | 56 | 34.84520454 | 39.93441037 / 39.93441037 | 8178.90660707 | 41/15/0 | `.context/context_os/PRE_REPLAY_BRIEF_20260705T212848Z_V121AG_EFFECTIVE_STOP_HAZARD_CAP_TRANSFER_REPAIR.md:21` |
| V90 | 2026-05-13..17 | 51 | 28.84201157 | 33.36349114 / 33.36349114 | 6371.80465431 | 37/14/0 | `.context/context_os/PRE_REPLAY_BRIEF_20260705T212848Z_V121AG_EFFECTIVE_STOP_HAZARD_CAP_TRANSFER_REPAIR.md:22` |
| V92 | 2026-05-13..17 | 51 | 29.35570236 | not reloaded in this matrix | not reloaded in this matrix | 37/14/0 | `.context/context_os/CURRENT_ROOT_CAUSE_MAP_20260705T225354Z_V122_FABLE_B0_B1_PROVENANCE_TRUTH.json` |
| V121AG | 2026-05-13..17 | 45 | 21.82482975 | 25.17869106 / 25.17869106 | 12465.17720161 | 27/18/0 | `.context/context_os/CURRENT_ROOT_CAUSE_MAP_20260705T225354Z_V122_FABLE_B0_B1_PROVENANCE_TRUTH.json` |

V121AG exact-window denominator:
- source-bound R available in window: `407295.6072920759`
- package axes: `1101`
- generated candidate axes: `886`
- scorecard/order axes: `33`
- filled trade axes: `29`
- actual executable R in window: `21.29589138`

V121AG vs V92:
- trade delta `-6`
- net R delta `-7.53087261`
- added V121AG trades `40` for `+19.48176809R`
- removed V92 trades `46` for `+27.37534711R`
- common trade delta `+0.36270641R`
- removed V92 winner R `+40.41333898`
- added V121AG loser R `-12.20870184`

## Batch Status Summary

| Batch | Status | Next Action |
| --- | --- | --- |
| B0 truth instrumentation baseline | DONE | Keep outputs as fixed baseline for later batch deltas. |
| B1 provenance truth contract | DONE | Keep B1 proof labeled as current-stack proof, not clean isolated V114A, because later-batch behavior changes were already present. |
| B2 fillability and reallocation truth chain | DONE | Keep V122B as behavior-neutral B2 correctness proof; do not reopen unless tier/context propagation regresses. |
| B3 risk-expression ladder and loss-bucket demotion | DONE WITH LABEL | Risk-ladder truth and proof surfaces are closed; non-June anti-overfit executable distribution is blocked by B4 fill-source realism, not by missing ladder provenance. |
| B4 fill-simulation realism | DONE WITH LABEL | V122J completed the full 24-symbol hostile five-day tick-hydrated proof. Executable fills are realism-passing only and residual source rows are exact diagnostic/non-executable. The run is losing, so B4 closes as truth repair, not performance success. |
| B5 verifier and comparison precision | DONE | V122J parity was built before comparisons were rerun; V121AG/V92/V122I comparisons now report computed axis-transfer deltas. Targeted V123 summaries also distinguish active replay symbol universe from configured 24-symbol universe. |
| B6 broker-cost calibration audit | DONE WITH LABEL | Full V122J audit found 12 USDJPY stale-floor/mapping instances; producer repair shipped. Targeted V123 replay/audit shows all regenerated USDJPY refusal cells honest and zero stale/mapping cells. |
| B7 full proof ladder | PARTIAL | B7.1 one-day proof is DONE on V125; B7.2 hostile five-day proof is DONE on V126; B7.3 non-hostile five-day proof is DONE on V127B. V128 repairs the router-refusal derived immediate-marketable authority leak and improves the non-hostile five-day headline. V129 repairs terminal-vs-soft guard authority and selected-policy executable-quality gating in a five-symbol targeted slice. V138/V140/V141/V142 close later B7 proof-surface authority leaks, with V142 demoting synthesized executable namespace authority on terminal-veto missed rows. B7 remains open because V104 winner recovery and broad same-window transfer are not solved. |
| B8 live path | OPEN | Run only after B7 passes; broker/live/final remain closed until then. |

## B0 - Truth Instrumentation Baseline

Status: DONE.

Requirements and evidence:
- DONE: one-off audit script exists at `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/audit_provenance_and_flags_v114.py`.
- DONE: provenance/flag output exists at `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/AUDIT_PROVENANCE_AND_FLAGS_V114.json`, generated `2026-07-05T23:04:05Z`, schema `v114_b0_provenance_and_flags_audit_v1`.
- DONE: broker-cost refusal histogram exists at `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/BROKER_COST_REFUSAL_HISTOGRAM_V111.json`, generated `2026-07-05T23:04:05Z`.
- DONE: V110B aggregate baseline recorded: `75562` rows, `12525` selector origin/effective mismatches, `0` mismatches without materialized flag, `0` stale cap zero-risk rows, `0` fallback-starved expired rows, `0` R-accounting drift rows, `0` raw-failure poisoning rows, reallocation hist `False=12492`, `True=437`, `missing=62633`.
- DONE: V111 aggregate baseline recorded: `76102` rows, `12705` selector origin/effective mismatches, `0` mismatches without materialized flag, `0` stale cap zero-risk rows, `0` fallback-starved expired rows, `0` R-accounting drift rows, `0` raw-failure poisoning rows, reallocation hist `False=12710`, `True=305`, `missing=63087`.
- DONE: B0 behavior expectation is neutral; no replay needed.

Remaining B0 gap:
- None for the Fable baseline. Later batches may add derivative scans, but B0 acceptance is met.

## B1 - Provenance Truth Contract

Status: DONE.

Requirements and evidence:
- DONE: selector decision has explicit immutable raw fields. Evidence: `src/components/selector_v4.py:3053` `selector_action`, `:3054` `selector_reason`, `:3055` `candidate_use_allowed_now_semantics`; `:3075` writes `record["selector_action"]`; `:5250` constructs `selector_action=would_action`.
- DONE: selector focused tests exist. Evidence: `tests/test_selector_v4.py:212` `test_selector_record_preserves_raw_selector_action_under_downstream_mutation`, `:241` `test_selector_action_and_would_action_contract`, `:262` `test_selector_open_reduced_reason_contract_stays_in_sync`.
- DONE: timewarp materialization preserves origin and effective action in many surfaces. Evidence: `src/research_infra/v4_timewarp_simulated_live_research_loop.py:55942`, `:56285`, `:56711`, `:56903`, `:57076`, `:57167`, `:58416`, `:58409`; tests around `tests/test_v4_timewarp_simulated_live_research_loop.py:1028`, `:1038`, `:1096`, `:1118`, `:1121`, `:1158`.
- DONE: runtime risk authority raw chain reads `scheduler_materialization_original_selector_action`. Evidence: `src/research_infra/v4_timewarp_simulated_live_research_loop.py:24915`, `:24919`, `:24922`, `:24925`.
- DONE: position/trade ledger surfaces have selector origin/effective fields. Evidence: `src/research_infra/v4_timewarp_simulated_live_research_loop.py:2340`, `:2423`, `:2454`, `:2484`, `:2485`.
- DONE: terminal lifecycle/account row gross/net identity code exists. Evidence: `src/research_infra/v4_timewarp_simulated_live_research_loop.py:2157`, `:2169`, `:2413`, `:2454`, `:2547`, `:2568`, `:2587`.
- DONE: scheduler allocator preserves raw metadata and writes effective separately. Evidence: `src/research/moonshot_scheduler_v4_best_trade_allocator.py:6256`, `:6272`, `:6309`, `:6310`.
- DONE: scheduler metadata focused test exists. Evidence: `tests/test_moonshot_scheduler_v4_best_trade_allocator.py:1187` `test_allocator_candidate_metadata_preserves_raw_selector_action_origin`.
- DONE: Fable-required E2E coverage exists as a focused chain rather than one monolithic test. Materialization row/candidate coverage: `tests/test_timewarp_scheduler_materialization.py:855`, `:984`, `:1333`, `:1538`, `:1641`. Risk packet raw/effective coverage: `tests/test_v4_timewarp_simulated_live_research_loop.py:1633` `test_full_risk_expression_preserves_raw_reject_materialized_effective_action`. Scorecard/normalizer coverage: `tests/test_v4_timewarp_simulated_live_research_loop.py:1024`, `:1084`, `:6905`, `:9197`, `:9456`. Trade/account R identity coverage: `tests/test_v4_timewarp_simulated_live_research_loop.py:12218`.
- DONE: B1 focused tests passed after this matrix: selector raw/effective contract, scheduler metadata origin, risk-ladder raw action preference, terminal close R identity, and five materialization-origin tests.
- DONE: B1 compile passed after this matrix for `selector_v4.py`, scheduler allocator, reduced-risk reason contract, timewarp loop, and B0 audit script.
- DONE WITH LABEL: targeted current-stack proof run completed at `BROAD_LIVE_AS_IF_REPLAY_V122_FABLE_B0_B1_PROVENANCE_TRUTH_20260603_REPAIRED_ONLY_COMPACT_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`. It is not a clean isolated V114A behavior-neutral run because the current code already includes later B2/B3/B4/B5 behavior changes. The B1 truth checks passed, but behavior moved relative to V114C: trades `12 -> 14`, orders `28 -> 15`, expired `16 -> 1`, fallback trades `12 -> 0`, net R `-2.30082618 -> -1.8242459`.
- DONE: V122 B1 truth scan on executable surfaces: order/trade executed REFUSED cost rows `0`, source-gap executions `0`, live/final true rows `0`, R identity drift rows `0`, selector origin/effective mismatches without materialized flag `0`.
- DONE: route verifier rerun after V122 proof wrote `VERIFICATION_RESULT.json` with `ok=true`, `issue_count=0`.

Next B1 implementation/proof steps:
- None. B1 is closed for current-stack dependency purposes. Do not rerun B1 unless a later patch reopens raw/effective provenance or R identity.

Behavior expectation:
- Candidate -> scorecard stayed unchanged versus V114C at `6603/96`.
- Current-stack behavior moved because later-batch changes are already present: V122 has `14` trades, `15` orders, `1` expired, `0` fallback trades, `-1.8242459R`.
- Provenance collapse and R identity proof surfaces are trustworthy on executable surfaces.

## B2 - Fillability And Reallocation Truth Chain

Status: DONE.

Requirements and evidence:
- DONE: `session_open_range_break` is in route-resolution authority families. Evidence: `src/research/moonshot_scheduler_v4_best_trade_allocator.py:306`; test `tests/test_moonshot_scheduler_v4_best_trade_allocator.py:203`.
- DONE: fill-floor authority now separates authority failures from raw/resolved failures in signed surfaces. Evidence: `src/research/moonshot_scheduler_v4_best_trade_allocator.py:15595` through `:15608`, `:18938` through `:18945`.
- DONE: reallocation quality soft-guard tests exist. Evidence: `tests/test_moonshot_scheduler_v4_best_trade_allocator.py:332`, `:408`, `:11546`.
- DONE: terminal veto sweep clears stale cap release fields. Evidence: `src/research/moonshot_scheduler_v4_best_trade_allocator.py:19389`, `:19397`.
- DONE: fallback-time clamp and expiry exhaustion surfaces exist. Evidence: `src/research_infra/v4_timewarp_simulated_live_research_loop.py:45877`, `:46136`, `:46217`, `:46504`; tests around `tests/test_v4_timewarp_simulated_live_research_loop.py:13912`, `:31151`.
- DONE: unconditional open-reduced tier demotion is repaired. Evidence: `_candidate_option` now records `selector_reduced_new_entry_pending_primary_trade_competitor_context` without demotion at `src/research/moonshot_scheduler_v4_best_trade_allocator.py:19467`; `_apply_selector_reduce_risk_fallback_priority_context` demotes to tier `1` only when an eligible runtime `trade` competitor exists at `src/research/moonshot_scheduler_v4_best_trade_allocator.py:8039`, and otherwise resolves to tier `0` with `selector_reduced_new_entry_no_primary_trade_competitor` at `:8107`.
- DONE: focused B2 tests passed after the patch: reallocation quality promotes/refuses signed soft-guard candidates, blocked executable candidate reallocates to next valid same-window candidate, no-trade-competitor priority remains pending before context, passive-limit fill-floor route resolution, numeric disagreement fallback, guarded-market lifetime clamp, finalizer passive-limit fallback clamp/exhaustion, degraded passive queue release, and fill-floor trace raw/resolved/unresolved exposure. Evidence: `tests/test_moonshot_scheduler_v4_best_trade_allocator.py:332`, `:408`, `:8161`, `:11542`, `:15041`, `:15071`; `tests/test_v4_timewarp_simulated_live_research_loop.py:13838`, `:31133`, `:31215`; `tests/test_timewarp_scheduler_materialization.py:6064`.
- DONE: B2 compile passed for `src/research/moonshot_scheduler_v4_best_trade_allocator.py` and `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`.
- DONE WITH LABEL: targeted B2 proof run completed at `BROAD_LIVE_AS_IF_REPLAY_V122B_FABLE_B2_PRIORITY_CONTEXT_REPAIR_20260603_REPAIRED_ONLY_COMPACT_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`. It is a one-day June 3 local repair proof, not full-reservoir proof. It was behavior-neutral versus V122 B1: `14` trades, net R `-1.8242459`, gross/final R `-0.74330096`, cash PnL `-1563.10136496`, W/L/F `5/9/0`, `15` orders, `1` expired, `6603` candidates, `96` scorecard rows, `6586` missed rows, fallback trades `0`.
- DONE: V122B executable-surface truth scan passed: trade/order/scorecard/missed rows had executed REFUSED cost rows `0`, executed source-gap rows `0`, live/final true rows `0`, and selector origin/effective mismatches without materialization authority `0`.

Next B2 implementation/proof steps:
- None. Reopen only if later B3/B4/B5 work breaks priority context propagation, reallocation trace, or executable-surface truth.

Behavior expectation:
- Correctness-changing and locally behavior-neutral on the June 3 proof slice. It removes artificial demotion of open-reduced rows without suppressing opportunity; no candidate/scorecard/order/fill transfer changed in V122B versus V122 B1.

## B3 - Risk-Expression Ladder And Loss-Bucket Demotion

Status: DONE WITH LABEL.

Requirements and evidence:
- DONE: config has diagnostic exact-block mode. Evidence: `config/agent_config.yaml:813`.
- DONE: selector fill-floor softening default is false in current config. Evidence: `config/agent_config.yaml:795`; selector code references defaults around `src/components/selector_v4.py:4253`, `:4672`, `:4769`.
- DONE: broker net gradient open-reduced default is false in current config. Evidence: `config/agent_config.yaml:1045`.
- DONE: below-full-trade-floor package authority tests exist. Evidence: `tests/test_selector_v4.py:1877`, `:1939`.
- DONE: fill-floor softening requires signed package authority test exists. Evidence: `tests/test_selector_v4.py:3793`.
- DONE: scheduler risk-expression ladder producer exists. Evidence: `src/research/moonshot_scheduler_v4_best_trade_allocator.py:7878`, `:7913`, `:19496` through `:19583`.
- DONE: timewarp risk ladder consumer/propagation surfaces exist. Evidence: `src/research_infra/v4_timewarp_simulated_live_research_loop.py:7806`, `:8937`, `:9187`, `:12417`, `:18739`, `:62498`.
- DONE: off-configured session configured open-reduced action is now semantic, not collapsed to generic reduce-risk. Evidence: `src/components/selector_v4.py:2175`, `src/components/selector_v4.py:4632`, `src/research/reduced_risk_action_reason_contract.py:56`, and focused test `tests/test_selector_v4.py:568`.
- DONE: dynamic-router configured open-reduced action has its own reason contract. Evidence: `src/components/selector_v4.py:2140`, `src/components/selector_v4.py:4630`, `src/research/reduced_risk_action_reason_contract.py:55`, and focused test `tests/test_selector_v4.py:2040`.
- DONE: prefixed scorecard/finalizer risk-expression ladders are consumed by the top-level ladder normalizer instead of remaining stranded under `scorecard_reported_`, `risk_finalizer_`, or `finalizer_primary_probe_` prefixes. Evidence: `src/research_infra/v4_timewarp_simulated_live_research_loop.py:7806`, `:7824`, `:7833`, `:8128`, and test `tests/test_v4_timewarp_simulated_live_research_loop.py:686`.
- DONE: no-probe and non-materialized missed-opportunity rows now receive explicit diagnostic risk-expression ladders with full-risk flags false rather than blank provenance. Evidence: `src/research_infra/v4_timewarp_simulated_live_research_loop.py:18621`, `:19138`; tests `tests/test_v4_timewarp_simulated_live_research_loop.py:6007`, `:6216`.
- DONE: V122B projection scan with the new normalizer closes the concrete missing-ladder surfaces without changing executable order/trade tier distribution: scorecard `24 -> 0` missing, missed-opportunity `4289 -> 0` missing, order `0 -> 0`, trade `0 -> 0`.
- DONE: focused B3 regression checks passed after the patch: selector configured-action set `7 passed`, scheduler/materialization raw/effective set `5 passed`, timewarp risk-ladder set `9 passed`, verifier full-risk/stale-priority set `2 passed`, all-touched `py_compile` passed.
- DONE WITH LABEL: V122C targeted June-3 proof completed at `BROAD_LIVE_AS_IF_REPLAY_V122C_FABLE_B3_RISK_LADDER_20260603_REPAIRED_ONLY_COMPACT_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`. This is a one-day local B3 repair proof, not full-reservoir conversion. It is behavior-neutral versus V122B: trades `14`, net R `-1.8242459`, gross/final R `-0.74330096`, cash PnL `-1563.10136496`, W/L/F `5/9/0`, candidates `6603`, scorecard `96`, orders `32`, missed `6586`, expired `1`, fallback trades `0`.
- DONE: V122C June-3 B3 checks passed: executed REFUSED cost rows `0`, executed source-gap rows `0`, live/final true rows `0`, full-risk signing bad rows `0`, ladder missing rows scorecard/missed/order/trade all `0`. Risk tiers: scorecard `diagnostic=96`; missed `diagnostic=6586`; order `full=8`, `reduced=22`, `diagnostic=2`; trade `full=3`, `reduced=11`.
- DONE WITH LABEL: V122D anti-overfit `2026-06-11` completed with final artifacts and zero missing ladder rows, zero executed REFUSED/source-gap rows, and zero live/final true rows, but had `0` filled trades and all `45` order rows diagnostic. It proves ladder truth generalizes to another day, not executable distribution.
- DONE WITH LABEL: V122E anti-overfit `2026-06-10` completed with final artifacts and zero missing ladder rows, zero executed REFUSED/source-gap rows, and zero live/final true rows, but had `0` filled trades and all `51` order rows diagnostic. Top order/missed causes are `postdecision_m15_proxy_diagnostic_path_not_executable`, `postdecision_m15_proxy_not_executable_order_fill_truth`, and broker-cost diagnostic refusal.
- DONE WITH B4 BLOCKER: B3 risk-expression provenance is closed; the remaining anti-overfit executable-distribution gap is a B4 fill-source realism/source-availability blocker, because non-June targets are diagnostic-only under skip-tick/M15-proxy paths.

Next B3 implementation/proof steps:
1. Do not rerun B3 just to chase a no-fill day. The repeated anti-overfit proofs now point to B4.
2. Move to B4 fill-simulation/source realism: prove whether the non-June diagnostic-only order paths are honest tick/source gaps, skip-tick proof-mode artifacts, or code/config fill-source miswiring.
3. Keep B3 artifacts as local repair proofs; do not call them full-reservoir conversion or live-ready proof.

Behavior expectation:
- Behavior-changing. Full-risk rows should become reachable only for signed, broker-cost-passed, source-complete, fillable, top-ranked package candidates. Reduced rows must carry tier causes. Diagnostic bucket demotion should reveal opportunity instead of suppressing it.

## B4 - Fill-Simulation Realism

Status: DONE.

Requirements and evidence:
- DONE: immediate marketable predecision source-time gate exists. Evidence: `src/research_infra/v4_timewarp_simulated_live_research_loop.py:36774`, `:36893`.
- DONE: immediate marketable predecision source-time gate now rejects same-time closed-bar snapshots and stale closed-M15 snapshots instead of treating them as executable immediate fills. Evidence: `tests/test_v4_timewarp_simulated_live_research_loop.py` focused tests `test_predecision_limit_fillability_rejects_same_time_closed_bar_snapshot`, `test_predecision_limit_fillability_rejects_stale_closed_bar_snapshot`, `test_immediate_marketable_limit_rejects_same_time_closed_bar_price`, and `test_immediate_marketable_limit_rejects_stale_closed_bar_price`; combined focused B4/B5 test run on `2026-07-06T04Z` passed `16`.
- DONE: same-bar ambiguity conservative close exists. Evidence: `src/research_infra/v4_timewarp_simulated_live_research_loop.py:41917`; tests `tests/test_v4_timewarp_simulated_live_research_loop.py:13106`, `:13124`.
- DONE: fill-realism class keys and classifier exist. Evidence: `src/research_infra/v4_timewarp_simulated_live_research_loop.py:41962`, `:42008`, `:42057`, `:42077`, `:42169`.
- DONE: fill-realism tests exist for M15 proxy, first-touch optimistic, ordered-tick required source gap, and legacy M1 first-touch without queue realism. Evidence: `tests/test_v4_timewarp_simulated_live_research_loop.py:2304`, `:2466`, `:2535`, `:2585`, `:2711`.
- DONE: selected diagnostic fill-realism counterfactual orders now expand into missed-opportunity accounting instead of disappearing from opportunity ledgers. Evidence: `tests/test_v4_timewarp_simulated_live_research_loop.py` focused test `test_selected_diagnostic_counterfactual_orders_expand_to_missed_contract` passed in the combined B4/B5 run.
- DONE: FTMO export/availability defaults now use resolver-compatible 24-symbol mappings when `--source-broker FTMO` is selected, preserving legacy mappings for non-FTMO. Evidence: `scripts/export_mt5_research_ohlcv.py`, `scripts/export_mt5_research_ticks.py`, `scripts/inspect_mt5_tick_availability.py`, and `tests/test_mt5_research_export_symbol_defaults.py` passed in the combined B4/B5 run.
- DONE: V122D/V122E non-June B3 anti-overfit proofs exposed the active B4 blocker: under compact skip-tick proof mode, non-June targets produced `0` filled trades and all orders diagnostic, dominated by `postdecision_m15_proxy_diagnostic_path_not_executable` and `postdecision_m15_proxy_not_executable_order_fill_truth`.
- DONE: MT5/Silicon bridge liveness recovered without restart. Raw RPyC root, MT5 import, `terminal_info()`, and a one-minute XAUUSD tick availability probe succeeded with `73` rows at `data/mt5_research_exports/tick_availability/v122f_b4_bridge_liveness_xauusd_1m_20260706T043259Z.json`.
- DONE: targeted FTMO ordered tick export for `2026-06-10T00:00:00Z..2026-06-11T02:00:00Z` completed with `errors=[]` at `data/mt5_research_exports/bridge_ftmo_ticks_v122e_20260610_full_plus_expiry/manifest.json`. Row counts: XAUUSD `358732`, GER40 `217107`, USDJPY `73348`, BTCUSD `557858`, USOIL_cash `90103`, UKOIL_cash `73063`, XAGUSD `393787`, AUDJPY `165750`, USDCHF `83684`.
- DONE: lazy tick source query now validates overlapping component file hashes before loading rows and reports validation events in `PathTruthIndex` metadata; focused test `test_tick_source_resolver_validates_lazy_manifest_sha_at_window_load` passed.
- DONE: tick source coverage now uses actual manifest `first`/`last` ticks before requested export bounds, preventing stale requested-window coverage from acting as path truth; focused test `test_tick_source_specs_use_actual_tick_first_last_for_coverage` passed.
- DONE: actual V122G export resolver/query check passed for all 9 exported symbols; each returned rows and exactly one overlapping `validated_file_hash_match` event for `2026-06-10..2026-06-11T02:00Z`.
- DONE WITH LABEL: first V122G replay attempt was interrupted before behavior proof and wrote `...V122G..._PARTIAL_SUMMARY.json` with `status=interrupted_partial_not_final_proof`; it is retained only as evidence of the eager-hash performance bug, not as replay behavior proof.
- DONE WITH LABEL: V122H targeted 2026-06-10 tick-enabled source-realism proof completed at `BROAD_LIVE_AS_IF_REPLAY_V122H_FABLE_B4_TICK_ENABLED_SOURCE_REALISM_20260610_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH`. It is a bounded one-day, 9-symbol tick-export proof, not a full 24-symbol/B7 proof and not a full-reservoir conversion claim.
- DONE: V122H kept V122E candidate and scorecard transfer stable while adding realism-passing fills: candidates `6369 -> 6369`, scorecard `96 -> 96`, terminal/simulated orders `0 -> 13`, filled trades `0 -> 10`, net R `0.0 -> 0.07137833`, gross/final R `0.0 -> 0.86997526`, cash PnL `0.0 -> 158.91066658`, W/L/F `0/0/0 -> 7/3/0`.
- DONE: V122H proof checks passed on executable surfaces: executed REFUSED cost rows `0`, executed source-gap rows `0`, broker/live mutation true rows `0`, final true rows `0`, missing risk ladder rows `0`, M15-proxy executable rows `0`, first-touch optimistic executable rows `0`.
- DONE: V122H fill-realism split shows executable trades only from ordered/realistic classes: trade fill realism `ordered_tick_entry_touch=5`, `source_safe_immediate_marketable=5`; order fill realism includes `not_filled=3`, `ordered_tick_entry_touch=5`, `source_safe_immediate_marketable=5` on terminal/simulated rows.
- DONE WITH LABEL: V122H improvement source is better ordered tick source conversion, not positive-by-suppression: candidate and scorecard counts were unchanged versus V122E, and the added trades are explicitly filled under tick/source-safe classes.
- DONE WITH LABEL: V122H still exposed B4 source realism blockers, which is why V122J was required. Missed fill-realism class counts were `m15_proxy=4502`, `not_filled=1077`, `ordered_tick_entry_touch=525`, `source_gap=94`, `source_safe_immediate_marketable=158`; this is retained as historical one-day evidence, not current B4 blocker status.
- DONE: V122H B4 blocker classifier is route-owned and reproducible at `classify_b4_source_realism_blockers.py`; focused test `tests/test_classify_b4_source_realism_blockers.py` passed. Generated artifacts: `BROAD_LIVE_AS_IF_REPLAY_V122H_FABLE_B4_TICK_ENABLED_SOURCE_REALISM_20260610_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH_B4_SOURCE_REALISM_BLOCKER_CLASSIFICATION.json` and `_B4_SOURCE_REALISM_BLOCKER_BUCKET_LEDGER.jsonl`.
- DONE WITH LABEL: V122H blocker classification shows remaining missed rows are not a pure B4 source leak. Stage buckets: B6 cost refusal/cost authority `4870` rows, `423` scoreable, `-264.70564042R`; B2/B3 scheduler-risk/admission `133` rows, `-26.27521669R`; B4 order geometry guard `106` rows, `-17.82874179R`; B4 source-realism/missing ordered source `696` rows, `0` scoreable opportunity R. Separate diagnostic proxy-mark accounting for unscoreable rows shows B4 source/missing-source proxy mark `48` rows, `-0.0166692602R`, positive `+8.6301837482R`, negative `-8.6468530084R`; `m15_proxy` proxy mark `94` rows, `-10.4640443244R`.
- DONE: full 24-symbol hostile-five-day tick surface was proven by V122J using `data/mt5_research_exports/bridge_ftmo_ticks_v122i_20260513_20260517_full_plus_expiry/manifest.json` with `24` files, `24` symbols, `0` errors, and `9941602` tick rows.
- DONE WITH LABEL: hostile five-day V122J proof completed at `BROAD_LIVE_AS_IF_REPLAY_V122J_FABLE_B4_HOSTILE_5D_FILL_REALISM_TICK_HYDRATED_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH`. It had `54` realism-passing filled trades and zero executed REFUSED/source-gap/M15-proxy/first-touch optimistic rows, but it lost `-3.52793853R`; this closes fill-source truth and exposes selected-transfer/exit behavior for B7, not B4 source incompleteness.
- DONE: current V122H analysis proves executable order/trade rows have zero `first_touch_optimistic` executable fills and zero `m15_proxy` executable fills.
- DONE: V122J B4 classifier artifacts exist at `BROAD_LIVE_AS_IF_REPLAY_V122J_FABLE_B4_HOSTILE_5D_FILL_REALISM_TICK_HYDRATED_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH_B4_SOURCE_REALISM_BLOCKER_CLASSIFICATION.json` and `_B4_SOURCE_REALISM_BLOCKER_BUCKET_LEDGER.jsonl`.

Next B4 implementation/proof steps:
- None for this dependency checkpoint. If B7 exposes a new fill-source regression in a different regime, reopen B4 with same-window tick/source evidence.

Behavior expectation:
- Behavior-changing truth repair. V122J worsened headline R because prior positive behavior depended on less strict source/cost/fill truth; keep the truth and continue with B7 proof ladder.

## B5 - Verifier And Comparison Precision

Status: DONE.

Requirements and evidence:
- DONE: verifier requires/uses `effective_selector_action` in compact/bridge scans. Evidence: `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py:2731`, `:2763`, `:2995`; test `tests/test_denominator_to_deployment_verifier.py:7386`.
- DONE: executable raw reject/effective trade leak test exists. Evidence: `tests/test_denominator_to_deployment_verifier.py:6801`.
- DONE: full-risk signing fatal exists. Evidence: `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py:4045`; test `tests/test_denominator_to_deployment_verifier.py:2256`.
- DONE: candidate-generation authority/symbol-scope proof fatal exists. Evidence: verifier around `:4207`, `:4238`; test evidence around `tests/test_denominator_to_deployment_verifier.py:4298` from current search context.
- DONE: off-configured guarded fallback predicate uses `off_configured_fallback_allowed is not True`. Evidence: `verify_denominator_to_deployment_execution.py:8798`, `:8826`.
- DONE: expected-count pins are behind `--pin-snapshot`. Evidence: `verify_denominator_to_deployment_execution.py:9983`, `:9990`; tests `tests/test_denominator_to_deployment_verifier.py:7859`.
- DONE: parity builder reads broad replay profile from row/summary. Evidence: `build_source_bound_execution_parity.py:1397`, `:1407`, `:1431`, `:1636`, `:2099`, `:2123`.
- DONE: same-window comparison now has a focused test pinning risk-ladder tier counts, ladder cause histogram, fill-realism class counts, executable counts, and fill-realism net R split. Evidence: `tests/test_compare_broad_live_as_if_replay_runs.py::test_trade_rollup_reports_risk_ladder_and_fill_realism_splits`.
- DONE: selected-package replay bridge scope is now verifier-enforced: `full-package` proof must not be bounded, while lifecycle/pending/m15 scoped bridge outputs must carry `bounded_smoke=true`. Evidence: `verify_denominator_to_deployment_execution.py::selected_package_replay_bridge_scope_issues` and `tests/test_denominator_to_deployment_verifier.py::test_selected_package_replay_bridge_scope_requires_explicit_bounded_smoke`.
- DONE: selected-package bridge compact candidate stop-hazard projection no longer invents a partial `predecision_stop_hazard_guard_risk_cap_applied=False` field when the guard is absent. Evidence: `run_selected_package_replay_bridge.py::_normalize_stop_hazard_cap_truth`, `tests/test_denominator_to_deployment_verifier.py::test_bridge_stop_hazard_normalizer_does_not_invent_partial_projection`, and regenerated bridge compact candidates show `307` rows with `0` partial stop-hazard projections.
- DONE: selected-package replay bridge regenerated from the route-owned runner, not hand-edited. Evidence: `REPLAY_EXTENSION_SELECTED_PACKAGE_REPLAY_BRIDGE_SUMMARY.json` generated `2026-07-06T04:21:20+00:00`, `bounded_smoke=true`, `symbol_scope=lifecycle-labels`, `candidate_rows=307`, `scorecard_rows=13`, `order_rows=0`, `trade_rows=0`, `broker_mutation=false`, `final_package_selection_allowed=false`.
- DONE: route verifier rerun after B4/B5 patches wrote `VERIFICATION_RESULT.json` with `ok=true`, `issue_count=0`, `verified_utc=2026-07-06T04:24:48Z`.
- DONE: focused B4/B5 test run passed `16 passed, 646 deselected`; touched-route py_compile passed for export/availability scripts, timewarp loop, comparator, selected-package bridge, verifier, and focused tests.
- DONE: V122J parity build and rerun comparisons bind axis-transfer deltas. Evidence: `SOURCE_BOUND_TO_EXECUTED_PARITY_V122J_FABLE_B4_HOSTILE_5D_FILL_REALISM_TICK_HYDRATED_SUMMARY.json`, V122J vs V121AG comparison with `axis_transfer_delta_status=computed`, V122J vs V92 comparison with `axis_transfer_delta_status=computed`, and V122J vs V122I comparison with `axis_transfer_delta_status=computed`.
- DONE: targeted V123 summaries now distinguish active replay denominator from configured universe. Evidence: `run_broad_live_as_if_replay_harness.py::active_replay_symbol_universe`, V123 summary fields `active_replay_symbol_universe=["USDJPY"]`, `active_replay_symbol_count=1`, `configured_symbol_count=24`, and regression `tests/test_build_source_bound_execution_parity.py::test_broad_live_as_if_replay_requested_symbols_preserve_cash_suffix_case`.

Next B5 implementation/proof steps:
- None for the Fable dependency ladder. Full proof-ladder verifier assertions still move to B7 after B4/B6 closure.

Behavior expectation:
- Mostly proof-machine repair. It should not change replay behavior but can change whether bad proof passes/fails.

## B6 - Broker-Cost Calibration Audit

Status: DONE WITH LABEL.

Requirements and evidence:
- DONE prerequisite: B0 refusal histogram exists at `BROKER_COST_REFUSAL_HISTOGRAM_V111.json`.
- DONE prerequisite: MT5 bridge tick proof exists at `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/mt5_tick_probes/tick_availability/v121ah_may_tick_gap_probe_20260705T224825Z.json`.
- DONE: broker-calibrated cost authority and tests exist; synthetic timewarp candidate-cost remains fallback diagnostic only.
- DONE: B6 calibration audit script exists at `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/audit_b6_broker_cost_calibration_v123.py`.
- DONE: focused audit regression exists at `tests/test_audit_b6_broker_cost_calibration.py::test_b6_audit_classifies_honest_and_stale_refused_cost_rows`.
- DONE: full V122J refusal sample classification exists at `BROKER_COST_CALIBRATION_AUDIT_V123_B6_BROKER_COST_CALIBRATION_AUDIT_V122J.json`: `23575` candidate rows, `16069` refused candidates, `27828` refusal reason instances, `795` cells, `10325` sampled rows, with `9699` honest refusal rows, `607` source-gap rows, `12` stale/mapping rows, and `7` metadata-review honest-refused rows.
- DONE: stale/mapping root bug patched in `src/research_infra/v4_timewarp_simulated_live_research_loop.py::_broker_cost_tick_from_row`. Actual historical predecision tick quotes now remain raw quote authority; static measured tick floor is fallback/metadata and no longer inflates valid historical bid/ask spreads.
- DONE: producer regression exists at `tests/test_v4_timewarp_simulated_live_research_loop.py::test_broker_calibrated_replay_cost_preserves_raw_historical_tick_below_static_floor`.
- DONE: recalibrated targeted proof exists at `BROAD_LIVE_AS_IF_REPLAY_V123_B6_RAW_TICK_COST_AUTHORITY_USDJPY_20260513_20260515_REPAIRED_ONLY_COMPACT_FULLGRID`: `424` candidates, `253` scorecard rows, `12` order rows, `6` fills, `418` missed rows, net `-0.99254709R`, active replay symbol universe `USDJPY`, configured count `24`, broker/live/final false.
- DONE: targeted V123 B6 audit exists at `BROKER_COST_CALIBRATION_AUDIT_V123_B6_BROKER_COST_CALIBRATION_AUDIT_USDJPY_TARGETED.json`: `125` refused candidates, `214` refusal reason instances, `38` cells, `210` sampled rows, all `210` classified `honest_refusal_measured_tick_matches_original_cost`, zero stale/mapping cells. Ten old stale IDs that regenerated now pass broker cost; two old stale IDs did not regenerate in the targeted candidate set.

Next B6 implementation/proof steps:
- None for this dependency checkpoint. Remaining source-gap/no-predecision-tick rows are labeled calibration gaps, not executable proof. If B7 exposes cost as a new material blocker in a broader regime, rerun B6 audit over that exact window.

Behavior expectation:
- Behavior-changing only for real-tick rows below stale static floor. REFUSED gate remains intact; REFUSED/source-gap rows remain non-executable and scoreable/missed unless regenerated broker-cost authority passes.

## B7 - Full Proof Ladder

Status: PARTIAL.

Requirements:
- DONE: 7.1 one-day June 3 proof after B1-B6 closure. Evidence: `BROAD_LIVE_AS_IF_REPLAY_V125_FABLE_B7_1_SIGNED_AUTHORITY_ALIAS_REPAIR_20260603_REPAIRED_ONLY_COMPACT_FULLGRID`; route verifier `ok=true`, `issue_count=0`; flow diagnostic materialized; prompt hardening and route artifact audit passed.
- DONE WITH NEGATIVE BEHAVIOR LABEL: 7.2 hostile five-day proof after fill realism/cost calibration closure. Evidence: `BROAD_LIVE_AS_IF_REPLAY_V126_FABLE_B7_2_HOSTILE_5D_SIGNED_AUTHORITY_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH`; route verifier `ok=true`, `issue_count=0`; flow diagnostic, parity, and V122J comparison materialized. Behavior versus V122J: trades `+1`, net R `-0.91168634`, axis-attributed actual R `-1.0228958`, added trades `2` for `-2.16054439R`, removed trades `1` for `-1.06208299R`.
- DONE WITH NEGATIVE BEHAVIOR LABEL: 7.3 non-hostile five-day proof after B7.2. Evidence: `BROAD_LIVE_AS_IF_REPLAY_V127B_FABLE_B7_3_NON_HOSTILE_5D_MISSED_AUTHORITY_REPAIR_20260601_20260605_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH`; route verifier `ok=true`, `issue_count=0`; flow diagnostic, parity, V104 comparison, V127 comparison, prompt hardening audit, route artifact audit, focused regression test, py_compile, and `git diff --check` passed. Behavior versus V104: trades `+63`, net R `-22.23904810`, axis-attributed actual R `-35.68821996`, added trades `103` for `-8.35722625R`, removed trades `40` for `+14.58298486R`.
- DONE WITH POSITIVE-HEADLINE / OPEN-TRANSFER LABEL: V128 B7 router-refusal derived immediate authority repair proof completed at `BROAD_LIVE_AS_IF_REPLAY_V128_B7_ROUTER_REFUSAL_DERIVED_IMMEDIATE_AUTHORITY_REPAIR_20260601_20260605_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH`. Behavior: `35191` candidates, `480` scorecard rows, `212` order rows, `55` filled trades, `35085` missed rows, headline net `+1.12099062R`, gross/final `+6.22739670R`, cash PnL `+$3007.28429755`, risk cash `$24524.77867515`, W/L/F `38/17/0`, full/reduced `22/33`, fill realism `ordered_tick_entry_touch=53` and `source_safe_immediate_marketable=2`, zero broker/live/final authority. V128 versus V127B: trades `-54`, net `+8.62902381R`, added `32` trades for `+0.24238086R`, removed `86` trades for `-8.38664295R`, source-safe immediate fills fell from `71` to `2`. V128 versus V104: trades `+9`, net `-13.61002429R`, common canonical trades `0`, added `55` trades for `+1.12099062R`, removed all `46` V104 trades for `+14.73101491R`. Exact-window transfer: package/source-bound R `531411.6867472403R`, package axes `1101`, candidate-generated axes `888`, scorecard/order axes `33`, filled axes `23`, axis-attributed executable R `-1.06981543R`. `OUTPUT_MANIFEST.json` and `COMPLETION_AUDIT.json` now pin V128, `VERIFICATION_RESULT.json` is `ok=true`, `issue_count=0`, and final/live remain false. Interpretation: the V128 patch fixed the immediate-marketability leak, but it is not a B7 pass because V104 positive transfer remains absent and axis transfer is still negative.
- DONE: V128 action-intent authority truth repair after verifier parse. Producer patch preserves effective lifecycle/root action over stale original `new_position` in `src/research/moonshot_scheduler_v4_best_trade_allocator.py` and `src/research_infra/v4_timewarp_simulated_live_research_loop.py`; verifier consumer order now reads effective/lifecycle/root action before stale flat action in `verify_denominator_to_deployment_execution.py`. Focused tests passed: `tests/test_timewarp_scheduler_materialization.py::test_scheduler_lifecycle_action_aliases_are_canonicalized`, `tests/test_moonshot_scheduler_v4_best_trade_allocator.py -k "allocator_option_materialized_action_uses_effective_lifecycle_root or allocator_option_lifts_lifecycle_root_action_to_record"`, and the broader checkpoint sweeps `tests/test_moonshot_scheduler_v4_best_trade_allocator.py -k "marketable_entry_guard or router_refusal or allocator_option_materialized_action_uses_effective_lifecycle_root or allocator_option_lifts_lifecycle_root_action_to_record"` (`19 passed`), `tests/test_v4_timewarp_simulated_live_research_loop.py -k "router_refusal or immediate_marketable or open_reduced or lifecycle_action_attribution or materialized_action"` (`55 passed`), and `tests/test_broad_replay_repair_config.py` (`88 passed`). Behavior expectation: neutral for existing V128 ledgers, correctness-changing for future materialization; it prevents signed `replace_pending` authority from being misread as unauthorized `new_position`.
- DONE: V128 marketability/reduce-risk contract repair found during focused verification. `src/research_infra/v4_timewarp_simulated_live_research_loop.py::build_package_marketable_entry_guard` now matches scheduler behavior by blocking package marketable conversion when predecision limit fillability is unavailable/stale instead of returning `clear`, preserving off-configured raw-session route failure semantics. `src/research/reduced_risk_action_reason_contract.py` now maps `broker_net_admission_ev_below_full_trade_floor` to `reduce-risk` across scheduler/timewarp/config consumers. Focused proof: the two failing contracts now pass, the three broader checkpoint suites above pass, py_compile passes, route verifier exits `0` with `VERIFICATION_RESULT.json ok=true issue_count=0`, prompt hardening passes, route artifact audit reports `ok=true missing_required=[] missing_warnings=[]`, and `git diff --check` passes. Behavior expectation: no replay rerun for this checkpoint; this is a correctness/proof-surface repair before the next B7 transfer patch.
- DONE WITH LOCAL IMPROVEMENT / OPEN-TRANSFER LABEL: V129 B7 terminal-vs-soft transfer recovery authority-contract repair and targeted proof. Producer: `src/research/moonshot_scheduler_v4_best_trade_allocator.py` now materializes `scheduler_terminal_vs_soft_guard`, terminal vetoes, soft-guard vetoes, and soft reallocation pool status into allocator records instead of collapsing all guard vetoes into terminal rejection. Consumers/proof surfaces: `src/research_infra/v4_timewarp_simulated_live_research_loop.py` consumes the explicit soft/terminal split, blocks selected-policy replay before path simulation when the predecision executable-quality gate fails, carries the gate and soft/terminal fields into order, trade, and missed rows, and preserves empty terminal-veto lists as proof. Verifier: `verify_denominator_to_deployment_execution.py` now fatals terminal vetoes entering soft reallocation pools and selected-policy quality gates that use outcome fields, have bad source boundaries, or reach filled execution while blocked. Focused proof: py_compile passed for touched scheduler/timewarp/verifier/tests; `tests/test_v4_timewarp_simulated_live_research_loop.py -k "scheduler_soft_probe_consumes_terminal_vs_soft_guard_contract or scheduler_soft_probe_keeps_terminal_veto_non_executable or selected_policy_quality_gate_ignores_generic_geometry_without_policy_evidence or selected_policy_quality_gate_blocks_predecision_stop_hazard or risk_finalizer_blocks_selected_policy_hazard_before_selection or risk_finalizer_soft_probes_package_executable_runtime_ineligible_option or risk_finalizer_promotes_exact_bound_soft_probe_runtime_and_risk_intent or selected_execution_policy_replay_blocks_predecision_quality_failure_before_path or risk_finalizer_trade_trace_carries_execution_fillability_aliases or missed_risk_attribution_preserves_probe_route_provenance"` passed `10`; `tests/test_moonshot_scheduler_v4_best_trade_allocator.py -k allocator_option_preserves_terminal_vs_soft_guard_contract` passed `1`; `tests/test_denominator_to_deployment_verifier.py -k "broad_emitted_scheduler_status_authority_scan_flags_ranked_package_leak or broad_selected_policy_replay_authority_flags_quality_gate_leaks or broad_selected_policy_replay_authority_accepts_m1_diagnostic_replay or broad_selected_policy_replay_authority_still_flags_raw_replayed_unbound"` passed `4`; route verifier exited `0` with `VERIFICATION_RESULT.json ok=true issue_count=0`; prompt hardening returned `overall_ok=True`; route artifact audit returned `ok=true missing_required=[] missing_warnings=[]`. Targeted same-window proof: `BROAD_LIVE_AS_IF_REPLAY_V129_B7_TERMINAL_SOFT_SELECTED_POLICY_QUALITY_20260601_20260605_TARGETED_SOFT_TRANSFER` over `XAUUSD/XAGUSD/USDCAD/USDJPY/UKOIL_cash`, `2026-06-01..2026-06-05`, `repaired_package_conversion_v3`, broker/live/final false. It produced `6633` candidates, `480` scorecard rows, `16` order rows, `4` filled trades, `6625` missed rows, `62` source rows, headline net `+2.23793804R`, gross/final `+2.59834042R`, cash PnL `+$1403.02143841`, risk cash `$3267.86878739`, W/L/F `4/0/0`, trade frequency `0.8/day`, order statuses `filled=4`, `expired_unfilled=4`, selected-policy quality gate `passed=4`, soft-pool eligible filled trade count `1`, zero terminal-veto/cost-refused/source-gap execution, guarded fallback applied `0`. V129 targeted versus V128 same symbols: V128 had `7` trades for `+1.49366856R`; V129 has `4` trades for `+2.23793804R`; common `1`, added `3` for `+2.07253834R`, removed `6` for `+1.32826886R`, net delta `+0.74426948R`. V129 targeted versus V104 same symbols remains open: V104 had `32` trades for `+18.12379175R`; V129 has `0` common V104 keys, adds `4` for `+2.23793804R`, and still removes all `32` V104 same-symbol trades for `+18.12379175R`. Flow artifacts and V129-vs-V128 comparison artifacts are materialized. Interpretation: V129 is a correct local improvement over V128 and prevents the selected-policy stop-loss loser pattern seen in this subset, but it is not a B7 transfer pass because V104 positive transfer remains mostly unrecovered.
- PARTIAL / REGRESSED: V130 B7 source-bound authority transfer repair targeted proof completed at `BROAD_LIVE_AS_IF_REPLAY_V130_B7_SOURCE_BOUND_AUTHORITY_TRANSFER_REPAIR_20260601_20260605_TARGETED`. Same symbols/window/profile as V129, broker/live/final false. It produced `6633` candidates, `480` scorecard rows, `8` order rows, `3` filled trades, `6629` missed rows, `62` source rows, headline net `-2.41628102R`, gross/final `-2.09777975R`, cash PnL `-$2399.58774081`, risk cash `$2967.01037059`, risk pct `3.0`, W/L/F `0/3/0`, all fills `XAUUSD SHORT`, and zero executed broker/live/final claim. V130 versus V129 targeted: same candidate and scorecard counts, order rows `8` vs `16`, trades `3` vs `4`, net delta `-4.65421906R`; V130 added earlier source-bound/router-refusal XAUUSD shorts that all lost, while V129 winner keys remained generated/missed and were blocked by same-symbol lifecycle or adaptive memory guards. Interpretation: V130 is not a B7 pass. It exposed selector admission over-broadening plus downstream lifecycle/memory displacement, especially signature-only source-bound router-refusal immediate-marketability authority being treated as executable instead of diagnostic/missed unless the explicit derived-immediate replay flag is present.
- DONE AS FOCUSED B7 CORRECTNESS PATCH / AWAITING TARGETED REPLAY: Source-bound router-refusal immediate-marketability authority is now tightened across scheduler and timewarp consumers. Producer/consumer files: `src/research/moonshot_scheduler_v4_best_trade_allocator.py` requires `package_marketable_entry_guard_router_refusal_derived_immediate_marketable_limit_replay_authority_enabled` before source-bound router-refusal signatures can become immediate-marketable executable authority, and classifies `router_refusal_open_reduced_immediate_marketable_execution_authority_missing` as a terminal authority failure rather than a soft reallocation guard. `src/research_infra/v4_timewarp_simulated_live_research_loop.py` mirrors the same derived-flag requirement and emits explicit false authority booleans for non-derived source-bound rows. Focused proof: `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py src/research/moonshot_scheduler_v4_best_trade_allocator.py tests/test_v4_timewarp_simulated_live_research_loop.py tests/test_moonshot_scheduler_v4_best_trade_allocator.py` passed; `python3 -m pytest tests/test_moonshot_scheduler_v4_best_trade_allocator.py -k "scheduler_order_executable_false_carries_cost_blocker_class or marketable_entry_guard or router_refusal or allocator_option_preserves_terminal_vs_soft_guard_contract" -q` passed `19`; `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k "source_bound_router_refusal_materialization_requires_derived_immediate_flag_for_marketable_replay_authority or router_refusal_open_reduced_immediate_marketable_requires_execution_authority or runtime_risk_authority_does_not_use_route_resolution_to_bypass_full_risk_fill_floor or normalize_package_row_does_not_treat_risk_cap_release_as_final_blocker" -q` passed `4`. Behavior expectation: V130’s three source-bound/router-refusal immediate-marketable XAUUSD SHORT fills should be blocked or reallocated unless explicit derived-immediate authority is present; valid source-bound rows remain scoreable/missed and full 82-sleeve scoring is preserved. The next proof should be a targeted same-window replay, not a broad replay, unless this focused contract regresses.
- DONE AS B7 PROOF-SURFACE CORRECTNESS PATCH / TRANSFER STILL OPEN: V142 B7 missed namespace executable authority demotion proof completed at `BROAD_LIVE_AS_IF_REPLAY_V142_B7_MISSED_NAMESPACE_EXECUTABLE_AUTHORITY_DEMOTION_20260601_20260605_TARGETED`. Producer: `src/research_infra/v4_timewarp_simulated_live_research_loop.py` adds `ledger_namespace_synthesized_executable_candidate_use_allowed` to the non-executable missed authority demotion set. Consumer/verifier: `verify_denominator_to_deployment_execution.py` treats true synthesized namespace authority as claim-bearing under terminal veto, with focused coverage in `tests/test_denominator_to_deployment_verifier.py`. Focused tests passed: missed authority demotion `2 passed`; verifier scheduler-status authority scan `1 passed`; py_compile passed for touched timewarp/verifier/tests. Targeted replay behavior is neutral versus V141: `6633` candidates, `480` scorecards, `15` orders, `3` fills, `6626` missed, net `+0.84449709R`, W/L/F `3/0/0`, broker/live/final false. Proof effect: `2727` terminal-veto missed rows now have zero true effective/synthesized executable authority fields. Route verifier `ok=true`, `issue_count=0`, verified `2026-07-07T03:03:08Z`; prompt hardening and route artifact audit pass. Interpretation: V142 closes a ledger/verifier authority leak; it does not solve B7 transfer recovery.
- OPEN: 7.4 broad 19-day proof.
- OPEN: 7.5 extended history across at least two non-adjacent months.

Acceptance notes:
- All comparisons must be same-window and keyed by canonical replay candidate instance.
- Hard rejection: positive by trade collapse, window-specific config deltas, un-attributed removed winners, executed REFUSED/source-gap rows, interrupted summaries.

Behavior expectation:
- Proof ladder, not tuning. V125 proves B7.1 route truth and authority; V126 proves B7.2 hostile five-day route truth; V127B proves B7.3 non-hostile five-day route truth; V128 proves the router-refusal derived immediate-marketability repair locally; V129 closes terminal-vs-soft and selected-policy executable-quality authority contracts and improves the targeted V128 subset; V142 closes the terminal-veto missed-row synthesized executable namespace proof leak. B7 is still not ready for B7.4 because V142 did not recover the V104 positive transfer set. The next dependency is ranking the valid missed winners from the latest targeted missed/decision/order ledgers and patching the next lifecycle/order/reallocation blocker that prevented their transfer.

Subagent incorporation after V128:
- Gibbs incorporated: all `46/46` V104 canonical trade keys still exist in V128 candidate and missed ledgers, but `0/46` reach order/trade. `23` removed V104 keys are honest broker-cost refused under V128 and remain non-executable unless a B6 cost audit proves otherwise; the other `23` are recoverable B7 scheduler/materialization/lifecycle authority classes.
- Helmholtz incorporated: dominant transfer leak is scheduler-side terminalization before reallocation, not candidate disappearance. `candidate_generated_not_scheduler_selected` plus `candidate_generated_selector_reduce_risk_not_scheduler_selected` represent `291` axes and about `477831.440104R` effective source-bound leakage. V129 implements the terminal-vs-soft veto split and source-bound soft-guard reallocation pool contract; the next proof is targeted replay measurement.
- Plato incorporated: V128 `selected_policy_replay:stop_loss` has `13` ordered-tick fills for `-14.31653698R` despite calibrated expected-net/probability/fill/source-completeness. V129 adds selected-policy executable-quality admission before path simulation and fatal verifier coverage; the next proof is targeted replay measurement.
- Feynman incorporated: selected-policy replay gate now runs before `simulate_policy`, and order/trade/missed rows carry terminal-vs-soft plus selected-policy executable-quality fields. `RISK_FINALIZER_TRADE_TRACE_KEYS`, finalizer order authority copying, `selected_policy_replay_ledger_fields`, and missed attribution all preserve the new fields.
- Nash incorporated: cost/source-gap and broker/live/final fatal coverage was already present; V129 adds the missing explicit terminal-vs-soft and selected-policy executable-quality fatal verifier assertions.

## B8 - Live Path

Status: OPEN.

Requirements:
- OPEN: production-return dossier after B7.
- OPEN: live-shadow stage using the exact replay decision stack with `SimulatedBroker`.
- OPEN: canary micro-live only after shadow parity and owner strategic approval.
- OPEN: scale per dossier risk schedule.

Current authority:
- Broker/live/final stay closed. This matrix does not open live authority.

## Selected Next Batch

Selected next dependency batch: B7 full proof ladder.

Why:
- B0 is done.
- B1 is closed for current-stack dependency purposes.
- B2 is closed for current-stack dependency purposes.
- B3 is closed with a label: focused semantics, tests, June-3 proof, and non-June no-fill structural proofs show ladder truth is deterministic.
- B4 is closed with a label: V122J full tick-hydrated hostile five-day proof has realism-passing executable fills only, zero executed REFUSED/source-gap/M15-proxy/first-touch optimistic rows, and exact residual diagnostic labels.
- B5 is closed: V122J comparison/parity deltas are computed and V123 targeted summaries expose active replay denominator separately from configured universe.
- B6 is closed with a label: V123 targeted repair proves stale USDJPY floor/mapping rows now use raw historical tick authority while REFUSED rows remain non-executable.
- B7.1 is closed: V125 one-day June 3 proof has route verifier green and no broker/live/final, REFUSED/source-gap, selected-policy/profit-harvest, or package-executable authority leaks.
- B7.2 is closed with a negative behavior label: V126 hostile five-day proof has route verifier green and no broker/live/final, REFUSED/source-gap, selected-policy/profit-harvest, or package-executable authority leaks, but it worsens V122J by `-0.91168634R` net.
- B7.3 is closed with a negative behavior label: V127B non-hostile five-day proof has route verifier green and no broker/live/final or REFUSED/source-gap leaks, but it worsens V104 by `-22.23904810R` net and removes `+14.58298486R` of V104 trades while adding `-8.35722625R` of current-stack trades.
- V128 repairs the router-refusal derived immediate-marketability leak: V128 improves V127B by `+8.62902381R` and cuts source-safe immediate fills from `71` to `2`, but still trails V104 by `-13.61002429R`, has `0` common canonical trades with V104, and has axis-attributed executable R `-1.06981543R` inside the exact five-day denominator.
- V142 closes the latest proof-surface authority leak in the five-symbol targeted slice. It is behavior-neutral versus V141 at `3` trades / `+0.84449709R`, with zero cost-refused/source-gap/broker/live/final execution, and `2727` terminal-veto missed rows now carry zero true effective/synthesized executable authority fields. It still has not recovered V104 positive transfer.

Immediate B7 proof targets:
1. Patch the same-root B7 transfer leak that remains after V142: valid missed winner keys are still candidate/missed but not transferred; rank them from V142 candidate/missed/order/decision ledgers, separate honest broker-cost/source gaps from recoverable scheduler/materialization/lifecycle blockers, and patch the highest-leverage recoverable blocker.
2. Prove the repair with a targeted same-window bucket replay/comparison before broad replay.
3. Run B7.4 broad 19-day proof only after the targeted/short B7 slices are verifier-green and behavior is repaired or their blockers are exactly classified.

Expected B7 success:
- Same-window source-bound, candidate, scorecard/order, fill, missed, and actual R denominators are reported.
- No executed REFUSED/source-gap rows.
- No broker/live/final authority.
- Improvement is not positive by suppressing opportunity; added/removed trades, missed positive R, and missed negative R are separated.
- If the system is still losing, dominant leak buckets are exact and belong to a real next batch rather than stale B0-B6 truth issues.

Expected B7 failure:
- Any executed REFUSED/source-gap/live/final row.
- Positive behavior from trade collapse without opportunity transfer.
- New stale cost/fill/source/provenance mismatch that contradicts B0-B6 acceptance.
- Persistent losing behavior dominated by selected-transfer/exit/stop geometry after truth repairs, requiring a B7 policy repair batch before B8.
