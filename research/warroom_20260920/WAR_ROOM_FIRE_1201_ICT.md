# WAR ROOM FIRE 1201 ICT — CONF_GATE band calibration (SHADOW)

**Owner:** Chair war-room executor  
**When:** 2026-09-20 12:06 ICT (fire ~12:01 ICT 2026-09-20)  
**Seat:** Chair box research (host-local)  
**Challenge:** 0 historical tape

## Laws observed

- Never host-mesh
- Never set `GTOS_JEV_FLUID_GATES_APPLY` / `GTOS_DIG_MULTI_STAGE_GUARD_APPLY` — **APPLY still unset**
- Never place / `order_send` (`order_send=0`)
- No NEWS invent (EVENT band = stamped proximity only)
- Jev never places
- Not a duplicate of S14/S15/S16 (those already ALL PASS at hist_prove_1008)

## What changed

Highest-leverage next step after S14/S15/S16 hist prove: **CONF_GATE band calibration against Challenge false_admit residual** (Dig handoff post gate-mining pause).

1. Absorbed close_loop packs: `gate_size_proposals`, `conf_gate_bands_false_admit_shadow`, `challenge_shadow_enforce_residual`, `s15_cost_matrix_from_tape`, win preservation, Dig CONF_GATE handoff, Codila `CHAIR_NEXT_SHADOW_WIRES` / S15 CONF absorb.
2. Ran **subclass-proxy SHADOW stand_down CF** on G4–G8 scoreboard (admission labels lack numeric confidence — honest upper-bound + pass-rate sensitivity).
3. Wrote shadow weight floors for STRICT / SESSION / EVENT / REVIEW — **LABEL only, no APPLY**.

## Scoreboard deltas

| State | Σ shadow R | Δ vs G4–G8 |
|---|---:|---:|
| Tape raw | −38.5948 | — |
| G4–G8 residual (baseline) | **+0.5857** | 0 |
| + CONF_GATE_STRICT UB stand_down (n=21 fs_half) | **+9.2984** | **+8.7127** |
| + SESSION UB (n=4) alone | (see scorecard) | +2.3231 |
| + EVENT UB (n=3) alone | (see scorecard) | +1.3063 |
| + STACK STRICT+SESSION+EVENT UB | **+12.9278** | **+12.3421** |
| REVIEW (291087142) | unchanged | 0 (LABEL only — NOT hard-off) |

- **Wins preserved** under stacked UB: **true** (0 win tickets touched).
- XAU Close Loop residual mine (−2.18 under G4–G8) stays Dig-off; STRICT UB addresses the −8.71R `fs_half_still_losing` false_admit subclass (post G4×0.5), not a new hard gate.
- Gate-size G1–G8: already enforced in residual; no new G# proposed this fire.

## Pass / fail bars (this fire)

| Bar | Result |
|---|---|
| decidable_rows | 60 PASS |
| bands_calibrated | 4 PASS |
| wins_preserved_stacked_ub | true PASS |
| order_send | 0 PASS |
| APPLY flags set | false PASS |
| news_invented | false PASS |
| broker_effect_all_false | true PASS |
| Monday-ready APPLY milestone | **NO** (numeric conf sidecar missing on hist admission) |

## Artifact paths (Chair box)

| Artifact | Path |
|---|---|
| Scorecard JSON | `/workspace/gtos/research/warroom_20260920/conf_gate_calib_1201/conf_gate_calib_scorecard.json` |
| Band weights SHADOW | `/workspace/gtos/research/warroom_20260920/conf_gate_calib_1201/conf_gate_band_weights_shadow.json` |
| MD summary | `/workspace/gtos/research/warroom_20260920/conf_gate_calib_1201/CONF_GATE_CALIB_1201.md` |
| This receipt | `/workspace/gtos/research/warroom_20260920/WAR_ROOM_FIRE_1201_ICT.md` |
| Inputs | `/workspace/gtos/close_loop/war_room_20260920/conf_gate_bands_false_admit_shadow.json` + `challenge_shadow_scoreboard_enforce_g4_g8.jsonl` |

## Recommendation

- **SHADOW wire next:** log `conf_gate_band` + disposition beside Challenge admit sidecar; floors HIGH 0.85 (STRICT/EVENT), MED_HIGH 0.70 (SESSION); REVIEW = KEEP surface only.
- **Do not APPLY** until numeric Choice/Score (or Noul concentration) exists on live/shadow rows and STRICT pass-rate sensitivity is re-run with real conf — hist prove used subclass proxy only.
- Retire vendor 0.85 only after that prove; still never place from conf band alone (confidence ≠ permission).

## Blockers

1. **Numeric confidence absent** on historical admission labels → cannot measure live HIGH hit-rate; UB CF is ceiling not promise.
2. **Not a Monday APPLY unlock** — research milestone only. Owner WakeParent only if Chair wants numeric-conf sidecar prioritized before Monday open.
3. VPS copy: **DONE** via machineId `7cfa9657-805b-4e9c-9fbb-886c500f997b` → `host-local\redacted_host\repo\research\warroom_20260920\` (`WAR_ROOM_FIRE_1201_ICT.md`, `conf_gate_calib_scorecard.json`, `conf_gate_band_weights_shadow.json`, `CONF_GATE_CALIB_1201.md`).

## APPLY confirmation

```
GTOS_JEV_FLUID_GATES_APPLY   → unset (never flipped this fire)
GTOS_DIG_MULTI_STAGE_GUARD_APPLY → unset
place / order_send / remint  → false
news_protocol invent         → false
```
