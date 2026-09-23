# MODULE FILE MAP — 20_whole_code_envelope_audit

**as_of_ict:** 2026-09-21T06:06:14+07:00  
**session:** `20_whole_code_envelope_audit`  
**posture:** DESIGN + PATCH DRAFTS + hist-prove plans only. `place=false`. Never broker / `order_send`.  
**VPS live tree:** UNREACHABLE this seat (`machineId 7cfa9657-805b-4e9c-9fbb-886c500f997b`). Mirrors only.

Freshest fire-path: `_pr41_land/ai-trading-agent` ultimate_book + judgment **mtime 2026-09-20 20:29 ICT**.  
Freshest sleeve_select: `VPS_LAND_SCOPED_APPLY_20260921/sleeve_select.py` **mtime 2026-09-21 05:53**.  
Policy C: `policy_c_activate_20260920` (not imported by PR41 `admission.py`).

---

## 1. Call graph into `evaluate()` / writer

```
run_book.py::main()
  └─ UltimateBookOwner.run_cycle(place=…)
       ├─ BookEngine.evaluate()                    # intents + generation_skips
       │    └─ bridge._decide → admission.admit_and_size
       │         └─ [GTOS_JEV_A1_LOG|ALIVE_SHADOW]
       │              a1_log.maybe_observe_ub_auth_010
       │                └─ observe_fluid_inventory → jev_client.evaluate(state)
       └─ per intent (place loop):
            _weekend_entry_block / occupancy / cost_screen
            [shadow] a1_log.maybe_observe_ub_plc_017
                     a1_log.maybe_observe_fluid_at_place
                       └─ observe / observe_fluid_inventory → jev_client.evaluate(state)
            [GTOS_JEV_APPLY_LIVE + Challenge login/ns]
                 apply_size.haircut_challenge_unit(evaluate_jev=True)
                   └─ jev_client.evaluate(state) → compose_shadow → maybe_haircut_unit
            router.place(...)                      # writer prints; this session never calls it

Parallel sidecar (not broker place):
  cycle.run_fluid_gate_cycle
    AliveMenu → evaluate_s14 (regime_system_one.call_system_one — NOT jev_client)
    → log_conf_gate → compose_everywhere / compose_warroom_shadow
    → optional sleeve_select.emit_sleeve_select_shadow_payload
    → done_outside
```

**Who actually POSTs `jev_client.evaluate()` today (PR41 land):**

| caller | when |
|---|---|
| `a1_log.observe` / `observe_fluid_inventory` | `GTOS_JEV_A1_LOG` or `GTOS_JEV_ALIVE_SHADOW` |
| `apply_size.haircut_challenge_unit` | `GTOS_JEV_APPLY_LIVE=1` + login `0` / ns `operator` |
| `challenge_shadow.py` | Challenge-true tape scorer (research) |

**POST gap (catch-all):** `regime_system_one.call_system_one` is offline/cache/injected — S14 does **not** hit `https://api.typesafe.ai/v1/systemone` via `jev_client`. Policy C / sleeve_select / two_stop helper are **not imported** by PR41 `admission.py` / `book_owner.py`.

Endpoint: `https://api.typesafe.ai/v1/systemone`  
Questions: `jev_questions.symbol_fanout_questions()` (alias of `gold_fanout_questions()`)  
Model: `jev-1.13.0`  
Budget in code: `GTOS_JEV_MAX_CALLS` default **200** — owner/session 19 raised to **500000** (residual).  
Fail-closed skips: `TYPESAFE_key_absent`, `GTOS_JEV_A1_CALL_off`, `call_budget_exhausted`. Never raises into fire path.

---

## 2. Judgment core (`_pr41_land/.../src/judgment/`)

