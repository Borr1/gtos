# HOST LEARN_LOOP_V0 LAND

**Tree:** VPS `redacted_host/repo` dirty f5-live (`redacted_host`)  
**Account:** Challenge `0` / ns `operator` only  
**This seat:** shadow / prove. **Jev never places.** Do not remint. Do not flatten.

Chair named this wave: XAU `293611741` `orig_stop` −1.03R `event_gap`; GBPJPY `293540988` `orig_tp` +2.96R `ok_win`.  
Close contract: `gtos.close_loop.v1` (locked; `orig_tp` first-class). LEARN_LOOP_V0 binds it. `prove_next` is LABEL / prove — not APPLY.

---

## Needed? Yes — after close, not after admit

GitHub already scores Challenge deals in `score_deals` / `learn_from_close`. The host is where **new** closes land (`just_closed_siblings.json` `closed[]` and deal history). Without a host splice the loop only sees fixtures + the 2026-09-17 deal drop.

The splice is an **observer**. It must not change a fire, a size, or a flatten.

---

## What Chair copies

1. GitHub files (do **not** wholesale-copy `book_owner.py` — host is ~10069 lines):
   - `src/judgment/learn_loop.py`
   - `src/judgment/hold_from_tape.py` (`named_exit_class`)
   - `src/judgment/gold_state.py` (`assemble_symbol_state_v0` alias only)
2. Env on the Challenge book worker **only**:
   ```
   GTOS_JEV_LEARN_LOOP=1
   GTOS_JEV_LEARN_LOOP_PATH=host-local\redacted_host\repo\judgment\astra\lab\learn_loop_v0\store.jsonl
   GTOS_JEV_A1_CALL=0
   ```
   Absence of `GTOS_JEV_LEARN_LOOP` is off. W7 armed books stay off.
3. Hook **after** a close is written to live `closed[]`, not before place:

```
# After just_closed_siblings.json closed[] append (or deal-history close).
# Env-gate BEFORE import. Never refuse. Never resize. Never flatten.
if os.environ.get("GTOS_JEV_LEARN_LOOP", "").strip() in {"1", "true", "yes"}:
    from src.judgment.learn_loop import maybe_learn_from_close
    maybe_learn_from_close(closed_row, books=None, spines=None)
```

Find the host writer for  
`pipeline_state/ultimate_book/operator/judgment/state/just_closed_siblings.json`  
— that is the site. Do not hunt leftover-ship `judgment/live/just_closed_siblings.json`.

---

## Must not

- Place, remint, flatten, or write inbox from this hook
- Invent `NEWS_PROTOCOL` / HIGH rows
- Wear XAU M15 on GBPJPY / US30 / FX
- Feed `closed_doc_from_deals` into the envelope 2-stop **COUNT** (LABEL only)
- Touch login `0` or W7 `--tags`
- Set `GTOS_JEV_APPLY_LIVE` for this land — APPLY is not this wave
- Copy GitHub `book_owner.py` over the host file

---

## Prove the land

1. After the next Challenge close (any symbol), `store.jsonl` grows by one row.
2. Row has `never_place: true`, `apply: false`, `exit_class` in `{orig_stop, orig_tp, time_stop, breach_flatten, other}`.
3. Ticket `293540988` may appear geometry-thin — missing stays missing.
4. Ticket `293611741` should read `orig_stop` if the host deal history now has the close print; prefer the broker exit over the implied SL.
5. `verify` / sit still healthy. Positions unchanged.

---

## If host splice waits

GitHub harness still scores the fixture pack:

```
python3 scripts/jev_learn_loop.py
```

That is enough to keep the loop honest on the named tickets. Host land can follow without blocking the PR.

The n=48 batch (`CLOSE_LOOP_BATCH_V1.json`) is a Chair-sealed aggregate on `0`. Host `store.jsonl` still writes one row per close. Do not invent the other 46 tickets from this seat. Asset-class split prove is LABEL only — never APPLY from the observer.
