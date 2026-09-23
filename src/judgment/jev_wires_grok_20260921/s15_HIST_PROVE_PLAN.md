# HIST-PROVE PLAN — 15_residual_static_book_owner_batch_a

**as_of_ict:** `2026-09-21T06:05:33+07:00`  
**account:** Challenge login `0` / ns `operator` / magic `0`  
**quarantine:** Verification `0` is not a payout tape.  
**APPLY:** off until this plan's gate is PASS and Chair says APPLY. This session does not APPLY.

Doctrine: hist / replay on Challenge tape **before any APPLY that changes live fire rate**.

---

## 0. Module_ATR honesty (non-negotiable)

Three exit lenses exist and **must not be merged**:

| lens | blotter examples on this box | R field |
|---|---|---|
| Dig_3R | Challenge closes / Dig geometry | Dig R only |
| Edge_ATR | Edge ATR-R | Edge R only |
| Module_ATR | `blotter_Module_ATR_XAUUSD_dsp_three_fresh_lower_lows.jsonl`, `blotter_Module_ATR_GBPJPY_sub_mid_dn_re_proxy_SHORT.jsonl`, XAGUSD metals/sub_xvol Module_ATR blotters under `/workspace/gtos/close_loop/war_room_20260920/` | `R_Module_ATR` only |

Rules:

- Never add Dig R + Edge R + Module_ATR R into one `sumR`.
- Never invent an ATR or `regime_tag` to fill COMPLETE_STATE. If compose (session 10) has not assembled `regime_tag` / `conf_band`, stamp `PENDING`.
- Module_ATR blotter is a **geometry proxy** (`stop0.75/tgt6.0`) — it is **not** the live W7 `TradeIntent` path (no stay_timing / peer_panel / admission). Yearfold receipts already label this APPROXIMATION.
- Weekend embargo hist is a **clock + firm-rule + sleeve-horizon** question. ATR is not the decision. Do not drag Module_ATR R into the embargo counterfactual unless the row is explicitly a Module_ATR Friday-entry subset, stamped `exit_model_tag=Module_ATR`, reported as a **separate** table.
- Alias Package B → `sub_mid_dn_revert` merge is forbidden (doctrine do-not list).

If a metric cannot be computed without inventing ATR/regime: write `MISSING` and drop the cell.

---

## 1. What can change fire rate (only these two)

| reason | proposed APPLY | fire-rate change | envelope that still binds |
|---|---|---|---|
| `weekend_entry_embargo` | `GTOS_JEV_WEEKEND_EMBARGO_APPLY` | SKIP → maybe continue intent (then still occupancy/spread/tick) | FN funded; same-tick flatten window; kill/halt/breach |
| `no_tick_transient` | `GTOS_JEV_NO_TICK_TAPE_FRESH_APPLY` | retry forever vs consume bar (STAND) | PLACE without tick forbidden |

Five ENVELOPE_KEEP reasons are **out of hist-prove for APPLY**. They may be counted as skip-rate context only.

---

## 2. Tapes found vs MISSING

### Found

| tape | path | use |
|---|---|---|
| Session BA weekend priced cells | `/workspace/gtos/close_loop/war_room_20260920/_pr41_land/ai-trading-agent/docs/audits/fable5-vision-audit-20260725/phase13/receipts/BA_WEEKEND_V1.json` | **Primary** embargo/flatten economics. `embargo.cells[]` include `arm=flat_calendar_m0_embargo_4h`, `embargo_hours`, `embargoed`, fold OOS mean R, failing_core_gates. |
| Firm rules | `_pr41_land/.../research/operations/broker_truth_layer_2026_07_27/FIRM_RULES_V1.json` | FTMO: no `weekend_holding`. FN: Challenge allowed, funded PROHIBITED. |
| Challenge 45-ticket Jev replay | `/workspace/gtos/cursor_project_seed/jev_replay_pack/challenge_replay_rows.jsonl` + `CHALLENGE_JEV_REPLAY_20260917.md` | n=45, 6 wins / 39 losses, actual PnL −4295.92 USD. **Close-level** R/DD. Not W7 skip reasons. |
| Module_ATR blotters | `/workspace/gtos/close_loop/war_room_20260920/blotter_Module_ATR_*.jsonl` | Optional **separate** Friday-entry lens. Do not mix R. |
| Sleeve-select V2 hist (context only) | cited in gap inventory: sumR_select=+235.36 vs keep_all=−74.72, n_conflicts=2353 | Not Batch A. Do not treat as embargo prove. |

