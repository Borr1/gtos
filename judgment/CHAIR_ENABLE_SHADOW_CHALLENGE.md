# Chair: enable Challenge fluid-gate shadow

**Account:** Challenge login **0** / pass **$110k** / magic **0** / ns `operator`.  
**Quarantine:** verification **0** — do not shadow-batch it.  
**Hard locks:** Jev never places, remints, flattens, or mints tokens. APPLY never reaches a broker.  
**Do not invent** `NEWS_PROTOCOL`.

Chair ENFORCE/LABEL source: [`GTOS_SCORE_STEALS.md`](GTOS_SCORE_STEALS.md).

---

## What this is

A1 shadow cycle for Challenge fluid gates:

1. **ALIVE_MENU** — rebuild Choice criteria from the live sleeve/worker inventory each cycle (W7 armed set + launcher workers + Challenge keep-family nouns, plus any injected leftover-ship tags). Escape hatches `HOLD` / `ABSTAIN` / `ESCALATE_CHAIR` / `BLOCKED` always present. Cap 255.
2. **CONF_GATE** — log `LOW` / `MED` / `HIGH` (starter 0.50 / 0.85). Confidence is not permission. `broker_effect` is always `false`.
3. **DONE_OUTSIDE** — code verifies the log (and any LABEL draft) exists and matches contract. Jev `DONE` is advisory only.
4. **S14 REGIME_GATE_SHADOW** — optional same-sidecar leg. Emits **bucketed** regime state from `gold_state.v0` (no raw OHLCV / ticks), one System One question pack (`regime_type` + `regime_change_likely` + `strategy_viable`), code compose → `stand_down | half_size | admit_ok_label` + logged `size_factor`. Cache by `sha256(bucket_state)`. Labels only — never place.
5. **S15 COST_OF_ERROR** — same admit sidecar. Logs tape-authority `{cost_false_yes, cost_false_no, cost_human, p, pick YES|NO|UNSURE}` plus Close Loop CONF_GATE SHADOW bands (`STRICT` / `SESSION` / `EVENT` / `REVIEW`). Sidecar stamps `s15_tape_authority` (false_abstain **0**; false_admit n=29 tape **−28.9172** shadow **−13.5428**; reject n=23 tape **−24.6586**; G4×G6 overshrink **False**; place **∞ VETO**). REVIEW `291087142` KEEP not hard-off; `293128383` KEEP×Off_hours is review only. Vendor 0.85 is a naive baseline only. No APPLY. No NEWS invent.

Writer / `run_book.py` / `order_send` are not imported.

---

## Enable shadow (A1) — this is the Chair step

On the Challenge host or Cloud Agent env for `Borr1/ai-trading-agent`:

```bash
export GTOS_JEV_FLUID_GATES_SHADOW=1
# equivalent sidecar fan-out (not a parallel place path):
# export GTOS_JEV_EVERYWHERE_SHADOW=1
# optional: TYPESAFE_API_KEY in secrets only — this cycle does not call TypeSafe
# optional: GTOS_JEV_FLUID_GATES_LOG_DIR=/path/to/judgment/live/jev_sidecar

python3 scripts/run_jev_fluid_gates_shadow.py
```

`--force` runs one dry-run when the env flag is unset (still shadow-only; still no broker).

Logs land at:

```
judgment/live/jev_sidecar/admit/<YYYY-MM-DD>/<cycle_id>.json
```

Each row stamps `mode: shadow_log_only`, `never_place/remint/flatten: true`, `login: 0`, `broker_effect: false`.

Without `GTOS_JEV_FLUID_GATES_SHADOW=1` the script exits 2 and writes nothing. That is the default.

---

## APPLY stays off

`GTOS_JEV_FLUID_GATES_APPLY` defaults **unset**. Even with HIGH confidence, the cycle only logs.

To allow a **LABEL draft** (file write, Chair verb LABEL, never place):

1. Keep shadow on.
2. Drop a prove receipt that uses an existing Alive-organism class — **A1**, **A2**, **A3**, or **W_named** — not A0 and not B-forbidden:

```json
{
  "site_id": "UB-AUTH-010",
  "wire_class": "A1",
  "proven": true,
  "owner_word": "chair named this site",
  "named_at": "2026-09-20T00:00:00Z"
}
```

Save as `judgment/live/prove/UB-AUTH-010.json` (or set `GTOS_JEV_FLUID_GATES_PROVE_DIR`).

3. `export GTOS_JEV_FLUID_GATES_APPLY=1`
4. Stake must be `label_assist` / `read_only` (MED+) or `sleeve_admit` / `corr_hold` (HIGH+).  
   `place` / `remint` / `flatten` / `broker` / `order` are **VETO** at every band.

```bash
GTOS_JEV_FLUID_GATES_SHADOW=1 \
GTOS_JEV_FLUID_GATES_APPLY=1 \
python3 scripts/run_jev_fluid_gates_shadow.py \
  --prove-site UB-AUTH-010 --stake label_assist --confidence 0.7
```

