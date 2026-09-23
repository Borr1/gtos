# Ordering, and what the host looks like if the operator stops halfway

**Session AZ. Read `AZ_CARRY_ENUMERATION.md` first; `MX_ACTIVATION_CEREMONY.md` implements
this.**

Four files, one restart, two live funded accounts with four armed sleeves and open-position
risk on them. The question is not "what order is tidiest" but **"if the operator stops at step
N, what is running?"**

Everything below is **measured** on a reconstruction of the host's own tree — the lineage
`redacted_host` with the Session S and Session AC carries applied at their verified after-bytes.
Receipt: `receipts/AZ_CARRY_PROBE_V1.json`, regenerate with `receipts/az_carry_probe.py`.

---

## 1. The state space, and why it is bigger than the last one

All **2⁴ = 16** subsets of {`execution_packets`, `order_router`, `book_owner`, `run_book`},
each materialised as a real tree and probed with seven questions: does every `src.` import in
`run_book.py` resolve (module-top **and** deferred); does `UltimateBookOwner` construct; does
it construct with a selection; does a placement build; does the router's own placement path
build; does the adopt path rehydrate; does it rehydrate under a selection.

```
applied         imp       rb-imp    ctor      ctor+sel  route     adopt     PLACE    verdict
--------------------------------------------------------------------------------------------
(none=host)     ok        ok        ok        FAIL      ok        ok        ok       safe, activation unavailable
EP              ok        ok        ok        FAIL      ok        ok        ok       safe, activation unavailable
OR              ok        ok        ok        FAIL      FAIL      ok        FAIL     UNSAFE: silent placement outage
BO              ok        ok        FAIL      FAIL      ok        ok        ok       FATAL: startup death
RB              ok        FAIL      ok        FAIL      ok        ok        ok       FATAL: module-load death
EP+OR           ok        ok        ok        FAIL      ok        ok        ok       safe, activation unavailable
EP+BO           ok        ok        FAIL      FAIL      ok        ok        ok       FATAL: startup death
EP+RB           ok        ok        ok        FAIL      ok        ok        ok       safe, activation unavailable
OR+BO           ok        ok        ok        FAIL      FAIL      ok        FAIL     UNSAFE: silent placement outage
OR+RB           ok        FAIL      ok        FAIL      FAIL      ok        FAIL     FATAL: module-load death
BO+RB           ok        FAIL      FAIL      FAIL      ok        ok        ok       FATAL: module-load death
EP+OR+BO        ok        ok        ok        ok        ok        ok        ok       safe; machinery complete
EP+OR+RB        ok        ok        ok        FAIL      ok        ok        ok       safe, activation unavailable
EP+BO+RB        ok        ok        FAIL      FAIL      ok        ok        ok       FATAL: startup death
OR+BO+RB        ok        FAIL      ok        FAIL      FAIL      ok        FAIL     FATAL: module-load death
EP+OR+BO+RB     ok        ok        ok        ok        ok        ok        ok       safe + ACTIVATION AVAILABLE
```

**Nine of sixteen states are unsafe**, in three classes.

> ### A module-top import probe finds ZERO of the nine
>
> Session AC found that probing the import graph alone found *half* of its fatal states, and
> that carrying on to the first construction found the rest. Here the same probe finds **none**
> — the column `imp` is `ok` in all sixteen rows. Every one of this carry's failures is a
> **signature mismatch** rather than a missing module:
>
> * **`run_book` without `execution_packets`** → `ImportError: cannot import name
>   'parse_frontier_exits'` at **module load of `main()`**, *unconditionally* — whether or not
>   `--frontier-exits` is on the command line. **4 states.** This is why `--check imports`
>   derives its import list from the **host's own `run_book.py` by AST**, deferred imports
>   included, instead of from a list; the first draft of the probe used module-top imports only
>   and reported every state safe.
> * **`book_owner` without `order_router`** → `TypeError: UltimateBookOrderRouter.__init__()
>   got an unexpected keyword argument 'frontier_exits'` **at STARTUP**, both namespaces.
>   **3 states.** Survives import; dies at construction.
> * **`order_router` without `execution_packets`** → **a SILENT TOTAL PLACEMENT OUTAGE.**
>   **2 states.** Survives import *and* construction. See the box below.

> ### The third class is not a crash, and getting that wrong overstates it in the wrong direction
>
> My first draft called this one "FATAL at PLACEMENT". It is worse than that word and less than
> it. `UltimateBookOrderRouter.place` wraps its whole body in `except Exception` — the comment
> says *"the book NEVER breaks the live path"* — so the `TypeError` never escapes. **Measured**
> by driving the real `place()` with a stub engine on each materialised tree:
>
> ```
> (none=host)  -> placed: True,  reason: "ok"
> OR           -> placed: False, reason: "router_exception:TypeError(build_book_trade_params()
>                                          got an unexpected keyword argument 'frontier_exits')"
> EP+OR        -> placed: True,  reason: "ok"
> ```
>
> So the process stays up, the heartbeat stays healthy, **exit management keeps running**, and
> every single unit refuses to place with a reason string, forever. It is recoverable and it
> loses no open position — and it is the state most likely to go unnoticed, because everything
> an operator normally looks at reads green. `--check deps` names it explicitly for that
> reason.

