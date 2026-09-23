# A+ setups as sleeves on the gate flow — 2026-09-18

**Seat:** architecture + research stubs. **SHADOW only.**  
**Owner vision:** 2026-09-18 — every instrument’s A+ setups are first-class **sleeves** on the same admit / fluid / selector-observe / Jev compose path as live Challenge. Not a side catalog.  
**Base:** `cursor/jev-alive-organism-72cf`.  
**Companions (do not overwrite):** SYMBOL_STATE_V0 multi-instrument typed state; code-walls limiting multi-instrument Jev. This pack **extends the sleeve/gate pipe**. Peer / CA slots are named hooks those PRs can fill.

No place. No remint. No flatten. No APPLY size. No `selector_v4.py` edit (R2 / H1). Inventory stays **48 fluid / 8 envelope**.

---

## 1. What a sleeve is today (map)

Two live identities already exist. Gates read **`identity.sleeve`**, not a grade letter.

| Surface | Object | How gates read it |
|---|---|---|
| W7 `ultimate_book` | `SleeveSpec` in `admission.py` (`name`, confidence, `asset_class`, symbols) | `--tags` ∩ registry ∩ include flags → `TradeIntent.sleeve` → generate / admit / place / manage. Jev A1 observes after `admit_and_size` and `_spread_cost_screen`. |
| F5 Challenge | ticket `comment` / tag (`dsp_spring_xau`, `vss_*`, `dsp_two_bar_t`) | `family.py` → `house_keep` / `house_hard_off` / `study`. `assemble_gold_state_v0` puts the tag on `identity.sleeve` + `family_class`. `sleeve_from_tape` fills `ac60` / A8. `compose_shadow` + `attach_fluid` stamp the 48 fluid questions. |
| Historical A+ | Primary Analyzer `setup_grade` A+/A/B on frameworks (`ob_retest`, `breaker_retest`, `session_sweep`) | **Side catalog.** Never a sleeve. Never rode admit / fluid / Jev. |

Wrong-trade law still holds: a missing **state** or a wrong **calculation**, not a missing letter grade.

```
run_book / F5 writer
  → generate (sleeve identity)
  → gold_state.v0          identity.sleeve + geometry + session + occupancy + news
  → fluid / admit / SEL-V4-002 observe
  → compose_shadow         Choice / Score / Noul → size shadow
  → APPLY only if named wire + Challenge login/ns + not A+
  → ExecutionEngine.open_trade / token     # Jev NEVER sits here
```

---

## 2. APlusSleeveV0

Schema `gtos.judgment.aplus_sleeve.v0`. Sleeve name `aplus_{setup_id}`. Family class **`aplus_study`** (does not inherit W7 `w7_sleeve` or F5 hard-off substrings).

| Field | Role |
|---|---|
| `symbol` | Instrument (`XAUUSD`, `GBPJPY`, `EURUSD`, `USDJPY`, …) |
| `setup_id` | Named A+ setup (`xau_london_ob_retest`) |
| `geometry_keys` | Closed set: entry / stop / target / stop_dist / target_dist / plan_r / stop_atr / target_atr / order_type / atr14. Defaults are the contract; a candidate fills prices. |
| `session` | Preferred kill zone (`london` / `ny` / `tokyo` / `asia` / `either`). Writer clock stays integer. |
| `occupancy_hooks` | `cluster`, `keep_one_symbol` (label), `isolated_reentry_minutes`. Tape fills `symbol_open` / isolated / corr. Envelope KEEP-one and 2-stop **COUNT** stay integers. |
| `peer_ca_hooks` | Named peers + `ca_role` + `dxy_hook=named_only` + `funding_hook=named_only`. `peer_state` is the SYMBOL_STATE_V0 join. **Never invent DXY / funding / peer OHLC.** |
| `completeness` | Spec complete vs tape/peers assembled. Missing stays visible. |
| `chair_fields` | Closed Chair-synthesis set (8). First-class sleeve inputs on the same 48 questions. SHADOW. See §4. |
| `pack2_fields` | Closed Instrument Edge PACK 2 Tier-1 set (9). `sleeve_field` / `gate_input` / `info` stubs on FLUID-ADM / SIZ / NWS only. SHADOW. See §7. |
| `pack3_fields` | Closed Instrument Edge PACK 3 fixture set (7). DST-true clocks on `time_utc` (server−3h). Locked constants + GBPJPY t1/t2/t4 vectors. SHADOW. See §8. |
| `pack4_fields` | Instrument Edge PACK 4 + `SLEEVE_ATTACH_MAP`. First Choice is GBPJPY A+ readiness. SHADOW. **Not an admit Choice.** See §9. |
| `pack5_fields` | Chair-canon `sleeve.gbpjpy_a_plus_ready` ∈ {a_plus, almost, blocked, null_state}. Adds `tone ≠ risk_off`. SHADOW. See §11. |
| `pack6_fields` | PROVE_SEED `sleeve.xau_dsp_shakeout_a_plus_ready`. Fixtures S0–S5. Hypothesis mute print\|guidance_live OR Warsh T±60. Honesty `n_in=3` = S0/S1/S2. SHADOW. See §12. |

