# VPS ceremony package 2 — one restart, four carries, and three questions that are not carries

**Session AI, wave 8, 2026-07-30.** Owner-executed. **Nothing in this package was run by a
session and nothing in it touches the VPS from this machine.**

This is a *consolidation*, not new engineering. Waves 5–7 produced VPS-side findings that have
been sitting in four different result documents with four different runbooks, and the standing
instruction has been to batch them into one restart rather than improvise at the console. Every
carry below already has its own tested artifact; what did not exist until now is one document
that says what goes, in what order, why each item is safe, and what to do when one of them
fails.

**FTMO is trading real money.** Balance $107,872.28, phase 1, target $110,000, static floor
$90,000, armed on three sleeves via `run_book.py --tags`, activation token valid to
**2026-08-05** binding config digest `ffe16657feaf`. Two rules govern everything here:

1. **Not one byte of `config/agent_config.yaml` changes.** The token hashes base-config +
   profile bytes; one byte and the armed book stops placing. Every item below is a source
   file, a launcher argument, or a read-only script — `config_digest_for` hashes none of those,
   so a supervisor edit is free.
2. **To disarm with positions open, flatten FIRST.** `live_broker_authority: false` returns
   before flattening (`book_owner.py:2364-2373`) and strands them — and the fourth row of
   CLAUDE.md's H8 table is the one nobody expects: routine per-tick trade management degrades
   to `live_broker_authority_false_observe_only` at `:2526`, so the book stops *managing* as
   well as stops closing. Flatten, confirm flat, then shut the gate.

---

## 0. What is in the package, in one table

