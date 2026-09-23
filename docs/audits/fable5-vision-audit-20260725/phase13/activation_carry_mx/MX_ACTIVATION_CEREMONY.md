# Ceremony — put `mx_btcusd @ target_5R` on the FTMO book

**Session AZ, wave 13. The orchestrator executes this; Session AZ never touches the VPS.**
Read `AZ_CARRY_ENUMERATION.md` (what is carried and why) and `ORDERING_AND_PARTIAL_STATES.md`
(what a half-done ceremony leaves running) first. This page is the operator surface.

**Host:** `C:\Users\MSI\Documents\ai-trading-agent`, branch
`vps/ultimate-conditioned-expansion-minimal-2026-06-18` @ `7017c6745`.
**Interpreter:** `.venv-gtos\Scripts\python.exe` (3.13.13).
**Package:** `docs\audits\fable5-vision-audit-20260725\phase13\activation_carry_mx\`.

---

## 0. What this ceremony does, and what it does not

It puts the estate's **one standing admission** on a live account: `mx_btcusd @ target_5R`,
p 0.0011, **admits at two of three cost bands** on the ratified RECORDED population at
`CANDIDATE_BOOK_V1` α 0.10 (`phase11/MX_BTCUSD_CHALLENGE_DOSSIER.md`; the family basis and α
are Borhen's ratified rule).

It does **not** arm anything else. `sub_xvol_pullback`'s `target_4R` cell is wired in the same
file and **must not be selected** — it is armed at 3R on both accounts and its 4R cell REJECTS
at all four cost bands at the ratified rule (AU §1.3, p 0.0080 against a 0.002083 bar; AS §0.3
independently). The six `mx_*` short-horizon cells are likewise wired and off.

**Two owner decisions sit above this page and are not made by it:** whether to add the sleeve to
FTMO's `--tags`, and whether to change its registry confidence. This page assumes the first is
approved and the second is **not** — see §7.

---

## 1. Preconditions, all already met

| # | precondition | state |
|---|---|---|
| P1 | **The terminal can feed a 7,680-bar time stop.** After AQ's repair an open `mx_*` position asks for `max(96, 7680+64) = 7744` M15 bars, and a short feed makes the stop **inert**, not late. | **MET** — the F15 `copy_rates` probe (read-only, both terminals) returned **7,800** on FTMO and on redacted_account. `phase8/receipts/FXJPY_PULL_20260730.md` §"And the mx_btcusd precondition cleared". |
| P2 | **The sleeve is in the host's effective registry.** | **MET, and it needs no config change** — driving the HOST's own `book_engine._active_sleeve_names()` with the host's own config values returns **32 sleeves including `mx_btcusd_d1_donchian_20_breakout`** (`include_market_expansion_book: true` + policy `positive_weighted12_after_swap`, which resolves 12 sleeves and this is one). |
| P3 | **`include_clean3` is true on the host** (or the `--tags` intersection silently drops sleeves). | **MET** — read directly on the host 2026-07-30, `phase8/receipts/VPS_STEP_ZERO_VERIFIED.md`. |
| P4 | **The exit contract is wired and identity-proven** against the research cell. | **MET** — AU §1.2: 318/318 trades economically identical, 0 unexpected relabels; re-proved here on the reconstructed HOST tree (`receipts/AZ_CARRY_PROBE_V1.json` → `identity`). |
| P5 | **No seal exposure.** | **MET** — all four carried paths unbound by R2, R1, `code_authority_paths` and `config_file_hashes` (AS §0.2, re-checked in AZ-1 §7). No config file is touched, so **neither activation token moves**. |
| P6 | **The launch banner cannot kill the worker.** | **MET as of this package** — B1852; six of the eight wired sleeves used to raise `KeyError` at launch. `mx_btcusd` was never one of them, but the ceremony would have shipped the landmine. |

---

## 2. Transfer mechanics

Learned on 2026-07-30 and unchanged:

* host-admin one-shot commands cap at ~8,191 chars of encoded command. Transfer files in
  **≤2,800-char base64 chunks** via `Add-Content -NoNewline`, then decode and hash. 8 K and
  28 K chunks both fail.
* **Do not `git fetch` on the host.** The repo is large with LFS and the host has ~9–12 GB free.
* `pywinrm` sometimes returns a spurious nonzero status with a CLIXML progress record on stderr
  ("Preparing modules for first use"). Tolerate unless `S="Error"` is present; rely on explicit
  hash checks, not exit codes.
* Count processes with `Get-CimInstance Win32_Process` (never `Get-Process | CommandLine` on
  PS 5.1). Each book appears as a **parent/child python pair** — four processes for two books.
* Detached launches that must survive the session: WMI `Win32_Process.Create` with
  `CurrentDirectory` set.

**Files to transfer** (payload sizes, all LF, all parse-checked here):

| # | payload | → destination | bytes |
|---|---|---|---:|
| 1 | `files/execution_packets.py` | `src\components\ultimate_book\execution_packets.py` | 38,376 |
| 2 | `files/order_router.py` | `src\components\ultimate_book\order_router.py` | 5,916 |
| 3 | `files/book_owner.py` | `src\components\ultimate_book\book_owner.py` | 226,002 |
| 4 | **the payload preflight names** | `run_book.py` | ~23 K |
| — | `MANIFEST.json` + `verify_carry.py` | the package dir on the host | — |

Exact sha256s: `MANIFEST.json`. **Verify each file's sha256 on the host after decoding, before
moving to the next.**

---

## 3. The sequence

Every step below is a safe place to stop except step 10, and steps 3–7 change nothing that
trades. `ORDERING_AND_PARTIAL_STATES.md` §3 is the same table with the consequences spelled out.

```
 0  Backup: run_book.py, execution_packets.py, order_router.py, book_owner.py,
    run_book_supervisor.ps1  ->  C:\Users\MSI\Documents\gtos-mx-activation-backup-<UTCstamp>\
    with BACKUP_MANIFEST.json recording each path's sha256. --check rollback REQUIRES it.

 1  verify_carry.py --check preflight
    -> confirms the three known files are at their expected pre-carry bytes,
    -> and NAMES the run_book.py payload for this host's actual sha256.
    An UNRECOGNISED run_book.py sha256 is a STOP. Do not copy the primary payload over it;
    send the printed sha256 + byte count back and a matching payload is one rebuild away.

 2  Confirm BOTH accounts FLAT (see section 4), then create BOTH kill flags:
       pipeline_state\ULTIMATE_BOOK_KILL_ftmo.flag
       pipeline_state\ULTIMATE_BOOK_KILL_fn.flag
    Placement pauses; exit management continues; the supervisor restarts nothing.

 3  Copy 1  execution_packets.py    -> verify sha256
 4  Copy 2  order_router.py         -> verify sha256
 5  Copy 3  book_owner.py           -> verify sha256
 6  Copy 4  run_book.py (the named payload) -> verify sha256
    IN THIS ORDER. Reversing any pair leaves an unsafe host state (9 of the 16 subsets
    are: 4 module-load deaths, 3 startup deaths, and 2 SILENT placement outages in which
    everything an operator looks at reads green).

 7  verify_carry.py --check all      (postflight + deps + imports + behaviour)
    Must be PASS, exit 0. STOP HERE IF NOT. The books are still running old code in memory.

 --- everything above is the CARRY. everything below is the ACTIVATION. ---

 8  Edit scripts\run_book_supervisor.ps1 (see section 5) — FTMO worker only:
       tags   += ,mx_btcusd_d1_donchian_20_breakout
       add      --frontier-exits mx_btcusd_d1_donchian_20_breakout

 9  Delete the FTMO namespace's firing_sleeves.json (back it up first) — section 6.