Research stubs (not live generators, not `--tags`):

| setup_id | symbol | session | family | cluster | peers |
|---|---|---|---|---|---|
| `xau_london_ob_retest` | XAUUSD | london | ob_retest | metals | USDJPY |
| `gbpjpy_london_session_sweep` | GBPJPY | london | session_sweep | jpy | USDJPY, EURJPY |
| `eurusd_ny_ob_retest` | EURUSD | ny | ob_retest | fx_major | GBPUSD, DXY |
| `usdjpy_tokyo_asia_fade` | USDJPY | tokyo | asia_fade | jpy | XAUUSD, GBPJPY |
| `xau_dsp_shakeout` | XAUUSD | either | dsp_shakeout | metals | USDJPY |

Module: `src/judgment/aplus_sleeve.py`.

---

## 3. How sleeves attach (no place / remint)

```
APlusSleeveV0
  → assemble_aplus_state
       identity.sleeve      = aplus_{setup_id}
       identity.setup_id
       identity.sleeve_kind = aplus_v0
       identity.family_class = aplus_study
       origin_organism      = aplus_research
       geometry / sessions / occupancy / sleeve_features.session
       aplus{} + peers{}
  → compose_shadow / attach_fluid / observe_fluid_inventory
       same 48 questions (state_sufficient, flow_*, session_fitness,
       geometry_vs_tape, occupancy, admit, SEL-V4-002 observe, …)
  → shadow_size_tilt may move
  → live_size_tilt = 1.0
  → apply_this_row = False
  → apply_named_tilts / maybe_haircut_unit no-op
```

`session_fitness` reads `aplus.session` when present (preferred session = 2, other live session = 1, dead/Friday = 0). It does not replace the writer clock.

`intent_gold_state` and `score_position` route `aplus_*` / catalog `setup_id` onto this assembler so a live intent or Challenge slate row is not a second catalog.

**Forbidden here:** `GTOS_JEV_APPLY_LIVE` haircut, `open_trade`, token mint, remint of 293332188, flattening, editing `selector_v4.py`, adding fluid gates (48 stays 48).

---

## 4. Chair synthesis fields → gate inputs (SHADOW)

Closed set of **8**. Module: `src/judgment/chair_fields.py`. Stamped on `gold_state.chair_fields` and `aplus.chair_fields`. Compose carries counts only. **No ninth field. No new fluid gate.** Unassembled peers stay visible. `invented` is always false.

Clock-true fields may assemble from `as_of_utc` / `sessions.named`. Peer / CA fields wait `peers.peer_state` (SYMBOL_STATE_V0). Named caller values are allowed; computed DXY / funding / peer OHLC are not.

