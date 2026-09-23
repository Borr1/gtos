# MODULE FILE MAP — 19_typesafe_usage_ramp_every_gate

**as_of_ict:** `2026-09-21T06:45:00+07:00`  
**freshest tree:** `/workspace/gtos/close_loop/war_room_20260920/_pr41_land/ai-trading-agent/`  
**doctrine:** `JEV_EVERYWHERE_DOCTRINE_20260921.md`  
**gap inventory:** `JEV_COMPLETE_JUDGE_GAP_INVENTORY_20260921.md` (n=45)  
**never_broker_place:** true (this session DESIGN + PATCH DRAFTS only)

Owner fact: Typesafe Usage **~$0.11 / 666 req / 7d — TOO CHEAP**. This map is the evaluate() coverage graph: who POSTs `https://api.typesafe.ai/v1/systemone` today, who does not, and which env flags starve the path.

---

## 0. Why usage is cheap (measured from box mirrors)

| Cause | Evidence | Effect on 7d usage |
|---|---|---|
| Process budget **200** | `jev_client.DEFAULT_MAX_CALLS = 200`; skip `call_budget_exhausted` | Long-lived Challenge PID stops POSTing after 200 |
| Only **3 production modules** import `evaluate` | `a1_log.py`, `apply_size.py`, `challenge_shadow.py` | Most gates never hit TypeSafe |
| Observe is **late** | `book_owner.run_cycle` skips occupancy/weekend/already_placed **before** `maybe_observe_*` | Skipped candidates = 0 req |
| Observe is **env-gated** | `GTOS_JEV_A1_LOG` / `GTOS_JEV_ALIVE_SHADOW` before import | Flags off → 0 req |
| Fluid cycle **injects answers** | `cycle.run_fluid_gate_cycle(answers=…)` never calls `evaluate()` | Sidecar labels without POSTs |
| Policy C is **static 4-voter** | `policy_c_admit.evaluate_policy_c` — no `jev_client` | Refuse/trim without Typesafe |
| Sleeve select is **local menu** | `sleeve_select.build_sleeve_select_menu` — no POST | Shadow jsonl ≠ System One |
| S14 / world / rdf **payloads unwired** | `regime_system_one.py` docstring: “A live TypeSafe call is **not** made” | Packs exist, 0 req |
| Duplicate POSTs on survivors | `maybe_observe_ub_plc_017` ×3 + fluid inventory ×1 + haircut ×1 | Inflates survivor cost, not coverage |
| Compose **fail-open** on dark | `flow_alignment_size_tilt(None) → 1.0` | Dark Jev still fires full size |

**Live POST call sites (PR41 land):**

| file | function | when |
|---|---|---|
| `src/judgment/a1_log.py:102` | `observe()` | `a1_enabled()` then `evaluate(state)` |
| `src/judgment/a1_log.py:141` | `observe_fluid_inventory()` | same; **one** POST stamps 48 fluid ids |
| `src/judgment/apply_size.py:549` | `haircut_challenge_unit(..., evaluate_jev=True)` | `GTOS_JEV_APPLY_LIVE` path |
| `src/judgment/challenge_shadow.py:278` | `score_position()` | lab/replay, not writer fire |
| `scripts/jev_gold_lab.py` | lab harness | research |

`symbol_fanout_questions()` = **49** questions (alias of `gold_fanout_questions()`). Model `jev-1.13.0`. API `POST https://api.typesafe.ai/v1/systemone`.

---

## 1. Canonical Jev client + question packs

| path | functions / classes | env flags | into evaluate()? |
|---|---|---|---|
| `_pr41_land/.../src/judgment/jev_client.py` | `evaluate`, `max_calls`, `calls_enabled`, `resolve_key`, `_skip`, `_consume_call` | `TYPESAFE_API_KEY`, `TYPESAFE_KEY`, `TYPESAFE_KEY_FILE`, `GTOS_JEV_A1_CALL`, **`GTOS_JEV_MAX_CALLS` (default 200, mission 500000)** | **IS** the POST |
| `_pr41_land/.../src/judgment/jev_questions.py` | `gold_fanout_questions`, `symbol_fanout_questions`, `systemone_payload`, `A1_GATE_IDS`, `MODEL` | — | payload builder for `evaluate` |
| `_pr41_land/.../src/judgment/world_questions.py` | `world_systemone_payload` (16 Nouls) | `GTOS_JEV_WORLD_CALL` documented default-off | **NOT called** |
| `_pr41_land/.../src/judgment/rdf_questions.py` | `rdf_systemone_payload` (4 Nouls) | — | **NOT called** |
| `_pr41_land/.../src/judgment/regime_system_one.py` | `QUESTION_PACK`, `RegimeAnswerCache`, `SystemOneResult` | — | **explicitly no network** |
| `_pr41_land/.../src/judgment/everywhere.py` | `EVERYWHERE_QUESTION_PACK` (30 ids), `compose_everywhere` | `GTOS_JEV_EVERYWHERE_SHADOW` | injected answers only |
| `_pr41_land/.../tests/judgment/test_jev_client.py` | budget mock `GTOS_JEV_MAX_CALLS=2` | — | unit |

