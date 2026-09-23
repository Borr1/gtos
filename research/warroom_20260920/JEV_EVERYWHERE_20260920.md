# JEV EVERYWHERE — 2026-09-20
**Mandate:** Jev questions on every admission surface that matters — not only admit yes/no.  
**Corpus:** Challenge historical closes n=60 · login 0 · 2026-09-20 13:20 ICT

## Covered now (train rows)
- **admit** Choice (hard_refuse / abstain / admit)
- **size_intent** Choice (stand_down / quarter / half / full)
- **surface_ok** Noul
- **toxic_family** Noul
- **geometry_quality** Score 0–2
- **session_fit** Score 0–2
- **cost_of_error** Score 0–2
- **event_proximity_ok** Noul (stamps only — never invent NEWS)
- **remint_risk** Noul

## Gaps (must hydrate before live Jev claim)
| surface | status | gap |
|---|---|---|
| regime | MISSING | regime_tag null ×60 — S14 |
| occupancy | MISSING | no concurrent open-count on scoreboard |
| corr_hold | MISSING | corr_cluster mostly unknown |
| confidence | SHADOW-only | do not wait on live conf for train |
| event | stamps_only | BOJ stamp; no NEWS invent |

## CF-C uses multi-question labels
Policy C does **not** collapse to a single panic hard-off bit. Fusion:
1. `size_intent=stand_down` OR `admit=hard_refuse` → stand_down
2. `event_proximity_ok` low (stamped) → stand_down
3. `toxic_family` high ∧ `surface_ok` low → stand_down
4. `cost_of_error≥2` ∧ toxic high → stand_down
5. else `size_intent` half/full → half_size / admit
6. keep surfaces with desired admit → full size (no boost)

Historical CF-C sumR = **8.9314** (vs A **-38.5948**).

## Desired label distribution
admit=7 · half_size=15 · stand_down=38

## Next concrete iteration (do not wait for owner)
See `jev_train_next_iteration.json` — hydrate regime/occupancy/corr; fuse S15 cost into admit; wire size_intent first-class; G8 remint sequence feature.

## Laws
- No order_send · No place · No NEWS invent · Panic hard-off religion revoked for research · CF ≠ live


## Honesty — CF-C oracle caveat
CF-C applies **outcome-oracle** `desired_label` (stand_down/half_size/admit) derived from miss/why/family after the close. Multi-question Choice/Score/Noul explain the label bundle, but this is **not** a claim that live Jev would have refused at entry. Treat C as an upper-bound train target (ΔC−A = +47.5R) with **false_abstain=0 on 7 ok_wins**. Next iteration must re-score C with **entry-time features only** (no miss_type leak) once regime/occupancy/corr hydrate.