---

## 2. The invariants — three inside the carry, and a fourth outside it

Measured, not argued. `verify_carry.py --check deps` asserts each one **on the bytes**, before
anything is imported, because two of the three are invisible to `--check imports`:

1. `order_router.py` present ⟹ `execution_packets.py` present.
2. `book_owner.py` present ⟹ `order_router.py` present.
3. `run_book.py` present ⟹ `execution_packets.py` **and** `book_owner.py` present.

Over the 16-state grid: no state violating none of them fails, and every state violating one
does.

> ### And a fourth, which the grid could not have found because it is outside the grid
>
> The state space above is the four FILES. But the activation also edits
> `scripts\run_book_supervisor.ps1`, and **`--frontier-exits` on the supervisor line with an
> uncarried `run_book.py` is `argparse` exiting on an unrecognised argument** — at every
> respawn of every namespace, forever. That is the most expensive state in this document, it
> is reachable by doing step 8 before step 6, and it is reachable *again* on the way out by
> rolling `run_book.py` back before the supervisor line (§7).
>
> 4. `run_book_supervisor.ps1` contains `--frontier-exits` ⟹ `run_book.py` is carried.
>
> `--check deps` reads the `.ps1` and asserts it in both directions, and when it is satisfied
> it says which of the two legitimate states the host is in — carried-and-armed, or
> carried-and-not-armed. The lesson is Session AC's own, one register out: **a completeness
> claim is only as wide as the space it was measured over**, and a four-file grid cannot see a
> fifth file.

**The adopt path never fails in any of the sixteen** — the `adopt` column is `ok` throughout.
That is not luck: the host's `execution.py` already handles the `time_stop` rehydration
(`AZ_CARRY_ENUMERATION.md` §3), and it is why this carry has four files instead of five.

---

## 3. The order, and where it is safe to stop

**Every prefix of this list is a safe state.** That is the property the order is chosen for.

| # | action | safe to stop after? | state if you do |
|---|---|---|---|
| 0 | back up the four destination paths + write `BACKUP_MANIFEST.json` | **yes** | nothing changed |
| 1 | `--check preflight` (this also NAMES the run_book payload) | **yes** | nothing changed |
| 2 | confirm both accounts FLAT, then create both kill flags | **yes** | books run and keep managing exits; no new units. §5 |
| 3 | copy **1** `execution_packets.py` | **yes** | superset API; every existing caller unchanged. The `mx_*` time stops become 7680 **on disk**; the running processes hold the old module in memory until step 7. Nothing armed moves either way. |
| 4 | copy **2** `order_router.py` | **yes** | the router accepts a selection nobody passes |
| 5 | copy **3** `book_owner.py` | **yes** | the owner accepts a selection nobody passes. **The machinery is complete here** and the launcher still has no flag — the last completely inert stop. |
| 6 | copy **4** `run_book.py` (the payload preflight named) | **yes** | the flag exists, defaults to none |
| 7 | `--check postflight`, `--check deps`, `--check imports`, `--check behaviour` | **yes** | old code in memory, new code on disk and proven loadable |
| 8 | edit `scripts\run_book_supervisor.ps1`: FTMO `--tags` + `--frontier-exits` | **yes** | nothing reads it until the task restarts |
| 9 | delete the FTMO namespace's `firing_sleeves.json` (§6) | **yes** | today's conviction union resets |
| 10 | restart the supervisor **task**; count book processes to zero, then back | *not a state you choose* | the restart |
| 11 | `--check behaviour`; confirm `tfs=[16388, 16408]` and the frontier banner in the log | **yes** | done |
| 12 | release both kill flags | **yes** | placement resumes, `mx_btcusd` live |

**Unsafe states, all reachable only by departing from that order:** copying `order_router`
before `execution_packets`; `book_owner` before `order_router`; `run_book` before either. Each
is one row of the grid in §1 and each is caught by `--check deps` **before** a restart.

**The one-way door is step 10**, and everything before it exists to make step 10 boring.

> ### Steps 8–12 are the ACTIVATION; steps 3–7 are only the carry
>
> This is the seam that matters. After step 7 the host can run the admission's contract and is
> not running it — every default is byte-identical to today, asserted by
> `--check behaviour` item 2 over all four armed sleeves. A ceremony that stops at step 7 has
> deployed nothing that trades differently. That separation is deliberate: it lets the code
> land, be verified and be lived with independently of the owner decision to arm.

