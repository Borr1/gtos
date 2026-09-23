# Session AC — the pre-arming carry, authored against the live lineage

**Wave 5, activation critical path. Branch `phase5/activation-carry` off `main` @ `c018987d4`.
Blocks B550–B579.**

Package: `phase5/activation_carry/` — `MANIFEST.json`, `diffs/`, `files/`, `verify_carry.py`,
`build_carry.py`, `receipts/`, `ACTIVATION_CARRY_VPS_RUNBOOK.md`, `ORDERING_AND_PARTIAL_STATES.md`.
Tests: `pytest tests/ultimate_book/test_activation_carry_vps_lineage.py -q`.
Rebuild the whole carry: `python3 docs/audits/fable5-vision-audit-20260725/phase5/activation_carry/build_carry.py`.

---

## 0. The answer

**The carry is built, it applies to the host's own bytes with zero fuzz, and both defects were
reproduced on those bytes before being fixed.** Four items in one package: the strand fix, B56, the
composition with Session S's packet carry, and — decided here, and argued in §5 — the same B56
defect in `.tools/monitor_books.py` as a separately gated stage D.

Three things changed the shape of the job, and none of them was in the prompt.

**1. `book_engine.py` cannot be carried from mainline, and copying it is the catastrophic class.**
Mainline's file differs from the host's by six changes, not one: B56 plus D3, D10, the bar-time
latch, and `config_safety_flag` in place of `config_bool_value`. Two of those are imports the host
**cannot satisfy** — `git show redacted_host:…/bridge.py` has no `config_safety_flag`, and `…/admission.py`
has no `precount_intent_filter`. Copying mainline's `book_engine.py` onto that host is an
`ImportError` at module load on both namespaces, i.e. exactly the failure Session S's carry existed
to prevent. It is carried as **one anchored hunk** instead. `governor_state.py`, by contrast,
differs from the host **only** by B56 and carries byte-identical.

**2. This carry makes `broker_clock.py` load-bearing, which falsifies a row of Session S's ordering
table.** S rates a missing, late or truncated `broker_clock.py` as costing *nothing* — correct, and
correctly reasoned, because `packet_economics.py:50-51` guards the import. The carried
`governor_state.py` does not guard it. After stage A2 that row is false and a half-written
`broker_clock.py` kills both books at module load. **The unguarded import is deliberate**: a guard
would fall back to the detected server offset, which is the early-reset behaviour B56 removes, and
it would do it silently on a funded account with nothing watching.

**3. Probing the import graph finds half the fatal partial states — and probing whole files finds
only part of the space.** Every subset was materialised and run. An import-only probe — which is what
S's carry needed, and what I nearly shipped — found **8** of the original 32 states fatal; carrying on
to the first construction, which `run_book.py:294` also does unguarded, found **16**. The extra eight
import perfectly and die on `TypeError: unexpected keyword argument 'reset_rule'`.

Then a refuter found a **third** invariant my grid could not contain (stage D without
`broker_clock.py` crash-loops the alerting layer), taking it to **64 states, 36 fatal**; and another
showed that **39 truncated** states pass both probe stages and are unsafe in three silent ways. All 39
fail the byte comparison, so the composite gate holds — but "`--check imports` is the reason the
restart is safe" was too strong and is withdrawn. Detail in §9.

**Session S's carry changes no verdict in any of the 32 pairs.** That is the composition answer, and
it is measured rather than argued.

---

## 1. The lineage is the host's own bytes

`_vps_lineage/{governor_state,book_engine,execution}.py`, fetched read-only from the running host on
2026-07-29, are **byte-identical** to `redacted_host`. So is `.tools/monitor_books.py` against the
2026-07-26 working-tree export. Session S had established 63/63 files across
`src/components/ultimate_book/`, `src/utils/` and `src/mt5/`; this extends the proxy to
`src/components/execution.py` and `.tools/`, which S's check did not cover, and shows it still holds
**27 days after** the export.

That is what makes `build_carry.py` possible: every carried file is either copied byte-identical
from mainline or constructed by applying **named, anchored edits to the host's own file**, with each
substitution asserting it matched exactly once. Nothing in `files/` is hand-written, and
`lineage_bytes()` fails closed if the fetched copy ever disagrees with the commit.

