# Activation carry — VPS runbook

**Windows PowerShell 5.1. Every code block runs as written.** No bash, no heredocs, no
`python` from PATH. Read `ORDERING_AND_PARTIAL_STATES.md` first; this implements it.

Applies, in **one restart**: the strand fix, B56 (the daily-loss reset rule), and Session S's
packet-emitter carry. Then, separately, the monitor's reset window.

**This is a live funded FTMO account.** Nothing here places, closes or modifies a trade, and
nothing here arms anything. The gates (`ultimate_book_live_activation_allowed`,
`ultimate_book_live_broker_authority`) are not touched and must stay false.

**If any step says STOP, stop.** Do not improvise a next step; report the output.

---

## 0. Before you start

### When to do this

**Prefer a market-closed window.** Between §7 and §8 the books are down for ~3–4 minutes with
`manage_open_positions` not running: no break-even move, no trailing, no time stop, no partial, no
breach flatten. Every W7 entry carries a broker-side stop and most carry a target (measured: 175 of
175 orders have a non-zero `sl`), so a position is not naked — but it is unmanaged for that window.
**Record the open-position count before you start**, so §8 can confirm it is unchanged.

### What you need, and where to get it

You need: RDP to the host, the `activation_carry` folder, and Session S's `packet_carry` folder.

`packet_carry` is **not on `main`**. It lives on branch **`phase4/packet-unblock`** at
`docs/audits/fable5-vision-audit-20260725/phase4/packet_carry/` (also recorded in this carry's
`MANIFEST.json` as `composes_with.session_S_packet_carry_source_ref`). If you cannot obtain it, you
can still run stages A, B and D — see §6's decision table — but **say so**; the packet emitter stays
blocked.

Copy **both** into the repo tree at their repo paths, so that this file ends up at

```text
<repo>\docs\audits\fable5-vision-audit-20260725\phase5\activation_carry\ACTIVATION_CARRY_VPS_RUNBOOK.md
<repo>\docs\audits\fable5-vision-audit-20260725\phase4\packet_carry\MANIFEST.json
```

`verify_carry.py` derives the repo root from its own location and refuses to run if it is not
in a real repo tree, so this placement is not cosmetic.

Open **Windows PowerShell** (not pwsh, not cmd) and confirm the version:

```powershell
$PSVersionTable.PSVersion
```

Expected major version `5`. Everything below is 5.1-compatible.

### If your shell dies mid-procedure

RDP drops. Every block from §4 on uses variables set in §1 and §3, and in Windows PowerShell an
**empty variable is not an error** — `Join-Path $null "x"` returns `x`, `$null -contains 1` is
`$false`, and a loop over an empty array prints nothing and reports success. So after any
disconnect, re-run **§1** (which re-derives `$repo`, `$py`, `$carry`) and re-set `$backup` and
`$targets` from §3 before continuing. §9 is the one block that needs none of this: it derives
everything from `$backup` alone.

---

## 1. Find the repo the books actually run from — do not assume it

**There are two repo trees on this host and they differ in 25 `src` files.** Deriving the root
from the running process is the only correct way to pick one.

`Get-Process` in Windows PowerShell 5.1 **does not expose `CommandLine`**. A filter written
that way silently matches nothing, and you would conclude "no books are running" on a host
where both are. Use `Get-CimInstance Win32_Process`.

```powershell
$books = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
           Where-Object { $_.CommandLine -like "*run_book.py*" })
$books | Select-Object ProcessId, ParentProcessId, CommandLine | Format-List
"book processes: {0}" -f $books.Count
```

**What must be true: at least one process for each of the two namespaces**
(`operator_profile`, `redacted_account_live_bee34003`). **STOP if either namespace shows zero.**

```powershell
foreach ($ns in @("operator_profile","redacted_account_live_bee34003")) {
  $c = @($books | Where-Object { $_.CommandLine -like "*--namespace $ns*" }).Count
  if ($c -eq 0) { Write-Host "STOP: no book process for $ns" -ForegroundColor Red }
  else { "{0,-26} {1} process(es)" -f $ns, $c }
}
```

(`foreach`, not `ForEach-Object`, and `$ns` captured explicitly: inside a nested `Where-Object`
scriptblock `$_` is the **inner** pipeline element — the process — not the namespace. That is a
silent wrong answer, not an error.)

**Do not treat the count itself as a gate.** The 2026-07-26 host snapshot shows **two** `python.exe`
per namespace, in a parent/child chain with identical command lines — but the supervisor launches
each book once, through `powershell.exe`, and nothing in `run_book.py` forks. The mechanism is
unexplained (most likely a venv launcher that re-execs), so the number is an observation, not a
contract. What matters operationally is only this: **§7 must stop every one of them**, and it counts
to zero rather than assuming how many there were.