---

## 4. What a module-load or startup death would cost, if one happened

The supervisor's own code (host copy, `scripts\run_book_supervisor.ps1`, 18,991 B — **not** the
6,980-byte one vendored into mainline; the two have forked): `Test-BookRunning` returns
`$false` **only** when zero `run_book.py --namespace <ns>` processes exist. Every other branch
returns `$true`, including the stale-heartbeat branch. **The supervisor never stops a book**; a
book that dies at load leaves zero processes and is restarted on the next loop, ~30 s + 3 s.

So a bad partial copy is a **~33-second crash loop on both namespaces**, during which
`manage_open_positions` never runs: no break-even move, no trail, no time stop, no partial, no
`_apply_breach_flatten`.

It is **not** an unprotected position: the book sends `sl` and `tp` with the entry itself, so
the stop lives on the broker's server and survives any number of restarts (Session AC measured
175/175 W7-tagged orders carrying a non-zero broker-side `sl`). What a crash loop costs is
**exit management and the breach flatten**, not the stop. That is bad enough to order around,
and saying it precisely is what lets an operator decide calmly at 2 a.m.

---

## 5. Why the kill flag is the brake and `Stop-Process` is not

`launcher.py:204-211` (host copy): `tick()` computes `place = not (killed or halted)`. The kill
flag **pauses placement**; it does not stop the process and it does not stop exit management,
so the supervisor restarts nothing, because nothing is missing.

Pause with the flag → stop the process for the code swap → unpause. If anything goes wrong at
any point, **re-creating the kill flag is a brake that costs nothing and orphans nothing.**

**Never reach for `live_broker_authority: false`** — H8: it returns before flattening, strands
open positions, and degrades routine exit management to observe-only.

---

## 6. The two live-behaviour hazards this ordering does not remove

**The conviction count (B365).** `RunningConvictionLedger` persists a per-`decision_day` union
of firing sleeves and `admission.py:1188` takes `na = max(na, override)` — monotone upward
within the day. Widening `--tags` from four sleeves to five can therefore raise the day's `na`
by one. Under the live half-Kelly bins `((1,1,0.748),(2,3,0.991),(4,99,1.241))` that crosses a
bin **only** when exactly three of the armed four have already fired today: `na` 3 → 4 moves
the multiplier **0.991 → 1.241, +25.2 % on every unit that day**. 4 → 5 does not move it at
all. Mitigation, and it is step 9: **delete that namespace's `firing_sleeves.json`** (backed
up first), or arm at a decision-day boundary. `_KEEP_DAYS = 2` plus today-only keys mean prior
days cannot contaminate a fresh day — the hazard is same-day only.

**The adopt-without-record rehydration.** `native_policy_instrumentation` is called with the
selection the process was launched under, and by definition there is no trade record to read
the placement's own contract off. So a `mx_btcusd` position opened at 2R and then adopted
*without a record* while the 5R selection is on would be rehydrated at 5R, and with
`live_broker_authority` true that MOVES its broker TP. `mx_btcusd` has never traded live, so
there is no such position today — which is exactly why the flip should happen now rather than
later. The general rule stands: **flip the selection at a flat book.**

---

## 7. Rollback

Rollback restores every path from the backup taken at step 0. All four destinations are
**modifications of existing files** — this carry creates no new file — so there is nothing to
delete and the "which were absent" clause that bit Session AC does not arise here.

`--check rollback` is a **separate gate from `postflight`** and asserts the opposite state:
every carried file back at the bytes the **`BACKUP_MANIFEST.json` recorded** (not the
lineage's — a host with two carries already applied is not on the lineage, which is Session S's
own defect and the one that reads as a green light for the wrong action), and then, always,
whether the tree still starts.

> **The first draft of `verify_carry.py` reproduced that defect through the behaviour half
> rather than the byte half**, and it was caught by running the gate on a correctly reverted
> tree rather than by reading it. `--check rollback` called `check_imports`, which demanded
> that the frontier selection construct — which, after a correct rollback, it cannot. A
> correct rollback FAILED, telling an operator at 2 a.m. that the tree was broken. Now the
> rollback path asserts the opposite: the book must start with **no** selection, and the
> frontier selection failing to construct is reported as *"which is what a completed rollback
> MEANS"*. Tested in both directions — `--check rollback` exits 0 on a reverted tree and 2 on a
> carried one, and `--check postflight` does the reverse.

**Rolling back the CODE does not roll back the ACTIVATION**, and the order matters: revert
`scripts\run_book_supervisor.ps1` **first** (drop `--frontier-exits` and the fifth tag), then
the four files. A host with the old `run_book.py` and a supervisor line still carrying
`--frontier-exits` is `error: unrecognized arguments` on every respawn — a permanent crash loop
of both books.
