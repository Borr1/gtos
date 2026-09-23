# HOST B — occupancy + governor into live gold_state

Chair land after Ultragoal Scout priority B. Copy `src/judgment/` onto
Challenge f5-live (`0` / `operator` only). Do **not**
wholesale-copy GitHub `book_owner.py` onto the ~10069-line dirty host.

Schema was ready. Shadow already fills occupancy from the deal tape.
Live haircut + A1 called `intent_gold_state` with no occupancy arg and
no governor kwarg, so `completeness.occupancy` stayed false and
`governor` stayed empty. This wave wires the host tape through.

Never place. Never remint. Never flatten. Do not invent DXY / yields.
Do not touch Fable `MinimalSizeScaler` / `honor_f5_scaler_risk`.

## What Chair copies

1. Copy `src/judgment/` (especially `host_occupancy.py`, `a1_log.py`,
   `apply_size.py`, `gold_state.py`, `occupancy.py`, `two_stop.py`).
2. Keep the existing haircut / A1 splices. Add **one helper call**
   after `cost_skip = self._spread_cost_screen(...)` and pass the
   extras into both observe and haircut.

```python
from src.judgment.host_occupancy import host_occupancy_governor
from src.judgment.a1_log import maybe_observe_fluid_at_place, maybe_observe_ub_plc_017
from src.judgment.apply_size import haircut_challenge_unit

# after cost_skip = self._spread_cost_screen(intent, tick)
pack = host_occupancy_governor(
    symbol=intent.symbol,
    as_of=now,                    # cycle UTC
    ticket=getattr(intent, "ticket", None) or getattr(intent, "candidate_id", None),
    sleeve=intent.sleeve,
    account_state=account_state,  # router bag (equity / baseline)
    opens=open_positions_snapshot,  # _open_book_positions_snapshot()
    # closed_doc omitted → loads pipeline_state/.../just_closed_siblings.json
    decision=decision,            # decision.governor
    governor_state=gs,            # GovernorState.open_risk_pct / realized_today_pct
    namespace=self._namespace,    # operator
)
occ, gov = pack["occupancy"], pack["governor"]

maybe_observe_ub_plc_017(intent, tick, cost_skip, occupancy=occ, governor=gov)
maybe_observe_fluid_at_place(intent, tick, cost_skip, occupancy=occ, governor=gov)

# after cost_skip is None, same extras:
adjusted_unit = haircut_challenge_unit(
    adjusted_unit,
    intent=intent,
    tick=tick,
    login=<mt5 login>,
    ns=self._namespace,
    already_admitted=True,
    evaluate_jev=True,
    occupancy=occ,
    governor=gov,
)
```

GitHub `book_owner.py` already has this reference splice. Dirty host
gets the helper call only — do not replace the 10069-line file.

## What the helper reads

| Input | Occupancy | Governor |
|---|---|---|
| `opens` / open book | `occupancy_at` — `symbol_open`, `minutes_since_flat`, cluster labels | — |
| `closed[]` / `just_closed_siblings.json` | `occupancy_from_closed` — 2-stop **label** (envelope COUNT stays the integer) | — |
| `decision.governor` | — | `allow_new` ← `allow_new_entries`; `cap_mult` ← `size_cap_multiplier`; `reason` |
| `governor_state` (`gs`) | — | `open_risk_pct`, `realized_today_pct` |
| `account_state` | optional `positions` / `opens` bag | named fields only if present |

Missing tape stays visible (`None` fields, `occupancy_source=deal_tape_absent`).
Empty searched tape is `symbol_open=False`, not invented crowded.

## Prove B on the next A1 / haircut row

On the next Challenge observe or `cost_skip is None` place:

1. `state.completeness.occupancy` is **true** when the open book is
   non-empty (or closed[] supplied a named fact).
2. `state.occupancy.symbol_open` and `minutes_since_flat` are **not
   null** when another same-symbol position is open and a prior close
   exists on the host tape.
3. `state.governor.open_risk_pct` **mirrors** `gs.open_risk_pct`
   (or the named host field). Do not invent a number.

If occupancy is still false and governor is empty, the helper was not
spliced or extras were not forwarded into `intent_gold_state`.

## Env / restart

Unchanged: `GTOS_JEV_ALIVE_SHADOW=1` `GTOS_JEV_APPLY_LIVE=1`
`GTOS_JEV_A1_LOG=1`. TypeSafe fp `00000000`.

Restart **only** `GTOS_F5_FTMO`. No remint. No flatten. No place from
this seat. Do not set APPLY_LIVE on W7 / `run_book.py`.