| Field | Kind | Assembles from | Gate questions (inventory ids) | Applies |
|---|---|---|---|---|
| `usd_proxy_vs_xau` | score | named USD proxy peer — **not** DXY | `flow_stance` FLUID-ADM-002; `flow_alignment` FLUID-ADM-003 / `f5_xau_flow_alignment_size_tilt`; `admit` FLUID-ADM-007 / UB-AUTH-010; `veto_corr` FLUID-PLC-001 | XAUUSD, USDJPY |
| `gbpjpy_dual_leg_agree` | noul | named GBPUSD + USDJPY legs | `flow_stance` FLUID-ADM-002; `flow_alignment` FLUID-ADM-003 / flow wire; `admit` FLUID-ADM-007 / UB-AUTH-010; `veto_corr` FLUID-PLC-001; `cluster_same_day` FLUID-REN-006 | GBPJPY |
| `us30_rth_vs_eth` | choice | clock 13:30–20:00 UTC (`dst_unresolved`) | `session_fitness` FLUID-ADM-004; `session_size` FLUID-SIZ-003; `friday_cutoff_label` FLUID-HLD-008 | US30 only. **ENV-US30 stays integer OFF.** |
| `sess.ldn_ny_overlap_vol` | score | clock 12:00–16:00 UTC. `vol` only if named M15 | `session_fitness` FLUID-ADM-004; `session_size` FLUID-SIZ-003; `geometry_vs_tape` FLUID-ADM-005 / SEL-V4-002; `geo_size` FLUID-SIZ-004; `cost_vs_tape` FLUID-PLC-005 | XAU + FX stubs |
| `fx_session_london_fit` | score | `sessions.named` (london=2, other live=1, dead/Friday=0) | `session_fitness` FLUID-ADM-004; `session_size` FLUID-SIZ-003; `admit` FLUID-ADM-007 / UB-AUTH-010 | FX stubs (not XAU) |
| `corr.eur_gbp_usd_co_move` | noul | named EUR/GBP/USD peers | `veto_corr` FLUID-PLC-001; `veto_occupancy_label` FLUID-PLC-004; `cluster_same_day` FLUID-REN-006; `flow_alignment` FLUID-ADM-003 / flow wire | EURUSD, GBPJPY, GBPUSD, EURGBP |
| `corr.xau_vs_eur_proxy_usd` | noul | named XAU vs EUR-as-USD-proxy | `veto_corr` FLUID-PLC-001; `flow_stance` FLUID-ADM-002; `flow_alignment` FLUID-ADM-003 / flow wire; `admit` FLUID-ADM-007 / UB-AUTH-010 | XAUUSD, EURUSD |
| `tokyo_fix_window_label` | noul | clock 00:50–01:10 UTC (09:55 JST). Not a news HIGH. 00:55 is writer `dead_21_00z`; 01:05 is `asia`. Writer clock stays integer. | `session_fitness` FLUID-ADM-004; `session_size` FLUID-SIZ-003; `friday_cutoff_label` FLUID-HLD-008 | USDJPY, GBPJPY, EURJPY |

Local compose:

- `session_fitness` / `session_size` source becomes `sessions.named+aplus.chair_fields` when a clock Chair field is assembled.
- `veto_corr` may read assembled Chair corr **only** when occupancy `corr_hold_named` is missing. Unassembled peers stay `decidable=false`.
- `live_size_tilt` stays 1.0 on `aplus_*`. Chair fields do not APPLY.

---

## 5. Coordination

| Parallel pack | Join |
|---|---|
| SYMBOL_STATE_V0 | Fill `peers.peer_state`. Do not invent. A+ completeness.peers flips true only when that object is assembled. |
| Code-walls | Do not add a parallel A+ catalog or a second gold_state. Extend this sleeve identity. |
| CA→size named shadow | May later read `peer_ca_hooks.ca_role` as a **shadow** Score. APPLY stays off on A+ until a named owner wire. |
| Challenge close learning | Close LABEL on A+ rows uses the same `compose` / `close_label` questions. |

---

## 6. Host

See [`lab/wires/HOST_APLUS_SLEEVES_LAND.md`](lab/wires/HOST_APLUS_SLEEVES_LAND.md). Copy `src/judgment/`. Do **not** turn APPLY on for `aplus_*`. Existing Challenge APPLY wires (`f5_xau_flow_alignment_size_tilt`, `F5-JEV-004`) stay Challenge-tag only.

---

