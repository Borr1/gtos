# Stage 3 (completion) — VPS runbook: land the held packet-emitter files

**Executed by Borhen. Never by an agent.** Nothing in this document was run against the VPS.
Every check below was proved on the research laptop against a reconstruction of the VPS's own
commit `redacted_host` — see §9 for what "reconstruction" means and how far it was verified.

**A live funded FTMO account is being armed on three sleeves.** Read §0 and §1 before touching
anything. Every **STOP** is a real stop: §7 puts you back where you started in under two minutes.

This runbook supersedes `phase3/PACKET_EMITTER_VPS_RUNBOOK.md`, which cannot be followed as
written — §10 lists the three defects and what replaced them.

---

## 0. What you are doing, in four sentences

On 2026-07-29 two inert files of Session P's packet carry landed and three were **held**, because
`book_owner.py` imported `convergence_advisory.py` — a module the VPS lineage has never had. You
are landing a **re-authored** version of those three files that does not import it, plus the two
inert ones if they are not already there.

This changes what the books *record*, not what they *do*: no config change, no new config key, no
change to any placement gate, order path, or activation token. The gates stay false and this
runbook stops if they are not.

The point is holding time and realized cost. Until this lands, the forward shadow records neither,
and holding time is the exact quantity that made OD-3 hard.

---

## 1. The ordering rules, with their real consequences

P's runbook said "file ORDER is the one thing that can break this" without saying what each
mistake actually costs. Measured on the reconstructed lineage, the four cases are **not**
equally bad, and knowing which is which is what keeps you calm at 2 a.m.

| what goes wrong | what actually happens | severity |
|---|---|---|
| **`book_owner.py` is present and ANY of files 2/3/4 is missing, stale, or half-copied** — this includes copying a **mainline** `book_owner.py`, and it includes landing `book_owner.py` before `runtime_learning_packet.py` | **`ImportError`/`ModuleNotFoundError` at module load.** `run_book.py:32` imports `UltimateBookOwner` at module top, unguarded, so the process **exits 1 at startup on both namespaces**. The supervisor only ever *starts* a missing book, never stops one → a 5-minute restart loop in which `manage_open_positions` **never runs at all**. Open positions go unmanaged on a live funded account. | **CATASTROPHIC** |
| `packet_guard.py` or `packet_economics.py` lands before `runtime_learning_packet.py`, with `book_owner.py` still the old one | Nothing. They are new files and **nothing on this lineage imports them** until `book_owner.py` lands. | none |
| `broker_clock.py` missing, or landing last, or never landing | Nothing. The import is guarded (`packet_economics.py:50-58`) and the guard catches **any** exception, not just `ImportError` — so an absent file *and a truncated one* both degrade to `rollover_nights: null` with a labelled reason. | none |

> **This table was wrong in its first version, and the correction matters.** It previously rated
> "`book_owner.py` before `runtime_learning_packet.py`" as *survivable*, on the reasoning that the
> new `economics=` keyword would raise a `TypeError` at `book_owner.py:1984` — the penultimate line
> of `manage_open_positions` (1879-1985), after all management effects — where `BookLauncher.tick()`
> (`launcher.py:290`) would catch it and the loop would survive.
>
> **That failure is structurally unreachable and the reasoning never gets a chance to apply.**
> Carried `book_owner.py:32` imports `packet_guard` at module top, and `packet_guard.py:46` imports
> `PACKET_REJECTED_EVENT_TYPE` from the emitter at module top. The import graph fails **before any
> function body runs**. All 32 partial-copy permutations were enumerated on the reconstructed
> lineage: **14 of the 16 containing `book_owner.py` die at module load**; only the full carry, and
> the full carry minus `broker_clock.py`, import at all.
>
> So there is no "degraded but survivable" middle case. **Any incomplete state that includes
> `book_owner.py` is the catastrophic one.** Found by an adversarial pass against this runbook.

