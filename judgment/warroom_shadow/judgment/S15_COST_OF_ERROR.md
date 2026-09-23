# S15 COST_OF_ERROR — shadow wire

**Account:** Challenge `0` / `$110k` / magic `0` / ns `operator`  
**Compose with:** PR #29 `CONF_GATE` + S14 `REGIME_GATE_SHADOW` (same admit sidecar)  
**Flags (default unset):** `GTOS_JEV_FLUID_GATES_SHADOW` · `GTOS_JEV_FLUID_GATES_APPLY`  
**Never:** place / `order_send` / remint / flatten / invent `NEWS_PROTOCOL`

## What it does

1. Load the Close Loop tape-authority cost matrix (`judgment/astra/s15_cost_matrix.json`, schema `gtos.dig.s15.cost_matrix.v2_tape_authority`). Starter gut priors stay demoted.
2. Attach `{cost_false_yes, cost_false_no, cost_human, p, pick YES|NO|UNSURE}` beside every ADM/SIZ shadow row on the existing `run_fluid_gate_cycle` path.
3. Stamp CONF_GATE SHADOW bands (labels only, no APPLY):

| Band | Floor | Subclass | Hard-off? |
|---|---|---|---|
| `CONF_GATE_STRICT` | HIGH | `fs_half_still_losing` | no — band on confidence, not an extra size cut |
| `CONF_GATE_SESSION` | MED_HIGH | `session_cut_loss` | no — G6 ×0.75 already snapped to `{0, 0.5, 1.0}` |
| `CONF_GATE_EVENT` | HIGH_EVENT_STAMP | `event_gap_shadow` | no — **stamped proximity only** |
| `CONF_GATE_REVIEW` | KEEP_SURFACE | `full_size_loss` ticket `291087142` | no — G7 KEEP no-boost |

4. Vendor 0.50 / 0.85 stays as a **naive baseline** for the prove "moved" count. It is not Challenge truth.
5. Place / remint / flatten / broker / order = **∞ VETO** regardless of costs.

Rule:

```
E[YES]   = (1-p) * cost_false_yes
E[NO]    = p     * cost_false_no
E[HUMAN] = cost_human
pick argmin; ties → UNSURE then NO
```

Tape key facts (baked on every SHADOW / `--force` sidecar as `s15_tape_authority`):

| Fact | Value |
|---|---|
| false_abstain | **0** |
| false_admit | n=29 tape **−28.9172** shadow **−13.5428** |
| cost_avoided_by_reject | n=23 tape **−24.6586** |
| G4×G6 overshrink | **False** |
| Place | **∞ VETO** |

REVIEW `291087142` stays KEEP (not hard-off). Ticket `293128383` is KEEP×Off_hours×false_structure — review, not a new hard-off. KEEP never boosts.

Dig pack authority: `gtos/research/codila_absorb/war_room/s15_cost_of_error/` (`cost_matrix.json`, `PR29_COMPOSE_NOTES.md`, `close_loop_s15_cost_matrix_from_tape.json`, `close_loop_conf_gate_bands_false_admit_shadow.json`, `DIG_HANDOFF_CONF_GATE_S15_PR29.json`). Local copy: [`astra/DIG_HANDOFF_CONF_GATE_S15_PR29.json`](astra/DIG_HANDOFF_CONF_GATE_S15_PR29.json).

Missing cost triple → do not derive a band; stay SHADOW.

## Chair G1–G8 (do not weaken)

S15 does not change S14 `stand_down | half_size | admit_ok_label` or `size_factor`. INDEX / `xa_huge` / `orb_*` / bleed / US30 stay hard-off. G4×G6 does not double-cut. G7 KEEP no-boost stands. G5 stay shadow.

## Historical prove (no live bars)

```bash
python3 scripts/run_s15_historical_prove.py --force \
  --log-dir /tmp/s15-prove \
  --score-out /tmp/s15-prove/scorecard.json \
  --write-tape judgment/astra/lab/s15_historical_tape/TAPE_0.jsonl
```

Bars: `n_decidable ≥ 20`, `n_moved ≥ 5` (cost pick ≠ vendor-0.85 pick), `n_invented_high == 0`, `n_order_send == 0`, `false_abstain == 0`, place ∞ VETO.

`--force` writes shadow logs without exporting `GTOS_JEV_FLUID_GATES_SHADOW`. Unset flags still write nothing. APPLY stays off. Size-tilt APPLY stays refused (`s15_shadow_only_no_size_tilt_apply`) until Chair NAME after this sheet is stable.

Negative tape ⇒ adjust relative costs on the **same** Challenge identities — not idle. Do not wait for live bars.

## Tests

```bash
python3 -m pytest -q tests/judgment/test_s15_cost_of_error.py tests/judgment/test_fluid_gates.py tests/judgment/test_s14_regime_gate.py
```
