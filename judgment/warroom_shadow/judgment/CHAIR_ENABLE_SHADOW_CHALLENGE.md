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

Writer / `run_book.py` / `order_send` are not imported.

---

## Enable shadow (A1) — this is the Chair step

On the Challenge host or Cloud Agent env for `Borr1/ai-trading-agent`:

```bash
export GTOS_JEV_FLUID_GATES_SHADOW=1
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

## Tests

```bash
python3 -m pytest -q tests/judgment
```