**The rule that carries all the weight: `book_owner.py` is LAST, and §5 must pass before any
restart.** Copy order is `1 → 2 → 3 → 4 → 5`. §4's five `Copy-Item`s are **not atomic** — if the
supervisor respawns a book while you are partway through, it respawns onto a broken tree. That is
survivable only because §5 catches it *before* you deliberately restart anything: the books keep
running on old code, in memory, until they are restarted. **Do not restart anything until §5.1 and
§5.2 both exit 0.**

---

## 2. Preconditions

Open **Windows PowerShell** (5.1) as the user that runs the books, and `cd` to the repo root.

```powershell
# 2.0 Confirm the shell. This runbook is written for 5.1 and uses no PowerShell 7 syntax.
$PSVersionTable.PSVersion
```

```powershell
# 2.1 Find the books, the interpreter they run, AND the repo they run FROM.
#     Get-Process does NOT expose CommandLine on Windows PowerShell 5.1 -- a Where-Object on
#     $_.CommandLine silently matches nothing and you would conclude the books are stopped.
#     Get-CimInstance is the form that works.
$books = Get-CimInstance Win32_Process -Filter "name like '%python%'" |
         Where-Object { $_.CommandLine -like '*run_book.py*' }
$books | Select-Object ProcessId, CommandLine | Format-List
```

> **Expect two rows**, one per namespace (`operator_profile`, `redacted_account_live_bee34003`).
> **If you see zero rows, STOP** — either the books are down (a different problem, and it
> outranks this one) or you are in the wrong session.

> ### STOP — there are TWO repo trees on this host, and they are not the same code
>
> Measured from the export manifest:
>
> | tree | `src\` files | runs the books? |
> |---|---:|---|
> | `C:\Users\MSI\Documents\ai-trading-agent` | 522 | **YES — all 10 live processes** |
> | `C:\Users\MSI\Documents\ai-trading-agent-runtime-learning-packet` | 519 | no |
>
> Over the 519 `src\` paths they share, **25 files differ by sha256** — including
> `book_owner.py`, `admission.py`, `execution.py`, `permissions.py`, `bridge.py` and
> `launcher.py`. **Carrying into the wrong one changes nothing and looks like it worked.**
> `preflight` would report `*** UNEXPECTED CONTENT ***` there, which is the correct answer, but
> do not rely on that — get the directory right.

```powershell
# 2.2 Derive the repo root and the interpreter FROM the running book, rather than typing them.
#     This is the fix for the wave-3 defect where every `python ...` step tested the PATH
#     interpreter (~3.11) instead of the one the books run (.venv-gtos, ~3.13).
$cl   = ($books | Select-Object -First 1).CommandLine
$PY   = [regex]::Match($cl, '^\s*"?([^"]*?python\.exe)"?').Groups[1].Value
$REPO = Split-Path (Split-Path (Split-Path $PY -Parent) -Parent) -Parent
Write-Host "interpreter : $PY"
Write-Host "repo root   : $REPO"
Set-Location $REPO
& $PY --version
```

> **Check both lines before continuing.** `$REPO` must be
> `C:\Users\MSI\Documents\ai-trading-agent` (see the STOP above) and `$PY` must be the
> `.venv-gtos` interpreter under it. If `$PY` came out empty, the command line was quoted
> differently than expected — read it off `$cl` by hand and set `$PY` yourself.

```powershell
# 2.3 The three ultimate_book gates MUST be false, and MUST still be false at the end.
#     The pattern is scoped on purpose: the unscoped form matches 26 lines in this config, of
#     which 12 read `true` (unrelated subsystems), so a literal reading of "if any reads true,
#     STOP" would stop you on a correctly-gated host.
Select-String -Path config\agent_config.yaml `
  -Pattern "ultimate_book_(apply_to_execution|live_activation_allowed|live_broker_authority)"
```

> **Expect exactly 3 lines, all `false`** — at `:1161`, `:1162`, `:1163` on the VPS lineage.
> **Any other count, or any `true`, and you STOP.** Fewer than 3 is also a stop: it means the
> config is not the one this runbook was written against. Copy the three lines into your notes —
> §8.1 compares against them.

