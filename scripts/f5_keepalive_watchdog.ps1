# f5_keepalive_watchdog.ps1 — F5 pair keep-alive: check by pinned argv, relaunch via the
# EXISTING launch mechanism only, append-only flap log, deduped alerts. STAGED — this file
# deploys nothing, registers nothing, and is inert on any host without the pin file.
#
# WHY (2026-08-17, REVIEW-20260817 §B defect 2): the operator pair died
# 07:10:20Z -> 12:16:52Z (5 h 04 m unwatched, second flap — Sunday board 12836 -> 12444;
# first flap was the pair task's own 72 h ExecutionTimeLimit killing it 2026-08-15 12:30,
# docs/audits/fable-20260816/SLEEVES.md:40). Liveness was hand-tended; this watchdog is the
# owed supervised keep-alive with flap logging.
#
# WHAT IT DOES, exactly, once per invocation (fire it from its own scheduled task):
#   1. Reads the pinned argv signature (pipeline_state\f5_keepalive_expected_argv.json,
#      captured from the LIVE worker at the carry ceremony — see DEPLOY-NOTE). No pin file
#      -> logs `not_armed` and exits. The watchdog NEVER composes an argv itself.
#   2. Finds python.exe processes whose CommandLine matches run_book.py + the exact
#      `--namespace operator` token (word-bounded — a sibling namespace never matches).
#   3. Worker present  -> verifies every pinned token appears in the live CommandLine
#      (argv_drift alert if not), flags forbidden tokens, reports heartbeat age and parent
#      pid. Two+ workers -> double_book CRITICAL alert. NEVER stops or kills anything.
#   4. Worker absent   -> if the F5 kill flag exists, the down is INTENTIONAL: no relaunch.
#      Otherwise: flap. Relaunches ONLY via `Start-ScheduledTask <pair task>` — the existing
#      mechanism, which reproduces the same argv by construction — then re-checks and logs
#      relaunch_verified / relaunch_argv_mismatch / relaunch_failed. Storm guard: at most
#      3 relaunch attempts per rolling 60 min, then backoff + alert.
#   5. Appends exactly ONE JSON line per invocation to shadow_logs\f5_keepalive_flaps.jsonl
#      (append-only). Alerts are deduped per alert-key over $AlertDedupMinutes via
#      pipeline_state\f5_keepalive_state.json; the newest alert is mirrored to
#      shadow_logs\f5_keepalive_LATEST-ALERT.txt for the boards.
#
# WHAT IT WILL NEVER DO: stop/kill/restart a live process; start redacted_account_f5_minimal
# (down by decision — JUDGMENT-LOCK.md §5); touch a production namespace; invent or edit
# argv; run a relaunch when the kill flag is present; do anything without the pin file.
#
# PRIOR ART (checked before building, per house rule): scripts/run_book_supervisor.ps1 —
# start-only principle, CIM CommandLine matching, and the hung-incumbent heartbeat lesson
# are reused from it; it is NOT the F5 starter (its F5 row lacks the live worker's
# --risk-unit-floor-mode shadow / --event-clock-shadow flags, and the host warns against
# wholesale carry). scripts/watchdog.ps1 is the LEGACY run_agent-lineage watchdog and was
# deliberately not reused: it kills processes on a trading-hours schedule — the exact
# opposite of the never-stop contract this book needs.
#
# =============================== DEPLOY-NOTE (carry ceremony) ===============================
# STAGED ONLY. Nothing below runs until an operator executes it ON the VPS F5 tree
# (host-local\redacted_host\repo). Do not run against the production tree.
#
#  0. Preconditions: pair healthy (heartbeat fresh), you know the pair's real starter task
#     name (2026-08-17 observation: `GTOS_F5_FTMO`, Ready, last run 00:27Z — VERIFY it is
#     still the mechanism and that its ACTION starts the CURRENT contract; the task's last
#     result 1073807364 predates the running pair, so confirm before trusting it).
#
#  1. PIN THE ARGV from the running worker (while healthy). From the F5 repo root:
#        $cl = (Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
#               Where-Object { $_.CommandLine -match 'run_book\.py' -and
#                              $_.CommandLine -match '--namespace\s+operator(\s|$)'
#              }).CommandLine
#        # Split into tokens, keep everything from run_book.py onward, store as required[]:
#        @{ namespace = "operator";
#           required  = @($cl -split '\s+' | Where-Object { $_ });
#           forbidden = @("--frontier-exits", "--spread-geometry-floor") } |
#          ConvertTo-Json | Set-Content pipeline_state\f5_keepalive_expected_argv.json -Encoding utf8
#     Then HAND-REVIEW the file: required[] must contain the six contract facts the lanes
#     verified live — --namespace operator, --f5-minimal-size-usd 10,
#     --f5-notional-initial-usd 100000, --frozen-intent-reprice, --poll-seconds 60,
#     --risk-unit-floor-mode shadow (+ --event-clock-shadow and the 32-name --tags value).
#     Trim machine-local noise (full python.exe path) if present; keep run_book.py onward.
#
#  2. VERIFY THE PAIR TASK reproduces that argv:
#        (Get-ScheduledTask -TaskName GTOS_F5_FTMO).Actions | Format-List
#     If the action's command line does not produce the pinned argv (stale contract), FIX
#     THE TASK FIRST — the watchdog will relaunch through it verbatim and will only be able
#     to tell you afterwards (relaunch_argv_mismatch) that the wrong contract came up.
#
#  3. REMOVE THE 72h CAP on the pair task (first flap's cause):
#        Set-ScheduledTask -TaskName GTOS_F5_FTMO -Settings `
#          (New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) `
#             -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries)
#
#  4. DRY-RUN the watchdog once by hand and read the JSONL row it appends:
#        powershell -ExecutionPolicy Bypass -File scripts\f5_keepalive_watchdog.ps1 -DryRun
#
#  5. REGISTER the watchdog's own task (5-min cadence; single instance; no time limit):
#        $act = New-ScheduledTaskAction -Execute "powershell.exe" -Argument `
#          "-NoProfile -ExecutionPolicy Bypass -File host-local\redacted_host\repo\scripts\f5_keepalive_watchdog.ps1"
#        $trg = New-ScheduledTaskTrigger -Once -At (Get-Date) `
#                 -RepetitionInterval (New-TimeSpan -Minutes 5)
#        $set = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 4) `
#                 -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
#        Register-ScheduledTask -TaskName GTOS_F5_KEEPALIVE -Action $act -Trigger $trg `
#          -Settings $set -Description "F5 pair keep-alive (start-only, argv-pinned)"
#
#  6. ROLLBACK: Unregister-ScheduledTask GTOS_F5_KEEPALIVE; delete the pin file. The script
#     is then inert even if fired by hand.
# ============================================================================================