### MISSING (honest)

| needed | status |
|---|---|
| Live W7 `shadow_logs/ultimate_book_launcher.jsonl` (or runtime-learning packets) for Challenge 0 with skip `reason` in the 7 | **MISSING on this box.** VPS Admin unreachable. |
| Count of `weekend_entry_embargo` skips on FTMO Challenge | **UNKNOWN.** Policy is default-OFF and FTMO has no weekend rule, so live n is likely **0** unless an operator armed `--weekend-flat`. |
| Count of `no_tick_transient` skips + whether a later tick on the same `decision_bar_iso` placed | **MISSING.** Tests pin the reason; live n unknown. |
| Named trading-session calendar (`symbol_info_session_trade`) | **MISSING** (weekend_policy.py documents this). Do not invent. |
| Module_ATR live TradeIntent path for embargo | **Not the W7 path.** Proxy only. |

Chair action: CopyFromBox W7 skip jsonl when machineId is up. Until then, embargo prove uses **BA_WEEKEND_V1** (research archive, not live Challenge skip census). no_tick prove is **BLOCKED** for APPLY (can still SHADOW).

---

## 3. Protocol A — `weekend_entry_embargo`

### 3.1 Hypothesis

Static `entry_blocked = hours_to_boundary <= max(embargo, flatten_before)` is blunt.

- Same-tick flatten window (hours ≤ `flatten_before_hours`) should stay SKIP — not a Jev question.
- Extra embargo hours, and crypto CALENDAR vs GRID, may destroy +EV Friday fires on firms that **allow** weekend hold (FTMO Challenge; FN Challenge).

### 3.2 Counterfactual (research archive)

Universe: BA_WEEKEND_V1 `embargo.cells` for the armed four (`crypto`, `energy_agri`, `sub_xvol_pullback`, `sub_mid_dn_revert`) **and** any FTMO Challenge FX+metals subset if skip jsonl arrives.

For each cell:

1. `static` = embargo ON (current code if policy armed).
2. `jev_shadow` = replay Batch A questions over COMPLETE_STATE built from named cell fields (hours, sleeve, firm=FTMO, phase=challenge). `regime_tag=PENDING`.
3. `cf_keep_embargo` = always KEEP_EMBARGO (control = static).
4. `cf_scoped` = take SCOPED_ENTRY_OK **only outside** flatten window **and** `firm_allows_weekend_hold`.

### 3.3 Metrics (report per lens, never mixed)

Required columns:

| metric | definition |
|---|---|
| `n` | trades or skip-events in cell |
| `n_embargoed` | static skips |
| `n_scoped_ok` | Jev SCOPED_ENTRY_OK that code would have allowed |
| `fire_rate_static` | placed / candidates |
| `fire_rate_cf` | placed after scoped exceptions |
| `sumR_static` | sum of **one** lens R |
| `sumR_cf` | same lens |
| `delta_sumR` | cf − static |
| `DD_static` / `DD_cf` | max drawdown of the equity path in that lens |
| `p_fail_dd` | if BA cell already has it, copy; else MISSING |
| `failing_core_gates` | copy from BA cell (expectancy/stability/robustness/significance) |

BA snapshot already shows `flat_calendar_m0_embargo_4h` on `flat_37_day_snapshot` with `delta_pooled_oos_mean_r = -0.320266` and failing expectancy/stability/robustness/significance — i.e. **4h embargo on that control band did not prove as a repair**. That is evidence **against** keeping a blunt embargo on FTMO, not a license to APPLY SCOPED_ENTRY_OK on live Challenge without the Challenge skip census.

### 3.4 Module_ATR side table (optional)

If Chair wants XAU Friday-entry Module_ATR:

- Input: `blotter_Module_ATR_XAUUSD_dsp_three_fresh_lower_lows.jsonl`
- Filter: decision time in `[boundary-24h, boundary)` broker.
- Report `sumR_Module_ATR` / `n` / `DD` **only**. Headline remains BA_WEEKEND_V1, not this table.

### 3.5 Gate to APPLY `GTOS_JEV_WEEKEND_EMBARGO_APPLY`

PASS all:

