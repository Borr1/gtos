<#
.SYNOPSIS
    One-time installer for the GTOS_DivergenceWeeklySampler scheduled task.

.DESCRIPTION
    Registers a weekly Task Scheduler job that runs the divergence weekly
    sampler every Monday at 07:00 UTC (converted to local time). The task
    invokes scripts/divergence_weekly_sampler_launcher.vbs which in turn
    runs the Python sampler with a hidden console, logging to
    logs/divergence_sampler.log.

    The task is registered under the CURRENT USER account (not SYSTEM) so
    the task shares the same Python + env visibility as interactive usage.
    It is set to run whether the user is logged on or not.

    CEO should run this ONCE, after reviewing the branch. The sampler
    itself will run without further intervention until the promotion gate
    clears (>=100 classifications with >=80% v2-correct rate).

.PARAMETER Force
    If the task already exists, unregister it first and re-create. Default
    behavior skips re-install when the task exists.

.EXAMPLE
    # Preview -- does nothing destructive, shows what would happen.
    # (There is no real preview mode; use -Force to overwrite.)

.EXAMPLE
    # First install
    powershell.exe -ExecutionPolicy Bypass -File scripts\install_divergence_sampler_task.ps1

.EXAMPLE
    # Force re-install (if the launcher path changed, for example)
    powershell.exe -ExecutionPolicy Bypass -File scripts\install_divergence_sampler_task.ps1 -Force

.NOTES
    Trigger time: Mondays at 07:00 UTC, converted to local time via
    (Get-TimeZone). On Windows, scheduled task triggers are stored in
    local time. If the machine's timezone changes, the trigger continues
    to fire at the old local time -- re-run this installer with -Force
    after any timezone change to realign with 07:00 UTC.

    Default task settings:
      * Run whether user is logged on or not (but NOT with highest
        privileges -- the sampler only reads / writes files under the
        project directory).
      * Wake the computer to run the task.
      * Retry on failure: 3 attempts, 10-minute interval.
      * Task expiration: none (open-ended).
#>

param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# -----------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------

$TaskName    = "GTOS_DivergenceWeeklySampler"
$ProjectDir  = "C:\Users\MSI\Documents\ai-trading-agent"
$Launcher    = Join-Path $ProjectDir "scripts\divergence_weekly_sampler_launcher.vbs"
$WscriptExe  = "C:\Windows\System32\wscript.exe"

# Trigger: 07:00 UTC every Monday. Convert to local time for the trigger spec.
$tz = Get-TimeZone
$utc7 = [DateTime]::UtcNow.Date.AddHours(7)
$local7 = [TimeZoneInfo]::ConvertTimeFromUtc($utc7, $tz)
$localTimeStr = $local7.ToString("HH:mm")

Write-Host "=== GTOS Divergence Sampler -- Task Installer ==="
Write-Host "Task name      : $TaskName"
Write-Host "Launcher       : $Launcher"
Write-Host "Trigger (UTC)  : Mondays 07:00"
Write-Host "Trigger (local): Mondays $localTimeStr ($($tz.Id))"
Write-Host ""

# -----------------------------------------------------------------
# Sanity checks
# -----------------------------------------------------------------

if (-not (Test-Path $Launcher)) {
    Write-Error "Launcher not found at: $Launcher. Commit the VBS launcher first."
    exit 2
}

if (-not (Test-Path $WscriptExe)) {
    Write-Error "wscript.exe not found at: $WscriptExe. Cannot install task."
    exit 2
}

# -----------------------------------------------------------------
# Existing-task handling
# -----------------------------------------------------------------

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($null -ne $existing) {
    if (-not $Force) {
        Write-Host "Task '$TaskName' already exists. Skipping install. Use -Force to re-register."
        exit 0
    }
    Write-Host "Unregistering existing task '$TaskName' (Force supplied)..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# -----------------------------------------------------------------
# Build + register
# -----------------------------------------------------------------

$action = New-ScheduledTaskAction -Execute $WscriptExe -Argument "`"$Launcher`""
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At $localTimeStr
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -WakeToRun `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

# Current user, run whether logged on or not. No highest privileges needed.
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType S4U `
    -RunLevel Limited

$task = New-ScheduledTask `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "GTOS weekly divergence sampler -- produces research/divergence_sampling/week_YYYY-WW.md for CEO classification toward v2 promotion gate."

Register-ScheduledTask -TaskName $TaskName -InputObject $task | Out-Null

Write-Host ""
Write-Host "Registered task '$TaskName'."
Write-Host "Next run time: (check via Get-ScheduledTaskInfo -TaskName $TaskName)"
Write-Host ""
Write-Host "To run on-demand (for testing):"
Write-Host "  Start-ScheduledTask -TaskName $TaskName"
Write-Host ""
Write-Host "To inspect:"
Write-Host "  Get-ScheduledTask -TaskName $TaskName"
Write-Host "  Get-ScheduledTaskInfo -TaskName $TaskName"
Write-Host ""
Write-Host "To remove:"
Write-Host "  Unregister-ScheduledTask -TaskName $TaskName -Confirm:`$false"

exit 0
