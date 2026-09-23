# DIG_E_LAND_CONSUME — Challenge dual-flag verdicts (2026-09-21)

**Board:** `APPLY_KILL_RECEIPTS_DUAL_FLAGS_CHALLENGE_20260921`  
**Account:** Challenge login **0** / ns `operator` / magic `0`  
**Pull:** this tip onto `cursor/swarm-land-challenge-3c51` (HOST swarm land / VPS `f5-live`). **Not W7 `main`.**  
**Machine receipt:** [`astra/lab/wires/DIG_E_LAND_CONSUME.json`](astra/lab/wires/DIG_E_LAND_CONSUME.json)  
**Flag register:** [`../docs/flags/README.md`](../docs/flags/README.md)

Jev never `order_send`. Dig `place=false` `apply=false`. Do not invent `NEWS_PROTOCOL`. `pack1b_beaten=false`. redacted_account / W7 untouched. `POLICY_C_SHADOW_EVAL` already `=1` — not re-litigated.

---

## Verdicts consumed

### 1. EVERYWHERE_SHADOW — APPLY_CANDIDATE ALREADY_LIVE

`GTOS_JEV_EVERYWHERE_SHADOW` is an alias of `GTOS_JEV_FLUID_GATES_SHADOW` (same sidecar write). Dig E confirms that alias. It is **not** listed as open `IN_PROVE` in `docs/flags`. `everywhere_is_open_in_prove()` is `False`.

### 2. TRAIN_HARVEST — ALREADY_LIVE SHADOW+CALL=1 APPLY=0

Confirm only. No `TRAIN_HARVEST` env exists and none was invented. Harvest attach (`attach_harvest_blocks`) + cycle `harvest=` CALL into `evaluate_s14` are already live. Shadow labels only. `ready_to_apply=false`. Live multiplier `1.0`. APPLY stays `0`.

### 3. DIG_MULTI_STAGE_GUARD — KILL

`GTOS_DIG_MULTI_STAGE_GUARD_SHADOW` default/off path is explicit `0`. `GTOS_DIG_MULTI_STAGE_GUARD_APPLY` is unset/forbidden (`s16_apply_enabled()` always `False`; env-set refuses prove exit 2). Removed from `CHALLENGE_PROVE_ONLY_DUAL_FLAGS`. Offline `--shadow` / `--force` remains shadow-only and never places.

---

## Files

- `src/judgment/flags.py`
- `src/judgment/s16_flags.py`
- `src/judgment/s16_fixtures.py`
- `src/judgment/s16_guard.py`
- `scripts/run_s16_prove.py`
- `judgment/CHAIR_LAND_RECIPE_VPS_F5_LIVE.md`
- `docs/flags/README.md`
- `docs/flags/CHALLENGE_DUAL_FLAGS.json`
