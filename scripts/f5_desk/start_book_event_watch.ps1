# Start book-event sidecar detached from SSH job. Does NOT bounce GTOS_F5_FTMO.
$ErrorActionPreference = 'Stop'
$Desk = 'host-local\redacted_host\repo\scripts\f5_desk'
$Py = 'C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe'
if (-not (Test-Path $Py)) { $Py = 'host-local\redacted_host\repo\.venv\Scripts\python.exe' }
$Watch = Join-Path $Desk 'watch_book_events.py'
$PidFile = 'host-local\redacted_host\repo\judgment\live\book_event_watch.pid'
$Log = 'host-local\redacted_host\repo\judgment\live\book_event_watch.log'

# Kill ONLY watch_book_events.py — never GTOS_F5_FTMO / run_book.py
$killed = @()
Get-CimInstance Win32_Process | Where-Object {
  $_.CommandLine -and ($_.CommandLine -like '*watch_book_events.py*') -and ($_.CommandLine -notlike '*Where-Object*')
} | ForEach-Object {
  $killed += $_.ProcessId
  Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 2
$still = @(Get-CimInstance Win32_Process | Where-Object {
  $_.CommandLine -and ($_.CommandLine -like '*watch_book_events.py*') -and ($_.CommandLine -notlike '*Where-Object*')
} | Select-Object -ExpandProperty ProcessId)
if ($still.Count -gt 0) {
  Write-Output ("FAIL still_running " + ($still -join ','))
  exit 2
}

New-Item -ItemType Directory -Force -Path (Split-Path $Log) | Out-Null
$cmd = ('"{0}" "{1}"' -f $Py, $Watch)
$created = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
  CommandLine = $cmd
  CurrentDirectory = $Desk
}
if (-not $created -or $created.ReturnValue -ne 0) {
  Write-Output ("FAIL create rv=" + $(if ($created) { $created.ReturnValue } else { 'null' }))
  exit 3
}
$procId = [int]$created.ProcessId
Start-Sleep -Seconds 4
$alive = Get-Process -Id $procId -ErrorAction SilentlyContinue
$writer = @(Get-CimInstance Win32_Process | Where-Object {
  $_.CommandLine -and ($_.CommandLine -like '*namespace operator*')
} | Select-Object -ExpandProperty ProcessId)
Write-Output ("killed=" + (($killed | Select-Object -Unique) -join ','))
Write-Output ("started pid=" + $procId + " alive=" + [bool]$alive + " wmi_rv=" + $created.ReturnValue)
Write-Output ("writer_pids=" + ($writer -join ','))
if (Test-Path $PidFile) {
  Write-Output ("pidfile=" + (Get-Content -LiteralPath $PidFile -TotalCount 1))
}