## 7. Instrument Edge PACK 2 Tier-1 (SHADOW)

Closed set of **9**. Module: `src/judgment/pack2_fields.py`. Stamped on `gold_state.pack2_fields` and `aplus.pack2_fields`. Compose carries counts only. **No tenth field. No new fluid gate. No new refuse wall.** Inventory stays 48 / 8. Unassembled peers and empty news spine stay visible. `invented` is always false. `ENV-US30` stays integer OFF.

Surfaces: `gate.*` = existing-question **gate_input**; `sleeve.*` = **sleeve_field**; `info.*` = informational bundle that cannot refuse.

Clock-true stubs may assemble from `as_of_utc` / `sessions.named`. Peer / CA stubs wait `peers.peer_state` (SYMBOL_STATE_V0). `gate.event_boj_window` waits a **named** BOJ HIGH on the existing news spine — empty spine is unassembled, not “no BOJ.”

| Field | Surface | Kind | Assembles from | Gate questions (ADM / SIZ / NWS only) | Applies |
|---|---|---|---|---|---|
| `gate.session_overlap_ok` | gate_input | noul | clock 12:00–16:00 UTC | `session_fitness` FLUID-ADM-004; `session_size` FLUID-SIZ-003 | XAU + FX stubs |
| `gate.asia_jpy_act_ok` | gate_input | noul | writer `asia` 01:00–07:00 UTC. `dead_21_00z` / Friday = not-ok | `session_fitness` FLUID-ADM-004; `session_size` FLUID-SIZ-003 | USDJPY, GBPJPY, EURJPY |
| `gate.ny_rth_us30_act_ok` | gate_input | noul | clock 13:30–20:00 UTC (`dst_unresolved`) | `session_fitness` FLUID-ADM-004; `session_size` FLUID-SIZ-003 | US30 only. **ENV-US30 stays integer OFF.** |
| `sleeve.usd_common_factor` | sleeve_field | score | named USD-proxy peer — **not** DXY | `flow_stance` FLUID-ADM-002; `flow_alignment` FLUID-ADM-003 / flow wire; `admit` FLUID-ADM-007 / UB-AUTH-010; `combined_size` FLUID-SIZ-008 | XAUUSD, USDJPY, EURUSD, GBPUSD |
| `sleeve.xau_usd_proxy_align` | sleeve_field | noul | named XAU vs USD-proxy | `flow_stance` FLUID-ADM-002; `flow_alignment` FLUID-ADM-003 / flow wire; `admit` FLUID-ADM-007 / UB-AUTH-010 | XAUUSD, EURUSD, USDJPY |
| `gate.cross_stack_gbpjpy` | gate_input | noul | named GBPUSD + USDJPY legs | `flow_stance` FLUID-ADM-002; `flow_alignment` FLUID-ADM-003 / flow wire; `admit` FLUID-ADM-007 / UB-AUTH-010 | GBPJPY |
| `sleeve.london_expand_eur_gbp` | sleeve_field | score | `sessions.named` / clock 07:00–12:00 UTC. Vol unassembled without named M15 | `session_fitness` FLUID-ADM-004; `session_size` FLUID-SIZ-003; `geometry_vs_tape` FLUID-ADM-005; `geo_size` FLUID-SIZ-004 | EURUSD, GBPUSD, EURGBP, GBPJPY |
| `gate.event_boj_window` | gate_input | noul | named BOJ HIGH in F5 window | `event_proximity` FLUID-NWS-001; `high_in_f5_window` FLUID-NWS-002; `warsh_class` FLUID-NWS-004; `event_size` FLUID-SIZ-006 | USDJPY, GBPJPY, EURJPY |
| `info.risk_on_off_bundle` | info | info | named peer stance only | `flow_stance` FLUID-ADM-002; `flow_alignment` FLUID-ADM-003 / flow wire; `warsh_class` FLUID-NWS-004; `event_size` FLUID-SIZ-006 | XAU + FX + US30. **Cannot refuse.** |

Local compose:

