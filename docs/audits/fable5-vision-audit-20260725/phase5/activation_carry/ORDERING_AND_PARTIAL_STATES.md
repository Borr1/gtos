# Ordering, and what the host looks like if the operator stops halfway

**Session AC. Read this before `ACTIVATION_CARRY_VPS_RUNBOOK.md`; the runbook implements it.**

Three changes, one restart, a live funded FTMO account. The question the runbook has to answer
is not "what order is tidiest" but **"if the operator stops at step N, what is running?"**

Everything below is measured on a reconstruction of the host's own tree
(`redacted_host`, verified byte-identical to the three files fetched from the running host on
2026-07-29). Receipt: `receipts/PARTIAL_STATES.json`, regenerate with
`receipts/enumerate_partial_states.py`.

---

## 1. What is being copied

| stage | file | on host | why it is in this carry |
|---|---|---|---|
| **A1** | `src\utils\broker_clock.py` | **absent** | new; the measured server + reset calendars. Shared with Session S's packet carry — **byte-identical, install once.** |
| **A2** | `src\components\ultimate_book\governor_state.py` | modified | B56: resolve the reset window by the **firm's** rule, not the server's. |
| **A3** | `src\components\ultimate_book\book_engine.py` | modified | B56: pass the account's rule to the governor. **One hunk.** |
| **B** | `src\components\execution.py` | modified | the strand: `0.03` lots normalized to `0.02` and no close could be issued. |
| **C** | Session S's five packet-carry files | mixed | `phase4/packet_carry/`, `book_owner.py` last. Not re-authored here. |
| **D** | `.tools\monitor_books.py` | modified | the same B56 defect in the alerting layer, plus a hardcode that breaks 2026-11-01. |

---

## 2. The three invariants, and they are the only three

Measured by materialising every one of the 64 subsets of {A1, A2, A3, B, D} × {S applied, S not
applied} and running what `run_book.py` runs, plus the monitor daemon's own module load:

1. `run_book.py:32` — `from …book_owner import UltimateBookOwner`, module top, unguarded.
2. `run_book.py:294` — `UltimateBookOwner(merged, mt5, ".", …)`, also outside any `try`.
3. the monitor daemon's own module load, which is on no book's import graph at all.

> **`A2` present without `A1`** → `ModuleNotFoundError: No module named 'src.utils.broker_clock'`
> at **module load**. `governor_state.py` imports it at module top, unguarded.
>
> **`A3` present without `A2`** → `TypeError: GovernorStateBuilder.__init__() got an unexpected
> keyword argument 'reset_rule'` at **startup**, inside `UltimateBookLiveEngine.__init__`.
>
> **`D` present without `A1`** → `ModuleNotFoundError` at **module load of the monitor daemon**.
> The carried `.tools/monitor_books.py` does `sys.path.insert(0, REPO_ROOT)` and then imports
> `src.utils.broker_clock` at module top, unguarded. The monitor is supervisor-restarted, so this
> is a permanent crash loop of the **alerting layer** — the thing watching the daily-loss rule of
> the account being armed.

> ### The third invariant was found by a refuter, and the state space was blind to it
>
> The first version of this document said "two invariants, and they are the only two" — and the
> enumeration could not have found a third, because stage D was not in the state space at all.
> Adding it takes the grid from 32 states to 64 and the fatal count from 16 to 36. A claim of
> completeness is only as wide as the space it was measured over, and mine was narrower than the
> claim.

**36 of the 64 states die before the first tick.** Every one of them violates at least one of those
three rules, and no state violating none of them fails. Stage **B** appears on both sides of the
line and never causes a failure by itself — it adds a module constant and edits one method body.

> ### Probing the import graph alone would have found half of this
>
> An import-only probe — which is what Session S's carry used, correctly, for a carry whose
> only failure mode *was* the import graph — found **8** of the original 32 states fatal. Carrying
> on to the first construction found **16**. The extra eight are `book_engine.py` without
> `governor_state.py`: they import perfectly and then die on a keyword argument. (Both figures are
> over the 32-state, books-only grid; adding stage D takes it to 64 and 36.)
>
> S's published lesson was "I traced the call-site consequence and never asked whether control
> reaches the call site." The inverse is just as cheap to make, and I nearly shipped it.