**Stale copies (same 200 budget, do not land from them):**

- `/workspace/gtos/_swarm_land_tip/land_pack/src_judgment/jev_client.py`
- `/workspace/gtos/_swarm_land_tip/extract/src/judgment/jev_client.py`
- `/workspace/gtos/_wave_m_fetch/src/judgment/jev_client.py`
- `/workspace/gtos/_size_apply_fetch/src/judgment/jev_client.py`

---

## 2. Observe / Alive path (A1)

| path | functions | env | call graph |
|---|---|---|---|
| `src/judgment/a1_log.py` | `a1_enabled`, `observe`, `observe_fluid_inventory`, `intent_gold_state`, `intent_symbol_state`, `maybe_observe_ub_auth_010`, `maybe_observe_ub_plc_017`, `maybe_observe_fluid_at_place`, `maybe_observe_fluid_at_admit`, `observe_sel_v4_002` | `GTOS_JEV_A1_LOG`, `GTOS_JEV_ALIVE_SHADOW`, `GTOS_JEV_A1_CALL`, `GTOS_JEV_A1_LOG_PATH`, `GTOS_JEV_HOST_EVENTS` | **→ evaluate()** |
| `src/judgment/aplus_pipe.py` | `maybe_observe_aplus_at_place`, `observe_aplus_candidate` | same A1 flags | → `observe` / `observe_fluid_inventory` |
| `src/judgment/a_plus_sleeve.py` | observe helpers | same | → `observe_fluid_inventory` |
| `src/judgment/host_sites.py` | `HOST_SITES`, `vps_land_plan` | — | maps UB-AUTH-010 / UB-PLC-017 / F5-JEV-004 / SEL-V4-002 / APLU-OBS-001 (`wired=False` on dirty host) |
| `src/components/ultimate_book/bridge.py` ~606–616 | `admit_and_size` hook | A1_LOG / ALIVE_SHADOW **before import** | → `maybe_observe_ub_auth_010` → 2 POSTs (observe + fluid inventory) |
| `src/components/ultimate_book/book_owner.py` ~2193–2283 | cost-screen hook | A1_LOG / ALIVE_SHADOW / APPLY_LIVE | → `maybe_observe_ub_plc_017` (3 POSTs) + `maybe_observe_fluid_at_place` (1 POST) + optional `haircut_challenge_unit` (1 POST) |

`observe_fluid_inventory` docstring: **“One System One call. Stamp every fluid gate id.”** That is the TypeSafe-correct fan-out. It is **not** 48 HTTP POSTs.

---

## 3. Writer / book_owner / admission (skip-before-observe)

| path | functions / reasons | env | evaluate()? |
|---|---|---|---|
| `src/components/ultimate_book/book_owner.py` | `run_cycle(place=)`, skip reasons listed below | writer flags; Jev only after cost screen | **no** until cost screen |
| `src/components/ultimate_book/book_engine.py` | `evaluate()` **governor/book** — not TypeSafe | — | name collision only |
| `src/components/ultimate_book/admission.py` | `evaluate_governor` reasons: `circuit_breaker_open`, `soft_daily_stop_reached`, `derisking_into_maxdd_wall`, `profit_target_protect_derisk`, `ceiling_profile_requires_smooth_ddefense`, `leader_impulse_veto` | `GTOS_UB_DERISK_MODE` | **no** |
| `src/judgment/host_occupancy.py` | `host_occupancy_governor` | — | feeds state, no POST |
| `src/judgment/occupancy.py` | occupancy_at / last_refusal_class | — | state only |

**book_owner skip reasons (STATIC; observe does not run):**  
`breach_flatten_block`, `kill_switch_or_halt_forced_observe_only`, `account_state_unavailable`, `profile_missing_instrument_config`, `weekend_entry_embargo`, `weekend_policy_clock_unavailable`, `already_placed_this_bar`, `already_placed_today`, `no_tick_transient`, `sleeve_already_holds_symbol`, `sleeve_already_holds_symbol_broker`, `same_broker_symbol_already_placed_this_cycle`, `same_broker_symbol_transient_attempt_this_cycle`, `same_broker_symbol_position_source_unavailable_for_lifecycle_guard`, `same_broker_symbol_open_position_lifecycle_guard`, `stale_late_entry_after_restart`, then `_spread_cost_screen` → `pretrade_spread_r_refuse`.  
`run_cycle(place=False)` returns after engine.evaluate **without** `maybe_observe_*`.

