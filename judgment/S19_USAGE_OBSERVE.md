# S19 USAGE_OBSERVE — skip-path continues (Challenge writer)

**Compose with:** existing A1 / Alive observe at UB-PLC-017.  
**Not** S16 Dig/Chair. **Not** APPLY. **Not** NEWS invent.  
**Login:** `0` (`operator`, magic `0`).  
**pack1b_beaten:** false.

## What it does

`src.judgment.book_owner_observe_splice` is the host-safe call.
Not re-exported from `src.judgment.__init__` — the package isolation
scan treats any `ImportFrom` whose module name contains `book_owner`
as a place-path import.

| API | Role |
|---|---|
| `usage_observe_on()` | OR of `GTOS_JEV_A1_LOG` / `GTOS_JEV_ALIVE_SHADOW` / `GTOS_JEV_A1_OBSERVE_EVERY` / `A1_OBSERVE_EVERY` |
| `observe_before_continue(..., cost_skip=)` | cost-screen site — `maybe_observe_ub_plc_017` + `maybe_observe_fluid_at_place` |
| `observe_before_continue(..., skipped_row=)` | earlier skip-path continues — EVERY only |

`book_owner` env-gates BEFORE import. Occupancy / haircut stay in `book_owner`. Skip decisions stay caller-owned.

## Laws

- Never mutate `cost_skip` or `skipped_row`.
- Never raise into the place loop.
- Never import s16. Never consult the Dig dual-flag.
- Never invent `NEWS_PROTOCOL`.
- Do not wholesale-copy `book_owner.py` onto the 10069-line host tree.

## Prove

```bash
python3 -m pytest -q tests/judgment/test_book_owner_observe_splice.py tests/judgment/test_host_sites.py
```