---

## 2. Both defects, reproduced before being fixed

### The strand

Calling the host's own `ExecutionEngine._normalize_volume`: **33 of 300** two-decimal lot sizes fail
to round-trip at `(0.01, 0.01)`, and `0.03 → 0.02`. The prompt's figure reproduces exactly.

What the prompt did not have: **it is much worse on coarser geometry.**

| `volume_min`, `volume_step` | stranded (of 500 valid volumes) |
|---|---|
| 0.10, 0.10 | **253 (50.6 %)** |
| 0.50, 0.10 | 180 |
| 0.01, 0.001 | 152 |
| 0.10, 0.01 | 128 |
| 0.01, 0.01 | 37 |
| 1.00, 1.00 | 0 |

After the carry: **0 of 17,000** across nine geometries, and **0** rounded up.

**44 of 327 real broker close deals** carried an affected volume — FTMO 17/135, redacted_account 27/192 —
measured directly from `vps-export-20260725/.../\*_history_deals_get.jsonl`. Session T's figure is
confirmed from the raw records rather than inherited.

One correction that runs the other way: the prompt's `(0.03 - 0.01) / 0.01 = 1.9999999999999996` is
right and **mainline's shipped comment is wrong** (`1.9999999999999998`). Fixed in the carried file.

### B56

Constructing the host's own `GovernorStateBuilder` with the measured FTMO server offset, the reset
window opens **1 h early normally and 2 h early inside a calendar-mismatch window**. Sharpest form:
at `2026-10-27T21:30Z` the host's governor says the current window opened **30 minutes ago**, while
FTMO's next reset is **1 h 30 away**. For those two hours the governor believes the daily-loss budget
has reset while FTMO is still counting against the previous day. That is the breach direction, and it
is why this item and not the strand is the one that can cost the account.

After the carry the FTMO window lands on 00:00 CE(S)T in every case and redacted_account stays on server
midnight — which is redacted_account's own rule, and must not change.

---

## 3. The claim I was told to verify rather than trust: it holds

> "`book_engine.py:111-113` reads `governor_daily_reset_rule` **or falls back to**
> `prop_safe_selector_daily_reset_timezone` — which the VPS FTMO profile **already sets**. So this
> should be **code-only, no config edit, no H1 exposure.** Verify that claim before relying on it."

Measured through `src.utils.config.apply_profile_overrides` — the production resolver, not a
hand-rolled YAML read — on the host's own config, for both profiles
`scripts/run_book_supervisor.ps1` launches:

| profile | key in the merged `gtos_vnext_runtime` | rule the carried engine passes |
|---|---|---|
| `operator_profile` | `prop_safe_selector_daily_reset_timezone: Europe/Prague` (profile `:87`) | `Europe/Prague` |
| `redacted_account` | absent | `None` → server midnight |

`book_owner.py:146` hands `merged["gtos_vnext_runtime"]` to the engine as `self.config`, and that is
the subtree the profile key lands in. **No config file changes.** Both FTMO profiles are
decision-contract-bound, so this is the difference between a code carry and a re-seal plus ~16.5
machine-hours per window.

`broker_clock.py` is also confirmed **stdlib-only** — read with `ast`, not `rg`, because the module
discusses `ZoneInfo` at length in prose explaining why it does not use it. That matters concretely:
the host venv has **27 packages and no `tzdata`**, so a `zoneinfo` dependency would raise
`ZoneInfoNotFoundError` inside the governor on Windows.

---

## 4. Ordering, and where it is safe to stop

Full table in `ORDERING_AND_PARTIAL_STATES.md`. The short version:

**Three invariants.** `governor_state ⇒ broker_clock` (else `ModuleNotFoundError` at module load),
`book_engine ⇒ governor_state` (else `TypeError` at startup), and `monitor_books ⇒ broker_clock`
(else a permanent crash loop of the alerting layer). **36 of 64 states violate at least one**; no
state violating none of them fails. So the copy order is
`broker_clock → governor_state → book_engine → execution → S's five with book_owner last`, then
`monitor_books` in a separate stage — and **every prefix of the runbook is a safe state to stop in**.