- `session_fitness` / `session_size` source becomes `sessions.named+aplus.chair_fields+aplus.pack2` when a clock Chair or PACK 2 field is assembled.
- PACK 2 never sets `refuse=true`. `attach_fluid` still stamps `refuse: false` on every fluid gate.
- `live_size_tilt` stays 1.0 on `aplus_*`. PACK 2 does not APPLY.

---

## 8. Instrument Edge PACK 3 fixture lock (SHADOW)

Closed set of **7**. Module: `src/judgment/pack3_fields.py`. Stamped on `gold_state.pack3_fields` and `aplus.pack3_fields`. Compose carries counts only. **No eighth field. No new fluid gate. No new refuse wall.** Inventory stays 48 / 8. Unassembled peers and empty news spine stay visible. `invented` is always false. `ENV-US30` stays integer OFF.

Chair-locked constants (do not retune):

| Constant | Value | Use |
|---|---|---|
| `resid_cap` | **0.15 GJ** | `corr.gbpjpy_risk_cross` residual. `t4` / `t3` fail above this. |
| `london_expand` | **≥ 1.25 pass**, **< 1.0 fail** | `london_open_eur_gbp_expand`. Mid is 1.0 ≤ r < 1.25. |
| `ny_impulse` | **≥ 1.5 impulse**, **< 1.0 chop** | `ny_cash_open_us30`. Mid is 1.0 ≤ r < 1.5. |

Clocks on **`time_utc` only**. Server wall converts as **server − 3h**. Never read `sessions.broker_hour` for these windows.

| Clock | Winter | Summer | DST |
|---|---|---|---|
| London open | 07:00–08:59 UTC | 06:00–07:59 UTC | UK (last Sunday March → last Sunday October) |
| US30 cash open | 14:30 UTC (hour to 15:30) | 13:30 UTC (hour to 14:30) | US (second Sunday March → first Sunday November) |
| LDN–NY overlap | 13–17 UTC | 12–16 UTC | US (NY cash) |

GBPJPY fixture vectors (unit-tested):

| Vector | Verdict | Reason |
|---|---|---|
| `t1` | pass | dual legs agree and residual 0.08 ≤ 0.15 |
| `t2` | fail | `dual_split` — GBPUSD long / USDJPY short |
| `t4` | fail | `residual` — legs agree, residual 0.22 > 0.15 |
| `t3` | alias of `t4` | Chair lock named the residual fail `t3`; owner brief named `t4` |

| Field | Surface | Kind | Assembles from | Gate questions (ADM / SIZ / NWS only) | Applies |
|---|---|---|---|---|---|
| `sess.ldn_ny_overlap_vol` | sleeve_field | score | `time_utc` overlap window. `vol` only if named M15 | `session_fitness` FLUID-ADM-004; `session_size` FLUID-SIZ-003; `geometry_vs_tape` FLUID-ADM-005 / SEL-V4-002; `geo_size` FLUID-SIZ-004 | XAU + FX stubs |
| `london_open_eur_gbp_expand` | sleeve_field | score | `time_utc` London-open + named expand ratio | `session_fitness` FLUID-ADM-004; `session_size` FLUID-SIZ-003; `geometry_vs_tape` FLUID-ADM-005; `geo_size` FLUID-SIZ-004 | EURUSD, GBPUSD, EURGBP, GBPJPY |
| `ny_cash_open_us30` | gate_input | noul | `time_utc` US30 cash-open + named impulse | `session_fitness` FLUID-ADM-004; `session_size` FLUID-SIZ-003 | US30 only. **ENV-US30 stays integer OFF.** |
| `corr.eur_gbp_usd_co_move` | sleeve_field | noul | named EUR/GBP/USD peers | `flow_stance` FLUID-ADM-002; `flow_alignment` FLUID-ADM-003 / flow wire; `admit` FLUID-ADM-007 / UB-AUTH-010 | EURUSD, GBPJPY, GBPUSD, EURGBP |
| `corr.xau_vs_eur_proxy_usd` | sleeve_field | noul | named XAU vs EUR-as-USD-proxy | `flow_stance` FLUID-ADM-002; `flow_alignment` FLUID-ADM-003 / flow wire; `admit` FLUID-ADM-007 / UB-AUTH-010 | XAUUSD, EURUSD |
| `corr.gbpjpy_risk_cross` | sleeve_field | noul | named GBPUSD + USDJPY legs + residual vs 0.15 GJ | `flow_stance` FLUID-ADM-002; `flow_alignment` FLUID-ADM-003 / flow wire; `admit` FLUID-ADM-007 / UB-AUTH-010 | GBPJPY |
| `macro.boj_guidance_window` | gate_input | noul | named BOJ HIGH timing on the F5 window | `event_proximity` FLUID-NWS-001; `high_in_f5_window` FLUID-NWS-002; `warsh_class` FLUID-NWS-004; `event_size` FLUID-SIZ-006 | USDJPY, GBPJPY, EURJPY |

