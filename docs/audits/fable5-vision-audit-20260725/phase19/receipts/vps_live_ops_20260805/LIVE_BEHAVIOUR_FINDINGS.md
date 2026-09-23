# Live-behaviour findings — what the book would do to an owner-set stop

Session LM, 2026-08-05. All line numbers are the **live host's**
`C:\Users\MSI\Documents\ai-trading-agent\src\components\execution.py` (10,199 lines), read directly.
**Nothing here was changed.** Each is an execution-behaviour change on armed money and belongs to
Borhen.

Context: on 2026-08-04 Borhen moved the stop on a live FTMO `energy_agri` position from 89.984 (the
book's) to 80.511 (his), locking ≈+0.40 R. The book never noticed. It also never fought him — but
only because the trade stayed below the trigger that would have made it act. These are the paths
that would have run if it hadn't.

---

## LB1 — the break-even move has **no** monotonicity guard, and would have given back the owner's locked profit

`_move_sl_to_breakeven` (`:9419`) is the path a `partial_be_runner` sleeve — which is what
`energy_agri` runs — takes when its trigger fires. Its whole body is:

```python
old_stop_loss = trade.stop_loss                      # :9442
for attempt in range(1, self.SL_MODIFY_MAX_ATTEMPTS + 1):
    success = self._modify_sl(ticket, trade.entry_price,   # :9444-9446
                              trade=trade, modify_reason="sl_to_breakeven")
```

**There is no worsening check of any kind.** It sets the broker stop to `trade.entry_price`,
unconditionally, on every call. Seven call sites reach it (`:3268, :7787, :7844, :7863, :7995,
:8929, :8934`).

Applied to the 2026-08-04 trade: entry 83.233, owner's stop 80.511 (+0.40 R locked). Had the trade
reached its **2.00 R software trigger** — the level the book logged at entry, *"broker TP set to
final 4.00R=56.23031; software trigger 2.00R"* — this would have issued
`_modify_sl(ticket, 83.233)` and moved a **+0.40 R protective stop back to 0 R**. The owner would
have watched his locked profit disappear and seen no explanation anywhere.

**The codebase already holds the principle it needs.** The docstring immediately above (`:9422-9440`)
is the BUG #28 fix, and its reasoning is exactly right: the old code *"threw away a fully-valid
existing SL (which is the safety floor)"* and that was *"directly responsible for the GBPJPY +0.74R
cap when the trade was on its way to a +6R target."* The lesson was learned for **broker-rejection**
failures. It was never extended to a stop that someone **improved**.

## LB2 — the guard that does exist reads the book's memory, not the broker

`_move_sl_to_dynamic_r` (`:7324`), the trailing/abort path, *does* ratchet:

```python
new_sl = self._trade_price_from_r(trade, target_r)
old_stop_loss = trade.stop_loss                                   # :7334
if old_stop_loss:
    would_worsen = ((trade.direction == "LONG"  and new_sl <= old_stop_loss)
                 or (trade.direction == "SHORT" and new_sl >= old_stop_loss))  # :7336-7340
    if would_worsen:
        return False                                              # :7342
```

`trade.stop_loss` is the book's **own in-memory record**, not the broker's live `position.sl`. For
this trade it was 89.984 all along. A break-even target of 83.233 against a remembered 89.984 gives
`83.233 >= 89.984 → False` on a SHORT, so the guard **passes** and the modify proceeds — even though
the *real* broker stop was 80.511 and the move is a 0.40 R regression.

The guard is not wrong; it is **pointed at the wrong source of truth.**

## LB3 — `trade.stop_loss` is never resynced from the broker on a normal position

Only two sites refresh it from the broker, and both are narrowly gated:

| site | condition | reachable here? |
|---|---|---|
| `_sync_recovered_partial_state_from_broker` `:3238-3245` (`trade.stop_loss = position.sl`) | called at `:3226` **only if** `recovered_partial` (`:3220-3223`) — adoption of a position whose partial was already taken | **no** |
| `_execute_tp1_partial` `:7691-7694` (`trade.stop_loss = broker_sl`) | **only if** `broker_volume < initial_volume` — a partial already reflected at the broker | **no** |

For a normal, un-partialled, book-owned position there is **no per-tick resync**. An external stop
change is therefore invisible to the book for the whole life of the trade.

## LB4 — the asymmetry that makes this look like an oversight rather than a policy

The two mirror functions treat the *other* leg's broker value in opposite ways:

| function | reads the broker for | preserves a manual… |
|---|---|---|
| `_modify_sl` `:9573-9585` | `current_tp = p.tp` (`:9579`) → sends `{"sl": new_sl, "tp": current_tp}` | **TP: yes. SL: no — it overwrites it.** |
| `_modify_tp` `:9815-9826` | `current_sl = p.sl` (`:9821`) → sends `{"sl": current_sl, "tp": new_tp}` | **SL: yes.** |

So a manual **take-profit** edit survives a book stop-move, and a manual **stop** edit does not
survive a book TP-move… but is destroyed by a book stop-move. The SL path is the only one of the four
combinations that discards owner input, and it does so silently.

## LB5 — what did work, and should be said plainly

Two guards behaved correctly on this trade and are worth keeping in mind before changing anything:

- **The close-classification guard.** At 2026-08-04 21:01:32 the terminal's link to FTMO-Server3
  dropped; `positions_get` returned empty **while the position was still open**. The book logged
  `Position 172916305 absent from positions_get but MT5 close deal confirmation status is
  HISTORY_UNAVAILABLE; deferring broker_closed for vNext` and refused to record a close it could not
  confirm. The terminal resynced at 21:02:08 reporting **1 position**. **The book did not fabricate a
  close from an absence** — that is the guard doing exactly its job, seven hours before the real
  close.
- **Server-side protection survives everything.** SL and TP are both set in the entry request
  (`execution.py:3488`; visible in the MT5 journal as `market sell 1.91 UKOIL.cash sl: 89.984
  tp: 56.230`), so the position was never dependent on the book being alive.

---

## LB6 — the learning lane cannot distinguish a human exit from a book exit

Detailed in `TRADE_FORENSIC_20260804_UKOIL.md` §6. In short: every field describing this exit says
`broker_closed`, and `deal.reason == 4 (DEAL_REASON_SL)` is identically true whether the stop that
fired was the book's or a human's. The book **knows both numbers** — the stop it set (89.984, in
`trade.stop_loss`) and the stop that fired (80.511, in the closing order's `price_open` and its
`[sl 80.511]` comment) — and compares neither.

The consequence is already on disk: `edge_state.json` now reads
`energy_agri: {n: 1, wins: 1, sum_profit: 493.2}`, crediting a sleeve with an exit price a human
chose, and the advisory's 151-trade closed set feeds from the same stream.

**The minimal honest fix is additive and changes no execution behaviour**: at close-classification,
record the broker's stop at exit alongside the book's last-known stop, and stamp a flag when they
differ beyond tick tolerance (`exit_stop_matches_book_intent: false`). That is a *labelling* change,
not a *behaviour* change, and it would let every downstream consumer choose whether to count the
trade. Filed, not implemented — it is a code change to the live lineage.

---

## Suggested order if Borhen wants these addressed

1. **LB6 (labelling)** — additive, no execution change, protects the forward record. Cheapest and
   most valuable.
2. **LB1/LB2 (respect an improved stop)** — one comparison against the broker's live `p.sl` before
   any book-initiated SL move, refusing the move when it would worsen the *actual* protection. Small,
   but it is a live execution-behaviour change and needs a ceremony and a decision about the
   intended contract: *does the book yield to a human stop, or own the stop absolutely?* Both are
   defensible; only one is currently implemented, and it was never chosen deliberately.
3. **LB3** — falls out of (2) if the comparison reads the broker rather than resyncing state.
