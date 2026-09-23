<#
.SYNOPSIS
    Configure the GTOS watchdog scheduled task for live VPS supervision.

.DESCRIPTION
    The watchdog is intentionally a one-shot health-and-repair pass. Task
    Scheduler owns durable, post-reboot repetition. This script makes that
    scheduler contract explicit and reproducible:

    - run hidden through scripts/watchdog_launcher.vbs;
    - repeat every minute during live supervision;
    - do not overlap runs;
    - bound a stuck run so it cannot block future supervision for hours;
    - restart the task on scheduler-visible failure.

    Safe to rerun. Does not touch broker orders, positions, deals, or MT5
    account state.
#>

param(
    [string]$TaskName = "GTOS_Watchdog",
    [string]$ProjectDir = "C:\Users\MSI\Documents\ai-trading-agent",
    [int]$IntervalMinutes = 1,
    [int]$ExecutionLimitMinutes = 10,
    [int]$RestartCount = 3,
    [int]$RestartIntervalMinutes = 1,
    [int]$RepetitionDurationDays = 3650
)

$ErrorActionPreference = "Stop"

if ($IntervalMinutes -lt 1) {
    throw "IntervalMinutes must be >= 1"
}
if ($ExecutionLimitMinutes -lt 2) {
    throw "ExecutionLimitMinutes must be >= 2"
}

$launcher = Join-Path $ProjectDir "scripts\watchdog_launcher.vbs"
if (-not (Test-Path -LiteralPath $launcher)) {
    throw "Missing watchdog launcher: $launcher"
}

$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$launcher`""
$trigger = New-ScheduledTaskTrigger `
    -Once `
    -At ((Get-Date).AddMinutes(1)) `
    -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
    -RepetitionDuration (New-TimeSpan -Days $RepetitionDurationDays)

$settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes $ExecutionLimitMinutes) `
    -RestartCount $RestartCount `
    -RestartInterval (New-TimeSpan -Minutes $RestartIntervalMinutes)

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($null -eq $existing) {
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings | Out-Null
} else {
    Set-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings | Out-Null
}

Enable-ScheduledTask -TaskName $TaskName | Out-Null

$task = Get-ScheduledTask -TaskName $TaskName
$info = Get-ScheduledTaskInfo -TaskName $TaskName
$configuredTrigger = @($task.Triggers)[0]

[pscustomobject]@{
    task_name = $TaskName
    state = $task.State.ToString()
    action_execute = @($task.Actions)[0].Execute
    action_arguments = @($task.Actions)[0].Arguments
    interval = $configuredTrigger.Repetition.Interval
    duration = $configuredTrigger.Repetition.Duration
    execution_time_limit = $task.Settings.ExecutionTimeLimit
    multiple_instances = $task.Settings.MultipleInstances.ToString()
    restart_count = $task.Settings.RestartCount
    restart_interval = $task.Settings.RestartInterval
    last_run_time = $info.LastRunTime
    next_run_time = $info.NextRunTime
    last_task_result = $info.LastTaskResult
} | ConvertTo-Json -Depth 3
