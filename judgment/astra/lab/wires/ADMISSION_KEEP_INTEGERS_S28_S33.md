# Admission KEEP/KILL integers — Challenge 0

Hist authority: **Dig B STATIC remaining board** (supersedes CHAIR_CONSUME_STale S29 KILL; consume is stale; do not re-score).

- login `0` / ns `operator`
- `ADMISSION_APPLY=0` (hardcoded 0)
- `pack1b_beaten=False`
- Choice wired: `4` KEEP rows
- resting SHADOW: `0`
- Envelope walls stay integers. Never place / remint / flatten / order_send.

## Hist table S28–S33

| sid | name | hist | verdict | Choice | APPLY |
|---|---|---|---|---|---|
| S28 | `circuit_breaker_open` | APPLY_CANDIDATE_KEEP | **KEEP** | True | 0 |
| S29 | `soft_daily_stop_reached` | APPLY_CANDIDATE_KEEP | **KEEP** | True | 0 |
| S30 | `derisking_into_maxdd_wall` | APPLY_CANDIDATE_KEEP | **KEEP** | True | 0 |
| S31 | `profit_target_protect_derisk` | KILL | **KILL** | False | 0 |
| S32 | `ceiling_profile_requires_smooth_ddefense` | APPLY_CANDIDATE_KEEP | **KEEP** | True | 0 |
| S33 | `leader_impulse_veto` | KILL | **KILL** | False | 0 |

## Env flags

See [`judgment/ADMISSION_KEEP_INTEGERS.md`](../../ADMISSION_KEEP_INTEGERS.md).

- `GTOS_JEV_ADMISSION_APPLY` — reserved; ignored; APPLY stays 0
- `GTOS_JEV_ADMISSION_CHOICE` — default on; KEEP-only Choice
- `GTOS_JEV_ADMISSION_KEEP` — default on; Challenge stamp
- `GTOS_JEV_APPLY_LIVE` / `GTOS_JEV_FLUID_GATES_APPLY` do **not** open admission APPLY

KEEP = house integer + Choice LABEL. APPLY stays 0. KILL = dead soft/Jev path, no Choice, no SHADOW. ENV-DD stays the hard floor. Dig never order_send.