The third came from a refuter, and the honest way to state it is that my enumeration **could not have
found it**: stage D was not in the state space. A completeness claim is only as wide as the space it
was measured over.

**What a bad partial state actually costs, measured rather than asserted:**

* The supervisor **never stops a book**. `Test-BookRunning` returns `$false` only when zero processes
  exist; the stale-heartbeat branch logs `alert_only_no_forced_restart open_position_safety`. This is
  read from the host's own supervisor — **18,991 bytes**, against the 6,980-byte copy vendored into
  mainline. The two have forked.
* The crash loop is **~33 s**, not the 5 minutes in my prompt. Five minutes is the scheduled task's
  re-fire interval, which only matters if the supervisor itself is gone.
* **It is not an unprotected position.** Of **175** `W7:`-tagged live orders with volume, **175 carry
  a non-zero broker-side `sl`** (97/97 FTMO, 78/78 redacted_account); 127 carry a `tp`. The book attaches
  them to the entry itself. A crash loop costs exit management and the breach flatten — no
  break-even, no trailing, no time stop, no partial — not the stop, which lives on the broker's
  server. Still bad enough to order around; not "naked and unmanaged", and the distinction is what
  lets an operator decide calmly instead of fast.
* **The brake is the kill flag, not `Stop-Process`.** `launcher.py:204-211` computes
  `place = not (killed or halted)`: the flag pauses placement, the process keeps running and keeps
  managing exits, and the supervisor restarts nothing because nothing is missing. `Stop-Process` is
  the code-swap mechanism, used exactly once.

---

## 5. `monitor_books.py` — in, surgically, and last

The prompt asked me to decide and justify either answer. **In**, and the reason is a defect, not a
deadline.

Two live processes run it, and it is the only thing alerting on the daily-loss rule of the account
being armed. `SRV_OFFSET_H = 3   # FTMO/FN server = UTC+3 (EEST)` drives `srv_today`, which selects
which deals count toward `realized_today` → `daily_pl_pct` → the **−4.5 % "NEAR −5 % HARD LIMIT"**
and −2.5 % soft-stop alerts. It is wrong twice, both times in the same dangerous direction: the
label is wrong and the number is dated (**both servers drop to +2 on 2026-11-01**), and the server
clock is not FTMO's reset rule at all, so the monitor's "today" is 1–2 h early exactly as the
governor's was.

Concretely: a real losing deal at 2026-10-27 20:00 UTC on FTMO is **counted** by the carried monitor
and **dropped** by the struck code, because `srv_today` had already rolled to 2026-10-28. Fixing the
governor and leaving this would make the risk layer and the alerting layer disagree about which day
it is — a half-fix that is harder to reason about than either state alone.

**But it is not in the funded-account restart.** No book imports it; the supervisor restarts it on
its own in ~35–40 s; so it is stage **D**, ordered after the books are verified healthy, with its own
gate (`--check stage-d`) and its own rollback. That keeps one verification gate over one risk
surface.

**It does have one hard dependency, and it is the third invariant** (§4): the carried monitor
imports `broker_clock` at module top, unguarded, so stage D without stage A1 crash-loops the
alerting layer. A refuter found that; my state space could not.

**Carried surgically** — two anchored edits, not mainline's 255-line divergence into a live
monitoring process. The window is computed as an **instant** rather than a date, because a CE(S)T
date compared against a broker-wall date is a type error wearing a fix; deal times are converted
with `broker_epoch_to_utc` under the server rule.

---

## 6. The runbook, and the four defects it does not reproduce

`ACTIVATION_CARRY_VPS_RUNBOOK.md` is Windows PowerShell 5.1 throughout: `Get-CimInstance
Win32_Process` (never `Get-Process | CommandLine`, which silently matches nothing on 5.1), no bash
heredocs, no bare PATH `python`, the interpreter and repo root **derived from the running book's own
command line** with a STOP if ambiguous, and multi-line Python as a file (`verify_carry.py`) rather
than a code block. `test_runbook_avoids_the_four_defects_found_on_that_host` pins all four
mechanically.

Two things it adds that the prompt did not ask for, both measured on the host:

* **Each book is TWO `python.exe` processes** with identical command lines, in a parent/child chain.
  A stop loop that kills one of a pair leaves the other alive; the supervisor then sees a book
  running, does not restart it, and the operator gets a green light on **old code**. §7 counts to
  zero and re-queries.