```powershell
# 2.4 Record the packet log's size and mtime so §6 can prove it grew.
Get-Item shadow_logs\ultimate_book_runtime_learning_packets.jsonl |
    Select-Object Name, Length, LastWriteTime
```

```powershell
# 2.5 Back up everything you are about to overwrite or add.
$stamp  = Get-Date -Format "yyyyMMddTHHmmssZ"
$backup = "..\gtos-packet-unblock-backup-$stamp"
New-Item -ItemType Directory -Force -Path $backup | Out-Null
Copy-Item src\components\ultimate_book\runtime_learning_packet.py $backup -ErrorAction SilentlyContinue
Copy-Item src\components\ultimate_book\book_owner.py              $backup -ErrorAction SilentlyContinue
Copy-Item src\components\ultimate_book\packet_economics.py        $backup -ErrorAction SilentlyContinue
Copy-Item src\components\ultimate_book\packet_guard.py            $backup -ErrorAction SilentlyContinue
Copy-Item src\utils\broker_clock.py                               $backup -ErrorAction SilentlyContinue
Write-Host "backup at $backup"
Get-ChildItem $backup | Select-Object Name, Length
```

---

## 3. Preflight — what is actually on this host

Transfer the carry directory to the host first (any channel — the hashes make it verifiable):

```
docs\audits\fable5-vision-audit-20260725\phase4\packet_carry\
    MANIFEST.json
    verify_carry.py
    files\   <- the six files you will copy
```

> **The transfer must preserve bytes exactly.** Every carried file is LF-only. A text-mode
> transfer that rewrites LF to CRLF changes the hash and §5 will refuse it — which is the point,
> but it is easier to use a binary-safe channel than to debug it afterwards.

```powershell
# 3.1 Read the host's current state. This does not modify anything.
& $PY docs\audits\fable5-vision-audit-20260725\phase4\packet_carry\verify_carry.py --check preflight
```

Each file reports one of:

- **`ABSENT`** — expected for `packet_guard.py`, and for the two inert files if the 2026-07-29
  carry did not in fact land them.
- **`AT EXPECTED BASE`** — the file is byte-identical to VPS commit `redacted_host`. Expected for
  `runtime_learning_packet.py` and `book_owner.py`.
- **`ALREADY CARRIED`** — this exact version is already there. Expected for `broker_clock.py` and
  `packet_economics.py` **if** the 2026-07-29 inert carry landed. Copying them again is a no-op.
- **`*** UNEXPECTED CONTENT ***`** — **STOP.** Someone changed that file on the host, or the
  lineage moved since `redacted_host`. Back it up and stop; do not overwrite something you cannot
  identify. The script exits non-zero and tells you the hash it found.

**The script exits 0 only if every file is absent, at base, or already carried.** If it exits
non-zero, stop here.

---

## 4. The carry — five files, `book_owner.py` last

```powershell
$src = "docs\audits\fable5-vision-audit-20260725\phase4\packet_carry\files"

# 1 - new, optional, no dependants
Copy-Item "$src\broker_clock.py"            src\utils\broker_clock.py                            -Force
# 2 - overwrite; adds ONE optional keyword argument, so the old book_owner keeps working
Copy-Item "$src\runtime_learning_packet.py" src\components\ultimate_book\runtime_learning_packet.py -Force
# 3 - new, inert
Copy-Item "$src\packet_economics.py"        src\components\ultimate_book\packet_economics.py     -Force
# 4 - new, inert; its imports resolve only once 2 has landed
Copy-Item "$src\packet_guard.py"            src\components\ultimate_book\packet_guard.py         -Force
# 5 - LAST. Nothing changes until this lands.
Copy-Item "$src\book_owner.py"              src\components\ultimate_book\book_owner.py           -Force
```

Optional, any time or never — standalone, read-only, imports nothing from the repo:

```powershell
Copy-Item "$src\ultimate_book_packet_silence_alarm.py" scripts\ultimate_book_packet_silence_alarm.py -Force
```

---

