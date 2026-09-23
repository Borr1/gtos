# HIST-PROVE PLAN — 02_admission_circuit_score

**as_of_ict:** `2026-09-21T06:05:25+07:00`  
**law:** Challenge hist / replay **before** any APPLY that changes live fire rate (admit, size).  
**place:** prove size/DERISK only. PLACE Choice is a different family (sessions 01/14).  
**this session:** plan + tape inventory. Does **not** run live APPLY. Does **not** broker-place.

## 1. Module_ATR honesty (non-negotiable)

Three R universes exist and **must not be merged**:

| lens | what it is | use in this prove |
|---|---|---|
| **Dig_3R** | research 3R geometry blotter | **not** governor size. Do not convert to ATR-R. |
| **Edge_ATR** | edge ATR-R | **not** mixed into Module_ATR sumR. |
| **Module_ATR** | module TradeIntent geometry (file stop/tgt as tagged on blotter) | sleeve-level R for overlay hist (leader_impulse / vol_level) **only when the blotter row is tagged Module_ATR** |

Rules:

- `exit_model_tag=Module_ATR` rows keep `R_Module_ATR` only. Null Dig/Edge on those rows.
- Do **not** invent `vr`, ATR(14), or a regime tag to fill COMPLETE_STATE. If substrate `TradeIntent.vr` is absent → `STATE_MISSING` and vol_level Score no-ops at 1.0.
- `leader_impulse_veto` hist on `sub_xvol_pullback` uses Module_ATR blotter  
  `/workspace/gtos/close_loop/war_room_20260920/blotter_Module_ATR_XAGUSD_sub_xvol_pullback_20260920.jsonl`  
  plus XAU substrate fires if a Module_ATR XAU sub_xvol blotter is later landed. **Do not** substitute Dig_3R three_fresh R for sub_xvol.
- Governor Score (soft daily / dd / target protect) is an **account-path** prove, not a sleeve-R prove. Use Challenge equity/deals + `SleeveBookPolicy` replay. Sleeve blotter R is a secondary slice, never the DD wall metric.
- Year-fold Module_ATR files (`THREE_FRESH_MODULE_ATR_YEARFOLD_20260920.json`) already stamp  
  `honesty: APPROXIMATION of Module_ATR fills — geometry proxy ≠ live module TradeIntent path (no stay_timing / peer_panel / admission)`.  
  Treat those sumR as **prior**, not as this governor prove.

## 2. Tapes found vs MISSING

### 2.1 Challenge bars (FTMO-true, `time_utc` already −3h)

**Present** (box mirror):

- `/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/XAUUSD_M15.csv` (n≈1598)
- `.../XAUUSD_H4.csv`, `.../XAUUSD_D1.csv`
- `.../multi/{USDJPY,EURUSD,GBPUSD,BTCUSD,ETHUSD,EURGBP,US30_cash,UK100_cash}_{M15,H4}.csv`

Code search dirs (`src/judgment/bars.py`): `challenge_shadow_20260917` under `_pr41_land` is **empty**; runtime also searches `_BOX_MULTI` above. Replay must pass `GTOS_CHALLENGE_BAR_MULTI=/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/multi` **or** copy into the repo landing slot. April `data/historical` is **never** Challenge tape.

**MISSING:**

- **GBPJPY** M15/H4 Challenge CSV — affinity instrument, not in the 2026-09-17 pull.
- Challenge login **0** deal/equity JSONL for reconstructing `realized_today_pct` / DD on the live Challenge path. VPS Admin unreachable this seat. `judgment/live/book_event_ledger.jsonl` n=1.
- Nightly `f5_study.json` deals are login **0** (not Challenge 0) — **do not** use as Challenge hist.

### 2.2 Module_ATR sleeve blotters (present)

- XAUUSD `dsp_three_fresh_lower_lows`, `dsp_spring_close_on_20low_through_the_box`
- XAGUSD `metals_core`, `sub_xvol_pullback`, `metal_session_reversion`
- GBPJPY `vss_fxcross_london_proxy`, `sub_mid_dn_re_proxy_SHORT`

Use for **overlay / vol_level** slices only, with lens tag enforced.

### 2.3 Replay engine (present)

- `src/research_infra/replay_policy/sleeve_book.py` (`SleeveBookPolicy`)
- Must feed **live dial** keys, not `bridge.DEFAULT_CONFIG` (1.25% / band). Live: `clean3_w7_ceiling_nom2p00` + `derisk_mode=smooth` + `kelly_lite` + `kelly_conservative`. Missing dial keys must **refuse** (`REQUIRED_DIAL_KEYS` / `strict_config=True`).

## 3. Counterfactuals (what we measure)

Replay the **same** Challenge bar stream and the **same** integer envelope, changing only the Score compose.

| id | treatment | what changes |
|---|---|---|
| T0 | **keep_integer** | current `evaluate_governor` + `admit_and_size`. Baseline. |
| T1 | **shadow_score** | POST evaluate() every admit; **do not** change cap_mult. Harvest train rows. |
| T2 | **soft_daily_trim** | On `soft_daily_stop_reached` only, map Score → `[0, 0.50]` instead of BLOCK. Joint-daily clamp still on. |
| T3 | **dd_haircut_only** | On `derisking_into_maxdd_wall`, Score may shrink cap_mult vs static, never widen. |
| T4 | **dd_restore** (v2) | Allow Score to restore toward 1.0 vs static, still BLOCK at entry buffer. **Only if T3 does not harm DD.** |
| T5 | **target_protect_reshape** | Score in `[0.10, 0.50]` after named target. Never 1.0. |
| T6 | **leader_impulse_score** | Only rows with named `ll_impulse` assembled. Else skip (latent). |
| T7 | **stress_reshape** | ladder/coloss Score inside `[0.60, 1.0]`. |