| path | functions / classes | flags | evaluate()? | notes |
|---|---|---|---|---|
| `jev_client.py` | `evaluate`, `resolve_key`, `calls_enabled`, `max_calls`, `_skip` | `GTOS_JEV_A1_CALL`, `GTOS_JEV_MAX_CALLS`, `TYPESAFE_*` | **defines** | POST; never raises |
| `jev_questions.py` | `gold_fanout_questions`, `symbol_fanout_questions`, `systemone_payload` | — | no | `A1_GATE_IDS`; MODEL `jev-1.13.0` |
| `flags.py` | `shadow_enabled`, `apply_enabled`, `apply_authorized`, `load_prove_receipt` | `GTOS_JEV_FLUID_GATES_{SHADOW,APPLY,PROVE_DIR}`, `GTOS_JEV_EVERYWHERE_SHADOW` | no | LABEL/REVIEW only; `veto_place_path` |
| `a1_log.py` | `observe`, `observe_fluid_inventory`, `maybe_observe_ub_auth_010`, `maybe_observe_ub_plc_017`, `maybe_observe_fluid_at_place` | `GTOS_JEV_A1_LOG`, `ALIVE_SHADOW`, `A1_LOG_PATH`, `HOST_EVENTS` | **yes** | Fire-path observe; stamps `never_place` |
| `apply_size.py` | `haircut_challenge_unit`, `physical_apply_allowed`, `apply_live_env` | `GTOS_JEV_APPLY_LIVE`, `APPLY_RECEIPT_PATH` | **yes** | Challenge-only lots haircut |
| `ca_size.py` | `ca_size_components`, `score_ca_size` | — | no | 7 CA labels; clamp `[0.70,1.00]` |
| `compose.py` | `compose_shadow`, `flow_alignment_size_tilt`, `cost_hurtful_size_tilt` | uses APPLY wires | no | flow × cost × ca |
| `process_lock.py` | `wire_apply_open`, `leave_orig_ticket`, `APPLIED_WIRES` | `GTOS_JEV_W_NAMED`, `GTOS_JEV_W_PROVE_PATH` | no | `WIRE_FLOW`, `WIRE_COST`, `WIRE_CA_SIZE`; leave-orig `293332188` |
| `fluid_gates.py` | `load_inventory`, `fluid_gate_ids`, `envelope_walls` | — | no | 48/8 lock |
| `fluid_pipeline.py` | `pipeline_snapshot`, `may_auto_apply` | — | no | status/ledger |
| `cycle.py` | `run_fluid_gate_cycle` | fluid SHADOW/APPLY/LOG_DIR | no | sidecar ALIVE→CONF→S14/S15→P0 |
| `gold_state.py` | `assemble_gold_state_v0`, `reject_expost` | — | no | COMPLETE_STATE gold body |
| `symbol_state.py` | `assemble_symbol_state_v0` | — | no | per-symbol |
| `world_state.py` | `assemble_world_state_v0`, `attach_world` | — | no | desk/world |
| `rates_dxy_funding.py` | `assemble_rates_dxy_funding_v0` | — | no | USDJPY stand-in; no FRED |
| `cross_asset.py` | `local_cross_asset_answers` | — | no | CA world fields; missing peer = null not 0.0 |
| `conf_gate.py` | `confidence_band`, `log_conf_gate`, `log_cost_of_error` | — | no | place stake VETO (doctrine residual) |
| `regime_gate.py` | `evaluate_s14` | — | **no jev_client** | offline `call_system_one` |
| `regime_system_one.py` | `call_system_one`, `RegimeAnswerCache` | — | no | POST gap |
| `regime_buckets.py` / `regime_compose.py` | emit + compose | — | no | S14 labels |
| `chair_enforce.py` | `hard_off_reason`, `stamp_chair_enforce`, `is_hard_off_sleeve` | — | no | 6 hard-off reasons + G8 remint notes |
| `chair_wires.py` / `chair_fields.py` | `assemble_chair_wires`, PACK fold | — | no | LABEL family; not admit Choice |
| `pack2_fields.py` … `pack6_fields.py` | `assemble_packN_fields`, gate maps | — | no | LABEL inputs; PACK6 mute honesty |
| `occupancy.py` | `occupancy_at`, `corr_hold_at` | — | no | tape labels; KEEP-one stays integer |
| `two_stop.py` | `two_stop_exhausted`, `same_sleeve_orig_stop_count_session_day` | `GTOS_JUST_CLOSED_SIBLINGS` | no | closed[] COUNT |
| `veto.py` | `refuse_broker_action`, `refuse_invented_news_protocol`, `refuse_raw_tick_dump_to_jev` | — | no | **eternal never_place docstring = residual vs owner override** |
| `p0_shadow_hooks.py` | `compose_warroom_shadow` | cites FLUID APPLY / DIG APPLY (must stay unset) | no | P0 Choice/Noul stamps; `apply=false` |
| `s16_guard.py` / `s16_flags.py` | `run_screen`, `assess_action` | `GTOS_DIG_MULTI_STAGE_GUARD_*` | no | Dig harness; ≠ fluid flags |
| `host_events.py` | `load_host_events`, `news_inventory_extra` | `GTOS_JEV_HOST_EVENTS`, `GTOS_CHALLENGE_EVENTS` | no | empty spine ≠ no HIGH |
| `news_spine.py` / `news_calendar_sync.py` | `attach_news`, `sync_from_spine` | — | no | STATE_MISSING honesty |
| `everywhere.py` | `compose_everywhere`, `surface_map` | everywhere/fluid shadow | no | fan-out labels |
| `sites.py` | `PRE_EVERYWHERE_SITES`, `pre_everywhere_gaps` | — | no | place/remint/flatten still listed Infinity VETO |
| `alive_menu.py` | `AliveMenu`, `rebuild_choice_criteria`, `StaleMenuError` | — | no | Session 10 |
| `family.py` | `family_class_for`, `HARD_OFF_FAMILIES` | — | no | |
| `challenge.py` | `CHALLENGE_LOGIN`, `CHALLENGE_HARD_OFF_FAMILIES` | — | no | login 0 |
| `cf_d.py` / `cf_priority.py` | `compose_cf_d`, `label_cf_priority` | — | no | CF-D SHADOW; sites.py gap |
| `aplus_pipe.py` / `a_plus_sleeve.py` / `aplus_sleeve.py` | `observe_aplus_candidate`, `APLU-OBS-001` | A1_LOG | via a1 | catalog ≠ TradeIntent |
| `edge_freeze.py` | `assert_edge_freeze`, `GBPJPY_READY`, `XAU_READY` | — | no | LABEL readiness |
| `research_armed.py` | `MODULE_ATR_WINNER_TAGS` | — | no | three_fresh + spring overlay; not live_armed_set |
| `learn_loop.py` | harvest observer | `GTOS_JEV_LEARN_LOOP` | maybe | session 18 |
| `harvest_patterns.py` / `harvest_prove.py` | tape harvest | — | no | session 18 |
| `done_outside.py` | `completion_truth`, `verify_side_effect` | — | no | code DONE owns |
| `host_occupancy.py` / `host_sites.py` | `host_occupancy_governor`, `HOST_SITES` | — | no | occupancy pack for a1 |
| `inventory.py` | `collect_live_inventory` | — | no | |
| `non_xau_remeasure.py` | remasure helpers | forces `GTOS_JEV_A1_CALL=0` in one path | no | |
| `shadow_unlock.py` / `wire_prove.py` / `p0_hist_prove.py` | prove helpers | — | no | |
| `challenge_shadow.py` | `score_position`, `score_sit` | — | **yes** | research scorer |

