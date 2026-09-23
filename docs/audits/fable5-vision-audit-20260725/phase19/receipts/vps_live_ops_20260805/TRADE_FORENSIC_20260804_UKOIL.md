# Forensic — the owner-intervened trade, FTMO `energy_agri` / UKOIL.cash

Session LM, 2026-08-05. All reads over host-admin as `trader` on `redacted_host`. **No broker-mutating
call was made.** Live root **`C:\Users\MSI\Documents\ai-trading-agent`** (derived from the running
process command line — `C:\GTOS` is a *different* tree with no `run_book.py`, no
`scripts\run_book_supervisor.ps1` and no `pipeline_state\ultimate_book`; editing there is a silent
no-op).

Primary receipt of the broker facts: `MT5_PROBE_20260805T1341Z.json` (read-only
`positions_get` / `history_deals_get` / `history_orders_get`, probe at 2026-08-05T13:41:55Z).

## 1. What fired

| field | value | source |
|---|---|---|
| account | **FTMO** login `531325516` (sha8 `310fcf06`) | probe `accounts.FTMO.account` |
| sleeve | `energy_agri` (cluster `energy`) | `placed_decisions.jsonl` last row |
| candidate | `W7_BOOK::energy::UKOIL_cash::2026-08-04::SHORT::energy_agri` | ibid. |
| decision bar | **2026-08-04T09:00:00Z** (H4), decision_day **2026-08-04** | ibid. |
| placed (book clock) | 2026-08-04T13:00:13.970243Z | ibid. |
| filled (broker) | **2026-08-04T13:00:28Z**, deal `162262885`, order/position `172916305` | probe, terminal journal |
| side / size | **SHORT 1.91 lots** UKOIL.cash @ **83.233** | probe |
| magic / comment | `20260401` / `W7:energy_agri` | probe |
| deal `reason` | **3 = DEAL_REASON_EXPERT** — API/book origin, confirmed | probe |
| SL / TP at entry | **SL 89.984**, **TP 56.230** (both server-side at entry) | probe `history_orders_7d`, journal |
| risk | logged `runtime-adjusted risk 1.20% (default 0.50%)` | `run_book_console.log` 13:00:27 |

**Arithmetic cross-check (independent):** stop distance 6.751 × 1.91 lots × 100 /pt = **$1,289.44**;
1.20 % of the 107,872.28 balance = $1,294.47. The sizing log, the stop and the account agree — the
position was sized exactly as declared.

## 2. What the book intended

`run_book_console.log`, 2026-08-04 13:00:27,633:

```
GTOS vNext partial_be_runner live management: broker TP set to final 4.00R=56.23031; software trigger 2.00R
```

So the intended contract was: server-side TP at **4R**, and a **software** trigger at **2.00R** for
the `partial_be_runner` scale-out + break-even move. The initial protective stop (89.984) was to
stand until that 2R trigger.

## 3. What actually happened at the exit

| field | value |
|---|---|
| closing deal | `162470299`, order `173141626`, **2026-08-05T04:56:43Z** |
| price | **80.547** (BUY to close the short) |
| deal `reason` | **4 = DEAL_REASON_SL** — a *server-side stop* fired |
| close order `price_open` / comment | **80.511** / `[sl 80.511]` |
| gross profit / swap / commission | **+513.03** / **−19.83** / **0.00** |
| **net** | **+493.20** |
| hold | 957.2 min (≈15.95 h) |

**The stop that fired was at 80.511. The stop the book set was at 89.984.** Someone moved it
**9.47 price units**, from 6.75 *above* entry to 2.72 *below* entry — converting an open-risk trade
into a locked-profit trade.

Realised **0.398 R**. Peak floating (from `high_water.json` 108,522.10 vs 107,872.28 balance) was
**+649.82 = 0.504 R**. **The trade never came close to the 2.00 R software trigger**, so the book had
no policy reason to touch the stop — and did not.

## 4. Attribution — who moved the stop [MEASURED, two independent lines]

**(a) The VPS terminal never issued a modify.** MT5 logs every trade request sent *through* a
terminal in that terminal's Journal. `C:\MT5\FTMO\logs\20260804.log` contains exactly five `Trades`
lines — all five are the entry (request → accepted → placed → deal → order done). `20260805.log`
contains exactly one — the closing deal *notification*. Across the last ten days of FTMO journals
there is **no `modify` line and no `sl:` line other than the three entry-request lines**. The book
acts only through this terminal, so the book did not move the stop.

