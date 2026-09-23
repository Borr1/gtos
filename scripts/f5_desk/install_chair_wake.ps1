# Register GTOS_F5_CHAIR_WAKE via schtasks.exe /XML.
# Register-ScheduledTask from host-admin is a silent no-op. Do not use it.
# Start-Process from host-admin dies with the job. This task is the durable host.
param(
    [string]$TaskName = "GTOS_F5_CHAIR_WAKE",
    [string]$RepoRoot = "host-local\redacted_host\repo",
    [string]$PythonExe = "C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path $RepoRoot)) { throw "RepoRoot not found: $RepoRoot" }
if (-not (Test-Path $PythonExe)) { throw "PythonExe not found: $PythonExe" }
$hostPy = Join-Path $RepoRoot "scripts\f5_desk\chair_wake_host.py"
if (-not (Test-Path $hostPy)) { throw "chair_wake_host.py not found at $hostPy" }

$logDir = Join-Path $RepoRoot "pipeline_state\ultimate_book\operator\judgment\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$taskLog = Join-Path $logDir "chair_wake_task.log"
$xmlPath = Join-Path $env:TEMP "GTOS_F5_CHAIR_WAKE.xml"

$args = '/c cd /d "' + $RepoRoot + '" && "' + $PythonExe + '" "' + $hostPy + '" >> "' + $taskLog + '" 2>&1'
$xml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>GTOS F5 chair wake host. Snapshot + orig latch + wake card + mechanical HOLD. Does not judge. schtasks.exe only.</Description>
  </RegistrationInfo>
  <Triggers>
    <BootTrigger>
      <Enabled>true</Enabled>
    </BootTrigger>
    <TimeTrigger>
      <StartBoundary>2026-08-26T00:01:00</StartBoundary>
      <Enabled>true</Enabled>
      <Repetition>
        <Interval>PT5M</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
    </TimeTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>Administrator</UserId>
      <LogonType>S4U</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
    <RestartOnFailure>
      <Interval>PT2M</Interval>
      <Count>3</Count>
    </RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>cmd.exe</Command>
      <Arguments>$args</Arguments>
      <WorkingDirectory>$RepoRoot</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@

# UTF-16 LE with BOM — Task Scheduler requires it.
$utf16 = New-Object System.Text.UnicodeEncoding $false, $true
[System.IO.File]::WriteAllText($xmlPath, $xml, $utf16)

schtasks.exe /Delete /TN $TaskName /F 2>$null | Out-Null
$create = schtasks.exe /Create /TN $TaskName /XML $xmlPath /F
if ($LASTEXITCODE -ne 0) { throw "schtasks /Create failed: $create" }
schtasks.exe /Run /TN $TaskName
if ($LASTEXITCODE -ne 0) { throw "schtasks /Run failed" }
schtasks.exe /Query /TN $TaskName /FO LIST /V
Write-Output "TASK_OK $TaskName log=$taskLog"