| # | carry | what it fixes | measured | already tested | risk if it lands wrong |
|---|---|---|---|---|---|
| **C1** | Y's F7/B29 clock repair | eight deployed candidate sleeves run session logic **3 h from where it was mined** | `[MEASURED]` B497 | yes, wave 3 | none of the eight is armed; a wrong carry changes *candidate* generation, not the armed book |
| **C2** | Y's leaked-zero-offset fix | **534 refused decision-bar slots in 8 days**, including armed sleeves (`metals_core` 5, `crypto` 2, `energy_agri` 2) | `[MEASURED]` B500 | yes (`book_engine._resolve_repair_offset_seconds`, persisted latch) | this one DOES touch the armed book — it is why `book_engine.py` cannot be copied wholesale |
| **C3** | Y's lineage stamp | the live book records **nothing** about which code it is running | `[MEASURED]` B502 | trivial, one string per cycle | none; the packet file is not contract-bound |
| **C4** | §4.10 packet additions (Session P's carry) | realized swap/commission on every close, broker deal timestamps, `spread_r` at intent time, first-of-day latch record | `[MEASURED]`, `PACKET_EMITTER_CARRY.md` | yes — six gates in `verify_carry.py`, four safety proofs | refusal, not exception (proven) |
| **C5** | **AB's pre-gap generation fix** | the last closed bar before every session gap is unreachable: **1.3–6.8 % of five H4 sleeves' trades**, **4.26 % of 134,027 D1 trades** | `[MEASURED]` on the replay, `[UNVERIFIED]` on the live feed | **wired and tested by this session** — 8 tests | **changes which bars an armed book trades.** Default OFF; see §3 |

**C1–C4 ship together. C5 is a separate decision** and it is the only item here that changes
what the armed book does, so it has its own section and its own recommendation (which is *not*
"turn it on").

**And three things in this package are NOT carries — they are questions** (§5). AD measured
them on armed money and they need a sample, not a deployment.

---

## 1. Ordering, and the one dependency that would break the live book

Session AC established the shape and Session S established the ordering; both hold. The
package is:

```
C4 (packet: 5 files, book_owner.py LAST)  →  C1, C3 (independent)  →  C2 (book_engine.py)
```

**`src/utils/broker_clock.py` does not exist on the VPS.** `20_src/utils/` has no such file
and the VPS `governor_state.py` predates the clock work entirely. A top-level
`from ...utils.broker_clock import ...` in `packet_economics.py` would raise at module load,
propagate through `book_owner.py`, and **break the live book's import** — the worst outcome
this package could have. Session P made the import optional by construction
(`packet_economics.py:41-68`): without it the night count degrades to
`rollover_nights: None` with `error: broker_clock_module_unavailable` and every other field
still works. That makes C4 **order-independent** — file 1 can land after file 5, or never.
Guarded by `test_the_carry_survives_a_host_with_no_broker_clock_module`.

**`book_engine.py` cannot be copied wholesale** and this is the trap that has caught two
sessions. Mainline imports `config_safety_flag` and `precount_intent_filter`; neither exists
on the host. AC carried it as **one anchored hunk**, and C2 must be carried the same way.
Copying the file replaces a working import graph with a broken one and the book crash-loops.

**Two host facts that cost previous ceremonies time:**

- **Each book is TWO `python.exe` processes** with identical command lines, in a parent/child
  chain. A stop loop that kills one of a pair leaves the other alive; the supervisor then sees
  a book running, does not restart it, and the operator gets a green light **on old code**.
  Count to zero and re-query (`Get-CimInstance Win32_Process`, never
  `Get-Process | CommandLine` — that silently matches nothing on PowerShell 5.1).
- **The rollback block must be self-contained and its guards must throw.** In PowerShell an
  empty variable is not an error, and the shell an operator rolls back in is very often not
  the shell they copied in. `ACTIVATION_CARRY_VPS_RUNBOOK.md` refuses to delete anything
  without a readable `BACKUP_MANIFEST.json`, and it stops the **monitor** as well as the books.

**The runbooks to execute, in preference order:**

| item | runbook | verifier |
|---|---|---|
| C4 | `phase4/PACKET_UNBLOCK_VPS_RUNBOOK.md` | `phase3/token_carry/…` + P's six gates |
| C1–C3 | `phase5/activation_carry/ACTIVATION_CARRY_VPS_RUNBOOK.md` | `phase5/activation_carry/verify_carry.py --check all` |

`verify_carry.py` has six gates with real exit codes, and the two rows that matter are the ones
a naive verifier would miss: **a truncated file passes `imports` and `behaviour`** and fails
only the byte comparison (scanning every 512-byte boundary of `governor_state.py` finds exactly
five cut points that still import, three of which also pass `behaviour`), and **a correct
rollback on a host that already had Session S's carry** failed the gate until §3 started writing
a backup manifest. Run `--check all`; do not read one gate's PASS as the tree being right.

---

## 2. What each carry actually is

### C1 — the clock repair (Y §7.1, B497)

Eight of the nine sleeves the F7/B29 repair fixed are in the deployed candidate allowlist
(`agent_config.yaml:1274-1283`) and are today running session logic **3 h from where it was
mined**. Broker server wall clock is `America/New_York + 7 h` for both firms — the **US** DST
calendar, not EET/EEST — and the two calendars disagree ~4 weeks a year. Use
`src/utils/broker_clock.py`; it fails closed on an unregistered server. **Never hardcode +3.**

> **One statement in Y §7.2 is now stale, and it lowers this item's urgency rather than
> raising it.** Y wrote *"`metals_core` is ARMED and its A8 `session_hour` runs on the stale EU
> calendar"*, and measured exactly one H4 bar per day flipping (the 21:00 UTC bar), with the VPS
> on the **restrictive** side. That was true of the 12:55 UTC armed set. **`metals_core` was
> pulled at 14:25 UTC on 2026-07-29** and is not armed today, so the clock divergence no longer
> touches armed money at all. Y's measurement is correct; its "ARMED" framing is not, and the
> next divergence window (**2026-10-25 → 11-01**) is far enough out that this is a scheduling
> item and not an urgency. Realised exposure in the observed window was already zero — all five
> of `metals_core`'s FTMO packet rows were `future_decision_bar_time` skips, which is C2.

### C2 — the leaked-zero-offset fix (Y §7.3, B500)

**534 `unit_skipped / future_decision_bar_time` refusals in 8 days**, concentrated on 06-29,
06-30, 07-06, 07-07, 07-08, 07-10, 07-15 and 07-24, and including armed sleeves. Mainline
repaired this in wave 3 (`book_engine._resolve_repair_offset_seconds` plus a persisted latch)
and the VPS has never received it.

This is the item most worth landing, because it is **pure recovery**: the sleeve wanted to
trade, the engine refused it for a clock artifact, and nothing about the strategy changes. It
is also the item that touches `book_engine.py`, so it goes **last** and as **one anchored
hunk**.

### C3 — the lineage stamp (Y §7.4, B502)

The live book records nothing about which code lineage it is running. Y's entire §7 finding
depended on a human knowing the VPS sits at `redacted_host`. One string per cycle in the runtime
learning packet, on a file that is not decision-contract-bound. Y called it *"the cheapest
missing capture in the programme"* and that is not an exaggeration — it would have turned a
session into a five-minute check.

### C4 — the packet additions (§4.10, Session P)

Five files, `book_owner.py` last, plus a standalone read-only silence alarm that can land any
time or never. What becomes recoverable that was not:

| field | today | after |
|---|---|---|
| swap / commission | absent on `position_closed`; the carry question needed a second extraction from the deal record | realized, per close |
| broker deal timestamps | absent; three hold anchors exist and differ by **44 %** (2.2565 h / 1.8783 h / **1.2603 h** broker-true) | on every close, so the anchor question closes |
| `spread_r` | a regex substring inside `skip_reason`, **failing legs only** — so today it can only ever say "spread was the reason", never "spread was fine" | populated on every evaluated leg, pass or fail, labelled `measured` |
| first-of-day latch | absent | (sleeve, day, latched bar), which makes candidate fidelity measurable forever after |

Four safety properties, all **proven by test** rather than asserted: the carry imports nothing
that can reach a broker (transitive import-graph walk); it is inert on 79 % of the stream under
current config; its failure mode is refusal, not exception; and it is backward compatible.

---

## 3. C5 — AB's pre-gap fix, now wired, and why the recommendation is still "not yet"

**What the defect is.** `bar_provider.candles_to_bars` does `rows = candles[:-1]`
unconditionally, on the assumption that the last candle is forming. At a session close it is
not: the market shuts, no new bar begins, and the last candle **is** the freshly-closed
decision bar. It is discarded — and by the time the next session's bar starts forming, that
bar's close is more than two intervals old and `book_engine.py`'s recency guard refuses it as
stale. **The last closed bar before every weekend and holiday is unreachable.**

| population | measured | share |
|---|---|---|
| H4, five sleeves (AB) | 29 of 29 fires immediately before a gap of ≥ 2 intervals | **1.3 %–6.8 %** per sleeve, **6.4 % on `sub_xvol_pullback`** |
| D1, 134,027 trades (AF) | 5,705 trades, every Friday is a pre-gap bar | **4.26 %** |

**What this session added.** AB wrote and tested the capability and declined to wire it, for a
reason that was right: wiring it changes which bars an armed book trades, and it could not be
gated behind a config key because `agent_config.yaml` is token-bound. The gate is therefore a
**launcher argument**:

```
run_book.py --recover-pre-gap-bar
```

which is the same mechanism `--tags` already uses to bound the armed book — settable at
`run_book_supervisor.ps1`, needs no source edit on a live host, and touches no config byte, so
the activation token's digest is untouched and the armed book keeps placing.

`UltimateBookLiveEngine.__init__(..., recover_pre_gap_bar=False)` →
`UltimateBookOwner(..., recover_pre_gap_bar=False)` → the CLI flag. Default **False**.
`tests/ultimate_book/test_pre_gap_bar_wiring.py` — **8 tests** — asserts:

- with only one of `now` / `interval_minutes`, behaviour is unchanged (three cases);
- OFF, the generation engine's fetch carries **no** pre-gap kwargs, checked by intercepting all
  27 fetch calls rather than by reading the diff — and the test refuses to pass on fewer than
  20 calls, so it cannot go vacuous;
- ON, all 27 carry `now` plus the interval **derived from each spec's own timeframe**
  (`{(15, 15), (16388, 240)}` — a single interval everywhere would mean the timeframe was being
  ignored);
- the owner and the launcher actually thread it through (signature + source, so a refactor that
  drops the passthrough fails here and not at the console);
- **no config key was added**, asserted against `agent_config.yaml`'s text, so a future session
  that adds one has to read why not;
- and the half a fetch-only fix would have missed: **the recovered bar survives the recency
  guard.** A cycle triggers *on* a reference symbol's bar close, so the recovered bar's age is
  0 against `1 × interval` for the bar the engine would otherwise have used. Both are inside
  the `2 × interval` guard — **which is exactly why the defect was silent**: the engine traded
  a one-interval-old bar and looked perfectly healthy.

**The recommendation is to land the wiring and leave the flag OFF, and the reason is that the
evidence points both ways.**

| | direction |
|---|---|
| at D1 (AF, 134,027 trades) | the unreachable population is **worse**: mean **−0.0771 R** against **+0.0117 R** for reachable trades. The defect is currently *saving* money on this family. |
| at H4 (AB) | the sleeve it costs most is `sub_xvol_pullback` at 6.4 % — **which is armed**, and whose only gate failure is significance at n=88, so 6 more trades is not nothing. |
| everywhere | `[UNVERIFIED]` on the live MT5 feed. Whether the terminal returns a forming candle at a session close is a property of the terminal and **cannot be checked from this machine.** |

So the honest sequence is: **land the wiring (inert), then verify the live-feed premise, then
decide.** The verification is cheap and is a C4 by-product — once `spread_r` and the deal
timestamps are on every evaluated leg, an operator can read directly whether a Friday close
produced a candle the engine dropped. **That makes C5's decision downstream of C4, which is
another reason to ship C4 first.**

---

## 4. What is deliberately NOT in this package

- **Any `config/agent_config.yaml` edit.** Including `ultimate_book_include_clean3`. Flipping it
  is a token re-mint plus an execution-seal digest change
  (`b7_5_post_acceleration_semantic_verifier.py:753-754`) — cite that digest, **not** H1's
  input-binding drift check, which does not catch a worktree-local flip.

  > **But READ it on the host before anything else, and record what it says. This is step zero of
  > the whole package.** The record disagrees with itself: `CLAUDE.md` §4 states it is already
  > `true` on the VPS (`:1200`, set at the 2026-07-29 14:25 arming, which is what admits
  > `sub_xvol_pullback`), while **mainline `:1270` and the read-only 2026-07-25 export `:1200`
  > both read `false`** — and the export predates the arming by four days, so it cannot settle it.
  > No session has contacted the host since, so the live value is `[UNVERIFIED]`.
  >
  > **Why it is step zero.** At `false`, `--tags crypto,energy_agri,sub_xvol_pullback` intersected
  > with `effective_registry` (`book_engine.py:454`, `:480-481`) resolves to **TWO sleeves,
  > `crypto` and `energy_agri`** — measured both ways (29-registry → 2, 32-registry → 3). If it is
  > still `false` then the armed book is generating two sleeves, not three, and **every published
  > figure for the armed three prices a book that is not running**: 4.501 %/month, P2 0.9172, the
  > 0.313 %/month out-of-window control, and every redacted_account comparison built on the same set.
  > It costs one `Select-String` on the host and it is worth more than any measurement in this
  > package.
- **Arming, tokens, gates, `--tags` composition, the dial.** Borhen's.
- **Session P's three owner decisions** (OD-P1 emit-on-change, OD-P2 the join key, OD-P3
  `modelled_cost_r`). They are in `PACKET_EMITTER_CARRY.md` §7 with recommendations and they
  are decisions, not carries. OD-P1 is **irreversible for the window in which it runs** —
  packets not emitted are not recoverable.
