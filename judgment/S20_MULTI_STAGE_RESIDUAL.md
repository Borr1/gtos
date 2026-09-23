# S20 MULTI_STAGE residual — Dig E KILL on Challenge place

**Compose with:** S16 Dig/Chair harness (off Challenge place scoreboard).  
**Not** a second Dig E APPLY. Residual cleanup only.  
**Login:** `0`. **pack1b_beaten:** false. **No NEWS invent.**

## What it does

Dig E KILL for the Challenge writer path:

- `CHALLENGE_PLACE_PATH_DUAL_FLAG = False`
- `dig_guard_on_challenge_place()` always returns False
- `book_owner` / `book_owner_observe_splice` never mention `DIG_MULTI_STAGE_GUARD` and never import s16
- `maybe_write_shadow_row` is observe-only: APPLY + forbidden tool **returns None** (does not raise). Place is not blocked.

`s16_apply_enabled` is unchanged. `assess_action` / `refuse_broker_action` still VETO place. `test_apply_still_never_place` still holds.

## Laws

- Dual-flag never sits on Challenge place.
- Observe-only harness must not block place.
- Off Challenge place scoreboard.
- Never invent `NEWS_PROTOCOL`.

## Prove

```bash
python3 -m pytest -q tests/judgment/test_s16_multi_stage_guard.py tests/judgment/test_book_owner_observe_splice.py
```