10  Restart the supervisor SCHEDULED TASK (not the books): stop task -> count book pythons to
    ZERO -> start task. The supervisor parses its worker args at ITS OWN start, so a .ps1 edit
    reaches respawns only through a task restart.

11  Post-verification — section 8. Both books back, four processes, FTMO's command line and log
    lines as specified. Then verify_carry.py --check behaviour once more.

12  Release BOTH kill flags (move them to the backup dir — reversible).
```

---

## 4. The flat check, and the honest reason for it

**Confirm both accounts flat before step 2.** The reason on record is now wrong and the rule is
still right, so both halves need saying:

`FXJPY_PULL_20260730.md` says *"AS's adopt-path `KeyError('trigger_r')` fix is not yet carried
to the host, so a restart must only happen with zero open positions until it is."* **That
premise is false.** The host's `execution.py` handles `time_stop` rehydration through a branch
mainline never received, and driving it returns `hydrated: True` today (AZ-1 §3). A restart
with open positions would not raise.

The rule stands for the **real** reason: `--frontier-exits` changes the exit contract, and a
position adopted **without a trade record** is rehydrated from the sleeve identity under
whatever selection the process was launched with. `mx_btcusd` has never traded live, so there
is no such position and no exposure today — which is precisely why the flip should happen now.
**Flip the selection at a flat book** is the same rule a `--tags` change already needs (B365),
and a flat book is the cheapest way to know that a restart changed nothing you did not intend.

If the accounts are not flat and the window matters more than the certainty: the carry (steps
0–7) is safe with positions open, because nothing in it runs until a restart. Stop at step 7
and do steps 8–12 at the next flat moment.

---

## 5. The supervisor edit

The host's `run_book_supervisor.ps1` (18,991 B, forked from the mainline copy) carries a
per-book table; the arming ceremonies added a `tags=` field to it twice, and the `fx_jpy` pull
edited both tag strings with the guard *"exactly 2 occurrences or abort"*.

**Recommended: mirror `tags` — a per-book `frontier` field, FTMO only.**

```
FTMO worker, after:
  tags     = "crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert,mx_btcusd_d1_donchian_20_breakout"
  frontier = "mx_btcusd_d1_donchian_20_breakout"

