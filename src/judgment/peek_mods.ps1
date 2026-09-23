$ErrorActionPreference = "Continue"
$repo = "host-local\redacted_host\repo"
$j = Join-Path $repo "src\judgment"
Write-Output "UTC $((Get-Date).ToUniversalTime().ToString('o'))"
Write-Output "=== HEADS ==="
foreach ($n in @("apply_size.py","writer_compose_place.py","complete_judge.py","dig_b_static.py","news_calendar_sync.py","harvest_patterns.py","sleeve_on_surface_loader.py","two_stop.py","occupancy.py","jev_wires.py","place_choice.py")) {
  $p = Join-Path $j $n
  if (-not (Test-Path $p)) { Write-Output "MISSING $n"; continue }
  Write-Output ("FILE {0} bytes={1}" -f $n, (Get-Item $p).Length)
  Get-Content $p -TotalCount 12
  Write-Output "---"
}
Write-Output "=== FN_AGAIN ==="
Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'python' -and $_.CommandLine -match 'redacted_account|0' } | ForEach-Object {
  Write-Output ("FN PID={0} {1}" -f $_.ProcessId, $_.CommandLine.Substring(0, [Math]::Min(180, $_.CommandLine.Length)))
}
Write-Output "=== HB ==="
Get-Content (Join-Path $repo "pipeline_state\ultimate_book\operator\heartbeat.json") -Raw
Write-Output "DONE"
