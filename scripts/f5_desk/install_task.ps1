# install_task.ps1 - register GTOS_F5_JUDGE: the resident F5 judgment daemon.
# STAGED - this file deploys nothing by being committed; an operator runs it ON the VPS
# F5 tree (host-local\redacted_host\repo) after the smoke check below passes.
#
# PATTERN (prior art, checked per house rule): scripts/f5_keepalive_watchdog.ps1 -
# at-startup + short-repetition scheduled task as the keep-alive, never-kill principle,
# logs under the namespace's own tree. The daemon itself is single-instance via a
# heartbeat lock file (pipeline_state\...\judgment\state\judge_daemon.lock), so the
# 5-minute repetition is a pure relauncher: a live daemon makes the extra start exit 0
# within a second; a dead one is back inside 5 minutes. Task-level
# MultipleInstances=IgnoreNew is belt on top of that suspender.
#
# WHAT THE DAEMON CAN DO: read shadow_logs streams, write judgment sidecars/manage
# files/journals under judgment\ and pipeline_state\ultimate_book\operator\
# judgment\, and call the local model CLIs (claude/cursor-agent/codex). It places no
# orders, needs no token, and the book treats its absence as PASS (code-only behavior).
#
# DEPLOY CEREMONY (operator, on the VPS, from the F5 repo root):
#   0. Preconditions: the F5 pair is healthy; you are in host-local\redacted_host\repo.
#   1. SMOKE the providers first (proves CLI auth + latency without touching the book):
#        .venv\Scripts\python.exe scripts\f5_desk\judge_daemon.py --smoke
#      Every provider you expect must print ok=True. All dark -> STOP, fix auth, re-run.
#   2. ONE HAND CYCLE and read the output (writes real sidecars; the book will consume
#      them - that is the point; a HOLD lasts at most 3600 s):
#        .venv\Scripts\python.exe scripts\f5_desk\judge_daemon.py --once
#   3. Register the task (this script):
#        powershell -ExecutionPolicy Bypass -File scripts\f5_desk\install_task.ps1 `
#          -PythonExe C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe
#      Optional: -RepoRoot <path>  -PythonExe <path>  -TaskName GTOS_F5_JUDGE
#      Action argv is --once --max-calls-per-day 200 (not run_forever).
#   4. Verify:  Get-ScheduledTask GTOS_F5_JUDGE | Get-ScheduledTaskInfo
#      then tail pipeline_state\ultimate_book\operator\judgment\logs\judge_daemon.log
#   5. To STOP the judge: Disable-ScheduledTask GTOS_F5_JUDGE, then (optionally) delete
#      the lock file. Nothing on the book changes when the judge dies - PASS is the
#      no-row answer by construction.

param(
    [string]$TaskName = "GTOS_F5_JUDGE",
    [string]$RepoRoot = "host-local\redacted_host\repo",
    [string]$PythonExe = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $RepoRoot)) {
    throw "RepoRoot not found: $RepoRoot - pass -RepoRoot for a non-default tree."
}
if (-not $PythonExe) {
    # Same resolution order the F5 tree's own tasks use; fall back to the venv names seen
    # on this host family, then PATH python.
    $candidates = @(
        (Join-Path $RepoRoot ".venv\Scripts\python.exe"),
        (Join-Path $RepoRoot ".venv-gtos\Scripts\python.exe")
    )
    foreach ($c in $candidates) { if (Test-Path $c) { $PythonExe = $c; break } }
    if (-not $PythonExe) {
        $onPath = (Get-Command python.exe -ErrorAction SilentlyContinue)
        if ($onPath) { $PythonExe = $onPath.Source }
    }
}
if (-not $PythonExe -or -not (Test-Path $PythonExe)) {
    throw "No python.exe resolved (tried repo venvs + PATH). Pass -PythonExe explicitly."
}

$daemon = Join-Path $RepoRoot "scripts\f5_desk\judge_daemon.py"
if (-not (Test-Path $daemon)) { throw "judge_daemon.py not found at $daemon" }

$logDir = Join-Path $RepoRoot "pipeline_state\ultimate_book\operator\judgment\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$taskLog = Join-Path $logDir "daemon_task.log"

# cmd wrapper so stdout/stderr land in the task log even before python logging is up.
$cmdLine = "/c cd /d `"$RepoRoot`" && `"$PythonExe`" `"$daemon`" --once --max-calls-per-day 200 >> `"$taskLog`" 2>&1"

Write-Host "TaskName : $TaskName"
Write-Host "RepoRoot : $RepoRoot"
Write-Host "Python   : $PythonExe"
Write-Host "Action   : cmd.exe $cmdLine"
if ($DryRun) { Write-Host "DryRun - nothing registered."; exit 0 }

$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument $cmdLine -WorkingDirectory $RepoRoot

$settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 2)

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Task $TaskName exists - updating Action in place (keep live 5-min + boot triggers)."
    Set-ScheduledTask -TaskName $TaskName -Action $action -Settings $settings | Out-Null
} else {
    # New task only. Do NOT use [TimeSpan]::MaxValue (P99999999DT23H59M59S rejected).
    # 3650d duration is valid; live XML uses empty Duration (indefinite).
    $bootTrigger = New-ScheduledTaskTrigger -AtStartup
    $repTrigger = New-ScheduledTaskTrigger -Once -At ([datetime]"2026-08-26T00:01:00") `
        -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 3650)
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
        -LogonType S4U -RunLevel Limited
    Register-ScheduledTask -TaskName $TaskName -Action $action `
        -Trigger @($bootTrigger, $repTrigger) -Settings $settings -Principal $principal `
        -Description "GTOS F5 judgment daemon (composer+judge+shim). --once every 5 min. Ceremony: scripts/f5_desk/install_task.ps1." | Out-Null
    Write-Host "Task $TaskName registered."
}
Start-ScheduledTask -TaskName $TaskName
Write-Host "Started. Tail: $taskLog"