## 5. Verify the copy **before** you restart anything

This is the step that catches a bad copy while both books are still running the old code.

```powershell
# 5.1 Every byte, against the manifest.
& $PY docs\audits\fable5-vision-audit-20260725\phase4\packet_carry\verify_carry.py --check postflight
if ($LASTEXITCODE -ne 0) { Write-Host "STOP - restore from $backup" -ForegroundColor Red }
```

```powershell
# 5.2 The module graph loads. This is the failure that blocked the carry.
& $PY docs\audits\fable5-vision-audit-20260725\phase4\packet_carry\verify_carry.py --check imports
if ($LASTEXITCODE -ne 0) { Write-Host "STOP - restore from $backup" -ForegroundColor Red }
```

`--check imports` prints four `OK` lines ending with `book_owner`, then two facts:

- **`broker_clock available : True`** — expected. `False` is **not** an error; it means night
  counts come back `null` with `error: broker_clock_module_unavailable` until file 1 lands.
- **`convergence advisory carried : False`** — this **must** read `False`. `True` means you copied
  the mainline emitter instead of the carry, and it will not run here.

```powershell
# 5.3 The existing corpus is untouched. Every historical packet must still re-hash to itself.
& $PY docs\audits\fable5-vision-audit-20260725\phase4\packet_carry\verify_carry.py --check packets
```

> At this point `carry an economics block : 0` is **correct** — nothing new has been emitted yet.

**If any of 5.1–5.3 exits non-zero, restore from `$backup` (§7) and stop.** Both books are still
running the old code; you have lost nothing.

---

## 6. Restart — one book at a time

Do **not** launch `run_book.py` yourself. Stop the worker and let the supervisor respawn it: it
loops every 30 s and sleeps 3 s after launching, so 45 s is enough.

> **The 45 s budget assumes a HEALTHY supervisor, and nothing so far has checked that.** The
> supervisor can hang; `run_book_supervisor.ps1` documents this itself, and in that case respawn
> falls to the 5-minute scheduled task instead — so a hung supervisor turns "45 s then 60 s more"
> into a five-minute silence that reads as a failed start. Check the heartbeat first.

```powershell
# 6.0 The supervisor is alive and recent. Its own staleness threshold is 120 s.
$hb = Get-Content pipeline_state\supervisor_heartbeat.json -Raw | ConvertFrom-Json
$hb | Format-List
Get-Item pipeline_state\supervisor_heartbeat.json | Select-Object LastWriteTime
Get-ScheduledTask -TaskName *GTOS* | Select-Object TaskName, State
```

> **If the heartbeat is older than ~2 minutes, the supervisor is not respawning on its 30 s loop.**
> You can still proceed, but budget **6 minutes**, not 45 seconds, before concluding a restart
> failed — and say so in your notes so the §6.3 timings are read correctly.

```powershell
# 6.0b How much is actually at risk if a restart goes wrong. Record this BEFORE you kill anything:
#      §1's severity table is written in terms of "open positions go unmanaged", and this is the
#      number that turns that phrase into an exposure you can size.
Get-Content shadow_logs\ultimate_book_runtime_learning_packets.jsonl -Tail 2000 |
    ForEach-Object { $_ | ConvertFrom-Json } |
    Where-Object { $_.event_type -eq 'position_managed' } |
    Select-Object -Last 20 created_at_utc, namespace, ticket_hash_sha256, symbol |
    Format-Table
```

```powershell
# 6.1 FTMO first. Get-CimInstance, not Get-Process -- see §2.1.
$ftmo = Get-CimInstance Win32_Process -Filter "name like '%python%'" |
        Where-Object { $_.CommandLine -like '*run_book.py*' -and $_.CommandLine -like '*ftmo_server3*' }
$ftmo | Select-Object ProcessId, CommandLine | Format-List
```

> **If that returns nothing, STOP and do not proceed to `Stop-Process`.** An empty match is the
> exact false-green this runbook exists to prevent: you would sleep 45 s, see *a* book running,
> and conclude the restart worked while it is still on the old code.