[CmdletBinding()]
param(
    # Report-only: never triggers the pair task, still logs the full check row.
    [switch]$DryRun,
    # The F5 repo root. Default = parent of this script's directory (repo\scripts\..).
    # $PSScriptRoot is EMPTY when Task Scheduler invokes via some -File/-Command contexts
    # (measured live 2026-08-18: every 5-min run exited 1 at this param default). Fall back
    # through the invocation path, then the canonical host repo root.
    [string]$F5Repo = $(
        if ($PSScriptRoot) { Split-Path -Parent $PSScriptRoot }
        elseif ($MyInvocation.MyCommand.Path) { Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path) }
        else { "host-local\redacted_host\repo" }
    ),
    # The ONE namespace this watchdog owns. redacted_account_f5_minimal stays down by decision;
    # never point this at a production namespace.
    [string]$Namespace = "operator",
    # The EXISTING pair starter task (the launch mechanism; the watchdog composes no argv).
    [string]$TaskName = "GTOS_F5_FTMO",
    [int]$AlertDedupMinutes = 60,
    [int]$VerifySeconds = 90,
    [int]$MaxRelaunchesPerHour = 3,
    [int]$HeartbeatStaleSeconds = 900
)

$ErrorActionPreference = "Continue"
$VERSION  = "f5_keepalive_watchdog_v1"
$PinFile  = Join-Path $F5Repo "pipeline_state\f5_keepalive_expected_argv.json"
$StateFile= Join-Path $F5Repo "pipeline_state\f5_keepalive_state.json"
$FlapLog  = Join-Path $F5Repo "shadow_logs\f5_keepalive_flaps.jsonl"
$AlertTxt = Join-Path $F5Repo "shadow_logs\f5_keepalive_LATEST-ALERT.txt"
$KillFlag = Join-Path $F5Repo "pipeline_state\ULTIMATE_BOOK_KILL_ftmo_f5.flag"
$HbFile   = Join-Path $F5Repo ("pipeline_state\ultimate_book\{0}\heartbeat.json" -f $Namespace)