* **The rollback block is self-contained and its guards throw.** It derives everything from
  `$backup` — the one thing the operator was told to write down — because the shell an operator
  rolls back in is very often not the shell they copied in, and in PowerShell an empty variable is
  not an error. It refuses to delete anything without a readable `BACKUP_MANIFEST.json`, and it
  stops the **monitor** as well as the books.

`verify_carry.py` has six gates with real exit codes. The matrix below is asserted by
`tests/ultimate_book/test_activation_carry_vps_lineage.py`, which **executes** the verifier — no
test did before a refuter pointed out that the authority gate could not pass at the step that runs
it:

| tree | preflight | postflight | imports | behaviour | stage-d | rollback |
|---|---|---|---|---|---|---|
| host base | **0** | 2 | 0 | — | — | **0** |
| the §6 state (A + B + C, stage D deferred) | — | **0** | **0** | **0** | 2 | — |
| full carry incl. stage D | 0 | **0** | 0 | 0 | **0** | 2 |
| `book_engine` only | — | 2 | **2** | — | — | — |
| `governor_state` truncated to 17,408 of 19,278 B | — | **2** | 0 | 0 | — | — |
| correctly rolled back, on an S-applied host | — | 2 | 0 | — | — | **0** |

The last two rows are the ones that matter. A truncated file **passes `imports` and `behaviour`**
and fails only the byte comparison — scanning every 512-byte boundary of `governor_state.py` finds
exactly **five** cut points that still import, and three of those five also pass `behaviour`, which
reproduces the refuter's "5 of 35" independently. And a correct rollback on a host that already had
Session S's carry **failed** the gate until §3 started writing a backup manifest.

The rollback gate is the one S's carry lacked: its only check demanded the **carried** shas, so an
operator who had just rolled back correctly was told the tree was broken and not to restart. Each
check now scores only its own failures, so a FAIL in one cannot be reported as a FAIL in the next
under `--check all`. And it refuses to answer at all under an interpreter that is not the books'
(exit 3), which is the wave-3 runbook defect that never bit because nobody checked.

---

## 7. What I got wrong, and withdrew

- **I shipped a fabricated sha256.** The first draft of the runbook quoted
  `b6a9ef7d98d2f1cb…e0f1` for `book_engine.py`: the correct 12-character prefix, read off a truncated
  console print, followed by **52 characters I invented**. An operator following the runbook alone
  would have hit a STOP on a perfectly correct copy of a live trading file, mid-procedure, on a
  funded account. Two mechanisms now: `build_carry.py::sync_runbook_hashes` **generates** every
  `sha="…"` from the manifest and refuses to finish if the runbook quotes a hash no manifest knows,
  and a test pins each quoted hash to its own file. It earned its keep within the hour — correcting
  the float literal changed `execution.py`'s sha and the test caught the stale quote at once.
- **My health gate was a false negative in both directions.** The first draft told the operator to
  confirm the kill flag by looking for `PLACEMENT PAUSED` in `run_book_console.log`. That string goes
  to `notify_alert` (`launcher.py:183-199`), a push channel, and `tick()` returns early on
  `no_new_bar` **without logging**, so a healthy H4 book writes nothing there for hours. Rebuilt
  around the per-namespace heartbeat, using the exact parsing idiom the host's own supervisor uses.
- **I nearly shipped the import-only probe**, which reports 8 fatal partial states instead of 16 —
  and then shipped a state space that could not see a third invariant at all, while calling it
  complete. "Two invariants, and they are the only two" was a claim about my grid, not about the
  carry.
- **I claimed `--check imports` was "the reason §7 is safe."** Withdrawn. It is necessary and not
  sufficient: 39 truncated states pass it. The byte comparison is the gate that does the work.
- **My first two tests were wrong, not the carry.** One asserted a 2 h gap between two window starts
  that are 22 h apart (the right statement is about the *next* reset); the other tested
  `"ZoneInfo(" not in src` against a module whose docstring explains at length why it avoids
  `ZoneInfo`. Both rewritten to say what they meant.

---

## 8. Three claims in my prompt that are wrong