- **Anything that would let this package be executed by a session.** It is for the owner's
  hands.

---

## 5. Three things AD measured on armed money that are questions, not carries

These need a **sample**, not a deployment. Each is stated with what would settle it and how
long that takes at the measured book rate of **~7 book-days/month**.

### 5.1 `energy_agri`'s live scale-out contract measures −0.308 R/day against the plain exit

`energy_agri` is armed and trading real money. Four sleeves run `partial_be_runner` live and
**no walk had ever simulated it**; AD did, and the policy is not uniformly good —
`metals_core` **+0.062**, `metals_softband` **−0.069**, `energy_agri` **−0.308 R/day**.

**It is thin and AD said so: n = 67 trades over 3 evaluable folds, p_raw 0.111.** Its best
cell, `flat_before_triple_swap`, reaches +0.603 R/day with `significance` as its only failing
gate — on the estate's thinnest generating sleeve.

**What would settle it.** The comparison is between two exit policies on the same entries, so
the sample needed is *trades*, not calendar time, and it can come from either direction:

| route | sample needed | at ~7 book-days/month |
|---|---|---|
| forward live evidence | ≥ 30 `energy_agri` fills at ≥ 30 distinct days (the lane's own day-blocked floor) | `energy_agri` produced **67 archive trades in 26 years** and **0 live fills in 38 days**. Forward-only is **not a route** — it is decades. |
| the archive, with more symbols | its FVG mechanism is **three symbols wide** and pooled at **+0.4571 R/day**, the strongest mean in AF's 30-family grid, dispersion ratio 0.117, 3 of 3 members positive | needs a **`NATGAS.cash` commission** — one deal row on either account, or a signed energy-class peer transfer. **Not** a tick capture and **not** a re-run: both leave the commission UNKNOWN. |
| re-simulate the plain exit only | already done — that IS the −0.308 | free, and it is what makes the question askable |

**So the honest answer is that live evidence cannot settle this and the data ask can.** That
makes AF §11's `NATGAS.cash` item the cheapest thing on this page.

### 5.2 The twelve `mx_*` D1 sleeves' live time stop truncates 72–90 % of their trades

`time_stop_bars` is **M15 PRINTED bars for every sleeve** (`execution.py:8953-8958`, verbatim),
so the twelve generating `mx_*` D1 sleeves' live time stop is **24–25 trading hours against a
72–96 h realised median**. Every published economic number for those sleeves describes a
contract the live book does not run.

**None of them is armed, so this is a composition input rather than an urgency** — and it cuts
both ways: it helps four of them and hurts five. It matters *now* only because `mx_btcusd` is
the estate's best new-edge candidate, and its live 1-D1-bar time stop costs **−0.141 R/day**
against the walk while what it actually wants is a **wider target** (`target_5R`,
**+0.309 R/day**, on a monotone ridge from 1R to 5R).

**Nothing to carry.** The number to carry into a composition decision is that `mx_btcusd`'s
published economics are at a contract the live book would not run, so an arming package for it
must state which exit it is being armed on.

### 5.3 The armed `crypto` sleeve's first positive out-of-window number

**+0.0869 R/day OOS, 60 % of folds positive, raw p 0.3001, n = 182, 2017-02..2026-07** — its
own rule on its own two symbols over the whole archive. Not significant and not presented as
such; the sign is right, and it is the sleeve-level version of the out-of-window question for
the book's largest single edge.

**What would settle it: sample, and the lever is conditioning, not breadth.** The same rule
across the nine-symbol crypto class scores **−0.1849** with a dispersion ratio of **4.74** and
a best-to-worst spread of **1.80 R per trade**. The crypto cluster is **refuted as
diversification**, so do not price a cluster cap as one.

---

## 6. The operator's checklist

0. **Read `ultimate_book_include_clean3` on the host and write down what it says** (§4). If it is
   `false`, stop and tell the sessions: the armed book is trading two sleeves, not three, and every
   published economic figure for the armed set is about a different book. One command, and it
   outranks everything below it.
1. **Read** `phase4/PACKET_UNBLOCK_VPS_RUNBOOK.md` §1 (ordering) and §2 (preconditions) in
   full before touching anything. It is PowerShell 5.1 throughout and the interpreter and repo
   root are derived **from the running book's own command line**, with a STOP if ambiguous.
2. **Write down `$backup`.** The rollback block derives everything from it and refuses to run
   without a readable `BACKUP_MANIFEST.json`.
3. **Preflight**, then copy C4's five files with `book_owner.py` LAST.
4. **`verify_carry.py --check all`.** All six gates. A truncated file passes two of them.
5. **Restart one book at a time.** Each book is two processes; count to zero.
6. **Confirm `--tags` is still on the command line.** The registry resolves **32** sleeves and
   `--tags` is the only thing bounding the book; a restart without it trades all 32 and the
   heartbeat looks perfectly healthy. `--tags ""` is falsy at `run_book.py:340` and means
   **all BUILT sleeves** — fail-open. Check the command line, not the heartbeat.
7. **Arm at a decision-day boundary, or delete `firing_sleeves.json` first.**
   `RunningConvictionLedger` persists a per-`decision_day` union of firing sleeves and
   `admission.py:1188` takes `na = max(na, override)` — monotone upward within the day. The
   exported VPS ledgers hold 6–7 distinct firing sleeves per day, and under the half-Kelly bins
   an `na` of 2 → 7 moves the multiplier 0.991 → 1.241: **+25.2 % on every unit that day.**
8. **Then C1, C3, then C2** as one anchored hunk. Re-verify after each.
9. **Leave `--recover-pre-gap-bar` off.** §3.

**Rollback is under two minutes from any point** and the runbook's guards throw rather than
proceed. If any gate fails, roll back and stop — the package is worth nothing compared to a
book running on a half-applied tree.
