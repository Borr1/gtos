$ErrorActionPreference = 'Stop'
$Desk = 'host-local\redacted_host\repo\scripts\f5_desk'
$Py = 'C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe'
if (-not (Test-Path $Py)) { $Py = 'host-local\redacted_host\repo\.venv\Scripts\python.exe' }
$Watch = Join-Path $Desk 'watch_book_events.py'
$PidFile = 'host-local\redacted_host\repo\judgment\live\book_event_watch.pid'
$Log = 'host-local\redacted_host\repo\judgment\live\book_event_watch.log'

# Kill ONLY watch_book_events.py — never GTOS_F5_FTMO
$killed = @()
Get-CimInstance Win32_Process | Where-Object {
  $_.CommandLine -and ($_.CommandLine -like '*watch_book_events.py*')
} | ForEach-Object {
  $killed += $_.ProcessId
  Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 2
$still = @(Get-CimInstance Win32_Process | Where-Object {
  $_.CommandLine -and ($_.CommandLine -like '*watch_book_events.py*')
} | Select-Object -ExpandProperty ProcessId)
if ($still.Count -gt 0) {
  Write-Output ("FAIL still_running " + ($still -join ','))
  exit 2
}

New-Item -ItemType Directory -Force -Path (Split-Path $Log) | Out-Null
$p = Start-Process -FilePath $Py -ArgumentList @($Watch) -WorkingDirectory $Desk -WindowStyle Hidden -RedirectStandardOutput ($Log + '.out') -RedirectStandardError ($Log + '.err') -PassThru
Start-Sleep -Seconds 3
$alive = Get-Process -Id $p.Id -ErrorAction SilentlyContinue
$writer = @(Get-CimInstance Win32_Process | Where-Object {
  $_.CommandLine -and ($_.CommandLine -like '*GTOS_F5_FTMO*')
} | Select-Object -ExpandProperty ProcessId)
Write-Output ("killed=" + (($killed | Select-Object -Unique) -join ','))
Write-Output ("started pid=" + $p.Id + " alive=" + [bool]$alive)
Write-Output ("writer_pids=" + ($writer -join ','))
Set-Content -LiteralPath $PidFile -Value ([string]$p.Id)