Derive the interpreter and the root from those command lines:

```powershell
$exes = @($books | ForEach-Object {
    if ($_.CommandLine -match '^"([^"]+python\.exe)"') { $matches[1] }
} | Sort-Object -Unique)
$exes
if ($exes.Count -ne 1) { throw "STOP: derived $($exes.Count) interpreters from the running books; expected exactly 1" }
$py   = $exes[0]
$repo = Split-Path (Split-Path (Split-Path $py -Parent) -Parent) -Parent
if (-not (Test-Path (Join-Path $repo "run_book.py"))) { throw "STOP: '$repo' is not the book repo root" }
"interpreter : $py"
"repo root   : $repo"
& $py -c "import sys; print(sys.version)"
```

**Expected:** `...\ai-trading-agent\.venv-gtos\Scripts\python.exe`, repo root
`C:\Users\MSI\Documents\ai-trading-agent`, Python **3.13.x**.

**STOP if** `$exes.Count -ne 1`, or the repo root is not the tree you copied the carry into, or
the version starts `3.11` (that is PATH python, not the books').

Confirm the carry landed in *that* tree:

```powershell
$carry = Join-Path $repo "docs\audits\fable5-vision-audit-20260725\phase5\activation_carry"
Test-Path (Join-Path $carry "MANIFEST.json")
Test-Path (Join-Path $repo "docs\audits\fable5-vision-audit-20260725\phase4\packet_carry\MANIFEST.json")
```

Both must print `True`. If the second is `False`, Session S's carry is not here and this
runbook's stage C cannot be verified — STOP and fetch it.

---

## 2. Preflight — is this host what the carry was authored against?

```powershell
Set-Location $repo
& $py (Join-Path $carry "verify_carry.py") --check preflight
"exit code: $LASTEXITCODE"
```

Every line must read `ALREADY CARRIED`, `AT EXPECTED BASE`, or `ABSENT (expected — new file)`,
and the exit code must be **0**.

**STOP on exit code 2.** `*** UNEXPECTED CONTENT ***` means the host has moved since the carry
was derived. Send the printed sha256 values back; do not copy anything.

**Exit code 3 is not a carry failure.** It means the verifier refused to answer: wrong interpreter
(it checks `sys.prefix` against `<repo>\.venv-gtos`) or it is not sitting inside the book's repo
tree. It prints which, and the command to re-run. Fix that and try again.

---

## 3. Back up every destination

Rollback restores from this. Take it before touching anything.

```powershell
$stamp  = Get-Date -Format "yyyyMMdd-HHmmss"
$backup = Join-Path $repo ("_carry_backup_AC_" + $stamp)
New-Item -ItemType Directory -Force -Path $backup | Out-Null

$targets = @(
  "src\utils\broker_clock.py",
  "src\components\ultimate_book\governor_state.py",
  "src\components\ultimate_book\book_engine.py",
  "src\components\execution.py",
  "src\components\ultimate_book\runtime_learning_packet.py",
  "src\components\ultimate_book\packet_economics.py",
  "src\components\ultimate_book\packet_guard.py",
  "src\components\ultimate_book\book_owner.py",
  "scripts\ultimate_book_packet_silence_alarm.py",
  ".tools\monitor_books.py"
)
foreach ($t in $targets) {
  $src = Join-Path $repo $t
  if (Test-Path $src) {
    $dst = Join-Path $backup $t
    New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
    Copy-Item -LiteralPath $src -Destination $dst -Force
    "backed up : $t"
  } else {
    "absent    : $t   (new file; rollback will DELETE it)"
  }
}

# The manifest is what makes the rollback gate correct. `--check rollback` compares against the
# state the host was ACTUALLY on -- which is NOT the same as the lineage base if this host already
# has Session S's packet carry applied. Without this file the gate falls back to the lineage and
# will fail a correct rollback.
$records = @()
foreach ($t in $targets) {
  $src = Join-Path $repo $t
  if (Test-Path $src) {
    $records += @{ repo_path = ($t -replace '\\','/'); sha256 = (Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash.ToLower() }
  } else {
    $records += @{ repo_path = ($t -replace '\\','/'); sha256 = $null }
  }
}
@{ schema = "gtos.phase5.activation_carry_backup.v1"; taken_utc = (Get-Date).ToUniversalTime().ToString("o");
   repo = $repo; files = $records } | ConvertTo-Json -Depth 5 |
  Set-Content -Path (Join-Path $backup "BACKUP_MANIFEST.json") -Encoding utf8
"backup at: $backup"
Test-Path (Join-Path $backup "BACKUP_MANIFEST.json")
```

The last command must print `True`. **Write `$backup` down.** Section 9 needs it — and §9 derives
everything else from it, so it is the one thing you must not lose.

---

## 4. Pause new entries — the brake

The kill flag pauses **placement only**. Both books keep running and keep managing open
positions (`launcher.py:204-211`), and the supervisor does not restart anything, because
nothing is missing. This is the reversible brake; `Stop-Process` in §7 is not.

```powershell
New-Item -ItemType Directory -Force -Path (Join-Path $repo "pipeline_state") | Out-Null
Set-Content -Path (Join-Path $repo "pipeline_state\ULTIMATE_BOOK_KILL_ftmo.flag") `
            -Value ("AC carry {0}" -f $stamp) -Encoding ascii
Set-Content -Path (Join-Path $repo "pipeline_state\ULTIMATE_BOOK_KILL_fn.flag") `
            -Value ("AC carry {0}" -f $stamp) -Encoding ascii
Get-ChildItem (Join-Path $repo "pipeline_state\ULTIMATE_BOOK_KILL_*.flag") | Select-Object Name, Length
```

Both flags must exist. Now **prove both books have seen them**, which is not the same as
believing they have.

> Do **not** look for `PLACEMENT PAUSED` in the console log. That string goes to `notify_alert`
> (`launcher.py:183-199`), a push channel — not to `run_book_console.log`. And a healthy H4 book
> legitimately writes nothing to any log for hours. Both are false-negative traps.
>
> The signal that exists for exactly this is the per-namespace **heartbeat**, written at the top of
> every tick before any broker call (`launcher.py:120-140`). `killed()` is re-evaluated on the same
> tick (`:204-208`), so **a heartbeat stamped after the flag was created proves that book has
> evaluated the flag.**

```powershell
$flagPath = Join-Path $repo "pipeline_state\ULTIMATE_BOOK_KILL_ftmo.flag"
if (-not (Test-Path $flagPath)) { Write-Host "STOP: the kill flag is not there - go back to the block above" -ForegroundColor Red }
$flagTime = (Get-Item $flagPath).LastWriteTimeUtc
Start-Sleep -Seconds 150
foreach ($ns in @("operator_profile","redacted_account_live_bee34003")) {
  $path = Join-Path $repo ("pipeline_state\ultimate_book\{0}\heartbeat.json" -f $ns)
  if (-not (Test-Path $path)) { Write-Host "STOP: no heartbeat for $ns" -ForegroundColor Red; continue }
  $hb  = Get-Content $path -Raw | ConvertFrom-Json
  $ts  = [datetimeoffset]::Parse([string]$hb.ts).UtcDateTime
  $age = ((Get-Date).ToUniversalTime() - $ts).TotalSeconds
  $seen = $ts -gt $flagTime
  "{0,-26} pid={1,-6} healthy={2,-5} age={3,5:n0}s  saw_the_flag={4}" -f $ns, $hb.pid, $hb.healthy, $age, $seen
  if ($age -gt 180) { Write-Host "STOP: $ns heartbeat is stale ($([int]$age)s)" -ForegroundColor Red }
  if (-not $seen)   { Write-Host "STOP: $ns has not ticked since the flag was created" -ForegroundColor Red }
}
```

Both namespaces must print `saw_the_flag=True` and an age under ~120 s. **STOP otherwise** — the
book you are about to swap code under is not ticking, and that is a different problem from this one.

The console logs are still worth a glance for errors, but they are not the gate:

```powershell
Get-Content (Join-Path $repo "shadow_logs\run_book_console.log") -Tail 20
Get-Content (Join-Path $repo "shadow_logs\run_book_fn_console.log") -Tail 20
```

---

## 5. Copy the files, in this order

Order matters and the reason is measured: **36 of 64 partial states die before the first tick.**
See `ORDERING_AND_PARTIAL_STATES.md` §2. Copy top to bottom and do not reorder.

```powershell
$acFiles = Join-Path $carry "files"
$sFiles  = Join-Path $repo "docs\audits\fable5-vision-audit-20260725\phase4\packet_carry\files"

$plan = @(
  @{ n=1;  stage="A1"; from=(Join-Path $acFiles "broker_clock.py");                   to="src\utils\broker_clock.py";                                    sha="78549c4d2b17b3d0078f918459c706b79de2eb8324cb92a2945725d6a1c2af8a" },
  @{ n=2;  stage="A2"; from=(Join-Path $acFiles "governor_state.py");                 to="src\components\ultimate_book\governor_state.py";               sha="53b745ed9aba5bc214e47410d3999b2f44df389c9abedcd53f47f2f1605c7db0" },
  @{ n=3;  stage="A3"; from=(Join-Path $acFiles "book_engine.py");                    to="src\components\ultimate_book\book_engine.py";                  sha="b6a9ef7d98d20629260c3aaf8db9bbbba72dae36ec70ad5088c9b3482cd7b68a" },
  @{ n=4;  stage="B";  from=(Join-Path $acFiles "execution.py");                      to="src\components\execution.py";                                  sha="d0d367877dfb6cde52f886a93623238dfaa788e5d7f14b8e19451e3c62938445" },
  @{ n=5;  stage="C1"; from=(Join-Path $sFiles  "runtime_learning_packet.py");        to="src\components\ultimate_book\runtime_learning_packet.py";      sha="1941472b4eac6e0b88f25e60d7a90c455c7e1999e94ef4a600fb3d949f3e025b" },
  @{ n=6;  stage="C2"; from=(Join-Path $sFiles  "packet_economics.py");               to="src\components\ultimate_book\packet_economics.py";             sha="cc8353ec4a124ca4435bf39e130832cdfea3bea2062aca29bbc03bbd3937fe8b" },
  @{ n=7;  stage="C3"; from=(Join-Path $sFiles  "packet_guard.py");                   to="src\components\ultimate_book\packet_guard.py";                 sha="4c9983f690ca1e5f61e3f80f4a9b5067de088485b6bbf310e2eb57cfe6964b9b" },
  @{ n=8;  stage="C4"; from=(Join-Path $sFiles  "ultimate_book_packet_silence_alarm.py"); to="scripts\ultimate_book_packet_silence_alarm.py";            sha="75580e35376bd7e25d293ca4a45257e6ae7bf45815f44bf150470df2f51d921c" },
  @{ n=9;  stage="C5"; from=(Join-Path $sFiles  "book_owner.py");                     to="src\components\ultimate_book\book_owner.py";                   sha="2b9aab7b0ff652647fd5cd304559ca20f900cd2e7b4c480e2c07cd557acf87e2" }
)

foreach ($p in $plan) {
  if (-not (Test-Path $p.from)) { Write-Host "STOP: source missing $($p.from)" -ForegroundColor Red; break }
  $dst = Join-Path $repo $p.to
  New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
  Copy-Item -LiteralPath $p.from -Destination $dst -Force
  $got = (Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash
  if ($got -eq $p.sha) {
    "{0}  {1,-3}  {2}" -f "ok  ", $p.stage, $p.to
  } else {
    Write-Host ("STOP at {0}: {1}`n  got      {2}`n  expected {3}" -f $p.stage, $p.to, $got, $p.sha) -ForegroundColor Red
    break
  }
}
```

**The `sha` values above are a convenience check only — `verify_carry.py --check postflight` in
§6 is the authority, and it reads them from `MANIFEST.json`.** If a line here disagrees with
the manifest, believe the manifest and report the discrepancy.

**If the loop stops partway**, you are in a partial state. Read
`ORDERING_AND_PARTIAL_STATES.md` §5: stopping after any completed line is safe *because the
books have not been restarted yet* — they are still running the old code from memory. Do not
restart anything. Either finish the copy or roll back (§9).

---

## 6. Verify on disk, before restarting anything

```powershell
& $py (Join-Path $carry "verify_carry.py") --check postflight
"postflight exit: $LASTEXITCODE"
& $py (Join-Path $carry "verify_carry.py") --check imports
"imports exit: $LASTEXITCODE"
& $py (Join-Path $carry "verify_carry.py") --check behaviour
"behaviour exit: $LASTEXITCODE"
```

**All three must exit 0.** (`--check all` runs the same three in one go; an exit of **3** is a
refusal, not a failure — wrong interpreter, or not run from inside the book's repo tree.)

* `postflight` — every byte where it should be, and the **three** dependency invariants hold.
  **This is the gate that does the work**, because it compares bytes: a truncated copy imports,
  constructs and ticks while the governor silently returns `None`, and only the sha sees it. Stage
  D is deliberately not applied yet and is reported, not counted.
* `imports` — every module `run_book.py` imports at module top, then its first construction.
  If this exits 2, the restart in §7 would be a ~33-second crash loop on both namespaces. **STOP
  and roll back.** It is **necessary and not sufficient**: 39 measured truncation states pass it.
* `behaviour` — 17,000 broker-valid volumes round-trip with none stranded and none rounded up;
  the FTMO reset window lands on 00:00 CE(S)T and the redacted_account one stays at server midnight,
  including inside a calendar-mismatch window.

**If `postflight` fails but `imports` exits 0, read which lines failed before deciding.**

| what failed | what it means | what to do |
|---|---|---|
| only `[S/C]` lines, all at their base sha | §5 stopped before stage C (usually `$sFiles` absent). **This is a safe, complete AC-only state** — `imports` exiting 0 proves it | fetch Session S's `packet_carry/files/`, re-run §5, do **not** roll back |
| any `[AC/…]` line | the AC carry is incomplete or a file is truncated | roll back (§9) |
| a sha that is neither base nor carried | a partial write, or the wrong file | roll back (§9) |
| an invariant line | the copy order was not followed | roll back (§9) |

A truncated file is the case the byte comparison exists for: a partial copy can import, construct
and tick while the governor silently returns `None`, so **`imports` alone is necessary and not
sufficient.** Measured: 39 truncation states pass `imports` and are unsafe; all of them fail
`postflight`.

Still nothing has changed for the running books: they hold the old code in memory.

---

## 7. The restart — the one-way door

### 7.1 First: is the supervisor alive?

**Nothing else in this procedure brings the books back.** `Stop-Process` below is unconditional,
and if the supervisor is gone the books simply stay down. It has three `exit` paths before its loop
and its own header says it can hang.

```powershell
$sup = @(Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue |
         Where-Object { $_.CommandLine -match '(?i)-File\s+"?[^"]*run_book_supervisor\.ps1"?' })
"supervisor processes: {0}" -f $sup.Count
$hbFile = Join-Path $repo "pipeline_state\supervisor_heartbeat.json"
if (Test-Path $hbFile) {
  $shb = Get-Content $hbFile -Raw | ConvertFrom-Json
  $sage = ((Get-Date).ToUniversalTime() - [datetimeoffset]::Parse([string]$shb.ts).UtcDateTime).TotalSeconds
  "supervisor heartbeat: pid={0} age={1:n0}s" -f $shb.pid, $sage
  if ($sage -gt 120) { Write-Host "STOP: supervisor heartbeat is stale ($([int]$sage)s) - it is hung or gone" -ForegroundColor Red }
} else {
  Write-Host "STOP: no supervisor heartbeat file - do not stop the books" -ForegroundColor Red
}
if ($sup.Count -eq 0) { Write-Host "STOP: no supervisor process - nothing would restart the books" -ForegroundColor Red }
```

**Both must be satisfied: at least one supervisor process, heartbeat under ~120 s.** If not, STOP
and get the supervisor healthy first. The scheduled task re-fires it every 5 minutes, so waiting is
usually enough — but 5 minutes is longer than the 3-minute rollback trigger in §7.3, so do not
confuse "the supervisor has not fired yet" with "the books cannot start".

### 7.2 Stop every book process

Stopping one of a pair leaves the other alive; the supervisor then sees a book running, does not
restart it, and you get a green light on **old code**. So this counts to zero rather than assuming
how many there were.

```powershell
# CAPTURE FIRST, and do not overwrite it. Section 8 compares against this list; re-running the
# loop below would re-capture only the SURVIVORS and section 8 would then pass on pids it never saw.
$oldPids = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
             Where-Object { $_.CommandLine -like "*run_book.py*" } |
             ForEach-Object { [int]$_.ProcessId })
"pre-restart pids: {0}" -f ($oldPids -join ", ")

for ($i = 1; $i -le 5; $i++) {
  $live = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -like "*run_book.py*" })
  if ($live.Count -eq 0) { break }
  "pass {0}: stopping {1} process(es)" -f $i, $live.Count
  foreach ($b in $live) { Stop-Process -Id $b.ProcessId -Force -ErrorAction SilentlyContinue }
  Start-Sleep -Seconds 4
}
$remaining = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
               Where-Object { $_.CommandLine -like "*run_book.py*" })
"remaining: {0}" -f $remaining.Count
if ($remaining.Count -gt 0) { Write-Host "STOP: books still running after 5 passes" -ForegroundColor Red }
```

`remaining` must be `0`.

### 7.3 Wait for the supervisor to bring them back

Its loop is `Start-Sleep -Seconds 30` plus the work, so a healthy pass is **~35–40 s**.

```powershell
Start-Sleep -Seconds 120
$now = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
         Where-Object { $_.CommandLine -like "*run_book.py*" })
$now | Select-Object ProcessId, CreationDate, CommandLine | Format-List
@("operator_profile","redacted_account_live_bee34003") | ForEach-Object {
  $ns = $_
  $c = @($now | Where-Object { $_.CommandLine -like "*--namespace $ns*" }).Count
  "{0,-26} {1} process(es)" -f $ns, $c
  if ($c -eq 0) { Write-Host "  ^ no process for $ns" -ForegroundColor Yellow }
}
$reused = @($now | Where-Object { $oldPids -contains [int]$_.ProcessId })
if ($reused.Count -gt 0) {
  Write-Host "CHECK: a pre-restart pid is present again. Windows recycles pids, so confirm CreationDate is AFTER you ran 7.2 before treating this as a failure." -ForegroundColor Yellow
}
```

Both namespaces must show at least one process. §8 is what proves they are the *new* ones.

**If a namespace shows 0 after 3 minutes**, read the logs before deciding:

```powershell
Get-Content (Join-Path $repo "shadow_logs\run_book_console.log.err") -Tail 40
Get-Content (Join-Path $repo "shadow_logs\run_book_fn_console.log.err") -Tail 40
Get-Content (Join-Path $repo "shadow_logs\book_supervisor.log") -Tail 40
```

* Repeated `(re)starting book ns=...` lines ~33 s apart in `book_supervisor.log`, with a traceback
  in the `.err` file — **that is the crash loop. Roll back (§9).**
* `book_supervisor.log` not moving at all — the **supervisor** is down, not the books. Re-check 7.1
  and wait for the 5-minute scheduled task. Rolling back will not bring the books back either.

---

## 8. Confirm health, then release the brake

```powershell
Start-Sleep -Seconds 150
foreach ($ns in @("operator_profile","redacted_account_live_bee34003")) {
  $path = Join-Path $repo ("pipeline_state\ultimate_book\{0}\heartbeat.json" -f $ns)
  if (-not (Test-Path $path)) { Write-Host "STOP: no heartbeat for $ns" -ForegroundColor Red; continue }
  $hb  = Get-Content $path -Raw | ConvertFrom-Json
  $ts  = [datetimeoffset]::Parse([string]$hb.ts).UtcDateTime
  $age = ((Get-Date).ToUniversalTime() - $ts).TotalSeconds
  if ($null -eq $oldPids -or @($oldPids).Count -eq 0) {
    Write-Host "STOP: `$oldPids is empty -- you are in a different shell from section 7. Re-run section 7's first block to capture the pids, or compare the heartbeat ts against the time you stopped the books, by hand." -ForegroundColor Red
    continue
  }
  $isNew = -not ($oldPids -contains [int]$hb.pid)
  "{0,-26} pid={1,-6} healthy={2,-5} age={3,5:n0}s  new_pid={4}" -f $ns, $hb.pid, $hb.healthy, $age, $isNew
  if ($age -gt 180)  { Write-Host "STOP: $ns heartbeat is stale" -ForegroundColor Red }
  if (-not $isNew)   { Write-Host "STOP: $ns heartbeat still names a pre-restart pid" -ForegroundColor Red }
  if (-not $hb.healthy) { Write-Host "WARN: $ns broker link unhealthy -- watch it, do not release the brake yet" -ForegroundColor Yellow }
}
Get-Content (Join-Path $repo "shadow_logs\run_book_console.log") -Tail 30
Get-Content (Join-Path $repo "shadow_logs\run_book_fn_console.log") -Tail 30
```

Then confirm the positions are the ones you started with. The books cannot have opened one — the
kill flags are still in place — so **any change is a close, and a close during the restart window
was the broker's stop, not the book's exit policy.** Read the count off each terminal, or off the
newest `positions` line in the console logs, and compare it with what you recorded in §0. A
difference is not a reason to roll back, but it **is** a reason to tell the owner before releasing
the brake.

Both heartbeats must be fresh — a healthy book stamps one every ~60 s, and the block STOPs above
180 s — must name a **new** pid, and `healthy` must be `True`.
`$oldPids` is set in §7. In a fresh shell it is empty — and an empty `$oldPids` makes
`-contains` return `$false`, which would print `new_pid=True` for a book still running **old code**.
The block above STOPs on that instead of passing it. Then:

```powershell
Remove-Item (Join-Path $repo "pipeline_state\ULTIMATE_BOOK_KILL_ftmo.flag") -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $repo "pipeline_state\ULTIMATE_BOOK_KILL_fn.flag")   -Force -ErrorAction SilentlyContinue
Get-ChildItem (Join-Path $repo "pipeline_state\ULTIMATE_BOOK_KILL_*.flag") -ErrorAction SilentlyContinue
```

The last command must print nothing. **The books are now on the carried code and placing.**

---

## 9. Rollback

Use this at any STOP after §5.

**Two refuters broke the first version of this section, and both breaks were of the same shape: a
`Write-Host "STOP"` that does not stop, and a variable whose emptiness reads as success.** The block
below is one scriptblock with `$ErrorActionPreference = "Stop"`, so every guard is a real `throw`;
it derives everything from `$backup`; and it will not delete anything if the backup is unusable —
because deleting the four new files while leaving the modified ones carried produces exactly the
`ModuleNotFoundError` crash loop this whole package is ordered to avoid.

**Edit one line, then paste the whole block.**

```powershell
& {
  $ErrorActionPreference = "Stop"

  # ---- EDIT THIS ONE LINE (the path section 3 printed) --------------------------------------
  $backup = "C:\Users\MSI\Documents\ai-trading-agent\_carry_backup_AC_YYYYMMDD-HHMMSS"
  # ------------------------------------------------------------------------------------------

  $manPath = Join-Path $backup "BACKUP_MANIFEST.json"
  if (-not (Test-Path $manPath)) {
    throw "STOP: no BACKUP_MANIFEST.json under '$backup'. WITHOUT IT THIS BLOCK WOULD DELETE FILES AND RESTORE NONE. Find the backup directory (it is named _carry_backup_AC_* inside the repo) before continuing."
  }
  $man = Get-Content $manPath -Raw | ConvertFrom-Json
  $global:repo = [string]$man.repo
  if (-not (Test-Path (Join-Path $global:repo "run_book.py"))) { throw "STOP: '$($global:repo)' is not the book repo root" }
  $global:py = Join-Path $global:repo ".venv-gtos\Scripts\python.exe"
  if (-not (Test-Path $global:py)) { throw "STOP: no interpreter at $($global:py)" }
  $global:carry = Join-Path $global:repo "docs\audits\fable5-vision-audit-20260725\phase5\activation_carry"
  if (-not (Test-Path (Join-Path $global:carry "verify_carry.py"))) { throw "STOP: no verify_carry.py under $($global:carry)" }
  "repo   : $($global:repo)"
  "backup : $backup  ($($man.files.Count) paths, taken $($man.taken_utc))"

  # Stop the books AND the monitor daemon. The monitor is not a book, and the carried one imports
  # broker_clock at module top -- deleting broker_clock under a running monitor leaves it
  # crash-looping. The supervisor restarts both once the files are back.
  foreach ($pat in @("run_book.py", "monitor_books.py")) {
    for ($i = 1; $i -le 5; $i++) {
      $live = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
                Where-Object { $_.CommandLine -like "*$pat*" })
      if ($live.Count -eq 0) { break }
      "stopping {0} x {1}" -f $live.Count, $pat
      foreach ($b in $live) { Stop-Process -Id $b.ProcessId -Force -ErrorAction SilentlyContinue }
      Start-Sleep -Seconds 4
    }
  }

  # Restore from the manifest. `sha256 = null` means the file did NOT exist when the backup was
  # taken, so it must be deleted -- that is the only thing that authorises a delete.
  $failed = 0
  foreach ($f in $man.files) {
    $rel = ([string]$f.repo_path) -replace "/", "\"
    $dst = Join-Path $global:repo $rel
    $src = Join-Path $backup $rel
    if ($null -eq $f.sha256) {
      if (Test-Path $dst) { Remove-Item -LiteralPath $dst -Force; "deleted  : $rel" }
      else { "absent   : $rel" }
    } elseif (Test-Path $src) {
      New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
      Copy-Item -LiteralPath $src -Destination $dst -Force
      $now = (Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash
      if ($now -eq $f.sha256) { "restored : $rel" }
      else { $failed++; Write-Host "FAILED   : $rel (now $now, backup says $($f.sha256))" -ForegroundColor Red }
    } else {
      $failed++; Write-Host "NO BACKUP COPY: $rel -- cannot restore" -ForegroundColor Red
    }
  }
  if ($failed -gt 0) { throw "STOP: $failed path(s) did not restore. Do not proceed; report the lines above." }

  & $global:py (Join-Path $global:carry "verify_carry.py") --check rollback
  $ok = $?; $rc = $LASTEXITCODE
  if ($ok -and $rc -eq 0) { "ROLLBACK VERIFIED (exit 0)" }
  else { Write-Host "ROLLBACK NOT VERIFIED (launched=$ok exit=$rc). Do not walk away." -ForegroundColor Red }
}
```

**`ROLLBACK VERIFIED (exit 0)` is the only acceptable ending.** Anything else — including a `throw`
message — means stop and report, not retry blindly.

> Three things that line is carrying, each of which was a defect first:
>
> * `--check rollback` judges against **`BACKUP_MANIFEST.json`**, i.e. the state this host was
>   actually on. Judging against the lineage failed a *correct* rollback on any host that already
>   had Session S's carry, and then told the operator to delete four files.
> * `$ok = $?` as well as `$LASTEXITCODE`. If `&` fails to launch anything, `$LASTEXITCODE` keeps
>   its previous value — which, in a shell reused from §6, is `0`. The first draft printed
>   "rollback exit: 0" for a block that had done nothing.
> * The delete arm is authorised by the **backup's own record** that the file was absent, not by a
>   hardcoded list consulted after a lookup miss. With a bad `$backup` the two were
>   indistinguishable, and the first draft deleted `broker_clock.py` while leaving
>   `governor_state.py` carried.
>
> Do **not** run `--check postflight` after a rollback. It will fail, and it is supposed to.

Then let the supervisor bring the books and the monitor back (§7.3's wait and checks apply), confirm
§8's heartbeats, and only then remove the kill flags.

---

## 10. Stage D — the monitor. Separate, and after the books are healthy

`.tools\monitor_books.py` carries the same B56 defect in the alerting layer, and a
`SRV_OFFSET_H = 3` constant that becomes wrong on **2026-11-01** when both servers drop to +2.
It is ordered last and gated separately because **no book imports it**, so it cannot affect a
book restart, and the supervisor restarts it on its own.

**It has its own dependency, and it is fatal:** the carried monitor imports
`src.utils.broker_clock` at module top, **unguarded**. Stage D without stage A1 is a permanent
crash loop of the alerting layer — the third of this carry's three invariants. `--check stage-d`
asserts it.

Do this only once §8 is clean.

```powershell
$acFiles = Join-Path $carry "files"
$stageD = @{ n=10; stage="D"; from=(Join-Path $acFiles "monitor_books.py"); to=".tools\monitor_books.py"; sha="91577c1f34656fdfd746ef067636c4fafd32c9d376fa791f13fe280629b025d3" }
$dst = Join-Path $repo $stageD.to
Copy-Item -LiteralPath $stageD.from -Destination $dst -Force
$got = (Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash
if ($got -eq $stageD.sha) { "ok   $($stageD.to)" } else { Write-Host "STOP: got $got expected $($stageD.sha)" -ForegroundColor Red }
& $py (Join-Path $carry "verify_carry.py") --check stage-d
$ok = $?; $rc = $LASTEXITCODE
"stage-d: launched=$ok exit=$rc"
```

**`--check stage-d`, not `--check behaviour`.** `behaviour` deliberately *skips* stage D when it is
absent — right at §6, and useless here, because it exits 0 whether or not the monitor landed.
`stage-d` fails unless the monitor is at the carried sha **and** `broker_clock.py` is there **and**
the window it computes agrees with the governor's. Exit must be `0`.

(The `-eq` comparison above is case-insensitive, which matters: `Get-FileHash` returns the hash
UPPERCASE and the manifest records it lowercase.)

Then cycle the monitor:

```powershell
$monOld = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -like "*monitor_books.py*" } | ForEach-Object { [int]$_.ProcessId })
"stopping monitor pids: {0}" -f ($monOld -join ", ")
foreach ($m in $monOld) { Stop-Process -Id $m -Force -ErrorAction SilentlyContinue }