---

## 4. Size APPLY (partial live POST)

| path | functions | env | evaluate()? |
|---|---|---|---|
| `src/judgment/apply_size.py` | `haircut_challenge_unit`, `maybe_haircut_unit`, `physical_apply_allowed` | `GTOS_JEV_APPLY_LIVE=1` + login `0` / ns `operator` | **yes** if `evaluate_jev` |
| `src/judgment/compose.py` | `compose_shadow`, `flow_alignment_size_tilt`, `cost_hurtful_size_tilt` | — | consumes answers; **fail-open** if None |
| `src/judgment/ca_size.py` | `score_ca_size`, `ca_size_components` | CA-SIZ-001; APPLY still `GTOS_JEV_APPLY_LIVE` | **no POST** (uses injected/local) |
| `src/judgment/process_lock.py` | `APPLIED_WIRES`, `wire_apply_open`, `leave_orig_ticket` | prove receipts | envelope lock |
| `src/judgment/cross_asset.py` | CA labels | — | local compose |

Named live tilts: `f5_xau_flow_alignment_size_tilt`, `F5-JEV-004`, `ca_cross_asset_size_tilt`. Combined = flow × cost × ca. Cannot zero. Leave-orig `293332188` stays 1.0.

---

## 5. Fluid 48 / envelope 8 / cycle (shadow sidecar, usually no POST)

| path | functions | env | evaluate()? |
|---|---|---|---|
| `judgment/astra/JEV_GATE_INVENTORY.json` | n_fluid=48, n_envelope=8 | — | inventory |
| `src/judgment/fluid_gates.py` | `fluid_gate_ids`, `envelope_walls`, `inventory_counts` | — | ids only |
| `src/judgment/flags.py` | `shadow_enabled`, `apply_enabled`, `apply_authorized` | `GTOS_JEV_FLUID_GATES_SHADOW`, `GTOS_JEV_EVERYWHERE_SHADOW`, `GTOS_JEV_FLUID_GATES_APPLY` | no |
| `src/judgment/cycle.py` | `run_fluid_gate_cycle` | same + `GTOS_JEV_FLUID_GATES_LOG_DIR` | **no** (injected answers) |
| `src/judgment/conf_gate.py` | `log_conf_gate`, `confidence_band`, S15 cost | — | bands from injected conf |
| `src/judgment/alive_menu.py` | `rebuild_choice_criteria` | — | menu, no POST |
| `src/judgment/done_outside.py` | `completion_truth`, `verify_side_effect` | — | file verify |
| `src/judgment/p0_shadow_hooks.py` | `compose_warroom_shadow` | — | stubs, apply always false |
| `src/judgment/sites.py` | `PRE_EVERYWHERE_SITES`, `pre_everywhere_gaps` | — | site map |

Envelope wall ids (integers, not Jev toys): `ENV-KILL`, `ENV-TWO-STOP`, `ENV-TOKEN`, `ENV-H8`, `ENV-DD`, `ENV-US30`, `ENV-OCC`, `ENV-DEAD`.

---

## 6. Policy C / sleeve select (Jev-shaped, no evaluate POST)

| path | functions | env | evaluate()? |
|---|---|---|---|
| `/workspace/gtos/policy_c_activate_20260920/src/judgment/policy_c_admit.py` | `evaluate_policy_c`, `strike_when_right_choice` | `GTOS_JEV_POLICY_C_APPLY=1` | **NO** — static 4 voters |
| `policy_c_activate_20260920/notes/PR39_POLICY_C_APPLY_LAND_NOTE_20260920.md` | admission `_refuse(..., "policy_c_stand_down")` | — | hook claimed on Admin; **absent from `_pr41_land` admission.py** |
| `/workspace/gtos/judgment/warroom_shadow/src/judgment/sleeve_select.py` | `build_sleeve_select_menu`, `emit_sleeve_select_shadow_payload`, scoped APPLY helpers | `GTOS_JEV_SLEEVE_SELECT_SHADOW`, **`GTOS_JEV_SLEEVE_SELECT_APPLY` (DO NOT flip global)**, `GTOS_JEV_SLEEVE_SELECT_APPLY_XAU_CONFLICT`, `..._GBPJPY_CONFLICT` | **NO POST** |
| `judgment/warroom_shadow/src/judgment/cycle.py` | sleeve_select sidecar emit | fluid shadow | local jsonl |
| `judgment/warroom_shadow/src/judgment/alive_sleeves_for_symbol.py` | affinity menu | — | no POST |

