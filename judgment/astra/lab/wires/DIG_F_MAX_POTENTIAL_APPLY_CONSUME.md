# Dig F MAX_POTENTIAL — APPLY_CONSUME

Challenge **0** / ns `operator` / magic **0** / pass **$110k**.
Dig never broker-sends. No NEWS_PROTOCOL invent. `pack1b_beaten=false`.

Chair already live (no new broker flags): `CONF_ORDER_CONSUME=1`, `PLACE_APPLY=1`, `PLACE_ENSEMBLE=1`.

## APPLY_CONSUME

| name | verdict | where | effect |
|---|---|---|---|
| `option_order_sensitivity` | APPLY_CONSUME | `src/judgment/place_choice.py` | option *order* is hashed; different order ≠ same stamp |
| `state_evidence_sufficiency` | APPLY_CONSUME | `src/judgment/place_choice.py` | `state_hash` required; incomplete digest refuses |
| `jev_repeatability_probe` | APPLY_CONSUME | `src/judgment/place_choice.py` | same inputs restamp identically |
| `noul_vs_choice_shape` | APPLY_CONSUME | `src/judgment/conf_gate.py` | Choice vs Noul bands; disagree downgrades HIGH |
| `od_13` | APPLY_CONSUME | `src/judgment/od13_ensemble.py` | **ALREADY_LIVE** under `PLACE_APPLY` / `PLACE_ENSEMBLE` |

`place_choice` hash stamps refuse incomplete `menu_hash` / `option_order_hash` / `state_hash`.
`conf_gate_order_block` HIGH-blocks when the band is a deterministic HIGH; vendor det false → MED.

## KILL_ENFORCE (ignore standalone APPLY)

| name | verdict | reason |
|---|---|---|
| `order_ensemble_shuffle` | KILL_ENFORCE | subsumed by OD-13 |
| `od_10_perm_avg_research_router` | KILL_ENFORCE | research router, not place/conf |
| `od_12_yesno_reverse_regression` | KILL_ENFORCE | CI only |

Fence: `src/judgment/order_ensemble_shuffle.py` — every APPLY entrypoint raises.
No standalone `ORDER_ENSEMBLE` path.

## Cycle sidecar

`run_fluid_gate_cycle` now stamps `place_choice`, `conf_order_block`, `od13_ensemble`,
`jev_repeatability_probe`, and `already_live_consume` on the same admit sidecar.
Writer still places. Jev still does not `order_send`.