# 150 s, not 60: the supervisor's loop is Start-Sleep 30 PLUS four Test-*Running passes, and its
# own header measures a healthy loop at ~35-40 s.
Start-Sleep -Seconds 150
$mon2 = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
          Where-Object { $_.CommandLine -like "*monitor_books.py*" })
"monitor back up: {0}" -f $mon2.Count
if ($mon2.Count -eq 0) { Write-Host "the monitor has not returned yet - wait one more supervisor pass before acting" -ForegroundColor Yellow }
Get-Content (Join-Path $repo "shadow_logs\monitor_daemon.log") -Tail 20
Get-Content (Join-Path $repo "shadow_logs\monitor_daemon.err") -Tail 20
```

`monitor back up` must reach at least 1 and `monitor_daemon.log` must show a fresh account line for
both accounts. A traceback in `monitor_daemon.err` naming `broker_clock` means stage A1 is not in
place — re-run §6's `postflight`.

If it does not come back, restore `.tools\monitor_books.py` from `$backup` — **the books are
unaffected either way**, which is the whole reason this is a separate stage.

---

## 11. What this runbook does not do

* It does not arm anything. `ultimate_book_live_activation_allowed` and
  `ultimate_book_live_broker_authority` are untouched and must remain false.
* It does not mint, move or inspect an activation token.
* It does not run `mt5_preflight.py`, `fn_smoke_trade.py`, `dual_broker_execution_follower.py`,
  or any other broker-capable script.
* It does not touch `config\agent_config.yaml` or either FTMO profile. **The B56 change needs no
  config edit** — the rule is already in the profile the host ships
  (`config\profiles\operator_profile.yaml:87`), which matters because both FTMO profiles
  are decision-contract-bound.
* It does not restart the supervisor, the AI companion, or the advisory refresher.