Local compose:

- `session_fitness` / `session_size` source becomes `sessions.named+aplus.chair_fields+aplus.pack2+aplus.pack3` when a clock Chair / PACK 2 / PACK 3 field is assembled.
- PACK 3 never sets `refuse=true`. Dual-split / residual / expand / chop are SHADOW labels.
- `live_size_tilt` stays 1.0 on `aplus_*`. PACK 3 does not APPLY.

---

## 9. Instrument Edge PACK 4 + SLEEVE_ATTACH_MAP (SHADOW)

Closed map from A+ `setup_id` → Edge PACK 4 state paths. Module: `src/judgment/pack4_fields.py`. Stamped on `gold_state.pack4_fields` and `aplus.pack4_fields`. Schema `gtos.judgment.aplus_pack4_fields.v0`. Compose carries counts + the readiness Choice label. **No new fluid gate. No new refuse wall. No admit Choice.** Inventory stays 48 / 8. `ENV-US30` stays integer OFF.

`SLEEVE_ATTACH_MAP` (first Choice is GBPJPY; others are named stubs):

| setup_id | symbol | Choice | Status |
|---|---|---|---|
| `gbpjpy_london_session_sweep` | GBPJPY | `choice.gbpjpy_aplus_ready` | implemented |
| `xau_london_ob_retest` | XAUUSD | — | not_applicable |
| `eurusd_ny_ob_retest` | EURUSD | — | not_applicable |
| `usdjpy_tokyo_asia_fade` | USDJPY | — | not_applicable |
| `xau_dsp_shakeout` | XAUUSD | — | not_applicable (PACK 6 owns the shakeout Choice) |

GBPJPY A+ readiness is a TypeSafe Choice, not `admit` / FLUID-ADM-007 / UB-AUTH-010:

```
session_ok ∧ cross.identity_ok ∧ agree ∧ dual_same
∧ boj_bucket ∉ {print, guidance_live}
```

| Answer | Meaning |
|---|---|
| `ready` | All five conjuncts true |
| `not_ready` | A named conjunct failed (dual_split before residual) |
| `unassembled` | A required conjunct is unassembled. Empty spine ≠ no BOJ |

| Conjunct | Pack 3 input | t1 | t2 | t4 |
|---|---|---|---|---|
| `session_ok` | `london_open_eur_gbp_expand.in_window` on `time_utc` | true (07:30 winter) | true | true |
| `cross.identity_ok` | `corr.gbpjpy_risk_cross.residual_class` pass (≤ 0.15 GJ) | true (0.08) | true (0.04) | **false (0.22)** |
| `agree` | risk-cross agree ∧ `corr.eur_gbp_usd_co_move` | true | false | true |
| `dual_same` | `dual_leg_agree` | true | **false** | true |
| `boj_clear` | `boj_bucket` not in `{print, guidance_live}` | true (`none`) | true (`none`) | true (`none`) |

Fixture encode (unit-tested): t1 `ready`; t2 `not_ready` / `dual_split` / `dual_same`; t4 `not_ready` / `residual` / `cross.identity_ok`. t3 aliases t4. Fixture vectors default `boj_bucket=none`. Live empty spine stays `unassembled`.

State paths (Edge PACK 4):