function Now-Utc { (Get-Date).ToUniversalTime() }
function Iso([datetime]$d) { $d.ToString("yyyy-MM-ddTHH:mm:ss.fffZ") }

# --- single-instance mutex: overlapping fires must not double-trigger the pair task ---
$mutex = New-Object System.Threading.Mutex($false, "Global\gtos_f5_keepalive_watchdog")
if (-not $mutex.WaitOne(0)) { exit 0 }

function Test-FtmoLaunchPause([string]$Namespace) {
  # ARRANGED_LAUNCH_PAUSE_SEAM_V1: future launches only. Not ULTIMATE_BOOK_KILL_ftmo_f5.flag.
  $path = Join-Path $F5Repo "pipeline_state\ftmo_writer_launch_pause.json"
  if (-not (Test-Path $path)) { return $false }
  try {
    $ctl = Get-Content $path -Raw -ErrorAction Stop | ConvertFrom-Json
    foreach ($n in @($ctl.paused_namespaces)) {
      if ([string]$n -eq $Namespace) { return $true }
    }
    return $false
  } catch {
    return $false
  }
}

try {
    $row = [ordered]@{
        ts_utc   = Iso (Now-Utc)
        schema   = "gtos.f5.keepalive_check.v1"
        version  = $VERSION
        host     = $env:COMPUTERNAME
        namespace= $Namespace
        dry_run  = [bool]$DryRun
        status   = $null          # ok | not_armed | kill_flag_down | argv_drift | double_book |
                                  # flap_relaunch_verified | flap_relaunch_argv_mismatch |
                                  # flap_relaunch_failed | flap_storm_backoff | flap_dry_run
        worker_pids = @()
        parent_pid  = $null
        hb_age_s    = $null
        kill_flag   = $false
        argv_missing_tokens   = @()
        argv_forbidden_tokens = @()
        relaunch = $null
        alert    = $null
    }

    # ---- state (dedup + relaunch history); malformed state degrades to empty, never throws
    $state = @{ alerts = @{}; relaunches = @() }
    if (Test-Path $StateFile) {
        try {
            $raw = Get-Content $StateFile -Raw | ConvertFrom-Json
            if ($raw.alerts)     { $raw.alerts.PSObject.Properties | ForEach-Object { $state.alerts[$_.Name] = $_.Value } }
            if ($raw.relaunches) { $state.relaunches = @($raw.relaunches) }
        } catch {}
    }

    function Save-State {
        try {
            $dir = Split-Path $StateFile -Parent
            if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
            @{ alerts = $state.alerts; relaunches = @($state.relaunches) } |
                ConvertTo-Json -Compress -Depth 4 | Set-Content $StateFile -Encoding utf8
        } catch {}
    }

    # One alert surface, deduped by key. Never a second transport; the boards read the files.
    function Raise-Alert([string]$key, [string]$message) {
        $fired = $false
        $lastTxt = $state.alerts[$key]
        $stale = $true
        if ($lastTxt) {
            try { $stale = ((Now-Utc) - ([datetime]$lastTxt).ToUniversalTime()).TotalMinutes -ge $AlertDedupMinutes } catch {}
        }
        if ($stale) {
            $fired = $true
            $state.alerts[$key] = Iso (Now-Utc)
            try {
                Set-Content -Path $AlertTxt -Encoding utf8 -Value ("{0} [{1}] {2}" -f (Iso (Now-Utc)), $key, $message)
            } catch {}
        }
        $row.alert = [ordered]@{ key = $key; message = $message; fired = $fired; deduped = (-not $fired) }
    }

    function Write-Row {
        try {
            $dir = Split-Path $FlapLog -Parent
            if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
            Add-Content -Path $FlapLog -Encoding utf8 -Value (($row | ConvertTo-Json -Compress -Depth 6))
        } catch {}
    }

    # Word-bounded namespace token: operator must never match a longer sibling.
    $nsPattern = "--namespace\s+{0}(\s|$)" -f [regex]::Escape($Namespace)
    function Get-Workers {
        @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
          Where-Object { $_.CommandLine -and $_.CommandLine -match 'run_book\.py' -and $_.CommandLine -match $nsPattern })
    }

    $row.kill_flag = Test-Path $KillFlag
    if (Test-Path $HbFile) {
        try {
            $hb = Get-Content $HbFile -Raw | ConvertFrom-Json
            $row.hb_age_s = [math]::Round(((Now-Utc) - ([datetime]$hb.ts).ToUniversalTime()).TotalSeconds, 1)
        } catch {}
    }

    # ---- 1. pin file: without it the watchdog is INERT (staged / fail-to-inert) ----
    if (-not (Test-Path $PinFile)) {
        $row.status = "not_armed"
        Write-Row; Save-State; exit 0
    }
    $pin = $null
    try { $pin = Get-Content $PinFile -Raw | ConvertFrom-Json } catch {}
    if (-not $pin -or -not $pin.required -or (@($pin.required).Count -lt 3) -or
        ($pin.namespace -and $pin.namespace -ne $Namespace)) {
        $row.status = "not_armed"   # malformed or wrong-namespace pin = inert, never a guess
        Raise-Alert "pin_invalid" ("expected-argv pin at {0} is malformed or for another namespace" -f $PinFile)
        Write-Row; Save-State; exit 0
    }

    # ---- 2/3. presence + argv verification (never stops anything) ----
    $workers = Get-Workers
    $row.worker_pids = @($workers | ForEach-Object { [int]$_.ProcessId })
    # The healthy F5 book is a process TREE: a launcher python whose child python carries
    # the same argv (measured live 2026-08-18: 5116 <- 7172, parent starter 11208).
    # A double book = more than one ROOT (a matching python whose parent is NOT itself a
    # matching python). Counting raw matches flagged the healthy pair as double_book.
    $matchPids = @($workers | ForEach-Object { [int]$_.ProcessId })
    $roots = @($workers | Where-Object { $matchPids -notcontains [int]$_.ParentProcessId })
    $row.worker_roots = @($roots | ForEach-Object { [int]$_.ProcessId })
    if (@($workers).Count -ge 1) {
        $row.parent_pid = [int]$workers[0].ParentProcessId
        if (@($roots).Count -gt 1) {
            $row.status = "double_book"
            Raise-Alert "double_book" ("{0} worker ROOTS match ns {1}: root pids {2} (all matches {3}) - HUMAN ACTION REQUIRED; watchdog never kills" -f @($roots).Count, $Namespace, ($row.worker_roots -join ","), ($row.worker_pids -join ","))
            Write-Row; Save-State; exit 0
        }
        $cl = [string]$workers[0].CommandLine
        $missing = @()
        foreach ($tok in @($pin.required)) {
            $t = [string]$tok
            if ($t -and ($cl.IndexOf($t, [System.StringComparison]::OrdinalIgnoreCase) -lt 0)) { $missing += $t }
        }
        $present_forbidden = @()
        foreach ($tok in @($pin.forbidden)) {
            $t = [string]$tok
            if ($t -and ($cl.IndexOf($t, [System.StringComparison]::OrdinalIgnoreCase) -ge 0)) { $present_forbidden += $t }
        }
        $row.argv_missing_tokens   = $missing
        $row.argv_forbidden_tokens = $present_forbidden
        if ($missing.Count -gt 0 -or $present_forbidden.Count -gt 0) {
            $row.status = "argv_drift"
            Raise-Alert "argv_drift" ("live worker pid {0} argv drifted: missing [{1}] forbidden-present [{2}]" -f $row.worker_pids[0], ($missing -join " "), ($present_forbidden -join " "))
        } else {
            $row.status = "ok"
            if (($null -ne $row.hb_age_s) -and ($row.hb_age_s -gt $HeartbeatStaleSeconds)) {
                Raise-Alert "hb_stale" ("worker pid {0} alive but heartbeat {1}s old (> {2}s) - possible hang; watchdog takes no action" -f $row.worker_pids[0], $row.hb_age_s, $HeartbeatStaleSeconds)
            }
        }
        Write-Row; Save-State; exit 0
    }

    # ---- 4. worker ABSENT ----
    if ($row.kill_flag) {
        $row.status = "kill_flag_down"   # intentional down: a kill-flagged book must stay down
        Write-Row; Save-State; exit 0
    }

    if (Test-FtmoLaunchPause -Namespace $Namespace) {
        $row.status = "launch_paused"
        Write-Row; Save-State; exit 0
    }

    # flap. Storm guard first.
    $cutoff = (Now-Utc).AddMinutes(-60)
    $recent = @($state.relaunches | Where-Object {
        try { ([datetime]$_).ToUniversalTime() -gt $cutoff } catch { $false }
    })
    if ($recent.Count -ge $MaxRelaunchesPerHour) {
        $row.status = "flap_storm_backoff"
        Raise-Alert "flap_storm" ("pair down and {0} relaunches already attempted in 60 min - backing off; HUMAN ACTION REQUIRED" -f $recent.Count)
        Write-Row; Save-State; exit 0
    }

    if ($DryRun) {
        $row.status = "flap_dry_run"
        Raise-Alert "flap" ("pair ns {0} is DOWN (dry-run: would Start-ScheduledTask {1})" -f $Namespace, $TaskName)
        Write-Row; Save-State; exit 0
    }

    # Relaunch via the EXISTING mechanism only. No argv is composed here, ever.
    $state.relaunches = @($recent) + @(Iso (Now-Utc))
    $rel = [ordered]@{ attempted = $true; task = $TaskName; task_started = $false; verified = $false }
    try {
        Start-ScheduledTask -TaskName $TaskName -ErrorAction Stop
        $rel.task_started = $true
    } catch {
        $rel.error = [string]$_.Exception.Message
    }
    if ($rel.task_started) {
        Start-Sleep -Seconds $VerifySeconds
        $after = Get-Workers
        if (@($after).Count -ge 1) {
            $cl2 = [string]$after[0].CommandLine
            $missing2 = @()
            foreach ($tok in @($pin.required)) {
                $t = [string]$tok
                if ($t -and ($cl2.IndexOf($t, [System.StringComparison]::OrdinalIgnoreCase) -lt 0)) { $missing2 += $t }
            }
            $row.worker_pids = @($after | ForEach-Object { [int]$_.ProcessId })
            if ($missing2.Count -eq 0) {
                $rel.verified = $true
                $row.status = "flap_relaunch_verified"
                Raise-Alert "flap_recovered" ("pair ns {0} was DOWN; relaunched via {1}; worker pid {2} argv verified" -f $Namespace, $TaskName, $row.worker_pids[0])
            } else {
                $rel.argv_missing_tokens = $missing2
                $row.status = "flap_relaunch_argv_mismatch"
                Raise-Alert "relaunch_argv_mismatch" ("relaunch via {0} came up WITHOUT pinned tokens [{1}] - the task action is stale; HUMAN ACTION REQUIRED" -f $TaskName, ($missing2 -join " "))
            }
        } else {
            $row.status = "flap_relaunch_failed"
            Raise-Alert "relaunch_failed" ("Start-ScheduledTask {0} fired but no worker matched ns {1} after {2}s" -f $TaskName, $Namespace, $VerifySeconds)
        }
    } else {
        $row.status = "flap_relaunch_failed"
        Raise-Alert "relaunch_failed" ("Start-ScheduledTask {0} FAILED: {1}" -f $TaskName, $rel.error)
    }
    $row.relaunch = $rel
    Write-Row; Save-State
    exit 0
}
finally {
    try { $mutex.ReleaseMutex() } catch {}
    $mutex.Dispose()
}
