# HOST A+ SLEEVES LAND — SHADOW only (2026-09-18)

**Goal:** Land APlusSleeveV0 so every instrument’s A+ setups are sleeves on the Challenge gate pipe.

**Account:** Challenge `0` / ns `operator` / magic `0` only.  
**Machine:** f5-live (`redacted_host`). Do not touch W7 / redacted_account workers.

## Do

1. Copy `src/judgment/` (especially `aplus_sleeve.py`, `gold_state.py`, `family.py`, `compose.py`, `apply_size.py`, `fluid_local.py`, `challenge_shadow.py`, `a1_log.py`, `pack4_fields.py`, `pack5_fields.py`, `pack6_fields.py`) onto dirty `host-local\redacted_host\repo\`.
2. Copy `judgment/astra/APLUS_SLEEVES_ON_GATES.md`, `SLEEVE_ATTACH_MAP.md`, `TIER1_FIXTURES_AND_GBPJPY_APLUS.md`, `GBPJPY_APLUS_FREEZE.md`, `XAU_DSP_SHAKEOUT_EVENT_GAP.md`, `gtos/_scout_packets/SLEEVE_ATTACH_MAP.md`, and this note.
3. Keep existing Alive splices (`bridge.py` after `_decide`, `book_owner.py` after `cost_skip`). Do **not** wholesale-copy GitHub `book_owner.py`.
4. Leave `GTOS_JEV_ALIVE_SHADOW=1` / `GTOS_JEV_A1_LOG=1` if already set so A+ rows log on the 48-fluid inventory.
5. Confirm `aplus_*` compose rows show `aplus_shadow_only: true`, `apply_this_row: false`, `live_size_tilt: 1.0`.
6. Confirm `chair_fields.n == 8`, `invented: false`. Clock-true fields (`fx_session_london_fit`, `sess.ldn_ny_overlap_vol`, `tokyo_fix_window_label`) may assemble from as-of. Peer fields stay unassembled until SYMBOL_STATE_V0. `us30_rth_vs_eth` does **not** lift `ENV-US30`.
7. Confirm `pack2_fields.n == 9`, `invented: false`, `never_refuse: true`. Clock stubs (`gate.session_overlap_ok`, `gate.asia_jpy_act_ok`, `sleeve.london_expand_eur_gbp`) may assemble from as-of. Peer stubs (`sleeve.usd_common_factor`, `sleeve.xau_usd_proxy_align`, `gate.cross_stack_gbpjpy`, `info.risk_on_off_bundle`) stay unassembled until SYMBOL_STATE_V0. `gate.event_boj_window` stays unassembled on empty spine. `gate.ny_rth_us30_act_ok` does **not** lift `ENV-US30`. No new refuse walls.
8. Confirm `pack3_fields.n == 7`, `invented: false`, `never_refuse: true`, constants `resid_cap=0.15`, `london_expand` 1.25/1.0, `ny_impulse` 1.5/1.0. Clocks on `time_utc` only (server−3h). Clock features (`sess.ldn_ny_overlap_vol`, `london_open_eur_gbp_expand`, `ny_cash_open_us30`) may assemble from as-of. Peer corr (`corr.eur_gbp_usd_co_move`, `corr.xau_vs_eur_proxy_usd`, `corr.gbpjpy_risk_cross`) stay unassembled until SYMBOL_STATE_V0. `macro.boj_guidance_window` stays unassembled on empty spine. GBPJPY vectors: t1 pass / t2 dual_split fail / t4 residual fail. `ny_cash_open_us30` does **not** lift `ENV-US30`. No new refuse walls.
9. Confirm `pack4_fields.n == 1`, `invented: false`, `never_refuse: true`, `never_admit: true`, schema `gtos.judgment.aplus_pack4_fields.v0`. `SLEEVE_ATTACH_MAP` implements GBPJPY `choice.gbpjpy_aplus_ready` only; other catalog sleeves stay `not_applicable`. Fixture encode: t1 `ready` / t2 `not_ready` `dual_split` / t4 `not_ready` `residual`. Live empty spine stays unassembled on the Choice (empty spine ≠ no BOJ). `admit` / FLUID-ADM-007 / UB-AUTH-010 stay flow+cost — PACK 4 does **not** write them. No new refuse walls.
10. Confirm Scout Tier-1 observe ids (ADM-004/005, SIZ-003, ADM-002, NWS-002/004, SIZ-006). `corr.xau_vs_eur_proxy_usd` is NO WIRE. Chair attach names (Scout packet `gtos/_scout_packets/SLEEVE_ATTACH_MAP.md`): `sleeve.gbpjpy_a_plus_ready` SHADOW; `gbpjpy_dual_leg` ≡ `gate.cross_stack_gbpjpy` resid_cap=0.15; `tokyo_event` SPLIT asia_jpy_act_ok+event_boj_window; `london_fit` SPLIT london_expand+session_overlap. Resolver `resolve_attach_name` — observe only, no refuse.
11. Confirm `pack5_fields.n == 1`, `never_admit: true`, Choice `sleeve.gbpjpy_a_plus_ready` ∈ {a_plus, almost, blocked, null_state}. Fixture encode: t1/t3 `a_plus` (PACK 5 t3 is pass-capable, not PACK 3 t3=t4); t2 `blocked` `dual_split`; t4 `blocked` `residual`. tone≠risk_off. PACK 4 answers stay {ready, not_ready, unassembled}.
12. Confirm `pack6_fields` PROVE_SEED `sleeve.xau_dsp_shakeout_a_plus_ready`. Revised fixtures **S0–S6**. Mute prefer close∈boj/warsh T±60 **or** fill∈T−90..T+60. `FILL_IN_ANY_HIGH` alone is **not** mute (S4). S6 fomc fill −40 blocked. Honesty `n_in=3` stays **S0/S1/S2**. S0 ticket `293611741` blocked. Hypothesis mute print|guidance_live OR Warsh T±60 kept. `assert_pack6_revised_mute` ok. No admit.
13. Confirm Edge FREEZE both `sleeve.*_ready` Choices (`GBPJPY_APLUS_FREEZE.md` + `XAU_DSP_SHAKEOUT_EVENT_GAP.md`, APLUS §13). Neither writes admit. `assert_edge_freeze` ok.

## Honesty (`n_in=3`)

`n_in=3` is the prove-seed in-sample bound: **S0, S1, S2**. Official lock fixtures are S0–S5; S3–S5 sit **outside** that bound. Do not quote a 6-row (or 7-row) sample as the seed.

| id | in_n | lock |
|---|---|---|
| S0 ticket `293611741` | yes | blocked `fill_in_boj_warsh_t90_t60` (Warsh fill −15). Not the 0.7467 scaler — intended risk stayed 150. |
| S1 | yes | a_plus (structure ok, no event) |
| S2 | yes | a_plus (other_high +180) |
| S3 | no | null_state |
| S4 | no | a_plus — FILL_IN_ANY_HIGH alone does not mute |
| S5 | no | blocked `close_in_boj_warsh_t60` |

Hypothesis mute on this lock: `print` / `guidance_live` (no minute window) **or** Warsh with \|T\| ≤ 60. Warsh T±60 does **not** rewrite S0’s fail_reason.

Revised window mute (S0–S6, still PROVE_SEED): prefer close∈boj/warsh T±60 **or** fill∈T−90..T+60. `FILL_IN_ANY_HIGH` alone is **not** mute (S4). S6 (fomc fill −40) is a revised-lock fixture **outside** `n_in`. This Choice does not admit.

## Do not

- Set a new APPLY wire for A+ sleeves.
- Let `GTOS_JEV_APPLY_LIVE=1` haircut `aplus_*` (code refuses; do not splice around it).
- Place, remint, flatten, or write inbox from this landing.
- Remint / manage ticket `293332188`.
- Edit host `selector_v4.py` (R2 / H1). SEL-V4-002 stays in `src/judgment/a1_log.py`.
- Add fluid gates (inventory stays 48 / 8).
- Invent DXY, funding, peer OHLC, a BOJ HIGH, or a risk-on/off print. `peers.peer_state` waits SYMBOL_STATE_V0.
- Lift `ENV-US30` from `us30_rth_vs_eth`, `gate.ny_rth_us30_act_ok`, or `ny_cash_open_us30`. Those fields are session LABELs only.
- Turn PACK 2 / PACK 3 / PACK 4 / PACK 5 / PACK 6 stubs into refuse walls. They are ADM / SIZ / NWS **inputs**. PACK 4 / PACK 5 / PACK 6 Choices are not admit Choices.
- Resize W7 armed books (`crypto` / `energy_agri` / `sub_xvol_pullback`).
- Print the TypeSafe key.

## Verify (read-only)

```
login 0  ns operator
positions / pending unchanged by this copy
no new order_send
compose.aplus_shadow_only true on any aplus_* row
```

If SYMBOL_STATE_V0 / code-walls land the same day: copy those modules too; A+ already exposes the `peers` join. Do not merge catalogs.