1. Challenge login stamp `0` on the prove receipt (or explicit `tape=BA_WEEKEND_V1_research` if live skip n=0 because policy OFF — then APPLY is a **no-op** on live FTMO until someone arms `--weekend-flat`, which FTMO should not).
2. `delta_sumR > 0` on the **primary** lens (BA cell or Challenge closes), same R universe.
3. `DD_cf` not worse than static by a pre-declared bound (copy BA `p_fail_dd` if present; else require DD_cf ≤ DD_static).
4. `n_scoped_ok >= 30` **or** honest `n=0 policy-OFF` → **do not APPLY** (nothing to apply).
5. Zero SCOPED_ENTRY_OK on FN funded flatten-window fixtures.
6. Fail-closed tests in PATCH_SKETCH §3.6 green.
7. Chair LABEL the receipt. This session does not APPLY.

FAIL → keep SHADOW. Do not weaken `WeekendPolicy.entry_blocked` by a silent hours edit.

---

## 4. Protocol B — `no_tick_transient`

### 4.1 Hypothesis

Always `bar_consumable=False` retries the same decision bar. That is correct for a 1-tick MT5 hole. It is toxic if the market is closed and the next tick is a Monday reopen chase (cousin of `stale_late_entry_after_restart` / `stale_tick_market_closed`).

### 4.2 Tape

**MISSING** live W7 skip jsonl. Cannot compute n / later-place rate on this box.

Substitute until CopyFromBox:

- Unit tests already pin skip + `bar_consumable=False` (`test_no_tick_leaves_bar_unconsumed_for_retry`).
- Shadow on Challenge observer: log every `no_tick_transient` with COMPLETE_STATE + Noul `tape_fresh` for ≥1 week.

### 4.3 Metrics once tape exists

| metric | definition |
|---|---|
| `n_no_tick` | skip events |
| `n_later_place_same_bar` | same (sleeve, symbol, decision_bar) placed on a later tick |
| `n_never_placed` | bar died |
| `n_stale_chase` | later place with tick_age>900s or Monday reopen (if clock named) |
| `sumR_later_place` | one lens only, on those later places |
| `sumR_if_consumed` | 0 for those events (STAND) |
| `delta_sumR` | consume-stale-chases vs keep-retry |
| `fire_rate` | later places / n_no_tick |

### 4.4 Gate to APPLY `GTOS_JEV_NO_TICK_TAPE_FRESH_APPLY`

PASS all:

1. Live or box-copied W7 skip jsonl with `n_no_tick >= 30`.
2. `delta_sumR` of consuming the Noul-false subset ≥ 0 (dropping stale chases does not lose more R than it saves) on **one** named lens.
3. Zero composed PLACE without `tick.present`.
4. Fail-closed: Jev dark → RETRY.
5. Chair LABEL.

Until tape exists: status **BLOCKED** for APPLY. SHADOW is allowed.

---

## 5. Envelope reasons — no APPLY hist

Count-only if skip jsonl arrives:

| reason | expected live | prove |
|---|---|---|
| `breach_flatten_block` | rare (near −4%/9%) | none — prop wall |
| `kill_switch_or_halt_forced_observe_only` | operator | none |
| `account_state_unavailable` | transient | none — retry already correct |
| `profile_missing_instrument_config` | config holes | repair profile, not Jev |
| `weekend_policy_clock_unavailable` | only if policy armed + clock dark | preflight already refuses start |

---

## 6. Replay worker (design)

- Offline. `place=false`. No MT5 send.
- Input: BA_WEEKEND_V1 cells + (if present) launcher jsonl.
- For each event: `build_batch_a_complete_state` → `evaluate_batch_a` **or** recorded answers if TypeSafe budget is the prove-time 500000 env.
- Compose with APPLY simulated, not live.
- Output receipt path (draft):  
  `sessions/15_residual_static_book_owner_batch_a/hist/BATCH_A_HIST_PROVE_RECEIPT.json`  
  **not written this session** — plan only.

Budget: `GTOS_JEV_MAX_CALLS=500000` at prove-time. Do not change client default 200 in-tree this pass.

---

## 7. Chair gate summary

| wire | SHADOW now | APPLY now | blocker |
|---|---|---|---|
| weekend_entry_embargo | yes (draft) | **NO** | Live skip n likely 0 (policy OFF on FTMO). BA cells show 4h embargo not a proven repair — need Chair + Challenge census or an explicit "policy-OFF, APPLY is no-op" LABEL. |
| no_tick_transient | yes (draft) | **NO** | Skip jsonl MISSING. |
| five envelope reasons | observe-only (session 12/19) | **NO** | Envelope. |

Next Chair verbs (Chair only): LABEL this receipt; CopyFromBox W7 skip jsonl; do not ENFORCE APPLY this pass.