```powershell
# 6.2 Stop it by PID -- explicit, so you can see what you killed.
$ftmo | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Start-Sleep -Seconds 45

# 6.3 Confirm it came back, and that it is a NEW process.
Get-CimInstance Win32_Process -Filter "name like '%python%'" |
    Where-Object { $_.CommandLine -like '*run_book.py*' -and $_.CommandLine -like '*ftmo_server3*' } |
    Select-Object ProcessId, CreationDate | Format-List
```

> **A new `ProcessId` and a `CreationDate` from the last minute.** If the PID is unchanged, the
> stop did not take — investigate before going further. If **no** row comes back after another
> 60 s (or ~6 min on a stale heartbeat, §6.0), the book is failing to start: go to §7, restore,
> and let it respawn on the old code.

```powershell
# 6.3b A new PID is NOT proof of health. A crash-looping book produces a new PID and a fresh
#      CreationDate every ~33 s -- which is exactly what 6.3 shows. These two logs settle it.
Get-Content shadow_logs\book_supervisor.log -Tail 15
Get-Content shadow_logs\run_book_console.log.err -Tail 25
```

> **One `(re)starting book ns=...` line for the restart you just did is normal. Several, seconds
> apart, is a crash loop**, and `run_book_console.log.err` will hold the traceback. A traceback
> naming `ImportError`, `ModuleNotFoundError`, `packet_guard`, `packet_economics` or
> `runtime_learning_packet` means the carry is the cause: **go to §7 now.**

```powershell
# 6.4 Confirm THIS book is emitting -- filtered by namespace.
#     Both namespaces write ONE shared log: the log path is a single global config key with no
#     namespace interpolation, and the live export holds 41,271 ftmo + 57,841 redacted_account rows in
#     the same file. So a bare `-Tail 3` routinely shows rows from the book you have NOT
#     restarted, which reads as success while the restarted book is silent. Always filter.
Get-Content shadow_logs\ultimate_book_runtime_learning_packets.jsonl -Tail 400 |
    ForEach-Object { $_ | ConvertFrom-Json } |
    Where-Object { $_.namespace -eq 'operator_profile' } |
    Select-Object -Last 3 created_at_utc, namespace, event_type |
    Format-Table
```

> **You need rows whose `namespace` is the book you just restarted, with a `created_at_utc` from
> the last couple of minutes.** If the only fresh rows belong to the other namespace, the
> restarted book is not emitting — that is a failed restart, not a success.

**Only then** repeat 6.1–6.4 for `redacted_account`, substituting `*redacted_account*` for `*ftmo_server3*`
and `redacted_account_live_bee34003` for the namespace.

---

## 7. Rollback — under two minutes, from any point

> **If you are in a new shell, `$backup` and `$PY` are gone.** Set them again first — the backup is
> the most recent `..\gtos-packet-unblock-backup-*` directory:
>
> ```powershell
> $backup = (Get-ChildItem .. -Directory -Filter "gtos-packet-unblock-backup-*" |
>            Sort-Object Name -Descending | Select-Object -First 1).FullName
> Write-Host "using backup: $backup"
> Get-ChildItem $backup | Select-Object Name, Length
> $PY = "C:\path\to\.venv-gtos\Scripts\python.exe"   # as read in §2.1
> ```

