# POLICY_C STRIKE_WHEN_RIGHT — SHADOW_ADMIT_CANDIDATE — 2026-09-20 14:52 ICT

**status=`SHADOW_ADMIT_CANDIDATE`** · place=false · apply=false · order_send=0 · promote=false  
**CF variants:** PAUSED except this shadow C wire · never_merge_R · no NEWS invent

## Doctrine
STRIKE_WHEN_RIGHT via `JEV_WIN_LOSE_LEARN_strike_rule_20260920.py` · policy `C_jev_trained_multi_question`  
**C ≡ actual** on Dig_3R absorb (`delta_C_minus_actual=0.0` in Dig pack).

## mapping_honesty
KEEP→**D_FULL** · STAND→**A_STAND_DOWN** · REVIEW→**C_SIZE_TRIM**

## Choice → shadow bits (primary wire)
| Choice | verb | bit flags | cf_C_mult |
|---|---|---|---:|
| `A_STAND_DOWN` | STAND | `cf_C_stand_down_bit=true` | 0.0 |
| `C_SIZE_TRIM` | REVIEW | `cf_C_size_trim_bit=true` | 0.75 |
| `D_FULL` | KEEP | `cf_C_full_bit=true` | 1.0 |

`B_SIZE_HALF` / `E_KEEP_CAP`: not invented — only if strike_when_right already emits them (Dig C Dig3R path used A|C|D only; E possible on keep_residual_fs).

## Fanout / VPS stamp
- namespace: `payload['shadow_jev_policy_c']`
- stamp: bits + Choice + `apply=false` + `order_send=0` + place=false + promote=false
- if STATE missing → `policy_c_skip_reason=STATE_MISSING` (no invent)

## Sources
- `CF_COUNTERFACTUAL_SCOREBOARD_ABSORB_DIG3R_20260920.json` (C ≡ actual)
- `JEV_WIN_LOSE_LEARN_strike_rule_20260920.py`
- JWL_Q / P0 fanout patterns in `warroom_shadow_jev_fanout_fields.json`

## Locks
place=false · apply=false · order_send=0 · promote=false · NEVER merge R with Challenge_book