Per working agreement §3, a prompt that turns out to be wrong is a finding.

1. **"The mainline fix is Session T's, on `main`."** It is not on `main`. At `c018987d4`,
   `src/components/execution.py:2345` still reads
   `steps = math.floor((lots - volume_min) / volume_step)`. T's fix is on `phase4/canary-package` and
   `phase4/wave4-integration`; Session S's packet carry, described as "being merged to `main` by
   Session U as you start", is on `phase4/packet-unblock` and also not on `main`. Nothing changes for
   the carry — both were read out of git — but a session that trusted the sentence and copied from
   its working tree would have shipped the **unfixed** file to a funded host.
2. **"a 5-minute restart loop."** Measured ~33 s.
3. **`1.9999999999999996`** — here the prompt is right and *mainline* is wrong. Recorded the other
   way round from the usual.

Everything else the prompt asserted and I could check held: the host's `execution.py` at `:2552`,
10,166 lines against mainline's 10,085; nine close producers; 33/300 and 44/327; the `:111-113`
fallback; `operator_profile.yaml:87`; `broker_clock.py` stdlib-only; and the code-only claim.

---

## 9. What the refuters overturned

Five refuters, distinct lenses, each told to default to "refuted". **Two claims survived intact and
three did not — and the three that did not were the three that mattered most.** Blocks B566–B573.

| # | lens | verdict |
|---|---|---|
| 1 | partial-application states | **PARTLY REFUTED** — a **third** fatal invariant the state space excluded by construction, plus 39 truncated states that pass the probe and are unsafe |
| 2 | break the rollback | **REFUTED** — three CRITICAL, including Session S's own defect reproduced inside this carry |
| 3 | is B56 really config-free | A, B, C **SURVIVE** (and stronger than stated); D **PARTLY REFUTED** — a DST-seam defect in the shortening direction |
| 4 | do the diffs reconstruct byte-identically | **SURVIVES** — 1,080,000 bitwise comparisons, 0 disagreements; five documentation defects |
| 5 | runbook executability | **REFUTED** — five CRITICAL, including a gate that could not pass at the step that runs it |

### The five that mattered most, all now fixed

1. **The authority gate could not pass where the runbook runs it.** `--check postflight` demanded the
   carried sha for stage D, which the runbook deliberately defers to §10 — so at §6, one step before
   the one-way door, a correct carry exited 2. That teaches an operator either to roll back a good
   carry or to walk past a red gate. **No test executed the verifier at all**; five now do.
2. **Session S's defect, reproduced inside the carry written to eliminate it.** `--check rollback`
   judged against the lineage base, but §3 backs up whatever the host was *actually* on. On a host
   that already has S's packet carry, a **correct** rollback failed the gate — and the failing lines
   then instructed a deletion that produces `ModuleNotFoundError` on both books. §3 now writes a
   `BACKUP_MANIFEST.json` and the gate judges against that.
3. **§9's `$backup` placeholder was a live grenade.** `"<the path printed in section 3>"` is a valid
   PowerShell string; `Test-Path` missed on all ten targets and the delete arm fired anyway, removing
   `broker_clock.py` while leaving `governor_state.py` carried — the exact fatal state the ordering
   document exists to prevent, 33 s before the supervisor restarts both books into it.
4. **A third fatal invariant** — stage D without stage A1 crash-loops the alerting layer — which the
   32-state enumeration **could not have found**, because stage D was not in the space. 64 states, 36
   fatal.
5. **The DST-seam defect**, in the shortening direction: at the autumn seam an hour of realized loss
   dropped out of the daily budget. Fixed in mainline with a correction pass; 17,520 hourly probes now
   sit exactly at 00:00 CE(S)T with zero backwards steps.

### And what they could not break

Published, because a refuter that only confirms is worth nothing. The carried `_normalize_volume` is
**bitwise identical to Session T's** over 1,080,000 comparisons including denormals, `±inf`, NaN and
`nextafter` neighbours; 4,549,807 broker-rejectability probes found **0** results off-grid, above
`volume_max` or below `volume_min`; eight mutations of the build inputs produced 8/8 named
`SystemExit`. `broker_clock`'s DST arithmetic matched `zoneinfo` on **26,304** hourly probes across
2026–2028 with **0** disagreements. The config-free claim held through the production resolver and is
**stronger** than I stated: all three of `operator_profile.yaml`, `ftmo.yaml` and
`agent_config.yaml` are decision-contract-bound in R2, and **none of the five carried files is**.
And the heartbeat rewrite is confirmed correct against the host's own logs — `PLACEMENT PAUSED`
appears **0 times** in them, while `run_book_fn_console.log`'s newest entry was **7 days old** on a
healthy book.