**Restore file by file, to the correct directory.** Do not use a wildcard copy: the backup is one
flat folder, so `Copy-Item "$backup\*.py" src\components\ultimate_book\` would drop a stray
`broker_clock.py` into the `ultimate_book` package — a state neither the carry nor the backup
describes, which nothing then removes.

```powershell
# 7.1 Restore the two files that EXISTED before the carry (both are always in the backup).
Copy-Item "$backup\book_owner.py"              src\components\ultimate_book\book_owner.py              -Force
Copy-Item "$backup\runtime_learning_packet.py" src\components\ultimate_book\runtime_learning_packet.py -Force
```

```powershell
# 7.2 For each of the three NEW files: restore it if the backup has it (it was already on the
#     host), otherwise DELETE it (it was absent before you started). This is exactly the
#     ABSENT-vs-ALREADY-CARRIED distinction §3.1 printed, re-derived from the backup so you do
#     not need that output any more.
$new = @{
  "packet_guard.py"     = "src\components\ultimate_book\packet_guard.py"
  "packet_economics.py" = "src\components\ultimate_book\packet_economics.py"
  "broker_clock.py"     = "src\utils\broker_clock.py"
}
foreach ($name in $new.Keys) {
  $saved = Join-Path $backup $name
  $dest  = $new[$name]
  if (Test-Path $saved) {
    Copy-Item $saved $dest -Force
    Write-Host "restored $dest"
  } else {
    Remove-Item $dest -Force -ErrorAction SilentlyContinue
    Write-Host "removed  $dest (absent before the carry)"
  }
}
```

```powershell
# 7.3 Prove the rollback landed. This MUST pass before you restart anything.
& $PY docs\audits\fable5-vision-audit-20260725\phase4\packet_carry\verify_carry.py --check imports
```

> `--check imports` is written to pass in **both** directions. On a rolled-back tree it reports
> `detected state : ROLLED BACK / PARTIAL`, confirms `book_owner` still loads, and exits 0 with an
> explicit reminder that **the carry is not in place and this is not a successful carry**. Only an
> actual import failure exits non-zero.

Then restart both workers exactly as in §6.

---

## 8. Verification after both books are back

```powershell
# 8.1 The gates did not move. Asserted against expected values, not eyeballed against a §2.3
#     screen that scrolled an hour ago.
$gates = Select-String -Path config\agent_config.yaml `
  -Pattern "ultimate_book_(apply_to_execution|live_activation_allowed|live_broker_authority)"
$gates | ForEach-Object { $_.Line.Trim() }
$bad = $gates | Where-Object { $_.Line -notmatch ':\s*false' }
if ($gates.Count -ne 3 -or $bad) {
    Write-Host "STOP - gates are not 3x false. THIS OUTRANKS THE CARRY." -ForegroundColor Red
    $bad | ForEach-Object { $_.Line.Trim() }
} else {
    Write-Host "gates OK: 3 of 3 false" -ForegroundColor Green
}

# 8.2 Both books alive, both namespaces.
Get-CimInstance Win32_Process -Filter "name like '%python%'" |
    Where-Object { $_.CommandLine -like '*run_book.py*' } |
    Select-Object ProcessId, CreationDate, CommandLine | Format-List

# 8.3 The corpus is intact and the new block is appearing.
& $PY docs\audits\fable5-vision-audit-20260725\phase4\packet_carry\verify_carry.py --check packets
```

> **`carry an economics block` should become non-zero once the market moves.** The block only
> attaches to events that have something to cost — placements, closes, and managed positions with
> broker fields. It is legitimately 0 for a while after the restart.
>
> **If it is still 0 after an hour of open market, do not declare success.** That is the
> false-green class this carry exists to prevent. Report it.

```powershell
# 8.4 Optional, and useful from now on: the silence alarm, if you copied it.
& $PY scripts\ultimate_book_packet_silence_alarm.py `
    --packets shadow_logs\ultimate_book_runtime_learning_packets.jsonl `
    --expect-namespace operator_profile --expect-namespace redacted_account_live_bee34003
Write-Host "silence alarm exit code: $LASTEXITCODE"
```

> **Expect a non-zero exit code, and do not treat it as a carry failure.** The alarm returns 1
> whenever `healthy` is false, and it evaluates the **entire retained log** — which on this host
> includes months of weekend closures. Run against the 2026-07-25 export with exactly these flags
> it reports `"silent": true`, **5 silence breaches** on `redacted_account` including one of **673.1
> minutes starting 2026-07-03** and `silent_hours: 145.33`. All historical, all long predating
> this carry.
>
> **What you are looking for is a NEW breach whose window contains your restart.** Compare the
> breach list against the timestamp you did §6.2. If the only breaches are the historical
> weekend ones, this step passed. If a breach opens at your restart, the book stopped emitting
> when you restarted it — go to §7.