A passing APPLY writes `judgment/live/jev_sidecar/apply/<day>/<cycle_id>.json` with `chair_verb: LABEL`. Chair still writes `verdict.json` if anyone speaks VETO.

---

## What Chair does **not** do from this sidecar

- Remint activation tokens.
- Flatten or shut `live_broker_authority`.
- Splice `--tags`.
- Call TypeSafe unless the owner later puts `TYPESAFE_API_KEY` in secrets **and** a later PR adds a client. This PR injects answers for tests / dry-run only.
- Invent HIGH / `NEWS_PROTOCOL`. Empty spine ⇒ event questions abstain.

---

## S14 historical prove (no live bars)

Do **not** wait for a live feed or host-mesh. Replay the Challenge `0` tape already on disk:

```bash
python3 scripts/run_s14_historical_prove.py --force \
  --log-dir /tmp/s14-prove \
  --score-out /tmp/s14-prove/scorecard.json \
  --write-tape judgment/astra/lab/s14_historical_tape/TAPE_0.jsonl
```

`--force` is the dry-run analog of `GTOS_JEV_FLUID_GATES_SHADOW=1`. APPLY stays off. The tape is gold_state buckets + cached/injected System One answers (no TypeSafe network, no live M15). Negative scorecard ⇒ research/adjust thresholds or favored_regimes on the **same** tape — not idle.

One-row sidecar (same flags):

```bash
python3 scripts/run_jev_fluid_gates_shadow.py --force \
  --gold-state /path/to/gold_state.json \
  --s14-answers /path/to/answers.json \
  --s14-research-thresholds
```

Research thresholds (`0.85` / `0.50`) are prove starters. Production compose leaves them unset (fail-closed stand_down after floors) until S15. Chair G1–G8 hard-offs (INDEX / xa_huge / orb_crypto / bleed / US30) and KEEP no-boost are not weakened.

See [`S14_REGIME_GATE_SHADOW.md`](S14_REGIME_GATE_SHADOW.md).

## S15 historical prove (no live bars)

Do **not** wait for a live feed. Replay the Challenge `0` Close Loop tape already encoded in `src/judgment/s15_tape.py`:

```bash
python3 scripts/run_s15_historical_prove.py --force \
  --log-dir /tmp/s15-prove \
  --score-out /tmp/s15-prove/scorecard.json \
  --write-tape judgment/astra/lab/s15_historical_tape/TAPE_0.jsonl
```

Bars: `n_decidable ≥ 20`, `n_moved ≥ 5`, `n_invented_high == 0`, `n_order_send == 0`, `false_abstain == 0`, place ∞ VETO. Negative sheet ⇒ adjust relative costs on the **same** tape — not idle.

See [`S15_COST_OF_ERROR.md`](S15_COST_OF_ERROR.md).

## Jev-everywhere historical prove (no live bars)

Sit Choice/Score/Noul on every **safe** decision site on the same sidecar. Walk Challenge `0` Close Loop tickets (S15 tape). Do **not** wait for a live bar.

```bash
python3 scripts/run_jev_everywhere_historical_prove.py --force \
  --log-dir /tmp/jev-everywhere \
  --write-tape judgment/astra/lab/jev_everywhere_closes/TAPE_0.jsonl \
  --write-map judgment/astra/jev_everywhere_sites.json \
  --score-out /tmp/jev-everywhere/scorecard.json
```

Bars: decidable ≥ 20, moved ≥ 5, sites ≥ 10, invented_high == 0, order_send == 0, no flatten in `action_scope`, hard-off families untouched, place ∞ VETO. No new hard-off cages. See [`JEV_EVERYWHERE.md`](JEV_EVERYWHERE.md).

## P0 warroom_shadow stubs (FIRE 1404 — apply always false)

Same sidecar. Stamps `conf_gate_band_disposition` (`STRICT`/`SESSION`/`EVENT`/`REVIEW`/`KEEP`)
plus four unwired hooks. FIRE 1201 floors stay SHADOW — hist labels lack
numeric conf, so **do not flip APPLY**. KEEP signature is read from STATE,
not a sleeve-name allowlist. Cost is never a kill-gate.

Chair enable + FIRE 1201 hist-prove (SHADOW only):

```bash
GTOS_JEV_FLUID_GATES_SHADOW=1 python3 scripts/run_p0_shadow_hooks_historical_prove.py \
  --log-dir /tmp/p0-shadow \
  --score-out /tmp/p0-shadow/scorecard.json \
  --receipt-out /tmp/p0-shadow/fire1201.json
```

`--force` is CI only. Never set `GTOS_JEV_FLUID_GATES_APPLY` or
`GTOS_DIG_MULTI_STAGE_GUARD_APPLY`. See
[`CHAIR_P0_SHADOW_ENABLE_HIST_PROVE.md`](CHAIR_P0_SHADOW_ENABLE_HIST_PROVE.md)
and [`P0_UNWIRED_SHADOW_HOOKS.md`](P0_UNWIRED_SHADOW_HOOKS.md).

## Tests

```bash
python3 -m pytest -q tests/judgment
```
