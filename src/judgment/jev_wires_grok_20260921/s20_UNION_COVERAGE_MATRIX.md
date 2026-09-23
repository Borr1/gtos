# UNION COVERAGE MATRIX + MISSING LIST

**session:** `20_whole_code_envelope_audit`  
**baseline inventory:** n=45 (`JEV_COMPLETE_JUDGE_GAP_INVENTORY_20260921`) — JEV_JUDGED=5, STATIC=33, SHADOW=7  
**union (this catch-all):** see `DECISION_REASON_WIRES.json`

| metric | n |
|---|---:|
| union reasons (unique keys) | **225** |
| covered by sessions 01-19 prompts (assigned) | 95 |
| residual catch-all (not in 01-19 dedicated focus) | **130** |
| duplicate keys | 0 |
| orphans (unclassified) | **0** |
| class_now JEV_JUDGED | 9 |
| class_now STATIC_CODE | 78 |
| class_now SHADOW_ONLY | 102 |
| class_now ENVELOPE | 36 |
| proposed JEV_WIRE | 148 |
| proposed ENVELOPE_KEEP | 77 |

No reason left without `JEV_WIRE` or `ENVELOPE_KEEP`.

---

## A. Gap inventory n=45 → session owner

| module | reason | class_now | session |
|---|---|---|---|
| policy_c_admit | policy_c_stand_down / incomplete_state / state_sufficient / STATE_MISSING | JEV_JUDGED | 05 (+11 news) |
| sleeve_select | jev_sleeve_select_shadow, scoped_xau, scoped_gbpjpy, refused_alias, soft_relax | SHADOW/STATIC | 03 (+09) |
| two_stop | wmb_2stop_day_circuit_… | STATIC | 08 |
| chair_enforce | 6× chair_*_hard_off | STATIC | 09 |
| book_owner | 18 lifecycle/place/occupancy/weekend/halt | STATIC | 01 / 15 / 16 |
| admission | 6 governor/derisk | STATIC | 02 / 17 |
| apply_size | jev_size_tilt_live | JEV_JUDGED | 06 |
| ca_size | ca_size_shadow | SHADOW | 06 |
| fluid_gates | fluid_inventory_48 (lumped) | SHADOW | 04 |
| conf_gate | conf_gate_shadow_bands | SHADOW | 07 |
| fluid_place | FLUID-PLC-001..007_label | SHADOW | 04+14 |

Cross-cutting (no extra inventory row): 10 COMPLETE_STATE, 11 news honesty, 12 writer observe, 13 affinity, 18 train-row, 19 usage ramp.

---

## B. Expanded 48 fluid IDs (inventory lumped these)

| family | ids | 01-19? | residual? |
|---|---|---|---|
| admit | FLUID-ADM-001..012, UB-AUTH-010, SEL-V4-002 | mostly 04/05 | **ADM-008 a8_agrees**, **SEL-V4-002 research_only** |
| size | f5_xau_flow…, F5-JEV-004, FLUID-SIZ-003..008 | 06 | no (family covered) |
| place_fluid | FLUID-PLC-001..007, UB-PLC-017 | 04+14 | no |
| **hold_exit** | **FLUID-HLD-001..008** | lumped only | **YES — no dedicated session** |
| reentry | FLUID-REN-001..006 | 08 has REN-005 | **REN-001..004, REN-006** |
| news_window | FLUID-NWS-001..006 | 11 | NWS-005 still SHADOW |

3 inventory SHADOW fluids still SHADOW: `FLUID-HLD-005` trail_vs_orig, `FLUID-HLD-008` friday_cutoff, `FLUID-NWS-005` spine_empty_honesty.

---

## C. 8 envelope walls

| id | keep? | session | residual? |
|---|---|---|---|
| ENV-KILL | ENVELOPE_KEEP | 09 | no |
| ENV-TWO-STOP | ENVELOPE_KEEP (Choice remint after hist; count stays integer) | 08 | no |
| **ENV-TOKEN** | ENVELOPE_KEEP | **20** | **yes** |
| ENV-H8 | ENVELOPE_KEEP | 15 | no |
| ENV-DD | ENVELOPE_KEEP | 02/17 | no |
| ENV-US30 | ENVELOPE_KEEP | 09 | no |
| ENV-OCC | ENVELOPE_KEEP | 01 | no |
| **ENV-DEAD** | ENVELOPE_KEEP (session_fitness Score labels only) | **20** | **yes** |