**(b) An external device was logged into the FTMO account, and only the FTMO account.** MT5 reports
the previous successful authorization for the account on each reconnect:

| day | FTMO journal auth IPs | redacted_account journal auth IPs |
|---|---|---|
| 07-27, 07-28 | `0.0.0.0` | `0.0.0.0` |
| 07-29 | `0.0.0.0`, **`0.0.0.0`** | — |
| 07-30 | `0.0.0.0`, **`0.0.0.0`, `0.0.0.0`** | `0.0.0.0` |
| 07-31 | `0.0.0.0`, **`0.0.0.0`, `0.0.0.0`** | `0.0.0.0` |
| 08-01 | `0.0.0.0` | `0.0.0.0` |
| **08-02 → 08-05** | **`0.0.0.0` only** | `0.0.0.0` only |

`0.0.0.0` is the VPS's own public IP — it is the *sole* IP on the redacted_account terminal every
single day, and the redacted_account terminal is never touched by a human. **Two terminals on one host
cannot have two different public IPs**, so from 2026-08-02 onward the FTMO account has been
authorized from an external device (`0.0.0.0`), and that device's authorizations are the ones
the VPS terminal reports as "previous" — including one at 2026-08-04 22:29:55 server time
(= 19:29:55 UTC), i.e. **during the life of this position**.

**Conclusion: Borhen moved the stop himself, from his own device, from 89.984 to 80.511, locking
≈$520 gross. The stop then filled at 80.547 for +493.20 net. The book neither placed nor requested
that exit.** This matches his own account of intervening with his own judgment.

*(Incidental, same evidence: two 0.01-lot XAUUSD deals on 2026-07-29 00:47/01:02 appear in the FTMO
journal with no `W7:` comment — a manual 0.01 test round-trip, not a book trade. Noted, not an
issue.)*

## 5. Did the book notice? Is its state coherent?

**Yes on both counts — and one guard worked exactly as designed.**

```
2026-08-04 21:01:32,008 WARNING Position 172916305 absent from positions_get but MT5 close deal
    confirmation status is HISTORY_UNAVAILABLE; deferring broker_closed for vNext
2026-08-05 04:57:26,259 INFO  Position 172916305 no longer exists -- closed by broker
```

At 21:01:06 the terminal lost its link to FTMO-Server3 (journal). `positions_get` therefore returned
empty **while the position was still open**. The book refused to declare it closed because the deal
history was unavailable — **it did not fabricate a close from an absence**. The real close was
detected at 04:57:26, **43 s** after the broker fill.

State coherence, checked against the broker:

| check | result |
|---|---|
| open positions FTMO / FN | **0 / 0** (probe) |
| FTMO equity vs balance | 108,365.48 = 108,365.48, floating 0.00 |
| balance movement | 107,872.28 + 493.20 = **108,365.48** ✔ |
| `edge_state.json` | `energy_agri: n=1, wins=1, sum_profit=493.2`; deal `162470299` in `seen_tickets` ✔ |
| `daily_pnl.json` | reconciled, `broker_deal_reconciled: true`, net 493.2 ✔ |
| orphaned managed state | **none** — no residual position record; `placed_decisions.jsonl` closed out |
| reconciliation population | `broker_closed` (not `broker_closed_absent_on_reconcile`, not `vnext_time_stop`) |

**There is no orphaned state and no book/broker divergence.** Nothing needed repair.

## 6. Did the learning lane record it honestly? — **PARTLY. This is the real finding.**

`shadow_logs/daily_pnl.json` (2026-08-05):

```json
"exit_type": "broker_closed",
"result_r": 0.0,
"r_evidence_class": "LOCAL_NOTIFICATION_R_INPUT",
"actual_r_claim_allowed": false,
"dollar_evidence_class": "BROKER_DEAL_RECONCILED_PROFIT",
"actual_dollar_claim_allowed": true,
"account_truth_status": "BROKER_DEAL_RECONCILED_AT_NOTIFICATION_TIME",
"gtos_vnext_notification_context": { "close_action": "broker_closed",
  "exit_reconciliation_status": "RECONCILED_FROM_ACCOUNT_HISTORY" }
```

