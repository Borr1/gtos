# Host land note — APLU-OBS-001 (SHADOW only)

Chair accepted the multi-instrument A+ diagnosis. This note is **how the dirty
host `book_owner.py` would call** the A+ observe helper. It is **not** a splice
on this tree and **not** APPLY.

Unlocks 2–5 only: observe body carries `setup_grade` / `framework` /
`kill_zone` / POI. `APLU-OBS-001` stays default-off.

## Do not

- Wholesale-copy GitHub `book_owner.py` onto the dirty **10069-line** host.
  Host file and GitHub main are different animals (`host_sites.py`).
- Edit `selector_v4.py` (R2 / H1). Do not import judgment from it.
- Place, remint, flatten, or write inbox.
- Soft-open envelope walls (`$KILL`, 2-stop **COUNT**, token digest, H8
  flatten, hard DD, `us30_off`). They stay integers.
- Expand `--tags` / `live_armed_set.json`. Armed set stays
  `crypto`, `energy_agri`, `sub_xvol_pullback`.
- Set `GTOS_JEV_APPLY_LIVE` for this hook. This helper never haircuts.

## Env-gate BEFORE import

Same pattern as `UB-PLC-017`. Do not pay a `judgment` import on the fire
path unless shadow is on.

```
GTOS_JEV_A1_LOG=1
# or
GTOS_JEV_ALIVE_SHADOW=1
```

Absent / unset → helper returns `skipped: GTOS_JEV_A1_LOG_off` and the
host must not import.

## Where to splice (mapped site)

Same CALL as `UB-PLC-017`:

| Tree | File | Needle |
|---|---|---|
| Host dirty f5-live | `src/components/ultimate_book/book_owner.py` | `def _spread_cost_screen` pulled **:9531**, then its **CALL** |
| GitHub this tree | same path | `cost_skip = self._spread_cost_screen` (after that assignment) |

**AFTER** `cost_skip = self._spread_cost_screen(intent, tick)`.
**BEFORE** `if cost_skip is not None`.
**Do not mutate `cost_skip`.**

## Call shape (copy these lines — not the file)

```python
cost_skip = self._spread_cost_screen(intent, tick)
_jev_shadow = (
    str(os.environ.get("GTOS_JEV_A1_LOG", "")).strip().lower() in {"1", "true", "yes"}
    or str(os.environ.get("GTOS_JEV_ALIVE_SHADOW", "")).strip().lower() in {"1", "true", "yes"}
)
if _jev_shadow:
    try:
        from src.judgment.aplus_pipe import maybe_observe_aplus_at_place
        maybe_observe_aplus_at_place(intent, tick, cost_skip)
    except Exception:
        pass
# cost_skip is unchanged. Envelope walls are unchanged. No send.
```

Copy `src/judgment/` (unbound) onto the host if it is missing. Do **not**
copy GitHub `book_owner.py` wholesale to land this.

## Observe body (SHADOW)

`maybe_observe_aplus_at_place` → `observe_aplus_candidate` (`APLU-OBS-001`)
stamps fluid inventory and carries:

- `setup_grade`
- `framework`
- `kill_zone`
- `poi` (`poi_type` / `price` / `zone` / `causing_event_type` — or
  `source: unassembled` if the packet has none)

Gold `levels.poi` is **not** written. XAU rows keep `gold_state.v0`.
GBPUSD rows stay GBPUSD (`symbol_state.v0`). Missing symbol stays empty.

W7 `TradeIntent` today has no grade / framework / POI. The helper still
logs the row (honest empty A+ fields) and does not invent them.

## This tree

`maybe_observe_aplus_at_place` is **not** imported from
`book_owner.py` / `bridge.py` / `selector_v4.py` here. Land on the host
by the snippet above, or not at all. Envelope and `--tags` do not move.