Envelope holds in **every** treatment: circuit, max_dd walls, fail_closed, ceiling×band, joint daily -5%.

## 4. Metrics (gate inputs)

Per treatment, per instrument (XAUUSD first; GBPJPY **blocked** until tape lands):

| metric | definition |
|---|---|
| `n` | admitted new-entry units (sized=true, risk>0) |
| `n_block_soft_daily` | cycles with integer `soft_daily_stop_reached` |
| `n_trim_soft_daily` | of those, T2 admitted with cap in (0, 0.50] |
| `fire_rate` | n / decision-days |
| `sumR` | sum of **lens-honest** R on admitted fires. Governor path: book unit-R from replay fills. Overlay slice: Module_ATR R only. |
| `meanR` | sumR / n (n>0) |
| `max_dd_frac` | peak (dd_ref − equity) / dd_ref |
| `worst_day_pct` | min realized_today_pct |
| `n_daily_breach_soft` | days realized ≤ −3% |
| `n_daily_breach_hard` | days realized ≤ −5% (**must stay 0**) |
| `n_maxdd_fail` | dd_frac ≥ 0.10 (**must stay 0**) |
| `n_ceiling_refuse` | `ceiling_profile_requires_smooth_ddefense` (must stay 0 on smooth dial) |
| `jev_calls` | POSTs |
| `jev_skip_dark` | dark/budget/http skips (fail-closed count) |

Report **XAUUSD** and **book-all** separately. Affinity: do not pool GBPJPY Module_ATR R into XAU sumR.

## 5. Gate to APPLY (Chair only)

A scoped APPLY flag may be proposed when **all** hold:

1. `n_daily_breach_hard_T* == 0` and `n_maxdd_fail_T* == 0` (envelope held).
2. `n` large enough to matter: **n_block_soft_daily ≥ 30** for T2; **n_derisk_cycles ≥ 50** for T3; else stay SHADOW.
3. T2: `sumR_T2 >= sumR_T0` **or** (sumR slightly worse AND max_dd_frac strictly better by ≥ 0.5pp) — Chair picks; default prefer **no extra hard-risk** + non-worse sumR.
4. T3 haircut-only: max_dd_frac ≤ T0 and fire_rate drop explained (not a silent off).
5. T4 restore: **forbidden** until T3 receipt exists and T4 max_dd_frac ≤ T0 + 0.0pp.
6. T5: only on days with named gain ≥ profit_target_pct. If Challenge never hit target on tape → **STATE_MISSING**, no APPLY.
7. T6: `ll_impulse` named on ≥ 20 Module_ATR sub_xvol rows; opposed cell stays ≤ none-cell meanR (KB5 direction). If generator still does not populate the tag → **APPLY stays 0** (latent).
8. Fail-closed rate (Jev dark) must not silently change fire rate: when dark, T* == T0 by construction (unit test).
9. Challenge ns/login cage: APPLY code path no-ops off `0` / `operator`.
10. **GBPJPY** scoped APPLY blocked until Challenge M15 tape is present (`challenge_tape_present('GBPJPY')`).

None of these gates is self-serve. Chair ENFORCE after reading the receipt.

## 6. How to run (when Chair says go — not this session)

```text
# 1. Point bars at Challenge-true CSVs (never April)
export GTOS_CHALLENGE_BAR_MULTI=/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/multi

# 2. Shadow only
export GTOS_JEV_ADMISSION_SHADOW=1
export GTOS_JEV_ADMISSION_APPLY=0
export GTOS_JEV_MAX_CALLS=500000
# TYPESAFE_API_KEY already on Challenge process; do not print

# 3. Replay SleeveBookPolicy with LIVE dial (ceiling + smooth), not DEFAULT_CONFIG
#    Compare T0 vs T1 receipts under sessions/02_admission_circuit_score/hist/

# 4. Module_ATR overlay slice: filter blotter lens==Module_ATR only
```

Replay driver sketch: wrap `SleeveBookPolicy` and inject `compose_admission` from `patches/admission_jev_score_sketch.py` **offline**. Do not import the sketch from `book_engine.py` until Chair lands it.

## 7. Equity-path honesty if deals stay MISSING

If Challenge 0 deals are still unreachable:

- Build **synthetic** `GovernorState` from replay fills + static 100k ref (same as MC). Label it `equity_path=replay_synthetic`, not `equity_path=challenge_deals`.
- T2/T3 APPLY **blocked** until either (a) Challenge deals land, or (b) Chair accepts synthetic equity_path in writing.
- T1 SHADOW (evaluate POST, no size change) **is** allowed on bars-only — fire-rate unchanged.

Do not use W7/redacted_account deals as a stand-in.

## 8. Interaction with other sessions

| session | conflict |
|---|---|
| 06 apply_size / ca_size | post-admit tilts. Prove governor Score **first**, then compose product. Do not attribute apply_size sumR to T2. |
| 05 Policy C | refuse/trim on state completeness. Run T0 with Policy C as-is; do not disable it to make T2 look good. |
| 17 residual admission | FFD shed / vp / A8 / damage. Leave integer for this prove. |
| 18 train-row harvest | T1 receipts are the harvest source (paired win/lose on Challenge closes). |
| 03 sleeve-select | do **not** flip global APPLY. XAU three_fresh×spring scoped select is independent. |

## 9. Deliverable of the prove run (later)

Write under this OUT dir when run:

- `hist/T0_keep_integer.json`
- `hist/T1_shadow_score.json`
- `hist/COMPARE.md` (sumR, DD, fire_rate, n, n_hard_breach)
- `hist/MODULE_ATR_SLICE.json` (overlay only, lens-tagged)

This session does **not** create those compare files (no replay executed; no evaluate() budget spent from this seat on Challenge).