**What is honest:** the dollar figure is broker-reconciled from account history, not projected; the
system **refuses to claim an R** for this trade (`actual_r_claim_allowed: false`, `result_r 0.0`);
swap and commission are captured from the deal. The evidence-class discipline is doing its job.

**What is NOT captured — and it matters:** every field describing the exit says only
`broker_closed`. There is **no field anywhere in the record that distinguishes**

- a stop **the book set** firing, from
- a stop **a human moved** firing.

`deal.reason == 4 (DEAL_REASON_SL)` is true of both. The book knows the stop it set (89.984) and it
can see the stop that fired (80.511, in the close order's `price_open` and comment) — **it captures
neither for comparison.** Consequently:

- `edge_state.json` now carries `energy_agri: n=1, wins=1, sum_profit=+493.2` — an **owner-chosen
  exit price credited to the sleeve** as if it were the sleeve's own performance.
- The runtime-learning advisory (`RUNTIME_LEARNING_DAILY_ADVISORY.json`, 151 deduped closed trades)
  and the learning lane consume that same stream.

**This contaminates the forward record.** It is one trade of 151 and the direction of the bias is
knowable (the manual exit at 0.40 R replaced an unknown outcome of a contract that ran to a 2 R
trigger and a 4 R target), but the *mechanism* is general: **any manual intervention on a live
position is currently indistinguishable, downstream, from book-generated evidence.** Since the
declared purpose of the mx/forward programme is an honest forward record, this is a defect worth
fixing at the source rather than annotating after the fact.

**Not fixed in-session.** The fix touches `src/components/execution.py`'s close-classification path
on a live, token-digest-bound, armed book; it is a code change to the live lineage and belongs in a
carried ceremony, not an ad-hoc edit. Proposal is in the result doc.

## 7. Would the book have *fought* the manual stop?

**Not on this trade — but only because the trade stayed small.** The `partial_be_runner` policy's
scale-out + break-even move is gated on a **2.00 R software trigger** (console line above); peak
floating was **0.504 R**, so the trigger never armed and the book issued no modify (confirmed by the
empty journal).

Had the trade reached 2 R, the book would have executed its own exit-management step against a
position whose stop the owner had already moved. The book reads the *position*, not the *delta from
its own last request — it has no record that an external actor moved the stop, and no
"external-modification detected" branch. The book's break-even level is the entry price (83.233);
Borhen's stop was **better than break-even** (80.511, +0.40 R locked). A book-issued break-even move
would therefore have moved the protective stop **backwards**, from +0.40 R locked to 0 R.

**Live-behaviour finding, filed not patched:** *on a manually-improved stop, the book's own
break-even step is a regression, not a protection.* Exact locus given in the result doc. It costs
nothing today (both accounts flat, no position open) and changing it is an execution-behaviour
change on armed money — owner's call.

## 8. Timeline

| UTC | event | source |
|---|---|---|
| 2026-08-04 09:00 | decision bar (H4) | `placed_decisions.jsonl` |
| 13:00:13 | book decides, places | ibid. |
| 13:00:27 | `partial_be_runner`: broker TP 4R = 56.230, software trigger 2R; risk 1.20 % | console |
| 13:00:28 | filled SHORT 1.91 @ 83.233, SL 89.984 TP 56.230 | journal, probe |
| ~19:29:55 | external device (`0.0.0.0`) authorized on the FTMO account | journal (prev-auth) |
| (unlogged on host) | **stop moved 89.984 → 80.511** — no VPS-terminal request exists | journal absence |
| 21:01:06 | terminal↔FTMO-Server3 link lost | journal |
| 21:01:32 | book sees position absent, **defers** `broker_closed` (history unavailable) | console |
| 21:02:08 | reconnect; terminal syncs **1 position** — position was still open ✔ | journal |
| 2026-08-05 04:56:43 | stop at 80.511 fills at **80.547**; +513.03 / −19.83 swap | probe, journal |
| 04:57:26 | book detects close, reconciles from account history, writes `daily_pnl` | console |
| 13:41:55 | probe: both accounts flat, FTMO 108,365.48 | probe |