---

## 7. Chair / two-stop / veto / news honesty

| path | functions | env | evaluate()? |
|---|---|---|---|
| `src/judgment/chair_enforce.py` | `is_hard_off_sleeve`, G1–G8 | — | integer labels |
| `src/judgment/two_stop.py` | `F5_SAME_SLEEVE_ORIG_STOP_DAY_CAP=2`, `occupancy_from_closed` | `GTOS_JUST_CLOSED_SIBLINGS` | integer COUNT |
| `close_loop/war_room_20260920/two_stop_day_circuit.py` (if present on war_room) | WMB 2-stop | — | STATIC refuse remint |
| `src/judgment/veto.py` | `JevPlacePathVeto`, `InventedNewsProtocolVeto`, `refuse_invented_news_protocol` | — | **blocks place + NEWS_PROTOCOL invent** |
| `src/judgment/host_events.py` | `news_inventory_extra`, `news_inventory_at` | `GTOS_JEV_HOST_EVENTS` | honesty join, no invent |
| `src/judgment/news_spine.py` | `load_spines` | — | empty spine ≠ no HIGH |
| `src/judgment/challenge.py` | `CHALLENGE_LOGIN=0`, hard-off / keep families | — | identity envelope |
| `src/judgment/research_armed.py` | `MODULE_ATR_WINNER_TAGS` | — | overlay only; not live_armed_set |

---

## 8. State assemblers (COMPLETE_STATE feed)

| path | role |
|---|---|
| `src/judgment/gold_state.py` | `assemble_gold_state_v0` (XAU) |
| `src/judgment/symbol_state.py` | `assemble_symbol_state_v0` (non-XAU) |
| `src/judgment/world_state.py` | `assemble_world_state_v0` |
| `src/judgment/rates_dxy_funding.py` | RDF pack (yield often unassembled — honest null) |
| `src/judgment/bars.py` | Challenge tape loaders — **April historical never Challenge** |
| `src/judgment/sleeve_from_tape.py` | sleeve features from M15/H4 |
| `src/judgment/family.py` | family_class / hard_off / keep |
| `src/judgment/pack2_fields.py` … `pack6_fields.py`, `chair_fields.py`, `chair_wires.py` | A+ / Edge packs as **inputs not refuse walls** |

Gap-inventory COMPLETE_STATE draft v0 fields: `symbol`, `broker_symbol`, `session_day`, `decision_bar_iso`, `session_bucket`, `alive_sleeves`, `alive_menu`, `selected_sleeve_candidate`, `conflict_set`, `regime_tag`, `conf_band`, `session_fit`, `phi`, `phi_by_sleeve`, `cost`, `occupancy`, `account`, `hard_off_hit`, `remint`, `news_join` (STATE_MISSING OK), `full_state_dark`, `n_incomplete`, `place_context`.

---

## 9. Challenge tape / Module_ATR hist (present on box)

**Challenge-true bars (do not use April `data/historical*`):**

- `_pr41_land/.../judgment/astra/lab/challenge_shadow_20260917/` — `XAUUSD_{M15,H4,D1}.csv`, `sit_20260917.json`, `deals_since_20260909.jsonl`, `events_since_20260915.jsonl`, `shadow.jsonl`
- `.../challenge_shadow_20260917/multi/` — M15 for EURGBP, XAUUSD, US30_cash, USDJPY, BTCUSD, EURUSD, UK100_cash, GBPUSD, GBPJPY, ETHUSD
- `/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/` — peer M15 set (no GBPJPY in box root sample)

**Module_ATR blotters (separate R universe — never merge Dig_3R / Edge_ATR):**

| blotter | n |
|---|---|
| `blotter_Module_ATR_XAUUSD_dsp_three_fresh_lower_lows.jsonl` | 11239 |
| `blotter_Module_ATR_XAUUSD_dsp_spring_close_on_20low_through_the_box.jsonl` | 5659 |
| `blotter_Module_ATR_GBPJPY_vss_fxcross_london_proxy.jsonl` | 818 |
| `blotter_Module_ATR_GBPJPY_sub_mid_dn_re_proxy_SHORT.jsonl` | 2057 |
| `blotter_Module_ATR_XAGUSD_metal_session_reversion_20260920.jsonl` | 782 |
| `blotter_Module_ATR_XAGUSD_metals_core_20260920.jsonl` | 16 |
| `blotter_Module_ATR_XAGUSD_sub_xvol_pullback_20260920.jsonl` | 5 |