Inventory JSON: `_pr41_land/.../judgment/astra/JEV_GATE_INVENTORY.json` — **n_fluid=48, n_envelope=8**, `never_place=true` (doctrine residual). Older Fable MD (`mac_ports_…`) claims 94/59/40 — **do not use**.

---

## 3. Ultimate book writer (`src/components/ultimate_book/`)

| path | functions | flags | evaluate()? | notes |
|---|---|---|---|---|
| `book_owner.py` | `UltimateBookOwner.run_cycle`, `_spread_cost_screen`, `_weekend_entry_block` | A1_LOG, ALIVE_SHADOW, APPLY_LIVE | via a1/apply | skip ledger (inventory + residuals) |
| `book_engine.py` | `BookEngine.evaluate`, `_spread_geometry_refusal`, `_entry_hour_deferral` | spread_geometry_floor, entry_hour | no | generation_skips |
| `admission.py` | `admit_and_size`, `evaluate_governor`, `size_correlated_units` | `GTOS_UB_DERISK_MODE` | no | governor + silent drops |
| `bridge.py` | `_decide`, triple-gate, `maybe_observe_ub_auth_010` | A1/ALIVE | via a1 | after final decide |
| `weekend_policy.py` | `WeekendPolicy`, `entry_blocked` | default-OFF FTMO | no | redacted_account funded-phase |
| `metals_confluence_gate.py` | `metals_confluence` | default-off | no | A8 K=3-of-4 **silent drop** |
| `symbol_damage_guard.py` | `classify_symbol_health`, `damage_multiplier` | default-off | no | quarantine **silent** |
| `spread_geometry.py` | `evaluate_intent` | default-off floor | no | generation refuse |
| `entry_hour.py` | `deferral_reason` | default-off | no | DELAY native |
| `packet_guard.py` | `GuardedPacketWriter` | — | no | learning packets; never stop book |
| `order_router.py` | `place` | — | no | `geometry_unavailable`, `open_trade_returned_none` |
| `governor_state.py` | GovernorState | — | no | |
| `sleeves/registry.py` | BUILT / CANDIDATE_BUILT | — | no | identity menu |