**Session S's carry changes no verdict**, in either direction, in any of the 32 pairs. The two
carries compose.

> ### And "it starts" is still not "it is safe" — the whole-file space is not the whole space
>
> A refuter truncated the carried files at block boundaries instead of omitting them, and found
> **39 measured states that pass the import + construct probe and are unsafe**, in three distinct
> silent ways: a truncated `governor_state.py` where `compute_governor_state()` returns `None` and
> the **breach flatten silently never fires**; a truncated `book_engine.py` where every tick
> returns `action:"error"` **and the supervisor never restarts it**, because the process is up; and
> a truncated `execution.py` invisible to import, construct and tick while `ExecutionEngine`
> carries as few as 1 of its 143 methods.
>
> **Every one of them fails `--check postflight`**, because the sha comparison sees bytes and the
> probe sees behaviour. So the composite gate is sound — but the claim "`--check imports` is the
> reason §7 is safe" was too strong, and the runbook now says `imports` is necessary and not
> sufficient. `postflight` additionally tests `broker_clock.py` by **sha** rather than by
> existence, which is how a truncated copy used to read as `ok`.

---

## 3. The one place the two carries genuinely interact

`src\utils\broker_clock.py` is in **both**. Byte-identical
(`78549c4d2b17b3d0078f918459c706b79de2eb8324cb92a2945725d6a1c2af8a`), so copying it twice is
harmless — but its **status changes**, and S's ordering table becomes wrong once this carry
lands:

> S's table, row 3: *"`broker_clock.py` missing, last, never, **or truncated** → nothing — the
> import is guarded and now catches any exception, not just `ImportError`."*

That is exactly right for the packet carry: `packet_economics.py:50-51` imports it inside a
`try`. **After stage A2 it is false.** `governor_state.py` imports it at module top with no
guard, so a missing, truncated or half-written `broker_clock.py` is a module-load death for
both books.

**That is deliberate and it should not be "fixed" by adding a guard.** A guarded import would
fall back to the detected server offset — which is precisely the early-reset behaviour B56
exists to remove — and it would do it silently, on a funded account, with nothing watching.
Fail closed and loudly beats fail open and quiet. The cost is paid by ordering (`A1` first) and
by `verify_carry.py --check postflight`, which asserts the invariant directly.

---

## 4. What a module-load death actually costs

The supervisor's own code, read from the host's copy
(`scripts\run_book_supervisor.ps1`, 18,991 bytes — **not** the 6,980-byte one vendored into
mainline; the two have forked):

* `Test-BookRunning` returns `$false` **only** when zero `run_book.py --namespace <ns>`
  processes exist (`:175-180`). Every other branch returns `$true`, including the stale-
  heartbeat branch, which logs `alert_only_no_forced_restart open_position_safety` (`:209`).
  **The supervisor never stops a book.** Confirmed for the version actually running.
* A book that dies at load leaves zero processes, so it is restarted on the **next supervisor
  loop: ~30 s + 3 s**, not the 5 minutes stated in my prompt. The 5 minutes is the scheduled
  task's re-fire interval, which only matters if the supervisor itself is gone.

So a bad partial copy is a **~33-second crash loop on both namespaces**, during which
`manage_open_positions` never runs: no break-even move, no trailing, no time stop, no partial,
no `_apply_breach_flatten`.

**It is not, however, an unprotected position.** Measured on the host's own order history
(`vps-export-20260725/extracted/09_mt5_api/*_history_orders_get.jsonl`): of **175** W7-tagged
orders with volume, **175 carry a non-zero broker-side `sl`** — 97/97 FTMO, 78/78 redacted_account.
Take-profit is attached on 127 of 175. The book sends `sl` and `tp` with the entry itself
(host `execution.py:3674-3675`), so the stop lives on the broker's server and survives any
number of restarts. What a crash loop costs is **exit management and the breach flatten**, not
the stop.

That is still bad enough to order around. It is not "unmanaged and naked", and saying so
precisely is what lets an operator decide calmly at 2 a.m.

---

## 5. The order, and where it is safe to stop

**Every prefix of this list is a safe state.** That is the property the order is chosen for.