redacted_account worker: UNCHANGED.
  tags     = "crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert"
  (no --frontier-exits)
```

and in `$bookCommand`, append the flag only when the field is non-empty.

**The exact tag string, to copy:**

```
crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert,mx_btcusd_d1_donchian_20_breakout
```

**Guards for this edit:**

* the tag string must appear **exactly twice** before the edit (one per book) and the FTMO one
  is the one that changes — abort on any other count;
* `--tags ""` is falsy at `run_book.py` and silently means **every BUILT sleeve** (B359). Never
  leave the field empty;
* an all-typo `--tags` stands the book down every tick **in silence** (`registry.py:144`).
  Verify the command line at step 11, not the heartbeat;
* `--frontier-exits ""` is **refused** at launch by design, and an unknown sleeve name is
  refused too — that fail-open shape is closed rather than inherited.

**The alternative** — one `--frontier-exits` on `$bookCommand` for both books — is
*measurably inert* on redacted_account, because the sleeve is not in FN's `--tags` so its profile is
never resolved and it has no position to adopt. It is not recommended: FN's live command line
would then advertise a contract FN does not run, and the post-verification in §8 reads exactly
those command lines.

**The most expensive mistake available here is doing step 8 before step 6.** `argparse` exits
on an unrecognised argument, so `--frontier-exits` with an uncarried `run_book.py` kills every
respawn of every namespace forever. `--check deps` reads the `.ps1` and refuses that state.

---

## 6. `firing_sleeves.json`, and the one sizing step this can take

`RunningConvictionLedger` persists a per-`decision_day` union of firing sleeves and
`admission.py:1188` takes `na = max(na, override)` — **monotone upward within the day**. Live
half-Kelly bins: `((1,1,0.748),(2,3,0.991),(4,99,1.241))`.

Widening `--tags` from four sleeves to five can raise the day's `na` by one. That crosses a bin
**only** when exactly three of the armed four have already fired today: `na` 3 → 4 moves the
multiplier **0.991 → 1.241, +25.2 % on every unit that day**. `na` 4 → 5 moves nothing.

**Mitigation (step 9), the same one the redacted_account arming used:** back up and delete the FTMO
namespace's `pipeline_state\ultimate_book\<ns>\firing_sleeves.json`, or arm at a decision-day
boundary. `_KEEP_DAYS = 2` and today-only keys mean prior days cannot contaminate a fresh day —
the hazard is same-day only.

---

## 7. What this is worth, stated so nobody is surprised

* **Registry confidence `0.025`**, against a total registry weight of `7.77` — **0.32 %**. This
  is small **by design**, and it is the pre-existing default-off market-expansion weight, not a
  number this ceremony chooses. AI's finding stands: *at registry confidence 0.025, admitting
  `mx_btcusd` is economically inert*, and **re-weighting it is a separate owner decision**
  (OD-AI-5) that this page does not take and should not be read as taking.
* **Size on the recent folds, not the headline.** The cell's chronological fold means are
  `+1.134, +1.512, +1.866, +0.284, +0.112` R/day. AN measured the admission **decaying
  chronologically** — the two most recent folds average **+0.198 R/day**, 13.2 % of the early
  folds. The ratified population rule's own guidance is to size on the recent folds. The
  `+0.982 R/day` in the dossier is the full-window mean and is **not** the planning number.
* **`maxbars` share 1.89 %** (0.31 % `maxbars` + 1.57 % `time_stop`), far below AR's
  pre-declared 25 % threshold — the cell is not measuring its horizon.
* **The admission is contingent on two repairs that are now both on this host**: AQ's time-stop
  unit repair (at the old `96` the same cell REJECTS at all four bands, p 0.0564) and AU's
  wiring (at the spec's 2R it REJECTS, p 0.0064). Neither alone admits. Any package citing this
  number must name both.
* Expect **long silences**. This is a D1 breakout sleeve at 0.32 % of book weight.

---

## 8. Post-verification — what to expect, and the line that PROVES it

Run these after step 10 and before step 12.

**8.1 Four book processes.** `Get-CimInstance Win32_Process` — two parent/child python pairs.

**8.2 FTMO's live command line** must contain **both**:

```
--tags crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert,mx_btcusd_d1_donchian_20_breakout
--frontier-exits mx_btcusd_d1_donchian_20_breakout
```

redacted_account's must contain the four-sleeve tags and **no** `--frontier-exits`.

**8.3 The two log lines that prove it took — this is the section's whole point.**

*The frontier contract resolved* — a `WARNING` from `run_book.py`, emitted once at startup,
before the launcher:

```
FRONTIER EXIT CONTRACT IS ON for mx_btcusd_d1_donchian_20_breakout: target_5R (broker TP 5.0R).
This changes WHERE or WHEN this book exits that sleeve; ...
```

Absence of this line means the flag did not reach the process — the book is running the
committed 2R contract with an otherwise perfectly healthy log. **Check for the line, not for
health.**

*The decision timeframes changed* — `BookLauncher starting: tfs=...`:

```
BEFORE (armed four, all H4):        tfs=[16388]
AFTER  (armed four + mx_btcusd):    tfs=[16388, 16408]
```

`16408` is D1 and it is **derived from the specs**, not from the flag
(`launcher.py:105-108`). So it is independent evidence that the *tag* landed, where the banner
is evidence that the *contract* landed. Both, or the ceremony is not done. (Measured on the
carried tree; the same derivation confirmed the M15 timeframe leaving with `fx_jpy`.)

**8.4 `authority_gates_ON=True halted=False killed=False`** on FTMO once the flag is released,
and `config_digest=ffe16657feaf` unchanged — **no config byte moved, so the token still binds.**

**8.5** `verify_carry.py --check behaviour` — PASS, exit 0.

**8.6** The monitor daemon's next line: both accounts' equity and DD headroom as before.

---

## 9. Rollback

**Order matters, and it is the reverse of the ceremony's:**

```
1  Re-create both kill flags (instant brake, orphans nothing).
2  Restore scripts\run_book_supervisor.ps1 FIRST from the backup.
   -- a host with the old run_book.py and a supervisor line still carrying --frontier-exits is
      `error: unrecognized arguments` on every respawn: a permanent crash loop of BOTH books.