Also: `src/components/execution.py` send-path reasons (`runtime_halt_blocked`, `pretrade_cost`, `exec_mgr_v4`, `order_rejected`, …).

---

## 4. Land packs outside PR41 (must be in union)

| path | functions | flags | evaluate()? | notes |
|---|---|---|---|---|
| `/workspace/gtos/policy_c_activate_20260920/src/judgment/policy_c_admit.py` | `evaluate_policy_c`, `strike_when_right_choice` | `GTOS_JEV_POLICY_C_APPLY` | no | **not imported by PR41 admission** |
| `/workspace/gtos/close_loop/war_room_20260920/VPS_LAND_SCOPED_APPLY_20260921/sleeve_select.py` | `emit_sleeve_select_shadow_payload`, `resolve_scoped_conflict_choice` | `GTOS_JEV_SLEEVE_SELECT_{SHADOW,APPLY,APPLY_XAU_CONFLICT,APPLY_GBPJPY_CONFLICT,APPLY_EURUSD_KEEP_ALL}` | no | freshest 05:53 ICT |
| `/workspace/gtos/close_loop/war_room_20260920/VPS_LAND_JEV_SLEEVE_SELECT_20260920/src/judgment/sleeve_select.py` | same family | same | no | 05:51 ICT |
| `/workspace/gtos/judgment/warroom_shadow/src/judgment/sleeve_select.py` | shadow sidecar | same | no | |
| `/workspace/gtos/close_loop/war_room_20260920/two_stop_day_circuit.py` | `refuse_reason` | — | no | **helper unwired into PR41 book_owner** |
| `/workspace/gtos/close_loop/war_room_20260920/alive_sleeves_for_symbol.py` | `alive_sleeves_for_symbol` | `GTOS_RELAX_TO_JEV`, `GTOS_INCLUDE_CANDIDATE_BUILT` | no | menu for select |
| `/workspace/gtos/run_book.py` (PR41) | `main` | — | no | constructs owner |

---

## 5. Env flags (union)

**Jev / fluid / size / select**