| # | action | safe to stop after? | state if you do |
|---|---|---|---|
| 0 | back up the six destination paths | **yes** | nothing changed |
| 1 | `--check preflight` | **yes** | nothing changed |
| 2 | **pause new entries**: create both kill flags | **yes** | books keep running and keep managing exits; no new units. See §6. |
| 3 | copy **A1** `broker_clock.py` | **yes** | nothing imports it yet; inert |
| 4 | copy **A2** `governor_state.py` | **yes** | needs A1, which is there. Old `book_engine` never passes `reset_rule`, so behaviour is unchanged until A3. |
| 5 | copy **A3** `book_engine.py` | **yes** | B56 complete |
| 6 | copy **B** `execution.py` | **yes** | strand fix complete |
| 7 | copy **C** Session S's five, `book_owner.py` **last** | **yes** | packet emitter unblocked |
| 8 | `--check postflight`, `--check imports`, `--check behaviour` | **yes** | still old code in memory; new code on disk and proven loadable |
| 9 | stop both books; supervisor restarts them on new code | **yes** | the restart |
| 10 | `--check behaviour` again; confirm both books healthy | **yes** | done for the books |
| 11 | remove both kill flags | **yes** | placement resumes |
| 12 | copy **D** `monitor_books.py` (runbook §10) | **yes** | needs A1, which landed at step 3 |
| 13 | `--check stage-d`, then stop the monitor | **yes** | supervisor restarts it within ~40 s |

**Unsafe states, all of them reachable only by departing from that order:**

* stopping between "copy A2" and "copy A1" — i.e. copying A2 first. Do not reorder stage A.
* stopping between "copy A3" and "copy A2" — same.
* copying **D** before **A1**, which is why stage D is step 12 and not step 1 even though it is
  independent of the books.
* **stopping between step 9 and step 10** is not a state you can choose; it is where the books
  are already down. If `--check imports` at step 8 passed, this window is a restart, not a
  loop. If you skipped step 8, this is where you find out.
* copying `book_owner.py` before the other four of stage C — S's carry documents this and
  `verify_carry.py --check imports` catches it.

**The one-way door is step 9**, and everything before it exists to make step 9 boring.

---

## 6. Why the kill flag is the brake and `Stop-Process` is not

`launcher.py:204-211` (host copy): `tick()` computes `place = not (killed or halted)`.
The kill flag **pauses placement**; it does not stop the process and it does not stop exit
management. The supervisor therefore does not restart anything, because nothing is missing.

So the correct sequence is *pause with the flag, then stop the process for the code swap, then
unpause* — and if anything goes wrong at any point, **re-creating the kill flag is a brake that
costs nothing and orphans nothing.**

`Stop-Process` is the code-swap mechanism, not the brake. It is used exactly once, at step 9.

---

## 7. Rollback

Rollback restores every path from the backup taken at step 0 and deletes the ones the backup
records as having been **absent**. That last clause is load-bearing: a hardcoded "these were new"
list is indistinguishable from "the backup could not be read", and a refuter showed that with an
unusable `$backup` the first draft deleted `broker_clock.py` while leaving `governor_state.py`
carried — manufacturing the exact fatal state §2 exists to prevent. Runbook §3 therefore writes a
`BACKUP_MANIFEST.json` of what it actually captured, and §9 refuses to do anything without it.

Order does not matter on the way back **provided the books AND the monitor are stopped first**.
The monitor is not a book: deleting `broker_clock.py` under a running monitor leaves it
crash-looping, and the supervisor restarts it into the same failure.

**And the base to judge against is the host's, not the lineage's.** A host that already has
Session S's packet carry applied is not on `redacted_host`. Judging a rollback against the lineage
there fails a *correct* rollback — which is Session S's own defect, reproduced inside the carry
written to eliminate it, and found by a refuter rather than by me.

`verify_carry.py --check rollback` is a **separate gate from `postflight`** and asserts the
opposite state: every modified file back at its lineage sha, every new file gone, and the tree
still imports and constructs.

> Session S found this defect in its own carry and it is worth restating, because it is the
> one that reads as a green light for the wrong action: a carry whose only gate demands the
> **carried** shas tells an operator who has just rolled back correctly that the tree is
> broken and not to restart. On a live account, at 2 a.m., that is the worst possible advice.
> Tested here in both directions — `--check rollback` exits 0 on a correctly reverted tree and
> 2 on a carried one, and `--check postflight` does the reverse.