---

## 9. What was proved before this was written, and what was not

**Proved [MEASURED]:**

- The VPS lineage commit `redacted_host` is byte-identical to the 2026-07-26 VPS working-tree export
  across `src/components/ultimate_book/`, `src/utils/` and `src/mt5/` — **63 of 63 files, 0
  mismatches**. That is why a reconstruction from the commit is a faithful stand-in for the host.
- The block reproduces exactly: a mainline `book_owner.py` on the reconstructed lineage raises
  `ModuleNotFoundError: No module named 'src.components.ultimate_book.convergence_advisory'` at
  `book_owner.py:24`. `packet_guard.py` against the old emitter raises
  `ImportError: cannot import name 'PACKET_REJECTED_EVENT_TYPE'`.
- With the carry applied, all four modules import on the reconstructed lineage, `book_owner`
  included — and with `broker_clock.py` deliberately withheld as well.
- All **99,112** packets in the live export reproduce their own recorded `packet_hash_sha256`
  under the carried emitter — **100.0000 %**.
- A `position_managed` packet with no economics comes out of the carried emitter **byte-identical**
  to what the live emitter produces today: same keys, same hash.

**Not proved, and it is the one thing you are checking for [UNVERIFIED]:**

- **The state of the host itself.** This was written without access to the VPS. Whether the
  2026-07-29 inert carry actually landed `broker_clock.py` and `packet_economics.py`, and whether
  anything else on that host has moved since `redacted_host`, is what §3.1 measures rather than
  assumes. If §3.1 reports `*** UNEXPECTED CONTENT ***`, this runbook's premise is wrong and you
  should stop rather than proceed.

---

## 10. Three defects in the wave-3 runbooks, and what replaced them

All three were found on the live host or by direct check, and all three are the false-green class.

1. **`Get-Process python | Where-Object { $_.CommandLine -like ... }` silently matches nothing.**
   Windows PowerShell 5.1's `Get-Process` does not expose `CommandLine`, so the filter drops every
   row and the pipeline does nothing — including `Stop-Process`. The operator sleeps 45 s, sees a
   book running, and concludes the restart worked **while it is still on old code**. Two
   occurrences, `phase3/PACKET_EMITTER_VPS_RUNBOOK.md:116,118`. Replaced throughout by
   `Get-CimInstance Win32_Process`, plus an explicit "if this returns nothing, STOP" in §6.1.
   *Session I's `STAGE0_VPS_RUNBOOK.md` already used the correct form; P's runbook regressed it.*
2. **`python - <<'PY'` heredocs — bash syntax in a PowerShell runbook.** They do not run as
   written. Two occurrences, `phase3/PACKET_EMITTER_VPS_RUNBOOK.md:155,181`. Replaced by
   `verify_carry.py`, a reviewable file with real exit codes and no quoting problem.
3. **Every `python ...` line tested the wrong interpreter.** The books run
   `.venv-gtos\Scripts\python.exe`; PATH `python` is a different version. **This is broader than
   previously recorded: it affects Session I's `STAGE0_VPS_RUNBOOK.md` too** (lines 122–125, 299),
   which is a live-safety runbook — 9 occurrences across the two documents. Replaced by §2.1–2.2,
   which *reads the interpreter off the running book's own command line* rather than hardcoding a
   path this session could not verify, and by a **dependency probe** inside `verify_carry.py` that
   stops if this interpreter lacks the book's own dependencies.
   *(Corrected 2026-07-29 at wave-4 integration, B367. This read "a version guard … that stops if it
   finds itself on a pre-3.10 interpreter" — the guard Session S itself withdrew at B313, because
   PATH `python` (~3.11) and the book's venv (~3.13) **both clear a 3.10 floor**, so it could never
   fire on the actual wrong interpreter. `verify_carry.py:85-86` says so in the code, and this
   runbook's own §2.1 already stated the two versions. The false-assurance wording was the one left
   in the summary.)*