### One finding recorded rather than fixed, and why

A malformed reset rule falls back to the **detected server offset** — the 1–2 h-early behaviour B56
removes — and **8 of 31 tested values do it silently, with no log at all**. Fixing it properly needs
a change in `book_engine.py` and a registry entry in `broker_clock.py`, and `broker_clock.py`'s sha is
**shared byte-for-byte with Session S's carry**, so touching it would force S's manifest to be
regenerated for a case the carry-time gate already covers (`--check behaviour` asserts the resolved
window for both accounts on the host). Full detail and the 31-value table in **B573**.

---

## 10. What is NOT verified

Stated next to the claims that are, because the difference is the whole value of the rest.

- **No PowerShell interpreter has parsed the runbook.** Neither `pwsh` nor `powershell` exists on
  this laptop. What was done: 21 code blocks balance-checked, zero non-ASCII inside any
  `Write-Host`/`throw` string, no bash heredocs, no bare PATH `python`, no `Get-Process | CommandLine`,
  every construct read against 5.1 semantics, and a refuter walking the whole document as the
  operator. **That is review, not execution**, and the first runnable check will be on the host.
  Two PowerShell defects survived every refuter and were caught by my own final read (B574) — a
  nested `$_` that matches nothing and reports "no book process" on a healthy host, and a bash-style
  `\$` escape inside a STOP message — so the residual rate is not zero.
- **The host's current state**, deliberately. `--check preflight` answers it at execution time.
- **`_vps_lineage/` is untracked**, so `build_carry.py`'s cross-check between the fetched host bytes
  and the lineage commit silently degrades to the `git show` fallback in a fresh clone.

Full list: **B575**.

---

## 11. What is NOT done, and what is next

- **Nothing was applied to the VPS**, nothing was armed, no token was minted, no gate was moved, and
  no broker-capable script was run. The orchestrator applies this package through an owner-executed
  ceremony.
- **The current state of the host is [UNVERIFIED] by design.** The three fetched files are current as
  of 2026-07-29 and the rest of the tree is `redacted_host` as of the 2026-07-26 export.
  `--check preflight` answers the question at execution time and STOPs on anything else.
- **`main` does not yet contain Session T's strand fix or Session S's packet carry** (§8.1). This
  package reads both out of git, so it is correct today; the wave-5 integrator should confirm the
  composed state again after wave 4 lands.
- **The 255-line mainline/host divergence in `.tools/monitor_books.py`** is untouched beyond the two
  anchored edits, and so is the fork between mainline's 6,980-byte supervisor and the host's
  18,991-byte one. Both are real, both are recorded, neither is this session's.
- **A malformed reset rule falls back to the dangerous behaviour, silently in 8 of 31 tested
  values** (B573). Not fixed here because the fix would touch `broker_clock.py`, whose sha is shared
  byte-for-byte with Session S's carry. The carry-time gate covers the live case; a future profile
  edit is what is left open.
- **`scripts/dual_broker_execution_follower.py:915-926` reads the same profile key with
  `ZoneInfo(tz_name)`** and, on a host with no `tzdata`, swallows the error and falls back to `3.0` —
  the exact 2 h-early behaviour. On the never-execute list, out of scope, recorded (B573).
- **Two shared-instrument findings for the wave-5 integrator.**
  `tests/test_implementation_state_block_citations.py` was passing above B200 for the wrong reason
  (bold-form blocks are invisible to it, so everything above the highest heading-form block was
  excused); writing the first heading-form block above B200 exposed 12 covered citations, and
  `IN_FLIGHT_WAVE_RANGE` is advanced rather than the regex re-fixed, because wave-4 integration
  already fixed the regex. And `_tracked_markdown()` does not consult git despite its name, so
  untracked scratch files are scanned as if they were repo content.