| Path | Role |
|---|---|
| `pack4_fields` | gold_state block |
| `aplus.pack4_fields` | sleeve copy |
| `pack4_fields.fields.choice.gbpjpy_aplus_ready` | TypeSafe Choice |

Maps onto existing session / flow / news **inputs** (`session_fitness` FLUID-ADM-004, `session_size` FLUID-SIZ-003, `flow_alignment` FLUID-ADM-003 / flow wire, `event_proximity` FLUID-NWS-001, `warsh_class` FLUID-NWS-004, `event_size` FLUID-SIZ-006). **Does not write** `admit`, FLUID-ADM-007, or UB-AUTH-010. `admit_choice` stays flow + cost.

Local compose:

- PACK 4 never sets `refuse=true`. Readiness is a SHADOW label.
- `live_size_tilt` stays 1.0 on `aplus_*`. PACK 4 does not APPLY.
- `FLUID-ADM-007` / `UB-AUTH-010` Choice stays `admit` / `abstain` / `hard_refuse` from flow+cost.

---

## 10. Scout Tier-1 → existing fluid ids (SHADOW observe)

Chair lock. **Observe only.** No new refuse walls. None of these ids write `admit`, FLUID-ADM-007, or UB-AUTH-010. `corr.xau_vs_eur_proxy_usd` is **NO WIRE** (alias of `usd_proxy_vs_xau`). Module: `src/judgment/pack5_fields.py` `SCOUT_TIER1_WIRES` + `SCOUT_TIER1_ALIASES`. Also frozen on `GBPJPY_APLUS_FREEZE.md`.

| Scout feature | PACK 3 / Chair field | Observe ids |
|---|---|---|
| `sess.ldn_ny_overlap_vol` | `sess.ldn_ny_overlap_vol` | FLUID-ADM-004 + FLUID-SIZ-003 |
| `sess.london_open_eur_gbp_expand` | `london_open_eur_gbp_expand` | FLUID-ADM-004 / FLUID-ADM-005 + FLUID-SIZ-003 |
| `sess.ny_cash_open_us30` | `ny_cash_open_us30` | FLUID-ADM-004 + FLUID-SIZ-003 |
| `corr.eur_gbp_usd_co_move` | `corr.eur_gbp_usd_co_move` | FLUID-ADM-002 |
| `corr.xau_vs_eur_proxy_usd` | `usd_proxy_vs_xau` | — (NO WIRE) |
| `corr.gbpjpy_risk_cross` | `corr.gbpjpy_risk_cross` | FLUID-ADM-002 |
| `macro.boj_guidance_window` | `macro.boj_guidance_window` | FLUID-NWS-002 / FLUID-NWS-004 + FLUID-SIZ-006 (**timing only**) |

Chair-canon attach aliases (`ATTACH_ALIASES`, Scout packet
`/workspace/gtos/_scout_packets/SLEEVE_ATTACH_MAP.md`, in-repo
`judgment/astra/SLEEVE_ATTACH_MAP.md`). Resolver `resolve_attach_name`
maps each name onto existing PACK 2 / PACK 5 fields. SHADOW. No refuse.

| Name | Equiv / split |
|---|---|
| `gbpjpy_dual_leg` | ≡ `gate.cross_stack_gbpjpy`, `resid_cap=0.15` |
| `tokyo_event` | SPLIT → `gate.asia_jpy_act_ok` + `gate.event_boj_window` |
| `london_fit` | SPLIT → `sleeve.london_expand_eur_gbp` + `gate.session_overlap_ok` |

---

## 11. Instrument Edge PACK 5 — `sleeve.gbpjpy_a_plus_ready` (SHADOW)

Chair-canon GBPJPY A+ Choice. Module: `src/judgment/pack5_fields.py`. Schema `gtos.judgment.aplus_pack5_fields.v0`. State path `pack5_fields` / `aplus.pack5_fields`. **Not an admit Choice.** Pack 4 `choice.gbpjpy_aplus_ready` {ready, not_ready, unassembled} stays intact.

```
a_plus = session_ok ∧ agree ∧ dual_same ∧ identity_ok(|resid|≤0.15)
         ∧ boj_bucket ∉ {print, guidance_live} ∧ tone ≠ risk_off
```

