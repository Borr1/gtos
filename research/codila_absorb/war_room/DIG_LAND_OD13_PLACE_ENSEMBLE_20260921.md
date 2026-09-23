# DIG LAND — OD-13 place_choice ensemble + Noul pair — 2026-09-21

**as_of_ict:** 2026-09-21T06:28:18+07:00  
**Chair priority:** Land `SHADOW_OD_OD-13_PLACE_CHOICE_ENSEMBLE_NOUL_PAIR` onto Challenge admit path  
**APPLY:** under `GTOS_JEV_PLACE_APPLY=1` + CONF_ORDER_CONSUME  
**Dig order_send:** false (host wires fire only)

## Flow landed
1. Thin evidence / missing `discriminating_span` → **DELAY**
2. Else Noul `place_now` gate
3. Else K=3 ensemble shuffle → PLACE|STAND|DELAY|REMINT|FLATTEN_CANDIDATE
4. Prefer ensemble + Noul over raw API conf (OD-07)
5. CONF_ORDER_CONSUME: order-sensitivity → PLACE→DELAY when blocked

## Env detection
| Flag | Behavior |
|------|----------|
| `GTOS_JEV_PLACE_APPLY` | Admit APPLY |
| `GTOS_JEV_OD13_ENSEMBLE` | Default **ON** when APPLY=1; explicit off wins |
| `GTOS_JEV_CONF_ORDER_CONSUME` (or `_APPLY` / `GTOS_CONF_ORDER_CONSUME`) | Optional; else ON with APPLY (Challenge-live) |

## Smoke table
| case | action | reason | refuse_place |
|------|--------|--------|--------------|
| thin_intent | DELAY | thin_state_order_becomes_policy | true |
| rich + noul high + ensemble PLACE | PLACE | noul_and_ensemble_agree_place | false |
| rich + noul blocks | STAND | noul_blocks_ensemble_place | true |

**`evaluate_place_choice` calls ensemble on APPLY path:** YES

## Files
- `judgment/warroom_shadow/src/judgment/place_choice_ensemble.py`
- `judgment/warroom_shadow/src/judgment/place_choice.py` (patched)
- `research/warroom_20260920/judgment/warroom_shadow/src/judgment/{place_choice,place_choice_ensemble}.py`
- `_vps_pull/{place_choice,place_choice_ensemble}.py`
- `research/codila_absorb/war_room/jev_place_writer_hooks/{place_choice,place_choice_ensemble}.py`
- Stage: `_vps_pull/od13_20260921/` (+ MANIFEST.md)

## Hard
- Dig does not order_send
- No writers restart
- No live_armed_set mutate
- No NEWS invent
- refuse_place = STAND|DELAY only
- broker_effect for PLACE/REMINT/FLATTEN as before
