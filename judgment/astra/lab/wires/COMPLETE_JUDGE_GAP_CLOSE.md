# Complete-judge gap close — Challenge 0

Owner law: Jev-everywhere. Static code keeps envelope (identity, prop walls,
fail-closed if Jev dark). Hist on Challenge tape before APPLY that changes
fire rate. No invented NEWS_PROTOCOL. Chair lock stays 48 fluid / 8 envelope.

Typesafe budget: `DEFAULT_MAX_CALLS = 500000` (Chair-raised; was 200). Tests
still override via `GTOS_JEV_MAX_CALLS=2`.

No open `IN_PROVE` without a hist path.

| ID | Module | Verdict | Primitive | Hist path | APPLY fire rate? |
|---|---|---|---|---|---|
| `CJ-ADM-RESIDUAL` | admit residual reasons | **APPLY_CANDIDATE** | Choice | S15/everywhere + overlays 291072108 / 291087142 | no |
| `CJ-CHAIR-G4` | chair_enforce G4 soft | **APPLY_CANDIDATE** | Choice | S15 `g4_applies` + KEEP overlay | no (ceiling STATIC) |
| `CJ-CHAIR-G6` | chair_enforce G6 soft | **APPLY_CANDIDATE** | Choice | S15 session_cut / off_hours + KEEP overlay | no (ceiling STATIC) |
| `CJ-CHAIR-G8` | chair_enforce G8 soft | **APPLY_CANDIDATE** | Noul | S15 occupancy + 291392252 overlays | no |
| `FLUID-HLD-005` | trail_vs_orig | **KILL** | — | ≥20 tickets named final vs orig, both poles. Do not invent `stop_now`. | no |
| `FLUID-HLD-008` | friday_cutoff_label | **KILL** | — | sit/deals after Friday 16:00Z+. Do not use asia Friday. | no |
| `FLUID-NWS-005` | spine_empty_honesty | **KILL** | — | as-of outside 10d spine AFTER host writer READ. No NEWS_PROTOCOL. | no |
| `CJ-APPLY-SIZE` | apply_size residual | **KILL** | — | n/a — envelope arithmetic, not a judgment | no |
| `CJ-REMINT-FLATTEN-CONSUME` | book_owner consume | **KILL** | — | n/a — Infinity VETO, no drafts | no |

## APPLY_CANDIDATE wire stubs

- `src/judgment/complete_judge.py` — COMPLETE_STATE view + typed questions
- `src/judgment/chair_enforce.py` — `soft_g4_choice` / `soft_g6_choice` / `soft_g8_noul` stamps; `size_ceiling` unchanged
- sidecar sites on `jev_fluid_gate_v1`: `admit_residual`, `chair_soft_g4`, `chair_soft_g6`, `chair_soft_g8`
- prove: `src/judgment/complete_judge_prove.py` + `scripts/run_complete_judge_historical_prove.py`

Hard-offs G1–G3 / INDEX / US30 stay envelope integers. SEL-V4-002 stays research-only.

## KILL WHY (short)

- Trail / Friday / empty spine: same missing poles as `SHADOW_UNLOCK_BACKLOG.md`. Waiting is the hist path. Inventing is forbidden.
- apply_size leftover is identity + compose of already-Jev tilts.
- remint/flatten consume drafts do not exist; flatten is H8 envelope.