| flag | role |
|---|---|
| `GTOS_JEV_A1_LOG` / `GTOS_JEV_ALIVE_SHADOW` | fire-path observe (env before import) |
| `GTOS_JEV_A1_CALL` | POST on/off (0=off; 1 or key→on) |
| `GTOS_JEV_MAX_CALLS` | POST budget (code default 200; owner 500000) |
| `GTOS_JEV_A1_LOG_PATH` | A1 JSONL |
| `GTOS_JEV_APPLY_LIVE` | physical Challenge haircut |
| `GTOS_JEV_APPLY_RECEIPT_PATH` | apply receipt |
| `GTOS_JEV_FLUID_GATES_SHADOW` / `_APPLY` / `_PROVE_DIR` / `_LOG_DIR` | sidecar |
| `GTOS_JEV_EVERYWHERE_SHADOW` | alias of fluid shadow |
| `GTOS_JEV_SLEEVE_SELECT_SHADOW` | select shadow |
| `GTOS_JEV_SLEEVE_SELECT_APPLY` | **global APPLY — DO NOT flip** |
| `GTOS_JEV_SLEEVE_SELECT_APPLY_XAU_CONFLICT` | scoped XAU |
| `GTOS_JEV_SLEEVE_SELECT_APPLY_GBPJPY_CONFLICT` | scoped GBPJPY |
| `GTOS_JEV_SLEEVE_SELECT_APPLY_EURUSD_KEEP_ALL` | scoped EURUSD KEEP_ALL |
| `GTOS_JEV_POLICY_C_APPLY` | Policy C refuse on stand-down (claimed ON) |
| `GTOS_JEV_HOST_EVENTS` / `GTOS_CHALLENGE_EVENTS` | host events.jsonl |
| `GTOS_JEV_LEARN_LOOP` / `_PATH` | harvest |
| `GTOS_JEV_W_NAMED` / `GTOS_JEV_W_PROVE_PATH` | named-wire prove |

**Draft flags (this session — not live):** `GTOS_JEV_HOLD_EXIT_SHADOW`, `GTOS_JEV_TWO_STOP_REMINT_SHADOW`, `GTOS_JEV_PRETRADE_COST_SHADOW`, `GTOS_JEV_OCCUPANCY_REMINT_SHADOW`, `GTOS_JEV_HARD_OFF_EXCEPTION_SHADOW`, `GTOS_JEV_ADMISSION_SCORE_SHADOW`, `GTOS_JEV_PLACE_FLUID_SHADOW`, `GTOS_JEV_ENTRY_HOUR_SHADOW`, `GTOS_JEV_CLUSTER_CAP_SHADOW`, `GTOS_JEV_COMPANION_*_SHADOW`, `GTOS_JEV_CONF_GATE_APPLY` (after hist only).

**Non-Jev:** `GTOS_DIG_MULTI_STAGE_GUARD_*`, `GTOS_UB_DERISK_MODE`, `GTOS_RELAX_TO_JEV`, `GTOS_INCLUDE_CANDIDATE_BUILT`, `GTOS_JUST_CLOSED_SIBLINGS`.

---

## 6. Challenge / Module_ATR tape paths (honesty)

Present under `/workspace/gtos/close_loop/war_room_20260920/`:

- `blotter_Module_ATR_XAUUSD_dsp_three_fresh_lower_lows.jsonl`
- `blotter_Module_ATR_XAUUSD_dsp_spring_close_on_20low_through_the_box.jsonl`
- `blotter_Module_ATR_GBPJPY_vss_fxcross_london_proxy.jsonl`
- `blotter_Module_ATR_GBPJPY_sub_mid_dn_re_proxy_SHORT.jsonl`
- `blotter_Module_ATR_XAGUSD_{metals_core,metal_session_reversion,sub_xvol_pullback}_20260920.jsonl`
- `JEV_SLEEVE_SELECT_HIST_PROVE_V2_20260920.{md,json}` — XAU conflict PASS; combined FAIL
- `JEV_SLEEVE_SELECT_SCOPED_XAU_APPLY_RECEIPT_20260920.{md,json}`
- `CF_C_MODULE_ATR_XAU_THREE_FRESH_SPRING_SCOREBOARD_20260920.{md,json}`
- `GROK_KEEP_HIST_PROVE_20260920/`

**Do not merge Dig3R R into Module_ATR sumR.** Dig3R pack is cite-only: `CF_COUNTERFACTUAL_SCOREBOARD_ABSORB_DIG3R_20260920.json`.

Host writer events (may be missing on box): `shadow_logs/f5_minimal/operator/events.jsonl` — honest STATE_MISSING if absent.

---

## 7. Sessions 01-19 vs this catch-all

See `UNION_COVERAGE_MATRIX.md` + `DECISION_REASON_WIRES.json`.  
Sibling session OUT dirs had **no** `DONE.json` / `DECISION_REASON_WIRES.json` at audit time — union is independently rescanned from mirrors + prompts, not a merge of unfinished session receipts.
