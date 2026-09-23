# CONF_GATE band calibration — Challenge 0 — 2026-09-20 12:06 ICT

**Mode:** SHADOW only · APPLY unset · order_send=0 · no NEWS invent · no host-mesh

## Baseline (G4–G8 already enforced)
- tape ΣR **-38.5948** → G4–G8 shadow residual **0.5857**
- false_admit n=29 shadow ΣR=-13.5428
- XAU leftover under G4–G8: **-2.1797** (Close Loop mine)

## Upper-bound stand_down CF (subclass proxy — numeric conf absent on hist labels)

| Scenario | n_stand | Σshadow after | Δ vs G4G8 | wins touched |
|---|---:|---:|---:|---:|
| S0_G4G8_BASELINE | 0 | 0.5857 | +0.0000 | 0 |
| S_CONF_GATE_STRICT_UB_STAND_DOWN | 21 | 9.2984 | +8.7127 | 0 |
| S_CONF_GATE_SESSION_UB_STAND_DOWN | 4 | 2.9088 | +2.3231 | 0 |
| S_CONF_GATE_EVENT_UB_STAND_DOWN | 3 | 1.8920 | +1.3063 | 0 |
| S_CONF_GATE_REVIEW_LABEL_ONLY | 0 | 0.5857 | +0.0000 | 0 |
| S_STACK_STRICT_SESSION_EVENT_UB | 28 | 12.9278 | +12.3421 | 0 |

## STRICT pass-rate sensitivity (optimistic = best tickets still HIGH-admit)

| pass_frac | mode | n_stand | Σshadow after | Δ |
|---:|---|---:|---:|---:|
| 0.00 | optimistic_best_pass | 21 | 9.2984 | +8.7127 |
| 0.25 | optimistic_best_pass | 16 | 7.5293 | +6.9436 |
| 0.50 | optimistic_best_pass | 11 | 5.6643 | +5.0786 |
| 0.75 | optimistic_best_pass | 5 | 3.2157 | +2.6300 |
| 1.00 | optimistic_best_pass | 0 | 0.5857 | +0.0000 |

## Win preservation
- wins n=7 tapeΣ=15.921 shadowΣ=15.0685
- stacked UB wins touched: **[]** → preserved=True

## Recommendation
CONF_GATE STRICT UB stand_down removes fs_half residual (−8.71R shadow) with 0 wins touched; but hist admission labels lack numeric confidence — cannot prove live HIGH-floor hit-rate yet. SHADOW wire: log conf_gate_band + disposition beside admit; keep APPLY unset until numeric conf sidecar on live/shadow proves pass-rate.

- STRICT UB ΔR = **+8.7127**
- STACK UB ΔR = **+12.3421** → residual **12.9278**
- Monday-ready milestone: **NO** (need numeric conf sidecar before APPLY discussion)
- APPLY still **unset**. Dig stays off XAU residual mine.

## Artifacts
- `/workspace/gtos/research/warroom_20260920/conf_gate_calib_1201/conf_gate_calib_scorecard.json`
- `/workspace/gtos/research/warroom_20260920/conf_gate_calib_1201/conf_gate_band_weights_shadow.json`