**Hist prove receipts:**

- `JEV_SLEEVE_SELECT_HIST_PROVE_V2_20260920.json` — **global FAIL**; XAU conflict PASS
- `JEV_SLEEVE_SELECT_SCOPED_XAU_APPLY_RECEIPT_20260920.json` — scoped APPLY recommended; **global APPLY=0**
- XAU Module_ATR day three_fresh×spring: n_conflicts=**2353**, sumR_select=**+235.36**, keep_all=**-74.72**
- Module_ATR combined conflicts: n=2366, select +1161.99 **does not** beat keep_all +2275.74 (EURUSD PackageB cell poisons global)

VPS Admin `host-local\redacted_host\repo` and live machineId `7cfa9657-805b-4e9c-9fbb-886c500f997b` are **UNREACHABLE this seat** (no host-mesh SSH). Confirm live `GTOS_JEV_*` / usage dashboard on host when online.

---

## 10. Call graph (evaluate / writer)

```
writer book_owner.run_cycle(place=?)
  ├─ book_engine.evaluate()          # NOT TypeSafe
  ├─ skip reasons (weekend, occupancy, already_placed, …)   # NO jev POST today
  ├─ _spread_cost_screen → cost_skip
  ├─ [if A1_LOG|ALIVE_SHADOW]
  │     maybe_observe_ub_plc_017 → observe×3 → jev_client.evaluate×3
  │     maybe_observe_fluid_at_place → observe_fluid_inventory → evaluate×1
  ├─ [if APPLY_LIVE and cost_skip is None]
  │     haircut_challenge_unit → evaluate×1 → compose_shadow → size tilt
  └─ router.place()                  # WRITER ONLY — this session never calls

bridge.admit_and_size
  └─ [if A1_LOG|ALIVE_SHADOW] maybe_observe_ub_auth_010 → evaluate×2

cycle.run_fluid_gate_cycle
  ├─ evaluate_s14 (cache/inject, no network)
  ├─ compose_everywhere (inject)
  └─ LABEL sidecar json            # NO evaluate()

policy_c_admit.evaluate_policy_c    # STATIC 4-voter, NO evaluate()
sleeve_select.build_sleeve_select_menu  # local Choice menu, NO evaluate()
challenge_shadow.score_position     # LAB: evaluate() per row
```

---

## 11. Env flag draft (usage ramp)

| flag | now (claimed / code) | draft |
|---|---|---|
| `GTOS_JEV_MAX_CALLS` | default **200** | **500000** |
| `GTOS_JEV_A1_CALL` | default-on if key present | keep; `0` = explicit off |
| `GTOS_JEV_A1_LOG` / `ALIVE_SHADOW` | claimed 1 on Challenge | keep |
| `GTOS_JEV_APPLY_LIVE` | claimed 1 Challenge-only | keep; no W7 |
| `GTOS_JEV_POLICY_C_APPLY` | claimed 1 | keep; **add real evaluate() POST** |
| `GTOS_JEV_FLUID_GATES_SHADOW` | claimed 1 | keep |
| `GTOS_JEV_FLUID_GATES_APPLY` | LABEL draft | keep LABEL; no place |
| `GTOS_JEV_SLEEVE_SELECT_SHADOW` | 1 | keep |
| `GTOS_JEV_SLEEVE_SELECT_APPLY` | **0** | **DO NOT flip global** |
| `GTOS_JEV_USAGE_RAMP_OBSERVE` | **missing** | **1** — observe every candidate + halt cycles |
| `GTOS_JEV_FANOUT_DEDUP` | missing | **1** — one fanout POST per candidate_fp |
| `GTOS_JEV_PER_GATE_POST` | missing | **0** default (TypeSafe fan-out); 1 = ablation |
| `GTOS_JEV_FAIL_CLOSED_DARK` | missing | **1** — dark Jev → STAND / no size-up |
| `GTOS_JEV_FLUID_CYCLE_CALL` / `S14_CALL` / `WORLD_CALL` / `RDF_CALL` / `SLEEVE_SELECT_CALL` / `CONF_GATE_CALL` | missing or default-off | **1** on Challenge observe |

---

## 12. Do-not (this session)

- No `order_send` / `router.place` / broker from tools.
- No invent `NEWS_PROTOCOL`.
- No global `GTOS_JEV_SLEEVE_SELECT_APPLY=1`.
- No silent hard-off flips.
- No merge Dig_3R R into Module_ATR R.
- No live APPLY land claimed — Chair verbs only.
- No redacted_account / W7 book edits.
