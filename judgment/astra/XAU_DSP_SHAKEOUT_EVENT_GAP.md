# XAU DSP shakeout — event-gap PROVE_SEED (SHADOW)

Frozen PACK 6 Choice. No admit. Official fixtures **S0–S5**. Honesty **`n_in=3`** = S0/S1/S2 only — not a 6-row sample.

**Choice:** `sleeve.xau_dsp_shakeout_a_plus_ready` ∈ {a_plus, almost, blocked, null_state}

**Seed ticket:** `293611741` (S0). Fill `2026-09-18T01:45:50Z`, comment `F5:dsp_shakeout_`, login `0` / ns `operator`. Receipt tilt 0.7467; intended risk stayed 150. PACK 6 blocks S0 via Warsh fill-window mute, not via the scaler.

**Hypothesis mute:** boj ∈ {print, guidance_live} **or** Warsh T±60. `print` / `guidance_live` mute with no minute window. Warsh T±60 does not rewrite S0’s fail_reason.

**Revised mute** (supersedes “FILL_IN_ANY_HIGH alone”). Prefer close, then fill:

- close ∈ boj/warsh T±60 → `close_in_boj_warsh_t60`
- **or** fill ∈ T−90..T+60 → `fill_in_boj_warsh_t90_t60`
- `FILL_IN_ANY_HIGH` alone does **not** mute (S4)

`boj/warsh` class set: boj, warsh, fomc, nfp, cpi, boe, guidance_live, print.

| id | in_n | expect |
|---|---|---|
| S0 | yes | blocked fill_in_boj_warsh_t90_t60 |
| S1 | yes | a_plus |
| S2 | yes | a_plus |
| S3 | no | null_state |
| S4 | no | a_plus (FILL_IN_ANY_HIGH alone) |
| S5 | no | blocked close_in_boj_warsh_t60 |
| S6 | no | blocked fill_in_boj_warsh_t90_t60 |

n_in = 3 is the honesty bound, not a sample of seven.

Does not write `admit` / FLUID-ADM-007 / UB-AUTH-010.
Paired freeze: `GBPJPY_APLUS_FREEZE.md`. Both Choices: `APLUS_SLEEVES_ON_GATES.md` §13.