| Answer | Meaning |
|---|---|
| `a_plus` | All six conjuncts true |
| `almost` | Session ok, no hard block, a conjunct is soft or `tone` unassembled |
| `blocked` | dual_split, residual > 0.15, boj print\|guidance_live, or tone=risk_off |
| `null_state` | Required conjuncts unassembled. Empty spine ≠ no BOJ |

PACK 5 fixture encode (t3 is **pass-capable**, not the PACK 3 t3=t4 residual alias): t1 / t3 `a_plus`; t2 `blocked` / `dual_split`; t4 `blocked` / `residual`. See `judgment/astra/TIER1_FIXTURES_AND_GBPJPY_APLUS.md` and `GBPJPY_APLUS_FREEZE.md`.

Maps existing ADM / SIZ / NWS **inputs** only. Does **not** write `admit`, FLUID-ADM-007, or UB-AUTH-010.

---

## 12. Instrument Edge PACK 6 — XAU DSP shakeout PROVE_SEED (SHADOW)

`sleeve.xau_dsp_shakeout_a_plus_ready`. Module: `src/judgment/pack6_fields.py`. Schema `gtos.judgment.aplus_pack6_fields.v0`. Official PROVE_SEED fixtures: **S0–S5**. Honesty: **`n_in=3`** = {S0, S1, S2} only — not a 6-row sample. **Not an admit Choice.**

Hypothesis mute (this lock): boj ∈ {print, guidance_live} **or** Warsh T±60 (`hypothesis_mute`). `print` / `guidance_live` mute with no minute window. Warsh T±60 does **not** rewrite S0’s fail_reason — S0 stays `fill_in_boj_warsh_t90_t60`.

Revised window mute (FILL_IN_ANY_HIGH alone is **not** mute). Prefer close, then fill:

- close ∈ boj/warsh T±60 → `close_in_boj_warsh_t60`
- **or** fill ∈ T−90..T+60 → `fill_in_boj_warsh_t90_t60`

| Fixture | Expect | Why |
|---|---|---|
| S0 ticket `293611741` | blocked | Warsh fill −15 min ∈ T−90..T+60 (`in_n`) |
| S1 | a_plus | structure ok, no event (`in_n`) |
| S2 | a_plus | other_high at +180 (`in_n`) |
| S3 | null_state | unassembled |
| S4 | a_plus | FILL_IN_ANY_HIGH alone, other_high +10 — proves revision |
| S5 | blocked | boj close +20 ∈ T±60 |
| S6 | blocked | fomc fill −40 ∈ T−90..T+60 |

See `judgment/astra/XAU_DSP_SHAKEOUT_EVENT_GAP.md`. Maps NWS / SIZ / session **inputs**. Does **not** write admit / FLUID-ADM-007 / UB-AUTH-010. Inventory stays 48 / 8. `ENV-US30` stays integer OFF.

---

## 13. Edge FREEZE — both `sleeve.*_ready` Choices (SHADOW)

Authority: `GBPJPY_APLUS_FREEZE.md` + `XAU_DSP_SHAKEOUT_EVENT_GAP.md`.
Lock module: `src/judgment/edge_freeze.py`. **Neither is an admit Choice.**

| Choice | Freeze | Answers | Notes |
|---|---|---|---|
| `sleeve.gbpjpy_a_plus_ready` | `GBPJPY_APLUS_FREEZE.md` | a_plus / almost / blocked / null_state | PACK 5. tone≠risk_off. t1/t3 a_plus; t2 dual_split; t4 residual. |
| `sleeve.xau_dsp_shakeout_a_plus_ready` | `XAU_DSP_SHAKEOUT_EVENT_GAP.md` | a_plus / almost / blocked / null_state | PACK 6 PROVE_SEED. Honesty `n_in=3`. S0 ticket `293611741` blocked. |

Both ride existing ADM / SIZ / NWS **inputs**. Neither writes `admit`, FLUID-ADM-007, or UB-AUTH-010. PACK 4 `choice.gbpjpy_aplus_ready` stays the five-conjunct readiness label.