---

## D. Missing list — residuals 01-19 did not dedicate

### D1. Writer skip strings not in n=45
- `cluster_unit_already_placed_today:*`
- `stale_tick_market_closed:*`
- `ai_companion_{control_state_issue,pause_new_entries,cooldown,zero_risk}`
- `intent_exception:*`
- `cost_screen_spread_r:*` (live sibling of `pretrade_spread_r_refuse`)
- `equity_unavailable` / `day_baseline_unavailable` / `engine_exception:*`
- `future_decision_bar_time`
- `spread_geometry_floor*` / `entry_hour_deferred:*`
- `weekend_flat` (flatten window)

### D2. Governor siblings session 17 prompt missed
- `fail_closed:{nan_state,nonpositive_equity,high_water_below_equity,negative_open_risk}`
- `max_dd_limit_reached` / `max_dd_entry_buffer_reached`
- `gross_risk_cap_exhausted` / `gross_risk_cap_would_exceed`
- `unknown_profile` / `fail_closed:{unknown_sleeve,bad_direction,nonpositive_stop}`
- `kelly_lite` / `sqrtN_pool` / `coloss_breaker` / `ladder_step` / `vol_level_tilt`

### D3. Silent drops (no skip_reason in ledger) — **highest forensic gap**
- `metals_confluence_reject` (A8)
- `symbol_damage_hard_quarantine`
- `learning_rerate_gate_zero`
- `vp_acceptance_drop`

### D4. Bridge / send-path
- triple-gate `ultimate_book_*`
- `missing_dial_keys` / candidate-book / market-expansion allowlist
- `geometry_unavailable`, `open_trade_returned_none`, `runtime_halt_blocked`, `exec_mgr_v4`, `pretrade_cost`, `order_rejected`, lot/tick family

### D5. Sleeve-select detail strings
- `eurusd_dual_pos_keep_all_identity` (**not in n=45**)
- `xag_no_conflict_set_single_KEEP`
- GBPJPY side-aware reason strings
- `blocked_escape:*`

### D6. Hold / exit / remint (biggest dedicated-session hole)
- FLUID-HLD-001..008
- `exit_policy_v4_family`
- Chair `g8_block_reentry_*`
- two_stop **helper unwired** into PR41 `book_owner`

### D7. P0 / CF-D / CA components / A+
- `P0_KEEP_REVIEW_*`, `P0_CFD_*`, `conf_gate_band_disposition`
- `cf_d` site gap (+11.17R cited)
- CA-OCC/LIQ/EVT/USD/CORR/RSK/IDX
- `APLU-OBS-001`

### D8. Doctrine / POST / wiring conflicts (Chair must LABEL)
- `JEV_GATE_INVENTORY.json` `never_place=true` vs owner 2026-09-21 DELETE eternal
- `veto.py` / `cycle.py` / `a1_log.py` / `sites.py` Infinity VETO wording
- `conf_gate` place stake = VETO as **eternal** vs default-until-prove
- `jev_client` default max_calls **200** vs owner **500000**
- S14 `call_system_one` **not** `jev_client.evaluate`
- Policy C **not imported** by PR41 admission (inventory says JEV_JUDGED live)
- two_stop_day_circuit **helper unwired**
- `regime_system_one` POST gap

### D9. Parked / bound (ENVELOPE_KEEP)
- Expanding V3 PARKED
- `selector_v4` R2-bound (`SEL-V4-002` research wrapper only)
- S16 Dig harness off Challenge place scoreboard
- leave-orig ticket `293332188` (`FLUID-HLD-006` / `ENV` cousin)

---

## E. Classification rule used (catch-all)

| proposed | when |
|---|---|
| **ENVELOPE_KEEP** | identity, prop walls, hard-offs, halt/kill, token, weekend FTMO-off, idempotency this-bar, missing data/clock, broker reject, parked/bound |
| **JEV_WIRE** | any fluid/select/admit/size/place/remint/hold/cost/occupancy/companion/confluence/damage/derisk that can change fire rate after Challenge hist-prove |

Soft exceptions to hard-offs: **Choice KEEP_OFF|SCOPED_EXCEPTION + hist only** — never silent code flip.

Place path: **Choice PLACE|STAND|DELAY** after hist — **never eternal never_place**; this session still `place=false`.