3  Restore the four files from the backup (order does not matter with the books stopped).
4  Restart the supervisor task; count book pythons to zero and back.
5  verify_carry.py --check rollback   -> must be PASS, exit 0.
   It judges against BACKUP_MANIFEST.json, not against the lineage, and it also asserts the
   tree still STARTS -- the frontier selection failing to construct is the SUCCESS condition
   there, not a failure.
6  Release the kill flags.
```

**A cheaper brake exists and should be reached for first.** To stop `mx_btcusd` trading without
touching any code: remove the tag and the flag from the supervisor line and restart the task.
The carried code is inert with no selection — every default is byte-identical to what the host
ran before, asserted by `--check behaviour` item 2 over all four armed sleeves. Full rollback
is for a defect in the carry itself, not for a change of mind about the sleeve.

**Never reach for `live_broker_authority: false`** (H8): it returns before flattening, strands
open positions, and degrades routine exit management to observe-only.

---

## 10. If something is wrong

| symptom | most likely cause | do this |
|---|---|---|
| `--check preflight` says a file has UNKNOWN bytes | something changed it since the last ceremony | **STOP.** Do not copy over it. Find out what changed first. |
| `--check preflight` says `run_book.py` is UNRECOGNISED | the host is on a version not in the variant table | **STOP.** Send back the printed sha256 + byte count; a matching payload is one rebuild away. Do **not** copy the primary payload. |
| `--check deps` FAILs | files copied out of order | copy the named dependency now, re-run. **Do not restart a book in that state.** The `order_router`-without-`execution_packets` case does not crash — it refuses every placement with a healthy heartbeat. |
| both books crash-looping after step 10 | step 8 done before step 6, or a truncated copy | re-create both kill flags, then §9. A crash loop costs exit management and the breach flatten; broker-side SL/TP survive it. |
| books healthy, no frontier line in the log | the flag did not reach the process | check the live command line (§8.2), not the heartbeat |
| books healthy, `tfs=[16388]` only | the tag did not reach the process, or `include_clean3` flipped | check the command line and re-read P3 |
