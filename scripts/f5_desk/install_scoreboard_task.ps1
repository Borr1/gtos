# install_scoreboard_task.ps1 — register GTOS_F5_SCOREBOARD (callable refresh).
# Read-only versus the book. Does not take the judge lock. Does not place/flatten.
# Does not restart book_owner. Pattern: scripts/f5_desk/install_task.ps1
#
# Chair / night / sit can also just run the python:
#   C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe `
#     host-local\redacted_host\repo\scripts\f5_desk\scoreboard.py
#
# Register:
#   powershell -ExecutionPolicy Bypass -File scripts\f5_desk\install_scoreboard_task.ps1 `
#     -PythonExe C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe

param(
    [string]$TaskName = "GTOS_F5_SCOREBOARD",
    [string]$RepoRoot = "host-local\redacted_host\repo",
    [string]$PythonExe = "C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path $RepoRoot)) { throw "RepoRoot not found: $RepoRoot" }
if (-not (Test-Path $PythonExe)) { throw "PythonExe not found: $PythonExe" }

$script = Join-Path $RepoRoot "scripts\f5_desk\scoreboard.py"
if (-not (Test-Path $script)) { throw "scoreboard.py not found at $script" }

$logDir = Join-Path $RepoRoot "pipeline_state\ultimate_book\operator\judgment\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$taskLog = Join-Path $logDir "scoreboard_task.log"

$cmdLine = "/c cd /d `"$RepoRoot`" && `"$PythonExe`" `"$script`" >> `"$taskLog`" 2>&1"
Write-Host "TaskName : $TaskName"
Write-Host "Python   : $PythonExe"
Write-Host "Action   : cmd.exe $cmdLine"
if ($DryRun) { Write-Host "DryRun - nothing registered."; exit 0 }

$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument $cmdLine -WorkingDirectory $RepoRoot
$settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Task $TaskName exists - updating Action."
    Set-ScheduledTask -TaskName $TaskName -Action $action -Settings $settings | Out-Null
} else {
    $bootTrigger = New-ScheduledTaskTrigger -AtStartup
    $repTrigger = New-ScheduledTaskTrigger -Once -At ([datetime]"2026-08-27T00:03:00") `
        -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Days 3650)
    $principal = New-ScheduledTaskPrincipal -UserId "trader" `
        -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName $TaskName -Action $action `
        -Trigger @($bootTrigger, $repTrigger) -Settings $settings -Principal $principal `
        -Description "GTOS F5 judge scoreboard refresh. Read-only. No judge lock. scripts/f5_desk/scoreboard.py" | Out-Null
    Write-Host "Task $TaskName registered."
}
Write-Host "Registered. Not starting judge. Tail: $taskLog"
