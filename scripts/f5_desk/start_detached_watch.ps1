$ErrorActionPreference = 'Stop'
$Desk = 'host-local\redacted_host\repo\scripts\f5_desk'
$Py = 'C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe'
if (-not (Test-Path $Py)) { $Py = 'host-local\redacted_host\repo\.venv\Scripts\python.exe' }
$Watch = Join-Path $Desk 'watch_book_events.py'
$PidFile = 'host-local\redacted_host\repo\judgment\live\book_event_watch.pid'
$Log = 'host-local\redacted_host\repo\judgment\live\book_event_watch.log'

Get-CimInstance Win32_Process | Where-Object {
  $_.CommandLine -and ($_.CommandLine -like '*watch_book_events.py*')
} | ForEach-Object {
  Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 1

# Detached. No stdio redirect — python logs itself. Survives SSH close.
$p = Start-Process -FilePath $Py -ArgumentList @($Watch) -WorkingDirectory $Desk -WindowStyle Hidden -PassThru
Start-Sleep -Seconds 6
$alive = Get-Process -Id $p.Id -ErrorAction SilentlyContinue
Set-Content -LiteralPath $PidFile -Value ([string]$p.Id)
Write-Output ("started pid={0} alive={1}" -f $p.Id, [bool]$alive)
if (Test-Path $Log) {
  Write-Output '---log---'
  Get-Content -LiteralPath $Log -Tail 8
}
$writer = Get-Process -Id 2760,10384 -ErrorAction SilentlyContinue
Write-Output ("writer_alive=" + (($writer | ForEach-Object { $_.Id }) -join ','))
